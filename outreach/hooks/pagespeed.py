"""
hooks/pagespeed.py — Hook 2: Google PageSpeed / Web Performance

Niche: Web design agencies, dev shops
API: Google PageSpeed Insights (free, no key needed for basic use)
"""

import requests
from hooks.base import HookModule


class PageSpeedHook(HookModule):
    name = "pagespeed"
    required_env_vars = []
    required_input_columns = ["website_url"]
    output_columns = ["perf_score", "top_issue", "lcp_seconds", "cls_score"]

    TIER_ANGLES = {
        "A": (
            "{business_name} scores {perf_score}/100 — strong. "
            "But Google's gap scoring is tightening and {top_competitor} just moved ahead. "
            "First-mover advantage on Core Web Vitals is still real."
        ),
        "B": (
            "{business_name} is at {perf_score}/100 on mobile. "
            "Industry leaders in {niche} are hitting 90+. "
            "Google measures this directly — it affects your local pack ranking."
        ),
        "C": (
            "{business_name} loads in {lcp_seconds}s on mobile. "
            "You're losing an estimated 30% of visitors before they see your phone number. "
            "Score: {perf_score}/100."
        ),
        "D": (
            "{business_name} scores {perf_score}/100. "
            "Google actively penalizes scores below 50 in local rankings. "
            "That's not a theory — it's baked into the Helpful Content and Page Experience updates."
        ),
    }

    def fetch_data(self, row: dict) -> dict:
        url = row.get("website_url", "").strip()
        if not url:
            return {}

        if not url.startswith("http"):
            url = "https://" + url

        api_url = (
            f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
            f"?url={url}&strategy=mobile"
        )

        try:
            r = requests.get(api_url, timeout=20)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"[pagespeed] Error fetching {url}: {e}")
            return {}

        try:
            lighthouse = data["lighthouseResult"]
            score = int(lighthouse["categories"]["performance"]["score"] * 100)
            audits = lighthouse["audits"]

            # LCP
            lcp = audits.get("largest-contentful-paint", {})
            lcp_seconds = lcp.get("displayValue", "?").replace(" s", "")

            # CLS
            cls = audits.get("cumulative-layout-shift", {})
            cls_score = cls.get("displayValue", "?")

            # Find worst failing audit by potential savings
            failing = [
                a for a in audits.values()
                if a.get("score") is not None and a["score"] < 0.5
                and a.get("details", {}).get("overallSavingsMs", 0) > 0
            ]
            if failing:
                worst = max(failing, key=lambda a: a["details"].get("overallSavingsMs", 0))
                top_issue = worst.get("title", "page speed")
            else:
                top_issue = "page load time"

            return {
                "perf_score": score,
                "top_issue": top_issue,
                "lcp_seconds": lcp_seconds,
                "cls_score": cls_score,
            }
        except (KeyError, TypeError) as e:
            print(f"[pagespeed] Parse error for {url}: {e}")
            return {}

    def assign_tier(self, data: dict) -> str:
        score = data.get("perf_score", 50)
        if score >= 90:
            return "A"
        if score >= 70:
            return "B"
        if score >= 50:
            return "C"
        return "D"
