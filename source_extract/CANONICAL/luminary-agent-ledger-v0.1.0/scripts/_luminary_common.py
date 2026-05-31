#!/usr/bin/env python3
"""Shared helpers for Luminary I/O Archivist."""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


ACTION_TYPES = {
    "user_instruction",
    "assistant_output",
    "tool_call",
    "tool_result",
    "file_read",
    "file_edit",
    "command_run",
    "validation",
    "decision",
    "receipt",
    "trace_update",
    "read",
    "search",
    "edit",
    "execute",
}

EVIDENCE_SOURCES = {
    "user_message",
    "assistant_message",
    "tool_log",
    "file_diff",
    "command_output",
    "receipt",
    "manual_note",
    "file_hash",
}

CONFIDENCE_LEVELS = {"direct", "derived", "inferred"}


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_layout(project_root: Path) -> Dict[str, Path]:
    base = project_root / ".luminary"
    paths = {
        "base": base,
        "events_dir": base / "events",
        "claims_dir": base / "claims",
        "receipts_dir": base / "receipts",
        "maps_dir": base / "maps",
        "events_file": base / "events" / "events.jsonl",
        "claims_file": base / "claims" / "claims.jsonl",
        "trace_map_file": base / "maps" / "trace_evidence_map.json",
    }
    for key in ("events_dir", "claims_dir", "receipts_dir", "maps_dir"):
        paths[key].mkdir(parents=True, exist_ok=True)
    paths["events_file"].touch(exist_ok=True)
    paths["claims_file"].touch(exist_ok=True)
    if not paths["trace_map_file"].exists():
        paths["trace_map_file"].write_text("{}\n", encoding="utf-8")
    return paths


def sha256_file(path: Path) -> Optional[str]:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not path.exists():
        return rows
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL in {path} line {line_no}: {exc}") from exc
    return rows


def append_jsonl(path: Path, obj: Dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, sort_keys=True) + "\n")


def next_event_id(events: Iterable[Dict[str, Any]], now: Optional[str] = None) -> str:
    if now is None:
        now = utc_now()
    date = now[:10].replace("-", "")
    prefix = f"EVT-{date}-"
    max_n = 0
    for event in events:
        event_id = str(event.get("event_id", ""))
        if event_id.startswith(prefix):
            try:
                max_n = max(max_n, int(event_id.rsplit("-", 1)[-1]))
            except ValueError:
                pass
    return f"{prefix}{max_n + 1:06d}"


def next_receipt_id(receipts_dir: Path, run_id: str, now: Optional[str] = None) -> str:
    if now is None:
        now = utc_now()
    date = now[:10].replace("-", "")
    safe_run = "".join(ch if ch.isalnum() or ch in ("-", "_") else "-" for ch in run_id).strip("-")
    base = f"RCP-{date}-{safe_run}"
    existing = sorted(receipts_dir.glob(base + "*.json"))
    if not existing:
        return base
    return f"{base}-{len(existing) + 1:02d}"


def split_multi(values: Optional[List[str]]) -> List[str]:
    if not values:
        return []
    out: List[str] = []
    for value in values:
        for part in str(value).split(","):
            part = part.strip()
            if part:
                out.append(part)
    seen = set()
    deduped = []
    for item in out:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped


def evidence_strength(event: Dict[str, Any]) -> str:
    action_type = event.get("action_type")
    source = event.get("evidence_source")
    if action_type == "receipt" or source == "receipt":
        return "E5"
    if action_type == "validation":
        return "E4"
    if event.get("before_hash") or event.get("after_hash") or source == "file_diff" or event.get("output_ref"):
        return "E3"
    if action_type in {"tool_call", "tool_result", "file_read", "file_edit", "command_run", "read", "search", "edit", "execute"}:
        return "E2"
    if event.get("target"):
        return "E1"
    return "E0"
