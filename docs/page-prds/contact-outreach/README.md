# PRD: Automated Contact Form Outreach

## What This Is

A two-phase pipeline that takes a raw list of business websites, filters it down to only clean targets (no CAPTCHA, no Cloudflare, form confirmed present), then automatically fills and submits the contact form on each — mimicking exactly what a human would do.

**V1 has zero CAPTCHA solving and zero proxies.** The filter eliminates those sites before the agent ever touches them. Complexity added only when actually needed.

---

## The Stack

| Component | Tool | Purpose |
|-----------|------|---------|
| List filter | Python + BeautifulSoup + requests | Finds contact URL, confirms form exists, detects all blockers |
| Browser automation | browser-use (open source Python library) | Navigates and fills the form |
| AI brain | Claude Haiku 4.5 via Anthropic API | Tells browser-use what to click (DOM-first, not screenshot-heavy) |
| Orchestrator | Python async script | Loops through clean CSV, calls browser-use per row |

**No Docker. No Skyvern. No 2captcha. No proxies. Just pip install and run.**

---

## Why browser-use Over Skyvern

- **Skyvern** = Docker container, separate API server, database, 20-minute setup minimum
- **browser-use** = `pip install browser-use`, done. It's a Python library.
- **Skyvern** = screenshot-first (every step sends an image to the LLM — expensive)
- **browser-use** = DOM-first (reads page HTML as text, only screenshots when truly needed — 5-10x cheaper per step)
- Both use Haiku as the brain. browser-use is just cheaper and simpler.

---

## Honest Success Rate

**On the raw unfiltered list:**
- ~40-60% of random business sites have CAPTCHAs, Cloudflare, or no form at all
- Don't run the agent on these — it's wasted money

**After the filter script runs:**
- 95-98% of what's left should fill successfully
- Failures will be: JS-only form submissions, broken sites, silent reCAPTCHA v3 rejections

**The filter is the product.** The agent just executes.

---

## Input / Output

**Input CSV (raw list):**
```
website_url, sender_name, sender_email, subject, message
https://acmeplumbing.com, Your Name, you@yourdomain.com, Quick question, Hi there...
https://bestlawyers.com, Your Name, you@yourdomain.com, Partnership idea, Hey...
```

**After Phase 1 filter — clean CSV:**
```
contact_url, sender_name, sender_email, subject, message
https://acmeplumbing.com/contact, Your Name, you@yourdomain.com, Quick question, Hi there...
```

**Output log:**
```
2026-04-19 10:01:22 SUCCESS: acmeplumbing.com -> /contact
2026-04-19 10:02:45 SUCCESS: bestlawyers.com -> /contact-us
2026-04-19 10:03:12 FAILED (timeout): somebrokenshop.com
```

---

## Phase 1: The Filter Script

Runs once on your raw list. No AI. Costs $0. Processes 200 sites in under 2 minutes.

**What it checks:**
1. Is the site reachable? (not 403, not Cloudflare challenge page)
2. Can it find a contact form page? (common paths + link scraping)
3. Does that page have an actual `<form>` with name/email/message fields?
4. Does the page source contain any CAPTCHA or bot-protection signatures?

**CAPTCHA signatures to detect:**
- `google.com/recaptcha` or `grecaptcha` or `g-recaptcha` → reCAPTCHA v2
- `grecaptcha.execute` or `grecaptcha.render` → **reCAPTCHA v3 (invisible — must catch this)**
- `hcaptcha.com` or `h-captcha` → hCaptcha
- `challenges.cloudflare.com` or `cf-turnstile` → Cloudflare Turnstile
- `friendlycaptcha.com` → FriendlyCaptcha
- Honeypot fields: hidden inputs named `website`, `url`, `phone2`, `fax` → flag as suspicious

**Cloudflare network block detection:**
- HTTP 403 response = blocked
- Response HTML contains `cf-browser-verification` or `Checking your browser` = Cloudflare challenge

```python
import requests
import csv
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
TIMEOUT = 8

CONTACT_PATHS = [
    '/contact', '/contact-us', '/contact_us', '/contactus',
    '/reach-us', '/get-in-touch', '/connect', '/about/contact',
    '/about-us/contact', '/support/contact', '/help/contact'
]

CONTACT_KEYWORDS = [
    'contact', 'contact us', 'get in touch', 'reach us',
    'write to us', 'message us', 'talk to us', 'connect'
]

CAPTCHA_SIGNATURES = [
    'google.com/recaptcha',
    'grecaptcha',
    'g-recaptcha',
    'hcaptcha.com',
    'h-captcha',
    'challenges.cloudflare.com',
    'cf-turnstile',
    'friendlycaptcha.com',
]

# reCAPTCHA v3 is invisible — must detect separately
RECAPTCHA_V3_SIGNATURES = [
    'grecaptcha.execute',
    'grecaptcha.render',
    "'v3'",
    '"v3"',
]

CLOUDFLARE_SIGNATURES = [
    'cf-browser-verification',
    'Checking your browser',
    'DDoS protection by Cloudflare',
    'cf_clearance',
]

HONEYPOT_NAMES = ['website', 'url', 'phone2', 'fax', 'address2', 'company_url']


def normalize_url(url):
    if not url.startswith('http'):
        return 'https://' + url
    return url


def is_cloudflare_blocked(response):
    if response.status_code == 403:
        return True
    text = response.text
    return any(sig in text for sig in CLOUDFLARE_SIGNATURES)


def find_contact_url(base_url):
    # Try common paths first
    for path in CONTACT_PATHS:
        test_url = base_url.rstrip('/') + path
        try:
            r = requests.head(test_url, timeout=5, headers=HEADERS, allow_redirects=True)
            if r.status_code == 200:
                return test_url
        except Exception:
            continue

    # Scrape homepage for contact links
    try:
        r = requests.get(base_url, timeout=TIMEOUT, headers=HEADERS)
        if is_cloudflare_blocked(r):
            return None
        soup = BeautifulSoup(r.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            href = a.get('href', '').lower()
            text = a.get_text().lower().strip()
            if any(kw in href or kw == text or kw in text for kw in CONTACT_KEYWORDS):
                full_url = urljoin(base_url, a['href'])
                if urlparse(full_url).netloc == urlparse(base_url).netloc:
                    return full_url
    except Exception:
        pass

    return None


def analyze_contact_page(contact_url):
    result = {
        'reachable': False,
        'has_form': False,
        'captcha_type': 'none',
        'cloudflare_blocked': False,
        'honeypot_detected': False,
    }

    try:
        r = requests.get(contact_url, timeout=TIMEOUT, headers=HEADERS)
        result['reachable'] = True

        if is_cloudflare_blocked(r):
            result['cloudflare_blocked'] = True
            return result

        html = r.text
        soup = BeautifulSoup(html, 'html.parser')

        # Check for actual form with email-like fields
        forms = soup.find_all('form')
        for form in forms:
            inputs = form.find_all(['input', 'textarea'])
            input_names = [i.get('name', '').lower() + i.get('type', '').lower() for i in inputs]
            input_text = ' '.join(input_names)
            if any(kw in input_text for kw in ['email', 'message', 'name', 'comment', 'text']):
                result['has_form'] = True
                break

        # Detect honeypots
        all_inputs = soup.find_all('input', {'type': 'hidden'})
        for inp in all_inputs:
            name = inp.get('name', '').lower()
            if name in HONEYPOT_NAMES:
                result['honeypot_detected'] = True

        # Detect CAPTCHA type (check v3 first — it's the sneaky one)
        if any(sig in html for sig in RECAPTCHA_V3_SIGNATURES):
            result['captcha_type'] = 'recaptcha_v3'
        elif any(sig in html for sig in CAPTCHA_SIGNATURES):
            for sig in CAPTCHA_SIGNATURES:
                if sig in html:
                    if 'hcaptcha' in sig:
                        result['captcha_type'] = 'hcaptcha'
                    elif 'turnstile' in sig or 'cloudflare' in sig:
                        result['captcha_type'] = 'turnstile'
                    else:
                        result['captcha_type'] = 'recaptcha_v2'
                    break

    except Exception as e:
        result['error'] = str(e)

    return result


def run_filter(input_csv, output_csv):
    with open(input_csv, 'r') as f:
        rows = list(csv.DictReader(f))

    clean = []
    skipped = []

    for i, row in enumerate(rows):
        url = normalize_url(row['website_url'])
        print(f"[{i+1}/{len(rows)}] {url}")

        contact_url = find_contact_url(url)
        if not contact_url:
            skipped.append({**row, 'skip_reason': 'no_contact_url_found'})
            continue

        analysis = analyze_contact_page(contact_url)

        if analysis.get('cloudflare_blocked'):
            skipped.append({**row, 'skip_reason': 'cloudflare_blocked'})
        elif not analysis.get('has_form'):
            skipped.append({**row, 'skip_reason': 'no_form_detected'})
        elif analysis.get('captcha_type') != 'none':
            skipped.append({**row, 'skip_reason': f"captcha_{analysis['captcha_type']}"})
        else:
            clean.append({**row, 'contact_url': contact_url})

        time.sleep(0.3)  # be polite

    # Write clean list
    if clean:
        with open(output_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=clean[0].keys())
            writer.writeheader()
            writer.writerows(clean)

    # Write skipped list for review
    if skipped:
        with open(output_csv.replace('.csv', '_skipped.csv'), 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=skipped[0].keys())
            writer.writeheader()
            writer.writerows(skipped)

    print(f"\nClean: {len(clean)} | Skipped: {len(skipped)} | Total: {len(rows)}")
    return clean


if __name__ == '__main__':
    run_filter('raw_list.csv', 'clean_list.csv')
```

---

## Phase 2: browser-use Runner

**Install:**
```bash
pip install browser-use langchain-anthropic
playwright install chromium
```

**Set env var:**
```
ANTHROPIC_API_KEY=your_key_here
```

**The runner:**
```python
import asyncio
import csv
import logging
from datetime import datetime
from browser_use import Agent
from langchain_anthropic import ChatAnthropic

logging.basicConfig(
    filename=f'outreach_log_{datetime.now().strftime("%Y%m%d_%H%M")}.txt',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

llm = ChatAnthropic(model='claude-haiku-4-5-20251001')


async def fill_form(contact_url, sender_name, sender_email, subject, message):
    task = f"""
    Go to this URL: {contact_url}

    Find the contact form and fill it with exactly these values:
    - Name / Full Name field: {sender_name}
    - Email field: {sender_email}
    - Subject field (only if it exists): {subject}
    - Message / Comment / Body field: {message}

    Rules:
    - Do NOT fill phone, company, or website fields
    - Do NOT check any checkboxes unless required to submit
    - After all fields are filled, click the Submit or Send button once
    - Do NOT navigate away or click anything else
    - If there is no form visible, stop and report failure
    """

    try:
        agent = Agent(task=task, llm=llm)
        result = await agent.run(max_steps=20)
        return 'success', str(result)
    except Exception as e:
        return 'failed', str(e)


async def run_outreach(clean_csv, delay_seconds=45):
    with open(clean_csv, 'r') as f:
        rows = list(csv.DictReader(f))

    counts = {'success': 0, 'failed': 0, 'total': len(rows)}

    for i, row in enumerate(rows):
        url = row['contact_url']
        print(f"[{i+1}/{len(rows)}] {url}")

        status, detail = await fill_form(
            contact_url=url,
            sender_name=row['sender_name'],
            sender_email=row['sender_email'],
            subject=row['subject'],
            message=row['message']
        )

        if status == 'success':
            logging.info(f"SUCCESS: {url}")
            counts['success'] += 1
        else:
            logging.warning(f"FAILED: {url} | {detail}")
            counts['failed'] += 1

        if i < len(rows) - 1:
            await asyncio.sleep(delay_seconds)

    print(f"\nDone — Success: {counts['success']} | Failed: {counts['failed']}")


if __name__ == '__main__':
    asyncio.run(run_outreach('clean_list.csv', delay_seconds=45))
```

**Key settings:**
- `max_steps=20` — a pre-filtered clean form should take 5-10 steps max; 20 is a safety ceiling
- `delay_seconds=45` — 45 seconds between submissions at 100/day = ~80 per working day, casual pace
- Reduce delay to 20s for 200+/day, but monitor for any blocks

---

## Cost Per Email

browser-use reads DOM (text) first, not screenshots. Steps are cheaper than Skyvern.

| Item | Cost |
|------|------|
| Haiku tokens (DOM text, ~5-10 steps, ~5k-15k tokens) | ~$0.005-0.015 |
| No CAPTCHA service needed (filtered out) | $0 |
| No proxies needed (filtered out) | $0 |
| **Total per successful submission** | **~$0.01-0.03** |

| Volume | Est. daily cost |
|--------|----------------|
| 100/day | $1-3 |
| 500/day | $5-15 |

Run 10 real submissions first and check your Anthropic usage dashboard to get your actual per-task cost before scaling.

---

## Build Order

1. `pip install requests beautifulsoup4` — run filter on 20 test URLs, confirm it finds forms and correctly flags CAPTCHAs
2. `pip install browser-use langchain-anthropic && playwright install chromium` — test one form fill manually on a known clean site
3. Wire them together: filter → clean CSV → runner
4. Run 20 real submissions, check logs and Anthropic cost dashboard
5. Scale up once actual cost-per-submission is confirmed

---

## V2 (Add Only If Needed)

These are NOT in V1. Add them only if real-world testing reveals they're necessary:

| Problem Seen | Solution |
|-------------|----------|
| reCAPTCHA v3 silent rejections still happening | Add 2captcha (pip install 2captcha-python, ~$0.001-0.003/solve) |
| Cloudflare blocks despite filtering | Add Smartproxy residential proxies (~$7-10/GB) |
| Site uses AJAX form (form submits but nothing happens) | browser-use handles real browser — usually works already |
| Want to run 5 concurrent agents | Wrap runner in asyncio.gather() with semaphore |

---

## What Will Still Fail (Accept It)

- Sites where the form is loaded by JavaScript after page load (rare but exists)
- reCAPTCHA v3 silent rejections — submission looks successful but gets spam-scored on their end
- Sites that check session age / cookie history before accepting submissions
- Honeypot fields that flag the submission as spam even if you didn't fill them

These are not solvable in V1. Log them, review manually if the site is important, move on.

---

## Files

```
contact-outreach/
  filter.py          # Phase 1: scrape, detect blockers, output clean CSV
  runner.py          # Phase 2: browser-use + Haiku, fill and submit
  raw_list.csv       # Your input (website_url + email fields)
  clean_list.csv     # Output of filter (contact_url + email fields)
  clean_list_skipped.csv   # Filtered-out sites with reason
  outreach_log_YYYYMMDD.txt  # Submission results
```

---

## Email Writing System (Shared by V1 and V2)

### How It Works

No AI call per email. No spinning service. Cost per email: **$0 after one-time setup.**

1. **One-time:** Claude generates 20-30 variant sentences for each section (~$0.10 total, run once, never again)
2. **Per email:** Python randomly picks one variant per section, injects the SEO data from the CSV, assembles the full email in milliseconds
3. **Result:** Every email looks completely unique. Same hook, different wording, different structure

### Why This Works As An Outreach Strategy

- Standard cold email: ~1% open rate
- Custom email (no SEO data): ~4% open rate (4x)
- This system with competitor data + traffic values in subject line: estimated 8-12%+ open rate
- The subject line does the work: *"[Competitor] is getting $10,400/mo in free traffic — [Business] is at #14"*
- Inside the email they see exactly who's beating them and how much it's costing them. That's the Loom video equivalent in text.

### Why Contact Forms Beat Cold Email For This

| | Cold Email | Contact Forms |
|--|-----------|--------------|
| Sending limits | 30-50/day per warmed inbox | None — you're not sending email |
| Domain warming required | Yes — 30 days minimum | No |
| Your IP/reputation at risk | Yes | No — their server sends the notification |
| Multiple accounts needed | Yes, for volume | No — one reply-to email handles everything |
| Deliverability issues | SPF/DKIM/spam filters | Not your problem — their server sends it |
| Days to get started | 30+ days warming | Today |

When you submit a contact form, their web server sends the notification to the business owner. Your email only appears as the reply-to. You are not sending anything. No warming, no limits, no reputation risk. One inbox handles all replies.

---

### CSV Shape (Full — SEO + Email Fields)

```
website_url, contact_url, blocker_type,
business_name, contact_first_name, niche, keyword, city,
their_rank,
comp1_name, comp1_rank, comp1_traffic,
comp2_name, comp2_rank, comp2_traffic,
comp3_name, comp3_rank, comp3_traffic,
top_competitor, top_rank, top_traffic,
sender_name, sender_email,
subject, message
```

The SEO scraper fills: `keyword` through `top_traffic` (one search per city, same data for every business in that city)
The filter fills: `contact_url`, `blocker_type`
The assembler fills: `subject`, `message`
The runner reads: `contact_url`, `sender_name`, `sender_email`, `subject`, `message`

---

### Step 1: Generate Variant Pool (Run Once)

```python
# generate_variants.py — run once, costs ~$0.10 total
import anthropic
import json

client = anthropic.Anthropic()

SECTIONS = {
    'greeting': 'Casual opening greeting using {first_name}. Short. Not "I hope this finds you well."',
    'opener': 'Opening line mentioning you looked at their rankings for {keyword} in {city}. Sound human, not salesy.',
    'competitor_intro': 'One sentence introducing the list of competitors about to be shown. No fluff.',
    'pain_point': 'One sentence about {top_competitor} capturing leads that should go to {business_name}. Direct.',
    'traffic_framing': 'One sentence framing ${top_traffic}/month as the value of that top ranking. Make it feel real.',
    'offer': 'One sentence saying you help local {niche} businesses move up in that pack. End with a single question asking if they want to talk.',
    'sign_off': 'Two-word casual sign-off. No "Best regards."',
}

variants = {}
for section, description in SECTIONS.items():
    response = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=1500,
        messages=[{
            'role': 'user',
            'content': f"""Write 25 different versions of this email section.
Description: {description}
Keep {{variable}} placeholders exactly as shown in the description.
Return ONLY a valid JSON array of 25 strings. Nothing else."""
        }]
    )
    variants[section] = json.loads(response.content[0].text.strip())
    print(f"Generated {section}: {len(variants[section])} variants")

with open('spinner_variants.json', 'w') as f:
    json.dump(variants, f, indent=2)

print("Done. spinner_variants.json saved.")
```

---

### Step 2: Assemble Emails (Run Per Batch, $0)

```python
# assemble_emails.py
import csv
import json
import random

with open('spinner_variants.json') as f:
    VARIANTS = json.load(f)

def pick(section, row):
    template = random.choice(VARIANTS[section])
    try:
        return template.format(**row)
    except KeyError:
        return template

def build_subject(row):
    templates = [
        "{comp1_name} gets ${comp1_traffic}/mo free — {business_name} is at #{their_rank}",
        "Your competitors are getting free traffic you're not — {keyword} in {city}",
        "${top_traffic}/mo going to {top_competitor} instead of {business_name}",
        "{comp1_name}, {comp2_name}, {comp3_name} all rank above {business_name} for {keyword}",
    ]
    return random.choice(templates).format(**row)

def assemble_email(row):
    body = f"""{pick('greeting', row)}

{pick('opener', row)}

{pick('competitor_intro', row)}

  #{row['comp1_rank']} {row['comp1_name']} — ~${row['comp1_traffic']}/mo in traffic value
  #{row['comp2_rank']} {row['comp2_name']} — ~${row['comp2_traffic']}/mo in traffic value
  #{row['comp3_rank']} {row['comp3_name']} — ~${row['comp3_traffic']}/mo in traffic value

{row['business_name']} is currently ranking #{row['their_rank']}.

{pick('pain_point', row)}

{pick('traffic_framing', row)}

{pick('offer', row)}

{pick('sign_off', row)}
{row['sender_name']}"""
    return body

def run_assembler(input_csv, output_csv):
    with open(input_csv, 'r') as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        row['subject'] = build_subject(row)
        row['message'] = assemble_email(row)

    with open(output_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Assembled {len(rows)} emails → {output_csv}")

if __name__ == '__main__':
    run_assembler('routed_list.csv', 'ready_to_send.csv')
```

---

### Full Pipeline (Both V1 and V2)

```
raw_list.csv
(website URLs + business name + niche + SEO data from one Ahrefs search)
        |
        v
filter.py
(finds contact URL, detects CAPTCHAs/Cloudflare, outputs blocker_type)
        |
        v
assemble_emails.py
(spins variants, injects SEO data, writes subject + message per row — $0)
        |
        v
[V1] runner.py          — clean sites only
[V2] orchestrator_v2.py — all sites, routes by blocker_type
        |
        v
ready_to_send_log_YYYYMMDD.txt
```

### Cost Summary

| Step | Cost |
|------|------|
| Variant pool generation (once ever) | ~$0.10 |
| Email assembly per batch | $0 |
| Browser-use + Haiku per submission | ~$0.01-0.03 |
| 2captcha per CAPTCHA site (V2 only) | ~$0.002 |
| Proxy per Cloudflare site (V2 only) | ~$0.01-0.02 |
| **V1 total per sent email** | **~$0.01-0.03** |
| **V2 total per sent email (blended)** | **~$0.015-0.05** |

100/day V1: ~$1-3. 500/day V1: ~$5-15.
100/day V2: ~$1.50-5. 500/day V2: ~$7.50-25.
