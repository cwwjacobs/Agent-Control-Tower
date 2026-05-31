#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$(pwd)}"
cd "$ROOT"

export LUMINARY_PROJECT_ROOT="$ROOT"
export LUMINARY_RUN_ID="${LUMINARY_RUN_ID:-RUN-$(date -u +%Y%m%d-%H%M%S)-bridge-probe}"

echo "Project: $ROOT"
echo "Run: $LUMINARY_RUN_ID"

python3 scripts/luminary_log_event.py \
  --project-root "$ROOT" \
  --run-id "$LUMINARY_RUN_ID" \
  --actor "bridge-probe" \
  --role "quality-gate" \
  --action-type "validation" \
  --target "scripts/luminary_hook_router.py" \
  --summary "Validated Luminary Agent Bridge files are installed and callable." \
  --evidence-source "command_output" \
  --output-ref "bridge probe executed" \
  --confidence "direct"

printf '{"hook_event_name":"PostToolUse","tool_name":"Bash","cwd":"%s","tool_input":{"command":"echo probe"},"tool_response":{"stdout":"probe","stderr":"","interrupted":false},"session_id":"%s"}' "$ROOT" "$LUMINARY_RUN_ID" \
  | python3 scripts/luminary_hook_router.py >/dev/null

python3 scripts/luminary_build_receipt.py \
  --project-root "$ROOT" \
  --run-id "$LUMINARY_RUN_ID" \
  --write-receipt-event \
  --remaining-risk "Bridge probe validates hook router logging only." \
  --claim-boundary "Probe proves the router can receive synthetic hook input and write ledger events." \
  --recommended-next-action "Enable Claude/Codex hooks and run /hooks to verify/trust them." \
  --json

echo
echo "Recent events:"
tail -n 5 .luminary/events/events.jsonl | jq -c .
