# Context Packet Schema

> **Version:** 1.0.0
> **Created by:** Phase 1D handoff
> **Purpose:** Defines the JSON data object that flows through all 10 stages of the PRD Maker pipeline

---

## 1. Overview

The **context packet** is a single JSON object that serves as the pipeline's memory. Every stage reads fields written by previous stages, adds its own data under a dedicated namespace, and passes the complete packet forward.

Think of it as a card on an assembly line. Each station reads the card, stamps its work onto it, and sends it to the next station. No station is allowed to erase or overwrite another station's stamps.

### Design Principles

| # | Principle | Rule |
|---|-----------|------|
| 1 | **Additive Only** | Stages only ADD data. No stage deletes or overwrites data from a previous stage. If modification is needed, write a new field (e.g., `mechanisms_raw` vs `mechanisms_classified`). |
| 2 | **Namespaced by Stage** | Each stage writes exclusively to its own `stage_N` object. Cross-stage collisions are impossible by design. |
| 3 | **Self-Describing** | The packet carries its own metadata: pipeline version, current stage, timestamps, confidence scores, and status. |
| 4 | **Serializable** | Everything is JSON-serializable. No functions, class instances, or circular references. Only objects, arrays, strings, numbers, booleans, and null. |
| 5 | **Recoverable** | The snapshot saved after Stage N-1 contains everything needed to restart Stage N from scratch. |

### Top-Level Structure

```json
{
  "metadata": { ... },
  "stage_0": { ... },
  "stage_1": { ... },
  "stage_2": { ... },
  "stage_3": { ... },
  "stage_4": { ... },
  "stage_5": { ... },
  "stage_6": { ... },
  "stage_7": { ... },
  "stage_8": { ... },
  "stage_9": { ... },
  "stage_10": { ... }
}
```

Each `stage_N` key is `null` until that stage runs. Once a stage completes, its namespace is populated and never modified again.

---

## 2. Full JSON Schema

### 2.1 `metadata`

Created before Stage 0 runs. Updated by every stage.

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `pipeline_version` | `string` | Yes | Semver of the pipeline that created this packet | Must match `^\d+\.\d+\.\d+$` |
| `created_at` | `string` | Yes | ISO 8601 timestamp when the pipeline run started | ISO 8601 format |
| `updated_at` | `string` | Yes | ISO 8601 timestamp of last modification | ISO 8601 format |
| `current_stage` | `integer` | Yes | Stage currently running or last completed (0-10) | `0 <= value <= 10` |
| `status` | `string` | Yes | Pipeline status | Enum: `"in_progress"`, `"completed"`, `"failed"`, `"needs_human"` |
| `app_type` | `string` | Yes | Application type | Enum: `"greenfield"`, `"existing"` |
| `archetype_matches` | `string[]` | No | Matched app archetypes from Stage 2 | Set after Stage 2 |
| `confidence_scores` | `object` | Yes | Keyed by stage number (as string). Each value is a confidence object. | See Confidence Object below |
| `stage_timestamps` | `object` | Yes | Keyed by stage number (as string). Each value is an ISO 8601 completion timestamp. | Keys: `"0"` through `"10"` |
| `escape_hatches` | `array` | Yes | Array of escape hatch records. Empty if no failures. | See Section 5 |
| `scope_contract_hash` | `string` | No | SHA-256 hash of the Stage 2 scope contract, used by scope creep detector | Set after Stage 2 |

**Confidence Object:**

```json
{
  "score": 85,
  "dimensions": {
    "completeness": 90,
    "clarity": 80,
    "consistency": 85
  },
  "gate_result": "pass"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `score` | `number` | Yes | Overall confidence 0-100 |
| `dimensions` | `object` | Yes | Breakdown scores by dimension (keys vary per stage) |
| `gate_result` | `string` | Yes | Enum: `"pass"` (>=90), `"flag"` (70-89), `"fail"` (<70) |

---

### 2.2 `stage_0` — Technical Foundation

Establishes platform context before any user input is processed.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `platform_profile` | `object` | Yes | Selected platform/boilerplate configuration |
| `platform_profile.boilerplate_id` | `string` | Yes | Identifier for selected boilerplate. One of: `"supabase_web"`, `"flutter_mobile"`, `"dual"`, `"no_boilerplate"`, `"raw_checklist"` |
| `platform_profile.boilerplate_name` | `string` | Yes | Human-readable name |
| `platform_profile.description` | `string` | Yes | Brief description of what this boilerplate provides |
| `tech_stack` | `object` | Yes | Technology decisions |
| `tech_stack.framework` | `string` | Yes | Primary framework (e.g., `"Next.js"`, `"Flutter"`, `"none"`) |
| `tech_stack.database` | `string` | Yes | Database choice (e.g., `"Supabase/Postgres"`, `"Firebase"`, `"none"`) |
| `tech_stack.auth_provider` | `string` | Yes | Auth provider (e.g., `"Supabase Auth"`, `"Firebase Auth"`, `"custom"`, `"none"`) |
| `tech_stack.hosting` | `string` | Yes | Hosting target (e.g., `"Vercel"`, `"AWS"`, `"self-hosted"`, `"undecided"`) |
| `tech_stack.additional` | `object` | No | Any additional stack decisions (key-value pairs) |
| `checklist_rule_ids` | `string[]` | Yes | List of agnostic checklist rule IDs that apply to this stack (references, not full content) |
| `command_allowlist` | `string[]` | No | Project-specific allowed bash commands |
| `existing_app_analysis` | `object` | No | **FUTURE:** Codebase analysis for `app_type: "existing"`. See Section 6. |

---

### 2.3 `stage_1` — Idea Capture

Raw, unstructured user brain dump. No processing, no cleanup.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `raw_input` | `string` | Yes | The complete, unedited user brain dump |
| `input_format` | `string` | Yes | How the input was provided. Enum: `"typed"`, `"voice_transcript"`, `"pasted_notes"`, `"mixed"` |
| `captured_at` | `string` | Yes | ISO 8601 timestamp of capture |
| `word_count` | `integer` | Yes | Word count of raw_input |
| `char_count` | `integer` | Yes | Character count of raw_input |
| `explicit_corrections` | `array` | No | Contradictions the user stated and then corrected |
| `explicit_corrections[].original` | `string` | Yes | What the user originally said |
| `explicit_corrections[].correction` | `string` | Yes | What they corrected it to |
| `explicit_corrections[].context` | `string` | No | Surrounding context |

---

### 2.4 `stage_2` — Gap Analysis

Compares raw input against A-N mechanism categories and the 30-category master checklist to find gaps and fill them.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `archetype_matches` | `array` | Yes | Matched app archetypes with confidence |
| `archetype_matches[].archetype` | `string` | Yes | Archetype name (e.g., `"dashboard"`, `"marketplace"`, `"chat"`, `"wizard"`, `"tool"`) |
| `archetype_matches[].confidence` | `number` | Yes | Match confidence 0-100 |
| `archetype_matches[].rationale` | `string` | Yes | Why this archetype was matched |
| `mechanisms_identified` | `array` | Yes | A-N mechanism categories found in the raw input |
| `mechanisms_identified[].category_id` | `string` | Yes | Category letter A-N |
| `mechanisms_identified[].category_name` | `string` | Yes | Human-readable name (e.g., `"Data Input"`, `"Authentication"`) |
| `mechanisms_identified[].sub_types` | `string[]` | Yes | Which sub-types within the category were mentioned |
| `mechanisms_identified[].evidence` | `string` | Yes | Quote or paraphrase from raw input that triggered this match |
| `mechanisms_gaps` | `array` | Yes | A-N categories NOT mentioned in raw input |
| `mechanisms_gaps[].category_id` | `string` | Yes | Category letter A-N |
| `mechanisms_gaps[].category_name` | `string` | Yes | Human-readable name |
| `mechanisms_gaps[].resolution` | `string` | Yes | Enum: `"asked"`, `"not_needed"`, `"developers_choice"` |
| `gap_questions` | `array` | Yes | Questions asked to fill gaps |
| `gap_questions[].id` | `string` | Yes | Unique question identifier |
| `gap_questions[].category_id` | `string` | Yes | Which A-N category this question addresses |
| `gap_questions[].question_text` | `string` | Yes | The question asked |
| `gap_questions[].source` | `string` | Yes | Enum: `"mechanism_framework"`, `"master_checklist"`, `"archetype_specific"` |
| `gap_answers` | `array` | Yes | User's answers to gap questions |
| `gap_answers[].question_id` | `string` | Yes | References `gap_questions[].id` |
| `gap_answers[].answer_text` | `string` | Yes | User's answer (or `"developers_choice"` if user said "I don't know") |
| `gap_answers[].is_default` | `boolean` | Yes | True if the system used a Developer's Choice default |
| `combined_raw` | `string` | Yes | Stage 1 raw_input + all gap answers merged into one text blob. Complete but still unstructured. |
| `completeness_score` | `number` | Yes | 0-100 score for how complete the information set is |
| `checklist_coverage` | `object` | Yes | Coverage of the 30-category master checklist |
| `checklist_coverage.covered` | `string[]` | Yes | Checklist category names that are covered |
| `checklist_coverage.not_applicable` | `string[]` | Yes | Categories explicitly marked N/A |
| `checklist_coverage.deferred` | `string[]` | Yes | Categories deferred to Developer's Choice |
| `scope_contract` | `string` | Yes | A summary of what IS and IS NOT in scope, used by scope creep detector in later stages |

---

### 2.5 `stage_3` — Agent OS Structuring

Transforms unstructured raw material into a structured Concept Document. Contains "what" and "why" but NOT "how."

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `concept_and_context` | `object` | Yes | Product identity |
| `concept_and_context.product_name` | `string` | Yes | Chosen product name |
| `concept_and_context.one_line_description` | `string` | Yes | Single-sentence product description |
| `concept_and_context.product_identity` | `string` | Yes | Detailed product identity paragraph |
| `concept_and_context.core_value_proposition` | `string` | Yes | What makes this product valuable |
| `target_user_and_market` | `object` | Yes | Who it is for |
| `target_user_and_market.personas` | `array` | Yes | Target user personas |
| `target_user_and_market.personas[].name` | `string` | Yes | Persona label (e.g., `"Busy Professional"`) |
| `target_user_and_market.personas[].description` | `string` | Yes | Who this person is |
| `target_user_and_market.personas[].pain_points` | `string[]` | Yes | What problems they face |
| `target_user_and_market.personas[].goals` | `string[]` | Yes | What they want to achieve |
| `target_user_and_market.market_context` | `string` | Yes | Market landscape description |
| `target_user_and_market.competitive_landscape` | `array` | No | Known competitors |
| `target_user_and_market.competitive_landscape[].name` | `string` | Yes | Competitor name |
| `target_user_and_market.competitive_landscape[].differentiator` | `string` | Yes | How this product differs |
| `feasibility_assessment` | `object` | Yes | Market viability analysis |
| `feasibility_assessment.viability_summary` | `string` | Yes | Overall feasibility assessment |
| `feasibility_assessment.risks` | `array` | No | Identified risks |
| `feasibility_assessment.risks[].risk` | `string` | Yes | Risk description |
| `feasibility_assessment.risks[].severity` | `string` | Yes | Enum: `"low"`, `"medium"`, `"high"` |
| `feasibility_assessment.risks[].mitigation` | `string` | Yes | How to mitigate |
| `problem_statement` | `string` | Yes | Clear statement of the problem being solved |
| `ambiguity_resolutions` | `array` | No | Ambiguities found in raw input and how they were resolved |
| `ambiguity_resolutions[].ambiguity` | `string` | Yes | What was ambiguous |
| `ambiguity_resolutions[].resolution` | `string` | Yes | How it was resolved |
| `ambiguity_resolutions[].source` | `string` | Yes | What information the resolution was based on |
| `drift_anchor` | `string` | Yes | Canonical product description used as reference point to detect scope creep in all later stages |

---

### 2.6 `stage_4` — Mechanism Extraction

Decomposes the structured concept into discrete, actionable mechanisms.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mechanisms` | `array` | Yes | List of extracted mechanisms |
| `mechanisms[].id` | `string` | Yes | Unique mechanism identifier (e.g., `"mech_001"`) |
| `mechanisms[].name` | `string` | Yes | Descriptive label (e.g., `"Auth System"`, `"Payment Flow"`) |
| `mechanisms[].description` | `string` | Yes | What this mechanism does |
| `mechanisms[].category_ids` | `string[]` | Yes | Maps to A-N categories (e.g., `["E", "F"]`) |
| `mechanisms[].classification` | `string` | Yes | Enum: `"OBVIOUS"`, `"NEEDS_EVALUATION"` |
| `mechanisms[].is_core_mechanism` | `boolean` | Yes | True if this is the one thing that makes the app special |
| `mechanisms[].chosen_approach` | `object` | Yes | The selected implementation approach |
| `mechanisms[].chosen_approach.name` | `string` | Yes | Approach name |
| `mechanisms[].chosen_approach.description` | `string` | Yes | How it works |
| `mechanisms[].chosen_approach.rationale` | `string` | Yes | Why it was chosen |
| `mechanisms[].alternate_approach` | `object` | No | Second approach if within 15% performance parity |
| `mechanisms[].alternate_approach.name` | `string` | Yes | Approach name |
| `mechanisms[].alternate_approach.description` | `string` | Yes | How it works |
| `mechanisms[].alternate_approach.score_delta` | `number` | Yes | Score difference from chosen (0-15) |
| `mechanisms[].evaluation` | `object` | No | Present only if `classification` is `"NEEDS_EVALUATION"` |
| `mechanisms[].evaluation.approaches` | `array` | Yes | Competing approaches evaluated |
| `mechanisms[].evaluation.approaches[].name` | `string` | Yes | Approach name |
| `mechanisms[].evaluation.approaches[].score` | `number` | Yes | Evaluation score 0-100 |
| `mechanisms[].evaluation.approaches[].pros` | `string[]` | Yes | Advantages |
| `mechanisms[].evaluation.approaches[].cons` | `string[]` | Yes | Disadvantages |
| `mechanisms[].evaluation.criteria` | `string[]` | Yes | The 10-step criteria used for evaluation |
| `mechanism_dependencies` | `array` | Yes | Dependencies between mechanisms |
| `mechanism_dependencies[].from_id` | `string` | Yes | Mechanism ID that depends on another |
| `mechanism_dependencies[].to_id` | `string` | Yes | Mechanism ID that is depended upon |
| `mechanism_dependencies[].relationship` | `string` | Yes | Nature of dependency (e.g., `"requires"`, `"uses_output_of"`, `"shares_data_with"`) |
| `mechanism_count` | `integer` | Yes | Total number of mechanisms extracted |
| `dual_design_count` | `integer` | Yes | Number of mechanisms with alternate approaches (15% rule) |

---

### 2.7 `stage_5` — 7-Question Scaffolding

Applies the Wall/Door/Room framework to every mechanism.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mechanism_blueprints` | `array` | Yes | One blueprint per mechanism (plus alternate if 15% rule applied) |
| `mechanism_blueprints[].mechanism_id` | `string` | Yes | References `stage_4.mechanisms[].id` |
| `mechanism_blueprints[].approach` | `string` | Yes | Enum: `"primary"`, `"alternate"` — which approach this blueprint covers |
| `mechanism_blueprints[].phases` | `array` | Yes | Grouped steps within this mechanism |
| `mechanism_blueprints[].phases[].phase_label` | `string` | Yes | Phase name within the mechanism |
| `mechanism_blueprints[].phases[].entry_condition` | `string` | Yes | What must be true to start this phase |
| `mechanism_blueprints[].phases[].exit_condition` | `string` | Yes | What must be true to proceed |
| `mechanism_blueprints[].phases[].validation_rules` | `string[]` | Yes | How to verify this phase was done correctly |
| `mechanism_blueprints[].phases[].steps` | `array` | Yes | Individual steps in this phase |
| `mechanism_blueprints[].phases[].steps[].id` | `string` | Yes | Unique step identifier |
| `mechanism_blueprints[].phases[].steps[].name` | `string` | Yes | What happens here (Question 1) |
| `mechanism_blueprints[].phases[].steps[].classification` | `string` | Yes | Enum: `"WALL"`, `"DOOR"`, `"ROOM"` (Question 2) |
| `mechanism_blueprints[].phases[].steps[].preconditions` | `string[]` | Yes | What must be true before this step starts (Question 3) |
| `mechanism_blueprints[].phases[].steps[].outcomes` | `array` | Yes | All possible outcomes (Question 4) |
| `mechanism_blueprints[].phases[].steps[].outcomes[].outcome` | `string` | Yes | Outcome description |
| `mechanism_blueprints[].phases[].steps[].outcomes[].next_step` | `string` | Yes | Where to go next (step ID or `"end"`) (Question 5) |
| `mechanism_blueprints[].phases[].steps[].verification` | `string` | Yes | How to verify this step was done correctly (Question 6) |
| `mechanism_blueprints[].phases[].steps[].skip_condition` | `string \| null` | Yes | Condition under which this step can be skipped, or null if not skippable (Question 7) |
| `build_rules_applied` | `string[]` | Yes | List of Martin's build rule IDs that shaped the scaffolding |

---

### 2.8 `stage_6` — Layout + Mockups + Style

Three sub-stages: arrangement selection, page mockups, and style application.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sub_6a` | `object` | Yes | Arrangement selection |
| `sub_6a.app_type_classification` | `string` | Yes | App type for wireframe lookup (e.g., `"dashboard"`, `"e-commerce"`, `"social"`) |
| `sub_6a.arrangement_options` | `array` | Yes | 2-3 arrangement options presented to user |
| `sub_6a.arrangement_options[].id` | `string` | Yes | Option identifier |
| `sub_6a.arrangement_options[].name` | `string` | Yes | Pattern name (e.g., `"Sidebar + Top Nav + Content Grid"`) |
| `sub_6a.arrangement_options[].description` | `string` | Yes | What it looks like |
| `sub_6a.selected_arrangement_id` | `string` | Yes | Which arrangement the user picked |
| `sub_6a.user_adjustments` | `string \| null` | No | Any adjustments the user requested |
| `sub_6b` | `object` | Yes | Page mockups |
| `sub_6b.pages` | `array` | Yes | Per-page mockup data |
| `sub_6b.pages[].page_name` | `string` | Yes | Page name (e.g., `"Dashboard"`, `"Settings"`, `"Task Detail"`) |
| `sub_6b.pages[].layout_pattern` | `string` | Yes | Layout pattern applied to this page |
| `sub_6b.pages[].components` | `array` | Yes | Components placed on this page |
| `sub_6b.pages[].components[].component_name` | `string` | Yes | Component name |
| `sub_6b.pages[].components[].placement` | `string` | Yes | Where on the page (e.g., `"header"`, `"sidebar"`, `"main-content"`, `"footer"`) |
| `sub_6b.pages[].components[].mechanism_ids` | `string[]` | Yes | Which mechanisms this component connects to |
| `sub_6b.pages[].user_approved` | `boolean` | Yes | Whether user approved this page layout |
| `sub_6c` | `object` | Yes | Style selection |
| `sub_6c.style_options_presented` | `array` | Yes | 3 curated style options shown to user |
| `sub_6c.style_options_presented[].id` | `string` | Yes | Style identifier |
| `sub_6c.style_options_presented[].name` | `string` | Yes | Style name |
| `sub_6c.style_options_presented[].vibe` | `string` | Yes | Short vibe description |
| `sub_6c.selected_style_id` | `string` | Yes | Which style the user picked (or `"developers_choice"`) |
| `sub_6c.design_tokens` | `object` | Yes | Complete design token set |
| `sub_6c.design_tokens.colors` | `object` | Yes | Color palette (key-value, e.g., `{"primary": "#3B82F6", ...}`) |
| `sub_6c.design_tokens.typography` | `object` | Yes | Typography hierarchy (font families, sizes, weights) |
| `sub_6c.design_tokens.spacing` | `object` | No | Spacing scale |
| `sub_6c.design_tokens.border_radius` | `object` | No | Border radius tokens |
| `sub_6c.design_tokens.shadows` | `object` | No | Shadow tokens |
| `sub_6c.tailwind_config_overrides` | `object` | No | Tailwind configuration overrides for the selected style |
| `sub_6c.audience_scores` | `object` | No | Style fit scores |
| `sub_6c.audience_scores.audience_fit` | `number` | No | 0-100 |
| `sub_6c.audience_scores.vibe_match` | `number` | No | 0-100 |
| `sub_6c.audience_scores.age_range_fit` | `number` | No | 0-100 |

---

### 2.9 `stage_7` — Phase Sequencing

Splits the complete spec into token-budgeted build phases with file sandboxes.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `token_budget` | `object` | Yes | Token budget calculation |
| `token_budget.total_spec_tokens` | `integer` | Yes | Estimated total tokens for the entire spec |
| `token_budget.budget_per_phase_content` | `integer` | Yes | Max content tokens per phase (~325,000) |
| `token_budget.overhead_per_phase` | `integer` | Yes | Fixed overhead tokens per phase (~25,000) |
| `token_budget.total_budget` | `integer` | Yes | Total available budget (~500,000) |
| `token_budget.phases_needed` | `integer` | Yes | Calculated number of phases |
| `phases` | `array` | Yes | Ordered list of build phases |
| `phases[].phase_number` | `integer` | Yes | Phase number (1-based) |
| `phases[].name` | `string` | Yes | Phase name (e.g., `"Core Auth & Data Layer"`) |
| `phases[].mechanism_ids` | `string[]` | Yes | Which mechanisms are built in this phase |
| `phases[].estimated_tokens` | `integer` | Yes | Estimated token count for this phase's content |
| `phases[].build_order` | `array` | Yes | Ordered list of file operations |
| `phases[].build_order[].file_path` | `string` | Yes | File to create or modify |
| `phases[].build_order[].operation` | `string` | Yes | Enum: `"create"`, `"modify"` |
| `phases[].build_order[].rationale` | `string` | Yes | Why this file at this position in the order |
| `phases[].files_allowed` | `string[]` | Yes | Files this phase can create or modify |
| `phases[].files_read_only` | `string[]` | Yes | Files this phase can reference but NOT change |
| `phases[].files_forbidden` | `string[]` | Yes | All other files — touching these is a violation |
| `phases[].depends_on` | `integer[]` | Yes | Phase numbers that must complete before this one |
| `phases[].do_not_change` | `string[]` | Yes | Files with DO NOT CHANGE protection in this phase |
| `mandatory_build_order` | `array` | Yes | Global constraints on phase ordering |
| `mandatory_build_order[].rule` | `string` | Yes | Description of the constraint |
| `mandatory_build_order[].phases_affected` | `integer[]` | Yes | Which phase numbers this rule affects |

---

### 2.10 `stage_8` — Protocol Injection

Embeds verification protocols (pulse, seam, full checkpoint) into each phase.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `protocol_injected_phases` | `array` | Yes | One entry per phase from Stage 7, now with protocols embedded |
| `protocol_injected_phases[].phase_number` | `integer` | Yes | Matches `stage_7.phases[].phase_number` |
| `protocol_injected_phases[].pulse_checks` | `array` | Yes | Per-file existence and export checks |
| `protocol_injected_phases[].pulse_checks[].file_path` | `string` | Yes | File to check |
| `protocol_injected_phases[].pulse_checks[].checks` | `string[]` | Yes | What to verify (e.g., `"file exists"`, `"exports function X"`) |
| `protocol_injected_phases[].seam_checks` | `array` | Yes | Connection-point checks |
| `protocol_injected_phases[].seam_checks[].component_a` | `string` | Yes | First component/file |
| `protocol_injected_phases[].seam_checks[].component_b` | `string` | Yes | Second component/file |
| `protocol_injected_phases[].seam_checks[].verification` | `string` | Yes | What to verify at the seam (e.g., `"A imports B correctly"`) |
| `protocol_injected_phases[].full_checkpoint` | `object` | Yes | End-of-phase checkpoint |
| `protocol_injected_phases[].full_checkpoint.pattern_checks` | `string[]` | Yes | Pattern verifications to run |
| `protocol_injected_phases[].full_checkpoint.functional_checks` | `string[]` | Yes | Functional verifications (e.g., `"npm run build"`, `"npm run test"`) |
| `protocol_injected_phases[].full_checkpoint.gate_condition` | `string` | Yes | What must pass to proceed to next phase |
| `protocol_injected_phases[].violation_rules` | `object` | Yes | Violation handling for this phase |
| `protocol_injected_phases[].violation_rules.low` | `object` | Yes | LOW severity config |
| `protocol_injected_phases[].violation_rules.low.triggers` | `string[]` | Yes | What triggers LOW (e.g., `"touched shared types/config"`) |
| `protocol_injected_phases[].violation_rules.low.response` | `string` | Yes | Action: `"log_and_proceed"` |
| `protocol_injected_phases[].violation_rules.medium` | `object` | Yes | MEDIUM severity config |
| `protocol_injected_phases[].violation_rules.medium.triggers` | `string[]` | Yes | What triggers MEDIUM (e.g., `"modified another phase's file"`) |
| `protocol_injected_phases[].violation_rules.medium.response` | `string` | Yes | Action: `"review_and_decide"` |
| `protocol_injected_phases[].violation_rules.medium.decision_tree` | `object` | Yes | Decision logic: `{"additive": "proceed_with_caution", "destructive": "revert_file", "unclear": "flag_human"}` |
| `protocol_injected_phases[].violation_rules.high` | `object` | Yes | HIGH severity config |
| `protocol_injected_phases[].violation_rules.high.triggers` | `string[]` | Yes | What triggers HIGH (e.g., `"deleted files"`, `"changed core config"`) |
| `protocol_injected_phases[].violation_rules.high.response` | `string` | Yes | Action: `"revert_entire_phase"` |
| `protocol_injected_phases[].violation_rules.critical` | `object` | Yes | CRITICAL severity config |
| `protocol_injected_phases[].violation_rules.critical.triggers` | `string[]` | Yes | What triggers CRITICAL (e.g., `"modified .env"`, `"modified CLAUDE.md"`, `"modified build config"`) |
| `protocol_injected_phases[].violation_rules.critical.response` | `string` | Yes | Action: `"full_stop"` |
| `protocol_injected_phases[].overhead_tokens` | `integer` | Yes | Actual token overhead for this phase's protocols (~25,000) |
| `overhead_breakdown` | `object` | Yes | Token overhead breakdown template |
| `overhead_breakdown.build_rules_preamble` | `integer` | Yes | ~8,000 tokens |
| `overhead_breakdown.file_sandbox_declaration` | `integer` | Yes | ~2,000 tokens |
| `overhead_breakdown.build_order_with_pulse` | `integer` | Yes | ~3,000 tokens |
| `overhead_breakdown.seam_check_definitions` | `integer` | Yes | ~2,000 tokens |
| `overhead_breakdown.full_checkpoint` | `integer` | Yes | ~5,000 tokens |
| `overhead_breakdown.pattern_verification` | `integer` | Yes | ~3,000 tokens |
| `overhead_breakdown.violation_handling` | `integer` | Yes | ~2,000 tokens |

---

### 2.11 `stage_9` — Verification Agent Setup

Configures how build phases are verified — either automated Agent B or manual preamble merge.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `verification_mode` | `string` | Yes | Enum: `"automated_agent_b"`, `"manual_preamble_merge"` |
| `two_strike_rule` | `object` | Yes | Auto-retry and failure escalation config |
| `two_strike_rule.max_retries_per_phase` | `integer` | Yes | Always `2` |
| `two_strike_rule.on_second_failure` | `string` | Yes | Always `"stop_for_human_review"` |
| `two_strike_rule.rationale` | `string` | Yes | `"If 2 fresh agents fail the same phase, the spec is wrong, not the agents"` |
| `verification_protocol` | `object` | Yes | Four-step verification protocol |
| `verification_protocol.step_1_self_report` | `object` | Yes | Agent lists files touched |
| `verification_protocol.step_1_self_report.description` | `string` | Yes | What the agent must report |
| `verification_protocol.step_1_self_report.output_format` | `string` | Yes | Expected output format |
| `verification_protocol.step_2_diff_check` | `object` | Yes | Git diff verification |
| `verification_protocol.step_2_diff_check.command` | `string` | Yes | `"git diff PHASE_N_BASELINE..HEAD --name-only"` |
| `verification_protocol.step_2_diff_check.compare_against` | `string[]` | Yes | `["allowed_files_list", "self_report"]` |
| `verification_protocol.step_2_diff_check.mismatch_is_violation` | `boolean` | Yes | `true` |
| `verification_protocol.step_3_violation_response` | `string` | Yes | References `stage_8.protocol_injected_phases[].violation_rules` |
| `verification_protocol.step_4_functional` | `object` | Yes | Functional verification |
| `verification_protocol.step_4_functional.commands` | `string[]` | Yes | Commands to run (e.g., `["npm run build", "npm run test"]`) |
| `verification_protocol.step_4_functional.page_render_check` | `boolean` | Yes | Whether to verify page renders |
| `per_phase_checker_config` | `array` | Yes | Phase-specific verification overrides |
| `per_phase_checker_config[].phase_number` | `integer` | Yes | Phase number |
| `per_phase_checker_config[].additional_checks` | `string[]` | No | Extra checks for this specific phase |
| `per_phase_checker_config[].skip_functional` | `boolean` | No | If true, skip functional checks (for infrastructure-only phases) |
| `agent_b_config` | `object` | No | Present only if `verification_mode` is `"automated_agent_b"` |
| `agent_b_config.context_tokens` | `integer` | Yes | ~10,000 tokens per verification |
| `agent_b_config.clean_context` | `boolean` | Yes | Always `true` — Agent B starts fresh |
| `agent_b_config.persistent_across_phases` | `boolean` | Yes | Whether Agent B accumulates pattern awareness |

---

### 2.12 `stage_10` — Output Generator

Produces the final deliverable package: phase files, build script, and reference documents.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `output_manifest` | `array` | Yes | List of all files to generate |
| `output_manifest[].file_path` | `string` | Yes | Output file path (e.g., `"phases/phase-1.md"`, `"build.sh"`) |
| `output_manifest[].file_type` | `string` | Yes | Enum: `"phase"`, `"build_script"`, `"claude_md"`, `"build_rules"`, `"readme"` |
| `output_manifest[].estimated_tokens` | `integer` | Yes | Estimated token count |
| `generated_files` | `object` | Yes | Generated file contents keyed by file path |
| `generated_files.<path>` | `string` | Yes | Full content of the generated file |
| `build_script_config` | `object` | Yes | Configuration for the build.sh script |
| `build_script_config.snapshot_enabled` | `boolean` | Yes | Whether git snapshots are created per phase |
| `build_script_config.rollback_enabled` | `boolean` | Yes | Whether rollback on failure is enabled |
| `build_script_config.forbidden_file_detection` | `boolean` | Yes | Whether forbidden file access is detected |
| `build_script_config.two_strike_retry` | `boolean` | Yes | Whether auto-retry with 2-strike rule is enabled |
| `build_script_config.chaining_operator` | `string` | Yes | Always `"&&"` (never `";"`) |
| `platform_target` | `string` | Yes | Target platform for wrapper. Enum: `"claude_cli"`, `"claude_web"`, `"codex_cli"`, `"gemini_cli"`, `"cursor"`, `"windsurf"`, `"bolt"`, `"lovable"`, `"generic"` |
| `claude_md_content` | `string` | Yes | Generated CLAUDE.md content |
| `build_rules_content` | `string` | Yes | Generated BUILD_RULES.md content |
| `final_validation` | `object` | Yes | Final validation results |
| `final_validation.open_questions_count` | `integer` | Yes | Must be `0` |
| `final_validation.all_phases_fit_budget` | `boolean` | Yes | Every phase within token budget |
| `final_validation.all_mechanisms_covered` | `boolean` | Yes | Every mechanism from Stage 4 appears in at least one phase |
| `final_validation.all_pages_covered` | `boolean` | Yes | Every page from Stage 6b appears in at least one phase |

---

## 3. Stage Read/Write Map

Every field a stage READS must have been WRITTEN by a previous stage. No forward references.

| Stage | Reads | Writes |
|-------|-------|--------|
| **0 — Technical Foundation** | *(none — first stage)* | `metadata.*`, `stage_0.platform_profile`, `stage_0.tech_stack`, `stage_0.checklist_rule_ids`, `stage_0.command_allowlist` |
| **1 — Idea Capture** | `stage_0.platform_profile` (to tailor capture prompts) | `stage_1.raw_input`, `stage_1.input_format`, `stage_1.captured_at`, `stage_1.word_count`, `stage_1.char_count`, `stage_1.explicit_corrections`, `metadata.current_stage`, `metadata.updated_at`, `metadata.confidence_scores["1"]`, `metadata.stage_timestamps["1"]` |
| **2 — Gap Analysis** | `stage_1.raw_input`, `stage_1.word_count`, `stage_1.explicit_corrections`, `stage_0.platform_profile`, `stage_0.checklist_rule_ids` | `stage_2.archetype_matches`, `stage_2.mechanisms_identified`, `stage_2.mechanisms_gaps`, `stage_2.gap_questions`, `stage_2.gap_answers`, `stage_2.combined_raw`, `stage_2.completeness_score`, `stage_2.checklist_coverage`, `stage_2.scope_contract`, `metadata.archetype_matches`, `metadata.scope_contract_hash`, `metadata.current_stage`, `metadata.updated_at`, `metadata.confidence_scores["2"]`, `metadata.stage_timestamps["2"]` |
| **3 — Agent OS Structuring** | `stage_2.combined_raw`, `stage_2.archetype_matches`, `stage_2.mechanisms_identified`, `stage_2.checklist_coverage`, `stage_1.explicit_corrections` | `stage_3.concept_and_context`, `stage_3.target_user_and_market`, `stage_3.feasibility_assessment`, `stage_3.problem_statement`, `stage_3.ambiguity_resolutions`, `stage_3.drift_anchor`, `metadata.current_stage`, `metadata.updated_at`, `metadata.confidence_scores["3"]`, `metadata.stage_timestamps["3"]` |
| **4 — Mechanism Extraction** | `stage_3.concept_and_context`, `stage_3.target_user_and_market`, `stage_3.problem_statement`, `stage_3.drift_anchor`, `stage_2.mechanisms_identified`, `stage_2.scope_contract` | `stage_4.mechanisms`, `stage_4.mechanism_dependencies`, `stage_4.mechanism_count`, `stage_4.dual_design_count`, `metadata.current_stage`, `metadata.updated_at`, `metadata.confidence_scores["4"]`, `metadata.stage_timestamps["4"]` |
| **5 — 7-Question Scaffolding** | `stage_4.mechanisms`, `stage_4.mechanism_dependencies`, `stage_0.checklist_rule_ids`, `stage_3.drift_anchor`, `stage_2.scope_contract` | `stage_5.mechanism_blueprints`, `stage_5.build_rules_applied`, `metadata.current_stage`, `metadata.updated_at`, `metadata.confidence_scores["5"]`, `metadata.stage_timestamps["5"]` |
| **6 — Layout + Mockups + Style** | `stage_5.mechanism_blueprints`, `stage_4.mechanisms`, `stage_4.mechanism_dependencies`, `stage_3.concept_and_context`, `stage_3.target_user_and_market`, `stage_2.archetype_matches`, `stage_3.drift_anchor` | `stage_6.sub_6a`, `stage_6.sub_6b`, `stage_6.sub_6c`, `metadata.current_stage`, `metadata.updated_at`, `metadata.confidence_scores["6"]`, `metadata.stage_timestamps["6"]` |
| **7 — Phase Sequencing** | `stage_5.mechanism_blueprints`, `stage_4.mechanisms`, `stage_4.mechanism_dependencies`, `stage_6.sub_6a`, `stage_6.sub_6b`, `stage_6.sub_6c.design_tokens`, `stage_3.drift_anchor`, `stage_2.scope_contract` | `stage_7.token_budget`, `stage_7.phases`, `stage_7.mandatory_build_order`, `metadata.current_stage`, `metadata.updated_at`, `metadata.confidence_scores["7"]`, `metadata.stage_timestamps["7"]` |
| **8 — Protocol Injection** | `stage_7.phases`, `stage_7.token_budget`, `stage_5.mechanism_blueprints`, `stage_4.mechanism_dependencies` | `stage_8.protocol_injected_phases`, `stage_8.overhead_breakdown`, `metadata.current_stage`, `metadata.updated_at`, `metadata.confidence_scores["8"]`, `metadata.stage_timestamps["8"]` |
| **9 — Verification Agent Setup** | `stage_8.protocol_injected_phases`, `stage_7.phases`, `stage_0.tech_stack` | `stage_9.verification_mode`, `stage_9.two_strike_rule`, `stage_9.verification_protocol`, `stage_9.per_phase_checker_config`, `stage_9.agent_b_config`, `metadata.current_stage`, `metadata.updated_at`, `metadata.confidence_scores["9"]`, `metadata.stage_timestamps["9"]` |
| **10 — Output Generator** | `stage_3.concept_and_context`, `stage_4.mechanisms`, `stage_5.mechanism_blueprints`, `stage_6.sub_6a`, `stage_6.sub_6b`, `stage_6.sub_6c`, `stage_7.phases`, `stage_7.token_budget`, `stage_8.protocol_injected_phases`, `stage_8.overhead_breakdown`, `stage_9.verification_mode`, `stage_9.two_strike_rule`, `stage_9.verification_protocol`, `stage_9.per_phase_checker_config`, `stage_9.agent_b_config`, `stage_0.platform_profile`, `stage_0.tech_stack`, `stage_3.drift_anchor` | `stage_10.output_manifest`, `stage_10.generated_files`, `stage_10.build_script_config`, `stage_10.platform_target`, `stage_10.claude_md_content`, `stage_10.build_rules_content`, `stage_10.final_validation`, `metadata.current_stage`, `metadata.status` → `"completed"`, `metadata.updated_at`, `metadata.confidence_scores["10"]`, `metadata.stage_timestamps["10"]` |

---

## 4. Version Control Protocol

### Snapshot Naming

After each stage completes successfully, save an immutable snapshot:

```
context_packet_v0.json   ← after Stage 0 completes
context_packet_v1.json   ← after Stage 1 completes
context_packet_v2.json   ← after Stage 2 completes
...
context_packet_v10.json  ← after Stage 10 completes (final output)
```

The working copy is always `context_packet.json` — this is the "current" version being modified.

### Immutability Rule

Once `context_packet_vN.json` is written, it is **never modified**. If you need to re-run Stage N:

1. Load `context_packet_v{N-1}.json`
2. Copy it to `context_packet.json` (overwrite the working copy)
3. Re-run Stage N
4. Save the new result as `context_packet_vN.json` (overwrite the old vN — the ONLY exception to immutability)

### Snapshot Metadata

Each snapshot includes a `_snapshot_metadata` field at the top level:

```json
{
  "_snapshot_metadata": {
    "snapshot_stage": 2,
    "snapshot_timestamp": "2026-04-03T10:30:00Z",
    "pipeline_version": "1.0.0",
    "confidence_score": 87,
    "gate_result": "pass",
    "checksum": "sha256:abc123..."
  },
  "metadata": { ... },
  "stage_0": { ... },
  "stage_1": { ... },
  "stage_2": { ... },
  "stage_3": null,
  ...
}
```

| Field | Type | Description |
|-------|------|-------------|
| `snapshot_stage` | `integer` | Stage number this snapshot was taken after |
| `snapshot_timestamp` | `string` | ISO 8601 when the snapshot was saved |
| `pipeline_version` | `string` | Semver of the pipeline |
| `confidence_score` | `number` | Confidence score of the completed stage |
| `gate_result` | `string` | Enum: `"pass"`, `"flag"`, `"fail"` |
| `checksum` | `string` | SHA-256 hash of the packet contents (excluding this metadata field) |

### Rollback Procedure

1. Identify the last good stage: find the highest `N` where `context_packet_vN.json` has `gate_result: "pass"`
2. Copy `context_packet_vN.json` to `context_packet.json`
3. Set `metadata.current_stage` to `N`
4. Set `metadata.status` to `"in_progress"`
5. Re-run Stage `N+1`

---

## 5. Escape Hatch Schema

When a stage fails and cannot proceed, it writes an escape hatch record. This record is appended to `metadata.escape_hatches` and also written to the stage's own namespace.

### Complete Schema

```json
{
  "stage": 4,
  "timestamp": "2026-04-03T14:30:00Z",
  "status": "NEEDS_HUMAN",
  "progress_summary": "Extracted 6 of 9 mechanisms. Stuck on mechanism #7.",
  "problem": "User described a 'smart matching algorithm' but provided no criteria for what 'smart' means. Cannot classify as OBVIOUS or NEEDS_EVALUATION without knowing the matching dimensions.",
  "attempted": [
    "Asked follow-up question about matching criteria",
    "Searched description for implicit criteria",
    "Checked archetype defaults for matching"
  ],
  "partial_output": {
    "mechanisms_completed": [ ... ],
    "mechanism_in_progress": { ... }
  },
  "suggested_actions": [
    "Ask user: What factors determine a good match?",
    "Ask user: Can you give an example of a good match and a bad match?",
    "Use Developer's Choice: implement basic keyword matching (can be upgraded later)"
  ],
  "resume_from": "mechanism_7_classification",
  "confidence_at_failure": 45,
  "scope_creep_detected": false
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `stage` | `integer` | Yes | Which stage failed (0-10) |
| `timestamp` | `string` | Yes | ISO 8601 when failure occurred |
| `status` | `string` | Yes | Always `"NEEDS_HUMAN"` |
| `progress_summary` | `string` | Yes | Human-readable summary of how far the stage got |
| `problem` | `string` | Yes | Detailed description of what went wrong and why the stage cannot continue |
| `attempted` | `string[]` | Yes | List of approaches already tried before giving up |
| `partial_output` | `object` | Yes | Whatever output the stage managed to produce before failing. Structure varies by stage. |
| `suggested_actions` | `string[]` | Yes | Actionable suggestions for the human (minimum 2) |
| `resume_from` | `string` | Yes | Identifier for where to resume within the stage (stage-specific label) |
| `confidence_at_failure` | `number` | Yes | Confidence score at the point of failure (0-100) |
| `scope_creep_detected` | `boolean` | Yes | Whether the failure was caused by scope creep beyond the Stage 2 contract |

### Recovery Flow

1. Pipeline detects `gate_result: "fail"` (confidence < 70) or stage throws exception
2. Stage writes escape hatch record to `metadata.escape_hatches[]`
3. Stage writes `partial_output` to its own namespace (e.g., `stage_4.partial_output`)
4. `metadata.status` set to `"needs_human"`
5. Pipeline controller presents escape hatch to user
6. User responds (answers questions, makes decisions, or says "use developer's choice")
7. Pipeline loads snapshot `context_packet_v{N-1}.json`, applies user's input, re-runs Stage N

---

## 6. Future: Existing App Support

The schema supports a future `app_type: "existing"` mode. These fields live in `stage_0.existing_app_analysis` and are all **optional** (unused for `app_type: "greenfield"`).

```json
{
  "stage_0": {
    "existing_app_analysis": {
      "file_tree": [],
      "framework_detection": {},
      "dependency_list": [],
      "existing_feature_inventory": [],
      "checklist_check_mode": {},
      "existing_mechanisms": [],
      "new_mechanisms_needed": []
    }
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `file_tree` | `string[]` | List of file paths in the existing codebase |
| `framework_detection` | `object` | Detected frameworks/libraries with versions |
| `framework_detection.primary_framework` | `string` | Main framework (e.g., `"Next.js 14"`) |
| `framework_detection.ui_library` | `string` | UI library (e.g., `"Tailwind CSS"`) |
| `framework_detection.database` | `string` | Database in use |
| `framework_detection.other` | `object` | Additional detected tech |
| `dependency_list` | `array` | Package dependencies with versions |
| `dependency_list[].name` | `string` | Package name |
| `dependency_list[].version` | `string` | Current version |
| `dependency_list[].type` | `string` | Enum: `"production"`, `"development"` |
| `existing_feature_inventory` | `array` | Features already implemented |
| `existing_feature_inventory[].name` | `string` | Feature name |
| `existing_feature_inventory[].files` | `string[]` | Files that implement this feature |
| `existing_feature_inventory[].mechanism_ids` | `string[]` | Maps to A-N categories |
| `checklist_check_mode` | `object` | Martin's checklist in CHECK mode |
| `checklist_check_mode.rules_followed` | `string[]` | Rule IDs already followed |
| `checklist_check_mode.rules_violated` | `string[]` | Rule IDs currently violated |
| `checklist_check_mode.rules_not_applicable` | `string[]` | Rule IDs not relevant |
| `existing_mechanisms` | `array` | Mechanisms that already exist (no need to build) |
| `existing_mechanisms[].mechanism_id` | `string` | A-N category reference |
| `existing_mechanisms[].description` | `string` | How it is currently implemented |
| `existing_mechanisms[].files` | `string[]` | Implementation files |
| `new_mechanisms_needed` | `array` | Mechanisms to add (feeds into Stage 4) |
| `new_mechanisms_needed[].category_id` | `string` | A-N category |
| `new_mechanisms_needed[].description` | `string` | What needs to be built |

---

## 7. Example: Context Packet After Stage 2 Completes

Realistic sample data for a "TaskFlow" task manager app. Shows the packet state after Stage 2 has finished — Stages 3-10 are null.

```json
{
  "_snapshot_metadata": {
    "snapshot_stage": 2,
    "snapshot_timestamp": "2026-04-03T10:35:22Z",
    "pipeline_version": "1.0.0",
    "confidence_score": 87,
    "gate_result": "pass",
    "checksum": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  },
  "metadata": {
    "pipeline_version": "1.0.0",
    "created_at": "2026-04-03T10:20:00Z",
    "updated_at": "2026-04-03T10:35:22Z",
    "current_stage": 2,
    "status": "in_progress",
    "app_type": "greenfield",
    "archetype_matches": ["dashboard", "tool"],
    "confidence_scores": {
      "0": {
        "score": 95,
        "dimensions": { "completeness": 95, "clarity": 95, "consistency": 95 },
        "gate_result": "pass"
      },
      "1": {
        "score": 72,
        "dimensions": { "completeness": 60, "clarity": 80, "consistency": 75 },
        "gate_result": "flag"
      },
      "2": {
        "score": 87,
        "dimensions": { "completeness": 90, "clarity": 85, "consistency": 86 },
        "gate_result": "pass"
      }
    },
    "stage_timestamps": {
      "0": "2026-04-03T10:20:15Z",
      "1": "2026-04-03T10:22:40Z",
      "2": "2026-04-03T10:35:22Z"
    },
    "escape_hatches": [],
    "scope_contract_hash": "sha256:a1b2c3d4e5f6789012345678abcdef0123456789abcdef0123456789abcdef01"
  },
  "stage_0": {
    "platform_profile": {
      "boilerplate_id": "supabase_web",
      "boilerplate_name": "Supabase Web App",
      "description": "Next.js + Supabase + Tailwind CSS full-stack web app with auth, database, and real-time subscriptions"
    },
    "tech_stack": {
      "framework": "Next.js 14",
      "database": "Supabase/Postgres",
      "auth_provider": "Supabase Auth",
      "hosting": "Vercel",
      "additional": {
        "styling": "Tailwind CSS",
        "state_management": "React Query + Zustand"
      }
    },
    "checklist_rule_ids": [
      "SC-001", "SC-002", "SC-003", "SR-001", "SR-002",
      "TS-001", "TS-002", "AP-001", "AP-002", "AP-003",
      "AU-001", "AU-002", "SE-001", "SE-002", "ST-001"
    ],
    "command_allowlist": ["npm", "npx", "node", "git", "curl"],
    "existing_app_analysis": null
  },
  "stage_1": {
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
  },
  "stage_2": {
    "archetype_matches": [
      {
        "archetype": "dashboard",
        "confidence": 75,
        "rationale": "Dashboard with charts showing task completion metrics, plus kanban board view"
      },
      {
        "archetype": "tool",
        "confidence": 85,
        "rationale": "Productivity tool for team task management with project organization, assignment, and tracking"
      }
    ],
    "mechanisms_identified": [
      {
        "category_id": "A",
        "category_name": "Data Input",
        "sub_types": ["forms"],
        "evidence": "Users can create projects and add tasks to them. Tasks have due dates, priorities, and assignees."
      },
      {
        "category_id": "B",
        "category_name": "Data Storage",
        "sub_types": ["relational_db"],
        "evidence": "Projects contain tasks with due dates, priorities, assignees — relational structure implied."
      },
      {
        "category_id": "D",
        "category_name": "Data Output",
        "sub_types": ["kanban_board", "lists_tables", "charts_graphs"],
        "evidence": "Kanban board view, list view sorted by due date, dashboard with completion chart."
      },
      {
        "category_id": "E",
        "category_name": "Authentication",
        "sub_types": ["email_password", "oauth_social"],
        "evidence": "Sign up with email or Google. Also GitHub login for developer teams."
      },
      {
        "category_id": "G",
        "category_name": "Communication",
        "sub_types": ["email", "in_app_notifications"],
        "evidence": "Notifications when someone assigns you a task or when a due date is coming up. Email and in-app."
      },
      {
        "category_id": "K",
        "category_name": "Collaboration",
        "sub_types": ["sharing"],
        "evidence": "Teams can create workspaces and invite members. Assign tasks to other people on your team."
      }
    ],
    "mechanisms_gaps": [
      {
        "category_id": "C",
        "category_name": "Data Processing",
        "resolution": "asked"
      },
      {
        "category_id": "F",
        "category_name": "Authorization",
        "resolution": "asked"
      },
      {
        "category_id": "H",
        "category_name": "Integration",
        "resolution": "not_needed"
      },
      {
        "category_id": "I",
        "category_name": "Workflow",
        "resolution": "asked"
      },
      {
        "category_id": "J",
        "category_name": "Search & Discovery",
        "resolution": "asked"
      },
      {
        "category_id": "L",
        "category_name": "Monetization",
        "resolution": "not_needed"
      },
      {
        "category_id": "M",
        "category_name": "Admin/Ops",
        "resolution": "developers_choice"
      },
      {
        "category_id": "N",
        "category_name": "Infrastructure",
        "resolution": "developers_choice"
      }
    ],
    "gap_questions": [
      {
        "id": "gq_001",
        "category_id": "F",
        "question_text": "What roles should exist in a workspace? (e.g., Admin, Member, Viewer) Can all members create projects or just admins?",
        "source": "mechanism_framework"
      },
      {
        "id": "gq_002",
        "category_id": "C",
        "question_text": "Should tasks have any automated processing? (e.g., auto-move overdue tasks, recurring tasks, auto-priority based on due date)",
        "source": "mechanism_framework"
      },
      {
        "id": "gq_003",
        "category_id": "I",
        "question_text": "When a task moves from 'In Progress' to 'Done', should anything happen automatically? (e.g., notify assignee, update project progress, trigger next task)",
        "source": "mechanism_framework"
      },
      {
        "id": "gq_004",
        "category_id": "J",
        "question_text": "Should users be able to search across tasks and projects? Filter by assignee, priority, or due date range?",
        "source": "master_checklist"
      }
    ],
    "gap_answers": [
      {
        "question_id": "gq_001",
        "answer_text": "Yeah, Admin and Member roles. Admins can invite people and manage the workspace. Members can create projects and tasks. No viewer role needed.",
        "is_default": false
      },
      {
        "question_id": "gq_002",
        "answer_text": "Recurring tasks would be cool actually. And yeah, overdue tasks should get flagged somehow — maybe a visual indicator, not auto-moved.",
        "is_default": false
      },
      {
        "question_id": "gq_003",
        "answer_text": "Just notify the project owner when a task is completed. Nothing else automatic.",
        "is_default": false
      },
      {
        "question_id": "gq_004",
        "answer_text": "Yes, definitely search and filter. Filter by assignee and priority at minimum.",
        "is_default": false
      }
    ],
    "combined_raw": "I want to build a task manager app. Like Todoist but simpler. Users can create projects and add tasks to them. Tasks have due dates, priorities (high/medium/low), and you can assign them to other people on your team. I want a kanban board view where you drag tasks between columns like To Do, In Progress, and Done. Also a regular list view sorted by due date. Users need to sign up with email or Google. Oh wait, not just Google — also GitHub login since this is for developer teams. There should be notifications when someone assigns you a task or when a due date is coming up. Maybe email and in-app notifications. I want it to look clean and modern, not cluttered. Dark mode would be nice. Teams should be able to create workspaces and invite members. Oh and I forgot — there should be a simple dashboard showing how many tasks are done vs pending, maybe a chart.\n\n[Gap Answers]\nRoles: Admin and Member roles. Admins can invite people and manage the workspace. Members can create projects and tasks. No viewer role needed.\nAutomation: Recurring tasks supported. Overdue tasks get flagged visually, not auto-moved.\nWorkflow: Notify project owner when a task is completed. No other automatic triggers.\nSearch: Yes, search and filter by assignee and priority at minimum.",
    "completeness_score": 87,
    "checklist_coverage": {
      "covered": [
        "Problem & Purpose", "Target Users & Personas", "Core Features",
        "User Flows", "Data Model", "Authentication", "Authorization",
        "UI/UX Patterns", "State Management", "Search & Discovery"
      ],
      "not_applicable": [
        "Monetization", "Legal/Compliance", "Internationalization",
        "Offline Support", "Migration/Import"
      ],
      "deferred": [
        "API Design", "Security Requirements", "Performance Requirements",
        "Scalability", "Responsive Design", "Accessibility", "Error Handling",
        "Testing Strategy", "Deployment", "Monitoring & Logging",
        "Third-Party Integrations", "Admin/Back-office", "Analytics",
        "Documentation", "Out of Scope"
      ]
    },
    "scope_contract": "IN SCOPE: Task management with projects, kanban + list views, team workspaces with Admin/Member roles, email + OAuth auth (Google, GitHub), email + in-app notifications, task search/filter, recurring tasks, completion dashboard with chart, dark mode. OUT OF SCOPE: Monetization, third-party integrations, offline support, internationalization, mobile app."
  },
  "stage_3": null,
  "stage_4": null,
  "stage_5": null,
  "stage_6": null,
  "stage_7": null,
  "stage_8": null,
  "stage_9": null,
  "stage_10": null
}
```

---

## Appendix A: Field Dependency Chain (Quality Check)

Verifying no forward references exist. For each stage's reads, confirming the writer:

| Stage Reads | Written By |
|-------------|-----------|
| `stage_0.platform_profile` → Stage 1 | Stage 0 writes it |
| `stage_1.raw_input` → Stage 2 | Stage 1 writes it |
| `stage_1.word_count` → Stage 2 | Stage 1 writes it |
| `stage_0.checklist_rule_ids` → Stage 2 | Stage 0 writes it |
| `stage_2.combined_raw` → Stage 3 | Stage 2 writes it |
| `stage_2.archetype_matches` → Stage 3 | Stage 2 writes it |
| `stage_2.mechanisms_identified` → Stage 3, 4 | Stage 2 writes it |
| `stage_3.concept_and_context` → Stage 4, 6, 10 | Stage 3 writes it |
| `stage_3.drift_anchor` → Stages 4, 5, 6, 7, 10 | Stage 3 writes it |
| `stage_2.scope_contract` → Stages 4, 5, 7 | Stage 2 writes it |
| `stage_4.mechanisms` → Stages 5, 6, 7, 10 | Stage 4 writes it |
| `stage_4.mechanism_dependencies` → Stages 5, 6, 7, 8 | Stage 4 writes it |
| `stage_5.mechanism_blueprints` → Stages 6, 7, 8, 10 | Stage 5 writes it |
| `stage_6.sub_6a` → Stages 7, 10 | Stage 6 writes it |
| `stage_6.sub_6b` → Stages 7, 10 | Stage 6 writes it |
| `stage_6.sub_6c` → Stages 7, 10 | Stage 6 writes it |
| `stage_7.phases` → Stages 8, 9, 10 | Stage 7 writes it |
| `stage_7.token_budget` → Stages 8, 10 | Stage 7 writes it |
| `stage_8.protocol_injected_phases` → Stages 9, 10 | Stage 8 writes it |
| `stage_8.overhead_breakdown` → Stage 10 | Stage 8 writes it |
| `stage_9.*` → Stage 10 | Stage 9 writes it |

**Result: No forward references.** Every field is written before it is read.

## Appendix B: Orphan Field Check

Every written field must be read by at least one downstream stage or appear in the final output:

| Field | Read By |
|-------|---------|
| `stage_0.command_allowlist` | Stage 10 (included in build script config) |
| `stage_1.input_format` | Stage 10 (final output metadata) |
| `stage_1.captured_at` | Stage 10 (final output metadata) |
| `stage_1.char_count` | Not directly read — **informational only**, retained for pipeline analytics. Acceptable: it is part of the Stage 1 snapshot and can be used for debugging/audit. |
| `stage_2.gap_questions` | Stage 10 (included in documentation of decisions made) |
| `stage_2.gap_answers` | Stage 10 (included in documentation of decisions made) |
| `stage_2.mechanisms_gaps` | Stage 4 (used to verify all gaps were addressed in mechanism extraction) |
| `stage_2.completeness_score` | Metadata confidence gate; Stage 10 documentation |
| `stage_2.checklist_coverage` | Stage 3 (guides structuring); Stage 10 documentation |
| `stage_3.target_user_and_market` | Stage 4, Stage 6 (design decisions); Stage 10 |
| `stage_3.feasibility_assessment` | Stage 10 (final output documentation) |
| `stage_3.problem_statement` | Stage 4 (mechanism extraction context); Stage 10 |
| `stage_3.ambiguity_resolutions` | Stage 10 (decision documentation) |
| `stage_4.mechanism_count` | Stage 7 (phase planning); Stage 10 (summary stats) |
| `stage_4.dual_design_count` | Stage 5 (knows to scaffold both); Stage 10 (summary stats) |
| `stage_5.build_rules_applied` | Stage 10 (BUILD_RULES.md generation) |
| `stage_7.mandatory_build_order` | Stage 10 (build script generation) |
| `stage_9.two_strike_rule` | Stage 10 (build script config) |

**Result: No orphan fields.** Every field is consumed downstream or is part of the final deliverable package.
