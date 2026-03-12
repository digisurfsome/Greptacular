# Subscription Auth & WebSocket Architecture — Mandatory Reference

**Status:** Active — ALL agents MUST follow this
**Date:** 2026-03-12

---

## 🚨🚨🚨 SUBSCRIPTION vs API KEY AUTH 🚨🚨🚨

```
┌─────────────────────────────────────────────────────────────────────┐
│  ALL 200K MODELS → SUBSCRIPTION ONLY (force_subscription=True)     │
│  ONLY 1M TOKEN MODELS → API KEY                                    │
│  NO EXCEPTIONS. NO API KEYS FOR 200K MODELS. EVER.                 │
└─────────────────────────────────────────────────────────────────────┘
```

### Why This Matters

The owner has a $200/month Max subscription. 200K context models (Opus 4.6, Sonnet 4.6, Haiku) are INCLUDED in the subscription at no extra cost. If you accidentally use an API key for these models, it burns pay-per-use API credits instead — costing real money for something that's already paid for.

### The Rule

| Model Context | Auth Method | How |
|---|---|---|
| 200K models (opus-4-6, sonnet-4-6, haiku) | **Subscription ONLY** | `force_subscription=True` → clears API key → uses OAuth |
| 1M token models | API key | Normal `ANTHROPIC_API_KEY` env var |

### The Single Source of Truth: `get_effective_sdk_env()`

Location: `registry.py` (line ~792)

Every Claude call in the entire system goes through this function. Here's what it does:

1. **Reads environment variables** — `ANTHROPIC_API_KEY`, `CLAUDE_CODE_USE_VERTEX`, etc. from process env (loaded from `~/.autoforge/.env`)
2. **Checks Settings UI** — if the user saved an API key via the Settings gear icon, it's stored in SQLite registry and used as `ANTHROPIC_API_KEY` if no env var exists
3. **Subscription override** — when `force_subscription=True`, it **clears both** `ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN` so the Claude CLI falls back to `~/.claude/.credentials.json` (subscription OAuth login)

### Who Uses What

| Component | Auth Method | Calls `get_effective_sdk_env()`? |
|---|---|---|
| Coding Agent (`client.py`) | Subscription (`force_subscription=True`) | Yes, indirectly via `ClaudeSDKClient` |
| YT Lab (`yt_processor.py`, `yt_discovery.py`) | SDK first → API key fallback | Yes — `_call_via_sdk()` uses it |
| Workspace Chat | Multi-provider (Claude/Codex/Gemini) | Yes, via `workspace_chat_session` |
| Assistant Chat | Claude SDK subprocess | Yes |
| DunkStack | NONE — doesn't make API calls | No |

### Where Credentials Live

| Location | What's There |
|---|---|
| `~/.autoforge/.env` | `ANTHROPIC_API_KEY=sk-ant-...` (manual setup) |
| `~/.claude/.credentials.json` | OAuth tokens from `claude login` (subscription) |
| Settings UI → SQLite registry | `api_auth_token` field (saved via gear icon) |

### The SDK → API Fallback in YT Lab

```
1. Try _call_via_sdk()
   → Uses ClaudeSDKClient (subscription auth)
   → If fails: logs "SDK unavailable" and falls back

2. Fallback: _call_via_api()
   → Uses anthropic.Anthropic(api_key=...)
   → Reads ANTHROPIC_API_KEY from env or Settings
   → This COSTS MONEY (burns API credits)
```

### ❌ WRONG vs ✅ RIGHT — Copy-Paste Examples

**When writing Python code that calls Claude:**

❌ **WRONG — burns API credits:**
```python
import anthropic
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
response = client.messages.create(model="claude-sonnet-4-6", ...)
```

❌ **ALSO WRONG — hardcoded key:**
```python
client = anthropic.Anthropic(api_key="sk-ant-api03-...")
```

❌ **ALSO WRONG — reading key from settings/env directly:**
```python
api_key = settings.get("api_auth_token") or os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=api_key)
```

✅ **RIGHT — uses subscription via SDK:**
```python
from registry import get_global_settings
from client import ClaudeSDKClient

# For subprocess-based calls (most common in AutoForge):
env = get_effective_sdk_env(provider="claude", force_subscription=True)
# Pass env to subprocess — subscription OAuth kicks in automatically

# For direct SDK calls:
# Use ClaudeSDKClient which handles auth correctly
```

✅ **RIGHT — for new workspace features:**
```python
# In your router/service, get env vars the correct way:
from registry import get_effective_sdk_env

sdk_env = get_effective_sdk_env(
    provider="claude",
    model="claude-sonnet-4-6",
    force_subscription=True  # THIS IS THE KEY LINE
)
# Pass sdk_env to your subprocess or SDK client
```

**When writing bash scripts:**

❌ **WRONG:**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
claude -p "do something"
```

✅ **RIGHT:**
```bash
unset ANTHROPIC_API_KEY 2>/dev/null || true
claude -p "do something"
```

### Pre-Commit Self-Check (MANDATORY)

Before committing ANY code that touches AI model calls, run these checks:

```bash
# Check 1: Search for raw API key usage in your new/modified files
grep -rn "ANTHROPIC_API_KEY" your_new_file.py
# If it appears WITHOUT force_subscription=True nearby → YOU HAVE A BUG

# Check 2: Search for direct anthropic client creation
grep -rn "anthropic.Anthropic(" your_new_file.py
# If it appears with api_key= parameter → YOU HAVE A BUG

# Check 3: Search for hardcoded keys
grep -rn "sk-ant-" your_new_file.py
# If ANYTHING matches → YOU HAVE A CRITICAL BUG
```

**If any check fails, fix it before committing. No exceptions.**

### For CLI Build Scripts

Always include this at the top of any bash build script:

```bash
# Unset API key so Claude CLI uses Max subscription instead of API credits
unset ANTHROPIC_API_KEY 2>/dev/null || true
```

This ensures `claude -p` uses the subscription login, not the API key.

### Token Tracking with `--output-format json`

**The Anthropic dashboard does NOT show subscription token usage.** To track how many tokens each build burns, always use:

```bash
claude -p --output-format json --model sonnet --dangerously-skip-permissions "prompt" > output.json
```

The JSON includes `usage.input_tokens`, `usage.output_tokens`, `usage.cache_creation_input_tokens`, `total_cost_usd` (API-equivalent cost), and `num_turns`. See `docs/SONNET_OPUS_OPTIMIZATION.md` for full field reference and parsing examples.

### How Auth Flows Through WebSocket

```
Frontend opens WebSocket
  → sends "start" with provider: "claude", model: "claude-opus-4-6"
  → Backend workspace.py router receives it
  → Creates BackgroundSession (background_session_manager.py)
  → BackgroundSession creates WorkspaceChatSession
  → WorkspaceChatSession calls get_effective_sdk_env()
  → SDK env has subscription credentials (force_subscription=True for Claude)
  → Claude CLI subprocess starts with those env vars
  → Subscription OAuth kicks in automatically
  → No API key burned
```

---

## 🚨 ONE WEBSOCKET PER PAGE 🚨

```
┌─────────────────────────────────────────────────────────────────────┐
│  ONE WebSocket connection per chat page. That's it.                 │
│  Do NOT open multiple WebSocket connections on the same page.       │
│  Do NOT modify the existing WebSocket hook or chat component.       │
└─────────────────────────────────────────────────────────────────────┘
```

### The Connection

Frontend connects to: `ws://localhost:8888/api/workspace/ws`

### Message Flow — Starting a New Conversation

**CLIENT sends:**
```json
{
  "type": "start",
  "conversation_id": null,
  "working_directory": "C:/path/to/repo",
  "context_mode": "1m",
  "model": "claude-opus-4-6",
  "provider": "claude"
}
```

**SERVER responds:**
```json
{
  "type": "session_created",
  "session_id": "abc-123",
  "conversation_id": 42
}
```

### Message Flow — Sending a Message

**CLIENT sends:**
```json
{ "type": "message", "content": "Build me a todo app" }
```

**SERVER streams back:**
```json
{ "type": "text", "content": "I'll start by..." }
{ "type": "text", "content": "creating the..." }
{ "type": "tool_call", "tool": "Write", "input": {} }
{ "type": "token_usage", "total": 15000, "budget": 1000000 }
{ "type": "session_completed" }
```

### Message Flow — Resuming an Existing Conversation

**CLIENT sends:**
```json
{
  "type": "attach",
  "session_id": "abc-123",
  "since_seq": 0
}
```

**SERVER responds:**
```json
{ "type": "attached", "session_id": "abc-123", "state": "running" }
{ "type": "replay", "events": [] }
{ "type": "replay_done", "current_seq": 47 }
```

### Other Client Messages

```json
{ "type": "walkie_talkie", "content": "..." }
{ "type": "ping" }
{ "type": "detach" }
```

### Other Server Messages

```json
{ "type": "heartbeat" }
{ "type": "token_usage", "total": 15000, "budget": 1000000, "model": "..." }
{ "type": "session_failed", "error": "..." }
{ "type": "error", "message": "..." }
{ "type": "pong" }
```

### Token Usage Events (Context Window Tracking)

The server sends `token_usage` events during streaming:

```json
{
  "type": "token_usage",
  "total": 43000,
  "budget": 1000000,
  "model": "claude-opus-4-6"
}
```

This is how the sidebar shows "43K" — the frontend reads `total` from these events and displays it. Store the latest value in `localStorage` per chat page so inactive pages show their last known context usage.

### Key Files — DO NOT MODIFY

| File | What It Does |
|---|---|
| `ui/src/hooks/useWorkspaceChat.ts` | Frontend WebSocket hook. Manages connection, sends/receives messages, tracks tokens. **Don't modify.** |
| `ui/src/components/workspace/WorkspaceChat.tsx` | Chat UI component. Renders messages, input box, streaming state. **Don't modify.** |
| `server/routers/workspace.py` | Backend WebSocket endpoint. Creates sessions, routes messages. **Don't modify.** |
| `server/services/background_session_manager.py` | Session lifecycle. Runs Claude in background, buffers output. **Don't modify.** |

### What the Builder Creates

The builder only creates:
- New `WorkspacePage.tsx` (page layout with sidebar + tabs + routing)
- Route configuration to handle `/#/workspace/:chatId`

Everything else already works. Don't reinvent the WebSocket. Don't create a second connection. Use what's there.

---

## For Agents Reading This

Before you write ANY code that:
- Calls an AI model → Check subscription vs API key (see auth section above)
- Opens a WebSocket → Use the ONE existing connection (see WebSocket section above)
- Creates a build script → Include `unset ANTHROPIC_API_KEY` at the top
- Creates a build script → Use `--output-format json` to capture token usage (see Token Tracking section above)

**If you violate these rules, you are creating a bug that costs the user real money.**
