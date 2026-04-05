# Agent A Handoff: Web Boilerplate — DevToDollars

## Your Assignment

You are a fresh agent. Your ONE job: produce 5 Exact Reality Sheets for the **DevToDollars web boilerplate** (Next.js + Supabase + Stripe + Tailwind).

**You are NOT building code.** You are producing documentation — structured markdown files that will be injected as preambles into AI agent build sessions.

---

## Your 5 Sheets (Progressive Build Order)

| # | File to Create | DB | Auth | Payments | AutoForge | Build Strategy |
|---|----------------|----|------|----------|-----------|----------------|
| 1 | `web_base.md` | - | - | - | - | **Start here.** Full boilerplate, nothing wired up. All DB/Auth/Payments code PRESENT but dormant. |
| 2 | `web_autoforge.md` | - | - | - | YES | Take sheet 1, add AutoForge connection hooks (attaches to AutoForge's port 8888, uses AF's auth/DB via SDK). |
| 3 | `web_db.md` | ON | - | - | - | Take sheet 1, wire up Supabase DB (activate client, RLS policies, CRUD service layer, migrations). |
| 4 | `web_db_auth.md` | ON | ON | - | - | Take sheet 3, wire up Supabase Auth (activate OAuth, session management, route guards, role system). |
| 5 | `web_db_auth_payments.md` | ON | ON | ON | - | Take sheet 4, wire up Stripe (activate webhooks, subscription management, pricing page). Full SaaS. |

**Write all sheets to:** `docs/page-prds/prd-maker/boilerplates/final/`

---

## Step 1: Read These Files First

### The Three Source Checklists (Templates)

1. **Martin's Agnostic Checklist** — `docs/page-prds/prd-maker/martin-agnostic-checklist.md`
   - 192 rules, 22 categories, 43 banned patterns
   - Rules numbered 1-192

2. **Industry Standards Checklist** — `docs/page-prds/prd-maker/industry-standards-checklist.md`
   - 71 rules, 10 categories
   - Rules numbered 200-270

3. **Mechanism Categories** — `docs/page-prds/prd-maker/skills/stage-00-technical-foundation/references/mechanism-categories.md`
   - 14 categories (A through N)

### The PRD (Output Format)
- `docs/page-prds/prd-maker/boilerplates/prd-stage-0a-boilerplate-matching.md` — Read the "Exact Reality Sheet Format" section for the output structure.

### Your Boilerplate
- **Repo:** `https://github.com/digisurfsome/Web-BoilerPlate-D2D`
- **Docs:** `https://www.devtodollars.com/docs/`
- **Stack:** Next.js + Supabase + Stripe + Tailwind
- **Focus on:** `package.json`, `tsconfig.json`, `src/` directory structure, `supabase/` config, auth patterns, database patterns, Stripe integration, middleware, route guards

### For the AutoForge Sheet (Sheet 2 Only)
Also read these AutoForge files:
- `/CLAUDE.md` — project overview, architecture, conventions
- `server/main.py` — how routers are registered
- `ui/src/App.tsx` — how pages are routed
- `ui/WORKSPACE_STANDARDS.md` — layout and component standards

---

## Step 2: Build Each Sheet

### How to Walk Through the Checklists

**Pass 1: Martin's Structural Rules (192 rules)**
Go through `martin-agnostic-checklist.md` rule by rule (all 22 categories). For each rule, find the matching code in the boilerplate and write the exact implementation.

**Pass 2: Industry Standards (71 rules)**
Go through `industry-standards-checklist.md` rule by rule (all 10 categories). Find how the boilerplate handles i18n, config externalization, env parity, accessibility, performance, error handling, testing, CI/CD, observability, and API design.

**Pass 3: Mechanism Coverage Matrix (14 categories)**
Go through `mechanism-categories.md` category by category (A-N). Determine if the boilerplate covers it natively, partially, or not at all. Document what's built-in with specific file paths and function names.

**Pass 4: Banned Patterns (43 patterns)**
Go through the banned patterns section of Martin's checklist. For each, write the stack-specific detection method.

### Match Tags

For each rule, tag the match:
- `EXACT` — boilerplate implements this exactly
- `ADAPTED` — principle applies, implementation differs (document how)
- `NOT_PRESENT` — boilerplate doesn't have this; agent builds from scratch
- `PRESENT_NOT_WIRED` — code exists in boilerplate but is dormant (for base sheet)
- `NOT_ACTIVATED` — toggled off for this variant

### Progressive Build Strategy

1. **Sheet 1 (`web_base`)** — Go through ALL 263 rules + 14 mechanisms + 43 bans. DB/Auth/Payments rules get tagged `PRESENT_NOT_WIRED`. This is the most work (~600-800 lines).
2. **Sheet 2 (`web_autoforge`)** — Copy sheet 1, add AutoForge connection section (~100 lines of additions). Uses AF's auth/DB/subscription, not standalone.
3. **Sheet 3 (`web_db`)** — Copy sheet 1, change DB-related rules from `PRESENT_NOT_WIRED` to `EXACT`/`ADAPTED`. Document the wiring.
4. **Sheet 4 (`web_db_auth`)** — Copy sheet 3, change Auth-related rules to active. Document the wiring.
5. **Sheet 5 (`web_db_auth_payments`)** — Copy sheet 4, change Payments-related rules to active. Full SaaS.

---

## Step 3: Write the Exact Implementation Column

**Good examples (specific, actionable):**

```
Rule: Auth provider sign-in flow
Exact: `await supabase.auth.signInWithOAuth({ provider: 'google', options: { redirectTo: `${window.location.origin}/auth/callback` } })` — configured in `src/lib/supabase.ts`, callback handled by `src/app/auth/callback/route.ts`
```

```
Rule: CRUD helper functions
Exact: Use `src/lib/database.ts` which exports `createRecord(table, data)`, `getRecords(table, filters)`, `updateRecord(table, id, data)`, `deleteRecord(table, id)`. All functions auto-inject `updated_at: new Date().toISOString()`. User-scoped queries use RLS.
```

**Bad examples (too vague — FAIL):**

```
Rule: Auth provider sign-in flow
Exact: Use the auth provider's sign-in method ← USELESS. Just repeated the agnostic column.
```

---

## Output Format

Use this structure for each sheet:

```markdown
# Exact Reality Sheet: [Name]

**Generated:** [date]
**Boilerplate:** DevToDollars Web — https://github.com/digisurfsome/Web-BoilerPlate-D2D
**Boilerplate version:** [commit hash]
**Toggles:** DB=[ON/OFF] | Auth=[ON/OFF] | Payments=[ON/OFF]

## Stack Summary
| Field | Value |
|-------|-------|
| Framework | Next.js 14 (App Router) |
| Database | Supabase/Postgres |
| Auth | Supabase Auth (Google OAuth) |
| Hosting | Vercel |
| CSS | Tailwind CSS |
| State Management | React Context |
| Payments | Stripe (via @stripe/stripe-js) |

---

## Part 1: Martin's Structural Rules ([X] of 192 active)
### [Category Name]
| # | Rule | Exact Implementation | Match | Severity |
|---|------|---------------------|-------|----------|
| 1 | [rule] | [specific implementation] | EXACT/ADAPTED/NOT_PRESENT/PRESENT_NOT_WIRED | CRITICAL/STANDARD/POLISH |
[... all 22 categories ...]

---

## Part 2: Industry Standards ([X] of 71 active)
### [Category Name]
| # | Rule | Exact Implementation | Match | Severity |
[... all 10 categories ...]

---

## Part 3: Mechanism Coverage Matrix (14 categories)
| ID | Category | Status | Boilerplate Implementation |
|----|----------|--------|---------------------------|
[... all 14 categories ...]

---

## Part 4: Banned Patterns (43 total)
| # | Pattern | Exact Enforcement |
|---|---------|-------------------|
[... all 43 ...]

---

## Deactivated Rules ([Y] rules)
| # | Source | Rule | Reason |
|---|--------|------|--------|
[... toggled-off rules ...]
```

---

## Validation Checklist

Before finishing each sheet, verify:
- [ ] All 192 Martin rules have an entry
- [ ] All 71 Industry Standards rules have an entry
- [ ] All 14 mechanism categories have an entry
- [ ] All 43 banned patterns have stack-specific enforcement
- [ ] Zero vague instructions ("use the configured X" is a FAIL)
- [ ] File paths match the actual boilerplate directory structure
- [ ] Function names and import paths are real (not guessed)
- [ ] Deactivated rules section is complete
- [ ] Stack Summary is accurate
