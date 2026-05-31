#!/usr/bin/env python3
"""
Demo: Generate real receipts from previously saved Gate output (OperatorDecision + DecisionRequest context).

This demonstrates Step 3.2 (per the map):
- Receipts are explicitly linked back to original events via a queryable manifest.
- You can ask "which receipts belong to this original event_id?"

Usage:
    python -m control_tower.demo.generate_receipts_from_gate
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from control_tower.gate.gate import OperatorDecision
from control_tower.receipts import ReceiptWriter


def load_operator_decisions(path: Path) -> list[OperatorDecision]:
    decisions = []
    if not path.exists():
        return decisions
    for line in path.read_text(encoding="utf-8").strip().splitlines():
        if not line:
            continue
        d = json.loads(line)
        decisions.append(OperatorDecision(
            request_id=d["request_id"],
            decision=d["decision"],
            rationale=d.get("rationale", ""),
            corrected_action=d.get("corrected_action"),
            timestamp=d.get("timestamp", ""),
        ))
    return decisions


def load_context_map(path: Path) -> Dict[str, Dict[str, Any]]:
    """Build context map keyed by request_id from the original DecisionRequest/ event data."""
    context_map: Dict[str, Dict[str, Any]] = {}
    if not path.exists():
        return context_map
    for line in path.read_text(encoding="utf-8").strip().splitlines():
        if not line:
            continue
        d = json.loads(line)
        request_id = d.get("request_id")
        if request_id:
            context_map[request_id] = {
                "request_id": request_id,
                "event_id": d.get("event_id", ""),
                "run_id": d.get("run_id", ""),
                "action_type": d.get("action_type", ""),
                "target": d.get("target", ""),
                "summary": d.get("summary", ""),
            }
    return context_map


def main():
    base = Path("/home/orz/Desktop/agent_control_tower_build_pack")

    decisions_path = base / "current_run" / "operator_decisions.jsonl"
    context_path = base / "current_run" / "escalated_decisions.jsonl"
    output_dir = base / "current_run" / "receipts"

    decisions = load_operator_decisions(decisions_path)
    context_map = load_context_map(context_path)

    if not decisions:
        print("[Receipts Demo] No operator decisions found. Run the Gate demo first.")
        return

    print(f"[Receipts Demo] Loaded {len(decisions)} operator decisions.")
    print(f"[Receipts Demo] Context available for {len(context_map)} requests.")

    writer = ReceiptWriter()
    written_paths = writer.write_receipts_batch(decisions, context_map, output_dir)

    print(f"\n[Receipts Demo] Generated {len(written_paths)} receipts in {output_dir}")
    for p in written_paths:
        print(f"  - {p.name}")

    # Demonstrate linkage via manifest (the key part of Step 3.2)
    manifest = ReceiptWriter.load_manifest(output_dir)
    print(f"\n[Receipts Demo] Manifest now contains {len(manifest)} linkage entries.")

    if manifest:
        sample_event_id = manifest[0]["event_id"]
        linked = ReceiptWriter.find_receipts_for_event(sample_event_id, output_dir)
        print(f"[Receipts Demo] Linkage query for event_id {sample_event_id}: {len(linked)} receipt(s) found")
        print(json.dumps(linked, indent=2))

    # Show one example receipt
    if written_paths:
        example = json.loads(written_paths[0].read_text(encoding="utf-8"))
        print("\n=== Example Receipt (first one) ===")
        print(json.dumps(example, indent=2))


if __name__ == "__main__":
    main()
