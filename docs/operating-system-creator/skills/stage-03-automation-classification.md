# OS Automation Skills — Stage 3: Automation Classification

> **What this does:** For each step from Stage 2, classifies HOW it gets automated — pure code, AI-driven, or must stay human. This determines what gets built and what gets prompted.

---

## When to Use

After Stage 2. Every decomposed step needs a classification.

## Input

`stage_2` output — all steps with their decisions, inputs, outputs.

## Process

### For Each Step, Classify:

| Classification | When It Applies | Example |
|---------------|----------------|---------|
| **Deterministic (Code)** | Fixed rules, no judgment, same input always produces same output | "If bounce rate > 5%, pause mailbox" |
| **AI-Driven (Claude)** | Needs language understanding, pattern recognition, or content generation | "Read this email and classify as interested/not interested/wrong person" |
| **Hybrid** | Code handles the logic, Claude handles one specific sub-task within it | "Code fetches all emails, Claude classifies each one, code routes based on classification" |
| **Human Required** | Subjective judgment, legal liability, or relationship-dependent | "Decide whether to fire this client" |
| **External API** | A third-party service handles it entirely | "MillionVerifier validates the email address" |

### For AI-Driven Steps, Capture the Prompt Skeleton:

The prompt IS the product for AI steps. Capture:

| Field | What to Record |
|-------|---------------|
| **Task** | What Claude is being asked to do (classify, generate, analyze, score) |
| **Input format** | What data gets fed to Claude (raw text, JSON, structured fields) |
| **Output format** | What Claude should return (JSON with specific fields, plain text, score) |
| **Model recommendation** | Haiku (cheap, fast, simple tasks) / Sonnet (balanced) / Opus (complex reasoning) |
| **Cost estimate** | Approximate cost per call based on input/output token counts |
| **Example** | One concrete input → expected output pair |

### For Deterministic Steps, Capture the Logic:

| Field | What to Record |
|-------|---------------|
| **Condition** | The if/then rule |
| **Thresholds** | Any numeric values that trigger actions |
| **Lookup tables** | Any mapping tables (warmup day → volume) |
| **Bash/CLI possible?** | Could this be a simple bash command instead of code? |

## Output

```json
{
  "stage_3": {
    "classifications": [
      {
        "step_number": 1,
        "step_name": "string",
        "classification": "deterministic | ai_driven | hybrid | human_required | external_api",
        "prompt_skeleton": {
          "task": "string",
          "input_format": "string",
          "output_format": "string",
          "model": "haiku | sonnet | opus",
          "cost_per_call": "string",
          "example_input": "string",
          "example_output": "string"
        },
        "deterministic_logic": {
          "conditions": ["string"],
          "thresholds": {"name": "value"},
          "lookup_tables": ["string"],
          "bash_possible": "boolean"
        }
      }
    ],
    "ai_step_count": "number",
    "deterministic_step_count": "number",
    "human_step_count": "number",
    "estimated_cost_per_run": "string"
  }
}
```

## Rules

1. Default to deterministic. Only use AI when the task genuinely requires language understanding. Don't use Claude to compare numbers.
2. Every AI step MUST have a prompt skeleton. No "Claude figures it out" hand-waving.
3. Always estimate cost. Haiku ≈ $0.001/call, Sonnet ≈ $0.01/call, Opus ≈ $0.05/call. Multiply by volume.
