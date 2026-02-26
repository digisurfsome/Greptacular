# PRD: Multi-Provider Chat Integration into DunkStack

**Status:** Ready for Implementation
**Priority:** High
**Branch:** `claude/setup-app-builder-base-P5LJm`

---

## 1. Summary

Wire the existing multi-provider chat system (Claude / Codex / Gemini) into the DunkStack page so users get the same side-by-side multi-provider pane experience that already works in the DashboardPage — but enriched with DunkStack's context gauge, safety system, bridge saves, and file-based session control.

## 2. Background

### What Already Exists

**DashboardPage** (`/#/dashboard` — lives on `origin/main`, not yet on this branch):
- Multi-pane layout: Single / Dual / Triple side-by-side
- Per-pane provider selector (Claude / Codex / Gemini pill buttons)
- Each pane wraps `WorkspaceChat` which handles all WebSocket, message display, token tracking
- Conversation sidebar with streaming indicators
- Provider definitions in `registry.py` (`WORKSPACE_PROVIDERS` dict)
- Backend routing: `workspace_chat_session.py` routes to Claude SDK, CodexBridge, or GeminiBridge
- Database: `workspace_conversations` table has `provider` column

**DunkStack** (`/#/dunkstack` — on current branch):
- File-based comms: reads/writes `.agent/comms/to_human.md` and `from_human.md`
- Context gauge: real-time token tracking with color-coded safety zones
- 3-tier safety system: Warning (45%) → Handoff (47.5%) → Hard Stop (50%)
- Session control modes: Idle / Continue / Autopilot
- Bridge save for session continuity
- Model preset selector (Opus 200K, Opus 1M, Sonnet 1M)
- Project sidebar
- Backend: `server/routers/dunkstack.py` with REST + WebSocket endpoints

### Gap

DunkStack has all the context management intelligence but only a simple file-based chat. DashboardPage has the multi-provider panes but no context management. We need to merge these capabilities.

## 3. Requirements

### 3.1 Pull Main into Branch (Prerequisite)

Before any code changes, merge `origin/main` into the current branch to bring in:
- `ui/src/pages/DashboardPage.tsx`
- `server/services/codex_bridge.py` (already present)
- `server/services/gemini_bridge.py` (already present)
- Updated `ui/src/main.tsx` with `/#/dashboard` route
- All provider plumbing in `workspace_chat_session.py`, `workspace_database.py`

### 3.2 Add Multi-Provider Panes to DunkStack

Replace the single `DunkStackCommsChat` center panel with the DashboardPage's multi-pane system:

**Layout:**
```
+------------------------------------------------------------------+
| Breadcrumb bar: ← AutoForge / DunkStack | Model pills | Controls |
+------------------------------------------------------------------+
| Context Gauge (DunkStack's token bar with safety coloring)       |
+----------+---------------------------+---------------------------+
| Projects | Pane 1                    | Pane 2 (or Safety Panel) |
| sidebar  | [Claude|Codex|Gemini]     | [Claude|Codex|Gemini]    |
|          | ┌─────────────────────┐   | ┌─────────────────────┐  |
|          | │   WorkspaceChat     │   | │   WorkspaceChat     │  |
|          | │   (full features)   │   | │   (full features)   │  |
|          | └─────────────────────┘   | └─────────────────────┘  |
+----------+---------------------------+---------------------------+
```

**What to reuse from DashboardPage:**
- `PaneState` interface and `createPane()` helper
- `ProviderSelector` pill-button component
- `CollapsedPaneBar` for collapsed panes
- `WorkspaceChat` component integration with `provider` prop
- Layout mode switching (Single / Dual / Triple)
- localStorage persistence for pane config
- Conversation sidebar integration

**What to keep from DunkStack:**
- `DunkStackContextGauge` — stays in its current position above the panes
- `DunkStackSafetyPanel` — stays as a toggleable right panel
- Model preset selector in breadcrumb bar
- Project sidebar (left)
- Guide overlay
- Bridge save functionality
- `useDunkStack` hook for context gauge, safety, and comms (runs in parallel with WorkspaceChat)

### 3.3 Update Model Lists

Update the provider model definitions in `registry.py` to current models:

```python
WORKSPACE_PROVIDERS = {
    "claude": {
        "models": [
            {"id": "opus", "name": "Claude Opus 4.6"},
            {"id": "sonnet", "name": "Claude Sonnet 4.6"},
            {"id": "haiku", "name": "Claude Haiku 4.5"},
        ],
        "default_model": "opus",
    },
    "codex": {
        "models": [
            {"id": "o3", "name": "o3"},
            {"id": "o4-mini", "name": "o4-mini"},
        ],
        "default_model": "o3",
    },
    "gemini": {
        "models": [
            {"id": "pro", "name": "Gemini 2.5 Pro"},
            {"id": "flash", "name": "Gemini 2.5 Flash"},
        ],
        "default_model": "pro",
    },
}
```

### 3.4 Per-Pane Model Dropdowns

Each pane should show a model dropdown next to the provider selector:
- Dropdown is populated from the selected provider's model list
- Default is the provider's `default_model`
- Selection is passed to `WorkspaceChat` as `pendingModel`
- Persisted per-pane to localStorage

### 3.5 Context Gauge Integration

The DunkStack context gauge should aggregate token usage across all active panes:
- Each `WorkspaceChat` pane reports tokens via `onStreamingChange` or a new callback
- `useDunkStack` hook tracks cumulative tokens across all panes
- Safety thresholds apply to the combined total
- When HANDOFF threshold is hit, all panes get a visual warning

## 4. Implementation Steps

### Step 1: Merge main
```bash
git fetch origin main
git merge origin/main --no-edit
```
Resolve any conflicts (likely in `ui/src/main.tsx` routing).

### Step 2: Rebuild and verify
```bash
cd ui && npm run build
```
Verify both `/#/dashboard` and `/#/dunkstack` routes load.

### Step 3: Create DunkStack pane components

Extract from DashboardPage into shared components or copy into DunkStackPage:
- `PaneState` type, `createPane` helper
- `ProviderSelector` component
- `CollapsedPaneBar` component
- Layout mode state management

### Step 4: Refactor DunkStackPage center panel

Replace `DunkStackCommsChat` with the multi-pane system:
1. Add `panes` state array (same as DashboardPage)
2. Add `layoutMode` state with Single/Dual/Triple buttons in breadcrumb bar
3. Render `WorkspaceChat` in each pane with `provider` prop
4. Keep `DunkStackCommsChat` as an optional "File Comms" tab within each pane (if desired) or as a toggle

### Step 5: Add per-pane model selector

Add a small dropdown next to each `ProviderSelector`:
```tsx
<ModelSelector
  provider={pane.provider}
  currentModel={pane.model}
  onChange={(model) => updatePane(pane.id, { model })}
/>
```

### Step 6: Wire context gauge to pane tokens

Add a token aggregation callback:
- Each `WorkspaceChat` reports token snapshots
- `useDunkStack` records them via `POST /api/dunkstack/tokens/record`
- Gauge reflects combined usage across all panes

### Step 7: Verify and build

```bash
cd ui && npm run lint && npm run build
```

## 5. Files to Modify

| File | Change |
|------|--------|
| `ui/src/pages/DunkStackPage.tsx` | Add multi-pane layout with WorkspaceChat, layout mode controls, per-pane provider/model selectors |
| `ui/src/hooks/useDunkStack.ts` | Add token aggregation across panes |
| `ui/src/main.tsx` | Verify `/#/dashboard` route exists after merge |
| `registry.py` | Update model lists to current versions |
| `ui/src/lib/types.ts` | Verify `WorkspaceProvider` type is present |

## 6. Files NOT to Modify

- `server/routers/dunkstack.py` — backend is already complete
- `server/services/codex_bridge.py` — already working
- `server/services/gemini_bridge.py` — already working
- `server/services/workspace_chat_session.py` — routing already handles all providers
- `ui/src/components/dunkstack/DunkStackContextGauge.tsx` — keep as-is
- `ui/src/components/dunkstack/DunkStackSafetyPanel.tsx` — keep as-is

## 7. Key Insight: Why This Is Straightforward

The DashboardPage already proved the pattern works:
1. `WorkspaceChat` accepts a `provider` prop and routes everything correctly
2. The WebSocket `start` message includes `provider` field
3. Backend `workspace_chat_session.py` routes to the correct bridge
4. All three bridges (Claude SDK, CodexBridge, GeminiBridge) are tested and working

DunkStack just needs to adopt the same pane system. The context gauge and safety system sit *above* the panes and don't need to know about provider details — they just track token totals.

**In short: copy the DashboardPage's pane rendering logic into DunkStackPage, keep all the DunkStack-specific features (gauge, safety, bridge, comms), and you're done.**

## 8. Success Criteria

- [ ] `/#/dunkstack` shows multi-provider panes with Claude/Codex/Gemini selector
- [ ] Layout mode switching (1/2/3 panes) works
- [ ] Context gauge reflects token usage from active chat panes
- [ ] Safety system triggers warnings based on combined token usage
- [ ] Bridge save still works
- [ ] Model dropdown shows correct models per provider
- [ ] `npm run build` succeeds with no TypeScript errors
- [ ] `npm run lint` passes
