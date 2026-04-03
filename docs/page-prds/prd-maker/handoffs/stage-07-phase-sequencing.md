# Build Stage 7 Skill: Phase Sequencing

> **Type:** Self-contained handoff prompt for a fresh Claude Code agent
> **Output:** `docs/page-prds/prd-maker/skills/stage-07-phase-sequencing/SKILL.md`

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

**You are building Stage 7: Phase Sequencing.** It reads from stages before it and writes to its own namespace in the context packet.

---

## Your Stage: Phase Sequencing

### Purpose

Takes the complete spec -- mechanisms scaffolded with Wall/Door/Room classifications, wireframes approved, style selected -- and splits it into build phases using math-based token budget calculations. Each phase becomes a self-contained "containment unit" with its own file sandbox, build order, and dependency mapping. Stage 7 does the structural split; Stage 8 then injects enforcement protocols into each phase.

### Inputs (What This Stage Receives)

From the context packet, this stage reads:

- `stage_5.mechanism_blueprints` -- Complete mechanism definitions with Wall/Door/Room classifications and 7-question scaffolding
- `stage_4.mechanisms` -- The discrete mechanism list with OBVIOUS/NEEDS_EVALUATION tags
- `stage_4.mechanism_dependencies` -- Dependency graph between mechanisms
- `stage_6.sub_6a` -- Selected arrangement/wireframe pattern and app type classification
- `stage_6.sub_6b` -- Per-page mockup data (page name, layout, components, mechanism connections)
- `stage_6.sub_6c.design_tokens` -- Applied style set with color palette, typography, spacing
- `stage_3.drift_anchor` -- Product identity and concept document (used to maintain alignment)
- `stage_2.scope_contract` -- Scope boundaries agreed during gap analysis

### Outputs (What This Stage Produces)

Written to `context_packet.stage_7`:

- `token_budget` (object):
  - `total_spec_tokens` (integer) -- estimated total tokens for the full spec content from Stages 3-6
  - `budget_per_phase_content` (integer) -- target ~325,000 tokens per phase for actual build instructions
  - `overhead_per_phase` (integer) -- ~25,000 tokens fixed overhead per phase
  - `total_budget` (integer) -- 500,000 tokens (50% of 1M context)
  - `phases_needed` (integer) -- calculated as total_spec_tokens / budget_per_phase_content, rounded up

- `phases` (array of objects, one per phase):
  - `phase_number` (integer) -- sequential starting at 1
  - `name` (string) -- descriptive name for the phase (e.g., "Auth System", "Dashboard + Features")
  - `mechanism_ids` (array of strings) -- which mechanisms from Stage 4 are included in this phase
  - `estimated_tokens` (integer) -- estimated token count for this phase's build content
  - `build_order` (array of objects):
    - `file_path` (string) -- exact file path to create or modify
    - `operation` (enum) -- "CREATE" | "MODIFY" | "ADD_ROUTE" | "ADD_EXPORT"
    - `rationale` (string) -- why this file is in this position (e.g., "core logic first")
  - `files_allowed` (array of strings) -- files this phase CAN create or modify
  - `files_read_only` (array of strings) -- files this phase can reference but NOT change
  - `files_forbidden` (array of strings) -- everything else, explicitly listed where important
  - `depends_on` (array of integers) -- phase numbers that must complete before this phase starts
  - `do_not_change` (array of strings) -- files that must never be modified by any phase (CLAUDE.md, .env, etc.)

- `mandatory_build_order` (array of strings) -- global constraints that apply across all phases (e.g., "core logic before state", "state before UI", "UI before integration")

### Process

**Step 1: Estimate Total Token Count**

Take the complete Agent OS document (output of Stages 3-6: structured concept, mechanism blueprints with W/D/R classifications, page layouts, design tokens). Estimate the total token count of ALL build content that needs to be conveyed to a coding agent.

**Step 2: Calculate Phase Count**

```
Total budget: 500,000 tokens (50% of 1M context window)
Per-phase overhead: ~25,000 tokens (fixed, templated)
  - Build rules preamble:          ~8,000 tokens
  - File sandbox declaration:      ~2,000 tokens
  - Build order with pulse points: ~3,000 tokens
  - Seam check definitions:        ~2,000 tokens
  - Full checkpoint at end:        ~5,000 tokens
  - Pattern verification prompt:   ~3,000 tokens
  - Violation handling:            ~2,000 tokens

Available per phase for build content: ~325,000 tokens
Target per phase (with buffer): 350,000 tokens total (325K content + 25K overhead)
Phase count = total_spec_tokens / 325,000 (rounded up)
```

**Step 3: Find Natural Break Points**

Divide the mechanism list at boundaries near the mathematical split points. NEVER cut a mechanism in half across phases. If a mechanism sits right at a split boundary, keep the entire mechanism in whichever phase makes it fit better. Prefer keeping tightly-coupled mechanisms together (check `stage_4.mechanism_dependencies`).

**Step 4: Assign File Sandboxes**

For each phase, define three tiers:

- **FILES ALLOWED**: The exact list of files this phase can create or modify. Be explicit -- list every file path.
- **FILES READ-ONLY**: Files the phase can reference for patterns (e.g., "reference auth pattern from api/auth.ts") but must NOT modify.
- **FILES FORBIDDEN**: Everything else. For critical files (CLAUDE.md, .env, build config, existing migration files), list them explicitly in forbidden even though "everything else" covers them.

**Step 5: Define Build Order Per Phase**

Within each phase, define a forced linear sequence following the pattern: core logic --> state management --> UI components --> integration/routing. Every file in the phase's ALLOWED list must appear in the build order. No file gets created or modified out of sequence.

**Step 6: Define Phase Dependencies**

Phase 1 depends on nothing. Phase 2 depends on Phase 1. If phases have independent work (rare), they can run in parallel, but default to sequential. Dependencies must be explicit -- if Phase 3 depends on the auth system from Phase 1 AND the data layer from Phase 2, list both.

**Step 7: Verify Fit**

For each phase, confirm: estimated_tokens + overhead_per_phase <= 350,000 (the 35% context target). If any phase exceeds this, adjust the split point. Move mechanisms to adjacent phases. Do NOT compress content to fit.

### Rules and Constraints

1. **500,000 token total budget.** 50% of the 1M context window. This is a hard ceiling. The other 50% is reserved for the agent's working memory, tools, and system prompts.

2. **~25,000 tokens per-phase overhead is fixed.** It is templated and predictable. Account for it BEFORE splitting, not after.

3. **Target 35% of context = 350,000 tokens per phase** (325,000 content + 25,000 overhead). The gap between 35% target and the theoretical ~47.5% max provides significant headroom. Never push right up to the wall.

4. **Split at mechanism boundaries.** NEVER cut a mechanism in half across phases. A mechanism is atomic -- all its files, logic, state, and UI belong in the same phase.

5. **Every phase must have all three sandbox tiers.** ALLOWED, READ-ONLY, FORBIDDEN. No exceptions. A phase without a sandbox is not a phase.

6. **Build order is mandatory.** No phase ships without a forced linear sequence. The order follows Martin's patterns: core logic --> state --> UI --> integration.

7. **Dependencies between phases must be explicit.** Phase N states exactly what must be complete before it starts. No implicit assumptions.

8. **Stage 7 does rough split; Stage 8 injects protocols; validation confirms fit.** This is a single forward pass, not an iterative loop. If validation fails, adjust the split -- do not re-architect.

9. **The overhead is templated.** The preamble, sandbox format, and checkpoint protocol are reused across all phases with project-specific values swapped in. This is why the overhead is predictable.

10. **DO NOT CHANGE protections.** Certain files must never be modified by any phase (CLAUDE.md, .env, build config, existing migrations). List these globally AND in each phase's forbidden list.

---

## Files to Read Before Building

Read ALL of these files completely before writing any skill content:

1. **`docs/page-prds/prd-maker/stage-extractions/stage-07-extraction.md`** -- The full extraction dossier for this stage. This is your primary source of truth for what the stage does. Contains the token math, file sandbox system, build order system, and worked examples.

2. **`docs/page-prds/prd-maker/context-packet-schema.md`** -- The data schema. Find Stage 7's namespace. Understand exactly which fields you read and write.

3. **`docs/page-prds/prd-maker/stage-contracts.md`** -- Find Stage 7's contract. Your skill must produce output that meets all "Done When" criteria and passes the confidence scoring.

4. **`docs/page-prds/prd-maker/martin-agnostic-checklist.md`** -- The structural checklist. The build order within phases follows Martin's patterns (core logic --> state --> UI --> integration). Understand these patterns so the build order reflects them.

5. **`docs/page-prds/prd-maker/nate-jones-skill-kit.md`** -- The skill-building methodology. Your SKILL.md must follow Nate's Prompt 2 output format and pass Nate's Prompt 3 agent-readiness criteria.

6. **`docs/page-prds/prd-maker/extracted-skills/haberlah/SKILL.md`** -- The haberlah skill reference. Contains phased prompt patterns and token budget calculation patterns that directly inform how Stage 7 structures its output. Pay attention to how phases are defined, how DO NOT CHANGE protections work, and how token budgets are calculated.

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

1. **Trigger Description as Routing Table** -- Does your description contain specific trigger phrases? Is it specific enough to avoid false matches? Does it specify what the skill PRODUCES?

2. **Output Format Completeness** -- Is the output format completely specified with exact sections, exact fields, exact structure? Could a downstream agent parse this output programmatically?

3. **Explicit Edge Case Handling** -- What happens when required data is missing? When input is ambiguous? When the request is partially out of scope? Are failure modes machine-readable?

4. **Composability** -- Could another skill (Stage 8) consume this skill's output cleanly? Does output contain ONLY the structured deliverable (no conversational preamble)?

If ANY criterion fails, revise the skill before finalizing.

---

## Skill Format Requirements

### SKILL.md Structure

```markdown
---
name: stage-07-phase-sequencing
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

{{One realistic example showing input --> process --> output for this stage}}
```

### Critical Format Rules

1. **YAML frontmatter `description` MUST be a single line.** Multi-line descriptions silently fail in Claude Code. Keep it under 120 characters.

2. **Total SKILL.md body MUST be under 500 lines / 5,000 tokens.** This is a hard limit from Claude Code's context window management. After compaction, skills are truncated to 5K tokens.

3. **Large reference material goes in a `references/` subfolder**, NOT in the SKILL.md body. Create files like:
   - `references/token-budget-math.md` -- the full token calculation formulas and worked examples
   - `references/file-sandbox-template.md` -- the three-tier sandbox template with examples
   - `references/build-order-patterns.md` -- Martin's build order patterns (core logic --> state --> UI --> integration) with concrete examples

4. **Output must be structured data (JSON or strict Markdown).** No free-form prose in the output section. Every field must have a name, type, and description.

5. **No conversational text in output.** The skill's output is data for Stage 8, not a message for a human. No "Here is what I found:" or "I analyzed the following:".

---

## Context Packet Integration

### Reading Input

Your skill reads from the context packet like this:

```python
# Pseudocode -- the skill receives the full context_packet JSON
mechanism_blueprints = context_packet["stage_5"]["mechanism_blueprints"]
mechanisms = context_packet["stage_4"]["mechanisms"]
mechanism_dependencies = context_packet["stage_4"]["mechanism_dependencies"]
wireframes = context_packet["stage_6"]["sub_6a"]
page_mockups = context_packet["stage_6"]["sub_6b"]
design_tokens = context_packet["stage_6"]["sub_6c"]["design_tokens"]
drift_anchor = context_packet["stage_3"]["drift_anchor"]
scope_contract = context_packet["stage_2"]["scope_contract"]
metadata = context_packet["metadata"]
```

Only read from stages BEFORE yours. Never read from stages after yours (they do not exist yet).

### Writing Output

Your skill writes to its own namespace:

```python
context_packet["stage_7"] = {
    "token_budget": {
        "total_spec_tokens": int,
        "budget_per_phase_content": 325000,
        "overhead_per_phase": 25000,
        "total_budget": 500000,
        "phases_needed": int
    },
    "phases": [
        {
            "phase_number": int,
            "name": str,
            "mechanism_ids": [str],
            "estimated_tokens": int,
            "build_order": [
                {"file_path": str, "operation": str, "rationale": str}
            ],
            "files_allowed": [str],
            "files_read_only": [str],
            "files_forbidden": [str],
            "depends_on": [int],
            "do_not_change": [str]
        }
    ],
    "mandatory_build_order": [str]
}
context_packet["metadata"]["current_stage"] = 7
context_packet["metadata"]["confidence_scores"]["7"] = {
    "score": total_score,
    "dimensions": {
        "completeness": score_1,
        "accuracy": score_2,
        "consistency": score_3,
        "specificity": score_4,
        "handoff_readiness": score_5
    }
}
context_packet["metadata"]["stage_timestamps"]["7"] = "ISO-8601-timestamp"
```

### Validation Before Writing

Before writing output, the skill MUST:
1. Verify all required output fields are populated
2. Verify no mechanism is split across phases (every mechanism_id appears in exactly one phase)
3. Verify total estimated tokens across all phases <= 500,000
4. Verify each phase's estimated_tokens + overhead_per_phase <= 350,000
5. Verify every file in files_allowed appears in build_order
6. Verify phase dependencies form a DAG (no circular dependencies)
7. Run the confidence scoring
8. If score < 70, trigger escape hatch instead of writing
9. If score 70-89, write but flag in metadata
10. If score >= 90, write normally

---

## Token Budget

Your skill will run within a Claude Code session with approximately 400,000-450,000 total tokens available (after accounting for system prompts, tools, and the context packet itself).

Budget allocation:
- SKILL.md: ~5,000 tokens (hard limit)
- References (combined): ~20,000 tokens max
- Context packet input: ~30,000-50,000 tokens (Stages 0-6 have accumulated significant content by this point)
- Working space for the agent: remaining tokens

Keep your skill lean. Do not repeat information available in the context packet. Reference it by field name instead.

---

## Escape Hatch Pattern

Every stage uses this standard escape hatch. Include it in your SKILL.md:

```
When to trigger:
- Required input fields are missing and cannot be inferred (e.g., no mechanism list from Stage 4)
- Total spec tokens cannot be estimated (Stages 3-6 output is incomplete or empty)
- A mechanism has no clear file mapping (cannot determine which files it needs)
- Mechanism dependencies form a cycle that prevents clean phase splitting
- Confidence score is below 70 after one retry

What to save:
- Current context_packet (with whatever partial phase list exists)
- Stage number (7) and step where the halt occurred
- Which mechanisms were successfully assigned to phases and which were not
- The token budget calculation (even if incomplete)
- Suggested questions for the human (e.g., "Mechanism X has no file mapping -- what files does it need?")

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

1. Completeness (0-20): Are ALL mechanisms assigned to exactly one phase? Do all phases have
   complete sandbox lists and build orders? Is the token budget fully calculated?

2. Accuracy (0-20): Do the token estimates reflect realistic content sizes? Are file paths
   real and correct for the tech stack in stage_0? Do mechanism groupings respect dependencies?

3. Consistency (0-20): Do phase dependencies match mechanism dependencies from Stage 4?
   Do file sandbox lists align with the page layouts from Stage 6? Does the build order
   follow Martin's patterns (core logic --> state --> UI --> integration)?

4. Specificity (0-20): Are file paths exact (not "some auth file" but "src/lib/auth.ts")?
   Are token estimates numbers (not "about 300K")? Are build order rationales concrete?

5. Handoff Readiness (0-20): Could Stage 8 (Protocol Injection) immediately insert pulse
   checks after each build order entry? Is the file sandbox precise enough for git diff
   verification? Are phase boundaries clear enough for checkpoint gates?

Total = sum of all 5 dimensions (/100)

>= 90: PASS -- proceed to Stage 8
70-89: WARN -- flag low dimensions, proceed with warning
< 70:  FAIL -- trigger escape hatch, do NOT pass output forward
```

---

## Output Location

Save the completed skill to:

```
docs/page-prds/prd-maker/skills/stage-07-phase-sequencing/SKILL.md
```

If you need reference files, save them to:

```
docs/page-prds/prd-maker/skills/stage-07-phase-sequencing/references/
```

---

## Agent-Readiness Checklist (Must Pass ALL)

Before finalizing your SKILL.md, verify:

- [ ] **Trigger routing:** The `description` field in YAML frontmatter contains specific trigger phrases and specifies what the skill produces
- [ ] **Output completeness:** Every output field has a name, type, and description. A downstream agent could parse the output with zero guessing.
- [ ] **Edge cases explicit:** Missing input, ambiguous input, and scope overflow all have defined behaviors with machine-readable responses
- [ ] **Composability:** The output contains ONLY structured data. No conversational text, no preamble, no "Here is what I found." Stage 8 can consume the output as-is.
- [ ] **Under 500 lines:** The SKILL.md body (excluding frontmatter) is under 500 lines
- [ ] **Single-line description:** The YAML `description` field is exactly one line, under 120 characters
- [ ] **Confidence gate included:** The self-scoring process is documented with all 5 dimensions
- [ ] **Escape hatch included:** The trigger conditions, save protocol, and signal method are documented
- [ ] **Example included:** At least one realistic input/output example showing a multi-phase split with token math
- [ ] **Context packet fields match schema:** Every field read/written matches the context-packet-schema.md
- [ ] **Token math is correct:** The worked example in the skill demonstrates the formula: phases_needed = total_spec_tokens / 325,000 rounded up, each phase <= 350,000 total
- [ ] **File sandbox has all 3 tiers:** Example output shows ALLOWED, READ-ONLY, and FORBIDDEN lists
- [ ] **Build order follows Martin's pattern:** core logic --> state --> UI --> integration

---

## Success Criteria

- [ ] SKILL.md exists at `docs/page-prds/prd-maker/skills/stage-07-phase-sequencing/SKILL.md`
- [ ] YAML frontmatter has `name` and single-line `description`
- [ ] SKILL.md body is under 500 lines
- [ ] All sections present: Purpose, When to Use, Input Format, Process, Output Format, Edge Cases, Confidence Scoring, Escape Hatch, Example
- [ ] Passes all 4 agent-readiness criteria (trigger routing, output completeness, edge cases, composability)
- [ ] Context packet fields match the schema document
- [ ] Contract criteria from stage-contracts.md are achievable by following the skill's process
- [ ] Reference files (if any) are in the `references/` subfolder and total under 20K tokens
- [ ] Token budget math is explicit with worked example (500K total, 25K overhead, 325K content per phase)
- [ ] File sandbox system has all 3 tiers defined with concrete file path examples
- [ ] Build order within phases follows core logic --> state --> UI --> integration
- [ ] No mechanism is ever split across phases in the example output
- [ ] Phase dependencies form a DAG with no cycles
