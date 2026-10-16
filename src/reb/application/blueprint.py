"""The blueprint: how an organization works (known / inferred / unknown per
component), how to rebuild it better, and how to confirm what is inferred."""

from __future__ import annotations

import datetime as dt
import urllib.parse
from typing import Any

from ..archetypes import apply_archetype, archetype, suggest
from ..domain.errors import RebError
from ..domain.ledger import Ledger
from ..domain.models import (
    COMPONENT_LAYER,
    ClaimStatus,
    Component,
    DesignKind,
    HypothesisConfidence,
    HypothesisStatus,
    Level,
    Replicability,
    UnknownStatus,
)
from ..kernel import blocks_for_component, family
from ..providers import web
from .analysis import to_mermaid
from .consistency import check_consistency
from .ingest import record_observation

COMPONENT_NAMES = {
    Component.IDENTITY: ("Identity & legal status", "الهوية والوضع القانوني"),
    Component.CUSTOMERS: ("Customers & segments", "العملاء والشرائح"),
    Component.OFFER: ("Offer & pricing", "العرض والتسعير"),
    Component.REVENUE_MODEL: ("Revenue model", "نموذج الإيراد"),
    Component.ACQUISITION: ("Acquisition & sales", "الاستقطاب ومسار البيع"),
    Component.OPERATIONS: ("Core operations", "العمليات الأساسية"),
    Component.TEAM: ("Team & structure", "الفريق والهيكل"),
    Component.SYSTEMS: ("Systems & data", "الأنظمة والبيانات"),
    Component.PARTNERS: ("Suppliers & partners", "الموردون والشركاء"),
    Component.ASSETS: ("Assets & equipment", "الأصول والمعدات"),
    Component.ECONOMICS: ("Unit economics & costs", "اقتصاديات الوحدة والتكاليف"),
    Component.MOAT: ("Culture & advantage", "الثقافة والميزة"),
}

LAYER_TO_COMPONENT = {}
for _c, _l in COMPONENT_LAYER.items():
    LAYER_TO_COMPONENT.setdefault(_l, _c)

OPEN = {UnknownStatus.OPEN, UnknownStatus.INVESTIGATING, UnknownStatus.BLOCKED, UnknownStatus.CONTRADICTED}
CONF_WEIGHT = {HypothesisConfidence.HIGH: 0.6, HypothesisConfidence.MEDIUM: 0.4, HypothesisConfidence.LOW: 0.15}
LEVEL = {Level.HIGH: 3, Level.MEDIUM: 2, Level.LOW: 1}


# ------------------------------------------------------------------ intake


def ingest_website(ledger: Ledger, url: str, *, max_pages: int = 15, delay: float = 0.5) -> dict[str, Any]:
    """Crawl a public site into public-signal sources plus a footprint observation."""
    crawl = web.crawl(url, max_pages=max_pages, delay=delay)
    if not crawl.pages:
        raise RebError("crawl_failed", f"No page could be read from {url}: {crawl.errors[:3] or crawl.skipped_by_robots[:3]}")
    host = urllib.parse.urlsplit(crawl.start).netloc
    today = dt.date.today().isoformat()
    source_ids = []
    for page in crawl.pages:
        text = f"{page.title}\n{page.url}\n\n{page.text}"
        src, _ = ledger.add_source(
            content=text.encode("utf-8"),
            kind="public_signal",
            custody="public",
            title=page.title or page.url,
            origin_party=host,
            controller=host,
            legal_basis=f"{page.url} (retrieved {today})",
            sensitivity="public",
            text=text,
        )
        source_ids.append(src.id)
    fp = web.footprint(crawl)
    facts = []
    if fp["cms"]:
        facts.append({"fact": f"The site declares the generator {', '.join(fp['cms'])}.", "layer": "systems"})
    if fp["tools"]:
        facts.append({"fact": f"The site loads or links: {', '.join(fp['tools'])}.", "layer": "systems"})
    if fp["contact_channels"]:
        facts.append({"fact": f"Public contact channels: {', '.join(fp['contact_channels'])}.", "layer": "customer"})
    mail = web.mail_provider(host.removeprefix("www."))
    if mail:
        facts.append({"fact": f"The domain's mail is handled by {mail} (MX record).", "layer": "systems"})
    obs = None
    if facts:
        obs = record_observation(
            ledger, title=f"Technical footprint of {host}", note=f"Read from the HTML served to any visitor of {host}.",
            observer_role="analyst", site=crawl.start, when=today, facts=facts, public_premises=True,
        )
    return {
        "pages": len(crawl.pages),
        "source_ids": source_ids,
        "footprint": fp,
        "mail_provider": mail,
        "footprint_evidence": [e["id"] for e in obs["evidence"]] if obs else [],
        "skipped_by_robots": crawl.skipped_by_robots,
        "errors": crawl.errors,
        "report_documents": crawl.documents,
        "js_rendered_pages": crawl.js_rendered,
        "next_steps": [
            "Ingest the report PDFs above (kind financial_statement or document, custody public, URL as legal_basis): "
            "annual and activity reports are usually the richest traces.",
            "Open JavaScript-rendered pages in a browser; the crawler only sees their empty shell.",
        ] if (crawl.documents or crawl.js_rendered) else [],
        "suggested_archetypes": suggest(" ".join(p.title + " " + p.text[:3000] for p in crawl.pages)),
    }


def start_blueprint(ledger: Ledger, *, url: str | None = None, archetype_id: str | None = None,
                    max_pages: int = 15) -> dict[str, Any]:
    """Collect the public site (if given), choose an archetype and seed the blueprint."""
    out: dict[str, Any] = {}
    if url:
        out["website"] = ingest_website(ledger, url, max_pages=max_pages)
    chosen = archetype_id
    if not chosen and url and out["website"]["suggested_archetypes"]:
        chosen = out["website"]["suggested_archetypes"][0]["archetype"]
    if chosen:
        out["archetype"] = apply_archetype(ledger, chosen)
    else:
        out["archetype"] = None
        out["next"] = "Choose an archetype with list_archetypes, then apply it."
    return out


# ------------------------------------------------------------------ build


def _component_of_claim(claim) -> Component:
    return claim.component or LAYER_TO_COMPONENT.get(claim.layer, Component.MOAT)


def _component_of_unknown(unknown) -> Component | None:
    if unknown.item and unknown.item.startswith("bp."):
        try:
            return Component(unknown.item[3:])
        except ValueError:
            pass
    return LAYER_TO_COMPONENT.get(unknown.layer) if unknown.layer else None


def _midpoint(r) -> str:
    return f"{r.low:,.0f}" if r.low == r.high else f"{r.low:,.0f}–{r.high:,.0f}"


def build_blueprint(ledger: Ledger) -> dict[str, Any]:
    ledger.reevaluate()
    ledger.reevaluate_hypotheses()
    lang = ledger.engagement.language
    arch = archetype(ledger.data.archetype) if ledger.data.archetype else None
    components = []
    for comp in Component:
        claims = [c for c in ledger.data.claims.values() if _component_of_claim(c) == comp and c.status != ClaimStatus.CONJECTURE]
        hyps = [h for h in ledger.data.hypotheses.values() if h.component == comp and h.status != HypothesisStatus.PROMOTED]
        live = [h for h in hyps if h.status != HypothesisStatus.REFUTED]
        unknowns = [u for u in ledger.data.unknowns.values() if _component_of_unknown(u) == comp and u.status in OPEN]
        score = sum(1.0 if c.status == ClaimStatus.TRIANGULATED else 0.7 for c in claims if c.status != ClaimStatus.CONTRADICTED)
        score += sum(CONF_WEIGHT[h.confidence] for h in live)
        comp_blocks = blocks_for_component(comp)
        fam = family(arch.family) if arch else None
        components.append({
            "component": comp.value,
            "name": COMPONENT_NAMES[comp][1 if lang == "ar" else 0],
            "blocks": [b.id for b in comp_blocks],
            "how_built": {
                "elements": [e.get(lang) for b in comp_blocks for e in b.elements],
                "rules": [r.get(lang) for b in comp_blocks for r in b.rules],
                "family_notes": [n.get(lang) for b in comp_blocks for n in (fam.blocks.get(b.id, []) if fam else [])],
            },
            "look_for": [{"trace": t.get(lang), "strength": t.strength} for b in comp_blocks for t in b.traces]
            + [{"trace": t.get(lang), "strength": t.strength}
               for t in (fam.traces if fam else []) if t.block in {b.id for b in comp_blocks}],
            "known": [{"id": c.id, "statement": c.statement, "grade": c.grade.value if c.grade else None,
                       "status": c.status.value} for c in claims],
            "inferred": [{"id": h.id, "statement": h.statement, "basis": h.basis.value, "confidence": h.confidence.value,
                          "status": h.status.value, "range": h.range.model_dump() if h.range else None,
                          "test": h.test, "signals": h.signal_evidence_ids}
                         for h in sorted(live, key=lambda h: list(HypothesisConfidence).index(h.confidence), reverse=True)],
            "refuted": [{"id": h.id, "statement": h.statement} for h in hyps if h.status == HypothesisStatus.REFUTED],
            "unknown": [{"id": u.id, "question": u.question, "status": u.status.value,
                         "probe": u.recommended_probes[0] if u.recommended_probes else None} for u in unknowns],
            "completeness": min(100, round(score / 3 * 100)),
        })

    process = _process(ledger, arch, lang)
    team = next(c for c in components if c["component"] == "team")
    numbers = [
        {"id": c.id, "statement": c.statement, "metric": c.metric, "value": c.value, "unit": c.unit, "kind": "known"}
        for c in ledger.data.claims.values() if c.value is not None
    ] + [
        {"id": h.id, "statement": h.statement, "metric": h.metric, "range": _midpoint(h.range), "unit": h.range.unit,
         "kind": "inferred", "confidence": h.confidence.value, "assumptions": h.assumptions}
        for h in ledger.data.hypotheses.values()
        if h.range and h.status not in (HypothesisStatus.REFUTED, HypothesisStatus.PROMOTED)
    ]
    consistency = check_consistency(ledger, open_unknowns=False)
    return {
        "identity": {
            "subject": ledger.engagement.subject,
            "mode": ledger.engagement.mode.value,
            "archetype": arch.id if arch else None,
            "archetype_name": (arch.name_ar if lang == "ar" else arch.name) if arch else None,
            "family": arch.family if arch else None,
            "sources": len(ledger.data.sources),
            "evidence": len(ledger.data.evidence),
        },
        "components": components,
        "process": process,
        "organization": {"known": team["known"], "inferred": team["inferred"],
                         "key_people": [c.statement for c in ledger.data.claims.values()
                                        if c.replicability == Replicability.NON_TRANSFERABLE and _component_of_claim(c) == Component.TEAM]},
        "equipment": [e.model_dump(mode="json") for e in sorted(ledger.data.equipment.values(), key=lambda e: e.station or 99)],
        "numbers": numbers,
        "consistency": consistency,
        "redesign": _redesign(ledger),
        "verification_plan": verification_plan(ledger),
        "calibration": calibration(ledger),
        "overall_completeness": round(sum(c["completeness"] for c in components) / len(components)),
    }


def _process(ledger: Ledger, arch, lang: str) -> dict[str, Any]:
    mined = [e for e in ledger.data.evidence.values() if e.operation == "discover_process"]
    if mined:
        latest = mined[-1].normalized
        top = latest["variants"][0]["trace"] if latest.get("variants") else []
        return {"basis": "event_log", "evidence_id": mined[-1].id, "stages": top, "mermaid": to_mermaid(latest)}
    if arch and arch.processes:
        stages = [p.get(lang) for p in arch.processes]
        lines = ["flowchart LR"] + [f'    S{i}["{s}"]' for i, s in enumerate(stages)]
        lines += [f"    S{i} --> S{i + 1}" for i in range(len(stages) - 1)]
        return {"basis": "archetype", "stages": stages, "mermaid": "\n".join(lines)}
    return {"basis": None, "stages": [], "mermaid": None}


def _redesign(ledger: Ledger) -> dict[str, Any]:
    by_comp: dict[str, dict[str, list]] = {}
    for d in ledger.data.design.values():
        if d.kind == DesignKind.BUILD_STEP:
            continue
        by_comp.setdefault(d.component.value, {}).setdefault(d.kind.value, []).append(
            {"id": d.id, "statement": d.statement, "refs": d.refs})
    for c in ledger.data.claims.values():  # replicability tags feed copy / cannot-copy
        kind = {"codifiable": "copy", "non_transferable": "cannot_copy", "needs_asset": "cannot_copy"}.get(c.replicability.value)
        if kind:
            by_comp.setdefault(_component_of_claim(c).value, {}).setdefault(kind, []).append(
                {"id": c.id, "statement": c.statement, "refs": [c.id]})
    phase_order = lambda d: (d.phase or "zz")  # noqa: E731
    recipe = [{"id": d.id, "component": d.component.value, "phase": d.phase, "statement": d.statement, "refs": d.refs,
               "cost": d.cost.model_dump() if d.cost else None}
              for d in sorted((d for d in ledger.data.design.values() if d.kind == DesignKind.BUILD_STEP), key=phase_order)]
    return {"by_component": by_comp, "build_recipe": recipe}


def verification_plan(ledger: Ledger, limit: int = 10) -> list[dict[str, Any]]:
    """Cheapest high-impact tests first: impact x uncertainty / cost."""
    uncertainty = {HypothesisConfidence.LOW: 3, HypothesisConfidence.MEDIUM: 2, HypothesisConfidence.HIGH: 1}
    candidates = [h for h in ledger.data.hypotheses.values() if h.status == HypothesisStatus.PROPOSED and h.test]
    ranked = sorted(candidates, key=lambda h: -(LEVEL[h.impact] * uncertainty[h.confidence] / LEVEL[h.test_cost]))
    return [{"hypothesis": h.id, "component": h.component.value, "statement": h.statement, "test": h.test,
             "impact": h.impact.value, "confidence": h.confidence.value, "test_cost": h.test_cost.value}
            for h in ranked[:limit]]


def calibration(ledger: Ledger) -> dict[str, Any]:
    """Owner verdicts per confidence level: are 'high' hypotheses really right more often?"""
    table: dict[str, dict[str, int]] = {}
    for h in ledger.data.hypotheses.values():
        if h.owner_verdict:
            row = table.setdefault(h.confidence.value, {"correct": 0, "partial": 0, "wrong": 0})
            row[h.owner_verdict] += 1
    for row in table.values():
        n = sum(row.values())
        row["accuracy"] = round((row["correct"] + 0.5 * row["partial"]) / n, 2) if n else None
    return table
