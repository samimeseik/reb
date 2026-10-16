# CLAIMS_VS_IMPLEMENTATION

Legend for the verdict column: **Proven** = exists and holds under counter-tests · **Partial** = exists but can be bypassed or is narrower than stated · **Formal** = present in form, weak in substance · **Not run** = not exercised by this audit.

| Stated capability | Where | Existing test | Audit test | Limits | Verdict |
|---|---|---|---|---|---|
| A–E grades computed, not asserted | grading.compute_grade | yes | F-01, F-02 | The grade measures source and custody, not whether the inference is valid. Typed observations score A. | Partial |
| Triangulation needs independent sources | grading.independent | yes | F-03, F-11 | Rests on declared controller and upstream. The subject's own website counts as independent. | **Partial (High gap)** |
| Testimony × N ≠ triangulation | evaluate_claim WEAK_AUTHORITIES | yes | — | Holds, but weak + document still triangulates. | Proven (narrow) |
| Quotes are checked | add_evidence substring | yes | F-01 | Checks that the quote is present, not that it supports the fact. | Partial |
| Modes self/engaged/public enforced | check_source_admissible | yes | F-05 | Trusts the kind and custody the analyst declares. Any string passes as legal_basis. | Partial |
| Consent required for chats/interviews | CONSENT_REQUIRED_KINDS + detect_kind | yes | F-04 | Renaming the file to .csv/.md/.log bypasses it. | **Partial (High gap)** |
| Pseudonymization before storage | Pseudonymizer | yes | F-09, F-10 | Covers chat senders and regex patterns only. The map is in clear text and tokens are unsalted. | Partial |
| Vocabulary guardrail | check_vocabulary | yes | — | Works. Its own README uses "proven". | Proven |
| Stated vs enacted | consistency.py | yes | (run C) | Only compares a stated value with an enacted one. It cannot compare two stated figures. | Proven (narrow) |
| Unknowns registry, resolution needs evidence of the required authority | ledger.update_unknown | yes | read | Works as designed. | Proven |
| Obligation ledger, `ready` only when proven | coverage.evaluate_obligation | yes | F-06 | The verifier result is a self-declared boolean. Cases can reuse the same evidence. Layer unknowns are ignored. | **Formal** |
| Concurrent-safe ledger | Ledger.open flock + atomic replace | yes | read | POSIX only. Every MCP and CLI write path goes through it. | Proven (read + tests) |
| Change detection of originals | read_original sha256 | yes | read | — | Proven |
| Evidence retraction/correction | — | — | F-08 | Absent. | Not implemented |
| Temporal / branch variation | ObservationContext period overlap | partial | read | Only the period field exists. Variation is treated as contradiction. | Formal |
| Profiles for any organization type | profiles/*.yaml (7) | yes | run C | Company-centric. No nonprofit, funder or government-service profile. Archetypes list a charity and a ministry, but no matching profile exists. | Partial |
| OCR / audio / Arabic-Turkish extraction | providers | partly | — | — | Not run |
| Web desk scan | providers/web.py | yes | R-01, S-01 | file:// is blocked. Private-IP SSRF was not tested. | Not run (partial) |

## REB vs REA (concepts)
Adapted from REA: the evidence record, the unknown registry with revisions, the rule that missing coverage means unknown and not absence, and the obligation ledger.
What changed in the move from software to organizations:
- REA's verifier is an **executed** check whose result must exist in the evidence bundle. REB's verifier is a **typed boolean**. This is the main loss of rigour (F-06).
- REA residual unknowns block closure globally. REB only blocks on unknowns tagged with the item.
- REA observations come from instrumented runs that can be replayed. REB observations are human notes, but they keep top-grade authority (F-02).
- Organizations vary over time and across branches. Software builds are deterministic. REB has no first-class notion of variation (F-07).

Licensing: MIT → MIT, credited in THIRD_PARTY_NOTICES. The languages differ (TypeScript vs Python), and no copied code was observed. Not a legal opinion.
