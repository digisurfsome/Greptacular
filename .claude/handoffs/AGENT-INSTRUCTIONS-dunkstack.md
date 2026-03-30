# AGENT TASK: Fix DunkStack System

**READ THESE FILES FIRST (in order):**
1. `.claude/handoffs/dunkstack-diagnosis-handoff.md` — full diagnosis with every bug and fix
2. This file — your task list

**IMPORTANT RULES:**
- Test after EACH fix. Don't batch everything then discover it's broken.
- ALL Claude models use subscription auth (force_sub = True). NEVER use API keys.
- Read `CLAUDE.md` in the project root for full project rules
- The "two brains" problem (two session classes) is the biggest issue — Task 3 fixes it

---

## TASK LIST (Do in this order)

### Task 1: Fix Billing Violation (2 minutes)
**CRITICAL — this is burning real money**

1. `server/services/dunkstack_chat_session.py` line 311: Change `force_sub = self.context_mode != "1m"` to `force_sub = True`
2. `server/services/dunkstack_session.py`: Find `_is_subscription_mode()` method — it returns `self.context_window <= 200_000`. Change to always return `True`.

### Task 2: Fix Haiku Model Mapping (2 minutes)
`ui/src/pages/DunkStackPage.tsx` line 259: The ternary only handles opus and sonnet. Add haiku:
```
preset.model === 'haiku' ? 'claude-haiku-4-5-20251001' : preset.model === 'opus' ? 'claude-opus-4-6' : 'claude-sonnet-4-6'
```

### Task 3: Merge Two Brains Into One (BIGGEST TASK)
**Goal**: The WebSocket chat session (`dunkstack_chat_session.py`) needs the walkie-talkie hooks and PreCompact hooks from the coding session (`dunkstack_session.py`). Then use the chat session everywhere.

**What to do:**
1. Copy the `walkie_talkie_hook` from `dunkstack_session.py` lines 291-389 into `dunkstack_chat_session.py`
2. Copy the `pre_compact_hook` from `dunkstack_session.py` lines 391-414 into `dunkstack_chat_session.py`
3. Wire both hooks into the `hooks` dict when creating the ClaudeSDKClient
4. Update the WebSocket handler in `dunkstack.py` to use the enhanced chat session for everything
5. The REST `/agent/start` endpoint should also use the chat session (streamed via WebSocket instead of blocking HTTP)

### Task 4: Fix Safety Status Project Scoping
`server/routers/dunkstack.py` line 727: `_get_safety_status()` ignores project_name. Pass it through the call chain so it reads the correct project's `.agent/settings/config.yml`.

### Task 5: Add receive_response() try/except
Both session files need the error recovery pattern from CLAUDE.md:
```python
try:
    async for msg in client.receive_response():
        # ... collect full_text ...
except Exception as exc:
    if full_text.strip() and "unknown message type" in str(exc).lower():
        pass  # Use the text we already have
    elif full_text.strip():
        pass  # Try to use what we have
    else:
        raise  # No text — re-raise
```

### Task 6: Fix WebSocket Project Scoping
`server/routers/dunkstack.py` line 1299: `_agent_dir()` called without project_name. Pass it from session context.

### Task 7: Handle Missing WebSocket Events
In `ui/src/hooks/useDunkStack.ts`, add cases for:
- `hard_stop` — show notification to user
- `model_preset_update` — update local state

### Task 8: Make Token State Per-Project
`server/routers/dunkstack.py` line 164: `_token_state` is global. Key it by project_name so tokens from project A don't bleed into project B.

### Task 9: Add Polling Loop (Same as Workspace)
Same concept as Workspace: agent polls a small file every ~30 seconds to keep the turn alive. Walkie-talkie messages (via the file-based hook from Task 3) get injected during polls.

Update the system prompt in `dunkstack_session.py` STARTUP_MESSAGE to include:
- After completing tasks, enter a polling loop
- Read `.agent/comms/walkie-check.txt` every ~30 seconds
- Process any new messages from `from_human.md` (the hook handles this)
- Continue until user says "end session" or context approaches limit

### Task 10: Add Session Chaining UI
DunkStack already HAS bridge save/restore. But it needs:
1. A way to select which previous session's bridge to load when starting a new agent
2. Show a list of saved bridges in the sidebar or startup form
3. Selected bridge gets passed to the startup message

---

## TESTING CHECKLIST

1. [ ] Start agent with Opus 1M — verify subscription auth (no API key in logs)
2. [ ] Start agent with Haiku — verify it actually uses Haiku model
3. [ ] Send walkie-talkie message via comms — agent receives it via hook
4. [ ] Agent polls and stays alive for 5+ minutes
5. [ ] Click Idle — agent pauses
6. [ ] Click Continue — agent resumes
7. [ ] Context reaches warning threshold — UI shows warning
8. [ ] Context reaches handoff threshold — bridge auto-saves
9. [ ] Save bridge manually — file appears in `.agent/bridge.md`
10. [ ] Start new agent — reads previous bridge on startup
11. [ ] Token counter is per-project, not global
12. [ ] `cd ui && npm run build` succeeds
13. [ ] `cd ui && npm run lint` passes
