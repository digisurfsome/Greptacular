"""
remove_shorts.py
Deletes video folders from output/videos/ that are under 3.5 minutes.
Reads the Duration line from each folder's info.md.
Run once after youtube_analyzer.py if Shorts slipped through.

RUN:
  python tools/remove_shorts.py
"""

import re
import shutil
from pathlib import Path

OUTPUT_DIR = Path("output/videos")
MIN_SECONDS = 210  # 3.5 minutes — same threshold as youtube_analyzer.py

SHORT_KEYWORDS = ["#shorts", "#short", " shorts"]


def parse_duration(info_text: str) -> int:
    """Extract duration in seconds from info.md Duration line.
    Handles: 45s | 2m 30s | 1h 5m 10s
    """
    m = re.search(r"\*\*Duration:\*\*\s*(.+)", info_text)
    if not m:
        return 0
    dur = m.group(1).strip()

    hours = minutes = seconds = 0
    h = re.search(r"(\d+)h", dur)
    mi = re.search(r"(\d+)m", dur)
    s = re.search(r"(\d+)s", dur)
    if h:  hours   = int(h.group(1))
    if mi: minutes = int(mi.group(1))
    if s:  seconds = int(s.group(1))
    return hours * 3600 + minutes * 60 + seconds


def is_short(info_text: str, duration_s: int) -> bool:
    text_lower = info_text.lower()
    if any(kw in text_lower for kw in SHORT_KEYWORDS):
        return True
    if 0 < duration_s < MIN_SECONDS:
        return True
    return False


def main():
    if not OUTPUT_DIR.exists():
        print(f"No output/videos/ folder found. Run youtube_analyzer.py first.")
        return

    folders = sorted(OUTPUT_DIR.iterdir())
    removed = []
    kept = []

    for folder in folders:
        if not folder.is_dir():
            continue
        info_path = folder / "info.md"
        if not info_path.exists():
            print(f"  [SKIP] No info.md: {folder.name}")
            continue

        info_text = info_path.read_text(encoding="utf-8", errors="ignore")
        duration_s = parse_duration(info_text)

        if is_short(info_text, duration_s):
            print(f"  [DELETE] {folder.name} ({duration_s}s)")
            shutil.rmtree(folder)
            removed.append(folder.name)
        else:
            kept.append(folder.name)

    print(f"\nDone. Removed {len(removed)} Shorts. Kept {len(kept)} real videos.")
    if removed:
        print("\nRemoved:")
        for r in removed:
            print(f"  - {r}")


if __name__ == "__main__":
    main()
