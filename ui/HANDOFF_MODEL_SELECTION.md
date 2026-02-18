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

## Task 4: Token Meter with 200K Pricing Cliff Indicator

### Why This Matters

When using the 1M context API panels (PRD Builder and Coder), there's a pricing
cliff at 200K input tokens. Once input exceeds 200K, ALL tokens (even the first
200K) are billed at 2x input / 1.5x output. This means the user has a strong
incentive to keep conversations under 200K when possible — especially on the
PRD Builder panel where they can front-load research on the free subscription panel.

### What Needs to Happen

Add a 200K pricing threshold marker to the existing `EnhancedContextBudgetBar`
on BOTH 1M API panels (PRD Builder AND Coder). The Coder panel meter is
especially valuable — it teaches the user how much token budget coding tasks
actually consume (file reads, code writes, test runs, iterations). Over time
this builds intuition for estimating costs before starting a feature.

### File: `ui/src/components/workspace/EnhancedContextBudgetBar.tsx`

#### 1. Add pricing threshold marker to the progress bar

The component already renders a thick `h-4` progress bar with token segments.
Add a vertical marker line at the 200K position (on 1M context panels):

```tsx
{/* 200K pricing cliff marker — only on 1M context panels */}
{totalBudget === 1_000_000 && (
  <div
    className="absolute top-0 h-full w-0.5 bg-amber-500 z-10"
    style={{ left: '20%' }}  // 200K / 1M = 20%
    title="200K pricing threshold — tokens above this cost 2x input / 1.5x output"
  >
    {/* Label above the marker */}
    <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 text-[9px] font-bold text-amber-500 whitespace-nowrap">
      200K
    </span>
  </div>
)}
```

Insert this inside the progress bar div (line ~131, after the segments map
and before the streaming shimmer).

#### 2. Add pricing tier label to the stats row

After the message count on the right side of the stats row, show whether
the conversation is in standard or premium pricing:

```tsx
{/* Pricing tier indicator for 1M panels */}
{totalBudget === 1_000_000 && (
  <span className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
    usedTokens > 200_000
      ? 'bg-amber-500/20 text-amber-500'
      : 'bg-emerald-500/20 text-emerald-500'
  }`}>
    {usedTokens > 200_000 ? '2x RATE' : 'STD RATE'}
  </span>
)}
```

#### 3. Color shift when crossing threshold

Update the `usageColor()` function to account for the pricing cliff.
When on a 1M panel, crossing 200K should trigger amber/warning colors
even though 200K out of 1M is only 20%:

```tsx
function usageColor(percent: number, totalBudget: number, usedTokens: number): string {
  // On 1M panels, warn early at the 200K pricing cliff
  if (totalBudget === 1_000_000 && usedTokens > 200_000) {
    if (percent > 90) return 'text-destructive'
    return 'text-amber-400'  // Premium pricing zone
  }
  // Standard thresholds
  if (percent > 90) return 'text-destructive'
  if (percent > 75) return 'text-orange-400'
  if (percent > 50) return 'text-yellow-400'
  return 'text-emerald-400'
}
```

#### 4. Add estimated cost display (optional but valuable)

Show the approximate cost of the current conversation based on token count
and pricing tier. This helps the user make informed decisions about whether
to keep going or start fresh.

```tsx
// Calculate estimated cost
function estimateCost(inputTokens: number, model: 'opus' | 'sonnet'): string {
  const isExtended = inputTokens > 200_000
  const rates = {
    opus:   { standard: 5, extended: 10 },
    sonnet: { standard: 3, extended: 6 },
  }
  const rate = isExtended ? rates[model].extended : rates[model].standard
  const cost = (inputTokens / 1_000_000) * rate
  return cost < 0.01 ? '<$0.01' : `~$${cost.toFixed(2)}`
}
```

To use this, `EnhancedContextBudgetBar` would need a new optional prop:
```tsx
/** Model name for cost estimation on API panels */
preferredModel?: 'opus' | 'sonnet'
```

This gets passed from WorkspaceChat (which knows its panelLabel) down to
the budget bar. The cost display only shows on 1M panels where it matters.

### Visual Result

For a 1M panel under 200K:
```
┌──────────────────────────────────────────────┐
│  8.2%    82.3K / 1.0M    12 msgs   STD RATE │
│ [████░░░░|░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] │
│         ↑                                    │
│        200K                                  │
│        marker                                │
└──────────────────────────────────────────────┘
```

For a 1M panel OVER 200K:
```
┌──────────────────────────────────────────────┐
│  28.5%   285K / 1.0M    34 msgs    2x RATE  │
│ [█████████████|░░░░░░░░░░░░░░░░░░░░░░░░░░░░] │
│              ↑ (amber marker, bar turns amber)│
│             200K                              │
└──────────────────────────────────────────────┘
```

### Research panel (200K subscription) — no changes needed
The research panel uses `totalBudget === 200_000` so the 200K marker
won't render. The existing usage colors are sufficient since there's no
pricing cliff on the subscription panel.

### How tool use (file reads, web research) affects tokens

Important context for the user: when the agent reads files (via Read, Grep,
Glob tools) or does web research, those tool results become part of the
conversation history. Every subsequent message re-sends the FULL history
including all tool results. So a single file read of 5K tokens becomes 5K
tokens added to EVERY future message in that conversation.

This is why the meter is critical — file reads compound. If the agent reads
10 files averaging 5K each, that's 50K tokens added permanently to the
conversation. Combined with the back-and-forth, it can push past 200K fast.

Strategy to stay under 200K on PRD Builder:
1. Do file exploration on the Research (subscription) panel — free
2. Have the Research agent include specific code snippets and file locations
   in the passoff document (compact, targeted)
3. The PRD Builder gets a clean, pre-digested plan instead of raw file dumps
4. The PRD Builder only reads files when it MUST verify something specific

## Note: Existing Project Organization

The workspace already has category-based project organization. No new work
needed — just documenting for context:

- **Categories** — one per software project. Conversations group under them
  in the sidebar. Collapsible, color-coded, reorderable.
  - DB: `WorkspaceCategory` table (name, color, sort_order)
  - UI: `CategoryManager.tsx` for CRUD
- **Tags** — free-form per conversation (stored comma-separated)
- **Pinning** — pin key conversations to sidebar top
- **Search** — hybrid client+server search across message content
- **Persistence** — SQLite at `~/.autoforge/workspace.db`
- **Per-conversation working directory** — each conversation remembers
  which repo it was working with

The user's mental model: each software = a category, each feature build =
a conversation within that category. All persistent, searchable, reviewable.

