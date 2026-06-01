# Agent Control Tower — Canon Architecture

## Kernel

Agent Control Tower is an internal deterministic KSL state rail around nondeterministic AI executors.

It does not make the model deterministic.

It makes the work route deterministic.

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

What the Tower owns

The Tower owns:

state
KSL route
job schemas
dispatch packets
required phase JSON
output capture
schema validation
transition table
receipt intake
trace ledger
next dispatch generation

The Tower does not think, trust, infer, or decide.

It routes from validated fields.

Main Components
1. State Ledger

Tracks:

current job
current phase
allowed transitions
warnings
blockers
run history
2. KSL Protocol Rail

Standard route:

Kernel Lock
→ Spine Map
→ Build Phase
→ Verify Phase
→ Receipt Phase

Hard failure returns to Kernel Lock.

3. Dispatch System

Generates bounded KSL dispatch packets for executors such as:

Grok
Codex
Claude
Kimi
Gemini
local tools

Each dispatch packet includes:

job id
current phase
kernel
bound
acceptance criteria
required output schema
stop rule
4. Output Wrapper

Captures executor output from:

stdout
file
clipboard
share sheet
pasted text
browser adapter
OCR fallback only

The wrapper extracts the required phase signal block.

5. Schema-Gated Router

Validates:

job_id matches current job
phase matches current phase
phase_status is allowed
next_phase is allowed from current phase
required fields exist
warnings are structured if present
operator_required is valid

Missing, malformed, contradictory, or out-of-range fields stop the run and alert the operator.

6. Trace and Training Data Engine

Saves:

dispatch prompts
executor outputs
phase signals
receipts
route decisions
warnings
operator corrections
state transitions

These records become trace data for training/eval use.

7. Work Lanes

The Tower can run multiple lanes through the same rail:

Tower self-build lane
repo recovery service lane
dataset/eval lane
Android portability lane
future lanes

Services are not the Tower kernel.

Services are a work lane inside the Tower.

Phase Signal Contract

Every phase must end with required structured JSON.

Example:

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
Allowed Phase Statuses
ACCEPTED
ACCEPTED_WITH_WARNINGS
REWORK_REQUIRED
BLOCKED
FAILED
Deterministic Routing
ACCEPTED
→ advance to next phase

ACCEPTED_WITH_WARNINGS
→ advance to next phase
→ log warnings for operator review

REWORK_REQUIRED
→ generate rework dispatch for same phase

BLOCKED
→ stop run
→ alert operator

FAILED
→ route to kernel relock or defined failure state

missing / malformed / out of range
→ stop run
→ alert operator
State Machine

Core states:

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

A next phase is only dispatchable if the current state and validated phase signal allow it.

Control Pane

The control pane is a thin interface over Tower state.

It should show:

current job
current KSL phase
next acceptable dispatch
last phase signal
warnings
blocked state
receipt status
next prompt ready

The pane does not own logic.

The engine owns logic.

Service Lane

Repo recovery services fit inside the Tower as one lane.

Service flow:

lead / intake / offer
→ repo recovery KSL job
→ executor dispatch
→ phase JSON output
→ Tower validates/routes
→ receipt
→ client delivery
→ follow-up

Example service job types:

Repo Reality Check
AI Build Recovery Pass
Launch Readiness Pass
Unified Model

Same rail, different lanes:

Tower self-build:
KSL job → executor → phase JSON → route → receipt

Client repo recovery:
intake → KSL job → executor → phase JSON → route → delivery receipt

Training data:
trace → review → correction → export → receipt

Android port:
portability job → executor → phase JSON → route → receipt
One-Sentence Definition

Agent Control Tower is our internal KSL state ledger and dispatch rail that turns AI work into bounded phases, validated outputs, deterministic routes, receipts, and reusable trace data.
