# PRD: Live Execution Viewer (Split-Screen Browser iframe)

## Overview
When the computer-use agent is executing steps, the UI transitions to a split-screen layout where the majority of the screen shows a live browser view (iframe) of what the agent is doing, while a sidebar and top bar show task status, agent logs, and controls.

## Layout Specification

### Screen Dimensions Strategy
To maintain correct browser aspect ratios, we take equal proportional margins from the left and top:
- Left sidebar: 280px
- Top bar: 48px
- The remaining space maintains the actual screen resolution aspect ratio

```
┌─────── 280px ──────┬── remaining width ──────────────┐
│  TOP BAR (48px)     │  TOP BAR (48px)                 │ 48px
│  Project: AI Agency │  [Chat input...] [Pause][Stop]  │
├─────────────────────┼────────────────────────────────┤
│                     │                                │
│  STEP TRACKER       │                                │
│                     │                                │
│  1. ✓ Brand Guide   │     LIVE BROWSER VIEW          │
│  2. ✓ Research      │     (noVNC iframe)             │
│  3. ● Store Page    │                                │
│  4. ○ Create Ads    │     Real-time view of agent    │
│  5. ○ Deploy Ads    │     controlling Chromium       │
│  6. ○ Lead List     │                                │
│  7. ○ Outreach      │                                │
│                     │                                │
│  ─────────────────  │                                │
│                     │                                │
│  AGENT LOG          │                                │
│  (scrolling)        │                                │
│                     │                                │
│  12:03 Navigating   │                                │
│  to Meta Ad Library │                                │
│  12:04 Searching    │                                │
│  "Honda dealer KC"  │                                │
│  12:04 Found 12 ads │                                │
│  12:05 Extracting   │                                │
│  ad creative data   │                                │
│                     │                                │
└─────────────────────┴────────────────────────────────┘
```

### Top Bar Components
- **Left section**: Project name, current step name, step X of Y
- **Center section**: Chat input (send messages to agent while it works)
- **Right section**: Model indicator (Opus/Sonnet/Haiku), Pause button, Resume button, Stop button, Take Over button

### Left Sidebar (280px, split vertically)
**Top half - Step Tracker:**
- Numbered list of all steps
- Status indicators: ✓ (done, green), ● (active, cyan/blue pulse), ○ (pending, gray)
- Active step highlighted with accent border
- Click a step to see its details in a tooltip/popover
- Progress bar at the top showing overall completion

**Bottom half - Agent Log:**
- Real-time scrolling log of what the agent is doing
- Timestamped entries
- Color-coded: actions (blue), thinking (gray), errors (red), success (green)
- Auto-scrolls to bottom, but user can scroll up to review
- Each log entry is a short description: "Navigating to Meta Ad Library", "Typing search query: Honda dealer Kansas City", "Found 12 active ads", etc.

### Browser Iframe (main area)
- noVNC WebSocket connection embedded in an iframe
- Renders the virtual display from the Docker container
- By default: view-only (user watches, agent controls)
- In "Take Over" mode: interactive (user can click/type)
- Maintains aspect ratio of the configured display resolution
- Black letterboxing if aspect ratio doesn't match available space

## Responsive Behavior

### Desktop (>1200px)
Full layout as described above.

### Tablet (768-1200px)
- Sidebar collapses to icons only (step numbers + status dots)
- Agent log moves to a slide-out drawer
- Top bar condensed

### Mobile (<768px)
- Browser view takes full screen
- Step tracker and log accessible via overlay/drawer
- Controls float at bottom

## Technical Implementation

### noVNC Integration
```typescript
// Connect to noVNC WebSocket
const vnc = new RFB(
  document.getElementById('vnc-container'),
  `ws://localhost:${NOVNC_PORT}/websockify`,
  {
    credentials: { password: '' },
    scaleViewport: true,
    resizeSession: false,
    showDotCursor: true,
  }
)

// View-only by default
vnc.viewOnly = true

// Enable interaction in takeover mode
function enableTakeover() {
  vnc.viewOnly = false
}
```

### Agent Log WebSocket
```typescript
// Real-time log streaming
const ws = new WebSocket(`ws://localhost:${PORT}/ws/execution/${sessionId}`)

ws.onmessage = (event) => {
  const data = JSON.parse(event.data)
  switch (data.type) {
    case 'agent_action':
      // Mouse click, keyboard input, screenshot taken
      addLogEntry({ text: data.description, type: 'action', timestamp: data.ts })
      break
    case 'agent_thinking':
      // What the agent is reasoning about
      addLogEntry({ text: data.content, type: 'thinking', timestamp: data.ts })
      break
    case 'step_complete':
      // Step finished, advance tracker
      updateStepStatus(data.stepId, 'complete')
      break
    case 'screenshot':
      // Screenshot captured, store for later
      addScreenshot(data.stepId, data.imageUrl)
      break
    case 'error':
      addLogEntry({ text: data.message, type: 'error', timestamp: data.ts })
      break
  }
}
```

### Chat Input (Talk to Agent)
```typescript
// Send message to agent during execution
async function sendAgentMessage(message: string) {
  await fetch(`/api/execution/${sessionId}/inject`, {
    method: 'POST',
    body: JSON.stringify({ message }),
  })
  // The execution engine injects this into the next agent turn
}
```

## Component Files
- `ui/src/components/yt-lab/ExecutionViewer.tsx` - Main split-screen component
- `ui/src/components/yt-lab/StepTracker.tsx` - Left sidebar step list
- `ui/src/components/yt-lab/AgentLog.tsx` - Real-time log panel
- `ui/src/components/yt-lab/ExecutionControls.tsx` - Top bar with chat + buttons
- `ui/src/components/yt-lab/BrowserView.tsx` - noVNC iframe wrapper

## Dependencies
- `@nicedoc/noVNC` or raw noVNC JS (for browser embedding)
- WebSocket connection to execution engine
- Docker container with noVNC server running

## Success Criteria
- User can watch the agent navigate websites in real-time
- Step tracker updates as steps complete
- Agent log shows clear, readable descriptions of actions
- Chat messages are delivered to the agent and it responds
- Pause/resume transitions are smooth (no broken state)
- Take Over mode works (user can interact, then return control)
- Layout is responsive and works in dark mode
- No noticeable lag between agent action and iframe display
