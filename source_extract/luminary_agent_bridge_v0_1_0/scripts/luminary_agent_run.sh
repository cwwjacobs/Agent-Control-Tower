#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: scripts/luminary_agent_run.sh <agent-name> -- <command> [args...]" >&2
  echo "Example: scripts/luminary_agent_run.sh codex -- codex" >&2
  exit 2
fi

AGENT="$1"
shift
if [[ "$1" != "--" ]]; then
  echo "Expected -- after agent name" >&2
  exit 2
fi
shift

ROOT="${LUMINARY_PROJECT_ROOT:-$(pwd)}"
RUN_ID="${LUMINARY_RUN_ID:-RUN-$(date -u +%Y%m%d-%H%M%S)-${AGENT}}"
export LUMINARY_PROJECT_ROOT="$ROOT"
export LUMINARY_RUN_ID="$RUN_ID"

mkdir -p "$ROOT/.luminary/agent_runs/$RUN_ID"
LOG="$ROOT/.luminary/agent_runs/$RUN_ID/${AGENT}_$(date -u +%Y%m%dT%H%M%SZ).log"
CMD_STR="$*"

python3 "$ROOT/scripts/luminary_log_event.py" \
  --project-root "$ROOT" \
  --run-id "$RUN_ID" \
  --actor "$AGENT" \
  --role "agent-wrapper" \
  --action-type "tool_call" \
  --target "$CMD_STR" \
  --summary "Started wrapped ${AGENT} command." \
  --evidence-source "manual_note" \
  --confidence "inferred" \
  --notes "Wrapper start event. Output will be captured to ${LOG}."

set +e
"$@" 2>&1 | tee "$LOG"
STATUS=${PIPESTATUS[0]}
set -e

python3 "$ROOT/scripts/luminary_log_event.py" \
  --project-root "$ROOT" \
  --run-id "$RUN_ID" \
  --actor "$AGENT" \
  --role "agent-wrapper" \
  --action-type "tool_result" \
  --target "${LOG#$ROOT/}" \
  --summary "Finished wrapped ${AGENT} command with exit status ${STATUS}." \
  --evidence-source "command_output" \
  --output-ref "exit_status=${STATUS}; log=${LOG#$ROOT/}" \
  --confidence "direct" \
  --notes "Captured stdout/stderr transcript for wrapped agent command."

exit "$STATUS"
