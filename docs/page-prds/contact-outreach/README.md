# PRD: Automated Contact Form Outreach

## What This Is

A pipeline that takes a list of business websites and a pre-written email, then automatically finds each site's contact form and submits the email — mimicking exactly what a human would do manually.

This is NOT a bulk email blaster. It sends one human-like form submission per website.

---

## The Stack (Confirmed From Docs)

| Component | Tool | Purpose |
|-----------|------|---------|
| Contact form finder | Python scraper (no AI) | Finds the actual contact form URL on each site |
| Browser automation | Skyvern (self-hosted via Docker) | Navigates and fills the form |
| AI brain | Claude Haiku (vision) via Anthropic API | Tells Skyvern what to click |
| CAPTCHA solving | 2captcha.com | Solves reCAPTCHA v2/v3, hCaptcha, Turnstile |
| Proxy rotation | Smartproxy residential | Rotates IPs so sites don't block |
| Orchestrator | Python script | Loops through CSV, calls everything |

---

## Honest Success Rate

| Scenario | Expected Rate |
|----------|--------------|
| Clean contact form, no CAPTCHA | ~90% |
| Contact form with reCAPTCHA (2captcha enabled) | ~80-85% |
| Site behind Cloudflare (proxies enabled) | ~70-80% |
| Site has no form (only email address shown) | 0% — skip |
| Login-walled or broken site | 0% — skip |

**Realistic blended rate across random business list: 70-85%**

The 15-30% failures are not fixable without manual work. Log them, skip them, move on.

---

## Input Format

CSV file with these columns:

```
website_url, contact_name, sender_name, sender_email, subject, message
https://acmeplumbing.com, John, Your Name, you@yourdomain.com, Quick question, Hi John...
https://bestlawyers.com, Sarah, Your Name, you@yourdomain.com, Partnership idea, Hey Sarah...
```

The `message` column contains your pre-written email — fully written, ready to paste.

---

## Pipeline Architecture

```
CSV (website_url + pre-written fields)
         |
         v
Phase 1: Contact Form Finder
  - Fetch homepage HTML
  - Check nav, footer for "Contact", "Get in Touch", etc.
  - Try common paths: /contact, /contact-us, /reach-us, /get-in-touch
  - Output: actual contact form URL (or SKIP if none found)
         |
         v
Phase 2: Skyvern Task
  - POST to local Skyvern API with form URL + prompt
  - Skyvern takes screenshots, uses Haiku to navigate
  - Fills: name, email, subject (if exists), message
  - Submits
         |
         v
Phase 3: CAPTCHA Handler (fires if Skyvern detects CAPTCHA)
  - 2captcha solves it
  - Returns token, Skyvern injects it, continues
         |
         v
Phase 4: Result Logger
  - Log: success / failed / skipped (no form) / blocked
  - Timestamp, site URL, error message if failed
```

---

## Component 1: Skyvern Setup

**Self-hosted via Docker (recommended — free compute, your Haiku key):**

```bash
git clone https://github.com/Skyvern-AI/skyvern.git
cd skyvern

# Create .env file
ANTHROPIC_API_KEY=your_haiku_api_key_here

# Start
docker compose up -d

# API runs at: http://localhost:8000
# UI runs at: http://localhost:8080
```

**Creating a task (real API call):**

```python
import requests
import time

SKYVERN_URL = "http://localhost:8000"
SKYVERN_KEY = "your_local_key"  # Found in Skyvern UI settings

def run_skyvern_task(contact_url, sender_name, sender_email, subject, message):
    payload = {
        "url": contact_url,
        "prompt": f"""
            Find the contact form on this page.
            Fill in the following fields:
            - Name or Full Name: {sender_name}
            - Email: {sender_email}
            - Subject (if the field exists): {subject}
            - Message or Comment: {message}
            If there is a phone field, skip it or leave it blank.
            After filling all fields, click the Submit or Send button.
            Do not click any other buttons.
        """,
        "engine": "skyvern-2.0",
        "max_steps": 25
    }

    headers = {
        "x-api-key": SKYVERN_KEY,
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"{SKYVERN_URL}/v1/run/tasks",
        json=payload,
        headers=headers
    )
    task = response.json()
    run_id = task["run_id"]

    # Poll for result
    for _ in range(60):  # max 5 minutes
        time.sleep(5)
        result = requests.get(
            f"{SKYVERN_URL}/v1/run/tasks/{run_id}",
            headers=headers
        ).json()
        status = result["status"]
        if status in ["completed", "failed", "timed_out"]:
            return status, result
    
    return "timeout", {}
```

**Key facts from docs:**
- `engine: "skyvern-2.0"` is their best engine for multi-step tasks
- `max_steps: 25` — each screenshot+action = 1 step; form fills usually take 8-15 steps
- Tasks take 30-60 seconds each
- Self-hosted uses whatever LLM you configure via env vars
- For Haiku specifically: set `LLM_CONFIG_NAME=ANTHROPIC_CLAUDE` in .env and configure model name

---

## Component 2: 2captcha Integration

**Install:**
```bash
pip install 2captcha-python
```

**Basic reCAPTCHA v2 solve:**
```python
from twocaptcha import TwoCaptcha, TimeoutException, ApiException

solver = TwoCaptcha('YOUR_2CAPTCHA_API_KEY')

def solve_captcha(sitekey, page_url):
    try:
        result = solver.recaptcha(
            sitekey=sitekey,
            url=page_url
        )
        return result['code']  # This is the token to inject
    except TimeoutException:
        return None  # Captcha took too long, skip this site
    except ApiException as e:
        return None  # API error, skip

def solve_captcha_v3(sitekey, page_url, action='submit'):
    try:
        result = solver.recaptcha(
            sitekey=sitekey,
            url=page_url,
            version='v3',
            action=action,
            score=0.7
        )
        return result['code']
    except Exception:
        return None
```

**Supported types (all relevant to contact forms):**
- reCAPTCHA v2 — standard checkbox: `solver.recaptcha(sitekey, url)`
- reCAPTCHA v3 — invisible score-based: `solver.recaptcha(sitekey, url, version='v3')`
- hCaptcha — common on Squarespace/Wix sites: `solver.hcaptcha(sitekey, url)`
- Cloudflare Turnstile — increasingly common: `solver.turnstile(sitekey, url)`

**Cost reality:**
- reCAPTCHA v2: $1.00–$2.99 per 1,000 solves
- reCAPTCHA v3: $1.45–$2.99 per 1,000 solves
- At 100/day, max $0.30/day for CAPTCHAs

**Note on Skyvern + 2captcha integration:**
Skyvern has partial native CAPTCHA handling. The integration point is: when Skyvern's task fails or stalls on a CAPTCHA, the orchestrator catches it, calls 2captcha directly with the sitekey (extracted from page HTML), gets the token back, and resumes. This requires a webhook or polling on the Skyvern task to detect the stall — OR you configure 2captcha credentials directly in Skyvern's `.env` so it handles it internally (check Skyvern docs for `TWOCAPTCHA_KEY` env var).

---

## Component 3: Contact Form URL Finder

This runs BEFORE Skyvern. Cheap, fast, no AI needed. Finds the real contact form URL so Skyvern doesn't waste steps hunting.

```python
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

CONTACT_KEYWORDS = [
    'contact', 'contact-us', 'reach-us', 'get-in-touch',
    'touch', 'connect', 'write-us', 'message-us', 'talk-to-us'
]

def find_contact_url(website_url):
    # Normalize URL
    if not website_url.startswith('http'):
        website_url = 'https://' + website_url

    # Step 1: Try common paths directly
    common_paths = ['/contact', '/contact-us', '/contact_us', '/reach-us',
                    '/get-in-touch', '/contactus', '/connect', '/about/contact']
    
    for path in common_paths:
        test_url = website_url.rstrip('/') + path
        try:
            r = requests.head(test_url, timeout=5, allow_redirects=True)
            if r.status_code == 200:
                return test_url
        except:
            continue

    # Step 2: Scrape homepage for contact links
    try:
        r = requests.get(website_url, timeout=8, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        soup = BeautifulSoup(r.text, 'html.parser')
        
        for a in soup.find_all('a', href=True):
            href = a['href'].lower()
            text = a.get_text().lower()
            if any(kw in href or kw in text for kw in CONTACT_KEYWORDS):
                full_url = urljoin(website_url, a['href'])
                # Make sure it's same domain
                if urlparse(full_url).netloc == urlparse(website_url).netloc:
                    return full_url
    except:
        pass

    return None  # No contact form found — skip this site
```

---

## Component 4: Proxy Rotation (Smartproxy)

Only needed if you start hitting Cloudflare blocks. Start WITHOUT proxies, add when you see failures.

**Skyvern self-hosted proxy config (in .env):**
```
PROXY_HOST=gate.smartproxy.com
PROXY_PORT=10001
PROXY_USERNAME=your_username
PROXY_PASSWORD=your_password
```

**Or pass per-task via Playwright proxy config inside Skyvern** (check Skyvern docs for `proxy` parameter in task payload — may be available in newer versions).

**Smartproxy cost:** Pay-as-you-go residential starts around $7-10/GB. At 100 form fills/day with ~2MB per session, that's ~0.2GB/day = ~$1.50-2/day if you need proxies for everything.

---

## Component 5: The Orchestrator (Full Flow)

```python
import csv
import json
import time
import logging
from datetime import datetime

logging.basicConfig(
    filename=f'outreach_log_{datetime.now().strftime("%Y%m%d")}.txt',
    level=logging.INFO,
    format='%(asctime)s %(message)s'
)

def run_outreach(csv_path, rate_per_hour=40):
    delay_seconds = 3600 / rate_per_hour  # seconds between submissions

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    results = {'success': 0, 'failed': 0, 'skipped': 0, 'total': len(rows)}

    for i, row in enumerate(rows):
        site = row['website_url']
        print(f"[{i+1}/{len(rows)}] Processing: {site}")

        # Phase 1: Find contact form
        contact_url = find_contact_url(site)
        if not contact_url:
            logging.info(f"SKIPPED (no form found): {site}")
            results['skipped'] += 1
            continue

        # Phase 2: Run Skyvern
        status, result = run_skyvern_task(
            contact_url=contact_url,
            sender_name=row['sender_name'],
            sender_email=row['sender_email'],
            subject=row['subject'],
            message=row['message']
        )

        if status == 'completed':
            logging.info(f"SUCCESS: {site} -> {contact_url}")
            results['success'] += 1
        else:
            logging.info(f"FAILED ({status}): {site} -> {contact_url}")
            results['failed'] += 1

        # Rate limiting — don't look like a bot
        time.sleep(delay_seconds)

    print(f"\nDone. Success: {results['success']} | Failed: {results['failed']} | Skipped: {results['skipped']}")
    return results

# Run it
if __name__ == "__main__":
    run_outreach('my_list.csv', rate_per_hour=40)
```

---

## Cost Per Email (Operational)

| Item | Cost |
|------|------|
| Claude Haiku (form fill ~30k tokens) | ~$0.02-0.04 |
| 2captcha (if CAPTCHA present, ~40% of sites) | ~$0.001 avg |
| Smartproxy (if needed, ~2MB/session) | ~$0.01-0.02 |
| **Total per successful email** | **~$0.03-0.07** |

100/day = ~$3-7/day in API costs. Essentially nothing.

---

## Build Order

1. **Get Skyvern running locally** — Docker compose up, verify UI at localhost:8080
2. **Test one manual task** — paste one contact URL into Skyvern UI, confirm it fills a form
3. **Build the contact form finder** — test on 20 URLs, verify hit rate
4. **Build the orchestrator** — CSV in, logs out, no CAPTCHA yet
5. **Test on 20 real sites** — measure actual success rate
6. **Add 2captcha** — get API key, integrate, retest
7. **Add proxies only if needed** — don't add complexity until you see Cloudflare blocks

---

## What Will Still Fail (Accept This)

- Sites with no contact form (email address only, or phone only)
- Sites that require account creation before contacting
- Sites with custom slider/puzzle CAPTCHAs (2captcha handles most but not all)
- Sites that block submissions without a real session cookie history
- Honeypot fields that mark submissions as spam server-side (form submits but goes to spam)

These are not solvable without human intervention. Log them, skip them.

---

## Files This Will Create

```
contact-outreach/
  find_contact_url.py        # Phase 1: URL finder
  skyvern_task.py            # Phase 2: Skyvern integration
  captcha_solver.py          # Phase 3: 2captcha integration  
  orchestrator.py            # Main runner (loops CSV)
  my_list.csv                # Your input list
  outreach_log_YYYYMMDD.txt  # Output log
```
