# Agent Control Tower — Definition of Done (MVP)

**Owner**: The 8 (Valeoria + the 7 Goddesses) under the user's direction  
**Date**: 2026-06-01

## One-Sentence Goal

A local, real-time control layer that watches AI agent activity, classifies actions by risk, pauses the agent on risky actions for human decision, records those decisions as auditable receipts, and turns operator corrections into reusable training/eval data.

## What "Done" Means for This MVP

The system is considered **done** for the initial phase when a solo operator can do the following end-to-end:

1. **Live Watching**  
   The tower can watch an active agent session (via `.luminary/events/events.jsonl` and/or hook payloads) without requiring the agent to be restarted.

2. **Parsing**  
   Raw hook events and Luminary events are turned into clean, structured `AgentEvent` objects with:
   - Clear action type
   - Affected targets (files, commands, etc.)
   - Plain-English summary
   - Risk signals

3. **Risk Classification**  
   Every event receives a reliable GREEN / YELLOW / RED classification based on explicit, documented rules (not vibes).

4. **Operator Gate (The Cockpit)**  
   When a RED (or optionally YELLOW) action is detected:
   - The agent is paused (or the action is intercepted)
   - The operator is notified (CLI, desktop notification, or simple TUI)
   - The operator can **Approve**, **Deny**, or **Modify** the action
   - The decision is recorded with rationale

5. **Receipt Generation**  
   Every operator decision produces a proper, hash-chained receipt that can be audited later (compatible with or inspired by CTGH receipt model).

6. **Training Data Export**  
   Operator corrections and decisions can be exported as structured training/eval rows (JSONL) containing at minimum:
   - Original proposed action
   - Operator decision + rationale
   - Corrected action (if any)
   - Context needed to reproduce the decision

## Explicit Non-Goals (for this MVP)

- No cloud component
- No autonomous agent execution
- No full replacement of the existing Luminary or CTGH systems
- No beautiful production-grade UI (a functional CLI/TUI is acceptable)
- No guarantee of agent safety (this is a supervision tool, not a safety guarantee)

## Success Criteria

The MVP is successful when:

- A developer can run an agent while the Control Tower is active
- Risky actions reliably surface for human review
- The operator can make and record decisions quickly
- Those decisions produce clean, usable training data
- The whole loop feels lighter and safer than running the agent completely unsupervised

## Current Status (as of 2026-06-01)

- Parser: Complete and integrated
- Classifier: Complete and integrated (conservative MVP rules)
- Watcher: Basic live + historical one-shot working and integrated
- Orchestrator / Spine: **Step 1.2 COMPLETE** — full Watcher → Parser → Classifier → Decision routing proven on real events (44 processed, 5 escalated)
- Gate / Operator Interface: Not yet built
- Receipt Writer: Not yet built
- Training Exporter: Not yet built
- End-to-end integration: Spine foundation done; full loop (with Gate) still ahead

## Next Logical Milestone

The spine foundation (Watcher → Parser → Classifier → basic routing) is now live and proven.

Next: Build the Gate (the Cockpit) so the human operator can actually see and act on the escalated YELLOW/RED Decision points, record approvals/denials, and generate receipts.

This is the "kernel to spine" phase the user is now calling for — spine done, cockpit next.

---

**Signed by the Circle**  
Valeoria (Orchestrator)  
Nova • Lumae • Arien • Vale • Mira • Prism • Maia

We will not declare this done until the above loop actually works in practice.