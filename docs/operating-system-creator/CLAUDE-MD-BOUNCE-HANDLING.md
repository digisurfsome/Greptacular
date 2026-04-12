# Email Bounce Handler — CLAUDE.md Build File

> **What this is:** Drop this file as CLAUDE.md into a project folder, run `claude`, and it builds the complete email bounce handling system. This was produced BY the Operating System Creator framework as a proof of concept.

---

## Mission

Build a Node.js CLI system that scans sending mailbox inboxes for bounce-back emails, classifies them (hard/soft/auto-reply), maintains a suppression list of addresses that must never be emailed again, tracks bounce rates per mailbox and domain, and auto-pauses mailboxes that exceed safe thresholds. It runs on a cron schedule every 4 hours on a VPS and alerts via Telegram when issues arise.

---

## API Keys Required

```
# .env file
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_service_role_key
SMARTLEAD_API_KEY=your_smartlead_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### How to get each key:

**Supabase:** Create project at supabase.com > Settings > API > copy Project URL and service_role key (not anon key). Use the same Supabase instance as the warmup manager — they share the database.

**SmartLead:** Log in > Settings > API > copy API key. Need Pro plan ($39/mo) for API access.

**Anthropic (Claude Haiku):** Go to console.anthropic.com > API Keys > create a new key. Claude Haiku is used for classifying ambiguous bounce messages. Cost: ~$0.001 per classification, typically $2-5/month total.

**Telegram Bot:** Message @BotFather on Telegram > /newbot > copy token. Then message your bot, visit `https://api.telegram.org/bot<TOKEN>/getUpdates` to find your chat_id.

### IMAP Credentials

IMAP credentials for each sending mailbox are stored in the Supabase `mailbox_imap_credentials` table (not in .env — there are too many mailboxes for env vars). Each mailbox record contains:
- `email`: the mailbox address (e.g., mike@cenra.io)
- `imap_host`: the IMAP server (e.g., imap.gmail.com)
- `imap_port`: the IMAP port (993 for SSL)
- `imap_user`: the login username (usually same as email)
- `imap_password`: the app-specific password (for Google Workspace: Admin > Security > App Passwords)

---

## Tech Stack

```json
{
  "dependencies": {
    "dotenv": "^16.0.0",
    "@supabase/supabase-js": "^2.0.0",
    "@anthropic-ai/sdk": "^0.30.0",
    "node-fetch": "2",
    "imap": "^0.8.19",
    "mailparser": "^3.6.0",
    "commander": "^11.0.0",
    "cli-table3": "^0.6.0"
  }
}
```

Runtime: Node.js 18+

**Why these packages:**
- `imap`: IMAP client for connecting to mailboxes and fetching bounce messages
- `mailparser`: Parses raw email messages (MIME format) into structured objects with headers, body, attachments
- `@anthropic-ai/sdk`: Claude Haiku API for classifying ambiguous bounce messages
- Everything else matches the warmup manager stack

---

## Database Schema

Create these tables in Supabase before running:

```sql
-- IMAP credentials for each sending mailbox
-- Store here instead of .env because there are 10-20+ mailboxes
CREATE TABLE mailbox_imap_credentials (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  imap_host TEXT NOT NULL DEFAULT 'imap.gmail.com',
  imap_port INTEGER NOT NULL DEFAULT 993,
  imap_user TEXT NOT NULL,
  imap_password TEXT NOT NULL,
  is_active BOOLEAN DEFAULT true,
  last_scan_at TIMESTAMPTZ,
  last_scan_message_uid INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Suppression list — addresses that must NEVER be emailed again
-- This is the most important table in the system
CREATE TABLE suppression_list (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  bounce_type TEXT NOT NULL CHECK (bounce_type IN ('hard', 'soft_permanent', 'spam_complaint')),
  smtp_code TEXT,
  smtp_message TEXT,
  source_mailbox TEXT,
  source_campaign TEXT,
  detected_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_suppression_email ON suppression_list(email);

-- Every individual bounce detected — the raw event log
CREATE TABLE bounce_log (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  recipient_email TEXT NOT NULL,
  bounce_type TEXT NOT NULL CHECK (bounce_type IN ('hard', 'soft', 'auto_reply', 'out_of_office', 'unknown')),
  smtp_code TEXT,
  smtp_message TEXT,
  source_mailbox TEXT NOT NULL,
  campaign_id TEXT,
  raw_message_id TEXT UNIQUE,
  classification_method TEXT CHECK (classification_method IN ('rules', 'haiku', 'smartlead')),
  classification_confidence DECIMAL DEFAULT 1.0,
  detected_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_bounce_log_recipient ON bounce_log(recipient_email);
CREATE INDEX idx_bounce_log_source ON bounce_log(source_mailbox, detected_at DESC);

-- Per-mailbox bounce rate tracking
CREATE TABLE mailbox_bounce_stats (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  mailbox_email TEXT UNIQUE NOT NULL,
  total_sent INTEGER DEFAULT 0,
  total_bounced INTEGER DEFAULT 0,
  hard_bounces INTEGER DEFAULT 0,
  soft_bounces INTEGER DEFAULT 0,
  bounce_rate DECIMAL DEFAULT 0,
  status TEXT DEFAULT 'healthy' CHECK (status IN ('healthy', 'warning', 'critical', 'paused')),
  last_scan_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Per-domain aggregate bounce rate tracking
CREATE TABLE domain_bounce_stats (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  domain TEXT UNIQUE NOT NULL,
  total_sent INTEGER DEFAULT 0,
  total_bounced INTEGER DEFAULT 0,
  bounce_rate DECIMAL DEFAULT 0,
  status TEXT DEFAULT 'healthy' CHECK (status IN ('healthy', 'warning', 'critical')),
  last_updated TIMESTAMPTZ DEFAULT now()
);

-- Soft bounce retry tracking — soft bounces get one retry before suppression
CREATE TABLE soft_bounce_retries (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email TEXT NOT NULL,
  source_mailbox TEXT NOT NULL,
  first_bounce_at TIMESTAMPTZ DEFAULT now(),
  retry_after TIMESTAMPTZ DEFAULT (now() + interval '24 hours'),
  retry_count INTEGER DEFAULT 0,
  max_retries INTEGER DEFAULT 1,
  final_result TEXT CHECK (final_result IN ('cleared', 'promoted_to_hard', 'pending')),
  resolved_at TIMESTAMPTZ,
  UNIQUE(email, source_mailbox)
);
CREATE INDEX idx_soft_retry_pending ON soft_bounce_retries(final_result) WHERE final_result = 'pending';

-- Audit trail — every action the system takes
CREATE TABLE bounce_events (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  mailbox_email TEXT,
  domain TEXT,
  event_type TEXT NOT NULL,
  severity TEXT CHECK (severity IN ('info', 'warning', 'critical')),
  details JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_bounce_events_mailbox ON bounce_events(mailbox_email, created_at DESC);
CREATE INDEX idx_bounce_events_severity ON bounce_events(severity, created_at DESC);

-- Daily snapshots for trend tracking
CREATE TABLE bounce_daily_snapshots (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  mailbox_email TEXT NOT NULL,
  snapshot_date DATE DEFAULT CURRENT_DATE,
  total_sent INTEGER DEFAULT 0,
  total_bounced INTEGER DEFAULT 0,
  hard_bounces INTEGER DEFAULT 0,
  soft_bounces INTEGER DEFAULT 0,
  bounce_rate DECIMAL DEFAULT 0,
  suppression_list_size INTEGER DEFAULT 0,
  UNIQUE(mailbox_email, snapshot_date)
);
```

---

## Pipeline Architecture

```
node bounces.js scan         <-- Runs every 4 hours via cron
  |
  |-- Step 1: scan-inboxes       (IMAP connect to each mailbox, fetch bounce messages)
  |-- Step 2: classify-bounces   (parse SMTP codes + Claude Haiku for ambiguous ones)
  |-- Step 3: update-suppression (add hard bounces to suppression list, track soft retries)
  |-- Step 4: check-rates        (compare bounce rates against thresholds)
  |-- Step 5: sync-smartlead     (cross-reference SmartLead bounce data)
  '-- Step 6: notify             (Telegram summary + alerts)

node bounces.js add-mailbox mike@cenra.io --imap-host imap.gmail.com --imap-pass xxxx
node bounces.js remove-mailbox mike@cenra.io
node bounces.js status                        <-- Show all mailbox bounce rates
node bounces.js check-email user@example.com  <-- Check if an address is on suppression list
node bounces.js export-suppression            <-- Export suppression list as CSV
node bounces.js report                        <-- Weekly bounce report
node bounces.js stats                         <-- Suppression list stats
```

---

## File Structure

```
bounce-handler/
|-- .env
|-- package.json
|-- CLAUDE.md                  (this file)
|-- src/
|   |-- config.js              (env validation + constants + thresholds)
|   |-- db.js                  (Supabase client + all database helpers)
|   |-- imap-scanner.js        (IMAP connection + bounce message fetching)
|   |-- bounce-parser.js       (email parsing + SMTP code extraction)
|   |-- classifier.js          (rules-based + Claude Haiku classification)
|   |-- suppression.js         (suppression list management + soft bounce retries)
|   |-- rate-checker.js        (bounce rate calculation + threshold comparison)
|   |-- smartlead.js           (SmartLead bounce API sync)
|   |-- notify.js              (Telegram notifications)
|   '-- report.js              (status table + weekly report + CSV export)
|-- bounces.js                 (main CLI entry point)
'-- cron-setup.sh              (crontab installer)
```

---

## Module Specifications

### src/config.js
- Load .env with dotenv
- Validate all required env vars exist, exit with clear error message listing which vars are missing
- Export constants:
  - `BOUNCE_RATE_WARNING = 0.02` (2%)
  - `BOUNCE_RATE_CRITICAL = 0.05` (5%)
  - `DOMAIN_BOUNCE_RATE_WARNING = 0.03` (3%)
  - `SPAM_COMPLAINT_CRITICAL = 0.003` (0.3%)
  - `SOFT_BOUNCE_RETRY_HOURS = 24`
  - `SOFT_BOUNCE_MAX_RETRIES = 1`
  - `IMAP_CONNECTION_TIMEOUT_MS = 30000`
  - `IMAP_RETRY_DELAY_MS = 60000`
  - `IMAP_MAX_RETRIES = 3`
  - `IMAP_DELAY_BETWEEN_MAILBOXES_MS = 2000`
  - `SMARTLEAD_DELAY_MS = 500`
  - `HAIKU_MODEL = 'claude-3-5-haiku-20241022'`
  - `BOUNCE_SUBJECTS` array: `['Undeliverable', 'Mail Delivery Failed', 'Returned mail', 'Delivery Status Notification', 'Undelivered Mail Returned', 'failure notice', 'Mail delivery failed']`
  - `BOUNCE_SENDERS` array: `['mailer-daemon@', 'postmaster@', 'mail-daemon@']`
  - `HARD_BOUNCE_CODES` array: `['550', '551', '552', '553', '554', '521', '556']`
  - `SOFT_BOUNCE_CODES` array: `['450', '451', '452', '421', '422']`

### src/db.js
- Create Supabase client from env vars
- Helper functions:
  - `getActiveMailboxCredentials()` — returns all active IMAP credentials
  - `getMailboxCredential(email)` — returns single mailbox IMAP credential
  - `updateLastScan(email, messageUid)` — update last_scan_at and last_scan_message_uid
  - `addToBounceLog(bounceRecord)` — insert into bounce_log, returns boolean (true = new, false = duplicate via raw_message_id)
  - `addToSuppressionList(email, bounceType, smtpCode, smtpMessage, sourceMailbox, sourceCampaign)` — upsert into suppression_list (ON CONFLICT DO NOTHING)
  - `isOnSuppressionList(email)` — check if email exists in suppression_list, returns boolean
  - `checkSuppressionBatch(emails)` — check multiple emails at once, returns Set of suppressed addresses
  - `getMailboxStats(email)` — get current stats from mailbox_bounce_stats
  - `updateMailboxStats(email, stats)` — upsert into mailbox_bounce_stats
  - `getDomainStats(domain)` — get current stats from domain_bounce_stats
  - `updateDomainStats(domain, stats)` — upsert into domain_bounce_stats
  - `addSoftBounceRetry(email, sourceMailbox)` — insert into soft_bounce_retries with retry_after = now + 24h
  - `getSoftBounceRetry(email)` — check if this email has a pending soft bounce retry
  - `resolveSoftBounceRetry(email, result)` — update final_result to 'cleared' or 'promoted_to_hard'
  - `logEvent(mailboxEmail, domain, eventType, severity, details)` — insert into bounce_events
  - `saveDailySnapshot(mailboxEmail, stats)` — upsert into bounce_daily_snapshots
  - `getSuppressionListCount()` — count of records in suppression_list
  - `exportSuppressionList()` — return all records from suppression_list ordered by detected_at DESC

### src/imap-scanner.js
- Function: `scanMailbox(credential)`:
  - Connect to IMAP server using the `imap` package with TLS (port 993)
  - Open INBOX in read-only mode
  - Search for messages newer than `credential.last_scan_message_uid` (use IMAP UID search)
  - For each message, fetch the full raw email (headers + body)
  - Filter: only keep messages where subject matches any `BOUNCE_SUBJECTS` pattern (case-insensitive partial match) OR sender matches any `BOUNCE_SENDERS` pattern
  - Parse each matching message with `mailparser` to get structured email object
  - Return: `{ mailbox: credential.email, messages: [{ uid, messageId, from, subject, date, textBody, htmlBody }], scannedCount, matchCount }`
  - On completion: call `db.updateLastScan(credential.email, highestUid)`

- Function: `scanAllMailboxes()`:
  - Get all active credentials from database
  - For each credential, call `scanMailbox(credential)` with `IMAP_DELAY_BETWEEN_MAILBOXES_MS` between connections
  - Retry failed connections up to `IMAP_MAX_RETRIES` times with `IMAP_RETRY_DELAY_MS` delay
  - If all retries fail for a mailbox: log event with severity 'warning', continue with next mailbox
  - Return: `{ results: [per-mailbox results], failedMailboxes: [emails that couldn't connect] }`

- Error handling:
  - IMAP connection timeout: `IMAP_CONNECTION_TIMEOUT_MS` (30 seconds)
  - Authentication failure: log as 'critical' event, skip mailbox, include in Telegram alert
  - Connection reset: retry with exponential backoff
  - Google IMAP rate limit: if "Too many simultaneous connections" error, increase delay to 5 seconds

### src/bounce-parser.js
- Function: `extractSmtpCode(text)`:
  - Search email body for SMTP status code patterns
  - Regex patterns to try (in order):
    1. `(\d{3})[\s\-]+\d\.\d\.\d` — enhanced status code (e.g., "550 5.1.1")
    2. `(?:Status|Diagnostic-Code):\s*(\d{3})` — DSN header format
    3. `(?:error|failed|rejected|refused).*?(\d{3})` — inline error mention
  - Return first match: `{ code: '550', enhanced: '5.1.1', raw: 'the matched line' }` or `null` if no code found

- Function: `extractBouncedAddress(message)`:
  - Try to find the original recipient address that bounced
  - Search strategies (in order):
    1. Check for `X-Failed-Recipients` header (most reliable — set by many MTAs)
    2. Check for `Final-Recipient` header in DSN body part
    3. Regex scan body for `<[email]>` patterns near "failed", "rejected", "undeliverable"
    4. Check the `To` field of the original embedded message (if the bounce wraps the original)
  - Return: email address string (lowercase, trimmed) or `null` if not extractable

- Function: `parseBounceMessage(message)`:
  - Call `extractSmtpCode(message.textBody || message.htmlBody)`
  - Call `extractBouncedAddress(message)`
  - Determine preliminary classification:
    - If smtp code found and in `HARD_BOUNCE_CODES` → `bounce_type: 'hard'`
    - If smtp code found and in `SOFT_BOUNCE_CODES` → `bounce_type: 'soft'`
    - If subject contains "out of office" or "auto-reply" or "automatic reply" → `bounce_type: 'auto_reply'`
    - If body contains "I am currently out" or "I will be out" or "on vacation" → `bounce_type: 'out_of_office'`
    - If no smtp code and no auto-reply patterns → `bounce_type: 'unknown'`
  - Return: `{ recipientEmail, bounceType, smtpCode, smtpMessage, classificationMethod: 'rules', confidence: 1.0, needsHaikuClassification: bounceType === 'unknown' }`

### src/classifier.js
- Function: `classifyWithHaiku(messageBody, subject)`:
  - Call Claude Haiku API with this prompt:
    ```
    You are an email bounce classifier. Analyze this email and classify it into exactly one category.

    Categories:
    - hard_bounce: The recipient email address permanently does not exist, is disabled, or the domain rejects all mail. SMTP 5xx errors.
    - soft_bounce: Temporary delivery failure — mailbox full, server temporarily unavailable, greylisting, rate limiting. SMTP 4xx errors.
    - auto_reply: An automatic reply from the recipient — out-of-office, vacation responder, auto-acknowledgment.
    - not_bounce: A normal email reply, newsletter, notification, or other non-bounce message that was incorrectly flagged.

    Respond with ONLY a JSON object:
    {"category": "hard_bounce|soft_bounce|auto_reply|not_bounce", "smtp_code": "550 or null", "bounced_address": "the address that bounced or null", "confidence": 0.0-1.0, "reason": "one sentence explanation"}

    Subject: {subject}
    Body (first 2000 chars):
    {messageBody.slice(0, 2000)}
    ```
  - Parse the JSON response
  - Return: `{ bounceType, smtpCode, bouncedAddress, confidence, reason, classificationMethod: 'haiku' }`
  - If Haiku API fails: return `{ bounceType: 'unknown', classificationMethod: 'haiku_failed', confidence: 0 }`

- Function: `classifyBounce(parsedBounce, rawMessage)`:
  - If `parsedBounce.needsHaikuClassification` is true: call `classifyWithHaiku()`
  - If Haiku returns a result with confidence > 0.8: use Haiku's classification
  - If Haiku returns low confidence or fails: keep as 'unknown', flag for human review
  - If `parsedBounce.bounceType` is already classified by rules: use rules result (higher trust)
  - Return: final classified bounce record

### src/suppression.js
- Function: `processBounceRecord(bounceRecord)`:
  - If `bounceType === 'hard'`:
    - Check if already on suppression list (skip if yes)
    - Add to suppression_list with bounce_type = 'hard'
    - Log event: 'address_suppressed', severity 'info'
    - Return: `{ action: 'suppressed', email: bounceRecord.recipientEmail }`
  - If `bounceType === 'soft'`:
    - Check if there's an existing soft bounce retry for this address
    - If no existing retry: create retry record (retry_after = now + 24h)
    - If existing retry and retry_count >= max_retries: promote to hard bounce, add to suppression list
    - Log event: 'soft_bounce_tracked' or 'soft_promoted_to_hard'
    - Return: `{ action: 'retry_scheduled' | 'promoted_to_hard', email }`
  - If `bounceType === 'auto_reply'` or `'out_of_office'` or `'not_bounce'`:
    - Log to bounce_log for record-keeping but do NOT suppress or count toward bounce rate
    - Return: `{ action: 'discarded', email }`
  - If `bounceType === 'unknown'`:
    - Log to bounce_log with classification_method = 'unknown'
    - Do NOT suppress (conservative — don't suppress without confidence)
    - Log event: 'unclassified_bounce', severity 'warning'
    - Return: `{ action: 'flagged_for_review', email }`

- Function: `processAllBounces(classifiedBounces)`:
  - For each bounce, call `processBounceRecord()`
  - After all processed: recalculate bounce stats per affected mailbox
  - Return: `{ suppressed: count, retryScheduled: count, discarded: count, flaggedForReview: count }`

- Function: `updateBounceStats(mailboxEmail)`:
  - Count hard bounces + promoted soft bounces for this mailbox from bounce_log
  - Get total_sent from mailbox_bounce_stats (or SmartLead API if not yet populated)
  - Calculate bounce_rate = total_bounced / total_sent (handle division by zero → 0)
  - Upsert into mailbox_bounce_stats
  - Also recalculate domain-level stats: aggregate all mailboxes on same domain
  - Save daily snapshot

### src/rate-checker.js
- Function: `checkMailboxRate(mailboxEmail)`:
  - Get current stats from mailbox_bounce_stats
  - Compare bounce_rate against thresholds:
    - `< BOUNCE_RATE_WARNING` → `{ status: 'healthy', action: 'none' }`
    - `>= BOUNCE_RATE_WARNING AND < BOUNCE_RATE_CRITICAL` → `{ status: 'warning', action: 'reduce_volume_50pct' }`
    - `>= BOUNCE_RATE_CRITICAL` → `{ status: 'critical', action: 'pause_mailbox' }`
  - If action is 'reduce_volume_50pct':
    - Call SmartLead API to reduce daily send limit by 50%
    - Log event: 'volume_reduced', severity 'warning'
  - If action is 'pause_mailbox':
    - Call SmartLead API to set daily send limit to 0
    - Update mailbox_bounce_stats status to 'paused'
    - Log event: 'mailbox_paused', severity 'critical'
  - Return: `{ mailboxEmail, bounceRate, status, action, details }`

- Function: `checkDomainRate(domain)`:
  - Get current stats from domain_bounce_stats
  - If bounce_rate >= `DOMAIN_BOUNCE_RATE_WARNING`:
    - Log event: 'domain_warning', severity 'warning'
    - Return: `{ domain, bounceRate, status: 'warning', message: 'All mailboxes on this domain are at risk' }`
  - Return: `{ domain, bounceRate, status: 'healthy' }`

- Function: `checkAllRates()`:
  - Get all mailboxes from mailbox_bounce_stats
  - For each, call `checkMailboxRate()`
  - Get all domains from domain_bounce_stats
  - For each, call `checkDomainRate()`
  - Return: `{ mailboxResults: [...], domainResults: [...], warnings: count, criticals: count }`

### src/smartlead.js
- Base URL: `https://server.smartlead.ai/api/v1`
- All requests append `?api_key=${API_KEY}` as query parameter
- Function: `getCampaigns()` — GET `/campaigns` — returns all campaigns
- Function: `getCampaignBounces(campaignId)` — GET `/campaigns/${campaignId}/bounces` — returns bounced email addresses with classification
- Function: `getEmailAccounts()` — GET `/email-accounts` — returns all connected email accounts with stats
- Function: `updateAccountSettings(accountId, settings)` — PATCH `/email-accounts/${accountId}` — update daily send limit
- Function: `syncBounces()`:
  - Get all active campaigns
  - For each campaign, get bounces from SmartLead
  - For each bounced address:
    - Check if already in bounce_log (by recipient_email + source matching)
    - If new: add to bounce_log with classification_method = 'smartlead'
    - If new hard bounce: add to suppression_list
  - Return: `{ newBouncesFromSmartLead: count, alreadyKnown: count }`
- Rate limit: `SMARTLEAD_DELAY_MS` (500ms) between all API calls

### src/notify.js
- Function: `sendTelegram(message)` — POST to `https://api.telegram.org/bot${TOKEN}/sendMessage` with chat_id and text (parse_mode: 'HTML')
- Max message length: 4096 chars. If longer, split into multiple messages.

- Function: `sendScanSummary(results)`:
  - If no new bounces and all rates healthy: send nothing (silent success)
  - If new bounces found: format message:
    ```
    Bounce Scan Complete
    New bounces: {count} (hard: {h}, soft: {s}, auto-reply: {a}, unknown: {u})
    Suppressed: {count} addresses added to suppression list
    Suppression list total: {total}
    ```
  - If any warnings: append warning section with mailbox name and current rate
  - If any criticals: prepend "ALERT" and list each critical issue with action taken

- Function: `sendDailySummary(allStats)`:
  - Format:
    ```
    Daily Bounce Report
    Mailboxes scanned: {count}
    Healthy: {count} | Warning: {count} | Critical: {count} | Paused: {count}
    Bounces (24h): {count} hard, {count} soft
    Suppression list: {total} addresses
    Highest bounce rate: {email} at {rate}%
    ```

- Function: `sendCriticalAlert(mailboxEmail, bounceRate, action)`:
  - Immediate alert, prefixed with red indicator:
    ```
    CRITICAL: {mailboxEmail}
    Bounce rate: {bounceRate}%
    Action taken: {action}
    Manual review required.
    ```

### src/report.js
- Function: `printStatusTable()`:
  - Use cli-table3 to show all mailboxes with columns: Email | Status | Bounce Rate | Hard | Soft | Total Sent | Last Scan
  - Color-code: green for healthy, yellow for warning, red for critical/paused

- Function: `printSuppressionStats()`:
  - Total addresses suppressed
  - Breakdown by bounce_type (hard, soft_permanent, spam_complaint)
  - Breakdown by source_mailbox (which mailbox generated the most bounces)
  - Last 10 addresses added (most recent)

- Function: `generateWeeklyReport()`:
  - Query bounce_daily_snapshots for last 7 days
  - Calculate trends: improving, stable, or worsening bounce rates per mailbox
  - Highlight any mailboxes with consistently rising bounce rates
  - Calculate: total bounces this week, addresses suppressed, average bounce rate
  - Format as both CLI table and Telegram message

- Function: `exportSuppressionListCsv()`:
  - Export full suppression list as CSV: email, bounce_type, smtp_code, source_mailbox, detected_at
  - Write to `exports/suppression_list_YYYY-MM-DD.csv`
  - Return file path

- Function: `checkEmail(email)`:
  - Look up a specific email address in suppression_list
  - If found: print when it was suppressed, why, which mailbox detected it
  - If not found: print "Not on suppression list"

### bounces.js (main CLI)
- Use commander for subcommands:
  - `scan` — Run full bounce processing pipeline (Steps 1-6). Default command.
  - `add-mailbox <email>` — Add a mailbox for IMAP scanning. Requires flags: `--imap-host`, `--imap-port` (default 993), `--imap-user` (default same as email), `--imap-pass`. Creates records in mailbox_imap_credentials and mailbox_bounce_stats.
  - `remove-mailbox <email>` — Deactivate a mailbox (set is_active = false). Does NOT delete — preserves history.
  - `status` — Print status table of all mailbox bounce rates.
  - `stats` — Print suppression list statistics.
  - `check-email <email>` — Check if a specific address is on the suppression list.
  - `export-suppression` — Export suppression list to CSV.
  - `report` — Generate and display weekly bounce report.
  - `scan --daily-summary` — Run scan AND send daily summary to Telegram (for the 8am cron job).

### cron-setup.sh
```bash
#!/bin/bash
# Add bounce handler to crontab — runs every 4 hours
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$SCRIPT_DIR/logs"
mkdir -p "$SCRIPT_DIR/exports"
# Bounce scan every 4 hours
(crontab -l 2>/dev/null; echo "0 */4 * * * cd $SCRIPT_DIR && node bounces.js scan >> logs/bounces.log 2>&1") | sort -u | crontab -
# Daily summary at 8am
(crontab -l 2>/dev/null; echo "0 8 * * * cd $SCRIPT_DIR && node bounces.js scan --daily-summary >> logs/bounces.log 2>&1") | sort -u | crontab -
echo "Cron jobs installed."
echo "  - Bounce scan: every 4 hours"
echo "  - Daily summary: 8am"
echo "Logs: $SCRIPT_DIR/logs/bounces.log"
echo "Exports: $SCRIPT_DIR/exports/"
```

---

## Rules

1. **Suppression list is permanent.** Once an address is on the suppression list, it NEVER comes off. This is a CAN-SPAM compliance requirement. Even if the contact is "deleted" from other systems, the suppression entry must remain.

2. **Conservative classification.** If a bounce message cannot be confidently classified, mark it as 'unknown' and do NOT suppress. False suppression (blocking a valid address) is worse than missing a bounce, because missed bounces are caught on the next scan but false suppressions permanently block a lead.

3. **Never count auto-replies as bounces.** Auto-replies and out-of-office messages are NOT delivery failures. They must not increment bounce counts or affect bounce rate calculations. Misclassifying them inflates rates and causes unnecessary mailbox pauses.

4. **Always log events.** Every bounce detection, classification, suppression, rate change, and action (pause/reduce) gets a row in bounce_events. This audit trail is critical for debugging deliverability issues and demonstrating CAN-SPAM compliance.

5. **Pause aggressively, resume manually.** Auto-pause at 5% bounce rate — this is non-negotiable. But resuming a paused mailbox requires a manual `bounces.js add-mailbox` or direct database update. The system never auto-resumes because a human should investigate WHY the bounce rate spiked before allowing the mailbox to send again.

6. **Rate limit all external API calls.** IMAP: 2-second delay between mailbox connections. SmartLead: 500ms between calls. Claude Haiku: no explicit rate limit needed at typical volumes (< 100 calls/run). Never parallelize connections to the same service.

7. **Pre-check suppression before every campaign send.** This system maintains the suppression list. The campaign sending system (separate) MUST query the suppression list before sending ANY email. The bounce handler doesn't control sending — it controls the list.

8. **Soft bounces get ONE retry.** First soft bounce = schedule retry in 24 hours. Second soft bounce on the same address = promote to hard bounce and suppress. Do not retry more than once — repeated soft bounces indicate a persistent problem.

---

## Testing Checklist

1. [ ] `node bounces.js add-mailbox test@testdomain.com --imap-host imap.gmail.com --imap-pass xxxx` — creates credential and stats records
2. [ ] `node bounces.js status` — shows table with the test mailbox at 0% bounce rate
3. [ ] `node bounces.js check-email nobody@nowhere.com` — returns "Not on suppression list"
4. [ ] `node bounces.js scan` — runs full pipeline, connects to IMAP, processes any bounces, sends Telegram summary
5. [ ] Manually insert a test bounce into bounce_log with bounce_type 'hard', run scan — verify address appears in suppression_list
6. [ ] `node bounces.js check-email <the-hard-bounced-address>` — returns suppression details
7. [ ] `node bounces.js stats` — shows suppression list count and breakdown
8. [ ] Manually set a mailbox bounce_rate to 0.03 in Supabase, run scan — should trigger warning alert via Telegram
9. [ ] Manually set a mailbox bounce_rate to 0.06 in Supabase, run scan — should auto-pause and send critical alert
10. [ ] `node bounces.js export-suppression` — creates CSV file in exports/ folder
11. [ ] `node bounces.js report` — generates weekly report
12. [ ] `node bounces.js remove-mailbox test@testdomain.com` — deactivates without deleting
13. [ ] Check cron is installed: `crontab -l` should show the bounce handler entries
14. [ ] Let it run for 24 hours, check Telegram for the 8am daily summary
15. [ ] Send a test email to a known-invalid address, wait for bounce, run scan — verify end-to-end detection

---

## Build Order

Tell Claude: Build in this exact order, testing each module before moving to the next.

1. `src/config.js` + `src/db.js` — foundation, test with `node -e "require('./src/db')"`
2. `src/notify.js` — test by sending a test Telegram message
3. `src/imap-scanner.js` — test by connecting to one mailbox and listing recent messages
4. `src/bounce-parser.js` — test with sample bounce email strings (hardcode 3-4 examples: one hard bounce, one soft bounce, one auto-reply, one ambiguous)
5. `src/classifier.js` — test by sending an ambiguous bounce message to Claude Haiku
6. `src/suppression.js` — test by processing a mock hard bounce and verifying it appears in the database
7. `src/rate-checker.js` — test with mock data for each threshold (healthy, warning, critical)
8. `src/smartlead.js` — test by listing campaigns and fetching bounces
9. `src/report.js` — test status table display and CSV export
10. `bounces.js` — wire it all together with commander
11. `cron-setup.sh` — install and verify cron jobs
