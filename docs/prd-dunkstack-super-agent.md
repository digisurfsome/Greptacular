# PRD: DunkStack Super Agent System

**Created: 2026-03-14 — Session 10**
**Status: Ready to build**
**Reference: `docs/truth-walkie-talkie-token-costs.md` for math and theory**

---

## What This Is

A complete upgrade to the DunkStack/walkie-talkie system that enables:
1. **Bug fixes** — walkie-talkie hook actually working, not silently broken
2. **Micro-bridges** — periodic session restart to clear tool receipt accumulation
3. **Super agent chain** — multiple agents reading previous agents' conversation files
4. **Crash recovery** — auto-restart with file-based state recovery
5. **Compaction control** — disable auto-compaction, use manual bridges instead

## Why It Matters

- Current system: 1 agent × 500K = 500K productive tokens
- With super agent chain: 5 agents × ~450K avg = 2.27M productive tokens (4.5x)
- With micro-bridges: each API call stays at ~20K instead of growing to 80-120K (10x less rate limit burn)
- Crash-proof: nothing lost because source of truth is files, not API session

---

## Phase 0: Critical Bug Fixes (MUST DO FIRST)

### 0.1 Fix walkie-talkie hook return format

**Problem:** `DunkStackCodingSession` walkie-talkie hook uses `SyncHookJSONOutput` which the SDK silently ignores. Messages are injected but the tool call isn't actually blocked.

**Fix:** Change return format to plain dict, matching the working pattern in `workspace_chat_session.py` lines 777-793.

**File:** `server/services/dunkstack_session.py` lines 348-354 and 368-381
**Change:** Replace all `SyncHookJSONOutput(hookSpecificOutput={...})` with `{"decision": "block", "reason": ...}`

### 0.2 Add walkie-talkie hook to DunkStackChatSession

**Problem:** `DunkStackChatSession` (WebSocket flow) has NO walkie-talkie PreToolUse hook. Only the REST-based `DunkStackCodingSession` has it.

**Fix:** Copy the walkie-talkie hook from CodingSession to ChatSession, using the plain dict return format.

**File:** `server/services/dunkstack_chat_session.py`

### 0.3 Add PreCompact hook to DunkStackChatSession

**Problem:** ChatSession has no PreCompact hook. If compaction fires, it doesn't know to preserve .agent/ file references.

**Fix:** Copy PreCompact hook from CodingSession lines 250-275.

---

## Phase 1: Stop Wiping Conversation Files + Archive System

### 1.1 Archive instead of wipe on agent start

**Problem:** `_reset_comms_files()` at router line 1005 wipes `from_human.md` and `to_human.md` on every agent start. This destroys the previous agent's conversation — making super agent chains impossible.

**Fix:**
1. Before wiping, copy current comms files to an archive directory
2. Archive structure: `.agent/archive/session_001/`, `.agent/archive/session_002/`, etc.
3. Each archive contains: `from_human.md`, `to_human.md`, `working_memory.md`, `bridge.md`
4. Increment session number automatically
5. THEN reset comms files for the new session

**Files to modify:**
- `server/routers/dunkstack.py` — `_reset_comms_files()` and agent start flow
- `server/services/agent_os_file_utils.py` — add archive template dir

### 1.2 Session counter

**Add:** `.agent/session_counter.txt` — simple integer, incremented on each agent start.
**Used by:** Archive naming, cab ride cost calculation, super agent chain logic.

### 1.3 Index of archived sessions

**Add:** `.agent/archive/index.md` — one-line summary per session:
```markdown
# Session Archive
- session_001: [2026-03-14 10:30] Built login page, edited 5 files
- session_002: [2026-03-14 14:15] Fixed auth bug, refactored middleware
```

Updated by the agent at bridge save time (system prompt instruction).

---

## Phase 2: Micro-Bridge (Tool Receipt Clearing)

### 2.1 Track tool receipt token accumulation

**Add to `_token_state`:**
```python
"tool_receipt_tokens": 0,  # Accumulated tool result tokens since last micro-bridge
"micro_bridge_count": 0,   # Number of micro-bridges in this session chain
```

**How to track:** In `record_tokens()`, the SDK reports `input_tokens` per response. The delta between consecutive responses is roughly the new tool results added. Track this delta as `tool_receipt_tokens`.

### 2.2 Micro-bridge threshold and trigger

**Config:** Add to `.agent/settings/config.yml`:
```yaml
micro_bridge:
  enabled: true
  threshold_tokens: 40000  # Trigger micro-bridge when tool receipts exceed this
  auto_restart: true       # Automatically restart session after bridge
```

**Trigger:** In `record_tokens()`, after updating `tool_receipt_tokens`:
```python
if tool_receipt_tokens >= threshold:
    # 1. Inject message to agent: "Write your current state to working_memory.md NOW"
    # 2. Wait for agent to comply (monitor working_memory.md mtime)
    # 3. Stop session
    # 4. Start fresh session (reads working_memory.md on bootstrap)
    # 5. Reset tool_receipt_tokens to 0
    # 6. Increment micro_bridge_count
```

### 2.3 Pre-restart state save injection

**When micro-bridge threshold is hit:**
1. Write to `from_human.md`: "MICRO-BRIDGE: Write your current state, task progress, and immediate next steps to .agent/working_memory.md immediately. Then stop and wait."
2. Set control mode to `idle`
3. Wait up to 30 seconds for working_memory.md mtime to update
4. Stop session
5. Archive current comms to `.agent/archive/session_NNN/`
6. Start fresh session

### 2.4 Add tool_log.md

**Create:** `.agent/tool_log.md` — rolling summary of recent tool calls.
**System prompt instruction:** "After every 5 tool calls, append a 1-line summary to .agent/tool_log.md: what tool, what file, what result. Keep entries concise."
**Purpose:** Helps new session (after micro-bridge) know what was just done without re-reading tool results.

---

## Phase 3: Super Agent Chain

### 3.1 New agent reads previous archives on startup

**Modify STARTUP_MESSAGE / bootstrap:**
```
After reading your current state files, check .agent/archive/index.md.
If previous sessions exist, read their from_human.md and to_human.md
files to understand the full conversation history.
Start with the most recent session and work backwards.
```

### 3.2 Cab ride cost tracking

**Add to `_token_state`:**
```python
"cab_ride_tokens": 0,  # Tokens spent reading previous session archives
"productive_tokens": 0, # Tokens spent on actual work
```

**How to track:** After startup, once the agent starts doing non-archive-reading work, switch from cab_ride to productive counting. The trigger: agent's first tool call that ISN'T a Read of `.agent/archive/*`.

### 3.3 Automated handoff from agent N to agent N+1

**At context limit bridge (50% / 500K):**
1. Inject HANDOFF message to agent
2. Agent writes final state to working_memory.md and bridge.md
3. Stop session
4. Archive session files
5. Increment session counter
6. Auto-start new session
7. New session reads archive index + all previous session files
8. New session reads bridge.md for immediate context
9. New session continues work

**UI indicator:** Show "Agent 3 of chain (cab ride: 46K, productive: 454K remaining)"

### 3.4 Selective reading mode

For later optimization (not Phase 3):
- Agent reads `archive/index.md` first (one-liners)
- Only reads full session files if the one-liner is relevant
- Reduces cab ride cost for agents late in the chain

---

## Phase 4: Crash Recovery

### 4.1 Watchdog process

**Add:** Background task that monitors the DunkStack session health.
- Check every 30 seconds: is the session process alive?
- If session died: log the crash, broadcast `agent_crashed` WebSocket event
- Files are already on disk (crash-proof by design)

### 4.2 Auto-restart on crash

**On crash detection:**
1. Wait 5 seconds (avoid rapid restart loops)
2. Archive current session (whatever state it was in)
3. Start new session
4. New session reads working_memory.md + bridge.md + from_human.md
5. New session continues from last known state

**Max restarts:** 3 consecutive crashes = stop and alert user

### 4.3 Incremental state saves

**Trigger:** Every 10K tokens of accumulated usage (tracked in `record_tokens()`)
**Action:** Inject message to agent: "Update .agent/working_memory.md with your current state."
**Purpose:** If crash happens, at most 10K tokens of state are lost.

---

## Phase 5: Compaction Control

### 5.1 Disable auto-compaction in SDK sessions

**Modify `DunkStackCodingSession.start()` and `DunkStackChatSession.start()`:**
- Pass compaction-related options to the SDK client
- If the SDK doesn't support disabling compaction, use the PreCompact hook to minimize damage

**Research needed:** Does the Claude Agent SDK TypeScript client accept an `autoCompactEnabled: false` option? If not, the PreCompact hook is the only control.

### 5.2 Improve PreCompact hook

**Current:** Tells agent to discard verbose tool results, keep state.
**Improvement:** Also tell agent: "Write EVERYTHING important to .agent/working_memory.md before compaction completes. This is your last chance to preserve context."

---

## Phase Order and Dependencies

```
Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
(bugs)    (archive)  (micro)   (chain)   (crash)   (compact)
```

Phase 0 is prerequisite for everything — the hook must actually work.
Phase 1 is prerequisite for Phase 3 — can't chain agents if files are wiped.
Phase 2 is independent — can be built in parallel with Phase 1.
Phase 4 and 5 are independent of each other.

---

## Estimated Difficulty Per Phase

| Phase | Difficulty | Files Changed | What It Gets You |
|-------|-----------|---------------|-----------------|
| 0: Bug fixes | 3/10 | 2 files | Walkie-talkie actually works |
| 1: Archive system | 4/10 | 3 files | Previous sessions preserved |
| 2: Micro-bridge | 6/10 | 3 files + system prompt | 10x less rate limit burn |
| 3: Super agent chain | 5/10 | 2 files + system prompt | 4.5-8x context multiplier |
| 4: Crash recovery | 5/10 | 2 files | Auto-restart, no lost work |
| 5: Compaction control | 3/10 | 1-2 files | No surprise summarization |

**Total: ~26/60 difficulty. Five phases. Each phase is a standalone commit.**

---

## Files That Need Modification

| File | Phases | Changes |
|------|--------|---------|
| `server/services/dunkstack_session.py` | 0, 2, 5 | Fix hook format, add micro-bridge injection, improve PreCompact |
| `server/services/dunkstack_chat_session.py` | 0 | Add walkie-talkie + PreCompact hooks |
| `server/routers/dunkstack.py` | 1, 2, 3, 4 | Archive logic, micro-bridge trigger, chain handoff, crash watchdog |
| `server/services/agent_os_file_utils.py` | 1 | Archive template creation |
| `server/templates/.../system_prompt.md` | 1, 2, 3 | Archive reading, tool_log.md, state save instructions |
| `server/templates/.../settings/config.yml` | 2 | Micro-bridge settings |

---

## New Files To Create

| File | Phase | Purpose |
|------|-------|---------|
| `.agent/archive/` directory | 1 | Archived session conversations |
| `.agent/archive/index.md` | 1 | One-line session summaries |
| `.agent/session_counter.txt` | 1 | Current session number |
| `.agent/tool_log.md` (template) | 2 | Rolling tool call summary |

---

## Success Criteria

After all phases are built:

1. **Walkie-talkie messages are reliably injected** — test by sending a message mid-tool-call and confirming the agent acknowledges it
2. **Micro-bridge fires automatically** — watch token tracking; at 40K tool receipt tokens, session restarts and agent continues seamlessly
3. **Agent 2 reads Agent 1's full conversation** — start agent, have a conversation, stop it, start a new agent, confirm it can reference what was discussed
4. **Crash recovery works** — kill the session process, confirm it auto-restarts and picks up from last state
5. **No auto-compaction** — run a long session and confirm compaction never fires; context gauge grows linearly until manual bridge

---

## Rate Limit Impact (Before vs After)

| Metric | Current | After All Phases |
|--------|---------|-----------------|
| Tokens per API call (avg) | ~60-120K | ~8-20K |
| Rate limit burn per hour | ~3-5M tokens | ~0.5-1M tokens |
| Effective context per "lifetime" | 500K | 2.27M (5 agents) to 4.04M (10 agents) |
| Crash recovery | Manual restart, state may be lost | Auto-restart, nothing lost |
| Compaction | Uncontrolled, lossy | Disabled, manual bridges only |
