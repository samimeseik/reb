# RED_TEAM_LOG

> **Update 2026-10-16:** Phase 1 is closed. All 11 findings are fixed and their counter-tests pass; S-01 (SSRF) is fixed; value is still unmeasured. This file is the record at audit time. Current status: [`PHASE1_CLOSEOUT.md`](PHASE1_CLOSEOUT.md).

Each round: conclusion, then evidence, then a counter-attack, then a re-test by a different method, then the corrected conclusion.
Note: these are review passes by the same auditor, not an independent red team.

## Round 1: implementation correctness
1. **"Consent cannot be bypassed."** Counter: rename the chat file. Re-test: script over four extensions (`logs/redteam_consent.txt`). `.txt` is blocked; `.csv`, `.md` and `.log` are admitted with names stored in clear. Result: **conclusion reversed** (F-04).
2. **"The crawler can read local files."** (a suspicion) Re-test: `crawl('file:///etc/hosts')` returns 0 pages because `_normalize` prefixes https. Result: **refuted** (R-01).
3. **"Writes are concurrency-safe."** Counter: an MCP and a CLI writing at the same moment. Re-test by reading every write path: all use `Ledger.open` (flock) and atomic replace. Result: holds on POSIX; not stress-tested.

## Round 2: method under misleading or incomplete input
4. **"Triangulation means independent corroboration."** Counter 1: a news article copying the press release → triangulated (F-03). Counter 2: in engaged mode, the organization's own website plus its report → triangulated (F-11). Re-test by a different method: run C's agent hit F-11 independently, without being told. Result: **narrowed** to "independence as declared by the analyst".
5. **"`ready` means reproducible."** Counter: one log row cited for two cases, a typed `passed: true` and an open layer unknown. Re-test: compared with REA's docs (the verifier result must be in the evidence bundle). Result: **narrowed** to "the record is complete as declared".
6. **"A gives a strong warranty."** Counter: an analyst note with no artifact gets A (F-02). Result: A means the source class is strong, not that this observation is.
7. Counter-check in REB's favour: weak contradiction dominates (F-07). Is that a bug or caution? Result: kept at Medium. It is safe-side behaviour but grade-blind.

## Round 3: practical value vs alternatives
8. **"REB improves correctness."** Test: blind A vs C on the NGO case. Result: tie at 14/14. Counter-attack on the test itself: the case is too easy (ceiling) and n = 1. Result: **neither proven nor disproven.** Effort cost is measured: about 6× tool calls and about 4× time.
9. **"REB adds nothing."** Counter: run C found ledger-forensics points that A did not (the Jul–Sep gap, confirming receipt of the grant) and produced a re-openable ledger. Result: some added value in structure and persistence is plausible but **unmeasured**.

## Round 4: residual-risk round (privacy)
10. **"Pseudonymized = anonymous."** Tokens are `sha256("PERSON:"+name)[:6]` with no salt, so a known name can be re-derived without the map. The map is in clear text. Result: pseudonymization only (F-09, F-10).

Stop condition: rounds 3 and 4 produced no new High finding beyond F-11 (which came from round 3's benchmark). Critical risks still open: F-04, F-06 and F-11 are untreated, so the verdict is conditional.
