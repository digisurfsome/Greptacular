---
name: stage-05-seven-question-scaffolding
description: Classify mechanism steps as WALL/DOOR/ROOM via 7-question framework, producing per-mechanism blueprints with phases and verification methods.
---

## Purpose

Apply the 7-question deterministic framework to every mechanism from Stage 4, classifying each process step as WALL (code handles), DOOR (AI within strict boundaries), or ROOM (AI creative freedom). Produces architectural blueprints that prevent builder agents from improvising in unstructured spaces.

## When to Use

Trigger when: Stage 4 mechanism extraction is complete and `context_packet.stage_4.mechanisms` exists with at least one mechanism. The pipeline is ready for 7-question scaffolding, wall/door/room classification, or mechanism blueprint generation.

Do NOT trigger when: Mechanisms have not been extracted yet (Stage 4 incomplete), or when doing layout/wireframing (Stage 6) or protocol injection (Stage 8).

## Input Format

```json
{
  "stage_4": {
    "mechanisms": [{ "id": "mech_001", "name": "string", "description": "string",
      "classification": "OBVIOUS|NEEDS_EVALUATION", "chosen_approach": { "name": "string", "description": "string" },
      "alternate_approach": { "name": "string", "description": "string", "score_delta": 0 } | null }],
    "mechanism_dependencies": [{ "from_id": "string", "to_id": "string", "relationship": "string" }],
    "dual_design_count": 0
  },
  "stage_3": { "drift_anchor": "string" },
  "stage_2": { "scope_contract": "string" },
  "stage_0": { "checklist_rule_ids": ["string"] }
}
```

## Process

### Step 1: Validate Inputs and Scope

Read `stage_4.mechanisms`. If empty or missing, trigger escape hatch. For each mechanism, verify it falls within `stage_2.scope_contract` and is consistent with `stage_3.drift_anchor`. If a mechanism exceeds scope, add a `scope_flag` note but still scaffold it — scope enforcement is not this stage's job.

### Step 2: Map Each Mechanism as a Human Process

For each mechanism, walk through what a human would do step by step. Use the mechanism's `chosen_approach.description` as the starting point. Think: "I'm a practitioner running this process. What happens first? What happens next? What determines which direction I go?"

Group steps into **phases** — logical chunks with clear entry/exit boundaries. A phase change occurs when the process crosses a meaningful boundary (e.g., from data collection to data processing, from user input to validation).

### Step 3: Apply the 7 Questions to Every Step

For each step within each phase, answer all 7 questions. See [references/seven-questions-framework.md](references/seven-questions-framework.md) for the complete framework and classification rules.

**Decision flow:** Question 2 is the primary classifier. Questions 3-7 refine and verify. Use the decision tree in [references/classification-decision-tree.md](references/classification-decision-tree.md) for borderline cases.

### Step 4: Apply Martin's Rules as Lens

While scaffolding, apply structural principles from `stage_0.checklist_rule_ids` as the design lens. These rules SHAPE scaffolding answers — they are not injected later. See [references/checklist-lens-rules.md](references/checklist-lens-rules.md) for the key rules.

Specifically enforce:
- **Single responsibility:** Each step does exactly one thing
- **No state leakage:** Entry/exit conditions enforce phase isolation
- **Service layer access:** Data steps go through service layer (WALL), not direct DB calls
- **Boundary validation:** Every step has verification
- **Separation of concerns:** UI steps separate from data steps separate from logic steps

Record which rule IDs influenced decisions in `build_rules_applied`.

### Step 5: Chain Entry/Exit Conditions

Verify that for every blueprint:
- Phase N's exit condition matches Phase N+1's entry condition
- Cross-mechanism dependencies (from `stage_4.mechanism_dependencies`) are reflected in entry conditions — if mechanism B depends on mechanism A, B's first phase entry condition references A's completion
- No gaps exist in the chain

### Step 6: Handle Dual-Design Mechanisms

For mechanisms with `alternate_approach` (15% rule from Stage 4), produce TWO complete blueprints — one with `approach: "primary"`, one with `approach: "alternate"`. Both get full scaffolding through all 7 questions. Stage 5 does not pick winners.

### Step 7: Validate and Score

Run all validation checks (see Validation section below). Then run confidence scoring. Process mechanisms sequentially to avoid accumulating too much intermediate state — write each blueprint before moving to the next.

## Output Format

Written to `context_packet.stage_5`:

```json
{
  "mechanism_blueprints": [{
    "mechanism_id": "string (refs stage_4.mechanisms[].id)",
    "approach": "primary|alternate",
    "phases": [{
      "phase_label": "string",
      "entry_condition": "string",
      "exit_condition": "string",
      "validation_rules": ["string"],
      "steps": [{
        "id": "string (unique, e.g. mech_001_p1_s1)",
        "name": "string (Q1: what happens here)",
        "classification": "WALL|DOOR|ROOM",
        "preconditions": ["string (Q3)"],
        "outcomes": [{ "outcome": "string (Q4)", "next_step": "string (step ID or 'end') (Q5)" }],
        "verification": "string (Q6: machine-checkable for WALLs)",
        "skip_condition": "string|null (Q7: null if not skippable)"
      }]
    }]
  }],
  "build_rules_applied": ["string (Martin's rule IDs that shaped scaffolding)"]
}
```

**Field constraints:**
- `classification`: Exactly one of `"WALL"`, `"DOOR"`, `"ROOM"` — no other values
- `verification` for WALLs: Must be machine-checkable (file exists, function exports X, schema matches)
- `skip_condition`: `null` for WALLs (never skippable), string condition for DOORs/ROOMs if applicable
- `outcomes[].next_step`: Must reference a valid step ID within the same phase, or `"end"` for phase termination
- DOOR steps: `preconditions` must include the constraint boundaries the AI operates within
- Every mechanism from Stage 4 must have at least one blueprint
- Dual-design mechanisms must have exactly two blueprints

Also write to `context_packet.metadata`:
- `metadata.current_stage`: `5`
- `metadata.confidence_scores["5"]`: Confidence object with 5 dimensions
- `metadata.stage_timestamps["5"]`: ISO 8601 timestamp

## Edge Cases

### Missing Input
If `stage_4.mechanisms` is empty/missing: trigger escape hatch with `reason: "no_mechanisms"`. Save partial state. Signal `NEEDS_HUMAN` with message: "Stage 4 produced no mechanisms. Cannot scaffold without mechanisms."

### Ambiguous Input
If a mechanism description is too vague for meaningful 7-question answers: scaffold what you can, flag the mechanism with `scope_flag: "vague_description"` in the blueprint, and add a suggested question to the escape hatch: "Mechanism X's description is too vague. Describe the step-by-step process a human would follow."

### Borderline WALL/DOOR Classification
When a step could be either WALL or DOOR, default to WALL (more restrictive). A WALL that should be a DOOR is discovered during build and relaxed. A DOOR that should be a WALL lets AI improvise where it shouldn't. See [references/classification-decision-tree.md](references/classification-decision-tree.md).

### 100% ROOM Mechanisms
Valid — some mechanisms (e.g., "generate marketing copy") have no walls. Still ask all 7 questions to confirm. The blueprint will have all steps classified as ROOM with topic boundaries defined in preconditions.

### Dual-Design Divergence
When primary and alternate approaches produce very different blueprints (different phase counts, different step classifications), this is expected and correct. Both blueprints stand independently. Do not try to reconcile them.

### Circular Dependencies
If cross-mechanism dependencies create circular scaffolding (A needs B's output, B needs A's output), trigger escape hatch with `reason: "circular_dependency"` and the mechanism IDs involved.

### Scope Overflow
If scaffolding reveals work that belongs to a different stage (e.g., discovering new mechanisms not in Stage 4), note it in `scope_flag` but complete your scaffolding. Do not add mechanisms — that's Stage 4's job.

## Confidence Scoring

After producing output, score each dimension 0-20:

1. **Completeness (0-20):** ALL mechanisms scaffolded? ALL steps classified? ALL 7 questions answered? Dual-design mechanisms have both blueprints?
2. **Accuracy (0-20):** Classifications obviously correct? Auth validation = WALL (not ROOM). Creative summary = ROOM (not WALL). No misclassifications?
3. **Consistency (0-20):** Blueprints align with Stage 4 descriptions? Entry/exit conditions chain? Cross-mechanism dependencies in entry conditions?
4. **Specificity (0-20):** WALL validations machine-checkable? DOOR constraints specific and bounded? Steps detailed enough to write code from?
5. **Handoff Readiness (0-20):** Could Stage 6 deterministically arrange pages? Every mechanism's UI surface clear? Connections between mechanisms explicit?

**Total = sum of 5 dimensions (/100)**

- **≥ 90:** PASS — proceed to Stage 6
- **70-89:** WARN — flag low dimensions in metadata, proceed with warning
- **< 70:** FAIL — trigger escape hatch, do NOT pass output forward

## Escape Hatch

**When to trigger:**
- Required input missing (no mechanisms from Stage 4)
- Mechanism description too vague for meaningful scaffolding (after one retry)
- Confidence score < 70 after one retry
- Circular cross-mechanism dependencies
- Mechanism fundamentally outside scope contract (not caught by Stage 4)

**What to save:**
- Current `context_packet` with partial blueprints
- Stage number (5) and mechanism ID being scaffolded when halt occurred
- List of mechanisms scaffolded vs remaining
- What was attempted and what failed
- Suggested questions for human

**How to signal:**
- Set `metadata.status = "needs_human"`
- Add entry to `metadata.escape_hatches[]` with `{ "stage": 5, "mechanism_id": "...", "reason": "..." }`
- Save context packet snapshot
- Output structured `NEEDS_HUMAN` message

## Example

See [references/example-blueprint.md](references/example-blueprint.md) for a complete worked example showing one mechanism ("User Authentication") run through all 7 questions with phases, steps, classifications, and chaining conditions.

**Quick inline example — one step scaffolded:**

Mechanism: "User Authentication" → Phase: "Credential Validation" → Step: "Validate email format"

| Question | Answer | Implication |
|----------|--------|-------------|
| Q1: What happens? | Check email matches RFC 5322 pattern | Named action |
| Q2: One way or varies? | One way — regex match | **WALL** |
| Q3: Preconditions? | Email field is non-empty | Precondition defined |
| Q4: All outcomes? | valid, invalid — two options only | Finite = deterministic |
| Q5: Next step per outcome? | valid → `check_password`, invalid → `show_error` | Arrows drawn |
| Q6: Verification? | `typeof result === 'boolean'`, regex tested against 5 known-valid and 5 known-invalid emails | Machine-checkable |
| Q7: Skippable? | No, never | Confirmed WALL |

Output step:
```json
{
  "id": "mech_001_p2_s1",
  "name": "Validate email format against RFC 5322",
  "classification": "WALL",
  "preconditions": ["Email field is non-empty string"],
  "outcomes": [
    { "outcome": "valid", "next_step": "mech_001_p2_s2" },
    { "outcome": "invalid", "next_step": "mech_001_p2_s3" }
  ],
  "verification": "Regex match returns boolean; tested against 5 valid + 5 invalid emails",
  "skip_condition": null
}
```
