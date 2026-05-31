# CTGH Deep Dive Notes

Repo: `cwwjacobs/CTGH`
Description from repo metadata: `claude's take on TerminusGateHarness`.
README title: `Terminus Gate Harness`.

## CTGH value spine

CTGH is a Python audit spine harness for Terminus Gate. It already includes:

- deterministic hash core
- receipt model
- receipt seal/validate
- JSONL receipt log
- audit-chain verification
- failure data lane
- local LMStudio-compatible task runner
- operator corrections
- training-corpus emission
- compact sidecar storage for large forensic blobs
- sidecar manifests and zip packaging
- optional Textual operator cockpit
- CLI proof commands

## Responsible operator framing

Core CTGH frame worth preserving:

> Model and tool output has zero responsibility to outcome. The human operator remains the authority for action, approval, and consequence. Terminus Gate Harness does not transfer responsibility. It makes actions, receipts, chains, failures, and operator decisions auditable.

This should stay as public/product boundary language.

## CLI commands observed

`terminus-gate` exposes commands including:

- `receipt-demo`
- `audit`
- `failure-demo`
- `run`
- `task`
- `correct`
- `corpus-emit`
- `sidecar-manifest`
- `package`
- `tui`

Most relevant for Agent Control Tower:

- `run`: policy-check, execute, and receipt a shell command.
- `task`: drive a multi-turn agent task against a local model.
- `correct`: author an operator correction for a failed receipt.
- `corpus-emit`: emit JSONL training corpus from operator-corrected failures.
- `tui`: launch operator cockpit.

## Receipt model fields worth mapping to Luminary

Core enums/classes observed:

- `ActionClassification`: `SHADOWABLE`, `PREVIEWABLE`, `CHECKABLE`, `BLOCKED`, `UNSAFE`, `CORRECTED`
- `RiskLevel`: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`
- `VerificationStatus`: `passed`, `failed`, `skipped`, `unknown`
- `ApprovalStatus`: `granted`, `denied`, `not_required`, `blocked`, `override`
- `Actor`: id + kind (`human`, `agent`, `tool`, `system`)
- `Evidence`: id, kind, summary, ref, hash
- `Approval`: required, status, scope, artifactHash, reason
- `StateRef`: externalStateChanged, beforeRef, afterRef
- `AgentContext`: modelId, systemPrompt, history, toolSurface
- `ProposedAction`: tool, args, rawCompletion
- `Correction`: correctsReceiptId, correctsContentHash, rationale, correctedAction

## Build mapping

Luminary hook payload -> parsed event -> action classification -> CTGH-style receipt -> optional correction -> training/eval row.

Suggested mapping:

- Luminary event `tool_call` / `command_run` => CTGH `ProposedAction`
- Luminary actor/source => CTGH `Actor`
- Green action => `ApprovalStatus.NOT_REQUIRED` or `GRANTED` depending mode
- Yellow action => approval not required but warning/uncertainty added
- Red action => approval required; denied/blocked/override/granted by operator
- Operator modify => `Correction` receipt
- Failed receipt + correction => corpus/eval emission

## What to take from CTGH

KEEP:

- receipt schema idea
- deterministic content hashing
- audit-chain verification
- correction model
- corpus emission model
- sidecar model for large logs/completions/tool surfaces
- responsible-operator framing
- CLI proof-command discipline

REWRITE/ADAPT:

- local-model task runner: useful later, not the first MVP
- Textual TUI: inspect if usable; likely adapt only if it is already simple
- shell runner policy: use as reference, but Control Tower needs hook-stream gating first

MISSING LAYER:

- live JSONL/hook tailer
- plain-English parser/renderer
- green/yellow/red policy rules
- focus/foreground alert for red action
- approve/deny/modify UI
- write decision receipt back into the log
