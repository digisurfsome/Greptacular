# Server Directory Map

> **Read this BEFORE exploring any server files.** It tells you exactly where everything is.
> If your task is about a specific API endpoint, find the router first, then its matching service.

## Architecture
- **Framework:** FastAPI (Python 3.11+)
- **Entry point:** `server/main.py` (registers all routers)
- **Pattern:** Router (HTTP/WebSocket endpoints) → Service (business logic) → Database
- **Database:** SQLite via SQLAlchemy (workspace.db at ~/.autoforge/)

---

## Routers (server/routers/) — API Endpoints

Each router handles one feature area. Find the right router = find the right endpoints.

| Router File | API Prefix | What It Does |
|-------------|-----------|-------------|
| `workspace.py` | `/api/workspace` | Workspace chat — conversations, messages, WebSocket, token logs, library |
| `projects.py` | `/api/projects` | Project CRUD with registry integration |
| `features.py` | `/api/features` | Feature management for projects |
| `agent.py` | `/api/agent` | Agent control — start/stop/pause/resume |
| `agent_os.py` | `/api/agent-os` | Agent OS — intake, specs, mechanisms, features, standards, handoff |
| `filesystem.py` | `/api/filesystem` | Filesystem browser with security controls |
| `terminal.py` | `/api/terminal` | Interactive terminal I/O with PTY (WebSocket) |
| `devserver.py` | `/api/devserver` | Dev server control — start/stop and config |
| `settings.py` | `/api/settings` | Global settings management |
| `schedules.py` | `/api/schedules` | Time-based agent scheduling CRUD |
| `spec_creation.py` | `/api/spec` | Interactive spec creation (WebSocket) |
| `expand_project.py` | `/api/expand` | Project expansion via natural language |
| `assistant_chat.py` | `/api/assistant` | Read-only project assistant chat |
| `dunkstack.py` | `/api/dunkstack` | DunkStack benchmarking sessions |
| `yt_processing.py` | `/api/yt` | YouTube video processing and analysis |
| `yt_batch.py` | `/api/yt/batch` | YouTube batch import |
| `yt_ingestion.py` | `/api/yt/ingestion` | YouTube data ingestion |
| `seo_tools.py` | `/api/seo` | SEO analysis tools |
| `cli_scripter.py` | `/api/cli-scripter` | CLI script building |
| `prd_shredder.py` | `/api/prd-shredder` | PRD decomposition |
| `role_library.py` | `/api/role-library` | Role blueprint management |
| `token_budget.py` | `/api/token-budget` | Token budget tracking |
| `tool_runner.py` | `/api/tool-runner` | Tool execution |
| `tool_factory.py` | `/api/tool-factory` | Tool generation and management |
| `tool_analyzer.py` | `/api/tool-analyzer` | Tool analysis |
| `tool_themes.py` | `/api/tool-themes` | Tool theming |
| `factory.py` | `/api/factory` | Factory controller |
| `execution.py` | `/api/execution` | Execution viewer |
| `actions.py` | `/api/actions` | Action log |
| `approvals.py` | `/api/approvals` | Approval workflows |
| `checkpoints.py` | `/api/checkpoints` | Build checkpoints |
| `captures.py` | `/api/captures` | Screen captures |
| `ci_status.py` | `/api/ci` | CI pipeline status |
| `design_guide.py` | `/api/design-guide` | Design guide management |
| `github.py` | `/api/github` | GitHub integration |
| `ingestion_sequences.py` | `/api/ingestion-sequences` | Data ingestion sequences |
| `meta_training.py` | `/api/meta-training` | Meta-training engine |
| `notifications.py` | `/api/notifications` | Notification system |
| `swarm.py` | `/api/swarm` | Swarm orchestration |
| `verifications.py` | `/api/verifications` | Build verification |
| `ap_code_manager.py` | `/api/ap-code` | Activepieces Code step source code read/write via Docker psql |
| `market_scraper.py` | `/api/market-scraper` | Reddit market scraper — scrapes, projects, angles |
| `preview_machine.py` | `/api/preview-machine` | Preview Machine pipeline — run/stop a stage, status, files, calibration |

---

## Services (server/services/) — Business Logic

Each service contains the core logic for a feature. Routers call services, not the other way around.

### Core Services (Touch With Care)

| Service File | What It Does |
|-------------|-------------|
| `workspace_chat_session.py` | **THE main chat engine.** Claude SDK client, message handling, tool use tracking. Read this if touching workspace chat. |
| `workspace_database.py` | **ALL database models and CRUD.** WorkspaceConversation, WorkspaceMessage, WorkspaceTokenLog, RoleBlueprint, etc. |
| `workspace_library.py` | Library management for workspace |
| `workspace_summary.py` | Conversation summarization |
| `workspace_repos.py` | Repository integration |
| `workspace_github.py` | GitHub operations from workspace |
| `workspace_token_encryption.py` | Token encryption |
| `process_manager.py` | Agent process lifecycle management |
| `project_config.py` | Project type detection and dev commands |
| `terminal_manager.py` | Terminal session management with PTY |
| `model_router.py` | Routes requests to correct AI model |
| `background_session_manager.py` | Background agent session management |

### Page-Specific Services

| Service File | Page | What It Does |
|-------------|------|-------------|
| `dunkstack_chat_session.py` | DunkStack | DunkStack chat sessions |
| `dunkstack_session.py` | DunkStack | DunkStack agent sessions |
| `dunkstack_hooks.py` | DunkStack | DunkStack event hooks |
| `yt_processor.py` | YT Lab | YouTube video processing — has working SDK pattern (copy this for new SDK clients) |
| `yt_discovery.py` | YT Lab | YouTube channel discovery |
| `prd_shredder.py` | PRD Shredder | PRD analysis and decomposition |
| `prd_analyzer.py` | PRD Shredder | PRD content analysis |
| `prd_ingestion.py` | PRD Shredder | PRD file ingestion |
| `tool_analyzer.py` | Tool Runner | Tool analysis |
| `tool_runner.py` | Tool Runner | Tool execution |
| `tool_registry.py` | Tool Runner | Tool registry |
| `tool_usage.py` | Tool Runner | Tool usage tracking |
| `batch_tool_generator.py` | Tool Factory | Batch tool generation |
| `token_budget.py` | Token Budget | Token budget calculations |
| `preview_machine_service.py` | Preview Machine | Runs pipeline stages as subprocesses (argv-only, whitelisted args); ring-buffer logs; runlog calibration |
| `ci_monitor.py` | Monitor | CI pipeline monitoring |

### Agent OS Services

| Service File | What It Does |
|-------------|-------------|
| `agent_os_session.py` | Agent OS session management |
| `agent_os_intake.py` | Intake processing |
| `agent_os_intake_dock.py` | Intake dock UI logic |
| `agent_os_specs.py` | Spec generation |
| `agent_os_mechanism.py` | Mechanism extraction |
| `agent_os_features.py` | Feature management |
| `agent_os_product.py` | Product panel logic |
| `agent_os_standards.py` | Standards enforcement |
| `agent_os_codebase.py` | Codebase analysis |
| `agent_os_expand.py` | Project expansion |
| `agent_os_handoff.py` | Agent handoff |
| `agent_os_file_utils.py` | File utilities for Agent OS |

### Chat Session Services

| Service File | What It Does |
|-------------|-------------|
| `assistant_chat_session.py` | Project assistant chat |
| `assistant_database.py` | Assistant data persistence |
| `spec_chat_session.py` | Spec creation chat (includes gap analysis) |
| `expand_chat_session.py` | Expand project chat |
| `design_guide_session.py` | Design guide chat |
| `chat_constants.py` | Shared constants for all chat services |

### Integration Services

| Service File | What It Does |
|-------------|-------------|
| `codex_bridge.py` | OpenAI Codex integration |
| `gemini_bridge.py` | Google Gemini integration |
| `github_integration.py` | GitHub API operations |
| `google_auth.py` | Google OAuth |

### Other Services

| Service File | What It Does |
|-------------|-------------|
| `scheduler_service.py` | APScheduler-based automated agent scheduling |
| `dev_server_manager.py` | Dev server lifecycle |
| `log_compaction.py` | Auto-cleanup for old action/verification logs |
| `rate_limit_logger.py` | Rate limit event logging |
| `swarm_orchestrator.py` | Multi-agent swarm coordination |
| `factory_controller.py` | Factory build orchestration |
| `boilerplate_manager.py` | Project boilerplate management |
| `component_registry.py` | UI component registry |
| `screen_recorder.py` | Screen recording |
| `screenshot_analyzer.py` | Screenshot analysis |
| `style_extractor.py` / `style_manager.py` / `style_modifiers.py` | Style management |
| `sheet_blueprint.py` / `sheet_deployer.py` / `sheet_theme_engine.py` | Sheet operations |
| `meta_output_router.py` / `meta_training_ingestor.py` / `meta_writing_engine.py` | Meta-training pipeline |
| `ingestion_sequence_generator.py` | Ingestion sequence generation |
| `handoff_watcher.py` | Handoff file watcher |
| `computer_use_agent.py` | Computer use agent |
| `docker_manager.py` | Docker container management |
| `api_research.py` | API research operations |

---

## Rules for Server Tasks

1. **Find the router first.** Every API endpoint lives in a router file. The router calls the service.
2. **Do NOT modify workspace_database.py** unless your task specifically requires a new database model or query.
3. **Do NOT modify workspace_chat_session.py** unless your task is specifically about the chat engine.
4. **New SDK clients** must copy the pattern from `yt_processor.py._call_via_sdk()` — it has all the fixes.
5. **New routers** must be registered in `server/main.py`.
6. **If your task is about one page's backend:** Read only that page's router + service. Do NOT explore other routers.
