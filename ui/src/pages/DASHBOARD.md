# DASHBOARD.md — Context Override

> When working in this app, THIS file takes priority over root CLAUDE.md.
> Only reference root CLAUDE.md for shared infrastructure (build, server, design tokens).

## Identity

The Multi-Session Dashboard runs 1, 2, or 3 independent AI sessions side-by-side. Each pane can use a different provider (Claude, Codex, Gemini) and any conversation from the sidebar. Sessions persist in the background when not actively viewed, enabling true multi-agent comparison and parallel work.

## Route

`/#/dashboard` — Full-page layout with sub-routes

## Components

### Page
- `ui/src/pages/DashboardPage.tsx` — Main page with pane management, layout modes, provider selection

### Reused Workspace Components (`ui/src/components/workspace/`)
- `WorkspaceSidebar.tsx` — Shared conversation sidebar
- `WorkspaceChat.tsx` — Chat interface (one instance per pane)
- `RepoSelector.tsx` — GitHub repository selector

## State & Data

- **PaneState**: `{ id, conversationId, provider, label, collapsed, attachedSessionId }`
- **LayoutMode**: `single | dual | triple`
- **Providers**: Claude (blue), Codex (emerald), Gemini (violet)
- Background session persistence via `attachedSessionId`
- Each pane has independent WebSocket connection via WorkspaceChat

## Patterns

- Panes are created dynamically via `createPane()` helper
- Layout modes switch between 1/2/3 column layouts
- CollapsedPaneBar: thin vertical strip for collapsed panes (same pattern as Workspace)
- Provider selector per pane with color-coded badges
- Sidebar shared across all panes — selecting a conversation targets the active pane

## Skill Recommendations

### Recommended
- `frontend-design` — When restyling pane layouts (~8% context)
- `webapp-testing` — When testing multi-pane interactions (~5% context)

### Specialized (load on demand)
- `mcp-builder` — If adding new provider integrations (~10% context)

### Context Budget: 1-2 skills ideal, 3+ not recommended

## Anti-Patterns

- Do NOT modify DunkStackPage, WorkspacePage, or YT Lab components
- Do NOT change AutoForge kanban/feature management from this context
- Do NOT break WorkspaceChat/WorkspaceSidebar compatibility — these are shared with Workspace
- Do NOT hardcode provider count — the system supports dynamic pane creation
- Do NOT mix pane state — each pane is fully independent

## Agent Personality

You are a parallel systems thinker focused on multi-provider comparison and independent session management. Think in terms of isolation, side-by-side comparison, and session persistence. When describing changes, reference pane independence and provider flexibility. Be modular and clean.
