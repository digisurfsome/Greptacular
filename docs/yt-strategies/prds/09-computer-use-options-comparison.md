# PRD: Computer-Use Agent Options & Integration Strategy

## Overview
This document compares all available computer-use agent options and recommends the best path forward for integrating autonomous browser control into the YT Strategy Lab.

## Option Comparison Matrix

| Feature | Custom (API) | Claude Desktop | Chrome Extension | Browser Use (OSS) |
|---------|-------------|---------------|-----------------|-------------------|
| **Embeddable in our app (iframe)** | YES (noVNC) | NO | NO | YES (Playwright) |
| **Full programmatic control** | YES | NO | LIMITED | YES |
| **Pause/Resume/Inject** | YES (we build it) | NO | NO | YES |
| **Model selection** | ANY Claude model | Limited | Limited | Any LLM |
| **Screen recording** | YES (ffmpeg) | NO | NO | YES |
| **No extra cost beyond API** | YES | Needs Max sub | Needs Pro+ sub | FREE (OSS) |
| **Setup complexity** | HIGH (Docker) | LOW (install app) | LOW (install ext) | MEDIUM (Python) |
| **Reliability** | HIGH (controlled env) | HIGH | MEDIUM | MEDIUM |
| **Speed** | FAST (dedicated) | FAST | FAST | VARIES |
| **SaaS-deployable** | YES | NO | NO | YES |

## Recommendation: Custom Computer Use API (Primary) + Chrome Extension (Fallback)

### Why Custom API is Best
1. **Embeddable**: noVNC gives us a live iframe view - the split-screen layout we designed
2. **Full control**: We control the agent loop, can pause/resume/inject
3. **Screen capture**: ffmpeg captures screenshots and video clips from the virtual display
4. **Model flexibility**: Use Opus for complex steps, Sonnet for medium, Haiku for simple
5. **SaaS-ready**: Docker container can be deployed to cloud for multi-user SaaS
6. **Subscription piping**: Use AutoForge's existing subscription model, not separate API keys

### Why Chrome Extension as Fallback
1. **Zero setup** for personal use - just install the extension
2. **Uses your existing browser sessions** (already logged into Facebook, Instagram, etc.)
3. **No Docker needed** for basic use cases
4. **Good for demos** and quick tests

### Integration Architecture

```
┌──────────────────────────────────────────────┐
│           YT Strategy Lab UI                  │
│                                               │
│  Step Builder → "Run Step" Button             │
│         │                                     │
│         ▼                                     │
│  ┌─────────────────────────────────────┐     │
│  │     Execution Engine Selector       │     │
│  │                                     │     │
│  │  ○ Custom Agent (Docker + noVNC)    │     │
│  │    - Full iframe view               │     │
│  │    - Screen recording               │     │
│  │    - Pause/resume/chat              │     │
│  │    - Recommended for workflows      │     │
│  │                                     │     │
│  │  ○ Chrome Extension                 │     │
│  │    - Uses your browser directly     │     │
│  │    - No Docker needed               │     │
│  │    - Quick & easy                   │     │
│  │    - Good for single steps          │     │
│  │                                     │     │
│  │  ○ Manual (Copy prompt)             │     │
│  │    - Copy prompt to clipboard       │     │
│  │    - Paste into any AI tool         │     │
│  │    - Paste output back              │     │
│  └─────────────────────────────────────┘     │
└──────────────────────────────────────────────┘
```

## Custom Computer Use Agent - Detailed Spec

### Docker Container Setup
```dockerfile
FROM anthropic/computer-use-reference:latest

# Pre-install common tools
RUN apt-get update && apt-get install -y \
    chromium-browser \
    ffmpeg \
    xdotool \
    novnc \
    websockify

# Expose ports
EXPOSE 5900  # VNC
EXPOSE 6080  # noVNC WebSocket
EXPOSE 8080  # Control API

# Start services
CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]
```

### Agent Loop (Python)
```python
import anthropic

class ComputerUseAgent:
    def __init__(self, model: str = "claude-opus-4-6"):
        self.client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY from env
        self.model = model
        self.messages = []
        self.paused = False
        self.tools = [
            {
                "type": "computer_20250124",
                "name": "computer",
                "display_width_px": 1920,
                "display_height_px": 1080,
                "display_number": 0,
            },
            {
                "type": "text_editor_20250124",
                "name": "str_replace_editor",
            },
            {
                "type": "bash_20250124",
                "name": "bash",
            }
        ]

    async def execute_step(self, step_prompt: str, context: str = ""):
        """Execute a single step using computer use."""
        full_prompt = f"{context}\n\n{step_prompt}" if context else step_prompt

        self.messages.append({
            "role": "user",
            "content": full_prompt
        })

        while True:
            # Check for pause
            if self.paused:
                await self._wait_for_resume()

            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                tools=self.tools,
                messages=self.messages,
            )

            # Process response
            self.messages.append({
                "role": "assistant",
                "content": response.content,
            })

            # Check if done (no more tool calls)
            if response.stop_reason == "end_turn":
                return self._extract_text_output(response)

            # Execute tool calls
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = await self._execute_tool(block)
                    tool_results.append(result)

            self.messages.append({
                "role": "user",
                "content": tool_results,
            })

    async def inject_message(self, message: str):
        """Inject a human message into the conversation."""
        self.messages.append({
            "role": "user",
            "content": f"[HUMAN MESSAGE]: {message}"
        })

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False
```

### Subscription Integration
The agent uses the ANTHROPIC_API_KEY that's already configured in AutoForge:
- For **personal use**: Direct API key in `.env`
- For **subscription mode**: AutoForge proxies the request through its subscription system
- No additional API key management needed
- Model selection per step: Opus for complex, Sonnet for medium, Haiku for simple

### Opus 4.6 as Default for Computer Use
The computer-use agent should default to **Opus 4.6** because:
- Computer use requires strong visual understanding
- Complex multi-step workflows need deep reasoning
- Navigation decisions require judgment
- Opus has the best performance on computer use benchmarks

Sonnet can be used for simpler steps (data gathering, basic navigation).
Haiku should NOT be used for computer use (insufficient reasoning for screen interaction).

## Chrome Extension Integration

For users who don't want Docker, offer a "lite" mode:
1. Step prompt is displayed with a "Copy to Clipboard" button
2. User pastes into Claude Chrome extension
3. Extension executes the step in their browser
4. User pastes the output back into the step's "AI Output" field

This is manual but requires zero infrastructure setup.

## Environment Variables
```bash
# Computer Use Engine (Custom)
COMPUTER_USE_ENABLED=true
COMPUTER_USE_DOCKER_IMAGE=anthropic/computer-use-reference:latest
COMPUTER_USE_DISPLAY_WIDTH=1920
COMPUTER_USE_DISPLAY_HEIGHT=1080
COMPUTER_USE_NOVNC_PORT=6080
COMPUTER_USE_DEFAULT_MODEL=claude-opus-4-6

# Anthropic API (already in AutoForge)
ANTHROPIC_API_KEY=sk-ant-...

# Optional: Chrome Extension mode
CHROME_EXTENSION_MODE=false
```

## Build Phases
1. **Phase 1**: Manual mode (copy prompt, paste output) - already works
2. **Phase 2**: Custom Computer Use API agent (single step execution)
3. **Phase 3**: noVNC iframe integration (live view)
4. **Phase 4**: Multi-step sequential execution
5. **Phase 5**: Pause/resume/inject
6. **Phase 6**: Screen recording + captures
7. **Phase 7**: Chrome Extension integration as alternative

## Success Criteria
- Custom agent can execute a step end-to-end via API
- noVNC iframe shows live browser view embedded in our app
- User can choose between Custom Agent, Chrome Extension, or Manual mode
- Opus 4.6 handles complex steps reliably
- Subscription-based access works (no extra API key setup)
