# Contributing

```bash
uv venv && uv pip install -e ".[dev,mcp,excel,pdf]"
.venv/bin/pytest -q
REB=.venv/bin/reb examples/furniture-workshop/run.sh
```

## Rules of the codebase

- **Layering:** `domain/` (records, grading, guardrails, ledger) → `providers/` (one source kind each) → `application/` (workflows shared by CLI and MCP) → `cli.py` and `mcp_server.py`. Domain code imports nothing from the layers above it.
- **Providers own parsing.** Consumers read a provider's normalized facts and never re-parse the raw source.
- **Grades are computed.** Never add a parameter that lets a caller choose a grade or a claim status.
- **Missing coverage is unknown.** A new analysis must report its limitations and must never claim absence from partial data.
- **No warranty language** in code-generated text. `check_vocabulary` exists for this reason.
- **Privacy:** new providers must return person names in `Extraction.names` so they are pseudonymized before storage. Never write raw personal data under `.reb/` without scrubbing it first.
- **Tests:** every guardrail and grading rule needs a test proving it refuses what it should.
- **Profiles:** YAML in `src/reb/profiles/`. Give every item an Arabic question (`question_ar`) and evidence `hints`.

All example data must be synthetic.
