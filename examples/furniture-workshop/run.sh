#!/usr/bin/env bash
# End-to-end walkthrough on the synthetic furniture workshop (all data is invented).
# Usage: ./run.sh   (needs `reb` on PATH, or set REB=/path/to/reb)
set -euo pipefail
cd "$(dirname "$0")"
REB="${REB:-reb}"
WS="engagement"
D="data"
rm -rf "$WS" && mkdir -p "$WS"
r() { "$REB" -w "$WS" --json "$@"; }
get() { python3 -c "import json,sys; d=json.load(sys.stdin); print($1)"; }

echo "== 1. open a self-mode engagement with the sop-replication profile"
r init --name "Workshop operating-system capture" --subject "Örnek Mobilya Atölyesi" \
  --mode self --authorization "owner (synthetic example)" --profile sop-replication --language ar >/dev/null

echo "== 2. ingest sources (names, phones are pseudonymized at ingest)"
CHAT=$(r ingest "$D/WhatsApp Chat - Siparisler.txt" --custody subject_held --origin "orders WhatsApp group" \
  --controller "workshop" --legal-basis "staff notice N-2026-01 (synthetic)" | get 'd["source"]["id"]')
ORDERS=$(r ingest "$D/orders.csv" --custody subject_held --origin "office order list" --controller "workshop" \
  --kind system_export | get 'd["source"]["id"]')
SOP=$(r ingest "$D/sop.md" --custody subject_held --origin "owner" --controller "workshop" | get 'd["source"]["id"]')
# The usta works for the workshop: his account is the workshop's own account, so the
# controller is "workshop". Interviews never count as independent of the organization.
INTERVIEW=$(r ingest "$D/interview-usta.txt" --kind interview --custody captured_live --origin "workshop master" \
  --controller "workshop" --legal-basis "consent C-2026-03 (synthetic)" | get 'd["source"]["id"]')
# Invoices handed over as files are subject_held (grade cap C). Use issuer_verifiable only
# after each UUID was checked with the tax authority and that check was logged as a source.
INV_IDS=()
for f in "$D"/invoices/*.xml; do
  INV_IDS+=("$(r ingest "$f" --custody subject_held --origin "workshop accounting" --controller "workshop" \
    --title "$(basename "$f")" | get 'd["source"]["id"]')")
done
echo "   chat=$CHAT orders=$ORDERS sop=$SOP interview=$INTERVIEW invoices=${#INV_IDS[@]}"

echo "== 3. process mining from the WhatsApp group"
PM=$(r eventlog "$CHAT" --activity-map "$D/activity-map.json" --case-pattern '#(\d+)' \
  --entity "order-to-delivery" --mermaid process.mmd)
PM_EV=$(echo "$PM" | get 'd["evidence_id"]')
MEDIAN_H=$(echo "$PM" | get 'd["cycle_time_hours"]["median"]')
P90_H=$(echo "$PM" | get 'd["cycle_time_hours"]["p90"]')
REWORK=$(echo "$PM" | get 'd["rework"]["cases"]')
SLOWEST=$(echo "$PM" | get 'max(d["edges"], key=lambda e: e["median_hours"])')
echo "   median cycle ${MEDIAN_H}h, p90 ${P90_H}h, rework cases ${REWORK}; slowest edge: ${SLOWEST}"

echo "== 4. revenue concentration from e-invoices"
INV=$(r invoices "${INV_IDS[@]}" --direction sales)
INV_EV=$(echo "$INV" | get 'd["evidence_id"]')

echo "== 5. evidence from documents and the interview (quotes are checked against the text)"
SOP_EV=$(r evidence --source "$SOP" --authority governing_document --layer operations \
  --fact "The written procedure states a standard lead time of 10 days." \
  --quote "Standart teslim süresi: 10 gün." --location "line 12" | get 'd["id"]')
INT_LT=$(r evidence --source "$INTERVIEW" --authority testimony --layer operations \
  --fact "The usta says a typical order takes about ten days." \
  --quote "Normally about ten days." --location "line 4" | get 'd["id"]')
INT_EDGE=$(r evidence --source "$INTERVIEW" --authority testimony --layer culture \
  --fact "Only one operator can set up the edge-bander for 2 mm PVC." \
  --quote "Nobody else can set it up for the 2 mm PVC." --location "line 7" | get 'd["id"]')
CHAT_EDGE=$(r evidence --source "$CHAT" --authority testimony --layer culture \
  --fact "A chat message says only one person can set up the edge-bander for 2 mm PVC." \
  --quote "Kenar bant makinesini 2mm PVC için sadece" --location "chat" | get 'd["id"]')
INT_PAINT=$(r evidence --source "$INTERVIEW" --authority testimony --layer operations \
  --fact "The usta names the single spray booth as where orders get stuck." \
  --quote "We have one spray booth and the lacquer needs a full day to cure." --location "line 10" | get 'd["id"]')

echo "== 6. a site walk (direct observation)"
OBS=$(r observe --title "Site walk 2026-10-10" --role "analyst" --site "workshop floor" --when "2026-10-10" \
  --legal-basis "staff notice N-2026-01 (synthetic)" \
  --note "Morning walk through all stations." \
  --fact '{"fact": "Nine assembled carcasses were waiting in front of the single spray booth.", "layer": "operations", "entity": "paint"}' \
  | get 'd["evidence"][0]["id"]')

echo "== 7. claims (status and grade are computed)"
r claim --statement "The written procedure and the usta state a lead time of about 10 days." --layer operations \
  --kind stated --metric lead_time_days --value 10 --unit days --entity order-to-delivery \
  --item ops.core-process --evidence "$SOP_EV" --evidence "$INT_LT" >/dev/null
DAYS=$(python3 -c "print(round($MEDIAN_H/24, 1))")
r claim --statement "Order-to-delivery takes a median of $DAYS days in the orders group (p90 $(python3 -c "print(round($P90_H/24,1))") days)." \
  --layer operations --kind enacted --metric lead_time_days --value "$DAYS" --unit days --entity order-to-delivery \
  --item ops.core-process --evidence "$PM_EV" --replicability codifiable >/dev/null
r claim --statement "The spray booth is the bottleneck: the longest wait in the process is before or in painting." \
  --layer operations --item ops.bottleneck --evidence "$PM_EV" --evidence "$INT_PAINT" --evidence "$OBS" \
  --replicability needs_asset >/dev/null
r claim --statement "Edge-bander setup for 2 mm PVC depends on a single operator." --layer culture \
  --item culture.tacit --evidence "$INT_EDGE" --evidence "$CHAT_EDGE" --replicability needs_capability >/dev/null
r claim --statement "Revenue is spread across a small number of customers (see concentration)." --layer revenue \
  --item revenue.customers --evidence "$INV_EV" >/dev/null
r claim --statement "Customers mostly come through architects' referrals." --layer revenue --industry-prior >/dev/null

echo "== 8. stated vs enacted"
r compare --metric lead_time_days --entity order-to-delivery | get '[(p["stated_value"], p["enacted_value"], p["relative_gap"]) for p in d.get("pairs", [])]'

echo "== 9. unknowns"
r unknown add --question "What is the unit cost of a kitchen cabinet (materials, labour minutes, overhead)?" \
  --layer finance --item econ.unit-cost --required-authority system_record \
  --probe "Collect purchase e-invoices for boards and edge tape for the same 3 months" >/dev/null
r unknown add --question "Which licences and permits does the workshop hold?" --layer regulation --item reg.licences \
  --required-authority public_record --probe "Pull the trade registry entry and municipal licence" >/dev/null

echo "== 10. one obligation progressed (owner + cases + verifier)"
# The verifier must cite evidence beyond the case evidence: the model (from the chat)
# predicted a queue at the spray booth; the site walk then observed it.
r obligation --item ops.bottleneck --owner "workshop manager" --case "happy_path=$PM_EV" --case "peak_load=$INT_PAINT" \
  --verifier prediction --passed --verifier-evidence "$OBS" \
  --note "Process model predicted the paint queue later observed on the site walk." >/dev/null

echo "== 11. coverage and report"
r coverage | get 'd["summary"]'
"$REB" -w "$WS" report --lang ar --out report.ar.md >/dev/null
"$REB" -w "$WS" report --lang en --out report.en.md >/dev/null
echo "   wrote report.ar.md, report.en.md, process.mmd"
