# Wall / Door / Room Classification Guide

## Definitions

### WALL (Deterministic)
- Must happen exactly one way. No variation.
- Enforced by code, not by convention.
- Never skippable.
- Verification is machine-checkable (file exists, function exports X, schema matches).
- Example: "Hash password before storing" — there is exactly one correct approach.

### DOOR (Constrained Choice)
- Multiple valid approaches exist, but within strict boundaries.
- AI can choose HOW but within defined constraints.
- Preconditions define the constraint envelope.
- Example: "Display user data" — could be table, cards, or list, but must show all required fields.

### ROOM (Creative Freedom)
- AI has flexibility in execution.
- Topic boundaries defined but approach is open.
- Example: "Design the onboarding experience" — many valid approaches.

## The 7 Questions (Apply to EVERY step of EVERY mechanism)

| # | Question | Purpose |
|---|----------|---------|
| Q1 | What happens here? | Names the action |
| Q2 | Is there only one way, or can it vary? | PRIMARY CLASSIFIER: One way = WALL. Constrained = DOOR. Free = ROOM |
| Q3 | What must be true before this step can start? | Preconditions / entry gate |
| Q4 | What are all possible outcomes? | Finite outcomes lean WALL/DOOR |
| Q5 | For each outcome, where do you go next? | Flow routing / arrows between steps |
| Q6 | How do you verify this was done correctly? | WALLs need machine-checkable proof |
| Q7 | Can this step be skipped? | WALLs: NEVER. DOORs/ROOMs: conditional |

## Classification Rules

1. **When ambiguous between WALL and DOOR, default to WALL.** A WALL relaxed to DOOR is discovered during build. A DOOR that should be WALL lets AI improvise where it shouldn't.
2. **Q2 is the primary classifier.** Other questions refine and verify.
3. **Every WALL must have a machine-checkable verification** (Q6). If you can't define one, it's probably a DOOR.
4. **Every DOOR must have explicit constraints.** If you can't define boundaries, it's a ROOM.
5. **ROOMs still have topic boundaries.** "Creative freedom" doesn't mean "do anything."

## Output Format Per Step

```json
{
  "step_id": "mech_001_step_03",
  "name": "Hash user password",
  "classification": "WALL",
  "preconditions": ["Raw password received", "bcrypt library available"],
  "outcomes": [
    {"result": "success", "next_step": "mech_001_step_04"},
    {"result": "failure", "next_step": "error_handler"}
  ],
  "verification": "bcrypt.compare(raw, stored) returns true",
  "skippable": false
}
```
