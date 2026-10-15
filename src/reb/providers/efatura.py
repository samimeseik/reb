"""UBL e-invoices (Turkish UBL-TR e-Fatura / e-Arşiv and other UBL 2.1 XML).

Each invoice carries a UUID (ETTN) that the issuing authority (GİB in Turkey)
can confirm. Register the source with custody `issuer_verifiable` only after
that check has been made and logged as its own source.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from . import Extraction, FactDraft

NS = {
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
}


def _text(node: ET.Element | None, path: str) -> str | None:
    if node is None:
        return None
    found = node.find(path, NS)
    return found.text.strip() if found is not None and found.text else None


def _party(root: ET.Element, role: str) -> dict[str, Any]:
    party = root.find(f"cac:{role}/cac:Party", NS)
    tax_id, scheme = None, None
    if party is not None:
        for pid in party.findall("cac:PartyIdentification/cbc:ID", NS):
            sid = (pid.get("schemeID") or "").upper()
            if sid in {"VKN", "TCKN"} or tax_id is None:
                tax_id, scheme = (pid.text or "").strip(), sid or None
    name = _text(party, "cac:PartyName/cbc:Name") or _text(party, "cac:PartyLegalEntity/cbc:RegistrationName")
    if not name and party is not None:  # natural persons carry Person/FirstName + FamilyName
        first, family = _text(party, "cac:Person/cbc:FirstName"), _text(party, "cac:Person/cbc:FamilyName")
        name = " ".join(p for p in (first, family) if p) or None
    # A TCKN (11 digits) identifies a natural person: their name is personal data.
    is_person = scheme == "TCKN" or (tax_id is not None and len(tax_id) == 11)
    return {"tax_id": tax_id, "scheme": scheme, "name": name, "person": is_person}


def _amount(value: str | None) -> float | None:
    try:
        return float(value) if value is not None else None
    except ValueError:
        return None


def parse(path: Path) -> list[dict[str, Any]]:
    tree = ET.parse(path)
    root = tree.getroot()
    invoices = [root] if root.tag.endswith("Invoice") else [
        el for el in root.iter() if el.tag.endswith("}Invoice")
    ]
    result = []
    for inv in invoices:
        lines = []
        for line in inv.findall("cac:InvoiceLine", NS):
            qty = line.find("cbc:InvoicedQuantity", NS)
            lines.append(
                {
                    "item": _text(line, "cac:Item/cbc:Name"),
                    "quantity": _amount(qty.text if qty is not None else None),
                    "unit": qty.get("unitCode") if qty is not None else None,
                    "amount": _amount(_text(line, "cbc:LineExtensionAmount")),
                }
            )
        result.append(
            {
                "id": _text(inv, "cbc:ID"),
                "uuid": _text(inv, "cbc:UUID"),
                "profile": _text(inv, "cbc:ProfileID"),
                "type": _text(inv, "cbc:InvoiceTypeCode"),
                "issue_date": _text(inv, "cbc:IssueDate"),
                "currency": _text(inv, "cbc:DocumentCurrencyCode"),
                "supplier": _party(inv, "AccountingSupplierParty"),
                "customer": _party(inv, "AccountingCustomerParty"),
                "payable": _amount(_text(inv, "cac:LegalMonetaryTotal/cbc:PayableAmount")),
                "tax_exclusive": _amount(_text(inv, "cac:LegalMonetaryTotal/cbc:TaxExclusiveAmount")),
                "lines": lines,
            }
        )
    return result


def extract(path: Path) -> Extraction:
    try:
        invoices = parse(path)
    except ET.ParseError as exc:
        return Extraction(provider="efatura", limitations=[f"Not a readable XML invoice: {exc}"])
    facts = []
    for inv in invoices:
        facts.append(
            FactDraft(
                fact=(
                    f"Invoice {inv['id']} dated {inv['issue_date']}: supplier tax id "
                    f"{inv['supplier']['tax_id']}, customer tax id {inv['customer']['tax_id']}, "
                    f"payable {inv['payable']} {inv['currency']}, {len(inv['lines'])} line(s)."
                ),
                operation="parse_invoice",
                location=f"invoice {inv['id']}",
                normalized=inv,
                layer="revenue",
                entity=inv["supplier"]["tax_id"],
                limitations=[
                    "Invoice UUID not yet confirmed with the issuing authority."
                ],
            )
        )
    text = "\n".join(
        f"{i['id']} {i['uuid']} {i['type']} {i['issue_date']} {i['supplier']['tax_id']} {i['customer']['tax_id']} "
        f"{i['customer']['name']} {i['payable']} {i['currency']}"
        for i in invoices
    )
    names = [
        p["name"] for i in invoices for p in (i["supplier"], i["customer"]) if p["person"] and p["name"]
    ]
    return Extraction(provider="efatura", text=text, facts=facts, rows=invoices, names=names)
