# The 7-Question Framework

For each step of each mechanism, ask these 7 questions. The answers determine the WALL/DOOR/ROOM classification.

## The Questions

### Question 1: WHAT happens here?
Name the action. Be specific and mechanical: "Validate email format", "Query user record by ID", "Generate welcome message". If you can't name it precisely, the mechanism description is too vague.

### Question 2: Is there ONLY ONE way to do this, or can it vary? (PRIMARY CLASSIFIER)
This is the fork:
- **Only one way** → **WALL** (deterministic, code it)
- **Can vary** → Continue to determine **DOOR** or **ROOM**

To distinguish DOOR from ROOM when the answer is "can vary":
- Can you enumerate ALL valid variations? → **DOOR** (constrained set)
- Variations are infinite/unpredictable? → **ROOM** (open floor)

### Question 3: What MUST be true before this step can start?
These are preconditions — walls that prevent skipping ahead. Examples:
- "User must be authenticated" (WALL precondition)
- "Previous step must have returned valid data" (WALL precondition)
- "Context must be established" (WALL precondition)

Every precondition is itself a WALL — it's a gate that must pass before proceeding.

### Question 4: What are ALL the possible outcomes of this step?
- **Can list them ALL** = deterministic outcomes. Strengthens WALL/DOOR classification.
- **Infinite/unpredictable outcomes** = AI territory. Points toward ROOM.

Examples:
- "valid, invalid" (2 outcomes — deterministic)
- "toward, away, toward_lean, away_lean" (4 outcomes — deterministic)
- "Any natural language response" (infinite — AI territory)

### Question 5: For each outcome, where do you go next?
Draws the arrows between steps. Every outcome must have a defined next step (by step ID) or "end" (terminates the phase). No dangling outcomes.

This question also reveals hidden complexity: if outcome A leads to step X but outcome B loops back to step Y, the branching logic itself is a WALL (code decides the routing, not AI).

### Question 6: How do you VERIFY this step was done correctly?
The validation question. This is the wall you bounce off if you try to cheat.

- **For WALLs:** Must be machine-checkable. Examples:
  - "File exists at path X"
  - "Function exports loginUser and signupUser"
  - "Response matches JSON schema"
  - "Return value is one of [valid, invalid]"
  - NOT: "Check it works" or "Looks correct"

- **For DOORs:** Must verify constraints were respected. Examples:
  - "Response contains all 3 required data points"
  - "Output uses only vocabulary from the approved list"
  - "Follow-up question references the same topic as the original"

- **For ROOMs:** Must verify topic boundaries. Examples:
  - "Response references all identified items from the data set"
  - "Output is related to the mechanism's domain"

### Question 7: Can this step be skipped? Ever? Under any circumstance?
- **No, never** → Strengthens WALL classification
- **Yes, if [specific condition]** → DOOR with a lock (the condition is the lock)
- **Yes, always optional** → Could be ROOM or DOOR depending on other answers

## Classification Summary Table

| Signal | WALL | DOOR | ROOM |
|--------|------|------|------|
| Q2: Variation | One way only | Enumerable variations | Infinite variations |
| Q4: Outcomes | Finite, listable | Finite but context-dependent | Unpredictable |
| Q6: Verification | Machine-checkable | Constraint-checkable | Topic-boundary check |
| Q7: Skippable | Never | Conditionally | Often |
| Data format | Structured (schema) | Semi-structured (template) | Unstructured (prose) |
| Who controls | Code only | Code + bounded AI | AI with topic fence |

## WALL Characteristics
- Must happen exactly this way, no variation
- Possible answers from a fixed list
- Order follows a set sequence
- Results recorded in structured format
- Cannot be skipped
- Verification is machine-checkable

## DOOR Characteristics
- AI can rephrase but MUST contain the core requirement
- Must pick from valid options ONLY
- Can ask follow-up but ONLY to clarify same topic — cannot drift
- Has explicit boundaries that cannot be crossed
- Every DOOR step must document its constraints in preconditions

## ROOM Characteristics
- Small talk, rapport building, creative generation
- Explaining results in accessible language
- Generating summaries or novel content
- Any output where format/content is genuinely unpredictable
- Still has topic boundaries (the "walls of the room")
