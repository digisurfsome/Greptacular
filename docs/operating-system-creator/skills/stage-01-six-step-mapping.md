# OS Automation Skills — Stage 1: 6-Step Mapping

> **What this does:** Takes the raw process from Stage 0 and maps it to the universal 6-step pattern: INPUT → PROCESS → OUTPUT → STATE → NOTIFY → SCHEDULE.

---

## When to Use

After Stage 0 is complete. Trigger: raw process has been captured and you need to identify the architecture pattern.

## Input

`stage_0` output — process name, data source, data destination, tools, failure modes.

## Process

### Step 1: Identify INPUT Type

Look at `stage_0.data_source` and match to one of these:

| Input Type | When It Applies |
|-----------|----------------|
| API call | Fresh data on demand from external service |
| Database query | Data already in your system from a previous step |
| Webhook listener | External system pushes data to you |
| File read | CSV, XLSX, JSON batch processing |
| Web scrape | Data on a public website to extract |
| Manual entry | Human provides starting data |
| Scheduled trigger | Time-based, runs at interval |

### Step 2: Identify PROCESS Type

What does the human brain DO with the data? Match to one of:

| Process Type | When It Applies |
|-------------|----------------|
| Generate content | Create text, code, documents from data |
| Classify/categorize | Sort incoming data into buckets |
| Score/rank | Assign numeric value to prioritize |
| Analyze/extract | Pull structured insights from unstructured data |
| Decide/route | Choose what happens next based on conditions |
| Transform | Convert data from one format to another |
| Compare | Check current state against thresholds or previous state |

**Critical rule:** If the PROCESS type involves real-world information, Claude ANALYZES data fed to it — Claude never RESEARCHES. Always have a data-gathering INPUT step before a Claude PROCESS step.

### Step 3: Identify OUTPUT Type

Where do results go? Match to one of:

| Output Type | When It Applies |
|------------|----------------|
| API push | Send to external service |
| Database write | Store for other steps or future reference |
| File export | Create downloadable artifact |
| Send message | Deliver to a person |
| Return to pipeline | Output becomes input to next step |
| Update settings | Change configuration in external tool |

### Step 4: Identify STATE Type

How is progress tracked?

| State Type | When It Applies |
|-----------|----------------|
| Database status field | Items move through stages (new → processing → done) |
| Event log table | Need audit trail of everything that happened |
| JSON state file | Simple single-machine tracking |
| CSV append log | Human-readable record |

**Rule:** Save incrementally, not at the end. After each item, not after all items.

### Step 5: Identify NOTIFY Type

Who needs to know, what do they need to know, how?

| Notify Type | When It Applies |
|------------|----------------|
| Telegram bot | Solo operator, instant mobile alerts |
| Email summary | Formal reporting, client-facing |
| Slack webhook | Team environment |
| Log file | Developer debugging only |
| Terminal output | During manual/CLI runs |

**Rule:** Always notify on completion AND on failure. Silent failures are worse than loud crashes.

### Step 6: Identify SCHEDULE Type

How does it run without the human?

| Schedule Type | When It Applies |
|--------------|----------------|
| Cron job | Simple, reliable, set times |
| Webhook trigger | Event-driven, runs when something happens |
| File watcher | Runs when new files appear |
| Manual CLI | Testing or low-volume |
| Queue system | High volume, process as items arrive |

### Step 7: Check for Multiple Levels

**Ask:** "Is this one phase or multiple?" If the process has distinct phases where Phase 1 output becomes Phase 2 input with different timing or triggers:
- Map each phase separately through Steps 1-6
- Document how phases connect (what output from Phase 1 feeds Phase 2)
- Note if phases can run independently or must be sequential

## Output

```json
{
  "stage_1": {
    "architecture": {
      "input_type": "string",
      "process_type": "string",
      "output_type": "string",
      "state_type": "string",
      "notify_type": "string",
      "schedule_type": "string"
    },
    "is_multi_phase": "boolean",
    "phases": [
      {
        "phase_name": "string",
        "input_type": "string",
        "process_type": "string",
        "output_type": "string",
        "connection_to_next": "string"
      }
    ],
    "architecture_diagram": "string (text diagram)"
  }
}
```

## Rules

1. Every process maps to this pattern. No exceptions. If it doesn't seem to fit, you're looking at it wrong.
2. Multi-phase systems are common. Always ask.
3. The architecture diagram is a simple text flowchart — not fancy, just clear.
