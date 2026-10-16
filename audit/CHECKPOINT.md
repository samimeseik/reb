# CHECKPOINT: 2026-10-16

> **Re-verified on `4fc917b`** (the user committed the 7 local edits plus more changes during the audit): all 11 counter-tests still fail as before, and 86/86 existing tests pass. The benchmark run C used the earlier `0a1a168` working tree.

Versions used: REB working tree @ `0a1a168` plus 7 uncommitted files (copied to a scratch folder); REA @ `e2db768`; Python 3.13.12, macOS. See `logs/env*.txt`.

| Phase | Status |
|---|---|
| 0 Pin reality | done |
| 1 What was built | done (code trace; MCP read, not run over transport) |
| 2 Method validity | done via counter-tests F-01…F-11 |
| 3 Technical/adversarial | partial: no OCR/audio/fuzzing/large files/SSRF |
| 4 Organizational cases | partial: only the NGO case |
| 5 Added value | partial: A vs C, n = 1; no B, D or ablation |
| 6 Verdict and plan | done (conditional) |

Results: 83/83 (0a1a168 tree) and 86/86 (4fc917b) existing tests pass. 11/11 audit counter-tests fail, which is expected: each failure is a reproduced finding. A vs C: 14/14 tie; C costs about 6× tool calls.

Blockers: none technical. Expanding the benchmark needs more agent runs (cost/time).

Next step, to reproduce the findings:
```bash
cp audit/tests/test_audit_adversarial.py tests/ && python -m pytest -q tests/test_audit_adversarial.py; rm tests/test_audit_adversarial.py
```
Next work item: DEVELOPMENT_PLAN task 1 (F-04), then re-run the command above. The matching test should pass.
