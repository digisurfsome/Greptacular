# PRD: Stage 0a — Boilerplate Matching Step

## Summary

Stage 0a is a **pre-build step** that runs before Stage 0 (Technical Foundation). Its job: take Martin's 192-rule agnostic checklist and produce an **Exact Reality Sheet** — a stack-specific document that tells every downstream stage exactly what to do for THIS build's technology stack.

This step is the foundation of the entire build. Every stage after it uses the Exact Reality Sheet as its structural preamble. Get this wrong and agents make guesses. Get this right and agents know exactly what auth calls to make, what database patterns to use, what imports are banned.

---

## The Problem

The agnostic checklist says things like "use the configured authentication provider's sign-in flow." That's correct but vague. An agent building with Supabase needs to know: "use `supabase.auth.signInWithOAuth({ provider: 'google' })`." An agent building with Flutter needs something different entirely. Without the Exact Reality Sheet, every downstream stage has to figure this out on its own — and they get it wrong.

---

## Three Source Checklists (Not Just Martin's)

The Exact Reality Sheet covers ALL structural knowledge, not just Martin's rules. Stage 0a resolves three source documents against the boilerplate:

### 1. Martin's Agnostic Checklist (`martin-agnostic-checklist.md`)
- **192 rules** across **22 categories** + **43 banned patterns**
- Covers: file structure, component patterns, state management, auth setup, styling, data access, routing, banned anti-patterns
- Rules numbered 1-192

### 2. Industry Standards Checklist (`industry-standards-checklist.md`)
- **71 rules** across **10 categories**
- Covers everything Martin didn't address: i18n, config externalization, environment parity, accessibility (WCAG 2.1 AA), performance budgets, error handling, testing standards, CI/CD, observability, API design
- Sources: IEEE 830, FURPS+, Volere, arc42, C4 Model, 12-Factor App, WCAG 2.1 AA
- Rules numbered 200-270 (no collision with Martin's)

### 3. Mechanism Coverage Matrix (`references/mechanism-categories.md`)
- **14 categories** (A through N)
- Not a rule-per-rule checklist — it's a coverage matrix showing which mechanism categories the boilerplate handles natively vs which need user input
- Categories: Data Input, Data Storage, Data Processing, Data Output, Authentication, Authorization, Communication, Integration, Workflow, Search & Discovery, Collaboration, Monetization, Admin/Ops, Infrastructure

### Combined Output

The Exact Reality Sheet merges all three into one document:

| Section | Source | Rule Count | What It Tells the Agent |
|---------|--------|------------|------------------------|
| Part 1: Structural Rules | Martin's checklist | 192 | Exact file paths, function names, import patterns, config values |
| Part 2: Industry Standards | Industry checklist | 71 | Exact i18n setup, env var patterns, a11y implementation, testing config |
| Part 3: Mechanism Coverage | Mechanism matrix | 14 categories | Which mechanisms are pre-built vs need building from scratch |
| Part 4: Banned Patterns | Martin's checklist | 43 | Stack-specific things to watch for and reject |

**Total: 263 rules + 14 mechanism categories + 43 banned patterns = one unified source of truth per boilerplate.**

---

## Flow

```
User starts a new build
         |
    ┌────▼────┐
    │ Pick a   │
    │ boilerplate │
    └────┬────┘
         |
    ┌────┼────────────────┬─────────────────┐
    ▼    ▼                ▼                 ▼
Pre-matched        New boilerplate     No boilerplate
boilerplate                          
    |                    |                  |
    ▼                    ▼                  ▼
Feature toggles     Run Stage 0a       Use default
(auth/db/payments)  matching agent     reality sheet
    |                    |                  |
    ▼                    ▼                  ▼
Load saved sheet    Agent reads          Load
+ apply toggles    agnostic checklist   no-boilerplate
                   + boilerplate code,  defaults
                   produces Exact       
                   Reality Sheet        
                        |
                        ▼
                   Save sheet for
                   future reuse
    |                    |                  |
    └────────┬───────────┘──────────────────┘
             ▼
    Exact Reality Sheet injected
    as preamble into Stage 0+
```

---

## Pre-Matched Boilerplates (Skip Stage 0a)

These are boilerplates we use regularly. Their Exact Reality Sheets are pre-built and saved. When selected, Stage 0a is skipped entirely — the sheet is loaded and injected directly.

### Boilerplate: Supabase Web (`supabase_web`)

**Stack:** Next.js 14 (App Router) + Supabase/Postgres + Supabase Auth + Vercel + Tailwind CSS

**Feature Toggles (checkboxes in UI):**

| Toggle | What It Controls | Default |
|--------|-----------------|---------|
| Database | Supabase/Postgres, RLS policies, CRUD service layer, server timestamps | ON |
| Auth | Supabase Auth, Google OAuth, session management, route guards, role system | ON |
| Payments | Stripe integration, webhook handling, subscription management, pricing page | OFF |

**Key concept:** DB/Auth/Payments code is always PRESENT in the boilerplate. "Wired up" means activated and connected. "Not wired" means dormant — the code is there, ready to activate later if you ever want to turn it into a standalone app.

**Progressive sheet variants (each builds on the last):**

| Variant | DB | Auth | Payments | Use Case |
|---------|----|----|----------|----------|
| `web_base` | - | - | - | Utility app, nothing wired. Starting point. |
| `web_autoforge` | - | - | - (+AF) | Same as base but attached to AutoForge. Uses AF's auth/DB via SDK. |
| `web_db` | ON | - | - | Data-driven app, no user accounts |
| `web_db_auth` | ON | ON | - | App with users but no payments |
| `web_db_auth_payments` | ON | ON | ON | Full SaaS app |

Each variant is its own saved Exact Reality Sheet. DB/Auth/Payments code stays in the codebase regardless — the sheet just tells the agent which pieces to wire up vs leave dormant.

### Boilerplate: Flutter Mobile (`flutter_mobile`)

**Stack:** Flutter + Supabase backend + Supabase Auth + Supabase Storage

**Same progressive system:** `mobile_base` → `mobile_db` → `mobile_db_auth` → `mobile_db_auth_payments`. No AutoForge variant for mobile-only (AutoForge is web-based).

### Boilerplate: Dual Web + Mobile (`dual`)

**Stack:** Both boilerplates combined. Shared Supabase backend, separate Flutter and Next.js frontends.

**Same progressive system as web:** `dual_base` → `dual_autoforge` → `dual_db` → `dual_db_auth` → `dual_db_auth_payments`. The AutoForge variant lets you run a personal cross-platform app through AutoForge (mobile talks to AF server, web module lives inside AF — only works when AF server is running).

Same toggles apply globally (if auth is on, it's on for both platforms). Sheet includes platform-specific instructions where web and mobile implementations differ.

---

## New Boilerplate Flow (Stage 0a Runs)

When a user (or SaaS customer) brings a boilerplate we haven't pre-matched:

### Input
1. Martin's agnostic checklist (192 rules, 22 categories, 43 banned patterns)
2. Industry standards checklist (71 rules, 10 categories)
3. Mechanism categories reference (14 categories A-N)
4. The boilerplate's source code (or a summary/manifest of it)

### Process
The Stage 0a agent reads all three source documents and cross-references every rule against the boilerplate:

**Pass 1: Martin's Structural Rules (192 rules)**
For each rule, find the matching implementation in the boilerplate and write the exact reality.

**Pass 2: Industry Standards (71 rules)**
Same process — find how the boilerplate handles i18n, config externalization, env parity, accessibility, performance, error handling, testing, CI/CD, observability, and API design.

**Pass 3: Mechanism Coverage Matrix (14 categories)**
For each mechanism category (A-N), determine whether the boilerplate covers it natively, partially, or not at all. Document what's built-in vs what the app-specific build must implement.

For each rule across all passes, tag the match type:
- `EXACT` — boilerplate implements this rule exactly
- `ADAPTED` — rule principle applies but boilerplate does it differently (document how)
- `NOT_PRESENT` — boilerplate doesn't cover this; agent must implement from scratch
- `NOT_ACTIVATED` — boilerplate has this but the user toggled it off; skip this rule

### Output
An **Exact Reality Sheet** with this format per rule:

| # | Rule | Exact Implementation | Match | Severity |
|---|------|---------------------|-------|----------|
| 1 | Dependency versions locked | `package-lock.json` is committed and frozen. Run `npm ci` not `npm install`. Never modify lock file directly. | EXACT | STANDARD |
| 2 | No redundant sub-imports | Do not add `@supabase/auth-js`, `@supabase/storage-js`, `@supabase/postgrest-js` separately. The `@supabase/supabase-js` client re-exports all modules. | EXACT | STANDARD |
| 3 | Auth provider | Supabase Auth with Google OAuth. Sign-in: `supabase.auth.signInWithOAuth({ provider: 'google' })`. Session check: `supabase.auth.getSession()`. Listener: `supabase.auth.onAuthStateChange()`. | EXACT | CRITICAL |

No comparison columns. No "Martin Says" column. No "Agnostic" column. Just the rule name and the exact implementation for this stack. This is what the agent reads during the build.

### Save for Reuse
After Stage 0a produces the sheet, it's saved as a named profile. Next time anyone selects that boilerplate, the saved sheet loads and Stage 0a is skipped. A "re-check" option is available to re-run the matching if the boilerplate has been updated.

---

## No Boilerplate Flow

When building without a boilerplate, the agnostic checklist itself serves as the preamble — but with one modification: a **Default Reality Sheet** is generated that fills in sensible defaults:

- Framework: Next.js 14 (or whatever Stage 0 detects/user specifies)
- Database: Supabase/Postgres (default)
- Auth: Supabase Auth (default)
- Styling: Tailwind CSS

This is essentially the `supabase_web_full` sheet but with everything marked as "must implement from scratch" (no `EXACT` matches since there's no existing boilerplate code).

---

## Exact Reality Sheet Format

The output document structure:

```markdown
# Exact Reality Sheet: [Boilerplate Name] — [Variant]
# Generated: [date]
# Boilerplate version: [commit hash or version]
# Toggles: DB=[ON/OFF] Auth=[ON/OFF] Payments=[ON/OFF]

## Stack Summary
| Field | Value |
|-------|-------|
| Framework | Next.js 14 (App Router) |
| Database | Supabase/Postgres |
| Auth | Supabase Auth (Google OAuth) |
| Hosting | Vercel |
| CSS | Tailwind CSS |
| Payments | Stripe (via @stripe/stripe-js) |

---

## Part 1: Martin's Structural Rules (192 rules, X active)

### Category: Stack (Mandatory)
| # | Rule | Exact Implementation | Match | Severity |
|---|------|---------------------|-------|----------|
| 1 | Framework with type safety | Next.js 14 with TypeScript strict mode (`"strict": true` in tsconfig.json) | EXACT | STANDARD |
| ... | ... | ... | ... | ... |

### Category: File Structure
| # | Rule | Exact Implementation | Match | Severity |
| ... |

[... all 22 categories ...]

---

## Part 2: Industry Standards (71 rules, X active)

### Category: Internationalization (i18n)
| # | Rule | Exact Implementation | Match | Severity |
|---|------|---------------------|-------|----------|
| 200 | Externalize all user-facing strings | All strings in `src/locales/en.json`. Use `useTranslation()` hook. No hardcoded text in components. | NOT_PRESENT | STANDARD |
| ... | ... | ... | ... | ... |

### Category: Config Externalization
| ... |

[... all 10 industry categories ...]

---

## Part 3: Mechanism Coverage Matrix (14 categories)

| ID | Category | Status | Boilerplate Implementation |
|----|----------|--------|---------------------------|
| A | Data Input | needs_user_input | Forms depend on app idea; boilerplate has no pre-built forms |
| B | Data Storage | covered | Supabase/Postgres via `@supabase/supabase-js`. Client at `src/lib/supabase.ts`. RLS policies in `supabase/migrations/`. |
| C | Data Processing | needs_user_input | App-specific logic |
| D | Data Output | needs_user_input | App-specific views |
| E | Authentication | covered | Supabase Auth. Sign-in at `src/app/auth/`. Callback at `src/app/auth/callback/route.ts`. |
| F | Authorization | covered | Supabase RLS. Policies in `supabase/migrations/`. Role column on `profiles` table. |
| G | Communication | needs_user_input | No notification system in boilerplate |
| H | Integration | needs_user_input | No external integrations |
| I | Workflow | needs_user_input | No workflow engine |
| J | Search & Discovery | needs_user_input | Postgres full-text search available but needs app-specific setup |
| K | Collaboration | needs_user_input | No collaboration features |
| L | Monetization | covered/NOT_ACTIVATED | Stripe via `@stripe/stripe-js`. Webhooks at `src/app/api/webhooks/stripe/`. Toggle-dependent. |
| M | Admin/Ops | needs_user_input | No admin panel |
| N | Infrastructure | covered | Vercel hosting (auto from `next.config.js`). Supabase managed DB. |

---

## Part 4: Banned Patterns (43 total)

| # | Pattern | Exact Enforcement |
|---|---------|-------------------|
| 1 | No inline styles | Grep for `style=` in JSX — reject any match except `style={cssVariableObj}` |
| ... | ... | ... |

[... all 43 banned patterns with stack-specific detection ...]

---

## Deactivated Rules (toggled off)
| # | Rule | Source | Reason |
|---|------|--------|--------|
| L-1 | Payment processor | Martin | Payments toggle OFF |
| 250 | Payment webhook validation | Industry | Payments toggle OFF |
| L | Monetization (full category) | Mechanism | Payments toggle OFF |
| ... | ... | ... | ... |
```

---

## UI Integration

### In the PRD Maker build flow:

```
Step 1: "Pick your boilerplate"
┌──────────────────────────────────────┐
│  ○ Supabase Web (default)            │
│  ○ Flutter Mobile                    │
│  ○ Dual (Web + Mobile)               │
│  ○ AutoForge Add-On                  │
│  ○ New boilerplate (upload/paste)    │
│  ○ No boilerplate                    │
└──────────────────────────────────────┘

Step 2 (if pre-matched): "Feature toggles"
┌──────────────────────────────────────┐
│  ☑ Database (Supabase/Postgres)     │
│  ☑ Auth (Supabase Auth + OAuth)     │
│  ☐ Payments (Stripe)                │
│                                      │
│  [Load Exact Reality Sheet →]        │
└──────────────────────────────────────┘

Step 2 (if new boilerplate): "Paste or upload"
┌──────────────────────────────────────┐
│  Paste boilerplate manifest, or      │
│  provide repo URL for analysis...    │
│                                      │
│  [Run Matching →]                    │
│  (produces Exact Reality Sheet)      │
└──────────────────────────────────────┘
```

---

## Sheets We Need to Pre-Build (14 total, 3 agents)

**Key concept:** DB/Auth/Payments code is always PRESENT in the boilerplate. "Wired up" means activated and connected. "Not wired" means the code is there but dormant — ready to activate later if needed.

### Agent A: Web (5 sheets)

| # | Sheet Name | DB | Auth | Payments | AutoForge | Priority |
|---|------------|----|------|----------|-----------|----------|
| 1 | `web_base` | - | - | - | - | HIGH |
| 2 | `web_autoforge` | - | - | - | YES | HIGH |
| 3 | `web_db` | ON | - | - | - | HIGH |
| 4 | `web_db_auth` | ON | ON | - | - | HIGH |
| 5 | `web_db_auth_payments` | ON | ON | ON | - | HIGH |

### Agent B: Mobile (4 sheets)

| # | Sheet Name | DB | Auth | Payments | Priority |
|---|------------|----|------|----------|----------|
| 6 | `mobile_base` | - | - | - | HIGH |
| 7 | `mobile_db` | ON | - | - | MEDIUM |
| 8 | `mobile_db_auth` | ON | ON | - | HIGH |
| 9 | `mobile_db_auth_payments` | ON | ON | ON | MEDIUM |

### Agent C: Dual (5 sheets)

| # | Sheet Name | DB | Auth | Payments | AutoForge | Priority |
|---|------------|----|------|----------|-----------|----------|
| 10 | `dual_base` | - | - | - | - | MEDIUM |
| 11 | `dual_autoforge` | - | - | - | YES | MEDIUM |
| 12 | `dual_db` | ON | - | - | - | MEDIUM |
| 13 | `dual_db_auth` | ON | ON | - | - | MEDIUM |
| 14 | `dual_db_auth_payments` | ON | ON | ON | - | MEDIUM |

### Build Order

Each agent builds progressively — stripped-down first, then layers on:

```
Base (nothing wired) → AutoForge variant (branch)
Base (nothing wired) → +DB → +DB+Auth → +DB+Auth+Payments
```

**Launch order:** Agent A first (web, 80% of builds). Then B (mobile). Then C (dual).

**Default (no boilerplate):** Just use the web boilerplate sheets. User picks their toggles → corresponding sheet is loaded.

---

## Relationship to Existing Stages

| Stage | How It Uses the Exact Reality Sheet |
|-------|-------------------------------------|
| **0a (this)** | PRODUCES the sheet |
| **0 (Tech Foundation)** | Reads sheet for tech_stack fields; skips tech detection since sheet already specifies everything |
| **1 (Idea Capture)** | Doesn't use sheet directly (idea is independent of stack) |
| **2 (Gap Analysis)** | Uses sheet to know which structural rules are already covered vs need implementation |
| **3 (Agent OS)** | Uses sheet for Wall/Door/Room classification — boilerplate-handled rules are Walls |
| **4 (Mechanism Extraction)** | Uses sheet to separate structural (already decided) from mechanism (still to extract) |
| **5 (7-Question)** | Skips structural questions that the sheet already answers |
| **6 (Layout/Mockups)** | Uses sheet for styling tokens, component patterns, navigation approach |
| **7 (Phase Sequencing)** | Uses sheet for file path conventions, build order dependencies |
| **8 (Protocol Injection)** | Uses sheet for exact import patterns, banned patterns, file sandbox rules |
| **9 (Verification)** | Uses sheet for functional check commands (what to test, what ports, what URLs) |
| **10 (Output Generator)** | Uses sheet for CLAUDE.md generation, build.sh commands, platform wrappers |

---

## Re-Check Flow

Saved sheets can go stale if the boilerplate is updated. The re-check flow:

1. User selects a pre-matched boilerplate
2. System checks: has the boilerplate changed since the sheet was generated? (compare commit hash or version)
3. If changed: "Your boilerplate has been updated. Re-run matching?" → runs Stage 0a again, produces updated sheet, replaces the saved copy
4. If unchanged: load saved sheet as-is

---

## Files This PRD Produces

| File | Purpose |
|------|---------|
| `docs/page-prds/prd-maker/skills/stage-0a-boilerplate-matching/SKILL.md` | The Stage 0a skill (agent instructions) |
| `docs/page-prds/prd-maker/skills/stage-0a-boilerplate-matching/references/agnostic-checklist.md` | Symlink or copy of the agnostic checklist template |
| `docs/page-prds/prd-maker/exact-reality-sheets/supabase_web_db_auth.md` | Pre-built sheet (first to build) |
| `docs/page-prds/prd-maker/exact-reality-sheets/autoforge_addon.md` | Pre-built sheet |
| `docs/page-prds/prd-maker/exact-reality-sheets/[variant].md` | One per variant from the table above |
| `docs/page-prds/prd-maker/stage-contracts.md` | Updated with Stage 0a contract |

---

## Open Questions

1. **Toggle granularity:** Are DB/Auth/Payments the right three toggles, or do we need more? (e.g., separate "File Storage" toggle, separate "Realtime/Subscriptions" toggle)
2. **Boilerplate versioning:** Do we version the boilerplate sheets by commit hash, semver, or just date?
3. **SaaS customer flow:** When a customer brings their own boilerplate, do they see the matching happen in real-time, or does it run in the background and notify them?
