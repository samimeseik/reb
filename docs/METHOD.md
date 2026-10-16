# Method

REB's method is REA's evidence discipline applied to organizations. This page
defines the records, the grading rules, independence, and when a
reconstruction counts as closed.

## Records

| Record | What it is | REA analogue |
|---|---|---|
| **Engagement** | Who is analysing which organization, in which mode, and under what authorization | investigation session |
| **Source** | One artifact: a file, a chat export, an invoice, an interview, an observation. It is identified by its sha256 and has custody, an origin party, a controller, derivation ancestry (`upstream_ids`), a legal basis, a sensitivity level and an observation context | artifact / subject |
| **Evidence** | One fact taken from a source, with a location, an optional verbatim quote, an authority and a confidence. The grade is computed | Evidence record |
| **Claim** | A statement about the organization, linked to supporting and contradicting evidence. Its status and grade are computed | derived finding |
| **Unknown** | An open question, revisioned, with the authority needed to settle it and the recommended probes | residual unknown |
| **Obligation** | One element of a reconstruction (a process, role, machine register, unit cost) with an owner, per-case evidence and a verifier | reconstruction obligation |

## Grades

```
grade = worst( authority_base , custody_cap , confidence_cap , observation_cap )
```

**Authority** is what kind of knowledge the evidence is:

| Authority | Base | Notes |
|---|---|---|
| `system_record` | A | ERP rows, ledgers, e-invoices, message timestamps. Strong on *what* happened, weak on *why* |
| `direct_observation` | A | The analyst saw it: site walk, time study, nameplate |
| `governing_document` | B | SOPs, contracts, manuals. They state intent, not practice |
| `public_record` | B | Registry, gazette, public court listings |
| `testimony` | D | What a person says. Interviews are always testimony |
| `public_signal` | D | Website, job ads, reviews |
| `analyst_inference` | E | Your reasoning |

**Custody** is who held the source when it reached you:

| Custody | Cap | Why |
|---|---|---|
| `captured_live` | A | You captured it, or watched the owner pull it on their own device |
| `issuer_verifiable` | A | Checked against the issuing body, e.g. an e-invoice UUID with the tax authority. Log the check as its own source |
| `third_party` + independent channel | A | From a customer, supplier or bank whose contact you found without the organization's help |
| `third_party` | B | Contact supplied by the organization |
| `public` | B | |
| `subject_held` | **C** | The organization handed it over and could have edited it first |

**Confidence**: `observed` and `derived` do not cap the grade. `inferred` caps it at D.

**Observation artifact**: an observation note with no attached artifact is capped
at **B**. An artifact is another ingested source the note references through
`artifact_ids` (stored as `verification_ids`) or `upstream_ids`: a photo, a count
sheet, a timestamped log. A typed note alone is one walk-through, possibly on a
staged day, and observed workers behave differently (Hawthorne effect).

### What the engine refuses, so grades cannot be talked up

- **Authority is capped by source kind.**
  - A document carries at most `governing_document`.
  - An interview carries only `testimony`, and a public signal only `public_signal`.
  - Exports, ledgers, e-invoices and chat timestamps can be `system_record`.
  - Only observations, and photos you took yourself, can be `direct_observation`.
- **`captured_live`** is accepted only for exports pulled live, chats, photos, observations and interviews. It is never accepted for a typed document.
- **`issuer_verifiable`** needs `verification_ids`. Ingest the issuer check itself first (for example a screenshot of the e-invoice UUID lookup), then cite it.
- **`public`** sources need their URL or registry reference in `legal_basis`.
- **The controller is forced** in `self` and `engaged` modes. Anything the organization handed over, and every interview with its people, gets the controller `subject:<organization>`.
- **Consent**: interviews, chat exports and non-public observations need a `legal_basis`. Every text-like file (`.txt`, `.csv`, `.tsv`, `.md`, `.log`, `.json`, no extension, …) is sniffed for chat content, so a chat renamed or re-saved under another extension is still a chat export: it needs a `legal_basis`, cannot be relabelled as another kind, and its senders are pseudonymized.

## Claim status

- `conjecture`: no supporting evidence. It is rendered only in a separate, clearly marked section.
- `single_source`: the evidence comes from one source, or from several sources under one controller.
- `triangulated`: the claim has evidence from at least two **independent** sources, and at least one of them is not testimony, a public signal or an inference. Several people saying the same thing is still testimony. An observation note without an artifact counts toward triangulation only when the claim also cites an observation session on a **different day** (the day comes from `when` = `YYYY-MM-DD…`, else the day it was recorded).
- `contradicted`: the claim has contradicting evidence attached.

### Independence

Two sources are independent only when **all three** conditions hold:

1. Their derivation ancestries do not intersect. A summary of an export is not independent of the export.
2. No source in either ancestry shares a `controller` with the other. **An organization's owner, staff, documents and systems share one controller.** Interviewing three employees gives you three testimonies from the same controller. It is not triangulation.
3. If both declare an observation period, the periods overlap.

## Stated vs enacted

Record what documents and people *say* as `kind=stated` claims, and what
records and observation *show* as `kind=enacted` claims, using the same
`metric` (for example `lead_time_days`). `compare_stated_vs_enacted` checks each
stated/enacted pair. A gap beyond the tolerance opens an Unknown with status
`contradicted`, and the related checklist item shows as contradicted.

These gaps are often the most valuable findings in an engagement.

## Coverage

Coverage is computed from the ledger across 11 layers: strategy, revenue,
customer, operations, equipment, systems, people, supply, finance, regulation
and culture. It is also computed per profile checklist item:

| Item state | Meaning |
|---|---|
| `met` | Best grade ≥ required grade |
| `below_required` | Covered, but the best grade is under the required grade |
| `contradicted` | A contradicted claim or a contradicted unknown exists on the item |
| `not_covered` | No evidence. This is **unknown, not absent** |

## Reconstruction obligations

A profile item marked `obligation: true` becomes an obligation. Its status is
`ready` only when every one of these holds:

1. It has an owner: the accountable role in the rebuilt or documented organization.
2. Each required case (`happy_path`, `exception_rework`, `peak_load`, `staff_absence`, `supplier_failure`) has at least one piece of evidence at or above the item's required grade. Each case needs its **own** evidence: one row cited for two cases keeps the item `open` unless a `reuse_justification` says why it covers both.
3. It has a passing verifier, strong enough for the evidence it checks. Verifiers from weakest to strongest: `desk_review` < `reconciliation` < `conformance` < `prediction` < `pilot`. A desk review cannot close an item whose case evidence includes system records or direct observation.
4. The verifier's result is **recorded as evidence**: `record_verification` (CLI `reb verify`) takes the check from an ingested source (reconciliation workbook, pilot log, site walk) and stores it with operation `verify:<item>` and its result. A `passed: true` flag alone does not close an obligation.
5. The recorded verification comes from a source **independent** of every case source. Re-citing the case evidence, or evidence from the same source, only checks the model against itself.
6. The item has no contradicted claims and no open unknowns, and its layer has no `contradicted` or `blocked` unknown, even one not tagged with the item.

`ready` means the record is complete on these rules. It does not mean the
reconstruction will work in practice; the verifier kind says how hard it was tested.

If the verifier failed (its flag or any recorded result), the status is `failed`. If no evidence exists, it is
`unknown`. Every other case is `open`, and the reasons are listed.

## Unknowns

Unknowns carry a revision; updates must name the current revision. Resolving needs evidence
of at least the `required_authority` (`verified`/`refuted`) or a written note (`out_of_scope`).
A **contradicted** unknown can only leave that state by being resolved with evidence — it
cannot be parked as "investigating" or declared out of scope. Resolved unknowns stay visible
in the report. Re-running `compare_stated_vs_enacted` reopens a resolved contradiction if the
gap is still there.

## Replicability

Each claim can carry one of these tags:

| Tag | Meaning |
|---|---|
| `codifiable` | Can be written down and taught |
| `needs_capability` | A skill or team has to be built |
| `needs_asset` | Needs a licence, a location, capital or equipment |
| `non_transferable` | Relationships, timing, the founder, history |

The report lists them so that a copied map is not over-trusted.

## What REB deliberately does not do

- It does not write findings for you. The agent proposes, and the engine grades and refuses.
- It gives no valuation and no opinion on financial statements.
- It does not treat interviews as facts. Testimony stays testimony until records or observation corroborate it.
