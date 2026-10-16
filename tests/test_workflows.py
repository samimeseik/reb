from __future__ import annotations

import json

import pytest

from conftest import EXAMPLE, add_text_source
from reb.application import analysis, coverage, ingest, report
from reb.domain.errors import RebError
from reb.domain.guardrails import Pseudonymizer
from reb.providers import efatura, whatsapp

CHAT = EXAMPLE / "WhatsApp Chat - Siparisler.txt"


def test_whatsapp_parses_ios_and_android():
    text = (
        "[16/10/2026, 09:15:22] Ali: #12 sipariş alındı\n"
        "devamı burada\n"
        "16.10.2026 10:20 - Ayşe: #12 teslim edildi\n"
    )
    msgs = whatsapp.parse_text(text)
    assert [m.sender for m in msgs] == ["Ali", "Ayşe"]
    assert "devamı" in msgs[0].body


def test_pseudonymizer_keeps_dates_and_amounts():
    p = Pseudonymizer()
    out = p.scrub("16.10.2026 09:15 tutar 12.500.000 TL, tel 0532 111 22 33, a@b.co, Ahmet geldi", names=["Ahmet"])
    assert "16.10.2026 09:15" in out and "12.500.000" in out
    assert "0532" not in out and "a@b.co" not in out and "Ahmet" not in out


def test_ingest_chat_pseudonymizes_senders_and_first_names(ledger):
    res = ingest.ingest_file(ledger, CHAT, custody="subject_held", origin_party="orders group",
                             controller="workshop", legal_basis="notice-1")
    text = ledger.source_text(res["source"]["id"])
    for name in ("Selin", "Ahmet", "Mehmet", "Yusuf"):
        assert name not in text
    assert "0532" not in text


def test_efatura_parse():
    inv = efatura.parse(EXAMPLE / "invoices" / "invoice-001.xml")[0]
    assert inv["supplier"]["tax_id"] == "9999999999"
    assert inv["payable"] > inv["tax_exclusive"]
    assert inv["lines"][0]["item"]


def test_process_mining_from_chat(ledger):
    res = ingest.ingest_file(ledger, CHAT, custody="subject_held", origin_party="orders group",
                             controller="workshop", legal_basis="notice-1")
    amap = json.loads((EXAMPLE / "activity-map.json").read_text(encoding="utf-8"))
    pm = analysis.analyze_event_log(ledger, res["source"]["id"], activity_map=amap, case_pattern=r"#(\d+)")
    assert pm["cases"] == 24
    assert pm["grade"] == "C"  # derived from a subject-held chat
    slowest = max(pm["edges"], key=lambda e: e["median_hours"])
    assert (slowest["from"], slowest["to"]) == ("assembly", "paint")
    assert pm["rework"]["cases"] > 0
    assert pm["mermaid"].startswith("flowchart LR")


def test_process_mining_from_table(ledger, tmp_path):
    csv_path = tmp_path / "log.csv"
    csv_path.write_text("case,activity,ts\n1,a,2026-01-01 08:00\n1,b,2026-01-01 10:00\n2,a,2026-01-02 08:00\n2,b,2026-01-02 12:00\n")
    res = ingest.ingest_file(ledger, csv_path, custody="captured_live", origin_party="erp", kind="event_log")
    pm = analysis.analyze_event_log(ledger, res["source"]["id"], case_column="case", activity_column="activity", time_column="ts")
    assert pm["cases"] == 2 and pm["cycle_time_hours"]["median"] in (2.0, 3.0, 4.0)


def test_invoice_concentration(ledger):
    ids = [
        ingest.ingest_file(ledger, f, custody="subject_held", origin_party="acct")["source"]["id"]
        for f in sorted((EXAMPLE / "invoices").glob("*.xml"))
    ]
    res = analysis.analyze_invoices(ledger, ids)
    assert res["invoices"] == 8 and 0 < res["top1_share"] <= 1 and res["hhi"] > 0


def test_stated_vs_enacted_opens_contradiction(ledger):
    sop = add_text_source(ledger, "lead time 10 days")
    log = add_text_source(ledger, "log", kind="system_export", controller="erp")
    es = ledger.add_evidence(source_id=sop.id, fact="10d", authority="governing_document")
    ee = ledger.add_evidence(source_id=log.id, fact="15d", authority="system_record")
    ledger.record_claim(statement="Stated lead time 10 days.", layer="operations", kind="stated",
                        metric="lead_time_days", value=10, evidence_ids=[es.id], item="ops.core-process")
    ledger.record_claim(statement="Enacted lead time 15 days.", layer="operations", kind="enacted",
                        metric="lead_time_days", value=15, evidence_ids=[ee.id], item="ops.core-process")
    res = analysis.compare_stated_vs_enacted(ledger, metric="lead_time_days")
    assert res["opened_unknowns"]
    cov = coverage.inspect_coverage(ledger)
    item = next(i for i in cov["items"] if i["item"] == "ops.core-process")
    assert item["state"] == "contradicted"


def test_obligation_rejects_circular_verifier(ledger):
    log = add_text_source(ledger, "log", kind="system_export", controller="erp")
    ev = ledger.add_evidence(source_id=log.id, fact="queue at paint", authority="system_record")
    ev2 = ledger.add_evidence(source_id=log.id, fact="queue at paint on peak day", authority="system_record")
    coverage.record_obligation(ledger, item="ops.bottleneck", owner="manager",
                               case_evidence={"happy_path": [ev.id], "peak_load": [ev2.id]})
    ob = coverage.record_verification(ledger, item="ops.bottleneck", source_id=log.id, kind="prediction",
                                      result="pass", fact="queue predicted and seen in the same log")["obligation"]
    assert ob["status"] == "open" and any("circular" in r for r in ob["reasons"])


def test_obligation_desk_review_too_weak_for_system_records(ledger):
    log = add_text_source(ledger, "log", kind="system_export", controller="erp", custody="captured_live")
    walk = add_text_source(ledger, "walk", kind="observation", custody="captured_live", controller="analyst")
    ev = ledger.add_evidence(source_id=log.id, fact="queue", authority="system_record")
    ev_peak = ledger.add_evidence(source_id=log.id, fact="queue on peak day", authority="system_record")
    coverage.record_obligation(ledger, item="ops.bottleneck", owner="manager",
                               case_evidence={"happy_path": [ev.id], "peak_load": [ev_peak.id]})
    ob = coverage.record_verification(ledger, item="ops.bottleneck", source_id=walk.id, kind="desk_review",
                                      result="pass", fact="queue seen")["obligation"]
    assert ob["status"] == "open"
    ob = coverage.record_verification(ledger, item="ops.bottleneck", source_id=walk.id, kind="prediction",
                                      result="pass", fact="predicted queue seen at paint")["obligation"]
    ob = ledger.data.obligations["ops.bottleneck"]
    assert ob.status.value == "ready"


def test_report_shows_conjecture_and_unknowns(ledger):
    ledger.record_claim(statement="Customers mostly come via architects.", layer="revenue", industry_prior=True)
    ledger.record_unknown(question="Which licences are held?", layer="regulation")
    text_en = report.render_report(ledger, language="en")
    assert "Conjecture" in text_en and "Which licences are held?" in text_en
    text_ar = report.render_report(ledger, language="ar")
    assert text_ar.startswith('<div dir="rtl">') and "تخمين" in text_ar


def test_unknown_profile_errors():
    from reb.profiles import load_profile

    with pytest.raises(RebError):
        load_profile("nope")


# ---------------------------------------------------------------- review regressions


def test_grade_inflation_by_labels_is_refused(ledger):
    from reb.domain.models import Custody

    with pytest.raises(RebError) as err:
        add_text_source(ledger, "sop", kind="document", custody="captured_live")
    assert err.value.code == "custody_mismatch"
    sop = add_text_source(ledger, "sop text")
    with pytest.raises(RebError) as err:
        ledger.add_evidence(source_id=sop.id, fact="x", authority="system_record")
    assert err.value.code == "authority_mismatch"
    with pytest.raises(RebError) as err:
        add_text_source(ledger, "inv", kind="einvoice", custody=Custody.ISSUER_VERIFIABLE.value)
    assert err.value.code == "verification_required"
    check = add_text_source(ledger, "gib lookup screenshot", kind="image", custody="captured_live", controller="analyst")
    inv = add_text_source(ledger, "inv2", kind="einvoice", custody="issuer_verifiable", controller="tax portal",
                          verification_ids=[check.id])
    assert ledger.add_evidence(source_id=inv.id, fact="invoice", authority="system_record").grade.value == "A"


def test_staff_interviews_never_triangulate(ledger):
    evs = []
    for role in ("foreman", "accountant", "driver"):
        src = add_text_source(ledger, f"{role} says 10 days", kind="interview", custody="captured_live",
                              controller=f"interviewee:{role}")
        assert src.controller == "subject:Test Co"
        evs.append(ledger.add_evidence(source_id=src.id, fact="10 days", authority="testimony").id)
    c = ledger.record_claim(statement="Lead time is 10 days.", layer="operations", evidence_ids=evs)
    assert c.status.value == "single_source"


def test_whatsapp_12h_and_arabic_locale_formats():
    ios12 = "[10/16/26, 9:15:22 AM] Ali: #1 sipariş\n[10/16/26, 1:05:00 PM] Ali: #1 teslim\n"
    msgs = whatsapp.parse_text(ios12)
    assert len(msgs) == 2 and msgs[0].timestamp.month == 10 and msgs[1].timestamp.hour == 13
    arabic = "16/10/2026، 9:15 م - سامي: #1 طلب جديد\n17/10/2026، 8:00 ص - سامي: #1 تم التسليم\n"
    msgs = whatsapp.parse_text(arabic)
    assert len(msgs) == 2 and msgs[0].timestamp.hour == 21 and msgs[1].timestamp.hour == 8


def test_renamed_chat_is_detected_and_needs_consent(ledger, tmp_path):
    f = tmp_path / "notes.txt"
    f.write_text(CHAT.read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(RebError) as err:
        ingest.ingest_file(ledger, f, custody="subject_held", origin_party="x", kind="document")
    assert err.value.code == "kind_mismatch"
    with pytest.raises(RebError) as err:
        ingest.ingest_file(ledger, f, custody="subject_held", origin_party="x")
    assert err.value.code == "consent_required"


@pytest.mark.parametrize("suffix", [".csv", ".md", ".log", ".json", ".tsv"])
def test_chat_saved_under_any_text_extension_is_still_a_chat(ledger, tmp_path, suffix):
    f = tmp_path / f"export{suffix}"
    f.write_text(CHAT.read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(RebError) as err:
        ingest.ingest_file(ledger, f, custody="subject_held", origin_party="x")
    assert err.value.code == "consent_required"
    res = ingest.ingest_file(ledger, f, custody="subject_held", origin_party="x", legal_basis="consent-1")
    assert res["source"]["kind"] == "chat_export"
    stored = ledger.source_text(res["source"]["id"])
    senders = {m.sender for m in whatsapp.parse_text(CHAT.read_text(encoding="utf-8"))}
    assert senders and not any(s in stored for s in senders)


def test_unparsed_chat_text_is_not_stored(ledger, tmp_path):
    f = tmp_path / "WhatsApp Chat.txt"
    f.write_text("Fatma Yilmaz said hello\nanother line\n", encoding="utf-8")
    res = ingest.ingest_file(ledger, f, custody="subject_held", origin_party="x", kind="chat_export", legal_basis="n")
    assert res["text_available"] is False


def test_names_are_scrubbed_across_sources_on_word_boundaries(ledger, tmp_path):
    ingest.ingest_file(ledger, CHAT, custody="subject_held", origin_party="g", legal_basis="n")
    note = tmp_path / "note.txt"
    note.write_text("Mehmet set it up. Canlı yayın.", encoding="utf-8")
    res = ingest.ingest_file(ledger, note, custody="subject_held", origin_party="owner")
    text = ledger.source_text(res["source"]["id"])
    assert "Mehmet" not in text and "Canlı yayın" in text
    ev = ledger.add_evidence(source_id=res["source"]["id"], fact="Mehmet sets up the machine", authority="governing_document",
                             quote="Mehmet set it up.")
    assert "Mehmet" not in ev.fact and "Mehmet" not in ev.quote


def test_efatura_person_names_and_tckn_are_scrubbed(ledger, tmp_path):
    import re

    xml = (EXAMPLE / "invoices" / "invoice-001.xml").read_text(encoding="utf-8")
    customer = (
        "<cac:AccountingCustomerParty><cac:Party>"
        '<cac:PartyIdentification><cbc:ID schemeID="TCKN">12345678901</cbc:ID></cac:PartyIdentification>'
        "<cac:PartyName><cbc:Name>Ayşe Demir</cbc:Name></cac:PartyName>"
        "</cac:Party></cac:AccountingCustomerParty>"
    )
    xml = re.sub(r"<cac:AccountingCustomerParty>.*?</cac:AccountingCustomerParty>", customer, xml, flags=re.S)
    f = tmp_path / "inv.xml"
    f.write_text(xml, encoding="utf-8")
    res = ingest.ingest_file(ledger, f, custody="subject_held", origin_party="acct")
    blob = json.dumps(res, ensure_ascii=False) + (ledger.source_text(res["source"]["id"]) or "")
    assert "12345678901" not in blob and "Ayşe Demir" not in blob
    out = analysis.analyze_invoices(ledger, [res["source"]["id"]])
    assert "12345678901" not in json.dumps(out)


def test_obligation_not_ready_on_low_grade_or_same_source_verifier(ledger):
    guess = add_text_source(ledger, "notes", controller="analyst-notes", custody="captured_live", kind="observation")
    e = ledger.add_evidence(source_id=guess.id, fact="guess", authority="analyst_inference", confidence="inferred")
    e2 = ledger.add_evidence(source_id=guess.id, fact="guess at peak", authority="analyst_inference",
                             confidence="inferred")
    coverage.record_obligation(ledger, item="ops.bottleneck", owner="m",
                               case_evidence={"happy_path": [e.id], "peak_load": [e2.id]})
    coverage.record_verification(ledger, item="ops.bottleneck", source_id=guess.id, kind="pilot",
                                 result="pass", fact="pilot noted in the same notes")
    ob = ledger.data.obligations["ops.bottleneck"]
    assert ob.status.value == "open"
    assert any("below grade" in r for r in ob.reasons) and any("circular" in r for r in ob.reasons)


def test_contradiction_cannot_be_dismissed_without_evidence(ledger):
    u = ledger.record_unknown(question="Why 10 vs 15 days?", status="contradicted")
    with pytest.raises(RebError):
        ledger.update_unknown(u.id, revision=1, status="investigating")
    with pytest.raises(RebError):
        ledger.update_unknown(u.id, revision=1, status="resolved", resolution={"kind": "out_of_scope", "note": "n"})


def test_concurrent_ingests_do_not_lose_sources(ledger, tmp_path):
    import subprocess
    import sys

    files = []
    for i in range(12):
        f = tmp_path / f"doc{i}.txt"
        f.write_text(f"document {i}", encoding="utf-8")
        files.append(f)
    procs = [
        subprocess.Popen([sys.executable, "-m", "reb.cli", "-w", str(ledger.workspace), "ingest", str(f),
                          "--custody", "subject_held", "--origin", "office"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        for f in files
    ]
    assert all(p.wait() == 0 for p in procs)
    from reb.domain.ledger import Ledger

    assert len(Ledger.load(ledger.workspace).data.sources) == 12


def test_changed_original_is_refused(ledger, tmp_path):
    f = tmp_path / "log.csv"
    f.write_text("case,activity,ts\n1,a,2026-01-01 08:00\n1,b,2026-01-01 10:00\n")
    res = ingest.ingest_file(ledger, f, custody="subject_held", origin_party="erp", kind="event_log")
    f.write_text("case,activity,ts\n1,a,2026-01-01 08:00\n1,b,2026-03-01 10:00\n")
    with pytest.raises(RebError) as err:
        analysis.analyze_event_log(ledger, res["source"]["id"], case_column="case", activity_column="activity", time_column="ts")
    assert err.value.code == "source_changed"


def test_compare_handles_zero_units_and_entities(ledger):
    log = add_text_source(ledger, "log", kind="system_export", controller="erp")
    ev = ledger.add_evidence(source_id=log.id, fact="x", authority="system_record")
    ledger.record_claim(statement="Stated scrap 0.1 percent.", layer="operations", kind="stated", metric="scrap",
                        value=0.1, unit="%", entity="line1", evidence_ids=[ev.id])
    ledger.record_claim(statement="Enacted scrap 0 percent.", layer="operations", kind="enacted", metric="scrap",
                        value=0, unit="%", entity="line1", evidence_ids=[ev.id])
    ledger.record_claim(statement="Enacted scrap line 2.", layer="operations", kind="enacted", metric="scrap",
                        value=5, unit="%", entity="line2", evidence_ids=[ev.id])
    ledger.record_claim(statement="Enacted scrap in kg.", layer="operations", kind="enacted", metric="scrap",
                        value=0.1, unit="kg", entity="line1", evidence_ids=[ev.id])
    res = analysis.compare_stated_vs_enacted(ledger, metric="scrap")
    assert len(res["pairs"]) == 1 and res["pairs"][0]["within_tolerance"] is False
    assert res["skipped"][0]["reason"] == "different units"


def test_invoice_analysis_is_order_independent_and_dedupes(ledger):
    files = sorted((EXAMPLE / "invoices").glob("*.xml"))[:3]
    held = [ingest.ingest_file(ledger, f, custody="subject_held", origin_party="acct")["source"]["id"] for f in files]
    a = analysis.analyze_invoices(ledger, held + held[:1])
    b = analysis.analyze_invoices(ledger, list(reversed(held)))
    assert a["grade"] == b["grade"] == "C" and a["invoices"] == b["invoices"] == 3


@pytest.mark.parametrize("field", ["fact", "question"])
def test_banned_vocabulary_everywhere(ledger, field):
    src = add_text_source(ledger, "x")
    with pytest.raises(RebError):
        if field == "fact":
            ledger.add_evidence(source_id=src.id, fact="Capacity is verified", authority="governing_document")
        else:
            ledger.record_unknown(question="Is the capacity guaranteed?")


def test_profile_mode_is_enforced(public_ledger):
    with pytest.raises(RebError) as err:
        coverage.inspect_coverage(public_ledger, "dd-evidence")
    assert err.value.code == "mode_not_allowed"


def test_empty_quote_is_refused(ledger):
    src = add_text_source(ledger, "abc")
    with pytest.raises(RebError):
        ledger.add_evidence(source_id=src.id, fact="f", authority="governing_document", quote="   ")


def test_cli_reports_invalid_input_without_traceback(ledger, capsys):
    from reb.cli import main

    src = add_text_source(ledger, "abc")
    ledger.save()
    code = main(["-w", str(ledger.workspace), "evidence", "--source", src.id, "--fact", "f", "--authority", "bogus"])
    assert code == 2 and "invalid_input" in capsys.readouterr().err


def test_obligation_needs_recorded_verifier_distinct_cases_and_no_blocking_unknown(ledger):
    log = add_text_source(ledger, "log", kind="system_export", controller="erp", custody="captured_live")
    audit = add_text_source(ledger, "recon", kind="system_export", controller="AuditCo", custody="third_party",
                            independent_channel=True)
    ev = ledger.add_evidence(source_id=log.id, fact="case 1 ran step a", authority="system_record")
    ev2 = ledger.add_evidence(source_id=log.id, fact="case 9 ran step a at peak", authority="system_record")
    ob = coverage.record_obligation(ledger, item="ops.bottleneck", owner="ops lead",
                                    case_evidence={"happy_path": [ev.id], "peak_load": [ev.id]},
                                    verifier={"kind": "reconciliation", "passed": True, "evidence_ids": []})
    assert ob.status.value == "open"
    assert any("not recorded" in r for r in ob.reasons) and any("different cases" in r for r in ob.reasons)
    ob.case_evidence["peak_load"] = [ev2.id]
    res = coverage.record_verification(ledger, item="ops.bottleneck", source_id=audit.id, kind="reconciliation",
                                       result="pass", fact="auditor reconciled cases 1 and 9")
    assert res["obligation"]["status"] == "ready", res["obligation"]["reasons"]
    u = ledger.record_unknown(question="Does the step depend on one person?", layer="operations", blocking=True)
    coverage.evaluate_obligation(ledger, ob)
    assert ob.status.value == "open" and any(u.id in r for r in ob.reasons)
    coverage.record_verification(ledger, item="ops.bottleneck", source_id=audit.id, kind="reconciliation",
                                 result="fail", fact="case 12 did not reconcile")
    assert ledger.data.obligations["ops.bottleneck"].status.value == "failed"
