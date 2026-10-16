"""Evidence grading, source independence and claim status.

Grades are computed, never asserted:
  grade = worst_of(authority_base, custody_cap, confidence_cap)
A claim is `triangulated` only when two supporting pieces of evidence come from
sources that share no controller and no derivation ancestry.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from .models import (
    Authority,
    Claim,
    ClaimStatus,
    Confidence,
    Custody,
    Evidence,
    Grade,
    Hypothesis,
    HypothesisBasis,
    HypothesisConfidence,
    Source,
    SourceKind,
)

GRADE_ORDER = [Grade.A, Grade.B, Grade.C, Grade.D, Grade.E]

AUTHORITY_BASE: dict[Authority, Grade] = {
    Authority.SYSTEM_RECORD: Grade.A,
    Authority.DIRECT_OBSERVATION: Grade.A,
    Authority.GOVERNING_DOCUMENT: Grade.B,
    Authority.PUBLIC_RECORD: Grade.B,
    Authority.TESTIMONY: Grade.D,
    Authority.PUBLIC_SIGNAL: Grade.D,
    Authority.ANALYST_INFERENCE: Grade.E,
}

CONFIDENCE_CAP: dict[Confidence, Grade] = {
    Confidence.OBSERVED: Grade.A,
    Confidence.DERIVED: Grade.A,
    Confidence.INFERRED: Grade.D,
}

WEAK_AUTHORITIES = {Authority.TESTIMONY, Authority.PUBLIC_SIGNAL, Authority.ANALYST_INFERENCE}

AUTHORITY_RANK = [
    Authority.SYSTEM_RECORD,
    Authority.DIRECT_OBSERVATION,
    Authority.GOVERNING_DOCUMENT,
    Authority.PUBLIC_RECORD,
    Authority.TESTIMONY,
    Authority.PUBLIC_SIGNAL,
    Authority.ANALYST_INFERENCE,
]

# Verifier kinds, weakest first. A verifier can only close an obligation whose
# case evidence it is strong enough to stand behind.
VERIFIER_RANK = ["desk_review", "reconciliation", "conformance", "prediction", "pilot"]


def custody_cap(source: Source) -> Grade:
    match source.custody:
        case Custody.SUBJECT_HELD:
            # The organization controls the content: it can be edited before handover.
            return Grade.C
        case Custody.ISSUER_VERIFIABLE | Custody.CAPTURED_LIVE:
            return Grade.A
        case Custody.THIRD_PARTY:
            return Grade.A if source.independent_channel else Grade.B
        case Custody.PUBLIC:
            return Grade.B
    return Grade.E


def worst(*grades: Grade) -> Grade:
    return max(grades, key=GRADE_ORDER.index)


def best(grades: Iterable[Grade]) -> Grade | None:
    grades = list(grades)
    return min(grades, key=GRADE_ORDER.index) if grades else None


def grade_at_least(grade: Grade | None, required: Grade) -> bool:
    return grade is not None and GRADE_ORDER.index(grade) <= GRADE_ORDER.index(required)


def unbacked_observation(source: Source | None) -> bool:
    """An observation typed by the analyst with no captured artifact (photo, count sheet)."""
    return bool(source) and source.kind == SourceKind.OBSERVATION and not source.artifact_ids


def compute_grade(authority: Authority, confidence: Confidence, source: Source) -> Grade:
    # A typed note of a single walk-through is not as strong as a record captured live:
    # without an artifact it can be mistaken, staged or recalled wrongly.
    artifact_cap = Grade.B if unbacked_observation(source) else Grade.A
    return worst(AUTHORITY_BASE[authority], CONFIDENCE_CAP[confidence], custody_cap(source), artifact_cap)


def ancestry(source_id: str, sources: Mapping[str, Source]) -> set[str]:
    """The source itself plus every source it was (transitively) derived from."""
    seen: set[str] = set()
    stack = [source_id]
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        src = sources.get(current)
        if src:
            stack.extend(src.upstream_ids)
    return seen


def independent(a: str, b: str, sources: Mapping[str, Source]) -> bool:
    """Two sources are independent when they share no controller and no ancestry."""
    if a == b:
        return False
    anc_a, anc_b = ancestry(a, sources), ancestry(b, sources)
    if anc_a & anc_b:
        return False
    controllers_a = {sources[s].controller.strip().lower() for s in anc_a if s in sources}
    controllers_b = {sources[s].controller.strip().lower() for s in anc_b if s in sources}
    if controllers_a & controllers_b:
        return False
    return _contexts_overlap(sources.get(a), sources.get(b))


def _contexts_overlap(a: Source | None, b: Source | None) -> bool:
    """If both sources declare an observation period, the periods must overlap."""
    if not a or not b:
        return True
    ca, cb = a.context, b.context
    if ca.period_start and ca.period_end and cb.period_start and cb.period_end:
        return ca.period_start <= cb.period_end and cb.period_start <= ca.period_end
    return True


def evaluate_claim(
    claim: Claim, evidence: Mapping[str, Evidence], sources: Mapping[str, Source]
) -> tuple[ClaimStatus, Grade | None]:
    supporting = [evidence[e] for e in claim.evidence_ids if e in evidence]
    grade = best(e.grade for e in supporting)
    if claim.contradicting_evidence_ids:
        return ClaimStatus.CONTRADICTED, grade
    if not supporting:
        return ClaimStatus.CONJECTURE, None
    # Triangulation needs two independent sources, and at least one of the two pieces of
    # evidence must be a record, an observation, a document or a public record:
    # several people saying the same thing is still testimony.
    # An observation without an artifact can only corroborate when the claim has unbacked
    # observations on at least two different days (one staged day is not enough).
    unbacked_days = {
        e.as_of or e.source_id for e in supporting if unbacked_observation(sources.get(e.source_id))
    }
    for i, a in enumerate(supporting):
        for b in supporting[i + 1 :]:
            if a.authority in WEAK_AUTHORITIES and b.authority in WEAK_AUTHORITIES:
                continue
            if len(unbacked_days) < 2 and any(
                unbacked_observation(sources.get(e.source_id)) for e in (a, b)
            ):
                continue
            if independent(a.source_id, b.source_id, sources):
                return ClaimStatus.TRIANGULATED, grade
    return ClaimStatus.SINGLE_SOURCE, grade


def strongest_authority(items: Iterable[Evidence]) -> Authority | None:
    items = list(items)
    if not items:
        return None
    return min((e.authority for e in items), key=AUTHORITY_RANK.index)


def verifier_sufficient(verifier_kind: str, case_authority: Authority | None) -> bool:
    """Desk review cannot close a claim originally grounded in system records or
    direct observation; those need at least a reconciliation."""
    if verifier_kind not in VERIFIER_RANK:
        return False
    if case_authority in (Authority.SYSTEM_RECORD, Authority.DIRECT_OBSERVATION):
        return VERIFIER_RANK.index(verifier_kind) >= VERIFIER_RANK.index("reconciliation")
    return True


# ------------------------------------------------------------ hypotheses


def hypothesis_confidence(
    hypothesis: Hypothesis,
    evidence: Mapping[str, Evidence],
    sources: Mapping[str, Source],
    upstream: Mapping[str, HypothesisConfidence] | None = None,
) -> HypothesisConfidence:
    """Computed, never chosen:
    - archetype pattern alone, or signals that are only inferences -> low
    - signals from one source (or one controller) -> medium
    - signals from two or more independent sources -> high
    - calculation -> the weakest of its inputs (and of its own signals, if any)
    """
    order = [HypothesisConfidence.LOW, HypothesisConfidence.MEDIUM, HypothesisConfidence.HIGH]
    signals = [evidence[e] for e in hypothesis.signal_evidence_ids if e in evidence]
    signals = [e for e in signals if e.authority != Authority.ANALYST_INFERENCE]
    if not signals:
        own = HypothesisConfidence.LOW
    else:
        own = HypothesisConfidence.MEDIUM
        source_ids = sorted({e.source_id for e in signals})
        if any(independent(a, b, sources) for i, a in enumerate(source_ids) for b in source_ids[i + 1 :]):
            own = HypothesisConfidence.HIGH
    if hypothesis.basis == HypothesisBasis.CALCULATION:
        inputs = [(upstream or {}).get(h) for h in hypothesis.derived_from]
        inputs = [c for c in inputs if c is not None]
        if not inputs:
            return HypothesisConfidence.LOW
        weakest = min(inputs, key=order.index)
        return weakest if not signals else min(weakest, own, key=order.index)
    if hypothesis.basis == HypothesisBasis.ARCHETYPE and not signals:
        return HypothesisConfidence.LOW
    return own
