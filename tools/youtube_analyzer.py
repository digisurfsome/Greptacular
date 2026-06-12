"""
YouTube Channel Analyzer
Fetches videos from last N months, filters out Shorts,
pulls transcripts, saves organized output.

SETUP:
  pip install requests youtube-transcript-api

CONFIGURE (lines below):
  YOUTUBE_API_KEY  — your YouTube Data API v3 key
  CHANNEL_ID       — the channel to scrape
  MONTHS_BACK      — how far back to go
  OUTPUT_DIR       — where to save everything

RUN:
  python tools/youtube_analyzer.py
"""

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

# ─────────────────────────────────────────
#  CONFIG — edit these
# ─────────────────────────────────────────
YOUTUBE_API_KEY = "PASTE_YOUR_KEY_HERE"
CHANNEL_ID      = "UCdmJVDnFnbGrQXJqBDkZpag"   # Connor's channel — update if needed
MONTHS_BACK     = 4                              # how far back to fetch
OUTPUT_DIR      = Path("output")

# YouTube Shorts are now up to 3 minutes (180s). Use 3.5 min as safe buffer.
# Regular tutorial/agency videos are almost always 5+ minutes.
MIN_DURATION_SECONDS = 210  # 3.5 minutes

# Keywords in title OR description that signal a Short
SHORT_KEYWORDS = ["#shorts", "#short", " shorts"]

# Manually add important older videos that fall outside the date window.
# These will be appended to the fetch results before transcript download.
MANUAL_VIDEO_IDS = [
    # Jan 9 — How to Build and Sell Ai Agents with GoHighLevel (9m 30s)
    "tBA-tXnNkSA",
    # Jan 7 — how i sell 1 GoHighLevel feature to make $56k/month (16m 15s)
    "7YDH9Q0vAaA",
    # Feb 5 — Watch me build a $100k/m Web Design app with AI (10m 56s)
    "GVbz3oWzuWk",
    # Feb 8 — The Perfect Sales Script to Sell GoHighLevel (8m 1s)
    "1XqLb2a5eqA",
]
# ─────────────────────────────────────────

BASE_URL = "https://www.googleapis.com/youtube/v3"


def iso_duration_to_seconds(duration: str) -> int:
    """Convert ISO 8601 duration (PT5M30S) to total seconds."""
    match = re.match(
        r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration or ""
    )
    if not match:
        return 0
    hours   = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


def format_duration(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m}m {s}s"
    return f"{m}m {s}s"


def is_short(title: str, duration_seconds: int, description: str = "") -> bool:
    """Return True if this video looks like a Short.

    Checks three signals:
    1. Title contains a shorts keyword
    2. Description contains a shorts keyword (many creators skip title tag)
    3. Duration under 3.5 minutes (YouTube Shorts now allowed up to 3 min)
    """
    title_lower = title.lower()
    desc_lower = description.lower()
    if any(kw in title_lower for kw in SHORT_KEYWORDS):
        return True
    if any(kw in desc_lower for kw in SHORT_KEYWORDS):
        return True
    if duration_seconds > 0 and duration_seconds < MIN_DURATION_SECONDS:
        return True
    return False


def get_uploads_playlist_id() -> str:
    """Get the uploads playlist ID for the channel."""
    url = f"{BASE_URL}/channels"
    params = {
        "part": "contentDetails",
        "id": CHANNEL_ID,
        "key": YOUTUBE_API_KEY,
    }
    r = requests.get(url, params=params)
    r.raise_for_status()
    data = r.json()
    return data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]


def get_video_ids_since(playlist_id: str, since: datetime) -> list[str]:
    """Walk the uploads playlist and collect video IDs published after `since`."""
    ids = []
    page_token = None
    while True:
        params = {
            "part": "contentDetails,snippet",
            "playlistId": playlist_id,
            "maxResults": 50,
            "key": YOUTUBE_API_KEY,
        }
        if page_token:
            params["pageToken"] = page_token

        r = requests.get(f"{BASE_URL}/playlistItems", params=params)
        r.raise_for_status()
        data = r.json()

        for item in data.get("items", []):
            published = item["snippet"]["publishedAt"]
            pub_dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
            if pub_dt < since:
                # Playlist is newest-first; once we're past the cutoff, stop.
                return ids
            ids.append(item["contentDetails"]["videoId"])

        page_token = data.get("nextPageToken")
        if not page_token:
            break
    return ids


def get_video_details(video_ids: list[str]) -> list[dict]:
    """Batch-fetch video details (title, description, duration, links)."""
    details = []
    # API allows max 50 per request
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i : i + 50]
        params = {
            "part": "snippet,contentDetails",
            "id": ",".join(batch),
            "key": YOUTUBE_API_KEY,
        }
        r = requests.get(f"{BASE_URL}/videos", params=params)
        r.raise_for_status()
        data = r.json()
        for item in data.get("items", []):
            snippet = item["snippet"]
            content = item["contentDetails"]
            duration_s = iso_duration_to_seconds(content.get("duration", ""))
            title = snippet.get("title", "")
            description = snippet.get("description", "")

            if is_short(title, duration_s, description):
                print(f"  [SKIP SHORT] {title} ({format_duration(duration_s)})")
                continue
            # Extract all URLs from description
            urls = re.findall(r"https?://\S+", description)
            # Flag tool/asset links (not GHL affiliate, not YouTube links)
            tool_urls = [
                u for u in urls
                if not any(skip in u for skip in [
                    "youtube.com", "youtu.be", "gohighlevel.com",
                    "instagram.com", "twitter.com", "x.com",
                    "facebook.com", "tiktok.com", "linktr.ee",
                ])
            ]

            details.append({
                "id": item["id"],
                "title": title,
                "published": snippet.get("publishedAt", ""),
                "duration_s": duration_s,
                "duration_fmt": format_duration(duration_s),
                "description": description,
                "tool_urls": tool_urls,
                "url": f"https://www.youtube.com/watch?v={item['id']}",
            })
    return details


def fetch_transcript(video_id: str) -> str:
    """Fetch transcript text. Returns empty string if unavailable."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join(seg["text"] for seg in transcript)
    except Exception as e:
        return f"[TRANSCRIPT UNAVAILABLE: {e}]"


def slugify(title: str) -> str:
    """Convert title to filesystem-safe slug."""
    slug = re.sub(r"[^\w\s-]", "", title.lower())
    slug = re.sub(r"[\s_-]+", "-", slug)
    return slug[:60].strip("-")


def save_video(video: dict, transcripts_combined: list[str]):
    """Save info.md + transcript.txt for one video."""
    date_str = video["published"][:10]
    folder_name = f"{date_str}_{slugify(video['title'])}"
    folder = OUTPUT_DIR / "videos" / folder_name
    folder.mkdir(parents=True, exist_ok=True)

    # info.md
    tool_section = ""
    if video["tool_urls"]:
        tool_section = "\n## Tool / Asset Links\n" + "\n".join(
            f"- {u}" for u in video["tool_urls"]
        )

    info_content = f"""# {video['title']}

- **Date:** {video['published'][:10]}
- **Duration:** {video['duration_fmt']}
- **URL:** {video['url']}
- **Has Tools:** {'YES' if video['tool_urls'] else 'no'}
{tool_section}

## Description

{video['description']}
"""
    (folder / "info.md").write_text(info_content, encoding="utf-8")

    # transcript.txt
    print(f"  Fetching transcript: {video['title'][:60]}...")
    transcript = fetch_transcript(video["id"])
    (folder / "transcript.txt").write_text(transcript, encoding="utf-8")

    # Append to combined file
    transcripts_combined.append(
        f"\n\n{'='*80}\n"
        f"VIDEO: {video['title']}\n"
        f"DATE:  {video['published'][:10]}\n"
        f"URL:   {video['url']}\n"
        f"{'='*80}\n\n"
        + transcript
    )


def write_index(videos: list[dict]):
    """Write master index.md."""
    lines = [
        "# Video Index\n",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
        f"Total videos (non-Shorts): {len(videos)}\n",
        f"With tool links: {sum(1 for v in videos if v['tool_urls'])}\n\n",
        "## All Videos\n",
        "| Date | Title | Duration | Tools | Link |",
        "|------|-------|----------|-------|------|",
    ]
    for v in videos:
        tool_flag = "✅" if v["tool_urls"] else ""
        title_safe = v["title"].replace("|", "-")
        lines.append(
            f"| {v['published'][:10]} | {title_safe} | {v['duration_fmt']} "
            f"| {tool_flag} | [Watch]({v['url']}) |"
        )

    lines.append("\n## Tool Videos — Links Extracted\n")
    for v in videos:
        if v["tool_urls"]:
            lines.append(f"\n### {v['title']}")
            lines.append(f"- Date: {v['published'][:10]}")
            lines.append(f"- Video: {v['url']}")
            for u in v["tool_urls"]:
                lines.append(f"- Tool: {u}")

    (OUTPUT_DIR / "index.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    if YOUTUBE_API_KEY == "PASTE_YOUR_KEY_HERE":
        print("ERROR: Set your YOUTUBE_API_KEY at the top of this script.")
        return

    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / "videos").mkdir(exist_ok=True)

    since = datetime.now(timezone.utc) - timedelta(days=MONTHS_BACK * 30)
    print(f"Fetching videos since {since.date()} (last {MONTHS_BACK} months)...")

    playlist_id = get_uploads_playlist_id()
    print(f"Uploads playlist: {playlist_id}")

    video_ids = get_video_ids_since(playlist_id, since)
    print(f"Found {len(video_ids)} video IDs in date range.")

    # Add manual IDs (deduplicated)
    for vid in MANUAL_VIDEO_IDS:
        if vid not in video_ids:
            video_ids.append(vid)
    print(f"Total after manual additions: {len(video_ids)}")

    print("Fetching video details + filtering Shorts...")
    videos = get_video_details(video_ids)
    # Sort oldest → newest (for truth builder to process in order)
    videos.sort(key=lambda v: v["published"])
    print(f"{len(videos)} non-Short videos to process.")

    write_index(videos)
    print(f"Index written to {OUTPUT_DIR}/index.md")

    transcripts_combined = []
    for i, video in enumerate(videos, 1):
        print(f"[{i}/{len(videos)}] {video['title'][:70]}")
        save_video(video, transcripts_combined)

    combined_path = OUTPUT_DIR / "all_transcripts.txt"
    combined_path.write_text(
        "\n".join(transcripts_combined), encoding="utf-8"
    )
    print(f"\nAll transcripts combined → {combined_path}")
    print("Run truth_builder.py next to build the truth document.")


if __name__ == "__main__":
    main()
