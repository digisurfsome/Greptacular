# FIXLIST: DunkStack Round 2

**Date:** 2026-03-30
**Scope:** 4 bugs/missing features in the DunkStack system
**Priority order:** Critical bugs first, then refactors

---

## Summary

1. Backslash URL bug in `dunkstackLoadBridge` when filename contains Windows path separators
2. Two-brains duplication: `dunkstack_session.py` and `dunkstack_chat_session.py` share 3 identical hooks that should be extracted to a shared module
3. Idle mode 10-second sleep burns agent turns (each blocked tool call counts as a turn)
4. Walkie-talkie forwarding only works for WebSocket (`DunkStackChatSession`) sessions, not REST-started (`DunkStackCodingSession`) sessions

---

## FIX 1 (BUG): Backslash URL bug in dunkstackLoadBridge

**Problem:** The `dunkstackLoadBridge` function uses `URLSearchParams` to build the query. On Windows, `filename` values from the bridge list may contain backslashes (e.g., `bridge_history\bridge-2026-03-30.md`). `URLSearchParams.toString()` encodes backslashes as `%5C`, but the FastAPI endpoint at `server/routers/dunkstack.py` line 552 receives `filename` as a query parameter and uses it directly in `Path(agent / "bridge_history" / filename)`. If the filename contains path separators, this can either fail to find the file or -- on Windows -- traverse unexpected paths.

**File:** `ui/src/lib/api.ts`
**Lines:** 1659-1664

**Current code:**
```typescript
export async function dunkstackLoadBridge(filename: string, projectName?: string): Promise<{ status: string; loaded: string; size: number }> {
  const params = new URLSearchParams()
  if (projectName) params.set('project_name', projectName)
  params.set('filename', filename)
  return fetchJSON(`/dunkstack/bridge/load?${params.toString()}`, { method: 'POST' })
}
```

**Fix:** Normalize the filename to strip any path components -- only the basename should be sent. Backslashes are never valid in filenames on the server side (bridge files are always in the flat `bridge_history/` directory):

```typescript
export async function dunkstackLoadBridge(filename: string, projectName?: string): Promise<{ status: string; loaded: string; size: number }> {
  // Strip any path separators -- only the base filename should be sent
  const safeName = filename.replace(/^.*[\\/]/, '')
  const params = new URLSearchParams()
  if (projectName) params.set('project_name', projectName)
  params.set('filename', safeName)
  return fetchJSON(`/dunkstack/bridge/load?${params.toString()}`, { method: 'POST' })
}
```

**Also add server-side validation** in `server/routers/dunkstack.py` line 552:

**Current code (lines 551-563):**
```python
@router.post("/bridge/load")
async def load_bridge(project_name: Optional[str] = None, filename: str = "bridge.md"):
    """Load a specific bridge file as the active bridge for the next session.

    Copies the selected bridge file to bridge.md so the agent reads it on startup.
    """
    agent = _agent_dir(project_name)

    if filename == "bridge.md":
        # Already the current bridge
        path = agent / "bridge.md"
    else:
        path = agent / "bridge_history" / filename
```

**Fix -- add path traversal protection after line 552:**
```python
@router.post("/bridge/load")
async def load_bridge(project_name: Optional[str] = None, filename: str = "bridge.md"):
    """Load a specific bridge file as the active bridge for the next session."""
    # Security: strip path components to prevent directory traversal
    import os
    safe_filename = os.path.basename(filename.replace("\\", "/"))
    if safe_filename != filename:
        logger.warning("Bridge load: sanitized filename %r -> %r", filename, safe_filename)
        filename = safe_filename

    agent = _agent_dir(project_name)
    ...
```

---

## FIX 2 (REFACTOR): Extract shared hooks to a single module

**Problem:** Three hooks are copy-pasted identically between two files:
- `walkie_talkie_hook` -- `dunkstack_session.py` lines 302-400 AND `dunkstack_chat_session.py` lines 393-488
- `bash_hook_with_context` -- `dunkstack_session.py` lines 251-260 AND `dunkstack_chat_session.py` lines 345-351
- `pre_compact_hook` -- `dunkstack_session.py` lines 261-296 AND `dunkstack_chat_session.py` lines 352-391

Any fix to one must be manually copied to the other. This is a maintenance hazard.

**Files involved:**
- `server/services/dunkstack_session.py` (1082 lines)
- `server/services/dunkstack_chat_session.py` (841 lines)

**Fix:** Create a new shared module:

**New file:** `server/services/dunkstack_hooks.py`

Extract these three hook factory functions:

```python
"""
DunkStack Shared Hooks
======================

Shared PreToolUse and PreCompact hooks used by both DunkStackCodingSession
and DunkStackChatSession. Extracted to avoid copy-paste duplication.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Any

from claude_agent_sdk.types import SyncHookJSONOutput

logger = logging.getLogger(__name__)


def create_bash_hook_with_context(bash_security_hook):
    """Create a Bash security hook that passes through to the global bash_security_hook."""
    async def bash_hook_with_context(input_data, tool_use_id=None, context=None):
        return bash_security_hook(input_data)
    return bash_hook_with_context


def create_pre_compact_hook(project_dir: Path):
    """Create a PreCompact hook that guides compaction toward file-based recovery.

    Args:
        project_dir: The project directory containing .agent/ files.
    """
    async def pre_compact_hook(input_data: Any, tool_use_id: Any = None, context: Any = None) -> SyncHookJSONOutput:
        # ... (copy the existing pre_compact_hook body from dunkstack_session.py lines 261-296)
        pass
    return pre_compact_hook


def create_walkie_talkie_hook(project_dir: Path):
    """Create a walkie-talkie PreToolUse hook for file-based messaging.

    Checks .agent/comms/from_human.md for new messages and .agent/comms/control.md
    for session mode (idle/continue/autopilot).

    Args:
        project_dir: The project directory containing .agent/ files.

    Returns:
        Tuple of (hook_function, walkie_state_dict) so the caller can access state.
    """
    walkie_state: dict[str, int] = {"last_size": 0}

    from_human_init = project_dir / ".agent" / "comms" / "from_human.md"
    if from_human_init.exists():
        try:
            walkie_state["last_size"] = len(from_human_init.read_text(encoding="utf-8"))
        except Exception:
            pass

    async def walkie_talkie_hook(input_data: Any, tool_use_id: Any = None, context: Any = None) -> SyncHookJSONOutput:
        # ... (copy the existing walkie_talkie_hook body from dunkstack_session.py lines 302-400)
        pass

    return walkie_talkie_hook, walkie_state
```

**Then in both `dunkstack_session.py` and `dunkstack_chat_session.py`**, replace the inline definitions with imports:

```python
from .dunkstack_hooks import create_bash_hook_with_context, create_pre_compact_hook, create_walkie_talkie_hook

# In the start() method:
bash_hook_with_context = create_bash_hook_with_context(bash_security_hook)
pre_compact_hook = create_pre_compact_hook(Path(self.working_directory))
walkie_talkie_hook, _walkie_state = create_walkie_talkie_hook(Path(self.working_directory))
```

**The hook registration block stays the same** -- only the function definitions move:

```python
hooks: dict[str, list[HookMatcher]] = {
    "PreToolUse": [
        HookMatcher(hooks=[walkie_talkie_hook]),
        HookMatcher(matcher="Bash", hooks=[bash_hook_with_context]),
    ],
    "PreCompact": [
        HookMatcher(hooks=[pre_compact_hook]),
    ],
}
```

**Estimated difficulty:** 3/10 -- pure extract-and-import refactor, no logic changes.

---

## FIX 3 (BUG): Idle mode 10s sleep burns agent turns

**Problem:** When the session mode is "idle", the walkie-talkie hook (in both files) calls `await asyncio.sleep(10)` at line 358 of `dunkstack_session.py` (and line 447 of `dunkstack_chat_session.py`) and then returns a `"block"` decision. This blocks the current tool call and the agent retries. Each retry is a full API turn. So "idle" mode burns 6 turns per minute doing absolutely nothing, accumulating token cost on each blocked tool call because Claude processes the block reason.

**Files:**
- `server/services/dunkstack_session.py` line 358
- `server/services/dunkstack_chat_session.py` line 447

**Current code (dunkstack_session.py line 357-365):**
```python
                # Sleep to avoid rapid-fire blocking that burns turns
                await asyncio.sleep(10)
                return SyncHookJSONOutput(
                    hookSpecificOutput={  # type: ignore[typeddict-item]
                        "hookEventName": "PreToolUse",
                        "decision": "block",
                        "reason": reason,
                    }
                )
```

**The fundamental problem:** A 10-second sleep still allows ~6 blocks per minute. Each block is an API turn with token cost. A 30-minute idle period would burn ~180 turns. The sleep should be much longer, OR the approach should change.

**Fix option A (quick):** Increase sleep to 60 seconds:
```python
                await asyncio.sleep(60)
```

This reduces burn to ~1 turn per minute instead of 6. Still not ideal but 6x better.

**Fix option B (better):** Use exponential backoff for idle blocking. Track consecutive idle blocks:

```python
            if control_mode == "idle":
                # Exponential backoff: 10s, 20s, 40s, 60s, 60s, ...
                idle_count = _walkie_state.get("idle_count", 0)
                _walkie_state["idle_count"] = idle_count + 1
                sleep_secs = min(60, 10 * (2 ** idle_count))
                await asyncio.sleep(sleep_secs)
                ...
```

And reset `idle_count` when mode changes away from idle:
```python
            # Reset idle backoff when not idle
            if control_mode != "idle":
                _walkie_state["idle_count"] = 0
```

Add `"idle_count": 0` to the `_walkie_state` dict initialization.

**If you do Fix 2 first**, only change it in `dunkstack_hooks.py`. Otherwise change it in both files.

---

## FIX 4 (BUG): Walkie-talkie forwarding only works for WebSocket sessions

**Problem:** The `write_from_human` endpoint at `server/routers/dunkstack.py` line 302-322 only forwards messages to sessions in `_agent_sessions` (line 1220). This dict only contains `DunkStackChatSession` instances (WebSocket-based). REST-started coding sessions (`DunkStackCodingSession` from `dunkstack_session.py`) are stored in a separate `_sessions` dict inside `dunkstack_session.py` and are never checked for forwarding.

**Result:** If the user starts a DunkStack coding agent via the REST endpoint (or from the Agent panel), and then types a walkie-talkie message, the message gets written to `from_human.md` but is NOT forwarded to the running agent. The agent only sees it at the next tool-call boundary when the hook re-reads the file -- which could be many seconds or even minutes later.

**File:** `server/routers/dunkstack.py`
**Lines:** 302-322

**Current code:**
```python
    forwarded = False
    if _agent_sessions:
        nudge = (
            f"New message from the human was posted to .agent/comms/from_human.md at {timestamp}. "
            "Re-read .agent/comms/from_human.md now and respond to the latest message. "
            "Write your response to .agent/comms/to_human.md (NOT in chat). "
            "Chat reply: 1-sentence status only."
        )
        for session_id, session in list(_agent_sessions.items()):
            try:
                async for event in session.send_message(nudge):
                    await _broadcast(event)
                forwarded = True
                logger.info("Forwarded walkie-talkie message to agent session %s", session_id)
            except Exception as e:
                logger.warning("Failed to forward message to agent session %s: %s", session_id, e)
```

**Fix:** Also check the REST coding session registry from `dunkstack_session.py`:

```python
    # Forward to WebSocket-based chat sessions
    forwarded = False
    if _agent_sessions:
        nudge = (
            f"New message from the human was posted to .agent/comms/from_human.md at {timestamp}. "
            "Re-read .agent/comms/from_human.md now and respond to the latest message. "
            "Write your response to .agent/comms/to_human.md (NOT in chat). "
            "Chat reply: 1-sentence status only."
        )
        for session_id, session in list(_agent_sessions.items()):
            try:
                async for event in session.send_message(nudge):
                    await _broadcast(event)
                forwarded = True
                logger.info("Forwarded walkie-talkie message to WS agent session %s", session_id)
            except Exception as e:
                logger.warning("Failed to forward to WS agent session %s: %s", session_id, e)

    # Also forward to REST-started coding sessions
    if not forwarded:
        from ..services.dunkstack_session import get_coding_session, list_coding_sessions as _list_coding
        for s_info in _list_coding():
            p_name = s_info.get("project_name")
            if not p_name:
                continue
            coding_session = get_coding_session(p_name)
            if coding_session and coding_session.status == "running":
                try:
                    async for event in coding_session.send_message(nudge):
                        await _broadcast(event)
                    forwarded = True
                    logger.info("Forwarded walkie-talkie message to REST coding session %s", p_name)
                except Exception as e:
                    logger.warning("Failed to forward to REST coding session %s: %s", p_name, e)

    return {"status": "ok", "timestamp": timestamp, "forwarded_to_agent": forwarded}
```

**Key detail:** `DunkStackCodingSession.send_message()` exists (line 542 of `dunkstack_session.py`) and returns the same `AsyncGenerator[dict, None]` as the chat session. So the same iteration pattern works.

**Note:** The `nudge` variable must be defined before the `if not forwarded` block. Move the `nudge` definition above the first `if _agent_sessions` block, or duplicate it. Simplest is to define it once before both blocks:

```python
    nudge = (
        f"New message from the human was posted to .agent/comms/from_human.md at {timestamp}. "
        "Re-read .agent/comms/from_human.md now and respond to the latest message. "
        "Write your response to .agent/comms/to_human.md (NOT in chat). "
        "Chat reply: 1-sentence status only."
    )

    forwarded = False
    # Forward to WebSocket-based chat sessions
    if _agent_sessions:
        for session_id, session in list(_agent_sessions.items()):
            ...

    # Also forward to REST-started coding sessions
    if not forwarded:
        ...
```

---

## Checklist

- [ ] **FIX 1** -- Sanitize `filename` in `dunkstackLoadBridge` (client) and `load_bridge` (server) to strip path components
- [ ] **FIX 2** -- Create `server/services/dunkstack_hooks.py` with shared hook factories; update both session files to import
- [ ] **FIX 3** -- Increase idle sleep from 10s to 60s (or implement exponential backoff) in walkie-talkie hook
- [ ] **FIX 4** -- Add REST coding session forwarding to `write_from_human` endpoint alongside existing WS forwarding
- [ ] **VERIFY** -- Run `cd ui && npm run build` after client-side changes (Fix 1)
- [ ] **VERIFY** -- Run `cd ui && npm run lint` after client-side changes
- [ ] **VERIFY** -- Run `ruff check server/services/dunkstack_hooks.py` after creating shared module
- [ ] **VERIFY** -- Test walkie-talkie forwarding works for BOTH WS and REST sessions
