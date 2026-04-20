# FormBlast V1 — Product Requirements Document
## Contact Form Outreach SaaS for SEO Agencies

---

## What It Is

A SaaS tool that automates personalized outreach through business contact forms.
No cold email. No domain warming. No sending limits. No inbox reputation at risk.

The system finds local businesses via Google SERP data, analyzes their competitive
position, assembles a personalized email based on real data, and submits it through
their own contact form. Their server sends the notification. Your email only appears
as the reply-to address.

---

## V1 Target Customer

**Primary:** SEO agencies doing local service business outreach
(plumbers, HVAC, roofers, dentists, lawyers, landscapers...)

**Secondary:** Web design agencies, reputation management agencies
(covered by PageSpeed and Reviews hooks — same tool, different angle)

**Not V1:** Agencies outside these niches, ecomm, enterprise, non-local businesses

---

## The Core Engine (Already Built)

All pipeline scripts exist in `outreach/`:

```
keyword_discovery.py    → generate 3 buyer-intent keywords per niche+city
serp_search.py          → DataForSEO API, pulls top 100 SERP results
build_list.py           → enriches with rankings, assigns tier A/B/C/D
classify_businesses.py  → Haiku flags nationals/directories, skip_outreach column
generate_variants.py    → one-time Claude call, generates 10 email variants per block
assemble_emails.py      → $0/email random assembly with variable substitution
filter.py               → visits each site, finds contact form, detects CAPTCHA
runner.py               → browser-use + Haiku fills and submits the form
run_campaign.py         → single command wraps the full pipeline
```

API keys managed on backend. Users never see or touch them.

---

## Hooks Available at V1 Launch

| Hook | Data Source | Agency Type | Status |
|------|------------|-------------|--------|
| SEO Rankings | DataForSEO | SEO agencies | ✅ Built |
| PageSpeed | Google API (free) | Web design agencies | ✅ Built |
| Reviews | SerpAPI | Reputation mgmt | 🔨 Next |
| Ad Spend | SpyFu | PPC agencies | 📋 Designed |
| Citations | BrightLocal | Local SEO | 📋 Designed |
| Social Presence | Apify | Social media mgmt | 📋 Designed |
| Tech Stack | BuiltWith | Web dev agencies | 📋 Designed |
| Ecomm Traffic | SimilarWeb | Ecomm SEO | 📋 Designed |

V1 ships with SEO Rankings + PageSpeed. Others added as they're built.
Hook logic lives in `outreach/hooks/` — each hook is ~100 lines of Python.

---

## Pages

### 1. Dashboard
- Stats bar: sent today, replies today, ready in queue, cities covered
- Active campaigns with live status
- Recent replies (linked to reply inbox)
- Pipeline health warning if < 2 days of campaigns queued

### 2. Campaigns (list)
- All campaigns: active, queued, completed, paused
- Columns: niche, city, hook used, sent/total, replies, status
- Quick actions: pause, resume, view detail

### 3. Campaign Detail
- Live status + progress bar
- Tier breakdown (A/B/C/D count + bar chart)
- Business list table: domain, tier, send status, reply indicator
- View assembled email per business (click row)
- Reply thread if reply received

### 4. New Campaign (wizard)

**Step 1 — Choose Hook**
- Card grid showing available hooks
- Each card shows: what data it pulls, what angle it uses, sample subject line
- Select one (or Multi-Hook for power mode)

**Step 2 — Target**
- Niche input (with autocomplete from known niches)
- City + State
- Reply-to email
- Estimated targets shown live

**Step 3 — Preview**
- Tier breakdown of found businesses
- Sample email per tier (assembled from real data)
- Flagged businesses (nationals, no-form, CAPTCHA) shown separately

**Step 4 — Schedule**
- Run now / schedule for specific time
- Save as draft option
- Confirm send count + estimated cost shown

### 5. Pipeline Planner
- Calendar view of scheduled campaigns
- Daily send volume chart (actual + projected)
- Alert if pipeline runs dry within 2 days
- Quick-add from draft campaigns
- Sequence status: touch 1 / touch 2 / touch 3 per business

### 6. Drafts
- Saved campaigns not yet launched
- All setup done, just waiting to be activated
- Sort by niche, city, hook, created date

### 7. Email Studio
- Template editor per hook per tier (A/B/C/D)
- Spintax displayed inline: `[word ▾]` colored brackets
- Click any bracketed word → popover shows all 10 variants
- Variable references shown in different color: `{business_name}`, `{kw1_rank}`
- Spin Checker sidebar: counts spin blocks, warns if below minimum
- Link inserter: add landing page URL to message body
- Preview assembled email with real data
- Regenerate variants button (calls Claude, ~$0.05)

**Spintax minimum standard:**
- Subject line: at least 1 spin block
- Body: at least 4 spin blocks across opener/hook/pain/pitch/CTA
- Checker turns green when threshold met

### 8. Analytics
- Reply rate by tier (A/B/C/D)
- Reply rate by hook type
- Reply rate by niche
- Reply rate by city size
- Top performing subject lines (ranked)
- Multi-touch performance: touch 1 vs 2 vs 3 reply rates
- Best time of day / day of week (based on submission time vs reply time)

### 9. Settings
- **Sender details:** name, reply-to email
- **Sending behavior:** delay range (min/max seconds), daily send limit, CAPTCHA handling (skip V1 / attempt V2)
- **Multi-touch sequences:** enable/disable, touch 2 delay (days), touch 3 delay (days)
- **Alerts:** push notification and/or email for: pipeline low, campaign done, new reply
- **Alert threshold:** pipeline low warning at X days remaining

No API key section. All managed on backend.

---

## Multi-Touch Sequences

Contact forms don't thread — but you can go back.

```
Touch 1: SEO Rankings angle    (day 0)
Touch 2: PageSpeed angle       (day 4 — different hook, different email)
Touch 3: Reviews angle         (day 9 — final attempt)
```

System tracks which businesses received each touch.
Schedules follow-ups automatically based on settings.
Each touch uses a different hook = completely different angle = not repetitive.

---

## Top Bar (persistent across all pages)

```
Logo | ● Plumbers/Austin · 18/31 · 4 replies [View] [■Pause] | 🔔 👤 [+New]
```

Always shows active campaign status. Click anywhere to go to campaign detail.
Notification bell for replies + alerts.

---

## Mobile

Responsive web app first. All pages work on mobile.
Push notifications via browser (PWA) for:
- New reply received
- Campaign completed
- Pipeline running low

Native mobile app is V1.5 after web is validated.

---

## Pricing (V1)

| Plan | Price | Campaigns/mo | Hooks | Multi-touch |
|------|-------|-------------|-------|-------------|
| Starter | $49/mo | 5 cities | SEO only | No |
| Pro | $97/mo | 20 cities | All active hooks | Yes |
| Agency | $197/mo | Unlimited | All hooks + priority queue | Yes |

All plans: managed API keys, no setup, no config.

---

## Tech Stack

**Frontend:** React (existing boilerplate)
**Backend:** FastAPI (existing server)
**Queue:** Redis + Celery (campaign job queue)
**Pipeline:** Python scripts in `outreach/` called as functions
**Database:** Convex (existing boilerplate)
**Auth + Billing:** existing boilerplate

---

## What's Left to Build

1. Frontend pages (all 9 pages above)
2. API endpoints wrapping the pipeline scripts
3. Job queue (Celery + Redis) for async campaign runs
4. Reply tracking (IMAP polling on reply-to inbox)
5. Multi-touch scheduler
6. Hooks: Reviews, Citations (2 more to get to 4 active at launch)
