# Evidence file: Örnek Mobilya Atölyesi

- **Organization:** Örnek Mobilya Atölyesi
- **Mode:** self
- **Authorization basis:** owner (synthetic example)
- **Profile:** sop-replication
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
| revenue | 2 | C | 0 |
| customer | 0 | — (no evidence) | 0 |
| operations | 3 | B | 1 |
| equipment | 0 | — (no evidence) | 0 |
| systems | 0 | — (no evidence) | 0 |
| people | 0 | — (no evidence) | 0 |
| supply | 0 | — (no evidence) | 0 |
| finance | 0 | — (no evidence) | 1 |
| regulation | 0 | — (no evidence) | 1 |
| culture | 1 | D | 0 |

## Profile checklist

| Item | Required | Best grade | State |
|---|---|---|---|
| What is the end-to-end core process (order to delivery) as actually enacted, including exceptions? | B | C | contradicted |
| Which step limits throughput, and by how much? | B | B | met |
| Which machines exist, their rated capacity, condition and who can operate them? | B | — | not covered |
| What does each role actually do, who decides what (RACI), and who is a single point of failure? | C | — | not covered |
| How are people recruited, onboarded, trained and paid? | C | — | not covered |
| Who are the critical suppliers, lead times and alternatives? | B | — | not covered |
| What does one unit / job cost (materials, labour minutes x rate, overhead) and what margin does it earn? | B | — | not covered |
| Where does revenue come from (customers, channels, concentration) and how is price set? | B | C | below required grade |
| Which tools and systems hold the data (incl. paper, WhatsApp, Excel) and how does information move? | C | — | not covered |
| Which licences, permits and registrations are required and current? | B | — | not covered |
| What know-how lives only in people's heads, and with whom? | C | D | below required grade |

## Findings

### revenue

- **[C]** Revenue is spread across a small number of customers (see concentration). — single source (or sources under one control) · `ev_b18517dfe1b9`

### operations

- **[B]** The spray booth is the bottleneck: the longest wait in the process is before or in painting. — single source (or sources under one control) · `ev_4df8e4bba69b`, `ev_be6db0c90b5f`, `ev_18b145c2ec73`
- **[C]** The written procedure and the usta state a lead time of about 10 days. — single source (or sources under one control) · `ev_1b9f9e9922ad`, `ev_4fa429b9c6c4`
- **[C]** Order-to-delivery takes a median of 14.9 days in the orders group (p90 18.4 days). — single source (or sources under one control) · `ev_4df8e4bba69b`

### culture

- **[D]** Edge-bander setup for 2 mm PVC depends on a single operator. — single source (or sources under one control) · `ev_b3dde0d62d97`, `ev_67129ffc8cf8`

## Contradictions (stated vs enacted)

- Why does the stated lead_time_days (10 days) differ from the enacted lead_time_days (14.9 days)? (`unk_0b07fd610764`)

## Open unknowns

- What is the unit cost of a kitchen cabinet (materials, labour minutes, overhead)? (`unk_cd0137391d58`, open) · needs: system_record · next probe: Collect purchase e-invoices for boards and edge tape for the same 3 months
- Which licences and permits does the workshop hold? (`unk_379196879fe2`, open) · needs: public_record · next probe: Pull the trade registry entry and municipal licence

## Conjecture — not supported by recorded evidence

- ⚠ Customers mostly come through architects' referrals.

## Replicability

**needs an asset (licence, location, capital, equipment)**

- The spray booth is the bottleneck: the longest wait in the process is before or in painting.

**needs a capability to be built**

- Edge-bander setup for 2 mm PVC depends on a single operator.

**codifiable (can be written down and taught)**

- Order-to-delivery takes a median of 14.9 days in the orders group (p90 18.4 days).

## Reconstruction obligations

**open** · {'open': 3, 'unknown': 6}

- `ops.core-process` — **open** — missing owner (accountable role); missing case evidence: happy_path, exception_rework, peak_load, staff_absence, supplier_failure; missing passing verifier; open unknowns on this item, or blocking/contradicted on its layer: unk_0b07fd610764
- `ops.bottleneck` — **open** — case evidence below grade B: happy_path, peak_load; open unknowns on this item, or blocking/contradicted on its layer: unk_0b07fd610764
- `equip.register` — **unknown** — no evidence recorded for this item
- `people.roles` — **unknown** — no evidence recorded for this item
- `people.hiring` — **unknown** — no evidence recorded for this item
- `supply.suppliers` — **unknown** — no evidence recorded for this item
- `econ.unit-cost` — **unknown** — no evidence recorded for this item
- `systems.map` — **unknown** — no evidence recorded for this item
- `culture.tacit` — **open** — missing owner (accountable role); missing case evidence: staff_absence; missing passing verifier

## Evidence annex

- `ev_18b145c2ec73` **[B]** Nine assembled carcasses were waiting in front of the single spray booth. — Source: Site walk 2026-10-10 (custody: captured_live), direct_observation · location: workshop floor · limitations: Observed workers may behave differently while observed (Hawthorne effect).
- `ev_1b9f9e9922ad` **[C]** The written procedure states a standard lead time of 10 days. · «Standart teslim süresi: 10 gün.» — Source: sop.md (custody: subject_held), governing_document · location: line 12
- `ev_4df8e4bba69b` **[C]** Process discovered from 24 cases / 177 events: median cycle time 357.0h (p90 441.0h); most common path order → measure → cut → edge → assembly → paint → deliver (15 cases); 9 cases with rework. — Source: WhatsApp Chat - Siparisler.txt (custody: subject_held), system_record · limitations: Events reconstructed from message keywords: steps never mentioned in this chat are missing.; Activity mapping was supplied by the analyst; different keywords give a different process.
- `ev_4fa429b9c6c4` **[D]** The usta says a typical order takes about ten days. · «Normally about ten days.» — Source: interview-usta.txt (custody: captured_live), testimony · location: line 4
- `ev_67129ffc8cf8` **[D]** A chat message says only one person can set up the edge-bander for 2 mm PVC. · «Kenar bant makinesini 2mm PVC için sadece» — Source: WhatsApp Chat - Siparisler.txt (custody: subject_held), testimony · location: chat
- `ev_b18517dfe1b9` **[C]** 8 sales invoices, 4 counterparties, total 351600.0 TRY; largest counterparty share 0.355; HHI 3014. — Source: invoice-001.xml (custody: subject_held), system_record · limitations: Covers only the invoices ingested; missing months or off-book sales are not represented.; Counterparties are identified by tax id. Check related parties separately.
- `ev_b3dde0d62d97` **[D]** Only one operator can set up the edge-bander for 2 mm PVC. · «Nobody else can set it up for the 2 mm PVC.» — Source: interview-usta.txt (custody: captured_live), testimony · location: line 7
- `ev_be6db0c90b5f` **[D]** The usta names the single spray booth as where orders get stuck. · «We have one spray booth and the lacquer needs a full day to cure.» — Source: interview-usta.txt (custody: captured_live), testimony · location: line 10
