# Agent Handoff: Build Exact Reality Sheets for All Boilerplates

## Purpose

You are a fresh agent. Your job is to produce one **Exact Reality Sheet** per boilerplate variant. Each sheet maps Martin's 192-rule agnostic checklist to the exact, specific implementation for that boilerplate + toggle combination.

**You are NOT building code.** You are producing documentation — structured markdown files that will be injected as preambles into AI agent build sessions.

---

## What You're Building

For each boilerplate, you read the boilerplate's source code and docs, then go through all 192 rules in the agnostic checklist and write the **exact implementation** for that stack. Not "use the configured database" — but "use `supabase.from('users').select('*')`."

---

## Input Files (Read These First)

### The Template
- `docs/page-prds/prd-maker/martin-agnostic-checklist.md` — The 192-rule agnostic checklist. This is your template. Every rule in here gets a specific implementation in each sheet.

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

### Step 2: Walk Through Every Checklist Rule

Go through `martin-agnostic-checklist.md` rule by rule (all 22 categories + banned patterns). For each rule:

1. **Find the matching code** in the boilerplate
2. **Write the exact implementation** — specific file paths, function names, import statements, config values
3. **Tag the match type:**
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
- [ ] Every one of the 192 rules has an entry (even if NOT_ACTIVATED)
- [ ] No branded tech names used incorrectly (e.g., don't say "Firebase" in a Supabase sheet)
- [ ] File paths match the actual boilerplate directory structure
- [ ] Function names and import paths are real (not guessed)
- [ ] Deactivated rules section lists everything that's toggled off with clear reasoning
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

Use this exact structure for each sheet:

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

## Active Rules ([X] of 192)

### [Category Name]

| # | Rule | Exact Implementation | Match | Severity |
|---|------|---------------------|-------|----------|
| 1 | [rule name] | [specific, actionable implementation] | EXACT/ADAPTED/NOT_PRESENT | CRITICAL/STANDARD/POLISH |

[... repeat for all 22 categories + banned patterns ...]

## Deactivated Rules ([Y] rules)

| # | Category | Rule | Reason |
|---|----------|------|--------|
| ... | ... | ... | [which toggle is OFF] |

## Banned Patterns (43 total)

| # | Pattern | Exact Enforcement |
|---|---------|-------------------|
| 1 | [banned thing] | [what specifically to watch for in this stack] |
```

---

## Execution Plan

**Recommended order for the agent:**

1. Read `martin-agnostic-checklist.md` thoroughly — understand all 22 categories and 192 rules
2. Read `prd-stage-0a-boilerplate-matching.md` — understand the output format
3. Clone/read DevToDollars web boilerplate → produce `supabase_web_db_auth.md` (Priority 1)
4. Read AutoForge codebase → produce `autoforge_addon.md` (Priority 1)
5. Derive `supabase_web_full.md` from #3 by adding Stripe/payments rules (Priority 2)
6. Clone/read ApparenceKit → produce `flutter_mobile_db_auth.md` (Priority 2)
7. Produce `no_boilerplate_default.md` using defaults (Priority 2)
8. Derive remaining variants from the full sheets (Priority 3)

**Estimated scope:** ~12 documents total. Each full sheet is ~400-600 lines. Variant sheets can be derived from the full sheet by toggling rules off, so they're faster.

---

## Quality Bar

An Exact Reality Sheet is GOOD if:
- A brand new agent with zero context could read it and know exactly what file to create, what function to call, what import to use — without reading the boilerplate source code
- It contains zero vague instructions ("use the configured X" is a FAIL)
- Every file path mentioned actually exists in the boilerplate
- Every function name mentioned is real
- The toggle variants correctly deactivate dependent rules (auth OFF → route guards also OFF)
