# BENCHMARK_RESULTS — n = 1 case, no statistical claim

Case: `cases/ngo` (synthetic nonprofit, 5 files). Ground truth: `cases/ngo_TRUTH_hidden.md`. The rubric (`RUBRIC.md`) was written before either run.
The same base model and the same instructions were used for both runs. Each run had its own copy of the files in its own folder. The scorer was a separate, smaller model that saw anonymized reports (X = C, Y = A).
Blinding is imperfect: X keeps the grade letters [C]/[D], which hints that it is the REB run.

| | A: agent, no REB | C: agent + REB CLI |
|---|---|---|
| Blind score /14 | **14** | **14** |
| Traps hit | 0 | 0 |
| Wrong citations (3 spot-checked) | 0 | 0 |
| Tool calls | 3 | 19 |
| Wall time | ~41 s | ~166 s |
| Sub-agent tokens | ~83k | ~118k |
| Persistent, re-checkable ledger | no | yes (5 sources, 14 evidence, 12 claims, 10 unknowns) |
| REB friction hit | — | invalid kind name; own-website independence (F-11, worked around by hand); no stated-vs-stated compare; company-only profile (`dd-evidence`) for an NGO; `people.key-person` shows "met" for a risk |

Insights unique to each run (from the blind scorer):
- **C only:** a ledger gap in Jul–Sep that is consistent with the stoppage (flagged as "not proof"); the ledger is likely incomplete; confirm the grant was actually received against the bank; a sampling plan.
- **A only:** reach may count repeat visits, not unique families; a critique of the survey method; donors and income are unknown; remedy options.

## Reading
- **Correctness:** no advantage was shown on this case. A strong agent with a careful prompt reaches the same result. The case was too easy (ceiling effect), so it cannot tell the runs apart.
- **Effort:** REB cost about 6× the tool calls, about 4× the wall time and about 1.4× the tokens.
- **What REB added that A cannot give:** a persistent, structured, re-openable record with IDs. Each unknown has its verification step attached. That helps a multi-session engagement or a second reviewer, but this benchmark did not measure that benefit.
- **What it would take to show value:** harder cases with many sources and several sessions (memory pressure), a laundering trap (derived copies), a staged observation, and a second analyst re-checking the work later. Also run B (a plain evidence-table template) to separate "structure" from "engine".

Not run: B (template), D (REA adapted), ablations, the other four case types, repetitions.
