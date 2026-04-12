# Domain Health Monitor — CLAUDE.md Build File

> **What this is:** Drop this file as CLAUDE.md into a project folder, run `claude`, and it builds the complete domain health monitoring system. This was produced BY the Operating System Creator framework as the second proof of concept.

---

## Mission

Build a Node.js CLI system that continuously monitors the health and reputation of sending domains used in cold email campaigns. The system validates DNS records (SPF, DKIM, DMARC), checks Google Postmaster reputation, scans 30+ blacklist providers, analyzes trends over time, and produces a composite health score (0-100) for each domain. It alerts via Telegram when issues arise and auto-pauses mailboxes on critically unhealthy domains. It runs on a cron schedule on a VPS.

---

## API Keys Required

```
# .env file
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_service_role_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
GOOGLE_POSTMASTER_CLIENT_EMAIL=your_service_account@project.iam.gserviceaccount.com
GOOGLE_POSTMASTER_PRIVATE_KEY=your_private_key
```

### How to get each key:

**Supabase:** Create project at supabase.com > Settings > API > copy Project URL and service_role key (not anon key).

**Telegram Bot:** Message @BotFather on Telegram > /newbot > copy token. Then message your bot, visit `https://api.telegram.org/bot<TOKEN>/getUpdates` to find your chat_id.

**Google Postmaster Tools:** Google Cloud Console > Create project > Enable Gmail Postmaster Tools API > Create Service Account > Download JSON key > Extract client_email and private_key. Then add the service account email as a verified owner in Google Postmaster Tools for each domain.

Note: DNS validation (Step 1) and blacklist scanning (Step 3) require NO API keys — they use public DNS lookups via Node.js built-in `dns` module.

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
    "cli-table3": "^0.6.0",
    "chalk": "^4.1.0"
  }
}
```

Runtime: Node.js 18+

Note: No external DNS library needed. Node.js built-in `dns.promises` module handles all DNS resolution (SPF/DKIM/DMARC record lookups and DNSBL blacklist checks).

---

## Database Schema

Create these tables in Supabase before running:

```sql
-- Domains being monitored
CREATE TABLE domains (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  domain TEXT UNIQUE NOT NULL,
  status TEXT DEFAULT 'registered' CHECK (status IN (
    'registered', 'dns_verified', 'monitoring', 'warning', 'paused', 'retired'
  )),
  health_score INTEGER DEFAULT 0,
  last_dns_check TIMESTAMPTZ,
  last_postmaster_check TIMESTAMPTZ,
  last_blacklist_check TIMESTAMPTZ,
  last_score_update TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- DNS record validation results
CREATE TABLE dns_checks (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  domain_id UUID REFERENCES domains(id) ON DELETE CASCADE,
  spf_status TEXT CHECK (spf_status IN ('pass', 'fail', 'missing')),
  spf_record TEXT,
  spf_includes_google BOOLEAN DEFAULT false,
  dkim_status TEXT CHECK (dkim_status IN ('pass', 'fail', 'missing')),
  dkim_record TEXT,
  dmarc_status TEXT CHECK (dmarc_status IN ('pass', 'fail', 'missing', 'policy_weak')),
  dmarc_record TEXT,
  dmarc_policy TEXT,
  cname_fingerprints JSONB DEFAULT '[]',
  records_changed BOOLEAN DEFAULT false,
  checked_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_dns_checks_domain ON dns_checks(domain_id, checked_at DESC);

-- Google Postmaster Tools results
CREATE TABLE postmaster_checks (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  domain_id UUID REFERENCES domains(id) ON DELETE CASCADE,
  reputation TEXT CHECK (reputation IN ('HIGH', 'MEDIUM', 'LOW', 'BAD', 'INSUFFICIENT_DATA')),
  spam_rate DECIMAL DEFAULT 0,
  spf_pass_rate DECIMAL DEFAULT 0,
  dkim_pass_rate DECIMAL DEFAULT 0,
  dmarc_pass_rate DECIMAL DEFAULT 0,
  delivery_error_rate DECIMAL DEFAULT 0,
  user_reported_spam_rate DECIMAL DEFAULT 0,
  checked_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_postmaster_checks_domain ON postmaster_checks(domain_id, checked_at DESC);

-- Blacklist scan results
CREATE TABLE blacklist_checks (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  domain_id UUID REFERENCES domains(id) ON DELETE CASCADE,
  is_listed BOOLEAN DEFAULT false,
  total_listings INTEGER DEFAULT 0,
  listings JSONB DEFAULT '[]',
  checked_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_blacklist_checks_domain ON blacklist_checks(domain_id, checked_at DESC);

-- Daily health snapshots for trend tracking (one per domain per day)
CREATE TABLE daily_health_snapshots (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  domain_id UUID REFERENCES domains(id) ON DELETE CASCADE,
  snapshot_date DATE DEFAULT CURRENT_DATE,
  health_score INTEGER DEFAULT 0,
  dns_score INTEGER DEFAULT 0,
  reputation_score INTEGER DEFAULT 0,
  blacklist_score INTEGER DEFAULT 0,
  trend_score INTEGER DEFAULT 0,
  reputation TEXT,
  spam_rate DECIMAL DEFAULT 0,
  is_blacklisted BOOLEAN DEFAULT false,
  blacklist_count INTEGER DEFAULT 0,
  spf_ok BOOLEAN DEFAULT false,
  dkim_ok BOOLEAN DEFAULT false,
  dmarc_ok BOOLEAN DEFAULT false,
  UNIQUE(domain_id, snapshot_date)
);
CREATE INDEX idx_snapshots_domain_date ON daily_health_snapshots(domain_id, snapshot_date DESC);

-- Event log for audit trail
CREATE TABLE health_events (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  domain_id UUID REFERENCES domains(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL,
  severity TEXT CHECK (severity IN ('info', 'warning', 'critical')),
  details JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_health_events_domain ON health_events(domain_id, created_at DESC);
CREATE INDEX idx_health_events_severity ON health_events(severity, created_at DESC);
```

---

## Pipeline Architecture

```
node domain-health.js check          <-- Runs full pipeline (Steps 1-5)
  |
  |-- Step 1: check-dns       (Node.js dns module -> SPF/DKIM/DMARC validation)
  |-- Step 2: check-postmaster (Google Postmaster API -> reputation + spam rate)
  |-- Step 3: check-blacklists (DNSBL DNS lookups -> 30+ blacklist providers)
  |-- Step 4: analyze-trends   (Supabase historical data -> 7-day/30-day trends)
  |-- Step 5: calculate-score  (weighted formula -> composite 0-100 score)
  +-- Step 6: notify           (Telegram alerts + daily summary)

node domain-health.js add <domain>              <-- Register a domain to monitor
node domain-health.js remove <domain>           <-- Stop monitoring a domain
node domain-health.js status                    <-- Show all domain health scores
node domain-health.js status <domain>           <-- Detailed health for one domain
node domain-health.js report                    <-- Weekly trend report
node domain-health.js pause <domain>            <-- Manually pause a domain
node domain-health.js resume <domain>           <-- Resume monitoring a paused domain
node domain-health.js retire <domain>           <-- Permanently retire a domain
node domain-health.js check-dns <domain>        <-- Run only DNS check for one domain
node domain-health.js check-blacklist <domain>  <-- Run only blacklist scan for one domain
```

---

## File Structure

```
domain-health-monitor/
|-- .env
|-- package.json
|-- CLAUDE.md                     (this file)
|-- src/
|   |-- config.js                 (env validation + constants + thresholds)
|   |-- db.js                     (Supabase client + query helpers)
|   |-- dns-checker.js            (SPF/DKIM/DMARC/CNAME validation via dns module)
|   |-- postmaster.js             (Google Postmaster Tools API client)
|   |-- blacklist-scanner.js      (DNSBL lookups against 30+ providers)
|   |-- trend-analyzer.js         (historical data analysis + trend detection)
|   |-- health-scorer.js          (composite score calculation 0-100)
|   |-- notify.js                 (Telegram notifications)
|   |-- report.js                 (CLI status tables + weekly reports)
|   +-- utils.js                  (shared utilities: retry, delay, IP resolution)
|-- domain-health.js              (main CLI entry point)
+-- cron-setup.sh                 (crontab installer)
```

---

## Module Specifications

### src/config.js

- Load .env with dotenv
- Validate all required env vars exist, exit with clear error if any missing
- Export constants:
  ```js
  // DNS expectations
  const EXPECTED_SPF_INCLUDE = '_spf.google.com'
  const DKIM_SELECTOR = 'google'  // checks google._domainkey.<domain>
  const DMARC_VALID_POLICIES = ['quarantine', 'reject']  // p=none is NOT valid per Google Nov 2025

  // Known cold email tracking CNAME fingerprints to flag
  const CNAME_FINGERPRINTS = [
    'instantly.ai', 'tracking.instantly.ai',
    'smartlead.ai', 'tracking.smartlead.ai',
    'lemlist.com', 'woodpecker.co'
  ]

  // Postmaster thresholds
  const REPUTATION_ACTIONS = {
    BAD:    { action: 'pause', severity: 'critical' },
    LOW:    { action: 'reduce', severity: 'warning' },
    MEDIUM: { action: 'monitor', severity: 'info' },
    HIGH:   { action: 'none', severity: 'info' }
  }
  const SPAM_RATE_WARNING = 0.003    // 0.3%
  const SPAM_RATE_CRITICAL = 0.01    // 1%
  const AUTH_PASS_WARNING = 0.95     // 95%

  // Health score weights (must sum to 100)
  const SCORE_WEIGHTS = {
    dns: 25,          // SPF=8, DKIM=8, DMARC=9
    reputation: 30,   // HIGH=30, MEDIUM=20, LOW=10, BAD=0
    blacklist: 25,    // clean=25, 1 minor=15, 1 major=5, multiple=0
    trend: 20         // improving=20, stable=15, declining=5, rapidly_declining=0
  }

  // Score thresholds
  const SCORE_HEALTHY = 90
  const SCORE_ACCEPTABLE = 70
  const SCORE_WARNING = 50
  const SCORE_CRITICAL = 30

  // Blacklist providers classified by severity
  const MAJOR_BLACKLISTS = ['zen.spamhaus.org', 'sbl.spamhaus.org', 'xbl.spamhaus.org']
  const MINOR_BLACKLISTS = [
    'b.barracudacentral.org',
    'dnsbl.sorbs.net',
    'bl.spamcop.net',
    'cbl.abuseat.org',
    'dnsbl-1.uceprotect.net',
    'psbl.surriel.com',
    'dyna.spamrats.com',
    'noptr.spamrats.com',
    'spam.spamrats.com',
    'db.wpbl.info',
    'bl.emailbasura.org',
    'combined.abuse.ch',
    'dnsbl.dronebl.org',
    'access.redhawk.org',
    'rbl.interserver.net',
    'ubl.unsubscore.com',
    'dnsbl.justspam.org',
    'bl.mailspike.net',
    'bl.spamcannibal.org',
    'backscatter.spameatingmonkey.net',
    'bl.spameatingmonkey.net',
    'netbl.spameatingmonkey.net',
    'ix.dnsbl.manitu.net',
    'truncate.gbudb.net',
    'dnsbl.inps.de',
    'bl.blocklist.de',
    'all.s5h.net',
    'rbl.megarbl.net'
  ]

  // Delisting info for major blacklists
  const DELIST_INSTRUCTIONS = {
    'zen.spamhaus.org': { url: 'https://check.spamhaus.org/listed/', autoExpires: false, notes: 'Must submit manual delisting request. Can take 24-48h.' },
    'sbl.spamhaus.org': { url: 'https://check.spamhaus.org/listed/', autoExpires: false, notes: 'Manual delisting required.' },
    'xbl.spamhaus.org': { url: 'https://check.spamhaus.org/listed/', autoExpires: true, notes: 'Usually auto-expires when spam activity stops.' },
    'b.barracudacentral.org': { url: 'https://www.barracudacentral.org/lookups/lookup-reputation', autoExpires: true, notes: 'Auto-expires after 12h of no spam. Manual request available.' },
    'bl.spamcop.net': { url: 'https://www.spamcop.net/bl.shtml', autoExpires: true, notes: 'Auto-expires within 24-48h if spam stops.' },
    'cbl.abuseat.org': { url: 'https://www.abuseat.org/lookup.cgi', autoExpires: false, notes: 'Self-service delisting available on website.' },
    'dnsbl.sorbs.net': { url: 'http://www.sorbs.net/lookup.shtml', autoExpires: false, notes: 'Must register and request removal.' }
  }
  ```

### src/db.js

- Create Supabase client using SUPABASE_URL and SUPABASE_KEY
- Helper functions:

```js
// Domain CRUD
async function getActiveDomains()
// Returns all domains where status != 'retired'. Sorted by domain name.

async function getDomain(domainName)
// Returns single domain record by domain name. Returns null if not found.

async function addDomain(domainName)
// Insert new domain with status='registered'. Returns the created record.
// Throws if domain already exists.

async function updateDomainStatus(domainId, status, healthScore)
// Update domain status and health_score fields.

async function updateDomainCheckTimestamp(domainId, checkType)
// Update last_dns_check, last_postmaster_check, or last_blacklist_check timestamp.
// checkType is one of 'dns', 'postmaster', 'blacklist', 'score'.

// DNS check results
async function saveDnsCheck(domainId, results)
// Insert row into dns_checks table. results = { spfStatus, spfRecord, spfIncludesGoogle, dkimStatus, dkimRecord, dmarcStatus, dmarcRecord, dmarcPolicy, cnameFingerprints, recordsChanged }

async function getLatestDnsCheck(domainId)
// Returns most recent dns_checks row for this domain.

async function getPreviousDnsCheck(domainId)
// Returns second-most-recent dns_checks row (for change detection).

// Postmaster check results
async function savePostmasterCheck(domainId, data)
// Insert row into postmaster_checks. data = { reputation, spamRate, spfPassRate, dkimPassRate, dmarcPassRate, deliveryErrorRate, userReportedSpamRate }

async function getLatestPostmasterCheck(domainId)
// Returns most recent postmaster_checks row.

// Blacklist check results
async function saveBlacklistCheck(domainId, results)
// Insert row into blacklist_checks. results = { isListed, totalListings, listings: [{ provider, severity, delistUrl, autoExpires }] }

async function getLatestBlacklistCheck(domainId)
// Returns most recent blacklist_checks row.

// Daily snapshots
async function saveDailySnapshot(domainId, snapshotData)
// Upsert into daily_health_snapshots using (domain_id, snapshot_date) as unique key.
// snapshotData = { healthScore, dnsScore, reputationScore, blacklistScore, trendScore, reputation, spamRate, isBlacklisted, blacklistCount, spfOk, dkimOk, dmarcOk }

async function getSnapshots(domainId, days)
// Returns daily_health_snapshots for the last N days, ordered by date DESC.

// Event logging
async function logEvent(domainId, eventType, severity, details)
// Insert into health_events. details is a JSON object with relevant context.

async function getRecentEvents(domainId, limit = 20)
// Returns last N events for a domain, ordered by created_at DESC.
```

### src/dns-checker.js

- Uses Node.js built-in `dns.promises` module (no external dependency)
- Functions:

```js
const dns = require('dns').promises

async function checkDns(domain)
// Master function that runs all DNS checks for a domain.
// Returns: {
//   spf: { status: 'pass'|'fail'|'missing', record: string|null, includesGoogle: boolean },
//   dkim: { status: 'pass'|'fail'|'missing', record: string|null },
//   dmarc: { status: 'pass'|'fail'|'missing'|'policy_weak', record: string|null, policy: string|null },
//   cnameFingerprints: string[],
//   recordsChanged: boolean,
//   overallStatus: 'pass'|'warn'|'fail'
// }

async function checkSpf(domain)
// Resolve TXT records for domain.
// Filter for records starting with 'v=spf1'.
// Check if the SPF record includes '_spf.google.com'.
// Returns: { status, record, includesGoogle }
// If no TXT record contains 'v=spf1' -> status = 'missing'
// If SPF exists but doesn't include google -> status = 'fail'
// If SPF exists and includes google -> status = 'pass'

async function checkDkim(domain)
// Resolve TXT records for 'google._domainkey.<domain>'.
// If record exists and is non-empty -> status = 'pass'
// If NXDOMAIN or empty -> status = 'missing'
// Returns: { status, record }

async function checkDmarc(domain)
// Resolve TXT records for '_dmarc.<domain>'.
// Parse the DMARC record to extract the p= policy value.
// If no record -> status = 'missing'
// If p=none -> status = 'policy_weak' (violates Google Nov 2025 rules)
// If p=quarantine or p=reject -> status = 'pass'
// If record exists but unparseable -> status = 'fail'
// Returns: { status, record, policy }

async function checkCnameFingerprints(domain)
// Check common tracking subdomains for CNAME records pointing to cold email tools.
// Subdomains to check: 'track.<domain>', 'click.<domain>', 'open.<domain>', 'link.<domain>', 'email.<domain>'
// For each subdomain, resolve CNAME and check if it points to any domain in CNAME_FINGERPRINTS.
// Returns: string[] of found fingerprints (e.g., ['track.cenra.io -> tracking.instantly.ai'])
// Silently skip subdomains that don't have CNAME records (NXDOMAIN is normal).

async function detectRecordChanges(domain, previousCheck)
// Compare current DNS check results against the previous check from the database.
// Returns true if any record (SPF, DKIM, DMARC) has changed content.
// Returns false if records are the same or if no previous check exists (first run).
```

### src/postmaster.js

- Use `googleapis` package to authenticate with Google Cloud Service Account
- Functions:

```js
const { google } = require('googleapis')

async function getPostmasterClient()
// Create and cache an authenticated client using GOOGLE_POSTMASTER_CLIENT_EMAIL
// and GOOGLE_POSTMASTER_PRIVATE_KEY. Uses JWT auth with scope
// 'https://www.googleapis.com/auth/postmaster.readonly'.
// Returns the gmailpostmastertools v1 client.

async function checkPostmaster(domain)
// Query the Postmaster Tools API for the given domain.
// API endpoint: domains/{domain}/trafficStats
// Get the most recent date's data (API returns daily aggregates).
// Returns: {
//   reputation: 'HIGH'|'MEDIUM'|'LOW'|'BAD'|'INSUFFICIENT_DATA',
//   spamRate: number (0.0 to 1.0),
//   spfPassRate: number (0.0 to 1.0),
//   dkimPassRate: number (0.0 to 1.0),
//   dmarcPassRate: number (0.0 to 1.0),
//   deliveryErrorRate: number (0.0 to 1.0),
//   userReportedSpamRate: number (0.0 to 1.0)
// }
// If API returns no data (domain too new, too little volume, or not verified):
//   Return { reputation: 'INSUFFICIENT_DATA' } with all rates set to 0.
// Rate limit: max 1 request per second — add 1000ms delay between calls.
```

### src/blacklist-scanner.js

- Uses Node.js built-in `dns.promises` for DNSBL lookups (no external dependency)
- Functions:

```js
const dns = require('dns').promises

async function scanBlacklists(domain)
// Master function that checks a domain's mail server IP against all configured blacklists.
// 1. Resolve the domain's MX records to find the mail server.
// 2. Resolve the MX host to get its IP address.
// 3. Reverse the IP octets (1.2.3.4 -> 4.3.2.1).
// 4. For each blacklist provider, attempt to resolve <reversed-ip>.<provider>.
//    - If it resolves (returns an A record) -> domain IS listed on that blacklist.
//    - If NXDOMAIN (resolution fails) -> domain is NOT listed.
// 5. Classify each listing by severity (major/minor) based on config.
// 6. Look up delisting instructions from DELIST_INSTRUCTIONS.
// Returns: {
//   isListed: boolean,
//   totalListings: number,
//   listings: [{ provider, severity: 'major'|'minor', delistUrl, autoExpires, notes }]
// }

async function resolveMailServerIp(domain)
// Resolve MX records for the domain. Take the highest-priority MX host.
// Then resolve that MX host to an A record (IPv4 address).
// Returns: { mxHost: string, ip: string }
// If MX resolution fails, try resolving the domain's A record directly (some
// setups use A records for mail delivery).
// If all resolution fails, throw with clear error message.

function reverseIp(ip)
// Reverse the octets of an IPv4 address.
// '74.125.200.26' -> '26.200.125.74'
// Returns: string

async function checkSingleBlacklist(reversedIp, provider)
// Attempt to resolve '<reversedIp>.<provider>' via DNS A record lookup.
// If resolves -> return { listed: true, provider }
// If NXDOMAIN -> return { listed: false, provider }
// If timeout (after 5 second timeout) -> return { listed: false, provider, error: 'timeout' }
// Use dns.setServers() is NOT needed — use system DNS resolver.
// Set a per-lookup timeout of 5 seconds to avoid hanging on slow DNSBL servers.

async function scanAllBlacklists(reversedIp, providers)
// Run checkSingleBlacklist for ALL providers concurrently (Promise.allSettled).
// Blacklist lookups are independent — parallelism is safe here.
// Collect results, separate listed vs clean vs failed.
// Returns: { listed: [{ provider, severity }], clean: [provider], failed: [{ provider, error }] }
```

### src/trend-analyzer.js

- Queries Supabase for historical health snapshots
- Functions:

```js
async function analyzeTrends(domainId)
// Pull daily_health_snapshots for the last 30 days.
// Calculate 7-day and 30-day trends for each metric.
// Returns: {
//   reputationTrend: 'improving'|'stable'|'declining'|'rapidly_declining',
//   spamRateTrend: 'improving'|'stable'|'declining'|'rapidly_declining',
//   scoreTrend: 'improving'|'stable'|'declining'|'rapidly_declining',
//   blacklistRecurrence: number,  // times blacklisted in last 30 days
//   dnsChanges: number,           // DNS record changes in last 30 days
//   hasEnoughData: boolean,       // false if < 7 days of snapshots
//   alerts: string[]              // human-readable trend alerts
// }

function calculateTrendDirection(values)
// Given an array of numeric values ordered by date (oldest first),
// determine the trend direction.
// Method: compare average of last 3 values against average of first 3 values.
// If improved by >10% -> 'improving'
// If degraded by >20% -> 'rapidly_declining'
// If degraded by >5% -> 'declining'
// Otherwise -> 'stable'
// Returns: 'improving'|'stable'|'declining'|'rapidly_declining'

function calculateReputationTrend(reputations)
// Convert reputation strings to numeric values (HIGH=4, MEDIUM=3, LOW=2, BAD=1).
// Apply calculateTrendDirection on the numeric array.
// Returns: 'improving'|'stable'|'declining'|'rapidly_declining'

function detectBlacklistRecurrence(snapshots)
// Count how many snapshots in the last 30 days have is_blacklisted=true.
// Returns: number

function detectDnsChanges(snapshots)
// Compare consecutive snapshots' spf_ok/dkim_ok/dmarc_ok values.
// Count transitions (ok -> not ok, or not ok -> ok).
// Returns: number
```

### src/health-scorer.js

- Pure calculation module — no API calls, no database access
- Functions:

```js
function calculateHealthScore(dnsResults, postmasterData, blacklistResults, trendData)
// Combine all inputs into a weighted composite score (0-100).
// Returns: {
//   score: number,              // 0-100
//   grade: string,              // 'healthy'|'acceptable'|'warning'|'critical'|'retire'
//   breakdown: { dns, reputation, blacklist, trend },
//   recommendedAction: string,  // human-readable action
//   details: string[]           // list of contributing factors
// }

function scoreDns(dnsResults)
// Max 25 points.
// SPF: pass=8, fail=0, missing=0
// DKIM: pass=8, fail=0, missing=0
// DMARC: pass(quarantine/reject)=9, policy_weak(none)=3, fail=0, missing=0
// Deduct 2 points per CNAME fingerprint found (min 0 total).
// Returns: { score: number, max: 25, details: string[] }

function scoreReputation(postmasterData)
// Max 30 points.
// Reputation: HIGH=30, MEDIUM=20, LOW=10, BAD=0, INSUFFICIENT_DATA=15 (neutral)
// Spam rate modifier: >1% = -10, >0.3% = -5, <=0.3% = 0
// Auth pass rates: if any < 95%, deduct 3 points
// Returns: { score: number, max: 30, details: string[] }

function scoreBlacklist(blacklistResults)
// Max 25 points.
// Not listed anywhere = 25
// Listed on 1 minor blacklist = 15
// Listed on 1 major blacklist = 5
// Listed on 2+ blacklists (any mix) = 0
// Returns: { score: number, max: 25, details: string[] }

function scoreTrend(trendData)
// Max 20 points.
// If hasEnoughData is false -> return 10 (neutral, not enough history to judge)
// Overall trend improving = 20
// Overall trend stable = 15
// Overall trend declining = 5
// Overall trend rapidly declining = 0
// Blacklist recurrence > 2 in 30 days -> deduct 5
// DNS changes > 1 in 30 days -> deduct 3
// Returns: { score: number, max: 20, details: string[] }

function scoreToGrade(score)
// 90-100 -> 'healthy'
// 70-89  -> 'acceptable'
// 50-69  -> 'warning'
// 30-49  -> 'critical'
// 0-29   -> 'retire'
// Returns: string

function getRecommendedAction(grade, breakdown, details)
// Based on grade, return a human-readable recommendation:
// 'healthy'    -> 'No action needed. Domain is in good health.'
// 'acceptable' -> 'Minor issues detected. Monitor: [specific issues].'
// 'warning'    -> 'Reduce sending volume on this domain. Investigate: [specific issues].'
// 'critical'   -> 'PAUSE all sending on this domain immediately. Issues: [specific issues].'
// 'retire'     -> 'Domain is burned. Begin replacement: buy new domain, start warmup.'
// Returns: string
```

### src/notify.js

- Telegram Bot API integration
- Functions:

```js
async function sendTelegram(message)
// POST to https://api.telegram.org/bot${TOKEN}/sendMessage
// Body: { chat_id: TELEGRAM_CHAT_ID, text: message, parse_mode: 'HTML' }
// Max message length: 4096 chars. If longer, split into multiple messages.
// Retry once on network failure with 3 second delay.
// Returns: boolean (true = sent, false = failed)

async function sendCriticalAlert(domain, issue, details)
// Format:
// "🚨 <b>CRITICAL: {domain}</b>
//  Issue: {issue}
//  Details: {details}
//  Action: {recommended action}
//  Time: {timestamp}"
// Always send immediately — do not batch or delay critical alerts.

async function sendWarningAlert(domain, issue, details)
// Format:
// "⚠️ <b>WARNING: {domain}</b>
//  Issue: {issue}
//  Details: {details}
//  Time: {timestamp}"

async function sendBlacklistAlert(domain, listings)
// Format:
// "🔴 <b>BLACKLISTED: {domain}</b>
//  Listed on: {provider names}
//  Severity: {major/minor}
//  Delist URL: {url}
//  Auto-expires: {yes/no}
//  Instructions: {notes}"
// Include delisting URL and instructions for each listing.

async function sendDailySummary(domainResults)
// Format:
// "📊 <b>Daily Domain Health Report</b>
//  {timestamp}
//
//  {domain1}: {score}/100 {grade} {trend_arrow}
//  {domain2}: {score}/100 {grade} {trend_arrow}
//  ...
//
//  Summary: {healthy_count} healthy, {warning_count} warning, {critical_count} critical
//  Action required: {list domains needing attention}"
// Trend arrows: improving=↑, stable=→, declining=↓, rapidly_declining=⇊
// Only send if there are active domains to report.

async function sendWeeklyTrendReport(trendResults)
// Format:
// "📈 <b>Weekly Domain Trend Report</b>
//  {date range}
//
//  {domain1}: {prev_score}→{curr_score} {trend_word}
//  {domain2}: {prev_score}→{curr_score} {trend_word}
//  ...
//
//  Domains improving: {count}
//  Domains stable: {count}
//  Domains declining: {count}
//  Blacklist incidents this week: {count}"
```

### src/report.js

- CLI status tables and reports using cli-table3 and chalk
- Functions:

```js
async function printStatusTable(domains)
// Use cli-table3 to display all domains with columns:
// Domain | Score | Grade | Reputation | DNS | Blacklisted | Trend | Last Check
// Color coding with chalk:
//   green: score >= 90 (healthy)
//   yellow: score 70-89 (acceptable)
//   magenta: score 50-69 (warning)
//   red: score < 50 (critical/retire)

async function printDetailedStatus(domain)
// Show detailed health breakdown for a single domain:
// - Overall score and grade
// - DNS check results (SPF, DKIM, DMARC with actual record values)
// - Postmaster data (reputation, spam rate, auth rates)
// - Blacklist status (listed/clean, which providers)
// - CNAME fingerprints found
// - Trend data (7-day direction, 30-day direction)
// - Score breakdown (dns/reputation/blacklist/trend contributions)
// - Last 10 events from audit log
// - Recommended action

async function generateWeeklyReport()
// Query daily_health_snapshots for the last 7 days for all domains.
// For each domain: calculate trend direction, score change, key events.
// Format as both CLI table and Telegram message.
// CLI table columns: Domain | 7-Day Score Change | Trend | Blacklist Events | Key Issue
// Also display aggregate stats: total domains, average score, domains at risk.
```

### src/utils.js

- Shared utility functions

```js
async function retry(fn, maxAttempts = 2, delayMs = 3000)
// Execute fn(). If it throws, wait delayMs and retry up to maxAttempts total.
// Returns the result of fn() on success.
// Throws the last error if all attempts fail.

function delay(ms)
// Returns a promise that resolves after ms milliseconds.
// Use between API calls for rate limiting.

async function resolveDomainIp(domain)
// Resolve a domain to its IPv4 address using dns.promises.resolve4().
// Returns the first IP address.
// Throws if resolution fails.

function formatTimestamp(date)
// Format a Date object as 'YYYY-MM-DD HH:mm:ss UTC'.

function truncateMessage(message, maxLength = 4096)
// If message exceeds maxLength, truncate at the last newline before maxLength
// and append '... (truncated)'.
// Returns: string

function splitMessage(message, maxLength = 4096)
// Split a long message into chunks of maxLength, breaking at newline boundaries.
// Returns: string[]
```

### domain-health.js (main CLI)

- Use commander for subcommands:

```js
const { Command } = require('commander')
const program = new Command()

program
  .name('domain-health')
  .description('Domain health monitoring for cold email infrastructure')
  .version('1.0.0')

program
  .command('check')
  .description('Run full health check pipeline on all active domains')
  .option('--daily-summary', 'Include daily summary in Telegram notification')
  .option('--weekly-report', 'Include weekly trend report in Telegram notification')
  .action(async (options) => {
    // 1. Get all active domains from database
    // 2. For each domain, run Steps 1-5 sequentially:
    //    a. checkDns(domain)        -> save results, detect changes
    //    b. checkPostmaster(domain) -> save results (skip if no credentials)
    //    c. scanBlacklists(domain)  -> save results
    //    d. analyzeTrends(domainId) -> calculate from historical data
    //    e. calculateHealthScore()  -> combine all data into 0-100 score
    // 3. Update domain status based on score:
    //    - score >= 70 and status is 'warning' -> transition to 'monitoring'
    //       (only if 3 consecutive checks are above 70)
    //    - score < 50 -> transition to 'paused', log critical event
    //    - score < 70 -> transition to 'warning', log warning event
    // 4. Save daily snapshot
    // 5. Send alerts for any critical/warning issues found
    // 6. If --daily-summary, send Telegram daily summary
    // 7. If --weekly-report, send Telegram weekly trend report
    // 8. Print status table to console
  })

program
  .command('add <domain>')
  .description('Register a new domain to monitor')
  .action(async (domain) => {
    // 1. Validate domain format (basic regex: contains at least one dot, no spaces)
    // 2. Check if domain already exists in database
    // 3. Insert with status='registered'
    // 4. Run initial DNS check immediately
    // 5. If DNS passes, update status to 'dns_verified'
    // 6. Log event: 'domain_added'
    // 7. Print confirmation with DNS check results
  })

program
  .command('remove <domain>')
  .description('Stop monitoring a domain (does not delete history)')
  .action(async (domain) => {
    // 1. Set status to 'retired'
    // 2. Log event: 'domain_removed'
    // 3. Print confirmation
  })

program
  .command('status [domain]')
  .description('Show health status for all domains or a specific domain')
  .action(async (domain) => {
    // If domain specified: printDetailedStatus(domain)
    // If no domain: printStatusTable(allDomains)
  })

program
  .command('report')
  .description('Generate and display weekly trend report')
  .option('--telegram', 'Also send report to Telegram')
  .action(async (options) => {
    // Generate weekly report
    // Print to console
    // If --telegram, send to Telegram as well
  })

program
  .command('pause <domain>')
  .description('Manually pause monitoring/sending for a domain')
  .action(async (domain) => {
    // 1. Set status to 'paused'
    // 2. Log event: 'domain_paused_manual' with severity 'warning'
    // 3. Print confirmation
  })

program
  .command('resume <domain>')
  .description('Resume a paused domain')
  .action(async (domain) => {
    // 1. Run DNS check and blacklist scan first
    // 2. If DNS passes and not blacklisted, set status to 'monitoring'
    // 3. If DNS fails or blacklisted, refuse to resume, explain why
    // 4. Log event: 'domain_resumed' or 'domain_resume_blocked'
    // 5. Print results
  })

program
  .command('retire <domain>')
  .description('Permanently retire a domain (marks as unsalvageable)')
  .action(async (domain) => {
    // 1. Set status to 'retired'
    // 2. Log event: 'domain_retired' with severity 'info'
    // 3. Print confirmation with note that historical data is preserved
  })

program
  .command('check-dns <domain>')
  .description('Run DNS validation for a single domain')
  .action(async (domain) => {
    // Run only Step 1 for the specified domain
    // Print detailed DNS results
  })

program
  .command('check-blacklist <domain>')
  .description('Run blacklist scan for a single domain')
  .action(async (domain) => {
    // Run only Step 3 for the specified domain
    // Print detailed blacklist results
  })
```

### cron-setup.sh

```bash
#!/bin/bash
# Install cron jobs for domain health monitoring
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Create logs directory
mkdir -p "$SCRIPT_DIR/logs"

# Full pipeline check — runs at 8am and 8pm daily
(crontab -l 2>/dev/null; echo "0 8 * * * cd $SCRIPT_DIR && node domain-health.js check --daily-summary >> logs/domain-health.log 2>&1") | sort -u | crontab -
(crontab -l 2>/dev/null; echo "0 20 * * * cd $SCRIPT_DIR && node domain-health.js check >> logs/domain-health.log 2>&1") | sort -u | crontab -

# Blacklist-only scan — runs every 4 hours (blacklisting is time-sensitive)
(crontab -l 2>/dev/null; echo "0 */4 * * * cd $SCRIPT_DIR && node domain-health.js check >> logs/domain-health.log 2>&1") | sort -u | crontab -

# Weekly trend report — runs Monday at 9am
(crontab -l 2>/dev/null; echo "0 9 * * 1 cd $SCRIPT_DIR && node domain-health.js check --weekly-report >> logs/domain-health.log 2>&1") | sort -u | crontab -

echo "Cron jobs installed:"
echo "  - Full health check: 8am and 8pm daily"
echo "  - Blacklist scan: every 4 hours"
echo "  - Weekly trend report: Monday 9am"
echo ""
echo "View logs: tail -f $SCRIPT_DIR/logs/domain-health.log"
```

---

## Rules

1. **DNS checks use NO external APIs.** Node.js `dns.promises` module resolves all records directly. No MXToolbox subscription, no DNS API keys. Keep it free and dependency-light.
2. **Blacklist checks are parallelized.** Unlike other API calls that must be sequential, DNSBL lookups are independent DNS queries — run all 30+ lookups with `Promise.allSettled()` for speed.
3. **Never auto-resume a paused domain.** Auto-pause is aggressive (good). But resuming requires manual `domain-health.js resume` which re-validates DNS and blacklists before allowing it. Prevents premature re-send on a still-broken domain.
4. **Always log events.** Every status change, every score calculation, every blacklist detection, every DNS change gets a row in health_events. This is the audit trail that answers "what happened to this domain?"
5. **Missing data does not equal good data.** If Postmaster returns no data, assign a neutral score (15/30), not a perfect score. If blacklist check times out, do not mark as clean — mark as "check_failed" and try again next cycle.
6. **Daily snapshots are sacred.** One snapshot per domain per day, saved via upsert. These are the foundation for all trend analysis. Never skip saving a snapshot, even if partial data.
7. **Rate limit Postmaster API.** 1000ms delay between calls. The API has undocumented rate limits that will silently return empty data if exceeded.
8. **DMARC p=none is a FAILURE.** Per Google's November 2025 rules, p=none no longer provides protection. Treat it as "policy_weak" — not as bad as missing, but not passing either. Score it at 3/9 instead of 9/9.
9. **Composite score is always recalculated from latest data.** Never cache or carry forward old scores. Each check run recalculates the score from the freshest data available for each component.
10. **Trend analysis requires 7+ days of data.** Do not calculate trends for domains with fewer than 7 daily snapshots. Assign a neutral trend score (10/20) until enough history exists.

---

## Testing Checklist

1. [ ] `node domain-health.js add testdomain.com` — creates domain record with status 'registered'
2. [ ] `node domain-health.js check-dns testdomain.com` — runs DNS check, prints SPF/DKIM/DMARC results
3. [ ] `node domain-health.js add realdomain.com` (use a domain you own) — should detect actual DNS records
4. [ ] `node domain-health.js check-blacklist realdomain.com` — scans 30+ blacklists, should return clean for a healthy domain
5. [ ] `node domain-health.js check` — runs full pipeline on all domains, sends Telegram summary
6. [ ] `node domain-health.js status` — displays table with all domains and scores
7. [ ] `node domain-health.js status realdomain.com` — shows detailed breakdown for one domain
8. [ ] Manually insert a daily_health_snapshot with lower scores for 7 past days, run check — should detect declining trend
9. [ ] `node domain-health.js pause realdomain.com` — status changes to paused
10. [ ] `node domain-health.js resume realdomain.com` — runs DNS + blacklist check first, then resumes if clean
11. [ ] `node domain-health.js report` — generates weekly trend report
12. [ ] `node domain-health.js report --telegram` — sends trend report to Telegram
13. [ ] Verify Telegram receives critical alert when a domain has DNS misconfiguration
14. [ ] Verify Telegram receives blacklist alert (test with a known-blacklisted IP if available)
15. [ ] Let it run for 7+ days, verify trend analysis produces meaningful results
16. [ ] Check cron is installed: `crontab -l` should show the domain health entries

---

## Build Order

Tell Claude: Build in this exact order, testing each module before moving to the next.

1. `src/config.js` + `src/utils.js` — foundation, constants, retry/delay helpers. Test with `node -e "require('./src/config')"`
2. `src/db.js` — Supabase client and all query helpers. Test by inserting and reading a test domain.
3. `src/notify.js` — Telegram integration. Test by sending a test message.
4. `src/dns-checker.js` — SPF/DKIM/DMARC/CNAME validation. Test against a known domain (e.g., your own). This module has ZERO external dependencies beyond Node.js built-in `dns`.
5. `src/postmaster.js` — Google Postmaster API client. Test with one verified domain. Skip if credentials not yet configured — the system should work without Postmaster data (assigns neutral score).
6. `src/blacklist-scanner.js` — DNSBL lookups. Test against a known-clean domain. Verify all 30+ providers are checked and results are correctly classified.
7. `src/trend-analyzer.js` — historical analysis. Test with manually inserted snapshot data.
8. `src/health-scorer.js` — composite score calculation. Test with mock data for every grade level (healthy/acceptable/warning/critical/retire). This is pure calculation — easiest to unit test.
9. `src/report.js` — CLI status tables and reports. Test formatting with sample data.
10. `domain-health.js` — wire everything together with commander. Test each subcommand.
11. `cron-setup.sh` — install and verify cron jobs.
