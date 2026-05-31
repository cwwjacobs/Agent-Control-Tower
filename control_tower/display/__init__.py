"""
Agent Control Tower - Display Layer

Shared utilities for presenting DecisionRequests and related data.

Intended to be used by any frontend (current CLI, future TUI, web, etc.)
so that rich presentation logic isn't duplicated or buried inside
decision handling code.
"""

from .decision_request import (
    decision_request_to_dict,
    decision_request_to_console_lines,
)

__all__ = [
    "decision_request_to_dict",
    "decision_request_to_console_lines",
]
