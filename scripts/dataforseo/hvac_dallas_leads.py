#!/usr/bin/env python3
"""
DataForSEO — HVAC Dallas Lead Finder
=====================================
Runs TWO separate keyword searches and keeps results completely separate.

Search A: "HVAC companies Dallas Texas"   → hvac_dallas_standard.csv
Search B: "emergency HVAC Dallas Texas"   → hvac_dallas_emergency.csv

Lean workflow: Maps SERP → pull 50 reviews on top 10 → flag missed-call language.

Cost estimate for this run (10 businesses × 50 reviews × 2 searches):
  2 Maps SERP calls            = $0.004
  20 businesses × 50 reviews   = $0.075  ($0.00375 per 50 reviews)
  Total                        ≈ $0.079  (less than a dime)

NOTE: If a business has fewer than 50 reviews, it just returns however many it has.
      No error — you just get 30 if they only have 30.

HOW TO RUN:
  1. Open a terminal in this folder
  2. Install the only dependency:
         pip install requests
  3. Run — pass your DataForSEO login email + password directly:
         python hvac_dallas_leads.py DATAFORSEO_LOGIN=you@email.com DATAFORSEO_PASSWORD=yourpass
     OR as positional args (same thing, shorter):
         python hvac_dallas_leads.py you@email.com yourpass
"""

import os
import json
import csv
import time
import sys
import requests
from datetime import datetime
from pathlib import Path
from requests.auth import HTTPBasicAuth

# ── Load .env file if present ─────────────────────────────────────────────────
# Looks for .env in same folder as this script — credentials never hardcoded
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

# ── Credentials ──────────────────────────────────────────────────────────────
DATAFORSEO_LOGIN    = os.environ.get("DATAFORSEO_LOGIN",    "")
DATAFORSEO_PASSWORD = os.environ.get("DATAFORSEO_PASSWORD", "")

BASE_URL = "https://api.dataforseo.com"

# ── Auth — built AFTER credentials are parsed ─────────────────────────────────

# ── Search Config ─────────────────────────────────────────────────────────────
LOCATION        = "Dallas,Texas,United States"
MAX_BUSINESSES  = 10        # 10 businesses per search (2 searches = 20 total)
REVIEW_DEPTH    = 50        # 50 reviews per business — if biz has fewer, just returns what it has
REVIEW_SORT     = "lowest_rating"   # "lowest_rating" | "newest" | "highest_rating"
MIN_REVIEWS     = 50        # skip businesses with fewer than 50 reviews (need enough to fill quota)

# The two separate searches — results stay completely separate
SEARCHES = [
    {
        "label":       "STANDARD",
        "keyword":     "HVAC companies Dallas Texas",
        "output_file": "hvac_dallas_standard.csv",
    },
    {
        "label":       "EMERGENCY",
        "keyword":     "emergency HVAC Dallas Texas",
        "output_file": "hvac_dallas_emergency.csv",
    },
]

# ── Missed Call / Unreachable Signal Keywords ────────────────────────────────
# Anything suggesting: didn't answer, went to voicemail, on hold too long,
# couldn't reach them, no callback, ignored — all signs they need an AI receptionist.
MISSED_CALL_KEYWORDS = [
    # Didn't pick up
    "no answer",
    "didn't answer",
    "did not answer",
    "no one answered",
    "nobody answered",
    "no one picked up",
    "nobody picked up",
    "never picked up",
    # Voicemail / machine
    "voicemail",
    "voice mail",
    "answering machine",
    "left a message",
    "left a voicemail",
    "left voicemail",
    "voicemail full",
    "mailbox full",
    # No callback
    "never called back",
    "didn't call back",
    "did not call back",
    "no return call",
    "no callback",
    "waiting for a call back",
    "still waiting",
    "never got a call",
    "no one called me back",
    # Can't reach them
    "couldn't reach",
    "could not reach",
    "can't reach",
    "cannot reach",
    "unreachable",
    "hard to reach",
    "impossible to reach",
    "can't get ahold",
    "can't get a hold",
    # On hold / waiting
    "on hold",
    "put me on hold",
    "hold for",
    "waited on hold",
    "long wait",
    "wait time",
    "waited forever",
    "waited so long",
    "hours waiting",
    # Ignored
    "no response",
    "never responded",
    "ignored",
    "no reply",
    "never replied",
    "no communication",
    # After hours
    "after hours",
    "after-hours",
    "closed",
    "not available",
    "unavailable",
    # Phone tag
    "phone tag",
    "keep calling",
    "called multiple times",
    "called several times",
    "called again",
    "tried calling",
    "tried to call",
    "hang up",
    "hung up",
    "disconnect",
    "disconnected",
]

# ── HTTP Helper ───────────────────────────────────────────────────────────────
def api_post(endpoint, payload):
    auth = HTTPBasicAuth(DATAFORSEO_LOGIN, DATAFORSEO_PASSWORD)
    resp = requests.post(f"{BASE_URL}{endpoint}", json=payload, auth=auth, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    if data.get("status_code") not in (20000, 20100):
        raise RuntimeError(f"API error {data.get('status_code')}: {data.get('status_message')}")
    return data

def api_get(endpoint):
    auth = HTTPBasicAuth(DATAFORSEO_LOGIN, DATAFORSEO_PASSWORD)
    resp = requests.get(f"{BASE_URL}{endpoint}", auth=auth, timeout=60)
    resp.raise_for_status()
    return resp.json()


# ── Step 1: Maps SERP ─────────────────────────────────────────────────────────
def discover_businesses(keyword):
    """
    One Maps SERP call → up to 100 businesses.
    Cost: $0.002 flat.
    Returns list filtered and sorted worst-rated first.
    """
    payload = [{
        "keyword":       keyword,
        "location_name": LOCATION,
        "language_name": "English",
        "device":        "desktop",
        "os":            "windows",
        "depth":         100,
    }]

    data = api_post("/v3/serp/google/maps/live/advanced", payload)

    raw_items = []
    for task in data.get("tasks", []):
        for result in task.get("result", []):
            for item in result.get("items", []):
                if item.get("type") == "maps_search":
                    raw_items.append(item)

    print(f"  Raw results from Google: {len(raw_items)} businesses")

    businesses = []
    for item in raw_items:
        rating_obj   = item.get("rating") or {}
        dist         = rating_obj.get("rating_distribution") or {}
        total        = rating_obj.get("votes_count", 0)
        star_value   = rating_obj.get("value", 5.0) or 5.0
        # Keys may be int or string depending on API response — try both
        one_star     = dist.get(1, 0) or dist.get("1", 0)
        two_star     = dist.get(2, 0) or dist.get("2", 0)
        three_star   = dist.get(3, 0) or dist.get("3", 0)
        four_star    = dist.get(4, 0) or dist.get("4", 0)
        five_star    = dist.get(5, 0) or dist.get("5", 0)
        one_star_pct = round((one_star / total * 100), 1) if total > 0 else 0.0

        businesses.append({
            "name":           item.get("title", ""),
            "phone":          item.get("phone", ""),
            "address":        item.get("address", ""),
            "city":           (item.get("address_info") or {}).get("city", ""),
            "zip":            (item.get("address_info") or {}).get("zip", ""),
            "website":        item.get("url", ""),
            "domain":         item.get("domain", ""),
            "contact_url":    item.get("contact_url", ""),
            "place_id":       item.get("place_id", ""),
            "cid":            item.get("cid", ""),
            "rating":         star_value,
            "review_count":   total,
            "is_claimed":     item.get("is_claimed", False),
            "one_star_count": one_star,
            "one_star_pct":   one_star_pct,
            "two_star":       two_star,
            "three_star":     three_star,
            "four_star":      four_star,
            "five_star":      five_star,
            "category":       item.get("category", ""),
            "price_level":    item.get("price_level", ""),
            "open_now":       (item.get("work_hours") or {}).get("current_status", ""),
            "total_photos":   item.get("total_photos", 0),
        })

    # Filter: must have minimum reviews
    businesses = [b for b in businesses if b["review_count"] >= MIN_REVIEWS]

    # Sort: worst rated first
    businesses.sort(key=lambda x: (x["rating"], -x["one_star_pct"]))

    # Cap to MAX_BUSINESSES
    selected = businesses[:MAX_BUSINESSES]

    print(f"  After filter ({MIN_REVIEWS}+ reviews): keeping top {len(selected)}")
    for i, b in enumerate(selected, 1):
        flag = "🔴" if b["rating"] <= 3.5 else "🟡" if b["rating"] <= 4.2 else "🟢"
        print(f"    {i:2}. {flag} {b['rating']}⭐ ({b['review_count']} reviews, "
              f"{b['one_star_pct']}% 1-star) — {b['name']}")

    return selected


# ── Step 2: Pull Reviews ──────────────────────────────────────────────────────
def pull_reviews(business):
    """
    Standard async reviews: task_post → poll task_get.
    Cost: $0.00075 per 10 reviews.
    """
    name     = business["name"]
    place_id = business.get("place_id")

    if not place_id:
        print(f"    ⚠️  No place_id — skipping '{name}'")
        return []

    # Use keyword + location — more reliable than place_id across endpoints
    payload = [{
        "keyword":       name,
        "location_name": LOCATION,
        "language_name": "English",
        "depth":         REVIEW_DEPTH,
        "sort_by":       REVIEW_SORT,
    }]

    try:
        post_data = api_post("/v3/business_data/google/reviews/task_post", payload)
        task_id   = post_data["tasks"][0]["id"]
        print(f"    ⏳ Task posted (id: {task_id[:8]}...), waiting 20s before polling...")
    except Exception as e:
        print(f"    ❌  Failed to post task for '{name}': {e}")
        return []

    # Wait before first poll
    time.sleep(20)

    # Poll up to 120 seconds (24 attempts × 5 seconds)
    # DataForSEO status codes:
    #   20000 = done/success
    #   20100 = task queued (still waiting)
    #   20010 = task in progress
    # Anything else = real error
    for attempt in range(24):
        time.sleep(5)
        try:
            result = api_get(f"/v3/business_data/google/reviews/task_get/{task_id}")
        except Exception as e:
            print(f"    ⚠️  Poll error attempt {attempt+1}: {e}")
            continue

        tasks  = result.get("tasks", [])
        if not tasks:
            print(f"    ⚠️  Empty response on attempt {attempt+1}, retrying...")
            continue

        status = tasks[0].get("status_code")
        msg    = tasks[0].get("status_message", "")

        if status == 20000:
            # Success — extract reviews
            result_list = tasks[0].get("result") or []
            if result_list:
                items = result_list[0].get("items") or []
                return items
            return []
        elif status in (20100, 20010):
            # Still queued or in progress — keep waiting
            print(f"    ⏳ Attempt {attempt+1}: {msg} — waiting...")
            continue
        else:
            # Real error
            print(f"    ❌ Task failed for '{name}': status {status} — {msg}")
            print(f"       Full task response: {json.dumps(tasks[0], indent=2)[:500]}")
            return []

    print(f"    ⏰  Timed out after 120s for '{name}'")
    return []


# ── Step 3: Analyze Reviews ───────────────────────────────────────────────────
def flag_missed_calls(text):
    if not text:
        return []
    lower = text.lower()
    return [kw for kw in MISSED_CALL_KEYWORDS if kw in lower]


def analyze_reviews(reviews):
    flagged             = []
    unanswered_low_star = 0

    for r in reviews:
        text         = r.get("review_text") or ""
        stars        = (r.get("rating") or {}).get("value", 5)
        signals      = flag_missed_calls(text)
        has_response = bool(r.get("owner_answer"))

        if stars <= 2 and not has_response:
            unanswered_low_star += 1

        if signals:
            flagged.append({
                "stars":         stars,
                "text_preview":  text[:400].replace("\n", " "),
                "signals":       signals,
                "date":          r.get("time_ago", ""),
                "reviewer":      r.get("profile_name", "Anonymous"),
                "owner_replied": has_response,
            })

    return flagged, unanswered_low_star


# ── Output ────────────────────────────────────────────────────────────────────
def save_csv(results, output_file, label):
    rows = []
    for biz, flagged, unanswered in results:
        sample_quote   = flagged[0]["text_preview"][:300] if flagged else ""
        sample_signals = ", ".join(flagged[0]["signals"])   if flagged else ""
        lead_score     = len(flagged) * 3 + unanswered

        rows.append({
            "SEARCH_TYPE":           label,
            "LEAD_SCORE":            lead_score,
            "name":                  biz["name"],
            "phone":                 biz["phone"],
            "website":               biz["website"],
            "address":               biz["address"],
            "rating":                biz["rating"],
            "review_count":          biz["review_count"],
            "one_star_count":        biz["one_star_count"],
            "one_star_pct":          biz["one_star_pct"],
            "is_claimed":            biz["is_claimed"],
            "missed_call_reviews":   len(flagged),
            "unanswered_complaints": unanswered,
            "owner_ignoring":        unanswered > 0,
            "sample_complaint":      sample_quote,
            "matched_keywords":      sample_signals,
            "place_id":              biz["place_id"],
            "contact_url":           biz["contact_url"],
        })

    rows.sort(key=lambda x: -x["LEAD_SCORE"])

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    return rows


def print_summary(rows, label):
    print(f"\n{'─'*55}")
    print(f"  TOP LEADS — {label}")
    print(f"{'─'*55}")
    for r in rows[:5]:
        flag = "🔴" if r["LEAD_SCORE"] >= 6 else "🟡" if r["LEAD_SCORE"] >= 3 else "🟢"
        print(f"\n  {flag} [{r['LEAD_SCORE']} pts] {r['name']}")
        print(f"     📞 {r['phone']}")
        print(f"     ⭐ {r['rating']} | {r['review_count']} reviews | "
              f"{r['one_star_pct']}% 1-star")
        print(f"     🚨 Missed-call signals: {r['missed_call_reviews']} | "
              f"Unanswered complaints: {r['unanswered_complaints']}")
        if r["sample_complaint"]:
            print(f"     💬 \"{r['sample_complaint'][:160]}...\"")
        if r["matched_keywords"]:
            print(f"     🔑 Keywords: {r['matched_keywords']}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print(f"\n{'='*60}")
    print(f"DataForSEO — HVAC Dallas Lead Finder (DUAL SEARCH)")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    print(f"\nSearches: {len(SEARCHES)}")
    for s in SEARCHES:
        print(f"  [{s['label']}] \"{s['keyword']}\" → {s['output_file']}")

    total_biz = MAX_BUSINESSES * len(SEARCHES)
    cost_serp    = 0.002 * len(SEARCHES)
    cost_reviews = total_biz * (REVIEW_DEPTH / 10) * 0.00075
    print(f"\nEst. total cost: ${cost_serp + cost_reviews:.4f}")
    print(f"  SERP calls: {len(SEARCHES)} × $0.002 = ${cost_serp:.4f}")
    print(f"  Reviews: {total_biz} biz × {REVIEW_DEPTH} reviews = ${cost_reviews:.4f}")

    if not DATAFORSEO_LOGIN or not DATAFORSEO_PASSWORD:
        print("\n❌ ERROR: Credentials missing.")
        print(f"   Expected .env file at: {_env_path}")
        print("   It should contain:")
        print("     DATAFORSEO_LOGIN=you@email.com")
        print("     DATAFORSEO_PASSWORD=yourpassword")
        return

    # Show what credentials we parsed (password masked)
    print(f"\n🔑 Login:    {DATAFORSEO_LOGIN}")
    print(f"🔑 Password: {'*' * len(DATAFORSEO_PASSWORD)} ({len(DATAFORSEO_PASSWORD)} chars)")

    # Quick credential test before running
    print(f"\n🧪 Testing credentials against DataForSEO...")
    try:
        test = api_get("/v3/appendix/user_data")
        balance = test.get("tasks", [{}])[0].get("result", [{}])[0].get("money_balance", "unknown")
        print(f"✅ Credentials valid! Account balance: ${balance}")
    except Exception as e:
        print(f"❌ Credential test FAILED: {e}")
        print(f"   Double-check your DataForSEO login email and password.")
        print(f"   Login used: {DATAFORSEO_LOGIN}")
        return

    # Run each search independently
    for search in SEARCHES:
        label       = search["label"]
        keyword     = search["keyword"]
        output_file = search["output_file"]

        print(f"\n{'='*60}")
        print(f"SEARCH: {label}")
        print(f"Query:  \"{keyword}\"")
        print(f"Output: {output_file}")
        print(f"{'='*60}")

        # Discover
        print(f"\n[1/3] Maps SERP — $0.002")
        businesses = discover_businesses(keyword)

        if not businesses:
            print(f"  No businesses found for '{keyword}'. Skipping.")
            continue

        # Reviews
        print(f"\n[2/3] Pulling {REVIEW_DEPTH} reviews per business...")
        results = []
        for i, biz in enumerate(businesses, 1):
            print(f"  [{i}/{len(businesses)}] {biz['name']}")
            reviews              = pull_reviews(biz)
            flagged, unanswered  = analyze_reviews(reviews)
            print(f"    → {len(reviews)} reviews | {len(flagged)} signals | "
                  f"{unanswered} unanswered complaints")
            results.append((biz, flagged, unanswered))

            if i < len(businesses):
                time.sleep(1)

        # Save
        print(f"\n[3/3] Saving to {output_file}...")
        rows = save_csv(results, output_file, label)
        print(f"  ✅ {len(rows)} businesses saved")

        # Summary
        hot = sum(1 for r in rows if r["LEAD_SCORE"] > 0)
        print(f"  🎯 {hot} of {len(rows)} businesses show missed-call signals")
        print_summary(rows, label)

    # Final totals
    print(f"\n{'='*60}")
    print(f"ALL DONE")
    print(f"{'='*60}")
    for s in SEARCHES:
        print(f"  {s['label']:12} → {s['output_file']}")
    print(f"\n💰 Approx spend: ${cost_serp + cost_reviews:.4f}")
    print(f"📌 Next step: open the CSV files and sort by LEAD_SCORE (highest first)")


if __name__ == "__main__":
    main()
