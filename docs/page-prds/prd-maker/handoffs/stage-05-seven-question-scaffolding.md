# Build Stage 5 Skill: 7-Question Scaffolding

> **Type:** Self-contained handoff prompt for a fresh Claude Code agent
> **Output:** `docs/page-prds/prd-maker/skills/stage-05-seven-question-scaffolding/SKILL.md`

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
| **5** | **7-Question Scaffolding** | **Classify every process step as WALL / DOOR / ROOM using 7 questions** | **Per-mechanism W/D/R blueprint with verification methods** |
| 6 | Layout + Mockups + Style | Define page layouts, wireframe patterns, and design system | Per-page component specs, style tokens, typography |
| 7 | Phase Sequencing | Split the spec into buildable phases within token budgets | Phase list with token estimates, file sandbox, build order |
| 8 | Protocol Injection | Configure verification system (pulse/seam/full checks) | Check configurations, violation thresholds, escalation rules |
| 9 | Verification Agent Setup | Configure separate checker agent with git diff rules | Checker config, two-strike rule, verification mode |
| 10 | Output Generator | Produce copy-paste-ready build files | Phase files, build script, CLAUDE.md, BUILD_RULES.md |

### How Stages Connect

Every stage reads from the context packet (a JSON object) and writes its output back to the packet. The packet is saved as a snapshot after each stage. If a stage fails, the pipeline rolls back to the previous snapshot and retries or asks a human for help.

**You are building Stage 5: 7-Question Scaffolding.** It reads from stages before it (primarily Stage 4, but also Stages 0-3 for context) and writes to its own namespace (`stage_5`) in the context packet.

---

## Your Stage: 7-Question Scaffolding

### Purpose

Stage 5 is THE CORE IP of the entire pipeline. It takes each mechanism identified in Stage 4 and runs it through a 7-question framework to classify every aspect as WALL (deterministic -- code handles, no AI), DOOR (constrained -- AI operates within strict boundaries), or ROOM (creative freedom -- AI can be flexible). This is "the engine. Everything before it is preparation. Everything after it is output formatting."

Without Stage 5, the PRD describes WHAT but not the mechanical HOW. The build drifts. The AI improvises. You get a toy. Stage 5 exists to prevent that by making every single process step in every mechanism explicit about who controls it (code vs constrained AI vs free AI) and how to verify it was done correctly.

### Inputs (What This Stage Receives)

From `context_packet.stage_4`:

- `mechanisms` (array): The full mechanism list with IDs, names, descriptions, categories, classification (OBVIOUS/NEEDS_EVALUATION), chosen approach, and optional alternate approach
- `mechanism_dependencies` (array): Dependencies between mechanisms (from_id, to_id, relationship)
- `dual_design_count` (integer): Number of mechanisms with alternate approaches (15% rule)

From `context_packet.stage_0`:

- Martin's agnostic build rules (referenced by checklist_rule_ids) -- used as the LENS through which scaffolding decisions are made

From `context_packet.stage_3`:

- `drift_anchor` (string): Canonical product description for scope creep detection

From `context_packet.stage_2`:

- `scope_contract` (string): What IS and IS NOT in scope

### Outputs (What This Stage Produces)

Written to `context_packet.stage_5`:

| Field | Type | Description |
|-------|------|-------------|
| `mechanism_blueprints` | `array` | One blueprint per mechanism (plus alternate if 15% rule applied) |
| `mechanism_blueprints[].mechanism_id` | `string` | References `stage_4.mechanisms[].id` |
| `mechanism_blueprints[].approach` | `string` | Enum: `"primary"`, `"alternate"` |
| `mechanism_blueprints[].phases` | `array` | Grouped steps within this mechanism |
| `mechanism_blueprints[].phases[].phase_label` | `string` | Phase name within the mechanism |
| `mechanism_blueprints[].phases[].entry_condition` | `string` | What must be true to start this phase |
| `mechanism_blueprints[].phases[].exit_condition` | `string` | What must be true to proceed |
| `mechanism_blueprints[].phases[].validation_rules` | `string[]` | How to verify this phase was done correctly |
| `mechanism_blueprints[].phases[].steps` | `array` | Individual steps in this phase |
| `mechanism_blueprints[].phases[].steps[].id` | `string` | Unique step identifier |
| `mechanism_blueprints[].phases[].steps[].name` | `string` | What happens here (Question 1) |
| `mechanism_blueprints[].phases[].steps[].classification` | `string` | Enum: `"WALL"`, `"DOOR"`, `"ROOM"` (Question 2) |
| `mechanism_blueprints[].phases[].steps[].preconditions` | `string[]` | What must be true before this step starts (Question 3) |
| `mechanism_blueprints[].phases[].steps[].outcomes` | `array` | All possible outcomes (Question 4) |
| `mechanism_blueprints[].phases[].steps[].outcomes[].outcome` | `string` | Outcome description |
| `mechanism_blueprints[].phases[].steps[].outcomes[].next_step` | `string` | Where to go next (step ID or `"end"`) (Question 5) |
| `mechanism_blueprints[].phases[].steps[].verification` | `string` | How to verify this step was done correctly (Question 6) |
| `mechanism_blueprints[].phases[].steps[].skip_condition` | `string \| null` | Condition to skip, or null if not skippable (Question 7) |
| `build_rules_applied` | `string[]` | Martin's build rule IDs that shaped the scaffolding |

### The 7 Questions (Exact Framework)

For each step of each mechanism, ask:

1. **WHAT happens here?** (name the action)
2. **Is there ONLY ONE way to do this, or can it vary?**
   - Only one way = WALL (deterministic, code it)
   - Can vary = DOOR or ROOM (AI territory)
3. **What MUST be true before this step can start?** (preconditions -- these are walls that prevent skipping ahead)
4. **What are ALL the possible outcomes of this step?**
   - Can list them ALL = deterministic
   - Infinite/unpredictable = AI territory
5. **For each outcome: where do you go next?** (draws the arrows between rooms)
6. **How do you VERIFY this step was done correctly?** (validation -- the wall you bounce off if you try to cheat)
7. **Can this step be skipped? Ever? Under any circumstance?**
   - No = WALL
   - Yes, if [condition] = DOOR with a lock

### Classification Rules (How Answers Map to WALL/DOOR/ROOM)

**WALL (Deterministic):** Code handles these. AI never touches them.
- Must happen exactly this way, no variation
- Possible answers are from a fixed list
- Order follows a set sequence
- Results recorded in structured format
- Cannot be skipped
- Verification is machine-checkable (file exists, function exports X, response matches schema)

**DOOR (Constrained AI):** AI operates but within strict rules.
- Can rephrase but MUST contain the core requirement
- Must pick from valid options ONLY
- Can ask follow-up but ONLY to clarify the same topic, cannot drift
- Has boundaries that cannot be crossed
- Every DOOR step must have explicit `constraints` in the blueprint

**ROOM (Open Floor / Free AI):** AI can be creative.
- Small talk, rapport building
- Explaining results in accessible language
- Generating summaries
- Any output where the format/content is genuinely unpredictable

### Where Martin's Rules Fit

Martin's 1,500 lines of build rules are NOT injected at Stage 8 or 9. They are the LENS through which Stage 5 operates.

"The architect follows building code WHILE designing." The rules shape scaffolding answers: when the system asks "what are the walls of this mechanism?" Martin's rules inform the answer -- the wall is clean, it does not leak state, it has a single responsibility, imports flow downward.

Specifically:
- Single responsibility per step (each step does exactly one thing)
- No state leakage between phases (entry/exit conditions enforce isolation)
- Data access through service layer (wall that prevents components from calling DB directly)
- Validation at boundaries (every step has verification)
- Separation of concerns (UI steps separate from data steps separate from logic steps)

Record which build rule IDs influenced each scaffolding decision in `build_rules_applied`.

### The 15% Dual-Design Rule

When Stage 4 flags two approaches scoring within 15% of each other, BOTH approaches get full scaffolding through Stage 5. Both get their own complete blueprint. Stage 5 does not pick winners -- it scaffolds whatever Stage 4 gives it. The branch test happens during the actual build phase.

### Process

1. Read all mechanisms from `stage_4.mechanisms`
2. For each mechanism:
   a. Identify its chosen approach (and alternate if 15% rule applied)
   b. Map the process as a human would do it -- walk through EXACTLY what happens step by step
   c. Group steps into phases with clear entry/exit conditions
   d. Apply the 7 questions to every step within every phase
   e. Classify each step as WALL, DOOR, or ROOM based on the answers
   f. For each WALL: define machine-checkable validation
   g. For each DOOR: define explicit constraints (boundaries the AI cannot cross)
   h. For each ROOM: define topic boundaries (what the room is about, even if execution is free)
   i. Verify entry/exit conditions chain correctly across phases
3. Apply Martin's build rules as a lens throughout -- every scaffolding decision reflects structural principles
4. If a mechanism has an alternate approach, repeat steps 2a-2i for the alternate
5. Compile `build_rules_applied` list
6. Run confidence scoring

### Rules and Constraints

1. **Every mechanism gets scaffolded.** No mechanism is skipped. No "TBD" or "UNCLEAR" classifications.
2. **Every step gets all 7 questions answered.** No question is blank or "N/A" without explicit justification.
3. **WALL validations must be machine-checkable.** "Check it works" is not acceptable. "Function exports loginUser and signupUser" is.
4. **DOOR constraints must be specific.** "Stay on topic" is not acceptable. "Must ask about {context} using one of these 3 question patterns, cannot introduce new topics, must use language from the user's own words" is.
5. **Entry/exit conditions must chain.** Phase 2's entry condition must match Phase 1's exit condition. No gaps.
6. **Mechanisms that are 100% ROOM are valid** -- but the 7 questions must still be asked to confirm there truly are no walls.
7. **Martin's rules are the lens, not the output.** Do not include Martin's rules verbatim in the blueprint. The blueprint reflects his principles structurally.
8. **Cross-mechanism dependencies from Stage 4 must be reflected in entry conditions.** If mechanism B depends on mechanism A, mechanism B's first phase entry condition must reference mechanism A's completion.
9. **Scope check:** Before scaffolding each mechanism, verify it is within the `scope_contract` from Stage 2 and consistent with the `drift_anchor` from Stage 3. If a mechanism seems to exceed scope, flag it but still scaffold it -- scope enforcement is not Stage 5's job.

---

## Files to Read Before Building

Read ALL of these files completely before writing any skill content:

1. **`docs/page-prds/prd-maker/stage-extractions/stage-05-extraction.md`** -- The full extraction dossier for Stage 5. This is your primary source of truth for what the stage does. Contains the 7 questions, classification rules, the 3-step prompting process, code examples, the practitioner template, and the Era 7 room prompt template.

2. **`docs/page-prds/prd-maker/context-packet-schema.md`** -- The data schema. Find Stage 5's namespace (section 2.7). Understand exactly which fields you read from Stage 4 (section 2.6) and write to Stage 5.

3. **`docs/page-prds/prd-maker/stage-contracts.md`** -- Find Stage 5's contract. Your skill must produce output that meets all "Done When" criteria and passes the confidence scoring. Pay special attention to the scoring rubric for Accuracy (classifications must be obviously correct) and Specificity (steps detailed enough to write code from).

4. **`docs/page-prds/prd-maker/martin-agnostic-checklist.md`** -- The structural checklist. Stage 5 uses this as the LENS for scaffolding decisions. Understand the rules well enough to cite them by ID in `build_rules_applied`.

5. **`docs/page-prds/prd-maker/nate-jones-skill-kit.md`** -- The skill-building methodology. Your SKILL.md must follow Nate's Prompt 2 output format and pass Nate's Prompt 3 agent-readiness criteria.

6. **`docs/page-prds/prd-maker/extracted-skills/haberlah/SKILL.md`** -- The Replit PRD Generator skill. Study its phased prompt structure and DO NOT CHANGE protection clauses. Stage 5 uses a similar phased approach (phases within mechanisms) and the DO NOT CHANGE pattern is directly relevant to WALL classification.

---

## Skill Building Instructions

You are building a Claude Code skill using the **Nate B. Jones Output-Extraction Method** (Prompt 2). This means you do NOT write a vague process description -- you reverse-engineer what GREAT output looks like and encode that into the skill.

### The Build Process

**Step 1: Understand the output.** Read the stage extraction dossier. Understand what a PERFECT stage output looks like. A perfect Stage 5 output has:
- One blueprint per mechanism (two for dual-design), with no mechanism left unscaffolded
- Phases with chaining entry/exit conditions (Phase 2 entry matches Phase 1 exit)
- Every step classified WALL/DOOR/ROOM with all 7 questions answered
- WALL validations that are machine-checkable (grep, file exists, function exports X)
- DOOR constraints that are specific and bounded (not "be appropriate")
- Build rules cited by ID showing which structural principles shaped each decision

**Step 2: Extract the methodology.** From the extraction dossier and haberlah reference skill, identify:
- Structural patterns: How blueprints are organized (mechanism > phases > steps), what fields are always present
- Decision patterns: The 7 questions AS the decision framework. Question 2 is the primary classifier. Questions 3-7 refine and verify.
- Quality signals: Machine-checkable WALL validations separate great from adequate. Specific DOOR constraints separate great from adequate. Chaining entry/exit conditions separate great from adequate.
- Edge cases: Mechanisms that are 100% ROOM. Dual-design mechanisms needing two blueprints. Cross-mechanism dependencies affecting entry conditions.

**Step 3: Build the SKILL.md.** Write the complete skill file following the format in the "Skill Format Requirements" section below.

**Step 4: Self-audit against the 4 Agent-Readiness Criteria** (Nate's Prompt 3):

1. **Trigger Description as Routing Table** -- Does your description contain specific trigger phrases like "7-question", "wall/door/room", "scaffolding", "classification"? Is it specific enough to avoid false matches with Stage 4 (mechanism extraction) or Stage 8 (protocol injection)? Does it specify that the skill PRODUCES mechanism blueprints with W/D/R classifications?

2. **Output Format Completeness** -- Is the output format completely specified with exact fields matching the context packet schema (section 2.7)? Could Stage 6 parse this output programmatically to determine what components go on which pages?

3. **Explicit Edge Case Handling** -- What happens when a mechanism from Stage 4 has a vague description? When a step could reasonably be classified as either DOOR or WALL? When a mechanism is 100% ROOM? When dual-design produces divergent blueprints?

4. **Composability** -- Could Stage 6 consume this output cleanly to determine page layouts? Does the output contain ONLY the structured blueprint data (no conversational preamble)?

If ANY criterion fails, revise the skill before finalizing.

---

## Skill Format Requirements

### SKILL.md Structure

```markdown
---
name: stage-05-seven-question-scaffolding
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

{{One realistic example showing input (one mechanism) -> 7 questions applied -> output (one blueprint with phases and steps)}}
```

### Critical Format Rules

1. **YAML frontmatter `description` MUST be a single line.** Multi-line descriptions silently fail in Claude Code. Keep it under 120 characters.

2. **Total SKILL.md body MUST be under 500 lines / 5,000 tokens.** This is a hard limit from Claude Code's context window management. After compaction, skills are truncated to 5K tokens.

3. **Large reference material goes in a `references/` subfolder**, NOT in the SKILL.md body. Create files like:
   - `references/seven-questions-framework.md` -- The 7 questions with classification rules and examples
   - `references/checklist-lens-rules.md` -- The specific Martin checklist rules most relevant to scaffolding
   - `references/example-blueprint.md` -- Extended example if the inline example is too large
   - `references/classification-decision-tree.md` -- Decision tree for WALL vs DOOR vs ROOM when borderline

4. **Output must be structured data (JSON or strict Markdown).** No free-form prose in the output section. Every field must have a name, type, and description.

5. **No conversational text in output.** The skill's output is data for the next stage, not a message for a human. No "Here is what I found:" or "I analyzed the following:".

---

## Context Packet Integration

### Reading Input

Your skill reads from the context packet like this:

```python
# Pseudocode -- the skill receives the full context_packet JSON
mechanisms = context_packet["stage_4"]["mechanisms"]
mechanism_dependencies = context_packet["stage_4"]["mechanism_dependencies"]
dual_design_count = context_packet["stage_4"]["dual_design_count"]
drift_anchor = context_packet["stage_3"]["drift_anchor"]
scope_contract = context_packet["stage_2"]["scope_contract"]
checklist_rule_ids = context_packet["stage_0"]  # Martin's rules as lens
```

Only read from stages BEFORE yours. Never read from stages after yours (they do not exist yet).

### Writing Output

Your skill writes to its own namespace:

```python
context_packet["stage_5"] = {
    "mechanism_blueprints": [...],  # One per mechanism (plus alternates)
    "build_rules_applied": [...]    # Martin's rule IDs that shaped scaffolding
}
context_packet["metadata"]["current_stage"] = 5
context_packet["metadata"]["confidence_scores"]["5"] = {
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
context_packet["metadata"]["stage_timestamps"]["5"] = "ISO-8601-timestamp"
```

### Validation Before Writing

Before writing output, the skill MUST:
1. Verify every mechanism from Stage 4 has a corresponding blueprint (no mechanism skipped)
2. Verify every dual-design mechanism has TWO blueprints (one per approach)
3. Verify every step has a classification of "WALL", "DOOR", or "ROOM" (no unclassified steps)
4. Verify every step has all 7 questions answered (no blank answers)
5. Verify every WALL step has a machine-checkable validation
6. Verify every DOOR step has explicit constraints
7. Verify entry/exit conditions chain across phases within each blueprint
8. Run the confidence scoring
9. If score < 70, trigger escape hatch instead of writing
10. If score 70-89, write but flag in metadata
11. If score >= 90, write normally

---

## Token Budget

Your skill will run within a Claude Code session with approximately 400,000-450,000 total tokens available (after accounting for system prompts, tools, and the context packet itself).

Budget allocation:
- SKILL.md: ~5,000 tokens (hard limit)
- References (combined): ~20,000 tokens max
- Context packet input: ~10,000-50,000 tokens (grows as pipeline progresses -- by Stage 5, expect ~30,000-40,000 tokens of prior stage data)
- Working space for the agent: remaining tokens

Keep your skill lean. Do not repeat information available in the context packet. Reference it by field name instead.

Stage 5 is the most compute-intensive stage in the pipeline because it must process every mechanism through 7 questions. For apps with 15+ mechanisms, this can consume significant working space. The skill should process mechanisms sequentially, writing each blueprint before moving to the next, to avoid accumulating too much intermediate state.

---

## Escape Hatch Pattern

Include this in your SKILL.md:

```
When to trigger:
- Required input fields are missing (no mechanisms from Stage 4)
- A mechanism's description is so vague that the 7 questions cannot produce meaningful answers
- Confidence score is below 70 after one retry
- A mechanism appears to be fundamentally outside the scope contract but was not caught by Stage 4
- Cross-mechanism dependencies create circular scaffolding (Phase A needs Phase B's output,
  but Phase B needs Phase A's output)

What to save:
- Current context_packet with whatever partial blueprints exist
- Stage number (5) and which mechanism was being scaffolded when the halt occurred
- List of mechanisms already scaffolded vs remaining
- What was attempted and what failed
- Suggested questions for the human (e.g., "Mechanism X's description is too vague.
  Can you describe the step-by-step process a human would follow to do this manually?")

How to signal:
- Set metadata.status = "needs_human"
- Add an entry to metadata.escape_hatches array with stage=5, mechanism_id, reason
- Save context_packet snapshot to disk
- Output a structured NEEDS_HUMAN message with the specific problem and suggested actions
```

---

## Confidence Gate Pattern

Include this self-scoring process in your SKILL.md:

```
After producing output, score each dimension 0-20:

1. Completeness: Are ALL mechanisms scaffolded? Do ALL steps have classifications?
   Do ALL 7 questions have answers? Do dual-design mechanisms have both blueprints?
2. Accuracy: Are classifications obviously correct? (Auth validation = WALL, not ROOM.
   Creative summary generation = ROOM, not WALL.) No misclassifications?
3. Consistency: Do blueprints align with Stage 4 mechanism descriptions?
   Do entry/exit conditions chain correctly? Do cross-mechanism dependencies
   show up in entry conditions?
4. Specificity: Are WALL validations machine-checkable? Are DOOR constraints
   specific and bounded? Are steps detailed enough to write code from?
5. Handoff Readiness: Could Stage 6 deterministically arrange pages from these
   blueprints? Is every mechanism's UI surface clear? Are connections between
   mechanisms' rooms explicit?

Total = sum of all 5 dimensions (/100)

>= 90: PASS -- proceed to Stage 6
70-89: WARN -- flag low dimensions, proceed with warning
< 70:  FAIL -- trigger escape hatch, do NOT pass output forward
```

---

## Output Location

Save the completed skill to:

```
docs/page-prds/prd-maker/skills/stage-05-seven-question-scaffolding/SKILL.md
```

If you need reference files, save them to:

```
docs/page-prds/prd-maker/skills/stage-05-seven-question-scaffolding/references/
```

---

## Agent-Readiness Checklist (Must Pass ALL)

Before finalizing your SKILL.md, verify:

- [ ] **Trigger routing:** The `description` field in YAML frontmatter contains specific trigger phrases ("7-question", "wall/door/room", "scaffolding", "classification", "mechanism blueprint") and specifies what the skill produces (per-mechanism W/D/R blueprints with verification methods)
- [ ] **Output completeness:** Every output field has a name, type, and description matching context-packet-schema.md section 2.7. Stage 6 could parse the output programmatically to determine page components and connections.
- [ ] **Edge cases explicit:** Missing mechanisms, vague descriptions, 100%-ROOM mechanisms, dual-design divergence, circular dependencies, borderline WALL/DOOR classification -- all have defined behaviors with machine-readable responses
- [ ] **Composability:** The output contains ONLY structured blueprint data. No conversational text, no preamble. Stage 6 can consume the output as-is to arrange page layouts.
- [ ] **Under 500 lines:** The SKILL.md body (excluding frontmatter) is under 500 lines
- [ ] **Single-line description:** The YAML `description` field is exactly one line, under 120 characters
- [ ] **Confidence gate included:** The self-scoring process is documented with all 5 dimensions (completeness, accuracy, consistency, specificity, handoff readiness)
- [ ] **Escape hatch included:** Trigger conditions (missing input, vague mechanisms, low confidence, circular dependencies), save protocol, and NEEDS_HUMAN signal method are documented
- [ ] **Example included:** At least one realistic example showing one mechanism run through all 7 questions, classified, and output as a blueprint with phases, steps, and chaining conditions
- [ ] **Context packet fields match schema:** Every field read (stage_4.mechanisms, stage_4.mechanism_dependencies, etc.) and written (stage_5.mechanism_blueprints, stage_5.build_rules_applied) matches context-packet-schema.md
- [ ] **Martin's rules integrated as lens:** The skill documents how build rules shape scaffolding decisions (not injected later) and records rule IDs in build_rules_applied

---

## Success Criteria

- [ ] SKILL.md exists at `docs/page-prds/prd-maker/skills/stage-05-seven-question-scaffolding/SKILL.md`
- [ ] YAML frontmatter has `name` and single-line `description`
- [ ] SKILL.md body is under 500 lines
- [ ] All sections present: Purpose, When to Use, Input Format, Process, Output Format, Edge Cases, Confidence Scoring, Escape Hatch, Example
- [ ] Passes all 4 agent-readiness criteria (trigger routing, output completeness, edge cases, composability)
- [ ] Context packet fields match the schema document (section 2.7 for writes, section 2.6 for reads)
- [ ] Stage 5 contract criteria from stage-contracts.md are achievable by following the skill's process (all 8 "Done When" criteria)
- [ ] Reference files (if any) are in the `references/` subfolder and total under 20K tokens
- [ ] The 7 questions are encoded as the decision framework, not just listed -- the skill must show HOW each question's answer maps to a classification
- [ ] The classification decision tree is unambiguous: given any step, the 7 questions produce exactly one of WALL/DOOR/ROOM
- [ ] Martin's build rules are used as a lens (shaping scaffolding answers) not as injected content
- [ ] Dual-design handling is documented: mechanisms with alternate approaches get two full blueprints
