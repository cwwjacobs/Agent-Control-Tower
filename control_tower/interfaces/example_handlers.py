"""
Example implementations of DecisionHandler.

These demonstrate how easy it is to plug in different behaviors
once the seam exists.
"""

from __future__ import annotations

from ..models.decision_request import DecisionRequest
from ..models.operator_decision import OperatorDecision


class AutoApproveHandler:
    """
    A trivial DecisionHandler that always approves.

    Useful for testing, dry-runs, or scripted flows where you want
    the engine to proceed without human input.
    """

    def handle_decision(self, request: DecisionRequest) -> OperatorDecision:
        return OperatorDecision(
            request_id=request.request_id,
            decision="approved",
            rationale="Auto-approved by AutoApproveHandler (for testing / scripted runs)",
        )


class ConsoleDecisionHandler:
    """
    Wrapper around the original interactive console experience.

    This exists so that code can depend on DecisionHandler instead of
    the concrete Gate class.
    """

    def __init__(self):
        from ..gate.gate import Gate
        self._gate = Gate()

    def handle_decision(self, request: DecisionRequest) -> OperatorDecision:
        return self._gate.handle_decision(request)
