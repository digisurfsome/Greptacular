# PRD: Optimization Support Agents & Dashboard

> **Status:** Plan — ready for implementation
> **Date:** 2026-04-03
> **Context:** Reduces token waste across all AutoForge workspace sessions.
> **Build order:** Dashboard first (visibility), then Rant Compressor (biggest daily savings), then Task Scout (per-task savings).

---

## The Problem

AutoForge workspace agents burn tokens on three things:
1. **File exploration** — Agents search the codebase to figure out where things are (PARTIALLY FIXED by CLAUDE.md file maps and tool-efficiency rules already pushed)
2. **Long user input** — Voice-to-text rants are 5-10x longer than they need to be, and every token gets re-sent on every turn of the conversation
3. **Unfocused tool usage** — Agents use tools they don't need because nothing tells them which tools are relevant to their task

This PRD covers three support agents and a dashboard to address all three problems.

---

## Feature 1: Optimization Dashboard (Pulldown Panel)

### What It Is
A persistent icon in the top nav bar (next to the existing G/GitHub icon) that opens a pulldown panel. The panel covers most of the page (like a drawer from the top) and shows optimization status, agent costs, and the optimization tracker content.

### UI Spec

**Icon placement:** Top nav bar, persistent across ALL pages. Icon: a gauge/speedometer or lightning bolt. Clicking it opens the panel as an overlay/drawer sliding down from the top.

**Panel sections:**

#### Section A: Live Usage Summary
- Today's total tokens used (input + output)
- Today's estimated cost (USD)
- Active conversations count
- "Avg tool calls per task" metric (calculated from token_log data)

#### Section B: Per-Conversation Breakdown (Last 24h)
- Table: Conversation title | Model | Tool calls | Input tokens | Output tokens | Est. cost
- Sortable by any column
- Click a row to expand and see per-tool breakdown (Read: X calls, Grep: Y calls, etc.)

#### Section C: Optimization Status
- Checklist pulled from the optimization tracker:
  - [x] File maps installed
  - [x] Tool efficiency rules installed  
  - [x] New page standards installed
  - [ ] Root CLAUDE.md optimized
  - [ ] Rant compressor active
  - [ ] Task scout active
  - etc.
- Each item shows DONE/PLANNED/IDEA status

#### Section D: Support Agent Status
- List of support agents (Rant Compressor, Task Scout, Map Keeper)
- Each shows: Enabled/Disabled toggle, calls today, tokens saved estimate

#### Section E: Notes
- Free-text area where the owner can jot ideas
- Persisted to database (simple key-value store or a dedicated table)
- Markdown rendered

### Backend

**Data source:** All usage data already exists in `workspace_token_log` table. No new data collection needed.

**New API endpoints:**
- `GET /api/workspace/optimization/summary` — Returns aggregated usage stats (today, this week)
- `GET /api/workspace/optimization/conversations` — Returns per-conversation cost breakdown (last 24h)
- `GET /api/workspace/optimization/status` — Returns optimization checklist status
- `GET /api/workspace/optimization/notes` — Get saved notes
- `PUT /api/workspace/optimization/notes` — Save notes

**New files:**
- `server/routers/optimization.py` — API endpoints
- `server/services/optimization_dashboard.py` — Aggregation queries against workspace_token_log
- `ui/src/components/optimization/OptimizationPanel.tsx` — The pulldown panel
- `ui/src/components/optimization/UsageSummary.tsx` — Live usage cards
- `ui/src/components/optimization/ConversationCostTable.tsx` — Per-conversation breakdown
- `ui/src/components/optimization/OptimizationChecklist.tsx` — Status checklist
- `ui/src/components/optimization/AgentStatusList.tsx` — Support agent status
- `ui/src/components/optimization/NotesEditor.tsx` — Notes area
- `ui/src/hooks/useOptimization.ts` — React Query hooks

**Where to add the icon:** The top nav bar component. Need to identify where the G icon lives and add the optimization icon next to it. Check `ui/src/App.tsx` or whatever component renders the persistent top bar.

### Estimated scope
- Backend: ~150 lines (queries + endpoints)
- Frontend: ~400 lines (panel + sub-components)
- Moderate complexity — mostly reading existing data in new ways

---

## Feature 2: Rant Compressor

### What It Is
A Haiku-powered agent that sits between the user's chat input and the worker agent. Takes the user's raw text (voice transcription, brain dump, stream of consciousness) and compresses it into a short, structured task description.

### How It Works

```
User types/speaks rant in chat input box
  → Clicks "Prep" button (or toggle: auto-compress ON)
  → Frontend sends rant to compression endpoint
  → Haiku agent compresses: 2000 tokens → 300 tokens
  → UI shows side-by-side: original | compressed
  → User reviews, optionally edits
  → Clicks "Send" to send compressed version to worker
```

### UI Spec

**Changes to WorkspaceChatInput.tsx:**

Current: One "Send" button.

New: Two-mode operation:

**Mode A: Manual (default)**
- "Prep" button replaces or sits next to "Send"
- Clicking "Prep" sends text to compression endpoint
- A comparison panel appears above the input:
  - Left side: "Your message" (original, grayed out)
  - Right side: "Compressed" (editable)
  - Small stats line: "Original: ~2,100 tokens → Compressed: ~310 tokens (85% reduction)"
- "Send" button appears to send the compressed version
- "Send Original" small link to bypass compression

**Mode B: Auto-compress (toggle)**
- Toggle switch in chat header: "Auto-compress: ON/OFF"
- When ON, every message automatically gets compressed before sending
- Brief flash showing "Compressing..." then sends
- User can expand to see original vs compressed in the message history

### Backend

**New API endpoint:**
- `POST /api/workspace/compress` — Takes raw text, returns compressed version

**Implementation:**
```python
# server/services/rant_compressor.py

COMPRESS_SYSTEM_PROMPT = """You are a message compressor. Your ONLY job is to take a user's 
raw, unstructured message and compress it into a clear, structured format.

Rules:
- Keep ALL information. Do not drop any details, requirements, or constraints.
- Remove: repetition, filler words, tangents that circle back to the same point.
- Output format:
  TASK: [1-2 sentences — what needs to be done]
  CONTEXT: [1-3 sentences — relevant background]
  FILES: [specific files mentioned, if any]
  CONSTRAINTS: [any limitations, preferences, or "do not" instructions]
- If the message is already short and clear (under 100 words), return it unchanged.
- Maximum output: 150 words.
"""
```

**Model:** Haiku (claude-haiku-4-5). Cost: ~$0.001 per compression. This is 25-60x cheaper than the Opus tokens it saves.

**New files:**
- `server/services/rant_compressor.py` — Compression logic
- `server/routers/compress.py` — API endpoint (or add to workspace router)
- `ui/src/components/workspace/CompressPreview.tsx` — Side-by-side comparison panel

**Modify:**
- `ui/src/components/workspace/WorkspaceChatInput.tsx` — Add Prep button and toggle
- `ui/src/hooks/useWorkspaceChat.ts` — Add compression state management

### Cost Math
- Average rant: ~2,000 tokens input to Haiku = ~$0.0005
- Haiku output: ~300 tokens = ~$0.000375
- Total compression cost: ~$0.001
- Savings on Opus: 1,700 tokens × 10 turns × $15/M = ~$0.255 saved per conversation
- **ROI: ~255x return on every compression call**

### Estimated scope
- Backend: ~80 lines
- Frontend: ~200 lines
- Low-medium complexity

---

## Feature 3: Task Scout

### What It Is
A Haiku agent that runs automatically when a workspace conversation starts (or when the first message is sent). It reads the task + the CLAUDE.md file maps and outputs a scoped "tool kit" that gets injected into the worker agent's system prompt.

### How It Works

```
User sends first message (or compressed message) to conversation
  → Before sending to worker, Task Scout runs:
    → Reads: user message + ui/CLAUDE.md + server/CLAUDE.md
    → Outputs JSON: { files_needed, tools_allowed, scope_directories, do_not_explore }
  → JSON is injected into worker's system prompt as a "Task Scope" section
  → Worker starts with focused context — no exploration needed
```

### Backend

**New service:**
```python
# server/services/task_scout.py

SCOUT_SYSTEM_PROMPT = """You are a Task Scout. Given a user's task description and 
the project's file maps, identify exactly which files and tools the worker agent needs.

You will receive:
1. The user's task description
2. The UI file map (ui/CLAUDE.md)
3. The Server file map (server/CLAUDE.md)

Output a JSON object:
{
  "task_type": "ui" | "backend" | "docs" | "full-stack" | "unknown",
  "files_to_read": ["exact/path/to/file1.tsx", "exact/path/to/file2.py"],
  "files_to_modify": ["exact/path/to/file.tsx"],
  "tools_allowed": ["Read", "Edit", "Write"],
  "scope_directories": ["ui/src/pages/", "ui/src/components/workspace/"],
  "do_not_explore": ["server/", "docs/", ".claude/"],
  "notes": "Brief explanation of why these files are needed"
}

Rules:
- Be specific. List exact file paths, not directories.
- Be conservative. Only list files the task actually needs.
- If the task is unclear, set task_type to "unknown" and list no files.
- Maximum 10 files in files_to_read.
- Maximum 5 files in files_to_modify.
"""
```

**Integration point:** `workspace_chat_session.py` — After receiving the first user message, before sending to the worker model, run the scout and inject its output into the system prompt.

**New files:**
- `server/services/task_scout.py` — Scout logic + Haiku call
- UI: No new components needed — this is invisible to the user (runs automatically)
- Optional: Show scout results in the optimization dashboard ("Task Scout scoped this conversation to 3 files, saving ~X exploratory calls")

**Modify:**
- `server/services/workspace_chat_session.py` — Add scout call before first worker turn

### Cost Math
- Scout input: ~3,000 tokens (task + file maps)
- Scout output: ~200 tokens (JSON)
- Total: ~$0.001 per scout call
- Savings: 5-15 fewer exploratory tool calls × 1,000 tokens each = 5,000-15,000 Opus tokens saved
- **ROI: ~50-150x return per scout call**

### Estimated scope
- Backend: ~120 lines
- Frontend: ~0 lines (invisible) or ~30 lines (optional dashboard integration)
- Medium complexity (touches the chat session flow)

---

## Feature 4: Support Agent Registry

### What It Is
A lightweight registry that tracks all support agents (Rant Compressor, Task Scout, Map Keeper, future agents). Each agent has an enabled/disabled toggle, usage stats, and configuration.

### Data Model

```python
# Add to workspace_database.py or new file

class SupportAgent(Base):
    __tablename__ = "support_agents"
    
    id = Column(String(50), primary_key=True)  # "rant_compressor", "task_scout", etc.
    display_name = Column(String(100))
    description = Column(Text)
    enabled = Column(Integer, default=1)  # 0 or 1
    model = Column(String(50), default="haiku")  # which model it uses
    calls_today = Column(Integer, default=0)
    calls_total = Column(Integer, default=0)
    tokens_saved_estimate = Column(Integer, default=0)
    config_json = Column(Text, nullable=True)  # JSON blob for agent-specific settings
    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)
```

### API

- `GET /api/workspace/agents` — List all support agents with stats
- `PUT /api/workspace/agents/{id}/toggle` — Enable/disable
- `PUT /api/workspace/agents/{id}/config` — Update config
- `GET /api/workspace/agents/{id}/stats` — Detailed usage stats

### UI

Displayed in the Optimization Dashboard (Section D: Support Agent Status).

Each agent card shows:
- Name + description
- ON/OFF toggle
- "23 calls today | ~4,500 tokens saved"
- Expand for config options

### Estimated scope
- Backend: ~100 lines (model + CRUD + endpoints)
- Frontend: Part of the Optimization Dashboard (~100 lines)

---

## Build Order

| Priority | Feature | Why This Order | Depends On |
|----------|---------|---------------|-----------|
| 1 | **Support Agent Registry** | Other features need it to register themselves | Nothing |
| 2 | **Rant Compressor** | Saves money on every conversation immediately. Owner uses it daily. | Registry (to register itself) |
| 3 | **Task Scout** | Saves money per task. Slightly more complex (touches chat session). | Registry + file maps (already done) |
| 4 | **Optimization Dashboard** | Shows all the data. Most useful AFTER the other agents exist and generate data. | Registry + token_log data (already exists) |

**Alternative order if owner wants visibility first:** Swap Dashboard to #1. It works without the other agents — it just shows usage data from existing token logs. The support agent section would be empty until agents are built.

---

## Implementation Notes for the Building Agent

### Key files to understand before building:
- `server/services/workspace_chat_session.py` — The main chat engine. Rant compressor hooks into message processing. Task scout hooks into system prompt generation.
- `server/services/workspace_database.py` — All database models. Support agent registry model goes here.
- `ui/src/components/workspace/WorkspaceChatInput.tsx` — Where the Prep/Send buttons go.
- `ui/src/hooks/useWorkspaceChat.ts` — Chat state management. Compression state goes here.
- `server/routers/workspace.py` — Workspace API. New endpoints can go here or in a new router.

### What NOT to touch:
- Do NOT modify the WebSocket connection logic
- Do NOT modify how messages are stored in the database
- Do NOT change the existing Send flow — ADD the Prep flow alongside it
- Do NOT modify workspace_chat_session.py's core _query_claude() method — add scout as a pre-step

### Testing approach:
- Rant compressor: Send a long message, verify compressed version is shorter and retains all info
- Task scout: Send a task, verify JSON output contains reasonable file paths
- Dashboard: Verify usage numbers match what's in workspace_token_log table
- Registry: Verify enable/disable toggles persist and affect agent behavior
