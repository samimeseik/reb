"""The investigation ledger: one JSON file per engagement workspace.

Layout:
  <workspace>/.reb/ledger.json      sources, evidence, claims, unknowns, obligations
  <workspace>/.reb/text/<id>.txt    extracted (pseudonymized) source text, for quote checks
  <workspace>/.reb/pseudonyms.json  identifier -> token map (local only, never rendered)
  <workspace>/.reb/lock             held while a command reads-modifies-writes the ledger
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import unicodedata
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from .errors import RebError
from .grading import AUTHORITY_RANK, compute_grade, evaluate_claim
from .guardrails import (
    Pseudonymizer,
    check_authority,
    check_source_admissible,
    check_vocabulary,
    normalize_controller,
)
from .models import (
    Authority,
    Claim,
    ClaimKind,
    Confidence,
    Custody,
    Engagement,
    Evidence,
    Layer,
    LedgerData,
    Mode,
    ObservationContext,
    Replicability,
    Resolution,
    Sensitivity,
    Source,
    SourceKind,
    Unknown,
    UnknownStatus,
    utc_now,
)

try:  # POSIX advisory locking; on other platforms commands are not serialized
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None  # type: ignore[assignment]

REB_DIR = ".reb"


def digest(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    # drop Arabic diacritics (tashkeel) and tatweel so quotes match regardless of vocalization
    text = re.sub(r"[ً-ٰٟـ]", "", text)
    return re.sub(r"\s+", " ", text).strip().casefold()


class Ledger:
    def __init__(self, workspace: Path, data: LedgerData):
        self.workspace = Path(workspace)
        self.data = data
        self._pseudo: Pseudonymizer | None = None

    # ---- lifecycle -----------------------------------------------------
    @property
    def root(self) -> Path:
        return self.workspace / REB_DIR

    @classmethod
    def init(
        cls,
        workspace: Path,
        *,
        name: str,
        subject: str,
        mode: Mode | str,
        authorization: str | None = None,
        profile: str | None = None,
        analyst: str | None = None,
        language: str = "ar",
    ) -> "Ledger":
        workspace = Path(workspace)
        if (workspace / REB_DIR / "ledger.json").exists():
            raise RebError("engagement_exists", f"An engagement already exists in {workspace}.")
        mode = Mode(mode)
        if mode != Mode.PUBLIC and not authorization:
            raise RebError(
                "authorization_required",
                "Modes 'self' and 'engaged' need --authorization (ownership or mandate reference).",
            )
        engagement = Engagement(
            id="eng_" + digest([name, subject, utc_now()])[:12],
            name=name,
            subject=subject,
            mode=mode,
            authorization=authorization,
            profile=profile,
            analyst=analyst,
            language=language,
        )
        ledger = cls(workspace, LedgerData(engagement=engagement))
        (ledger.root / "text").mkdir(parents=True, exist_ok=True)
        (ledger.root / ".gitignore").write_text("*\n", encoding="utf-8")
        ledger.save()
        return ledger

    @classmethod
    def load(cls, workspace: Path) -> "Ledger":
        path = Path(workspace) / REB_DIR / "ledger.json"
        if not path.exists():
            raise RebError(
                "no_engagement",
                f"No engagement in {workspace}. Run `reb init` (or open_engagement) first.",
            )
        data = LedgerData.model_validate_json(path.read_text(encoding="utf-8"))
        return cls(Path(workspace), data)

    @classmethod
    @contextlib.contextmanager
    def open(cls, workspace: Path, *, write: bool = True) -> Iterator["Ledger"]:
        """Load under an exclusive lock and save on success, so concurrent commands
        (parallel CLI runs, an MCP server and a terminal) cannot lose each other's writes."""
        root = Path(workspace) / REB_DIR
        if not (root / "ledger.json").exists():
            raise RebError("no_engagement", f"No engagement in {workspace}. Run `reb init` first.")
        with open(root / "lock", "a+") as lock:
            if fcntl:
                fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                ledger = cls.load(workspace)
                yield ledger
                if write:
                    ledger.save()
            finally:
                if fcntl:
                    fcntl.flock(lock, fcntl.LOCK_UN)

    def save(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        tmp = self.root / f"ledger.json.{os.getpid()}.tmp"
        tmp.write_text(self.data.model_dump_json(indent=2), encoding="utf-8")
        tmp.replace(self.root / "ledger.json")
        if self._pseudo is not None:
            ptmp = self.root / f"pseudonyms.json.{os.getpid()}.tmp"
            ptmp.write_text(json.dumps(self._pseudo.mapping, ensure_ascii=False, indent=2), encoding="utf-8")
            ptmp.replace(self.root / "pseudonyms.json")

    @property
    def pseudonymizer(self) -> Pseudonymizer:
        if self._pseudo is None:
            path = self.root / "pseudonyms.json"
            mapping = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
            self._pseudo = Pseudonymizer(mapping)
        return self._pseudo

    def scrub(self, text: str | None) -> str | None:
        return None if text is None else self.pseudonymizer.scrub(text)

    @property
    def engagement(self) -> Engagement:
        return self.data.engagement

    # ---- sources -------------------------------------------------------
    def build_source(
        self,
        *,
        content: bytes,
        kind: SourceKind | str,
        custody: Custody | str,
        title: str,
        origin_party: str,
        controller: str | None = None,
        path: str | None = None,
        legal_basis: str | None = None,
        sensitivity: Sensitivity | str = Sensitivity.INTERNAL,
        language: str | None = None,
        context: ObservationContext | dict | None = None,
        upstream_ids: list[str] | None = None,
        verification_ids: list[str] | None = None,
        independent_channel: bool = False,
        notes: str | None = None,
    ) -> Source:
        """Build and check a source without storing it (ingest checks before parsing)."""
        sha = hashlib.sha256(content).hexdigest()
        for up in [*(upstream_ids or []), *(verification_ids or [])]:
            if up not in self.data.sources:
                raise RebError("unknown_source", f"Source {up} is not in the ledger.")
        if isinstance(context, dict):
            context = ObservationContext.model_validate(context)
        source = Source(
            id="src_" + sha[:12],
            sha256=sha,
            kind=SourceKind(kind),
            custody=Custody(custody),
            title=title,
            path=path,
            origin_party=origin_party,
            controller=controller or origin_party,
            controller_explicit=bool(controller),
            upstream_ids=upstream_ids or [],
            verification_ids=verification_ids or [],
            legal_basis=legal_basis,
            sensitivity=Sensitivity(sensitivity),
            language=language,
            context=context or ObservationContext(),
            independent_channel=independent_channel,
            notes=notes,
        )
        normalize_controller(self.engagement, source)
        check_source_admissible(self.engagement, source, set(self.data.sources))
        return source

    def add_source(self, *, text: str | None = None, **kwargs: Any) -> tuple[Source, bool]:
        """Register a source. Returns (source, created). Text is stored pseudonymized."""
        source = self.build_source(**kwargs)
        if source.id in self.data.sources:
            return self.data.sources[source.id], False
        if text is not None:
            text_file = self.root / "text" / f"{source.id}.txt"
            text_file.parent.mkdir(parents=True, exist_ok=True)
            text_file.write_text(self.pseudonymizer.scrub(text), encoding="utf-8")
            source.text_path = str(text_file.relative_to(self.workspace))
        self.data.sources[source.id] = source
        return source, True

    def source(self, source_id: str) -> Source:
        try:
            return self.data.sources[source_id]
        except KeyError:
            raise RebError("unknown_source", f"Source {source_id} is not in the ledger.") from None

    def source_text(self, source_id: str) -> str | None:
        src = self.source(source_id)
        if not src.text_path:
            return None
        return (self.workspace / src.text_path).read_text(encoding="utf-8")

    def read_original(self, source_id: str) -> Path:
        """Path to the original file, refusing if it changed since ingest."""
        src = self.source(source_id)
        if not src.path or not Path(src.path).is_file():
            raise RebError("no_original", f"The original file of {source_id} is not available.")
        if hashlib.sha256(Path(src.path).read_bytes()).hexdigest() != src.sha256:
            raise RebError(
                "source_changed",
                f"{src.path} changed since it was ingested as {source_id}. Ingest the new version as a new source.",
            )
        return Path(src.path)

    # ---- evidence ------------------------------------------------------
    def add_evidence(
        self,
        *,
        source_id: str,
        fact: str,
        authority: Authority | str,
        provider: str = "analyst",
        operation: str = "record_evidence",
        confidence: Confidence | str = Confidence.OBSERVED,
        location: str | None = None,
        quote: str | None = None,
        entity: str | None = None,
        layer: Layer | str | None = None,
        normalized: dict | None = None,
        limitations: list[str] | None = None,
        as_of: str | None = None,
    ) -> Evidence:
        source = self.source(source_id)
        authority = Authority(authority)
        confidence = Confidence(confidence)
        layer = Layer(layer) if layer else None
        check_authority(source, authority)
        fact = self.scrub(fact) or ""
        check_vocabulary(fact)
        entity = self.scrub(entity)
        limitations = list(limitations or [])
        if quote is not None:
            if not quote.strip():
                raise RebError("empty_quote", "An empty quote checks nothing. Omit it or quote the source.")
            quote = self.scrub(quote)
            text = self.source_text(source_id)
            if text is None:
                limitations.append("quote not machine-checked: source has no extracted text")
            elif normalize_text(quote) not in normalize_text(text):
                raise RebError(
                    "quote_not_found",
                    "The quote does not appear in the source text. Quote the source verbatim "
                    "(read_source shows the stored text) or omit the quote and lower the confidence.",
                )
        grade = compute_grade(authority, confidence, source)
        payload = [source_id, operation, fact, location, quote, authority.value, confidence.value, entity,
                   layer.value if layer else None]
        ev = Evidence(
            id="ev_" + digest(payload)[:12],
            source_id=source_id,
            provider=provider,
            operation=operation,
            fact=fact,
            location=location,
            quote=quote,
            entity=entity,
            layer=layer,
            authority=authority,
            confidence=confidence,
            grade=grade,
            normalized=normalized or {},
            limitations=limitations,
            as_of=as_of,
        )
        self.data.evidence.setdefault(ev.id, ev)
        return self.data.evidence[ev.id]

    def evidence(self, evidence_id: str) -> Evidence:
        try:
            return self.data.evidence[evidence_id]
        except KeyError:
            raise RebError("unknown_evidence", f"Evidence {evidence_id} is not in the ledger.") from None

    # ---- claims --------------------------------------------------------
    def record_claim(
        self,
        *,
        statement: str,
        layer: Layer | str,
        evidence_ids: list[str] | None = None,
        contradicting_evidence_ids: list[str] | None = None,
        entity: str | None = None,
        item: str | None = None,
        kind: ClaimKind | str = ClaimKind.NEUTRAL,
        metric: str | None = None,
        value: float | None = None,
        unit: str | None = None,
        replicability: Replicability | str = Replicability.UNASSESSED,
        industry_prior: bool = False,
        as_of: str | None = None,
    ) -> Claim:
        statement = self.scrub(statement) or ""
        check_vocabulary(statement)
        entity = self.scrub(entity)
        for eid in [*(evidence_ids or []), *(contradicting_evidence_ids or [])]:
            self.evidence(eid)
        kind = ClaimKind(kind)
        layer = Layer(layer)
        claim = Claim(
            id="clm_" + digest([statement, layer.value, entity, item, metric, kind.value, value, unit])[:12],
            statement=statement,
            layer=layer,
            entity=entity,
            item=item,
            kind=kind,
            metric=metric,
            value=value,
            unit=unit,
            evidence_ids=list(dict.fromkeys(evidence_ids or [])),
            contradicting_evidence_ids=list(dict.fromkeys(contradicting_evidence_ids or [])),
            replicability=Replicability(replicability),
            industry_prior=industry_prior,
            as_of=as_of,
        )
        existing = self.data.claims.get(claim.id)
        if existing:
            existing.evidence_ids = list(dict.fromkeys([*existing.evidence_ids, *claim.evidence_ids]))
            existing.contradicting_evidence_ids = list(
                dict.fromkeys([*existing.contradicting_evidence_ids, *claim.contradicting_evidence_ids])
            )
            if claim.replicability != Replicability.UNASSESSED:
                existing.replicability = claim.replicability
            existing.industry_prior = existing.industry_prior or claim.industry_prior
            claim = existing
        self.data.claims[claim.id] = claim
        self.reevaluate_claim(claim)
        return claim

    def claim(self, claim_id: str) -> Claim:
        try:
            return self.data.claims[claim_id]
        except KeyError:
            raise RebError("unknown_claim", f"Claim {claim_id} is not in the ledger.") from None

    def reevaluate_claim(self, claim: Claim) -> None:
        claim.status, claim.grade = evaluate_claim(claim, self.data.evidence, self.data.sources)

    def reevaluate(self) -> None:
        for claim in self.data.claims.values():
            self.reevaluate_claim(claim)

    # ---- unknowns ------------------------------------------------------
    def record_unknown(
        self,
        *,
        question: str,
        layer: Layer | str | None = None,
        entity: str | None = None,
        item: str | None = None,
        status: UnknownStatus | str = UnknownStatus.OPEN,
        required_authority: Authority | str | None = None,
        recommended_probes: list[str] | None = None,
        supporting_evidence_ids: list[str] | None = None,
        contradicting_evidence_ids: list[str] | None = None,
    ) -> Unknown:
        question = self.scrub(question) or ""
        probes = [self.scrub(p) or "" for p in recommended_probes or []]
        for text in [question, *probes]:
            check_vocabulary(text)
        for eid in [*(supporting_evidence_ids or []), *(contradicting_evidence_ids or [])]:
            self.evidence(eid)
        status = UnknownStatus(status)
        if status == UnknownStatus.RESOLVED:
            raise RebError("invalid_status", "Record the unknown first, then resolve it with update_unknown.")
        unknown = Unknown(
            id="unk_" + digest([question, layer, entity, item])[:12],
            question=question,
            layer=Layer(layer) if layer else None,
            entity=self.scrub(entity),
            item=item,
            status=status,
            required_authority=Authority(required_authority) if required_authority else None,
            recommended_probes=probes,
            supporting_evidence_ids=supporting_evidence_ids or [],
            contradicting_evidence_ids=contradicting_evidence_ids or [],
        )
        self.data.unknowns.setdefault(unknown.id, unknown)
        return self.data.unknowns[unknown.id]

    def update_unknown(
        self,
        unknown_id: str,
        *,
        revision: int,
        status: UnknownStatus | str | None = None,
        add_supporting: list[str] | None = None,
        add_contradicting: list[str] | None = None,
        add_probes: list[str] | None = None,
        resolution: Resolution | dict | None = None,
    ) -> Unknown:
        try:
            unknown = self.data.unknowns[unknown_id]
        except KeyError:
            raise RebError("unknown_unknown", f"Unknown {unknown_id} is not in the ledger.") from None
        if revision != unknown.revision:
            raise RebError(
                "stale_revision",
                f"Unknown {unknown_id} is at revision {unknown.revision}, not {revision}. Re-read it first.",
            )
        for eid in [*(add_supporting or []), *(add_contradicting or [])]:
            self.evidence(eid)
        probes = [self.scrub(p) or "" for p in add_probes or []]
        for p in probes:
            check_vocabulary(p)
        if status:
            status = UnknownStatus(status)
            if unknown.status == UnknownStatus.CONTRADICTED and status not in (
                UnknownStatus.CONTRADICTED,
                UnknownStatus.RESOLVED,
            ):
                raise RebError(
                    "contradiction_needs_resolution",
                    "A contradicted unknown can only leave that state by being resolved with evidence "
                    "(verified or refuted).",
                )
            if status == UnknownStatus.RESOLVED:
                if resolution is None:
                    raise RebError("resolution_required", "Resolving an unknown needs a resolution.")
                resolution = Resolution.model_validate(resolution) if isinstance(resolution, dict) else resolution
                if resolution.note:
                    resolution.note = self.scrub(resolution.note)
                    check_vocabulary(resolution.note)
                self._check_resolution(unknown, resolution)
                unknown.resolution = resolution
        unknown.supporting_evidence_ids = list(
            dict.fromkeys([*unknown.supporting_evidence_ids, *(add_supporting or [])])
        )
        unknown.contradicting_evidence_ids = list(
            dict.fromkeys([*unknown.contradicting_evidence_ids, *(add_contradicting or [])])
        )
        unknown.recommended_probes = list(dict.fromkeys([*unknown.recommended_probes, *probes]))
        if status:
            unknown.status = status
        unknown.revision += 1
        unknown.updated_at = utc_now()
        return unknown

    def reopen_unknown(self, unknown: Unknown, status: UnknownStatus) -> None:
        unknown.status = status
        unknown.resolution = None
        unknown.revision += 1
        unknown.updated_at = utc_now()

    def _check_resolution(self, unknown: Unknown, resolution: Resolution) -> None:
        if resolution.kind not in {"verified", "refuted", "out_of_scope"}:
            raise RebError("invalid_resolution", "resolution.kind must be verified, refuted or out_of_scope.")
        if resolution.kind == "out_of_scope":
            if unknown.status == UnknownStatus.CONTRADICTED:
                raise RebError(
                    "contradiction_needs_resolution",
                    "A contradiction cannot be declared out of scope; resolve it with evidence.",
                )
            if not resolution.note:
                raise RebError("note_required", "Explain in resolution.note why this is out of scope.")
            return
        if not resolution.evidence_ids:
            raise RebError(
                "evidence_required",
                "Only evidence can settle an unknown. Attach evidence_ids or mark it out_of_scope.",
            )
        items = [self.evidence(e) for e in resolution.evidence_ids]
        if unknown.required_authority:
            needed = AUTHORITY_RANK.index(unknown.required_authority)
            if not any(AUTHORITY_RANK.index(e.authority) <= needed for e in items):
                raise RebError(
                    "insufficient_authority",
                    f"This unknown needs evidence of authority '{unknown.required_authority.value}' "
                    "or stronger to be settled.",
                )
