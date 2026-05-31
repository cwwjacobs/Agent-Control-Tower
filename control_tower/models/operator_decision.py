"""
Agent Control Tower - OperatorDecision

This is the canonical record of a decision made by the Responsible Operator
on a DecisionRequest.

It is deliberately kept as a pure data object so that any frontend
(CLI, TUI, web UI, scripted handler, etc.) can produce it without
the core engine caring how the decision was collected.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class OperatorDecision:
    """Structured record of an operator's decision on a DecisionRequest."""
    request_id: str
    decision: str                  # "approved" | "denied" | "modified"
    rationale: str = ""
    corrected_action: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def is_approved(self) -> bool:
        return self.decision == "approved"

    def is_denied(self) -> bool:
        return self.decision == "denied"

    def is_modified(self) -> bool:
        return self.decision == "modified"
