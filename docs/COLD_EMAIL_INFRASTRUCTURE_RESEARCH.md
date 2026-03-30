# Cold Email Infrastructure Research Report
## For Automated SEO Report Delivery System
### Compiled March 28, 2026

---

# SECTION 1: INSTANTLY.IO API & PLATFORM

## API Availability
- **Yes, Instantly has a full REST API**
- Docs: https://developer.instantly.ai/
- You can programmatically: create campaigns, add leads with custom fields, trigger sends, upload templates with dynamic variables

## Dynamic Variables
- Instantly supports custom variables like `{{first_name}}`, `{{company_name}}`, `{{custom_field_1}}`
- You can pass ANY custom field when uploading leads via API
- This means you can insert `{{competitor_name}}`, `{{ranking}}`, `{{dollar_amount}}` etc.
- SpinTax is supported in templates: `{Hey|Hi|Hello}`

## How Emails Get Into Accounts (Your Core Question)
**The flow works like this:**
1. You connect your Gmail/Workspace accounts to Instantly via OAuth
2. You upload leads (email addresses + custom fields) via API or CSV
3. You create email templates with dynamic variables
4. Instantly sends FROM your connected Gmail accounts TO the leads
5. Instantly handles scheduling, rotation across mailboxes, warm-up

**You do NOT manually compose emails in Gmail.** Instantly does it all through the OAuth connection. The emails go out through your Gmail accounts but are composed and sent by Instantly's system.

**For AI-customized emails:** You generate the custom content BEFORE uploading to Instantly. Your workflow:
1. AI generates unique email body per prospect → stores in a custom field
2. Upload prospect + custom email body to Instantly via API
3. Template just uses `{{custom_email_body}}` as the variable
4. Instantly sends it from your connected Gmail accounts

## Pricing
- **Growth:** $30/mo — 1,000 active contacts, 5,000 emails/mo, unlimited accounts
- **Hypergrowth:** $77.6/mo — 25,000 active contacts, 75,000 emails/mo
- **Light Speed:** $286.3/mo — 500,000 active contacts, unlimited emails
- All plans: unlimited email accounts connected

## Warm-Up
- **Included free** on all plans
- Automatic — just toggle it on per account
- Takes ~14 days minimum, 3-4 weeks ideal
- Ramp: starts at 3-5/day, builds to your target over 2-3 weeks

## Plain Text vs HTML
- Can send both
- Best practice per LeadGenJay: **first email plain text only**
- Follow-ups can include links (YouTube, Loom)

---

# SECTION 2: GOOGLE WORKSPACE FOR COLD EMAIL

## Sending Limits
- **Google Workspace:** 2,000 emails/day per user (official limit)
- **Free Gmail:** 500 emails/day
- **Practical cold email limit:** 20-50/day per mailbox to maintain deliverability
- **LeadGenJay recommendation:** 10-15/day per mailbox (his survived the bans)

## Cost Per Account
| Source | Price |
|--------|-------|
| Direct from Google | $7-8.40/user/month |
| Authorized Reseller | $2.99-4/user/month |

**Reseller accounts are the SAME Google product**, just cheaper with value-added services (automated DNS, deliverability support). LeadGenJay's Inbox Insiders uses this model.

## Multiple Accounts Per Domain
- One Workspace can have up to 600 domains (1 primary + 599 secondary)
- Standard practice: buy separate domains (yourbrand-mail.com, yourbrand-hq.com)
- 3-5 sending accounts per domain

## Google Reseller vs Legacy Panels
| | Google Reseller | Legacy Panels |
|--|----------------|---------------|
| **Cost** | $3-8/user/month | One-time purchase ($2-5K) |
| **Risk** | Low-Medium | HIGH (Google banning these) |
| **Monthly fees** | Yes | No |
| **Deliverability** | Excellent | Good but declining |
| **Recommendation** | YES — use these | AVOID for new setups |

## What Google Changed (November 2025)
- Messages failing SPF/DKIM/DMARC now **REJECTED** (not just spam-foldered)
- Spam complaint rate must stay below **0.3%**
- Bounce rate must stay below **2%**
- DMARC policy must be `p=quarantine` or `p=reject` (p=none no longer accepted)
- Google retired old Postmaster Tools, launched v2 with binary pass/fail

## OAuth (Instantly) vs Gmail Web App
| | OAuth via Instantly | Gmail Web App |
|--|-------------------|---------------|
| **Sending method** | IMAP connection | Native Gmail interface |
| **Deliverability** | Good | Slightly better (no fingerprints) |
| **Scalability** | Easy (hundreds of accounts) | Hard (need proxies + anti-detect browser per account) |
| **Automation** | Built-in | Requires browser automation |
| **Cost** | Instantly subscription | VPS + proxies + anti-detect browser |

**LeadGenJay's finding:** Same mailbox, same copy — Gmail web app hits inbox EVERY TIME while Instantly/OAuth sometimes doesn't. But Gmail web app automation is much harder to scale.

---

# SECTION 3: EMAIL WARM-UP

## Services
- **Instantly** — warm-up included free, automatic
- **Mailreach** — dedicated warm-up service, private pools
- **Email Bison** — invite-only, cleanest warm-up pool
- **Warmup Inbox** — standalone service

## Timeline
- **Minimum:** 14 days before sending cold emails
- **Ideal:** 3-4 weeks for strong trust
- **Ramp schedule:** Start 3-5 emails/day → increase gradually → reach 40-50/day over 2-3 weeks

## Warm-Up Pool Quality (Critical)
- Bad warm-up pools = destroyed mailboxes
- **Instantly:** Good — kicks out bad actors
- **Email Bison:** Best — invite-only, vetted senders
- **Newer platforms:** HIGH RISK — avoid unless pool quality is proven

---

# SECTION 4: PROXIES FOR COLD EMAIL

## Do You Need Proxies?
- **If using Instantly (OAuth):** NO — Instantly handles the connection. Your Gmail accounts send through Google's servers.
- **If doing browser automation (Gmail web app):** YES — one residential proxy per Gmail account, plus anti-detect browser
- **If managing 10+ Gmail accounts manually:** YES — Google links accounts by IP

## Proxy Types for Email
| Type | Use Case | Price |
|------|----------|-------|
| **Static Residential (ISP)** | Best for email — consistent IP per account | $2-5/IP/month |
| **Sticky Residential** | Good — same IP for 30-60 min sessions | $3-15/GB |
| **Rotating Residential** | BAD for email — IP changes too often | $3-15/GB |
| **Datacenter** | BAD — Google detects and blocks these | $0.50/IP |

**For email: use STATIC RESIDENTIAL or STICKY (30-60 min minimum).** Never rotating, never datacenter.

## Proxy Providers (Cold Email Industry)
| Provider | Pool Size | Starting Price |
|----------|-----------|---------------|
| Smartproxy | 65M+ IPs | ~$3.50/GB |
| Oxylabs | 100M+ IPs | $8/GB |
| NodeMaven | Smaller | Varies — built for Gmail |
| IPRoyal | 5.5M+ | $1.75/GB (sticky) |
| Bright Data | Largest | Premium pricing |
| Infatica | — | $4/GB pay-as-you-go |

## Cost Estimate (10 Gmail accounts with proxies)
- Static residential: ~$20-50/month for 10 dedicated IPs
- Bandwidth cost is minimal (text emails use almost no data)

## Anti-Detect Browsers (Required for Browser Automation)
- **Multilogin** — most popular, $99+/mo
- **GoLogin** — budget option, ~$49/mo
- **AdsPower** — mid-range
- **Dolphin Anty** — popular in email community
- Each creates unique browser fingerprint per Gmail account

## Email Bison's Model (NOT Standard Proxies)
- Single-tenant infrastructure — dedicated IPs per customer
- Custom SMTP/IMAP servers (not Gmail)
- Private warm-up pool (not shared)
- Automated DNS setup
- Invite-only, quote-based pricing

---

# SECTION 5: ANTHROPIC COMPUTER USE

## Can It Send Emails Through Gmail Web App?
**Technically yes, practically expensive and unreliable.**

## API vs Subscription
| | API Computer Use | Claude Cowork | Claude in Chrome |
|--|-----------------|---------------|-----------------|
| **Access** | API key only | Pro/Max subscription | Max/Team/Enterprise subscription |
| **Cost** | Per-token ($3-15/MTok) | Included in plan | Included in plan |
| **Scale** | Programmable, can loop | Interactive only | Interactive only |
| **Gmail automation** | Possible but expensive | Possible but manual | Possible but manual |

## Computer Use API — Can It Do This?
- Navigate to Gmail: **YES**
- Fill in To/Subject/Body fields: **YES**
- Click Send: **YES**
- Handle CAPTCHAs: **NO**
- Scale to 1000 emails/day: **EXTREMELY EXPENSIVE**

## Cost Estimate: 1000 Emails/Day via Computer Use API

| Scenario | Per Email | Daily (1000) | Monthly |
|----------|----------|-------------|---------|
| Best case (Sonnet, no retries) | $0.06 | $60 | $1,800 |
| Realistic (retries, varied) | $0.15-0.30 | $150-300 | $4,500-9,000 |

**Compare to Instantly:** ~$30-77/month for unlimited emails. Computer use is 50-100x more expensive.

## Claude Cowork (Desktop Agent)
- Launched January 2026
- Included in Pro ($20/mo) and Max ($200/mo) subscriptions
- Controls your desktop — clicks, types, navigates apps
- Available on macOS and Windows
- **NOT designed for scale** — it's an interactive assistant, not a batch processor
- Could send a few emails manually but not 1000/day

## VPS Requirements for Computer Use API
- Linux (Docker container recommended)
- 2+ vCPU, 4GB+ RAM minimum
- Display: 1024x768 to 1280x800 resolution
- **Cheapest VPS:** Hetzner CX22 ~$8-10/month (2 vCPU, 4GB RAM)

## Bottom Line on Computer Use for Email
**Don't use it for bulk email sending.** It's 50-100x more expensive than Instantly and less reliable. Use it only if you need to send <50 emails/day from accounts you can't connect via OAuth.

**Where computer use DOES make sense for your business:**
- Filling out contact forms on agency websites (one-off, not email)
- Small-scale personalized outreach (10-50/day for premium prospects)
- Warm-up monitoring (checking inbox placement manually)

---

# SECTION 6: BROWSER AUTOMATION ALTERNATIVES

## Playwright/Puppeteer for Gmail
- **Can it work?** Yes, technically
- **Will Google block it?** Yes, frequently. Google detects automation via:
  - Headless browser markers
  - WebDriver flags
  - Synthetic input patterns
  - Missing browser fingerprints
- **Mitigation:** Anti-detect browsers + residential proxies
- **Reliability at scale:** LOW — constant maintenance, accounts get locked

## Tools for Multi-Account Browser Automation
| Tool | Purpose | Cost |
|------|---------|------|
| Multilogin | Anti-detect browser profiles | $99+/mo |
| GoLogin | Budget anti-detect browser | ~$49/mo |
| Browserless.io | Managed headless browsers | Usage-based |
| Browserbase | Cloud browser for AI agents | Usage-based |

## VPS Pricing for 24/7 Browser Automation
| Provider | Spec | Price |
|----------|------|-------|
| Hetzner CX22 | 2 vCPU, 4GB RAM | ~$8-10/mo |
| Hetzner CX11 | 1 vCPU, 2GB RAM | ~$4-5/mo |
| DigitalOcean | 2 vCPU, 4GB RAM | $24/mo |

**Hetzner is ~60% cheaper** than DigitalOcean for comparable specs.

---

# SECTION 7: DATAFORSEO API

## Google Maps Endpoint
- **Results per query:** Up to 100 (default), configurable up to 700
- **Data returned per business:** name, address, phone, website, rating (with star breakdown), hours, categories, photos, coordinates, place_id, is_claimed, rank position
- **Location targeting:** City+State text, location code, or GPS coordinates (7 decimal places)

## Local Pack vs Maps
- **Local Pack:** The 3-business box in regular Google Search — returns ~3-10 results
- **Maps:** Full Google Maps search — returns up to 100-700 results
- **Use Maps** for comprehensive competitor analysis

## Keywords Data API
- **Batch up to 1,000 keywords per task**
- **Up to 100 tasks per POST request** (100,000 keywords in one call)
- Returns: search volume, monthly trends, competition, CPC bid ranges

## Google Business Profile Endpoint
- **YES** — `/v3/business_data/google/my_business_info/`
- Query by business name, place_id, or cid
- Returns full business profile data

## Pricing
| Endpoint | Standard (~5 min) | Live (~6 sec) |
|----------|-------------------|---------------|
| Google Maps SERP | $0.0006/page | $0.002/page |
| Google Local Pack | $0.0006/page | $0.002/page |
| Keywords Data | $0.001/task + $0.0001/keyword | Same |

**10,000 Maps queries:** $6 (standard) or $20 (live). Very cheap.

**Minimum deposit:** $50. Free trial: $1 credit.

## Limitation
- Ranking data and keyword volume data come from SEPARATE endpoints
- You call both and merge by keyword on your end

---

# SECTION 8: DYNAMIC LANDING PAGES FOR REPORTS

## Simplest Approach
One HTML template + URL parameter: `yoursite.com/report?id=abc123`
Page loads → reads ID → fetches data from database → renders report.

## Platform Comparison
| Option | Difficulty | Cost (10K pages) | Speed |
|--------|-----------|-----------------|-------|
| **Cloudflare Workers + KV** | 3/10 | $0-5/mo | Fast (edge) |
| **Vercel (Next.js)** | 4/10 | $0-20/mo | Fast |
| **Static Site Generator** | 5/10 | $0-5/mo | Fastest |
| **PHP on shared hosting** | 2/10 | $3-5/mo | Slow |

## Winner: Cloudflare Workers + KV
- Free tier: 100,000 requests/day, 1GB storage
- Paid: $5/month for 10M requests
- 10,000 reports viewed 50x each/month = 500K requests = $5/month
- No bandwidth charges
- Password protection: simple token check in the Worker
- SSL: free

## Storage for Report Data
| Storage | Cost | Best For |
|---------|------|----------|
| Cloudflare KV | Free (<1GB) | Key-value lookups, read-heavy |
| Cloudflare D1 (SQLite) | Free tier: 5M rows/day | Relational queries |
| Supabase (Postgres) | Free: 500MB | Full SQL + auth |
| JSON on R2/S3 | ~$0.015/GB/mo | Static data |

**Recommendation:** Cloudflare KV. Each report = JSON blob stored by business ID.

## Total Hosting Cost Estimate
| Component | Monthly Cost |
|-----------|-------------|
| Cloudflare Workers | $0-5 |
| Cloudflare KV | $0 |
| Custom domain | $0 |
| SSL | $0 |
| **Total** | **$0-5/month** |

---

# SECTION 9: OPTIONS ANALYSIS — HOW TO SEND 1000 CUSTOM EMAILS/DAY

## Option A: Instantly API + AI Pre-Generation (RECOMMENDED)
**How it works:**
1. N8N or Python script generates unique email per prospect using AI (Claude/GPT)
2. Upload prospects + custom email body to Instantly via API
3. Instantly sends from your connected Google Workspace accounts
4. Instantly handles warm-up, scheduling, rotation, bounce protection

| Factor | Rating |
|--------|--------|
| Cost | $30-77/mo (Instantly) + $3-8/mailbox/mo (Google) + AI generation costs |
| Reliability | HIGH |
| Scale | 1000+/day easy (50 mailboxes × 20/day) |
| Setup difficulty | 3/10 |
| Risk | MEDIUM (OAuth fingerprint, Google can crack down) |

**Mailbox math:** 1000 emails/day ÷ 20 per mailbox = **50 Google Workspace accounts needed**
- At reseller pricing ($3-4/ea): **$150-200/month for mailboxes**
- Total: ~$250-350/month for 1000 emails/day

## Option B: Email Bison + AI Pre-Generation (PREMIUM)
**How it works:**
Same as Option A but using Email Bison instead of Instantly. Custom SMTP servers, no OAuth fingerprint, private warm-up pool.

| Factor | Rating |
|--------|--------|
| Cost | Higher (quote-based, ~2x Instantly) |
| Reliability | HIGHEST |
| Scale | 1000+/day |
| Setup difficulty | 2/10 (they handle everything) |
| Risk | LOW (no Google/Microsoft dependency) |

**Limitation:** Invite-only. Must apply and qualify.

## Option C: Browser Automation (Gmail Web App)
**How it works:**
1. Load Gmail accounts in anti-detect browser (Multilogin/GoLogin)
2. Each account gets its own residential proxy
3. Playwright/Puppeteer script logs in and sends emails through Gmail UI
4. Zero OAuth fingerprint

| Factor | Rating |
|--------|--------|
| Cost | $49-99/mo (anti-detect) + $20-50/mo (proxies) + $8-10/mo (VPS) |
| Reliability | LOW (Google blocks bots, constant maintenance) |
| Scale | Hard to go past 200-500/day |
| Setup difficulty | 8/10 |
| Risk | HIGH (accounts get locked) |

**This is what LeadGenJay is building for himself.** He acknowledges it's hard to scale and hard to offer as a service. Not recommended as primary method.

## Option D: Computer Use (Claude API) for Small Scale
**How it works:**
1. Claude API computer use navigates to Gmail
2. Composes and sends each email individually
3. Each session costs $0.06-0.30

| Factor | Rating |
|--------|--------|
| Cost | $1,800-9,000/mo for 1000/day |
| Reliability | LOW-MEDIUM (beta, can misclick) |
| Scale | Technically unlimited but prohibitively expensive |
| Setup difficulty | 6/10 |
| Risk | MEDIUM |

**Only makes sense for:** <50 emails/day to ultra-premium prospects where $0.30/email is justified by deal size.

## Option E: Computer Use (Cowork/Subscription) for Agencies Without Infrastructure
**How it works:**
1. Agency subscribes to Claude Max ($200/mo)
2. Cowork opens Gmail, composes personalized emails one at a time
3. Human monitors and approves

| Factor | Rating |
|--------|--------|
| Cost | $200/mo (subscription) |
| Reliability | MEDIUM |
| Scale | 50-100/day MAX (interactive, not batch) |
| Setup difficulty | 2/10 |
| Risk | LOW |

**Good for:** New agencies doing 50-100 cold emails/day who want personalization without infrastructure. Your SaaS generates the custom email content → they paste it into Cowork → Cowork sends through their Gmail.

## Option F: SMTP Direct (SendGrid/Amazon SES)
**How it works:**
1. Send directly via SMTP API
2. Your own domains, your own IPs
3. Cheapest per-email cost

| Factor | Rating |
|--------|--------|
| Cost | $1-20/mo for 1000/day |
| Reliability | HIGH (if warmed properly) |
| Scale | Unlimited |
| Setup difficulty | 5/10 |
| Risk | MEDIUM (IP reputation management is on you) |

**Limitation:** No warm-up service, no hostile prospect filtering, no spam trap avoidance. You manage everything yourself.

---

# SECTION 10: RECOMMENDED SETUP FOR YOUR BUSINESS

## For Your Agency Tool (1000+ emails/day)
**Use Option A: Instantly API + AI Pre-Generation**

```
YOUR TOOL (generates custom SEO report email per prospect)
    ↓
N8N / Python script (calls AI to personalize email copy)
    ↓
Instantly API (uploads prospects + custom email body)
    ↓
50+ Google Workspace accounts (connected via OAuth)
    ↓
Prospect's inbox
```

**Monthly cost:** ~$250-350/month for 1000 emails/day
**Setup time:** 1-2 weeks (account creation + warm-up)

## For New Agency Clients (Small Scale, No Infrastructure)
**Use Option E: Your Tool + Manual/Cowork Sending**

```
YOUR TOOL (generates custom SEO report email)
    ↓
Agency copies email into Gmail (manually or via Cowork)
    ↓
Prospect's inbox
```

**Monthly cost:** $0-200/month
**Scale:** 50-100 emails/day
**Advantage:** No infrastructure setup needed. Agency starts immediately.

## For Premium Clients (Budget Available)
**Use Option B: Email Bison**
- Apply for access
- Highest deliverability, lowest risk
- They handle everything

---

# SECTION 11: SDK/SUBSCRIPTION ANSWERS (QUICK REFERENCE)

| Question | Answer |
|----------|--------|
| Can computer use run on Max subscription? | NO — API credits only for programmatic computer use |
| Can Claude Cowork send emails? | YES — but interactive only, not batch. Included in Pro/Max |
| Can Claude in Chrome send emails? | YES — but interactive only. Included in Max |
| Can you build your own computer use with SDK? | YES — API computer use tool is programmable, but costs per-token |
| Is there a subscription option for batch email automation? | NO — batch automation requires API credits |
| Can Claude Code SDK do computer use? | NO — Claude Code uses bash/file tools, not screenshot/mouse |

---

# LINKS & SOURCES

- Instantly API docs: https://developer.instantly.ai/
- Instantly pricing: https://instantly.ai/pricing
- Google Workspace pricing: https://workspace.google.com/pricing
- Google Workspace sending limits: https://support.google.com/a/answer/166852
- Anthropic Computer Use: https://docs.anthropic.com/en/docs/agents-and-tools/computer-use
- Anthropic Pricing: https://docs.anthropic.com/en/docs/about-claude/pricing
- Claude Cowork: https://www.anthropic.com/product/claude-cowork
- DataForSEO docs: https://docs.dataforseo.com/v3/
- DataForSEO pricing: https://dataforseo.com/pricing
- Cloudflare Workers pricing: https://developers.cloudflare.com/workers/platform/pricing/
- MXToolbox blacklist check: https://mxtoolbox.com/blacklists.aspx
- LeadGenJay Inbox Insiders: https://leadgenjay.com/inbox
