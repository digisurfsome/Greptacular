# Page Index — Unified File Map

> **THE index.** One row per page = every file for that page.
> Read this INSTEAD of the three separate CLAUDE.md directory maps when you know which page you're working on.

## How to read this

Each row lists every file you need for that one page: the page component, its component folder, its hook, its backend router, its backend service, and its PRD folder. ONE read of this file and you know every path — no searching.

## Page Table

| Page | Route | Components | Hook(s) | Router | Service | PRD |
|------|-------|-----------|---------|--------|---------|-----|
| `DashboardPage.tsx` | `/` | root-level shared (`KanbanBoard`, `DependencyGraph`) + `orchestrator/` | `useProjects.ts`, `useWebSocket.ts`, `useSchedules.ts`, `useCelebration.ts` | `projects.py`, `features.py`, `agent.py`, `schedules.py` | `process_manager.py`, `scheduler_service.py` | `dashboard/` |
| `WorkspacePage.tsx` | `/workspace` | `workspace/` | `useWorkspaceChat.ts`, `useWorkspaceConversations.ts`, `useWorkspaceLibrary.ts`, `useWorkspaceCategories.ts` | `workspace.py` | `workspace_chat_session.py`, `workspace_database.py`, `workspace_library.py`, `workspace_summary.py` | `workspace/` |
| `DunkStackPage.tsx` | `/dunkstack` | `dunkstack/` | `useDunkStack.ts` | `dunkstack.py` | `dunkstack_chat_session.py`, `dunkstack_session.py`, `dunkstack_hooks.py` | `dunkstack/` |
| `ArenaPage.tsx` | `/arena` | (uses shared) | — | — | `model_router.py` | `arena/` |
| `ArenaChatPage.tsx` | `/arena/chat/:id` | (uses shared) | — | — | `model_router.py` | `arena/` |
| `YTStrategyLabPage.tsx` | `/yt-lab` | `yt-lab/` | — | `yt_processing.py`, `yt_batch.py`, `yt_ingestion.py` | `yt_processor.py`, `yt_discovery.py` | `yt-strategy-lab/` |
| `CliScripterPage.tsx` | `/cli-scripter` | `cli-scripter/` | — | `cli_scripter.py` | — | `cli-scripter/` |
| `MetaEnginePage.tsx` | `/meta-engine` | — | — | `meta_training.py` | `meta_training_ingestor.py`, `meta_writing_engine.py`, `meta_output_router.py` | `meta-engine/` |
| `MonitorPage.tsx` | `/monitor` | — | — | `ci_status.py` | `ci_monitor.py` | `monitor/` |
| `PRDShredderPage.tsx` | `/prd-shredder` | `prd-shredder/` | `usePRDShredder.ts` | `prd_shredder.py` | `prd_shredder.py`, `prd_analyzer.py`, `prd_ingestion.py` | `prd-shredder/` |
| `RoleLibraryPage.tsx` | `/role-library` | — | `useRoleLibrary.ts` | `role_library.py` | — | `role-library/` |
| `SEOToolsPage.tsx` | `/seo-tools` | — | — | `seo_tools.py` | — | `seo-tools/` |
| `TokenBudgetPage.tsx` | `/token-budget` | — | `useTokenBudget.ts` | `token_budget.py` | `token_budget.py` | `token-budget/` |
| `ToolRunnerPage.tsx` | `/tool-runner` | `tool-factory/` | `useToolFactory.ts` | `tool_runner.py`, `tool_factory.py`, `tool_analyzer.py`, `tool_themes.py` | `tool_runner.py`, `tool_analyzer.py`, `tool_registry.py`, `tool_usage.py`, `batch_tool_generator.py` | `tool-runner/` |
| `ComponentDashboardPage.tsx` | `/components` | — | — | — | `component_registry.py` | `component-dashboard/` |

## Shared Infrastructure (not tied to one page)

| Concern | File |
|---------|------|
| UI route paths | `ui/src/lib/routes.ts` |
| UI API client (all fetch calls) | `ui/src/lib/api.ts` |
| UI types | `ui/src/lib/types.ts` |
| UI app entry / router | `ui/src/App.tsx` |
| UI shared components (shadcn primitives) | `ui/src/components/ui/` |
| Server entry (router registration) | `server/main.py` |
| Database models + CRUD | `server/services/workspace_database.py` |
| Subscription auth rules | `docs/SUBSCRIPTION_AND_WEBSOCKET_GUIDE.md` |
| Working SDK client pattern to copy | `server/services/yt_processor.py._call_via_sdk()` |

## Agent OS (not a single page)

| File | Role |
|------|------|
| `server/routers/agent_os.py` | API prefix `/api/agent-os` |
| `server/services/agent_os_session.py` | Session management |
| `server/services/agent_os_intake.py`, `agent_os_intake_dock.py` | Intake |
| `server/services/agent_os_specs.py` | Spec generation |
| `server/services/agent_os_mechanism.py` | Mechanism extraction |
| `server/services/agent_os_features.py` | Feature management |
| `server/services/agent_os_product.py` | Product panel |
| `server/services/agent_os_standards.py` | Standards |
| `server/services/agent_os_codebase.py` | Codebase analysis |
| `server/services/agent_os_expand.py` | Project expansion |
| `server/services/agent_os_handoff.py` | Handoff |
| UI | `ui/src/components/appbuilder/` |

## When to use this file vs. the directory maps

- **Use this file** when you know which page you're working on → one read, all paths located.
- **Use `ui/CLAUDE.md` / `server/CLAUDE.md` / `docs/CLAUDE.md`** when you need the full inventory of a layer (every hook, every service, every doc) or for anything not listed above.
- **If you're about to Glob or Grep for a file** → stop and check this index first.
