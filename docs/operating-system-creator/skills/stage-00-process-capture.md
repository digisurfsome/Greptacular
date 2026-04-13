# OS Automation Skills — Stage 0: Process Capture

> **What this does:** Captures the raw description of the manual process being automated. This is the intake — get everything on paper before organizing.

---

## When to Use

First stage. Always runs first. Trigger: user describes a process they want to automate, provides a video transcript of a process, or points to documentation of a workflow.

## Input

Raw description from the user. Can be:
- Voice transcript (messy, with filler words — that's fine)
- Written description
- Video transcript run through a transcription tool
- Existing documentation or SOP
- Chat conversation describing the process

## Process

### Step 1: Capture Raw Input

Record everything exactly as stated. Do NOT filter, organize, or clean up. Contradictions, tangents, and repetitions are valuable — they reveal what the user actually cares about vs. what they think they should say.

### Step 2: Extract Process Identity

From the raw input, identify:

| Field | Question | Example |
|-------|----------|---------|
| **Process name** | What would you call this in 3-5 words? | "Email Warmup Manager" |
| **Trigger** | What causes this process to start? | "New mailbox created" / "Daily at 8am" / "When I remember" |
| **Frequency** | How often does this run? | "Multiple times daily" / "Weekly" / "On-demand" |
| **Duration** | How long does one full run take a human? | "30-45 minutes" |
| **Volume** | How many items per run? | "10-20 mailboxes" |
| **Pain level** | What sucks most about doing this manually? | "Forgetting to check a flagged mailbox" |

### Step 3: Extract Data Endpoints

| Field | Question |
|-------|----------|
| **Starting data** | Where does the input come from? (API, file, inbox, manual, database, web) |
| **End result** | Where does the output go? (Tool, database, file, person, dashboard) |
| **Tools in use** | What services/tools are involved today? For each: does it have an API? |

### Step 4: Capture What Breaks

Ask: "What goes wrong most often? What's the most expensive mistake? What do you dread about this process?"

Record every failure mode mentioned. These become the error handling rules later.

## Output

```json
{
  "stage_0": {
    "raw_input": "full unedited text",
    "process_name": "string",
    "trigger": "string",
    "frequency": "string",
    "duration_minutes": "number",
    "volume_per_run": "string",
    "pain_points": ["string"],
    "data_source": "string",
    "data_destination": "string",
    "tools_in_use": [{"name": "string", "has_api": "boolean"}],
    "failure_modes": ["string"],
    "word_count": "number"
  }
}
```

## Rules

1. Never filter the raw input. Capture everything.
2. If the user can't answer a question, mark it `"unknown"` and move on. Never block.
3. Pain points and failure modes are the most important fields — they drive the entire build priority.
