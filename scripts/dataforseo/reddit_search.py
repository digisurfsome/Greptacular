#!/usr/bin/env python3
"""
Reddit Business Search
======================
Reads business names from any *_standard.csv or *_emergency.csv output by
hvac_dallas_leads.py, searches Reddit for each business, prints and saves results.

No API key needed. No cost. Rate limit: ~1 req/sec is fine.

HOW TO RUN:
    python reddit_search.py
    python reddit_search.py hvac_dallas_standard_newest.csv
    python reddit_search.py hvac_dallas_emergency_newest.csv

Output:
    *_reddit_results.csv  — one row per Reddit post found
    *_reddit_summary.txt  — readable summary per business
"""

import os
import sys
import json
import csv
import time
import urllib.parse
import urllib.request
from pathlib import Path
from datetime import datetime

HEADERS    = {"User-Agent": "LeadResearchBot/1.0"}
MAX_POSTS  = 15     # per business search
SLEEP      = 1.2    # seconds between requests — polite to Reddit


def search_reddit(query: str, max_posts: int = MAX_POSTS) -> list:
    url = (
        f"https://www.reddit.com/search.json"
        f"?q={urllib.parse.quote(query)}"
        f"&sort=top&limit={max_posts}&t=all&type=link"
    )
    try:
        req  = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data  = json.loads(resp.read())
            posts = data.get("data", {}).get("children", [])
    except Exception as e:
        print(f"    ⚠️  Reddit error: {e}")
        return []

    results = []
    for post in posts:
        d = post.get("data", {})
        title  = d.get("title", "")
        body   = d.get("selftext", "")
        text   = f"{title}\n{body}".strip() if body else title
        if not text or len(text) < 20:
            continue

        ts = d.get("created_utc", 0)
        try:
            date_str = datetime.utcfromtimestamp(int(ts)).strftime("%Y-%m-%d") if ts else ""
        except Exception:
            date_str = ""

        results.append({
            "title":     title,
            "body":      body[:600],
            "full_text": text[:800],
            "url":       f"https://reddit.com{d.get('permalink', '')}",
            "subreddit": d.get("subreddit", ""),
            "upvotes":   d.get("score", 0),
            "comments":  d.get("num_comments", 0),
            "date":      date_str,
        })

    return results


def load_businesses(csv_path: str) -> list:
    businesses = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = row.get("name", "").strip()
            city = "Dallas"
            if name:
                businesses.append({"name": name, "city": city, "phone": row.get("phone",""), "rating": row.get("rating","")})
    return businesses


def run(csv_path: str):
    path = Path(csv_path)
    if not path.exists():
        print(f"❌ File not found: {csv_path}")
        return

    businesses = load_businesses(str(path))
    print(f"\n{'='*60}")
    print(f"Reddit Search — {path.name}")
    print(f"Businesses: {len(businesses)}")
    print(f"Max posts per biz: {MAX_POSTS}")
    print(f"{'='*60}\n")

    all_rows  = []
    summary   = []

    for idx, biz in enumerate(businesses, 1):
        name  = biz["name"]
        city  = biz["city"]
        query = f'"{name}" {city}'

        print(f"[{idx}/{len(businesses)}] {name}")
        print(f"  Searching: {query}")

        posts = search_reddit(query)

        if not posts:
            # Try without quotes — broader search
            query2 = f"{name} HVAC {city} review"
            print(f"  No results — trying broader: {query2}")
            time.sleep(SLEEP)
            posts = search_reddit(query2)

        if posts:
            print(f"  ✅ {len(posts)} posts found:")
            for p in posts[:5]:  # print top 5
                print(f"    [{p['upvotes']}↑ r/{p['subreddit']}] {p['title'][:80]}")
                if p["body"]:
                    print(f"      → {p['body'][:120].strip()}")
        else:
            print(f"  ❌ No Reddit mentions found")

        biz_summary = {
            "name":       name,
            "post_count": len(posts),
            "posts":      posts,
        }
        summary.append(biz_summary)

        for post in posts:
            all_rows.append({
                "business":  name,
                "phone":     biz["phone"],
                "rating":    biz["rating"],
                "subreddit": post["subreddit"],
                "date":      post["date"],
                "upvotes":   post["upvotes"],
                "comments":  post["comments"],
                "title":     post["title"],
                "body":      post["body"],
                "url":       post["url"],
            })

        print()
        time.sleep(SLEEP)

    # Save CSV
    out_csv = str(path).replace(".csv", "_reddit_results.csv")
    if all_rows:
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            fields = ["business","phone","rating","subreddit","date","upvotes","comments","title","body","url"]
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(all_rows)
        print(f"✅ Reddit results saved → {Path(out_csv).name} ({len(all_rows)} posts)")
    else:
        print("❌ No Reddit posts found for any business.")

    # Save readable summary
    out_txt = str(path).replace(".csv", "_reddit_summary.txt")
    with open(out_txt, "w", encoding="utf-8") as f:
        f.write(f"Reddit Search Summary — {path.name}\n")
        f.write(f"Run: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write("="*60 + "\n\n")
        for biz in summary:
            f.write(f"{'─'*50}\n")
            f.write(f"  {biz['name']} — {biz['post_count']} Reddit posts\n")
            f.write(f"{'─'*50}\n")
            if not biz["posts"]:
                f.write("  No Reddit mentions found.\n\n")
                continue
            for p in biz["posts"]:
                f.write(f"\n  [{p['upvotes']}↑ | r/{p['subreddit']} | {p['date']}]\n")
                f.write(f"  {p['title']}\n")
                if p["body"]:
                    f.write(f"  {p['body'][:300]}\n")
                f.write(f"  {p['url']}\n")
            f.write("\n")

    print(f"✅ Readable summary   → {Path(out_txt).name}")

    # Print final hit rate
    with_hits = sum(1 for b in summary if b["post_count"] > 0)
    print(f"\n📊 {with_hits} of {len(businesses)} businesses have Reddit mentions")


def main():
    files = sys.argv[1:]
    if not files:
        # Auto-detect CSVs in same folder
        folder = Path(__file__).parent
        files  = list(folder.glob("*_newest.csv")) + list(folder.glob("*_standard.csv")) + list(folder.glob("*_emergency.csv"))
        # Deduplicate
        seen = set()
        files = [f for f in files if not (str(f) in seen or seen.add(str(f)))]
        if not files:
            print("❌ No CSV files found. Run hvac_dallas_leads.py first.")
            return
        print(f"Found {len(files)} CSV file(s) to process.")

    for f in files:
        run(str(f))


if __name__ == "__main__":
    main()
