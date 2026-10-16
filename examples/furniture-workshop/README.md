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
- **Bottleneck.** The longest wait is assembly → paint, plus a repaint loop. The process data, the interview and a site walk agree, but the claim stays `single_source`: the data and the interview share the workshop as controller, and the site walk is a typed note with no photo or count sheet, so it is capped at grade B and needs a second session on another day (or an attached artifact) to triangulate.
- **Not triangulation.** The SOP and the usta's interview share one controller (the workshop), so they count as one source. Agreeing with yourself is not corroboration.
- **Tacit knowledge.** Only one person can set up the edge-bander for 2 mm PVC. The evidence is testimony only (grade D), from a single controller. The next probe is to observe it.
- **Invoices.** They were handed over as files, so their custody is `subject_held` and the grade is capped at C. They would reach A only after each UUID is checked with the tax authority.
- **Conjecture.** "Customers mostly come through architects" has no evidence and is shown as conjecture.
- **Obligations.** `ops.bottleneck` has an owner, its own evidence per case, and a recorded verification (`reb verify`): the process model predicted the paint queue and the site walk found it. It still stays `open` for two reasons. Its case evidence comes from a chat the workshop handed over (grade C) and an interview (grade D), both below the item's required grade B. And the lead-time contradiction on the operations layer is still unresolved. Pulling the order log live, or timing the paint queue on site, and resolving the lead-time gap would close it. The other obligations stay `open` or `unknown`, with reasons.

Regenerate the data with `python generate_data.py`.
