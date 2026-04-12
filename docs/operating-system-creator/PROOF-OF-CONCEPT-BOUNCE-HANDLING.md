# Operating System Creator — Proof of Concept: Bounce Handling

> **What this is:** We're running the Wizard Questionnaire (Part 2) on the "bounce handling" gap from the cold email system. This takes the bounce processing component — which is referenced inside the warmup system's Step 4 but never built as a standalone system — and decomposes it into its own dedicated pipeline using the 6-step pattern.

---

## Section A: Big Picture (Filled Out)

**A1. Process name:** Email Bounce Handler

**A2. What a human does today:**
1. Log into each sending mailbox's inbox (via webmail or email client)
2. Search for emails with subjects like "Undeliverable", "Mail Delivery Failed", "Returned mail", "Delivery Status Notification"
3. Open each bounce-back email and read the error message
4. Identify the SMTP status code (550 = address doesn't exist, 452 = mailbox full, etc.)
5. Determine if it's a hard bounce (permanent — never email again) or soft bounce (temporary — retry later)
6. Filter out auto-replies and out-of-office messages that look like bounces but aren't
7. For hard bounces: find the original recipient address, add it to a "do not email" list/spreadsheet
8. For soft bounces: note the address, plan to retry in 24-48 hours
9. Update the sending mailbox's bounce count and recalculate the bounce rate
10. Check if the bounce rate for any mailbox or domain has crossed a danger threshold (>2% warning, >5% critical)
11. If thresholds exceeded: manually pause the mailbox in SmartLead, send yourself a note
12. Repeat for every sending mailbox — 10-20 mailboxes across multiple domains

**A3. How often:** Every 4-6 hours during active sending. Bounces can arrive minutes to hours after sending, so frequent checks catch problems before they compound.

**A4. How long per run:** 15-30 minutes per full check of all mailboxes, depending on bounce volume. Heavy sending days can mean 50+ bounce messages to triage.

**A5. Items per run:** 10-20 mailboxes to scan, 0-100+ bounce messages to classify per run (varies with send volume and list quality).

**A6. Starting data:**
- IMAP credentials for each sending mailbox (to read incoming bounce notifications)
- SmartLead API (campaign bounce data as a secondary source)
- Existing suppression list (to avoid re-processing known bounces)

**A7. End result goes to:**
- Supabase (suppression list — addresses that must never be emailed again)
- Supabase (bounce logs — per-mailbox and per-domain bounce rate tracking)
- Telegram (alerts when bounce rates exceed thresholds)
- SmartLead (pause mailbox API call if bounce rate is critical)

**A8. Tools already in use:**

| Tool/Service | What it's used for | Has API? |
|---|---|---|
| IMAP (Gmail/Google Workspace) | Reading bounce-back emails from sending mailboxes | Yes (Python imaplib, built-in) |
| SmartLead | Cold email sending platform, has bounce data endpoint | Yes (REST API) |
| Supabase | Database for suppression list and bounce logs | Yes (JS client library) |
| Claude Haiku | Classifying ambiguous bounce messages | Yes (Anthropic API) |
| Telegram | Alert notifications | Yes (Bot API) |
| MillionVerifier / ZeroBounce | Pre-send email verification (reduces bounces proactively) | Yes ($0.0005-0.008/email) |

**A9. What breaks most often:**
- Not checking frequently enough — bounces pile up, bounce rate spikes to 5%+ before anyone notices, domain gets blacklisted
- Misclassifying auto-replies as bounces — inflates bounce rate, triggers false alarms, causes unnecessary mailbox pauses
- Missing delayed bounces — some ISPs send bounce notifications 6-24 hours after the original send, so a single daily check misses them
- Not maintaining the suppression list — a bounced address gets emailed again in the next campaign, bounces again, double-counting the damage
- IMAP connection failures — Google rate-limits IMAP connections, especially with many mailboxes. If the scanner can't connect, bounces go undetected

**A10. Legal/compliance:** CAN-SPAM requires honoring unsubscribe requests and maintaining suppression lists. Repeatedly emailing addresses that hard-bounce is a compliance risk — ISPs track this and it can lead to domain-level blocks. GDPR applies if any bounced contacts are EU-based (the bounce record itself contains PII — the email address). Suppression list must be retained even if contact is "deleted" to prevent re-sending.

---

## Section B: Step Breakdown

### Step 1: Inbox Scan for Bounce Messages

**B1. What the human does:** Connect to each sending mailbox via IMAP. Search the inbox for emails with bounce-related subjects: "Undeliverable", "Mail Delivery Failed", "Returned mail", "Delivery Status Notification (Failure)", "Undelivered Mail Returned to Sender". Also check for messages from "MAILER-DAEMON" or "postmaster@". Mark processed messages so they aren't re-scanned.

**B2. Input needed:** IMAP credentials (host, port, username, password) for each sending mailbox. List of active mailboxes from the database. Timestamp of last scan (to only fetch new messages since last run).

**B3. Decisions:**
- Which emails are potential bounces vs. normal replies, auto-replies, or out-of-office messages
- Whether to skip mailboxes that failed IMAP connection on previous run
- Whether a message has already been processed (check message ID against processed log)

**B4. Could Claude decide?** Partially. Subject-line matching and sender-address matching (MAILER-DAEMON, postmaster@) handle 90% of cases with simple rules. For edge cases where the subject is ambiguous, Claude Haiku can read the email body and classify it. Cost: ~$0.001 per ambiguous message.

**B5. Output:** List of raw bounce email messages (with headers, body, and metadata) per mailbox.

**B6. Output goes to:** Into Step 2 (Bounce Parser) as input.

**B7. API tool:**

| Tool | API? | Cost | Notes |
|---|---|---|---|
| Python imaplib | Built-in | Free | Standard IMAP client, works with Gmail/Google Workspace |
| Gmail API (alternative) | Yes | Free (quota limits) | OAuth2-based, more reliable than IMAP for Google, but more setup |

**B8. Error case:** IMAP connection refused — retry after 60 seconds, max 3 retries. If still failing, log the error, skip this mailbox, alert via Telegram. Google rate-limits IMAP to ~15 connections/minute per account — add 2-second delay between mailbox connections.

**B9. Human time:** 3-5 minutes per mailbox to open, search, and collect bounce messages. 30-60 minutes for 10-20 mailboxes.

---

### Step 2: Bounce Parsing and Classification

**B1. What the human does:** Read each bounce-back email. Find the SMTP status code in the body (e.g., "550 5.1.1 User unknown", "452 4.2.2 Mailbox full"). Extract the original recipient email address that bounced. Determine if it's a hard bounce (5xx codes — permanent failure) or soft bounce (4xx codes — temporary). Filter out auto-replies ("I'm out of the office until...") and delivery delay warnings that aren't actual bounces.

**B2. Input needed:** Raw bounce email messages from Step 1.

**B3. Decisions:**
- Hard bounce (550, 551, 552, 553, 554): address doesn't exist, domain doesn't exist, mailbox disabled, permanently rejected — never email again
- Soft bounce (450, 451, 452): mailbox full, server temporarily unavailable, greylisting — retry once after 24 hours
- Auto-reply / out-of-office: NOT a bounce — discard, do not count toward bounce rate
- Delivery delay notification: NOT a bounce yet — ignore unless followed by a final failure
- Ambiguous / no clear status code: use Claude Haiku to classify based on the full message body

**B4. Could Claude decide?** Yes. Rules-based parsing handles 80-85% of bounces (clear SMTP codes in standard DSN format). Claude Haiku handles the remaining 15-20% — messages with non-standard formatting, foreign-language bounce notifications, or missing status codes. Cost: ~$0.001 per classification, roughly $0.10-0.50/month at typical volumes.

**B5. Output:** Structured bounce record: `{ recipient_email, bounce_type: 'hard'|'soft'|'auto_reply'|'unknown', smtp_code, smtp_message, source_mailbox, original_subject, timestamp }`.

**B6. Output goes to:** Into Step 3 (Suppression & State Update) as input.

**B7. API tool:**

| Tool | API? | Cost | Notes |
|---|---|---|---|
| Python email module | Built-in | Free | Parses MIME messages, extracts headers and body parts |
| Claude Haiku (claude-3-5-haiku) | Yes | ~$0.001/call | For ambiguous bounce messages that rules can't classify |
| SmartLead Bounce API | Yes | Included | GET /campaigns/{id}/bounces — secondary data source, pre-classified |

**B8. Error case:** Unparseable email format — log the raw message, classify as 'unknown', flag for human review. Claude Haiku API failure — fall back to rules-only classification, flag ambiguous ones for later re-processing.

**B9. Human time:** 1-2 minutes per bounce message to read, interpret, and classify. At 50 bounces, that's 50-100 minutes — the most time-consuming step.

---

### Step 3: Suppression List & State Update

**B1. What the human does:** For each hard bounce, add the recipient email address to the "do not email" list. Check if the address is already on the list (skip if yes). Update the sending mailbox's bounce count: increment total_bounced, recalculate bounce_rate as (total_bounced / total_sent). Update the domain's aggregate bounce rate. For soft bounces, schedule a retry — if the same address soft-bounces a second time, treat it as a hard bounce and suppress.

**B2. Input needed:** Classified bounce records from Step 2. Current mailbox stats (total_sent, total_bounced) from the database. Current suppression list (to check for duplicates).

**B3. Decisions:**
- Hard bounce → add to suppression list immediately, no second chances
- First soft bounce → mark for retry in 24 hours, do not suppress yet
- Second soft bounce on same address → promote to hard bounce, add to suppression list
- Already on suppression list → skip, do not double-count in bounce rate
- Auto-reply / out-of-office → discard entirely, no state change

**B4. Could Claude decide?** Yes, with clear rules. No judgment needed — this is pure conditional logic based on bounce_type and whether the address already exists in suppression_list or soft_bounce_retries.

**B5. Output:** Updated suppression list. Updated per-mailbox bounce counts and rates. Updated per-domain aggregate bounce rates.

**B6. Output goes to:** Database (suppression_list, mailbox stats, domain stats) + feeds into Step 4 (Rate Check & Alerting).

**B7. API tool:**

| Tool | API? | Cost | Notes |
|---|---|---|---|
| Supabase JS Client | Yes | Free tier sufficient | Upsert to suppression_list, update mailbox/domain stats |

**B8. Error case:** Database write fails — retry with exponential backoff. Duplicate key on suppression_list insert — expected behavior, use upsert (ON CONFLICT DO NOTHING). Stale mailbox stats (another process updated them) — re-read and recalculate before writing.

**B9. Human time:** 1 minute per bounce to update the spreadsheet/list. At scale, this is where errors creep in — humans forget to update the list, or update the wrong column.

---

### Step 4: Rate Check & Alerting

**B1. What the human does:** After processing all bounces, review the updated bounce rate for each mailbox and each domain. Compare against thresholds. If bounce rate > 2%: reduce sending volume by 50%. If bounce rate > 5%: pause the mailbox entirely. If a domain's aggregate bounce rate is problematic: consider pausing all mailboxes on that domain. Send themselves a reminder or note about which mailboxes need attention.

**B2. Input needed:** Updated mailbox stats from Step 3. Threshold configuration (warning at 2%, critical at 5%). SmartLead API access (to pause mailboxes or reduce volume).

**B3. Decisions:**
- Bounce rate < 2% → healthy, no action needed
- Bounce rate 2-5% → warning: reduce daily send volume by 50%, send warning alert
- Bounce rate > 5% → critical: pause mailbox immediately (set volume to 0 in SmartLead), send critical alert
- Domain aggregate bounce rate > 3% → warning: all mailboxes on this domain are at risk
- Spam complaint rate > 0.3% → critical: pause mailbox immediately regardless of bounce rate

**B4. Could Claude decide?** Yes — pure threshold comparison. No judgment needed.

**B5. Output:** List of actions taken (paused, reduced, healthy). Telegram notifications for any non-healthy mailbox. Daily summary message.

**B6. Output goes to:** SmartLead API (pause/reduce volume) + Telegram (alerts) + Database (event log of actions taken).

**B7. API tool:**

| Tool | API? | Cost | Notes |
|---|---|---|---|
| SmartLead API | Yes | Included with Pro plan | PATCH /email-accounts/{id} to update daily send limit or pause |
| Telegram Bot API | Yes | Free | POST /sendMessage for alerts |

**B8. Error case:** SmartLead API fails to pause a mailbox — this is a CRITICAL failure. Retry 3 times with 5-second delay. If still failing, send Telegram alert with manual instructions: "MANUAL ACTION REQUIRED: Pause {email} in SmartLead immediately."

**B9. Human time:** 5-10 minutes to review all mailboxes and take actions. The danger is delay — if the human doesn't check for 12 hours, a mailbox with 6% bounce rate has been sending all day, burning the domain.

---

### Step 5: SmartLead Bounce Sync (Secondary Source)

**B1. What the human does:** In addition to IMAP scanning, check SmartLead's built-in bounce reporting via the campaign dashboard. SmartLead detects some bounces that don't generate IMAP bounce-back emails (e.g., when the receiving server rejects during SMTP handshake before a bounce email is generated). Cross-reference SmartLead bounces with the IMAP-detected bounces to catch anything missed.

**B2. Input needed:** SmartLead API key. List of active campaign IDs. Existing suppression list (to avoid duplicates).

**B3. Decisions:**
- If SmartLead reports a bounce that wasn't detected via IMAP → add to suppression list
- If SmartLead and IMAP both report the same bounce → already handled, skip
- SmartLead classifies its own bounces — trust its classification for addresses it detected

**B4. Could Claude decide?** Yes — this is a set-difference operation. No judgment needed.

**B5. Output:** Additional bounced addresses caught by SmartLead but missed by IMAP. Merged into the same suppression list and bounce rate calculations.

**B6. Output goes to:** Database (suppression_list, mailbox stats) — same destination as Step 3.

**B7. API tool:**

| Tool | API? | Cost | Notes |
|---|---|---|---|
| SmartLead API | Yes | Included | GET /campaigns/{id}/bounces — returns list of bounced addresses with classification |

**B8. Error case:** SmartLead API returns empty data — could mean no bounces (good) or API issue. If ALL campaigns return empty and there was recent sending, log a warning. API rate limit hit — add 500ms delay between campaign requests.

**B9. Human time:** 5-10 minutes to check SmartLead dashboard and cross-reference. Tedious but catches 10-15% of bounces that IMAP misses.

---

## Section C: Operations Layer (Filled Out)

### State Tracking

**C1. Statuses per bounce record:**
`detected → classified → suppressed` (for hard bounces)
`detected → classified → retry_scheduled → retried → suppressed` (for soft bounces that fail retry)
`detected → classified → retry_scheduled → retried → cleared` (for soft bounces that succeed on retry)
`detected → classified → discarded` (for auto-replies / out-of-office)

**C2. Audit trail:** Yes — full event log. Every bounce detection, classification, suppression list addition, rate calculation, and action taken (pause/reduce/alert) must be logged with timestamps. Critical for debugging deliverability issues and proving CAN-SPAM compliance (we can show when an address was suppressed and that we never emailed it again after that).

**C3. Dedup:** Unique identifier = bounced email address (lowercase, trimmed). Also deduplicate by IMAP message ID to prevent re-processing the same bounce notification. Suppression list uses email as UNIQUE constraint — upsert pattern ensures no duplicates.

### Notifications

**C4. Who needs to know:** Just me (solo operator). Later: team members or clients if running as agency.

**C5. What they need to know:**
- Every run: "Bounce scan complete. 3 new hard bounces, 1 soft bounce. All mailboxes healthy."
- Warning: "WARNING: mike@cenra.io bounce rate hit 2.8% (14/500 sent) — volume reduced to 10/day."
- Critical: "CRITICAL: mike@cenra.io bounce rate hit 5.2% — PAUSED. Manual review required."
- Daily digest: "Daily Bounce Report: 12 bounces processed, 8 hard / 3 soft / 1 auto-reply. Suppression list: 847 addresses. All 15 mailboxes below 2%."

**C6. How:** Telegram for instant alerts and run summaries. Silent if all mailboxes are healthy and no new bounces detected.

### Scheduling

**C7. When:** Every 4 hours via cron. Bounces can arrive with delay, so 4-hour intervals catch them before they compound. During high-volume sending days, can be increased to every 2 hours.

**C8. Failure recovery:** Resume from where it left off. Each mailbox is scanned independently — if one IMAP connection fails, continue with the remaining mailboxes. Track last successful scan timestamp per mailbox so the next run picks up where the failed one stopped.

**C9. Infrastructure:** Cloud server (same VPS running the rest of the cold email pipeline). Hetzner or DigitalOcean, $6-12/month. Shares Supabase instance with warmup manager and other pipeline components.

---

## Section D: Success Criteria (Filled Out)

**D1. Metrics:**

| Metric | Current (Manual) | Target (Automated) |
|---|---|---|
| Time spent on bounce processing | 15-30 min/run, 2-3 runs/day = 45-90 min/day | 0 min/day (fully automated, review Telegram alerts only) |
| Time to detect a bounce rate spike | 4-12 hours (depends on when human checks) | < 1 hour (automated 4-hour scan cycle) |
| Domains burned from undetected bounces | 1-2 per quarter | 0 (auto-pause catches issues before domain damage) |
| Suppression list accuracy | ~90% (human misses some, misclassifies others) | 99%+ (rules + Claude Haiku classification) |
| Bounced addresses re-emailed | Happens occasionally (list not synced) | 0 (pre-send suppression check enforced) |

**D2. Human cost:** 45-90 min/day x 30 days = 22-45 hours/month. At $50/hour contractor rate = $1,100-2,250/month. This is more expensive than warmup monitoring because bounce processing requires reading and interpreting individual emails — high cognitive load, highly error-prone, deeply tedious.

**D3. Budget:** Minimal — IMAP is free, Python email module is free, Claude Haiku for classification is ~$2-5/month at typical volumes. Supabase free tier is sufficient. Telegram bot is free. SmartLead API is included with Pro plan. Total incremental cost: < $10/month.

**D4. MVP step:** Step 2 (Bounce Parsing and Classification) — this is the step where humans spend the most time and make the most errors. Automating the classification of bounce messages and extraction of bounced addresses delivers the highest immediate value. Step 3 (Suppression List Update) is the natural second priority since it directly prevents re-sending to bad addresses.

---

## The 6-Step Architecture Map

```
SCHEDULE: Cron job — runs every 4 hours on VPS
    |
    v
INPUT: IMAP (bounce-back emails from each sending mailbox)
       SmartLead API (campaign bounce data as secondary source)
       Supabase (existing suppression list for dedup check)
    |
    v
PROCESS: 
    Step 1 — Inbox scan: IMAP connect to each mailbox, fetch bounce-like messages
    Step 2 — Parse & classify: extract recipient + SMTP code, classify hard/soft/auto-reply
    Step 3 — Suppression & state: add hard bounces to suppression list, update bounce counts
    Step 4 — Rate check & alert: compare bounce rates against thresholds, pause/reduce if needed
    Step 5 — SmartLead sync: cross-reference SmartLead bounce data to catch IMAP misses
    |
    v
OUTPUT: Supabase (suppression_list — addresses never to email again)
        SmartLead API (pause or reduce volume on high-bounce mailboxes)
    |
    v
STATE: Supabase tables:
    - suppression_list (email, bounce_type, smtp_code, source_mailbox, detected_at)
    - bounce_log (id, recipient_email, bounce_type, smtp_code, smtp_message, source_mailbox, campaign_id, raw_message_id, detected_at)
    - mailbox_bounce_stats (mailbox_email, total_sent, total_bounced, bounce_rate, last_scan_at)
    - domain_bounce_stats (domain, total_sent, total_bounced, bounce_rate, last_updated)
    - bounce_events (id, mailbox_email, event_type, severity, details, created_at)
    - soft_bounce_retries (email, first_bounce_at, retry_scheduled_at, retried, retry_result)
    |
    v
NOTIFY: Telegram bot
    - Every run: silent if no new bounces and all rates healthy
    - New bounces: "Processed 5 bounces: 3 hard, 1 soft, 1 auto-reply"
    - Warning: "mike@cenra.io bounce rate 2.8% — volume reduced to 10/day"
    - Critical: "PAUSED mike@cenra.io — bounce rate 5.2%. Manual review required."
    - Daily 8am: summary of all mailbox bounce rates and suppression list size
```

---

## Proof This Framework Works

We took the bounce handling gap — which was mentioned as a sub-step inside the warmup system but never built out as its own pipeline — and decomposed it into a complete standalone system using the same wizard questionnaire. The result:

1. A complete process breakdown (5 steps with inputs, outputs, decisions, error cases, and time estimates)
2. A full operations plan (state tracking with lifecycle statuses, audit trail, dedup strategy)
3. Success criteria with measurable targets and cost justification
4. A 6-step architecture map ready to be turned into a CLAUDE.md build file

The bounce handler is more granular than the warmup manager because it deals with individual messages (not just aggregate stats), requires natural language classification (Claude Haiku), and has stronger compliance requirements (CAN-SPAM suppression). The framework handled this increased complexity without any structural changes — the same 6-step pattern and the same questionnaire sections produced a complete specification.

**Next step:** The CLAUDE-MD-BOUNCE-HANDLING.md build file turns this architecture into an actual buildable system with code specifications.
