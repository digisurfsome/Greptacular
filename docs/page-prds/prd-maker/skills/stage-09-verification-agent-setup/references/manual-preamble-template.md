# Manual Preamble Template

## Purpose

For users pasting prompts into Claude Code web/desktop (no bash automation), verification of Phase N is merged as a 30-second preamble into Phase N+1's prompt. This avoids doubling the agent count.

## Template

The following template is inserted at the TOP of Phase N+1's prompt, before the phase's own work begins. Replace `{N}` with the previous phase number and fill in the phase-specific values.

```markdown
## Pre-Phase Validation (Phase {N} Deliverables)

Before starting Phase {N+1} work, validate that Phase {N} was completed correctly.

### File Check
Run: `git diff {PHASE_N_BASELINE}..HEAD --name-only`

Expected files (Phase {N} allowed list):
{ALLOWED_FILES_LIST — one per line}

**If any file in the diff is NOT in the expected list above:**
- Shared types/config file (e.g., types.ts, index.ts) -> Note it, proceed
- File from a different phase's domain -> STOP. Revert that file: `git checkout {PHASE_N_BASELINE} -- {file}`
- Core system file (.env, CLAUDE.md, build config) -> STOP. Revert ALL Phase {N} changes: `git reset --hard {PHASE_N_BASELINE}` and redo Phase {N} from scratch

### Functional Check
Run these commands and verify they pass:
{FUNCTIONAL_COMMANDS — one per line with expected outcome}

Example:
- `npm run build` -> exits with code 0
- `npm run test` -> all tests pass (0 failures)
- Navigate to {EXPECTED_ROUTES} -> pages render without errors

### Verdict
- All files match + all checks pass -> Proceed with Phase {N+1} work below
- Minor issues (1-2 extra shared files, warnings but no errors) -> Fix inline, then proceed
- Major issues (wrong files modified, build fails, tests fail) -> Fix ALL issues before starting Phase {N+1}

---
## Phase {N+1}: {PHASE_NAME}
{... Phase N+1's actual instructions follow ...}
```

## Customization Rules

1. **`ALLOWED_FILES_LIST`**: Copy directly from `stage_7.phases[N].files_allowed`. One file per line.
2. **`FUNCTIONAL_COMMANDS`**: Derive from `stage_0.tech_stack`:
   - Node/React: `npm run build`, `npm run test`, route checks
   - Python: `python -m pytest`, `ruff check .`, `mypy .`
   - Rust: `cargo build`, `cargo test`
   - Go: `go build ./...`, `go test ./...`
3. **`EXPECTED_ROUTES`**: Derive from the pages/routes created in Phase N (from `stage_6.sub_6b` mapped to phases in Stage 7).
4. **`PHASE_N_BASELINE`**: The git commit hash or tag created before Phase N started. In practice, this is set by the build script or manually noted.

## Duration Estimate

The preamble check takes approximately 30 seconds of the agent's time:
- Read the diff output: ~5 seconds
- Compare against allowed list: ~10 seconds
- Run functional checks (if not already run): ~10 seconds
- Make pass/fix/redo decision: ~5 seconds

This is negligible compared to the 10-30 minutes a typical phase takes.

## Agent Count Impact

| Approach | Phases | Agents | Idle Gaps |
|----------|--------|--------|-----------|
| Separate checker agents | 4 | 8 (4 build + 4 check) | 4 gaps (5-25 min each) |
| Preamble merge | 4 | 4 (each checks previous) | 0 extra gaps |

The preamble approach saves 4 idle gaps and halves the agent sessions for manual users.

## Edge Case: Phase 1

Phase 1 has no previous phase to validate. Its prompt does NOT include the preamble. The preamble first appears in Phase 2's prompt (validating Phase 1).

## Edge Case: Final Phase

The final phase's output has no "next phase" to validate it. For manual users, the final phase should include its own self-validation step at the end (the standard 4-step protocol runs as an epilogue rather than as the next phase's preamble).
