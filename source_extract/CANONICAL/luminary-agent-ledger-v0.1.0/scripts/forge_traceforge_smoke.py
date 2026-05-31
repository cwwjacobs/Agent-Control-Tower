#!/usr/bin/env python3
"""Forge a small TraceForge training-row smoke set from a corpus."""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


DEFAULT_SCHEMA = """{
  "trace_title": "string",
  "task": "string",
  "domain": "string",
  "steps": [
    {
      "step": 1,
      "state": "what is known at this point",
      "decision": "the next decision or action",
      "rationale": "concise reason for the decision",
      "evidence": "source in prompt or explicit assumption",
      "uncertainty": "unknowns, risks, or limits",
      "next_action": "next action",
      "quality_signal": "why this step is useful for training"
    }
  ],
  "final_answer": "string",
  "training_notes": {
    "what_to_learn": "string",
    "failure_modes": "string",
    "honesty_notes": "string"
  }
}"""


def parse_json_response(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, flags=re.I).strip()
        text = re.sub(r"```$", "", text).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("no JSON object found in model response")
    parsed = json.loads(text[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("trace JSON root must be an object")
    return parsed


def score_trace(trace: dict[str, Any], requested_steps: int) -> tuple[int, str, list[str], bool]:
    validation: list[str] = []
    score = 25
    steps = trace.get("steps")
    if not isinstance(steps, list) or not steps:
        return 0, "BLOCK", ["missing non-empty steps array"], False
    if abs(len(steps) - requested_steps) <= 1:
        score += 15
    else:
        validation.append(f"step count {len(steps)} differs from requested {requested_steps}")
        score += 7

    required = ("state", "decision", "rationale", "evidence", "uncertainty", "next_action", "quality_signal")
    complete_steps = 0
    honest_steps = 0
    for idx, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            validation.append(f"step {idx} is not an object")
            continue
        missing = [field for field in required if not str(step.get(field, "")).strip()]
        if missing:
            validation.append(f"step {idx} missing {', '.join(missing)}")
        else:
            complete_steps += 1
        uncertainty = str(step.get("uncertainty", "")).lower()
        evidence = str(step.get("evidence", "")).lower()
        if uncertainty and evidence and "none" not in uncertainty:
            honest_steps += 1

    score += int(25 * (complete_steps / len(steps)))
    score += int(15 * (honest_steps / len(steps)))
    if str(trace.get("final_answer", "")).strip():
        score += 10
    else:
        validation.append("missing final_answer")
    notes = trace.get("training_notes")
    if isinstance(notes, dict) and all(
        str(notes.get(k, "")).strip() for k in ("what_to_learn", "failure_modes", "honesty_notes")
    ):
        score += 10
    else:
        validation.append("training_notes incomplete")

    score = min(score, 100)
    if score >= 90:
        tier = "DIAMOND"
    elif score >= 80:
        tier = "GOLD"
    elif score >= 65:
        tier = "SILVER"
    else:
        tier = "BRONZE"
    trainable = score >= 80 and not any(item.startswith("step") and "missing" in item for item in validation)
    if not validation:
        validation.append("ok")
    return score, tier, validation, trainable


def fill_template(template: str, entry: dict[str, Any]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        value = entry.get(key)
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return "" if value is None else str(value)

    return re.sub(r"{([a-zA-Z0-9_]+)}", replace, template)


def call_model(endpoint: str, model: str, system: str, user: str, timeout: int) -> str:
    url = endpoint.rstrip("/") + "/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
        "max_tokens": 2200,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))
    return body["choices"][0]["message"]["content"]


def training_row(
    *,
    system: str,
    user: str,
    trace: dict[str, Any],
    model: str,
    endpoint: str,
    corpus: dict[str, Any],
    entry: dict[str, Any],
    score: int,
    tier: str,
    validation: list[str],
    trainable: bool,
) -> dict[str, Any]:
    run_id = uuid4().hex[:12]
    return {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
            {"role": "assistant", "content": json.dumps(trace, ensure_ascii=False)},
        ],
        "meta": {
            "format": "traceforge.training_trace.v2",
            "id": run_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "model": model,
            "endpoint": endpoint,
            "domain": corpus.get("domain"),
            "trace_kind": corpus.get("trace_kind"),
            "score": score,
            "tier": tier,
            "trainable": trainable,
            "validation": validation,
            "steps": len(trace.get("steps", [])),
            "truth_state": "LOCAL_CORPUS",
            "corpus_id": corpus.get("corpus_id"),
            "corpus_entry_ref": entry.get("conversation_id"),
            "variation_angle": "smoke-local-model",
            "source": "local_llm_generated_trace",
        },
    }


def main(argv: list[str]) -> int:
    if len(argv) != 6:
        print(
            "Usage: forge_traceforge_smoke.py <corpus.json> <output_dir> <endpoint> <model> <count>",
            file=sys.stderr,
        )
        return 2

    corpus_path = Path(argv[1]).resolve()
    output_dir = Path(argv[2]).resolve()
    endpoint = argv[3]
    model = argv[4]
    count = int(argv[5])
    requested_steps = 5

    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    entries = corpus["entries"][:count]
    output_dir.mkdir(parents=True, exist_ok=True)

    system = corpus.get("system_prompt") or "Return strict JSON only."
    system = system + "\n\nRequired JSON schema:\n" + DEFAULT_SCHEMA
    template = corpus.get("task_template") or "Task: {trace_seed}\n\nProduce a training trace."

    rows = []
    failures = []
    for entry in entries:
        user = fill_template(template, entry)
        user += f"\n\nRequirement: produce exactly {requested_steps} steps."
        try:
            raw = call_model(endpoint, model, system, user, timeout=180)
            trace = parse_json_response(raw)
            score, tier, validation, trainable = score_trace(trace, requested_steps)
            rows.append(
                training_row(
                    system=system,
                    user=user,
                    trace=trace,
                    model=model,
                    endpoint=endpoint,
                    corpus=corpus,
                    entry=entry,
                    score=score,
                    tier=tier,
                    validation=validation,
                    trainable=trainable,
                )
            )
            print(f"ok {entry.get('conversation_id')} score={score} tier={tier}")
        except Exception as exc:
            failures.append({"conversation_id": entry.get("conversation_id"), "error": str(exc)})
            print(f"fail {entry.get('conversation_id')} {exc}", file=sys.stderr)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    jsonl_path = output_dir / f"traceforge_conversations_smoke_traces_{ts}.jsonl"
    receipt_path = output_dir / f"traceforge_conversations_smoke_traces_{ts}.receipt.json"

    with jsonl_path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    tier_counts = Counter(row["meta"]["tier"] for row in rows)
    receipt = {
        "receipt_kind": "traceforge_local_model_smoke_forge",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "corpus": str(corpus_path),
        "endpoint": endpoint,
        "model": model,
        "requested_count": count,
        "row_count": len(rows),
        "failure_count": len(failures),
        "tier_counts": dict(sorted(tier_counts.items())),
        "failures": failures,
        "training_file": str(jsonl_path),
        "claim_boundary": [
            "Small smoke forge only, not a full 533-entry corpus run.",
            "Rows were generated through the local OpenAI-compatible endpoint.",
            "Rows inherit LOCAL_CORPUS trust from the user-supplied conversation corpus.",
        ],
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
