"""Markdown evidence report (Arabic or English).

Rules carried from the ledger:
- every finding shows its grade, status and evidence ids;
- uncited claims appear only in a separate, clearly labelled conjecture section;
- unknowns and contradictions are listed, not smoothed over;
- non-transferable factors are listed so a rebuilt copy is not over-trusted.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ..domain.grading import GRADE_ORDER
from ..domain.ledger import Ledger
from ..domain.models import ClaimStatus, Layer, Replicability, UnknownStatus
from .coverage import inspect_coverage, obligation_ledger

L = {
    "en": {
        "title": "Evidence file",
        "subject": "Organization",
        "mode": "Mode",
        "authorization": "Authorization basis",
        "profile": "Profile",
        "generated": "Generated",
        "disclaimer": (
            "This file states what the recorded evidence shows, with a grade for each finding. "
            "It is not an audit, a valuation, legal advice or a warranty. Anything not covered "
            "below is unknown, not absent."
        ),
        "how": "How to read grades",
        "grades": {
            "A": "record checked with its issuer, captured live, or independent third party",
            "B": "governing document, public record, or third party",
            "C": "record handed over by the organization itself",
            "D": "single testimony or public signal",
            "E": "analyst inference",
        },
        "status": {
            "triangulated": "triangulated (2+ independent sources)",
            "single_source": "single source (or sources under one control)",
            "contradicted": "contradicted",
            "conjecture": "conjecture (no evidence)",
        },
        "coverage": "Coverage by layer",
        "layer": "Layer",
        "claims": "Claims",
        "best": "Best grade",
        "unknowns": "Open unknowns",
        "no_evidence": "no evidence",
        "checklist": "Profile checklist",
        "item": "Item",
        "required": "Required",
        "state": "State",
        "states": {
            "met": "met",
            "below_required": "below required grade",
            "contradicted": "contradicted",
            "not_covered": "not covered",
        },
        "findings": "Findings",
        "contradictions": "Contradictions (stated vs enacted)",
        "open_unknowns": "Open unknowns",
        "probe": "next probe",
        "resolved": "Resolved unknowns",
        "retractions": "Retracted evidence",
        "retracted": "retracted",
        "affected": "claims affected",
        "reopened": "unknowns reopened",
        "needs": "needs",
        "conjecture": "Conjecture — not supported by recorded evidence",
        "industry_prior": "relies on industry norms, not this organization",
        "transfer": "Replicability",
        "replicability": {
            "codifiable": "codifiable (can be written down and taught)",
            "needs_capability": "needs a capability to be built",
            "needs_asset": "needs an asset (licence, location, capital, equipment)",
            "non_transferable": "non-transferable (relationships, timing, founder, history)",
        },
        "obligations": "Reconstruction obligations",
        "annex": "Evidence annex",
        "source": "Source",
        "custody": "custody",
        "location": "location",
        "limits": "limitations",
        "none": "None recorded.",
    },
    "ar": {
        "title": "ملف الأدلة",
        "subject": "المنشأة",
        "mode": "وضع التحليل",
        "authorization": "أساس التفويض",
        "profile": "ملف التشغيل",
        "generated": "تاريخ الإصدار",
        "disclaimer": (
            "يعرض هذا الملف ما تُظهره الأدلة المسجّلة، مع درجة لكل نتيجة. "
            "وهو ليس تدقيقاً ولا تقييماً ولا استشارة قانونية ولا ضماناً. "
            "كل ما لم يُغطَّ أدناه مجهول، وليس غير موجود."
        ),
        "how": "كيف تُقرأ الدرجات",
        "grades": {
            "A": "سجل جرى التحقق منه لدى الجهة المُصدِرة، أو التُقط مباشرة، أو من طرف ثالث مستقل",
            "B": "وثيقة حاكمة أو سجل عام أو طرف ثالث",
            "C": "سجل سلّمته المنشأة نفسها",
            "D": "شهادة شخص واحد أو مؤشر عام",
            "E": "استنتاج المحلل",
        },
        "status": {
            "triangulated": "مثلَّث (مصدران مستقلان أو أكثر)",
            "single_source": "مصدر واحد (أو مصادر تحت جهة واحدة)",
            "contradicted": "متعارض",
            "conjecture": "تخمين (بلا دليل)",
        },
        "coverage": "التغطية حسب الطبقة",
        "layer": "الطبقة",
        "claims": "الادعاءات",
        "best": "أفضل درجة",
        "unknowns": "مجهولات مفتوحة",
        "no_evidence": "لا أدلة",
        "checklist": "قائمة ملف التشغيل",
        "item": "البند",
        "required": "المطلوب",
        "state": "الحالة",
        "states": {
            "met": "مستوفى",
            "below_required": "أقل من الدرجة المطلوبة",
            "contradicted": "متعارض",
            "not_covered": "غير مغطّى",
        },
        "findings": "النتائج",
        "contradictions": "التعارضات (المُعلَن مقابل الفعلي)",
        "open_unknowns": "المجهولات المفتوحة",
        "probe": "الخطوة التالية",
        "resolved": "مجهولات حُسمت",
        "retractions": "أدلة سُحبت",
        "retracted": "مسحوب",
        "affected": "ادعاءات تأثرت",
        "reopened": "مجهولات أُعيد فتحها",
        "needs": "يحتاج",
        "conjecture": "تخمين: غير مدعوم بأدلة مسجّلة",
        "industry_prior": "يعتمد على أعراف القطاع لا على هذه المنشأة",
        "transfer": "قابلية النسخ",
        "replicability": {
            "codifiable": "قابل للتدوين (يمكن كتابته وتعليمه)",
            "needs_capability": "يحتاج بناء قدرة",
            "needs_asset": "يحتاج أصلاً (رخصة، موقع، رأس مال، معدات)",
            "non_transferable": "غير قابل للنقل (علاقات، توقيت، المؤسس، تاريخ)",
        },
        "obligations": "التزامات إعادة البناء",
        "annex": "ملحق الأدلة",
        "source": "المصدر",
        "custody": "الحيازة",
        "location": "الموضع",
        "limits": "القيود",
        "none": "لا شيء مسجّل.",
    },
}

LAYER_AR = {
    "strategy": "الاستراتيجية",
    "revenue": "الإيراد والتسعير",
    "customer": "رحلة العميل",
    "operations": "العمليات",
    "equipment": "المكائن وخطوط الإنتاج",
    "systems": "الأنظمة والبيانات",
    "people": "الناس والتوظيف",
    "supply": "التوريد",
    "finance": "المالية والتكاليف",
    "regulation": "التراخيص والوضع القانوني",
    "culture": "الثقافة والمعرفة الضمنية",
}


def _layer(name: str, lang: str) -> str:
    return LAYER_AR.get(name, name) if lang == "ar" else name


def render_report(ledger: Ledger, *, language: str | None = None, profile: str | None = None) -> str:
    lang = language or ledger.engagement.language
    lang = lang if lang in L else "en"
    t = L[lang]
    eng = ledger.engagement
    ledger.reevaluate()
    cov = inspect_coverage(ledger, profile)
    claims = list(ledger.data.claims.values())
    out: list[str] = []
    w = out.append

    w(f"# {t['title']}: {eng.subject}\n")
    w(f"- **{t['subject']}:** {eng.subject}")
    w(f"- **{t['mode']}:** {eng.mode.value}")
    if eng.authorization:
        w(f"- **{t['authorization']}:** {eng.authorization}")
    if cov.get("profile"):
        w(f"- **{t['profile']}:** {cov['profile']}")
    w(f"- **{t['generated']}:** {datetime.now(timezone.utc).date().isoformat()}\n")
    w(f"> {t['disclaimer']}\n")

    w(f"## {t['how']}\n")
    for g in GRADE_ORDER:
        w(f"- **{g.value}**: {t['grades'][g.value]}")
    w("")

    w(f"## {t['coverage']}\n")
    w(f"| {t['layer']} | {t['claims']} | {t['best']} | {t['unknowns']} |")
    w("|---|---|---|---|")
    for row in cov["layers"]:
        best = row["best_grade"] or f"— ({t['no_evidence']})"
        w(f"| {_layer(row['layer'], lang)} | {row['claims']} | {best} | {row['open_unknowns']} |")
    w("")

    if cov.get("items"):
        w(f"## {t['checklist']}\n")
        w(f"| {t['item']} | {t['required']} | {t['best']} | {t['state']} |")
        w("|---|---|---|---|")
        for it in cov["items"]:
            q = it["question_ar"] if lang == "ar" and it["question_ar"] else it["question"]
            w(f"| {q} | {it['required_grade']} | {it['best_grade'] or '—'} | {t['states'][it['state']]} |")
        w("")

    w(f"## {t['findings']}\n")
    supported = [c for c in claims if c.status in (ClaimStatus.TRIANGULATED, ClaimStatus.SINGLE_SOURCE)]
    if not supported:
        w(t["none"] + "\n")
    for layer in Layer:
        group = sorted(
            (c for c in supported if c.layer == layer),
            key=lambda c: GRADE_ORDER.index(c.grade) if c.grade else 9,
        )
        if not group:
            continue
        w(f"### {_layer(layer.value, lang)}\n")
        for c in group:
            refs = ", ".join(f"`{e}`" for e in c.evidence_ids)
            extra = f" · _{t['industry_prior']}_" if c.industry_prior else ""
            w(f"- **[{c.grade.value if c.grade else '?'}]** {c.statement} — {t['status'][c.status.value]} · {refs}{extra}")
        w("")

    w(f"## {t['contradictions']}\n")
    contra = [c for c in claims if c.status == ClaimStatus.CONTRADICTED]
    contra_unk = [u for u in ledger.data.unknowns.values() if u.status == UnknownStatus.CONTRADICTED]
    if not contra and not contra_unk:
        w(t["none"] + "\n")
    for c in contra:
        w(
            f"- {c.statement} — "
            + ", ".join(f"`{e}`" for e in c.evidence_ids)
            + " ⟂ "
            + ", ".join(f"`{e}`" for e in c.contradicting_evidence_ids)
        )
    for u in contra_unk:
        w(f"- {u.question} (`{u.id}`)")
    w("")

    w(f"## {t['open_unknowns']}\n")
    open_unk = [
        u
        for u in ledger.data.unknowns.values()
        if u.status in (UnknownStatus.OPEN, UnknownStatus.INVESTIGATING, UnknownStatus.BLOCKED)
    ]
    if not open_unk:
        w(t["none"] + "\n")
    for u in open_unk:
        needs = f" · {t['needs']}: {u.required_authority.value}" if u.required_authority else ""
        probe = f" · {t['probe']}: {u.recommended_probes[0]}" if u.recommended_probes else ""
        w(f"- {u.question} (`{u.id}`, {u.status.value}){needs}{probe}")
    w("")

    resolved = [u for u in ledger.data.unknowns.values() if u.status == UnknownStatus.RESOLVED and u.resolution]
    if resolved:
        w(f"## {t['resolved']}\n")
        for u in resolved:
            refs = ", ".join(f"`{e}`" for e in u.resolution.evidence_ids)
            note = f" · {u.resolution.note}" if u.resolution.note else ""
            w(f"- {u.question} → **{u.resolution.kind}** {refs}{note}")
        w("")

    retracted = sorted((e for e in ledger.data.evidence.values() if e.retracted), key=lambda e: e.retracted.at)
    if retracted:
        w(f"## {t['retractions']}\n")
        for ev in retracted:
            r = ev.retracted
            extra = []
            if r.affected_claims:
                extra.append(f"{t['affected']}: " + ", ".join(f"`{c}`" for c in r.affected_claims))
            if r.reopened_unknowns:
                extra.append(f"{t['reopened']}: " + ", ".join(f"`{u}`" for u in r.reopened_unknowns))
            tail = f" · {' · '.join(extra)}" if extra else ""
            w(f"- `{ev.id}` ~~{ev.fact}~~ — {r.reason} ({r.at[:10]}){tail}")
        w("")

    conj = [c for c in claims if c.status == ClaimStatus.CONJECTURE]
    if conj:
        w(f"## {t['conjecture']}\n")
        for c in conj:
            w(f"- ⚠ {c.statement}")
        w("")

    repl = [c for c in claims if c.replicability != Replicability.UNASSESSED]
    if repl:
        w(f"## {t['transfer']}\n")
        for kind in (Replicability.NON_TRANSFERABLE, Replicability.NEEDS_ASSET, Replicability.NEEDS_CAPABILITY, Replicability.CODIFIABLE):
            group = [c for c in repl if c.replicability == kind]
            if group:
                w(f"**{t['replicability'][kind.value]}**\n")
                for c in group:
                    w(f"- {c.statement}")
                w("")

    if cov.get("profile"):
        try:
            obl = obligation_ledger(ledger, profile)
        except Exception:
            obl = None
        if obl and obl["obligations"]:
            w(f"## {t['obligations']}\n")
            w(f"**{obl['overall']}** · {obl['summary']}\n")
            for o in obl["obligations"]:
                reasons = "; ".join(o["reasons"]) if o["reasons"] else ""
                w(f"- `{o['item']}` — **{o['status']}**{(' — ' + reasons) if reasons else ''}")
            w("")

    w(f"## {t['annex']}\n")
    cited = {e for c in claims for e in (*c.evidence_ids, *c.contradicting_evidence_ids)}
    cited |= {e for u in ledger.data.unknowns.values() for e in (*u.supporting_evidence_ids, *u.contradicting_evidence_ids)}
    for eid in sorted(cited):
        ev = ledger.data.evidence.get(eid)
        if not ev:
            continue
        src = ledger.data.sources.get(ev.source_id)
        loc = f" · {t['location']}: {ev.location}" if ev.location else ""
        lim = f" · {t['limits']}: {'; '.join(ev.limitations)}" if ev.limitations else ""
        src_txt = f"{src.title} ({t['custody']}: {src.custody.value})" if src else ev.source_id
        mark = f" **({t['retracted']})**" if ev.retracted else ""
        w(f"- `{ev.id}` **[{ev.grade.value}]**{mark} {ev.fact} — {t['source']}: {src_txt}, {ev.authority.value}{loc}{lim}")
    w("")
    body = "\n".join(out)
    # GitHub and most Markdown viewers honour dir="rtl" on a wrapping block.
    return f'<div dir="rtl">\n\n{body}\n\n</div>\n' if lang == "ar" else body
