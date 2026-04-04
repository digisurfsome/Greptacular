# PRD Maker — All Stages (Pipeline Edition)

This file contains all 11 PRD Maker skill stages with `[STAGE_COMPLETE]` pipeline
integration blocks appended to each one. The original SKILL.md files are NOT modified.

Generated: 2026-04-04T22:33:28Z

---

================================================================================
STAGE 0: TECHNICAL FOUNDATION
================================================================================

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
  "checklist_rule_ids": ["string — rule IDs that apply to this stack"],
  "command_allowlist": ["string — allowed bash commands"],
  "resolved_rules": [{
    "rule_id": "string",
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


---

## 🔗 Pipeline Integration — Automatic Stage Advancement

**This section is added for pipeline automation. It tells you how to signal stage completion.**

After completing ALL steps above and producing your complete output:

### Stage Completion Protocol

1. **Verify your confidence score** meets the gate threshold (≥ 70)
2. **Verify the complete JSON output** has been produced and meets the contract
3. **Output the completion marker** on its own line as the ABSOLUTE LAST thing in your response:

```
[STAGE_COMPLETE]
```

### Rules for the completion marker:

- `[STAGE_COMPLETE]` MUST be the absolute last thing in your response — nothing after it
- Your complete JSON output (context_packet) MUST come BEFORE the marker
- **Never** output `[STAGE_COMPLETE]` until the stage contract is fully met
- **Never** output `[STAGE_COMPLETE]` if the confidence score is below 70
- If you need to ask the user questions, do **NOT** output `[STAGE_COMPLETE]` — wait for answers first, produce your final output, THEN output the marker
- If the gate_result is "fail" (score < 70), trigger the escape hatch protocol instead — do NOT output `[STAGE_COMPLETE]`

### What happens when you output [STAGE_COMPLETE]:

1. The pipeline captures everything before the marker as your stage output
2. Your output becomes the input for the next stage
3. The next stage starts automatically — no manual intervention needed

### Example — end of your response:

```json
{
  "stage_0": { ... your complete output ... },
  "metadata": {
    "confidence_scores": {
      "0": { "score": 93, "gate_result": "pass" }
    }
  }
}
```

[STAGE_COMPLETE]


================================================================================
STAGE 1: IDEA CAPTURE
================================================================================

---
name: stage-1-idea-capture
description: Capture raw app idea brain dump with zero filtering. Outputs raw_input, word count, format, corrections.
---

## Purpose

Capture the user's raw, unstructured app idea exactly as given — preserving contradictions, tangents, filler words, and repetitions — so Stage 2 (Gap Analysis) receives complete, unfiltered raw material to work with.

## When to Use

Activate when: the user provides a raw app idea, brain dump, rant, voice transcript, scattered notes, or stream-of-consciousness description AND `context_packet.stage_0.platform_profile` exists (Stage 0 is complete). Trigger phrases: "describe your app", "here's my idea", "I want to build", "brain dump", "idea capture", "raw idea".

Do NOT activate for: gap analysis questions (Stage 2), structuring/organizing ideas (Stage 3), mechanism extraction (Stage 4), or any request to "clean up" or "organize" raw input.

## Input Format

```json
{
  "stage_0": {
    "platform_profile": {
      "boilerplate_id": "string",
      "boilerplate_name": "string",
      "description": "string"
    },
    "tech_stack": {
      "framework": "string",
      "database": "string",
      "auth_provider": "string",
      "hosting": "string"
    }
  },
  "metadata": {
    "pipeline_version": "string",
    "current_stage": 0,
    "status": "in_progress"
  }
}
```

The primary input is the **user's free-form idea description** — no structure required.

## Process

### Step 1: Present Intake Prompt

Read `context_packet.stage_0.platform_profile` and `stage_0.tech_stack.framework` to lightly tailor the prompt. See `references/intake-prompt-templates.md` for platform-specific variations.

Present a low-friction prompt that:
- Invites the user to describe their app idea however they want
- States explicitly: no wrong answers, no forms, no required format
- Encourages verbosity: "The more detail you give now, the fewer questions later"
- Gives 1-2 gentle contextual cues based on platform (e.g., "pages and flows" for web, "screens and gestures" for mobile)
- Welcomes contradictions, tangents, and repetitions

**Do NOT** present a form, template, questionnaire, or structured input. The user talks however they want.

### Step 2: Capture Everything Verbatim

Accept whatever the user provides and store the complete text as `raw_input`.

**Capture rules — all mandatory:**
- Do NOT summarize, paraphrase, or condense
- Do NOT reorganize into sections or categories
- Do NOT correct grammar, spelling, or formatting
- Do NOT remove filler words ("um", "like", "you know")
- Do NOT resolve contradictions — both versions stay in raw_input
- DO preserve exact words, sentence structure, and flow
- DO preserve formatting artifacts from pasted content

If the user provides input across multiple messages, concatenate all messages in order with a blank line between each, preserving everything.

### Step 3: Detect Input Format

Classify `input_format` using textual signals:

| Format | Signals |
|--------|---------|
| `"voice_transcript"` | Filler words, run-on sentences, self-corrections mid-sentence, informal speech, lack of punctuation |
| `"typed"` | Complete sentences, proper punctuation, paragraph breaks, no filler words |
| `"pasted_notes"` | Bullet points, numbered lists, formatting artifacts (markdown, HTML), mixed formatting |
| `"mixed"` | Combination of above patterns in the same input |

Default to `"typed"` if uncertain.

### Step 4: Detect Explicit Corrections

Scan `raw_input` for correction markers. See `references/correction-detection-patterns.md` for the full pattern list.

Common markers: "actually", "wait", "no", "I mean", "scratch that", "instead", "not X, Y", "oh wait", "I forgot", "let me change that".

For each detected correction, record:
- `original`: What the user first said
- `correction`: What they changed it to
- `context`: (optional) Why they corrected

**Both the original AND correction remain in `raw_input`.** The corrections array is metadata ABOUT the input, not a replacement. Resolution happens in Stage 3.

If no corrections detected, set `explicit_corrections` to `[]`.

### Step 5: Count and Timestamp

- `word_count`: Split `raw_input` on whitespace, count tokens
- `char_count`: Total character length of `raw_input`
- `captured_at`: Current ISO 8601 timestamp (e.g., `"2026-04-03T10:22:40Z"`)

### Step 6: Validate Minimum Viability

If `word_count >= 20`: proceed to Step 7.

If `word_count < 20`: prompt the user for more detail:
> "I have your idea captured, but it's quite brief. The more you tell me now, the fewer questions I'll need to ask next. Could you add more about what the app does, who it's for, or the main features you envision?"

If user adds more: re-capture (append to raw_input), re-count. If user declines: proceed with what you have — expect lower confidence score.

### Step 7: Score Confidence and Write Output

Run the confidence scoring (see Confidence Scoring section below). Then:

- **Score >= 90**: Write output to context packet. Proceed to Stage 2.
- **Score 70-89**: Write output with warning. Add low-scoring dimensions to metadata notes.
- **Score < 70**: Prompt user for more detail once. If still < 70 after retry, trigger escape hatch.

## Output Format

Written to `context_packet.stage_1`:

```json
{
  "raw_input": "string — complete unedited user brain dump",
  "input_format": "typed | voice_transcript | pasted_notes | mixed",
  "captured_at": "ISO 8601 timestamp string",
  "word_count": 168,
  "char_count": 892,
  "explicit_corrections": [
    {
      "original": "string — what user originally said",
      "correction": "string — what they changed it to",
      "context": "string (optional) — why they corrected"
    }
  ]
}
```

Written to `context_packet.metadata`:

```json
{
  "current_stage": 1,
  "updated_at": "ISO 8601 timestamp",
  "confidence_scores": {
    "1": {
      "score": 92,
      "dimensions": {
        "completeness": 18,
        "accuracy": 20,
        "consistency": 18,
        "specificity": 18,
        "handoff_readiness": 18
      },
      "gate_result": "pass | flag | fail"
    }
  },
  "stage_timestamps": {
    "1": "ISO 8601 timestamp"
  }
}
```

**Validation before writing:**
1. All required fields populated: `raw_input`, `input_format`, `captured_at`, `word_count`, `char_count`
2. `raw_input` is non-empty
3. `input_format` is one of: `"typed"`, `"voice_transcript"`, `"pasted_notes"`, `"mixed"`
4. `captured_at` is valid ISO 8601
5. `word_count` matches actual word count within 5% tolerance
6. Confidence score computed and gate_result set

**Output contains ONLY the structured JSON data. No conversational preamble, no "Here is what I captured:", no prose.**

## Edge Cases

### Missing or Insufficient Input

- **Under 20 words**: Prompt for more detail. If user declines after one prompt, proceed but flag `gate_result: "flag"` if score is 70-89, or trigger escape hatch if < 70.
- **Empty input**: Trigger escape hatch immediately.
- **Non-app input** (e.g., "hello", "test", random characters): Trigger escape hatch. The input contains no identifiable app concept.

### Pre-Structured Input

User pastes markdown with headers, numbered lists, or organized sections. **Capture it exactly as-is.** Set `input_format` to `"pasted_notes"`. Do NOT strip formatting. Downstream stages handle structure — Stage 1 preserves everything.

### Scope Overflow

User asks Stage 1 to organize, analyze, or improve their idea. **Decline politely.** Say: "I'll capture everything you've said as-is. The next stage will ask follow-up questions and organize things. For now, just keep describing your idea." Capture whatever they said, including the request to organize.

### Missing Stage 0 Data

If `context_packet.stage_0.platform_profile` is missing or malformed: use the generic intake prompt (no platform-specific cues). Log a warning but do NOT block capture. Stage 0 data is used for tailoring, not gating.

### Extremely Long Input

If `raw_input` exceeds 10,000 words: capture all of it. No truncation. Set `input_format` based on content signals as normal. Note: extremely long input almost guarantees a high confidence score.

## Confidence Scoring

Score each dimension 0-20 after producing output:

**1. Completeness (0-20):**
- 0-5: raw_input empty or under 10 words; required fields missing
- 6-10: 10-19 words; all fields present but minimal
- 11-15: 20-100 words; all fields populated; at least one app concept identifiable
- 16-20: 100+ words with rich detail; multiple concepts, context, and user intent

**2. Accuracy (0-20):**
- 0-5: raw_input was edited, summarized, or rewritten
- 6-10: Mostly faithful but some paraphrasing detected
- 11-15: Preserves user's language faithfully; minor formatting differences OK
- 16-20: Verbatim capture including filler phrases, self-corrections, informal language

**3. Consistency (0-20):**
- 0-5: raw_input contradicts input_format (e.g., format says voice but text is structured markdown)
- 6-10: word_count off by >10%
- 11-15: Metadata matches content; word_count accurate within 5%
- 16-20: All metadata precisely matches; zero discrepancies

**4. Specificity (0-20):**
- 0-5: So vague no app concept identifiable ("I want to make something cool")
- 6-10: App concept present but no features, users, or context
- 11-15: App concept + 2-3 feature ideas or user descriptions
- 16-20: App concept + multiple features + target users + contextual details

**5. Handoff Readiness (0-20):**
- 0-5: Stage 2 cannot determine app type
- 6-10: Stage 2 can identify rough app type but needs fundamental questions
- 11-15: Stage 2 can identify app type and start gap analysis; gaps are in specifics, not core
- 16-20: Stage 2 can identify app type, match archetype, generate targeted gap questions

**Total = sum of all 5 (/100)**

| Score | Gate Result | Action |
|-------|-------------|--------|
| >= 90 | `"pass"` | Proceed to Stage 2 automatically |
| 70-89 | `"flag"` | Proceed with warning; note low dimensions |
| < 70 | `"fail"` | Trigger escape hatch |

## Escape Hatch

**Trigger when:**
- User provides fewer than 20 words and declines to add more
- raw_input contains no identifiable app concept
- Confidence score < 70 after one retry
- Stage 0 platform_profile is missing AND user provides no usable input

**Save:**
- Current context_packet with partial `stage_1` output
- Stage number (1) and step where halt occurred
- What was attempted and what failed

**Signal:**
```json
{
  "status": "needs_human",
  "stage": 1,
  "problem": "specific problem description",
  "suggested_questions": [
    "Could you describe what your app does in a few more sentences?",
    "Who is this app for? What problem does it solve?",
    "What are the main features you envision?"
  ]
}
```

Set `metadata.status = "needs_human"` and append to `metadata.escape_hatches[]`:
```json
{
  "stage": 1,
  "timestamp": "ISO 8601",
  "status": "NEEDS_HUMAN",
  "progress_summary": "what was captured so far",
  "problem": "specific reason",
  "attempted": ["list of what was tried"],
  "partial_output": {},
  "suggested_actions": ["action 1", "action 2"],
  "resume_from": "step_name",
  "confidence_at_failure": 45,
  "scope_creep_detected": false
}
```

## Example

**User input:**

> I want to build a task manager app. Like Todoist but simpler. Users can create projects and add tasks to them. Tasks have due dates, priorities (high/medium/low), and you can assign them to other people on your team. I want a kanban board view where you drag tasks between columns like To Do, In Progress, and Done. Also a regular list view sorted by due date. Users need to sign up with email or Google. Oh wait, not just Google — also GitHub login since this is for developer teams. There should be notifications when someone assigns you a task or when a due date is coming up. Maybe email and in-app notifications. I want it to look clean and modern, not cluttered. Dark mode would be nice. Teams should be able to create workspaces and invite members. Oh and I forgot — there should be a simple dashboard showing how many tasks are done vs pending, maybe a chart.

**Output written to context_packet.stage_1:**

```json
{
  "raw_input": "I want to build a task manager app. Like Todoist but simpler. Users can create projects and add tasks to them. Tasks have due dates, priorities (high/medium/low), and you can assign them to other people on your team. I want a kanban board view where you drag tasks between columns like To Do, In Progress, and Done. Also a regular list view sorted by due date. Users need to sign up with email or Google. Oh wait, not just Google — also GitHub login since this is for developer teams. There should be notifications when someone assigns you a task or when a due date is coming up. Maybe email and in-app notifications. I want it to look clean and modern, not cluttered. Dark mode would be nice. Teams should be able to create workspaces and invite members. Oh and I forgot — there should be a simple dashboard showing how many tasks are done vs pending, maybe a chart.",
  "input_format": "typed",
  "captured_at": "2026-04-03T10:22:40Z",
  "word_count": 168,
  "char_count": 892,
  "explicit_corrections": [
    {
      "original": "Google login only",
      "correction": "Google AND GitHub login",
      "context": "User initially said Google, then added GitHub for developer teams"
    }
  ]
}
```

**Confidence: 92/100** (completeness: 18, accuracy: 20, consistency: 18, specificity: 18, handoff_readiness: 18) — `gate_result: "pass"`. Proceeds to Stage 2.


---

## REFERENCE: correction-detection-patterns

# Correction Detection Patterns

Linguistic markers for detecting explicit self-corrections in user input. Used by Stage 1, Step 4.

---

## High-Confidence Markers

These almost always indicate the user is correcting a previous statement:

| Marker | Example |
|--------|---------|
| `"actually"` | "I want Google login. Actually, also GitHub login." |
| `"wait"` / `"oh wait"` | "Oh wait, not just email — also SMS." |
| `"no,"` / `"no —"` | "No, not a chat app. More like a task board." |
| `"I mean"` | "I want it in Python. I mean TypeScript." |
| `"scratch that"` | "Add a calendar view. Scratch that, just a list view." |
| `"instead"` | "Instead of Google login, use magic links." |
| `"not X, Y"` / `"not just X"` | "Not just admin users — all users can create projects." |
| `"let me change that"` | "Let me change that — make it a SPA, not multi-page." |
| `"correction:"` / `"edit:"` | Explicit meta-correction labels in pasted notes. |

---

## Medium-Confidence Markers

These may indicate corrections but could also be additive statements. Look for surrounding context:

| Marker | Example | Additive or Corrective? |
|--------|---------|-------------------------|
| `"also"` | "Also add GitHub login" | Additive if new info; corrective if contradicts prior |
| `"I forgot"` / `"oh and"` | "Oh and I forgot — there should be a dashboard" | Usually additive, but record if it contradicts something |
| `"but"` | "I want it simple but also feature-rich" | Tension/contradiction — record both sides |
| `"well,"` | "Well, maybe not three tiers. Just two." | Often a softened correction |
| `"on second thought"` | "On second thought, skip the mobile version" | Almost always a correction |

---

## Contradiction Without Markers

Sometimes the user says X, then later says Y without explicit correction language:

- "I want it to be free" ... (later) ... "Users pay $10/month"
- "No login required" ... (later) ... "Users sign in with Google"

**Rule:** Only record in `explicit_corrections` if the user uses a correction marker. Implicit contradictions (no marker) are preserved in `raw_input` but NOT tagged in `explicit_corrections`. Implicit contradiction resolution is Stage 3's job.

---

## Recording Format

For each detected correction:

```json
{
  "original": "exact phrase or paraphrase of what they first said",
  "correction": "exact phrase or paraphrase of the correction",
  "context": "optional — why they corrected (if they said)"
}
```

**Rules:**
- Keep `original` and `correction` concise — extract the relevant clause, not the full paragraph
- `context` is optional — only include if the user explained why they changed their mind
- Both the original statement AND the correction remain verbatim in `raw_input`
- When in doubt about whether something is a correction, do NOT record it — err on the side of fewer entries


---

## REFERENCE: example-captures

# Example Captures

Realistic Stage 1 captures at different detail levels. Each shows raw user input and the resulting `stage_1` output.

---

## Example 1: Minimal Input (2-3 sentences)

**User says:**
> I want a recipe app where people can save recipes and search by ingredient.

**stage_1 output:**

```json
{
  "raw_input": "I want a recipe app where people can save recipes and search by ingredient.",
  "input_format": "typed",
  "captured_at": "2026-04-03T11:00:00Z",
  "word_count": 14,
  "char_count": 71,
  "explicit_corrections": []
}
```

**Confidence: 52/100** — Fails minimum viability (14 words < 20). Prompt user for more detail. If user declines, trigger escape hatch.

**After prompting, user adds:**
> It should have categories like breakfast, lunch, dinner. Users can rate recipes and leave comments. Maybe a meal planner for the week.

**Updated stage_1:**

```json
{
  "raw_input": "I want a recipe app where people can save recipes and search by ingredient.\n\nIt should have categories like breakfast, lunch, dinner. Users can rate recipes and leave comments. Maybe a meal planner for the week.",
  "input_format": "typed",
  "captured_at": "2026-04-03T11:01:30Z",
  "word_count": 41,
  "char_count": 213,
  "explicit_corrections": []
}
```

**Confidence: 74/100** — Flag (low specificity and completeness). Proceeds with warning.

---

## Example 2: Average Input (5-8 sentences)

**User says:**
> I'm thinking of a fitness tracking app for personal trainers. They can create workout plans for their clients, track progress over time, and see charts of improvement. Clients get a separate view where they log their workouts and see what's assigned. I want Google login for both trainers and clients. It should work on mobile since people use it at the gym. Something like Trainerize but less expensive and more customizable.

**stage_1 output:**

```json
{
  "raw_input": "I'm thinking of a fitness tracking app for personal trainers. They can create workout plans for their clients, track progress over time, and see charts of improvement. Clients get a separate view where they log their workouts and see what's assigned. I want Google login for both trainers and clients. It should work on mobile since people use it at the gym. Something like Trainerize but less expensive and more customizable.",
  "input_format": "typed",
  "captured_at": "2026-04-03T11:05:00Z",
  "word_count": 82,
  "char_count": 460,
  "explicit_corrections": []
}
```

**Confidence: 88/100** — Flag (handoff_readiness slightly low — trainer/client permissions not fully described). Proceeds with warning.

---

## Example 3: Verbose Input (40+ sentences)

**User says:**
> OK so I've been thinking about this for a while. I want to build a freelancer management platform. Think of it like a mix between Upwork and Notion. Freelancers sign up, create a profile with their skills, hourly rate, portfolio links. Companies post gigs — not full job listings, more like project briefs. So a company says "I need a landing page designed" and freelancers can bid on it. But here's the thing — I don't want it to be a race to the bottom on pricing like Fiverr. I want quality matching. So maybe there's a rating system based on completed work, and the platform suggests matches based on skills and past work quality. Companies can also create teams of freelancers they work with regularly, like a favorites list. Payments should be handled through the platform — escrow style. Company pays upfront, money is held, released when work is approved. Disputes go to mediation. I want Stripe for payments. Users sign up with email. Actually wait, also Google and LinkedIn since it's a professional platform. The dashboard for companies shows active projects, pending invoices, team performance. Freelancers see their pipeline, earnings chart, upcoming deadlines. There should be a messaging system between freelancers and companies, with file sharing. Not real-time chat necessarily — more like threaded conversations per project. Notifications for new messages, project updates, payment received. I want it to feel professional, not startup-y. Clean design, maybe a blue and white color scheme. Oh and I forgot — there should be a public profile page for freelancers that they can share as a portfolio link. And companies should have a public page too showing their posted gigs. SEO matters for these pages.

**stage_1 output:**

```json
{
  "raw_input": "OK so I've been thinking about this for a while. I want to build a freelancer management platform. Think of it like a mix between Upwork and Notion. Freelancers sign up, create a profile with their skills, hourly rate, portfolio links. Companies post gigs — not full job listings, more like project briefs. So a company says \"I need a landing page designed\" and freelancers can bid on it. But here's the thing — I don't want it to be a race to the bottom on pricing like Fiverr. I want quality matching. So maybe there's a rating system based on completed work, and the platform suggests matches based on skills and past work quality. Companies can also create teams of freelancers they work with regularly, like a favorites list. Payments should be handled through the platform — escrow style. Company pays upfront, money is held, released when work is approved. Disputes go to mediation. I want Stripe for payments. Users sign up with email. Actually wait, also Google and LinkedIn since it's a professional platform. The dashboard for companies shows active projects, pending invoices, team performance. Freelancers see their pipeline, earnings chart, upcoming deadlines. There should be a messaging system between freelancers and companies, with file sharing. Not real-time chat necessarily — more like threaded conversations per project. Notifications for new messages, project updates, payment received. I want it to feel professional, not startup-y. Clean design, maybe a blue and white color scheme. Oh and I forgot — there should be a public profile page for freelancers that they can share as a portfolio link. And companies should have a public page too showing their posted gigs. SEO matters for these pages.",
  "input_format": "typed",
  "captured_at": "2026-04-03T11:10:00Z",
  "word_count": 271,
  "char_count": 1534,
  "explicit_corrections": [
    {
      "original": "email login only",
      "correction": "email AND Google AND LinkedIn login",
      "context": "User initially said email, then added Google and LinkedIn since it's a professional platform"
    }
  ]
}
```

**Confidence: 96/100** — Pass. Rich detail, multiple features, target users, comparisons, technical preferences, and contextual detail.

---

## Example 4: Voice Transcript (with filler words and self-corrections)

**User says (transcribed from voice):**
> um ok so like I want to make this app right where uh people can like track their habits you know like drinking water exercising reading whatever um and it shows you like streaks so if you do it every day your streak goes up and if you miss a day it resets well actually maybe not resets completely like maybe it just you know shows a gap and you can still see your overall progress um I think it should be really simple like not a lot of buttons just open it check off what you did today see your streaks maybe some stats like how many times you exercised this month um I don't know about login maybe just use the phone no wait it should sync between devices so yeah login with Apple or Google I guess um and like maybe there's a social thing where you can share your streaks with friends but that's not the main thing the main thing is just tracking your own habits simply

**stage_1 output:**

```json
{
  "raw_input": "um ok so like I want to make this app right where uh people can like track their habits you know like drinking water exercising reading whatever um and it shows you like streaks so if you do it every day your streak goes up and if you miss a day it resets well actually maybe not resets completely like maybe it just you know shows a gap and you can still see your overall progress um I think it should be really simple like not a lot of buttons just open it check off what you did today see your streaks maybe some stats like how many times you exercised this month um I don't know about login maybe just use the phone no wait it should sync between devices so yeah login with Apple or Google I guess um and like maybe there's a social thing where you can share your streaks with friends but that's not the main thing the main thing is just tracking your own habits simply",
  "input_format": "voice_transcript",
  "captured_at": "2026-04-03T11:15:00Z",
  "word_count": 170,
  "char_count": 837,
  "explicit_corrections": [
    {
      "original": "streak resets when you miss a day",
      "correction": "streak shows a gap but overall progress still visible",
      "context": "User reconsidered full reset as too punishing"
    },
    {
      "original": "no login, just use the phone",
      "correction": "login with Apple or Google for device sync",
      "context": "User realized syncing between devices requires login"
    }
  ]
}
```

**Confidence: 90/100** — Pass. Filler words preserved, corrections detected, app concept clear despite informal language.


---

## REFERENCE: intake-prompt-templates

# Intake Prompt Templates

Platform-tailored intake prompts for Stage 1: Idea Capture. Each template is a gentle, low-friction invitation — NOT a questionnaire.

---

## Web App (framework: Next.js, React, Vue, Svelte, etc.)

> Tell me about the app you want to build. Describe it however makes sense to you — a few sentences, a full brain dump, bullet points, whatever works.
>
> Think about things like: What pages or screens would it have? What happens when someone visits? What can users do? Who is it for?
>
> There are no wrong answers. Contradictions are fine — just keep talking. The more detail you give me now, the fewer questions I'll need to ask later.

---

## Mobile App (framework: Flutter, React Native, SwiftUI, Kotlin)

> Tell me about the app you want to build. Describe it however makes sense to you — a few sentences, a full rant, scattered notes, whatever.
>
> Think about things like: What screens would someone swipe through? What happens when they tap something? Are there gestures like drag, swipe, or pull-to-refresh? Who would download this?
>
> No wrong answers. Contradictions are welcome — both versions get captured. The more you describe, the less I need to ask later.

---

## Dual Platform (web + mobile)

> Tell me about the app you want to build. Describe it however makes sense to you — there's no template or form to fill out.
>
> Since this is for both web and mobile: think about what happens on a big screen vs. a phone. Are the features the same on both, or does one get a simpler version? What do people do on desktop vs. on the go?
>
> Just talk. Tangents, repetitions, contradictions — all welcome. More detail now means fewer questions later.

---

## No Boilerplate / Raw Checklist / Unknown Platform

> Tell me about the app you want to build. Just describe it in your own words — a few sentences, a long rant, bullet points, voice notes, whatever comes naturally.
>
> What does it do? Who is it for? What are the main things a user can do with it? Are there any apps out there that are similar to what you're imagining?
>
> There's no form to fill out. No wrong answers. Contradictions are fine — just keep going. The more you tell me, the less I'll need to ask later.

---

## Usage Notes

- Read `context_packet.stage_0.tech_stack.framework` to select the appropriate template
- If framework is unrecognized, use the "No Boilerplate" template
- These are starting prompts only — if the user starts talking, do NOT interrupt with more prompting
- Never convert these into a numbered questionnaire or form
- The contextual cues (pages/screens/gestures) are suggestions, not requirements


---

## 🔗 Pipeline Integration — Automatic Stage Advancement

**This section is added for pipeline automation. It tells you how to signal stage completion.**

After completing ALL steps above and producing your complete output:

### Stage Completion Protocol

1. **Verify your confidence score** meets the gate threshold (≥ 70)
2. **Verify the complete JSON output** has been produced and meets the contract
3. **Output the completion marker** on its own line as the ABSOLUTE LAST thing in your response:

```
[STAGE_COMPLETE]
```

### Rules for the completion marker:

- `[STAGE_COMPLETE]` MUST be the absolute last thing in your response — nothing after it
- Your complete JSON output (context_packet) MUST come BEFORE the marker
- **Never** output `[STAGE_COMPLETE]` until the stage contract is fully met
- **Never** output `[STAGE_COMPLETE]` if the confidence score is below 70
- If you need to ask the user questions, do **NOT** output `[STAGE_COMPLETE]` — wait for answers first, produce your final output, THEN output the marker
- If the gate_result is "fail" (score < 70), trigger the escape hatch protocol instead — do NOT output `[STAGE_COMPLETE]`

### What happens when you output [STAGE_COMPLETE]:

1. The pipeline captures everything before the marker as your stage output
2. Your output becomes the input for the next stage
3. The next stage starts automatically — no manual intervention needed

### Example — end of your response:

```json
{
  "stage_1": { ... your complete output ... },
  "metadata": {
    "confidence_scores": {
      "1": { "score": 93, "gate_result": "pass" }
    }
  }
}
```

[STAGE_COMPLETE]


================================================================================
STAGE 2: GAP ANALYSIS
================================================================================

---
name: stage-2-gap-analysis
description: Match idea to app archetypes, scan A-N mechanism gaps, ask targeted questions, produce combined_raw + scope contract.
---

## Purpose

Take the raw idea from Stage 1, match it to known app archetypes, scan for missing mechanism categories (A-N), ask the minimum targeted questions needed to fill gaps, and produce a complete information set (`combined_raw`) plus a `scope_contract` for downstream stages. Stage 2 is the first ambiguity-reduction pass — if gaps pass through here, every downstream stage inherits them.

## When to Use

Activate when: `context_packet.stage_1.raw_input` exists AND `context_packet.stage_0.platform_profile` exists (Stages 0 and 1 are complete). Trigger phrases: "gap analysis", "archetype matching", "identify missing mechanisms", "fill gaps", "what's missing from the idea".

Do NOT activate for: raw idea capture (Stage 1), structuring/organizing ideas (Stage 3), breaking into mechanisms (Stage 4), or any request to "build" or "scaffold" features.

## Input Format

```json
{
  "stage_0": {
    "platform_profile": { "boilerplate_id": "string", "boilerplate_name": "string", "description": "string" },
    "tech_stack": { "framework": "string", "database": "string", "auth_provider": "string", "hosting": "string", "additional": {} },
    "checklist_rule_ids": ["string"]
  },
  "stage_1": {
    "raw_input": "string",
    "input_format": "typed | voice_transcript | pasted_notes | mixed",
    "captured_at": "ISO 8601",
    "word_count": 168,
    "char_count": 892,
    "explicit_corrections": [{ "original": "string", "correction": "string" }]
  },
  "metadata": { "app_type": "greenfield | existing", "current_stage": 1 }
}
```

## Process

### Step 1: Assess Detail Level

Read `stage_1.raw_input` and `stage_1.word_count`. Determine expected question depth:

| Word Count | Detail Level | Target Questions |
|------------|-------------|-----------------|
| < 50 | Minimal | 8-15 (minimum 5) |
| 50-150 | Moderate | 5-10 (minimum 2) |
| 150-300 | Detailed | 3-7 (minimum 2) |
| 300+ | Comprehensive | 2-5 (minimum 2) |

If `explicit_corrections` is present, apply corrections: the corrected version takes precedence. If unresolved contradictions exist (user said two conflicting things without correcting), note them for clarifying questions.

### Step 2: Match to App Archetypes

Compare `raw_input` against the 8 archetypes (see `references/archetype-mechanism-maps.md`). Match based on primary user action:

- Views data/metrics -> **Dashboard**
- Buys/sells between parties -> **Marketplace**
- Sends/receives messages -> **Chat**
- Creates/edits/deletes records -> **CRUD/Tool**
- Posts content, follows users -> **Social**
- Walks through step-by-step -> **Wizard**
- Marketing/info page -> **Landing**
- Pays subscription for software -> **SaaS**

**Rules:**
- An app can match MULTIPLE archetypes. Union all REQUIRED categories.
- If subscription billing or team management is mentioned alongside another archetype, ALSO match **SaaS** and union maps.
- Record each match with `confidence` (0-100) and `rationale` citing evidence from `raw_input`.
- If NO archetype matches, set `archetype_matches` to `[{"archetype": "none", "confidence": 100, "rationale": "App does not fit standard archetypes; full A-N scan required"}]`.

### Step 3: Scan A-N Mechanism Categories

Read `raw_input` against all 14 categories from `references/mechanism-categories.md`:

A=Data Input, B=Data Storage, C=Data Processing, D=Data Output, E=Authentication, F=Authorization, G=Communication, H=Integration, I=Workflow, J=Search & Discovery, K=Collaboration, L=Monetization, M=Admin/Ops, N=Infrastructure.

For each category:
1. Search `raw_input` for direct or implied mentions.
2. **Found**: Record in `mechanisms_identified` with sub-types and evidence quote.
3. **Not found**: Record in `mechanisms_gaps` and classify using archetype defaults:

| Archetype Says | User Mentioned? | Action |
|---------------|----------------|--------|
| REQUIRED | No | Gap. Ask about it. `resolution: "asked"` |
| REQUIRED | Yes | Identified. Ask only about uncovered sub-types. |
| OPTIONAL | No | Ask ONE targeted question. |
| OPTIONAL | Yes | Identified. Skip question. |
| UNLIKELY | No | Skip. `resolution: "not_needed"` |
| UNLIKELY | Yes | Override to REQUIRED. Ask sub-questions. |

If no archetype matched, treat ALL 14 categories as potential gaps and ask about each.

### Step 4: Check Structural Checklist

Scan the 30-category structural checklist (Martin's 22 + Industry Standards 10) for coverage gaps that affect mechanism identification:

- Auth mentioned but no auth method specified? Flag.
- Data storage implied but no strategy stated? Flag.
- Monetization mentioned but no pricing model? Flag.

Record in `checklist_coverage`: `.covered` (addressed), `.not_applicable` (explicitly N/A), `.deferred` (Developer's Choice).

### Step 5: Generate Adaptive Questions

Generate questions targeting ONLY identified gaps. Follow `references/question-templates.md` patterns:

1. **REQUIRED gaps**: Ask specific questions with archetype context and 2-3 options.
2. **OPTIONAL categories**: Ask ONE question per category.
3. **UNLIKELY categories**: Do NOT ask unless user mentioned them.
4. **Sub-type gaps in identified categories**: Ask about missing specifics.
5. **Stack-aware**: Use `stage_0.tech_stack` to tailor questions (e.g., Supabase -> ask about Row Level Security).

**Question rules:**
- Be specific, never generic ("tell me more").
- Offer 2-3 concrete options per question.
- Reference what the user ALREADY said.
- Group related questions by category.
- Minimize count while maximizing information gained.

Each question gets a unique ID (`gq_001`, `gq_002`, ...), the A-N category it addresses, and source (`"mechanism_framework"`, `"master_checklist"`, `"archetype_specific"`).

### Step 6: Present Questions and Collect Answers

Present all questions in a single batch, grouped by category. For each answer:
- Record in `gap_answers` with matching `question_id`.
- If user says "I don't know" / "you decide" / "whatever works": set `answer_text: "developers_choice"`, `is_default: true`, and use the archetype's default sub-type.
- If user gives a partial answer: record what they said, mark remaining sub-gaps as Developer's Choice.

### Step 7: Merge into Combined Raw

Concatenate into `combined_raw`:

```
--- ORIGINAL IDEA (from Stage 1) ---
{stage_1.raw_input}

--- GAP ANALYSIS ANSWERS ---
Q: {question_text}
A: {answer_text}

[...repeat for all answered questions...]
```

**Do NOT organize, restructure, or rewrite.** `combined_raw` is raw material for Stage 3.

### Step 8: Calculate Completeness Score

Score 0-100: `(REQUIRED categories with substantive coverage / total REQUIRED) * 70 + (OPTIONAL categories resolved / total OPTIONAL) * 30`.

| Range | Meaning |
|-------|---------|
| 0-30 | Critical gaps — multiple REQUIRED categories missing |
| 31-60 | Major gaps — 2-3 REQUIRED categories thin |
| 61-80 | Moderate — all REQUIRED mentioned, some lack specifics |
| 81-90 | Good — all REQUIRED + most OPTIONAL covered with specifics |
| 91-100 | Excellent — comprehensive coverage |

### Step 9: Write Scope Contract

Produce `scope_contract` string:

```
IN SCOPE:
- [Features, mechanisms, capabilities being built]

NOT IN SCOPE:
- [Explicitly excluded features]
- [Categories marked not_needed]

DEFERRED:
- [Items marked Developer's Choice — system decides approach]
```

## Output Format

Written to `context_packet.stage_2`:

```json
{
  "archetype_matches": [
    { "archetype": "string", "confidence": 85, "rationale": "string" }
  ],
  "mechanisms_identified": [
    { "category_id": "A", "category_name": "Data Input", "sub_types": ["Forms"], "evidence": "quote from raw_input" }
  ],
  "mechanisms_gaps": [
    { "category_id": "L", "category_name": "Monetization", "resolution": "not_needed | asked | developers_choice" }
  ],
  "gap_questions": [
    { "id": "gq_001", "category_id": "H", "question_text": "string", "source": "mechanism_framework | master_checklist | archetype_specific" }
  ],
  "gap_answers": [
    { "question_id": "gq_001", "answer_text": "string", "is_default": false }
  ],
  "combined_raw": "string — Stage 1 raw_input + all gap answers merged",
  "completeness_score": 85,
  "checklist_coverage": {
    "covered": ["category names"],
    "not_applicable": ["category names"],
    "deferred": ["category names"]
  },
  "scope_contract": "IN SCOPE:\n- ...\nNOT IN SCOPE:\n- ...\nDEFERRED:\n- ..."
}
```

Written to `context_packet.metadata`:

```json
{
  "current_stage": 2,
  "archetype_matches": ["marketplace", "saas"],
  "scope_contract_hash": "sha256 hex string",
  "confidence_scores": {
    "2": {
      "score": 88,
      "dimensions": { "completeness": 18, "accuracy": 17, "consistency": 18, "specificity": 17, "handoff_readiness": 18 },
      "gate_result": "pass | flag | fail"
    }
  },
  "stage_timestamps": { "2": "ISO 8601 timestamp" }
}
```

**Validation before writing:**
1. All required fields populated (no null/empty where content expected)
2. Every `gap_answers[].question_id` matches an entry in `gap_questions[].id`
3. Every REQUIRED category (per archetype) has coverage in `combined_raw`
4. `archetype_matches` has at least one entry with confidence >= 70 (or "none" fallback)
5. All 14 A-N categories classified across `mechanisms_identified` + `mechanisms_gaps`
6. If `word_count < 50`: at least 5 questions asked. If `>= 50`: at least 2.
7. Confidence score computed; gate_result set per thresholds.

## Edge Cases

### Missing Input
- **`raw_input` missing or empty**: Trigger escape hatch immediately.
- **`word_count < 20`**: Trigger escape hatch — minimum viable input not met.

### No Archetype Match
- Set `archetype_matches` to `[{"archetype": "none", "confidence": 100, "rationale": "..."}]`.
- Fall back to full A-N scan — ask about all 14 categories.

### Multiple Archetype Match
- Union all REQUIRED categories from matched archetypes.
- For conflicting default sub-types, ask user which fits better.
- Record all matches in `archetype_matches` array.

### User Declines All Questions
- Set all `gap_answers[].answer_text` to `"developers_choice"`, `is_default: true`.
- Use archetype defaults for all REQUIRED categories.
- If `raw_input` alone has enough detail for Stage 3 (completeness >= 70), proceed with warning.
- If completeness < 70, trigger escape hatch.

### Contradictory Input
- If `explicit_corrections` exists, use corrected version.
- If unresolved contradictions remain in `raw_input`, generate a clarifying question targeting each contradiction.

### Scope Overflow
- If the user asks to structure, organize, or build features: decline. Say: "I'm identifying what's missing from your idea. Structuring happens in the next stage."
- Capture any new information they provide but do not change scope.

## Confidence Scoring

Score each dimension 0-20 after producing output:

**1. Completeness (0-20):** All 14 A-N categories classified? `archetype_matches` populated? All questions answered or declined? `combined_raw` present? `checklist_coverage` populated? `scope_contract` present?
- 0-5: >4 categories unclassified; archetype missing
- 6-10: 2-4 unclassified; archetype low confidence (<50)
- 11-15: All classified; 1-2 REQUIRED categories thin
- 16-20: All classified; every REQUIRED category has substantive coverage

**2. Accuracy (0-20):** Archetype match fits the description? Categories correctly identified with valid evidence? Nothing falsely marked "not_needed"?
- 0-5: Archetype clearly wrong
- 6-10: Archetype plausible but not best fit; 2-3 misclassified categories
- 11-15: Archetype matches well; at most 1 borderline classification
- 16-20: Archetype is obvious best match; all classifications defensible

**3. Consistency (0-20):** `gap_answers` align with `raw_input`? Scope contract matches mechanisms? Archetype aligns with identified mechanisms?
- 0-5: Contradictions between answers and raw_input not flagged
- 6-10: Some contradictions partially noted
- 11-15: Minor inconsistencies documented
- 16-20: Internally consistent; all contradictions resolved or flagged

**4. Specificity (0-20):** Questions precise with options and user references? Evidence quotes actual phrases? Answers contain concrete details?
- 0-5: Generic "tell me more" questions
- 6-10: Targeted but broad ("What about authentication?")
- 11-15: Specific gaps with options ("Will auth use email/password, OAuth, or magic links?")
- 16-20: Precise, references user's words, 2-3 options, minimized count

**5. Handoff Readiness (0-20):** Could Stage 3 start immediately from `combined_raw`? Comprehensive enough for all 4 concept document sections?
- 0-5: Stage 3 would need "what is this app?"
- 6-10: Concept identifiable but 3+ sections would struggle
- 11-15: Structured doc possible but 1-2 sections thin
- 16-20: Full concept document producible without additional info

**Total = sum of all 5 (/100)**

| Score | Gate | Action |
|-------|------|--------|
| >= 90 | `"pass"` | Proceed to Stage 3 |
| 70-89 | `"flag"` | Proceed with warning; flag low dimensions |
| < 70 | `"fail"` | Trigger escape hatch |

## Escape Hatch

**Trigger when:**
- `stage_1.raw_input` missing or empty
- `stage_1.word_count < 20`
- No archetype matchable AND description < 10 words about the app concept
- Confidence < 70 after one retry
- User refuses ALL questions AND raw_input alone insufficient for Stage 3

**Save:**
- Current `context_packet` with partial output (archetype matches, partial mechanism scan, questions generated)
- Stage number (2), step where halt occurred, what failed

**Signal:**
- Set `metadata.status = "needs_human"`
- Append to `metadata.escape_hatches[]`:

```json
{
  "stage": 2,
  "step": "step that failed",
  "reason": "specific reason",
  "suggested_actions": ["action 1", "action 2"],
  "partial_output": {}
}
```

- Save context_packet snapshot. Output structured NEEDS_HUMAN message.

## Example

**Input** (`stage_1.raw_input`, 168 words, typed):

> I want to build a task manager app. Like Todoist but simpler. Users can create projects and add tasks to them. Tasks have due dates, priorities (high/medium/low), and you can assign them to other people on your team. I want a kanban board view where you drag tasks between columns like To Do, In Progress, and Done. Also a regular list view sorted by due date. Users need to sign up with email or Google. Oh wait, not just Google — also GitHub login since this is for developer teams. There should be notifications when someone assigns you a task or when a due date is coming up. Maybe email and in-app notifications. I want it to look clean and modern, not cluttered. Dark mode would be nice. Teams should be able to create workspaces and invite members. Oh and I forgot — there should be a simple dashboard showing how many tasks are done vs pending, maybe a chart.

**Step 2 result:** Archetypes matched: CRUD/Tool (confidence: 90, "create projects and add tasks, kanban board, list view") + SaaS (confidence: 75, "teams, workspaces, invite members"). Union REQUIRED: A, B, C, D, E, F, G, L, M.

**Step 3 result:** Mechanisms identified from raw_input: A (Forms, Drag-and-Drop — "create projects and add tasks", "drag tasks between columns"), B (Relational DB — "projects, tasks, due dates, priorities"), C (Validation — "priorities high/medium/low"), D (Lists/Tables, Charts, Kanban — "list view sorted by due date", "kanban board", "chart"), E (Email/Password, OAuth — "sign up with email or Google, GitHub"), F (RBAC — "assign to team"), G (In-App Notifications, Email — "notifications when someone assigns you a task"), K (Profiles — "teams, workspaces, invite members"). Gaps: H (Integration — OPTIONAL, not mentioned), I (Workflow — OPTIONAL for CRUD, "kanban columns" partially covers), J (Search — OPTIONAL, not mentioned), L (Monetization — REQUIRED by SaaS, not mentioned), M (Admin — REQUIRED by SaaS, not mentioned), N (Infrastructure — UNLIKELY, skip).

**Step 5 result — 5 questions generated:**

1. `gq_001` (L): "You mentioned teams and workspaces. Will this be a paid product with subscription tiers (free/pro/team), or free for everyone?"
2. `gq_002` (M): "Will there be an admin role who can manage workspace settings, billing, and member permissions beyond just inviting people?"
3. `gq_003` (H): "Does the app need to integrate with external tools like Slack, GitHub issues, or a calendar app?"
4. `gq_004` (J): "As tasks grow, will users need to search across projects? Full-text search, or just filtering by status/priority/assignee?"
5. `gq_005` (I): "Beyond kanban columns (To Do / In Progress / Done), are there other workflow states or automations? E.g., auto-assign when moved to In Progress?"

**Answers collected, combined_raw produced, completeness score: 88. Confidence: 90/100. Gate: pass.**


---

## REFERENCE: archetype-mechanism-maps

# Archetype Mechanism Maps

> Quick lookup: REQUIRED (R), OPTIONAL (O), UNLIKELY (U) per archetype per A-N category.
> Source: `app-archetype-library.md`. Used by Stage 2 to determine which gaps to ask about.

## Combined Matrix

| Cat | Name | Dashboard | Marketplace | Chat | CRUD/Tool | Social | Wizard | Landing | SaaS |
|-----|------|-----------|-------------|------|-----------|--------|--------|---------|------|
| A | Data Input | R | R | R | R | R | R | O | R |
| B | Data Storage | R | R | R | R | R | R | U | R |
| C | Data Processing | R | R | O | R | R | R | U | R |
| D | Data Output | R | R | R | R | R | R | R | R |
| E | Authentication | R | R | R | R | R | O | U | R |
| F | Authorization | O | R | O | O | R | U | U | R |
| G | Communication | O | R | R | O | R | O | O | R |
| H | Integration | O | R | O | O | O | O | O | O |
| I | Workflow | U | R | U | O | U | R | U | U |
| J | Search & Discovery | O | R | O | O | R | U | U | O |
| K | Collaboration | U | U | R | O | R | U | U | O |
| L | Monetization | U | R | U | U | U | U | U | R |
| M | Admin/Ops | O | R | O | U | R | U | U | R |
| N | Infrastructure | O | U | O | U | O | U | O | U |

## REQUIRED Category Counts

| Archetype | REQUIRED | OPTIONAL | UNLIKELY | Total Active (R+O) |
|-----------|----------|----------|----------|-------------------|
| Dashboard | 5 (ABCDE) | 6 (FGHJMN) | 3 (IKL) | 11 |
| Marketplace | 12 (ABCDEFGHIJLM) | 0 | 2 (KN) | 12 |
| Chat | 6 (ABDEGK) | 6 (CFHJMN) | 2 (IL) | 12 |
| CRUD/Tool | 5 (ABCDE) | 6 (FGHIJK) | 3 (LMN) | 11 |
| Social | 10 (ABCDEFGJKM) | 2 (HN) | 2 (IL) | 12 |
| Wizard | 5 (ABCDI) | 3 (EGH) | 6 (FJKLMN) | 8 |
| Landing | 1 (D) | 4 (AGHN) | 9 (BCEFIJKLM) | 5 |
| SaaS | 9 (ABCDEFGLM) | 3 (HJK) | 2 (IN) | 12 |

## Default Sub-Types per Archetype (REQUIRED categories only)

### Dashboard
- A: Forms (filter controls, date pickers)
- B: Relational DB or API
- C: Calculations (aggregations, statistics)
- D: Charts/Graphs
- E: Email/Password

### Marketplace
- A: Forms (listing creation)
- B: Relational DB
- C: Validation (pricing, availability)
- D: Lists/Tables (browse listings)
- E: Email/Password + OAuth
- F: RBAC (buyer/seller/admin)
- G: In-App Notifications
- H: Payment Gateways (Stripe/PayPal)
- I: State Machines (order flow)
- J: Faceted Search
- L: Marketplace/Commission
- M: Content Moderation

### Chat / Messaging
- A: Forms (message composer)
- B: NoSQL/Document
- D: Real-time Feeds
- E: Email/Password
- G: Chat/Messaging + Push Notifications
- K: Profiles (presence, status)

### CRUD / Tool
- A: Forms (record creation/editing)
- B: Relational DB
- C: Validation
- D: Lists/Tables
- E: Email/Password

### Social Platform
- A: Forms + File Upload
- B: Relational DB + Blob Storage
- C: Filtering/Sorting (feed ranking)
- D: Real-time Feeds
- E: OAuth/Social
- F: Resource Ownership (privacy)
- G: In-App Notifications
- J: Full-text Search
- K: Comments + Reactions + Following
- M: Content Moderation

### Wizard / Onboarding
- A: Forms (multi-step)
- B: Relational DB (persist progress)
- C: Validation (per-step)
- D: Lists/Tables (summary/review)
- I: Wizards/Multi-step

### Landing Page
- D: Lists/Tables (feature tables, pricing)

### SaaS Product
- A: Forms (data entry, settings)
- B: Relational DB
- C: Calculations (business logic, metering)
- D: Lists/Tables + Charts
- E: Email/Password + OAuth
- F: RBAC + Feature Flags (tier gating)
- G: Email (transactional)
- L: Subscriptions
- M: Admin Dashboard

## Multi-Archetype Union Rules

When multiple archetypes match:
1. A category REQUIRED in ANY archetype -> REQUIRED in combined map.
2. A category OPTIONAL in one and UNLIKELY in another -> OPTIONAL wins.
3. For conflicting default sub-types, ask the user which fits.
4. SaaS always adds: F (RBAC + Feature Flags), G (Email), L (Subscriptions), M (Admin).


---

## REFERENCE: mechanism-categories

# Mechanism Categories A-N — Condensed Reference

> Source: `mechanism-identification-framework.md`. Stage 2 uses this to scan raw_input and generate sub-questions.

## Category A: Data Input
**What it is:** How data enters the system.
**Sub-types:** Forms, File Upload, Voice/Audio, Camera/OCR, Drag-and-Drop, Sensors/IoT, Copy/Paste & Import.
**Key sub-questions:**
1. What data types do users input? (text, numbers, dates, files, rich text?)
2. Multi-step forms or wizards?
3. File types accepted? Size limits?
4. Real-time validation or on-submit?
5. Bulk input needed? (CSV import, batch creation?)
6. Draft/autosave requirements?

## Category B: Data Storage
**What it is:** How and where data persists.
**Sub-types:** Relational DB, NoSQL/Document, Blob/File Storage, Cache Layer, Search Index, Audit Trail.
**Key sub-questions:**
1. Main entities/objects? (users, products, orders?)
2. Relationships between entities?
3. Schema fixed or flexible?
4. Data volume? (hundreds, thousands, millions?)
5. Data isolated per user/tenant or shared?
6. Audit/history requirement?

## Category C: Data Processing
**What it is:** Transformations, calculations, and logic.
**Sub-types:** Validation, Calculations, AI/ML, Batch Processing, Format Conversion, Filtering/Sorting.
**Key sub-questions:**
1. What calculations or transformations?
2. Trigger? (user action, schedule, event?)
3. Real-time or background?
4. AI/ML components? What do they do?
5. What happens if processing fails?

## Category D: Data Output
**What it is:** How data is displayed or delivered.
**Sub-types:** Lists/Tables, Charts/Graphs, Maps, Timelines, Kanban/Board, Export, Real-time Feeds.
**Key sub-questions:**
1. Main views/pages users see?
2. List views? Columns? Sortable? Filterable?
3. Dashboard/analytics views? What metrics?
4. Export needed? What formats?
5. Real-time updating? (live counters, feeds?)
6. Pagination? Infinite scroll?

## Category E: Authentication
**What it is:** How users prove who they are.
**Sub-types:** Email/Password, OAuth/Social, SSO, MFA, Magic Link, API Keys, Session Management.
**Key sub-questions:**
1. How do users sign up? (email/password, social, invite-only?)
2. Which OAuth providers?
3. MFA required?
4. Session management? (JWT, cookies?)
5. Password requirements? Reset flow?
6. Account deletion? What happens to data?

## Category F: Authorization
**What it is:** What users are allowed to do.
**Sub-types:** RBAC, ABAC, Resource Ownership, Multi-tenancy, Feature Flags, Rate Limiting.
**Key sub-questions:**
1. What roles exist? (admin, user, moderator?)
2. What can each role do?
3. Data isolated per user? Per org/team?
4. Subscription tiers that unlock features?
5. Can users share access? (invite, transfer?)
6. Row-level security?

## Category G: Communication
**What it is:** System-to-user and user-to-user communication.
**Sub-types:** Email, Push Notifications, In-App Notifications, SMS, Chat/Messaging, Webhooks, Activity Feeds.
**Key sub-questions:**
1. What events trigger notifications?
2. Which channels? (email, push, in-app?)
3. User notification preferences configurable?
4. Real-time chat needed? (1:1, group, channels?)
5. Webhooks to external services?

## Category H: Integration
**What it is:** Connections to external services.
**Sub-types:** REST/GraphQL Consumption, REST/GraphQL Exposure, Web Scraping, Payment Gateways, File/Data Sync, Social Media, Email Services.
**Key sub-questions:**
1. Which external services?
2. What data sent/received?
3. What happens when external service is down?
4. Does the app expose its own API?
5. Payment processor? Which one? What flows?

## Category I: Workflow
**What it is:** Multi-step processes and automation.
**Sub-types:** State Machines, Approval Flows, Cron Jobs, Queues, Event Triggers, Wizards/Multi-step, Retry/Recovery.
**Key sub-questions:**
1. Multi-step processes? What states?
2. What triggers state transitions?
3. Time-based triggers? (expire, remind?)
4. Scheduled/automated tasks?
5. Undo/rollback capability?

## Category J: Search & Discovery
**What it is:** How users find things.
**Sub-types:** Full-text Search, Faceted Search, Autocomplete, Recommendations, Tags/Categories, Favorites, Recent/History.
**Key sub-questions:**
1. What is searchable?
2. Full-text or just field-based filtering?
3. Filters? (category, date, status?)
4. Autocomplete needed?
5. Recommendations? Based on what?
6. Browse/explore mode?

## Category K: Collaboration
**What it is:** How users interact with each other.
**Sub-types:** Comments, @Mentions, Sharing, Co-editing, Reactions, Following, Profiles.
**Key sub-questions:**
1. Can users comment? On what?
2. @mentioning?
3. Share content? How? (link, invite, public?)
4. Real-time co-editing?
5. Reactions/votes? (likes, upvotes?)
6. User profiles? What info shown?

## Category L: Monetization
**What it is:** How the app makes money.
**Sub-types:** Subscriptions, One-time Purchase, Freemium/Trials, Usage-based, Marketplace/Commission, Invoicing, Refunds.
**Key sub-questions:**
1. Revenue model? (subscription, one-time, freemium, marketplace?)
2. Plans/tiers? What does each include?
3. Free tier? Trial period?
4. Payment processor?
5. Refund handling?
6. Team/org billing?

## Category M: Admin/Ops
**What it is:** Back-office management tools.
**Sub-types:** Admin Dashboard, User Management, Content Moderation, Feature Flags, Analytics, Configuration.
**Key sub-questions:**
1. Admin panel? What can admins do?
2. User management? (view, edit, suspend?)
3. Content moderation?
4. Analytics dashboards? What metrics?
5. Audit log?

## Category N: Infrastructure
**What it is:** System-level concerns.
**Sub-types:** Caching, DB Migrations, Circuit Breakers, Auto-scaling, Logging, Monitoring/APM, CI/CD.
**Key sub-questions:**
1. Where hosted? (cloud, serverless, self-hosted?)
2. Expected traffic?
3. Caching strategy needed?
4. Deployment method?
5. Monitoring/alerting needs?
6. Compliance requirements?

## Quick Signal Map

| User Says | Primary | Secondary |
|-----------|---------|-----------|
| "sign up and log in" | E | F |
| "sends an email when..." | G | I |
| "search for..." | J | D |
| "scrapes data from websites" | H | C |
| "subscription plan" | L | F |
| "upload files" | A | B |
| "generates a PDF" | C | D |
| "dashboard showing..." | D | M |
| "orders go through stages" | I | B |
| "comment and like" | K | G |
| "admins can ban users" | M | F |
| "handle 10K users" | N | B |
| "share with a link" | K | F |
| "calculates a score" | C | D |
| "chat feature" | G | K |


---

## REFERENCE: question-templates

# Question Templates for Gap Analysis

> Reusable patterns for generating adaptive gap questions.
> Fill in {placeholders} with app-specific context from raw_input and platform_profile.

## Pattern 1: REQUIRED Gap (Archetype expects it, user didn't mention it)

**Template:**
> "{Archetype} apps typically need {category_name}. {Specific_need_description}. How will yours handle this? ({option_1}, {option_2}, {option_3}, or something else?)"

**Examples:**
- "Marketplace apps need payment processing. How will buyers pay sellers? (Stripe, PayPal, direct bank transfer, or something else?)"
- "SaaS products need subscription billing. Will you offer plan tiers? (free/pro/team, single paid plan, usage-based, or something else?)"
- "Social platforms need content moderation. How will you handle inappropriate posts? (automated filters, user reports + manual review, AI moderation, or something else?)"

## Pattern 2: OPTIONAL Inquiry (Archetype says optional, check if needed)

**Template:**
> "Does your app need {category_name}? For example, {example_relevant_to_their_app}."

**Examples:**
- "Does your app need search? For example, letting users search across all their tasks by keyword or filter by status?"
- "Does your app need integrations? For example, syncing tasks with Google Calendar or importing from Trello?"
- "Does your app need a notification system? For example, email alerts when a due date is approaching?"

## Pattern 3: Sub-Type Specifics (Category identified but details missing)

**Template:**
> "You mentioned {what_user_said}. {Specific_sub_question}? ({option_1}, {option_2}, or {option_3}?)"

**Examples:**
- "You mentioned users can upload photos. What file types and size limits? (JPEG/PNG only up to 5MB, any image type up to 20MB, or also video files?)"
- "You mentioned email login. Will you also support social login? (Google only, Google + GitHub, Google + Apple, or email-only?)"
- "You mentioned a dashboard with charts. What specific metrics? (task completion rates, team productivity, time tracking, or something else?)"

## Pattern 4: Stack-Aware Question (Use platform_profile for context)

**Template:**
> "Since you're using {tech_stack_component}, {stack_specific_question}? ({stack_option_1}, {stack_option_2}?)"

**Stack-specific examples by platform:**

### Supabase
- "Since you're using Supabase, will you use Row Level Security to isolate user data, or handle authorization in your application code?"
- "Since you're using Supabase, will you use Supabase Auth for login, or a separate auth provider?"
- "Since you're using Supabase, will you use Edge Functions for server-side logic, or a separate API server?"

### Firebase
- "Since you're using Firebase, will you use Firestore security rules for authorization, or Cloud Functions middleware?"
- "Since you're using Firebase, will file uploads go to Cloud Storage with Firebase SDK, or a separate storage service?"
- "Since you're using Firebase, will you use Firebase Hosting, or deploy elsewhere?"

### Next.js / Vercel
- "Since you're using Next.js, will data fetching happen server-side (RSC), client-side (SWR/React Query), or a mix?"
- "Since you're deploying to Vercel, will you use Vercel's built-in analytics and edge functions?"

### Flutter / Mobile
- "Since you're building a mobile app, which platforms? (iOS only, Android only, or both?)"
- "Since you're using Flutter, will you use Firebase for the backend, Supabase, or a custom API?"

### Generic (no specific stack)
- "Where do you plan to host this? (Vercel, AWS, self-hosted, or undecided?)"
- "Do you have a preference for the database? (PostgreSQL, MySQL, MongoDB, or whatever fits best?)"

## Pattern 5: Contradiction Clarifier

**Template:**
> "You mentioned '{statement_1}' but also '{statement_2}'. Which takes priority? ({interpretation_1}, {interpretation_2}, or both in different contexts?)"

**Examples:**
- "You mentioned 'it should be simple' but also listed 12 features. Should we prioritize a minimal MVP first, or include all features from the start?"
- "You mentioned 'free for everyone' but also 'team workspaces with billing'. Will there be a free tier alongside a paid team plan, or is the entire app free?"

## Pattern 6: Developer's Choice Confirmation

**Template:**
> "For {category_name}, the standard approach for {archetype} apps is {default_approach}. Works for you, or do you have something different in mind?"

**Examples:**
- "For data storage, the standard approach for CRUD apps is a relational database (PostgreSQL). Works for you, or do you need something different?"
- "For session management, the standard approach is JWT with refresh tokens. Works for you?"

## Grouping Rules

When presenting questions, group by topic area:

1. **Core functionality gaps** — REQUIRED categories missing (highest priority)
2. **Feature questions** — OPTIONAL categories to confirm/deny
3. **Implementation specifics** — Sub-type details for identified categories
4. **Stack-specific** — Platform-tailored questions

Within each group, order from most impactful to least. Lead with the question whose answer affects the most downstream decisions (e.g., monetization model before payment processor details).

## Anti-Patterns (NEVER do these)

- "Tell me more about your app." (too vague)
- "What about authentication?" (too broad — offer specific options)
- "Have you thought about scalability?" (generic, not actionable)
- "What's your budget?" (not a mechanism question)
- "Can you describe the user flow?" (Stage 3's job, not Stage 2)
- Asking about something the user already clearly described in raw_input.
- Asking the same category twice in different questions.
- Asking more than 15 questions regardless of input length.


---

## REFERENCE: App Archetype Library

# App Archetype Library

> Used during Stage 2 (Gap Analysis) to reduce questioning overhead.
> Match the user's description to an archetype, load defaults, ask only about gaps.
>
> 8 archetypes x 14 mechanism categories (A-N) = pre-mapped defaults for fast gap analysis.
>
> **Relationship to pipeline:** Stage 2 (Gap Analysis) reads this library to identify which archetype(s) the user's idea matches. REQUIRED categories get auto-filled with default sub-types. OPTIONAL categories get one targeted question each. UNLIKELY categories are skipped unless the user specifically mentioned them.

---

## Archetype 1: Dashboard App

**One-line description:** An app that displays data, metrics, and analytics in visual layouts where users primarily read information with limited write operations like filters and date ranges.

### Mechanism Requirements

| Category | Name | Classification | Default Sub-type | Notes |
|----------|------|---------------|-----------------|-------|
| A | Data Input | REQUIRED | Forms | Dashboards need filter controls, date range pickers, and configuration forms |
| B | Data Storage | REQUIRED | Relational DB or API | Data has to come from somewhere — either a local database or external API endpoints |
| C | Data Processing | REQUIRED | Calculations | Aggregations, statistics, and metric computations are the core value of a dashboard |
| D | Data Output | REQUIRED | Charts/Graphs | Visualizing data is the entire purpose of a dashboard app |
| E | Authentication | REQUIRED | Email/Password | Users need accounts to see their personalized data |
| F | Authorization | OPTIONAL | — | Some dashboards have role-based views (admin vs viewer), but many are single-role |
| G | Communication | OPTIONAL | — | Scheduled report emails or threshold alerts are common but not universal |
| H | Integration | OPTIONAL | — | Many dashboards pull data from external APIs, but some use only local data |
| I | Workflow | UNLIKELY | — | Dashboards are read-heavy; they display results of processes, not manage processes |
| J | Search & Discovery | OPTIONAL | — | Filtering and searching through data points is common in data-heavy dashboards |
| K | Collaboration | UNLIKELY | — | Dashboards are typically solo viewing experiences, not collaborative |
| L | Monetization | UNLIKELY | — | Most dashboards are internal tools or features within a larger product, not standalone paid products |
| M | Admin/Ops | OPTIONAL | — | Some dashboards have admin settings for data sources or user management |
| N | Infrastructure | OPTIONAL | — | Caching matters for performance with large datasets, but not critical for MVP |

### Standard Pages

- **Overview Dashboard** — Primary view showing key metrics, KPI cards, and summary charts
- **Analytics Detail** — Drill-down view for a specific metric category with granular charts and data tables
- **Data Explorer** — Table view with sortable columns, filters, and search for raw data inspection
- **Login / Signup** — Authentication page with email/password or OAuth options
- **Settings & Preferences** — User preferences for date ranges, default views, notification thresholds
- **Report Builder** — Configure and export custom reports as PDF or CSV

### Example Apps

- **Google Analytics** — The canonical dashboard app: metrics, charts, date ranges, drill-downs, and export
- **Shopify Admin Dashboard** — E-commerce metrics (sales, orders, traffic) in visual layouts with filter controls
- **Datadog** — Infrastructure monitoring dashboard with real-time charts, alerts, and configurable views

---

## Archetype 2: Marketplace

**One-line description:** A two-sided platform connecting buyers and sellers (or providers and consumers) with listings, search, transactions, reviews, and trust mechanisms.

### Mechanism Requirements

| Category | Name | Classification | Default Sub-type | Notes |
|----------|------|---------------|-----------------|-------|
| A | Data Input | REQUIRED | Forms | Sellers create listings with structured forms (title, description, price, images) |
| B | Data Storage | REQUIRED | Relational DB | Listings, users, transactions, and reviews form a heavily relational data model |
| C | Data Processing | REQUIRED | Validation | Pricing calculations, availability checks, matching algorithms, and commission computation |
| D | Data Output | REQUIRED | Lists/Tables | Browsing listings, search results, and order history are core read operations |
| E | Authentication | REQUIRED | Email/Password + OAuth | Both buyers and sellers need accounts; social login reduces signup friction |
| F | Authorization | REQUIRED | RBAC | Distinct buyer, seller, and admin roles with different permissions and views |
| G | Communication | REQUIRED | In-App Notifications | Order updates, new messages, review requests — both sides need real-time alerts |
| H | Integration | REQUIRED | Payment Gateways | Transactions between buyers and sellers require Stripe/PayPal with escrow or split payments |
| I | Workflow | REQUIRED | State Machines | Orders flow through states: pending → paid → shipped → delivered → reviewed |
| J | Search & Discovery | REQUIRED | Faceted Search | Finding products/services by category, price, location, rating is a core user action |
| K | Collaboration | UNLIKELY | — | Reviews/ratings are feedback, not collaboration; co-editing, @mentions, and following are not marketplace mechanics |
| L | Monetization | REQUIRED | Marketplace/Commission | Platform takes a percentage of each transaction — this is the business model |
| M | Admin/Ops | REQUIRED | Content Moderation | Dispute resolution, listing approval, seller verification, and fraud detection are essential |
| N | Infrastructure | UNLIKELY | — | CDN and caching help at scale but MVP marketplaces run on basic hosting without special infra |

### Standard Pages

- **Home / Browse** — Featured listings, categories, and promotional sections
- **Search Results** — Filtered and sorted listings with faceted search sidebar
- **Listing Detail** — Full listing information with images, description, price, seller info, and reviews
- **Create / Edit Listing** — Multi-step form for sellers to create or update listings
- **Shopping Cart / Checkout** — Cart management and payment flow for buyers
- **Order Management** — Order history and status tracking for both buyers and sellers
- **Seller Dashboard** — Sales metrics, active listings, earnings, and payout information
- **User Profile** — Public profile showing ratings, reviews, and listing history

### Example Apps

- **Airbnb** — Two-sided marketplace connecting hosts and guests with listings, search, booking workflow, reviews, and platform commission
- **Etsy** — Seller storefronts, product search, cart/checkout, reviews, and transaction-based monetization
- **Uber** — Provider-consumer matching with real-time availability, pricing, payment processing, and rating system

---

## Archetype 3: Chat / Messaging App

**One-line description:** A real-time communication app where users send and receive messages in 1:1, group, or channel-based conversations with presence indicators and notifications.

### Mechanism Requirements

| Category | Name | Classification | Default Sub-type | Notes |
|----------|------|---------------|-----------------|-------|
| A | Data Input | REQUIRED | Forms | Message composer is a text input with optional rich formatting, emoji, and attachments |
| B | Data Storage | REQUIRED | NoSQL/Document | Messages are append-heavy, nested in conversations — document store fits naturally |
| C | Data Processing | OPTIONAL | — | Media processing (image resizing, link previews) and message formatting are common but not universal |
| D | Data Output | REQUIRED | Real-time Feeds | Message streams update live as new messages arrive — this is the core display pattern |
| E | Authentication | REQUIRED | Email/Password | Users need accounts tied to their identity for messaging |
| F | Authorization | OPTIONAL | — | Channel permissions and admin roles exist in some chat apps but not all (1:1 apps skip this) |
| G | Communication | REQUIRED | Chat/Messaging + Push Notifications | Real-time messaging IS the app; push notifications alert users when they are not in the app |
| H | Integration | OPTIONAL | — | Bots, webhooks, and external service connections are common in team chat, rare in personal chat |
| I | Workflow | UNLIKELY | — | Messages are sent and received — there are no multi-step state machines in core messaging |
| J | Search & Discovery | OPTIONAL | — | Message search and people/channel discovery are common in larger chat apps |
| K | Collaboration | REQUIRED | Profiles | User presence (online/offline/away), status messages, and contact lists are core to messaging |
| L | Monetization | UNLIKELY | — | Most chat apps are free for users; monetization (if any) is enterprise pricing, not per-message |
| M | Admin/Ops | OPTIONAL | — | Team/workspace administration exists in business chat apps but not personal messaging |
| N | Infrastructure | OPTIONAL | — | WebSocket infrastructure and message caching matter for performance but are implementation details |

### Standard Pages

- **Login / Signup** — Authentication with phone number or email verification
- **Conversation List (Inbox)** — All active conversations sorted by recency with unread indicators
- **Chat Room / Conversation** — Message thread with real-time updates, typing indicators, and message input
- **Contact / People List** — User directory for starting new conversations or adding to groups
- **User Profile** — Avatar, display name, status, and contact information
- **Settings** — Notification preferences, privacy controls, account management

### Example Apps

- **WhatsApp** — 1:1 and group messaging with end-to-end encryption, media sharing, and presence indicators
- **Slack** — Channel-based team messaging with threads, search, integrations, and workspace administration
- **Discord** — Server/channel structure with voice chat, roles, and bot ecosystem for communities

---

## Archetype 4: CRUD / Tool

**One-line description:** A utility app focused on creating, reading, updating, and deleting structured data — task managers, note apps, inventory trackers, CRM tools, and spreadsheet-like apps.

### Mechanism Requirements

| Category | Name | Classification | Default Sub-type | Notes |
|----------|------|---------------|-----------------|-------|
| A | Data Input | REQUIRED | Forms | Creating and editing records through structured forms is the primary user action |
| B | Data Storage | REQUIRED | Relational DB | Structured data with defined fields and relationships (tasks, contacts, inventory items) |
| C | Data Processing | REQUIRED | Validation | Input validation, business rule checks, and data consistency enforcement on every save |
| D | Data Output | REQUIRED | Lists/Tables | The main view is always a list or table of records with sorting and filtering |
| E | Authentication | REQUIRED | Email/Password | Users need accounts to store and retrieve their data |
| F | Authorization | OPTIONAL | — | Resource ownership (users see only their own data) is common; team roles are less common |
| G | Communication | OPTIONAL | — | Email notifications for deadlines or changes are nice-to-have, not core |
| H | Integration | OPTIONAL | — | Import/export and API connections to other tools are common in mature CRUD apps |
| I | Workflow | OPTIONAL | — | Some tools have status workflows (to-do → in progress → done) but many are flat CRUD |
| J | Search & Discovery | OPTIONAL | — | Searching and filtering records becomes important as data volume grows |
| K | Collaboration | OPTIONAL | — | Sharing records and team collaboration exist in some tools but many are single-user |
| L | Monetization | UNLIKELY | — | Many CRUD tools are internal/personal utilities, not standalone paid products |
| M | Admin/Ops | UNLIKELY | — | Small-team tools rarely need admin panels or content moderation |
| N | Infrastructure | UNLIKELY | — | Simple CRUD apps run on basic hosting with no special infrastructure needs |

### Standard Pages

- **Login / Signup** — Authentication page
- **Item List** — Main view showing all records in a table or card grid with sort/filter controls
- **Item Detail** — Full record view with all fields, history, and related data
- **Create / Edit Form** — Form for creating new records or editing existing ones
- **Dashboard / Overview** — Summary statistics (total items, items by status, recent activity)
- **Settings** — User preferences, data export options, account management

### Example Apps

- **Todoist** — Task management CRUD with projects, priorities, due dates, and status tracking
- **Airtable** — Spreadsheet-database hybrid for structured data with views, filters, and formulas
- **Google Keep** — Minimal note-taking CRUD with labels, colors, and search

---

## Archetype 5: Social Platform

**One-line description:** An app centered on user-generated content, social graphs (following/followers), algorithmic or chronological feeds, and engagement mechanics like likes, comments, and shares.

### Mechanism Requirements

| Category | Name | Classification | Default Sub-type | Notes |
|----------|------|---------------|-----------------|-------|
| A | Data Input | REQUIRED | Forms + File Upload | Users create posts with text, images, and video — both form fields and media upload |
| B | Data Storage | REQUIRED | Relational DB + Blob Storage | User data and relationships in a relational DB; media files in blob/object storage |
| C | Data Processing | REQUIRED | Filtering/Sorting | Feed ranking, content recommendations, and trending calculations are core to engagement |
| D | Data Output | REQUIRED | Real-time Feeds | The social feed — an infinite-scroll stream of content from followed users and recommendations |
| E | Authentication | REQUIRED | OAuth/Social | Social login (Google, Apple) is natural for social platforms and reduces signup friction |
| F | Authorization | REQUIRED | Resource Ownership | Users own their posts; privacy settings control who sees what (public, friends-only, private) |
| G | Communication | REQUIRED | In-App Notifications | "Someone liked your post" and "New follower" notifications are essential for engagement loops |
| H | Integration | OPTIONAL | — | Social sharing to other platforms and link embeds are common but not required for core function |
| I | Workflow | UNLIKELY | — | Social platforms are event-driven (post, like, comment), not process-driven with state machines |
| J | Search & Discovery | REQUIRED | Full-text Search | Finding people, hashtags, and content is a core navigation mechanism |
| K | Collaboration | REQUIRED | Comments + Reactions + Following | Likes, comments, shares, and follow relationships ARE the social platform |
| L | Monetization | UNLIKELY | — | Most social platforms defer monetization; MVP launches are free and ad-free |
| M | Admin/Ops | REQUIRED | Content Moderation | User-generated content requires moderation for spam, harassment, and policy violations |
| N | Infrastructure | OPTIONAL | — | CDN for media delivery and caching for feeds help at scale but are not MVP-critical |

### Standard Pages

- **Login / Signup** — Social login and email registration
- **Feed (Home Timeline)** — Scrollable stream of posts from followed users and recommendations
- **User Profile** — Bio, avatar, post history, follower/following counts, and follow button
- **Post Detail** — Single post with full comments thread and engagement buttons
- **Discover / Explore** — Trending content, recommended users, hashtag browsing
- **Notifications** — Activity feed showing likes, comments, follows, and mentions
- **Create Post** — Composer for text, images, video with preview
- **Settings** — Account, privacy, notification preferences, blocked users

### Example Apps

- **Instagram** — Photo/video sharing with feed, stories, explore, likes, comments, and follower graph
- **Twitter/X** — Short-form text posts with retweets, likes, threads, and trending topics
- **Reddit** — Community-based content with upvotes, comments, subreddits, and content discovery

---

## Archetype 6: Wizard / Onboarding Flow

**One-line description:** A step-by-step guided process that collects information or walks users through a setup, with linear or branching progression, validation at each step, and a final summary or confirmation.

### Mechanism Requirements

| Category | Name | Classification | Default Sub-type | Notes |
|----------|------|---------------|-----------------|-------|
| A | Data Input | REQUIRED | Forms | Multi-step form input is the entire core mechanic — each step collects specific data |
| B | Data Storage | REQUIRED | Relational DB | Collected data must persist, including partial progress for resume-later capability |
| C | Data Processing | REQUIRED | Validation | Each step validates before allowing progression; final step may trigger calculations or decisions |
| D | Data Output | REQUIRED | Lists/Tables | Summary/review screen shows all collected data before final submission |
| E | Authentication | OPTIONAL | — | Some wizards are part of signup (pre-auth); others require login first — depends on context |
| F | Authorization | UNLIKELY | — | Wizards are typically single-path with no role differentiation |
| G | Communication | OPTIONAL | — | Confirmation emails after completion are common but not part of the core wizard flow |
| H | Integration | OPTIONAL | — | Wizard results often get sent to external systems (CRM, email service, payment processor) |
| I | Workflow | REQUIRED | Wizards/Multi-step | Step-by-step progression with branching logic IS a workflow by definition |
| J | Search & Discovery | UNLIKELY | — | Linear guided processes have no search — users are led through a fixed path |
| K | Collaboration | UNLIKELY | — | Wizards are solo experiences — one user filling out one flow |
| L | Monetization | UNLIKELY | — | Wizards collect data or configure settings; they do not sell anything directly |
| M | Admin/Ops | UNLIKELY | — | Simple flow with no admin layer needed |
| N | Infrastructure | UNLIKELY | — | Wizards are lightweight with no special infrastructure demands |

### Standard Pages

- **Welcome / Intro Screen** — Explains what the wizard does and what information will be needed
- **Step 1-N (Data Collection Steps)** — Each step focuses on one category of information with validation
- **Conditional Branch Screen** — Optional path that appears based on previous answers
- **Review / Summary** — Shows all collected data in a readable format for user confirmation
- **Confirmation / Success** — Final screen confirming submission with next steps or results

### Example Apps

- **TurboTax** — Step-by-step tax filing wizard that collects income, deductions, and credits through guided questions
- **Typeform** — Conversational form builder where each question is one step with smooth transitions
- **Wix Site Builder Setup** — Guided onboarding that asks about business type, goals, and preferences to generate a starter site

---

## Archetype 7: Landing Page

**One-line description:** A marketing or informational page focused on conversion with static content, CTAs, signup forms, pricing tables, and social proof — minimal backend logic.

### Mechanism Requirements

| Category | Name | Classification | Default Sub-type | Notes |
|----------|------|---------------|-----------------|-------|
| A | Data Input | OPTIONAL | — | Signup forms and contact forms are common but not every landing page has them |
| B | Data Storage | UNLIKELY | — | Landing pages are mostly static; at most they store form submissions or email signups |
| C | Data Processing | UNLIKELY | — | Static content pages have no data processing requirements |
| D | Data Output | REQUIRED | Lists/Tables | Feature comparison tables, pricing tiers, testimonial cards — structured content display |
| E | Authentication | UNLIKELY | — | Landing pages are public; authentication belongs to the product they link to |
| F | Authorization | UNLIKELY | — | Everyone sees the same page — no roles or permissions |
| G | Communication | OPTIONAL | — | Newsletter signup and email capture are common conversion tactics |
| H | Integration | OPTIONAL | — | Analytics (Google Analytics), email services (Mailchimp), and CRM integrations are common |
| I | Workflow | UNLIKELY | — | Static pages have no multi-step processes |
| J | Search & Discovery | UNLIKELY | — | Landing pages are small enough that search is unnecessary |
| K | Collaboration | UNLIKELY | — | Landing pages are not collaborative experiences |
| L | Monetization | UNLIKELY | — | The landing page drives users TO a monetized product — it does not monetize itself |
| M | Admin/Ops | UNLIKELY | — | Static content with no admin layer needed |
| N | Infrastructure | OPTIONAL | — | CDN and caching improve load speed, which directly affects conversion rates |

### Standard Pages

- **Hero / Home** — Primary landing section with headline, value proposition, and main CTA
- **Features / Benefits** — Detailed breakdown of what the product offers with icons or illustrations
- **Pricing** — Plan comparison table with feature lists and signup buttons per tier
- **Testimonials / Social Proof** — Customer quotes, logos, case study snippets, and trust badges
- **FAQ** — Common questions and answers to reduce signup friction
- **Contact / Signup** — Form for leads, demo requests, or newsletter subscription

### Example Apps

- **Stripe's Homepage** — Clean, conversion-focused landing with product explanation, feature sections, pricing, and developer-friendly CTAs
- **Linear's Homepage** — Minimal, fast landing page with feature highlights, social proof, and clear signup flow
- **Notion's Homepage** — Template-rich landing page with use case sections, pricing comparison, and customer logos

---

## Archetype 8: SaaS Product

**One-line description:** A subscription-based software product with user accounts, feature tiers, team management, billing, and an admin layer — typically combines CRUD + Dashboard mechanics with a unique value proposition.

### Mechanism Requirements

| Category | Name | Classification | Default Sub-type | Notes |
|----------|------|---------------|-----------------|-------|
| A | Data Input | REQUIRED | Forms | User data entry, settings configuration, and content creation forms |
| B | Data Storage | REQUIRED | Relational DB | User data, subscription records, team structures, and product-specific data |
| C | Data Processing | REQUIRED | Calculations | Business logic specific to the SaaS value prop plus usage metering and billing calculations |
| D | Data Output | REQUIRED | Lists/Tables + Charts | Product-specific views plus usage dashboards and account overview |
| E | Authentication | REQUIRED | Email/Password + OAuth | Multiple auth methods reduce friction; enterprise customers may need SSO |
| F | Authorization | REQUIRED | RBAC + Feature Flags | Subscription tiers gate features; team roles control access within organizations |
| G | Communication | REQUIRED | Email | Transactional emails (welcome, invoice, password reset), onboarding sequences, and product updates |
| H | Integration | OPTIONAL | — | Many SaaS products integrate with other tools, but the core product may stand alone |
| I | Workflow | UNLIKELY | — | Default SaaS products are CRUD-based; complex state machines and approval flows are feature-specific, not archetype-standard |
| J | Search & Discovery | OPTIONAL | — | Depends on data volume — products with many records need search, simple tools may not |
| K | Collaboration | OPTIONAL | — | Team features (shared workspaces, comments, mentions) are common in B2B SaaS but not universal |
| L | Monetization | REQUIRED | Subscriptions | Monthly/annual billing with plan tiers is the defining characteristic of SaaS |
| M | Admin/Ops | REQUIRED | Admin Dashboard | System health, user management, subscription analytics, and feature flag controls |
| N | Infrastructure | UNLIKELY | — | Monitoring, auto-scaling, and CI/CD become important at scale but MVP SaaS runs on basic hosting |

### Standard Pages

- **Marketing / Landing Page** — Public-facing page explaining the product with pricing and signup CTA
- **Login / Signup** — Multi-method authentication with social login and SSO options
- **Main Workspace / Dashboard** — The core product experience where users spend most of their time
- **Account Settings** — Profile, password, notification preferences, and connected accounts
- **Billing / Subscription** — Current plan, usage metrics, payment method, invoice history, and upgrade options
- **Team Management** — Invite members, assign roles, manage permissions within an organization
- **Admin Panel** — Internal dashboard for system operators showing user metrics, health, and config

### Example Apps

- **Figma** — Design tool SaaS with team workspaces, subscription tiers (free/pro/org), real-time collaboration, and admin controls
- **Notion** — Workspace SaaS combining notes, databases, and docs with team plans, member management, and usage-based features
- **Canva** — Design SaaS with free/pro/team tiers, template marketplace, team brand kits, and asset management

---

## How to Use This Library

These instructions are for the Stage 2 (Gap Analysis) agent. Follow them mechanically.

### Step 1: Match

Read the user's raw idea description from Stage 1. Identify which archetype(s) it most closely matches.

**Matching rules:**
- An app can match MULTIPLE archetypes. Example: "a marketplace with analytics" = Marketplace + Dashboard.
- Match based on the PRIMARY user action described:
  - User views data/metrics → **Dashboard**
  - User buys/sells between two parties → **Marketplace**
  - User sends/receives messages in real time → **Chat / Messaging**
  - User creates/edits/deletes records → **CRUD / Tool**
  - User posts content and follows other users → **Social Platform**
  - User walks through a step-by-step process → **Wizard / Onboarding**
  - The output is a marketing/info page → **Landing Page**
  - User pays a subscription for ongoing software access → **SaaS Product**
- If the description mentions subscription billing or team management alongside another archetype, ALSO match **SaaS Product** and union the mechanism maps.
- If multiple archetypes match, union all REQUIRED categories from each. A category that is REQUIRED in ANY matched archetype becomes REQUIRED in the combined map.

### Step 2: Load Defaults

For the matched archetype(s), load all REQUIRED mechanism categories with their default sub-types. These are pre-filled into the context packet.

**Rules:**
- Do NOT ask the user about REQUIRED categories unless their description explicitly contradicts the default. Example: if their Dashboard description says "no user accounts needed," then E (Authentication) drops from REQUIRED to inapplicable despite the archetype default.
- If multiple archetypes matched, use the most specific default sub-type from whichever archetype is more relevant. Example: if both Dashboard (Forms) and Marketplace (Forms) mark A as REQUIRED, keep "Forms" as the default.

### Step 3: Ask About OPTIONAL

For each OPTIONAL category in the combined map, ask the user ONE targeted question. Use this format:

> "Does your app need **[category name]**? For example, [archetype-specific example relevant to their idea]."

**Rules:**
- Phrase the example in terms of THEIR app, not generic terms. Example: for a recipe-sharing app (Social archetype), ask "Does your app need **monetization**? For example, a premium tier that unlocks exclusive recipes?" — not "Does your app need monetization? For example, subscriptions."
- Ask all OPTIONAL questions in a single batch, not one at a time.
- If the user already mentioned something that maps to an OPTIONAL category in their rant, skip the question — mark it as needed and move to sub-questions.

### Step 4: Skip UNLIKELY

Do NOT ask about UNLIKELY categories. Period.

**Exception:** If the user's Stage 1 description specifically mentions something that maps to an UNLIKELY category, override the UNLIKELY classification and treat it as REQUIRED. Example: if a Dashboard user says "and it should have a chat feature," that maps to G (Communication) and K (Collaboration), which are UNLIKELY for Dashboards. Override them to REQUIRED and ask sub-questions.

### Step 5: Deep-Dive on Mentioned

For every category that is active (either REQUIRED by archetype, confirmed OPTIONAL by user, or mentioned in the rant), ask the sub-questions from the `mechanism-identification-framework.md` to get specifics.

**Rules:**
- For REQUIRED categories with default sub-types, start with a confirming question: "For data storage, the standard approach is a relational database. Does that work, or do you need something different?"
- For user-confirmed OPTIONAL categories, ask the full sub-question set.
- For rant-mentioned categories, ask only the sub-questions that the rant didn't already answer.

### Step 6: Handle No-Match

If the user's idea does not match ANY archetype:

1. State: "Your app doesn't fit a standard archetype, so I need to ask about all mechanism categories."
2. Fall back to asking about ALL 14 categories (A-N) one by one using the standard questions from the mechanism identification framework.
3. Flag `archetype_match: "none"` in the context packet so downstream stages know this was a full-coverage gap analysis.

### Step 7: Handle Hybrid

If the user's idea matches 2 or more archetypes:

1. State: "Your app looks like a combination of **[Archetype A]** and **[Archetype B]**. I'm loading the standard requirements for both."
2. Union the REQUIRED categories (anything REQUIRED in either archetype is REQUIRED in the combined map).
3. For categories where both archetypes have different default sub-types, ask: "For [category], [Archetype A] apps typically use [sub-type A] while [Archetype B] apps typically use [sub-type B]. Which fits your app better?"
4. For OPTIONAL categories, ask about any that are OPTIONAL in either archetype (even if UNLIKELY in the other).
5. Flag `archetype_match: ["Archetype A", "Archetype B"]` in the context packet.

---

## Quick Reference: Classification Counts

| Archetype | REQUIRED | OPTIONAL | UNLIKELY |
|-----------|----------|----------|----------|
| Dashboard App | 5 (A, B, C, D, E) | 6 (F, G, H, J, M, N) | 3 (I, K, L) |
| Marketplace | 12 (A, B, C, D, E, F, G, H, I, J, L, M) | 0 | 2 (K, N) |
| Chat / Messaging | 6 (A, B, D, E, G, K) | 6 (C, F, H, J, M, N) | 2 (I, L) |
| CRUD / Tool | 5 (A, B, C, D, E) | 6 (F, G, H, I, J, K) | 3 (L, M, N) |
| Social Platform | 10 (A, B, C, D, E, F, G, J, K, M) | 2 (H, N) | 2 (I, L) |
| Wizard / Onboarding | 5 (A, B, C, D, I) | 3 (E, G, H) | 6 (F, J, K, L, M, N) |
| Landing Page | 1 (D) | 4 (A, G, H, N) | 9 (B, C, E, F, I, J, K, L, M) |
| SaaS Product | 9 (A, B, C, D, E, F, G, L, M) | 3 (H, J, K) | 2 (I, N) |

> **Note on Marketplace having 0 OPTIONAL:** Marketplaces are inherently complex — every mechanism is either definitely needed (REQUIRED) or genuinely irrelevant (UNLIKELY). This means the gap analysis agent asks zero OPTIONAL questions for a pure marketplace, but has 12 REQUIRED categories to deep-dive on. Expect a longer conversation.

---

## Archetype Complexity Ranking

For agent planning and user expectation-setting:

| Rank | Archetype | Active Categories | Build Complexity |
|------|-----------|-------------------|-----------------|
| 1 | Landing Page | 1 REQUIRED + 4 OPTIONAL = ~3-5 active | Low |
| 2 | Wizard / Onboarding | 5 REQUIRED + 3 OPTIONAL = ~6-7 active | Low-Medium |
| 3 | CRUD / Tool | 5 REQUIRED + 6 OPTIONAL = ~7-9 active | Medium |
| 4 | Dashboard App | 5 REQUIRED + 6 OPTIONAL = ~7-9 active | Medium |
| 5 | Chat / Messaging | 6 REQUIRED + 6 OPTIONAL = ~8-10 active | Medium-High |
| 6 | Social Platform | 10 REQUIRED + 2 OPTIONAL = ~10-11 active | High |
| 7 | SaaS Product | 9 REQUIRED + 3 OPTIONAL = ~10-11 active | High |
| 8 | Marketplace | 12 REQUIRED + 0 OPTIONAL = ~12 active | Very High |


---

## REFERENCE: Mechanism Identification Framework

# Mechanism Identification Framework

> The "Periodic Table of App Mechanisms" — used during Stage 2 (Gap Analysis) and Stage 4 (Mechanism Extraction) to systematically break down what an app DOES.
>
> When someone describes their app, map their description to these categories. Then ask the sub-questions for each identified mechanism. For categories they DIDN'T mention, ask if their app needs them.

---

## How to Use This

1. **Listen to the user's description** (rant, brain dump, whatever)
2. **Tag every feature/action they describe** with a mechanism category (A-N)
3. **For each tagged mechanism**, ask the sub-questions below
4. **For categories NOT mentioned**, ask: "Does your app need [category]?"
5. **Output**: A complete mechanism map with answers for each active category

---

## Category A: Data Input

**What it is:** How data enters the system from users or external sources.

| Sub-type | Examples |
|----------|----------|
| Forms | Text inputs, dropdowns, date pickers, multi-step wizards |
| File Upload | Images, documents, video, bulk CSV import |
| Voice/Audio | Speech-to-text, voice commands, audio recording |
| Camera/OCR | Photo capture, document scanning, barcode reading |
| Drag-and-Drop | Reordering lists, kanban boards, file drop zones |
| Sensors/IoT | GPS location, accelerometer, biometric input |
| Copy/Paste & Import | Clipboard, URL parsing, data import from other apps |

### Sub-Questions
1. What types of data do users input? (text, numbers, dates, files, rich text?)
2. Are there multi-step forms or wizards?
3. What file types are accepted? Size limits?
4. Is real-time validation needed (as-they-type) or on-submit?
5. Do users input data on behalf of others (admin entry)?
6. Is bulk input needed (CSV import, batch creation)?
7. Are there draft/autosave requirements?

---

## Category B: Data Storage

**What it is:** How and where data persists.

| Sub-type | Examples |
|----------|----------|
| Relational DB | PostgreSQL, MySQL, SQLite — structured, normalized |
| NoSQL/Document | MongoDB, Firestore — flexible schema, nested documents |
| Blob/File Storage | S3, Cloud Storage — media, attachments, exports |
| Cache Layer | Redis, Memcached — hot data, session state |
| Search Index | Elasticsearch, Algolia, pgvector — fast text/vector search |
| Audit Trail | Immutable log of all changes for compliance |

### Sub-Questions
1. What are the main entities/objects? (users, products, orders, etc.)
2. What are the relationships between entities? (one-to-many, many-to-many?)
3. Is the schema fixed or does it need to be flexible?
4. How much data will there be? (hundreds, thousands, millions of records?)
5. Is data isolated per user/tenant or shared?
6. What needs to be cached for performance?
7. Is there an audit/history requirement? (who changed what, when?)
8. Data retention — how long is data kept? Auto-delete rules?

---

## Category C: Data Processing

**What it is:** Transformations, calculations, and logic applied to data.

| Sub-type | Examples |
|----------|----------|
| Validation | Input sanitization, business rule checks |
| Calculations | Pricing, scoring, statistics, aggregations |
| AI/ML | Classification, generation, recommendations, embeddings |
| Batch Processing | Nightly reports, bulk updates, data migrations |
| Format Conversion | PDF generation, image resizing, data export formatting |
| Filtering/Sorting | Complex queries, faceted results, dynamic sorting |

### Sub-Questions
1. What calculations or transformations happen to the data?
2. What triggers the processing? (user action, schedule, event?)
3. Is it real-time (blocking) or background (async)?
4. What's the input and what's the expected output?
5. Are there AI/ML components? What do they do specifically?
6. What happens if processing fails? Retry? Fallback?
7. Are there rate limits or resource constraints?

---

## Category D: Data Output

**What it is:** How data is displayed or delivered to users.

| Sub-type | Examples |
|----------|----------|
| Lists/Tables | Paginated lists, sortable tables, infinite scroll |
| Charts/Graphs | Bar, line, pie, heatmaps, dashboards |
| Maps | Geographic data, location markers, route display |
| Timelines | Activity feeds, history views, changelog |
| Kanban/Board | Status columns, drag-to-reorder |
| Export | PDF, CSV, Excel, JSON download |
| Print | Print-optimized layouts, receipts |
| Real-time Feeds | Live updates, streaming data, websocket-driven |

### Sub-Questions
1. What are the main views/pages users see?
2. Are there list views? What columns/fields? Sortable? Filterable?
3. Are there dashboard/analytics views? What metrics?
4. Do users need to export data? What formats?
5. Is real-time updating needed? (live counters, streaming feeds?)
6. What does an empty state look like? (no data yet)
7. Is there pagination? Infinite scroll? Load-more?

---

## Category E: Authentication

**What it is:** How users prove who they are.

| Sub-type | Examples |
|----------|----------|
| Email/Password | Traditional signup/login |
| OAuth/Social | Google, GitHub, Apple, Facebook sign-in |
| SSO | SAML, enterprise single sign-on |
| MFA | Two-factor via SMS, authenticator app, hardware key |
| Magic Link | Passwordless email link login |
| API Keys | Machine-to-machine authentication |
| Session Management | JWT, cookies, refresh tokens, session timeout |

### Sub-Questions
1. How do users sign up? (email/password, social, invite-only?)
2. Which OAuth providers are needed?
3. Is MFA required? For all users or just admins?
4. How are sessions managed? (JWT, cookies, refresh tokens?)
5. What's the session timeout?
6. Is there a "remember me" feature?
7. Password requirements? Reset flow?
8. Is there account deletion? What happens to user data?

---

## Category F: Authorization

**What it is:** What users are allowed to do once authenticated.

| Sub-type | Examples |
|----------|----------|
| RBAC | Admin, editor, viewer roles |
| ABAC | Attribute-based (department, location, subscription tier) |
| Resource Ownership | Users can only see/edit their own data |
| Multi-tenancy | Organizations/teams with isolated data |
| Feature Flags | Features enabled per user/plan/group |
| Rate Limiting | Per-user or per-plan API/action limits |

### Sub-Questions
1. What roles exist? (admin, user, moderator, viewer?)
2. What can each role do? (CRUD per entity)
3. Is data isolated per user? Per organization/team?
4. Are there subscription tiers that unlock features?
5. Can users share access with others? (invite, transfer ownership?)
6. Are there approval workflows? (request access, admin approves?)
7. Row-level security? (users see only their own records?)

---

## Category G: Communication

**What it is:** How the system communicates with users or external systems.

| Sub-type | Examples |
|----------|----------|
| Email | Transactional, marketing, digests |
| Push Notifications | Mobile push, browser notifications |
| In-App Notifications | Bell icon, notification center, badges |
| SMS | Verification codes, alerts |
| Chat/Messaging | Real-time chat, direct messages, channels |
| Webhooks | Outbound event notifications to other systems |
| Activity Feeds | "John liked your post" style updates |

### Sub-Questions
1. What events trigger notifications? (signup, purchase, mention, etc.)
2. Which channels? (email, push, in-app, SMS?)
3. Can users configure notification preferences?
4. Are there email templates? What content?
5. Is real-time chat needed? 1:1, group, or channels?
6. Are there digest/summary emails? (daily, weekly?)
7. Do you need to send webhooks to external services?

---

## Category H: Integration

**What it is:** Connections to external services and APIs.

| Sub-type | Examples |
|----------|----------|
| REST/GraphQL Consumption | Calling external APIs |
| REST/GraphQL Exposure | Providing APIs for others to call |
| Web Scraping | Extracting data from websites |
| Payment Gateways | Stripe, PayPal, Apple Pay |
| File/Data Sync | Dropbox, Google Drive, S3 sync |
| Social Media | Posting, reading feeds, sharing |
| Email Services | SendGrid, SES, Mailgun |

### Sub-Questions
1. Which external services does the app connect to?
2. What data is sent/received from each?
3. What authentication does each external API need?
4. What happens when an external service is down? Fallback?
5. Are there rate limits on external APIs?
6. Does the app expose its own API for others?
7. Is there a payment processor? Which one? What flows? (one-time, subscription, refunds?)

---

## Category I: Workflow

**What it is:** Multi-step processes, state machines, and automation.

| Sub-type | Examples |
|----------|----------|
| State Machines | Order status (pending → processing → shipped → delivered) |
| Approval Flows | Submit → review → approve/reject |
| Cron Jobs | Scheduled tasks (nightly cleanup, weekly reports) |
| Queues | Background job processing, retry logic |
| Event Triggers | "When X happens, do Y" automation |
| Wizards/Multi-step | Step-by-step guided processes |
| Retry/Recovery | Automatic retry on failure, dead letter queues |

### Sub-Questions
1. What multi-step processes exist? What are the states?
2. What triggers transitions between states?
3. Who can trigger each transition? (user, admin, system?)
4. Are there time-based triggers? (expire after 24h, send reminder after 3 days?)
5. What happens when a step fails?
6. Are there scheduled/automated tasks? How often?
7. Is there an undo/rollback capability?

---

## Category J: Search & Discovery

**What it is:** How users find things within the app.

| Sub-type | Examples |
|----------|----------|
| Full-text Search | Keyword search across content |
| Faceted Search | Filter by category, price range, date, etc. |
| Autocomplete | Type-ahead suggestions |
| Recommendations | "Similar items", "You might also like" |
| Tags/Categories | Taxonomy, tagging system |
| Favorites/Bookmarks | Save for later |
| Recent/History | Recently viewed, search history |

### Sub-Questions
1. What is searchable? (products, users, content, everything?)
2. Is full-text search needed or just field-based filtering?
3. What filters are available? (category, date, status, price range?)
4. Is autocomplete/type-ahead needed?
5. Are there recommendations? Based on what? (behavior, similarity, manual curation?)
6. Can users save/bookmark items?
7. Is there a browse/explore mode? (categories, trending, new?)

---

## Category K: Collaboration

**What it is:** How users interact with each other through the app.

| Sub-type | Examples |
|----------|----------|
| Comments | On items, documents, tasks |
| @Mentions | Notify specific users in content |
| Sharing | Share items via link, invite collaborators |
| Co-editing | Simultaneous editing (Google Docs style) |
| Reactions | Likes, upvotes, emoji reactions |
| Following | Follow users, topics, items for updates |
| Profiles | User profiles, avatars, bio |

### Sub-Questions
1. Can users comment on things? What things?
2. Is there @mentioning? Who can be mentioned?
3. Can users share content with others? How? (link, invite, public?)
4. Is real-time co-editing needed?
5. Are there reactions/votes? (likes, upvotes, stars?)
6. Can users follow other users or items?
7. Are there user profiles? What info is shown?

---

## Category L: Monetization

**What it is:** How the app makes money.

| Sub-type | Examples |
|----------|----------|
| Subscriptions | Monthly/annual plans, auto-renewal |
| One-time Purchase | Buy once, own forever |
| Freemium/Trials | Free tier with paid upgrades, time-limited trials |
| Usage-based/Metering | Pay per API call, per GB stored, per seat |
| Marketplace/Commission | Platform fee on transactions between users |
| Invoicing | B2B billing, custom invoices, net-30 terms |
| Refunds/Credits | Cancellation policy, prorated refunds |

### Sub-Questions
1. What's the revenue model? (subscription, one-time, freemium, marketplace?)
2. What plans/tiers exist? What does each include?
3. Is there a free tier? What's included?
4. Is there a trial period? How long?
5. What payment processor? (Stripe, PayPal, etc.)
6. How are refunds handled?
7. Is there usage metering? What's metered?
8. Are there team/organization billing features?

---

## Category M: Admin/Ops

**What it is:** Back-office tools for managing the system.

| Sub-type | Examples |
|----------|----------|
| Admin Dashboard | System overview, KPIs, health metrics |
| User Management | View/edit/ban users, impersonate |
| Content Moderation | Review flagged content, approve/reject |
| Feature Flags | Toggle features per user/group/environment |
| Analytics | Usage stats, funnel analysis, event tracking |
| Configuration | System settings, environment config |

### Sub-Questions
1. Is there an admin panel? What can admins do?
2. Can admins manage users? (view, edit, suspend, delete?)
3. Is there content moderation? What gets moderated?
4. Are there analytics dashboards? What metrics?
5. Can admins configure system settings?
6. Is there an audit log? (who did what, when?)
7. Are there feature flags or A/B testing needs?

---

## Category N: Infrastructure

**What it is:** System-level concerns that support the app.

| Sub-type | Examples |
|----------|----------|
| Caching | CDN, Redis, browser cache, service worker |
| Database Migrations | Schema versioning, zero-downtime migrations |
| Circuit Breakers | Graceful degradation when services fail |
| Auto-scaling | Handle traffic spikes, scale-to-zero |
| Logging | Structured logs, log aggregation |
| Monitoring/APM | Uptime checks, performance tracking, alerting |
| CI/CD | Automated testing, deployment pipelines |

### Sub-Questions
1. Where is the app hosted? (cloud, serverless, self-hosted?)
2. What's the expected traffic? (concurrent users, requests/sec?)
3. Is there a caching strategy needed?
4. How are deployments done? (CI/CD, manual, blue-green?)
5. What monitoring/alerting is needed?
6. What's the uptime requirement? (99.9%? 99.99%?)
7. Are there compliance requirements that affect infrastructure? (data residency, encryption at rest?)

---

## Quick Reference: Mechanism Identification Cheat Sheet

When the user says... → It maps to:

| User Says | Primary Mechanism | Secondary |
|-----------|------------------|-----------|
| "users can sign up and log in" | E (Auth) | F (Authorization) |
| "it sends you an email when..." | G (Communication) | I (Workflow) |
| "you can search for..." | J (Search) | D (Output) |
| "it scrapes data from websites" | H (Integration) | C (Processing) |
| "there's a subscription plan" | L (Monetization) | F (Authorization) |
| "users can upload files" | A (Input) | B (Storage) |
| "it generates a PDF report" | C (Processing) | D (Output) |
| "there's a dashboard showing..." | D (Output) | M (Admin) |
| "orders go through stages" | I (Workflow) | B (Storage) |
| "users can comment and like" | K (Collaboration) | G (Communication) |
| "admins can ban users" | M (Admin) | F (Authorization) |
| "it needs to handle 10K users" | N (Infrastructure) | B (Storage) |
| "users can share with a link" | K (Collaboration) | F (Authorization) |
| "it calculates a score based on..." | C (Processing) | D (Output) |
| "there's a chat feature" | G (Communication) | K (Collaboration) |


---

## 🔗 Pipeline Integration — Automatic Stage Advancement

**This section is added for pipeline automation. It tells you how to signal stage completion.**

After completing ALL steps above and producing your complete output:

### Stage Completion Protocol

1. **Verify your confidence score** meets the gate threshold (≥ 70)
2. **Verify the complete JSON output** has been produced and meets the contract
3. **Output the completion marker** on its own line as the ABSOLUTE LAST thing in your response:

```
[STAGE_COMPLETE]
```

### Rules for the completion marker:

- `[STAGE_COMPLETE]` MUST be the absolute last thing in your response — nothing after it
- Your complete JSON output (context_packet) MUST come BEFORE the marker
- **Never** output `[STAGE_COMPLETE]` until the stage contract is fully met
- **Never** output `[STAGE_COMPLETE]` if the confidence score is below 70
- If you need to ask the user questions, do **NOT** output `[STAGE_COMPLETE]` — wait for answers first, produce your final output, THEN output the marker
- If the gate_result is "fail" (score < 70), trigger the escape hatch protocol instead — do NOT output `[STAGE_COMPLETE]`

### What happens when you output [STAGE_COMPLETE]:

1. The pipeline captures everything before the marker as your stage output
2. Your output becomes the input for the next stage
3. The next stage starts automatically — no manual intervention needed

### Example — end of your response:

```json
{
  "stage_2": { ... your complete output ... },
  "metadata": {
    "confidence_scores": {
      "2": { "score": 93, "gate_result": "pass" }
    }
  }
}
```

[STAGE_COMPLETE]


================================================================================
STAGE 3: AGENT OS STRUCTURING
================================================================================

---
name: stage-03-agent-os-structuring
description: Structure raw idea into concept document with product identity, personas, feasibility, and drift anchor.
---

## Purpose

Transform the complete raw information from Stages 1+2 into a structured four-section concept document — product identity, target users, feasibility assessment, and problem statement. This is the normalization step: raw clay into a shaped block. No mechanism extraction, no "how" — only "what" and "why." The output persists as a drift anchor throughout the entire build.

## When to Use

Activate when: `context_packet.stage_2.combined_raw` exists AND `context_packet.stage_1` exists AND `context_packet.stage_0.platform_profile` exists (Stages 0-2 complete). Trigger phrases: "structure the idea", "agent os structuring", "organize concept", "create concept document", "structure into sections", "format the raw material".

Do NOT activate for: raw idea capture (Stage 1), gap analysis (Stage 2), mechanism extraction (Stage 4), scaffolding (Stage 5), or any request to "break into parts" or "extract mechanisms".

## Input Format

```json
{
  "stage_0": {
    "platform_profile": { "boilerplate_id": "string", "boilerplate_name": "string", "description": "string" },
    "tech_stack": { "framework": "string", "database": "string", "auth_provider": "string", "hosting": "string" }
  },
  "stage_1": {
    "raw_input": "string",
    "explicit_corrections": [{ "original": "string", "correction": "string", "context": "string" }]
  },
  "stage_2": {
    "combined_raw": "string — primary input, Stage 1 raw + all gap answers merged",
    "archetype_matches": [{ "archetype": "string", "confidence": 85, "rationale": "string" }],
    "mechanisms_identified": [{ "category_id": "A", "category_name": "string", "sub_types": ["string"], "evidence": "string" }],
    "checklist_coverage": { "covered": ["string"], "not_applicable": ["string"], "deferred": ["string"] },
    "scope_contract": "string"
  },
  "metadata": { "app_type": "greenfield | existing", "current_stage": 2 }
}
```

## Process

### Step 1: Ingest and Inventory Raw Material

Read `stage_2.combined_raw` in full. Also read `stage_1.explicit_corrections`. Before structuring, make a mental inventory answering five questions:

1. **What product is being described?** — Name, core functionality
2. **Who is it for?** — Target users, personas
3. **What problem does it solve?** — Pain point from user's perspective
4. **What market context is mentioned?** — Competitors, landscape, timing
5. **What has the user explicitly corrected?** — Contradictions, corrections

Cross-reference `stage_2.mechanisms_identified` to ensure every mentioned mechanism category appears in your inventory. Cross-reference `stage_2.checklist_coverage` for completeness awareness. Do NOT skip any information — every piece must appear in the structured output.

### Step 2: Resolve Ambiguities

Scan `combined_raw` for overlapping, contradictory, or duplicate concepts. Apply resolution rules (see `references/ambiguity-resolution-rules.md`):

- **Later overrides earlier**: If user said "for enterprises" then "actually for freelancers" → resolution is "freelancers"
- **Explicit corrections win**: Apply all entries from `stage_1.explicit_corrections` — corrected version takes precedence
- **Merge duplicates**: Same feature described two ways → unify into one description, note both phrasings
- **Separate bundles**: Two distinct concepts lumped together → acknowledge both, keep logically separate

Log every resolution in the `ambiguity_resolutions` array. If an ambiguity CANNOT be resolved without user input, still log it with `source: "unresolvable — needs human input"` and include the specific question needed.

### Step 3: Structure into Four Sections

Apply the Agent OS five-lens framework (see `references/agent-os-framework.md`) to organize all material into four output sections:

**Section 1 — Concept & Context** (`concept_and_context`):
- `product_name`: Clear, concrete name (use what user stated, or derive from the core concept)
- `one_line_description`: Single sentence a stranger can understand
- `product_identity`: 1-2 paragraph identity description — what this product IS
- `core_value_proposition`: Why this product matters — the unique value

**Section 2 — Target User & Market** (`target_user_and_market`):
- `personas`: 1-4 concrete personas (NOT "users" — specific types: "freelance designer", "startup CTO"). Each has name, description, pain_points[], goals[]
- `market_context`: Market landscape, timing, trends
- `competitive_landscape`: Named competitors with specific differentiators (optional — only if user mentioned competitors or if obvious from context)

**Section 3 — Feasibility Assessment** (`feasibility_assessment`):
- `viability_summary`: Is this buildable and viable? Overall assessment
- `risks`: Identified risks with severity (low/medium/high) and mitigation strategies (optional — only if real risks exist)

**Section 4 — Problem Statement** (`problem_statement`):
- Clear, user-centric statement of the PAIN. Not the solution, not features — the problem.

**Writing rules:**
- Organized, readable prose — not stream-of-consciousness
- Each section must have 50+ words of substantive content
- Contains ONLY "what" and "why" — zero "how" (no architecture, no tech choices, no implementation)
- Do NOT decompose into mechanisms (no "auth system", "payment flow" as discrete units)
- Reference features in context but do not classify or break them apart

### Step 4: Create the Drift Anchor

Write `drift_anchor`: a 2-4 sentence canonical product description capturing the ESSENCE. This persists throughout the entire build as the reference point for scope creep detection.

**Good drift anchor criteria:**
- Specific enough that adding an unrelated feature would be flagged
- General enough that legitimate feature decisions aren't blocked
- Written in plain language a non-coder can read
- Covers: what it is, who it's for, what problem it solves

### Step 5: Validate Completeness

Before writing output, verify:

1. Every piece of information from `combined_raw` appears in at least one section
2. All `mechanisms_identified` categories from Stage 2 are referenced (not decomposed) in the output
3. All gap answers from Stage 2 are incorporated
4. No information was invented — organize only, do not add
5. Output contains ONLY "what" and "why" — zero "how"
6. Each section has 50+ words of substantive content
7. `drift_anchor` is present and meets the criteria above

If any check fails, revise the relevant section before proceeding to scoring.

### Step 6: Score and Gate

Run the confidence scoring (see Confidence Scoring section below). Based on total:
- **>= 90**: Write output normally
- **70-89**: Write output with warning flag in metadata
- **< 70**: Trigger escape hatch — do NOT write output

## Output Format

Written to `context_packet.stage_3`:

```json
{
  "concept_and_context": {
    "product_name": "string",
    "one_line_description": "string — single sentence",
    "product_identity": "string — 1-2 paragraphs",
    "core_value_proposition": "string"
  },
  "target_user_and_market": {
    "personas": [
      {
        "name": "string — e.g., Freelance Designer",
        "description": "string — who this person is",
        "pain_points": ["string"],
        "goals": ["string"]
      }
    ],
    "market_context": "string",
    "competitive_landscape": [
      { "name": "string — competitor name", "differentiator": "string — how this product differs" }
    ]
  },
  "feasibility_assessment": {
    "viability_summary": "string",
    "risks": [
      { "risk": "string", "severity": "low | medium | high", "mitigation": "string" }
    ]
  },
  "problem_statement": "string — user-centric pain statement",
  "ambiguity_resolutions": [
    { "ambiguity": "string", "resolution": "string", "source": "string — what info drove the resolution" }
  ],
  "drift_anchor": "string — 2-4 sentence canonical product description"
}
```

Written to `context_packet.metadata`:

```json
{
  "current_stage": 3,
  "confidence_scores": {
    "3": {
      "score": 92,
      "dimensions": {
        "completeness": 19,
        "accuracy": 18,
        "consistency": 19,
        "specificity": 18,
        "handoff_readiness": 18
      },
      "gate_result": "pass | flag | fail"
    }
  },
  "stage_timestamps": { "3": "ISO 8601 timestamp" }
}
```

**Validation before writing:**
1. All four sections populated with 50+ words each
2. `drift_anchor` is 2-4 sentences
3. `ambiguity_resolutions` logged for every resolved ambiguity
4. No fields are null or empty where required
5. Confidence score computed and gate_result set
6. `product_name` is not empty or generic ("My App")
7. At least 1 persona in `personas` array with all required sub-fields

## Edge Cases

### Missing Input
- **`combined_raw` missing or empty**: Trigger escape hatch immediately. Stage 2 must have failed.
- **`combined_raw` under 20 words**: Trigger escape hatch — insufficient material to structure.
- **`explicit_corrections` missing**: Proceed normally — field is optional.
- **`archetype_matches` missing**: Proceed but note reduced framing context in confidence scoring.

### Ambiguous Input
- **Unresolvable contradictions** (user said two conflicting things, no later correction): Log in `ambiguity_resolutions` with `source: "unresolvable — needs human input: [specific question]"`. If more than 3 unresolvable ambiguities exist AND they affect core identity (product name, target user, or primary problem), trigger escape hatch.
- **Vague product description** (cannot determine even the product name): Trigger escape hatch with suggested question: "What is the core thing you are building?"
- **Multiple products described** (user described 2+ distinct apps): Structure the PRIMARY product (most detail). Log the secondary as an ambiguity: "Input describes multiple products. Structured [X]; deferred [Y]."

### Scope Overflow
- **Discovering mechanism-level details**: If you find yourself listing discrete moving parts (auth system, payment flow, notification engine) and classifying them — STOP. You have crossed into Stage 4. Mention features in context but do not decompose them.
- **Technical implementation details surfacing**: Do not include architecture, database schemas, API designs, or technology choices. These belong to later stages.
- **User asks to break into features**: Decline: "This stage structures the concept. Feature extraction happens in the next stage."

## Confidence Scoring

Score each dimension 0-20 after producing output:

**1. Completeness (0-20):** All four sections populated with 50+ words? Every piece of `combined_raw` represented? All Stage 2 mechanisms referenced?
- 0-5: 2+ sections empty or placeholder
- 6-10: All sections exist but 1-2 under 50 words
- 11-15: All sections substantive; minor raw material gaps
- 16-20: Thorough; every concept from `combined_raw` represented

**2. Accuracy (0-20):** Faithfully represents user's idea? No invented features? No assumptions beyond what was stated?
- 0-5: Describes a different app than user intended
- 6-10: Core idea captured but details embellished
- 11-15: Faithful representation; no invented features
- 16-20: Precise structuring with clear sourcing; nothing added, nothing lost

**3. Consistency (0-20):** Sections align with each other? Problem matches personas? Risks align with market? Ambiguities resolved consistently?
- 0-5: Sections contradict each other
- 6-10: Minor inconsistencies between sections
- 11-15: Consistent; ambiguity resolutions documented
- 16-20: Perfect alignment; thorough ambiguity log

**4. Specificity (0-20):** Precise enough that two readers draw the same conclusions? Personas concrete? Value proposition specific?
- 0-5: Vague generalizations ("helps people")
- 6-10: References the app but broad language
- 11-15: Names specific users, features, value props
- 16-20: Two readers would identify the same product, users, and problem

**5. Handoff Readiness (0-20):** Could Stage 4 extract every mechanism without ambiguity? Overlapping concepts resolved? Feature boundaries clear?
- 0-5: Stage 4 would ask "what is this app?"
- 6-10: Some mechanisms identifiable, others unclear
- 11-15: Clean extraction possible; 1-2 edge cases
- 16-20: Every mechanism extractable without ambiguity

**Total = sum of all 5 (/100)**

| Score | Gate | Action |
|-------|------|--------|
| >= 90 | `"pass"` | Proceed to Stage 4 |
| 70-89 | `"flag"` | Proceed with warning; flag low dimensions |
| < 70 | `"fail"` | Trigger escape hatch |

## Escape Hatch

**Trigger when:**
- `combined_raw` missing, empty, or under 20 words
- Product name cannot be determined from the raw material
- More than 3 unresolvable ambiguities affecting core identity
- Confidence score < 70 after one revision attempt

**Save:**
- Current `context_packet` with partial output
- Stage number (3), step where halt occurred, what failed

**Signal:**
- Set `metadata.status = "needs_human"`
- Append to `metadata.escape_hatches[]`:

```json
{
  "stage": 3,
  "step": "string — step that failed",
  "reason": "string — specific reason",
  "suggested_questions": ["string — specific questions for the human"],
  "partial_output": {}
}
```

- Save context_packet snapshot. Output structured NEEDS_HUMAN message.

## Example

**Input** (abbreviated): `combined_raw` describes a task manager for developer teams with projects, tasks, kanban board, list view, email/Google/GitHub auth, notifications, team workspaces, dark mode, dashboard with charts. Archetype: CRUD/Tool + SaaS. Platform: Next.js + Supabase.

**Output** (abbreviated — full example in `references/example-output.json`):

```json
{
  "concept_and_context": {
    "product_name": "TaskFlow",
    "one_line_description": "A clean, developer-focused task manager with kanban boards, team workspaces, and real-time notifications.",
    "product_identity": "TaskFlow is a project management tool designed specifically for developer teams who want Todoist-level simplicity without the clutter of enterprise tools like Jira. It organizes work into projects with tasks that have priorities, due dates, and assignees, displayed through kanban boards and sortable list views. Teams operate within shared workspaces with member invitations and role-based access.",
    "core_value_proposition": "Developer teams get a focused, uncluttered task management experience with the kanban and notification features they need, without the complexity of enterprise project management tools."
  },
  "target_user_and_market": {
    "personas": [
      {
        "name": "Small Dev Team Lead",
        "description": "Leads a 3-10 person development team, needs visibility into task status without micromanaging",
        "pain_points": ["Jira is too complex for small teams", "Todoist lacks team features", "No single tool handles kanban + assignments + notifications"],
        "goals": ["See team progress at a glance", "Assign and track tasks without overhead", "Keep the team aligned on priorities"]
      }
    ],
    "market_context": "The task management space is crowded but developer-specific tools that balance simplicity with team features are underserved. Jira dominates enterprise; Todoist dominates personal. The gap is small-team developer workflows.",
    "competitive_landscape": [
      { "name": "Todoist", "differentiator": "TaskFlow adds team workspaces, kanban boards, and developer-specific auth (GitHub)" },
      { "name": "Jira", "differentiator": "TaskFlow is radically simpler — no sprints, no epics, no configuration overhead" }
    ]
  },
  "feasibility_assessment": {
    "viability_summary": "Highly feasible. All components (kanban, tasks, auth, notifications) are well-understood patterns with existing libraries. Supabase handles auth and real-time out of the box. Primary risk is differentiation in a crowded market.",
    "risks": [
      { "risk": "Crowded market with established competitors", "severity": "medium", "mitigation": "Laser focus on developer teams; GitHub auth and clean UX as differentiators" }
    ]
  },
  "problem_statement": "Developer teams working on small-to-medium projects are stuck choosing between personal task apps that lack team features and enterprise tools that drown small teams in configuration and complexity. They need a way to organize, assign, and track work across their team without the overhead.",
  "ambiguity_resolutions": [
    { "ambiguity": "Auth methods: user first said 'Google' then corrected to 'not just Google — also GitHub'", "resolution": "Both Google and GitHub OAuth supported alongside email/password", "source": "Explicit correction in raw_input" }
  ],
  "drift_anchor": "TaskFlow is a task management tool for small developer teams. It provides kanban boards, task assignments with priorities and due dates, team workspaces, and real-time notifications — all with a clean, uncluttered interface. It is simpler than Jira but more team-capable than Todoist."
}
```


---

## REFERENCE: agent-os-framework

# Agent OS Framework — Five Lenses

> Origin: 15-year software veteran's framework that cut build time from 1.5 days to 0.5 days with fewer bugs.
> Function: Guardrailing system that adds walls and doors to keep agents centered on concept and context.

## The Five Lenses

Every raw idea is processed through five questions. Together they produce the four output sections.

### Lens 1: What Is the Product?

- **Name it.** Use whatever the user called it, or derive from the core concept.
- **Define it in one sentence.** A stranger reads this sentence and knows what it does.
- **Describe its identity.** 1-2 paragraphs covering what it is, how it presents itself, what makes it distinctive.

→ Maps to: `concept_and_context.product_name`, `one_line_description`, `product_identity`

### Lens 2: What Is It Solving?

- **Identify the pain.** What frustration, inefficiency, or gap does the user experience?
- **State it from the user's perspective.** Not "the system will..." but "users currently struggle with..."
- **Be specific.** Not "it helps people" but "freelance designers waste 3 hours per week manually tracking invoices."

→ Maps to: `problem_statement`

### Lens 3: Market Feasibility

- **Is this viable?** Does the market exist? Are people paying for solutions in this space?
- **What exists already?** Name competitors. Be specific.
- **What are the risks?** Technical, market, adoption risks with severity levels.
- **How does this product differ?** What's the actual differentiator — not aspirational, but real.

→ Maps to: `feasibility_assessment`, `target_user_and_market.competitive_landscape`

### Lens 4: Who Is It For?

- **Define specific personas.** Not "users" — specific types of people.
- **What are their pain points?** Real frustrations they experience.
- **What are their goals?** What they want to achieve (related to the product domain).
- **What is the market context?** Landscape, timing, trends.

→ Maps to: `target_user_and_market.personas`, `market_context`

### Lens 5: What Exists Already?

- **Name competitors.** Real products, not categories.
- **State differentiators.** For each competitor, how does THIS product differ?
- **Identify the gap.** What's the underserved niche?

→ Maps to: `target_user_and_market.competitive_landscape`

## Lens-to-Section Mapping

| Lens | Output Section |
|------|---------------|
| 1 (What is it?) | `concept_and_context` |
| 2 (What's it solving?) | `problem_statement` |
| 3 (Feasibility) | `feasibility_assessment` + `competitive_landscape` |
| 4 (Who's it for?) | `target_user_and_market` |
| 5 (What exists?) | `competitive_landscape` (overlaps with Lens 3) |

## Critical Boundaries

- **No "how":** The five lenses produce "what" and "why" only. Architecture, databases, APIs, implementation details are deferred.
- **No mechanism extraction:** Features may be mentioned in context but not decomposed into discrete units.
- **No invention:** The lenses organize what the user said. They do not add features, assumptions, or embellishments.
- **Persistent output:** The structured document serves as a drift anchor — agents reference it throughout the entire build.


---

## REFERENCE: ambiguity-resolution-rules

# Ambiguity Resolution Rules

> Stage 3 must resolve or flag every ambiguity before passing output to Stage 4.
> Unresolved ambiguity causes downstream mechanism extraction to split or miss concepts.

## Rule 1: Later Statements Override Earlier Ones

If the user said something, then later contradicted it, the LATER statement wins.

**Example:**
- Early: "This is for enterprise teams"
- Later: "Actually, I'm targeting freelancers"
- Resolution: Target user is freelancers

**Log as:**
```json
{
  "ambiguity": "Target user: 'enterprise teams' vs 'freelancers'",
  "resolution": "Freelancers — later statement overrides earlier",
  "source": "Chronological ordering in combined_raw"
}
```

## Rule 2: Explicit Corrections Always Win

Entries in `stage_1.explicit_corrections` are pre-identified contradictions. Always apply the corrected version.

**Log as:**
```json
{
  "ambiguity": "[original statement]",
  "resolution": "[corrected statement]",
  "source": "Explicit correction from Stage 1"
}
```

## Rule 3: Merge Duplicate Concepts

If the user described the same feature two different ways, unify them into one description that captures both phrasings.

**Example:**
- "Users can drag tasks between columns" AND "There's a board where you move items through stages"
- Resolution: One concept — kanban board with drag-and-drop task movement

**Log as:**
```json
{
  "ambiguity": "Two descriptions of the same feature: drag-between-columns and board-with-stages",
  "resolution": "Unified as kanban board with drag-and-drop task movement between status columns",
  "source": "Both descriptions reference the same UI pattern"
}
```

## Rule 4: Separate Bundled Concepts

If the user lumped two distinct things together, acknowledge both but keep them logically separate in the structured output.

**Example:**
- "I want a dashboard with charts and also a way to export reports"
- These are two separate concepts: dashboard visualization and report export

**Do NOT merge them. Do NOT decompose them into mechanisms (that's Stage 4). Mention both in the relevant section as related but distinct capabilities.**

## Rule 5: Unresolvable Ambiguities

If an ambiguity CANNOT be resolved from available information:

1. Do NOT guess
2. Log it with a specific question for the human
3. Use the most conservative interpretation for structuring

**Log as:**
```json
{
  "ambiguity": "User mentions both B2B and B2C use cases with equal emphasis",
  "resolution": "Cannot resolve — both appear equally intended. Structured with B2B as primary based on team features, but this needs confirmation.",
  "source": "unresolvable — needs human input: Is your primary market B2B (teams/companies) or B2C (individual users)?"
}
```

**Threshold:** If more than 3 unresolvable ambiguities affect core identity (product name, target user, or primary problem), trigger the escape hatch.

## Rule 6: Gap Answers Override Raw Input

If a gap question in Stage 2 asked about something vague in the raw input, and the user gave a specific answer, the gap answer is authoritative.

**Example:**
- Raw: "Some kind of login"
- Gap answer: "Email/password and Google OAuth"
- Resolution: Auth is email/password + Google OAuth

## Priority Order

When rules conflict:
1. Explicit corrections (Rule 2) — highest priority
2. Gap answers (Rule 6)
3. Later statements (Rule 1)
4. Merge duplicates (Rule 3)
5. Separate bundles (Rule 4)
6. Flag unresolvable (Rule 5) — last resort


---

## REFERENCE: example-output

{
  "stage_3": {
    "concept_and_context": {
      "product_name": "TaskFlow",
      "one_line_description": "A clean, developer-focused task manager with kanban boards, team workspaces, and real-time notifications.",
      "product_identity": "TaskFlow is a project management tool designed specifically for developer teams who want Todoist-level simplicity without the clutter of enterprise tools like Jira. It organizes work into projects containing tasks with priorities (high/medium/low), due dates, and assignees. Work is visualized through both kanban boards with drag-and-drop between status columns (To Do, In Progress, Done) and sortable list views ordered by due date. Teams operate within shared workspaces where they can invite members and manage access. The interface is clean, modern, and uncluttered, with dark mode support. A simple dashboard provides at-a-glance progress visibility through charts showing completed vs. pending task ratios.",
      "core_value_proposition": "Developer teams get a focused, uncluttered task management experience with the kanban boards, task assignments, and notification features they need — without the sprint planning, epic hierarchies, and configuration overhead of enterprise project management tools."
    },
    "target_user_and_market": {
      "personas": [
        {
          "name": "Small Dev Team Lead",
          "description": "Leads a 3-10 person development team at a startup or small company. Makes tooling decisions for the team. Values simplicity and low configuration overhead.",
          "pain_points": [
            "Jira requires hours of configuration and training before the team can use it",
            "Personal task apps like Todoist lack team features — no shared workspaces or assignment",
            "No single tool handles kanban, assignments, and notifications without bloat",
            "Switching between multiple tools fragments the team's workflow"
          ],
          "goals": [
            "See the team's progress at a glance without running reports",
            "Assign and track tasks with minimal process overhead",
            "Keep the team aligned on priorities without daily standups for status updates",
            "Onboard new team members to the tool in under 5 minutes"
          ]
        },
        {
          "name": "Individual Developer on the Team",
          "description": "A developer who receives task assignments and needs to manage their own workload within the team context. Uses the tool daily.",
          "pain_points": [
            "Gets assigned tasks through Slack messages that get buried",
            "Loses track of due dates across multiple projects",
            "Has to check multiple places to find what they should work on next"
          ],
          "goals": [
            "See all assigned tasks in one place with clear priorities",
            "Get notified when assigned new tasks or when deadlines approach",
            "Quickly update task status without navigating complex interfaces"
          ]
        }
      ],
      "market_context": "The task management market is crowded at the extremes — enterprise tools (Jira, Asana, Monday.com) dominate large teams while personal productivity apps (Todoist, Notion, Things) serve individuals. The gap is small-to-medium developer teams (3-15 people) who need team features without enterprise complexity. Developer-specific affordances like GitHub OAuth and clean, distraction-free interfaces serve this niche. The trend toward remote development teams increases demand for lightweight async coordination tools.",
      "competitive_landscape": [
        {
          "name": "Todoist",
          "differentiator": "TaskFlow adds team workspaces, shared kanban boards, task assignment, and developer-specific auth (GitHub OAuth) — features Todoist lacks for team workflows"
        },
        {
          "name": "Jira",
          "differentiator": "TaskFlow is radically simpler — no sprints, no epics, no story points, no configuration wizards. A team can start using it in minutes, not days"
        },
        {
          "name": "Linear",
          "differentiator": "TaskFlow targets a broader developer workflow (general task management) rather than Linear's focus on issue tracking and engineering cycle management"
        }
      ]
    },
    "feasibility_assessment": {
      "viability_summary": "Highly feasible. All core components — kanban boards, task CRUD, authentication, real-time notifications, team workspaces — are well-understood patterns with mature libraries and frameworks. The chosen stack (Next.js + Supabase) natively supports auth (email, Google, GitHub), real-time subscriptions (for notifications and live board updates), and row-level security (for team isolation). No novel technical challenges. Primary risk is market differentiation, not technical execution.",
      "risks": [
        {
          "risk": "Crowded market with well-funded established competitors (Todoist, Linear, Asana)",
          "severity": "medium",
          "mitigation": "Laser focus on the small dev team niche. GitHub auth, clean UX, zero-config setup as differentiators. Avoid feature creep into enterprise territory."
        },
        {
          "risk": "Scope creep toward enterprise features (sprints, epics, time tracking) based on user requests",
          "severity": "low",
          "mitigation": "The drift anchor explicitly defines TaskFlow as simpler-than-Jira. Any feature addition must pass the simplicity test."
        }
      ]
    },
    "problem_statement": "Developer teams working on small-to-medium projects are stuck choosing between personal task apps that lack team features (no shared workspaces, no assignments, no team notifications) and enterprise tools that drown small teams in configuration complexity, mandatory process overhead, and features they will never use. They need a way to organize, assign, and track work across their team — seeing who is working on what, when things are due, and what is blocked — without spending hours setting up the tool or training the team to use it.",
    "ambiguity_resolutions": [
      {
        "ambiguity": "Auth methods: user initially said 'email or Google' then corrected to 'not just Google — also GitHub login since this is for developer teams'",
        "resolution": "Three auth methods supported: email/password, Google OAuth, and GitHub OAuth",
        "source": "Explicit correction in raw_input — later statement adds GitHub, does not remove Google"
      },
      {
        "ambiguity": "Notification channels: user said 'Maybe email and in-app notifications' — the word 'maybe' introduces uncertainty",
        "resolution": "Both email and in-app notifications are included. 'Maybe' was used as a speech filler introducing the list, not expressing doubt — the user then specified both channels concretely.",
        "source": "Contextual interpretation of 'maybe' as conversational hedge, not conditional"
      },
      {
        "ambiguity": "Dashboard scope: user said 'maybe a chart' — unclear if dashboard is a core feature or nice-to-have",
        "resolution": "Dashboard with task completion charts is included as a feature. The user described it as part of the core concept ('there should be a simple dashboard showing how many tasks are done vs pending').",
        "source": "User's phrasing 'there should be' indicates intent, despite 'maybe a chart' hedging on chart specifics"
      }
    ],
    "drift_anchor": "TaskFlow is a task management tool for small developer teams. It provides kanban boards, task assignments with priorities and due dates, team workspaces with member invitations, and real-time notifications — all with a clean, uncluttered interface. It is simpler than Jira but more team-capable than Todoist, targeting the underserved gap between personal productivity apps and enterprise project management tools."
  },
  "metadata": {
    "current_stage": 3,
    "confidence_scores": {
      "3": {
        "score": 92,
        "dimensions": {
          "completeness": 19,
          "accuracy": 18,
          "consistency": 19,
          "specificity": 18,
          "handoff_readiness": 18
        },
        "gate_result": "pass"
      }
    },
    "stage_timestamps": {
      "3": "2026-04-03T14:30:00Z"
    }
  }
}


---

## 🔗 Pipeline Integration — Automatic Stage Advancement

**This section is added for pipeline automation. It tells you how to signal stage completion.**

After completing ALL steps above and producing your complete output:

### Stage Completion Protocol

1. **Verify your confidence score** meets the gate threshold (≥ 70)
2. **Verify the complete JSON output** has been produced and meets the contract
3. **Output the completion marker** on its own line as the ABSOLUTE LAST thing in your response:

```
[STAGE_COMPLETE]
```

### Rules for the completion marker:

- `[STAGE_COMPLETE]` MUST be the absolute last thing in your response — nothing after it
- Your complete JSON output (context_packet) MUST come BEFORE the marker
- **Never** output `[STAGE_COMPLETE]` until the stage contract is fully met
- **Never** output `[STAGE_COMPLETE]` if the confidence score is below 70
- If you need to ask the user questions, do **NOT** output `[STAGE_COMPLETE]` — wait for answers first, produce your final output, THEN output the marker
- If the gate_result is "fail" (score < 70), trigger the escape hatch protocol instead — do NOT output `[STAGE_COMPLETE]`

### What happens when you output [STAGE_COMPLETE]:

1. The pipeline captures everything before the marker as your stage output
2. Your output becomes the input for the next stage
3. The next stage starts automatically — no manual intervention needed

### Example — end of your response:

```json
{
  "stage_3": { ... your complete output ... },
  "metadata": {
    "confidence_scores": {
      "3": { "score": 93, "gate_result": "pass" }
    }
  }
}
```

[STAGE_COMPLETE]


================================================================================
STAGE 4: MECHANISM EXTRACTION
================================================================================

---
name: stage-04-mechanism-extraction
description: Break structured concept into tagged mechanisms with evaluations, dependencies, and core mechanism ID.
---

## Purpose

Decompose the Stage 3 structured concept document into every discrete functional mechanism. Tag each as OBVIOUS or NEEDS_EVALUATION, run 10-step criteria evaluation on NEEDS_EVALUATION mechanisms, apply Developer's Choice routing and the 15% dual-design rule, identify the core mechanism, and map all dependencies as a DAG.

## When to Use

Activate when: `context_packet.stage_3.concept_and_context` exists AND `context_packet.stage_3.drift_anchor` exists (Stage 3 is complete). Trigger phrases: "mechanism extraction", "break into mechanisms", "identify moving parts", "extract features", "what are the parts".

Do NOT activate for: gap analysis (Stage 2), structuring/organizing ideas (Stage 3), scaffolding walls/doors/rooms (Stage 5), or any request to define HOW a mechanism works internally.

## Input Format

```json
{
  "stage_0": {
    "platform_profile": {
      "boilerplate_id": "string", "boilerplate_name": "string",
      "supported_mechanisms": ["string"]
    }
  },
  "stage_2": {
    "mechanisms_identified": [
      { "category_id": "A", "category_name": "string", "sub_types": ["string"] }
    ],
    "mechanisms_gaps": [
      { "category_id": "L", "resolution": "not_needed | asked | developers_choice" }
    ],
    "scope_contract": "string"
  },
  "stage_3": {
    "concept_and_context": { "name": "string", "description": "string", "identity_paragraph": "string", "core_value_proposition": "string" },
    "target_user_and_market": { "primary_persona": {}, "market_context": "string" },
    "problem_statement": "string",
    "drift_anchor": "string",
    "feasibility_assessment": {}
  },
  "metadata": { "current_stage": 3 }
}
```

## Process

### Step 1: Read and Internalize the Concept

Read all Stage 3 sections: `concept_and_context`, `target_user_and_market`, `feasibility_assessment`, `problem_statement`, and `drift_anchor`. Do NOT extract until you can answer: What is this product? Who is it for? What is the core value proposition? What problem does it solve?

### Step 2: Enumerate Every Discrete Mechanism

Scan the concept document for every distinct functional unit. A mechanism is a **functional unit with its own internal logic, its own inputs/outputs, and its own implementation decisions**.

**Sizing rules:**
- Too small: a single button, field, or CSS class → merge up
- Too big: "the whole dashboard" with multiple independent areas → split down
- Right-sized: auth system, payment flow, video engine, template library, notification engine

Cross-reference `stage_2.mechanisms_identified` (A-N categories) to ensure nothing is missed. For each mechanism:
1. Assign a unique ID: `mech_001`, `mech_002`, ...
2. Name it descriptively (e.g., "Auth System", "Payment Flow")
3. Write a 2-5 sentence description of what it does
4. Map to one or more A-N category IDs
5. **Scope check**: Is it within `scope_contract`? Does it relate to `drift_anchor`? If outside scope and potentially critical, flag — do not silently include or exclude

### Step 3: Match Against Known Patterns

Before classifying, compare each mechanism to the known patterns library (see `references/known-patterns-library.md`). Standard patterns — auth, CRUD, dashboard, settings, admin, search, notifications — are likely OBVIOUS unless the app's version is genuinely novel.

Reference `stage_0.platform_profile.supported_mechanisms` to identify mechanisms the boilerplate handles natively. If the boilerplate covers it, it is OBVIOUS.

### Step 4: Classify Every Mechanism

Tag each mechanism:
- **OBVIOUS**: One clear implementation path. Standard pattern or natively handled by boilerplate. Set `chosen_approach` directly with name, description, and rationale. Set `evaluation: null`.
- **NEEDS_EVALUATION**: Multiple viable approaches exist. Must proceed to Step 5.

Every mechanism MUST receive a classification. No untagged mechanisms.

### Step 5: Evaluate NEEDS_EVALUATION Mechanisms

For each NEEDS_EVALUATION mechanism, identify 2-3 competing approaches. Score each approach 0-100 using the 10-step criteria (see `references/10-step-evaluation-criteria.md`):

1. Technical Complexity, 2. Scalability, 3. Maintainability, 4. Performance, 5. Security, 6. User Experience, 7. Cost, 8. Time to Implement, 9. Ecosystem Fit, 10. Future Flexibility.

For each approach, list concrete pros and cons. Record all criteria names in `evaluation.criteria`.

### Step 6: Apply Developer's Choice Routing

**Developer's Choice is the default (the "92% route").** When one approach scores highest with >15 points margin over the next-best, select it automatically as `chosen_approach`. No user decision needed.

### Step 7: Apply the 15% Threshold Rule

If two approaches score within 15 points of each other (on the 0-100 scale):
- Record the higher-scoring as `chosen_approach`
- Record the other as `alternate_approach` with `score_delta` = actual point difference
- Both get fully designed — both proceed to Stage 5 scaffolding

If the user has said "go with developer's choice on all of it", skip the 15% rule and always pick the top scorer.

### Step 8: Identify the Core Mechanism

Mark exactly ONE mechanism as `is_core_mechanism: true`. This is the mechanism that:
- Directly addresses `problem_statement`
- Embodies `core_value_proposition`
- If removed, the app has nothing to sell
- Gets built first in Phase Sequencing (Stage 7)

All other mechanisms get `is_core_mechanism: false`.

### Step 9: Map Dependencies

Identify dependencies between mechanisms:
- `"requires"`: mechanism B cannot function without A
- `"uses_output_of"`: mechanism B consumes data produced by A
- `"shares_data_with"`: bidirectional data relationship

Record each as `{ from_id, to_id, relationship }`. **Verify the graph is a DAG** — no circular dependencies. If a cycle is detected, restructure the involved mechanisms (split or merge) to break the cycle. If the cycle cannot be resolved, trigger escape hatch.

### Step 10: Validate and Count

Before writing output, verify:
1. `mechanism_count` >= 3
2. Every REQUIRED category from `stage_2.mechanisms_identified` has at least one mechanism
3. Exactly one mechanism has `is_core_mechanism: true`
4. All NEEDS_EVALUATION mechanisms have >= 2 approaches with scores
5. Dependency graph is acyclic
6. All required fields are populated on every mechanism
7. Count mechanisms with `alternate_approach` and set `dual_design_count`

If any check fails, attempt one fix. If still failing, trigger escape hatch.

## Output Format

Written to `context_packet.stage_4`:

```json
{
  "mechanisms": [
    {
      "id": "mech_001",
      "name": "string",
      "description": "string (2-5 sentences)",
      "category_ids": ["E", "F"],
      "classification": "OBVIOUS | NEEDS_EVALUATION",
      "is_core_mechanism": false,
      "chosen_approach": {
        "name": "string",
        "description": "string",
        "rationale": "string"
      },
      "alternate_approach": null,
      "evaluation": null
    },
    {
      "id": "mech_002",
      "name": "string",
      "description": "string",
      "category_ids": ["C", "G"],
      "classification": "NEEDS_EVALUATION",
      "is_core_mechanism": true,
      "chosen_approach": {
        "name": "string",
        "description": "string",
        "rationale": "string"
      },
      "alternate_approach": {
        "name": "string",
        "description": "string",
        "score_delta": 12
      },
      "evaluation": {
        "approaches": [
          {
            "name": "string",
            "score": 85,
            "pros": ["string"],
            "cons": ["string"]
          }
        ],
        "criteria": [
          "Technical Complexity", "Scalability", "Maintainability",
          "Performance", "Security", "User Experience", "Cost",
          "Time to Implement", "Ecosystem Fit", "Future Flexibility"
        ]
      }
    }
  ],
  "mechanism_dependencies": [
    { "from_id": "mech_002", "to_id": "mech_001", "relationship": "requires" }
  ],
  "mechanism_count": 8,
  "dual_design_count": 1
}
```

Written to `context_packet.metadata`:

```json
{
  "current_stage": 4,
  "confidence_scores": {
    "4": {
      "score": 92,
      "dimensions": {
        "completeness": 19, "accuracy": 18, "consistency": 19,
        "specificity": 18, "handoff_readiness": 18
      },
      "gate_result": "pass | flag | fail"
    }
  },
  "stage_timestamps": { "4": "ISO-8601" }
}
```

**Field types and constraints:**
- `mechanisms[].id`: string, unique, format `mech_NNN`
- `mechanisms[].classification`: enum `"OBVIOUS"` | `"NEEDS_EVALUATION"`
- `mechanisms[].is_core_mechanism`: boolean, exactly one `true` in array
- `mechanisms[].evaluation`: object if NEEDS_EVALUATION, `null` if OBVIOUS
- `mechanisms[].alternate_approach`: object if 15% rule applies, `null` otherwise
- `mechanisms[].alternate_approach.score_delta`: number 0-15
- `mechanism_dependencies[].relationship`: enum `"requires"` | `"uses_output_of"` | `"shares_data_with"`
- `mechanism_count`: integer >= 3
- `dual_design_count`: integer >= 0

## Edge Cases

### Missing Input
- **`concept_and_context` missing or empty**: Trigger escape hatch immediately. Stage 3 must run first.
- **`drift_anchor` missing**: Proceed but disable scope-creep detection. Flag in confidence scoring (handoff_readiness -5).
- **`mechanisms_identified` missing**: Proceed without A-N cross-reference. Flag completeness dimension.

### Ambiguous Input
- **Mechanism too vague to classify**: If the concept description does not provide enough detail to determine OBVIOUS vs NEEDS_EVALUATION, default to NEEDS_EVALUATION and note in the description that the mechanism needs more detail from the user.
- **Two features that might be one mechanism or two**: If they share >50% of their inputs/outputs and internal logic, merge. If they have distinct decision paths, split.

### Scope Overflow
- **Discovering HOW details**: If you start defining walls/doors/rooms or internal step sequences, STOP. That is Stage 5. Record only WHAT the mechanism does, not the internal workflow.
- **New feature discovered not in scope**: If a mechanism emerges that is outside `scope_contract` but appears critical, do NOT silently include. Flag it in a `scope_creep_flags` array and note it in escape hatch if confidence drops.

### All Mechanisms OBVIOUS
- Valid if the app uses entirely standard patterns on a mature boilerplate. Set `dual_design_count: 0` and note in confidence scoring.

### Fewer Than 3 Mechanisms
- Trigger escape hatch. The concept may be too abstract (Stage 3 needs revision) or too simple for this pipeline.

### Circular Dependencies
- Attempt to restructure: split the entangled mechanism into sub-mechanisms or merge two circular dependencies into one mechanism. If the cycle cannot be broken, trigger escape hatch.

## Confidence Scoring

Score each dimension 0-20 after producing output:

**1. Completeness (0-20):** All REQUIRED A-N categories represented? All mechanism fields populated? `mechanism_count` >= 3? Exactly one core mechanism? Dependency graph complete?
- 0-5: <3 mechanisms; REQUIRED categories missing; fields empty
- 6-10: 3+ mechanisms but 2+ REQUIRED categories unrepresented
- 11-15: All REQUIRED categories covered; all fields complete; 1-2 mechanisms may need splitting
- 16-20: All relevant categories covered; every mechanism properly sized; core identified; dependencies comprehensive

**2. Accuracy (0-20):** Every mechanism traces to concept document? No hallucinated mechanisms? Classifications defensible? Evaluation scores reflect real tradeoffs?
- 0-5: Mechanisms not in concept (hallucinated); classifications clearly wrong
- 6-10: Most match but 2-3 misidentified or misclassified
- 11-15: All match concept; classifications defensible; scores reasonable
- 16-20: Direct traceability; classifications obviously correct; evaluations reflect genuine engineering judgment

**3. Consistency (0-20):** No overlapping mechanisms? Dependency graph acyclic? Descriptions non-contradictory? Category mappings correct?
- 0-5: Same feature described twice; circular dependencies
- 6-10: Minor overlaps; mostly correct dependencies
- 11-15: No overlaps; valid DAG; consistent descriptions
- 16-20: Clean separation; comprehensive acyclic graph; each mechanism has unique non-overlapping scope

**4. Specificity (0-20):** Descriptions precise enough for Stage 5? Approach descriptions concrete?
- 0-5: Vague ("handles user stuff"); no clear boundaries
- 6-10: Names feature area but lacks I/O detail
- 11-15: Explains what it does, inputs, outputs, decisions involved
- 16-20: Stage 5 can immediately apply 7 questions without asking "what does this mechanism do?"

**5. Handoff Readiness (0-20):** Stage 5 can scaffold every mechanism? `chosen_approach` set for all? Dual-design mechanisms fully specified? Dependencies clear for Stage 7?
- 0-5: Stage 5 would ask "what are the mechanisms?"
- 6-10: Most scaffoldable but 2-3 too vague
- 11-15: All scaffoldable; 1-2 need minor clarification
- 16-20: Every mechanism immediately ready for 7-question framework

**Total = sum (/100)**

| Score | Gate | Action |
|-------|------|--------|
| >= 90 | `"pass"` | Proceed to Stage 5 |
| 70-89 | `"flag"` | Proceed with warning; flag low dimensions |
| < 70 | `"fail"` | Trigger escape hatch |

## Escape Hatch

**Trigger when:**
- `concept_and_context` is missing or empty
- Fewer than 3 mechanisms identifiable after examining all context
- Circular dependencies that cannot be resolved by restructuring
- A mechanism is outside scope but appears critical — cannot decide without human input
- Confidence score < 70 after one retry

**Save:**
- Current `context_packet` with partial mechanism list
- Stage number (4) and step where halt occurred
- Which mechanisms were successfully extracted
- What was attempted and what failed
- Suggested questions for the human

**Signal:**
- Set `metadata.status = "needs_human"`
- Append to `metadata.escape_hatches[]`:

```json
{
  "stage": 4,
  "step": "string (e.g., mechanism_classification, dependency_validation)",
  "reason": "string",
  "suggested_questions": ["string"],
  "partial_output": {
    "mechanisms_extracted_so_far": [],
    "mechanisms_blocked": []
  }
}
```

- Save context_packet snapshot. Output structured NEEDS_HUMAN message.

## Example

**Input summary:** A task manager app (from Stage 3). Concept: "TaskFlow — Kanban + list-based task manager for developer teams with workspaces, assignments, notifications, and analytics dashboard." Platform: Next.js + Supabase. Stage 2 identified A,B,C,D,E,F,G,K as present; L,M as gaps (resolved via questions: freemium SaaS model, admin role).

**Extraction result** (abbreviated):

```json
{
  "mechanisms": [
    {
      "id": "mech_001", "name": "Auth System",
      "description": "User registration, login (email + OAuth via Google/GitHub), password reset, session management. Handles team invitations via email link.",
      "category_ids": ["E"],
      "classification": "OBVIOUS",
      "is_core_mechanism": false,
      "chosen_approach": { "name": "Supabase Auth", "description": "Built-in Supabase Auth with OAuth providers.", "rationale": "Native to boilerplate. Zero custom auth code." },
      "alternate_approach": null, "evaluation": null
    },
    {
      "id": "mech_002", "name": "Task Management Engine",
      "description": "Core CRUD for tasks: create, read, update, delete. Tasks have title, description, due date, priority (high/med/low), assignee, status (todo/in-progress/done). Supports kanban drag-drop and list view with sorting/filtering.",
      "category_ids": ["A", "B", "D"],
      "classification": "OBVIOUS",
      "is_core_mechanism": true,
      "chosen_approach": { "name": "Supabase CRUD + React DnD", "description": "Supabase tables with RLS + React DnD for kanban.", "rationale": "Standard CRUD pattern. Drag-drop is a UI concern, not a novel mechanism." },
      "alternate_approach": null, "evaluation": null
    },
    {
      "id": "mech_003", "name": "Notification Engine",
      "description": "In-app and email notifications for task assignments, due date reminders, and workspace activity. User-configurable preferences.",
      "category_ids": ["G"],
      "classification": "NEEDS_EVALUATION",
      "is_core_mechanism": false,
      "chosen_approach": { "name": "Supabase Edge Functions + Resend", "description": "Edge Functions trigger on DB events, send via Resend.", "rationale": "Scored highest: native to stack, low cost, simple." },
      "alternate_approach": { "name": "Dedicated Queue + Worker", "description": "BullMQ queue with Node worker for async processing.", "score_delta": 11 },
      "evaluation": {
        "approaches": [
          { "name": "Supabase Edge Functions + Resend", "score": 82, "pros": ["Native to stack", "Low cost", "Simple setup"], "cons": ["Limited retry logic", "Cold start latency"] },
          { "name": "Dedicated Queue + Worker", "score": 71, "pros": ["Robust retry", "Scalable", "Full control"], "cons": ["Extra infrastructure", "More complex", "Higher cost"] }
        ],
        "criteria": ["Technical Complexity","Scalability","Maintainability","Performance","Security","User Experience","Cost","Time to Implement","Ecosystem Fit","Future Flexibility"]
      }
    }
  ],
  "mechanism_dependencies": [
    { "from_id": "mech_002", "to_id": "mech_001", "relationship": "requires" },
    { "from_id": "mech_003", "to_id": "mech_001", "relationship": "requires" },
    { "from_id": "mech_003", "to_id": "mech_002", "relationship": "uses_output_of" }
  ],
  "mechanism_count": 3,
  "dual_design_count": 1
}
```

Confidence: Completeness 18, Accuracy 18, Consistency 19, Specificity 17, Handoff Readiness 18 = **90. Gate: pass.**


---

## REFERENCE: 10-step-evaluation-criteria

# 10-Step Criteria Evaluation for NEEDS_EVALUATION Mechanisms

When a mechanism has multiple viable implementation approaches, score each approach 0-100 using these 10 criteria. Each criterion is worth 0-10 points. Sum all 10 for the total score.

---

## Criteria

### 1. Technical Complexity (0-10)
How hard is this approach to implement correctly?
- 0-3: Requires deep expertise, novel algorithms, or cutting-edge tech
- 4-6: Moderate complexity, well-documented but requires careful implementation
- 7-10: Straightforward, well-trodden path, ample examples and libraries

**Score HIGH for simpler approaches** (less complexity = better).

### 2. Scalability (0-10)
How well does this approach handle growth (10x users, 100x data)?
- 0-3: Will hit walls at moderate scale, requires rearchitecture
- 4-6: Scales with known effort (add caching, indexes, workers)
- 7-10: Scales naturally, horizontally, or has proven track record at scale

### 3. Maintainability (0-10)
How easy is this to maintain, debug, and modify over time?
- 0-3: Complex internals, poor observability, tightly coupled
- 4-6: Standard patterns but some hidden complexity
- 7-10: Clean separation, good logging, easy to understand and modify

### 4. Performance (0-10)
What are the latency, throughput, and resource characteristics?
- 0-3: Slow, resource-heavy, or creates bottlenecks
- 4-6: Acceptable performance with optimization
- 7-10: Fast, efficient, minimal resource usage

### 5. Security (0-10)
What are the security implications and attack surface?
- 0-3: Large attack surface, requires significant security hardening
- 4-6: Standard security concerns, handled by following best practices
- 7-10: Minimal attack surface, security built into the approach

### 6. User Experience (0-10)
How does this approach affect what the end user sees and feels?
- 0-3: Visible UX compromises (loading delays, limited features, workarounds)
- 4-6: Acceptable UX with minor tradeoffs
- 7-10: Seamless UX, no compromises visible to the user

### 7. Cost (0-10)
What are the infrastructure, service, and operational costs?
- 0-3: Expensive ongoing costs, paid APIs, dedicated infrastructure
- 4-6: Moderate costs, scales linearly with usage
- 7-10: Low cost, free tier sufficient, or included in existing stack

### 8. Time to Implement (0-10)
How long does this approach take from start to production-ready?
- 0-3: Weeks of development, significant integration work
- 4-6: Days of focused work, some integration required
- 7-10: Hours to days, drop-in solution or minimal wiring

### 9. Ecosystem Fit (0-10)
How well does this approach integrate with the chosen stack?
- 0-3: Foreign to the stack, requires adapters, bridges, or workarounds
- 4-6: Compatible but not native, some glue code needed
- 7-10: Native to the stack, first-party support, idiomatic usage

### 10. Future Flexibility (0-10)
How well does this approach accommodate future changes?
- 0-3: Locked in, hard to swap, creates vendor/architectural lock-in
- 4-6: Changeable with moderate refactoring
- 7-10: Easy to swap, extend, or replace without cascading changes

---

## Scoring Process

1. For each NEEDS_EVALUATION mechanism, list 2-3 competing approaches
2. Score each approach on all 10 criteria (0-10 per criterion)
3. Sum for total (0-100)
4. List 2-4 concrete pros and 2-4 concrete cons per approach
5. Apply Developer's Choice: if top score has >15 point margin, auto-select
6. Apply 15% rule: if top two scores are within 15 points, design both

## Score Interpretation

| Total Score | Meaning |
|-------------|---------|
| 80-100 | Strong approach — high confidence |
| 60-79 | Viable approach — acceptable with known tradeoffs |
| 40-59 | Weak approach — significant concerns |
| 0-39 | Poor approach — should not be selected |

## Example

**Mechanism:** Notification Engine
**Approaches:** (A) Supabase Edge Functions + Resend, (B) BullMQ Queue + Worker

| Criterion | Approach A | Approach B |
|-----------|-----------|-----------|
| Technical Complexity | 8 | 5 |
| Scalability | 6 | 9 |
| Maintainability | 8 | 6 |
| Performance | 7 | 8 |
| Security | 8 | 7 |
| User Experience | 8 | 8 |
| Cost | 9 | 5 |
| Time to Implement | 9 | 5 |
| Ecosystem Fit | 9 | 6 |
| Future Flexibility | 6 | 7 |
| **Total** | **78** | **66** |

Delta = 12 points (within 15) → **Design both. Record alternate_approach with score_delta: 12.**


---

## REFERENCE: known-patterns-library

# Known Patterns Library

Standard patterns for quick OBVIOUS classification. If a mechanism matches one of these patterns AND the boilerplate/stack supports it natively, classify as OBVIOUS and use the standard approach.

---

## Auth System
**Pattern:** Registration, login, password reset, session management, OAuth providers.
**Standard approach:** Use the boilerplate's auth provider (Supabase Auth, NextAuth, Firebase Auth, Clerk).
**When NEEDS_EVALUATION:** Custom auth flows, unusual session requirements, multi-tenant SSO, or boilerplate has no built-in auth.

## CRUD Operations
**Pattern:** Create, read, update, delete for any entity. Forms, lists, detail views.
**Standard approach:** Database table + ORM + REST/GraphQL endpoints + standard UI components.
**When NEEDS_EVALUATION:** Complex validation rules, multi-step creation wizards, optimistic updates with conflict resolution, or real-time collaborative editing.

## Dashboard
**Pattern:** Sidebar navigation + main content area + summary widgets/cards + charts.
**Standard approach:** Layout component + widget grid + charting library (Recharts, Chart.js).
**When NEEDS_EVALUATION:** Real-time streaming data, customizable widget layouts, complex drill-down analytics, or AI-generated insights.

## Settings Page
**Pattern:** Key-value preferences, toggles, dropdowns. User profile, notification preferences, theme.
**Standard approach:** Form with save button, stored in user profile table or key-value store.
**When NEEDS_EVALUATION:** Almost never. This is OBVIOUS in virtually all cases.

## Admin Panel
**Pattern:** User management (view/edit/ban), content moderation, system config, analytics.
**Standard approach:** Protected routes + admin role check + CRUD views for system entities.
**When NEEDS_EVALUATION:** Multi-tenant admin with org-level permissions, complex moderation workflows, or feature flag management systems.

## Search
**Pattern:** Text search across entities, filters, sorting, pagination.
**Standard approach:** Database full-text search (PostgreSQL `tsvector`, SQLite FTS5) or search service (Algolia, Meilisearch).
**When NEEDS_EVALUATION:** Semantic/vector search, faceted search across multiple entity types, search with AI-powered ranking, or search at >1M documents.

## Notifications
**Pattern:** In-app notifications (bell icon), email notifications, push notifications.
**Standard approach:** Database notification table + email service (Resend, SendGrid) + in-app polling or WebSocket.
**When NEEDS_EVALUATION:** Complex notification routing (different channels per event type), digest/batching logic, real-time push at scale, or notification preferences with granular controls.

## File Upload
**Pattern:** Single/multi file upload, image preview, progress bar, size/type validation.
**Standard approach:** Presigned URLs to S3/Supabase Storage + client-side validation + progress tracking.
**When NEEDS_EVALUATION:** Large file processing (video transcoding, PDF parsing), collaborative file editing, or complex file pipeline (upload → process → store → serve).

## Payment / Billing
**Pattern:** One-time payments, subscriptions, plan management, invoices.
**Standard approach:** Stripe integration with Checkout or Elements. Webhook for fulfillment.
**When NEEDS_EVALUATION:** Multiple payment processors, marketplace payments (split payouts), usage-based/metered billing, or cryptocurrency payments.

## Email System
**Pattern:** Transactional emails (welcome, reset, receipt), marketing emails, templates.
**Standard approach:** Email service (Resend, SendGrid, SES) + HTML templates.
**When NEEDS_EVALUATION:** Complex template engine, email builder UI, bulk sending with deliverability optimization, or multi-language email support.

## Credit / Token System
**Pattern:** Balance tracking, deduction on action, purchase/top-up, usage history.
**Standard approach:** Integer balance column + atomic decrement + purchase via Stripe + transaction log table.
**When NEEDS_EVALUATION:** Complex pricing tiers, expiring credits, shared team pools, or credits across multiple resource types with different costs.

## API / Integration Layer
**Pattern:** REST/GraphQL API for external consumers, webhook endpoints, third-party API consumption.
**Standard approach:** Standard API routes + API key auth + rate limiting middleware.
**When NEEDS_EVALUATION:** Multiple external APIs with fallback logic, complex data sync, real-time webhooks at scale, or building a public API platform.

---

## Decision Rule

1. Does the mechanism match a pattern above? → Likely OBVIOUS
2. Does the boilerplate handle it natively? → Definitely OBVIOUS
3. Does the "When NEEDS_EVALUATION" condition apply? → NEEDS_EVALUATION
4. Is the mechanism genuinely novel (no pattern match)? → NEEDS_EVALUATION


---

## REFERENCE: mechanism-categories-summary

# A-N Mechanism Categories — Quick Reference

Condensed from the Mechanism Identification Framework. Use for cross-referencing during extraction.

| ID | Category | What It Covers | Common Sub-types |
|----|----------|---------------|-----------------|
| A | Data Input | How data enters the system | Forms, file upload, voice/audio, camera/OCR, drag-and-drop, sensors, import |
| B | Data Storage | How and where data persists | Relational DB, NoSQL, blob storage, cache, search index, audit trail |
| C | Data Processing | Transformations and logic applied to data | Validation, calculations, AI/ML, batch processing, format conversion, filtering |
| D | Data Output | How data is displayed or delivered | Lists/tables, charts, maps, timelines, kanban, export, print, real-time feeds |
| E | Authentication | How users prove identity | Email/password, OAuth, SSO, MFA, magic link, API keys, session management |
| F | Authorization | What users are allowed to do | RBAC, ABAC, resource ownership, multi-tenancy, feature flags, rate limiting |
| G | Communication | How system communicates | Email, push notifications, in-app notifications, SMS, chat, webhooks, activity feeds |
| H | Integration | Connections to external services | REST/GraphQL APIs, scraping, payment gateways, file sync, social media, email services |
| I | Workflow | Multi-step processes and automation | State machines, approval flows, cron jobs, queues, event triggers, wizards, retry/recovery |
| J | Search & Discovery | How users find things | Full-text search, faceted search, autocomplete, recommendations, tags, favorites, history |
| K | Collaboration | How users interact with each other | Comments, @mentions, sharing, co-editing, reactions, following, profiles |
| L | Monetization | How the app makes money | Subscriptions, one-time purchase, freemium, usage-based, marketplace, invoicing, refunds |
| M | Admin/Ops | Back-office management tools | Admin dashboard, user management, moderation, feature flags, analytics, configuration |
| N | Infrastructure | System-level support concerns | Caching, DB migrations, circuit breakers, auto-scaling, logging, monitoring, CI/CD |

## Cross-Reference Rules

1. Every REQUIRED category from `stage_2.mechanisms_identified` must have at least one mechanism extracted for it
2. Categories in `stage_2.mechanisms_gaps` with `resolution: "not_needed"` can be skipped
3. Categories with `resolution: "developers_choice"` should have a mechanism with OBVIOUS classification using the default approach
4. A single mechanism can map to multiple categories (e.g., an auth system maps to E and potentially F)
5. If a mechanism spans 4+ categories, consider whether it should be split into smaller mechanisms


---

## 🔗 Pipeline Integration — Automatic Stage Advancement

**This section is added for pipeline automation. It tells you how to signal stage completion.**

After completing ALL steps above and producing your complete output:

### Stage Completion Protocol

1. **Verify your confidence score** meets the gate threshold (≥ 70)
2. **Verify the complete JSON output** has been produced and meets the contract
3. **Output the completion marker** on its own line as the ABSOLUTE LAST thing in your response:

```
[STAGE_COMPLETE]
```

### Rules for the completion marker:

- `[STAGE_COMPLETE]` MUST be the absolute last thing in your response — nothing after it
- Your complete JSON output (context_packet) MUST come BEFORE the marker
- **Never** output `[STAGE_COMPLETE]` until the stage contract is fully met
- **Never** output `[STAGE_COMPLETE]` if the confidence score is below 70
- If you need to ask the user questions, do **NOT** output `[STAGE_COMPLETE]` — wait for answers first, produce your final output, THEN output the marker
- If the gate_result is "fail" (score < 70), trigger the escape hatch protocol instead — do NOT output `[STAGE_COMPLETE]`

### What happens when you output [STAGE_COMPLETE]:

1. The pipeline captures everything before the marker as your stage output
2. Your output becomes the input for the next stage
3. The next stage starts automatically — no manual intervention needed

### Example — end of your response:

```json
{
  "stage_4": { ... your complete output ... },
  "metadata": {
    "confidence_scores": {
      "4": { "score": 93, "gate_result": "pass" }
    }
  }
}
```

[STAGE_COMPLETE]


================================================================================
STAGE 5: SEVEN-QUESTION SCAFFOLDING
================================================================================

---
name: stage-05-seven-question-scaffolding
description: Classify mechanism steps as WALL/DOOR/ROOM via 7-question framework, producing per-mechanism blueprints with phases and verification methods.
---

## Purpose

Apply the 7-question deterministic framework to every mechanism from Stage 4, classifying each process step as WALL (code handles), DOOR (AI within strict boundaries), or ROOM (AI creative freedom). Produces architectural blueprints that prevent builder agents from improvising in unstructured spaces.

## When to Use

Trigger when: Stage 4 mechanism extraction is complete and `context_packet.stage_4.mechanisms` exists with at least one mechanism. The pipeline is ready for 7-question scaffolding, wall/door/room classification, or mechanism blueprint generation.

Do NOT trigger when: Mechanisms have not been extracted yet (Stage 4 incomplete), or when doing layout/wireframing (Stage 6) or protocol injection (Stage 8).

## Input Format

```json
{
  "stage_4": {
    "mechanisms": [{ "id": "mech_001", "name": "string", "description": "string",
      "classification": "OBVIOUS|NEEDS_EVALUATION", "chosen_approach": { "name": "string", "description": "string" },
      "alternate_approach": { "name": "string", "description": "string", "score_delta": 0 } | null }],
    "mechanism_dependencies": [{ "from_id": "string", "to_id": "string", "relationship": "string" }],
    "dual_design_count": 0
  },
  "stage_3": { "drift_anchor": "string" },
  "stage_2": { "scope_contract": "string" },
  "stage_0": { "checklist_rule_ids": ["string"] }
}
```

## Process

### Step 1: Validate Inputs and Scope

Read `stage_4.mechanisms`. If empty or missing, trigger escape hatch. For each mechanism, verify it falls within `stage_2.scope_contract` and is consistent with `stage_3.drift_anchor`. If a mechanism exceeds scope, add a `scope_flag` note but still scaffold it — scope enforcement is not this stage's job.

### Step 2: Map Each Mechanism as a Human Process

For each mechanism, walk through what a human would do step by step. Use the mechanism's `chosen_approach.description` as the starting point. Think: "I'm a practitioner running this process. What happens first? What happens next? What determines which direction I go?"

Group steps into **phases** — logical chunks with clear entry/exit boundaries. A phase change occurs when the process crosses a meaningful boundary (e.g., from data collection to data processing, from user input to validation).

### Step 3: Apply the 7 Questions to Every Step

For each step within each phase, answer all 7 questions. See [references/seven-questions-framework.md](references/seven-questions-framework.md) for the complete framework and classification rules.

**Decision flow:** Question 2 is the primary classifier. Questions 3-7 refine and verify. Use the decision tree in [references/classification-decision-tree.md](references/classification-decision-tree.md) for borderline cases.

### Step 4: Apply Martin's Rules as Lens

While scaffolding, apply structural principles from `stage_0.checklist_rule_ids` as the design lens. These rules SHAPE scaffolding answers — they are not injected later. See [references/checklist-lens-rules.md](references/checklist-lens-rules.md) for the key rules.

Specifically enforce:
- **Single responsibility:** Each step does exactly one thing
- **No state leakage:** Entry/exit conditions enforce phase isolation
- **Service layer access:** Data steps go through service layer (WALL), not direct DB calls
- **Boundary validation:** Every step has verification
- **Separation of concerns:** UI steps separate from data steps separate from logic steps

Record which rule IDs influenced decisions in `build_rules_applied`.

### Step 5: Chain Entry/Exit Conditions

Verify that for every blueprint:
- Phase N's exit condition matches Phase N+1's entry condition
- Cross-mechanism dependencies (from `stage_4.mechanism_dependencies`) are reflected in entry conditions — if mechanism B depends on mechanism A, B's first phase entry condition references A's completion
- No gaps exist in the chain

### Step 6: Handle Dual-Design Mechanisms

For mechanisms with `alternate_approach` (15% rule from Stage 4), produce TWO complete blueprints — one with `approach: "primary"`, one with `approach: "alternate"`. Both get full scaffolding through all 7 questions. Stage 5 does not pick winners.

### Step 7: Validate and Score

Run all validation checks (see Validation section below). Then run confidence scoring. Process mechanisms sequentially to avoid accumulating too much intermediate state — write each blueprint before moving to the next.

## Output Format

Written to `context_packet.stage_5`:

```json
{
  "mechanism_blueprints": [{
    "mechanism_id": "string (refs stage_4.mechanisms[].id)",
    "approach": "primary|alternate",
    "phases": [{
      "phase_label": "string",
      "entry_condition": "string",
      "exit_condition": "string",
      "validation_rules": ["string"],
      "steps": [{
        "id": "string (unique, e.g. mech_001_p1_s1)",
        "name": "string (Q1: what happens here)",
        "classification": "WALL|DOOR|ROOM",
        "preconditions": ["string (Q3)"],
        "outcomes": [{ "outcome": "string (Q4)", "next_step": "string (step ID or 'end') (Q5)" }],
        "verification": "string (Q6: machine-checkable for WALLs)",
        "skip_condition": "string|null (Q7: null if not skippable)"
      }]
    }]
  }],
  "build_rules_applied": ["string (Martin's rule IDs that shaped scaffolding)"]
}
```

**Field constraints:**
- `classification`: Exactly one of `"WALL"`, `"DOOR"`, `"ROOM"` — no other values
- `verification` for WALLs: Must be machine-checkable (file exists, function exports X, schema matches)
- `skip_condition`: `null` for WALLs (never skippable), string condition for DOORs/ROOMs if applicable
- `outcomes[].next_step`: Must reference a valid step ID within the same phase, or `"end"` for phase termination
- DOOR steps: `preconditions` must include the constraint boundaries the AI operates within
- Every mechanism from Stage 4 must have at least one blueprint
- Dual-design mechanisms must have exactly two blueprints

Also write to `context_packet.metadata`:
- `metadata.current_stage`: `5`
- `metadata.confidence_scores["5"]`: Confidence object with 5 dimensions
- `metadata.stage_timestamps["5"]`: ISO 8601 timestamp

## Edge Cases

### Missing Input
If `stage_4.mechanisms` is empty/missing: trigger escape hatch with `reason: "no_mechanisms"`. Save partial state. Signal `NEEDS_HUMAN` with message: "Stage 4 produced no mechanisms. Cannot scaffold without mechanisms."

### Ambiguous Input
If a mechanism description is too vague for meaningful 7-question answers: scaffold what you can, flag the mechanism with `scope_flag: "vague_description"` in the blueprint, and add a suggested question to the escape hatch: "Mechanism X's description is too vague. Describe the step-by-step process a human would follow."

### Borderline WALL/DOOR Classification
When a step could be either WALL or DOOR, default to WALL (more restrictive). A WALL that should be a DOOR is discovered during build and relaxed. A DOOR that should be a WALL lets AI improvise where it shouldn't. See [references/classification-decision-tree.md](references/classification-decision-tree.md).

### 100% ROOM Mechanisms
Valid — some mechanisms (e.g., "generate marketing copy") have no walls. Still ask all 7 questions to confirm. The blueprint will have all steps classified as ROOM with topic boundaries defined in preconditions.

### Dual-Design Divergence
When primary and alternate approaches produce very different blueprints (different phase counts, different step classifications), this is expected and correct. Both blueprints stand independently. Do not try to reconcile them.

### Circular Dependencies
If cross-mechanism dependencies create circular scaffolding (A needs B's output, B needs A's output), trigger escape hatch with `reason: "circular_dependency"` and the mechanism IDs involved.

### Scope Overflow
If scaffolding reveals work that belongs to a different stage (e.g., discovering new mechanisms not in Stage 4), note it in `scope_flag` but complete your scaffolding. Do not add mechanisms — that's Stage 4's job.

## Confidence Scoring

After producing output, score each dimension 0-20:

1. **Completeness (0-20):** ALL mechanisms scaffolded? ALL steps classified? ALL 7 questions answered? Dual-design mechanisms have both blueprints?
2. **Accuracy (0-20):** Classifications obviously correct? Auth validation = WALL (not ROOM). Creative summary = ROOM (not WALL). No misclassifications?
3. **Consistency (0-20):** Blueprints align with Stage 4 descriptions? Entry/exit conditions chain? Cross-mechanism dependencies in entry conditions?
4. **Specificity (0-20):** WALL validations machine-checkable? DOOR constraints specific and bounded? Steps detailed enough to write code from?
5. **Handoff Readiness (0-20):** Could Stage 6 deterministically arrange pages? Every mechanism's UI surface clear? Connections between mechanisms explicit?

**Total = sum of 5 dimensions (/100)**

- **≥ 90:** PASS — proceed to Stage 6
- **70-89:** WARN — flag low dimensions in metadata, proceed with warning
- **< 70:** FAIL — trigger escape hatch, do NOT pass output forward

## Escape Hatch

**When to trigger:**
- Required input missing (no mechanisms from Stage 4)
- Mechanism description too vague for meaningful scaffolding (after one retry)
- Confidence score < 70 after one retry
- Circular cross-mechanism dependencies
- Mechanism fundamentally outside scope contract (not caught by Stage 4)

**What to save:**
- Current `context_packet` with partial blueprints
- Stage number (5) and mechanism ID being scaffolded when halt occurred
- List of mechanisms scaffolded vs remaining
- What was attempted and what failed
- Suggested questions for human

**How to signal:**
- Set `metadata.status = "needs_human"`
- Add entry to `metadata.escape_hatches[]` with `{ "stage": 5, "mechanism_id": "...", "reason": "..." }`
- Save context packet snapshot
- Output structured `NEEDS_HUMAN` message

## Example

See [references/example-blueprint.md](references/example-blueprint.md) for a complete worked example showing one mechanism ("User Authentication") run through all 7 questions with phases, steps, classifications, and chaining conditions.

**Quick inline example — one step scaffolded:**

Mechanism: "User Authentication" → Phase: "Credential Validation" → Step: "Validate email format"

| Question | Answer | Implication |
|----------|--------|-------------|
| Q1: What happens? | Check email matches RFC 5322 pattern | Named action |
| Q2: One way or varies? | One way — regex match | **WALL** |
| Q3: Preconditions? | Email field is non-empty | Precondition defined |
| Q4: All outcomes? | valid, invalid — two options only | Finite = deterministic |
| Q5: Next step per outcome? | valid → `check_password`, invalid → `show_error` | Arrows drawn |
| Q6: Verification? | `typeof result === 'boolean'`, regex tested against 5 known-valid and 5 known-invalid emails | Machine-checkable |
| Q7: Skippable? | No, never | Confirmed WALL |

Output step:
```json
{
  "id": "mech_001_p2_s1",
  "name": "Validate email format against RFC 5322",
  "classification": "WALL",
  "preconditions": ["Email field is non-empty string"],
  "outcomes": [
    { "outcome": "valid", "next_step": "mech_001_p2_s2" },
    { "outcome": "invalid", "next_step": "mech_001_p2_s3" }
  ],
  "verification": "Regex match returns boolean; tested against 5 valid + 5 invalid emails",
  "skip_condition": null
}
```


---

## REFERENCE: checklist-lens-rules

# Martin's Checklist Rules as Scaffolding Lens

These are the Martin's Structural Checklist rules most relevant to Stage 5 scaffolding decisions. These rules SHAPE how you answer the 7 questions — they are the building code the architect follows WHILE designing.

## How to Use This Document

When scaffolding a mechanism's steps, consult these rules to inform your answers:
- **When defining WALLs:** Rules ensure walls are clean (single responsibility, no state leakage)
- **When setting phase boundaries:** Rules enforce isolation between phases
- **When writing verification:** Rules define what "correct" looks like structurally

Record every rule ID that influenced a scaffolding decision in `build_rules_applied`.

## Key Rules by Scaffolding Decision

### Step Granularity (Single Responsibility)

| Rule ID | Category | Rule | Scaffolding Impact |
|---------|----------|------|-------------------|
| FileStructure.1 | File Structure | One component per file | Each UI step maps to one component file |
| FileStructure.2 | File Structure | Feature folders for grouping | Steps in the same mechanism phase share a feature folder |
| FileStructure.3 | File Structure | Centralized type definitions | Data types are WALLs — defined once, referenced everywhere |

### Data Access (Service Layer Enforcement)

| Rule ID | Category | Rule | Scaffolding Impact |
|---------|----------|------|-------------------|
| FileStructure.8 | File Structure | Services folder for data access | Any step that touches DB → WALL with service layer access pattern |
| DataService.1 | Data Service Layer | All CRUD via service functions | Direct DB imports in components = violation. Service layer = WALL. |
| DataService.2 | Data Service Layer | Typed return values | Service functions return typed data → verification is type-checkable |
| DataService.3 | Data Service Layer | Error handling in service layer | Errors caught in service, not in components → clean phase boundaries |

### State Management (Phase Isolation)

| Rule ID | Category | Rule | Scaffolding Impact |
|---------|----------|------|-------------------|
| Stack.5 | Stack | Built-in state management | State flows through framework primitives → WALL (deterministic) |
| Stack.6 | Stack | No external state libraries | State complexity stays bounded → fewer DOORs needed |
| Config.1 | Configuration | Single config source | Config is a WALL — one place, one format, no variation |

### Authentication (Heavy WALL Zone)

| Rule ID | Category | Rule | Scaffolding Impact |
|---------|----------|------|-------------------|
| Auth.1 | Authentication | Auth provider pattern | Auth steps are WALLs — provider handles, code enforces |
| Auth.2 | Authentication | Auth context wraps app | Auth state check = WALL precondition for protected routes |
| Auth.3 | Authentication | Redirect on auth failure | Auth failure routing = WALL (code decides, not AI) |
| RouteGuard.1 | Route Guards | Protected route component | Route protection = WALL entry condition for every protected phase |

### Validation (Boundary Enforcement)

| Rule ID | Category | Rule | Scaffolding Impact |
|---------|----------|------|-------------------|
| DataAPI.1 | Data/API Patterns | Input validation before writes | Every data-write step must have a validation WALL before it |
| DataAPI.2 | Data/API Patterns | Sanitize user input | Input handling = WALL (deterministic sanitization) |
| ErrorHandling.1 | Error Handling | Consistent error format | Error display = DOOR (text varies) with WALL format constraint |
| ErrorHandling.2 | Error Handling | User-facing error messages | Never expose raw errors → DOOR with constraint |

### UI Patterns (Component Classification)

| Rule ID | Category | Rule | Scaffolding Impact |
|---------|----------|------|-------------------|
| UX.1 | UX Standards | Loading states for async | Loading indicator = WALL (always present during async) |
| UX.2 | UX Standards | Empty states with guidance | Empty state = DOOR (text varies, must guide user) |
| UX.3 | UX Standards | Confirmation for destructive | Confirm dialog = WALL (must appear before delete/destroy) |
| UX.6 | UX Standards | Form validation feedback | Inline validation = WALL (immediate, specific feedback) |

### Separation of Concerns

| Rule ID | Category | Rule | Scaffolding Impact |
|---------|----------|------|-------------------|
| FileStructure.4 | File Structure | Custom hooks per feature | Logic steps separate from UI steps → clean phase splits |
| FileStructure.5 | File Structure | Required directory structure | File placement = WALL (deterministic by convention) |
| DataStructure.1 | Data Structure | Typed interfaces | Schema definition = WALL (code enforces shape) |

## Rule Citation Format

When recording rules in `build_rules_applied`, use the format: `"Category.RuleNumber"` — for example:
- `"FileStructure.8"` — Services folder for data access
- `"DataService.1"` — All CRUD via service functions
- `"Auth.1"` — Auth provider pattern
- `"UX.3"` — Confirmation for destructive actions
- `"ErrorHandling.1"` — Consistent error format

## Most Common Rules Per Mechanism Type

| Mechanism Type | Commonly Applied Rules |
|---------------|----------------------|
| Authentication | Auth.1, Auth.2, Auth.3, RouteGuard.1, DataAPI.1 |
| Data CRUD | DataService.1, DataService.2, FileStructure.8, DataAPI.1, DataAPI.2 |
| UI Forms | UX.6, ErrorHandling.1, ErrorHandling.2, DataStructure.1 |
| Navigation | RouteGuard.1, Auth.2, FileStructure.5 |
| Dashboard/Display | UX.1, UX.2, FileStructure.4, DataService.1 |
| User Settings | UX.3, DataService.1, DataAPI.1, ErrorHandling.2 |
| Search/Filter | DataService.1, UX.1, FileStructure.4 |
| File Upload | DataAPI.2, UX.1, ErrorHandling.1, DataService.1 |


---

## REFERENCE: classification-decision-tree

# Classification Decision Tree

Use this tree when the 7-question answers don't produce an immediately obvious classification. Start at the top and follow the first matching branch.

## Primary Decision (Question 2)

```
Is there ONLY ONE way to do this step?
│
├─ YES → Is it skippable? (Q7)
│  ├─ NO → Is verification machine-checkable? (Q6)
│  │  ├─ YES → ██ WALL ██
│  │  └─ NO → Rewrite verification to be machine-checkable. If impossible → DOOR
│  └─ YES, if [condition] → DOOR (the skip condition is itself a wall-gate)
│
└─ NO, it can vary → Can you list ALL valid variations?
   ├─ YES (finite set) → DOOR
   │  └─ Document the valid set as constraints
   └─ NO (infinite/unpredictable) → ROOM
      └─ Define topic boundaries
```

## Borderline Cases

### Case: "It's mostly one way but delivery varies"
**Example:** "Ask the user for their email" — the data collected is fixed (WALL) but HOW you phrase the question can vary (DOOR).

**Resolution:** Split into two steps:
1. "Present email input field" → WALL (fixed UI element)
2. "Display contextual help text" → DOOR (can vary but must reference email)

If splitting is not justified (too granular), classify as WALL — the deterministic part dominates.

### Case: "Outcomes are finite but context-dependent"
**Example:** "Classify user sentiment" — outcomes are [positive, negative, neutral] (finite) but determining which one requires judgment.

**Resolution:** DOOR. The valid outcomes are the constraint (must be one of 3). The classification logic is bounded AI.

### Case: "Verification exists but isn't fully machine-checkable"
**Example:** "Generated summary must be accurate" — accuracy requires judgment.

**Resolution:** Make verification partially machine-checkable:
- "Summary must reference all 5 key points from the data" (checkable: count references)
- "Summary must be under 200 words" (checkable: word count)
- Remaining subjective quality → ROOM aspect

If you can make >50% of verification machine-checkable → DOOR. Otherwise → ROOM.

### Case: "Step can vary but variations are trivially equivalent"
**Example:** "Return success response" — could be `{success: true}` or `{status: "ok"}` but they're functionally identical.

**Resolution:** WALL. Pick one format and enforce it. The variation is an implementation detail, not meaningful flexibility.

### Case: "100% creative but has a fixed trigger"
**Example:** "Generate personalized greeting" — triggered by login (WALL), content is creative (ROOM).

**Resolution:** Split:
1. "Trigger greeting generation on login" → WALL
2. "Generate greeting content" → ROOM (with topic boundary: must reference user's name)

## The Default Rule

**When in doubt, classify as WALL (more restrictive).**

Rationale: A WALL that should have been a DOOR is discovered during build when the builder agent finds it too rigid — easy to relax by changing the classification. A DOOR that should have been a WALL lets the AI improvise where deterministic code should run — bugs are harder to find and fix.

## Anti-Patterns

| Wrong Classification | Why It's Wrong | Correct |
|---------------------|----------------|---------|
| Auth validation → ROOM | Auth MUST follow exact rules; no creative freedom | WALL |
| Database schema → DOOR | Schema is fixed; no AI variation | WALL |
| Error message text → WALL | User-facing text can be rephrased while keeping meaning | DOOR |
| API endpoint routing → DOOR | Routes are fixed paths; no flexibility | WALL |
| Onboarding tutorial → WALL | Tutorial content can be adaptive to user level | DOOR or ROOM |
| "Handle edge case" → ROOM | Vague. Break into specific cases, classify each | Split into specific steps |


---

## REFERENCE: example-blueprint

# Example Blueprint: User Authentication Mechanism

## Input (from Stage 4)

```json
{
  "id": "mech_001",
  "name": "User Authentication",
  "description": "Email/password registration and login with session management. Users register with email and password, verify their email, log in to receive a session token, and can reset forgotten passwords.",
  "category_ids": ["B"],
  "classification": "OBVIOUS",
  "chosen_approach": {
    "name": "Email/Password with JWT",
    "description": "Standard email/password auth using JWT tokens for session management, with email verification via one-time links and password reset via time-limited tokens.",
    "rationale": "Most common auth pattern, well-supported by all frameworks"
  },
  "alternate_approach": null
}
```

## Step 2: Map as Human Process

Walking through what a human admin would do:
1. User arrives at registration page → enters email + password
2. System validates email format and password strength
3. System checks if email already exists in database
4. System creates user record and sends verification email
5. User clicks verification link → system marks email as verified
6. User goes to login page → enters credentials
7. System validates credentials against stored hash
8. System issues session token
9. User can request password reset → system sends reset link
10. User clicks reset link → enters new password → system updates hash

Group into phases: Registration, Email Verification, Login, Password Reset.

## Step 3: Apply 7 Questions

### Phase 1: Registration

**Entry condition:** User is on the registration page; no active session exists.
**Exit condition:** User record exists in database with `email_verified: false`.

#### Step: Render registration form

| Q | Answer | Classification |
|---|--------|---------------|
| Q1 | Display form with email, password, confirm password fields | |
| Q2 | One way — exact fields required | **WALL** |
| Q3 | Registration page loaded; no existing session | |
| Q4 | Form displayed successfully, or page load error | |
| Q5 | Success → user fills form; Error → show error page | |
| Q6 | DOM contains input[name=email], input[name=password], input[name=confirmPassword], button[type=submit] | |
| Q7 | No — cannot skip | |

```json
{
  "id": "mech_001_p1_s1",
  "name": "Render registration form with email, password, confirm password fields",
  "classification": "WALL",
  "preconditions": ["Registration page route loaded", "No active user session"],
  "outcomes": [
    { "outcome": "Form rendered successfully", "next_step": "mech_001_p1_s2" },
    { "outcome": "Page load error", "next_step": "end" }
  ],
  "verification": "DOM contains input[name=email], input[name=password], input[name=confirmPassword], button[type=submit]",
  "skip_condition": null
}
```

#### Step: Validate email format

```json
{
  "id": "mech_001_p1_s2",
  "name": "Validate email format against RFC 5322 pattern",
  "classification": "WALL",
  "preconditions": ["Email field is non-empty string"],
  "outcomes": [
    { "outcome": "Email format valid", "next_step": "mech_001_p1_s3" },
    { "outcome": "Email format invalid", "next_step": "mech_001_p1_s5" }
  ],
  "verification": "Regex returns boolean; tested against 5 valid + 5 invalid email formats",
  "skip_condition": null
}
```

#### Step: Validate password strength

```json
{
  "id": "mech_001_p1_s3",
  "name": "Validate password meets minimum strength requirements",
  "classification": "WALL",
  "preconditions": ["Password field is non-empty", "Email validation passed"],
  "outcomes": [
    { "outcome": "Password meets requirements (8+ chars, 1 upper, 1 number)", "next_step": "mech_001_p1_s4" },
    { "outcome": "Password too weak", "next_step": "mech_001_p1_s5" }
  ],
  "verification": "Strength check returns {valid: boolean, failures: string[]}; tested against known-weak and known-strong passwords",
  "skip_condition": null
}
```

#### Step: Check email uniqueness in database

```json
{
  "id": "mech_001_p1_s4",
  "name": "Query database to verify email is not already registered",
  "classification": "WALL",
  "preconditions": ["Email format valid", "Password strength valid"],
  "outcomes": [
    { "outcome": "Email not found — available", "next_step": "mech_001_p1_s6" },
    { "outcome": "Email already exists", "next_step": "mech_001_p1_s5" }
  ],
  "verification": "Database query returns boolean; service layer function getUserByEmail() called (not direct DB access)",
  "skip_condition": null
}
```

#### Step: Display validation error

```json
{
  "id": "mech_001_p1_s5",
  "name": "Display specific validation error message to user",
  "classification": "DOOR",
  "preconditions": ["At least one validation check failed", "Error type is known (email_format|password_weak|email_exists)"],
  "outcomes": [
    { "outcome": "Error displayed, user corrects input", "next_step": "mech_001_p1_s2" }
  ],
  "verification": "Error element visible in DOM; error text contains the specific failure reason; error disappears when user modifies the relevant field",
  "skip_condition": null
}
```

Note: DOOR because the error message text can be rephrased ("Invalid email" vs "Please enter a valid email address") but MUST identify the specific failure. Constraint: message must reference the failed field and the requirement that was not met.

#### Step: Create user record and send verification email

```json
{
  "id": "mech_001_p1_s6",
  "name": "Create user record in database and trigger verification email",
  "classification": "WALL",
  "preconditions": ["All validations passed", "Email is unique"],
  "outcomes": [
    { "outcome": "User created, verification email sent", "next_step": "end" },
    { "outcome": "Database write error", "next_step": "mech_001_p1_s5" }
  ],
  "verification": "User record exists in DB with email_verified=false; verification token generated; email service called with token link",
  "skip_condition": null
}
```

### Phase 1 Validation Rules
- `["User record exists in database with email_verified=false", "Verification email was dispatched via email service", "No direct database imports in component files — all through service layer"]`

---

### Phase 2: Email Verification

**Entry condition:** User record exists with `email_verified: false`; verification token exists in database.
**Exit condition:** User record has `email_verified: true`.

*(Steps follow same pattern — abbreviated for space)*

### Phase 3: Login

**Entry condition:** User record exists with `email_verified: true`; user is on login page.
**Exit condition:** Valid session token issued and stored.

### Phase 4: Password Reset

**Entry condition:** User has a verified account; user requests password reset.
**Exit condition:** Password hash updated in database; old sessions invalidated.

## Complete Output Blueprint

```json
{
  "mechanism_id": "mech_001",
  "approach": "primary",
  "phases": [
    {
      "phase_label": "Registration",
      "entry_condition": "User is on registration page; no active session exists",
      "exit_condition": "User record exists in database with email_verified=false",
      "validation_rules": [
        "User record exists in database with email_verified=false",
        "Verification email dispatched via email service",
        "All DB access through service layer (no direct imports)"
      ],
      "steps": ["(6 steps as shown above)"]
    },
    {
      "phase_label": "Email Verification",
      "entry_condition": "User record exists with email_verified=false; verification token exists",
      "exit_condition": "User record has email_verified=true",
      "validation_rules": ["..."],
      "steps": ["..."]
    },
    {
      "phase_label": "Login",
      "entry_condition": "User record exists with email_verified=true; user on login page",
      "exit_condition": "Valid session token issued and stored client-side",
      "validation_rules": ["..."],
      "steps": ["..."]
    },
    {
      "phase_label": "Password Reset",
      "entry_condition": "User has verified account; user requests password reset",
      "exit_condition": "Password hash updated; old sessions invalidated",
      "validation_rules": ["..."],
      "steps": ["..."]
    }
  ]
}
```

**Key observations:**
- Phase 1 exit → Phase 2 entry: Both reference "user record with email_verified=false" ✓
- Phase 2 exit → Phase 3 entry: Both reference "email_verified=true" ✓
- Phase 3 and Phase 4 can be entered independently (Phase 4 doesn't require login)
- 5 of 6 Registration steps are WALL (deterministic). Only error display is DOOR. This is typical for auth mechanisms — mostly walls.
- Build rules applied: `["FileStructure.8"]` (services folder for data access), `["DataService.1"]` (CRUD through service layer), `["Auth.1"]` (auth provider pattern), `["FileStructure.1"]` (one component per file for form)


---

## REFERENCE: seven-questions-framework

# The 7-Question Framework

For each step of each mechanism, ask these 7 questions. The answers determine the WALL/DOOR/ROOM classification.

## The Questions

### Question 1: WHAT happens here?
Name the action. Be specific and mechanical: "Validate email format", "Query user record by ID", "Generate welcome message". If you can't name it precisely, the mechanism description is too vague.

### Question 2: Is there ONLY ONE way to do this, or can it vary? (PRIMARY CLASSIFIER)
This is the fork:
- **Only one way** → **WALL** (deterministic, code it)
- **Can vary** → Continue to determine **DOOR** or **ROOM**

To distinguish DOOR from ROOM when the answer is "can vary":
- Can you enumerate ALL valid variations? → **DOOR** (constrained set)
- Variations are infinite/unpredictable? → **ROOM** (open floor)

### Question 3: What MUST be true before this step can start?
These are preconditions — walls that prevent skipping ahead. Examples:
- "User must be authenticated" (WALL precondition)
- "Previous step must have returned valid data" (WALL precondition)
- "Context must be established" (WALL precondition)

Every precondition is itself a WALL — it's a gate that must pass before proceeding.

### Question 4: What are ALL the possible outcomes of this step?
- **Can list them ALL** = deterministic outcomes. Strengthens WALL/DOOR classification.
- **Infinite/unpredictable outcomes** = AI territory. Points toward ROOM.

Examples:
- "valid, invalid" (2 outcomes — deterministic)
- "toward, away, toward_lean, away_lean" (4 outcomes — deterministic)
- "Any natural language response" (infinite — AI territory)

### Question 5: For each outcome, where do you go next?
Draws the arrows between steps. Every outcome must have a defined next step (by step ID) or "end" (terminates the phase). No dangling outcomes.

This question also reveals hidden complexity: if outcome A leads to step X but outcome B loops back to step Y, the branching logic itself is a WALL (code decides the routing, not AI).

### Question 6: How do you VERIFY this step was done correctly?
The validation question. This is the wall you bounce off if you try to cheat.

- **For WALLs:** Must be machine-checkable. Examples:
  - "File exists at path X"
  - "Function exports loginUser and signupUser"
  - "Response matches JSON schema"
  - "Return value is one of [valid, invalid]"
  - NOT: "Check it works" or "Looks correct"

- **For DOORs:** Must verify constraints were respected. Examples:
  - "Response contains all 3 required data points"
  - "Output uses only vocabulary from the approved list"
  - "Follow-up question references the same topic as the original"

- **For ROOMs:** Must verify topic boundaries. Examples:
  - "Response references all identified items from the data set"
  - "Output is related to the mechanism's domain"

### Question 7: Can this step be skipped? Ever? Under any circumstance?
- **No, never** → Strengthens WALL classification
- **Yes, if [specific condition]** → DOOR with a lock (the condition is the lock)
- **Yes, always optional** → Could be ROOM or DOOR depending on other answers

## Classification Summary Table

| Signal | WALL | DOOR | ROOM |
|--------|------|------|------|
| Q2: Variation | One way only | Enumerable variations | Infinite variations |
| Q4: Outcomes | Finite, listable | Finite but context-dependent | Unpredictable |
| Q6: Verification | Machine-checkable | Constraint-checkable | Topic-boundary check |
| Q7: Skippable | Never | Conditionally | Often |
| Data format | Structured (schema) | Semi-structured (template) | Unstructured (prose) |
| Who controls | Code only | Code + bounded AI | AI with topic fence |

## WALL Characteristics
- Must happen exactly this way, no variation
- Possible answers from a fixed list
- Order follows a set sequence
- Results recorded in structured format
- Cannot be skipped
- Verification is machine-checkable

## DOOR Characteristics
- AI can rephrase but MUST contain the core requirement
- Must pick from valid options ONLY
- Can ask follow-up but ONLY to clarify same topic — cannot drift
- Has explicit boundaries that cannot be crossed
- Every DOOR step must document its constraints in preconditions

## ROOM Characteristics
- Small talk, rapport building, creative generation
- Explaining results in accessible language
- Generating summaries or novel content
- Any output where format/content is genuinely unpredictable
- Still has topic boundaries (the "walls of the room")


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

## 🔗 Pipeline Integration — Automatic Stage Advancement

**This section is added for pipeline automation. It tells you how to signal stage completion.**

After completing ALL steps above and producing your complete output:

### Stage Completion Protocol

1. **Verify your confidence score** meets the gate threshold (≥ 70)
2. **Verify the complete JSON output** has been produced and meets the contract
3. **Output the completion marker** on its own line as the ABSOLUTE LAST thing in your response:

```
[STAGE_COMPLETE]
```

### Rules for the completion marker:

- `[STAGE_COMPLETE]` MUST be the absolute last thing in your response — nothing after it
- Your complete JSON output (context_packet) MUST come BEFORE the marker
- **Never** output `[STAGE_COMPLETE]` until the stage contract is fully met
- **Never** output `[STAGE_COMPLETE]` if the confidence score is below 70
- If you need to ask the user questions, do **NOT** output `[STAGE_COMPLETE]` — wait for answers first, produce your final output, THEN output the marker
- If the gate_result is "fail" (score < 70), trigger the escape hatch protocol instead — do NOT output `[STAGE_COMPLETE]`

### What happens when you output [STAGE_COMPLETE]:

1. The pipeline captures everything before the marker as your stage output
2. Your output becomes the input for the next stage
3. The next stage starts automatically — no manual intervention needed

### Example — end of your response:

```json
{
  "stage_5": { ... your complete output ... },
  "metadata": {
    "confidence_scores": {
      "5": { "score": 93, "gate_result": "pass" }
    }
  }
}
```

[STAGE_COMPLETE]


================================================================================
STAGE 6: LAYOUT, MOCKUPS & STYLE
================================================================================

---
name: stage-06-layout-mockups-style
description: Define page layouts, wireframe patterns, component placement, and design tokens from classified mechanisms.
---

## Purpose

Transform classified mechanisms (with Wall/Door/Room blueprints from Stage 5) into visual structure: page layouts with component placement, navigation patterns, and a complete design token system. Three sequential sub-stages: 6a (arrangement selection), 6b (page mockups), 6c (style selection).

## When to Use

Activate when: `context_packet.stage_5.mechanism_blueprints` exists AND `context_packet.stage_4.mechanisms` exists (Stages 4-5 complete). Trigger phrases: "layout", "wireframe", "mockup", "style selection", "page arrangement", "design tokens", "component placement", "page layout".

Do NOT activate for: mechanism classification (Stage 5), phase sequencing (Stage 7), or any request about build ordering or verification protocols.

## Input Format

```json
{
  "stage_2": {
    "archetype_matches": [{ "archetype_id": "string", "confidence": 0.0 }]
  },
  "stage_3": {
    "concept_and_context": { "name": "string", "description": "string", "core_value_proposition": "string" },
    "target_user_and_market": { "primary_persona": {}, "pain_points": [], "goals": [] },
    "drift_anchor": "string"
  },
  "stage_4": {
    "mechanisms": [{ "id": "string", "name": "string", "description": "string", "category": "string" }],
    "mechanism_dependencies": [{ "from_id": "string", "to_id": "string", "relationship": "string" }]
  },
  "stage_5": {
    "mechanism_blueprints": [{
      "mechanism_id": "string",
      "steps": [{ "step": "string", "classification": "WALL|DOOR|ROOM" }]
    }]
  }
}
```

## Process

### Step 1: Classify App Type (Sub-6a)

Read `stage_2.archetype_matches[0].archetype_id` and `stage_3.concept_and_context`. Map to one of the 7 recognized app types using the deterministic lookup in `references/wireframe-pattern-lookup.md`:

`dashboard` | `chat` | `wizard` | `marketplace` | `tool` | `landing` | `settings`

If the archetype does not map cleanly, pick the CLOSEST match and note the deviation. This is never skipped.

### Step 2: Generate Arrangement Options (Sub-6a)

Using the app type, pull the standard wireframe pattern from the lookup table. Generate 2-3 arrangement options:

1. **Primary option**: The standard pattern for the app type (the 92% case)
2. **Secondary option**: A reasonable variation (e.g., top-nav instead of sidebar)
3. **Third option** (optional): Only if a hybrid pattern is genuinely viable

Each option has: `id`, `name` (e.g., "Sidebar + Top Nav + Content Grid"), `description` (what it looks like and why it fits).

Present to user. User MUST pick or adjust — this is a WALL. Record `selected_arrangement_id` and `user_adjustments`.

### Step 3: Identify UI-Facing Mechanisms (Sub-6b)

For each mechanism in `stage_4.mechanisms`, check its blueprint in `stage_5.mechanism_blueprints`:

- If the blueprint has steps classified as DOOR or ROOM → **user-facing** (needs a page or component)
- If ALL steps are WALL with zero user interaction → **backend-only** (no page needed, but still map to a page's "backend services" note)

### Step 4: Group Mechanisms into Pages (Sub-6b)

Apply standard grouping conventions from `references/component-placement-conventions.md`:

- Auth mechanisms → Login/Register page(s)
- Dashboard/overview mechanisms → Dashboard page
- CRUD mechanisms per entity → Entity list + detail pages
- Settings/preferences → Settings page
- Each major workflow → Its own page or modal

For each page, define: `page_name`, `route` (kebab-case, logical hierarchy), `layout_pattern` (from selected arrangement), `components` array, `user_approved`.

### Step 5: Place Components on Pages (Sub-6b)

For each page, identify every UI component needed. For each component specify:

- `component_name`: Descriptive (e.g., "TaskListTable", "CreateTaskModal")
- `placement`: Zone on the page — `"header"` | `"sidebar"` | `"main-content"` | `"footer"` | `"modal"` | `"drawer"`
- `mechanism_ids`: Array of mechanism IDs from Stage 4 this component serves
- Every `mechanism_id` must reference a real ID from `stage_4.mechanisms`

**Validation**: After all pages are defined, verify every mechanism from Stage 4 appears in at least one component's `mechanism_ids`. If any mechanism is "homeless," either add it to an existing page or create a new page.

Present each page to user for approval — this is a WALL. Set `user_approved: true` for each.

### Step 6: Curate Style Options (Sub-6c)

From the 12 predefined styles in `references/style-catalog.md`, select exactly 3 that best match:

1. **App type fit**: Dashboard → flat-design or dark-mode; Chat → minimalism or glassmorphism; etc.
2. **Target audience**: From `stage_3.target_user_and_market` — age range, professional vs casual, tech-savvy vs general
3. **Vibe match**: From `stage_3.concept_and_context.core_value_proposition` — premium, playful, technical, friendly

Present 3 options with: `id`, `name`, `vibe` (one-line description). Include a "Choose for me" default that selects the highest-scoring option. User picks one. Record `selected_style_id`.

### Step 7: Generate Design Tokens (Sub-6c)

For the selected style, populate the COMPLETE `design_tokens` object from `references/style-catalog.md`:

- `colors`: Primary, secondary, accent, surface, text, border, success, warning, error, info — all as hex values
- `typography`: Font families (heading, body, mono), size scale (xs through 4xl in rem), weights, line-heights
- `spacing`: Scale from 0.25rem to 6rem
- `border_radius`: sm, md, lg, xl, full
- `shadows`: sm, md, lg, xl

Generate `tailwind_config_overrides` — an object that can extend a Tailwind config with the selected style's tokens.

Calculate `audience_scores`: `audience_fit` (0-100), `vibe_match` (0-100), `age_range_fit` (0-100) based on persona alignment.

### Step 8: Validate and Score

Run all validation checks before writing output:

1. `app_type_classification` is set and recognized
2. `arrangement_options` has 2-3 entries, one selected
3. `pages` has ≥ 2 pages (auth + one functional)
4. Every page has `page_name`, `route`, `layout_pattern`, `components[]`, `user_approved`
5. Every mechanism from Stage 4 is on ≥ 1 page's component `mechanism_ids`
6. Every `mechanism_ids` entry references a real Stage 4 mechanism ID
7. `style_options_presented` has exactly 3 entries
8. `design_tokens` has `colors` and `typography` sub-objects with specific values
9. `selected_style_id` is from the predefined set or `"developers_choice"`
10. Run confidence scoring (see below)

## Output Format

```json
{
  "stage_6": {
    "sub_6a": {
      "app_type_classification": "string",
      "arrangement_options": [
        { "id": "string", "name": "string", "description": "string" }
      ],
      "selected_arrangement_id": "string",
      "user_adjustments": "string | null"
    },
    "sub_6b": {
      "pages": [
        {
          "page_name": "string",
          "route": "/kebab-case",
          "layout_pattern": "string",
          "components": [
            {
              "component_name": "string",
              "placement": "header|sidebar|main-content|footer|modal|drawer",
              "mechanism_ids": ["string"]
            }
          ],
          "user_approved": true
        }
      ]
    },
    "sub_6c": {
      "style_options_presented": [
        { "id": "string", "name": "string", "vibe": "string" }
      ],
      "selected_style_id": "string",
      "design_tokens": {
        "colors": { "primary": "#hex", "secondary": "#hex", "...": "..." },
        "typography": { "heading_font": "string", "body_font": "string", "sizes": {} },
        "spacing": { "1": "0.25rem", "...": "..." },
        "border_radius": { "sm": "string", "...": "..." },
        "shadows": { "sm": "string", "...": "..." }
      },
      "tailwind_config_overrides": {},
      "audience_scores": { "audience_fit": 0, "vibe_match": 0, "age_range_fit": 0 }
    }
  },
  "metadata": {
    "current_stage": 6,
    "confidence_scores": { "6": { "score": 0, "dimensions": {}, "gate_result": "pass|flag|fail" } },
    "stage_timestamps": { "6": "ISO-8601" }
  }
}
```

## Edge Cases

### Missing Input

- No `mechanism_blueprints` from Stage 5 → Trigger escape hatch. Cannot determine UI surfaces without blueprints.
- No `mechanisms` from Stage 4 → Trigger escape hatch. Nothing to lay out.
- No `archetype_matches` from Stage 2 → Fall back to analyzing `concept_and_context` description to classify app type. Log the fallback.

### Ambiguous Input

- Mechanism blueprint has only WALLs but mechanism name implies UI ("UserProfileEditor" with all-WALL steps) → Classify as user-facing with a flag. Ask user if available: "This mechanism appears backend-only but its name suggests UI. Should it have a page?"
- App is a hybrid (dashboard + chat) → Present the dominant pattern as primary, the secondary pattern as option 2, and a hybrid layout as option 3. Let user pick.

### Backend-Only Mechanisms

- Mechanisms with zero DOOR/ROOM steps are NOT placed on any page as components. Instead, note them in the nearest related page as "Backend service: [mechanism_name]" in a `backend_services` field. They still count as "mapped" for the all-mechanisms-mapped check.

### User Rejects All Style Options

- If user rejects all 3 curated styles AND the "Choose for me" default → Present 3 MORE from the remaining 9 styles. If still rejected → Trigger escape hatch with `reason: "style_rejection"` and `suggested_action: "custom_style_needed"`.

### Non-Standard App Type

- If the app doesn't fit any of the 7 standard types → Pick the closest match, present it with a note: "This is the closest standard pattern. What would you change?" The adjustment is a WALL.

### Scope Overflow

- If page creation implies mechanisms not in `stage_2.scope_contract` → Flag but do not create pages for out-of-scope mechanisms. Note the gap in metadata.

## Confidence Scoring

Score each dimension 0-20 after producing output:

1. **Completeness** (0-20): ≥2 pages? Every mechanism mapped? All 3 sub-stages populated? Design tokens complete (colors + typography + spacing)?
2. **Accuracy** (0-20): Wireframe pattern matches app type? Mechanisms on correct pages (auth→login, CRUD→entity pages)? Style matches target audience?
3. **Consistency** (0-20): No route conflicts? All component `mechanism_ids` reference real Stage 4 IDs? Style matches app type and archetype? All pages use selected arrangement consistently?
4. **Specificity** (0-20): Every component has exact placement + mechanism connection? Design tokens are specific values (hex, rem, px)? A developer could build any page from the spec alone?
5. **Handoff Readiness** (0-20): Could Stage 7 create file sandboxes and build orders? Every page/component detailed enough for token estimation? File paths inferable from page/component names?

**Total = sum of 5 dimensions (/100)**

- ≥ 90: PASS — proceed to Stage 7
- 70-89: WARN — flag low dimensions, proceed with warning
- < 70: FAIL — trigger escape hatch, do NOT pass output forward

## Escape Hatch

**When to trigger:**

- Required input fields missing (no blueprints, no mechanisms)
- App does not fit ANY wireframe pattern and user unavailable for guidance
- Mechanism cannot be mapped to any page (ambiguous UI surface, not backend-only)
- User rejects all 6 style options (3 curated + 3 alternates)
- Confidence score < 70 after one retry

**What to save:**

- Current `context_packet` with partial layout/style data
- Stage number (6) and active sub-stage (6a, 6b, or 6c)
- Pages already defined/approved vs remaining
- Unmapped mechanisms list
- What was attempted and what failed
- Suggested questions for the human

**How to signal:**

- Set `metadata.status = "needs_human"`
- Add entry to `metadata.escape_hatches[]`: `{ "stage": 6, "sub_stage": "6a|6b|6c", "reason": "string", "suggested_actions": ["string"] }`
- Save context packet snapshot
- Output structured NEEDS_HUMAN message

## Example

See `references/example-output.md` for a complete walkthrough: a task management app flowing through Sub-6a (dashboard type → sidebar arrangement), Sub-6b (5 pages with component placement), Sub-6c (flat-design style with full tokens).

**Quick summary of the flow:**

1. Archetype: "productivity-dashboard" → App type: `dashboard`
2. Lookup: dashboard → sidebar + top nav + content grid + cards
3. Options: (a) Sidebar+TopNav+Grid [selected], (b) TopNav-only+Grid, (c) Tabbed+Grid
4. Pages: Login, Dashboard, Task List, Task Detail, Settings — each with named components mapped to mechanism IDs
5. Style curation: flat-design (88), minimalism (82), dark-mode (79) → User picks flat-design
6. Tokens: `#3B82F6` primary, Inter/system-ui fonts, 4px spacing scale, etc.


---
## REFERENCE: component-placement-conventions

# Component Placement Conventions

> Standard UI component placement patterns per app type. Used by Sub-6b to place components on pages.

## Universal Placement Rules

These apply to ALL app types:

1. **Navigation** goes at the top (horizontal) or left side (vertical sidebar). Never bottom, never right.
2. **Primary action buttons** (CTA) go top-right of the content area or bottom-right of forms.
3. **Search** goes at the top, either in the nav bar or immediately below it.
4. **User menu / avatar** goes top-right corner, always.
5. **Notifications** go top-right, near the user menu (bell icon pattern).
6. **Breadcrumbs** go immediately below the top nav, above the content area.
7. **Modals** center on screen with backdrop overlay.
8. **Toast notifications** appear top-right or bottom-right, stacked.
9. **Loading states** replace the content area; never show a blank page.
10. **Empty states** show in the content area with illustration + CTA to create first item.

## Per-App-Type Conventions

### Dashboard

| Component Type | Placement | Notes |
|---------------|-----------|-------|
| Summary cards (KPIs) | Main content, top row | 3-5 cards in a row, full-width |
| Data tables | Main content, below cards | Full-width or 2/3 width |
| Charts/graphs | Main content, mixed with tables | Card containers, responsive grid |
| Activity feed | Sidebar (right) or bottom of main | Scrollable, time-ordered |
| Quick actions | Top bar or sidebar | Common operations (create, export) |
| Filters / date range | Top of content area, below breadcrumbs | Persistent across page sections |
| Navigation items | Left sidebar | Grouped by category with icons |

### Chat

| Component Type | Placement | Notes |
|---------------|-----------|-------|
| Conversation list | Left panel (fixed width ~300px) | Scrollable, search at top |
| Message thread | Center panel (flex) | Scrollable, newest at bottom |
| Message input | Bottom of center panel | Fixed position, expands on focus |
| User/channel info | Right panel (collapsible) | Member list, shared files, pinned items |
| Typing indicator | Above input bar | Inline with message thread |
| File attachments | Inline in messages + drag-drop zone | Preview thumbnails |
| Emoji/reaction picker | Popover from input bar or message hover | Floating panel |

### Wizard / Form

| Component Type | Placement | Notes |
|---------------|-----------|-------|
| Step indicator | Top of content area | Horizontal steps with numbers/labels |
| Form fields | Center content (max-width ~600px) | Single column, generous spacing |
| Field validation | Inline below each field | Red text + icon on error |
| Next/Back buttons | Bottom of form area, right-aligned | Primary (next) + secondary (back) |
| Summary/review step | Final step, read-only view of all inputs | Editable via "edit" links per section |
| Progress bar | Top, as part of step indicator | Percentage or step count |
| Help text / tooltips | Inline below labels or hover info icons | Context-sensitive |

### Marketplace

| Component Type | Placement | Notes |
|---------------|-----------|-------|
| Search bar | Top, prominent, full-width or centered | Auto-suggest, recent searches |
| Category filters | Left sidebar (desktop) / top accordion (mobile) | Collapsible sections per filter type |
| Product grid | Main content (right of filters) | 3-4 columns, responsive to 1-2 on mobile |
| Product card | Within grid | Image, title, price, rating, CTA |
| Sort controls | Top of product grid, right-aligned | Dropdown: relevance, price, rating, newest |
| Pagination | Bottom of product grid | Page numbers or infinite scroll |
| Cart icon | Top nav, right side | Badge with item count |
| Product detail | Full page (replaces grid) | Image gallery left, info right |

### Tool

| Component Type | Placement | Notes |
|---------------|-----------|-------|
| Toolbar | Top of workspace | Icon buttons, grouped by function |
| Tool palette | Left sidebar (narrow, icon-only) | Vertical icon strip |
| Canvas/workspace | Center (takes maximum space) | Scrollable/zoomable |
| Properties panel | Right sidebar (collapsible) | Context-sensitive to selected element |
| Layers panel | Right sidebar (below properties) | Drag-reorderable list |
| Zoom controls | Bottom-right of canvas | Zoom in/out/fit buttons |
| Status bar | Bottom of screen, full-width | File info, cursor position, zoom level |
| Command palette | Center modal (on keyboard shortcut) | Searchable command list |

### Landing Page

| Component Type | Placement | Notes |
|---------------|-----------|-------|
| Nav bar | Top, sticky on scroll | Logo left, links center/right, CTA right |
| Hero section | Full-width, first section | Headline, subheadline, CTA, optional image/video |
| Feature grid | Below hero | 3-4 columns, icon + title + description |
| Social proof / testimonials | Below features | Carousel or grid of testimonial cards |
| Pricing table | Own section | 2-4 tier columns, highlight recommended |
| FAQ | Below pricing | Accordion pattern |
| CTA banner | Above footer | Full-width, contrasting background |
| Footer | Bottom | Logo, link columns, social icons, legal |

### Settings

| Component Type | Placement | Notes |
|---------------|-----------|-------|
| Tab/section nav | Left sidebar (vertical) or top (horizontal) | Category labels: Profile, Security, Notifications, etc. |
| Form sections | Main content area | Grouped by category, separated by dividers |
| Toggle switches | Inline in form sections | Right-aligned within rows |
| Save/Cancel buttons | Bottom of each section or sticky footer | Primary (save) + secondary (cancel) |
| Danger zone | Bottom of settings, red-bordered | Account deletion, data export |
| Avatar upload | Top of profile section | Click-to-upload with preview |
| Connected accounts | Own section | List with connect/disconnect buttons |

## Page Grouping Rules

When grouping mechanisms into pages:

| Mechanism Pattern | Page Pattern | Notes |
|------------------|-------------|-------|
| Auth (login, register, forgot password) | 1-3 pages: Login, Register, Forgot Password | Can be combined into one page with tabs |
| CRUD for an entity | 2 pages: Entity List + Entity Detail | Detail page handles create/edit via modal or inline |
| User profile | 1 page: Profile (within settings or standalone) | Combines view + edit modes |
| Search + Browse | 1 page with filters | Search is a component, not a separate page |
| Notifications | 0 pages (dropdown) or 1 page (full history) | Depends on notification volume |
| Admin panel | Multiple pages mirroring main app | Often a separate route prefix (/admin/*) |
| Onboarding | 1 wizard page (multi-step) | Shown once after registration |
| Error pages | 2 pages: 404, 500 | Static, minimal |

## Route Conventions

| Route Pattern | Usage |
|--------------|-------|
| `/` | Dashboard or landing (authenticated vs not) |
| `/login`, `/register`, `/forgot-password` | Auth pages |
| `/{entity}` | Entity list (e.g., `/tasks`, `/products`) |
| `/{entity}/:id` | Entity detail (e.g., `/tasks/123`) |
| `/{entity}/new` | Create new entity |
| `/settings` | Settings root |
| `/settings/{section}` | Settings sub-section |
| `/admin` | Admin panel root |
| `/admin/{entity}` | Admin entity management |


---
## REFERENCE: example-output

# Example Output — Task Management App

> Complete walkthrough of Stage 6 processing a task management app ("TaskFlow") with 8 mechanisms from Stage 4.

## Input Summary

**App concept:** TaskFlow — a team task management app with boards, lists, and card-based workflows.

**Archetype match:** `productivity-dashboard` (confidence: 0.92)

**Mechanisms from Stage 4:**

| ID | Name | Category | Has UI (from Stage 5 blueprints) |
|----|------|----------|----------------------------------|
| M1 | User Authentication | Auth | Yes (DOOR: login form, register form) |
| M2 | Team Management | Admin | Yes (DOOR: invite members, ROOM: team settings) |
| M3 | Board CRUD | Core | Yes (DOOR: create/edit board, ROOM: board view) |
| M4 | Task CRUD | Core | Yes (DOOR: create/edit task, ROOM: task detail) |
| M5 | Task Assignment | Core | Yes (DOOR: assign dropdown) |
| M6 | Notification Engine | System | Backend-only (all WALL steps) |
| M7 | Dashboard Analytics | Reporting | Yes (ROOM: charts, WALL: data aggregation) |
| M8 | User Preferences | Settings | Yes (DOOR: theme toggle, notification prefs) |

## Sub-6a Output: Arrangement Selection

```json
{
  "sub_6a": {
    "app_type_classification": "dashboard",
    "arrangement_options": [
      {
        "id": "opt_1",
        "name": "Sidebar + Top Nav + Content Grid",
        "description": "Collapsible left sidebar for board navigation, top bar with search and user menu, main area with card grid. Standard pattern for task management tools (Trello, Asana, Linear)."
      },
      {
        "id": "opt_2",
        "name": "Top Nav Only + Content Grid",
        "description": "No sidebar. Top nav with board switcher dropdown. Main area with full-width card grid. Simpler layout, better for fewer boards."
      },
      {
        "id": "opt_3",
        "name": "Sidebar + Kanban Columns",
        "description": "Left sidebar for boards, main area uses horizontal kanban columns instead of a grid. Best for workflow-heavy task management."
      }
    ],
    "selected_arrangement_id": "opt_1",
    "user_adjustments": null
  }
}
```

## Sub-6b Output: Page Mockups

```json
{
  "sub_6b": {
    "pages": [
      {
        "page_name": "Login",
        "route": "/login",
        "layout_pattern": "centered-form",
        "components": [
          {
            "component_name": "LoginForm",
            "placement": "main-content",
            "mechanism_ids": ["M1"]
          },
          {
            "component_name": "RegisterLink",
            "placement": "main-content",
            "mechanism_ids": ["M1"]
          }
        ],
        "user_approved": true
      },
      {
        "page_name": "Register",
        "route": "/register",
        "layout_pattern": "centered-form",
        "components": [
          {
            "component_name": "RegisterForm",
            "placement": "main-content",
            "mechanism_ids": ["M1"]
          }
        ],
        "user_approved": true
      },
      {
        "page_name": "Dashboard",
        "route": "/",
        "layout_pattern": "sidebar-topnav-grid",
        "components": [
          {
            "component_name": "BoardSidebar",
            "placement": "sidebar",
            "mechanism_ids": ["M3"]
          },
          {
            "component_name": "TopNavBar",
            "placement": "header",
            "mechanism_ids": []
          },
          {
            "component_name": "SearchBar",
            "placement": "header",
            "mechanism_ids": ["M4"]
          },
          {
            "component_name": "UserMenu",
            "placement": "header",
            "mechanism_ids": ["M1", "M8"]
          },
          {
            "component_name": "TaskSummaryCards",
            "placement": "main-content",
            "mechanism_ids": ["M7"]
          },
          {
            "component_name": "RecentActivityFeed",
            "placement": "main-content",
            "mechanism_ids": ["M7"]
          },
          {
            "component_name": "TeamOverviewWidget",
            "placement": "main-content",
            "mechanism_ids": ["M2", "M7"]
          }
        ],
        "backend_services": ["M6"],
        "user_approved": true
      },
      {
        "page_name": "Board Detail",
        "route": "/boards/:id",
        "layout_pattern": "sidebar-topnav-grid",
        "components": [
          {
            "component_name": "BoardSidebar",
            "placement": "sidebar",
            "mechanism_ids": ["M3"]
          },
          {
            "component_name": "BoardHeader",
            "placement": "main-content",
            "mechanism_ids": ["M3"]
          },
          {
            "component_name": "TaskCardGrid",
            "placement": "main-content",
            "mechanism_ids": ["M4", "M5"]
          },
          {
            "component_name": "CreateTaskButton",
            "placement": "main-content",
            "mechanism_ids": ["M4"]
          },
          {
            "component_name": "TaskDetailDrawer",
            "placement": "drawer",
            "mechanism_ids": ["M4", "M5"]
          }
        ],
        "user_approved": true
      },
      {
        "page_name": "Settings",
        "route": "/settings",
        "layout_pattern": "sidebar-tabs-form",
        "components": [
          {
            "component_name": "SettingsTabNav",
            "placement": "sidebar",
            "mechanism_ids": ["M8"]
          },
          {
            "component_name": "ProfileSection",
            "placement": "main-content",
            "mechanism_ids": ["M1"]
          },
          {
            "component_name": "TeamManagementSection",
            "placement": "main-content",
            "mechanism_ids": ["M2"]
          },
          {
            "component_name": "NotificationPreferences",
            "placement": "main-content",
            "mechanism_ids": ["M8"]
          },
          {
            "component_name": "ThemeToggle",
            "placement": "main-content",
            "mechanism_ids": ["M8"]
          }
        ],
        "user_approved": true
      }
    ]
  }
}
```

### Mechanism Mapping Verification

| Mechanism | Pages |
|-----------|-------|
| M1 (Auth) | Login, Register, Dashboard (UserMenu), Settings (ProfileSection) |
| M2 (Team) | Dashboard (TeamOverviewWidget), Settings (TeamManagementSection) |
| M3 (Board CRUD) | Dashboard (BoardSidebar), Board Detail (BoardSidebar, BoardHeader) |
| M4 (Task CRUD) | Dashboard (SearchBar), Board Detail (TaskCardGrid, CreateTaskButton, TaskDetailDrawer) |
| M5 (Task Assignment) | Board Detail (TaskCardGrid, TaskDetailDrawer) |
| M6 (Notifications) | Dashboard (backend_services) — backend-only, no UI components |
| M7 (Analytics) | Dashboard (TaskSummaryCards, RecentActivityFeed, TeamOverviewWidget) |
| M8 (Preferences) | Dashboard (UserMenu), Settings (SettingsTabNav, NotificationPreferences, ThemeToggle) |

**All mechanisms mapped: ✅**

## Sub-6c Output: Style Selection

### Style Curation Scoring

| Style | audience_fit | vibe_match | app_type_fit | Composite |
|-------|-------------|------------|-------------|-----------|
| flat-design | 90 | 85 | 95 | **89.75** |
| minimalism | 85 | 80 | 85 | **83.25** |
| dark-mode | 80 | 75 | 90 | **80.75** |

### Output

```json
{
  "sub_6c": {
    "style_options_presented": [
      {
        "id": "flat-design",
        "name": "Flat Design",
        "vibe": "Clean, clear, universal — the 'just works' default for productivity tools"
      },
      {
        "id": "minimalism",
        "name": "Minimalism",
        "vibe": "Premium, elegant — Apple-inspired feel for a focused task experience"
      },
      {
        "id": "dark-mode",
        "name": "Dark Mode Elegant",
        "vibe": "Refined dark theme — easy on the eyes for long work sessions"
      }
    ],
    "selected_style_id": "flat-design",
    "design_tokens": {
      "colors": {
        "primary": "#3B82F6",
        "secondary": "#8B5CF6",
        "accent": "#F59E0B",
        "surface": "#FFFFFF",
        "surface_alt": "#F8FAFC",
        "text": "#1E293B",
        "text_secondary": "#64748B",
        "border": "#E2E8F0",
        "success": "#22C55E",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "info": "#3B82F6"
      },
      "typography": {
        "heading_font": "Inter, system-ui, sans-serif",
        "body_font": "Inter, system-ui, sans-serif",
        "mono_font": "JetBrains Mono, Fira Code, monospace",
        "sizes": {
          "xs": "0.75rem",
          "sm": "0.875rem",
          "base": "1rem",
          "lg": "1.125rem",
          "xl": "1.25rem",
          "2xl": "1.5rem",
          "3xl": "1.875rem",
          "4xl": "2.25rem"
        },
        "weights": { "normal": 400, "medium": 500, "semibold": 600, "bold": 700 },
        "line_heights": { "tight": 1.25, "normal": 1.5, "relaxed": 1.75 }
      },
      "spacing": {
        "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
        "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
        "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
      },
      "border_radius": {
        "sm": "0.25rem", "md": "0.375rem", "lg": "0.5rem", "xl": "0.75rem", "full": "9999px"
      },
      "shadows": {
        "sm": "0 1px 2px rgba(0,0,0,0.05)",
        "md": "0 4px 6px rgba(0,0,0,0.07)",
        "lg": "0 10px 15px rgba(0,0,0,0.1)",
        "xl": "0 20px 25px rgba(0,0,0,0.1)"
      }
    },
    "tailwind_config_overrides": {
      "extend": {
        "colors": {
          "primary": "#3B82F6",
          "secondary": "#8B5CF6",
          "accent": "#F59E0B",
          "surface": { "DEFAULT": "#FFFFFF", "alt": "#F8FAFC" }
        },
        "fontFamily": {
          "heading": ["Inter", "system-ui", "sans-serif"],
          "body": ["Inter", "system-ui", "sans-serif"],
          "mono": ["JetBrains Mono", "Fira Code", "monospace"]
        },
        "borderRadius": {
          "sm": "0.25rem", "md": "0.375rem", "lg": "0.5rem", "xl": "0.75rem"
        },
        "boxShadow": {
          "sm": "0 1px 2px rgba(0,0,0,0.05)",
          "md": "0 4px 6px rgba(0,0,0,0.07)",
          "lg": "0 10px 15px rgba(0,0,0,0.1)"
        }
      }
    },
    "audience_scores": {
      "audience_fit": 90,
      "vibe_match": 85,
      "age_range_fit": 88
    }
  }
}
```

## Confidence Scoring

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Completeness | 19/20 | 5 pages, all 8 mechanisms mapped, all 3 sub-stages populated, full design tokens |
| Accuracy | 19/20 | Dashboard pattern correct for productivity app; auth on login pages, CRUD on board detail, analytics on dashboard |
| Consistency | 20/20 | No route conflicts; all mechanism_ids reference real M1-M8; flat-design matches productivity archetype |
| Specificity | 18/20 | Every component has placement and mechanism connection; tokens are hex/rem values; a developer could build from this |
| Handoff Readiness | 18/20 | Stage 7 can create file lists from page/component names; token estimates derivable from component count |

**Total: 94/100 — PASS**

## Metadata Written

```json
{
  "metadata": {
    "current_stage": 6,
    "updated_at": "2026-04-03T14:30:00Z",
    "confidence_scores": {
      "6": {
        "score": 94,
        "dimensions": {
          "completeness": 19,
          "accuracy": 19,
          "consistency": 20,
          "specificity": 18,
          "handoff_readiness": 18
        },
        "gate_result": "pass"
      }
    },
    "stage_timestamps": {
      "6": "2026-04-03T14:30:00Z"
    }
  }
}
```


---
## REFERENCE: style-catalog

# Style Catalog — 12 Predefined Styles

> Complete token sets for all 12 styles. The skill curates 3 from these 12 based on app type + audience fit.

## Curation Algorithm

To select 3 styles from the catalog:

1. **Score each style** against three criteria (0-100 each):
   - `audience_fit`: Does the style match the target user's age, profession, and expectations?
   - `vibe_match`: Does the style's vibe align with the product's core value proposition?
   - `app_type_fit`: Is this style commonly used for this app type?
2. **Composite score** = (audience_fit × 0.4) + (vibe_match × 0.35) + (app_type_fit × 0.25)
3. **Pick top 3** by composite score. If a tie, prefer more universally appealing styles.
4. **"Choose for me"** default = highest composite score.

### App Type Affinity Matrix

| Style | dashboard | chat | wizard | marketplace | tool | landing | settings |
|-------|-----------|------|--------|-------------|------|---------|----------|
| flat-design | 95 | 80 | 90 | 85 | 80 | 85 | 90 |
| minimalism | 85 | 85 | 85 | 80 | 75 | 95 | 85 |
| neumorphism | 80 | 60 | 75 | 55 | 70 | 60 | 85 |
| glassmorphism | 75 | 80 | 70 | 75 | 65 | 90 | 70 |
| skeuomorphism | 50 | 45 | 60 | 55 | 65 | 40 | 70 |
| neubrutalism | 55 | 65 | 50 | 70 | 55 | 85 | 45 |
| bauhaus | 60 | 55 | 55 | 60 | 70 | 80 | 50 |
| claymorphism | 55 | 70 | 75 | 65 | 45 | 75 | 60 |
| retro-futurism | 45 | 50 | 40 | 50 | 60 | 70 | 35 |
| cyberpunk | 50 | 55 | 35 | 45 | 70 | 65 | 40 |
| dark-mode | 90 | 85 | 65 | 70 | 95 | 75 | 80 |
| warmer-shades | 70 | 75 | 80 | 75 | 50 | 80 | 80 |

### Audience Affinity Guide

| Audience Trait | Best Styles | Avoid |
|---------------|-------------|-------|
| Enterprise / Corporate | flat-design, minimalism, dark-mode | neubrutalism, cyberpunk, claymorphism |
| Gen Z / Young Adults | neubrutalism, glassmorphism, cyberpunk | skeuomorphism, neumorphism |
| Creative Professionals | bauhaus, minimalism, dark-mode | skeuomorphism, flat-design |
| General Consumer | flat-design, claymorphism, warmer-shades | cyberpunk, bauhaus |
| Developers / Technical | dark-mode, flat-design, minimalism | claymorphism, skeuomorphism |
| Older Demographics (50+) | skeuomorphism, warmer-shades, flat-design | cyberpunk, neubrutalism |
| Health / Wellness | claymorphism, minimalism, warmer-shades | cyberpunk, neubrutalism |
| Gaming / Entertainment | cyberpunk, retro-futurism, neubrutalism | minimalism, flat-design |
| Finance / Banking | neumorphism, dark-mode, minimalism | claymorphism, retro-futurism |
| Education | flat-design, claymorphism, warmer-shades | cyberpunk, bauhaus |

---

## Style Definitions

### 1. flat-design

**Vibe:** Clean, clear, universal — the "just works" default
**Best for:** Clarity, scalability, universal appeal

```json
{
  "colors": {
    "primary": "#3B82F6",
    "secondary": "#8B5CF6",
    "accent": "#F59E0B",
    "surface": "#FFFFFF",
    "surface_alt": "#F8FAFC",
    "text": "#1E293B",
    "text_secondary": "#64748B",
    "border": "#E2E8F0",
    "success": "#22C55E",
    "warning": "#F59E0B",
    "error": "#EF4444",
    "info": "#3B82F6"
  },
  "typography": {
    "heading_font": "Inter, system-ui, sans-serif",
    "body_font": "Inter, system-ui, sans-serif",
    "mono_font": "JetBrains Mono, Fira Code, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
      "xl": "1.25rem", "2xl": "1.5rem", "3xl": "1.875rem", "4xl": "2.25rem"
    },
    "weights": { "normal": 400, "medium": 500, "semibold": 600, "bold": 700 },
    "line_heights": { "tight": 1.25, "normal": 1.5, "relaxed": 1.75 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0.25rem", "md": "0.375rem", "lg": "0.5rem", "xl": "0.75rem", "full": "9999px" },
  "shadows": {
    "sm": "0 1px 2px rgba(0,0,0,0.05)",
    "md": "0 4px 6px rgba(0,0,0,0.07)",
    "lg": "0 10px 15px rgba(0,0,0,0.1)",
    "xl": "0 20px 25px rgba(0,0,0,0.1)"
  }
}
```

**Tailwind overrides:**
```json
{
  "extend": {
    "colors": { "primary": "#3B82F6", "secondary": "#8B5CF6", "accent": "#F59E0B" },
    "fontFamily": { "heading": ["Inter", "system-ui", "sans-serif"], "body": ["Inter", "system-ui", "sans-serif"] }
  }
}
```

---

### 2. minimalism

**Vibe:** Premium, elegant, Apple-inspired — less is more
**Best for:** Premium feel, Apple-style elegance

```json
{
  "colors": {
    "primary": "#000000",
    "secondary": "#6B7280",
    "accent": "#2563EB",
    "surface": "#FFFFFF",
    "surface_alt": "#FAFAFA",
    "text": "#111827",
    "text_secondary": "#9CA3AF",
    "border": "#F3F4F6",
    "success": "#10B981",
    "warning": "#F59E0B",
    "error": "#EF4444",
    "info": "#2563EB"
  },
  "typography": {
    "heading_font": "SF Pro Display, -apple-system, system-ui, sans-serif",
    "body_font": "SF Pro Text, -apple-system, system-ui, sans-serif",
    "mono_font": "SF Mono, Menlo, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
      "xl": "1.25rem", "2xl": "1.5rem", "3xl": "2rem", "4xl": "2.5rem"
    },
    "weights": { "normal": 400, "medium": 500, "semibold": 600, "bold": 700 },
    "line_heights": { "tight": 1.2, "normal": 1.5, "relaxed": 1.75 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0.25rem", "md": "0.5rem", "lg": "0.75rem", "xl": "1rem", "full": "9999px" },
  "shadows": {
    "sm": "0 1px 3px rgba(0,0,0,0.04)",
    "md": "0 4px 6px rgba(0,0,0,0.04)",
    "lg": "0 10px 20px rgba(0,0,0,0.06)",
    "xl": "0 25px 50px rgba(0,0,0,0.08)"
  }
}
```

---

### 3. neumorphism

**Vibe:** Soft, tactile, embossed — like pressing real buttons
**Best for:** Finance apps, dashboards, toggles

```json
{
  "colors": {
    "primary": "#6366F1",
    "secondary": "#8B5CF6",
    "accent": "#EC4899",
    "surface": "#E0E5EC",
    "surface_alt": "#D1D9E6",
    "text": "#2D3748",
    "text_secondary": "#718096",
    "border": "#C9D1DC",
    "success": "#48BB78",
    "warning": "#ECC94B",
    "error": "#FC8181",
    "info": "#63B3ED"
  },
  "typography": {
    "heading_font": "Poppins, sans-serif",
    "body_font": "Poppins, sans-serif",
    "mono_font": "Fira Code, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
      "xl": "1.25rem", "2xl": "1.5rem", "3xl": "1.875rem", "4xl": "2.25rem"
    },
    "weights": { "normal": 400, "medium": 500, "semibold": 600, "bold": 700 },
    "line_heights": { "tight": 1.25, "normal": 1.5, "relaxed": 1.75 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0.5rem", "md": "0.75rem", "lg": "1rem", "xl": "1.5rem", "full": "9999px" },
  "shadows": {
    "sm": "3px 3px 6px #b8b9be, -3px -3px 6px #ffffff",
    "md": "5px 5px 10px #b8b9be, -5px -5px 10px #ffffff",
    "lg": "8px 8px 16px #b8b9be, -8px -8px 16px #ffffff",
    "xl": "12px 12px 24px #b8b9be, -12px -12px 24px #ffffff"
  }
}
```

---

### 4. glassmorphism

**Vibe:** Frosted glass, depth, modern — translucent layers
**Best for:** Modern SaaS, trendy products

```json
{
  "colors": {
    "primary": "#7C3AED",
    "secondary": "#2DD4BF",
    "accent": "#F472B6",
    "surface": "rgba(255, 255, 255, 0.25)",
    "surface_alt": "rgba(255, 255, 255, 0.15)",
    "text": "#1E293B",
    "text_secondary": "#64748B",
    "border": "rgba(255, 255, 255, 0.3)",
    "success": "#34D399",
    "warning": "#FBBF24",
    "error": "#F87171",
    "info": "#60A5FA"
  },
  "typography": {
    "heading_font": "Plus Jakarta Sans, sans-serif",
    "body_font": "Plus Jakarta Sans, sans-serif",
    "mono_font": "JetBrains Mono, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
      "xl": "1.25rem", "2xl": "1.5rem", "3xl": "1.875rem", "4xl": "2.25rem"
    },
    "weights": { "normal": 400, "medium": 500, "semibold": 600, "bold": 700 },
    "line_heights": { "tight": 1.25, "normal": 1.5, "relaxed": 1.75 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0.5rem", "md": "0.75rem", "lg": "1rem", "xl": "1.5rem", "full": "9999px" },
  "shadows": {
    "sm": "0 2px 8px rgba(0,0,0,0.1)",
    "md": "0 8px 32px rgba(0,0,0,0.12)",
    "lg": "0 16px 48px rgba(0,0,0,0.15)",
    "xl": "0 24px 64px rgba(0,0,0,0.18)"
  }
}
```

**Note:** Glassmorphism requires `backdrop-filter: blur(16px)` on surface elements.

---

### 5. skeuomorphism

**Vibe:** Familiar, physical, textured — like real-world objects
**Best for:** Familiarity, older demographics

```json
{
  "colors": {
    "primary": "#2E7D32",
    "secondary": "#5D4037",
    "accent": "#FF8F00",
    "surface": "#F5F0EB",
    "surface_alt": "#EDE7E0",
    "text": "#3E2723",
    "text_secondary": "#6D4C41",
    "border": "#BCAAA4",
    "success": "#2E7D32",
    "warning": "#FF8F00",
    "error": "#C62828",
    "info": "#1565C0"
  },
  "typography": {
    "heading_font": "Georgia, Times New Roman, serif",
    "body_font": "Verdana, Geneva, sans-serif",
    "mono_font": "Courier New, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
      "xl": "1.25rem", "2xl": "1.5rem", "3xl": "1.875rem", "4xl": "2.25rem"
    },
    "weights": { "normal": 400, "medium": 500, "semibold": 600, "bold": 700 },
    "line_heights": { "tight": 1.3, "normal": 1.6, "relaxed": 1.8 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0.25rem", "md": "0.375rem", "lg": "0.5rem", "xl": "0.625rem", "full": "9999px" },
  "shadows": {
    "sm": "0 1px 2px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.3)",
    "md": "0 3px 6px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.25)",
    "lg": "0 6px 12px rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.2)",
    "xl": "0 10px 20px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.15)"
  }
}
```

---

### 6. neubrutalism

**Vibe:** Bold, raw, unapologetic — thick borders, loud colors
**Best for:** Young/edgy, Gen Z products

```json
{
  "colors": {
    "primary": "#FF6B6B",
    "secondary": "#4ECDC4",
    "accent": "#FFE66D",
    "surface": "#FFFFFF",
    "surface_alt": "#FFF8E1",
    "text": "#000000",
    "text_secondary": "#333333",
    "border": "#000000",
    "success": "#4ECDC4",
    "warning": "#FFE66D",
    "error": "#FF6B6B",
    "info": "#45B7D1"
  },
  "typography": {
    "heading_font": "Space Grotesk, sans-serif",
    "body_font": "Space Grotesk, sans-serif",
    "mono_font": "Space Mono, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.25rem",
      "xl": "1.5rem", "2xl": "2rem", "3xl": "2.5rem", "4xl": "3rem"
    },
    "weights": { "normal": 400, "medium": 500, "semibold": 700, "bold": 800 },
    "line_heights": { "tight": 1.1, "normal": 1.4, "relaxed": 1.6 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0", "md": "0.25rem", "lg": "0.5rem", "xl": "0.75rem", "full": "9999px" },
  "shadows": {
    "sm": "2px 2px 0 #000000",
    "md": "4px 4px 0 #000000",
    "lg": "6px 6px 0 #000000",
    "xl": "8px 8px 0 #000000"
  }
}
```

**Note:** Neubrutalism uses thick solid borders (2-3px black) instead of subtle borders.

---

### 7. bauhaus

**Vibe:** Geometric, primary colors, form-follows-function
**Best for:** Design-forward, artistic

```json
{
  "colors": {
    "primary": "#D32F2F",
    "secondary": "#1976D2",
    "accent": "#FBC02D",
    "surface": "#FAFAFA",
    "surface_alt": "#F5F5F5",
    "text": "#212121",
    "text_secondary": "#757575",
    "border": "#BDBDBD",
    "success": "#388E3C",
    "warning": "#FBC02D",
    "error": "#D32F2F",
    "info": "#1976D2"
  },
  "typography": {
    "heading_font": "Oswald, sans-serif",
    "body_font": "Roboto, sans-serif",
    "mono_font": "Roboto Mono, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
      "xl": "1.25rem", "2xl": "1.75rem", "3xl": "2.25rem", "4xl": "3rem"
    },
    "weights": { "normal": 400, "medium": 500, "semibold": 600, "bold": 700 },
    "line_heights": { "tight": 1.2, "normal": 1.5, "relaxed": 1.7 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0", "md": "0", "lg": "0", "xl": "0", "full": "50%" },
  "shadows": {
    "sm": "0 2px 4px rgba(0,0,0,0.1)",
    "md": "0 4px 8px rgba(0,0,0,0.12)",
    "lg": "0 8px 16px rgba(0,0,0,0.15)",
    "xl": "0 16px 32px rgba(0,0,0,0.18)"
  }
}
```

**Note:** Bauhaus uses sharp corners (border-radius: 0) except for deliberate circles (full: 50%).

---

### 8. claymorphism

**Vibe:** Soft, puffy, friendly — like clay or dough
**Best for:** Friendly, approachable products

```json
{
  "colors": {
    "primary": "#7C5CFC",
    "secondary": "#FF8A65",
    "accent": "#4DD0E1",
    "surface": "#F0EEFF",
    "surface_alt": "#E8E4FF",
    "text": "#2D2B55",
    "text_secondary": "#6E6B9A",
    "border": "#D4D0F0",
    "success": "#66BB6A",
    "warning": "#FFB74D",
    "error": "#EF5350",
    "info": "#42A5F5"
  },
  "typography": {
    "heading_font": "Nunito, sans-serif",
    "body_font": "Nunito, sans-serif",
    "mono_font": "Source Code Pro, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
      "xl": "1.25rem", "2xl": "1.5rem", "3xl": "1.875rem", "4xl": "2.25rem"
    },
    "weights": { "normal": 400, "medium": 600, "semibold": 700, "bold": 800 },
    "line_heights": { "tight": 1.3, "normal": 1.6, "relaxed": 1.8 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0.75rem", "md": "1rem", "lg": "1.5rem", "xl": "2rem", "full": "9999px" },
  "shadows": {
    "sm": "0 4px 8px rgba(124,92,252,0.15), inset 0 -2px 4px rgba(0,0,0,0.05)",
    "md": "0 8px 16px rgba(124,92,252,0.18), inset 0 -3px 6px rgba(0,0,0,0.06)",
    "lg": "0 12px 24px rgba(124,92,252,0.2), inset 0 -4px 8px rgba(0,0,0,0.07)",
    "xl": "0 16px 32px rgba(124,92,252,0.22), inset 0 -5px 10px rgba(0,0,0,0.08)"
  }
}
```

---

### 9. retro-futurism

**Vibe:** Neon + nostalgia, VHS tracking lines, 80s sci-fi
**Best for:** Gaming, entertainment

```json
{
  "colors": {
    "primary": "#FF00FF",
    "secondary": "#00FFFF",
    "accent": "#FFFF00",
    "surface": "#1A0033",
    "surface_alt": "#2A0052",
    "text": "#FFFFFF",
    "text_secondary": "#B794F6",
    "border": "#6B21A8",
    "success": "#00FF88",
    "warning": "#FFFF00",
    "error": "#FF0066",
    "info": "#00CCFF"
  },
  "typography": {
    "heading_font": "Orbitron, sans-serif",
    "body_font": "Rajdhani, sans-serif",
    "mono_font": "Share Tech Mono, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
      "xl": "1.25rem", "2xl": "1.5rem", "3xl": "2rem", "4xl": "2.5rem"
    },
    "weights": { "normal": 400, "medium": 500, "semibold": 600, "bold": 700 },
    "line_heights": { "tight": 1.2, "normal": 1.5, "relaxed": 1.7 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0", "md": "0.25rem", "lg": "0.5rem", "xl": "0.75rem", "full": "9999px" },
  "shadows": {
    "sm": "0 0 8px rgba(255,0,255,0.4)",
    "md": "0 0 16px rgba(255,0,255,0.5)",
    "lg": "0 0 32px rgba(255,0,255,0.5), 0 0 8px rgba(0,255,255,0.3)",
    "xl": "0 0 48px rgba(255,0,255,0.6), 0 0 16px rgba(0,255,255,0.4)"
  }
}
```

---

### 10. cyberpunk

**Vibe:** Dark, glitchy, neon-on-black, tech-dystopia
**Best for:** Edgy tech, gaming

```json
{
  "colors": {
    "primary": "#00F0FF",
    "secondary": "#FF003C",
    "accent": "#B6FF00",
    "surface": "#0D0D0D",
    "surface_alt": "#1A1A2E",
    "text": "#E0E0E0",
    "text_secondary": "#888888",
    "border": "#333355",
    "success": "#B6FF00",
    "warning": "#FFB800",
    "error": "#FF003C",
    "info": "#00F0FF"
  },
  "typography": {
    "heading_font": "Exo 2, sans-serif",
    "body_font": "IBM Plex Sans, sans-serif",
    "mono_font": "IBM Plex Mono, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
      "xl": "1.25rem", "2xl": "1.5rem", "3xl": "2rem", "4xl": "2.5rem"
    },
    "weights": { "normal": 400, "medium": 500, "semibold": 600, "bold": 700 },
    "line_heights": { "tight": 1.2, "normal": 1.5, "relaxed": 1.7 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0", "md": "0.125rem", "lg": "0.25rem", "xl": "0.5rem", "full": "9999px" },
  "shadows": {
    "sm": "0 0 6px rgba(0,240,255,0.3)",
    "md": "0 0 12px rgba(0,240,255,0.4)",
    "lg": "0 0 24px rgba(0,240,255,0.4), 0 0 6px rgba(255,0,60,0.2)",
    "xl": "0 0 48px rgba(0,240,255,0.5), 0 0 12px rgba(255,0,60,0.3)"
  }
}
```

---

### 11. dark-mode

**Vibe:** Refined dark, professional, easy on the eyes
**Best for:** Developer tools, media apps

```json
{
  "colors": {
    "primary": "#818CF8",
    "secondary": "#34D399",
    "accent": "#FBBF24",
    "surface": "#111827",
    "surface_alt": "#1F2937",
    "text": "#F9FAFB",
    "text_secondary": "#9CA3AF",
    "border": "#374151",
    "success": "#34D399",
    "warning": "#FBBF24",
    "error": "#F87171",
    "info": "#60A5FA"
  },
  "typography": {
    "heading_font": "Inter, system-ui, sans-serif",
    "body_font": "Inter, system-ui, sans-serif",
    "mono_font": "JetBrains Mono, Fira Code, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
      "xl": "1.25rem", "2xl": "1.5rem", "3xl": "1.875rem", "4xl": "2.25rem"
    },
    "weights": { "normal": 400, "medium": 500, "semibold": 600, "bold": 700 },
    "line_heights": { "tight": 1.25, "normal": 1.5, "relaxed": 1.75 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0.25rem", "md": "0.375rem", "lg": "0.5rem", "xl": "0.75rem", "full": "9999px" },
  "shadows": {
    "sm": "0 1px 2px rgba(0,0,0,0.3)",
    "md": "0 4px 6px rgba(0,0,0,0.4)",
    "lg": "0 10px 15px rgba(0,0,0,0.5)",
    "xl": "0 20px 25px rgba(0,0,0,0.6)"
  }
}
```

---

### 12. warmer-shades

**Vibe:** Warm, nostalgic, comfortable — earth tones and soft edges
**Best for:** Nostalgic, comfortable feel

```json
{
  "colors": {
    "primary": "#B45309",
    "secondary": "#92400E",
    "accent": "#D97706",
    "surface": "#FFFBEB",
    "surface_alt": "#FEF3C7",
    "text": "#451A03",
    "text_secondary": "#78350F",
    "border": "#D6C4A8",
    "success": "#65A30D",
    "warning": "#D97706",
    "error": "#DC2626",
    "info": "#0284C7"
  },
  "typography": {
    "heading_font": "Lora, Georgia, serif",
    "body_font": "Source Sans 3, sans-serif",
    "mono_font": "Source Code Pro, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
      "xl": "1.25rem", "2xl": "1.5rem", "3xl": "1.875rem", "4xl": "2.25rem"
    },
    "weights": { "normal": 400, "medium": 500, "semibold": 600, "bold": 700 },
    "line_heights": { "tight": 1.3, "normal": 1.6, "relaxed": 1.8 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0.375rem", "md": "0.5rem", "lg": "0.75rem", "xl": "1rem", "full": "9999px" },
  "shadows": {
    "sm": "0 1px 3px rgba(120,53,15,0.08)",
    "md": "0 4px 8px rgba(120,53,15,0.1)",
    "lg": "0 8px 16px rgba(120,53,15,0.12)",
    "xl": "0 16px 32px rgba(120,53,15,0.15)"
  }
}
```


---
## REFERENCE: wireframe-pattern-lookup

# Wireframe Pattern Lookup Table

> Deterministic mapping from app type to wireframe pattern. This is NOT AI creativity — it's a lookup. The AI identifies the app type; the pattern follows from this table.

## Primary Patterns (92% Case)

| App Type | Wireframe Pattern | Navigation | Content Area | Key Elements |
|----------|------------------|------------|-------------|-------------|
| `dashboard` | Sidebar + Top Nav + Content Grid + Cards | Collapsible sidebar (left), breadcrumb top bar | Grid of cards/widgets, charts, tables | Summary cards, data tables, charts, activity feed, quick actions |
| `chat` | Conversation List + Message Thread + Input Bar | Left panel (conversation list), no top nav needed | Message thread (center), optional right panel (details) | Contact/channel list, message bubbles, input with attachments, typing indicator |
| `wizard` | Step Indicator + Single Form Area + Next/Back | Step progress bar (top), minimal nav | Single form section (center), navigation buttons (bottom) | Progress steps, form fields, validation, prev/next buttons, summary step |
| `marketplace` | Search Bar + Filter Sidebar + Product Grid | Top search bar, left filter panel | Product card grid (center), pagination | Search input, category filters, price range, sort, product cards, cart icon |
| `tool` | Toolbar + Workspace + Properties Panel | Toolbar (top), tool palette (left optional) | Canvas/workspace (center), properties panel (right) | Tool buttons, canvas area, property editors, layers panel, zoom controls |
| `landing` | Hero + Features + Testimonials + CTA | Sticky top nav with CTA button | Full-width sections, stacked vertically | Hero with headline + CTA, feature grid, testimonial cards, pricing table, footer |
| `settings` | Tab List + Form Sections | Vertical tab list (left) or horizontal tabs (top) | Form sections per tab | Tab navigation, labeled form groups, toggles, save/cancel buttons |

## Secondary Patterns (Variations)

### Dashboard Variations

| Variant | Description | When to Use |
|---------|-------------|-------------|
| Top Nav Only + Grid | No sidebar, horizontal nav with dropdowns | Simple dashboards with < 5 sections |
| Sidebar + Cards Only | No top nav, sidebar handles all navigation | Data-heavy dashboards, admin panels |
| Tabbed Dashboard | Tab bar at top, each tab is a dashboard view | Multi-role dashboards (e.g., admin vs user view) |

### Chat Variations

| Variant | Description | When to Use |
|---------|-------------|-------------|
| Full-width Thread | No conversation list visible, toggle to switch | Mobile-first chat, single-conversation focus |
| Chat + Sidebar Widgets | Conversation list + thread + right sidebar with tools | Support/helpdesk apps with customer context |
| Threaded Channels | Channel list + thread + nested replies | Team communication (Slack-like) |

### Wizard Variations

| Variant | Description | When to Use |
|---------|-------------|-------------|
| Sidebar Steps | Steps listed in left sidebar instead of top bar | Complex wizards with 8+ steps |
| Card-per-Step | Each step is a card, all visible, expand on click | Short wizards (3-4 steps) where overview matters |
| Modal Wizard | Wizard in a modal overlay | Secondary flows (e.g., onboarding after signup) |

### Marketplace Variations

| Variant | Description | When to Use |
|---------|-------------|-------------|
| Map + List | Split view: map (left/top) + list (right/bottom) | Location-based marketplaces (Airbnb-like) |
| Gallery Grid | No filter sidebar, full-width masonry grid | Visual-first marketplaces (art, photography) |
| Category Browse | Category cards → subcategory → product list | Deep catalog with hierarchical categories |

### Tool Variations

| Variant | Description | When to Use |
|---------|-------------|-------------|
| Split Pane | Two resizable panes (e.g., code editor + preview) | Editor/IDE tools, diff viewers |
| Canvas Only | Full-screen canvas, floating toolbars | Drawing/design tools, whiteboard apps |
| Command Palette | Minimal UI, keyboard-driven with command palette | Developer tools, power-user interfaces |

### Landing Variations

| Variant | Description | When to Use |
|---------|-------------|-------------|
| Single Page Scroll | All sections on one page, smooth scroll between | Simple products with one offering |
| Multi-page Marketing | Landing + separate pages for features, pricing, docs | Complex products needing deep content |
| App-Shell Landing | Landing that transitions into the app (no full reload) | SaaS products with free-tier access |

## Hybrid Pattern Resolution

When an app combines two types (e.g., dashboard + chat):

1. Identify the DOMINANT type — what does the user spend 70%+ of their time doing?
2. Use the dominant type's pattern as the PRIMARY arrangement
3. Embed the secondary type as a component WITHIN the primary layout:
   - Chat in a dashboard → Chat panel in sidebar or slide-out drawer
   - Dashboard in a tool → Stats widgets in the tool's properties panel
   - Marketplace with chat → Chat as a modal/drawer from product detail
4. Present BOTH the pure dominant pattern AND the hybrid as separate arrangement options

## Archetype-to-App-Type Mapping

| Archetype Keywords | App Type |
|-------------------|----------|
| productivity, admin, analytics, monitoring, CRM, ERP | `dashboard` |
| messaging, communication, support, helpdesk | `chat` |
| onboarding, form-builder, survey, checkout, registration | `wizard` |
| e-commerce, listings, search-browse, two-sided | `marketplace` |
| editor, builder, IDE, canvas, designer | `tool` |
| marketing, portfolio, product-page, SaaS-homepage | `landing` |
| preferences, configuration, profile, account | `settings` |

If the archetype contains keywords from multiple types, it's a hybrid — follow the hybrid resolution above.



---

## 🔗 Pipeline Integration — Automatic Stage Advancement

**This section is added for pipeline automation. It tells you how to signal stage completion.**

After completing ALL steps above and producing your complete output:

### Stage Completion Protocol

1. **Verify your confidence score** meets the gate threshold (≥ 70)
2. **Verify the complete JSON output** has been produced and meets the contract
3. **Output the completion marker** on its own line as the ABSOLUTE LAST thing in your response:

```
[STAGE_COMPLETE]
```

### Rules for the completion marker:

- `[STAGE_COMPLETE]` MUST be the absolute last thing in your response — nothing after it
- Your complete JSON output (context_packet) MUST come BEFORE the marker
- **Never** output `[STAGE_COMPLETE]` until the stage contract is fully met
- **Never** output `[STAGE_COMPLETE]` if the confidence score is below 70
- If you need to ask the user questions, do **NOT** output `[STAGE_COMPLETE]` — wait for answers first, produce your final output, THEN output the marker
- If the gate_result is "fail" (score < 70), trigger the escape hatch protocol instead — do NOT output `[STAGE_COMPLETE]`

### What happens when you output [STAGE_COMPLETE]:

1. The pipeline captures everything before the marker as your stage output
2. Your output becomes the input for the next stage
3. The next stage starts automatically — no manual intervention needed

### Example — end of your response:

```json
{
  "stage_6": { ... your complete output ... },
  "metadata": {
    "confidence_scores": {
      "6": { "score": 93, "gate_result": "pass" }
    }
  }
}
```

[STAGE_COMPLETE]


================================================================================
STAGE 7: PHASE SEQUENCING
================================================================================

---
name: stage-07-phase-sequencing
description: Split a complete PRD spec into token-budgeted build phases with file sandboxes, build orders, and dependency mapping.
---

## Purpose

Takes a complete spec (mechanisms scaffolded with Wall/Door/Room classifications, wireframes approved, style selected from Stages 0–6) and splits it into buildable phases using math-based token budget calculations. Each phase becomes a self-contained containment unit with its own file sandbox, forced build order, and explicit dependency mapping. Stage 7 does the structural split; Stage 8 injects enforcement protocols.

## When to Use

Activate when ALL of the following are present in the context packet:
- `stage_5.mechanism_blueprints` — mechanisms with W/D/R classifications
- `stage_4.mechanisms` and `stage_4.mechanism_dependencies` — mechanism list and dependency graph
- `stage_6.sub_6a`, `stage_6.sub_6b`, `stage_6.sub_6c.design_tokens` — wireframes and style
- `stage_3.drift_anchor` and `stage_2.scope_contract` — product identity and scope

This skill produces: `stage_7.token_budget`, `stage_7.phases`, `stage_7.mandatory_build_order`.

## Input Format

```json
{
  "stage_2": { "scope_contract": "..." },
  "stage_3": { "drift_anchor": "..." },
  "stage_4": {
    "mechanisms": [{ "id": "M1", "name": "...", "tags": ["OBVIOUS"] }],
    "mechanism_dependencies": [{ "from": "M1", "to": "M2" }]
  },
  "stage_5": {
    "mechanism_blueprints": [{ "mechanism_id": "M1", "wdr_classification": {...} }]
  },
  "stage_6": {
    "sub_6a": { "arrangement_type": "...", "wireframe_pattern": "..." },
    "sub_6b": [{ "page_name": "...", "components": [...], "mechanism_connections": [...] }],
    "sub_6c": { "design_tokens": { "colors": {...}, "typography": {...} } }
  },
  "stage_0": { "tech_stack": { "framework": "...", "language": "..." } }
}
```

## Process

### Step 1: Estimate Total Token Count

Aggregate all build content from Stages 3–6. For each mechanism blueprint, estimate tokens based on complexity:
- Simple mechanism (1–2 files, WALL-dominant): ~15,000–25,000 tokens
- Medium mechanism (3–5 files, mixed W/D/R): ~30,000–60,000 tokens
- Complex mechanism (6+ files, DOOR/ROOM-heavy): ~60,000–120,000 tokens

Add per-page UI tokens from Stage 6b (~5,000–15,000 tokens per page depending on component count). Sum all estimates to get `total_spec_tokens`.

### Step 2: Calculate Phase Count

Apply the formula (see [references/token-budget-math.md](references/token-budget-math.md)):

```
total_budget = 500,000 tokens (50% of 1M context)
overhead_per_phase = 25,000 tokens (fixed)
budget_per_phase_content = 325,000 tokens
phases_needed = ceil(total_spec_tokens / 325,000)
```

Minimum 1 phase. If `total_spec_tokens` ≤ 325,000, use 1 phase.

### Step 3: Find Natural Break Points

1. Sort mechanisms by dependency order (topological sort using `stage_4.mechanism_dependencies`).
2. Walk the sorted list, accumulating token estimates.
3. When accumulated tokens approach 325,000, look for the nearest mechanism boundary.
4. NEVER split a mechanism across phases. If a mechanism straddles the boundary, keep it in whichever phase maintains the best fit.
5. Keep tightly-coupled mechanisms together (check dependency edges — if M1→M2, prefer same phase).
6. Verify: every mechanism appears in exactly one phase.

### Step 4: Assign File Sandboxes

For each phase, derive file paths from the mechanisms' blueprints and Stage 6b page layouts. Classify into three tiers (see [references/file-sandbox-template.md](references/file-sandbox-template.md)):

- **files_allowed**: Exact file paths this phase creates or modifies. Mark each as NEW or MODIFY.
- **files_read_only**: Files from prior phases this phase can reference for patterns (e.g., auth patterns, DB helpers). Always include CLAUDE.md.
- **files_forbidden**: Everything else. Explicitly list critical files: `.env`, existing migrations, config files, and files owned by other phases.
- **do_not_change**: Global protections that apply to ALL phases: `CLAUDE.md`, `.env`, `BUILD_RULES.md`, existing migration files.

### Step 5: Define Build Order Per Phase

Within each phase, define a forced linear sequence following Martin's pattern (see [references/build-order-patterns.md](references/build-order-patterns.md)):

1. **Core logic** — Business logic, utilities, helpers, types
2. **State management** — Contexts, stores, hooks, data fetching
3. **UI components** — Pages, components, forms
4. **Integration** — Route wiring, exports, entry points

Every file in `files_allowed` MUST appear in `build_order`. Each entry includes `file_path`, `operation` ("create" or "modify"), and `rationale` explaining its position.

### Step 6: Define Phase Dependencies

- Phase 1 always has `depends_on: []`.
- Default: sequential (Phase N depends on Phase N-1).
- If two phases share no mechanism dependencies and no file overlaps, they MAY run in parallel (rare).
- Dependencies must form a DAG — verify no cycles.

### Step 7: Verify Fit

For each phase, confirm:
- `estimated_tokens + 25,000 (overhead) ≤ 350,000`
- If exceeded, move the last mechanism to the next phase and recalculate.
- Confirm: `sum(all phases' estimated_tokens) ≈ total_spec_tokens` (±10%).
- Do NOT compress content to fit. Adjust split points instead.

## Output Format

Written to `context_packet.stage_7`:

```json
{
  "token_budget": {
    "total_spec_tokens": 650000,
    "budget_per_phase_content": 325000,
    "overhead_per_phase": 25000,
    "total_budget": 500000,
    "phases_needed": 2
  },
  "phases": [
    {
      "phase_number": 1,
      "name": "Core Auth & Data Layer",
      "mechanism_ids": ["M1", "M2", "M3"],
      "estimated_tokens": 310000,
      "build_order": [
        { "file_path": "src/lib/auth.ts", "operation": "create", "rationale": "Core auth logic — all other files depend on this" },
        { "file_path": "src/contexts/AuthContext.tsx", "operation": "create", "rationale": "State wrapper for auth — needed by UI" },
        { "file_path": "src/pages/SignIn.tsx", "operation": "create", "rationale": "UI consumes AuthContext" },
        { "file_path": "src/App.tsx", "operation": "modify", "rationale": "Wire auth routes — integration last" }
      ],
      "files_allowed": ["src/lib/auth.ts", "src/contexts/AuthContext.tsx", "src/pages/SignIn.tsx", "src/pages/SignUp.tsx", "src/App.tsx"],
      "files_read_only": ["CLAUDE.md", "package.json"],
      "files_forbidden": ["src/lib/supabase.ts", ".env", "supabase/migrations/*"],
      "depends_on": [],
      "do_not_change": ["CLAUDE.md", ".env", "BUILD_RULES.md"]
    }
  ],
  "mandatory_build_order": [
    { "rule": "Core logic files before state management", "phases_affected": [1, 2] },
    { "rule": "State management before UI components", "phases_affected": [1, 2] },
    { "rule": "UI components before integration/routing", "phases_affected": [1, 2] }
  ]
}
```

Also update metadata:
```json
{
  "metadata.current_stage": 7,
  "metadata.stage_timestamps.7": "ISO-8601",
  "metadata.confidence_scores.7": { "score": 92, "dimensions": {...} }
}
```

## Edge Cases

### Missing Input

If `stage_4.mechanisms` is empty or missing: trigger escape hatch. Phase sequencing requires a mechanism list — there is nothing to split.

If `stage_6.sub_6b` (page mockups) is missing: proceed with mechanism-only file inference. Flag `handoff_readiness` confidence dimension as reduced (max 12/20). Build orders will lack specific page/component paths.

If `stage_4.mechanism_dependencies` is missing: treat all mechanisms as independent. Default to sequential phases ordered by mechanism complexity (simplest first). Flag in metadata.

### Ambiguous Input

If a mechanism has no clear file mapping (no page in Stage 6b references it): create a placeholder path based on the mechanism name and tech stack conventions (e.g., `src/lib/{mechanism-name-kebab}.ts`). Add a warning to the phase noting the inferred path.

If mechanism token estimates vary by >50% depending on interpretation: use the higher estimate. It is safer to have extra phases than to overflow.

### Scope Overflow

If total estimated tokens exceed 2,000,000 (would produce 7+ phases): flag as `NEEDS_HUMAN` with message "Spec is unusually large ({N} tokens). Consider splitting into separate projects." Still produce the phase list but mark confidence as ≤ 70.

If a single mechanism exceeds 325,000 tokens: it cannot fit in one phase. Flag as `NEEDS_HUMAN` with message "Mechanism {id} exceeds single-phase budget. It must be decomposed before phase sequencing."

## Confidence Scoring

Score each dimension 0–20 after producing output:

1. **Completeness** (0–20): All mechanisms assigned to exactly one phase? All phases have 3-tier sandboxes, build orders with rationales, explicit dependencies?
2. **Accuracy** (0–20): Token estimates realistic for the tech stack? Mechanism groupings respect dependency order? File paths match Stage 0 conventions?
3. **Consistency** (0–20): Phase dependencies match mechanism dependencies? File sandboxes don't overlap (same file in "allowed" for two phases)? Build orders reference only sandbox files?
4. **Specificity** (0–20): File paths are exact (not "some auth file")? Token estimates are numbers? Build order rationales are concrete (not "needed later")?
5. **Handoff Readiness** (0–20): Could Stage 8 inject pulse checks after each build order entry? Are sandbox lists precise enough for `git diff` verification? Are phase boundaries unambiguous?

**Total = sum of all 5 (/100)**

- **≥ 90**: PASS — proceed to Stage 8.
- **70–89**: WARN — flag low dimensions in metadata, proceed with warning. Retry once if no human available.
- **< 70**: FAIL — trigger escape hatch. Do NOT write output forward.

## Escape Hatch

**Trigger when:**
- Required input fields missing and cannot be inferred (no mechanism list)
- Total spec tokens cannot be estimated (Stages 3–6 output is empty)
- A mechanism has no file mapping and cannot be inferred
- Mechanism dependencies form a cycle preventing clean phase split
- Confidence score < 70 after one retry
- Single mechanism exceeds 325,000 tokens

**Save:**
- Partial `stage_7` with whatever phases were successfully created
- Step number where halt occurred
- Which mechanisms were assigned vs. unassigned
- Token budget calculation (even if incomplete)
- Suggested questions for the human

**Signal:**
```json
{
  "metadata.status": "needs_human",
  "metadata.escape_hatches": [{
    "stage": 7,
    "step": "Step N description",
    "reason": "Specific problem",
    "mechanisms_assigned": ["M1", "M2"],
    "mechanisms_unassigned": ["M5"],
    "suggested_actions": ["Decompose mechanism M5", "Clarify file mapping for M5"]
  }]
}
```

## Example

**Input:** A task management app with 4 mechanisms (Auth, Tasks CRUD, Dashboard, Notifications) totaling ~580,000 estimated tokens.

**Token math:**
```
total_spec_tokens = 580,000
phases_needed = ceil(580,000 / 325,000) = 2
```

**Phase split** (at mechanism boundary between Tasks CRUD and Dashboard):

Phase 1 — "Auth & Task Engine" (~290K content + 25K overhead = 315K):
- Mechanisms: M1 (Auth, ~120K), M2 (Tasks CRUD, ~170K)
- Build order: `src/lib/auth.ts` → `src/lib/tasks.ts` → `src/contexts/AuthContext.tsx` → `src/contexts/TaskContext.tsx` → `src/pages/SignIn.tsx` → `src/pages/TaskList.tsx` → `src/pages/TaskDetail.tsx` → modify `src/App.tsx`
- files_allowed: all 8 files above
- files_read_only: `CLAUDE.md`, `package.json`, `tsconfig.json`
- files_forbidden: `.env`, `src/pages/Dashboard.tsx`, `src/lib/notifications.ts`

Phase 2 — "Dashboard & Notifications" (~290K + 25K = 315K):
- Mechanisms: M3 (Dashboard, ~160K), M4 (Notifications, ~130K)
- Build order: `src/lib/dashboard.ts` → `src/lib/notifications.ts` → `src/contexts/NotificationContext.tsx` → `src/pages/Dashboard.tsx` → `src/pages/NotificationSettings.tsx` → modify `src/App.tsx`
- files_allowed: all 6 files above
- files_read_only: `src/lib/auth.ts`, `src/lib/tasks.ts`, `src/contexts/AuthContext.tsx`, `CLAUDE.md`
- files_forbidden: `.env`, Phase 1's UI files
- depends_on: [1]

**Verification:** 290K + 25K = 315K ≤ 350K ✓ for both phases. All 4 mechanisms assigned. No splits. DAG is valid (2→1). Confidence: 94/100.


---
## REFERENCE: build-order-patterns

# Build Order Patterns — Phase Sequencing Reference

## Martin's Pattern: The Four Layers

Every phase follows the same forced linear sequence. This is derived from Martin's structural checklist and ensures predictable, auditable builds.

```
Layer 1: CORE LOGIC      — Business logic, utilities, helpers, types, database schemas
Layer 2: STATE MANAGEMENT — Contexts, stores, hooks, data fetching, API clients
Layer 3: UI COMPONENTS    — Pages, components, forms, modals, layouts
Layer 4: INTEGRATION      — Route wiring, exports, entry points, app configuration
```

## Why This Order

- **Core logic first**: Everything downstream depends on the types, utilities, and business rules defined here. Building UI before logic forces the agent to make assumptions that it later has to fix.
- **State second**: State management wraps core logic and exposes it to UI. Without it, UI components can't access data.
- **UI third**: With logic and state in place, UI components are straightforward — they consume hooks and call functions. No guessing.
- **Integration last**: Wiring routes and exports is the final step that connects everything. Doing it earlier means wiring to components that don't exist yet.

## Concrete Examples By Tech Stack

### React + TypeScript

```
1. src/lib/auth.ts              (core logic — auth functions)
2. src/lib/validators.ts        (core logic — validation rules)
3. src/types/user.ts            (core logic — type definitions)
4. src/contexts/AuthContext.tsx  (state — wraps auth logic)
5. src/hooks/useAuth.ts         (state — hook for consuming auth)
6. src/pages/SignIn.tsx          (UI — sign-in page)
7. src/pages/SignUp.tsx          (UI — sign-up page)
8. src/components/AuthGuard.tsx  (UI — route protection component)
9. src/App.tsx                   (integration — add routes)
```

### Next.js + TypeScript

```
1. src/lib/db.ts                (core logic — database client)
2. src/lib/auth.ts              (core logic — auth utilities)
3. src/types/index.ts           (core logic — type definitions)
4. src/app/api/auth/route.ts    (state/API — auth API route)
5. src/hooks/useAuth.ts         (state — client-side auth hook)
6. src/app/sign-in/page.tsx     (UI — sign-in page)
7. src/app/sign-up/page.tsx     (UI — sign-up page)
8. src/middleware.ts             (integration — route protection)
9. src/app/layout.tsx            (integration — layout wrapper)
```

### Python + FastAPI

```
1. src/models/user.py           (core logic — data models)
2. src/services/auth_service.py (core logic — business logic)
3. src/schemas/user.py          (core logic — Pydantic schemas)
4. src/dependencies/auth.py     (state — dependency injection)
5. src/routers/auth.py          (UI/API — route handlers)
6. src/main.py                  (integration — register router)
```

### Flutter + Dart

```
1. lib/models/user.dart         (core logic — data models)
2. lib/services/auth_service.dart (core logic — business logic)
3. lib/providers/auth_provider.dart (state — state management)
4. lib/screens/sign_in_screen.dart  (UI — sign-in screen)
5. lib/screens/sign_up_screen.dart  (UI — sign-up screen)
6. lib/app.dart                     (integration — route registration)
```

## Build Order Entry Format

Each entry in the `build_order` array MUST have:

```json
{
  "file_path": "src/lib/auth.ts",
  "operation": "create",
  "rationale": "Core auth logic — session management, token validation. All auth UI and state depend on this."
}
```

### Operation Values

| Value | When to Use |
|-------|-------------|
| `create` | File does not exist, phase creates it from scratch |
| `modify` | File exists (from a prior phase or boilerplate), phase adds to or changes it |

### Rationale Guidelines

Good rationales explain WHY this file is at this position:
- "Core auth logic — all auth UI depends on these functions"
- "State wrapper — must exist before any component can consume auth"
- "Page component — consumes AuthContext, must come after state layer"
- "Route wiring — final integration step, all pages must exist first"

Bad rationales (too vague — avoid these):
- "Needed for the app"
- "Important file"
- "Should come first"
- "Related to auth"

## Cross-Phase Patterns

When a file is MODIFIED across phases (e.g., `App.tsx` gets new routes in each phase):

- Phase 1: `{ "file_path": "src/App.tsx", "operation": "create", "rationale": "Initial app shell with auth routes" }`
- Phase 2: `{ "file_path": "src/App.tsx", "operation": "modify", "rationale": "Add dashboard routes — auth routes already wired" }`
- Phase 3: `{ "file_path": "src/App.tsx", "operation": "modify", "rationale": "Add settings routes — all prior routes stable" }`

The file appears in `files_allowed` for ALL phases that touch it, but only Phase 1 has `"create"`. Subsequent phases use `"modify"` and their rationale references what was already done.


---
## REFERENCE: file-sandbox-template

# File Sandbox Template — Phase Sequencing Reference

## The Three Tiers

Every phase MUST have all three tiers defined. No exceptions.

### Tier 1: FILES ALLOWED

Exact file paths this phase can create or modify. Be explicit — list every file path with its operation status.

```
files_allowed:
  - src/lib/auth.ts              (NEW — create from scratch)
  - src/contexts/AuthContext.tsx  (NEW — create from scratch)
  - src/pages/SignIn.tsx          (NEW — create from scratch)
  - src/pages/SignUp.tsx          (NEW — create from scratch)
  - src/App.tsx                   (MODIFY — add routes only)
  - supabase/migrations/00001_auth.sql (NEW — create migration)
```

**Rules:**
- Every file in `build_order` MUST appear here
- Mark each as NEW (create) or MODIFY (change existing)
- MODIFY files should specify WHAT is allowed (e.g., "add routes only", "add export")
- Keep the list precise — "src/components/*" is NOT acceptable, list each file

### Tier 2: FILES READ-ONLY

Files the phase can reference for patterns but MUST NOT modify. These are typically files from prior phases or global config.

```
files_read_only:
  - CLAUDE.md                     (global — always read-only)
  - package.json                  (reference for dependencies)
  - tsconfig.json                 (reference for paths)
  - src/lib/supabase.ts           (reference for DB pattern)
  - src/components/ui/Button.tsx  (reference for component pattern)
```

**Rules:**
- Always include CLAUDE.md
- Include files from prior phases that this phase needs to reference
- Include configuration files the agent might need to check
- A file can be READ-ONLY in one phase and ALLOWED in another (the phase that creates it has ALLOWED, subsequent phases have READ-ONLY)

### Tier 3: FILES FORBIDDEN

Everything not in ALLOWED or READ-ONLY. For critical files, list them explicitly even though "everything else" covers them.

```
files_forbidden:
  - .env                          (NEVER — contains secrets)
  - .env.local                    (NEVER — contains secrets)
  - supabase/migrations/00000_*.sql (existing migrations — never modify)
  - src/lib/credits.ts            (owned by Phase 2 — do not touch)
  - src/pages/Dashboard.tsx       (owned by Phase 2 — do not touch)
  - ANY files in node_modules/
  - ANY files in .git/
```

**Rules:**
- Explicitly list `.env` and `.env.local` (critical, never touch)
- Explicitly list existing migration files
- Explicitly list files owned by other phases
- Include `node_modules/` and `.git/`
- Use "ANY files not listed above" as the catch-all at the end

## DO NOT CHANGE Protections

Some files must NEVER be modified by ANY phase. These appear in every phase's `do_not_change` array AND in every phase's `files_forbidden`:

```
do_not_change (global):
  - CLAUDE.md
  - .env
  - .env.local
  - BUILD_RULES.md
  - package-lock.json (modify only via npm install, not directly)
  - Any existing migration files (those with numbers lower than this phase's migrations)
```

## Enforcement Model

The sandbox is an **alarm system, not a fence**. The agent CAN touch any file during the build. After it finishes:

1. `git diff --name-only $SNAPSHOT` captures every file created, modified, or deleted
2. The diff is compared against the phase's `files_allowed` list
3. Unauthorized changes trigger violation handling:
   - **LOW**: Touched shared types/config → log and proceed
   - **MEDIUM**: Modified another phase's file → review and decide (additive = proceed with caution, destructive = revert)
   - **HIGH**: Modified `.env`, deleted files, touched forbidden core → halt and revert

## Complete Phase Sandbox Example

```json
{
  "phase_number": 2,
  "name": "Dashboard & Analytics",
  "files_allowed": [
    "src/lib/dashboard.ts",
    "src/lib/analytics.ts",
    "src/contexts/DashboardContext.tsx",
    "src/pages/Dashboard.tsx",
    "src/pages/Analytics.tsx",
    "src/components/charts/BarChart.tsx",
    "src/components/charts/LineChart.tsx",
    "src/App.tsx"
  ],
  "files_read_only": [
    "CLAUDE.md",
    "package.json",
    "tsconfig.json",
    "src/lib/auth.ts",
    "src/contexts/AuthContext.tsx",
    "src/lib/supabase.ts"
  ],
  "files_forbidden": [
    ".env",
    ".env.local",
    "supabase/migrations/00001_auth.sql",
    "src/pages/SignIn.tsx",
    "src/pages/SignUp.tsx",
    "src/contexts/AuthContext.tsx",
    "node_modules/**",
    ".git/**"
  ],
  "do_not_change": [
    "CLAUDE.md",
    ".env",
    ".env.local",
    "BUILD_RULES.md"
  ]
}
```


---
## REFERENCE: token-budget-math

# Token Budget Math — Phase Sequencing Reference

## Constants

| Constant | Value | Rationale |
|----------|-------|-----------|
| Total context window | 1,000,000 tokens | Claude 1M context |
| Total budget for spec content | 500,000 tokens | 50% of context — other 50% is agent working memory, tools, system prompts |
| Overhead per phase | 25,000 tokens | Fixed templated content (see breakdown below) |
| Content budget per phase | 325,000 tokens | 350,000 target minus 25,000 overhead |
| Target per phase (total) | 350,000 tokens | 35% of context — significant headroom below the 50% ceiling |

## Overhead Breakdown (Per Phase)

| Component | Tokens | Purpose |
|-----------|--------|---------|
| Build rules preamble | ~8,000 | Martin's structural rules, DO NOT CHANGE protections |
| File sandbox declaration | ~2,000 | ALLOWED / READ-ONLY / FORBIDDEN lists |
| Build order with pulse points | ~3,000 | Forced linear sequence with pulse check markers |
| Seam check definitions | ~2,000 | Connection-point verification rules |
| Full checkpoint at end | ~5,000 | End-of-phase pattern + functional verification |
| Pattern verification prompt | ~3,000 | Instructions for verifying build patterns |
| Violation handling | ~2,000 | Severity rules and escalation protocol |
| **Total** | **~25,000** | |

This overhead is predictable because it is templated. The preamble is the same text every time (with project-specific file lists swapped in). This allows advance calculation — account for overhead BEFORE splitting, not after.

## Phase Count Formula

```
phases_needed = ceil(total_spec_tokens / budget_per_phase_content)
             = ceil(total_spec_tokens / 325,000)
```

## Token Estimation Heuristics

### Per-Mechanism Estimates

| Complexity | Characteristics | Token Range |
|------------|----------------|-------------|
| Simple | 1–2 files, WALL-dominant, single concern | 15,000–25,000 |
| Medium | 3–5 files, mixed W/D/R, 2–3 connected components | 30,000–60,000 |
| Complex | 6+ files, DOOR/ROOM-heavy, integrations, multi-page | 60,000–120,000 |

### Per-Page UI Estimates (from Stage 6b)

| Page Type | Token Range |
|-----------|-------------|
| Simple static page (about, settings) | 5,000–8,000 |
| Form page (sign in, create item) | 8,000–12,000 |
| Dashboard / data-heavy page | 12,000–20,000 |
| Complex interactive page (editor, kanban) | 20,000–40,000 |

### Additional Content Estimates

| Content Type | Token Range |
|-------------|-------------|
| Database schema / migration | 3,000–8,000 per table |
| API route / endpoint | 5,000–10,000 per route |
| Shared utility / helper library | 3,000–6,000 per file |
| Type definitions | 2,000–5,000 per domain area |

## Worked Examples

### Example 1: Small App (1 Phase)

```
Mechanisms:
  M1 Auth (simple):     20,000 tokens
  M2 Profile (simple):  18,000 tokens
  M3 Settings (simple): 15,000 tokens
Total:                  53,000 tokens

phases_needed = ceil(53,000 / 325,000) = 1

Phase 1: 53,000 content + 25,000 overhead = 78,000 total
78,000 ≤ 350,000 ✓
```

### Example 2: Medium App (2 Phases)

```
Mechanisms:
  M1 Auth (medium):         45,000 tokens
  M2 Tasks CRUD (complex):  90,000 tokens
  M3 Dashboard (complex):   80,000 tokens
  M4 Notifications (medium):50,000 tokens
  M5 Search (medium):       40,000 tokens
  M6 Settings (simple):     20,000 tokens
Total:                     325,000 tokens

phases_needed = ceil(325,000 / 325,000) = 1

But check fit: 325,000 + 25,000 = 350,000 ≤ 350,000 ✓ (exactly at limit)
Keep as 1 phase, OR split to 2 for safety margin.

If split to 2:
  Phase 1 (M1+M2+M3): 215,000 + 25,000 = 240,000 ≤ 350,000 ✓
  Phase 2 (M4+M5+M6): 110,000 + 25,000 = 135,000 ≤ 350,000 ✓
```

### Example 3: Large App (3 Phases)

```
Mechanisms:
  M1 Auth (complex):           100,000 tokens
  M2 Payments (complex):       110,000 tokens
  M3 Content Editor (complex): 120,000 tokens
  M4 Analytics (complex):       95,000 tokens
  M5 Social (medium):           60,000 tokens
  M6 Admin Panel (complex):     80,000 tokens
  M7 Notifications (medium):    45,000 tokens
  M8 Search (medium):           40,000 tokens
Total:                         650,000 tokens

phases_needed = ceil(650,000 / 325,000) = 2

Check fit with 2 phases:
  Best split: M1+M2+M3 = 330,000 → 330,000 + 25,000 = 355,000 > 350,000 ✗
  Adjusted: M1+M2 = 210,000 → 210,000 + 25,000 = 235,000 ✓
            M3+M4+M5+M6+M7+M8 = 440,000 → 440,000 + 25,000 = 465,000 > 350,000 ✗

Need 3 phases:
  Phase 1 (M1+M2):       210,000 + 25,000 = 235,000 ✓
  Phase 2 (M3+M4):       215,000 + 25,000 = 240,000 ✓
  Phase 3 (M5+M6+M7+M8): 225,000 + 25,000 = 250,000 ✓

All phases ≤ 350,000 ✓
```

## Verification Checklist

After calculating phases:
- [ ] Every phase: `estimated_tokens + 25,000 ≤ 350,000`
- [ ] `sum(all phase estimated_tokens)` ≈ `total_spec_tokens` (±10%)
- [ ] `phases.length` ≈ `ceil(total_spec_tokens / 325,000)` (±1 for boundary adjustments)
- [ ] No mechanism split across phases
- [ ] No mechanism dropped (all mechanism IDs from Stage 4 appear in exactly one phase)



---

## 🔗 Pipeline Integration — Automatic Stage Advancement

**This section is added for pipeline automation. It tells you how to signal stage completion.**

After completing ALL steps above and producing your complete output:

### Stage Completion Protocol

1. **Verify your confidence score** meets the gate threshold (≥ 70)
2. **Verify the complete JSON output** has been produced and meets the contract
3. **Output the completion marker** on its own line as the ABSOLUTE LAST thing in your response:

```
[STAGE_COMPLETE]
```

### Rules for the completion marker:

- `[STAGE_COMPLETE]` MUST be the absolute last thing in your response — nothing after it
- Your complete JSON output (context_packet) MUST come BEFORE the marker
- **Never** output `[STAGE_COMPLETE]` until the stage contract is fully met
- **Never** output `[STAGE_COMPLETE]` if the confidence score is below 70
- If you need to ask the user questions, do **NOT** output `[STAGE_COMPLETE]` — wait for answers first, produce your final output, THEN output the marker
- If the gate_result is "fail" (score < 70), trigger the escape hatch protocol instead — do NOT output `[STAGE_COMPLETE]`

### What happens when you output [STAGE_COMPLETE]:

1. The pipeline captures everything before the marker as your stage output
2. Your output becomes the input for the next stage
3. The next stage starts automatically — no manual intervention needed

### Example — end of your response:

```json
{
  "stage_7": { ... your complete output ... },
  "metadata": {
    "confidence_scores": {
      "7": { "score": 93, "gate_result": "pass" }
    }
  }
}
```

[STAGE_COMPLETE]


================================================================================
STAGE 8: PROTOCOL INJECTION
================================================================================

---
name: stage-08-protocol-injection
description: Embed pulse/seam/full verification protocols inline into phased build orders from Stage 7.
---

## Purpose

Take phases from Stage 7 (with file sandboxes and build orders) and inject three tiers of verification checkpoints INTO them — pulse checks after every file, seam checks at mechanism connection points, full checkpoints at phase boundaries — producing self-verifying build units with embedded violation handling.

## When to Use

Activate when: `context_packet.stage_7.phases` exists AND `context_packet.stage_5.mechanism_blueprints` exists AND `context_packet.stage_4.mechanism_dependencies` exists. Trigger phrases: "protocol injection", "inject verification", "embed checks", "pulse seam full", "verification protocols", "inject protocols into phases".

Do NOT activate for: phase splitting (Stage 7), verification agent setup (Stage 9), output generation (Stage 10), or any layout/style work (Stage 6).

## Input Format

```json
{
  "stage_7": {
    "phases": [{
      "phase_number": 1,
      "name": "string",
      "mechanism_ids": ["string"],
      "estimated_tokens": 0,
      "build_order": ["src/file1.ts", "src/file2.tsx"],
      "files_allowed": ["string"],
      "files_read_only": ["string"],
      "files_forbidden": ["string"],
      "depends_on": [],
      "do_not_change": ["string"]
    }],
    "token_budget": {
      "total_spec_tokens": 0,
      "budget_per_phase_content": 0,
      "overhead_per_phase": 25000,
      "total_budget": 0,
      "phases_needed": 0
    }
  },
  "stage_5": {
    "mechanism_blueprints": [{
      "mechanism_id": "string",
      "steps": [{ "step": "string", "classification": "WALL|DOOR|ROOM" }]
    }]
  },
  "stage_4": {
    "mechanism_dependencies": [{
      "from_id": "string",
      "to_id": "string",
      "relationship": "string"
    }]
  }
}
```

## Process

### Step 1: Load and Index Phase Data

Read `stage_7.phases`. For each phase, index its `build_order` (file sequence), `files_allowed` (sandbox), and `mechanism_ids`. Build a lookup: `mechanism_id → phase_number` so you know which mechanisms live in which phase.

### Step 2: Build Dependency Interface Map

Read `stage_4.mechanism_dependencies`. For each dependency edge `(from_id, to_id)`, check if both mechanisms appear in the SAME phase. If yes, identify which file in the build order is the CONSUMER (imports from the other). That file is a seam check insertion point. Record: `{component_a, component_b, trigger_file}`.

If two connected mechanisms are in DIFFERENT phases, the seam check goes in the LATER phase at the first file that imports from the earlier phase's mechanism.

### Step 3: Insert Pulse Checks (Every File)

For EACH file in each phase's `build_order`, generate a pulse check:

1. Read the file's name and purpose from context (mechanism blueprints, file sandbox)
2. Generate SPECIFIC checks — not generic. Examples:
   - `auth.ts` → `["file exists", "exports loginUser function", "exports logoutUser function", "no syntax errors"]`
   - `AuthContext.tsx` → `["file exists", "exports AuthProvider component", "exports useAuth hook", "no syntax errors"]`
3. Assign `file_path` = the file from build_order

Use `references/protocol-tier-templates.md` for the check generation patterns. Every file gets a pulse check — no exceptions.

### Step 4: Insert Seam Checks at Connection Points

Using the interface map from Step 2, for each connection point within a phase:

1. Identify `component_a` (provider) and `component_b` (consumer)
2. Generate SPECIFIC verification: `"AuthContext.tsx imports from auth.ts and re-exports auth state"` — not generic `"A imports B"`
3. Place the seam check after the CONSUMER file in the build order (the file that creates the connection)

If a phase has NO mechanism interfaces (single-mechanism phase, no cross-mechanism connections), it gets zero seam checks. This is valid — pulse and full checkpoint still apply.

### Step 5: Define Full Checkpoint at Phase Boundary

For each phase, create a `full_checkpoint` with three parts:

**pattern_checks** — sandbox compliance via git diff:
- `"Run git diff --name-only $PHASE_N_BASELINE to list all modified files"`
- `"Compare modified files against files_allowed list"`
- `"Flag any file modified that is NOT in files_allowed"`
- `"Flag any file in build_order that was NOT created/modified"`
- `"Flag any unexpected imports from files outside sandbox"`

**functional_checks** — runtime verification (tech-stack-specific):
- Read `stage_0.tech_stack` to determine commands (e.g., `"npm run build"`, `"cargo build"`)
- Add phase-specific checks: `"Navigate to /sign-in route"`, `"Verify dashboard page renders"`
- Always include: compile check, existing features still work, new features render

**gate_condition** — binary pass/fail:
- `"ALL pattern_checks pass (zero unauthorized file modifications) AND ALL functional_checks pass (app compiles, new pages render, existing routes work). If ANY check fails, fix before next phase."`

### Step 6: Embed Violation Rules Per Phase

For each phase, populate the 4-level violation tree using `references/violation-decision-tree.md`. Customize triggers to the phase's specific sandbox:

- **low**: `triggers` reference that phase's shared files. `response`: `"log_and_proceed"`
- **medium**: `triggers` reference files from other phases' `files_allowed`. `response`: `"review_and_decide"`. Include `decision_tree`: `{"additive": "proceed_with_caution", "destructive": "revert_file", "unclear": "flag_human"}`
- **high**: `triggers`: file deletion, core config changes outside scope. `response`: `"revert_entire_phase"`
- **critical**: `triggers`: `.env`, `CLAUDE.md`, `package.json scripts`, build config, CI/CD. `response`: `"full_stop"`

### Step 7: Calculate Overhead and Validate Budget

For each phase, calculate `overhead_tokens` by summing the 7 overhead components (see `references/overhead-budget-breakdown.md`). Standard total: ~25,000 tokens.

**Validation checks:**
1. Every phase from Stage 7 has a corresponding `protocol_injected_phases` entry
2. Every file in every build_order has a pulse_check
3. Seam checks exist at every mechanism interface point within each phase
4. Every phase has full_checkpoint with both pattern_checks and functional_checks
5. violation_rules has all four severity levels for every phase
6. `overhead_tokens` ≤ 30,000 per phase
7. `estimated_tokens` (Stage 7) + `overhead_tokens` ≤ 350,000 per phase

If overhead exceeds 30,000 for any phase, trim verbose descriptions. If total exceeds 350,000, signal back to Stage 7 for re-splitting.

## Output Format

```json
{
  "stage_8": {
    "protocol_injected_phases": [
      {
        "phase_number": 1,
        "pulse_checks": [
          {
            "file_path": "src/lib/auth.ts",
            "checks": ["file exists", "exports loginUser", "exports logoutUser", "no syntax errors"]
          }
        ],
        "seam_checks": [
          {
            "component_a": "src/lib/auth.ts",
            "component_b": "src/contexts/AuthContext.tsx",
            "verification": "AuthContext imports loginUser and logoutUser from auth.ts"
          }
        ],
        "full_checkpoint": {
          "pattern_checks": ["git diff --name-only against files_allowed", "flag unauthorized modifications", "flag incomplete build_order items"],
          "functional_checks": ["npm run build succeeds", "navigate to /sign-in renders login form"],
          "gate_condition": "ALL pattern_checks pass AND ALL functional_checks pass. Fix before next phase."
        },
        "violation_rules": {
          "low": {
            "triggers": ["touched shared types file", "added import to existing utility"],
            "response": "log_and_proceed"
          },
          "medium": {
            "triggers": ["modified file from another phase's files_allowed"],
            "response": "review_and_decide",
            "decision_tree": {
              "additive": "proceed_with_caution",
              "destructive": "revert_file",
              "unclear": "flag_human"
            }
          },
          "high": {
            "triggers": ["deleted files", "modified core config outside scope"],
            "response": "revert_entire_phase"
          },
          "critical": {
            "triggers": ["modified .env", "modified CLAUDE.md", "modified build config"],
            "response": "full_stop"
          }
        },
        "overhead_tokens": 25000
      }
    ],
    "overhead_breakdown": {
      "build_rules_preamble": 8000,
      "file_sandbox_declaration": 2000,
      "build_order_with_pulse": 3000,
      "seam_check_definitions": 2000,
      "full_checkpoint": 5000,
      "pattern_verification": 3000,
      "violation_handling": 2000
    }
  },
  "metadata": {
    "current_stage": 8,
    "confidence_scores": {
      "8": { "score": 0, "dimensions": {}, "gate_result": "pass|flag|fail" }
    },
    "stage_timestamps": { "8": "ISO-8601" }
  }
}
```

## Edge Cases

### Missing Input

- No `stage_7.phases` → Escape hatch. Cannot inject protocols without phases.
- No `stage_4.mechanism_dependencies` → Proceed with zero seam checks per phase. Pulse and full checkpoint still apply. Log: `"No mechanism dependencies — seam checks skipped."`
- Empty `build_order` in a phase → Escape hatch for that phase. Cannot inject pulse checks into empty build order.

### Ambiguous Input

- Mechanism dependency exists but neither file is in the current phase's build_order → Skip this seam check for this phase. The seam belongs to whichever phase contains the consumer file.
- File appears in build_order but has no clear purpose from mechanism blueprints → Generate minimal pulse check: `["file exists", "no syntax errors"]`. Flag as `"generic_pulse"` in metadata.

### Scope Overflow

- If protocol injection reveals that a phase needs files not in its sandbox (e.g., seam check requires reading a file from another phase) → Do NOT modify the sandbox. Note it as a read dependency. Stage 7 already handles `files_read_only`.
- If overhead exceeds 30,000 tokens → Trim check descriptions to single-line commands. If still over, flag for Stage 7 re-split.

## Confidence Scoring

Score each dimension 0-20 after producing output:

1. **Completeness** (0-20): Every file has a pulse check? Every mechanism interface has a seam check? Every phase has full_checkpoint with pattern + functional checks? All 4 violation severity levels defined per phase?

2. **Accuracy** (0-20): Seam checks placed at actual mechanism interfaces (not arbitrary)? Functional checks match the tech stack (`npm run build` for Node, `cargo build` for Rust)? Violation triggers are realistic and specific to each phase's sandbox?

3. **Consistency** (0-20): Protocol-injected phases match Stage 7 phases exactly (same numbers, same files)? Seam check connection points align with Stage 4 dependency graph? Violation severity classification is uniform across all phases?

4. **Specificity** (0-20): Pulse checks verify specific exports per file (not generic "file works")? Seam checks name exact import relationships? Functional checks are executable commands? Gate conditions are binary pass/fail?

5. **Handoff Readiness** (0-20): Could Stage 9 configure a verifier agent from these protocols alone? Every check, threshold, and rollback action is explicit? No interpretation needed?

**Total = sum (/100).** ≥90: PASS. 70-89: WARN (flag, proceed). <70: FAIL (escape hatch).

## Escape Hatch

**When to trigger:**
- Required fields missing (no phases from Stage 7, no mechanism data from Stage 4)
- Phase build_order has zero files
- Mechanism dependencies are circular or unresolvable
- Overhead exceeds 30,000 tokens after trimming
- Confidence score < 70 after one retry

**What to save:**
- Current context_packet with whatever phases were successfully injected
- Stage number (8) and step where halt occurred
- Which phases were injected vs which failed
- Overhead calculations per phase
- Suggested human questions (e.g., "Phase 3 has no mechanism interfaces — confirm zero seam checks?")

**How to signal:**
- Set `metadata.status = "needs_human"`
- Add entry to `metadata.escape_hatches[]`: `{"stage": 8, "step": "string", "reason": "string", "suggested_actions": ["string"]}`
- Save context_packet snapshot
- Output structured `NEEDS_HUMAN` message

## Example

**Input:** Phase 1 "Auth System" with build_order: `[auth.ts, AuthContext.tsx, SignIn.tsx, SignUp.tsx, App.tsx(routes)]`. Mechanisms: `auth_core` depends on nothing. `auth_ui` depends on `auth_core`. Both in Phase 1.

**Protocol-injected output (inline):**

```
Phase 1: Auth System
├── BUILD ORDER with embedded protocols:
│   1. Create src/lib/auth.ts
│      └─ PULSE: [file exists, exports loginUser, exports logoutUser, no syntax errors]
│   2. Create src/contexts/AuthContext.tsx
│      └─ PULSE: [file exists, exports AuthProvider, exports useAuth hook, no syntax errors]
│   3. Create src/pages/SignIn.tsx
│      └─ PULSE: [file exists, exports SignIn component, no syntax errors]
│      └─ SEAM: SignIn.tsx imports useAuth from AuthContext ← AuthContext imports from auth.ts
│   4. Create src/pages/SignUp.tsx
│      └─ PULSE: [file exists, exports SignUp component, no syntax errors]
│   5. Wire routes in App.tsx
│      └─ PULSE: [file exists, routes array includes /sign-in and /sign-up, no syntax errors]
│      └─ SEAM: App.tsx routes point to SignIn and SignUp page components
│
├── FULL CHECKPOINT (gate):
│   ├─ Pattern: git diff --name-only vs files_allowed; flag unauthorized changes
│   ├─ Functional: npm run build succeeds; /sign-in renders; /sign-up renders
│   └─ Gate: ALL pass → proceed to Phase 2. ANY fail → fix first.
│
└── VIOLATION RULES:
    ├─ LOW: touched shared types → log, proceed
    ├─ MEDIUM: modified another phase's file → review (additive: proceed / destructive: revert)
    ├─ HIGH: deleted files or changed core config → revert entire phase
    └─ CRITICAL: modified .env, CLAUDE.md, build config → FULL STOP
```

Overhead: ~25,000 tokens. Phase estimated_tokens (Stage 7): 80,000. Total: 105,000 ≤ 350,000. ✅


---
## REFERENCE: overhead-budget-breakdown

# Overhead Budget Breakdown

## Standard Per-Phase Overhead (~25,000 tokens)

Every protocol-injected phase adds a fixed overhead on top of Stage 7's `estimated_tokens`. This overhead is predictable because it uses standardized templates.

| Component | Token Estimate | What It Contains |
|-----------|---------------|------------------|
| Build rules preamble | ~8,000 | Martin's structural rules applicable to this phase. Sourced from the agnostic checklist. Includes banned patterns, file naming conventions, component structure rules, state management rules. |
| File sandbox declaration | ~2,000 | `files_allowed`, `files_read_only`, `files_forbidden` lists with explanations. Includes "DO NOT MODIFY" warnings for protected files. |
| Build order with pulse points | ~3,000 | The ordered file list with pulse check definitions after each entry. More files = more tokens, but pulse checks are concise (~50 tokens each). |
| Seam check definitions | ~2,000 | Connection-point verification instructions. Typically 2-5 seam checks per phase at ~200-400 tokens each. Phases with no interfaces: ~200 tokens (just the "no seam checks needed" note). |
| Full checkpoint | ~5,000 | Pattern verification instructions (~2,000), functional check commands (~1,500), gate condition (~500), checkpoint summary format (~1,000). |
| Pattern verification prompt | ~3,000 | Instructions for the git diff process: how to run it, how to compare, how to interpret results, what to report. |
| Violation handling | ~2,000 | The 4-level decision tree with triggers and responses customized to this phase's sandbox. |
| **TOTAL** | **~25,000** | |

## Budget Validation Rules

1. **Per-phase overhead MUST be ≤ 30,000 tokens.** If it exceeds this after injection, trim verbose descriptions. Checks should be single-line commands, not paragraphs.

2. **Per-phase total MUST be ≤ 350,000 tokens.** Formula: `stage_7.phases[].estimated_tokens + overhead_tokens ≤ 350,000`. This leaves room for the Claude context window overhead (system prompt, tools, etc.).

3. **If overhead exceeds 30,000**, apply these trims in order:
   - Reduce build rules preamble to only the rules relevant to this phase's mechanisms (can drop to ~4,000)
   - Condense pulse checks to single-line format: `"PULSE: auth.ts → [exists, exports loginUser/logoutUser]"`
   - Merge similar seam checks
   - If still over: flag for Stage 7 to re-split the phase

4. **If total exceeds 350,000**, signal back to Stage 7 that this phase has too much content and needs to be split into sub-phases.

## Overhead Variation by Phase Size

| Phase Size (files) | Typical Pulse Overhead | Typical Seam Overhead | Total Overhead Range |
|--------------------|-----------------------|----------------------|---------------------|
| 2-5 files | ~500 tokens | ~400 tokens | 22,000 - 24,000 |
| 6-10 files | ~1,000 tokens | ~800 tokens | 24,000 - 26,000 |
| 11-15 files | ~1,500 tokens | ~1,200 tokens | 26,000 - 28,000 |
| 16+ files | ~2,000+ tokens | ~1,600+ tokens | 28,000 - 30,000 |

Phases with 16+ files are rare (Stage 7 typically caps at ~12 files per phase). If you see one, it's likely a candidate for splitting.

## Recording the Breakdown

The `overhead_breakdown` object in the output is a TEMPLATE — it records the standard budget allocation, not the per-phase actual. Per-phase actuals are in each phase's `overhead_tokens` field.

```json
{
  "overhead_breakdown": {
    "build_rules_preamble": 8000,
    "file_sandbox_declaration": 2000,
    "build_order_with_pulse": 3000,
    "seam_check_definitions": 2000,
    "full_checkpoint": 5000,
    "pattern_verification": 3000,
    "violation_handling": 2000
  }
}
```

This is the same for every run. Individual phase `overhead_tokens` may vary slightly based on file count and seam check count.


---
## REFERENCE: protocol-tier-templates

# Protocol Tier Templates

## Pulse Check Template (Per-File)

Generate after EVERY file in the build_order. Checks must be SPECIFIC to the file.

### Pattern: Determine checks from file type and purpose

| File Type | Standard Checks | Additional Checks |
|-----------|----------------|-------------------|
| Library/utility (`.ts`, `.py`) | file exists, no syntax errors | exports expected functions by name |
| React component (`.tsx`, `.jsx`) | file exists, no syntax errors | exports named component, accepts expected props |
| Context/Provider (`.tsx`) | file exists, no syntax errors | exports Provider component, exports custom hook |
| Page component (`.tsx`, `.jsx`) | file exists, no syntax errors | exports default/named page component |
| Route config (`App.tsx`, `router.ts`) | file exists, no syntax errors | route paths defined, routes point to imports |
| API route (`/api/*.ts`) | file exists, no syntax errors | exports handler function, correct HTTP method |
| Schema/model (`.prisma`, `.sql`) | file exists, no syntax errors | defines expected tables/models |
| Config file (`.config.ts`) | file exists, no syntax errors | exports config object |
| Style file (`.css`, `.scss`) | file exists | defines expected classes/tokens |
| Test file (`.test.ts`) | file exists, no syntax errors | imports subject under test, has test cases |

### Deriving "Expected Functions/Components"

Read the mechanism blueprint (`stage_5.mechanism_blueprints`) for the mechanism this file serves. Each WALL step = a deterministic function. Each DOOR step = a constrained AI function. Each ROOM step = a creative component. The exports should map to these steps.

Example: Mechanism "auth_core" has steps:
- WALL: "Hash password" → expect `hashPassword` export
- WALL: "Verify password" → expect `verifyPassword` export
- DOOR: "Validate email format" → expect `validateEmail` export

Pulse check for `auth.ts`: `["file exists", "exports hashPassword", "exports verifyPassword", "exports validateEmail", "no syntax errors"]`

## Seam Check Template (At Connection Points)

Place ONLY where two mechanisms interface. Derive placement from `stage_4.mechanism_dependencies`.

### Pattern: Identify the connection

1. Find the dependency edge: `from_id → to_id` (from provides, to consumes)
2. Find which file in the build_order belongs to the consumer mechanism
3. The seam check goes AFTER that consumer file

### Verification content

The verification string must name BOTH sides and the specific connection:

- Import check: `"[Consumer] imports [specific function/component] from [Provider]"`
- Data flow: `"[Consumer] passes [specific data] received from [Provider]"`
- Route wiring: `"Route [path] points to [PageComponent] which imports [required context]"`

### When NO seam checks apply

A phase with a single mechanism and no cross-mechanism dependencies within it gets zero seam checks. This is correct — not an error. Pulse checks and the full checkpoint still provide coverage.

## Full Checkpoint Template (Phase Boundary Gate)

Always placed at the END of each phase. Three mandatory parts:

### Pattern Checks (git diff verification)

Always include these 5 checks:
1. `"Run git diff --name-only $PHASE_N_BASELINE to list all actually modified files"`
2. `"Compare actual modified files against this phase's files_allowed list"`
3. `"FLAG: any file modified that is NOT in files_allowed"`
4. `"FLAG: any file in build_order that was NOT created or modified"`
5. `"FLAG: any new imports from files outside this phase's sandbox"`

### Functional Checks (runtime verification)

Determine from `stage_0.tech_stack`:

| Stack | Compile Check | Test Check | Render Check |
|-------|--------------|------------|--------------|
| Node/React | `npm run build` | `npm run test` (if tests exist) | Navigate to new routes |
| Python/Django | `python manage.py check` | `python manage.py test` | Hit new endpoints |
| Rust | `cargo build` | `cargo test` | Run binary with args |
| Flutter | `flutter analyze` | `flutter test` | Launch on emulator |
| Go | `go build ./...` | `go test ./...` | Run binary |

Add phase-specific checks: name the exact pages/routes/features this phase adds.

### Gate Condition

Always this format (customize the specifics):
`"ALL pattern_checks pass (zero unauthorized file modifications) AND ALL functional_checks pass ([compile command] succeeds, [specific pages] render, existing features still work). If ANY check fails, fix before Phase N+1 starts."`

The gate is BINARY: pass or fail. No "proceed with warnings" at the gate level — that's what violation severity handles.


---
## REFERENCE: violation-decision-tree

# Violation Decision Tree

## The Four Severity Levels

Every phase gets all four levels. Triggers are customized per phase based on its `files_allowed` sandbox.

```
VIOLATION DETECTED (via git diff comparison)
│
├─ LOW: Touched shared/common files
│   Triggers:
│   - Modified a shared types file (e.g., types.ts, interfaces.ts)
│   - Added an import to an existing utility file
│   - Added an export to a shared constants file
│   - Modified a shared config that multiple phases reference
│   Response: log_and_proceed
│   Action: Log the modification in the phase report. Note which file
│   was touched and why. Proceed with the build. Review at full checkpoint.
│
├─ MEDIUM: Modified another phase's domain file
│   Triggers:
│   - Modified a file listed in ANOTHER phase's files_allowed
│   - Added a new export to a file owned by another phase
│   - Changed import structure of a file from another phase
│   Response: review_and_decide
│   Decision Tree:
│   ├─ Additive change (added export, added prop, added route):
│   │   → proceed_with_caution — log it, continue, verify at checkpoint
│   ├─ Destructive change (renamed function, changed logic, removed export):
│   │   → revert_file — git checkout that specific file, re-run phase
│   │   with constraint: "Do NOT modify [file]"
│   └─ Unclear (can't determine if additive or destructive):
│       → flag_human — save state, present the diff, ask human to decide
│
├─ HIGH: Deleted files or changed core config outside scope
│   Triggers:
│   - Deleted any file (rm, unlink)
│   - Modified core config files outside this phase's scope
│   - Changed authentication logic outside the auth phase
│   - Modified database schema outside the data-model phase
│   - Changed environment variable definitions
│   Response: revert_entire_phase
│   Action: git reset --hard to phase baseline snapshot. Re-run with
│   tighter constraints or break the phase into smaller sub-phases.
│
└─ CRITICAL: Touched protected files
    Triggers:
    - Modified CLAUDE.md
    - Modified .env or any .env.* file
    - Modified package.json "scripts" section
    - Modified build configuration (vite.config, webpack.config, tsconfig)
    - Modified CI/CD configuration (.github/workflows, Dockerfile)
    - Modified security configuration (auth middleware, CORS settings)
    Response: full_stop
    Action: IMMEDIATELY STOP. Revert ALL changes. Flag for human review.
    This is either a prompt injection attempt or a fundamentally confused
    agent. Do NOT retry automatically. Human must inspect and approve
    before any further work.
```

## Customizing Triggers Per Phase

When embedding the violation tree into a specific phase:

1. **LOW triggers**: List the specific shared files relevant to this phase. Example: Phase 2 (Dashboard) might list `src/types/index.ts` and `src/lib/utils.ts`.

2. **MEDIUM triggers**: List specific files from OTHER phases' sandboxes. Example: If Phase 1 owns `src/lib/auth.ts`, then Phase 2's MEDIUM triggers include `"modified src/lib/auth.ts (owned by Phase 1)"`.

3. **HIGH triggers**: Always include file deletion. Add phase-specific high-severity items (e.g., "changed auth logic" for non-auth phases).

4. **CRITICAL triggers**: These are the same across ALL phases. The protected file list is global.

## Self-Report vs Git Diff

The violation tree is evaluated using TWO inputs:

1. **Agent self-report** (Step 1): Agent lists files it created/modified. This is the FIRST pass.
2. **Git diff** (Step 2): Run `git diff --name-only $BASELINE`. This is GROUND TRUTH.

If the self-report and git diff DO NOT MATCH, that ITSELF is a violation:
- If agent reported MORE files than git shows → probably harmless (agent over-reported), log as LOW
- If git shows MORE files than agent reported → agent touched files it didn't disclose. Treat as MEDIUM minimum, escalate to HIGH if the undisclosed files are from another phase's domain.



---

## 🔗 Pipeline Integration — Automatic Stage Advancement

**This section is added for pipeline automation. It tells you how to signal stage completion.**

After completing ALL steps above and producing your complete output:

### Stage Completion Protocol

1. **Verify your confidence score** meets the gate threshold (≥ 70)
2. **Verify the complete JSON output** has been produced and meets the contract
3. **Output the completion marker** on its own line as the ABSOLUTE LAST thing in your response:

```
[STAGE_COMPLETE]
```

### Rules for the completion marker:

- `[STAGE_COMPLETE]` MUST be the absolute last thing in your response — nothing after it
- Your complete JSON output (context_packet) MUST come BEFORE the marker
- **Never** output `[STAGE_COMPLETE]` until the stage contract is fully met
- **Never** output `[STAGE_COMPLETE]` if the confidence score is below 70
- If you need to ask the user questions, do **NOT** output `[STAGE_COMPLETE]` — wait for answers first, produce your final output, THEN output the marker
- If the gate_result is "fail" (score < 70), trigger the escape hatch protocol instead — do NOT output `[STAGE_COMPLETE]`

### What happens when you output [STAGE_COMPLETE]:

1. The pipeline captures everything before the marker as your stage output
2. Your output becomes the input for the next stage
3. The next stage starts automatically — no manual intervention needed

### Example — end of your response:

```json
{
  "stage_8": { ... your complete output ... },
  "metadata": {
    "confidence_scores": {
      "8": { "score": 93, "gate_result": "pass" }
    }
  }
}
```

[STAGE_COMPLETE]


================================================================================
STAGE 9: VERIFICATION & AGENT SETUP
================================================================================

---
name: stage-09-verification-agent-setup
description: Configure independent verification agent (Agent B) with git-diff rules, two-strike retry, and per-phase checker configs for PRD build phases.
---

## Purpose

Configure an independent verification agent that audits builder output after each phase using git diff as ground truth. Produces both automated (Agent B) and manual (preamble merge) verification paths, the two-strike retry rule, and per-phase checker configs that Stage 10 renders into build scripts.

## When to Use

Activate when the context packet contains completed `stage_8.protocol_injected_phases`, `stage_7.phases`, and `stage_0.tech_stack`. This skill produces `stage_9.*` — the verification agent configuration, two-strike rule, 4-step verification protocol, per-phase checker configs, Agent B config, and manual preamble config.

## Input Format

```json
{
  "stage_8": {
    "protocol_injected_phases": [
      {
        "phase_number": 1,
        "pulse_checks": [...],
        "seam_checks": [...],
        "full_checkpoint": {...},
        "violation_rules": {
          "LOW": { "action": "log_and_proceed" },
          "MEDIUM": { "action": "review_change" },
          "HIGH": { "action": "revert_entire_phase" },
          "CRITICAL": { "action": "full_stop_revert_flag" }
        },
        "overhead_tokens": 25000
      }
    ]
  },
  "stage_7": {
    "phases": [
      {
        "phase_number": 1,
        "files_allowed": ["src/lib/auth.ts", "src/contexts/AuthContext.tsx"],
        "files_read_only": ["package.json"],
        "files_forbidden": [".env", "CLAUDE.md"],
        "build_order": [...]
      }
    ]
  },
  "stage_0": {
    "tech_stack": {
      "framework": "react",
      "language": "typescript",
      "runtime": "node",
      "database": "supabase",
      "build_command": "npm run build",
      "test_command": "npm run test",
      "lint_command": "npm run lint"
    }
  }
}
```

## Process

### Step 1: Determine Verification Mode

Read `stage_0.tech_stack`. Map to delivery approach:

| Signal | Mode | Rationale |
|--------|------|-----------|
| `tech_stack.runtime` is `node`, `python`, `rust`, `go` AND no explicit `manual_delivery: true` | `automated_agent_b` | CLI-capable stack implies bash automation |
| `tech_stack` contains `manual_delivery: true` OR platform is web-only (Bolt, Lovable, etc.) | `manual_preamble_merge` | No CLI automation available |
| Ambiguous | `automated_agent_b` | Default to automated; manual config is always generated anyway |

**Both configs are always generated regardless of mode.** The `verification_mode` field tells Stage 10 which wrapper to use as PRIMARY.

### Step 2: Build the 4-Step Verification Protocol

Define the universal verification protocol (identical for both modes):

1. **Self-Report** — Agent lists every file created/modified. Compare against `files_allowed`.
2. **Diff Check** — Run `git diff PHASE_N_BASELINE..HEAD --name-only`. Compare against BOTH self-report AND `files_allowed`. Mismatch between self-report and diff is itself a violation.
3. **Violation Response** — For any file in diff NOT in `files_allowed`, apply `stage_8.protocol_injected_phases[N].violation_rules` decision tree.
4. **Functional Checks** — Run tech-stack-appropriate compile, test, render, and route checks.

Map tech stack to functional check commands using the reference in `references/four-step-verification.md`.

### Step 3: Generate Per-Phase Checker Configs

For each phase in `stage_7.phases`:

1. Copy `files_allowed` as the verification baseline
2. Set `baseline_snapshot` to `"git_commit_hash_before_phase_N_starts"`
3. Determine applicable functional checks:
   - Phase 1: compile only (no prior features to regression-test)
   - Phase 2+: compile + test (if tests exist from prior phases)
   - Phases with UI: add render check + route check
4. Define `expected_outcomes` — specific exit codes and observable results
5. Add `overrides` for phase-specific deviations (e.g., Phase 1 skips test check)

Cross-reference each phase's `violation_rules` from Stage 8 to ensure severity levels match.

### Step 4: Configure Agent B (Automated Verifier)

Build the `agent_b_config` object:

- **context_tokens**: ~10,000. Agent B is intentionally lean.
- **clean_context**: `true`. No knowledge of builder's reasoning.
- **persistent_across_phases**: `true`. Accumulates pattern log across the build.
- **receives**: Exactly 4 items: `["allowed_files_list", "git_diff_output", "functional_check_results", "violation_decision_tree"]`
- **produces**: Single classification per phase: `CLEAN | LOW | MEDIUM | HIGH | CRITICAL`
- **on_high_or_critical**: `"git reset --hard $PHASE_BASELINE && retry_with_fresh_agent_a && apply_two_strike_rule"`

Use the complete Agent B prompt template from `references/agent-b-config-template.md`.

### Step 5: Configure Two-Strike Rule

Set the auto-retry parameters (non-negotiable values):

- `max_retries`: `2` (always 2, not configurable)
- `on_second_failure`: `"stop_for_human_review"`
- `rationale`: `"If 2 fresh agents fail the same phase, the problem is the phase spec, not the agents. Human must intervene."`

Do NOT allow 3+ retries. See `references/two-strike-bash-script.md` for the bash implementation.

### Step 6: Configure Manual Preamble

Build the `manual_preamble_config`:

- Write a concrete preamble template that opens Phase N+1's prompt with Phase N validation
- Set `check_duration_estimate`: `"30 seconds"`
- Set `agent_count`: `"same as phase count, NOT doubled"`
- Set `on_issues_found`: `"fix_inline_before_proceeding_with_phase_work"`

The preamble must reference specific checks from Phase N's `full_checkpoint`, NOT generic "validate the previous phase." See `references/manual-preamble-template.md`.

### Step 7: Validate Consistency with Stage 8

Before writing output, verify:

1. Every violation severity in checker config matches Stage 8's `violation_rules`
2. Functional checks reference real commands from `stage_0.tech_stack`
3. Stage 8's `full_checkpoint` gate aligns with the 4-step protocol
4. No checker rule contradicts the builder's phase spec
5. `per_phase_checker_config` has exactly one entry per phase from Stage 7

If any contradiction is found, flag the specific conflict and attempt resolution. If unresolvable, trigger escape hatch.

## Output Format

```json
{
  "stage_9": {
    "verification_mode": "automated_agent_b | manual_preamble_merge",
    "two_strike_rule": {
      "max_retries": 2,
      "on_second_failure": "stop_for_human_review",
      "rationale": "string"
    },
    "verification_protocol": {
      "step_1_self_report": {
        "description": "Agent lists every file created or modified",
        "compare_against": "files_allowed list from phase spec",
        "output_format": "newline-separated file paths"
      },
      "step_2_diff_check": {
        "command": "git diff PHASE_N_BASELINE..HEAD --name-only",
        "compare_against": ["self_report", "allowed_files_list"],
        "mismatch_is_violation": true
      },
      "step_3_violation_response": "stage_8.protocol_injected_phases[N].violation_rules",
      "step_4_functional": {
        "commands": ["tech-stack-specific compile", "test", "lint"],
        "page_render_check": true
      }
    },
    "per_phase_checker_config": [
      {
        "phase_number": 1,
        "baseline_snapshot": "git_commit_hash_before_phase_1_starts",
        "allowed_files": ["copied from stage_7.phases[0].files_allowed"],
        "functional_checks": ["npm run build"],
        "expected_outcomes": ["exit code 0"],
        "overrides": { "skip_test_check": true }
      }
    ],
    "agent_b_config": {
      "context_tokens": 10000,
      "clean_context": true,
      "persistent_across_phases": true,
      "receives": ["allowed_files_list", "git_diff_output", "functional_check_results", "violation_decision_tree"],
      "produces": "CLEAN | LOW | MEDIUM | HIGH | CRITICAL",
      "on_high_or_critical": "git reset --hard $PHASE_BASELINE, retry fresh Agent A, apply two_strike_rule"
    },
    "manual_preamble_config": {
      "preamble_template": "concrete template text — see references/manual-preamble-template.md",
      "check_duration_estimate": "30 seconds",
      "agent_count": "same as phase count, NOT doubled",
      "on_issues_found": "fix_inline_before_proceeding_with_phase_work"
    }
  }
}
```

Metadata updates:

```json
{
  "metadata.current_stage": 9,
  "metadata.confidence_scores.9": { "score": 0, "dimensions": {...} },
  "metadata.stage_timestamps.9": "ISO-8601"
}
```

## Edge Cases

### Missing Input

| Missing Field | Action |
|---------------|--------|
| `stage_8.protocol_injected_phases` | FAIL — trigger escape hatch. Cannot configure verification without protocols. |
| `stage_7.phases` | FAIL — trigger escape hatch. Cannot build per-phase configs without phase definitions. |
| `stage_0.tech_stack` | WARN — default to Node/npm commands. Flag in confidence scoring (Accuracy penalty). |
| `stage_8.*.violation_rules` empty for some phases | Generate default LOW/MEDIUM/HIGH/CRITICAL tree for those phases. Flag as override. |

### Ambiguous Input

| Ambiguity | Resolution |
|-----------|------------|
| Tech stack has both `build_command` and `compile_command` | Use `build_command` for functional check. |
| Phase has no `files_allowed` (empty list) | Treat as infrastructure-only phase. Set `skip_functional: true` in overrides. |
| Violation rules differ between Stage 8 phases | Use the strictest interpretation. Log the discrepancy. |

### Scope Overflow

| Discovery | Action |
|-----------|--------|
| Phase spec needs restructuring to be verifiable | Do NOT restructure. Flag as `NEEDS_HUMAN` with suggestion: "Phase N may need splitting — verification requires clearer file boundaries." |
| Functional checks need new tooling not in tech stack | Log the gap. Use closest available command. Flag in confidence. |

## Confidence Scoring

Score each dimension 0-20 after producing output:

1. **Completeness** (0-20): Both verification approaches configured? Every phase has `per_phase_checker_config`? All 4 protocol steps defined? Two-strike rule set with `max_retries=2`?

2. **Accuracy** (0-20): Functional checks use real commands from `stage_0.tech_stack`? Agent B config matches spec (~10K tokens, clean context, persistent)? Violation severities match Stage 8 exactly?

3. **Consistency** (0-20): Checker's `allowed_files` matches Stage 7's `files_allowed` per phase? Protocol aligns with Stage 8's `full_checkpoint`? Both approaches use identical core protocol?

4. **Specificity** (0-20): Git commands are exact (not "run a diff")? Preamble template is concrete text? Expected outcomes include exit codes?

5. **Handoff Readiness** (0-20): Stage 10 can render `build.sh` from this output? Bash retry logic is copy-ready? Preamble is paste-ready into Phase N+1?

**Total /100: >= 90 PASS | 70-89 WARN (flag + proceed) | < 70 FAIL (escape hatch)**

## Escape Hatch

**Trigger when:**
- Required inputs missing (no `protocol_injected_phases`, no `phases`, no `tech_stack`)
- Tech stack unrecognized (cannot determine compile/test commands)
- Stage 8 violation rules are incomplete or contradictory
- Checker config would contradict builder's phase spec
- Confidence score < 70 after one retry

**Save:** Current `context_packet`, stage number (9), step where halt occurred, which phases have configs and which don't, suggested questions for human.

**Signal:**
```json
{
  "metadata.status": "needs_human",
  "metadata.escape_hatches": [{ "stage": 9, "reason": "...", "suggested_actions": [...] }]
}
```

## Example

See `references/four-step-verification.md` for a complete walkthrough showing both automated and manual flows for a React+TypeScript app with 3 phases. The example covers:
- Phase 1 (auth): compile-only check, Agent B classifies CLEAN
- Phase 2 (dashboard): compile + test + route check, Agent B detects MEDIUM drift on shared types file
- Phase 3 (payments): Agent B detects HIGH violation, triggers revert + retry, fresh Agent A passes on second attempt
- Manual flow: Phase 2 opens with Phase 1 validation preamble, finds and fixes a missing export inline


---
## REFERENCE: agent-b-config-template

# Agent B Configuration Template

## Agent B Prompt (Automated Verifier)

```
You are a build verification agent. You audit the builder agent's output for a single phase.
You have NO knowledge of WHY the builder made its decisions. You see only evidence.

## Your Inputs

1. ALLOWED_FILES: The list of files this phase was permitted to create or modify.
2. GIT_DIFF: Output of `git diff PHASE_N_BASELINE..HEAD --name-only` — every file actually touched.
3. FUNCTIONAL_RESULTS: Output of compile, test, render, and route checks.
4. VIOLATION_TREE: The severity classification rules for unauthorized file changes.

## Your Job

Compare GIT_DIFF against ALLOWED_FILES. For every file in the diff:
- If it appears in ALLOWED_FILES: PASS (expected change)
- If it does NOT appear in ALLOWED_FILES: classify using the VIOLATION_TREE

Review FUNCTIONAL_RESULTS:
- If any check failed (non-zero exit code, render error, route 404): flag as functional failure

## Your Output

Produce exactly ONE classification for this phase:

| Classification | Meaning | Trigger |
|----------------|---------|---------|
| CLEAN | All files in diff are in allowed list. All functional checks pass. | Zero violations, zero failures |
| LOW | 1-2 files outside allowed list, but they are shared types/config files. All functional checks pass. | Minor drift, additive changes only |
| MEDIUM | Files from another phase's domain were modified, OR a functional check has warnings (not errors). | Cross-phase drift or soft failures |
| HIGH | Files were deleted, core config was changed, OR a functional check failed (non-zero exit). | Dangerous drift or build breakage |
| CRITICAL | .env, CLAUDE.md, build config, or environment files were modified. OR multiple functional checks failed. | Security-relevant changes or cascading failures |

## Format

```
PHASE: {N}
CLASSIFICATION: {CLEAN|LOW|MEDIUM|HIGH|CRITICAL}
FILES_IN_DIFF: {count}
FILES_ALLOWED: {count}
UNAUTHORIZED_FILES: {list or "none"}
FUNCTIONAL_CHECKS: {all_pass|failures_list}
PATTERN_NOTE: {any cumulative observation from prior phases, or "first phase"}
```

## Rules

- You CANNOT edit any files. You are read-only.
- You CANNOT access the builder's conversation, reasoning, or context.
- If classification is HIGH or CRITICAL, the orchestrator will revert and retry.
- Be precise. "MEDIUM" is not "probably fine" — it means cross-phase drift was detected.
- If this is not the first phase, note patterns (e.g., "builder has drifted toward types.ts in 2 of 3 phases").
```

## Token Budget

- **Per-verification**: ~10,000 tokens
  - Allowed files list: ~500 tokens
  - Git diff output: ~1,000 tokens (typical phase touches 5-15 files)
  - Functional check results: ~2,000 tokens (build output, test output)
  - Violation decision tree: ~2,000 tokens
  - Agent B prompt: ~2,000 tokens
  - Working space: ~2,500 tokens
- **Across full build (4 phases)**: ~40,000 tokens total

## Persistence Model

Agent B persists across all phases. Its cumulative context grows by ~1,000 tokens per phase (the classification output + pattern note). By Phase 4 of a 4-phase build, Agent B's total context is ~13,000 tokens.

### Pattern Accumulation

After each phase, Agent B appends to its pattern log:

```
PHASE 1: CLEAN — 0 unauthorized files
PHASE 2: LOW — types.ts touched (shared type added)
PHASE 3: LOW — types.ts touched again (same file)
PHASE 4: MEDIUM — types.ts + utils/helpers.ts touched — PATTERN DETECTED: builder consistently drifts toward types.ts. Flagging as systemic.
```

If the same file appears as unauthorized in 3+ phases, escalate from LOW to MEDIUM regardless of individual severity, and add: `"SYSTEMIC: builder repeatedly touches {file} across phases. Consider adding to allowed list or splitting differently."`

## Integration with Orchestrator

```bash
# The orchestrator calls Agent B after each phase
PHASE_RESULT=$(run_agent_b \
  --allowed-files "phase-${N}-allowed.txt" \
  --diff-output "phase-${N}-diff.txt" \
  --functional-results "phase-${N}-checks.txt" \
  --violation-tree "violation-rules.json" \
  --pattern-log "agent-b-pattern-log.txt" \
)

# Parse the classification
CLASSIFICATION=$(echo "$PHASE_RESULT" | grep "CLASSIFICATION:" | cut -d' ' -f2)
```


---
## REFERENCE: four-step-verification

# Four-Step End-of-Phase Verification Protocol

## Overview

Every phase ends with this 4-step verification. It is identical for automated and manual modes — only the delivery wrapper differs.

## The Protocol

### Step 1: Self-Report

The builder agent lists every file it created, modified, or deleted during the phase.

**Input**: Agent's own memory of what it changed.
**Compare against**: `files_allowed` from the phase spec.
**Output format**:
```
FILES_CREATED:
- src/lib/auth.ts
- src/contexts/AuthContext.tsx

FILES_MODIFIED:
- src/App.tsx (added routes)

FILES_DELETED:
(none)
```

**Why this exists**: First-pass sanity check. Fast, but unreliable — agents can forget files or hallucinate changes. This is a courtesy check, NOT ground truth.

### Step 2: Diff Check (Ground Truth)

Run the deterministic git diff command.

**Command**: `git diff PHASE_N_BASELINE..HEAD --name-only`

**Compare against**:
1. The self-report from Step 1
2. The `files_allowed` list from the phase spec

**Mismatch handling**:
- File in diff but NOT in self-report: Agent forgot to mention it. This is a violation (agent honesty failure).
- File in self-report but NOT in diff: Agent hallucinated a change. Flag but not critical.
- File in diff but NOT in `files_allowed`: Unauthorized file change. Classify using violation tree.

**Why this is ground truth**: `git diff` is mechanical. It cannot lie, cannot forget, cannot hallucinate. It captures every byte that changed.

### Step 3: Violation Response

For every unauthorized file (in diff but NOT in `files_allowed`), apply the violation decision tree from `stage_8.protocol_injected_phases[N].violation_rules`:

| Severity | Example | Action |
|----------|---------|--------|
| LOW | Touched a shared `types.ts` to add an export | Log it. Note in phase report. Proceed. |
| MEDIUM | Modified a file from another phase's domain | STOP. If additive (added export/prop): log + proceed with caution. If destructive (renamed, changed logic): revert that file to baseline. |
| HIGH | Deleted files, modified core config, changed auth logic | REVERT ENTIRE PHASE. Re-run with tighter constraints. |
| CRITICAL | Modified `.env`, `CLAUDE.md`, build config, environment files | FULL STOP. REVERT. FLAG. Human must intervene. |

### Step 4: Functional Checks

Run tech-stack-appropriate verification commands.

#### Command Mapping

| Tech Stack | Compile Check | Test Check | Lint Check |
|------------|--------------|------------|------------|
| Node/React/Next.js | `npm run build` | `npm run test` | `npm run lint` |
| Python/Django/Flask | `python -m py_compile {files}` | `python -m pytest` | `ruff check .` |
| Rust | `cargo build` | `cargo test` | `cargo clippy` |
| Go | `go build ./...` | `go test ./...` | `golangci-lint run` |
| Flutter/Dart | `flutter build` | `flutter test` | `flutter analyze` |

#### Render & Route Checks (Web Apps)

For phases that create UI pages:
- **Render check**: Do new pages/components render without errors? (Check browser console for React errors, 500s, blank screens)
- **Route check**: Can you navigate to expected routes? (e.g., `/sign-in` returns 200, not 404)

#### Expected Outcomes

Each functional check has a specific pass condition:
- Compile: exits with code 0
- Test: 0 failures (warnings OK)
- Lint: 0 errors (warnings OK)
- Render: no runtime errors in console
- Route: expected routes return 200

**ALL FOUR STEPS MUST PASS BEFORE THE NEXT PHASE BEGINS.**

---

## Complete Example: React + TypeScript App (3 Phases)

### Phase 1: Auth System

**Allowed files**: `src/lib/auth.ts`, `src/contexts/AuthContext.tsx`, `src/pages/SignIn.tsx`, `src/pages/SignUp.tsx`, `src/App.tsx`

**Automated flow (Agent B)**:
1. Agent A builds auth system
2. `git diff phase-1-baseline..HEAD --name-only` returns:
   ```
   src/lib/auth.ts
   src/contexts/AuthContext.tsx
   src/pages/SignIn.tsx
   src/pages/SignUp.tsx
   src/App.tsx
   ```
3. Agent B compares: all 5 files are in allowed list. Zero unauthorized files.
4. Functional checks: `npm run build` exits 0. No tests yet (Phase 1 override: `skip_test_check: true`).
5. **Classification: CLEAN**. Proceed to Phase 2.

**Manual flow**: Phase 1 has no preamble (no prior phase to validate). Phase 2 will open with Phase 1 validation.

### Phase 2: Dashboard + Data Layer

**Allowed files**: `src/pages/Dashboard.tsx`, `src/hooks/useData.ts`, `src/lib/api.ts`, `src/components/DataTable.tsx`

**Automated flow (Agent B)**:
1. Agent A builds dashboard
2. `git diff phase-2-baseline..HEAD --name-only` returns:
   ```
   src/pages/Dashboard.tsx
   src/hooks/useData.ts
   src/lib/api.ts
   src/components/DataTable.tsx
   src/lib/types.ts          <-- NOT in allowed list
   ```
3. Agent B compares: 4 files match, 1 unauthorized (`types.ts`).
4. Agent B checks violation tree: `types.ts` is a shared types file. Classification: **LOW**.
5. Functional checks: `npm run build` exits 0. `npm run test` exits 0 (auth tests from Phase 1 still pass).
6. **Classification: LOW**. Log drift, proceed to Phase 3.
7. Pattern log: `"Phase 2: LOW — types.ts touched (shared type added)"`

**Manual flow (Phase 2 prompt opens with)**:
```
## Pre-Phase Validation (Phase 1 Deliverables)
Before starting Phase 2 work, validate Phase 1:
Run: git diff phase-1-baseline..HEAD --name-only
Expected: src/lib/auth.ts, src/contexts/AuthContext.tsx, src/pages/SignIn.tsx, src/pages/SignUp.tsx, src/App.tsx
Run: npm run build (expect exit 0)
Navigate to /sign-in and /sign-up (expect pages render)
```
Agent finds Phase 1 clean. Proceeds with Phase 2 work.

### Phase 3: Payments

**Allowed files**: `src/pages/Checkout.tsx`, `src/lib/payments.ts`, `src/components/PaymentForm.tsx`

**Automated flow (Agent B) — failure scenario**:
1. Agent A builds payments
2. `git diff phase-3-baseline..HEAD --name-only` returns:
   ```
   src/pages/Checkout.tsx
   src/lib/payments.ts
   src/components/PaymentForm.tsx
   src/lib/auth.ts            <-- Phase 1's file! NOT in allowed list
   .env                       <-- CRITICAL
   ```
3. Agent B compares: 3 files match, 2 unauthorized.
4. `src/lib/auth.ts` = modified another phase's file = MEDIUM/HIGH.
5. `.env` = environment file = **CRITICAL**.
6. Functional checks skipped (CRITICAL already determined).
7. **Classification: CRITICAL**. Trigger revert.

**Revert + retry**:
1. `git reset --hard phase-3-baseline`
2. Fresh Agent A (new context, no memory of failed attempt)
3. Fresh Agent A builds payments without touching auth.ts or .env
4. Agent B verifies: CLEAN
5. **Phase 3 passes on second attempt.**

**If second attempt also failed**: STOP. Write failure report. Human reviews Phase 3 spec.


---
## REFERENCE: manual-preamble-template

# Manual Preamble Template

## Purpose

For users pasting prompts into Claude Code web/desktop (no bash automation), verification of Phase N is merged as a 30-second preamble into Phase N+1's prompt. This avoids doubling the agent count.

## Template

The following template is inserted at the TOP of Phase N+1's prompt, before the phase's own work begins. Replace `{N}` with the previous phase number and fill in the phase-specific values.

```markdown
## Pre-Phase Validation (Phase {N} Deliverables)

Before starting Phase {N+1} work, validate that Phase {N} was completed correctly.

### File Check
Run: `git diff {PHASE_N_BASELINE}..HEAD --name-only`

Expected files (Phase {N} allowed list):
{ALLOWED_FILES_LIST — one per line}

**If any file in the diff is NOT in the expected list above:**
- Shared types/config file (e.g., types.ts, index.ts) -> Note it, proceed
- File from a different phase's domain -> STOP. Revert that file: `git checkout {PHASE_N_BASELINE} -- {file}`
- Core system file (.env, CLAUDE.md, build config) -> STOP. Revert ALL Phase {N} changes: `git reset --hard {PHASE_N_BASELINE}` and redo Phase {N} from scratch

### Functional Check
Run these commands and verify they pass:
{FUNCTIONAL_COMMANDS — one per line with expected outcome}

Example:
- `npm run build` -> exits with code 0
- `npm run test` -> all tests pass (0 failures)
- Navigate to {EXPECTED_ROUTES} -> pages render without errors

### Verdict
- All files match + all checks pass -> Proceed with Phase {N+1} work below
- Minor issues (1-2 extra shared files, warnings but no errors) -> Fix inline, then proceed
- Major issues (wrong files modified, build fails, tests fail) -> Fix ALL issues before starting Phase {N+1}

---
## Phase {N+1}: {PHASE_NAME}
{... Phase N+1's actual instructions follow ...}
```

## Customization Rules

1. **`ALLOWED_FILES_LIST`**: Copy directly from `stage_7.phases[N].files_allowed`. One file per line.
2. **`FUNCTIONAL_COMMANDS`**: Derive from `stage_0.tech_stack`:
   - Node/React: `npm run build`, `npm run test`, route checks
   - Python: `python -m pytest`, `ruff check .`, `mypy .`
   - Rust: `cargo build`, `cargo test`
   - Go: `go build ./...`, `go test ./...`
3. **`EXPECTED_ROUTES`**: Derive from the pages/routes created in Phase N (from `stage_6.sub_6b` mapped to phases in Stage 7).
4. **`PHASE_N_BASELINE`**: The git commit hash or tag created before Phase N started. In practice, this is set by the build script or manually noted.

## Duration Estimate

The preamble check takes approximately 30 seconds of the agent's time:
- Read the diff output: ~5 seconds
- Compare against allowed list: ~10 seconds
- Run functional checks (if not already run): ~10 seconds
- Make pass/fix/redo decision: ~5 seconds

This is negligible compared to the 10-30 minutes a typical phase takes.

## Agent Count Impact

| Approach | Phases | Agents | Idle Gaps |
|----------|--------|--------|-----------|
| Separate checker agents | 4 | 8 (4 build + 4 check) | 4 gaps (5-25 min each) |
| Preamble merge | 4 | 4 (each checks previous) | 0 extra gaps |

The preamble approach saves 4 idle gaps and halves the agent sessions for manual users.

## Edge Case: Phase 1

Phase 1 has no previous phase to validate. Its prompt does NOT include the preamble. The preamble first appears in Phase 2's prompt (validating Phase 1).

## Edge Case: Final Phase

The final phase's output has no "next phase" to validate it. For manual users, the final phase should include its own self-validation step at the end (the standard 4-step protocol runs as an epilogue rather than as the next phase's preamble).


---
## REFERENCE: two-strike-bash-script

# Two-Strike Bash Script Pattern

## Purpose

Bash implementation of the two-strike retry rule for automated (Agent B) verification. Copy this pattern into `build.sh` generation in Stage 10.

## Script Pattern

```bash
#!/bin/bash
set -euo pipefail

# ============================================================
# Two-Strike Verification Loop
# If a phase fails HIGH/CRITICAL twice, stop for human review.
# ============================================================

PHASE_NUMBER=$1
PHASE_FILE="phases/phase-${PHASE_NUMBER}.md"
BASELINE_TAG="phase-${PHASE_NUMBER}-baseline"

# Capture baseline before phase starts
git tag -f "$BASELINE_TAG" HEAD

run_phase() {
    local attempt=$1
    echo "=== Phase ${PHASE_NUMBER}, Attempt ${attempt} ==="

    # Run builder agent (Agent A)
    # Replace with actual agent invocation command
    claude --prompt-file "$PHASE_FILE" \
           --permission-mode acceptEdits \
           --settings-file .claude/settings.json

    # Capture diff
    git diff "${BASELINE_TAG}..HEAD" --name-only > "phase-${PHASE_NUMBER}-diff.txt"

    # Run functional checks
    run_functional_checks "$PHASE_NUMBER" > "phase-${PHASE_NUMBER}-checks.txt" 2>&1
    FUNC_EXIT=$?

    # Run Agent B (verifier)
    CLASSIFICATION=$(run_agent_b \
        --allowed-files "phases/phase-${PHASE_NUMBER}-allowed.txt" \
        --diff-output "phase-${PHASE_NUMBER}-diff.txt" \
        --functional-results "phase-${PHASE_NUMBER}-checks.txt" \
        --violation-tree "violation-rules.json" \
        --pattern-log "agent-b-pattern-log.txt" \
    | grep "CLASSIFICATION:" | cut -d' ' -f2)

    echo "Phase ${PHASE_NUMBER} classification: ${CLASSIFICATION}"
    echo "$CLASSIFICATION"
}

# --- Attempt 1 ---
RESULT=$(run_phase 1)

if [ "$RESULT" = "HIGH" ] || [ "$RESULT" = "CRITICAL" ]; then
    echo "!!! Phase ${PHASE_NUMBER} FAILED verification (${RESULT}). Reverting..."
    git reset --hard "$BASELINE_TAG"

    # --- Attempt 2 (fresh agent, clean context) ---
    RESULT=$(run_phase 2)

    if [ "$RESULT" = "HIGH" ] || [ "$RESULT" = "CRITICAL" ]; then
        echo "!!! Phase ${PHASE_NUMBER} FAILED TWICE (${RESULT}). STOPPING FOR HUMAN REVIEW."
        git reset --hard "$BASELINE_TAG"

        # Write failure report
        cat > "phase-${PHASE_NUMBER}-failure-report.txt" <<REPORT
PHASE: ${PHASE_NUMBER}
STATUS: FAILED_TWICE
CLASSIFICATION: ${RESULT}
ACTION_REQUIRED: Human review needed.
REASON: Two fresh agents failed the same phase. The problem is likely the phase specification, not the agents.
SUGGESTED_ACTIONS:
  1. Review the phase spec for ambiguity or contradictions
  2. Check if files_allowed is too restrictive
  3. Check if the phase scope is too large (consider splitting)
  4. Review the functional check expectations
REPORT

        exit 1
    fi
fi

# If we get here, phase passed (CLEAN, LOW, or MEDIUM)
echo "Phase ${PHASE_NUMBER} PASSED verification: ${RESULT}"

# Tag the successful completion
git tag -f "phase-${PHASE_NUMBER}-complete" HEAD
```

## Functional Check Helper

```bash
run_functional_checks() {
    local phase=$1
    local exit_code=0

    echo "--- Compile Check ---"
    # Tech-stack-specific: replace with actual commands
    npm run build 2>&1 || exit_code=1

    echo "--- Test Check ---"
    if [ -f "package.json" ] && grep -q '"test"' package.json; then
        npm run test 2>&1 || exit_code=1
    else
        echo "No test script found. Skipping."
    fi

    echo "--- Render Check ---"
    # For web apps: start dev server, check routes, stop
    # This is tech-stack-specific and may use curl or playwright
    echo "Render check: manual verification required for web apps"

    return $exit_code
}
```

## Key Rules

1. **max_retries = 2. Always.** Do not make this configurable. Three retries waste tokens and almost never succeed when two have failed.
2. **Fresh agent on retry.** The retried Agent A has zero memory of the first attempt. Clean context, clean slate.
3. **Revert before retry.** `git reset --hard $BASELINE_TAG` ensures the second attempt starts from the exact same state as the first.
4. **Exit 1 on double failure.** The build script stops. A human must read the failure report and intervene.
5. **Tag baselines.** Every phase gets a git tag before it starts. This is the rollback point.

## Integration Notes

- Stage 10 fills in the actual agent invocation commands based on `stage_0.tech_stack`
- Stage 10 fills in the actual functional check commands
- The `run_agent_b` function is a wrapper around the Agent B prompt from `agent-b-config-template.md`
- The pattern log (`agent-b-pattern-log.txt`) persists across phases for Agent B's cumulative awareness



---

## 🔗 Pipeline Integration — Automatic Stage Advancement

**This section is added for pipeline automation. It tells you how to signal stage completion.**

After completing ALL steps above and producing your complete output:

### Stage Completion Protocol

1. **Verify your confidence score** meets the gate threshold (≥ 70)
2. **Verify the complete JSON output** has been produced and meets the contract
3. **Output the completion marker** on its own line as the ABSOLUTE LAST thing in your response:

```
[STAGE_COMPLETE]
```

### Rules for the completion marker:

- `[STAGE_COMPLETE]` MUST be the absolute last thing in your response — nothing after it
- Your complete JSON output (context_packet) MUST come BEFORE the marker
- **Never** output `[STAGE_COMPLETE]` until the stage contract is fully met
- **Never** output `[STAGE_COMPLETE]` if the confidence score is below 70
- If you need to ask the user questions, do **NOT** output `[STAGE_COMPLETE]` — wait for answers first, produce your final output, THEN output the marker
- If the gate_result is "fail" (score < 70), trigger the escape hatch protocol instead — do NOT output `[STAGE_COMPLETE]`

### What happens when you output [STAGE_COMPLETE]:

1. The pipeline captures everything before the marker as your stage output
2. Your output becomes the input for the next stage
3. The next stage starts automatically — no manual intervention needed

### Example — end of your response:

```json
{
  "stage_9": { ... your complete output ... },
  "metadata": {
    "confidence_scores": {
      "9": { "score": 93, "gate_result": "pass" }
    }
  }
}
```

[STAGE_COMPLETE]


================================================================================
STAGE 10: OUTPUT GENERATOR
================================================================================

---
name: stage-10-output-generator
description: Render Stages 0-9 output into deliverable build package — phase files, build.sh, CLAUDE.md, BUILD_RULES.md, and README.md.
---

## Purpose

Serialize all decisions from Stages 0-9 into a copy-paste-ready file package that a coding agent or human developer can execute without asking any questions. This stage is pure rendering — zero design decisions, zero open questions. Every ambiguity was resolved upstream.

## When to Use

Activate when the context packet contains completed data from stages 0, 3, 4, 5, 6, 7, 8, and 9. Trigger phrases: "output generator", "render build files", "serialize phase documents", "generate phase files", "produce output package". This skill PRODUCES a deliverable file package: `phases/phase-N.md` files + `build.sh` + `CLAUDE.md` + `BUILD_RULES.md` + `README.md`.

## Input Format

```json
{
  "stage_0": { "platform_profile": {...}, "tech_stack": {...}, "command_allowlist": [...] },
  "stage_3": { "concept_and_context": {...}, "drift_anchor": "string" },
  "stage_4": { "mechanisms": [...], "mechanism_dependencies": [...] },
  "stage_5": { "mechanism_blueprints": [...], "build_rules_applied": [...] },
  "stage_6": { "sub_6a": {...}, "sub_6b": {...}, "sub_6c": {...} },
  "stage_7": { "phases": [...], "token_budget": {...}, "mandatory_build_order": [...] },
  "stage_8": { "protocol_injected_phases": [...], "overhead_breakdown": {...} },
  "stage_9": {
    "verification_mode": "automated_agent_b | manual_preamble_merge",
    "two_strike_rule": {...}, "verification_protocol": {...},
    "per_phase_checker_config": [...], "agent_b_config": {...}
  },
  "metadata": { "app_type": "string", "archetype_matches": [...], "confidence_scores": {...} }
}
```

## Process

### Step 1: Build Output Manifest

Enumerate every file to generate. For each, record `file_path`, `file_type`, and `estimated_tokens`:

- `phases/phase-N.md` (one per phase from `stage_7.phases`) — type: `"phase"`, tokens: `stage_7.token_budget.per_phase[N]` + `stage_8.overhead_breakdown.per_phase[N]`
- `build.sh` — type: `"build_script"`, tokens: ~2,000
- `CLAUDE.md` — type: `"claude_md"`, tokens: ~3,000 (must stay under 500 lines)
- `BUILD_RULES.md` — type: `"build_rules"`, tokens: ~8,000
- `README.md` — type: `"readme"`, tokens: ~1,500

### Step 2: Render Phase Files

For each phase in `stage_8.protocol_injected_phases`, compile a standalone `phase-N.md` with exactly 9 sections in order. Use the template in `references/phase-file-template.md`. Each section's source:

1. **Build Rules Preamble** (~8K tokens): From `stage_5.build_rules_applied` + `stage_3.drift_anchor`. Distribute Martin's rules as architecture principles — NEVER as a standalone "Martin's Rules" block.
2. **File Sandbox Declaration** (~2K tokens): From `stage_7.phases[N].files_allowed`, `files_read_only`, `files_forbidden`.
3. **Build Order with Pulse Points** (~3K tokens): From `stage_7.mandatory_build_order` + `stage_8.protocol_injected_phases[N].pulse_checks`.
4. **Seam Check Definitions** (~2K tokens): From `stage_8.protocol_injected_phases[N].seam_checks`.
5. **Objective and Feature Requirements**: From `stage_7.phases[N].features` cross-referenced with `stage_4.mechanisms` and `stage_6.sub_6b`.
6. **Pattern References**: From `stage_5.mechanism_blueprints` — file:line references for patterns to follow, informed by Wall/Door/Room classifications.
7. **Violation Handling Instructions** (~2K tokens): From `stage_8.protocol_injected_phases[N].violation_rules`. Decision tree: LOW (log+continue), MEDIUM (fix first), HIGH (rollback to pulse), CRITICAL (stop+human).
8. **Full Checkpoint at End** (~5K tokens): From `stage_8.protocol_injected_phases[N].full_checkpoint`. 4-step check: self-report, diff check, violation response, functional verification.
9. **Gate Condition**: "ALL FOUR STEPS MUST PASS BEFORE PHASE [N+1] BEGINS" (or "PIPELINE COMPLETE" for last phase).

**Critical**: Each phase file MUST be self-contained — executable in a fresh agent context without cross-file references (except READ-ONLY codebase files).

### Step 3: Generate build.sh

Create the deterministic bash wrapper using the template in `references/build-sh-template.md`:

- `set -e` — stop on ANY error
- Per-phase block: git snapshot (`SNAPSHOT=$(git rev-parse HEAD)`), pre-build validation, agent work marker, post-build validation, forbidden file detection via `git diff --name-only $SNAPSHOT`, commit
- Phase chaining with `&&` (NEVER `;`)
- Two-strike retry from `stage_9.two_strike_rule`: fail → rollback → retry with fresh agent → second fail → stop for human
- Platform-adaptive commands from `stage_0.tech_stack` (build, lint, test commands)
- Forbidden file detection: `git diff --name-only $SNAPSHOT | grep -E "forbidden_pattern"` built from each phase's `files_forbidden`

Set `build_script_config`:
```json
{
  "snapshot_enabled": true,
  "rollback_enabled": true,
  "forbidden_file_detection": true,
  "two_strike_retry": true,
  "chaining_operator": "&&"
}
```

### Step 4: Generate CLAUDE.md

Create quick-reference guardrails file using `references/claude-md-template.md`. MUST be under 500 lines. Contents:

- **Architecture Principles**: Distilled from `stage_5.mechanism_blueprints` and `stage_5.build_rules_applied`. Single-responsibility, state placement, file size limits, import direction.
- **Modification Rules**: Read before edit, don't refactor uninstructed, match existing style.
- **Testing Protocol**: Compile check, render check, regression check.
- **File Structure Map**: Generated from `stage_6.sub_6a` (page arrangement) and `stage_7.phases` (file sandboxes).
- **Pointers to BUILD_RULES.md**: Section references for debugging, feature addition, code review protocols.

CLAUDE.md is distilled. BUILD_RULES.md has depth. They never contradict.

### Step 5: Generate BUILD_RULES.md

Create detailed reference playbook using `references/build-rules-sections.md`. Map Martin's modules to sections adapted for `stage_0.tech_stack`:

| Martin Module | BUILD_RULES.md Section |
|---------------|----------------------|
| 08 (Bug Fix) | "Debugging Protocol" |
| 09 (Feature Add) | "Feature Addition Protocol" |
| 10 (Debug) | "Trace-First Debugging" |
| 13 (Testing) | "Testing & Verification" |
| 03 (Data Layer) | "Data Access Patterns" |
| 05 (CRUD Flow) | "Entity CRUD Pattern" |

Other modules (01 Scaffold, 02 Auth, 04 UI Kit, 06 Polish, 07 Style, 11 Clean Room, 12 PRD Generator) are handled by phase files or the UI style system — no separate sections needed.

### Step 6: Generate README.md

Document the build package:

- Product name + description (from `stage_3.concept_and_context`)
- Tech stack (from `stage_0.tech_stack`)
- How to run the build (platform-specific from `platform_target`)
- Phase overview (what each phase builds, from `stage_7.phases`)
- How to add features post-build (pointer to BUILD_RULES.md)

### Step 7: Platform Picker Rendering

Set `platform_target` based on user's chosen platform. Adapt wrapper instructions per `references/platform-wrappers.md`:

| Platform | Method | Automation |
|----------|--------|-----------|
| `claude_cli` | `bash build.sh` | Fully automatic |
| `claude_web` | Copy-paste `phase-N.md` | Manual |
| `codex_cli` / `gemini_cli` | Platform CLI commands | Fully automatic |
| `cursor` / `windsurf` | Terminal, semi-auto | Semi-automatic |
| `bolt` / `lovable` | No terminal | Manual export |
| `generic` | Copy-paste anywhere | Fully manual |

Phase file CONTENT is identical across platforms. Only execution wrapper changes.

### Step 8: Internal Consistency Verification

Before writing output, verify ALL of the following:

1. Every file path in every sandbox declaration exists in a build order
2. Every mechanism in `stage_4.mechanisms` appears in at least one phase
3. Every page in `stage_6.sub_6b` appears in at least one phase
4. Every import/pattern reference points to a file that gets created or exists as READ-ONLY
5. `open_questions_count` == 0 (scan all feature requirements for question marks or TBD markers)
6. Every phase's total tokens (content + overhead) fits within budget
7. No phase file references content from another phase file (self-containment check)

Write results to `final_validation`. If ANY check fails, attempt auto-fix (reorder, reassign). If unfixable, trigger escape hatch.

## Output Format

```json
{
  "stage_10": {
    "output_manifest": [
      { "file_path": "phases/phase-1.md", "file_type": "phase", "estimated_tokens": 45000 }
    ],
    "generated_files": {
      "phases/phase-1.md": "full markdown content...",
      "build.sh": "#!/bin/bash\nset -e\n...",
      "CLAUDE.md": "# Build Rules\n...",
      "BUILD_RULES.md": "# Build Rules Reference\n...",
      "README.md": "# Product Name\n..."
    },
    "build_script_config": {
      "snapshot_enabled": true,
      "rollback_enabled": true,
      "forbidden_file_detection": true,
      "two_strike_retry": true,
      "chaining_operator": "&&"
    },
    "platform_target": "claude_cli",
    "claude_md_content": "string (under 500 lines)",
    "build_rules_content": "string",
    "final_validation": {
      "open_questions_count": 0,
      "all_phases_fit_budget": true,
      "all_mechanisms_covered": true,
      "all_pages_covered": true
    }
  }
}
```

Metadata updates:
```json
{
  "metadata.current_stage": 10,
  "metadata.status": "completed",
  "metadata.confidence_scores.10": { "score": 0, "dimensions": {...}, "gate_result": "pass" },
  "metadata.stage_timestamps.10": "ISO-8601",
  "metadata.updated_at": "ISO-8601"
}
```

## Edge Cases

### Missing Input

| Missing Field | Action |
|---------------|--------|
| `stage_7.phases` is null or empty | FAIL — escape hatch. No phases = no output. |
| `stage_8.protocol_injected_phases` missing | FAIL — escape hatch. Cannot render phase files without protocols. |
| `stage_9` missing entirely | WARN — generate build.sh without verification/retry. Flag in confidence (Completeness -10). |
| `stage_0.tech_stack` missing | WARN — default to Node/npm. Flag in confidence (Accuracy -5). |
| `stage_5.build_rules_applied` empty | Generate minimal preamble from universal rules only. Flag in confidence (Specificity -5). |

### Ambiguous Input

| Ambiguity | Resolution |
|-----------|------------|
| Mechanism assigned to no phase | FAIL — triggers consistency check failure. Escape hatch with suggestion to re-run Stage 7. |
| Page in `stage_6.sub_6b` has no phase | FAIL — triggers consistency check failure. Escape hatch with suggestion to re-run Stage 7. |
| Token budget exceeded for a phase | Attempt split: move last feature to next phase. If still over, escape hatch. |
| Platform is `bolt`/`lovable` (no terminal) | Generate build.sh anyway for documentation, but set primary wrapper to manual copy-paste. |

### Scope Overflow

| Discovery | Action |
|-----------|--------|
| Feature requirement contains open question (TBD, "to be decided") | Do NOT render. Set `open_questions_count` > 0. Escape hatch with pointer to originating stage. |
| Phase spec needs design changes to be renderable | Do NOT redesign. Flag as `NEEDS_HUMAN`: "Phase N requires restructuring — re-run Stage 7 with constraint X." |
| Missing pattern reference (file doesn't exist yet) | Check if another phase creates it. If yes, mark as cross-phase dependency (allowed as READ-ONLY in later phase). If no, flag. |

## Confidence Scoring

Score each dimension 0-20 after producing output:

1. **Completeness**: All files in manifest generated? Every phase file has all 9 sections? build.sh has verification + retry? CLAUDE.md + BUILD_RULES.md present and populated? No skeletal sections?

2. **Accuracy**: Every reference resolves? build.sh commands valid for platform? CLAUDE.md rules match project architecture? Zero dangling references to nonexistent files/mechanisms/patterns?

3. **Consistency**: Phase sandbox rules respected across phases? build.sh verification matches phase checkpoints? CLAUDE.md and BUILD_RULES.md complement without contradiction? No phase modifies files another phase forbids?

4. **Specificity**: Phase requirements specify exact file paths, exports, patterns? Not vague ("build the auth system")? build.sh uses real paths and commands?

5. **Handoff Readiness**: Can a coding agent execute ALL phases without asking a single question? The output package IS the complete instruction set. If any question would need to be asked, score < 16.

**Total /100: >= 90 PASS (deliver) | 70-89 WARN (deliver with warning) | < 70 FAIL (escape hatch)**

## Escape Hatch

**Trigger when:**
- Required input namespace missing (`stage_7`, `stage_8` null)
- `stage_7.phases` is empty
- Open question detected in any feature requirement
- Mechanism from `stage_4` has no phase assignment
- Page from `stage_6.sub_6b` has no phase assignment
- Token budget exceeded for any phase after attempted rebalance
- Internal consistency check fails (dangling references)
- Confidence score < 70 after one retry

**Save:** Current `context_packet` with partial `stage_10` output, stage number (10), step where halt occurred, list of specific validation failures, partial `generated_files`.

**Signal:**
```json
{
  "metadata.status": "needs_human",
  "metadata.escape_hatches": [{
    "stage": 10,
    "step": "step_name",
    "reason": "description",
    "details": { "uncovered_mechanisms": [], "dangling_refs": [], "budget_overflow": [] },
    "suggested_actions": ["Re-run Stage 7 with constraint X", "Resolve open question in Stage Y"]
  }]
}
```

## Example

**Input** (abbreviated):
```json
{
  "stage_0": { "tech_stack": { "framework": "react", "database": "supabase", "build_command": "npm run build", "lint_command": "npm run lint" } },
  "stage_3": { "concept_and_context": { "name": "TaskFlow", "description": "Team task management app" }, "drift_anchor": "Task management for small teams" },
  "stage_7": { "phases": [{ "phase_number": 1, "features": ["auth", "db-setup"], "files_allowed": ["src/lib/supabase.ts"] }, { "phase_number": 2, "features": ["task-board"], "files_allowed": ["src/components/Board.tsx"] }], "token_budget": { "per_phase": { "1": 20000, "2": 25000 } } }
}
```

**Output** (abbreviated):
```json
{
  "stage_10": {
    "output_manifest": [
      { "file_path": "phases/phase-1.md", "file_type": "phase", "estimated_tokens": 45000 },
      { "file_path": "phases/phase-2.md", "file_type": "phase", "estimated_tokens": 50000 },
      { "file_path": "build.sh", "file_type": "build_script", "estimated_tokens": 2000 },
      { "file_path": "CLAUDE.md", "file_type": "claude_md", "estimated_tokens": 3000 },
      { "file_path": "BUILD_RULES.md", "file_type": "build_rules", "estimated_tokens": 8000 },
      { "file_path": "README.md", "file_type": "readme", "estimated_tokens": 1500 }
    ],
    "generated_files": {
      "phases/phase-1.md": "# Phase 1: Foundation\n\n## Build Rules Preamble\n...[9 sections]...\n## Gate Condition\nALL FOUR STEPS MUST PASS BEFORE PHASE 2 BEGINS",
      "phases/phase-2.md": "# Phase 2: Task Board\n...[9 sections]...\n## Gate Condition\nPIPELINE COMPLETE",
      "build.sh": "#!/bin/bash\nset -e\n\nrun_phase() {\n  SNAPSHOT=$(git rev-parse HEAD)\n  npm run build || { echo 'ABORT'; exit 1; }\n  # ... agent work ...\n  npm run build && npm run lint || { git reset --hard $SNAPSHOT; exit 1; }\n}\n\nrun_phase 1 && run_phase 2",
      "CLAUDE.md": "# Build Rules\n## Architecture Principles\n- Components do ONE thing...",
      "BUILD_RULES.md": "# Build Rules Reference\n## Debugging Protocol\n...",
      "README.md": "# TaskFlow\nTeam task management app..."
    },
    "build_script_config": { "snapshot_enabled": true, "rollback_enabled": true, "forbidden_file_detection": true, "two_strike_retry": true, "chaining_operator": "&&" },
    "platform_target": "claude_cli",
    "claude_md_content": "# Build Rules\n...",
    "build_rules_content": "# Build Rules Reference\n...",
    "final_validation": { "open_questions_count": 0, "all_phases_fit_budget": true, "all_mechanisms_covered": true, "all_pages_covered": true }
  }
}
```

The output contains ONLY the structured file package. No conversational text. Each phase file is independently consumable. The build.sh chains them with `&&` and includes two-strike retry.


---
## REFERENCE: build-rules-sections

# BUILD_RULES.md — Section Templates

> Detailed reference playbook. Lives alongside CLAUDE.md in repo root.
> CLAUDE.md points to specific sections here for deeper protocols.
> Derived from Martin's 13 modules, adapted to the user's tech stack.

---

## Section Map

| Section | Source Module | Purpose |
|---------|-------------|---------|
| Debugging Protocol | Martin Module 08 (Bug Fix) | Step-by-step bug fixing methodology |
| Trace-First Debugging | Martin Module 10 (Debug) | Deep debugging with tracing |
| Feature Addition Protocol | Martin Module 09 (Feature Add) | How to add features safely |
| Testing & Verification | Martin Module 13 (Testing) | Testing standards and checklist |
| Data Access Patterns | Martin Module 03 (Data Layer) | Database and data layer conventions |
| Entity CRUD Pattern | Martin Module 05 (CRUD Flow) | Standard CRUD implementation pattern |

---

## Section Templates

### Debugging Protocol

```markdown
## Debugging Protocol

When you encounter a bug, follow this sequence. Do NOT skip steps.

### 1. Reproduce
- Identify the exact steps that trigger the bug
- Note the expected vs actual behavior
- Check if the bug is consistent or intermittent

### 2. Read the Error
- Read the FULL error message and stack trace
- Identify the file and line number
- Note any relevant variable values

### 3. Trace the Path
- Start at the error location
- Trace backwards through the call stack
- Identify where the data becomes incorrect
- Map the flow: {source} → {transform} → {destination} → {error}

### 4. Isolate
- Determine the smallest change that causes the bug
- Check: is this a data problem, logic problem, or timing problem?
- Check recent changes: `git log --oneline -10`

### 5. Fix
- Fix the ROOT CAUSE, not the symptom
- Make the minimal change needed
- Don't refactor while fixing — that's a separate task

### 6. Verify
```bash
# Run build
{build_command}

# Run tests
{test_command}

# Verify the specific bug is fixed
{manual_verification_step}

# Verify nothing else broke
{lint_command}
```

### 7. Document
- If the bug was non-obvious, add a comment explaining WHY the fix works
- If it could happen again, consider adding a test
```

---

### Trace-First Debugging

```markdown
## Trace-First Debugging

For complex bugs where the Debugging Protocol didn't find the root cause.

### Approach
1. Add logging at EVERY step of the suspected code path
2. Log inputs, outputs, and intermediate values
3. Run the reproduction steps
4. Read the trace from start to finish
5. The bug is where the trace diverges from expectations

### Trace Template
```{language}
// At function entry
console.log('[{function_name}] INPUT:', JSON.stringify({params}));

// At decision points
console.log('[{function_name}] BRANCH:', {condition} ? 'true-path' : 'false-path');

// At function exit
console.log('[{function_name}] OUTPUT:', JSON.stringify({result}));
```

### When to Use
- The bug only appears with specific data
- The error message doesn't point to the real cause
- Multiple components interact and you're unsure which one is wrong
- The bug is timing-related (race condition, async ordering)

### Clean Up
After finding the bug, REMOVE all trace logging before committing.
```

---

### Feature Addition Protocol

```markdown
## Feature Addition Protocol

When adding a new feature, follow this sequence to avoid breaking existing code.

### 1. Understand Context
- Read ALL files that will be affected by the feature
- Identify existing patterns for similar features
- Check if a similar feature already exists (extend it, don't duplicate)

### 2. Plan the Changes
- List every file that needs modification
- List every new file to create
- Identify which existing tests need updating
- Check: does this feature touch any shared/critical files?

### 3. Implement
- Create new files FIRST (types, interfaces, utilities)
- Modify existing files SECOND (add imports, wire up)
- Follow existing patterns — if the codebase uses {pattern}, you use {pattern}
- Keep changes minimal — don't refactor while adding

### 4. Wire Up
- Update route definitions if adding a page
- Update navigation if adding a user-facing feature
- Update exports/imports in index files
- Update types if adding new data shapes

### 5. Verify
```bash
{build_command}
{lint_command}
{test_command}
```

### 6. Self-Check
- [ ] Does the feature match the requirement exactly (no more, no less)?
- [ ] Did I modify only the files that needed changing?
- [ ] Did I follow existing patterns?
- [ ] Did I update all imports and exports?
- [ ] Is error handling present at boundaries?
```

---

### Testing & Verification

```markdown
## Testing & Verification

### After Every Change
```bash
# Compile check — does it build?
{build_command}

# Lint check — does it meet code standards?
{lint_command}

# Test check — do existing tests pass?
{test_command}
```

### When to Write Tests
- New utility functions: ALWAYS
- New API endpoints: ALWAYS
- Complex business logic: ALWAYS
- Simple UI components: ONLY if they have conditional rendering logic
- Configuration changes: NEVER (just verify the build)

### Test Structure
```{language}
describe('{ComponentOrFunction}', () => {
  it('should {expected_behavior} when {condition}', () => {
    // Arrange: set up test data
    // Act: call the function / render the component
    // Assert: verify the expected outcome
  });

  it('should handle {edge_case}', () => {
    // Test the boundary condition
  });

  it('should throw/return error when {invalid_input}', () => {
    // Test error handling
  });
});
```

### Regression Checklist
After any change, manually verify:
- [ ] The changed feature works as expected
- [ ] Adjacent features still work (anything sharing state, routes, or data)
- [ ] No console errors in browser (for UI changes)
- [ ] No new lint warnings
```

---

### Data Access Patterns

```markdown
## Data Access Patterns

### Single Source of Truth
All database access goes through a dedicated data layer.
- {Database access file path from stage_0/stage_7}
- Components NEVER query the database directly
- All queries are typed and return typed results

### Query Pattern
```{language}
// GOOD: centralized, typed, reusable
export async function get{Entity}ById(id: string): Promise<{Entity}> {
  const { data, error } = await {db_client}.from('{table}').select('*').eq('id', id).single();
  if (error) throw new {EntityError}(error.message);
  return data;
}

// BAD: inline query in component
const { data } = await supabase.from('items').select('*');  // NEVER do this
```

### Mutation Pattern
```{language}
export async function create{Entity}(input: Create{Entity}Input): Promise<{Entity}> {
  // Validate input
  // Execute mutation
  // Return typed result
  // Handle errors at this layer
}
```

### Rules
- Every query function returns a typed result
- Error handling happens in the data layer, not the UI
- Queries include only the fields needed (no `select('*')` in production)
- Mutations validate input before executing
```

---

### Entity CRUD Pattern

```markdown
## Entity CRUD Pattern

When building CRUD for any entity, follow this standard pattern.

### File Structure
```
{entity_directory}/
├── {entity}.types.ts     # Types and interfaces
├── {entity}.queries.ts   # Data access (read operations)
├── {entity}.mutations.ts # Data access (write operations)
├── {entity}.list.tsx     # List/table view component
├── {entity}.detail.tsx   # Detail/single view component
├── {entity}.form.tsx     # Create/edit form component
└── {entity}.test.ts      # Tests
```

### Implementation Order
1. Types first — define the entity shape
2. Queries — read operations (list, getById, search)
3. Mutations — write operations (create, update, delete)
4. List view — display all entities
5. Detail view — display single entity
6. Form — create and edit
7. Wire up routes and navigation

### Standard Operations
| Operation | Function | Route |
|-----------|----------|-------|
| List | `get{Entity}List()` | `/{entities}` |
| Detail | `get{Entity}ById(id)` | `/{entities}/:id` |
| Create | `create{Entity}(input)` | `/{entities}/new` |
| Update | `update{Entity}(id, input)` | `/{entities}/:id/edit` |
| Delete | `delete{Entity}(id)` | N/A (action on detail page) |

### Rules
- Always include loading states
- Always include error states
- Always include empty states (no data)
- Delete requires confirmation
- Forms validate before submission
- Optimistic updates where appropriate (list operations)
```

---

## Rendering Rules

1. Replace ALL `{placeholders}` with actual values from `stage_0.tech_stack`
2. Replace `{language}` with the stack's primary language (typescript, python, etc.)
3. Replace `{build_command}`, `{lint_command}`, `{test_command}` with actual commands
4. Replace `{db_client}` with the actual database client name
5. If a section is not applicable to the tech stack (e.g., "Entity CRUD Pattern" for a CLI tool), omit it entirely
6. Martin's name NEVER appears. Rules are presented as project conventions.
7. Keep each section focused — no cross-references between BUILD_RULES.md sections
8. CLAUDE.md references these sections by exact name — section headings must be stable


---
## REFERENCE: build-sh-template

# build.sh Template

> Deterministic bash wrapper that chains phase execution with verification.
> Uses `&&` chaining (NEVER `;`). Failure in any phase stops the pipeline.

---

## Template

```bash
#!/bin/bash
set -e

# ============================================================
# {PRODUCT_NAME} — Automated Build Script
# Generated by PRD Maker Pipeline (Stage 10)
# Platform: {platform_target}
# Phases: {phase_count}
# ============================================================

# --- Configuration ---
BUILD_CMD="{stage_0.tech_stack.build_command}"    # e.g., "npm run build"
LINT_CMD="{stage_0.tech_stack.lint_command}"       # e.g., "npm run lint"
TEST_CMD="{stage_0.tech_stack.test_command}"       # e.g., "npm run test"
PHASE_DIR="./phases"
MAX_RETRIES=2  # Two-strike rule: 2 failures = stop for human

# --- Helper Functions ---

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

take_snapshot() {
  git rev-parse HEAD
}

validate_build() {
  log "Running build validation..."
  $BUILD_CMD || return 1
  $LINT_CMD || return 1
  log "Build validation passed."
}

check_forbidden_files() {
  local SNAPSHOT=$1
  local PHASE_NUM=$2
  local FORBIDDEN_PATTERN=$3

  if [ -z "$FORBIDDEN_PATTERN" ]; then
    return 0
  fi

  FORBIDDEN_CHANGES=$(git diff --name-only "$SNAPSHOT" | grep -E "$FORBIDDEN_PATTERN" || true)
  if [ -n "$FORBIDDEN_CHANGES" ]; then
    log "FAIL: Phase $PHASE_NUM modified forbidden files:"
    echo "$FORBIDDEN_CHANGES"
    return 1
  fi
  return 0
}

run_phase() {
  local PHASE_NUM=$1
  local PHASE_FILE="$PHASE_DIR/phase-${PHASE_NUM}.md"
  local FORBIDDEN_PATTERN=$2  # Regex of forbidden file paths

  if [ ! -f "$PHASE_FILE" ]; then
    log "ERROR: $PHASE_FILE not found"
    exit 1
  fi

  log "=========================================="
  log "PHASE $PHASE_NUM: Starting"
  log "=========================================="

  # --- DETERMINISTIC: Snapshot ---
  local SNAPSHOT
  SNAPSHOT=$(take_snapshot)
  log "Snapshot: $SNAPSHOT"

  # --- DETERMINISTIC: Pre-build validation ---
  validate_build || {
    log "ABORT: Build broken BEFORE phase $PHASE_NUM started"
    exit 1
  }

  # --- AI AGENT: Creative work ---
  log "Phase $PHASE_NUM: Executing agent with $PHASE_FILE"
  # {PLATFORM_SPECIFIC_AGENT_COMMAND}
  # For claude_cli:  claude --print "$PHASE_FILE"
  # For codex_cli:   codex --file "$PHASE_FILE"
  # For gemini_cli:  gemini --file "$PHASE_FILE"
  # For manual:      echo "Paste contents of $PHASE_FILE into your agent"

  # --- DETERMINISTIC: Post-build validation ---
  validate_build || {
    log "FAIL: Build broken after phase $PHASE_NUM"
    git reset --hard "$SNAPSHOT"
    log "Rolled back to $SNAPSHOT"
    return 1
  }

  # --- DETERMINISTIC: Forbidden file detection ---
  check_forbidden_files "$SNAPSHOT" "$PHASE_NUM" "$FORBIDDEN_PATTERN" || {
    git reset --hard "$SNAPSHOT"
    log "Rolled back to $SNAPSHOT due to forbidden file modification"
    return 1
  }

  # --- DETERMINISTIC: Commit ---
  git add -A
  git commit -m "Phase $PHASE_NUM complete"
  log "Phase $PHASE_NUM: PASSED"
}

run_phase_with_retry() {
  local PHASE_NUM=$1
  local FORBIDDEN_PATTERN=$2
  local ATTEMPT=1

  while [ $ATTEMPT -le $MAX_RETRIES ]; do
    log "Phase $PHASE_NUM — Attempt $ATTEMPT of $MAX_RETRIES"

    if run_phase "$PHASE_NUM" "$FORBIDDEN_PATTERN"; then
      return 0
    fi

    log "Phase $PHASE_NUM failed on attempt $ATTEMPT"
    ATTEMPT=$((ATTEMPT + 1))

    if [ $ATTEMPT -le $MAX_RETRIES ]; then
      log "Retrying with fresh agent..."
    fi
  done

  log "============================================"
  log "STOPPED: Phase $PHASE_NUM failed $MAX_RETRIES times."
  log "The problem is likely in the phase spec, not the agent."
  log "Human review required."
  log "============================================"
  exit 1
}

# --- Main Execution ---

log "Starting build: {PRODUCT_NAME}"
log "Phases: {phase_count}"
log "Platform: {platform_target}"

# {PHASE_EXECUTION_BLOCK}
# Generated per phase. Example for 3 phases:

run_phase_with_retry 1 "{phase_1_forbidden_pattern}" && \
run_phase_with_retry 2 "{phase_2_forbidden_pattern}" && \
run_phase_with_retry 3 "{phase_3_forbidden_pattern}"

log "============================================"
log "BUILD COMPLETE: All {phase_count} phases passed."
log "============================================"
```

---

## Rendering Rules

1. Replace `{PRODUCT_NAME}` with `stage_3.concept_and_context.name`
2. Replace `{platform_target}` with the chosen platform enum
3. Replace `{phase_count}` with length of `stage_7.phases`
4. Replace `BUILD_CMD`, `LINT_CMD`, `TEST_CMD` with actual values from `stage_0.tech_stack`
5. Generate one `run_phase_with_retry N "pattern"` call per phase, chained with `&&`
6. Build `FORBIDDEN_PATTERN` per phase from `stage_7.phases[N].files_forbidden` as a grep-compatible regex (pipe-separated paths, escaped dots)
7. The agent command inside `run_phase()` is platform-specific — see `platform-wrappers.md` for the correct command per platform
8. `MAX_RETRIES` is always 2 (from `stage_9.two_strike_rule.max_retries`)
9. If `stage_9.verification_mode` is `automated_agent_b`, add Agent B verification call between agent work and commit (see Stage 9 output for the exact command)
10. If platform is `bolt` or `lovable`, replace `run_phase` body with manual instructions (no bash automation available)

## Platform-Specific Agent Commands

| Platform | Command in `run_phase()` |
|----------|-------------------------|
| `claude_cli` | `claude --print "$(cat $PHASE_FILE)"` |
| `codex_cli` | `codex run --prompt-file "$PHASE_FILE"` |
| `gemini_cli` | `gemini code --prompt-file "$PHASE_FILE"` |
| `cursor` | `echo "Open terminal in Cursor, paste contents of $PHASE_FILE"` |
| `windsurf` | `echo "Open terminal in Windsurf, paste contents of $PHASE_FILE"` |
| `bolt` / `lovable` | `echo "Manual: Copy $PHASE_FILE content into platform chat"` |
| `generic` | `echo "Paste contents of $PHASE_FILE into your coding agent"` |


---
## REFERENCE: claude-md-template

# CLAUDE.md Template

> Quick-reference guardrails file. Lives in repo root FOREVER.
> Read by EVERY agent interaction — even "fix this button color."
> MUST be under 500 lines. Tight, fast, actionable.
> Points to BUILD_RULES.md for deeper protocols.

---

## Template

```markdown
# {PRODUCT_NAME}

> {One-line product description from stage_3.concept_and_context}

## Architecture Principles

{Distilled from stage_5.build_rules_applied. 10-15 rules max.}

- Components do ONE thing. If it does two things, split it.
- State lives at the lowest possible level. Don't hoist unless required.
- No file over 300 lines. Split at 250.
- Imports flow downward. Never circular.
- UI components don't contain business logic.
- Every function has a single responsibility.
- Error handling at boundaries, not everywhere.
- {Stack-specific: e.g., "All Supabase queries go through src/lib/db.ts"}
- {Stack-specific: e.g., "Auth state managed exclusively in AuthContext"}
- {Stack-specific: e.g., "Server actions in app/actions/, never in components"}

## Modification Rules

- Before editing ANY file, read it completely first.
- Don't refactor code you didn't write unless explicitly asked.
- Don't add features that weren't requested.
- Don't "improve" working code while fixing a bug.
- Keep existing patterns. Match the style that's there.
- When in doubt, check how similar code is written elsewhere in the project.

## Testing Protocol

After ANY change, verify:

```bash
# 1. Does it compile?
{build_command}

# 2. Does it lint?
{lint_command}

# 3. Do tests pass? (if tests exist)
{test_command}

# 4. Do existing features still work? (manual check for UI changes)
```

Don't delete tests. Don't skip tests. Don't modify tests to make them pass.

## Tech Stack

{From stage_0.tech_stack — concise reference.}

| Layer | Technology |
|-------|-----------|
| Framework | {framework} |
| Language | {language} |
| Database | {database} |
| Auth | {auth_provider} |
| Hosting | {hosting} |
| Styling | {styling} |

## File Structure

{Generated from stage_6.sub_6a (page arrangement) + stage_7.phases (file sandboxes).}

```
{project_root}/
├── src/
│   ├── components/     # UI components ({component_list})
│   ├── lib/            # Shared utilities ({utility_list})
│   ├── contexts/       # State management ({context_list})
│   ├── pages/          # Page components ({page_list})
│   └── types/          # TypeScript types
├── {api_directory}/    # API routes / server functions
├── {db_directory}/     # Database schema / migrations
├── CLAUDE.md           # This file (guardrails)
├── BUILD_RULES.md      # Detailed protocols
└── {config_files}      # Config (DO NOT MODIFY without reason)
```

## Key Files (Don't Break These)

{Critical files that should rarely be modified. From stage_7 sandbox forbidden lists.}

- `{auth_file}` — Authentication setup. Modify ONLY if auth feature is explicitly requested.
- `{db_config_file}` — Database connection. Almost never needs changes.
- `{env_file}` — Environment variables. NEVER commit secrets.
- `{config_files}` — Build config. Change only if build is broken.

## When Debugging

Follow the debugging protocol in BUILD_RULES.md Section "Debugging Protocol."

1. Read the error message completely
2. Find the actual file and line causing the error
3. Trace the data flow from source to error
4. Fix the root cause, not the symptom
5. Verify the fix doesn't break anything else

Do NOT guess at fixes. Trace the actual error path first.

## When Adding Features

Follow the feature addition protocol in BUILD_RULES.md Section "Feature Addition Protocol."

1. Read all connected files before modifying any of them
2. Check if a similar feature already exists (follow its pattern)
3. Create new files for new features — don't bloat existing files
4. Update imports and exports
5. Run the full testing protocol

## When Reviewing Code

Check BUILD_RULES.md Section "Testing & Verification" for the full review checklist.

Quick checks:
- Does it compile and lint?
- Does it match existing patterns?
- Are there any hardcoded values that should be config?
- Is error handling present at boundaries?
- Are there any security concerns (exposed secrets, missing auth checks)?
```

---

## Rendering Rules

1. Replace `{PRODUCT_NAME}` with `stage_3.concept_and_context.name`
2. Replace `{build_command}`, `{lint_command}`, `{test_command}` from `stage_0.tech_stack`
3. Generate "Architecture Principles" from `stage_5.build_rules_applied` — pick the 10-15 most impactful rules, adapted to the tech stack
4. Generate "File Structure" tree from `stage_6.sub_6a` page arrangement and `stage_7.phases` file sandbox declarations — show the actual project structure
5. Generate "Key Files" from the union of all phases' `files_forbidden` lists
6. Keep all BUILD_RULES.md section references accurate — section names must match what Step 5 generates
7. Martin's rules are EMBEDDED as architecture principles — NEVER reference "Martin" by name
8. Total output MUST be under 500 lines. If approaching the limit, remove examples rather than removing rules
9. Every bash command must be copy-paste ready (no placeholders in the final output)


---
## REFERENCE: phase-file-template

# Phase File Template — 9-Section Format

> Each `phase-N.md` is a standalone, copy-paste-ready build document.
> A fresh agent receiving ONLY this file can execute the phase without additional context.

---

## Template

```markdown
# Phase {N}: {Phase Title}

> **Product**: {product_name} — {one-line description from stage_3.drift_anchor}
> **Phase**: {N} of {total_phases}
> **Token Budget**: {content_tokens} content + {overhead_tokens} overhead = {total_tokens} total

---

## 1. Build Rules Preamble

{~8,000 tokens. The agent's operating manual for HOW to behave.}

### Architecture Principles

{Derived from stage_5.build_rules_applied. Adapt to stage_0.tech_stack.}

- Components do ONE thing. If it does two things, split it.
- State lives at the lowest possible level. Don't hoist unless required.
- No file over 300 lines. Split at 250.
- Imports flow downward. Never circular.
- UI components don't contain business logic.
- {Stack-specific rules based on stage_0.tech_stack.framework}

### Modification Rules

- Read every file completely before editing it.
- Don't refactor code you didn't write unless explicitly instructed.
- Don't add features that weren't requested in this phase.
- Don't "improve" working code while fixing a bug.
- Match existing patterns. If the codebase uses X, you use X.

### Coding Standards

{From stage_5.build_rules_applied — stack-specific.}

- {Language-specific rules: TypeScript strict mode, Python type hints, etc.}
- {Import ordering convention}
- {Error handling convention}
- {Naming conventions}

### Product Context

{From stage_3.drift_anchor — keeps agent centered on the original vision.}

This phase is part of building **{product_name}**: {drift_anchor_text}.
Do NOT drift from this vision. If a feature seems to contradict the product
concept, flag it rather than improvising.

---

## 2. File Sandbox Declaration

{~2,000 tokens. Three explicit lists.}

### Files You CAN Modify (Create or Edit)

{From stage_7.phases[N].files_allowed}

```
{file_path_1}
{file_path_2}
...
```

### Files You CAN Read (But NOT Modify)

{From stage_7.phases[N].files_read_only}

```
{file_path_1}
{file_path_2}
...
```

### Files You CANNOT Touch

{From stage_7.phases[N].files_forbidden}

```
{file_path_1}
{file_path_2}
...
```

**Rule**: If `git diff` at the end shows ANY file not in the "CAN Modify" list
was changed, the phase FAILS verification.

---

## 3. Build Order with Pulse Points

{~3,000 tokens. Numbered implementation sequence with verification triggers.}

{From stage_7.mandatory_build_order + stage_8.protocol_injected_phases[N].pulse_checks}

### Implementation Sequence

1. **{Feature/Task 1}**: {description}
   - Files: `{file_1}`, `{file_2}`
   - Expected: {what should exist after this step}

{PULSE CHECK after step 1}:
- [ ] `{build_command}` exits 0
- [ ] `{lint_command}` exits 0
- [ ] Created files exist and export expected symbols

2. **{Feature/Task 2}**: {description}
   - Files: `{file_3}`, `{file_4}`
   - Expected: {what should exist after this step}

3. **{Feature/Task 3}**: {description}
   - Files: `{file_5}`
   - Expected: {what should exist after this step}

{PULSE CHECK after step 3}:
- [ ] All prior checks still pass
- [ ] New components render without errors
- [ ] {Feature-specific check}

{Continue for all features in this phase...}

---

## 4. Seam Check Definitions

{~2,000 tokens. Integration verification points where components meet.}

{From stage_8.protocol_injected_phases[N].seam_checks}

| Seam | Components | Verification |
|------|-----------|-------------|
| {seam_1_name} | `{component_A}` ↔ `{component_B}` | {How to verify the integration works} |
| {seam_2_name} | `{component_C}` ↔ `{component_D}` | {How to verify} |

### Seam Verification Commands

```bash
# Seam 1: {name}
{verification_command_1}

# Seam 2: {name}
{verification_command_2}
```

---

## 5. Objective and Feature Requirements

{Variable tokens. The actual implementation instructions — WHAT to build.}

{Cross-reference: stage_7.phases[N].features + stage_4.mechanisms + stage_6.sub_6b}

### Phase Objective

{One paragraph: what this phase accomplishes in the overall build.}

### Feature: {feature_name_1}

**Mechanism**: {mechanism_id} — {mechanism_name} from Stage 4
**Classification**: {WALL | DOOR | ROOM} from Stage 5
**Page**: {page_name} from Stage 6b (if applicable)

**Requirements**:
1. {Specific, actionable requirement with file path and expected behavior}
2. {Specific requirement}
3. {Specific requirement}

**Acceptance Criteria**:
- [ ] {Testable criterion}
- [ ] {Testable criterion}

### Feature: {feature_name_2}

{Same structure...}

---

## 6. Pattern References

{From stage_5.mechanism_blueprints — file:line references.}

When implementing features in this phase, follow these existing patterns:

| Pattern | Reference | Used For |
|---------|-----------|----------|
| {pattern_name_1} | `{file_path}:{line_range}` | {Which feature/mechanism} |
| {pattern_name_2} | `{file_path}:{line_range}` | {Which feature/mechanism} |

**Wall patterns** (deterministic — implement exactly as shown):
- {pattern reference}

**Door patterns** (constrained — follow the structure, adapt the specifics):
- {pattern reference}

**Room patterns** (creative — use as inspiration, not prescription):
- {pattern reference}

---

## 7. Violation Handling Instructions

{~2,000 tokens. Decision tree for when rules are broken.}

{From stage_8.protocol_injected_phases[N].violation_rules}

| Severity | Trigger | Action |
|----------|---------|--------|
| **LOW** | Style inconsistency, minor naming deviation | Log the issue. Continue building. Fix in cleanup pass. |
| **MEDIUM** | Modified a read-only file, missing an export | Stop current feature. Fix the violation. Then continue. |
| **HIGH** | Modified a forbidden file, broke existing tests | Rollback to last pulse point. Re-implement from that checkpoint. |
| **CRITICAL** | Security violation, deleted required files, data loss risk | Full stop. Rollback entire phase. Flag for human review. |

### Self-Detection Protocol

After each pulse check, verify:
1. Run `git diff --name-only {BASELINE}` — are all changed files in the "CAN Modify" list?
2. Run `{build_command}` — does it still pass?
3. Run `{test_command}` (if tests exist) — do they still pass?

If any check fails, classify the violation using the table above and take the
prescribed action.

---

## 8. Full Checkpoint at End

{~5,000 tokens. The final verification gate for this phase.}

{From stage_8.protocol_injected_phases[N].full_checkpoint}

### Step 1: Self-Report

List every file you created or modified in this phase:

```
{Expected to be filled by the agent during execution}
```

### Step 2: Diff Check

Run:
```bash
git diff {PHASE_N_BASELINE}..HEAD --name-only
```

Compare the output against:
- Your self-report (Step 1) — every file in the diff must be in your report
- The "CAN Modify" list (Section 2) — every file in the diff must be allowed
- **Mismatch between self-report and diff is itself a violation.**

### Step 3: Violation Response

For any file in the diff NOT in the allowed list:
- Apply the violation severity table from Section 7
- Take the prescribed action
- Document: "Violation detected: {file} — severity: {level} — action: {taken}"

### Step 4: Functional Verification

```bash
# Compile check
{build_command}

# Lint check
{lint_command}

# Test check (if applicable)
{test_command}

# Render check (if UI phase)
{render_check_command}
```

ALL FOUR STEPS must produce exit code 0.

---

## 9. Gate Condition

**ALL FOUR CHECKPOINT STEPS MUST PASS BEFORE PHASE {N+1} BEGINS.**

{For the final phase, replace with: "ALL FOUR CHECKPOINT STEPS MUST PASS. PIPELINE COMPLETE."}

If any step fails:
1. Classify the failure severity
2. Apply violation handling (Section 7)
3. Re-run the checkpoint
4. If it fails again, stop for human review (two-strike rule)
```

---

## Rendering Rules

1. Replace ALL `{placeholders}` with actual values from the context packet
2. Martin's rules appear as architecture principles and coding standards — NEVER reference "Martin" by name
3. Each phase file is 100% self-contained — no `See phase-1.md` references
4. Every feature requirement must be specific enough to implement without asking questions
5. File paths in sandbox lists are exact (no globs unless the phase spec uses globs)
6. Pulse check commands use the actual build/lint/test commands from `stage_0.tech_stack`
7. Overhead tokens (~25,000 per phase) are the sections 1-4 + 7-9. Section 5-6 tokens come from the phase's content budget.


---
## REFERENCE: platform-wrappers

# Platform Wrappers — Execution Instructions Per Platform

> Phase file CONTENT is identical across all platforms.
> Only the execution method and wrapper instructions change.
> This file provides per-platform instructions included in README.md.

---

## Platform Matrix

| Platform | Enum Value | Terminal? | Automation | Agent Command |
|----------|-----------|-----------|-----------|---------------|
| Claude Code CLI | `claude_cli` | Yes | Full | `claude --print "$(cat phase-N.md)"` |
| Claude Code Web | `claude_web` | No | Manual | Copy-paste phase-N.md content |
| Codex CLI | `codex_cli` | Yes | Full | `codex run --prompt-file phase-N.md` |
| Gemini CLI | `gemini_cli` | Yes | Full | `gemini code --prompt-file phase-N.md` |
| Cursor | `cursor` | Yes | Semi | Paste into Cursor terminal/chat |
| Windsurf | `windsurf` | Yes | Semi | Paste into Windsurf terminal/chat |
| Bolt | `bolt` | No | Manual | Paste into Bolt chat interface |
| Lovable | `lovable` | No | Manual | Paste into Lovable chat interface |
| Generic | `generic` | Varies | Manual | Paste into any coding agent |

---

## Per-Platform README Instructions

### claude_cli

```markdown
## How to Build

### Automated (Recommended)
```bash
chmod +x build.sh
bash build.sh
```

The build script will:
1. Take a git snapshot before each phase
2. Run pre-build validation (build + lint)
3. Execute the phase via Claude Code CLI
4. Run post-build validation
5. Check for forbidden file modifications
6. Commit and continue to the next phase
7. Auto-retry failed phases (2 attempts max)

### Manual (If build.sh fails)
If the script stops at Phase N:
1. Open `phases/phase-N.md`
2. Run: `claude --print "$(cat phases/phase-N.md)"`
3. After completion, run build + lint manually
4. Continue with Phase N+1

### Hybrid
Run `build.sh`. If it crashes at Phase 3, open `phases/phase-3.md`
and pick up manually from there. Each phase is self-contained.
```

---

### claude_web

```markdown
## How to Build

1. Open Claude Code in your browser
2. Open `phases/phase-1.md`
3. Copy the ENTIRE contents and paste into the chat
4. Wait for the agent to complete Phase 1
5. Verify: run `{build_command}` and `{lint_command}` in your terminal
6. If both pass, proceed to Phase 2
7. Repeat for each phase in order

**Important**: Each phase is self-contained. The agent does not need
context from previous phases — each phase file includes everything needed.

**Between phases**: Wait 2-3 minutes for rate limits to reset.
```

---

### codex_cli

```markdown
## How to Build

### Automated
```bash
chmod +x build.sh
bash build.sh
```

### Manual
```bash
codex run --prompt-file phases/phase-1.md
{build_command} && {lint_command}
# If passes, continue:
codex run --prompt-file phases/phase-2.md
{build_command} && {lint_command}
# ... repeat for all phases
```
```

---

### gemini_cli

```markdown
## How to Build

### Automated
```bash
chmod +x build.sh
bash build.sh
```

### Manual
```bash
gemini code --prompt-file phases/phase-1.md
{build_command} && {lint_command}
# If passes, continue:
gemini code --prompt-file phases/phase-2.md
{build_command} && {lint_command}
# ... repeat for all phases
```
```

---

### cursor

```markdown
## How to Build

1. Open the project in Cursor
2. Open `phases/phase-1.md`
3. Copy the contents and paste into Cursor's AI chat (Cmd+L / Ctrl+L)
4. Let the agent implement Phase 1
5. Open terminal (Ctrl+`) and verify:
   ```bash
   {build_command} && {lint_command}
   ```
6. If both pass, proceed to Phase 2
7. Repeat for each phase

**Tip**: Use Cursor's terminal to run verification commands between phases.
```

---

### windsurf

```markdown
## How to Build

1. Open the project in Windsurf
2. Open `phases/phase-1.md`
3. Copy the contents and paste into Windsurf's Cascade chat
4. Let the agent implement Phase 1
5. Open terminal and verify:
   ```bash
   {build_command} && {lint_command}
   ```
6. If both pass, proceed to Phase 2
7. Repeat for each phase
```

---

### bolt

```markdown
## How to Build

Bolt does not have terminal access. Follow these steps:

1. Open Bolt and start a new project
2. Open `phases/phase-1.md` in a text editor
3. Copy the ENTIRE contents and paste into Bolt's chat
4. Wait for the agent to complete Phase 1
5. Download the project and verify locally:
   ```bash
   {build_command} && {lint_command}
   ```
6. If verification passes, go back to Bolt
7. Open `phases/phase-2.md` and paste into chat
8. Repeat for each phase

**Important**: Since Bolt has no terminal, you must download and
verify locally between phases. Do NOT skip verification.
```

---

### lovable

```markdown
## How to Build

Lovable does not have terminal access. Follow these steps:

1. Open Lovable and start a new project
2. Open `phases/phase-1.md` in a text editor
3. Copy the ENTIRE contents and paste into Lovable's prompt
4. Wait for the agent to complete Phase 1
5. Use Lovable's preview to visually verify the output
6. Export to GitHub and verify locally:
   ```bash
   git clone {repo_url}
   cd {project_name}
   {build_command} && {lint_command}
   ```
7. If verification passes, continue to Phase 2
8. Repeat for each phase

**Important**: Export and verify locally between phases.
```

---

### generic

```markdown
## How to Build

This build package works with any coding agent.

### Steps
1. Open `phases/phase-1.md` in a text editor
2. Copy the ENTIRE contents
3. Paste into your coding agent of choice
4. Wait for completion
5. Verify in terminal:
   ```bash
   {build_command} && {lint_command}
   ```
6. If both pass, continue to Phase 2
7. Repeat for each phase in order

### Key Points
- Each phase file is self-contained (no cross-references)
- Phases must be executed in order (1, 2, 3...)
- Verify build + lint between every phase
- If a phase fails, re-run it from scratch (don't try to fix partial work)
- `CLAUDE.md` stays in the repo forever — any future agent interaction will read it
```

---

## Rendering Rules

1. Replace `{build_command}` and `{lint_command}` with actual commands from `stage_0.tech_stack`
2. Replace `{project_name}` with `stage_3.concept_and_context.name`
3. Include ONLY the section matching `platform_target` in the final README.md
4. For automated platforms (`claude_cli`, `codex_cli`, `gemini_cli`), always include BOTH automated and manual fallback instructions
5. For no-terminal platforms (`bolt`, `lovable`), emphasize local verification between phases
6. The `build.sh` file is always generated regardless of platform (serves as documentation even if not executable on the target platform)



---

## 🔗 Pipeline Integration — Automatic Stage Advancement

**This section is added for pipeline automation. It tells you how to signal stage completion.**

After completing ALL steps above and producing your complete output:

### Stage Completion Protocol

1. **Verify your confidence score** meets the gate threshold (≥ 70)
2. **Verify the complete JSON output** has been produced and meets the contract
3. **Output the completion marker** on its own line as the ABSOLUTE LAST thing in your response:

```
[STAGE_COMPLETE]
```

### Rules for the completion marker:

- `[STAGE_COMPLETE]` MUST be the absolute last thing in your response — nothing after it
- Your complete JSON output (context_packet) MUST come BEFORE the marker
- **Never** output `[STAGE_COMPLETE]` until the stage contract is fully met
- **Never** output `[STAGE_COMPLETE]` if the confidence score is below 70
- If you need to ask the user questions, do **NOT** output `[STAGE_COMPLETE]` — wait for answers first, produce your final output, THEN output the marker
- If the gate_result is "fail" (score < 70), trigger the escape hatch protocol instead — do NOT output `[STAGE_COMPLETE]`

### What happens when you output [STAGE_COMPLETE]:

1. The pipeline captures everything before the marker as your stage output
2. Your output becomes the input for the next stage
3. The next stage starts automatically — no manual intervention needed

### Example — end of your response:

```json
{
  "stage_10": { ... your complete output ... },
  "metadata": {
    "confidence_scores": {
      "10": { "score": 93, "gate_result": "pass" }
    }
  }
}
```

[STAGE_COMPLETE]


