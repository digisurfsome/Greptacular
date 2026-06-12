"""
run_campaign.py — Single command to run the full outreach pipeline.

One command. One niche. One city. Done.

Usage:
  python outreach/run_campaign.py --niche plumber --city Austin --state Texas --reply-to you@gmail.com

  # Dry run (no actual form submissions)
  python outreach/run_campaign.py --niche plumber --city Austin --state Texas --reply-to you@gmail.com --dry-run

  # Local model instead of Haiku (zero API cost for form filling)
  python outreach/run_campaign.py --niche plumber --city Austin --state Texas --reply-to you@gmail.com --local-model

  # Test: preview emails + filter only, no sending
  python outreach/run_campaign.py --niche plumber --city Austin --state Texas --reply-to you@gmail.com --filter-only

  # Limit send to first N forms
  python outreach/run_campaign.py --niche plumber --city Austin --state Texas --reply-to you@gmail.com --limit 10

Cost breakdown (Haiku API mode):
  DataForSEO:      ~$0.01  (3 keyword searches)
  Email variants:  ~$0.00  (cached after first run per hook)
  Filter:          ~$0.00  (pure Python)
  Form submission: ~$0.015/form  (Haiku, DOM-first)
  Total 30 forms:  ~$0.50-0.60/city

Cost breakdown (local model mode):
  DataForSEO:      ~$0.01
  Everything else: ~$0.00
  Total:           ~$0.01/city
"""

import argparse
import asyncio
import csv
import os
import sys
from datetime import datetime
from pathlib import Path

# Make sure we can import from outreach/ regardless of where script is run
OUTREACH_DIR = Path(__file__).parent
sys.path.insert(0, str(OUTREACH_DIR))


def step(msg: str):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")


def check_env(local_model: bool):
    missing = []
    if not os.environ.get("DATAFORSEO_LOGIN"):
        missing.append("DATAFORSEO_LOGIN")
    if not os.environ.get("DATAFORSEO_PASSWORD"):
        missing.append("DATAFORSEO_PASSWORD")
    if not local_model and not os.environ.get("ANTHROPIC_API_KEY"):
        missing.append("ANTHROPIC_API_KEY")

    if missing:
        print(f"\nMissing env vars: {', '.join(missing)}")
        print("Set them with:  set VAR=value  (Windows)  or  export VAR=value  (Mac/Linux)")
        sys.exit(1)


async def main():
    parser = argparse.ArgumentParser(description="Full outreach pipeline — one command")
    parser.add_argument("--niche",      required=True, help="Target niche (e.g. 'plumber')")
    parser.add_argument("--city",       required=True, help="Target city (e.g. 'Austin')")
    parser.add_argument("--state",      default="",    help="State (e.g. 'Texas')")
    parser.add_argument("--reply-to",   required=True, help="Your reply-to email")
    parser.add_argument("--hook",       default="seo_rankings",
                        help="Data hook to use (default: seo_rankings)")
    parser.add_argument("--dry-run",    action="store_true",
                        help="Assemble emails and filter but don't submit forms")
    parser.add_argument("--filter-only", action="store_true",
                        help="Stop after filtering — don't assemble emails or submit")
    parser.add_argument("--limit",      type=int, default=0,
                        help="Only submit first N forms (0 = all)")
    parser.add_argument("--local-model", action="store_true",
                        help="Use local Ollama model instead of Haiku (zero API cost)")
    parser.add_argument("--preview",    type=int, default=3,
                        help="Number of sample emails to print (default 3, 0 to skip)")
    parser.add_argument("--delay-min",  type=float, default=15.0)
    parser.add_argument("--delay-max",  type=float, default=45.0)
    args = parser.parse_args()

    check_env(args.local_model)

    city_slug  = args.city.lower().replace(" ", "_")
    niche_slug = args.niche.lower().replace(" ", "_")
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M")
    run_label  = f"{args.hook}_{niche_slug}_{city_slug}"

    enriched_path  = OUTREACH_DIR / f"enriched_{run_label}.csv"
    emails_path    = OUTREACH_DIR / f"emails_{run_label}.csv"
    filtered_path  = OUTREACH_DIR / f"filtered_{run_label}.csv"
    results_path   = OUTREACH_DIR / f"sent_{run_label}_{ts}.csv"

    # ── Step 1: Discover + enrich businesses ──────────────────────────────────
    step(f"STEP 1/4 — Discover {args.niche}s in {args.city} {args.state}")
    print(f"  Hook: {args.hook} | Cost: ~$0.01 (DataForSEO, 3 keywords)")

    from build_list import build_from_serp, print_summary, write_csv
    rows = build_from_serp(args.niche, args.city, args.state)
    write_csv(rows, str(enriched_path))
    print_summary(rows)

    local_count = sum(1 for r in rows if not r.get("skip_outreach"))
    print(f"\n  {local_count} local businesses found")

    if local_count == 0:
        print("  Nothing to send to. Exiting.")
        sys.exit(0)

    if args.filter_only:
        print("\n  --filter-only: stopping after discovery.")
        sys.exit(0)

    # ── Step 2: Generate email variants (once per hook, cached) ───────────────
    step("STEP 2/4 — Email variant pool (one-time, cached)")

    from generate_variants import HOOK_SPECS, VARIANTS_DIR
    if args.hook not in HOOK_SPECS:
        print(f"  No variant spec for hook '{args.hook}'. Skipping variant generation.")
    else:
        tiers_needed = set(r.get("tier", "D") for r in rows if not r.get("skip_outreach"))
        missing_tiers = [
            t for t in tiers_needed
            if not (VARIANTS_DIR / f"{args.hook}_tier_{t.lower()}.json").exists()
        ]

        if missing_tiers:
            print(f"  Generating variants for tiers: {missing_tiers}")
            from generate_variants import generate_hook_variants
            generate_hook_variants(args.hook)
        else:
            print("  Variants already cached for all tiers — skipping (~$0.00)")

    # ── Step 3: Assemble emails ───────────────────────────────────────────────
    step("STEP 3/4 — Assemble personalized emails")
    print("  Cost: $0 (pure Python random assembly)")

    from assemble_emails import assemble_batch, write_output
    from assemble_emails import print_summary as email_summary

    with open(str(enriched_path), newline="", encoding="utf-8") as f:
        enriched_rows = list(csv.DictReader(f))

    email_rows = assemble_batch(enriched_rows, args.hook, args.reply_to)
    write_output(email_rows, str(emails_path))

    if args.preview > 0:
        from assemble_emails import print_preview
        print_preview(email_rows, args.preview)

    email_summary(email_rows)

    # ── Step 4: Filter contact forms ──────────────────────────────────────────
    step("STEP 4/4 — Pre-screen contact forms")
    print("  Cost: $0 (no AI, pure HTTP + BeautifulSoup)")

    from filter import filter_batch, print_filter_summary

    with open(str(emails_path), newline="", encoding="utf-8") as f:
        email_rows_fresh = list(csv.DictReader(f))

    filtered_rows = filter_batch(email_rows_fresh, delay=1.5)
    print_filter_summary(filtered_rows)

    # Write filtered
    if filtered_rows:
        all_keys = list(dict.fromkeys(k for r in filtered_rows for k in r.keys()))
        with open(str(filtered_path), "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=all_keys, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(filtered_rows)
        print(f"\n  Filtered list saved: {filtered_path}")

    ready = [r for r in filtered_rows if r.get("filter_status") == "ready"]
    print(f"\n  {len(ready)} forms ready to submit")

    if not ready:
        print("\n  No forms to submit. Done.")
        sys.exit(0)

    if args.dry_run:
        print("\n  --dry-run: stopping before submission.")
        print(f"  To submit: python outreach/runner.py --input {filtered_path} --reply-to {args.reply_to}")
        sys.exit(0)

    # ── Step 5: Submit forms ──────────────────────────────────────────────────
    step(f"SUBMITTING — {len(ready)} contact forms")

    if args.local_model:
        print("  Using local Ollama model (zero API cost)")
        _patch_local_model()
    else:
        cost_est = len(ready) * 0.02
        print(f"  Using Claude Haiku API | Est. cost: ~${cost_est:.2f}")

    from runner import print_run_summary, run_batch, write_results

    send_rows = filtered_rows
    if args.limit > 0:
        ready_limited = [r for r in filtered_rows if r.get("filter_status") == "ready"][:args.limit]
        not_ready = [r for r in filtered_rows if r.get("filter_status") != "ready"]
        send_rows = ready_limited + not_ready
        print(f"  Limiting to {args.limit} forms")

    results = await run_batch(send_rows, args.reply_to, False, args.delay_min, args.delay_max)
    write_results(results, str(results_path))
    print_run_summary(results)

    submitted = sum(1 for r in results if r.get("submit_status") == "submitted")
    print(f"\n{'='*60}")
    print(f"  DONE. {submitted} emails sent for {args.niche} in {args.city}.")
    print(f"  Results: {results_path}")
    print(f"{'='*60}")


def _patch_local_model():
    """Swap Haiku for local Ollama model in runner.py context."""
    try:
        import runner
        from langchain_ollama import ChatOllama
        runner._LOCAL_LLM = ChatOllama(model=os.environ.get("OLLAMA_MODEL", "qwen2.5:7b"))
        print(f"  Ollama model: {os.environ.get('OLLAMA_MODEL', 'qwen2.5:7b')}")
    except ImportError:
        print("  langchain-ollama not installed. Falling back to Haiku.")
        print("  pip install langchain-ollama  +  ollama pull qwen2.5:7b")


if __name__ == "__main__":
    asyncio.run(main())
