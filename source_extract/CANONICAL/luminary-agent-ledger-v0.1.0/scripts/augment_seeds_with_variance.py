#!/usr/bin/env python3
"""
Prime Swarm 7 - High Tier Seed Variance Amplifier

Takes the small set of high-tier seeds (the 18 best) and generates controlled,
high-signal variations to expand the high-quality training material while
preserving the core learning value.

This is "seed amplification" rather than low-quality data inflation.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


VARIANCE_PROMPT_TEMPLATE = """You are an expert at creating high-quality training data for AI systems.

You are given a high-signal "seed" summary of a real technical conversation. Your job is to generate {n_variations} high-quality **variations** of this seed.

Each variation must:
- Preserve the core learning objective and technical depth of the original.
- Change the surface form meaningfully (different user phrasing, added constraints, different framing, different difficulty, slightly shifted domain, different failure mode being explored, etc.).
- Remain realistic and useful for training an AI to handle similar situations.
- Be written in the same "Conversation seed" style as the input.
- Never invent new technical facts that contradict the spirit of the original.

Output **strict JSON** only with this exact structure:

{{
  "variations": [
    {{
      "title": "Clear, specific title for this variation",
      "trace_seed": "The full varied conversation seed text (same style and length as the input seed)",
      "variation_angle": "One sentence describing what changed (e.g. 'Added explicit constraints around performance', 'Reframed as a debugging exercise instead of greenfield design')",
      "expected_training_value": "high"
    }}
  ]
}}

Original high-tier seed:
{seed_text}
"""

@dataclass
class Seed:
    conversation_id: str
    title: str
    trace_seed: str
    category: str
    tags: list[str]
    training_value_score: int
    turn_count: int


def load_high_tier_seeds(path: Path) -> list[Seed]:
    seeds = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        seeds.append(Seed(
            conversation_id=data.get("conversation_id", str(uuid4())),
            title=data.get("title", "Untitled"),
            trace_seed=data.get("trace_seed", ""),
            category=data.get("category", "general"),
            tags=data.get("tags", []),
            training_value_score=data.get("training_value_score", 0),
            turn_count=data.get("turn_count", 0),
        ))
    return seeds


def call_model(endpoint: str, model: str, system: str, user: str, timeout: int = 180) -> str:
    url = endpoint.rstrip("/") + "/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.7,   # Some creativity for variance, but not too high
        "max_tokens": 2800,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))
    return body["choices"][0]["message"]["content"]


def parse_variations(raw: str) -> list[dict[str, Any]]:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, flags=re.I).strip()
        text = re.sub(r"```$", "", text).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("No JSON object found in model response")
    parsed = json.loads(text[start : end + 1])
    return parsed.get("variations", [])


def main(argv: list[str]) -> int:
    if len(argv) < 5:
        print("Usage: augment_seeds_with_variance.py <high_tier_seeds.jsonl> <output_dir> <endpoint> <model> [variations_per_seed]", file=sys.stderr)
        print("Example: python scripts/augment_seeds_with_variance.py outputs/high_tier_seeds_20260525/high_tier_seeds.jsonl outputs/high_tier_augmented_20260525 http://localhost:1234 mistral 5", file=sys.stderr)
        return 2

    seeds_path = Path(argv[1]).resolve()
    output_dir = Path(argv[2]).resolve()
    endpoint = argv[3]
    model = argv[4]
    n_variations = int(argv[5]) if len(argv) > 5 else 5

    output_dir.mkdir(parents=True, exist_ok=True)

    seeds = load_high_tier_seeds(seeds_path)
    print(f"Loaded {len(seeds)} high-tier seeds")

    augmented_entries = []
    variation_log = []

    system_prompt = "You are a precise and creative training data engineer. Follow instructions exactly and return only valid JSON."

    for idx, seed in enumerate(seeds, 1):
        print(f"\n[{idx}/{len(seeds)}] Processing: {seed.title}")

        user_prompt = VARIANCE_PROMPT_TEMPLATE.format(
            n_variations=n_variations,
            seed_text=seed.trace_seed
        )

        try:
            raw = call_model(endpoint, model, system_prompt, user_prompt)
            variations = parse_variations(raw)

            for v_idx, var in enumerate(variations, 1):
                new_id = f"{seed.conversation_id}-var{v_idx}"
                entry = {
                    "conversation_id": new_id,
                    "original_seed_id": seed.conversation_id,
                    "original_title": seed.title,
                    "title": var.get("title", f"{seed.title} - Variation {v_idx}"),
                    "trace_seed": var.get("trace_seed", ""),
                    "variation_angle": var.get("variation_angle", "unspecified"),
                    "category": seed.category,
                    "tags": seed.tags + ["variance-augmented"],
                    "training_value_score": seed.training_value_score,
                    "training_value_tier": "high",
                    "turn_count": seed.turn_count,
                    "source": "high-tier-variance-amplification",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                augmented_entries.append(entry)
                variation_log.append({
                    "original": seed.title,
                    "variation_title": entry["title"],
                    "angle": entry["variation_angle"]
                })
                print(f"  + Generated variation {v_idx}: {entry['title'][:60]}")

        except Exception as e:
            print(f"  ERROR on seed {seed.title}: {e}", file=sys.stderr)
            # Still keep the original as a fallback
            augmented_entries.append({
                "conversation_id": seed.conversation_id,
                "original_seed_id": seed.conversation_id,
                "original_title": seed.title,
                "title": seed.title,
                "trace_seed": seed.trace_seed,
                "variation_angle": "original (no variation generated)",
                "category": seed.category,
                "tags": seed.tags,
                "training_value_score": seed.training_value_score,
                "training_value_tier": "high",
                "turn_count": seed.turn_count,
                "source": "high-tier-original",
            })

    # Build final corpus
    corpus = {
        "corpus_id": "high-tier-augmented-via-variance-20260525",
        "version": "1.0",
        "domain": "ai-conversation-workflows",
        "trace_kind": "high-signal-seed-variance",
        "truth_state": "LOCAL_CORPUS",
        "source": "Amplified from 18 high-tier seeds extracted from ChatGPT export",
        "original_high_tier_count": len(seeds),
        "variations_per_seed": n_variations,
        "total_entries": len(augmented_entries),
        "claim_boundary": "All entries are high-signal variations generated from a small set of verified high-tier conversation seeds. Variations were produced by a local model under controlled prompting. Full source conversations are not included. This remains LOCAL_CORPUS material.",
        "system_prompt": "You generate auditable training traces from high-quality varied conversation seeds. Return strict JSON only.",
        "task_template": "High-quality varied seed:\n{trace_seed}\n\nProduce a detailed, honest training trace that captures the reasoning process for this type of request.",
        "entries": augmented_entries,
    }

    # Write outputs
    corpus_path = output_dir / "high_tier_augmented_corpus.json"
    seeds_jsonl = output_dir / "high_tier_augmented_seeds.jsonl"
    receipt_path = output_dir / "high_tier_augmented.receipt.json"

    corpus_path.write_text(json.dumps(corpus, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    with seeds_jsonl.open("w", encoding="utf-8") as f:
        for e in augmented_entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    receipt = {
        "receipt_kind": "high_tier_seed_variance_amplification",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_seeds_file": str(seeds_path),
        "original_high_tier_count": len(seeds),
        "variations_requested_per_seed": n_variations,
        "total_augmented_entries": len(augmented_entries),
        "endpoint": endpoint,
        "model": model,
        "output_files": {
            "corpus": str(corpus_path),
            "seeds_jsonl": str(seeds_jsonl),
        },
        "claim_boundary": corpus["claim_boundary"],
        "variation_log_sample": variation_log[:15],
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"\n\n=== COMPLETE ===")
    print(f"Generated {len(augmented_entries)} total entries from {len(seeds)} original high-tier seeds.")
    print(f"Corpus: {corpus_path}")
    print(f"Receipt: {receipt_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
