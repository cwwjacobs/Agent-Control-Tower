#!/usr/bin/env bash
set -euo pipefail

export LUMINARY_PROJECT_ROOT="${LUMINARY_PROJECT_ROOT:-$(pwd)}"
export LUMINARY_RUN_ID="${LUMINARY_RUN_ID:-RUN-$(date -u +%Y%m%d-%H%M%S)-agent-bridge}"

mkdir -p "$LUMINARY_PROJECT_ROOT/.luminary/events" "$LUMINARY_PROJECT_ROOT/.luminary/receipts"

python3 "$LUMINARY_PROJECT_ROOT/scripts/luminary_log_event.py" \
  --project-root "$LUMINARY_PROJECT_ROOT" \
  --run-id "$LUMINARY_RUN_ID" \
  --actor "user" \
  --role "responsible-operator" \
  --action-type "decision" \
  --target "Luminary Agent Bridge" \
  --summary "Activated Luminary Agent Bridge for Claude/Codex/Grok workflow." \
  --evidence-source "manual_note" \
  --confidence "inferred" \
  --notes "Activation marker only; proves this run id exists, not that all future actions are automatically captured."

echo "LUMINARY_RUN_ID=$LUMINARY_RUN_ID"
echo "LUMINARY_PROJECT_ROOT=$LUMINARY_PROJECT_ROOT"
echo
echo "Keep this shell open, or export these vars in any agent shell:"
echo "export LUMINARY_PROJECT_ROOT=\"$LUMINARY_PROJECT_ROOT\""
echo "export LUMINARY_RUN_ID=\"$LUMINARY_RUN_ID\""
