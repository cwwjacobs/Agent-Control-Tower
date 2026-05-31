"""
Shared display helpers for DecisionRequest.

These functions produce structured data (or rich text) that can be used
by different frontends:

- The current console Gate
- A future proper TUI (Textual, etc.)
- Web UI
- Logging / audit output

The goal is to keep presentation concerns out of the engine and out of
the decision logic itself.
"""

from __future__ import annotations

from typing import Any, Dict

from ..models.decision_request import DecisionRequest


def decision_request_to_dict(request: DecisionRequest) -> Dict[str, Any]:
    """
    Convert a DecisionRequest into a plain dictionary suitable for
    rich rendering in a TUI, web UI, or logging.
    """
    return {
        "request_id": request.request_id,
        "timestamp": request.timestamp,
        "run_id": request.event.run_id,
        "actor": request.event.actor,
        "role": request.event.role,
        "action_type": request.event.action_type,
        "target": request.event.target,
        "summary": request.event.summary,
        "escalation_reason": request.escalation_reason,
        "risk_level": request.classification.risk_level.value,
        "suggested_action": request.classification.suggested_action,
        "requires_operator": request.classification.requires_operator,
        "affected_files": request.event.affected_files,
        "risk_indicators": request.event.risk_indicators,
        "operator_context": request.operator_context,
        "status": request.status,
    }


def decision_request_to_console_lines(request: DecisionRequest) -> list[str]:
    """
    Legacy-style plain text lines for the current console Gate.
    This is what the old _display_request was doing.
    """
    lines = []
    lines.append("=" * 70)
    lines.append(f"  DECISION REQUEST  |  {request.request_id}")
    lines.append("=" * 70)
    lines.append(f"Risk Level : {request.classification.risk_level.value.upper()}")
    lines.append(f"Action     : {request.event.action_type} → {request.event.target}")
    lines.append(f"Summary    : {request.event.summary}")
    lines.append(f"Reason     : {request.escalation_reason}")
    lines.append(f"Suggested  : {request.classification.suggested_action}")
    if request.event.affected_files:
        lines.append(f"Affected   : {', '.join(request.event.affected_files)}")
    lines.append("-" * 70)
    return lines
