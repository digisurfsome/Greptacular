# QA Agent B — Verify Phases 4, 5, 6, 8 (Execution Engine Stack)

## Your Role

You are a **QA verification agent**. Your job is to test and verify four features that form the computer-use execution stack. You did NOT build these features — you are a fresh set of eyes. Find bugs. Fix them. Ship clean code.

## What Was Built (4 Features to Verify)

| Phase | Feature | Key Files |
|-------|---------|-----------|
| Phase 4 | Computer Use Engine | `server/services/computer_use_agent.py`, `server/services/docker_manager.py`, `server/routers/execution.py`, `docker/computer-use/Dockerfile` |
| Phase 5 | Live Execution Viewer | `ui/src/components/yt-lab/ExecutionViewer.tsx`, `StepTracker.tsx`, `AgentLog.tsx`, `BrowserView.tsx` |
| Phase 6 | Pause/Resume/Takeover | `ui/src/components/yt-lab/ExecutionTopBar.tsx`, state machine in viewer |
| Phase 8 | Screen Recording | `server/services/screen_recorder.py`, `ui/src/components/yt-lab/CaptureGallery.tsx` |

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
   docs/yt-strategies/prds/02-custom-computer-use-engine.md
   docs/yt-strategies/prds/03-live-execution-viewer.md
   docs/yt-strategies/prds/05-pause-resume-takeover.md
   docs/yt-strategies/prds/08-screen-recording-and-capture.md
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
4. **Phase 4: Cross-Feature Integration** — Do the features chain correctly (4→5→6, 4→8)?
5. **Phase 5: Responsive & Visual** — Check layouts at mobile/tablet/desktop
6. **Phase 6: Issue Handling** — Fix critical and high issues immediately
7. **Phase 7: Final Pass** — Re-run everything after fixes
8. **Phase 8: Report** — Output structured verification report

## Feature-Specific Test Cases

### Phase 4 (Computer Use Engine)
- Does the `ComputerUseAgent` class have the correct tool definitions (`computer_20250124`, `text_editor_20250124`, `bash_20250124`)?
- Does the agent loop correctly: send prompt → get response → check stop_reason → execute tools → repeat?
- Does `pause()` wait for current tool call to complete before pausing?
- Does `inject_message()` correctly add user messages to the conversation?
- Does `DockerManager` handle container start/stop/health check?
- Are all API endpoints registered: start, pause, resume, inject, stop, status?
- Is the WebSocket handler at `/ws/execution/{session_id}` properly set up?
- Does it default to `claude-opus-4-6` for execution?
- Does it use existing `ANTHROPIC_API_KEY` (no separate key config)?

### Phase 5 (Live Execution Viewer)
- Does the split-screen layout render: 280px sidebar + 48px top bar + noVNC main area?
- Does StepTracker show all steps with correct status indicators (✓/●/○)?
- Does AgentLog auto-scroll and show color-coded entries?
- Are WebSocket events properly handled (status_change, agent_action, step_change, screenshot)?
- Does the noVNC iframe connect and display the virtual display?
- Is the viewer view-only by default?
- Responsive: does sidebar collapse at <1200px? Full-screen browser at <768px?

### Phase 6 (Pause/Resume/Takeover)
- State machine correctness: IDLE→RUNNING→PAUSED→RUNNING? PAUSED→TAKEOVER→RUNNING?
- Does Pause show correct buttons (Resume + Take Over)?
- Does Take Over enable interactive noVNC (`viewOnly = false`)?
- Does "Return Control" take screenshot and resume agent with context?
- Does chat input send messages via inject endpoint?
- Do chat messages appear in agent log with correct prefixes (YOU: / AGENT:)?
- Does Stop button work from any state?
- No orphaned state: what happens on connection loss?

### Phase 8 (Screen Recording)
- Does `capture_screenshot()` work with ffmpeg/import commands?
- Does `capture_clip()` produce valid MP4 files?
- Does `SessionRecorder` start/stop cleanly?
- Are auto-capture triggers firing at the right moments?
- Does CaptureGallery display thumbnails organized by step?
- Can you click screenshots to enlarge? Play clips inline?
- Is storage organized at `.autoforge/yt-lab/{project_id}/captures/`?
- Storage cap: is total size reasonable?

## Testing Limitations

Some features require Docker to fully test (container startup, noVNC display, ffmpeg capture). If Docker is not available:
- Focus on **code analysis** (bug hunting in the source)
- Verify **API endpoint structure** (correct routes, Pydantic models, error handling)
- Test **UI components** in isolation (do they render? do they handle states correctly?)
- Verify **static analysis** (lint, types, build)
- Check **WebSocket handler** code paths
- Trace **logic errors** in the agent loop and state machine

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
- The execution stack is the most complex part of the system — pay extra attention to state management and error handling.
- Commit and push all fixes.
