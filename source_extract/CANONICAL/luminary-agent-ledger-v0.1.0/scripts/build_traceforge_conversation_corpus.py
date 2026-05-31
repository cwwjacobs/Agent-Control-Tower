#!/usr/bin/env python3
"""Build a TraceForge TUI corpus from a ChatGPT conversations.json export."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MAX_FIELD_CHARS = 1400
MAX_DIGEST_TURNS = 8


KEYWORD_TAGS = {
    "code": ["code", "python", "javascript", "typescript", "react", "api", "bug", "test", "repo", "git", "debug", "refactor"],
    "reasoning": ["because", "therefore", "hypothesis", "tradeoff", "trade-off", "why", "how would", "what if", "alternative", "consider", "rationale", "evidence"],
    "agentic": ["agent", "swarm", "orchestrator", "subagent", "tool use", "mcp", "function call", "traceforge", "prime-swarm"],
    "skill": ["skill", "codex", "workflow", "prompt engineering", "system prompt"],
    "corpus": ["corpus", "training", "trace", "dataset", "jsonl", "fine-tune", "fine tune", "training data"],
    "debugging": ["debug", "bug", "error", "fix", "root cause", "reproduce"],
    "architecture": ["architecture", "design", "modular", "coupling", "scalability", "tradeoffs"],
    "device": ["phone", "samsung", "usb", "hub", "dex", "ios", "termux"],
    "support": ["setup", "guide", "help", "options", "backup", "install"],
    "personal": ["love", "apology", "consent", "home", "message", "my love"],
    "gaming": ["fo76", "geforce", "game", "settings"],
}


def compact_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def truncate(text: str, limit: int = MAX_FIELD_CHARS) -> str:
    text = compact_ws(text)
    if len(text) <= limit:
        return text
    return text[: limit - 20].rstrip() + " ... [truncated]"


def iso_from_epoch(value: Any) -> str | None:
    if not isinstance(value, (int, float)):
        return None
    try:
        return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()
    except (OverflowError, OSError, ValueError):
        return None


def message_text(message: dict[str, Any] | None) -> str:
    if not message:
        return ""
    content = message.get("content") or {}
    content_type = content.get("content_type")
    if content_type == "text":
        parts = content.get("parts") or []
        return "\n".join(str(part) for part in parts if part is not None)
    if content_type == "multimodal_text":
        parts = content.get("parts") or []
        out = []
        for part in parts:
            if isinstance(part, str):
                out.append(part)
            elif isinstance(part, dict) and part.get("content_type") == "text":
                out.append(str(part.get("text", "")))
        return "\n".join(out)
    return ""


def ordered_messages(conversation: dict[str, Any]) -> list[dict[str, str]]:
    mapping = conversation.get("mapping") or {}
    current = conversation.get("current_node")
    path: list[str] = []
    seen: set[str] = set()

    while current and current in mapping and current not in seen:
        seen.add(current)
        path.append(current)
        current = (mapping.get(current) or {}).get("parent")
    path.reverse()

    if not path:
        path = list(mapping.keys())

    messages: list[dict[str, str]] = []
    for node_id in path:
        node = mapping.get(node_id) or {}
        msg = node.get("message") or {}
        role = ((msg.get("author") or {}).get("role") or "").strip()
        if role not in {"user", "assistant"}:
            continue
        text = message_text(msg)
        if not compact_ws(text):
            continue
        messages.append(
            {
                "role": role,
                "text": text,
                "node_id": node_id,
            }
        )
    return messages


def tags_for(title: str, messages: list[dict[str, str]]) -> list[str]:
    # Weight the title + first 4 and last 3 messages more heavily for signal
    haystack_parts = [title]
    for m in messages[:4]:
        haystack_parts.append(m["text"][:800])
    for m in messages[-3:]:
        haystack_parts.append(m["text"][:600])
    haystack = "\n".join(haystack_parts).lower()

    tags = [tag for tag, keys in KEYWORD_TAGS.items() if any(key in haystack for key in keys)]

    # Boost reasoning/agentic if we see explicit back-and-forth technical language
    reasoning_hits = sum(1 for m in messages if any(k in m["text"].lower() for k in KEYWORD_TAGS.get("reasoning", [])))
    if reasoning_hits >= 3 and "reasoning" not in tags:
        tags.append("reasoning")

    if not tags:
        tags.append("general")
    return sorted(set(tags))


def category_for(tags: list[str]) -> str:
    priority = ["agentic", "reasoning", "debugging", "architecture", "code", "skill", "corpus", "device", "gaming", "support", "personal"]
    for item in priority:
        if item in tags:
            return item
    return tags[0] if tags else "general"


def digest(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    if len(messages) <= MAX_DIGEST_TURNS:
        selected = list(enumerate(messages))
    else:
        head = list(enumerate(messages[:4]))
        tail = list(enumerate(messages[-4:], start=len(messages) - 4))
        selected = head + tail

    return [
        {
            "turn_index": idx,
            "role": msg["role"],
            "excerpt": truncate(msg["text"], 700),
        }
        for idx, msg in selected
    ]


def code_block_count(messages: list[dict[str, str]]) -> int:
    return sum(msg["text"].count("```") // 2 for msg in messages)


def training_value(messages: list[dict[str, str]], tags: list[str]) -> tuple[int, str]:
    user_turns = sum(1 for m in messages if m["role"] == "user")
    assistant_turns = sum(1 for m in messages if m["role"] == "assistant")
    chars = sum(len(m["text"]) for m in messages)
    code_blocks = code_block_count(messages)

    # Base score — deliberately lower than before to reduce length gaming
    score = 15

    # Strong signal: real multi-turn technical iteration
    if user_turns >= 4 and assistant_turns >= 4:
        score += 18
    if user_turns >= 8 and assistant_turns >= 6:
        score += 12

    # Reasoning density (the most important new signal)
    reasoning_keywords = {"because", "therefore", "hypothesis", "tradeoff", "why", "how would", "alternative", "consider", "rationale", "evidence", "root cause"}
    reasoning_count = 0
    for m in messages:
        text_lower = m["text"].lower()
        reasoning_count += sum(1 for kw in reasoning_keywords if kw in text_lower)
    if reasoning_count >= 5:
        score += 22
    elif reasoning_count >= 2:
        score += 12

    # Code + explanation pairs are gold for training
    if code_blocks >= 2:
        score += 15
    elif code_blocks >= 1:
        score += 8

    # High-value domain tags get significant boost
    high_value_tags = {"agentic", "reasoning", "debugging", "architecture", "code", "skill", "corpus"}
    tag_boost = len(high_value_tags & set(tags)) * 6
    score += tag_boost

    # Length is now a weak secondary signal only
    if chars >= 6000 and reasoning_count >= 3:
        score += 10
    elif chars >= 12000 and reasoning_count >= 6:
        score += 8

    # Personal noise penalty (long affectionate threads that happen to mention tech)
    personal_hits = sum(1 for m in messages if any(k in m["text"].lower() for k in KEYWORD_TAGS.get("personal", [])))
    if personal_hits > len(messages) * 0.30:
        score -= 22
    if personal_hits > len(messages) * 0.45:
        score -= 15  # extra penalty for very personal-heavy threads

    # Hard gate for "high" tier: must have meaningful technical signal
    has_real_technical = (
        code_blocks >= 1 or
        reasoning_count >= 4 or
        bool({"agentic", "debugging", "architecture", "reasoning"} & set(tags))
    )

    score = max(0, min(score, 100))

    if score >= 78 and has_real_technical:
        return score, "high"
    if score >= 55:
        return score, "medium"
    return score, "low"


def build_entry(index: int, conversation: dict[str, Any]) -> dict[str, Any] | None:
    title = compact_ws(str(conversation.get("title") or f"Conversation {index + 1}"))
    messages = ordered_messages(conversation)
    if not messages:
        return None

    tags = tags_for(title, messages)
    category = category_for(tags)
    score, value_tier = training_value(messages, tags)
    user_msgs = [m for m in messages if m["role"] == "user"]
    assistant_msgs = [m for m in messages if m["role"] == "assistant"]
    total_chars = sum(len(m["text"]) for m in messages)
    entry_id = conversation.get("conversation_id") or conversation.get("id") or f"conversation-{index + 1:04d}"

    first_user = user_msgs[0]["text"] if user_msgs else ""
    last_user = user_msgs[-1]["text"] if user_msgs else ""
    last_assistant = assistant_msgs[-1]["text"] if assistant_msgs else ""

    trace_seed = (
        f"Conversation title: {title}\n"
        f"Category: {category}; tags: {', '.join(tags)}; turns: {len(messages)}.\n"
        f"Initial user request: {truncate(first_user, 600)}\n"
        f"Final user request: {truncate(last_user, 600)}\n"
        f"Final assistant response excerpt: {truncate(last_assistant, 800)}"
    )

    return {
        "conversation_id": str(entry_id),
        "source_index": index,
        "title": title,
        "created_at": iso_from_epoch(conversation.get("create_time")),
        "updated_at": iso_from_epoch(conversation.get("update_time")),
        "category": category,
        "tags": tags,
        "turn_count": len(messages),
        "user_turn_count": len(user_msgs),
        "assistant_turn_count": len(assistant_msgs),
        "total_message_chars": total_chars,
        "code_block_count": code_block_count(messages),
        "training_value_score": score,
        "training_value_tier": value_tier,
        "first_user_request": truncate(first_user),
        "last_user_request": truncate(last_user),
        "last_assistant_excerpt": truncate(last_assistant),
        "dialogue_digest": digest(messages),
        "trace_seed": trace_seed,
        "privacy_note": "Bounded excerpts only; raw full conversation text was not copied into this corpus entry.",
    }


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("Usage: build_traceforge_conversation_corpus.py <conversations.json> <output_dir>", file=sys.stderr)
        return 2

    source_path = Path(argv[1]).resolve()
    output_dir = Path(argv[2]).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    source_bytes = source_path.read_bytes()
    conversations = json.loads(source_bytes.decode("utf-8"))
    if not isinstance(conversations, list):
        raise ValueError("expected conversations.json root to be a list")

    entries = []
    skipped = 0
    for idx, conversation in enumerate(conversations):
        if not isinstance(conversation, dict):
            skipped += 1
            continue
        entry = build_entry(idx, conversation)
        if entry is None:
            skipped += 1
            continue
        entries.append(entry)

    entries.sort(key=lambda e: (e["training_value_score"], e["turn_count"], e["total_message_chars"]), reverse=True)
    category_counts = Counter(e["category"] for e in entries)
    tier_counts = Counter(e["training_value_tier"] for e in entries)

    corpus = {
        "corpus_id": "traceforge-conversations-20260525-hardened",
        "version": "1.1-hardened",
        "domain": "ai-conversation-workflows",
        "trace_kind": "conversation-to-training-trace",
        "truth_state": "LOCAL_CORPUS",
        "source_file": str(source_path),
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "processing_notes": "Hardened v1.1 scoring: reasoning density, technical iteration, and high-value domain tags heavily prioritized. Length and generic keyword presence down-weighted. Personal noise penalized.",
        "claim_boundary": "User-supplied ChatGPT export transformed into bounded local training-trace seeds. Not independently verified. Full raw conversations are not copied. Scoring improvements in v1.1 reduce contamination from long personal threads. This is seed material only — actual high-quality traces require the TraceForge TUI forge step with a capable local model.",
        "system_prompt": (
            "You generate auditable training traces from bounded conversation seeds. "
            "Return strict JSON only in the TraceForge schema. Treat excerpts as incomplete local context, "
            "mark uncertainty honestly, and never invent raw conversation details not present in the seed."
        ),
        "task_template": (
            "Conversation seed:\n{trace_seed}\n\n"
            "Produce a training trace that teaches how to handle this kind of user request. "
            "Use the entry metadata as evidence, preserve privacy boundaries, and mark missing context explicitly."
        ),
        "schema_hint": {
            "id_field": "conversation_id",
            "summary_field": "trace_seed",
            "category_field": "category",
            "tags_field": "tags",
        },
        "entries": entries,
    }

    corpus_path = output_dir / "traceforge_conversations_corpus.json"
    sample_path = output_dir / "traceforge_conversations_corpus.sample25.json"
    jsonl_path = output_dir / "traceforge_conversations_seeds.jsonl"
    index_path = output_dir / "traceforge_conversations_index.csv"
    receipt_path = output_dir / "traceforge_conversations_corpus.receipt.json"

    write_json(corpus_path, corpus)
    sample = dict(corpus)
    sample["entries"] = entries[:25]
    write_json(sample_path, sample)

    with jsonl_path.open("w", encoding="utf-8") as fh:
        for entry in entries:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    with index_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "conversation_id",
                "title",
                "category",
                "training_value_tier",
                "training_value_score",
                "turn_count",
                "total_message_chars",
                "created_at",
            ],
        )
        writer.writeheader()
        for entry in entries:
            writer.writerow({field: entry.get(field) for field in writer.fieldnames})

    receipt = {
        "receipt_kind": "traceforge_conversation_corpus_build",
        "version": "1.1-hardened",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_file": str(source_path),
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "source_conversation_count": len(conversations),
        "entry_count": len(entries),
        "skipped_count": skipped,
        "category_counts": dict(sorted(category_counts.items())),
        "training_value_tier_counts": dict(sorted(tier_counts.items())),
        "outputs": {
            "corpus": str(corpus_path),
            "sample25": str(sample_path),
            "seeds_jsonl": str(jsonl_path),
            "index_csv": str(index_path),
        },
        "output_sha256": {
            "corpus": sha256_file(corpus_path),
            "sample25": sha256_file(sample_path),
            "seeds_jsonl": sha256_file(jsonl_path),
            "index_csv": sha256_file(index_path),
        },
        "claim_boundary": [
            "LOCAL_CORPUS only; source is user-supplied conversations.json.",
            "v1.1-hardened: scoring now prioritizes reasoning density and technical iteration over raw length.",
            "No local LLM forge was run by this script.",
            "Generated corpus entries contain bounded excerpts and deterministic metadata, not full raw conversations.",
            "TraceForge TUI can load the corpus and then generate model-produced training rows through its normal local endpoint flow.",
        ],
        "processing_summary": "Hardened pass using Prime Swarm 7 principles. Personal noise down-weighted. High-signal agentic/reasoning/debugging conversations elevated.",
    }
    write_json(receipt_path, receipt)

    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
