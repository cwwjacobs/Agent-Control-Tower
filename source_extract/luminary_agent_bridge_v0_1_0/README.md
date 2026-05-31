# Luminary Agent Bridge v0.1.0

Purpose: connect Luminary I/O Archivist to Claude Code, Codex CLI, and Grok/Grok Build workflows.

This pack assumes your project already has:

- `.luminary/events/events.jsonl`
- `scripts/luminary_log_event.py`
- `scripts/luminary_build_receipt.py`
- `scripts/_luminary_common.py`

It adds a shared hook router, shell wrappers, and integration snippets.

## What this does

- Logs agent lifecycle/tool events into `.luminary/events/events.jsonl`
- Hashes output targets when they are real files
- Builds receipts per `RUN_ID`
- Gives Claude and Codex hook entrypoints
- Gives Grok a safe wrapper + AGENTS contract

## Claim boundary

This bridge proves that hooked/wrapped events were logged. It does not prove universal correctness, security, production readiness, or that every possible tool action was intercepted.

## Quick install

From your SWARMPRIMETRACE root:

```bash
unzip luminary_agent_bridge_v0_1_0.zip
cp -a luminary_agent_bridge_v0_1_0/. .
chmod +x scripts/luminary_*.sh scripts/luminary_hook_router.py integrations/grok/lumi-grok
```

## Turn on a run

```bash
source scripts/luminary_session_on.sh
```

## Manual wrapper pattern

```bash
scripts/luminary_agent_run.sh codex -- codex
scripts/luminary_agent_run.sh claude -- claude
scripts/luminary_agent_run.sh grok -- grok-build
```

For headless / prompt mode:

```bash
scripts/luminary_agent_run.sh grok -- grok-build -p "audit the repo and output a report"
```

## End a run

```bash
scripts/luminary_session_receipt.sh
```

## Claude Code hook install

Copy `integrations/claude/settings.local.json.snippet` into `.claude/settings.local.json`, merging with existing settings if needed.

Claude has first-class hook events such as `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, and `SessionEnd`.

## Codex hook install

Copy `integrations/codex/hooks.json` into `.codex/hooks.json`.

Codex hooks are project-local once the `.codex/` layer is trusted. Use `/hooks` in Codex to review/trust them.

## Grok install

Grok Build's public docs say AGENTS.md, plugins, hooks, skills, and MCP servers work out of the box, but if exact local hook schema is uncertain, use the wrapper:

```bash
integrations/grok/lumi-grok -p "your prompt"
```

Or paste the content of `integrations/grok/AGENTS.luminary.md` into your project `AGENTS.md`.
