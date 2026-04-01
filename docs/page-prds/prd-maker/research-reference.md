# PRD Maker — Research Reference

> **Status:** Research complete. No code built yet. This document captures everything discovered so we can build from it.
>
> **Date:** 2026-04-01

---

## Table of Contents

1. [The Big Objective](#the-big-objective)
2. [The 10-Stage Pipeline](#the-10-stage-pipeline)
3. [Martin's Prompts](#martins-prompts)
4. [The Two Halves of the Puzzle](#the-two-halves-of-the-puzzle)
5. [The Periodic Table of App Mechanisms](#the-periodic-table-of-app-mechanisms)
6. [The 30-Category Master Checklist](#the-30-category-master-checklist)
7. [The Preamble System](#the-preamble-system)
8. [Existing Skills Found (External Repos)](#existing-skills-found-external-repos)
9. [affaan-m/everything-claude-code — Full Inventory](#affaan-m-skills-inventory)
10. [Source Repos and Links](#source-repos-and-links)

---

## The Big Objective

Build a **PRD Maker** — a system that takes a non-coder's messy human description of an app idea and turns it into a complete, buildable technical spec. The PRD Maker is a 10-stage pipeline where each stage becomes a Claude Code skill so it's repeatable, deterministic, and doesn't rely on AI improvising.

---

## The 10-Stage Pipeline

Source: [Vid-Gen-OG docs](https://github.com/digisurfsome/Vid-Gen-OG/tree/main/docs)

### Stage 1: IDEA CAPTURE
- **Input:** Rants, transcripts, notes, stream-of-consciousness
- **Output:** Unprocessed brain dump with all contradictions preserved
- **Rule:** More verbosity is better. Preserve contradictions for Stage 3 resolution.
- **Philosophy:** "You can't analyze what you don't have"

### Stage 2: GAP ANALYSIS
- **Purpose:** Intelligent questioning to identify missing concepts, ambiguity, unstated assumptions
- **Process:** Identifies app archetype → loads standard requirements → compares provided info → generates targeted questions for gaps
- **Output:** Combined raw info + answers, still unstructured
- **THE PROBLEM:** Without a preamble, this stage is too open-ended. Agent tries to figure out EVERYTHING (UI, payments, structure, features) at once. The preamble system (see below) scopes this down to just the IDEA half.

### Stage 3: AGENT OS STRUCTURING
- **Purpose:** Transforms messy raw material into organized concept document
- **Five dimensions:** Product Identity, Problem Statement, Market Viability, Target Users, Competitive Landscape
- **Output format:** 4 sections — Concept & Context, Target User & Market, Feasibility Assessment, Problem Statement
- **Rules:** No mechanism decomposition, no "how" questions (only "what/why"), must resolve ambiguity

### Stage 4: MECHANISM EXTRACTION
- **Purpose:** Breaks structured app into discrete moving parts
- **Three questions:** What are the moving parts? Which have one clear way to build? Which have multiple viable approaches?
- **Tagging:** OBVIOUS (one standard approach) vs NEEDS_EVALUATION (multiple approaches, requires 10-step criteria)
- **15% Threshold Rule:** If two approaches score within 15% performance parity, both get designed and placed in PRD for later branch testing

### Stage 5: 7-QUESTION SCAFFOLDING (THE ENGINE)
- **Purpose:** Classifies every process step as WALL (deterministic code), DOOR (constrained AI), or ROOM (creative freedom)
- **The 7 Questions per step:**
  1. What action occurs here?
  2. Is there only one way, or can it vary?
  3. What preconditions must exist?
  4. What are ALL possible outcomes?
  5. Where does each outcome lead next?
  6. How do you verify correct execution?
  7. Can this step ever be skipped?
- **Martin's build rules function as the architectural lens during Stage 5**
- **Philosophy:** "This is the engine. Everything before is preparation. Everything after is output formatting."

### Stage 6: LAYOUT + MOCKUPS + STYLE (3 sub-stages)
- **6a: Arrangement Selection** — Identifies app type, presents deterministic wireframe pattern
- **6b: Page Mockups** — Each page layout with component placement and mechanism connections
- **6c: Style Selection** — 3 curated style options matched to app type (not 12 overwhelming choices)

### Stage 7: PHASE SEQUENCING
- **Token Budget Framework:**
  - Total budget: 500,000 tokens (half of 1M context)
  - Fixed overhead per phase: ~25,000 tokens
  - Available per phase: ~325,000 tokens
  - Formula: Total spec tokens / 325,000 = number of phases needed
- **Three-Tier File Sandbox:** ALLOWED (create/modify), READ-ONLY (reference only), FORBIDDEN (alarm system)
- **Mandatory Build Order:** Core logic → state management → UI → integration

### Stage 8: PROTOCOL INJECTION
- **Seven Enforcement Mechanisms:**
  - A: Pulse Checks (file-level verification every 3 files)
  - B: Seam Checks (integration testing at component connection points)
  - C: Full Checkpoints (comprehensive phase-boundary validation)
  - Plus: file sandboxing, build order sequencing, pattern verification, Martin's 1,500-line lens
- **Violation Handling:** LOW → MEDIUM → HIGH → CRITICAL with escalating responses

### Stage 9: VERIFICATION AGENT SETUP
- **Core principle:** Checker is NOT the same agent as builder
- **Two approaches:** Automated (separate Agent B) or Manual (30-second preamble merged into next phase)
- **Uses git diff as ground truth** — self-report → diff check → violation classification → functional verification
- **Two-strike rule:** If two fresh agents fail same phase, the spec has issues

### Stage 10: OUTPUT GENERATOR
- **Deliverables:**
  - `phases/phase-1.md` through `phases/phase-N.md` — copy-paste ready
  - `build.sh` — deterministic bash wrapper with snapshot/rollback
  - `CLAUDE.md` — lightweight guardrails
  - `BUILD_RULES.md` — comprehensive reference playbook
  - `README.md` — build documentation

---

## Martin's Prompts

Source: [Vid-Gen-OG docs](https://github.com/digisurfsome/Vid-Gen-OG/tree/main/docs)

### 1. App Idea Generator (Idea Code)
**File:** `docs/1-MARTINS APP IDEA PROMPT-TEXT FILE.txt`

Structured framework for transforming rough app concepts into clear MVP specs. Outputs two sections:
- **Section 1 (App Identity):** Name, one-sentence description, target user, core problem
- **Section 2 (Features):** Maximum 5 core features in plain-language user actions

Key rules: Maximum 5 features (MVP thinking), excludes technical infrastructure (auth, responsive design), triggers clarifying questions for vague concepts.

### 2. Design System Prompt (Style Guide Generator)
**File:** `docs/2-MARTINS DESIGN SYSTEM PROMPT-TEXT FILE.txt`

Extracts design systems from visual references (screenshots). Analyzes:
1. Color tokens (named by function, not appearance)
2. Typography hierarchy
3. Component patterns (cards, buttons, inputs)
4. Spacing physics
5. Tailwind CSS configuration

Output: Technical Design System Report in Markdown.

### 3. Main Build PRD (1,500-line prompt)
**File:** `docs/3-MARTINS MAIN BUILD PRD-TEXT FILE.txt`

Comprehensive React/Firebase scaffold. Core stack: React 19, TypeScript, Tailwind CSS, Firebase (Google Sign-In), Cloud Firestore, React Context, Lucide React.

**Critical rules:** No alert()/confirm()/prompt(), no inline styles, no external UI libraries, no Docker/backend APIs, no unprotected routes. Six mandatory components: Modal, ConfirmModal, Toast, Skeleton, EmptyState, ThemeToggle.

**This prompt needs meshing with our boilerplates** — Martin wrote it for Firebase but our web boilerplate uses Supabase. See "Preamble System" below.

---

## The Two Halves of the Puzzle

### Structure Half (handled by preamble)
What every app needs regardless of the idea: file structure, naming, components, state management, API patterns, auth, security, styling, testing, anti-patterns. This is what Martin's 1,500 lines cover. This is what the boilerplates implement.

### Mechanism Half (handled by gap analysis)
What THIS specific app does: features, user flows, data transformations, integrations. Varies per app. This is what Stages 2-5 focus on.

**The insight:** Without separating these halves, gap analysis tries to figure out EVERYTHING. With the preamble handling structure, gap analysis only needs to focus on mechanisms.

---

## The Periodic Table of App Mechanisms

14 categories (A-N) covering every type of thing an app can do:

| Cat | Type | Examples |
|-----|------|----------|
| A | Data Input | Forms, file upload, voice, camera, drag-drop |
| B | Data Storage | SQL, NoSQL, blob, cache, search index |
| C | Data Processing | Validation, calculations, AI/ML, batch jobs |
| D | Data Output | Lists, charts, maps, export, real-time feeds |
| E | Authentication | Password, OAuth, SSO, MFA, magic link |
| F | Authorization | RBAC, multi-tenancy, feature flags |
| G | Communication | Email, push, SMS, chat, webhooks |
| H | Integration | REST/GraphQL, scraping, payment gateways |
| I | Workflow | State machines, cron jobs, queues, wizards |
| J | Search & Discovery | Full-text, faceted, autocomplete, recommendations |
| K | Collaboration | Comments, sharing, co-editing, following |
| L | Monetization | Subscriptions, trials, marketplace, invoicing |
| M | Admin/Ops | Admin dashboard, moderation, analytics |
| N | Infrastructure | Caching, CDN, migrations, logging |

**Usage:** When someone describes their app, map their description to these categories. Then gap analysis asks about the categories they missed.

---

## The 30-Category Master Checklist

Synthesized from IEEE 830, FURPS+, Volere, arc42, C4 Model, and 12-Factor App. Defines what a "complete app specification" covers:

1. Problem & Purpose
2. Target Users & Personas
3. Market Context
4. Core Features
5. User Flows
6. Data Model
7. API Design
8. Authentication
9. Authorization
10. Security Requirements
11. Performance Requirements
12. Scalability
13. UI/UX Patterns
14. Responsive Design
15. Accessibility
16. State Management
17. Error Handling
18. Testing Strategy
19. Deployment
20. Monitoring & Logging
21. Third-Party Integrations
22. Monetization
23. Legal/Compliance
24. Internationalization
25. Offline Support
26. Migration/Import
27. Admin/Back-office
28. Analytics
29. Documentation
30. Out of Scope

Gap analysis compares what the user said against these 30 categories and asks about whatever's empty.

---

## The Preamble System

### What It Is
A document that sits BEFORE Stage 1 — the floor the house is built on. Every stage gets the preamble injected at the top so the agent knows what's already covered and what NOT to think about.

### The Meshing Process
Martin's 1,500 lines → structured checklist → each item matched against boilerplate:

| Status | Meaning | Example |
|--------|---------|---------|
| MATCH | Martin says X, boilerplate does X | Both use Tailwind |
| REPLACE | Martin says X, boilerplate does Y | Firebase → Supabase |
| ENHANCE | Martin says "handle X," boilerplate has full X system | Auth → point to exact files |
| HANDLED | Martin says "set up X," boilerplate already has it | Routing → "don't touch" |

### The Five Pre-Built Preambles

| File | Purpose |
|------|---------|
| `martin-raw-checklist.md` | Structured checklist, no boilerplate matched |
| `martin-web-supabase.md` | Matched to Supabase web boilerplate |
| `martin-mobile-flutter.md` | Matched to Flutter mobile boilerplate |
| `martin-dual.md` | Both web + mobile combined |
| `martin-no-boilerplate.md` | Martin's original, agnosticized (generic AI, generic DB) |

### What This Fixes
- **Without preamble:** "Tell me about your app" → agent tries to figure out EVERYTHING → chaos
- **With preamble:** "Structure is handled. Your ONLY job is to figure out what the app DOES — features, mechanisms, user flows."

---

## Existing Skills Found (External Repos)

### Best PRD-Adjacent Skills

| Skill/Repo | What It Does | Why It Matters |
|------------|-------------|----------------|
| **rodrigorjsf/prd-generator-plugin** | 7-block structured interviews, generates PRD + ARCHITECTURE + enforcement guardian skills. Has evolution/delta model. | Most sophisticated PRD generator found |
| **nicknisi/claude-plugins ideation** | 5-phase pipeline with confidence scoring that determines how many questions to ask. Best "messy input" handling. | Closest to our rant-to-spec problem |
| **haberlah/replit-prd-skill** | Has [DO NOT CHANGE] protection clauses in phased prompts | Good pattern for Stage 7 sandbox rules |
| **ChatPRD** | Market leader, 100K+ PMs use it, 10-section template | Industry standard reference |

### Existing Skills We Already Have

| Skill | Relevance |
|-------|-----------|
| `doc-coauthoring` | Handles structured document creation workflow — partial rant-to-spec capability |
| `skill-creator` | Can generate new skills from patterns — useful for building the 10-stage skills |
| `create-spec` | Existing spec creation command with gap analysis — starting point for Stage 2 |

---

## affaan-m Skills Inventory

Source: [affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code)

**Scale:** 36 agents, 68 commands, 142 skills

### THE BIG FIND: PRP (Product Ready Pipeline)

The repo's flagship feature is a **5-command pipeline** that mirrors our 10-stage concept:

| Command | What It Does | Maps to Our Stage |
|---------|-------------|-------------------|
| `/prp-prd` | Interactive 8-phase PRD generator (problem validation → market research → technical assessment → MVP scoping → complete PRD) | Stages 1-3 (Idea Capture → Gap Analysis → Structuring) |
| `/prp-plan` | Converts PRDs into implementation plans with task breakdown, dependencies, validation strategies | Stages 4-5 (Mechanism Extraction → Scaffolding) |
| `/prp-implement` | Executes plans step-by-step with continuous validation; never accumulates broken state | Stages 7-8 (Phase Sequencing → Protocol Injection) |
| `/prp-pr` | Prepares pull requests with structured descriptions and validation checksums | Stage 10 (Output) |
| `/prp-commit` | Ensures commits follow product-ready standards with message validation | Stage 10 (Output) |

**This is the closest existing implementation to what we're building.** The key differences:
- PRP is code-focused (PRD → implementation). Ours is spec-focused (rant → buildable spec).
- PRP doesn't have our preamble system (boilerplate-aware structure half).
- PRP doesn't have our mechanism taxonomy (A-N categories).
- PRP doesn't have the Wall/Door/Room classification (Stage 5 engine).

**Verdict:** Study `/prp-prd` closely before building Stage 1-3. It solves a subset of our problem well.

### Most Relevant — Tier 1 (Directly Useful)

**Planning & Architecture:**
- `planner` agent — Feature implementation planning
- `architect` agent — System design decisions
- `/plan` command — Implementation planning with risk identification
- `/multi-plan` command — Multi-agent task decomposition for complex projects
- `product-lens` skill — Product strategy framework for defining goals/features
- `strategic-compact` skill — Strategic planning methodology
- `architecture-decision-records` skill — Framework for documenting architectural choices

**Pattern Libraries (feeds the preamble system):**
- `backend-patterns` — Core backend architecture concepts
- `frontend-patterns` — React/Vue/Angular structural patterns
- `api-design` — RESTful and GraphQL API design principles
- `design-system` — Component library architecture
- `hexagonal-architecture` — Ports and adapters pattern

**Verification (Stages 8-9):**
- `/verify` command — Verification loop
- `/quality-gate` command — Quality gate checks
- `verification-loop` skill — Continuous verification patterns

**Pipeline Orchestration (multi-stage execution):**
- `loop-operator` agent — Autonomous loop execution
- `/orchestrate` command — Multi-agent coordination
- `autonomous-loops` skill — Continuous feedback mechanisms

### Most Relevant — Tier 2 (Useful Patterns)

**Code Quality:**
- `code-reviewer`, `security-reviewer` agents
- `tdd-guide` agent + `tdd-workflow` skill
- `e2e-testing`, `ai-regression-testing` skills

**Documentation:**
- `doc-updater` agent — Documentation sync
- `content-engine` skill — Content generation pipeline
- `codebase-onboarding` skill — Structured onboarding docs
- `/docs` + `/update-docs` commands

**Knowledge Management:**
- `/skill-create` command — Auto-generates skills from git history
- `/rules-distill` command — Extracts coding rules from repos
- `/instinct-export` + `/instinct-import` — Pattern portability

### Not Relevant (Skip)

- Language-specific reviewers (Go, Python, TS, Java, Kotlin, Rust, C++) — too specialized
- Language-specific build commands (go-build, kotlin-build, etc.)
- Content/marketing skills (article-writing, investor-materials, lead-intelligence)
- Healthcare, security, data integration specializations

### Verdict: What to Take

| Category | Take? | Reason |
|----------|-------|--------|
| **PRP pipeline** (`/prp-prd`, `/prp-plan`) | **YES — PRIORITY** | Closest existing implementation to our pipeline. Study before building. |
| `planner` + `architect` agents | **YES** | Stages 3-4 (structuring and mechanism extraction) |
| `product-lens` + `strategic-compact` | **YES** | Feeds Stage 2 gap analysis with structured frameworks |
| `/plan` + `/multi-plan` commands | **YES** | Pipeline orchestration across stages |
| Pattern libraries (backend/frontend/api/design-system) | **YES** | Feeds the preamble system (structural knowledge) |
| `/verify` + `/quality-gate` | **YES** | Stage 8-9 protocol injection and verification |
| `autonomous-loops` + `loop-operator` + `/orchestrate` | **YES** | Multi-stage pipeline execution |
| `architecture-decision-records` | **YES** | Document choices made during spec generation |
| `/skill-create` + `/rules-distill` | **YES** | Bootstrap our 10 stage skills from patterns |
| `code-reviewer` + `security-reviewer` | **MAYBE** | Stage 9 verification — but we may build our own |
| `tdd-guide` + `tdd-workflow` | **MAYBE** | Pattern, not core to PRD generation |
| `doc-updater` + `content-engine` | **MAYBE** | Keeping generated specs in sync |
| Language-specific anything | **NO** | Too specialized |
| Content/marketing skills | **NO** | Not relevant |

**Bottom line:** ~15 skills/agents/commands are directly useful, with the **PRP pipeline being the single highest-value find**. The `planner`, `architect`, pattern libraries, `/verify`, `/quality-gate`, and `autonomous-loops` round out the top tier.

---

## Source Repos and Links

| Resource | URL | What It Contains |
|----------|-----|-----------------|
| Vid-Gen-OG docs | https://github.com/digisurfsome/Vid-Gen-OG/tree/main/docs | 10-stage pipeline, Martin's prompts, master-source.md |
| affaan-m skills | https://github.com/affaan-m/everything-claude-code | 36 agents, 68 commands, 142 skills |
| rodrigorjsf PRD generator | https://github.com/rodrigorjsf/prd-generator-plugin | 7-block PRD interviews |
| nicknisi ideation | https://github.com/nicknisi/claude-plugins | Confidence-scored ideation pipeline |
| haberlah replit-prd | https://github.com/haberlah/replit-prd-skill | Phased prompts with protection clauses |
| Stage extractions | https://github.com/digisurfsome/Vid-Gen-OG/tree/main/docs/stage-extractions | stage-01 through stage-10 individual docs |
| Martin's Idea Prompt | Vid-Gen-OG/docs/1-MARTINS APP IDEA PROMPT-TEXT FILE.txt | App Idea Generator |
| Martin's Design Prompt | Vid-Gen-OG/docs/2-MARTINS DESIGN SYSTEM PROMPT-TEXT FILE.txt | Style Guide Generator |
| Martin's Build PRD | Vid-Gen-OG/docs/3-MARTINS MAIN BUILD PRD-TEXT FILE.txt | 1,500-line React/Firebase scaffold |

---

## What Happens Next (When We're Ready to Build)

1. **Mesh Martin's prompt** — Structure the 1,500 lines into a checklist, match against boilerplates, produce the 5 preamble files
2. **Build Stage 1 skill** — Rant capture with the nicknisi confidence-scoring pattern
3. **Build Stage 2 skill** — Gap analysis scoped by preamble + mechanism categories
4. **Build Stages 3-10** — One skill per stage, each consuming the previous stage's output
5. **Wire the pipeline** — Orchestration using affaan-m's autonomous-loops pattern
6. **Test end-to-end** — Feed a real app rant through all 10 stages

But that's building. This document is the reference for when we start.
