"""Derived analyses. Results are recorded as `derived` evidence linked to the
source they were computed from, so they inherit that source's grade cap."""

from __future__ import annotations

import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any

from ..domain.errors import RebError

from ..domain.ledger import Ledger
from ..domain.models import Authority, ClaimKind, Confidence, SourceKind, UnknownStatus
from ..providers import spreadsheet, whatsapp
from ..timeparse import infer_dayfirst, parse_timestamp

# ---------------------------------------------------------------- event logs


def _events_from_table(ledger: Ledger, source_id: str, case_col: str, activity_col: str, time_col: str):
    rows = spreadsheet.read_rows(ledger.read_original(source_id))
    if rows and not {case_col, activity_col, time_col} <= set(rows[0]):
        raise RebError("missing_columns", f"Columns not found. Available: {list(rows[0])}.")
    dayfirst, _ = infer_dayfirst(r.get(time_col) for r in rows)
    events = []
    for i, row in enumerate(rows, start=2):
        ts = parse_timestamp(row.get(time_col), dayfirst)
        case, act = row.get(case_col), row.get(activity_col)
        if ts and case not in (None, "") and act not in (None, ""):
            events.append((str(case), str(act).strip(), ts, f"row {i}"))
    return events


def _events_from_chat(ledger: Ledger, source_id: str, activity_map: dict[str, list[str]], case_pattern: str):
    text = ledger.source_text(source_id)
    if text is None:
        raise RebError("no_text", "The chat source has no stored text.")
    case_re = re.compile(case_pattern)
    lowered = {act: [k.casefold() for k in kws] for act, kws in activity_map.items()}
    events = []
    for msg in whatsapp.parse_text(text):
        m = case_re.search(msg.body)
        if not m:
            continue
        case = m.group(1) if m.groups() else m.group(0)
        body = msg.body.casefold()
        for act, keywords in lowered.items():
            if any(k in body for k in keywords):
                events.append((case, act, msg.timestamp, f"line {msg.line}"))
    return events


def _hours(a: datetime, b: datetime) -> float:
    return round((b - a).total_seconds() / 3600, 2)


def _pct(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    idx = min(len(ordered) - 1, max(0, int(round(q * (len(ordered) - 1)))))
    return ordered[idx]


def discover_process(events: list[tuple[str, str, datetime, str]]) -> dict[str, Any]:
    """Directly-follows graph, variants, cycle times and rework — the core of
    process mining without external dependencies (export to pm4py for more)."""
    by_case: dict[str, list[tuple[str, datetime, str]]] = defaultdict(list)
    for case, act, ts, loc in events:
        by_case[case].append((act, ts, loc))
    variants: Counter[tuple[str, ...]] = Counter()
    edges: dict[tuple[str, str], list[float]] = defaultdict(list)
    cycle: list[float] = []
    rework_cases = []
    for case, evs in by_case.items():
        evs.sort(key=lambda e: e[1])
        trace = tuple(a for a, _, _ in evs)
        variants[trace] += 1
        for (a1, t1, _), (a2, t2, _) in zip(evs, evs[1:]):
            edges[(a1, a2)].append(_hours(t1, t2))
        if len(evs) > 1:
            cycle.append(_hours(evs[0][1], evs[-1][1]))
        repeated = [a for a, n in Counter(trace).items() if n > 1]
        if repeated:
            rework_cases.append({"case": case, "repeated": repeated})
    return {
        "cases": len(by_case),
        "events": len(events),
        "activities": sorted({a for _, a, _, _ in events}),
        "variants": [
            {"trace": list(t), "cases": n, "share": round(n / max(1, len(by_case)), 3)}
            for t, n in variants.most_common(20)
        ],
        "edges": [
            {
                "from": a,
                "to": b,
                "count": len(d),
                "median_hours": round(statistics.median(d), 2),
                "p90_hours": _pct(d, 0.9),
            }
            for (a, b), d in sorted(edges.items(), key=lambda kv: -len(kv[1]))
        ],
        "cycle_time_hours": {
            "median": round(statistics.median(cycle), 2) if cycle else None,
            "p90": _pct(cycle, 0.9) if cycle else None,
            "max": max(cycle) if cycle else None,
        },
        "rework": {"cases": len(rework_cases), "examples": rework_cases[:10]},
        "case_examples": {c: [loc for _, _, loc in evs[:3]] for c, evs in list(by_case.items())[:5]},
    }


def to_mermaid(result: dict[str, Any], min_count: int = 1) -> str:
    ids = {a: f"A{i}" for i, a in enumerate(result["activities"])}
    lines = ["flowchart LR"]
    for act, nid in ids.items():
        lines.append(f'    {nid}["{act}"]')
    for e in result["edges"]:
        if e["count"] >= min_count:
            lines.append(f'    {ids[e["from"]]} -->|"{e["count"]}× · {e["median_hours"]}h"| {ids[e["to"]]}')
    return "\n".join(lines)


def analyze_event_log(
    ledger: Ledger,
    source_id: str,
    *,
    case_column: str | None = None,
    activity_column: str | None = None,
    time_column: str | None = None,
    activity_map: dict[str, list[str]] | None = None,
    case_pattern: str | None = None,
    entity: str | None = None,
) -> dict[str, Any]:
    src = ledger.source(source_id)
    if src.kind == SourceKind.CHAT_EXPORT:
        if not activity_map or not case_pattern:
            raise RebError(
                "missing_mapping",
                "Chat exports need activity_map ({activity: [keywords]}) and case_pattern (regex with one group).",
            )
        events = _events_from_chat(ledger, source_id, activity_map, case_pattern)
        limitations = [
            "Events reconstructed from message keywords: steps never mentioned in this chat are missing.",
            "Activity mapping was supplied by the analyst; different keywords give a different process.",
        ]
    else:
        if not (case_column and activity_column and time_column):
            raise RebError("missing_columns", "Tables need case_column, activity_column and time_column.")
        events = _events_from_table(ledger, source_id, case_column, activity_column, time_column)
        limitations = ["Only activities recorded in this export appear; off-system work is invisible."]
    if not events:
        raise RebError("no_events", "No events could be built from this source with the given mapping.")
    result = discover_process(events)
    result["mermaid"] = to_mermaid(result)
    ct = result["cycle_time_hours"]
    top = result["variants"][0]
    ev = ledger.add_evidence(
        source_id=source_id,
        fact=(
            f"Process discovered from {result['cases']} cases / {result['events']} events: "
            f"median cycle time {ct['median']}h (p90 {ct['p90']}h); most common path "
            f"{' → '.join(top['trace'])} ({top['cases']} cases); {result['rework']['cases']} cases with rework."
        ),
        authority=Authority.SYSTEM_RECORD,
        confidence=Confidence.DERIVED,
        provider="process_mining",
        operation="discover_process",
        entity=entity,
        layer="operations",
        normalized={k: v for k, v in result.items() if k != "mermaid"},
        limitations=limitations,
    )
    return {"evidence_id": ev.id, "grade": ev.grade.value, "limitations": limitations, **result}


# ----------------------------------------------------------------- invoices

CREDIT_NOTE_TYPES = {"IADE", "CREDITNOTE", "381"}


def analyze_invoices(ledger: Ledger, source_ids: list[str], *, direction: str = "sales") -> dict[str, Any]:
    """Revenue (sales) or spend (purchases) concentration across e-invoices.
    Reads the parsed (pseudonymized) invoice evidence, not the original files."""
    if direction not in ("sales", "purchases"):
        raise RebError("invalid_input", "direction must be 'sales' or 'purchases'.")
    if not source_ids:
        raise RebError("invalid_input", "Give at least one e-invoice source id.")
    invoices: dict[str, dict[str, Any]] = {}
    duplicates = 0
    for sid in source_ids:
        src = ledger.source(sid)
        if src.kind != SourceKind.EINVOICE:
            raise RebError("not_einvoice", f"{sid} is not an e-invoice source.")
        parsed = [e for e in ledger.data.evidence.values() if e.source_id == sid and e.operation == "parse_invoice"]
        if not parsed:
            raise RebError("no_invoices", f"No invoices were parsed from {sid}.")
        for ev in parsed:
            inv = ev.normalized
            key = inv.get("uuid") or f"{inv.get('id')}|{inv.get('issue_date')}"
            if key in invoices:
                duplicates += 1
                continue
            invoices[key] = inv
    totals: Counter[str] = Counter()
    currencies: set[str] = set()
    dates: list[str] = []
    credit_notes = 0
    for inv in invoices.values():
        party = inv["customer"] if direction == "sales" else inv["supplier"]
        key = party.get("tax_id") or "unknown"
        sign = -1 if (inv.get("type") or "").upper() in CREDIT_NOTE_TYPES else 1
        credit_notes += sign < 0
        totals[key] += sign * (inv.get("payable") or 0)
        currencies.add(inv.get("currency") or "?")
        if inv.get("issue_date"):
            dates.append(inv["issue_date"])
    grand = sum(totals.values())
    shares = [(k, v, v / grand if grand else 0) for k, v in totals.most_common()]
    hhi = round(sum((s * 100) ** 2 for _, _, s in shares))
    result = {
        "direction": direction,
        "invoices": len(invoices),
        "duplicates_skipped": duplicates,
        "credit_notes": credit_notes,
        "counterparties": len(totals),
        "total": round(grand, 2),
        "currencies": sorted(currencies),
        "period": [min(dates), max(dates)] if dates else None,
        "top": [{"tax_id": k, "share": round(s, 3), "amount": round(v, 2)} for k, v, s in shares[:10]],
        "hhi": hhi,
        "top1_share": round(shares[0][2], 3) if shares else None,
    }
    limitations = [
        "Covers only the invoices ingested; missing months or off-book sales are not represented.",
        "Counterparties are identified by tax id. Check related parties separately.",
    ]
    if len(currencies) > 1:
        limitations.append("Mixed currencies were summed without conversion.")
    # Attach to the weakest input so the result never out-grades its least reliable source.
    from ..domain.grading import GRADE_ORDER, custody_cap

    weakest = max(source_ids, key=lambda s: GRADE_ORDER.index(custody_cap(ledger.source(s))))
    ev = ledger.add_evidence(
        source_id=weakest,
        fact=(
            f"{len(invoices)} {direction} invoices, {len(totals)} counterparties, total {result['total']} "
            f"{'/'.join(result['currencies'])}; largest counterparty share {result['top1_share']}; HHI {hhi}."
        ),
        authority=Authority.SYSTEM_RECORD,
        confidence=Confidence.DERIVED,
        provider="invoices",
        operation="analyze_invoices",
        layer="revenue" if direction == "sales" else "supply",
        normalized=result | {"source_ids": sorted(source_ids)},
        limitations=limitations,
    )
    return {"evidence_id": ev.id, "grade": ev.grade.value, "limitations": limitations, **result}


# ------------------------------------------------------ stated vs enacted


def compare_stated_vs_enacted(
    ledger: Ledger, *, metric: str, entity: str | None = None, tolerance: float = 0.15
) -> dict[str, Any]:
    """Compare what documents/people state against what records/observation show.
    Only claims about the same entity and in the same unit are compared. A gap
    beyond the tolerance opens (or reopens) an Unknown with status `contradicted`."""
    claims = [
        c
        for c in ledger.data.claims.values()
        if c.metric == metric and (entity is None or c.entity == entity) and c.value is not None
    ]
    stated = [c for c in claims if c.kind == ClaimKind.STATED]
    enacted = [c for c in claims if c.kind == ClaimKind.ENACTED]
    if not stated or not enacted:
        return {
            "metric": metric,
            "entity": entity,
            "comparable": False,
            "reason": "Need at least one stated and one enacted claim with a value for this metric.",
            "stated": [c.id for c in stated],
            "enacted": [c.id for c in enacted],
        }
    pairs, skipped, unknowns = [], [], []
    for s in stated:
        for e in enacted:
            if s.entity != e.entity:
                continue
            if (s.unit or "") != (e.unit or ""):
                skipped.append({"stated_claim": s.id, "enacted_claim": e.id, "reason": "different units"})
                continue
            base = max(abs(s.value), abs(e.value))
            gap = 0.0 if base == 0 else (e.value - s.value) / base
            ok = abs(gap) <= tolerance
            pairs.append(
                {
                    "stated_claim": s.id,
                    "stated_value": s.value,
                    "enacted_claim": e.id,
                    "enacted_value": e.value,
                    "unit": e.unit,
                    "entity": e.entity,
                    "relative_gap": round(gap, 3),
                    "within_tolerance": ok,
                }
            )
            if ok:
                continue
            unk = ledger.record_unknown(
                question=(
                    f"Why does the stated {metric} ({s.value:g} {s.unit or ''}) differ from the "
                    f"enacted {metric} ({e.value:g} {e.unit or ''})?"
                ).replace("  ", " "),
                layer=e.layer,
                entity=e.entity,
                item=e.item or s.item,
                status="contradicted",
                required_authority="system_record",
                recommended_probes=[
                    "Extend the record period and re-measure.",
                    "Ask the person who stated it what period or case they had in mind.",
                    "Check whether both measure the same thing (definitions, units, start and end events).",
                ],
                supporting_evidence_ids=e.evidence_ids,
                contradicting_evidence_ids=s.evidence_ids,
            )
            if unk.status != UnknownStatus.CONTRADICTED:
                ledger.reopen_unknown(unk, UnknownStatus.CONTRADICTED)
            unknowns.append(unk.id)
    return {
        "metric": metric,
        "entity": entity,
        "comparable": bool(pairs),
        "pairs": pairs,
        "skipped": skipped,
        "opened_unknowns": unknowns,
    }
