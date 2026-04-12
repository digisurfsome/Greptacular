# Operating System Creator — Proof of Concept: Email Warmup

> **What this is:** We're running the Wizard Questionnaire (Part 2) on the "email warmup" gap from the cold email system. This proves the framework works by taking a missing component and building it from scratch using the 6-step pattern.

---

## Section A: Big Picture (Filled Out)

**A1. Process name:** Email Mailbox Warmup Manager

**A2. What a human does today:**
1. Buy 2-5 domains related to the business (e.g., cenra.io, getcenra.com, trycentra.co)
2. Set up Google Workspace on each domain ($6/user/month)
3. Create 2-3 mailboxes per domain (e.g., mike@cenra.io, m.johnson@cenra.io)
4. Configure SPF, DKIM, and DMARC DNS records for each domain
5. Sign up for a warmup service (Lemwarm, Warmup Inbox) OR manually send emails between accounts
6. Start at 5 emails/day per mailbox, increasing by 2-3/day every few days
7. Monitor deliverability — check if emails land in inbox vs spam
8. After 14-21 days, begin cold sending at low volume (5/day) and ramp up
9. Ongoing: monitor bounce rates, spam complaints, and inbox placement per mailbox
10. If a mailbox gets flagged: pause it, reduce volume, or retire the domain

**A3. How often:** Daily monitoring during warmup (21 days), then ongoing daily health checks

**A4. How long per run:** 30-45 minutes/day manually checking all mailboxes

**A5. Items per run:** 10-20 mailboxes across 5-8 domains (per business)

**A6. Starting data:**
- Domain registrar (Namecheap, Google Domains, Cloudflare)
- Google Workspace admin panel
- DNS provider (Cloudflare, Namecheap DNS)
- Warmup service dashboard OR your own mailbox network

**A7. End result goes to:**
- SmartLead (mailboxes ready for cold campaigns)
- Supabase (health metrics logged)
- Telegram (alerts when something goes wrong)

**A8. Tools already in use:**

| Tool/Service | What it's used for | Has API? |
|---|---|---|
| Google Workspace | Email hosting | Yes (Admin SDK) |
| Cloudflare | DNS management | Yes |
| SmartLead | Cold email sending | Yes |
| Lemwarm OR Warmup Inbox | Warmup sending/receiving | Limited (Lemwarm has basic API) |
| Google Postmaster Tools | Deliverability monitoring | Yes (API available) |
| MillionVerifier | Pre-send email validation | Yes |

**A9. What breaks most often:**
- Forgetting to check a mailbox that got flagged — it keeps sending and burns the whole domain
- DNS records set up wrong — SPF/DKIM fail silently, emails go to spam from day 1
- Ramping up too fast — going from 5/day to 50/day in a week triggers spam filters
- Not monitoring bounce rates — a 5% bounce rate on one mailbox poisons the domain reputation

**A10. Legal/compliance:** CAN-SPAM (physical address, unsubscribe), GDPR if targeting EU. Warmup emails between your own accounts have no legal issues.

---

## Section B: Step Breakdown

### Step 1: Domain Health Check

**B1. What the human does:** Log into Google Postmaster Tools, check each domain's reputation (High/Medium/Low/Bad), spam rate, authentication pass rates (SPF/DKIM/DMARC).

**B2. Input needed:** List of sending domains, Google Postmaster Tools credentials.

**B3. Decisions:** If reputation drops to "Low" — pause all mailboxes on that domain. If spam rate exceeds 0.3% — investigate which mailbox is causing it.

**B4. Could Claude decide?** Yes, with clear rules: reputation < Medium = pause. Spam rate > 0.3% = alert. Auth failure = check DNS.

**B5. Output:** Per-domain health status (healthy / warning / critical).

**B6. Output goes to:** Database (health log) + Telegram (if warning/critical).

**B7. API tool:** Google Postmaster Tools API — free, provides domain reputation and spam rate data.

**B8. Error case:** API returns no data (domain too new or too little volume). Action: skip, mark as "insufficient data."

**B9. Human time:** 5-10 minutes per domain, 30+ minutes for 5-8 domains.

---

### Step 2: Mailbox Health Check

**B1. What the human does:** For each mailbox, check: emails sent today, bounces, bounce rate, replies received, spam reports. Compare against thresholds.

**B2. Input needed:** SmartLead API (campaign stats per email account), IMAP access to each mailbox (to check for bounce-back emails).

**B3. Decisions:**
- Bounce rate > 2%: reduce volume by 50%
- Bounce rate > 5%: pause mailbox for 48 hours
- No replies in 5+ days during warmup: check if landing in spam
- Spam complaints > 0.1%: pause immediately

**B4. Could Claude decide?** Yes, with clear threshold rules above. No judgment needed — pure math.

**B5. Output:** Per-mailbox health status + recommended action (continue / reduce / pause / retire).

**B6. Output goes to:** Database (mailbox_health table) + Telegram (alerts for any non-healthy mailbox).

**B7. API tool:** SmartLead API for campaign stats. Python imaplib for bounce detection.

**B8. Error case:** SmartLead API down — retry after 5 minutes, alert if still down. IMAP connection fails — alert, skip mailbox.

**B9. Human time:** 2-3 minutes per mailbox, 20-40 minutes for 10-20 mailboxes.

---

### Step 3: Warmup Volume Management

**B1. What the human does:** Check how many days each mailbox has been warming up. Adjust daily send volume according to the ramp schedule. Update the warmup service or SmartLead settings.

**B2. Input needed:** Mailbox creation date, current daily volume, ramp schedule, health status from Step 2.

**B3. Decisions:**
- Days 1-3: 5 emails/day
- Days 4-7: 10 emails/day
- Days 8-14: 15 emails/day
- Days 15-21: 20 emails/day
- Day 22+: Ready for cold sending, start at 5 cold/day + maintain 10 warmup/day
- If health status is "warning": freeze volume at current level
- If health status is "critical": reduce to 5/day

**B4. Could Claude decide?** Yes — this is a pure lookup table + health status check. No judgment needed.

**B5. Output:** Updated daily volume target per mailbox + SmartLead API call to update settings.

**B6. Output goes to:** SmartLead (volume update) + Database (volume log) + Telegram (daily summary).

**B7. API tool:** SmartLead API to update email account settings.

**B8. Error case:** SmartLead API fails to update — retry, then alert. Mailbox hit sending limit — reduce volume target.

**B9. Human time:** 1-2 minutes per mailbox to check and adjust.

---

### Step 4: Bounce Processing

**B1. What the human does:** Check each sending mailbox's inbox for bounce-back emails. Read each one. Determine if it's a hard bounce (address doesn't exist) or soft bounce (temporary issue). Update the contact record so that address is never emailed again.

**B2. Input needed:** IMAP access to each sending mailbox.

**B3. Decisions:**
- Hard bounce (550, 551, 552, 553, 554 error codes): Mark contact as `bounced`, add to suppression list, never email again
- Soft bounce (450, 451, 452 codes): Retry once after 24 hours. If bounces again, treat as hard bounce
- Auto-reply / out-of-office: Not a bounce — ignore for health purposes

**B4. Could Claude decide?** Yes — Claude Haiku can classify bounce emails by reading the error message and extracting the status code. Cost: ~$0.001 per bounce email.

**B5. Output:** List of hard-bounced addresses to add to suppression list. Updated bounce count per mailbox.

**B6. Output goes to:** Supabase (suppression_list table + bounce count update) + feeds back into Step 2 (bounce rate calculation).

**B7. API tool:** Python imaplib for reading bounce emails. Claude Haiku API for classification.

**B8. Error case:** IMAP locked/busy — retry after 60 seconds. Unparseable bounce format — flag for human review.

**B9. Human time:** 5-15 minutes per mailbox depending on volume.

---

## Section C: Operations Layer (Filled Out)

### State Tracking

**C1. Statuses per mailbox:**
`created → dns_configured → warming → warm_ready → active_sending → warning → paused → retired`

**C2. Audit trail:** Yes — full event log. Need to know exactly when a mailbox was paused, why, and what the metrics were at that time. Important for debugging deliverability issues.

**C3. Dedup:** Unique identifier = email address of the mailbox (e.g., mike@cenra.io). Also deduplicate bounced contacts by email address in the suppression list.

### Notifications

**C4. Who needs to know:** Just me (solo operator). Later: clients if running as agency.

**C5. What they need to know:**
- Daily summary: "All 15 mailboxes healthy. 3 in warmup (day 12, 8, 4). 12 active."
- Instant alert: "ALERT: mike@cenra.io bounce rate hit 4.2% — auto-paused."
- Weekly report: "Domain cenra.io reputation: High. Average open rate: 62%. 0 spam complaints."

**C6. How:** Telegram for instant alerts + daily summary. Email for weekly client reports.

### Scheduling

**C7. When:** Twice daily — morning check (8am) and evening check (6pm). Bounce processing runs every 4 hours.

**C8. Failure recovery:** Resume from where it left off. Each mailbox is checked independently — if one fails, continue checking the rest.

**C9. Infrastructure:** Cloud server (same VPS running n8n and the rest of the cold email pipeline). Hetzner or DigitalOcean, $6-12/month.

---

## Section D: Success Criteria (Filled Out)

**D1. Metrics:**

| Metric | Current (Manual) | Target (Automated) |
|---|---|---|
| Time spent on warmup monitoring | 30-45 min/day | 5 min/day (review Telegram alerts) |
| Domains burned per quarter | 1-2 (caught too late) | 0 (auto-pause catches issues instantly) |
| Time to detect deliverability issue | 12-24 hours (next manual check) | < 1 hour (automated check cycle) |
| Mailboxes managed per operator | 10-15 (manual ceiling) | 50+ (automated monitoring) |

**D2. Human cost:** 30-45 min/day x 30 days = 15-22 hours/month. At $50/hour contractor rate = $750-1,100/month.

**D3. Budget:** Minimal — Google Postmaster API is free. IMAP is free. Claude Haiku for bounce classification is ~$2/month. VPS already exists.

**D4. MVP step:** Step 2 (Mailbox Health Check) — this catches problems before they burn domains. Highest impact, prevents the most expensive failure mode.

---

## The 6-Step Architecture Map

```
SCHEDULE: Cron job — runs every 4 hours on VPS
    │
    ▼
INPUT: Google Postmaster API (domain reputation)
       SmartLead API (campaign stats per mailbox)
       IMAP (bounce-back emails from each mailbox)
    │
    ▼
PROCESS: 
    Step 1 — Domain health: compare reputation against thresholds
    Step 2 — Mailbox health: calculate bounce rate, compare against thresholds
    Step 3 — Volume management: lookup ramp schedule, adjust based on health
    Step 4 — Bounce processing: Claude Haiku classifies bounce type
    │
    ▼
OUTPUT: SmartLead API (update volume settings, pause mailboxes)
        Supabase (suppression_list table — bounced addresses)
    │
    ▼
STATE: Supabase tables:
    - mailbox_health (mailbox_id, status, bounce_rate, daily_volume, warmup_day, last_checked)
    - domain_health (domain, reputation, spam_rate, auth_status, last_checked)
    - health_events (event_id, mailbox_id, event_type, details, timestamp)
    - suppression_list (email, bounce_type, source_mailbox, bounced_at)
    │
    ▼
NOTIFY: Telegram bot
    - Every run: silent if all healthy
    - Warning: "mike@cenra.io bounce rate 2.3% — volume reduced to 10/day"
    - Critical: "PAUSED mike@cenra.io — bounce rate 5.1%"
    - Daily 8am: summary of all mailbox statuses
```

---

## Proof This Framework Works

We just took a gap (email warmup) that had ZERO documentation in the original cold email system, ran it through the wizard questionnaire, and produced:

1. A complete process breakdown (4 steps with inputs, outputs, decisions, error cases)
2. A full operations plan (state tracking, notifications, scheduling)
3. Success criteria with measurable targets
4. A 6-step architecture map ready to be turned into a CLAUDE.md build file

This is the exact same level of detail as the Skool guy's best modules (like `2-MOD-daily-lead-engine.md`). The framework extracted the pattern, and the questionnaire guided us to fill in all the blanks.

**Next step:** Part 4 turns this architecture into an actual CLAUDE.md build file with code specifications.
