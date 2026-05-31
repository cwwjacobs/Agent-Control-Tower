#!/usr/bin/env python3
"""Audit trace markdown evidence coverage against the Luminary ledger."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List

from _luminary_common import ensure_layout, evidence_strength, load_jsonl


TRACE_HEADING_RE = re.compile(r"^###\s+(Trace\s+\d+):\s*(.+?)\s*$", re.MULTILINE)


def normalize_trace_id(label: str) -> str:
    match = re.search(r"(\d+)", label)
    if not match:
        return label.upper().replace(" ", "-")
    return f"TRACE-{int(match.group(1)):03d}"


def quality_for(events: List[Dict[str, Any]], receipt_events: List[Dict[str, Any]]) -> str:
    if not events:
        return "no_evidence_events"
    strengths = {evidence_strength(e) for e in events}
    if receipt_events or "E5" in strengths:
        return "receipt_covered"
    if "E4" in strengths:
        return "validation_evidence"
    if "E3" in strengths:
        return "direct_evidence_anchors"
    if "E2" in strengths:
        return "action_logged_only"
    return "weak_evidence"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit trace evidence coverage.")
    parser.add_argument("--project-root", default=".", help="Project root containing .luminary/.")
    parser.add_argument("--trace-file", required=True, help="Markdown file containing Trace headings.")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    paths = ensure_layout(project_root)
    trace_file = (project_root / args.trace_file).resolve()
    if not trace_file.exists():
        raise SystemExit(f"trace file not found: {trace_file}")

    md = trace_file.read_text(encoding="utf-8")
    headings = [(normalize_trace_id(label), title.strip()) for label, title in TRACE_HEADING_RE.findall(md)]

    events = load_jsonl(paths["events_file"])
    by_trace: Dict[str, List[Dict[str, Any]]] = {}
    receipt_by_trace: Dict[str, List[Dict[str, Any]]] = {}
    for event in events:
        for trace in event.get("trace_links", []) or []:
            by_trace.setdefault(trace, []).append(event)
            if event.get("action_type") == "receipt" or event.get("evidence_source") == "receipt":
                receipt_by_trace.setdefault(trace, []).append(event)

    rows = []
    for trace_id, title in headings:
        linked_events = by_trace.get(trace_id, [])
        rows.append({
            "trace_id": trace_id,
            "title": title,
            "event_count": len(linked_events),
            "quality": quality_for(linked_events, receipt_by_trace.get(trace_id, [])),
            "validation_events": sum(1 for e in linked_events if e.get("action_type") == "validation"),
            "receipt_events": len(receipt_by_trace.get(trace_id, [])),
        })

    if args.format == "json":
        print(json.dumps(rows, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print("| Trace | Evidence Quality | Events | Validation | Receipt | Title |")
        print("|---|---|---:|---:|---:|---|")
        for row in rows:
            print(f"| {row['trace_id']} | {row['quality']} | {row['event_count']} | {row['validation_events']} | {row['receipt_events']} | {row['title']} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
