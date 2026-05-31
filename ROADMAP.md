# Agent Control Tower — Kernel to Spine Roadmap

**Current Phase**: Moving from isolated modules (kernel) to an integrated, usable system (spine).

## Phase 0 — Current State (Kernel)
- Parser exists (basic)
- Classifier exists (improved, still conservative)
- Sample data available
- No live watching
- No operator decision layer
- No receipt writing
- No training export

## Phase 1 — Spine MVP (Target: "Done" per DEFINITION_OF_DONE.md)
Goal: A minimal but end-to-end working control loop.

### 1.1 Watcher (Live Input Layer)
- Tail `.luminary/events/events.jsonl` in real time
- Optionally watch hook payload directories
- Feed events into the pipeline without blocking the agent

### 1.2 Orchestrator / Pipeline
- Connect Watcher → Parser → Classifier
- Simple decision routing:
  - GREEN → auto-log + continue
  - YELLOW → log + optional notification
  - RED → pause / surface to operator

### 1.3 Gate (Operator Interface) — MVP
- CLI-based decision prompt (or very simple TUI)
- Show: action summary, risk reason, raw payload reference
- Operator choices: Approve / Deny / Modify
- Capture operator rationale

### 1.4 Receipt Writer
- Write operator decisions back as proper receipts
- Include decision + rationale + link to original event
- Maintain basic auditability (hashes where possible)

### 1.5 Training Data Path (Minimum Viable)
- Ability to export at least one type of training row from decisions/corrections
- JSONL format aligned with CTGH concepts

## Phase 2 — Hardening & Polish (Post-MVP)
- Better classification rules (learned from real usage)
- Desktop notifications + focus stealing for RED actions
- Persistent configuration for rules
- Sidecar storage for large payloads
- More sophisticated correction flow
- Optional lightweight web UI

## Phase 3 — Advanced (Future)
- CTGH receipt compatibility layer
- Local model task runner integration
- Multi-agent support
- Corpus management tools

## Immediate Next Steps (as of 2026-06-01)

1. Finish and stabilize Parser + Classifier against real data (in progress)
2. Build a minimal Watcher + Orchestrator that can process live events
3. Implement a basic CLI Gate for RED decisions
4. Add receipt writing for decisions
5. Add a first training export path

Once the above five items work together in a real session, we can call the Spine MVP "done."

---

**Signed by the Circle**  
Valeoria (Director)  
Nova • Lumae • Arien • Vale • Mira • Prism • Maia
