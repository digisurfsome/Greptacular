#!/usr/bin/env python3
"""
Stage 3: Consolidate transcripts into markdown files.
Usage: python consolidate.py

Outputs:
  docs/info/jeremy-miner-corpus/videos/<sub-folder-name>/all-transcripts.md
  docs/info/jeremy-miner-corpus/videos/_video-index.md

Per-video format in concatenated MD:
  ## <video filename without extension>
  <transcript text>
  ---
"""

import json
from pathlib import Path
from datetime import datetime

AUDIO_ROOT  = Path(r"E:\AutoForge\jeremy-audio")
# Resolve docs output relative to this script: scripts/transcription/ → repo root
REPO_ROOT   = Path(__file__).parent.parent.parent
CORPUS_ROOT = REPO_ROOT / "docs" / "info" / "jeremy-miner-corpus" / "videos"
INDEX_PATH  = CORPUS_ROOT / "_video-index.md"


def parse_duration_from_json(json_path: Path) -> float:
    """Extract duration seconds from a Deepgram .json sidecar."""
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        if "metadata" in data and "duration" in data["metadata"]:
            return float(data["metadata"]["duration"])
        utterances = data.get("results", {}).get("utterances", [])
        if utterances:
            return float(max(u["end"] for u in utterances))
    except Exception:
        pass
    return 0.0


def consolidate():
    if not AUDIO_ROOT.exists():
        print(f"ERROR: Audio root not found: {AUDIO_ROOT}")
        return

    CORPUS_ROOT.mkdir(parents=True, exist_ok=True)

    # Collect first-level subdirectories under AUDIO_ROOT (each = one section)
    subdirs = sorted(
        d for d in AUDIO_ROOT.iterdir()
        if d.is_dir() and not d.name.startswith("_")
    )

    if not subdirs:
        print(f"No section folders found under: {AUDIO_ROOT}")
        return

    index_rows   = []
    grand_words  = 0
    grand_dur    = 0.0

    for subdir in subdirs:
        txt_files = sorted(subdir.rglob("*.txt"))
        # Skip any index/manifest txt files
        txt_files = [f for f in txt_files if not f.name.startswith("_")]

        if not txt_files:
            print(f"SKIP (no .txt files): {subdir.name}")
            continue

        # Output: CORPUS_ROOT / <same relative path> / all-transcripts.md
        rel_to_audio = subdir.relative_to(AUDIO_ROOT)
        out_folder   = CORPUS_ROOT / rel_to_audio
        out_folder.mkdir(parents=True, exist_ok=True)
        out_file = out_folder / "all-transcripts.md"

        # Don't overwrite existing (per constraint: only add under videos/)
        if out_file.exists():
            print(f"EXISTS (keeping): {out_file}")
            # Still count for index
            try:
                existing = out_file.read_text(encoding="utf-8")
                word_count = len(existing.split())
            except Exception:
                word_count = 0
            index_rows.append({
                "folder":          str(rel_to_audio),
                "file_count":      len(txt_files),
                "word_count":      word_count,
                "runtime_minutes": 0.0,
                "output":          str(out_file),
            })
            continue

        md_lines   = [f"# {subdir.name}\n\n"]
        word_count = 0
        dur_sec    = 0.0

        for txt_path in txt_files:
            stem = txt_path.stem
            try:
                content = txt_path.read_text(encoding="utf-8").strip()
            except Exception as e:
                content = f"[ERROR reading transcript: {e}]"

            md_lines.append(f"## {stem}\n\n{content}\n\n---\n\n")
            word_count += len(content.split())

            # Duration from JSON sidecar
            json_path = txt_path.with_suffix(".json")
            if json_path.exists():
                dur_sec += parse_duration_from_json(json_path)

        out_file.write_text("".join(md_lines), encoding="utf-8")

        grand_words += word_count
        grand_dur   += dur_sec

        index_rows.append({
            "folder":          str(rel_to_audio),
            "file_count":      len(txt_files),
            "word_count":      word_count,
            "runtime_minutes": round(dur_sec / 60, 1),
            "output":          str(out_file),
        })
        print(
            f"Written: {out_file}\n"
            f"  → {len(txt_files)} videos | {word_count:,} words | {dur_sec/60:.1f} min"
        )

    if not index_rows:
        print("No transcripts found to consolidate.")
        return

    # ── Master index ──────────────────────────────────────────────────────────
    total_files = sum(r["file_count"] for r in index_rows)
    lines = [
        "# Jeremy Miner Video Transcript Index\n\n",
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n\n",
        f"**Total:** {total_files} videos | "
        f"{grand_words:,} words | "
        f"{grand_dur / 60:.1f} minutes ({grand_dur / 3600:.2f} hrs)\n\n",
        "| Folder | Videos | Words | Runtime (min) | Output file |\n",
        "|--------|--------|-------|---------------|-------------|\n",
    ]
    for row in index_rows:
        lines.append(
            f"| {row['folder']} | {row['file_count']} | {row['word_count']:,} | "
            f"{row['runtime_minutes']} | {row['output']} |\n"
        )

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text("".join(lines), encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"Master index: {INDEX_PATH}")
    print(f"Totals: {total_files} videos | {grand_words:,} words | {grand_dur/3600:.2f} hrs")


if __name__ == "__main__":
    consolidate()
