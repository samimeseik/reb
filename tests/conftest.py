from __future__ import annotations

from pathlib import Path

import pytest

from reb.domain.ledger import Ledger

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "furniture-workshop" / "data"


@pytest.fixture
def ledger(tmp_path: Path) -> Ledger:
    return Ledger.init(tmp_path, name="t", subject="Test Co", mode="self", authorization="owner", profile="sop-replication")


@pytest.fixture
def public_ledger(tmp_path: Path) -> Ledger:
    return Ledger.init(tmp_path, name="t", subject="Test Co", mode="public", profile="desk-scan")


def add_text_source(ledger: Ledger, text: str, *, controller: str = "org", custody: str = "subject_held",
                    kind: str = "document", legal_basis: str | None = "basis-ref", **kw):
    src, _ = ledger.add_source(content=text.encode(), kind=kind, custody=custody, title="doc",
                               origin_party=controller, controller=controller, text=text,
                               legal_basis=legal_basis, **kw)
    return src
