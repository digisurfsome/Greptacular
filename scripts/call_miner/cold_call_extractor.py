#!/usr/bin/env python3
"""
cold_call_extractor.py — Direct cold-call corpus builder.

Reads cold-call transcript folders, extracts every exchange pair verbatim
via Claude, and writes a structured cold_call_corpus.md.

No sweeps, no registry, no taxonomy gate, no silent failures.

Usage:
    python scripts/call_miner/cold_call_extractor.py \
      --videos "output/videos" \
      --output "output/cold_call_corpus.md" \
      --keywords cold-call cold-calling live calling demo
"""

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Prevent CLAUDECODE=1 poisoning nested claude processes (exit 11)
os.environ.pop("CLAUDECODE", None)

# Sibling import: channel_brain/_claude.py
sys.path.insert(0, str(Path(__file__).parent.parent / "channel_brain"))
from _claude import call_claude_stdin, preflight, parse_json, preprocess_transcript  # noqa: E402

# ---------------------------------------------------------------------------
# Tiktoken for transcript chunking
# ---------------------------------------------------------------------------
try:
    import tiktoken
    _ENC = tiktoken.get_encoding("cl100k_base")

    def _token_count(s: str) -> int:
        return len(_ENC.encode(s))

    def _chunk_text(text: str, max_tokens: int, overlap: int) -> list[str]:
        tokens = _ENC.encode(text)
        chunks: list[str] = []
        i = 0
        while i < len(tokens):
            chunk_tokens = tokens[i : i + max_tokens]
            chunks.append(_ENC.decode(chunk_tokens))
            i += max_tokens - overlap
        return chunks

    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

    def _token_count(s: str) -> int:
        return len(s) // 4  # rough estimate

    def _chunk_text(text: str, max_tokens: int, overlap: int) -> list[str]:
        # Char-based fallback (~4 chars per token)
        size = max_tokens * 4
        step = (max_tokens - overlap) * 4
        return [text[i : i + size] for i in range(0, len(text), step)] or [text]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CHUNK_TOKENS = 1500    # tokens per Claude call
CHUNK_OVERLAP = 200    # token overlap between chunks
CHUNK_CHAR_CAP = 5000  # char threshold above which we chunk

EXTRACTION_PROMPT_LABELED = """\
You are reading a transcript of a real sales call or cold call recording.
Speakers are labeled: SELLER = salesperson, PROSPECT = customer/lead.

Extract EVERY exchange where PROSPECT says something and SELLER responds.
Capture VERBATIM — exact words, no paraphrasing, no summarizing.
Include ALL exchanges — openers, objections, questions, small talk that advances the call, closes.
Do NOT skip exchanges because they seem minor or repetitive.

For each exchange, assign ONE label from this list:
  opener, missed-call-pitch, pricing-objection, ai-skepticism, human-touch-objection,
  competitor-mention, discovery-question, demo-request, close-attempt, misc

Return ONLY raw JSON, no markdown fences:
{
  "exchanges": [
    {
      "prospect": "exact PROSPECT words verbatim",
      "sales": "exact SELLER response verbatim",
      "label": "one label from the list above"
    }
  ]
}

If this is clearly NOT a sales call (tutorial, monologue, no PROSPECT lines), return:
{"exchanges": [], "not_a_call": true}

TRANSCRIPT:
"""

EXTRACTION_PROMPT_PLAIN = """\
You are reading a transcript of a real sales call or cold call recording.
There are no speaker labels — infer who is the salesperson vs the prospect from context.
The salesperson is usually asking questions, pitching, handling objections.
The prospect is usually asking questions, expressing doubts, or responding briefly.

Extract EVERY exchange where a prospect/customer says something and the salesperson responds.
Capture VERBATIM — exact words, no paraphrasing, no summarizing.
Include ALL exchanges — openers, objections, questions, small talk that advances the call, closes.
Do NOT skip exchanges because they seem minor or repetitive.

For each exchange, assign ONE label from this list:
  opener, missed-call-pitch, pricing-objection, ai-skepticism, human-touch-objection,
  competitor-mention, discovery-question, demo-request, close-attempt, misc

Return ONLY raw JSON, no markdown fences:
{
  "exchanges": [
    {
      "prospect": "exact prospect words verbatim",
      "sales": "exact salesperson response verbatim",
      "label": "one label from the list above"
    }
  ]
}

If this is clearly NOT a sales call (tutorial, monologue, no dialogue), return:
{"exchanges": [], "not_a_call": true}

TRANSCRIPT:
"""

VALID_LABELS = {
    "opener", "missed-call-pitch", "pricing-objection", "ai-skepticism",
    "human-touch-objection", "competitor-mention", "discovery-question",
    "demo-request", "close-attempt", "misc",
}


# ---------------------------------------------------------------------------
# Sidecar tracking — _extracted.json next to output .md
# ---------------------------------------------------------------------------

def sidecar_path(output_path: Path) -> Path:
    return output_path.parent / "_extracted.json"


def load_sidecar(output_path: Path) -> dict:
    sp = sidecar_path(output_path)
    if sp.exists():
        try:
            return json.loads(sp.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_sidecar(output_path: Path, data: dict) -> None:
    sp = sidecar_path(output_path)
    sp.parent.mkdir(parents=True, exist_ok=True)
    sp.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Video discovery
# ---------------------------------------------------------------------------

def find_matching_videos(videos_dir: Path, keywords: list[str]) -> list[Path]:
    """Return sorted list of video folders whose name matches any keyword."""
    if not videos_dir.is_dir():
        print(f"FATAL: videos directory does not exist: {videos_dir}")
        sys.exit(1)

    folders = sorted(
        d for d in videos_dir.iterdir()
        if d.is_dir() and (d / "transcript.txt").exists()
    )

    if not keywords:
        return folders

    lower_keywords = [kw.lower() for kw in keywords]
    matched = [
        f for f in folders
        if any(kw in f.name.lower() for kw in lower_keywords)
    ]
    return matched


def video_title(folder: Path) -> str:
    """Extract human-readable title from info.md or folder name."""
    info_path = folder / "info.md"
    if info_path.exists():
        first_line = info_path.read_text(encoding="utf-8", errors="replace").split("\n")[0].strip()
        # Strip leading markdown heading markers
        title = first_line.lstrip("# ").strip()
        if title:
            return title
    # Fallback: clean up folder name
    return folder.name.replace("-", " ").replace("_", " ").title()


# ---------------------------------------------------------------------------
# Exchange extraction
# ---------------------------------------------------------------------------

def _parse_exchanges(raw: str) -> list[dict]:
    """Parse Claude response into a list of exchange dicts."""
    parsed = parse_json(raw)
    if parsed is None:
        return []

    if isinstance(parsed, dict):
        # {"exchanges": [...], "not_a_call": true} case
        if parsed.get("not_a_call"):
            return []
        exchanges = parsed.get("exchanges", [])
    elif isinstance(parsed, list):
        exchanges = parsed
    else:
        return []

    valid: list[dict] = []
    for ex in exchanges:
        if not isinstance(ex, dict):
            continue
        prospect = str(ex.get("prospect", "")).strip()
        sales = str(ex.get("sales", "")).strip()
        label = str(ex.get("label", "misc")).strip().lower()
        if not prospect or not sales:
            continue
        # Normalize label — fall back to misc if invalid
        if label not in VALID_LABELS:
            label = "misc"
        valid.append({"prospect": prospect, "sales": sales, "label": label})
    return valid


async def extract_from_video(folder: Path, label: str) -> list[dict]:
    """Extract all exchanges from one video folder's transcript."""
    t_path = folder / "transcript.txt"
    raw_transcript = t_path.read_text(encoding="utf-8", errors="replace").strip()

    if len(raw_transcript) < 200:
        print(f"  skipping — transcript too short ({len(raw_transcript)} chars)")
        return []

    # Detect speaker format, extract call window, normalize labels
    transcript, fmt = preprocess_transcript(raw_transcript)
    prompt_template = EXTRACTION_PROMPT_PLAIN if fmt == "plain" else EXTRACTION_PROMPT_LABELED

    if fmt != "plain":
        # Show how much narration we stripped
        stripped = len(raw_transcript) - len(transcript)
        if stripped > 200:
            print(f"[{fmt}, stripped {stripped:,} chars narration] ", end="", flush=True)
        else:
            print(f"[{fmt}] ", end="", flush=True)

    # Short transcripts: single call
    if len(transcript) <= CHUNK_CHAR_CAP:
        prompt = prompt_template + transcript
        raw = await call_claude_stdin(prompt, label=label)
        if not raw:
            raise RuntimeError("Claude returned empty response")
        exchanges = _parse_exchanges(raw)
        return exchanges

    # Long transcripts: chunk to avoid exit 15
    chunks = _chunk_text(transcript, max_tokens=CHUNK_TOKENS, overlap=CHUNK_OVERLAP)
    print(f"({len(transcript):,} chars -> {len(chunks)} chunks)", end=" ", flush=True)

    all_exchanges: list[dict] = []
    seen_pairs: set[tuple[str, str]] = set()  # dedup across chunk boundaries

    for ci, chunk in enumerate(chunks):
        chunk_label = f"{label}-c{ci + 1}"
        prompt = prompt_template + chunk
        raw = await call_claude_stdin(prompt, label=chunk_label)
        if not raw:
            print(f"  chunk {ci + 1}/{len(chunks)} returned nothing", flush=True)
            continue
        chunk_exchanges = _parse_exchanges(raw)
        for ex in chunk_exchanges:
            # Dedup by first 80 chars of prospect + sales
            key = (ex["prospect"][:80], ex["sales"][:80])
            if key not in seen_pairs:
                seen_pairs.add(key)
                all_exchanges.append(ex)
        # Brief pause between chunks to avoid rate limiting
        if ci < len(chunks) - 1:
            await asyncio.sleep(1)

    return all_exchanges


# ---------------------------------------------------------------------------
# Markdown output
# ---------------------------------------------------------------------------

def format_video_section(
    video_num: int,
    title: str,
    folder_name: str,
    exchanges: list[dict],
) -> str:
    """Format one video's exchanges as a markdown section."""
    lines: list[str] = []
    lines.append(f"## [V{video_num:03d}] {title}")
    lines.append(f"**File:** {folder_name}")
    lines.append(f"**Extracted:** {len(exchanges)} exchanges")
    lines.append("")

    # Group exchanges by label, preserving original order within each group
    label_groups: dict[str, list[dict]] = {}
    for ex in exchanges:
        label_groups.setdefault(ex["label"], []).append(ex)

    for label, group in label_groups.items():
        for ex in group:
            lines.append(f"### {label}")
            lines.append(f"**PROSPECT:** {ex['prospect']}")
            lines.append(f"**SALES:** {ex['sales']}")
            lines.append("")
            lines.append("---")
            lines.append("")

    return "\n".join(lines)


def write_header(
    output_path: Path,
    total_videos: int,
    total_exchanges: int,
    video_summaries: list[dict],
) -> None:
    """Write the corpus header with summary table."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = []
    lines.append("# Cold Call Corpus")
    lines.append(f"Generated: {now}  |  Videos: {total_videos}  |  Exchanges: {total_exchanges}")
    lines.append("")
    lines.append("| # | Video | Exchanges | Labels |")
    lines.append("|---|-------|-----------|--------|")
    for vs in video_summaries:
        labels_str = ", ".join(sorted(vs["labels"])) if vs["labels"] else "none"
        lines.append(f"| V{vs['num']:03d} | {vs['title'][:50]} | {vs['exchanges']} | {labels_str} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def append_video_section(output_path: Path, section: str) -> None:
    """Append a video section to the output file."""
    with open(output_path, "a", encoding="utf-8") as f:
        f.write(section)
        f.write("\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Cold call corpus builder — extract exchanges from transcripts"
    )
    parser.add_argument(
        "--videos", required=True,
        help="Path to folder of video subfolders (each has transcript.txt)",
    )
    parser.add_argument(
        "--output", required=True,
        help="Path to output .md file",
    )
    parser.add_argument(
        "--keywords", nargs="+", default=[],
        help="Only process videos whose folder name contains one of these strings",
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Wipe sidecar and start over",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="List matching videos without calling Claude",
    )
    args = parser.parse_args()

    videos_dir = Path(args.videos).resolve()
    output_path = Path(args.output).resolve()

    # Find matching videos
    matched = find_matching_videos(videos_dir, args.keywords)
    if not matched:
        print("No matching videos found.")
        if args.keywords:
            print(f"  Keywords: {args.keywords}")
            all_folders = sorted(
                d.name for d in videos_dir.iterdir()
                if d.is_dir() and (d / "transcript.txt").exists()
            )
            print(f"  Available folders ({len(all_folders)}):")
            for name in all_folders[:20]:
                print(f"    {name}")
            if len(all_folders) > 20:
                print(f"    ... and {len(all_folders) - 20} more")
        sys.exit(0)

    print(f"Found {len(matched)} matching videos in {videos_dir}")

    # Dry run — list and exit
    if args.dry_run:
        print("\n-- DRY RUN — would process these videos --")
        for i, folder in enumerate(matched, 1):
            t_path = folder / "transcript.txt"
            chars = len(t_path.read_text(encoding="utf-8", errors="replace"))
            title = video_title(folder)
            chunks_est = max(1, chars // (CHUNK_TOKENS * 4)) if chars > CHUNK_CHAR_CAP else 1
            print(f"  [{i}/{len(matched)}] {title}")
            print(f"           folder: {folder.name}")
            print(f"           chars: {chars:,}  (est. {chunks_est} chunk{'s' if chunks_est > 1 else ''})")
        print(f"\nTotal: {len(matched)} videos. Use without --dry-run to extract.")
        return

    # Handle sidecar / reset
    if args.reset:
        sp = sidecar_path(output_path)
        if sp.exists():
            sp.unlink()
            print("Sidecar reset.")
        if output_path.exists():
            output_path.unlink()
            print("Output file reset.")

    sidecar = load_sidecar(output_path)

    # Filter out already-extracted videos
    remaining = [f for f in matched if f.name not in sidecar]
    already_done = len(matched) - len(remaining)
    if already_done > 0:
        print(f"Skipping {already_done} already-extracted videos (use --reset to redo all)")
    if not remaining:
        print("All matching videos already extracted. Nothing to do.")
        return

    # Preflight auth check
    await preflight()

    # If output file doesn't exist yet, create it with a placeholder header
    # We'll rewrite the header at the end with accurate totals
    if not output_path.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("", encoding="utf-8")

    # Track results for summary table
    video_summaries: list[dict] = []

    # Rebuild summaries from sidecar for already-done videos
    for i, folder in enumerate(matched, 1):
        if folder.name in sidecar:
            entry = sidecar[folder.name]
            video_summaries.append({
                "num": i,
                "title": video_title(folder),
                "exchanges": entry.get("exchanges", 0),
                "labels": set(entry.get("labels", [])),
            })

    total_exchanges = sum(vs["exchanges"] for vs in video_summaries)
    success_count = len(video_summaries)
    fail_count = 0

    # Process remaining videos
    for idx, folder in enumerate(remaining):
        # Compute the global video number (position in full matched list)
        global_num = matched.index(folder) + 1
        title = video_title(folder)
        t_path = folder / "transcript.txt"
        chars = len(t_path.read_text(encoding="utf-8", errors="replace"))

        chunks_est = max(1, chars // (CHUNK_TOKENS * 4)) if chars > CHUNK_CHAR_CAP else 1
        progress = f"[{idx + 1 + already_done}/{len(matched)}]"
        print(
            f"{progress} {title} ({chars:,} chars -> {chunks_est} chunk{'s' if chunks_est > 1 else ''}) ... ",
            end="", flush=True,
        )

        t_start = time.monotonic()
        try:
            exchanges = await extract_from_video(folder, label=f"v{global_num}")
            elapsed = time.monotonic() - t_start

            if not exchanges:
                print(f"0 exchanges ({elapsed:.0f}s) — possibly not a sales call")
            else:
                print(f"{len(exchanges)} exchanges ({elapsed:.0f}s)")

            # Build section and append to output
            section = format_video_section(global_num, title, folder.name, exchanges)
            append_video_section(output_path, section)

            # Update sidecar — only on success
            labels_found = sorted(set(ex["label"] for ex in exchanges))
            sidecar[folder.name] = {
                "exchanges": len(exchanges),
                "labels": labels_found,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            save_sidecar(output_path, sidecar)

            video_summaries.append({
                "num": global_num,
                "title": title,
                "exchanges": len(exchanges),
                "labels": set(labels_found),
            })
            total_exchanges += len(exchanges)
            success_count += 1

        except Exception as e:
            elapsed = time.monotonic() - t_start
            fail_count += 1
            print(f"FAILED — {e} ({elapsed:.0f}s). Skipping.")

    # Rewrite the file with proper header + all sections
    # Read existing sections (everything after the header)
    _rewrite_with_header(output_path, video_summaries, total_exchanges)

    # Final summary
    print(f"\nDone. {success_count}/{len(matched)} videos extracted. "
          f"{total_exchanges} exchanges. Output: {output_path}")
    if fail_count > 0:
        print(f"  {fail_count} video(s) failed — check output above for details.")


def _rewrite_with_header(
    output_path: Path,
    video_summaries: list[dict],
    total_exchanges: int,
) -> None:
    """Rewrite the output file with a proper header followed by all video sections."""
    # Read current content — may include sections appended during this run
    # plus content from prior runs
    current = output_path.read_text(encoding="utf-8")

    # Find where the video sections start (first ## [V...)
    section_start = current.find("## [V")
    sections = current[section_start:] if section_start >= 0 else ""

    # Build new header
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    header_lines: list[str] = []
    header_lines.append("# Cold Call Corpus")
    header_lines.append(
        f"Generated: {now}  |  Videos: {len(video_summaries)}  |  Exchanges: {total_exchanges}"
    )
    header_lines.append("")
    header_lines.append("| # | Video | Exchanges | Labels |")
    header_lines.append("|---|-------|-----------|--------|")
    for vs in sorted(video_summaries, key=lambda x: x["num"]):
        labels_str = ", ".join(sorted(vs["labels"])) if vs["labels"] else "none"
        title_trunc = vs["title"][:50]
        header_lines.append(
            f"| V{vs['num']:03d} | {title_trunc} | {vs['exchanges']} | {labels_str} |"
        )
    header_lines.append("")
    header_lines.append("---")
    header_lines.append("")

    output_path.write_text("\n".join(header_lines) + sections, encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
