"""
Agent Control Tower - DecisionRequest Model

This is the canonical internal type for any action that requires (or may require)
human operator attention.

It is the central "decision currency" that flows from the spine to the Gate,
receipts, training export, and audit layers.

Step: 1.3 – Basic Decision Request Model + Simple Escalation Hook
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from ..parser import AgentEvent
from ..classifier import ClassificationResult, RiskLevel


@dataclass
class DecisionRequest:
    """
    A formal, auditable request for an operator decision.

    This object is produced by the Orchestrator whenever the Classifier
    determines an event is not GREEN (or in future, for any policy that
    requires human oversight).
    """

    request_id: str
    timestamp: str
    event: AgentEvent
    classification: ClassificationResult

    escalation_reason: str
    operator_context: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending | approved | denied | modified | auto_resolved

    # Future extension points (kept minimal for Step 1.3)
    suggested_resolution: Optional[str] = None
    operator_notes: str = ""

    @classmethod
    def from_event_and_classification(
        cls,
        event: AgentEvent,
        classification: ClassificationResult,
        escalation_reason: Optional[str] = None,
    ) -> DecisionRequest:
        """Factory for the common case: turning a classified non-GREEN event into a DecisionRequest."""
        if escalation_reason is None:
            escalation_reason = classification.reason

        now = datetime.now(timezone.utc).isoformat()

        # Build a compact but useful operator_context for the future Gate
        operator_context = {
            "run_id": event.run_id,
            "actor": event.actor,
            "role": event.role,
            "action_type": event.action_type,
            "target": event.target,
            "summary": event.summary,
            "risk_level": classification.risk_level.value,
            "requires_operator": classification.requires_operator,
            "suggested_action": classification.suggested_action,
            "affected_files": event.affected_files,
            "risk_indicators": event.risk_indicators,
        }

        return cls(
            request_id=f"DR-{uuid4().hex[:12]}",
            timestamp=now,
            event=event,
            classification=classification,
            escalation_reason=escalation_reason,
            operator_context=operator_context,
            status="pending",
            suggested_resolution=classification.suggested_action,
        )

    def is_red(self) -> bool:
        return self.classification.risk_level == RiskLevel.RED

    def is_yellow(self) -> bool:
        return self.classification.risk_level == RiskLevel.YELLOW

    def to_summary(self) -> str:
        """Human-readable one-liner for logs and early Gate displays."""
        return (
            f"[{self.classification.risk_level.value.upper()}] "
            f"{self.event.action_type} → {self.event.target} | "
            f"{self.escalation_reason}"
        )


# Convenience re-export
__all__ = ["DecisionRequest"]
