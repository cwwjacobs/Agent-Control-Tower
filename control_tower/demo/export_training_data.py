#!/usr/bin/env python3
"""
Demo: Export real training data from existing Gate decisions + receipts.

This demonstrates Step 4.1 (Phase 4 per the map):
- Uses the defined TrainingRow schema.
- Produces actual usable JSONL training examples.

Usage:
    python -m control_tower.demo.export_training_data
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from control_tower.gate.gate import OperatorDecision
from control_tower.training import TrainingExporter


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
    ctx_map: Dict[str, Dict[str, Any]] = {}
    if not path.exists():
        return ctx_map
    for line in path.read_text(encoding="utf-8").strip().splitlines():
        if not line:
            continue
        d = json.loads(line)
        req_id = d.get("request_id")
        if req_id:
            ctx_map[req_id] = {
                "event_id": d.get("event_id", ""),
                "request_id": req_id,
                "run_id": d.get("run_id", ""),
                "action_type": d.get("action_type", ""),
                "target": d.get("target", ""),
                "summary": d.get("summary", ""),
                "risk_level": d.get("risk_level", ""),
                "classification_reason": d.get("escalation_reason", ""),
            }
    return ctx_map


def load_receipt_map(receipts_dir: Path) -> Dict[str, str]:
    """Map request_id -> receipt_id from the manifest."""
    mapping: Dict[str, str] = {}
    manifest = receipts_dir / "receipts_manifest.jsonl"
    if not manifest.exists():
        return mapping
    for line in manifest.read_text(encoding="utf-8").strip().splitlines():
        if line:
            e = json.loads(line)
            mapping[e["request_id"]] = e["receipt_id"]
    return mapping


def main():
    base = Path("/home/orz/Desktop/agent_control_tower_build_pack")
    decisions_path = base / "current_run" / "operator_decisions.jsonl"
    context_path = base / "current_run" / "escalated_decisions.jsonl"
    receipts_dir = base / "current_run" / "receipts"
    output_path = base / "current_run" / "training_data.jsonl"

    decisions = load_operator_decisions(decisions_path)
    context_map = load_context_map(context_path)
    receipt_map = load_receipt_map(receipts_dir)

    if not decisions:
        print("[Training Export] No operator decisions found. Generate some first.")
        return

    print(f"[Training Export] Loaded {len(decisions)} decisions and context for {len(context_map)} requests.")

    exporter = TrainingExporter()
    rows = []
    for decision in decisions:
        ctx = context_map.get(decision.request_id, {})
        receipt_id = receipt_map.get(decision.request_id)
        row = exporter.create_row(
            decision=decision,
            context=ctx,
            receipt_id=receipt_id,
            risk_level=ctx.get("risk_level", ""),
            classification_reason=ctx.get("classification_reason", ""),
        )
        rows.append(row)

    exporter.export_to_jsonl(rows, output_path)

    print(f"\n[Training Export] Exported {len(rows)} training rows to {output_path}")
    print("\n=== Sample Training Row (first one) ===")
    print(json.dumps(rows[0].to_dict(), indent=2))


if __name__ == "__main__":
    main()
