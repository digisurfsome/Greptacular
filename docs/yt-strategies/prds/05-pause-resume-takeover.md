# PRD: Pause, Resume, Human Takeover & Agent Chat

## Overview
Full human-in-the-loop control system for the computer-use execution engine. Users can pause the agent, chat with it, take over the browser manually, and resume - all without losing context or breaking the workflow.

## Feature Set

### 1. Pause / Resume
**Pause:**
- User clicks Pause button in top bar
- Agent finishes current tool call (doesn't interrupt mid-click)
- Screenshot taken of current browser state
- Current URL, step, and progress captured
- Agent state serialized to memory/disk
- UI shows "Paused" indicator with pulsing border
- noVNC stays connected (user can see the frozen screen)

**Resume:**
- User clicks Resume button
- System sends context to agent: screenshot + "You were working on [step]. You were at [URL]. Here's what you've done so far: [summary]. Continue where you left off."
- Agent resumes naturally
- "Paused" indicator clears

### 2. Agent Chat (Mid-Execution Communication)
Chat input in the top bar allows real-time communication with the agent while it's working.

**Use cases:**
- "Hey, skip this step and move to step 5"
- "The login page popped up - my username is X"
- "Focus on the top 5 results only, don't be too thorough"
- "Can you also grab the pricing info while you're on that page?"
- "That looks wrong - try a different search term"

**Implementation:**
- Messages queue and inject at the next natural pause point (between tool calls)
- Agent receives: "USER MESSAGE: {message}" as an additional context injection
- Agent responds in the agent log (not a separate chat - same stream)
- Message appears in log with "YOU:" prefix, agent response with "AGENT:" prefix

### 3. Human Takeover Mode
The user temporarily takes direct control of the browser.

**Flow:**
1. User clicks "Take Over" button
2. Agent pauses (same as pause flow)
3. noVNC switches from view-only to interactive
4. User can: navigate, click, type, research, fill forms, etc.
5. Top bar shows "YOU ARE IN CONTROL" indicator
6. When done, user clicks "Return Control to Agent"
7. Screenshot taken of current state
8. Agent receives: "I took over and navigated to [current_url]. [Optional user note about what they did]. Continue from here."
9. Agent resumes from the new state

**Why this matters:**
- Sometimes the user spots something interesting and wants to explore
- Login/auth pages that the agent shouldn't handle
- Quick manual fixes (typo correction, selecting the right option)
- Research that requires human judgment before the agent continues

### 4. Step Skip / Jump
User can tell the agent to skip to a different step:
- Click on any step in the step tracker
- "Jump to this step" option
- Agent wraps up current state and starts the new step
- Previous step marked as "skipped" (not complete)

## State Machine

```
                    ┌──────────┐
                    │  IDLE    │
                    └────┬─────┘
                         │ Start
                         ▼
                    ┌──────────┐
            ┌──────│ RUNNING  │──────┐
            │      └──────────┘      │
            │ Pause      │           │ Complete
            ▼            │ Inject    ▼
       ┌──────────┐      │     ┌──────────┐
       │ PAUSED   │      │     │ COMPLETE │
       └────┬─────┘      │     └──────────┘
            │             │
            │ Take Over   │
            ▼             │
       ┌──────────┐      │
       │ TAKEOVER │──────┘
       └────┬─────┘  Return Control
            │
            │ Resume
            ▼
       ┌──────────┐
       │ RUNNING  │
       └──────────┘
```

## API Endpoints

```
POST   /api/execution/{session_id}/pause
POST   /api/execution/{session_id}/resume
POST   /api/execution/{session_id}/inject    Body: { "message": "..." }
POST   /api/execution/{session_id}/takeover  Body: { "enable": true/false }
POST   /api/execution/{session_id}/jump      Body: { "step_id": "..." }
GET    /api/execution/{session_id}/state     Returns full state snapshot
WS     /ws/execution/{session_id}            Real-time status stream
```

## WebSocket Events

```typescript
type ExecutionEvent =
  | { type: 'status_change'; status: 'running' | 'paused' | 'takeover' | 'complete' }
  | { type: 'agent_action'; description: string; timestamp: string }
  | { type: 'agent_thinking'; content: string; timestamp: string }
  | { type: 'step_change'; stepId: string; status: string }
  | { type: 'screenshot'; stepId: string; imageUrl: string }
  | { type: 'user_message'; content: string; timestamp: string }
  | { type: 'agent_response'; content: string; timestamp: string }
  | { type: 'error'; message: string; timestamp: string }
```

## UI Components

### Execution Controls Bar (top bar)
```tsx
<div className="flex items-center h-12 px-4 border-b border-border bg-card">
  {/* Left: Project + Step info */}
  <div className="flex items-center gap-2">
    <span className="text-sm font-semibold">{project.name}</span>
    <ChevronRight size={12} />
    <span className="text-xs text-muted-foreground">Step {currentStep} of {totalSteps}</span>
    <StatusBadge status={executionStatus} />
  </div>

  {/* Center: Chat input */}
  <div className="flex-1 mx-4">
    <Input
      placeholder="Talk to the agent..."
      value={chatMessage}
      onChange={setChatMessage}
      onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
      disabled={status === 'complete'}
    />
  </div>

  {/* Right: Controls */}
  <div className="flex items-center gap-2">
    <ModelIndicator model={currentModel} />
    {status === 'running' && (
      <Button variant="outline" size="sm" onClick={pause}>
        <Pause size={14} /> Pause
      </Button>
    )}
    {status === 'paused' && (
      <>
        <Button size="sm" onClick={resume}>
          <Play size={14} /> Resume
        </Button>
        <Button variant="outline" size="sm" onClick={enableTakeover}>
          <Hand size={14} /> Take Over
        </Button>
      </>
    )}
    {status === 'takeover' && (
      <Button size="sm" className="bg-amber-500" onClick={returnControl}>
        <RotateCcw size={14} /> Return Control
      </Button>
    )}
    <Button variant="destructive" size="sm" onClick={stop}>
      <Square size={14} /> Stop
    </Button>
  </div>
</div>
```

## Success Criteria
- Pause/resume preserves full agent context (no "where was I?" moments)
- Chat messages are delivered within 1-2 seconds
- Agent acknowledges chat messages in its response
- Human takeover gives full browser control with zero lag
- Return-to-agent transition is smooth (agent picks up correctly)
- All state transitions are logged in the agent log
- No data loss on any state transition
- Works in both dark and light modes
