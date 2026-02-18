# Handoff: Per-Panel Model Selection + Passoff UX Improvements

## Context

The workspace split-view has been rebuilt into a three-panel accordion system:
- **Panel 1: RESEARCH (200K)** — subscription billing, for exploration
- **Panel 2: PRD BUILDER (Opus 4.6)** — API billing, 1M context, creates PRDs
- **Panel 3: CODER (Sonnet 4.6)** — API billing, 1M context, executes PRDs

The panels currently label themselves with model names but the backend doesn't
route to different models per panel. All panels use whatever model is globally
configured. This handoff describes the work needed to make per-panel model
selection functional.

## Files to Know

### UI (React/TypeScript)
- `ui/src/pages/WorkspacePage.tsx` — Three-panel layout, accordion collapse,
  passoff overlay, auto-forward wiring
- `ui/src/components/workspace/WorkspaceChat.tsx` — Chat panel component.
  Props: `fixedContextMode`, `panelLabel`, `injectMessage`, `onResponseComplete`
- `ui/src/components/workspace/PassoffEditor.tsx` — Passoff staging area
- `ui/src/components/ChatMessage.tsx` — Has `onCopyToPassoff` button
- `ui/src/hooks/useWorkspaceChat.ts` — WebSocket hook, sends `start` message

### Backend (Python/FastAPI)
- `server/routers/workspace.py` — WebSocket endpoint `/api/workspace/ws`,
  handles `start` message with `context_mode` and `cost_settings`
- `server/services/workspace_chat_session.py` — Creates `ClaudeSDKClient`,
  controls billing via `get_effective_sdk_env(force_subscription)`.
  Key lines ~280-294: context_mode determines API key vs subscription
- `client.py` — `ClaudeSDKClient` configuration, accepts model params
- `env_constants.py` — `API_ENV_VARS` including model env vars

## Task 1: Per-Panel Model Selection (Backend + UI)

### What Needs to Happen

Each panel needs to specify which model to use (Opus 4.6 vs Sonnet 4.6).
The model preference must flow from UI → WebSocket → backend session → SDK client.

### Backend Changes

1. **`server/routers/workspace.py`** — In `workspace_chat_websocket()`, extract
   a new `model` field from the `start` message:
   ```python
   model = message.get("model")  # e.g. "opus", "sonnet"
   ```
   Pass it to `create_session()`.

2. **`server/services/workspace_chat_session.py`** — In `WorkspaceChatSession`:
   - Accept `model` parameter in constructor
   - In `start()`, resolve model to actual model ID:
     ```python
     MODEL_MAP = {
         "opus": os.environ.get("ANTHROPIC_DEFAULT_OPUS_MODEL", "claude-opus-4-6"),
         "sonnet": os.environ.get("ANTHROPIC_DEFAULT_SONNET_MODEL", "claude-sonnet-4-5-20250929"),
     }
     resolved_model = MODEL_MAP.get(self.model, MODEL_MAP["opus"])
     ```
   - Pass `resolved_model` to `ClaudeSDKClient` creation.
   - Check `client.py` for how model is currently set — it likely reads from
     env vars. You may need to add a `model` parameter to `ClaudeSDKClient.__init__`.

3. **`client.py`** — Add optional `model` parameter to `ClaudeSDKClient` that
   overrides the env var default when provided.

### UI Changes

1. **`ui/src/hooks/useWorkspaceChat.ts`** — Update the `start()` function to
   accept and send a `model` field in the WebSocket `start` message:
   ```typescript
   ws.send(JSON.stringify({
     type: 'start',
     conversation_id: conversationId,
     working_directory: workingDirectory,
     context_mode: contextMode,
     cost_settings: costSettings,
     model: model,  // NEW: "opus" | "sonnet"
   }))
   ```

2. **`ui/src/components/workspace/WorkspaceChat.tsx`** — Add `preferredModel`
   prop (`'opus' | 'sonnet'`), pass it through to `start()`.

3. **`ui/src/pages/WorkspacePage.tsx`** — Pass `preferredModel="opus"` to
   PRD Builder panel and `preferredModel="sonnet"` to Coder panel.
   Research panel doesn't need it (uses subscription default).

### Testing

- Start a split-view session
- PRD Builder panel should use Opus model (check server logs)
- Coder panel should use Sonnet model (check server logs)
- Research panel should use subscription default

## Task 2: Passoff Overlay UX — Move Out of Way When Typing

### Current Behavior
The passoff editor overlays on top of the PRD Builder panel as a full-screen
overlay (`absolute inset-0 z-20`). This blocks the chat input underneath.

### Desired Behavior
When the user starts typing in the PRD panel's chat input (the textarea at the
bottom), the passoff overlay should automatically slide out of the way. Options:

**Option A (Recommended): Slide to adjacent panel**
- When user focuses the PRD panel's input textarea, the passoff overlay
  transitions (CSS animation) to overlay the Research or Coder panel instead
- When user blurs the input, it slides back
- Implementation: lift passoff overlay state to WorkspacePage, detect focus
  on PRD panel's input, change which panel the overlay renders over

**Option B: Shrink to top half**
- When input is focused, passoff overlay shrinks to top 50% of the panel
- Chat input and messages are visible in bottom 50%
- Implementation: conditional CSS classes based on focus state

**Option C: Tab between passoff and chat**
- Instead of overlay, add tabs at top of PRD panel: "Chat" | "Passoff"
- User switches between views within the same panel
- Simplest implementation but loses the overlay feel

### Implementation Notes for Option A
- Add `onInputFocus` and `onInputBlur` callbacks to WorkspaceChat
- WorkspacePage tracks which panel's input is focused
- Passoff overlay div moves between panels based on focus state
- Use CSS `transition` for smooth sliding: `transition-all duration-300`

## Task 3: Flexible Accordion Combinations

### Current State
Each panel independently collapses to a thin vertical bar. All combinations work.

### Enhancement Ideas
- Add keyboard shortcuts for collapsing panels (e.g. `1`, `2`, `3` to toggle)
- Add preset layouts: "Research Focus" (2+3 collapsed), "Code Focus" (1+2 collapsed)
- Remember collapse state in localStorage

## Pricing Reference (for cost display in UI)

### Standard Pricing (≤200K input tokens)
| Model | Input | Output |
|-------|-------|--------|
| Opus 4.6 | $5/MTok | $25/MTok |
| Sonnet 4.6 | $3/MTok | $15/MTok |

### Extended Context Pricing (>200K input tokens)
Once input exceeds 200K, ALL tokens are billed at premium rate:
| Model | Input | Output |
|-------|-------|--------|
| Opus 4.6 | $10/MTok | $37.50/MTok |
| Sonnet 4.6 | $6/MTok | $22.50/MTok |

Sonnet is 40% cheaper than Opus at both tiers.

### Cache Pricing
| Model | 5-min cache write | 1-hour cache write |
|-------|------|------|
| Opus 4.6 | $6.25/MTok | $10/MTok |
| Sonnet 4.6 | $3.75/MTok | $6/MTok |

Cache reads are always free for first 5 minutes.
