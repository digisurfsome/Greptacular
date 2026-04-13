"""
Idea Validator — Automated App Idea Validation via Market Scraper
=================================================================

Takes a list of app ideas, generates smart search queries for each,
runs them through the existing Market Scraper API, collects all results,
and produces a ranked validation report.

Usage:
    python scripts/idea-validator.py                    # Run all ideas from ideas.json
    python scripts/idea-validator.py --idea "Sugar Scanner"  # Run one idea by name
    python scripts/idea-validator.py --report           # Show report from last run
    python scripts/idea-validator.py --top 5            # Show top 5 ideas only

Requires: AutoForge running on localhost:8888
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

AUTOFORGE_URL = os.getenv("AUTOFORGE_URL", "http://localhost:8888")
API_BASE = f"{AUTOFORGE_URL}/api/market-scraper"
IDEAS_FILE = Path(__file__).parent / "ideas.json"
RESULTS_FILE = Path(__file__).parent / "validation-results.json"
REPORT_FILE = Path(__file__).parent / "validation-report.md"

# Pause between scrapes to respect Reddit rate limits (seconds)
SCRAPE_DELAY = 8

# Search config per query
DEFAULT_SORT = "relevance"
DEFAULT_TIME = "year"
DEFAULT_THREADS = 5


# ---------------------------------------------------------------------------
# Search query templates — these are the different "angles" to search from
# ---------------------------------------------------------------------------

QUERY_TEMPLATES = [
    # Direct problem search
    "{keyword} frustrations",
    "{keyword} problems",
    # Alternative seeking
    "looking for {keyword}",
    "{keyword} alternative",
    "best {keyword} app",
    # Pain-based
    "hate {keyword}",
    "why is {keyword} so hard",
    # Validation signals
    "would pay for {keyword}",
    "I wish there was {keyword}",
    # Competitor complaints
    "{competitor} sucks",
    "{competitor} alternative",
]


def generate_queries(idea: dict) -> list[str]:
    """Generate search queries from an idea's keywords and competitors."""
    queries = []
    keywords = idea.get("keywords", [])
    competitors = idea.get("competitors", [])
    custom_queries = idea.get("queries", [])

    # Add custom queries first (highest priority)
    queries.extend(custom_queries)

    # Generate from keywords
    for kw in keywords:
        queries.append(f"{kw} frustrations")
        queries.append(f"{kw} problems")
        queries.append(f"looking for {kw}")
        queries.append(f"{kw} alternative")
        queries.append(f"I wish there was {kw}")

    # Generate from competitors
    for comp in competitors:
        queries.append(f"{comp} alternative")
        queries.append(f"{comp} problems")
        queries.append(f"switching from {comp}")

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for q in queries:
        q_lower = q.lower()
        if q_lower not in seen:
            seen.add(q_lower)
            unique.append(q)

    return unique


def search_and_scrape(query: str, client: httpx.Client) -> dict | None:
    """Call the Market Scraper search-and-scrape endpoint."""
    try:
        resp = client.post(
            f"{API_BASE}/search-and-scrape",
            json={
                "query": query,
                "subreddits": [],
                "sort": DEFAULT_SORT,
                "time_filter": DEFAULT_TIME,
                "max_threads": DEFAULT_THREADS,
                "search_type": "link",
                "include_nsfw": False,
                "min_comments": 2,
                "max_comments_per_post": 0,
                "skip_comments": False,
            },
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            print(f"    Rate limited. Waiting 60s...")
            time.sleep(60)
            return search_and_scrape(query, client)  # Retry once
        print(f"    HTTP error {e.response.status_code}: {e.response.text[:200]}")
        return None
    except httpx.ConnectError:
        print(f"    ERROR: Can't connect to AutoForge at {AUTOFORGE_URL}")
        print(f"    Make sure AutoForge is running (start_ui.bat)")
        return None
    except Exception as e:
        print(f"    Error: {e}")
        return None


def score_idea(idea: dict, all_scrapes: list[dict]) -> dict:
    """Score an idea based on all scrape results."""
    total_phrases = 0
    category_totals = {
        "pain_point": 0,
        "desire": 0,
        "validation": 0,
        "feature_request": 0,
        "social_proof": 0,
    }
    top_phrases = []
    threads_found = 0
    total_comments = 0

    for scrape in all_scrapes:
        if not scrape:
            continue
        # Handle both single scrape and list of scrapes
        scrapes = scrape if isinstance(scrape, list) else [scrape]
        for s in scrapes:
            threads_found += 1
            phrases = s.get("phrases", [])
            total_phrases += len(phrases)
            cats = s.get("category_counts", {})
            for cat, count in cats.items():
                if cat in category_totals:
                    category_totals[cat] += count

            # Collect high-signal phrases
            for p in phrases:
                if p.get("validation_signal", 0) >= 3:
                    top_phrases.append({
                        "text": p["raw_text"][:200],
                        "category": p["category"],
                        "score": p.get("validation_signal", 0),
                        "subreddit": s.get("subreddit", ""),
                        "ad_hook": p.get("ad_hook", ""),
                    })

    # Sort top phrases by validation signal
    top_phrases.sort(key=lambda x: x["score"], reverse=True)
    top_phrases = top_phrases[:20]  # Keep top 20

    # Calculate demand score (0-100)
    pain_signal = min(category_totals["pain_point"] * 2, 30)
    desire_signal = min(category_totals["desire"] * 3, 25)
    validation_signal = min(category_totals["validation"] * 5, 25)
    volume_signal = min(threads_found * 2, 20)

    demand_score = pain_signal + desire_signal + validation_signal + volume_signal
    demand_score = min(demand_score, 100)

    # Recommendation
    if demand_score >= 70:
        recommendation = "STRONG — Clear demand signals. Build this."
    elif demand_score >= 40:
        recommendation = "MODERATE — Some signal. Worth deeper research."
    else:
        recommendation = "WEAK — Limited evidence of demand. Consider pivoting."

    return {
        "idea_name": idea["name"],
        "description": idea.get("description", ""),
        "demand_score": demand_score,
        "recommendation": recommendation,
        "threads_found": threads_found,
        "total_phrases": total_phrases,
        "category_totals": category_totals,
        "top_phrases": top_phrases,
        "queries_run": len(all_scrapes),
    }


def run_idea(idea: dict, client: httpx.Client) -> dict:
    """Run full validation for a single idea."""
    print(f"\n{'='*60}")
    print(f"  Validating: {idea['name']}")
    print(f"  {idea.get('description', '')}")
    print(f"{'='*60}")

    queries = generate_queries(idea)
    print(f"  Generated {len(queries)} search queries")

    all_scrapes = []
    for i, query in enumerate(queries, 1):
        print(f"  [{i}/{len(queries)}] Searching: \"{query}\"")
        result = search_and_scrape(query, client)
        if result:
            # Result can be a single scrape or list
            if isinstance(result, list):
                count = sum(s.get("total_phrases", 0) for s in result)
            else:
                count = result.get("total_phrases", 0)
            print(f"    Found {count} phrases")
            all_scrapes.append(result)
        else:
            print(f"    No results")

        # Rate limit pause (skip after last query)
        if i < len(queries):
            print(f"    Waiting {SCRAPE_DELAY}s (rate limit)...")
            time.sleep(SCRAPE_DELAY)

    score = score_idea(idea, all_scrapes)
    print(f"\n  Score: {score['demand_score']}/100 — {score['recommendation']}")
    print(f"  Pain points: {score['category_totals']['pain_point']} | "
          f"Desires: {score['category_totals']['desire']} | "
          f"Validation: {score['category_totals']['validation']}")

    return score


def generate_report(results: list[dict]) -> str:
    """Generate a markdown report from validation results."""
    # Sort by demand score
    ranked = sorted(results, key=lambda x: x["demand_score"], reverse=True)

    lines = [
        "# App Idea Validation Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Ideas tested: {len(ranked)}",
        "",
        "## Rankings",
        "",
        "| Rank | Idea | Score | Pain | Desire | Validation | Recommendation |",
        "|------|------|-------|------|--------|------------|----------------|",
    ]

    for i, r in enumerate(ranked, 1):
        cats = r["category_totals"]
        lines.append(
            f"| {i} | {r['idea_name']} | {r['demand_score']}/100 | "
            f"{cats['pain_point']} | {cats['desire']} | {cats['validation']} | "
            f"{r['recommendation'].split('—')[0].strip()} |"
        )

    lines.append("")

    # Detailed sections per idea
    for i, r in enumerate(ranked, 1):
        lines.append(f"---")
        lines.append(f"## #{i}: {r['idea_name']} — {r['demand_score']}/100")
        lines.append(f"")
        lines.append(f"**{r['recommendation']}**")
        lines.append(f"")
        lines.append(f"_{r['description']}_")
        lines.append(f"")
        lines.append(f"- Threads found: {r['threads_found']}")
        lines.append(f"- Total phrases: {r['total_phrases']}")
        lines.append(f"- Queries run: {r['queries_run']}")
        lines.append(f"")

        if r["top_phrases"]:
            lines.append(f"### Top Signals")
            lines.append(f"")
            for p in r["top_phrases"][:10]:
                emoji = {"pain_point": "🔴", "desire": "🟡", "validation": "🟢",
                         "feature_request": "🔵", "social_proof": "🟣"}.get(p["category"], "⚪")
                lines.append(f"- {emoji} **[{p['category']}]** r/{p['subreddit']}: \"{p['text'][:150]}\"")
                if p.get("ad_hook"):
                    lines.append(f"  - Ad hook: _{p['ad_hook']}_")
            lines.append(f"")

    return "\n".join(lines)


def load_ideas(file_path: Path) -> list[dict]:
    """Load ideas from JSON file."""
    if not file_path.exists():
        print(f"ERROR: Ideas file not found: {file_path}")
        print(f"Create it with this format:")
        print(json.dumps({"ideas": [
            {
                "name": "Sugar Scanner",
                "description": "Barcode scanner that detects hidden sugars using a 92-alias database",
                "keywords": ["sugar scanner", "hidden sugar", "keto app", "food scanner"],
                "competitors": ["Sugar AI", "Yuka", "MyFitnessPal"],
                "queries": ["why is it so hard to avoid sugar", "keto barcode scanner"]
            }
        ]}, indent=2))
        sys.exit(1)

    with open(file_path) as f:
        data = json.load(f)
    return data.get("ideas", [])


def main():
    parser = argparse.ArgumentParser(description="Validate app ideas using Reddit market research")
    parser.add_argument("--idea", type=str, help="Run a specific idea by name")
    parser.add_argument("--report", action="store_true", help="Show report from last run")
    parser.add_argument("--top", type=int, default=0, help="Show only top N ideas in report")
    parser.add_argument("--file", type=str, help="Path to ideas JSON file")
    args = parser.parse_args()

    ideas_file = Path(args.file) if args.file else IDEAS_FILE

    # Report mode — just display previous results
    if args.report:
        if REPORT_FILE.exists():
            print(REPORT_FILE.read_text())
        else:
            print("No results yet. Run the validator first.")
        return

    # Load ideas
    ideas = load_ideas(ideas_file)
    if not ideas:
        print("No ideas found in file.")
        return

    # Filter to specific idea if requested
    if args.idea:
        ideas = [i for i in ideas if args.idea.lower() in i["name"].lower()]
        if not ideas:
            print(f"No idea matching '{args.idea}' found.")
            return

    print(f"Idea Validator — {len(ideas)} ideas to validate")
    print(f"AutoForge: {AUTOFORGE_URL}")
    print(f"Rate limit delay: {SCRAPE_DELAY}s between searches")

    # Test connection
    client = httpx.Client(timeout=120)
    try:
        resp = client.get(f"{API_BASE}/search-options", timeout=10)
        resp.raise_for_status()
        print("AutoForge connection: OK")
    except Exception:
        print(f"\nERROR: Can't connect to AutoForge at {AUTOFORGE_URL}")
        print("Make sure AutoForge is running (start_ui.bat)")
        client.close()
        return

    # Run validation
    results = []
    for i, idea in enumerate(ideas, 1):
        print(f"\n[Idea {i}/{len(ideas)}]")
        score = run_idea(idea, client)
        results.append(score)

        # Save progress after each idea
        with open(RESULTS_FILE, "w") as f:
            json.dump(results, f, indent=2)

    client.close()

    # Generate and save report
    report = generate_report(results)
    REPORT_FILE.write_text(report)
    print(f"\n{'='*60}")
    print(f"  DONE — {len(results)} ideas validated")
    print(f"  Results: {RESULTS_FILE}")
    print(f"  Report:  {REPORT_FILE}")
    print(f"{'='*60}")
    print()
    print(report)


if __name__ == "__main__":
    main()
