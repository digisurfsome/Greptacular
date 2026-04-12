# Email Warmup Manager — CLAUDE.md Build File

> **What this is:** Drop this file as CLAUDE.md into a project folder, run `claude`, and it builds the complete email warmup monitoring system. This was produced BY the Operating System Creator framework as a proof of concept.

---

## Mission

Build a Node.js CLI system that monitors and manages email mailbox warmup for cold email campaigns. The system checks domain health, mailbox health, manages warmup volume ramp schedules, processes bounces, and alerts via Telegram when issues arise. It runs on a cron schedule every 4 hours on a VPS.

---

## API Keys Required

```
# .env file
SMARTLEAD_API_KEY=your_smartlead_api_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_service_role_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
GOOGLE_POSTMASTER_CLIENT_EMAIL=your_service_account@project.iam.gserviceaccount.com
GOOGLE_POSTMASTER_PRIVATE_KEY=your_private_key
```

### How to get each key:

**SmartLead:** Log in > Settings > API > copy API key. Need Pro plan ($39/mo) for API access.

**Supabase:** Create project at supabase.com > Settings > API > copy Project URL and service_role key (not anon key).

**Telegram Bot:** Message @BotFather on Telegram > /newbot > copy token. Then message your bot, visit `https://api.telegram.org/bot<TOKEN>/getUpdates` to find your chat_id.

**Google Postmaster Tools:** Google Cloud Console > Create project > Enable Gmail Postmaster Tools API > Create Service Account > Download JSON key > Extract client_email and private_key. Then add the service account email as a verified owner in Google Postmaster Tools for each domain.

---

## Tech Stack

```json
{
  "dependencies": {
    "dotenv": "^16.0.0",
    "@supabase/supabase-js": "^2.0.0",
    "node-fetch": "2",
    "googleapis": "^130.0.0",
    "commander": "^11.0.0",
    "cli-table3": "^0.6.0"
  }
}
```

Runtime: Node.js 18+

---

## Database Schema

Create these tables in Supabase before running:

```sql
-- Domains being monitored
CREATE TABLE domains (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  domain TEXT UNIQUE NOT NULL,
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'warning', 'paused', 'retired')),
  reputation TEXT DEFAULT 'unknown',
  spam_rate DECIMAL DEFAULT 0,
  spf_pass BOOLEAN DEFAULT false,
  dkim_pass BOOLEAN DEFAULT false,
  dmarc_pass BOOLEAN DEFAULT false,
  last_checked TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Individual mailboxes
CREATE TABLE mailboxes (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  domain_id UUID REFERENCES domains(id),
  smartlead_account_id TEXT,
  status TEXT DEFAULT 'created' CHECK (status IN (
    'created', 'dns_configured', 'warming', 'warm_ready',
    'active_sending', 'warning', 'paused', 'retired'
  )),
  warmup_start_date DATE,
  warmup_day INTEGER DEFAULT 0,
  daily_volume INTEGER DEFAULT 0,
  target_volume INTEGER DEFAULT 5,
  bounce_rate DECIMAL DEFAULT 0,
  total_sent INTEGER DEFAULT 0,
  total_bounced INTEGER DEFAULT 0,
  last_checked TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Event log for audit trail
CREATE TABLE health_events (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  mailbox_id UUID REFERENCES mailboxes(id),
  domain_id UUID REFERENCES domains(id),
  event_type TEXT NOT NULL,
  severity TEXT CHECK (severity IN ('info', 'warning', 'critical')),
  details JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_health_events_mailbox ON health_events(mailbox_id, created_at DESC);
CREATE INDEX idx_health_events_severity ON health_events(severity, created_at DESC);

-- Bounced addresses - never email these again
CREATE TABLE suppression_list (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  bounce_type TEXT CHECK (bounce_type IN ('hard', 'soft_permanent', 'spam_complaint')),
  source_mailbox TEXT,
  original_campaign TEXT,
  bounced_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_suppression_email ON suppression_list(email);

-- Daily snapshots for trend tracking
CREATE TABLE daily_snapshots (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  mailbox_id UUID REFERENCES mailboxes(id),
  snapshot_date DATE DEFAULT CURRENT_DATE,
  emails_sent INTEGER DEFAULT 0,
  bounces INTEGER DEFAULT 0,
  bounce_rate DECIMAL DEFAULT 0,
  replies INTEGER DEFAULT 0,
  spam_complaints INTEGER DEFAULT 0,
  UNIQUE(mailbox_id, snapshot_date)
);
```

---

## Pipeline Architecture

```
node warmup.js check        ← Runs every 4 hours via cron
  │
  ├── Step 1: check-domains    (Google Postmaster API → domain reputation)
  ├── Step 2: check-mailboxes  (SmartLead API → per-mailbox stats)
  ├── Step 3: manage-volume    (ramp schedule → SmartLead volume update)
  ├── Step 4: process-bounces  (SmartLead API → bounce detection → suppression list)
  └── Step 5: notify           (Telegram summary + alerts)

node warmup.js add-domain cenra.io          ← Register a new domain
node warmup.js add-mailbox mike@cenra.io    ← Register a new mailbox
node warmup.js status                       ← Show all mailbox statuses
node warmup.js report                       ← Weekly health report
```

---

## File Structure

```
warmup-manager/
├── .env
├── package.json
├── CLAUDE.md                  (this file)
├── src/
│   ├── config.js              (env validation + constants)
│   ├── db.js                  (Supabase client + helpers)
│   ├── postmaster.js          (Google Postmaster Tools API)
│   ├── smartlead.js           (SmartLead API - account stats)
│   ├── health.js              (threshold checks + decisions)
│   ├── volume.js              (warmup ramp schedule logic)
│   ├── bounces.js             (bounce detection + suppression)
│   ├── notify.js              (Telegram notifications)
│   └── report.js              (status table + weekly report)
├── warmup.js                  (main CLI entry point)
└── cron-setup.sh              (crontab installer)
```

---

## Module Specifications

### src/config.js
- Load .env with dotenv
- Validate all required env vars exist, exit with clear error if any missing
- Export constants:
  - `BOUNCE_RATE_WARNING = 0.02` (2%)
  - `BOUNCE_RATE_CRITICAL = 0.05` (5%)
  - `SPAM_RATE_WARNING = 0.003` (0.3%)
  - `DOMAIN_REPUTATION_PAUSE = 'LOW'`
  - `WARMUP_RAMP` array (see volume.js section)

### src/db.js
- Create Supabase client
- Helper functions: `getActiveDomains()`, `getActiveMailboxes()`, `getMailboxesByDomain(domainId)`, `updateMailboxStatus(id, status)`, `updateDomainHealth(id, data)`, `logEvent(mailboxId, domainId, type, severity, details)`, `addToSuppressionList(email, bounceType, source)`, `isOnSuppressionList(email)`, `saveDailySnapshot(mailboxId, stats)`

### src/postmaster.js
- Use googleapis package to authenticate with service account
- Function: `getDomainReputation(domain)` — calls Postmaster Tools API
  - Returns: `{ reputation: 'HIGH'|'MEDIUM'|'LOW'|'BAD', spamRate: 0.001, spfPass: true, dkimPass: true, dmarcPass: true }`
  - If API returns no data (domain too new): return `{ reputation: 'INSUFFICIENT_DATA' }`
- Rate limit: max 1 request per second

### src/smartlead.js
- Base URL: `https://server.smartlead.ai/api/v1`
- All requests append `?api_key=${API_KEY}` as query parameter
- Function: `getEmailAccounts()` — GET `/email-accounts` — returns all connected email accounts
- Function: `getAccountStats(accountId)` — GET `/email-accounts/${accountId}/stats` — returns sent count, bounce count, reply count
- Function: `updateAccountSettings(accountId, settings)` — PATCH `/email-accounts/${accountId}` — update daily send limit
- Function: `getCampaignBounces(campaignId)` — GET `/campaigns/${campaignId}/bounces` — returns bounced email addresses
- Rate limit: max 2 requests per second, add 500ms delay between calls

### src/health.js
- Function: `checkDomainHealth(domain, postmasterData)`:
  - If reputation is BAD → status = 'paused', severity = 'critical'
  - If reputation is LOW → status = 'warning', severity = 'warning'
  - If spam rate > 0.3% → severity = 'warning'
  - If SPF/DKIM/DMARC fail → severity = 'critical' (DNS misconfigured)
  - If reputation is HIGH or MEDIUM → status = 'active', severity = 'info'
  - Returns: `{ status, severity, actions: ['pause_all_mailboxes'] | ['reduce_volume'] | [] }`

- Function: `checkMailboxHealth(mailbox, stats)`:
  - Calculate bounce rate: `stats.bounces / stats.sent` (handle division by zero)
  - If bounce rate > 5% → status = 'paused', action = 'pause_48h'
  - If bounce rate > 2% → status = 'warning', action = 'reduce_volume_50pct'
  - If no replies in 5+ days AND in warmup phase → action = 'check_spam_placement'
  - If spam complaints > 0.1% → status = 'paused', action = 'pause_immediately'
  - Otherwise → status unchanged, action = 'continue'
  - Returns: `{ status, severity, action, bounceRate, details }`

### src/volume.js
- Warmup ramp schedule:
  ```
  WARMUP_RAMP = [
    { days: [1, 2, 3],     volume: 5  },
    { days: [4, 5, 6, 7],  volume: 10 },
    { days: [8, 9, 10, 11, 12, 13, 14], volume: 15 },
    { days: [15, 16, 17, 18, 19, 20, 21], volume: 20 },
    { days: 'post_warmup', volume: 25, note: 'Ready for cold sending. Maintain 10 warmup + 15 cold.' }
  ]
  ```
- Function: `getTargetVolume(warmupDay, healthStatus)`:
  - Look up volume from WARMUP_RAMP based on current warmup day
  - If healthStatus is 'warning' → freeze at current volume (don't increase)
  - If healthStatus is 'critical' → reduce to 5/day
  - If healthStatus is 'paused' → reduce to 0/day
  - Returns: `{ targetVolume, reason }`

- Function: `applyVolumeChange(mailbox, targetVolume)`:
  - If targetVolume !== mailbox.daily_volume → call SmartLead API to update
  - Log the change as an event
  - Returns: `{ changed: true|false, from: oldVolume, to: targetVolume }`

### src/bounces.js
- Function: `processBounces()`:
  - Get all active campaigns from SmartLead
  - For each campaign, get bounced addresses
  - For each bounce:
    - Check if already in suppression_list (skip if yes)
    - Add to suppression_list with bounce_type = 'hard'
    - Increment the source mailbox's total_bounced count
    - Recalculate bounce rate
  - Returns: `{ newBounces: count, totalProcessed: count }`

### src/notify.js
- Function: `sendTelegram(message)` — POST to `https://api.telegram.org/bot${TOKEN}/sendMessage` with chat_id and text (parse_mode: 'HTML')
- Function: `sendHealthSummary(results)`:
  - If all healthy: single message with green checkmarks and counts
  - If any warnings: list each warning with mailbox name and metric
  - If any critical: ALERT prefix, list each critical issue with recommended action
- Function: `sendDailySummary(allMailboxes)`:
  - Format: "Daily Warmup Report\n{count} mailboxes active\n{count} warming (days X, Y, Z)\n{count} warnings\n{count} paused"
- Max message length: 4096 chars. If longer, split into multiple messages.

### src/report.js
- Function: `printStatusTable()`:
  - Use cli-table3 to show all mailboxes with columns: Email | Status | Day | Volume | Bounce% | Last Check
  - Color-code: green for healthy, yellow for warning, red for paused/critical
- Function: `generateWeeklyReport()`:
  - Query daily_snapshots for the last 7 days
  - Calculate trends: improving, stable, or declining bounce rates per mailbox
  - Calculate overall stats: total sent, total bounces, average bounce rate, domains at risk
  - Format as both CLI table and Telegram message

### warmup.js (main CLI)
- Use commander for subcommands:
  - `check` — Run full health check pipeline (Steps 1-5). Default command.
  - `add-domain <domain>` — Add a domain to monitor. Creates record in domains table.
  - `add-mailbox <email>` — Add a mailbox. Auto-detects domain, links to domain record, sets warmup_start_date to today.
  - `status` — Print status table of all mailboxes.
  - `report` — Generate and display weekly report.
  - `pause <email>` — Manually pause a mailbox.
  - `resume <email>` — Resume a paused mailbox (resets to 5/day volume).
  - `retire <email>` — Permanently retire a mailbox (never use again).

### cron-setup.sh
```bash
#!/bin/bash
# Add warmup check to crontab - runs every 4 hours
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
(crontab -l 2>/dev/null; echo "0 */4 * * * cd $SCRIPT_DIR && node warmup.js check >> logs/warmup.log 2>&1") | sort -u | crontab -
# Add daily summary at 8am
(crontab -l 2>/dev/null; echo "0 8 * * * cd $SCRIPT_DIR && node warmup.js check --daily-summary >> logs/warmup.log 2>&1") | sort -u | crontab -
echo "Cron jobs installed. Warmup check runs every 4 hours. Daily summary at 8am."
```

---

## Rules

1. **Never skip a health check step.** Run all 4 steps every time, even if a previous step found issues. A domain might be fine but an individual mailbox might not.
2. **Always log events.** Every status change, every volume adjustment, every bounce gets a row in health_events. This is the audit trail.
3. **Pause aggressively, resume cautiously.** Auto-pause at 5% bounce rate. But resuming requires manual `warmup.js resume` command — never auto-resume.
4. **Suppression list is permanent.** Once an address is on the suppression list, it never comes off. Pre-check against this list before every campaign send in the main pipeline.
5. **Rate limit all API calls.** SmartLead: 500ms between calls. Postmaster: 1000ms between calls. Never parallelize API calls to the same service.

---

## Testing Checklist

1. [ ] `node warmup.js add-domain testdomain.com` — creates domain record
2. [ ] `node warmup.js add-mailbox test@testdomain.com` — creates mailbox record, links to domain
3. [ ] `node warmup.js status` — shows table with the test mailbox
4. [ ] `node warmup.js check` — runs full pipeline, logs events, sends Telegram summary
5. [ ] Manually set a mailbox bounce_rate to 0.06 in Supabase, run check — should auto-pause and alert
6. [ ] `node warmup.js pause test@testdomain.com` — status changes to paused
7. [ ] `node warmup.js resume test@testdomain.com` — status changes back, volume resets to 5
8. [ ] `node warmup.js report` — generates weekly report
9. [ ] Check cron is installed: `crontab -l` should show the warmup entries
10. [ ] Let it run overnight, check Telegram for the 8am daily summary

---

## Build Order

Tell Claude: Build in this exact order, testing each module before moving to the next.

1. `src/config.js` + `src/db.js` — foundation, test with `node -e "require('./src/db')"` 
2. `src/notify.js` — test by sending a test Telegram message
3. `src/postmaster.js` — test with one domain
4. `src/smartlead.js` — test by listing email accounts
5. `src/health.js` — test with mock data for each threshold
6. `src/volume.js` — test ramp schedule calculations
7. `src/bounces.js` — test bounce processing
8. `src/report.js` — test status table display
9. `warmup.js` — wire it all together with commander
10. `cron-setup.sh` — install and verify cron jobs
