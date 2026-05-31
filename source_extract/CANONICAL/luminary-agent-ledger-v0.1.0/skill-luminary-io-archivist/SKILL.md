# Luminary I/O Archivist

## Purpose

Luminary I/O Archivist is a local-first evidence ledger for strengthening Prime Swarm / Luminary traces.

It captures input/output boundary events so later traces can cite evidence instead of relying only on narrative memory.
Use it when a session produces decisions, edits, validation checks, receipts, training traces, or context that should be
auditable after compaction.

## Core Doctrine

Good traces need a spine of evidence.

A trace should be able to answer:

1. What happened?
2. Who or what performed the action?
3. What file, tool, command, or output anchors it?
4. Which claim does it support?
5. Which trace does it strengthen?
6. What does this evidence **not** prove?

## When To Use

Use this skill during:

- Prime Swarm / Luminary Swarm hardening sessions
- Pre-compaction Insight Harvest reviews
- File repair passes
- Skill or card pipeline work
- Any session where trace quality matters
- Any moment where a future reader may ask: "What proves this?"

## Standard Flow

1. Start or name a `run_id`.
2. Log important user instructions.
3. Log reads/searches/edits/commands as events.
4. Log validation checks separately from normal command runs.
5. Link events to claim IDs and trace IDs.
6. Build a receipt after meaningful work.
7. Audit trace markdown for weak or missing evidence coverage.

## Required Boundary

This skill logs evidence. It does not certify correctness, security, release readiness, or absence of missed context.
Validation means the specific logged check passed or produced the recorded output. It does not mean universal certainty.

The Responsible Operator keeps final authority over canon, release, and promotion decisions.

## Scripts

- `scripts/luminary_log_event.py`: append one structured event to `.luminary/events/events.jsonl`.
- `scripts/luminary_build_receipt.py`: summarize events for a run and emit a receipt JSON.
- `scripts/luminary_trace_audit.py`: inspect trace markdown against the evidence ledger.

## Minimum Event Fields

- event_id
- run_id
- timestamp
- actor
- role
- action_type
- target
- summary
- evidence_source
- input_ref
- output_ref
- before_hash
- after_hash
- claim_links
- trace_links
- confidence
- operator_approved
- notes

## Evidence Strength

- E0: claim only
- E1: file/path observed
- E2: action logged
- E3: diff/hash/output anchored
- E4: validation check
- E5: receipt + trace + claim linkage

## Output Rule

Every meaningful session should end with a receipt containing:

- files inspected
- files modified
- events logged
- claims supported
- checks performed
- remaining risks
- claim boundary
- recommended next action
