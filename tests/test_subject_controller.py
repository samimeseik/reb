"""F-11: the organization never corroborates itself, whatever custody or mode its source carries."""

from __future__ import annotations

import json

import pytest

from reb.domain.ledger import Ledger


def _src(led: Ledger, text: str, *, origin: str, custody: str, kind: str = "document",
         controller: str | None = None, legal_basis: str | None = "basis-ref"):
    src, _ = led.add_source(content=text.encode(), kind=kind, custody=custody, title=text[:20],
                            origin_party=origin, controller=controller, text=text, legal_basis=legal_basis)
    return src


def _claim(led: Ledger, a, b, auth_a: str, auth_b: str):
    ea = led.add_evidence(source_id=a.id, fact="a", authority=auth_a)
    eb = led.add_evidence(source_id=b.id, fact="b", authority=auth_b)
    return led.record_claim(statement="12,000 families served", layer="customer", evidence_ids=[ea.id, eb.id])


@pytest.mark.parametrize("origin", ["Hope Bridge", "hope bridge", "  HOPE   BRIDGE "])
def test_own_website_not_independent_of_handed_over_report(tmp_path, origin):
    led = Ledger.init(tmp_path, name="t", subject="Hope Bridge", mode="engaged", authorization="m")
    site = _src(led, "We served 12,000 families.", origin=origin, custody="public", kind="public_signal",
                legal_basis="https://hopebridge.example")
    report = _src(led, "Families served total 12,000.", origin="director", custody="subject_held")
    assert site.controller == report.controller == "subject:Hope Bridge"
    assert _claim(led, site, report, "public_signal", "governing_document").status.value != "triangulated"


def test_alias_and_domain_are_the_subject(tmp_path):
    led = Ledger.init(tmp_path, name="t", subject="Hope Bridge", mode="self", authorization="owner",
                      aliases=["HB Relief"], domains=["https://www.HopeBridge.example/"])
    assert led.engagement.domains == ["hopebridge.example"]
    by_alias = _src(led, "press release", origin="hb relief", custody="public", legal_basis="https://news.example/1")
    by_domain = _src(led, "about page", origin="website", custody="public", kind="public_signal",
                     legal_basis="https://donate.hopebridge.example/about")
    by_controller = _src(led, "annual report", origin="auditor", controller="HopeBridge.example",
                         custody="third_party")
    for s in (by_alias, by_domain, by_controller):
        assert s.controller == "subject:Hope Bridge", s.origin_party
    assert _claim(led, by_alias, by_domain, "governing_document", "public_signal").status.value != "triangulated"


def test_subject_normalized_in_public_mode(tmp_path):
    led = Ledger.init(tmp_path, name="t", subject="Acme", mode="public", domains=["acme.example"])
    release = _src(led, "Acme ships 5,000 units.", origin="Acme", custody="public", legal_basis="https://acme.example/pr")
    blog = _src(led, "We ship 5,000 units.", origin="marketing", custody="public", kind="public_signal",
                legal_basis="https://blog.acme.example/post")
    assert release.controller == blog.controller == "subject:Acme"
    assert _claim(led, release, blog, "governing_document", "public_signal").status.value != "triangulated"


def test_unrelated_public_source_stays_independent(tmp_path):
    led = Ledger.init(tmp_path, name="t", subject="Acme", mode="public", aliases=["Acme Ltd"], domains=["acme.example"])
    # lookalike names and domains are not the subject
    for origin, url in [("Acme Ltd Watch", "https://notacme.example/x"), ("registry", "https://acme.example.org/x")]:
        src = _src(led, f"{origin} text", origin=origin, custody="public", legal_basis=url)
        assert src.controller == origin
    news = _src(led, "Acme ships 5,000 units, records show.", origin="newsco", custody="public",
                legal_basis="https://newsco.example/acme")
    registry = _src(led, "Filing: 5,000 units.", origin="trade registry", custody="public", kind="public_record",
                    legal_basis="https://registry.example/acme")
    assert news.controller == "newsco"
    assert _claim(led, news, registry, "governing_document", "public_record").status.value == "triangulated"


def test_old_ledger_without_aliases_still_loads(tmp_path):
    Ledger.init(tmp_path, name="t", subject="Acme", mode="public")
    path = tmp_path / ".reb" / "ledger.json"
    data = json.loads(path.read_text())
    data["engagement"].pop("aliases")
    data["engagement"].pop("domains")
    path.write_text(json.dumps(data))
    with Ledger.open(tmp_path) as led:
        assert led.engagement.aliases == [] and led.engagement.domains == []


def test_cli_init_accepts_aliases_and_domains(tmp_path, capsys):
    from reb.cli import main

    code = main(["-w", str(tmp_path), "init", "--name", "t", "--subject", "Acme", "--mode", "public",
                 "--alias", "Acme Ltd", "--alias", "ACME Group", "--domain", "www.acme.example"])
    assert code == 0
    with Ledger.open(tmp_path) as led:
        assert led.engagement.aliases == ["Acme Ltd", "ACME Group"]
        assert led.engagement.domains == ["acme.example"]
