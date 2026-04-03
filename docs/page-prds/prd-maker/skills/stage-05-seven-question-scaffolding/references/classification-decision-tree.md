# Classification Decision Tree

Use this tree when the 7-question answers don't produce an immediately obvious classification. Start at the top and follow the first matching branch.

## Primary Decision (Question 2)

```
Is there ONLY ONE way to do this step?
│
├─ YES → Is it skippable? (Q7)
│  ├─ NO → Is verification machine-checkable? (Q6)
│  │  ├─ YES → ██ WALL ██
│  │  └─ NO → Rewrite verification to be machine-checkable. If impossible → DOOR
│  └─ YES, if [condition] → DOOR (the skip condition is itself a wall-gate)
│
└─ NO, it can vary → Can you list ALL valid variations?
   ├─ YES (finite set) → DOOR
   │  └─ Document the valid set as constraints
   └─ NO (infinite/unpredictable) → ROOM
      └─ Define topic boundaries
```

## Borderline Cases

### Case: "It's mostly one way but delivery varies"
**Example:** "Ask the user for their email" — the data collected is fixed (WALL) but HOW you phrase the question can vary (DOOR).

**Resolution:** Split into two steps:
1. "Present email input field" → WALL (fixed UI element)
2. "Display contextual help text" → DOOR (can vary but must reference email)

If splitting is not justified (too granular), classify as WALL — the deterministic part dominates.

### Case: "Outcomes are finite but context-dependent"
**Example:** "Classify user sentiment" — outcomes are [positive, negative, neutral] (finite) but determining which one requires judgment.

**Resolution:** DOOR. The valid outcomes are the constraint (must be one of 3). The classification logic is bounded AI.

### Case: "Verification exists but isn't fully machine-checkable"
**Example:** "Generated summary must be accurate" — accuracy requires judgment.

**Resolution:** Make verification partially machine-checkable:
- "Summary must reference all 5 key points from the data" (checkable: count references)
- "Summary must be under 200 words" (checkable: word count)
- Remaining subjective quality → ROOM aspect

If you can make >50% of verification machine-checkable → DOOR. Otherwise → ROOM.

### Case: "Step can vary but variations are trivially equivalent"
**Example:** "Return success response" — could be `{success: true}` or `{status: "ok"}` but they're functionally identical.

**Resolution:** WALL. Pick one format and enforce it. The variation is an implementation detail, not meaningful flexibility.

### Case: "100% creative but has a fixed trigger"
**Example:** "Generate personalized greeting" — triggered by login (WALL), content is creative (ROOM).

**Resolution:** Split:
1. "Trigger greeting generation on login" → WALL
2. "Generate greeting content" → ROOM (with topic boundary: must reference user's name)

## The Default Rule

**When in doubt, classify as WALL (more restrictive).**

Rationale: A WALL that should have been a DOOR is discovered during build when the builder agent finds it too rigid — easy to relax by changing the classification. A DOOR that should have been a WALL lets the AI improvise where deterministic code should run — bugs are harder to find and fix.

## Anti-Patterns

| Wrong Classification | Why It's Wrong | Correct |
|---------------------|----------------|---------|
| Auth validation → ROOM | Auth MUST follow exact rules; no creative freedom | WALL |
| Database schema → DOOR | Schema is fixed; no AI variation | WALL |
| Error message text → WALL | User-facing text can be rephrased while keeping meaning | DOOR |
| API endpoint routing → DOOR | Routes are fixed paths; no flexibility | WALL |
| Onboarding tutorial → WALL | Tutorial content can be adaptive to user level | DOOR or ROOM |
| "Handle edge case" → ROOM | Vague. Break into specific cases, classify each | Split into specific steps |
