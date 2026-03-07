# Browser System Test Script — Full Sweep for Next Agent

## What You're Testing

AutoForge has **3 separate browser systems**. Your job is to find every bug across all of them.

### The 3 Browser Systems

| System | Status | What It Does |
|--------|--------|-------------|
| **1. Playwright MCP** | FULLY WORKING | Coding/testing agents use it to browse the web, test apps, take screenshots via MCP tools |
| **2. Docker/noVNC (YT Strategy Lab)** | Infrastructure done, agent loop is PLACEHOLDER | Visual browser in Docker container streamed via noVNC — `_execute_step()` just sleeps 2s |
| **3. Computer Use QA Module** | PLACEHOLDER | Standalone budget-controlled QA — immediately returns "skipped, API pending" |

**Systems 2 and 3 have complete infrastructure but no actual AI agent actions** — they're waiting for Claude Computer Use API support in the SDK. Test their infrastructure (Docker, WebSocket, state machine, UI) even though the agent loop is simulated.

## How System 1 Works (Playwright MCP — The Main One)

### Architecture Overview

```
Agent (Claude) → MCP Tool Call → Playwright MCP Server → Browser Instance → Website
                                                    ↑
                                              Config from client.py:
                                              - headless vs visible
                                              - browser type (firefox/chrome/webkit/msedge)
                                              - viewport size (1280x720)
                                              - isolated mode (for parallel agents)
```

## How System 2 Works (Docker/noVNC Computer Use)

```
UI (YTStrategyLabPage) → startExecution API → computer_use_agent.py
       |                                              |
       v                                              v
ExecutionViewer                             DockerManager.start_container()
(BrowserView + StepTracker + AgentLog)                |
       |                                              v
       v                                   Docker container (X11+noVNC)
noVNC iframe ← WebSocket events                       |
                                                      v
                                           CaptureManager (ffmpeg)
                                                      |
                                                      v
                                           _execute_step() [PLACEHOLDER — sleeps 2s]
```

### System 2 Key Files

| File | What It Does |
|------|-------------|
| `server/services/computer_use_agent.py` | State machine: idle→running→paused/takeover→completed. `_execute_step()` is placeholder (lines 380-407) |
| `server/services/docker_manager.py` | Docker container lifecycle, noVNC on port 6080, graceful fallback when Docker unavailable |
| `server/services/screen_recorder.py` | ffmpeg x11grab screenshots, clips, full session recording |
| `server/services/screenshot_analyzer.py` | AI vision analysis with Claude Haiku |
| `server/routers/execution.py` | REST: start/pause/resume/stop/inject/takeover/jump + WebSocket |
| `server/routers/captures.py` | Capture file endpoints (list, retrieve, manual trigger, recording control) |
| `docker/computer-use/Dockerfile` | Ubuntu 24.04, Xvfb, x11vnc, noVNC, Chromium, Fluxbox |
| `ui/src/components/yt-lab/ExecutionViewer.tsx` | Main viewer: sidebar + BrowserView |
| `ui/src/components/yt-lab/BrowserView.tsx` | noVNC iframe wrapper |
| `ui/src/components/yt-lab/ExecutionTopBar.tsx` | Control bar (pause/resume/stop/takeover) |
| `ui/src/components/yt-lab/CaptureGallery.tsx` | Screenshot/clip grid with lightbox |
| `ui/src/hooks/useExecutionWebSocket.ts` | WebSocket for execution events |

### System 3 Key Files

| File | What It Does |
|------|-------------|
| `computer_use.py` | Budget tracking ($1-$10), session runner — immediately returns "skipped" |
| `.claude/templates/computer_use_prompt.template.md` | Prompt template for CU sessions |

## Known Bug (FIXED): Headless Default Mismatch

`schemas.py` defaulted to `True` (headless) while `client.py` defaulted to `False` (visible). This has been fixed — both now default to `False` (visible).

### Key Files

| File | What It Does |
|------|-------------|
| `client.py` (lines 24-32) | Default config: `DEFAULT_PLAYWRIGHT_HEADLESS = False`, `DEFAULT_PLAYWRIGHT_BROWSER = "firefox"` |
| `client.py` (lines 257-287) | `PLAYWRIGHT_TOOLS` — full list of 19 MCP tools the agent can call |
| `client.py` (lines 463-489) | MCP server setup — builds npx command with args |
| `client.py` (lines 75-97) | `get_playwright_headless()` and `get_playwright_browser()` — read env vars |
| `server/services/process_manager.py` (line 429) | Passes `PLAYWRIGHT_HEADLESS` env var to subprocess |
| `server/routers/settings.py` (lines 131, 176-177) | Settings API for headless toggle |
| `ui/src/components/SettingsModal.tsx` (lines 408-424) | UI toggle for headless mode |
| `ui/src/components/workspace/WorkspaceChat.tsx` | Visible/Headless toggle pill in chat header |

### The 19 Playwright MCP Tools (What the Agent Can Call)

**Navigation:**
1. `browser_navigate` — Go to a URL
2. `browser_navigate_back` — Go back

**Screenshots & DOM:**
3. `browser_take_screenshot` — Capture current page as image
4. `browser_snapshot` — Get accessible DOM snapshot (text representation)

**Element Interaction:**
5. `browser_click` — Click an element
6. `browser_type` — Type text into an element
7. `browser_fill_form` — Fill a form field
8. `browser_select_option` — Select from dropdown
9. `browser_press_key` — Press keyboard key
10. `browser_drag` — Drag and drop
11. `browser_hover` — Hover over element
12. `browser_file_upload` — Upload a file

**JavaScript & Debugging:**
13. `browser_evaluate` — Run JavaScript in page context
14. `browser_console_messages` — Get console log output
15. `browser_network_requests` — Get network requests

**Browser Management:**
16. `browser_resize` — Change viewport size
17. `browser_wait_for` — Wait for element/condition
18. `browser_handle_dialog` — Handle alert/confirm/prompt dialogs
19. `browser_install` — Install browser binaries
20. `browser_close` — Close browser
21. `browser_tabs` — Manage tabs

**REMOVED (known crash):**
- `browser_run_code` — Commented out in client.py because it crashes the Playwright MCP server

---

## How to Detect Bugs

Since this is internal agent tooling, bugs show up in these places:

### 1. Console Errors (Browser Dev Tools)
- Open AutoForge UI in Chrome
- Press F12 → Console tab
- Look for red errors, especially during agent runs

### 2. Agent Output Logs (Debug Panel)
- In AutoForge, press `D` to open the debug panel
- Watch the "Agent" tab for error lines
- Look for: `MCP error`, `Playwright`, `browser`, `timeout`, `crashed`

### 3. Server Terminal Output
- The terminal running `start_ui.bat` / `start_ui.sh` shows Python server output
- Look for Python tracebacks, MCP server errors, subprocess crashes

### 4. WebSocket Messages
- In browser dev tools → Network → WS tab
- Filter for `agent_update` messages with `state: "error"`

### 5. Process Crashes
- If the Playwright MCP server crashes, the agent loses all browser tools mid-session
- Signs: agent suddenly can't take screenshots, "MCP server disconnected" errors

---

## Test Scenarios — The Full Sweep

### PHASE 1: Configuration & Startup

These test if the browser system initializes correctly under different configurations.

**Test 1.1: Default Configuration**
- Start an agent with default settings (visible browser, Firefox)
- Expected: Browser window appears, agent can navigate
- Check: No errors in server terminal about Playwright startup

**Test 1.2: Headless Mode Toggle**
- Go to Settings (`,` key) → toggle "Headless Browser" ON
- Start an agent
- Expected: NO visible browser window, but agent still works
- Check: `PLAYWRIGHT_HEADLESS=true` appears in process env

**Test 1.3: Headless Mode Toggle via Workspace**
- In Workspace chat header, click the Visible/Headless toggle pill
- Expected: Setting changes, reflected in next agent start

**Test 1.4: Browser Type Switching**
- Set `PLAYWRIGHT_BROWSER=chrome` in environment
- Start an agent
- Expected: Chrome launches instead of Firefox
- Repeat for: `webkit`, `msedge`
- Check: `get_playwright_browser()` returns correct value

**Test 1.5: YOLO Mode (No Browser)**
- Start agent in YOLO mode (lightning bolt button)
- Expected: No Playwright MCP server started at all
- Check: Server output says "YOLO MODE (no Playwright)"
- Check: Agent's allowed_tools does NOT include any `mcp__playwright__*` tools

**Test 1.6: Reviewer Agent (No Browser)**
- If you can trigger a reviewer agent type
- Expected: No Playwright MCP server (reviewers don't need browsers)

**Test 1.7: Invalid Browser Type**
- Set `PLAYWRIGHT_BROWSER=safari` (invalid)
- Start an agent
- Expected: Should fallback or error gracefully, not crash

---

### PHASE 2: Navigation & Screenshots

These test core browsing functionality.

**Test 2.1: Basic Navigation**
- Have the agent navigate to a known URL (e.g., the dev server it built)
- Expected: Page loads, no timeout errors
- Check: Agent can describe what it sees via `browser_snapshot`

**Test 2.2: Screenshot Capture**
- Have the agent take a screenshot
- Expected: Base64 image data returned (large response)
- Check: `max_buffer_size=10 * 1024 * 1024` in client.py handles the data
- Check: No truncation errors in context compaction

**Test 2.3: Navigate Back**
- Navigate to page A, then page B, then call `browser_navigate_back`
- Expected: Returns to page A

**Test 2.4: Invalid URL Navigation**
- Have agent navigate to `http://localhost:99999` (nothing running)
- Expected: Graceful error, agent can recover and try another URL
- Check: No MCP server crash

**Test 2.5: HTTPS Certificate Errors**
- Navigate to a self-signed HTTPS URL
- Expected: Graceful handling (Playwright usually ignores cert errors)

**Test 2.6: Very Large Page**
- Navigate to a page with thousands of DOM elements
- Expected: `browser_snapshot` returns without timeout
- Check: Context window doesn't blow up from massive snapshot data

---

### PHASE 3: Element Interaction

These test the agent's ability to interact with page elements.

**Test 3.1: Click**
- Agent clicks a button on a page
- Expected: Button action fires, page state changes
- Check: Agent can verify the change via follow-up snapshot

**Test 3.2: Type Text**
- Agent types into an input field
- Expected: Text appears in field
- Check: Special characters, unicode, long strings

**Test 3.3: Fill Form**
- Agent fills a multi-field form and submits
- Expected: Form submission works

**Test 3.4: Select Dropdown**
- Agent selects an option from a `<select>` dropdown
- Expected: Correct option selected

**Test 3.5: Press Key**
- Agent presses Enter, Tab, Escape, arrow keys
- Expected: Key events fire correctly

**Test 3.6: Drag and Drop**
- Agent drags element A to position B
- Expected: Element moves (this is tricky, may have edge cases)

**Test 3.7: Hover**
- Agent hovers over an element that shows a tooltip
- Expected: Tooltip appears in next snapshot

**Test 3.8: File Upload**
- Agent uploads a file to a file input
- Expected: File is accepted
- Edge case: What file paths can the agent access? (sandbox restrictions)

**Test 3.9: Click Non-Existent Element**
- Agent tries to click a selector that doesn't exist
- Expected: Graceful error message, not a crash

**Test 3.10: Interact with Element Inside iframe**
- Agent tries to interact with content inside an iframe
- Expected: May or may not work — document the behavior

---

### PHASE 4: JavaScript & Debugging

**Test 4.1: Evaluate JavaScript**
- Agent runs `document.title` via `browser_evaluate`
- Expected: Returns the page title

**Test 4.2: Evaluate with DOM Manipulation**
- Agent runs JS that changes page content
- Expected: Changes visible in next screenshot/snapshot

**Test 4.3: Console Messages**
- Navigate to a page with `console.log`, `console.error` calls
- Call `browser_console_messages`
- Expected: Returns the console output

**Test 4.4: Network Requests**
- Navigate to a page that makes API calls
- Call `browser_network_requests`
- Expected: Returns list of network requests with URLs, status codes

**Test 4.5: Evaluate Throws Error**
- Agent runs JS that throws: `browser_evaluate("throw new Error('test')")`
- Expected: Error returned gracefully, not a crash

**Test 4.6: Evaluate Infinite Loop**
- Agent runs `while(true){}` via evaluate
- Expected: Timeout kicks in, graceful error

---

### PHASE 5: Browser Management

**Test 5.1: Resize Viewport**
- Agent calls `browser_resize` to change to mobile dimensions (375x812)
- Expected: Viewport changes, next screenshot shows mobile layout

**Test 5.2: Wait For Element**
- Agent calls `browser_wait_for` for an element that appears after delay
- Expected: Waits and succeeds

**Test 5.3: Wait For Element That Never Appears**
- Agent waits for `#nonexistent-element`
- Expected: Timeout error, not a crash

**Test 5.4: Handle Dialog (Alert)**
- Navigate to page that triggers `alert()`
- Call `browser_handle_dialog`
- Expected: Dialog dismissed

**Test 5.5: Handle Dialog (Confirm)**
- Navigate to page with `confirm()`
- Expected: Agent can accept or dismiss

**Test 5.6: Handle Dialog (Prompt)**
- Navigate to page with `prompt()`
- Expected: Agent can enter text and accept

**Test 5.7: Tab Management**
- Agent opens multiple tabs, switches between them
- Expected: `browser_tabs` shows correct tab list

**Test 5.8: Close Browser**
- Agent calls `browser_close`
- Expected: Browser closes cleanly
- Then: Can the agent open a new browser? Or is the MCP server dead?

**Test 5.9: Browser Install**
- Call `browser_install` when browsers are already installed
- Expected: No-op or quick success, not an error

---

### PHASE 6: Parallel Mode & Isolation

**Test 6.1: Two Agents, Isolated Browsers**
- Start parallel mode with 2+ agents
- Expected: Each agent gets `--isolated` flag
- Check: Agents don't interfere with each other's browser tabs

**Test 6.2: Agent Finishes, Browser Cleanup**
- After an agent finishes its feature, does its browser close?
- Expected: Browser process cleans up
- Check: No orphaned browser processes (`ps aux | grep playwright`)

**Test 6.3: Agent Crashes Mid-Browser-Use**
- Kill an agent process while it's browsing
- Expected: Browser process also dies (or gets cleaned up)
- Check: No zombie processes

**Test 6.4: Concurrent Screenshots**
- Two agents take screenshots at the same time
- Expected: Both succeed, no cross-contamination

**Test 6.5: Max Process Limits**
- Start 5 agents in parallel (MAX_PARALLEL_AGENTS)
- Expected: 5 separate browser instances, system doesn't run out of memory
- Check: Resource usage stays reasonable

---

### PHASE 7: Context Window & Data Flow

**Test 7.1: Screenshot Size in Context**
- Agent takes many screenshots in one session
- Expected: Context compaction handles the base64 data
- Check: client.py line 596 says screenshots should be summarized, not stored verbatim
- Check: `max_buffer_size=10 * 1024 * 1024` is sufficient

**Test 7.2: Rapid Screenshot Spam**
- Agent takes 20 screenshots in quick succession
- Expected: No buffer overflow, no MCP server crash

**Test 7.3: Snapshot of Complex Page**
- Agent snapshots a page with hundreds of elements
- Expected: Accessible snapshot is manageable size
- Check: Doesn't blow up agent's context budget

**Test 7.4: Network Request Data Volume**
- Navigate to a page that makes 100+ API calls
- Call `browser_network_requests`
- Expected: Data is returned without overwhelming context

---

### PHASE 8: Error Recovery & Edge Cases

**Test 8.1: MCP Server Crash Recovery**
- The `browser_run_code` tool was removed because it crashed the MCP server
- Verify it's still commented out (client.py line 276)
- If someone uncomments it: does it still crash?

**Test 8.2: Network Disconnection**
- Agent navigates to a URL, then network drops
- Expected: Timeout error, not a hang

**Test 8.3: Page Crash (Out of Memory)**
- Navigate to a page that allocates massive memory
- Expected: Tab crash is reported, agent can recover

**Test 8.4: Mixed Content (HTTP on HTTPS)**
- Navigate to HTTPS page that loads HTTP resources
- Expected: Browser handles it (Playwright is usually lenient)

**Test 8.5: Authentication Dialogs**
- Navigate to URL that triggers HTTP Basic Auth
- Expected: Either handles it or errors gracefully

**Test 8.6: Download Triggered**
- Navigate to a URL that triggers a file download
- Expected: Doesn't hang the browser

**Test 8.7: Popup Windows**
- Page opens a popup via `window.open()`
- Expected: Popup handled (may appear as new tab)

**Test 8.8: WebSocket Pages**
- Navigate to a page using WebSockets
- Expected: Page loads normally, snapshot works

---

## How to Actually Run These Tests

Since these tools are agent-internal (not buttons you push), here's how to exercise them:

### Method 1: Direct Agent Prompting
Start an AutoForge agent on a test project and give it prompts that force browser use:
- "Navigate to http://localhost:3000 and take a screenshot"
- "Fill in the login form and submit it"
- "Check the console for errors"
- "Resize the browser to mobile and screenshot"

### Method 2: Manual MCP Tool Testing
If you can invoke MCP tools directly:
```bash
# Start the Playwright MCP server standalone
npx @playwright/mcp@latest --browser firefox --viewport-size 1280x720
```
Then send JSON-RPC calls to test individual tools.

### Method 3: Python Script Testing
Write a test script that creates a `ClaudeSDKClient` via `client.py` and sends tool calls:
```python
from client import create_client
from pathlib import Path

client = create_client(
    project_dir=Path("/tmp/test-project"),
    model="claude-sonnet-4-6",
    yolo_mode=False,
)
# Then exercise browser tools through the client
```

### Method 4: Check Code Paths Statically
Read through `client.py` and look for:
- Unhandled edge cases in `get_playwright_headless()` and `get_playwright_browser()`
- Missing error handling in MCP server setup
- Env var parsing issues
- Permission mismatches (tool in allowed_tools but not in permissions_list or vice versa)

---

---

### PHASE 9: Docker/noVNC Computer Use (System 2) — Infrastructure Testing

Even though the agent loop is a placeholder, test the infrastructure:

**Test 9.1: Execution Start (Docker Available)**
- Call `POST /api/execution/start` with valid project
- Expected: Docker container starts, noVNC URL returned
- Check: Container named `autoforge-cu-{session_id[:12]}` is running

**Test 9.2: Execution Start (No Docker)**
- Try starting execution when Docker daemon isn't running
- Expected: Graceful degradation — mock URLs returned, warning logged
- Check: `docker_manager.py` fallback path works without crash

**Test 9.3: WebSocket Event Stream**
- Connect to `/ws/execution/{session_id}`
- Expected: Receives `status_change`, `agent_thinking`, `step_change` events
- Check: `useExecutionWebSocket.ts` handles all event types

**Test 9.4: Pause/Resume/Stop Controls**
- Start execution, then pause, resume, stop
- Expected: State machine transitions correctly: running→paused→running→stopped
- Check: WebSocket broadcasts correct status events

**Test 9.5: Takeover Mode**
- Enable takeover mode via `POST /{id}/takeover`
- Expected: `BrowserView.tsx` switches from `view_only=true` to `view_only=false` in noVNC iframe
- Check: "YOU ARE IN CONTROL" banner appears

**Test 9.6: Message Injection**
- Send message via `POST /{id}/inject`
- Expected: Message appears in agent log, broadcast via WebSocket

**Test 9.7: Step Jump**
- Jump to a specific step via `POST /{id}/jump`
- Expected: Agent moves to that step

**Test 9.8: BrowserView Component**
- Load `ExecutionViewer` in the YT Lab page
- Expected: No console errors, status overlays render correctly for each state (idle, completed, error, loading, paused)

**Test 9.9: CaptureGallery Component**
- Check capture gallery renders with mock/empty data
- Expected: No crashes, empty state handled
- Check: Lightbox modal works for screenshots, video player works for clips

**Test 9.10: Session Cleanup**
- Stop execution
- Expected: Docker container removed, session cleared from registry
- Check: No orphaned containers (`docker ps -a | grep autoforge-cu`)

**Test 9.11: Concurrent Sessions**
- Start 2+ execution sessions simultaneously
- Expected: Each gets its own container, WebSocket, state machine
- Check: Events don't cross-contaminate between sessions

---

### PHASE 10: Computer Use QA Module (System 3) — Placeholder Verification

**Test 10.1: Module Returns "Skipped"**
- Call `run_computer_use_session()` from `computer_use.py`
- Expected: Immediately returns status "skipped" with "API pending" message
- Check: No crash, clean exit

**Test 10.2: Budget Tracking**
- Create `ComputerUseBudget(max_budget=5.0)`
- Expected: Budget tracking works (even though nothing spends it)
- Check: Spending more than max raises error

**Test 10.3: Settings Integration**
- Check `computer_use_enabled` and `computer_use_budget` in settings
- Expected: Settings save/load correctly
- Check: `computer_use_enabled` defaults to `False`

**Test 10.4: Report Output**
- After running session, check for `{project_dir}/.autoforge/computer-use-report.json`
- Expected: Report file created with "skipped" status

---

### PHASE 11: Static Code Analysis — Cross-System Consistency

**Test 11.1: Tool Permission Alignment**
- In `client.py`, verify every tool in `PLAYWRIGHT_TOOLS` (line 257) is also in `permissions_list` (line 401-404)
- Expected: Perfect alignment — no tool allowed but not permitted, or vice versa

**Test 11.2: Agent Type Exclusions**
- Verify reviewer agents are excluded from browser in BOTH allowed_tools AND permissions
- Check lines 368-369 and 401-404

**Test 11.3: YOLO Mode Exclusion**
- Verify YOLO mode excludes Playwright from BOTH allowed_tools, permissions, AND mcp_servers
- Check: No MCP server started, no tools listed

**Test 11.4: Env Var Parsing**
- `get_playwright_headless()`: What happens if env var is "yes", "1", "TRUE", "True", empty string?
- `get_playwright_browser()`: What if env var is empty? Spaces? Invalid value?
- Expected: All edge cases handled gracefully

**Test 11.5: Schema Default Consistency**
- Verify `schemas.py` `playwright_headless` default matches `client.py` `DEFAULT_PLAYWRIGHT_HEADLESS`
- Both should be `False` (visible browser)
- Also check `settings.py` `_parse_bool` default matches

**Test 11.6: Execution Router Import Safety**
- Check `server/main.py` imports `execution_router` and `captures_router`
- Expected: No import errors even if Docker is unavailable

---

## Definition of Done — When You've Found Everything

You can stop testing when:

1. All 11 phases have been exercised (or confirmed impossible to test in this environment)
2. Every Playwright MCP tool (all 19) has been verified to not crash the MCP server
3. Configuration switches (headless, browser type, YOLO, isolated) all work correctly
4. Parallel mode doesn't create cross-contamination or orphan processes
5. Error paths (bad URLs, missing elements, timeouts) all fail gracefully
6. No Python tracebacks in server terminal
7. No uncaught exceptions in browser console
8. Context compaction correctly summarizes screenshot data
9. The commented-out `browser_run_code` is still safely disabled
10. Docker/noVNC system handles Docker-unavailable gracefully (System 2)
11. Computer Use QA module returns "skipped" cleanly (System 3)
12. All defaults are consistent across schemas.py, settings.py, and client.py

## Bugs Found — Log Template

For each bug found, log:

```
BUG #: [number]
SEVERITY: Critical / High / Medium / Low
PHASE: [which test phase]
TEST: [which specific test]
DESCRIPTION: [what happened]
EXPECTED: [what should have happened]
ACTUAL: [what actually happened]
FILE: [which source file is involved]
LINE: [approximate line number]
REPRODUCTION: [steps to reproduce]
FIX SUGGESTION: [if you have one]
```
