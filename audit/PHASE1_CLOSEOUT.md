# PHASE 1 CLOSEOUT: 2026-10-16

Phase 1 ("harden the core") is closed. The audit files in this folder are kept
as the record of what was found on `0a1a168` / `4fc917b`. This file says what
has been done about each item since.

## Findings: all 11 fixed
All 11 counter-tests in `tests/test_audit_adversarial.py` pass on `main`
(they failed 11/11 at audit time). Project tests: 107 pass.

| ID | Sev | Fix | Where |
|---|---|---|---|
| F-04 | High | Chat content sniffed for every text-like file, whatever its extension | samimeseik/reb#5 |
| F-11 | High | Sources from the subject, its `aliases` or domains share `subject:<name>` in every mode | samimeseik/reb#5 |
| F-06 | High | Verifier must be a recorded run (`reb verify`); distinct case evidence; `blocking` layer unknowns; README wording | samimeseik/reb#5 |
| F-02 | High | Observation without a captured artifact capped at B; corroborates only with another day | samimeseik/reb#5 |
| F-08 | Medium | `reb retract` / `retract_evidence` re-evaluates everything downstream; report lists it | samimeseik/reb#5 |
| F-01 | Medium | Fact with numbers not in its quote capped at D; no shared word/number/code capped at C; quote shown beside fact | samimeseik/reb#5 |
| F-03 | Medium | Near-duplicate text flags a possible upstream and opens an unknown; `reb independent` clears it | samimeseik/reb#5 |
| F-05 | Medium | Public custody needs a URL or a numbered registry reference; cross-family kind override needs `kind_reason` | samimeseik/reb#5 |
| F-07 | Medium | A/B support vs only D/E contradiction is `disputed_weak` | samimeseik/reb#5 |
| F-09 | Medium | Person names detected in all text, plus an explicit `--name` list | samimeseik/reb#5 |
| F-10 | Low | Salted tokens; only names persisted; `REB_PSEUDONYM_DIR`; "pseudonymized, not anonymized" | samimeseik/reb#5 |

## Suspicions
| ID | Status |
|---|---|
| S-01 SSRF via the crawler | **Fixed.** URLs and redirect targets that resolve to loopback, private, link-local or reserved addresses are refused (`REB_ALLOW_PRIVATE_HOSTS=1` to opt in). Tested on 127.0.0.1, localhost, 169.254.169.254, 10.x, ::1 |
| S-02 Prompt injection through ingested text | **Not tested.** The engine is passive; the risk sits in the agent driving it. Carried to the next phase |

## "Simplify / remove" items
| Item | Status |
|---|---|
| Drop "for any organization" from the README | Done. README says profiles are built and tested for companies, factories and workshops, with a first non-profit profile |
| Remove "proven" from the README | Done (with F-06) |
| Publish valid `--kind` values in `--help` | Done (CLI `ingest --help` and the MCP `ingest_source` description) |
| Keep the blueprint layer out of the core claims until measured | Done in wording: README "Status" marks it exploratory and outside the measurement. No code removed |

## Run C friction
| Friction | Status |
|---|---|
| Invalid kind name | Done (`--kind` choices) |
| Own website counted as independent | Done (F-11) |
| No NGO profile | Done: `ngo-funder` profile (12 items). Not yet exercised on a case |
| `people.key-person` shows "met" for a risk | Done: `met` is now labelled "answered at the required grade (not a judgement)" in the report and METHOD |
| No stated-vs-stated compare | **Open.** Carried to the next phase |

## Not done: carried to the next phase
1. **Measure value** (plan item 10 / first-five task 5): at least 3 harder cases (many sources, several sessions, a laundering trap, a staged observation), arms A (agent), B (plain evidence-table template), C (agent + REB), with repeats and a rubric frozen beforehand. Until then, REB's advantage over a careful agent is unmeasured.
2. Stated-vs-stated comparison.
3. S-02 prompt-injection test.
4. Untested in the audit and still untested: OCR, audio, Arabic/Turkish extraction accuracy, malformed-file fuzzing, large files, MCP over a real transport.
5. Profiles for government services, factories as a public-sector supplier, clubs and schools (path 3 in the plan: hold until the core is measured).
