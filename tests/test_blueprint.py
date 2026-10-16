from __future__ import annotations

import http.server
import threading
from pathlib import Path

import pytest

from conftest import add_text_source
from reb.application import blueprint as bpmod
from reb.application.blueprint_render import render_html, render_markdown
from reb.application.consistency import check_consistency
from reb.archetypes import apply_archetype, archetypes, suggest
from reb.domain.errors import RebError
from reb.domain.ledger import Ledger
from reb.kernel import blocks, equipment, families
from reb.providers import web


@pytest.fixture
def bp_ledger(tmp_path: Path) -> Ledger:
    return Ledger.init(tmp_path, name="t", subject="Test Org", mode="self", authorization="owner",
                       profile="blueprint", language="en")


# ------------------------------------------------------------------ kernel & library


def test_kernel_traces_point_to_real_elements():
    for b in blocks():
        ids = {e.id for e in b.elements}
        assert all(t.element in ids for t in b.traces), b.id
    assert set(families()) == {"business", "public_body", "nonprofit", "industrial"}
    block_ids = {b.id for b in blocks()}
    for f in families().values():
        assert set(f.blocks) <= block_ids and all(t.block in block_ids for t in f.traces)


@pytest.mark.parametrize("archetype_id", sorted(archetypes()))
def test_every_archetype_seeds_a_low_confidence_blueprint(tmp_path, archetype_id):
    led = Ledger.init(tmp_path, name="t", subject="X", mode="public", profile="blueprint", language="ar")
    res = apply_archetype(led, archetype_id)
    assert res["hypotheses"] >= 10
    assert all(h.confidence.value == "low" and h.basis.value == "archetype" for h in led.data.hypotheses.values())
    assert not led.data.claims  # nothing inferred is presented as known
    for item in led.data.design.values():
        assert item.refs and all(r in led.data.hypotheses for r in item.refs)
    bp = bpmod.build_blueprint(led)
    assert len(bp["components"]) == 12 and bp["process"]["mermaid"]


def test_industrial_archetypes_list_known_equipment():
    for a in archetypes().values():
        if a.family == "industrial":
            assert a.equipment and all(e in equipment() for e in a.equipment)


def test_suggest_matches_keywords():
    assert suggest("Bakanlık ministry of trade")[0]["archetype"] == "ministry"


# ------------------------------------------------------------------ hypotheses


def test_confidence_is_computed_from_signals(bp_ledger):
    led = bp_ledger
    site = add_text_source(led, "site", custody="public", kind="public_signal", controller="org-site",
                           legal_basis="https://x")
    ads = add_text_source(led, "job ads", custody="public", kind="public_signal", controller="job-board",
                          legal_basis="https://y")
    e1 = led.add_evidence(source_id=site.id, fact="site mentions an ERP", authority="public_signal")
    e2 = led.add_evidence(source_id=ads.id, fact="job ad asks for ERP skills", authority="public_signal")
    guess = led.add_evidence(source_id=site.id, fact="guess", authority="analyst_inference", confidence="inferred")
    h = led.add_hypothesis(statement="They run an ERP.", component="systems", basis="signal", signal_evidence_ids=[e1.id])
    assert h.confidence.value == "medium"
    h = led.update_hypothesis(h.id, revision=1, add_signals=[e2.id])
    assert h.confidence.value == "high"
    h2 = led.add_hypothesis(statement="They have 3 shifts.", component="operations", basis="signal",
                            signal_evidence_ids=[guess.id])
    assert h2.confidence.value == "low"
    calc = led.add_hypothesis(statement="Revenue band.", component="economics", basis="calculation",
                              derived_from=[h.id, h2.id], assumptions=["two inputs"])
    assert calc.confidence.value == "low"  # weakest input


@pytest.mark.parametrize("kwargs,code", [
    ({"basis": "signal"}, "signal_required"),
    ({"basis": "calculation"}, "calculation_inputs_required"),
    ({"basis": "archetype"}, "archetype_required"),
])
def test_hypothesis_needs_its_basis(bp_ledger, kwargs, code):
    with pytest.raises(RebError) as err:
        bp_ledger.add_hypothesis(statement="x", component="team", **kwargs)
    assert err.value.code == code


def test_support_needs_corroboration_and_promotion_needs_support(bp_ledger):
    led = bp_ledger
    site = add_text_source(led, "site says 40 staff", custody="public", kind="public_signal", controller="site",
                           legal_basis="https://x")
    e1 = led.add_evidence(source_id=site.id, fact="site says 40 staff", authority="public_signal")
    e1b = led.add_evidence(source_id=site.id, fact="team page shows 40 photos", authority="public_signal")
    h = led.add_hypothesis(statement="About 40 people work there.", component="team", basis="signal",
                           signal_evidence_ids=[e1.id])
    with pytest.raises(RebError):
        led.promote_hypothesis(h.id, revision=1)
    with pytest.raises(RebError) as err:  # same weak source again is not support
        led.update_hypothesis(h.id, revision=1, status="supported", status_evidence_ids=[e1b.id])
    assert err.value.code == "insufficient_support"
    roster = add_text_source(led, "payroll roster", kind="system_export", custody="captured_live", controller="hr")
    e2 = led.add_evidence(source_id=roster.id, fact="roster lists 41 people", authority="system_record")
    h = led.update_hypothesis(h.id, revision=1, status="supported", status_evidence_ids=[e2.id])
    claim = led.promote_hypothesis(h.id, revision=h.revision)
    assert claim.component.value == "team" and led.data.hypotheses[h.id].status.value == "promoted"


def test_design_items_need_existing_refs(bp_ledger):
    with pytest.raises(RebError):
        bp_ledger.add_design_item(component="team", kind="improve", statement="Train a second operator.", refs=[])
    with pytest.raises(RebError):
        bp_ledger.add_design_item(component="team", kind="improve", statement="Train a second operator.", refs=["hyp_x"])


def test_hypotheses_never_render_as_known(bp_ledger):
    apply_archetype(bp_ledger, "restaurant-cafe")
    md = render_markdown(bpmod.build_blueprint(bp_ledger), "en")
    assert "**Known**" not in md and "**Inferred**" in md
    for section in ("1. Identity card", "2. Operating model", "3. Process map", "4. Organization", "5. Numbers",
                    "6. Redesign", "7. Verification plan"):
        assert section in md
    html = render_html(bpmod.build_blueprint(bp_ledger), "ar")
    assert "dir='rtl'" in html and "نستنتج" in html and "<script>alert" not in html


def test_html_escapes_content(bp_ledger):
    site = add_text_source(bp_ledger, "x", custody="public", kind="public_signal", controller="s", legal_basis="u")
    e = bp_ledger.add_evidence(source_id=site.id, fact="x", authority="public_signal")
    bp_ledger.add_hypothesis(statement="<script>alert(1)</script>", component="moat", basis="signal",
                             signal_evidence_ids=[e.id])
    assert "<script>alert(1)" not in render_html(bpmod.build_blueprint(bp_ledger), "en")


# ------------------------------------------------------------------ consistency & equipment


def test_consistency_flags_revenue_mismatch(bp_ledger):
    led = bp_ledger
    src = add_text_source(led, "x", custody="public", kind="public_signal", controller="s", legal_basis="u")
    e = led.add_evidence(source_id=src.id, fact="x", authority="public_signal")
    for metric, value in (("units_per_year", 1000), ("price_per_unit", 10), ("revenue_per_year", 50000)):
        led.add_hypothesis(statement=f"{metric} about {value}", component="economics", basis="signal",
                           signal_evidence_ids=[e.id], metric=metric, range={"low": value, "high": value, "unit": "x"})
    res = check_consistency(led)
    rule = next(c for c in res["checks"] if c["rule"] == "revenue_equals_volume_times_price")
    assert rule["state"] == "inconsistent" and any("Revenue" in u.question for u in led.data.unknowns.values())


def test_line_capacity_uses_the_bottleneck(bp_ledger):
    led = bp_ledger
    src = add_text_source(led, "x", custody="public", kind="public_signal", controller="s", legal_basis="u")
    e = led.add_evidence(source_id=src.id, fact="video shows machines", authority="public_signal")
    led.add_equipment(name="Mixer", refs=[e.id], station=1, count=2, rate={"low": 500, "high": 500, "unit": "kg/hour"})
    led.add_equipment(name="Oven", refs=[e.id], station=2, count=1, rate={"low": 300, "high": 300, "unit": "kg/hour"})
    led.add_hypothesis(statement="They claim 200 tonnes a month.", component="assets", basis="signal",
                       signal_evidence_ids=[e.id], metric="output_per_month",
                       range={"low": 200000, "high": 200000, "unit": "kg/month"})
    line = next(c for c in check_consistency(led)["checks"] if c["rule"] == "line_capacity")
    assert line["bottleneck_station"] == 2 and line["capacity_per_month"] == 300 * 352
    assert line["state"] == "inconsistent"


# ------------------------------------------------------------------ web provider


def test_crawler_respects_robots_and_stays_on_host(tmp_path):
    (tmp_path / "robots.txt").write_text("User-agent: *\nDisallow: /private\n")
    (tmp_path / "index.html").write_text(
        "<html><head><title>Home</title><meta name='generator' content='WordPress 6.5'>"
        "<script src='https://connect.facebook.net/x.js'></script></head><body><h1>Welcome</h1>"
        "<a href='/about.html'>About</a><a href='/private/secret.html'>S</a>"
        "<a href='https://other.example/x'>X</a><a href='https://wa.me/123'>WA</a></body></html>")
    (tmp_path / "about.html").write_text("<html><head><title>About</title></head><body>We make bread.</body></html>")
    (tmp_path / "private").mkdir()
    (tmp_path / "private" / "secret.html").write_text("<html><body>secret</body></html>")
    handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(*a, directory=str(tmp_path), **k)  # noqa: E731
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        crawl = web.crawl(f"http://127.0.0.1:{server.server_port}/index.html", max_pages=10, delay=0)
    finally:
        server.shutdown()
    texts = " ".join(p.text for p in crawl.pages)
    assert "We make bread." in texts and "secret" not in texts
    assert any("private" in u for u in crawl.skipped_by_robots)
    fp = web.footprint(crawl)
    assert "WordPress 6.5" in fp["cms"] and "Meta Pixel" in fp["tools"] and "WhatsApp" in fp["contact_channels"]


def test_fingerprints_match_hosts_not_words():
    c = web.Crawl(start="https://x.example/", pages=[web.Page(
        url="https://x.example/", title="", text="politikası", generator=None,
        scripts=["https://x.example/bilgi-politikasi.js"], links=["https://x.example/politikasi"])])
    assert web.footprint(c)["tools"] == []
