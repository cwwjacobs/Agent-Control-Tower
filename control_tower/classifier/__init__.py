"""
Agent Control Tower - Classifier Module

Applies green / yellow / red risk classification to normalized AgentEvents.

This is the decision layer that determines whether an action can proceed
automatically, needs warning, or must be escalated to the human operator.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from ..parser import AgentEvent


class RiskLevel(str, Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


@dataclass
class ClassificationResult:
    risk_level: RiskLevel
    reason: str
    suggested_action: str
    requires_operator: bool
    auto_allow: bool


class RiskClassifier:
    """
    Core classification engine for the Agent Control Tower.

    Rules are intentionally conservative for the MVP.
    """

    # High-risk targets / patterns (RED)
    RED_TARGETS = {
        "secret", ".env", "credentials", "auth", "token", "password",
        "deploy", "production", "dns", "domain", ".pem", "id_rsa",
        "payment", "billing", "stripe", "api_key"
    }

    RED_ACTIONS = {
        "rm", "rm -rf", "git push --force", "git reset --hard",
        "chmod", "chown", "sudo", "production deploy", "domain change"
    }

    # Medium-risk (YELLOW)
    YELLOW_TARGETS = {
        "config", "requirements", "pyproject.toml", "package.json",
        "dockerfile", "compose", "settings", "pricing", "claims",
        "legal", "medical", "security"
    }

    YELLOW_ACTIONS = {
        "write", "edit", "apply_patch", "refactor", "dependency update",
        "broad change", "generated code"
    }

    def classify(self, event: AgentEvent) -> ClassificationResult:
        """Classify a single normalized event."""

        target_lower = event.target.lower()
        summary_lower = event.summary.lower()
        action_lower = event.action_type.lower()

        combined = f"{target_lower} {summary_lower} {action_lower}"

        # More precise command detection
        is_command_action = event.action_type in {"tool_call", "command_run", "user_instruction"}

        # === RED checks (highest priority) ===
        for keyword in self.RED_TARGETS:
            if keyword in target_lower or keyword in summary_lower:
                return ClassificationResult(
                    risk_level=RiskLevel.RED,
                    reason=f"Target or content contains high-risk keyword: '{keyword}'",
                    suggested_action="Pause and require explicit operator approval before proceeding.",
                    requires_operator=True,
                    auto_allow=False,
                )

        # Only treat RED_ACTIONS as dangerous if it's actually a command/action
        # For user_instruction, only flag if the *action_type* itself looks like a direct rm (rare), not if the summary narrative merely mentions "rm" or "cleanup"
        if is_command_action:
            for keyword in self.RED_ACTIONS:
                if keyword in action_lower:
                    return ClassificationResult(
                        risk_level=RiskLevel.RED,
                        reason=f"Action contains destructive or high-risk pattern: '{keyword}'",
                        suggested_action="Block or require strong operator confirmation.",
                        requires_operator=True,
                        auto_allow=False,
                    )
                # Only check summary for true execution contexts, not descriptive user_instructions
                if event.action_type in {"command_run", "tool_call"} and keyword in summary_lower:
                    return ClassificationResult(
                        risk_level=RiskLevel.RED,
                        reason=f"Action contains destructive or high-risk pattern: '{keyword}'",
                        suggested_action="Block or require strong operator confirmation.",
                        requires_operator=True,
                        auto_allow=False,
                    )

        # === YELLOW checks ===
        for keyword in self.YELLOW_TARGETS:
            if keyword in combined:
                return ClassificationResult(
                    risk_level=RiskLevel.YELLOW,
                    reason=f"Target touches configuration, dependency, or sensitive business area: '{keyword}'",
                    suggested_action="Allow with warning + log. Consider operator notification.",
                    requires_operator=False,
                    auto_allow=False,
                )

        for keyword in self.YELLOW_ACTIONS:
            if keyword in combined:
                return ClassificationResult(
                    risk_level=RiskLevel.YELLOW,
                    reason=f"Action type indicates meaningful change: '{keyword}'",
                    suggested_action="Allow with summary. Monitor for drift.",
                    requires_operator=False,
                    auto_allow=False,
                )

        # === GREEN (default safe) ===
        return ClassificationResult(
            risk_level=RiskLevel.GREEN,
            reason="Action appears low-risk based on current rules.",
            suggested_action="Auto-allow and log.",
            requires_operator=False,
            auto_allow=True,
        )


# Convenience function
def classify_event(event: AgentEvent) -> ClassificationResult:
    return RiskClassifier().classify(event)
