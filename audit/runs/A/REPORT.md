# Hope Bridge — Funder Due-Diligence Report (synthetic case)

Sources: 5 files in `case/`. All originate from or quote the organization; none is independent (news article explicitly relays "the charity said in a statement", news_article.md:1).

## 1. Reach
**Evidence:** Annual families served 2020–2024: 600 / 1,800 / 2,400 / 2,900 / 3,100 (annual_report_2024.md:2). Sum = **10,800**.
**Contradiction:** Website and news claim **12,000** families "since 2020" (website.md:2, news_article.md:1) — 1,200 (+11%) above the organization's own annual figures.
**Unknown:** Whether annual counts are unique families or repeat visits (if repeat, unique reach < 10,800). No beneficiary register.

## 2. Funding & use of funds
**Evidence:**
- Fund X granted 400,000 TRY in 2024, "restricted to the food basket program" (annual_report_2024.md:3).
- Expenses charged to FundX total 400,000 TRY: food baskets 120,000 (expenses_2024.csv row 2) + 100,000 (row 3) and **admin salaries 180,000 (row 4)**.
- **Finding:** 180,000 TRY (45% of the restricted grant) was charged to salaries — on the face of the records, a breach of the restriction, unless an amendment exists that is not in the files.
- Total recorded 2024 spend 505,000 TRY; food baskets 265,000 (52%); salaries+rent 240,000 (48%) (rows 2–6).

**Contradiction:** Website: "Every donation goes directly to food baskets" (website.md:3) vs. 48% overhead in the ledger (rows 4–5).
**Unknown:** Total income and other donors ("general" funds not broken down, rows 5–6); whether the ledger is complete (only 5 rows for a full year); whether accounts are audited.

## 3. Operations & people
**Evidence:**
- Staff: 1 director, 3 coordinators, 40 volunteers (annual_report_2024.md:4).
- Director approved all 5 expenses (expenses_2024.csv, `approved_by` column).
- Director: "Every distribution and every payment passes through me" (interview_director.md:2).
- Distributions stopped for three weeks when the director travelled in August (interview_director.md:2).

**Inferred:** No segregation of duties; single point of failure — both a fraud/control risk and a service-continuity risk. The 3 coordinators apparently lack delegated authority.
**Unknown:** Board oversight, written financial controls, payroll detail (who received the 180,000 TRY).

## 4. Impact
**Claim:** "95% of families report a better life" (website.md:2, news_article.md:1).
**Evidence of method:** Only "a quick phone call with some families afterwards; most are happy" (interview_director.md:3).
**Assessment:** The 95% figure is **unsupported** — no sample size, instrument, baseline, or random selection; "some families" is not a random sample, and "happy" ≠ "better life". Outputs (baskets distributed) can be inferred; outcomes cannot.

## 5. Verification steps
1. Beneficiary register 2020–2024: reconcile to 10,800 vs 12,000; deduplicate families.
2. Fund X grant agreement + any amendments; written confirmation from Fund X on whether salary use was approved.
3. Full 2024 general ledger, bank statements, and audited/independently reviewed financial statements; check completeness of the 5-row ledger.
4. Payroll records for the 180,000 TRY salaries.
5. Independent beneficiary survey: random sample, stated method, outcome indicators.
6. Governance review: board minutes, delegation of authority, backup signatory/distribution lead.
7. Unannounced site visit during distributions.

## 6. Recommendation
**Do not fund now; reconsider conditionally.** The organization appears to deliver food baskets at real scale (~2–3k families/year by own count), but three issues block a grant: a probable restricted-fund breach (45%), public claims contradicted by its own data (12,000; "every donation"), and an unsubstantiated impact figure.

**Conditions precedent:** (a) Fund X written confirmation the salary use was approved, or repayment/reallocation; (b) correction of public claims; (c) dual authorization for payments and a named deputy for distributions.

**If funded:** tranche-based disbursement tied to reconciled distribution lists; explicit overhead budget line (so salaries aren't charged to restricted funds); quarterly expense reports with receipts; independent outcome survey before tranche 2.
