# Benchmarks: does the blueprint layer predict how organizations really work?

## Method (hold-out)

1. Open a `public`-mode blueprint and run `start_blueprint` on the organization's public website.
2. Choose an **answer key**: the pages or documents where the organization describes its own internals (organization chart, team page, production page, franchise terms, annual report). Set it aside.
3. From the **other** pages only:
   - record the strong traces as claims;
   - record **predictions** (hypotheses) about the parts that are not visible, each with a test.
4. Only then read the answer key. Grade each prediction `correct`, `partial` or `wrong` with `grade_hypothesis`. Predictions the answer key cannot settle stay ungraded.
5. Feed every miss back into the library (archetypes, kernel, equipment) and every tool failure back into the code.

Verdicts are used **only for calibration**. The engine does not accept them as evidence. When the answer key came from the same website as the signals, the engine refused to mark predictions "supported" (no self-corroboration). The predictions stay inferences, and the strong traces were recorded as separate claims.

## Results (October 2026, v0.2)

| Organization | Type (archetype) | Answer key | Graded | Correct | Partial | Wrong |
|---|---|---|---|---|---|---|
| Turkish Ministry of Trade | public body (`ministry`) | published unit list (site navigation) | 7 | 3 | 4 | 0 |
| Tat Gıda (listed food manufacturer) | industrial (`food-factory`) | 2025 integrated annual report (PDF) | 7 | 4 | 3 | 0 |
| TEMA Foundation (environmental NGO) | non-profit (`charity`) | governance pages, HQ team page, representations list, enterprise page | 6 | 4 | 1 | 1 |
| Kahve Dünyası (café chain) | business (`restaurant-cafe`) | production page, franchise page | 4 | 2 | 2 | 0 |
| **Total** | | | **24** | **13** | **10** | **1** |

Accuracy, counting a partial as one half:

| Confidence | Graded | Accuracy |
|---|---|---|
| low (archetype only) | 8 | 0.75 |
| medium (one source) | 16 | 0.75 |
| high (independent sources) | 0 | — |

Seven further predictions could not be settled by the answer keys (for example store count, procurement practice, agriculture team). They remain open unknowns.

## What the benchmarks taught us (and what changed)

### Method
- **Low and medium confidence had the same accuracy.** Every signal came from the organization's own site, so no prediction could reach "high". A real blueprint must collect **independent** traces (registries, job boards, procurement awards, reports by third parties). This step is now explicit in the skill.
- **Strong traces are often already public.** The ministry's site navigation lists every central and regional unit; TEMA publishes its full HQ team. These are facts (claims), not inferences, and navigation repeated on every page is **one** source.
- **Old pages leave stale traces.** Tat Gıda's history page and its current "at a glance" page disagree on the number of plants. The annual report settled it: three plants.
- **Annual and activity reports are the richest traces.** They hold headcount, export share, plant capacities, cost structure and channels.

### Library (archetypes, kernel, equipment)
- **Ministry.** Added:
  - law-enforcement arms and special-zone administrations;
  - revolving funds next to the budget;
  - regional (multi-province) field directorates.
- **Charity / foundation.** Added:
  - a commercial arm selling services (e.g. landscaping);
  - three-layer governance (trustees, board of directors, science board);
  - lawsuits handled outside an in-house legal unit.
- **Food factory.** Added:
  - contract farming with seasonal advances;
  - a permanent core plus seasonal workforce;
  - plant specialization;
  - new equipment: multi-effect evaporator, aseptic filler, retort.
- **Café chain.** Added:
  - vertical integration (own roasting, chocolate, ice cream);
  - partly in-store production;
  - franchising only abroad (master franchise per country);
  - multiple store formats.

### Tooling
- **Crawler priority.** Breadth-first crawling got stuck in a product catalogue. Organization pages (about, corporate, franchise, careers, management, investors, reports, production, stores) are now visited first.
- **Report PDFs.** Linked report PDFs are now listed (`report_documents`) so the agent can ingest them. Public mode now accepts published financial statements and open-data tables.
- **JavaScript-rendered pages** (for example a store locator) are flagged (`js_rendered_pages`) for a browser visit.
- **Archetype suggestion** now matches whole words. Before, "kurum" matched "kurumsal" and "UN" matched "bulunan". All four benchmarks now get the right archetype first.
- **Fingerprints** match hosts, not page words (fixed a false "ikas" detection). The mail-gateway providers Proofpoint and Mimecast are recognized.
- **`read_source(skip_boilerplate=true)`** hides menus and footers repeated across a site's pages and keeps the original line numbers.

## Reproducing

```bash
reb init --name "Benchmark" --subject "<organization>" --mode public --profile blueprint
reb blueprint start --url https://<site> --archetype <archetype>
# choose the answer key, record predictions from the other pages, then read the key and:
reb hypothesis grade <hypothesis_id> --verdict correct|partial|wrong
reb blueprint build --json | jq .calibration
```

Benchmark ledgers are kept outside the repository. They contain public pages of real organizations, and some of those pages name individuals.
