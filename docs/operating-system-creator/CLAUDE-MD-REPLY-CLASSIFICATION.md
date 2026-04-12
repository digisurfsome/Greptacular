# Reply Classification Engine — CLAUDE.md Build File

> **What this is:** Drop this file as CLAUDE.md into a project folder, run `claude`, and it builds the complete reply classification and routing system for cold email campaigns. This was produced BY the Operating System Creator framework as a proof of concept.

---

## Mission

Build a Node.js CLI system that monitors sending mailboxes for prospect replies, classifies each reply using Claude Haiku into 9 categories (interested, maybe, not interested, unsubscribe, wrong person/referral, out of office, hostile, bounce, auto-reply), executes the correct routing action for each category, and alerts via Telegram when high-priority replies arrive. It supports two input modes: IMAP polling (cron every 5 minutes) and a SmartLead webhook listener (real-time). It runs on a VPS alongside the rest of the cold email pipeline.

---

## API Keys Required

```
# .env file
ANTHROPIC_API_KEY=your_anthropic_api_key
SMARTLEAD_API_KEY=your_smartlead_api_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_service_role_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
WEBHOOK_PORT=3100
WEBHOOK_SECRET=your_webhook_secret
```

### How to get each key:

**Anthropic (Claude Haiku):** Sign up at console.anthropic.com > API Keys > Create Key. Claude Haiku (claude-3-5-haiku-latest) costs ~$0.25/MTok input, $1.25/MTok output. At ~500 tokens per classification, that's ~$0.001-0.003 per reply.

**SmartLead:** Log in > Settings > API > copy API key. Need Pro plan ($39/mo) for API access. Webhook URL is configured per campaign under Campaign > Settings > Webhook.

**Supabase:** Create project at supabase.com > Settings > API > copy Project URL and service_role key (not anon key).

**Telegram Bot:** Message @BotFather on Telegram > /newbot > copy token. Then message your bot, visit `https://api.telegram.org/bot<TOKEN>/getUpdates` to find your chat_id.

**Webhook Secret:** Generate your own with `node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"`. Used to verify incoming SmartLead webhook payloads.

---

## Tech Stack

```json
{
  "dependencies": {
    "dotenv": "^16.0.0",
    "@anthropic-ai/sdk": "^0.30.0",
    "@supabase/supabase-js": "^2.0.0",
    "node-fetch": "2",
    "express": "^4.18.0",
    "imapflow": "^1.0.0",
    "mailparser": "^3.6.0",
    "commander": "^11.0.0",
    "cli-table3": "^0.6.0",
    "dayjs": "^1.11.0"
  }
}
```

Runtime: Node.js 18+

**Why these packages:**
- `imapflow` — Modern IMAP client with IDLE support (better than raw `imaplib`, handles connection pooling)
- `mailparser` — Parses raw email into structured objects (headers, body, attachments)
- `express` — Minimal HTTP server for SmartLead webhook listener
- `dayjs` — Lightweight date parsing for out-of-office return dates
- `@anthropic-ai/sdk` — Official Anthropic SDK for Claude Haiku calls

---

## Database Schema

Create these tables in Supabase before running:

```sql
-- Processed replies with classification results
CREATE TABLE reply_log (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  message_id TEXT UNIQUE NOT NULL,
  sender_email TEXT NOT NULL,
  sender_name TEXT,
  campaign_id TEXT,
  prospect_id TEXT,
  subject TEXT,
  body_text TEXT,
  body_hash TEXT NOT NULL,
  category TEXT NOT NULL CHECK (category IN (
    'interested', 'maybe', 'not_interested', 'unsubscribe',
    'wrong_person', 'out_of_office', 'hostile', 'bounce', 'auto_reply',
    'classification_failed'
  )),
  confidence INTEGER DEFAULT 0 CHECK (confidence >= 0 AND confidence <= 100),
  extracted_data JSONB DEFAULT '{}',
  reasoning TEXT,
  actions_taken JSONB DEFAULT '[]',
  source TEXT CHECK (source IN ('imap', 'webhook')),
  mailbox_email TEXT NOT NULL,
  model_used TEXT DEFAULT 'claude-3-5-haiku-latest',
  processing_time_ms INTEGER,
  processed_at TIMESTAMPTZ DEFAULT now(),
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_reply_log_sender ON reply_log(sender_email);
CREATE INDEX idx_reply_log_category ON reply_log(category, created_at DESC);
CREATE INDEX idx_reply_log_campaign ON reply_log(campaign_id, created_at DESC);
CREATE INDEX idx_reply_log_message_id ON reply_log(message_id);

-- Lead status tracking (updated by classification actions)
CREATE TABLE lead_status (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  company TEXT,
  current_status TEXT DEFAULT 'contacted' CHECK (current_status IN (
    'new', 'contacted', 'replied', 'interested', 'booked',
    'declined', 'unsubscribed', 'blacklisted', 'nurture'
  )),
  last_reply_category TEXT,
  last_reply_at TIMESTAMPTZ,
  campaign_id TEXT,
  updated_at TIMESTAMPTZ DEFAULT now(),
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_lead_status_email ON lead_status(email);
CREATE INDEX idx_lead_status_status ON lead_status(current_status);

-- Referral leads extracted from "wrong person" replies
CREATE TABLE referral_leads (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  referred_by_email TEXT NOT NULL,
  referred_by_name TEXT,
  referred_name TEXT,
  referred_email TEXT,
  referred_role TEXT,
  referred_company TEXT,
  source_campaign TEXT,
  source_reply_id UUID REFERENCES reply_log(id),
  status TEXT DEFAULT 'new' CHECK (status IN ('new', 'contacted', 'converted', 'declined')),
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_referral_leads_email ON referral_leads(referred_email);

-- Suppression list — never email these addresses again (shared with warmup system)
CREATE TABLE IF NOT EXISTS suppression_list (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  reason TEXT CHECK (reason IN ('unsubscribe', 'hostile', 'hard_bounce', 'soft_permanent', 'spam_complaint', 'manual')),
  source_campaign TEXT,
  source_mailbox TEXT,
  added_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_suppression_email ON suppression_list(email);

-- Daily reply statistics per campaign
CREATE TABLE daily_reply_stats (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  stat_date DATE DEFAULT CURRENT_DATE,
  campaign_id TEXT,
  campaign_name TEXT,
  total_replies INTEGER DEFAULT 0,
  interested INTEGER DEFAULT 0,
  maybe INTEGER DEFAULT 0,
  not_interested INTEGER DEFAULT 0,
  unsubscribed INTEGER DEFAULT 0,
  wrong_person INTEGER DEFAULT 0,
  out_of_office INTEGER DEFAULT 0,
  hostile INTEGER DEFAULT 0,
  bounce INTEGER DEFAULT 0,
  auto_reply INTEGER DEFAULT 0,
  classification_failed INTEGER DEFAULT 0,
  avg_confidence DECIMAL DEFAULT 0,
  UNIQUE(stat_date, campaign_id)
);

-- Classification event log for audit trail and debugging
CREATE TABLE classification_events (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  reply_id UUID REFERENCES reply_log(id),
  event_type TEXT NOT NULL,
  severity TEXT CHECK (severity IN ('info', 'warning', 'critical')),
  details JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_classification_events_reply ON classification_events(reply_id, created_at DESC);
CREATE INDEX idx_classification_events_severity ON classification_events(severity, created_at DESC);

-- IMAP polling state (tracks last-checked timestamp per mailbox)
CREATE TABLE mailbox_poll_state (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  mailbox_email TEXT UNIQUE NOT NULL,
  imap_host TEXT NOT NULL,
  imap_port INTEGER DEFAULT 993,
  imap_user TEXT NOT NULL,
  imap_pass_encrypted TEXT NOT NULL,
  last_uid INTEGER DEFAULT 0,
  last_checked TIMESTAMPTZ,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## Pipeline Architecture

```
reply-classifier.js check          <-- Runs every 5 min via cron (IMAP mode)
  |
  +-- Step 1: ingest-replies         (IMAP poll all mailboxes for new replies)
  +-- Step 2: classify               (Claude Haiku classifies each reply)
  +-- Step 3: route-actions          (execute actions per category)
  +-- Step 4: report                 (daily summary to Telegram)

reply-classifier.js webhook        <-- Runs continuously (webhook mode)
  |
  +-- Express server on port 3100
  +-- POST /webhook/smartlead       (receives SmartLead reply notifications)
  +-- Same Steps 2-4 as above

reply-classifier.js add-mailbox <email> <imap_host> <imap_user> <imap_pass>
reply-classifier.js list-mailboxes
reply-classifier.js status
reply-classifier.js report [--weekly]
reply-classifier.js reprocess <reply_id>
reply-classifier.js test-classify "<reply text>"
```

---

## File Structure

```
reply-classifier/
+-- .env
+-- package.json
+-- CLAUDE.md                    (this file)
+-- src/
|   +-- config.js                (env validation + constants + thresholds)
|   +-- db.js                    (Supabase client + query helpers)
|   +-- imap.js                  (IMAP connection + reply fetching)
|   +-- webhook.js               (Express server + SmartLead webhook handler)
|   +-- classifier.js            (Claude Haiku classification logic + prompt)
|   +-- router.js                (action routing per category)
|   +-- smartlead.js             (SmartLead API — pause/stop sequences)
|   +-- notify.js                (Telegram notifications)
|   +-- report.js                (daily/weekly stats + CLI tables)
|   +-- referrals.js             (referral lead extraction + creation)
|   +-- suppression.js           (suppression list management)
|   +-- utils.js                 (date parsing, text hashing, dedup helpers)
+-- reply-classifier.js          (main CLI entry point)
+-- cron-setup.sh                (crontab installer)
```

---

## Module Specifications

### src/config.js
- Load .env with dotenv
- Validate all required env vars exist, exit with clear error if any missing
- Export constants:
  - `CONFIDENCE_HIGH = 80` — auto-route threshold
  - `CONFIDENCE_REVIEW = 60` — flag for human review threshold
  - `UNSUBSCRIBE_RATE_WARNING = 0.02` — flag campaign if > 2% unsubs
  - `HOSTILE_RATE_WARNING = 0.01` — flag campaign if > 1% hostile
  - `IMAP_POLL_INTERVAL_MS = 300000` — 5 minutes
  - `IMAP_POLL_INTERVAL_NIGHT_MS = 1800000` — 30 minutes (10pm-7am)
  - `MAX_REPLY_LENGTH = 5000` — truncate reply text beyond this for classification
  - `CLASSIFICATION_TIMEOUT_MS = 10000` — max wait for Haiku response
  - `WEBHOOK_PORT = 3100`
  - `BUSINESS_HOURS = { start: 8, end: 20 }` — for polling interval logic

### src/db.js
- Create Supabase client
- Helper functions:
  - `isReplyProcessed(messageId)` — check reply_log for existing message_id (dedup)
  - `saveReply(replyData)` — insert into reply_log
  - `updateLeadStatus(email, status, category)` — upsert lead_status
  - `getLeadByEmail(email)` — fetch lead record
  - `addToSuppressionList(email, reason, source)` — insert into suppression_list
  - `isOnSuppressionList(email)` — check if email exists in suppression_list
  - `createReferralLead(referralData)` — insert into referral_leads
  - `getMailboxPollStates()` — get all active mailboxes with IMAP credentials
  - `updatePollState(mailboxEmail, lastUid)` — update last processed UID
  - `saveDailyStats(campaignId, stats)` — upsert daily_reply_stats
  - `getDailyStats(date)` — get all campaign stats for a date
  - `getWeeklyStats()` — get last 7 days of stats
  - `logEvent(replyId, eventType, severity, details)` — insert classification_events

### src/imap.js
- Use `imapflow` package for IMAP connections
- Function: `connectToMailbox(credentials)`:
  - Creates ImapFlow client with host, port, auth
  - Handles connection errors gracefully
  - Returns connected client
- Function: `fetchNewReplies(client, lastUid)`:
  - Select INBOX
  - Search for messages with UID > lastUid
  - For each message: fetch full RFC822 content
  - Parse with `mailparser` (simpleParser)
  - Filter OUT: messages from mailer-daemon, messages with `Auto-Submitted` header (except "no"), messages where sender matches the mailbox itself
  - Return array of: `{ messageId, uid, from: { email, name }, subject, textBody, htmlBody, date, inReplyTo, references }`
- Function: `getHighestUid(client)`:
  - Get the highest UID in INBOX (for initial state setup)
- Rate limit: process one mailbox at a time (sequential, not parallel IMAP connections)

### src/webhook.js
- Create Express server on `WEBHOOK_PORT`
- Middleware: verify webhook secret (compare `x-webhook-secret` header against `WEBHOOK_SECRET`)
- Route: `POST /webhook/smartlead`:
  - Parse incoming JSON payload
  - Extract: `{ leadEmail, leadName, replyText, campaignId, campaignName, emailAccountId }`
  - SmartLead webhook payload fields: `to_email`, `from_email`, `reply_message_body`, `campaign_id`, `email_account_id`, `message_id`
  - Check dedup: has this message_id been processed?
  - If new: pass to classifier, then router
  - Respond 200 immediately, process asynchronously
- Route: `GET /health` — returns `{ status: 'ok', uptime, repliesProcessed }`
- Function: `startWebhookServer()`:
  - Start Express server
  - Log: "Webhook listener running on port {PORT}"
  - Returns server instance (for graceful shutdown)

### src/classifier.js
- Use `@anthropic-ai/sdk` for Claude Haiku calls
- Function: `classifyReply(replyText, originalSubject)`:
  - Truncate replyText to MAX_REPLY_LENGTH
  - Call Claude Haiku with the classification prompt (see below)
  - Parse structured JSON response
  - Return: `{ category, confidence, extractedData, reasoning, processingTimeMs }`
  - If API error: retry once after 5 seconds
  - If second failure: return `{ category: 'classification_failed', confidence: 0, reasoning: 'API error' }`

**Classification Prompt (exact prompt to use):**

```
You are an email reply classifier for a cold outreach system. Classify the following email reply into exactly ONE category.

CATEGORIES:
1. "interested" — The person wants to talk, learn more, schedule a call, asks questions about the product/service, or gives any positive buying signal. Examples: "Yes, tell me more", "Can we schedule a call?", "What's the pricing?", "Send me a proposal"
2. "maybe" — Soft interest but not committed. Wants more info before deciding, says "not right now but maybe later", asks to follow up in the future. Examples: "Send me some case studies", "Check back in Q3", "Interesting but we just signed a contract"
3. "not_interested" — Clear decline but not hostile. Says no politely. Examples: "No thanks", "We're all set", "Not a fit", "We already use X", "Not looking for this right now"
4. "unsubscribe" — Explicitly asks to stop receiving emails, be removed from list, or unsubscribe. ANY request to stop contact goes here, even if politely worded. Examples: "Please remove me", "Unsubscribe", "Stop emailing me", "Take me off your list"
5. "wrong_person" — Says they're not the right contact, refers you to someone else, provides another person's name/email/role. Examples: "I don't handle this, try Sarah in marketing", "You should reach out to our procurement team", "I'm not the decision maker"
6. "out_of_office" — Auto-reply indicating the person is away, on vacation, on leave. Usually contains a return date. Examples: "I am out of the office until January 15th", "Currently on PTO, returning Monday"
7. "hostile" — Angry, threatening, or abusive. Threatens to report as spam, uses profanity, threatens legal action. Examples: "Stop spamming me or I'll report you", "This is spam", "I'm forwarding this to the FTC"
8. "bounce" — Delivery failure notification. Email could not be delivered. Contains SMTP error codes (550, 551, etc.) or phrases like "undeliverable", "mailbox not found", "user unknown"
9. "auto_reply" — Generic automated response that is NOT out-of-office and NOT a bounce. Examples: "Thank you for your email, someone will respond shortly", "This mailbox is not monitored", "Your message has been received"

RULES:
- If the reply contains BOTH a decline and a referral (e.g., "I'm not interested but try my colleague John at john@co.com"), classify as "wrong_person" — the referral is more actionable than the decline.
- If the reply is ambiguous between "interested" and "maybe", lean toward "maybe" unless there's a clear call-to-action (scheduling, pricing request).
- If the reply contains the word "unsubscribe", "remove", or "stop" in the context of not wanting emails, ALWAYS classify as "unsubscribe" regardless of other content.
- Confidence score must be 0-100. Use 90-100 for obvious cases, 70-89 for clear but not trivial cases, 50-69 for ambiguous cases.

EXTRACTION RULES:
- For "wrong_person": extract { referredName, referredEmail, referredRole } if mentioned. Set to null if not found.
- For "out_of_office": extract { returnDate } in ISO 8601 format (YYYY-MM-DD). Set to null if no date found.
- For "interested": extract { requestedAction } — what they want (call, demo, pricing, info). Set to null if not specific.
- For all other categories: extractedData should be {}.

Respond with ONLY valid JSON, no markdown, no explanation outside the JSON:
{
  "category": "one_of_the_9_categories",
  "confidence": 85,
  "extractedData": {},
  "reasoning": "One sentence explaining why this category was chosen"
}

EMAIL SUBJECT: {{subject}}

EMAIL REPLY:
{{replyText}}
```

- Function: `testClassify(replyText)`:
  - Same as classifyReply but prints the full prompt, response, and timing to stdout
  - Used for manual testing via CLI

### src/router.js
- Function: `routeReply(classification, replyData)`:
  - Master routing function — takes classification result and original reply data
  - Calls the appropriate action function based on category
  - Returns: `{ actions: [...actionsExecuted], errors: [...anyErrors] }`

- Function: `routeInterested(classification, replyData)`:
  - If confidence >= CONFIDENCE_HIGH (80):
    - Update lead status to "interested"
    - Pause sequence in SmartLead for this prospect
    - Send Telegram alert: "HOT LEAD: {name} ({company}) — '{excerpt}' — Campaign: {campaign}"
    - Log event: severity = 'critical' (critical = needs human attention, not an error)
  - If confidence >= CONFIDENCE_REVIEW (60) and < CONFIDENCE_HIGH:
    - Update lead status to "replied"
    - Send Telegram alert with "REVIEW" prefix
    - Log event: severity = 'warning'
  - If confidence < CONFIDENCE_REVIEW:
    - Log as classification_failed for manual review
    - Send no alert

- Function: `routeUnsubscribe(classification, replyData)`:
  - Add email to suppression_list with reason = 'unsubscribe'
  - Stop ALL sequences for this prospect in SmartLead
  - Update lead status to "unsubscribed"
  - Log event: severity = 'info'
  - NO confidence check — any unsubscribe classification triggers removal (CAN-SPAM compliance)

- Function: `routeNotInterested(classification, replyData)`:
  - Update lead status to "declined"
  - Stop sequence in SmartLead for this prospect
  - Log event: severity = 'info'

- Function: `routeMaybe(classification, replyData)`:
  - Update lead status to "nurture"
  - Pause (not stop) sequence in SmartLead
  - Log event: severity = 'info'

- Function: `routeWrongPerson(classification, replyData)`:
  - Stop sequence for original prospect
  - Update lead status to "declined" (for the original prospect)
  - If extractedData has referredEmail or referredName:
    - Create referral lead record
    - Send Telegram alert: "REFERRAL: {originalName} referred {referredName} ({referredEmail}) — Campaign: {campaign}"
  - Log event: severity = 'info'

- Function: `routeOutOfOffice(classification, replyData)`:
  - If extractedData.returnDate exists:
    - Parse return date with dayjs
    - Log the return date for future scheduling (the sequence management system handles rescheduling)
  - Do NOT stop the sequence — SmartLead handles OOO pausing natively
  - Log event: severity = 'info'

- Function: `routeHostile(classification, replyData)`:
  - Add email to suppression_list with reason = 'hostile'
  - Add entire domain to suppression_list (e.g., if john@acme.com is hostile, suppress *@acme.com) — BUT only if this is the first contact at that domain. If multiple contacts at that domain exist, suppress only the individual.
  - Stop ALL sequences for this prospect in SmartLead
  - Update lead status to "blacklisted"
  - Send Telegram alert: "HOSTILE: {email} — auto-blacklisted. Reply: '{excerpt}'"
  - Log event: severity = 'critical'

- Function: `routeBounce(classification, replyData)`:
  - Route to the warmup system's bounce handler (if integrated)
  - Add to suppression_list with reason = 'hard_bounce'
  - Log event: severity = 'warning'

- Function: `routeAutoReply(classification, replyData)`:
  - No action — keep sequence running
  - Log event: severity = 'info'
  - Do NOT send any notification

### src/smartlead.js
- Base URL: `https://server.smartlead.ai/api/v1`
- All requests append `?api_key=${API_KEY}` as query parameter
- Function: `pauseSequenceForLead(campaignId, leadEmail)` — POST `/campaigns/${campaignId}/leads/pause` — pauses the sequence for a specific lead
- Function: `stopSequenceForLead(campaignId, leadEmail)` — POST `/campaigns/${campaignId}/leads/remove` — removes lead from campaign (stops all future emails)
- Function: `getLeadByCampaign(campaignId, leadEmail)` — GET `/campaigns/${campaignId}/leads?email=${leadEmail}` — find lead record in SmartLead
- Function: `getAllCampaigns()` — GET `/campaigns` — list all campaigns (for matching replies to campaigns)
- Function: `getCampaignLeads(campaignId)` — GET `/campaigns/${campaignId}/leads` — list all leads in a campaign
- Rate limit: max 2 requests per second, add 500ms delay between calls

### src/notify.js
- Function: `sendTelegram(message)` — POST to `https://api.telegram.org/bot${TOKEN}/sendMessage` with chat_id and text (parse_mode: 'HTML')
- Function: `sendInterestedAlert(replyData, classification)`:
  - Format: "<b>HOT LEAD</b>\n{name} ({company})\nCampaign: {campaign}\nConfidence: {confidence}%\n\nReply:\n<i>{excerpt (first 200 chars)}</i>"
  - If confidence 60-80: prefix with "REVIEW — "
- Function: `sendHostileAlert(replyData, classification)`:
  - Format: "<b>HOSTILE — AUTO-BLACKLISTED</b>\n{email}\nCampaign: {campaign}\n\nExcerpt:\n<i>{excerpt (first 200 chars)}</i>"
- Function: `sendReferralAlert(replyData, referralData)`:
  - Format: "<b>REFERRAL</b>\nFrom: {originalName}\nReferred: {referredName} ({referredEmail})\nRole: {referredRole}\nCampaign: {campaign}"
- Function: `sendDailySummary(stats)`:
  - Format: "<b>Daily Reply Report — {date}</b>\nTotal: {total}\nInterested: {interested}\nMaybe: {maybe}\nDeclined: {declined}\nUnsubscribed: {unsubscribed}\nReferrals: {referrals}\nHostile: {hostile}\nOOO: {ooo}\nAuto-reply: {autoReply}\nFailed: {failed}"
- Function: `sendWeeklySummary(weeklyStats)`:
  - Per-campaign breakdown with interest rate and unsubscribe rate
  - Flag campaigns with unsubscribe rate > 2% or hostile rate > 1%
- Max message length: 4096 chars. If longer, split into multiple messages.

### src/report.js
- Function: `printStatusTable()`:
  - Use cli-table3 to show recent replies with columns: Time | From | Category | Confidence | Campaign | Actions
  - Color-code: green for interested, yellow for maybe, red for hostile/unsubscribe, cyan for referral
  - Default: show last 50 replies
- Function: `printCampaignStats(date)`:
  - Query daily_reply_stats for given date
  - Show per-campaign breakdown with columns: Campaign | Total | Interested | Maybe | Declined | Unsub | Hostile | Interest%
  - Flag anomalies with warning symbols
- Function: `generateDailySummary()`:
  - Aggregate all reply_log entries for today
  - Group by campaign_id
  - Calculate per-campaign stats
  - Save to daily_reply_stats
  - Format for both CLI and Telegram
  - Return stats object
- Function: `generateWeeklyReport()`:
  - Query daily_reply_stats for last 7 days
  - Calculate trends: improving/declining interest rates, rising unsubscribe rates
  - Identify best-performing campaign (highest interest rate)
  - Identify worst-performing campaign (highest unsub/hostile rate)
  - Format as both CLI table and Telegram message

### src/referrals.js
- Function: `extractReferralInfo(extractedData, replyText)`:
  - If classifier extracted referredEmail: use it directly
  - If classifier extracted referredName but no email: log as partial referral (human needs to find the email)
  - If neither: attempt regex extraction from replyText for email patterns
  - Return: `{ referredName, referredEmail, referredRole, referredCompany, isComplete }`
- Function: `createReferral(referralInfo, sourceReplyId, sourceCampaign)`:
  - Insert into referral_leads table
  - Check suppression_list for referredEmail (don't create lead if suppressed)
  - Return the created referral record

### src/suppression.js
- Function: `suppress(email, reason, sourceCampaign, sourceMailbox)`:
  - Normalize email to lowercase
  - Check if already suppressed (skip if yes)
  - Insert into suppression_list
  - Return: `{ suppressed: true, alreadyExists: false }` or `{ suppressed: false, alreadyExists: true }`
- Function: `suppressDomain(domain, reason)`:
  - Extract domain from email
  - Count how many contacts exist at this domain in lead_status
  - If count <= 1: suppress `*@{domain}` pattern
  - If count > 1: suppress only the individual email, log warning that other contacts at this domain are active
  - Return: `{ domainSuppressed: true|false, reason }`
- Function: `checkSuppressed(email)`:
  - Check exact email match
  - Check domain wildcard match
  - Return: `{ suppressed: true|false, reason, addedAt }`
- Function: `getSuppressionStats()`:
  - Count by reason: unsubscribe, hostile, hard_bounce, etc.
  - Return summary object

### src/utils.js
- Function: `hashText(text)` — SHA-256 hash of reply text (for storage instead of full body)
- Function: `truncateForClassification(text, maxLength)` — smart truncation that preserves the beginning and end of the email (where intent signals usually are)
- Function: `extractEmailFromText(text)` — regex to find email addresses in free text (for referral extraction)
- Function: `parseReturnDate(text)` — parse natural language dates ("January 15th", "next Monday", "1/15") into ISO 8601 using dayjs
- Function: `isBusinessHours()` — check if current time is within BUSINESS_HOURS (for poll interval selection)
- Function: `excerptForAlert(text, maxLength)` — clean excerpt for Telegram alerts: strip signatures, quoted text, HTML tags, limit to maxLength chars
- Function: `normalizeEmail(email)` — lowercase, trim whitespace

### reply-classifier.js (main CLI)
- Use commander for subcommands:
  - `check` — Run full IMAP poll pipeline (Steps 1-4). Default command.
  - `webhook` — Start the webhook listener server (runs continuously).
  - `add-mailbox <email> <imap_host> <imap_user> <imap_pass>` — Register a mailbox for IMAP polling. Encrypts IMAP password before storing.
  - `list-mailboxes` — Show all registered mailboxes with last-checked timestamps.
  - `status` — Print table of recent reply classifications.
  - `report` — Generate and display daily report.
  - `report --weekly` — Generate and display weekly report.
  - `test-classify "<reply text>"` — Classify a reply manually and show the full result (for testing/debugging).
  - `reprocess <reply_id>` — Re-classify a specific reply (if the first classification was wrong).
  - `suppress <email> [reason]` — Manually add an email to the suppression list.
  - `suppression-stats` — Show suppression list statistics.
  - `referrals` — Show all referral leads with their status.

### cron-setup.sh
```bash
#!/bin/bash
# Add reply classification check to crontab
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# IMAP polling every 5 minutes during business hours (8am-8pm)
(crontab -l 2>/dev/null; echo "*/5 8-20 * * * cd $SCRIPT_DIR && node reply-classifier.js check >> logs/classifier.log 2>&1") | sort -u | crontab -

# IMAP polling every 30 minutes overnight (off-hours)
(crontab -l 2>/dev/null; echo "*/30 0-7,21-23 * * * cd $SCRIPT_DIR && node reply-classifier.js check >> logs/classifier.log 2>&1") | sort -u | crontab -

# Daily summary at 7pm
(crontab -l 2>/dev/null; echo "0 19 * * * cd $SCRIPT_DIR && node reply-classifier.js report >> logs/classifier.log 2>&1") | sort -u | crontab -

# Weekly report Monday 8am
(crontab -l 2>/dev/null; echo "0 8 * * 1 cd $SCRIPT_DIR && node reply-classifier.js report --weekly >> logs/classifier.log 2>&1") | sort -u | crontab -

# Create logs directory
mkdir -p "$SCRIPT_DIR/logs"

echo "Cron jobs installed:"
echo "  - IMAP poll: every 5 min (8am-8pm), every 30 min (overnight)"
echo "  - Daily summary: 7pm daily"
echo "  - Weekly report: Monday 8am"
echo ""
echo "For real-time processing, use the webhook listener instead:"
echo "  node reply-classifier.js webhook"
```

---

## Rules

1. **Never skip classification.** Every reply gets classified, even if it looks obvious. The audit trail requires a classification record for every processed reply.
2. **Unsubscribe is non-negotiable.** ANY classification of "unsubscribe" triggers immediate removal, regardless of confidence score. CAN-SPAM compliance is not optional. No human review gate on unsubscribes.
3. **Hostile triggers domain review.** A hostile classification doesn't just suppress the individual — it triggers a check of how many contacts at that domain are in active sequences. If it's the only contact, suppress the entire domain.
4. **Dedup before classify.** Always check message_id against reply_log before sending to Claude Haiku. Duplicate classifications waste money and can trigger duplicate alerts.
5. **Never store raw reply bodies long-term.** Store a SHA-256 hash for dedup, and a truncated excerpt for alert context. Full reply text is processed in memory and discarded. This protects PII and reduces storage.
6. **Rate limit Haiku calls.** Max 10 concurrent classification requests. Add 200ms between sequential calls. Claude Haiku is fast but rate limits apply.
7. **Low confidence = human review.** If Claude returns confidence < 60%, do NOT auto-route. Log as "classification_failed" and include the reply in the daily summary for human review.
8. **Referrals are gold.** Wrong-person replies with a referral contact should trigger a Telegram alert, not be silently logged. These are warm leads.
9. **Suppression list is permanent.** Once on the list, never removed programmatically. Manual `suppress` command exists for adding. No `unsuppress` command — if needed, remove directly from Supabase (deliberate friction).
10. **Log everything.** Every classification, every action, every error gets a row in classification_events. This is the compliance audit trail.

---

## Testing Checklist

1. [ ] `node reply-classifier.js test-classify "Yes, I'd love to learn more. Can we do a call Thursday?"` — should return `interested`, confidence > 85
2. [ ] `node reply-classifier.js test-classify "Please remove me from your mailing list"` — should return `unsubscribe`, confidence > 90
3. [ ] `node reply-classifier.js test-classify "I'm not the right person for this. Try reaching out to Sarah Chen, our VP of Marketing — sarah.chen@acme.com"` — should return `wrong_person`, extractedData should contain referredEmail
4. [ ] `node reply-classifier.js test-classify "I am out of the office until January 15th with limited access to email."` — should return `out_of_office`, extractedData should contain returnDate = "2025-01-15"
5. [ ] `node reply-classifier.js test-classify "Stop emailing me. I've reported you as spam."` — should return `hostile`, confidence > 85
6. [ ] `node reply-classifier.js test-classify "Thanks but we're not looking for this right now"` — should return `not_interested`, confidence > 75
7. [ ] `node reply-classifier.js test-classify "Thank you for your email. Someone from our team will get back to you shortly."` — should return `auto_reply`, confidence > 80
8. [ ] `node reply-classifier.js test-classify "Interesting, but we just signed a 2-year contract with a competitor. Check back in Q1 2026."` — should return `maybe`, confidence > 70
9. [ ] `node reply-classifier.js add-mailbox test@testdomain.com imap.gmail.com test@testdomain.com password123` — creates mailbox poll state record
10. [ ] `node reply-classifier.js list-mailboxes` — shows the test mailbox with last-checked = never
11. [ ] `node reply-classifier.js check` — runs full IMAP poll pipeline, processes any replies, sends Telegram summary
12. [ ] `node reply-classifier.js webhook` — starts Express server on port 3100, `GET /health` returns OK
13. [ ] Send test POST to `http://localhost:3100/webhook/smartlead` with valid payload — reply is classified and routed
14. [ ] Verify dedup: process the same reply twice — second time should skip with "already processed" log
15. [ ] Verify suppression: classify an "unsubscribe" reply, then check suppression_list contains the email
16. [ ] Verify referral: classify a "wrong_person" reply with an email, then check referral_leads table
17. [ ] `node reply-classifier.js status` — shows table of recent classifications
18. [ ] `node reply-classifier.js report` — generates daily summary, sends to Telegram
19. [ ] `node reply-classifier.js report --weekly` — generates weekly report with campaign breakdown
20. [ ] Check cron is installed: `crontab -l` should show the classifier entries
21. [ ] Let it run for 24 hours, verify daily summary arrives at 7pm via Telegram

---

## Build Order

Tell Claude: Build in this exact order, testing each module before moving to the next.

1. `src/config.js` + `src/db.js` + `src/utils.js` — foundation, test with `node -e "require('./src/db')"`
2. `src/notify.js` — test by sending a test Telegram message
3. `src/classifier.js` — test with `test-classify` command using all 9 category examples
4. `src/suppression.js` — test by adding and checking a suppressed email
5. `src/referrals.js` — test referral extraction from sample reply text
6. `src/smartlead.js` — test by listing campaigns
7. `src/router.js` — test each routing function with mock classification results
8. `src/imap.js` — test IMAP connection and reply fetching with one mailbox
9. `src/webhook.js` — test Express server starts, health endpoint works, test payload processes
10. `src/report.js` — test status table and daily summary generation
11. `reply-classifier.js` — wire it all together with commander
12. `cron-setup.sh` — install and verify cron jobs
