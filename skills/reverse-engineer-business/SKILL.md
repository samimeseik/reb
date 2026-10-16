---
name: reverse-engineer-business
description: Reverse engineer how an organization actually works (processes, machines, hiring, suppliers, systems, unit economics, tacit knowledge) with REB's evidence ledger. Use when asked to map, document, replicate, diligence or understand a business, factory, workshop, agency or any organization from its documents, exports, chats, invoices, interviews or site visits. Not for software internals (use REA).
metadata:
  version: "1"
---

# REB: Reverse Engineer any Business

REB grades every finding by its evidence, records what is unknown, and closes a
reconstruction only on recorded evidence. Your job is to collect evidence and
propose claims. The engine grades them and refuses what the evidence does not
support. Do not argue with a refusal. Get better evidence.

## 0. Before anything: mode and authorization

Ask, or infer from the request, **whose organization this is**:

- **The user's own organization** → `mode=self`, `authorization="owner"`.
- **The organization gave a written mandate** → `mode=engaged`, with the mandate reference.
- **Neither** → `mode=public`. Public sources only. Never help obtain a non-consenting organization's internal information, contact its staff for it, or draft pretexts (fake customer, applicant or supplier approaches). Read `docs/LEGAL.md`.

Pick a profile with `list_profiles`:
- `sop-replication`: documenting your own business
- `dd-evidence`: before buying or partnering, with consent
- `factory-capacity`
- `hiring-system`
- `it-systems`
- `desk-scan`: public mode

## 1. Ingest

Call `ingest_source` for every file. Set the following carefully, because they decide the grades:

- **custody**
  - `subject_held`: the organization handed it over. Most files are this.
  - `captured_live`: you captured it yourself, or watched the owner pull it on their own device.
  - `issuer_verifiable`: **only** after the issuer check is done. Ingest the check first and cite it in `verification_ids`.
  - `third_party`: from a customer, supplier or bank. Give its `controller`. Add `independent_channel` only if you found the contact yourself.
  - `public`: put the URL or registry reference in `legal_basis`.
- **controller**: the organization's owner, staff, documents and systems all share **one** controller. The engine enforces this in self and engaged modes, so naming them differently does not make them independent.
- **legal_basis**: required for interviews, chat exports and observations of staff (a consent or staff-notice reference).
- **Authority is capped by source kind.** A document can never be a `system_record`. If the engine refuses, corroborate instead of relabelling.

## 2. Evidence with quotes

Use `read_source` to get pseudonymized text with line numbers. For each fact you
will rely on, call `record_evidence` with a **verbatim quote** and its location.
A quote that does not appear in the source is rejected. Never quote from memory.

Choose authority honestly:
- interviews → `testimony`
- SOPs and contracts → `governing_document`
- exports, ledgers, invoices, message timestamps → `system_record`
- what you saw → `direct_observation` (use `record_observation`). Attach the photo or
  count sheet with `artifact_ids` and date the session in `when` (YYYY-MM-DD). A note
  with no artifact is capped at grade B and triangulates only with a session on another day.

## 3. Analyse

- **Process:** `analyze_event_log`.
  - For a table, pass the case, activity and time columns.
  - For a WhatsApp group, pass an `activity_map` of keywords per step and a `case_pattern` regex such as `#(\d+)`.
  - Use the Mermaid graph, edge waits, variants and rework.
- **Revenue or spend concentration:** `analyze_invoices`.
- **Stated vs enacted:** record what people and documents say as `kind=stated` claims, and what records show as `kind=enacted` claims, with the same `metric` and a `value`. Then call `compare_stated_vs_enacted`. **Report contradictions plainly.** They are often the most important finding.

## 4. Claims

Call `record_claim` once per finding, citing evidence ids. Then:

- Tag `replicability`. Mark `non_transferable` for relationships, licences, location, timing and founder dependence.
- If a statement rests on general industry knowledge rather than this organization, set `industry_prior=true`.
- **Never fill a gap with a typical-industry story.** Record an unknown instead.
- Never use warranty words: verified, proven, guaranteed, certified, مضمون, موثّق, مثبت, kesinlikle. Let the grade speak.

## 5. Unknowns and coverage

`inspect_coverage` shows each layer and profile item as `met`,
`below_required`, `contradicted` or `not_covered`. For every gap, call
`record_unknown` with:
- the `required_authority`;
- the **cheapest probe** (for example "3 months of purchase e-invoices", "time 5 cycles at the edge-bander", "ask the shift lead what happens when X is absent").

Missing coverage is **unknown, not absent**.

## 6. Reconstruction obligations (sop-replication, hiring-system, it-systems)

`record_obligation` takes an owner (a role), evidence per required case, and a
verifier: `desk_review`, `reconciliation`, `conformance`, `prediction` or `pilot`.

- Give each case its own evidence; reusing one item for two cases needs `reuse_justification`.
- Record the check itself with `record_verification` (its source, what it compared, passed
  or failed). A `passed: true` flag alone never makes an obligation `ready`.
- The verification must come from a source **independent** of the case evidence.
- A desk review cannot close items grounded in records or observation.
- A contradicted or blocked unknown on the same layer keeps the obligation open.

`build_obligation_ledger` shows what is still open and why.

## 7. Report

`render_report` produces Arabic (RTL) or English. When you summarise for the user:
- lead with contradictions and the biggest unknowns;
- give grades next to findings;
- never upgrade confidence in your prose beyond what the ledger says.

## Communicating with the user

- Say which mode you are in, and why.
- Say which items are not covered and the next probe for each.
- If the user asks for something mode-inadmissible (for example a competitor's internal files), explain the limit and offer the public desk scan instead.
