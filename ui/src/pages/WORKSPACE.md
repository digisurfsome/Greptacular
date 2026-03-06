# WORKSPACE.md — Context Override

> When working in this app, THIS file takes priority over root CLAUDE.md.
> Only reference root CLAUDE.md for shared infrastructure (build, server, design tokens).

## Identity

IdeaForge Workspace is a full-page coding workspace with multi-conversation management, a three-panel split view (Research / PRD Builder / Coder), file library, GitHub repo integration, and real-time context budget tracking. It supports passoff editing (sending PRD output to the Coder panel), swarm mode for parallel agents, and CI status monitoring.

## Route

`/#/workspace` — Full-page layout with sub-routes

## Components

### Page
- `ui/src/pages/WorkspacePage.tsx` — Main page with split view, sidebar, library, keyboard shortcuts

### Core Components (`ui/src/components/workspace/`)
- `WorkspaceSidebar.tsx` — Conversation list and management
- `WorkspaceChat.tsx` — Chat interface (used in split view panels)
- `WorkspaceLibrary.tsx` — File library panel
- `WorkspaceKeyboardHelp.tsx` — Keyboard shortcut overlay
- `WorkspaceUserGuide.tsx` — User guide modal
- `RepoSelector.tsx` — GitHub repository selector
- `PassoffEditor.tsx` — PRD-to-Coder passoff editor with sections
- `SwarmPanel.tsx` — Parallel agent swarm controls
- `CIStatusWidget.tsx` — CI/CD status indicator
- `CountdownTimerBar.tsx` — Countdown timer display

### Shared Components
- `GitActivityWidget.tsx` — Git activity feed (in `ui/src/components/`)

### Hooks
- `ui/src/hooks/useWorkspaceKeyboardShortcuts.ts` — Keyboard shortcut management

## State & Data

- Conversations managed via WorkspaceSidebar (API-backed via React Query)
- Working directory tracked per conversation
- Split view state: which panels are expanded/collapsed
- Passoff sections: structured PRD output with auto-forward to Coder
- Swarm state: parallel agent coordination
- Settings fetched via `getSettings()` API call

## Patterns

- Three-panel accordion: Research (200K) / PRD Builder (Opus 1M) / Coder (Sonnet/Opus)
- CollapsedPanelBar: thin vertical strip with rotated label for collapsed panels
- Auto-forward: PRD panel completion auto-sends to Coder panel
- Walkie-talkie log entries tracked via `WalkieTalkieLogEntry` type
- Breadcrumb navigation in header

## Skill Recommendations

### Recommended
- `frontend-design` — When building/restyling workspace panels (~8% context)
- `webapp-testing` — When testing multi-panel interactions (~5% context)
- `theme-factory` — When working on workspace theming (~6% context)

### Specialized (load on demand)
- `mcp-builder` — If integrating new tool servers (~10% context)
- `doc-coauthoring` — If writing workspace documentation (~4% context)

### Context Budget: 1-2 skills ideal, 3+ not recommended

## Anti-Patterns

- Do NOT modify DunkStackPage, DashboardPage, or YT Lab components
- Do NOT change AutoForge kanban/feature management from this context
- Do NOT share state directly between split view panels — use passoff/auto-forward pattern
- Do NOT remove breadcrumb navigation — it's the primary way back to the main app

## Agent Personality

You are a workflow architect focused on developer productivity. Think in terms of information flow between panels, seamless handoffs, and reducing context switches. When describing changes, reference the Research → PRD → Code pipeline. Be practical and output-focused.
