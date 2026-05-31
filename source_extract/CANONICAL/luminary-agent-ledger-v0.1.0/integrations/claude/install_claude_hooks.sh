#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(pwd)}"
mkdir -p "$ROOT/.claude"
if [[ -f "$ROOT/.claude/settings.local.json" ]]; then
  cp "$ROOT/.claude/settings.local.json" "$ROOT/.claude/settings.local.json.bak.$(date -u +%Y%m%d%H%M%S)"
  echo "Existing .claude/settings.local.json backed up. Merge integrations/claude/settings.local.json.snippet manually."
  exit 1
else
  cp "$ROOT/integrations/claude/settings.local.json.snippet" "$ROOT/.claude/settings.local.json"
  echo "Installed Claude hook settings to .claude/settings.local.json"
fi
