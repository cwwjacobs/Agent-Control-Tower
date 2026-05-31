#!/usr/bin/env python3
"""Build a receipt JSON for a Luminary run from logged events."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from _luminary_common import (
    append_jsonl,
    ensure_layout,
    evidence_strength,
    load_jsonl,
    next_receipt_id,
    sha256_file,
    split_multi,
    utc_now,
)


INSPECT_ACTIONS = {"file_read", "read", "search", "tool_call", "tool_result"}
MODIFY_ACTIONS = {"file_edit", "edit", "trace_update"}
CHECK_ACTIONS = {"validation"}


def unique_preserve(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a Luminary I/O Archivist receipt for one run.")
    parser.add_argument("--project-root", default=".", help="Project root containing .luminary/.")
    parser.add_argument("--run-id", required=True, help="Run/session identifier to summarize.")
    parser.add_argument("--receipt-id", help="Optional explicit receipt id.")
    parser.add_argument("--remaining-risk", action="append", default=[], help="Remaining risk. Repeat or comma-separate.")
    parser.add_argument("--claim-boundary", default="Receipt summarizes logged events only; it does not prove full system correctness.")
    parser.add_argument("--recommended-next-action", default="Review unsupported claims and add validation events where needed.")
    parser.add_argument("--write-receipt-event", action="store_true", help="Also append an action_type=receipt event to events.jsonl.")
    parser.add_argument("--json", action="store_true", help="Print receipt JSON to stdout.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    paths = ensure_layout(project_root)
    all_events = load_jsonl(paths["events_file"])
    run_events = [event for event in all_events if event.get("run_id") == args.run_id]

    now = utc_now()
    receipt_id = args.receipt_id or next_receipt_id(paths["receipts_dir"], args.run_id, now)

    files_inspected = unique_preserve([
        e.get("target", "") for e in run_events
        if e.get("action_type") in INSPECT_ACTIONS and e.get("target")
    ])
    files_modified = unique_preserve([
        e.get("target", "") for e in run_events
        if e.get("action_type") in MODIFY_ACTIONS and e.get("target")
    ])
    checks_performed = [
        {
            "event_id": e.get("event_id"),
            "target": e.get("target"),
            "summary": e.get("summary"),
            "output_ref": e.get("output_ref"),
        }
        for e in run_events if e.get("action_type") in CHECK_ACTIONS
    ]

    claims = unique_preserve([claim for e in run_events for claim in e.get("claim_links", [])])
    traces = unique_preserve([trace for e in run_events for trace in e.get("trace_links", [])])

    strength_counts: Dict[str, int] = {}
    for event in run_events:
        strength = evidence_strength(event)
        strength_counts[strength] = strength_counts.get(strength, 0) + 1

    receipt: Dict[str, Any] = {
        "receipt_id": receipt_id,
        "run_id": args.run_id,
        "date": now,
        "files_inspected": files_inspected,
        "files_modified": files_modified,
        "events_logged": len(run_events),
        "event_ids": [e.get("event_id") for e in run_events],
        "claims_supported": claims,
        "traces_linked": traces,
        "checks_performed": checks_performed,
        "evidence_strength_counts": strength_counts,
        "remaining_risks": split_multi(args.remaining_risk),
        "claim_boundary": args.claim_boundary,
        "recommended_next_action": args.recommended_next_action,
    }

    output_path = paths["receipts_dir"] / f"{receipt_id}.json"
    output_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

    if args.write_receipt_event:
        event = {
            "event_id": None,  # filled below
            "run_id": args.run_id,
            "timestamp": now,
            "actor": "luminary_build_receipt.py",
            "role": "receipt-builder",
            "action_type": "receipt",
            "target": str(output_path.relative_to(project_root)),
            "summary": f"Built receipt {receipt_id} from {len(run_events)} logged events.",
            "evidence_source": "receipt",
            "input_ref": paths["events_file"].as_posix(),
            "output_ref": str(output_path.relative_to(project_root)),
            "before_hash": None,
            "after_hash": sha256_file(output_path),
            "claim_links": claims,
            "trace_links": traces,
            "confidence": "derived",
            "operator_approved": False,
            "notes": args.claim_boundary,
        }
        from _luminary_common import next_event_id
        event["event_id"] = next_event_id(all_events, now)
        append_jsonl(paths["events_file"], event)

    if args.json:
        print(json.dumps(receipt, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(f"wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
