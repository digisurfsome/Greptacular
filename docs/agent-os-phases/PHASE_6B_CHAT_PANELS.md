# Phase 6b: UI — Agent OS Chat & Auxiliary Panels

## Pre-Reading (Required)

Before building anything, read these files in order:
1. `docs/agent-os-phases/CONTEXT_PRIMER.md` — How everything connects
2. `AGENT_OS_PRD.md` — Focus on: UI Components section, Interactive PRD Creation Workflow
3. `docs/agent-os-phases/PHASE_5_ROUTER.md` — The WebSocket protocol you consume
4. `docs/agent-os-phases/PHASE_6A_INTAKE_DOCK.md` — The hooks and types you import
5. `ui/src/components/SpecCreationChat.tsx` — **CRITICAL.** The closest analog for the chat component. Study its WebSocket handling, message rendering, input area, and phase indicator.
6. `ui/src/hooks/useSpecChat.ts` — WebSocket hook pattern for chat sessions
7. `ui/src/components/ChatMessage.tsx` — Message rendering component (reuse this)
8. `ui/src/components/QuestionOptions.tsx` — Question rendering with options (reuse this)
9. `ui/src/components/TypingIndicator.tsx` — Loading indicator (reuse this)
10. `ui/src/components/DependencyGraph.tsx` — Graph component (reuse for feature dependencies)
11. `ui/src/components/FeatureCard.tsx` — Feature card pattern (reference for SpecCards)

---

## What You're Building

Five UI components + one WebSocket hook that implement the interactive Agent OS chat experience:

1. **AgentOSChat.tsx** — Main chat interface for the PRD creation workflow
2. **StandardsPanel.tsx** — Standards viewer/editor side panel
3. **ProductPanel.tsx** — Product layer viewer
4. **SpecCards.tsx** — Feature spec cards with status (draft/reviewed/approved)
5. **GapAnalysisPanel.tsx** — Gap display with severity and resolution

Plus:
6. **useAgentOSChat.ts** — WebSocket hook for the interactive session

---

## Dependencies

From Phase 6a:
```typescript
import {
  useStandards, useFeatures, useGaps, useStagedFiles, useHandoffStatus,
  agentOSKeys, type StagedFile, type ReadinessStatus, type FeatureCreate,
} from '@/hooks/useAgentOS'
```

Existing components to reuse:
```typescript
import { ChatMessage } from '@/components/ChatMessage'
import { QuestionOptions } from '@/components/QuestionOptions'
import { TypingIndicator } from '@/components/TypingIndicator'
```

From Phase 5 (WebSocket protocol):
- Client sends: `{"type": "message", "content": "..."}`, `{"type": "answer", ...}`, `{"type": "approve", ...}`
- Server sends: `{"type": "message", ...}`, `{"type": "question", ...}`, `{"type": "stage_change", ...}`, `{"type": "features", ...}`, `{"type": "gaps", ...}`, etc.

---

## Files to Create

### 1. `ui/src/hooks/useAgentOSChat.ts` (~120 lines)

WebSocket hook for the interactive Agent OS PRD creation session.

```typescript
/**
 * useAgentOSChat Hook
 *
 * Manages the WebSocket connection for the interactive Agent OS
 * PRD creation workflow. Handles all message types from the server
 * and provides send functions for client messages.
 */

import { useState, useEffect, useCallback, useRef } from 'react'
```

**Follow the `useSpecChat.ts` pattern exactly.** The key differences:

**State:**
```typescript
interface AgentOSChatState {
  messages: ChatMessage[]
  currentStage: string
  stageIndex: number
  totalStages: number
  currentQuestion: Question | null
  features: Feature[]
  gaps: Gap[]
  specPreview: { featureId: number; content: string } | null
  handoffStatus: HandoffStatus | null
  isConnected: boolean
  isThinking: boolean
}
```

**Types:**
```typescript
interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
}

interface Question {
  id: string
  question: string
  type: 'text' | 'choice' | 'multi_choice'
  options?: string[]
  purpose?: string
}

interface Feature {
  id: number
  name: string
  description: string
  priority: string
  complexity: string
  category: string
  dependencies: number[]
}

interface Gap {
  id: number
  type: string
  severity: string
  message: string
  recommendation: string
  confidence: number
  auto_fillable: boolean
  resolved: boolean
}

interface HandoffStatus {
  ready: boolean
  missing: string[]
  feature_count: number
  build_order: number[]
  estimated_sessions: number
}
```

**WebSocket connection:**
```typescript
const wsUrl = `ws://${window.location.host}/api/agent-os/ws/${projectName}`
```

**Message handlers (process server events):**
```typescript
const handleServerMessage = useCallback((event: MessageEvent) => {
  const data = JSON.parse(event.data)

  switch (data.type) {
    case 'message':
      // Append to messages
      break
    case 'question':
      // Set currentQuestion
      break
    case 'stage_change':
      // Update currentStage, stageIndex
      break
    case 'progress':
      // Update stage-specific progress
      break
    case 'features':
      // Update feature list
      break
    case 'gaps':
      // Update gap list
      break
    case 'spec_preview':
      // Set specPreview
      break
    case 'handoff_ready':
      // Set handoffStatus
      break
    case 'error':
      // Show error message
      break
  }
}, [])
```

**Send functions:**
```typescript
const sendMessage = useCallback((content: string) => {
  ws.current?.send(JSON.stringify({ type: 'message', content }))
}, [])

const sendAnswer = useCallback((questionId: string, answer: string) => {
  ws.current?.send(JSON.stringify({ type: 'answer', question_id: questionId, answer }))
}, [])

const sendApprove = useCallback((target: string) => {
  ws.current?.send(JSON.stringify({ type: 'approve', target }))
}, [])

const skipStage = useCallback(() => {
  ws.current?.send(JSON.stringify({ type: 'skip_stage' }))
}, [])
```

**Return type:**
```typescript
interface UseAgentOSChatReturn {
  // State
  messages: ChatMessage[]
  currentStage: string
  stageIndex: number
  totalStages: number
  currentQuestion: Question | null
  features: Feature[]
  gaps: Gap[]
  specPreview: { featureId: number; content: string } | null
  handoffStatus: HandoffStatus | null
  isConnected: boolean
  isThinking: boolean

  // Actions
  sendMessage: (content: string) => void
  sendAnswer: (questionId: string, answer: string) => void
  sendApprove: (target: string) => void
  skipStage: () => void
}
```

---

### 2. `ui/src/components/appbuilder/AgentOSChat.tsx` (~200 lines)

The main chat interface.

```typescript
/**
 * AgentOSChat Component
 *
 * Interactive chat interface for the Agent OS PRD creation workflow.
 * Shows the conversation, current stage indicator, questions, and
 * provides input for user responses.
 */
```

**Props:**
```typescript
interface AgentOSChatProps {
  projectName: string
  onComplete: () => void  // Called when handoff is ready
  onCancel: () => void
}
```

**Layout:**
```
┌───────────────────────────────────────────────────────────────┐
│  AGENT OS PRD CREATION                                        │
│  ──────────────────────────────────────────────────────────── │
│  Stage: [1]─[2]─[3]─[4]─[5]─[6]─[7]─[8]                    │
│         Intake → Standards → Product → Features → Gaps →      │
│         Specs → Database → Handoff                            │
│  Current: ████████░░░░░░░░░░ Product Discovery                │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  💬 Chat Messages Area (scrollable)                           │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ 🤖 Welcome! Tell me about what you want to build.       │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ 👤 I want to build a task management app with...        │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ 🤖 Great! Here's what I understand so far...            │ │
│  │    Now, in one sentence, what does this product do       │ │
│  │    for the user?                                        │ │
│  │                                                         │ │
│  │    [Text input for answer]                              │ │
│  │    — or —                                               │ │
│  │    [Option A] [Option B] [Option C]                     │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
├───────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Type your response...                          [Send ➤] │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  [Skip Stage →]                              [Cancel]        │
└───────────────────────────────────────────────────────────────┘
```

**Key behaviors:**

1. **Stage progress bar** — Shows all 8 stages as a horizontal stepper. Current stage is highlighted. Completed stages have a checkmark. Use the `stageIndex` from the hook.

2. **Message rendering** — Reuse `ChatMessage` component from the existing codebase. Agent messages and user messages alternate. Questions appear inline within agent messages.

3. **Question handling** — When `currentQuestion` is set:
   - For `type: "text"` — Show the text input (same as normal message input)
   - For `type: "choice"` — Show option buttons (reuse `QuestionOptions` component)
   - For `type: "multi_choice"` — Show checkboxes
   - When user answers, call `sendAnswer(questionId, answer)` and clear the question

4. **Feature review** — When `features` array is populated (during Stage 4), show a feature list card below the chat. Each feature shows name, priority badge, complexity badge. User can approve the list (`sendApprove('feature_list')`) or provide feedback.

5. **Gap display** — When `gaps` array is populated (during Stage 5), show gaps inline. Blocking gaps have a red border. User must resolve blocking gaps before proceeding.

6. **Spec preview** — When `specPreview` is set (during Stage 6), show the spec markdown in a collapsible panel below the chat.

7. **Handoff** — When `handoffStatus` is set and `ready: true`, show the build plan summary and a "Start Build" button that calls `onComplete`.

8. **Auto-scroll** — Chat area auto-scrolls to bottom on new messages. Use a ref + `scrollIntoView`.

**Styling:**
- Follow `SpecCreationChat.tsx` styling patterns exactly
- Stage progress bar: use colored segments (completed = `bg-neo-done`, current = `bg-neo-progress`, pending = `bg-gray-200`)
- Message area: scrollable with `overflow-y-auto max-h-[60vh]`

---

### 3. `ui/src/components/appbuilder/StandardsPanel.tsx` (~150 lines)

Side panel showing current standards.

```typescript
/**
 * StandardsPanel Component
 *
 * Collapsible side panel showing the project's coding standards.
 * Allows viewing and editing standards files.
 */
```

**Props:**
```typescript
interface StandardsPanelProps {
  projectName: string
  isOpen: boolean
  onToggle: () => void
}
```

**Content:**
- Lists all 6 standards files
- Each file is an accordion item (click to expand/collapse)
- Expanded view shows the markdown content rendered as text
- Edit button switches to a textarea for editing
- Save button calls `useAgentOS` mutation to update the file
- Uses `useStandards(projectName)` hook

**Layout:**
```
┌─────────────────────────────┐
│  STANDARDS          [Close] │
├─────────────────────────────┤
│ ▼ Technology Stack          │
│   Languages: TypeScript     │
│   Frontend: React           │
│   Backend: FastAPI          │
│   Database: SQLite          │
│                    [Edit]   │
├─────────────────────────────┤
│ ▶ Coding Conventions        │
├─────────────────────────────┤
│ ▶ Architecture Patterns     │
├─────────────────────────────┤
│ ▶ UI/UX Standards           │
├─────────────────────────────┤
│ ▶ Quality Standards         │
├─────────────────────────────┤
│ ▶ Security Requirements     │
└─────────────────────────────┘
```

---

### 4. `ui/src/components/appbuilder/ProductPanel.tsx` (~100 lines)

Product layer viewer.

**Props:**
```typescript
interface ProductPanelProps {
  projectName: string
  isOpen: boolean
  onToggle: () => void
}
```

Same accordion pattern as StandardsPanel but for product files (vision, target-users, use-cases, roadmap, constraints, competitive-context). Read-only display (product files are generated by the workflow, not manually edited).

---

### 5. `ui/src/components/appbuilder/SpecCards.tsx` (~150 lines)

Feature spec cards showing status.

**Props:**
```typescript
interface SpecCardsProps {
  projectName: string
  features: Feature[]
  onReviewSpec: (featureId: number) => void
}
```

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  FEATURE SPECS                                               │
├────────────┬────────────┬────────────┬────────────┬─────────┤
│  #1 Auth   │  #2 Dash   │  #3 API    │  #4 Tests  │  ...    │
│  ━━━━━━━━  │  ━━━━━━━━  │  ━━━━━━━━  │  ━━━━━━━━  │         │
│  MVP       │  MVP       │  v1.1      │  v1.1      │         │
│  Medium    │  Large     │  Small     │  Small     │         │
│            │            │            │            │         │
│  [Draft]   │ [Approved] │ [Pending]  │ [Pending]  │         │
│  [Review→] │  ✅        │            │            │         │
└────────────┴────────────┴────────────┴────────────┴─────────┘
```

Each card shows:
- Feature ID + name
- Priority badge (MVP = green, v1.1 = blue, Future = gray)
- Complexity badge (small = green, medium = amber, large = red)
- Status: pending (gray), draft (yellow), reviewed (blue), approved (green)
- "Review" button that calls `onReviewSpec(featureId)` which opens the spec preview in the chat

Grid layout: `grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3`

---

### 6. `ui/src/components/appbuilder/GapAnalysisPanel.tsx` (~100 lines)

Gap display panel.

**Props:**
```typescript
interface GapAnalysisPanelProps {
  projectName: string
  gaps: Gap[]
  onResolveGap: (gapId: number, resolution: string) => void
  onAutoResolve: () => void
}
```

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  GAP ANALYSIS                    [Auto-Resolve High Conf →] │
├─────────────────────────────────────────────────────────────┤
│  🔴 BLOCKING (must resolve)                                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Gap #1: Auth feature references 'social login' but   │  │
│  │  doesn't specify which providers                      │  │
│  │  Recommendation: Use Google + GitHub (87% confidence)  │  │
│  │  [Accept Recommendation] [Provide Custom Resolution]   │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  🟡 IMPORTANT                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Gap #3: No performance requirements defined           │  │
│  │  Recommendation: Set 200ms API response target (72%)   │  │
│  │  [Accept] [Custom] [Skip]                              │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ✅ RESOLVED (2)                                            │
│  └ Gap #2: Missing database choice → PostgreSQL (accepted)  │
│  └ Gap #4: Unstated auth dependency → Added to feature #1   │
└─────────────────────────────────────────────────────────────┘
```

Features:
- Grouped by severity (blocking → important → minor → resolved)
- Each gap shows message, recommendation, confidence percentage
- "Accept Recommendation" button resolves with the recommendation text
- "Provide Custom Resolution" opens a text input
- Auto-resolve button calls `onAutoResolve` to resolve all high-confidence gaps at once
- Resolved gaps collapsed at the bottom with a count

---

## Integration Points

These components need to be wired into an Agent OS page layout. The parent component (which may already exist or needs to be created depending on the app builder page structure) should:

1. Show `IntakeDock` first (from Phase 6a)
2. When intake is processed, transition to `AgentOSChat` + side panels
3. Side panels (`StandardsPanel`, `ProductPanel`, `SpecCards`, `GapAnalysisPanel`) are shown/hidden based on the current stage

**Suggested parent layout:**

```typescript
// In the app builder page, the Agent OS section would look like:
function AgentOSWorkflow({ projectName }: { projectName: string }) {
  const [phase, setPhase] = useState<'intake' | 'workflow' | 'complete'>('intake')

  if (phase === 'intake') {
    return (
      <IntakeDock
        projectName={projectName}
        onProcessComplete={() => setPhase('workflow')}
        onSkip={() => setPhase('workflow')}
      />
    )
  }

  if (phase === 'workflow') {
    return (
      <div className="flex gap-4">
        {/* Main chat area */}
        <div className="flex-1">
          <AgentOSChat
            projectName={projectName}
            onComplete={() => setPhase('complete')}
            onCancel={() => setPhase('intake')}
          />
        </div>
        {/* Side panels */}
        <div className="w-80 space-y-4">
          <StandardsPanel projectName={projectName} />
          <ProductPanel projectName={projectName} />
          <SpecCards projectName={projectName} features={[]} onReviewSpec={() => {}} />
          <GapAnalysisPanel projectName={projectName} gaps={[]} onResolveGap={() => {}} onAutoResolve={() => {}} />
        </div>
      </div>
    )
  }

  return <div>Build plan ready! Start the agent.</div>
}
```

---

## Completion Criteria

Phase 6b is DONE when:
- [ ] `ui/src/hooks/useAgentOSChat.ts` exists with WebSocket connection and all handlers
- [ ] `ui/src/components/appbuilder/AgentOSChat.tsx` exists and renders the chat + stage indicator
- [ ] `ui/src/components/appbuilder/StandardsPanel.tsx` exists with accordion view + edit
- [ ] `ui/src/components/appbuilder/ProductPanel.tsx` exists with accordion view
- [ ] `ui/src/components/appbuilder/SpecCards.tsx` exists with card grid
- [ ] `ui/src/components/appbuilder/GapAnalysisPanel.tsx` exists with severity groups + resolution
- [ ] WebSocket connects and receives stage_change events
- [ ] Chat messages render correctly with auto-scroll
- [ ] Question options render for choice/multi_choice types
- [ ] All components pass `npm run lint` and `npm run build`
- [ ] Components follow neobrutalism design tokens from `globals.css`

---

*End of Phase 6b PRD.*
