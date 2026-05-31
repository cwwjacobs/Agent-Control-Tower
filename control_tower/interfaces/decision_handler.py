"""
Agent Control Tower - DecisionHandler Protocol

This is the key seam the user (Responsible Operator) asked for.

Any frontend — current CLI Gate, future proper TUI, web UI, scripted handler,
or even a completely different system — can implement this protocol.

The core engine (ControlTower, etc.) should only ever depend on this interface,
never on a specific console implementation.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..models.decision_request import DecisionRequest
from ..models.operator_decision import OperatorDecision


@runtime_checkable
class DecisionHandler(Protocol):
    """
    The primary architectural seam for all human-in-the-loop decision making.

    This is the contract the engine speaks to. Everything on the "engine" side
    (ControlTower, future orchestration, receipts, training data, etc.)
    should only ever depend on this interface — never on any specific
    presentation layer.

    This exists specifically so that the Responsible Operator can use
    whatever interface they actually prefer (CLI for others, a proper TUI
    for themselves, web UI later, etc.) without the core having to change.
    """

    def handle_decision(self, request: DecisionRequest) -> OperatorDecision:
        """
        Present the given DecisionRequest to the operator (in whatever form
        the implementation chooses) and return their decision.

        Implementations are expected to:
        - Richly present the request (summary, risk, targets, context, etc.)
        - Collect Approve / Deny / Modify + rationale
        - Return a clean OperatorDecision

        The engine does not care if this is done via print/input, a full TUI
        framework (Textual, etc.), a web interface, or anything else.
        """
        ...
