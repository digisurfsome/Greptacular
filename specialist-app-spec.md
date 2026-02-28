# The Specialist App — Full Product Specification

## "The Million-Token Specialist Crew"

**App Name:** Specialist (working title)
**Tagline:** *"Your AI dev team that actually remembers."*
**Category:** Developer Productivity / AI Agent Management SaaS
**Target Users:** Vibe coders, AI-assisted developers, non-traditional developers managing multiple apps

---

## The Problem

Every AI-assisted developer hits the same wall:

1. **Context burn** — Agents spend 50%+ of their token budget (150K+ tokens) just *understanding* the codebase before they can even start fixing anything
2. **Agent roulette** — When one agent fails, starting another is worse than starting from scratch because now you're scared, over-preparing, and the new agent might break what the last one touched
3. **Compounding frustration** — 7-10 failed agents on the same problem isn't uncommon. Each failure costs time, money, emotional energy, and confidence
4. **No memory** — Every new session starts from zero. The system never learns. The same problems get re-investigated from scratch every time
5. **The fizzle spiral** — People quit. The frustration loop (agent fails → stress → over-prep → agent fails again → family doubts → self-doubt) causes people to abandon projects that could have been life-changing

**The real cost isn't money — it's time, stress, and lost momentum.** Would you pay $1.50 to get a fix done permanently, in one shot, right now? Instead of burning through 10 agents at $5-15 each that each make it worse?

---

## The Solution

**Persistent specialist agents** — each one deeply context-loaded on a specific problem domain, sitting idle until needed, then able to fix issues instantly because they already understand the codebase in that area.

The economics work because of the 1M token context window:
- Spend ~100-200K tokens loading context and learning a specific subsystem (one-time cost)
- Have 500-800K tokens remaining purely for fixes
- Since they only activate when that specific problem recurs, token spend is efficient
- The context persists — no re-learning

---

## Core Architecture

### Three-Tier Model System

| Role | Model | Context | Cost Tier | Job |
|------|-------|---------|-----------|-----|
| **Orchestrator** | Haiku 4.5 / small model | 200K | Cheapest | User-facing. You talk to this one. It manages specialists, routes tasks, triages problems |
| **Mapper** | Sonnet 4.6 | 1M | Mid-tier | Maps out codebases, builds architecture blueprints. One-time cost per app |
| **Specialist** | Opus 4.6 | 1M | Premium | Does the actual coding fixes with full domain context loaded |

**Why this tiering matters:**
- Sonnet does the expensive-but-not-hard work of reading the entire codebase and structuring the blueprint — half the price of Opus for the mapping phase
- The architecture blueprint is shared across ALL specialists for that app — map once, specialize many times
- Opus only fires when there's real coding work to do, and it starts with all context already organized
- The Orchestrator handles conversation management at the cheapest tier — no reason to burn premium tokens on routing and triage

### Specialist Knowledge File Structure

```
~/.specialist-app/
  projects/
    my-saas-app/
      architecture.md              # Sonnet-generated full codebase blueprint
      architecture-meta.json       # When mapped, which model, token cost, file count
      specialists/
        auth-flow/
          context.md               # Subset of architecture relevant to auth
          fix-log.md               # History: what was fixed, when, why, what worked
          known-issues.md          # Recurring patterns that keep breaking
          session-snapshots/       # Checkpoint saves of specialist state
            2026-02-28-oauth-fix.json
        payment-system/
          context.md
          fix-log.md
          known-issues.md
        websocket-lifecycle/
          context.md
          fix-log.md
          known-issues.md
    another-app/
      architecture.md
      specialists/
        ...
```

**Key design principles:**
- Each specialist **inherits** from the master architecture blueprint but only loads what it needs
- The fix log is gold — if the same problem comes back, the specialist doesn't even need to diagnose, it already knows the fix pattern
- Specialists can create their own sub-documents as they learn more about their domain
- Session snapshots allow resuming exactly where a specialist left off

---

## Core Features

### 1. Project Registry — Connect Any Repo

Connect repositories by local path or git URL. The app works with ANY codebase, not just its own ecosystem.

**Flow:**
1. User adds a repo (local path or git clone URL)
2. System validates access, detects project type (React, Python, Node, etc.)
3. Triggers the Mapper (Sonnet 4.6) to do a full architecture scan
4. Generates `architecture.md` — the master blueprint that all specialists inherit from
5. Project appears in the dashboard, ready for specialist creation

**Project card shows:**
- Project name and path/URL
- Tech stack detected
- Number of active specialists
- Last activity date
- Architecture blueprint status (mapped / needs update / stale)
- Total token investment across all specialists

### 2. Architecture Mapper — One-Time Codebase Understanding

**Powered by Sonnet 4.6 (1M context)**

When a new project is connected, the Mapper agent:
1. Reads the entire codebase structure (files, directories, dependencies)
2. Identifies key patterns: routing, state management, API layers, database models, auth flows
3. Documents the architecture in a structured, searchable format
4. Identifies common problem areas and fragile code paths
5. Generates a dependency map showing how components connect

**The blueprint is shared** — map once, every specialist for that app inherits the understanding. When you create a new specialist for "payment processing," it doesn't need to re-read the whole codebase. It loads the architecture blueprint and zooms in on the payment-related sections.

**Blueprint refresh:** The mapper can be re-run when the codebase changes significantly. It diffs against the previous version and updates only what changed. Specialists are notified their context may be stale.

### 3. Specialist Roster — Your Team of Experts

A grid/list view of all specialists across all projects. Each specialist card shows:

- **Name & specialty label** (e.g., "Auth Guardian", "WebSocket Wrangler")
- **Target project** — which repo this specialist knows
- **Domain focus** — which subsystem/problem class they handle
- **Token budget** — total context used / remaining capacity
- **Fix count** — how many issues this specialist has resolved
- **Last active** — when they last ran
- **Status indicator:**
  - Green: idle, ready to deploy
  - Cyan: actively working (background)
  - Yellow: waiting for user input
  - Red: hit an error, needs attention
  - Gray: stale (codebase changed significantly since last active)
- **"Deploy" button** — opens the specialist's conversation, loads its context, ready to work

### 4. Specialist Creation Wizard

When creating a new specialist:

1. **Select project** — which repo does this specialist cover?
2. **Define domain** — what problem area? (free text or select from detected patterns)
3. **Context loading** — system automatically pulls relevant sections from the architecture blueprint
4. **Initial learning session** — specialist reads its context files, asks clarifying questions, builds its mental model
5. **Validation** — specialist summarizes what it understands, user confirms or corrects
6. **Ready state** — specialist is now loaded and idle, waiting for deployment

**Specialist types (suggested presets):**
- Auth & Security — login flows, token management, OAuth, API keys
- Database & Models — schema, migrations, queries, relationships
- Frontend State — React state, hooks, context, component lifecycle
- API & Routing — endpoints, middleware, request/response handling
- Build & Deploy — CI/CD, bundling, environment configs
- Testing — test infrastructure, coverage gaps, flaky tests
- Performance — bottlenecks, memory leaks, slow queries
- Custom — user defines the domain from scratch

### 5. Orchestrator — Your Command Center

The Orchestrator is who you talk to. Powered by a cheap model (Haiku 4.5), it:

- **Receives problem reports** — "Hey, the auth is broken again" or paste an error message
- **Routes to the right specialist** — identifies which specialist handles this domain
- **Deploys the specialist** — fires it off with the problem context
- **Reports back** — streams specialist progress, shows the fix, asks for approval
- **Manages the team** — suggests creating new specialists when it sees uncovered problem areas
- **Cross-references** — checks if this problem was solved before in the fix log

**Conversation flow:**
```
You:    "The OAuth token is expiring mid-session and users are seeing 401 errors"
Orch:   "That's Auth Guardian's domain. It has handled 3 similar issues before.
         The last one was the workspace chat session fallback — same pattern?
         Deploying Auth Guardian to your-app repo now..."
         [Specialist works in background]
Orch:   "Auth Guardian found the issue. The dunkstack_session.py has no OAuth
         fallback. Fix ready — 2 files changed. Want me to create the PR?"
You:    "Ship it."
Orch:   "PR created: fix/oauth-fallback-dunkstack. Auth Guardian logged this
         fix for future reference."
```

### 6. The Orchestrator's Intelligence Layer

The Orchestrator doesn't just route — it gets smarter over time:

- **Pattern recognition** — "You've had 4 auth issues this month. Want me to create a specialist that covers your entire auth subsystem?"
- **Proactive alerts** — "Your architecture blueprint is 2 weeks old and 47 files changed. Want me to refresh it?"
- **Cost optimization** — "This problem looks simple enough for Sonnet to handle. Skip the Opus specialist and save 60%?"
- **Cross-project insights** — "This same error pattern exists in 3 of your other apps. Want to deploy the specialist to all of them?"

---

## Advanced Features

### 7. Agent Failure Detection & Auto-Recovery

The #1 pain point. The system actively monitors running specialists for:

- **Circular behavior** — agent trying the same fix 3+ times (thrashing detection)
- **Token burn rate spikes** — spending tokens rapidly without making progress
- **Hallucination indicators** — claiming to install packages that don't exist, referencing files that aren't there
- **Regression creation** — detecting when a fix breaks something that was previously working

**When detected:**
1. Auto-pause the specialist BEFORE it wastes the entire session
2. Alert the user with a clear explanation of what went wrong
3. Save a checkpoint of the state right before things went sideways
4. Offer options: retry with different approach, escalate to human, roll back to checkpoint

**This kills the "restart nightmare."** Instead of discovering after $15 of wasted tokens that the agent was lying about installing the SDK, you get alerted 30 seconds in.

### 8. Session Black Box Recorder

Like an airplane's flight recorder. Every specialist session automatically records:

- **What was attempted** — every tool call, file edit, command run
- **What worked** — successful fixes, verified by tests
- **What failed** — failed approaches and WHY they failed
- **Root cause** — the actual issue, not the symptom
- **Time & cost** — how long, how many tokens, which model

**The Black Box feeds forward:**
- When a specialist re-encounters a similar problem, it loads relevant black box entries
- When a NEW specialist is created for a related domain, it gets relevant lessons learned
- The Orchestrator uses black box data to route more intelligently
- Your 10 failed agents become 10 lessons that make agent #11 nearly bulletproof

### 9. Cross-Project Standardization Engine

For users managing multiple apps (the target audience):

**Standards Library:**
- Define once: lint configs, component patterns, naming conventions, folder structures
- Apply across all projects
- When the specialist knows one app, it basically knows them all

**Standards Audit:**
- Point it at a messy project → it tells you exactly what doesn't conform
- Auto-fix mode: apply standards automatically where possible
- Deviation report: show exactly where each project diverges

**Standards Templates (Marketplace Opportunity):**
- Package proven standards as downloadable/purchasable templates
- "React + TypeScript + Tailwind Standard" — everything configured correctly
- Community-contributed standards
- Your standards become sellable assets

**The economic argument:** If everything follows the same patterns, specialists are dramatically cheaper to create and operate. A specialist that knows "how React auth works in your standard" can fix auth in ANY of your apps — not just one.

### 10. Progress & Momentum Dashboard

This fights the emotional fizzle spiral directly:

- **Streak tracker** — "You've shipped 14 features this week"
- **Time saved calculator** — "This would have taken an estimated 47 hours manually, you did it in 6"
- **Project timeline** — visual history of progress, see how far you've come
- **Win log** — automatic log of every successful fix and feature shipped
- **Cost efficiency** — "Specialists saved you $X vs. raw agent sessions"
- **Specialist ROI** — each specialist shows its total investment vs. value delivered

When your family says "you're spinning your wheels," you pull this up and say **"I shipped 14 features this week, here's the proof."**

### 11. Guardrails Mode — The Anti-Fizzle System

For users who are new and fragile in the process:

- **Guided workflows** — step-by-step processes that prevent common mistakes
- **Complexity warnings** — "This feature is complex, consider breaking it into 3 smaller ones"
- **Suggested break points** — "You've been at this 4 hours, your error rate is climbing, take a break"
- **Quick wins queue** — always have easy tasks ready so you can get a win when frustrated
- **Burnout detection** — monitors session length, error frequency, restart patterns
- **Recovery suggestions** — "Your last 3 sessions had issues. Here's what's working well — focus there"

### 12. Knowledge Base That Grows With You

Every solved problem becomes institutional knowledge:

- **Searchable solutions** — "I've seen this error before" with auto-surfacing
- **Project-specific knowledge** — patterns unique to each app
- **Global knowledge** — cross-project patterns and solutions
- **Error fingerprinting** — hash common errors to instantly match known solutions
- **Learning curves** — track which problem types you're getting faster at solving

This is what makes the 50th app dramatically easier than the 1st.

### 13. Specialist Handoff Packages

When you DO need to bring in a human developer:

- **One-click export** of project state, standards, architecture decisions
- **Problem briefing** — "Here's exactly what's wrong, here's what we've tried, here's the codebase map"
- **Context package** — everything a human needs to understand the situation in 5 minutes, not 5 hours
- **Attempt history** — every approach tried, why each failed
- Cuts human specialist onboarding from hours to minutes
- Saves hundreds of dollars per engagement

---

## Specialist Lifecycle

### How a Specialist Works End-to-End

```
1. CREATION
   User: "I keep having auth issues in my-app"
   Orchestrator: "Let me create an Auth specialist"
   → Mapper loads architecture.md
   → Extracts auth-relevant sections → context.md
   → Specialist does initial learning session
   → Validation: "I understand your auth uses OAuth with API key fallback..."
   → Status: READY (idle, green)

2. DEPLOYMENT
   User: "OAuth is expiring mid-session again"
   Orchestrator: "Deploying Auth Guardian..."
   → Specialist loads: context.md + fix-log.md + known-issues.md
   → Checks fix-log: "I've fixed this pattern before (2026-02-28)"
   → Connects to repo, creates branch
   → Makes the fix (already knows where to look)
   → Runs tests, verifies
   → Status: COMPLETED

3. LEARNING
   → Fix is logged in fix-log.md with full details
   → Known issues updated if new pattern discovered
   → Black box records the full session
   → Orchestrator notified: "Fix complete, PR ready"
   → Status: IDLE (green, fix count +1)

4. CROSS-DEPLOYMENT
   User: "Same auth error in my-other-app"
   Orchestrator: "Auth Guardian knows this pattern. Different repo but same fix class."
   → Specialist loads other-app architecture
   → Maps known fix pattern onto new codebase structure
   → Applies adapted fix
   → Logs cross-project fix

5. MAINTENANCE
   → Architecture blueprint refreshed when codebase changes
   → Specialist gets notified if its context areas changed
   → Stale specialists flagged for re-learning
   → Unused specialists archived after configurable period
```

---

## Technical Architecture

### Stack

- **Frontend:** React 19, TypeScript, Tailwind CSS v4, TanStack Query
- **Backend:** Python 3.11+, FastAPI, SQLAlchemy, SQLite (local) / Neon or Supabase (cloud)
- **AI Integration:** Claude Agent SDK (Opus 4.6, Sonnet 4.6, Haiku 4.5)
- **Real-time:** WebSocket for live specialist status, progress streaming
- **Process Management:** Background session manager for concurrent specialists
- **Storage:** Local filesystem for knowledge files, database for metadata/tracking

### Database Schema (Core Tables)

```sql
-- Projects (connected repos)
projects
  id, name, path_or_url, project_type, tech_stack (JSON),
  architecture_status, architecture_mapped_at, architecture_token_cost,
  created_at, updated_at

-- Specialists
specialists
  id, project_id (FK), name, domain_label, specialist_type,
  status (idle/active/stale/archived), context_tokens_used,
  context_tokens_remaining, fix_count, last_active_at,
  created_at, updated_at

-- Fix Log (the gold mine)
fix_log
  id, specialist_id (FK), project_id (FK),
  problem_description, root_cause, fix_description,
  files_changed (JSON), approach_taken, token_cost,
  duration_seconds, model_used, success (bool),
  created_at

-- Black Box Recordings
session_recordings
  id, specialist_id (FK), session_start, session_end,
  total_tokens, model_used, outcome (success/failure/partial),
  tool_calls (JSON), errors_encountered (JSON),
  lessons_learned (text), created_at

-- Standards Templates
standards
  id, name, description, tech_stack, config (JSON),
  lint_rules (JSON), folder_structure (JSON),
  is_marketplace (bool), author, downloads,
  created_at, updated_at

-- Knowledge Base Entries
knowledge_base
  id, project_id (FK, nullable for global), specialist_id (FK, nullable),
  error_fingerprint, problem_description, solution_description,
  tags (JSON), times_referenced, confidence_score,
  created_at, updated_at

-- User Metrics (momentum dashboard)
user_metrics
  id, date, features_shipped, fixes_completed,
  tokens_spent, tokens_saved_vs_raw, time_spent_minutes,
  estimated_manual_hours, streak_days,
  created_at
```

### API Endpoints (Core)

```
# Projects
GET    /api/projects                    # List all connected projects
POST   /api/projects                    # Connect a new project
GET    /api/projects/:id                # Get project details
DELETE /api/projects/:id                # Disconnect project
POST   /api/projects/:id/map           # Trigger architecture mapping
GET    /api/projects/:id/architecture   # Get architecture blueprint

# Specialists
GET    /api/specialists                 # List all specialists (filterable by project)
POST   /api/specialists                 # Create new specialist
GET    /api/specialists/:id             # Get specialist details
DELETE /api/specialists/:id             # Archive specialist
POST   /api/specialists/:id/deploy      # Deploy specialist to fix a problem
POST   /api/specialists/:id/pause       # Pause running specialist
GET    /api/specialists/:id/fix-log     # Get specialist's fix history
GET    /api/specialists/:id/knowledge   # Get specialist's knowledge files

# Orchestrator
POST   /api/orchestrator/message        # Send message to orchestrator
GET    /api/orchestrator/suggestions     # Get proactive suggestions
WS     /ws/orchestrator                 # Real-time orchestrator conversation

# Knowledge Base
GET    /api/knowledge                   # Search knowledge base
POST   /api/knowledge/match             # Find matching solutions for an error
GET    /api/knowledge/stats             # Knowledge base statistics

# Standards
GET    /api/standards                   # List standards templates
POST   /api/standards                   # Create new standard
POST   /api/standards/:id/audit         # Audit a project against a standard
POST   /api/standards/:id/apply         # Apply standard to a project

# Dashboard
GET    /api/dashboard/metrics           # Get momentum dashboard data
GET    /api/dashboard/streaks           # Get streak information
GET    /api/dashboard/roi               # Get specialist ROI calculations

# Sessions
GET    /api/sessions                    # List active/recent sessions
GET    /api/sessions/:id/blackbox       # Get session black box recording
WS     /ws/specialist/:id              # Real-time specialist output stream
```

---

## UI Pages

### 1. Command Center (Home/Dashboard)

The main landing page. Three sections:

**Top:** Orchestrator chat — always visible, always ready for input
**Middle:** Active specialists — cards for any currently running agents with live status
**Bottom:** Momentum dashboard — streaks, stats, recent wins

### 2. Projects Page

Grid of connected repos. Each card shows:
- Project name, path, tech stack badges
- Architecture status (mapped/stale/pending)
- Specialist count
- Quick actions: map, add specialist, open

### 3. Specialist Roster Page

Full grid/list of all specialists across all projects. Filterable by:
- Project
- Status (idle, active, stale)
- Domain type
- Last active

Each card is clickable → opens specialist detail view with:
- Full fix history
- Knowledge files
- Context size visualization
- Deploy button
- Re-learn button (refresh context)

### 4. Specialist Workspace

When a specialist is deployed, this is the live view:

**Left panel:** Specialist's conversation (what it's doing, thinking, fixing)
**Right panel:** File diff viewer (real-time changes)
**Bottom bar:** Progress indicators, token usage, elapsed time
**Top bar:** Specialist name, project, domain, controls (pause/stop/approve)

### 5. Knowledge Base Page

Searchable database of all solved problems:
- Full-text search across all fix logs and knowledge entries
- Filter by project, specialist, date range, error type
- Click any entry → see the full fix details, approach, files changed
- "Apply to current problem" button

### 6. Standards Library Page

Manage and apply coding standards:
- Create/edit standards templates
- Audit results view (project compliance scores)
- Marketplace browser (future: community standards)

### 7. Settings & Config

- API key management (BYOK)
- Model preferences per role (Orchestrator/Mapper/Specialist)
- Token budget limits
- Notification preferences
- Standards defaults

---

## Business Model & Pricing

### Recommended: BYOK + Platform Fee

Users bring their own Anthropic API key. They pay their own token costs directly. The platform charges for the specialist management infrastructure.

**Why BYOK first:**
- Target users already have API keys — they're already spending on agents that fail
- You're not selling API access, you're selling *the system that makes their API spend actually work*
- No margin risk on API costs
- Simpler to launch, simpler to explain

**Pricing Tiers:**

| Tier | Price | Projects | Specialists | Features |
|------|-------|----------|-------------|----------|
| **Starter** | $29/mo | 3 | 5 | Core features, basic dashboard |
| **Pro** | $49/mo | 10 | 25 | + Black box, knowledge base, standards |
| **Team** | $99/mo | Unlimited | Unlimited | + Marketplace, priority support, API access |

### Alternative: Credits Model (Phase 2)

Monthly sub ($19-79 tiered) includes X specialist sessions. Overage at per-session rate. Mark up API costs 20-30%. More revenue per user but carries API cost risk.

### Revenue Expansion Opportunities

1. **Standards Marketplace** — sell/buy proven project templates (take 30% cut)
2. **Education Content** — courses on standardization, best practices, "the methodology"
3. **Specialist Network** — vetted human developers who know the system (referral fees)
4. **Enterprise/Team** — shared specialists across team repos
5. **Template Packs** — pre-built specialist configurations for common stacks

---

## The Value Proposition

### For the User

> "Would you pay $1.50 to get that fixed right now, permanently, one shot — instead of burning through 10 agents at $5-15 each that each make it worse?"

**The math:**
- 10 failed agent sessions: $50-150 in wasted API costs + hours of time + emotional damage
- 1 specialist session: $3-5 in API costs + seconds of your time
- Platform fee: $29-49/month (pays for itself after 1-2 uses)

### For the Market

Most dev tools market on "build faster." This markets on **"don't give up."**

The target user isn't a senior dev who wants marginally faster tooling. It's the person who:
- Has 5-15 apps they're building or maintaining
- Isn't a traditional developer (vibe coder, entrepreneur, creator)
- Has been burned by agents failing repeatedly
- Is close to quitting but doesn't want to
- Needs wins, not just features

**That's a huge, underserved market** — and it's growing every day as more non-developers start building with AI.

---

## Development Roadmap

### Phase 1: Core (MVP)
- Project registry (connect repos)
- Architecture mapper (Sonnet 4.6)
- Specialist creation & deployment (Opus 4.6)
- Orchestrator (Haiku 4.5)
- Basic specialist roster UI
- Fix log
- BYOK API key management

### Phase 2: Intelligence
- Black box recorder
- Failure detection & auto-recovery
- Knowledge base with error fingerprinting
- Cross-project specialist deployment
- Momentum dashboard

### Phase 3: Standards & Growth
- Standardization engine
- Standards audit & auto-apply
- Guardrails mode
- Handoff packages
- Proactive orchestrator suggestions

### Phase 4: Marketplace & Community
- Standards marketplace
- Community knowledge sharing
- Specialist templates
- Team/enterprise features
- Education content platform

---

## Why This Will Work

1. **The pain is real and universal** — anyone doing AI-assisted development has experienced the agent failure loop
2. **The solution is technically proven** — the 1M context window, the SDK integration, the background session management all exist today
3. **The economics compound** — every app onboarded makes every specialist more valuable
4. **Usage drives retention** — more projects = more specialists = stickier product
5. **The emotional angle is viral** — "don't give up" hits different than "build faster"
6. **The market is growing exponentially** — more non-developers are building with AI every day
7. **No real competition** — there are agent tools, but none that provide persistent, specialist-level memory across projects

---

## Key Differentiator: Transferable Knowledge

A specialist that deeply understands "OAuth token expiry and API key fallback" doesn't just know how YOUR code handles it — it understands the *pattern*. When you point it at a different app with the same class of problem, it already knows what to look for and how to fix it. The repo-specific learning (file structure, naming conventions) is a fraction of the cost compared to learning the problem domain from scratch.

**This is the killer feature.** Your specialist bench gets more powerful with every app you add, not more expensive.
