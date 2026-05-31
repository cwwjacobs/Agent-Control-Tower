#!/usr/bin/env python3
"""
Generate high-quality variance prompts for the 18 high-tier seeds.

Each prompt is designed to be fed to a strong local model (or any good model)
to produce 4-6 high-signal variations per seed.
"""

import json
from pathlib import Path

VARIANCE_INSTRUCTIONS = """You are an expert training-data engineer specializing in creating high-leverage, high-signal variations of technical conversations for AI fine-tuning and reasoning training.

Given the high-tier seed below, generate exactly 5 high-quality variations.

Rules for good variations:
- Keep the core technical challenge, reasoning process, and learning objective intact.
- Change the surface presentation substantially (user phrasing, constraints, framing, stakes, domain flavor, failure mode, or success criteria).
- Make each variation feel like a fresh, realistic request that would still produce excellent training data.
- Do NOT make the variations easier or lower quality.
- Vary the "angle": one more constrained, one more open-ended, one focused on debugging an existing attempt, one focused on greenfield design, one with added non-functional requirements (performance, security, maintainability), etc.

Output strict JSON only in this format:

{
  "original_title": "...",
  "variations": [
    {
      "title": "Short, descriptive title",
      "trace_seed": "Full varied seed in the exact same style and density as the input seed. Include initial request, key constraints that emerged, and the nature of the final useful response.",
      "variation_angle": "One clear sentence explaining the transformation (e.g. 'Reframed as a post-mortem debugging session after a failed first attempt', 'Added strict performance and security constraints for production deployment')"
    }
  ]
}
"""

def main():
    seeds_path = Path("outputs/high_tier_seeds_20260525/high_tier_seeds.jsonl")
    out_dir = Path("outputs/high_tier_variance_prompts")
    out_dir.mkdir(parents=True, exist_ok=True)

    seeds = [json.loads(l) for l in seeds_path.read_text(encoding="utf-8").splitlines() if l.strip()]

    index = []
    for i, seed in enumerate(seeds, 1):
        prompt = f"{VARIANCE_INSTRUCTIONS}\n\nHigh-tier seed to vary:\n\n{seed['trace_seed']}\n"

        safe_name = seed['title'].lower().replace(" ", "_").replace("/", "-")[:60]
        prompt_file = out_dir / f"{i:02d}_{safe_name}.prompt.txt"
        prompt_file.write_text(prompt, encoding="utf-8")

        index.append({
            "index": i,
            "original_title": seed["title"],
            "score": seed.get("training_value_score"),
            "prompt_file": str(prompt_file),
            "recommended_variations": 5
        })

    (out_dir / "00_INDEX.json").write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Generated {len(seeds)} variance prompts in {out_dir}")
    print("See 00_INDEX.json for the mapping.")

if __name__ == "__main__":
    main()
