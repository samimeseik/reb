"""Consistency checks between components — the design rules of the kernel used
in reverse: if the parts of a reconstructed organization cannot all be true at
once, at least one of them is wrong.

Values come from claims (`metric` + `value`) first, then from hypotheses
(`metric` + midpoint of `range`). A failed check never edits anything; it opens
an Unknown that names the parts in conflict.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from ..domain.ledger import Ledger
from ..domain.models import ClaimStatus, HypothesisStatus

DEFAULT_OPERATING_HOURS_PER_MONTH = 352  # 2 shifts x 8 h x 22 days — an assumption, shown as such


@dataclass
class Value:
    metric: str
    value: float
    unit: str | None
    ref: str
    kind: str  # claim | hypothesis


def _values(ledger: Ledger) -> dict[str, Value]:
    out: dict[str, Value] = {}
    for h in ledger.data.hypotheses.values():
        if h.metric and h.range and h.status not in (HypothesisStatus.REFUTED, HypothesisStatus.PROMOTED):
            out[h.metric] = Value(h.metric, (h.range.low + h.range.high) / 2, h.range.unit, h.id, "hypothesis")
    for c in ledger.data.claims.values():  # facts override inferences
        if c.metric and c.value is not None and c.status != ClaimStatus.CONTRADICTED:
            out[c.metric] = Value(c.metric, c.value, c.unit, c.id, "claim")
    return out


@dataclass
class Rule:
    id: str
    en: str
    ar: str
    inputs: list[str]
    target: str
    formula: Callable[[dict[str, float]], float]
    tolerance: float = 0.3


RULES = [
    Rule(
        "revenue_equals_volume_times_price",
        "Revenue should be close to units sold × average price.",
        "الإيراد يجب أن يقارب عدد الوحدات المباعة × متوسط السعر.",
        ["units_per_year", "price_per_unit"],
        "revenue_per_year",
        lambda v: v["units_per_year"] * v["price_per_unit"],
    ),
    Rule(
        "deals_times_commission",
        "Commission revenue should be close to deals × average deal value × commission rate.",
        "إيراد العمولة يجب أن يقارب عدد الصفقات × متوسط قيمة الصفقة × نسبة العمولة.",
        ["deals_per_year", "avg_deal_value", "commission_rate_pct"],
        "revenue_per_year",
        lambda v: v["deals_per_year"] * v["avg_deal_value"] * v["commission_rate_pct"] / 100,
    ),
    Rule(
        "littles_law",
        "Lead time should be close to work-in-progress ÷ throughput (Little's law).",
        "مدة التنفيذ يجب أن تقارب الأعمال الجارية ÷ الطاقة (قانون ليتل).",
        ["wip_units", "throughput_per_day"],
        "lead_time_days",
        lambda v: v["wip_units"] / v["throughput_per_day"],
    ),
    Rule(
        "headcount_from_workload",
        "Headcount should be close to monthly workload hours ÷ productive hours per person.",
        "عدد الموظفين يجب أن يقارب ساعات العمل الشهرية ÷ الساعات المنتجة للفرد.",
        ["workload_hours_per_month", "productive_hours_per_person_month"],
        "headcount",
        lambda v: v["workload_hours_per_month"] / v["productive_hours_per_person_month"],
    ),
]


def _line_capacity(ledger: Ledger, hours_per_month: float) -> dict[str, Any] | None:
    """Line capacity = slowest station along the routing (machines x rated rate)."""
    stations: dict[int, list] = {}
    for eq in ledger.data.equipment.values():
        if eq.station is not None and eq.rate:
            stations.setdefault(eq.station, []).append(eq)
    if not stations:
        return None
    units = {eq.rate.unit for group in stations.values() for eq in group}
    per_station = []
    for station, group in sorted(stations.items()):
        rate = sum(eq.count * (eq.rate.low + eq.rate.high) / 2 for eq in group)
        per_station.append({"station": station, "rate": rate, "unit": group[0].rate.unit,
                            "equipment": [eq.id for eq in group]})
    slowest = min(per_station, key=lambda s: s["rate"])
    result = {"stations": per_station, "bottleneck_station": slowest["station"], "units": sorted(units)}
    if len(units) == 1 and next(iter(units)).endswith("/hour"):
        result["capacity_per_month"] = round(slowest["rate"] * hours_per_month, 1)
        result["unit"] = next(iter(units)).replace("/hour", "/month")
    else:
        result["note"] = "Stations use different or non-hourly units; convert rates to one unit per hour to compute line capacity."
    return result


def check_consistency(ledger: Ledger, *, open_unknowns: bool = True) -> dict[str, Any]:
    lang = ledger.engagement.language
    values = _values(ledger)
    results = []
    for rule in RULES:
        needed = [*rule.inputs, rule.target]
        missing = [m for m in needed if m not in values]
        if missing:
            results.append({"rule": rule.id, "state": "not_enough_data", "missing": missing})
            continue
        expected = rule.formula({m: values[m].value for m in rule.inputs})
        actual = values[rule.target].value
        gap = 0.0 if max(abs(expected), abs(actual)) == 0 else (actual - expected) / max(abs(expected), abs(actual))
        ok = abs(gap) <= rule.tolerance
        refs = [values[m].ref for m in needed]
        results.append({"rule": rule.id, "state": "consistent" if ok else "inconsistent",
                        "expected": round(expected, 2), "actual": actual, "relative_gap": round(gap, 3), "refs": refs})
        if not ok and open_unknowns:
            ledger.record_unknown(
                question=(rule.ar if lang == "ar" else rule.en)
                + (f" (متوقع {expected:,.0f}، مسجّل {actual:,.0f})" if lang == "ar" else f" (expected {expected:,.0f}, recorded {actual:,.0f})"),
                recommended_probes=["Re-check the input with the weakest basis first." if lang != "ar"
                                    else "أعد فحص المُدخل ذي الأساس الأضعف أولاً."],
            )
    hours = values["operating_hours_per_month"].value if "operating_hours_per_month" in values else DEFAULT_OPERATING_HOURS_PER_MONTH
    line = _line_capacity(ledger, hours)
    if line:
        line["hours_per_month"] = hours
        line["hours_assumed"] = "operating_hours_per_month" not in values
        if "capacity_per_month" in line and "output_per_month" in values:
            out = values["output_per_month"]
            ratio = out.value / line["capacity_per_month"] if line["capacity_per_month"] else None
            line["claimed_output"] = out.value
            line["utilization"] = round(ratio, 2) if ratio is not None else None
            if ratio is not None and ratio > 1.0:
                line["state"] = "inconsistent"
                if open_unknowns:
                    ledger.record_unknown(
                        question=("الإنتاج المُعلن يتجاوز طاقة الخط المحسوبة من المعدات" if lang == "ar"
                                  else "Stated output exceeds the line capacity computed from the equipment")
                        + f" ({out.value:,.0f} > {line['capacity_per_month']:,.0f} {line['unit']})",
                        layer="equipment",
                        recommended_probes=["Count shifts and machines on site; check for subcontracting."],
                    )
            else:
                line["state"] = "consistent"
        results.append({"rule": "line_capacity", **line})
    return {"checks": results,
            "summary": {s: sum(1 for r in results if r.get("state") == s)
                        for s in ("consistent", "inconsistent", "not_enough_data")}}
