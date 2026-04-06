# Agent B Handoff: Mobile Boilerplate — ApparenceKit

## Your Assignment

You are a fresh agent. Your ONE job: produce 4 Exact Reality Sheets for the **ApparenceKit Flutter mobile boilerplate** (Flutter + Supabase backend).

**You are NOT building code.** You are producing documentation — structured markdown files that will be injected as preambles into AI agent build sessions.

---

## Your 4 Sheets (Progressive Build Order)

| # | File to Create | DB | Auth | Payments | Build Strategy |
|---|----------------|----|------|----------|----------------|
| 1 | `mobile_base.md` | - | - | - | **Start here.** Flutter scaffold, nothing wired up. Personal apps, phone-only storage. |
| 2 | `mobile_db.md` | ON | - | - | Take sheet 1, wire up Supabase DB (activate Supabase client, data service layer). |
| 3 | `mobile_db_auth.md` | ON | ON | - | Take sheet 2, wire up Supabase Auth (activate auth service, navigation guards). |
| 4 | `mobile_db_auth_payments.md` | ON | ON | ON | Take sheet 3, wire up payments (activate in-app purchases or Stripe). Full SaaS. |

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
- **Repo:** `https://github.com/digisurfsome/apparence-kit-supabase`
- **Docs:** `https://apparencekit.dev/docs/start/overview/`
- **Stack:** Flutter + Supabase backend
- **Focus on:** `pubspec.yaml`, `lib/` directory structure, auth service, database service, navigation patterns, state management (Riverpod or Provider), Supabase client setup

---

## Step 2: Build Each Sheet

### How to Walk Through the Checklists

**Pass 1: Martin's Structural Rules (192 rules)**
Go through `martin-agnostic-checklist.md` rule by rule (all 22 categories). For each rule, find the matching code in the boilerplate and write the exact Flutter/Dart implementation.

**Pass 2: Industry Standards (71 rules)**
Go through `industry-standards-checklist.md` rule by rule (all 10 categories). Find how the boilerplate handles i18n, config externalization, env parity, accessibility, performance, error handling, testing, CI/CD, observability, and API design.

**Pass 3: Mechanism Coverage Matrix (14 categories)**
Go through `mechanism-categories.md` category by category (A-N). Determine if the boilerplate covers it natively, partially, or not at all.

**Pass 4: Banned Patterns (43 patterns)**
Go through the banned patterns section. For each, write the Flutter/Dart-specific detection method.

### Match Tags

- `EXACT` — boilerplate implements this exactly
- `ADAPTED` — principle applies, implementation differs (document how)
- `NOT_PRESENT` — boilerplate doesn't have this; agent builds from scratch
- `PRESENT_NOT_WIRED` — code exists but dormant (for base sheet)
- `NOT_ACTIVATED` — toggled off for this variant

### Progressive Build Strategy

1. **Sheet 1 (`mobile_base`)** — All 263 rules + 14 mechanisms + 43 bans. DB/Auth/Payments tagged `PRESENT_NOT_WIRED`. Most work (~600-800 lines).
2. **Sheet 2 (`mobile_db`)** — Copy sheet 1, change DB rules to active. Document the wiring.
3. **Sheet 3 (`mobile_db_auth`)** — Copy sheet 2, change Auth rules to active. Document the wiring.
4. **Sheet 4 (`mobile_db_auth_payments`)** — Copy sheet 3, change Payments rules to active. Full SaaS.

---

## Step 3: Write the Exact Implementation Column

**Good examples (specific, actionable — use Flutter/Dart, not JS):**

```
Rule: Auth provider sign-in flow
Exact: `await Supabase.instance.client.auth.signInWithOAuth(OAuthProvider.google)` — configured in `lib/src/features/auth/data/auth_repository.dart`, redirect handled by deep link config in `AndroidManifest.xml` and `Info.plist`
```

```
Rule: CRUD helper functions
Exact: Use `lib/src/features/core/data/database_repository.dart` which provides `create(table, data)`, `read(table, filters)`, `update(table, id, data)`, `delete(table, id)`. Uses `Supabase.instance.client.from(table)` internally.
```

**Bad examples (FAIL):**

```
Rule: Auth provider sign-in flow
Exact: Use the auth provider's sign-in method ← USELESS.
```

---

## Output Format

Use this structure for each sheet:

```markdown
# Exact Reality Sheet: [Name]

**Generated:** [date]
**Boilerplate:** ApparenceKit Flutter — https://github.com/digisurfsome/apparence-kit-supabase
**Boilerplate version:** [commit hash]
**Toggles:** DB=[ON/OFF] | Auth=[ON/OFF] | Payments=[ON/OFF]

## Stack Summary
| Field | Value |
|-------|-------|
| Framework | Flutter [version] |
| Database | Supabase/Postgres |
| Auth | Supabase Auth |
| Hosting | App Store / Google Play |
| CSS | Flutter Widgets + Theme |
| State Management | [Riverpod/Provider — check boilerplate] |
| Payments | [Stripe / In-App Purchases or "Not activated"] |

---

## Part 1: Martin's Structural Rules ([X] of 192 active)
[... all 22 categories ...]

## Part 2: Industry Standards ([X] of 71 active)
[... all 10 categories ...]

## Part 3: Mechanism Coverage Matrix (14 categories)
[... all 14 ...]

## Part 4: Banned Patterns (43 total)
[... all 43 ...]

## Deactivated Rules ([Y] rules)
[... toggled-off rules ...]
```

---

## Validation Checklist

- [ ] All 192 Martin rules have an entry
- [ ] All 71 Industry Standards rules have an entry
- [ ] All 14 mechanism categories have an entry
- [ ] All 43 banned patterns have Flutter/Dart-specific enforcement
- [ ] Zero vague instructions
- [ ] File paths match actual boilerplate structure
- [ ] Function names are real (not guessed)
- [ ] Deactivated rules section is complete
- [ ] Stack Summary is accurate
