# Build Agent 1 — Phase 2: YouTube Auto-Processor

## What You're Building

You are building **one feature** inside the **YT Strategy Lab** system in the AutoForge application (Greptacular codebase). YT Strategy Lab is a platform for extracting actionable strategies from YouTube videos and executing them with AI agents.

**Your feature:** The AI processing pipeline that takes raw YouTube transcript + metadata and automatically generates a fully populated strategy project with steps, prompts, and notes.

Phase 1 (core UI + YouTube ingestion) is already done. You are building Phase 2.

---

## Step 1: Read These Documents (In This Order)

**Do not write any code until you have read all three documents and confirmed your understanding.**

1. **Context Primer** — Read this FIRST. It explains the entire system, vocabulary, architecture, and patterns:
   ```
   docs/yt-strategies/CONTEXT_PRIMER.md
   ```

2. **Your PRD** — The specific feature you're building:
   ```
   docs/yt-strategies/prds/07-youtube-auto-processor.md
   ```

3. **Build Standards** — Code quality standards to follow:
   ```
   .claude/build-prompts/App Builder Prompt Template (Platform-Agnostic).txt
   ```

---

## Step 2: Prove Understanding

Before writing code, briefly state:
1. What the Auto-Processor does (one paragraph)
2. What files you will create or modify
3. What existing patterns you'll follow (from the Context Primer)

---

## Step 3: Build

Create the AI processing pipeline:

### Backend
- **`server/routers/yt_processing.py`** — New router with `POST /api/yt-lab/process` endpoint
  - Pydantic request/response models (ProcessRequest, ProcessResponse)
  - Follow the pattern in `server/routers/yt_ingestion.py` exactly
  - Router prefix: `/api/yt-lab`
- **`server/services/yt_processor.py`** — Service class for AI processing logic
  - System prompt for strategy extraction
  - Takes transcript + user context + metadata → returns structured project + steps
  - Default model: `claude-sonnet-4-6` (configurable)
  - Uses existing ANTHROPIC_API_KEY from environment (subscription piping)
- Register the new router in `server/routers/__init__.py` and `server/main.py`

### Frontend
- Add `processVideo()` function to `ui/src/lib/api.ts`
- Add TypeScript types to `ui/src/lib/types.ts` (ProcessRequest, ProcessResponse)
- Add "Process Video" button to the project create flow in `YTStrategyLabPage.tsx`
  - Shows after successful ingestion
  - Processing spinner + status text
  - On completion, creates project with all steps pre-filled

### Key Rules (from Context Primer)
- NO SQLAlchemy models — V1 uses localStorage
- NO React Router — use `window.location.hash`
- NO separate API key config — use existing subscription piping
- Service class pattern (NOT inline API calls in router)
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

- Stay under 50% context window if possible. If verification pushes you to 55-60%, that's acceptable for bug fixes.
- Commit with clear messages describing what you built.
- Push to your branch when done.
