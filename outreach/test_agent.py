"""
test_agent.py — Visual proof-of-concept. Watch the agent fill a contact form.

Opens a VISIBLE browser window so you can see exactly what's happening.
Uses test data by default — nothing real gets sent unless you pass --real.

Usage:
  # Test against a specific URL (safe test data, won't submit)
  python outreach/test_agent.py --url https://reliantplumbing.com/contact

  # Test against a URL and actually submit
  python outreach/test_agent.py --url https://reliantplumbing.com/contact --real --reply-to you@gmail.com

  # Auto-find a contact form from homepage
  python outreach/test_agent.py --url https://reliantplumbing.com --find-form

  # Run against first ready business in your CSV
  python outreach/test_agent.py --csv filtered_emails_enriched_seo_rankings_plumber_austin.csv
"""

import asyncio
import argparse
import os
import sys
import csv
from pathlib import Path

try:
    from browser_use import Agent, Browser, BrowserConfig
    from langchain_anthropic import ChatAnthropic
except ImportError:
    print("Install dependencies first:")
    print("  pip install browser-use langchain-anthropic playwright")
    print("  playwright install chromium")
    sys.exit(1)

# Test data — safe fake info, clearly a test
TEST_DATA = {
    "sender_name":    "Test User",
    "sender_email":   "test@example.com",
    "subject":        "[TEST] This is an automated test — please ignore",
    "message":        "[TEST MESSAGE — IGNORE] This is an automated test of a form submission system. No action required.",
}


def build_task(url: str, data: dict, submit: bool = False) -> str:
    submit_instruction = (
        "Submit the form by clicking the submit/send button."
        if submit else
        "DO NOT click the submit button. Fill in all fields but stop before submitting."
    )

    return f"""
Go to this URL: {url}

Find the contact form on this page (it may be on the page already or you may need to scroll).

Fill in the form fields with these details:
- Name field: {data['sender_name']}
- Email field: {data['sender_email']}
- Subject field (if present): {data['subject']}
- Message or comments field: {data['message']}

If there is a phone number field, skip it or leave it blank.
If there are any required dropdowns, select the first non-empty option.

{submit_instruction}

After filling (or attempting to fill), describe:
1. What fields were on the form
2. What you filled in
3. Whether you found a CAPTCHA
4. Whether submission was successful (or that you stopped before submitting)
""".strip()


async def run_test(url: str, data: dict, submit: bool = False, headless: bool = False):
    print(f"\n{'='*60}")
    print(f"  URL: {url}")
    print(f"  Submit: {submit}")
    print(f"  Headless: {headless}")
    print(f"{'='*60}\n")

    llm = ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    # Show browser window unless headless explicitly requested
    browser = Browser(
        config=BrowserConfig(headless=headless)
    )

    task = build_task(url, data, submit)
    print(f"TASK:\n{task}\n")
    print("="*60)
    print("Agent running... watch the browser window.")
    print("="*60)

    agent = Agent(task=task, llm=llm, browser=browser)

    try:
        result = await agent.run(max_steps=20)
        print(f"\n{'='*60}")
        print("AGENT RESULT:")
        print(result)
        print("="*60)
        return result
    except Exception as e:
        print(f"\nError: {e}")
        return None
    finally:
        await browser.close()


def get_first_ready_row(csv_path: str) -> dict:
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    ready = [r for r in rows if r.get("filter_status") == "ready"]
    if not ready:
        print(f"No rows with filter_status='ready' in {csv_path}")
        print(f"Run filter.py first: python outreach/filter.py --input <emails_csv>")
        sys.exit(1)

    row = ready[0]
    print(f"\nUsing first ready business:")
    print(f"  Business: {row.get('business_name', row.get('domain', '?'))}")
    print(f"  Tier: {row.get('tier', '?')}")
    print(f"  Contact URL: {row.get('contact_url', '')}")
    print(f"  Subject: {row.get('email_subject', '')[:70]}")
    return row


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test agent form filling — watch it work live")
    parser.add_argument("--url", help="Contact page URL to test against")
    parser.add_argument("--csv", help="Use first ready row from filtered CSV")
    parser.add_argument("--find-form", action="store_true",
                        help="Auto-find contact form from homepage URL")
    parser.add_argument("--real", action="store_true",
                        help="Use real email data and actually submit (requires --reply-to)")
    parser.add_argument("--reply-to", default="",
                        help="Your real reply-to email (required with --real)")
    parser.add_argument("--headless", action="store_true",
                        help="Run without visible browser window")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Set ANTHROPIC_API_KEY first:")
        print("  set ANTHROPIC_API_KEY=your_key_here  (Windows)")
        sys.exit(1)

    # Get URL and data
    if args.csv:
        row = get_first_ready_row(args.csv)
        url = row.get("contact_url") or row.get("website_url", "")
        if args.real and args.reply_to:
            data = {
                "sender_name":  os.environ.get("SENDER_NAME", "Your Name"),
                "sender_email": args.reply_to,
                "subject":      row.get("email_subject", ""),
                "message":      row.get("email_body", ""),
            }
        else:
            data = TEST_DATA
            if args.real:
                print("--real requires --reply-to. Using test data.")
    elif args.url:
        url = args.url
        data = TEST_DATA
        if args.real and args.reply_to:
            print("--real with --url: using test subject/message but your real email")
            data = {**TEST_DATA, "sender_email": args.reply_to}
    else:
        print("Provide --url or --csv")
        parser.print_help()
        sys.exit(1)

    if not url:
        print("No URL found. Check your CSV or provide --url")
        sys.exit(1)

    submit = args.real and bool(args.reply_to)
    if not submit:
        print("\n[SAFE MODE] Will fill form but NOT submit.")
        print("Pass --real --reply-to you@email.com to actually submit.\n")

    asyncio.run(run_test(url, data, submit=submit, headless=args.headless))
