#!/usr/bin/env python3
"""
Sweep 1 — Verbatim Extraction (Dump Pass)

For each video:
- Reads transcript.txt + info.md
- Calls Claude to extract ALL quotes/claims/scripts verbatim
- NO dedup, NO truth-doc context, NO judgment about "is this new"
- Each video is isolated — context rot is impossible

Output: {output_dir}/extractions/{video_folder_name}.jsonl
One JSON object per line:
  {"verbatim": "exact words", "bucket": "category-slug", "context_note": "...",
   "source_folder": "...", "source_video": "..."}

Resumable: already-extracted .jsonl files are skipped.
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _claude import call_claude_stdin, parse_json, load_config, load_progress, save_progress


# =============================================================================
# EXTRACTION PROMPT
# =============================================================================

EXTRACT_SYSTEM = """Extract ALL quotes, claims, scripts, tactics, frameworks, and specific information from this video transcript. This is a YouTube video about a specific topic.

RULES — read carefully:
1. VERBATIM ONLY. Use exact words from the transcript. No paraphrasing, no summarising.
   If the speaker says "we charge five grand a month" — extract "we charge five grand a month",
   NOT "they charge $5,000/month".
2. NO DEDUP. Capture ALL instances, even if similar to each other. Two slightly different
   phrasings of the same idea = two separate entries. Wording variants are the value.
3. INCLUDE EVERYTHING: prices, scripts, objection responses, tool names, URLs, processes,
   warnings, mindset phrases, exact numbers, step-by-step workflows, cold email/call lines.
4. SKIP: intro filler, "smash subscribe", sponsor reads, off-topic tangents.
5. Empty list [] ONLY if transcript has literally zero extractable content.
6. bucket MUST be one of the provided category names (exact slug match).

Return ONLY raw JSON, no markdown fences:
{
  "extractions": [
    {
      "verbatim": "exact words from transcript",
      "bucket": "category-slug",
      "context_note": "1 sentence: what was happening when this was said"
    }
  ]
}"""


# =============================================================================
# HELPERS
# =============================================================================

def get_video_folders(videos_dir: Path) -> list[Path]:
    folders = [
        p for p in videos_dir.iterdir()
        if p.is_dir() and (p / "transcript.txt").exists()
    ]
    folders.sort(key=lambda p: p.stat().st_mtime)
    return folders


def read_transcript(folder: Path) -> str | None:
    t = folder / "transcript.txt"
    if not t.exists():
        return None
    text = t.read_text(encoding="utf-8", errors="replace").strip()
    bad_markers = ("[Transcript unavailable", "[Transcript", "Could not retrieve")
    if len(text) < 200 or any(text.startswith(m) for m in bad_markers):
        return None
    return text


def read_info(folder: Path) -> str:
    i = folder / "info.md"
    return i.read_text(encoding="utf-8", errors="replace") if i.exists() else ""


def count_jsonl_lines(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


# =============================================================================
# SINGLE VIDEO EXTRACTION
# =============================================================================

# Chunking — per playbook, 1,500 tokens ≈ 6,000 chars w/ 800 char overlap.
# Single-prompt per video = 100% exit-15 on long transcripts (documented in
# docs/info/live-call-extraction-playbook.md).
CHUNK_CHARS = 6000
CHUNK_OVERLAP = 800


def _chunk_transcript(text: str) -> list[str]:
    if len(text) <= CHUNK_CHARS:
        return [text]
    chunks = []
    i = 0
    n = len(text)
    while i < n:
        end = min(i + CHUNK_CHARS, n)
        # Try to break at a sentence/space boundary near the end
        if end < n:
            cut = text.rfind(" ", i + CHUNK_CHARS - 400, end)
            if cut > i:
                end = cut
        chunks.append(text[i:end])
        if end >= n:
            break
        i = max(end - CHUNK_OVERLAP, i + 1)
    return chunks


async def extract_video(folder: Path, bucket_names: list[str], label: str) -> list[dict]:
    transcript = read_transcript(folder)
    if not transcript:
        return []

    info = read_info(folder)
    source_title = info.split("\n")[0].strip() if info else folder.name

    buckets_str = "\n".join(f"  - {b}" for b in bucket_names)
    info_block = info[:400].strip()

    chunks = _chunk_transcript(transcript)
    valid_buckets = set(bucket_names)
    results: list[dict] = []
    seen_verbatim: set[str] = set()  # cross-chunk dedup (overlap region)

    for ci, chunk in enumerate(chunks, 1):
        chunk_label = f"{label}-c{ci}/{len(chunks)}" if len(chunks) > 1 else label
        prompt = (
            EXTRACT_SYSTEM
            + f"\n\nAVAILABLE BUCKETS (use exact slug):\n{buckets_str}"
            + f"\n\n--- VIDEO INFO ---\n{info_block}"
            + (f"\n\n--- TRANSCRIPT (chunk {ci}/{len(chunks)}) ---\n" if len(chunks) > 1
               else "\n\n--- TRANSCRIPT ---\n")
            + chunk
        )

        raw = await call_claude_stdin(prompt, label=chunk_label)
        if raw is None:
            continue

        parsed = parse_json(raw)
        if not parsed or not isinstance(parsed, dict) or "extractions" not in parsed:
            continue

        for item in parsed["extractions"]:
            verbatim = (item.get("verbatim") or "").strip()
            if not verbatim:
                continue
            key = verbatim.lower()
            if key in seen_verbatim:
                continue
            seen_verbatim.add(key)
            bucket = item.get("bucket", "misc")
            if bucket not in valid_buckets:
                bucket = "misc"
            results.append({
                "verbatim":     verbatim,
                "bucket":       bucket,
                "context_note": (item.get("context_note") or "").strip(),
                "source_folder": folder.name,
                "source_video":  source_title,
            })

    return results


# =============================================================================
# MAIN SWEEP
# =============================================================================

async def run(
    cfg: dict,
    taxonomy: dict,
    limit: int | None = None,
    dry_run: bool = False,
) -> int:
    output_dir    = Path(cfg["output_dir"])
    videos_dir    = Path(cfg["videos_dir"])
    extractions_dir = output_dir / "extractions"
    extractions_dir.mkdir(parents=True, exist_ok=True)

    bucket_names = [c["name"] for c in taxonomy.get("categories", [])]
    if not bucket_names:
        print("  ERROR: taxonomy has no categories — run Sweep 0 first")
        return 0

    folders = get_video_folders(videos_dir)

    # Skip videos that already have a .jsonl (even empty = skip, was processed)
    done_names = {f.stem for f in extractions_dir.glob("*.jsonl")}
    todo = [f for f in folders if f.name not in done_names]

    print(
        f"  Sweep 1: {len(folders)} videos | {len(done_names)} done | {len(todo)} to extract",
        flush=True,
    )

    if limit:
        todo = todo[:limit]
        print(f"  Limited to first {limit}")

    if dry_run:
        print(f"  DRY RUN: would make {len(todo)} LLM calls (1 per video)")
        return 0

    if not todo:
        total = sum(count_jsonl_lines(f) for f in extractions_dir.glob("*.jsonl"))
        print(f"  Nothing new to extract. Total extractions so far: {total}")
        return total

    progress = load_progress(output_dir)

    for i, folder in enumerate(todo, 1):
        print(f"  [{i}/{len(todo)}] {folder.name}", flush=True, end=" ")
        t0 = time.time()

        extractions = await extract_video(folder, bucket_names, label=f"s1-v{i}")
        elapsed = time.time() - t0

        jsonl_path = extractions_dir / f"{folder.name}.jsonl"

        if not extractions:
            print(f"→ 0 extractions ({elapsed:.0f}s)")
            # Write empty file to mark as processed (skip on next run)
            jsonl_path.write_text("", encoding="utf-8")
            progress["sweep1_done"].append(folder.name)
            save_progress(output_dir, progress)
            await asyncio.sleep(1)
            continue

        lines = [json.dumps(e, ensure_ascii=False) for e in extractions]
        jsonl_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"→ {len(extractions)} extractions ({elapsed:.0f}s)")

        progress["sweep1_done"].append(folder.name)
        save_progress(output_dir, progress)

        # Small inter-video delay to avoid throttling
        await asyncio.sleep(2)

    # Count total across all JSONL files
    total = sum(count_jsonl_lines(f) for f in extractions_dir.glob("*.jsonl"))
    print(f"  Sweep 1 done — {total} total extractions across all videos")
    return total


# =============================================================================
# STANDALONE ENTRY
# =============================================================================

def main() -> None:
    ap = argparse.ArgumentParser(description="Sweep 1: Verbatim Extraction")
    ap.add_argument("--config", required=True)
    ap.add_argument("--limit", type=int, default=None, help="Process only first N videos")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = load_config(args.config)
    output_dir = Path(cfg["output_dir"])
    taxonomy_path = output_dir / "taxonomy.json"

    if not taxonomy_path.exists():
        print("ERROR: taxonomy.json not found. Run Sweep 0 first.")
        print(f"  Expected: {taxonomy_path}")
        sys.exit(1)

    taxonomy = json.loads(taxonomy_path.read_text(encoding="utf-8"))
    asyncio.run(run(cfg, taxonomy, limit=args.limit, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
