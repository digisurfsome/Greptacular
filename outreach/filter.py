"""
filter.py — Pre-screen websites for contact forms and blockers.

Runs BEFORE the AI runner. Pure Python, no AI, no cost.
Visits each website, finds the contact form URL, detects CAPTCHAs and Cloudflare.

Adds columns to the CSV:
  contact_url       → URL of the contact/contact-us page
  has_contact_form  → true/false
  blocker_type      → none | recaptcha_v2 | recaptcha_v3 | hcaptcha | turnstile | cloudflare | unknown
  filter_status     → ready | skip_captcha | skip_cloudflare | skip_no_form | error

V1: ready rows go to runner.py (no CAPTCHA)
V2: all rows go to orchestrated runner (CAPTCHA rows → 2captcha, Cloudflare → proxy)

Usage:
  python filter.py --input emails_enriched.csv
  python filter.py --input emails_enriched.csv --include-captcha   # V2 mode, keep all
"""

import argparse
import csv
import sys
import time
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Missing: pip install beautifulsoup4 requests")
    sys.exit(1)

# ─── Detection signatures ──────────────────────────────────────────────────────

CAPTCHA_SIGNATURES = [
    "google.com/recaptcha",
    "g-recaptcha",
    "hcaptcha.com",
    "h-captcha",
    "challenges.cloudflare.com",
    "cf-turnstile",
    "friendlycaptcha.com",
]

RECAPTCHA_V3_SIGNATURES = [
    "grecaptcha.execute",
    "'v3'",
    '"v3"',
]

CLOUDFLARE_SIGNATURES = [
    "cf-browser-verification",
    "Checking your browser",
    "DDoS protection by Cloudflare",
    "cf_clearance",
    "Ray ID",
    "__cf_bm",
]

DIRECTORY_DOMAINS = {
    "yelp.com", "yellowpages.com", "angi.com", "homeadvisor.com",
    "thumbtack.com", "nextdoor.com", "bbb.org", "bestprosintown.com",
    "plumbersden.com", "manta.com", "superpages.com", "hotfrog.com",
    "foursquare.com", "trustpilot.com", "google.com", "facebook.com",
    "linkedin.com", "instagram.com", "twitter.com", "x.com",
    "pinterest.com", "reddit.com", "indeed.com", "glassdoor.com",
    "ziprecruiter.com", "craigslist.org", "merchantcircle.com",
}

HONEYPOT_PATTERNS = [
    'name="url"',
    'name="website"',
    'name="homepage"',
    'style="display:none"',
    'style="visibility:hidden"',
    'tabindex="-1"',
]

CONTACT_URL_PATTERNS = [
    "/contact", "/contact-us", "/contactus", "/get-in-touch",
    "/reach-us", "/reach-out", "/talk-to-us", "/connect",
    "/request-quote", "/free-quote", "/get-a-quote",
    "/free-estimate", "/get-estimate", "/request-estimate",
    # Deliberately excluded: /book /schedule /appointment
    # Booking widgets are not contact forms. Prefer real contact pages.
]

# Embedded booking widgets — if a "form" is just one of these, it's not a contact form
BOOKING_WIDGET_SIGNATURES = [
    "calendly.com",
    "acuityscheduling.com",
    "squarespacescheduling.com",
    "squarespace-scheduling.com",
    "app.squarespacescheduling.com",
    "housecallpro.com/book",
    "book.housecallpro.com",
    "housecallpro.com/lead-form",
    "bookingbug.com",
    "cal.com/embed",
    "app.simplybook.me",
    "book.getjobber.com",
    "servicetitan.com/book",
    "scheduler.servicetitan.com",
    "getjobber.com/online-booking",
    "localimpact.com/embed",
    "book-online",
    'class="booking',
    'id="booking',
    "appointment-widget",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


# ─── Core detection functions ──────────────────────────────────────────────────

def detect_cloudflare(html: str, resp) -> bool:
    """Check if page is Cloudflare-blocked."""
    if resp.status_code in (403, 429, 503):
        server = resp.headers.get("Server", "")
        if "cloudflare" in server.lower():
            return True
    for sig in CLOUDFLARE_SIGNATURES:
        if sig in html:
            return True
    return False


def detect_captcha_type(html: str) -> Optional[str]:
    """Return captcha type string or None."""
    # Check v3 first (invisible — not visually obvious)
    for sig in RECAPTCHA_V3_SIGNATURES:
        if sig in html:
            return "recaptcha_v3"

    # Check v2 / other CAPTCHAs
    if "google.com/recaptcha" in html or "g-recaptcha" in html:
        return "recaptcha_v2"
    if "hcaptcha.com" in html or "h-captcha" in html:
        return "hcaptcha"
    if "challenges.cloudflare.com" in html or "cf-turnstile" in html:
        return "turnstile"
    if "friendlycaptcha.com" in html:
        return "friendly_captcha"

    return None


def has_real_contact_form(html: str) -> bool:
    """Check if page has a legitimate contact form (not just a phone number)."""
    soup = BeautifulSoup(html, "html.parser")
    forms = soup.find_all("form")

    for form in forms:
        inputs = form.find_all("input")
        textareas = form.find_all("textarea")

        # A real contact form has at least: name/email field + message area + 3+ fields
        has_name_or_email = any(
            inp.get("name", "").lower() in ("name", "email", "your-name", "your-email",
                                             "full_name", "fullname", "firstname",
                                             "first_name", "contact_name")
            or inp.get("type", "").lower() == "email"  # email type only, not generic text
            for inp in inputs
        )
        has_message = bool(textareas)  # require actual textarea, not input named "message"

        total_fields = len(inputs) + len(textareas)
        if has_name_or_email and has_message and total_fields >= 3:
            return True

    return False


def find_contact_url(base_url: str, html: str) -> Optional[str]:
    """Find contact page URL from homepage HTML."""
    soup = BeautifulSoup(html, "html.parser")

    # Check all links for contact-related paths
    for a in soup.find_all("a", href=True):
        href = a["href"].lower().strip()
        text = a.get_text().lower().strip()

        # Match by href pattern
        for pattern in CONTACT_URL_PATTERNS:
            if pattern in href:
                return urljoin(base_url, a["href"])

        # Match by link text (deliberately excludes "schedule"/"book" — those are booking widgets)
        if any(word in text for word in ["contact", "quote", "estimate"]):
            full_url = urljoin(base_url, a["href"])
            # Only follow same-domain links
            if urlparse(full_url).netloc == urlparse(base_url).netloc:
                return full_url

    return None


def fetch_page(url: str, timeout: int = 12) -> Tuple[Optional[str], Optional[requests.Response]]:
    """Fetch URL, return (html, response) or (None, None) on failure."""
    try:
        resp = SESSION.get(url, timeout=timeout, allow_redirects=True)
        return resp.text, resp
    except requests.exceptions.SSLError:
        try:
            resp = SESSION.get(url.replace("https://", "http://"), timeout=timeout)
            return resp.text, resp
        except Exception:
            return None, None
    except Exception:
        return None, None


# ─── Playwright fallback (renders JS-built contact forms) ────────────────────

_PW = None
_BROWSER = None

def _get_browser():
    """Lazy-init a headless Chromium. Returns None if Playwright unavailable."""
    global _PW, _BROWSER
    if _BROWSER is not None:
        return _BROWSER
    try:
        from playwright.sync_api import sync_playwright
        _PW = sync_playwright().start()
        _BROWSER = _PW.chromium.launch(headless=True)
        return _BROWSER
    except Exception as e:
        print(f"  [warn] Playwright unavailable ({e}) — static-only mode")
        return None


def close_browser():
    """Tear down the shared Playwright browser. Call once at end of batch."""
    global _PW, _BROWSER
    try:
        if _BROWSER:
            _BROWSER.close()
    except Exception:
        pass
    try:
        if _PW:
            _PW.stop()
    except Exception:
        pass
    _BROWSER = None
    _PW = None


def fetch_page_js(url: str, timeout: int = 15) -> Optional[str]:
    """Fetch URL with full JavaScript rendering. Returns rendered HTML or None."""
    browser = _get_browser()
    if browser is None:
        return None
    try:
        ctx = browser.new_context(user_agent=HEADERS["User-Agent"])
        page = ctx.new_page()
        page.goto(url, timeout=timeout * 1000, wait_until="domcontentloaded")
        # Wait briefly for JS-rendered forms to mount
        try:
            page.wait_for_selector("form, iframe[src]", timeout=3000)
        except Exception:
            pass
        html = page.content()
        ctx.close()
        return html
    except Exception:
        return None


def detect_booking_only(html: str) -> bool:
    """True when the page primarily embeds a booking widget (Calendly/Acuity/etc)."""
    lowered = html.lower()
    return any(sig.lower() in lowered for sig in BOOKING_WIDGET_SIGNATURES)


# ─── Main per-row filter ───────────────────────────────────────────────────────

def filter_row(row: dict) -> dict:
    """
    Visit the business website, find contact form, detect blockers.
    Returns row with filter columns added.
    """
    website_url = row.get("website_url", "").strip()
    if not website_url:
        return {**row, "contact_url": "", "has_contact_form": False,
                "blocker_type": "none", "filter_status": "skip_no_url"}

    if not website_url.startswith("http"):
        website_url = "https://" + website_url

    # Skip directory/aggregator sites (have forms, but aren't target businesses)
    domain = urlparse(website_url).netloc.lower().replace("www.", "")
    if any(domain == d or domain.endswith("." + d) for d in DIRECTORY_DOMAINS):
        return {**row, "contact_url": "", "has_contact_form": False,
                "blocker_type": "directory", "filter_status": "skip_directory"}

    # Fetch homepage
    html, resp = fetch_page(website_url)

    if html is None:
        return {**row, "contact_url": "", "has_contact_form": False,
                "blocker_type": "none", "filter_status": "error"}

    # Check Cloudflare block
    if detect_cloudflare(html, resp):
        return {**row, "contact_url": "", "has_contact_form": False,
                "blocker_type": "cloudflare", "filter_status": "skip_cloudflare"}

    # Find contact page URL
    contact_url = find_contact_url(website_url, html)

    # If contact form isn't on homepage, fetch the contact page
    contact_html = html
    if contact_url and contact_url != website_url:
        c_html, c_resp = fetch_page(contact_url)
        if c_html:
            contact_html = c_html
            # Re-check Cloudflare on contact page
            if detect_cloudflare(c_html, c_resp):
                return {**row, "contact_url": contact_url, "has_contact_form": False,
                        "blocker_type": "cloudflare", "filter_status": "skip_cloudflare"}

    # Detect CAPTCHA type
    captcha_type = detect_captcha_type(contact_html)

    # Check for real contact form (static HTML)
    has_form = has_real_contact_form(contact_html)
    booking_widget = detect_booking_only(contact_html)

    # Fallback: if static scan found no form and we have a contact URL,
    # re-fetch with Playwright to catch JS-rendered forms.
    if not has_form and contact_url:
        js_html = fetch_page_js(contact_url)
        if js_html:
            contact_html = js_html
            captcha_type = captcha_type or detect_captcha_type(js_html)
            has_form = has_real_contact_form(js_html)
            booking_widget = booking_widget or detect_booking_only(js_html)

    # If this site only exposes a booking widget (Calendly/Acuity/etc), skip it
    if not has_form and booking_widget:
        return {**row, "contact_url": contact_url or "", "has_contact_form": False,
                "blocker_type": "booking_widget", "filter_status": "skip_booking"}

    if not has_form:
        return {**row, "contact_url": contact_url or "", "has_contact_form": False,
                "blocker_type": captcha_type or "none", "filter_status": "skip_no_form"}

    # Has a real form — but if it's sitting next to a booking widget,
    # prefer the real form path (continue to ready).

    if captcha_type:
        return {**row,
                "contact_url": contact_url or website_url,
                "has_contact_form": has_form,
                "blocker_type": captcha_type,
                "filter_status": "skip_captcha"}

    return {**row,
            "contact_url": contact_url or website_url,
            "has_contact_form": has_form,
            "blocker_type": "none",
            "filter_status": "ready"}


# ─── Batch runner ──────────────────────────────────────────────────────────────

def filter_batch(rows: list, include_captcha: bool = False,
                 delay: float = 1.0) -> list:
    """
    Run filter on all rows that aren't flagged skip_outreach.
    Returns rows with filter columns added.
    """
    results = []
    eligible = [r for r in rows if not r.get("skip_outreach")]
    skipped  = [r for r in rows if r.get("skip_outreach")]

    print(f"[filter] Checking {len(eligible)} sites ({len(skipped)} pre-flagged, skipping)...")

    for i, row in enumerate(eligible, 1):
        domain = row.get("domain") or row.get("business_name", "?")
        print(f"  [{i}/{len(eligible)}] {domain}", end=" ", flush=True)

        filtered = filter_row(row)
        status = filtered.get("filter_status", "?")
        blocker = filtered.get("blocker_type", "?")

        if status == "ready":
            print("✓ contact form found")
        elif blocker == "cloudflare":
            print("✗ Cloudflare blocked")
        elif status == "skip_captcha":
            print(f"~ CAPTCHA: {blocker}")
        elif status == "skip_no_form":
            print("✗ no contact form")
        elif status == "skip_directory":
            print("✗ directory/aggregator site")
        elif status == "skip_booking":
            print("✗ booking widget only (Calendly/Acuity/etc)")
        else:
            print(f"? {status}")

        results.append(filtered)

        if i < len(eligible):
            time.sleep(delay)

    # Add back the pre-flagged rows with empty filter columns
    for row in skipped:
        results.append({
            **row,
            "contact_url": "",
            "has_contact_form": False,
            "blocker_type": "none",
            "filter_status": "skip_not_local",
        })

    # Tear down the shared Playwright browser, if it was started
    close_browser()

    return results


def print_filter_summary(rows: list):
    from collections import Counter
    statuses = Counter(r.get("filter_status", "?") for r in rows)

    print("\n--- Filter Summary ---")
    print(f"  Ready to send:    {statuses.get('ready', 0)}")
    print(f"  No contact form:  {statuses.get('skip_no_form', 0)}")
    print(f"  Booking widget:   {statuses.get('skip_booking', 0)}")
    print(f"  Directory site:   {statuses.get('skip_directory', 0)}")
    print(f"  CAPTCHA (skip):   {statuses.get('skip_captcha', 0)}")
    print(f"  Cloudflare:       {statuses.get('skip_cloudflare', 0)}")
    print(f"  Not local:        {statuses.get('skip_not_local', 0)}")
    print(f"  Errors:           {statuses.get('error', 0)}")
    print(f"  Total:            {len(rows)}")


# ─── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pre-screen websites for contact forms")
    parser.add_argument("--input", required=True, help="Email-assembled CSV")
    parser.add_argument("--output", help="Output CSV path (auto-named if omitted)")
    parser.add_argument("--include-captcha", action="store_true",
                        help="Keep CAPTCHA rows in output (V2 mode with 2captcha)")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="Seconds between site requests (default 1.0)")
    args = parser.parse_args()

    with open(args.input, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"Loaded {len(rows)} rows from {args.input}")

    results = filter_batch(rows, args.include_captcha, args.delay)

    # Output path
    if args.output:
        output_path = args.output
    else:
        base = Path(args.input).stem
        output_path = f"filtered_{base}.csv"

    # Write CSV
    if not results:
        print("No results to write.")
        sys.exit(0)

    all_keys = []
    seen_keys = set()
    for row in results:
        for k in row.keys():
            if k not in seen_keys:
                all_keys.append(k)
                seen_keys.add(k)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    print(f"\nWrote {len(results)} rows to {output_path}")
    print_filter_summary(results)

    ready = [r for r in results if r.get("filter_status") == "ready"]
    print(f"\nNext step: python runner.py --input {output_path}")
    print(f"  {len(ready)} forms ready to submit")
