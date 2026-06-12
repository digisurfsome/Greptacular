#!/usr/bin/env python3
"""
Stage 1: Audio extraction from video files using ffmpeg.
Usage: python extract_audio.py "<input-folder>"
Output mirrors structure under E:\\AutoForge\\jeremy-audio\\

Features:
- Skip if mp3 already exists (resumable)
- Progress: "[3/53] Extracting: filename.mp4"
- On error: log to extract_errors.log, continue
- Manifest at E:\\AutoForge\\jeremy-audio\\_manifest.json
"""

import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path

OUTPUT_ROOT = Path(r"E:\AutoForge\jeremy-audio")
MANIFEST_PATH = OUTPUT_ROOT / "_manifest.json"
ERROR_LOG = OUTPUT_ROOT / "extract_errors.log"
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".ts"}


def setup_logging():
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=str(ERROR_LOG),
        level=logging.ERROR,
        format="%(asctime)s - %(message)s"
    )


def load_manifest():
    if MANIFEST_PATH.exists():
        try:
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_manifest(manifest):
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def get_duration(path):
    """Get duration in seconds using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(path)
            ],
            capture_output=True, text=True, timeout=30
        )
        val = result.stdout.strip()
        return float(val) if val else 0.0
    except Exception:
        return 0.0


def extract_audio(input_folder_str):
    input_folder = Path(input_folder_str).resolve()
    if not input_folder.exists():
        print(f"ERROR: Input folder not found: {input_folder}")
        sys.exit(1)

    setup_logging()

    # Collect all video files
    videos = []
    for ext in VIDEO_EXTENSIONS:
        videos.extend(input_folder.rglob(f"*{ext}"))
    videos = sorted(set(videos))

    total = len(videos)
    if total == 0:
        print(f"No video files found in: {input_folder}")
        return

    print(f"Found {total} video file(s) in: {input_folder}")
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()

    for idx, video_path in enumerate(videos, 1):
        # Output path: OUTPUT_ROOT / <input_folder.name> / relative_subpath.mp3
        rel = video_path.relative_to(input_folder)
        out_path = OUTPUT_ROOT / input_folder.name / rel.with_suffix(".mp3")
        out_path.parent.mkdir(parents=True, exist_ok=True)

        key = str(out_path)
        print(f"[{idx}/{total}] Extracting: {video_path.name}")

        if out_path.exists():
            print(f"  → SKIP (already exists): {out_path.name}")
            if key not in manifest:
                dur = get_duration(out_path)
                manifest[key] = {
                    "source": str(video_path),
                    "output": key,
                    "duration_seconds": dur,
                    "file_size_bytes": out_path.stat().st_size,
                    "status": "exists",
                    "timestamp": datetime.utcnow().isoformat()
                }
                save_manifest(manifest)
            continue

        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-vn",
            "-ar", "16000",
            "-ac", "1",
            "-b:a", "32k",
            "-y",
            str(out_path)
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=7200
            )
            if result.returncode != 0:
                stderr_tail = result.stderr[-600:] if result.stderr else "no stderr"
                raise RuntimeError(f"ffmpeg exit {result.returncode}: {stderr_tail}")

            dur = get_duration(out_path)
            size = out_path.stat().st_size

            manifest[key] = {
                "source": str(video_path),
                "output": key,
                "duration_seconds": dur,
                "file_size_bytes": size,
                "status": "success",
                "timestamp": datetime.utcnow().isoformat()
            }
            print(f"  → OK: {out_path.name} ({dur:.0f}s, {size // 1024}KB)")

        except Exception as e:
            err_msg = str(e)
            print(f"  → ERROR: {err_msg[:200]}")
            logging.error(f"FAILED: {video_path} | {err_msg}")
            manifest[key] = {
                "source": str(video_path),
                "output": key,
                "duration_seconds": 0.0,
                "file_size_bytes": 0,
                "status": "error",
                "error": err_msg[:400],
                "timestamp": datetime.utcnow().isoformat()
            }

        save_manifest(manifest)

    # Summary
    entries = list(manifest.values())
    success = sum(1 for v in entries if v["status"] in ("success", "exists"))
    errors  = sum(1 for v in entries if v["status"] == "error")
    total_dur = sum(v.get("duration_seconds", 0) for v in entries)
    print(f"\n{'='*60}")
    print(f"Extraction complete: {success} OK, {errors} errors")
    print(f"Total audio: {total_dur / 3600:.2f} hrs")
    print(f"Manifest:    {MANIFEST_PATH}")
    if errors:
        print(f"Error log:   {ERROR_LOG}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_audio.py \"<input-folder>\"")
        sys.exit(1)
    extract_audio(sys.argv[1])
