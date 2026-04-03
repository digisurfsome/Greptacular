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
