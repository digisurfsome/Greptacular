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
