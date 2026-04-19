# PRD: Automated Contact Form Outreach — V2 Full (CAPTCHA + Cloudflare)

## What This Is

Same pipeline as V1 but nothing gets filtered out. Every site on the list gets attempted.
The filter script still runs first — but instead of discarding blocked sites, it routes them
to the appropriate handler. Clean sites go through the fast cheap runner. CAPTCHA sites get
2captcha. Cloudflare sites get residential proxies. Every site gets a real attempt.

**Build V1 first. Build this second. Don't build this until V1 is working.**

---

## How It Differs From V1

| | V1 | V2 |
|--|----|----|
| CAPTCHA sites | Skipped | 2captcha solves them |
| Cloudflare sites | Skipped | Residential proxy routes around them |
| reCAPTCHA v3 | Skipped | 2captcha v3 solve + token injection |
| hCaptcha | Skipped | 2captcha hCaptcha solve |
| Cloudflare Turnstile | Skipped | 2captcha Turnstile solve |
| Cost/form (clean) | $0.01-0.03 | $0.01-0.03 |
| Cost/form (CAPTCHA) | N/A | $0.01-0.03 + ~$0.002 CAPTCHA solve |
| Cost/form (Cloudflare) | N/A | $0.01-0.03 + ~$0.02 proxy bandwidth |

---

## The Stack

| Component | Tool | Purpose |
|-----------|------|---------|
| List filter | Python + BeautifulSoup (same as V1) | Routes sites by blocker type |
| Browser automation | browser-use (open source) | Fills and submits forms |
| AI brain | Claude Haiku 4.5 via Anthropic API | Decides what to click |
| CAPTCHA solving | 2captcha.com Python SDK | Solves v2, v3, hCaptcha, Turnstile |
| Proxy rotation | Smartproxy residential | Routes around Cloudflare network blocks |
| Orchestrator | Python async | Routes each site to correct handler |

---

## Install

```bash
pip install browser-use langchain-anthropic 2captcha-python requests beautifulsoup4
playwright install chromium
```

Set env vars:
```
ANTHROPIC_API_KEY=your_key
TWOCAPTCHA_API_KEY=your_key
SMARTPROXY_USER=your_username
SMARTPROXY_PASS=your_password
```

---

## Architecture: Route By Blocker Type

The filter script (same as V1) outputs one CSV with a `blocker_type` column instead of two separate files.

```
raw_list.csv
      |
      v
filter.py (same script as V1, extended output)
      |
      +---> blocker_type = none          --> fast_runner (V1 logic, no extras)
      |
      +---> blocker_type = recaptcha_v2  --> captcha_runner (2captcha v2)
      +---> blocker_type = recaptcha_v3  --> captcha_runner (2captcha v3)
      +---> blocker_type = hcaptcha      --> captcha_runner (2captcha hcaptcha)
      +---> blocker_type = turnstile     --> captcha_runner (2captcha turnstile)
      |
      +---> blocker_type = cloudflare    --> proxy_runner (Smartproxy residential)
      |
      +---> blocker_type = no_form       --> skip entirely (nothing to fill)
```

One orchestrator reads the routed CSV and dispatches each row to the right runner.

---

## Component 1: Extended Filter Script

Same as V1 filter.py but outputs `blocker_type` column instead of splitting into clean/skipped.

```python
# Addition to V1 filter — change the output logic:

def classify_site(url, row):
    base_url = normalize_url(url)
    contact_url = find_contact_url(base_url)

    if not contact_url:
        return {**row, 'contact_url': '', 'blocker_type': 'no_form'}

    analysis = analyze_contact_page(contact_url)

    if not analysis.get('has_form'):
        return {**row, 'contact_url': contact_url, 'blocker_type': 'no_form'}

    if analysis.get('cloudflare_blocked'):
        return {**row, 'contact_url': contact_url, 'blocker_type': 'cloudflare'}

    captcha = analysis.get('captcha_type', 'none')
    return {**row, 'contact_url': contact_url, 'blocker_type': captcha}
```

Output CSV columns:
```
website_url, contact_url, blocker_type, sender_name, sender_email, subject, message
```

Where `blocker_type` is one of: `none`, `recaptcha_v2`, `recaptcha_v3`, `hcaptcha`, `turnstile`, `cloudflare`, `no_form`

---

## Component 2: 2captcha Integration

Install: `pip install 2captcha-python`

How it works with browser-use: browser-use opens the page in a real Chromium browser.
When it detects a CAPTCHA, the orchestrator pauses, calls 2captcha with the sitekey extracted
from the page source, gets a token back, and injects it into the page before browser-use continues.

```python
from twocaptcha import TwoCaptcha, TimeoutException, ApiException
import os

solver = TwoCaptcha(os.environ['TWOCAPTCHA_API_KEY'])


def solve_recaptcha_v2(sitekey, page_url):
    try:
        result = solver.recaptcha(sitekey=sitekey, url=page_url)
        return result['code']
    except (TimeoutException, ApiException):
        return None


def solve_recaptcha_v3(sitekey, page_url, action='submit'):
    try:
        result = solver.recaptcha(
            sitekey=sitekey,
            url=page_url,
            version='v3',
            action=action,
            score=0.7
        )
        return result['code']
    except (TimeoutException, ApiException):
        return None


def solve_hcaptcha(sitekey, page_url):
    try:
        result = solver.hcaptcha(sitekey=sitekey, url=page_url)
        return result['code']
    except (TimeoutException, ApiException):
        return None


def solve_turnstile(sitekey, page_url):
    try:
        result = solver.turnstile(sitekey=sitekey, url=page_url)
        return result['code']
    except (TimeoutException, ApiException):
        return None


def extract_sitekey(html, captcha_type):
    """Pull sitekey from page HTML for each captcha type."""
    import re
    patterns = {
        'recaptcha_v2': [
            r'data-sitekey=["\']([^"\']+)["\']',
            r'grecaptcha\.render\([^,]+,\s*\{[^}]*["\']sitekey["\']\s*:\s*["\']([^"\']+)["\']',
        ],
        'recaptcha_v3': [
            r'grecaptcha\.execute\(["\']([^"\']+)["\']',
            r'data-sitekey=["\']([^"\']+)["\']',
        ],
        'hcaptcha': [
            r'data-sitekey=["\']([^"\']+)["\']',
        ],
        'turnstile': [
            r'data-sitekey=["\']([^"\']+)["\']',
        ],
    }
    for pattern in patterns.get(captcha_type, []):
        match = re.search(pattern, html)
        if match:
            return match.group(1)
    return None


def solve_captcha(html, captcha_type, page_url):
    sitekey = extract_sitekey(html, captcha_type)
    if not sitekey:
        return None

    if captcha_type == 'recaptcha_v2':
        return solve_recaptcha_v2(sitekey, page_url)
    elif captcha_type == 'recaptcha_v3':
        return solve_recaptcha_v3(sitekey, page_url)
    elif captcha_type == 'hcaptcha':
        return solve_hcaptcha(sitekey, page_url)
    elif captcha_type == 'turnstile':
        return solve_turnstile(sitekey, page_url)
    return None
```

**Cost reality:**
- reCAPTCHA v2: $1.00–$2.99 per 1,000 solves (~$0.001-0.003 each)
- reCAPTCHA v3: $1.45–$2.99 per 1,000 solves
- hCaptcha: ~$2.00 per 1,000
- Turnstile: ~$2.00 per 1,000
- At 100 CAPTCHA sites/day: max ~$0.30/day

---

## Component 3: Proxy Runner (Cloudflare Sites)

Smartproxy residential proxies route your requests through real home IPs.
Cloudflare sees a real residential IP, not a datacenter — stops blocking.

**Proxy URL format (Smartproxy):**
```
http://username:password@gate.smartproxy.com:10001
```

browser-use runs on Playwright under the hood. Pass the proxy at browser launch:

```python
from browser_use import Agent, Browser, BrowserConfig
from langchain_anthropic import ChatAnthropic
import os

llm = ChatAnthropic(model='claude-haiku-4-5-20251001')


async def fill_form_with_proxy(contact_url, sender_name, sender_email, subject, message):
    proxy_url = (
        f"http://{os.environ['SMARTPROXY_USER']}:"
        f"{os.environ['SMARTPROXY_PASS']}@gate.smartproxy.com:10001"
    )

    browser_config = BrowserConfig(
        proxy=proxy_url,
        headless=True,
    )

    task = f"""
    Go to this URL: {contact_url}

    Fill the contact form with exactly these values:
    - Name / Full Name field: {sender_name}
    - Email field: {sender_email}
    - Subject field (only if it exists): {subject}
    - Message / Comment / Body field: {message}

    Do NOT fill phone, company, or website fields.
    After all fields are filled, click the Submit or Send button once.
    If there is no form visible, stop and report failure.
    """

    try:
        browser = Browser(config=browser_config)
        agent = Agent(task=task, llm=llm, browser=browser)
        result = await agent.run(max_steps=20)
        await browser.close()
        return 'success', str(result)
    except Exception as e:
        return 'failed', str(e)
```

**Smartproxy cost:** ~$7-10/GB residential. Each form session uses ~1-3MB. At 100 Cloudflare sites/day: ~0.3GB = ~$2-3/day extra.

---

## Component 4: CAPTCHA Runner

For sites with CAPTCHA, browser-use opens the page, the orchestrator grabs the page HTML,
extracts the sitekey, calls 2captcha, gets the token, then injects it via JavaScript before
browser-use continues to fill and submit.

```python
import asyncio
import requests
from browser_use import Agent, Browser, BrowserConfig
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(model='claude-haiku-4-5-20251001')


async def fill_form_with_captcha(contact_url, sender_name, sender_email,
                                  subject, message, captcha_type):
    # Fetch page HTML to extract sitekey (before launching agent)
    try:
        r = requests.get(contact_url, timeout=8, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        html = r.text
    except Exception as e:
        return 'failed', f'Could not fetch page: {e}'

    # Solve CAPTCHA via 2captcha
    token = solve_captcha(html, captcha_type, contact_url)
    if not token:
        return 'failed', f'Could not solve {captcha_type}'

    # Tell browser-use to inject the token and then fill the form
    task = f"""
    Go to this URL: {contact_url}

    Before filling the form, inject this CAPTCHA token into the page using JavaScript.
    Run this JavaScript: document.getElementById('g-recaptcha-response').value = '{token}'
    Also run: window.grecaptcha && grecaptcha.getResponse && (grecaptcha.getResponse = () => '{token}')

    Then fill the contact form with exactly these values:
    - Name / Full Name field: {sender_name}
    - Email field: {sender_email}
    - Subject field (only if it exists): {subject}
    - Message / Comment / Body field: {message}

    Do NOT fill phone, company, or website fields.
    After all fields are filled, click the Submit or Send button once.
    """

    try:
        browser = Browser(config=BrowserConfig(headless=True))
        agent = Agent(task=task, llm=llm, browser=browser)
        result = await agent.run(max_steps=25)
        await browser.close()
        return 'success', str(result)
    except Exception as e:
        return 'failed', str(e)
```

**Note on reCAPTCHA v3:** Token injection is the same but v3 runs silently. The form will submit — whether the site's backend accepts the score is outside your control. If a site uses v3 aggressively, submissions may still get spam-scored. Flag v3 sites for manual review if success rate is low.

---

## Component 5: V2 Orchestrator

Routes each site to the right runner based on `blocker_type`.

```python
import asyncio
import csv
import logging
import os
from datetime import datetime

logging.basicConfig(
    filename=f'outreach_v2_log_{datetime.now().strftime("%Y%m%d_%H%M")}.txt',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

CAPTCHA_TYPES = {'recaptcha_v2', 'recaptcha_v3', 'hcaptcha', 'turnstile'}


async def process_row(row, delay_seconds):
    url = row['contact_url']
    blocker = row['blocker_type']

    if blocker == 'no_form' or not url:
        logging.info(f"SKIPPED (no form): {row['website_url']}")
        return 'skipped'

    kwargs = dict(
        contact_url=url,
        sender_name=row['sender_name'],
        sender_email=row['sender_email'],
        subject=row['subject'],
        message=row['message']
    )

    if blocker == 'none':
        # V1 fast path — no extras
        from runner import fill_form
        status, detail = await fill_form(**kwargs)

    elif blocker in CAPTCHA_TYPES:
        status, detail = await fill_form_with_captcha(**kwargs, captcha_type=blocker)

    elif blocker == 'cloudflare':
        status, detail = await fill_form_with_proxy(**kwargs)

    else:
        status, detail = 'skipped', f'Unknown blocker: {blocker}'

    if status == 'success':
        logging.info(f"SUCCESS [{blocker}]: {url}")
    else:
        logging.warning(f"FAILED [{blocker}]: {url} | {detail}")

    await asyncio.sleep(delay_seconds)
    return status


async def run_v2(routed_csv, delay_seconds=45):
    with open(routed_csv, 'r') as f:
        rows = list(csv.DictReader(f))

    counts = {'success': 0, 'failed': 0, 'skipped': 0}

    for i, row in enumerate(rows):
        print(f"[{i+1}/{len(rows)}] {row.get('website_url')} [{row.get('blocker_type')}]")
        result = await process_row(row, delay_seconds)
        counts[result] = counts.get(result, 0) + 1

    print(f"\nDone — Success: {counts['success']} | Failed: {counts['failed']} | Skipped: {counts['skipped']}")


if __name__ == '__main__':
    asyncio.run(run_v2('routed_list.csv', delay_seconds=45))
```

---

## Cost Per Email (V2)

| Site Type | Haiku tokens | 2captcha | Proxy | Total |
|-----------|-------------|----------|-------|-------|
| Clean (no blocker) | ~$0.01-0.03 | $0 | $0 | ~$0.01-0.03 |
| CAPTCHA site | ~$0.01-0.03 | ~$0.002 | $0 | ~$0.012-0.032 |
| Cloudflare site | ~$0.01-0.03 | $0 | ~$0.01-0.02 | ~$0.02-0.05 |
| CAPTCHA + Cloudflare | ~$0.01-0.03 | ~$0.002 | ~$0.01-0.02 | ~$0.022-0.052 |

**100/day blended (all types): $1.50-5/day**
**500/day blended: $7.50-25/day**

---

## Build Order

1. **Build and verify V1 first.** No point building V2 until the clean-site path works.
2. Add 2captcha — get API key, test solve on one known CAPTCHA site before wiring in
3. Add proxy runner — test Smartproxy connection before wiring in
4. Wire together in V2 orchestrator
5. Test 20 mixed sites (clean + CAPTCHA + Cloudflare), verify all three paths work
6. Scale

---

## What Still Won't Work (Accept It)

- **reCAPTCHA v3 silent rejections** — submission goes through but backend spam-scores it. Invisible, undetectable. Flag v3 sites, check if you're actually getting responses.
- **Slider/image puzzle CAPTCHAs** (not reCAPTCHA) — 2captcha handles these differently; may need manual review
- **Login-walled contact forms** — require an account to message. Not worth solving.
- **Sites that track mouse movement / keystroke timing** — some enterprise sites flag robotic behavior regardless of IP. Rare on small business sites.

---

## Files

```
contact-outreach/
  filter.py              # Shared by V1 and V2 — outputs blocker_type column
  runner.py              # V1: clean sites only
  captcha_solver.py      # 2captcha integration (all types)
  captcha_runner.py      # browser-use + 2captcha injection
  proxy_runner.py        # browser-use + Smartproxy
  orchestrator_v2.py     # Routes by blocker_type, calls right runner
  raw_list.csv           # Your input
  routed_list.csv        # Filter output with blocker_type column
  outreach_v2_log_YYYYMMDD.txt
```

---

## Email Writing System (Same As V1 — Shared Component)

See `README.md` (V1 PRD) for the full email system spec. Everything is identical between V1 and V2.

The only difference in V2: the `ready_to_send.csv` output of `assemble_emails.py` feeds into `orchestrator_v2.py` instead of `runner.py`. The email assembly pipeline is the same script.

### Why V2 Is Worth It For The SEO Use Case

One Ahrefs search for "plumber in [city]" gives you:
- Top 3 competitors (same for every plumber in that city)
- Their rankings (same for every plumber)
- Traffic values (same for every plumber)

That data goes into every email in the batch. You do the research once.

- **V1:** Loses 30-50% of the plumber list to CAPTCHAs and Cloudflare
- **V2:** Hits every plumber on the list

For the SEO outreach use case specifically, V2 pays for itself. You already did the research — don't leave half the list on the table because of a CAPTCHA.

### Cost Comparison For One City (50 Plumbers)

| | V1 (filter out blocked) | V2 (bust through everything) |
|--|------------------------|------------------------------|
| Sites attempted | ~30 (60% pass filter) | 50 (all of them) |
| CAPTCHA cost | $0 | ~$0.10 (50 × $0.002) |
| Proxy cost | $0 | ~$0.50 (20 CF sites × $0.02) |
| Haiku cost | ~$0.45 | ~$0.75 |
| Emails written | $0 (spinner) | $0 (spinner) |
| **Total** | **~$0.45** | **~$1.35** |
| Businesses reached | ~28 | ~45 |
| Cost per business reached | ~$0.016 | ~$0.030 |

V2 costs 3x more but reaches 60% more businesses from the same research investment. For outreach that's worth it.
