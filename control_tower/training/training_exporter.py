"""
Agent Control Tower - Training Data Exporter (Phase 4)

Defines a minimal, usable TrainingRow schema and a basic exporter
that turns OperatorDecision + Receipt context into training data.

Per the map (MVP_END_TO_END_ROADMAP.md Phase 4).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models import OperatorDecision


@dataclass
class TrainingRow:
    """
    A single training example derived from an operator decision.

    This is the canonical schema for Phase 4.
    """
    event_id: str
    request_id: str
    receipt_id: Optional[str]
    run_id: str
    action_type: str
    target: str
    original_summary: str
    risk_level: str
    classification_reason: str

    # The actual decision the operator made
    operator_decision: str          # approved | denied | modified
    operator_rationale: str
    corrected_action: Optional[str]

    # Derived / useful fields for training
    was_modified: bool
    decision_category: str          # e.g. "safety", "scope", "style", "other"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TrainingExporter:
    """
    Simple exporter that can turn existing Gate + Receipt artifacts
    into training JSONL.
    """

    def __init__(self):
        pass

    def create_row(
        self,
        decision: OperatorDecision,
        context: Dict[str, Any],
        receipt_id: Optional[str] = None,
        classification_reason: str = "",
        risk_level: str = "",
    ) -> TrainingRow:
        """Build a TrainingRow from a decision and its context."""
        return TrainingRow(
            event_id=context.get("event_id", ""),
            request_id=decision.request_id,
            receipt_id=receipt_id,
            run_id=context.get("run_id", ""),
            action_type=context.get("action_type", ""),
            target=context.get("target", ""),
            original_summary=context.get("summary", ""),
            risk_level=risk_level or context.get("risk_level", ""),
            classification_reason=classification_reason or context.get("classification_reason", ""),
            operator_decision=decision.decision,
            operator_rationale=decision.rationale,
            corrected_action=decision.corrected_action,
            was_modified=(decision.decision == "modified"),
            decision_category=self._infer_category(decision, context),
        )

    def _infer_category(self, decision: OperatorDecision, context: Dict[str, Any]) -> str:
        """Very lightweight heuristic for now. Can be improved later."""
        text = (decision.rationale or "").lower() + " " + (decision.corrected_action or "").lower()
        if any(word in text for word in ["secret", "env", "credential", "token", "password", "key"]):
            return "safety"
        if any(word in text for word in ["scope", "boundary", "hardening", "limit"]):
            return "scope"
        if any(word in text for word in ["style", "clarity", "readability", "comment"]):
            return "style"
        return "other"

    def export_to_jsonl(
        self,
        rows: List[TrainingRow],
        output_path: Path,
    ) -> Path:
        """Write training rows to JSONL."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row.to_dict()) + "\n")
        return output_path

    @staticmethod
    def load_rows(path: Path) -> List[TrainingRow]:
        """Load previously exported training rows."""
        rows = []
        if not path.exists():
            return rows
        for line in path.read_text(encoding="utf-8").strip().splitlines():
            if line:
                data = json.loads(line)
                rows.append(TrainingRow(**data))
        return rows
