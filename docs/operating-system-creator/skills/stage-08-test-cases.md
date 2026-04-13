# OS Automation Skills — Stage 8: Test Cases & Health Checks

> **What this does:** Defines exactly how to verify the system works — sample test data, health check commands, and ongoing monitoring.

---

## When to Use

After Stage 7. The build plan exists. Now define how to prove it works.

## Input

All previous stages — steps, environment, build order.

## Process

### Step 1: Sample Test Case

Provide ONE real, concrete example that can be used to test the entire pipeline end-to-end:

| Field | What to Provide |
|-------|----------------|
| **Test input** | A real URL, file, data point, or query to process |
| **Expected behavior** | What should happen at each step |
| **Expected output** | What the final result should look like |
| **How to verify** | Check database? Check file? Check Telegram? |

Example: "Use `test@testdomain.com` as a mailbox. After running `check`, it should appear in the status table with status `warming`, day 1, volume 5."

### Step 2: Testing Checklist

Numbered list of manual verification steps:

```
1. [ ] [setup command] — creates initial record
2. [ ] [main command] — runs full pipeline, no errors
3. [ ] [status command] — shows results in table
4. [ ] [specific check] — verify specific behavior
5. [ ] [error test] — intentionally trigger an error, verify handling
6. [ ] [rerun test] — run again, verify deduplication works
7. [ ] [notification test] — check Telegram received message
8. [ ] [export test] — verify output file is created and correct
```

### Step 3: Health Check Commands

Commands the operator can run anytime to verify the system is healthy:

| Command | What It Checks | Healthy Output |
|---------|---------------|----------------|
| `[tool] status` | Overall system state | All items showing recent timestamps |
| `[tool] health` | API connections | "All 3 APIs responding" |
| `node -e "require('./src/db')"` | Database connection | No errors |
| `curl [api-endpoint]` | Specific API reachable | 200 response |

### Step 4: Ongoing Monitoring

What should be checked regularly after deployment?

| Check | Frequency | What to Look For |
|-------|-----------|-----------------|
| Error log | Daily | Any new errors since last check |
| API costs | Weekly | Spending within budget |
| Data volume | Monthly | Database not growing unbounded |
| Output quality | Weekly | Spot-check 5 random outputs |

### Step 5: Regression Tests

After changing prompts, thresholds, or logic:

| What Changed | What to Re-test |
|-------------|----------------|
| Claude prompt | Run 5 sample items, compare output to previous |
| Threshold value | Test items near the old and new boundary |
| New API version | Run full pipeline, compare results |
| New step added | Run full pipeline, verify existing steps unaffected |

## Output

```json
{
  "stage_8": {
    "sample_test": {
      "input": "string",
      "expected_behavior": "string",
      "expected_output": "string",
      "verification": "string"
    },
    "testing_checklist": [
      {"step": "number", "command": "string", "expected": "string"}
    ],
    "health_checks": [
      {"command": "string", "what": "string", "healthy": "string"}
    ],
    "ongoing_monitoring": [
      {"check": "string", "frequency": "string", "look_for": "string"}
    ],
    "regression_tests": [
      {"change_type": "string", "retest": "string"}
    ]
  }
}
```

## Rules

1. The sample test case must be REAL, not hypothetical. A real URL, a real email, a real search query.
2. The testing checklist must be runnable by someone who didn't build the system.
3. Every test should have a clear pass/fail — no "check if it looks right."
