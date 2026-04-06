# Architecture Reference

## Project Overview

Autonomous coding agent system with a React-based UI. Uses the Claude Agent SDK to build complete applications over multiple sessions:

1. **Initializer Agent** — Reads app spec, creates features in SQLite
2. **Coding Agent** — Implements features one by one, marks as passing

## npm CLI (bin/, lib/)

The `autoforge` command is a Node.js wrapper:
- `bin/autoforge.js` — Entry point
- `lib/cli.js` — Python detection, venv management at `~/.autoforge/venv/`, server startup
- `package.json` — npm package config (`autoforge-ai`)
- `requirements-prod.txt` — Runtime-only Python deps

## Core Python Modules

- `start.py` — CLI launcher with project creation/selection menu
- `autonomous_agent_demo.py` — Agent entry point (`--yolo`, `--parallel`, `--batch-size`, `--batch-features`)
- `autoforge_paths.py` — Path resolution with dual-path backward compatibility
- `agent.py` — Agent session loop using Claude Agent SDK
- `client.py` — ClaudeSDKClient with security hooks, MCP servers, Vertex AI
- `security.py` — Bash command allowlist validation
- `prompts.py` — Prompt template loading with project-specific fallback
- `progress.py` — Progress tracking, database queries, webhooks
- `registry.py` — Project registry (name-to-path mapping), global settings
- `parallel_orchestrator.py` — Concurrent agent execution with dependency-aware scheduling
- `auth.py` — Authentication error detection
- `env_constants.py` — Shared env var constants (API_ENV_VARS)
- `rate_limit_utils.py` — Rate limit detection, retry parsing, exponential backoff
- `api/database.py` — SQLAlchemy models (Feature, Schedule, ScheduleOverride)
- `api/dependency_resolver.py` — Cycle detection (Kahn's + DFS) and dependency validation
- `api/migration.py` — JSON-to-SQLite migration

## Project Registry

Registry maps project names to paths using SQLite at `~/.autoforge/registry.db`. Uses POSIX path format for cross-platform compatibility.

## Feature Management

Features stored in SQLite (`features.db`) via SQLAlchemy. Agent interacts through MCP server (`mcp_server/feature_mcp.py`).

MCP tools: `feature_get_stats`, `feature_get_by_id`, `feature_get_summary`, `feature_get_ready`, `feature_get_blocked`, `feature_get_graph`, `feature_claim_and_get`, `feature_mark_in_progress`, `feature_mark_passing`, `feature_mark_failing`, `feature_skip`, `feature_clear_in_progress`, `feature_create_bulk`, `feature_create`, `feature_add_dependency`, `feature_remove_dependency`, `feature_set_dependencies`

## Project Structure for Generated Apps

Projects registered in `~/.autoforge/registry.db`. Each contains:
- `.autoforge/prompts/app_spec.txt` — App specification (XML)
- `.autoforge/prompts/initializer_prompt.md` — First session prompt
- `.autoforge/prompts/coding_prompt.md` — Continuation prompt
- `.autoforge/features.db` — Feature database
- `.autoforge/.agent.lock` — Lock file
- `.autoforge/allowed_commands.yaml` — Custom bash allowlist (optional)
- `CLAUDE.md` — Project root (SDK convention)

Legacy projects auto-migrate to `.autoforge/` on next agent start.

## Key Patterns

### Prompt Loading Fallback
1. Project-specific: `{project_dir}/.autoforge/prompts/{name}.md`
2. Base template: `.claude/templates/{name}.template.md`

### Agent Session Flow
1. Check `.autoforge/features.db` for features (initializer vs coding)
2. Create ClaudeSDKClient with security settings
3. Send prompt and stream response
4. Auto-continue with 3-second delay

### Real-time UI Updates (WebSocket)
Messages via `/ws/projects/{project_name}`: `progress`, `agent_status`, `log`, `feature_update`, `agent_update`

### Parallel Mode
Orchestrator spawns multiple agents (up to `--max-concurrency`). Features claimed atomically via `feature_claim_and_get`. Max 5 coding + 5 testing agents (11 total including orchestrator).

### Multi-Feature Batching
`--batch-size N` (1-3, default 3), `--batch-features 1,2,3` for specific IDs.

### Design System
Neobrutalism with Tailwind CSS v4. Variables in `ui/src/styles/globals.css`. Color tokens: `--color-neo-pending` (yellow), `--color-neo-progress` (cyan), `--color-neo-done` (green).
