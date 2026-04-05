# PRD: Prompt Chain Pipeline — Full System

> **Status:** Ready to build on a clean page (NOT workspace)
> **Date:** 2026-04-05
> **Context:** Built and tested on AutoForge workspace page. Core mechanism works but the workspace chat has a pre-existing glitch that interferes. This PRD captures everything learned so a fresh build avoids that issue.

---

## What This Is

A sequential prompt chain system. You load N skill prompts (markdown files), the system runs them one after another through Claude, and the output of each skill feeds as input to the next. The agent signals completion with `[STAGE_COMPLETE]` — that's the "button" that triggers advancement.

## Core Mechanism

```
Skill 1 runs → agent produces output → outputs [STAGE_COMPLETE]
    → pipeline captures output → feeds to Skill 2 as input
    → Skill 2 runs → agent produces output → [STAGE_COMPLETE]
    → pipeline captures → feeds to Skill 3 → ... → Skill N → Done
```

### The [STAGE_COMPLETE] Marker

Each skill prompt has instructions appended (via a configurable text box) telling the agent:
1. Do your work, produce your JSON output
2. When your contract is met and confidence >= 70
3. Output `[STAGE_COMPLETE]` as the VERY LAST thing in your response

The pipeline watches the streaming output for this marker:
- **Found** → strip marker, extract everything before it as output, feed to next stage
- **Not found** → stage enters waiting state. User can interact via chat. After each interaction, check again for marker. Force Next button as manual override.

### The Append System

- A global text box holds the `[STAGE_COMPLETE]` instructions
- Global ON/OFF toggle (default: ON)
- Per-skill checkbox "SC" (default: checked)
- When both are ON: the text gets appended to the skill prompt at send time
- The LAST skill never gets the append (it's the final output)
- Original skill files stay untouched — append happens only at runtime

---

## Four Execution Modes

The system supports 4 modes, selectable via dropdown:

### Mode 1: Same Session
- ONE Claude session (WorkspaceChatSession equivalent) for entire pipeline
- All stages are messages in the same conversation
- Agent has full context from all previous stages naturally
- **Pro:** Rich context, agent remembers everything
- **Con:** Token budget can blow up on long pipelines

### Mode 2: New Session
- Fresh Claude session per stage
- Previous stage's output is baked into the prompt via `<previous_stage_output>` tags
- Session closes after each stage
- **Pro:** Clean context per stage, no token bloat
- **Con:** Agent has no memory of earlier stages (only sees N-1)

### Mode 3: File Based
- Each stage writes output to `~/.autoforge/pipeline/{pipeline_id}/stage-{N}-output.txt`
- Next stage reads the file as input
- Fresh session per stage
- **Pro:** Outputs persisted to disk, debuggable, can be manually edited between runs
- **Con:** File I/O overhead (minimal)

### Mode 4: Database
- Each stage saves output to SQLite database
- Next stage reads previous output from database
- Fresh session per stage
- **Pro:** Queryable history, survives crashes
- **Con:** Slightly more complex than file-based

---

## Prompt Construction

### Stage 0 (first stage):
```
{skill_text}

## User's Input

{kickoff_message}

{append_text if enabled}
```

### Stages 1+ (subsequent stages):
```
{skill_text}

## Output From Previous Stage ({prev_label})

<previous_stage_output>
{previous_stage_output}
</previous_stage_output>

{append_text if enabled}
```

No extra rules, no pipeline instructions, no `[WAITING]` tags. Just the skill text + previous output + append. Let the skills speak for themselves.

---

## UI Layout

### Full-Page Two-Column Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  ⚡ SKILL PIPELINE — [project name]    [RUNNING]            ✕   │
├──────────────────┬───────────────────────────────────────────────┤
│                  │                                               │
│  LEFT COLUMN     │  RIGHT COLUMN                                │
│  (~350px)        │  (flex-1)                                    │
│                  │                                               │
│  • Project       │  Pipeline Output Viewer:                     │
│    selector      │  - Stage headers with status badges          │
│  • Working Dir   │  - Streaming text output per stage           │
│  • Kickoff Msg   │  - Token counts per stage                    │
│  • Token Budget  │  - Chat messages (user green, agent gray)    │
│  • Model         │  - Auto-scroll                               │
│  • Output Mode   │                                               │
│  • Exec Mode     │  Bottom: Chat input (always visible)         │
│  • Auto-Append   │  - Text area + Send button                   │
│    [ON/OFF]      │  - File/image upload button                  │
│    [editable     │  - Ctrl+Enter to send                        │
│     text box]    │  - Attachments bar                            │
│  • Skills list   │                                               │
│    [SC] Skill 1  │                                               │
│    [SC] Skill 2  │                                               │
│    ...           │                                               │
│  • [+ Add Skill] │                                               │
│  • [Launch]      │                                               │
│                  │                                               │
│  When running:   │                                               │
│  • [Stop]        │                                               │
│  • [Force Next]  │                                               │
│  • Stage cards   │                                               │
│  • Token bar     │                                               │
│  • Download btn  │                                               │
│  • Endpoint      │                                               │
│    placeholder   │                                               │
│                  │                                               │
├──────────────────┴───────────────────────────────────────────────┤
│  Chat input area                                                 │
└──────────────────────────────────────────────────────────────────┘
```

### Configure Mode (before launch)
Left column shows: project selector, settings, skills list, launch button

### Running Mode (during execution)  
Left column shows: stop/force-next buttons, stage progress cards with status badges, token budget bar, download button

### Stage Progress Cards
Each stage shows:
- Status badge: Pending (gray clock), Running (cyan spinner), Done (green check), Failed (red X)
- Label (extracted from first # heading in skill)
- Token count and duration when completed
- "View Output" toggle to expand/collapse output text

---

## Pipeline Projects

Save/load/delete/clone pipeline configurations:

### Database Model: PipelineProject
```
id, name, description, output_mode, default_model, default_token_budget,
stages_json (JSON array of {label, skill_text}), created_at, updated_at
```

### CRUD Operations
- Save: creates or updates project
- Save As: prompts for name, creates new
- Clone: copies project with new name
- Delete: removes with confirmation
- Load: dropdown selector populates all settings from saved project

---

## Pipeline Run Persistence

### Database Model: PipelineRun
```
id, pipeline_id, name, status, model, token_budget, total_tokens,
total_duration, working_directory, kickoff_message, stages_json,
created_at, completed_at
```

### Database Model: PipelineStageOutput
```
id, pipeline_id, stage_index, label, output_text, tokens_used,
duration_seconds, status, error, completed_at
```

---

## Folder Loading

`POST /api/pipeline/load-folder` — reads a directory of skill files:
1. Scans subdirectories sorted alphabetically
2. Prefers `SKILL-COMPLETE.md` over `SKILL.md` in each subfolder
3. Extracts label from first `# heading`
4. Returns `[{label, skill_text}]`
5. Security: absolute path required, must exist, .md files only

---

## Output Extraction

### JSON Extract Mode
When `output_mode = "json"`, the pipeline extracts the JSON context_packet from the agent's full response:
1. Find the LAST ```json code fence → use that
2. Fall back: find the LAST valid JSON object > 100 chars
3. Fall back: use full text as-is

### Full Text Mode
When `output_mode = "text"`, the full response is the output. No extraction.

---

## Combined Export

Download all outputs as a single markdown file:
```markdown
# Skill Pipeline Output

**Generated:** {timestamp}
**Model:** {model}
**Token Budget:** {budget}
**Total Tokens:** {total}
**Total Duration:** {duration}
**Stages Completed:** {N}/{total}

---

## Stage 0: {label}
**Tokens:** {n} | **Duration:** {n}s

{full_output}

---

## Stage 1: {label}
...
```

---

## Chat Input (PipelineOutputViewer)

The output viewer has a chat input at the bottom that:
1. Sends user messages to the currently running stage's session
2. Collects the agent's response
3. Shows both as chat bubbles (user = green, agent = gray)
4. Supports file/image uploads (.md, .txt, .json, .csv, .png, .jpg)
5. Ctrl+Enter to send
6. Always visible when a pipeline exists

The `inject_answer()` method on the pipeline:
1. Calls `session.send_message(answer)` on the current session
2. Collects the full response
3. Appends to the stage's output
4. Returns the response to the frontend
5. Signals `_answer_event` so the waiting loop can check for `[STAGE_COMPLETE]`

---

## Force Next / Force Advance

Manual override button that:
1. Closes the current session
2. Marks the running stage as completed with whatever output exists
3. Extracts output from `full_response`
4. Clears any waiting state
5. Lets the pipeline continue to the next stage

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | /api/pipeline/start | Start pipeline, returns pipeline_id |
| POST | /api/pipeline/stop | Stop running pipeline |
| POST | /api/pipeline/answer | Send message to running stage |
| POST | /api/pipeline/force-advance | Force advance to next stage |
| GET | /api/pipeline/status/{id} | Get pipeline + all stage statuses |
| GET | /api/pipeline/history | List past pipeline runs |
| GET | /api/pipeline/export/{id} | Download combined output markdown |
| POST | /api/pipeline/projects | Create project |
| GET | /api/pipeline/projects | List projects |
| GET | /api/pipeline/projects/{id} | Get project |
| PATCH | /api/pipeline/projects/{id} | Update project |
| DELETE | /api/pipeline/projects/{id} | Delete project |
| POST | /api/pipeline/projects/{id}/clone | Clone project |
| POST | /api/pipeline/load-folder | Load skills from folder |

---

## Key Lessons Learned

1. **Don't use [WAITING] tags for mid-stage interaction.** The SDK session can't handle reliable mid-conversation answer injection. The agent either ignores the answer or produces a 2-second garbage response.

2. **Don't connect WorkspaceChat to pipeline sessions.** Two sessions competing for the same conversation causes hangs. Keep the pipeline's sessions completely independent.

3. **Let the agent control advancement.** The `[STAGE_COMPLETE]` marker is the right mechanism — the agent decides when it's done based on its own contract, not the pipeline guessing.

4. **The workspace chat has a pre-existing glitch** where it hangs mid-response and requires a manual nudge. Build on a clean chat implementation, not the workspace.

5. **Four execution modes** give flexibility. Test all of them — different approaches work better for different use cases.

6. **Keep prompts clean.** Don't add pipeline rules, waiting instructions, or formatting guidance. Just: skill text + previous output + [STAGE_COMPLETE] append. Let the skills do their job.

---

## Future: Endpoint / Next Action

Placeholder for routing pipeline output to the next system:
- Send to Swarm Builder
- Send to Coder Agent
- Export to file
- Done — no further action

---

## Future: Modular Page

Same pipeline concept but each step can be:
- **AI** — prompt goes to Claude (current behavior)
- **Code** — runs a Python/JS function deterministically
- **Hybrid** — code pre-processes → AI processes → code post-processes

Standard interface: Input JSON → Output JSON. Steps are interchangeable.
See separate PRD for modular pipeline design.
