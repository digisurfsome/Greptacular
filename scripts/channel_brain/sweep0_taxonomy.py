#!/usr/bin/env python3
"""
Sweep 0 — Taxonomy Discovery

Reads all video info.md files + samples N random transcripts to let Claude
propose channel-specific subject categories. Merges with a generic seed list.

Output: {output_dir}/taxonomy.json

Run standalone:
    python sweep0_taxonomy.py --config ../channel_brain/config.example.json
Or imported by truth_builder_v2.py.
"""

import argparse
import asyncio
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _claude import call_claude_stdin, load_config, parse_json, preflight

# =============================================================================
# GENERIC SEED CATEGORIES (fallback / merge)
# =============================================================================

SEED_CATEGORIES = [
    {"name": "services-pricing",    "label": "Services & Pricing",        "rationale": "What they offer and what it costs"},
    {"name": "client-acquisition",  "label": "Client Acquisition",        "rationale": "How to find and land clients"},
    {"name": "sales-scripts",       "label": "Sales Scripts & Pitches",   "rationale": "Verbatim lines used in calls / outreach"},
    {"name": "automation-tech",     "label": "Automation & Tech Stack",   "rationale": "Tools, platforms, workflows"},
    {"name": "niche-strategy",      "label": "Niche & Targeting",         "rationale": "Which markets / verticals to pursue"},
    {"name": "retention",           "label": "Client Retention",          "rationale": "How to keep clients paying"},
    {"name": "scaling-hiring",      "label": "Scaling & Hiring",          "rationale": "Growing beyond solo"},
    {"name": "mindset",             "label": "Mindset & Motivation",      "rationale": "Mental / state content"},
    {"name": "misc",                "label": "Misc Tactics",              "rationale": "Catch-all for uncategorised content"},
]

TAXONOMY_PROMPT = """You are analyzing a YouTube channel to discover its content categories.

You will receive:
1. Titles + description snippets for EVERY video on the channel.
2. Full transcript samples from {sample_n} random videos.

Your job: propose 12-25 SPECIFIC subject categories for THIS channel.
These become the extraction buckets used in subsequent processing — be specific, not generic.

Rules:
- Each category must reflect content THIS channel actually covers (not a generic template)
- Mutually exclusive where possible
- Name each with a lowercase hyphenated slug  (e.g. "cold-email-outreach")
- Include a human-readable label
- 1-sentence rationale explaining why THIS channel needs this category
- 3 example phrases / topics that belong here

Return ONLY raw JSON, no markdown fences:
{{
  "categories": [
    {{
      "name": "category-slug",
      "label": "Human Label",
      "rationale": "why this specific channel needs this bucket",
      "examples": ["example phrase 1", "example phrase 2", "example phrase 3"]
    }}
  ]
}}"""


# =============================================================================
# HELPERS
# =============================================================================

def get_video_folders(videos_dir: Path) -> list[Path]:
    if not videos_dir.exists():
        print(f"FATAL: videos_dir not found: {videos_dir}")
        sys.exit(1)
    folders = [p for p in videos_dir.iterdir() if p.is_dir()]
    folders.sort(key=lambda p: p.stat().st_mtime)
    return folders


# =============================================================================
# MAIN SWEEP
# =============================================================================

async def run(cfg: dict, dry_run: bool = False) -> dict:
    output_dir = Path(cfg["output_dir"])
    videos_dir = Path(cfg["videos_dir"])
    taxonomy_path = output_dir / "taxonomy.json"
    sample_n = int(cfg.get("taxonomy_sample_n", 10))

    output_dir.mkdir(parents=True, exist_ok=True)

    # Already done — skip unless deleted
    if taxonomy_path.exists():
        data = json.loads(taxonomy_path.read_text(encoding="utf-8"))
        cats = data.get("categories", [])
        print(f"  Sweep 0: taxonomy.json exists ({len(cats)} categories) — skipping. Delete to re-run.")
        return data

    print(f"  Sweep 0: scanning {videos_dir}", flush=True)
    folders = get_video_folders(videos_dir)
    print(f"  Found {len(folders)} video folders")

    # Collect info.md content (title + description snippets)
    info_blocks = []
    for folder in folders:
        info_path = folder / "info.md"
        if info_path.exists():
            info = info_path.read_text(encoding="utf-8", errors="replace")
            info_blocks.append(f"[{folder.name}]\n{info[:400].strip()}")
        else:
            info_blocks.append(f"[{folder.name}]\n(no info.md)")

    # Sample N transcripts
    transcript_dirs = [f for f in folders if (f / "transcript.txt").exists()]
    sampled = random.sample(transcript_dirs, min(sample_n, len(transcript_dirs)))
    transcript_samples = []
    for folder in sampled:
        t = (folder / "transcript.txt").read_text(encoding="utf-8", errors="replace")
        transcript_samples.append(f"=== {folder.name} ===\n{t[:4000].strip()}")

    print(f"  Sampled {len(transcript_samples)} transcripts for analysis", flush=True)

    if dry_run:
        print("  DRY RUN: would make 1 LLM call for taxonomy discovery")
        result = {
            "categories": SEED_CATEGORIES,
            "dry_run": True,
            "video_count": len(folders),
            "note": "seed categories only — dry-run skipped LLM discovery"
        }
        taxonomy_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result

    await preflight()

    prompt = (
        TAXONOMY_PROMPT.format(sample_n=len(transcript_samples))
        + "\n\n--- ALL VIDEO TITLES + DESCRIPTIONS ---\n\n"
        + "\n\n".join(info_blocks)
        + "\n\n--- SAMPLE TRANSCRIPTS ---\n\n"
        + "\n\n".join(transcript_samples)
    )

    print("  Calling Claude for taxonomy discovery ...", flush=True)
    raw = await call_claude_stdin(prompt, label="sweep0")

    if raw is None:
        print("  WARNING: LLM call failed — using seed categories as fallback")
        result = {
            "categories": SEED_CATEGORIES,
            "fallback": True,
            "video_count": len(folders),
        }
    else:
        parsed = parse_json(raw)
        if parsed and isinstance(parsed, dict) and "categories" in parsed:
            channel_cats = parsed["categories"]
            channel_names = {c["name"] for c in channel_cats}
            # Merge: add any seed categories not already covered
            merged = channel_cats + [s for s in SEED_CATEGORIES if s["name"] not in channel_names]
            result = {
                "categories": merged,
                "video_count": len(folders),
                "sample_count": len(transcript_samples),
                "channel_specific_count": len(channel_cats),
                "seed_added": len(merged) - len(channel_cats),
            }
            print(
                f"  Discovered {len(channel_cats)} channel-specific categories "
                f"+ {len(merged) - len(channel_cats)} seed fallbacks = {len(merged)} total"
            )
        else:
            print("  WARNING: could not parse taxonomy response — using seed categories")
            result = {
                "categories": SEED_CATEGORIES,
                "parse_error": True,
                "raw_snippet": (raw or "")[:200],
                "video_count": len(folders),
            }

    taxonomy_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"  Saved → {taxonomy_path}")
    return result


# =============================================================================
# STANDALONE ENTRY
# =============================================================================

def main() -> None:
    ap = argparse.ArgumentParser(description="Sweep 0: Taxonomy Discovery")
    ap.add_argument("--config", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    cfg = load_config(args.config)
    asyncio.run(run(cfg, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
