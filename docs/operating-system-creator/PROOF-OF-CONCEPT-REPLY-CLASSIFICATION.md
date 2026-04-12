# Operating System Creator — Proof of Concept: Reply Classification

> **What this is:** We're running the Wizard Questionnaire (Part 2) on the "reply classification" gap from the cold email system. This takes the manual process of reading and routing prospect replies and turns it into an automated Claude-powered classification pipeline using the 6-step pattern.

---

## Section A: Big Picture (Filled Out)

**A1. Process name:** Reply Classification & Routing Engine

**A2. What a human does today:**
1. Check the inbox of each sending mailbox for new replies (10-20 mailboxes across 5-8 domains)
2. Open each reply and read the full email thread to understand context
3. Mentally classify the reply: interested, not interested, unsubscribe request, out of office, wrong person, hostile, etc.
4. Based on the classification, take the appropriate action:
   - Interested: immediately notify the sales person, move lead to "hot" status in CRM
   - Unsubscribe: remove from all active sequences, add to suppression list
   - Not interested: mark as declined, stop the sequence for that prospect
   - Wrong person/referral: extract the referred contact info, create a new lead
   - Out of office: note the return date, reschedule follow-up
   - Hostile: blacklist the domain, remove from all lists, alert the operator
5. Update the lead status in SmartLead / the CRM
6. Log what happened so there's a record
7. Repeat across all mailboxes, multiple times per day

**A3. How often:** Multiple times per day — interested replies lose value by the hour. Unsubscribe requests have legal deadlines (CAN-SPAM). Ideally checked every 5-15 minutes.

**A4. How long per run:** 20-40 minutes per check across all mailboxes. With 50+ replies/day during active campaigns, this is 1-2 hours/day of pure email reading and routing.

**A5. Items per run:** 10-80 replies per day depending on campaign volume. During peak sending (20 mailboxes x 25 emails/day = 500 outbound), expect 2-5% reply rate = 10-25 replies/day. Spikes during new campaign launches.

**A6. Starting data:**
- IMAP inbox of each sending mailbox (replies land here)
- SmartLead webhook notifications (push-based alternative to IMAP polling)
- SmartLead API (campaign context — which campaign/sequence triggered the reply)
- The original outbound email thread (needed for context)

**A7. End result goes to:**
- Supabase (reply logs, lead status updates, classification records)
- Telegram (instant alert for "interested" replies)
- SmartLead API (pause sequence for unsubscribes, stop sequence for declines)
- Suppression list in Supabase (unsubscribe/hostile addresses never emailed again)

**A8. Tools already in use:**

| Tool/Service | What it's used for | Has API? |
|---|---|---|
| SmartLead | Cold email sending + sequence management | Yes (webhooks + REST API) |
| Supabase | Database for leads, campaigns, suppression lists | Yes |
| Claude Haiku | AI text classification (not yet used for replies) | Yes (Anthropic API) |
| Telegram | Operator notifications | Yes (Bot API) |
| Python imaplib | IMAP inbox access | Built-in Python library |
| Instantly | Alternative sending platform (has basic keyword triggers) | Yes (limited) |

**A9. What breaks most often:**
- Missing an "interested" reply for 6+ hours — prospect goes cold, competitor books the meeting instead. Speed to lead is the #1 conversion factor.
- Not processing unsubscribe requests — leads to spam complaints, which damage sender reputation and can burn entire domains. CAN-SPAM violation risk.
- Hostile replies not caught — prospect reports you as spam, ISP flags the domain, deliverability tanks for ALL mailboxes on that domain.
- Wrong-person referrals missed — these are the warmest leads in cold email (someone vouched for you) and they get buried in the inbox.
- Out-of-office replies not parsed — the sequence keeps firing emails into the void, wasting send volume and looking unprofessional.
- Manual fatigue — reading 50+ replies/day across multiple inboxes is tedious; humans start skimming, misclassify, or just stop checking.

**A10. Legal/compliance:**
- **CAN-SPAM (US):** Must honor unsubscribe requests within 10 business days. Best practice is within minutes. Failure = $51,744 penalty per email.
- **GDPR (EU):** If targeting EU prospects, unsubscribe/removal requests must be processed and the contact's data deleted upon request.
- **Hostile/spam reports:** Not a legal requirement to process instantly, but failure to blacklist hostile contacts leads to domain reputation damage that is expensive and slow to recover from.
- **Data retention:** Reply content may contain PII. Store classification results and metadata, not full reply bodies long-term.

---

## Section B: Step Breakdown

### Step 1: Reply Ingestion

**B1. What the human does:** Check each sending mailbox's inbox for new replies. Open each one. Distinguish actual prospect replies from auto-replies, bounce notifications, and spam.

**B2. Input needed:** IMAP credentials for each sending mailbox. Alternatively, SmartLead webhook payload (pushes reply notifications in real-time). A timestamp of the last check (to only process new replies).

**B3. Decisions:**
- Is this a real reply or a system-generated message (delivery notification, newsletter confirmation, etc.)?
- Has this reply already been processed? (deduplication)
- Can we match this reply back to a specific campaign and prospect?

**B4. Could Claude decide?** Partially — matching replies to campaigns is a database lookup (not AI). Distinguishing real replies from system messages can be done with header inspection (auto-submitted headers, mailer-daemon sender). Claude is not needed for this step — it's pure logic.

**B5. Output:** A list of new, unprocessed prospect replies, each with: reply body text, sender email, timestamp, matched campaign ID, matched prospect record.

**B6. Output goes to:** Into Step 2 (classification).

**B7. API tool:**

| Tool | API? | Cost | Notes |
|---|---|---|---|
| Python imaplib | Built-in | Free | Poll-based, check every 5 min |
| SmartLead Webhooks | Yes | Included in plan | Push-based, near real-time, preferred |
| IMAP IDLE | Built-in | Free | Persistent connection, instant notification |

**B8. Error case:** IMAP connection fails — retry after 60 seconds, alert if 3 consecutive failures. SmartLead webhook endpoint down — fall back to IMAP polling. Reply can't be matched to a campaign — log as "unmatched" for human review.

**B9. Human time:** 5-10 minutes per check across all mailboxes just to open and scan replies.

---

### Step 2: AI Classification

**B1. What the human does:** Read each reply carefully. Determine the intent: are they interested? Saying no? Asking to be removed? Referring someone else? Out of office? Angry? Figure out the category and how confident they are in that assessment.

**B2. Input needed:** Reply body text from Step 1. Optionally, the original outbound email (for context on what was pitched).

**B3. Decisions:**
- Which of the 9 categories does this reply fall into?
- How confident are we? (Some replies are ambiguous: "Let me think about it" — interested or polite decline?)
- If it's a referral, what's the referred contact's name/email/role?
- If it's out of office, what's the return date?
- If it contains multiple signals (e.g., "I'm not interested but my colleague John might be — john@company.com"), how to handle the multi-intent?

**B4. Could Claude decide?** Yes — this is the core AI step. Claude Haiku excels at text classification. Feed it the reply text, a clear prompt with category definitions, and it returns: category, confidence score (0-100), extracted data (referral contact, return date), and reasoning. Cost: ~$0.001-0.003 per classification.

**B5. Output:** Per-reply classification object: `{ category, confidence, extractedData, reasoning }`.

**B6. Output goes to:** Into Step 3 (routing/actions) + Database (classification_log table for audit trail).

**B7. API tool:**

| Tool | API? | Cost | Notes |
|---|---|---|---|
| Claude Haiku (claude-3-5-haiku) | Yes (Anthropic API) | ~$0.001-0.003/reply | Fast, cheap, accurate for classification |
| OpenAI GPT-4o-mini | Yes | ~$0.002/reply | Alternative, slightly more expensive |

**B8. Error case:** Claude API returns error or times out — retry once after 5 seconds. If still fails, log reply as "classification_failed" for manual review. Confidence score below 60% — flag for human review rather than auto-routing.

**B9. Human time:** 1-2 minutes per reply to read, classify, and decide. At 50 replies/day = 50-100 minutes of pure classification labor.

---

### Step 3: Action Routing

**B1. What the human does:** Based on the classification, take the correct action for each reply. Update CRM status. Pause or stop sequences. Send alerts. Create new leads from referrals.

**B2. Input needed:** Classification result from Step 2. Prospect record from database. Campaign/sequence info from SmartLead.

**B3. Decisions:**

| Category | Action |
|---|---|
| Interested (confidence > 80%) | Alert via Telegram immediately. Update lead status to "hot". Pause the sequence (human takes over). |
| Interested (confidence 60-80%) | Alert via Telegram with "possible interest" flag. Queue for human review. |
| Maybe/Soft Interest | Pause current sequence. Add to nurture list. No urgent alert. |
| Not Interested | Stop sequence for this prospect. Mark as "declined". No further outreach. |
| Unsubscribe/Remove | IMMEDIATE: Remove from all active sequences. Add to global suppression list. Send confirmation (if configured). |
| Wrong Person/Referral | Stop sequence for original prospect. Extract referral contact. Create new lead record. Start referral-specific sequence. |
| Out of Office | Parse return date. Pause sequence. Schedule resume for return date + 2 days. |
| Hostile/Complaint | IMMEDIATE: Blacklist entire domain. Remove from all lists. Alert operator. Log for compliance. |
| Bounce | Route to bounce handler (separate warmup system). Not processed here. |
| Auto-Reply (other) | Ignore. Keep sequence running. Log for records. |

**B4. Could Claude decide?** No AI needed — this is pure rule execution. The classification already happened in Step 2. Step 3 is a routing table: category + confidence = action. Fully deterministic.

**B5. Output:** Executed actions: API calls made, database records updated, notifications sent, new leads created.

**B6. Output goes to:** SmartLead API (sequence pause/stop), Supabase (lead status updates, suppression list, new referral leads), Telegram (alerts), health_events table (audit log).

**B7. API tool:**

| Tool | API? | Cost | Notes |
|---|---|---|---|
| SmartLead API | Yes | Included | Pause/stop sequences per lead |
| Supabase | Yes | Free tier | Database updates |
| Telegram Bot API | Yes | Free | Instant alerts |

**B8. Error case:** SmartLead API fails to pause sequence — retry, then alert operator (critical: prospect might get another email after asking to be removed). Telegram fails — log the alert, retry, continue processing (notification failure shouldn't block action). Supabase write fails — retry with exponential backoff, this is the audit trail.

**B9. Human time:** 2-5 minutes per reply to take all the correct actions. This is where most time is wasted — the human already knows what to do, but has to click through multiple tools.

---

### Step 4: Reporting & Metrics

**B1. What the human does:** At the end of the day, tally up: how many replies total, how many interested, how many unsubscribes, etc. Calculate reply rate per campaign. Identify which campaigns are generating interest vs. hostility.

**B2. Input needed:** All classification results from the day. Campaign send volumes from SmartLead. Historical data for trend comparison.

**B3. Decisions:**
- Is the reply rate for a campaign abnormally low (< 1%)? Might indicate deliverability issues.
- Is the hostile/unsubscribe rate for a campaign abnormally high (> 2%)? Might need to adjust targeting or messaging.
- Which campaigns are generating the most "interested" replies? Double down on those.

**B4. Could Claude decide?** Yes, with clear threshold rules. High unsubscribe rate > 2% = flag campaign. Hostile rate > 1% = pause campaign and alert. But campaign strategy changes (which campaigns to scale) should remain human decisions.

**B5. Output:** Daily summary report: total replies, breakdown by category, per-campaign metrics, flagged campaigns.

**B6. Output goes to:** Telegram (daily summary message) + Supabase (daily_reply_stats table) + CLI output (on-demand report).

**B7. API tool:** No external API needed — all data is already in Supabase from Steps 1-3.

**B8. Error case:** Supabase query fails — retry. If persistent, send Telegram alert with whatever partial data is available.

**B9. Human time:** 10-15 minutes to manually compile daily stats from multiple tools.

---

## Section C: Operations Layer (Filled Out)

### State Tracking

**C1. Statuses per reply:**
`received → classified → routed → action_complete → archived`

**Statuses per lead (updated by classification):**
`new → contacted → replied → interested → booked → declined → unsubscribed → blacklisted`

**C2. Audit trail:** Yes — full event log. Every classification must be logged with: reply text hash (not full text for privacy), category assigned, confidence score, actions taken, timestamp. Critical for debugging false classifications and for CAN-SPAM compliance proof (proving unsubscribe was processed).

**C3. Dedup:** Unique identifier = combination of `sender_email + message_id` (IMAP Message-ID header). This prevents processing the same reply twice if both IMAP polling and SmartLead webhook fire. Also deduplicate against suppression_list by email before any outbound action.

### Notifications

**C4. Who needs to know:** Just me (solo operator) for "interested" alerts. Later: sales team in Slack for team environments. Compliance officer for hostile/unsubscribe reports.

**C5. What they need to know:**
- **Instant alert:** "HOT LEAD: Sarah Chen (VP Marketing, Acme Corp) replied 'interested' to Campaign: SaaS-Directors-Q1. Reply: 'Yes, I'd love to learn more. Can you do Thursday at 2pm?'"
- **Instant alert (hostile):** "HOSTILE: john@badco.com on Campaign: Retail-Owners flagged as hostile. Auto-blacklisted. Reply excerpt: 'Stop emailing me or I will report you.'"
- **Daily summary:** "Today: 47 replies processed. 3 interested (alerts sent), 8 not interested, 2 unsubscribed (removed), 1 referral (new lead created), 28 out-of-office, 5 auto-replies."
- **Weekly digest:** "This week: 312 replies. 18 interested (3.6% of outbound). Campaign 'SaaS-Directors' has 5.2% interest rate (best). Campaign 'Retail-Owners' has 1.8% unsubscribe rate (investigate)."

**C6. How:** Telegram for instant "interested" and "hostile" alerts (time-critical). Telegram for daily summary. Email for weekly client reports if running as agency.

### Scheduling

**C7. When:**
- **Primary (IMAP polling):** Every 5 minutes during business hours (8am-8pm). Every 30 minutes overnight.
- **Alternative (SmartLead webhook):** Real-time — webhook listener runs continuously, processes replies as they arrive.
- **Daily summary:** Once per day at 7pm (after business hours).
- **Weekly report:** Monday 8am.

**C8. Failure recovery:** Resume from where it left off. Each reply is processed independently — if one fails, continue with the rest. The `last_processed_timestamp` per mailbox ensures no replies are skipped or double-processed after a crash.

**C9. Infrastructure:** Same VPS running the rest of the cold email pipeline. Hetzner or DigitalOcean, $6-12/month. Webhook listener needs a publicly accessible endpoint (use the existing server or set up a simple Express endpoint).

---

## Section D: Success Criteria (Filled Out)

**D1. Metrics:**

| Metric | Current (Manual) | Target (Automated) |
|---|---|---|
| Time from "interested" reply to sales alert | 1-6 hours (next manual inbox check) | < 5 minutes (automated classification + Telegram) |
| Time to process unsubscribe request | 1-24 hours | < 5 minutes |
| Replies processed per day (capacity) | 50 (human ceiling before fatigue errors) | 500+ (limited only by API rate limits) |
| Time spent reading/routing replies | 1-2 hours/day | 5 min/day (review Telegram alerts) |
| Missed referral leads | 2-3/week (buried in inbox) | 0 (auto-extracted and logged) |
| Classification accuracy | 90% (human, fatigued) | 95%+ (Claude Haiku, consistent) |
| Hostile replies caught before damage | 70% (missed during off-hours) | 100% (24/7 automated monitoring) |

**D2. Human cost:** 1-2 hours/day x 30 days = 30-60 hours/month. At $50/hour contractor rate = $1,500-3,000/month.

**D3. Budget:** Minimal. Claude Haiku classification: ~$0.002/reply x 50 replies/day x 30 days = ~$3/month. Supabase free tier covers the database. Telegram is free. VPS already exists. Total incremental cost: < $5/month.

**D4. MVP step:** Step 2 (AI Classification) + Step 3 (Action Routing for "interested" and "unsubscribe" only). These two categories have the highest urgency: interested replies lose value every minute, and unsubscribe failures have legal risk. Get those two routing correctly, then add the other categories.

---

## The 6-Step Architecture Map

```
SCHEDULE: Cron job — IMAP poll every 5 min OR SmartLead webhook listener (continuous)
    |
    v
INPUT: SmartLead webhook (push — preferred, near real-time)
       IMAP polling (pull — fallback, every 5 minutes)
       SmartLead API (campaign/prospect context for matching)
    |
    v
PROCESS:
    Step 1 — Ingestion: fetch new replies, deduplicate, match to campaign/prospect
    Step 2 — Classification: Claude Haiku classifies reply into 9 categories + confidence
    Step 3 — Routing: execute actions based on category (alert, suppress, pause, create lead)
    Step 4 — Reporting: aggregate daily/weekly stats, flag anomalous campaigns
    |
    v
OUTPUT: SmartLead API (pause/stop sequences for specific prospects)
        Supabase (new referral leads created from wrong-person replies)
        Telegram (instant alerts for interested + hostile)
    |
    v
STATE: Supabase tables:
    - reply_log (reply_id, sender_email, campaign_id, raw_text_hash, category, confidence, 
                 extracted_data, actions_taken, processed_at)
    - lead_status (lead_id, email, current_status, last_reply_category, updated_at)
    - suppression_list (email, reason, source_campaign, added_at) — shared with warmup system
    - referral_leads (id, referred_by_email, referred_name, referred_email, referred_role,
                      source_campaign, created_at, status)
    - daily_reply_stats (date, campaign_id, total_replies, interested, maybe, declined,
                         unsubscribed, referrals, hostile, ooo, auto_reply)
    - classification_events (id, reply_id, category, confidence, model_used, 
                             processing_time_ms, created_at)
    |
    v
NOTIFY: Telegram bot
    - Interested (confidence > 80%): instant alert with prospect name, company, reply excerpt
    - Interested (confidence 60-80%): instant alert with "REVIEW" flag
    - Hostile: instant alert + confirmation of auto-blacklist
    - Unsubscribe: silent (auto-processed, logged, no alert unless daily summary)
    - Daily 7pm: summary of all replies processed that day by category
    - Weekly Monday 8am: campaign performance breakdown with flagged anomalies
```

---

## Proof This Framework Works (Again)

We just took the second gap (reply classification) from the cold email system, ran it through the same wizard questionnaire, and produced:

1. A complete process breakdown (4 steps with inputs, outputs, decisions, error cases)
2. A full operations plan (state tracking, notifications, scheduling)
3. Success criteria with measurable targets
4. A 6-step architecture map ready to be turned into a CLAUDE.md build file

The reply classification gap is more complex than warmup because it involves AI judgment (Claude Haiku for classification), multiple output destinations (alerts, database, API calls), and time-critical routing (interested replies lose value by the minute). The framework handled this complexity the same way it handled the simpler warmup monitoring — by breaking it into discrete steps and mapping each to the 6-step pattern.

**Next step:** The CLAUDE-MD-REPLY-CLASSIFICATION.md build file turns this architecture into code specifications with function signatures, database schemas, and a build order.
