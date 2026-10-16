"""Shared ingest workflow (used by both the CLI and the MCP server)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..domain.errors import RebError
from ..domain.guardrails import check_vocabulary
from ..domain.ledger import Ledger
from ..domain.models import Confidence, Custody, SourceKind
from ..providers import default_authority, detect_kind, extract


def ingest_file(
    ledger: Ledger,
    path: str | Path,
    *,
    custody: Custody | str,
    origin_party: str,
    controller: str | None = None,
    kind: SourceKind | str | None = None,
    title: str | None = None,
    legal_basis: str | None = None,
    sensitivity: str = "internal",
    language: str | None = None,
    context: dict | None = None,
    upstream_ids: list[str] | None = None,
    verification_ids: list[str] | None = None,
    independent_channel: bool = False,
    notes: str | None = None,
) -> dict[str, Any]:
    path = Path(path).expanduser()
    if not path.is_file():
        raise RebError("file_not_found", f"No file at {path}.")
    detected = detect_kind(path)
    kind = SourceKind(kind) if kind else detected
    if detected == SourceKind.CHAT_EXPORT and kind != SourceKind.CHAT_EXPORT:
        raise RebError(
            "kind_mismatch",
            "This file looks like a chat export. Ingest it as kind 'chat_export' (it needs a legal_basis).",
        )
    content = path.read_bytes()
    spec = dict(
        content=content,
        kind=kind,
        custody=custody,
        title=title or path.name,
        origin_party=origin_party,
        controller=controller,
        path=str(path),
        legal_basis=legal_basis,
        sensitivity=sensitivity,
        language=language,
        context={k: v for k, v in (context or {}).items() if v},
        upstream_ids=upstream_ids,
        verification_ids=verification_ids,
        independent_channel=independent_channel,
        notes=notes,
    )
    # Admissibility is checked before any provider reads the content.
    probe = ledger.build_source(**spec)
    if probe.id in ledger.data.sources:
        return {"source": ledger.data.sources[probe.id].model_dump(mode="json"), "created": False, "evidence": []}
    try:
        extraction = extract(path, probe.kind, language=language)
    except ImportError as exc:
        raise RebError("missing_extra", str(exc)) from exc
    pseudo = ledger.pseudonymizer
    for name in extraction.names:
        token = pseudo.person(name)
        # "Ahmet Usta" also appears as plain "Ahmet" inside messages: map the first
        # name to the same token. Only capitalized first names of 3+ letters.
        parts = name.split()
        first = parts[0] if parts else ""
        if len(first) >= 3 and first[0].isupper() and first != name:
            pseudo.mapping.setdefault(f"PERSON:{first}", token)
    source, created = ledger.add_source(text=extraction.text, **spec)
    authority = default_authority(source.kind, source.custody)
    evidence = []
    for fact in extraction.facts:
        normalized = json.loads(ledger.scrub(json.dumps(fact.normalized, ensure_ascii=False, default=str)))
        ev = ledger.add_evidence(
            source_id=source.id,
            fact=fact.fact,
            authority=authority,
            provider=extraction.provider,
            operation=fact.operation,
            confidence=Confidence.OBSERVED,
            location=fact.location,
            entity=fact.entity,
            layer=fact.layer,
            normalized=normalized,
            limitations=[*fact.limitations],
        )
        evidence.append(ev.model_dump(mode="json"))
    return {
        "source": source.model_dump(mode="json"),
        "created": created,
        "evidence": evidence,
        "limitations": extraction.limitations,
        "text_available": source.text_path is not None,
    }


def record_observation(
    ledger: Ledger,
    *,
    title: str,
    note: str,
    observer_role: str,
    legal_basis: str | None = None,
    site: str | None = None,
    when: str | None = None,
    shift: str | None = None,
    facts: list[dict[str, Any]] | None = None,
    public_premises: bool = False,
    artifact_ids: list[str] | None = None,
) -> dict[str, Any]:
    """A structured site-walk / time-study entry captured by the analyst in person.
    Observing staff needs a legal basis (e.g. staff notice); public premises need the place.
    Without artifact_ids (captured photos, count sheets) the observation is capped at grade B
    and only corroborates other sources when observations on two different days agree."""
    facts = facts or [{"fact": note}]
    for text in [note, *(f.get("fact", "") for f in facts)]:
        check_vocabulary(text)
    payload = {"title": title, "note": note, "site": site, "when": when, "shift": shift, "facts": facts,
               "artifacts": sorted(artifact_ids or [])}
    content = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    if public_premises and not legal_basis:
        legal_basis = f"public premises: {site or title}"
    source, _ = ledger.add_source(
        content=content,
        kind=SourceKind.OBSERVATION,
        custody=Custody.PUBLIC if public_premises else Custody.CAPTURED_LIVE,
        title=title,
        origin_party=observer_role,
        controller=f"observer:{observer_role}",
        legal_basis=legal_basis,
        sensitivity="public" if public_premises else "internal",
        context={"site": site, "shift": shift, "note": when},
        artifact_ids=artifact_ids,
        text=note + "\n" + "\n".join(f.get("fact", "") for f in facts),
    )
    evidence = []
    for f in facts:
        ev = ledger.add_evidence(
            source_id=source.id,
            fact=f["fact"],
            authority="direct_observation",
            provider="observation",
            operation="record_observation",
            location=f.get("location") or site,
            entity=f.get("entity"),
            layer=f.get("layer"),
            normalized={k: v for k, v in f.items() if k not in {"fact", "location", "entity", "layer"}},
            limitations=["Observed workers may behave differently while observed (Hawthorne effect)."],
            as_of=when,
        )
        evidence.append(ev.model_dump(mode="json"))
    return {"source": source.model_dump(mode="json"), "evidence": evidence}


def _boilerplate(ledger: Ledger, source_id: str) -> set[str]:
    """Lines repeated on many pages from the same controller (menus, footers)."""
    from collections import Counter

    me = ledger.source(source_id)
    peers = [s for s in ledger.data.sources.values() if s.controller == me.controller and s.text_path]
    if len(peers) < 4:
        return set()
    counts: Counter[str] = Counter()
    for s in peers:
        counts.update(set((ledger.source_text(s.id) or "").splitlines()))
    return {line for line, n in counts.items() if n > max(2, 0.3 * len(peers))}


def read_source(ledger: Ledger, source_id: str, *, start_line: int = 1, max_lines: int = 200,
                skip_boilerplate: bool = False) -> dict[str, Any]:
    text = ledger.source_text(source_id)
    if text is None:
        return {"source_id": source_id, "text_available": False, "lines": []}
    lines = text.splitlines()
    if skip_boilerplate:
        common = _boilerplate(ledger, source_id)
        numbered = [(i + 1, t) for i, t in enumerate(lines) if t not in common]
        window = [n for n in numbered if n[0] >= start_line][:max_lines]
        return {
            "source_id": source_id, "text_available": True, "total_lines": len(lines),
            "lines": [{"line": n, "text": t} for n, t in window],
            "boilerplate_lines_hidden": len(lines) - len(numbered),
            "note": "Menus and footers repeated across this site's pages are hidden; line numbers are the originals.",
        }
    start = max(1, start_line)
    window = lines[start - 1 : start - 1 + max_lines]
    return {
        "source_id": source_id,
        "text_available": True,
        "total_lines": len(lines),
        "lines": [{"line": start + i, "text": t} for i, t in enumerate(window)],
        "next_start_line": start + len(window) if start - 1 + len(window) < len(lines) else None,
        "note": "Text is pseudonymized. Quote it verbatim with the line number as the location.",
    }
