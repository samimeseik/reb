# Evidence file: Hope Bridge

- **Organization:** Hope Bridge
- **Mode:** engaged
- **Authorization basis:** synthetic-test-mandate
- **Profile:** dd-evidence
- **Generated:** 2026-10-16

> This file states what the recorded evidence shows, with a grade for each finding. It is not an audit, a valuation, legal advice or a warranty. Anything not covered below is unknown, not absent.

## How to read grades

- **A**: record checked with its issuer, captured live, or independent third party
- **B**: governing document, public record, or third party
- **C**: record handed over by the organization itself
- **D**: single testimony or public signal
- **E**: analyst inference

## Coverage by layer

| Layer | Claims | Best grade | Open unknowns |
|---|---|---|---|
| strategy | 0 | — (no evidence) | 0 |
| revenue | 0 | — (no evidence) | 0 |
| customer | 4 | D | 2 |
| operations | 1 | D | 1 |
| equipment | 0 | — (no evidence) | 0 |
| systems | 0 | — (no evidence) | 0 |
| people | 2 | C | 1 |
| supply | 0 | — (no evidence) | 0 |
| finance | 5 | C | 5 |
| regulation | 0 | — (no evidence) | 1 |
| culture | 0 | — (no evidence) | 0 |

## Profile checklist

| Item | Required | Best grade | State |
|---|---|---|---|
| Who legally owns and controls the company (shareholders, directors, signatories)? | A | — | not covered |
| Does the company have overdue tax debt? | A | — | not covered |
| Social-security debt and the registered headcount? | A | — | not covered |
| Liens, seizures and pending litigation against the company or its key assets? | A | — | not covered |
| Who owns the premises and on what terms are they used? | B | — | not covered |
| How concentrated is revenue across customers over the last 12 months? | A | C | below required grade |
| Do the largest customers confirm the relationship and recent invoices? | A | — | not covered |
| Do bank movements match invoiced revenue? | A | C | contradicted |
| Do the claimed machines exist, belong to the company and are they unencumbered? | A | — | not covered |
| What does an unannounced visit show versus the planned visit? | A | — | not covered |
| How dependent is the business on the founder or a few individuals? | C | C | met |
| Is claimed capacity consistent with electricity use and machine hours? | B | — | not covered |
| Staff tenure and turnover? | B | — | not covered |
| How dependent is the business on single suppliers? | B | — | not covered |

## Findings

### customer

- **[D]** Hope Bridge states 95% of families report a better life — single source (or sources under one control) · `ev_b50ab74d117d`, `ev_10614f60b36a`
- **[D]** The only described follow-up method is an informal phone call with some families after distribution — single source (or sources under one control) · `ev_95ef22d37c49`

### operations

- **[D]** Director reports all distributions and payments pass through the director and distributions stopped for three weeks during the director's August travel — single source (or sources under one control) · `ev_02139afe4e8e`

### people

- **[C]** All five 2024 expense rows were approved by the director — single source (or sources under one control) · `ev_406b865f6f49`, `ev_9eefce01ebea`, `ev_1e33c8f9d941`, `ev_f14065f95a90`, `ev_631df280861e`
- **[C]** Annual report states 1 director, 3 coordinators and 40 volunteers — single source (or sources under one control) · `ev_8e5057b9e56d`

### finance

- **[C]** Fund X grant of 400,000 TRY (2024) is restricted to the food basket program — single source (or sources under one control) · `ev_db912bcd19e5`
- **[C]** FundX accounts for 400,000 of 505,000 TRY (79%) of recorded 2024 spending; the rest is labelled general — single source (or sources under one control) · `ev_406b865f6f49`, `ev_9eefce01ebea`, `ev_1e33c8f9d941`, `ev_f14065f95a90`, `ev_631df280861e`
- **[D]** Website states every donation goes directly to food baskets — single source (or sources under one control) · `ev_292fbd15e40e`

## Contradictions (stated vs enacted)

- Hope Bridge states it has served 12,000 families since 2020 (website, repeated by news article from the charity's statement) — `ev_38d29cad7eed`, `ev_10614f60b36a` ⟂ `ev_14e8ca3717ac`
- Annual report year-by-year figures sum to 10,800 families for 2020-2024, 1,200 fewer than the 12,000 claimed publicly — `ev_14e8ca3717ac` ⟂ `ev_38d29cad7eed`
- Expense ledger charges 220,000 TRY of FundX to food baskets (rows 2-3) and 180,000 TRY of FundX to admin salaries (row 4) — `ev_406b865f6f49`, `ev_9eefce01ebea`, `ev_1e33c8f9d941` ⟂ `ev_db912bcd19e5`
- Ledger total 2024 spend is 505,000 TRY, of which food baskets 265,000 TRY (52.5%); admin salaries 180,000 and rent 60,000 — `ev_406b865f6f49`, `ev_9eefce01ebea`, `ev_1e33c8f9d941`, `ev_f14065f95a90`, `ev_631df280861e` ⟂ `ev_292fbd15e40e`
- Why does the stated fundx_food_basket_spend_try (400000 TRY) differ from the enacted fundx_food_basket_spend_try (220000 TRY)? (`unk_9d008fdada5c`)
- Why does the stated food_basket_share_of_spend_pct (100 pct) differ from the enacted food_basket_share_of_spend_pct (52.5 pct)? (`unk_ab3a77954e3a`)

## Open unknowns

- Were 12,000 or 10,800 families served 2020-2024, and are counts unique families or distributions? (`unk_854f80f2ab66`, open) · needs: system_record · next probe: Request beneficiary register (unique IDs, dates) for 2020-2024; dedupe; sample 30 households by independent phone/visit
- Did Fund X approve charging 180,000 TRY of its restricted grant to admin salaries? (`unk_b4431b51da3f`, open) · needs: system_record · next probe: Obtain grant agreement, budget and any written variation from Fund X directly (independent channel); request payroll for the salary row
- Was the 400,000 TRY Fund X grant actually received, and does the ledger reconcile to bank movements? (`unk_a666e8a8e897`, open) · needs: system_record · next probe: Bank statements for 2024 pulled live by the treasurer; confirm disbursement with Fund X
- Is the 5-row expense ledger complete for 2024 (no rows for utilities, transport, coordinators' pay, Jan, Mar, May, Aug, Oct-Dec)? (`unk_90237ade34cc`, open) · needs: system_record · next probe: Full general ledger and audited/annual financial statements 2024; reconcile to bank
- What is the evidence base for '95% report a better life' (sample, instrument, response rate)? (`unk_307b40cfc2be`, open) · needs: direct_observation · next probe: Request survey instrument and raw responses; run independent follow-up with a random sample of households
- How many baskets were distributed, at what unit cost, to whom, and with what supplier invoices? (`unk_55f73de953fb`, open) · needs: system_record · next probe: Distribution lists with signatures, supplier invoices for food baskets; unannounced distribution visit
- Who besides the director can approve payments and run distributions; is there a board and segregation of duties? (`unk_81a4cb4bdd70`, open) · needs: governing_document · next probe: Board minutes, bylaws, signatory mandate from bank; interview coordinators separately
- Legal status, registration and governing board of Hope Bridge? (`unk_a5c7b00b604f`, open) · needs: public_record · next probe: Associations registry extract and board list

## Evidence annex

- `ev_02139afe4e8e` **[D]** Director says every distribution and payment passes through the director, and distributions stopped three weeks when the director travelled in August — Source: Director interview (custody: captured_live), testimony · location: line 2
- `ev_10614f60b36a` **[D]** News article reports 12,000 families since 2020 and 95% better life, attributed to the charity's own statement — Source: News article (custody: public), public_signal · location: line 1
- `ev_14e8ca3717ac` **[C]** Annual report states families served per year 2020-2024: 600, 1,800, 2,400, 2,900, 3,100 (sum 10,800) — Source: Annual report 2024 (custody: subject_held), governing_document · location: line 2
- `ev_1e33c8f9d941` **[C]** Expense row: 2024-06-30 admin salaries charged to FundX, 180,000 TRY, approved by director — Source: Expenses 2024 (custody: subject_held), system_record · location: row 4
- `ev_292fbd15e40e` **[D]** Website states every donation goes directly to food baskets — Source: Website (custody: public), public_signal · location: line 3
- `ev_38d29cad7eed` **[D]** Website states 12,000 families served since 2020 — Source: Website (custody: public), public_signal · location: line 2
- `ev_406b865f6f49` **[C]** Expense row: 2024-02-10 food baskets, FundX, 120,000 TRY, approved by director — Source: Expenses 2024 (custody: subject_held), system_record · location: row 2
- `ev_631df280861e` **[C]** Expense row: 2024-09-12 food baskets, general funds, 45,000 TRY, approved by director — Source: Expenses 2024 (custody: subject_held), system_record · location: row 6
- `ev_8e5057b9e56d` **[C]** Annual report states staff of 1 director, 3 coordinators, 40 volunteers — Source: Annual report 2024 (custody: subject_held), governing_document · location: line 4
- `ev_95ef22d37c49` **[D]** Director says follow-up is a quick phone call with some families afterwards; most are happy — Source: Director interview (custody: captured_live), testimony · location: line 3
- `ev_9eefce01ebea` **[C]** Expense row: 2024-04-15 food baskets, FundX, 100,000 TRY, approved by director — Source: Expenses 2024 (custody: subject_held), system_record · location: row 3
- `ev_b50ab74d117d` **[D]** Website states 95% of families report a better life — Source: Website (custody: public), public_signal · location: line 2
- `ev_db912bcd19e5` **[C]** Annual report states Fund X awarded 400,000 TRY in 2024 restricted to the food basket program — Source: Annual report 2024 (custody: subject_held), governing_document · location: line 3
- `ev_f14065f95a90` **[C]** Expense row: 2024-07-01 rent, general funds, 60,000 TRY, approved by director — Source: Expenses 2024 (custody: subject_held), system_record · location: row 5
