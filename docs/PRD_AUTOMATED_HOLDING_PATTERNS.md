# PRD: Automated Holding Patterns — Minimum-Cost Session Persistence

## CRITICAL BOUNDARIES

**BUILD IN:** Workspace session system only (files under `server/services/workspace_chat_session.py`, `server/routers/workspace.py`, `server/schemas.py`, `ui/src/components/workspace/`, `ui/src/hooks/useWorkspaceChat.ts`, `ui/src/pages/WorkspacePage.tsx`)

**DO NOT TOUCH:** AutoForge app builder system (`agent.py`, `client.py`, `autonomous_agent_demo.py`, `parallel_orchestrator.py`, `mcp_server/`). The AutoForge system is production-stable and must not be altered.

**DEPENDS ON:** Walkie-Talkie system (PRD_WALKIE_TALKIE_SYSTEM.md) — must be fully functional before this feature.

---

## 1. OVERVIEW

### What Are Automated Holding Patterns?

When a Claude agent finishes a task and has no new work queued, instead of ending the API call (which forces a new call with token overhead to resume), the system automatically enters a **holding pattern** — a loop of zero-cost or near-zero-cost actions that keep the API call alive and the full context window intact.

Think of it like an airplane circling at minimum fuel burn, ready to land the instant the runway clears.

### Why Does This Matter?

**Cost optimization:** Each new API call has overhead — the full conversation history must be re-sent. On a 1M context window with 200K of accumulated history, that's 200K input tokens just to "wake up" the agent. If the agent stays in a holding pattern instead, the next task costs only the new prompt tokens.

**Context preservation:** Long-running sessions accumulate rich context — code understanding, user preferences, architectural decisions. Ending the API call doesn't lose this (it's in conversation history), but re-sending it costs money. Holding patterns keep the context "hot" for free.

**Responsiveness:** An agent in a holding pattern responds to walkie-talkie messages in <5 seconds (next tool call). A cold agent requires a full API call startup (5-30 seconds depending on context size).

### Cost Math

Example: 1M Sonnet 4.6, session at 300K tokens of context.

| Scenario | Cost to Resume |
|----------|---------------|
| **Cold start** (new API call) | 300K input tokens × $3/MTok = **$0.90** |
| **Holding pattern** (same API call) | ~50 tokens per hold cycle = **$0.00015** |
| **[WAITING] pause** (zero tokens) | **$0.00** |

Over a full workday with 20 task transitions, that's **$18 in cold starts vs ~$0.003 in holding patterns**. The holding pattern pays for itself thousands of times over.

---

## 2. ARCHITECTURE

### 2.1 Hold Strategy Hierarchy (Cheapest to Most Expensive)

The system uses a tiered approach, preferring the cheapest strategy that keeps the session alive:

| Tier | Strategy | Token Cost | Duration | Description |
|------|----------|-----------|----------|-------------|
| **T0** | `[WAITING]` pause | 0 tokens | Up to `comm_wait_timeout` (max 300s) | Agent asks "Ready for next task?" and waits. Completely free. |
| **T1** | Heartbeat micro-read | ~30 tokens | ~1 second | Read 1 line of a tiny status file. Just enough to trigger a tool call and reset the cycle. |
| **T2** | Context summary | ~200 tokens | ~3 seconds | Agent generates a brief internal summary of work done. Useful as a checkpoint. |
| **T3** | Proactive check | ~500 tokens | ~5 seconds | Agent checks for lint errors, file changes, or other lightweight validation on recent work. |

### 2.2 Hold Loop Flow

```
Agent finishes task
    ↓
System prompt instructs: "Enter holding pattern"
    ↓
┌──────────────────────────────────────────────────┐
│  HOLDING LOOP                                     │
│                                                   │
│  1. [WAITING] "Ready for next task" (T0, free)   │
│       ↓                                           │
│     User responds? ──Yes──→ EXIT LOOP, do task    │
│       ↓ No (timeout)                              │
│                                                   │
│  2. Heartbeat micro-read (T1, ~30 tokens)        │
│     Read ~/.autoforge/.hold_signal                │
│       ↓                                           │
│     Signal file has task? ──Yes──→ EXIT LOOP      │
│       ↓ No                                        │
│                                                   │
│  3. Back to step 1 (loop)                        │
│                                                   │
│  Emergency exit after max_hold_cycles (default 50)│
│  = ~250 minutes at 5-min waits = ~4 hour max hold│
└──────────────────────────────────────────────────┘
```

### 2.3 Hold Signal File

A lightweight coordination mechanism using the filesystem:

- **Path:** `~/.autoforge/.hold_signal` (or per-session: `~/.autoforge/sessions/{session_id}/.hold_signal`)
- **Empty file** = keep holding
- **File with content** = new task, exit holding pattern and execute
- **File deleted** = gracefully end session

This allows external systems (UI, cron jobs, other agents) to inject work into a holding agent.

### 2.4 Cost Budget

The holding pattern has a configurable **cost budget** to prevent runaway spending:

```python
hold_budget_tokens: int = 5000  # Max tokens to spend on holding (~$0.015 on Sonnet)
hold_max_cycles: int = 50       # Max hold cycles before graceful exit
hold_strategy: str = "auto"     # auto, wait_only, heartbeat
```

At ~30 tokens per heartbeat cycle and 50 max cycles, the holding pattern burns at most 1,500 tokens (~$0.0045 on Sonnet 4.6). The `[WAITING]` pauses between heartbeats are free.

---

## 3. SETTINGS

### 3.1 New Settings Fields

Add to `GlobalSettings` in `server/schemas.py`:

```python
# Holding Pattern settings
hold_enabled: bool = True                    # Enable automated holding patterns
hold_strategy: str = "auto"                  # auto | wait_only | heartbeat | off
hold_max_duration_minutes: int = 240         # Max hold time (4 hours default)
hold_budget_tokens: int = 5000               # Token budget for hold operations
hold_notify_on_idle: bool = True             # Notify UI when entering hold
```

### 3.2 Strategy Options

| Strategy | Behavior | Best For |
|----------|----------|----------|
| `auto` | Uses T0 (wait) primarily, T1 (heartbeat) to bridge between waits. Cheapest possible. | Default, recommended for all-day sessions |
| `wait_only` | Only uses `[WAITING]` pauses. If user doesn't respond before max cycles, session ends. | Maximum cost savings, requires active user |
| `heartbeat` | Alternates between waits and micro-reads. More resilient, slightly higher cost. | Unattended sessions where you want guaranteed persistence |
| `off` | No holding pattern. Session ends when task completes. | Short tasks, budget-constrained usage |

### 3.3 Settings UI

Add a "Session Persistence" section to SettingsModal.tsx:

```
┌─────────────────────────────────────────────┐
│  SESSION PERSISTENCE                         │
│                                              │
│  Holding Pattern    [Auto ▾]                 │
│  Max Hold Time      [4 hours ▾]              │
│  Token Budget       [5000 tokens ▾]          │
│  Notify on Idle     [✓]                      │
│                                              │
│  ℹ Keeps your session alive between tasks    │
│    at near-zero cost. The agent waits for    │
│    your next instruction without ending      │
│    the API call.                             │
└─────────────────────────────────────────────┘
```

---

## 4. SYSTEM PROMPT ADDITIONS

Add to `get_workspace_system_prompt()` in `workspace_chat_session.py`:

```
## Holding Pattern (Session Persistence)

When you complete a task and have no further instructions:

1. Do NOT end your turn or say "Let me know if you need anything else"
2. Instead, enter a holding pattern:
   a. Output: [WAITING]Ready for your next task. I'll hold the session open.[/WAITING]
   b. When the wait times out, perform a minimal heartbeat action:
      - Read one line from the hold signal file: `head -1 ~/.autoforge/.hold_signal`
      - If the file contains a task, execute it
      - If empty or not found, go back to step (a)
3. Continue this loop until:
   - The user sends a walkie-talkie message (execute their request)
   - The hold signal file contains a task (execute it)
   - You've completed {max_hold_cycles} cycles (gracefully end: "Session hold limit reached. Send a new message to start a fresh session.")

IMPORTANT: The holding pattern keeps your full context alive at near-zero cost.
The [WAITING] pause costs zero tokens. The heartbeat read costs ~30 tokens.
This is far cheaper than ending the session and re-sending all context on the next call.
```

---

## 5. BACKEND IMPLEMENTATION

### 5.1 `server/services/workspace_chat_session.py` (MODIFY)

**Changes:**

1. Add hold state tracking to `__init__()`:
   ```python
   self.hold_active: bool = False
   self.hold_cycles: int = 0
   self.hold_tokens_spent: int = 0
   self.hold_max_cycles: int = 50
   self.hold_budget_tokens: int = 5000
   self.hold_strategy: str = "auto"
   ```

2. Add hold signal file management:
   ```python
   def _get_hold_signal_path(self) -> Path:
       """Get the hold signal file path for this session."""
       return Path.home() / ".autoforge" / "sessions" / self.session_id / ".hold_signal"

   async def write_hold_signal(self, content: str = "") -> None:
       """Write to the hold signal file. Empty = keep holding, content = new task."""
       path = self._get_hold_signal_path()
       path.parent.mkdir(parents=True, exist_ok=True)
       path.write_text(content)

   async def clear_hold_signal(self) -> None:
       """Clear the hold signal file."""
       path = self._get_hold_signal_path()
       if path.exists():
           path.write_text("")
   ```

3. Track hold state in the response streaming loop:
   ```python
   # In _query_claude() response streaming, detect holding pattern:
   if "[WAITING]" in text and "holding" in text.lower():
       self.hold_active = True
       self.hold_cycles += 1
       yield {"type": "hold_status", "cycles": self.hold_cycles, "active": True}
   ```

4. Add hold-aware walkie-talkie hook enhancement:
   ```python
   # In the walkie_talkie_hook, when a message arrives during hold:
   if self.hold_active:
       self.hold_active = False
       self.hold_cycles = 0
       yield {"type": "hold_status", "cycles": 0, "active": False}
   ```

### 5.2 `server/routers/workspace.py` (MODIFY)

**Changes:**

1. Add REST endpoint for injecting tasks into holding agent:
   ```python
   @router.post("/workspace/sessions/{session_id}/hold/inject")
   async def inject_hold_task(session_id: str, body: dict):
       """Inject a task into a holding agent via signal file."""
       session = get_session(session_id)
       if not session:
           raise HTTPException(404, "Session not found")
       await session.write_hold_signal(body.get("task", ""))
       return {"status": "injected"}
   ```

2. Forward `hold_status` events through WebSocket:
   ```python
   if chunk["type"] == "hold_status":
       await websocket.send_json(chunk)
   ```

3. Add hold status to session status endpoint:
   ```python
   # In get_session_status or similar:
   return {
       ...existing_fields,
       "hold_active": session.hold_active,
       "hold_cycles": session.hold_cycles,
       "hold_tokens_spent": session.hold_tokens_spent,
   }
   ```

### 5.3 `server/schemas.py` (MODIFY)

Add settings fields as described in section 3.1. Add validators:

```python
@field_validator('hold_strategy')
@classmethod
def validate_hold_strategy(cls, v: str | None) -> str | None:
    if v is not None and v not in ('auto', 'wait_only', 'heartbeat', 'off'):
        raise ValueError("hold_strategy must be 'auto', 'wait_only', 'heartbeat', or 'off'")
    return v

@field_validator('hold_max_duration_minutes')
@classmethod
def validate_hold_max_duration(cls, v: int | None) -> int | None:
    if v is not None and (v < 5 or v > 480):
        raise ValueError("hold_max_duration_minutes must be between 5 and 480 (8 hours)")
    return v

@field_validator('hold_budget_tokens')
@classmethod
def validate_hold_budget(cls, v: int | None) -> int | None:
    if v is not None and (v < 100 or v > 50000):
        raise ValueError("hold_budget_tokens must be between 100 and 50000")
    return v
```

---

## 6. FRONTEND IMPLEMENTATION

### 6.1 Hold Status Indicator (`WorkspaceChat.tsx`)

When `hold_status.active === true`, show a minimal indicator in the chat area:

```
┌─────────────────────────────────────────────┐
│  ◉ Session holding · Cycle 3/50 · ~0 cost   │
│  [Send Task] [End Session]                   │
└─────────────────────────────────────────────┘
```

**Styling:**
- Muted background (gray-50 or slate-50)
- Pulsing dot (slow, calming — not urgent)
- Small text showing cycle count
- Two action buttons:
  - "Send Task" focuses the walkie-talkie input
  - "End Session" sends a stop signal

### 6.2 Hold Events in `useWorkspaceChat.ts`

```typescript
// In WebSocket onmessage handler:
case "hold_status":
  setHoldActive(parsed.active)
  setHoldCycles(parsed.cycles)
  break
```

### 6.3 Settings UI Addition (`SettingsModal.tsx`)

Add the "Session Persistence" section (described in section 3.3) to the existing settings modal. Place it after the "Communication" section since it's related to walkie-talkie behavior.

### 6.4 Hold Notification

When the agent first enters hold mode, show a brief toast notification:

```
"Agent is holding — send a message anytime to resume"
```

This reassures the user that the session is alive and waiting, not frozen or crashed.

---

## 7. DATA FLOW DIAGRAMS

### 7.1 Automatic Hold Entry

```
Agent finishes task
    ↓
Agent has walkie-talkie instructions + hold instructions in system prompt
    ↓
Agent outputs: [WAITING]Ready for your next task. Holding session open.[/WAITING]
    ↓
_query_claude() detects [WAITING] + "holding"
    ↓
Sets hold_active = True, emits hold_status event
    ↓
UI shows hold indicator (pulsing dot, cycle count)
    ↓
CountdownTimerBar activates (comm_wait_timeout)
    ↓
Timeout fires → auto-reply "Continue holding"
    ↓
Agent receives auto-reply → does heartbeat micro-read → back to [WAITING]
    ↓
Loop continues until user sends task or max cycles reached
```

### 7.2 User Breaks Hold with Walkie-Talkie

```
Agent in hold (cycle 5, [WAITING] active)
    ↓
User types "Build the settings page" in walkie-talkie input
    ↓
sendWalkieTalkie("Build the settings page")
    ↓
WebSocket → queue_walkie_talkie_message()
    ↓
Auto-reply timer cancelled (or next tool call picks up message first)
    ↓
Agent's next tool call (heartbeat read) → hook intercepts
    ↓
Hook delivers: "[WALKIE-TALKIE MESSAGE] Build the settings page"
    ↓
hold_active = False, hold_cycles reset
    ↓
UI hold indicator disappears
    ↓
Agent starts building settings page with full context intact
```

### 7.3 External Task Injection (Signal File)

```
Agent in hold (cycle 10)
    ↓
External system writes to ~/.autoforge/sessions/{id}/.hold_signal:
    "Run the test suite and report results"
    ↓
Agent's heartbeat cycle reads signal file
    ↓
File has content → agent exits hold, executes task
    ↓
After task completion → re-enters hold
```

---

## 8. AUTO-REPLY BEHAVIOR DURING HOLD

The existing `comm_auto_reply` setting needs special behavior during holding patterns:

### When `comm_auto_reply = true` (Default)
- CountdownTimerBar fires → sends "Continue holding" (not "Continue with your best judgment")
- Agent receives this → understands it means "stay in hold mode"
- Performs heartbeat → loops back to [WAITING]
- **This is the key mechanism that chains [WAITING] pauses indefinitely**

### When `comm_auto_reply = false`
- CountdownTimerBar fires → sends "No response within timeout. Proceed with your best judgment."
- Agent interprets this as "end holding" and gracefully closes the session
- **Use this if you want sessions to auto-terminate when you walk away**

### Auto-Reply Message Override

Add a new setting for customizing the hold auto-reply message:

```python
hold_auto_reply_message: str = "Continue holding"  # Sent when timer expires during hold
```

This keeps the hold loop going. The agent's system prompt should recognize "Continue holding" as a signal to stay in the loop, distinct from a real user task.

---

## 9. COST TRACKING

### 9.1 Per-Session Hold Cost Display

Track and display the cost of holding:

```python
# In workspace_chat_session.py
self.hold_tokens_input: int = 0   # Input tokens during hold
self.hold_tokens_output: int = 0  # Output tokens during hold

# After each hold cycle, estimate from tool call size:
self.hold_tokens_input += estimated_input_tokens
self.hold_tokens_output += estimated_output_tokens
```

### 9.2 UI Cost Display

Show in the hold indicator:

```
◉ Holding · Cycle 12/50 · ~$0.002 hold cost · Session context: 245K tokens
```

This gives the user confidence that holding is cheap and shows the context they're preserving.

---

## 10. EDGE CASES

### 10.1 Agent Doesn't Follow Hold Instructions
Some models may not reliably follow the hold pattern instructions. Fallback: if the agent's response ends without a `[WAITING]` tag and no new user message is queued, the system can inject a follow-up prompt: "No new tasks. Enter holding pattern." This costs ~100 tokens but ensures the hold loop starts.

### 10.2 Network Disconnection During Hold
If the WebSocket disconnects while the agent is in [WAITING]:
- The API call continues server-side (it's the SDK, not the WebSocket, that owns the call)
- When the user reconnects, the UI polls session status and shows hold indicator
- Queued walkie-talkie messages are lost (in-memory queue) but the session is alive
- User can send a new walkie-talkie message after reconnecting

### 10.3 Token Budget Exceeded
If `hold_tokens_spent > hold_budget_tokens`:
- Agent exits hold gracefully: "Hold budget reached. Send a new message to continue."
- UI shows notification: "Session hold ended — token budget reached"
- **Does not** end the session abruptly. The agent completes its current [WAITING] cycle first.

### 10.4 Max Cycles Reached
If `hold_cycles >= hold_max_cycles`:
- Same graceful exit as budget exceeded
- At 50 cycles × 5-min waits, this is ~4 hours of holding
- Configurable up to 480 minutes (8 hours) via `hold_max_duration_minutes`

### 10.5 Multiple Panels in Trifecta Mode
Each panel has its own hold state. One panel can be holding while another is actively working. The hold indicator appears per-panel, not globally.

---

## 11. IMPLEMENTATION ORDER

### Phase 1: System Prompt + Basic Hold (30 min)
1. Add hold instructions to `get_workspace_system_prompt()`
2. Add hold state tracking to `WorkspaceChatSession.__init__()`
3. Detect `[WAITING]` + hold keywords in response streaming
4. Emit `hold_status` events
5. Test: agent enters hold after completing a task

### Phase 2: Auto-Reply Hold Chaining (20 min)
1. Modify auto-reply message during hold: "Continue holding" instead of "Continue with your best judgment"
2. Add `hold_auto_reply_message` setting
3. Agent recognizes "Continue holding" → heartbeat → [WAITING] loop
4. Test: verify hold chains across multiple cycles

### Phase 3: Settings + UI (30 min)
1. Add settings fields to `schemas.py` (hold_enabled, hold_strategy, etc.)
2. Add "Session Persistence" section to SettingsModal
3. Add hold indicator to WorkspaceChat
4. Add `hold_status` handler to useWorkspaceChat
5. Test: settings control hold behavior

### Phase 4: Signal File + External Injection (20 min)
1. Implement hold signal file path management
2. Add heartbeat micro-read of signal file in system prompt
3. Add REST endpoint for task injection
4. Test: inject task via signal file, agent picks it up

### Phase 5: Cost Tracking + Polish (20 min)
1. Track hold tokens (input/output estimates)
2. Display hold cost in UI indicator
3. Add toast notification on hold entry
4. Handle edge cases (budget exceeded, max cycles)
5. Final end-to-end test

---

## 12. COMPATIBILITY

- **Model agnostic:** Works with any model (Opus, Sonnet, Haiku). The hold behavior is driven by system prompt instructions, not model-specific features.
- **Context mode agnostic:** Works with 200K and 1M context. Most valuable on 1M where the preserved context is larger and cold-start cost is higher.
- **Walkie-talkie dependent:** Requires the walkie-talkie system (PreToolUse hook, message queue) to be functional. The auto-reply chaining mechanism is the core of how holds persist.
- **Backward compatible:** When `hold_enabled = false` or `hold_strategy = "off"`, the system behaves exactly as before — agent completes task and waits for user's next message (new API call).

---

## 13. FUTURE ENHANCEMENTS (NOT IN THIS BUILD)

- **Intelligent hold activities:** During hold, agent could do useful low-cost work (organize notes, prepare summaries, pre-read files it thinks the user will ask about)
- **Cross-session hold transfer:** Transfer a holding session from one device to another (phone → desktop)
- **Hold scheduling:** "Hold until 2pm, then run this task" — scheduled task injection
- **Hold cost forecasting:** "At current rate, this session can hold for ~6 more hours within budget"
- **Tiered auto-escalation:** If hold runs long, auto-downgrade from heartbeat to wait_only to save tokens
- **Hold analytics:** Dashboard showing hold time vs active time, cost savings vs cold starts
