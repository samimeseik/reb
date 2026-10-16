# Hope Bridge — funder diligence (synthetic case)

Grades: C = record handed over by the organization; D = testimony/public signal. Nothing reaches A/B: every source traces back to Hope Bridge itself (the news article explicitly repeats "the charity said in a statement", news_article.md:1, so it is not independent).

## What the evidence shows (Known)
- **Use of funds [C]:** 2024 ledger spend 505,000 TRY: food baskets 265,000; admin salaries 180,000; rent 60,000 (expenses_2024.csv rows 2–6).
- **Restricted grant charged to salaries [C]:** Fund X 400,000 TRY "restricted to the food basket program" (annual_report_2024.md:3); ledger charges 220,000 FundX to food baskets (rows 2–3) and **180,000 FundX to admin salaries** (row 4). Stated-vs-enacted gap 45%; unknown opened.
- **Funding concentration [C]:** Fund X = 79% of recorded spend (400k / 505k).
- **Key-person dependence [C + D]:** director approved all 5 expense rows (rows 2–6); director states "every distribution and every payment passes through me" and distributions stopped three weeks during an August trip (interview_director.md:2). Ledger has no rows between 2024-07-01 and 2024-09-12 — consistent with, not proof of, that account.
- **Staffing (stated) [C]:** 1 director, 3 coordinators, 40 volunteers (annual_report_2024.md:4).

## Contradictions
1. **Reach:** 12,000 families since 2020 (website.md:2; news_article.md:1) vs annual figures summing to **10,800** (annual_report_2024.md:2) — 1,200 (11%) unaccounted.
2. **"Every donation goes directly to food baskets"** (website.md:3) vs ledger: food baskets 52.5% of spend (rows 2–6).
3. **Restricted grant vs actual use** (above).

## Inferred (not established)
- The 180k salary charge may breach the grant restriction unless Fund X approved a variation; no variation in the files.
- Food-basket spend 265k / 3,100 families ≈ 85 TRY per family per year — implausibly low for a basket program; suggests the reach figure or the ledger is incomplete (analyst inference, grade E).
- The ledger looks incomplete: no coordinator pay, transport, utilities; most months empty.

## Unknown (with probes recorded in REB)
| Unknown | Verification step |
|---|---|
| Real unique families | Beneficiary register with unique IDs, de-duplicate; independent calls/visits to 30 sampled households |
| Fund X approval of salary use | Contact Fund X directly for grant agreement and any variation; 2024 payroll |
| Grant received; ledger vs bank | Treasurer pulls 2024 bank statements live; reconcile to ledger |
| Ledger completeness | Full general ledger and 2024 financial statements |
| Basis for "95% better life" | Survey instrument and raw data; only method described is "quick phone call with some families" (interview_director.md:3) |
| Baskets, unit cost, suppliers | Signed distribution lists, supplier invoices, unannounced visit during distribution |
| Governance / segregation of duties | Registry extract, board minutes, bank signatory mandate; separate coordinator interviews |

Coverage: 4 of 11 layers have evidence (finance, people at C; customer, operations at D); `fin.cash` contradicted; most diligence items (legal status, bank reconciliation, unannounced visit) have no evidence — unknown, not absent.

## Funding recommendation
**Do not fund now; reconsider conditionally.** The organization runs a food-basket activity (the ledger shows it), but three issues block a grant: restricted funds apparently partly diverted to salaries; public reach/impact claims not supported by the organization's own records; one person controls every payment and distribution.

Conditions: (1) written explanation of the 180k salary charge plus independent confirmation from Fund X; (2) bank-reconciled 2024 ledger and financial statements; (3) de-duplicated beneficiary register and correction or substantiation of the public 12,000 figure; (4) dual authorization on payments and a named deputy for distributions.

If met: small tranche-based grant restricted to direct program costs, each tranche released against distribution lists and supplier invoices, plus an independently run outcome survey to replace the 95% claim.
