# AUDIT_SCOPE

> **Re-verified on `4fc917b`** (the user committed the 7 local edits plus more changes during the audit): all 11 counter-tests still fail as before, and 86/86 existing tests pass. The benchmark run C used the earlier `0a1a168` working tree.

**Question:** What can a user achieve with REB, and at what accuracy, reliability and effort, compared with the same model and tools without REB?

## In scope (done, short form at the user's request: "اختصر في التنفيذ")
- Phase 0: pin both local repos and the environment.
- Phase 1: trace the pipeline in code. Covers grading, independence, quote check, mode/consent guardrails, pseudonymization, coverage, obligations, and storage/locking.
- Phases 2–3: method review plus 11 counter-tests (`audit/tests/test_audit_adversarial.py`) and one red-team script.
- Phases 4–5: **one** synthetic nonprofit case with a hidden ground truth, run A (agent, no REB) vs run C (same agent, REB CLI), scored blind against a rubric declared before the runs.

## Out of scope / not done (explicit)
- Runs B (plain evidence template) and D (REA adapted) were not done. No ablation runs.
- Factory, profit-making service firm, government-service and public-only cases were not built. Only the nonprofit case ran.
- No repetition, so there is **no statistical claim**.
- OCR, audio, Arabic/Turkish extraction accuracy, PDF/XLSX malformed-file fuzzing, large-file limits and XML bombs were not exercised.
- No MCP transport test. The MCP and CLI call the same `application/*` functions (read, not executed through MCP).
- Prompt-injection behaviour of an agent driving REB was not tested.

## Agents
Separate sub-agents were used for run A, run C and the blind scorer. All three used the same base model family. The scorer was a smaller model working on anonymized files. The remaining "roles" (architect, evidence specialist, red team, and so on) were review **passes by the lead auditor**, not independent agents.

## Access constraints
- REB local = `origin/main` (`0a1a168`) plus 7 uncommitted files. The audit copied the working tree to a scratch folder and modified nothing of the user's.
- REA local = `morluto/rea` `main` @ `e2db768` (package v6.5.0). Only its docs were read; it was not run.
- No network services were used beyond `git fetch`.
