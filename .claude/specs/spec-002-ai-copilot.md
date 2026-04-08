# Spec 002 — AI Co-Pilot (Plain English → Built Pipeline)

## What This Is
The AI co-pilot lets a user describe what they want in plain English and get a complete, working pipeline in the Activepieces builder — all settings configured, all nodes connected, ready to run. No clicking. No configuring settings. No dragging nodes.

## Why It Matters
This is the core paid feature. The difference between free (drag nodes yourself) and Pro (describe it, it builds itself). This is also what solves the n8n problem — 6 hours of configuration failures because the AI was describing what to do instead of generating the actual JSON and injecting it.

---

## How It Works — The Full Flow

```
User: "I want to pull new YouTube videos from 3 channels daily,
       transcribe them, summarize with Claude, and email a digest."

Co-Pilot: "Here's what I'd build:

  [Schedule Trigger] → runs daily at 8am
  [Loop over 3 channel IDs]
    → [YouTube: Get Videos] (new in last 24hrs)
    → [HTTP: Transcription API call]
    → [Claude: Summarize + extract key points]
  [Aggregate all summaries]
  [Gmail: Send digest email]

  Total nodes: 7
  Need your: Gmail connection, YouTube API key, Transcription API key

  Build it?"

User: "Yes, but swap Gmail for Slack"

Co-Pilot: [generates flow JSON, calls IMPORT_FLOW]
         "Done. Open http://localhost:8080 — it's there."
```

---

## Implementation

### Step 1: The Co-Pilot Service

Create `copilot/flow_generator.py`:

```python
import anthropic
import requests
import json
import os

class FlowGenerator:
    def __init__(self):
        self.ap_base = os.getenv("AP_BASE_URL")
        self.ap_key = os.getenv("AP_API_KEY")
        self.ap_project = os.getenv("AP_PROJECT_ID")
        self.headers = {
            "Authorization": f"Bearer {self.ap_key}",
            "Content-Type": "application/json"
        }

    def generate_plan(self, user_description: str) -> dict:
        """Step 1: Generate a human-readable plan before building."""
        # Uses Context7 to pull Activepieces schemas
        # Returns: { nodes: [...], connections_needed: [...], questions: [...] }
        pass

    def generate_flow_json(self, plan: dict, user_adjustments: str = "") -> dict:
        """Step 2: Generate the complete FlowVersion JSON."""
        # Uses Context7 to get exact pieceName, actionName, input field names
        # Returns valid FlowVersion JSON
        pass

    def inject_flow(self, flow_json: dict, display_name: str) -> str:
        """Step 3: Two-call pattern to create and populate the flow."""
        # Call 1: Create empty flow
        create_resp = requests.post(
            f"{self.ap_base}/api/v1/flows",
            headers=self.headers,
            json={"displayName": display_name, "projectId": self.ap_project}
        )
        flow_id = create_resp.json()["id"]

        # Call 2: Import the complete definition
        import_resp = requests.post(
            f"{self.ap_base}/api/v1/flows/{flow_id}",
            headers=self.headers,
            json={"type": "IMPORT_FLOW", "request": flow_json}
        )
        return flow_id
```

### Step 2: The System Prompt for Flow Generation

When calling Claude to generate flow JSON, use this system prompt structure:

```
You are an Activepieces flow generator. Your job is to generate valid FlowVersion JSON
for Activepieces (schemaVersion "21") based on a user's plain English description.

RULES:
1. Always use Context7 to pull the exact schema for any piece you use before including it
2. Never guess pieceName, actionName, or input field names — read them from Context7
3. Generate the complete FlowVersion object including trigger and all actions
4. Actions are a linked list via nextAction — do NOT use arrays
5. Each step needs a unique name: "trigger", "step_1", "step_2", etc.
6. Variable references use: {{step_1.output.fieldName}}
7. Always include errorHandlingOptions for PieceActions
8. schemaVersion must be "21"

CONTEXT7 USAGE:
Before generating any piece's settings, call:
  use context7: /activepieces/activepieces
  search for: [pieceName] [actionName]
This gives you the exact input fields and valid values.

OUTPUT: Return ONLY valid JSON (FlowVersion format). No explanation. No markdown.
```

### Step 3: The Plan Confirmation Step

Before injecting the flow, always show the plan to the user:

```python
def format_plan_for_user(plan: dict) -> str:
    """Human-readable plan summary before building."""
    lines = ["Here's what I'd build:\n"]
    
    for i, node in enumerate(plan["nodes"]):
        prefix = "→" if i > 0 else " "
        lines.append(f"  {prefix} [{node['type']}] {node['description']}")
    
    if plan.get("connections_needed"):
        lines.append("\nYou'll need to connect:")
        for conn in plan["connections_needed"]:
            lines.append(f"  - {conn}")
    
    lines.append("\nBuild it? Or tell me what to change.")
    return "\n".join(lines)
```

### Step 4: Iteration Handling

After a flow is built, the user can iterate:

| User Says | Action |
|-----------|--------|
| "Change Gmail to Slack" | Regenerate only that action node's JSON, apply UPDATE_ACTION operation |
| "Add a filter after step 2" | Generate new action, apply ADD_ACTION operation |
| "Remove the summary step" | Apply DELETE_ACTION operation |
| "Change the schedule to every hour" | Apply UPDATE_TRIGGER operation |
| "Start over" | Create new empty flow, IMPORT_FLOW with fresh definition |

For updates to existing flows, use the individual operation types instead of IMPORT_FLOW:
```python
# Update a specific action
requests.post(f"{BASE_URL}/api/v1/flows/{flow_id}", headers=HEADERS, json={
    "type": "UPDATE_ACTION",
    "request": {
        "name": "step_2",   # the step to update
        "action": { ... }   # new action definition
    }
})
```

---

## The Schema Grounding Rule

**This is what fixes the n8n problem.**

Before generating JSON for any piece, Claude MUST pull its schema. Example for Gmail:

```
Context7 query: /activepieces/activepieces → search "piece-gmail send_email"

Returns:
  pieceName: "@activepieces/piece-gmail"
  actionName: "send_email"
  pieceVersion: "~0.6.0"
  input fields:
    - to: ShortText (required)
    - subject: ShortText (required)  
    - body: LongText (required)
    - cc: ShortText (optional)
    - bcc: ShortText (optional)
    - replyTo: ShortText (optional)
```

Now Claude generates the JSON with the exact field names. No guessing. No wrong settings.

---

## The 20 Priority Pieces to Support First

Cover these and you cover 90% of all AI automation use cases:

| Category | Pieces |
|----------|--------|
| Triggers | Schedule, Webhook, New Email |
| Data Fetch | HTTP Request, YouTube, Google Sheets |
| AI/LLM | Anthropic Claude, OpenAI, Perplexity |
| Transform | Loop on Items, Router/Branch, Filter, Merge |
| Storage | Google Sheets (write), Airtable, Notion |
| Output | Gmail, Slack, Discord, Webhook POST |
| Utility | Delay, Code (custom JS), Aggregate |

Load these 20 schemas into Claude's context at the start of every co-pilot session.

---

## UI for the Co-Pilot

The co-pilot lives in the skin as a chat panel. It is NOT built into the Activepieces builder itself.

```
┌────────────────────────────────────┐
│  Pipeline Builder                  │
│  ┌──────────────────────────────┐  │
│  │  [Activepieces builder]      │  │
│  │  (shows after build)         │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │  AI Co-Pilot Chat            │  │
│  │                              │  │
│  │  > Tell me what you want     │  │
│  │  ____________________________│  │
│  │  [Send]                      │  │
│  └──────────────────────────────┘  │
└────────────────────────────────────┘
```

After the flow is built, the builder panel above refreshes to show the newly created flow.

---

## Success Criteria

- [ ] User types a pipeline description → co-pilot returns a readable plan
- [ ] User confirms → flow appears in Activepieces builder with all steps and settings correct
- [ ] User says "change X to Y" → specific node updates, rest of flow unchanged
- [ ] User says "add a step after step 2" → new step appears in correct position
- [ ] No setting in any generated flow is guessed — all come from Context7 schemas
- [ ] The flow runs successfully on first manual test trigger

---

## Protocol Checkpoints (Stage 08 Injection)

### Pulse Checks — After Each File
| File | Assertions |
|------|-----------|
| `copilot/flow_generator.py` | File exists; `FlowGenerator` class defined; `generate_plan()`, `generate_flow_json()`, `inject_flow()` all present; no syntax errors |
| `copilot/mechanism_search.py` | File exists (even if minimal at this phase); `search_mechanisms()` function present |
| System prompt constant | `SCOPED_CODE_PROMPT` or equivalent string constant exists in `flow_generator.py` or a prompts file; contains "IMPORT_FLOW" reference |

### Seam Checks — Connection Points
**Seam 1: generate_flow_json() → inject_flow()** (the critical one)
- `generate_flow_json()` returns a dict with keys: `displayName`, `schemaVersion`, `trigger`
- `inject_flow()` accepts that dict and posts it to AP — verify with a simple 2-node test flow
- AP returns HTTP 200 on the IMPORT_FLOW call

**Seam 2: Context7 → flow generation**
- Prompt sent to Claude includes piece schema info (verify by checking prompt string contains `pieceName` and `actionName` references for the pieces used)
- Generated JSON's `pieceName` values match known AP piece names (not guessed strings)

### Full Checkpoint (Phase 2 Gate)
**Pattern checks (git diff):**
```
Expected new files: copilot/__init__.py, copilot/flow_generator.py, copilot/mechanism_search.py (or similar)
No modification to docker-compose.yml or AP core files.
```

**Functional checks:**
```bash
# Test: plain English → flow appears in AP builder
python -c "
from copilot.flow_generator import FlowGenerator
gen = FlowGenerator()
plan = gen.generate_plan('Fetch a URL every hour and save result to a file')
print('Plan nodes:', len(plan['nodes']))
flow_id = gen.inject_flow(gen.generate_flow_json(plan), 'Phase 2 Test')
print('Flow ID:', flow_id)
assert flow_id, 'No flow ID returned'
print('✓ AI Co-Pilot working')
"
# Then: open AP builder and confirm the flow appears with correct node types
```

**Gate condition:** Test script prints `✓ AI Co-Pilot working` AND the generated flow appears in AP with the correct node types (trigger + at least one action). Zero wrong `pieceName` values. PASS or FAIL.

### Violation Rules
| Level | Trigger | Action |
|-------|---------|--------|
| LOW | Plan has correct nodes but display names are slightly off | Log, proceed |
| MEDIUM | Flow injects but one node has wrong `actionName` | Fix schema lookup, regenerate |
| HIGH | IMPORT_FLOW returns 4xx; flow does not appear in builder | Revert flow_generator.py, fix and retry |
| CRITICAL | Claude generates hallucinated pieceName values not in AP | Stop — Context7 integration broken; fix before any further generation |

### Two-Strike Rule
Max 2 retries. On second failure: stop for human review. The problem is likely in the system prompt or Context7 integration — not fixable by retrying the same approach.
