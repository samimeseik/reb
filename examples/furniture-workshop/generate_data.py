"""Generate the synthetic furniture-workshop dataset (deterministic).

Everything here is invented. The workshop, people, tax ids and invoices do not exist.
Run: python generate_data.py   (writes into ./data)
"""

from __future__ import annotations

import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(7)
DATA = Path(__file__).parent / "data"
DATA.mkdir(exist_ok=True)

STAFF = {"office": "Selin Ofis", "usta": "Ahmet Usta", "cnc": "Mehmet CNC", "paint": "Yusuf Boya"}
CUSTOMERS = [
    ("1111111111", "Örnek Mimarlık Ltd."),
    ("2222222222", "Deneme Otel A.Ş."),
    ("3333333333", "Bireysel Müşteri"),
    ("4444444444", "Test Kafe"),
]
PRODUCTS = ["mutfak dolabı", "gardırop", "TV ünitesi", "banyo dolabı"]

# activity -> (who posts it, message template, hours after previous step (min, max))
STEPS = [
    ("order", "office", "#{oid} sipariş alındı – {product}", (0, 0)),
    ("measure", "usta", "#{oid} ölçü alındı ✅", (20, 60)),
    ("cut", "cnc", "#{oid} kesim başladı", (30, 120)),
    ("edge", "cnc", "#{oid} kenar bantlama bitti", (6, 30)),
    ("assembly", "usta", "#{oid} montaj tamam", (10, 48)),
    ("paint", "paint", "#{oid} boyaya girdi", (60, 200)),  # the spray booth queue
    ("deliver", "office", "#{oid} teslim edildi, müşteri memnun", (24, 72)),
]

messages: list[tuple[datetime, str, str]] = []
orders = []
start = datetime(2026, 7, 1, 9, 0)
for n in range(24):
    oid = 1001 + n
    product = random.choice(PRODUCTS)
    vkn, cname = random.choice(CUSTOMERS)
    t = start + timedelta(days=n * 2.5, hours=random.randint(0, 6))
    order_time = t
    for act, who, tpl, (lo, hi) in STEPS:
        t = t + timedelta(hours=random.randint(lo, hi))
        messages.append((t, STAFF[who], tpl.format(oid=oid, product=product)))
        if act == "paint" and random.random() < 0.25:  # repaint = rework
            t = t + timedelta(hours=random.randint(24, 60))
            messages.append((t, STAFF["paint"], f"#{oid} renk tutmadı, tekrar boyaya girdi"))
    amount = random.choice([18000, 26000, 34000, 52000, 75000])
    orders.append({"order_id": oid, "customer_vkn": vkn, "product": product,
                   "order_date": order_time.strftime("%d.%m.%Y"), "delivery_date": t.strftime("%d.%m.%Y"),
                   "amount_try": amount})

# a few non-order messages, including a phone number that must be pseudonymized
messages.append((datetime(2026, 7, 14, 11, 5), STAFF["usta"], "Kenar bant makinesini 2mm PVC için sadece Mehmet ayarlayabiliyor"))
messages.append((datetime(2026, 8, 2, 16, 40), STAFF["office"], "Tedarikçi Kaya Kereste yeni numara: 0532 111 22 33"))
messages.sort()

with open(DATA / "WhatsApp Chat - Siparisler.txt", "w", encoding="utf-8") as fh:
    for ts, who, body in messages:
        fh.write(f"[{ts.strftime('%d/%m/%Y, %H:%M:%S')}] {who}: {body}\n")

with open(DATA / "orders.csv", "w", newline="", encoding="utf-8") as fh:
    writer = csv.DictWriter(fh, fieldnames=list(orders[0].keys()))
    writer.writeheader()
    writer.writerows(orders)

INVOICE = """<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
 xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
 xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <cbc:ProfileID>TICARIFATURA</cbc:ProfileID>
  <cbc:ID>{id}</cbc:ID>
  <cbc:UUID>{uuid}</cbc:UUID>
  <cbc:IssueDate>{date}</cbc:IssueDate>
  <cbc:InvoiceTypeCode>SATIS</cbc:InvoiceTypeCode>
  <cbc:DocumentCurrencyCode>TRY</cbc:DocumentCurrencyCode>
  <cac:AccountingSupplierParty><cac:Party>
    <cac:PartyIdentification><cbc:ID schemeID="VKN">9999999999</cbc:ID></cac:PartyIdentification>
    <cac:PartyName><cbc:Name>Örnek Mobilya Atölyesi</cbc:Name></cac:PartyName>
  </cac:Party></cac:AccountingSupplierParty>
  <cac:AccountingCustomerParty><cac:Party>
    <cac:PartyIdentification><cbc:ID schemeID="VKN">{vkn}</cbc:ID></cac:PartyIdentification>
    <cac:PartyName><cbc:Name>{cname}</cbc:Name></cac:PartyName>
  </cac:Party></cac:AccountingCustomerParty>
  <cac:LegalMonetaryTotal>
    <cbc:TaxExclusiveAmount currencyID="TRY">{net}</cbc:TaxExclusiveAmount>
    <cbc:PayableAmount currencyID="TRY">{gross}</cbc:PayableAmount>
  </cac:LegalMonetaryTotal>
  <cac:InvoiceLine>
    <cbc:ID>1</cbc:ID>
    <cbc:InvoicedQuantity unitCode="C62">1</cbc:InvoicedQuantity>
    <cbc:LineExtensionAmount currencyID="TRY">{net}</cbc:LineExtensionAmount>
    <cac:Item><cbc:Name>{product}</cbc:Name></cac:Item>
  </cac:InvoiceLine>
</Invoice>
"""
inv_dir = DATA / "invoices"
inv_dir.mkdir(exist_ok=True)
for i, o in enumerate(orders[:8], start=1):
    cname = dict(CUSTOMERS)[o["customer_vkn"]]
    d = datetime.strptime(o["delivery_date"], "%d.%m.%Y").strftime("%Y-%m-%d")
    net = o["amount_try"]
    (inv_dir / f"invoice-{i:03d}.xml").write_text(
        INVOICE.format(id=f"OMA2026{i:09d}", uuid=f"00000000-0000-4000-8000-{i:012d}", date=d,
                       vkn=o["customer_vkn"], cname=cname, net=f"{net:.2f}", gross=f"{net * 1.2:.2f}",
                       product=o["product"]),
        encoding="utf-8",
    )

(DATA / "activity-map.json").write_text(json.dumps({
    "order": ["sipariş alındı"],
    "measure": ["ölçü alındı"],
    "cut": ["kesim başladı"],
    "edge": ["kenar bantlama"],
    "assembly": ["montaj tamam"],
    "paint": ["boyaya girdi"],
    "deliver": ["teslim edildi"],
}, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"wrote {len(messages)} messages, {len(orders)} orders, 8 invoices to {DATA}")
