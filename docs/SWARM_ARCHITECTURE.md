# The 25-Agent Swarm: Complete Architecture

## The Kitchen Analogy (Prep Cooks, Sous Chefs, Head Chefs)

The fundamental insight: **you don't want 25 Opus agents all burning through 200k context windows.** That's like staffing a restaurant with 25 head chefs and zero prep cooks. You want a hierarchy:

| Tier | Model | Context | Cost | Role | Count |
|------|-------|---------|------|------|-------|
| **Prep Cook** | Haiku | 200k (uses <20k) | ~$0.25/M in, $1.25/M out | Fast, narrow tasks | 10-12 |
| **Sous Chef** | Sonnet | 200k (uses 40-80k) | ~$3/M in, $15/M out | Core implementation | 8-10 |
| **Head Chef** | Opus | 200k (uses 80-150k) | ~$15/M in, $75/M out | Architecture, complex decisions | 3-5 |

**Cost math:** A full 200k Opus session costs ~$14 just for the input tokens. A Haiku session doing 20k tokens of analysis costs ~$0.005. You can run **2,800 Haiku prep sessions for the cost of one Opus session.** That's the leverage.

---

## The Complete 25-Agent Roster

### Phase 0: Intelligence Gathering (Before Any Code Exists)

These agents run ONCE at the start. They're the mise en place — everything prepped before the first flame is lit.

#### Agent 1: Spec Analyzer (Haiku)
**Already exists** as `spec_analyzer_prompt.template.md`
- Reads app_spec.txt and scores completeness (1-5)
- Identifies missing sections, contradictions, ambiguities
- Fast, cheap, catches problems before you burn expensive agent time
- **Output:** `.autoforge/spec-analysis.md`
- **Context used:** ~15k tokens (spec + analysis template)

#### Agent 2: Architecture Planner (Opus)
**Already exists** as `architect_prompt.template.md`
- Reads spec + spec analysis report
- Designs database schema, API structure, component tree, file organization
- This is where you WANT Opus — architectural decisions propagate to every feature
- **Output:** `ARCHITECTURE.md`
- **Context used:** ~60-100k tokens (deep reasoning about trade-offs)

#### Agent 3: Dependency Graph Builder (Sonnet)
**NEW — Currently embedded in the Initializer**
- Takes the architecture plan and builds the optimal feature ordering
- Runs cycle detection (Kahn's algorithm — already in `dependency_resolver.py`)
- Computes critical path — which features, if delayed, delay everything?
- Assigns priority scores for scheduling
- **Output:** Feature dependency graph written to `features.db`
- **Context used:** ~30k tokens
- **Why separate?** The initializer currently does feature creation AND ordering in one shot. Splitting lets you optimize ordering independently with graph theory algorithms the LLM doesn't need to reinvent.

#### Agent 4: Codebase Scout (Haiku)
**NEW — The most underrated prep cook**
- If working on an existing codebase (not greenfield), this agent reads every file
- Builds a map: what exists, what patterns are used, what conventions to follow
- Creates a `CODEBASE_MAP.md` that every subsequent agent gets injected into their prompt
- **Output:** `.autoforge/codebase-map.md`
- **Context used:** ~15-40k tokens (reads files, summarizes)
- **Why it matters:** Without this, every coding agent independently rediscovers the codebase patterns, wasting 10-15 turns of their context window on orientation. Do it ONCE.

#### Agent 5: Style Guide Extractor (Haiku)
**NEW — Specialized prep cook**
- Reads the existing codebase (or spec's style requirements)
- Extracts: naming conventions, file organization, component patterns, CSS approach
- Creates machine-readable style rules that get injected into coding prompts
- **Output:** `.autoforge/style_guide.md` (already supported by `_get_style_context()`)
- **Context used:** ~10k tokens

### Phase 1: Initialization (Feature Creation)

#### Agent 6: Feature Decomposer / Initializer (Opus)
**Already exists** as `initializer_prompt.template.md`
- Reads spec + architecture plan + codebase map
- Creates all features with descriptions, steps, acceptance criteria
- Sets dependencies between features
- THIS is the most important single agent — it defines what everyone else builds
- **Context used:** ~80-120k tokens (needs to reason about the full scope)

#### Agent 7: Feature Validator (Haiku)
**NEW — Quality gate after initialization**
- Reads all created features and validates them against the spec
- Checks: every spec requirement mapped to at least one feature?
- Checks: feature steps actually testable? Dependencies make sense?
- Checks: no circular dependencies (redundant with code check, but catches logical ones)
- **Output:** Validation report, optionally blocks the build
- **Context used:** ~20k tokens

### Phase 2: Implementation (The Assembly Line)

This is where parallelism matters. The orchestrator manages these concurrently.

#### Agents 8-12: Coding Agents (Sonnet x5)
**Already exist** — the core workers
- Each claims a feature via `feature_claim_and_get`
- Implements the feature following architecture plan + style guide
- Runs lint/typecheck, browser testing (unless YOLO)
- Marks passing and commits
- **Context used:** ~40-80k tokens per feature
- **Why Sonnet not Opus?** Sonnet is 5x cheaper and handles most single-feature implementation fine. The architecture plan gives enough guidance that you don't need Opus reasoning here.

#### Agent 13: Foundation Layer Agent (Opus)
**NEW — The first-mover**
- Specifically handles Feature #1 (or the foundation features with no dependencies)
- Gets Opus because foundational code (database schemas, auth, routing, shared components) has the highest downstream impact
- Every other agent builds on what this one creates
- **Context used:** ~100k tokens
- **Why dedicated?** If the foundation is wrong, every subsequent agent builds on sand. This is worth the Opus cost.

#### Agent 14: Integration Specialist (Sonnet)
**NEW — Runs alongside coding agents**
- Watches for completed features that need to connect to each other
- Example: Feature A creates a user API, Feature B creates a dashboard. This agent ensures the dashboard actually calls the user API correctly.
- Reads git diffs from recently completed features and checks integration points
- **Output:** Integration patches committed directly, or filed as issues
- **Context used:** ~40-60k tokens
- **When it runs:** After every 3-4 features complete

### Phase 3: Quality Assurance (Catch Before They Test)

These run CONCURRENTLY with Phase 2. The idea: catch problems before they reach the expensive testing agents.

#### Agent 15: Lint Watcher (Haiku)
**NEW — The cheapest quality gate**
- Runs continuously: `npm run lint`, `ruff check .`, `npx tsc --noEmit`
- After every coding agent commits, checks if they introduced lint errors
- If yes: marks the feature as failing with specific lint output
- **Context used:** ~5k tokens (just runs commands and reads output)
- **Why?** Coding agents sometimes "forget" to lint at the end. This catches it for pennies.

#### Agent 16: Static Analysis Agent (Haiku)
**NEW**
- Runs security-focused static analysis after each commit
- Checks for: XSS vulnerabilities, SQL injection, exposed secrets, unsafe dependencies
- Uses existing tools (`npm audit`, dependency scanning) rather than LLM reasoning
- **Output:** Security report per feature
- **Context used:** ~10k tokens
- **Why Haiku?** It's running tools and reading output, not reasoning about code.

#### Agent 17: Type Coherence Checker (Haiku)
**NEW**
- After N features complete, checks that TypeScript types are consistent across the codebase
- Catches: mismatched API response types between frontend/backend, broken imports across module boundaries
- This is the bug class that individual feature agents miss because they only see their own feature
- **Context used:** ~15k tokens

### Phase 4: Testing (Verify It Works)

#### Agents 18-19: Regression Testing Agents (Sonnet x2)
**Already exist** as `testing_prompt.template.md`
- Run existing test suites against completed features
- Browser automation with Playwright
- Batch mode: test 3-5 features per session
- **Context used:** ~40-60k tokens per batch
- **Why Sonnet?** Browser testing involves multi-step reasoning (navigate, fill form, assert). Haiku would struggle.

#### Agent 20: Code Review Agent (Sonnet)
**Already exists** as `reviewer_prompt.template.md`
- Reviews completed+tested features for code quality
- Checks: security, error handling, test quality, accessibility
- Marks features as reviewed or fails them back with notes
- **Context used:** ~30-50k tokens per batch

#### Agent 21: QA Agent (Sonnet)
**Already exists** as `qa_prompt.template.md`
- Final sweep: end-to-end functionality, cross-feature integration
- Runs AFTER all features are reviewed
- The last gate before "done"
- **Context used:** ~50-80k tokens

### Phase 5: Polish & Documentation (After Core Is Complete)

These only run after all features pass.

#### Agent 22: Documentation Generator (Haiku)
**NEW — The knowledge base writer**
- Reads all completed code and generates:
  - API documentation (endpoints, request/response schemas)
  - Component library docs (props, usage examples)
  - Database schema docs (tables, relationships)
  - Setup/installation guide
- **Output:** `docs/` directory with full project documentation
- **Context used:** ~20k tokens (reads code, writes structured docs)
- **Why Haiku?** Documentation is structured transformation, not creative reasoning.

#### Agent 23: README & Onboarding Agent (Sonnet)
**NEW**
- Creates the public-facing README.md
- Generates: project description, screenshots placeholder, quick start guide, architecture overview diagram (mermaid), contributing guide
- **Context used:** ~20k tokens
- **Why Sonnet over Haiku?** Good READMEs require persuasive writing, not just code summarization.

#### Agent 24: Test Coverage Analyzer (Haiku)
**NEW**
- Runs coverage tools and identifies untested code paths
- Generates additional test cases for uncovered critical paths
- Prioritizes: auth flows, payment flows, data mutation paths
- **Output:** Additional test files + coverage report
- **Context used:** ~15k tokens

#### Agent 25: Performance Baseline Agent (Haiku)
**NEW**
- Runs Lighthouse (or equivalent) against the built app
- Records baseline performance metrics
- Identifies obvious performance issues (unoptimized images, missing lazy loading, N+1 queries)
- **Output:** `.autoforge/performance-baseline.md`
- **Context used:** ~10k tokens

---

## The Orchestration Timeline

```
TIME ─────────────────────────────────────────────────────────────►

PHASE 0: Intelligence Gathering (~5 min)
├─ [Haiku] Spec Analyzer ──────┐
├─ [Haiku] Codebase Scout ─────┤ (parallel)
└─ [Haiku] Style Extractor ────┘
         │
         ▼
   [Opus] Architect ────────────── (sequential, needs Phase 0 output)
         │
PHASE 1: Initialization (~15 min)
         ▼
   [Opus] Feature Decomposer ───── (sequential)
         │
   [Haiku] Feature Validator ───── (sequential gate)
         │
PHASE 2+3: Implementation + Quality (~30-90 min, parallel)
         ▼
   ┌─────────────────────────────────────────────────┐
   │  [Opus]   Foundation Agent ──► Feature #1       │
   │  [Sonnet] Coder #1 ──────────► Feature #2       │
   │  [Sonnet] Coder #2 ──────────► Feature #3       │ CONCURRENT
   │  [Sonnet] Coder #3 ──────────► Feature #4       │
   │  [Sonnet] Coder #4 ──────────► Feature #5       │
   │  [Sonnet] Coder #5 ──────────► (ready pool)     │
   │                                                   │
   │  [Haiku]  Lint Watcher ───────► (continuous)     │
   │  [Haiku]  Static Analysis ────► (on commit)      │
   │  [Haiku]  Type Coherence ─────► (every N done)   │
   │  [Sonnet] Integration ────────► (every 3-4 done) │
   │                                                   │
   │  [Sonnet] Tester #1 ─────────► (regression)     │
   │  [Sonnet] Tester #2 ─────────► (regression)     │
   │  [Sonnet] Reviewer ──────────► (review batch)   │
   └─────────────────────────────────────────────────┘
         │
PHASE 4: Final QA (~15 min)
         ▼
   [Sonnet] QA Agent ───────────── (full sweep)
         │
PHASE 5: Polish (~10 min)
         ▼
   ┌─────────────────────────────────────────────────┐
   │  [Haiku]  Doc Generator ──────► API/schema docs │
   │  [Sonnet] README Agent ───────► README.md       │ CONCURRENT
   │  [Haiku]  Coverage Analyzer ──► test gaps       │
   │  [Haiku]  Performance ────────► baseline        │
   └─────────────────────────────────────────────────┘
```

---

## Cost Breakdown: The 25-Agent Run

Assuming a medium-complexity app (20 features, ~15k lines of code):

| Agent Role | Model | Sessions | Tokens/Session | Cost/Session | Total Cost |
|-----------|-------|----------|----------------|-------------|-----------|
| Spec Analyzer | Haiku | 1 | ~15k in, 3k out | $0.01 | $0.01 |
| Codebase Scout | Haiku | 1 | ~30k in, 5k out | $0.01 | $0.01 |
| Style Extractor | Haiku | 1 | ~10k in, 3k out | $0.01 | $0.01 |
| Architect | Opus | 1 | ~80k in, 20k out | $2.70 | $2.70 |
| Initializer | Opus | 1 | ~100k in, 30k out | $3.75 | $3.75 |
| Feature Validator | Haiku | 1 | ~20k in, 5k out | $0.01 | $0.01 |
| Foundation Agent | Opus | 1 | ~100k in, 25k out | $3.38 | $3.38 |
| Coding Agents | Sonnet | 20 | ~60k in, 15k out | $0.41 | $8.10 |
| Lint Watcher | Haiku | 5 | ~5k in, 2k out | $0.004 | $0.02 |
| Static Analysis | Haiku | 5 | ~10k in, 3k out | $0.01 | $0.04 |
| Type Coherence | Haiku | 3 | ~15k in, 5k out | $0.01 | $0.03 |
| Integration | Sonnet | 3 | ~50k in, 10k out | $0.30 | $0.90 |
| Testers | Sonnet | 8 | ~50k in, 10k out | $0.30 | $2.40 |
| Reviewer | Sonnet | 4 | ~40k in, 10k out | $0.27 | $1.08 |
| QA Agent | Sonnet | 1 | ~60k in, 15k out | $0.41 | $0.41 |
| Doc Generator | Haiku | 1 | ~20k in, 10k out | $0.02 | $0.02 |
| README Agent | Sonnet | 1 | ~20k in, 8k out | $0.18 | $0.18 |
| Coverage Analyzer | Haiku | 1 | ~15k in, 5k out | $0.01 | $0.01 |
| Performance | Haiku | 1 | ~10k in, 3k out | $0.01 | $0.01 |
| **TOTAL** | | **~59 sessions** | | | **~$23.07** |

Compare to running 25 Opus agents with full context: **~$90-$130.** The tiered approach cuts cost by 70-80%.

---

## Where Features Stop Adding Value (The Value Cliff)

### Tier 1: Core Value (MUST HAVE — directly sells the product)

These are the features that make someone say "I need this":

1. **Multi-agent parallel orchestration** — THE differentiator. No one else does dependency-aware parallel Claude agents.
2. **Visual kanban + dependency graph** — People need to SEE the swarm working. This is the demo moment.
3. **One-click project creation** (spec → features → code) — The "it just works" moment.
4. **YOLO mode** — Fast prototyping, skip testing. People want speed first, quality later.
5. **Browser-based testing** — Agents that actually verify their own work in a real browser.
6. **Real-time progress streaming** — WebSocket updates, live agent output. You're watching robots build your app.
7. **Spec creation assistant** — Natural language → structured spec. Lowers the barrier to "what do I type?"
8. **Feature dependency system** — Ensures foundational code exists before dependent features start. Without this, parallel mode produces garbage.
9. **Batch mode** — Multiple features per session. Critical for reducing session overhead.
10. **Auto-retry on failure** — Features that fail get retried automatically. Resilience.

### Tier 2: Competitive Advantage (SHOULD HAVE — differentiates from competitors)

These push you ahead of alternatives (Cursor, Windsurf, Bolt, v0, etc.):

11. **Multi-model tiering** (Opus/Sonnet/Haiku per role) — Cost optimization that no competitor offers at the orchestration level.
12. **Spec analyzer + quality gate** — Catches bad specs BEFORE burning $20+ on implementation.
13. **Architecture planner agent** — Pre-computes the blueprint so coding agents don't make conflicting decisions.
14. **Code review agent pipeline** — Automated code review without human intervention.
15. **QA agent** — Final quality sweep. The "we actually verify this works" story.
16. **Regression testing agents** — Continuously verify nothing is broken as new features land.
17. **Scheduling** (time-based agent runs) — "Build this overnight while I sleep."
18. **Project expansion** (add features to existing projects) — Not just greenfield; you can grow projects.
19. **Style guide system** — Consistent design language across all agent-generated code.
20. **Custom command allowlists** — Enterprise security. Control exactly what agents can execute.

### Tier 3: Power User Features (NICE TO HAVE — deepens engagement)

These keep power users happy but don't sell the product:

21. **Integration specialist agent** — Catches cross-feature bugs automatically.
22. **Lint/static analysis watchers** — Cheap quality gates running continuously.
23. **Type coherence checking** — Cross-module type consistency.
24. **Codebase scout agent** — For existing codebases, pre-maps everything before coding.
25. **Performance baseline agent** — Lighthouse scores out of the box.
26. **Documentation generator** — Auto-generated API docs, component docs.
27. **Boilerplate templates** — Pre-built starting points (SaaS, e-commerce, etc.).
28. **Dev server control** — Start/stop the dev server from the UI.
29. **Terminal integration** — xterm.js terminal in the UI.
30. **Keyboard shortcuts** — Power user productivity.

### Tier 4: Marketing & Ecosystem (DIMINISHING VALUE — nice stories but not features)

31. **Tutorial video generation** — Cool demo, but a one-time marketing effort, not a product feature.
32. **Landing page generation** — Marketing, not product.
33. **User manual / knowledge base** — Documentation that should exist as docs, not as a feature.
34. **CLI mode** — Already exists. The UI is the product.
35. **Alternative API providers** (GLM, Ollama, Kimi) — Expands market but doesn't deepen core value.

### THE VALUE CLIFF

```
VALUE
  │
  │  ████  Tier 1: Core (features 1-10)
  │  ████  — Every feature here DIRECTLY drives adoption
  │  ████  — Missing any of these = deal-breaker for target users
  │  ████
  │  ████
  │  ████
  │  ██████  Tier 2: Competitive (features 11-20)
  │  ██████  — Each one adds significant differentiation
  │  ██████  — But you CAN launch without them
  │  ██████
  │  ████████  Tier 3: Power User (features 21-30)
  │  ████████  — Diminishing returns start here
  │  ████████  — Each feature helps EXISTING users, not NEW users
  │  ████████
  │  ──────────── THE CLIFF ────────────
  │  ██████████  Tier 4: Ecosystem (31+)
  │  ██████████  — These are content/marketing, not product
  │  ██████████  — Building them as "features" is over-engineering
  │
  └──────────────────────────────────────► FEATURE COUNT
        10        20        30        40
```

**The cliff is at feature ~25-30.** After that, you're building marketing assets that should be blog posts, not product features.

---

## Optimal Build Order (What to Build Next)

Based on your EXISTING architecture (`parallel_orchestrator.py` already has Phases 0-2, testing, review, QA):

### Already Built (your current state):
- Spec Analyzer (Phase 0)
- Architect Planner (Phase 0.5)
- Initializer (Phase 1)
- Coding Agents x5 parallel (Phase 2)
- Testing Agents (Phase 3)
- Review Agents (Phase 3)
- QA Agent (Phase 4)
- Scheduling
- Project expansion
- Style guide injection
- Boilerplate templates
- Dev server control
- Terminal integration

### Next to build (highest ROI, in order):

**1. Multi-model tiering** — Biggest cost savings, biggest "aha" for users
- Haiku for prep tasks, Sonnet for implementation, Opus for architecture
- Change `_spawn_coding_agent` to accept a model parameter per agent type
- Already partially supported via `self.model` on the orchestrator

**2. Codebase Scout agent** — Biggest quality improvement for existing codebases
- New template: `scout_prompt.template.md`
- Runs in Phase 0 alongside spec analysis
- Output injected into all subsequent prompts via `_get_scout_context()`

**3. Lint Watcher (continuous)** — Cheapest quality improvement
- Haiku agent that runs `lint` + `tsc` after every coding agent commit
- Catches problems in seconds for fractions of a penny
- Separate from testing agents (those use browser automation)

**4. Foundation Agent (dedicated Opus for Feature #1)** — Biggest quality improvement for greenfield
- Route the first feature (or features with 0 dependencies) to an Opus agent
- Everything else stays on Sonnet
- The foundation determines 70% of downstream code quality

**5. Integration Specialist** — Catches the bug class parallel mode creates
- When features are built in parallel, they don't know about each other
- This agent reads recently completed features and patches integration points
- Runs every 3-4 features

**6. Type Coherence Checker** — The TypeScript-specific quality gate
- After N features, verify all types are consistent
- Catches: API types drifting between frontend/backend
- Haiku, runs tools and reads output

---

## Marketing Angles: How to Frame This

### The Core Positioning

**"25 AI agents build your app in parallel — from spec to deployed, in under an hour."**

That's the headline. Everything else is supporting evidence.

### Specific Angles (by audience)

#### For Solo Developers:
- "The engineering team you always wanted but couldn't afford"
- "Write a spec in English. Get a production app with tests, docs, and code review."
- "Your AI agents test each other's work. You just approve the final result."
- **Key benefit:** One person can ship what used to require a team of 5-10.

#### For Startups:
- "Build your MVP overnight. Literally."
- "Schedule your agents to run at 2am. Wake up to a working app."
- "Multi-model tiering means your AI bill is $23, not $130."
- **Key benefit:** Speed to market with controlled costs.

#### For Agencies / Freelancers:
- "Turn a client spec into a working prototype during the sales call"
- "YOLO mode for the pitch, full testing mode for delivery"
- "Each project gets its own security sandbox. Client isolation by default."
- **Key benefit:** 10x throughput on client work.

#### For Enterprise:
- "Every bash command your agents run goes through a security allowlist"
- "Org-wide blocked commands. Project-level permissions. Defense in depth."
- "Full audit trail: every agent action logged, every feature tracked, every test recorded."
- **Key benefit:** Security and compliance without sacrificing automation.

### The "Why This and Not Cursor/Copilot" Pitch

**Cursor/Copilot:** One agent, one file at a time, one suggestion at a time. YOU still architect, coordinate, test, review, and deploy. They're a better autocomplete.

**AutoForge:** 25 agents that handle the ENTIRE pipeline — from analyzing your spec for completeness, to planning the architecture, to implementing features in parallel, to testing them with a real browser, to reviewing the code for security, to generating documentation. You go from idea to deployed app.

**The analogy:** Cursor is a really smart pair programmer. AutoForge is a software company.

### Feature-Specific Selling Points

| Feature | How to Sell It |
|---------|---------------|
| Parallel orchestration | "5 coding agents working simultaneously, each on a different feature" |
| Dependency-aware scheduling | "Agents never start a feature until its prerequisites are done" |
| Multi-model tiering | "Opus for the architecture, Sonnet for the code, Haiku for the lint — optimized cost" |
| Browser testing | "Your agents actually open a browser and verify what they built works" |
| Spec analysis gate | "Catches incomplete specs BEFORE burning $20 on bad code" |
| Live kanban + graph | "Watch your app get built in real-time on a visual dependency graph" |
| YOLO mode | "Need it fast? Skip testing. Need it right? Turn testing back on." |
| Scheduling | "Set it to build overnight. Wake up to 20 features implemented." |
| Security sandbox | "Agents can only run commands you've whitelisted. Full org-level control." |
| Code review pipeline | "Every feature gets reviewed by an AI senior developer before it's marked done" |

### The Moat

Your real competitive advantages (hard to replicate):

1. **The orchestrator** — Dependency-aware parallel agent scheduling is genuinely novel. Cursor, Bolt, v0 don't have this.
2. **The pipeline** — Spec → Analyze → Architect → Initialize → Code → Test → Review → QA is a complete SDLC in a box. No one else has the full pipeline.
3. **The cost optimization** — Multi-model tiering is obvious in retrospect but no one else has implemented it at the orchestration level.
4. **The security model** — Hierarchical allowlists with org/project separation. Enterprise-ready from day one.
5. **The filesystem protocol** — Using files (features.db, prompts/, ARCHITECTURE.md) as the coordination fabric between agents. Simple, debuggable, human-readable. Same pattern as drone choreography (config.csv, trajectory files).

---

## The "Prep Cook" Philosophy: Context Window Budget Management

The most important insight for the 25-agent swarm:

### The Problem
An Opus agent at 200k context costs ~$14 per session. If that agent spends 30% of its context window on ORIENTATION (reading files, understanding the codebase, figuring out conventions), that's **$4.20 wasted** per session across 20 sessions = **$84 wasted.**

### The Solution: Prep Cooks Pre-Chew the Context

```
WITHOUT PREP COOKS:
  Coding Agent Session:
  ├─ Turn  1-15: Read codebase, figure out patterns     (WASTED ORIENTATION)
  ├─ Turn 16-25: Read architecture, plan approach        (WASTED PLANNING)
  ├─ Turn 26-100: Actually implement the feature         (PRODUCTIVE WORK)
  └─ Turn 101-120: Test, commit, clean up                (PRODUCTIVE WORK)

  Productive: 79% | Wasted: 21% | Cost: $14/session

WITH PREP COOKS:
  [Haiku] Codebase Scout: Pre-reads everything, creates map    ($0.01)
  [Haiku] Style Extractor: Documents conventions               ($0.01)
  [Opus] Architect: Creates ARCHITECTURE.md                    ($2.70)

  Coding Agent Session (receives pre-chewed context):
  ├─ Turn 1-3: Read injected map + architecture (MINIMAL ORIENTATION)
  ├─ Turn 4-100: Actually implement the feature  (PRODUCTIVE WORK)
  └─ Turn 101-120: Test, commit, clean up        (PRODUCTIVE WORK)

  Productive: 97% | Wasted: 3% | Cost: $8/session (Sonnet)

  Net savings per session: $6 * 20 sessions = $120 saved
  Prep cook cost: $2.72
  NET BENEFIT: $117.28 saved + higher quality (consistent patterns)
```

### Context Budget Allocation Per Agent Type

| Agent Type | Max Turns | Orientation Budget | Implementation Budget | Wrap-up Budget |
|-----------|-----------|-------------------|----------------------|---------------|
| Prep Cook (Haiku) | 30 | 3 turns (10%) | 22 turns (73%) | 5 turns (17%) |
| Coding Agent (Sonnet) | 135 | 5 turns (4%) | 110 turns (81%) | 20 turns (15%) |
| Architecture (Opus) | 150 | 15 turns (10%) | 115 turns (77%) | 20 turns (13%) |
| Testing (Sonnet) | 80 | 5 turns (6%) | 60 turns (75%) | 15 turns (19%) |
| Review (Sonnet) | 60 | 5 turns (8%) | 45 turns (75%) | 10 turns (17%) |

### The Rule of Three Pre-Chews

Before ANY expensive agent starts, it should receive THREE pre-chewed artifacts:
1. **ARCHITECTURE.md** — What to build and how
2. **CODEBASE_MAP.md** — What already exists (or empty if greenfield)
3. **STYLE_GUIDE.md** — How it should look and feel

Total cost of pre-chewing: ~$3. Savings across 20 feature sessions: ~$100+.

---

## Every Possible Feature (Complete Inventory)

### Already Implemented (in the codebase today)

| # | Feature | File(s) | Tier |
|---|---------|---------|------|
| 1 | Parallel orchestration (1-5 agents) | `parallel_orchestrator.py` | Core |
| 2 | Dependency-aware scheduling | `api/dependency_resolver.py` | Core |
| 3 | Visual kanban board | `ui/src/App.tsx` | Core |
| 4 | Dependency graph visualization | `ui/src/components/DependencyGraph.tsx` | Core |
| 5 | One-click project creation | `server/routers/projects.py` | Core |
| 6 | YOLO mode (skip testing) | `prompts.py`, `parallel_orchestrator.py` | Core |
| 7 | Browser-based testing (Playwright) | `testing_prompt.template.md` | Core |
| 8 | Real-time WebSocket progress | `ui/src/hooks/useWebSocket.ts` | Core |
| 9 | Spec creation assistant | `server/routers/spec_creation.py` | Core |
| 10 | Feature dependency system | `mcp_server/feature_mcp.py` | Core |
| 11 | Batch mode (multi-feature/session) | `prompts.py` (batch prompts) | Core |
| 12 | Auto-retry on failure | `parallel_orchestrator.py` | Core |
| 13 | Spec analyzer (Phase 0) | `spec_analyzer_prompt.template.md` | Competitive |
| 14 | Architecture planner (Phase 0.5) | `architect_prompt.template.md` | Competitive |
| 15 | Code review agent pipeline | `reviewer_prompt.template.md` | Competitive |
| 16 | QA agent (final sweep) | `qa_prompt.template.md` | Competitive |
| 17 | Regression testing agents | `testing_prompt.template.md` | Competitive |
| 18 | Time-based scheduling | `server/services/scheduler_service.py` | Competitive |
| 19 | Project expansion (add features) | `server/routers/expand_project.py` | Competitive |
| 20 | Style guide system | `prompts.py` (`_get_style_context`) | Competitive |
| 21 | Security allowlists | `security.py` | Competitive |
| 22 | Boilerplate templates | `server/services/boilerplate_manager.py` | Power User |
| 23 | Dev server control | `server/services/dev_server_manager.py` | Power User |
| 24 | Terminal integration | `ui/src/components/Terminal.tsx` | Power User |
| 25 | Assistant chat panel | `ui/src/components/AssistantPanel.tsx` | Power User |
| 26 | Keyboard shortcuts | UI keyboard handler | Power User |
| 27 | In-app documentation | `ui/src/components/docs/` | Power User |
| 28 | Celebration overlay (confetti) | `ui/src/components/CelebrationOverlay.tsx` | Polish |
| 29 | Agent mascots (Spark, Fizz, Octo) | `AgentMissionControl.tsx` | Polish |
| 30 | Vertex AI support | `client.py` | Ecosystem |
| 31 | Alternative providers (GLM, Ollama) | Settings UI | Ecosystem |
| 32 | npm global install | `bin/autoforge.js`, `lib/cli.js` | Distribution |
| 33 | Extra read paths (cross-project) | `client.py` | Enterprise |
| 34 | Org-level config | `security.py`, `examples/org_config.yaml` | Enterprise |

### Not Yet Implemented (The Roadmap)

Ordered by ROI (value delivered per effort invested):

| Priority | Feature | Model Tier | Est. Effort | Impact |
|----------|---------|-----------|-------------|--------|
| **P0** | Multi-model tiering (Haiku/Sonnet/Opus per role) | Architecture | 2-3 days | Cuts costs 70%+ |
| **P0** | Codebase Scout agent | Haiku | 1 day | 20% less wasted context |
| **P1** | Foundation Agent (Opus for first feature) | Opus | 1 day | Higher downstream quality |
| **P1** | Lint Watcher (continuous Haiku) | Haiku | 0.5 day | Catches errors for pennies |
| **P1** | Feature Validator (post-init quality gate) | Haiku | 0.5 day | Catches bad features early |
| **P2** | Integration Specialist agent | Sonnet | 2 days | Fixes parallel-mode gaps |
| **P2** | Type Coherence Checker | Haiku | 1 day | Cross-module consistency |
| **P2** | Static Analysis agent | Haiku | 0.5 day | Security without cost |
| **P2** | Documentation Generator | Haiku | 1 day | Auto-generated docs |
| **P3** | Test Coverage Analyzer | Haiku | 1 day | Identifies test gaps |
| **P3** | Performance Baseline | Haiku | 0.5 day | Lighthouse scores |
| **P3** | README/Onboarding Agent | Sonnet | 0.5 day | Better first impression |
| **P3** | Dependency Graph Builder (separate from init) | Sonnet | 1.5 days | Optimal ordering |
| **P4** | Computer Use agent (visual testing) | Sonnet | 3 days | "Eyes" on the app |
| **P4** | Deployment agent (Vercel/Netlify) | Haiku | 2 days | One-click deploy |
| **P4** | Git PR agent (auto-create PRs) | Haiku | 1 day | Git workflow |
| **P4** | Monitoring setup agent | Haiku | 1 day | Production readiness |

---

## The "Never Test" Strategy: How Prep Cooks Reduce Testing

This is the counterintuitive insight: **the more you invest in upstream quality, the less you need downstream testing.**

```
TRADITIONAL PIPELINE (test-heavy):
  Code → Lint → Test → Review → QA → Ship
  Cost: $$$$ testing, bugs found LATE (expensive to fix)

PREP COOK PIPELINE (prevention-heavy):
  Analyze → Architect → Scout → Extract Style →
  Code (with injected context) → Lint Watch → Type Check →
  Light Test → Quick Review → Ship
  Cost: $$ prep + $ testing, bugs PREVENTED (never exist)
```

What each prep cook prevents:

| Prep Cook | Bugs Prevented | Testing Saved |
|-----------|---------------|--------------|
| Spec Analyzer | Incomplete features, missing requirements | 30% of QA failures |
| Architect | Conflicting database schemas, broken APIs | 40% of integration bugs |
| Codebase Scout | Wrong patterns, duplicate utilities | 20% of review findings |
| Style Extractor | Inconsistent UI, wrong component usage | 50% of visual bugs |
| Feature Validator | Untestable features, circular deps | 15% of blocked agents |
| Lint Watcher | Syntax errors, import issues | 90% of "obvious" failures |
| Type Coherence | Mismatched API types | 60% of runtime type errors |

**Net effect:** The prep cooks cost ~$3 total but prevent ~$15-20 worth of testing agent time and rerun costs.

---

## The CLI-to-SaaS Bridge: How the Mesh Becomes the Product

### The Key Insight

Right now, running through the Claude Code CLI, you get an entire **control mesh for free**:

```
CLI MODE (Current - R&D Lab)
├── .claude/agents/         → Agent personalities, workflows, quality bars
├── .claude/commands/       → Slash commands (/create-spec, /checkpoint)
├── .claude/skills/         → Reusable capabilities (frontend-design, gsd-to-spec)
├── CLAUDE.md               → Project-level rules every agent reads
├── Hooks (PreToolUse)      → Intercept EVERY bash command before execution
├── Hooks (PreCompact)      → Control what survives context compaction
├── setting_sources          → Pull config from project dir automatically
├── allowed_tools           → Per-agent tool scoping (coding vs testing vs review)
├── permissions             → Filesystem sandboxing, read-only paths
├── MCP servers             → Feature tracking, Playwright browser automation
└── max_turns               → Hard budget caps per agent type
```

This is the **prototyping environment**. You're dialing in the exact formula for how
agents should behave — what rules keep them on track, what hooks catch bad commands,
what tool scoping prevents agents from stepping on each other, what compaction
instructions preserve the right context when memory runs low.

For a **SaaS tool**, you can't use the CLI directly — you're calling the Anthropic API
with API keys, not spawning `claude` CLI processes. BUT the formulas you've dialed in
through CLI experimentation translate directly to API-level equivalents:

### The Translation Map: CLI Features → API Equivalents

```
CLI FEATURE                          API EQUIVALENT
──────────────────────────────────── ─────────────────────────────────────
.claude/agents/*.md                  → system_prompt per agent session
  (agent personality, workflow)         (inject the .md content as system prompt)

CLAUDE.md                            → Shared system prompt prefix
  (project rules)                       (prepend to every agent's system prompt)

Hooks: PreToolUse (Bash security)    → tool_choice filtering + custom middleware
                                        (validate tool inputs server-side before
                                         forwarding to the API)

Hooks: PreCompact                    → Manual context management
                                        (token counting + selective message pruning
                                         using the same preserve/discard rules)

allowed_tools per agent type         → tools parameter on API call
  CODING_AGENT_TOOLS = [...]            (only send the tools array for that role)
  TESTING_AGENT_TOOLS = [...]

permissions (filesystem sandbox)     → Server-side path validation
                                        (your API server validates file paths
                                         before executing any file operations)

MCP servers (feature tracking)       → Direct database calls
                                        (feature_claim_and_get becomes a
                                         REST endpoint, not an MCP tool)

max_turns                            → Turn counter in your API loop
                                        (count messages, stop at limit)

setting_sources: ["project"]         → Load project config from DB
                                        (same data, different storage)

.claude/skills/                      → Prompt libraries / templates
                                        (store skill content in DB, inject
                                         into system prompt when needed)

.claude/commands/                    → API endpoints
                                        (/create-spec becomes POST /api/spec)
```

### What You're Actually Building in CLI Mode

Every time you tweak an agent rule, add a hook, or adjust tool scoping, you're
**writing the specification for the SaaS version without knowing it**:

```python
# CLI MODE (current) - in client.py:
hooks={
    "PreToolUse": [
        HookMatcher(matcher="Bash", hooks=[bash_hook_with_context]),
    ],
    "PreCompact": [
        HookMatcher(hooks=[pre_compact_hook]),
    ],
}

# SaaS MODE (future) - becomes middleware:
class AgentMiddleware:
    async def before_tool_use(self, tool_name, tool_input, agent_context):
        """Same logic as bash_security_hook, but runs server-side."""
        if tool_name == "bash":
            return await self.validate_command(tool_input["command"], agent_context)
        return {"allow": True}

    async def before_compaction(self, messages, agent_context):
        """Same logic as pre_compact_hook, but manages message array directly."""
        return self.prune_messages(messages, preserve_rules=COMPACTION_RULES)
```

```python
# CLI MODE (current) - per-agent tool scoping in client.py:
CODING_AGENT_TOOLS = [
    "mcp__features__feature_claim_and_get",
    "mcp__features__feature_mark_passing",
    "mcp__features__feature_mark_failing",
    "mcp__features__feature_skip",
    "mcp__features__feature_split",
    # ... 10 tools total
]

TESTING_AGENT_TOOLS = [
    "mcp__features__feature_get_stats",
    "mcp__features__feature_get_by_id",
    "mcp__features__feature_mark_passing",
    "mcp__features__feature_mark_failing",
    # ... 5 tools total — LESS than coding agent
]

# SaaS MODE (future) - same scoping, different delivery:
AGENT_TOOL_PROFILES = {
    "coding": {
        "tools": [claim_tool, mark_passing_tool, mark_failing_tool, skip_tool, split_tool],
        "max_turns": 150,
        "model": "claude-sonnet-4-6",
    },
    "testing": {
        "tools": [get_stats_tool, get_by_id_tool, mark_passing_tool, mark_failing_tool],
        "max_turns": 75,
        "model": "claude-sonnet-4-6",
    },
    "architect": {
        "tools": [],  # No feature tools — just reads and writes files
        "max_turns": 100,
        "model": "claude-opus-4-6",
    },
}
```

### The Agent Rules → System Prompts Pipeline

Your `.claude/agents/coder.md` is 200+ lines of carefully tuned instructions:
- "You are an elite software architect and principal engineer"
- Mandatory research phase before writing any code
- Pattern matching requirements (find existing conventions first)
- Security consciousness rules
- Git workflow rules

In the CLI, this loads automatically via `setting_sources=["project"]`. In the SaaS
version, this becomes:

```python
# Load the proven agent personality from the same .md file
agent_prompt = Path(".claude/agents/coder.md").read_text()

# Strip the YAML frontmatter, keep the instructions
instructions = extract_instructions(agent_prompt)

# Inject as system prompt in the API call
response = anthropic.messages.create(
    model="claude-sonnet-4-6",
    system=f"{project_claude_md}\n\n{instructions}\n\n{feature_assignment}",
    tools=AGENT_TOOL_PROFILES["coding"]["tools"],
    messages=conversation,
)
```

**The .md files ARE the system prompts.** You're already writing them. The CLI just
happens to load them from disk; the API version loads them from a database.

### The Communication Mesh

In CLI mode, agents communicate through **files and the database**:

```
Agent A (Coding)                    Agent B (Testing)
    │                                   │
    ├─ writes code to filesystem        │
    ├─ calls feature_mark_passing ──────┤──► reads feature status
    ├─ git commits ─────────────────────┤──► reads git log/diff
    │                                   ├─ runs tests against the code
    │                                   ├─ calls feature_mark_failing ──► Agent C picks up
    │                                   │
    │   ARCHITECTURE.md ◄───────────────┤──► both agents read this
    │   CLAUDE.md ◄─────────────────────┤──► both agents read this
    │   .autoforge/style_guide.md ◄─────┤──► both agents read this
```

In the SaaS version, the same communication paths exist, just routed differently:

```
Agent A (Coding)                    Agent B (Testing)
    │                                   │
    ├─ writes code via API sandbox      │
    ├─ POST /api/features/1/passing ────┤──► GET /api/features/1
    ├─ git commits in sandbox ──────────┤──► reads via API
    │                                   ├─ runs tests in sandbox
    │                                   ├─ POST /api/features/1/failing ──► Agent C picks up
    │                                   │
    │   architecture (from DB) ◄────────┤──► injected into system prompt
    │   project rules (from DB) ◄───────┤──► injected into system prompt
    │   style guide (from DB) ◄─────────┤──► injected into system prompt
```

**Same mesh. Same formulas. Different transport layer.**

### The PreCompact → Token Management Pipeline

The `pre_compact_hook` in `client.py` is perhaps the most valuable formula to extract.
It tells the CLI exactly what to preserve and discard during context compaction:

```
PRESERVE:                           DISCARD:
- Feature ID and status             - Screenshot base64 data
- Modified file list                - Long grep output
- Test results (pass/fail)          - Repeated file reads
- Architectural decisions           - Verbose npm install output
- Git operations performed          - Passing lint output
- MCP tool results                  - Browser console dumps
```

In the SaaS version, you implement this as **manual message pruning** since there's
no CLI compaction — you manage the message array yourself:

```python
def manage_context(messages: list, max_tokens: int) -> list:
    """Apply the same preserve/discard rules from pre_compact_hook."""
    if count_tokens(messages) < max_tokens * 0.8:
        return messages  # Under budget, keep everything

    pruned = []
    for msg in messages:
        if is_screenshot(msg):
            pruned.append(summarize_screenshot(msg))  # "Took screenshot of login page"
        elif is_verbose_output(msg):
            pruned.append(summarize_output(msg))  # "Lint passed with 0 errors"
        elif is_repeated_read(msg, pruned):
            continue  # Skip duplicate file reads
        else:
            pruned.append(msg)  # Keep everything else

    return pruned
```

### Why This Matters for the Swarm

The 25-agent swarm architecture described in this document works in BOTH modes:

**CLI mode (now):** Each agent is a `claude` CLI subprocess with hooks, rules,
tool scoping, and MCP servers configured via `ClaudeSDKClient`. The orchestrator
spawns processes and communicates via stdout + SQLite.

**SaaS mode (future):** Each agent is an API loop with system prompts (from the
same .md files), tool arrays (same scoping), middleware (same hook logic), and
REST endpoints (same database operations). The orchestrator spawns async tasks
and communicates via API + PostgreSQL.

The agent count, model tiers, phase pipeline, and communication patterns stay
**identical**. Only the plumbing changes.

```
CLI (R&D Lab)                    SaaS (Production Factory)
─────────────────                ─────────────────────────
subprocess.Popen          →      asyncio.create_task
ClaudeSDKClient           →      anthropic.AsyncAnthropic
hooks dict                →      middleware classes
.claude/agents/*.md       →      system_prompt from DB
MCP server (stdio)        →      REST API endpoints
SQLite + WAL mode         →      PostgreSQL + row locking
filesystem sandbox        →      container/VM sandbox
setting_sources           →      project config table
max_turns                 →      turn counter in loop
```

The CLI is the R&D lab where you perfect the recipe. The API is the factory
where you scale it. **Every hook you tune today becomes a middleware rule
tomorrow. Every agent .md you write today becomes a system prompt tomorrow.
Nothing is wasted.**

---

## Summary: The Optimal 25-Agent Swarm

```
PREP COOKS (Haiku, ~$0.01 each):
  1. Spec Analyzer
  2. Codebase Scout
  3. Style Extractor
  4. Feature Validator
  5. Lint Watcher (continuous)
  6. Static Analysis
  7. Type Coherence Checker
  8. Test Coverage Analyzer
  9. Performance Baseline
  10. Doc Generator

SOUS CHEFS (Sonnet, ~$0.30-0.50 each):
  11-15. Coding Agents (x5 parallel)
  16. Integration Specialist
  17-18. Testing Agents (x2)
  19. Code Reviewer
  20. QA Agent
  21. README/Onboarding Agent

HEAD CHEFS (Opus, ~$2.70-3.75 each):
  22. Architecture Planner
  23. Feature Decomposer/Initializer
  24. Foundation Agent (Feature #1)
  25. Complex Feature Specialist (features with 3+ deps)
```

**Total cost for a 20-feature app: ~$23** (vs. ~$130 with all-Opus)
**Total time: ~45-90 minutes** (vs. 4-6 hours sequential)
**Quality: Higher** (because upstream prevention > downstream detection)
