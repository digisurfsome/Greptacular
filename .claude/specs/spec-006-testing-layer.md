# Spec 006 — Testing Layer (5 Levels)

## What This Is
A 5-level testing system for Code Module nodes. Each level catches a different class of problem. A node must pass all 5 levels before it can be promoted from `draft` to `stable`. The gate is automated — not a manual judgment call.

## Why It Matters
The biggest time sink in any development workflow is "it seemed to work but it doesn't." The testing layer catches schema mismatches before a node runs, catches logic errors before they hit real APIs, and catches integration failures before they hit production. Each level is faster to fix than the next — you want to fail at Level 1, not Level 5.

---

## Level 1 — Schema Validation (Before the Node Runs)

**What it catches:** Wrong input types, missing required fields, output that doesn't match the declared shape.

**When it runs:** Immediately when the node config is saved (before any code executes).

```typescript
// src/lib/validation/schema-validator.ts

interface NodeSchema {
  inputFields: Record<string, { type: string; required: boolean }>
  outputShape: Record<string, string>
}

export function validateInputSchema(input: unknown, schema: NodeSchema): ValidationResult {
  const errors: string[] = []

  for (const [field, config] of Object.entries(schema.inputFields)) {
    if (config.required && (input as any)[field] === undefined) {
      errors.push(`Missing required field: ${field}`)
    }
    if ((input as any)[field] !== undefined) {
      const actualType = typeof (input as any)[field]
      if (actualType !== config.type) {
        errors.push(`Field ${field}: expected ${config.type}, got ${actualType}`)
      }
    }
  }

  return { valid: errors.length === 0, errors }
}

export function validateOutputSchema(output: unknown, schema: NodeSchema): ValidationResult {
  const errors: string[] = []

  for (const [field, expectedType] of Object.entries(schema.outputShape)) {
    if ((output as any)[field] === undefined) {
      errors.push(`Output missing field: ${field}`)
    } else {
      const actualType = typeof (output as any)[field]
      if (actualType !== expectedType) {
        errors.push(`Output field ${field}: expected ${expectedType}, got ${actualType}`)
      }
    }
  }

  return { valid: errors.length === 0, errors }
}
```

**Passing condition:** Zero schema errors. All required fields present. All types match declarations.

---

## Level 2 — Mock Mode (Test Logic Without Real APIs)

**What it catches:** Logic errors, null pointer errors, unexpected data transformations — without actually calling Gmail/Slack/external APIs.

**When it runs:** On demand (before connecting real credentials to the node).

Mock mode intercepts external calls and returns synthetic data shaped like real responses:

```typescript
// src/lib/testing/mock-runner.ts

const MOCK_RESPONSES: Record<string, unknown> = {
  'gmail.send_email': { success: true, messageId: 'mock_msg_123' },
  'slack.send_message': { ok: true, ts: '1234567890.123' },
  'http.send_http_request': { status: 200, body: { mock: true } },
  'anthropic.ask_claude': { content: 'Mock LLM response for testing.' }
}

export async function runInMockMode(
  nodeCode: string,
  testInput: unknown,
  stepName: string
): Promise<MockRunResult> {
  // Replace external API calls with mock responses
  const mockContext = {
    ...realContext,
    externalCall: (piece: string, action: string) => {
      const key = `${piece}.${action}`
      return MOCK_RESPONSES[key] ?? { mock: true, note: `No mock for ${key}` }
    }
  }

  try {
    const fn = new Function('input', 'context', nodeCode)
    const output = await fn(testInput, mockContext)
    return { passed: true, output, errors: [] }
  } catch (err) {
    return { passed: false, output: null, errors: [(err as Error).message] }
  }
}
```

**Passing condition:** Node executes without throwing. Output is non-null and has the right shape. No unhandled exceptions.

---

## Level 3 — Auto-Generated Unit Tests

**What it catches:** The specific cases the node is supposed to handle, tested against the exact examples the user provided in Step 7 of the 7-step form.

**When it runs:** Automatically generated at build time from the `success_definition` field.

### Test Generation

When Claude generates the node code, it also generates test cases:

```
From the success_definition in the 7-step form:
"Input: { url: 'https://youtube.com/watch?v=abc123' }
Expected output: { transcript: 'Hello world this is a test video...', word_count: 7 }"

Claude generates:
```

```typescript
// tests/code-module/[node-name].test.ts
import { describe, it, expect } from '@jest/globals'
import { nodeFunction } from '../../pieces/code-module/src/lib/generated/[node-name]'

describe('[node-name] unit tests', () => {

  it('happy path — processes valid input correctly', async () => {
    const input = { url: 'https://youtube.com/watch?v=abc123' }
    const output = await nodeFunction(input, mockContext)
    expect(output.transcript).toBeDefined()
    expect(typeof output.transcript).toBe('string')
    expect(output.word_count).toBeGreaterThan(0)
  })

  it('handles null input gracefully', async () => {
    await expect(nodeFunction(null, mockContext)).rejects.toThrow()
    // OR: returns error object without throwing — depending on declared failure handling
  })

  it('handles empty URL', async () => {
    const output = await nodeFunction({ url: '' }, mockContext)
    expect(output).toHaveProperty('error')   // declared failure case
  })

})
```

**Passing condition:** All auto-generated test cases pass. Run with: `npm test tests/code-module/[node-name].test.ts`

---

## Level 4 — Regression Gate (draft → stable Promotion)

**What it catches:** Regressions when code is edited. A node that previously passed its tests now fails after a change.

**When it runs:** Every time `generated_code` is modified. Blocks promotion to `stable` if any test fails.

```python
# copilot/quality_gate.py

def attempt_stable_promotion(node_name: str, node_code: str) -> PromotionResult:
    """
    Try to promote a node from draft to stable.
    All 4 previous levels must pass.
    """
    results = {
        "level_1_schema": run_schema_validation(node_name, node_code),
        "level_2_mock": run_mock_mode(node_name, node_code),
        "level_3_unit": run_unit_tests(node_name),
    }

    all_passed = all(r["passed"] for r in results.values())

    if all_passed:
        # Update quality_status in the flow's node config
        update_node_quality_status(node_name, "stable")
        return PromotionResult(success=True, results=results)
    else:
        failed_levels = [k for k, v in results.items() if not v["passed"]]
        return PromotionResult(
            success=False,
            results=results,
            message=f"Cannot promote. Failed: {', '.join(failed_levels)}"
        )
```

**Passing condition:** All of Levels 1-3 pass after the most recent code change. Status updates to `stable` automatically.

---

## Level 5 — Pipeline Integration Test

**What it catches:** The node works in isolation but breaks something in the full flow. Upstream data shape doesn't match what the node expects. Node's output shape doesn't match what downstream expects.

**When it runs:** Before any pipeline is activated for real use. Run manually or triggered by "Go Live" button in the skin.

```python
# copilot/integration_test.py

def run_pipeline_integration_test(flow_id: str, test_payload: dict) -> IntegrationResult:
    """
    Run the complete flow with mock data, check each step's output feeds correctly into the next.
    """
    # Trigger the flow with mock data (AP's built-in test run feature)
    run_resp = requests.post(f"{AP_BASE}/api/v1/flow-runs", headers=HEADERS, json={
        "flowId": flow_id,
        "projectId": PROJECT_ID,
        "payload": test_payload,
        "environment": "TEST"   # uses mock connections
    })
    run_id = run_resp.json()["id"]

    # Poll for completion
    result = poll_until_complete(run_id, timeout_seconds=60)

    # Check each step
    step_issues = []
    for step in result["steps"]:
        if step["status"] == "FAILED":
            step_issues.append({
                "step": step["name"],
                "error": step["errorMessage"],
                "input": step["input"],   # what it received
                "expected_input_shape": get_node_input_schema(step["name"])
            })

    return IntegrationResult(
        passed=len(step_issues) == 0,
        step_issues=step_issues,
        full_run_output=result["output"]
    )
```

**Passing condition:** The flow runs end-to-end with test data. Every step executes. No step receives data of the wrong shape. Final output matches the expected shape.

---

## The Full Quality Gate Summary

| Level | Catches | When | Time |
|-------|---------|------|------|
| 1 — Schema | Wrong types, missing fields | On config save | Instant |
| 2 — Mock | Logic errors, null crashes | On demand | < 5 sec |
| 3 — Unit | Specific cases from Step 7 | On code save | < 10 sec |
| 4 — Regression | Breaks after edits | On code change | < 15 sec |
| 5 — Integration | Step output/input mismatches | Before go-live | < 60 sec |

**Total time to know a node is stable: under 2 minutes.**

---

## The Quality Status Flow

```
Code written  →  draft
                  ↓
         Run Levels 1-4 (automated)
                  ↓
         All pass?
         ↓         ↓
       YES          NO
        ↓            ↓
      stable    Keep as draft
        ↓       Show which level failed
  Run Level 5   Fix → re-run
  (integration)
        ↓
     All pass?
     ↓       ↓
   YES        NO
    ↓          ↓
 promoted   Back to stable
 Save key    (integration
 functions   issue to fix)
 to mechanism
 library
```

---

## Success Criteria

- [ ] Level 1 catches a missing required field and shows a clear error message
- [ ] Level 2 runs the node with mock API responses and reports pass/fail
- [ ] Level 3 test file is auto-generated from Step 7 of the 7-step form
- [ ] `npm test` on the generated test file runs and shows results
- [ ] Editing `generated_code` triggers Level 4 and blocks promotion if tests fail
- [ ] Level 5 runs the full flow with test payload and reports which step failed and why
- [ ] `quality_status` updates to `stable` automatically when Levels 1-4 pass
- [ ] A node that fails Level 3 cannot be marked stable (blocked at the gate)
