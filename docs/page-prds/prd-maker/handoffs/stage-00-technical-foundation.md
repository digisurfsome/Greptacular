# Build Stage 0 Skill: Technical Foundation

> **Type:** Self-contained handoff prompt for a fresh Claude Code agent
> **Output:** `docs/page-prds/prd-maker/skills/stage-00-technical-foundation/SKILL.md`

---

## System Overview: The 10-Stage PRD Maker Pipeline

You are building one skill for a 10-stage pipeline that transforms a non-coder's messy app description into a complete, buildable technical specification. Each stage is a separate Claude Code skill. The stages run in sequence, passing a JSON data object (the "context packet") from one to the next.

### The Pipeline at a Glance

| Stage | Name | Purpose | Key Output |
|-------|------|---------|------------|
| 0 | Technical Foundation | Establish platform context (framework, DB, auth, hosting) before any idea-specific work | Platform profile + agnostic checklist reference |
| 1 | Idea Capture | Capture the user's raw brain dump with zero filtering or structure | Raw text, preserved contradictions, word count |
| 2 | Gap Analysis | Match to archetype, identify missing mechanism categories (A-N), ask targeted questions | Complete mechanism map, archetype match, gap answers |
| 3 | Agent OS Structuring | Transform messy raw material into organized concept document | Product identity, problem statement, target users, feasibility |
| 4 | Mechanism Extraction | Break structured app into discrete moving parts tagged OBVIOUS or NEEDS_EVALUATION | Mechanism list with dependencies and evaluation tags |
| 5 | 7-Question Scaffolding | Classify every process step as WALL (deterministic) / DOOR (constrained AI) / ROOM (creative) | Per-mechanism W/D/R classification with verification methods |
| 6 | Layout + Mockups + Style | Define page layouts, wireframe patterns, and design system | Per-page component specs, style tokens, typography |
| 7 | Phase Sequencing | Split the spec into buildable phases within token budgets | Phase list with token estimates, file sandbox, build order |
| 8 | Protocol Injection | Configure verification system (pulse/seam/full checks) | Check configurations, violation thresholds, escalation rules |
| 9 | Verification Agent Setup | Configure separate checker agent with git diff rules | Checker config, two-strike rule, verification mode |
| 10 | Output Generator | Produce copy-paste-ready build files | Phase files, build script, CLAUDE.md, BUILD_RULES.md |

### How Stages Connect

Every stage reads from the context packet (a JSON object) and writes its output back to the packet. The packet is saved as a snapshot after each stage. If a stage fails, the pipeline rolls back to the previous snapshot and retries or asks a human for help.

**You are building Stage 0: Technical Foundation.** It is the FIRST stage in the pipeline. It reads no prior stage output. It writes to its own namespace in the context packet, and every downstream stage (1-10) inherits the platform context it establishes.

Stage 0 is unique: it runs BEFORE the user provides any app idea. Its job is to lock down the technical environment so that all subsequent stages operate against known technical truths rather than assumptions.

---

## Your Stage: Technical Foundation

### Purpose

Stage 0 is a deterministic preamble and targeting layer that runs BEFORE any user idea input. It establishes platform context (framework, database, auth, hosting), loads the agnostic checklist resolved for the selected profile, maps the 30-category structural target model and A-N mechanism categories, defines a question budget and clarification strategy, and emits a stage contract for Stage 1. It constrains scope, loads known technical truths, and separates "already handled structure" from "unknown app mechanisms."

### Inputs (What This Stage Receives)

Stage 0 is the first stage. It has no prior stage output to read. Its inputs come directly from the user or from pipeline defaults:

- **User answers to platform questions** (may be provided or may be absent):
  - Greenfield vs existing app
  - Web / mobile / dual platform target
  - Target stack preferences (framework, database, auth, hosting)
  - Repo source (new repo, existing repo, boilerplate)
  - Deployment target
- **Available boilerplate library** (hardcoded in the skill): list of supported stack profiles with their capabilities
- **Default stack configuration**: the recommended stack when the user has no preference
- **Martin agnostic checklist** (loaded from reference file): ~192 structural rules across 22 categories + 43 banned patterns
- **Industry standards supplement checklist** (loaded from reference file): 71 additional rules across 10 gap areas

### Outputs (What This Stage Produces)

Written to `context_packet.stage_0`:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `platform_profile` | `object` | Yes | Selected platform/boilerplate configuration |
| `platform_profile.boilerplate_id` | `string` | Yes | One of: `"supabase_web"`, `"flutter_mobile"`, `"dual"`, `"no_boilerplate"`, `"raw_checklist"` |
| `platform_profile.boilerplate_name` | `string` | Yes | Human-readable name (e.g., "Supabase Web Starter") |
| `platform_profile.description` | `string` | Yes | Brief description of what this boilerplate provides |
| `tech_stack` | `object` | Yes | Technology decisions |
| `tech_stack.framework` | `string` | Yes | Primary framework (e.g., `"Next.js"`, `"Flutter"`, `"none"`) |
| `tech_stack.database` | `string` | Yes | Database choice (e.g., `"Supabase/Postgres"`, `"Firebase"`, `"none"`) |
| `tech_stack.auth_provider` | `string` | Yes | Auth provider (e.g., `"Supabase Auth"`, `"custom"`, `"none"`) |
| `tech_stack.hosting` | `string` | Yes | Hosting target (e.g., `"Vercel"`, `"AWS"`, `"undecided"`) |
| `tech_stack.additional` | `object` | No | Any additional stack decisions (key-value pairs) |
| `checklist_rule_ids` | `string[]` | Yes | Agnostic checklist rule IDs that apply to this stack |
| `command_allowlist` | `string[]` | No | Project-specific allowed bash commands |
| `resolved_rules` | `object[]` | Yes | Each Martin rule tagged with resolution status |
| `resolved_rules[].rule_id` | `string` | Yes | Rule identifier (e.g., `"stack-1"`, `"file-3"`) |
| `resolved_rules[].resolution` | `string` | Yes | One of: `"MATCH"`, `"REPLACE"`, `"ENHANCE"`, `"HANDLED"`, `"N/A"` |
| `resolved_rules[].priority` | `string` | Yes | One of: `"critical"`, `"important"`, `"nice"` |
| `resolved_rules[].enforcement` | `string` | Yes | One of: `"hard"`, `"soft"` |
| `resolved_rules[].evidence` | `string` | No | File path, config, or test artifact that satisfies this rule |
| `structural_coverage` | `object` | Yes | 30-category structural target model |
| `structural_coverage.categories` | `object[]` | Yes | Array of category coverage entries |
| `structural_coverage.categories[].name` | `string` | Yes | Category name from the structural checklist |
| `structural_coverage.categories[].status` | `string` | Yes | One of: `"covered_by_preamble"`, `"provided_by_user"`, `"missing"` |
| `mechanism_target` | `object` | Yes | A-N mechanism category target model |
| `mechanism_target.categories` | `object[]` | Yes | Array of A-N category entries |
| `mechanism_target.categories[].id` | `string` | Yes | Category letter (A-N) |
| `mechanism_target.categories[].name` | `string` | Yes | Category name |
| `mechanism_target.categories[].status` | `string` | Yes | One of: `"covered_by_boilerplate"`, `"needs_user_input"`, `"not_applicable"` |
| `assumptions` | `object[]` | Yes | Every auto-filled default logged as an assumption |
| `assumptions[].field` | `string` | Yes | Which field was assumed |
| `assumptions[].value` | `string` | Yes | The assumed value |
| `assumptions[].confidence` | `string` | Yes | One of: `"known"`, `"inferred"`, `"assumed"` |
| `assumptions[].reversal_cost` | `string` | Yes | One of: `"low"`, `"medium"`, `"high"` |
| `assumptions[].source` | `string` | Yes | Why this assumption was made |
| `question_budget` | `object` | Yes | Clarification strategy for downstream stages |
| `question_budget.mode` | `string` | Yes | One of: `"full_detail"`, `"minimal_input"`, `"zero_input"` |
| `question_budget.max_rounds` | `integer` | Yes | Maximum question rounds before fallback inference |
| `question_budget.blocking_questions_only` | `boolean` | Yes | If true, only ask questions that block progress |
| `stage_contract` | `object` | Yes | Contract for Stage 0 completion and Stage 1 entry |
| `stage_contract.stop_go` | `string` | Yes | One of: `"go"`, `"conditional"`, `"stop"` |
| `stage_contract.unresolved_blockers` | `string[]` | Yes | List of unresolved items (empty if `"go"`) |
| `nfr_budgets` | `object` | No | Non-functional requirement budgets (latency, reliability, cost, scale, security, maintainability) |
| `data_governance` | `object` | No | PII handling, retention, auditability, regional constraints |
| `observability_requirements` | `object` | No | Required logs, metrics, traces, alert thresholds |
| `out_of_scope` | `string[]` | No | Explicitly stated exclusions from this build pass |

Also updates in `metadata`:
- `metadata.current_stage` = `0`
- `metadata.updated_at` = ISO 8601 timestamp
- `metadata.confidence_scores["0"]` = confidence object with 5 dimensions
- `metadata.stage_timestamps["0"]` = ISO 8601 timestamp

### Process

Stage 0 follows a strict 7-step canonical order. Each step must complete before the next begins.

#### Step 1: Context Intake

Capture the user's platform preferences. Ask these questions (present all at once, user answers together):

1. **New or existing app?** Greenfield (starting from scratch) or adding to an existing codebase?
2. **Platform target?** Web app, mobile app, or both?
3. **Target stack?** Do you have a preferred framework/database/auth provider, or should I recommend one?
4. **Repo source?** Starting a new repo, using a boilerplate, or working in an existing repo?
5. **Deployment target?** Where will this run? (Vercel, AWS, self-hosted, undecided)

For each answer, record the confidence level:
- `known` -- user explicitly stated it
- `inferred` -- derived from user's other answers
- `assumed` -- system default applied because user did not answer

**Low-input rule:** If the user provides no answers or says "I don't know," auto-fill ALL fields with defaults and log every default as an assumption. Do not block progress waiting for answers.

#### Step 2: Boilerplate/Profile Resolution

Based on the intake answers, select exactly one profile:

| Profile ID | Name | When to Select |
|------------|------|---------------|
| `supabase_web` | Supabase Web Starter | Greenfield + web + no strong stack preference |
| `flutter_mobile` | Flutter Mobile + Supabase | Mobile-only or mobile-first |
| `dual` | Dual Web + Mobile + Supabase | User explicitly wants both web and mobile |
| `no_boilerplate` | No Boilerplate | User has a specific non-standard stack |
| `raw_checklist` | Raw Checklist Only | Existing app or bring-your-own architecture |

**Default rule:** If profile is unknown after intake, assign `supabase_web` and mark the assumption. This is the lowest-risk, highest-coverage default.

#### Step 3: Martin Rules Preamble Injection

Load the technology-agnostic checklist (~192 rules, 22 categories, 43 banned patterns). For each rule, assign a resolution status based on the selected profile:

- `MATCH` -- Rule applies as-is to this profile. Carry unchanged.
- `REPLACE` -- Rule principle applies but implementation differs for this stack. Swap provider-specific implementation.
- `ENHANCE` -- Keep the rule AND add boilerplate-specific file pointers or extended implementation notes.
- `HANDLED` -- The boilerplate already implements this rule. Lock as "do not recreate." The coding agent must not rebuild this.
- `N/A` -- Not relevant to the selected profile (e.g., mobile-specific rules for a web-only app).

For each resolved rule, also assign:
- `priority`: `critical` / `important` / `nice`
- `enforcement`: `hard` (non-negotiable) / `soft` (recommendation)
- `evidence`: file path, config reference, or test artifact that satisfies the rule (if applicable)

**What to keep as hard constraints:**
- Build hygiene, structure, naming discipline, anti-pattern bans
- Security, auth boundaries, state/data handling consistency
- Deterministic component and testing standards

**What to make soft guidance:**
- "Only 5 features" becomes recommendation, not hard blocker
- Provider-specific assumptions become provider-agnostic mappings

#### Step 4: Structural Target Model (30 Categories)

Instantiate the full 30-category structural target map. The 22 categories from Martin's checklist plus the 10 gap areas from the industry standards supplement minus 2 overlaps = 30 unique structural categories.

For each category, mark coverage status:
- `covered_by_preamble` -- The selected boilerplate + resolved rules handle this category
- `provided_by_user` -- User explicitly addressed this in their intake answers
- `missing` -- Neither the preamble nor the user has addressed this; must be resolved in later stages

The output is a coverage matrix: 30 categories with a status for each.

#### Step 5: Mechanism Target Model (A-N Categories)

Instantiate the 14 mechanism categories (A through N) from the Mechanism Identification Framework:

| ID | Category |
|----|----------|
| A | Data Input |
| B | Data Storage |
| C | Data Processing |
| D | Data Output |
| E | Authentication |
| F | Authorization |
| G | Communication |
| H | Integration |
| I | Workflow |
| J | Search & Discovery |
| K | Collaboration |
| L | Monetization |
| M | Admin/Ops |
| N | Infrastructure |

For each category, mark:
- `covered_by_boilerplate` -- The selected boilerplate natively handles this mechanism
- `needs_user_input` -- This mechanism requires user decisions during idea capture and gap analysis
- `not_applicable` -- Definitively not relevant (rare at this stage; most will be `needs_user_input`)

Note: At Stage 0, the user has NOT described their app idea yet. Most mechanism categories will be `needs_user_input`. Categories like E (Authentication) and B (Data Storage) may be `covered_by_boilerplate` if the profile provides them.

#### Step 6: Question Budget + Clarification Strategy

Determine the question strategy for the entire pipeline based on the level of detail the user provided in Step 1:

| Input Level | Mode | Strategy |
|-------------|------|----------|
| Full detail (user answered all 5 questions with specifics) | `full_detail` | Ask only blocking questions in downstream stages. Max 2 rounds. |
| Partial detail (user answered 2-3 questions) | `minimal_input` | Fill gaps with defaults + assumption log. Ask up to 3 rounds. |
| Zero detail (user said "just build something" or skipped intake) | `zero_input` | Fill ALL fields with deterministic defaults. Ask 0 questions. Log everything as assumptions. |

**Defaults for zero-input users:**
- Assistant/tooling: Claude Code
- Data layer: Supabase
- Payments: Stripe (only if monetization signal is present in later stages)
- Auth: Boilerplate-native auth stack
- Hosting: Vercel

**Maximum question rounds before fallback inference:** 3 rounds total across all stages. After 3 rounds of unanswered questions, the pipeline auto-fills with defaults and proceeds.

#### Step 7: Stage Contract Emission

Emit the Stage 0 completion contract and Stage 1 entry criteria:

**Stage 0 Contract:**
- Goal: Platform context fully established
- Exit artifacts: `platform_profile`, `tech_stack`, `checklist_rule_ids`, `resolved_rules`, `structural_coverage`, `mechanism_target`, `assumptions`, `question_budget`
- Quality gates: All required fields populated, no `"TBD"` values, profile exists in supported profiles, no contradictions between fields
- Stop/go: `"go"` if all gates pass, `"conditional"` if score 70-89, `"stop"` if score < 70

**Stage 1 Input Pack:**
- Stage 1 does not directly consume Stage 0 output (Stage 1 captures raw user input)
- BUT Stage 2 (Gap Analysis) uses the platform profile for stack-aware gap questions
- Stage 4 (Mechanism Extraction) uses mechanism_target to tag mechanisms as OBVIOUS when boilerplate handles them
- The platform profile persists through the entire pipeline and appears in the final output

### Rules and Constraints

1. **Defaults must be logged as assumptions** with confidence level and reversal cost. No silent defaults.
2. **Never block progress** waiting for user answers. If the user does not respond, auto-fill and proceed.
3. **No idea-specific work.** Stage 0 must not ask about the user's app idea. That is Stage 1's job.
4. **No mechanism decomposition.** Stage 0 maps the mechanism category framework but does NOT analyze the user's idea against it. That is Stage 2's job.
5. **Hard constraints are non-negotiable:** build hygiene, structure, naming discipline, anti-pattern bans, security, auth boundaries, state/data handling.
6. **Soft guidance is advisory:** feature count limits, provider-specific assumptions. These become recommendations with logged justification.
7. **Critical additions that must be initialized** (even if mostly empty at Stage 0):
   - Non-functional requirement budgets (latency, reliability, cost, scale, security, maintainability)
   - Data governance/compliance lens (PII handling, retention, auditability, regional constraints)
   - Observability requirements (logs, metrics, traces, alert thresholds)
   - Out-of-scope guardrail (explicitly state what this build pass will NOT include)
   - Decision log (every inferred decision tagged with source and confidence)
   - Assumption burn-down (track assumptions to resolve in later stages)

---

## Files to Read Before Building

Read ALL of these files completely before writing any skill content:

1. **`docs/page-prds/prd-maker/consulting-conclusion-stage-0.md`** -- The primary source of truth for Stage 0. This document defines Stage 0's canonical order, required artifacts, contract system, defaults for low-input users, what to keep vs relax from Martin, critical additions, success criteria, and the pipeline crosswalk. There is no separate `stage-00-extraction.md` file; this document IS the extraction.

2. **`docs/page-prds/prd-maker/context-packet-schema.md`** -- The data schema. Find Stage 0's namespace (section 2.2 `stage_0`). Understand exactly which fields you read and write. Pay close attention to the `metadata` object (section 2.1) which Stage 0 must also update.

3. **`docs/page-prds/prd-maker/stage-contracts.md`** -- Find Stage 0's contract (the first stage contract in the document). Your skill must produce output that meets all "Done When" criteria and passes the confidence scoring. The 5 dimensions are: Completeness, Accuracy, Consistency, Specificity, Handoff Readiness.

4. **`docs/page-prds/prd-maker/martin-agnostic-checklist.md`** -- The full structural checklist (~192 rules, 22 categories, 43 banned patterns). Stage 0 loads this checklist and resolves each rule against the selected profile. Your skill must reference this document and produce a resolved rule pack.

5. **`docs/page-prds/prd-maker/nate-jones-skill-kit.md`** -- The skill-building methodology. Your SKILL.md must follow Nate's Prompt 2 output format and pass Nate's Prompt 3 agent-readiness criteria. The 4 criteria are: Trigger routing, Output completeness, Edge case handling, Composability.

6. **`docs/page-prds/prd-maker/extracted-skills/affaan-m/commands/prp-prd.md`** -- The Block 5-7 interrogation pattern for platform questioning. Study the phased question-gate-research flow (INITIATE -> FOUNDATION -> GROUNDING -> DEEP DIVE -> DECISIONS -> GENERATE). Stage 0 adapts this pattern: present platform questions all at once, wait for response, then proceed deterministically. The key insight is the GATE pattern (wait for user response before proceeding) and the fallback behavior (if no input provided, use defaults).

7. **`docs/page-prds/prd-maker/industry-standards-checklist.md`** -- The 71 supplementary rules across 10 gap areas that Martin's checklist does not cover. Stage 0 must be aware of these to produce a complete structural coverage matrix. Rule numbering starts at 200 to avoid collision with Martin's rules 1-192.

8. **`docs/page-prds/prd-maker/mechanism-identification-framework.md`** -- The A-N mechanism category definitions. Stage 0 instantiates this framework as a target model. Each category has sub-types and sub-questions that later stages use. Stage 0 only marks each category's status relative to the selected boilerplate.

9. **`docs/page-prds/prd-maker/app-archetype-library.md`** -- The 8 app archetypes with pre-mapped mechanism requirements. Stage 0 does not match an archetype (that is Stage 2's job), but awareness of the archetype library helps Stage 0 understand which mechanism categories boilerplates typically cover.

---

## Skill Building Instructions

You are building a Claude Code skill using the **Nate B. Jones Output-Extraction Method** (Prompt 2). This means you do NOT write a vague process description -- you reverse-engineer what GREAT output looks like and encode that into the skill.

### The Build Process

**Step 1: Understand the output.** Read the consulting conclusion document and the stage contract. Understand what a PERFECT Stage 0 output looks like. What fields are populated? What quality level? What format? A perfect output has: a fully resolved platform profile with no TBD values, every Martin rule tagged with a resolution status, a complete 30-category structural coverage matrix, a 14-category mechanism target model, all assumptions logged with confidence and reversal cost, a question budget set, and a stage contract emitted with pass/fail gates.

**Step 2: Extract the methodology.** From the consulting conclusion and reference skills, identify:
- **Structural patterns:** The 7-step canonical order (Context Intake -> Profile Resolution -> Rules Injection -> Structural Model -> Mechanism Model -> Question Budget -> Contract Emission). Each step has a defined input, process, and output.
- **Decision patterns:** Profile selection is a lookup table, not a creative decision. Rule resolution is systematic (MATCH/REPLACE/ENHANCE/HANDLED/N/A). Question budget is determined by input completeness level.
- **Quality signals:** No TBD values. No contradictions between fields. Every assumption logged. Boilerplate ID exists in the supported set. Mechanism coverage includes at minimum A, B, and E.
- **Edge cases:** User requests unsupported stack. User provides contradictory preferences. User provides zero input. User requests existing app analysis (future feature).

**Step 3: Build the SKILL.md.** Write the complete skill file following the format in the "Skill Format Requirements" section below.

**Step 4: Self-audit against the 4 Agent-Readiness Criteria** (Nate's Prompt 3):

1. **Trigger Description as Routing Table** -- Does your description contain specific trigger phrases ("technical foundation", "platform setup", "stack selection")? Is it specific enough to avoid false matches with Stage 2 (which also touches mechanism categories)? Does it specify what the skill PRODUCES (platform profile, resolved checklist, coverage matrix)?

2. **Output Format Completeness** -- Is every output field specified with name, type, and description? Could Stage 1 (or more importantly Stage 2) parse this output programmatically? Are the enum values for `boilerplate_id`, `resolution`, `priority`, `enforcement`, `status`, and `confidence` all explicitly listed?

3. **Explicit Edge Case Handling** -- What happens when the user requests an unsupported stack? When all intake questions go unanswered? When the user says "I want Firebase" but the profile is Supabase-based? Each edge case must have a defined, machine-readable response.

4. **Composability** -- Could Stage 2 consume Stage 0's output cleanly? Does the output contain ONLY structured data (no conversational preamble)? Is the `platform_profile` object self-contained enough that any downstream stage can reference it for stack-specific decisions?

If ANY criterion fails, revise the skill before finalizing.

---

## Skill Format Requirements

### SKILL.md Structure

```markdown
---
name: stage-0-technical-foundation
description: {{SINGLE LINE DESCRIPTION -- this is a YAML field, multi-line SILENTLY FAILS}}
---

## Purpose

{{1-2 sentences}}

## When to Use

{{Trigger conditions -- what input or request activates this skill}}

## Input Format

{{Exact JSON structure this skill expects from the context packet}}

## Process

### Step 1: {{Name}}
{{Detailed instructions with decision criteria}}

### Step 2: {{Name}}
{{...}}

[... as many steps as needed ...]

## Output Format

{{Exact JSON structure this skill writes to the context packet -- field names, types, validation rules}}

## Edge Cases

### Missing Input
{{What to do when required fields are empty or missing}}

### Ambiguous Input
{{What to do when input can be interpreted multiple ways}}

### Scope Overflow
{{What to do when the stage discovers work that belongs to a different stage}}

## Confidence Scoring

{{The 5 scoring dimensions from the stage contract, with self-scoring instructions}}

## Escape Hatch

{{When to trigger, what to save, how to signal NEEDS_HUMAN}}

## Example

{{One realistic example showing input -> process -> output for this stage}}
```

### Critical Format Rules

1. **YAML frontmatter `description` MUST be a single line.** Multi-line descriptions silently fail in Claude Code. Keep it under 120 characters.

2. **Total SKILL.md body MUST be under 500 lines / 5,000 tokens.** This is a hard limit from Claude Code's context window management. After compaction, skills are truncated to 5K tokens.

3. **Large reference material goes in a `references/` subfolder**, NOT in the SKILL.md body. Create files like:
   - `references/boilerplate-profiles.md` -- The 5 supported boilerplate profiles with their capabilities and default stacks
   - `references/rule-resolution-guide.md` -- How to map each Martin checklist category to a resolution status for each profile
   - `references/structural-categories.md` -- The 30 structural categories for the coverage matrix
   - `references/mechanism-categories.md` -- The 14 mechanism categories (A-N) with boilerplate coverage defaults
   - `references/default-assumptions.md` -- The complete set of defaults for zero-input users with reversal costs
   - `references/example-output.md` -- Extended example if the inline example is too large

4. **Output must be structured data (JSON or strict Markdown).** No free-form prose in the output section. Every field must have a name, type, and description.

5. **No conversational text in output.** The skill's output is data for the next stage, not a message for a human. No "Here is what I found:" or "I analyzed the following:".

---

## Context Packet Integration

### Reading Input

Stage 0 is the first stage. It does NOT read from any prior stage. It reads only from `metadata` (which is initialized before Stage 0 runs):

```python
# Pseudocode -- Stage 0 reads initial metadata only
metadata = context_packet["metadata"]
app_type = metadata["app_type"]  # "greenfield" or "existing"
```

The user's platform answers come from the skill invocation context (the user's chat message or form submission), NOT from a prior stage.

### Writing Output

Stage 0 writes to its own namespace:

```python
context_packet["stage_0"] = {
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
    "checklist_rule_ids": ["stack-1", "stack-2", "stack-3", ...],
    "command_allowlist": ["npm", "npx", "git", "node", "curl"],
    "resolved_rules": [...],
    "structural_coverage": {...},
    "mechanism_target": {...},
    "assumptions": [...],
    "question_budget": {...},
    "stage_contract": {...},
    "nfr_budgets": {...},
    "data_governance": {...},
    "observability_requirements": {...},
    "out_of_scope": [...]
}

context_packet["metadata"]["current_stage"] = 0
context_packet["metadata"]["confidence_scores"]["0"] = {
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
context_packet["metadata"]["stage_timestamps"]["0"] = "2026-04-02T12:00:00Z"
```

### Validation Before Writing

Before writing output, the skill MUST:
1. Verify all required output fields are populated (no `null`, no `"TBD"`)
2. Verify `boilerplate_id` is one of the 5 supported values
3. Verify `tech_stack` fields are internally consistent (no contradictions like Supabase profile with Firebase auth)
4. Verify every assumption has all 4 metadata fields (field, value, confidence, reversal_cost)
5. Run the confidence scoring (see below)
6. If score < 70, trigger escape hatch instead of writing
7. If score 70-89, write but flag in metadata with `gate_result: "flag"`
8. If score >= 90, write normally with `gate_result: "pass"`

---

## Token Budget

Your skill will run within a Claude Code session with approximately 400,000-450,000 total tokens available (after accounting for system prompts, tools, and the context packet itself).

Budget allocation:
- SKILL.md: ~5,000 tokens (hard limit)
- References (combined): ~20,000 tokens max
- Context packet input: ~1,000-2,000 tokens (Stage 0 receives a nearly empty packet -- only metadata exists)
- Working space for the agent: remaining tokens

Stage 0 has the lightest context packet input of any stage because no prior stages have written data. Use this budget advantage to produce thorough reference files if needed.

Keep your skill lean. Do not embed the full Martin checklist in the SKILL.md. Reference it by file path and describe the resolution logic. The agent running the skill will read the checklist file separately.

---

## Escape Hatch Pattern

Every stage uses this standard escape hatch. Include it in your SKILL.md:

```
When to trigger:
- User requests a stack that is not in the supported profiles AND refuses the closest alternative
- Confidence score is below 70 after one retry
- The user's platform preferences contradict each other in a way that cannot be resolved
  (e.g., "I want a mobile-only app" + "I want server-side rendering")
- metadata.app_type is "existing" and existing_app_analysis is required but not yet supported

What to save:
- Current context_packet (with whatever partial output exists in stage_0)
- Stage number (0) and step number where the halt occurred
- What was attempted and what failed
- Suggested questions for the human (e.g., "You said you want X and Y, but those conflict. Which do you prefer?")

How to signal:
- Set metadata.status = "needs_human"
- Add an entry to metadata.escape_hatches array:
  {
    "stage": 0,
    "step": <step_number>,
    "reason": "<specific reason>",
    "attempted": "<what the skill tried>",
    "suggested_actions": ["<action 1>", "<action 2>"]
  }
- Save context_packet snapshot to disk
- Output a structured NEEDS_HUMAN message with the specific problem and suggested actions
```

---

## Confidence Gate Pattern

Include this self-scoring process in your SKILL.md:

```
After producing output, score each dimension 0-20:

1. Completeness (0-20): Are ALL required output fields populated with real data (not placeholders)?
   - 0-5: 3+ fields in platform_profile are empty or "TBD"
   - 6-10: 1-2 fields missing; boilerplate_id present but mechanism coverage incomplete
   - 11-15: All fields populated but structural_coverage or mechanism_target may have gaps
   - 16-20: All fields populated; structural_coverage covers every category; mechanism_target covers A-N

2. Accuracy (0-20): Does the output correctly reflect the input? No invented information?
   - 0-5: Selected stack does not exist or framework/database are incompatible
   - 6-10: Stack exists but version or configuration details are wrong
   - 11-15: Stack is valid and compatible; minor configuration details not specified
   - 16-20: Stack is valid, compatible, version-correct, configuration matches boilerplate exactly

3. Consistency (0-20): Does the output align internally? No contradictions between fields?
   - 0-5: platform_profile contradicts itself (e.g., framework says Next.js but auth says Firebase)
   - 6-10: Minor mismatches that could be resolved with one clarification
   - 11-15: Fields are internally consistent; no contradictions
   - 16-20: All fields align perfectly -- framework, database, auth, hosting form a coherent stack

4. Specificity (0-20): Is every field precise enough for downstream stages to parse programmatically?
   - 0-5: Fields contain vague values like "a database" or "some framework"
   - 6-10: Fields name technologies but lack version or configuration detail
   - 11-15: Fields specify exact technologies with versions; mechanism categories use codes A-N
   - 16-20: Fields specify exact technology + version + configuration; mechanism coverage includes capability notes

5. Handoff Readiness (0-20): Could Stage 1 start immediately from this output?
   - 0-5: Stage 1 would need to ask "what stack are we building on?"
   - 6-10: Stage 1 could proceed but Stage 2 would need to guess at database patterns
   - 11-15: Stage 1 can proceed; platform context is clear for Stage 2
   - 16-20: All downstream stages (1-10) can reference platform_profile without ambiguity

Total = sum of all 5 dimensions (/100)

>= 90: PASS -- proceed to Stage 1 automatically
70-89: WARN -- flag low dimensions, proceed with warning in metadata
< 70:  FAIL -- trigger escape hatch, do NOT pass output forward
```

---

## Output Location

Save the completed skill to:

```
docs/page-prds/prd-maker/skills/stage-00-technical-foundation/SKILL.md
```

If you need reference files, save them to:

```
docs/page-prds/prd-maker/skills/stage-00-technical-foundation/references/
```

---

## Agent-Readiness Checklist (Must Pass ALL)

Before finalizing your SKILL.md, verify:

- [ ] **Trigger routing:** The `description` field in YAML frontmatter contains specific trigger phrases ("technical foundation", "platform profile", "stack selection") and specifies what the skill produces (platform profile, resolved checklist, coverage matrix, stage contract)
- [ ] **Output completeness:** Every output field has a name, type, and description. A downstream agent could parse the output with zero guessing. All enum values are explicitly listed.
- [ ] **Edge cases explicit:** Missing input (zero-input user), ambiguous input (contradictory stack preferences), unsupported stack request, and scope overflow (user tries to describe their app idea during Stage 0) all have defined behaviors with machine-readable responses
- [ ] **Composability:** The output contains ONLY structured data. No conversational text, no preamble, no "Here is what I found." Stage 2 can consume the output as-is for stack-aware gap analysis.
- [ ] **Under 500 lines:** The SKILL.md body (excluding frontmatter) is under 500 lines
- [ ] **Single-line description:** The YAML `description` field is exactly one line, under 120 characters
- [ ] **Confidence gate included:** The self-scoring process is documented with all 5 dimensions and the 0-20 rubric per dimension
- [ ] **Escape hatch included:** Trigger conditions (unsupported stack, contradictory preferences, score < 70), save protocol, and signal method are documented
- [ ] **Example included:** At least one realistic input/output example is present showing both a full-input and a zero-input scenario
- [ ] **Context packet fields match schema:** Every field read/written matches `context-packet-schema.md` section 2.2 (`stage_0`) and section 2.1 (`metadata`)
- [ ] **Stage contract criteria achievable:** Following the skill's 7-step process will produce output that meets all 6 "Done When" criteria from `stage-contracts.md`
- [ ] **Reference files bounded:** All reference files combined are under 20K tokens

---

## Success Criteria

- [ ] SKILL.md exists at `docs/page-prds/prd-maker/skills/stage-00-technical-foundation/SKILL.md`
- [ ] YAML frontmatter has `name: stage-0-technical-foundation` and a single-line `description`
- [ ] SKILL.md body is under 500 lines
- [ ] All sections present: Purpose, When to Use, Input Format, Process (7 steps), Output Format, Edge Cases, Confidence Scoring, Escape Hatch, Example
- [ ] Passes all 4 agent-readiness criteria (trigger routing, output completeness, edge cases, composability)
- [ ] Context packet fields match `context-packet-schema.md` section 2.2 (`stage_0`)
- [ ] All 6 "Done When" criteria from `stage-contracts.md` Stage 0 are achievable by following the skill's process
- [ ] The 5 boilerplate profiles are defined with their default stacks and capabilities
- [ ] The Martin checklist resolution logic (MATCH/REPLACE/ENHANCE/HANDLED/N/A) is documented with clear criteria per resolution type
- [ ] The 30-category structural coverage matrix is defined
- [ ] The 14 mechanism categories (A-N) are mapped with boilerplate coverage defaults
- [ ] Default assumptions for zero-input users are documented with confidence and reversal cost
- [ ] Question budget modes (full_detail, minimal_input, zero_input) are defined with clear selection criteria
- [ ] Reference files (if any) are in the `references/` subfolder and total under 20K tokens
