# TOS Compliance Analysis: What You Can and Can't Sell

> **Last Updated:** April 12, 2026
> **Sources:** Anthropic Terms of Service, Claude Code Legal & Compliance docs, Agent SDK docs, OpenClaw enforcement actions
> **Status:** ACTIONABLE — clear rules now exist

---

## The Two Paths: What OpenClaw Did vs What the SDK Does

**This is the critical distinction.** OpenClaw and AutoForge are NOT in the same category.

### What OpenClaw Did (BANNED)

OpenClaw **"reverse-engineered or intercepted the communication between a browser session and Claude.ai's backend, then re-exposed that connection as something your own tools could call."**

> Source: [MindStudio analysis](https://www.mindstudio.ai/blog/anthropic-openclaw-ban-third-party-harnesses-claude-subscriptions)

It exploited session-based authentication — browser fingerprints, cookies, behavioral signals — to pretend to BE Claude.ai. It spoofed the headers. It routed subscription tokens through unauthorized third-party interfaces.

Anthropic engineer Thariq Shihipar:
> "Third-party harnesses using Claude subscriptions create problems for users and are prohibited by our Terms of Service. **They generate unusual traffic patterns without any of the usual telemetry that the Claude Code harness provides.**"
> — Source: [The Register, Feb 2026](https://www.theregister.com/2026/02/20/anthropic_clarifies_ban_third_party_claude_access/)

### What the Agent SDK Does (ALLOWED — Anthropic Built It For This)

The Agent SDK is Anthropic's official product for building custom applications. From their own docs:

> "Build AI agents that autonomously read files, run commands, search the web, edit code, and more. The Agent SDK gives you the same tools, agent loop, and context management that power Claude Code, **programmable in Python and TypeScript.**"
> — Source: [Agent SDK Overview](https://code.claude.com/docs/en/agent-sdk/overview)

Authentication is via API keys:
```bash
export ANTHROPIC_API_KEY=your-api-key
```

The SDK explicitly supports building products for customers:
> "Use of the Claude Agent SDK is governed by Anthropic's Commercial Terms of Service, **including when you use it to power products and services that you make available to your own customers and end users.**"
> — Source: [Agent SDK Overview](https://code.claude.com/docs/en/agent-sdk/overview), License section

The SDK even has a comparison table showing it's DESIGNED for custom apps:

| Use case | Best choice |
|----------|------------|
| Interactive development | CLI |
| CI/CD pipelines | SDK |
| **Custom applications** | **SDK** |
| Production automation | SDK |

### The Auth Rule (Why The Distinction Matters)

> "**Unless previously approved, Anthropic does not allow third party developers to offer claude.ai login or rate limits for their products, including agents built on the Claude Agent SDK. Please use the API key authentication methods described in this document instead.**"
> — Source: [Agent SDK Overview](https://code.claude.com/docs/en/agent-sdk/overview), Step 2 setup note

This means:
- **Using API keys to build a product** → ALLOWED, encouraged, designed for this
- **Using subscription OAuth in a product** → NOT ALLOWED
- **Spoofing browser sessions** → ABSOLUTELY NOT ALLOWED (what OpenClaw did)

---

## The OpenClaw Crackdown (April 2026)

### What Happened

On April 4, 2026, Anthropic blocked third-party tools from using Claude subscription OAuth tokens. Affected:
- **OpenClaw** — reverse-engineered Claude.ai browser sessions
- **NanoClaw** — similar approach
- **OpenCode** — removed Claude subscription support after "Anthropic legal requests"
- **Any tool** routing subscription OAuth on behalf of users

~135,000 OpenClaw instances were running. Users faced cost increases up to **50x** (from $200/mo subscription to $1,000-$5,000/mo API costs).

### Why It Happened

1. **Token arbitrage** — running $1,000-$5,000 of compute through a $200/mo subscription
2. **Header spoofing** — pretending to be official Claude.ai clients
3. **No telemetry** — generating traffic patterns without Claude Code's standard telemetry
4. **Capacity strain** — "Capacity is a resource we manage thoughtfully"

OpenClaw's creator Peter Steinberger joined OpenAI on Feb 14, 2026. Enforcement came within weeks. His account was temporarily suspended April 10 (reinstated hours later after going viral).

---

## AutoForge: WHY It's Different

AutoForge uses the Claude Agent SDK with API key authentication. This is fundamentally different from OpenClaw:

| Factor | OpenClaw | AutoForge |
|--------|----------|-----------|
| **Authentication** | Spoofed browser sessions/OAuth | API keys (official method) |
| **SDK** | None — reverse-engineered Claude.ai | Official Claude Agent SDK |
| **Telemetry** | "Unusual traffic patterns" | Standard SDK telemetry |
| **Anthropic's stance** | Banned, accounts suspended | SDK designed for this exact use case |
| **Commercial Terms** | Violated Consumer TOS | Covered under Commercial TOS |
| **Branding** | Impersonated Claude.ai | Own branding (AutoForge) |

### What AutoForge Does Right
1. Uses **API keys** — the authentication method Anthropic tells developers to use
2. Uses the **official SDK** — not a reverse-engineered hack
3. Provides its own **UI/branding** — doesn't pretend to be Claude Code
4. Each user provides **their own API key** — no credential routing
5. Adds value through the **dashboard layer** — same tools, better interface

### The Branding Rules (From SDK Docs)

**Allowed:**
- "Claude Agent" (for dropdown menus)
- "Claude" (within a menu already labeled "Agents")
- "{YourAgentName} Powered by Claude" → "AutoForge Powered by Claude"

**Not permitted:**
- "Claude Code" or "Claude Code Agent"
- Claude Code-branded ASCII art or visuals that mimic Claude Code

> Source: [Agent SDK Overview](https://code.claude.com/docs/en/agent-sdk/overview), Branding section

AutoForge has its own branding. No issue here.

---

## The Rules (As Of April 2026)

### Authentication: The Core Distinction

From [Claude Code Legal & Compliance](https://code.claude.com/docs/en/legal-and-compliance):

| Auth Method | Who It's For | Allowed Use |
|------------|-------------|-------------|
| **OAuth tokens** | Subscribers (Free/Pro/Max/Team/Enterprise) | ONLY for native Anthropic apps: Claude.ai, Claude Code, Claude Desktop, Claude Cowork |
| **API keys** | Developers building products/services | Third-party tools, Agent SDK apps, **commercial products for your own customers** |

### What's Allowed on Subscriptions (OAuth)

- Claude.ai (web interface)
- Claude Code (official CLI)
- Claude Desktop (desktop client)
- Claude Cowork (team collaboration)
- Skills within Claude Code (just markdown files)
- Personal/ordinary Agent SDK usage

### What Requires API Keys

- Products you build for others (like AutoForge)
- Agent SDK in commercial products
- Any tool that serves multiple users
- Custom dashboards and UIs

---

## Business Models: Compliance Status

### Model 1: Selling Skills/Frameworks (SAFE — No Auth Involved)

Skills are markdown files. They don't route API calls, act as intermediary, or access Claude in any non-standard way. Customer installs them in their own Claude Code using their own subscription or API key.

**Pricing:** $200-$500 per skill, $750-$1,000 for packs, $2,000-$3,000 for orchestrated systems.

### Model 2: Setup & Training Service (SAFE — Customer's Own Auth)

Configuring a client's own Claude Code instance. You're working on THEIR computer with THEIR subscription. Standard consulting work.

**Pricing:** $500-$1,000 one-time, $200-$500/mo ongoing.

### Model 3: Affiliate Marketing (SAFE — No TOS Implications)

Referring people to Caleb's group (Agentic Academy) for 40% commission ($30/mo recurring). Standard affiliate marketing.

### Model 4: Dashboard/Product Built on Agent SDK (SAFE — With API Keys)

This is AutoForge's category. The Agent SDK is designed for this:

> "Use of the Claude Agent SDK is governed by Anthropic's Commercial Terms of Service, including when you use it to power products and services that you make available to your own customers and end users."

Requirements:
- Must use API key authentication (not subscription OAuth)
- Must not pretend to be Claude Code (own branding)
- Users bring their own API keys or you use your own (paid per token)

**Cost note:** API key usage costs more than subscription. But this is the legitimate path and Anthropic explicitly supports it.

### Model 5: "Free Dashboard + Paid Internals" (SAFE)

Give people the dashboard (or just Claude Code itself), sell the skills/frameworks that make it powerful. Safest model because you're selling knowledge, not compute.

---

## Decision Matrix

| Business Activity | Auth Method | TOS Status | Notes |
|------------------|------------|------------|-------|
| Sell skill packs (markdown files) | None needed | **SAFE** | Just text files |
| Setup & training service | Customer's own | **SAFE** | Consulting work |
| Affiliate referrals | N/A | **SAFE** | Standard affiliate |
| YouTube content + bonuses | N/A | **SAFE** | Content business |
| Cold email service | Your own tools | **SAFE** | Service business |
| AutoForge (SDK + API keys) | API keys | **SAFE** | Explicitly supported by SDK docs |
| Dashboard with API keys | API keys | **SAFE** | SDK designed for this |
| Dashboard with subscription OAuth | OAuth tokens | **BANNED** | What OpenClaw did |
| Spoofing browser sessions | None/stolen | **BANNED** | Illegal, accounts suspended |

---

## Simon's Dashboard — Still Unknown

Simon's Agentic OS dashboard — we don't know how it authenticates yet. When you get access, check:

1. Does it ask for an API key? → **Safe** (same as AutoForge)
2. Does it use your Claude subscription login? → **Risky** (same category as OpenClaw)
3. Does it use its own API key on your behalf? → **Fine for Simon** but he's paying per-token

This determines whether his dashboard is sustainable and whether the affiliate strategy holds up long-term.

---

## Key Quotes (With Sources)

> "Unless previously approved, Anthropic does not allow third party developers to offer claude.ai login or rate limits for their products, including agents built on the Claude Agent SDK. Please use the API key authentication methods described in this document instead."
> — [Agent SDK Overview](https://code.claude.com/docs/en/agent-sdk/overview)

> "Use of the Claude Agent SDK is governed by Anthropic's Commercial Terms of Service, including when you use it to power products and services that you make available to your own customers and end users."
> — [Agent SDK Overview](https://code.claude.com/docs/en/agent-sdk/overview)

> "Third-party harnesses using Claude subscriptions create problems for users and are prohibited by our Terms of Service. They generate unusual traffic patterns without any of the usual telemetry that the Claude Code harness provides."
> — Thariq Shihipar, Anthropic engineer, [The Register](https://www.theregister.com/2026/02/20/anthropic_clarifies_ban_third_party_claude_access/)

> "Subscriptions weren't built for the usage patterns of these third-party tools. Capacity is a resource we manage thoughtfully."
> — Anthropic Head of Claude Code, April 2026

> "[OpenClaw] reverse-engineered or intercepted the communication between a browser session and Claude.ai's backend, then re-exposed that connection as something your own tools could call"
> — [MindStudio](https://www.mindstudio.ai/blog/anthropic-openclaw-ban-third-party-harnesses-claude-subscriptions)

---

## Action Items

- [ ] Check Simon's dashboard auth method when you get access (API key vs OAuth)
- [ ] If OAuth → his product is at risk long-term, factor into affiliate strategy
- [ ] If API key → confirm total cost to users ($77/mo group + API usage)
- [ ] AutoForge is SAFE — uses SDK + API keys, which is the explicitly supported path
- [ ] Build the "sell skills, not access" business model as primary revenue stream
- [ ] Consider "AutoForge Powered by Claude" branding if going public
