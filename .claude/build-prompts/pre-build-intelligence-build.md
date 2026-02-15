# Build Prompt: Pre-Build Intelligence — Direct Implementation into AutoForge

## What You Are Doing

You are implementing the Pre-Build Intelligence Pipeline directly into the AutoForge
codebase. This is NOT building a separate app — you are adding new features to the
existing Python backend and React UI that AutoForge already has.

Read the full handoff document FIRST before writing any code:
- `.claude/handoffs/pre-build-intelligence-handoff.md` — The 3-phase pre-build pipeline (3 features)

## Critical Context

AutoForge is an autonomous coding agent system. It uses Claude Code CLI to build apps.
The Pre-Build Intelligence Pipeline adds analysis and planning phases BEFORE the existing
build process starts.

### Existing Architecture You Must Understand

Read these files to understand the patterns you MUST follow:

**Core Python backend:**
- `agent.py` — Agent session loop (Claude Agent SDK). New agent types (spec-analyzer, architect) follow this pattern.
- `client.py` — ClaudeSDKClient with security hooks. New agents get their own client config (spec-analyzer and architect are READ-ONLY — no Playwright, no code writing).
- `autonomous_agent_demo.py` — Entry point for running agents. This is where the build pipeline sequence lives. Pre-build phases run BEFORE the existing initializer.
- `prompts.py` — Prompt template loading with fallback chain. New agent types get new prompt templates.
- `progress.py` — Progress tracking. Add pre-build phase progress events.

**MCP feature server:**
- `mcp_server/feature_mcp.py` — Feature management tools. The auto-dependency detection (Feature 3) calls `feature_add_dependency` here.
- `api/database.py` — SQLAlchemy models (Feature table with dependencies).
- `api/dependency_resolver.py` — Cycle detection (Kahn's algorithm + DFS). Auto-dependency uses this for validation.

**Prompt templates:**
- `.claude/templates/coding_prompt.template.md` — Existing coding prompt. Add reference to ARCHITECTURE.md.
- `.claude/templates/initializer_prompt.template.md` — Existing initializer prompt. Enhance with dependency detection instructions.

**React UI:**
- `ui/src/App.tsx` — Main app. Show pre-build phase status.
- `ui/src/hooks/useWebSocket.ts` — Real-time updates. New event types for pre-build phases.
- `ui/src/lib/types.ts` — TypeScript types.
- `ui/src/components/AgentMissionControl.tsx` — Agent dashboard. Show pre-build agents.

**Server routers:**
- `server/routers/agent.py` — Agent control. Add pre-build phase triggers.

**Server services:**
- `server/services/process_manager.py` — Process lifecycle. New pre-build agent processes.

**Project structure (what AutoForge creates in user projects):**
- `autoforge_paths.py` — Central path resolution. New output files (spec-analysis.md, ARCHITECTURE.md) go in the project directory.

### Key Patterns to Follow

1. **New agent types** follow the same `agent.py` session loop — they get a prompt, a client config, and run as a subprocess.
2. **Spec Analyzer and Architect agents are READ-ONLY** — they do NOT write application code. They produce analysis documents only (spec-analysis.md, ARCHITECTURE.md). Configure their ClaudeSDKClient accordingly (no Playwright MCP server, restricted write paths).
3. **New CLI flags** go in `autonomous_agent_demo.py` argparse. Example: `--skip-analysis`, `--skip-architect`, `--analyze-only`.
4. **New prompt templates** go in `.claude/templates/` as `.template.md` files.
5. **Pre-build phases run BEFORE the initializer** — they insert into the existing pipeline in `autonomous_agent_demo.py`, not after it.
6. **ARCHITECTURE.md is committed to the project root** and referenced by all subsequent coding agents via an addition to the coding prompt template.

## Build Order

Implement features in this order (matches the handoff):

1. **Feature 1: Smart Spec Analyzer Agent** — New agent type that validates app_spec.txt before building. Produces spec-analysis.md with a completeness score (1-5). Blocks build if score < 3 (configurable via `--min-spec-score`).
2. **Feature 2: Architecture Planning Agent** — New agent type that reads the validated spec and produces ARCHITECTURE.md (database schema, API structure, component tree, routing, auth strategy). All subsequent coding agents reference this document.
3. **Feature 3: Auto-Dependency Detection** — Enhance the initializer to run a second pass after creating features. AI analysis + keyword heuristics detect dependencies between features and call `feature_add_dependency` automatically. Validates acyclic graph via existing Kahn's algorithm in `dependency_resolver.py`.

## What NOT To Do

- Do NOT create a new project — this goes into the EXISTING AutoForge codebase
- Do NOT modify the existing build flow for users who don't want pre-build analysis — phases are OPTIONAL (toggled via flags, on by default for non-YOLO mode, off for YOLO mode)
- Do NOT break backward compatibility — existing `--yolo` mode skips all pre-build phases
- Do NOT add new pip dependencies unless absolutely necessary
- Do NOT change database schema in a way that breaks existing features.db files
- Do NOT make the spec analyzer agent write any application code — it only produces a report
- Do NOT make the architect agent write any application code — it only produces ARCHITECTURE.md

## Testing

After implementing each feature:
```bash
ruff check .                          # Lint
python test_security.py               # Security tests
python -m pytest test_client.py       # Client tests
python -m pytest test_dependency_resolver.py  # Dependency resolver tests (critical for Feature 3)
cd ui && npm run build                # UI type check + build
```

## How to Verify Success

- Running `python autonomous_agent_demo.py --project-dir my-app` now runs spec analysis + architect + initializer + coding (pre-build ON by default)
- Running `python autonomous_agent_demo.py --project-dir my-app --yolo` skips all pre-build phases (backward compatible)
- Running `python autonomous_agent_demo.py --project-dir my-app --skip-analysis` skips just the spec analyzer
- Running `python autonomous_agent_demo.py --project-dir my-app --analyze-only` runs just the spec analyzer and stops
- The spec analyzer produces `{project_dir}/.autoforge/spec-analysis.md` with a completeness score
- The architect produces `{project_dir}/ARCHITECTURE.md` referenced by coding agents
- After initialization, features have auto-detected dependencies in the features database
- The UI shows pre-build phase status (analyzing, planning, initializing) before coding begins
