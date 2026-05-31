#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(pwd)}"
mkdir -p "$ROOT/.codex"
if [[ -f "$ROOT/.codex/hooks.json" ]]; then
  cp "$ROOT/.codex/hooks.json" "$ROOT/.codex/hooks.json.bak.$(date -u +%Y%m%d%H%M%S)"
  echo "Existing .codex/hooks.json backed up. Merge integrations/codex/hooks.json manually."
  exit 1
else
  cp "$ROOT/integrations/codex/hooks.json" "$ROOT/.codex/hooks.json"
  echo "Installed Codex hook settings to .codex/hooks.json"
  echo "Open Codex and run /hooks to review/trust the hook definitions."
fi
