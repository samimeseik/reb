"""Coverage and reconstruction obligations — computed from the ledger, never
written by a model. Missing coverage is reported as unknown, not as absence."""

from __future__ import annotations

from collections import Counter
from typing import Any

from ..domain.errors import RebError
from ..domain.grading import best, grade_at_least, independent, strongest_authority, verifier_sufficient
from ..domain.guardrails import check_vocabulary
from ..domain.ledger import Ledger
from ..domain.models import (
    ClaimStatus,
    Layer,
    Obligation,
    ObligationStatus,
    UnknownStatus,
    Verifier,
)
from ..profiles import Profile, load_profile

OPEN_UNKNOWN = {UnknownStatus.OPEN, UnknownStatus.INVESTIGATING, UnknownStatus.BLOCKED, UnknownStatus.CONTRADICTED}


def _profile(ledger: Ledger, profile: str | None) -> Profile | None:
    name = profile or ledger.engagement.profile
    if not name:
        return None
    prof = load_profile(name)
    if ledger.engagement.mode not in prof.allowed_modes:
        raise RebError(
            "mode_not_allowed",
            f"Profile '{prof.id}' runs in modes {[m.value for m in prof.allowed_modes]}, "
            f"not '{ledger.engagement.mode.value}'.",
        )
    return prof


def layer_coverage(ledger: Ledger) -> list[dict[str, Any]]:
    rows = []
    for layer in Layer:
        claims = [c for c in ledger.data.claims.values() if c.layer == layer]
        statuses = Counter(c.status.value for c in claims)
        supported = [c.grade for c in claims if c.grade and c.status != ClaimStatus.CONTRADICTED]
        unknowns = [u for u in ledger.data.unknowns.values() if u.layer == layer and u.status in OPEN_UNKNOWN]
        rows.append(
            {
                "layer": layer.value,
                "claims": len(claims),
                "statuses": dict(statuses),
                "best_grade": best(supported).value if supported else None,
                "open_unknowns": len(unknowns),
                "state": "no_evidence" if not supported else "covered",
            }
        )
    return rows


def item_coverage(ledger: Ledger, profile: Profile) -> list[dict[str, Any]]:
    rows = []
    for item in profile.items:
        claims = [c for c in ledger.data.claims.values() if c.item == item.id]
        contradicted = [c.id for c in claims if c.status == ClaimStatus.CONTRADICTED]
        grades = [c.grade for c in claims if c.grade and c.status != ClaimStatus.CONTRADICTED]
        top = best(grades)
        item_unknowns = [u for u in ledger.data.unknowns.values() if u.item == item.id and u.status in OPEN_UNKNOWN]
        unknowns = [u.id for u in item_unknowns]
        if contradicted or any(u.status == UnknownStatus.CONTRADICTED for u in item_unknowns):
            state = "contradicted"
        elif top is None:
            state = "not_covered"
        elif grade_at_least(top, item.required_grade):
            state = "met"
        else:
            state = "below_required"
        rows.append(
            {
                "item": item.id,
                "layer": item.layer.value,
                "question": item.question,
                "question_ar": item.question_ar,
                "required_grade": item.required_grade.value,
                "best_grade": top.value if top else None,
                "state": state,
                "claims": [c.id for c in claims],
                "open_unknowns": unknowns,
                "hints": item.hints,
            }
        )
    return rows


def inspect_coverage(ledger: Ledger, profile: str | None = None) -> dict[str, Any]:
    prof = _profile(ledger, profile)
    result: dict[str, Any] = {"layers": layer_coverage(ledger)}
    if prof:
        items = item_coverage(ledger, prof)
        result["profile"] = prof.id
        result["items"] = items
        result["summary"] = dict(Counter(i["state"] for i in items))
    conjectures = [c.id for c in ledger.data.claims.values() if c.status == ClaimStatus.CONJECTURE]
    result["conjecture_claims"] = conjectures
    result["note"] = "Missing coverage means unknown, not absent."
    return result


# ------------------------------------------------------------ obligations


def record_obligation(
    ledger: Ledger,
    *,
    item: str,
    owner: str | None = None,
    case_evidence: dict[str, list[str]] | None = None,
    verifier: dict[str, Any] | None = None,
    profile: str | None = None,
) -> Obligation:
    prof = _profile(ledger, profile)
    if not prof:
        raise RebError("no_profile", "Obligations come from a profile; set one on the engagement or pass profile.")
    pitem = prof.item(item)
    if not pitem or not pitem.obligation:
        raise RebError("not_an_obligation", f"'{item}' is not an obligation item in profile '{prof.id}'.")
    ob = ledger.data.obligations.get(item) or Obligation(
        id=item, item=item, layer=pitem.layer, statement=pitem.question, required_cases=pitem.cases,
        required_grade=pitem.required_grade,
    )
    if owner:
        check_vocabulary(owner)
        ob.owner = ledger.scrub(owner)
    for case, ids in (case_evidence or {}).items():
        if case not in pitem.cases:
            raise RebError("unknown_case", f"Case '{case}' is not required for '{item}': {pitem.cases}.")
        for eid in ids:
            ledger.evidence(eid)
        ob.case_evidence[case] = list(dict.fromkeys([*ob.case_evidence.get(case, []), *ids]))
    if verifier:
        v = Verifier.model_validate(verifier)
        # A passing result is never taken from this flag alone: evaluate_obligation
        # looks for a recorded verification (see record_verification).
        if v.note:
            check_vocabulary(v.note)
            v.note = ledger.scrub(v.note)
        for eid in v.evidence_ids:
            ledger.evidence(eid)
        ob.verifier = v
    ledger.data.obligations[item] = ob
    evaluate_obligation(ledger, ob)
    return ob


def verify_operation(item: str) -> str:
    return f"verify:{item}"


def record_verification(
    ledger: Ledger,
    *,
    item: str,
    source_id: str,
    kind: str,
    result: str,
    fact: str,
    location: str | None = None,
    quote: str | None = None,
    profile: str | None = None,
) -> dict[str, Any]:
    """Record the outcome of a verification run as evidence on the source that holds it
    (the reconciliation sheet, the pilot log, the observed prediction), then attach it as the
    obligation's verifier. This is the only way a verifier can count as passing."""
    from ..providers import default_authority

    if result not in ("pass", "fail"):
        raise RebError("invalid_result", "result must be 'pass' or 'fail'.")
    source = ledger.source(source_id)
    ev = ledger.add_evidence(
        source_id=source_id,
        fact=fact,
        authority=default_authority(source.kind, source.custody),
        provider="verification",
        operation=verify_operation(item),
        location=location,
        quote=quote,
        normalized={"verifier": kind, "result": result},
    )
    prior = ledger.data.obligations.get(item)
    ids = [*(prior.verifier.evidence_ids if prior and prior.verifier and prior.verifier.kind == kind else []), ev.id]
    ob = record_obligation(
        ledger, item=item, profile=profile,
        verifier={"kind": kind, "passed": result == "pass", "evidence_ids": list(dict.fromkeys(ids))},
    )
    return {"evidence": ev.model_dump(mode="json"), "obligation": ob.model_dump(mode="json")}


def _recorded_results(ledger: Ledger, ob: Obligation) -> tuple[list, list]:
    """Verifier evidence that records a verification of this item, split by result."""
    if not ob.verifier:
        return [], []
    recorded = [
        ev for eid in ob.verifier.evidence_ids
        if (ev := ledger.data.evidence.get(eid)) and ev.operation == verify_operation(ob.item)
    ]
    return ([e for e in recorded if e.normalized.get("result") == "pass"],
            [e for e in recorded if e.normalized.get("result") == "fail"])


def _blocking_unknowns(ledger: Ledger, ob: Obligation) -> list[str]:
    """Open unknowns on this item, plus contradicted or blocking ones anywhere on its layer."""
    out = []
    for u in ledger.data.unknowns.values():
        if u.status not in OPEN_UNKNOWN:
            continue
        if u.item == ob.item or (
            u.layer == ob.layer and (u.blocking or u.status == UnknownStatus.CONTRADICTED)
        ):
            out.append(u.id)
    return out


def evaluate_obligation(ledger: Ledger, ob: Obligation) -> None:
    reasons: list[str] = []
    case_ev = [ledger.data.evidence[e] for ids in ob.case_evidence.values() for e in ids if e in ledger.data.evidence]
    claims = [c for c in ledger.data.claims.values() if c.item == ob.item]
    if not case_ev and not claims:
        ob.status, ob.reasons = ObligationStatus.UNKNOWN, ["no evidence recorded for this item"]
        return
    passes, fails = _recorded_results(ledger, ob)
    if fails or (ob.verifier and ob.verifier.passed is False):
        ob.status, ob.reasons = ObligationStatus.FAILED, [f"verifier '{ob.verifier.kind}' failed"]
        return
    if not ob.owner:
        reasons.append("missing owner (accountable role)")
    missing = [c for c in ob.required_cases if not ob.case_evidence.get(c)]
    if missing:
        reasons.append(f"missing case evidence: {', '.join(missing)}")
    weak = [
        c
        for c, ids in ob.case_evidence.items()
        if ids and not any(
            grade_at_least(ledger.data.evidence[e].grade, ob.required_grade) for e in ids if e in ledger.data.evidence
        )
    ]
    if weak:
        reasons.append(f"case evidence below grade {ob.required_grade.value}: {', '.join(weak)}")
    seen: dict[str, str] = {}
    reused = set()
    for case, ids in ob.case_evidence.items():
        for eid in ids:
            if eid in seen and seen[eid] != case:
                reused.add(eid)
            seen.setdefault(eid, case)
    if reused:
        reasons.append(f"the same evidence is cited for different cases: {', '.join(sorted(reused))}")
    if not ob.verifier or ob.verifier.passed is not True:
        reasons.append("missing passing verifier")
    elif not passes:
        reasons.append(
            f"verifier result not recorded: record the run with record_verification "
            f"(evidence with operation '{verify_operation(ob.item)}' and result 'pass')"
        )
    elif not verifier_sufficient(ob.verifier.kind, strongest_authority(case_ev)):
        reasons.append(
            f"verifier '{ob.verifier.kind}' is too weak for evidence of authority "
            f"'{strongest_authority(case_ev).value}'"
        )
    elif not _verifier_independent(passes, case_ev, ledger):
        # A verifier drawn from the same sources as the cases checks the model against itself.
        reasons.append("verifier cites no evidence independent of the case evidence (circular)")
    if any(c.status == ClaimStatus.CONTRADICTED for c in claims):
        reasons.append("contradicted claims on this item")
    blocking = _blocking_unknowns(ledger, ob)
    if blocking:
        reasons.append(f"open unknowns on this item, or blocking/contradicted on its layer: {', '.join(blocking)}")
    ob.status = ObligationStatus.READY if not reasons else ObligationStatus.OPEN
    ob.reasons = reasons


def _verifier_independent(passes: list, case_ev: list, ledger: Ledger) -> bool:
    case_sources = {e.source_id for e in case_ev}
    return any(
        all(independent(ev.source_id, cs, ledger.data.sources) for cs in case_sources) for ev in passes
    )


def obligation_ledger(ledger: Ledger, profile: str | None = None) -> dict[str, Any]:
    prof = _profile(ledger, profile)
    if not prof:
        raise RebError("no_profile", "Set a profile on the engagement or pass profile.")
    rows = []
    for pitem in prof.items:
        if not pitem.obligation:
            continue
        ob = ledger.data.obligations.get(pitem.id) or Obligation(
            id=pitem.id, item=pitem.id, layer=pitem.layer, statement=pitem.question, required_cases=pitem.cases,
            required_grade=pitem.required_grade,
        )
        evaluate_obligation(ledger, ob)
        rows.append(ob.model_dump(mode="json"))
    summary = Counter(r["status"] for r in rows)
    overall = (
        "ready"
        if rows and summary.get("ready") == len(rows)
        else "failed"
        if summary.get("failed")
        else "unknown"
        if summary.get("unknown") == len(rows)
        else "open"
    )
    return {"profile": prof.id, "overall": overall, "summary": dict(summary), "obligations": rows}
