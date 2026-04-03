# Two-Strike Bash Script Pattern

## Purpose

Bash implementation of the two-strike retry rule for automated (Agent B) verification. Copy this pattern into `build.sh` generation in Stage 10.

## Script Pattern

```bash
#!/bin/bash
set -euo pipefail

# ============================================================
# Two-Strike Verification Loop
# If a phase fails HIGH/CRITICAL twice, stop for human review.
# ============================================================

PHASE_NUMBER=$1
PHASE_FILE="phases/phase-${PHASE_NUMBER}.md"
BASELINE_TAG="phase-${PHASE_NUMBER}-baseline"

# Capture baseline before phase starts
git tag -f "$BASELINE_TAG" HEAD

run_phase() {
    local attempt=$1
    echo "=== Phase ${PHASE_NUMBER}, Attempt ${attempt} ==="

    # Run builder agent (Agent A)
    # Replace with actual agent invocation command
    claude --prompt-file "$PHASE_FILE" \
           --permission-mode acceptEdits \
           --settings-file .claude/settings.json

    # Capture diff
    git diff "${BASELINE_TAG}..HEAD" --name-only > "phase-${PHASE_NUMBER}-diff.txt"

    # Run functional checks
    run_functional_checks "$PHASE_NUMBER" > "phase-${PHASE_NUMBER}-checks.txt" 2>&1
    FUNC_EXIT=$?

    # Run Agent B (verifier)
    CLASSIFICATION=$(run_agent_b \
        --allowed-files "phases/phase-${PHASE_NUMBER}-allowed.txt" \
        --diff-output "phase-${PHASE_NUMBER}-diff.txt" \
        --functional-results "phase-${PHASE_NUMBER}-checks.txt" \
        --violation-tree "violation-rules.json" \
        --pattern-log "agent-b-pattern-log.txt" \
    | grep "CLASSIFICATION:" | cut -d' ' -f2)

    echo "Phase ${PHASE_NUMBER} classification: ${CLASSIFICATION}"
    echo "$CLASSIFICATION"
}

# --- Attempt 1 ---
RESULT=$(run_phase 1)

if [ "$RESULT" = "HIGH" ] || [ "$RESULT" = "CRITICAL" ]; then
    echo "!!! Phase ${PHASE_NUMBER} FAILED verification (${RESULT}). Reverting..."
    git reset --hard "$BASELINE_TAG"

    # --- Attempt 2 (fresh agent, clean context) ---
    RESULT=$(run_phase 2)

    if [ "$RESULT" = "HIGH" ] || [ "$RESULT" = "CRITICAL" ]; then
        echo "!!! Phase ${PHASE_NUMBER} FAILED TWICE (${RESULT}). STOPPING FOR HUMAN REVIEW."
        git reset --hard "$BASELINE_TAG"

        # Write failure report
        cat > "phase-${PHASE_NUMBER}-failure-report.txt" <<REPORT
PHASE: ${PHASE_NUMBER}
STATUS: FAILED_TWICE
CLASSIFICATION: ${RESULT}
ACTION_REQUIRED: Human review needed.
REASON: Two fresh agents failed the same phase. The problem is likely the phase specification, not the agents.
SUGGESTED_ACTIONS:
  1. Review the phase spec for ambiguity or contradictions
  2. Check if files_allowed is too restrictive
  3. Check if the phase scope is too large (consider splitting)
  4. Review the functional check expectations
REPORT

        exit 1
    fi
fi

# If we get here, phase passed (CLEAN, LOW, or MEDIUM)
echo "Phase ${PHASE_NUMBER} PASSED verification: ${RESULT}"

# Tag the successful completion
git tag -f "phase-${PHASE_NUMBER}-complete" HEAD
```

## Functional Check Helper

```bash
run_functional_checks() {
    local phase=$1
    local exit_code=0

    echo "--- Compile Check ---"
    # Tech-stack-specific: replace with actual commands
    npm run build 2>&1 || exit_code=1

    echo "--- Test Check ---"
    if [ -f "package.json" ] && grep -q '"test"' package.json; then
        npm run test 2>&1 || exit_code=1
    else
        echo "No test script found. Skipping."
    fi

    echo "--- Render Check ---"
    # For web apps: start dev server, check routes, stop
    # This is tech-stack-specific and may use curl or playwright
    echo "Render check: manual verification required for web apps"

    return $exit_code
}
```

## Key Rules

1. **max_retries = 2. Always.** Do not make this configurable. Three retries waste tokens and almost never succeed when two have failed.
2. **Fresh agent on retry.** The retried Agent A has zero memory of the first attempt. Clean context, clean slate.
3. **Revert before retry.** `git reset --hard $BASELINE_TAG` ensures the second attempt starts from the exact same state as the first.
4. **Exit 1 on double failure.** The build script stops. A human must read the failure report and intervene.
5. **Tag baselines.** Every phase gets a git tag before it starts. This is the rollback point.

## Integration Notes

- Stage 10 fills in the actual agent invocation commands based on `stage_0.tech_stack`
- Stage 10 fills in the actual functional check commands
- The `run_agent_b` function is a wrapper around the Agent B prompt from `agent-b-config-template.md`
- The pattern log (`agent-b-pattern-log.txt`) persists across phases for Agent B's cumulative awareness
