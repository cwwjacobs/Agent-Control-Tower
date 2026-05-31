"""
Agent Control Tower - Minimal Orchestrator (Early Spine)

This is the beginning of the integrated pipeline:
Watcher → Parser → Classifier → Decision Routing

Phase: 1 (Live Spine)
Current Step: 1.3 – Basic Decision Request Model + Simple Escalation Hook
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .watcher import LiveWatcher
from .parser import AgentEvent
from .classifier import classify_event, ClassificationResult, RiskLevel
from .models import DecisionRequest, OperatorDecision
from .interfaces.decision_handler import DecisionHandler


class ControlTower:
    """
    The core engine of the Agent Control Tower.

    This is the "engine" the Responsible Operator wants built first.
    It handles the spine (watching, parsing, classifying, producing DecisionRequests)
    and provides the escalation seam.

    Interfaces (DecisionHandler implementations for CLI, TUI, web, etc.)
    are injected at the integration level, not baked into the engine.
    This is the correct order: Engine first, then interfaces.
    """

    def __init__(
        self,
        project_root: Path,
        default_handler: DecisionHandler | None = None,
    ):
        self.project_root = project_root.resolve()
        self.watcher = LiveWatcher(self.project_root)
        self._default_handler = default_handler  # The seam is configured here, not hardcoded

    def process_event(self, event: AgentEvent) -> Optional[DecisionRequest]:
        """
        Core pipeline step.
        Returns a DecisionRequest only for events that require operator attention (non-GREEN).
        Returns None for GREEN events (auto-continue path).
        """
        classification = classify_event(event)

        if classification.risk_level == RiskLevel.GREEN:
            return None

        # Non-GREEN → produce a proper DecisionRequest (Step 1.3 model)
        return DecisionRequest.from_event_and_classification(
            event=event,
            classification=classification,
        )

    def escalate(
        self,
        request: DecisionRequest,
        handler: DecisionHandler | None = None,
    ) -> OperatorDecision | None:
        """
        The primary escalation seam for the engine.

        The engine will use the provided handler, or fall back to the
        default_handler that was injected at construction time.

        This is the clean integration point. Different interfaces
        (CLI, TUI, etc.) are supplied here — the engine itself stays pure.
        """
        request.status = "escalated"

        effective_handler = handler or self._default_handler

        if effective_handler is not None:
            decision = effective_handler.handle_decision(request)
            return decision

        # No handler available — legacy / dry-run / notification behavior
        print(f"[ESCALATE] {request.to_summary()}")
        return None

    def run_dry(self, max_events: Optional[int] = None, historical: bool = False):
        """
        Dry-run mode: Process events without taking any action.
        This is the current target for Step 1.2 EOS.
        When historical=True (for testing on sample data), uses one-shot read so it terminates.
        Live mode (historical=False) uses the infinite tailing watch() for real sessions.
        """
        print(f"[ControlTower] Starting dry run on {self.project_root}")
        mode = "historical (bounded)" if historical else "live (tailing)"
        print(f"[ControlTower] Mode: {mode}")
        print("[ControlTower] Pipeline: Watcher → Parser → Classifier → DecisionRequest Routing (Step 1.3)\n")

        escalated_requests: list[DecisionRequest] = []
        green = 0
        yellow = 0
        red = 0
        count = 0

        if historical:
            events = self.watcher.watch_once(limit=max_events)
            event_iter = iter(events)
        else:
            event_iter = self.watcher.watch()

        for event in event_iter:
            request = self.process_event(event)

            if request is None:
                # GREEN — auto-continue, no DecisionRequest created
                green += 1
            else:
                # Non-GREEN — we now have a proper DecisionRequest
                escalated_requests.append(request)
                self.escalate(request)

                if request.is_yellow():
                    yellow += 1
                else:
                    red += 1

            count += 1
            if max_events is not None and count >= max_events:
                break

        print("=== Dry Run Summary ===")
        print(f"Total events processed: {count}")
        print(f"GREEN : {green}")
        print(f"YELLOW: {yellow}")
        print(f"RED   : {red}")
        print(f"DecisionRequests created (sent to escalation seam): {len(escalated_requests)}")
        print(f"\n[ControlTower] Dry run complete.")

        return escalated_requests  # Only escalated items are returned (the ones that hit the Gate seam)

    def run_and_save_decisions(self, output_path: Path, max_events: Optional[int] = None, historical: bool = False):
        """Run dry and save all escalated DecisionRequests to a JSONL file. Useful for later Gate / training work."""
        requests = self.run_dry(max_events=max_events, historical=historical)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for req in requests:
                record = {
                    "request_id": req.request_id,
                    "timestamp": req.timestamp,
                    "event_id": req.event.event_id,
                    "run_id": req.event.run_id,
                    "action_type": req.event.action_type,
                    "target": req.event.target,
                    "summary": req.event.summary,
                    "risk_level": req.classification.risk_level.value,
                    "escalation_reason": req.escalation_reason,
                    "suggested_action": req.classification.suggested_action,
                    "status": req.status,
                }
                f.write(json.dumps(record) + "\n")

        print(f"\n[ControlTower] Saved {len(requests)} DecisionRequests to {output_path}")


if __name__ == "__main__":
    # Try robust sample locations that contain real .luminary/events/events.jsonl
    candidates = [
        Path("source_extract/CANONICAL/luminary-agent-ledger-v0.1.0"),
        Path("source_extract"),
    ]
    sample_root = None
    for cand in candidates:
        if (cand / ".luminary" / "events" / "events.jsonl").exists():
            sample_root = cand
            break

    if sample_root is None:
        print("[ControlTower] ERROR: No sample events.jsonl found in candidates.")
        print("Tried:", [str(c) for c in candidates])
        raise SystemExit(1)

    print(f"[ControlTower] Using sample root: {sample_root}")
    tower = ControlTower(sample_root)

    # Demo for Step 1.3: DecisionRequest model + escalation hook
    requests = tower.run_dry(max_events=50, historical=True)

    # Save the DecisionRequests for later Gate / training work
    output_file = Path("current_run/escalated_decisions.jsonl")
    tower.run_and_save_decisions(output_file, max_events=50, historical=True)
