# Tool Bank Business Strategy

## The Core Concept

"Tool Bank" — a bank of tools that also makes bank selling tools.

A multi-tool SaaS platform where businesses subscribe to access a library of AI-powered tools. Not selling AI access — selling purpose-built tools that happen to use AI under the hood.

---

## Phase 1: Consulting (Current / Near-Term)

**Model:** Install custom tools directly on businesses' own machines, using their own Claude subscriptions.

**How it works:**
- Take existing tool repos (like AutoForge pattern)
- ~50% get customized for the client, ~50% taken as-is
- Install on their machine, tap into their subscription (same as AutoForge on your own machine)
- Tool doesn't do anything beyond what Claude Code CLI already enables
- You're selling software + installation expertise, not AI access

**TOS status:** Clean. Their machine, their subscription, their credentials. You're a consultant/integrator.

**Purpose of this phase:**
- Revenue to fund Phase 3
- Direct conversations with businesses to learn what tools they actually need
- Every custom tool built = new tool for the tool bank inventory
- Learn pricing tolerance, sales pitch, pain points
- Build relationships with early customers who become beta testers
- Full-blown market research while getting paid

**Scale:** Target a manageable number of businesses (not 50-100 simultaneous consulting relationships). Enough to learn, not so many it becomes the whole business.

---

## Phase 2: Tool Development & Inventory Building

**What happens here:**
- Each consulting engagement produces tools that go into the bank
- Refine and generalize tools so they work across industries/use cases
- Build the deterministic/DunkStack systems to reduce API costs per tool
- Develop the PRD maker for rapid tool creation
- Goal: 20-50 tools covering common business needs

**Key insight:** Once the tool-building process is systemized, each new tool is a variation on established patterns — different mixtures of the same ingredients.

---

## Phase 3: SaaS Platform ("The Warehouse")

**Architecture: One Platform, Many Tools (Multi-Tenant)**

```
Tool Bank Platform
├── Auth & Billing (ONE Stripe, one login)
├── Shared Database (PostgreSQL)
│   ├── Users / Organizations / Subscriptions
│   └── Tool-specific tables (each tool gets own tables)
├── Shared UI Shell (sidebar nav, settings, billing)
├── Tool 1: [Content Tool]
├── Tool 2: [Analysis Tool]
├── Tool 3: [Automation Tool]
├── ... Tool 20-50
└── AI Backend (API calls to Claude/etc.)
```

**Why one platform, not 50 separate apps:**
- One login, one billing system, one deploy pipeline
- One bug fix = fixed everywhere (vs. same bug x50)
- Customer gets one dashboard with all their tools
- Adding a new tool = adding a route + tables, not a whole new app
- "Apartment building" not "50 separate houses"

**Scaling limits (what actually matters):**

| Factor | Limit |
|--------|-------|
| Number of tools | 100+ is fine — just routes and components |
| Number of users | 10,000+ concurrent before real infra needed. 300 businesses = trivial |
| Database | One Postgres handles millions of rows. Tools get own tables, don't interfere |
| AI API costs | THE real scaling constraint. Not the platform. |

**Pricing model options:**
- Tiered: "Basic: 10 tools, Pro: all 30 tools, Enterprise: custom"
- Per-seat pricing for teams
- Heavy-use tools: offer dedicated install option at premium price
- Some tools are "micro" — 3-5 related functions bundled as one tool

---

## Phase 4: Scale & Feedback Loop

- Heavy ad promotion for the SaaS
- Stop doing custom consulting (except big enterprise deals)
- Continuous feedback loop: users request features/tools, you build them
- The tool-building system is refined enough that new tools ship fast

---

## Revenue Streams

1. **Consulting installs** (Phase 1) — per-engagement fees
2. **SaaS subscriptions** (Phase 3) — monthly recurring from tool bank access
3. **Enterprise custom installs** (ongoing) — big clients who want dedicated/customized versions
4. **Tool licensing** — if a company wants to "own" a specific tool for heavy internal use

---

## DunkStack Cost Advantage

The DunkStack system (deterministic prompt assembly, reduced tool usage) could dramatically lower API costs per tool operation. This directly improves SaaS margins since AI API calls are the #1 COGS.

Priority: Get DunkStack validated and working, then bake it into the tool-building template so every new tool benefits.

---

## Moat Analysis

**What has a moat:**
- Consumer apps solving specific problems (sugar scanner, niche mobile apps) — AI platforms won't build these niche tools anytime soon
- Deep domain expertise from consulting phase — knowing exactly what businesses need
- The tool-building system itself — the ability to ship new tools fast
- Customer relationships and feedback loops

**What doesn't have a moat:**
- Any individual tool (can be replicated)
- The AI capabilities themselves (Anthropic/OpenAI keep improving)

**The real moat:** Speed of tool creation + understanding of customer needs + the platform itself (network effects once businesses depend on it)

---

## TOS / Legal Considerations by Scenario

| Scenario | Status |
|----------|--------|
| Install on their machine, their subscription | Clean — consulting |
| Company with 50-100 employees using installed tool on company subscription | Clean — same as any internal tool built by/for the company |
| SaaS where you host and route AI calls | Need commercial API agreement with Anthropic — contact their sales team |
| Free open-source tool (like Leon's AutoForge) | Clean — no money changing hands, doesn't exceed CLI capabilities |
| Selling to thousands via website | SaaS territory — need proper commercial terms |

**Key principle:** The determining factor is whether the tool automates things that couldn't already be done through the CLI, AND whether you're reselling AI access vs. selling software.

**Action item:** Before launching Phase 3 SaaS, contact Anthropic's partnerships/sales team for a commercial API agreement. By that point you'll have traction and paying customers — they'll want to talk to you.

---

## What to Build vs. What to Hire Out

| You build (with AI tools) | Hire dev team for |
|---------------------------|-------------------|
| Individual tool logic & PRDs | Platform shell (auth, billing, multi-tenancy) |
| UI designs and flows | Database architecture & security |
| Testing with real customers | CI/CD, monitoring, infrastructure |
| Tool specs from consulting insights | Scaling, load balancing, job queues |

---

## Timeline Window

- Estimated 6-12 months before AI platforms might offer similar tool-building capabilities natively
- Consulting phase builds capital + knowledge during this window
- Consumer/niche apps have longer moats than enterprise tools
- Speed matters: get tools built, get customers paying, get platform launched

---

*Strategy developed through multiple conversations. This is the master reference document.*
