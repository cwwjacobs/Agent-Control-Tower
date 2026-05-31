"""
Agent Control Tower - Interfaces (Seams)

These are the clean contracts between the engine and any frontend.

Currently:
- DecisionHandler: the seam for turning DecisionRequests into OperatorDecisions.
- TUIHandler: placeholder showing intent for a proper TUI.

The display/ package provides shared rich presentation data that any
frontend (CLI or TUI) can consume.
"""

from .decision_handler import DecisionHandler
from .example_handlers import AutoApproveHandler, ConsoleDecisionHandler
from .models import DecisionPresentation, OperatorInput
from .tui import TUIHandler

__all__ = [
    "DecisionHandler",
    "AutoApproveHandler",
    "ConsoleDecisionHandler",
    "TUIHandler",
    "DecisionPresentation",
    "OperatorInput",
]
