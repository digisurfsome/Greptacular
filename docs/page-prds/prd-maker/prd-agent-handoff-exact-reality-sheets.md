# Agent Handoff: Build Exact Reality Sheets for All Boilerplates

## Purpose

You are a fresh agent assigned to **ONE specific boilerplate**. Your job is to produce Exact Reality Sheets for that boilerplate's toggle variants. Each sheet maps three source checklists (263 rules + 14 mechanism categories + 43 banned patterns) to the exact, specific implementation for that boilerplate.

**You are NOT building code.** You are producing documentation — structured markdown files that will be injected as preambles into AI agent build sessions.

---

## IMPORTANT: One Agent Per Boilerplate

Each boilerplate type gets its own fresh agent session. This prevents cross-contamination — an agent that just analyzed a Flutter codebase might confuse patterns with a Next.js codebase.

| Agent Session | Boilerplate | Sheets to Produce |
|---------------|-------------|-------------------|
| **Agent A: Web** | DevToDollars (supabase_web) | `supabase_web_db_auth`, `supabase_web_full`, `supabase_web_db_only`, `supabase_web_minimal` |
| **Agent B: Mobile** | ApparenceKit (flutter_mobile) | `flutter_mobile_db_auth`, `flutter_mobile_full`, `flutter_mobile_db_only`, `flutter_mobile_minimal` |
| **Agent C: Dual** | Fullstack (dual) | `dual_db_auth`, `dual_full` |
| **Agent D: AutoForge** | AutoForge Add-On | `autoforge_addon` (web only, no DB/Auth/Payments) |
| **Agent E: No Boilerplate** | None | `no_boilerplate_default` |

**When launching an agent, tell it which boilerplate it's responsible for.** Give it only the repo/docs for that ONE boilerplate.

---

## What You're Building

For your assigned boilerplate, you read its source code and docs, then go through ALL rules across three source checklists and write the **exact implementation** for that stack. Not "use the configured database" — but "use `supabase.from('users').select('*')`."

---

## Input Files (Read These First)

### The Three Source Checklists (Templates)

1. **Martin's Agnostic Checklist** — `docs/page-prds/prd-maker/martin-agnostic-checklist.md`
   - 192 rules, 22 categories, 43 banned patterns
   - Covers: file structure, components, state, auth, styling, data access, routing, bans
   - Rules numbered 1-192

2. **Industry Standards Checklist** — `docs/page-prds/prd-maker/industry-standards-checklist.md`
   - 71 rules, 10 categories
   - Covers: i18n, config externalization, env parity, accessibility (WCAG 2.1 AA), performance budgets, error handling, testing, CI/CD, observability, API design
   - Rules numbered 200-270

3. **Mechanism Categories** — `docs/page-prds/prd-maker/skills/stage-00-technical-foundation/references/mechanism-categories.md`
   - 14 categories (A through N)
   - Coverage matrix: which mechanisms the boilerplate handles vs which need user input

### The PRD (Your Instructions)
- `docs/page-prds/prd-maker/prd-stage-0a-boilerplate-matching.md` — The full PRD describing what Exact Reality Sheets are, the format, and the toggle system. **Read the "Exact Reality Sheet Format" section carefully** — that's the output structure you must follow.

### Boilerplate Sources

#### Web Boilerplate: DevToDollars (`supabase_web`)
- **Repo:** `https://github.com/digisurfsome/Web-BoilerPlate-D2D`
- **Docs:** `https://www.devtodollars.com/docs/`
- **Stack:** Next.js + Supabase + Stripe + Tailwind
- **Clone and read:** Focus on `package.json`, `tsconfig.json`, `src/` directory structure, `supabase/` config, auth patterns, database patterns, Stripe integration, middleware, route guards

#### Mobile Boilerplate: ApparenceKit (`flutter_mobile`)
- **Repo:** `https://github.com/digisurfsome/apparence-kit-supabase`
- **Docs:** `https://apparencekit.dev/docs/start/overview/`
- **Stack:** Flutter + Supabase backend
- **Clone and read:** Focus on `pubspec.yaml`, `lib/` directory structure, auth service, database service, navigation patterns, state management

#### Dual/Fullstack Boilerplate (`dual`)
- **Repo:** `https://github.com/digisurfsome/fullstack-boilerplate`
- **Stack:** Combines web + mobile boilerplates with shared Supabase backend
- **Clone and read:** Focus on how the two frontends share the same backend, any shared types/models, deployment config

---

## Output Files to Produce

Write each sheet to `docs/page-prds/prd-maker/exact-reality-sheets/`:

### Priority 1 (Build These First)

| File | Boilerplate | Toggles | Notes |
|------|------------|---------|-------|
| `supabase_web_db_auth.md` | DevToDollars Web | DB: ON, Auth: ON, Payments: OFF | **Most common build config (80% of use).** Start here. |
| `autoforge_addon.md` | AutoForge Add-On | Fixed — no DB/Auth/Payments | Special variant. Read AutoForge's `CLAUDE.md`, `server/main.py`, `ui/src/App.tsx` to understand the existing patterns this module must follow. |

### Priority 2

| File | Boilerplate | Toggles | Notes |
|------|------------|---------|-------|
| `supabase_web_full.md` | DevToDollars Web | DB: ON, Auth: ON, Payments: ON | Full SaaS build. Includes all Stripe rules. |
| `flutter_mobile_db_auth.md` | ApparenceKit | DB: ON, Auth: ON, Payments: OFF | Flutter + Supabase, no payments. |
| `no_boilerplate_default.md` | None | DB: ON, Auth: ON, Payments: OFF | Default sheet when no boilerplate selected. Uses Supabase defaults but everything marked `NOT_PRESENT` (must implement from scratch). |

### Priority 3

| File | Boilerplate | Toggles | Notes |
|------|------------|---------|-------|
| `supabase_web_db_only.md` | DevToDollars Web | DB: ON, Auth: OFF, Payments: OFF | Data app, no users. |
| `supabase_web_minimal.md` | DevToDollars Web | All OFF | Static/utility app on the scaffold. |
| `flutter_mobile_full.md` | ApparenceKit | DB: ON, Auth: ON, Payments: ON | Flutter full SaaS. |
| `flutter_mobile_db_only.md` | ApparenceKit | DB: ON, Auth: OFF, Payments: OFF | Flutter data app. |
| `flutter_mobile_minimal.md` | ApparenceKit | All OFF | Flutter scaffold only. |
| `dual_full.md` | Fullstack | DB: ON, Auth: ON, Payments: ON | Both platforms, full features. |
| `dual_db_auth.md` | Fullstack | DB: ON, Auth: ON, Payments: OFF | Both platforms, no payments. |

---

## How to Build Each Sheet

### Step 1: Clone and Explore the Boilerplate

For each boilerplate repo, understand:
- **Directory structure** — where components, pages, services, hooks, config live
- **Package dependencies** — what's installed, what versions
- **Auth implementation** — exact function calls, provider config, session handling
- **Database patterns** — how queries are built, CRUD helpers, RLS setup
- **Payment integration** — Stripe setup, webhook handling, subscription logic (if Payments toggle ON)
- **Styling** — Tailwind config, theme tokens, dark mode approach
- **State management** — what's used (Context, Riverpod, etc.)
- **Routing** — how routes are defined, guards, middleware

### Step 2: Walk Through All Three Checklists

**Pass 1: Martin's Structural Rules (192 rules)**
Go through `martin-agnostic-checklist.md` rule by rule (all 22 categories). For each rule, find the matching code in the boilerplate and write the exact implementation.

**Pass 2: Industry Standards (71 rules)**
Go through `industry-standards-checklist.md` rule by rule (all 10 categories). Same process — find how the boilerplate handles i18n, config externalization, env parity, accessibility, performance, error handling, testing, CI/CD, observability, and API design.

**Pass 3: Mechanism Coverage Matrix (14 categories)**
Go through `mechanism-categories.md` category by category (A through N). For each, determine if the boilerplate covers it natively, partially, or not at all. Document what's built-in with specific file paths and function names.

**Pass 4: Banned Patterns (43 patterns)**
Go through the banned patterns section of Martin's checklist. For each banned pattern, write the stack-specific detection method (what to grep for, what imports to reject, etc.).

For each rule across all passes, tag the match type:
- `EXACT` — boilerplate implements this exactly
- `ADAPTED` — principle applies, implementation differs (document how)
- `NOT_PRESENT` — boilerplate doesn't have this; agent builds it from scratch following the rule's guidance
- `NOT_ACTIVATED` — only for toggled-off features; rule is skipped

### Step 3: Handle Toggle Variants

For each boilerplate, you produce multiple sheets (one per toggle combination). The efficient way:

1. **Build the full sheet first** (all toggles ON) — this is the complete mapping
2. **For each variant**, copy the full sheet and mark toggled-off rules as `NOT_ACTIVATED` with a note in the Deactivated Rules section
3. Rules that depend on a toggled-off feature also get deactivated (e.g., if Auth is OFF, route guards are also NOT_ACTIVATED)

### Step 4: Write the Exact Implementation Column

**Good examples (specific, actionable):**

```
Rule: Auth provider sign-in flow
Exact: `await supabase.auth.signInWithOAuth({ provider: 'google', options: { redirectTo: `${window.location.origin}/auth/callback` } })` — configured in `src/lib/supabase.ts`, callback handled by `src/app/auth/callback/route.ts`
```

```
Rule: CRUD helper functions
Exact: Use `src/lib/database.ts` which exports `createRecord(table, data)`, `getRecords(table, filters)`, `updateRecord(table, id, data)`, `deleteRecord(table, id)`. All functions auto-inject `updated_at: new Date().toISOString()`. User-scoped queries use RLS (no manual `WHERE user_id =` needed).
```

```
Rule: No redundant sub-imports
Exact: Do NOT add `@supabase/auth-js`, `@supabase/storage-js`, `@supabase/postgrest-js`, or `@supabase/realtime-js` to package.json. The `@supabase/supabase-js` package re-exports everything. Import only from `@supabase/supabase-js` or from your local `src/lib/supabase.ts` client.
```

**Bad examples (too vague, defeats the purpose):**

```
Rule: Auth provider sign-in flow
Exact: Use the auth provider's sign-in method ← THIS IS JUST THE AGNOSTIC COLUMN REPEATED. USELESS.
```

```
Rule: CRUD helper functions
Exact: Create CRUD functions in the services directory ← NO. Tell me the exact file path, function names, and patterns.
```

### Step 5: Validate

For each completed sheet, verify:
- [ ] All 192 Martin rules have an entry (even if NOT_ACTIVATED)
- [ ] All 71 Industry Standards rules have an entry (even if NOT_ACTIVATED)
- [ ] All 14 mechanism categories have an entry with status and implementation details
- [ ] All 43 banned patterns have stack-specific enforcement guidance
- [ ] No branded tech names used incorrectly (e.g., don't say "Firebase" in a Supabase sheet)
- [ ] File paths match the actual boilerplate directory structure
- [ ] Function names and import paths are real (not guessed)
- [ ] Deactivated rules section lists everything that's toggled off with clear reasoning (from ALL three source checklists)
- [ ] Stack Summary table at the top is accurate

---

## The AutoForge Add-On Sheet (Special Case)

This one is different from the others. Instead of matching against a boilerplate repo, you're matching against **AutoForge's own codebase**:

### What to Read
- `/CLAUDE.md` — project overview, architecture, conventions
- `server/main.py` — how routers are registered
- `server/routers/` — existing router patterns (pick any 2-3 as examples)
- `server/services/` — existing service patterns
- `ui/src/App.tsx` — how pages are routed
- `ui/src/pages/` — existing page patterns
- `ui/src/components/` — component organization
- `ui/src/hooks/` — hook patterns
- `ui/src/lib/api.ts` — API client patterns
- `ui/src/lib/types.ts` — type definition patterns
- `ui/WORKSPACE_STANDARDS.md` — layout and component standards

### Key Differences from Standalone Sheets
- No standalone auth (uses AutoForge's existing subscription OAuth)
- No standalone database setup (uses AutoForge's existing Supabase instance)
- No standalone deployment (deploys WITH AutoForge via `start_ui.bat`)
- Must follow AutoForge's FastAPI router registration pattern
- Must follow AutoForge's React Query + TanStack patterns
- Must follow AutoForge's neobrutalism design system
- File paths are within AutoForge's directory tree, not standalone

---

## Output Format Reference

Use this exact structure for each sheet (matches the format in `prd-stage-0a-boilerplate-matching.md`):

```markdown
# Exact Reality Sheet: [Name]

**Generated:** [date]
**Boilerplate:** [name + repo URL]
**Boilerplate version:** [commit hash]
**Toggles:** DB=[ON/OFF] | Auth=[ON/OFF] | Payments=[ON/OFF]

## Stack Summary

| Field | Value |
|-------|-------|
| Framework | [exact framework + version] |
| Database | [exact database] |
| Auth | [exact auth provider + method] |
| Hosting | [exact hosting platform] |
| CSS | [exact styling approach] |
| State Management | [exact approach] |
| Payments | [exact payment provider or "Not activated"] |

---

## Part 1: Martin's Structural Rules ([X] of 192 active)

### [Category Name]
| # | Rule | Exact Implementation | Match | Severity |
|---|------|---------------------|-------|----------|
| 1 | [rule name] | [specific, actionable implementation] | EXACT/ADAPTED/NOT_PRESENT | CRITICAL/STANDARD/POLISH |

[... repeat for all 22 categories ...]

---

## Part 2: Industry Standards ([X] of 71 active)

### [Category Name]
| # | Rule | Exact Implementation | Match | Severity |
|---|------|---------------------|-------|----------|
| 200 | [rule name] | [specific implementation] | EXACT/ADAPTED/NOT_PRESENT | CRITICAL/STANDARD/POLISH |

[... repeat for all 10 industry categories ...]

---

## Part 3: Mechanism Coverage Matrix (14 categories)

| ID | Category | Status | Boilerplate Implementation |
|----|----------|--------|---------------------------|
| A | Data Input | needs_user_input/covered/NOT_ACTIVATED | [specific files, functions, patterns] |
| B | Data Storage | covered | [exact database client, file paths, query patterns] |
[... all 14 categories ...]

---

## Part 4: Banned Patterns (43 total)

| # | Pattern | Exact Enforcement |
|---|---------|-------------------|
| 1 | [banned thing] | [what specifically to watch for in this stack] |

[... all 43 banned patterns ...]

---

## Deactivated Rules ([Y] rules across all sources)

| # | Source | Rule | Reason |
|---|--------|------|--------|
| ... | Martin/Industry/Mechanism | ... | [which toggle is OFF] |
```

---

## Execution Plan (Per Agent)

Since each boilerplate gets its own fresh agent, here's what each agent does:

### Agent A: Web (DevToDollars)
1. Read all three source checklists (Martin's, Industry Standards, Mechanism Categories)
2. Read `prd-stage-0a-boilerplate-matching.md` — understand the output format
3. Clone/read DevToDollars web boilerplate (`digisurfsome/Web-BoilerPlate-D2D`)
4. Produce `supabase_web_full.md` first (all toggles ON — this is the complete mapping)
5. Derive `supabase_web_db_auth.md` from full (toggle Payments OFF)
6. Derive `supabase_web_db_only.md` (toggle Auth + Payments OFF)
7. Derive `supabase_web_minimal.md` (all toggles OFF)

### Agent B: Mobile (ApparenceKit)
1. Read all three source checklists
2. Read the Stage 0a PRD for output format
3. Clone/read ApparenceKit (`digisurfsome/apparence-kit-supabase`) + docs (`apparencekit.dev`)
4. Produce `flutter_mobile_full.md` first
5. Derive `flutter_mobile_db_auth.md`, `flutter_mobile_db_only.md`, `flutter_mobile_minimal.md`

### Agent C: Dual (Fullstack)
1. Read all three source checklists
2. Read the Stage 0a PRD for output format
3. Clone/read fullstack boilerplate (`digisurfsome/fullstack-boilerplate`)
4. Also reference the completed web + mobile sheets if available (for cross-platform differences)
5. Produce `dual_full.md` and `dual_db_auth.md`

### Agent D: AutoForge Add-On
1. Read all three source checklists
2. Read the Stage 0a PRD for output format
3. Read AutoForge's own codebase (CLAUDE.md, server/, ui/, etc.)
4. Produce `autoforge_addon.md` — **web only, no DB/Auth/Payments toggles**
5. This is a fixed configuration: uses AutoForge's existing subscription auth, existing Supabase, no standalone payments

### Agent E: No Boilerplate Default
1. Read all three source checklists
2. Read the Stage 0a PRD for output format
3. Produce `no_boilerplate_default.md` — uses Supabase/Next.js defaults but everything marked `NOT_PRESENT`
4. This is the simplest sheet: just the rules with generic Supabase implementation guidance, no boilerplate code to reference

**Estimated scope per agent:** 1-4 documents. Each full sheet is ~600-800 lines (covering all 263 rules + mechanisms + bans). Variant sheets are derived from the full sheet by toggling rules off.

**Recommended launch order:** Agent A (web) first since it's 80% of builds. Then Agent D (AutoForge). Then B, E, C.

---

## Quality Bar

An Exact Reality Sheet is GOOD if:
- A brand new agent with zero context could read it and know exactly what file to create, what function to call, what import to use — without reading the boilerplate source code
- It contains zero vague instructions ("use the configured X" is a FAIL)
- Every file path mentioned actually exists in the boilerplate
- Every function name mentioned is real
- The toggle variants correctly deactivate dependent rules across ALL THREE checklists (auth OFF → Martin's route guard rules OFF + Industry's auth testing rules OFF + Mechanism E deactivated)
- All 263 rules + 14 mechanism categories + 43 banned patterns are accounted for (no gaps)
- The four parts (Martin, Industry, Mechanisms, Bans) are clearly separated with their own headers
