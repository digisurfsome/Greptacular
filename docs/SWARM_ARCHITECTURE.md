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

## The Definitive Agent Lineups: 12 Configurations for 12 Use Cases

The swarm isn't one fixed roster. It's a **configurable team** that reshapes itself
depending on the job. A clean room reverse engineering job needs forensic analysts
and standards architects. A spaghetti code rescue needs pattern detectives and
refactoring specialists. A boilerplate factory needs template designers and
parameterization experts.

Below is the perfect lineup for each use case — the exact org chart, agent roles,
model tiers, sequencing, and cost. This is what I'd build if I were designing
each configuration as a `.claude/agents/` file with full CLI tooling.

---

### THE MANAGEMENT HIERARCHY (Universal Across All Configurations)

Every configuration shares the same management spine. What changes is who reports
to whom and how many workers each manager controls.

```
                    ┌──────────────────┐
                    │   ORCHESTRATOR   │  (Python process, not an LLM)
                    │   Spawns agents  │  Routes work, manages lifecycle
                    │   Tracks state   │  Reads features.db, emits WebSocket
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼──────┐ ┌────▼────────┐ ┌──▼───────────┐
     │ PLANNING LANE │ │ CODING LANE │ │ QUALITY LANE │
     │               │ │             │ │              │
     │ Architect     │ │ Coders x5   │ │ Testers x2   │
     │ Initializer   │ │ Foundation  │ │ Reviewer      │
     │ Scout         │ │ Integration │ │ QA Agent      │
     │ Analyzer      │ │             │ │ Lint Watcher  │
     │ Style Extract │ │             │ │ Security Scan │
     └───────────────┘ └─────────────┘ └──────────────┘
```

**The three lanes run concurrently** (with sequencing within each lane):
- **Planning Lane** runs first (Phase 0-1), produces artifacts that feed the other lanes
- **Coding Lane** consumes planning artifacts, produces code
- **Quality Lane** runs alongside coding, catches problems in near-real-time

---

### CONFIGURATION 1: Greenfield Feature Build (The Default)

**Use case:** "I have an app idea. Build it from scratch."
**This is the current AutoForge pipeline, optimized.**

```
PLANNING LANE (sequential):                   COST
  [Haiku]  Spec Analyzer ─────────────────── $0.01
  [Haiku]  Style Extractor ───────────────── $0.01
  [Opus]   Architecture Planner ──────────── $2.70
  [Opus]   Feature Decomposer ────────────── $3.75
  [Haiku]  Feature Validator ─────────────── $0.01

CODING LANE (parallel, after planning):
  [Opus]   Foundation Agent (Feature #1) ─── $3.38
  [Sonnet] Coder #1 ─────────── (x4 features) $1.64
  [Sonnet] Coder #2 ─────────── (x4 features) $1.64
  [Sonnet] Coder #3 ─────────── (x4 features) $1.64
  [Sonnet] Coder #4 ─────────── (x4 features) $1.64
  [Sonnet] Coder #5 ─────────── (x3 features) $1.23
  [Sonnet] Integration Specialist ─────────── $0.90

QUALITY LANE (concurrent with coding):
  [Haiku]  Lint Watcher (continuous) ──────── $0.02
  [Haiku]  Static Analysis (on commit) ────── $0.04
  [Haiku]  Type Coherence (every N done) ──── $0.03
  [Sonnet] Tester #1 (regression batches) ── $1.20
  [Sonnet] Tester #2 (regression batches) ── $1.20
  [Sonnet] Code Reviewer (batch review) ──── $1.08
  [Sonnet] QA Agent (final sweep) ─────────── $0.41

POLISH LANE (after all pass):
  [Haiku]  Doc Generator ─────────────────── $0.02
  [Sonnet] README Agent ──────────────────── $0.18
  [Haiku]  Coverage Analyzer ─────────────── $0.01
  [Haiku]  Performance Baseline ──────────── $0.01
                                        ─────────
                                 TOTAL: ~$23.00
                                  TIME: ~60-90 min
                                AGENTS: 25
```

---

### CONFIGURATION 2: Clean Room Reverse Engineering

**Use case:** "I have a competitor's product (or a legacy app). I need to understand
exactly what it does and rebuild it from scratch with clean code and proper standards.
No tainted code — clean room."

**The key constraint:** The analysis team NEVER shares raw code with the build team.
They share SPECIFICATIONS only. This is the legal firewall.

```
═══════════════════════════════════════════════════════════════
  ANALYSIS TEAM (reads the original)     FIREWALL     BUILD TEAM (never sees original)
═══════════════════════════════════════════════════════════════

PHASE 0: Forensic Analysis                    │
                                               │
  [Opus]   Behavior Analyst ──────────────── $3.75  │
  │  Reads the original app/codebase              │
  │  Documents WHAT it does (not HOW)             │
  │  Maps every user flow, screen, feature        │
  │  Output: behavior-spec.md (functional only)   │
  │                                                │
  [Sonnet] API Reverse Engineer ──────────── $0.41  │
  │  Maps all API endpoints, request/response     │
  │  Documents data models (from observation)     │
  │  Output: api-spec.md                          │
  │                                                │
  [Sonnet] UI/UX Documenter ─────────────── $0.41  │
  │  Screenshots every screen, documents layout   │
  │  Maps navigation flows, component inventory   │
  │  Output: ui-spec.md (descriptions, not code)  │
  │                                                │
  [Haiku]  Data Model Extractor ──────────── $0.01  │
  │  Infers database schema from UI + API         │
  │  Documents entities, relationships, constraints│
  │  Output: data-model-spec.md                   │
  │                                                │
  [Haiku]  Business Rules Extractor ──────── $0.01  │
  │  Documents validation rules, calculations     │
  │  Maps permissions, access control patterns    │
  │  Output: business-rules-spec.md               │
                                               │
  ════════════ CLEAN ROOM WALL ════════════   │  SPECIFICATIONS ONLY CROSS THIS LINE
                                               │  (no source code, no implementation)
PHASE 1: Clean Architecture                   │
                                               │
  [Opus]   Clean Room Architect ──────────── $2.70
  │  Reads ONLY the specs from Phase 0
  │  Designs fresh architecture from scratch
  │  Chooses modern stack, patterns, conventions
  │  Output: ARCHITECTURE.md + tech decisions
  │
  [Opus]   Feature Decomposer ────────────── $3.75
  │  Creates features from behavior-spec.md
  │  Maps to clean architecture (not original)
  │  Output: features.db with dependencies

PHASE 2: Clean Implementation
  (Same as Config 1 Coding Lane)
  [Opus]   Foundation Agent ──────────────── $3.38
  [Sonnet] Coders x5 ────────────────────── $8.10
  [Sonnet] Integration Specialist ─────────── $0.90

PHASE 3: Verification Against Spec
  [Sonnet] Behavior Verifier ─────────────── $0.41
  │  Checks rebuilt app against behavior-spec
  │  Does the new version DO everything the old one did?
  │  Does NOT compare code, only behavior
  │
  [Sonnet] Testers x2 ───────────────────── $2.40
  [Sonnet] Reviewer ──────────────────────── $1.08
  [Sonnet] QA Agent ──────────────────────── $0.41

QUALITY WATCHERS (continuous):
  [Haiku]  Lint + Type + Security ─────────── $0.09
                                          ──────────
                                   TOTAL: ~$28.00
                                    TIME: ~2-3 hours
                                  AGENTS: 22
                              UNIQUE ROLES: 7 new agents
```

**The 7 NEW agent roles for clean room:**
1. **Behavior Analyst** (Opus) — The forensic expert. Documents what, never how.
2. **API Reverse Engineer** (Sonnet) — Maps the interface contract.
3. **UI/UX Documenter** (Sonnet) — Visual inventory without code access.
4. **Data Model Extractor** (Haiku) — Infers schema from observations.
5. **Business Rules Extractor** (Haiku) — Documents the "why" behind behaviors.
6. **Clean Room Architect** (Opus) — Designs from spec only, no original influence.
7. **Behavior Verifier** (Sonnet) — Validates functional parity without code comparison.

**CLI agent files this creates:**
```
.claude/agents/
  behavior-analyst.md       # "You analyze software behavior. You NEVER output code."
  api-reverse-engineer.md   # "You document API contracts from observation."
  ui-documenter.md          # "You describe what users see, not how it's built."
  clean-room-architect.md   # "You design from specifications. You have NEVER seen the original."
  behavior-verifier.md      # "You verify functional parity. You compare behaviors, not code."
```

---

### CONFIGURATION 3: Spaghetti Code Rescue

**Use case:** "Someone vibe-coded this app. It works but it's a disaster. No tests,
no types, inconsistent patterns, 47 different ways to fetch data. I want to keep the
features but rebuild it properly."

**The key insight:** You can't refactor spaghetti in place. You need to understand it
first, extract the INTENT, then rebuild with standards. This is archaeology, not renovation.

```
PHASE 0: Archaeology (Understand the Mess)

  [Opus]   Code Archaeologist ────────────── $3.75
  │  Reads EVERY file. Maps the actual architecture (not intended).
  │  Identifies: duplicate utilities, conflicting patterns, dead code,
  │    circular dependencies, god objects, prop drilling chains
  │  Creates a "state of the disaster" report
  │  Output: .autoforge/archaeology-report.md
  │  THIS IS THE MOST IMPORTANT AGENT — it sees the truth
  │
  [Sonnet] Pattern Detective ─────────────── $0.41
  │  Catalogs every coding pattern used in the codebase
  │  Groups them: "there are 4 ways data fetching is done"
  │  Identifies which pattern is BEST and which are accidental
  │  Output: .autoforge/pattern-inventory.md
  │
  [Haiku]  Dependency Mapper ─────────────── $0.01
  │  Runs static analysis: import graph, dependency tree
  │  Identifies circular imports, unused deps, version conflicts
  │  Output: .autoforge/dependency-map.md
  │
  [Haiku]  Dead Code Detector ────────────── $0.01
  │  Finds unreachable code, unused exports, orphaned files
  │  Estimates how much can be deleted safely
  │  Output: .autoforge/dead-code-report.md
  │
  [Sonnet] Feature Extractor ─────────────── $0.41
  │  Reads the working app and reverse-engineers the feature list
  │  "What does this app actually DO from a user's perspective?"
  │  Maps features to files (which files implement which feature)
  │  Output: features extracted into features.db

PHASE 1: Standards Definition

  [Opus]   Standards Architect ───────────── $2.70
  │  Reads archaeology report + pattern inventory
  │  Defines THE standard: one way to do each thing
  │  Writes: coding standards, file organization, naming conventions,
  │    data fetching pattern, state management pattern, error handling
  │  Output: ARCHITECTURE.md + CODING_STANDARDS.md
  │  This is the "law" — every subsequent agent follows this
  │
  [Haiku]  Migration Planner ─────────────── $0.01
  │  Creates the refactoring dependency graph
  │  "Shared utilities must be standardized BEFORE components that use them"
  │  "Auth must be refactored BEFORE pages that depend on auth"
  │  Output: migration ordering in features.db

PHASE 2: Incremental Rebuild (NOT a full rewrite)

  [Opus]   Foundation Refactorer ──────────── $3.38
  │  Refactors the SHARED INFRASTRUCTURE first:
  │    - API client (one pattern)
  │    - Auth system (one pattern)
  │    - State management (one pattern)
  │    - Shared types/interfaces
  │  Everything downstream depends on this being right
  │
  [Sonnet] Refactorer #1-5 (x5 parallel) ── $8.10
  │  Each takes a feature (or feature group) and refactors it
  │  Reads: CODING_STANDARDS.md + ARCHITECTURE.md
  │  Replaces spaghetti with standardized patterns
  │  Preserves behavior while changing structure
  │  MUST maintain feature parity (regression tests run after each)
  │
  [Sonnet] Test Writer ───────────────────── $0.41
  │  Writes tests BEFORE refactoring (if none exist)
  │  These tests verify the CURRENT behavior
  │  Refactoring agents run these tests to prove they didn't break anything
  │  Output: test files for each feature

PHASE 3: Verification

  [Sonnet] Regression Testers x2 ─────────── $2.40
  │  Run the full test suite after each refactoring batch
  │  Catches behavioral regressions immediately
  │
  [Sonnet] Standards Compliance Checker ──── $0.41
  │  After all refactoring: does the codebase follow the standards?
  │  Catches agents who "fell back" to old patterns
  │  Reports: "File X still uses the old data fetching pattern"
  │
  [Sonnet] Code Reviewer ────────────────── $1.08
  [Sonnet] QA Agent ─────────────────────── $0.41

QUALITY WATCHERS (continuous):
  [Haiku]  Lint + Type + Dead Code ────────── $0.09
                                          ──────────
                                   TOTAL: ~$24.00
                                    TIME: ~2-4 hours
                                  AGENTS: 21
                              UNIQUE ROLES: 7 new agents
```

**The 7 NEW agent roles for spaghetti rescue:**
1. **Code Archaeologist** (Opus) — Sees the truth of the codebase without judgment.
2. **Pattern Detective** (Sonnet) — Catalogs every pattern, picks the winner.
3. **Dead Code Detector** (Haiku) — Identifies what can be deleted safely.
4. **Feature Extractor** (Sonnet) — Reverse-engineers "what does this DO?"
5. **Standards Architect** (Opus) — Writes the law that all refactoring follows.
6. **Migration Planner** (Haiku) — Orders the refactoring for safety.
7. **Standards Compliance Checker** (Sonnet) — Enforces the new standards post-refactoring.

---

### CONFIGURATION 4: Boilerplate Factory

**Use case:** "I want to create reusable project templates — SaaS starter, e-commerce
skeleton, blog platform, dashboard app — that anyone can spin up and customize."

**The key insight:** A boilerplate isn't a finished app. It's a **parameterized skeleton**
with clear extension points. The agents need to think about customizability, not just code.

```
PHASE 0: Template Design

  [Opus]   Template Architect ────────────── $2.70
  │  Designs the boilerplate structure:
  │    - What's included vs what's left for the user
  │    - Extension points (where users add their code)
  │    - Configuration surface (what's customizable)
  │    - File organization that scales
  │  Output: TEMPLATE_ARCHITECTURE.md
  │
  [Sonnet] Stack Selector ───────────────── $0.41
  │  For each boilerplate type, selects optimal tech stack
  │  Documents WHY each choice (React vs Vue, Prisma vs Drizzle, etc.)
  │  Ensures dependencies are stable, maintained, well-documented
  │  Output: STACK_DECISIONS.md
  │
  [Haiku]  Convention Documenter ─────────── $0.01
  │  Writes the conventions the template follows
  │  This becomes the CLAUDE.md for projects spun up from this template
  │  Output: template CLAUDE.md, CONTRIBUTING.md

PHASE 1: Skeleton Implementation

  [Opus]   Foundation Builder ────────────── $3.38
  │  Builds the core skeleton:
  │    - Auth system (configurable: email, OAuth, magic link)
  │    - Database layer (configurable: Postgres, SQLite, etc.)
  │    - API framework (configurable: REST, GraphQL, tRPC)
  │    - Frontend shell (configurable: theme, layout)
  │
  [Sonnet] Feature Module Builder x3 ────── $1.23
  │  Each builds one "optional module" for the template:
  │    - Payments module (Stripe integration)
  │    - Email module (transactional emails)
  │    - File upload module (S3/local)
  │    - Admin panel module
  │  These are DROP-IN modules users can enable/disable
  │
  [Sonnet] Config System Builder ─────────── $0.41
  │  Builds the template configuration system:
  │    - CLI scaffolder ("create-my-app" style)
  │    - Config file (template.config.ts)
  │    - Feature flags for optional modules
  │    - Environment variable templates

PHASE 2: Documentation & DX

  [Sonnet] DX Agent ──────────────────────── $0.41
  │  Developer experience specialist:
  │    - "Getting started in 5 minutes" guide
  │    - Interactive CLI walkthrough
  │    - VS Code settings, recommended extensions
  │    - Hot reload, debug configurations
  │
  [Sonnet] README & Marketing ────────────── $0.41
  │  Creates the public-facing template page:
  │    - Feature comparison table
  │    - Architecture diagram (mermaid)
  │    - Screenshot placeholders with descriptions
  │    - "Why this template" positioning
  │
  [Haiku]  Example App Builder ───────────── $0.01
  │  Generates a small example app using the template
  │  Proves the template actually works end-to-end

PHASE 3: Quality

  [Sonnet] Template Tester ───────────────── $0.41
  │  Spins up the template with every configuration combination
  │  Verifies each combination builds, lints, passes tests
  │
  [Haiku]  Lint + Type Watcher ───────────── $0.02
  [Sonnet] Code Reviewer ────────────────── $1.08
                                          ──────────
                                   TOTAL: ~$10.50
                                    TIME: ~30-60 min
                                  AGENTS: 14
                              UNIQUE ROLES: 6 new agents
```

---

### CONFIGURATION 5: Code Migration (JS→TS, Class→Hooks, Python 2→3, etc.)

**Use case:** "Migrate my entire codebase from X to Y without breaking anything."

```
PHASE 0: Migration Analysis

  [Opus]   Migration Strategist ──────────── $2.70
  │  Analyzes the full codebase, designs migration strategy
  │  Decides: big bang vs incremental, what order, what coexistence
  │  Identifies high-risk files (complex logic, many dependents)
  │  Output: MIGRATION_PLAN.md with phases
  │
  [Haiku]  Compatibility Scanner ─────────── $0.01
  │  Scans for migration blockers:
  │    - Deprecated APIs, incompatible patterns
  │    - Third-party dependencies that need updating
  │    - Build system changes needed
  │  Output: compatibility-report.md
  │
  [Sonnet] Test Baseline Agent ───────────── $0.41
  │  Runs existing tests and records baseline results
  │  If no tests: generates minimal regression tests first
  │  These tests MUST pass after every migration step

PHASE 1: Infrastructure Migration

  [Opus]   Config Migrator ───────────────── $3.38
  │  Migrates build tooling, configs, package.json, tsconfig, etc.
  │  Everything downstream depends on the build system working
  │
  [Sonnet] Type Definition Agent ─────────── $0.41
  │  (For JS→TS) Generates type definitions for all modules
  │  (For other migrations) Generates the "bridge" layer

PHASE 2: Incremental File Migration

  [Sonnet] Migrator #1-5 (x5 parallel) ──── $8.10
  │  Each migrates files according to the plan
  │  Follows strict ordering (utilities → components → pages)
  │  Runs tests after each file to catch regressions

PHASE 3: Verification

  [Sonnet] Migration Verifier ────────────── $0.41
  │  Full sweep: are there ANY remaining un-migrated files?
  │  Checks for leftover compatibility shims, TODOs, any/unknown types
  │
  [Haiku]  Lint + Type Watcher ───────────── $0.02
  [Sonnet] Testers x2 ───────────────────── $2.40
  [Sonnet] Reviewer ──────────────────────── $1.08
                                          ──────────
                                   TOTAL: ~$19.00
                                    TIME: ~1-3 hours
                                  AGENTS: 16
```

---

### CONFIGURATION 6: Security Audit & Hardening

**Use case:** "Audit my codebase for security vulnerabilities and fix them."

```
PHASE 0: Threat Assessment

  [Opus]   Threat Modeler ───────────────── $2.70
  │  Analyzes attack surface: auth, input handling, data flow
  │  Creates STRIDE threat model for the application
  │  Identifies crown jewels (what's most valuable to protect)
  │  Output: THREAT_MODEL.md
  │
  [Sonnet] OWASP Scanner ───────────────── $0.41
  │  Systematic check against OWASP Top 10:
  │    - Injection (SQL, XSS, command)
  │    - Broken auth/session management
  │    - Sensitive data exposure
  │    - Security misconfiguration
  │  Output: owasp-findings.md with severity ratings
  │
  [Haiku]  Dependency Auditor ──────────── $0.01
  │  Runs npm audit, pip-audit, cargo audit
  │  Checks for known CVEs in dependencies
  │  Output: dependency-vulnerabilities.md
  │
  [Haiku]  Secrets Scanner ────────────── $0.01
  │  Scans for hardcoded secrets, API keys, tokens
  │  Checks .env handling, git history for leaked secrets
  │  Output: secrets-report.md

PHASE 1: Prioritized Fixes

  [Opus]   Security Architect ──────────── $3.38
  │  Designs fixes for CRITICAL and HIGH findings
  │  Architectural changes: input sanitization layer,
  │    CSRF protection, rate limiting, auth hardening
  │
  [Sonnet] Fix Agent #1-3 (x3 parallel) ── $1.23
  │  Each takes a batch of findings and implements fixes
  │  Follows security architect's design
  │
  [Sonnet] Penetration Tester ──────────── $0.41
  │  Writes and runs attack scenarios against the fixes
  │  Verifies fixes actually prevent the vulnerability

PHASE 2: Verification

  [Sonnet] Security Reviewer ──────────── $0.41
  │  Reviews all fixes for correctness and completeness
  │  Checks for fix-induced regressions
  │
  [Haiku]  Compliance Checker ─────────── $0.01
  │  Generates compliance report (OWASP, SOC2 relevant controls)
                                          ──────────
                                   TOTAL: ~$8.60
                                    TIME: ~1-2 hours
                                  AGENTS: 12
```

---

### CONFIGURATION 7: Test Suite Builder

**Use case:** "My app has zero tests. Build comprehensive test coverage from scratch."

```
  [Opus]   Test Strategist ──────────────── $2.70
  │  Analyzes codebase, designs test strategy:
  │    - What to unit test, integration test, e2e test
  │    - Test priorities (critical paths first)
  │    - Test infrastructure setup (Jest, Playwright, etc.)
  │
  [Haiku]  Test Infrastructure Agent ─────── $0.01
  │  Sets up test framework, config files, CI integration
  │
  [Sonnet] Unit Test Writer x3 ──────────── $1.23
  │  Each writes unit tests for assigned modules
  │  Focus: pure functions, utilities, data transformations
  │
  [Sonnet] Integration Test Writer ──────── $0.41
  │  Writes API integration tests, database tests
  │  Focus: module boundaries, API contracts
  │
  [Sonnet] E2E Test Writer ─────────────── $0.41
  │  Writes Playwright end-to-end tests
  │  Focus: critical user flows (signup, checkout, etc.)
  │
  [Haiku]  Coverage Analyzer ───────────── $0.01
  │  Runs coverage report, identifies gaps
  │  Feeds gaps back to test writers for second pass
  │
  [Sonnet] Test Reviewer ──────────────── $0.41
  │  Reviews test quality: are tests actually testing the right things?
  │  Catches: tests that always pass, snapshot tests of irrelevant data
                                          ──────────
                                   TOTAL: ~$5.20
                                    TIME: ~30-60 min
                                  AGENTS: 10
```

---

### CONFIGURATION 8: Performance Optimization

**Use case:** "My app is slow. Find the bottlenecks and fix them."

```
  [Opus]   Performance Analyst ──────────── $2.70
  │  Profiles the full application:
  │    - Lighthouse audit (FCP, LCP, CLS, TTI)
  │    - Bundle analysis (what's making it big)
  │    - N+1 query detection (database)
  │    - Memory leak patterns (React re-renders)
  │  Creates prioritized fix list by IMPACT
  │
  [Sonnet] Bundle Optimizer ─────────────── $0.41
  │  Code splitting, lazy loading, tree shaking
  │  Dynamic imports for heavy dependencies
  │
  [Sonnet] Query Optimizer ──────────────── $0.41
  │  Fixes N+1 queries, adds proper indexing
  │  Implements caching (Redis, in-memory, HTTP)
  │
  [Sonnet] Render Optimizer ─────────────── $0.41
  │  React: useMemo, useCallback, virtualization
  │  Eliminates unnecessary re-renders
  │  Implements proper suspense boundaries
  │
  [Haiku]  Asset Optimizer ──────────────── $0.01
  │  Image optimization, font subsetting, CDN config
  │  Static asset compression settings
  │
  [Sonnet] Benchmark Agent ─────────────── $0.41
  │  Runs before/after benchmarks for every fix
  │  Generates performance comparison report
                                          ──────────
                                   TOTAL: ~$4.40
                                    TIME: ~30-45 min
                                  AGENTS: 6
```

---

### CONFIGURATION 9: API Design & Implementation

**Use case:** "Design and build a production-quality API from a description."

```
  [Opus]   API Architect ────────────────── $2.70
  │  Designs: endpoints, auth, pagination, error handling
  │  Writes OpenAPI spec BEFORE any implementation
  │  Defines: rate limiting, versioning strategy, CORS
  │
  [Haiku]  Schema Generator ─────────────── $0.01
  │  Generates database models from API spec
  │  Creates migration files
  │
  [Sonnet] Endpoint Builder x3 ──────────── $1.23
  │  Each builds a group of endpoints following the spec
  │
  [Sonnet] Auth Builder ─────────────────── $0.41
  │  Implements auth: JWT, API keys, OAuth
  │  Rate limiting, CORS, security headers
  │
  [Sonnet] API Test Writer ─────────────── $0.41
  │  Generates integration tests for every endpoint
  │  Tests: happy path, validation, auth, error cases
  │
  [Haiku]  API Doc Generator ───────────── $0.01
  │  Generates Swagger UI, Postman collection
  │  Writes usage examples for each endpoint
  │
  [Sonnet] API Reviewer ────────────────── $0.41
  │  Reviews for: consistency, REST conventions, security
                                          ──────────
                                   TOTAL: ~$5.20
                                    TIME: ~30-60 min
                                  AGENTS: 10
```

---

### CONFIGURATION 10: Design System Builder

**Use case:** "Create a reusable component library / design system."

```
  [Opus]   Design System Architect ──────── $2.70
  │  Defines: token system, component API patterns,
  │    composition model, theming approach
  │  Output: DESIGN_SYSTEM.md with every decision
  │
  [Sonnet] Token Builder ────────────────── $0.41
  │  Implements: colors, spacing, typography, shadows
  │  CSS variables, Tailwind config, theme provider
  │
  [Sonnet] Primitive Builder ────────────── $0.41
  │  Builds atomic components: Button, Input, Badge, etc.
  │  Full prop API, variants, sizes, states
  │
  [Sonnet] Composite Builder ────────────── $0.41
  │  Builds complex components: DataTable, Modal, Form, etc.
  │  Uses primitives, demonstrates composition
  │
  [Sonnet] Documentation Agent ──────────── $0.41
  │  Storybook stories for every component
  │  Interactive prop playground, usage examples
  │
  [Haiku]  Accessibility Auditor ────────── $0.01
  │  ARIA attributes, keyboard navigation, contrast ratios
  │  Screen reader testing documentation
  │
  [Sonnet] Reviewer ─────────────────────── $0.41
                                          ──────────
                                   TOTAL: ~$4.80
                                    TIME: ~30-45 min
                                  AGENTS: 7
```

---

### CONFIGURATION 11: Legacy Modernization

**Use case:** "I have a working app on an old stack (jQuery, Angular.js, PHP).
Migrate it to a modern stack while keeping it running the whole time."

```
PHASE 0: Strangler Fig Analysis

  [Opus]   Modernization Strategist ─────── $2.70
  │  Designs the strangler fig pattern:
  │    - Which parts to modernize first (highest ROI)
  │    - How old and new coexist during migration
  │    - Bridge/adapter layer design
  │    - Feature flag strategy for gradual rollout
  │
  [Sonnet] Route Mapper ─────────────────── $0.41
  │  Maps every route/page in the legacy app
  │  Prioritizes by usage and complexity
  │
  [Haiku]  Legacy Dependency Auditor ────── $0.01
  │  Identifies deprecated dependencies
  │  Finds modern replacements for each

PHASE 1: Bridge Layer

  [Opus]   Bridge Builder ───────────────── $3.38
  │  Creates the adapter layer:
  │    - Route-level switching (old vs new per page)
  │    - Shared auth between old and new
  │    - Shared state/data layer
  │    - CSS isolation (old styles don't leak into new)

PHASE 2: Page-by-Page Migration

  [Sonnet] Migrator x5 (parallel) ──────── $8.10
  │  Each migrates one page/feature at a time
  │  Old page still works — new page hidden behind flag
  │  Tests verify feature parity before switchover

PHASE 3: Cleanup

  [Sonnet] Legacy Remover ──────────────── $0.41
  │  After all pages migrated: remove legacy code
  │  Remove bridge layer, feature flags, old dependencies
  │
  [Haiku]  Lint + Type Watcher ─────────── $0.02
  [Sonnet] Testers x2 ─────────────────── $2.40
  [Sonnet] Reviewer ────────────────────── $1.08
                                          ──────────
                                   TOTAL: ~$18.50
                                    TIME: ~2-3 hours
                                  AGENTS: 14
```

---

### CONFIGURATION 12: Documentation & Knowledge Base

**Use case:** "Generate complete documentation for an existing, undocumented codebase."

```
  [Opus]   Documentation Strategist ─────── $2.70
  │  Reads entire codebase, designs doc structure
  │  Identifies: what needs public docs, internal docs, API docs
  │  Creates documentation sitemap
  │
  [Sonnet] API Doc Writer ──────────────── $0.41
  │  OpenAPI spec, endpoint documentation
  │  Request/response examples, error codes
  │
  [Sonnet] Architecture Doc Writer ──────── $0.41
  │  System architecture, data flow diagrams (mermaid)
  │  Component interaction patterns
  │
  [Haiku]  Code Comment Generator ────────── $0.01
  │  Adds JSDoc/docstrings to all exported functions
  │  Type documentation for complex interfaces
  │
  [Sonnet] Tutorial Writer ─────────────── $0.41
  │  Getting started guide, common tasks
  │  Step-by-step walkthroughs for key workflows
  │
  [Haiku]  Diagram Generator ───────────── $0.01
  │  Mermaid diagrams for: ERD, sequence, component tree
  │
  [Sonnet] Doc Reviewer ────────────────── $0.41
  │  Verifies accuracy: do the docs match the code?
  │  Checks for stale information, missing sections
                                          ──────────
                                   TOTAL: ~$4.40
                                    TIME: ~20-30 min
                                  AGENTS: 7
```

---

## Master Comparison: All 12 Configurations

| # | Configuration | Agents | Opus | Sonnet | Haiku | Cost | Time |
|---|---------------|--------|------|--------|-------|------|------|
| 1 | **Greenfield Build** | 25 | 3 | 12 | 10 | ~$23 | 60-90m |
| 2 | **Clean Room RE** | 22 | 3 | 10 | 9 | ~$28 | 2-3h |
| 3 | **Spaghetti Rescue** | 21 | 3 | 10 | 8 | ~$24 | 2-4h |
| 4 | **Boilerplate Factory** | 14 | 2 | 7 | 5 | ~$11 | 30-60m |
| 5 | **Code Migration** | 16 | 2 | 9 | 5 | ~$19 | 1-3h |
| 6 | **Security Audit** | 12 | 2 | 5 | 5 | ~$9 | 1-2h |
| 7 | **Test Suite Builder** | 10 | 1 | 6 | 3 | ~$5 | 30-60m |
| 8 | **Performance Opt** | 6 | 1 | 4 | 1 | ~$4 | 30-45m |
| 9 | **API Design** | 10 | 1 | 5 | 4 | ~$5 | 30-60m |
| 10 | **Design System** | 7 | 1 | 4 | 2 | ~$5 | 30-45m |
| 11 | **Legacy Modernization** | 14 | 2 | 8 | 4 | ~$19 | 2-3h |
| 12 | **Documentation** | 7 | 1 | 4 | 2 | ~$4 | 20-30m |

### The Pattern: Opus Only Where Decisions Propagate

Across ALL 12 configurations, Opus is used for **exactly the same reason**:
making decisions that affect everything downstream. Architecture, strategy,
threat models, migration plans. Never for grunt work.

```
OPUS USAGE ACROSS ALL CONFIGS:
  ✅ Architecture decisions (propagate to every feature)
  ✅ Strategy/planning (propagate to every agent)
  ✅ Foundation code (propagate to every file)
  ✅ Threat modeling (propagate to every security fix)
  ❌ Never for: file-by-file implementation
  ❌ Never for: test writing
  ❌ Never for: documentation generation
  ❌ Never for: linting/scanning/watching
```

### Unique Agent Roles Across All Configurations: 47 Total

```
UNIVERSAL AGENTS (appear in most configs):
  Architect/Planner, Coders x5, Testers x2, Reviewer, QA,
  Lint Watcher, Foundation Agent

FORENSIC AGENTS (configs 2, 3):
  Behavior Analyst, Code Archaeologist, Pattern Detective,
  API Reverse Engineer, UI/UX Documenter, Feature Extractor,
  Dead Code Detector, Business Rules Extractor

STANDARDS AGENTS (configs 3, 5):
  Standards Architect, Standards Compliance Checker,
  Migration Planner, Migration Strategist, Migration Verifier

SECURITY AGENTS (config 6):
  Threat Modeler, OWASP Scanner, Secrets Scanner,
  Penetration Tester, Compliance Checker

TEMPLATE AGENTS (config 4):
  Template Architect, Stack Selector, Config System Builder,
  DX Agent, Example App Builder, Template Tester

OPTIMIZATION AGENTS (config 8):
  Performance Analyst, Bundle Optimizer, Query Optimizer,
  Render Optimizer, Asset Optimizer, Benchmark Agent

DOCUMENTATION AGENTS (config 12):
  Documentation Strategist, API Doc Writer, Architecture Doc Writer,
  Code Comment Generator, Tutorial Writer, Diagram Generator
```

**Each of these becomes a `.claude/agents/*.md` file** in the CLI, or a
**system prompt template in the database** in the SaaS version. The user selects
a configuration, the orchestrator assembles the right team, and the swarm
goes to work.

---

### How This Becomes the Product: Configuration Selection UI

```
┌─────────────────────────────────────────────────────────┐
│  🏗️  What would you like to build?                      │
│                                                         │
│  ┌───────────────┐  ┌───────────────┐  ┌─────────────┐ │
│  │  New App      │  │  Rescue Code  │  │  Migrate     │ │
│  │  from Spec    │  │  from Chaos   │  │  to Modern   │ │
│  │               │  │               │  │  Stack       │ │
│  │  25 agents    │  │  21 agents    │  │  16 agents   │ │
│  │  ~$23, ~1hr   │  │  ~$24, ~3hr   │  │  ~$19, ~2hr  │ │
│  └───────────────┘  └───────────────┘  └─────────────┘ │
│                                                         │
│  ┌───────────────┐  ┌───────────────┐  ┌─────────────┐ │
│  │  Security     │  │  Build Tests  │  │  Make It     │ │
│  │  Audit        │  │  from Scratch │  │  Faster      │ │
│  │               │  │               │  │              │ │
│  │  12 agents    │  │  10 agents    │  │  6 agents    │ │
│  │  ~$9, ~1.5hr  │  │  ~$5, ~45min  │  │  ~$4, ~30min │ │
│  └───────────────┘  └───────────────┘  └─────────────┘ │
│                                                         │
│  ┌───────────────┐  ┌───────────────┐  ┌─────────────┐ │
│  │  Clean Room   │  │  Boilerplate  │  │  Design      │ │
│  │  Reverse Eng  │  │  Factory      │  │  System      │ │
│  │               │  │               │  │              │ │
│  │  22 agents    │  │  14 agents    │  │  7 agents    │ │
│  │  ~$28, ~2.5hr │  │  ~$11, ~45min │  │  ~$5, ~30min │ │
│  └───────────────┘  └───────────────┘  └─────────────┘ │
│                                                         │
│  ┌───────────────┐  ┌───────────────┐  ┌─────────────┐ │
│  │  Build API    │  │  Modernize    │  │  Generate    │ │
│  │  from Spec    │  │  Legacy App   │  │  Full Docs   │ │
│  │               │  │               │  │              │ │
│  │  10 agents    │  │  14 agents    │  │  7 agents    │ │
│  │  ~$5, ~45min  │  │  ~$19, ~2.5hr │  │  ~$4, ~20min │ │
│  └───────────────┘  └───────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**This is the product.** The user picks a card. The swarm assembles.
The agents go to work. The user watches on the kanban board.

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
