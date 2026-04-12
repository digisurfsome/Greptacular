# CAN-SPAM Compliance & Suppression List Manager — CLAUDE.md Build File

> **What this is:** Drop this file as CLAUDE.md into a project folder, run `claude`, and it builds the complete compliance and suppression list management system. This was produced BY the Operating System Creator framework as a proof of concept.

---

## Mission

Build a Node.js system that manages CAN-SPAM/GDPR compliance for cold email operations. The system maintains a centralized suppression list fed by multiple sources (bounces, unsubscribes, spam complaints, GDPR requests), exposes a pre-send validation API that other systems call before every email send, syncs suppressions to all connected sending platforms, and generates compliance audit reports. It runs as an Express.js server (webhook receiver + validation API) with cron-scheduled tasks for syncing, GDPR processing, and reporting.

---

## API Keys Required

```
# .env file
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_service_role_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
SMARTLEAD_API_KEY=your_smartlead_api_key
INSTANTLY_API_KEY=your_instantly_api_key
MILLIONVERIFIER_API_KEY=your_millionverifier_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
WEBHOOK_SECRET=your_shared_secret_for_webhook_auth
SERVER_PORT=3100
PHYSICAL_ADDRESS="Your Company Name, 123 Main St, City, ST 12345"
```

### How to get each key:

**Supabase:** Create project at supabase.com > Settings > API > copy Project URL and service_role key (not anon key).

**Telegram Bot:** Message @BotFather on Telegram > /newbot > copy token. Then message your bot, visit `https://api.telegram.org/bot<TOKEN>/getUpdates` to find your chat_id.

**SmartLead:** Log in > Settings > API > copy API key. Need Pro plan ($39/mo) for API access.

**Instantly:** Log in > Settings > Integrations > API > copy API key. Need Growth plan for API access.

**MillionVerifier:** Sign up at millionverifier.com > Dashboard > API > copy API key. Pay-as-you-go at $0.0005/email.

**Anthropic (Claude Haiku):** Sign up at console.anthropic.com > API Keys > create key. Used for parsing ambiguous unsubscribe requests. Cost: ~$0.001 per request.

**Webhook Secret:** Generate a random 32-character string. Share this with any system that sends webhook events to your suppression endpoint. Used to verify webhook authenticity.

---

## Tech Stack

```json
{
  "dependencies": {
    "dotenv": "^16.0.0",
    "@supabase/supabase-js": "^2.0.0",
    "@anthropic-ai/sdk": "^0.30.0",
    "express": "^4.18.0",
    "node-fetch": "2",
    "commander": "^11.0.0",
    "cli-table3": "^0.6.0",
    "node-cron": "^3.0.0",
    "puppeteer": "^22.0.0",
    "helmet": "^7.0.0",
    "express-rate-limit": "^7.0.0"
  }
}
```

Runtime: Node.js 18+

---

## Database Schema

Create these tables in Supabase before running:

```sql
-- Centralized suppression list — single source of truth
-- Once an email is added, it is NEVER automatically removed
CREATE TABLE suppression_list (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email TEXT NOT NULL,
  reason TEXT NOT NULL CHECK (reason IN (
    'hard_bounce', 'unsubscribe', 'spam_complaint', 'hostile_reply',
    'gdpr_request', 'manual', 'spam_trap', 'domain_blacklist'
  )),
  source TEXT NOT NULL,
  source_detail JSONB DEFAULT '{}',
  is_gdpr BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(email, reason)
);
CREATE INDEX idx_suppression_email ON suppression_list(email);
CREATE INDEX idx_suppression_reason ON suppression_list(reason);
CREATE INDEX idx_suppression_created ON suppression_list(created_at DESC);

-- Audit log — every action on every record, immutable
CREATE TABLE audit_log (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email TEXT NOT NULL,
  action TEXT NOT NULL CHECK (action IN (
    'suppression_added', 'suppression_duplicate_skipped',
    'validation_checked', 'validation_blocked', 'validation_warned',
    'sync_started', 'sync_completed', 'sync_failed',
    'gdpr_received', 'gdpr_deletion_started', 'gdpr_deletion_completed',
    'gdpr_deletion_failed', 'unsubscribe_confirmed',
    'report_generated', 'manual_override'
  )),
  source TEXT NOT NULL,
  details JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_audit_email ON audit_log(email, created_at DESC);
CREATE INDEX idx_audit_action ON audit_log(action, created_at DESC);
CREATE INDEX idx_audit_created ON audit_log(created_at DESC);

-- GDPR deletion requests — tracked separately with deadlines
CREATE TABLE gdpr_requests (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email TEXT NOT NULL,
  status TEXT DEFAULT 'received' CHECK (status IN (
    'received', 'verified', 'deleting', 'partially_deleted',
    'fully_deleted', 'confirmed_to_requester', 'failed'
  )),
  request_source TEXT NOT NULL,
  requested_at TIMESTAMPTZ DEFAULT now(),
  deadline TIMESTAMPTZ NOT NULL,
  deletion_manifest JSONB DEFAULT '{}',
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_gdpr_email ON gdpr_requests(email);
CREATE INDEX idx_gdpr_status ON gdpr_requests(status);
CREATE INDEX idx_gdpr_deadline ON gdpr_requests(deadline);

-- Validation log — every pre-send check recorded
CREATE TABLE validation_log (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email TEXT NOT NULL,
  result TEXT NOT NULL CHECK (result IN ('allowed', 'blocked', 'warned')),
  blocks JSONB DEFAULT '[]',
  warnings JSONB DEFAULT '[]',
  caller TEXT,
  checked_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_validation_email ON validation_log(email, checked_at DESC);
CREATE INDEX idx_validation_result ON validation_log(result, checked_at DESC);

-- Cross-system sync tracking
CREATE TABLE sync_status (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  suppression_id UUID REFERENCES suppression_list(id),
  email TEXT NOT NULL,
  platform TEXT NOT NULL CHECK (platform IN ('smartlead', 'instantly')),
  synced BOOLEAN DEFAULT false,
  attempts INTEGER DEFAULT 0,
  last_attempt TIMESTAMPTZ,
  synced_at TIMESTAMPTZ,
  error TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_sync_pending ON sync_status(synced, platform);
CREATE INDEX idx_sync_email ON sync_status(email);

-- Compliance reports metadata
CREATE TABLE compliance_reports (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  report_type TEXT NOT NULL CHECK (report_type IN ('daily', 'weekly', 'monthly', 'on_demand')),
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  summary JSONB DEFAULT '{}',
  html_path TEXT,
  pdf_path TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Domain blacklist — known spam trap domains and dangerous domains
CREATE TABLE domain_blacklist (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  domain TEXT UNIQUE NOT NULL,
  reason TEXT NOT NULL,
  source TEXT NOT NULL,
  added_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_domain_blacklist ON domain_blacklist(domain);

-- Frequency tracking — when was each recipient last emailed
CREATE TABLE send_history (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email TEXT NOT NULL,
  sent_at TIMESTAMPTZ DEFAULT now(),
  campaign_id TEXT,
  mailbox TEXT
);
CREATE INDEX idx_send_history_email ON send_history(email, sent_at DESC);
```

---

## Pipeline Architecture

```
compliance-manager server          ← Express.js, always running on port 3100
  │
  ├── POST /api/suppress           ← Webhook: receive suppression events from any source
  ├── POST /api/validate           ← API: pre-send validation (other systems call this)
  ├── POST /api/validate/batch     ← API: batch pre-send validation
  ├── POST /api/unsubscribe        ← Web form: public unsubscribe endpoint
  ├── POST /api/gdpr               ← Web form: GDPR deletion request endpoint
  ├── GET  /api/health             ← Health check endpoint
  ├── GET  /api/stats              ← Quick stats (suppression count, sync status)
  │
  └── Cron jobs (internal):
      ├── Every 15 min: sync pending suppressions to all platforms
      ├── Daily 9am: check GDPR request deadlines, send daily summary
      ├── Weekly Monday 9am: generate weekly compliance report
      └── Monthly 1st 9am: generate monthly compliance report

node compliance.js suppress <email> --reason <reason>   ← Manual CLI suppression
node compliance.js validate <email>                     ← Manual CLI validation
node compliance.js status                               ← Show suppression list stats
node compliance.js sync                                 ← Force sync to all platforms
node compliance.js report --type weekly                 ← Generate report on demand
node compliance.js gdpr <email>                         ← Initiate GDPR deletion
node compliance.js import-blacklist <file>              ← Import domain blacklist CSV
```

---

## File Structure

```
compliance-manager/
├── .env
├── package.json
├── CLAUDE.md                       (this file)
├── src/
│   ├── config.js                   (env validation + constants)
│   ├── db.js                       (Supabase client + helpers)
│   ├── server.js                   (Express.js server + routes)
│   ├── suppress.js                 (suppression list ingestion logic)
│   ├── validate.js                 (pre-send validation engine)
│   ├── unsubscribe.js              (unsubscribe request processor)
│   ├── sync.js                     (cross-system sync to SmartLead/Instantly)
│   ├── gdpr.js                     (GDPR deletion handler)
│   ├── notify.js                   (Telegram notifications)
│   ├── report.js                   (compliance report generator — HTML + PDF)
│   └── classifier.js              (Claude Haiku for ambiguous request parsing)
├── templates/
│   ├── report-weekly.html          (HTML template for weekly report)
│   ├── report-monthly.html         (HTML template for monthly report)
│   └── unsubscribe-confirm.html    (unsubscribe confirmation page)
├── reports/                        (generated reports — gitignored)
├── compliance.js                   (main CLI entry point)
└── cron-setup.sh                   (crontab installer for scheduled tasks)
```

---

## Module Specifications

### src/config.js
- Load .env with dotenv
- Validate all required env vars exist, exit with clear error if any missing
- Export constants:
  - `FREQUENCY_CAP_DAYS = 3` (minimum days between emails to same recipient)
  - `GDPR_DEADLINE_DAYS = 30` (GDPR deletion must complete within 30 days)
  - `GDPR_WARNING_DAYS = 7` (alert when deadline is 7 days away)
  - `SYNC_RETRY_MAX = 8` (max sync retry attempts)
  - `SYNC_RETRY_INTERVAL_MS = 900000` (15 minutes between retries)
  - `WEBHOOK_SECRET` (shared secret for authenticating webhook senders)
  - `PHYSICAL_ADDRESS` (required physical address for compliance checks)
  - `PLATFORMS = ['smartlead', 'instantly']` (connected sending platforms)

### src/db.js
- Create Supabase client
- Helper functions:
  - `addSuppression(email, reason, source, sourceDetail)` — insert into suppression_list, return the record. If duplicate (same email+reason), skip but log to audit_log.
  - `isOnSuppressionList(email)` — returns `{ suppressed: true/false, reasons: [...] }`. Case-insensitive lookup (lowercase + trim before query).
  - `getSuppressionsByEmail(email)` — returns all suppression records for an email.
  - `getPendingSyncs(platform)` — returns suppression records not yet synced to a specific platform.
  - `markSynced(syncId, platform)` — update sync_status to synced.
  - `markSyncFailed(syncId, platform, error)` — update sync_status with error, increment attempts.
  - `logAudit(email, action, source, details)` — insert into audit_log. Never fails silently — if audit write fails, throw.
  - `logValidation(email, result, blocks, warnings, caller)` — insert into validation_log.
  - `addGdprRequest(email, requestSource)` — insert into gdpr_requests with deadline = now + 30 days.
  - `getPendingGdprRequests()` — returns all GDPR requests not in `fully_deleted` or `confirmed_to_requester` status.
  - `getGdprRequestsNearDeadline(daysRemaining)` — returns GDPR requests with deadline within N days.
  - `updateGdprStatus(id, status, deletionManifest)` — update GDPR request status and manifest.
  - `getLastSendDate(email)` — query send_history for most recent send_at for this email.
  - `isDomainBlacklisted(domain)` — check domain_blacklist table.
  - `getSuppressionStats(startDate, endDate)` — aggregate counts by reason for reporting.
  - `getAuditTrail(email)` — return full audit history for a specific email, ordered by timestamp.

### src/server.js
- Create Express.js app with helmet for security headers and express-rate-limit
- Rate limit: 100 requests per 15 minutes per IP for webhook endpoints, 1000 requests per 15 minutes for validation API
- Middleware: JSON body parser, webhook secret verification (check `x-webhook-secret` header against `WEBHOOK_SECRET`)
- Routes:

  **POST /api/suppress** — Receive suppression events
  - Body: `{ email, reason, source, detail? }`
  - Validate: email format, reason is valid enum, source is non-empty
  - Call `suppress.ingest(email, reason, source, detail)`
  - Response: `{ success: true, suppression_id, was_duplicate: false }`
  - Auth: x-webhook-secret header must match WEBHOOK_SECRET

  **POST /api/validate** — Pre-send validation (single)
  - Body: `{ email, from_address?, has_physical_address?, has_unsubscribe?, is_first_contact? }`
  - Call `validate.checkRecipient(email, options)`
  - Response: `{ allowed: true/false, blocks: [...], warnings: [...] }`
  - Auth: x-webhook-secret header

  **POST /api/validate/batch** — Pre-send validation (batch)
  - Body: `{ emails: [{ email, from_address?, ... }] }` (max 1000 per batch)
  - Call `validate.checkBatch(emails)`
  - Response: `{ results: [{ email, allowed, blocks, warnings }], summary: { total, allowed, blocked, warned } }`
  - Auth: x-webhook-secret header

  **POST /api/unsubscribe** — Public unsubscribe web form
  - Body: `{ email }`
  - No auth required (public endpoint)
  - Rate limit: 10 requests per 15 minutes per IP
  - Call `unsubscribe.process(email, 'web_form')`
  - Response: HTML confirmation page (from templates/unsubscribe-confirm.html)

  **POST /api/gdpr** — GDPR deletion request
  - Body: `{ email, requester_name?, requester_email? }`
  - Rate limit: 5 requests per 15 minutes per IP
  - Call `gdpr.receiveRequest(email, source)`
  - Response: `{ received: true, deadline: '2026-05-12', reference_id: uuid }`

  **GET /api/health** — Health check
  - No auth required
  - Checks: Supabase connection, server uptime, last sync time
  - Response: `{ status: 'healthy', uptime_seconds, last_sync, suppression_count }`

  **GET /api/stats** — Quick stats
  - Auth: x-webhook-secret header
  - Response: `{ total_suppressions, by_reason: {...}, pending_syncs, pending_gdpr, last_report }`

- Start cron jobs (via node-cron):
  - `*/15 * * * *` — call `sync.syncAll()`
  - `0 9 * * *` — call `gdpr.checkDeadlines()` then `notify.sendDailySummary()`
  - `0 9 * * 1` — call `report.generateWeekly()`
  - `0 9 1 * *` — call `report.generateMonthly()`

### src/suppress.js
- Function: `ingest(email, reason, source, detail)`:
  - Normalize email: lowercase, trim whitespace
  - Validate email format (basic regex — must contain @ and domain)
  - Check if already on suppression list with same reason → if yes, log `suppression_duplicate_skipped` to audit, return `{ was_duplicate: true }`
  - Insert into suppression_list
  - Log `suppression_added` to audit_log
  - Create sync_status records for each platform in PLATFORMS (one row per platform, synced = false)
  - If reason is 'spam_complaint' → send immediate Telegram alert
  - If reason is 'gdpr_request' → also call `gdpr.receiveRequest(email, source)`
  - Return: `{ suppression_id, was_duplicate: false }`

- Function: `importBlacklist(filePath)`:
  - Read CSV file (columns: domain, reason, source)
  - For each row, insert into domain_blacklist
  - Skip duplicates
  - Return: `{ imported: count, skipped: count }`

### src/validate.js
- Function: `checkRecipient(email, options)`:
  - Normalize email: lowercase, trim
  - Initialize `blocks = []` and `warnings = []`
  - Check 1: Is email on suppression_list? → block with reason `{ rule: 'suppressed', reasons: [...] }`
  - Check 2: Is email domain on domain_blacklist? → block with `{ rule: 'domain_blacklisted', domain }`
  - Check 3: Is options.has_physical_address === false? → warn `{ rule: 'missing_physical_address' }`
  - Check 4: Is options.has_unsubscribe === false? → warn `{ rule: 'missing_unsubscribe' }`
  - Check 5: Get last send date — if within FREQUENCY_CAP_DAYS → warn `{ rule: 'frequency_cap', last_sent, days_ago }`
  - Check 6: If options.is_first_contact and email appears to be HTML → warn `{ rule: 'html_first_contact' }`
  - Determine result: if any blocks → `allowed = false`. If only warnings → `allowed = true` (warnings are advisory).
  - Log to validation_log: `validation_blocked` or `validation_warned` or `validation_checked`
  - Return: `{ allowed, blocks, warnings }`

- Function: `checkBatch(emailList)`:
  - For each item in emailList, call `checkRecipient(item.email, item)`
  - Collect results
  - Calculate summary: total, allowed count, blocked count, warned count
  - Return: `{ results: [...], summary: { total, allowed, blocked, warned } }`
  - Note: batch lookup — query suppression_list with `email IN (...)` for efficiency instead of N individual queries

### src/unsubscribe.js
- Function: `process(email, channel, originalMessage)`:
  - Normalize email
  - If channel is 'reply_email' and originalMessage is provided:
    - Call `classifier.isUnsubscribe(originalMessage)` to parse ambiguous requests
    - If classifier says not an unsubscribe → return `{ processed: false, reason: 'not_unsubscribe', classified_as: result }`
  - Call `suppress.ingest(email, 'unsubscribe', channel, { original_message: originalMessage })`
  - Log `unsubscribe_confirmed` to audit_log
  - If channel is 'web_form' or 'direct_email' → queue confirmation (do NOT confirm spam complaints)
  - Return: `{ processed: true, suppression_id }`

### src/sync.js
- Function: `syncAll()`:
  - For each platform in PLATFORMS:
    - Get pending syncs: `getPendingSyncs(platform)` — records where synced = false AND attempts < SYNC_RETRY_MAX
    - For each pending record:
      - Call the platform-specific sync function
      - If success → `markSynced(syncId, platform)`
      - If failure → `markSyncFailed(syncId, platform, error)`
      - If attempts >= SYNC_RETRY_MAX → send Telegram alert: "CRITICAL: Sync to {platform} failed after {max} attempts for {email}"
    - Log `sync_completed` or `sync_failed` to audit_log
  - Send summary to Telegram if any failures

- Function: `syncToSmartlead(email)`:
  - POST to `https://server.smartlead.ai/api/v1/email-accounts/block-list?api_key=${API_KEY}`
  - Body: `{ email_list: [email] }`
  - Rate limit: 500ms between calls
  - Return: `{ success: true/false, error? }`

- Function: `syncToInstantly(email)`:
  - POST to `https://api.instantly.ai/api/v2/block-list` with header `Authorization: Bearer ${API_KEY}`
  - Body: `{ entries: [{ email }] }`
  - Rate limit: 500ms between calls
  - Return: `{ success: true/false, error? }`

### src/gdpr.js
- Function: `receiveRequest(email, requestSource)`:
  - Create record in gdpr_requests with status = 'received', deadline = now + 30 days
  - Add to suppression list with reason = 'gdpr_request'
  - Log `gdpr_received` to audit_log
  - Send Telegram alert: "GDPR REQUEST: {email} — deadline {deadline}. Processing started."
  - Return: `{ request_id, deadline }`

- Function: `processRequest(requestId)`:
  - Update status to 'deleting'
  - Build deletion manifest (which systems have data):
    - Supabase: query all tables for this email
    - SmartLead: search for lead by email via API
    - Instantly: search for lead by email via API
  - For each system with data:
    - Delete all records containing this email
    - Record what was deleted in the deletion_manifest
    - If deletion fails on any system → update status to 'partially_deleted', alert via Telegram
  - If all deletions succeed:
    - Update status to 'fully_deleted'
    - Log `gdpr_deletion_completed` to audit_log
    - Note: the suppression_list entry for this email is KEPT (with reason 'gdpr_request') to prevent re-emailing. Only the data is deleted, not the suppression.
  - Return: `{ status, deletion_manifest }`

- Function: `checkDeadlines()`:
  - Get all GDPR requests with status not in ('fully_deleted', 'confirmed_to_requester')
  - For each request:
    - If deadline is within GDPR_WARNING_DAYS → Telegram alert: "GDPR DEADLINE WARNING: {email} — {days} days remaining"
    - If deadline has passed → Telegram CRITICAL alert: "GDPR DEADLINE EXPIRED: {email} — OVERDUE. Immediate action required."
    - If status is 'received' → auto-start processing: call `processRequest(requestId)`
  - Return: `{ pending_count, warning_count, overdue_count }`

### src/notify.js
- Function: `sendTelegram(message)` — POST to `https://api.telegram.org/bot${TOKEN}/sendMessage` with chat_id and text (parse_mode: 'HTML'). Max message length: 4096 chars. If longer, split into multiple messages.

- Function: `alertSpamComplaint(email, source)`:
  - Format: "SPAM COMPLAINT: {email}\nSource: {source}\nAction: Auto-suppressed, sync queued to all platforms."

- Function: `alertGdprRequest(email, deadline)`:
  - Format: "GDPR REQUEST: {email}\nDeadline: {deadline}\nStatus: Processing started."

- Function: `alertSyncFailure(email, platform, error)`:
  - Format: "CRITICAL — SYNC FAILURE\nEmail: {email}\nPlatform: {platform}\nError: {error}\nManual intervention may be required."

- Function: `sendDailySummary()`:
  - Query today's audit_log for counts by action type
  - Query pending GDPR requests
  - Query pending syncs
  - Format: "Compliance Daily Summary\n{date}\n---\nSuppressions added: {count} ({breakdown by reason})\nValidation checks: {count} ({blocked}/{allowed})\nPending syncs: {count}\nPending GDPR: {count}\nStatus: {ALL_SYNCED | SYNC_ISSUES}"

- Function: `sendWeeklySummary(reportData)`:
  - Format: "Compliance Weekly Report\n{date range}\n---\nTotal suppressions: {count}\nBy reason: {breakdown}\nSync success rate: {percent}\nGDPR requests: {count} ({completed}/{pending})\nReport saved: {path}"

### src/classifier.js
- Function: `isUnsubscribe(messageText)`:
  - Call Claude Haiku (claude-3-5-haiku-20241022) with system prompt:
    ```
    You are an email classifier. Given a reply to a cold email, classify it as one of:
    - "unsubscribe" — the person wants to stop receiving emails (e.g., "remove me", "unsubscribe", "stop emailing me", "take me off your list")
    - "not_interested" — the person is declining the offer but NOT asking to be removed (e.g., "not interested right now", "no thanks", "we're all set")
    - "hostile" — the person is angry or threatening (e.g., "I'll report you as spam", "this is spam", threats)
    - "other" — anything else (out of office, wrong person, question, positive reply)

    Respond with ONLY the classification word. Nothing else.
    ```
  - User message: the reply email text
  - Return: `{ classification: 'unsubscribe'|'not_interested'|'hostile'|'other', should_suppress: true/false }`
  - should_suppress = true if classification is 'unsubscribe' or 'hostile'
  - Cost: ~$0.001 per call
  - Timeout: 5 seconds. If Haiku times out, default to 'unsubscribe' (err on the side of suppression — safer than accidentally re-emailing)

### src/report.js
- Function: `generateWeekly()`:
  - Query suppression stats for the last 7 days
  - Query validation stats for the last 7 days
  - Query sync success rate for the last 7 days
  - Query GDPR request status
  - Build data object with all metrics
  - Render HTML from templates/report-weekly.html (simple string interpolation — no template engine needed)
  - Save HTML to reports/weekly-{date}.html
  - Use Puppeteer to convert HTML to PDF: reports/weekly-{date}.pdf
  - Save report metadata to compliance_reports table
  - Send weekly summary via Telegram
  - Return: `{ html_path, pdf_path, summary }`

- Function: `generateMonthly()`:
  - Same as weekly but for 30-day period
  - Additional sections: trend analysis (is suppression rate increasing/decreasing?), GDPR compliance status, platform sync reliability
  - Render from templates/report-monthly.html
  - Save to reports/monthly-{date}.html and .pdf
  - Return: `{ html_path, pdf_path, summary }`

- Function: `generateOnDemand(startDate, endDate)`:
  - Custom date range report
  - Same structure as monthly
  - Return: `{ html_path, pdf_path, summary }`

- Function: `printStatusTable()`:
  - Use cli-table3 to show suppression list summary:
    - Columns: Reason | Count | Last Added | Sync Status
  - Show pending GDPR requests:
    - Columns: Email | Status | Deadline | Days Remaining
  - Show recent audit log (last 20 entries):
    - Columns: Time | Email | Action | Source

### compliance.js (main CLI)
- Use commander for subcommands:
  - `server` — Start the Express.js server (webhook receiver + validation API + cron jobs). Default command.
  - `suppress <email>` — Manually add an email to the suppression list. Options: `--reason <reason>` (required), `--source <source>` (default: 'manual_cli').
  - `validate <email>` — Manually validate an email against the suppression list and all rules. Prints result.
  - `validate-batch <file>` — Validate a CSV/text file of emails (one per line). Prints summary.
  - `status` — Print suppression list stats table, pending GDPR requests, recent audit trail.
  - `sync` — Force immediate sync of all pending suppressions to all platforms.
  - `report` — Generate a report. Options: `--type weekly|monthly|custom`, `--start <date>`, `--end <date>`.
  - `gdpr <email>` — Initiate a GDPR "right to be forgotten" deletion for an email.
  - `audit <email>` — Print the full audit trail for a specific email address.
  - `import-blacklist <file>` — Import a domain blacklist from CSV file (columns: domain, reason).
  - `check-compliance <email-file>` — Scan an email template file for compliance issues (physical address, unsubscribe link).

### templates/report-weekly.html
- Clean, professional HTML report layout
- Sections: Header (report title, date range, generated timestamp), Suppression Summary (table with counts by reason, comparison to previous week), Validation Summary (total checks, blocks, warnings, block rate), Sync Status (per-platform sync success rate), GDPR Status (pending requests with deadlines), Audit Highlights (any critical events), Footer (generated by Compliance Manager)
- Inline CSS (no external stylesheets — PDF rendering requires it)

### templates/report-monthly.html
- Same as weekly plus: Trend Charts section (using inline SVG bar charts — no JavaScript), Month-over-Month Comparison, Compliance Score (percentage based on: sync success rate, GDPR on-time rate, suppression response time)

### templates/unsubscribe-confirm.html
- Simple, clean page: "You have been removed from our mailing list. You will no longer receive emails from us. If you believe this was in error, contact {PHYSICAL_ADDRESS}."
- No tracking pixels, no JavaScript, no cookies — pure HTML

### cron-setup.sh
```bash
#!/bin/bash
# Install cron jobs for scheduled compliance tasks
# Only needed if NOT using the built-in node-cron (server mode handles scheduling internally)
# Use this for CLI-only mode on a VPS

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$SCRIPT_DIR/logs"

# Sync pending suppressions every 15 minutes
(crontab -l 2>/dev/null; echo "*/15 * * * * cd $SCRIPT_DIR && node compliance.js sync >> logs/compliance.log 2>&1") | sort -u | crontab -

# Daily GDPR deadline check + summary at 9am
(crontab -l 2>/dev/null; echo "0 9 * * * cd $SCRIPT_DIR && node compliance.js gdpr --check-deadlines >> logs/compliance.log 2>&1") | sort -u | crontab -

# Weekly compliance report on Monday at 9am
(crontab -l 2>/dev/null; echo "0 9 * * 1 cd $SCRIPT_DIR && node compliance.js report --type weekly >> logs/compliance.log 2>&1") | sort -u | crontab -

# Monthly compliance report on 1st at 9am
(crontab -l 2>/dev/null; echo "0 9 1 * * cd $SCRIPT_DIR && node compliance.js report --type monthly >> logs/compliance.log 2>&1") | sort -u | crontab -

echo "Cron jobs installed:"
echo "  - Sync: every 15 minutes"
echo "  - GDPR check: daily at 9am"
echo "  - Weekly report: Monday 9am"
echo "  - Monthly report: 1st of month 9am"
```

---

## Rules

1. **Fail closed, never fail open.** If the suppression list database is unreachable, the pre-send validation API must return `{ allowed: false }`. Never allow an email send when you can't verify the suppression list. Sending to a suppressed address costs up to $51,744. A false block costs nothing.

2. **Suppression list is append-only.** Once an email is added to the suppression list, it is NEVER automatically removed. Manual removal requires CLI command `suppress --remove` with mandatory `--reason` flag, and the removal is logged to the audit trail. This is the single most important rule in the entire system.

3. **Every action gets an audit log entry.** Every suppression addition, every validation check, every sync attempt, every GDPR action — all logged with timestamp, source, and details. The audit log is the legal defense. If the audit write fails, the operation should throw, not continue silently.

4. **Normalize all emails.** Before any operation — suppress, validate, sync, check — lowercase and trim the email address. `John@Example.COM` and `john@example.com` are the same address.

5. **Sync to all platforms immediately.** When a suppression is added, sync records are created for every platform. The sync cron picks them up within 15 minutes. If a sync fails after SYNC_RETRY_MAX attempts, send a CRITICAL Telegram alert. A suppression that exists in the database but not in the sending platform is a lawsuit waiting to happen.

6. **GDPR requests are the highest priority.** When a GDPR request arrives: immediately suppress the email, immediately start deletion across all systems, and track the 30-day deadline. Alert at 7 days remaining. CRITICAL alert if deadline passes. A GDPR violation is up to 4% of annual global revenue.

7. **Rate limit all external API calls.** SmartLead: 500ms between calls. Instantly: 500ms between calls. MillionVerifier: 200ms between calls. Claude Haiku: 100ms between calls. Never parallelize calls to the same service.

8. **Webhook authentication is mandatory.** Every incoming webhook must include the `x-webhook-secret` header matching the configured WEBHOOK_SECRET. Reject unauthenticated webhooks with 401. Exception: the public /api/unsubscribe endpoint (no auth, but heavy rate limiting).

9. **Reports are immutable artifacts.** Once a report is generated, it is never modified. If a correction is needed, generate a new report. Reports serve as legal evidence and must be trustworthy.

10. **When in doubt, suppress.** If the classifier can't determine whether a reply is an unsubscribe, treat it as an unsubscribe. If a webhook payload is ambiguous, suppress and alert. The cost of a false suppression (one lost prospect) is infinitely lower than the cost of emailing a suppressed address ($51,744 fine).

---

## Testing Checklist

1. [ ] `node compliance.js server` — starts Express server on configured port, all routes respond
2. [ ] `curl -X POST http://localhost:3100/api/suppress -H "x-webhook-secret: $SECRET" -H "Content-Type: application/json" -d '{"email":"test@example.com","reason":"hard_bounce","source":"test"}'` — returns success, record appears in suppression_list
3. [ ] `curl -X POST http://localhost:3100/api/validate -H "x-webhook-secret: $SECRET" -H "Content-Type: application/json" -d '{"email":"test@example.com"}'` — returns `{ allowed: false, blocks: [{ rule: "suppressed" }] }`
4. [ ] `curl -X POST http://localhost:3100/api/validate -H "x-webhook-secret: $SECRET" -H "Content-Type: application/json" -d '{"email":"clean@example.com"}'` — returns `{ allowed: true }`
5. [ ] `curl -X POST http://localhost:3100/api/unsubscribe -H "Content-Type: application/json" -d '{"email":"unsub@example.com"}'` — returns confirmation HTML, email added to suppression_list with reason 'unsubscribe'
6. [ ] `node compliance.js suppress bad@example.com --reason spam_complaint --source manual` — adds to list, Telegram alert sent
7. [ ] `node compliance.js validate test@example.com` — prints blocked + reasons
8. [ ] `node compliance.js status` — prints stats table with correct counts
9. [ ] `node compliance.js sync` — syncs pending suppressions to SmartLead and Instantly, updates sync_status
10. [ ] `node compliance.js gdpr user@example.de` — creates GDPR request, adds suppression, sends Telegram alert
11. [ ] `node compliance.js report --type weekly` — generates HTML + PDF report in reports/ folder
12. [ ] `node compliance.js audit test@example.com` — prints full audit trail for that email
13. [ ] Submit same suppression twice — second time returns `was_duplicate: true`, only one record in suppression_list
14. [ ] Kill Supabase connection, call /api/validate — must return `{ allowed: false }` (fail closed)
15. [ ] Send webhook without x-webhook-secret header — must return 401
16. [ ] Let it run overnight, check Telegram for 9am daily summary

---

## Build Order

Tell Claude: Build in this exact order, testing each module before moving to the next.

1. `src/config.js` + `src/db.js` — foundation, test with `node -e "require('./src/db')"`
2. `src/notify.js` — test by sending a test Telegram message
3. `src/suppress.js` — test by adding a suppression via code, verify it appears in Supabase
4. `src/validate.js` — test with suppressed email (should block) and clean email (should allow)
5. `src/classifier.js` — test with sample unsubscribe messages: "remove me" → unsubscribe, "not interested" → not_interested, "this is spam I'll report you" → hostile
6. `src/unsubscribe.js` — test with clear and ambiguous unsubscribe requests
7. `src/sync.js` — test sync to SmartLead and Instantly (need active accounts)
8. `src/gdpr.js` — test GDPR request flow: receive → delete → confirm
9. `src/report.js` — test report generation (HTML renders, PDF generates)
10. `src/server.js` — wire Express routes, test all endpoints with curl
11. `compliance.js` — wire CLI commands with commander, test each subcommand
12. `templates/` — create HTML templates, verify they render correctly
13. `cron-setup.sh` — install and verify cron jobs (or verify node-cron runs in server mode)
