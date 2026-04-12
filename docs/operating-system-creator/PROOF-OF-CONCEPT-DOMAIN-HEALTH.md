# Operating System Creator — Proof of Concept: Domain Health Monitoring

> **What this is:** We're running the Wizard Questionnaire (Part 2) on the "domain health monitoring" gap from the cold email system. This is a STANDALONE monitoring system — separate from the warmup manager's Step 1 domain check — that provides comprehensive DNS validation, blacklist monitoring, trend analysis, and composite health scoring across all sending domains.

---

## Section A: Big Picture (Filled Out)

**A1. Process name:** Domain Health Monitor

**A2. What a human does today:**
1. Log into Google Postmaster Tools for each domain — check reputation (High/Medium/Low/Bad), spam rate, authentication pass rates
2. Open MXToolbox.com (or similar) — run each domain through blacklist checks against 80+ providers
3. Log into the DNS provider (Cloudflare, Namecheap) — verify SPF, DKIM, and DMARC records are still correctly configured and haven't been accidentally modified or deleted
4. Check for stale CNAME tracking records pointing to Instantly or SmartLead — these are fingerprints that get domains flagged
5. Compare today's metrics against last week — is reputation trending up or down? Is spam rate creeping up?
6. Calculate a mental "health score" for each domain — factor in reputation, DNS, blacklists, spam rate, bounce rate
7. If a domain is unhealthy: pause all mailboxes on it, investigate root cause, potentially retire the domain
8. If a domain is blacklisted: look up the specific blacklist's delisting process, submit delisting request, monitor until removed
9. Log findings in a spreadsheet for historical tracking
10. Repeat daily for every domain (5-15 domains per business, more for agencies)

**A3. How often:** Daily monitoring for active sending domains. Twice daily during high-volume campaigns.

**A4. How long per run:** 45-90 minutes for a full check across 10-15 domains. Longer when issues are found and need investigation.

**A5. Items per run:** 10-15 domains per business, 50-100+ for agencies managing multiple clients.

**A6. Starting data:**
- Google Postmaster Tools (domain reputation, spam rate, auth rates)
- DNS records (SPF, DKIM, DMARC TXT records at the domain's DNS provider)
- Blacklist DNS servers (DNSBL lookups against known blacklist providers)
- Historical health data (previous days' snapshots for trend analysis)

**A7. End result goes to:**
- Supabase (health snapshots, trend data, blacklist history)
- Telegram (alerts when issues arise, daily health summaries)
- CLI output (operator dashboard with health scores)

**A8. Tools already in use:**

| Tool/Service | What it's used for | Has API? |
|---|---|---|
| Google Postmaster Tools | Domain reputation and spam rate | Yes (Gmail Postmaster Tools API via Google Cloud Service Account) |
| MXToolbox | Blacklist checking | Yes (paid) — but DNS-based blacklist lookups are free via Node.js `dns` module |
| Cloudflare / Namecheap | DNS record management | Yes — but for READ-ONLY checks, Node.js `dns` module works without credentials |
| Supabase | Health data storage and trend history | Yes (@supabase/supabase-js) |
| Telegram | Alerts and summaries | Yes (Bot API) |

**A9. What breaks most often:**
- DNS records silently changed or deleted — someone edits DNS and accidentally removes the DKIM record, emails start failing authentication and go straight to spam. Nobody notices for days.
- Domain lands on a blacklist — deliverability drops to near zero overnight. Without automated checking, the operator doesn't know until reply rates collapse days later.
- Reputation degradation is gradual and invisible — a domain goes from HIGH to MEDIUM to LOW over two weeks. By the time the operator checks, it's too late to recover without pausing.
- Google's November 2025 rule changes — SPF/DKIM/DMARC failures now result in REJECTION (not just spam-foldering). DMARC must be p=quarantine or p=reject. Domains configured with p=none are now non-compliant.
- Tracking domain CNAME records left pointing to old services — these act as fingerprints that email providers use to flag the domain as a cold email sender.
- One bad domain poisons the perception of others — shared IP patterns or similar sending behavior can create cross-contamination.

**A10. Legal/compliance:** CAN-SPAM requires valid physical address and unsubscribe mechanism. Google requires spam complaint rate below 0.3% and bounce rate below 2%. DMARC policy must be p=quarantine or p=reject per Google's November 2025 requirements. No special legal issues with the monitoring itself — it's reading publicly available DNS records and using authorized API access.

---

## Section B: Step Breakdown

### Step 1: DNS Records Validation

**B1. What the human does:** For each domain, open a DNS lookup tool or log into the DNS provider. Check that SPF, DKIM, and DMARC records exist and are correctly configured. Verify SPF includes `_spf.google.com`. Verify DKIM exists at `google._domainkey.domain.com`. Verify DMARC is set to `p=quarantine` or `p=reject` (not `p=none`). Check for stale CNAME records pointing to Instantly, SmartLead, or other cold email tools (fingerprint risk).

**B2. Input needed:** List of domains to check. No credentials needed — DNS records are public and can be queried using Node.js `dns` module.

**B3. Decisions:**
- SPF record missing or doesn't include `_spf.google.com` → critical, emails will fail SPF authentication
- DKIM record missing at `google._domainkey.domain.com` → critical, emails will fail DKIM authentication
- DMARC record missing or set to `p=none` → critical, violates Google's November 2025 requirement
- DMARC set to `p=quarantine` → acceptable but `p=reject` is better
- CNAME records pointing to Instantly/SmartLead tracking domains → warning, fingerprint risk
- Any record changed since last check → alert, investigate whether intentional

**B4. Could Claude decide?** Yes, with clear rules. DNS validation is deterministic — records either match the expected values or they don't. No judgment needed.

**B5. Output:** Per-domain DNS health report: `{ spf: pass|fail|missing, dkim: pass|fail|missing, dmarc: pass|fail|missing|policy_weak, cnameFingerprints: [], recordChanges: [] }`

**B6. Output goes to:** Database (dns_checks table) + Telegram (critical alert if any record is missing or misconfigured) + feeds into Step 5 (composite score calculation).

**B7. API tool:** Node.js built-in `dns` module (specifically `dns.promises.resolveTxt()` and `dns.promises.resolveCname()`). Free, no API key needed, no rate limits.

| Tool | API? | Cost | Notes |
|---|---|---|---|
| Node.js `dns` module | Built-in | Free | Resolves TXT, CNAME, MX records directly |

**B8. Error case:** DNS resolution timeout (domain's nameservers slow or down). Action: retry once after 5 seconds. If still failing, log as "dns_unreachable" and alert operator. Do not treat timeout as a failure — the records may still be correct.

**B9. Human time:** 3-5 minutes per domain manually checking each record type. 30-60 minutes for 10-15 domains.

---

### Step 2: Google Postmaster Reputation Check

**B1. What the human does:** Log into Google Postmaster Tools dashboard. For each verified domain, check: domain reputation (HIGH/MEDIUM/LOW/BAD), spam rate percentage, SPF/DKIM/DMARC authentication pass rates, delivery error rate, and user-reported spam rate.

**B2. Input needed:** List of domains, Google Cloud Service Account credentials with Gmail Postmaster Tools API enabled. Each domain must be verified in Google Postmaster Tools with the service account added as a verified owner.

**B3. Decisions:**
- Reputation BAD → Pause ALL mailboxes on this domain immediately. Domain may be unsalvageable.
- Reputation LOW → Reduce all mailboxes to 5/day. Domain is at risk.
- Reputation MEDIUM → Monitor closely but no action needed. Normal for newer domains.
- Reputation HIGH → All clear. Optimal sending reputation.
- Spam rate > 0.3% → Alert. Investigate which mailbox or campaign is causing complaints.
- Spam rate > 1% → Pause domain. Something is seriously wrong.
- Authentication pass rate < 95% → Warning. Likely DNS misconfiguration (feeds back to Step 1).

**B4. Could Claude decide?** Yes, with clear threshold rules above. Pure comparison against known thresholds — no judgment needed.

**B5. Output:** Per-domain Postmaster health: `{ reputation, spamRate, spfPassRate, dkimPassRate, dmarcPassRate, deliveryErrorRate, userReportedSpamRate }`

**B6. Output goes to:** Database (postmaster_checks table) + Telegram (if reputation is LOW or BAD, or spam rate exceeds threshold) + feeds into Step 5 (composite score calculation).

**B7. API tool:** Google Gmail Postmaster Tools API via `googleapis` npm package.

| Tool | API? | Cost | Notes |
|---|---|---|---|
| Google Postmaster Tools API | Yes | Free | Requires Google Cloud Service Account, domain verification |

**B8. Error case:** API returns no data (domain too new, too little sending volume, or not verified). Action: mark as "insufficient_data", do not treat as failure. Alert operator only if a domain that previously had data suddenly returns none (could indicate verification was removed).

**B9. Human time:** 5-10 minutes per domain navigating the Postmaster Tools dashboard. 30-60 minutes for 10-15 domains.

---

### Step 3: Blacklist Scanning

**B1. What the human does:** Go to MXToolbox.com or a similar multi-blacklist checker. Enter each domain. Wait for results across 80+ blacklist providers. If listed on any blacklist: note which one, look up the delisting process, submit delisting request if possible.

**B2. Input needed:** List of domains. No credentials needed — blacklist checks use DNS lookups against known DNSBL (DNS-based Blackhole List) servers.

**B3. Decisions:**
- Listed on Spamhaus → Critical. Spamhaus is the most impactful blacklist. Deliverability will be severely degraded across all major email providers. Delisting requires visiting their website and following the removal process.
- Listed on Barracuda → Warning. Significant impact on corporate email deliverability. Auto-expires after 12 hours of no spam activity, or can be manually requested.
- Listed on SORBS → Warning. Moderate impact. Delisting available through their website.
- Listed on SpamCop → Warning. Usually auto-expires within 24-48 hours if spam stops.
- Listed on CBL (Composite Blocking List) → Warning. Typically means compromised machine or botnet activity. Self-service delisting available.
- Listed on any other provider → Monitor. Less impactful individually but cumulative listings indicate serious problems.
- Not listed anywhere → All clear.

**B4. Could Claude decide?** Yes — this is a lookup operation (listed or not listed) followed by severity classification based on which blacklist. No judgment needed.

**B5. Output:** Per-domain blacklist report: `{ listed: true|false, listings: [{ provider, severity, delistUrl, autoExpires }], totalListings: count }`

**B6. Output goes to:** Database (blacklist_checks table) + Telegram (immediate alert if listed on any blacklist, with delisting instructions) + feeds into Step 5 (composite score calculation).

**B7. API tool:** Node.js `dns` module — reverse-DNS lookups against known DNSBL servers. Each blacklist provider has a DNS zone (e.g., `zen.spamhaus.org`, `b.barracudacentral.org`). To check if a domain's IP is listed, resolve `<reversed-ip>.zen.spamhaus.org`. If it resolves, the IP is listed.

| Tool | API? | Cost | Notes |
|---|---|---|---|
| Node.js `dns` module (DNSBL lookups) | Built-in | Free | Reverse-DNS lookup against blacklist DNS zones |
| MXToolbox API | Yes | $99/mo+ | Alternative, but DNS-based approach is free and sufficient |

**B8. Error case:** DNSBL server not responding (timeout). Action: skip that provider, note as "check_failed", continue with remaining providers. Retry failed providers on next run. If consistently failing, the DNSBL server may be down — do not alert operator for DNSBL downtime.

**B9. Human time:** 2-5 minutes per domain on MXToolbox. 20-50 minutes for 10-15 domains, longer if delisting is required.

---

### Step 4: Trend Analysis

**B1. What the human does:** Open the tracking spreadsheet. Compare today's metrics against the last 7 days and 30 days. Look for patterns: Is reputation trending down? Is spam rate creeping up? Are bounce rates increasing? Identify domains that are gradually degrading before they hit critical thresholds.

**B2. Input needed:** Historical health data from the database — daily snapshots of reputation, spam rate, DNS status, and blacklist status for each domain over the past 30 days.

**B3. Decisions:**
- Reputation dropped from HIGH to MEDIUM in the last 7 days → Warning. Something changed — investigate sending patterns.
- Spam rate increased by more than 0.1% over the past 7 days → Warning. Trend is heading toward the 0.3% threshold.
- Domain was on a blacklist 2+ times in the past 30 days → Warning. Recurring blacklisting indicates a systemic issue.
- DNS records changed in the last 24 hours → Alert. Intentional change should be confirmed; accidental change needs immediate attention.
- All metrics stable or improving → No action.

**B4. Could Claude decide?** Yes — trend analysis is comparing current values against historical values and checking for directional changes. Pure math, no judgment needed.

**B5. Output:** Per-domain trend report: `{ reputationTrend: 'improving'|'stable'|'declining', spamRateTrend, bounceRateTrend, blacklistRecurrence: count, dnsChanges: count, alerts: [] }`

**B6. Output goes to:** Database (trend_reports table) + Telegram (weekly trend summary, immediate alert if declining trends detected) + feeds into Step 5 (composite score calculation).

**B7. API tool:** No external API — this step queries the Supabase database for historical data and performs calculations.

| Tool | API? | Cost | Notes |
|---|---|---|---|
| Supabase (querying existing data) | Yes | Included in existing plan | Queries daily_health_snapshots table |

**B8. Error case:** Insufficient historical data (domain added less than 7 days ago). Action: skip trend analysis, note as "insufficient_history", only perform trend analysis once 7+ days of data exist.

**B9. Human time:** 10-15 minutes reviewing spreadsheet data and identifying patterns. More if trends require investigation.

---

### Step 5: Composite Health Score Calculation

**B1. What the human does:** Mentally combine all the data from Steps 1-4 into an overall assessment for each domain. "This domain has good reputation, DNS is fine, not blacklisted, trends are stable — it's healthy." Or: "Reputation dropped, spam rate is creeping up, was blacklisted last week — this domain needs attention."

**B2. Input needed:** Results from Steps 1-4 for each domain: DNS validation results, Postmaster reputation data, blacklist scan results, trend analysis.

**B3. Decisions:**
- Score 90-100 → Healthy. No action needed.
- Score 70-89 → Acceptable. Minor issues to monitor.
- Score 50-69 → Warning. Reduce sending volume on this domain, investigate root cause.
- Score 30-49 → Critical. Pause all sending on this domain immediately.
- Score 0-29 → Retire. Domain is burned. Begin replacement process.

Scoring formula (out of 100):
- DNS validation: 25 points (SPF=8, DKIM=8, DMARC=9 — DMARC weighted higher due to Google's November 2025 rules)
- Postmaster reputation: 30 points (HIGH=30, MEDIUM=20, LOW=10, BAD=0)
- Blacklist status: 25 points (clean=25, listed on 1 minor=15, listed on 1 major=5, listed on multiple=0)
- Trend stability: 20 points (improving=20, stable=15, declining=5, rapidly declining=0)

**B4. Could Claude decide?** Yes — this is a weighted formula with deterministic inputs. No judgment needed.

**B5. Output:** Per-domain composite health score: `{ score: 0-100, grade: 'healthy'|'acceptable'|'warning'|'critical'|'retire', breakdown: { dns, reputation, blacklist, trend }, recommendedAction }`

**B6. Output goes to:** Database (domain_health_scores table, updates domain status) + Telegram (daily summary with all domain scores, immediate alert for any domain below 50) + CLI output (operator dashboard).

**B7. API tool:** No external API — pure calculation based on data from Steps 1-4.

| Tool | API? | Cost | Notes |
|---|---|---|---|
| Internal calculation | N/A | Free | Weighted formula using existing data |

**B8. Error case:** Missing data from one or more previous steps (e.g., Postmaster API returned no data). Action: calculate score from available data only, note which components are missing, reduce max possible score proportionally. Never assign a high score when data is missing — err on the side of caution.

**B9. Human time:** 5-10 minutes per domain to mentally calculate and categorize. This is the step that benefits most from automation because humans are bad at consistently weighting multiple factors.

---

## Section C: Operations Layer (Filled Out)

### State Tracking

**C1. Statuses per domain:**
`registered → dns_verified → monitoring → warning → paused → retired`

Status transitions:
- `registered` → `dns_verified`: DNS records validated, SPF/DKIM/DMARC all passing
- `dns_verified` → `monitoring`: First Postmaster data received, baseline established
- `monitoring` → `warning`: Health score drops below 70 or any single metric trips a warning threshold
- `warning` → `monitoring`: Health score recovers above 70 for 3 consecutive checks
- `monitoring` → `paused`: Health score drops below 50 or any single metric trips a critical threshold
- `warning` → `paused`: Health score drops below 50
- `paused` → `monitoring`: Manual resume after investigation (never auto-resume)
- Any status → `retired`: Manual retirement when domain is deemed unsalvageable

**C2. Audit trail:** Yes — full event log. Need to know exactly when a domain's health changed, what triggered the change, and what automated action was taken. Critical for post-mortem analysis when a domain is burned ("What happened? When did things go wrong? Could we have caught it earlier?").

**C3. Dedup:** Unique identifier = domain name (e.g., `cenra.io`). Each domain appears exactly once. Daily health snapshots are deduplicated by `(domain, snapshot_date)` — one snapshot per domain per day.

### Notifications

**C4. Who needs to know:** Just me (solo operator). Later: clients if running as agency (per-client domain dashboards).

**C5. What they need to know:**
- Instant critical alert: "CRITICAL: cenra.io SPF record MISSING — emails will fail authentication. Fix DNS immediately."
- Instant blacklist alert: "ALERT: cenra.io listed on Spamhaus. Deliverability severely impacted. Delist at: [URL]"
- Daily summary: "Domain Health Report — 8 domains: 6 healthy (avg score 92), 1 warning (getcenra.com: score 64, spam rate rising), 1 paused (trycentra.co: score 38, blacklisted)."
- Weekly trend report: "Weekly Trends — cenra.io: stable (92→93). getcenra.com: declining (85→64, investigate). trycentra.co: recovering (38→52, consider resuming)."

**C6. How:** Telegram for instant alerts + daily summaries. Telegram for weekly trend reports. All notifications go to a single Telegram chat (configurable per-client for agency mode).

### Scheduling

**C7. When:**
- DNS validation: Every 6 hours (DNS changes are infrequent but catastrophic when wrong)
- Postmaster reputation: Every 12 hours (data updates once daily in Postmaster Tools anyway)
- Blacklist scan: Every 4 hours (blacklistings can happen anytime and need rapid detection)
- Trend analysis: Once daily at 8am (feeds into the daily summary)
- Composite score: After every check run (recalculated using latest data)
- Full pipeline (all steps): Twice daily — 8am and 8pm

**C8. Failure recovery:** Resume from where it left off. Each domain is checked independently — if one domain's check fails, continue with the remaining domains. Each step is independent — if Postmaster API is down, still run DNS checks and blacklist scans.

**C9. Infrastructure:** Cloud server (same VPS as the rest of the cold email pipeline). Hetzner or DigitalOcean, $6-12/month. DNS checks and blacklist lookups are lightweight — no significant resource usage.

---

## Section D: Success Criteria (Filled Out)

**D1. Metrics:**

| Metric | Current (Manual) | Target (Automated) |
|---|---|---|
| Time spent on domain health monitoring | 45-90 min/day | 5 min/day (review Telegram alerts) |
| Time to detect DNS misconfiguration | 12-48 hours (next manual check) | < 6 hours (automated check cycle) |
| Time to detect blacklisting | 24-72 hours (often discovered via reply rate drop) | < 4 hours (automated blacklist scan) |
| Domains burned per quarter due to late detection | 1-3 domains ($8-12 each + $30-120/mo in Google Workspace waste) | 0 (auto-pause catches issues before domain is unsalvageable) |
| Domains monitored per operator | 10-15 (manual ceiling) | 100+ (automated monitoring) |
| Trend-based early warnings | 0 (humans don't track trends consistently) | Daily trend analysis catches degradation before thresholds hit |

**D2. Human cost:** 45-90 min/day x 30 days = 22-45 hours/month. At $50/hour contractor rate = $1,100-2,250/month. Plus the hidden cost of burned domains: a burned domain doesn't just waste the $8-12 domain cost — it wastes the $30-120/month in Google Workspace accounts attached to it, and the 2-3 weeks of warmup time already invested.

**D3. Budget:** Minimal — Google Postmaster API is free. DNS lookups via Node.js are free. Blacklist DNS lookups are free. Supabase free tier handles the data volume. Telegram bot is free. Total additional cost: $0/month beyond existing infrastructure.

**D4. MVP step:** Step 1 (DNS Records Validation) — this catches the most catastrophic failure mode (authentication failures that cause all emails to be rejected). It requires zero API credentials (DNS records are public), making it the fastest to ship and test. Step 3 (Blacklist Scanning) is a close second because blacklisting is the most time-sensitive issue to detect.

---

## The 6-Step Architecture Map

```
SCHEDULE: Cron jobs — full pipeline twice daily (8am/8pm), blacklist scan every 4h
    |
    v
INPUT: Node.js dns module (SPF, DKIM, DMARC, CNAME records)
       Google Postmaster API (domain reputation, spam rate, auth rates)
       DNSBL DNS lookups (blacklist status across 30+ providers)
       Supabase (historical snapshots for trend analysis)
    |
    v
PROCESS: 
    Step 1 — DNS validation: resolve TXT/CNAME records, validate against expected values
    Step 2 — Postmaster check: query reputation, spam rate, auth pass rates
    Step 3 — Blacklist scan: reverse-DNS lookups against DNSBL providers
    Step 4 — Trend analysis: compare current data against 7-day and 30-day history
    Step 5 — Composite score: weighted formula combining all factors (0-100)
    |
    v
OUTPUT: Supabase (update domain status, pause mailboxes if critical)
        Telegram (alerts, daily summary, weekly trends)
        CLI (operator dashboard with health scores)
    |
    v
STATE: Supabase tables:
    - domains (domain, status, health_score, last_checked)
    - dns_checks (domain_id, spf, dkim, dmarc, cname_fingerprints, checked_at)
    - postmaster_checks (domain_id, reputation, spam_rate, auth_rates, checked_at)
    - blacklist_checks (domain_id, listed, listings, checked_at)
    - daily_health_snapshots (domain_id, date, score, reputation, spam_rate, blacklisted)
    - health_events (domain_id, event_type, severity, details, created_at)
    |
    v
NOTIFY: Telegram bot
    - Critical: "SPF record MISSING on cenra.io — fix DNS immediately"
    - Blacklist: "cenra.io listed on Spamhaus — delist at [URL]"
    - Daily 8am: health scores for all domains with trend arrows
    - Weekly: trend report with improving/stable/declining classification
```

---

## How This Differs from the Warmup System

The warmup manager's Step 1 does a basic domain health check as PART of the warmup flow. This standalone Domain Health Monitor is a more comprehensive, dedicated system:

| Capability | Warmup Manager Step 1 | Domain Health Monitor |
|---|---|---|
| Postmaster reputation check | Yes | Yes |
| DNS record validation (SPF/DKIM/DMARC) | No (trusts initial setup) | Yes (continuous validation) |
| Blacklist monitoring | No | Yes (30+ DNSBL providers) |
| CNAME fingerprint detection | No | Yes |
| Trend analysis (7-day, 30-day) | No | Yes |
| Composite health score (0-100) | No (simple pass/fail) | Yes (weighted multi-factor) |
| Delisting instructions | No | Yes |
| Historical data tracking | Basic (last check only) | Full (daily snapshots, 30-day history) |
| DNS change detection | No | Yes (alerts on unexpected changes) |
| Independent scheduling | Tied to warmup check cycle | Runs on its own schedule |

The two systems are complementary: the warmup manager uses domain health as one input to warmup decisions. The Domain Health Monitor is the single source of truth for domain health across the entire cold email pipeline.

---

## Proof This Framework Works (Again)

We took another gap (domain health monitoring) — a process that was either done manually, done inconsistently, or not done at all — and ran it through the same wizard questionnaire. The output:

1. A complete process breakdown (5 steps with inputs, outputs, decisions, error cases)
2. DNS validation using free, built-in tools (no paid API required)
3. Blacklist scanning using DNS-based lookups (free, no MXToolbox subscription needed)
4. A composite health scoring formula that replaces human "gut feel" with deterministic math
5. Trend analysis that catches gradual degradation before it becomes catastrophic
6. A full operations plan (state tracking, notifications, scheduling)
7. Success criteria with measurable targets
8. A 6-step architecture map ready to be turned into a CLAUDE.md build file

The framework extracted the same pattern. Different process, same structure, same quality of output.

**Next step:** The CLAUDE-MD-DOMAIN-HEALTH.md build file turns this architecture into code specifications.
