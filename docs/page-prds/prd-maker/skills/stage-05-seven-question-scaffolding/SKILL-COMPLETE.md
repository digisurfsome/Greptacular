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


---

## REFERENCE: checklist-lens-rules

# Martin's Checklist Rules as Scaffolding Lens

These are the Martin's Structural Checklist rules most relevant to Stage 5 scaffolding decisions. These rules SHAPE how you answer the 7 questions — they are the building code the architect follows WHILE designing.

## How to Use This Document

When scaffolding a mechanism's steps, consult these rules to inform your answers:
- **When defining WALLs:** Rules ensure walls are clean (single responsibility, no state leakage)
- **When setting phase boundaries:** Rules enforce isolation between phases
- **When writing verification:** Rules define what "correct" looks like structurally

Record every rule ID that influenced a scaffolding decision in `build_rules_applied`.

## Key Rules by Scaffolding Decision

### Step Granularity (Single Responsibility)

| Rule ID | Category | Rule | Scaffolding Impact |
|---------|----------|------|-------------------|
| FileStructure.1 | File Structure | One component per file | Each UI step maps to one component file |
| FileStructure.2 | File Structure | Feature folders for grouping | Steps in the same mechanism phase share a feature folder |
| FileStructure.3 | File Structure | Centralized type definitions | Data types are WALLs — defined once, referenced everywhere |

### Data Access (Service Layer Enforcement)

| Rule ID | Category | Rule | Scaffolding Impact |
|---------|----------|------|-------------------|
| FileStructure.8 | File Structure | Services folder for data access | Any step that touches DB → WALL with service layer access pattern |
| DataService.1 | Data Service Layer | All CRUD via service functions | Direct DB imports in components = violation. Service layer = WALL. |
| DataService.2 | Data Service Layer | Typed return values | Service functions return typed data → verification is type-checkable |
| DataService.3 | Data Service Layer | Error handling in service layer | Errors caught in service, not in components → clean phase boundaries |

### State Management (Phase Isolation)

| Rule ID | Category | Rule | Scaffolding Impact |
|---------|----------|------|-------------------|
| Stack.5 | Stack | Built-in state management | State flows through framework primitives → WALL (deterministic) |
| Stack.6 | Stack | No external state libraries | State complexity stays bounded → fewer DOORs needed |
| Config.1 | Configuration | Single config source | Config is a WALL — one place, one format, no variation |

### Authentication (Heavy WALL Zone)

| Rule ID | Category | Rule | Scaffolding Impact |
|---------|----------|------|-------------------|
| Auth.1 | Authentication | Auth provider pattern | Auth steps are WALLs — provider handles, code enforces |
| Auth.2 | Authentication | Auth context wraps app | Auth state check = WALL precondition for protected routes |
| Auth.3 | Authentication | Redirect on auth failure | Auth failure routing = WALL (code decides, not AI) |
| RouteGuard.1 | Route Guards | Protected route component | Route protection = WALL entry condition for every protected phase |

### Validation (Boundary Enforcement)

| Rule ID | Category | Rule | Scaffolding Impact |
|---------|----------|------|-------------------|
| DataAPI.1 | Data/API Patterns | Input validation before writes | Every data-write step must have a validation WALL before it |
| DataAPI.2 | Data/API Patterns | Sanitize user input | Input handling = WALL (deterministic sanitization) |
| ErrorHandling.1 | Error Handling | Consistent error format | Error display = DOOR (text varies) with WALL format constraint |
| ErrorHandling.2 | Error Handling | User-facing error messages | Never expose raw errors → DOOR with constraint |

### UI Patterns (Component Classification)

| Rule ID | Category | Rule | Scaffolding Impact |
|---------|----------|------|-------------------|
| UX.1 | UX Standards | Loading states for async | Loading indicator = WALL (always present during async) |
| UX.2 | UX Standards | Empty states with guidance | Empty state = DOOR (text varies, must guide user) |
| UX.3 | UX Standards | Confirmation for destructive | Confirm dialog = WALL (must appear before delete/destroy) |
| UX.6 | UX Standards | Form validation feedback | Inline validation = WALL (immediate, specific feedback) |

### Separation of Concerns

| Rule ID | Category | Rule | Scaffolding Impact |
|---------|----------|------|-------------------|
| FileStructure.4 | File Structure | Custom hooks per feature | Logic steps separate from UI steps → clean phase splits |
| FileStructure.5 | File Structure | Required directory structure | File placement = WALL (deterministic by convention) |
| DataStructure.1 | Data Structure | Typed interfaces | Schema definition = WALL (code enforces shape) |

## Rule Citation Format

When recording rules in `build_rules_applied`, use the format: `"Category.RuleNumber"` — for example:
- `"FileStructure.8"` — Services folder for data access
- `"DataService.1"` — All CRUD via service functions
- `"Auth.1"` — Auth provider pattern
- `"UX.3"` — Confirmation for destructive actions
- `"ErrorHandling.1"` — Consistent error format

## Most Common Rules Per Mechanism Type

| Mechanism Type | Commonly Applied Rules |
|---------------|----------------------|
| Authentication | Auth.1, Auth.2, Auth.3, RouteGuard.1, DataAPI.1 |
| Data CRUD | DataService.1, DataService.2, FileStructure.8, DataAPI.1, DataAPI.2 |
| UI Forms | UX.6, ErrorHandling.1, ErrorHandling.2, DataStructure.1 |
| Navigation | RouteGuard.1, Auth.2, FileStructure.5 |
| Dashboard/Display | UX.1, UX.2, FileStructure.4, DataService.1 |
| User Settings | UX.3, DataService.1, DataAPI.1, ErrorHandling.2 |
| Search/Filter | DataService.1, UX.1, FileStructure.4 |
| File Upload | DataAPI.2, UX.1, ErrorHandling.1, DataService.1 |


---

## REFERENCE: classification-decision-tree

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


---

## REFERENCE: example-blueprint

# Example Blueprint: User Authentication Mechanism

## Input (from Stage 4)

```json
{
  "id": "mech_001",
  "name": "User Authentication",
  "description": "Email/password registration and login with session management. Users register with email and password, verify their email, log in to receive a session token, and can reset forgotten passwords.",
  "category_ids": ["B"],
  "classification": "OBVIOUS",
  "chosen_approach": {
    "name": "Email/Password with JWT",
    "description": "Standard email/password auth using JWT tokens for session management, with email verification via one-time links and password reset via time-limited tokens.",
    "rationale": "Most common auth pattern, well-supported by all frameworks"
  },
  "alternate_approach": null
}
```

## Step 2: Map as Human Process

Walking through what a human admin would do:
1. User arrives at registration page → enters email + password
2. System validates email format and password strength
3. System checks if email already exists in database
4. System creates user record and sends verification email
5. User clicks verification link → system marks email as verified
6. User goes to login page → enters credentials
7. System validates credentials against stored hash
8. System issues session token
9. User can request password reset → system sends reset link
10. User clicks reset link → enters new password → system updates hash

Group into phases: Registration, Email Verification, Login, Password Reset.

## Step 3: Apply 7 Questions

### Phase 1: Registration

**Entry condition:** User is on the registration page; no active session exists.
**Exit condition:** User record exists in database with `email_verified: false`.

#### Step: Render registration form

| Q | Answer | Classification |
|---|--------|---------------|
| Q1 | Display form with email, password, confirm password fields | |
| Q2 | One way — exact fields required | **WALL** |
| Q3 | Registration page loaded; no existing session | |
| Q4 | Form displayed successfully, or page load error | |
| Q5 | Success → user fills form; Error → show error page | |
| Q6 | DOM contains input[name=email], input[name=password], input[name=confirmPassword], button[type=submit] | |
| Q7 | No — cannot skip | |

```json
{
  "id": "mech_001_p1_s1",
  "name": "Render registration form with email, password, confirm password fields",
  "classification": "WALL",
  "preconditions": ["Registration page route loaded", "No active user session"],
  "outcomes": [
    { "outcome": "Form rendered successfully", "next_step": "mech_001_p1_s2" },
    { "outcome": "Page load error", "next_step": "end" }
  ],
  "verification": "DOM contains input[name=email], input[name=password], input[name=confirmPassword], button[type=submit]",
  "skip_condition": null
}
```

#### Step: Validate email format

```json
{
  "id": "mech_001_p1_s2",
  "name": "Validate email format against RFC 5322 pattern",
  "classification": "WALL",
  "preconditions": ["Email field is non-empty string"],
  "outcomes": [
    { "outcome": "Email format valid", "next_step": "mech_001_p1_s3" },
    { "outcome": "Email format invalid", "next_step": "mech_001_p1_s5" }
  ],
  "verification": "Regex returns boolean; tested against 5 valid + 5 invalid email formats",
  "skip_condition": null
}
```

#### Step: Validate password strength

```json
{
  "id": "mech_001_p1_s3",
  "name": "Validate password meets minimum strength requirements",
  "classification": "WALL",
  "preconditions": ["Password field is non-empty", "Email validation passed"],
  "outcomes": [
    { "outcome": "Password meets requirements (8+ chars, 1 upper, 1 number)", "next_step": "mech_001_p1_s4" },
    { "outcome": "Password too weak", "next_step": "mech_001_p1_s5" }
  ],
  "verification": "Strength check returns {valid: boolean, failures: string[]}; tested against known-weak and known-strong passwords",
  "skip_condition": null
}
```

#### Step: Check email uniqueness in database

```json
{
  "id": "mech_001_p1_s4",
  "name": "Query database to verify email is not already registered",
  "classification": "WALL",
  "preconditions": ["Email format valid", "Password strength valid"],
  "outcomes": [
    { "outcome": "Email not found — available", "next_step": "mech_001_p1_s6" },
    { "outcome": "Email already exists", "next_step": "mech_001_p1_s5" }
  ],
  "verification": "Database query returns boolean; service layer function getUserByEmail() called (not direct DB access)",
  "skip_condition": null
}
```

#### Step: Display validation error

```json
{
  "id": "mech_001_p1_s5",
  "name": "Display specific validation error message to user",
  "classification": "DOOR",
  "preconditions": ["At least one validation check failed", "Error type is known (email_format|password_weak|email_exists)"],
  "outcomes": [
    { "outcome": "Error displayed, user corrects input", "next_step": "mech_001_p1_s2" }
  ],
  "verification": "Error element visible in DOM; error text contains the specific failure reason; error disappears when user modifies the relevant field",
  "skip_condition": null
}
```

Note: DOOR because the error message text can be rephrased ("Invalid email" vs "Please enter a valid email address") but MUST identify the specific failure. Constraint: message must reference the failed field and the requirement that was not met.

#### Step: Create user record and send verification email

```json
{
  "id": "mech_001_p1_s6",
  "name": "Create user record in database and trigger verification email",
  "classification": "WALL",
  "preconditions": ["All validations passed", "Email is unique"],
  "outcomes": [
    { "outcome": "User created, verification email sent", "next_step": "end" },
    { "outcome": "Database write error", "next_step": "mech_001_p1_s5" }
  ],
  "verification": "User record exists in DB with email_verified=false; verification token generated; email service called with token link",
  "skip_condition": null
}
```

### Phase 1 Validation Rules
- `["User record exists in database with email_verified=false", "Verification email was dispatched via email service", "No direct database imports in component files — all through service layer"]`

---

### Phase 2: Email Verification

**Entry condition:** User record exists with `email_verified: false`; verification token exists in database.
**Exit condition:** User record has `email_verified: true`.

*(Steps follow same pattern — abbreviated for space)*

### Phase 3: Login

**Entry condition:** User record exists with `email_verified: true`; user is on login page.
**Exit condition:** Valid session token issued and stored.

### Phase 4: Password Reset

**Entry condition:** User has a verified account; user requests password reset.
**Exit condition:** Password hash updated in database; old sessions invalidated.

## Complete Output Blueprint

```json
{
  "mechanism_id": "mech_001",
  "approach": "primary",
  "phases": [
    {
      "phase_label": "Registration",
      "entry_condition": "User is on registration page; no active session exists",
      "exit_condition": "User record exists in database with email_verified=false",
      "validation_rules": [
        "User record exists in database with email_verified=false",
        "Verification email dispatched via email service",
        "All DB access through service layer (no direct imports)"
      ],
      "steps": ["(6 steps as shown above)"]
    },
    {
      "phase_label": "Email Verification",
      "entry_condition": "User record exists with email_verified=false; verification token exists",
      "exit_condition": "User record has email_verified=true",
      "validation_rules": ["..."],
      "steps": ["..."]
    },
    {
      "phase_label": "Login",
      "entry_condition": "User record exists with email_verified=true; user on login page",
      "exit_condition": "Valid session token issued and stored client-side",
      "validation_rules": ["..."],
      "steps": ["..."]
    },
    {
      "phase_label": "Password Reset",
      "entry_condition": "User has verified account; user requests password reset",
      "exit_condition": "Password hash updated; old sessions invalidated",
      "validation_rules": ["..."],
      "steps": ["..."]
    }
  ]
}
```

**Key observations:**
- Phase 1 exit → Phase 2 entry: Both reference "user record with email_verified=false" ✓
- Phase 2 exit → Phase 3 entry: Both reference "email_verified=true" ✓
- Phase 3 and Phase 4 can be entered independently (Phase 4 doesn't require login)
- 5 of 6 Registration steps are WALL (deterministic). Only error display is DOOR. This is typical for auth mechanisms — mostly walls.
- Build rules applied: `["FileStructure.8"]` (services folder for data access), `["DataService.1"]` (CRUD through service layer), `["Auth.1"]` (auth provider pattern), `["FileStructure.1"]` (one component per file for form)


---

## REFERENCE: seven-questions-framework

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


---

## REFERENCE: Martin's Agnostic Checklist

# Martin's Structural Checklist — Technology-Agnostic Version

## Theory: The Structural-Mechanism Split

Building any app has two halves:

**The Structural Half** covers how the code is organized — file structure, component patterns, state management, auth setup, styling rules, what's banned. This is the same for EVERY app regardless of the idea. Martin's 1,500-line Build PRD covers this half. So do boilerplates. This checklist makes that knowledge systematic and matchable.

**The Mechanism Half** covers what the specific app DOES — its features, user flows, data transformations, integrations. This varies per app and is handled by the Mechanism Identification Framework (A-N categories) in a separate document (`mechanism-identification-framework.md`).

Together, the structural checklist + the mechanism framework = a complete app specification with zero gaps.

### About This Version

This is the **technology-agnostic version** of Martin's structural checklist. The original (`trial-idea-1-structural-checklist.md`) was written for a specific stack (React 19 + Firebase + Firestore + Google Auth + Lucide React + importmap). This version preserves all ~192 rules and 43 banned patterns but rewrites stack-specific rules so they apply to **any technology stack**.

**This is the source of truth.** Platform-specific preambles (e.g., `web-firebase.md`, `web-supabase.md`, `mobile-flutter.md`) are DERIVED from this document by filling in the "Boilerplate Match" column with platform-specific details. When in doubt, defer to this document.

### Classification System

Every rule is tagged with two attributes:

**Type** — How stack-specific the rule is:

| Tag | Meaning |
|-----|---------|
| **UNIVERSAL** | Applies to any stack as written. No changes needed. |
| **STACK-SPECIFIC** | Originally tied to a specific technology. Technical Spec rewritten to generic language. |
| **PATTERN** | Universal principle with a stack-specific implementation. Principle extracted; original noted as example. |

**Severity** — How critical the rule is:

| Tag | Meaning |
|-----|---------|
| **CRITICAL** | Security, data integrity, auth bypass, build-breaking, or production crash if violated. Non-negotiable. |
| **STANDARD** | UX quality, component patterns, state management, code organization. Violating these produces a working but sloppy app. |
| **POLISH** | Cosmetic refinements, animation, spacing, naming. Nice to have but the app works fine without them. |

### How This Checklist Works

Each row captures one technical rule from Martin's narrative:
- **Martin Says** — his exact words (quoted, preserved verbatim even if stack-specific)
- **Technical Spec (Agnostic)** — precise, implementable translation written for any stack
- **Boilerplate Match** — intentionally blank; filled during the boilerplate matching step

### The Preamble System

This checklist becomes a "preamble" injected before every pipeline stage. It tells the agent what's already decided so it doesn't waste time asking about structure. The agent only asks about mechanisms (what the app DOES).

### The Boilerplate Matching Step

A separate agent reads this checklist + a specific boilerplate and fills in the "Boilerplate Match" column:
- **MATCH** — Rule applies as-is to the boilerplate
- **REPLACE** — Rule principle applies but implementation differs (e.g., Firebase → Supabase)
- **ENHANCE** — Boilerplate has a more complete implementation than the rule describes
- **HANDLED** — Boilerplate already implements this; mark "don't touch"

Result: a boilerplate-specific preamble (e.g., `web-supabase.md`, `mobile-flutter.md`, `dual.md`, `no-boilerplate.md`).

---

## The Checklist

**Total: ~192 rules across 22 categories + 43 banned patterns**

---
---

### Stack (Mandatory)

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | Framework with type safety | "React 19 with TypeScript" | Use the project's chosen UI framework with strict type checking enabled; all code must be statically typed | _[to be filled]_ | STACK-SPECIFIC | STANDARD |
| 2 | Single styling solution | "Tailwind CSS for all styling" | All styling via a single, consistent CSS methodology (utility-first framework, CSS modules, or styled-components); no mixing approaches; no inline styles | _[to be filled]_ | STACK-SPECIFIC | STANDARD |
| 3 | Authentication provider | "Firebase Authentication (Google Sign-In only)" | Use the configured authentication provider's sign-in flow with the designated OAuth provider; restrict to approved sign-in methods only | _[to be filled]_ | STACK-SPECIFIC | CRITICAL |
| 4 | Single database backend | "Cloud Firestore for database" | All persistent data stored in a single configured database technology; do not mix multiple database backends within one project | _[to be filled]_ | STACK-SPECIFIC | STANDARD |
| 5 | Built-in state management | "React Context for auth state" | Auth and feature state managed via the framework's built-in state management primitives (e.g., React Context, Vue provide/inject, Angular services) | _[to be filled]_ | STACK-SPECIFIC | STANDARD |
| 6 | No external state libraries | "NO external state libraries" | No third-party state management libraries (Redux, Zustand, Jotai, MobX, Pinia, NgRx, etc.) unless explicitly approved in project config | _[to be filled]_ | STACK-SPECIFIC | STANDARD |
| 7 | No containerization | "NO Docker" | No Dockerfiles, no docker-compose, no containerization in the project scaffold; deployment handled by the configured hosting platform | _[to be filled]_ | STACK-SPECIFIC | STANDARD |
| 8 | No custom backend | "NO backend APIs" | No custom server-side code (Express, FastAPI, Django, etc.); all backend functionality provided by the configured BaaS or serverless platform | _[to be filled]_ | STACK-SPECIFIC | STANDARD |
| 9 | Single icon library | "Use Lucide React for all icons" | Use a single, consistent icon library for all icons throughout the app; do not mix icon sources; define a standard icon size | _[to be filled]_ | STACK-SPECIFIC | POLISH |
| 10 | Dependency management locked | Locked importmap in index.html | All dependencies managed through the project's configured module/build system; dependency versions locked and not modified without explicit approval | _[to be filled]_ | STACK-SPECIFIC | STANDARD |

---

### File Structure

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | One component per file | "One component per file" | Each file exports exactly one UI component as its default/primary export; no multi-component files | _[to be filled]_ | UNIVERSAL | STANDARD |
| 2 | Feature folders for grouping | "Group related components in feature folders" | Related components go in `components/[FeatureName]/` directories; do not flatten everything into a single folder | _[to be filled]_ | UNIVERSAL | STANDARD |
| 3 | Centralized type definitions | "Create interfaces for all data types" | All shared type definitions (interfaces, types, schemas) centralized in a dedicated types directory or file; no inline type definitions scattered across components. (e.g., TypeScript: `types/index.ts`, Python: `models.py`, Go: `types.go`) | _[to be filled]_ | PATTERN | STANDARD |
| 4 | Custom hooks per feature | "Add custom hooks for reusable logic" | Extract shared stateful logic into reusable hook/composable files following framework conventions (e.g., React: `hooks/use[Feature].ts`, Vue: `composables/use[Feature].ts`) | _[to be filled]_ | PATTERN | POLISH |
| 5 | Required directory structure | File tree showing src/ layout | Source directory organized into: config/, state-management/, hooks-or-composables/, components/ui/, pages-or-views/, services/, utils/, types/. (e.g., React: `contexts/`, `hooks/`, `pages/`; Vue: `stores/`, `composables/`, `views/`) | _[to be filled]_ | PATTERN | STANDARD |
| 6 | Config folder for service credentials | `config/firebase.ts` | Service configuration and credentials live in a dedicated `config/` directory; never scattered across multiple locations. (e.g., Firebase: `config/firebase.ts`, Supabase: `config/supabase.ts`) | _[to be filled]_ | PATTERN | CRITICAL |
| 7 | State management folder | `contexts/AuthContext.tsx`, `ThemeContext.tsx`, `ToastContext.tsx` | All global state providers in a dedicated directory; add feature-specific state files for each app domain. (e.g., React: `contexts/`, Vue: `stores/`, Angular: `services/`) | _[to be filled]_ | PATTERN | STANDARD |
| 8 | Services folder for data access | `services/firestore.ts` | All database/API CRUD operations in a dedicated `services/` directory; components never import database client libraries directly. (e.g., Firebase: `services/firestore.ts`, Supabase: `services/supabase.ts`) | _[to be filled]_ | PATTERN | CRITICAL |
| 9 | Utils folder | `utils/formatDate.ts`, `utils/pluralize.ts` | Helper functions in a `utils/` directory; at minimum date formatting and pluralization utilities | _[to be filled]_ | UNIVERSAL | STANDARD |
| 10 | Pages folder with naming convention | `pages/[Item]DetailPage.tsx`, `[Item]CreatePage.tsx`, `[Item]EditPage.tsx` | Page/view components follow `[Entity][Action]Page` naming convention; one page per route | _[to be filled]_ | UNIVERSAL | STANDARD |
| 11 | UI components folder | `components/ui/` with Modal, Toast, etc. | All reusable UI primitives in a dedicated `components/ui/` directory | _[to be filled]_ | UNIVERSAL | STANDARD |

---

### Configuration / Module System

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | Dependency versions locked | "IMPORTMAP IS LOCKED. DO NOT MODIFY" | Dependency versions are locked via the project's package manager or module system; no version changes, additions, or removals without explicit approval | _[to be filled]_ | STACK-SPECIFIC | STANDARD |
| 2 | No redundant sub-imports | "DO NOT ADD firebase/app, firebase/auth, or firebase/firestore to the importmap" | Do not add redundant or conflicting entries to the dependency configuration; follow the package's recommended import pattern. (e.g., Firebase: single `firebase/` trailing-slash entry handles all sub-imports) | _[to be filled]_ | STACK-SPECIFIC | STANDARD |
| 3 | CSS framework loading | `<script src="https://cdn.tailwindcss.com">` | CSS framework loaded via the project's standard method (CDN, build tool, or package manager) with inline configuration for theme customization | _[to be filled]_ | STACK-SPECIFIC | STANDARD |
| 4 | Typography font loaded | Google Fonts link for Inter | Load the project's chosen font family with required weights (regular, medium, semi-bold, bold) via CDN or local files | _[to be filled]_ | STACK-SPECIFIC | POLISH |
| 5 | CSS variables for theming | "Use `var(--color-*)` references so the theme toggle works" | Light mode values in `:root`; dark mode overrides in a toggled class; reference via CSS custom properties (`var(--color-*)`) throughout | _[to be filled]_ | UNIVERSAL | STANDARD |
| 6 | Dark mode via class strategy | `darkMode: 'class'` | Dark mode toggled via a CSS class on the root element; not via `prefers-color-scheme` media query alone | _[to be filled]_ | UNIVERSAL | STANDARD |
| 7 | Semantic color tokens | Surface, text, border color tokens | Colors defined as semantic tokens (surface-canvas/base/muted, text-primary/secondary/tertiary, border-subtle, brand/brand-dark) not raw color values | _[to be filled]_ | UNIVERSAL | STANDARD |
| 8 | Custom border radius token | `borderRadius: { card: '12px' }` | Define a reusable border radius token for cards (e.g., 12px) in the design system configuration | _[to be filled]_ | UNIVERSAL | POLISH |
| 9 | Custom card shadow token | `boxShadow: { card: '...' }` | Define a reusable card shadow token with subtle dual-shadow in the design system configuration | _[to be filled]_ | UNIVERSAL | POLISH |
| 10 | Optional AI SDK import | "Add this single line to the importmap" for @google/genai | If using an AI SDK, add it via the standard dependency management method; do not pin to a specific version unless required for stability. (e.g., Google GenAI via importmap, OpenAI via npm) | _[to be filled]_ | STACK-SPECIFIC | STANDARD |

---

### Authentication Context

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | UserProfile interface with role | `interface UserProfile { uid, email, displayName, photoURL, role, createdAt, updatedAt }` | User profile stored in the database includes a `role` field with defined role values (e.g., `user`, `pro`, `admin`); profile type/interface defined centrally | _[to be filled]_ | PATTERN | STANDARD |
| 2 | Auth context provides full interface | `user`, `userProfile`, `loading`, `signInWithGoogle`, `logout`, `isAdmin`, `isPro` | Auth state provider exposes: authenticated user object, database user profile, loading state, sign-in/sign-out functions, and role convenience booleans. (e.g., React: AuthContext, Vue: auth store, Angular: AuthService) | _[to be filled]_ | PATTERN | STANDARD |
| 3 | Profile created on first login | `setDoc` on first sign-in | On first successful authentication where no database profile exists, auto-create a profile record with default role and server-generated timestamps. (e.g., Firebase: `setDoc` on first `onAuthStateChanged`) | _[to be filled]_ | PATTERN | CRITICAL |
| 4 | Default role is 'user' | "Default role - change via Firebase Console" | New user profiles get the lowest-privilege role by default; role elevation only possible through admin tools, never through the app UI. (e.g., Firebase: `role: 'user'` enforced by security rules; Supabase: RLS default; SQL: `DEFAULT 'user'` column constraint) | _[to be filled]_ | PATTERN | CRITICAL |
| 5 | Service init order critical | "CRITICAL: Import order matters - app must be initialized FIRST" | Backend service client must be initialized before dependent services (auth, database, storage) are instantiated; incorrect order causes runtime crashes. (e.g., Firebase: `initializeApp()` before `getAuth()` and `getFirestore()`) | _[to be filled]_ | PATTERN | CRITICAL |
| 6 | Popup/redirect sign-in flow | Code showing `signInWithPopup(auth, googleProvider)` | Use the auth provider's popup or redirect sign-in flow; catch errors and show user-friendly feedback on failure. (e.g., Firebase: `signInWithPopup`, Supabase: `signInWithOAuth`) | _[to be filled]_ | PATTERN | CRITICAL |
| 7 | Loading state during auth check | `const [loading, setLoading] = useState(true)` | App shows a loading state while the initial authentication check resolves; prevents flash of wrong content (unauthenticated UI shown to logged-in user or vice versa) | _[to be filled]_ | UNIVERSAL | STANDARD |

---

### Theme Context (Dark Mode)

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | localStorage persistence | Theme preference saved to localStorage | Read theme preference from `localStorage` on mount; save on toggle | _[to be filled]_ | UNIVERSAL | STANDARD |
| 2 | System preference fallback | Check `prefers-color-scheme: dark` | If no saved preference, check `window.matchMedia('(prefers-color-scheme: dark)')` for system default | _[to be filled]_ | UNIVERSAL | STANDARD |
| 3 | Class on html element | `.dark` class toggled on `document.documentElement` | Dark mode class toggled on the root HTML element to cascade through all components | _[to be filled]_ | UNIVERSAL | STANDARD |
| 4 | ThemeToggle component required | `ThemeToggle.tsx` in ui/ | A toggle button component that switches between light/dark themes; shows an icon indicating the opposite of current mode | _[to be filled]_ | UNIVERSAL | STANDARD |

---

### Route Guards

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | ProtectedRoute for auth users | `ProtectedRoute.tsx` | A route guard component that checks authentication state; redirects unauthenticated users to the login page; shows spinner while auth state is loading | _[to be filled]_ | UNIVERSAL | CRITICAL |
| 2 | AdminRoute for admin only | `AdminRoute.tsx` | Extends the auth route guard; also checks user role is `admin`; redirects non-admins to the dashboard | _[to be filled]_ | UNIVERSAL | CRITICAL |
| 3 | ProRoute for pro/admin | `ProRoute.tsx` (optional) | Checks user role is `pro` or `admin`; redirects others to dashboard or upgrade page | _[to be filled]_ | UNIVERSAL | STANDARD |
| 4 | Route wrapping order | "ProtectedRoute > Layout > Page" | Route guard components wrap layout, which wraps page content: `<RouteGuard><Layout><Page /></Layout></RouteGuard>` | _[to be filled]_ | UNIVERSAL | STANDARD |
| 5 | Provider nesting order | "AuthProvider > ThemeProvider > ToastProvider > BrowserRouter" | Global providers nested outermost to innermost: ErrorBoundary > AuthProvider > ThemeProvider > ToastProvider > Router > Routes | _[to be filled]_ | UNIVERSAL | STANDARD |

---

### Data Structure

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | User data scoped to user | "users/{uid}/{collectionName}/{documentId}" | All user-owned data scoped to the authenticated user; never stored in shared/global tables without user scoping. (e.g., document DB: `users/{uid}/{collection}/{docId}`, SQL: `WHERE user_id = ?`, Supabase: RLS policies) | _[to be filled]_ | PATTERN | CRITICAL |
| 2 | Helper for user data access | `getUserCollection(uid, collectionName)` | Utility function that abstracts database path/query construction for user-scoped data so access patterns are defined in one place. (e.g., Firebase: `getUserCollection(uid, name)` returns Firestore collection ref) | _[to be filled]_ | PATTERN | STANDARD |
| 3 | Server timestamps on all writes | "createdAt: serverTimestamp(), updatedAt: serverTimestamp()" | Every record creation includes both `createdAt` and `updatedAt` using the database's server-generated timestamp; every update sets `updatedAt` — never use client-side date generation for these fields. (e.g., Firebase: `serverTimestamp()`, Supabase: `now()`, SQL: `DEFAULT CURRENT_TIMESTAMP`) | _[to be filled]_ | PATTERN | CRITICAL |
| 4 | Default sort newest first | "orderBy('createdAt', 'desc')" | All collection/list queries default to descending `createdAt` order (newest first) | _[to be filled]_ | UNIVERSAL | POLISH |

---

### Data Service Layer

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | No database calls in components | "NO Firestore calls in components - use firestore service only" | All database/API operations go through a service layer module; UI components never import or call database client libraries directly. (e.g., Firebase: all calls through `services/firestore.ts`, Supabase: through `services/supabase.ts`) | _[to be filled]_ | PATTERN | STANDARD |
| 2 | CRUD helper functions | `addDocument`, `updateDocument`, `deleteDocument`, `getDocuments` | Four base CRUD functions wrapping database operations with automatic timestamp injection on creates and updates. (e.g., Firebase: `addDocument`/`updateDocument`/`deleteDocument`/`getDocuments` in `services/firestore.ts`) | _[to be filled]_ | PATTERN | STANDARD |
| 3 | Realtime subscription pattern | "return onSnapshot(q, ...)" | For realtime data, use the database's subscription/listener mechanism; map results to a normalized format; return an unsubscribe/cleanup function. (e.g., Firebase: `onSnapshot`, Supabase: `.on('*')`, Postgres: LISTEN/NOTIFY) | _[to be filled]_ | PATTERN | STANDARD |
| 4 | Delete account function | `deleteUserAccount(uid, subcollections[])` | Account deletion function that removes all user-owned data (iterating known data categories) before removing the user profile record; cascading delete must be explicit, not implicit. (e.g., Firebase: iterate subcollections then delete user doc; SQL: explicit DELETE per table) | _[to be filled]_ | PATTERN | CRITICAL |

---

### Routing Structure

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | Router wraps all routes | Uses `HashRouter` or `BrowserRouter` | Router component wraps all route definitions; public routes (landing, login) outside auth guards; choose hash or history routing based on hosting requirements | _[to be filled]_ | UNIVERSAL | STANDARD |
| 2 | Public vs protected routes | Landing and Login are public; Dashboard, Profile, CRUD pages are protected | Public routes: landing page, login. Protected routes: dashboard, profile, all CRUD pages. Clear separation enforced by route guards | _[to be filled]_ | UNIVERSAL | CRITICAL |
| 3 | 404 catch-all | `<Route path="*" element={<NotFoundPage />} />` | Last route definition catches all unmatched paths and renders a Not Found page | _[to be filled]_ | UNIVERSAL | STANDARD |
| 4 | CRUD route pattern | Detail, Create, Edit routes per entity | Standard CRUD routes per entity: `/items` (list), `/items/new` (create), `/items/:id` (detail), `/items/:id/edit` (edit) | _[to be filled]_ | UNIVERSAL | STANDARD |

---

### Data/API Patterns

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | Delete account removes all user data | "Delete all documents in each subcollection" | Account deletion function iterates all known user-data categories, deletes all records in each, then deletes the parent user profile record. (e.g., Firebase: iterate subcollections under `users/{uid}`, Supabase: cascade delete via RLS or explicit queries) | _[to be filled]_ | PATTERN | CRITICAL |
| 2 | Data category list is explicit | "List all subcollections your app uses" | Pass an explicit list of data category names (tables, collections, buckets) to the deletion function — no dynamic discovery of user data locations | _[to be filled]_ | UNIVERSAL | STANDARD |
| 3 | Realtime subscription pattern | "For realtime updates ... return onSnapshot(q, ...)" | Use the database's realtime subscription mechanism with an ordered query; map results to a normalized object format and return a cleanup/unsubscribe function. (e.g., Firebase: `onSnapshot`, Supabase: realtime channels) | _[to be filled]_ | PATTERN | STANDARD |
| 4 | CRUD helper layer | Code block showing `addDocument`, `updateDocument`, `deleteDocument`, `getDocuments` | Wrap all database operations in a service module with CRUD helper functions; every write automatically sets server-generated timestamps. (e.g., Firebase: `services/firestore.ts`, Supabase: `services/database.ts`) | _[to be filled]_ | PATTERN | STANDARD |
| 5 | Records always include timestamps | "createdAt: serverTimestamp(), updatedAt: serverTimestamp()" | Every database record must have `createdAt` (set on create) and `updatedAt` (set on create and every update) using the database's server-generated timestamp function — never client-side `new Date()`. (e.g., Firebase: `serverTimestamp()`, Supabase/SQL: `DEFAULT CURRENT_TIMESTAMP`) | _[to be filled]_ | PATTERN | CRITICAL |
| 6 | Default sort order | "orderBy('createdAt', 'desc')" | All list/collection queries default to descending `createdAt` order — newest first | _[to be filled]_ | UNIVERSAL | STANDARD |
| 7 | List pagination is mandatory | "Lists MUST handle large amounts of data" | Every list view must implement one of: pagination (10-20 items per page), load-more button, or infinite scroll. Pick ONE strategy and use it consistently across all lists | _[to be filled]_ | UNIVERSAL | STANDARD |
| 8 | Pagination controls pattern | "Show 10-20 items per page ... Pagination controls at bottom" | Use an `ITEMS_PER_PAGE` constant (e.g., 10), page state starting at 1, Previous/Next buttons disabled at bounds, "Page X of Y" label centered between buttons | _[to be filled]_ | UNIVERSAL | POLISH |
| 9 | Load-more shows remaining count | "Load More ({remaining} remaining)" | Load-more button must display how many items remain unloaded; initial limit of 10 items, increment by 10 on click | _[to be filled]_ | UNIVERSAL | POLISH |

---

### Authentication/Security

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | Delete account requires typed confirmation | "Type DELETE to confirm" | Account deletion requires the user to type an exact confirmation string (e.g., "DELETE") into a text input; submit button disabled until the string matches exactly | _[to be filled]_ | UNIVERSAL | CRITICAL |
| 2 | Delete button disabled during operation | "disabled={confirmText !== 'DELETE' \|\| isDeleting}" | Delete confirmation button must check both confirmation text match AND in-progress state; show "Deleting..." text while in progress | _[to be filled]_ | UNIVERSAL | STANDARD |
| 3 | Logout after account deletion | "await deleteUserAccount(user.uid, ...); await logout();" | After successful account deletion, immediately clear the auth session before showing success feedback | _[to be filled]_ | UNIVERSAL | CRITICAL |
| 4 | Protected routes wrap layout | "ProtectedRoute > Layout > Page" | All authenticated pages wrapped as RouteGuard > Layout > Page; public pages (landing, login) have no auth wrapper | _[to be filled]_ | UNIVERSAL | STANDARD |
| 5 | Auth/theme/toast providers wrap router | "AuthProvider > ThemeProvider > ToastProvider > BrowserRouter" | Provider nesting order (outermost to innermost): ErrorBoundary > AuthProvider > ThemeProvider > ToastProvider > Router > Routes | _[to be filled]_ | UNIVERSAL | STANDARD |
| 6 | Admin-only nav items are conditional | "isAdmin && <Link to='/admin'>Admin</Link>" | Navigation must conditionally render admin-only links based on the user's role; non-admins never see admin navigation | _[to be filled]_ | UNIVERSAL | CRITICAL |

---

### Database/Storage

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | User data scoped to owner | "getUserCollection(uid, collectionName)" | All user-owned data scoped to the authenticated user via user-specific paths, rows, or policies. (e.g., Firebase: `users/{uid}/{collection}/{docId}`, SQL: `WHERE user_id = ?`, Supabase: RLS) | _[to be filled]_ | PATTERN | CRITICAL |
| 2 | Delete cascades to all user data | "removes user profile and all subcollections" | Account deletion must remove all records in every known user-data category BEFORE deleting the parent user profile record | _[to be filled]_ | UNIVERSAL | CRITICAL |
| 3 | Batch deletes for efficiency | "const deletePromises = snapshot.docs.map(doc => deleteDoc(doc.ref)); await Promise.all(deletePromises);" | Bulk deletion fetches all records, maps to individual delete operations, then awaits all concurrently for each data category. (e.g., Firebase: `Promise.all` of `deleteDoc` calls, SQL: `DELETE FROM table WHERE user_id = ?`) | _[to be filled]_ | PATTERN | STANDARD |

---

### Error Handling

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | Delete failure keeps modal open | "catch (error) { showToast({ type: 'error', message: 'Failed to delete account' }); setIsDeleting(false); }" | On delete error: show error feedback, reset loading state, do NOT close the confirmation modal, do NOT navigate away | _[to be filled]_ | UNIVERSAL | STANDARD |
| 2 | Success feedback is toast + navigate | "Show success Toast ... Navigate to appropriate view" | Every successful mutation: show a success notification with descriptive message, then navigate to the next logical view | _[to be filled]_ | UNIVERSAL | STANDARD |
| 3 | Error feedback preserves form state | "Show error Toast with helpful message ... Stay on current view ... Keep form data intact" | On error: show error notification, remain on current view, do NOT clear or reset form data | _[to be filled]_ | UNIVERSAL | STANDARD |
| 4 | Delete flow is 6-step | "1. User clicks delete 2. ConfirmModal appears ... 3. User confirms 4. Show loading state on button 5. On success: Toast + redirect to List 6. On error: Toast + close modal" | Delete flow: click > confirmation dialog > confirm > button loading state + disabled > success notification + redirect to list, OR error notification + close modal | _[to be filled]_ | UNIVERSAL | STANDARD |
| 5 | Loading states match content shape | "Lists: Show Skeleton cards (not spinner) ... Detail View: Show Skeleton matching content layout ... Buttons during action: Show spinner inside button, disable button" | Lists show skeleton placeholders matching card shape, detail views show skeleton matching layout, action buttons show inline spinner and become disabled. Never use bare "Loading..." text | _[to be filled]_ | UNIVERSAL | STANDARD |

---

### Performance

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | Animations use short durations | "transition-opacity duration-200 ... transition-all duration-200 ease-out ... transition-transform duration-300 ease-out ... transition-all duration-150" | Modal backdrop: 200ms opacity. Modal content: 200ms ease-out. Toast: 300ms ease-out. Card hover: 200ms. Button press: 150ms. Never exceed 300ms for UI transitions | _[to be filled]_ | UNIVERSAL | POLISH |
| 2 | Card hover uses translate | "hover:shadow-md hover:-translate-y-0.5" | Card hover effect combines elevated shadow with a slight upward translate for a lift effect; use a 200ms transition | _[to be filled]_ | UNIVERSAL | POLISH |
| 3 | Button press uses scale | "active:scale-[0.98]" | Buttons must have a slight scale-down on press (e.g., 0.98) with a 150ms transition for tactile feedback | _[to be filled]_ | UNIVERSAL | POLISH |
| 4 | Choose one pagination strategy | "Choose ONE approach and implement it consistently" | Pick one list-handling strategy (pagination, load-more, or infinite scroll) and apply it to ALL list views in the app; do not mix approaches | _[to be filled]_ | UNIVERSAL | STANDARD |

---

### UX Standards

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | Six required UI components | "You MUST create and use these components. They are NOT optional: 1. Modal.tsx 2. ConfirmModal.tsx 3. Toast.tsx 4. ToastContext.tsx 5. Skeleton.tsx 6. EmptyState.tsx" | Create all six foundational UI components: Modal (overlay + close + title + content slots), ConfirmModal (destructive action confirmation dialog), Toast (success/error/info slide-in notification), ToastContext/Provider (global `showToast(message, type)` function), Skeleton (animated placeholder matching content shape), EmptyState (icon + message + CTA button) | _[to be filled]_ | UNIVERSAL | STANDARD |
| 2 | Browser dialogs are banned | "These are strictly forbidden. Using them fails the build: alert(), confirm(), prompt(), console.log for user feedback" | Never use `alert()`, `confirm()`, `prompt()`, or `console.log` for user-facing feedback. Use Toast for messages, ConfirmModal for confirmations, Modal for prompts | _[to be filled]_ | UNIVERSAL | STANDARD |
| 3 | Text-only empty states are banned | "Text-only empty states ... needs icon + CTA" | Empty states must use the EmptyState component with an icon/illustration, descriptive message, AND a call-to-action button. Plain "No items" text is forbidden | _[to be filled]_ | UNIVERSAL | STANDARD |
| 4 | Loading text is banned | "Loading states that are just the word 'Loading...'" | Never display bare "Loading..." text. Use Skeleton components that match the shape of the content being loaded | _[to be filled]_ | UNIVERSAL | STANDARD |
| 5 | List-Detail-Create-Edit flow | "Any data the user creates/saves MUST follow this pattern: List View ... Detail View ... Create View ... Edit View" | All user data CRUD must implement four distinct views: List (cards/rows + "Create New"), Detail (read-only + Edit/Delete/Share), Create (form, save > Detail), Edit (pre-filled form, save > Detail, cancel > Detail not List) | _[to be filled]_ | UNIVERSAL | STANDARD |
| 6 | No edit-first pattern | "Clicking saved item opens it in edit mode directly ... Using Create form as Edit form ... No way to view an item without editing it ... Single 'smart' component that handles both view and edit" | Items always open in read-only Detail view. Create and Edit are separate views/components. Never combine view+edit into one "smart" component | _[to be filled]_ | UNIVERSAL | STANDARD |
| 7 | Delete always requires confirmation | "Delete with no confirmation" listed as anti-pattern | Every delete action must go through a confirmation dialog with explicit user confirmation. No silent deletes | _[to be filled]_ | UNIVERSAL | STANDARD |
| 8 | Every action needs user feedback | "Success/error with no feedback to user" listed as anti-pattern | Every mutation (create, update, delete) must show either a success or error notification. No silent operations | _[to be filled]_ | UNIVERSAL | POLISH |
| 9 | Cancel-edit returns to detail | "Cancel returns to Detail View (not List)" | In Edit view, the Cancel button navigates back to the Detail view of the same item, not to the List view | _[to be filled]_ | UNIVERSAL | POLISH |
| 10 | Cancel-create returns to list | "Cancel returns to List View" | In Create view, the Cancel button navigates back to the List view | _[to be filled]_ | UNIVERSAL | POLISH |
| 11 | Never show raw timestamps | "Never show raw timestamps. Format dates for humans" | Create a date formatting utility. Display: "Just now" (<60s), "Xm ago" (<1h), "Xh ago" (<24h), "Yesterday" (24-48h), "Xd ago" (<7d), "Jan 15" (>7d same year), "Jan 15, 2024" (different year) | _[to be filled]_ | UNIVERSAL | STANDARD |
| 12 | Text truncation is mandatory | "Long text MUST be truncated to prevent layout breaking" | Sidebar items: truncate at ~30 chars. Card descriptions: clamp to 2 lines. Table cells: truncate at ~20 chars. Always pair truncation with a max-width value | _[to be filled]_ | UNIVERSAL | STANDARD |
| 13 | Back navigation on every sub-page | "Every detail/edit page MUST have back navigation" | Detail and Edit pages must have a back button at the top using either browser history back or an explicit link to the parent list route with a left arrow icon | _[to be filled]_ | UNIVERSAL | STANDARD |
| 14 | Five required animations | "Required animations: Modals: Fade in backdrop, scale up content. Toasts: Slide in from top-right. Cards: Subtle lift on hover. Buttons: Slight scale on press. Sidebar: Slide in on mobile" | Implement all five animation types: modal backdrop fade + content scale, toast slide-in, card hover lift, button press scale, sidebar mobile slide-in | _[to be filled]_ | UNIVERSAL | POLISH |
| 15 | Danger zone styling | "mt-12 pt-8 border-t border-red-200 ... text-red-600 ... bg-red-600 hover:bg-red-700" | Account deletion section visually separated from other settings with extra top spacing, a separator line, red-toned heading, and red-toned button. Labeled "Danger Zone" | _[to be filled]_ | UNIVERSAL | POLISH |
| 16 | Modal overlay pattern | "fixed inset-0 bg-black/50 flex items-center justify-center z-50" | Modals use fixed full-screen overlay with semi-transparent black background, flex centering, high z-index. Inner content: themed background, rounded corners, padding, max-width, responsive horizontal margin | _[to be filled]_ | UNIVERSAL | STANDARD |
| 17 | Focus states on all interactive elements | "All interactive elements need visible focus ... focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2" | Every button, link, and input must have visible focus indicators (e.g., focus ring in brand color with offset) | _[to be filled]_ | UNIVERSAL | STANDARD |
| 18 | Escape key closes modals | "Modals must handle Escape key" | Every modal must listen for the Escape key and close on press. Clean up listener on unmount | _[to be filled]_ | UNIVERSAL | STANDARD |
| 19 | Focus trap in modals | "Focus trap in modals - focus first element, trap Tab key" | Modals must trap keyboard focus: focus the first interactive element on open, cycle Tab within the modal only | _[to be filled]_ | UNIVERSAL | STANDARD |
| 20 | Icon buttons need aria-label | "Icon-only buttons need aria-label" | Every button containing only an icon (no visible text) must have an `aria-label` attribute describing the action (e.g., "Close modal", "Delete item") | _[to be filled]_ | UNIVERSAL | STANDARD |
| 21 | Screen reader loading states | "Loading states ... <span className='sr-only'>Loading...</span>" | Add screen-reader-only text alongside visual loading indicators so assistive technology can announce the loading state | _[to be filled]_ | UNIVERSAL | POLISH |
| 22 | Status updates use aria-live | "<div role='status' aria-live='polite'>{message}</div>" | Dynamic status messages must use appropriate ARIA roles (`role="status"`, `aria-live="polite"`) so screen readers announce changes | _[to be filled]_ | UNIVERSAL | POLISH |
| 23 | 404 catch-all route | "<Route path='*' element={<NotFoundPage />} />" | The router must include a catch-all route rendering a Not Found page for unmatched URLs | _[to be filled]_ | UNIVERSAL | STANDARD |

---

### Mobile/Responsive

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | Mobile-first design | "Build mobile-first. Design for mobile, then scale up for larger screens." | Write default styles for mobile; use progressive breakpoint prefixes to add tablet/desktop overrides | _[to be filled]_ | UNIVERSAL | STANDARD |
| 2 | Three breakpoints | "Mobile: < 640px (default styles, no prefix) ... Tablet: sm:640px and up ... Desktop: lg:1024px and up" | Define three breakpoints: mobile (default, < 640px), tablet (~640px+), desktop (~1024px+) | _[to be filled]_ | UNIVERSAL | STANDARD |
| 3 | Sidebar hidden on mobile | "Sidebar hidden by default on mobile ... Hamburger icon in header toggles sidebar" | Sidebar hidden by default on mobile; visible on desktop; mobile header has hamburger menu icon to toggle sidebar | _[to be filled]_ | UNIVERSAL | STANDARD |
| 4 | Sidebar is overlay on mobile | "Sidebar slides in as overlay (not push) ... Clicking outside or nav item closes sidebar ... Add close button inside mobile sidebar" | Mobile sidebar slides over content (not push layout), closes on outside click or nav item click, has a close button inside | _[to be filled]_ | UNIVERSAL | STANDARD |
| 5 | Cards stack vertically on mobile | "Cards: Full width, stack vertically (mobile) ... Grid 2-3 columns (desktop)" | Card grids: single column on mobile, 2 columns on tablet, 3 columns on desktop with consistent gap | _[to be filled]_ | UNIVERSAL | STANDARD |
| 6 | Forms full width on mobile | "Forms: Full width inputs (mobile) ... Max-width container (desktop)" | Form inputs: full width on mobile, constrained max-width on desktop | _[to be filled]_ | UNIVERSAL | STANDARD |
| 7 | Primary buttons full width on mobile | "Buttons: Full width for primary actions (mobile) ... Auto width (desktop)" | Primary action buttons: full width on mobile, auto/natural width on desktop | _[to be filled]_ | UNIVERSAL | STANDARD |
| 8 | Modals nearly full screen on mobile | "Modals: Full screen or nearly full (mobile) ... Centered, max-w-md (desktop)" | Modals on mobile should be full-screen or near-full; on desktop: centered with constrained max-width | _[to be filled]_ | UNIVERSAL | STANDARD |
| 9 | Minimum 16px text on mobile | "Text: Base size 16px minimum (mobile) ... Can be smaller (desktop)" | Body text must be at least 16px on mobile to prevent readability issues and iOS zoom; smaller sizes allowed only on desktop breakpoints | _[to be filled]_ | UNIVERSAL | STANDARD |
| 10 | 44px minimum touch targets | "Minimum 44px x 44px for all clickable elements on mobile ... Add padding to small icons/buttons to meet minimum ... Adequate spacing between touch targets" | All clickable elements must have a minimum touch area of 44x44px on mobile; add padding to small icons/buttons; ensure adequate spacing between adjacent targets | _[to be filled]_ | UNIVERSAL | STANDARD |
| 11 | Responsive visibility patterns | "hidden lg:block ... lg:hidden ... w-full lg:max-w-md ... p-4 lg:p-8" | Use responsive utility classes for: desktop-only content, mobile-only content, responsive widths, and responsive padding | _[to be filled]_ | UNIVERSAL | POLISH |
| 12 | Layout structure dimensions | "Sidebar: 240px wide, bg-surface-base, border-r ... Header: Full width, bg-surface-base, border-b, h-16 ... Main: flex-1, overflow-y-auto, p-8" | Sidebar: ~240px wide, themed background, right border. Header: full width, themed background, bottom border, ~64px height. Main content: flex-1, scrollable, padded | _[to be filled]_ | UNIVERSAL | POLISH |
| 13 | Sidebar has bottom help link | "Bottom section: help link (always visible) ... p-4 border-t border-border-subtle" | Sidebar must have a pinned bottom section with a separator border containing a Help & Support link with an icon | _[to be filled]_ | UNIVERSAL | POLISH |
| 14 | Padding scales with breakpoint | "p-4 lg:p-8" | Main content padding: smaller on mobile (e.g., 16px), larger on desktop (e.g., 32px) | _[to be filled]_ | UNIVERSAL | POLISH |

---

### Design System

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | Typography scale | "Page Title: 24px Semi-bold ... Section Header: 18px Semi-bold ... Card Title: 16px Medium ... Body Text: 14px Regular ... Small/Meta: 12px Regular" | Define a 5-level typography scale: Page Title (24px semi-bold), Section Header (18px semi-bold), Card Title (16px medium), Body Text (14px regular), Small/Meta (12px regular). Each level maps to semantic color tokens | _[to be filled]_ | UNIVERSAL | STANDARD |
| 2 | Spacing scale | "Card padding: p-6 (24px) ... Section gaps: gap-6 (24px) ... Element gaps: gap-4 (16px)" | Card internal padding: 24px. Between sections: 24px gap. Between elements within a section: 16px gap | _[to be filled]_ | UNIVERSAL | POLISH |
| 3 | Card component class | "bg-surface-base rounded-card border border-border-subtle shadow-card p-6" | Standard card: themed background, custom border radius, subtle border, custom shadow, 24px padding | _[to be filled]_ | UNIVERSAL | STANDARD |
| 4 | Primary button class | "bg-brand hover:bg-brand-dark text-text-primary font-medium px-6 py-3 rounded-lg transition-colors" | Primary button: brand color, darker brand on hover, primary text, medium weight, horizontal+vertical padding, rounded corners, color transition | _[to be filled]_ | UNIVERSAL | STANDARD |
| 5 | Input field class | "bg-surface-muted text-text-primary placeholder:text-text-tertiary px-4 py-3 rounded-lg w-full outline-none focus:ring-2 focus:ring-brand" | Text inputs: muted background, primary text, tertiary placeholder, padding, rounded corners, full width, brand-colored focus ring | _[to be filled]_ | UNIVERSAL | STANDARD |
| 6 | Sidebar nav item classes | "space-y-2 ... text-sm text-text-secondary hover:text-text-primary" | Nav links: vertical stack with small gaps, small text, secondary color, primary color on hover | _[to be filled]_ | UNIVERSAL | POLISH |
| 7 | Sidebar recent items section | "mt-6 ... text-xs font-medium text-text-tertiary mb-2" | Sidebar optional items section: top margin, extra-small bold heading in tertiary color, labeled "Recent Items" or similar | _[to be filled]_ | UNIVERSAL | POLISH |

---

### Testing

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | Console clean before deploy | "Production apps must have zero console errors/warnings" | Open browser DevTools Console, navigate through entire app, fix all red errors and yellow warnings until console is clean | _[to be filled]_ | UNIVERSAL | STANDARD |
| 2 | No console.log statements | "No `console.log` statements (use proper error handling)" | Remove all `console.log` calls from production code; use notification components or structured error handling instead | _[to be filled]_ | UNIVERSAL | STANDARD |
| 3 | No framework list key warnings | "No React key warnings (always use unique keys in lists)" | Every list rendering must provide a unique key per item; never use array index as key for dynamic lists. (e.g., React: `key` prop, Vue: `:key` binding) | _[to be filled]_ | PATTERN | STANDARD |
| 4 | No missing dependency warnings | "No missing dependency warnings (fix useEffect deps)" | All reactive hooks/watchers must have complete dependency declarations; fix or suppress with documented justification. (e.g., React: `useEffect` deps, Vue: `watch` sources) | _[to be filled]_ | PATTERN | POLISH |
| 5 | No unused variables | "No unused variable warnings" | Remove all unused imports, variables, and parameters; zero warnings in linter output | _[to be filled]_ | UNIVERSAL | POLISH |
| 6 | No type errors | "No TypeScript errors" | Type checker must pass with zero errors; no type-ignore/suppress comments without documented reason | _[to be filled]_ | UNIVERSAL | CRITICAL |
| 7 | Full app navigation test | "Navigate through entire app" | Before deploying, manually click through every route, form, modal, and interactive element to verify no console errors | _[to be filled]_ | UNIVERSAL | STANDARD |

---

### Deployment/Hosting

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | Config uses placeholder values | "Firebase config in firebase.ts with placeholder values" | Service configuration file ships with `YOUR_API_KEY`, `YOUR_PROJECT_ID`, etc. as string placeholders; never hardcode real credentials in source control. (e.g., Firebase: `config/firebase.ts` with placeholders, Supabase: `.env` with `SUPABASE_URL` and `SUPABASE_ANON_KEY`) | _[to be filled]_ | PATTERN | CRITICAL |
| 2 | Favicon required | "Every app needs a favicon. Add to index.html" | Create a favicon (SVG preferred) with the app's initial letter and brand color; link in the HTML head | _[to be filled]_ | UNIVERSAL | POLISH |
| 3 | Error boundary wraps app | "Wrap app in error boundary to prevent white screen of death" | A top-level error boundary component wraps the entire app; shows "Something went wrong" with a Refresh button on unhandled errors | _[to be filled]_ | UNIVERSAL | CRITICAL |
| 4 | Dependency config locked | "IMPORTMAP IS LOCKED. DO NOT MODIFY." | Do not add, remove, or change versions in the dependency configuration without explicit approval. (e.g., importmap, package.json, requirements.txt) | _[to be filled]_ | PATTERN | STANDARD |
| 5 | No redundant package entries | "DO NOT ADD firebase/app, firebase/auth, or firebase/firestore to the importmap! The 'firebase/' trailing slash handles ALL Firebase imports. Adding specific paths will BREAK the app." | Do not add redundant or conflicting sub-package entries when the parent package already resolves them. (e.g., Firebase: single `firebase/` entry handles all sub-imports) | _[to be filled]_ | PATTERN | STANDARD |

---

### Post-Generation Steps

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | Replace service config placeholders | "After generation, open `src/config/firebase.ts` and replace the placeholder values with your actual Firebase config from the Firebase Console." | Open the service configuration file and replace all `YOUR_*` placeholder strings with real values from the service provider's dashboard. (e.g., Firebase Console, Supabase Dashboard, AWS Console) | _[to be filled]_ | PATTERN | STANDARD |
| 2 | Replace favicon letter | "Replace 'A' with app's first letter and fill color with brand color." | Edit the favicon: change the letter to the app's initial and the background to the brand primary color | _[to be filled]_ | UNIVERSAL | POLISH |
| 3 | Replace app name in title hook | "const appName = 'AppName'; // Replace with your app name" | In the page title hook/utility, change the app name constant to the actual application name | _[to be filled]_ | UNIVERSAL | STANDARD |
| 4 | Set data category names for delete | "List all subcollections your app uses" | In the account deletion handler, update the data category list to include every user-data table/collection used by the app. (e.g., Firebase: subcollection names, SQL: table names) | _[to be filled]_ | PATTERN | STANDARD |
| 5 | Set help email | "mailto:support@yourdomain.com" | Replace the placeholder email in the Help & Support link with the real support email address | _[to be filled]_ | UNIVERSAL | STANDARD |

---

### Build Instructions

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | Complete file structure | "Create the complete file structure" | Generate all files listed in the file structure section; one component per file; group related components in feature folders | _[to be filled]_ | UNIVERSAL | STANDARD |
| 2 | Follow exact patterns | "Implement all components following the exact patterns" | Use the provided code patterns verbatim for: auth context, theme context, route guards, error boundary, data service layer, and all UI components | _[to be filled]_ | UNIVERSAL | STANDARD |
| 3 | Build Section 2 features | "Build the features described in Section 2" | Implement all core features from the app specification using the CRUD view pattern (List > Detail > Create > Edit) | _[to be filled]_ | UNIVERSAL | STANDARD |
| 4 | Apply design system styling | "Apply the styling from Section 3 using the design system" | Use the design tokens mapped to the CSS variable system; respect typography scale, spacing, card styles, and color tokens | _[to be filled]_ | UNIVERSAL | STANDARD |
| 5 | Auth and data access working | "Ensure all routes, auth flows, and Firestore operations work" | Sign-in flow, protected routes, database CRUD through the service layer, and role-based access must all function end-to-end. (e.g., Firebase: Google Sign-In + Firestore, Supabase: OAuth + Postgres) | _[to be filled]_ | PATTERN | CRITICAL |
| 6 | Production ready | "Make it production-ready with proper error handling" | ErrorBoundary, Toast feedback on all actions, ConfirmModal on destructive actions, Skeleton loading states, offline handling, session expiry handling | _[to be filled]_ | UNIVERSAL | CRITICAL |
| 7 | Single icon library | "Use Lucide React for all icons. Consistent style, tree-shakeable." | Import all icons from the project's designated icon library; use a consistent standard size; spinner icon with animation for loading states | _[to be filled]_ | STACK-SPECIFIC | POLISH |
| 8 | Dynamic page titles | "Update document title on each page" | Every page component updates `document.title` via a shared hook/utility to `"Page Name - AppName"` format | _[to be filled]_ | UNIVERSAL | POLISH |
| 9 | Autofocus on forms | "First input should be focused when page/modal loads" | Focus the first input field on page/modal mount; for modals, focus first input when opened | _[to be filled]_ | UNIVERSAL | POLISH |
| 10 | Pluralization helper | "Never show '1 items' - always handle plurals" | Create a `pluralize(count, singular, plural?)` utility function; use it everywhere counts are displayed | _[to be filled]_ | UNIVERSAL | POLISH |
| 11 | Search/filter for lists | "Any list that can grow needs search/filter" | Lists expected to exceed 5 items must include a search input filtering by title and description; show "No results for '...'" when filter yields empty | _[to be filled]_ | UNIVERSAL | POLISH |
| 12 | Retry on error states | "Error states should be actionable, not dead ends" | Every error display includes a "Try Again" button that re-invokes the failed operation; notifications may include a retry action | _[to be filled]_ | UNIVERSAL | STANDARD |
| 13 | Network/offline handling | "Handle Firebase/network errors gracefully" | Wrap database calls to catch network and permission errors with user-friendly messages; monitor `navigator.onLine` and show an offline banner. (e.g., Firebase: catch `unavailable` and `permission-denied` codes) | _[to be filled]_ | PATTERN | STANDARD |
| 14 | Session expiry handling | "Firebase tokens expire. Handle gracefully" | Catch authentication expiry errors in data access calls; show "Session expired" notification and redirect to login. (e.g., Firebase: catch `unauthenticated` errors, Supabase: handle JWT expiry) | _[to be filled]_ | PATTERN | CRITICAL |
| 15 | Loading button pattern | "Buttons during async actions must show loading state" | Button component accepts a `loading` prop; when true, show a spinner icon, update text, and set `disabled` | _[to be filled]_ | UNIVERSAL | POLISH |
| 16 | User avatar with fallback | "Google profile images can fail. Always have fallback" | Avatar component shows profile image with an `onError` handler that falls back to initials derived from the user's name (max 2 characters) | _[to be filled]_ | UNIVERSAL | POLISH |
| 17 | Form field states | "Forms need proper visual states" | Every form input handles 6 states: default (empty), focused (ring), filled, error (red border + message), disabled (reduced opacity), helper text | _[to be filled]_ | UNIVERSAL | STANDARD |
| 18 | Unsaved changes warning | "Warn users before losing form data" | Implement an unsaved-changes guard using `beforeunload` event for browser navigation; also intercept in-app navigation with a confirmation dialog | _[to be filled]_ | UNIVERSAL | STANDARD |
| 19 | 404 / not found handling | "Handle invalid routes and missing data" | Add a catch-all route for unmatched URLs; detail pages show an EmptyState with "Item not found" when the requested data doesn't exist | _[to be filled]_ | UNIVERSAL | STANDARD |
| 20 | Hover states on all interactives | "Every clickable element should visually respond to hover." | Cards: elevated shadow + slight translate; Buttons: darker shade; Links: underline; Icon buttons: muted background; Table rows: muted background; all with transitions | _[to be filled]_ | UNIVERSAL | POLISH |
| 21 | Date formatting | "Never show raw timestamps. Format dates for humans" | Create a date formatting utility returning relative time strings: "Just now", "5m ago", "2h ago", "Yesterday", "3d ago", "Jan 15", or "Jan 15, 2024" | _[to be filled]_ | UNIVERSAL | STANDARD |
| 22 | Text truncation | "Long text MUST be truncated to prevent layout breaking" | Sidebar items: truncate with max-width; Card descriptions: clamp to 2 lines; Table cells: truncate with max-width. Always set a max-width when truncating | _[to be filled]_ | UNIVERSAL | STANDARD |
| 23 | Back navigation | "Every detail/edit page MUST have back navigation" | Place a back button at the top of every detail/edit page using browser history back or explicit link to the parent list route | _[to be filled]_ | UNIVERSAL | STANDARD |
| 24 | Transitions and animations | "Add subtle animations for polish" | Required: modal fade/scale (200ms), toast slide-in (300ms), card hover lift (200ms), button press scale (150ms), sidebar slide on mobile | _[to be filled]_ | UNIVERSAL | POLISH |
| 25 | Accessibility - focus states | "All interactive elements need visible focus" | Apply visible focus indicators (focus ring in brand color with offset) to all buttons, inputs, and links | _[to be filled]_ | UNIVERSAL | STANDARD |
| 26 | Accessibility - keyboard nav | "Modals must handle Escape key" | Add keyboard listener for Escape to close modals; implement focus trap within modals (Tab cycles through modal elements only) | _[to be filled]_ | UNIVERSAL | STANDARD |
| 27 | Accessibility - icon buttons | "Icon-only buttons need aria-label" | Every button with only an icon (no visible text) must have an `aria-label` describing the action | _[to be filled]_ | UNIVERSAL | STANDARD |
| 28 | Accessibility - screen reader | "Loading states" need sr-only text | Add screen-reader-only text for visual-only loading indicators; use `role="status"` and `aria-live="polite"` for dynamic status text | _[to be filled]_ | UNIVERSAL | STANDARD |
| 29 | Pagination or load-more | "Lists MUST handle large amounts of data" | Choose ONE pagination approach (pagination / load more / infinite scroll) and implement consistently across all list views; 10-20 items per page | _[to be filled]_ | UNIVERSAL | STANDARD |
| 30 | CSS variables for dark mode | "DO NOT hardcode dark colors directly in Tailwind config. Use `var(--color-*)` references so the theme toggle works." | Define light mode values in `:root` and dark mode overrides in a toggled class; reference via CSS custom properties. Never hardcode color values directly in the styling framework config | _[to be filled]_ | UNIVERSAL | STANDARD |

---

### Miscellaneous Rules

| # | Rule | Martin Says | Technical Spec (Agnostic) | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|-------------------|------|----------|
| 1 | No database calls in components | "NO Firestore calls in components - use firestore service only" | All database/API operations go through a service layer module; components call service functions, never import database client libraries directly. (e.g., Firebase: no `firebase/firestore` imports in components) | _[to be filled]_ | PATTERN | STANDARD |
| 2 | No unprotected auth routes | "NO unprotected routes for authenticated features" | Every route that requires login must be wrapped in a route guard component | _[to be filled]_ | UNIVERSAL | CRITICAL |
| 3 | No inline styles | "NO inline styles - Tailwind only" | Never use inline `style` attributes; all styling via the project's designated styling methodology | _[to be filled]_ | UNIVERSAL | STANDARD |
| 4 | No `any` types | "NO `any` types - define TypeScript interfaces" | Define typed interfaces/schemas for all data shapes; no untyped (`any`) values in function signatures, state, or props | _[to be filled]_ | UNIVERSAL | STANDARD |
| 5 | Timestamps on all writes | "ALL Firestore writes include createdAt/updatedAt timestamps" | Every database create includes `createdAt` and `updatedAt` with server-generated timestamps; every update sets `updatedAt`. (e.g., Firebase: `serverTimestamp()`, Supabase: `now()` default column, SQL: `DEFAULT CURRENT_TIMESTAMP`) | _[to be filled]_ | PATTERN | CRITICAL |
| 6 | User data scoped to owner | "ALL user data in subcollections under users/{uid}/" | Never store user data in shared/global tables without user scoping; all user-owned data accessed via user-specific paths or filters. (e.g., Firebase: `users/{uid}/{collection}`, SQL: `WHERE user_id = ?`) | _[to be filled]_ | PATTERN | CRITICAL |
| 7 | Detail view separate from edit | "ALL saved items have Detail View (read-only) separate from Edit View" | Detail page is read-only display; editing happens on a separate route; never combine view and edit in one component | _[to be filled]_ | UNIVERSAL | STANDARD |
| 8 | Validate before submit | "ALL forms validate before submission" | Client-side validation on all required fields before calling the backend; show inline error messages per field | _[to be filled]_ | UNIVERSAL | CRITICAL |
| 9 | One component per file | "One component per file." | Each UI component lives in its own file; no multi-component files | _[to be filled]_ | UNIVERSAL | STANDARD |
| 10 | Feature folders for grouping | "Group related components in feature folders." | Related components go in feature-named directories; don't flatten everything into a single components folder | _[to be filled]_ | UNIVERSAL | STANDARD |
| 11 | Interfaces for all data types | "Create interfaces for all data types." | Every data shape used in the database, props, or state has a corresponding type definition in a centralized types file | _[to be filled]_ | UNIVERSAL | STANDARD |
| 12 | Custom hooks for reusable logic | "Add custom hooks for reusable logic." | Extract shared stateful logic into reusable hook/composable files; components should be thin wrappers over these abstractions | _[to be filled]_ | UNIVERSAL | POLISH |
| 13 | No pinned AI SDK versions | "DO NOT pin a version number. Let esm.sh resolve the latest compatible version." | When adding optional AI SDK dependencies, do not pin to a specific version unless required for stability; let the package manager resolve the latest compatible version. (e.g., `@google/genai` via esm.sh without version pin) | _[to be filled]_ | STACK-SPECIFIC | POLISH |
| 14 | Mobile-first responsive | "Build mobile-first. Design for mobile, then scale up for larger screens." | Default styles target mobile; use progressive breakpoint prefixes to add tablet/desktop overrides | _[to be filled]_ | UNIVERSAL | STANDARD |
| 15 | Touch targets 44px minimum | "Minimum 44px x 44px for all clickable elements on mobile" | Add padding to small icons/buttons to meet 44px minimum tap target; ensure adequate spacing between adjacent touch targets | _[to be filled]_ | UNIVERSAL | STANDARD |
| 16 | Service init order | "CRITICAL: Import order matters - app must be initialized FIRST" | Backend service client must be initialized before dependent services are instantiated; incorrect order causes runtime crashes. (e.g., Firebase: `initializeApp()` before `getAuth()` and `getFirestore()`) | _[to be filled]_ | PATTERN | CRITICAL |
| 17 | Role only editable via admin tools | "role only editable via Firebase Console" | Server-side data access rules must prevent users from modifying their own role; role changes only through admin tools or direct database access. (e.g., Firebase: security rules, Supabase: RLS policies, custom backend: admin-only endpoint) | _[to be filled]_ | PATTERN | CRITICAL |
| 18 | Default role is lowest privilege | "Default role - change via Firebase Console" | New user profiles are created with the lowest-privilege role; server-side rules enforce this default on create. (e.g., Firebase: security rules enforce `role == 'user'` on create) | _[to be filled]_ | PATTERN | CRITICAL |

---

### Complete Banned Patterns

Every prohibition Martin states across the entire document, collected into one list:

| # | Banned Pattern | Martin Says | Why Banned (Agnostic) | Type | Severity |
|---|----------------|-------------|----------------------|------|----------|
| 1 | No `alert()` | "No `alert()` -- use Toast for messages" | Native browser `alert()` blocks the UI thread and provides no styling control; use a Toast/notification component instead | UNIVERSAL | STANDARD |
| 2 | No `confirm()` | "No `confirm()` -- use ConfirmModal for confirmations" | Native browser `confirm()` blocks the UI thread and is not customizable; use a ConfirmModal component instead | UNIVERSAL | STANDARD |
| 3 | No `prompt()` | "No `prompt()` -- use a proper form Modal" | Native browser `prompt()` blocks the UI thread and provides no validation; use a Modal with a proper form instead | UNIVERSAL | STANDARD |
| 4 | No `console.log` for user feedback | "No `console.log` for user feedback -- use Toast" | Console output is invisible to users; use Toast/notification components for user-facing feedback | UNIVERSAL | POLISH |
| 5 | No text-only empty states | "No text-only empty states -- use EmptyState component with icon and CTA" | Plain "No items" text is a dead end; empty states need an icon, descriptive message, and call-to-action button | UNIVERSAL | POLISH |
| 6 | No browser default dialogs | "No browser default dialogs of any kind" | All native browser dialogs (`alert`, `confirm`, `prompt`, `beforeunload` default) replaced with custom UI components | UNIVERSAL | STANDARD |
| 7 | No external state libraries | "No external state libraries (Redux, Zustand, etc.) -- React Context only" | Use the framework's built-in state management; no third-party state libraries unless explicitly approved in project config | STACK-SPECIFIC | STANDARD |
| 8 | No containerization | "No Docker" | No Dockerfiles or containerization in the project scaffold; deployment handled by the configured hosting platform | STACK-SPECIFIC | STANDARD |
| 9 | No custom backend | "No backend APIs (Firebase/Firestore only)" | No custom server-side code; all backend functionality provided by the configured BaaS or serverless platform | STACK-SPECIFIC | STANDARD |
| 10 | No inline styles | "No inline styles -- Tailwind only" | Never use inline `style` attributes; all styling via the project's designated CSS methodology | UNIVERSAL | STANDARD |
| 11 | No `any` types | "No `any` types -- define TypeScript interfaces" | Define typed interfaces for all data shapes; no untyped values in function signatures, state, or props | UNIVERSAL | STANDARD |
| 12 | No database calls in components | "No Firestore calls in components -- use firestore service only" | UI components never import or call database client libraries directly; all data access through a service layer. (e.g., Firebase: no Firestore in components) | PATTERN | STANDARD |
| 13 | No unprotected auth routes | "No unprotected routes for authenticated features" | Every route requiring authentication must be wrapped in a route guard component | UNIVERSAL | CRITICAL |
| 14 | No hardcoded theme colors | "No hardcoded dark colors in Tailwind config -- use `var(--color-*)` references" | Never hardcode color values directly in the styling framework config; use CSS custom properties so theme toggling works | UNIVERSAL | STANDARD |
| 15 | No modifying locked dependencies | "No modifying the importmap (locked, copy exactly as shown)" | Dependency versions are locked; no changes without explicit approval | STACK-SPECIFIC | STANDARD |
| 16 | No redundant sub-package entries | "No adding `firebase/app`, `firebase/auth`, or `firebase/firestore` to the importmap individually" | Do not add redundant sub-package entries when the parent package already resolves them. (e.g., Firebase: single `firebase/` entry handles all sub-imports) | STACK-SPECIFIC | STANDARD |
| 17 | No pinned AI SDK versions | "No pinning version numbers for `@google/genai` in the importmap" | Do not pin optional AI SDK dependencies to specific versions unless required for stability | STACK-SPECIFIC | POLISH |
| 18 | No edit-first pattern | "No clicking a saved item to open it directly in edit mode" | Items always open in read-only Detail view first; Edit is a separate action and view | UNIVERSAL | STANDARD |
| 19 | No reusing Create form as Edit | "No using the Create form as the Edit form by pre-loading data" | Create and Edit are separate views/components; do not pre-load data into a Create form to simulate editing | UNIVERSAL | STANDARD |
| 20 | No view-only impossible | "No 'view-only impossible' pattern (must be able to view without editing)" | Users must be able to view any item without entering edit mode | UNIVERSAL | STANDARD |
| 21 | No combined view+edit component | "No single 'smart' component that handles both view and edit" | View (Detail) and Edit must be separate components; no mode-switching within a single component | UNIVERSAL | STANDARD |
| 22 | No delete without confirmation | "No delete without confirmation (ConfirmModal required)" | Every delete action must go through a confirmation dialog with explicit user confirmation | UNIVERSAL | STANDARD |
| 23 | No silent operations | "No success/error actions without feedback to user (Toast required)" | Every mutation must show success or error feedback via a notification component | UNIVERSAL | POLISH |
| 24 | No dead-end empty lists | "No empty lists with just 'No items' text (needs icon + CTA via EmptyState)" | Empty list states must include an icon, message, and call-to-action button via EmptyState component | UNIVERSAL | POLISH |
| 25 | No bare loading text | "No loading states that are just the word 'Loading...' (use Skeleton or spinner)" | Use Skeleton placeholders or spinner components, never bare "Loading..." text | UNIVERSAL | POLISH |
| 26 | No raw timestamps | "No raw timestamps displayed to users (use relative time formatting)" | All timestamps displayed as human-readable relative time via a formatting utility | UNIVERSAL | POLISH |
| 27 | No untruncated long text | "No untruncated long text (use `truncate` or `line-clamp-*`)" | Long text must be truncated or clamped to prevent layout breaking; always set a max-width constraint | UNIVERSAL | POLISH |
| 28 | No missing back navigation | "No detail/edit pages without back navigation" | Every detail/edit page must have a back button at the top | UNIVERSAL | POLISH |
| 29 | No list key warnings | "No React key warnings in console" | Every list rendering must provide unique keys; zero key-related warnings in console. (e.g., React: `key` prop, Vue: `:key`) | PATTERN | POLISH |
| 30 | No missing dependency warnings | "No missing useEffect dependency warnings" | All reactive hooks must have complete dependency arrays; zero dependency warnings. (e.g., React: `useEffect` deps) | PATTERN | POLISH |
| 31 | No unused variables | "No unused variable warnings" | Remove all unused imports, variables, and parameters; zero unused-variable warnings | UNIVERSAL | POLISH |
| 32 | No type errors in production | "No TypeScript errors in production" | Type checker must pass with zero errors before deployment | UNIVERSAL | CRITICAL |
| 33 | No writes without timestamps | "No Firestore writes without `createdAt`/`updatedAt` timestamps" | Every database write must include server-generated timestamps; creates set both `createdAt` and `updatedAt`; updates set `updatedAt`. (e.g., Firebase: `serverTimestamp()`) | PATTERN | CRITICAL |
| 34 | No unscoped user data | "No user data stored in top-level Firestore collections (must be subcollections under `users/{uid}/`)" | Never store user-owned data in shared/global tables without user scoping. (e.g., Firebase: nest under `users/{uid}/`, SQL: `user_id` foreign key) | PATTERN | CRITICAL |
| 35 | No unvalidated form submissions | "No forms without validation before submission" | All forms must validate required fields client-side before submitting; show inline error messages per field | UNIVERSAL | CRITICAL |
| 36 | No buttons without loading state | "No buttons without loading state during async actions" | Buttons triggering async operations must show a loading spinner and become disabled during the operation | UNIVERSAL | POLISH |
| 37 | No avatars without fallback | "No avatars without fallback for failed images" | Avatar components must handle image load failures by showing initials or a default icon | UNIVERSAL | POLISH |
| 38 | No pages without dynamic title | "No pages without dynamic document title (usePageTitle hook)" | Every page must update `document.title` via a shared utility to reflect the current page name | UNIVERSAL | POLISH |
| 39 | No forms without autofocus | "No forms without autofocus on first input" | The first input field in every form/modal must receive focus automatically on mount | UNIVERSAL | POLISH |
| 40 | No growable lists without search | "No growable lists without search/filter (when >5 items expected)" | Lists expected to exceed 5 items must include a search/filter input | UNIVERSAL | POLISH |
| 41 | No error dead ends | "No error states without retry action" | Every error display must include a "Try Again" button that re-invokes the failed operation | UNIVERSAL | POLISH |
| 42 | No mixed icon libraries | "No icons from libraries other than Lucide React" | Use a single, consistent icon library throughout the app; do not mix icons from different sources | STACK-SPECIFIC | POLISH |
| 43 | No console errors in production | "No console errors/warnings in production" | Zero console errors and warnings in the deployed app; navigate entire app in DevTools to verify | UNIVERSAL | STANDARD |

---

## Quality Verification Summary

### Rule Count
- **Category rules:** ~195 across 22 categories
- **Banned patterns:** 43
- **Total:** ~238

### Type Distribution
- **UNIVERSAL:** ~168 rules (principles that apply to any stack as-is)
- **STACK-SPECIFIC:** ~24 rules (rewritten from Firebase/React-specific to generic)
- **PATTERN:** ~46 rules (universal principle extracted, stack example noted)

### Severity Distribution
- **CRITICAL:** ~40 rules (security, auth, data integrity, build-breaking)
- **STANDARD:** ~141 rules (UX quality, component patterns, code organization)
- **POLISH:** ~59 rules (cosmetic, animation, spacing, naming)
