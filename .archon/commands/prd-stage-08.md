# Stage 8: Protocol Injection

You are a verification protocol specialist. Your job is to inject three tiers of verification checkpoints into the phased build orders, producing self-verifying build units.

## Input

Read `$ARTIFACTS_DIR/context_packet.json`. You need `stage_5.mechanism_blueprints` (for Wall/Door/Room classifications), `stage_7.phases` (for build orders and file sandboxes).

## Process

### Step 1: Inject PULSE Checks (Light — After Every File)

For each file in each phase's build order, generate specific verification checks:
- File exists at expected path
- File exports expected functions/components (derived from mechanism blueprints)
- No syntax errors
- Matches Wall classification requirements (if applicable)

These are NOT generic. Each pulse check references the specific mechanism step it validates.

### Step 2: Inject SEAM Checks (Medium — At Connection Points)

Place at every point where one mechanism's file imports from another mechanism's file:
- Import resolves correctly
- Interface/type contracts match
- Data flows match expected shape

If no cross-mechanism connections exist in a phase, zero seam checks (valid).

### Step 3: Inject FULL Checkpoint (Heavy — End of Each Phase)

Four-part checkpoint:
1. **Pattern check**: `git diff` against `files_allowed` — flag any unauthorized file modifications
2. **Compile check**: Framework-specific build/compile command
3. **Functional check**: Route verification, render checks, API endpoint validation
4. **Gate condition**: ALL must pass before next phase begins

### Step 4: Define Violation Handling (4 Levels Per Phase)

| Level | Trigger | Response |
|-------|---------|----------|
| LOW | Touched shared types file | Log and proceed |
| MEDIUM | Modified another phase's file | Review: additive = proceed with caution, destructive = revert file |
| HIGH | Deleted files, modified core config | Revert entire phase |
| CRITICAL | Modified .env, CLAUDE.md, build config | FULL STOP — human review |

### Step 5: Calculate Overhead

Target ~25K tokens per phase for all protocol overhead:
- Build rules preamble: ~8K
- File sandbox declaration: ~2K
- Build order + pulse checks: ~3K
- Seam checks: ~2K
- Full checkpoint: ~5K
- Pattern verification: ~3K
- Violation handling: ~2K

## Output

Update `$ARTIFACTS_DIR/context_packet.json` — add `stage_8`:

```json
{
  "stage_8": {
    "protocol_injected_phases": [
      {
        "phase_number": 1,
        "pulse_checks": [
          {"after_file": "src/lib/db/schema.ts", "checks": ["file exists", "exports UserSchema"]}
        ],
        "seam_checks": [
          {"provider": "auth.ts", "consumer": "AuthContext.tsx", "validates": "loginUser export"}
        ],
        "full_checkpoint": {
          "pattern_check": "git diff --name-only against files_allowed",
          "compile_check": "npm run build",
          "functional_checks": [],
          "gate": "ALL_MUST_PASS"
        },
        "violation_rules": {
          "low": [], "medium": [], "high": [], "critical": []
        },
        "overhead_tokens": 25000
      }
    ],
    "stage_contract": "pass"
  }
}
```

IMPORTANT: Read existing context_packet.json, merge stage_8, increment version to 8, write back.
