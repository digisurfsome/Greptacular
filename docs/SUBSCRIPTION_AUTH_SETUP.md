# Subscription Auth Setup Guide

**Purpose:** How to wire up Claude model calls using the Max subscription instead of burning API credits.
**Audience:** Any agent, PRD author, or developer adding a feature that calls a Claude model.
**Last Updated:** 2026-03-23

---

## The Rule (One Sentence)

Every Claude model call in AutoForge uses **subscription OAuth** — never an API key — so the owner pays $0 per request on their $200/month Max plan.

---

## Why This Matters

The owner has a Claude Max subscription ($200/month). All Claude models — Opus 4.6, Sonnet 4.6, Haiku — with both 200K and 1M context are **included at no extra cost**. If code accidentally uses an API key instead, it routes to pay-per-use billing and costs real money for something already paid for.

This has happened repeatedly. At least 6 different agents introduced API-key fallback patterns that silently burned credits. The fix is always the same: force subscription auth, never fall back to API keys.

---

## How Subscription Auth Works

```
┌──────────────────────────────────────────────────────────┐
│  get_effective_sdk_env(force_subscription=True)           │
│                                                          │
│  1. Clears ANTHROPIC_API_KEY (set to empty string)       │
│  2. Clears ANTHROPIC_AUTH_TOKEN (set to empty string)    │
│  3. Claude CLI can't find an API key                     │
│  4. Falls back to ~/.claude/.credentials.json            │
│  5. That file has OAuth tokens from `claude login`       │
│  6. Subscription auth kicks in → $0 per request          │
└──────────────────────────────────────────────────────────┘
```

The single source of truth is `get_effective_sdk_env()` in `registry.py` (~line 792). Every Claude call in the system goes through this function.

---

## Setup Checklist for New Features

If you're building a feature that calls Claude:

- [ ] Import `get_effective_sdk_env` from `registry.py`
- [ ] Call it with `force_subscription=True`
- [ ] Pass the returned env dict to your `ClaudeSDKClient` or subprocess
- [ ] Do NOT import `anthropic` and create `anthropic.Anthropic(api_key=...)`
- [ ] Do NOT read `ANTHROPIC_API_KEY` from env or settings
- [ ] Do NOT add a fallback that uses an API key if subscription fails

---

## Code Examples

### The Right Way — Simple Prompt (No Tools)

Use this for any service that sends a prompt and gets text back.

```python
import shutil
import tempfile
from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
from registry import get_effective_sdk_env

async def call_claude(system_prompt: str, user_message: str, model: str = "claude-sonnet-4-6") -> str:
    system_cli = shutil.which("claude")
    if not system_cli:
        raise RuntimeError("Claude CLI not found on PATH")

    # THIS IS THE KEY LINE — forces subscription auth
    sdk_env = get_effective_sdk_env(force_subscription=True)

    scratch = tempfile.mkdtemp(prefix="my_feature_")

    client = ClaudeSDKClient(
        options=ClaudeAgentOptions(
            model=model,
            cli_path=system_cli,
            system_prompt=system_prompt,
            env=sdk_env,
            max_turns=1,
            permission_mode="acceptEdits",
            allowed_tools=[],
            cwd=scratch,
        )
    )

    try:
        await client.__aenter__()
        await client.query(user_message)

        full_text = ""
        try:
            async for msg in client.receive_response():
                if type(msg).__name__ == "AssistantMessage" and hasattr(msg, "content"):
                    for block in msg.content:
                        if type(block).__name__ == "TextBlock" and hasattr(block, "text"):
                            full_text += block.text
        except Exception as exc:
            # SDK throws "Unknown message type: rate_limit_event" AFTER
            # collecting the full response. Recover what we have.
            if full_text.strip() and "unknown message type" in str(exc).lower():
                pass  # Use the text we already collected
            elif full_text.strip():
                pass  # Try to use what we have
            else:
                raise  # No text at all — re-raise

        if not full_text.strip():
            raise RuntimeError("Claude SDK returned empty response")
        return full_text.strip()
    finally:
        try:
            await client.__aexit__(None, None, None)
        except Exception:
            pass
```

### The Right Way — Interactive Chat (With Tools)

Use this for chat panels, assistants, or multi-turn conversations.

```python
from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
from registry import get_effective_sdk_env

system_cli = shutil.which("claude")
sdk_env = get_effective_sdk_env(force_subscription=True)

client = ClaudeSDKClient(
    options=ClaudeAgentOptions(
        model="claude-opus-4-6",
        cli_path=system_cli,
        system_prompt=system_prompt,
        env=sdk_env,
        max_turns=100,
        permission_mode="acceptEdits",
        allowed_tools=["Read", "Grep", "Glob", "Write", "Edit"],
        cwd=str(working_directory),
    )
)

await client.__aenter__()
await client.query(user_message)
async for msg in client.receive_response():
    # stream response to frontend...
await client.__aexit__(None, None, None)
```

### The Right Way — Bash/Build Scripts

```bash
#!/bin/bash
# ALWAYS unset API key so Claude CLI uses subscription
unset ANTHROPIC_API_KEY 2>/dev/null || true

# Now claude commands use subscription OAuth automatically
claude -p --model sonnet "your prompt here"
```

---

## The Wrong Way (Do Not Do These)

### Wrong: Direct Anthropic SDK with API key

```python
# BAD — burns API credits
import anthropic
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
response = client.messages.create(model="claude-sonnet-4-6", ...)
```

### Wrong: Hardcoded API key

```python
# BAD — hardcoded key, burns credits, security risk
client = anthropic.Anthropic(api_key="sk-ant-api03-...")
```

### Wrong: Reading key from settings

```python
# BAD — reads API key from settings/env, bypasses subscription
api_key = settings.get("api_auth_token") or os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=api_key)
```

### Wrong: API key fallback on error

```python
# BAD — falls back to API key when SDK fails
try:
    result = await _call_via_sdk(prompt)
except Exception:
    # "Just in case" fallback — THIS IS THE #1 CAUSE OF BURNED CREDITS
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    result = client.messages.create(...)
```

### Wrong: Exporting API key in bash

```bash
# BAD — forces CLI to use API key billing
export ANTHROPIC_API_KEY="sk-ant-..."
claude -p "do something"
```

---

## Where Credentials Live

| Location | What's There | Used By |
|----------|-------------|---------|
| `~/.claude/.credentials.json` | OAuth tokens from `claude login` | Subscription auth (the correct path) |
| `~/.autoforge/.env` | `ANTHROPIC_API_KEY=sk-ant-...` | API billing (cleared by `force_subscription`) |
| Settings UI (SQLite registry) | `api_auth_token` field | API billing (cleared by `force_subscription`) |

---

## How to Verify It's Working

Check server logs for these lines:

```
>>> SUBSCRIPTION AUTH CONFIRMED: ANTHROPIC_API_KEY='', ANTHROPIC_AUTH_TOKEN='' <<<
>>> SUBSCRIPTION BILLING: Processing via SDK (force_subscription=True) <<<
```

If you see `ANTHROPIC_API_KEY` with a **non-empty** value, there's a bug.

---

## Pre-Commit Checks

Before committing any code that calls a Claude model:

```bash
# 1. No raw API key usage without force_subscription nearby
grep -rn "ANTHROPIC_API_KEY" your_file.py

# 2. No direct anthropic client creation
grep -rn "anthropic.Anthropic(" your_file.py

# 3. No hardcoded keys anywhere
grep -rn "sk-ant-" your_file.py
```

If any check finds a match without proper `force_subscription=True` handling, fix it before committing.

---

## SDK Gotchas

### 1. permission_mode

Use `"acceptEdits"` — NOT `"bypassPermissions"`. The bypass mode crashes the Bun runtime on Windows (exit code 3). Pair it with a settings file that has `{"permissions": {"defaultMode": "acceptEdits", "allow": []}}`.

### 2. rate_limit_event exception

The SDK throws `"Unknown message type: rate_limit_event"` as an **exception**, not a yielded message. This kills the `async for msg in client.receive_response()` loop AFTER the full response has been collected. Always wrap with try/except and recover the text (see code example above).

### 3. Logging

Every `_call_via_sdk()` should log to both `logger.info()` and an `on_progress()` callback. SDK calls take 120-200 seconds. Without logs streaming to the browser, debugging is impossible.

---

## Reference Implementations

Copy from these working files:

| What You're Building | Copy From | Pattern |
|---------------------|-----------|---------|
| Simple prompt-in/text-out | `server/services/yt_processor.py` → `_call_via_sdk()` | Full logging + error recovery |
| Interactive chat panel | `server/services/workspace_chat_session.py` | Multi-turn with tools |
| Read-only assistant | `server/services/assistant_chat_session.py` | Chat with read-only tools |
| Full coding agent | `client.py` → `create_client()` | MCP servers + security hooks |

---

## Quick Reference Card

```
CALLING CLAUDE FROM PYTHON:
  1. from registry import get_effective_sdk_env
  2. sdk_env = get_effective_sdk_env(force_subscription=True)
  3. Pass sdk_env to ClaudeSDKClient(options=ClaudeAgentOptions(env=sdk_env, ...))
  4. Done. Subscription auth handles the rest.

CALLING CLAUDE FROM BASH:
  1. unset ANTHROPIC_API_KEY 2>/dev/null || true
  2. claude -p "your prompt"
  3. Done.

NEVER DO:
  - anthropic.Anthropic(api_key=...)
  - os.getenv("ANTHROPIC_API_KEY") for auth
  - Fallback patterns that switch to API key on error
  - export ANTHROPIC_API_KEY in build scripts
```
