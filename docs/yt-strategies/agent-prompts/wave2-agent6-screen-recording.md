# Build Agent 6 — Phase 8: Screen Recording & Video Capture

## What You're Building

You are building **one feature** inside the **YT Strategy Lab** system in the AutoForge application (Greptacular codebase). YT Strategy Lab is a platform for extracting actionable strategies from YouTube videos and executing them with AI agents.

**Your feature:** Screen recording and video capture during computer-use execution. Captures screenshots at step transitions, short video clips (3-10 seconds) around key moments, and optionally records full sessions. All captures are organized per project/step and viewable in the strategy builder.

**Prerequisites:** Phase 4 (Computer Use Engine) must be done. You'll use the Docker container's X11 display and ffmpeg for capture.

---

## Step 1: Read These Documents (In This Order)

**Do not write any code until you have read all documents and confirmed your understanding.**

1. **Context Primer** — Read this FIRST:
   ```
   docs/yt-strategies/CONTEXT_PRIMER.md
   ```

2. **Your PRD** — The specific feature you're building:
   ```
   docs/yt-strategies/prds/08-screen-recording-and-capture.md
   ```

3. **Build Standards**:
   ```
   .claude/build-prompts/App Builder Prompt Template (Platform-Agnostic).txt
   ```

4. **Also read Phase 4's PRD** for Docker container context:
   ```
   docs/yt-strategies/prds/02-custom-computer-use-engine.md
   ```

---

## Step 2: Prove Understanding

Before writing code, briefly state:
1. The three capture types (screenshots, short clips, full session) and when each triggers
2. The storage structure under `.autoforge/yt-lab/{project_id}/captures/`
3. How ffmpeg captures from the X11 virtual display
4. The complete list of files you will create or modify

---

## Step 3: Build

### Backend Service
- **`server/services/screen_recorder.py`** — The main capture service:

  **Screenshot Capture:**
  - `capture_screenshot(display_number, output_path)` — Single frame capture
  - Triggers: step start, step complete, navigation, pause, error

  **Short Clip Capture:**
  - `capture_clip(display_number, output_path, duration=5)` — Short video clip
  - `capture_clip_async(...)` — Non-blocking version using threading
  - Triggers: step complete (3s), form fill (5s), button click (3s), error (5s)
  - Codec: libx264, preset ultrafast, CRF 28, 15fps

  **Full Session Recording:**
  - `SessionRecorder` class with `start()` / `stop()` methods
  - Runs ffmpeg as subprocess for entire session
  - Opt-in only (not default)
  - Codec: libx264, preset ultrafast, CRF 30, 10fps

  **Manual Capture:**
  - Endpoint for user-triggered capture (screenshot + optional 5s clip)

### Backend API
- Add to `server/routers/execution.py` (or create `server/routers/captures.py`):
  - `GET /api/execution/{session_id}/captures` — List all captures for session
  - `GET /api/execution/{session_id}/captures/{capture_id}` — Get specific capture file
  - `POST /api/execution/{session_id}/capture` — Manual capture trigger
  - `POST /api/execution/{session_id}/recording/start` — Start full session recording
  - `POST /api/execution/{session_id}/recording/stop` — Stop recording

### Frontend
- **`ui/src/components/yt-lab/CaptureGallery.tsx`** — Gallery component:
  - Thumbnail grid organized by step
  - Screenshots: click to enlarge in modal
  - Video clips: click to play inline (HTML5 `<video>` element)
  - Full recording: link to open in new tab
  - Show capture type icon (camera for screenshots, film for clips)
  - Show timestamp and trigger reason

- Integrate gallery into step detail view in `YTStrategyLabPage.tsx`
- Add capture types to `ui/src/lib/types.ts`
- Add capture API functions to `ui/src/lib/api.ts`

### Storage
- Captures stored at `.autoforge/yt-lab/{project_id}/captures/step-{N}/`
- Keep total storage reasonable (< 500MB per typical 7-step workflow)

### Auto-Capture Trigger Table
| Trigger | Type | Duration |
|---------|------|----------|
| Step starts | Screenshot | — |
| Step completes | Screenshot + 3s clip | 3s |
| Agent clicks button | 3s clip | 3s |
| Agent fills form | 5s clip | 5s |
| Agent navigates | Screenshot (after load) | — |
| User pauses | Screenshot | — |
| Error occurs | Screenshot + 5s clip | 5s |

### Key Rules
- Do NOT build a custom video player — use HTML5 `<video>` element
- ffmpeg and xdotool are already in the Docker container
- Container lifecycle managed by `server/services/docker_manager.py` (Phase 4)
- Follow existing service patterns

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
Read it. Follow all 8 phases. Fix any issues found. Note: ffmpeg capture testing may be limited without Docker — focus on code analysis, static verification, and API endpoint structure.

---

## Important

- This feature depends on Phase 4 — check that `server/services/docker_manager.py` and the Docker setup exist from Agent 3.
- This is a lighter build (~20K tokens). You have plenty of budget for thorough verification.
- Stay under 50% context window if possible. If verification pushes you to 55-60%, that's acceptable.
- Commit with clear messages. Push to your branch when done.
