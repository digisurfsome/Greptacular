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

## Commercial API Agreements Explained

### What Is It?

Three ways to use Claude:
1. **Consumer subscription** ($20/month) — chatting in browser or Claude Code
2. **API (pay-per-use)** — programmatic access, pay per token
3. **Commercial/Enterprise agreement** — call Anthropic's sales team, negotiate a deal

Option 3 is what you need for Phase 3 (SaaS). You call Anthropic and say: "I'm building a SaaS with 300 businesses. My platform makes 50,000 API calls/month. I need volume pricing and commercial terms."

### What You Get
- **Lower per-token pricing** (volume discount — more you use, cheaper per call)
- **Higher rate limits** (more requests per minute than regular API key)
- **Legal agreement** explicitly permitting you to build products on their API and charge customers
- **Dedicated support** (actual humans who help when stuff breaks)
- Sometimes **priority access** to new models

### Why Anthropic Does This
You're a sales channel. Your 300 business customers generate API usage that Anthropic profits from. They'd rather give you a discount than lose you to OpenAI or Google.

### What OpenClaw Should Have Done
1. Go to Anthropic's sales team BEFORE launching
2. Say "we want to build X product using Claude"
3. Get a commercial agreement that explicitly permits this
4. Get volume pricing so margins work
5. Launch legally with Anthropic's blessing

The problem wasn't building a product using Claude. It was doing it without permission, violating terms, and arguably competing with Anthropic directly.

### The Cursor Case Study
- Started as VS Code fork wrapping AI models (GPT, Claude)
- Every AI feature = Cursor's servers making API calls to OpenAI/Anthropic
- Charged users $20/month; chunk went to paying API costs
- Margin = subscription price minus API costs per user
- Risk: heavy user makes $25 in API calls, pays $20 = you lose money
- Got big enough to negotiate volume discounts, then started training own models
- Now building their own AI = margins explode
- **Key: Cursor had commercial agreements from the start**

### When to Talk to Anthropic
- Not that big. Even $5K-10K/month in API usage, they'll talk to you
- They WANT companies building on their platform — it's growth
- Steps: anthropic.com → Sales/Enterprise → describe your product → get terms → sign → build

### How It Applies to Each Phase

| Phase | AI Billing | Agreement Needed? |
|-------|-----------|-------------------|
| Phase 1 (Consulting) | Client's subscription | No |
| Phase 3 (SaaS) | You pay API, bill customers | Yes — commercial agreement |
| Enterprise installs | Client's subscription | No |

---

## Phase 1 Installation Playbook

### The Complexity Spectrum

Installation complexity scales with company size and IT infrastructure:

**Tier 1: Solo / Small Team (1-10 people) — YOU CAN DO THIS**
- One person's laptop or a shared office machine
- No IT department, no corporate firewalls, no VPN restrictions
- Basically the same as your own AutoForge setup
- Install: Python, Node.js, clone repo, configure subscription, done
- **Complexity: Same as setting up your own machine**

**Tier 2: Small Business (10-50 people) — YOU CAN PROBABLY DO THIS**
- Might have a shared server or a cloud VM (AWS, Azure, etc.)
- Possibly a basic IT person but no locked-down policies
- Might need to set up on a server so multiple employees can access via browser
- Install: Same as Tier 1 but on a server, configure for network access
- **New variables:** firewall ports, SSL certs if they want HTTPS, user accounts
- **Complexity: Manageable with a checklist**

**Tier 3: Mid-Size Business (50-500 people) — YOU WANT A DEV**
- Has an IT department with policies
- Corporate VPN, firewalls, security requirements
- Might require SSO (Single Sign-On) integration
- Might need to run in Docker containers or Kubernetes
- Data compliance requirements (where data is stored, who can access it)
- **New variables:** IT approval processes, security audits, compliance docs
- **Complexity: You need someone who speaks their IT team's language**

**Tier 4: Enterprise (500+ people) — DEFINITELY HIRE A DEV**
- Full IT governance, change management boards
- Everything runs in their cloud (AWS/Azure/GCP) behind 5 layers of security
- Needs to integrate with their identity provider (Okta, Azure AD)
- Data residency requirements, SOC 2 compliance questions
- **Complexity: This is a project, not an install**

### Your Strategy: Target Tier 1-2, Build Repeatable Process

**The installation kit (what you build once, use every time):**

```
install-kit/
├── INSTALL_GUIDE.md          — Step-by-step for each OS (Windows/Mac/Linux)
├── preflight-check.py        — Script that checks: Python version, Node version,
│                                disk space, network access, subscription status
├── install.py                — Automated installer: clones repo, sets up venv,
│                                installs deps, configures subscription auth
├── verify.py                 — Post-install verification: runs health checks,
│                                confirms AI calls work, confirms UI loads
├── troubleshoot.py           — Common problems + auto-fixes
└── SUPPORT_RUNBOOK.md        — For when something goes wrong (you reference this)
```

**The repeatable process (what you do every time):**

1. **Pre-call (15 min):** Ask client: What OS? How many users? Do you have a Claude subscription? Any IT restrictions?
2. **Preflight (5 min):** Run `preflight-check.py` on their machine — tells you if everything's ready
3. **Install (15-30 min):** Run `install.py` — automated, does everything
4. **Verify (5 min):** Run `verify.py` — confirms it works
5. **Walkthrough (15 min):** Show them how to use it
6. **Total: ~1 hour per install**

**Practice plan:**
- Install #1-3: Do them yourself, note every issue, fix the scripts
- Install #4-5: Should be smooth — scripts handle 90% of it
- Install #6+: It's a repeatable checklist, takes an hour, you're confident

### When You Need a Dev (and What Kind)

**Signs you need help:**
- Client says "we need it on our AWS/Azure"
- Client says "it needs to work with our SSO/Okta"
- Client's IT sends you a security questionnaire
- Client wants it in a Docker container
- More than ~20 people need to access it simultaneously

**What kind of dev:**
- NOT a full-stack app developer (overkill)
- A **DevOps / infrastructure person** — someone who knows servers, Docker, networking
- They set up the environment, you install the tool
- Freelance, on-call basis — maybe 5-10 hours per complex install
- Over time they build you templates (Docker configs, cloud deploy scripts) that make future installs faster

### Pricing by Tier

| Tier | Your effort | Suggested pricing |
|------|------------|-------------------|
| Tier 1 (solo/small) | 1-2 hours | $500-1,000 flat |
| Tier 2 (small biz) | 2-4 hours | $1,500-3,000 flat |
| Tier 3 (mid-size) | You + dev, 1-2 days | $5,000-10,000 |
| Tier 4 (enterprise) | Dev-led, 1-2 weeks | $15,000-30,000+ |

Plus monthly support/maintenance fee: $200-500/month for Tier 1-2, more for Tier 3-4.

### The Install Kit as a Moat

The more installs you do, the better your scripts get. By install #10, you have:
- A script that handles 95% of setups automatically
- A troubleshooting guide that covers every weird edge case you've hit
- A preflight check that catches problems before you start
- A verified process that takes an hour, not a day

That IS the product for Phase 1. The tool is what they're buying, but the frictionless install is what makes them say yes.

---

## Automated Installation Tool (Claude Does the Install)

### The Reality

You're not a coder. You're never going to SSH into a machine and run commands yourself. Claude Code is doing the work. So the installation process itself needs to be a tool — a deterministic, repeatable skill that Claude executes with minimal human input.

### Why This Works

Think about what an install actually is:

```
FIXED (same every time, 90% of the work):
├── Check Python version, install if needed
├── Check Node.js version, install if needed
├── Clone the tool repo
├── Create virtual environment
├── Install Python dependencies
├── Install Node dependencies
├── Build the UI
├── Set up the database
├── Configure startup scripts
└── Run verification checks

VARIABLE (the only parts that change):
├── Which OS (Windows / Mac / Linux) — 3 options
├── Which tool to install — pick from your tool list
├── Subscription config — their Claude credentials
└── Custom settings — if they want anything tweaked
```

90% of it is deterministic — literally the same commands in the same order every time. The variable parts are just a few inputs up front.

### The Installation Skill Architecture

**Layer 1: The Intake Questionnaire (human-facing)**
You ask the client a few questions. Could be a form, a call, a chat:
- What OS are they on? (Windows / Mac / Linux)
- Which tool(s) do they want?
- How many people will use it?
- Do they have a Claude subscription already?
- Any IT restrictions? (VPN, firewall, etc.)

**Layer 2: The Installation Skill (Claude-facing)**
A Claude Code skill (`.claude/skills/` or `.claude/commands/`) that takes those answers as inputs and runs the entire install. The skill would look something like:

```
SKILL: install-tool-for-client

INPUTS:
- os_type: windows | mac | linux
- tool_name: [from tool catalog]
- install_path: where to put it
- subscription_type: claude_max | claude_pro | api_key
- multi_user: true | false

DETERMINISTIC STEPS:
1. Detect OS and set platform-specific commands
2. Check prerequisites (Python 3.11+, Node 20+)
   - If missing: provide exact install instructions for their OS
3. Clone tool repo to install_path
4. Create venv, install deps
5. Build UI if applicable
6. Configure subscription auth
   - If claude_max/pro: set up credential forwarding
   - If api_key: configure .env
7. If multi_user: configure for network access (host 0.0.0.0, set port)
8. Create startup script for their OS
9. Run verification suite:
   - Can it reach the AI? ✓/✗
   - Does the UI load? ✓/✗
   - Can it process a test request? ✓/✗
10. Generate install report (what was done, how to start it, troubleshooting)

DETERMINISTIC WALLS (things that can't deviate):
- Python version must be 3.11+
- Node version must be 20+
- Subscription auth must follow the pattern in registry.py
- Security settings must match client.py defaults
- Verification must pass before declaring success
```

**Layer 3: Deterministic Walls (error prevention)**
These are the hard rules that Claude cannot deviate from, no matter what:

| Wall | Rule | Why |
|------|------|-----|
| Auth | Never use API keys for subscription models | Burns credits (see CLAUDE.md) |
| Security | Never use bypassPermissions | Crashes on Windows (see CLAUDE.md) |
| SDK Pattern | Always wrap receive_response in try/except | Rate limit events kill responses |
| Verification | Must pass all checks before marking done | Can't deliver a broken install |
| Rollback | If install fails, clean up everything | Don't leave half-installs |

### The Improvement Loop

**Install #1-3:** Run the skill manually, watch for failures, fix them.
Each failure becomes a new deterministic wall or a new check in the preflight.

**Install #4-6:** The skill handles 90%+ automatically. You're mostly just
answering the intake questions and watching it work.

**Install #7-10:** You start finding patterns — "Windows machines always need
this extra step" or "Mac users always hit this Python issue." Each pattern
gets baked into the skill as a conditional.

**Install #10+:** The skill is nearly autopilot. The only things that can go
wrong are truly new situations (weird corporate firewalls, unusual OS configs).
Those are rare and each one makes the skill better.

### What Makes This Different from a Human Dev Doing It

A human dev doing installs:
- Gets bored, makes mistakes on the 15th install
- Forgets steps they haven't done in a while
- Each install takes the same amount of time (no learning curve for the tool)

Claude with a deterministic skill:
- Never forgets a step
- Every install follows the exact same process
- Gets BETTER over time as you add walls and checks
- Can do the install in 15 minutes instead of an hour
- Generates a clean install report every time

### The Tool Catalog

Each tool in your bank gets an entry:

```yaml
# tool-catalog/content-writer.yaml
name: Content Writer
repo: github.com/you/tool-content-writer
requires:
  - python: ">=3.11"
  - node: ">=20"
  - subscription: claude
install_type: standard  # vs "custom" for tools needing extra config
estimated_install_time: 15min
monthly_support_tier: basic
```

The installation skill reads this catalog entry and knows exactly what to do.
New tool? Add a YAML entry. Same install process.

### From Install Skill to Support Skill

The same pattern works for support:

```
SKILL: diagnose-tool-issue

INPUTS:
- tool_name: which tool is broken
- symptom: what's happening (from client description)
- install_path: where it's installed

DETERMINISTIC STEPS:
1. Run health checks (same as install verification)
2. Check logs for known error patterns
3. Match against known-issues database
4. If match found: apply known fix
5. If no match: gather diagnostics, report what was tried
```

Every support call makes the known-issues database bigger. Every fix becomes
a deterministic step. Support gets cheaper and faster over time.

### Summary

You're not learning to code. You're building a machine that installs and
supports your tools. The machine is Claude + deterministic skills + a growing
knowledge base of every install and every issue. Each engagement makes the
machine better. By the time you're doing 20+ installs, the whole process is:

1. Client fills out intake form (5 min)
2. You connect to their machine (5 min)
3. You say "run the install skill" (Claude does 15 min of work)
4. You show them how to use it (15 min)
5. Done. Bill them.

---

*Strategy developed through multiple conversations. This is the master reference document.*
