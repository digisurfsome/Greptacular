"""
classify_businesses.py — AI-powered national chain / non-business classifier.

Uses Claude Haiku to flag domains that are NOT outreach targets:
  - National chains (Roto-Rooter, ServiceMaster, HomeAdvisor...)
  - Directories (Yelp, Angi, BBB...)
  - Media / news sites (Forbes, local newspaper...)
  - Job boards, social networks, etc.

Runs ONCE per niche and caches the result. Never re-runs for the same niche.
Cost: ~$0.001 per niche (tiny Haiku call, cached forever after).

Domains NOT in the classifier result are assumed to be local businesses.
"""

import os
import json
import anthropic
from pathlib import Path
from typing import Set, List

CACHE_DIR = Path(__file__).parent / ".classifier_cache"
CACHE_DIR.mkdir(exist_ok=True)

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    return _client


def _cache_path(niche: str) -> Path:
    safe = niche.lower().replace(" ", "_").replace("/", "_")
    return CACHE_DIR / f"{safe}_nationals.json"


def get_national_domains(niche: str) -> Set[str]:
    """
    Return set of domains known to be national chains / non-local-businesses
    for this niche. Result is cached — Haiku only called once per niche.
    """
    path = _cache_path(niche)

    if path.exists():
        with open(path) as f:
            data = json.load(f)
        return set(data.get("domains", []))

    domains = _fetch_from_haiku(niche)
    with open(path, "w") as f:
        json.dump({"niche": niche, "domains": sorted(domains)}, f, indent=2)

    return domains


def _fetch_from_haiku(niche: str) -> Set[str]:
    """Ask Haiku for national chain domains in this niche."""
    prompt = (
        f"List the domain names (no www) of national franchise chains, "
        f"large regional chains, and aggregator/directory websites that "
        f"appear in Google search results for the '{niche}' industry. "
        f"Include: national service franchises, lead-gen directories, "
        f"review aggregators, home services marketplaces. "
        f"Do NOT include local businesses or small regional companies. "
        f"Return ONLY a JSON array of domain strings. No explanation."
    )

    try:
        client = _get_client()
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip()

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        if raw.endswith("```"):
            raw = raw.rsplit("```", 1)[0]

        domains = json.loads(raw.strip())
        if isinstance(domains, list):
            return {d.lower().replace("www.", "").strip() for d in domains if isinstance(d, str)}
    except Exception as e:
        print(f"[classifier] Haiku call failed for '{niche}': {e}")

    return set()


def classify_rows(rows: List[dict], niche: str) -> List[dict]:
    """
    Add skip_outreach + skip_reason columns to each row.
    Flags national chains, directories, job boards, media sites.
    Local businesses pass through with skip_outreach=False.
    """
    # Base exclusions always applied (directories, socials, etc.)
    from build_list import EXCLUDED_DOMAINS, is_excluded

    # Niche-specific nationals from Haiku (cached)
    if os.environ.get("ANTHROPIC_API_KEY"):
        national_domains = get_national_domains(niche)
        print(f"[classifier] {len(national_domains)} national domains for '{niche}' niche")
    else:
        national_domains = set()
        print("[classifier] No ANTHROPIC_API_KEY — skipping Haiku classifier, using blocklist only")

    for row in rows:
        domain = row.get("domain", "").lower().replace("www.", "")

        if is_excluded(domain):
            row["skip_outreach"] = True
            row["skip_reason"] = "directory_or_aggregator"
        elif domain in national_domains:
            row["skip_outreach"] = True
            row["skip_reason"] = "national_chain"
        else:
            row["skip_outreach"] = False
            row["skip_reason"] = ""

    skipped = sum(1 for r in rows if r["skip_outreach"])
    print(f"[classifier] {skipped} flagged to skip, {len(rows) - skipped} local businesses ready")
    return rows


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--niche", required=True)
    parser.add_argument("--show-cache", action="store_true")
    args = parser.parse_args()

    if args.show_cache:
        path = _cache_path(args.niche)
        if path.exists():
            print(open(path).read())
        else:
            print(f"No cache yet for '{args.niche}'")
    else:
        domains = get_national_domains(args.niche)
        print(f"\nNational/non-local domains for '{args.niche}':")
        for d in sorted(domains):
            print(f"  {d}")
