# Build Stage 4 Skill: Mechanism Extraction

> **Type:** Self-contained handoff prompt for a fresh Claude Code agent
> **Output:** `docs/page-prds/prd-maker/skills/stage-04-mechanism-extraction/SKILL.md`

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
| **4** | **Mechanism Extraction** | **Break structured app into discrete moving parts tagged OBVIOUS or NEEDS_EVALUATION** | **Mechanism list with dependencies and evaluation tags** |
| 5 | 7-Question Scaffolding | Classify every process step as WALL (deterministic) / DOOR (constrained AI) / ROOM (creative) | Per-mechanism W/D/R classification with verification methods |
| 6 | Layout + Mockups + Style | Define page layouts, wireframe patterns, and design system | Per-page component specs, style tokens, typography |
| 7 | Phase Sequencing | Split the spec into buildable phases within token budgets | Phase list with token estimates, file sandbox, build order |
| 8 | Protocol Injection | Configure verification system (pulse/seam/full checks) | Check configurations, violation thresholds, escalation rules |
| 9 | Verification Agent Setup | Configure separate checker agent with git diff rules | Checker config, two-strike rule, verification mode |
| 10 | Output Generator | Produce copy-paste-ready build files | Phase files, build script, CLAUDE.md, BUILD_RULES.md |

### How Stages Connect

Every stage reads from the context packet (a JSON object) and writes its output back to the packet. The packet is saved as a snapshot after each stage. If a stage fails, the pipeline rolls back to the previous snapshot and retries or asks a human for help.

**You are building Stage 4: Mechanism Extraction.** It reads from stages before it and writes to its own namespace in the context packet.

---

## Your Stage: Mechanism Extraction

### Purpose

Stage 4 breaks the structured app description from Stage 3 into its discrete moving parts -- individual mechanisms, features, and components. Each mechanism is tagged as OBVIOUS (one clear implementation path) or NEEDS_EVALUATION (multiple viable approaches). This stage includes a 10-step criteria evaluation for NEEDS_EVALUATION mechanisms, with the 15% threshold rule and Developer's Choice routing.

Without mechanism extraction, the PRD describes WHAT the app does but not the mechanical HOW. The build drifts. The AI improvises. You get a toy. The source states this directly: "THIS IS THE STAGE THAT WAS MISSING FROM YOUR PIPELINE."

### Inputs (What This Stage Receives)

From `context_packet.stage_3`:

- `concept_and_context` (object): Product identity -- name, description, identity paragraph, core value proposition. Provides the framing for what mechanisms to extract.
- `target_user_and_market` (object): Personas and market context. Informs which mechanisms are core vs. supporting.
- `problem_statement` (string): What pain the product solves. Helps identify the core mechanism.
- `drift_anchor` (string): Canonical product description. Used to detect scope creep during extraction -- if a mechanism does not relate to the drift anchor, it should not be extracted.

From `context_packet.stage_2`:

- `mechanisms_identified` (array): A-N mechanism categories already found in the raw input. Cross-reference to ensure nothing is missed.
- `scope_contract` (string): Summary of what IS and IS NOT in scope. Mechanisms outside scope should not be extracted.

From `context_packet.stage_0`:

- `platform_profile` (object): Stack context. Used to determine which mechanisms are OBVIOUS because the boilerplate handles them natively.

### Outputs (What This Stage Produces)

Written to `context_packet.stage_4`:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mechanisms` | `array` | Yes | List of extracted mechanisms |
| `mechanisms[].id` | `string` | Yes | Unique identifier (e.g., "mech_001") |
| `mechanisms[].name` | `string` | Yes | Descriptive label (e.g., "Auth System", "Payment Flow") |
| `mechanisms[].description` | `string` | Yes | What this mechanism does (2-5 sentences) |
| `mechanisms[].category_ids` | `string[]` | Yes | Maps to A-N categories (e.g., ["E", "F"]) |
| `mechanisms[].classification` | `string` | Yes | Enum: "OBVIOUS", "NEEDS_EVALUATION" |
| `mechanisms[].is_core_mechanism` | `boolean` | Yes | True if this is the one thing that makes the app special |
| `mechanisms[].chosen_approach` | `object` | Yes | The selected implementation approach |
| `mechanisms[].chosen_approach.name` | `string` | Yes | Approach name |
| `mechanisms[].chosen_approach.description` | `string` | Yes | How it works |
| `mechanisms[].chosen_approach.rationale` | `string` | Yes | Why it was chosen |
| `mechanisms[].alternate_approach` | `object` | No | Second approach if within 15% score parity |
| `mechanisms[].alternate_approach.name` | `string` | Yes | Approach name |
| `mechanisms[].alternate_approach.description` | `string` | Yes | How it works |
| `mechanisms[].alternate_approach.score_delta` | `number` | Yes | Score difference from chosen (0-15) |
| `mechanisms[].evaluation` | `object` | No | Present only if classification is "NEEDS_EVALUATION" |
| `mechanisms[].evaluation.approaches` | `array` | Yes | Competing approaches evaluated |
| `mechanisms[].evaluation.approaches[].name` | `string` | Yes | Approach name |
| `mechanisms[].evaluation.approaches[].score` | `number` | Yes | Evaluation score 0-100 |
| `mechanisms[].evaluation.approaches[].pros` | `string[]` | Yes | Advantages |
| `mechanisms[].evaluation.approaches[].cons` | `string[]` | Yes | Disadvantages |
| `mechanisms[].evaluation.criteria` | `string[]` | Yes | The 10-step criteria used for evaluation |
| `mechanism_dependencies` | `array` | Yes | Dependencies between mechanisms |
| `mechanism_dependencies[].from_id` | `string` | Yes | Mechanism ID that depends on another |
| `mechanism_dependencies[].to_id` | `string` | Yes | Mechanism ID that is depended upon |
| `mechanism_dependencies[].relationship` | `string` | Yes | Nature of dependency (e.g., "requires", "uses_output_of", "shares_data_with") |
| `mechanism_count` | `integer` | Yes | Total number of mechanisms extracted |
| `dual_design_count` | `integer` | Yes | Number of mechanisms with alternate approaches (15% rule) |

### Process

#### Step 1: Read the Structured Concept Document

Read all four sections of the Stage 3 output: `concept_and_context`, `target_user_and_market`, `feasibility_assessment`, and `problem_statement`. Also read the `drift_anchor`.

Understand the FULL product before extracting any mechanisms. Do not start extracting until you can answer:
- What is this product?
- Who is it for?
- What is the core value proposition?
- What problem does it solve?

#### Step 2: Identify Every Discrete Mechanism

A mechanism is a **functional unit with its own internal logic, its own inputs and outputs, and its own set of decisions about how to implement it.** It is NOT a single button, a single database column, or a single CSS class (too small). It is NOT "the whole dashboard" if the dashboard contains multiple independent functional areas (too big).

**Right-sized mechanisms**: Auth system, payment flow, video generation engine, template library, notification engine, credit system, search engine, admin panel, settings page, dashboard widgets, data import/export.

Scan the structured concept for every distinct functional area. Use the A-N mechanism categories from `stage_2.mechanisms_identified` as a cross-reference to ensure nothing is missed.

For each identified mechanism:
- Give it a unique ID (e.g., "mech_001", "mech_auth", "mech_payment")
- Name it descriptively
- Write a 2-5 sentence description of what it does
- Map it to one or more A-N categories
- Check: is this in scope per the `scope_contract`? If not, do not extract it.
- Check: does this relate to the `drift_anchor`? If not, flag for scope creep.

#### Step 3: Match Against Known Patterns

Most mechanisms in most apps are standard patterns. Before treating anything as novel, check if it matches a known pattern:

- **Auth** -- login, signup, password reset, session management = standard pattern
- **CRUD operations** -- create, read, update, delete for any entity = standard pattern
- **Dashboard** -- sidebar + content + widgets = standard pattern
- **Settings page** -- key-value preferences = standard pattern
- **Admin panel** -- user management, permissions = standard pattern
- **Search** -- text search, filters, sorting = standard pattern
- **Notifications** -- in-app, email, push = standard pattern

If a mechanism matches a known pattern, it is likely OBVIOUS. If it does something novel or has multiple viable implementation paths, it is likely NEEDS_EVALUATION.

#### Step 4: Classify Each Mechanism

Tag every mechanism as OBVIOUS or NEEDS_EVALUATION:

- **OBVIOUS** -- One clear way to build it. The boilerplate or standard pattern handles it. No evaluation needed.
- **NEEDS_EVALUATION** -- Multiple approaches exist. Must go through the 10-step criteria evaluation.

Reference `stage_0.platform_profile` to identify mechanisms the boilerplate handles natively (e.g., if the boilerplate includes Supabase Auth, then auth is OBVIOUS).

#### Step 5: Run 10-Step Criteria Evaluation for NEEDS_EVALUATION Mechanisms

For each NEEDS_EVALUATION mechanism, evaluate from an engineer's perspective:

1. **Technical Complexity** -- How hard is each approach to implement?
2. **Scalability** -- How well does each approach handle growth?
3. **Maintainability** -- How easy is each approach to maintain over time?
4. **Performance** -- What are the performance characteristics?
5. **Security** -- What are the security implications?
6. **User Experience** -- How does each approach affect the end user?
7. **Cost** -- What are the infrastructure/service costs?
8. **Time to Implement** -- How long does each approach take?
9. **Ecosystem Fit** -- How well does each approach integrate with the chosen stack?
10. **Future Flexibility** -- How well does each approach accommodate future changes?

Score each approach 0-100. List pros and cons for each.

#### Step 6: Apply Developer's Choice Routing

**Developer's Choice is the default.** When one approach clearly wins (scores highest with >15% margin), select it automatically. This is the "92% route" -- the engineer-recommended approach that works the vast majority of the time.

The user can override with "go with developer's choice on all of it" to accept the top-scoring approach for every mechanism without review.

#### Step 7: Apply the 15% Threshold Rule

If two approaches score within 15% of each other, BOTH get designed. The rationale: "What if you come across something on the first one unforeseen? You already have the designs made for the second one."

For mechanisms within the 15% threshold:
- Record both approaches as `chosen_approach` and `alternate_approach`
- Set `alternate_approach.score_delta` to the actual difference
- Both approaches will be scaffolded in Stage 5
- Both can be built on separate git branches and tested

#### Step 8: Identify the Core Mechanism

Exactly one mechanism should be marked as `is_core_mechanism: true`. This is the one thing that makes the app worth using -- the mechanism that, if removed, means "you don't even have anything to sell."

The core mechanism:
- Directly addresses the `problem_statement`
- Embodies the `core_value_proposition`
- Is what the user would describe when asked "what does your app DO?"
- Gets built first in Phase Sequencing (Stage 7)

#### Step 9: Map Dependencies

Identify dependencies between mechanisms:
- Which mechanisms require other mechanisms to function? (e.g., payment requires auth)
- Which mechanisms share data? (e.g., dashboard reads from analytics engine)
- Which mechanisms produce output that another consumes?

Record each dependency with `from_id`, `to_id`, and `relationship`. Verify the dependency graph is a **directed acyclic graph (DAG)** -- no circular dependencies. If a circular dependency is detected, one of the two mechanisms needs to be restructured.

#### Step 10: Validate and Count

Before writing output:
- Verify `mechanism_count` >= 3 (any real app has at least 3 discrete mechanisms)
- Verify every REQUIRED category from `stage_2.mechanisms_identified` has at least one mechanism
- Verify exactly one mechanism has `is_core_mechanism: true`
- Verify all NEEDS_EVALUATION mechanisms have at least 2 approaches with scores
- Verify dependency graph is acyclic
- Count mechanisms with alternate approaches and set `dual_design_count`

### Rules and Constraints

1. **Extraction cannot happen before structuring.** The structured concept from Stage 3 must exist first. Unstructured ideas have overlapping concepts that look like separate things but are not (or vice versa).

2. **Every moving part must be identified.** Nothing can be left implicit. If a mechanism is missed at this stage, it will not get scaffolded in Stage 5, will not appear in wireframes in Stage 6, and will be improvised by the builder agent.

3. **Mechanisms must be discrete.** Each mechanism is a self-contained unit. If two things are entangled, separate them. If two things that look separate are actually the same mechanism, merge them.

4. **Tag every mechanism.** Every single mechanism must receive either OBVIOUS or NEEDS_EVALUATION. No mechanism can proceed untagged.

5. **Match against known patterns first.** Auth, CRUD, dashboard, settings = standard. Treat these as OBVIOUS unless the app's version is genuinely novel.

6. **The 15% rule for evaluation.** If two approaches score within 15% of each other, design both. Do not force a single choice when the data does not clearly favor one.

7. **Developer's Choice is the default.** 92% of the time, the engineer-recommended approach is the right one. Do not create unnecessary decision points for the user.

8. **Martin's 13 modules inform extraction.** When auth is identified as a mechanism, Martin's auth module provides the pattern knowledge. When CRUD is identified, Martin's CRUD module informs the standard pattern. These modules are a knowledge base REFERENCED by extraction, not a layer.

9. **No scaffolding in this stage.** Stage 4 identifies WHAT the mechanisms are. Stage 5 defines HOW each mechanism works internally (walls/doors/rooms). The boundary: "what are the parts?" = Stage 4. "How does each part work mechanically?" = Stage 5.

10. **Scope creep detection.** Every extracted mechanism must relate to the `drift_anchor` and fall within the `scope_contract`. If a mechanism emerges that was not anticipated, flag it rather than silently including it.

---

## Files to Read Before Building

Read ALL of these files completely before writing any skill content:

1. **`docs/page-prds/prd-maker/stage-extractions/stage-04-extraction.md`** -- The full extraction dossier for Stage 4. This is your primary source of truth. Contains the three driving questions, the tagging system, mechanism examples from VidAi / PRD Maker / Practitioner Bot, the 15% rule discussion, granularity guidance, and the boundary with Stage 5.

2. **`docs/page-prds/prd-maker/context-packet-schema.md`** -- The data schema. Find Stage 4's namespace (section 2.6). Understand exactly which fields you read and write. Pay special attention to the mechanism object structure, evaluation sub-objects, and dependency array format.

3. **`docs/page-prds/prd-maker/stage-contracts.md`** -- Find Stage 4's contract. Your skill must produce output that meets all "Done When" criteria and passes the confidence scoring. The seven completion criteria and the five confidence dimensions with rubrics are your quality bar.

4. **`docs/page-prds/prd-maker/mechanism-identification-framework.md`** -- The "Periodic Table of App Mechanisms." Categories A through N with sub-types and sub-questions. This is the primary reference for identifying and classifying mechanisms. Your skill must cross-reference extracted mechanisms against these categories.

5. **`docs/page-prds/prd-maker/nate-jones-skill-kit.md`** -- The skill-building methodology. Your SKILL.md must follow Nate's Prompt 2 output format and pass Nate's Prompt 3 agent-readiness criteria.

6. **`docs/page-prds/prd-maker/extracted-skills/affaan-m/skills/product-lens.md`** -- The Product Lens skill from the affaan-m skill set. Study Mode 4 (Feature Prioritization) for the ICE scoring pattern (Impact x Confidence / Effort). This informs how the 10-step criteria evaluation scores competing approaches. Also study Mode 1 (Product Diagnostic) for identifying the core mechanism ("What's the MVP? Smallest thing that proves the thesis").

---

## Skill Building Instructions

You are building a Claude Code skill using the **Nate B. Jones Output-Extraction Method** (Prompt 2). This means you do NOT write a vague process description -- you reverse-engineer what GREAT output looks like and encode that into the skill.

### The Build Process

**Step 1: Understand the output.** Read the stage extraction dossier. Understand what a PERFECT stage output looks like. For Stage 4, perfect output is a complete list of discrete mechanisms with zero gaps, each properly tagged, the core mechanism identified, NEEDS_EVALUATION mechanisms evaluated with scored approaches, dependencies mapped as an acyclic graph, and the 15% rule correctly applied.

**Step 2: Extract the methodology.** From the extraction dossier and reference skills, identify:
- Structural patterns (mechanism object structure, evaluation sub-structure, dependency format)
- Decision patterns (OBVIOUS vs NEEDS_EVALUATION classification criteria, 15% threshold math, core mechanism identification)
- Quality signals (proper granularity, complete category coverage, acyclic dependencies, no hallucinated mechanisms)
- Edge cases (mechanisms too vague to classify, app with only 1-2 mechanisms, circular dependencies, all mechanisms being OBVIOUS)

**Step 3: Build the SKILL.md.** Write the complete skill file following the format below.

**Step 4: Self-audit against the 4 Agent-Readiness Criteria** (Nate's Prompt 3):

1. **Trigger Description as Routing Table** -- Does your description contain specific trigger phrases? Is it specific enough to avoid false matches? Does it specify what the skill PRODUCES?

2. **Output Format Completeness** -- Is the output format completely specified with exact sections, exact fields, exact structure? Could a downstream agent parse this output programmatically?

3. **Explicit Edge Case Handling** -- What happens when required data is missing? When a mechanism resists classification? When the app has circular dependencies? When all mechanisms are OBVIOUS? Are failure modes machine-readable?

4. **Composability** -- Could another skill (Stage 5) consume this skill's output cleanly? Does output contain ONLY the structured deliverable? Can Stage 5 immediately apply the 7-question framework to every mechanism?

If ANY criterion fails, revise the skill before finalizing.

---

## Skill Format Requirements

### SKILL.md Structure

```markdown
---
name: stage-04-mechanism-extraction
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
   - `references/mechanism-categories-summary.md` -- condensed version of the A-N framework relevant to extraction
   - `references/10-step-evaluation-criteria.md` -- full evaluation criteria with scoring guidance
   - `references/known-patterns-library.md` -- standard patterns (auth, CRUD, dashboard, etc.) for quick OBVIOUS matching
   - `references/example-output.md` -- extended example if the inline example is too large

4. **Output must be structured data (JSON or strict Markdown).** No free-form prose in the output section. Every field must have a name, type, and description.

5. **No conversational text in output.** The skill's output is data for the next stage, not a message for a human. No "Here is what I found:" or "I analyzed the following:".

---

## Context Packet Integration

### Reading Input

Your skill reads from the context packet like this:

```python
# Pseudocode -- the skill receives the full context_packet JSON
stage_3 = context_packet["stage_3"]
concept_and_context = stage_3["concept_and_context"]
target_user_and_market = stage_3["target_user_and_market"]
problem_statement = stage_3["problem_statement"]
drift_anchor = stage_3["drift_anchor"]

stage_2 = context_packet["stage_2"]
mechanisms_identified = stage_2["mechanisms_identified"]
scope_contract = stage_2["scope_contract"]

stage_0 = context_packet["stage_0"]
platform_profile = stage_0["platform_profile"]

metadata = context_packet["metadata"]
```

Only read from stages BEFORE yours. Never read from stages after yours (they do not exist yet).

### Writing Output

Your skill writes to its own namespace:

```python
context_packet["stage_4"] = {
    "mechanisms": [
        {
            "id": "mech_001",
            "name": "Auth System",
            "description": "Handles user registration, login, password reset, and session management.",
            "category_ids": ["E"],
            "classification": "OBVIOUS",
            "is_core_mechanism": False,
            "chosen_approach": {
                "name": "Supabase Auth",
                "description": "Leverage built-in Supabase Auth for all auth flows.",
                "rationale": "Native to the boilerplate. Zero custom code needed."
            },
            "alternate_approach": None,
            "evaluation": None
        },
        {
            "id": "mech_002",
            "name": "Video Generation Engine",
            "description": "Generates AI video from user prompts via fal.ai API...",
            "category_ids": ["C", "G"],
            "classification": "NEEDS_EVALUATION",
            "is_core_mechanism": True,
            "chosen_approach": { ... },
            "alternate_approach": { ... },  # if within 15%
            "evaluation": {
                "approaches": [ ... ],
                "criteria": [ ... ]
            }
        }
    ],
    "mechanism_dependencies": [
        {
            "from_id": "mech_002",
            "to_id": "mech_001",
            "relationship": "requires"
        }
    ],
    "mechanism_count": 8,
    "dual_design_count": 1
}
context_packet["metadata"]["current_stage"] = 4
context_packet["metadata"]["confidence_scores"]["4"] = {
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
context_packet["metadata"]["stage_timestamps"]["4"] = "ISO-8601-timestamp"
```

### Validation Before Writing

Before writing output, the skill MUST:
1. Verify all required output fields are populated
2. Verify mechanism_count >= 3
3. Verify exactly one mechanism has is_core_mechanism = true
4. Verify dependency graph is acyclic (no circular dependencies)
5. Run the confidence scoring
6. If score < 70, trigger escape hatch instead of writing
7. If score 70-89, write but flag in metadata
8. If score >= 90, write normally

---

## Token Budget

Your skill will run within a Claude Code session with approximately 400,000-450,000 total tokens available (after accounting for system prompts, tools, and the context packet itself).

Budget allocation:
- SKILL.md: ~5,000 tokens (hard limit)
- References (combined): ~20,000 tokens max
- Context packet input: ~10,000-50,000 tokens (grows as pipeline progresses; by Stage 4, stages 0-3 are populated)
- Working space for the agent: remaining tokens

Keep your skill lean. Do not repeat information available in the context packet. Reference it by field name instead. Move the A-N mechanism category details and the 10-step evaluation criteria to reference files.

---

## Escape Hatch Pattern

Every stage uses this standard escape hatch. Include it in your SKILL.md:

```
When to trigger:
- Required input fields are missing (concept_and_context is empty or malformed)
- A mechanism is too vague to classify as OBVIOUS or NEEDS_EVALUATION after examining
  all available context (the structured concept does not provide enough detail)
- Circular dependencies detected that cannot be resolved by restructuring mechanisms
- The app described has fewer than 3 identifiable mechanisms (may indicate Stage 3
  output was too abstract or the app is not complex enough for this pipeline)
- Confidence score is below 70 after one retry
- A mechanism emerges that is outside scope_contract and drift_anchor but appears
  critical -- the system cannot decide whether to include it without human input

What to save:
- Current context_packet (with whatever partial mechanism list exists)
- Stage number (4) and step where the halt occurred
- Which mechanisms were successfully extracted before the halt
- What was attempted and what failed
- Suggested questions for the human
  (e.g., "Is video generation the core mechanism, or is the script engine more important?")
  (e.g., "The concept mentions both a marketplace and a tool -- are these separate products?")

How to signal:
- Set metadata.status = "needs_human"
- Add an entry to metadata.escape_hatches array:
  {
    "stage": 4,
    "step": "mechanism_classification",
    "reason": "...",
    "suggested_questions": ["..."],
    "partial_output": {
      "mechanisms_extracted_so_far": [...],
      "mechanisms_blocked": [...]
    }
  }
- Save context_packet snapshot to disk
- Output a structured NEEDS_HUMAN message with the specific problem and suggested actions
```

---

## Confidence Gate Pattern

Include this self-scoring process in your SKILL.md:

```
After producing output, score each dimension 0-20:

1. Completeness: Are all REQUIRED A-N categories represented with at least one mechanism?
   Are all mechanisms fully populated (id, name, description, category_ids, classification,
   chosen_approach)? Is mechanism_count >= 3? Is exactly one core mechanism identified?
2. Accuracy: Does every mechanism trace directly to the Stage 3 concept document?
   No hallucinated mechanisms? Classifications (OBVIOUS/NEEDS_EVALUATION) are defensible?
   Approach evaluations reflect genuine engineering tradeoffs?
3. Consistency: No overlapping mechanisms (same feature described twice)? Dependency
   graph is acyclic? Mechanism descriptions do not contradict each other? Category
   mappings are correct?
4. Specificity: Are mechanism descriptions precise enough for Stage 5 to apply the
   7-question framework without asking "what exactly does this mechanism do?"
   Are approach descriptions concrete (not "use a good solution")?
5. Handoff Readiness: Could Stage 5 immediately scaffold every mechanism? Is
   chosen_approach set for every mechanism? For dual_design mechanisms, is the
   alternate_approach also fully specified? Are dependencies clear enough for
   Stage 7 to sequence phases?

Total = sum of all 5 dimensions (/100)

>= 90: PASS -- proceed to next stage
70-89: WARN -- flag low dimensions, proceed with warning
< 70:  FAIL -- trigger escape hatch, do NOT pass output forward
```

---

## Output Location

Save the completed skill to:

```
docs/page-prds/prd-maker/skills/stage-04-mechanism-extraction/SKILL.md
```

If you need reference files, save them to:

```
docs/page-prds/prd-maker/skills/stage-04-mechanism-extraction/references/
```

---

## Agent-Readiness Checklist (Must Pass ALL)

Before finalizing your SKILL.md, verify:

- [ ] **Trigger routing:** The `description` field in YAML frontmatter contains specific trigger phrases and specifies what the skill produces (a tagged mechanism list with dependencies, evaluations, and core mechanism identification)
- [ ] **Output completeness:** Every output field has a name, type, and description. A downstream agent could parse the output with zero guessing. The mechanism object, evaluation sub-object, and dependency array are fully specified.
- [ ] **Edge cases explicit:** Missing input (empty concept document), ambiguous input (mechanism too vague to classify), scope overflow (discovering scaffolding-level details that belong to Stage 5), circular dependencies, all-OBVIOUS apps, and fewer-than-3 mechanisms all have defined behaviors with machine-readable responses
- [ ] **Composability:** The output contains ONLY structured data. No conversational text, no preamble, no "Here is what I found." Stage 5 can consume the output as-is and apply the 7-question framework to every mechanism.
- [ ] **Under 500 lines:** The SKILL.md body (excluding frontmatter) is under 500 lines
- [ ] **Single-line description:** The YAML `description` field is exactly one line, under 120 characters
- [ ] **Confidence gate included:** The self-scoring process is documented with all 5 dimensions tailored to Stage 4's actual outputs (mechanism completeness, classification accuracy, consistency, specificity, handoff readiness)
- [ ] **Escape hatch included:** The trigger conditions (missing concept document, unclassifiable mechanism, circular dependencies, < 3 mechanisms, score < 70), save protocol, and signal method are documented
- [ ] **Example included:** At least one realistic input/output example showing a structured concept decomposed into tagged mechanisms with evaluations and dependencies
- [ ] **Context packet fields match schema:** Every field read/written matches the context-packet-schema.md (section 2.6 for outputs, sections 2.3-2.5 for inputs)

---

## Success Criteria

- [ ] SKILL.md exists at `docs/page-prds/prd-maker/skills/stage-04-mechanism-extraction/SKILL.md`
- [ ] YAML frontmatter has `name: stage-04-mechanism-extraction` and single-line `description`
- [ ] SKILL.md body is under 500 lines
- [ ] All sections present: Purpose, When to Use, Input Format, Process, Output Format, Edge Cases, Confidence Scoring, Escape Hatch, Example
- [ ] Passes all 4 agent-readiness criteria (trigger routing, output completeness, edge cases, composability)
- [ ] Context packet fields match the schema document (section 2.6)
- [ ] Contract criteria from stage-contracts.md (Stage 4 section) are achievable by following the skill's process -- specifically: mechanism_count >= 3, all REQUIRED categories represented, exactly one core mechanism, acyclic dependency graph, proper granularity, 15% rule applied
- [ ] Reference files (if any) are in the `references/` subfolder and total under 20K tokens
- [ ] The skill enforces the boundary with Stage 5 -- identifies WHAT the mechanisms are, not HOW they work internally (no wall/door/room classification)
- [ ] The 10-step evaluation criteria are clearly defined (in SKILL.md or a reference file) with scoring guidance
- [ ] The 15% threshold rule is implemented correctly -- mechanisms within 15% get both approaches fully designed
- [ ] Developer's Choice routing is the default path, with clear rules for when it applies
