"""Regression tests for the High findings of the external audit (audit/FINDINGS.md):
F-04 (chat consent by extension), F-06 (`ready` gating), F-02 (typed observations)."""

from __future__ import annotations

from pathlib import Path

import pytest

from reb.application import coverage
from reb.application.ingest import ingest_file, record_observation
from reb.domain.errors import RebError
from reb.domain.ledger import Ledger

from conftest import add_text_source

CHAT = "16.10.2026 09:15 - Ahmet Usta: siparis hazir\n16.10.2026 09:16 - Ali Kaya: tamam\n" * 5


def _engaged(tmp_path: Path, profile: str | None = None) -> Ledger:
    return Ledger.init(tmp_path, name="t", subject="Acme", mode="engaged", authorization="mandate-1", profile=profile)


def _write(tmp_path: Path, name: str, text: str) -> Path:
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


# ------------------------------------------------------------ F-04


@pytest.mark.parametrize("suffix", [".csv", ".md", ".log", ".json", ".tsv", ".text"])
def test_renamed_chat_needs_consent(tmp_path, suffix):
    led = _engaged(tmp_path)
    p = _write(tmp_path, "export" + suffix, CHAT)
    with pytest.raises(RebError) as err:
        ingest_file(led, p, custody="subject_held", origin_party="owner")
    assert err.value.code == "consent_required"
    # relabelling it as a spreadsheet/document does not skip the check either
    with pytest.raises(RebError) as err:
        ingest_file(led, p, kind="document", custody="subject_held", origin_party="owner")
    assert err.value.code == "kind_mismatch"


@pytest.mark.parametrize("suffix", [".csv", ".md", ".log", ".json"])
def test_renamed_chat_senders_are_pseudonymized(tmp_path, suffix):
    led = _engaged(tmp_path)
    p = _write(tmp_path, "export" + suffix, CHAT)
    res = ingest_file(led, p, kind="chat_export", custody="subject_held", origin_party="owner",
                      legal_basis="staff notice N-1")
    assert res["source"]["kind"] == "chat_export"
    text = led.source_text(res["source"]["id"]) or ""
    assert text and "Ahmet" not in text and "Ali Kaya" not in text


def test_chat_saved_as_quoted_csv_is_detected(tmp_path):
    led = _engaged(tmp_path)
    quoted = "".join(f'"{line}"\n' for line in CHAT.splitlines())
    p = _write(tmp_path, "export.csv", quoted)
    with pytest.raises(RebError):
        ingest_file(led, p, custody="subject_held", origin_party="owner")
    res = ingest_file(led, p, kind="chat_export", custody="subject_held", origin_party="owner", legal_basis="n-1")
    assert "Ahmet" not in (led.source_text(res["source"]["id"]) or "")


def test_plain_csv_is_still_a_spreadsheet(tmp_path):
    led = _engaged(tmp_path)
    p = _write(tmp_path, "orders.csv", "order,date\n1,2026-10-01\n2,2026-10-02\n")
    res = ingest_file(led, p, custody="subject_held", origin_party="owner")
    assert res["source"]["kind"] == "spreadsheet"


# ------------------------------------------------------------ F-06


def _obligation_setup(tmp_path):
    led = _engaged(tmp_path, profile="sop-replication")
    s1 = ingest_file(led, _write(tmp_path, "log.csv", "case,step\n1,a\n2,b\n"), custody="captured_live",
                     origin_party="erp")["source"]["id"]
    s2 = ingest_file(led, _write(tmp_path, "ext.csv", "case,ok\n1,yes\n"), custody="third_party",
                     origin_party="auditor", controller="AuditCo", independent_channel=True)["source"]["id"]
    ev = led.add_evidence(source_id=s1, fact="Case 1 ran step a", authority="system_record")
    ev_peak = led.add_evidence(source_id=s1, fact="Case 2 ran step b in the peak week", authority="system_record")
    return led, s2, ev, ev_peak


def test_ready_needs_recorded_verification_distinct_cases_and_no_layer_blocker(tmp_path):
    led, s2, ev, ev_peak = _obligation_setup(tmp_path)
    ver = led.add_evidence(source_id=s2, fact="Auditor ticked case 1", authority="system_record")
    led.record_unknown(question="Does the bottleneck step depend on one person?", layer="operations")
    ob = coverage.record_obligation(led, item="ops.bottleneck", owner="ops lead",
                                    case_evidence={"happy_path": [ev.id], "peak_load": [ev.id]},
                                    verifier={"kind": "reconciliation", "passed": True, "evidence_ids": [ver.id]})
    assert ob.status.value == "open"
    assert any("several cases" in r for r in ob.reasons)
    assert any("no recorded verification result" in r for r in ob.reasons)

    # distinct case evidence + a recorded verification result -> ready (open layer unknown is not blocking)
    led.data.obligations["ops.bottleneck"].case_evidence = {}
    coverage.record_obligation(led, item="ops.bottleneck",
                               case_evidence={"happy_path": [ev.id], "peak_load": [ev_peak.id]})
    res = coverage.record_verification(led, item="ops.bottleneck", kind="reconciliation", passed=True,
                                       source_id=s2, fact="Auditor's ticks match the log for cases 1-2",
                                       authority="system_record")
    assert res["evidence"]["operation"] == "verify:ops.bottleneck"
    assert res["obligation"]["status"] == "ready", res["obligation"]["reasons"]

    # a contradicted unknown on the same layer, not tagged with the item, blocks ready
    led.record_unknown(question="Why does the log show 2 shifts and the SOP 3?", layer="operations",
                       status="contradicted")
    ob = led.data.obligations["ops.bottleneck"]
    coverage.evaluate_obligation(led, ob)
    assert ob.status.value == "open" and any("layer operations" in r for r in ob.reasons)


def test_blocked_layer_unknown_blocks_ready(tmp_path):
    led, s2, ev, ev_peak = _obligation_setup(tmp_path)
    led.record_unknown(question="Can we see the payroll?", layer="operations", status="blocked")
    coverage.record_obligation(led, item="ops.bottleneck", owner="ops lead",
                               case_evidence={"happy_path": [ev.id], "peak_load": [ev_peak.id]})
    res = coverage.record_verification(led, item="ops.bottleneck", kind="reconciliation", passed=True,
                                       source_id=s2, fact="ticks match", authority="system_record")
    assert res["obligation"]["status"] == "open"


def test_case_reuse_needs_justification(tmp_path):
    led, s2, ev, _ = _obligation_setup(tmp_path)
    coverage.record_obligation(led, item="ops.bottleneck", owner="ops lead",
                               case_evidence={"happy_path": [ev.id], "peak_load": [ev.id]})
    res = coverage.record_verification(led, item="ops.bottleneck", kind="reconciliation", passed=True,
                                       source_id=s2, fact="ticks match", authority="system_record")
    assert res["obligation"]["status"] == "open"
    ob = coverage.record_obligation(led, item="ops.bottleneck",
                                    reuse_justification="The log row covers the peak week; there is one case.")
    assert ob.status.value == "ready", ob.reasons


def test_failed_verification_result_fails_the_obligation(tmp_path):
    led, s2, ev, ev_peak = _obligation_setup(tmp_path)
    coverage.record_obligation(led, item="ops.bottleneck", owner="ops lead",
                               case_evidence={"happy_path": [ev.id], "peak_load": [ev_peak.id]})
    res = coverage.record_verification(led, item="ops.bottleneck", kind="reconciliation", passed=False,
                                       source_id=s2, fact="case 2 missing from the auditor's sheet",
                                       authority="system_record")
    assert res["obligation"]["status"] == "failed"
    # an agent-typed passed flag cannot override the recorded failure
    ob = coverage.record_obligation(led, item="ops.bottleneck",
                                    verifier={"kind": "reconciliation", "passed": True,
                                              "evidence_ids": [res["evidence"]["id"]]})
    assert ob.status.value == "failed"


# ------------------------------------------------------------ F-02


def _subject_record(led, tmp_path):
    src = ingest_file(led, _write(tmp_path, "prod.csv", "day,units\nmon,500\n"), custody="subject_held",
                      origin_party="owner")["source"]["id"]
    return led.add_evidence(source_id=src, fact="Monday output was 500 units", authority="system_record")


def test_typed_observation_is_capped_and_does_not_triangulate(tmp_path):
    led = _engaged(tmp_path)
    e1 = _subject_record(led, tmp_path)
    obs = record_observation(led, title="walk", note="I saw roughly 500 units", observer_role="analyst",
                             legal_basis="staff notice", when="2026-10-12")
    e2 = obs["evidence"][0]
    assert e2["grade"] == "B"
    c = led.record_claim(statement="Daily output is about 500 units", layer="operations", evidence_ids=[e1.id, e2["id"]])
    assert c.status.value == "single_source"


def test_observation_with_artifact_keeps_grade_a_and_triangulates(tmp_path):
    led = _engaged(tmp_path)
    e1 = _subject_record(led, tmp_path)
    sheet = add_text_source(led, "count sheet: 498 units", controller="observer:analyst", custody="captured_live",
                            kind="image")
    obs = record_observation(led, title="walk", note="Counted 498 units", observer_role="analyst",
                             legal_basis="staff notice", when="2026-10-12", artifact_ids=[sheet.id])
    e2 = obs["evidence"][0]
    assert e2["grade"] == "A"
    c = led.record_claim(statement="Daily output is about 500 units", layer="operations", evidence_ids=[e1.id, e2["id"]])
    assert c.status.value == "triangulated"


def test_observation_sessions_on_two_days_triangulate(tmp_path):
    led = _engaged(tmp_path)
    e1 = _subject_record(led, tmp_path)
    o1 = record_observation(led, title="walk 1", note="About 500 units", observer_role="analyst",
                            legal_basis="staff notice", when="2026-10-12")["evidence"][0]["id"]
    o2 = record_observation(led, title="walk 2", note="About 490 units", observer_role="analyst",
                            legal_basis="staff notice", when="2026-10-14")["evidence"][0]["id"]
    c = led.record_claim(statement="Daily output is about 500 units", layer="operations", evidence_ids=[e1.id, o1, o2])
    assert c.status.value == "triangulated"


def test_two_observation_notes_on_the_same_day_do_not_triangulate(tmp_path):
    led = _engaged(tmp_path)
    e1 = _subject_record(led, tmp_path)
    o1 = record_observation(led, title="walk am", note="About 500 units", observer_role="analyst",
                            legal_basis="staff notice", when="2026-10-12 09:00")["evidence"][0]["id"]
    o2 = record_observation(led, title="walk pm", note="About 490 units", observer_role="analyst",
                            legal_basis="staff notice", when="2026-10-12 15:00")["evidence"][0]["id"]
    c = led.record_claim(statement="Daily output is about 500 units", layer="operations", evidence_ids=[e1.id, o1, o2])
    assert c.status.value == "single_source"
