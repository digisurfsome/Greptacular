"""
hooks/seo_rankings.py — Hook 1: SEO Rankings via DataForSEO

Niche: Local service businesses (plumbers, roofers, HVAC, lawyers, dentists...)
Data source: DataForSEO organic SERP API
"""

import os
import sys

# Allow running from parent dir
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from keyword_discovery import get_keywords
from serp_search import get_top_competitors, search_all_keywords

from hooks.base import HookModule


class SEORankingsHook(HookModule):
    name = "seo_rankings"
    required_env_vars = ["DATAFORSEO_LOGIN", "DATAFORSEO_PASSWORD"]
    required_input_columns = ["niche", "city", "domain"]
    output_columns = [
        "kw1", "kw1_rank", "kw1_traffic",
        "kw2", "kw2_rank", "kw2_traffic",
        "kw3", "kw3_rank", "kw3_traffic",
        "top_competitor", "top_traffic",
    ]

    TIER_ANGLES = {
        "A": (
            "{top_competitor} owns {kw2} — estimated ${top_traffic}/mo in traffic. "
            "{business_name} is right there at #{kw2_rank}. Gap is closable."
        ),
        "B": (
            "{business_name} ranks #{kw1_rank} for '{kw1}' in {city}. "
            "{top_competitor} is at #1 pulling ~${top_traffic}/mo. "
            "Page 1 is the difference between phone calls and silence."
        ),
        "C": (
            "{business_name} is buried at #{kw1_rank} for '{kw1}'. "
            "Page 2 gets less than 1% of clicks. "
            "{top_competitor} is at #1 with an estimated ${top_traffic}/mo in traffic from that keyword alone."
        ),
        "D": (
            "{top_competitor} owns '{kw1}' in {city} — Google, Bing, and now AI Search. "
            "AI Search results are still wide open. Nobody's claimed that position yet."
        ),
    }

    def fetch_data(self, row: dict) -> dict:
        niche = row.get("niche", "")
        city = row.get("city", "")
        state = row.get("state", "")
        domain = row.get("domain", "").replace("www.", "").lower()

        city_label = f"{city} {state}".strip()
        keywords = get_keywords(niche, city_label)
        serp_results = search_all_keywords(keywords, city, state)

        output = {}

        for i, kw in enumerate(keywords[:3], 1):
            kw_key = f"kw{i}"
            output[kw_key] = kw
            output[f"{kw_key}_rank"] = None
            output[f"{kw_key}_traffic"] = 0

            results = serp_results.get(kw, [])
            for result in results:
                result_domain = result.get("domain", "").replace("www.", "").lower()
                if result_domain == domain or domain in result_domain or result_domain in domain:
                    output[f"{kw_key}_rank"] = result["rank"]
                    output[f"{kw_key}_traffic"] = result["traffic_estimate"]
                    break

        top_comps = get_top_competitors(serp_results, top_n=1)
        if top_comps:
            output["top_competitor"] = top_comps[0]["domain"]
            output["top_traffic"] = int(top_comps[0]["avg_traffic"])
        else:
            output["top_competitor"] = ""
            output["top_traffic"] = 0

        return output

    def assign_tier(self, data: dict) -> str:
        ranks = [
            data.get("kw1_rank"),
            data.get("kw2_rank"),
            data.get("kw3_rank"),
        ]
        ranks = [r for r in ranks if r is not None]

        if not ranks:
            return "D"

        best = min(ranks)
        if best <= 3:
            return "A"
        elif best <= 10:
            return "B"
        elif best <= 20:
            return "C"
        return "D"
