# Build Stage 10 Skill: Output Generator

> **Type:** Self-contained handoff prompt for a fresh Claude Code agent
> **Output:** `docs/page-prds/prd-maker/skills/stage-10-output-generator/SKILL.md`

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

**You are building Stage 10: Output Generator.** It is the FINAL stage. It reads from every prior stage and writes the deliverable package. There is no stage after it -- its output goes to the end user (a coding agent or human developer).

---

## Your Stage: Output Generator

### Purpose

Stage 10 is pure serialization, not design. By this point every decision has been made -- ZERO open questions remain. A builder agent can execute the output without asking anything. This stage renders all preceding work (Stages 0-9) into a deliverable package of files: phase documents, a build script, CLAUDE.md, BUILD_RULES.md, and a README.

Stated plainly: "Everything is defined. You're just rendering the format -- bash script, markdown PRD, downloadable doc. This is serialization, not design."

### Inputs (What This Stage Receives)

This stage reads the FULL context packet from all prior stages. The specific fields consumed are:

**From Stage 0 -- Technical Foundation:**
- `stage_0.platform_profile` -- Stack context (framework, database, auth, hosting, boilerplate_id)
- `stage_0.tech_stack` -- Technology decisions (framework, database, auth_provider, hosting)
- `stage_0.command_allowlist` -- Project-specific allowed bash commands (included in build script config)

**From Stage 3 -- Agent OS Structuring:**
- `stage_3.concept_and_context` -- Product identity (name, description, value proposition)
- `stage_3.drift_anchor` -- Canonical product description used as reference point throughout

**From Stage 4 -- Mechanism Extraction:**
- `stage_4.mechanisms` -- Complete mechanism inventory with IDs, names, categories, approaches, dependencies

**From Stage 5 -- 7-Question Scaffolding:**
- `stage_5.mechanism_blueprints` -- Per-mechanism Wall/Door/Room classifications with verification methods
- `stage_5.build_rules_applied` -- Which Martin checklist rules were applied (feeds BUILD_RULES.md generation)

**From Stage 6 -- Layout + Mockups + Style:**
- `stage_6.sub_6a` -- Page arrangement and navigation structure
- `stage_6.sub_6b` -- Per-page component specs and wireframe patterns
- `stage_6.sub_6c` -- Design system tokens (colors, typography, spacing, animations)

**From Stage 7 -- Phase Sequencing:**
- `stage_7.phases` -- Phase structure with file sandboxes, build orders, and feature assignments
- `stage_7.token_budget` -- Per-phase token estimates and total budget math
- `stage_7.mandatory_build_order` -- Required build sequence across phases

**From Stage 8 -- Protocol Injection:**
- `stage_8.protocol_injected_phases` -- Phases with embedded pulse/seam/full checkpoint protocols
- `stage_8.overhead_breakdown` -- Per-phase overhead token costs (preamble, sandbox, checks, etc.)

**From Stage 9 -- Verification Agent Setup:**
- `stage_9.verification_mode` -- Selected verification mode (single_agent, dual_agent, hybrid)
- `stage_9.two_strike_rule` -- Two-strike retry configuration (retry_count, escalation_behavior)
- `stage_9.verification_protocol` -- Verification protocol details
- `stage_9.per_phase_checker_config` -- Per-phase checker configuration
- `stage_9.agent_b_config` -- Separate checker agent configuration (if dual_agent mode)

**From metadata:**
- `metadata.app_type` -- greenfield or existing
- `metadata.archetype_matches` -- Matched archetypes from Stage 2
- `metadata.confidence_scores` -- All prior stage confidence scores

### Outputs (What This Stage Produces)

Written to `context_packet.stage_10`:

| Field | Type | Description |
|-------|------|-------------|
| `output_manifest` | `array` | List of all files to generate, each with `file_path`, `file_type`, `estimated_tokens` |
| `generated_files` | `object` | Full content of each generated file, keyed by file path (e.g., `"phases/phase-1.md"`: "...content...") |
| `build_script_config` | `object` | Build script configuration: `snapshot_enabled`, `rollback_enabled`, `forbidden_file_detection`, `two_strike_retry`, `chaining_operator` (always `"&&"`) |
| `platform_target` | `string` | Target platform. Enum: `"claude_cli"`, `"claude_web"`, `"codex_cli"`, `"gemini_cli"`, `"cursor"`, `"windsurf"`, `"bolt"`, `"lovable"`, `"generic"` |
| `claude_md_content` | `string` | Generated CLAUDE.md content (quick-reference guardrails, under 500 lines) |
| `build_rules_content` | `string` | Generated BUILD_RULES.md content (detailed reference playbook) |
| `final_validation` | `object` | Validation results: `open_questions_count` (must be `0`), `all_phases_fit_budget` (bool), `all_mechanisms_covered` (bool), `all_pages_covered` (bool) |

### Process

Stage 10 performs these steps in order:

**Step 1: Build the Output Manifest**

Enumerate every file that will be generated. For each, record:
- `file_path` (e.g., `"phases/phase-1.md"`, `"build.sh"`, `"CLAUDE.md"`, `"BUILD_RULES.md"`, `"README.md"`)
- `file_type` (enum: `"phase"`, `"build_script"`, `"claude_md"`, `"build_rules"`, `"readme"`)
- `estimated_tokens` (from Stage 7's token budget + Stage 8's overhead breakdown)

The number of phase files equals the `phase_count` from Stage 7.

**Step 2: Render Phase Files**

For each phase from `stage_8.protocol_injected_phases`, compile a standalone `phase-N.md` file containing all 9 required sections in this order:

1. **Build Rules Preamble** (~8,000 tokens) -- Martin's rules distilled as the agent's operating manual for HOW to behave while building. Architecture principles, modification rules, coding standards. Derived from `stage_5.build_rules_applied` and the agnostic checklist. Martin's rules are DISTRIBUTED here, not cited as a standalone block.
2. **File Sandbox Declaration** (~2,000 tokens) -- Three lists: files the agent CAN modify, CAN read, CANNOT touch. Pulled from `stage_7.phases[N].file_sandbox`.
3. **Build Order with Pulse Points** (~3,000 tokens) -- Feature implementation sequence with intermediate verification triggers. Derived from `stage_7.mandatory_build_order` and `stage_8.protocol_injected_phases[N].pulse_points`.
4. **Seam Check Definitions** (~2,000 tokens) -- Integration verification points where components meet. From `stage_8.protocol_injected_phases[N].seam_checks`.
5. **Objective and Feature Requirements** -- The actual implementation instructions. What to build, which mechanisms, which pages. From `stage_7.phases[N].features` cross-referenced with `stage_4.mechanisms` and `stage_6.sub_6b`.
6. **Pattern References** -- Specific `file:line` references to existing patterns the builder agent should follow. From `stage_5.mechanism_blueprints` (Wall/Door/Room classifications inform which patterns apply).
7. **Violation Handling Instructions** (~2,000 tokens) -- Decision tree for when rules are broken: LOW (log + continue), MEDIUM (fix before proceeding), HIGH (rollback to last pulse point), CRITICAL (stop + human review). From `stage_8.protocol_injected_phases[N].violation_handling`.
8. **Full Checkpoint at End** (~5,000 tokens) -- Self-report, git diff check, violation response, functional verification. From `stage_8.protocol_injected_phases[N].full_checkpoint`.
9. **Gate Condition** -- "ALL FOUR STEPS MUST PASS BEFORE PHASE [N+1] BEGINS" (or "PIPELINE COMPLETE" for the final phase).

Total overhead per phase: ~25,000 tokens (fixed, templated).

Each phase file MUST be self-contained -- copy-pasteable into a fresh agent context and executable without referencing other files (except READ-ONLY files in the codebase).

**Step 3: Generate build.sh**

Create the deterministic bash wrapper:

- `set -e` (stop on ANY error)
- Per-phase block: git snapshot, pre-build validation (lint + build), agent work, post-build validation, forbidden file detection via git diff against sandbox, commit
- Phase chaining with `&&` (NEVER `;`)
- Auto-retry logic implementing the two-strike rule from `stage_9.two_strike_rule`: if a phase fails verification, rollback and retry with a fresh agent; if it fails again, stop for human review
- Platform-adaptive commands based on `platform_target` (e.g., `npm run build` vs `flutter build` vs generic)
- Forbidden file detection via `git diff --name-only $SNAPSHOT | grep -E "forbidden_pattern"`

**Step 4: Generate CLAUDE.md**

Create the quick-reference guardrails file. This file lives in the repo root FOREVER. Every agent interaction reads it. It must be tight and fast -- under 500 lines.

Contents:
- Architecture Principles (distilled from Stage 5 blueprints and Martin's rules)
- Modification Rules (read before edit, don't refactor uninstructed, match existing style)
- Testing Protocol (compile check, render check, regression check)
- File Structure Map (generated from Stage 6 page arrangement and Stage 7 phase file sandboxes)
- Pointers to BUILD_RULES.md sections for deeper protocols (debugging, feature addition, code review)

CLAUDE.md is the "distilled" version. BUILD_RULES.md is the "full" version. CLAUDE.md points to BUILD_RULES.md sections by name.

**Step 5: Generate BUILD_RULES.md**

Create the detailed reference playbook. Derived from Martin's 13 modules, adapted to the user's chosen tech stack from `stage_0.tech_stack`:

| Module | BUILD_RULES.md Section |
|--------|----------------------|
| 08 (Bug Fix Protocol) | "Debugging Protocol" |
| 09 (Feature Add) | "Feature Addition Protocol" |
| 10 (Debug Protocol) | "Trace-First Debugging" |
| 13 (Testing Protocol) | "Testing & Verification" |
| 03 (Data Layer) | "Data Access Patterns" |
| 05 (CRUD Flow) | "Entity CRUD Pattern" |

Other modules (01 Scaffold, 02 Auth, 04 UI Kit, 06 Polish, 07 Style, 11 Clean Room, 12 PRD Generator) are either already handled by the phase files or the UI style system, and do not need separate BUILD_RULES.md sections.

**Step 6: Generate README.md**

Document what was built and how to continue:
- Product name and description (from `stage_3.concept_and_context`)
- Tech stack (from `stage_0.tech_stack`)
- How to run the build (platform-specific instructions)
- Phase overview (what each phase builds)
- How to add features after initial build (pointer to BUILD_RULES.md)

**Step 7: Platform Picker Rendering**

Adapt wrapper instructions based on `platform_target`:

| Platform | Execution Method | Automation Level |
|----------|-----------------|-----------------|
| `claude_cli` | `bash build.sh` (auto-invokes agent + checks) | Fully automatic |
| `claude_web` | Copy-paste `phase-N.md` per phase | Manual |
| `codex_cli` | Platform-specific CLI commands | Fully automatic |
| `gemini_cli` | Platform-specific CLI commands | Fully automatic |
| `cursor` / `windsurf` | Terminal access, semi-automatic | Semi-automatic |
| `bolt` / `lovable` | No terminal access | Manual export |
| `generic` | Copy-paste anywhere | Fully manual |

The phase file CONTENT stays the same across all platforms. Only the execution command and wrapper instructions change.

**Step 8: Internal Consistency Verification**

Before writing output, verify:
- Every file path in every sandbox declaration exists in a build order somewhere
- Every mechanism referenced in a phase file exists in `stage_4.mechanisms`
- Every page referenced in a phase file exists in `stage_6.sub_6b`
- Every import/reference pattern points to a file that another phase creates or that already exists as READ-ONLY
- `final_validation.open_questions_count` == 0
- `final_validation.all_phases_fit_budget` -- every phase within token budget
- `final_validation.all_mechanisms_covered` -- every mechanism from Stage 4 appears in at least one phase
- `final_validation.all_pages_covered` -- every page from Stage 6b appears in at least one phase

### Rules and Constraints

1. **Zero open questions.** By Stage 10, every ambiguity has been resolved. The builder agent executes without asking anything. If ANY open question is detected, the stage MUST NOT produce output -- trigger the escape hatch.

2. **Phase files are self-contained.** Each `phase-N.md` works independently if copy-pasted into a fresh agent context. No cross-file references except to READ-ONLY codebase files.

3. **build.sh uses `&&` not `;`.** Failure in one phase stops the pipeline. No silent continuation past failures.

4. **CLAUDE.md is distilled, not exhaustive.** Under 500 lines. It is read by EVERY agent interaction (even "fix this button color"), so it must be tight and fast. BUILD_RULES.md handles depth.

5. **Martin's rules are distributed, not centralized.** They appear through architecture decisions (Stage 5), build order (Stage 7), and preambles (Stage 10). There is NEVER a standalone "Martin's Rules" section anywhere in the output.

6. **Multiple consumption paths.** The output MUST support: (a) automated -- `bash build.sh`, (b) manual -- copy-paste `phase-N.md`, (c) hybrid -- bash crashes halfway, user picks up manually with the next phase file.

7. **Internal consistency verified.** Every file path in a sandbox exists in a build order. Every mechanism referenced in a phase exists in Stage 4. Every import pattern points to a file that gets created. No dangling references.

8. **The preamble is the operating manual.** The Build Rules Preamble in each phase file tells the agent HOW to behave. The rest of the phase file tells the agent WHAT to build. These are separate concerns and must not be mixed.

9. **Platform-adaptive, content-identical.** The phase content is the same for all platforms. Only the wrapper/execution instructions change.

---

## Files to Read Before Building

Read ALL of these files completely before writing any skill content:

1. **`docs/page-prds/prd-maker/stage-extractions/stage-10-extraction.md`** -- The full extraction dossier for Stage 10. This is your primary source of truth for what the stage does, including the output package structure, phase file format, build.sh structure, CLAUDE.md vs BUILD_RULES.md distinction, platform picker, and Tier 1/Tier 2 differences.

2. **`docs/page-prds/prd-maker/context-packet-schema.md`** -- The data schema. Find Stage 10's namespace (Section 2.12). Understand exactly which fields you read (from ALL prior stages) and write. Also study the Stage Read/Write Map (Section 3) which explicitly lists every field Stage 10 consumes.

3. **`docs/page-prds/prd-maker/stage-contracts.md`** -- Find Stage 10's contract. Your skill must produce output that meets all "Done When" criteria and passes the confidence scoring. Stage 10's contract is the final one -- its success criteria include: all 9 sections in every phase file, self-contained phases, build.sh with snapshot/rollback/retry, CLAUDE.md under 500 lines, internal consistency verified, and Martin's rules distributed (not centralized).

4. **`docs/page-prds/prd-maker/martin-agnostic-checklist.md`** -- The structural checklist (~192 rules across 22 categories + 43 banned patterns). Your skill generates CLAUDE.md and BUILD_RULES.md content derived from this checklist, adapted to the user's tech stack. Understand the classification system (UNIVERSAL/STACK-SPECIFIC/PATTERN) and severity levels (CRITICAL/STANDARD/POLISH).

5. **`docs/page-prds/prd-maker/nate-jones-skill-kit.md`** -- The skill-building methodology. Your SKILL.md must follow Nate's Prompt 2 output format (reverse-engineer from great output, not stated intentions) and pass Nate's Prompt 3 agent-readiness criteria (trigger routing, output completeness, edge case handling, composability).

6. **Stage-specific reference files:**

   - **`docs/page-prds/prd-maker/extracted-skills/nicknisi/references/contract-template.md`** -- Contract template format. Study the Problem Statement, Goals, Success Criteria, Scope Boundaries pattern. Stage 10 produces a README.md that uses a similar structure for documenting what was built.

   - **`docs/page-prds/prd-maker/extracted-skills/nicknisi/references/spec-template.md`** -- Spec template format. Study the File Changes, Implementation Details, Feedback Strategy, Validation Commands, Failure Modes patterns. Stage 10's phase files follow a similar but distinct structure (9-section format described above).

   - **`docs/page-prds/prd-maker/extracted-skills/ognjengt/skills/sop-creator/SKILL.md`** -- SOP creation pattern. Study how this skill handles: execution logic branching, writing rules as hard constraints, output format specification with exact structure, quality checklist self-verification, and defaults/assumptions. Stage 10's skill should follow similar patterns for its serialization logic.

---

## Skill Building Instructions

You are building a Claude Code skill using the **Nate B. Jones Output-Extraction Method** (Prompt 2). This means you do NOT write a vague process description -- you reverse-engineer what GREAT output looks like and encode that into the skill.

### The Build Process

**Step 1: Understand the output.** Read the Stage 10 extraction dossier. Understand what a PERFECT output package looks like. The output package consists of:
- `phases/phase-1.md` through `phases/phase-N.md` (each with 9 sections, each copy-paste ready)
- `build.sh` (deterministic bash wrapper with snapshot, verification, retry, rollback)
- `CLAUDE.md` (under 500 lines, quick-reference guardrails, pointers to BUILD_RULES.md)
- `BUILD_RULES.md` (detailed playbook derived from Martin's 13 modules)
- `README.md` (what was built, how to continue)

A PERFECT output has zero dangling references, zero open questions, every mechanism covered in at least one phase, every page covered, every phase within token budget, and supports automated/manual/hybrid consumption.

**Step 2: Extract the methodology.** From the extraction dossier and reference skills, identify:

- **Structural patterns:** The 9-section phase file format. The CLAUDE.md vs BUILD_RULES.md split. The build.sh structure. The output manifest.
- **Decision patterns:** How to determine which Martin rules go in the preamble vs CLAUDE.md vs BUILD_RULES.md. How to adapt build.sh commands per platform. How to distribute mechanisms across phases (this is decided by Stage 7, but Stage 10 verifies it).
- **Quality signals:** Internal consistency (no dangling references). Self-containment of phase files. build.sh that actually stops on failure. CLAUDE.md that is genuinely under 500 lines and genuinely useful.
- **Edge cases:** What if Stage 7 produced only 1 phase? What if the platform is `bolt` (no terminal)? What if a mechanism has no page assignment? What if token budget is exceeded?

**Step 3: Build the SKILL.md.** Write the complete skill file following the format in the "Skill Format Requirements" section below.

**Step 4: Self-audit against the 4 Agent-Readiness Criteria** (Nate's Prompt 3):

1. **Trigger Description as Routing Table** -- Does your description contain specific trigger phrases like "output generator", "render output package", "serialize build files", "generate phase files"? Is it specific enough to avoid false matches with Stage 7 (phase sequencing) or Stage 8 (protocol injection)? Does it specify that the skill PRODUCES a deliverable file package?

2. **Output Format Completeness** -- Is every output field completely specified? Can a downstream consumer (the user) receive the output and know exactly what files they have, in what format, and how to use them? Is the `output_manifest` structure exact? Is the `generated_files` structure exact? Is `final_validation` structure exact?

3. **Explicit Edge Case Handling** -- What happens when `stage_7.phases` is empty? When `stage_9.verification_mode` is missing? When a mechanism has no phase assignment? When token budget is exceeded? When the platform is `bolt` and there is no terminal? Are failure modes machine-readable?

4. **Composability** -- Stage 10 is the FINAL stage, so "composability" means: can the output be consumed by a coding agent without human interpretation? Does the output contain ONLY structured deliverables (no conversational text like "Here is your build package")? Can each phase file be consumed independently?

If ANY criterion fails, revise the skill before finalizing.

---

## Skill Format Requirements

### SKILL.md Structure

```markdown
---
name: stage-10-output-generator
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
   - `references/phase-file-template.md` -- The 9-section phase file template with exact structure
   - `references/build-sh-template.md` -- The build.sh template with all sections
   - `references/claude-md-template.md` -- The CLAUDE.md template structure
   - `references/build-rules-template.md` -- The BUILD_RULES.md template with section headers
   - `references/platform-wrappers.md` -- Platform-specific execution instructions for each supported platform

4. **Output must be structured data (JSON or strict Markdown).** No free-form prose in the output section. Every field must have a name, type, and description.

5. **No conversational text in output.** The skill's output is a file package for the end user, not a message for a human. No "Here is your build package:" or "I generated the following files:". The output IS the files.

---

## Context Packet Integration

### Reading Input

Your skill reads from the context packet. Stage 10 reads from MORE stages than any other -- it is the convergence point:

```python
# Pseudocode -- the skill receives the full context_packet JSON
stage_0 = context_packet["stage_0"]   # platform_profile, tech_stack, command_allowlist
stage_3 = context_packet["stage_3"]   # concept_and_context, drift_anchor
stage_4 = context_packet["stage_4"]   # mechanisms
stage_5 = context_packet["stage_5"]   # mechanism_blueprints, build_rules_applied
stage_6 = context_packet["stage_6"]   # sub_6a, sub_6b, sub_6c
stage_7 = context_packet["stage_7"]   # phases, token_budget, mandatory_build_order
stage_8 = context_packet["stage_8"]   # protocol_injected_phases, overhead_breakdown
stage_9 = context_packet["stage_9"]   # verification_mode, two_strike_rule, verification_protocol,
                                      # per_phase_checker_config, agent_b_config
metadata = context_packet["metadata"] # app_type, archetype_matches, confidence_scores
```

Only read from stages BEFORE yours. Stage 10 reads from stages 0, 3, 4, 5, 6, 7, 8, 9, and metadata. It does NOT read from stages 1 or 2 directly (their data has been consumed and transformed by stages 3-9).

### Writing Output

Your skill writes to its own namespace:

```python
context_packet["stage_10"] = {
    "output_manifest": [...],         # array of {file_path, file_type, estimated_tokens}
    "generated_files": {...},         # full file contents keyed by path
    "build_script_config": {
        "snapshot_enabled": True,
        "rollback_enabled": True,
        "forbidden_file_detection": True,
        "two_strike_retry": True,
        "chaining_operator": "&&"
    },
    "platform_target": "claude_cli",  # or other platform enum value
    "claude_md_content": "...",       # full CLAUDE.md string
    "build_rules_content": "...",     # full BUILD_RULES.md string
    "final_validation": {
        "open_questions_count": 0,
        "all_phases_fit_budget": True,
        "all_mechanisms_covered": True,
        "all_pages_covered": True
    }
}
context_packet["metadata"]["current_stage"] = 10
context_packet["metadata"]["status"] = "completed"
context_packet["metadata"]["confidence_scores"]["10"] = {
    "score": total_score,
    "dimensions": {
        "completeness": score_1,
        "accuracy": score_2,
        "consistency": score_3,
        "specificity": score_4,
        "handoff_readiness": score_5
    },
    "gate_result": "pass"  # or "flag" or "fail"
}
context_packet["metadata"]["stage_timestamps"]["10"] = "ISO-8601-timestamp"
context_packet["metadata"]["updated_at"] = "ISO-8601-timestamp"
```

### Validation Before Writing

Before writing output, the skill MUST:
1. Verify all required output fields are populated
2. Verify `final_validation.open_questions_count` == 0
3. Verify `final_validation.all_phases_fit_budget` == true
4. Verify `final_validation.all_mechanisms_covered` == true
5. Verify `final_validation.all_pages_covered` == true
6. Run the confidence scoring
7. If score < 70, trigger escape hatch instead of writing
8. If score 70-89, write but flag in metadata with a warning note documenting weak areas
9. If score >= 90, write normally and set `metadata.status` to `"completed"`

---

## Token Budget

Your skill will run within a Claude Code session with approximately 400,000-450,000 total tokens available (after accounting for system prompts, tools, and the context packet itself).

Budget allocation:
- SKILL.md: ~5,000 tokens (hard limit)
- References (combined): ~20,000 tokens max
- Context packet input: ~50,000-80,000 tokens (Stage 10 receives the FULL packet from all prior stages -- the largest input of any stage)
- Working space for the agent: remaining tokens (~250,000-375,000)

Stage 10's token budget is the most constrained because it reads from the most stages AND produces the most output (the entire file package). Keep your skill lean. Do not repeat information available in the context packet. Reference it by field name instead.

The OUTPUT that Stage 10 produces (the generated files) can be arbitrarily large since it is written to disk, not held in context. The constraint is on the skill instructions and working memory, not the generated artifact size.

---

## Escape Hatch Pattern

Include this in your SKILL.md:

```
When to trigger:
- Any required input namespace is missing entirely (e.g., stage_7 is null)
- stage_7.phases is empty (no phases to render)
- An open question is detected in any phase's feature requirements
- A mechanism from stage_4 has no phase assignment in stage_7
- A page from stage_6.sub_6b has no phase assignment in stage_7
- Token budget exceeded for any phase (stage_7 token estimate + stage_8 overhead > limit)
- Confidence score below 70 after one retry
- Internal consistency check fails (dangling file references, missing sandbox entries)

What to save:
- Current context_packet (with whatever partial output exists)
- Stage number (10) and step where the halt occurred
- List of specific validation failures (which mechanisms are uncovered, which pages are missing, which references dangle)
- Partial generated_files (whatever was rendered before the halt)

How to signal:
- Set metadata.status = "needs_human"
- Add an entry to metadata.escape_hatches array:
  {
    "stage": 10,
    "step": "step_name",
    "reason": "description of failure",
    "details": { ... specific failure data ... },
    "suggested_actions": ["Fix X in Stage Y", "Re-run Stage Z"]
  }
- Save context_packet snapshot to disk
- Output a structured NEEDS_HUMAN message with the specific problem and suggested actions
```

---

## Confidence Gate Pattern

Include this self-scoring process in your SKILL.md:

```
After producing output, score each dimension 0-20:

1. Completeness: Are ALL output files present? Does every phase file
   have all 9 sections? Is build.sh complete with verification and
   retry? Are CLAUDE.md and BUILD_RULES.md present and populated?
   Are any requirement sections thin or skeletal?

2. Accuracy: Does every reference in every file resolve correctly?
   Do build.sh commands match the chosen platform? Do CLAUDE.md rules
   accurately reflect the project architecture? Are there zero
   dangling references to nonexistent files, mechanisms, or patterns?

3. Consistency: Do phase files respect each other's sandbox rules?
   (Phase 2 does not modify files Phase 1's sandbox forbids.)
   Does build.sh verification match phase checkpoint rules?
   Do CLAUDE.md and BUILD_RULES.md complement each other without
   contradiction?

4. Specificity: Are phase requirements detailed enough for a coding
   agent to build without asking questions? Do they specify exact
   file paths, exact exports, exact patterns? Or do they say vague
   things like "build the auth system"?

5. Handoff Readiness: Can a coding agent execute the entire build --
   all phases, in order -- without asking a single question?
   This is the ultimate test. The output package IS the complete
   instruction set. If ANY question would need to be asked, this
   dimension scores below 16.

Total = sum of all 5 dimensions (/100)

>= 90: PASS -- pipeline is complete, deliver the output package
70-89: WARN -- flag low dimensions, deliver with warning note
< 70:  FAIL -- trigger escape hatch, do NOT deliver output
```

Note: For Stage 10, "handoff readiness" means readiness for the END USER (a coding agent or human developer), not readiness for a "next stage" -- there is no next stage.

---

## Output Location

Save the completed skill to:

```
docs/page-prds/prd-maker/skills/stage-10-output-generator/SKILL.md
```

If you need reference files (and you almost certainly will -- the phase file template, build.sh template, CLAUDE.md template, BUILD_RULES.md template, and platform wrapper instructions are all too large to inline), save them to:

```
docs/page-prds/prd-maker/skills/stage-10-output-generator/references/
```

Suggested reference files:
- `references/phase-file-template.md` -- The 9-section phase file template
- `references/build-sh-template.md` -- The build.sh skeleton with all sections
- `references/claude-md-template.md` -- The CLAUDE.md structure
- `references/build-rules-sections.md` -- BUILD_RULES.md section headers and content patterns
- `references/platform-wrappers.md` -- Per-platform execution instructions

Total reference files MUST stay under 20,000 tokens combined.

---

## Agent-Readiness Checklist (Must Pass ALL)

Before finalizing your SKILL.md, verify:

- [ ] **Trigger routing:** The `description` field in YAML frontmatter contains specific trigger phrases ("output generator", "render build files", "serialize phase documents") and specifies that the skill produces a deliverable file package (phase files + build.sh + CLAUDE.md + BUILD_RULES.md + README.md)
- [ ] **Output completeness:** Every output field (`output_manifest`, `generated_files`, `build_script_config`, `platform_target`, `claude_md_content`, `build_rules_content`, `final_validation`) has exact name, type, and description. A downstream consumer can parse the output programmatically with zero guessing.
- [ ] **Edge cases explicit:** Missing input stages, empty phase lists, token budget overflow, platform without terminal, uncovered mechanisms, uncovered pages, dangling references -- all have defined behaviors with machine-readable error responses
- [ ] **Composability:** The output contains ONLY the structured file package. No conversational text, no preamble, no "Here is what I generated." Each phase file is independently consumable. The end user receives files, not a chat message.
- [ ] **Under 500 lines:** The SKILL.md body (excluding frontmatter) is under 500 lines
- [ ] **Single-line description:** The YAML `description` field is exactly one line, under 120 characters
- [ ] **Confidence gate included:** The self-scoring process documents all 5 dimensions with Stage 10-specific criteria (completeness of file package, accuracy of references, consistency across phases, specificity of requirements, handoff readiness for end user)
- [ ] **Escape hatch included:** Trigger conditions (missing stages, empty phases, open questions, uncovered mechanisms, dangling references), save protocol, and signal method are all documented
- [ ] **Example included:** At least one realistic input/output example showing: context packet input (abbreviated) -> rendering process -> output manifest + generated file excerpts
- [ ] **Context packet fields match schema:** Every field read matches `context-packet-schema.md` Section 3 (Stage Read/Write Map, row for Stage 10). Every field written matches Section 2.12 (`stage_10` namespace).
- [ ] **Final validation checks are executable:** The `final_validation` object fields (open_questions_count, all_phases_fit_budget, all_mechanisms_covered, all_pages_covered) are computed from actual data, not assumed to be true
- [ ] **Martin's rules distribution verified:** The skill instructions explicitly state that Martin's rules appear in preambles, architecture decisions, and build order -- NEVER as a standalone "Martin's Rules" section

---

## Success Criteria

- [ ] SKILL.md exists at `docs/page-prds/prd-maker/skills/stage-10-output-generator/SKILL.md`
- [ ] YAML frontmatter has `name: stage-10-output-generator` and single-line `description`
- [ ] SKILL.md body is under 500 lines
- [ ] All sections present: Purpose, When to Use, Input Format, Process, Output Format, Edge Cases, Confidence Scoring, Escape Hatch, Example
- [ ] Passes all 4 agent-readiness criteria (trigger routing, output completeness, edge cases, composability)
- [ ] Context packet fields match the schema document (Section 2.12 for writes, Section 3 Stage Read/Write Map for reads)
- [ ] Contract criteria from `stage-contracts.md` Stage 10 section are achievable by following the skill's process: all 9 phase sections present, self-contained phases, build.sh with snapshot/rollback/retry, CLAUDE.md under 500 lines, internal consistency verified, Martin's rules distributed
- [ ] Reference files (if any) are in the `references/` subfolder and total under 20K tokens combined
- [ ] The skill's process steps cover ALL 8 steps described in this handoff (manifest, phase files, build.sh, CLAUDE.md, BUILD_RULES.md, README.md, platform picker, internal consistency verification)
- [ ] The skill does NOT invent new decisions -- it serializes decisions already made by Stages 0-9. If the skill's process includes any step that requires judgment beyond formatting/rendering, that step belongs in an earlier stage.
