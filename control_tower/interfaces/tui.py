"""
Agent Control Tower - TUI Layer (Planned / Future)

This module is a placeholder for proper TUI (Textual, Rich, etc.) support.

The goal is that a real TUI can implement DecisionHandler cleanly,
without the engine ever knowing it is talking to a TUI instead of
the old console Gate.

This file exists because the Responsible Operator has expressed that
they intend to primarily use a TUI, not the basic CLI.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .decision_handler import DecisionHandler


class TUIHandler:
    """
    Placeholder for a future proper TUI implementation of DecisionHandler.

    When implemented (e.g. with Textual), this class will:
    - Provide rich, interactive display of DecisionRequests
    - Support keyboard-driven Approve / Deny / Modify flows
    - Offer better context, history, diff views, etc.
    - Still return plain OperatorDecision objects

    The engine (ControlTower, etc.) will be able to use this the same way
    it uses the current console Gate — by receiving a DecisionHandler.
    """

    def handle_decision(self, request):
        # This is intentionally not implemented yet.
        # It exists as an architectural marker and future seam.
        raise NotImplementedError(
            "TUIHandler is a planned interface. "
            "The DecisionHandler protocol is ready for a real TUI implementation."
        )
