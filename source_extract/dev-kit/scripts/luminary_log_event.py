#!/usr/bin/env python3
"""Append one structured event to .luminary/events/events.jsonl."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from _luminary_common import (
    ACTION_TYPES,
    CONFIDENCE_LEVELS,
    EVIDENCE_SOURCES,
    append_jsonl,
    ensure_layout,
    load_jsonl,
    next_event_id,
    sha256_file,
    split_multi,
    utc_now,
)


def infer_confidence(evidence_source: str) -> str:
    if evidence_source in {"user_message", "assistant_message", "tool_log", "file_diff", "command_output", "receipt", "file_hash"}:
        return "direct"
    return "inferred"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Log one Luminary I/O Archivist event.")
    parser.add_argument("--project-root", default=".", help="Project root containing .luminary/ (default: current directory).")
    parser.add_argument("--event-id", help="Optional explicit event id. Defaults to EVT-YYYYMMDD-######.")
    parser.add_argument("--run-id", required=True, help="Run/session identifier.")
    parser.add_argument("--timestamp", help="ISO timestamp. Defaults to current UTC time.")
    parser.add_argument("--actor", required=True, help="Actor that performed or observed the event, e.g. codex, grok-cli, user, maia.")
    parser.add_argument("--role", default="unassigned", help="Role in the workflow, e.g. orchestrator, quality-gate, responsible-operator.")
    parser.add_argument("--action-type", required=True, choices=sorted(ACTION_TYPES))
    parser.add_argument("--target", required=True, help="File, command, prompt, tool, or artifact target.")
    parser.add_argument("--summary", required=True, help="Concise description of the event.")
    parser.add_argument("--evidence-source", required=True, choices=sorted(EVIDENCE_SOURCES))
    parser.add_argument("--input-ref", default=None, help="Optional input reference, snippet id, command, prompt id, or hash.")
    parser.add_argument("--output-ref", default=None, help="Optional output reference, snippet id, command result, receipt id, or hash.")
    parser.add_argument("--before-hash", default=None, help="Known pre-change hash. Never auto-invented.")
    parser.add_argument("--after-hash", default=None, help="Known post-change hash. If omitted and target is an existing file, computed automatically.")
    parser.add_argument("--claim", action="append", help="Claim id to link. Repeat or comma-separate.")
    parser.add_argument("--trace", action="append", help="Trace id to link. Repeat or comma-separate.")
    parser.add_argument("--confidence", choices=sorted(CONFIDENCE_LEVELS), help="direct | derived | inferred. Defaults from evidence source.")
    parser.add_argument("--operator-approved", action="store_true", help="Mark event as explicitly operator approved.")
    parser.add_argument("--notes", default="", help="Claim boundary or other notes.")
    parser.add_argument("--json", action="store_true", help="Print the event JSON after logging.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    paths = ensure_layout(project_root)

    if args.action_type == "validation":
        if args.evidence_source != "command_output" and args.evidence_source != "tool_log":
            parser.error("validation events must use evidence_source=command_output or tool_log.")
        if not args.output_ref:
            parser.error("validation events require --output-ref containing the check output or command result.")

    timestamp = args.timestamp or utc_now()
    events = load_jsonl(paths["events_file"])
    event_id = args.event_id or next_event_id(events, timestamp)

    target_path = (project_root / args.target).resolve()
    after_hash = args.after_hash
    if after_hash is None and target_path.exists() and target_path.is_file():
        after_hash = sha256_file(target_path)

    confidence = args.confidence or infer_confidence(args.evidence_source)

    event: Dict[str, Any] = {
        "event_id": event_id,
        "run_id": args.run_id,
        "timestamp": timestamp,
        "actor": args.actor,
        "role": args.role,
        "action_type": args.action_type,
        "target": args.target,
        "summary": args.summary,
        "evidence_source": args.evidence_source,
        "input_ref": args.input_ref,
        "output_ref": args.output_ref,
        "before_hash": args.before_hash,
        "after_hash": after_hash,
        "claim_links": split_multi(args.claim),
        "trace_links": split_multi(args.trace),
        "confidence": confidence,
        "operator_approved": bool(args.operator_approved),
        "notes": args.notes,
    }

    append_jsonl(paths["events_file"], event)

    # Maintain a basic trace->event map for convenience.
    try:
        trace_map_path = paths["trace_map_file"]
        trace_map = json.loads(trace_map_path.read_text(encoding="utf-8") or "{}")
        for trace_id in event["trace_links"]:
            trace_map.setdefault(trace_id, [])
            if event_id not in trace_map[trace_id]:
                trace_map[trace_id].append(event_id)
        trace_map_path.write_text(json.dumps(trace_map, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except Exception as exc:  # ledger write succeeded; map update should not destroy the run
        print(f"warning: event logged but trace map update failed: {exc}")

    if args.json:
        print(json.dumps(event, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(f"logged {event_id} -> {paths['events_file']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
