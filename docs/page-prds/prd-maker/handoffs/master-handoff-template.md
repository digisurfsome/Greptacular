# Master Handoff Template — Phase 2 Stage Skill Builds

> **Purpose:** This template defines the PATTERN for creating handoff prompts for Phase 2 agents (one agent per stage skill). Copy this template, fill in the stage-specific sections marked with `{{PLACEHOLDER}}`, and hand it to a fresh agent.
>
> **Usage:** One copy per stage (0-10). Each copy is a complete, self-contained prompt.

---

## TEMPLATE STARTS HERE

---

# Build Stage {{STAGE_NUMBER}} Skill: {{STAGE_NAME}}

> **Type:** Self-contained handoff prompt for a fresh Claude Code agent
> **Output:** `docs/page-prds/prd-maker/skills/stage-{{STAGE_NUMBER_PADDED}}-{{STAGE_SLUG}}/SKILL.md`

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

**You are building Stage {{STAGE_NUMBER}}: {{STAGE_NAME}}.** It reads from stages before it and writes to its own namespace in the context packet.

---

## Your Stage: {{STAGE_NAME}}

### Purpose

{{STAGE_PURPOSE — 2-3 sentences explaining what this stage does and why it matters in the pipeline}}

### Inputs (What This Stage Receives)

{{LIST OF SPECIFIC CONTEXT PACKET FIELDS THIS STAGE READS — from the context-packet-schema.md}}

### Outputs (What This Stage Produces)

{{LIST OF SPECIFIC CONTEXT PACKET FIELDS THIS STAGE WRITES — from the context-packet-schema.md}}

### Process

{{DETAILED DESCRIPTION OF THE STAGE'S LOGIC — from the stage extraction dossier. Include:
- Step-by-step process
- Decision points
- Rules and constraints
- Edge cases}}

### Rules and Constraints

{{SPECIFIC RULES FROM THE STAGE EXTRACTION — things like "preserve contradictions" or "no mechanism decomposition" or "15% threshold rule"}}

---

## Files to Read Before Building

Read ALL of these files completely before writing any skill content:

1. **`docs/page-prds/prd-maker/stage-extractions/stage-{{STAGE_NUMBER_PADDED}}-extraction.md`** — The full extraction dossier for this stage. This is your primary source of truth for what the stage does.

2. **`docs/page-prds/prd-maker/context-packet-schema.md`** — The data schema. Find Stage {{STAGE_NUMBER}}'s namespace. Understand exactly which fields you read and write.

3. **`docs/page-prds/prd-maker/stage-contracts.md`** — Find Stage {{STAGE_NUMBER}}'s contract. Your skill must produce output that meets all "Done When" criteria and passes the confidence scoring.

4. **`docs/page-prds/prd-maker/martin-agnostic-checklist.md`** — The structural checklist. Your skill may need to reference specific rules or inject the checklist as context.

5. **`docs/page-prds/prd-maker/nate-jones-skill-kit.md`** — The skill-building methodology. Your SKILL.md must follow Nate's Prompt 2 output format and pass Nate's Prompt 3 agent-readiness criteria.

6. {{STAGE_SPECIFIC_REFERENCE_FILES — additional files relevant to this specific stage, e.g.:
   - Stage 1: `docs/page-prds/prd-maker/extracted-skills/nicknisi/skills/ideation/SKILL.md`
   - Stage 2: `docs/page-prds/prd-maker/mechanism-identification-framework.md` + `docs/page-prds/prd-maker/app-archetype-library.md`
   - Stage 4: `docs/page-prds/prd-maker/extracted-skills/affaan-m/skills/product-lens.md`
   - Stage 5: `docs/page-prds/prd-maker/extracted-skills/haberlah/SKILL.md`
   - Stage 7: `docs/page-prds/prd-maker/extracted-skills/haberlah/SKILL.md`
   - Stage 8: `docs/page-prds/prd-maker/extracted-skills/affaan-m/commands/verify.md` + `quality-gate.md`
   - Stage 9: `docs/page-prds/prd-maker/extracted-skills/nicknisi/agents/reviewer.md`
   - Stage 10: `docs/page-prds/prd-maker/extracted-skills/nicknisi/references/contract-template.md` + `spec-template.md`
   }}

---

## Skill Building Instructions

You are building a Claude Code skill using the **Nate B. Jones Output-Extraction Method** (Prompt 2). This means you do NOT write a vague process description -- you reverse-engineer what GREAT output looks like and encode that into the skill.

### The Build Process

**Step 1: Understand the output.** Read the stage extraction dossier. Understand what a PERFECT stage output looks like. What fields are populated? What quality level? What format?

**Step 2: Extract the methodology.** From the extraction dossier and reference skills, identify:
- Structural patterns (what sections appear in the output, in what order)
- Decision patterns (what judgment calls are made, what criteria drive them)
- Quality signals (what separates great output from adequate output)
- Edge cases (what happens when input is incomplete, contradictory, or ambiguous)

**Step 3: Build the SKILL.md.** Write the complete skill file following the format below.

**Step 4: Self-audit against the 4 Agent-Readiness Criteria** (Nate's Prompt 3):

1. **Trigger Description as Routing Table** — Does your description contain specific trigger phrases? Is it specific enough to avoid false matches? Does it specify what the skill PRODUCES?

2. **Output Format Completeness** — Is the output format completely specified with exact sections, exact fields, exact structure? Could a downstream agent parse this output programmatically?

3. **Explicit Edge Case Handling** — What happens when required data is missing? When input is ambiguous? When the request is partially out of scope? Are failure modes machine-readable?

4. **Composability** — Could another skill (the next stage) consume this skill's output cleanly? Does output contain ONLY the structured deliverable (no conversational preamble)?

If ANY criterion fails, revise the skill before finalizing.

---

## Skill Format Requirements

### SKILL.md Structure

```markdown
---
name: stage-{{STAGE_NUMBER}}-{{STAGE_SLUG}}
description: {{SINGLE LINE DESCRIPTION — this is a YAML field, multi-line SILENTLY FAILS}}
---

## Purpose

{{1-2 sentences}}

## When to Use

{{Trigger conditions — what input or request activates this skill}}

## Input Format

{{Exact JSON structure this skill expects from the context packet}}

## Process

### Step 1: {{Name}}
{{Detailed instructions with decision criteria}}

### Step 2: {{Name}}
{{...}}

[... as many steps as needed ...]

## Output Format

{{Exact JSON structure this skill writes to the context packet — field names, types, validation rules}}

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

{{One realistic example showing input → process → output for this stage}}
```

### Critical Format Rules

1. **YAML frontmatter `description` MUST be a single line.** Multi-line descriptions silently fail in Claude Code. Keep it under 120 characters.

2. **Total SKILL.md body MUST be under 500 lines / 5,000 tokens.** This is a hard limit from Claude Code's context window management. After compaction, skills are truncated to 5K tokens.

3. **Large reference material goes in a `references/` subfolder**, NOT in the SKILL.md body. Create files like:
   - `references/mechanism-framework.md` — extracted subset of the mechanism framework relevant to this stage
   - `references/checklist-subset.md` — only the Martin checklist rules this stage needs
   - `references/example-output.md` — extended example if the inline example is too large

4. **Output must be structured data (JSON or strict Markdown).** No free-form prose in the output section. Every field must have a name, type, and description.

5. **No conversational text in output.** The skill's output is data for the next stage, not a message for a human. No "Here is what I found:" or "I analyzed the following:".

---

## Context Packet Integration

### Reading Input

Your skill reads from the context packet like this:

```python
# Pseudocode — the skill receives the full context_packet JSON
input_data = context_packet["stage_{{PREVIOUS_STAGE}}"]
metadata = context_packet["metadata"]
```

Only read from stages BEFORE yours. Never read from stages after yours (they do not exist yet).

### Writing Output

Your skill writes to its own namespace:

```python
context_packet["stage_{{STAGE_NUMBER}}"] = {
    # Your output fields here
}
context_packet["metadata"]["current_stage"] = {{STAGE_NUMBER}}
context_packet["metadata"]["confidence_scores"]["{{STAGE_NUMBER}}"] = {
    "score": total_score,
    "dimensions": {
        "completeness": score_1,
        "accuracy": score_2,
        "consistency": score_3,
        "specificity": score_4,
        "handoff_readiness": score_5
    }
}
context_packet["metadata"]["stage_timestamps"]["{{STAGE_NUMBER}}"] = "ISO-8601-timestamp"
```

### Validation Before Writing

Before writing output, the skill MUST:
1. Verify all required output fields are populated
2. Run the confidence scoring
3. If score < 70, trigger escape hatch instead of writing
4. If score 70-89, write but flag in metadata
5. If score >= 90, write normally

---

## Token Budget

Your skill will run within a Claude Code session with approximately 400,000-450,000 total tokens available (after accounting for system prompts, tools, and the context packet itself).

Budget allocation:
- SKILL.md: ~5,000 tokens (hard limit)
- References (combined): ~20,000 tokens max
- Context packet input: ~10,000-50,000 tokens (grows as pipeline progresses)
- Working space for the agent: remaining tokens

Keep your skill lean. Do not repeat information available in the context packet. Reference it by field name instead.

---

## Escape Hatch Pattern

Every stage uses this standard escape hatch. Include it in your SKILL.md:

```
When to trigger:
- Required input fields are missing and cannot be inferred
- Confidence score is below 70 after one retry
- The stage encounters a situation not covered by its rules
- The user's input contradicts itself in a way that cannot be resolved without human input

What to save:
- Current context_packet (with whatever partial output exists)
- Stage number and step where the halt occurred
- What was attempted and what failed
- Suggested questions for the human

How to signal:
- Set metadata.status = "needs_human"
- Add an entry to metadata.escape_hatches array
- Save context_packet snapshot to disk
- Output a structured NEEDS_HUMAN message with the specific problem and suggested actions
```

---

## Confidence Gate Pattern

Include this self-scoring process in your SKILL.md:

```
After producing output, score each dimension 0-20:

1. Completeness: Are ALL required output fields populated with real data (not placeholders)?
2. Accuracy: Does the output correctly reflect the input? No invented information?
3. Consistency: Does the output align with all previous stages? No contradictions?
4. Specificity: Is every field precise enough for the next stage to parse programmatically?
5. Handoff Readiness: Could Stage {{NEXT_STAGE_NUMBER}} start immediately from this output?

Total = sum of all 5 dimensions (/100)

>= 90: PASS — proceed to next stage
70-89: WARN — flag low dimensions, proceed with warning
< 70:  FAIL — trigger escape hatch, do NOT pass output forward
```

---

## Output Location

Save the completed skill to:

```
docs/page-prds/prd-maker/skills/stage-{{STAGE_NUMBER_PADDED}}-{{STAGE_SLUG}}/SKILL.md
```

If you need reference files, save them to:

```
docs/page-prds/prd-maker/skills/stage-{{STAGE_NUMBER_PADDED}}-{{STAGE_SLUG}}/references/
```

---

## Agent-Readiness Checklist (Must Pass ALL)

Before finalizing your SKILL.md, verify:

- [ ] **Trigger routing:** The `description` field in YAML frontmatter contains specific trigger phrases and specifies what the skill produces
- [ ] **Output completeness:** Every output field has a name, type, and description. A downstream agent could parse the output with zero guessing.
- [ ] **Edge cases explicit:** Missing input, ambiguous input, and scope overflow all have defined behaviors with machine-readable responses
- [ ] **Composability:** The output contains ONLY structured data. No conversational text, no preamble, no "Here is what I found." The next stage can consume the output as-is.
- [ ] **Under 500 lines:** The SKILL.md body (excluding frontmatter) is under 500 lines
- [ ] **Single-line description:** The YAML `description` field is exactly one line, under 120 characters
- [ ] **Confidence gate included:** The self-scoring process is documented with all 5 dimensions
- [ ] **Escape hatch included:** The trigger conditions, save protocol, and signal method are documented
- [ ] **Example included:** At least one realistic input/output example is present
- [ ] **Context packet fields match schema:** Every field read/written matches the context-packet-schema.md

---

## Success Criteria

- [ ] SKILL.md exists at the specified output path
- [ ] YAML frontmatter has `name` and single-line `description`
- [ ] SKILL.md body is under 500 lines
- [ ] All sections present: Purpose, When to Use, Input Format, Process, Output Format, Edge Cases, Confidence Scoring, Escape Hatch, Example
- [ ] Passes all 4 agent-readiness criteria (trigger routing, output completeness, edge cases, composability)
- [ ] Context packet fields match the schema document
- [ ] Contract criteria from stage-contracts.md are achievable by following the skill's process
- [ ] Reference files (if any) are in the `references/` subfolder and total under 20K tokens

---

## TEMPLATE ENDS HERE

---

## How to Use This Template

1. Copy everything between "TEMPLATE STARTS HERE" and "TEMPLATE ENDS HERE"
2. Replace all `{{PLACEHOLDER}}` values with stage-specific content
3. The stage extraction dossier (`stage-NN-extraction.md`) is the primary source for filling in the stage-specific sections
4. The context packet schema (`context-packet-schema.md`) provides the exact field names for inputs/outputs
5. The stage contracts (`stage-contracts.md`) provide the "Done When" criteria and confidence rubrics
6. Add stage-specific reference files to the "Files to Read" section based on the mapping in the build-game-plan.md

### Placeholder Reference

| Placeholder | Example (Stage 1) | Where to Find It |
|-------------|-------------------|-------------------|
| `{{STAGE_NUMBER}}` | `1` | Stage extraction filename |
| `{{STAGE_NUMBER_PADDED}}` | `01` | Zero-padded to 2 digits |
| `{{STAGE_NAME}}` | `Idea Capture` | Stage extraction title |
| `{{STAGE_SLUG}}` | `idea-capture` | Kebab-case of stage name |
| `{{STAGE_PURPOSE}}` | From extraction "Purpose" section | Stage extraction dossier |
| `{{PREVIOUS_STAGE}}` | `stage_0` | N-1 |
| `{{NEXT_STAGE_NUMBER}}` | `2` | N+1 |
| `{{STAGE_SPECIFIC_REFERENCE_FILES}}` | See mapping in template | build-game-plan.md "Stage Build Sequence" table |

### Stage-to-Reference-Skill Mapping

| Stage | Key Reference Skills to Include |
|-------|-------------------------------|
| 0 | `rodrigorjsf/commands/prp-prd.md` (Block 5-7 interrogation pattern) |
| 1 | `nicknisi/skills/ideation/SKILL.md` (intake pattern) |
| 2 | `nicknisi/references/confidence-rubric.md` + `mechanism-identification-framework.md` + `app-archetype-library.md` |
| 3 | `rodrigorjsf/commands/prp-prd.md` (context_packet structuring) |
| 4 | `mechanism-identification-framework.md` + `affaan-m/skills/product-lens.md` (ICE scoring) |
| 5 | `haberlah/SKILL.md` (DO NOT CHANGE protection clauses) |
| 6 | `affaan-m/skills/design-system.md` + `affaan-m/skills/frontend-patterns.md` |
| 7 | `haberlah/SKILL.md` (phased prompts) + token budget math from Stage 7 extraction |
| 8 | `affaan-m/commands/verify.md` + `affaan-m/commands/quality-gate.md` |
| 9 | `nicknisi/agents/reviewer.md` + `affaan-m/skills/verification-loop.md` |
| 10 | `nicknisi/references/contract-template.md` + `nicknisi/references/spec-template.md` + `ognjengt/skills/sop-creator/SKILL.md` |
