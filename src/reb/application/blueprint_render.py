"""Render a blueprint as a Markdown report or a self-contained interactive HTML page."""

from __future__ import annotations

import html
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

T = {
    "en": {
        "title": "Blueprint", "s1": "1. Identity card", "s2": "2. Operating model (12 components)",
        "s3": "3. Process map", "s4": "4. Organization", "s5": "5. Numbers", "s6": "6. Redesign",
        "s7": "7. Verification plan", "known": "Known", "inferred": "Inferred", "unknown": "Unknown",
        "how": "How this is built", "look": "Traces to look for", "rules": "Design rules",
        "complete": "completeness", "basis": "basis", "conf": "confidence", "test": "test",
        "archetype": "Archetype", "family": "Family", "mode": "Mode", "sources": "Sources",
        "evidence": "Evidence items", "overall": "Overall completeness", "none": "Nothing recorded yet.",
        "proc_basis": {"event_log": "mined from records", "archetype": "typical for this archetype (to be confirmed)", None: "not mapped yet"},
        "copy": "Keep", "improve": "Improve / beat", "cannot_copy": "Cannot be copied", "recipe": "Build recipe",
        "equipment": "Equipment register", "consistency": "Consistency checks", "key_people": "Key people",
        "impact": "impact", "cost": "test cost", "calibration": "Calibration (owner verdicts)",
        "disclaimer": "Known = graded evidence. Inferred = hypotheses with computed confidence, never facts. Unknown = open questions with the next probe. Not an audit, valuation or warranty.",
        "strength": {"strong": "strong", "moderate": "moderate", "weak": "weak"},
        "confs": {"high": "high", "medium": "medium", "low": "low"},
    },
    "ar": {
        "title": "المخطط الهندسي", "s1": "1. بطاقة الهوية", "s2": "2. نموذج التشغيل (12 مكوّناً)",
        "s3": "3. خريطة العمليات", "s4": "4. الهيكل التنظيمي", "s5": "5. الأرقام", "s6": "6. إعادة التصميم",
        "s7": "7. خطة التحقق", "known": "نعرف", "inferred": "نستنتج", "unknown": "لا نعرف",
        "how": "كيف يُبنى هذا المكوّن", "look": "الآثار التي نبحث عنها", "rules": "قواعد التصميم",
        "complete": "الاكتمال", "basis": "الأساس", "conf": "الثقة", "test": "طريقة التأكد",
        "archetype": "النموذج المرجعي", "family": "العائلة", "mode": "الوضع", "sources": "المصادر",
        "evidence": "عناصر الأدلة", "overall": "الاكتمال الكلي", "none": "لا شيء مسجّل بعد.",
        "proc_basis": {"event_log": "مستخرجة من السجلات", "archetype": "نمطية لهذا النموذج (تحتاج تأكيداً)", None: "لم تُرسم بعد"},
        "copy": "يُنسخ كما هو", "improve": "يُحسَّن أو نتفوق فيه", "cannot_copy": "لا يمكن نسخه", "recipe": "وصفة البناء",
        "equipment": "سجل المعدات", "consistency": "فحوص التماسك", "key_people": "أشخاص محوريون",
        "impact": "الأثر", "cost": "تكلفة الاختبار", "calibration": "المعايرة (تقييم المالك)",
        "disclaimer": "«نعرف» = أدلة مُدرَّجة. «نستنتج» = فرضيات بثقة محسوبة وليست حقائق. «لا نعرف» = أسئلة مفتوحة مع الخطوة التالية. ليس تدقيقاً ولا تقييماً ولا ضماناً.",
        "strength": {"strong": "قوي", "moderate": "متوسط", "weak": "ضعيف"},
        "confs": {"high": "عالية", "medium": "متوسطة", "low": "منخفضة"},
    },
}


def _t(lang: str) -> dict:
    return T["ar" if lang == "ar" else "en"]


# ------------------------------------------------------------------ markdown


def render_markdown(bp: dict[str, Any], lang: str) -> str:
    t = _t(lang)
    idn = bp["identity"]
    out: list[str] = []
    w = out.append
    w(f"# {t['title']}: {idn['subject']}\n")
    w(f"> {t['disclaimer']}\n")
    w(f"## {t['s1']}\n")
    w(f"- **{t['archetype']}:** {idn['archetype_name'] or '—'} · **{t['family']}:** {idn['family'] or '—'}")
    w(f"- **{t['mode']}:** {idn['mode']} · **{t['sources']}:** {idn['sources']} · **{t['evidence']}:** {idn['evidence']}")
    w(f"- **{t['overall']}:** {bp['overall_completeness']}%\n")

    w(f"## {t['s2']}\n")
    for c in bp["components"]:
        w(f"### {c['name']} — {t['complete']} {c['completeness']}%\n")
        if c["known"]:
            w(f"**{t['known']}**")
            for k in c["known"]:
                w(f"- [{k['grade']}] {k['statement']} `{k['id']}`")
        if c["inferred"]:
            w(f"\n**{t['inferred']}**")
            for h in c["inferred"]:
                rng = f" ({h['range']['low']:g}–{h['range']['high']:g} {h['range']['unit']})" if h["range"] else ""
                test = f" — _{t['test']}: {h['test']}_" if h["test"] else ""
                w(f"- ({t['confs'][h['confidence']]}) {h['statement']}{rng}{test} `{h['id']}`")
        if c["unknown"]:
            w(f"\n**{t['unknown']}**")
            for u in c["unknown"]:
                w(f"- {u['question']}" + (f" → {u['probe']}" if u["probe"] else ""))
        if not (c["known"] or c["inferred"] or c["unknown"]):
            w(t["none"])
        hb = c["how_built"]
        if hb["elements"]:
            w(f"\n<details><summary>{t['how']}</summary>\n")
            for e in hb["elements"]:
                w(f"- {e}")
            for n in hb["family_notes"]:
                w(f"- {n}")
            if hb["rules"]:
                w(f"\n_{t['rules']}:_")
                for r in hb["rules"]:
                    w(f"- {r}")
            if c["look_for"]:
                w(f"\n_{t['look']}:_")
                for lf in c["look_for"]:
                    w(f"- {lf['trace']} ({t['strength'].get(lf['strength'], lf['strength'])})")
            w("\n</details>")
        w("")

    w(f"## {t['s3']}\n")
    p = bp["process"]
    w(f"_{t['basis']}: {t['proc_basis'].get(p['basis'], p['basis'])}_\n")
    if p["mermaid"]:
        w("```mermaid\n" + p["mermaid"] + "\n```\n")

    w(f"## {t['s4']}\n")
    org = bp["organization"]
    for k in org["known"]:
        w(f"- [{k['grade']}] {k['statement']}")
    for h in org["inferred"]:
        w(f"- ({t['confs'][h['confidence']]}) {h['statement']}")
    if org["key_people"]:
        w(f"\n**{t['key_people']}:** " + "؛ ".join(org["key_people"]))
    if bp["equipment"]:
        w(f"\n**{t['equipment']}**\n")
        w("| # | Equipment | × | Rate |\n|---|---|---|---|")
        for e in bp["equipment"]:
            rate = f"{e['rate']['low']:g}–{e['rate']['high']:g} {e['rate']['unit']}" if e["rate"] else "—"
            w(f"| {e['station'] or ''} | {e['name']} | {e['count']} | {rate} |")
    w("")

    w(f"## {t['s5']}\n")
    if bp["numbers"]:
        w("| | Metric | Value | Basis |\n|---|---|---|---|")
        for n in bp["numbers"]:
            if n["kind"] == "known":
                w(f"| {t['known']} | {n['statement']} | {n['value']:g} {n['unit'] or ''} | `{n['id']}` |")
            else:
                w(f"| {t['inferred']} ({t['confs'][n['confidence']]}) | {n['statement']} | {n['range']} {n['unit']} | {'; '.join(n['assumptions'])} |")
    else:
        w(t["none"])
    checks = [c for c in bp["consistency"]["checks"] if c.get("state") in ("consistent", "inconsistent")]
    if checks:
        w(f"\n**{t['consistency']}**")
        for c in checks:
            w(f"- {c['rule']}: **{c['state']}**")
    w("")

    w(f"## {t['s6']}\n")
    for comp, kinds in bp["redesign"]["by_component"].items():
        name = next((c["name"] for c in bp["components"] if c["component"] == comp), comp)
        w(f"### {name}")
        for kind in ("copy", "improve", "cannot_copy"):
            for item in kinds.get(kind, []):
                w(f"- **{t[kind]}:** {item['statement']}")
        w("")
    if bp["redesign"]["build_recipe"]:
        w(f"**{t['recipe']}**\n")
        for step in bp["redesign"]["build_recipe"]:
            w(f"- [{step['phase'] or '—'}] {step['statement']} `{', '.join(step['refs'])}`")
    w("")

    w(f"## {t['s7']}\n")
    for i, v in enumerate(bp["verification_plan"], 1):
        w(f"{i}. {v['test']} — _{v['statement']}_ ({t['impact']}: {v['impact']}, {t['conf']}: {t['confs'][v['confidence']]}, {t['cost']}: {v['test_cost']})")
    if bp["calibration"]:
        w(f"\n**{t['calibration']}:** `{json.dumps(bp['calibration'], ensure_ascii=False)}`")
    body = "\n".join(out)
    return f'<div dir="rtl">\n\n{body}\n\n</div>\n' if lang == "ar" else body


# ------------------------------------------------------------------ html

_CSS = """
:root{--bg:#f7f6f2;--card:#fff;--ink:#1d1d1b;--muted:#6b6a64;--line:#e4e2da;--known:#1f7a4d;--known-bg:#e6f4ec;
--inferred:#9a6200;--inferred-bg:#fbf0dc;--unknown:#5b5f6b;--unknown-bg:#eceef2;--accent:#2b4c7e}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#151514;--card:#1f1f1d;--ink:#ecebe6;--muted:#a3a29b;--line:#34332f;
--known:#6fd3a0;--known-bg:#173326;--inferred:#f0b45a;--inferred-bg:#3a2c12;--unknown:#b6bac6;--unknown-bg:#2a2c31;--accent:#8fb3ea}}
:root[data-theme="dark"]{--bg:#151514;--card:#1f1f1d;--ink:#ecebe6;--muted:#a3a29b;--line:#34332f;--known:#6fd3a0;--known-bg:#173326;
--inferred:#f0b45a;--inferred-bg:#3a2c12;--unknown:#b6bac6;--unknown-bg:#2a2c31;--accent:#8fb3ea}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 system-ui,-apple-system,"Segoe UI","Noto Naskh Arabic",Tahoma,sans-serif}
main{max-width:1080px;margin:0 auto;padding:24px 16px 64px}h1{font-size:26px;margin:0 0 4px}h2{font-size:19px;margin:36px 0 12px}
.note{color:var(--muted);font-size:13px}.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin:10px 0}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}.stat b{display:block;font-size:22px}
.tabs{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px}.tab{border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:999px;padding:6px 12px;cursor:pointer;font:inherit;font-size:13px}
.tab[aria-selected="true"]{background:var(--accent);color:#fff;border-color:var(--accent)}.panel{display:none}.panel.on{display:block}
.bar{height:6px;background:var(--line);border-radius:4px;overflow:hidden;margin:6px 0 12px}.bar i{display:block;height:100%;background:var(--accent)}
.b{display:inline-block;font-size:12px;border-radius:6px;padding:1px 8px;margin-inline-end:6px;font-weight:600}
.k{color:var(--known);background:var(--known-bg)}.i{color:var(--inferred);background:var(--inferred-bg)}.u{color:var(--unknown);background:var(--unknown-bg)}
ul{padding-inline-start:20px;margin:6px 0}li{margin:4px 0}.test{color:var(--muted);font-size:13px}code{font-size:11px;color:var(--muted)}
table{border-collapse:collapse;width:100%;font-size:14px}td,th{border-bottom:1px solid var(--line);padding:6px;text-align:start;vertical-align:top}
details summary{cursor:pointer;color:var(--accent)}.mermaid{background:var(--card);overflow-x:auto}
"""

_JS = """
document.querySelectorAll('.tab').forEach(b=>b.addEventListener('click',()=>{
document.querySelectorAll('.tab').forEach(x=>x.setAttribute('aria-selected','false'));
document.querySelectorAll('.panel').forEach(x=>x.classList.remove('on'));
b.setAttribute('aria-selected','true');document.getElementById(b.dataset.p).classList.add('on');}));
if(window.mermaid){mermaid.initialize({startOnLoad:true,theme:matchMedia('(prefers-color-scheme: dark)').matches?'dark':'default'});}
"""


def render_html(bp: dict[str, Any], lang: str) -> str:
    t = _t(lang)
    e = html.escape
    idn = bp["identity"]
    parts: list[str] = []
    a = parts.append
    a(f"<h1>{e(t['title'])}: {e(idn['subject'])}</h1><p class='note'>{e(t['disclaimer'])}</p>")
    a(f"<h2>{e(t['s1'])}</h2><div class='stats'>")
    for label, value in [(t["archetype"], idn["archetype_name"] or "—"), (t["family"], idn["family"] or "—"),
                         (t["mode"], idn["mode"]), (t["sources"], idn["sources"]), (t["overall"], f"{bp['overall_completeness']}%")]:
        a(f"<div class='card stat'><span class='note'>{e(str(label))}</span><b>{e(str(value))}</b></div>")
    a("</div>")

    a(f"<h2>{e(t['s2'])}</h2><div class='tabs' role='tablist'>")
    for i, c in enumerate(bp["components"]):
        a(f"<button class='tab' role='tab' aria-selected='{str(i == 0).lower()}' data-p='p{i}'>{e(c['name'])} · {c['completeness']}%</button>")
    a("</div>")
    for i, c in enumerate(bp["components"]):
        a(f"<div class='panel card{' on' if i == 0 else ''}' id='p{i}'><b>{e(c['name'])}</b>")
        a(f"<div class='bar'><i style='width:{c['completeness']}%'></i></div><ul>")
        for k in c["known"]:
            a(f"<li><span class='b k'>{e(t['known'])} · {e(str(k['grade']))}</span>{e(k['statement'])} <code>{e(k['id'])}</code></li>")
        for h in c["inferred"]:
            rng = f" ({h['range']['low']:g}–{h['range']['high']:g} {e(h['range']['unit'])})" if h["range"] else ""
            test = f"<div class='test'>{e(t['test'])}: {e(h['test'])}</div>" if h["test"] else ""
            a(f"<li><span class='b i'>{e(t['inferred'])} · {e(t['confs'][h['confidence']])}</span>{e(h['statement'])}{rng}{test}</li>")
        for u in c["unknown"]:
            probe = f"<div class='test'>→ {e(u['probe'])}</div>" if u["probe"] else ""
            a(f"<li><span class='b u'>{e(t['unknown'])}</span>{e(u['question'])}{probe}</li>")
        if not (c["known"] or c["inferred"] or c["unknown"]):
            a(f"<li class='note'>{e(t['none'])}</li>")
        a("</ul>")
        hb = c["how_built"]
        if hb["elements"] or c["look_for"]:
            a(f"<details><summary>{e(t['how'])} · {e(t['look'])}</summary><ul>")
            for x in [*hb["elements"], *hb["family_notes"]]:
                a(f"<li>{e(x)}</li>")
            for r in hb["rules"]:
                a(f"<li class='note'>{e(t['rules'])}: {e(r)}</li>")
            for lf in c["look_for"]:
                a(f"<li class='test'>🔎 {e(lf['trace'])} ({e(t['strength'].get(lf['strength'], lf['strength']))})</li>")
            a("</ul></details>")
        a("</div>")

    p = bp["process"]
    a(f"<h2>{e(t['s3'])}</h2><p class='note'>{e(t['basis'])}: {e(t['proc_basis'].get(p['basis'], str(p['basis'])))}</p>")
    if p["mermaid"]:
        a(f"<div class='card'><pre class='mermaid'>{e(p['mermaid'])}</pre></div>")

    a(f"<h2>{e(t['s4'])}</h2><div class='card'><ul>")
    for k in bp["organization"]["known"]:
        a(f"<li><span class='b k'>{e(t['known'])}</span>{e(k['statement'])}</li>")
    for h in bp["organization"]["inferred"]:
        a(f"<li><span class='b i'>{e(t['inferred'])} · {e(t['confs'][h['confidence']])}</span>{e(h['statement'])}</li>")
    a("</ul>")
    if bp["equipment"]:
        a(f"<b>{e(t['equipment'])}</b><table><tr><th>#</th><th></th><th>×</th><th></th></tr>")
        for q in bp["equipment"]:
            rate = f"{q['rate']['low']:g}–{q['rate']['high']:g} {q['rate']['unit']}" if q["rate"] else "—"
            a(f"<tr><td>{q['station'] or ''}</td><td>{e(q['name'])}</td><td>{q['count']}</td><td>{e(rate)}</td></tr>")
        a("</table>")
    a("</div>")

    a(f"<h2>{e(t['s5'])}</h2><div class='card'>")
    if bp["numbers"]:
        a("<table>")
        for n in bp["numbers"]:
            if n["kind"] == "known":
                a(f"<tr><td><span class='b k'>{e(t['known'])}</span></td><td>{e(n['statement'])}</td><td>{n['value']:g} {e(n['unit'] or '')}</td></tr>")
            else:
                a(f"<tr><td><span class='b i'>{e(t['inferred'])}</span></td><td>{e(n['statement'])}<div class='test'>{e('; '.join(n['assumptions']))}</div></td><td>{e(n['range'])} {e(n['unit'])}</td></tr>")
        a("</table>")
    else:
        a(f"<p class='note'>{e(t['none'])}</p>")
    a("</div>")

    a(f"<h2>{e(t['s6'])}</h2>")
    for comp, kinds in bp["redesign"]["by_component"].items():
        name = next((c["name"] for c in bp["components"] if c["component"] == comp), comp)
        a(f"<div class='card'><b>{e(name)}</b><ul>")
        for kind, badge in (("copy", "k"), ("improve", "i"), ("cannot_copy", "u")):
            for item in kinds.get(kind, []):
                a(f"<li><span class='b {badge}'>{e(t[kind])}</span>{e(item['statement'])}</li>")
        a("</ul></div>")
    if bp["redesign"]["build_recipe"]:
        a(f"<div class='card'><b>{e(t['recipe'])}</b><ul>")
        for s in bp["redesign"]["build_recipe"]:
            a(f"<li><span class='b u'>{e(s['phase'] or '—')}</span>{e(s['statement'])}</li>")
        a("</ul></div>")

    a(f"<h2>{e(t['s7'])}</h2><div class='card'><ol>")
    for v in bp["verification_plan"]:
        a(f"<li>{e(v['test'])}<div class='test'>{e(v['statement'])} · {e(t['impact'])}: {e(v['impact'])} · {e(t['conf'])}: {e(t['confs'][v['confidence']])}</div></li>")
    a("</ol></div>")

    direction = "rtl" if lang == "ar" else "ltr"
    return (
        f"<!doctype html><html lang='{e(lang)}' dir='{direction}'><head><meta charset='utf-8'>"
        f"<meta name='viewport' content='width=device-width,initial-scale=1'><title>{e(t['title'])} · {e(idn['subject'])}</title>"
        f"<style>{_CSS}</style></head><body><main>{''.join(parts)}</main>"
        "<script src='https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js'></script>"
        f"<script>{_JS}</script></body></html>"
    )


def html_to_pdf(html_path: Path, pdf_path: Path) -> bool:
    """Print with a local headless Chrome/Chromium if one is installed."""
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        shutil.which("google-chrome") or "", shutil.which("chromium") or "", shutil.which("chromium-browser") or "",
    ]
    chrome = next((c for c in candidates if c and Path(c).exists()), None)
    if not chrome:
        return False
    subprocess.run([chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer", "--virtual-time-budget=5000",
                    f"--print-to-pdf={pdf_path}", html_path.resolve().as_uri()],
                   capture_output=True, timeout=120)
    return pdf_path.exists()
