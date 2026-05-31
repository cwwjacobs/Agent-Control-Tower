# MVP Build Target: Agent Control Tower

## One sentence

A local control tower for Claude/Codex/Kimi-style agents that watches hook/log streams, parses actions, auto-allows safe work, interrupts for risky work, and turns failures/corrections into reusable training/eval data.

## MVP user story

As an operator using an AI coding agent, I want the agent to keep working on safe actions, but I want a foreground alert when it attempts a risky file edit, command, config change, secret/payment/auth/deploy change, or destructive operation.

## MVP modules

### 1. Watcher

Inputs:

- `.luminary/events/events.jsonl`
- `.luminary/hook_payloads/**/*.json`
- optional CTGH `.terminus-gate/receipts.jsonl`

Behavior:

- tail JSONL or poll file tree
- normalize each payload into an internal `AgentEvent`

### 2. Parser

Turns raw event into:

- source agent
- session/run id
- event type
- proposed action
- affected files
- command/tool name
- risk indicators
- plain-English summary

### 3. Classifier

Rules:

GREEN:

- read-only file reads
- status/list commands
- docs-only small edits
- generated reports/receipts
- formatting-only changes

YELLOW:

- dependency files
- config files
- public copy/pricing/claims
- broad refactors
- generated code touching app behavior

RED:

- secrets/env/auth/payment/deploy files
- destructive commands (`rm`, `git reset --hard`, force push, credential writes)
- production deploy or domain/DNS changes
- repo-wide delete/rename
- legal/medical/security claims
- permission changes

### 4. Gate/UI

MVP can be simple:

- terminal TUI or tiny local web UI
- red action causes beep/focus/desktop notification if possible
- show action summary + raw payload path
- buttons/keys: approve / deny / modify / mark green next time

### 5. Receipt writer

Output:

- normalized decision receipt
- link to raw payload hash/ref
- operator decision
- reason/rationale
- before/after refs if available

### 6. Training data exporter

Rows from:

- blocked action + approved correction
- failed action + operator corrected action
- drifted output + preferred output
- red/yellow classification decision

Output format:

- JSONL eval/corpus rows
- include input/context/action/decision/rationale/corrected_action

## First implementation target

Build a parser/classifier against the sample files included in this pack before wiring any live controls.

Suggested first command:

```bash
python -m control_tower.parse_samples --root ./source_extract/.luminary --out ./current_run/parsed_events.jsonl
```

Suggested second command:

```bash
python -m control_tower.watch --events ./source_extract/.luminary/events/events.jsonl --mode dry-run
```

## Non-goals for MVP

- no cloud SaaS
- no production sandbox claim
- no autonomous credential management
- no promise that agents are safe
- no universal agent framework

## Sellable name options

- Agent Control Tower
- Agent Receipt Tower
- Luminary Control Tower
- Terminus Agent Gate
- Live Gate + Receipt Trail

## Strongest product claim

Turn AI-agent work into supervised actions, auditable receipts, and reusable correction data.
