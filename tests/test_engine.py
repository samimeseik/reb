from __future__ import annotations

import pytest

from conftest import add_text_source
from reb.domain.errors import RebError
from reb.domain.ledger import Ledger


def test_grade_is_capped_by_custody(ledger):
    held = add_text_source(ledger, "ledger rows", custody="subject_held", kind="system_export")
    live = add_text_source(ledger, "pulled live", custody="captured_live", kind="system_export")
    a = ledger.add_evidence(source_id=held.id, fact="x", authority="system_record")
    b = ledger.add_evidence(source_id=live.id, fact="y", authority="system_record")
    assert a.grade.value == "C"
    assert b.grade.value == "A"


def test_inferred_confidence_caps_grade(ledger):
    src = add_text_source(ledger, "rows", custody="captured_live", kind="system_export")
    ev = ledger.add_evidence(source_id=src.id, fact="guess", authority="system_record", confidence="inferred")
    assert ev.grade.value == "D"


def test_third_party_needs_independent_channel_for_A(ledger):
    plain = add_text_source(ledger, "statement 1", custody="third_party", kind="system_export", controller="bank")
    indep = add_text_source(ledger, "statement 2", custody="third_party", kind="system_export", controller="bank2",
                            independent_channel=True)
    assert ledger.add_evidence(source_id=plain.id, fact="a", authority="system_record").grade.value == "B"
    assert ledger.add_evidence(source_id=indep.id, fact="b", authority="system_record").grade.value == "A"


def test_quote_must_match_source_text(ledger):
    src = add_text_source(ledger, "Standart teslim süresi: 10 gün.")
    ok = ledger.add_evidence(source_id=src.id, fact="10 days", authority="governing_document",
                             quote="standart  teslim süresi: 10 gün")
    assert ok.quote
    with pytest.raises(RebError) as err:
        ledger.add_evidence(source_id=src.id, fact="5 days", authority="governing_document", quote="5 gün")
    assert err.value.code == "quote_not_found"


def test_interview_is_testimony(ledger):
    src = add_text_source(ledger, "he said so", kind="interview", custody="captured_live", legal_basis="consent-1")
    with pytest.raises(RebError) as err:
        ledger.add_evidence(source_id=src.id, fact="x", authority="system_record")
    assert err.value.code == "authority_mismatch"


def test_claim_without_evidence_is_conjecture(ledger):
    c = ledger.record_claim(statement="Customers come via referrals.", layer="revenue")
    assert c.status.value == "conjecture" and c.grade is None


def test_same_controller_is_not_triangulation(ledger):
    a = add_text_source(ledger, "sop says 10 days", controller="workshop")
    b = add_text_source(ledger, "usta says 10 days", controller="workshop", kind="interview",
                        custody="captured_live", legal_basis="c-1")
    ea = ledger.add_evidence(source_id=a.id, fact="10d", authority="governing_document")
    eb = ledger.add_evidence(source_id=b.id, fact="10d", authority="testimony")
    c = ledger.record_claim(statement="Lead time is about 10 days.", layer="operations", evidence_ids=[ea.id, eb.id])
    assert c.status.value == "single_source"


def test_independent_controllers_triangulate(ledger):
    a = add_text_source(ledger, "rows", controller="workshop", kind="system_export")
    photo = add_text_source(ledger, "photo of queue", controller="observer:analyst", custody="captured_live",
                            kind="image")
    b = add_text_source(ledger, "walk", controller="observer:analyst", custody="captured_live", kind="observation",
                        artifact_ids=[photo.id])
    ea = ledger.add_evidence(source_id=a.id, fact="queue", authority="system_record")
    eb = ledger.add_evidence(source_id=b.id, fact="queue seen", authority="direct_observation")
    c = ledger.record_claim(statement="Paint is the bottleneck.", layer="operations", evidence_ids=[ea.id, eb.id])
    assert c.status.value == "triangulated" and c.grade.value == "A"


def test_typed_observation_is_capped_and_needs_a_second_day(ledger):
    a = add_text_source(ledger, "rows", controller="workshop", kind="system_export")
    ea = ledger.add_evidence(source_id=a.id, fact="queue", authority="system_record")
    w1 = add_text_source(ledger, "walk 1", controller="observer:analyst", custody="captured_live", kind="observation")
    e1 = ledger.add_evidence(source_id=w1.id, fact="queue seen", authority="direct_observation", as_of="2026-10-10")
    assert e1.grade.value == "B"
    c = ledger.record_claim(statement="Paint is the bottleneck.", layer="operations", evidence_ids=[ea.id, e1.id])
    assert c.status.value == "single_source"
    w2 = add_text_source(ledger, "walk 2", controller="observer:analyst", custody="captured_live", kind="observation")
    e2 = ledger.add_evidence(source_id=w2.id, fact="queue seen again", authority="direct_observation",
                             as_of="2026-10-14")
    c = ledger.record_claim(statement="Paint is the bottleneck on most days.", layer="operations",
                            evidence_ids=[ea.id, e1.id, e2.id])
    assert c.status.value == "triangulated"
    with pytest.raises(RebError):
        add_text_source(ledger, "walk 3", custody="captured_live", kind="observation", artifact_ids=[a.id])


def test_derived_source_is_not_independent_of_its_parent(ledger):
    parent = add_text_source(ledger, "export", controller="erp", kind="system_export")
    child = add_text_source(ledger, "summary of export", controller="consultant", upstream_ids=[parent.id])
    ea = ledger.add_evidence(source_id=parent.id, fact="a", authority="system_record")
    eb = ledger.add_evidence(source_id=child.id, fact="a again", authority="governing_document")
    c = ledger.record_claim(statement="Volume is 100 units a week.", layer="operations", evidence_ids=[ea.id, eb.id])
    assert c.status.value == "single_source"


def test_non_overlapping_periods_do_not_triangulate(ledger):
    a = add_text_source(ledger, "2024 rows", controller="erp", kind="system_export",
                        context={"period_start": "2024-01-01", "period_end": "2024-06-30"})
    b = add_text_source(ledger, "2026 walk", controller="analyst", custody="captured_live", kind="observation",
                        context={"period_start": "2026-10-01", "period_end": "2026-10-01"})
    ea = ledger.add_evidence(source_id=a.id, fact="x", authority="system_record")
    eb = ledger.add_evidence(source_id=b.id, fact="x", authority="direct_observation")
    c = ledger.record_claim(statement="Two shifts run.", layer="operations", evidence_ids=[ea.id, eb.id])
    assert c.status.value == "single_source"


@pytest.mark.parametrize("word", ["verified", "guaranteed", "مضمون", "موثّق", "kesinlikle"])
def test_banned_vocabulary(ledger, word):
    with pytest.raises(RebError) as err:
        ledger.record_claim(statement=f"The capacity is {word} at 500 units.", layer="equipment")
    assert err.value.code == "banned_vocabulary"


def test_public_mode_rejects_private_sources(public_ledger):
    with pytest.raises(RebError) as err:
        add_text_source(public_ledger, "internal sop", custody="subject_held")
    assert err.value.code == "mode_violation"
    with pytest.raises(RebError):
        add_text_source(public_ledger, "chat", custody="public", kind="chat_export", legal_basis="x")
    with pytest.raises(RebError) as err:
        add_text_source(public_ledger, "registry page", custody="public", kind="public_record", legal_basis=None)
    assert err.value.code == "public_reference_required"
    ok = add_text_source(public_ledger, "registry page", custody="public", kind="public_record",
                         legal_basis="https://registry.example/123")
    assert ok.id.startswith("src_")


def test_interviews_need_consent(ledger):
    with pytest.raises(RebError) as err:
        add_text_source(ledger, "transcript", kind="interview", custody="captured_live", legal_basis=None)
    assert err.value.code == "consent_required"


def test_private_modes_need_authorization(tmp_path):
    with pytest.raises(RebError) as err:
        Ledger.init(tmp_path, name="t", subject="X", mode="engaged")
    assert err.value.code == "authorization_required"


def test_unknown_resolution_needs_evidence_of_required_authority(ledger):
    u = ledger.record_unknown(question="What is the unit cost?", layer="finance", required_authority="system_record")
    talk = add_text_source(ledger, "owner says 900", kind="interview", custody="captured_live", legal_basis="c")
    ev_talk = ledger.add_evidence(source_id=talk.id, fact="900 TRY", authority="testimony")
    with pytest.raises(RebError) as err:
        ledger.update_unknown(u.id, revision=1, status="resolved",
                              resolution={"kind": "verified", "evidence_ids": [ev_talk.id]})
    assert err.value.code == "insufficient_authority"
    rows = add_text_source(ledger, "cost rows", kind="system_export")
    ev_rows = ledger.add_evidence(source_id=rows.id, fact="cost 870", authority="system_record")
    u2 = ledger.update_unknown(u.id, revision=1, status="resolved",
                               resolution={"kind": "verified", "evidence_ids": [ev_rows.id]})
    assert u2.status.value == "resolved" and u2.revision == 2
    with pytest.raises(RebError) as err:
        ledger.update_unknown(u.id, revision=1, add_probes=["x"])
    assert err.value.code == "stale_revision"


def test_ledger_round_trip(ledger):
    src = add_text_source(ledger, "abc")
    ledger.add_evidence(source_id=src.id, fact="f", authority="governing_document")
    ledger.save()
    again = Ledger.load(ledger.workspace)
    assert again.data.sources.keys() == ledger.data.sources.keys()
    assert (ledger.workspace / ".reb" / ".gitignore").exists()


def test_quoted_warranty_words_are_reported_speech(ledger):
    c = ledger.record_claim(statement='The site states a policy of "no guarantees" on returns.', layer="strategy")
    assert c.status.value == "conjecture"
    with pytest.raises(RebError):
        ledger.record_claim(statement="Returns are guaranteed by the developer.", layer="strategy")


def test_public_mode_accepts_published_reports_but_not_chats(public_ledger):
    rep = add_text_source(public_ledger, "annual report", kind="financial_statement", custody="public",
                          legal_basis="https://example.com/annual-report.pdf")
    assert rep.kind.value == "financial_statement"
    with pytest.raises(RebError):
        add_text_source(public_ledger, "chat", kind="chat_export", custody="public", legal_basis="https://x")


@pytest.mark.parametrize("mode", ["engaged", "public"])
def test_subject_own_publications_share_its_controller(tmp_path, mode):
    led = Ledger.init(tmp_path, name="t", subject="Hope Bridge", mode=mode,
                      authorization=None if mode == "public" else "m", aliases=["HB Foundation", "hopebridge.org"])
    by_name = add_text_source(led, "site", controller="hope-bridge", kind="public_signal", custody="public",
                              legal_basis="https://example.net/a")
    by_alias = add_text_source(led, "press", controller="HB foundation", kind="public_signal", custody="public",
                               legal_basis="https://example.net/b")
    by_domain = add_text_source(led, "blog", controller="comms team", kind="public_signal", custody="public",
                                legal_basis="https://www.blog.hopebridge.org/post")
    other = add_text_source(led, "news", controller="newsco", kind="public_signal", custody="public",
                            legal_basis="https://news.example/x")
    assert {by_name.controller, by_alias.controller, by_domain.controller} == {"subject:Hope Bridge"}
    assert other.controller == "newsco"


def test_fact_beyond_quote_is_capped(ledger):
    src = add_text_source(ledger, "invoice,amount\nINV-1,100\n", kind="system_export", custody="captured_live")
    ev = ledger.add_evidence(source_id=src.id, fact="The company is highly profitable and collects all receivables",
                             authority="system_record", quote="INV-1,100")
    assert ev.grade.value == "C" and any("shares no words" in x for x in ev.limitations)
    ev = ledger.add_evidence(source_id=src.id, fact="Invoice INV-1 was for 900", authority="system_record",
                             quote="INV-1,100")
    assert ev.grade.value == "D"
    ev = ledger.add_evidence(source_id=src.id, fact="Invoice INV-1 amount was 100", authority="system_record",
                             quote="INV-1,100")
    assert ev.grade.value == "A"


def test_weak_contradiction_is_a_dispute_not_a_contradiction(ledger):
    a = add_text_source(ledger, "rows", controller="erp", kind="system_export", custody="captured_live")
    b = add_text_source(ledger, "bank", controller="Bank", kind="system_export", custody="third_party",
                        independent_channel=True)
    r = add_text_source(ledger, "rumour", controller="staff")
    e1 = ledger.add_evidence(source_id=a.id, fact="paid on time", authority="system_record")
    e2 = ledger.add_evidence(source_id=b.id, fact="bank shows on time", authority="system_record")
    weak = ledger.add_evidence(source_id=r.id, fact="someone says late", authority="testimony")
    strong = ledger.add_evidence(source_id=b.id, fact="bank shows one late payment", authority="system_record")
    c = ledger.record_claim(statement="Payments are on time.", layer="finance", evidence_ids=[e1.id, e2.id],
                            contradicting_evidence_ids=[weak.id])
    assert c.status.value == "disputed_weak"
    c = ledger.record_claim(statement="Payments are on time.", layer="finance", contradicting_evidence_ids=[strong.id])
    assert c.status.value == "contradicted"


def test_near_duplicate_sources_are_not_independent_until_declared(public_ledger):
    led = public_ledger
    a = add_text_source(led, "Acme serves 10,000 customers across the region.", controller="acme",
                        kind="public_signal", custody="public", legal_basis="https://acme.example/p")
    b = add_text_source(led, "Acme serves 10,000 customers across the region, the company said.",
                        controller="newsco", kind="document", custody="public", legal_basis="https://news.example/x")
    assert b.possible_upstream_ids == [a.id]
    assert any(u.entity == f"upstream:{b.id}:{a.id}" for u in led.data.unknowns.values())
    e1 = led.add_evidence(source_id=a.id, fact="Acme says 10,000 customers", authority="public_signal")
    e2 = led.add_evidence(source_id=b.id, fact="News reports 10,000 customers", authority="governing_document")
    c = led.record_claim(statement="Acme has 10,000 customers", layer="customer", evidence_ids=[e1.id, e2.id])
    assert c.status.value == "single_source"
    led.declare_independent(b.id, a.id, reason="reporter cites the regulator's filing, checked separately")
    assert led.claim(c.id).status.value == "triangulated"


def test_public_reference_and_kind_override_rules(public_ledger):
    with pytest.raises(RebError) as err:
        add_text_source(public_ledger, "page", kind="public_signal", custody="public", legal_basis="n/a")
    assert err.value.code == "public_reference_required"
    assert add_text_source(public_ledger, "registry", kind="public_record", custody="public",
                           legal_basis="MERSIS 0123456789").legal_basis


def test_document_names_salted_tokens_and_map(tmp_path, monkeypatch):
    from reb.application.ingest import ingest_file

    led = Ledger.init(tmp_path / "w", name="t", subject="Acme", mode="engaged", authorization="m")
    memo = tmp_path / "memo.md"
    memo.write_text("Ahmet Yilmaz approves discounts. Ask Mr. Brown or Selim Bey. Mail a.b@example.com\n"
                    "Also Kerim Kaya signs.", encoding="utf-8")
    src = ingest_file(led, memo, custody="subject_held", origin_party="owner", names=["Kerim Kaya"])["source"]
    text = led.source_text(src["id"])
    for clear in ("Ahmet Yilmaz", "Brown", "Selim", "Kerim Kaya", "a.b@example.com"):
        assert clear not in text
    other = Ledger.init(tmp_path / "w2", name="t", subject="Acme", mode="engaged", authorization="m")
    assert other.pseudonymizer.person("Ahmet Yilmaz") != led.pseudonymizer.person("Ahmet Yilmaz")
    led.save()
    stored = (tmp_path / "w" / ".reb" / "pseudonyms.json").read_text(encoding="utf-8")
    assert "a.b@example.com" not in stored and "Ahmet Yilmaz" in stored
    monkeypatch.setenv("REB_PSEUDONYM_DIR", str(tmp_path / "keys"))
    led2 = Ledger.load(tmp_path / "w")
    led2.pseudonymizer.person("Someone Else")
    led2.save()
    assert (tmp_path / "keys" / f"{led2.engagement.id}.json").exists()


def test_kind_override_across_families_needs_reason(tmp_path):
    from reb.application.ingest import ingest_file

    led = Ledger.init(tmp_path / "w", name="t", subject="Acme", mode="engaged", authorization="m")
    f = tmp_path / "payroll.csv"
    f.write_text("name,salary\nX,1000\n", encoding="utf-8")
    with pytest.raises(RebError) as err:
        ingest_file(led, f, kind="document", custody="subject_held", origin_party="owner")
    assert err.value.code == "kind_override_reason_required"
    res = ingest_file(led, f, kind="document", custody="subject_held", origin_party="owner",
                      kind_reason="exported memo table, read as text")
    assert "kind override" in res["source"]["notes"]
