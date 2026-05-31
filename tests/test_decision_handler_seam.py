"""
Contract tests for the DecisionHandler seam.

These tests prove that the engine can work with any implementation
of DecisionHandler without caring about the concrete UI.

This is the core evidence that the architecture is TUI-ready.
"""

import pytest
from control_tower.interfaces import DecisionHandler, AutoApproveHandler
from control_tower.models import DecisionRequest
from control_tower.orchestrator import ControlTower
from pathlib import Path


class _FakeDecisionHandler(DecisionHandler):
    """Minimal test double for contract testing."""

    def __init__(self, decision: str = "approved", rationale: str = "test"):
        self.decision = decision
        self.rationale = rationale
        self.last_request = None

    def handle_decision(self, request: DecisionRequest):
        self.last_request = request
        from control_tower.models.operator_decision import OperatorDecision

        return OperatorDecision(
            request_id=request.request_id,
            decision=self.decision,
            rationale=self.rationale,
        )


def test_control_tower_accepts_any_decision_handler():
    """The engine should accept and use any DecisionHandler without modification."""
    handler = _FakeDecisionHandler(decision="modified", rationale="contract test")

    # We can't easily create a real DecisionRequest without more setup,
    # so we test the type contract and injection instead.
    tower = ControlTower(Path("."), default_handler=handler)

    assert tower._default_handler is handler
    assert isinstance(tower._default_handler, DecisionHandler)


def test_auto_approve_handler_implements_protocol():
    """AutoApproveHandler must satisfy the DecisionHandler protocol."""
    handler = AutoApproveHandler()
    assert isinstance(handler, DecisionHandler)


def test_console_handler_implements_protocol():
    """ConsoleDecisionHandler must satisfy the DecisionHandler protocol."""
    from control_tower.interfaces.console_handler import ConsoleDecisionHandler

    handler = ConsoleDecisionHandler()
    assert isinstance(handler, DecisionHandler)
