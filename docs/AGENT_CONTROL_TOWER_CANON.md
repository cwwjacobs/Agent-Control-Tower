# Agent Control Tower — Canon Architecture

## Kernel

Agent Control Tower is an internal deterministic KSL state rail around nondeterministic AI executors.

It does not make the model deterministic. It makes the work route deterministic.

Core flow:

```text
KSL dispatch packet
→ executor works inside the bounded phase
→ executor emits required JSON phase signal
→ output wrapper captures the signal
→ schema validator checks fields
→ transition table routes state
→ Tower writes state ledger
→ next dispatch becomes available
```

## What the Tower Owns

The Tower owns state, the KSL route, job schemas, dispatch packets, required phase JSON, output capture, schema validation, the transition table, receipt intake, the trace ledger, and next dispatch generation.

The Tower does not think, trust, infer, or decide. It routes from validated fields.

## Main Components

### 1. State Ledger

Tracks the current job, current phase, allowed transitions, warnings, blockers, and run history.

### 2. KSL Protocol Rail

Standard route:

```text
Kernel Lock
→ Spine Map
→ Build Phase
→ Verify Phase
→ Receipt Phase
```

Hard failure returns to Kernel Lock.

### 3. Dispatch System

Generates bounded KSL dispatch packets for Grok, Codex, Claude, Kimi, Gemini, and local tools.

Each dispatch packet includes job id, current phase, kernel, bound, acceptance criteria, required output schema, and stop rule.

### 4. Output Wrapper

Captures executor output from stdout, file, clipboard, share sheet, pasted text, browser adapter, or OCR fallback.

The wrapper extracts the required phase signal block.

### 5. Schema-Gated Router

Validates that job_id matches the current job, phase matches the current phase, phase_status is allowed, next_phase is allowed from the current phase, required fields exist, warnings are structured if present, and operator_required is valid.

Missing, malformed, contradictory, or out-of-range fields stop the run and alert the operator.

### 6. Trace and Training Data Engine

Saves dispatch prompts, executor outputs, phase signals, receipts, route decisions, warnings, operator corrections, and state transitions.

These records become trace data for training/eval use.

### 7. Work Lanes

The Tower can run multiple lanes through the same rail:

```text
Tower self-build lane
repo recovery service lane
dataset/eval lane
Android portability lane
future lanes
```

Services are not the Tower kernel. Services are a work lane inside the Tower.

## Phase Signal Contract

Every phase must end with required structured JSON.

Example:

```text
KSL_PHASE_JSON
{
  "job_id": "trace_quality_001",
  "phase": "BUILD",
  "phase_status": "ACCEPTED_WITH_WARNINGS",
  "next_phase_ready": true,
  "next_phase": "VERIFY",
  "operator_required": false,
  "warnings": [
    "Expected behavior is missing for 3 weak rows."
  ],
  "summary": "Implemented row quality validation, eval case shaping, and quality report generation."
}
END_KSL_PHASE_JSON
```

## Allowed Phase Statuses

```text
ACCEPTED
ACCEPTED_WITH_WARNINGS
REWORK_REQUIRED
BLOCKED
FAILED
```

## Deterministic Routing

```text
ACCEPTED → advance to next phase
ACCEPTED_WITH_WARNINGS → advance to next phase and log warnings for operator review
REWORK_REQUIRED → generate rework dispatch for same phase
BLOCKED → stop run and alert operator
FAILED → route to kernel relock or defined failure state
missing / malformed / out of range → stop run and alert operator
```

## State Machine

Core states:

```text
DRAFT
KERNEL_LOCKED
SPINE_MAPPED
BUILD_READY
BUILD_DISPATCHED
BUILD_SIGNAL_RECEIVED
VERIFY_READY
VERIFY_DISPATCHED
RECEIPT_READY
PASSED
PASSED_WITH_WARNINGS
REWORK_REQUIRED
FAILED
BLOCKED
KERNEL_RELOCK_REQUIRED
```

A next phase is only dispatchable if the current state and validated phase signal allow it.

## Control Pane

The control pane is a thin interface over Tower state. It should show current job, current KSL phase, next acceptable dispatch, last phase signal, warnings, blocked state, receipt status, and next prompt readiness.

The pane does not own logic. The engine owns logic.

## Service Lane

Repo recovery services fit inside the Tower as one lane.

Service flow:

```text
lead / intake / offer
→ repo recovery KSL job
→ executor dispatch
→ phase JSON output
→ Tower validates/routes
→ receipt
→ client delivery
→ follow-up
```

Example service job types:

```text
Repo Reality Check
AI Build Recovery Pass
Launch Readiness Pass
```

## Unified Model

Same rail, different lanes:

```text
Tower self-build:
KSL job → executor → phase JSON → route → receipt

Client repo recovery:
intake → KSL job → executor → phase JSON → route → delivery receipt

Training data:
trace → review → correction → export → receipt

Android port:
portability job → executor → phase JSON → route → receipt
```

## One-Sentence Definition

Agent Control Tower is our internal KSL state ledger and dispatch rail that turns AI work into bounded phases, validated outputs, deterministic routes, receipts, and reusable trace data.
