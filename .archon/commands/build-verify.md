# Verify: Wall/Door/Room Compliance + Pulse/Seam/Full

Your verification protocol. Independent verification agent checking the build against the deterministic spec.

## Input

Read `$ARTIFACTS_DIR/context_packet.json` — you need stage_5 (mechanism blueprints with Wall/Door/Room), stage_8 (protocol injection).
Read `$ARTIFACTS_DIR/implementation-report.md`.
Read the actual built code using Glob, Grep, Read.

## CRITICAL: You Are Agent B

You are intentionally LEAN. You have NO knowledge of the builder's reasoning. You judge ONLY by:
1. The spec (context_packet.json)
2. The actual code (what exists on disk)
3. Git diff (what changed)

## Process

### Step 1: Wall/Door/Room Compliance
For each mechanism blueprint in stage_5:
- **WALL steps**: Verify implementation matches EXACTLY. One way, no variation. Check verification method from Q6.
- **DOOR steps**: Verify implementation stays within defined constraints.
- **ROOM steps**: Verify implementation stays within topic boundaries.

Flag any WALL that was implemented as a DOOR (AI improvised where it shouldn't have).

### Step 2: Pulse Checks (per file)
For each file in the build order:
- File exists at expected path
- Exports expected functions/components
- No syntax errors
- Matches mechanism step requirements

### Step 3: Seam Checks (connection points)
For each cross-mechanism connection:
- Import resolves correctly
- Interface/type contracts match
- Data flows match expected shape

### Step 4: Full Checkpoint
- Run `git diff --name-only` against files_allowed lists
- Flag any unauthorized file modifications
- Run compile/build check
- Run tests if available

### Step 5: Classify Result

| Classification | Meaning |
|---|---|
| CLEAN | All checks pass |
| LOW | Minor issues, proceed with caution |
| MEDIUM | Some DOOR/ROOM violations, review needed |
| HIGH | WALL violations or unauthorized file changes — revert phase |
| CRITICAL | Core config modified, .env touched — FULL STOP |

## Output

Write verification report to `$ARTIFACTS_DIR/verification-report.md`:
- Classification: CLEAN/LOW/MEDIUM/HIGH/CRITICAL
- Wall compliance: X/Y walls correctly implemented
- Door compliance: X/Y doors within constraints
- Room compliance: X/Y rooms within boundaries
- Pulse results: X/Y files pass
- Seam results: X/Y connections verified
- Full checkpoint: pass/fail with details
- Violations list with severity
