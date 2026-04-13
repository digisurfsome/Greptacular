# OS Automation Skills — Stage 2: Step Decomposition

> **What this does:** Breaks each step (or phase) into granular detail — inputs, outputs, decisions, error cases. This is where the process goes from "I do stuff" to "here's exactly what happens."

---

## When to Use

After Stage 1. For each step identified in the 6-step mapping, decompose it fully.

## Input

`stage_1` output — architecture mapping, phases if multi-phase.

## Process

**Repeat this entire section for EACH step in the process.**

### For Each Step, Answer:

| # | Question | What It Captures |
|---|----------|-----------------|
| 1 | **What does the human do?** | Exact action — "They search Apollo for companies in construction with 10-50 employees" |
| 2 | **What data does this step need to start?** | Input — from previous step, a tool, a file, a person? |
| 3 | **What decisions does the human make?** | Judgment calls — "They decide if the lead is a good fit based on company size" |
| 4 | **Could Claude make this decision?** | Yes with clear rules / Yes but needs judgment / No, must stay human |
| 5 | **What's the output?** | What gets produced — a list? A score? A file? A yes/no? |
| 6 | **Where does that output go?** | Next step / database / API / file / person / multiple |
| 7 | **Is there an API tool for this?** | Search "[need] API" — what exists? Cost? |
| 8 | **What's the error case?** | What happens when it fails? Skip / retry / alert / stop? |
| 9 | **How long does this take a human?** | Minutes per item — prioritize longest steps |
| 10 | **Does this step repeat N times?** | Fixed count or variable? Per item? Per filter? |
| 11 | **Does the option list grow over time?** | Are there extensible categories/filters/templates? |

### After All Steps Are Decomposed, Ask:

- **Can multiple items be batch-processed together?** Or must each item go through individually?
- **Are there common combinations that should be saved as presets?** (e.g., "always run steps 1, 3, and 5 together")
- **Is there a step that's the MVP?** Which single step, if automated, gives the most relief?

## Output

```json
{
  "stage_2": {
    "steps": [
      {
        "step_number": 1,
        "name": "string",
        "human_action": "string",
        "input_needed": "string",
        "decisions": ["string"],
        "claude_can_decide": "yes_with_rules | yes_with_judgment | no",
        "decision_rules": "string (if yes)",
        "output": "string",
        "output_destination": "string",
        "api_tool": {"name": "string", "cost": "string", "notes": "string"},
        "error_case": "string",
        "error_action": "skip | retry | alert | stop",
        "human_time_minutes": "number",
        "repeats": "boolean",
        "repeat_count": "fixed N | variable | per_item",
        "extensible_options": "boolean",
        "option_examples": ["string"]
      }
    ],
    "supports_batch": "boolean",
    "presets": [
      {"name": "string", "steps_included": [1, 3, 5]}
    ],
    "mvp_step": "number",
    "mvp_reasoning": "string"
  }
}
```

## Rules

1. Be brutally specific. "They check the data" is not a step. "They compare bounce rate against 2% threshold and pause if exceeded" is a step.
2. Every decision the human makes must be captured. If you miss a decision, the automation will make the wrong choice silently.
3. The MVP step is the one with the highest (human_time × frequency × pain_level). Automate that first.
