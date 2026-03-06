# DUNKSTACK.md — Context Override

> When working in this app, THIS file takes priority over root CLAUDE.md.
> Only reference root CLAUDE.md for shared infrastructure (build, server, design tokens).

## Identity

DunkStack is a file-based context management workspace. It provides real-time token tracking with color-coded zones, a 3-tier safety system (warning / handoff / hard stop), file-based walkie-talkie chat via `.agent/comms/` files, and session control modes (idle / continue / autopilot). It also integrates an Agent OS workflow for app building with intake, standards, gap analysis, and spec cards.

## Route

`/#/dunkstack` — Full-page layout

## Components

### Page
- `ui/src/pages/DunkStackPage.tsx` — Main page with model presets, panel management, Agent OS integration

### Core Components (`ui/src/components/dunkstack/`)
- `DunkStackContextGauge.tsx` — Real-time token tracking gauge with color zones
- `DunkStackAgentView.tsx` — Agent communication and walkie-talkie chat
- `DunkStackSafetyPanel.tsx` — 3-tier safety system controls
- `DunkStackGuidePanel.tsx` — Contextual guidance panel
- `DunkStackPreviewPanel.tsx` — Preview panel for agent output

### Agent OS Components (`ui/src/components/appbuilder/`)
- `IntakeDock.tsx` — App intake form
- `AgentOSChat.tsx` — Agent OS chat interface
- `StandardsPanel.tsx` — Standards management
- `ProductPanel.tsx` — Product overview
- `SpecCards.tsx` — Feature specification cards
- `GapAnalysisPanel.tsx` — Gap analysis for specs
- `ExpandPanel.tsx` — Expand features panel

### Hooks
- `ui/src/hooks/useDunkStack.ts` — DunkStack state management
- `ui/src/hooks/useAgentOS.ts` — Agent OS features, gaps, resolution hooks

## State & Data

- Model presets stored in `localStorage` (`dunkstack-model-preset`)
- Three model presets: Opus 200K, Opus 1M, Sonnet 1M
- Agent OS features/gaps via `useAgentOS` hooks (API-backed)
- Walkie-talkie chat reads/writes `.agent/comms/` files
- DunkStack state managed via `useDunkStack` hook

## Patterns

- Right panel system: `safety | files | agent-os | preview | null`
- Center view system: `chat | agent-os-intake | agent-os-workflow`
- Model preset selection updates both UI and backend via `dunkstackUpdateModelPreset`
- Theme selector and dark mode toggle are independent copies (not shared with main app)

## Skill Recommendations

### Recommended
- `frontend-design` — When restyling gauge or panels (~8% context)
- `webapp-testing` — When testing interactions (~5% context)

### Specialized (load on demand)
- `mcp-builder` — If building new MCP integrations (~10% context)
- `doc-coauthoring` — If writing Agent OS documentation (~4% context)

### Context Budget: 1-2 skills ideal, 3+ not recommended

## Anti-Patterns

- Do NOT modify AutoForge kanban/dependency graph code from this context
- Do NOT touch WorkspacePage, DashboardPage, or YT Lab components
- Do NOT change shared hooks in `useProjects` or `useWebSocket` without understanding cross-app impact
- Do NOT remove the independent theme selector — DunkStack owns its own theme state

## Agent Personality

You are a systems-level thinker focused on context efficiency and token management. Think in terms of budgets, safety margins, and graceful degradation. When describing changes, reference token costs and context window implications. Be precise about safety thresholds.
