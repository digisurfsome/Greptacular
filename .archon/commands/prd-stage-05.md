# Stage 5: Seven-Question Scaffolding

You are the deterministic scaffolding engine. This is the most important stage. You apply the 7-question framework to every mechanism, classifying every process step as WALL, DOOR, or ROOM.

## Input

Read `$ARTIFACTS_DIR/context_packet.json`. You need `stage_4.mechanisms`, `stage_4.mechanism_dependencies`, and `stage_0.structural_rules`.

Also read `references/wall-door-room-guide.md` for classification rules and the 7 questions.

## Process

### Step 1: For Each Mechanism, Map as a Human Process

Break each mechanism into sequential steps as a human would perform them. Group steps into phases with entry/exit boundaries.

Example for "User Authentication":
- Phase 1: Registration (steps: show form → validate input → hash password → store user → send confirmation)
- Phase 2: Login (steps: show form → validate credentials → create session → redirect)
- Phase 3: Password Reset (steps: request reset → send email → validate token → update password)

### Step 2: Apply 7 Questions to EVERY Step

For each step, answer all 7 questions from the reference guide:

1. **Q1**: What happens here? (Name it)
2. **Q2**: Is there only one way, or can it vary? (WALL / DOOR / ROOM)
3. **Q3**: What must be true before this step can start? (Preconditions)
4. **Q4**: What are all possible outcomes? (List them)
5. **Q5**: For each outcome, where do you go next? (Routing)
6. **Q6**: How do you verify this was done correctly? (Verification method)
7. **Q7**: Can this step be skipped? (WALLs: never)

### Step 3: Apply Structural Rules as Design Lens

For each step, check against the structural rules from stage_0:
- Single responsibility: Does this step do only one thing?
- No state leakage: Does this step contain its state?
- Boundary validation: Are inputs validated at entry?

Record which rules influenced each classification decision.

### Step 4: Chain Entry/Exit Conditions

Phase N's exit conditions must match Phase N+1's entry conditions. Cross-mechanism dependencies must also align.

### Step 5: Borderline Rule

When ambiguous between WALL and DOOR, **default to WALL**. It's safer to relax a WALL to a DOOR during build than to discover a DOOR should have been a WALL.

## Output

Update `$ARTIFACTS_DIR/context_packet.json` — add `stage_5`:

```json
{
  "stage_5": {
    "mechanism_blueprints": [
      {
        "mechanism_id": "mech_001",
        "phases": [
          {
            "phase_name": "Registration",
            "entry_conditions": [],
            "exit_conditions": [],
            "steps": [
              {
                "step_id": "mech_001_step_01",
                "name": "Show registration form",
                "classification": "DOOR",
                "preconditions": ["User is not authenticated"],
                "outcomes": [
                  {"result": "form_submitted", "next_step": "mech_001_step_02"},
                  {"result": "cancelled", "next_step": null}
                ],
                "verification": "Form renders with all required fields",
                "skippable": false,
                "rules_applied": ["single_responsibility"]
              }
            ]
          }
        ]
      }
    ],
    "total_walls": 0,
    "total_doors": 0,
    "total_rooms": 0,
    "stage_contract": "pass"
  }
}
```

IMPORTANT: Read existing context_packet.json, merge stage_5, increment version to 5, write back. This stage produces the most data — take your time and be thorough.
