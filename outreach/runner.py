"""
runner.py — AI contact form filler using browser-use + Claude Haiku.

Reads filtered CSV (filter_status = "ready"), submits the personalized email
through each business's contact form.

Requirements:
  pip install browser-use langchain-anthropic playwright
  playwright install chromium

Cost: ~$0.01-0.03 per form (Haiku DOM-first, reads HTML not screenshots)
Speed: ~30-60 seconds per form

Usage:
  python runner.py --input filtered_emails.csv --reply-to you@yourdomain.com
  python runner.py --input filtered_emails.csv --dry-run   # print tasks, don't submit
  python runner.py --input filtered_emails.csv --limit 10  # first 10 only
"""

import asyncio
import csv
import sys
import time
import argparse
import os
import random
from pathlib import Path
from typing import List
from datetime import datetime

try:
    from browser_use import Agent
    from langchain_anthropic import ChatAnthropic
except ImportError:
    print("Missing dependencies. Run:")
    print("  pip install browser-use langchain-anthropic playwright")
    print("  playwright install chromium")
    sys.exit(1)

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)


# ─── Task builder ──────────────────────────────────────────────────────────────

def build_task(row: dict, reply_to: str) -> str:
    """
    Build the natural language task for browser-use.
    Tells the agent exactly what to fill in and where.
    """
    business_name = row.get("business_name", "")
    contact_url   = row.get("contact_url", row.get("website_url", ""))
    subject       = row.get("email_subject", "")
    body          = row.get("email_body", "")
    sender_name   = os.environ.get("SENDER_NAME", "")
    sender_email  = reply_to or row.get("reply_to", "")

    return f"""
Go to this URL: {contact_url}

Fill out the contact form with these details:
- Name field: {sender_name}
- Email field: {sender_email}
- Subject or "How can we help" field: {subject}
- Message or "Tell us about your project" field: {body}

If there is a phone field, leave it blank or enter a placeholder.
If there is a company/business name field for the sender, use: {sender_name}
Do not check any checkboxes or select any dropdowns unless they are required.
Submit the form by clicking the submit/send button.

If the form has already been submitted or shows a thank you message, stop and report success.
If you cannot find a contact form on this page, report "no form found".
If there is a CAPTCHA you cannot solve, report "captcha blocked".
""".strip()


# ─── Single form submitter ─────────────────────────────────────────────────────

async def submit_form(row: dict, reply_to: str, dry_run: bool = False) -> dict:
    """
    Submit one contact form. Returns result dict with status + notes.
    """
    business = row.get("domain") or row.get("business_name", "?")
    contact_url = row.get("contact_url", "")

    if dry_run:
        print(f"  [DRY RUN] Would submit to: {contact_url}")
        print(f"  Subject: {row.get('email_subject', '')[:60]}")
        return {**row, "submit_status": "dry_run", "submit_note": "", "submitted_at": ""}

    task = build_task(row, reply_to)

    try:
        llm = ChatAnthropic(
            model="claude-haiku-4-5-20251001",
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
        )
        agent = Agent(task=task, llm=llm)
        result = await agent.run(max_steps=25)

        # Parse result text for success/failure signals
        result_text = str(result).lower()

        if any(w in result_text for w in ["success", "submitted", "thank you", "thank-you",
                                           "message sent", "form submitted", "received"]):
            status = "submitted"
            note = "form submitted successfully"
        elif "no form" in result_text or "could not find" in result_text:
            status = "no_form"
            note = "no contact form found on page"
        elif "captcha" in result_text:
            status = "captcha_blocked"
            note = "captcha encountered at submission time"
        else:
            status = "uncertain"
            note = result_text[:200]

    except Exception as e:
        status = "error"
        note = str(e)[:200]

    return {
        **row,
        "submit_status": status,
        "submit_note": note,
        "submitted_at": datetime.utcnow().isoformat(),
    }


# ─── Batch runner ──────────────────────────────────────────────────────────────

async def run_batch(rows: List[dict], reply_to: str, dry_run: bool = False,
                    delay_min: float = 15.0, delay_max: float = 45.0) -> List[dict]:
    """
    Submit forms for all ready rows. Runs sequentially with random delays.
    Random delays (15-45s default) prevent looking like automated traffic.
    """
    ready = [r for r in rows if r.get("filter_status") == "ready"]
    not_ready = [r for r in rows if r.get("filter_status") != "ready"]

    print(f"\n[runner] {len(ready)} forms ready to submit ({len(not_ready)} skipped)")

    if not ready:
        print("[runner] Nothing to submit.")
        return rows

    results = []

    for i, row in enumerate(ready, 1):
        domain = row.get("domain") or row.get("business_name", "?")
        tier = row.get("tier", "?")
        print(f"\n[{i}/{len(ready)}] {domain} (Tier {tier})")
        print(f"  URL: {row.get('contact_url', '')}")
        print(f"  Subject: {row.get('email_subject', '')[:70]}")

        result = await submit_form(row, reply_to, dry_run)
        results.append(result)

        status = result.get("submit_status", "?")
        if status == "submitted":
            print(f"  ✓ Submitted")
        elif status == "dry_run":
            print(f"  ~ Dry run")
        elif status == "captcha_blocked":
            print(f"  ✗ CAPTCHA blocked at submit time")
        elif status == "no_form":
            print(f"  ✗ No form found")
        elif status == "error":
            print(f"  ✗ Error: {result.get('submit_note', '')[:80]}")
        else:
            print(f"  ? {status}: {result.get('submit_note', '')[:80]}")

        # Random delay between submissions — look human
        if i < len(ready) and not dry_run:
            delay = random.uniform(delay_min, delay_max)
            print(f"  Waiting {delay:.0f}s before next...")
            await asyncio.sleep(delay)

    # Combine with non-ready rows
    all_results = results + [{**r, "submit_status": "skipped", "submit_note": r.get("filter_status", ""),
                              "submitted_at": ""} for r in not_ready]

    return all_results


# ─── Logging ───────────────────────────────────────────────────────────────────

def write_results(rows: List[dict], output_path: str):
    if not rows:
        return

    all_keys = []
    seen = set()
    for row in rows:
        for k in row.keys():
            if k not in seen:
                all_keys.append(k)
                seen.add(k)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nResults written to {output_path}")


def print_run_summary(rows: List[dict]):
    from collections import Counter
    statuses = Counter(r.get("submit_status", "?") for r in rows)

    print("\n--- Run Summary ---")
    print(f"  Submitted:        {statuses.get('submitted', 0)}")
    print(f"  Uncertain:        {statuses.get('uncertain', 0)}")
    print(f"  CAPTCHA blocked:  {statuses.get('captcha_blocked', 0)}")
    print(f"  No form:          {statuses.get('no_form', 0)}")
    print(f"  Errors:           {statuses.get('error', 0)}")
    print(f"  Skipped:          {statuses.get('skipped', 0)}")
    if statuses.get("dry_run"):
        print(f"  Dry run:          {statuses['dry_run']}")
    print(f"  Total:            {len(rows)}")


# ─── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Submit personalized emails via contact forms")
    parser.add_argument("--input", required=True, help="Filtered CSV (output of filter.py)")
    parser.add_argument("--output", help="Output CSV with results (auto-named if omitted)")
    parser.add_argument("--reply-to", required=True, help="Your reply-to email address")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be submitted without actually submitting")
    parser.add_argument("--limit", type=int, default=0,
                        help="Only submit first N forms (0 = all)")
    parser.add_argument("--delay-min", type=float, default=15.0,
                        help="Min seconds between submissions (default 15)")
    parser.add_argument("--delay-max", type=float, default=45.0,
                        help="Max seconds between submissions (default 45)")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Set ANTHROPIC_API_KEY env var")
        sys.exit(1)

    with open(args.input, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if args.limit > 0:
        ready = [r for r in rows if r.get("filter_status") == "ready"][:args.limit]
        not_ready = [r for r in rows if r.get("filter_status") != "ready"]
        rows = ready + not_ready
        print(f"Limiting to first {args.limit} ready rows")

    print(f"Loaded {len(rows)} rows from {args.input}")

    results = asyncio.run(run_batch(
        rows, args.reply_to, args.dry_run,
        args.delay_min, args.delay_max
    ))

    if args.output:
        output_path = args.output
    else:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M")
        base = Path(args.input).stem
        output_path = f"sent_{base}_{ts}.csv"

    write_results(results, output_path)
    print_run_summary(results)
