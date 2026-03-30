# Cold Email Deliverability Playbook 2026
## Source: LeadGenJay — Post-Google Apocalypse Recovery Guide

---

# PART 1: STEP-BY-STEP SETUP PLAYBOOK

## Phase 1: DNS Records (Perfect, Not Just Good)

1. **SPF Record** — Configure correctly for your domain
2. **DKIM Record** — Configure correctly for your domain
3. **DMARC Record** — Configure correctly for your domain
4. **REMOVE your custom tracking domain (CNAME record)** — This is NEW. If you have a CNAME pointing to Instantly/SmartLead, delete it. It's a fingerprint that flags you as a cold emailer.
   - If you MUST track (open rates or link clicks), a custom CNAME pointing to Instantly is still better than Instantly's default tracking domain
   - But best practice: remove it entirely

## Phase 2: Instantly Campaign Settings

1. **Settings > Block List > AI Block List Triggers**
   - Add trigger words: `stop`, `bad fit`, `unsubscribe`, `remove`, `opt out`
   - This auto-unsubscribes hostile replies so you don't accidentally keep emailing them

2. **Settings > Advanced Deliverability**
   - "Unlikely to reply" → Set to **Send Last** or **Skip**
   - "Hostile prospects" → **Skip** (absolutely skip)

3. **Campaign > Options > Deliverability Optimization**
   - Check: "Send email as text only" (or at minimum "Send FIRST email as text only")
   - This lets you include links (YouTube, Loom) in follow-ups but keeps first touch clean

4. **Campaign > Advanced Options** (scroll down)
   - "Allow risky emails" → **Leave UNCHECKED** (disabled = good)
   - "Bounce protect" → **Leave ENABLED** (do not disable)
   - These use Instantly's collective data to avoid spam traps and bounces

## Phase 3: Volume Control

1. **Max 20 emails per day per mailbox** — Hard ceiling
2. **Ideal: 10-15 per day per mailbox** — Jay's personal mailboxes survived the ban at this volume
3. **Scale by adding MORE mailboxes**, not by cranking volume on existing ones
4. **Why this works:** Warm-up emails are "good" emails. If you only send 10-15 cold emails on top of warm-up, your spam-to-good ratio stays healthy

## Phase 4: Email Copy Rules

1. **Plain text only** for first emails — No HTML, no tracking codes, no images
2. **No unsubscribe links** — Yes, Google says you need them. Ignore that. Unsubscribe links HURT deliverability. Use AI block list triggers instead (Phase 2 step 1)
3. **No open tracking**
4. **No click tracking**
5. **Heavy SpinTax** — Go overboard. Every phrase should have 5-7+ variations minimum
6. **AI-generated unique copy per prospect** — The next level beyond SpinTax (see Encyclopedia section below)

## Phase 5: Infrastructure Setup (Current Best Practice)

**Recommended mix:**
- **Primary: Google Reseller Mailboxes** — Best deliverability right now, ~half the cost of SMTP
- **Secondary: SMTP (Mission Inbox)** — Futureproofing. Can't be shut down by Google/Microsoft
- **Tertiary: Microsoft** — $30 for 49 mailboxes (5 emails/day each), uses a workaround

**Where to get them:**
- LeadGenJay's Inbox Insiders service: `leadgenjay.com/inbox` or `inbox.leadgenjay.com`
- Mission Inbox (SMTP) — available through Inbox Insiders at near-cost pricing
- Google Reseller — available through Inbox Insiders (official paid Google accounts, not legacy panels)

## Phase 6: Blacklist Monitoring

1. Go to **MXToolbox.com > Blacklist Check**
2. Enter your domain
3. It runs against all major blacklist providers
4. If you're on any, follow removal process (Jay has a separate video on this)
5. Check regularly if you're having deliverability issues

## Phase 7: Inbox Placement Testing

1. Test the SAME email with and without specific phrases
2. Swap one variable at a time (e.g., business address vs no address)
3. Identify which exact phrase is triggering spam
4. Jay is building a tool for this — join his free School community for early access

---

# PART 2: ENCYCLOPEDIA — DEEP DIVES

## The Google Apocalypse (November 2025)

**What happened:** Google banned thousands of Google Workspace mailboxes overnight. Legacy panels (grandfathered bulk Google Suite accounts) that had been running perfectly for years were wiped out. Jay personally lost over $250K. Thousands of his clients' mailboxes were gone.

**The second wave:** Weeks after the bans, Google changed their spam filter algorithms. Campaigns that had 100% inbox rates for 2+ years dropped below 50% overnight. This hit everyone — not just small operators.

**The recovery timeline:** ~3 months of testing by all major cold email operators (Jay, Zapmail, Instantly, and others in private mastermind groups) to find what works again.

**Current status (March 2026):** Cold email is back to normal. Jay's stats from last 7 days:
- Google to Google: **94% inbox**
- Google to Microsoft: **99% inbox**
- Google to Other: **94% inbox**

## Fingerprints — The Core Concept

**What are fingerprints?** Every signal attached to your email that Google/Microsoft can use to identify you as a cold emailer. The game is now about ELIMINATING fingerprints.

**Known fingerprints:**
| Fingerprint | Risk Level | Solution |
|---|---|---|
| CNAME tracking domain pointing to Instantly/SmartLead | HIGH | Remove it entirely |
| OAuth code (connecting to Instantly) | MEDIUM | No good workaround yet; Email Bison uses custom servers |
| Naming conventions (J.Feldman, Jay Feldman, Jay Feld) | MEDIUM | Vary naming patterns |
| Same headshot across accounts | MEDIUM | Vary or omit photos |
| Business address in signature | HIGH (new) | Remove, or use AI-generated local addresses |
| Specific phrases used by thousands of cold emailers | HIGH (new) | AI-unique copy per prospect |
| High volume from single mailbox | HIGH | Keep under 20/day, ideally 10-15 |
| Default tracking domains | HIGH | Disable all tracking |
| IP address | MEDIUM | Rotating residential IPs (advanced) |

## OAuth (OOTH) Problem

When you connect Gmail to Instantly via OAuth, everyone using Instantly shares similar OAuth signatures. Google could theoretically use this to flag cold emailers. Same OAuth method is used for legitimate services (like connecting Gmail to N8N), so it's not a smoking gun yet — but it's a signal.

**Email Bison's solution:** Instead of logging into `instantly.ai`, you log into a custom server (e.g., `send.leadgenjay.com`). Your DNS records and OAuth point to YOUR server, not a known cold email platform. Invite-only, used for high-ticket clients.

## Spam Traps Explained

Blacklist providers (checked via MXToolbox) plant fake email addresses ("landmines") across the internet. The only way to find and email these addresses is through scraped/purchased lists — i.e., cold email. If you hit one, you get blacklisted. Instantly's bounce protection and spam trap avoidance uses collective data to filter these out before you send.

## SpinTax vs AI-Generated Copy

**SpinTax (still required, minimum bar):**
```
{Hi|Hey|Hello} {first_name}, {I noticed|I saw|I came across} {your company|{company_name}}...
```
- Rotates through hard-coded phrase variations
- Limitation: Still a finite set (e.g., 7 variations). If 4 get blacklisted, you're down to 3.

**AI-Generated Copy (the new standard):**
- Every email is 100% unique — Google can't pattern-match a phrase that only exists once
- You don't need to rewrite the ENTIRE email — just the phrases you suspect could get flagged
- Example: Replace your static business address with an AI-generated address in the prospect's city → instant rapport + no repeating phrase

**How to do AI copy at scale:**
1. **Clay** — AI personalization/enrichment platform. Costs a few hundred/month. Easy to set up.
2. **N8N** — Free, open-source automation. Jay has templates for this. Build automations that generate unique copy per prospect.

## Infrastructure Types Compared

| Type | Cost | Deliverability | Futureproof | Risk |
|---|---|---|---|---|
| **Google Reseller** | ~$6-8/mo per mailbox | BEST right now | MEDIUM — Google can ban again | Official paid accounts, much safer than legacy |
| **Google Legacy Panels** | One-time purchase ($thousands) | Good | LOW — could get banned in next wave | No more monthly fees but high risk |
| **Mission Inbox (SMTP)** | Higher (~2x Google) | Very good | HIGH — independent of Google/Microsoft | Clean IP addresses, can't be shut down by big providers |
| **Microsoft** | $30/49 mailboxes | Good | MEDIUM — uses a workaround/loophole | 5 emails/day per mailbox limit |
| **Email Bison** | Premium/invite-only | Excellent | HIGH — custom servers, clean warm-up pools | Not publicly available |

## Warm-Up Pool Quality

**Why it matters:** Your mailboxes "warm up" by exchanging emails with other mailboxes in a pool. If the pool has bad/spammy mailboxes, your reputation gets dragged down.

**Platform comparison:**
- **Instantly** — Good. Detects bad mailboxes, kicks them out, pauses them
- **Email Bison** — Excellent. Only lets proven good mailboxes in
- **Reach Inbox** — Improved recently, now does better at keeping pool clean
- **Newer/smaller platforms** — HIGH RISK. Bad warm-up pools will destroy your infrastructure faster than anything else

## Mailchimp/ActiveCampaign Analogy for SMTP

SMTP providers like Mission Inbox work like Mailchimp in terms of IP reputation. Mailchimp has great deliverability because:
1. They maintain clean IP addresses
2. Email providers trust those IPs
3. They kick off anyone who gets spam complaints

Mission Inbox does the same thing — they're responsible for keeping IPs clean, which is why they cost more but offer long-term stability.

---

# PART 3: THEN vs NOW

| Factor | Before Nov 2025 | After Nov 2025 (Now) |
|---|---|---|
| **Primary infrastructure** | Google Legacy Panels (bulk, no monthly cost) | Google Reseller (paid monthly, official) |
| **Tracking domains** | Custom CNAME to Instantly = best practice | NO tracking domains. Remove CNAME entirely |
| **Open/click tracking** | Already declining, some still used it | Completely off. No exceptions |
| **Unsubscribe links** | Debated, some used them | DO NOT use. Use AI block list triggers instead |
| **Volume per mailbox** | 30-50/day common | MAX 20/day, ideal 10-15/day |
| **Spam phrase detection** | Obvious spam words flagged | ENTIRE PHRASES flagged, even innocent ones (business address, company name) |
| **SpinTax** | Important | Non-negotiable minimum. AI-unique copy is the new gold standard |
| **Infrastructure diversification** | Mostly Google | Google primary + SMTP + Microsoft mix |
| **Microsoft deliverability** | Terrible in 2024, nobody could inbox | Fixed. Now 99% inbox rate |
| **Google deliverability** | 100% for years | Crashed to <50%, now recovered to 94%+ with new practices |
| **Warm-up pools** | Less scrutinized | Critical. Bad pool = dead mailboxes fast |
| **Fingerprint awareness** | Low priority | THE central concept. Every decision = "does this leave a fingerprint?" |

---

# PART 4: DO'S AND DON'TS

## DO
- Keep volume under 20/day per mailbox (10-15 ideal)
- Scale with MORE mailboxes, not more volume
- Use heavy SpinTax on everything
- Use AI to generate unique phrases per prospect
- Diversify infrastructure (Google + SMTP + Microsoft)
- Use Instantly's hostile prospect filtering
- Set up AI block list triggers for angry replies
- Send plain text only (especially first email)
- Monitor blacklists via MXToolbox
- Run inbox placement tests with copy variations
- Use Google Reseller mailboxes (official, paid)
- Think about EVERY element as a potential fingerprint

## DON'T
- Use tracking domains (remove your CNAME)
- Track opens or clicks
- Use unsubscribe links
- Send HTML in first emails
- Send more than 20 emails/day per mailbox
- Email someone who said stop/remove/unsubscribe
- Ignore Instantly's bounce protection (leave it enabled)
- Enable "risky emails" in Instantly
- Use cheap/new platforms with bad warm-up pools
- Use the same phrases thousands of other cold emailers use
- Put your business address in email signatures (it gets flagged)
- Assume any infrastructure is permanently safe

---

# PART 5: SOFTWARE & TOOLS BREAKDOWN

| Tool | Purpose | Cost | Notes |
|---|---|---|---|
| **Instantly** | Primary cold email sending platform | Paid plans | Best for 99% of users. Collective data for spam trap/bounce avoidance |
| **SmartLead** | Alternative sending platform | Paid plans | Similar to Instantly |
| **Email Bison** | Premium sending with custom servers | Invite-only | Eliminates OAuth fingerprint. Used for high-ticket clients |
| **Clay** | AI personalization/enrichment at scale | ~$hundreds/mo | Generate unique copy per prospect |
| **N8N** | Free automation platform | Free | Build AI copy generation workflows. Jay has templates |
| **MXToolbox** | Blacklist checker | Free | Check if your domain is on any blacklist |
| **Mission Inbox** | SMTP mailbox provider | Higher cost | Independent IPs, futureproof, can't be shut down by Google |
| **Reach Inbox** | Alternative sending platform | Paid | Improved warm-up pool quality recently |
| **Inbox Insiders (LeadGenJay)** | Mailbox infrastructure service | Varies | One-stop shop for Google Reseller, SMTP, Microsoft mailboxes |
| **Jay's Inbox Placement Tester** | Test which phrases inbox vs spam | Coming soon | Join his School community for early access |
| **Jay's AI Automation Insiders** | School community for N8N/Claude Code automations | Free tier available | Templates for cold email AI personalization |

---

# PART 6: FUTURE-PROOFING — BROWSER AUTOMATION (ADVANCED)

**The nuclear option Jay is building:**

**Concept:** Instead of sending through Instantly (which uses OAuth = fingerprint), load Gmail accounts into actual browsers and send emails through browser automation — exactly like a human would.

**Why it works:** When Jay tests the same mailbox sending the same copy through Instantly (OAuth) vs the actual Gmail web app, the Gmail app version hits inbox EVERY TIME. The native Gmail infrastructure has zero cold-email fingerprints.

**Challenges:**
- Hard to automate at scale
- Hard to offer as a service (can't have 1000 clients doing browser automation)
- IP address tracking is still a fingerprint (solution: rotating residential IPs)

**Status:** Jay is building this for himself. Not publicly available yet.

**Why this matters for your SaaS plans:** If you're building cold email tools, browser-automated sending that eliminates OAuth fingerprints is the frontier. This is where the market is heading if providers keep cracking down.

---

# PART 7: KEY QUOTES & INSIGHTS

- "The name of the game isn't to email as many people as possible. It's to get the HIGHEST POSSIBLE ENGAGEMENT RATE."
- Google and Microsoft's goal is user experience, not helping cold emailers. Their advice (like "use unsubscribe links") serves THEIR interests, not yours.
- Every pattern repeats: Microsoft cracked down in 2024 (now fixed, 99% inbox). Google cracked down Nov 2025 (now fixed, 94% inbox). The next crackdown WILL come.
- The entire industry runs on this cycle: Provider changes → panic → testing → solution → normal → repeat
- Legacy Google panels: Jay still has thousands of mailboxes on these. Current ones seem safe (no new ban waves since November), but risk remains. Available for purchase through his community.

---

# PART 8: ACTION ITEMS FOR YOUR SITUATION

Since you're building cold email SaaS tools and planning to enter this market:

1. **The infrastructure layer is a service business** — LeadGenJay's Inbox Insiders model (reselling Google Reseller + SMTP + Microsoft at near-cost) is proven
2. **AI copy generation is the biggest automation opportunity** — Clay charges hundreds/month; a tool that does this cheaper or better has a market
3. **Inbox placement testing tool** — Jay is building one but it's not live yet. First-mover opportunity
4. **Browser-automated sending** — The frontier. Eliminates the biggest remaining fingerprint (OAuth). Extremely hard to build at scale, which means high barrier to entry = high value
5. **The warm-up pool problem** — Any sending platform you build needs clean pool management or it's DOA
