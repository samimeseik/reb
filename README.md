<div align="center">

**English** · [العربية](README.ar.md)

# REB: Reverse Engineer any Business

### Evidence-graded reverse engineering of how an organization actually works — for AI agents (MCP) and the terminal.

**See a business you want to understand. Find out how it really runs — with the evidence, and with what is still unknown.**

</div>

---

REB is a sibling of [REA — Reverse Engineer Anything](https://github.com/morluto/rea),
which reverse-engineers software. REB applies the same discipline to
**companies, factories with their equipment, workshops, ministries, agencies,
NGOs, clubs, schools — any organization**: processes, machines, hiring,
suppliers, systems, unit economics and the know-how that lives only in people's heads.

Give it whatever is available — a website, a name, social accounts, documents,
exports — and it produces the organization's **blueprint**: how it is built,
what is **known**, what is **inferred** (with computed confidence) and what is
**unknown**, how to rebuild it better, and the cheapest tests that would turn
inferences into facts.

The hard part of analysing a business is not producing a convincing story.
Consultants and language models do that too easily. A plausible but invented
process map reads perfectly well, while invented code at least fails to run.
REB exists to stop that:

- **Every claim is tied to evidence** with a computed grade (A–E). You do not get to choose the grade.
- **Missing coverage is unknown, not absent.** Gaps become explicit Unknowns with the cheapest probe that would close them.
- **What people say is kept apart from what records show** (*stated vs enacted*). Gaps between the two are recorded as contradictions instead of being averaged away.
- **Quotes are checked.** Evidence that quotes a source must match the source text verbatim, and a fact that states numbers or claims its quote does not contain is graded down.
- **Copies are not corroboration.** A source that largely repeats another source's text counts as derived from it until you check otherwise.
- **Personal data is pseudonymized, not anonymized.** Names, phones, e-mails and ids are replaced by salted tokens before text is stored.
- **Reconstructions close only when the record is complete.** A rebuilt process or SOP item is `ready` only with an owner, distinct evidence for every required case, a verification run recorded as evidence from an independent source, and no blocking unknown on its layer. `ready` means the record is complete and checked; it does not certify that the process will work. These are REA's reconstruction obligation ledgers, applied to organizations.
- **Copying has limits.** Each finding can be tagged as codifiable, needs a capability, needs an asset, or non-transferable (relationships, licences, location, timing, founder).

## How it works: forward engineering, used in reverse

REB first knows how organizations are **built**, then reads their traces backwards.

| Layer | What it holds |
|---|---|
| **Design kernel** (`src/reb/kernel/`) | 10 building blocks every organization has — direction, demand, delivery, people, money, assets & equipment, information, control, support, improvement — each with its elements, design rules and the **traces it leaves** (strong / moderate / weak) |
| **Families** | how a business, a government body, a non-profit or international organization, and an industrial plant each build those blocks, and their specific traces (founding law, budget law, procurement awards, equipment nameplates…) |
| **Archetypes** (`src/reb/archetypes/`) | 17 composable modules on three axes (how value is created, how it is delivered, who pays) and 15 ready-made models: real-estate brokerage, consulting, marketing agency, recruitment, food factory, manufacturing workshop, retail/e-commerce, restaurant, clinic, charity, sports club, school, ministry, regulatory agency, international-organization office |
| **Equipment library** | 20 machine types with function, typical rate, inputs/outputs, operator skill and maintenance; plus an equipment register with routing and line capacity |

Applying an archetype seeds the full blueprint with **low-confidence hypotheses**.
Traces then raise, refute or promote them:

```
archetype pattern only        → low
one source (or one controller) → medium
two independent sources        → high
supported by stronger evidence → promoted to a graded claim
```

Consistency checks test that the parts fit together (revenue vs volume × price,
Little's law, headcount vs workload, stated output vs the slowest station's
capacity). The blueprint report has 7 sections — identity, the 12-component
operating model (with how each is built and the traces to look for), process
map, organization, numbers, redesign (copy / improve / cannot copy / build
recipe) and verification plan — as Markdown, an interactive HTML page (AR/EN)
and PDF.

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
| Site walks and time studies | `observation` | Direct-observation evidence (grade A only with a captured photo or count sheet; otherwise B) |

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

## Quick start: a blueprint

```bash
pip install "reb-agents[mcp,excel,pdf]"

mkdir acme && cd acme
reb init --name "Acme blueprint" --subject "Acme" --mode public --profile blueprint --language ar
reb blueprint start --url https://acme.example        # crawl + footprint + archetype suggestion + seed
reb archetypes                                        # or choose one: reb blueprint apply food-factory
reb hypothesis add --component team --basis signal --signal ev_… \
    --statement "Three shifts run the oven line." --test "Count cars at shift change" --impact high
reb consistency
reb blueprint render --md blueprint.md --html blueprint.html --pdf blueprint.pdf
```

## Quick start: documenting your own business

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
Build the blueprint of https://acme.example in public mode: how it works,
what we know, what we infer, what we don't know, and how to build a stronger one.
```

```text
Open a self-mode engagement for my workshop with the sop-replication profile,
ingest the files in ~/exports, map the order-to-delivery process from the
WhatsApp group, and tell me what is still unknown.
```

33 tools: evidence (`open_engagement`, `ingest_source`, `read_source`,
`record_observation`, `record_evidence`, `retract_evidence`, `declare_independent`, `record_claim`, `record_unknown`,
`update_unknown`, `search_evidence`), analyses (`analyze_event_log`,
`analyze_invoices`, `compare_stated_vs_enacted`, `check_consistency`),
blueprint (`show_kernel`, `list_archetypes`, `start_blueprint`,
`apply_archetype`, `add_hypothesis`, `update_hypothesis`, `promote_hypothesis`,
`grade_hypothesis`, `add_design_item`, `add_equipment`, `build_blueprint`,
`render_blueprint`) and reports (`list_profiles`, `inspect_coverage`,
`record_obligation`, `record_verification`, `build_obligation_ledger`, `render_report`).
See [docs/TOOLS.md](docs/TOOLS.md).

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

- **v0.2:** blueprint layer — design kernel, families, equipment library,
  archetypes, hypotheses with computed confidence, redesign, consistency
  checks, web provider, Markdown/HTML/PDF blueprint. Benchmarks in
  [docs/BENCHMARKS.md](docs/BENCHMARKS.md).
- **v0.1:** evidence engine, core providers, six profiles, CLI, MCP server, agent skill.

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
