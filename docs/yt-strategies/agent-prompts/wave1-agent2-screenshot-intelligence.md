# Build Agent 2 — Phase 9: Video Screenshot Intelligence

## What You're Building

You are building **one feature** inside the **YT Strategy Lab** system in the AutoForge application (Greptacular codebase). YT Strategy Lab is a platform for extracting actionable strategies from YouTube videos and executing them with AI agents.

**Your feature:** Enhanced screenshot capture and AI-powered analysis of video screenshots. The system captures screenshots at key moments during YouTube videos, runs OCR + vision analysis on them, and links them to strategy steps.

Phase 1 (core UI + YouTube ingestion) is already done. You are building Phase 9, which only depends on Phase 1's ingestion backend.

---

## Step 1: Read These Documents (In This Order)

**Do not write any code until you have read all three documents and confirmed your understanding.**

1. **Context Primer** — Read this FIRST. It explains the entire system, vocabulary, architecture, and patterns:
   ```
   docs/yt-strategies/CONTEXT_PRIMER.md
   ```

2. **Your PRD** — The specific feature you're building:
   ```
   docs/yt-strategies/prds/04-video-screenshot-intelligence.md
   ```

3. **Build Standards** — Code quality standards to follow:
   ```
   .claude/build-prompts/App Builder Prompt Template (Platform-Agnostic).txt
   ```

---

## Step 2: Prove Understanding

Before writing code, briefly state:
1. What Screenshot Intelligence does (one paragraph)
2. What files you will create or modify
3. How it integrates with the existing ingestion backend

---

## Step 3: Build

### Backend Enhancements
- **Enhance `server/routers/yt_ingestion.py`** — Add new screenshot detection patterns:
  - Screen transition cues ("I opened up", "I went to", "I navigated to")
  - Result cues ("here's what it created", "the output was")
  - Instruction cues ("all I typed was", "I just prompted it to")
  - Duration-based capture (every 30-60 seconds as baseline)
  - Multi-frame capture around cue timestamps (cue-2s, cue, cue+2s)

- **`server/services/screenshot_analyzer.py`** — New service for screenshot analysis:
  - OCR text extraction from screenshots
  - UI/app identification (what website/tool is shown)
  - Content classification (prompt, result, dashboard, form, navigation)
  - Relevance scoring (1-10)
  - Context linking to nearest transcript segment
  - Uses Claude Haiku 4.5 for vision analysis (fast + cheap)

- Add new Pydantic models: `ScreenshotCapture`, `EnhancedIngestResponse`
- Extend the ingest endpoint response to include screenshot analysis

### Frontend
- Add screenshot gallery component to `ui/src/components/yt-lab/ScreenshotGallery.tsx`
  - Thumbnail grid per step
  - Click to enlarge in a modal
  - Show OCR text below each screenshot
  - Show relevance score and classification badge
- Integrate gallery into the step detail view in `YTStrategyLabPage.tsx`
- Add types to `ui/src/lib/types.ts`

### Key Rules (from Context Primer)
- Follow `server/routers/yt_ingestion.py` patterns exactly
- Prefix all types with `YT`
- Use `ffmpeg` and `yt-dlp` for capture (already available)
- No more than 20-30 screenshots per 10-minute video
- Deduplicate frames that are >95% similar

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
- This feature is INDEPENDENT — it only depends on Phase 1 (already done). No other agents need to finish first.
- Commit with clear messages. Push to your branch when done.
