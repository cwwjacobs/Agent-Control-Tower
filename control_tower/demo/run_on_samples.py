#!/usr/bin/env python3
"""
Quick demo: Load real Luminary sample events and run them through
the current Parser + Classifier.

This is early scaffolding for the Agent Control Tower.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any

# Add parent to path so we can import the package
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from control_tower.parser import parse_event, AgentEvent
from control_tower.classifier import classify_event, RiskLevel


def load_sample_events(root: Path, limit: int = 30) -> List[Dict[str, Any]]:
    """Load events from a .luminary/events/events.jsonl if it exists."""
    events_file = root / "events" / "events.jsonl"
    if not events_file.exists():
        print(f"No events.jsonl found at {events_file}")
        return []

    events: List[Dict[str, Any]] = []
    with open(events_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
                if len(events) >= limit:
                    break
            except json.JSONDecodeError:
                continue
    return events


def main():
    # Try the strongest sample location first
    candidates = [
        Path("source_extract/CANONICAL/luminary-agent-ledger-v0.1.0/.luminary"),
        Path("source_extract/.luminary"),
    ]

    sample_root = None
    for cand in candidates:
        if (cand / "events" / "events.jsonl").exists():
            sample_root = cand
            break

    if sample_root is None:
        print("No sample events.jsonl found in expected locations.")
        print("Tried:")
        for c in candidates:
            print(f"  - {c}")
        return

    print(f"Loading samples from: {sample_root}")
    raw_events = load_sample_events(sample_root, limit=50)

    if not raw_events:
        print("No events loaded.")
        return

    print(f"Loaded {len(raw_events)} events.\n")

    green = 0
    yellow = 0
    red = 0

    for raw in raw_events:
        event: AgentEvent = parse_event(raw)
        result = classify_event(event)

        if result.risk_level == RiskLevel.GREEN:
            green += 1
        elif result.risk_level == RiskLevel.YELLOW:
            yellow += 1
        else:
            red += 1

        # Print interesting ones
        if result.risk_level != RiskLevel.GREEN:
            print(f"[{result.risk_level.upper()}] {event.action_type:20} | {event.target[:70]}")
            print(f"    Reason: {result.reason}")
            print(f"    Suggested: {result.suggested_action}\n")

    print("=== Summary ===")
    print(f"GREEN : {green}")
    print(f"YELLOW: {yellow}")
    print(f"RED   : {red}")
    print(f"Total : {len(raw_events)}")


if __name__ == "__main__":
    main()
