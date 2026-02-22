# AutoForge Throttling Levers

## What This Is

Documentation of the CostControls lever system — a 5-parameter throttling panel originally built for the workspace chat dashboard. This system is **not currently connected to AutoForge** but could be wired up to control AutoForge agent sessions in the future. The file and backend validation code were intentionally preserved for this purpose.

## Current Status

- **Workspace dashboard:** REMOVED (as of Feb 2026). The `<CostControls>` component was disconnected from `WorkspaceChat.tsx` because the "effort" lever was dead code and testing showed no meaningful cost impact.
- **AutoForge:** NOT connected. AutoForge agent sessions (`client.py`, `autonomous_agent_demo.py`) do not use CostSettings.
- **Code:** PRESERVED. Both the frontend component and backend validation remain in the codebase, ready to be wired up.

## Why It Was Removed From Workspace

1. **The "effort" lever was dead code.** The backend received the effort value, logged it, then threw it away. A comment in `workspace_chat_session.py:537-538` explicitly stated: *"Note: effort is not a ClaudeAgentOptions param — it only applies to direct API calls, not the Agent SDK."*

2. **Testing confirmed no effect.** Changing effort from Low to Medium to High produced identical or near-identical costs ($0.01 variance) for the same "what model are you" query across both Opus 4.6 and Sonnet 4.6.

3. **The effort mapping was homebrew, not Anthropic's API.** The lever mapped effort to a *percentage of max_tokens* for "thinking" (30%/70%/150%), which is NOT how Anthropic's actual effort parameter works. Anthropic's real effort parameter (`output_config.effort` in the Messages API, or `CLAUDE_CODE_EFFORT_LEVEL` env var for Claude Code CLI) controls adaptive thinking depth at the model level.

## File Locations

### Frontend

| File | Purpose |
|---|---|
| `ui/src/components/workspace/CostControls.tsx` | The full lever panel component (379 lines). Includes presets, sliders, cost estimator. **Preserved but unused.** |
| `ui/src/components/workspace/WorkspaceChat.tsx` | Previously imported and rendered `<CostControls>`. Import and JSX removed. |

### Backend

| File | Lines | Purpose |
|---|---|---|
| `server/services/workspace_chat_session.py` | 85-130 | `DEFAULT_COST_SETTINGS` dict, `VALID_EFFORT_LEVELS` tuple, `validate_cost_settings()` function. **All preserved.** |
| `server/services/workspace_chat_session.py` | 162-190 | Constructor accepts `cost_settings` param, validates and stores it. |
| `server/services/workspace_chat_session.py` | 519-542 | Where `ClaudeSDKClient` is created. `max_turns` from cost_settings IS applied. `effort` is NOT applied (dead code). |
| `server/services/workspace_chat_session.py` | 692-696 | `history_budget` from cost_settings IS applied to message loading. |
| `server/services/workspace_chat_session.py` | 728-732 | `library_cap` from cost_settings IS applied to library file injection. |
| `server/routers/workspace.py` | ~1138 | WebSocket handler receives `cost_settings` from frontend and passes to session. |

### WebSocket Hook

| File | Purpose |
|---|---|
| `ui/src/hooks/useWorkspaceChat.ts` | `start()` function signature still accepts `costSettings` parameter (5th arg). Currently passed as `undefined` from WorkspaceChat. |

## The 5 Parameters

| Parameter | Range | Default | Actually Wired? | What It Controls |
|---|---|---|---|---|
| `effort` | low / medium / high | low | **NO** — dead code | Was supposed to control thinking depth. Never sent to API. |
| `max_tokens` | 4,096–65,536 | 16,384 | Partially | Set but Agent SDK manages its own output limits. |
| `max_turns` | 10–100 | 50 | **YES** | Controls agent tool-call rounds per message. |
| `history_budget` | 25,000–400,000 | 100,000 | **YES** | Token budget for conversation history on resume. Above 200K triggers premium pricing. |
| `library_cap` | 10,000–200,000 | 50,000 | **YES** | Max tokens injected from workspace library files per message. |

## The 4 Presets

| Preset | Effort | Max Tokens | Max Turns | History Budget | Library Cap |
|---|---|---|---|---|---|
| Economy | low | 8,192 | 25 | 50,000 | 25,000 |
| Balanced | low | 16,384 | 50 | 100,000 | 50,000 |
| Performance | medium | 32,768 | 75 | 200,000 | 100,000 |
| Max Quality | high | 65,536 | 100 | 400,000 | 200,000 |

## How To Wire Up For AutoForge

If you want to connect these levers to AutoForge agent sessions:

1. **Add cost_settings to `client.py`'s `get_client()` function.** Currently `get_client()` at `client.py:624` creates `ClaudeAgentOptions` with hardcoded `max_turns`. Replace with configurable values from cost_settings.

2. **Pass settings from the UI.** The AutoForge agent is started via `server/routers/agent.py`. Add a `cost_settings` field to the start request and forward it to the agent subprocess.

3. **The 3 working levers matter most for AutoForge:**
   - `max_turns` — controls how many tool calls per feature implementation (lower = cheaper, less thorough)
   - `history_budget` — controls context loading (lower = cheaper, less context)
   - `library_cap` — not relevant for AutoForge (workspace-only concept)

4. **Don't use the "effort" lever as-is.** It's broken (never sent to API). Use Anthropic's real `CLAUDE_CODE_EFFORT_LEVEL` env var instead. See the new effort control being built for the workspace as a reference.

## Anthropic's Real Effort Control (Reference)

The actual API parameter for controlling thinking depth:

**Messages API:**
```python
response = client.messages.create(
    model="claude-opus-4-6",
    output_config={"effort": "medium"},  # low | medium | high | max
    thinking={"type": "adaptive"},
    ...
)
```

**Claude Code CLI / Agent SDK:**
```python
# Via environment variable
sdk_env["CLAUDE_CODE_EFFORT_LEVEL"] = "medium"  # low | medium | high

# Via settings file
{"effortLevel": "medium"}
```

**Supported levels:**

| Level | Opus 4.6 | Sonnet 4.6 | Behavior |
|---|---|---|---|
| low | yes | yes | Minimal thinking. Cheapest, fastest. |
| medium | yes | yes | Balanced. Recommended default for Sonnet 4.6. |
| high (default) | yes | yes | Deep thinking. Same as omitting the parameter. |
| max | **yes** | **NO — error** | Maximum capability. Opus 4.6 only via Messages API. Not available in Claude Code CLI. |

## Key Takeaway

The old lever system's `effort` parameter was an internal calculation (% of max_tokens), not Anthropic's actual thinking effort control. The other 3 parameters (`max_turns`, `history_budget`, `library_cap`) DO work and could meaningfully throttle AutoForge agent costs. If wiring up for AutoForge, use the working parameters and replace the broken effort lever with `CLAUDE_CODE_EFFORT_LEVEL`.
