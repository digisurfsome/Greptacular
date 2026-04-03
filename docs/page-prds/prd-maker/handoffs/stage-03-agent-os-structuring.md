# Build Stage 3 Skill: Agent OS Structuring

> **Type:** Self-contained handoff prompt for a fresh Claude Code agent
> **Output:** `docs/page-prds/prd-maker/skills/stage-03-agent-os-structuring/SKILL.md`

---

## System Overview: The 10-Stage PRD Maker Pipeline

You are building one skill for a 10-stage pipeline that transforms a non-coder's messy app description into a complete, buildable technical specification. Each stage is a separate Claude Code skill. The stages run in sequence, passing a JSON data object (the "context packet") from one to the next.

### The Pipeline at a Glance

| Stage | Name | Purpose | Key Output |
|-------|------|---------|------------|
| 0 | Technical Foundation | Establish platform context (framework, DB, auth, hosting) before any idea-specific work | Platform profile + agnostic checklist reference |
| 1 | Idea Capture | Capture the user's raw brain dump with zero filtering or structure | Raw text, preserved contradictions, word count |
| 2 | Gap Analysis | Match to archetype, identify missing mechanism categories (A-N), ask targeted questions | Complete mechanism map, archetype match, gap answers |
| **3** | **Agent OS Structuring** | **Transform messy raw material into organized concept document** | **Product identity, problem statement, target users, feasibility** |
| 4 | Mechanism Extraction | Break structured app into discrete moving parts tagged OBVIOUS or NEEDS_EVALUATION | Mechanism list with dependencies and evaluation tags |
| 5 | 7-Question Scaffolding | Classify every process step as WALL (deterministic) / DOOR (constrained AI) / ROOM (creative) | Per-mechanism W/D/R classification with verification methods |
| 6 | Layout + Mockups + Style | Define page layouts, wireframe patterns, and design system | Per-page component specs, style tokens, typography |
| 7 | Phase Sequencing | Split the spec into buildable phases within token budgets | Phase list with token estimates, file sandbox, build order |
| 8 | Protocol Injection | Configure verification system (pulse/seam/full checks) | Check configurations, violation thresholds, escalation rules |
| 9 | Verification Agent Setup | Configure separate checker agent with git diff rules | Checker config, two-strike rule, verification mode |
| 10 | Output Generator | Produce copy-paste-ready build files | Phase files, build script, CLAUDE.md, BUILD_RULES.md |

### How Stages Connect

Every stage reads from the context packet (a JSON object) and writes its output back to the packet. The packet is saved as a snapshot after each stage. If a stage fails, the pipeline rolls back to the previous snapshot and retries or asks a human for help.

**You are building Stage 3: Agent OS Structuring.** It reads from stages before it and writes to its own namespace in the context packet.

---

## Your Stage: Agent OS Structuring

### Purpose

Stage 3 takes the complete raw information produced by Stage 1 (Idea Capture) and Stage 2 (Gap Analysis) combined and FORMATS it into organized sections. It transforms messy human language into a structured concept document. The explicit analogy: "raw clay into a shaped block. Not the sculpture yet."

This is the normalization step. It does NOT break the idea into mechanisms (Stage 4's job). It does NOT evaluate approaches or apply scaffolding. It strictly organizes and structures the gap-filled concept so downstream stages can process it cleanly.

The framework originates from a 15-year software veteran (the user's mentor) who reported that when he started putting ideas into this framework, his builds went from a day and a half down to half a day, with significantly fewer bugs. It functions as a "guardrailing system" -- adding walls and doors that help the agent center itself on the concept and context if it starts to drift during building.

### Inputs (What This Stage Receives)

From `context_packet.stage_2`:

- `combined_raw` (string): Stage 1 raw_input + all gap answers merged into one text blob. Complete but still unstructured. This is the PRIMARY input.
- `archetype_matches` (array): Matched app archetypes with confidence scores. Use for framing context.
- `mechanisms_identified` (array): A-N mechanism categories found in the raw input. Use for ensuring nothing is dropped.
- `checklist_coverage` (object): Coverage of the 30-category master checklist. Use for completeness awareness.
- `scope_contract` (string): Summary of what IS and IS NOT in scope.

From `context_packet.stage_1`:

- `explicit_corrections` (array): Contradictions the user stated and then corrected. Use for ambiguity resolution (later corrections override earlier statements).

From `context_packet.stage_0`:

- `platform_profile` (object): Selected boilerplate configuration. Use for technical framing context.

From `context_packet.metadata`:

- `app_type` (string): "greenfield" or "existing" -- affects framing.

### Outputs (What This Stage Produces)

Written to `context_packet.stage_3`:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `concept_and_context` | `object` | Yes | Product identity |
| `concept_and_context.product_name` | `string` | Yes | Chosen product name |
| `concept_and_context.one_line_description` | `string` | Yes | Single-sentence product description |
| `concept_and_context.product_identity` | `string` | Yes | Detailed product identity paragraph |
| `concept_and_context.core_value_proposition` | `string` | Yes | What makes this product valuable |
| `target_user_and_market` | `object` | Yes | Who it is for |
| `target_user_and_market.personas` | `array` | Yes | Target user personas |
| `target_user_and_market.personas[].name` | `string` | Yes | Persona label (e.g., "Busy Professional") |
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
| `feasibility_assessment.risks[].severity` | `string` | Yes | Enum: "low", "medium", "high" |
| `feasibility_assessment.risks[].mitigation` | `string` | Yes | How to mitigate |
| `problem_statement` | `string` | Yes | Clear statement of the problem being solved |
| `ambiguity_resolutions` | `array` | No | Ambiguities found in raw input and how they were resolved |
| `ambiguity_resolutions[].ambiguity` | `string` | Yes | What was ambiguous |
| `ambiguity_resolutions[].resolution` | `string` | Yes | How it was resolved |
| `ambiguity_resolutions[].source` | `string` | Yes | What information the resolution was based on |
| `drift_anchor` | `string` | Yes | Canonical product description used as reference point to detect scope creep in all later stages |

### Process

#### Step 1: Ingest and Inventory the Raw Material

Read `stage_2.combined_raw` in full. Also read `stage_1.explicit_corrections` for known contradictions. Before any structuring, make a mental inventory:

- What product is being described?
- Who is it for?
- What problem does it solve?
- What market context is mentioned?
- What has the user explicitly corrected or contradicted?

Do NOT skip any information. Every piece of the combined raw material must appear in the structured output.

#### Step 2: Apply the Agent OS Framework

Structure the raw material through five lenses:

1. **What is the product?** -- Name it. Define it in one sentence. Describe its identity.
2. **What is it solving?** -- Identify the pain point. State it from the user's perspective.
3. **Market feasibility** -- Is this viable? What exists already? What are the risks?
4. **Who is it for?** -- Define specific personas with pain points and goals.
5. **What exists already?** -- Map the competitive landscape.

These five lenses map to the four output sections: Concept & Context, Target User & Market, Feasibility Assessment, and Problem Statement.

#### Step 3: Resolve Ambiguities

Unstructured ideas contain overlapping concepts that look like separate things but are not (or vice versa). Identify and resolve these:

- **Later statements override earlier ones** -- if the user said "it's for enterprises" then later said "actually it's for freelancers," the resolution is "freelancers."
- **Reference `explicit_corrections` from Stage 1** -- these are already-identified contradictions.
- **Merge duplicate concepts** -- if the user described the same feature two different ways, unify them.
- **Separate bundled concepts** -- if the user lumped two distinct things together, acknowledge both but keep them logically separate.

Log every resolution in `ambiguity_resolutions` with what was ambiguous, how it was resolved, and what information drove the resolution.

If an ambiguity CANNOT be resolved without asking the user, do NOT guess. Flag it in the output and note the specific question that needs answering.

#### Step 4: Structure into Four Sections

Write each section as organized, readable prose -- not stream-of-consciousness:

1. **Concept & Context** (`concept_and_context`): Product name, one-line description, identity paragraph, core value proposition. A stranger should be able to read this section and immediately understand what is being built.

2. **Target User & Market** (`target_user_and_market`): Concrete personas (not "users" but specific types of people), their pain points, their goals. Market context. Known competitors with differentiators.

3. **Feasibility Assessment** (`feasibility_assessment`): Is this viable? What are the technical and market risks? How severe are they? What mitigations exist?

4. **Problem Statement** (`problem_statement`): A clear, user-centric statement of the problem. Not the solution, not the features -- the PAIN.

#### Step 5: Create the Drift Anchor

Write a single, canonical product description (2-4 sentences) that captures the ESSENCE of the product. This is the `drift_anchor`. It serves as the persistent reference point throughout the entire build process. When a building agent starts to wander from the original concept, the drift anchor is what it uses to re-center.

The drift anchor must be:
- Specific enough to detect scope creep (if someone adds a feature not covered by the anchor, it is flagged)
- General enough to not block legitimate feature decisions
- Written in plain language a non-coder can read

#### Step 6: Validate Completeness

Before writing output, verify:
- Every piece of information from `combined_raw` appears in at least one section
- All `mechanisms_identified` from Stage 2 are represented in the structured output (referenced, not decomposed)
- All gap answers from Stage 2 are incorporated
- No information was invented -- only organize, do not add
- The output contains ONLY "what" and "why" -- zero "how"

### Rules and Constraints

1. **No mechanism extraction in this stage.** Stage 3 structures; Stage 4 extracts. If you find yourself listing discrete moving parts (auth system, payment flow, notification engine) and classifying them, you have crossed into Stage 4. Mention features in context but do not decompose them.

2. **No "how" -- only "what" and "why."** The structured document describes what the product does and why it matters. Technical implementation approaches, architecture decisions, and technology choices are deferred to later stages.

3. **Must resolve ambiguity.** Overlapping concepts, duplicate descriptions, contradictory statements -- all must be resolved or explicitly flagged. Stage 4 depends on clean, unambiguous input.

4. **The structured output serves as a persistent drift anchor.** This document is not consumed and discarded. It remains available throughout the entire build as a reference for re-centering when agents drift.

5. **Must incorporate ALL gap-filled information.** Everything from Stage 2's combined_raw must appear in the structured output. If a gap was identified and answered, it must be woven into the appropriate section.

6. **Format must be standardized.** The four-section Agent OS format is a consistent structure that downstream stages expect. Stage 4 (Mechanism Extraction) depends on receiving input in this standardized format.

7. **The structuring reduces and organizes but does not add.** Stage 3 is a normalization step, not a creative step. It organizes what exists from Stages 1+2. It does not generate new ideas, features, or assumptions.

---

## Files to Read Before Building

Read ALL of these files completely before writing any skill content:

1. **`docs/page-prds/prd-maker/stage-extractions/stage-03-extraction.md`** -- The full extraction dossier for Stage 3. This is your primary source of truth for what the stage does. Contains the Agent OS origin story, the 3-layer format, the funnel metaphor, and the boundary between Stage 3 and Stage 4.

2. **`docs/page-prds/prd-maker/context-packet-schema.md`** -- The data schema. Find Stage 3's namespace (section 2.5). Understand exactly which fields you read and write. Pay special attention to the `drift_anchor` field and the `ambiguity_resolutions` array.

3. **`docs/page-prds/prd-maker/stage-contracts.md`** -- Find Stage 3's contract. Your skill must produce output that meets all "Done When" criteria and passes the confidence scoring. The six completion criteria and the five confidence dimensions with their rubrics are your quality bar.

4. **`docs/page-prds/prd-maker/martin-agnostic-checklist.md`** -- The structural checklist. Stage 3 does not apply the checklist directly, but the Agent OS format itself was derived from the mentor's (Martin's) systematic thinking. Understanding the checklist provides context for what kind of structural rigor the pipeline expects.

5. **`docs/page-prds/prd-maker/nate-jones-skill-kit.md`** -- The skill-building methodology. Your SKILL.md must follow Nate's Prompt 2 output format and pass Nate's Prompt 3 agent-readiness criteria.

6. **`docs/page-prds/prd-maker/extracted-skills/affaan-m/commands/prp-prd.md`** -- The PRD generator command from the affaan-m skill set. Study its context_packet structuring pattern, specifically how it organizes problem statements, user personas, market context, and feasibility into structured sections. This is the closest reference skill to what Stage 3 produces. Focus on Phase 2 (Foundation), Phase 4 (Deep Dive), and Phase 7 (Generate) for the structuring patterns.

---

## Skill Building Instructions

You are building a Claude Code skill using the **Nate B. Jones Output-Extraction Method** (Prompt 2). This means you do NOT write a vague process description -- you reverse-engineer what GREAT output looks like and encode that into the skill.

### The Build Process

**Step 1: Understand the output.** Read the stage extraction dossier. Understand what a PERFECT stage output looks like. What fields are populated? What quality level? What format? For Stage 3, perfect output is a four-section structured concept document that a stranger could read and fully understand the product being built -- its identity, its users, its market, its problem, its risks -- without any ambiguity or mechanism decomposition.

**Step 2: Extract the methodology.** From the extraction dossier and reference skills, identify:
- Structural patterns (what sections appear in the output, in what order)
- Decision patterns (what judgment calls are made, what criteria drive them)
- Quality signals (what separates great output from adequate output)
- Edge cases (what happens when input is incomplete, contradictory, or ambiguous)

**Step 3: Build the SKILL.md.** Write the complete skill file following the format below.

**Step 4: Self-audit against the 4 Agent-Readiness Criteria** (Nate's Prompt 3):

1. **Trigger Description as Routing Table** -- Does your description contain specific trigger phrases? Is it specific enough to avoid false matches? Does it specify what the skill PRODUCES?

2. **Output Format Completeness** -- Is the output format completely specified with exact sections, exact fields, exact structure? Could a downstream agent parse this output programmatically?

3. **Explicit Edge Case Handling** -- What happens when required data is missing? When input is ambiguous? When the request is partially out of scope? Are failure modes machine-readable?

4. **Composability** -- Could another skill (the next stage) consume this skill's output cleanly? Does output contain ONLY the structured deliverable (no conversational preamble)?

If ANY criterion fails, revise the skill before finalizing.

---

## Skill Format Requirements

### SKILL.md Structure

```markdown
---
name: stage-03-agent-os-structuring
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
   - `references/agent-os-framework.md` -- the five lenses and their mapping to output sections
   - `references/ambiguity-resolution-rules.md` -- rules for handling contradictions, duplicates, and gaps
   - `references/example-output.md` -- extended example if the inline example is too large

4. **Output must be structured data (JSON or strict Markdown).** No free-form prose in the output section. Every field must have a name, type, and description.

5. **No conversational text in output.** The skill's output is data for the next stage, not a message for a human. No "Here is what I found:" or "I analyzed the following:".

---

## Context Packet Integration

### Reading Input

Your skill reads from the context packet like this:

```python
# Pseudocode -- the skill receives the full context_packet JSON
stage_2 = context_packet["stage_2"]
combined_raw = stage_2["combined_raw"]
archetype_matches = stage_2["archetype_matches"]
mechanisms_identified = stage_2["mechanisms_identified"]
checklist_coverage = stage_2["checklist_coverage"]
scope_contract = stage_2["scope_contract"]

stage_1 = context_packet["stage_1"]
explicit_corrections = stage_1.get("explicit_corrections", [])

stage_0 = context_packet["stage_0"]
platform_profile = stage_0["platform_profile"]

metadata = context_packet["metadata"]
app_type = metadata["app_type"]
```

Only read from stages BEFORE yours. Never read from stages after yours (they do not exist yet).

### Writing Output

Your skill writes to its own namespace:

```python
context_packet["stage_3"] = {
    "concept_and_context": {
        "product_name": "...",
        "one_line_description": "...",
        "product_identity": "...",
        "core_value_proposition": "..."
    },
    "target_user_and_market": {
        "personas": [...],
        "market_context": "...",
        "competitive_landscape": [...]
    },
    "feasibility_assessment": {
        "viability_summary": "...",
        "risks": [...]
    },
    "problem_statement": "...",
    "ambiguity_resolutions": [...],
    "drift_anchor": "..."
}
context_packet["metadata"]["current_stage"] = 3
context_packet["metadata"]["confidence_scores"]["3"] = {
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
context_packet["metadata"]["stage_timestamps"]["3"] = "ISO-8601-timestamp"
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
  (e.g., combined_raw is empty or under 20 words)
- Confidence score is below 70 after one retry
- Ambiguity that cannot be resolved without human input
  (contradictions with no later correction, concepts that could mean two entirely different things)
- The raw material describes something so vague that even the product name cannot be determined

What to save:
- Current context_packet (with whatever partial output exists)
- Stage number (3) and step where the halt occurred
- What was attempted and what failed
- Suggested questions for the human
  (e.g., "The input mentions both a B2B and B2C market. Which is your primary target?")

How to signal:
- Set metadata.status = "needs_human"
- Add an entry to metadata.escape_hatches array:
  {
    "stage": 3,
    "step": "ambiguity_resolution",
    "reason": "...",
    "suggested_questions": ["..."],
    "partial_output": { ... }
  }
- Save context_packet snapshot to disk
- Output a structured NEEDS_HUMAN message with the specific problem and suggested actions
```

---

## Confidence Gate Pattern

Include this self-scoring process in your SKILL.md:

```
After producing output, score each dimension 0-20:

1. Completeness: Are ALL four sections populated with substantive content (50+ words each)?
   Does every piece of information from combined_raw appear in at least one section?
2. Accuracy: Does the output faithfully represent the user's idea? No invented features?
   No assumptions beyond what was stated?
3. Consistency: Do the four sections align with each other? Does the problem statement
   match the personas? Do the risks align with the market context? Are ambiguity
   resolutions logged and consistent?
4. Specificity: Is every field precise enough that two different readers would draw the
   same conclusions about what is being built? Are personas concrete (not "users")?
5. Handoff Readiness: Could Stage 4 (Mechanism Extraction) extract every mechanism from
   this document without ambiguity? Are overlapping concepts resolved? Are feature
   boundaries clear enough for clean extraction?

Total = sum of all 5 dimensions (/100)

>= 90: PASS -- proceed to next stage
70-89: WARN -- flag low dimensions, proceed with warning
< 70:  FAIL -- trigger escape hatch, do NOT pass output forward
```

---

## Output Location

Save the completed skill to:

```
docs/page-prds/prd-maker/skills/stage-03-agent-os-structuring/SKILL.md
```

If you need reference files, save them to:

```
docs/page-prds/prd-maker/skills/stage-03-agent-os-structuring/references/
```

---

## Agent-Readiness Checklist (Must Pass ALL)

Before finalizing your SKILL.md, verify:

- [ ] **Trigger routing:** The `description` field in YAML frontmatter contains specific trigger phrases and specifies what the skill produces (a structured concept document with product identity, personas, feasibility, and problem statement)
- [ ] **Output completeness:** Every output field has a name, type, and description. A downstream agent could parse the output with zero guessing. The four sections are fully specified.
- [ ] **Edge cases explicit:** Missing input (empty combined_raw), ambiguous input (unresolvable contradictions), and scope overflow (discovering mechanism-level details that belong to Stage 4) all have defined behaviors with machine-readable responses
- [ ] **Composability:** The output contains ONLY structured data. No conversational text, no preamble, no "Here is what I found." Stage 4 can consume the output as-is to begin mechanism extraction.
- [ ] **Under 500 lines:** The SKILL.md body (excluding frontmatter) is under 500 lines
- [ ] **Single-line description:** The YAML `description` field is exactly one line, under 120 characters
- [ ] **Confidence gate included:** The self-scoring process is documented with all 5 dimensions tailored to Stage 3's actual outputs
- [ ] **Escape hatch included:** The trigger conditions (missing combined_raw, unresolvable ambiguity, score < 70), save protocol, and signal method are documented
- [ ] **Example included:** At least one realistic input/output example showing a raw app description structured into the four-section format
- [ ] **Context packet fields match schema:** Every field read/written matches the context-packet-schema.md (section 2.5 for outputs, sections 2.3-2.4 for inputs)

---

## Success Criteria

- [ ] SKILL.md exists at `docs/page-prds/prd-maker/skills/stage-03-agent-os-structuring/SKILL.md`
- [ ] YAML frontmatter has `name: stage-03-agent-os-structuring` and single-line `description`
- [ ] SKILL.md body is under 500 lines
- [ ] All sections present: Purpose, When to Use, Input Format, Process, Output Format, Edge Cases, Confidence Scoring, Escape Hatch, Example
- [ ] Passes all 4 agent-readiness criteria (trigger routing, output completeness, edge cases, composability)
- [ ] Context packet fields match the schema document (section 2.5)
- [ ] Contract criteria from stage-contracts.md (Stage 3 section) are achievable by following the skill's process -- specifically: all four sections with 50+ words each, no mechanism decomposition, all ambiguities resolved or flagged, readable organized prose
- [ ] Reference files (if any) are in the `references/` subfolder and total under 20K tokens
- [ ] The skill enforces the "what and why, not how" boundary -- no mechanism extraction, no technical implementation details
- [ ] The drift_anchor field is produced with clear rules for what makes a good anchor (specific enough for scope creep detection, general enough for legitimate decisions)
