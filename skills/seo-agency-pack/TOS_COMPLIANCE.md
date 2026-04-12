# TOS Compliance Analysis: What You Can and Can't Sell

> **Last Updated:** April 12, 2026
> **Sources:** Anthropic Terms of Service, Claude Code Legal & Compliance docs, OpenClaw enforcement actions
> **Status:** ACTIONABLE — clear rules now exist

---

## The OpenClaw Crackdown (April 2026)

### What Happened

On April 4, 2026, Anthropic blocked all third-party tools from using Claude subscription OAuth tokens. This affected:
- **OpenClaw** — AI agent framework (WhatsApp, Telegram, Slack, Discord, Teams)
- **NanoClaw** — Similar third-party agent tool
- **OpenCode** — Community-developed coding assistant
- **Any non-official tool** using subscription OAuth authentication

~135,000 OpenClaw instances were running at the time. Users faced cost increases up to **50x** their previous monthly bill.

### Why It Happened

Anthropic's stated reason: "Subscriptions weren't built for the usage patterns of these third-party tools." The real issue was **token arbitrage** — people running $1,000-$5,000 worth of compute through a $200/month subscription via third-party wrappers.

OpenClaw's creator Peter Steinberger joined OpenAI on Feb 14, 2026. Anthropic's restrictions came within weeks. His account was temporarily suspended on April 10 for "suspicious activity" (reinstated within hours after it went viral).

---

## The Rules (As Of April 2026)

### Authentication: The Core Distinction

From [Claude Code Legal & Compliance](https://code.claude.com/docs/en/legal-and-compliance):

| Auth Method | Who It's For | Allowed Use |
|------------|-------------|-------------|
| **OAuth tokens** | Subscribers (Free/Pro/Max/Team/Enterprise) | ONLY for native Anthropic apps: Claude.ai, Claude Code, Claude Desktop, Claude Cowork |
| **API keys** | Developers building products/services | Third-party tools, Agent SDK apps, commercial products |

**The hard rule:** "Anthropic does not permit third-party developers to offer Claude.ai login or to route requests through Free, Pro, or Max plan credentials on behalf of their users."

### What's Still Allowed on Subscriptions

- Claude.ai (web interface)
- Claude Code (official CLI)
- Claude Desktop (desktop client)
- Claude Cowork (team collaboration)
- Skills within Claude Code (they're just markdown files Claude reads)
- Agent SDK usage with subscription auth for **personal/ordinary use**

### What Requires API Keys

- Any product or service you BUILD for others
- Agent SDK usage in commercial products
- Anything that routes requests through your credentials on behalf of users
- Any wrapper, dashboard, or tool that sits between users and Claude

---

## What This Means for Our Business Models

### Model 1: Selling Skills/Frameworks (SAFE)

**What it is:** Selling markdown files (skill.md), reference docs, templates, brand context files.

**TOS Status: COMPLIANT**

Skills are just text files. They don't:
- Route API calls through anyone's credentials
- Act as a wrapper or intermediary
- Require any special authentication
- Access Claude in any non-standard way

The customer installs them in their own Claude Code instance, using their own subscription or API key. This is identical to selling a recipe book — you're selling knowledge and structure, not access.

**Pricing:** $200-$500 per skill, $750-$1,000 for contextualized packs, $2,000-$3,000 for full orchestrated systems.

### Model 2: Setup & Training Service (SAFE)

**What it is:** Configuring a client's own Claude Code instance — installing skills, building brand context files, training their team.

**TOS Status: COMPLIANT**

You're working on THEIR computer, with THEIR subscription. This is consulting/services work. No different from an IT consultant setting up someone's Microsoft Office.

**Pricing:** $500-$1,000 one-time setup, $200-$500/mo ongoing tuning.

### Model 3: Affiliate Marketing (SAFE)

**What it is:** Referring people to Caleb's group (Agentic Academy) for 40% commission ($30/mo recurring).

**TOS Status: COMPLIANT**

Standard affiliate marketing. No TOS implications — you're just referring people to a legitimate product. The group is Caleb's responsibility to keep compliant.

**Pricing:** $30/mo per signup, recurring.

### Model 4: Selling a Dashboard/Wrapper (RISKY → REQUIRES API KEYS)

**What it is:** Building and selling a UI that wraps Claude Code functionality.

**TOS Status: ONLY COMPLIANT WITH API KEY AUTH**

If you build a dashboard:
- It CANNOT use OAuth/subscription tokens on behalf of users
- Users MUST authenticate via their own API keys
- You CANNOT route requests through your own credentials
- You MUST use API key authentication, not subscription auth

**The cost problem:** API key usage costs ~7x more than subscription. A $200/mo subscription workload becomes $1,000-$1,400/mo on API keys. This fundamentally changes the economics of selling a wrapper product.

**The Caleb question:** If Caleb's dashboard uses subscription OAuth on behalf of users, it's in the same crosshairs as OpenClaw. If it uses API keys, it's compliant but expensive. This is THE question to answer when you get access tomorrow.

### Model 5: "Free Dashboard + Paid Internals" (MOSTLY SAFE)

**What it is:** Give away a basic dashboard (or just help them use Claude Code directly), sell the skills/frameworks/brand context that make it powerful.

**TOS Status: COMPLIANT IF...**
- The "free dashboard" is just Claude Code itself (not a wrapper)
- OR the dashboard uses API key auth (not subscription OAuth)
- The "paid internals" are just skill files, reference docs, templates

**This is the safest commercial model.** You're not building a wrapper. You're selling the knowledge layer that makes Claude Code actually useful for a specific business. The customer uses their own Claude Code installation.

---

## Decision Matrix

| Business Activity | Auth Needed | TOS Risk | Revenue Potential |
|------------------|-------------|----------|-------------------|
| Sell skill packs (markdown files) | None — customer's own | NONE | $200-$3,000 per sale |
| Setup & training service | Customer's own sub | NONE | $500-$1,000/client |
| Affiliate referrals | N/A | NONE | $30/mo recurring |
| YouTube content + bonuses | N/A | NONE | Ad revenue + affiliate |
| Cold email service | Your own tools | NONE | $500-$2,000/mo |
| Build a dashboard (API keys) | API keys only | LOW | High but expensive |
| Build a dashboard (subscription) | OAuth tokens | HIGH — BANNED | N/A — don't do this |
| Route requests for users | Your credentials | HIGH — BANNED | N/A — don't do this |

---

## The Safe Business Stack

```
Revenue Layer 1: Content (YouTube + 8 platforms)
  → Drives affiliate signups ($30/mo recurring)
  → Drives skill pack sales ($200-$3,000)
  → Builds authority for service sales

Revenue Layer 2: Skill Packs (Digital Products)
  → SEO Agency Pack (10+ skills): $500-$1,000
  → Custom skill creation: $200-$500 each
  → Ongoing skill updates: $200-$500/mo

Revenue Layer 3: Services (Consulting)
  → Setup & configuration: $500-$1,000
  → Brand context building: included in setup
  → Team training: included or $500 add-on
  → Monthly optimization: $200-$500/mo

Revenue Layer 4: Cold Email (Lead Gen)
  → For yourself: drives all above
  → As a service for clients: $500-$2,000/mo
```

**What's NOT in the stack:** Wrapping Claude's API, routing subscription tokens, building a competing interface, reselling Claude access. Stay away from the access layer entirely. Sell knowledge, not compute.

---

## Key Quotes from Anthropic

> "Anthropic does not permit third-party developers to offer Claude.ai login or to route requests through Free, Pro, or Max plan credentials on behalf of their users."
> — Claude Code Legal & Compliance

> "Advertised usage limits for Pro and Max plans assume ordinary, individual usage of Claude Code and the Agent SDK."
> — Claude Code Legal & Compliance

> "Subscriptions weren't built for the usage patterns of these third-party tools."
> — Anthropic Head of Claude Code, April 2026

> "Anthropic reserves the right to take measures to enforce these restrictions and may do so without prior notice."
> — Claude Code Legal & Compliance

---

## AutoForge Implications

AutoForge (your project) uses Claude Agent SDK with a React UI. Key questions:

1. **How does it authenticate?** If it uses subscription OAuth on behalf of users → at risk. If it uses API keys → safe.
2. **Who are the users?** If it's just you using your own subscription → fine (ordinary personal use). If it's a product others log into → must use API keys.
3. **Does it route requests?** If it proxies Claude calls through your server → must use API keys, not subscription tokens.

**Safe path for AutoForge:** Use API key authentication. Let users bring their own API keys. The UI layer is fine — it's the auth method that matters.

---

## Action Items

- [ ] Check Caleb's dashboard auth method when you get access (OAuth vs API key)
- [ ] If OAuth → his product is at risk, adjust your affiliate strategy accordingly
- [ ] If API key → confirm total cost to users ($77/mo group + API usage)
- [ ] Verify AutoForge auth method — ensure API key path, not subscription OAuth
- [ ] Build the "sell skills, not access" business model as primary revenue stream
- [ ] Position yourself as a Claude Code consultant, not a Claude Code reseller
