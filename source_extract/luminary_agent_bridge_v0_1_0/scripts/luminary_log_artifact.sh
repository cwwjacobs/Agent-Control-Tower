#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: scripts/luminary_log_artifact.sh <artifact-path> <summary>" >&2
  exit 2
fi

ROOT="${LUMINARY_PROJECT_ROOT:-$(pwd)}"
RUN_ID="${LUMINARY_RUN_ID:-}"
ARTIFACT="$1"
SUMMARY="$2"

if [[ -z "$RUN_ID" ]]; then
  echo "LUMINARY_RUN_ID is not set. Run: source scripts/luminary_session_on.sh" >&2
  exit 2
fi

python3 "$ROOT/scripts/luminary_log_event.py" \
  --project-root "$ROOT" \
  --run-id "$RUN_ID" \
  --actor "workflow" \
  --role "artifact-logger" \
  --action-type "trace_update" \
  --target "$ARTIFACT" \
  --summary "$SUMMARY" \
  --evidence-source "file_hash" \
  --output-ref "$ARTIFACT" \
  --confidence "direct" \
  --notes "Artifact explicitly logged by workflow."
