# Agent Control Tower — Architecture (Current State)

**Status**: Phase 5 — TUI-Ready Interface Seam (in progress)

## Guiding Principle

> Engines first. Then interfaces.

The core of the system (the "engine") must remain independent of any particular user interface. Interfaces (CLI, TUI, web, scripted, etc.) are adapters that plug into the engine at integration time.

This architecture exists because the Responsible Operator intends to primarily use a proper TUI, not the basic console experience.

## Current Architecture

### The Engine
- `ControlTower` (orchestrator.py) is the central engine.
- It owns the spine: Watcher → Parser → Classifier → DecisionRequest production.
- It exposes one primary seam for human decisions: `escalate(request, handler=...)`.
- The engine can be constructed with a `default_handler: DecisionHandler`.

### The Primary Seam
- `DecisionHandler` (interfaces/decision_handler.py) — a `Protocol`.
- Any code that turns a `DecisionRequest` into an `OperatorDecision` must implement this.
- The engine only depends on this interface.

### Current Adapters
- `ConsoleDecisionHandler` (interfaces/console_handler.py) — the original terminal experience, now a proper adapter.
- `AutoApproveHandler` — example of a non-interactive handler.
- `TUIHandler` — architectural placeholder (not implemented).

### Supporting Layers
- `display/` — frontend-agnostic rich data for DecisionRequests (used by both console and future TUIs).
- `models/` — pure data objects (`DecisionRequest`, `OperatorDecision`).

## What This Means

- The engine no longer "owns" the console.
- The console is **one** adapter implementation of `DecisionHandler`.
- A real TUI can implement the same `DecisionHandler` protocol and be dropped in without changing `ControlTower`, receipts, training export, or any other engine component.
- Adding a web UI later follows the exact same pattern.

## Current Limitations (Honest State)

- The interactive decision experience is still the original console Gate (now wrapped as `ConsoleDecisionHandler`).
- No real TUI implementation exists yet.
- Some legacy convenience functions (`run_cli_gate`) still exist for backward compatibility during the transition.
- Documentation and end-to-end seam tests are being added as part of this Phase 5 pass.

## How to Use the Seam (Example)

```python
from control_tower.orchestrator import ControlTower
from control_tower.interfaces import ConsoleDecisionHandler  # or your TUI handler

# Create the engine
tower = ControlTower(Path("."), default_handler=ConsoleDecisionHandler())

# Later, when you have a DecisionRequest:
decision = tower.escalate(some_request)   # uses the default handler
# or
decision = tower.escalate(some_request, handler=my_tui_handler)
```

## Roadmap Alignment

This work is part of making Phase 5 "TUI-ready" as directed. We are deliberately **not** building a full TUI yet. The goal is to make the claim below true:

> "The engine is no longer console-owned. The console is one interface adapter, and the architecture is ready for a real TUI without rewriting the core."

---

**Last updated**: During the Phase 5 TUI-readiness pass.
