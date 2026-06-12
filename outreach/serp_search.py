"""
serp_search.py — Search DataForSEO for local business rankings.

For each keyword, fetches top 20 organic results and extracts:
- Business domain + name (from Google local pack if available, else organic)
- Rank position
- Estimated monthly traffic value

Outputs a list of dicts ready for build_list.py to cross-reference.

DataForSEO pricing: ~$0.0015 per SERP request (3 keywords = ~$0.005/city)
"""

import base64
import os
import time
from typing import Dict, List

import requests

DATAFORSEO_LOGIN = os.getenv("DATAFORSEO_LOGIN")
DATAFORSEO_PASSWORD = os.getenv("DATAFORSEO_PASSWORD")

DATAFORSEO_BASE = "https://api.dataforseo.com/v3"

# Language/location defaults — override per call if needed
DEFAULT_LANGUAGE = "en"
DEFAULT_LOCATION_CODE = 2840  # United States


def _auth_header() -> dict:
    creds = base64.b64encode(f"{DATAFORSEO_LOGIN}:{DATAFORSEO_PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {creds}", "Content-Type": "application/json"}


def search_keyword(keyword: str, location_name: str = None, location_code: int = None,
                   depth: int = 100) -> List[Dict]:
    """
    Run a Google organic SERP search for keyword.
    Returns list of result dicts: {rank, domain, title, url, traffic_estimate}

    Use location_name (e.g. "Austin,Texas,United States") OR location_code.
    If neither provided, uses DEFAULT_LOCATION_CODE (US).
    """
    payload = [{
        "keyword": keyword,
        "language_code": DEFAULT_LANGUAGE,
        "depth": depth,
        "calculate_rectangles": False,
    }]

    if location_name:
        payload[0]["location_name"] = location_name
    else:
        payload[0]["location_code"] = location_code or DEFAULT_LOCATION_CODE

    try:
        resp = requests.post(
            f"{DATAFORSEO_BASE}/serp/google/organic/live/regular",
            headers=_auth_header(),
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[serp_search] API error for '{keyword}': {e}")
        return []

    results = []
    try:
        tasks = data.get("tasks", [])
        if not tasks or tasks[0].get("status_code") != 20000:
            print(f"[serp_search] Bad task status for '{keyword}': {tasks[0].get('status_message')}")
            return []

        items = tasks[0]["result"][0].get("items", [])

        # Track local_pack rank separately — these are the Google Maps 3-pack.
        # For local service searches they appear ABOVE organic results and dominate
        # phone calls. We give local_pack businesses effective organic ranks 1-3.
        local_pack_count = 0

        for item in items:
            item_type = item.get("type")

            if item_type == "local_pack":
                # Skip paid local pack entries
                if item.get("is_paid"):
                    continue
                local_pack_count += 1
                domain = item.get("domain", "").replace("www.", "")
                title = item.get("title", "")
                url = item.get("url", "")

                # Pull rating data — useful for reviews hook later
                rating = item.get("rating") or {}

                results.append({
                    "rank": local_pack_count,  # 1, 2, 3 — maps pack position
                    "domain": domain,
                    "title": title,
                    "url": url,
                    "traffic_estimate": 0,
                    "result_type": "local_pack",
                    "rating": rating.get("value"),
                    "review_count": rating.get("votes_count"),
                    "phone": item.get("phone"),
                })
                continue

            if item_type != "organic":
                continue

            rank = item.get("rank_absolute")
            url = item.get("url", "")
            domain = item.get("domain", "")
            title = item.get("title", "")
            etv = item.get("etv", 0) or 0

            results.append({
                "rank": rank,
                "domain": domain,
                "title": title,
                "url": url,
                "traffic_estimate": etv,
                "result_type": "organic",
                "rating": None,
                "review_count": None,
                "phone": None,
            })
    except (KeyError, IndexError, TypeError) as e:
        print(f"[serp_search] Parse error for '{keyword}': {e}")

    return results


def search_all_keywords(keywords: List[str], city: str, state: str = "") -> Dict[str, List[Dict]]:
    """
    Search all keywords for a city, respecting API rate limits.
    Returns dict: {keyword: [results]}
    """
    # Format location for DataForSEO: "City,State,United States"
    if state:
        location_name = f"{city},{state},United States"
    else:
        location_name = f"{city},United States"

    all_results = {}

    for i, kw in enumerate(keywords):
        if i > 0:
            time.sleep(0.5)  # Avoid hammering the API

        print(f"  Searching: {kw}")
        results = search_keyword(kw, location_name=location_name)
        all_results[kw] = results

        if results:
            print(f"    Got {len(results)} results, top: {results[0]['domain']}")

    return all_results


def get_top_competitors(serp_results: Dict[str, List[Dict]], top_n: int = 3) -> List[Dict]:
    """
    From SERP results across all keywords, identify the top N competitor domains
    by frequency and rank.

    Returns list of {domain, best_rank, keyword_count, avg_traffic}
    """
    # Import here to avoid circular dependency with build_list
    try:
        from build_list import is_excluded
    except ImportError:
        def is_excluded(d): return False

    domain_stats = {}

    for keyword, results in serp_results.items():
        for r in results[:20]:
            domain = r["domain"]
            if not domain or is_excluded(domain.replace("www.", "").lower()):
                continue

            if domain not in domain_stats:
                domain_stats[domain] = {
                    "domain": domain,
                    "best_rank": r["rank"],
                    "keyword_count": 0,
                    "total_traffic": 0,
                    "keywords_ranked": [],
                }

            stats = domain_stats[domain]
            stats["keyword_count"] += 1
            stats["total_traffic"] += r["traffic_estimate"]
            stats["keywords_ranked"].append(keyword)
            if r["rank"] < stats["best_rank"]:
                stats["best_rank"] = r["rank"]

    # Sort by keyword count (appears most), then best rank
    sorted_domains = sorted(
        domain_stats.values(),
        key=lambda x: (-x["keyword_count"], x["best_rank"])
    )

    # Compute avg traffic
    for d in sorted_domains:
        d["avg_traffic"] = d["total_traffic"] / d["keyword_count"] if d["keyword_count"] > 0 else 0

    return sorted_domains[:top_n]


if __name__ == "__main__":
    # Test with a single keyword — requires env vars set
    if not DATAFORSEO_LOGIN:
        print("Set DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD env vars")
    else:
        from keyword_discovery import get_keywords

        niche = "plumber"
        city = "Austin"
        state = "Texas"

        keywords = get_keywords(niche, f"{city} {state}")
        print(f"Keywords for {niche} in {city}, {state}:")
        for kw in keywords:
            print(f"  {kw}")

        print("\nSearching SERPs...")
        results = search_all_keywords(keywords, city, state)

        print("\nTop competitors:")
        competitors = get_top_competitors(results)
        for c in competitors:
            print(f"  {c['domain']} — best rank #{c['best_rank']}, "
                  f"in {c['keyword_count']} keywords, avg traffic {c['avg_traffic']:.1f}")
