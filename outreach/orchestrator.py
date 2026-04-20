"""
orchestrator.py — Run a hook against a business list and write enriched CSV.

This is the data enrichment layer. It does NOT send emails or fill forms.
Output CSV feeds directly into assemble_emails.py.

Usage:
  # Enrich from SERP auto-discovery:
  python orchestrator.py --hook seo_rankings --niche plumber --city Austin --state Texas

  # Enrich existing business list:
  python orchestrator.py --hook seo_rankings --input businesses.csv

  # Multi-hook (runs both and merges columns):
  python orchestrator.py --hook seo_rankings --hook pagespeed --input businesses.csv

Output: enriched_{hook}_{niche}_{city}.csv  (or --output to override)
"""

import csv
import os
import sys
import time
import argparse
from typing import List, Dict

from hooks.registry import get_hook, list_hooks
from build_list import build_from_serp, build_from_csv, write_csv, print_summary, OUTPUT_COLUMNS


def enrich_with_hook(hook_name: str, rows: List[Dict], delay: float = 0.5) -> List[Dict]:
    """
    Run hook.fetch_data() + hook.assign_tier() for each row.
    Adds hook output columns + tier to each row.
    """
    hook = get_hook(hook_name)

    missing_env = hook.check_env()
    if missing_env:
        print(f"[orchestrator] ERROR: Missing env vars for hook '{hook_name}': {missing_env}")
        sys.exit(1)

    print(f"\n[orchestrator] Running hook '{hook_name}' on {len(rows)} businesses...")

    enriched = []
    for i, row in enumerate(rows, 1):
        print(f"  [{i}/{len(rows)}] {row.get('business_name', row.get('domain', '?'))}")

        missing_cols = hook.check_input(row)
        if missing_cols:
            print(f"    Skipping — missing input columns: {missing_cols}")
            row["tier"] = "SKIP"
            enriched.append(row)
            continue

        try:
            data = hook.fetch_data(row)
        except Exception as e:
            print(f"    fetch_data error: {e}")
            data = {}

        if data:
            tier = hook.assign_tier(data)
            row.update(data)
            row["tier"] = tier
            print(f"    Tier {tier} — {_tier_summary(hook_name, row)}")
        else:
            row["tier"] = "SKIP"
            print(f"    No data returned — skipped")

        enriched.append(row)

        if i < len(rows) and delay > 0:
            time.sleep(delay)

    return enriched


def _tier_summary(hook_name: str, row: dict) -> str:
    """Short summary line for console output."""
    if hook_name == "seo_rankings":
        rank = min(
            r for r in [row.get("kw1_rank"), row.get("kw2_rank"), row.get("kw3_rank")]
            if r is not None
        ) if any(row.get(f"kw{i}_rank") for i in range(1, 4)) else None
        if rank:
            return f"best rank #{rank}"
        return "not ranked"
    if hook_name == "pagespeed":
        return f"score {row.get('perf_score', '?')}/100"
    return ""


def build_output_columns(hook_names: List[str]) -> List[str]:
    """Combine base columns + all hook output columns."""
    base = ["business_name", "website_url", "domain", "niche", "city", "state"]
    hook_cols = []
    for name in hook_names:
        hook = get_hook(name)
        for col in hook.output_columns:
            if col not in base and col not in hook_cols:
                hook_cols.append(col)
    return base + hook_cols + ["tier"]


def write_enriched_csv(rows: List[Dict], columns: List[str], output_path: str):
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n[orchestrator] Wrote {len(rows)} rows to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enrich business list with hook data")
    parser.add_argument("--hook", action="append", required=True,
                        help=f"Hook name(s). Available: {list_hooks()}")
    parser.add_argument("--input", help="Input CSV of businesses (optional)")
    parser.add_argument("--output", help="Output CSV path (auto-named if omitted)")
    parser.add_argument("--niche", help="Niche for SERP auto-discovery")
    parser.add_argument("--city", help="City for SERP auto-discovery")
    parser.add_argument("--state", help="State for SERP auto-discovery", default="")
    parser.add_argument("--delay", type=float, default=0.5,
                        help="Seconds between API calls (default 0.5)")

    args = parser.parse_args()

    # Validate hooks
    available = list_hooks()
    for h in args.hook:
        if h not in available:
            print(f"Unknown hook '{h}'. Available: {available}")
            sys.exit(1)

    # Build base business list
    if args.input:
        print(f"[orchestrator] Loading businesses from {args.input}...")
        rows = build_from_csv(args.input, args.niche, args.city, args.state)
    elif args.niche and args.city:
        # For seo_rankings, build_from_serp already enriches — use it directly
        if args.hook == ["seo_rankings"]:
            rows = build_from_serp(args.niche, args.city, args.state)
        else:
            # Build base list from SERP first, then run hooks
            rows = build_from_serp(args.niche, args.city, args.state)
    else:
        print("Error: provide --input CSV or --niche + --city")
        sys.exit(1)

    # Run additional hooks (seo_rankings is already run by build_from_serp)
    for hook_name in args.hook:
        if hook_name == "seo_rankings" and not args.input:
            continue  # Already done in build_from_serp
        rows = enrich_with_hook(hook_name, rows, delay=args.delay)

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        hook_str = "_".join(args.hook)
        city_str = (args.city or "list").lower().replace(" ", "_")
        niche_str = (args.niche or "businesses").lower().replace(" ", "_")
        output_path = f"enriched_{hook_str}_{niche_str}_{city_str}.csv"

    # Write output
    columns = build_output_columns(args.hook)
    write_enriched_csv(rows, columns, output_path)
    print_summary(rows)

    print(f"\nNext step: python assemble_emails.py --input {output_path}")
