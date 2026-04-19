"""
build_list.py — Build enriched business list for outreach.

Pipeline:
  1. Read input CSV (business_name, website_url, niche, city, state)
     OR pass niche + city to auto-generate from SERP data
  2. For each business, find their ranking across the 3 keywords
  3. Assign tier: A (1-3), B (4-10), C (11-20), D (not ranked)
  4. Find top competitor stats for each keyword
  5. Write enriched CSV ready for assemble_emails.py

Output columns per business:
  business_name, website_url, niche, city, state, domain,
  kw1, kw1_rank, kw1_traffic,
  kw2, kw2_rank, kw2_traffic,
  kw3, kw3_rank, kw3_traffic,
  top_competitor, top_traffic,
  tier

Usage:
  # From existing business list:
  python build_list.py --input businesses.csv --output enriched.csv

  # Auto-build from SERP (finds all businesses ranking in top 20):
  python build_list.py --niche plumber --city Austin --state Texas --output enriched.csv
"""

import csv
import json
import argparse
import sys
from typing import List, Dict, Optional
from urllib.parse import urlparse

from keyword_discovery import get_keywords
from serp_search import search_all_keywords, get_top_competitors

# Directories, aggregators, and national chains that are NOT outreach targets
EXCLUDED_DOMAINS = {
    # Directories / review sites
    "yelp.com", "yellowpages.com", "angi.com", "angieslist.com", "thumbtack.com",
    "homeadvisor.com", "houzz.com", "porch.com", "bark.com", "nextdoor.com",
    "bbb.org", "manta.com", "chamberofcommerce.com", "mapquest.com",
    "tripadvisor.com", "foursquare.com", "citysearch.com",
    # Search / social
    "google.com", "bing.com", "yahoo.com", "facebook.com", "instagram.com",
    "twitter.com", "linkedin.com", "youtube.com", "reddit.com", "tiktok.com",
    "pinterest.com",
    # National chains (not local businesses)
    "rotorooter.com", "servicemaster.com", "servpro.com", "terminix.com",
    "rentacenter.com", "lowes.com", "homedepot.com",
    # Info / media / news
    "wikipedia.org", "wikihow.com", "bobvila.com", "thisoldhouse.com",
    "familyhandyman.com", "consumeraffairs.com",
    "forbes.com", "statesman.com", "nytimes.com", "usatoday.com",
    "businessinsider.com", "cnet.com", "tomshardware.com",
    # Job boards
    "indeed.com", "glassdoor.com", "ziprecruiter.com", "monster.com", "careerbuilder.com",
}


def is_excluded(domain: str) -> bool:
    domain = domain.lower().replace("www.", "")
    if domain in EXCLUDED_DOMAINS:
        return True
    # Also exclude subdomains of excluded domains
    for excl in EXCLUDED_DOMAINS:
        if domain.endswith("." + excl):
            return True
    return False


def extract_domain(url: str) -> str:
    """Extract clean domain from URL."""
    if not url:
        return ""
    if not url.startswith("http"):
        url = "https://" + url
    try:
        return urlparse(url).netloc.replace("www.", "").lower().strip()
    except Exception:
        return url.lower().strip()


def find_business_rankings(domain: str, serp_results: Dict[str, List[Dict]]) -> Dict:
    """
    Given a domain and SERP results, find where that domain ranks for each keyword.
    Returns dict with kw1/kw2/kw3 rank and traffic data.
    """
    keywords = list(serp_results.keys())
    ranking_data = {}

    for i, kw in enumerate(keywords[:3], 1):
        kw_key = f"kw{i}"
        ranking_data[f"{kw_key}"] = kw
        ranking_data[f"{kw_key}_rank"] = None
        ranking_data[f"{kw_key}_traffic"] = 0

        for result in serp_results[kw]:
            result_domain = result.get("domain", "").replace("www.", "").lower()
            if result_domain == domain or domain in result_domain or result_domain in domain:
                ranking_data[f"{kw_key}_rank"] = result["rank"]
                ranking_data[f"{kw_key}_traffic"] = result["traffic_estimate"]
                break

    return ranking_data


def assign_tier(kw1_rank: Optional[int], kw2_rank: Optional[int], kw3_rank: Optional[int]) -> str:
    """
    A = ranked 1-3 on any keyword
    B = ranked 4-10 on any keyword
    C = ranked 11-20 on any keyword
    D = not in top 20 anywhere
    """
    ranks = [r for r in [kw1_rank, kw2_rank, kw3_rank] if r is not None]
    if not ranks:
        return "D"

    best_rank = min(ranks)
    if best_rank <= 3:
        return "A"
    elif best_rank <= 10:
        return "B"
    elif best_rank <= 20:
        return "C"
    return "D"


def build_from_serp(niche: str, city: str, state: str = "") -> List[Dict]:
    """
    Auto-build business list from SERP results — finds every domain in top 20
    across all keywords and builds a row for each.
    """
    print(f"[build_list] Discovering keywords for {niche} in {city} {state}...")
    city_label = f"{city} {state}".strip()
    keywords = get_keywords(niche, city_label)

    print(f"[build_list] Keywords: {keywords}")
    serp_results = search_all_keywords(keywords, city, state)

    # Collect all unique domains from results
    seen_domains = set()
    businesses = []

    for kw, results in serp_results.items():
        for r in results:
            domain = r["domain"].replace("www.", "").lower()
            if domain and domain not in seen_domains and not is_excluded(domain):
                seen_domains.add(domain)
                businesses.append({
                    "business_name": r["title"] or domain,
                    "website_url": r["url"],
                    "domain": domain,
                    "niche": niche,
                    "city": city,
                    "state": state,
                    # Carry phone/rating from local_pack if available
                    "phone": r.get("phone") or "",
                    "google_rating": r.get("rating") or "",
                    "review_count": r.get("review_count") or "",
                })

    # Get top competitor stats
    top_comps = get_top_competitors(serp_results, top_n=1)
    top_comp_domain = top_comps[0]["domain"] if top_comps else ""
    top_comp_traffic = top_comps[0]["avg_traffic"] if top_comps else 0

    # Enrich each business with ranking data
    enriched = []
    for biz in businesses:
        domain = biz["domain"]
        ranking = find_business_rankings(domain, serp_results)

        tier = assign_tier(
            ranking.get("kw1_rank"),
            ranking.get("kw2_rank"),
            ranking.get("kw3_rank"),
        )

        row = {
            **biz,
            **ranking,
            "top_competitor": top_comp_domain,
            "top_traffic": int(top_comp_traffic),
            "tier": tier,
        }
        enriched.append(row)

    # Sort by tier then best rank
    def sort_key(r):
        tier_order = {"A": 0, "B": 1, "C": 2, "D": 3}
        ranks = [r.get(f"kw{i}_rank") for i in range(1, 4)]
        ranks = [x for x in ranks if x is not None]
        best = min(ranks) if ranks else 99
        return (tier_order.get(r["tier"], 4), best)

    enriched.sort(key=sort_key)
    return enriched


def build_from_csv(input_path: str, niche: str = None, city: str = None,
                   state: str = None) -> List[Dict]:
    """
    Enrich existing CSV of businesses with ranking data.
    CSV must have: business_name, website_url
    Optional columns: niche, city, state (or pass as args for uniform batch)
    """
    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print("[build_list] Empty input CSV")
        return []

    # Group by niche+city so we batch SERP calls
    groups = {}
    for row in rows:
        n = niche or row.get("niche", "").strip()
        c = city or row.get("city", "").strip()
        s = state or row.get("state", "").strip()
        key = f"{n}|{c}|{s}"
        if key not in groups:
            groups[key] = {"niche": n, "city": c, "state": s, "rows": []}
        groups[key]["rows"].append(row)

    enriched_all = []

    for group_key, group in groups.items():
        n, c, s = group["niche"], group["city"], group["state"]
        print(f"\n[build_list] Processing group: {n} / {c} {s} ({len(group['rows'])} businesses)")

        city_label = f"{c} {s}".strip()
        keywords = get_keywords(n, city_label)
        serp_results = search_all_keywords(keywords, c, s)

        top_comps = get_top_competitors(serp_results, top_n=1)
        top_comp_domain = top_comps[0]["domain"] if top_comps else ""
        top_comp_traffic = top_comps[0]["avg_traffic"] if top_comps else 0

        for row in group["rows"]:
            domain = extract_domain(row.get("website_url", ""))
            ranking = find_business_rankings(domain, serp_results)

            # Fill keywords if not already set
            keywords_list = list(serp_results.keys())
            for i in range(1, 4):
                if f"kw{i}" not in ranking and i <= len(keywords_list):
                    ranking[f"kw{i}"] = keywords_list[i - 1]
                    ranking[f"kw{i}_rank"] = ranking.get(f"kw{i}_rank")
                    ranking[f"kw{i}_traffic"] = ranking.get(f"kw{i}_traffic", 0)

            tier = assign_tier(
                ranking.get("kw1_rank"),
                ranking.get("kw2_rank"),
                ranking.get("kw3_rank"),
            )

            enriched_row = {
                "business_name": row.get("business_name", ""),
                "website_url": row.get("website_url", ""),
                "domain": domain,
                "niche": n,
                "city": c,
                "state": s,
                **ranking,
                "top_competitor": top_comp_domain,
                "top_traffic": int(top_comp_traffic),
                "tier": tier,
            }
            enriched_all.append(enriched_row)

    return enriched_all


OUTPUT_COLUMNS = [
    "business_name", "website_url", "domain", "niche", "city", "state",
    "kw1", "kw1_rank", "kw1_traffic",
    "kw2", "kw2_rank", "kw2_traffic",
    "kw3", "kw3_rank", "kw3_traffic",
    "top_competitor", "top_traffic",
    "tier",
]


def write_csv(rows: List[Dict], output_path: str):
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n[build_list] Wrote {len(rows)} rows to {output_path}")


def print_summary(rows: List[Dict]):
    from collections import Counter
    tiers = Counter(r["tier"] for r in rows)
    print("\n--- Tier Summary ---")
    for tier in ["A", "B", "C", "D"]:
        count = tiers.get(tier, 0)
        print(f"  Tier {tier}: {count} businesses")
    print(f"  Total: {len(rows)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build enriched business list for outreach")
    parser.add_argument("--input", help="Input CSV of businesses (optional)")
    parser.add_argument("--output", required=True, help="Output enriched CSV path")
    parser.add_argument("--niche", help="Niche (e.g. 'plumber')")
    parser.add_argument("--city", help="City (e.g. 'Austin')")
    parser.add_argument("--state", help="State (e.g. 'Texas')")

    args = parser.parse_args()

    if args.input:
        rows = build_from_csv(args.input, args.niche, args.city, args.state)
    elif args.niche and args.city:
        rows = build_from_serp(args.niche, args.city, args.state or "")
    else:
        print("Error: provide --input CSV or --niche + --city")
        sys.exit(1)

    write_csv(rows, args.output)
    print_summary(rows)
