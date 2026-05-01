#!/usr/bin/env python3
"""
transcribe_call.py — YouTube URL to diarized transcript

Downloads audio from a YouTube URL via yt-dlp, sends to Deepgram Nova-3
for diarized transcription, and writes a speaker-labeled transcript file.

Output format:
    [SPEAKER_0 00:00:03]: Hello, is this John?
    [SPEAKER_1 00:00:05]: Yeah, who's this?

Slug generation: {yt_video_id}-{sanitized-title-first-5-words}

Usage:
    cd C:\\Users\\lober\\.autoforge\\workspace\\repos\\digisurfsome__Greptacular
    python scripts/jeremy/transcribe_call.py {youtube_url} --output {path}

Requirements:
    pip install yt-dlp
    ffmpeg on PATH
    DEEPGRAM_API_KEY in .env or environment
"""

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import time
import urllib.request
import urllib.error
from pathlib import Path


# ── Load .env (no python-dotenv required) ────────────────────────────────────
def _load_dotenv() -> None:
    for candidate in [
        Path(".env"),
        Path(__file__).parent / ".env",
        Path(__file__).parent.parent.parent / ".env",
    ]:
        if candidate.exists():
            for line in candidate.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
            break


_load_dotenv()


# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY", "")
DEEPGRAM_URL = (
    "https://api.deepgram.com/v1/listen"
    "?model=nova-3"
    "&smart_format=true"
    "&diarize=true"
    "&utterances=true"
    "&punctuate=true"
)

# Retry backoff delays (seconds) for Deepgram 429 / transient errors
RETRY_DELAYS = [5, 10, 20, 40, 80]


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def extract_video_id(url: str) -> str:
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r"(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"(?:embed/)([a-zA-Z0-9_-]{11})",
        r"(?:shorts/)([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    # Last resort: assume the URL itself might be an ID
    if re.match(r"^[a-zA-Z0-9_-]{11}$", url):
        return url
    raise ValueError(f"Cannot extract video ID from: {url}")


def sanitize_for_slug(title: str) -> str:
    """Turn a video title into a slug-safe string (first 5 words)."""
    # Strip non-alphanumeric except spaces/hyphens
    cleaned = re.sub(r"[^a-zA-Z0-9\s-]", "", title.lower())
    words = cleaned.split()[:5]
    return "-".join(words) if words else "untitled"


def generate_slug(video_id: str, title: str) -> str:
    """Generate slug: {video_id}-{sanitized-title-first-5-words}."""
    return f"{video_id}-{sanitize_for_slug(title)}"


def format_timestamp(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format."""
    total = int(seconds)
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


# ══════════════════════════════════════════════════════════════════════════════
# YOUTUBE DOWNLOAD
# ══════════════════════════════════════════════════════════════════════════════

def download_audio(url: str, tmp_dir: str) -> tuple[str, str]:
    """Download audio from YouTube URL. Returns (audio_file_path, video_title).

    Uses yt-dlp to download best audio, post-processed to 16kHz mono WAV
    via ffmpeg for optimal Deepgram compatibility.
    """
    # Check yt-dlp is available
    ytdlp = shutil.which("yt-dlp")
    if not ytdlp:
        print("FATAL: yt-dlp not found on PATH.")
        print("       Install: pip install yt-dlp")
        sys.exit(2)

    # Check ffmpeg is available
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("FATAL: ffmpeg not found on PATH.")
        print("       Install: https://ffmpeg.org/download.html")
        sys.exit(2)

    output_template = os.path.join(tmp_dir, "%(id)s.%(ext)s")
    info_file = os.path.join(tmp_dir, "info.json")

    # First: get video info (title) without downloading
    import subprocess

    result = subprocess.run(
        [ytdlp, "--dump-json", "--no-download", url],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        print(f"FATAL: yt-dlp info fetch failed: {result.stderr[:300]}")
        sys.exit(2)

    info = json.loads(result.stdout)
    video_title = info.get("title", "Unknown Title")
    video_id = info.get("id", "unknown")

    print(f"  Video: {video_title}", flush=True)
    print(f"  ID:    {video_id}", flush=True)

    # Download audio and convert to 16kHz mono WAV
    audio_path = os.path.join(tmp_dir, f"{video_id}.wav")
    dl_result = subprocess.run(
        [
            ytdlp,
            "-x",                          # extract audio only
            "--audio-format", "wav",        # output as WAV
            "--postprocessor-args",
            "ffmpeg:-ar 16000 -ac 1",       # 16kHz mono
            "-o", output_template,
            url,
        ],
        capture_output=True, text=True, timeout=600,
    )

    if dl_result.returncode != 0:
        print(f"FATAL: yt-dlp download failed: {dl_result.stderr[:500]}")
        sys.exit(2)

    # Find the output file (yt-dlp may name it differently)
    wav_files = list(Path(tmp_dir).glob("*.wav"))
    if not wav_files:
        # Fallback: look for any audio file and convert
        audio_files = list(Path(tmp_dir).glob("*.*"))
        audio_files = [f for f in audio_files if f.suffix in (".m4a", ".webm", ".opus", ".mp3", ".ogg")]
        if not audio_files:
            print("FATAL: no audio file found after yt-dlp download")
            sys.exit(2)
        # Convert with ffmpeg
        src = str(audio_files[0])
        subprocess.run(
            [ffmpeg, "-i", src, "-ar", "16000", "-ac", "1", audio_path],
            capture_output=True, timeout=300,
        )
        if not os.path.exists(audio_path):
            print("FATAL: ffmpeg conversion failed")
            sys.exit(2)
    else:
        audio_path = str(wav_files[0])

    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    print(f"  Audio: {file_size_mb:.1f} MB WAV (16kHz mono)", flush=True)

    return audio_path, video_title


# ══════════════════════════════════════════════════════════════════════════════
# DEEPGRAM TRANSCRIPTION
# ══════════════════════════════════════════════════════════════════════════════

def transcribe_with_deepgram(audio_path: str) -> dict:
    """Send audio to Deepgram Nova-3 and return the JSON response.

    Retries on 429 (rate limit) with exponential backoff.
    Hard-stops on 401 (bad API key).
    """
    if not DEEPGRAM_API_KEY:
        print("FATAL: DEEPGRAM_API_KEY not set.")
        print("       Add to .env: DEEPGRAM_API_KEY=your_key_here")
        sys.exit(2)

    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    print(f"  Sending {len(audio_bytes) / (1024*1024):.1f} MB to Deepgram Nova-3 ...", flush=True)

    for attempt, delay in enumerate([0] + RETRY_DELAYS):
        if delay:
            print(f"  Retrying in {delay}s (attempt {attempt + 1}) ...", flush=True)
            time.sleep(delay)

        req = urllib.request.Request(
            DEEPGRAM_URL,
            data=audio_bytes,
            headers={
                "Authorization": f"Token {DEEPGRAM_API_KEY}",
                "Content-Type": "audio/wav",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=600) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body)

        except urllib.error.HTTPError as e:
            if e.code == 401:
                print("FATAL: Deepgram 401 Unauthorized — check your DEEPGRAM_API_KEY.")
                sys.exit(2)
            if e.code == 429 and attempt < len(RETRY_DELAYS):
                print(f"  Deepgram 429 rate limit — will retry ...", flush=True)
                continue
            error_body = e.read().decode("utf-8", errors="replace")[:300] if e.fp else ""
            print(f"FATAL: Deepgram HTTP {e.code}: {error_body}")
            sys.exit(2)

        except urllib.error.URLError as e:
            if attempt < len(RETRY_DELAYS):
                print(f"  Network error: {e.reason} — will retry ...", flush=True)
                continue
            print(f"FATAL: Network error calling Deepgram: {e.reason}")
            sys.exit(2)

    print("FATAL: exhausted all Deepgram retries")
    sys.exit(2)


def format_transcript(dg_response: dict) -> str:
    """Format Deepgram response into speaker-labeled transcript.

    Uses utterances (preferred) for diarized output. Falls back to
    plain transcript if diarization data is absent.
    """
    results = dg_response.get("results", {})

    # Try utterances first (best diarization output)
    utterances = results.get("utterances", [])
    if utterances:
        lines = []
        for utt in utterances:
            speaker = utt.get("speaker", 0)
            start = utt.get("start", 0.0)
            text = utt.get("transcript", "").strip()
            if text:
                ts = format_timestamp(start)
                lines.append(f"[SPEAKER_{speaker} {ts}]: {text}")
        if lines:
            return "\n".join(lines)

    # Fallback: try channel/alternatives with word-level speaker info
    channels = results.get("channels", [])
    if channels:
        alternatives = channels[0].get("alternatives", [])
        if alternatives:
            words = alternatives[0].get("words", [])
            if words and words[0].get("speaker") is not None:
                # Build utterances from word-level speaker changes
                lines = []
                current_speaker = None
                current_words = []
                current_start = 0.0

                for word in words:
                    speaker = word.get("speaker", 0)
                    if speaker != current_speaker:
                        if current_words:
                            ts = format_timestamp(current_start)
                            text = " ".join(current_words)
                            lines.append(f"[SPEAKER_{current_speaker} {ts}]: {text}")
                        current_speaker = speaker
                        current_words = [word.get("punctuated_word", word.get("word", ""))]
                        current_start = word.get("start", 0.0)
                    else:
                        current_words.append(word.get("punctuated_word", word.get("word", "")))

                if current_words:
                    ts = format_timestamp(current_start)
                    text = " ".join(current_words)
                    lines.append(f"[SPEAKER_{current_speaker} {ts}]: {text}")

                if lines:
                    return "\n".join(lines)

            # Final fallback: plain transcript without diarization
            transcript = alternatives[0].get("transcript", "")
            if transcript:
                print("  WARNING: diarization unavailable, using plain transcript", flush=True)
                return transcript

    return "(empty transcript)"


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Transcribe a YouTube video using Deepgram Nova-3 with diarization."
    )
    parser.add_argument("url", help="YouTube URL to transcribe")
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Output file path for the transcript",
    )
    args = parser.parse_args()

    sep = "-" * 60
    print(f"\n{sep}")
    print("  transcribe_call.py — YouTube to Diarized Transcript")
    print(f"{sep}\n")

    # Extract video ID for slug
    video_id = extract_video_id(args.url)
    print(f"  Video ID: {video_id}", flush=True)

    # Download audio to temp dir (cleaned up on exit)
    tmp_dir = tempfile.mkdtemp(prefix="transcribe_call_")
    try:
        audio_path, video_title = download_audio(args.url, tmp_dir)

        # Transcribe via Deepgram
        dg_response = transcribe_with_deepgram(audio_path)

        # Format transcript
        transcript = format_transcript(dg_response)

        # Generate slug
        slug = generate_slug(video_id, video_title)
        print(f"  Slug: {slug}", flush=True)

        # Write output
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(transcript, encoding="utf-8")

        line_count = transcript.count("\n") + 1
        print(f"\n  Transcript written: {output_path}")
        print(f"  Lines: {line_count}")
        print(f"  Title: {video_title}")
        print(f"  Slug:  {slug}")

        # Print slug and title to stdout as JSON for parent process to parse
        # (last line of output — harvest_calls.py reads this)
        meta = json.dumps({"slug": slug, "title": video_title})
        print(f"\n__META__:{meta}")

    finally:
        # Clean up temp files even on error
        try:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass


if __name__ == "__main__":
    main()
