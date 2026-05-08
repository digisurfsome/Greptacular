#!/usr/bin/env python3
"""
YouTube auto-transcript batch puller — FREE, INSTANT.

Walks a videos folder (e.g. E:/AutoForge/lsa_videos/) where each subfolder
contains a transcript.info.json (written by yt-dlp --write-info-json).

For each video:
  1. Read video_id from transcript.info.json
  2. If transcript.txt already exists and is non-empty → skip (resumable)
  3. Pull YouTube auto-captions via youtube-transcript-api
  4. Write transcript.txt next to the .info.json
  5. If no captions available → log to _deepgram_fallback.txt for paid run

Usage:
    python youtube_transcript_batch.py "E:/AutoForge/lsa_videos"

Cost: $0. Speed: ~1 sec per video.
"""

import sys
import json
from pathlib import Path

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (
        TranscriptsDisabled,
        NoTranscriptFound,
        VideoUnavailable,
    )
except ImportError:
    print("ERROR: youtube-transcript-api not installed.")
    print("Install: pip install youtube-transcript-api")
    sys.exit(1)


def get_video_id(info_json_path: Path) -> str | None:
    try:
        data = json.loads(info_json_path.read_text(encoding="utf-8"))
        return data.get("id")
    except Exception:
        return None


def fetch_transcript(video_id: str) -> tuple[str | None, str]:
    """Returns (transcript_text, status). status one of: ok, disabled, none, unavailable, error"""
    try:
        entries = YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "en-US", "en-GB"])
        text = " ".join(e["text"].strip() for e in entries if e.get("text"))
        text = text.replace("\n", " ").strip()
        return text, "ok"
    except TranscriptsDisabled:
        return None, "disabled"
    except NoTranscriptFound:
        return None, "none"
    except VideoUnavailable:
        return None, "unavailable"
    except Exception as e:
        return None, f"error: {type(e).__name__}: {e}"


def main():
    if len(sys.argv) < 2:
        print("Usage: python youtube_transcript_batch.py <videos_folder>")
        sys.exit(1)

    videos_dir = Path(sys.argv[1])
    if not videos_dir.exists():
        print(f"FATAL: folder not found: {videos_dir}")
        sys.exit(1)

    info_files = sorted(videos_dir.rglob("transcript.info.json"))
    # Exclude the playlist-level metadata file (no 'id' as a video)
    video_info_files = []
    for p in info_files:
        # Skip the playlist's own transcript.info.json (in NA_LSA_Ads_Skool_Group folder)
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if data.get("_type") == "playlist":
                continue
            if not data.get("id"):
                continue
            video_info_files.append(p)
        except Exception:
            continue

    print(f"Found {len(video_info_files)} videos in {videos_dir}\n")

    fallback_log = videos_dir / "_deepgram_fallback.txt"
    fallback_lines = []
    ok = skipped = failed = 0

    for i, info_path in enumerate(video_info_files, 1):
        folder = info_path.parent
        txt_path = folder / "transcript.txt"
        video_id = get_video_id(info_path)
        label = f"[{i}/{len(video_info_files)}] {folder.name[:60]}"

        if txt_path.exists() and txt_path.stat().st_size > 200:
            print(f"{label}  SKIP (already have transcript.txt)")
            skipped += 1
            continue

        if not video_id:
            print(f"{label}  ! no video_id in info.json")
            failed += 1
            fallback_lines.append(f"{folder}  (no video_id)")
            continue

        text, status = fetch_transcript(video_id)
        if text and len(text) > 200:
            txt_path.write_text(text, encoding="utf-8")
            print(f"{label}  OK ({len(text):,} chars)")
            ok += 1
        else:
            print(f"{label}  FAIL ({status}) -> needs Deepgram")
            failed += 1
            fallback_lines.append(f"{folder}  ({status})")

    if fallback_lines:
        fallback_log.write_text(
            "Videos that need Deepgram fallback (no YouTube captions available):\n\n"
            + "\n".join(fallback_lines)
            + "\n",
            encoding="utf-8",
        )

    print(f"\n{'='*60}")
    print(f"  OK: {ok}  |  Skipped: {skipped}  |  Need Deepgram: {failed}")
    print(f"{'='*60}")
    if fallback_lines:
        print(f"\nFallback list written to: {fallback_log}")
        print(f"For those videos, run: python scripts/transcription/transcribe_deepgram.py \"{videos_dir}\"")
        print("(Deepgram script skips folders that already have transcript.txt — only fallback set runs.)")


if __name__ == "__main__":
    main()
