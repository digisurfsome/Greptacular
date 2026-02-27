# Greptacular — Agent Briefing

> **Read this first.** This gives you full architectural awareness in ~2K tokens instead of reading the whole codebase. Then read the relevant feature brief in `docs/agent-briefs/` for your specific task.

---

## What This Is

Greptacular is an autonomous coding agent platform with a React UI. It uses Claude to build complete applications over multiple sessions. The system has four major areas: **AutoForge** (the core agent engine), **Workspace** (multi-panel AI chat), **DunkStack** (context-aware agent management), and **YT Strategy Lab** (YouTube video processing pipeline).

## Tech Stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy, uvicorn, WebSockets
- **Frontend:** React 19, TypeScript, Vite 7, TanStack Query, Tailwind CSS v4, Radix UI
- **Database:** SQLite (per-project `features.db`, global `workspace.db`, global `registry.db`), migrating to Supabase
- **AI:** Claude Agent SDK, Anthropic API (Claude Opus/Sonnet/Haiku), optional Vertex AI
- **Tools:** yt-dlp, ffmpeg, xterm.js, dagre, noVNC

## Directory Map

```
/                           Root — Python backend + config
├── server/                 FastAPI server
│   ├── routers/            API route handlers (one file per feature area)
│   ├── services/           Business logic services
│   └── utils/              Shared utilities
├── ui/                     React frontend (Vite)
│   ├── src/pages/          Page components (one per route)
│   ├── src/components/     Feature-grouped component folders
│   ├── src/hooks/          React hooks (data fetching, WebSocket, state)
│   ├── src/lib/            api.ts (REST client), types.ts (all TypeScript types)
│   └── src/styles/         globals.css (Tailwind v4 theme)
├── api/                    Database models + migration
├── mcp_server/             MCP server for agent-to-feature communication
├── docs/                   Strategy docs, PRDs, agent briefs
│   └── agent-briefs/       Feature-specific briefing docs for coding agents
├── .claude/                Claude Code commands, agents, skills, templates
├── blueprints/             Implementation blueprints (phased plans)
└── examples/               Config examples
```

## Database Schema Summary

### Per-Project (`{project}/.autoforge/features.db`)
| Table | Purpose |
|-------|---------|
| features | Coding tasks with priority, category, status, dependencies |
| schedules | Time-based agent scheduling |
| schedule_overrides | Schedule exception rules |

### Global (`~/.autoforge/workspace.db`)
| Table | Purpose |
|-------|---------|
| workspace_conversations | Chat sessions with model, effort, context mode |
| workspace_messages | Messages within conversations |
| workspace_categories | User-defined conversation categories |
| workspace_library_folders | Nested folder structure for file library |
| workspace_library_files | Uploaded/saved files with content and type |
| workspace_file_activations | Per-conversation file activation state |
| workspace_connected_repos | GitHub repo connections |
| workspace_summaries | Auto-generated conversation summaries |
| workspace_notifications | Agent notifications |
| workspace_rate_limit_events | Rate limit tracking |
| workspace_premium_ledger | Token cost tracking for >200K context |
| workspace_token_logs | Per-turn token audit |

### Global (`~/.autoforge/registry.db`)
| Table | Purpose |
|-------|---------|
| projects | Maps project names → filesystem paths |

### DunkStack (file-based, not SQLite)
Lives in `{project}/.agent/` — uses markdown files for comms, YAML for config, and in-memory token tracking via API.

## API Endpoint Index

### AutoForge Core (`/api/`)
- `projects/*` — Project CRUD with registry
- `features/*` — Feature management (CRUD, status, dependencies)
- `agent/*` — Agent control (start/stop/pause/resume)
- `filesystem/*` — Filesystem browser with security
- `schedules/*` — Time-based scheduling
- `settings/*` — Global settings (model, YOLO, batch size)
- `terminal/*` — PTY terminal sessions (WebSocket)
- `devserver/*` — Dev server lifecycle

### Workspace (`/api/workspace/`)
- `conversations/*` — Chat session CRUD, search, summaries
- `categories/*` — Category management
- `usage/*` — Token usage analytics
- `ws` — WebSocket for real-time chat streaming

### DunkStack (`/api/dunkstack/`)
- `comms/*` — Walkie-talkie message read/write
- `control` — Session mode (idle/continue/autopilot)
- `tokens/*` — Token tracking with safety tiers
- `bridge/*` — Session continuity bridge save/load
- `config` — YAML config management
- `ws` — WebSocket for real-time updates

### YT Strategy Lab (`/api/yt-lab/`)
- `ingest` — YouTube URL → transcript, metadata, screenshots
- `discover` / `discover-stream` — AI opportunity analysis (SSE)
- `process` / `process-stream` — Strategy extraction (SSE)
- `batch/*` — Multi-video batch processing
- `health` — Dependency health check
- `channels/*` — Channel tracking (planned)

## Key Patterns

1. **SSE streaming** — Discovery and processing endpoints use Server-Sent Events for real-time progress
2. **WebSocket** — Each major system has its own WebSocket for real-time updates
3. **React Query** — All data fetching uses TanStack Query with custom hooks
4. **SQLAlchemy ORM** — All database access through models, not raw SQL
5. **MCP Server** — Agent communicates with features database through MCP tools
6. **Neobrutalism design** — Tailwind v4 with bold borders, shadows, and bright accent colors
7. **localStorage** — YT Lab projects still use localStorage (migrating to Supabase)
8. **File-based comms** — DunkStack uses markdown files in `.agent/` for agent communication
9. **Types in one file** — All TypeScript interfaces live in `ui/src/lib/types.ts`
10. **API in one file** — All REST client functions live in `ui/src/lib/api.ts`

## File Naming Conventions

- **Pages:** `ui/src/pages/{Name}Page.tsx`
- **Components:** `ui/src/components/{feature-name}/{ComponentName}.tsx`
- **Hooks:** `ui/src/hooks/use{Name}.ts`
- **Routers:** `server/routers/{feature_name}.py`
- **Services:** `server/services/{feature_name}.py` or `{feature_name}_service.py`
- **Types:** All in `ui/src/lib/types.ts` (search for the interface name)
- **API functions:** All in `ui/src/lib/api.ts` (search for the function name)
