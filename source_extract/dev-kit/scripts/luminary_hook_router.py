#!/usr/bin/env python3
"""
Luminary hook router for Claude Code and Codex.

Reads one JSON hook event from stdin, maps it to a Luminary event, and logs it
using scripts/luminary_log_event.py.

Designed to be defensive:
- never blocks the agent unless the logger itself is badly misconfigured
- records raw hook JSON into .luminary/hook_payloads/ for audit
- avoids storing giant tool responses inline in the ledger
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict


def compact(obj: Any, limit: int = 600) -> str:
    try:
        text = json.dumps(obj, ensure_ascii=False, sort_keys=True)
    except Exception:
        text = str(obj)
    if len(text) > limit:
        return text[:limit] + "...[truncated]"
    return text


def find_project_root(payload: Dict[str, Any]) -> Path:
    env_root = os.environ.get("LUMINARY_PROJECT_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()
    cwd = payload.get("cwd") or os.getcwd()
    cur = Path(cwd).expanduser().resolve()
    for p in [cur, *cur.parents]:
        if (p / ".luminary").exists() and (p / "scripts" / "luminary_log_event.py").exists():
            return p
    return cur


def choose_action_type(event_name: str, tool_name: str) -> str:
    e = (event_name or "").lower()
    t = (tool_name or "").lower()
    if e == "userpromptsubmit":
        return "user_instruction"
    if e in {"sessionstart", "subagentstart"}:
        return "decision"
    if e in {"stop", "sessionend", "subagentstop"}:
        return "assistant_output"
    if "failure" in e:
        return "tool_result"
    if e == "pretooluse":
        return "tool_call"
    if e == "posttooluse":
        if any(x in t for x in ["write", "edit", "apply_patch"]):
            return "file_edit"
        if any(x in t for x in ["bash", "shell", "execute"]):
            return "command_run"
        if any(x in t for x in ["read", "grep", "search"]):
            return "file_read"
        return "tool_result"
    return "tool_result"


def pick_target(project_root: Path, payload: Dict[str, Any]) -> str:
    tool_input = payload.get("tool_input") or {}
    tool_response = payload.get("tool_response") or {}
    for key in ("file_path", "filePath", "path"):
        val = tool_input.get(key) or tool_response.get(key)
        if val:
            try:
                p = Path(str(val))
                if p.is_absolute():
                    return str(p.resolve().relative_to(project_root))
            except Exception:
                pass
            return str(val)
    if "command" in tool_input:
        return str(tool_input.get("command"))
    if "prompt" in payload:
        return "user_prompt"
    if payload.get("transcript_path"):
        return str(payload.get("transcript_path"))
    return payload.get("hook_event_name", "unknown_hook_event")


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw or "{}")
    except Exception as exc:
        payload = {"hook_event_name": "InvalidHookPayload", "raw": raw[:2000], "error": str(exc)}

    project_root = find_project_root(payload)
    run_id = os.environ.get("LUMINARY_RUN_ID") or payload.get("session_id") or f"RUN-hook-{os.getpid()}"
    event_name = payload.get("hook_event_name") or payload.get("event") or "UnknownHook"
    tool_name = payload.get("tool_name") or payload.get("tool") or ""

    payload_dir = project_root / ".luminary" / "hook_payloads" / str(run_id)
    payload_dir.mkdir(parents=True, exist_ok=True)

    digest = hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()[:16]
    payload_path = payload_dir / f"{event_name}-{digest}.json"
    payload_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

    action_type = choose_action_type(event_name, tool_name)
    target = pick_target(project_root, payload)

    if action_type == "tool_call":
        evidence_source = "tool_log"
    elif action_type in {"file_edit", "command_run", "file_read", "tool_result"}:
        evidence_source = "tool_log"
    elif action_type == "user_instruction":
        evidence_source = "user_message"
    else:
        evidence_source = "tool_log"

    output_ref = f"hook_payload={payload_path.relative_to(project_root)}"
    if action_type == "command_run":
        output_ref += f"; tool_response={compact(payload.get('tool_response', payload.get('error', '')))}"
    elif "error" in payload:
        output_ref += f"; error={compact(payload.get('error'))}"

    summary = f"{event_name}"
    if tool_name:
        summary += f" for {tool_name}"
    summary += f" logged by Luminary hook router."

    cmd = [
        sys.executable,
        str(project_root / "scripts" / "luminary_log_event.py"),
        "--project-root", str(project_root),
        "--run-id", str(run_id),
        "--actor", os.environ.get("LUMINARY_AGENT_NAME", "agent-hook"),
        "--role", "hook-router",
        "--action-type", action_type,
        "--target", target,
        "--summary", summary,
        "--evidence-source", evidence_source,
        "--output-ref", output_ref,
        "--confidence", "direct",
        "--notes", "Automated hook event. Payload stored separately; ledger entry is a compact evidence anchor."
    ]

    # If this target is a real file, luminary_log_event.py will compute after_hash.
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as exc:
        # Do not break the agent loop for logging failure; leave a local failure marker.
        failure_path = payload_dir / f"LOGGER_FAILURE-{digest}.txt"
        failure_path.write_text(str(exc) + "\n" + " ".join(cmd) + "\n", encoding="utf-8")

    # Hook success. Return minimal JSON context only where accepted.
    print(json.dumps({
        "systemMessage": "Luminary Archivist logged this hook event.",
        "suppressOutput": True
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
