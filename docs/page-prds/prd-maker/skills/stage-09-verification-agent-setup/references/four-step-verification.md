# Four-Step End-of-Phase Verification Protocol

## Overview

Every phase ends with this 4-step verification. It is identical for automated and manual modes — only the delivery wrapper differs.

## The Protocol

### Step 1: Self-Report

The builder agent lists every file it created, modified, or deleted during the phase.

**Input**: Agent's own memory of what it changed.
**Compare against**: `files_allowed` from the phase spec.
**Output format**:
```
FILES_CREATED:
- src/lib/auth.ts
- src/contexts/AuthContext.tsx

FILES_MODIFIED:
- src/App.tsx (added routes)

FILES_DELETED:
(none)
```

**Why this exists**: First-pass sanity check. Fast, but unreliable — agents can forget files or hallucinate changes. This is a courtesy check, NOT ground truth.

### Step 2: Diff Check (Ground Truth)

Run the deterministic git diff command.

**Command**: `git diff PHASE_N_BASELINE..HEAD --name-only`

**Compare against**:
1. The self-report from Step 1
2. The `files_allowed` list from the phase spec

**Mismatch handling**:
- File in diff but NOT in self-report: Agent forgot to mention it. This is a violation (agent honesty failure).
- File in self-report but NOT in diff: Agent hallucinated a change. Flag but not critical.
- File in diff but NOT in `files_allowed`: Unauthorized file change. Classify using violation tree.

**Why this is ground truth**: `git diff` is mechanical. It cannot lie, cannot forget, cannot hallucinate. It captures every byte that changed.

### Step 3: Violation Response

For every unauthorized file (in diff but NOT in `files_allowed`), apply the violation decision tree from `stage_8.protocol_injected_phases[N].violation_rules`:

| Severity | Example | Action |
|----------|---------|--------|
| LOW | Touched a shared `types.ts` to add an export | Log it. Note in phase report. Proceed. |
| MEDIUM | Modified a file from another phase's domain | STOP. If additive (added export/prop): log + proceed with caution. If destructive (renamed, changed logic): revert that file to baseline. |
| HIGH | Deleted files, modified core config, changed auth logic | REVERT ENTIRE PHASE. Re-run with tighter constraints. |
| CRITICAL | Modified `.env`, `CLAUDE.md`, build config, environment files | FULL STOP. REVERT. FLAG. Human must intervene. |

### Step 4: Functional Checks

Run tech-stack-appropriate verification commands.

#### Command Mapping

| Tech Stack | Compile Check | Test Check | Lint Check |
|------------|--------------|------------|------------|
| Node/React/Next.js | `npm run build` | `npm run test` | `npm run lint` |
| Python/Django/Flask | `python -m py_compile {files}` | `python -m pytest` | `ruff check .` |
| Rust | `cargo build` | `cargo test` | `cargo clippy` |
| Go | `go build ./...` | `go test ./...` | `golangci-lint run` |
| Flutter/Dart | `flutter build` | `flutter test` | `flutter analyze` |

#### Render & Route Checks (Web Apps)

For phases that create UI pages:
- **Render check**: Do new pages/components render without errors? (Check browser console for React errors, 500s, blank screens)
- **Route check**: Can you navigate to expected routes? (e.g., `/sign-in` returns 200, not 404)

#### Expected Outcomes

Each functional check has a specific pass condition:
- Compile: exits with code 0
- Test: 0 failures (warnings OK)
- Lint: 0 errors (warnings OK)
- Render: no runtime errors in console
- Route: expected routes return 200

**ALL FOUR STEPS MUST PASS BEFORE THE NEXT PHASE BEGINS.**

---

## Complete Example: React + TypeScript App (3 Phases)

### Phase 1: Auth System

**Allowed files**: `src/lib/auth.ts`, `src/contexts/AuthContext.tsx`, `src/pages/SignIn.tsx`, `src/pages/SignUp.tsx`, `src/App.tsx`

**Automated flow (Agent B)**:
1. Agent A builds auth system
2. `git diff phase-1-baseline..HEAD --name-only` returns:
   ```
   src/lib/auth.ts
   src/contexts/AuthContext.tsx
   src/pages/SignIn.tsx
   src/pages/SignUp.tsx
   src/App.tsx
   ```
3. Agent B compares: all 5 files are in allowed list. Zero unauthorized files.
4. Functional checks: `npm run build` exits 0. No tests yet (Phase 1 override: `skip_test_check: true`).
5. **Classification: CLEAN**. Proceed to Phase 2.

**Manual flow**: Phase 1 has no preamble (no prior phase to validate). Phase 2 will open with Phase 1 validation.

### Phase 2: Dashboard + Data Layer

**Allowed files**: `src/pages/Dashboard.tsx`, `src/hooks/useData.ts`, `src/lib/api.ts`, `src/components/DataTable.tsx`

**Automated flow (Agent B)**:
1. Agent A builds dashboard
2. `git diff phase-2-baseline..HEAD --name-only` returns:
   ```
   src/pages/Dashboard.tsx
   src/hooks/useData.ts
   src/lib/api.ts
   src/components/DataTable.tsx
   src/lib/types.ts          <-- NOT in allowed list
   ```
3. Agent B compares: 4 files match, 1 unauthorized (`types.ts`).
4. Agent B checks violation tree: `types.ts` is a shared types file. Classification: **LOW**.
5. Functional checks: `npm run build` exits 0. `npm run test` exits 0 (auth tests from Phase 1 still pass).
6. **Classification: LOW**. Log drift, proceed to Phase 3.
7. Pattern log: `"Phase 2: LOW — types.ts touched (shared type added)"`

**Manual flow (Phase 2 prompt opens with)**:
```
## Pre-Phase Validation (Phase 1 Deliverables)
Before starting Phase 2 work, validate Phase 1:
Run: git diff phase-1-baseline..HEAD --name-only
Expected: src/lib/auth.ts, src/contexts/AuthContext.tsx, src/pages/SignIn.tsx, src/pages/SignUp.tsx, src/App.tsx
Run: npm run build (expect exit 0)
Navigate to /sign-in and /sign-up (expect pages render)
```
Agent finds Phase 1 clean. Proceeds with Phase 2 work.

### Phase 3: Payments

**Allowed files**: `src/pages/Checkout.tsx`, `src/lib/payments.ts`, `src/components/PaymentForm.tsx`

**Automated flow (Agent B) — failure scenario**:
1. Agent A builds payments
2. `git diff phase-3-baseline..HEAD --name-only` returns:
   ```
   src/pages/Checkout.tsx
   src/lib/payments.ts
   src/components/PaymentForm.tsx
   src/lib/auth.ts            <-- Phase 1's file! NOT in allowed list
   .env                       <-- CRITICAL
   ```
3. Agent B compares: 3 files match, 2 unauthorized.
4. `src/lib/auth.ts` = modified another phase's file = MEDIUM/HIGH.
5. `.env` = environment file = **CRITICAL**.
6. Functional checks skipped (CRITICAL already determined).
7. **Classification: CRITICAL**. Trigger revert.

**Revert + retry**:
1. `git reset --hard phase-3-baseline`
2. Fresh Agent A (new context, no memory of failed attempt)
3. Fresh Agent A builds payments without touching auth.ts or .env
4. Agent B verifies: CLEAN
5. **Phase 3 passes on second attempt.**

**If second attempt also failed**: STOP. Write failure report. Human reviews Phase 3 spec.
