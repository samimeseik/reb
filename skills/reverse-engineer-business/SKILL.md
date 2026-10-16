---
name: reverse-engineer-business
description: Reverse engineer how any organization works — company, factory with its equipment, workshop, ministry, agency, NGO, club, school — and produce its blueprint (how it is built, what is known / inferred / unknown, how to rebuild it better) with REB's evidence ledger. Use when asked to understand, map, analyse, replicate, redesign or diligence an organization from whatever is available (a website, a name, social accounts, documents, exports, chats, invoices, interviews, site visits). Not for software internals (use REA).
metadata:
  version: "2"
---

# REB: Reverse Engineer any Business

REB knows how organizations are **built** (the design kernel: 10 building
blocks, design rules, families, archetypes, equipment). You use that knowledge in
reverse: every trace you find is evidence of some block, and every gap gets an
explicit hypothesis or unknown.

Your job is to research and propose. The engine grades, computes confidence and
refuses what the evidence does not support. Do not argue with a refusal. Get
better evidence.

Three layers that must never mix:

| Layer | Record | Meaning |
|---|---|---|
| **Known** | `record_claim` | backed by graded evidence |
| **Inferred** | `add_hypothesis` | confidence computed from signals; never rendered as fact |
| **Unknown** | `record_unknown` | open question plus the cheapest probe |

## 0. Mode, authorization, profile

Decide **whose organization this is**:

| Situation | Mode | Notes |
|---|---|---|
| It belongs to the user | `self` | `authorization="owner"` |
| The user has a written mandate from it | `engaged` | give the mandate reference |
| Neither | `public` | public sources only (`docs/LEGAL.md`) |

In public mode, never obtain internal information of a non-consenting organization, contact its staff for it, draft pretexts, log in, or bypass captchas.

For "how does X work / rebuild it", use profile **`blueprint`**. Other profiles:
`sop-replication`, `dd-evidence`, `factory-capacity`, `hiring-system`, `it-systems`, `desk-scan`.

## The deep-analysis playbook (follow every step, in order)

### Step 1: Collect traces ("whatever is available")

- **Website:** `start_blueprint(url=…)` crawls the same host (respecting robots.txt), stores pages as public-signal sources, records the technical footprint (CMS, pixels, chat, mail provider), and suggests archetypes.
- **Files the user sends:** `ingest_source` (PDF, DOCX, images/OCR, CSV/XLSX, WhatsApp exports, e-invoices, interview audio).
- **Wider public traces**, using your own web search. Ingest each page you rely on as `kind=public_signal` or `public_record`, `custody=public`, with its URL in `legal_basis`:

| Look for | It reveals |
|---|---|
| Trade / associations registry, official gazette | owners, capital, managers, founding law |
| Job ads and careers pages | roles, tools, shifts, growth, turnover |
| Annual reports, budget law, audit-court reports | money, structure, control |
| Procurement portals | suppliers, spend, what they buy |
| Maps (sites, size, hours) and reviews | footprint, pain points |
| Ad libraries and social accounts | acquisition channels |
| Factory videos, trade fairs, dealer case studies | equipment and nameplates |
| Certificates (ISO, CE, halal, food safety) | documented processes and scope |

- Use `show_kernel()` and `show_kernel(family=…)`. Every block lists **the traces it leaves** and how strong they are. Hunt for them component by component.

### Step 2: Choose the archetype

- Start from the suggestion, or from `list_archetypes`.
- `apply_archetype` seeds the full starting blueprint. Every element is a **LOW-confidence** hypothesis with a test.
- If nothing fits, apply the closest one and add modules. The family matters most (business / public_body / nonprofit / industrial).

### Step 3: Record facts from strong traces

- `read_source` → `record_evidence` with a **verbatim quote**. Quotes are checked.
- A **strong** trace IS the element: a published org chart, a registry entry, an ISO certificate, a budget line. Record it with `record_claim(component=…)` as a **fact**, not a hypothesis.
- Site navigation often lists every unit of an organization, and it repeats on every page. Treat it as one strong trace from one source, not as many sources.
- When a fact settles an archetype hypothesis, call `update_hypothesis(status="supported", status_evidence_ids=[…])`, then `promote_hypothesis`. If it contradicts the hypothesis, mark it `refuted`.

### Step 4: Generate hypotheses from moderate / weak traces

- `add_hypothesis(basis="signal", signal_evidence_ids=[…], component=…, test=…, impact=…, test_cost=…)`.
- Confidence is computed:
  - one source → medium;
  - two **independent** sources → high;
  - the organization's own pages all count as **one** source.
- Industrial plants: add machines with `add_equipment` (`station` = position in the routing; one rate unit per hour). The kernel equipment library gives function, typical rate, skill and maintenance.

### Step 5: Numbers

- Use `add_hypothesis(basis="calculation", derived_from=[…], assumptions=[…], range={low, high, unit}, metric=…)`.
- Use the metric names the checks know:
  - `revenue_per_year`, `units_per_year`, `price_per_unit`
  - `deals_per_year`, `avg_deal_value`, `commission_rate_pct`
  - `headcount`, `workload_hours_per_month`, `productive_hours_per_person_month`
  - `wip_units`, `throughput_per_day`, `lead_time_days`
  - `output_per_month`, `operating_hours_per_month`
- Run `check_consistency`. If the parts cannot all be true together, one of them is wrong; report it plainly.

### Step 6: Redesign

- `add_design_item(kind=copy | improve | cannot_copy | build_step, refs=[…])`. Every item must rest on a claim, hypothesis or evidence.
- **Copy:** what works and is codifiable.
- **Improve:** weaknesses you can beat. Use the failure points the archetype seeded and the contradictions you found.
- **Cannot copy:** licences, location, relationships, founder, timing.
- **Build recipe:** roles, systems, licences and first-90-day steps, each with a phase.

### Step 7: Verification plan and render

- `build_blueprint` ranks the cheapest high-impact tests.
- `render_blueprint(md_path, html_path, pdf_path)` writes the 7-section report:
  1. identity
  2. 12-component model with how each is built and the traces to look for
  3. process map
  4. organization
  5. numbers
  6. redesign
  7. verification plan
- If the owner can judge the hypotheses, `grade_hypothesis(verdict)` records calibration. It is never evidence.

## Rules the engine enforces (do not try to get around them)

- Authority is capped by source kind (a document is never a `system_record`). Custody caps the grade (handed over by the organization → max C).
- The organization's own staff, documents and systems share one controller. Interviews are testimony.
- Interviews, chat exports and observations of staff need a `legal_basis`. Public sources need their URL.
- No warranty words in your own text: verified, proven, guaranteed, certified, مضمون, موثّق, مثبت, kesinlikle. Quoting a source inside "…" is allowed.
- A contradicted unknown leaves that state only with evidence.
- A supported hypothesis needs evidence beyond its original signals.

## How to talk to the user

- **Lead with:**
  - what the organization is (identity);
  - how it makes and spends money;
  - the core process and its bottleneck;
  - the biggest contradictions;
  - the top three tests.
- **Always say which layer a statement is in:** نعرف / نستنتج / لا نعرف (known / inferred / unknown), with the grade or confidence.
- **Never upgrade confidence in prose** beyond what the ledger says.
- **If the request needs inadmissible access** (a competitor's internal files), say so and offer the public blueprint instead.
