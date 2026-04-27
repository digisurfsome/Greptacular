#!/usr/bin/env python3
"""
DataForSEO — HVAC Dallas Lead Finder
=====================================
Runs TWO separate keyword searches and keeps results completely separate.

Search A: "HVAC companies Dallas Texas"      → hvac_dallas_standard.csv
Search B: "emergency HVAC Dallas Texas"      → hvac_dallas_emergency.csv

Lean workflow: Maps SERP → filter low-rated → pull reviews → flag missed calls.

Cost estimate for this run (20 businesses × 10 reviews × 2 searches):
  2 Maps SERP calls          = $0.004
  40 review pulls × 10 depth = $0.030  ($0.00075 per 10 reviews)
  Total                      ≈ $0.034

Usage:
  Set your DataForSEO credentials as environment variables, then run:
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
DATAFORSEO_LOGIN    = os.environ.get("DATAFORSEO_LOGIN",    "YOUR_LOGIN_EMAIL")
DATAFORSEO_PASSWORD = os.environ.get("DATAFORSEO_PASSWORD", "YOUR_PASSWORD")

BASE_URL = "https://api.dataforseo.com"

# ── Search Config ─────────────────────────────────────────────────────────────
LOCATION        = "Dallas,Texas,United States"
MAX_BUSINESSES  = 20        # how many leads to pull reviews for (per search)
REVIEW_DEPTH    = 10        # reviews per business — 10 to test, bump to 50 for real runs
REVIEW_SORT     = "lowest_rating"   # "lowest_rating" | "newest" | "highest_rating"
MIN_REVIEWS     = 5         # skip businesses with fewer reviews than this

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
    "no response",
    "never responded",
    "after hours",
    "answering machine",
]

# ── HTTP Helper ───────────────────────────────────────────────────────────────
auth = HTTPBasicAuth(DATAFORSEO_LOGIN, DATAFORSEO_PASSWORD)

def api_post(endpoint, payload):
    resp = requests.post(f"{BASE_URL}{endpoint}", json=payload, auth=auth, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    if data.get("status_code") not in (20000, 20100):
        raise RuntimeError(f"API error {data.get('status_code')}: {data.get('status_message')}")
    return data

def api_get(endpoint):
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
        one_star     = dist.get("1", 0)
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
        print(f"    ❌  Failed to post task for '{name}': {e}")
        return []

    # Poll up to 90 seconds
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
            continue  # still processing
        else:
            msg = tasks[0].get("status_message", "unknown error")
            print(f"    ⚠️  Task error for '{name}': {status} — {msg}")
            return []

    print(f"    ⏰  Timed out for '{name}'")
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

    if "YOUR_" in DATAFORSEO_LOGIN:
        print("\n❌ ERROR: Set your DataForSEO credentials first.")
        print("   export DATAFORSEO_LOGIN=you@email.com")
        print("   export DATAFORSEO_PASSWORD=yourpassword")
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
