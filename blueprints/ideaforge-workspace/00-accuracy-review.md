# IdeaForge Workspace: Accuracy Review & Corrections

## Overview

This document reviews the handoff at `handoffs/ideaforge-million-token-workspace.md` against the actual AutoForge codebase. Every claim was verified against source code. Issues are categorized as **INCORRECT** (wrong information), **INCOMPLETE** (missing critical details), or **CONFIRMED** (accurate as stated).

---

## Issues Found & Corrections

### ISSUE 1: Database Scoping — INCORRECT

**Handoff says:** "Extend the existing `assistant_database.py` — do NOT create a separate database."

**Reality:** `assistant_database.py` is **per-project**. Every function requires `project_dir: Path` as its first argument. The database lives at `{project_dir}/.autoforge/assistant.db`. The workspace is project-independent — it's a global concept that exists outside any single project.

**Correction:** The workspace needs its own global database at `~/.autoforge/workspace.db`. Create a new `server/services/workspace_database.py` that uses `Path.home() / ".autoforge" / "workspace.db"` as its database path. The new module should follow the same patterns as `assistant_database.py` (SQLAlchemy, engine caching, session factories) but with a global scope instead of per-project scope.

---

### ISSUE 2: CSS Variable Names — INCORRECT

**Handoff says:** References neobrutalism as THE design system. The project's CLAUDE.md also references `--color-neo-pending`, `--color-neo-progress`, `--color-neo-done`.

**Reality:** These CSS variable names **do not exist** in the codebase. The actual variables are:
- `--color-status-pending` (not `--color-neo-pending`)
- `--color-status-progress` (not `--color-neo-progress`)
- `--color-status-done` (not `--color-neo-done`)

Furthermore, neobrutalism is only **1 of 6 themes** (Twitter, Claude, Neo Brutalism, Retro Arcade, Aurora, Business). The UI must use theme-agnostic Tailwind tokens like `bg-background`, `text-foreground`, `bg-card`, `border-border`, `text-muted-foreground`, etc. These adapt to all themes automatically.

**Correction:** All workspace components must use the `@theme inline` tokens defined in `ui/src/styles/globals.css`. Never hardcode neobrutalism-specific styles. Use Tailwind classes like `bg-background`, `text-foreground`, `bg-card`, `border-border`, `rounded-lg`, `shadow-md`, etc.

---

### ISSUE 3: Routing Mechanism — INCOMPLETE

**Handoff says:** "Add to `App.tsx` router alongside existing routes."

**Reality:** There is **no React Router** (no react-router-dom, no HashRouter, no BrowserRouter). The app uses custom hand-rolled hash routing:
- `ui/src/lib/routes.ts` — defines route detection functions (`isStylePreviewRoute()`, `isQuadPreviewRoute()`)
- `ui/src/main.tsx` — `Root()` function checks each route function and returns the matching component

**Correction:** To add `/#/workspace`:
1. Add `isWorkspaceRoute()` to `ui/src/lib/routes.ts`
2. Add conditional to `Root()` in `ui/src/main.tsx`
3. Navigation uses `window.location.hash = '#/workspace'`

---

### ISSUE 4: WebSocket URL — INCOMPLETE

**Handoff says:** `WS /ws/{conversation_id}`

**Reality:** All existing WebSocket endpoints include their router prefix. The assistant WebSocket is at `/api/assistant/ws/{project_name}` (not just `/ws/{project_name}`).

**Correction:** The workspace WebSocket should be at `/api/workspace/ws/{conversation_id}` (with the full router prefix). The URL must match the `APIRouter(prefix="/api/workspace")` pattern.

---

### ISSUE 5: Bash Tool Security — INCOMPLETE

**Handoff says:** Enable Bash tool in the workspace.

**Reality:** The handoff lists Bash as a tool but doesn't mention the security hook. The coding agent in `client.py` adds a `PreToolUse` hook for Bash validation via `bash_security_hook` from `security.py`. Without this hook, Bash would be completely unguarded.

**Correction:** The workspace must add a `PreToolUse` hook for the Bash tool, using the same `bash_security_hook` from `security.py`. This validates commands against the allowlist and blocklist.

---

### ISSUE 6: Server Cleanup — MISSING

**Handoff says:** Nothing about server lifecycle cleanup.

**Reality:** `server/main.py` has a lifespan handler that cleans up sessions on shutdown:
```python
await cleanup_assistant_sessions()
await cleanup_all_expand_sessions()
```

**Correction:** The workspace needs its own `cleanup_all_workspace_sessions()` function registered in the main.py lifespan shutdown block.

---

### ISSUE 7: Security Settings JSON — MISSING

**Handoff says:** Nothing about a settings file.

**Reality:** Every chat session type writes a security settings JSON file to disk (e.g., `.autoforge/.claude-assistant-settings.json`). This file contains `permissions.allow` and `permissions.defaultMode`. The Claude SDK reads this file for security enforcement.

**Correction:** The workspace needs its own settings file (e.g., `~/.autoforge/.workspace-settings.json`) that includes Write, Edit, and Bash permissions.

---

### ISSUE 8: Context Loading Approach — INCOMPLETE

**Handoff says:** "Instead of 35-message cap, use intelligent context loading: Always include last 100 messages verbatim"

**Reality:** The 35-message cap is correct (verified at line 358 of `assistant_chat_session.py`). However, the handoff's proposed approach of "100 messages verbatim" needs more nuance. Each message is currently truncated to 500 chars. At 100 messages x 500 chars = 50K chars = ~12.5K tokens minimum. With full messages (no truncation for the workspace), 100 messages could easily be 200K-500K tokens.

**Correction:** The 100-message target is reasonable for a 1M window, but:
1. Don't truncate messages (the whole point is the large context window)
2. Track actual token counts, not just message counts
3. Dynamically adjust how many messages to include based on remaining context budget
4. Always prioritize the summary + recent messages over older verbatim messages

---

### ISSUE 9: `make_multimodal_message()` — MISSING FROM PLAN

**Handoff says:** Nothing about multimodal support.

**Reality:** `chat_constants.py` exports `make_multimodal_message()` which wraps content blocks (text + images) for the Claude SDK's `query()` method. The workspace's file library feature will need this for image files.

**Correction:** When implementing file injection into chat context, use `make_multimodal_message()` for image files. Text files can be injected as plain text context.

---

## Confirmed Claims (Accurate)

| Claim | Verification |
|-------|-------------|
| `permission_mode = "acceptEdits"` | Correct — used by `spec_chat_session.py` with Write/Edit tools |
| 35-message history cap | Correct — line 358 of `assistant_chat_session.py` |
| Default model: Claude Opus | Correct — `DEFAULT_MODEL = "claude-opus-4-6"` in `registry.py` |
| Fork `assistant_chat_session.py` | Correct approach — it's the right starting point |
| Tool enablement via `allowed_tools` | Correct — flat list of strings on `ClaudeAgentOptions` |
| MCP server for features | Correct — but workspace doesn't need the feature MCP |
| WebSocket streaming protocol | Correct — `type` discriminator JSON messages |
| `assistant_database.py` schema | Correct — `conversations` and `conversation_messages` tables exist exactly as described |
| Conversation resume via conversation_id | Correct — passed in `start` message, loaded from DB |
| Claude SDK client creation pattern | Correct — `ClaudeSDKClient(options=ClaudeAgentOptions(...))` |
| Router registration pattern | Correct — 3-file pattern (router file, `__init__.py`, `main.py`) |
| Context budget bar concept | Present and well-described with sticky positioning |
| Auto-summary side-channel concept | Sound approach — use Haiku for fast/cheap summaries |

---

## Summary

**Total issues found: 9**
- 2 INCORRECT (database scoping, CSS variables)
- 7 INCOMPLETE/MISSING (routing mechanism, WS URL, Bash security, cleanup, settings JSON, context loading, multimodal support)

**Verdict:** The plan is architecturally solid. The core concepts (full-page workspace, persistent 1M-window chats, context budget visualization, auto-summaries, file library, GitHub integration) are all sound and buildable. The issues are implementation details, not design flaws — the kind of things that surface when you map a plan against actual code.

All corrections have been incorporated into the phase blueprints that follow.
