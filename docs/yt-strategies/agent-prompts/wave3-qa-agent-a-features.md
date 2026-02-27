# QA Agent A — Verify Phases 2, 9, 3, 7 (UI & Backend Features)

## Your Role

You are a **QA verification agent**. Your job is to test and verify four features that were built by separate coding agents. You did NOT build these features — you are a fresh set of eyes. Find bugs. Fix them. Ship clean code.

## What Was Built (4 Features to Verify)

| Phase | Feature | Key Files |
|-------|---------|-----------|
| Phase 2 | YouTube Auto-Processor | `server/routers/yt_processing.py`, `server/services/yt_processor.py`, UI in `YTStrategyLabPage.tsx` |
| Phase 9 | Video Screenshot Intelligence | `server/services/screenshot_analyzer.py`, `ui/src/components/yt-lab/ScreenshotGallery.tsx` |
| Phase 3 | Batch YouTube Import | `server/routers/yt_batch.py`, `ui/src/components/yt-lab/BatchImportView.tsx` |
| Phase 7 | Model Routing & Roles | `server/services/model_router.py`, role dropdowns in step editor |

## Step 1: Read the Context

1. **Understand the vision** (what this system actually IS — it's a mini-app factory, not a single-purpose tool):
   ```
   docs/yt-strategies/VISION.md
   ```

2. **Understand the technical system:**
   ```
   docs/yt-strategies/CONTEXT_PRIMER.md
   ```

3. **Read the PRDs for each feature you're testing:**
   ```
   docs/yt-strategies/prds/07-youtube-auto-processor.md
   docs/yt-strategies/prds/04-video-screenshot-intelligence.md
   docs/yt-strategies/prds/01-batch-youtube-import.md
   docs/yt-strategies/prds/06-model-routing-and-roles.md
   ```

4. **Read the verification protocol and follow it exactly:**
   ```
   .claude/templates/e2e_verification_prompt.template.md
   ```

## Step 2: Execute the Full Verification Protocol

Follow every phase in `e2e_verification_prompt.template.md`:

1. **Phase 1: Parallel Research** — Investigate app structure, data flows, and hunt for bugs in the code
2. **Phase 2: Static Verification** — Lint, type check, build, run existing tests
3. **Phase 3: Functional Verification** — Start the app, test each feature end-to-end
4. **Phase 4: Cross-Feature Integration** — Do the features work together correctly?
5. **Phase 5: Responsive & Visual** — Check layouts at mobile/tablet/desktop
6. **Phase 6: Issue Handling** — Fix critical and high issues immediately
7. **Phase 7: Final Pass** — Re-run everything after fixes
8. **Phase 8: Report** — Output structured verification report

## Feature-Specific Test Cases

### Phase 2 (Auto-Processor)
- Does `POST /api/yt-lab/process` accept transcript + context and return structured project?
- Does the "Process Video" button appear after ingestion?
- Does processing create a project with meaningful steps (not just transcript dumps)?
- Does user context influence the output?
- Is the default model Sonnet 4.6?
- Error handling: what happens with empty transcript? Timeout?

### Phase 9 (Screenshot Intelligence)
- Do enhanced screenshot detection patterns work (screen transitions, results, instructions)?
- Does screenshot analysis return OCR text, classification, relevance score?
- Does the gallery display thumbnails per step?
- Can you click a screenshot to enlarge it?
- Is deduplication working (>95% similar frames removed)?
- Cap check: no more than 20-30 screenshots per 10-minute video?

### Phase 3 (Batch Import)
- Can you paste 3-5 URLs and get preview cards for all?
- Does the URL parser handle all formats (youtube.com, youtu.be, shorts)?
- Can you add context per video?
- Does "Process All" work and show progress?
- Do all processed videos become projects?
- What happens with an invalid URL in the batch?

### Phase 7 (Model Routing)
- Does each step have a model dropdown (Opus, Sonnet, Haiku, Auto)?
- Does each step have a role dropdown with the 6 default roles?
- Does "Auto" mode show the system's recommendation?
- Are model + role selections persisted to localStorage?
- Does "Custom (from Role Library)" link to `/#/roles`?

## Step 3: Fix Issues

- Fix critical and high severity issues immediately
- Re-verify fixes work
- Commit fixes with clear messages
- Push to branch

## Step 4: Report

Output the structured verification report as specified in the protocol.

## Important

- You can go up to 55-60% context if needed for bug fixes. QA agents fixing small targeted issues don't suffer from context degradation.
- Be thorough. The goal is zero critical/high issues remaining.
- Commit and push all fixes.
