# UI Directory Map

> **Read this BEFORE exploring any UI files.** It tells you exactly where everything is.
> If your task is about a specific page, ONLY read that page's files. Do NOT explore other pages.

## Tech Stack
- React 19, TypeScript, Vite 7, TanStack Query, Tailwind CSS v4, Radix UI
- Entry point: `src/App.tsx` (routes defined here)
- API client: `src/lib/api.ts`
- Types: `src/lib/types.ts`
- Routes: `src/lib/routes.ts`
- Styles: `src/styles/globals.css`

---

## Pages (src/pages/)

Each page is a single `.tsx` file. Some have page-specific markdown docs alongside them.

| Page File | Route | What It Does |
|-----------|-------|-------------|
| `DashboardPage.tsx` | `/` | Main project dashboard — kanban board, agent controls, dependency graph |
| `WorkspacePage.tsx` | `/workspace` | AI chat workspace — conversations, library, token tracking |
| `DunkStackPage.tsx` | `/dunkstack` | DunkStack agent benchmarking and safety testing |
| `ArenaPage.tsx` | `/arena` | Model comparison arena — side-by-side AI evaluation |
| `ArenaChatPage.tsx` | `/arena/chat/:id` | Individual arena chat session |
| `YTStrategyLabPage.tsx` | `/yt-lab` | YouTube strategy lab — video analysis, tool extraction |
| `CliScripterPage.tsx` | `/cli-scripter` | CLI script builder and executor |
| `MetaEnginePage.tsx` | `/meta-engine` | Meta-training engine for AI model improvement |
| `MonitorPage.tsx` | `/monitor` | System monitoring dashboard |
| `PRDShredderPage.tsx` | `/prd-shredder` | PRD analysis and decomposition tool |
| `RoleLibraryPage.tsx` | `/role-library` | Agent role blueprint library |
| `SEOToolsPage.tsx` | `/seo-tools` | SEO analysis and optimization tools |
| `TokenBudgetPage.tsx` | `/token-budget` | Token usage tracking and budget management |
| `ToolRunnerPage.tsx` | `/tool-runner` | Execute and manage extracted tools |
| `ComponentDashboardPage.tsx` | `/components` | UI component inventory and preview |
| `MarketScraperPage.tsx` | (in Scraper hub) | Reddit market scraper — rendered inside the Scraper hub toggle |
| `PreviewMachinePage.tsx` | `/market-scraper` | Scraper hub — toggle between Preview Machine (default) and Market Scraper |

---

## Components (src/components/)

### Page-Specific Component Folders

Each folder contains components used ONLY by that page. If your task is about a page, look in its folder.

| Folder | Used By | Key Components |
|--------|---------|---------------|
| `workspace/` | WorkspacePage | WorkspaceChat, WorkspaceSidebar, WorkspaceChatInput, TokenLogPanel, UsageDashboard, LibraryPickerModal, RepoBrowser, SwarmPanel |
| `dunkstack/` | DunkStackPage | DunkStackAgentView, DunkStackCommsChat, DunkStackContextGauge, DunkStackGuidePanel, DunkStackPreviewPanel, DunkStackSafetyPanel |
| `yt-lab/` | YTStrategyLabPage | AgentLog, BatchImportView, BrowserView, CaptureGallery, DiscoveryPanel, ExecutionViewer, VideoIngestPanel, StepTracker |
| `cli-scripter/` | CliScripterPage | BuildDashboard, BuildLibrary, BuildLogPanel, PhaseStatusSidebar, PromptBar, ProjectFileBrowser, RuleBlock, GatePopup |
| `prd-shredder/` | PRDShredderPage | BuildRulesPanel, ShredderStatusBadge |
| `orchestrator/` | DashboardPage | ActionLogPanel, ApprovalBanner, CheckpointTimeline, CommitsPanel, VerificationHistory |
| `factory/` | (Factory features) | FactoryPanel, FactorySettings, PhasePRDManager |
| `appbuilder/` | (App builder features) | AgentOSChat, ExpandPanel, GapAnalysisPanel, IntakeDock, ProductPanel, SpecCards, StandardsPanel |
| `tool-factory/` | ToolRunnerPage | ToolCard, ToolDetailView, ToolManagerPage, ChainVisualizer, ThemePicker, PRDUploadModal, AnalyticsDashboard |
| `preview-machine/` | PreviewMachinePage | PipelinePanel, CopywriterControls, CalibrationCard |
| `ui/` | ALL pages | Shared primitives: alert, badge, button, card, checkbox, dialog, dropdown-menu, input, label, separator, switch, textarea |

### Shared Components (src/components/ root level)

These are used across multiple pages. Modify with care.

| Component | What It Does |
|-----------|-------------|
| `AgentMissionControl.tsx` | Dashboard showing active agents with mascots |
| `KanbanBoard.tsx` / `KanbanColumn.tsx` | Feature kanban board |
| `DependencyGraph.tsx` | Interactive node graph with dagre layout |
| `Terminal.tsx` / `TerminalTabs.tsx` | xterm.js multi-tab terminal |
| `AssistantChat.tsx` / `AssistantPanel.tsx` | AI project assistant |
| `SettingsModal.tsx` | Global settings panel |
| `ScheduleModal.tsx` | Agent scheduling UI |
| `FolderBrowser.tsx` | Server-side filesystem browser |
| `CelebrationOverlay.tsx` | Confetti on feature completion |
| `ExpandProjectModal.tsx` / `ExpandProjectChat.tsx` | Add features via natural language |
| `ProjectSelector.tsx` | Project selection dropdown |
| `FeatureCard.tsx` / `FeatureModal.tsx` | Feature display and editing |
| `DebugLogViewer.tsx` | Debug log display |
| `ErrorBoundary.tsx` | React error boundary |
| `ConfirmDialog.tsx` | Confirmation modal |

---

## Hooks (src/hooks/)

| Hook | Used By | What It Does |
|------|---------|-------------|
| `useWorkspaceChat.ts` | WorkspacePage | WebSocket connection for workspace chat |
| `useWorkspaceConversations.ts` | WorkspacePage | Conversation CRUD |
| `useWorkspaceLibrary.ts` | WorkspacePage | Library management |
| `useWorkspaceCategories.ts` | WorkspacePage | Category management |
| `useWebSocket.ts` | DashboardPage | Real-time project updates |
| `useProjects.ts` | DashboardPage | Project CRUD API hooks |
| `useDunkStack.ts` | DunkStackPage | DunkStack session management |
| `useAgentOS.ts` / `useAgentOSChat.ts` | App builder | Agent OS integration |
| `useFactory.ts` | Factory features | Factory controller hooks |
| `useToolFactory.ts` | ToolRunnerPage | Tool factory management |
| `usePRDShredder.ts` | PRDShredderPage | PRD shredder operations |
| `useRoleLibrary.ts` | RoleLibraryPage | Role blueprint CRUD |
| `useTokenBudget.ts` | TokenBudgetPage | Token budget tracking |
| `usePreviewMachine.ts` | PreviewMachinePage | Preview Machine pipeline status (2s poll), files, run/stop, calibration |
| `useSchedules.ts` | DashboardPage | Schedule management |
| `useConversations.ts` | Workspace | Conversation state |
| `useBackgroundSessions.ts` | Workspace | Background agent sessions |
| `useCheckpoints.ts` | Orchestrator | Checkpoint management |
| `useCommits.ts` | Orchestrator | Git commit tracking |
| `useActionLog.ts` | Orchestrator | Action log display |
| `useApprovals.ts` | Orchestrator | Approval workflow |
| `useTheme.ts` | Global | Theme/dark mode |
| `usePersistedState.ts` | Global | localStorage-backed state |
| `useCelebration.ts` | DashboardPage | Confetti trigger |

---

## Utility Files (src/lib/)

| File | What It Does |
|------|-------------|
| `api.ts` | REST API client — all fetch calls to the backend |
| `types.ts` | TypeScript type definitions for the entire app |
| `routes.ts` | Route path constants |
| `keyboard.ts` | Keyboard shortcut definitions |
| `utils.ts` | General utility functions |
| `timeUtils.ts` | Time formatting helpers |
| `paletteUtils.ts` | Color palette utilities |
| `waveParser.ts` | Audio wave parsing |

---

## Rules for UI Tasks

1. **If your task is about ONE page:** Only read that page's file + its component folder. Do NOT explore other pages.
2. **If your task is about a shared component:** Read the component file + check which pages import it before modifying.
3. **Do NOT read all hooks.** Read only the hook used by the page you're working on.
4. **The `ui/` components folder** contains shadcn/ui primitives. Do not modify these unless specifically asked.
5. **All API calls** go through `src/lib/api.ts`. Do not create new fetch calls elsewhere.
6. **All types** are defined in `src/lib/types.ts`. Add new types there, not in component files.
