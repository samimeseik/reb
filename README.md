<div align="center">

**English** · [العربية](README.ar.md)

# REB: Reverse Engineer any Business

### Evidence-graded reverse engineering of how an organization actually works — for AI agents (MCP) and the terminal.

**See a business you want to understand. Find out how it really runs — with the evidence, and with what is still unknown.**

</div>

---

REB is a sibling of [REA — Reverse Engineer Anything](https://github.com/morluto/rea),
which reverse-engineers software. REB applies the same discipline to
**factories, workshops, companies, clinics, agencies — any organization**:
processes, machines, hiring, suppliers, systems, unit economics and the
know-how that lives only in people's heads.

The hard part of analysing a business is not producing a convincing story.
Consultants and language models do that too easily. A plausible but invented
process map reads perfectly well, while invented code at least fails to run.
REB exists to stop that:

- **Every claim is tied to evidence** with a computed grade (A–E). You do not get to choose the grade.
- **Missing coverage is unknown, not absent.** Gaps become explicit Unknowns with the cheapest probe that would close them.
- **What people say is kept apart from what records show** (*stated vs enacted*). Gaps between the two are recorded as contradictions instead of being averaged away.
- **Quotes are checked.** Evidence that quotes a source must match the source text verbatim.
- **Reconstructions close only on recorded evidence.** A rebuilt process or SOP item is `ready` only with an owner, its own evidence for every required case, a recorded verification result from an independent source, and no contradicted or blocked unknown on its layer. `ready` means the record is complete, not that the process will work. These are REA's reconstruction obligation ledgers, applied to organizations.
- **Copying has limits.** Each finding can be tagged as codifiable, needs a capability, needs an asset, or non-transferable (relationships, licences, location, timing, founder).

## Three modes, enforced by the engine

| Mode | When | What is admissible |
|---|---|---|
| `self` | You own or run the organization | Everything, with consent for interviews and chats |
| `engaged` | You hold a written mandate from it (consulting, due diligence with consent) | Everything, with consent for interviews and chats |
| `public` | Public sources only | Public records and public signals. Internal documents, exports, chats and interviews are **rejected by the engine** |

REB is not a tool for obtaining someone else's trade secrets. Read [docs/LEGAL.md](docs/LEGAL.md).

## What it reads

| Source | Provider | What REB returns |
|---|---|---|
| Text, Markdown, DOCX, PDF (`[pdf]`) | `documents` | Text with line/page locations for quoting |
| Photos, scans, nameplates (`[ocr]`, Tesseract `ara+tur+eng`) | `ocr` | Recognized text, flagged as OCR |
| CSV / TSV / XLSX (`[excel]`) exports | `spreadsheet` | Columns, rows, date coverage; rows for process mining |
| WhatsApp chat exports (iOS / Android, AR/TR/EN) | `whatsapp` | Messages, participants, period. Senders are pseudonymized |
| UBL e-invoices (Turkish e-Fatura / e-Arşiv, UBL 2.1) | `efatura` | Invoice id, UUID, parties' tax ids, totals, lines |
| Interview audio (`[audio]`, faster-whisper) or transcripts | `whisper` | Time-stamped transcript, held as testimony |
| Site walks and time studies | `observation` | Direct-observation evidence |

Analyses:
- **Process mining** from event tables or chat exports: variants, a directly-follows graph (exported as Mermaid), cycle times, rework.
- **Invoice concentration**: top counterparties and HHI.
- **Stated vs enacted** comparison.
- **Coverage** across 11 layers.
- **Obligation ledger** and a **Markdown report** in Arabic or English.

## Profiles: one engine, many questions

| Profile | Use | Modes |
|---|---|---|
| `sop-replication` | Capture your own operating system to scale, franchise, hand over or sell | self, engaged |
| `dd-evidence` | Evidence file before buying or partnering, with consent. No valuation | engaged, self |
| `factory-capacity` | Can this factory make what it claims? | engaged, self |
| `hiring-system` | How people are found, selected, onboarded, paid and kept | self, engaged |
| `it-systems` | Systems and data map, manual hand-offs. Software internals go to REA | self, engaged |
| `desk-scan` | Public records and signals only: observations and questions | public |

Profiles are YAML. Add your own with `reb coverage --profile path/to/profile.yaml`.

## Quick start

```bash
pip install "reb-agents[mcp,excel,pdf]"     # or: uv pip install -e ".[mcp,excel,pdf]"

mkdir my-workshop && cd my-workshop
reb init --name "Workshop capture" --subject "Our workshop" --mode self \
         --authorization "owner" --profile sop-replication --language en

reb ingest ~/exports/orders.csv --custody subject_held --origin "workshop office"
reb ingest "~/exports/WhatsApp Chat - Orders.txt" --custody subject_held \
         --origin "orders group" --legal-basis "staff notice 2026-10"
reb coverage
reb report --lang en --out report.md
```

A complete synthetic walkthrough is in [examples/furniture-workshop](examples/furniture-workshop).

## Use it from your agent (MCP)

```json
{
  "mcpServers": {
    "reb": {
      "command": "reb",
      "args": ["mcp"],
      "env": { "REB_WORKSPACE": "/absolute/path/to/engagement" }
    }
  }
}
```

For Claude Code:

```bash
claude mcp add reb -e REB_WORKSPACE=/absolute/path/to/engagement -- reb mcp
```

Then install the agent skill in [skills/reverse-engineer-business](skills/reverse-engineer-business) and ask:

```text
Open a self-mode engagement for my workshop with the sop-replication profile,
ingest the files in ~/exports, map the order-to-delivery process from the
WhatsApp group, and tell me what is still unknown.
```

Tools: `list_profiles`, `open_engagement`, `ingest_source`, `read_source`,
`record_observation`, `record_evidence`, `record_claim`, `record_unknown`,
`update_unknown`, `search_evidence`, `analyze_event_log`, `analyze_invoices`,
`compare_stated_vs_enacted`, `inspect_coverage`, `record_obligation`,
`build_obligation_ledger`, `render_report`. See [docs/TOOLS.md](docs/TOOLS.md).

## Evidence grades

`grade = worst(authority base, custody cap, confidence cap)`:

| Authority | Base | | Custody | Cap |
|---|---|---|---|---|
| system record, direct observation | A | | captured live, issuer-verifiable | A |
| governing document, public record | B | | third party (independent channel) | A |
| testimony, public signal | D | | third party, public | B |
| analyst inference | E | | **held by the organization itself** | **C** |

A record handed over by the organization can be edited before handover, so it
caps at C until it is checked with its issuer (for example an e-invoice UUID
with the tax authority) or captured live. Two sources count as independent only
if they share no controller and no derivation ancestry. See
[docs/METHOD.md](docs/METHOD.md).

## Privacy

- **Local-first.** REB stores the ledger in `<workspace>/.reb/`, which is git-ignored automatically. It never copies original files.
- **Pseudonymized at ingest.** Person names in chats, e-mails, phone numbers, IBANs and national ids are replaced with stable tokens before text is stored. The mapping stays local and never appears in reports.
- If your agent sends this data to a hosted model, that is a cross-border transfer under KVKK, GDPR or PDPL. See [docs/LEGAL.md](docs/LEGAL.md).

## Status

v0.1: engine, core providers, six profiles, CLI, MCP server and agent skill.

Planned:
- OCEL 2.0 / pm4py export
- ERP SQL templates (Logo, Netsis, Mikro, Odoo, ERPNext)
- Nameplate parser and OEE
- Speaker diarization
- Organizational network analysis

See [docs/ROADMAP.md](docs/ROADMAP.md).

## Credits

The evidence, unknown and reconstruction-obligation model is adapted from
[REA](https://github.com/morluto/rea) (MIT). See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

MIT licensed.
