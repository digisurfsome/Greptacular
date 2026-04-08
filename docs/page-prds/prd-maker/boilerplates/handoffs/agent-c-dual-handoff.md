# Agent C Handoff: Dual Web+Mobile Boilerplate — Fullstack

## Your Assignment

You are a fresh agent. Your ONE job: produce 5 Exact Reality Sheets for the **Fullstack dual boilerplate** (Next.js web + Flutter mobile + shared Supabase backend).

**You are NOT building code.** You are producing documentation — structured markdown files that will be injected as preambles into AI agent build sessions.

---

## Your 5 Sheets (Progressive Build Order)

| # | File to Create | DB | Auth | Payments | AutoForge | Build Strategy |
|---|----------------|----|------|----------|-----------|----------------|
| 1 | `dual_base.md` | - | - | - | - | **Start here.** Both frontends, nothing wired up. Cross-platform personal app. |
| 2 | `dual_autoforge.md` | - | - | - | YES | Take sheet 1, add AutoForge hooks (mobile talks to AF server, web module lives inside AF). |
| 3 | `dual_db.md` | ON | - | - | - | Take sheet 1, wire up shared Supabase DB for both platforms. |
| 4 | `dual_db_auth.md` | ON | ON | - | - | Take sheet 3, wire up Supabase Auth for both platforms. |
| 5 | `dual_db_auth_payments.md` | ON | ON | ON | - | Take sheet 4, wire up Stripe for both platforms. Full SaaS. |

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
- **Repo:** `https://github.com/digisurfsome/fullstack-boilerplate`
- **Stack:** Next.js web frontend + Flutter mobile frontend + shared Supabase backend
- **Focus on:** How the two frontends share the same Supabase backend, shared types/models, deployment config, platform-specific auth flows, platform-specific styling

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
Go through `martin-agnostic-checklist.md` rule by rule. For EACH rule, document the implementation for BOTH platforms where they differ. Use this format:

```
Rule: Auth provider sign-in flow
Exact (Web): `await supabase.auth.signInWithOAuth({ provider: 'google' })` in `web/src/lib/supabase.ts`
Exact (Mobile): `await Supabase.instance.client.auth.signInWithOAuth(OAuthProvider.google)` in `mobile/lib/src/auth/auth_repository.dart`
```

If both platforms use the same approach, just write one entry.

**Pass 2: Industry Standards (71 rules)** — Same dual-platform approach.

**Pass 3: Mechanism Coverage Matrix (14 categories)** — Note shared vs platform-specific mechanisms.

**Pass 4: Banned Patterns (43 patterns)** — Enforcement for both JS/TS (web) and Dart (mobile).

### Match Tags

- `EXACT` — boilerplate implements this exactly
- `ADAPTED` — principle applies, implementation differs
- `NOT_PRESENT` — not in boilerplate, build from scratch
- `PRESENT_NOT_WIRED` — code exists but dormant
- `NOT_ACTIVATED` — toggled off

### Progressive Build Strategy

1. **Sheet 1 (`dual_base`)** — All rules, both platforms. DB/Auth/Payments tagged `PRESENT_NOT_WIRED`. Most work.
2. **Sheet 2 (`dual_autoforge`)** — Copy sheet 1, add AutoForge hooks. Mobile talks to AF server, web module inside AF.
3. **Sheet 3 (`dual_db`)** — Copy sheet 1, wire up shared Supabase DB for both platforms.
4. **Sheet 4 (`dual_db_auth`)** — Copy sheet 3, wire up Auth for both platforms.
5. **Sheet 5 (`dual_db_auth_payments`)** — Copy sheet 4, wire up Payments. Full SaaS.

---

## Step 3: Write the Exact Implementation Column

**Good examples (dual-platform, specific):**

```
Rule: CRUD helper functions
Exact (Web): `web/src/lib/database.ts` exports `createRecord()`, `getRecords()`, `updateRecord()`, `deleteRecord()`. Uses `@supabase/supabase-js`.
Exact (Mobile): `mobile/lib/src/core/data/database_repository.dart` provides same CRUD pattern. Uses `supabase_flutter` package.
Shared: Both use the same Supabase tables, same RLS policies, same schema.
```

**Bad examples (FAIL):**

```
Rule: CRUD helper functions
Exact: Create CRUD functions for both platforms ← NO. Give exact file paths and function names for EACH platform.
```

---

## Output Format

```markdown
# Exact Reality Sheet: [Name]

**Generated:** [date]
**Boilerplate:** Fullstack Dual — https://github.com/digisurfsome/fullstack-boilerplate
**Boilerplate version:** [commit hash]
**Toggles:** DB=[ON/OFF] | Auth=[ON/OFF] | Payments=[ON/OFF]

## Stack Summary
| Field | Value (Web) | Value (Mobile) |
|-------|-------------|----------------|
| Framework | Next.js 14 | Flutter [version] |
| Database | Supabase/Postgres (shared) | Supabase/Postgres (shared) |
| Auth | Supabase Auth | Supabase Auth |
| Hosting | Vercel | App Store / Google Play |
| CSS/Styling | Tailwind CSS | Flutter Theme |
| State Management | React Context | [Riverpod/Provider] |
| Payments | Stripe | Stripe / In-App Purchases |

---

## Part 1: Martin's Structural Rules ([X] of 192 active)
[... all 22 categories, with Web + Mobile implementations where they differ ...]

## Part 2: Industry Standards ([X] of 71 active)
[... all 10 categories ...]

## Part 3: Mechanism Coverage Matrix (14 categories)
[... note shared backend vs platform-specific implementations ...]

## Part 4: Banned Patterns (43 total)
[... enforcement for both JS/TS and Dart ...]

## Deactivated Rules ([Y] rules)
[... toggled-off rules ...]
```

---

## Validation Checklist

- [ ] All 192 Martin rules have entries (with dual-platform detail where needed)
- [ ] All 71 Industry Standards rules have entries
- [ ] All 14 mechanism categories show shared vs platform-specific
- [ ] All 43 banned patterns have enforcement for BOTH platforms
- [ ] Zero vague instructions
- [ ] File paths match actual boilerplate structure for BOTH frontends
- [ ] Function names are real for BOTH platforms
- [ ] Deactivated rules section is complete
- [ ] Stack Summary covers both platforms
