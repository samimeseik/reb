# Roadmap

## v0.1 (this release)
- **Engine:** evidence grading (authority × custody × confidence), source independence, stated vs enacted, unknowns with revisions, obligation ledger, coverage across 11 layers, banned vocabulary, pseudonymization.
- **Providers:** text/MD/DOCX/PDF, image OCR, CSV/XLSX, WhatsApp exports, UBL e-invoices (e-Fatura), audio transcription.
- **Analyses:** process discovery from tables and chats, invoice concentration.
- **Profiles:** `sop-replication`, `dd-evidence`, `factory-capacity`, `hiring-system`, `it-systems`, `desk-scan`.
- **Interfaces:** CLI, MCP server, agent skill, Arabic and English reports.

## Next
- **OCEL 2.0 / XES export**, plus an optional pm4py adapter for BPMN discovery and conformance (fitness as a `conformance` verifier).
- **ERP extract templates:** Logo, Netsis, Mikro (MS SQL), Odoo, ERPNext, and common POS exports.
- **Equipment:** nameplate field parser (maker, model, year, kW, serial); OEE from downtime and production logs; capacity vs utility consumption.
- **Interviews:** speaker diarization; interview protocol templates (critical incident, DACUM, RACI) in Arabic and Turkish.
- **People:** organizational network analysis from consented surveys; role cards; RACI rendering.
- **Unit economics:** BOM × labour minutes × loaded rate plus overhead drivers, verified by reconciliation against invoices.
- **Outputs:** BPMN 2.0 XML, value stream map, ISO 9001-style SOP pack (AR/TR/EN), evidence bundle export/import, report diff between versions.
- **Hand-off to REA** for software found in the systems map.
- **Retention:** `retention_until` enforcement and a destruction log.

Contributions welcome. See [CONTRIBUTING.md](../CONTRIBUTING.md).
