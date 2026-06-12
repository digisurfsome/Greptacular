#!/usr/bin/env python3
"""
Stage 2: Deepgram Nova-3 transcription.
Usage: python transcribe_deepgram.py "<audio-folder>"

Walks the audio folder, sends each .mp3 to Deepgram.
Per-file output: <same-path>.txt (transcript) + <same-path>.json (full response)

Features:
- Skip if .txt exists (resumable, no re-spend)
- 5 concurrent uploads (threading + requests)
- Exponential backoff on 429: 5s 10s 20s 40s 80s
- Cost tracker with running total
- Manifest at <audio-folder>/_transcribe_manifest.json
- On 401: stop immediately
"""

import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: 'requests' package not installed. Run: pip install requests")
    sys.exit(1)

# ── Config ────────────────────────────────────────────────────────────────────
DG_URL    = "https://api.deepgram.com/v1/listen"
DG_PARAMS = {
    "model":        "nova-3",
    "smart_format": "true",
    "punctuate":    "true",
    "utterances":   "true",
    "diarize":      "true",   # Speaker 0: / Speaker 1: labels in output
}
COST_PER_SECOND = 0.0047 / 60   # $0.0047/min (nova-3 $0.0043 + diarize $0.0004)
MAX_WORKERS     = 5
BACKOFF_DELAYS  = [5, 10, 20, 40, 80]   # seconds between retries

# ── Shared state ─────────────────────────────────────────────────────────────
_lock         = threading.Lock()
_total_cost   = 0.0
_completed    = 0
_total_files  = 0
_manifest     = {}
_manifest_path = None


def load_env_key():
    """Read DEEPGRAM_API_KEY from environment or nearest .env file."""
    key = os.environ.get("DEEPGRAM_API_KEY", "").strip()
    if key:
        return key

    # Search up from script dir for a .env file
    search_dirs = [
        Path(__file__).parent,
        Path(__file__).parent.parent,
        Path(__file__).parent.parent.parent,
        Path.cwd(),
    ]
    for d in search_dirs:
        env_file = d / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("DEEPGRAM_API_KEY"):
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        v = parts[1].strip().strip('"').strip("'")
                        if v:
                            return v
    return ""


def load_manifest(path: Path):
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_manifest():
    global _manifest, _manifest_path
    try:
        with open(_manifest_path, "w", encoding="utf-8") as f:
            json.dump(_manifest, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"  [WARN] Could not save manifest: {e}")


def update_manifest(key, data):
    with _lock:
        _manifest[key] = data
        save_manifest()


def parse_duration(data: dict) -> float:
    """Extract audio duration from Deepgram response."""
    try:
        if "metadata" in data and "duration" in data["metadata"]:
            return float(data["metadata"]["duration"])
    except Exception:
        pass
    try:
        utterances = data["results"]["utterances"]
        if utterances:
            return float(max(u["end"] for u in utterances))
    except Exception:
        pass
    return 0.0


def transcribe_file(mp3_path: Path, api_key: str) -> dict:
    global _total_cost, _completed

    txt_path  = mp3_path.with_suffix(".txt")
    json_path = mp3_path.with_suffix(".json")
    key       = str(mp3_path)

    # ── Resumable skip ────────────────────────────────────────────────────────
    if txt_path.exists() and json_path.exists():
        with _lock:
            _completed += 1
            print(f"[{_completed}/{_total_files}] SKIP (exists): {mp3_path.name}")
        return {"file": key, "status": "skipped"}

    # ── Load audio bytes once ─────────────────────────────────────────────────
    try:
        audio_bytes = mp3_path.read_bytes()
    except Exception as e:
        result = {
            "file": key, "status": "error",
            "cost_usd": 0.0, "duration_sec": 0.0,
            "retries": 0, "error": f"read failed: {e}",
            "timestamp": datetime.utcnow().isoformat()
        }
        update_manifest(key, result)
        with _lock:
            _completed += 1
            print(f"[{_completed}/{_total_files}] READ ERROR: {mp3_path.name} — {e}")
        return result

    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type":  "audio/mpeg",
    }

    retries   = 0
    last_error = ""

    for attempt_idx, delay in enumerate([0] + BACKOFF_DELAYS):
        if delay > 0:
            print(f"  → Retry {attempt_idx}/{len(BACKOFF_DELAYS)} in {delay}s: {mp3_path.name}")
            time.sleep(delay)

        try:
            resp = requests.post(
                DG_URL,
                params=DG_PARAMS,
                headers=headers,
                data=audio_bytes,
                timeout=600
            )

            # ── Auth failure — hard stop ───────────────────────────────────────
            if resp.status_code == 401:
                print("\nDEEPGRAM_API_KEY invalid or expired.")
                print("Set DEEPGRAM_API_KEY in your environment or in a .env file.")
                sys.exit(1)

            # ── Rate limit — backoff + retry ──────────────────────────────────
            if resp.status_code == 429:
                last_error = "429 rate limited"
                retries += 1
                continue

            resp.raise_for_status()
            data = resp.json()

            # Build speaker-labeled transcript from utterances (diarization)
            utterances = data["results"].get("utterances", [])
            if utterances:
                lines = []
                for u in utterances:
                    spk = u.get("speaker", 0)
                    txt = u.get("transcript", "").strip()
                    if txt:
                        lines.append(f"Speaker {spk}: {txt}")
                transcript = "\n".join(lines)
            else:
                # Fallback: flat transcript (diarization had no data)
                transcript = data["results"]["channels"][0]["alternatives"][0]["transcript"]
            duration_sec = parse_duration(data)
            cost = duration_sec * COST_PER_SECOND

            # Write outputs
            txt_path.write_text(transcript, encoding="utf-8")
            json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

            with _lock:
                _total_cost += cost
                _completed  += 1
                print(
                    f"[{_completed}/{_total_files}] "
                    f"Done: {mp3_path.name} "
                    f"({duration_sec:.0f}s) | "
                    f"Spent so far: ${_total_cost:.4f}"
                )

            result = {
                "file":         key,
                "status":       "success",
                "cost_usd":     round(cost, 6),
                "duration_sec": round(duration_sec, 2),
                "retries":      retries,
                "error":        "",
                "timestamp":    datetime.utcnow().isoformat()
            }
            update_manifest(key, result)
            return result

        except SystemExit:
            raise

        except Exception as e:
            last_error = str(e)
            retries += 1
            # Still have backoff slots remaining — loop will sleep
            if attempt_idx < len(BACKOFF_DELAYS):
                continue
            break

    # ── All retries exhausted ─────────────────────────────────────────────────
    with _lock:
        _completed += 1
        print(f"[{_completed}/{_total_files}] FAILED: {mp3_path.name} — {last_error[:120]}")

    result = {
        "file":         key,
        "status":       "error",
        "cost_usd":     0.0,
        "duration_sec": 0.0,
        "retries":      retries,
        "error":        last_error[:400],
        "timestamp":    datetime.utcnow().isoformat()
    }
    update_manifest(key, result)
    return result


def transcribe_folder(audio_folder_str: str):
    global _total_files, _manifest, _manifest_path

    api_key = load_env_key()
    if not api_key:
        print("DEEPGRAM_API_KEY not found.")
        print("Add it to your environment or create a .env file at the repo root:")
        print("  DEEPGRAM_API_KEY=your_key_here")
        sys.exit(1)

    audio_folder = Path(audio_folder_str).resolve()
    if not audio_folder.exists():
        print(f"ERROR: Audio folder not found: {audio_folder}")
        sys.exit(1)

    mp3_files = sorted(audio_folder.rglob("*.mp3"))
    # Exclude any stray manifest files (shouldn't be .mp3 but be safe)
    mp3_files = [f for f in mp3_files if not f.name.startswith("_")]

    _total_files   = len(mp3_files)
    _manifest_path = audio_folder / "_transcribe_manifest.json"
    _manifest.update(load_manifest(_manifest_path))

    if _total_files == 0:
        print(f"No .mp3 files found in: {audio_folder}")
        return

    print(f"Found {_total_files} .mp3 file(s). Sending to Deepgram (model=nova-3, {MAX_WORKERS} workers)...")
    print(f"Manifest: {_manifest_path}\n")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(transcribe_file, mp3, api_key): mp3
            for mp3 in mp3_files
        }
        for future in as_completed(futures):
            try:
                future.result()
            except SystemExit:
                raise
            except Exception as e:
                mp3 = futures[future]
                print(f"  [UNHANDLED] {mp3.name}: {e}")

    # ── Final summary ─────────────────────────────────────────────────────────
    entries       = list(_manifest.values())
    success_count = sum(1 for v in entries if v.get("status") == "success")
    skip_count    = sum(1 for v in entries if v.get("status") == "skipped")
    error_count   = sum(1 for v in entries if v.get("status") == "error")
    total_dur     = sum(v.get("duration_sec", 0) for v in entries)

    print(f"\n{'='*60}")
    print("Transcription complete:")
    print(f"  Success:  {success_count}")
    print(f"  Skipped:  {skip_count}")
    print(f"  Errors:   {error_count}")
    print(f"  Runtime:  {total_dur / 3600:.2f} hrs")
    print(f"  Cost:     ${_total_cost:.4f}")
    print(f"  Manifest: {_manifest_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python transcribe_deepgram.py \"<audio-folder>\"")
        sys.exit(1)
    transcribe_folder(sys.argv[1])
