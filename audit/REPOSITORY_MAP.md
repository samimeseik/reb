# REPOSITORY_MAP

> **Re-verified on `4fc917b`** (the user committed the 7 local edits plus more changes during the audit): all 11 counter-tests still fail as before, and 86/86 existing tests pass. The benchmark run C used the earlier `0a1a168` working tree.

| Repo | Path | Remote | Branch / SHA | Local state |
|---|---|---|---|---|
| REB | `~/Desktop/reb` | github.com/samimeseik/reb | `docs-and-benchmarks` @ `0a1a168` (= origin/main) | 7 modified files (README×2, METHOD, TOOLS, SKILL, providers/web.py, tests/test_blueprint.py) — untouched by audit |
| REA | `~/Desktop/rea` | github.com/morluto/rea | `main` @ `e2db768`, package v6.5.0 | clean (not run; docs read) |
| runs | `~/Desktop/reb-runs` | none | — | earlier benchmark outputs (tema, ticaret, tatgida, kahvedunyasi, idexrealestate); not re-scored |

REB = Python ≥3.11, deps pydantic + pyyaml; extras mcp/excel/pdf/ocr/audio/process. ~6.3k LOC src, 83 tests (all pass on 3.13.12). CI: 3.11–3.13, pytest + example script. License MIT; THIRD_PARTY_NOTICES credits REA concepts, states no REA code copied (spot check: REB is Python, REA is TypeScript — consistent).

```
src/reb/
  domain/   models.py (pydantic), grading.py (A–E, independence, triangulation),
            guardrails.py (modes, consent, vocabulary, pseudonymizer), ledger.py (JSON store, flock, atomic save)
  application/ ingest, analysis (event log / invoices), consistency (stated vs enacted),
            coverage (profiles, obligations, ready), report, blueprint(+render)
  providers/ documents, spreadsheet, whatsapp, efatura (XML), audio, web (crawler)
  profiles/*.yaml (7)  archetypes/  kernel/
  cli.py, mcp_server.py  -> both call application/* (same validation path)
```

Pipeline and who decides what:
| Step | Code does | Agent/human decides | Error propagation |
|---|---|---|---|
| Ingest | hash, kind sniff (.txt only), admissibility, extract, pseudonymize known names | kind, custody, controller, upstream, legal_basis | wrong custody/controller → wrong grade & independence everywhere downstream |
| Evidence | authority ceiling per kind, quote substring check, grade = worst(authority, confidence, custody) | fact text, authority, confidence | fact may exceed quote (F-01) |
| Claim | status from evidence: contradicted / conjecture / single / triangulated | which evidence supports/contradicts | any contradiction dominates (F-07) |
| Coverage | per profile item: met / below / contradicted / not_covered | item tagging | untagged unknowns invisible to items |
| Obligation | ready iff owner, all cases, grade, verifier passed & independent, no item-tagged open unknowns | `verifier.passed` boolean | self-declared closure (F-06) |
| Report | renders grades, statuses, unknowns; vocabulary filter | — | — |
