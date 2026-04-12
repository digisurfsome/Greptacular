# SiteSprint Auto-Builder -- Sites Built Automatically When Leads Reply

**Monitor SmartLead -> Classify Reply -> Research Company -> Build Site -> Deploy to Vercel -> Notify via Telegram**

## What You'll Build

An automated system that monitors your SmartLead campaigns for interested replies, auto-researches the company, builds a premium dark-theme website, deploys it to Vercel, and sends you a Telegram notification with the live URL -- all without you touching anything. Runs every 30 minutes via a macOS LaunchAgent.

This is the crown jewel automation. A lead replies "interested" and within 30 minutes you have a live custom website ready to show them.

---

## Golden Rules

These rules are non-negotiable across the entire SiteSprint system:

1. **NOTHING IS EVER FABRICATED** -- Reviews must be from verifiable platforms (Google, Yelp, BBB, Facebook, Nextdoor, Houzz). Include the reviewer's name exactly as it appears. Never generate or paraphrase reviews. If reviews can't be scraped, replace the testimonials section with a "Verified Social Proof" section showing platform logos + ratings + links.
2. **ALL IMAGES FROM THEIR SITE** -- Scrape every image from the business's existing website. Use Wix image API format for consistent sizing. If no images are available, use CSS-only backgrounds (gradients, patterns) -- NEVER stock photos.
3. **LOGO IS ALWAYS INCORPORATED** -- Place it in the navbar, footer, and hero (if distinctive). If no logo is available, use a styled text logo with a Lucide icon.
4. **NO LINKS TO OLD SITES** -- Never link CTAs to the business's existing website. All CTAs link to `/contact#book`. Include a booking placeholder with a dashed border: "Calendar booking coming soon -- call or message for now."
5. **COLD EMAIL SCRIPTS -- NO SIGNATURES** -- SmartLead handles signatures and subject lines separately. Never include them in your email copy.

---

## Prerequisites

- Python 3.10+
- Node.js 18+
- SmartLead account with active campaigns
- Anthropic API key (Claude Haiku for classification, Claude Sonnet for research)
- Vercel account with API token
- Telegram bot token and chat ID
- The `premium-v2` Next.js site template already built

## Environment Variables

These must be set in your shell environment or `.env`:

```
SMARTLEAD_API_KEY=your_smartlead_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
VERCEL_TOKEN=your_vercel_api_token
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=5915551069
```

---

## The Pipeline (6 Stages)

### Stage 1: MONITOR -- Poll SmartLead for New Replies

The script polls two SmartLead campaigns every 30 minutes:

- **Campaign 3099885** -- Service Businesses
- **Campaign 3099933** -- Website Redesign

API call to fetch replies:

```python
import requests

SMARTLEAD_API_KEY = os.environ["SMARTLEAD_API_KEY"]
CAMPAIGN_IDS = [3099885, 3099933]

def fetch_new_replies():
    all_replies = []
    for campaign_id in CAMPAIGN_IDS:
        url = f"https://server.smartlead.ai/api/v1/campaigns/{campaign_id}/replies?api_key={SMARTLEAD_API_KEY}"
        response = requests.get(url)
        replies = response.json()
        all_replies.extend(replies)
    return all_replies
```

Each reply contains the lead's email, company name, and the reply text. The script checks these against `sitesprint_processed.json` to skip already-handled replies.

---

### Stage 2: CLASSIFY -- Claude Haiku Determines Intent

Each new reply is sent to Claude Haiku for fast, cheap classification.

Classification prompt:

```python
CLASSIFY_PROMPT = """You are classifying a cold email reply from a business owner.

The original email offered to build them a free demo website.

Classify this reply into exactly one category:
- INTERESTED: They want to see the site, learn more, or are open to it
- MEETING_REQUEST: They want to schedule a call or meeting
- NOT_INTERESTED: They declined, asked to be removed, or are not interested

Reply with ONLY the category name, nothing else.

Reply text:
{reply_text}"""
```

```python
import anthropic

client = anthropic.Anthropic()

def classify_reply(reply_text):
    message = client.messages.create(
        model="claude-haiku-4-20250414",
        max_tokens=20,
        messages=[{
            "role": "user",
            "content": CLASSIFY_PROMPT.format(reply_text=reply_text)
        }]
    )
    classification = message.content[0].text.strip()
    return classification  # "INTERESTED", "MEETING_REQUEST", or "NOT_INTERESTED"
```

Only `INTERESTED` and `MEETING_REQUEST` replies trigger the auto-build pipeline. `NOT_INTERESTED` replies are logged and skipped.

---

### Stage 3: ALERT -- Telegram Notification

As soon as an interested reply is detected, send an immediate Telegram alert:

```python
def send_telegram(message):
    bot_token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    requests.post(url, json={
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    })

# On interested reply:
send_telegram(
    f"*New interested lead detected*\n"
    f"Company: {lead['company_name']}\n"
    f"Email: {lead['email']}\n"
    f"Reply: {lead['reply_text'][:200]}\n\n"
    f"Auto-building site now..."
)
```

---

### Stage 4: RESEARCH -- Claude Sonnet Gathers Verified Data

Claude Sonnet researches the company across multiple sources to build a verified data profile.

Research prompt:

```python
RESEARCH_PROMPT = """You are researching a local service business to build them a website.
Gather ONLY verified, factual information. Do NOT fabricate anything.

Business: {company_name}
Email domain: {domain}
Location: {city}, {state}

Research the following sources and extract:

1. **Their website** (if exists): ALL content, services listed, images, contact info, about text
2. **BBB (bbb.org)**: Rating, complaints, years in business, owner name, license info
3. **Google Business Profile**: Reviews (with exact reviewer names), photos, hours, service area
4. **Facebook**: Page info, reviews, photos
5. **Yelp**: Reviews (with exact reviewer names), photos, rating
6. **Nextdoor**: Recommendations, if available
7. **Houzz**: Portfolio, reviews, if applicable

Return a JSON object with:
{{
  "company_name": "...",
  "owner_name": "..." or null,
  "phone": "...",
  "address": "...",
  "city": "...",
  "state": "...",
  "industry": "...",
  "years_in_business": number or null,
  "bbb_rating": "..." or null,
  "services": ["..."],
  "reviews": [
    {{"platform": "Google", "author": "Exact Name", "text": "Exact review text", "rating": 5}}
  ],
  "images": ["url1", "url2"],
  "logo_url": "..." or null,
  "hours": "..." or null,
  "service_area": "...",
  "about_text": "..." or null,
  "licenses": ["..."] or []
}}

CRITICAL RULES:
- Reviews must have the exact reviewer name and exact text from the platform
- If you cannot verify a piece of information, set it to null
- Never fabricate reviews, services, or business details
- If the business has no verifiable reviews, return an empty reviews array"""
```

```python
def research_company(lead):
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": RESEARCH_PROMPT.format(
                company_name=lead["company_name"],
                domain=lead["email"].split("@")[1],
                city=lead.get("city", ""),
                state=lead.get("state", "")
            )
        }]
    )
    research = json.loads(message.content[0].text)

    # Save research to file for reference
    slug = slugify(lead["company_name"])
    with open(os.path.expanduser(f"~/{slug}-research.md"), "w") as f:
        f.write(f"# {lead['company_name']} Research\n\n")
        f.write(json.dumps(research, indent=2))

    return research
```

---

### Stage 5: BUILD -- Generate the Next.js Site

The builder copies the `premium-v2` template, injects the verified config, and runs the build.

```python
import subprocess
import shutil

def build_site(research_data):
    slug = slugify(research_data["company_name"])
    site_dir = f"04-sites-built/{slug}"

    # Copy premium-v2 template
    shutil.copytree("templates/premium-v2", site_dir)

    # Determine industry theme (dark theme with accent)
    theme = get_industry_theme(research_data["industry"])

    # Write site-config.json with all verified data
    config = {
        "business": research_data,
        "theme": theme,
        "reviews": research_data["reviews"],  # Empty array if none verified
        "pages": ["home", "services", "about", "contact"]
    }
    with open(f"{site_dir}/site-config.json", "w") as f:
        json.dump(config, f, indent=2)

    # Install dependencies and build
    subprocess.run(["npm", "install"], cwd=site_dir, check=True)
    subprocess.run(["npx", "next", "build"], cwd=site_dir, check=True)

    return site_dir, slug
```

#### What Gets Built Automatically

- Dark themed site with industry-appropriate accent color
- 4 pages: Home, Services, About, Contact
- Verified business data only (from BBB, directories)
- Reviews array empty by default (no fabrication -- reviews added only if scraped from verifiable platforms)
- Booking placeholder at `/contact#book` with dashed border
- Framer Motion animations: `ParallaxSection`, `AnimatedCounter`, `TextReveal`, `RevealLine`, `ScrollZoom`, `SlideIn`
- Logo in navbar and footer (scraped from their site, or styled text + Lucide icon)
- All images scraped from their existing site (CSS-only backgrounds if none found -- never stock photos)

#### Industry Dark Themes

| Industry | Accent Color |
|---|---|
| Concrete | slate/amber |
| Tree service | forest green |
| Garage doors | steel blue |
| Plumbing | blue |
| Landscaping | green |
| HVAC | sky blue |
| Roofing | amber/brown |

#### File Structure Per Site

```
04-sites-built/[business-slug]/
├── site-config.json          # All business data
├── next.config.js            # Image remote patterns
├── public/                   # Local images if needed
├── src/
│   ├── app/
│   │   ├── page.tsx          # Homepage
│   │   ├── services/page.tsx
│   │   ├── about/page.tsx
│   │   ├── contact/page.tsx
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── Navbar.tsx
│   │   ├── Footer.tsx
│   │   ├── Motion.tsx        # All animation components
│   │   └── StarRating.tsx
│   └── lib/
│       ├── config.ts         # Types + theme
│       └── icons.ts          # Service icon mapping
```

#### Tech Stack

- Next.js 14 (React 18)
- Tailwind CSS
- Framer Motion with enhanced animations
- Lucide React icons
- Vercel hosting (public, OIDC auth disabled)

---

### Stage 6: DEPLOY -- Push to Vercel and Disable Auth

Deploy the built site to Vercel and ensure it's publicly accessible.

```python
def deploy_site(site_dir, slug):
    vercel_token = os.environ["VERCEL_TOKEN"]

    # Step 1: Deploy to Vercel
    result = subprocess.run(
        [
            "npx", "vercel", "--prod", "--yes",
            "--name", slug,
            "--scope", "alex-kamels-projects",
            "--token", vercel_token
        ],
        cwd=site_dir,
        capture_output=True,
        text=True,
        check=True
    )
    deploy_url = result.stdout.strip()

    # Step 2: CRITICAL -- Disable OIDC auth so site is publicly accessible
    # First, get the project ID
    project_response = requests.get(
        f"https://api.vercel.com/v9/projects/{slug}",
        headers={"Authorization": f"Bearer {vercel_token}"}
    )
    project_id = project_response.json()["id"]

    # Disable OIDC auth
    requests.patch(
        f"https://api.vercel.com/v1/projects/{project_id}",
        headers={
            "Authorization": f"Bearer {vercel_token}",
            "Content-Type": "application/json"
        },
        json={"oidcTokenConfig": {"enabled": False}}
    )

    # Step 3: Redeploy after auth disabled
    result = subprocess.run(
        [
            "npx", "vercel", "--prod", "--yes",
            "--name", slug,
            "--scope", "alex-kamels-projects",
            "--token", vercel_token
        ],
        cwd=site_dir,
        capture_output=True,
        text=True,
        check=True
    )
    final_url = result.stdout.strip()

    # Step 4: Verify public access
    verify = requests.get(final_url)
    if verify.status_code != 200:
        raise Exception(f"Site not publicly accessible: {final_url} returned {verify.status_code}")

    return final_url
```

---

### Stage 7: NOTIFY -- Send Live URL via Telegram

After successful deployment, send the final notification with the live URL and a summary of verified info for your review.

```python
def notify_completion(lead, research_data, live_url):
    review_count = len(research_data.get("reviews", []))
    services = ", ".join(research_data.get("services", [])[:5])

    message = (
        f"*Site built and deployed!*\n\n"
        f"Company: {research_data['company_name']}\n"
        f"URL: {live_url}\n"
        f"Industry: {research_data.get('industry', 'Unknown')}\n"
        f"Services: {services}\n"
        f"Verified reviews: {review_count}\n"
        f"BBB rating: {research_data.get('bbb_rating', 'N/A')}\n"
        f"Owner: {research_data.get('owner_name', 'N/A')}\n\n"
        f"*Review before sending to lead:*\n"
        f"- Verify site looks correct\n"
        f"- Add real reviews if found manually\n"
        f"- Confirm business info accuracy\n"
        f"- Add images from their site if available"
    )
    send_telegram(message)
```

---

## Human Review Before Sending (Important!)

The auto-builder creates the site, but you review it before replying to the lead. Checklist:

- Verify the site looks correct and loads properly
- Add any real reviews found manually from Google, Yelp, BBB, etc.
- Confirm business info is accurate (phone, address, services)
- Add images if available from their existing site
- Customize headline/copy if needed for this specific business
- THEN reply to the lead with the URL

Never send a site URL to a lead without reviewing it first.

---

## Deduplication and State Tracking

Processed leads are tracked in `sitesprint_processed.json` to prevent re-processing the same reply:

```json
{
  "processed": [
    {
      "reply_id": "abc123",
      "email": "owner@business.com",
      "company_name": "Joe's Plumbing",
      "classification": "INTERESTED",
      "site_url": "https://joes-plumbing-austin.vercel.app",
      "processed_at": "2025-03-28T14:30:00Z",
      "campaign_id": 3099885
    }
  ],
  "last_poll": "2025-03-28T15:00:00Z"
}
```

On each run, the script loads this file, checks each reply ID against the `processed` array, and skips any already-handled replies.

---

## The Main Script: sitesprint_auto.py

```python
#!/usr/bin/env python3
"""
SiteSprint Auto-Builder
Monitors SmartLead campaigns for interested replies and auto-builds sites.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
LOG_FILE = os.path.expanduser("~/Desktop/SiteSprint/sitesprint_auto.log")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

PROCESSED_FILE = "sitesprint_processed.json"

def load_processed():
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE) as f:
            return json.load(f)
    return {"processed": [], "last_poll": None}

def save_processed(data):
    data["last_poll"] = datetime.utcnow().isoformat() + "Z"
    with open(PROCESSED_FILE, "w") as f:
        json.dump(data, f, indent=2)

def main():
    logging.info("SiteSprint Auto-Builder starting...")

    processed = load_processed()
    processed_ids = {p["reply_id"] for p in processed["processed"]}

    # Stage 1: Fetch new replies
    replies = fetch_new_replies()
    new_replies = [r for r in replies if r["id"] not in processed_ids]
    logging.info(f"Found {len(new_replies)} new replies")

    for reply in new_replies:
        try:
            # Stage 2: Classify
            classification = classify_reply(reply["text"])
            logging.info(f"{reply['company_name']}: {classification}")

            if classification not in ("INTERESTED", "MEETING_REQUEST"):
                processed["processed"].append({
                    "reply_id": reply["id"],
                    "email": reply["email"],
                    "company_name": reply["company_name"],
                    "classification": classification,
                    "site_url": None,
                    "processed_at": datetime.utcnow().isoformat() + "Z",
                    "campaign_id": reply["campaign_id"]
                })
                save_processed(processed)
                continue

            # Stage 3: Alert
            send_telegram(
                f"*New interested lead detected*\n"
                f"Company: {reply['company_name']}\n"
                f"Auto-building site now..."
            )

            # Stage 4: Research
            research = research_company(reply)

            # Stage 5: Build
            site_dir, slug = build_site(research)

            # Stage 6: Deploy
            live_url = deploy_site(site_dir, slug)

            # Stage 7: Notify
            notify_completion(reply, research, live_url)

            # Track as processed
            processed["processed"].append({
                "reply_id": reply["id"],
                "email": reply["email"],
                "company_name": reply["company_name"],
                "classification": classification,
                "site_url": live_url,
                "processed_at": datetime.utcnow().isoformat() + "Z",
                "campaign_id": reply["campaign_id"]
            })
            save_processed(processed)

            logging.info(f"SUCCESS: {reply['company_name']} -> {live_url}")

        except Exception as e:
            logging.error(f"FAILED: {reply['company_name']} - {str(e)}")
            send_telegram(f"*Auto-build FAILED*\nCompany: {reply['company_name']}\nError: {str(e)}")

    logging.info("SiteSprint Auto-Builder complete.")

if __name__ == "__main__":
    main()
```

---

## Scheduling with macOS LaunchAgent

The script runs every 30 minutes (1800 seconds) via a macOS LaunchAgent.

### LaunchAgent Plist

Save to `~/Library/LaunchAgents/com.sitesprint.autobuilder.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.sitesprint.autobuilder</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/alexanderkamel/Desktop/SiteSprint/sitesprint_auto.py</string>
    </array>
    <key>StartInterval</key>
    <integer>1800</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/alexanderkamel/Desktop/SiteSprint/sitesprint_auto.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/alexanderkamel/Desktop/SiteSprint/sitesprint_auto.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
    </dict>
    <key>WorkingDirectory</key>
    <string>/Users/alexanderkamel/Desktop/SiteSprint</string>
</dict>
</plist>
```

### Load the LaunchAgent

```bash
# Load (starts immediately and runs every 30 minutes)
launchctl load ~/Library/LaunchAgents/com.sitesprint.autobuilder.plist

# Unload (stop the schedule)
launchctl unload ~/Library/LaunchAgents/com.sitesprint.autobuilder.plist

# Check status
launchctl list | grep sitesprint
```

---

## Build Instructions (Step by Step)

1. **Create the project directory:**
   ```bash
   mkdir -p ~/Desktop/SiteSprint
   cd ~/Desktop/SiteSprint
   ```

2. **Set up environment variables** in your shell profile (`~/.zshrc`):
   ```bash
   export SMARTLEAD_API_KEY="your_key"
   export ANTHROPIC_API_KEY="your_key"
   export VERCEL_TOKEN="your_token"
   export TELEGRAM_BOT_TOKEN="your_bot_token"
   export TELEGRAM_CHAT_ID="5915551069"
   ```

3. **Install Python dependencies:**
   ```bash
   pip3 install requests anthropic
   ```

4. **Ensure the premium-v2 template exists** at `templates/premium-v2/` with the full Next.js 14 + Tailwind + Framer Motion setup.

5. **Create the `sitesprint_auto.py` script** with all the functions from the stages above (fetch_new_replies, classify_reply, send_telegram, research_company, build_site, deploy_site, notify_completion, main).

6. **Initialize the processed leads tracker:**
   ```bash
   echo '{"processed": [], "last_poll": null}' > sitesprint_processed.json
   ```

7. **Create the `04-sites-built/` directory:**
   ```bash
   mkdir -p 04-sites-built
   ```

8. **Install the LaunchAgent:**
   ```bash
   cp com.sitesprint.autobuilder.plist ~/Library/LaunchAgents/
   launchctl load ~/Library/LaunchAgents/com.sitesprint.autobuilder.plist
   ```

---

## Testing

### 1. Manual trigger

Run the script directly to test without waiting for the 30-minute interval:

```bash
cd ~/Desktop/SiteSprint
python3 sitesprint_auto.py
```

### 2. Verify classification

Test the classifier with sample replies:

```python
# Should return INTERESTED
classify_reply("Yeah that sounds great, I'd love to see it")

# Should return MEETING_REQUEST
classify_reply("Can we hop on a call this week to discuss?")

# Should return NOT_INTERESTED
classify_reply("Please remove me from your list")
```

### 3. Check site builds

After a successful build, verify:
- The site exists in `04-sites-built/[slug]/`
- `site-config.json` contains verified data
- `npm run dev` starts the site locally
- All 4 pages render (Home, Services, About, Contact)
- Dark theme with correct industry accent color
- No fabricated reviews (reviews array should be empty if none were scraped)
- Booking placeholder shows at `/contact#book`
- No links to their old website

### 4. Confirm Telegram notifications

Check that you receive:
- The "auto-building site now" alert immediately after classification
- The "site built and deployed" notification with the live URL after deployment
- Error notifications if any stage fails

### 5. Verify Vercel deployment

- Visit the deployed URL
- Confirm it loads without requiring Vercel login (OIDC disabled)
- Check all 4 pages are accessible
- Verify mobile responsiveness

### 6. Check deduplication

Run the script twice -- the second run should skip all previously processed replies. Check `sitesprint_processed.json` to confirm entries are tracked.

### 7. Check logs

```bash
tail -f ~/Desktop/SiteSprint/sitesprint_auto.log
```

Verify you see entries for each stage: polling, classification, research, build, deploy, notify.

---

## You're Done When...

A lead replies "interested" to your SmartLead campaign, and within 30 minutes you get a Telegram notification with a live Vercel URL of their custom dark-theme website -- built automatically from verified business data. The site has 4 pages, Framer Motion animations, their real business info, no fabricated reviews, and is publicly accessible without a Vercel login wall. You review it, add any manual touches, and reply to the lead with the URL.
