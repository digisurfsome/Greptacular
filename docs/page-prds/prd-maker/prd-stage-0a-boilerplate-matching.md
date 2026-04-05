# PRD: Stage 0a — Boilerplate Matching Step

## Summary

Stage 0a is a **pre-build step** that runs before Stage 0 (Technical Foundation). Its job: take Martin's 192-rule agnostic checklist and produce an **Exact Reality Sheet** — a stack-specific document that tells every downstream stage exactly what to do for THIS build's technology stack.

This step is the foundation of the entire build. Every stage after it uses the Exact Reality Sheet as its structural preamble. Get this wrong and agents make guesses. Get this right and agents know exactly what auth calls to make, what database patterns to use, what imports are banned.

---

## The Problem

The agnostic checklist says things like "use the configured authentication provider's sign-in flow." That's correct but vague. An agent building with Supabase needs to know: "use `supabase.auth.signInWithOAuth({ provider: 'google' })`." An agent building with Flutter needs something different entirely. Without the Exact Reality Sheet, every downstream stage has to figure this out on its own — and they get it wrong.

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

**Toggle Combinations → Sheet Variants:**

| Variant | DB | Auth | Payments | Use Case |
|---------|----|----|----------|----------|
| `supabase_web_full` | ON | ON | ON | Full SaaS app |
| `supabase_web_db_auth` | ON | ON | OFF | App with users but no payments |
| `supabase_web_db_only` | ON | OFF | OFF | Data-driven app, no user accounts |
| `supabase_web_minimal` | OFF | OFF | OFF | Static/utility app on the boilerplate scaffold |

Each variant is its own saved Exact Reality Sheet. The only difference between them is which rules are active vs marked "NOT ACTIVATED — skip."

### Boilerplate: Flutter Mobile (`flutter_mobile`)

**Stack:** Flutter + Supabase backend + Supabase Auth + Supabase Storage

**Same toggle system as web.** Same 4 variants (full, db_auth, db_only, minimal).

### Boilerplate: Dual Web + Mobile (`dual`)

**Stack:** Both boilerplates combined. Shared Supabase backend, separate Flutter and Next.js frontends.

**Same toggles apply globally** (if auth is on, it's on for both platforms). Sheet includes platform-specific instructions for each rule where the implementation differs between web and mobile.

### Boilerplate: AutoForge Add-On (`autoforge_addon`)

**Stack:** Inherits from AutoForge's existing setup. Uses AutoForge's database via SDK. Uses AutoForge's subscription auth model. No separate auth, no separate database, no payments.

**No toggles needed.** This is a fixed configuration:
- Auth: OFF (uses AutoForge's existing subscription/OAuth)
- Database: OFF as standalone (uses AutoForge's existing Supabase via SDK)  
- Payments: OFF (handled by AutoForge's subscription)
- Special rules: "This module attaches to AutoForge's server at port 8888. Use the existing FastAPI router pattern. Use the existing React component patterns. Follow CLAUDE.md conventions."

**The Exact Reality Sheet for this variant includes:**
- All 192 structural rules adapted for "module within existing app" context
- File paths relative to AutoForge's directory structure
- Import patterns that match AutoForge's existing codebase
- No standalone deployment rules (it deploys WITH AutoForge)

---

## New Boilerplate Flow (Stage 0a Runs)

When a user (or SaaS customer) brings a boilerplate we haven't pre-matched:

### Input
1. The agnostic checklist (192 rules, all generic)
2. The boilerplate's source code (or a summary/manifest of it)

### Process
The Stage 0a agent reads every rule in the agnostic checklist and cross-references it against the boilerplate:

For each rule:
1. **Find the matching implementation** in the boilerplate (file path, code pattern, config setting)
2. **Write the Exact Reality** — not "use the configured database" but "use `supabase.from('table').select('*')`"
3. **Tag the match type:**
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

## Rules (192 total, X active for this variant)

### Category: Stack (Mandatory)
| # | Rule | Exact Implementation | Severity |
|---|------|---------------------|----------|
| 1 | Framework with type safety | Next.js 14 with TypeScript strict mode (`"strict": true` in tsconfig.json) | STANDARD |
| ... | ... | ... | ... |

### Category: File Structure
| # | Rule | Exact Implementation | Severity |
| ... |

[... all 22 categories + banned patterns ...]

## Deactivated Rules (toggled off)
| # | Rule | Reason |
|---|------|--------|
| L-1 | Payment processor | Payments toggle OFF |
| ... | ... | ... |
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

## Sheets We Need to Pre-Build

| # | Sheet Name | Boilerplate | Toggles | Priority |
|---|-----------|-------------|---------|----------|
| 1 | `supabase_web_full` | Supabase Web | DB+Auth+Payments | HIGH |
| 2 | `supabase_web_db_auth` | Supabase Web | DB+Auth | HIGH |
| 3 | `supabase_web_db_only` | Supabase Web | DB only | MEDIUM |
| 4 | `supabase_web_minimal` | Supabase Web | None | LOW |
| 5 | `flutter_mobile_full` | Flutter Mobile | DB+Auth+Payments | HIGH |
| 6 | `flutter_mobile_db_auth` | Flutter Mobile | DB+Auth | HIGH |
| 7 | `flutter_mobile_db_only` | Flutter Mobile | DB only | MEDIUM |
| 8 | `flutter_mobile_minimal` | Flutter Mobile | None | LOW |
| 9 | `dual_full` | Dual | DB+Auth+Payments | MEDIUM |
| 10 | `dual_db_auth` | Dual | DB+Auth | MEDIUM |
| 11 | `autoforge_addon` | AutoForge | Fixed (no toggles) | HIGH |
| 12 | `no_boilerplate_default` | None | DB+Auth (defaults) | HIGH |

**Build order:** Start with #2 (`supabase_web_db_auth`) since that's 80% of builds. Then #11 (`autoforge_addon`), then #1, then #5, then #12.

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
