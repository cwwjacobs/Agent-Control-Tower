"""
Agent Control Tower - Parser Module

Responsible for normalizing raw Luminary events and hook payloads
into clean internal AgentEvent objects that the classifier can reason over.

This is the first layer of the control tower.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class AgentEvent:
    """Normalized internal representation of an agent action or event."""
    event_id: str
    run_id: str
    timestamp: str
    actor: str
    role: str
    action_type: str
    target: str
    summary: str
    evidence_source: str
    confidence: str = "inferred"
    operator_approved: bool = False
    affected_files: List[str] = field(default_factory=list)
    risk_indicators: List[str] = field(default_factory=list)
    raw_payload_path: Optional[str] = None
    notes: str = ""

    def is_high_risk(self) -> bool:
        return bool(self.risk_indicators)


class LuminaryEventParser:
    """
    Parses Luminary-style events (from events.jsonl or hook payloads)
    into AgentEvent objects.
    """

    HIGH_RISK_KEYWORDS = {
        "secret", "env", "credential", "token", "password", "key",
        "deploy", "production", "dns", "domain", "rm -rf", "git push --force",
        "permission", "chmod", "chown", "auth", "payment", "billing"
    }

    def parse_luminary_event(self, raw_event: Dict[str, Any], raw_payload_path: Optional[str] = None) -> AgentEvent:
        """Convert a raw Luminary event dict into an AgentEvent."""
        target = raw_event.get("target", "")
        action_type = raw_event.get("action_type", "")
        summary = raw_event.get("summary", "")

        risk_indicators = self._detect_risk_indicators(target, summary, action_type)

        return AgentEvent(
            event_id=raw_event["event_id"],
            run_id=raw_event["run_id"],
            timestamp=raw_event["timestamp"],
            actor=raw_event.get("actor", "unknown"),
            role=raw_event.get("role", "unassigned"),
            action_type=action_type,
            target=target,
            summary=summary,
            evidence_source=raw_event.get("evidence_source", "unknown"),
            confidence=raw_event.get("confidence", "inferred"),
            operator_approved=raw_event.get("operator_approved", False),
            affected_files=self._extract_affected_files(raw_event),
            risk_indicators=risk_indicators,
            raw_payload_path=raw_payload_path,
            notes=raw_event.get("notes", ""),
        )

    def _detect_risk_indicators(self, target: str, summary: str, action_type: str) -> List[str]:
        indicators = []
        combined = f"{target} {summary} {action_type}".lower()

        for keyword in self.HIGH_RISK_KEYWORDS:
            if keyword in combined:
                indicators.append(keyword)

        if "write" in action_type or "edit" in action_type:
            if any(x in target.lower() for x in ["secret", ".env", "config", "auth"]):
                indicators.append("sensitive_file_write")

        return list(set(indicators))

    def _extract_affected_files(self, raw_event: Dict[str, Any]) -> List[str]:
        # Placeholder - will be expanded when we parse hook payloads more deeply
        files = raw_event.get("affected_files", [])
        if isinstance(files, str):
            return [files]
        return files or []


# Convenience function for quick use
def parse_event(raw_event: Dict[str, Any], raw_payload_path: Optional[str] = None) -> AgentEvent:
    return LuminaryEventParser().parse_luminary_event(raw_event, raw_payload_path)
