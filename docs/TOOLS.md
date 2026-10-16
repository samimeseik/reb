# Tools (MCP) and commands (CLI)

The MCP tools and the CLI commands share the same workflows. Every tool accepts
`workspace`, which defaults to `$REB_WORKSPACE` and then the current directory.
On failure a tool returns `{"error": "<code>", "message": "<remedy>"}`.

| MCP tool | CLI | Shape | Purpose |
|---|---|---|---|
| `list_profiles` | `reb profiles` | list | Built-in checklists and their allowed modes |
| `open_engagement` | `reb init` | setup | Organization, aliases (other names and web domains: their sources never count as independent), mode, authorization, profile, language |
| `ingest_source` | `reb ingest PATH` | inspect | Hash, check admissibility, extract, pseudonymize, record inventory evidence |
| `read_source` | `reb read SRC` | inspect | Stored text with line numbers, for quoting |
| `record_observation` | `reb observe` | observe | Site walk, time study or nameplate reading as direct observation |
| `record_evidence` | `reb evidence` | record | One fact from a source. The quote is checked and the grade computed |
| `record_claim` | `reb claim` | record | Statement plus evidence. Status and grade are computed |
| `record_unknown` / `update_unknown` | `reb unknown add/update` | record | Open questions with revisions. Resolving one needs evidence of the required authority |
| `search_evidence` | `reb export` + jq | search | Filter evidence by text, layer, entity or minimum grade |
| `analyze_event_log` | `reb eventlog SRC` | trace | Variants, directly-follows graph (Mermaid), cycle times, rework |
| `analyze_invoices` | `reb invoices SRC…` | inspect | Sales or purchase concentration (top shares, HHI) |
| `compare_stated_vs_enacted` | `reb compare` | compare | Opens contradicted unknowns for gaps beyond the tolerance |
| `inspect_coverage` | `reb coverage` | workflow | Coverage per layer and per profile item |
| `record_obligation` | `reb obligation` | record | Owner, case evidence and verifier for an obligation |
| `build_obligation_ledger` | `reb ledger` | workflow | Status (`ready` / `open` / `failed` / `unknown`) with reasons |
| `render_report` | `reb report` | workflow | Markdown report in Arabic (RTL) or English |

### Blueprint layer

| MCP tool | CLI | Purpose |
|---|---|---|
| `show_kernel` | `reb kernel [--family F]` | Building blocks, design rules, traces; how a family builds them |
| `list_archetypes` | `reb archetypes` | Ready-made operating models |
| `start_blueprint` | `reb blueprint start --url U [--archetype A]` | Crawl the public site (robots.txt), footprint, archetype suggestion, seed |
| `apply_archetype` | `reb blueprint apply A` | Seed (more) archetype hypotheses |
| `add_hypothesis` | `reb hypothesis add` | Inference with signals / calculation; confidence computed |
| `update_hypothesis` | `reb hypothesis update` | Add signals; support or refute with evidence |
| `promote_hypothesis` | `reb hypothesis promote` | Supported hypothesis becomes a graded claim |
| `grade_hypothesis` | `reb hypothesis grade` | Owner verdict, for calibration only |
| `add_design_item` | `reb design` | copy / improve / cannot_copy / build_step, with refs |
| `add_equipment` | `reb equipment` | Equipment register entry with station and rate |
| `check_consistency` | `reb consistency` | Do the parts fit together? |
| `build_blueprint` | `reb blueprint build` | Full blueprint as JSON |
| `render_blueprint` | `reb blueprint render --md --html --pdf` | 7-section report |

## Blueprint loop

1. `open_engagement(profile="blueprint")` → `start_blueprint(url)`.
2. Search for wider public traces (registries, job ads, reports, procurement, maps, videos); ingest each one you use.
3. Record strong traces as claims. Support, refute or promote the archetype hypotheses.
4. Add signal hypotheses, equipment and calculations with metrics. Then call `check_consistency`.
5. Add redesign items with refs.
6. Call `render_blueprint`.

## Typical agent loop

1. `open_engagement`, choosing the mode and profile carefully.
2. `ingest_source` for each file. Then `read_source`, followed by `record_evidence` with verbatim quotes.
3. `analyze_event_log` and `analyze_invoices` where the data allows.
4. `record_claim`: one claim per finding, `kind=stated` or `kind=enacted` when a number is involved.
5. `compare_stated_vs_enacted` for each metric that has both kinds.
6. `inspect_coverage`. For each `not_covered` or `below_required` item, `record_unknown` with a probe.
7. `record_obligation` as owners, cases and verifiers become available.
8. `render_report`.
