# Agent Control Tower Build Pack

Purpose: handoff pack for building the next MVP from the Luminary wrapper/hook system + CTGH receipt/training spine.

## Product spine

**Agent Control Tower** = live wrapper/hook monitor + parsed receipt UI + training-data loop.

Target behavior:

1. Watch agent JSONL/log/hook streams live.
2. Parse hook payloads and receipts into plain-English events.
3. Classify actions:
   - GREEN: auto-allow, log only.
   - YELLOW: allow/log/summarize, maybe warn.
   - RED: pause/foreground UI for operator decision.
4. Operator can approve, deny, or modify.
5. Decision writes a receipt.
6. Failure/correction pairs emit training/eval data.

## What is in this pack

- `source_extract/CANONICAL/luminary-agent-ledger-v0.1.0/` — strongest Luminary ledger source.
- `source_extract/luminary_agent_bridge_v0_1_0/` — bridge wrapper package.
- `source_extract/scripts/` — top-level Luminary scripts.
- `source_extract/integrations/` — Claude/Codex/Grok hooks/integration files.
- `source_extract/schemas/` — event/receipt/claim schemas.
- `source_extract/.luminary/` — example events, hook payloads, and receipts for parser fixtures.
- `notes/CTGH_DEEP_DIVE_NOTES.md` — notes from inspecting cwwjacobs/CTGH through connector.
- `notes/MVP_BUILD_TARGET.md` — build target and first-pass architecture.

## Build intent

Do not rebuild everything. Preserve working Luminary capture pieces, then add the missing layer:

- live parser
- classification policy
- operator cockpit / foreground alert
- CTGH-compatible receipt/correction/training export

## First files to inspect

1. `source_extract/CANONICAL/luminary-agent-ledger-v0.1.0/scripts/luminary_hook_router.py`
2. `source_extract/CANONICAL/luminary-agent-ledger-v0.1.0/scripts/luminary_log_event.py`
3. `source_extract/CANONICAL/luminary-agent-ledger-v0.1.0/scripts/luminary_build_receipt.py`
4. `source_extract/CANONICAL/luminary-agent-ledger-v0.1.0/schemas/event.schema.json`
5. `source_extract/CANONICAL/luminary-agent-ledger-v0.1.0/schemas/receipt.schema.json`
6. `source_extract/CANONICAL/luminary-agent-ledger-v0.1.0/integrations/claude/settings.local.json.snippet`
7. `source_extract/CANONICAL/luminary-agent-ledger-v0.1.0/integrations/codex/hooks.json`

## Current assessment

Luminary already captures/writes the agent trail. CTGH already has stronger receipt/correction/corpus concepts. The valuable MVP is the live control layer between them.
