# OS Automation Skills — Stage 5: Error Handling & Validation

> **What this does:** Defines what happens when things go wrong — retries, rollback, quality gates, and recovery for every step.

---

## When to Use

After Stage 4. You know the full pipeline and environment. Now bulletproof it.

## Input

`stage_2` steps (with error cases) + `stage_4` rate limits and API details.

## Process

### Step 1: Error Matrix

For EACH step, fill out:

| Field | What to Capture |
|-------|----------------|
| **What can fail?** | API down, rate limited, bad data, timeout, auth expired, empty result |
| **How do you detect it?** | HTTP status code, empty response, validation check, timeout |
| **What's the action?** | Retry / skip / alert / pause / stop everything |
| **Retry strategy** | How many times? With what delay? Exponential backoff? |
| **Fallback** | Is there an alternative if the primary fails? |

### Step 2: Quality Gates

For steps that produce output that could be wrong but "succeed":

| Question | Answer |
|----------|--------|
| How do you know the output is good? | "Classification is one of the valid categories" / "Score is 0-100" / "File has > 0 rows" |
| What makes output unacceptable? | "Empty result" / "All items scored the same" / "JSON parse fails" |
| What happens on bad quality? | Retry with different parameters / flag for human review / skip |

### Step 3: Rollback & Redo

| Question | Answer |
|----------|--------|
| Can this step be re-run safely? | Yes (idempotent) / No (side effects) / Partially |
| What needs to be undone first? | Delete previous output / Reset status / Nothing |
| Can old items be reprocessed with a new prompt/config? | Yes / No |
| How is versioning handled? | Overwrite / Append with timestamp / Keep all versions |

### Step 4: Data Retention

| Question | Answer |
|----------|--------|
| How long is raw data kept? | Forever / 90 days / 30 days / until processed |
| How long are results kept? | Forever / 1 year / until archived |
| When does archiving happen? | Never / monthly / when DB exceeds X rows |
| Is there PII that needs special handling? | Yes (what?) / No |

### Step 5: Cascade Failures

If Step 2 fails, what happens to Steps 3, 4, 5?

| Failure Point | Impact | Action |
|--------------|--------|--------|
| Step 1 fails | Nothing else can run | Alert and stop |
| Step 2 fails for one item | Other items continue | Skip item, log, continue |
| Step 3 fails | Output incomplete | Alert, deliver partial results |

## Output

```json
{
  "stage_5": {
    "error_matrix": [
      {
        "step_number": 1,
        "failure_modes": [
          {
            "what_fails": "string",
            "detection": "string",
            "action": "retry | skip | alert | pause | stop",
            "retry_strategy": "string",
            "fallback": "string"
          }
        ]
      }
    ],
    "quality_gates": [
      {
        "step_number": 1,
        "good_output": "string",
        "bad_output": "string",
        "bad_action": "string"
      }
    ],
    "rollback": {
      "idempotent_steps": [1, 3, 5],
      "side_effect_steps": [2, 4],
      "versioning": "overwrite | append | keep_all"
    },
    "data_retention": {
      "raw_data": "string",
      "results": "string",
      "archive_trigger": "string",
      "pii_present": "boolean"
    },
    "cascade_rules": [
      {"failure_point": "string", "impact": "string", "action": "string"}
    ]
  }
}
```

## Rules

1. Every step MUST have at least one failure mode documented. If you think a step can't fail, you haven't thought hard enough.
2. Default to "skip and continue" over "stop everything" unless data integrity is at risk.
3. Rate limit errors are ALWAYS retryable with exponential backoff. Never treat 429 as a permanent failure.
