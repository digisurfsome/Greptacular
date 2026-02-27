# Build Agent 4 — Phase 3: Batch Import + Phase 7: Model Routing & Roles

## What You're Building

You are building **two features** inside the **YT Strategy Lab** system in the AutoForge application (Greptacular codebase). YT Strategy Lab is a platform for extracting actionable strategies from YouTube videos and executing them with AI agents.

**Feature A (Phase 3):** Batch YouTube Import — paste multiple URLs, preview them all, add context per video, process all into projects on autopilot.

**Feature B (Phase 7):** Model Routing & Roles — per-step model selection (Opus/Sonnet/Haiku/Auto) and role attachments (system prompts from the Role Library).

**Prerequisites:** Phase 2 (Auto-Processor) must be done before you start Phase 3. Phase 7's UI is standalone but its execution integration would use Phase 4. Build the UI portion fully; wire execution later.

---

## Step 1: Read These Documents (In This Order)

**Do not write any code until you have read all documents and confirmed your understanding.**

1. **Context Primer** — Read this FIRST:
   ```
   docs/yt-strategies/CONTEXT_PRIMER.md
   ```

2. **PRD for Batch Import** (Feature A):
   ```
   docs/yt-strategies/prds/01-batch-youtube-import.md
   ```

3. **PRD for Model Routing & Roles** (Feature B):
   ```
   docs/yt-strategies/prds/06-model-routing-and-roles.md
   ```

4. **Build Standards**:
   ```
   .claude/build-prompts/App Builder Prompt Template (Platform-Agnostic).txt
   ```

---

## Step 2: Prove Understanding

Before writing code, briefly state:
1. What Batch Import does and how it uses the Phase 2 processing pipeline
2. What Model Routing does and how Auto mode selects models
3. The complete list of files you will create or modify
4. How these two features are independent of each other

---

## Step 3A: Build Batch Import (Phase 3)

### Backend
- **`server/routers/yt_batch.py`** — New router:
  - `POST /api/yt-lab/batch-ingest` — Accept array of URLs with per-video context
  - `POST /api/yt-lab/batch-process` — Queue all videos for AI processing
  - `GET /api/yt-lab/batch-status/{batch_id}` — Return progress of batch
  - Uses existing `/api/yt-lab/ingest` (Phase 1) and `/api/yt-lab/process` (Phase 2) internally
  - Background task queue using asyncio
- Register in `server/routers/__init__.py` and `server/main.py`

### Frontend
- **`ui/src/components/yt-lab/BatchImportView.tsx`** — New component:
  - Multi-URL textarea input (one per line, comma-separated, or mixed)
  - URL parser that handles youtube.com/watch?v=, youtu.be/, youtube.com/shorts/
  - "Fetch Previews" button → shows card per video with:
    - Thumbnail, title, channel, duration
    - Context/instructions textarea per video
    - Niche/tag inputs
    - Screenshot capture toggle
    - Priority ordering
  - "Process All" button → queues batch processing
  - Progress tracking (overall bar + per-video status: Queued → Processing → Complete)
  - Model selection dropdown (Sonnet default for bulk)
- Add batch API functions to `ui/src/lib/api.ts`
- Add batch types to `ui/src/lib/types.ts`
- Integrate BatchImportView into `YTStrategyLabPage.tsx` (new view or button in list view)

---

## Step 3B: Build Model Routing & Roles (Phase 7)

### Backend
- **`server/services/model_router.py`** — Auto-routing logic:
  - `select_model(step)` function that picks Opus/Sonnet/Haiku based on step keywords
  - Opus: strategy, create, write, analyze, design, brand
  - Haiku: list, find, search, gather, collect, navigate
  - Sonnet: everything else (default)

### Frontend — Step Editor Enhancements
- Add **Model dropdown** to each step in the strategy builder:
  - Options: Opus 4.6, Sonnet 4.6, Haiku 4.5, Auto
  - "Auto" shows the system's recommendation as a hint
- Add **Role dropdown** to each step:
  - Default roles: Researcher, Marketer, Designer, Analyst, Outreach Specialist, Full-Stack Operator
  - "Custom (from Role Library)..." option that links to `/#/roles`
  - "None (no role)" option
- Store model + role selections in `YTStrategyStep` (update types)
- Add default role system prompts as constants

### Key Rules (from Context Primer)
- Subscription-based model access — NO raw API key config in UI
- Follow existing `MODEL_OPTIONS` pattern in YTStrategyLabPage.tsx
- Roles come from the existing Role Library at `/#/roles`
- Prefix all types with `YT`

---

## Step 4: Quick Verification

After building, run:
```bash
cd ui && npm run lint && npm run build
cd .. && ruff check server/
```

Fix any errors. Commit your work.

---

## Step 5: Follow Post-Build Verification Protocol

After the build compiles clean, execute the full verification protocol:
```
.claude/templates/e2e_verification_prompt.template.md
```
Read it. Follow all 8 phases. Fix any issues found.

---

## Important

- **Phase 3 depends on Phase 2** — the processing pipeline must exist. Check that `server/routers/yt_processing.py` exists from Agent 1's work. If it doesn't exist yet, build Phase 7 first and stub Phase 3's processing calls.
- Stay under 50% context window if possible. Two features in one session is tight — be efficient.
- Commit with clear messages. Push to your branch when done.
