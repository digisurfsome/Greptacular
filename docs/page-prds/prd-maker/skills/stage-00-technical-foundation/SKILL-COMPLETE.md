---
name: stage-0-technical-foundation
description: Establishes platform profile, resolves structural checklist, maps mechanism categories, emits stage contract before idea capture.
---

## Purpose

Stage 0 is the deterministic preamble that runs BEFORE the user describes their app idea. It locks down the technical environment (framework, database, auth, hosting) so all downstream stages operate against known technical truths. It separates "already handled structure" from "unknown app mechanisms" and emits a contract for Stage 1 entry.

## When to Use

Trigger when: "technical foundation", "platform setup", "stack selection", "initialize pipeline", "start PRD", "new spec", "set up tech stack", or the pipeline begins a new run. This is always the FIRST stage. It produces: platform profile, resolved checklist, structural coverage matrix, mechanism target model, assumption log, question budget, and stage contract.

## Input Format

Stage 0 reads only initialized metadata (no prior stage output exists):

```json
{
  "metadata": {
    "pipeline_version": "1.0.0",
    "created_at": "2026-04-03T12:00:00Z",
    "app_type": "greenfield",
    "status": "in_progress",
    "confidence_scores": {},
    "stage_timestamps": {},
    "escape_hatches": []
  }
}
```

User platform preferences come from the invocation context (chat message or form submission), NOT from a prior stage.

## Process

### Step 1: Context Intake

Present all 5 platform questions at once. User answers together:

1. **New or existing app?** Greenfield (from scratch) or adding to existing codebase?
2. **Platform target?** Web app, mobile app, or both?
3. **Target stack?** Preferred framework/database/auth provider, or should I recommend?
4. **Repo source?** New repo, using a boilerplate, or existing repo?
5. **Deployment target?** Vercel, AWS, self-hosted, or undecided?

Record confidence for each answer: `known` (user stated), `inferred` (derived from other answers), `assumed` (default applied because user did not answer).

**Low-input rule:** If user provides no answers or says "I don't know," auto-fill ALL fields with defaults. Log every default as an assumption with confidence, reversal cost, and source. Never block progress waiting for answers.

### Step 2: Boilerplate/Profile Resolution

Select exactly one profile based on intake. See `references/boilerplate-profiles.md` for full definitions.

| Profile ID | When to Select |
|------------|---------------|
| `supabase_web` | Greenfield + web + no strong preference **(DEFAULT)** |
| `flutter_mobile` | Mobile-only or mobile-first |
| `dual` | User explicitly wants web + mobile |
| `no_boilerplate` | User has a specific non-standard stack |
| `raw_checklist` | Existing app or bring-your-own architecture |

Default rule: If profile unknown after intake, assign `supabase_web` and log the assumption.

### Step 3: Martin Rules Preamble Injection

Load the agnostic checklist (`martin-agnostic-checklist.md`, ~192 rules, 22 categories, 43 banned patterns) and the industry standards supplement (`industry-standards-checklist.md`, 71 rules, 10 categories). Resolve each rule against the selected profile. See `references/rule-resolution-guide.md`.

| Resolution | Meaning |
|-----------|---------|
| `MATCH` | Applies as-is. Carry unchanged. |
| `REPLACE` | Principle applies, implementation differs for this stack. |
| `ENHANCE` | Keep rule AND add boilerplate-specific file pointers. |
| `HANDLED` | Boilerplate already implements this. Lock as "do not recreate." |
| `N/A` | Not relevant to this profile. |

Per rule, also assign:
- `priority`: `critical` | `important` | `nice`
- `enforcement`: `hard` (non-negotiable) | `soft` (recommendation)
- `evidence`: file path, config, or test artifact satisfying the rule (if applicable)

**Hard constraints (always `enforcement: "hard"`):** Build hygiene, structure, naming discipline, anti-pattern bans, security, auth boundaries, state/data handling consistency, deterministic component and testing standards.

**Soft guidance (always `enforcement: "soft"`):** Feature count limits, provider-specific assumptions. These become recommendations with logged justification.

### Step 4: Structural Target Model (30 Categories)

Instantiate the 30-category coverage matrix. See `references/structural-categories.md` for the full list (22 Martin categories + 10 industry gap areas − 2 overlaps = 30).

For each category, mark status:
- `covered_by_preamble` — boilerplate + resolved rules handle it
- `provided_by_user` — user addressed in intake answers
- `missing` — must be resolved in later stages

### Step 5: Mechanism Target Model (A-N)

Instantiate the 14 mechanism categories. See `references/mechanism-categories.md` for definitions and per-profile boilerplate coverage defaults.

For each category, mark:
- `covered_by_boilerplate` — boilerplate natively handles this mechanism
- `needs_user_input` — requires user decisions during idea capture / gap analysis
- `not_applicable` — definitively not relevant (rare at Stage 0)

Note: At Stage 0, the user has NOT described their idea. Most categories will be `needs_user_input`. Typically only B (Data Storage), E (Authentication), and N (Infrastructure) may be `covered_by_boilerplate` depending on the profile.

### Step 6: Question Budget + Clarification Strategy

Determine question strategy for the entire pipeline:

| Input Level | Mode | Max Rounds | Blocking Only | Strategy |
|-------------|------|------------|---------------|----------|
| All 5 questions answered with specifics | `full_detail` | 2 | true | Ask only blocking questions downstream |
| 2-3 questions answered | `minimal_input` | 3 | false | Fill gaps with defaults + assumption log |
| Zero answers or "just build something" | `zero_input` | 0 | true | Fill ALL fields deterministically. Zero questions. |

See `references/default-assumptions.md` for the complete zero-input default set.

### Step 7: Stage Contract Emission

Emit completion contract:

- **Goal:** Platform context fully established
- **Exit artifacts:** `platform_profile`, `tech_stack`, `checklist_rule_ids`, `resolved_rules`, `structural_coverage`, `mechanism_target`, `assumptions`, `question_budget`
- **Quality gates:** All required fields populated, no `"TBD"` values, `boilerplate_id` exists in supported set, no contradictions between fields
- **Stop/go:** `go` if score ≥ 90, `conditional` if 70-89, `stop` if < 70

Also initialize (even if mostly empty at this stage):
- `nfr_budgets` — latency, reliability, cost, scale, security, maintainability targets
- `data_governance` — PII handling, retention, auditability, regional constraints
- `observability_requirements` — required logs, metrics, traces, alert thresholds
- `out_of_scope` — explicitly stated exclusions from this build pass

## Output Format

Write to `context_packet.stage_0`:

```json
{
  "platform_profile": {
    "boilerplate_id": "supabase_web|flutter_mobile|dual|no_boilerplate|raw_checklist",
    "boilerplate_name": "string",
    "description": "string"
  },
  "tech_stack": {
    "framework": "string (e.g. 'Next.js 14')",
    "database": "string (e.g. 'Supabase/Postgres')",
    "auth_provider": "string (e.g. 'Supabase Auth')",
    "hosting": "string (e.g. 'Vercel')",
    "additional": {}
  },
  "checklist_rule_ids": ["string — rule IDs that apply to this stack (see Rule ID Naming Convention below)"],
  "command_allowlist": ["string — allowed bash commands"],
  "resolved_rules": [{
    "rule_id": "string (see Rule ID Naming Convention below)",
    "resolution": "MATCH|REPLACE|ENHANCE|HANDLED|N/A",
    "priority": "critical|important|nice",
    "enforcement": "hard|soft",
    "evidence": "string|null"
  }],
  "structural_coverage": {
    "categories": [{
      "name": "string",
      "status": "covered_by_preamble|provided_by_user|missing"
    }]
  },
  "mechanism_target": {
    "categories": [{
      "id": "A|B|C|D|E|F|G|H|I|J|K|L|M|N",
      "name": "string",
      "status": "covered_by_boilerplate|needs_user_input|not_applicable"
    }]
  },
  "assumptions": [{
    "field": "string — which field was assumed",
    "value": "string — the assumed value",
    "confidence": "known|inferred|assumed",
    "reversal_cost": "low|medium|high",
    "source": "string — why this assumption was made"
  }],
  "question_budget": {
    "mode": "full_detail|minimal_input|zero_input",
    "max_rounds": "integer (0-3)",
    "blocking_questions_only": "boolean"
  },
  "stage_contract": {
    "stop_go": "go|conditional|stop",
    "unresolved_blockers": ["string — empty if go"]
  },
  "nfr_budgets": { "latency": null, "reliability": null, "cost": null, "scale": null, "security": null, "maintainability": null },
  "data_governance": { "pii_handling": null, "retention": null, "auditability": null, "regional_constraints": null },
  "observability_requirements": { "logs": null, "metrics": null, "traces": null, "alert_thresholds": null },
  "out_of_scope": ["string"]
}
```

Also update `metadata`:

```json
{
  "metadata.current_stage": 0,
  "metadata.updated_at": "ISO 8601",
  "metadata.confidence_scores.0": { "score": 92, "dimensions": { "completeness": 19, "accuracy": 18, "consistency": 20, "specificity": 17, "handoff_readiness": 18 }, "gate_result": "pass" },
  "metadata.stage_timestamps.0": "ISO 8601"
}
```

### Validation Before Writing

1. All required output fields populated — no `null`, no `"TBD"`
2. `boilerplate_id` is one of: `supabase_web`, `flutter_mobile`, `dual`, `no_boilerplate`, `raw_checklist`
3. `tech_stack` fields internally consistent (no contradictions like Supabase profile with Firebase auth)
4. Every assumption has all 5 metadata fields: `field`, `value`, `confidence`, `reversal_cost`, `source`
5. Run confidence scoring (see below)
6. Score < 70 → trigger escape hatch, do NOT write
7. Score 70-89 → write with `gate_result: "flag"`
8. Score ≥ 90 → write with `gate_result: "pass"`

### Rule ID Naming Convention

Rule IDs in `checklist_rule_ids` and `resolved_rules[].rule_id` follow the format `{category-prefix}-{sequential-number}`, where:

1. **Category prefix**: A short kebab-case abbreviation derived from the checklist category name. The 22 Martin categories and their prefixes:

| # | Category | Prefix | Example IDs |
|---|----------|--------|-------------|
| 1 | Stack Definition | `stack` | `stack-1`, `stack-2` |
| 2 | File Structure | `file` | `file-1`, `file-2` |
| 3 | Component Architecture | `comp` | `comp-1`, `comp-2` |
| 4 | State Management | `state` | `state-1`, `state-2` |
| 5 | Routing | `route` | `route-1`, `route-2` |
| 6 | Styling | `style` | `style-1`, `style-2` |
| 7 | Data Fetching | `fetch` | `fetch-1`, `fetch-2` |
| 8 | Auth & Security | `auth` | `auth-1`, `auth-2` |
| 9 | Forms & Validation | `form` | `form-1`, `form-2` |
| 10 | Error Handling | `error` | `error-1`, `error-2` |
| 11 | Testing | `test` | `test-1`, `test-2` |
| 12 | Build & Bundle | `build` | `build-1`, `build-2` |
| 13 | Type Safety | `type` | `type-1`, `type-2` |
| 14 | Code Quality | `quality` | `quality-1`, `quality-2` |
| 15 | Git & Version Control | `git` | `git-1`, `git-2` |
| 16 | Environment Config | `env` | `env-1`, `env-2` |
| 17 | Performance | `perf` | `perf-1`, `perf-2` |
| 18 | SEO | `seo` | `seo-1`, `seo-2` |
| 19 | Analytics & Monitoring | `analytics` | `analytics-1`, `analytics-2` |
| 20 | Deployment | `deploy` | `deploy-1`, `deploy-2` |
| 21 | Documentation | `docs` | `docs-1`, `docs-2` |
| 22 | Banned Patterns | `ban` | `ban-1`, `ban-2`, ... `ban-43` |

The 10 industry standards gap areas (categories 23-30) use prefixes derived from their area name. Rule numbers in the source checklist start at 200:

| # | Category | Prefix | Source Rule Range |
|---|----------|--------|-------------------|
| 23 | Internationalization (i18n) | `i18n` | 200-207 |
| 24 | Config Externalization | `config` | 208-214 |
| 25 | Environment Parity | `parity` | 215-220 |
| 26 | Logging Strategy | `log` | 221-228 |
| 27 | Dependency Management | `deps` | 229-235 |
| 28 | Legal/Compliance | `legal` | 236-243 |
| 29 | Deep Accessibility (WCAG AA) | `a11y` | 244-253 |
| 30 | API Versioning | `api-ver` | 254-258 |

2. **Sequential number**: Rules are numbered sequentially within each category, starting at 1. The number corresponds to the row position within that category's section in the source checklist (e.g., the 3rd rule in category 8 "Auth & Security" becomes `auth-3`).

3. **Examples**: Checklist row #1 in "Stack Definition" -> `stack-1`. The 1st rule in "Auth & Security" -> `auth-1`. The 15th banned pattern -> `ban-15`. Industry standards rule 201 (the 2nd i18n rule) -> `i18n-2`.

## Edge Cases

### Missing Input (Zero-Input User)

Auto-fill ALL fields with deterministic defaults. Profile: `supabase_web`. Stack: Next.js 14 + Supabase/Postgres + Supabase Auth + Vercel. Log every field as assumption with `confidence: "assumed"`. Set `question_budget.mode: "zero_input"`, `max_rounds: 0`. Proceed without blocking. See `references/default-assumptions.md`.

### Ambiguous Input (Contradictory Preferences)

Example: user says "mobile-only" AND "server-side rendering." Present conflict: "Mobile-only apps don't use SSR. Which is your priority?" If no response within timeout, select the first-stated preference, log as assumption with `reversal_cost: "high"`, and add to `stage_contract.unresolved_blockers`.

### Unsupported Stack Request

If user requests a stack not in profiles (e.g., "Deno + MongoDB"), assign `no_boilerplate`, map requested stack to `tech_stack` fields, resolve checklist rules against generic patterns. If stack is truly unknown AND user refuses alternatives, trigger escape hatch.

### Scope Overflow (User Describes App Idea)

If user starts describing their app idea during Stage 0, save the text to `metadata.early_idea_capture` for Stage 1. Redirect: "I'll save that for the next step. Right now I need to lock down your tech stack." Continue with platform questions only. Do NOT analyze the idea.

### Existing App (app_type = "existing")

Set profile to `raw_checklist`. Log that existing app analysis is a future feature. Proceed with checklist resolution against the user's stated stack. Flag `stage_contract.unresolved_blockers: ["existing_app_analysis_not_yet_supported"]`.

## Confidence Scoring

After producing output, score each dimension 0-20:

| Dimension | 0-5 | 6-10 | 11-15 | 16-20 |
|-----------|-----|------|-------|-------|
| **Completeness** | 3+ fields empty/TBD | 1-2 fields missing; boilerplate_id present but mechanism coverage incomplete | All fields populated; minor gaps in structural_coverage or mechanism_target | All fields populated; structural_coverage covers all 30 categories; mechanism_target covers A-N |
| **Accuracy** | Stack doesn't exist or framework/database incompatible | Stack exists, version or config wrong | Stack valid and compatible; minor config details unspecified | Stack valid, compatible, version-correct, config matches boilerplate exactly |
| **Consistency** | Fields contradict (e.g., Next.js framework + Firebase Auth on Supabase profile) | Minor mismatches, one clarification needed | Internally consistent, no contradictions | All fields align — framework, database, auth, hosting form a coherent stack |
| **Specificity** | Vague values ("a database", "some framework") | Named tech without version/config | Exact tech + versions; mechanism categories use A-N codes | Tech + version + config; mechanism coverage includes capability notes |
| **Handoff Readiness** | Stage 1 must ask "what stack?" | Stage 2 must guess DB patterns | Platform context clear for Stage 2 | All downstream stages reference platform_profile without ambiguity |

**Total = sum of 5 dimensions (/100)**

- ≥ 90: **PASS** — proceed to Stage 1
- 70-89: **FLAG** — proceed with warning in metadata
- < 70: **FAIL** — trigger escape hatch, do NOT pass output forward

## Escape Hatch

**Trigger when:**
- User requests unsupported stack AND refuses closest alternative
- Confidence score < 70 after one retry
- Contradictory preferences that cannot be auto-resolved (e.g., "mobile-only" + "SSR")
- `app_type: "existing"` and existing app analysis is required but not yet supported

**Save:**
- Current `context_packet` with partial `stage_0` data
- Stage number (0) and step number where halt occurred
- What was attempted and what failed
- Suggested questions for human resolution

**Signal:**
- Set `metadata.status = "needs_human"`
- Append to `metadata.escape_hatches`:
  ```json
  { "stage": 0, "step": 2, "reason": "Unsupported stack requested", "attempted": "Offered supabase_web as alternative", "suggested_actions": ["Choose a supported profile", "Provide specific framework details for no_boilerplate profile"] }
  ```
- Save context packet snapshot to disk
- Output structured NEEDS_HUMAN message with the specific problem and suggested actions

## Example

See `references/example-output.md` for complete input→output examples covering both scenarios:

**Full-input:** User answers all 5 questions ("Greenfield web app, Next.js + Supabase, new repo, Vercel"). Result: `supabase_web` profile, all fields `known`, `full_detail` budget, score 96, gate `pass`.

**Zero-input:** User says "just help me build something." Result: `supabase_web` default, all fields `assumed`, `zero_input` budget, 12 assumptions logged with reversal costs, score 92, gate `pass`.


---
## REFERENCE: Boilerplate Profiles

# Boilerplate Profiles Reference

> 5 supported profiles with their default stacks, capabilities, and mechanism coverage.

---

## Profile: `supabase_web`

**Name:** Supabase Web Starter
**Description:** Next.js + Supabase + Vercel stack with auth, database, and hosting pre-configured.
**When to select:** Greenfield + web-only or web-first + no strong stack preference. This is the DEFAULT profile.

| Field | Value |
|-------|-------|
| Framework | Next.js 14 (App Router) |
| Database | Supabase/Postgres |
| Auth Provider | Supabase Auth (email/password + OAuth) |
| Hosting | Vercel |
| CSS/Styling | Tailwind CSS |
| ORM/Query | Supabase client SDK |
| File Storage | Supabase Storage |

**Mechanism Coverage (what the boilerplate handles natively):**

| Category | Status | Notes |
|----------|--------|-------|
| A - Data Input | needs_user_input | Forms depend on app idea |
| B - Data Storage | covered_by_boilerplate | Supabase/Postgres + Storage |
| C - Data Processing | needs_user_input | App-specific logic |
| D - Data Output | needs_user_input | App-specific views |
| E - Authentication | covered_by_boilerplate | Supabase Auth |
| F - Authorization | covered_by_boilerplate | Row Level Security (RLS) |
| G - Communication | needs_user_input | Not included in base |
| H - Integration | needs_user_input | App-specific |
| I - Workflow | needs_user_input | App-specific |
| J - Search & Discovery | needs_user_input | Postgres full-text search available |
| K - Collaboration | needs_user_input | App-specific |
| L - Monetization | needs_user_input | Not included in base |
| M - Admin/Ops | needs_user_input | Not included in base |
| N - Infrastructure | covered_by_boilerplate | Vercel + Supabase managed hosting |

**Command Allowlist:** `npm`, `npx`, `git`, `node`, `curl`, `next`, `supabase`

---

## Profile: `flutter_mobile`

**Name:** Flutter Mobile + Supabase
**Description:** Flutter for mobile UI + Supabase backend for auth, database, and storage.
**When to select:** Mobile-only or mobile-first projects.

| Field | Value |
|-------|-------|
| Framework | Flutter (latest stable) |
| Database | Supabase/Postgres |
| Auth Provider | Supabase Auth |
| Hosting | App stores (iOS/Android) + Supabase backend |
| CSS/Styling | Flutter Material/Cupertino widgets |
| ORM/Query | Supabase Dart SDK |
| File Storage | Supabase Storage |

**Mechanism Coverage:**

| Category | Status | Notes |
|----------|--------|-------|
| A - Data Input | needs_user_input | Mobile-specific input patterns |
| B - Data Storage | covered_by_boilerplate | Supabase/Postgres |
| C - Data Processing | needs_user_input | App-specific |
| D - Data Output | needs_user_input | App-specific |
| E - Authentication | covered_by_boilerplate | Supabase Auth (mobile SDK) |
| F - Authorization | covered_by_boilerplate | RLS |
| G - Communication | needs_user_input | Push notifications need setup |
| H - Integration | needs_user_input | App-specific |
| I - Workflow | needs_user_input | App-specific |
| J - Search & Discovery | needs_user_input | App-specific |
| K - Collaboration | needs_user_input | App-specific |
| L - Monetization | needs_user_input | In-app purchases need setup |
| M - Admin/Ops | needs_user_input | Not included in base |
| N - Infrastructure | covered_by_boilerplate | Supabase managed backend |

**Command Allowlist:** `flutter`, `dart`, `git`, `curl`, `supabase`, `pod` (iOS)

---

## Profile: `dual`

**Name:** Dual Web + Mobile + Supabase
**Description:** Next.js web app + Flutter mobile app sharing a Supabase backend.
**When to select:** User explicitly wants both web and mobile clients.

| Field | Value |
|-------|-------|
| Framework | Next.js 14 (web) + Flutter (mobile) |
| Database | Supabase/Postgres |
| Auth Provider | Supabase Auth |
| Hosting | Vercel (web) + App stores (mobile) + Supabase (backend) |
| CSS/Styling | Tailwind CSS (web) + Flutter widgets (mobile) |
| ORM/Query | Supabase client SDK (JS + Dart) |
| File Storage | Supabase Storage |

**Mechanism Coverage:** Same as `supabase_web` (B, E, F, N covered). Mobile-specific concerns (push notifications, app store requirements) are flagged as additional needs in assumptions.

**Command Allowlist:** `npm`, `npx`, `git`, `node`, `curl`, `next`, `supabase`, `flutter`, `dart`, `pod`

---

## Profile: `no_boilerplate`

**Name:** No Boilerplate (Custom Stack)
**Description:** User has a specific stack not covered by supported boilerplates. Checklist rules still apply but no boilerplate file pointers exist.
**When to select:** User requests a non-standard stack (e.g., Django + PostgreSQL, Rails + MySQL, SvelteKit + Firebase).

| Field | Value |
|-------|-------|
| Framework | User-specified |
| Database | User-specified |
| Auth Provider | User-specified |
| Hosting | User-specified |
| CSS/Styling | User-specified |
| ORM/Query | User-specified |
| File Storage | User-specified |

**Mechanism Coverage:** All categories are `needs_user_input`. No boilerplate assumptions.

**Command Allowlist:** `git`, `curl` + user-specified tools

---

## Profile: `raw_checklist`

**Name:** Raw Checklist Only
**Description:** Existing app or bring-your-own architecture. The structural checklist applies but is resolved in CHECK mode against the existing codebase rather than a boilerplate.
**When to select:** `app_type: "existing"` or user is adding features to an existing project.

| Field | Value |
|-------|-------|
| Framework | Determined by existing codebase |
| Database | Determined by existing codebase |
| Auth Provider | Determined by existing codebase |
| Hosting | Determined by existing codebase |

**Mechanism Coverage:** All categories are `needs_user_input` until codebase analysis is supported (future feature).

**Command Allowlist:** Determined by existing project configuration

**Note:** Existing app analysis (codebase scanning, dependency detection) is a future feature. For now, the user must manually specify their stack, and it is recorded as assumptions.


---
## REFERENCE: Default Assumptions

# Default Assumptions Reference

> Complete set of defaults for zero-input users. Every default is logged as an assumption with confidence level and reversal cost.

---

## Zero-Input Default Set

When the user provides no answers or says "I don't know" / "just build something," ALL of the following are applied:

| # | Field | Default Value | Confidence | Reversal Cost | Source |
|---|-------|--------------|------------|---------------|--------|
| 1 | `metadata.app_type` | `greenfield` | assumed | high | No existing codebase indicated |
| 2 | `platform_profile.boilerplate_id` | `supabase_web` | assumed | medium | Lowest-risk, highest-coverage default for web apps |
| 3 | `tech_stack.framework` | `Next.js 14` | assumed | medium | Default web framework for supabase_web profile |
| 4 | `tech_stack.database` | `Supabase/Postgres` | assumed | high | Core data layer for supabase_web profile |
| 5 | `tech_stack.auth_provider` | `Supabase Auth` | assumed | medium | Native auth for supabase_web profile |
| 6 | `tech_stack.hosting` | `Vercel` | assumed | low | Default hosting for Next.js apps |
| 7 | Platform target | Web only | assumed | medium | Web is the most common starting platform |
| 8 | Repo source | New repo | assumed | low | Greenfield implies new repo |
| 9 | CSS/Styling | Tailwind CSS | assumed | low | Included in supabase_web boilerplate |
| 10 | Payment processor | Stripe (deferred) | assumed | low | Only activated if monetization signal appears in later stages |
| 11 | AI/Tooling | Claude Code | assumed | low | Running within this pipeline |
| 12 | `question_budget.mode` | `zero_input` | assumed | low | No user input provided |

---

## Reversal Cost Definitions

| Cost | Meaning | Examples |
|------|---------|----------|
| `low` | Can change later with minimal rework. Affects config or tooling only. | Hosting provider, CSS framework, repo setup |
| `medium` | Changing requires moderate rework. Affects code patterns and file structure. | Framework change (Next.js → SvelteKit), auth provider swap |
| `high` | Changing requires significant rework. Affects data model, auth, or core architecture. | Database engine change, greenfield → existing app, platform target change |

---

## Partial-Input Inference Rules

When the user answers some questions but not others, use these inference rules:

| User Says | Inference | Confidence |
|-----------|-----------|------------|
| "Web app" (no framework preference) | Framework: Next.js 14 | inferred |
| "Mobile app" (no framework preference) | Framework: Flutter | inferred |
| "Both web and mobile" | Profile: dual | known |
| "I want to use React" | Framework: Next.js 14 (React-based) | inferred |
| "I want to use Vue" | Profile: no_boilerplate, Framework: Nuxt.js | inferred |
| "I want to use Firebase" | Profile: no_boilerplate, Database: Firebase/Firestore, Auth: Firebase Auth | known |
| "Deploy to AWS" | Hosting: AWS | known |
| "I have an existing app" | Profile: raw_checklist, app_type: existing | known |
| "I don't care about the stack" | Apply full zero-input defaults | assumed |

---

## Question Budget Defaults

| Mode | Max Rounds | Blocking Only | Downstream Behavior |
|------|------------|---------------|---------------------|
| `full_detail` | 2 | true | Stages 2-9 ask only questions that block progress |
| `minimal_input` | 3 | false | Stages 2-9 fill gaps with defaults, ask 1-3 rounds |
| `zero_input` | 0 | true | Stages 2-9 fill ALL gaps with defaults, ask 0 questions |

After `max_rounds` of unanswered questions across the entire pipeline, the system auto-fills remaining gaps with deterministic defaults and proceeds.


---
## REFERENCE: Example Output

# Example Output Reference

> Two complete input→output scenarios for Stage 0.

---

## Scenario 1: Full-Input User

### Input

User answers all 5 platform questions:

> 1. Greenfield app — starting from scratch.
> 2. Web app only.
> 3. I want Next.js with Supabase for the database and auth.
> 4. New repo, using the Supabase starter.
> 5. Deploy to Vercel.

### Output: `context_packet.stage_0`

```json
{
  "platform_profile": {
    "boilerplate_id": "supabase_web",
    "boilerplate_name": "Supabase Web Starter",
    "description": "Next.js + Supabase + Vercel stack with auth, database, and hosting pre-configured"
  },
  "tech_stack": {
    "framework": "Next.js 14",
    "database": "Supabase/Postgres",
    "auth_provider": "Supabase Auth",
    "hosting": "Vercel",
    "additional": {}
  },
  "checklist_rule_ids": ["stack-1", "stack-2", "file-1", "file-2", "comp-1", "...all applicable rule IDs"],
  "command_allowlist": ["npm", "npx", "git", "node", "curl", "next", "supabase"],
  "resolved_rules": [
    { "rule_id": "stack-1", "resolution": "HANDLED", "priority": "critical", "enforcement": "hard", "evidence": "boilerplate: package.json defines Next.js 14 + Supabase" },
    { "rule_id": "auth-1", "resolution": "HANDLED", "priority": "critical", "enforcement": "hard", "evidence": "boilerplate: src/lib/supabase.ts provides auth client" },
    { "rule_id": "comp-1", "resolution": "MATCH", "priority": "important", "enforcement": "hard", "evidence": null },
    { "rule_id": "ban-1", "resolution": "MATCH", "priority": "critical", "enforcement": "hard", "evidence": null }
  ],
  "structural_coverage": {
    "categories": [
      { "name": "Stack Definition", "status": "covered_by_preamble" },
      { "name": "File Structure", "status": "covered_by_preamble" },
      { "name": "Component Architecture", "status": "covered_by_preamble" },
      { "name": "State Management", "status": "covered_by_preamble" },
      { "name": "Routing", "status": "covered_by_preamble" },
      { "name": "Styling", "status": "covered_by_preamble" },
      { "name": "Data Fetching", "status": "covered_by_preamble" },
      { "name": "Auth & Security", "status": "covered_by_preamble" },
      { "name": "Forms & Validation", "status": "missing" },
      { "name": "Error Handling", "status": "missing" },
      { "name": "Testing", "status": "missing" },
      { "name": "Build & Bundle", "status": "covered_by_preamble" },
      { "name": "Type Safety", "status": "covered_by_preamble" },
      { "name": "Code Quality", "status": "missing" },
      { "name": "Git & Version Control", "status": "missing" },
      { "name": "Environment Config", "status": "covered_by_preamble" },
      { "name": "Performance", "status": "missing" },
      { "name": "SEO", "status": "missing" },
      { "name": "Analytics & Monitoring", "status": "missing" },
      { "name": "Deployment", "status": "covered_by_preamble" },
      { "name": "Documentation", "status": "missing" },
      { "name": "Banned Patterns", "status": "covered_by_preamble" },
      { "name": "Internationalization", "status": "missing" },
      { "name": "Config Externalization", "status": "covered_by_preamble" },
      { "name": "Environment Parity", "status": "missing" },
      { "name": "Logging Strategy", "status": "missing" },
      { "name": "Dependency Management", "status": "missing" },
      { "name": "Legal/Compliance", "status": "missing" },
      { "name": "Deep Accessibility", "status": "missing" },
      { "name": "API Versioning", "status": "missing" }
    ]
  },
  "mechanism_target": {
    "categories": [
      { "id": "A", "name": "Data Input", "status": "needs_user_input" },
      { "id": "B", "name": "Data Storage", "status": "covered_by_boilerplate" },
      { "id": "C", "name": "Data Processing", "status": "needs_user_input" },
      { "id": "D", "name": "Data Output", "status": "needs_user_input" },
      { "id": "E", "name": "Authentication", "status": "covered_by_boilerplate" },
      { "id": "F", "name": "Authorization", "status": "covered_by_boilerplate" },
      { "id": "G", "name": "Communication", "status": "needs_user_input" },
      { "id": "H", "name": "Integration", "status": "needs_user_input" },
      { "id": "I", "name": "Workflow", "status": "needs_user_input" },
      { "id": "J", "name": "Search & Discovery", "status": "needs_user_input" },
      { "id": "K", "name": "Collaboration", "status": "needs_user_input" },
      { "id": "L", "name": "Monetization", "status": "needs_user_input" },
      { "id": "M", "name": "Admin/Ops", "status": "needs_user_input" },
      { "id": "N", "name": "Infrastructure", "status": "covered_by_boilerplate" }
    ]
  },
  "assumptions": [
    { "field": "tech_stack.additional.css", "value": "Tailwind CSS", "confidence": "inferred", "reversal_cost": "low", "source": "Included in supabase_web boilerplate" }
  ],
  "question_budget": {
    "mode": "full_detail",
    "max_rounds": 2,
    "blocking_questions_only": true
  },
  "stage_contract": {
    "stop_go": "go",
    "unresolved_blockers": []
  },
  "nfr_budgets": { "latency": null, "reliability": null, "cost": null, "scale": null, "security": null, "maintainability": null },
  "data_governance": { "pii_handling": null, "retention": null, "auditability": null, "regional_constraints": null },
  "observability_requirements": { "logs": null, "metrics": null, "traces": null, "alert_thresholds": null },
  "out_of_scope": []
}
```

### Metadata Updates

```json
{
  "current_stage": 0,
  "updated_at": "2026-04-03T12:05:00Z",
  "confidence_scores": {
    "0": {
      "score": 96,
      "dimensions": {
        "completeness": 20,
        "accuracy": 19,
        "consistency": 20,
        "specificity": 18,
        "handoff_readiness": 19
      },
      "gate_result": "pass"
    }
  },
  "stage_timestamps": {
    "0": "2026-04-03T12:05:00Z"
  }
}
```

---

## Scenario 2: Zero-Input User

### Input

User says: "Just help me build something. I don't know anything about tech stacks."

No platform questions answered.

### Output: `context_packet.stage_0`

```json
{
  "platform_profile": {
    "boilerplate_id": "supabase_web",
    "boilerplate_name": "Supabase Web Starter",
    "description": "Next.js + Supabase + Vercel stack with auth, database, and hosting pre-configured"
  },
  "tech_stack": {
    "framework": "Next.js 14",
    "database": "Supabase/Postgres",
    "auth_provider": "Supabase Auth",
    "hosting": "Vercel",
    "additional": { "css": "Tailwind CSS" }
  },
  "checklist_rule_ids": ["stack-1", "stack-2", "file-1", "...all applicable rule IDs"],
  "command_allowlist": ["npm", "npx", "git", "node", "curl", "next", "supabase"],
  "resolved_rules": [
    { "rule_id": "stack-1", "resolution": "HANDLED", "priority": "critical", "enforcement": "hard", "evidence": "boilerplate: package.json defines stack" },
    { "rule_id": "comp-1", "resolution": "MATCH", "priority": "important", "enforcement": "hard", "evidence": null }
  ],
  "structural_coverage": {
    "categories": [
      { "name": "Stack Definition", "status": "covered_by_preamble" },
      { "name": "File Structure", "status": "covered_by_preamble" },
      { "name": "Auth & Security", "status": "covered_by_preamble" },
      { "name": "Forms & Validation", "status": "missing" },
      { "name": "Testing", "status": "missing" }
    ]
  },
  "mechanism_target": {
    "categories": [
      { "id": "A", "name": "Data Input", "status": "needs_user_input" },
      { "id": "B", "name": "Data Storage", "status": "covered_by_boilerplate" },
      { "id": "C", "name": "Data Processing", "status": "needs_user_input" },
      { "id": "D", "name": "Data Output", "status": "needs_user_input" },
      { "id": "E", "name": "Authentication", "status": "covered_by_boilerplate" },
      { "id": "F", "name": "Authorization", "status": "covered_by_boilerplate" },
      { "id": "G", "name": "Communication", "status": "needs_user_input" },
      { "id": "H", "name": "Integration", "status": "needs_user_input" },
      { "id": "I", "name": "Workflow", "status": "needs_user_input" },
      { "id": "J", "name": "Search & Discovery", "status": "needs_user_input" },
      { "id": "K", "name": "Collaboration", "status": "needs_user_input" },
      { "id": "L", "name": "Monetization", "status": "needs_user_input" },
      { "id": "M", "name": "Admin/Ops", "status": "needs_user_input" },
      { "id": "N", "name": "Infrastructure", "status": "covered_by_boilerplate" }
    ]
  },
  "assumptions": [
    { "field": "metadata.app_type", "value": "greenfield", "confidence": "assumed", "reversal_cost": "high", "source": "No existing codebase indicated" },
    { "field": "platform_profile.boilerplate_id", "value": "supabase_web", "confidence": "assumed", "reversal_cost": "medium", "source": "Lowest-risk default for web apps" },
    { "field": "tech_stack.framework", "value": "Next.js 14", "confidence": "assumed", "reversal_cost": "medium", "source": "Default web framework for supabase_web profile" },
    { "field": "tech_stack.database", "value": "Supabase/Postgres", "confidence": "assumed", "reversal_cost": "high", "source": "Core data layer for supabase_web profile" },
    { "field": "tech_stack.auth_provider", "value": "Supabase Auth", "confidence": "assumed", "reversal_cost": "medium", "source": "Native auth for supabase_web profile" },
    { "field": "tech_stack.hosting", "value": "Vercel", "confidence": "assumed", "reversal_cost": "low", "source": "Default hosting for Next.js apps" },
    { "field": "platform_target", "value": "web", "confidence": "assumed", "reversal_cost": "medium", "source": "Web is most common starting platform" },
    { "field": "repo_source", "value": "new_repo", "confidence": "assumed", "reversal_cost": "low", "source": "Greenfield implies new repo" },
    { "field": "tech_stack.additional.css", "value": "Tailwind CSS", "confidence": "assumed", "reversal_cost": "low", "source": "Included in supabase_web boilerplate" },
    { "field": "payment_processor", "value": "Stripe (deferred)", "confidence": "assumed", "reversal_cost": "low", "source": "Only activated if monetization signal in later stages" },
    { "field": "tooling", "value": "Claude Code", "confidence": "assumed", "reversal_cost": "low", "source": "Running within this pipeline" },
    { "field": "question_budget.mode", "value": "zero_input", "confidence": "assumed", "reversal_cost": "low", "source": "No user input provided" }
  ],
  "question_budget": {
    "mode": "zero_input",
    "max_rounds": 0,
    "blocking_questions_only": true
  },
  "stage_contract": {
    "stop_go": "go",
    "unresolved_blockers": []
  },
  "nfr_budgets": { "latency": null, "reliability": null, "cost": null, "scale": null, "security": null, "maintainability": null },
  "data_governance": { "pii_handling": null, "retention": null, "auditability": null, "regional_constraints": null },
  "observability_requirements": { "logs": null, "metrics": null, "traces": null, "alert_thresholds": null },
  "out_of_scope": []
}
```

### Metadata Updates

```json
{
  "current_stage": 0,
  "updated_at": "2026-04-03T12:02:00Z",
  "confidence_scores": {
    "0": {
      "score": 92,
      "dimensions": {
        "completeness": 19,
        "accuracy": 18,
        "consistency": 20,
        "specificity": 17,
        "handoff_readiness": 18
      },
      "gate_result": "pass"
    }
  },
  "stage_timestamps": {
    "0": "2026-04-03T12:02:00Z"
  }
}
```

### Why Score is 92 (not higher)

- **Specificity: 17** — All tech is specified but since everything is assumed, capability notes are minimal.
- **Accuracy: 18** — Defaults are valid and compatible, but without user confirmation, there's inherent uncertainty.
- **Completeness: 19** — All fields populated, but structural_coverage has many "missing" categories (expected at Stage 0).
- The score is still ≥ 90 because the defaults form a coherent, valid stack and the assumption log is complete.


---
## REFERENCE: Mechanism Categories

# Mechanism Categories Reference (A-N)

> 14 mechanism categories from the Mechanism Identification Framework.
> Stage 0 instantiates these as a target model. Each category is tagged with boilerplate coverage status.

---

## Categories

| ID | Name | Description |
|----|------|-------------|
| A | Data Input | How data enters the system (forms, file upload, voice, camera, drag-and-drop, sensors, import) |
| B | Data Storage | How and where data persists (relational DB, NoSQL, blob storage, cache, search index, audit trail) |
| C | Data Processing | Transformations and logic applied to data (validation, calculations, AI/ML, batch, format conversion) |
| D | Data Output | How data is displayed or delivered (lists, charts, maps, timelines, kanban, export, print, real-time feeds) |
| E | Authentication | How users prove who they are (email/password, OAuth, SSO, MFA, magic link, API keys, sessions) |
| F | Authorization | What users are allowed to do (RBAC, ABAC, resource ownership, multi-tenancy, feature flags, rate limiting) |
| G | Communication | How the system communicates (email, push, in-app notifications, SMS, chat, webhooks, activity feeds) |
| H | Integration | Connections to external services (REST/GraphQL, web scraping, payment gateways, file sync, social media) |
| I | Workflow | Multi-step processes and automation (state machines, approval flows, cron jobs, queues, event triggers) |
| J | Search & Discovery | How users find things (full-text search, faceted search, autocomplete, recommendations, tags, favorites) |
| K | Collaboration | How users interact with each other (comments, @mentions, sharing, co-editing, reactions, following, profiles) |
| L | Monetization | How the app makes money (subscriptions, one-time, freemium, usage-based, marketplace, invoicing, refunds) |
| M | Admin/Ops | Back-office tools (admin dashboard, user management, content moderation, feature flags, analytics, config) |
| N | Infrastructure | System-level concerns (caching, DB migrations, circuit breakers, auto-scaling, logging, monitoring, CI/CD) |

---

## Default Status by Profile

### `supabase_web`

| ID | Status | Rationale |
|----|--------|-----------|
| A | needs_user_input | Input patterns depend entirely on the app idea |
| B | covered_by_boilerplate | Supabase/Postgres + Supabase Storage are pre-configured |
| C | needs_user_input | Processing logic is app-specific |
| D | needs_user_input | Display patterns depend on the app idea |
| E | covered_by_boilerplate | Supabase Auth handles email/password + OAuth |
| F | covered_by_boilerplate | Supabase Row Level Security (RLS) is available |
| G | needs_user_input | No notification system in base boilerplate |
| H | needs_user_input | No external integrations in base |
| I | needs_user_input | No workflow engine in base |
| J | needs_user_input | Postgres full-text search available but needs app-specific setup |
| K | needs_user_input | No collaboration features in base |
| L | needs_user_input | No payment integration in base |
| M | needs_user_input | No admin panel in base |
| N | covered_by_boilerplate | Vercel hosting + Supabase managed infra |

### `flutter_mobile`

| ID | Status | Rationale |
|----|--------|-----------|
| A | needs_user_input | Mobile-specific input patterns depend on app |
| B | covered_by_boilerplate | Supabase/Postgres backend |
| C | needs_user_input | App-specific |
| D | needs_user_input | App-specific |
| E | covered_by_boilerplate | Supabase Auth mobile SDK |
| F | covered_by_boilerplate | Supabase RLS |
| G | needs_user_input | Push notifications need platform-specific setup |
| H | needs_user_input | App-specific |
| I | needs_user_input | App-specific |
| J | needs_user_input | App-specific |
| K | needs_user_input | App-specific |
| L | needs_user_input | In-app purchases need platform-specific setup |
| M | needs_user_input | App-specific |
| N | covered_by_boilerplate | Supabase managed backend |

### `dual`

Same as `supabase_web` coverage. Both web and mobile clients share the Supabase backend, so B, E, F, and N are covered.

### `no_boilerplate`

All categories: `needs_user_input`. No boilerplate assumptions.

### `raw_checklist`

All categories: `needs_user_input`. Existing app analysis not yet supported.


---
## REFERENCE: Rule Resolution Guide

# Rule Resolution Guide

> How to resolve each Martin checklist category and industry standards rule against each boilerplate profile.

---

## Resolution Decision Tree

For each rule in the agnostic checklist and industry standards supplement:

```
1. Does the boilerplate already implement this rule?
   → YES: resolution = "HANDLED", evidence = file/config path
   → NO: continue

2. Does the rule's principle apply to this stack?
   → NO: resolution = "N/A" (e.g., mobile-specific rule for web-only app)
   → YES: continue

3. Does the rule's IMPLEMENTATION need to change for this stack?
   → NO: resolution = "MATCH" (carry as-is)
   → YES: continue

4. Can the boilerplate's native tooling enhance the rule?
   → YES: resolution = "ENHANCE" (keep rule + add boilerplate pointers)
   → NO: resolution = "REPLACE" (swap implementation, keep principle)
```

---

## Priority Assignment

| Priority | Criteria |
|----------|----------|
| `critical` | Security, auth, data integrity, build hygiene. Failure = broken app or security vulnerability. |
| `important` | Structure, naming, testing, accessibility, config. Failure = technical debt or poor quality. |
| `nice` | Polish, documentation, optimization. Failure = suboptimal but functional. |

---

## Enforcement Assignment

| Enforcement | Criteria |
|-------------|----------|
| `hard` | Build hygiene, structure, naming discipline, anti-pattern bans, security, auth boundaries, state/data handling consistency, deterministic component and testing standards. Non-negotiable. |
| `soft` | Feature count limits ("only 5 features" → recommendation), provider-specific assumptions, optimization suggestions. Advisory. |

---

## Per-Profile Resolution Patterns

### `supabase_web` Profile

| Martin Category | Typical Resolution | Rationale |
|----------------|-------------------|-----------|
| 1. Stack Definition | HANDLED | Supabase Web Starter defines the full stack |
| 2. File Structure | ENHANCE | Base structure exists; add Supabase-specific directories |
| 3. Component Architecture | MATCH | Component rules are framework-agnostic |
| 4. State Management | MATCH | State rules apply to any React app |
| 5. Routing | ENHANCE | Next.js App Router has specific patterns |
| 6. Styling | ENHANCE | Tailwind CSS is pre-configured |
| 7. Data Fetching | REPLACE | Supabase SDK replaces generic fetch patterns |
| 8. Auth & Security | HANDLED | Supabase Auth + RLS pre-configured |
| 9. Forms & Validation | MATCH | Form rules are stack-agnostic |
| 10. Error Handling | MATCH | Error patterns are universal |
| 11-22. (remaining) | MATCH or ENHANCE | Most structural rules apply as-is or with minor enhancements |
| Banned Patterns (43) | MATCH | All banned patterns are universal anti-patterns |

| Industry Standards | Typical Resolution | Rationale |
|-------------------|-------------------|-----------|
| 1. i18n | MATCH | Rules are stack-agnostic |
| 2. Config Externalization | ENHANCE | Vercel env vars + Next.js conventions |
| 3. Environment Parity | ENHANCE | Supabase local dev + Vercel preview |
| 4. Logging | MATCH | Rules are stack-agnostic |
| 5. Dependency Management | ENHANCE | npm-specific tooling |
| 6. Legal/Compliance | MATCH | Rules are stack-agnostic |
| 7. Accessibility (WCAG) | MATCH | Rules are stack-agnostic |
| 8. API Versioning | MATCH | Rules are stack-agnostic |
| 9. ADRs | MATCH | Rules are stack-agnostic |
| 10. Error Recovery/Retry | MATCH | Rules are stack-agnostic |

### `flutter_mobile` Profile

| Martin Category | Typical Resolution | Rationale |
|----------------|-------------------|-----------|
| 1. Stack Definition | HANDLED | Flutter + Supabase defines the stack |
| 2. File Structure | REPLACE | Flutter has different directory conventions |
| 3. Component Architecture | REPLACE | Flutter uses widgets, not JSX components |
| 4. State Management | REPLACE | Flutter state (Provider/Riverpod/Bloc) differs from React |
| 5. Routing | REPLACE | Flutter Navigator/GoRouter differs from web routing |
| 6. Styling | REPLACE | Flutter themes, not CSS |
| 7. Data Fetching | REPLACE | Supabase Dart SDK |
| 8. Auth & Security | HANDLED | Supabase Auth mobile SDK |
| 9-22. (remaining) | MATCH, REPLACE, or N/A | Many web-specific rules need mobile adaptation |
| Web-specific rules | N/A | CSS, HTML semantic, browser-specific rules don't apply |

### `no_boilerplate` and `raw_checklist` Profiles

All rules default to `MATCH` (carry as-is) since no boilerplate handles anything. The user's stated stack is used to determine which rules are `N/A` (e.g., mobile rules for a web-only project). No rules are `HANDLED` or `ENHANCE` because there are no boilerplate file pointers to reference.

---

## Evidence Examples

| Resolution | Evidence Format |
|-----------|----------------|
| HANDLED | `"boilerplate: src/lib/supabase.ts provides auth client"` |
| ENHANCE | `"extends: boilerplate uses Tailwind; add theme token file at src/styles/tokens.ts"` |
| REPLACE | `"replaces: Firebase Firestore patterns with Supabase Postgres + RLS"` |
| MATCH | `null` (no evidence needed — rule carries unchanged) |
| N/A | `null` (rule does not apply) |


---
## REFERENCE: Structural Categories

# Structural Categories Reference (30 Total)

> 22 Martin checklist categories + 10 industry standards gap areas − 2 overlaps = 30 unique categories.
> Each category must appear in the `structural_coverage.categories` array.

---

## Martin Checklist Categories (22)

| # | Category | Description |
|---|----------|-------------|
| 1 | Stack Definition | Framework, runtime, language, package manager choices |
| 2 | File Structure | Directory layout, naming conventions, file organization |
| 3 | Component Architecture | Component patterns, composition, prop contracts |
| 4 | State Management | Global state, local state, derived state patterns |
| 5 | Routing | Page routing, navigation, URL structure |
| 6 | Styling | CSS methodology, design tokens, responsive approach |
| 7 | Data Fetching | API calls, caching, loading/error states |
| 8 | Auth & Security | Authentication flow, session management, CSRF, XSS |
| 9 | Forms & Validation | Form handling, input validation, error display |
| 10 | Error Handling | Try/catch patterns, error boundaries, user-facing errors |
| 11 | Testing | Unit, integration, E2E test strategy and tooling |
| 12 | Build & Bundle | Build pipeline, bundling, code splitting |
| 13 | Type Safety | TypeScript/typing strategy, strict mode |
| 14 | Code Quality | Linting, formatting, code review standards |
| 15 | Git & Version Control | Branch strategy, commit conventions, PR process |
| 16 | Environment Config | Dev/staging/prod configuration |
| 17 | Performance | Core Web Vitals, lazy loading, optimization |
| 18 | SEO | Meta tags, sitemap, structured data (web only) |
| 19 | Analytics & Monitoring | Usage tracking, error monitoring |
| 20 | Deployment | CI/CD pipeline, deploy process |
| 21 | Documentation | README, inline docs, API docs |
| 22 | Banned Patterns | 43 anti-patterns that must never appear |

---

## Industry Standards Gap Areas (10)

These cover structural areas Martin's checklist does not address. Rule numbers start at 200.

| # | Category | Rules | Description |
|---|----------|-------|-------------|
| 23 | Internationalization (i18n) | 200-207 | String externalization, locale formatting, RTL readiness |
| 24 | Config Externalization | 208-214 | Secrets management, env vars, feature flags |
| 25 | Environment Parity | 215-220 | Dev/staging/prod consistency, seed data |
| 26 | Logging Strategy | 221-228 | Structured logs, log levels, correlation IDs |
| 27 | Dependency Management | 229-235 | Lockfiles, version pinning, security audits |
| 28 | Legal/Compliance | 236-243 | Privacy policy, terms, cookie consent, GDPR |
| 29 | Deep Accessibility (WCAG AA) | 244-253 | Contrast, semantic HTML, ARIA, reduced motion |
| 30 | API Versioning | 254-258 | Version identifiers, deprecation, backward compat |

---

## Overlap Resolution

Two categories from the industry standards overlap with Martin's checklist:

| Industry Category | Martin Overlap | Resolution |
|-------------------|---------------|------------|
| Architecture Decision Records (ADRs) | #21 Documentation | Merged into #21. ADR rules (259-263) are sub-rules of Documentation. |
| Error Recovery / Retry Strategy | #10 Error Handling | Merged into #10. Retry rules (264-270) are sub-rules of Error Handling. |

This produces 22 + 10 − 2 = **30 unique categories**.

---

## Default Coverage by Profile

### `supabase_web` Defaults

| Category | Default Status |
|----------|---------------|
| 1. Stack Definition | covered_by_preamble |
| 2. File Structure | covered_by_preamble |
| 3. Component Architecture | covered_by_preamble |
| 4-7 | covered_by_preamble |
| 8. Auth & Security | covered_by_preamble |
| 9-22 | missing (app-specific) |
| 23-30 (industry) | missing (not in boilerplate) |

Note: "covered_by_preamble" means the boilerplate + resolved rules address the category. "missing" means it must be resolved by the user's app idea in downstream stages. Categories can move to "provided_by_user" if the user explicitly addresses them in intake.


---
## REFERENCE: Martin's Agnostic Checklist

# Martin's Structural Checklist — Technology-Agnostic Version

## Theory: The Structural-Mechanism Split

Building any app has two halves:

**The Structural Half** covers how the code is organized — file structure, component patterns, state management, auth setup, styling rules, what's banned. This is the same for EVERY app regardless of the idea. Martin's 1,500-line Build PRD covers this half. So do boilerplates. This checklist makes that knowledge systematic and matchable.

**The Mechanism Half** covers what the specific app DOES — its features, user flows, data transformations, integrations. This varies per app and is handled by the Mechanism Identification Framework (A-N categories) in a separate document (`mechanism-identification-framework.md`).

Together, the structural checklist + the mechanism framework = a complete app specification with zero gaps.

### About This Version

This is the **technology-agnostic version** of Martin's structural checklist. The original (`trial-idea-1-structural-checklist.md`) was written for a specific stack (React 19 + Firebase + Firestore + Google Auth + Lucide React + importmap). This version preserves all ~192 rules and 43 banned patterns but rewrites stack-specific rules so they apply to **any technology stack**.

**This is the source of truth.** Platform-specific preambles (e.g., `web-firebase.md`, `web-supabase.md`, `mobile-flutter.md`) are DERIVED from this document by filling in the "Boilerplate Match" column with platform-specific details. When in doubt, defer to this document.

### Classification System

Every rule is tagged with two attributes:

**Type** — How stack-specific the rule is:

| Tag | Meaning |
|-----|---------|
| **UNIVERSAL** | Applies to any stack as written. No changes needed. |
| **STACK-SPECIFIC** | Originally tied to a specific technology. Technical Spec rewritten to generic language. |
| **PATTERN** | Universal principle with a stack-specific implementation. Principle extracted; original noted as example. |

**Severity** — How critical the rule is:

| Tag | Meaning |
|-----|---------|
| **CRITICAL** | Security, data integrity, auth bypass, build-breaking, or production crash if violated. Non-negotiable. |
| **STANDARD** | UX quality, component patterns, state management, code organization. Violating these produces a working but sloppy app. |
| **POLISH** | Cosmetic refinements, animation, spacing, naming. Nice to have but the app works fine without them. |

### How This Checklist Works

Each row captures one technical rule from Martin's narrative:
- **Martin Says** — his exact words (quoted, preserved verbatim even if stack-specific)
- **Technical Spec (Agnostic)** — precise, implementable translation written for any stack
- **Boilerplate Match** — intentionally blank; filled during the boilerplate matching step

### The Preamble System

This checklist becomes a "preamble" injected before every pipeline stage. It tells the agent what's already decided so it doesn't waste time asking about structure. The agent only asks about mechanisms (what the app DOES).

### The Boilerplate Matching Step

A separate agent reads this checklist + a specific boilerplate and fills in the "Boilerplate Match" column:
- **MATCH** — Rule applies as-is to the boilerplate
- **REPLACE** — Rule principle applies but implementation differs (e.g., Firebase → Supabase)
- **ENHANCE** — Boilerplate has a more complete implementation than the rule describes
- **HANDLED** — Boilerplate already implements this; mark "don't touch"

Result: a boilerplate-specific preamble (e.g., `web-supabase.md`, `mobile-flutter.md`, `dual.md`, `no-boilerplate.md`).

---

## The Checklist

**Total: ~192 rules across 22 categories + 43 banned patterns**

---
---

### Stack (Mandatory)

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | Framework with type safety | "React 19 with TypeScript" | Use the project's chosen UI framework with strict type checking enabled; all code must be statically typed | _[to be filled]_ | STACK-SPECIFIC | STANDARD |
| 2 | Single styling solution | "Tailwind CSS for all styling" | All styling via a single, consistent CSS methodology (utility-first framework, CSS modules, or styled-components); no mixing approaches; no inline styles | _[to be filled]_ | STACK-SPECIFIC | STANDARD |
| 3 | Authentication provider | "Firebase Authentication (Google Sign-In only)" | Use the configured authentication provider's sign-in flow with the designated OAuth provider; restrict to approved sign-in methods only | _[to be filled]_ | STACK-SPECIFIC | CRITICAL |
| 4 | Single database backend | "Cloud Firestore for database" | All persistent data stored in a single configured database technology; do not mix multiple database backends within one project | _[to be filled]_ | STACK-SPECIFIC | STANDARD |
| 5 | Built-in state management | "React Context for auth state" | Auth and feature state managed via the framework's built-in state management primitives (e.g., React Context, Vue provide/inject, Angular services) | _[to be filled]_ | STACK-SPECIFIC | STANDARD |
| 6 | No external state libraries | "NO external state libraries" | No third-party state management libraries (Redux, Zustand, Jotai, MobX, Pinia, NgRx, etc.) unless explicitly approved in project config | _[to be filled]_ | STACK-SPECIFIC | STANDARD |
| 7 | No containerization | "NO Docker" | No Dockerfiles, no docker-compose, no containerization in the project scaffold; deployment handled by the configured hosting platform | _[to be filled]_ | STACK-SPECIFIC | STANDARD |
| 8 | No custom backend | "NO backend APIs" | No custom server-side code (Express, FastAPI, Django, etc.); all backend functionality provided by the configured BaaS or serverless platform | _[to be filled]_ | STACK-SPECIFIC | STANDARD |
| 9 | Single icon library | "Use Lucide React for all icons" | Use a single, consistent icon library for all icons throughout the app; do not mix icon sources; define a standard icon size | _[to be filled]_ | STACK-SPECIFIC | POLISH |
| 10 | Dependency management locked | Locked importmap in index.html | All dependencies managed through the project's configured module/build system; dependency versions locked and not modified without explicit approval | _[to be filled]_ | STACK-SPECIFIC | STANDARD |

---

### File Structure

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | One component per file | "One component per file" | Each file exports exactly one UI component as its default/primary export; no multi-component files | _[to be filled]_ | UNIVERSAL | STANDARD |
| 2 | Feature folders for grouping | "Group related components in feature folders" | Related components go in `components/[FeatureName]/` directories; do not flatten everything into a single folder | _[to be filled]_ | UNIVERSAL | STANDARD |
| 3 | Centralized type definitions | "Create interfaces for all data types" | All shared type definitions (interfaces, types, schemas) centralized in a dedicated types directory or file; no inline type definitions scattered across components. (e.g., TypeScript: `types/index.ts`, Python: `models.py`, Go: `types.go`) | _[to be filled]_ | PATTERN | STANDARD |
| 4 | Custom hooks per feature | "Add custom hooks for reusable logic" | Extract shared stateful logic into reusable hook/composable files following framework conventions (e.g., React: `hooks/use[Feature].ts`, Vue: `composables/use[Feature].ts`) | _[to be filled]_ | PATTERN | POLISH |
| 5 | Required directory structure | File tree showing src/ layout | Source directory organized into: config/, state-management/, hooks-or-composables/, components/ui/, pages-or-views/, services/, utils/, types/. (e.g., React: `contexts/`, `hooks/`, `pages/`; Vue: `stores/`, `composables/`, `views/`) | _[to be filled]_ | PATTERN | STANDARD |
| 6 | Config folder for service credentials | `config/firebase.ts` | Service configuration and credentials live in a dedicated `config/` directory; never scattered across multiple locations. (e.g., Firebase: `config/firebase.ts`, Supabase: `config/supabase.ts`) | _[to be filled]_ | PATTERN | CRITICAL |
| 7 | State management folder | `contexts/AuthContext.tsx`, `ThemeContext.tsx`, `ToastContext.tsx` | All global state providers in a dedicated directory; add feature-specific state files for each app domain. (e.g., React: `contexts/`, Vue: `stores/`, Angular: `services/`) | _[to be filled]_ | PATTERN | STANDARD |
| 8 | Services folder for data access | `services/firestore.ts` | All database/API CRUD operations in a dedicated `services/` directory; components never import database client libraries directly. (e.g., Firebase: `services/firestore.ts`, Supabase: `services/supabase.ts`) | _[to be filled]_ | PATTERN | CRITICAL |
| 9 | Utils folder | `utils/formatDate.ts`, `utils/pluralize.ts` | Helper functions in a `utils/` directory; at minimum date formatting and pluralization utilities | _[to be filled]_ | UNIVERSAL | STANDARD |
| 10 | Pages folder with naming convention | `pages/[Item]DetailPage.tsx`, `[Item]CreatePage.tsx`, `[Item]EditPage.tsx` | Page/view components follow `[Entity][Action]Page` naming convention; one page per route | _[to be filled]_ | UNIVERSAL | STANDARD |
| 11 | UI components folder | `components/ui/` with Modal, Toast, etc. | All reusable UI primitives in a dedicated `components/ui/` directory | _[to be filled]_ | UNIVERSAL | STANDARD |

---

### Configuration / Module System

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | Dependency versions locked | "IMPORTMAP IS LOCKED. DO NOT MODIFY" | Dependency versions are locked via the project's package manager or module system; no version changes, additions, or removals without explicit approval | _[to be filled]_ | STACK-SPECIFIC | STANDARD |
| 2 | No redundant sub-imports | "DO NOT ADD firebase/app, firebase/auth, or firebase/firestore to the importmap" | Do not add redundant or conflicting entries to the dependency configuration; follow the package's recommended import pattern. (e.g., Firebase: single `firebase/` trailing-slash entry handles all sub-imports) | _[to be filled]_ | STACK-SPECIFIC | STANDARD |
| 3 | CSS framework loading | `<script src="https://cdn.tailwindcss.com">` | CSS framework loaded via the project's standard method (CDN, build tool, or package manager) with inline configuration for theme customization | _[to be filled]_ | STACK-SPECIFIC | STANDARD |
| 4 | Typography font loaded | Google Fonts link for Inter | Load the project's chosen font family with required weights (regular, medium, semi-bold, bold) via CDN or local files | _[to be filled]_ | STACK-SPECIFIC | POLISH |
| 5 | CSS variables for theming | "Use `var(--color-*)` references so the theme toggle works" | Light mode values in `:root`; dark mode overrides in a toggled class; reference via CSS custom properties (`var(--color-*)`) throughout | _[to be filled]_ | UNIVERSAL | STANDARD |
| 6 | Dark mode via class strategy | `darkMode: 'class'` | Dark mode toggled via a CSS class on the root element; not via `prefers-color-scheme` media query alone | _[to be filled]_ | UNIVERSAL | STANDARD |
| 7 | Semantic color tokens | Surface, text, border color tokens | Colors defined as semantic tokens (surface-canvas/base/muted, text-primary/secondary/tertiary, border-subtle, brand/brand-dark) not raw color values | _[to be filled]_ | UNIVERSAL | STANDARD |
| 8 | Custom border radius token | `borderRadius: { card: '12px' }` | Define a reusable border radius token for cards (e.g., 12px) in the design system configuration | _[to be filled]_ | UNIVERSAL | POLISH |
| 9 | Custom card shadow token | `boxShadow: { card: '...' }` | Define a reusable card shadow token with subtle dual-shadow in the design system configuration | _[to be filled]_ | UNIVERSAL | POLISH |
| 10 | Optional AI SDK import | "Add this single line to the importmap" for @google/genai | If using an AI SDK, add it via the standard dependency management method; do not pin to a specific version unless required for stability. (e.g., Google GenAI via importmap, OpenAI via npm) | _[to be filled]_ | STACK-SPECIFIC | STANDARD |

---

### Authentication Context

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | UserProfile interface with role | `interface UserProfile { uid, email, displayName, photoURL, role, createdAt, updatedAt }` | User profile stored in the database includes a `role` field with defined role values (e.g., `user`, `pro`, `admin`); profile type/interface defined centrally | _[to be filled]_ | PATTERN | STANDARD |
| 2 | Auth context provides full interface | `user`, `userProfile`, `loading`, `signInWithGoogle`, `logout`, `isAdmin`, `isPro` | Auth state provider exposes: authenticated user object, database user profile, loading state, sign-in/sign-out functions, and role convenience booleans. (e.g., React: AuthContext, Vue: auth store, Angular: AuthService) | _[to be filled]_ | PATTERN | STANDARD |
| 3 | Profile created on first login | `setDoc` on first sign-in | On first successful authentication where no database profile exists, auto-create a profile record with default role and server-generated timestamps. (e.g., Firebase: `setDoc` on first `onAuthStateChanged`) | _[to be filled]_ | PATTERN | CRITICAL |
| 4 | Default role is 'user' | "Default role - change via Firebase Console" | New user profiles get the lowest-privilege role by default; role elevation only possible through admin tools, never through the app UI. (e.g., Firebase: `role: 'user'` enforced by security rules; Supabase: RLS default; SQL: `DEFAULT 'user'` column constraint) | _[to be filled]_ | PATTERN | CRITICAL |
| 5 | Service init order critical | "CRITICAL: Import order matters - app must be initialized FIRST" | Backend service client must be initialized before dependent services (auth, database, storage) are instantiated; incorrect order causes runtime crashes. (e.g., Firebase: `initializeApp()` before `getAuth()` and `getFirestore()`) | _[to be filled]_ | PATTERN | CRITICAL |
| 6 | Popup/redirect sign-in flow | Code showing `signInWithPopup(auth, googleProvider)` | Use the auth provider's popup or redirect sign-in flow; catch errors and show user-friendly feedback on failure. (e.g., Firebase: `signInWithPopup`, Supabase: `signInWithOAuth`) | _[to be filled]_ | PATTERN | CRITICAL |
| 7 | Loading state during auth check | `const [loading, setLoading] = useState(true)` | App shows a loading state while the initial authentication check resolves; prevents flash of wrong content (unauthenticated UI shown to logged-in user or vice versa) | _[to be filled]_ | UNIVERSAL | STANDARD |

---

### Theme Context (Dark Mode)

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | localStorage persistence | Theme preference saved to localStorage | Read theme preference from `localStorage` on mount; save on toggle | _[to be filled]_ | UNIVERSAL | STANDARD |
| 2 | System preference fallback | Check `prefers-color-scheme: dark` | If no saved preference, check `window.matchMedia('(prefers-color-scheme: dark)')` for system default | _[to be filled]_ | UNIVERSAL | STANDARD |
| 3 | Class on html element | `.dark` class toggled on `document.documentElement` | Dark mode class toggled on the root HTML element to cascade through all components | _[to be filled]_ | UNIVERSAL | STANDARD |
| 4 | ThemeToggle component required | `ThemeToggle.tsx` in ui/ | A toggle button component that switches between light/dark themes; shows an icon indicating the opposite of current mode | _[to be filled]_ | UNIVERSAL | STANDARD |

---

### Route Guards

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | ProtectedRoute for auth users | `ProtectedRoute.tsx` | A route guard component that checks authentication state; redirects unauthenticated users to the login page; shows spinner while auth state is loading | _[to be filled]_ | UNIVERSAL | CRITICAL |
| 2 | AdminRoute for admin only | `AdminRoute.tsx` | Extends the auth route guard; also checks user role is `admin`; redirects non-admins to the dashboard | _[to be filled]_ | UNIVERSAL | CRITICAL |
| 3 | ProRoute for pro/admin | `ProRoute.tsx` (optional) | Checks user role is `pro` or `admin`; redirects others to dashboard or upgrade page | _[to be filled]_ | UNIVERSAL | STANDARD |
| 4 | Route wrapping order | "ProtectedRoute > Layout > Page" | Route guard components wrap layout, which wraps page content: `<RouteGuard><Layout><Page /></Layout></RouteGuard>` | _[to be filled]_ | UNIVERSAL | STANDARD |
| 5 | Provider nesting order | "AuthProvider > ThemeProvider > ToastProvider > BrowserRouter" | Global providers nested outermost to innermost: ErrorBoundary > AuthProvider > ThemeProvider > ToastProvider > Router > Routes | _[to be filled]_ | UNIVERSAL | STANDARD |

---

### Data Structure

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | User data scoped to user | "users/{uid}/{collectionName}/{documentId}" | All user-owned data scoped to the authenticated user; never stored in shared/global tables without user scoping. (e.g., document DB: `users/{uid}/{collection}/{docId}`, SQL: `WHERE user_id = ?`, Supabase: RLS policies) | _[to be filled]_ | PATTERN | CRITICAL |
| 2 | Helper for user data access | `getUserCollection(uid, collectionName)` | Utility function that abstracts database path/query construction for user-scoped data so access patterns are defined in one place. (e.g., Firebase: `getUserCollection(uid, name)` returns Firestore collection ref) | _[to be filled]_ | PATTERN | STANDARD |
| 3 | Server timestamps on all writes | "createdAt: serverTimestamp(), updatedAt: serverTimestamp()" | Every record creation includes both `createdAt` and `updatedAt` using the database's server-generated timestamp; every update sets `updatedAt` — never use client-side date generation for these fields. (e.g., Firebase: `serverTimestamp()`, Supabase: `now()`, SQL: `DEFAULT CURRENT_TIMESTAMP`) | _[to be filled]_ | PATTERN | CRITICAL |
| 4 | Default sort newest first | "orderBy('createdAt', 'desc')" | All collection/list queries default to descending `createdAt` order (newest first) | _[to be filled]_ | UNIVERSAL | POLISH |

---

### Data Service Layer

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | No database calls in components | "NO Firestore calls in components - use firestore service only" | All database/API operations go through a service layer module; UI components never import or call database client libraries directly. (e.g., Firebase: all calls through `services/firestore.ts`, Supabase: through `services/supabase.ts`) | _[to be filled]_ | PATTERN | STANDARD |
| 2 | CRUD helper functions | `addDocument`, `updateDocument`, `deleteDocument`, `getDocuments` | Four base CRUD functions wrapping database operations with automatic timestamp injection on creates and updates. (e.g., Firebase: `addDocument`/`updateDocument`/`deleteDocument`/`getDocuments` in `services/firestore.ts`) | _[to be filled]_ | PATTERN | STANDARD |
| 3 | Realtime subscription pattern | "return onSnapshot(q, ...)" | For realtime data, use the database's subscription/listener mechanism; map results to a normalized format; return an unsubscribe/cleanup function. (e.g., Firebase: `onSnapshot`, Supabase: `.on('*')`, Postgres: LISTEN/NOTIFY) | _[to be filled]_ | PATTERN | STANDARD |
| 4 | Delete account function | `deleteUserAccount(uid, subcollections[])` | Account deletion function that removes all user-owned data (iterating known data categories) before removing the user profile record; cascading delete must be explicit, not implicit. (e.g., Firebase: iterate subcollections then delete user doc; SQL: explicit DELETE per table) | _[to be filled]_ | PATTERN | CRITICAL |

---

### Routing Structure

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | Router wraps all routes | Uses `HashRouter` or `BrowserRouter` | Router component wraps all route definitions; public routes (landing, login) outside auth guards; choose hash or history routing based on hosting requirements | _[to be filled]_ | UNIVERSAL | STANDARD |
| 2 | Public vs protected routes | Landing and Login are public; Dashboard, Profile, CRUD pages are protected | Public routes: landing page, login. Protected routes: dashboard, profile, all CRUD pages. Clear separation enforced by route guards | _[to be filled]_ | UNIVERSAL | CRITICAL |
| 3 | 404 catch-all | `<Route path="*" element={<NotFoundPage />} />` | Last route definition catches all unmatched paths and renders a Not Found page | _[to be filled]_ | UNIVERSAL | STANDARD |
| 4 | CRUD route pattern | Detail, Create, Edit routes per entity | Standard CRUD routes per entity: `/items` (list), `/items/new` (create), `/items/:id` (detail), `/items/:id/edit` (edit) | _[to be filled]_ | UNIVERSAL | STANDARD |

---

### Data/API Patterns

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | Delete account removes all user data | "Delete all documents in each subcollection" | Account deletion function iterates all known user-data categories, deletes all records in each, then deletes the parent user profile record. (e.g., Firebase: iterate subcollections under `users/{uid}`, Supabase: cascade delete via RLS or explicit queries) | _[to be filled]_ | PATTERN | CRITICAL |
| 2 | Data category list is explicit | "List all subcollections your app uses" | Pass an explicit list of data category names (tables, collections, buckets) to the deletion function — no dynamic discovery of user data locations | _[to be filled]_ | UNIVERSAL | STANDARD |
| 3 | Realtime subscription pattern | "For realtime updates ... return onSnapshot(q, ...)" | Use the database's realtime subscription mechanism with an ordered query; map results to a normalized object format and return a cleanup/unsubscribe function. (e.g., Firebase: `onSnapshot`, Supabase: realtime channels) | _[to be filled]_ | PATTERN | STANDARD |
| 4 | CRUD helper layer | Code block showing `addDocument`, `updateDocument`, `deleteDocument`, `getDocuments` | Wrap all database operations in a service module with CRUD helper functions; every write automatically sets server-generated timestamps. (e.g., Firebase: `services/firestore.ts`, Supabase: `services/database.ts`) | _[to be filled]_ | PATTERN | STANDARD |
| 5 | Records always include timestamps | "createdAt: serverTimestamp(), updatedAt: serverTimestamp()" | Every database record must have `createdAt` (set on create) and `updatedAt` (set on create and every update) using the database's server-generated timestamp function — never client-side `new Date()`. (e.g., Firebase: `serverTimestamp()`, Supabase/SQL: `DEFAULT CURRENT_TIMESTAMP`) | _[to be filled]_ | PATTERN | CRITICAL |
| 6 | Default sort order | "orderBy('createdAt', 'desc')" | All list/collection queries default to descending `createdAt` order — newest first | _[to be filled]_ | UNIVERSAL | STANDARD |
| 7 | List pagination is mandatory | "Lists MUST handle large amounts of data" | Every list view must implement one of: pagination (10-20 items per page), load-more button, or infinite scroll. Pick ONE strategy and use it consistently across all lists | _[to be filled]_ | UNIVERSAL | STANDARD |
| 8 | Pagination controls pattern | "Show 10-20 items per page ... Pagination controls at bottom" | Use an `ITEMS_PER_PAGE` constant (e.g., 10), page state starting at 1, Previous/Next buttons disabled at bounds, "Page X of Y" label centered between buttons | _[to be filled]_ | UNIVERSAL | POLISH |
| 9 | Load-more shows remaining count | "Load More ({remaining} remaining)" | Load-more button must display how many items remain unloaded; initial limit of 10 items, increment by 10 on click | _[to be filled]_ | UNIVERSAL | POLISH |

---

### Authentication/Security

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | Delete account requires typed confirmation | "Type DELETE to confirm" | Account deletion requires the user to type an exact confirmation string (e.g., "DELETE") into a text input; submit button disabled until the string matches exactly | _[to be filled]_ | UNIVERSAL | CRITICAL |
| 2 | Delete button disabled during operation | "disabled={confirmText !== 'DELETE' \|\| isDeleting}" | Delete confirmation button must check both confirmation text match AND in-progress state; show "Deleting..." text while in progress | _[to be filled]_ | UNIVERSAL | STANDARD |
| 3 | Logout after account deletion | "await deleteUserAccount(user.uid, ...); await logout();" | After successful account deletion, immediately clear the auth session before showing success feedback | _[to be filled]_ | UNIVERSAL | CRITICAL |
| 4 | Protected routes wrap layout | "ProtectedRoute > Layout > Page" | All authenticated pages wrapped as RouteGuard > Layout > Page; public pages (landing, login) have no auth wrapper | _[to be filled]_ | UNIVERSAL | STANDARD |
| 5 | Auth/theme/toast providers wrap router | "AuthProvider > ThemeProvider > ToastProvider > BrowserRouter" | Provider nesting order (outermost to innermost): ErrorBoundary > AuthProvider > ThemeProvider > ToastProvider > Router > Routes | _[to be filled]_ | UNIVERSAL | STANDARD |
| 6 | Admin-only nav items are conditional | "isAdmin && <Link to='/admin'>Admin</Link>" | Navigation must conditionally render admin-only links based on the user's role; non-admins never see admin navigation | _[to be filled]_ | UNIVERSAL | CRITICAL |

---

### Database/Storage

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | User data scoped to owner | "getUserCollection(uid, collectionName)" | All user-owned data scoped to the authenticated user via user-specific paths, rows, or policies. (e.g., Firebase: `users/{uid}/{collection}/{docId}`, SQL: `WHERE user_id = ?`, Supabase: RLS) | _[to be filled]_ | PATTERN | CRITICAL |
| 2 | Delete cascades to all user data | "removes user profile and all subcollections" | Account deletion must remove all records in every known user-data category BEFORE deleting the parent user profile record | _[to be filled]_ | UNIVERSAL | CRITICAL |
| 3 | Batch deletes for efficiency | "const deletePromises = snapshot.docs.map(doc => deleteDoc(doc.ref)); await Promise.all(deletePromises);" | Bulk deletion fetches all records, maps to individual delete operations, then awaits all concurrently for each data category. (e.g., Firebase: `Promise.all` of `deleteDoc` calls, SQL: `DELETE FROM table WHERE user_id = ?`) | _[to be filled]_ | PATTERN | STANDARD |

---

### Error Handling

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | Delete failure keeps modal open | "catch (error) { showToast({ type: 'error', message: 'Failed to delete account' }); setIsDeleting(false); }" | On delete error: show error feedback, reset loading state, do NOT close the confirmation modal, do NOT navigate away | _[to be filled]_ | UNIVERSAL | STANDARD |
| 2 | Success feedback is toast + navigate | "Show success Toast ... Navigate to appropriate view" | Every successful mutation: show a success notification with descriptive message, then navigate to the next logical view | _[to be filled]_ | UNIVERSAL | STANDARD |
| 3 | Error feedback preserves form state | "Show error Toast with helpful message ... Stay on current view ... Keep form data intact" | On error: show error notification, remain on current view, do NOT clear or reset form data | _[to be filled]_ | UNIVERSAL | STANDARD |
| 4 | Delete flow is 6-step | "1. User clicks delete 2. ConfirmModal appears ... 3. User confirms 4. Show loading state on button 5. On success: Toast + redirect to List 6. On error: Toast + close modal" | Delete flow: click > confirmation dialog > confirm > button loading state + disabled > success notification + redirect to list, OR error notification + close modal | _[to be filled]_ | UNIVERSAL | STANDARD |
| 5 | Loading states match content shape | "Lists: Show Skeleton cards (not spinner) ... Detail View: Show Skeleton matching content layout ... Buttons during action: Show spinner inside button, disable button" | Lists show skeleton placeholders matching card shape, detail views show skeleton matching layout, action buttons show inline spinner and become disabled. Never use bare "Loading..." text | _[to be filled]_ | UNIVERSAL | STANDARD |

---

### Performance

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | Animations use short durations | "transition-opacity duration-200 ... transition-all duration-200 ease-out ... transition-transform duration-300 ease-out ... transition-all duration-150" | Modal backdrop: 200ms opacity. Modal content: 200ms ease-out. Toast: 300ms ease-out. Card hover: 200ms. Button press: 150ms. Never exceed 300ms for UI transitions | _[to be filled]_ | UNIVERSAL | POLISH |
| 2 | Card hover uses translate | "hover:shadow-md hover:-translate-y-0.5" | Card hover effect combines elevated shadow with a slight upward translate for a lift effect; use a 200ms transition | _[to be filled]_ | UNIVERSAL | POLISH |
| 3 | Button press uses scale | "active:scale-[0.98]" | Buttons must have a slight scale-down on press (e.g., 0.98) with a 150ms transition for tactile feedback | _[to be filled]_ | UNIVERSAL | POLISH |
| 4 | Choose one pagination strategy | "Choose ONE approach and implement it consistently" | Pick one list-handling strategy (pagination, load-more, or infinite scroll) and apply it to ALL list views in the app; do not mix approaches | _[to be filled]_ | UNIVERSAL | STANDARD |

---

### UX Standards

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | Six required UI components | "You MUST create and use these components. They are NOT optional: 1. Modal.tsx 2. ConfirmModal.tsx 3. Toast.tsx 4. ToastContext.tsx 5. Skeleton.tsx 6. EmptyState.tsx" | Create all six foundational UI components: Modal (overlay + close + title + content slots), ConfirmModal (destructive action confirmation dialog), Toast (success/error/info slide-in notification), ToastContext/Provider (global `showToast(message, type)` function), Skeleton (animated placeholder matching content shape), EmptyState (icon + message + CTA button) | _[to be filled]_ | UNIVERSAL | STANDARD |
| 2 | Browser dialogs are banned | "These are strictly forbidden. Using them fails the build: alert(), confirm(), prompt(), console.log for user feedback" | Never use `alert()`, `confirm()`, `prompt()`, or `console.log` for user-facing feedback. Use Toast for messages, ConfirmModal for confirmations, Modal for prompts | _[to be filled]_ | UNIVERSAL | STANDARD |
| 3 | Text-only empty states are banned | "Text-only empty states ... needs icon + CTA" | Empty states must use the EmptyState component with an icon/illustration, descriptive message, AND a call-to-action button. Plain "No items" text is forbidden | _[to be filled]_ | UNIVERSAL | STANDARD |
| 4 | Loading text is banned | "Loading states that are just the word 'Loading...'" | Never display bare "Loading..." text. Use Skeleton components that match the shape of the content being loaded | _[to be filled]_ | UNIVERSAL | STANDARD |
| 5 | List-Detail-Create-Edit flow | "Any data the user creates/saves MUST follow this pattern: List View ... Detail View ... Create View ... Edit View" | All user data CRUD must implement four distinct views: List (cards/rows + "Create New"), Detail (read-only + Edit/Delete/Share), Create (form, save > Detail), Edit (pre-filled form, save > Detail, cancel > Detail not List) | _[to be filled]_ | UNIVERSAL | STANDARD |
| 6 | No edit-first pattern | "Clicking saved item opens it in edit mode directly ... Using Create form as Edit form ... No way to view an item without editing it ... Single 'smart' component that handles both view and edit" | Items always open in read-only Detail view. Create and Edit are separate views/components. Never combine view+edit into one "smart" component | _[to be filled]_ | UNIVERSAL | STANDARD |
| 7 | Delete always requires confirmation | "Delete with no confirmation" listed as anti-pattern | Every delete action must go through a confirmation dialog with explicit user confirmation. No silent deletes | _[to be filled]_ | UNIVERSAL | STANDARD |
| 8 | Every action needs user feedback | "Success/error with no feedback to user" listed as anti-pattern | Every mutation (create, update, delete) must show either a success or error notification. No silent operations | _[to be filled]_ | UNIVERSAL | POLISH |
| 9 | Cancel-edit returns to detail | "Cancel returns to Detail View (not List)" | In Edit view, the Cancel button navigates back to the Detail view of the same item, not to the List view | _[to be filled]_ | UNIVERSAL | POLISH |
| 10 | Cancel-create returns to list | "Cancel returns to List View" | In Create view, the Cancel button navigates back to the List view | _[to be filled]_ | UNIVERSAL | POLISH |
| 11 | Never show raw timestamps | "Never show raw timestamps. Format dates for humans" | Create a date formatting utility. Display: "Just now" (<60s), "Xm ago" (<1h), "Xh ago" (<24h), "Yesterday" (24-48h), "Xd ago" (<7d), "Jan 15" (>7d same year), "Jan 15, 2024" (different year) | _[to be filled]_ | UNIVERSAL | STANDARD |
| 12 | Text truncation is mandatory | "Long text MUST be truncated to prevent layout breaking" | Sidebar items: truncate at ~30 chars. Card descriptions: clamp to 2 lines. Table cells: truncate at ~20 chars. Always pair truncation with a max-width value | _[to be filled]_ | UNIVERSAL | STANDARD |
| 13 | Back navigation on every sub-page | "Every detail/edit page MUST have back navigation" | Detail and Edit pages must have a back button at the top using either browser history back or an explicit link to the parent list route with a left arrow icon | _[to be filled]_ | UNIVERSAL | STANDARD |
| 14 | Five required animations | "Required animations: Modals: Fade in backdrop, scale up content. Toasts: Slide in from top-right. Cards: Subtle lift on hover. Buttons: Slight scale on press. Sidebar: Slide in on mobile" | Implement all five animation types: modal backdrop fade + content scale, toast slide-in, card hover lift, button press scale, sidebar mobile slide-in | _[to be filled]_ | UNIVERSAL | POLISH |
| 15 | Danger zone styling | "mt-12 pt-8 border-t border-red-200 ... text-red-600 ... bg-red-600 hover:bg-red-700" | Account deletion section visually separated from other settings with extra top spacing, a separator line, red-toned heading, and red-toned button. Labeled "Danger Zone" | _[to be filled]_ | UNIVERSAL | POLISH |
| 16 | Modal overlay pattern | "fixed inset-0 bg-black/50 flex items-center justify-center z-50" | Modals use fixed full-screen overlay with semi-transparent black background, flex centering, high z-index. Inner content: themed background, rounded corners, padding, max-width, responsive horizontal margin | _[to be filled]_ | UNIVERSAL | STANDARD |
| 17 | Focus states on all interactive elements | "All interactive elements need visible focus ... focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2" | Every button, link, and input must have visible focus indicators (e.g., focus ring in brand color with offset) | _[to be filled]_ | UNIVERSAL | STANDARD |
| 18 | Escape key closes modals | "Modals must handle Escape key" | Every modal must listen for the Escape key and close on press. Clean up listener on unmount | _[to be filled]_ | UNIVERSAL | STANDARD |
| 19 | Focus trap in modals | "Focus trap in modals - focus first element, trap Tab key" | Modals must trap keyboard focus: focus the first interactive element on open, cycle Tab within the modal only | _[to be filled]_ | UNIVERSAL | STANDARD |
| 20 | Icon buttons need aria-label | "Icon-only buttons need aria-label" | Every button containing only an icon (no visible text) must have an `aria-label` attribute describing the action (e.g., "Close modal", "Delete item") | _[to be filled]_ | UNIVERSAL | STANDARD |
| 21 | Screen reader loading states | "Loading states ... <span className='sr-only'>Loading...</span>" | Add screen-reader-only text alongside visual loading indicators so assistive technology can announce the loading state | _[to be filled]_ | UNIVERSAL | POLISH |
| 22 | Status updates use aria-live | "<div role='status' aria-live='polite'>{message}</div>" | Dynamic status messages must use appropriate ARIA roles (`role="status"`, `aria-live="polite"`) so screen readers announce changes | _[to be filled]_ | UNIVERSAL | POLISH |
| 23 | 404 catch-all route | "<Route path='*' element={<NotFoundPage />} />" | The router must include a catch-all route rendering a Not Found page for unmatched URLs | _[to be filled]_ | UNIVERSAL | STANDARD |

---

### Mobile/Responsive

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | Mobile-first design | "Build mobile-first. Design for mobile, then scale up for larger screens." | Write default styles for mobile; use progressive breakpoint prefixes to add tablet/desktop overrides | _[to be filled]_ | UNIVERSAL | STANDARD |
| 2 | Three breakpoints | "Mobile: < 640px (default styles, no prefix) ... Tablet: sm:640px and up ... Desktop: lg:1024px and up" | Define three breakpoints: mobile (default, < 640px), tablet (~640px+), desktop (~1024px+) | _[to be filled]_ | UNIVERSAL | STANDARD |
| 3 | Sidebar hidden on mobile | "Sidebar hidden by default on mobile ... Hamburger icon in header toggles sidebar" | Sidebar hidden by default on mobile; visible on desktop; mobile header has hamburger menu icon to toggle sidebar | _[to be filled]_ | UNIVERSAL | STANDARD |
| 4 | Sidebar is overlay on mobile | "Sidebar slides in as overlay (not push) ... Clicking outside or nav item closes sidebar ... Add close button inside mobile sidebar" | Mobile sidebar slides over content (not push layout), closes on outside click or nav item click, has a close button inside | _[to be filled]_ | UNIVERSAL | STANDARD |
| 5 | Cards stack vertically on mobile | "Cards: Full width, stack vertically (mobile) ... Grid 2-3 columns (desktop)" | Card grids: single column on mobile, 2 columns on tablet, 3 columns on desktop with consistent gap | _[to be filled]_ | UNIVERSAL | STANDARD |
| 6 | Forms full width on mobile | "Forms: Full width inputs (mobile) ... Max-width container (desktop)" | Form inputs: full width on mobile, constrained max-width on desktop | _[to be filled]_ | UNIVERSAL | STANDARD |
| 7 | Primary buttons full width on mobile | "Buttons: Full width for primary actions (mobile) ... Auto width (desktop)" | Primary action buttons: full width on mobile, auto/natural width on desktop | _[to be filled]_ | UNIVERSAL | STANDARD |
| 8 | Modals nearly full screen on mobile | "Modals: Full screen or nearly full (mobile) ... Centered, max-w-md (desktop)" | Modals on mobile should be full-screen or near-full; on desktop: centered with constrained max-width | _[to be filled]_ | UNIVERSAL | STANDARD |
| 9 | Minimum 16px text on mobile | "Text: Base size 16px minimum (mobile) ... Can be smaller (desktop)" | Body text must be at least 16px on mobile to prevent readability issues and iOS zoom; smaller sizes allowed only on desktop breakpoints | _[to be filled]_ | UNIVERSAL | STANDARD |
| 10 | 44px minimum touch targets | "Minimum 44px x 44px for all clickable elements on mobile ... Add padding to small icons/buttons to meet minimum ... Adequate spacing between touch targets" | All clickable elements must have a minimum touch area of 44x44px on mobile; add padding to small icons/buttons; ensure adequate spacing between adjacent targets | _[to be filled]_ | UNIVERSAL | STANDARD |
| 11 | Responsive visibility patterns | "hidden lg:block ... lg:hidden ... w-full lg:max-w-md ... p-4 lg:p-8" | Use responsive utility classes for: desktop-only content, mobile-only content, responsive widths, and responsive padding | _[to be filled]_ | UNIVERSAL | POLISH |
| 12 | Layout structure dimensions | "Sidebar: 240px wide, bg-surface-base, border-r ... Header: Full width, bg-surface-base, border-b, h-16 ... Main: flex-1, overflow-y-auto, p-8" | Sidebar: ~240px wide, themed background, right border. Header: full width, themed background, bottom border, ~64px height. Main content: flex-1, scrollable, padded | _[to be filled]_ | UNIVERSAL | POLISH |
| 13 | Sidebar has bottom help link | "Bottom section: help link (always visible) ... p-4 border-t border-border-subtle" | Sidebar must have a pinned bottom section with a separator border containing a Help & Support link with an icon | _[to be filled]_ | UNIVERSAL | POLISH |
| 14 | Padding scales with breakpoint | "p-4 lg:p-8" | Main content padding: smaller on mobile (e.g., 16px), larger on desktop (e.g., 32px) | _[to be filled]_ | UNIVERSAL | POLISH |

---

### Design System

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | Typography scale | "Page Title: 24px Semi-bold ... Section Header: 18px Semi-bold ... Card Title: 16px Medium ... Body Text: 14px Regular ... Small/Meta: 12px Regular" | Define a 5-level typography scale: Page Title (24px semi-bold), Section Header (18px semi-bold), Card Title (16px medium), Body Text (14px regular), Small/Meta (12px regular). Each level maps to semantic color tokens | _[to be filled]_ | UNIVERSAL | STANDARD |
| 2 | Spacing scale | "Card padding: p-6 (24px) ... Section gaps: gap-6 (24px) ... Element gaps: gap-4 (16px)" | Card internal padding: 24px. Between sections: 24px gap. Between elements within a section: 16px gap | _[to be filled]_ | UNIVERSAL | POLISH |
| 3 | Card component class | "bg-surface-base rounded-card border border-border-subtle shadow-card p-6" | Standard card: themed background, custom border radius, subtle border, custom shadow, 24px padding | _[to be filled]_ | UNIVERSAL | STANDARD |
| 4 | Primary button class | "bg-brand hover:bg-brand-dark text-text-primary font-medium px-6 py-3 rounded-lg transition-colors" | Primary button: brand color, darker brand on hover, primary text, medium weight, horizontal+vertical padding, rounded corners, color transition | _[to be filled]_ | UNIVERSAL | STANDARD |
| 5 | Input field class | "bg-surface-muted text-text-primary placeholder:text-text-tertiary px-4 py-3 rounded-lg w-full outline-none focus:ring-2 focus:ring-brand" | Text inputs: muted background, primary text, tertiary placeholder, padding, rounded corners, full width, brand-colored focus ring | _[to be filled]_ | UNIVERSAL | STANDARD |
| 6 | Sidebar nav item classes | "space-y-2 ... text-sm text-text-secondary hover:text-text-primary" | Nav links: vertical stack with small gaps, small text, secondary color, primary color on hover | _[to be filled]_ | UNIVERSAL | POLISH |
| 7 | Sidebar recent items section | "mt-6 ... text-xs font-medium text-text-tertiary mb-2" | Sidebar optional items section: top margin, extra-small bold heading in tertiary color, labeled "Recent Items" or similar | _[to be filled]_ | UNIVERSAL | POLISH |

---

### Testing

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | Console clean before deploy | "Production apps must have zero console errors/warnings" | Open browser DevTools Console, navigate through entire app, fix all red errors and yellow warnings until console is clean | _[to be filled]_ | UNIVERSAL | STANDARD |
| 2 | No console.log statements | "No `console.log` statements (use proper error handling)" | Remove all `console.log` calls from production code; use notification components or structured error handling instead | _[to be filled]_ | UNIVERSAL | STANDARD |
| 3 | No framework list key warnings | "No React key warnings (always use unique keys in lists)" | Every list rendering must provide a unique key per item; never use array index as key for dynamic lists. (e.g., React: `key` prop, Vue: `:key` binding) | _[to be filled]_ | PATTERN | STANDARD |
| 4 | No missing dependency warnings | "No missing dependency warnings (fix useEffect deps)" | All reactive hooks/watchers must have complete dependency declarations; fix or suppress with documented justification. (e.g., React: `useEffect` deps, Vue: `watch` sources) | _[to be filled]_ | PATTERN | POLISH |
| 5 | No unused variables | "No unused variable warnings" | Remove all unused imports, variables, and parameters; zero warnings in linter output | _[to be filled]_ | UNIVERSAL | POLISH |
| 6 | No type errors | "No TypeScript errors" | Type checker must pass with zero errors; no type-ignore/suppress comments without documented reason | _[to be filled]_ | UNIVERSAL | CRITICAL |
| 7 | Full app navigation test | "Navigate through entire app" | Before deploying, manually click through every route, form, modal, and interactive element to verify no console errors | _[to be filled]_ | UNIVERSAL | STANDARD |

---

### Deployment/Hosting

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | Config uses placeholder values | "Firebase config in firebase.ts with placeholder values" | Service configuration file ships with `YOUR_API_KEY`, `YOUR_PROJECT_ID`, etc. as string placeholders; never hardcode real credentials in source control. (e.g., Firebase: `config/firebase.ts` with placeholders, Supabase: `.env` with `SUPABASE_URL` and `SUPABASE_ANON_KEY`) | _[to be filled]_ | PATTERN | CRITICAL |
| 2 | Favicon required | "Every app needs a favicon. Add to index.html" | Create a favicon (SVG preferred) with the app's initial letter and brand color; link in the HTML head | _[to be filled]_ | UNIVERSAL | POLISH |
| 3 | Error boundary wraps app | "Wrap app in error boundary to prevent white screen of death" | A top-level error boundary component wraps the entire app; shows "Something went wrong" with a Refresh button on unhandled errors | _[to be filled]_ | UNIVERSAL | CRITICAL |
| 4 | Dependency config locked | "IMPORTMAP IS LOCKED. DO NOT MODIFY." | Do not add, remove, or change versions in the dependency configuration without explicit approval. (e.g., importmap, package.json, requirements.txt) | _[to be filled]_ | PATTERN | STANDARD |
| 5 | No redundant package entries | "DO NOT ADD firebase/app, firebase/auth, or firebase/firestore to the importmap! The 'firebase/' trailing slash handles ALL Firebase imports. Adding specific paths will BREAK the app." | Do not add redundant or conflicting sub-package entries when the parent package already resolves them. (e.g., Firebase: single `firebase/` entry handles all sub-imports) | _[to be filled]_ | PATTERN | STANDARD |

---

### Post-Generation Steps

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | Replace service config placeholders | "After generation, open `src/config/firebase.ts` and replace the placeholder values with your actual Firebase config from the Firebase Console." | Open the service configuration file and replace all `YOUR_*` placeholder strings with real values from the service provider's dashboard. (e.g., Firebase Console, Supabase Dashboard, AWS Console) | _[to be filled]_ | PATTERN | STANDARD |
| 2 | Replace favicon letter | "Replace 'A' with app's first letter and fill color with brand color." | Edit the favicon: change the letter to the app's initial and the background to the brand primary color | _[to be filled]_ | UNIVERSAL | POLISH |
| 3 | Replace app name in title hook | "const appName = 'AppName'; // Replace with your app name" | In the page title hook/utility, change the app name constant to the actual application name | _[to be filled]_ | UNIVERSAL | STANDARD |
| 4 | Set data category names for delete | "List all subcollections your app uses" | In the account deletion handler, update the data category list to include every user-data table/collection used by the app. (e.g., Firebase: subcollection names, SQL: table names) | _[to be filled]_ | PATTERN | STANDARD |
| 5 | Set help email | "mailto:support@yourdomain.com" | Replace the placeholder email in the Help & Support link with the real support email address | _[to be filled]_ | UNIVERSAL | STANDARD |

---

### Build Instructions

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | Complete file structure | "Create the complete file structure" | Generate all files listed in the file structure section; one component per file; group related components in feature folders | _[to be filled]_ | UNIVERSAL | STANDARD |
| 2 | Follow exact patterns | "Implement all components following the exact patterns" | Use the provided code patterns verbatim for: auth context, theme context, route guards, error boundary, data service layer, and all UI components | _[to be filled]_ | UNIVERSAL | STANDARD |
| 3 | Build Section 2 features | "Build the features described in Section 2" | Implement all core features from the app specification using the CRUD view pattern (List > Detail > Create > Edit) | _[to be filled]_ | UNIVERSAL | STANDARD |
| 4 | Apply design system styling | "Apply the styling from Section 3 using the design system" | Use the design tokens mapped to the CSS variable system; respect typography scale, spacing, card styles, and color tokens | _[to be filled]_ | UNIVERSAL | STANDARD |
| 5 | Auth and data access working | "Ensure all routes, auth flows, and Firestore operations work" | Sign-in flow, protected routes, database CRUD through the service layer, and role-based access must all function end-to-end. (e.g., Firebase: Google Sign-In + Firestore, Supabase: OAuth + Postgres) | _[to be filled]_ | PATTERN | CRITICAL |
| 6 | Production ready | "Make it production-ready with proper error handling" | ErrorBoundary, Toast feedback on all actions, ConfirmModal on destructive actions, Skeleton loading states, offline handling, session expiry handling | _[to be filled]_ | UNIVERSAL | CRITICAL |
| 7 | Single icon library | "Use Lucide React for all icons. Consistent style, tree-shakeable." | Import all icons from the project's designated icon library; use a consistent standard size; spinner icon with animation for loading states | _[to be filled]_ | STACK-SPECIFIC | POLISH |
| 8 | Dynamic page titles | "Update document title on each page" | Every page component updates `document.title` via a shared hook/utility to `"Page Name - AppName"` format | _[to be filled]_ | UNIVERSAL | POLISH |
| 9 | Autofocus on forms | "First input should be focused when page/modal loads" | Focus the first input field on page/modal mount; for modals, focus first input when opened | _[to be filled]_ | UNIVERSAL | POLISH |
| 10 | Pluralization helper | "Never show '1 items' - always handle plurals" | Create a `pluralize(count, singular, plural?)` utility function; use it everywhere counts are displayed | _[to be filled]_ | UNIVERSAL | POLISH |
| 11 | Search/filter for lists | "Any list that can grow needs search/filter" | Lists expected to exceed 5 items must include a search input filtering by title and description; show "No results for '...'" when filter yields empty | _[to be filled]_ | UNIVERSAL | POLISH |
| 12 | Retry on error states | "Error states should be actionable, not dead ends" | Every error display includes a "Try Again" button that re-invokes the failed operation; notifications may include a retry action | _[to be filled]_ | UNIVERSAL | STANDARD |
| 13 | Network/offline handling | "Handle Firebase/network errors gracefully" | Wrap database calls to catch network and permission errors with user-friendly messages; monitor `navigator.onLine` and show an offline banner. (e.g., Firebase: catch `unavailable` and `permission-denied` codes) | _[to be filled]_ | PATTERN | STANDARD |
| 14 | Session expiry handling | "Firebase tokens expire. Handle gracefully" | Catch authentication expiry errors in data access calls; show "Session expired" notification and redirect to login. (e.g., Firebase: catch `unauthenticated` errors, Supabase: handle JWT expiry) | _[to be filled]_ | PATTERN | CRITICAL |
| 15 | Loading button pattern | "Buttons during async actions must show loading state" | Button component accepts a `loading` prop; when true, show a spinner icon, update text, and set `disabled` | _[to be filled]_ | UNIVERSAL | POLISH |
| 16 | User avatar with fallback | "Google profile images can fail. Always have fallback" | Avatar component shows profile image with an `onError` handler that falls back to initials derived from the user's name (max 2 characters) | _[to be filled]_ | UNIVERSAL | POLISH |
| 17 | Form field states | "Forms need proper visual states" | Every form input handles 6 states: default (empty), focused (ring), filled, error (red border + message), disabled (reduced opacity), helper text | _[to be filled]_ | UNIVERSAL | STANDARD |
| 18 | Unsaved changes warning | "Warn users before losing form data" | Implement an unsaved-changes guard using `beforeunload` event for browser navigation; also intercept in-app navigation with a confirmation dialog | _[to be filled]_ | UNIVERSAL | STANDARD |
| 19 | 404 / not found handling | "Handle invalid routes and missing data" | Add a catch-all route for unmatched URLs; detail pages show an EmptyState with "Item not found" when the requested data doesn't exist | _[to be filled]_ | UNIVERSAL | STANDARD |
| 20 | Hover states on all interactives | "Every clickable element should visually respond to hover." | Cards: elevated shadow + slight translate; Buttons: darker shade; Links: underline; Icon buttons: muted background; Table rows: muted background; all with transitions | _[to be filled]_ | UNIVERSAL | POLISH |
| 21 | Date formatting | "Never show raw timestamps. Format dates for humans" | Create a date formatting utility returning relative time strings: "Just now", "5m ago", "2h ago", "Yesterday", "3d ago", "Jan 15", or "Jan 15, 2024" | _[to be filled]_ | UNIVERSAL | STANDARD |
| 22 | Text truncation | "Long text MUST be truncated to prevent layout breaking" | Sidebar items: truncate with max-width; Card descriptions: clamp to 2 lines; Table cells: truncate with max-width. Always set a max-width when truncating | _[to be filled]_ | UNIVERSAL | STANDARD |
| 23 | Back navigation | "Every detail/edit page MUST have back navigation" | Place a back button at the top of every detail/edit page using browser history back or explicit link to the parent list route | _[to be filled]_ | UNIVERSAL | STANDARD |
| 24 | Transitions and animations | "Add subtle animations for polish" | Required: modal fade/scale (200ms), toast slide-in (300ms), card hover lift (200ms), button press scale (150ms), sidebar slide on mobile | _[to be filled]_ | UNIVERSAL | POLISH |
| 25 | Accessibility - focus states | "All interactive elements need visible focus" | Apply visible focus indicators (focus ring in brand color with offset) to all buttons, inputs, and links | _[to be filled]_ | UNIVERSAL | STANDARD |
| 26 | Accessibility - keyboard nav | "Modals must handle Escape key" | Add keyboard listener for Escape to close modals; implement focus trap within modals (Tab cycles through modal elements only) | _[to be filled]_ | UNIVERSAL | STANDARD |
| 27 | Accessibility - icon buttons | "Icon-only buttons need aria-label" | Every button with only an icon (no visible text) must have an `aria-label` describing the action | _[to be filled]_ | UNIVERSAL | STANDARD |
| 28 | Accessibility - screen reader | "Loading states" need sr-only text | Add screen-reader-only text for visual-only loading indicators; use `role="status"` and `aria-live="polite"` for dynamic status text | _[to be filled]_ | UNIVERSAL | STANDARD |
| 29 | Pagination or load-more | "Lists MUST handle large amounts of data" | Choose ONE pagination approach (pagination / load more / infinite scroll) and implement consistently across all list views; 10-20 items per page | _[to be filled]_ | UNIVERSAL | STANDARD |
| 30 | CSS variables for dark mode | "DO NOT hardcode dark colors directly in Tailwind config. Use `var(--color-*)` references so the theme toggle works." | Define light mode values in `:root` and dark mode overrides in a toggled class; reference via CSS custom properties. Never hardcode color values directly in the styling framework config | _[to be filled]_ | UNIVERSAL | STANDARD |

---

### Miscellaneous Rules

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | No database calls in components | "NO Firestore calls in components - use firestore service only" | All database/API operations go through a service layer module; components call service functions, never import database client libraries directly. (e.g., Firebase: no `firebase/firestore` imports in components) | _[to be filled]_ | PATTERN | STANDARD |
| 2 | No unprotected auth routes | "NO unprotected routes for authenticated features" | Every route that requires login must be wrapped in a route guard component | _[to be filled]_ | UNIVERSAL | CRITICAL |
| 3 | No inline styles | "NO inline styles - Tailwind only" | Never use inline `style` attributes; all styling via the project's designated styling methodology | _[to be filled]_ | UNIVERSAL | STANDARD |
| 4 | No `any` types | "NO `any` types - define TypeScript interfaces" | Define typed interfaces/schemas for all data shapes; no untyped (`any`) values in function signatures, state, or props | _[to be filled]_ | UNIVERSAL | STANDARD |
| 5 | Timestamps on all writes | "ALL Firestore writes include createdAt/updatedAt timestamps" | Every database create includes `createdAt` and `updatedAt` with server-generated timestamps; every update sets `updatedAt`. (e.g., Firebase: `serverTimestamp()`, Supabase: `now()` default column, SQL: `DEFAULT CURRENT_TIMESTAMP`) | _[to be filled]_ | PATTERN | CRITICAL |
| 6 | User data scoped to owner | "ALL user data in subcollections under users/{uid}/" | Never store user data in shared/global tables without user scoping; all user-owned data accessed via user-specific paths or filters. (e.g., Firebase: `users/{uid}/{collection}`, SQL: `WHERE user_id = ?`) | _[to be filled]_ | PATTERN | CRITICAL |
| 7 | Detail view separate from edit | "ALL saved items have Detail View (read-only) separate from Edit View" | Detail page is read-only display; editing happens on a separate route; never combine view and edit in one component | _[to be filled]_ | UNIVERSAL | STANDARD |
| 8 | Validate before submit | "ALL forms validate before submission" | Client-side validation on all required fields before calling the backend; show inline error messages per field | _[to be filled]_ | UNIVERSAL | CRITICAL |
| 9 | One component per file | "One component per file." | Each UI component lives in its own file; no multi-component files | _[to be filled]_ | UNIVERSAL | STANDARD |
| 10 | Feature folders for grouping | "Group related components in feature folders." | Related components go in feature-named directories; don't flatten everything into a single components folder | _[to be filled]_ | UNIVERSAL | STANDARD |
| 11 | Interfaces for all data types | "Create interfaces for all data types." | Every data shape used in the database, props, or state has a corresponding type definition in a centralized types file | _[to be filled]_ | UNIVERSAL | STANDARD |
| 12 | Custom hooks for reusable logic | "Add custom hooks for reusable logic." | Extract shared stateful logic into reusable hook/composable files; components should be thin wrappers over these abstractions | _[to be filled]_ | UNIVERSAL | POLISH |
| 13 | No pinned AI SDK versions | "DO NOT pin a version number. Let esm.sh resolve the latest compatible version." | When adding optional AI SDK dependencies, do not pin to a specific version unless required for stability; let the package manager resolve the latest compatible version. (e.g., `@google/genai` via esm.sh without version pin) | _[to be filled]_ | STACK-SPECIFIC | POLISH |
| 14 | Mobile-first responsive | "Build mobile-first. Design for mobile, then scale up for larger screens." | Default styles target mobile; use progressive breakpoint prefixes to add tablet/desktop overrides | _[to be filled]_ | UNIVERSAL | STANDARD |
| 15 | Touch targets 44px minimum | "Minimum 44px x 44px for all clickable elements on mobile" | Add padding to small icons/buttons to meet 44px minimum tap target; ensure adequate spacing between adjacent touch targets | _[to be filled]_ | UNIVERSAL | STANDARD |
| 16 | Service init order | "CRITICAL: Import order matters - app must be initialized FIRST" | Backend service client must be initialized before dependent services are instantiated; incorrect order causes runtime crashes. (e.g., Firebase: `initializeApp()` before `getAuth()` and `getFirestore()`) | _[to be filled]_ | PATTERN | CRITICAL |
| 17 | Role only editable via admin tools | "role only editable via Firebase Console" | Server-side data access rules must prevent users from modifying their own role; role changes only through admin tools or direct database access. (e.g., Firebase: security rules, Supabase: RLS policies, custom backend: admin-only endpoint) | _[to be filled]_ | PATTERN | CRITICAL |
| 18 | Default role is lowest privilege | "Default role - change via Firebase Console" | New user profiles are created with the lowest-privilege role; server-side rules enforce this default on create. (e.g., Firebase: security rules enforce `role == 'user'` on create) | _[to be filled]_ | PATTERN | CRITICAL |

---

### Complete Banned Patterns

Every prohibition Martin states across the entire document, collected into one list:

| # | Banned Pattern | Martin Says | Why Banned (Agnostic) | Type | Severity |
|---|----------------|-------------|----------------------|------|----------|
| 1 | No `alert()` | "No `alert()` -- use Toast for messages" | Native browser `alert()` blocks the UI thread and provides no styling control; use a Toast/notification component instead | UNIVERSAL | STANDARD |
| 2 | No `confirm()` | "No `confirm()` -- use ConfirmModal for confirmations" | Native browser `confirm()` blocks the UI thread and is not customizable; use a ConfirmModal component instead | UNIVERSAL | STANDARD |
| 3 | No `prompt()` | "No `prompt()` -- use a proper form Modal" | Native browser `prompt()` blocks the UI thread and provides no validation; use a Modal with a proper form instead | UNIVERSAL | STANDARD |
| 4 | No `console.log` for user feedback | "No `console.log` for user feedback -- use Toast" | Console output is invisible to users; use Toast/notification components for user-facing feedback | UNIVERSAL | POLISH |
| 5 | No text-only empty states | "No text-only empty states -- use EmptyState component with icon and CTA" | Plain "No items" text is a dead end; empty states need an icon, descriptive message, and call-to-action button | UNIVERSAL | POLISH |
| 6 | No browser default dialogs | "No browser default dialogs of any kind" | All native browser dialogs (`alert`, `confirm`, `prompt`, `beforeunload` default) replaced with custom UI components | UNIVERSAL | STANDARD |
| 7 | No external state libraries | "No external state libraries (Redux, Zustand, etc.) -- React Context only" | Use the framework's built-in state management; no third-party state libraries unless explicitly approved in project config | STACK-SPECIFIC | STANDARD |
| 8 | No containerization | "No Docker" | No Dockerfiles or containerization in the project scaffold; deployment handled by the configured hosting platform | STACK-SPECIFIC | STANDARD |
| 9 | No custom backend | "No backend APIs (Firebase/Firestore only)" | No custom server-side code; all backend functionality provided by the configured BaaS or serverless platform | STACK-SPECIFIC | STANDARD |
| 10 | No inline styles | "No inline styles -- Tailwind only" | Never use inline `style` attributes; all styling via the project's designated CSS methodology | UNIVERSAL | STANDARD |
| 11 | No `any` types | "No `any` types -- define TypeScript interfaces" | Define typed interfaces for all data shapes; no untyped values in function signatures, state, or props | UNIVERSAL | STANDARD |
| 12 | No database calls in components | "No Firestore calls in components -- use firestore service only" | UI components never import or call database client libraries directly; all data access through a service layer. (e.g., Firebase: no Firestore in components) | PATTERN | STANDARD |
| 13 | No unprotected auth routes | "No unprotected routes for authenticated features" | Every route requiring authentication must be wrapped in a route guard component | UNIVERSAL | CRITICAL |
| 14 | No hardcoded theme colors | "No hardcoded dark colors in Tailwind config -- use `var(--color-*)` references" | Never hardcode color values directly in the styling framework config; use CSS custom properties so theme toggling works | UNIVERSAL | STANDARD |
| 15 | No modifying locked dependencies | "No modifying the importmap (locked, copy exactly as shown)" | Dependency versions are locked; no changes without explicit approval | STACK-SPECIFIC | STANDARD |
| 16 | No redundant sub-package entries | "No adding `firebase/app`, `firebase/auth`, or `firebase/firestore` to the importmap individually" | Do not add redundant sub-package entries when the parent package already resolves them. (e.g., Firebase: single `firebase/` entry handles all sub-imports) | STACK-SPECIFIC | STANDARD |
| 17 | No pinned AI SDK versions | "No pinning version numbers for `@google/genai` in the importmap" | Do not pin optional AI SDK dependencies to specific versions unless required for stability | STACK-SPECIFIC | POLISH |
| 18 | No edit-first pattern | "No clicking a saved item to open it directly in edit mode" | Items always open in read-only Detail view first; Edit is a separate action and view | UNIVERSAL | STANDARD |
| 19 | No reusing Create form as Edit | "No using the Create form as the Edit form by pre-loading data" | Create and Edit are separate views/components; do not pre-load data into a Create form to simulate editing | UNIVERSAL | STANDARD |
| 20 | No view-only impossible | "No 'view-only impossible' pattern (must be able to view without editing)" | Users must be able to view any item without entering edit mode | UNIVERSAL | STANDARD |
| 21 | No combined view+edit component | "No single 'smart' component that handles both view and edit" | View (Detail) and Edit must be separate components; no mode-switching within a single component | UNIVERSAL | STANDARD |
| 22 | No delete without confirmation | "No delete without confirmation (ConfirmModal required)" | Every delete action must go through a confirmation dialog with explicit user confirmation | UNIVERSAL | STANDARD |
| 23 | No silent operations | "No success/error actions without feedback to user (Toast required)" | Every mutation must show success or error feedback via a notification component | UNIVERSAL | POLISH |
| 24 | No dead-end empty lists | "No empty lists with just 'No items' text (needs icon + CTA via EmptyState)" | Empty list states must include an icon, message, and call-to-action button via EmptyState component | UNIVERSAL | POLISH |
| 25 | No bare loading text | "No loading states that are just the word 'Loading...' (use Skeleton or spinner)" | Use Skeleton placeholders or spinner components, never bare "Loading..." text | UNIVERSAL | POLISH |
| 26 | No raw timestamps | "No raw timestamps displayed to users (use relative time formatting)" | All timestamps displayed as human-readable relative time via a formatting utility | UNIVERSAL | POLISH |
| 27 | No untruncated long text | "No untruncated long text (use `truncate` or `line-clamp-*`)" | Long text must be truncated or clamped to prevent layout breaking; always set a max-width constraint | UNIVERSAL | POLISH |
| 28 | No missing back navigation | "No detail/edit pages without back navigation" | Every detail/edit page must have a back button at the top | UNIVERSAL | POLISH |
| 29 | No list key warnings | "No React key warnings in console" | Every list rendering must provide unique keys; zero key-related warnings in console. (e.g., React: `key` prop, Vue: `:key`) | PATTERN | POLISH |
| 30 | No missing dependency warnings | "No missing useEffect dependency warnings" | All reactive hooks must have complete dependency arrays; zero dependency warnings. (e.g., React: `useEffect` deps) | PATTERN | POLISH |
| 31 | No unused variables | "No unused variable warnings" | Remove all unused imports, variables, and parameters; zero unused-variable warnings | UNIVERSAL | POLISH |
| 32 | No type errors in production | "No TypeScript errors in production" | Type checker must pass with zero errors before deployment | UNIVERSAL | CRITICAL |
| 33 | No writes without timestamps | "No Firestore writes without `createdAt`/`updatedAt` timestamps" | Every database write must include server-generated timestamps; creates set both `createdAt` and `updatedAt`; updates set `updatedAt`. (e.g., Firebase: `serverTimestamp()`) | PATTERN | CRITICAL |
| 34 | No unscoped user data | "No user data stored in top-level Firestore collections (must be subcollections under `users/{uid}/`)" | Never store user-owned data in shared/global tables without user scoping. (e.g., Firebase: nest under `users/{uid}/`, SQL: `user_id` foreign key) | PATTERN | CRITICAL |
| 35 | No unvalidated form submissions | "No forms without validation before submission" | All forms must validate required fields client-side before submitting; show inline error messages per field | UNIVERSAL | CRITICAL |
| 36 | No buttons without loading state | "No buttons without loading state during async actions" | Buttons triggering async operations must show a loading spinner and become disabled during the operation | UNIVERSAL | POLISH |
| 37 | No avatars without fallback | "No avatars without fallback for failed images" | Avatar components must handle image load failures by showing initials or a default icon | UNIVERSAL | POLISH |
| 38 | No pages without dynamic title | "No pages without dynamic document title (usePageTitle hook)" | Every page must update `document.title` via a shared utility to reflect the current page name | UNIVERSAL | POLISH |
| 39 | No forms without autofocus | "No forms without autofocus on first input" | The first input field in every form/modal must receive focus automatically on mount | UNIVERSAL | POLISH |
| 40 | No growable lists without search | "No growable lists without search/filter (when >5 items expected)" | Lists expected to exceed 5 items must include a search/filter input | UNIVERSAL | POLISH |
| 41 | No error dead ends | "No error states without retry action" | Every error display must include a "Try Again" button that re-invokes the failed operation | UNIVERSAL | POLISH |
| 42 | No mixed icon libraries | "No icons from libraries other than Lucide React" | Use a single, consistent icon library throughout the app; do not mix icons from different sources | STACK-SPECIFIC | POLISH |
| 43 | No console errors in production | "No console errors/warnings in production" | Zero console errors and warnings in the deployed app; navigate entire app in DevTools to verify | UNIVERSAL | STANDARD |

---

## Quality Verification Summary

### Rule Count
- **Category rules:** ~195 across 22 categories
- **Banned patterns:** 43
- **Total:** ~238

### Type Distribution
- **UNIVERSAL:** ~168 rules (principles that apply to any stack as-is)
- **STACK-SPECIFIC:** ~24 rules (rewritten from Firebase/React-specific to generic)
- **PATTERN:** ~46 rules (universal principle extracted, stack example noted)

### Severity Distribution
- **CRITICAL:** ~40 rules (security, auth, data integrity, build-breaking)
- **STANDARD:** ~141 rules (UX quality, component patterns, code organization)
- **POLISH:** ~59 rules (cosmetic, animation, spacing, naming)


---
## REFERENCE: Industry Standards Checklist

# Industry Standards Supplement Checklist

> Covers structural rules that Martin's checklist does not address.
> This checklist + Martin's agnostic checklist = complete structural coverage for any app spec.
>
> Sources: IEEE 830, FURPS+, Volere, arc42, C4 Model, 12-Factor App, WCAG 2.1 AA
>
> **Numbering starts at 200** to avoid collision with Martin's rules 1-192.
> **Severity distribution:** 14 CRITICAL (20%), 34 STANDARD (49%), 21 POLISH (31%)

---

### 1. Internationalization (i18n)

Covers string externalization, locale-aware formatting, and multi-language readiness. Even apps that launch in one language must be structured so adding a second language doesn't require rewriting every component. Gaps here create tech debt that compounds per-page.

**Source frameworks:** IEEE 830 (functionality requirements), FURPS+ (usability/supportability)

| # | Rule | Description | Technical Spec | Boilerplate Match | Severity |
|---|------|-------------|----------------|-------------------|----------|
| 200 | Externalize all user-facing strings | No hardcoded user-facing text in component files. All strings come from a translation resource file. | Every string rendered to the user (labels, buttons, headings, placeholders, error messages, toast messages) must be loaded from a key-value translation file (e.g., `en.json`, `es.json`). Direct string literals in JSX/HTML/template markup are prohibited. Developer-only strings (console logs, code comments) are exempt. | _[to be filled]_ | STANDARD |
| 201 | Translation key naming convention | Translation keys follow a hierarchical, predictable naming scheme. | Keys use dot-notation matching the feature and element: `{page}.{section}.{element}`. Example: `dashboard.header.title`, `auth.login.submitButton`, `errors.network.timeout`. No flat keys like `btn1` or `title`. Keys must be lowercase with no spaces. | _[to be filled]_ | STANDARD |
| 202 | Locale-aware date formatting | Dates display in the user's locale format, not a hardcoded format. | All date rendering must use the runtime locale (e.g., `Intl.DateTimeFormat` in JS, `DateFormat` in Dart, locale-aware libraries in other stacks). No hardcoded date format strings like `MM/DD/YYYY`. The locale is determined by the user's language setting or browser locale. | _[to be filled]_ | STANDARD |
| 203 | Locale-aware number and currency formatting | Numbers and currencies display with locale-correct separators and symbols. | All number display (counts, prices, percentages) must use locale-aware formatting (e.g., `Intl.NumberFormat`). No hardcoded decimal separators (`.` vs `,`), no hardcoded currency symbols (`$`). Currency code is passed as a parameter, not embedded in format strings. | _[to be filled]_ | STANDARD |
| 204 | RTL layout readiness | Layout uses logical properties so RTL languages render correctly without code changes. | CSS/styling uses logical properties (`margin-inline-start` not `margin-left`, `padding-inline-end` not `padding-right`, `start`/`end` not `left`/`right` for flex/grid alignment). If the styling framework doesn't support logical properties natively, a directional abstraction layer must exist. Icons with directional meaning (arrows, chevrons) must flip in RTL. | _[to be filled]_ | POLISH |
| 205 | Pluralization handling | Plural forms use locale rules, not ternary operators. | Pluralization must use ICU MessageFormat or equivalent (e.g., `{count, plural, one {# item} other {# items}}`). No inline ternary logic like `count === 1 ? 'item' : 'items'`. The translation system must support at least the plural categories: `zero`, `one`, `two`, `few`, `many`, `other` (languages like Arabic use all six). | _[to be filled]_ | POLISH |
| 206 | Language detection and fallback chain | App detects the user's preferred language and falls back gracefully if translations are missing. | Language selection follows this priority: (1) user's explicit language setting stored in their profile, (2) browser/device language preference, (3) app default language. If a translation key is missing for the current locale, the app falls back to the default language rather than showing a raw key like `dashboard.header.title`. Missing keys must log a warning in development mode. | _[to be filled]_ | POLISH |
| 207 | Translation file completeness check | Every supported language has all keys present. | A CI/build step must verify that all translation files contain the same set of keys. If `en.json` has 200 keys and `es.json` has 198, the build warns (not fails) listing the 2 missing keys. In development, missing keys render with a visible marker (e.g., `[MISSING: key.name]`) so they're caught during manual testing. | _[to be filled]_ | POLISH |

---

### 2. Config Externalization

Covers separation of configuration from code. Environment-specific values (URLs, keys, feature flags) must live outside the codebase so the same build artifact runs in any environment without code changes.

**Source frameworks:** 12-Factor App (Factor III: Config), arc42 (cross-cutting concepts)

| # | Rule | Description | Technical Spec | Boilerplate Match | Severity |
|---|------|-------------|----------------|-------------------|----------|
| 208 | No hardcoded environment URLs | API endpoints, service URLs, and CDN paths are never hardcoded in source files. | All URLs that differ between environments (API base URL, auth endpoint, storage bucket URL, WebSocket endpoint) must be read from environment variables or a runtime config object populated by env vars. Grep the codebase for `http://` and `https://` — every match must be either (a) in an env config file, (b) in a test fixture, or (c) a documentation URL in a comment. | _[to be filled]_ | CRITICAL |
| 209 | Secrets never in source control | API keys, tokens, passwords, and private keys never appear in committed files. | No file in the repository contains a live secret value. All secrets are loaded from environment variables at runtime. The repo must contain a `.env.example` (or equivalent) with placeholder values documenting every required secret variable. A `.gitignore` entry must block `.env`, `.env.local`, and any file matching `*.secret.*`. | _[to be filled]_ | CRITICAL |
| 210 | Secrets never in client bundles | Secrets are never included in frontend/client-side build output. | No environment variable containing a secret (API secret key, service account key, database password) is referenced by client-side code. Only public client identifiers (e.g., public API key, project ID) may appear in client bundles. Build tooling must be configured so that server-only env vars are not available to client-side bundling (e.g., `NEXT_PUBLIC_` prefix convention, Vite's `VITE_` prefix, or equivalent gating mechanism). | _[to be filled]_ | CRITICAL |
| 211 | Configuration hierarchy | Config values follow a clear precedence order. | Configuration resolution order (lowest to highest priority): (1) hardcoded defaults in code, (2) config files checked into repo (non-secret defaults), (3) environment variables, (4) runtime overrides (CLI flags, admin panel). Higher-priority sources override lower ones. The app documents this hierarchy in a README or config reference. | _[to be filled]_ | STANDARD |
| 212 | Feature flags as config | Feature toggles are controlled via config, not code branches. | Features that can be enabled/disabled use a boolean config value (env var or remote config) rather than commenting out code or using git branches. Format: `FEATURE_{NAME}_ENABLED=true|false`. The codebase checks this flag at runtime. Disabled features must not render UI elements or execute backend logic — they are fully gated, not hidden with CSS. | _[to be filled]_ | STANDARD |
| 213 | Build-time vs runtime config separation | The app distinguishes values baked into the build from values resolved at runtime. | Build-time config (framework version, feature flags that affect code splitting, public API base URL) is set during build and cannot change without rebuilding. Runtime config (user-specific settings, A/B test assignments, dynamic feature flags) is loaded after the app starts via API call or injected script tag. The codebase clearly separates these in different config files or namespaces. No runtime decision depends on a build-time-only value that could be stale. | _[to be filled]_ | STANDARD |
| 214 | Env var validation at startup | The app validates that all required environment variables are present before starting. | On server startup (or build start for static apps), the app checks that every required env var is set and non-empty. If any are missing, the app exits immediately with an error message listing every missing variable — not a cryptic crash three minutes later when the var is first used. Optional env vars have documented defaults. Validation happens in a single config module, not scattered across the codebase. | _[to be filled]_ | STANDARD |

---

### 3. Environment Parity (Dev/Staging/Prod)

Covers keeping development, staging, and production environments as similar as possible. Divergence between environments is the #1 cause of "works on my machine" bugs that waste developer time and break production.

**Source frameworks:** 12-Factor App (Factor X: Dev/Prod Parity)

| # | Rule | Description | Technical Spec | Boilerplate Match | Severity |
|---|------|-------------|----------------|-------------------|----------|
| 215 | Same database technology across environments | Dev and prod use the same database engine. | If production uses PostgreSQL, development uses PostgreSQL — not SQLite. If production uses MongoDB, development uses MongoDB — not a JSON file. The database version in development must be within one major version of production. Docker Compose or equivalent can provide the database locally. Exceptions only for unit tests that use an in-memory test double clearly marked as non-integration tests. | _[to be filled]_ | CRITICAL |
| 216 | Same auth flow in all environments | Authentication uses the same provider and flow in dev and prod. | No mock auth in development that bypasses the real auth flow. If prod uses OAuth, dev uses OAuth (against a test tenant or sandbox provider). If a local auth emulator exists (e.g., Firebase Auth Emulator, Supabase local), it must implement the same API contract. A `DEV_BYPASS_AUTH=true` env var may exist for rapid prototyping but must be blocked from running in staging/production by the env var validation step. | _[to be filled]_ | CRITICAL |
| 217 | Config via env vars only, not code branches | No `if (environment === 'development')` in application logic. | Environment-specific behavior is controlled exclusively through configuration values (env vars, config files), never through code branches that check the environment name. `process.env.NODE_ENV` (or equivalent) may only be checked by the build tool and the config loader — never in business logic, component rendering, or API handlers. | _[to be filled]_ | STANDARD |
| 218 | Seed data strategy for development | Development has a reproducible way to populate the database with test data. | A seed script or migration exists that populates the development database with realistic test data covering all user roles, common data states (empty, normal, edge cases), and relationships. Running the seed is a single command documented in the README. Seed data uses consistent IDs so developers can reference them in manual testing. Seed data never contains real user information. | _[to be filled]_ | STANDARD |
| 219 | Production data never in development | Real user data is never copied to development environments. | No database dump from production is imported into development or staging. No script exists to sync production data to other environments. If realistic data is needed, it must be generated synthetically by the seed script. This rule is non-negotiable for GDPR/CCPA compliance and liability. | _[to be filled]_ | CRITICAL |
| 220 | Reproducible dev environment setup | A new developer can set up the full development environment in one command. | The project README contains a "Getting Started" section with a single setup command (e.g., `docker compose up`, `make setup`, `npm run setup`) that installs dependencies, starts required services (database, cache, auth), and runs migrations. The setup must complete without manual steps beyond cloning the repo and running the command. Any required system tools (Docker, Node, Python) are listed as prerequisites with version requirements. | _[to be filled]_ | STANDARD |

---

### 4. Logging Strategy

Covers structured logging, log levels, correlation IDs, and the principle that logs are event streams routed by the environment, not managed by the app itself. Martin mentions banning `console.log` but provides no alternative logging architecture.

**Source frameworks:** 12-Factor App (Factor XI: Logs), arc42 (cross-cutting concepts)

| # | Rule | Description | Technical Spec | Boilerplate Match | Severity |
|---|------|-------------|----------------|-------------------|----------|
| 221 | Structured log format | All server-side logs use structured format, not string concatenation. | Every log entry must be a structured object (JSON or equivalent) with at minimum these fields: `timestamp` (ISO 8601), `level` (ERROR/WARN/INFO/DEBUG), `message` (human-readable string), `service` (app/service name). Additional context fields are added as key-value pairs on the object, not concatenated into the message string. Example: `{"timestamp":"2026-04-02T12:00:00Z","level":"ERROR","service":"api","message":"Payment failed","orderId":"abc123","errorCode":"CARD_DECLINED"}` — NOT `"ERROR: Payment failed for order abc123 - CARD_DECLINED"`. | _[to be filled]_ | STANDARD |
| 222 | Log level usage guidelines | Each log level has a defined meaning that is consistent across the codebase. | `ERROR`: Something failed that requires investigation — a request could not be fulfilled, data was lost, an external service is unreachable after retries. `WARN`: Something unexpected happened but the operation completed — deprecated API used, fallback triggered, slow query. `INFO`: Normal operational events — server started, user logged in, payment processed, background job completed. `DEBUG`: Detailed diagnostic info only useful during development — function inputs/outputs, cache hit/miss, SQL queries. All developers on the project follow these definitions. | _[to be filled]_ | STANDARD |
| 223 | No raw console output in production code | Server-side production code uses the structured logger, not console.log/print. | No `console.log()`, `console.warn()`, `console.error()`, `print()`, or `System.out.println()` in production server code. All logging goes through the structured logging utility. Exception: client-side code may use `console.error()` as a last-resort fallback when the error reporting service itself fails. A lint rule or CI check enforces this by flagging raw console calls in server-side directories. | _[to be filled]_ | STANDARD |
| 224 | Request correlation ID | Every incoming request is assigned a unique ID that propagates through all related log entries and downstream calls. | When a request arrives at the server, middleware assigns a UUID correlation ID (or reads one from a `X-Request-ID` / `X-Correlation-ID` header if present). This ID is: (a) included in every log entry generated while handling that request, (b) passed to any downstream service calls as a header, (c) returned to the client in the response headers. This enables tracing a single user action across all log entries. | _[to be filled]_ | STANDARD |
| 225 | Sensitive data never logged | Passwords, tokens, credit card numbers, and PII are excluded from all log output. | Log entries must never contain: passwords, API secret keys, auth tokens, session tokens, credit card numbers, Social Security numbers, or unmasked email addresses. If any of these values must appear for debugging, they are masked (e.g., `tok_****abc`, `user@****.com`). A code review checklist item verifies that new log statements do not leak sensitive data. The structured logger has a sanitization middleware that redacts fields matching patterns like `password`, `secret`, `token`, `authorization`, `creditCard`, `ssn`. | _[to be filled]_ | CRITICAL |
| 226 | Logs to stdout/stderr | The application writes logs to standard output streams, not to files. | Server processes write all log output to `stdout` (INFO, DEBUG) and `stderr` (ERROR, WARN). The application never opens, writes, rotates, or manages log files directly. Log routing (to files, to a log aggregator, to a cloud service) is handled by the execution environment (container orchestrator, process manager, cloud platform). This keeps the app portable across hosting environments. | _[to be filled]_ | STANDARD |
| 227 | Client-side error reporting | Uncaught exceptions and unhandled promise rejections in the browser/client are captured and reported. | The client app installs a global error boundary (or equivalent) that catches uncaught exceptions and unhandled promise rejections. Captured errors are sent to an error reporting endpoint (server API route or third-party service) with: error message, stack trace, browser/device info, current route/page, and user ID (if authenticated). In development, errors also log to the console. The error boundary renders a user-friendly fallback UI, not a blank screen. | _[to be filled]_ | STANDARD |
| 228 | Log retention and size limits | Logging does not consume unbounded disk or memory. | If the app runs in an environment where logs accumulate locally (not a managed cloud service), a log rotation policy is configured: max file size (e.g., 10MB), max number of files (e.g., 5), or max retention period (e.g., 30 days). In containerized environments where logs go to stdout, the container runtime's log driver handles rotation. The app never accumulates an unbounded in-memory log buffer. | _[to be filled]_ | POLISH |

---

### 5. Dependency Management

Covers explicit dependency declaration, lockfiles, version pinning, and audit policies. Martin's checklist specifies the stack (React, TypeScript, etc.) but says nothing about how dependencies are managed, updated, or secured.

**Source frameworks:** 12-Factor App (Factor II: Dependencies)

| # | Rule | Description | Technical Spec | Boilerplate Match | Severity |
|---|------|-------------|----------------|-------------------|----------|
| 229 | Lockfile committed to source control | The dependency lockfile is always committed alongside package manifests. | `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `Pipfile.lock`, `pubspec.lock`, `Gemfile.lock`, or the equivalent for the project's package manager must be committed to the repository. `.gitignore` must NOT include the lockfile. CI/CD installs dependencies using the lockfile (e.g., `npm ci` not `npm install`, `pip install -r requirements.txt` with pinned versions). | _[to be filled]_ | CRITICAL |
| 230 | Dependencies explicitly declared | No reliance on globally installed packages or system-level tools. | Every dependency the app needs to build and run is listed in the package manifest (`package.json`, `requirements.txt`, `pubspec.yaml`, etc.). The app cannot assume `curl`, `imagemagick`, `ffmpeg`, or any other system tool is available unless it is documented as a system prerequisite in the README with the minimum required version. If a system tool is required, the Dockerfile or setup script installs it explicitly. | _[to be filled]_ | STANDARD |
| 231 | No floating version ranges in production | Production dependencies use exact or tightly bounded versions. | Direct production dependencies use exact versions (`1.2.3`) or caret ranges (`^1.2.3`) — never `*`, `latest`, `>=1.0.0`, or bare version ranges without an upper bound. Dev dependencies may use wider ranges. The lockfile provides the actual pinning; this rule ensures the manifest doesn't allow wild upgrades if the lockfile is regenerated. | _[to be filled]_ | STANDARD |
| 232 | Dependency security audit in CI | Every build checks dependencies for known security vulnerabilities. | CI runs a dependency audit command (`npm audit`, `pip-audit`, `bundler-audit`, `flutter pub audit`, or equivalent) on every push. Vulnerabilities rated HIGH or CRITICAL fail the build. MODERATE and LOW vulnerabilities generate warnings but don't block. The audit command is in the CI config file, not a manual step. | _[to be filled]_ | CRITICAL |
| 233 | Peer dependency conflicts resolved | No unresolved peer dependency warnings in the install output. | Running the package install command produces zero peer dependency conflict warnings. If a conflict exists between two libraries requiring different versions of a shared peer dependency, it must be resolved (by upgrading, replacing one library, or adding an explicit resolution/override) before merging. CI fails if the install step produces peer dependency warnings (for package managers that support this check). | _[to be filled]_ | STANDARD |
| 234 | Dependency age monitoring | Dependencies older than 18 months are flagged for review. | A quarterly (or CI-automated) check identifies production dependencies whose latest installed version was published more than 18 months ago. Each flagged dependency is triaged: (a) update if possible, (b) document why it can't be updated (breaking changes, abandoned package), (c) identify a replacement if the package is abandoned. The goal is awareness, not automatic upgrading. | _[to be filled]_ | POLISH |
| 235 | Minimal dependency principle | Every dependency must justify its inclusion. | No production dependency is added for a function that can be implemented in under 20 lines of code (e.g., `is-odd`, `left-pad`, `is-number`). When adding a new dependency, the developer verifies: (a) it has >1,000 weekly downloads or is maintained by a known org, (b) its license is compatible with the project, (c) it doesn't duplicate functionality already in the project or in an existing dependency. Utility libraries that bundle many unused functions (e.g., full Lodash) are imported selectively (e.g., `lodash/get`). | _[to be filled]_ | POLISH |

---

### 6. Legal/Compliance

Covers the legal pages, consent mechanisms, and data handling obligations required by privacy regulations. Shipping an app that collects user data without these creates direct legal liability.

**Source frameworks:** IEEE 830 (legal requirements), Volere (legal constraints), GDPR, CCPA

| # | Rule | Description | Technical Spec | Boilerplate Match | Severity |
|---|------|-------------|----------------|-------------------|----------|
| 236 | Privacy policy page | Any app collecting user data has a privacy policy page. | If the app collects any user data (account creation, analytics, cookies, form submissions), a `/privacy` or `/privacy-policy` route exists containing: what data is collected, why, how it's stored, who it's shared with, how long it's retained, and how users can request deletion. The page is linked from the signup/registration flow and the app footer. Content must be written in plain language, not legal boilerplate that no one reads. | _[to be filled]_ | CRITICAL |
| 237 | Terms of service page | Any app where users create accounts has terms of service. | A `/terms` or `/terms-of-service` route exists containing: acceptable use policy, account termination conditions, limitation of liability, and governing jurisdiction. Users must explicitly accept terms during account creation (checkbox, not pre-checked). The acceptance timestamp and terms version are stored in the database alongside the user record. | _[to be filled]_ | STANDARD |
| 238 | Cookie consent mechanism | If the app uses non-essential cookies, a consent banner is shown. | Before setting any non-essential cookie (analytics, advertising, third-party tracking), the app displays a consent banner with: (a) a plain-language explanation of what cookies are used for, (b) an "Accept" button, (c) a "Reject" or "Manage preferences" button, (d) a link to the cookie policy. Essential cookies (session, CSRF, auth) do not require consent. Cookie preferences are stored and respected — rejected categories are not loaded. No third-party analytics scripts load until consent is given. | _[to be filled]_ | CRITICAL |
| 239 | Data export capability | Users can export their personal data in a machine-readable format. | A user-accessible function (settings page button or API endpoint) generates a downloadable file (JSON or CSV) containing all personal data the app stores about that user: profile info, content they created, activity history, preferences. The export completes within a reasonable time (under 5 minutes for typical accounts) and is delivered as a download or sent via email. This satisfies GDPR Article 20 (right to data portability). | _[to be filled]_ | STANDARD |
| 240 | Data deletion capability | Users can request deletion of their account and all associated data. | A user-accessible function (settings page or support flow) allows account deletion. Deletion removes or anonymizes: user profile, content they authored (or reassigns to "Deleted User"), activity logs containing PII, and any cached or derived data. Deletion is confirmed within 30 days. The system retains only data required by legal obligation (e.g., financial transaction records for tax purposes) and documents what is retained and why. This satisfies GDPR Article 17 (right to erasure). | _[to be filled]_ | CRITICAL |
| 241 | Consent tracking | The app records what each user consented to and when. | A `user_consents` table (or equivalent) stores: user ID, consent type (terms acceptance, cookie preferences, marketing opt-in), version of the document accepted, timestamp of acceptance, and IP address at time of consent. When terms or privacy policy are updated, users are prompted to re-accept. Historical consent records are never overwritten — new records are appended. | _[to be filled]_ | STANDARD |
| 242 | Third-party data sharing disclosure | Users are informed before their data is shared with third parties. | The privacy policy lists every third-party service that receives user data (analytics, payment processors, CRM, advertising). For each, it states: what data is shared, why, and the third party's privacy policy URL. If a new third-party integration is added that accesses user data, the privacy policy is updated before the integration goes live. | _[to be filled]_ | STANDARD |
| 243 | Open-source license compliance | All dependencies have licenses compatible with the project's license. | Before adding a dependency, its license is checked against the project's allowed license list. Permissive licenses (MIT, Apache 2.0, BSD) are allowed by default. Copyleft licenses (GPL, AGPL) require explicit approval and documentation of compliance obligations. A license audit tool (e.g., `license-checker`, `pip-licenses`, `flutter pub deps`) runs in CI and fails if an unapproved license is detected. A `THIRD_PARTY_LICENSES` file or page is generated listing all dependencies and their licenses. | _[to be filled]_ | CRITICAL |

---

### 7. Deep Accessibility (WCAG AA)

Covers accessibility requirements beyond Martin's basic rules (keyboard navigation, focus management). These rules target WCAG 2.1 Level AA compliance, which is the legal standard in many jurisdictions and the threshold for avoiding accessibility lawsuits.

**Source frameworks:** WCAG 2.1 AA, FURPS+ (usability), Section 508, EN 301 549

| # | Rule | Description | Technical Spec | Boilerplate Match | Severity |
|---|------|-------------|----------------|-------------------|----------|
| 244 | Color contrast ratios | Text meets WCAG AA minimum contrast against its background. | Normal text (under 18pt / 24px or under 14pt / 18.5px bold): minimum 4.5:1 contrast ratio against background. Large text (18pt+ / 24px+ or 14pt+ / 18.5px+ bold): minimum 3:1 contrast ratio. UI components and graphical objects: minimum 3:1 contrast ratio against adjacent colors. Contrast is tested with computed colors, not eyeballed. A contrast checking tool runs against the design tokens or renders. | _[to be filled]_ | CRITICAL |
| 245 | Semantic HTML structure | Content uses correct semantic elements, not styled divs. | Headings use `h1`-`h6` in hierarchical order (no skipping levels). Navigation uses `<nav>`. Main content uses `<main>`. Lists use `<ul>`/`<ol>`/`<li>`. Tables use `<table>` with `<thead>` and `<th scope>`. Buttons use `<button>`, not `<div onClick>`. Links use `<a href>`, not `<span onClick>`. Page has exactly one `<main>` and one `<h1>`. Landmark regions (`<header>`, `<nav>`, `<main>`, `<footer>`) are present on every page. | _[to be filled]_ | STANDARD |
| 246 | Skip navigation link | A skip link allows keyboard users to jump past repeated navigation. | The first focusable element on every page is a "Skip to main content" link that moves focus to the `<main>` element. The link is visually hidden by default and becomes visible on focus (so sighted keyboard users see it). The target element has `tabindex="-1"` to receive focus programmatically. The skip link appears before any navigation menus or repeated header content. | _[to be filled]_ | STANDARD |
| 247 | Reduced motion support | Animations respect the user's motion preference. | All CSS animations and transitions check `prefers-reduced-motion: reduce` and either disable entirely or reduce to a simple opacity fade (max 200ms duration). JavaScript-driven animations (scroll effects, parallax, auto-playing carousels) also check this media query and disable when set. The check must be implemented globally (e.g., in the CSS reset or animation utility), not per-component. No animation plays on page load without checking this preference first. | _[to be filled]_ | STANDARD |
| 248 | Color scheme preference support | The app respects the OS dark/light mode setting when no explicit theme is chosen. | If the user has not explicitly chosen a theme in the app's settings, the app defaults to the OS preference via `prefers-color-scheme` media query. Once the user explicitly sets a theme, that preference overrides the OS setting and is persisted. Theme switching must not cause a flash of the wrong theme on page load (server-side rendering or a blocking script sets the correct class before paint). | _[to be filled]_ | POLISH |
| 249 | ARIA live regions for dynamic content | Screen readers are notified when content updates without a page reload. | Dynamic content changes (toast notifications, form validation errors appearing, live search results updating, chat messages arriving, progress indicators) use `aria-live` regions. Urgent messages (errors, alerts) use `aria-live="assertive"`. Informational updates (search results, status changes) use `aria-live="polite"`. The live region element must exist in the DOM before content is injected — do not dynamically create the live region and populate it simultaneously. | _[to be filled]_ | STANDARD |
| 250 | Touch target minimum size | All interactive elements are large enough to tap without precision. | Every interactive element (buttons, links, form inputs, checkboxes, toggles, icons that trigger actions) has a minimum touch target of 44x44 CSS pixels. If the visible element is smaller (e.g., a 16px icon button), invisible padding extends the tappable area to 44x44. Adjacent targets have at least 8px spacing between their tappable areas. This applies to mobile viewports; desktop may use smaller targets if the element is also hoverable. | _[to be filled]_ | STANDARD |
| 251 | Image alt text policy | Every image has appropriate alt text or is marked decorative. | Non-decorative images have `alt` text describing the image content or function (not the filename). Decorative images have `alt=""` (empty string, not missing). Images that are links or buttons describe the destination/action, not the image appearance. Complex images (charts, infographics) have both brief alt text and a longer text description (via `aria-describedby` or a visible caption). `alt` attributes must never be omitted — this causes screen readers to read the filename. | _[to be filled]_ | STANDARD |
| 252 | Form error association | Error messages are programmatically linked to their form fields. | When a form field has a validation error, the error message element is linked to the input via `aria-describedby` (pointing to the error's ID). The input is also marked `aria-invalid="true"`. Error messages appear adjacent to the field (not only at the top of the form). Focus moves to the first errored field on submission failure. Error messages are announced by screen readers when they appear (via the live region or focus change). | _[to be filled]_ | STANDARD |
| 253 | Focus visible indicator | Focused elements always have a visible outline or ring. | No CSS rule sets `outline: none` or `outline: 0` without providing an alternative visible focus indicator. The focus indicator has a minimum 3:1 contrast ratio against the surrounding background. Custom focus styles (e.g., box shadow, ring) are acceptable but must be at least as visible as the browser default. The `:focus-visible` pseudo-class is used to show focus indicators on keyboard navigation while hiding them on mouse click (not `:focus` alone which shows on click). | _[to be filled]_ | STANDARD |

---

### 8. API Versioning

Covers version management for APIs so clients don't break when the backend evolves. Martin's checklist defines API patterns (service layer, data fetching) but says nothing about how APIs change over time without breaking existing consumers.

**Source frameworks:** arc42 (architecture decisions, interface documentation), IEEE 830 (interface requirements)

| # | Rule | Description | Technical Spec | Boilerplate Match | Severity |
|---|------|-------------|----------------|-------------------|----------|
| 254 | API version identifier | Every API endpoint includes a version identifier. | All API routes include a version prefix in the URL path (e.g., `/api/v1/users`) OR the API accepts a version header (e.g., `Accept: application/vnd.myapp.v1+json`). Choose one approach and use it consistently across all endpoints. The version is a positive integer that increments on breaking changes. Non-breaking additions (new optional fields, new endpoints) do not require a version bump. | _[to be filled]_ | STANDARD |
| 255 | Deprecation notice period | Deprecated API endpoints remain functional for a documented minimum period. | When an API endpoint is deprecated, it: (a) returns a `Deprecation` HTTP header with the date it was deprecated, (b) returns a `Sunset` HTTP header with the date it will be removed, (c) continues functioning for at least 90 days after the deprecation announcement, (d) is documented as deprecated in the API docs with a migration path to the replacement. No endpoint is removed without prior deprecation. | _[to be filled]_ | STANDARD |
| 256 | Backward compatibility for minor changes | New fields added to API responses do not break existing clients. | Adding a new field to a JSON response is a non-breaking change and does not require a version bump. Removing a field, renaming a field, changing a field's type, or changing the meaning of a field are breaking changes that require either a new API version or a deprecation period. Clients must be built to ignore unknown fields (no strict schema validation on responses that would reject new fields). | _[to be filled]_ | STANDARD |
| 257 | Breaking change documentation | Every breaking API change has a documented migration path. | When a new API version is released, a migration guide exists (in the API docs or a `CHANGELOG.md`) that lists: (a) every breaking change, (b) what the old behavior was, (c) what the new behavior is, (d) code examples showing how to update client code. The changelog follows a consistent format (e.g., Keep a Changelog). The migration guide is published before or simultaneously with the new version release. | _[to be filled]_ | POLISH |
| 258 | API response envelope consistency | All API responses follow the same structure. | Every API response uses a consistent envelope structure. Success responses include at minimum: the data payload and a status indicator. Error responses include at minimum: an error code (machine-readable string, not just HTTP status), a human-readable message, and optionally a details array for field-level validation errors. The same envelope shape is used across all endpoints — clients never have to guess whether `data` is at the top level or nested. | _[to be filled]_ | STANDARD |

---

### 9. Architecture Decision Records (ADRs)

Covers documenting significant technical decisions so future developers (and future you) understand WHY the codebase is structured the way it is. Without ADRs, every new developer re-litigates settled decisions.

**Source frameworks:** arc42 (section 9: architecture decisions), Cognitect ADR format

| # | Rule | Description | Technical Spec | Boilerplate Match | Severity |
|---|------|-------------|----------------|-------------------|----------|
| 259 | ADR template exists | The project has a standard template for recording architecture decisions. | An ADR template file exists at `docs/adr/template.md` (or equivalent path) containing four required sections: **Status** (Proposed / Accepted / Deprecated / Superseded), **Context** (the problem or question that prompted the decision), **Decision** (what was decided and why), **Consequences** (what changes as a result — both positive and negative). Each ADR is a separate file. | _[to be filled]_ | STANDARD |
| 260 | ADR trigger threshold | ADRs are written for decisions that meet a defined impact threshold. | An ADR must be created when any of these are true: (a) a new dependency is introduced, (b) the change affects 5+ files across 2+ directories, (c) the change introduces a new architectural pattern not previously used, (d) the team disagrees on the approach (the ADR documents the resolution), (e) the decision is difficult to reverse later. Trivial decisions (variable naming, single-file refactors) do not need ADRs. | _[to be filled]_ | POLISH |
| 261 | ADR numbering and storage | ADRs are numbered sequentially and stored in a consistent location. | ADRs are stored in `docs/adr/` (or `docs/decisions/`), named `NNNN-short-title.md` where NNNN is a zero-padded sequential number (e.g., `0001-use-postgresql.md`, `0002-adopt-rest-over-graphql.md`). Numbers are never reused. A `docs/adr/README.md` or index file lists all ADRs with their status and one-line summary for quick scanning. | _[to be filled]_ | POLISH |
| 262 | Superseded ADRs link forward | When an ADR is replaced, it links to its successor. | When a new decision supersedes an old one, the old ADR's status is changed to `Superseded by [NNNN]` with a link to the new ADR. The new ADR's Context section references the old ADR it replaces and explains what changed. This creates a traceable decision history. Old ADRs are never deleted or modified beyond the status change. | _[to be filled]_ | POLISH |
| 263 | ADRs part of onboarding | New team members read existing ADRs as part of project onboarding. | The project's onboarding documentation (README, contributing guide, or onboarding checklist) includes a step to read all Accepted ADRs. ADRs are written in plain language that a new developer can understand without deep project context — no jargon without definition, no references to conversations that aren't documented. | _[to be filled]_ | POLISH |

---

### 10. Error Recovery / Retry Strategy

Covers how the app handles transient failures (network blips, service outages, rate limits) without crashing, losing data, or silently hanging. Martin's checklist covers error handling (try/catch, error states in UI) but says nothing about retry logic, circuit breakers, or graceful degradation.

**Source frameworks:** 12-Factor App (Factor IX: Disposability), arc42 (quality requirements, cross-cutting concepts)

| # | Rule | Description | Technical Spec | Boilerplate Match | Severity |
|---|------|-------------|----------------|-------------------|----------|
| 264 | Transient failure detection | The app distinguishes transient failures from permanent ones. | Network timeouts, HTTP 502/503/504, connection refused, DNS resolution failures, and HTTP 429 (rate limit) are classified as transient (retryable). HTTP 400, 401, 403, 404, 422 are classified as permanent (do not retry). The classification is implemented in a shared HTTP client utility, not duplicated per API call. Unrecognized errors default to permanent (no retry) unless overridden. | _[to be filled]_ | STANDARD |
| 265 | Exponential backoff with jitter | Retries use exponential backoff with randomized jitter, not fixed intervals. | Retry delay formula: `min(base_delay * 2^attempt + random_jitter, max_delay)` where `base_delay` is 1 second, `random_jitter` is 0 to 1 second (uniform random), and `max_delay` is 30 seconds. This prevents thundering herd problems where all clients retry at the same instant. The retry utility is a shared module — individual callers do not implement their own backoff math. | _[to be filled]_ | STANDARD |
| 266 | Maximum retry count | All retry loops have a hard upper limit. | No operation retries more than 5 times (configurable per operation type). After the maximum retries are exhausted, the operation fails with a clear error that includes: how many retries were attempted, the last error received, and a user-facing message appropriate for the context (e.g., "Unable to save. Please check your connection and try again."). There must be no code path where a retry loop runs indefinitely. | _[to be filled]_ | CRITICAL |
| 267 | Circuit breaker for external services | Repeated failures to an external service trigger a circuit breaker that stops sending requests temporarily. | When a specific external service fails N consecutive times (default: 5), the circuit opens and subsequent calls immediately return a cached response or a graceful error without attempting the network call. After a cooldown period (default: 60 seconds), the circuit enters half-open state and allows one test request. If it succeeds, the circuit closes. If it fails, the circuit reopens. Circuit state (open/closed/half-open) is logged at WARN level on every state change. | _[to be filled]_ | POLISH |
| 268 | Graceful degradation | The app remains usable when non-critical services are unavailable. | Each external service dependency is classified as CRITICAL (app cannot function without it — e.g., primary database, auth provider) or NON-CRITICAL (app functions with reduced capability — e.g., analytics, recommendations, notifications, search suggestions). When a non-critical service is down, the feature it powers shows a fallback state (cached data, "temporarily unavailable" message, or is hidden) rather than crashing the page or showing a generic error. The classification is documented. | _[to be filled]_ | STANDARD |
| 269 | Retry state visible to user | Users can see when the app is retrying a failed operation, not a silent hang. | When an operation is being retried, the UI shows an indicator appropriate to the context: a "Retrying..." label on a submit button, a toast like "Connection lost, retrying...", or a status banner for background operations. The user is never left staring at a spinner with no feedback for more than 5 seconds without being told what's happening. After max retries fail, the user gets an actionable message ("Try again" button or instructions), not just "Something went wrong." | _[to be filled]_ | STANDARD |
| 270 | Idempotency for retried operations | Operations that may be retried are safe to execute multiple times. | Any write operation (create, update, delete, payment, email send) that is retried must produce the same outcome whether it executes once or multiple times. Implementation strategies: (a) client sends an idempotency key (UUID) with the request, server deduplicates by key, (b) server uses database constraints (unique keys, upserts) to prevent duplicate creation, (c) delete operations check existence before failing. Payment and financial operations MUST use idempotency keys — no exceptions. | _[to be filled]_ | CRITICAL |

---

## Summary

| Category | Rules | Range | CRITICAL | STANDARD | POLISH |
|----------|-------|-------|----------|----------|--------|
| 1. Internationalization (i18n) | 8 | 200-207 | 0 | 4 | 4 |
| 2. Config Externalization | 7 | 208-214 | 3 | 4 | 0 |
| 3. Environment Parity | 6 | 215-220 | 3 | 3 | 0 |
| 4. Logging Strategy | 8 | 221-228 | 1 | 6 | 1 |
| 5. Dependency Management | 7 | 229-235 | 2 | 3 | 2 |
| 6. Legal/Compliance | 8 | 236-243 | 4 | 4 | 0 |
| 7. Deep Accessibility (WCAG AA) | 10 | 244-253 | 1 | 8 | 1 |
| 8. API Versioning | 5 | 254-258 | 0 | 4 | 1 |
| 9. Architecture Decision Records | 5 | 259-263 | 0 | 1 | 4 |
| 10. Error Recovery / Retry Strategy | 7 | 264-270 | 2 | 4 | 1 |
| **TOTAL** | **71** | **200-270** | **16 (23%)** | **41 (58%)** | **14 (20%)** |
