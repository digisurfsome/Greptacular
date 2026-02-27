# Build Agent 3 — Phase 4: Custom Computer Use Execution Engine

## What You're Building

You are building **one feature** inside the **YT Strategy Lab** system in the AutoForge application (Greptacular codebase). YT Strategy Lab is a platform for extracting actionable strategies from YouTube videos and executing them with AI agents.

**Your feature:** The core computer-use execution engine — a Docker container with Xvfb + Chromium + noVNC, a Python agent loop using Anthropic's Computer Use API, and REST/WebSocket endpoints for controlling execution sessions. This is the BIGGEST single feature and the foundation that Phases 5, 6, and 8 build on.

Phase 1 (core UI + YouTube ingestion) is already done. You are building Phase 4.

---

## Step 1: Read These Documents (In This Order)

**Do not write any code until you have read all three documents and confirmed your understanding.**

1. **Context Primer** — Read this FIRST. It explains the entire system, vocabulary, architecture, and patterns:
   ```
   docs/yt-strategies/CONTEXT_PRIMER.md
   ```

2. **Your PRD** — The specific feature you're building:
   ```
   docs/yt-strategies/prds/02-custom-computer-use-engine.md
   ```

3. **Options Comparison** — Architectural decision context (read for background, not a build spec):
   ```
   docs/yt-strategies/prds/09-computer-use-options-comparison.md
   ```

4. **Build Standards** — Code quality standards to follow:
   ```
   .claude/build-prompts/App Builder Prompt Template (Platform-Agnostic).txt
   ```

---

## Step 2: Prove Understanding

Before writing code, briefly state:
1. What the Computer Use Engine does (one paragraph)
2. The complete list of files you will create
3. How the agent loop works (screenshot → Claude API → tool execution → repeat)
4. How the Docker container, backend service, and frontend connect

---

## Step 3: Build

This is a large feature. Build in this order:

### 3a. Docker Container
- **`docker/computer-use/Dockerfile`** — Based on Anthropic's reference image
  - Xvfb virtual display (1920x1080)
  - Chromium browser
  - noVNC server (port 6080)
  - ffmpeg (for future screen recording)
  - supervisord for process management
- **`docker/computer-use/supervisord.conf`** — Process manager config

### 3b. Backend Services
- **`server/services/computer_use_agent.py`** — The core `ComputerUseAgent` class:
  - Agent loop: send prompt → get response → execute tool calls → repeat
  - Uses `computer_20250124`, `text_editor_20250124`, `bash_20250124` tools
  - Pause/resume support (check `self.paused` between tool calls)
  - Message injection (inject human messages mid-execution)
  - Screenshot capture at step transitions
  - Default model: `claude-opus-4-6`
  - Uses existing ANTHROPIC_API_KEY (subscription piping)

- **`server/services/docker_manager.py`** — Container lifecycle:
  - Start/stop Docker containers
  - Port allocation and cleanup
  - Health checks
  - Container isolation per session

- **`server/routers/execution.py`** — REST API endpoints:
  - `POST /api/execution/start` — Start a new execution session
  - `POST /api/execution/{session_id}/pause` — Pause execution
  - `POST /api/execution/{session_id}/resume` — Resume execution
  - `POST /api/execution/{session_id}/inject` — Inject human message
  - `POST /api/execution/{session_id}/stop` — Stop execution
  - `GET /api/execution/{session_id}/status` — Get session status
  - `WS /ws/execution/{session_id}` — Real-time event stream

- Register router in `server/routers/__init__.py` and `server/main.py`

### 3c. Frontend (Minimal — just types and API)
- Add execution types to `ui/src/lib/types.ts`:
  - `YTExecutionSession`, `YTExecutionEvent`, `YTExecutionStatus`
  - Status union: `'idle' | 'starting' | 'running' | 'paused' | 'completed' | 'error'`
- Add API functions to `ui/src/lib/api.ts`:
  - `startExecution()`, `pauseExecution()`, `resumeExecution()`, `injectMessage()`, `stopExecution()`, `getExecutionStatus()`
- **Do NOT build the execution viewer UI** — that's Phase 5 (Agent 5's job)

### 3d. Environment Config
- Add environment variables to `.env.example` or document them:
  - `COMPUTER_USE_ENABLED`, `COMPUTER_USE_DOCKER_IMAGE`, `COMPUTER_USE_DISPLAY_WIDTH/HEIGHT`
  - `COMPUTER_USE_NOVNC_PORT`, `COMPUTER_USE_DEFAULT_MODEL`

### Key Rules (from Context Primer)
- Container lifecycle in services, NOT in routers
- Follow `server/services/process_manager.py` as the pattern for process lifecycle
- Follow `server/services/terminal_manager.py` as the pattern for interactive sessions
- Follow `server/routers/yt_ingestion.py` for router patterns
- Use Pydantic models for ALL request/response bodies
- WebSocket follows existing `/ws/` pattern

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
Read it. Follow all 8 phases. Fix any issues found. Note: Docker container testing may be limited without Docker running — focus on code analysis, static verification, and API endpoint structure verification.

---

## Important

- **This is the biggest single build.** You have the full session budget (~43K tokens of 61K available). Stay focused.
- Stay under 50% context window if possible. If verification pushes you to 55-60%, that's acceptable for bug fixes.
- This feature is INDEPENDENT — only depends on Phase 1 (already done).
- Other agents (Phases 5, 6, 8) depend on YOUR output. Build clean, well-documented interfaces.
- Commit with clear messages. Push to your branch when done.
