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
grade = worst( authority_base , custody_cap , confidence_cap )
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

**Artifact**: an observation is a note the analyst typed. Without an artifact captured on the
spot (a photo, a count sheet, a timed log: a `captured_live` source passed as `artifact_ids`)
it is capped at **B**, because a single walk-through can be staged, misread or recalled wrongly.

### What the engine refuses, so grades cannot be talked up

- **Authority is capped by source kind.**
  - A document carries at most `governing_document`.
  - An interview carries only `testimony`, and a public signal only `public_signal`.
  - Exports, ledgers, e-invoices and chat timestamps can be `system_record`.
  - Only observations, and photos you took yourself, can be `direct_observation`.
- **`captured_live`** is accepted only for exports pulled live, chats, photos, observations and interviews. It is never accepted for a typed document.
- **`issuer_verifiable`** needs `verification_ids`. Ingest the issuer check itself first (for example a screenshot of the e-invoice UUID lookup), then cite it.
- **`public`** sources need their URL (`https://…`) or a registry reference with its number (`MERSIS 0123456789`) in `legal_basis`. Placeholders such as `n/a` are refused.
- **A declared kind must fit the file.** It may refine the detected kind within its family (a `.md` page as `public_signal`, a `.csv` as `event_log`). Crossing families (a spreadsheet declared a `document`) needs a `kind_reason`, which is kept on the source.
- **The controller is forced.** Anything the organization handed over, every interview with its people, and anything published by the subject, its declared `aliases` or its domains, gets the controller `subject:<organization>`, in every mode.
- **A fact cannot outrun its quote.** A quote proves the words are in the source, not that they support the fact. Numbers in the fact that the quote lacks cap the evidence at D. A fact that shares no word, number or code with a quote in the same script is capped at C. Record the inference separately (`confidence=inferred`) or as a claim. The report shows each quote next to its fact.
- **Consent**: interviews, chat exports and non-public observations need a `legal_basis`. A renamed chat export is still detected from its content.

## Claim status

- `conjecture`: no supporting evidence. It is rendered only in a separate, clearly marked section.
- `single_source`: the evidence comes from one source, or from several sources under one controller.
- `triangulated`: the claim has evidence from at least two **independent** sources, and at least one of them is not testimony, a public signal or an inference. Several people saying the same thing is still testimony.
- `contradicted`: the claim has contradicting evidence of grade C or better, or its own support is weaker than B.
- `disputed_weak`: support of grade A or B against only weak contradiction (D or E). It still has to be resolved, but it is not shown as two strong records disagreeing. The report shows the strongest grade on each side.

### Independence

Two sources are independent only when **all three** conditions hold:

1. Their derivation ancestries do not intersect. A summary of an export is not independent of the export.
2. No source in either ancestry shares a `controller` with the other. **An organization's owner, staff, documents and systems share one controller.** Interviewing three employees gives you three testimonies from the same controller. It is not triangulation.
3. If both declare an observation period, the periods overlap.

**Copies.** When most of one source's text (3-word shingles, 60% of the shorter text) appears in
a source under a different controller, the new source is flagged as possibly derived from the
older one and an unknown is opened. Until the analyst records the real `upstream_ids` or runs
`declare_independent` with a reason, the two are not independent. A news article that reprints
a press release is one source, not two.

An observation without an artifact corroborates another source only when the claim also has
artifact-less observations from **at least two different days** (`as_of`). One staged day is
not enough.

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
| `met` | The question is answered with evidence at or above the required grade. It says nothing about whether the answer is good: a key-person risk can be `met` |
| `below_required` | Covered, but the best grade is under the required grade |
| `contradicted` | A contradicted claim or a contradicted unknown exists on the item |
| `disputed` | A claim on the item is disputed by weak evidence only |
| `not_covered` | No evidence. This is **unknown, not absent** |

## Reconstruction obligations

A profile item marked `obligation: true` becomes an obligation. Its status is
`ready` only when every one of these holds:

1. It has an owner: the accountable role in the rebuilt or documented organization.
2. Each required case (`happy_path`, `exception_rework`, `peak_load`, `staff_absence`, `supplier_failure`) has at least one piece of evidence at or above the item's required grade. One piece of evidence cannot stand for two different cases.
3. It has a passing verifier, strong enough for the evidence it checks. Verifiers from weakest to strongest: `desk_review` < `reconciliation` < `conformance` < `prediction` < `pilot`. A desk review cannot close an item whose case evidence includes system records or direct observation.
4. The verifier's run is **recorded as evidence** (`record_verification` / `reb verify`: operation `verify:<item>` with result `pass` or `fail`) on a source **independent** of every case source. A `passed: true` flag on its own does not count. Re-citing the case evidence, or evidence from the same source, only checks the model against itself.
5. The item has no contradicted claims and no open unknowns, and its layer has no open unknown that is contradicted or marked `blocking`.

`ready` means the record is complete and checked. It does not certify that the rebuilt process will work.
If a recorded verification failed, the status is `failed`. If no evidence exists, it is
`unknown`. Every other case is `open`, and the reasons are listed.

## Retraction

Evidence found wrong (a bad extraction, a forged or superseded document) is retracted with a
reason (`retract_evidence` / `reb retract`), one item or a whole source at a time. It stays in
the ledger and in the report, marked, but every computation ignores it: claims, hypotheses and
obligations are re-evaluated, a resolved unknown that rested only on it is reopened, and it can
no longer be cited.

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

## The blueprint layer: forward engineering used in reverse

### Design kernel
`src/reb/kernel/blocks.yaml` defines the 10 blocks every working organization has:

| Block | Feeds components |
|---|---|
| direction & governance | identity, moat |
| demand | customers, acquisition, offer |
| value delivery | operations |
| people & structure | team |
| money | revenue_model, economics |
| assets, equipment & tools | assets |
| information & systems | systems |
| control | identity, operations |
| support functions | partners, team |
| learning & improvement | moat |

Each block has **elements** (what must exist in some form), **design rules**
(for example: throughput equals the slowest stage; a manager directly supervises about
5–15 people; in public bodies, budget lines mirror the organization chart) and
**traces**, each with a strength:

- `strong`: the trace is the element itself or an official record of it. Record it as a **claim**.
- `moderate`: the trace exists mainly because the element exists. Record it as a **hypothesis signal**.
- `weak`: compatible with the element, but with other explanations. Record it as a hypothesis signal, and look for a second source.

`families.yaml` says how a `business`, a `public_body`, a `nonprofit` and an
`industrial` plant build each block, and lists the traces specific to each
family. `equipment.yaml` holds the machine library: function, typical rate,
inputs and outputs, skill and maintenance.

### Archetypes
`src/reb/archetypes/` composes **modules** on three axes:
- value: manufacturing, trading, professional service, brokerage, platform, membership, non-profit, hospitality/retail
- delivery: fixed site, field, remote/digital, project
- payer: consumer, business, government, donors, third party

A family plus modules plus specifics (process stages, roles, equipment, build
steps) makes an archetype. Applying one seeds every component with
`basis=archetype` hypotheses (confidence **low**), each with its cheapest test.
It also seeds design items: failure points become `improve` items, and build
steps become `build_step` items. Each design item references the hypothesis it
came from.

### Hypotheses
A hypothesis is never rendered as a fact. Its confidence is **computed**:

| Support | Confidence |
|---|---|
| archetype pattern only, or only analyst inferences | low |
| signals from one source, or several under one controller | medium |
| signals from two or more independent sources | high |
| calculation | the weakest of its inputs |

Rules for changing its status:
- `supported` needs evidence beyond the original signals: a record, an observation, a document or a public record, or a source independent of every signal source.
- `refuted` needs evidence.
- `promote_hypothesis` turns a supported hypothesis into an ordinary graded claim.
- Owner verdicts (`grade_hypothesis`) feed **calibration** only. They are never evidence.

### Consistency checks
`check_consistency` reads metric values from claims first, then from hypotheses
(the midpoint of their range). It checks:
- revenue ≈ units × price;
- commission revenue ≈ deals × average deal value × rate;
- lead time ≈ work-in-progress ÷ throughput;
- headcount ≈ workload ÷ productive hours;
- stated output ≤ line capacity. Line capacity is the slowest station in the equipment routing × operating hours, and the 352 hours/month default is shown as an assumption.

A conflict opens an unknown that names both sides.

### Blueprint
`build_blueprint` assembles, for each of the 12 components:
- how it is built (kernel elements, rules, family notes);
- the traces to look for;
- what is known, inferred, refuted and unknown;
- a completeness score.

It adds the process map (mined from records if any exist, otherwise the archetype stages), the
organization, the numbers, the consistency results, the redesign, the
**verification plan** (proposed hypotheses ranked by impact × uncertainty ÷ test cost)
and the calibration.

## What REB deliberately does not do

- It does not write findings for you. The agent proposes, and the engine grades and refuses.
- It gives no valuation and no opinion on financial statements.
- It does not treat interviews as facts. Testimony stays testimony until records or observation corroborate it.
