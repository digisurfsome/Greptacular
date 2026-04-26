#!/usr/bin/env python3
"""
YouTube Channel Analyzer
========================
Fetches all videos from a YouTube channel for the last N months,
downloads transcripts, extracts description links, and identifies
videos that include free tools or downloadable assets.

Output structure:
  output/
    index.md              <- master list: all videos, flagged tool videos, all links
    videos/
      YYYY-MM-DD_title/
        info.md           <- title, date, duration, description, extracted links
        transcript.txt    <- full spoken transcript

Usage:
  python tools/youtube_analyzer.py

Requirements:
  pip install requests youtube-transcript-api
"""

import re
import time
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi

# ── Config ────────────────────────────────────────────────────────────────────

API_KEY        = "AIzaSyDGab7qioHQUDYsI-DTxgE891i8-oproyk"
CHANNEL_HANDLE = "connorcahil"
MONTHS_BACK    = 2
OUTPUT_DIR     = Path("output")

YT_API = "https://www.googleapis.com/youtube/v3"

# Domains that signal a free tool, template, or downloadable asset
TOOL_DOMAINS = [
    "lovable.app",
    "docs.google.com",
    "skool.com",
    "gohighlevel.com",
    "bookacall",
    "agency-vault",
    "notion.so",
    "airtable.com",
    "zapier.com",
    "make.com",
]

# ── YouTube API helpers ───────────────────────────────────────────────────────

def yt_get(endpoint, params):
    """Make a YouTube Data API v3 GET request."""
    params["key"] = API_KEY
    resp = requests.get(f"{YT_API}/{endpoint}", params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_channel_info(handle):
    """Return (channel_id, uploads_playlist_id) for a handle like 'connorcahil'."""
    data = yt_get("channels", {"part": "id,contentDetails", "forHandle": handle})
    if not data.get("items"):
        raise ValueError(f"Channel @{handle} not found.")
    ch = data["items"][0]
    return ch["id"], ch["contentDetails"]["relatedPlaylists"]["uploads"]


def get_recent_videos(uploads_playlist_id, since_date):
    """
    Page through the uploads playlist and return all videos published
    after since_date. Playlist is newest-first so we stop early.
    """
    videos     = []
    page_token = None

    while True:
        params = {
            "part":       "snippet,contentDetails",
            "playlistId": uploads_playlist_id,
            "maxResults": 50,
        }
        if page_token:
            params["pageToken"] = page_token

        data = yt_get("playlistItems", params)

        for item in data["items"]:
            pub_str = item["snippet"]["publishedAt"]
            pub_dt  = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))

            if pub_dt < since_date:
                return videos  # everything past here is older

            videos.append({
                "video_id":     item["contentDetails"]["videoId"],
                "title":        item["snippet"]["title"],
                "published_at": pub_str,
                "pub_dt":       pub_dt,
            })

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    return videos


def get_video_details(video_ids):
    """Batch-fetch full details for up to 50 video IDs at a time."""
    details = {}
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i : i + 50]
        data  = yt_get("videos", {
            "part": "snippet,contentDetails,statistics",
            "id":   ",".join(batch),
        })
        for item in data["items"]:
            details[item["id"]] = {
                "title":        item["snippet"]["title"],
                "description":  item["snippet"]["description"],
                "duration":     item["contentDetails"]["duration"],
                "view_count":   item["statistics"].get("viewCount", "0"),
                "published_at": item["snippet"]["publishedAt"],
            }
    return details

# ── Transcript ────────────────────────────────────────────────────────────────

def get_transcript(video_id):
    """Fetch full transcript text. Returns an error note if unavailable."""
    try:
        api    = YouTubeTranscriptApi()
        result = api.fetch(video_id)
        return " ".join(s.text for s in result.snippets)
    except Exception as exc:
        return f"[Transcript unavailable: {exc}]"

# ── Utilities ─────────────────────────────────────────────────────────────────

def extract_links(text):
    pattern = r'https?://[^\s\)\]>\"\'<]+'
    return [url.rstrip(".,;") for url in re.findall(pattern, text)]


def classify_links(links):
    tools, other = [], []
    for link in links:
        (tools if any(d in link for d in TOOL_DOMAINS) else other).append(link)
    return tools, other


def parse_duration(iso):
    m = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', iso)
    if not m:
        return iso
    h, mn, s = (int(x or 0) for x in m.groups())
    return f"{h}h {mn}m" if h else f"{mn}m {s}s"


def slugify(text):
    text = re.sub(r'[^\w\s-]', '', text.lower())
    text = re.sub(r'[\s_-]+', '-', text)
    return text[:60].strip('-')

# ── File output ───────────────────────────────────────────────────────────────

def save_video_folder(video, detail, transcript, base_dir):
    date_str    = video["pub_dt"].strftime("%Y-%m-%d")
    folder_name = f"{date_str}_{slugify(detail['title'])}"
    folder      = base_dir / "videos" / folder_name
    folder.mkdir(parents=True, exist_ok=True)

    all_links         = extract_links(detail["description"])
    tool_links, promo = classify_links(all_links)
    duration          = parse_duration(detail["duration"])
    yt_url            = f"https://www.youtube.com/watch?v={video['video_id']}"

    lines = [
        f"# {detail['title']}",
        "",
        f"**URL:** {yt_url}",
        f"**Date:** {date_str}",
        f"**Duration:** {duration}",
        f"**Views:** {detail['view_count']}",
        "",
    ]

    if tool_links:
        lines += ["## Free Tools / Assets", ""]
        for t in tool_links:
            lines.append(f"- {t}")
        lines.append("")

    if promo:
        lines += ["## Other Links", ""]
        for p in promo:
            lines.append(f"- {p}")
        lines.append("")

    lines += ["## Description", "", detail["description"]]

    (folder / "info.md").write_text("\n".join(lines), encoding="utf-8")
    (folder / "transcript.txt").write_text(transcript, encoding="utf-8")

    return {
        "folder":     folder_name,
        "title":      detail["title"],
        "date":       date_str,
        "duration":   duration,
        "view_count": detail["view_count"],
        "has_tools":  bool(tool_links),
        "tools":      tool_links,
        "all_links":  all_links,
        "video_id":   video["video_id"],
        "yt_url":     yt_url,
    }


def write_index(results, base_dir, months_back):
    tool_videos = [r for r in results if r["has_tools"]]
    now_str     = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        "# Connor Cahill — YouTube Channel Analysis",
        "",
        f"**Generated:** {now_str}",
        f"**Period:** Last {months_back} months",
        f"**Total videos:** {len(results)}",
        f"**Videos with free tools/assets:** {len(tool_videos)}",
        "",
        "---",
        "",
        "## Videos with Free Tools or Assets",
        "",
    ]

    if tool_videos:
        for r in tool_videos:
            lines += [
                f"### [{r['title']}]({r['yt_url']})",
                f"**Date:** {r['date']} | **Duration:** {r['duration']} | **Views:** {r['view_count']}",
                "",
                "**Tools / Assets:**",
            ]
            for t in r["tools"]:
                lines.append(f"- {t}")
            lines += ["", f"Folder: `videos/{r['folder']}`", ""]
    else:
        lines += ["*None found in this period.*", ""]

    lines += [
        "---",
        "",
        "## All Videos (newest first)",
        "",
        "| Date | Title | Duration | Views | Tools? |",
        "|------|-------|----------|-------|--------|",
    ]

    for r in results:
        flag  = "YES" if r["has_tools"] else ""
        title = f"[{r['title']}]({r['yt_url']})"
        lines.append(f"| {r['date']} | {title} | {r['duration']} | {r['view_count']} | {flag} |")

    lines += [
        "",
        "---",
        "",
        "## All Unique Tool / Asset Links",
        "",
    ]

    seen = set()
    for r in results:
        for t in r["tools"]:
            if t not in seen:
                seen.add(t)
                lines.append(f"- [{r['title']}]({r['yt_url']}) → {t}")

    (base_dir / "index.md").write_text("\n".join(lines), encoding="utf-8")

# ── Main ──────────────────────────────────────────────────────────────────────

def write_combined_transcripts(results, base_dir):
    """Write every transcript into one file, oldest-first, for easy agent ingestion."""
    lines = ["# All Transcripts — Connor Cahill", ""]
    for r in reversed(results):  # reversed = oldest first
        folder = base_dir / "videos" / r["folder"]
        tf     = folder / "transcript.txt"
        text   = tf.read_text(encoding="utf-8") if tf.exists() else "[No transcript file]"
        lines += [
            f"## {r['date']} — {r['title']}",
            f"URL: {r['yt_url']}",
            f"Duration: {r['duration']}",
            "",
            text,
            "",
            "---",
            "",
        ]
    (base_dir / "all_transcripts.txt").write_text("\n".join(lines), encoding="utf-8")


def main():
    print("=" * 60)
    print("  YouTube Channel Analyzer")
    print("=" * 60)

    since_date = datetime.now(timezone.utc) - timedelta(days=MONTHS_BACK * 30)

    print(f"\n→ Looking up @{CHANNEL_HANDLE}...")
    channel_id, uploads_id = get_channel_info(CHANNEL_HANDLE)
    print(f"  Channel ID : {channel_id}")

    print(f"\n→ Fetching videos since {since_date.strftime('%Y-%m-%d')}...")
    videos = get_recent_videos(uploads_id, since_date)
    print(f"  Found {len(videos)} videos")

    if not videos:
        print("\nNo videos found. Try increasing MONTHS_BACK.")
        return

    print("\n→ Fetching video details...")
    details = get_video_details([v["video_id"] for v in videos])

    OUTPUT_DIR.mkdir(exist_ok=True)
    results = []

    for i, video in enumerate(videos, 1):
        vid_id = video["video_id"]
        title  = details[vid_id]["title"]
        print(f"\n  [{i:02d}/{len(videos)}] {title}")
        print(f"           Transcript...", end=" ", flush=True)

        transcript = get_transcript(vid_id)
        status     = "OK" if not transcript.startswith("[Transcript") else "unavailable"
        print(status)

        result = save_video_folder(video, details[vid_id], transcript, OUTPUT_DIR)
        results.append(result)

        if result["has_tools"]:
            print(f"           TOOLS: {result['tools']}")

        time.sleep(0.3)

    print("\n→ Writing index.md...")
    write_index(results, OUTPUT_DIR, MONTHS_BACK)

    print("→ Writing all_transcripts.txt...")
    write_combined_transcripts(results, OUTPUT_DIR)

    tool_count = sum(1 for r in results if r["has_tools"])
    print("\n" + "=" * 60)
    print(f"  Output : {OUTPUT_DIR.resolve()}")
    print(f"  Videos : {len(results)}  |  With tools : {tool_count}")
    print("=" * 60)

    if tool_count:
        print("\nTool videos:")
        for r in results:
            if r["has_tools"]:
                print(f"  {r['date']}  {r['title']}")
                for t in r["tools"]:
                    print(f"    → {t}")


if __name__ == "__main__":
    main()
