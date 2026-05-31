#!/usr/bin/env python3
"""
Demo: Load real DecisionRequests (produced by the spine) and run them through the Gate.

This demonstrates Step 2.2:
- Full interactive Approve/Deny/Modify
- End-of-session summary / terminal notification
- Automatic persistence of OperatorDecision objects to disk

Usage:
    python -m control_tower.demo.run_gate_on_samples

For non-interactive testing (shows what the Gate would present):
    python -m control_tower.demo.run_gate_on_samples --dry
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

# Make the package importable when run directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from control_tower.models import DecisionRequest
from control_tower.gate import run_cli_gate
from control_tower.models import OperatorDecision


def load_decision_requests(path: Path) -> List[DecisionRequest]:
    """Load DecisionRequests from the JSONL file saved by the orchestrator."""
    if not path.exists():
        print(f"[Demo] No file found at {path}")
        return []

    requests: List[DecisionRequest] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)

            # Reconstruct a minimal AgentEvent-like object for display
            # (we only need the fields the Gate shows)
            class MinimalEvent:
                def __init__(self, d):
                    self.event_id = d.get("event_id", "")
                    self.run_id = d.get("run_id", "")
                    self.action_type = d.get("action_type", "")
                    self.target = d.get("target", "")
                    self.summary = d.get("summary", "")
                    self.affected_files = []

            class MinimalClassification:
                def __init__(self, d):
                    self.risk_level = type("RL", (), {"value": d.get("risk_level", "yellow")})()
                    self.reason = d.get("escalation_reason", "")
                    self.suggested_action = d.get("suggested_action", "")

            # Build a lightweight DecisionRequest for the Gate demo
            req = DecisionRequest(
                request_id=data.get("request_id", "unknown"),
                timestamp=data.get("timestamp", ""),
                event=MinimalEvent(data),  # type: ignore
                classification=MinimalClassification(data),  # type: ignore
                escalation_reason=data.get("escalation_reason", ""),
                operator_context={},
                status=data.get("status", "escalated"),
            )
            requests.append(req)

    return requests


def main():
    parser = argparse.ArgumentParser(description="Run the Control Tower Gate on real spine output.")
    parser.add_argument("--dry", action="store_true", help="Non-interactive mode: only show what the Gate would present")
    parser.add_argument("--file", type=str, default="current_run/escalated_decisions.jsonl",
                        help="Path to DecisionRequests JSONL (default: current_run/escalated_decisions.jsonl)")
    args = parser.parse_args()

    requests = load_decision_requests(Path(args.file))

    if not requests:
        print("[Demo] No DecisionRequests loaded. Run the orchestrator first to generate some.")
        return

    print(f"[Demo] Loaded {len(requests)} DecisionRequest(s) from {args.file}")

    if args.dry:
        print("\n[Demo] DRY MODE — Gate would present the following:\n")
        for req in requests:
            print(f"  - {req.to_summary()}")
        print("\n[Demo] In real use, run without --dry for interactive Approve/Deny/Modify.")
        return

    # Real interactive path with persistence + session notification (Step 2.2)
    output_path = Path("current_run/operator_decisions.jsonl")
    decisions: List[OperatorDecision] = run_cli_gate(requests, auto_save_path=output_path)

    print("\n=== Operator Decisions Recorded (in memory) ===")
    for d in decisions:
        print(f"  {d.request_id}: {d.decision.upper()}")
        if d.rationale:
            print(f"    Rationale: {d.rationale}")
        if d.corrected_action:
            print(f"    Corrected: {d.corrected_action}")


if __name__ == "__main__":
    main()
