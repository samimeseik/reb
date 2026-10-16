# FINDINGS — REB audit (2026-10-16)

> **Re-verified on `4fc917b`** (the user committed the 7 local edits plus more changes during the audit): all 11 counter-tests still fail as before, and 86/86 existing tests pass. The benchmark run C used the earlier `0a1a168` working tree.

Version audited: working tree of `docs-and-benchmarks` @ `0a1a168` plus 7 uncommitted files (copied, not modified).
Reproduce: `pytest -q audit/tests/test_audit_adversarial.py` (copy into `tests/` or run with `--rootdir`). Each failing test = one reproduced finding.

Severity: **High** = can make a user act on a wrong conclusion with REB's backing, or leaks personal data; **Medium** = misleading under realistic misuse; **Low** = limited impact / hygiene.
Type: CODE (bug) · METHOD (design weakness) · DATA (needs external data) · USE (user error that REB should catch).

| ID | Sev | Type | Title | Status |
|---|---|---|---|---|
| F-04 | High | CODE | Renamed WhatsApp export skips the consent check **and** pseudonymization | **Fixed**: content sniffing for every text-like file |
| F-11 | High | CODE | In `engaged`/`self` mode the subject's own public website/press is a separate controller → "independent" of its internal records | **Fixed**: subject name, aliases and domains map to `subject:<name>` in every mode |
| F-06 | High | METHOD+CODE | `ready` reachable with a self-declared verifier, reused case evidence and an open material unknown | **Fixed**: recorded verification run, distinct case evidence, blocking layer unknowns, README wording |
| F-02 | High | METHOD | Analyst-typed observation note = grade A and an independent source → triangulates alone | **Fixed**: artifact-less observation capped at B; corroborates only with a second day |
| F-01 | Medium | METHOD | Quote check proves presence, not entailment; grade belongs to the source, not the inference | Reproduced |
| F-03 | Medium | METHOD | Derived copy (news reprinting a press release) counts as independent corroboration unless the analyst declares `upstream_ids` | Reproduced |
| F-05 | Medium | USE | Public mode admits any file relabelled `kind=document custody=public` with any text in `legal_basis` | Reproduced |
| F-07 | Medium | METHOD | One E-grade contradicting item flips a triangulated A claim to `contradicted` (grade-blind) | Reproduced |
| F-08 | Medium | CODE | No retraction/supersession of evidence; claims keep citing evidence later found wrong | Reproduced (API absent) |
| F-09 | Medium | CODE | Names in plain documents are not pseudonymized (only chat senders + regex identifiers) | Reproduced |
| F-10 | Low | DESIGN | `pseudonyms.json` (re-identification table) stored in clear next to ledger | Reproduced; documented as local-only |
| S-01 | — | suspicion | Crawler accepts http(s) to private/link-local IPs (SSRF via MCP `start_blueprint`) | Not tested |
| S-02 | — | suspicion | Prompt injection in ingested text steering the agent to record evidence | Engine is passive; agent-level, not tested |
| R-01 | — | refuted | `file://` URLs in crawler | `_normalize` forces https — no local file read |

---

### F-04 — Consent and pseudonymization bypassed by file extension (High, CODE)
- Where: `src/reb/providers/__init__.py: detect_kind` — chat detection runs only for `.txt` or no suffix; `guardrails.CONSENT_REQUIRED_KINDS`; `ingest.py` gets names only from the chat extractor.
- Repro: same WhatsApp text saved as `.txt` → `consent_required`; as `.csv` → admitted as `spreadsheet`; `.md` → `document`; `.log` → `other`. In all three, sender names are stored **in clear** in `.reb/text/*.txt` (`audit/logs/redteam_consent.txt`).
- Expected: content sniffing for every text-like file; chat content needs `legal_basis` and gets sender pseudonymization.
- Impact: the two guardrails the README presents as engine-enforced (consent, pseudonymization) can be skipped by accident (Excel "Save as CSV" of a chat) — personal data of third parties is stored unprotected.
- Acceptance: test `test_renamed_chat_needs_consent` passes for `.csv/.md/.log/.json`; sender names absent from stored text.

### F-11 — The organization corroborates itself (High, CODE)
- Where: `guardrails.normalize_controller` only rewrites `subject_held` and interviews to `subject:<name>`; `public` custody keeps `controller = origin_party`.
- Repro: `test_own_website_not_independent` — website (`public_signal`, origin "Hope Bridge") + director's report (`subject_held`) → `triangulated`. The benchmark agent (run C) found the same issue on its own and worked around it by hand.
- Impact: the most common mixed engagement (public site + handed-over docs) can upgrade the subject's own marketing to "independent corroboration".
- Acceptance: any source whose origin_party/controller matches the engagement subject (case-folded, plus declared aliases/domains) is normalized to `subject:<name>` in every mode.

### F-06 — `ready` is a record-completeness state, not a validity state (High)
- Where: `application/coverage.py: evaluate_obligation`, `_verifier_independent`; `models.Verifier.passed`.
- Repro: `test_ready_despite_material_unknown` — one event-log row cited for both `happy_path` and `peak_load`; verifier `{"kind":"reconciliation","passed":true}` typed by the analyst citing one third-party row; an open unknown on the same layer (not tagged with the item id) → status `READY`, reasons `[]`.
- Gaps: (a) `passed` is a boolean the agent writes — nothing executes or records the check (REA requires the verifier result to be present in the evidence bundle); (b) the same evidence may satisfy different cases; (c) only unknowns tagged with `item` block; (d) README says "close only when **proven**" — a word REB's own vocabulary filter bans.
- Impact: a user reads `ready` as "this SOP/process can be reproduced". It means "the slots are filled".
- Acceptance: verifier closure requires a recorded verification artifact (evidence with operation `verify:<obligation>` and a result); distinct evidence per case (or explicit justification); layer-level open unknowns of status `contradicted`/blocking flag block `ready`; README wording changed.

### F-02 — Typed observation is grade A and independent (High, METHOD)
- Where: `ingest.record_observation` (custody `captured_live`, authority `direct_observation`, controller `observer:<role>`), `grading.custody_cap`.
- Repro: owner's spreadsheet (C) + analyst note "I saw roughly 500 units" → note graded **A**, claim **triangulated**.
- Why it matters: the note has no artifact (photo, timestamp, count sheet); its grade equals an ERP export captured live. A single walk-through (staged day, Hawthorne) becomes the top grade. The limitation string mentions Hawthorne but does not change the grade.
- Acceptance: observation without an attached artifact capped at B (or C); triangulation via observation requires an artifact or ≥2 observation sessions on different days.

### F-01 — Quote presence ≠ support (Medium, METHOD)
- `ledger.add_evidence` checks `normalize_text(quote) in normalize_text(source_text)` and computes grade from `(authority, confidence, custody)` only. `fact` is free text.
- Repro: quote `INV-1,100` + fact "The company is highly profitable and collects all receivables" → grade **A**.
- Mitigation in place: `confidence="inferred"` caps at D — but it is the agent's choice; default is `observed`.
- Acceptance: evidence `fact` is restricted to what the quote/row states (operation-typed facts), and inferences must be separate `inferred` evidence or a claim; or at minimum the report shows quote and fact side by side and flags facts longer/broader than the quote.

### F-03 — Copy laundering in public mode (Medium, METHOD)
- `grading.independent` relies on declared `controller` and `upstream_ids`; in `public` mode `normalize_controller` returns early.
- Repro: press release (acme) + news article copying it (newsco), both `document/public` → claim **triangulated** at B.
- Acceptance: near-duplicate text detection between sources (e.g. shingle overlap > threshold) forces an `upstream` question/unknown before independence is granted.

### F-05 — Public-mode relabelling (Medium, USE)
- `check_source_admissible` trusts `kind`/`custody`; `legal_basis="n/a"` passes as a "URL or registry reference".
- Acceptance: public custody needs a syntactically valid URL/registry id; `kind` override that contradicts the detected kind (spreadsheet→document) requires a reason and is logged in the report.

### F-07 — Grade-blind contradiction (Medium, METHOD)
- `grading.evaluate_claim`: any `contradicting_evidence_ids` ⇒ `CONTRADICTED`.
- Conservative by intent (forces resolution), but an E-grade remark and an A-grade bank record have identical effect, and coverage then shows the item as `contradicted` — no signal of weight. Also no notion of variation by branch/period (difference is labelled contradiction unless contexts are declared).
- Acceptance: report shows the strongest grade on each side; a claim with A-support vs D/E-contradiction is `disputed_weak` (still needs resolution, not equated with strong contradiction).

### F-08 — No retraction (Medium, CODE)
- No API to withdraw/supersede evidence or a source; evidence is content-addressed and immutable. A wrong extraction or a forged document stays in every claim that cites it.
- Acceptance: `retract_evidence(id, reason)` marks it, re-evaluates claims/obligations/hypotheses, and the report lists retractions.

### F-09 / F-10 — Pseudonymization scope (Medium / Low)
- `Pseudonymizer.scrub` replaces known names (from chat senders or earlier) + email/IBAN/phone/TCKN regex. Names in documents, PDFs, interview notes are stored in clear unless the analyst passes them. Phone `0532 111 22 33` *is* caught.
- `pseudonyms.json` maps tokens back to identities in clear; `.reb/.gitignore` = `*` (good), but any copy/zip of the workspace carries it.
- This is pseudonymization, not anonymization: tokens are stable sha256 prefixes of the name (6 hex chars) — a known name can be re-derived without the map (`sha256("PERSON:<name>")`). 
- Acceptance: README says "pseudonymized, not anonymized"; map optionally encrypted or stored outside the workspace; salted tokens; names extraction for documents (or an explicit `--names` list required in modes self/engaged).

### Verified OK (attempts to break that failed)
- `file://` crawl blocked (R-01). Locking: every MCP/CLI write goes through `Ledger.open` (flock) and atomic tmp→replace saves. Re-ingest of identical bytes is idempotent. Changed originals are refused by `read_original`. Unknown resolution needs evidence of the required authority; contradiction cannot be closed as out_of_scope. Desk review cannot close a system-record obligation.
