"""
Minimal, stable models for the Operator Interface seam.

These are the contracts that any frontend (Console, TUI, Web, etc.)
must be able to produce and consume.

The goal is to keep the engine independent of how decisions are
collected and how information is displayed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional


# -----------------------------------------------------------------------------
# Operator Input Model
# What a frontend returns when the operator makes a decision.
# -----------------------------------------------------------------------------

DecisionType = Literal["approved", "denied", "modified"]


@dataclass(frozen=True)
class OperatorInput:
    """
    The minimal information a frontend must collect from the operator
    when handling a DecisionRequest.

    This is what gets turned into an OperatorDecision by the adapter layer.
    """
    decision: DecisionType
    rationale: str = ""
    corrected_action: Optional[str] = None

    def to_operator_decision(self, request_id: str) -> "OperatorDecision":
        """Convenience to turn this input into the canonical OperatorDecision."""
        from ..models.operator_decision import OperatorDecision

        return OperatorDecision(
            request_id=request_id,
            decision=self.decision,
            rationale=self.rationale,
            corrected_action=self.corrected_action,
        )


# -----------------------------------------------------------------------------
# Display Output Model
# Rich, structured data a frontend can use to present a DecisionRequest.
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class DecisionPresentation:
    """
    A frontend-agnostic, rich representation of a DecisionRequest
    suitable for display in CLI, TUI, or web interfaces.

    This is what the engine (or an adapter) provides to any UI layer.
    """
    request_id: str
    timestamp: str
    run_id: str
    actor: str
    role: str
    action_type: str
    target: str
    summary: str
    escalation_reason: str
    risk_level: str
    suggested_action: str
    requires_operator: bool
    affected_files: list[str]
    risk_indicators: list[str]
    operator_context: dict

    @classmethod
    def from_decision_request(cls, request) -> "DecisionPresentation":
        """Factory to create a presentation object from a DecisionRequest."""
        event = request.event
        classification = request.classification

        return cls(
            request_id=request.request_id,
            timestamp=request.timestamp,
            run_id=event.run_id,
            actor=event.actor,
            role=event.role,
            action_type=event.action_type,
            target=event.target,
            summary=event.summary,
            escalation_reason=request.escalation_reason,
            risk_level=classification.risk_level.value,
            suggested_action=classification.suggested_action,
            requires_operator=classification.requires_operator,
            affected_files=event.affected_files or [],
            risk_indicators=event.risk_indicators or [],
            operator_context=request.operator_context,
        )
