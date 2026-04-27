#!/usr/bin/env python3
"""
DataForSEO — HVAC Dallas Lead Finder
=====================================
Lean workflow: Maps SERP → filter low-rated → pull 50 worst reviews → flag missed calls.

Cost estimate for this run:
  1 Maps SERP call          = $0.002
  50 reviews × 20 businesses = $0.075
  Total                      ≈ $0.077

Usage:
  Set env vars, then run:
    DATAFORSEO_LOGIN=you@email.com DATAFORSEO_PASSWORD=yourpass python hvac_dallas_leads.py

  Or edit the CREDENTIALS block below directly.
"""

import os
import json
import csv
import time
import requests
from datetime import datetime
from requests.auth import HTTPBasicAuth

# ── Credentials ──────────────────────────────────────────────────────────────
# Option 1: set environment variables (recommended)
# Option 2: paste directly here
DATAFORSEO_LOGIN    = os.environ.get("DATAFORSEO_LOGIN", "YOUR_LOGIN_EMAIL")
DATAFORSEO_PASSWORD = os.environ.get("DATAFORSEO_PASSWORD", "YOUR_PASSWORD")

BASE_URL = "https://api.dataforseo.com"

# ── Search Config ─────────────────────────────────────────────────────────────
KEYWORD         = "HVAC companies Dallas Texas"
LOCATION        = "Dallas,Texas,United States"
MAX_BUSINESSES  = 20        # how many leads to pull reviews for
REVIEW_DEPTH    = 50        # reviews per business (50 = $0.00375, 20 = $0.0015)
REVIEW_SORT     = "lowest_rating"   # "lowest_rating" | "newest" | "highest_rating"
MIN_REVIEWS     = 5         # skip businesses with fewer than this many reviews
MAX_RATING      = 4.8       # only pull reviews for businesses at or below this rating
OUTPUT_FILE     = "hvac_dallas_results.csv"

# ── Missed Call Signal Keywords ───────────────────────────────────────────────
MISSED_CALL_KEYWORDS = [
    "no answer",
    "didn't answer",
    "did not answer",
    "voicemail",
    "voice mail",
    "never called back",
    "didn't call back",
    "did not call back",
    "couldn't reach",
    "could not reach",
    "no one picked up",
    "nobody answered",
    "left a message",
    "no return call",
    "unreachable",
    "hard to reach",
    "not available",
    "hung up",
    "disconnect",
    "phone tag",
]

# ── HTTP Helper ───────────────────────────────────────────────────────────────
auth = HTTPBasicAuth(DATAFORSEO_LOGIN, DATAFORSEO_PASSWORD)

def api_post(endpoint, payload):
    """POST to DataForSEO, raise on any error."""
    resp = requests.post(f"{BASE_URL}{endpoint}", json=payload, auth=auth, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    if data.get("status_code") not in (20000, 20100):
        raise RuntimeError(f"API error {data.get('status_code')}: {data.get('status_message')}")
    return data

def api_get(endpoint):
    """GET from DataForSEO."""
    resp = requests.get(f"{BASE_URL}{endpoint}", auth=auth, timeout=60)
    resp.raise_for_status()
    return resp.json()


# ── Step 1: Maps SERP ─────────────────────────────────────────────────────────
def discover_businesses():
    """
    One Maps SERP call → up to 100 businesses.
    Cost: $0.002 flat.
    Returns list sorted worst-rated first.
    """
    print(f"\n{'='*60}")
    print(f"STEP 1 — Maps SERP: '{KEYWORD}'")
    print(f"{'='*60}")
    print(f"Cost: $0.002")

    payload = [{
        "keyword":       KEYWORD,
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

    print(f"Raw results from Google Maps: {len(raw_items)} businesses")

    businesses = []
    for item in raw_items:
        rating_obj  = item.get("rating") or {}
        dist        = rating_obj.get("rating_distribution") or {}
        total       = rating_obj.get("votes_count", 0)
        star_value  = rating_obj.get("value", 5.0) or 5.0
        one_star    = dist.get("1", 0)
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
            "two_star":       dist.get("2", 0),
            "three_star":     dist.get("3", 0),
            "four_star":      dist.get("4", 0),
            "five_star":      dist.get("5", 0),
            "category":       item.get("category", ""),
            "price_level":    item.get("price_level", ""),
            "open_now":       (item.get("work_hours") or {}).get("current_status", ""),
            "total_photos":   item.get("total_photos", 0),
        })

    # Filter: must have minimum reviews
    before = len(businesses)
    businesses = [b for b in businesses if b["review_count"] >= MIN_REVIEWS]
    print(f"After filter (>= {MIN_REVIEWS} reviews): {len(businesses)} of {before}")

    # Sort: worst rated first, then highest 1-star % as tiebreaker
    businesses.sort(key=lambda x: (x["rating"], -x["one_star_pct"]))

    # Cap to MAX_BUSINESSES
    selected = businesses[:MAX_BUSINESSES]

    print(f"\nTop {len(selected)} leads (worst-rated first):")
    for i, b in enumerate(selected, 1):
        flag = "🔴" if b["rating"] <= 3.5 else "🟡" if b["rating"] <= 4.2 else "🟢"
        print(f"  {i:2}. {flag} {b['rating']}⭐ | {b['review_count']} reviews "
              f"| {b['one_star_pct']}% 1-star | {b['name']}")

    return selected


# ── Step 2: Pull Reviews ──────────────────────────────────────────────────────
def pull_reviews(business):
    """
    Standard (async) reviews pull: task_post → poll task_get.
    Cost: $0.00375 for 50 reviews.
    """
    name     = business["name"]
    place_id = business.get("place_id")

    if not place_id:
        print(f"  ⚠️  No place_id for '{name}' — skipping")
        return []

    # Post task
    payload = [{
        "place_id":      place_id,
        "depth":         REVIEW_DEPTH,
        "sort_by":       REVIEW_SORT,
        "language_name": "English",
    }]

    try:
        post_data = api_post("/v3/business_data/google/reviews/task_post", payload)
        task_id   = post_data["tasks"][0]["id"]
    except Exception as e:
        print(f"  ❌  Failed to post review task for '{name}': {e}")
        return []

    # Poll for results (max 90 seconds)
    for attempt in range(18):
        time.sleep(5)
        result = api_get(f"/v3/business_data/google/reviews/task_get/{task_id}")
        tasks  = result.get("tasks", [])

        if not tasks:
            continue

        status = tasks[0].get("status_code")

        if status == 20000:
            items = (tasks[0].get("result") or [{}])[0].get("items") or []
            return items
        elif status in (40602, 40200):
            # Still queued or processing — keep waiting
            continue
        else:
            msg = tasks[0].get("status_message", "unknown error")
            print(f"  ⚠️  Review task error for '{name}': {status} — {msg}")
            return []

    print(f"  ⏰  Timed out waiting for reviews for '{name}'")
    return []


# ── Step 3: Analyze Reviews ───────────────────────────────────────────────────
def flag_missed_calls(text):
    """Return list of matched missed-call keywords."""
    if not text:
        return []
    lower = text.lower()
    return [kw for kw in MISSED_CALL_KEYWORDS if kw in lower]


def analyze_reviews(reviews):
    """
    Returns:
      - flagged: list of reviews with missed-call signals
      - unanswered_complaints: count of 1-2 star reviews with no owner response
    """
    flagged              = []
    unanswered_low_star  = 0

    for r in reviews:
        text     = r.get("review_text") or ""
        stars    = (r.get("rating") or {}).get("value", 5)
        signals  = flag_missed_calls(text)
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
def save_csv(results):
    """Write results to CSV. results = list of (business_dict, flagged, unanswered_count)."""
    rows = []
    for biz, flagged, unanswered in results:
        sample_quote   = flagged[0]["text_preview"][:300] if flagged else ""
        sample_signals = ", ".join(flagged[0]["signals"])   if flagged else ""

        rows.append({
            "LEAD_SCORE":            len(flagged) * 3 + unanswered,  # simple score
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

    # Sort by lead score (highest first)
    rows.sort(key=lambda x: -x["LEAD_SCORE"])

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✅ Saved to {OUTPUT_FILE}")
    return rows


def print_summary(results):
    """Print a clean console summary of top leads."""
    print(f"\n{'='*60}")
    print("TOP AI RECEPTIONIST LEADS — HVAC DALLAS")
    print(f"{'='*60}")

    sorted_results = sorted(results, key=lambda x: -(len(x[1]) * 3 + x[2]))

    for biz, flagged, unanswered in sorted_results[:10]:
        print(f"\n🎯 {biz['name']}")
        print(f"   📞 {biz['phone']}")
        print(f"   🌐 {biz['website']}")
        print(f"   ⭐ {biz['rating']} | {biz['review_count']} reviews | "
              f"{biz['one_star_pct']}% 1-star")
        print(f"   🚨 Missed-call reviews: {len(flagged)} | "
              f"Unanswered complaints: {unanswered}")
        if flagged:
            top = flagged[0]
            print(f"   💬 \"{top['text_preview'][:160]}...\"")
            print(f"   🔑 Keywords found: {', '.join(top['signals'])}")
            print(f"   👤 Owner replied: {top['owner_replied']}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print(f"\nDataForSEO — HVAC Dallas Lead Finder")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nConfig: {MAX_BUSINESSES} businesses | {REVIEW_DEPTH} reviews each | sort: {REVIEW_SORT}")
    cost_reviews = MAX_BUSINESSES * (REVIEW_DEPTH / 10) * 0.00075
    print(f"Est. cost: $0.002 (SERP) + ${cost_reviews:.4f} (reviews) = ${0.002 + cost_reviews:.4f} total")

    # Validate credentials
    if "YOUR_" in DATAFORSEO_LOGIN:
        print("\n❌ ERROR: Set your DataForSEO credentials first.")
        print("   Option A: export DATAFORSEO_LOGIN=you@email.com")
        print("             export DATAFORSEO_PASSWORD=yourpassword")
        print("   Option B: edit the CREDENTIALS block at top of this file")
        return

    # Step 1: Discover
    businesses = discover_businesses()
    if not businesses:
        print("No businesses found. Check credentials/API access.")
        return

    # Step 2 & 3: Reviews + analysis
    print(f"\n{'='*60}")
    print(f"STEP 2 — Pulling {REVIEW_DEPTH} reviews per business")
    print(f"{'='*60}")
    print("Using STANDARD mode (async). Each business takes ~5–30 seconds.")

    results = []
    for i, biz in enumerate(businesses, 1):
        print(f"\n[{i}/{len(businesses)}] {biz['name']} ({biz['rating']}⭐)")
        reviews          = pull_reviews(biz)
        flagged, unanswered = analyze_reviews(reviews)
        print(f"  Reviews fetched: {len(reviews)} | "
              f"Missed-call signals: {len(flagged)} | "
              f"Unanswered 1-2★: {unanswered}")
        results.append((biz, flagged, unanswered))

        if i < len(businesses):
            time.sleep(1)  # brief pause between businesses

    # Output
    print(f"\n{'='*60}")
    print("STEP 3 — Saving results")
    print(f"{'='*60}")
    save_csv(results)
    print_summary(results)

    hot_leads = sum(1 for _, f, u in results if f or u > 0)
    print(f"\n📊 {hot_leads} of {len(businesses)} businesses show missed-call signals.")
    print(f"💰 Approx spend: ${0.002 + (len(businesses) * (REVIEW_DEPTH / 10) * 0.00075):.4f}")
    print(f"\nDone. Open {OUTPUT_FILE} to see full data.")


if __name__ == "__main__":
    main()
