"""Audit counter-tests. Each test asserts the behaviour a careful analyst would EXPECT.
A failure is a reproduced finding (see audit/FINDINGS.md), not a broken test."""
from pathlib import Path

import pytest

from reb.application.coverage import obligation_ledger, record_obligation
from reb.application.ingest import ingest_file, record_observation
from reb.domain.errors import RebError
from reb.domain.ledger import Ledger


def _eng(tmp_path, mode="engaged", profile=None):
    return Ledger.init(tmp_path, name="t", subject="Acme", mode=mode,
                       authorization=None if mode == "public" else "mandate-1", profile=profile)


def _write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


# F-01: a verbatim quote "supports" an unrelated fact; grade comes from the source, not the inference.
def test_quote_must_entail_fact(tmp_path):
    led = _eng(tmp_path)
    p = _write(tmp_path, "inv.csv", "invoice,amount\nINV-1,100\n")
    src = ingest_file(led, p, custody="captured_live", origin_party="erp")["source"]["id"]
    ev = led.add_evidence(source_id=src, fact="The company is highly profitable and collects all receivables",
                          authority="system_record", quote="INV-1,100")
    assert ev.grade.value != "A", "an A grade was attached to a profitability inference from one invoice line"


# F-02: an analyst-typed note becomes grade-A 'direct observation' and is independent of the subject,
# so it alone triangulates a subject-held record.
def test_typed_observation_triangulates(tmp_path):
    led = _eng(tmp_path)
    p = _write(tmp_path, "prod.csv", "day,units\nmon,500\n")
    src = ingest_file(led, p, custody="subject_held", origin_party="owner")["source"]["id"]
    e1 = led.add_evidence(source_id=src, fact="Monday output was 500 units", authority="system_record")
    obs = record_observation(led, title="walk", note="I saw roughly 500 units", observer_role="analyst",
                             legal_basis="staff notice")
    e2 = obs["evidence"][0]["id"]
    c = led.record_claim(statement="Daily output is about 500 units", layer="operations", evidence_ids=[e1.id, e2])
    assert not (c.status.value == "triangulated" and led.evidence(e2).grade.value == "A"), \
        "free-text observation with no artifact scored A and triangulated the claim"


# F-03: public mode, a press release and a news article that copied it, declared under different
# controllers with no upstream link -> 'triangulated'.
def test_public_copy_laundering(tmp_path):
    led = _eng(tmp_path, mode="public")
    a = _write(tmp_path, "press.md", "Acme serves 10,000 customers.")
    b = _write(tmp_path, "news.md", "Acme serves 10,000 customers, the company said.")
    sa = ingest_file(led, a, kind="document", custody="public", origin_party="acme", legal_basis="https://acme/p")
    sb = ingest_file(led, b, kind="document", custody="public", origin_party="newsco", legal_basis="https://news/x")
    e1 = led.add_evidence(source_id=sa["source"]["id"], fact="Acme says 10,000 customers",
                          authority="governing_document")
    e2 = led.add_evidence(source_id=sb["source"]["id"], fact="News reports 10,000 customers",
                          authority="governing_document")
    c = led.record_claim(statement="Acme has 10,000 customers", layer="customer", evidence_ids=[e1.id, e2.id])
    assert c.status.value != "triangulated", "a derived copy counted as independent corroboration"


# F-04: a WhatsApp export renamed to .csv skips the chat detection and the consent check.
def test_renamed_chat_needs_consent(tmp_path):
    led = _eng(tmp_path)
    chat = "16.10.2026 09:15 - Ahmet Usta: siparis hazir\n16.10.2026 09:16 - Ali: tamam\n" * 5
    p = _write(tmp_path, "export.csv", chat)
    with pytest.raises(RebError):
        ingest_file(led, p, custody="subject_held", origin_party="owner")


# F-05: public mode admits an internal export relabelled kind=document custody=public.
def test_public_mode_relabel(tmp_path):
    led = _eng(tmp_path, mode="public")
    p = _write(tmp_path, "payroll.xlsx.csv", "name,salary\nX,1000\n")
    with pytest.raises(RebError):
        ingest_file(led, p, kind="document", custody="public", origin_party="acme", legal_basis="n/a")


# F-06: obligation reaches READY with a self-asserted passing verifier while a material unknown
# (not tagged with the item id) is open.
def test_ready_despite_material_unknown(tmp_path):
    led = _eng(tmp_path, profile="sop-replication")
    p = _write(tmp_path, "log.csv", "case,step\n1,a\n")
    s1 = ingest_file(led, p, custody="captured_live", origin_party="erp")["source"]["id"]
    q = _write(tmp_path, "ext.csv", "case,ok\n1,yes\n")
    s2 = ingest_file(led, q, custody="third_party", origin_party="auditor", controller="AuditCo",
                     independent_channel=True)["source"]["id"]
    ev = led.add_evidence(source_id=s1, fact="Case 1 ran step a", authority="system_record")
    ver = led.add_evidence(source_id=s2, fact="Auditor ticked case 1", authority="system_record")
    led.record_unknown(question="Does the bottleneck step depend on one person?", layer="operations")
    ob = record_obligation(led, item="ops.bottleneck", owner="ops lead",
                           case_evidence={"happy_path": [ev.id], "peak_load": [ev.id]},
                           verifier={"kind": "reconciliation", "passed": True, "evidence_ids": [ver.id]})
    assert ob.status.value != "ready", "READY with one log row reused for two cases and an open layer unknown"


# F-07: a single low-grade contradicting item flips a triangulated grade-A claim to CONTRADICTED.
def test_weak_contradiction_dominates(tmp_path):
    led = _eng(tmp_path)
    p = _write(tmp_path, "a.csv", "x\n1\n")
    s1 = ingest_file(led, p, custody="captured_live", origin_party="erp")["source"]["id"]
    q = _write(tmp_path, "b.csv", "y\n2\n")
    s2 = ingest_file(led, q, custody="third_party", origin_party="bank", controller="Bank",
                     independent_channel=True)["source"]["id"]
    e1 = led.add_evidence(source_id=s1, fact="Paid on time", authority="system_record")
    e2 = led.add_evidence(source_id=s2, fact="Bank shows payment on time", authority="system_record")
    r = _write(tmp_path, "rumor.md", "someone said they pay late")
    s3 = ingest_file(led, r, kind="document", custody="subject_held", origin_party="staff")["source"]["id"]
    e3 = led.add_evidence(source_id=s3, fact="A staff member says payments are late",
                          authority="analyst_inference", confidence="inferred")
    c = led.record_claim(statement="Supplier payments are on time", layer="finance",
                         evidence_ids=[e1.id, e2.id], contradicting_evidence_ids=[e3.id])
    assert c.status.value != "contradicted", "an E-grade remark outweighed two independent A records"


# F-08: no way to retract evidence; a claim keeps citing evidence later found wrong.
def test_evidence_retraction_exists():
    assert hasattr(Ledger, "retract_evidence") or hasattr(Ledger, "withdraw_evidence")


# F-09: names not surfaced by the extractor (plain document) are stored in clear text.
def test_unknown_names_scrubbed(tmp_path):
    led = _eng(tmp_path)
    p = _write(tmp_path, "memo.md", "Ahmet Yilmaz approves every discount above 5%. Call 0532 111 22 33.")
    s = ingest_file(led, p, kind="document", custody="subject_held", origin_party="owner")["source"]["id"]
    text = led.source_text(s)
    assert "Ahmet Yilmaz" not in text, "person name stored un-pseudonymized"


# F-10: mapping file holds the clear identifiers next to the ledger (re-identification table).
def test_pseudonym_map_location(tmp_path):
    led = _eng(tmp_path)
    p = _write(tmp_path, "m.md", "mail me at a.b@example.com")
    ingest_file(led, p, kind="document", custody="subject_held", origin_party="owner")
    led.save()
    m = (tmp_path / ".reb" / "pseudonyms.json").read_text()
    assert "a.b@example.com" not in m, "re-identification map sits unencrypted beside the ledger"


# F-11: engaged mode, the subject's OWN public website is treated as independent of its handed-over records.
def test_own_website_not_independent(tmp_path):
    led = Ledger.init(tmp_path, name="t", subject="Hope Bridge", mode="engaged", authorization="m")
    w = _write(tmp_path, "site.md", "We served 12,000 families.")
    r = _write(tmp_path, "report.md", "Families served total 12,000.")
    sw = ingest_file(led, w, kind="public_signal", custody="public", origin_party="Hope Bridge",
                     legal_basis="https://hopebridge.example")["source"]["id"]
    sr = ingest_file(led, r, kind="document", custody="subject_held", origin_party="director")["source"]["id"]
    e1 = led.add_evidence(source_id=sw, fact="Website says 12,000 families", authority="public_signal")
    e2 = led.add_evidence(source_id=sr, fact="Report says 12,000 families", authority="governing_document")
    c = led.record_claim(statement="12,000 families served", layer="customer", evidence_ids=[e1.id, e2.id])
    assert c.status.value != "triangulated", "the organization's own website corroborated its own report"
