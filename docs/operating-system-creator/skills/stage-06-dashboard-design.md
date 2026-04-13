# OS Automation Skills — Stage 6: Dashboard Design

> **What this does:** Defines what the operator needs to SEE — the monitoring interface. For automations, this is a terminal dashboard, not a web app. Shows status, health, errors, and key metrics at a glance.

---

## When to Use

After Stage 5. You know all the steps, what can fail, and what gets tracked. Now design what the operator looks at.

## Input

`stage_2` steps + `stage_5` error handling + `stage_0` process identity.

## Process

### Step 1: Identify the Operator's Questions

What does the person running this system need to know at a glance?

Common questions for any automation:

| Question | What Answers It |
|----------|----------------|
| "Is it running?" | Status indicator (running / idle / error / paused) |
| "When did it last run?" | Timestamp of last execution |
| "Did anything fail?" | Error count, last error message |
| "What's it doing right now?" | Current step, items processed / total |
| "How's it performing?" | Key metrics (success rate, items/hour, cost so far) |
| "Do I need to do anything?" | Action items, alerts requiring human response |

### Step 2: Define Key Metrics

Pick 3-5 metrics that matter most for THIS specific automation:

| Metric | Example | Update Frequency |
|--------|---------|-----------------|
| Primary throughput | "Leads processed: 142 today" | Per run |
| Error rate | "Bounce rate: 1.2%" | Per run |
| Cost tracker | "API spend: $0.47 today" | Per run |
| Quality indicator | "Avg score: 72/100" | Per run |
| Trend | "↑ 15% vs last week" | Daily |

### Step 3: Terminal Dashboard Layout

Design the CLI output when user runs `[tool] status`:

```
┌─────────────────────────────────────────────┐
│  [SYSTEM NAME] — Status Dashboard           │
├─────────────────────────────────────────────┤
│  Status: ● RUNNING    Last run: 2 min ago   │
│  Next run: in 3h 58m  Errors: 0             │
├─────────────────────────────────────────────┤
│  [KEY METRICS TABLE]                        │
│  Metric 1: value    Metric 2: value         │
│  Metric 3: value    Metric 4: value         │
├─────────────────────────────────────────────┤
│  [ITEMS TABLE - recent items with status]   │
│  Name | Status | Score | Last Check         │
│  item1 | ● OK  | 85    | 5 min ago          │
│  item2 | ⚠ WARN | 42   | 5 min ago          │
│  item3 | ● OK  | 91    | 5 min ago          │
├─────────────────────────────────────────────┤
│  [ALERTS - if any]                          │
│  ⚠ item2 score dropped below threshold      │
└─────────────────────────────────────────────┘
```

### Step 4: Interaction Points

What can the operator DO from the dashboard?

| Action | Command | What It Does |
|--------|---------|-------------|
| View status | `[tool] status` | Show dashboard |
| Force run | `[tool] run` | Run pipeline now |
| Pause item | `[tool] pause [name]` | Pause specific item |
| View details | `[tool] report [name]` | Detailed view of one item |
| View history | `[tool] history` | Recent runs with results |

### Step 5: Notification Thresholds

What triggers an alert vs. just showing up on the dashboard?

| Severity | When | Action |
|----------|------|--------|
| Info | Normal completion | Show on dashboard only |
| Warning | Metric crosses threshold | Dashboard + Telegram |
| Critical | Failure or dangerous metric | Dashboard + Telegram + pause if needed |

## Output

```json
{
  "stage_6": {
    "operator_questions": ["string"],
    "key_metrics": [
      {"name": "string", "example": "string", "update_frequency": "string"}
    ],
    "dashboard_layout": "string (ASCII mockup)",
    "cli_commands": [
      {"command": "string", "description": "string"}
    ],
    "notification_thresholds": [
      {"severity": "string", "condition": "string", "action": "string"}
    ]
  }
}
```

## Rules

1. Keep it simple. 3-5 metrics max on the main dashboard. Details go in sub-commands.
2. Color coding: green = healthy, yellow = warning, red = critical. Universal.
3. The dashboard must answer "do I need to do anything?" within 2 seconds of looking at it.
4. Terminal dashboards use cli-table3 or similar. No web framework needed.
