# HANDOFF: DunkStack Full Diagnosis + Fix Plan

**Date**: 2026-03-30
**From**: Claude Opus session (workspace/chat-8)
**Related**: Read `walkie-talkie-revolution-handoff.md` first — covers the Workspace side

---

## EXECUTIVE SUMMARY

DunkStack is 70% built. The architecture is solid and most features exist. But there are 3 critical bugs, 5 significant issues, and a fundamental "two brains" problem where two separate agent backends exist with different capabilities.

---

## WHAT WORKS (No Changes Needed)

- ✅ File-based walkie-talkie (agent writes to `.agent/comms/to_human.md`, human writes to `from_human.md`)
- ✅ Session control buttons (Idle/Continue/Autopilot) — write to `control.md`
- ✅ Bridge save and restore (`.agent/bridge.md`)
- ✅ Context safety system (3 tiers with configurable thresholds)
- ✅ Token tracking (cumulative, displayed in gauge)
- ✅ Model selection UI (5 presets: Opus/Sonnet/Haiku × 200K/1M)
- ✅ Build log viewer
- ✅ Working memory viewer
- ✅ WebSocket connection (connect, ping/pong, reconnect)
- ✅ Comms polling (3-second interval reads files)
- ✅ Auto-bridge on handoff threshold
- ✅ Auto-stop on hard stop threshold
- ✅ Config read/write (YAML)
- ✅ Guide panel (draggable, resizable, notes system)
- ✅ Live preview panel (iframe with responsive toggles)
- ✅ Project creation
- ✅ Benchmark mode

---

## CRITICAL BUGS (Fix Immediately)

### Bug 1: Billing Violation — Burning API Credits on 1M Context

**File**: `server/services/dunkstack_chat_session.py` line 311
**Problem**: `force_sub = self.context_mode != "1m"` — means 1M context uses API key billing instead of subscription
**CLAUDE.md rule**: "ALL CLAUDE MODELS (200K AND 1M) → SUBSCRIPTION ONLY. NO EXCEPTIONS."
**Fix**: Change to `force_sub = True`

Also check `server/services/dunkstack_session.py` line 222 — uses `self._is_subscription_mode()` which returns `self.context_window <= 200_000` — same bug, different form. Fix: always return `True`.

### Bug 2: Haiku Model Maps to Sonnet

**File**: `ui/src/pages/DunkStackPage.tsx` line 259
**Problem**: `const modelId = preset.model === 'opus' ? 'claude-opus-4-6' : 'claude-sonnet-4-6'` — no haiku branch
**Fix**: Add haiku branch to the ternary

### Bug 3: Safety System Reads Wrong Project's Config

**File**: `server/routers/dunkstack.py` line 727
**Problem**: `_get_safety_status()` calls `_agent_dir()` with no project_name — always reads ROOT config
**Fix**: Pass `project_name` through the call chain

---

## SIGNIFICANT ISSUES (Fix Before Launch)

### Issue 1: Two Separate Agent Backends ("Two Brains" Problem)

ROOT CAUSE of several bugs. DunkStack has TWO session classes:

| | REST Coding Session | WebSocket Chat Session |
|---|---|---|
| **File** | `dunkstack_session.py` | `dunkstack_chat_session.py` |
| **Started via** | `POST /agent/start` | WebSocket `start_agent` message |
| **Has walkie-talkie hook** | ✅ YES | ❌ NO |
| **Has PreCompact hook** | ✅ YES | ❌ NO |
| **Streams to UI** | ❌ Blocks HTTP | ✅ Real-time WebSocket |

**Fix**: Merge walkie-talkie hooks from coding session INTO chat session, use chat session everywhere.

### Issue 2: REST Agent Start Blocks for Minutes

**File**: `server/routers/dunkstack.py` lines 979-1034
**Fix**: Return immediately, stream bootstrap events via WebSocket.

### Issue 3: Walkie-Talkie Forwarding Only Works for WebSocket Sessions

**File**: `server/routers/dunkstack.py` line 271
**Fix**: Check both registries or unify to one.

### Issue 4: Missing receive_response() try/except

**Files**: Both session files
**Fix**: Wrap per CLAUDE.md pattern (copy from `workspace_chat_session.py`).

### Issue 5: WebSocket Handler Writes to Wrong Project

**File**: `server/routers/dunkstack.py` line 1299
**Fix**: Pass project name from session context.

---

## MINOR ISSUES

1. `hard_stop` WebSocket event not handled by frontend
2. `model_preset_update` WebSocket event not handled
3. Token state is global, not per-project — key by project_name
4. Orchestrator section has no DunkStack backend — remove or integrate

---

## FIX ORDER

| # | Task | Difficulty | Time Est |
|---|------|-----------|----------|
| 1 | Fix billing violation (force_sub = True) | 1/10 | 2 min |
| 2 | Fix Haiku model mapping | 1/10 | 2 min |
| 3 | Merge walkie-talkie hooks into chat session | 5/10 | 30-60 min |
| 4 | Fix safety status project scoping | 2/10 | 10 min |
| 5 | Add receive_response() try/except | 2/10 | 10 min |
| 6 | Fix WebSocket project scoping | 2/10 | 10 min |
| 7 | Handle hard_stop/model_preset events | 1/10 | 5 min |
| 8 | Make token state per-project | 2/10 | 10 min |
| 9 | Remove or integrate orchestrator section | 3/10 | 20 min |

**Total: ~2-3 hours of agent work**

---

## KEY FILES

| File | Lines | Role |
|------|-------|------|
| `server/routers/dunkstack.py` | ~1362 | ALL endpoints |
| `server/services/dunkstack_session.py` | ~1060 | REST coding agent with hooks |
| `server/services/dunkstack_chat_session.py` | ~679 | WS chat agent (no hooks) |
| `ui/src/pages/DunkStackPage.tsx` | ~1037 | Main page |
| `ui/src/hooks/useDunkStack.ts` | ~503 | State + WebSocket |
| `ui/src/components/dunkstack/*.tsx` | various | All UI components |

---

## ARCHITECTURE: How the File-Based Protocol Works

### Startup Message (sent to agent on session start)
```
Begin your session. Follow the file-based operating protocol:
1. Read .agent/index.md (your file map)
2. Read .agent/working_memory.md (your current state)
3. If .agent/bridge.md has content, read it and incorporate the context
4. Read .agent/comms/from_human.md for any instructions
5. Read .agent/comms/control.md for mode signal
6. Begin working on whatever task is described
```

### Walkie-Talkie Hook (coding session only — needs to be in chat session too)
- Fires on every tool call
- Reads `.agent/comms/from_human.md`, compares MD5 hash to last read
- If changed → extracts new messages → blocks tool → injects as message
- Also checks `control.md` for mode (idle → pause agent)

### PreCompact Hook (coding session only — needs to be in chat session too)
- Fires when SDK compacts context
- Tells agent to re-read protocol files after compaction
- Prevents agent from "forgetting" the file protocol

### Bridge System
- `POST /api/dunkstack/bridge/save` → writes `.agent/bridge.md`
- Auto-triggered at handoff threshold (~47.5% context)
- Next session reads bridge.md on startup (step 3 of startup message)

---

## WHAT THE OWNER WANTS

Both DunkStack AND Workspace should:
1. Support walkie-talkie communication
2. Keep turns alive via polling (avoid expensive history resends)
3. Chain sessions via handoff files (10-20+ sessions with full context)
4. Have working context safety (auto-save, auto-stop)
5. Share the same patterns so both work the same way
