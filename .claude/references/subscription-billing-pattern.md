# Subscription Billing Pattern (ClaudeSDKClient)

> **Keywords:** subscription, billing, free, CLI, API key, OAuth, ClaudeSDKClient, force_subscription, sdk_env, no API credits

## TL;DR

When calling Claude AI from any service in this codebase, **always use `ClaudeSDKClient`** from the Agent SDK. This routes through subscription OAuth (free) instead of burning API credits.

**NEVER** use raw `subprocess.run(["claude", "-p", ...])` — it fails to authenticate with subscription and silently falls back to paid API billing.

---

## The Pattern That Works

Every working service (workspace chat, assistant chat, spec chat, coding agents) uses this exact pattern:

```python
import shutil
import tempfile
from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
from registry import get_effective_sdk_env

system_cli = shutil.which("claude")
sdk_env = get_effective_sdk_env(force_subscription=True)

client = ClaudeSDKClient(
    options=ClaudeAgentOptions(
        model=model,
        cli_path=system_cli,
        system_prompt=system_prompt,
        env=sdk_env,
        # ... other options
    )
)

await client.__aenter__()
# ... use client ...
await client.__aexit__(None, None, None)
```

### Key Elements

| Element | What It Does | Required? |
|---------|-------------|-----------|
| `shutil.which("claude")` | Finds the system CLI binary | Yes |
| `get_effective_sdk_env(force_subscription=True)` | Clears API keys so SDK uses subscription OAuth | Yes |
| `ClaudeSDKClient` | Wraps CLI with proper auth handling | Yes |
| `env=sdk_env` | Passes subscription env to CLI subprocess | Yes |

---

## Use Case 1: Simple Prompt-In / Text-Out (No Tools)

For services that just need to send a prompt and get text back (e.g., YT Lab processing, any AI analysis pipeline):

```python
async def _call_via_sdk(self, system_prompt: str, user_message: str, model: str) -> str:
    from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
    from registry import get_effective_sdk_env

    system_cli = shutil.which("claude")
    if not system_cli:
        raise RuntimeError("Claude CLI not found on PATH")

    sdk_env = get_effective_sdk_env(force_subscription=True)
    scratch = tempfile.mkdtemp(prefix="my_service_")

    client = ClaudeSDKClient(
        options=ClaudeAgentOptions(
            model=model,
            cli_path=system_cli,
            system_prompt=system_prompt,
            env=sdk_env,
            max_turns=1,
            permission_mode="bypassPermissions",
            allowed_tools=[],
            cwd=scratch,
        )
    )

    try:
        await client.__aenter__()
        await client.query(user_message)

        full_text = ""
        async for msg in client.receive_response():
            if type(msg).__name__ == "AssistantMessage" and hasattr(msg, "content"):
                for block in msg.content:
                    if type(block).__name__ == "TextBlock" and hasattr(block, "text"):
                        full_text += block.text

        if not full_text.strip():
            raise RuntimeError("Claude SDK returned empty response")
        return full_text.strip()
    finally:
        try:
            await client.__aexit__(None, None, None)
        except Exception:
            pass
```

**When to use:** Any feature that sends a system prompt + user message and just needs the text response. No file access, no tools, no multi-turn conversation.

---

## Use Case 2: Interactive Chat Session (With Tools)

For services that need multi-turn conversation with tool access (e.g., workspace chat, assistant chat):

```python
from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
from registry import get_effective_sdk_env

system_cli = shutil.which("claude")
sdk_env = get_effective_sdk_env(force_subscription=True)

client = ClaudeSDKClient(
    options=ClaudeAgentOptions(
        model=model,
        cli_path=system_cli,
        system_prompt=system_prompt,
        env=sdk_env,
        max_turns=100,
        permission_mode="bypassPermissions",
        allowed_tools=["Read", "Grep", "Glob", ...],
        setting_sources=["project"],
        cwd=str(working_directory),
    )
)

await client.__aenter__()

# Send messages and stream responses
await client.query(user_message)
async for msg in client.receive_response():
    if type(msg).__name__ == "AssistantMessage" and hasattr(msg, "content"):
        for block in msg.content:
            if type(block).__name__ == "TextBlock":
                yield block.text

# When done
await client.__aexit__(None, None, None)
```

**When to use:** Chat panels, interactive assistants, anything that needs back-and-forth conversation or tool use.

---

## Use Case 3: Full Coding Agent (With MCP + Security)

For agents that need full file access, MCP servers, and security hooks — see `client.py:create_client()`. This is the most complete setup used by AutoForge coding/testing/initializer agents.

---

## What NOT To Do

### DO NOT use raw subprocess calls to `claude -p`

```python
# BAD - This fails subscription auth and falls back to paid API
cmd = [cli_path, "-p", "--model", model, "--system-prompt", prompt]
result = subprocess.run(cmd, input=message, env=env)
```

The `claude -p` (print mode) subprocess does not authenticate through subscription OAuth the same way the SDK does. Even with `force_subscription=True` env vars, the raw CLI can't find the OAuth credentials and returns a non-zero exit code, triggering fallback to your paid API key.

### DO NOT call the Anthropic Python SDK directly (unless as a fallback)

```python
# AVOID - This always uses API key billing
import anthropic
client = anthropic.Anthropic(api_key=...)
client.messages.create(...)
```

Direct Anthropic SDK calls always use API key authentication. Only use this as a last-resort fallback, and log prominently when it activates.

---

## Where `force_subscription` Lives

**`registry.py` → `get_effective_sdk_env(force_subscription=True)`**

When `force_subscription=True`:
- Sets `ANTHROPIC_API_KEY=""` (empty string overrides env)
- Sets `ANTHROPIC_AUTH_TOKEN=""` (empty string overrides env)
- This forces the CLI to use subscription OAuth from `~/.claude/.credentials.json`

When `force_subscription=False`:
- Passes through API keys from env / Settings UI
- Use this only for features that REQUIRE API billing (e.g., 1M context beta)

---

## Reference Implementations

| Service | File | Pattern |
|---------|------|---------|
| Coding agents | `client.py:create_client()` | Full agent with MCP + security hooks |
| Assistant chat | `server/services/assistant_chat_session.py` | Interactive chat with tools |
| Workspace chat | `server/services/workspace_chat_session.py` | Interactive chat with tools |
| Spec chat | `server/services/spec_chat_session.py` | Interactive chat |
| YT Processor | `server/services/yt_processor.py` | Simple prompt-in/text-out |
| YT Discovery | `server/services/yt_discovery.py` | Simple prompt-in/text-out |
