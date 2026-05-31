#!/usr/bin/env bash
set -euo pipefail

ROOT="${LUMINARY_PROJECT_ROOT:-$(pwd)}"
RUN_ID="${LUMINARY_RUN_ID:-}"

if [[ -z "$RUN_ID" ]]; then
  echo "LUMINARY_RUN_ID is not set. Run: source scripts/luminary_session_on.sh" >&2
  exit 2
fi

python3 "$ROOT/scripts/luminary_build_receipt.py" \
  --project-root "$ROOT" \
  --run-id "$RUN_ID" \
  --write-receipt-event \
  --remaining-risk "This receipt summarizes explicitly hooked or wrapped events only." \
  --claim-boundary "Luminary Agent Bridge records events it receives from hooks/wrappers; it does not prove universal capture or system correctness." \
  --recommended-next-action "Review event coverage and add missing hooks/wrappers for uncaptured actions." \
  --json
