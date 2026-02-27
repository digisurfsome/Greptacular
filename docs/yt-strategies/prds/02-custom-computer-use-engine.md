# PRD: Custom Computer Use Execution Engine

## Overview
Build a custom computer-use system using Anthropic's Computer Use API that can autonomously execute the strategy steps defined in the YT Strategy Lab. This gives us maximum flexibility - full control over the browser view, iframe embedding, pause/resume, and human-in-the-loop interaction.

## Why Build Our Own (vs Chrome Extension / Desktop)
- **Claude in Chrome**: Can't embed in an iframe, can't programmatically control execution, limited to Chrome extension APIs
- **Claude Desktop / Cowork**: Runs in its own VM, can't embed the view into our app
- **Custom via API**: Full control. We run the Docker container, expose the display via noVNC, embed it in our app, and control the agent loop programmatically

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────┐
│                  YT Strategy Lab UI                  │
│                                                      │
│  ┌──────────┐  ┌──────────────────┐  ┌────────────┐ │
│  │ Step List │  │  Browser Iframe  │  │ Agent Log  │ │
│  │ & Status  │  │  (noVNC stream)  │  │ & Chat     │ │
│  └──────────┘  └──────────────────┘  └────────────┘ │
│       ↕              ↕                     ↕         │
│  ┌──────────────────────────────────────────────────┐│
│  │         Execution Engine API (FastAPI)            ││
│  │  /api/execution/start                            ││
│  │  /api/execution/pause                            ││
│  │  /api/execution/resume                           ││
│  │  /api/execution/inject-message                   ││
│  │  /ws/execution/{session_id}                      ││
│  └──────────────────────────────────────────────────┘│
│       ↕                                              │
│  ┌──────────────────────────────────────────────────┐│
│  │         Computer Use Container (Docker)           ││
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐ ││
│  │  │ Xvfb       │  │ Chromium   │  │ noVNC      │ ││
│  │  │ (display)  │  │ (browser)  │  │ (stream)   │ ││
│  │  └────────────┘  └────────────┘  └────────────┘ ││
│  │       ↕                                          ││
│  │  ┌────────────────────────────────────────────┐  ││
│  │  │ Claude API (computer_use_20250124 tool)    │  ││
│  │  │ + text_editor + bash tools                 │  ││
│  │  └────────────────────────────────────────────┘  ││
│  └──────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

### Agent Loop
```python
# Simplified execution flow
for step in project.steps:
    # 1. Build context from previous steps + brand docs + strategy
    context = build_step_context(step, previous_outputs)

    # 2. Send to Claude with computer_use tool
    response = client.messages.create(
        model=selected_model,  # opus-4-6, sonnet-4-6, etc.
        tools=[
            {"type": "computer_20250124", "name": "computer", ...},
            {"type": "text_editor_20250124", "name": "str_replace_editor"},
            {"type": "bash_20250124", "name": "bash"},
        ],
        messages=[{"role": "user", "content": step.prompt}]
    )

    # 3. Execute tool calls (screenshot, click, type, etc.)
    # 4. Stream actions to frontend via WebSocket
    # 5. Check for pause/inject signals
    # 6. Capture output, store in step.aiOutput
    # 7. Take completion screenshot
    # 8. Mark step complete, advance to next
```

### Model Selection Strategy
- **Opus 4.6**: Complex reasoning steps (strategy creation, competitive analysis, ad copy)
- **Sonnet 4.6**: Medium complexity (form filling, data extraction, navigation)
- **Haiku 4.5**: Simple tasks (copy/paste, basic data gathering, screenshot analysis)
- Default model set per step in the strategy builder
- Subscription-based access piped through AutoForge (not raw API keys)

## Technical Requirements

### Docker Container
- Based on Anthropic's reference implementation
- Xvfb virtual display (1920x1080)
- Chromium browser pre-installed
- noVNC server exposing display on a WebSocket port
- Accessible from our FastAPI server

### Backend (server/services/computer_use_engine.py)
```python
class ComputerUseEngine:
    """Manages computer-use agent execution sessions."""

    async def start_session(self, project_id: str, step_ids: list[str]) -> str:
        """Start a new execution session. Returns session_id."""

    async def pause_session(self, session_id: str) -> None:
        """Pause execution. Takes screenshot of current state."""

    async def resume_session(self, session_id: str) -> None:
        """Resume from where we paused."""

    async def inject_message(self, session_id: str, message: str) -> None:
        """Send a human message to the agent mid-execution."""

    async def stop_session(self, session_id: str) -> None:
        """Stop execution entirely."""

    async def get_session_status(self, session_id: str) -> SessionStatus:
        """Get current status, step progress, screenshots."""
```

### Frontend Components

#### ExecutionView (the split-screen layout)
```
┌────────────────────┬────────────────────────────────┐
│  PROJECT INFO      │  AGENT CHAT / STATUS BAR       │
│  Step 3 of 7       │  [Chat input] [Pause] [Stop]   │
│  "Research Ads"    │  Model: Opus 4.6               │
├────────────────────┼────────────────────────────────┤
│                    │                                │
│  STEP STATUS       │                                │
│  ✓ Brand Guide     │     BROWSER IFRAME             │
│  ✓ Research        │     (noVNC WebSocket)           │
│  ● Store Page      │                                │
│  ○ Create Ads      │     Live view of what agent    │
│  ○ Deploy Ads      │     is doing in Chromium       │
│  ○ Lead List       │                                │
│  ○ Outreach        │                                │
│                    │                                │
│  AGENT LOG         │                                │
│  > Opening Meta    │                                │
│    Ad Library...   │                                │
│  > Searching for   │                                │
│    "Honda dealer"  │                                │
│  > Found 12 ads    │                                │
│  > Extracting...   │                                │
│                    │                                │
└────────────────────┴────────────────────────────────┘
```

Layout rules:
- Left sidebar: ~280px (same as strategy builder sidebar)
- Top bar: ~48px (project info + chat input + controls)
- Main area: remaining space = browser iframe
- The iframe maintains correct aspect ratio by taking equal margin from left and top, preserving screen dimensions
- Sidebar split: top half = step list with status, bottom half = real-time agent log

#### Controls
- **Pause button**: Stops agent loop, takes screenshot of current state, stores in memory
- **Resume button**: Sends screenshot + "continue from where you left off" to agent
- **Chat input**: Sends message to agent as an injection between tool calls
- **Stop button**: Kills the session entirely
- **Take Over mode**: Pauses agent, user interacts with browser directly via noVNC, then resumes

### Pause/Resume Logic
```
User clicks Pause →
  1. Set session.paused = true
  2. Wait for current tool call to complete (don't interrupt mid-action)
  3. Take screenshot of current browser state
  4. Store: current_step, current_url, screenshot, agent_messages so far
  5. Display "Paused" indicator on UI

User clicks Resume →
  1. Send screenshot + context: "You were working on {step}. You were at {url}. Continue."
  2. Set session.paused = false
  3. Agent continues from where it left off
```

### Human Takeover Mode
```
User clicks "Take Over" →
  1. Pause agent (same as above)
  2. Enable interactive noVNC (keyboard/mouse input enabled in iframe)
  3. User can browse, research, navigate freely
  4. When done, user clicks "Return Control"
  5. Take screenshot of current state
  6. Resume agent with new context: "I manually navigated to {url}. Continue from here."
```

## Environment Variables
```
# Computer Use Engine
COMPUTER_USE_ENABLED=true
COMPUTER_USE_DISPLAY_WIDTH=1920
COMPUTER_USE_DISPLAY_HEIGHT=1080
COMPUTER_USE_NOVNC_PORT=6080
COMPUTER_USE_CONTAINER_IMAGE=anthropic/computer-use-reference:latest

# Model Access (subscription-based via AutoForge)
# Uses existing ANTHROPIC_API_KEY or subscription piped through AutoForge
# No separate API key needed
```

## Roles & System Prompts
Each step can have an attached "role" that shapes the agent's behavior:
- **Researcher**: Focus on data gathering, be thorough, document everything
- **Marketer**: Think about conversion, urgency, compelling copy
- **Designer**: Focus on visual quality, brand consistency
- **Analyst**: Extract patterns, create frameworks, think strategically
- **Outreach Specialist**: Personalize messages, be professional but warm

Roles are defined in the existing Role Library (`/#/roles`) and can be attached to steps in the strategy builder.

## Success Criteria
- Agent can execute a 7-step workflow end-to-end without human intervention
- User can watch the agent work in real-time via the embedded browser view
- Pause/resume works cleanly without losing context
- Human can inject messages and the agent responds appropriately
- Screenshots are captured at each step transition
- Step results are stored back into the project
- Subscription-based model access works (no raw API keys for the agent itself)

## Dependencies
- Docker (for running the computer-use container)
- Anthropic API with computer_use tool support
- noVNC (for WebSocket-based browser streaming)
- Existing AutoForge subscription/model piping
- Existing Role Library for role attachments

## Estimated Build Phases
1. **Phase 1**: Basic execution engine (single step, no iframe) - run step prompt through computer_use API
2. **Phase 2**: Docker + noVNC integration (iframe live view)
3. **Phase 3**: Multi-step execution with context passing
4. **Phase 4**: Pause/resume/inject functionality
5. **Phase 5**: Human takeover mode
6. **Phase 6**: Role attachments and model selection per step
