"""
ConsoleDecisionHandler

The current terminal-based implementation of DecisionHandler.

This is the "first adapter" — it keeps the existing console experience working
while the engine no longer owns console-specific behavior.
"""

from __future__ import annotations

from ..models.decision_request import DecisionRequest
from ..models.operator_decision import OperatorDecision
from .decision_handler import DecisionHandler
from .models import DecisionPresentation, OperatorInput


class ConsoleDecisionHandler(DecisionHandler):
    """
    Interactive console implementation of DecisionHandler.

    This adapter is responsible for:
    - Displaying a DecisionRequest to the terminal
    - Collecting operator input via stdin
    - Returning a clean OperatorDecision

    The engine (ControlTower) only ever sees the DecisionHandler interface.
    """

    def handle_decision(self, request: DecisionRequest) -> OperatorDecision:
        presentation = DecisionPresentation.from_decision_request(request)
        self._display(presentation)

        while True:
            choice = input("\nYour decision [A]pprove / [D]eny / [M]odify: ").strip().lower()

            if choice in ("a", "approve"):
                rationale = input("Optional rationale (press Enter to skip): ").strip()
                operator_input = OperatorInput(decision="approved", rationale=rationale)
                return operator_input.to_operator_decision(request.request_id)

            elif choice in ("d", "deny"):
                rationale = input("Reason for denial (recommended): ").strip()
                operator_input = OperatorInput(decision="denied", rationale=rationale)
                return operator_input.to_operator_decision(request.request_id)

            elif choice in ("m", "modify"):
                print("Enter the corrected instruction / action the agent should take instead:")
                corrected = input("> ").strip()
                rationale = input("Optional note about the modification: ").strip()
                operator_input = OperatorInput(
                    decision="modified",
                    rationale=rationale,
                    corrected_action=corrected,
                )
                return operator_input.to_operator_decision(request.request_id)

            else:
                print("Please enter A, D, or M.")

    def _display(self, presentation: DecisionPresentation) -> None:
        """Render the decision using the shared display layer."""
        from ..display.decision_request import decision_request_to_console_lines

        # Reconstruct a minimal DecisionRequest-like object for the helper
        # (this is temporary until we fully migrate display usage)
        class _FakeEvent:
            def __init__(self, p):
                self.action_type = p.action_type
                self.target = p.target
                self.summary = p.summary
                self.affected_files = p.affected_files

        class _FakeClassification:
            def __init__(self, p):
                self.risk_level = type("rl", (), {"value": p.risk_level})()
                self.suggested_action = p.suggested_action

        class _FakeRequest:
            def __init__(self, p):
                self.request_id = p.request_id
                self.event = _FakeEvent(p)
                self.classification = _FakeClassification(p)
                self.escalation_reason = p.escalation_reason

        fake_req = _FakeRequest(presentation)
        for line in decision_request_to_console_lines(fake_req):
            print(line)
