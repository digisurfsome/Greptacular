# AutoForge Core — Agent Brief

> The core autonomous coding engine. Projects, features, agent lifecycle, security, and the MCP server.

## What It Does

AutoForge runs Claude as an autonomous coding agent. You create a project with an app spec, it generates features in a SQLite database, then implements them one by one across multiple sessions. Supports parallel agents, batch feature processing, YOLO mode (skip testing), and scheduled runs.

## Files Involved

### Backend (Python)
| File | Purpose |
|------|---------|
| `autonomous_agent_demo.py` | Entry point — `--yolo`, `--parallel`, `--batch-size`, `--batch-features` |
| `agent.py` | Agent session loop using Claude Agent SDK |
| `client.py` | ClaudeSDKClient — security hooks, MCP servers, Vertex AI |
| `security.py` | Bash command allowlist validation (ALLOWED_COMMANDS) |
| `prompts.py` | Prompt loading with project-specific fallback + batch prompts |
| `progress.py` | Progress tracking, DB queries, webhook notifications |
| `registry.py` | Project name → path mapping (SQLite) |
| `parallel_orchestrator.py` | Concurrent agent execution with dependency-aware scheduling |
| `start.py` | CLI launcher with project creation/selection |
| `autoforge_paths.py` | Path resolution with dual-path backward compat |
| `rate_limit_utils.py` | Rate limit detection, exponential backoff |
| `auth.py` | Authentication error detection |
| `env_constants.py` | Shared env var constants (API_ENV_VARS) |

### Backend (API)
| File | Purpose |
|------|---------|
| `api/database.py` | SQLAlchemy models: Feature, Schedule, ScheduleOverride |
| `api/dependency_resolver.py` | Cycle detection (Kahn's + DFS), dependency validation |
| `api/migration.py` | JSON-to-SQLite migration |

### Server Routers
| File | Purpose |
|------|---------|
| `server/routers/projects.py` | Project CRUD with registry |
| `server/routers/features.py` | Feature management |
| `server/routers/agent.py` | Agent start/stop/pause/resume |
| `server/routers/filesystem.py` | Filesystem browser with security |
| `server/routers/schedules.py` | Time-based scheduling |
| `server/routers/settings.py` | Global settings (model, YOLO, batch, headless) |
| `server/routers/terminal.py` | PTY terminal sessions |
| `server/routers/devserver.py` | Dev server control |

### Server Services
| File | Purpose |
|------|---------|
| `server/services/process_manager.py` | Agent process lifecycle |
| `server/services/project_config.py` | Project type detection, dev commands |
| `server/services/terminal_manager.py` | Terminal sessions with PTY |
| `server/services/scheduler_service.py` | APScheduler-based scheduling |
| `server/services/dev_server_manager.py` | Dev server lifecycle |

### MCP Server
| File | Purpose |
|------|---------|
| `mcp_server/feature_mcp.py` | Feature management tools for the agent |

### Frontend
| File | Purpose |
|------|---------|
| `ui/src/App.tsx` | Main app — project selection, kanban board, agent controls |
| `ui/src/components/AgentMissionControl.tsx` | Dashboard with agent mascots |
| `ui/src/components/DependencyGraph.tsx` | Interactive node graph (dagre) |
| `ui/src/components/CelebrationOverlay.tsx` | Confetti on feature completion |
| `ui/src/components/FolderBrowser.tsx` | Filesystem browser for project selection |
| `ui/src/components/Terminal.tsx` | xterm.js terminal |
| `ui/src/components/ScheduleModal.tsx` | Schedule management |
| `ui/src/components/SettingsModal.tsx` | Global settings panel |
| `ui/src/hooks/useWebSocket.ts` | Real-time updates (progress, agent status, logs) |
| `ui/src/hooks/useProjects.ts` | React Query hooks for project API |

## Data Flow

```
User creates project → Registry maps name → path
Agent starts → Reads app_spec.txt → Creates features in features.db (via MCP)
Session loop → Claims next feature → Implements → Marks passing → Next feature
Parallel mode → Multiple agents claim features atomically
UI ← WebSocket ← Progress/status/log updates
```

## Database Tables (features.db)

- **features** — id, priority, category, name, description, steps, status (pending/in_progress/passing/failing), dependencies
- **schedules** — Cron-like scheduling for automated runs
- **schedule_overrides** — Exception rules for schedules

## Key MCP Tools (available to the coding agent)

- `feature_get_ready` — Features with all dependencies met
- `feature_claim_and_get` — Atomic claim for parallel mode
- `feature_mark_passing` / `feature_mark_failing` — Status updates
- `feature_create_bulk` — Initialize all features (initializer agent)
- `feature_add_dependency` / `feature_set_dependencies` — Dependency management

## Common Modifications

- **Add a new setting:** `server/routers/settings.py` + `registry.py` (GlobalSettings model) + `ui/src/components/SettingsModal.tsx`
- **Add a new agent capability:** `client.py` (MCP servers or tools) + `security.py` (if new bash commands needed)
- **Add a new feature field:** `api/database.py` (Feature model) + `mcp_server/feature_mcp.py` (MCP tools) + `ui/src/lib/types.ts` + relevant UI components
