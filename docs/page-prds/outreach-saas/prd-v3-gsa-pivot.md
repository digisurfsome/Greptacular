# PRD v3 — GSA Pivot Amendment

> **Status:** Amendment to v1 and v2. Does not replace them — modifies the delivery layer and adds persistence/re-messaging architecture.
>
> **Read order:** `README.md` → `prd-v1.md` → `hook-framework.md` → **this doc**. `prd-v2.md` BYOK concepts still valid.
>
> **Source of truth:** On conflict, this doc wins.

---

## Why This Amendment Exists

v1 and v2 assumed delivery happened via a Python `runner.py` script using `browser-use` + Playwright to fill and submit contact forms one at a time. That's slow (1–3 submits/minute), fragile (browser quirks, captcha challenges per submission), and requires us to build/maintain proxy rotation and captcha-solver integration from scratch.

The operator owns **GSA Website Contact**, a mature Windows desktop tool that solves the entire delivery problem for $147 one-time + ~$25/mo in proxies. It does 10–50 submits/minute, handles captcha via integrated solvers, rotates proxies, retries failures. It has worked in production for 15 years.

The pivot: **our Python pipeline stops being a delivery layer and becomes a content-generation layer.** We produce the per-prospect custom message with live SEO/competitor data baked in (the part nobody else does), and GSA handles delivery.

This is an arbitrage: GSA's infrastructure + our custom per-row messages. No competitor combines these two.

---

## One-Paragraph Architecture Summary

```
DataForSEO keyword pull
    ↓
filter.py (contact form discovery, booking-widget skip, already built)
    ↓
Hook module (per-niche: SEO data, PageSpeed, reviews, ...) pulls live data
    ↓
assemble_emails.py (Haiku variants + spintax + placeholder injection)
    ↓
Database (persistent lead bank — every scrape, every hook, every send logged)
    ↓
CSV exporter (GSA-import format)
    ↓
GSA Website Contact (Windows machine — operator or Windows VPS)
    ↓
Replies land in reply-to Gmail → response bot → appointment setter → landing page
```

---

## Change 1 — Delivery Layer Swap

**Old (v1/v2):**
> Step 6 — `runner.py` iterates `ready_to_send.csv`, spawns browser-use agent per row, fills form, submits.

**New (v3):**
> Step 6 — `export_gsa.py` takes `ready_to_send.csv` plus data from the lead database and writes `gsa_import_{campaign}_{timestamp}.csv` in GSA's import schema. Operator imports the file into GSA on their Windows machine. GSA handles submission end-to-end.

### Deleted from scope

- `runner.py` hardening beyond what already works for QA-level testing
- Playwright scale-up for submission
- Proxy rotation infrastructure in Python
- 2captcha integration in Python
- Browser-use retries / error recovery beyond current state
- Any cost-per-send LLM spend for form-filling (runner's Haiku cost)

`runner.py` stays in the repo as a fallback / QA tool. Not the production delivery path.

### Cost model update

| Old line item | v3 change |
|---|---|
| Contact form sends via runner.py: ~$0.45 per 30 sends | **Removed** |
| 2captcha: ~$120/mo at 5k sends/day | **Removed** (GSA operator owns CapMonster) |
| Residential proxies: $100–300/mo | **Replaced** with GSA's ~$25/mo proxy requirement (operator-owned) |
| Haiku per form fill: ~$0.03/send | **Removed**. Haiku is ONLY used for message generation now (~$0.002/row). |
| GSA license: $147 one-time | **Operator-owned, out of SaaS scope** |

Net per 1,000 sends: **~$0.50 in DataForSEO + ~$2 in Haiku generation = ~$2.50 for content, delivered by GSA for free from our side.**

---

## Change 2 — Persistent Database Layer (NEW)

v1/v2 are CSV-only. The operator's real workflow requires re-messaging the same prospect list 10+ times over weeks with different offers. That is impossible without persistence.

### Required Tables (SQLite for pilot, Postgres-ready schema)

```
leads
  id                    PK
  business_name
  website_url
  contact_form_url
  city
  state
  niche
  discovered_at
  first_source          # which campaign found this lead first
  filter_status         # ready / skip_no_form / skip_booking / skip_directory / blocked_cloudflare
  has_contact_form      # boolean
  dedupe_key            # normalized domain — used to prevent re-ingest

seo_data
  lead_id               FK
  keyword
  rank_position
  competitor_top3_json  # array of {name, url, est_traffic_value}
  pulled_at
  hook_module           # 'seo' / 'pagespeed' / 'reviews' / 'voice_bot' / etc.

hooks
  id                    PK
  name                  # e.g. 'seo_competitor_traffic', 'voice_bot_demo'
  description
  niche_fit             # which niches this hook applies to
  data_requirements     # JSON — what live data this hook pulls

offers
  id                    PK
  name                  # e.g. "Tier A SEO hook - March 2026", "Voice bot demo - April 2026"
  hook_id               FK
  message_template      # the spintax template body
  subject_template
  created_at
  active                # boolean

sends
  id                    PK
  lead_id               FK
  offer_id              FK
  sent_at
  delivery_method       # 'gsa' / 'runner' / 'manual'
  gsa_import_batch      # reference to the GSA import CSV filename
  landed                # nullable boolean — set when reply detected or landing confirmed
  replied               # boolean
  replied_at
  response_classification  # 'interested' / 'question' / 'not_interested' / 'ooo' — set by response bot
  appointment_booked    # boolean
  appointment_booked_at
  landing_page_visit_count
  notes

agencies
  id                    PK
  name
  contact_email
  calendly_url
  active
  lead_quota_remaining
  buys_niches           # JSON array — which niches this agency purchases
  price_per_lead

lead_assignments
  lead_id               FK
  agency_id             FK
  assigned_at
  status                # assigned / booked / paid / rejected
  paid_at
```

### Why this schema, in plain English

- **leads** — master list of every business ever scraped. Dedupe by normalized domain. Never re-scrape.
- **seo_data** — scraped SEO/hook data for each lead. One lead can have many rows here (different hooks, different dates).
- **hooks / offers** — a hook is a *category* of angle (SEO, voice bot, PageSpeed); an offer is a *specific campaign* using that hook at a point in time.
- **sends** — every attempt to contact a lead with a specific offer. This is the table that makes re-messaging work — query `leads WHERE id NOT IN (SELECT lead_id FROM sends WHERE offer_id = X)` to find everyone not yet hit with offer X.
- **agencies / lead_assignments** — for the lead-selling business model. Which agency got assigned which lead, booked it, paid for it.

### Dedup rules

- New scrape normalizes `website_url` to domain-only (strip www, strip protocol, lowercase)
- If `dedupe_key` exists in `leads`: update `seo_data` only. Do not insert new lead row.
- If `dedupe_key` absent: insert new lead + new seo_data row.

This is the one rule that makes "same list, 10 offers over weeks" possible.

---

## Change 3 — API Layer / Harness (NEW)

Current Python scripts are CLI-only. Future dashboard UI cannot invoke them directly. Add a thin **FastAPI service layer** that wraps every Python script as an HTTP endpoint, reading and writing to the database above.

### Required endpoints

```
POST /api/discover              — runs keyword pull + filter.py on a niche/city, writes leads + seo_data
POST /api/hook/{hook_name}/run  — runs a hook module over a lead selection, writes seo_data
POST /api/offer/create          — saves a new offer (hook + template)
POST /api/offer/{id}/generate   — runs assemble_emails.py over unsent leads for this offer
POST /api/offer/{id}/export-gsa — writes the GSA-format import CSV
POST /api/sends/record-batch    — marks a batch of sends as submitted after GSA upload
POST /api/sends/{id}/reply      — webhook target for response bot
GET  /api/leads                 — paginated, filterable (city, niche, status, last-contacted-before, etc.)
GET  /api/leads/{id}            — full detail + send history + seo data history
GET  /api/offers                — list offers with performance stats
GET  /api/offers/{id}/stats     — reply rate, landing rate, appointment rate
GET  /api/agencies              — list agencies
POST /api/agencies              — create agency
POST /api/leads/{id}/assign/{agency_id} — assign lead
```

### Why this matters (plain English)

Every piece of the system becomes a URL. The dashboard UI makes web calls to these URLs. The Python scripts don't change — they just get wrapped. When the SaaS is built later, the same URLs serve the paying-customer dashboard. Zero rewrite.

### Stack

- FastAPI (Python) — single file `api_server.py` to start
- SQLite via SQLAlchemy for pilot — schema migrates cleanly to Postgres
- Runs on same Hetzner Linux VPS as filter.py etc.
- Protected by a single bearer token in `.env` for pilot (multi-tenant auth comes later)

---

## Change 4 — GSA CSV Import Spec (NEW)

The export file GSA imports. Column spec:

| Column | Source | Example |
|---|---|---|
| `url` | `leads.contact_form_url` | `https://example-plumber.com/contact` |
| `domain` | extracted from `url` | `example-plumber.com` |
| `first_name` | operator's sender name | `John` |
| `last_name` | operator's sender last name | `Mitchell` |
| `email` | reply-to Gmail | `johnmitchell.seo@gmail.com` |
| `company` | operator's company name | `LeadFlow Media` |
| `phone` | operator's phone (optional) | `555-555-5555` |
| `subject` | generated per-row by `assemble_emails.py` | `Joe's Plumbing is getting $10,400/mo free — you're at #14` |
| `message` | generated per-row by `assemble_emails.py` | Full custom body, 150–300 words, no spintax remnants |
| `website` | operator's landing page URL (with unique `{lead_id}` token) | `https://leads.operator.com/ld/9f3a2b` |
| `captcha_field` | blank — GSA auto-detects | — |
| `comments` | duplicate of `message` (some forms use this field name) | — |

The exporter writes UTF-8 CSV with `"` quoting and comma separators. GSA accepts this as-is.

### One-time GSA project config (documented separately in operator runbook)

- Project name: `{niche}_{city}_{offer_name}`
- Submission engine: standard Website Contact
- Captcha solver: operator-provided (CapMonster or equivalent)
- Proxy list: operator-provided (~$25/mo residential)
- Threads: start at 10, ramp to 50 once stable
- Retry on fail: 2
- Submit speed: conservative (3–5 sec delays) for pilot

---

## Change 5 — Dashboard Addition: Lead Bank Page (NEW)

Adds a 10th page to the v1 dashboard spec (was 9 pages).

### Page: Lead Bank

**Purpose:** searchable/filterable view of every lead ever scraped, with full send + hook history per lead.

**Layout:**
- Top bar: search (business name, domain, city), filters (niche, status, last-contacted-before-date, assigned-agency, has-replied, booked)
- Main table: lead rows with columns — business, domain, city, niche, first discovered, last contacted, total sends, replies, appointment booked, assigned agency
- Row click → detail drawer showing:
  - All SEO/hook data pulled for this lead over time
  - Full send history (offer, date, delivery method, reply status, appointment status)
  - Landing page visits (count + timestamps)
  - Assigned agency + payment status
  - Manual action buttons: "Add to offer X", "Mark as sold", "Exclude from all future sends"

**Bulk actions from filtered view:**
- "Add {N} filtered leads to offer: [dropdown]"
- "Export {N} leads as GSA CSV"
- "Assign {N} leads to agency: [dropdown]"

This is the page that makes the re-messaging strategy operable. Without it, the re-messaging is theoretical.

---

## Change 6 — Multi-Offer Re-Messaging Workflow (NEW)

The operator wants to hit the same lead list with ~10 different offers over weeks. Specify the workflow:

### Create an offer

1. Operator picks a hook (SEO, voice bot, reviews, etc.)
2. Operator writes the message template (or clones an existing offer + edits)
3. Operator names the offer and saves it

### Generate sends for an offer

1. Operator selects an offer + a lead filter (e.g., "all plumbers in Texas, not contacted in last 14 days, has contact form")
2. System runs:
   - For each lead in filter: check `sends` table — has this lead received this offer? If yes, skip. If no, proceed.
   - Pull required hook data (may reuse existing `seo_data` if recent, or refresh)
   - Run `assemble_emails.py` to produce subject + body per row
   - Write to GSA import CSV
   - Pre-create `sends` rows in "pending" state
3. Operator imports CSV into GSA, runs
4. Operator runs `/api/sends/record-batch` with the GSA result file — marks pending sends as "submitted"

### Reply attribution

1. Response bot polls reply-to Gmail
2. On new reply, match sender email → look up which lead it came from via `sends` table
3. Call `/api/sends/{id}/reply` with classification
4. If "interested" → bot sends personalized reply with landing page link
5. Landing page visit tracked via URL token back to `sends.landing_page_visit_count`

### The flywheel

Lead never expires from the bank. Every new offer = new pass over the bank (minus already-contacted-with-this-offer). One scrape of 5,000 plumbers → 10 offers × 5,000 = 50,000 potential sends over 6 months, with one DataForSEO cost.

---

## Change 7 — Voice-Bot Product Variant (NEW, ACKNOWLEDGED)

The operator plans a second offer type: AI voice-receptionist demo built per-business, hosted at a dedicated phone number, pitched via the same GSA delivery pipeline.

**Treated as a new hook module + offer, not a separate product.**

Hook module requirements:
- Pulls business name, hours, services from scraped site or DataForSEO local pack data
- Generates audio recording via TTS with business-specific dialogue
- Stages recording on IVR/cheap phone number service (keep hosted for 30+ days)
- Produces phone number + recording URL for insertion into message template

Offer template says something like:
> "Hey [Business], we built a live AI receptionist for your business. Call [phone] to hear it in action. Drops in 24 hours — here's the recording if you missed it: [recording_url]."

**Not built in pilot.** Ships as second hook after SEO hook pilot proves the pipeline end-to-end.

---

## Change 8 — Pilot Scope (NEW, EXPLICIT)

Before any of this database/API/dashboard build, the pilot must prove the GSA delivery path works with our custom messages. Pilot spec:

**Pilot deliverables:**
- 50–100 custom messages generated for verified-good contact-form sites from the existing 50-site test
- Messages exported to GSA CSV format
- Submitted via GSA on operator's Windows machine with one proxy + operator's CapMonster
- Replies tracked in reply-to Gmail
- Manual log of: landed submits (estimated via reply volume), replies, appointment interest

**Pilot success criteria:**
- GSA accepts the CSV cleanly
- At least 30% of submissions result in no error (GSA-side "submitted OK")
- At least 1 reply within 5 days (proves message lands somewhere real)
- No Gmail account lockout

**Pilot blockers:**
- Reply-to Gmail must be set up first
- Landing page template must exist (even placeholder) because every message links to one
- One verified agency Calendly (operator's own) for the landing page CTA

Pilot is ~1 day of operator setup + 1 hour of agent build work on the exporter.

---

## Execution Order Post-Pilot

Once pilot confirms GSA + custom messages works:

1. **Database layer + API endpoints** (the harness) — unblocks everything downstream
2. **Lead Bank dashboard page** — makes operation sustainable
3. **Response bot** (Cody's GTM recipe) — automates reply handling
4. **Appointment setter bot** (operator's open-source repo) — closes on landing page
5. **Agency router + assignment UI** — enables lead-sale business model
6. **Voice-bot hook module** — second product variant
7. **Additional hooks** — PageSpeed, reviews, etc. as needed per niche

---

## What Explicitly Stays From v1/v2

- All 9 v1 dashboard pages (Lead Bank added as 10th)
- Hook framework (`hook-framework.md` unchanged)
- Tier A/B/C/D ranking-based message selection logic
- Spintax spinner variant system
- DataForSEO as primary data source
- Haiku as message generation LLM
- Pricing tiers from v1 (still apply when SaaS-ified)
- v2 BYOK concepts (still relevant for eventual SaaS)

---

## What Explicitly Changes From v1/v2

| Thing | v1/v2 state | v3 state |
|---|---|---|
| Delivery mechanism | runner.py browser-use | GSA Website Contact (external) |
| Persistent storage | None (CSV-only) | SQLite → Postgres |
| API access to scripts | None (CLI only) | FastAPI endpoints |
| Lead re-messaging | Not supported | Core feature |
| Lead Bank page | Absent | Required |
| Voice-bot offer | Not contemplated | Second hook module |
| 2captcha / proxies | Our problem | Operator's GSA config, out of scope |
| Cost per send | ~$0.04 (Haiku + 2captcha + proxy) | ~$0.002 (Haiku only) |

---

## Open Questions (Resolve Before Full Build)

1. Does the operator want the Windows VPS set up now, or run GSA from their own machine for pilot?
2. Is the landing page domain purchased? (Needed for message URL token.)
3. What specific subject-line policy for initial offer? (Pull from existing `assemble_emails.py` defaults, or custom for pilot?)
4. Approval workflow — does the operator want to review every 50-message GSA batch before send, or run unattended?

These don't block pilot. Resolve during pilot execution.

---

## Out Of Scope For This Amendment

- Agency-facing dashboards and onboarding (separate future PRD)
- Multi-tenant auth (pilot is single-tenant, operator-only)
- Billing / subscription mgmt (only relevant when SaaS-ified)
- Email warming / domain reputation — not needed (GSA delivers through targets' forms, not via our SMTP)
- Compliance UI / unsubscribe handling — operator has flagged awareness, handled operationally for now

---

**Amendment complete. v1/v2 + this doc = current truth.**
