# PRD: Cold Email Engine — 4 Components
## Descriptive PRD for AutoForge Build Pipeline

---

# OVERVIEW

Build a cold email sending system that works with Gmail SMTP (app passwords) to send AI-personalized emails without the OAuth fingerprint that platforms like Instantly leave. Four components, each independently buildable and testable.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                YOUR PROPRIETARY SAAS                 │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐                 │
│  │ Component 1  │  │ Component 2  │                 │
│  │ SMTP Rotator │  │ Warm-Up      │                 │
│  │ + Pacing     │  │ Engine       │                 │
│  └──────┬───────┘  └──────┬───────┘                 │
│         │                  │                         │
│  ┌──────┴───────┐  ┌──────┴───────┐                 │
│  │ Component 3  │  │ Component 4  │                 │
│  │ AI Email     │  │ SEO Report   │                 │
│  │ Personalizer │  │ Engine       │                 │
│  └──────┬───────┘  └──────┬───────┘                 │
│         │                  │                         │
│         └────────┬─────────┘                         │
│                  │                                   │
│            API BOUNDARY                              │
│                  │                                   │
│    ┌─────────────┴──────────────┐                    │
│    │    External Services       │                    │
│    │  Listmonk (AGPL, unmod)   │                    │
│    │  check-if-email-exists    │                    │
│    │  Postal (MIT)             │                    │
│    │  Cloudflare Workers       │                    │
│    └────────────────────────────┘                    │
└─────────────────────────────────────────────────────┘
```

## License Strategy
- Components 1-4: Proprietary (your code, your IP)
- Listmonk: AGPL, run as separate Docker container, unmodified, accessed via API only
- check-if-email-exists: AGPL, run as separate service, unmodified, accessed via API only
- Postal: MIT, no license concerns whatsoever
- All API boundaries maintained — no license contamination

---

# COMPONENT 1: Gmail SMTP Rotation + Pacing Engine

## What It Is
A Python service that manages multiple Gmail accounts and sends emails through them via SMTP (app passwords), rotating across accounts, pacing sends to look human, and tracking per-account daily limits.

## What It Does

### Account Registry
- Stores Gmail accounts with their app passwords (encrypted at rest)
- Tracks per-account state: emails sent today, last send time, daily limit, warm-up status, health score
- Supports adding/removing accounts without restart
- Groups accounts by domain (for domain-level limit tracking)

### Send Queue
- Accepts email jobs: recipient, subject, body (plain text), from-account preference (optional)
- Queues jobs in SQLite or Postgres
- Prioritizes by: account availability, time since last send, daily remaining quota

### Rotation Logic
- Round-robin across available accounts
- Skips accounts that have hit daily limit
- Skips accounts flagged as unhealthy (bouncing, throttled)
- Weighted rotation: accounts with more remaining daily quota get more sends
- Never sends two emails from the same account within a configurable minimum gap (default: 60-120 seconds, randomized)

### Pacing Engine
- Human-like send timing: random delays between 30-180 seconds between sends
- Gaussian distribution (most sends at 60-90 sec gap, occasional fast/slow)
- Configurable daily schedule: sends during business hours only (9am-6pm recipient timezone)
- Ramp-up mode for new accounts: starts at 3/day, increases by 2-3/day automatically
- Weekend reduction: optionally sends 50% less on weekends

### SMTP Connection Management
- Connection pooling: keeps SMTP connections alive to reduce handshake overhead
- Auto-reconnect on dropped connections
- TLS enforcement (port 587 STARTTLS or 465 SSL)
- Timeout handling: 30-second connect timeout, 60-second send timeout
- Error classification: temporary failure (retry) vs permanent failure (mark bad)

### Monitoring
- Per-account dashboard: sent today, remaining, health status, last error
- Per-domain dashboard: aggregate stats
- Alert on: account hitting Google throttle, unusual bounce rate, SMTP auth failure
- Daily summary: total sent, total bounced, total complaints, accounts used

### IMAP Inbox Monitor (runs in parallel)
- Connects to each sending account's inbox via IMAP
- Scans for bounce-back notifications (subjects containing "Undeliverable", "Delivery Failed", "Returned mail")
- Scans for complaint replies (keywords: "stop", "unsubscribe", "remove", "not interested", profanity)
- Auto-adds bounced addresses to suppression list
- Auto-adds complaint senders to blacklist
- Logs all inbound replies for manual review (potential leads)

## Technical Decisions
- **Language:** Python 3.11+
- **SMTP:** Built-in `smtplib` + `email.mime` (no external dependency needed)
- **IMAP:** Built-in `imaplib` (no external dependency needed)
- **Queue:** SQLite for simplicity, Postgres if scaling past 100 accounts
- **Scheduling:** APScheduler for send timing
- **Config:** YAML or JSON file for account credentials (encrypted)
- **API:** FastAPI endpoints for job submission, account management, stats

## Data Model
```
accounts:
  - email: string
  - app_password: string (encrypted)
  - domain: string
  - daily_limit: int (default 20)
  - sent_today: int
  - last_send_time: datetime
  - health_status: enum (active, paused, throttled, dead)
  - warmup_mode: bool
  - warmup_day: int (days since account creation)
  - created_at: datetime

send_queue:
  - id: int
  - recipient_email: string
  - subject: string
  - body_plain: string
  - from_account: string (optional preference)
  - status: enum (queued, sending, sent, failed, bounced)
  - assigned_account: string
  - send_time: datetime
  - created_at: datetime
  - error_message: string (nullable)

suppression_list:
  - email: string
  - reason: enum (bounced, complained, unsubscribed, spam_trap)
  - added_at: datetime

daily_stats:
  - date: date
  - account_email: string
  - sent: int
  - bounced: int
  - complaints: int
  - replies: int
```

## Estimated Token Count: ~300-400K tokens (1 AutoForge session)

---

# COMPONENT 2: Warm-Up Engine

## What It Is
A Python service that warms up new Gmail accounts by sending/receiving legitimate-looking emails between your own accounts, gradually building sender reputation before cold sending begins.

## What It Does

### Warm-Up Pool
- Maintains a pool of "warm-up partner" accounts (your own Gmail + optionally Outlook/Yahoo accounts)
- Each warm-up account can both send and receive warm-up emails
- Pool should have at minimum 20-30 accounts for variety

### Warm-Up Sequence
- For each new sending account, runs a daily warm-up schedule:
  - Days 1-3: 3-5 warm-up emails/day (send + receive)
  - Days 4-7: 8-12/day
  - Days 8-14: 15-20/day
  - Days 15-21: 20-30/day (start mixing in 5-10 cold sends)
  - Days 22+: Full sending mode, warm-up reduces to 5-10/day maintenance
- Schedule is configurable per account

### Warm-Up Email Content
- Library of 50-100 warm-up email templates (conversational, business, casual)
- Templates rotate so no two warm-up emails are identical
- Subjects and bodies generated from templates with light randomization
- Emails look like real conversations: some are questions, some are replies, some share links
- Thread simulation: some warm-up emails are "replies" to previous warm-up emails (creates realistic threads)

### Warm-Up Reply Automation
- When a warm-up email arrives in an account's inbox:
  1. If it's in spam → move to inbox (trains Gmail that this sender is legitimate)
  2. If it's in inbox → mark as read after a random delay (30-300 seconds)
  3. Optionally "reply" to create a thread (improves engagement signals)
  4. Star some emails (positive engagement signal)

### Health Monitoring
- Track warm-up email delivery: did it arrive in inbox or spam?
- If warm-up emails are going to spam → flag the account, slow down
- Weekly warm-up health report per account
- Auto-pause cold sending if warm-up health drops below threshold

## Technical Decisions
- **Language:** Python 3.11+
- **SMTP/IMAP:** Same as Component 1 (built-in libraries)
- **Template storage:** YAML files or SQLite
- **Scheduling:** APScheduler (same as Component 1)
- **Integration:** Shares account registry with Component 1

## Key Insight
The warm-up engine and the SMTP rotator share the same account registry and SMTP connection logic. They're really two modes of the same system: warm-up mode sends to your own accounts, cold mode sends to prospects. The account state machine is:

```
NEW ACCOUNT → WARMING UP → WARM (ready for cold) → ACTIVE (sending cold + maintenance warm-up)
                                                         │
                                                         ▼
                                                   THROTTLED (too many bounces/complaints)
                                                         │
                                                         ▼
                                                   COOLING DOWN (warm-up only, no cold)
                                                         │
                                                         ▼
                                                   WARM (ready again)
```

## Estimated Token Count: ~250-350K tokens (1 AutoForge session)

---

# COMPONENT 3: AI Email Personalizer

## What It Is
A service that takes prospect data (name, company, industry, competitor info, ranking data) and generates a completely unique email for each prospect using AI.

## What It Does

### Input
- Prospect record with fields: name, email, company, website, industry, city, state
- Competitor data from Component 4 (SEO Report Engine): top competitors, rankings, keyword values
- Email template/prompt: the "formula" for the email (editable by user, NOT hardcoded)

### Processing
1. Takes the prospect data + competitor data
2. Feeds it into an AI prompt (Claude Haiku for cost efficiency, or Sonnet for quality)
3. AI generates a completely unique email body (plain text)
4. Applies quality checks: length (50-150 words), no spam trigger words, has clear CTA
5. Returns the finished email ready for Component 1 to send

### Prompt Management
- Prompts stored in database, editable from UI
- Multiple prompt templates: "aggressive offer", "soft intro", "report delivery", "follow-up"
- A/B testing: randomly assign prospects to different prompt versions
- Track which prompt version gets best response rates

### Cost Control
- Use Haiku 4.5 by default ($1/$5 per MTok) — cheapest option
- ~500-800 tokens per email generation
- Cost: ~$0.003-0.005 per email
- 1000 emails/day = $3-5/day = ~$100-150/month in AI costs
- Option to use Sonnet for premium clients (~10x more expensive but higher quality)

### Batch Processing
- Generate all emails for the day in one batch (not real-time)
- Store generated emails in queue for Component 1 to pick up
- Regenerate option: if email bounces or account changes, regenerate with different AI output

## Technical Decisions
- **Language:** Python 3.11+
- **AI:** Anthropic API (Haiku for cost, Sonnet for quality) or Ollama local (Qwen for free)
- **Prompt storage:** SQLite or Postgres (same DB as other components)
- **Integration:** Feeds directly into Component 1's send queue

## You've Already Figured This Out
This is the simplest component. It's prompt engineering + an API call. The DataForSEO data from Component 4 feeds in, the AI prompt generates the email, Component 1 sends it.

## Estimated Token Count: ~150-200K tokens (combined with Component 4 in 1 session)

---

# COMPONENT 4: SEO Report Engine

## What It Is
A service that pulls local SEO competitor data from DataForSEO, generates a visual report, and hosts it on a dynamic landing page.

## What It Does

### Data Collection (DataForSEO API)
1. Input: prospect's business type + city/state (e.g., "plumber" + "Denver, CO")
2. Call Google Maps SERP API → get top 10-20 competitors in that area
3. Call Keywords Data API → get search volume + CPC for relevant keywords
4. Call Google Business Profile API → get prospect's own profile data
5. Merge: for each keyword, who ranks where, what that position is worth ($)

### Report Generation
1. Take the raw data
2. Calculate dollar values: (monthly search volume × CTR for position × CPC = estimated monthly value)
3. Format into a clean report: "Your competitor ABC ranks #1 for 'plumber denver' — that position is worth $4,200/month"
4. Generate a unique report ID
5. Store report data in Cloudflare KV (or database)

### Landing Page
1. Hosted on Cloudflare Workers
2. URL: `yourdomain.com/report/{unique-id}`
3. Prospect clicks link in email → sees their personalized competitor report
4. Optional: require access code (from the email) to view
5. Report includes: competitor rankings table, dollar values, their position (or absence), CTA to book a call

### Cost per Report
- DataForSEO: ~$0.002-0.006 per business (Maps query + keywords query)
- Cloudflare hosting: $0-5/month for thousands of reports
- Total per report: **less than $0.01**

## Technical Decisions
- **Language:** Python 3.11+ for data collection, JavaScript for Cloudflare Worker
- **DataForSEO:** REST API, JSON responses
- **Storage:** Cloudflare KV for reports (free tier: 1GB)
- **Landing page:** Single Cloudflare Worker template, data injected per report ID
- **Integration:** Feeds competitor data into Component 3 for email personalization

## You've Already Figured This Out Too
DataForSEO API is documented, cheap, and straightforward. The landing page is a single template. The report generation is data formatting. This is the easiest component.

## Estimated Token Count: ~150-200K tokens (combined with Component 3 in 1 session)

---

# BUILD ORDER

| Session | What | Tokens | Time |
|---------|------|--------|------|
| **Session 1** | Component 1: SMTP Rotator + Pacing + IMAP Monitor | ~300-400K | ~30 min |
| **Session 2** | Component 2: Warm-Up Engine + integration with Component 1 | ~250-350K | ~30 min |
| **Session 3** | Components 3+4: AI Personalizer + SEO Report Engine + Cloudflare Worker | ~300-400K | ~30 min |
| **Session 4** | Integration testing + dashboard + Docker compose for AGPL services | ~200-300K | ~30 min |
| **TOTAL** | **Complete cold email engine** | **~1.0-1.5M tokens** | **~2 hours build** |

Plus testing/debugging between sessions. Realistic total: **one afternoon to one day.**

---

# EXTERNAL SERVICES (API KEY IN, NOT YOUR CODE)

These run as separate Docker containers alongside your app. Unmodified. Accessed via API only.

| Service | License | What It Handles | Docker Image |
|---------|---------|----------------|-------------|
| **Listmonk** | AGPL | List management, templates, subscriber tracking | `listmonk/listmonk` |
| **check-if-email-exists** | AGPL | Email verification before sending | `reacherhq/backend` |
| **Postal** | MIT | SMTP delivery backbone (optional — can use Gmail SMTP directly) | `postalserver/postal` |

**Docker Compose:** One file spins up all three services + your app. Agency clients run one command to start everything.

---

# WHAT YOU'RE SELLING

## Tier 1: DIY Tool ($49-99/month)
- Agency gets the report engine + AI email generator
- They copy/paste emails into Gmail manually
- 50-100 emails/day

## Tier 2: Automated Sending ($199-399/month)
- Everything in Tier 1
- SMTP rotation engine sends for them
- Warm-up included
- Bounce/complaint handling
- 200-1000 emails/day

## Tier 3: Full Service ($499-999/month)
- Everything in Tier 2
- You provide the Google Workspace accounts
- You manage domains, DNS, warm-up
- White-glove deliverability monitoring
- 1000-5000 emails/day

---

# SUCCESS METRICS

| Metric | Target |
|--------|--------|
| Gmail inbox rate | >90% |
| Bounce rate | <2% |
| Spam complaint rate | <0.3% |
| Email generation cost | <$0.01/email |
| Warm-up time to full sending | <21 days |
| System uptime | >99% |
| Response rate (with AI personalization) | >8% |
