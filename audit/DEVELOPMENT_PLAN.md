# DEVELOPMENT_PLAN

Effort estimates assume one developer who knows the codebase. S ≈ ≤ 1 day, M ≈ 2–4 days, L ≈ 1–2 weeks.

## Path comparison
| Path | What it means | Verdict |
|---|---|---|
| 1. Harden the core | Fix F-04, F-11, F-06, F-02, F-08 | **Do first.** Cheap. Without it the grades and `ready` overstate confidence. |
| 2. Deepen the highest-value use | Multi-session diligence ledger: re-openable record, unknowns paired with probes, a second reviewer re-checking | **Do second, but measure first.** The value is plausible, not yet shown. |
| 3. Widen the organizational scope | More profiles (NGO, government service, factory) | **Hold.** No evidence yet that the core beats a template. Add an NGO/funder profile only (S), because run C needed it. |

## Changes
| # | Problem | Evidence | Benefit | Change | Type | Deps | Effort | Acceptance |
|---|---|---|---|---|---|---|---|---|
| 1 | Consent and pseudonymization bypassed by extension | F-04 | Closes a personal-data leak | Sniff chat content for every text-like file. Block a kind override that contradicts the sniff. | code | — | S | `test_renamed_chat_needs_consent` passes for .csv/.md/.log/.json. Senders absent from stored text. |
| 2 | Subject corroborates itself | F-11 | Triangulation means what it says | Normalize the controller for any source whose origin matches the subject or its declared aliases/domains, in every mode | code | engagement `aliases` field | S | `test_own_website_not_independent` passes |
| 3 | `ready` is self-declared | F-06 | `ready` becomes defensible | The verifier must cite evidence with `operation=verify:<obligation>` and a recorded result. Distinct evidence per case. A blocking-unknown flag on the layer blocks closure. Rename the state `record_complete`, or keep `ready` but change the README wording. | code + method + docs | — | M | `test_ready_despite_material_unknown` passes. README no longer says "proven". |
| 4 | Typed observation = A | F-02 | The grade reflects the actual capture | Cap an observation at B without an artifact (photo, count sheet). Triangulation through an observation needs an artifact or two sessions on different days. | method | — | S | `test_typed_observation_triangulates` passes |
| 5 | No retraction | F-08 | Errors can be corrected safely | `retract_evidence(id, reason)` re-evaluates everything downstream. The report lists retractions. | code | — | M | New test: retracting drops the claim status. The report shows the retraction. |
| 6 | Copy laundering | F-03 | Fewer false "independent" sources | Shingle/near-duplicate check between sources opens an "upstream?" unknown before independence is granted | code | — | M | `test_public_copy_laundering` passes |
| 7 | Fact may exceed its quote | F-01 | Less over-claiming | The report shows quote and fact side by side. Flag a fact that has numbers or entities not present in the quote. | code/UX | — | S–M | `test_quote_must_entail_fact` passes (via the flag or a cap) |
| 8 | Grade-blind contradiction | F-07 | Signals the weight of a conflict | Show the strongest grade on each side. Add a `disputed_weak` status. | method | — | S | `test_weak_contradiction_dominates` passes |
| 9 | Pseudonymization scope | F-09/F-10 | Honest privacy claim | Salt tokens per engagement. Optional key for the map. Require a `--names` list in self/engaged modes. README: "pseudonymized, not anonymized". | code + docs | — | S–M | Both tests pass. Docs updated. |
| 10 | Value unmeasured | BENCHMARK | Know whether the engine earns its 4–6× effort | Run 4–5 harder cases with B (a template) and repeats. Ablate grading, obligations and persistence. | eval | 1–4 | M | Pre-registered rubric. Report any difference with n stated. |

## Simplify / remove
- Keep the blueprint, archetypes, kernel and hypothesis layer (~1.3k LOC) out of the core claims until the evidence core is hardened and measured. They add surface without measured value.
- Drop "for any organization" from the README until profiles exist and have been tested beyond companies.
- Remove "proven" from the README (it violates REB's own vocabulary rule).
- Publish the valid `--kind` values in `--help` (run C friction).

## First five tasks
1. Fix F-04. Acceptance: the audit test passes and the existing 83 still pass.
2. Fix F-11. Acceptance: the audit test passes, and run C's workaround is no longer needed.
3. F-06: require a verifier artifact and distinct case evidence. Acceptance: the audit test passes and README wording is changed.
4. F-02: observation cap. Acceptance: the audit test passes.
5. Re-run this benchmark with 3 harder cases plus arm B. Acceptance: `BENCHMARK_RESULTS.md` updated with n ≥ 3 per arm and the rubric frozen beforehand.
