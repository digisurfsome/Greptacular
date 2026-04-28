#!/usr/bin/env python3
"""
Transcribe a single audio file (any format ffmpeg handles, or raw .mp3).
Usage: python transcribe_single.py "<input_file>" "<output_folder>"

Output:
  <output_folder>/<stem>.txt   — clean transcript
  <output_folder>/<stem>.json  — full Deepgram response
  <output_folder>/all-transcripts.md — consolidated markdown

Reads DEEPGRAM_API_KEY from env or nearest .env file.
"""

import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path

# ── locate .env ──────────────────────────────────────────────────────────────
def load_api_key():
    key = os.environ.get("DEEPGRAM_API_KEY", "").strip()
    if key:
        return key
    search = [Path(__file__).parent, Path(__file__).parent.parent,
              Path(__file__).parent.parent.parent, Path.cwd()]
    for d in search:
        env = d / ".env"
        if env.exists():
            for line in env.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("DEEPGRAM_API_KEY"):
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        v = parts[1].strip().strip('"').strip("'")
                        if v:
                            return v
    return ""

# ── extract to mp3 if not already mp3 ────────────────────────────────────────
def ensure_mp3(input_path: Path) -> tuple[Path, bool]:
    """Returns (mp3_path, was_temp). Caller must delete temp if was_temp."""
    if input_path.suffix.lower() == ".mp3":
        return input_path, False
    tmp = Path(tempfile.mktemp(suffix=".mp3"))
    print(f"Converting {input_path.name} → temp mp3 via ffmpeg...")
    result = subprocess.run(
        ["ffmpeg", "-i", str(input_path), "-vn", "-ar", "16000",
         "-ac", "1", "-b:a", "32k", "-y", str(tmp)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"ffmpeg error:\n{result.stderr}")
        sys.exit(1)
    return tmp, True

# ── transcribe ────────────────────────────────────────────────────────────────
def transcribe(mp3_path: Path, api_key: str) -> dict:
    import urllib.request
    url = ("https://api.deepgram.com/v1/listen"
           "?model=nova-3&smart_format=true&punctuate=true&utterances=true")
    with open(mp3_path, "rb") as f:
        audio_bytes = f.read()

    file_size_mb = len(audio_bytes) / (1024 * 1024)
    print(f"Uploading {file_size_mb:.1f} MB to Deepgram Nova-3...")

    req = urllib.request.Request(
        url,
        data=audio_bytes,
        headers={
            "Authorization": f"Token {api_key}",
            "Content-Type": "audio/mpeg",
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        return json.loads(resp.read().decode("utf-8"))

# ── main ──────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 3:
        print("Usage: python transcribe_single.py <input_file> <output_folder>")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    output_folder = Path(sys.argv[2])

    if not input_file.exists():
        print(f"File not found: {input_file}")
        sys.exit(1)

    api_key = load_api_key()
    if not api_key:
        print("DEEPGRAM_API_KEY not found. Set env var or create .env at repo root.")
        sys.exit(1)

    output_folder.mkdir(parents=True, exist_ok=True)
    stem = input_file.stem

    # Skip if already done
    txt_out = output_folder / f"{stem}.txt"
    if txt_out.exists():
        print(f"Already transcribed: {txt_out}. Delete it to redo.")
        sys.exit(0)

    # Convert to mp3 if needed
    mp3_path, was_temp = ensure_mp3(input_file)

    try:
        data = transcribe(mp3_path, api_key)
    finally:
        if was_temp and mp3_path.exists():
            mp3_path.unlink()

    # Extract transcript
    try:
        transcript = data["results"]["channels"][0]["alternatives"][0]["transcript"]
    except (KeyError, IndexError) as e:
        print(f"Unexpected Deepgram response structure: {e}")
        print(json.dumps(data, indent=2)[:500])
        sys.exit(1)

    # Get duration for cost calc
    try:
        duration_s = data["metadata"]["duration"]
        cost = duration_s * (0.0043 / 60)
    except Exception:
        duration_s = 0
        cost = 0

    # Save .txt and .json
    txt_out.write_text(transcript, encoding="utf-8")
    json_out = output_folder / f"{stem}.json"
    json_out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    # Write consolidated markdown
    md_out = output_folder / "all-transcripts.md"
    with open(md_out, "w", encoding="utf-8") as f:
        f.write(f"# {output_folder.name}\n\n")
        f.write(f"## {stem}\n\n")
        f.write(transcript)
        f.write("\n\n---\n")

    word_count = len(transcript.split())
    duration_min = duration_s / 60 if duration_s else 0

    print()
    print("=" * 60)
    print(f"  File:      {input_file.name}")
    print(f"  Duration:  {duration_min:.1f} min")
    print(f"  Words:     {word_count:,}")
    print(f"  Cost:      ${cost:.4f}")
    print(f"  Transcript: {txt_out}")
    print(f"  Markdown:   {md_out}")
    print("=" * 60)

if __name__ == "__main__":
    main()
