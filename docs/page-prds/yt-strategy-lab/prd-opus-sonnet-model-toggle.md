# PRD: Opus/Sonnet Model Toggle for PRD Extraction

## Problem

The YT Strategy Lab "From PRD" flow currently hardcodes Claude Sonnet 4.6 for extracting steps from PRDs. Since each step becomes a skill-level prompt, the quality of the extraction matters a lot. There's no way to compare Opus vs Sonnet output to see which produces better skill prompts.

## Goal

Add a toggle in the UI that lets the user choose between Opus 4.6 and Sonnet 4.6 (or run both) when extracting steps from a PRD. This enables A/B comparison of prompt quality between models.

## User Stories

1. **Single model run:** User opens "From PRD" modal, selects Opus or Sonnet from a toggle, pastes PRD, clicks submit. Steps are extracted using the chosen model.
2. **Dual model comparison:** User enables "Compare Both" mode. System runs extraction through both Opus and Sonnet (sequentially to avoid rate limits). Results appear side-by-side so the user can pick the better set of steps or cherry-pick individual steps from each.

## Technical Design

### Frontend Changes

**File:** `ui/src/components/tool-factory/PRDUploadModal.tsx`

- Add a model selector below the paste/upload tabs:
  - Radio buttons: `Sonnet 4.6` (default) | `Opus 4.6` | `Compare Both`
- Pass selected model to the API call
- When "Compare Both" is selected, show a split-pane comparison view after results return

**File:** `ui/src/pages/YTStrategyLabPage.tsx`

- `handlePRDExtractionComplete()` needs to handle dual results
- Add a comparison modal/view that shows Opus steps vs Sonnet steps side-by-side
- Allow user to select which set to use, or mix-and-match individual steps

### Backend Changes

**File:** `server/services/prd_ingestion.py`

- `extract_steps_from_prd()` already accepts a model via `YTProcessor(model=...)`. Change:
  - Add `model` parameter (default: `"claude-sonnet-4-6"`)
  - Pass it through to `_call_via_sdk()`
  - Keep timeout at 300s (already updated)

**File:** `server/routers/tool_factory.py`

- `generate-from-prd` endpoint: Add optional `model` field to request body
- Add new endpoint `POST /api/tool-factory/compare-prd` that runs both models sequentially and returns both result sets

### API Contract

**Existing endpoint (updated):**
```
POST /api/tool-factory/generate-from-prd
Body: { content, filename, user_context, model?: "claude-sonnet-4-6" | "claude-opus-4-6" }
Response: { prd_id, extraction, blueprint, tool_id }
```

**New endpoint:**
```
POST /api/tool-factory/compare-prd
Body: { content, filename, user_context }
Response: {
  prd_id: string,
  sonnet: { extraction, blueprint, tool_id, elapsed_seconds },
  opus: { extraction, blueprint, tool_id, elapsed_seconds }
}
```

### Rate Limit Considerations

- Opus uses more of the hourly quota per request (1M context)
- "Compare Both" runs two sequential calls. If first call rate-limits, wait and retry before starting second
- Show estimated wait time in UI if rate-limited
- Consider running Sonnet first (faster, cheaper) so user sees partial results quickly

### Subscription Auth

Both models use subscription auth (`force_subscription=True`). No API key changes needed. The existing `get_effective_sdk_env()` in `registry.py` handles this.

## UI Mockup (Text)

```
┌─────────────────────────────────────────────┐
│  From PRD                              [X]  │
│                                             │
│  [Upload File] [Paste Content]              │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │ (paste area)                        │    │
│  │                                     │    │
│  └─────────────────────────────────────┘    │
│  14,854 characters                          │
│                                             │
│  Model: ○ Sonnet 4.6  ○ Opus 4.6           │
│         ○ Compare Both                      │
│                                             │
│  [Extract Steps]  [Cancel]                  │
└─────────────────────────────────────────────┘
```

## Comparison View (after "Compare Both")

```
┌──────────────────────┬──────────────────────┐
│  Sonnet 4.6 (42s)    │  Opus 4.6 (128s)     │
├──────────────────────┼──────────────────────┤
│  Step 1: ...         │  Step 1: ...         │
│  ☐ Use this          │  ☑ Use this          │
│                      │                      │
│  Step 2: ...         │  Step 2: ...         │
│  ☑ Use this          │  ☐ Use this          │
│  ...                 │  ...                 │
├──────────────────────┴──────────────────────┤
│  [Use All Sonnet] [Use All Opus] [Use Mix]  │
└─────────────────────────────────────────────┘
```

## Implementation Order

1. Backend: Add `model` parameter to `extract_steps_from_prd()` (5 min)
2. Backend: Add `model` field to `generate-from-prd` endpoint (5 min)
3. Frontend: Add model radio buttons to PRDUploadModal (15 min)
4. Backend: Add `/compare-prd` endpoint (20 min)
5. Frontend: Build comparison view component (30 min)
6. Frontend: Wire up "Compare Both" flow (15 min)

## Out of Scope (for now)

- Auto-selecting the "better" result via another AI call
- Saving comparison history for later review
- Cost tracking per model (subscription, so no direct cost difference)
- Parallel execution of both models (sequential avoids rate limit issues)
