"""
Agent Control Tower - Minimal CLI Gate (Step 2.1)

This is the first interactive layer of the Cockpit.
It consumes DecisionRequest objects produced by the spine and lets the
Responsible Operator make real Approve / Deny / Modify decisions.

Scope for this step: Pure CLI interaction + structured decision capture.
No receipts, no real agent control, no training export yet.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from ..models import DecisionRequest, OperatorDecision
from ..interfaces.decision_handler import DecisionHandler
from ..interfaces.console_handler import ConsoleDecisionHandler


# OperatorDecision now lives in models/ for clean separation.
# We re-export it here for backward compatibility during the transition.
from ..models import OperatorDecision  # noqa: F401


class Gate(DecisionHandler):
    """
    The original console-based DecisionHandler.

    This class implements the DecisionHandler protocol for the classic
    terminal experience. It is *one* possible implementation.

    The engine (ControlTower, etc.) should never import or depend on this
    class directly if you want to keep the ability to swap interfaces.
    """

    def __init__(self):
        self.decisions: List[OperatorDecision] = []
        self._handler = ConsoleDecisionHandler()  # The real adapter

    def handle_decision(self, request: DecisionRequest) -> OperatorDecision:
        """DecisionHandler protocol implementation (delegates to console adapter)."""
        return self._handler.handle_decision(request)

    def process_requests(self, requests: List[DecisionRequest]) -> List[OperatorDecision]:
        """
        Process a batch of DecisionRequests using the console adapter.
        Kept for backward compatibility with existing code paths.
        """
        results = []
        for req in requests:
            decision = self.handle_decision(req)
            results.append(decision)
            self.decisions.append(decision)
        return results

    def get_session_summary(self) -> dict:
        """Returns counts for the terminal notification / summary."""
        approved = sum(1 for d in self.decisions if d.is_approved())
        denied = sum(1 for d in self.decisions if d.is_denied())
        modified = sum(1 for d in self.decisions if d.is_modified())
        return {
            "total": len(self.decisions),
            "approved": approved,
            "denied": denied,
            "modified": modified,
        }

    def save_decisions(self, output_path: Path) -> None:
        """Persist all OperatorDecision objects to JSONL. This makes them durable for receipts/training."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for d in self.decisions:
                record = {
                    "request_id": d.request_id,
                    "decision": d.decision,
                    "rationale": d.rationale,
                    "corrected_action": d.corrected_action,
                    "timestamp": d.timestamp,
                }
                f.write(json.dumps(record) + "\n")
        print(f"[Gate] Saved {len(self.decisions)} operator decisions to {output_path}")


def run_cli_gate(
    requests: List[DecisionRequest],
    auto_save_path: Optional[Path] = None,
) -> List[OperatorDecision]:
    """
    Convenience function for the current console-based decision experience.

    This is one concrete implementation of the DecisionHandler seam.
    In the future, other handlers (TUI, web, scripted, etc.) can be used
    in the same places without changing the engine.
    """
    if not requests:
        print("[Gate] No DecisionRequests to process.")
        return []

    handler = ConsoleDecisionHandler()
    print(f"\n[Gate] Starting CLI Gate. {len(requests)} request(s) waiting for your decision.")

    decisions: list[OperatorDecision] = []
    for req in requests:
        decision = handler.handle_decision(req)
        decisions.append(decision)

    # Build summary using a temporary Gate instance for the helper methods
    # (this is transitional until we fully move summary logic)
    temp_gate = Gate()
    temp_gate.decisions = decisions
    summary = temp_gate.get_session_summary()

    print("\n" + "=" * 50)
    print("  GATE SESSION COMPLETE — OPERATOR DECISIONS")
    print("=" * 50)
    print(f"Total decisions : {summary['total']}")
    print(f"  Approved      : {summary['approved']}")
    print(f"  Denied        : {summary['denied']}")
    print(f"  Modified      : {summary['modified']}")
    print("=" * 50)

    if auto_save_path:
        temp_gate.save_decisions(auto_save_path)

    return decisions
