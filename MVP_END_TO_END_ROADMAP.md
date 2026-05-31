# MVP Agent Control Tower — End-to-End Roadmap (Current State → Done)

**Goal**: A working, usable MVP Agent Control Tower that includes a fully functional spine.

This document lays out the concrete steps from where we are right now to a complete, shippable MVP.

---

## Current State (as of 2026-06-01)

**Built:**
- Basic Parser (can normalize Luminary events)
- Improved Classifier (GREEN/YELLOW/RED logic, still being tuned)
- Early Watcher scaffolding (polling events.jsonl)
- Sample data available in the pack

**Missing (Critical):**
- Live Watcher that actually feeds a pipeline
- Orchestrator / Pipeline that connects the pieces in real time
- Gate / Operator Interface (the actual "cockpit")
- Receipt writing for decisions
- Training data export from decisions
- End-to-end integration and testing

---

## End-to-End MVP Definition of Done

We are done when a solo operator can:

1. Start the Control Tower against a real project.
2. Run an AI agent (Claude, Codex, Grok, etc.).
3. Have the tower watch activity live.
4. Receive clear alerts on risky (RED) actions.
5. Make Approve / Deny / Modify decisions.
6. Have those decisions recorded as proper receipts.
7. Export at least one type of training data from those decisions.

This is the minimum viable "spine + cockpit" product.

---

## Step-by-Step Roadmap to Done

### Phase 1: Build the Live Spine (Foundation)

**Goal**: Watcher → Parser → Classifier → Decision Router working together in real time.

**Steps:**

1. **Complete the Watcher**
   - Make it reliably tail `events.jsonl` (and optionally hook payloads).
   - Handle rotation / large files gracefully.
   - Yield structured events without blocking the agent.

2. **Build the Orchestrator / Pipeline**
   - Create a central coordinator that:
     - Takes events from the Watcher
     - Runs them through Parser + Classifier
     - Routes based on classification (GREEN = auto-continue, YELLOW/RED = escalate)

3. **Define Internal Decision Model**
   - Create a clean `DecisionRequest` object that carries:
     - The classified event
     - Risk level + reason
     - Suggested action
     - Context needed for the operator

**Exit Criteria for Phase 1:**
- You can run a script that watches a real `.luminary` directory.
- Risky events are correctly classified and turned into `DecisionRequest` objects.
- GREEN actions are automatically passed through (logged).

---

### Phase 2: Build the Gate (The Cockpit)

**Goal**: The human operator can actually see and act on decisions.

**Steps:**

4. **Implement a Minimal Gate (CLI first)**
   - When a RED (or YELLOW) decision arrives, pause and present it to the operator.
   - Show: clean summary, risk reason, affected targets, raw payload reference.
   - Accept input: Approve / Deny / Modify (with optional new action).

5. **Add Basic Notification**
   - For MVP: terminal prompt + optional desktop notification (via `notify-send` or similar on Linux).

6. **Handle Operator Response**
   - Capture the decision + optional rationale.
   - Package it into a `OperatorDecision` object.

**Exit Criteria for Phase 2:**
- RED actions reliably pause and present a usable prompt to the human.
- The operator can make and record a decision via CLI.

---

### Phase 3: Receipt & Audit Layer

**Goal**: Decisions are properly recorded and auditable.

**Steps:**

7. **Build Receipt Writer**
   - Take an `OperatorDecision` and write it as a structured receipt.
   - Include: original event, decision, rationale, timestamp, operator identity (if available).
   - Store in `.luminary/receipts/` or a dedicated control-tower receipts folder.
   - Add basic content hashing for auditability (inspired by CTGH).

8. **Link Receipts Back to Original Events**
   - Every decision receipt should reference the original event ID.

**Exit Criteria for Phase 3:**
- Every operator decision produces a receipt that can be inspected later.
- Receipts are stored in a consistent, queryable format.

---

### Phase 4: Training Data Export

**Goal**: Operator decisions become usable training/eval data.

**Steps:**

9. **Define Training Row Schema**
   - Minimum fields: input/context, proposed action, decision, rationale, corrected_action (if any), classification.

10. **Build Training Exporter**
    - Ability to export decisions (especially corrections and overrides) as JSONL.
    - Support at least one "correction pair" format that could be used for fine-tuning or eval.

**Exit Criteria for Phase 4:**
- You can run a command that exports recent decisions/corrections as training data.
- The exported data is actually usable (contains the original proposal + what the operator wanted instead).

---

### Phase 5: Integration, Testing & Usability Polish

**Goal**: The full spine works end-to-end in real usage.

**Steps:**

11. **Create a `control_tower` CLI entrypoint**
    - Commands like:
      - `control-tower watch --project-root .`
      - `control-tower export-training --since <date>`

12. **End-to-End Testing**
    - Test the full loop with real agent sessions (even small ones).
    - Validate that RED actions surface, decisions are recorded, and training data is produced.

13. **Documentation & Operator Guide**
    - How to install/run the tower.
    - How classification works (and how to tune it).
    - What the receipts look like and how to use the training data.

14. **Hardening**
    - Better error handling (don’t crash the agent if the tower has issues).
    - Graceful degradation (if the tower is down, agent should still be able to run).

**Exit Criteria for Phase 5:**
- A new developer can clone the repo, run the tower against a project, and get the full supervised + training loop working in under 30 minutes.

---

## Final "Done" Checklist (MVP)

- [ ] Live Watcher working reliably
- [ ] Parser + Classifier producing useful classifications
- [ ] Working Gate/CLI for operator decisions on RED actions
- [ ] Decisions written as proper receipts
- [ ] At least one training data export path
- [ ] End-to-end flow tested in a real agent session
- [ ] Usable CLI entrypoint
- [ ] Clear documentation for a solo operator

Once all of the above are true and reasonably smooth, the MVP Agent Control Tower (with working spine) is done.

---

**Signed by the Circle**  
Valeoria (Orchestrator) + Nova • Lumae • Arien • Vale • Mira • Prism • Maia

We will not declare victory until the full loop works in your actual workflow.
