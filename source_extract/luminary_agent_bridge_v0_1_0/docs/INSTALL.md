# Installing Luminary Agent Bridge into SWARMPRIMETRACE

## 1. Copy files

```bash
cd ~/Desktop/SWARMPRIMETRACE
unzip /path/to/luminary_agent_bridge_v0_1_0.zip
cp -a luminary_agent_bridge_v0_1_0/. .
chmod +x scripts/luminary_*.sh scripts/luminary_hook_router.py integrations/*/*.sh integrations/grok/lumi-grok
```

## 2. Probe

```bash
scripts/luminary_bridge_probe.sh
```

## 3. Claude

```bash
integrations/claude/install_claude_hooks.sh
```

If `.claude/settings.local.json` already exists, merge `integrations/claude/settings.local.json.snippet` manually.

Inside Claude Code, run:

```text
/hooks
```

Confirm the Luminary hook entries are visible.

## 4. Codex

```bash
integrations/codex/install_codex_hooks.sh
```

Inside Codex, run:

```text
/hooks
```

Review and trust the hook definitions.

## 5. Grok

```bash
integrations/grok/lumi-grok -p "audit this project and write a short report to outputs/grok_probe.md"
```

Then log the output:

```bash
scripts/luminary_log_artifact.sh outputs/grok_probe.md "Grok probe output saved."
```

## 6. End session

```bash
scripts/luminary_session_receipt.sh
```
