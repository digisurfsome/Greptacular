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
