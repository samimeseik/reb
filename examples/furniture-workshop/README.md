# Example: furniture workshop (synthetic)

A 4-person furniture workshop that runs its order book in a WhatsApp group.
Everything here is invented: the workshop, the people, the tax ids and the invoices.

| File | What it plays |
|---|---|
| `data/WhatsApp Chat - Siparisler.txt` | The orders group: 24 orders from order to delivery, with repaints |
| `data/orders.csv` | The office's order list |
| `data/invoices/*.xml` | 8 UBL-TR sales e-invoices |
| `data/sop.md` | The owner's written procedure ("10 days") |
| `data/interview-usta.txt` | Interview with the workshop master (with consent) |
| `data/activity-map.json` | Keywords that map chat messages to process steps |

```bash
REB=../../.venv/bin/reb ./run.sh     # or just ./run.sh if `reb` is on PATH
```

The run writes `report.ar.md`, `report.en.md` and `process.mmd`. It shows:

- **Stated vs enacted.** The SOP and the usta say about 10 days. The orders group shows a median of about 15 days. This becomes a contradicted unknown, and the checklist item is marked `contradicted`.
- **Bottleneck.** The longest wait is assembly → paint, plus a repaint loop. The process data, the interview and one site walk agree, but the claim stays **single source [B]**: the data and the interview are both the workshop's, and a single typed site walk with no photo or count sheet is capped at B and cannot corroborate on its own. A photo of the queue, or a second walk on another day, would triangulate it.
- **Not triangulation.** The SOP and the usta's interview share one controller (the workshop), so they count as one source. Agreeing with yourself is not corroboration.
- **Tacit knowledge.** Only one person can set up the edge-bander for 2 mm PVC. The evidence is testimony only (grade D), from a single controller. The next probe is to observe it.
- **Invoices.** They were handed over as files, so their custody is `subject_held` and the grade is capped at C. They would reach A only after each UUID is checked with the tax authority.
- **Conjecture.** "Customers mostly come through architects" has no evidence and is shown as conjecture.
- **Obligations.** `ops.bottleneck` has an owner, cases, and a prediction confirmed by an independent site walk, recorded with `reb verify`. It still stays `open`: an open contradiction on the operations layer (stated vs enacted lead time) blocks it, and its case evidence comes from a chat the workshop handed over (grade C) and an interview (grade D), both below the item's required grade B. Pulling the order log live, or timing the paint queue on site, would close it. The other obligations stay `open` or `unknown`, with reasons.

Regenerate the data with `python generate_data.py`.
