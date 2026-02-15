# Build Prompt: QA Pipeline — Direct Implementation into AutoForge

## What You Are Doing

You are implementing the QA Pipeline directly into the AutoForge codebase. This is NOT
building a separate app — you are adding new features to the existing Python backend and
React UI that AutoForge already has.

Read the full handoff document FIRST before writing any code:
- `.claude/handoffs/qa-pipeline-handoff.md` — The 4-phase QA pipeline (8 features)
- `.claude/handoffs/computer-use-qa-handoff.md` — Feature 8: Computer Use exploratory QA

## Critical Context

AutoForge is an autonomous coding agent system. It uses Claude Code CLI to build apps.
The QA Pipeline adds quality assurance phases to the existing build process.

### Existing Architecture You Must Understand

Read these files to understand the patterns you MUST follow:

**Core Python backend:**
- `agent.py` — Agent session loop (Claude Agent SDK). New agent types (review, QA) follow this pattern.
- `client.py` — ClaudeSDKClient with security hooks. New agents get their own client config.
- `autonomous_agent_demo.py` — Entry point for running agents. Add new CLI flags here.
- `parallel_orchestrator.py` — Concurrent agent execution. QA phases integrate here.
- `prompts.py` — Prompt template loading. New agent types get new prompt templates.
- `progress.py` — Progress tracking, database queries. New feature states go here.
- `security.py` — Bash command allowlist. Review agents need read-only access.

**MCP feature server:**
- `mcp_server/feature_mcp.py` — Feature management tools. New states (REVIEWED, QA_VERIFIED) go here.
- `api/database.py` — SQLAlchemy models. Feature model needs new status values.

**Prompt templates:**
- `.claude/templates/coding_prompt.template.md` — Existing coding agent prompt. Enhance with test generation.
- `.claude/templates/initializer_prompt.template.md` — Existing initializer prompt.

**React UI:**
- `ui/src/App.tsx` — Main app with kanban board. New QA states need columns/colors.
- `ui/src/hooks/useWebSocket.ts` — Real-time updates. New event types for QA status.
- `ui/src/lib/types.ts` — TypeScript types. Add new feature status types.
- `ui/src/components/AgentMissionControl.tsx` — Agent dashboard. Show QA agents.

**Server routers:**
- `server/routers/agent.py` — Agent control. Add QA agent start/stop.
- `server/routers/features.py` — Feature management API. New endpoints for QA status.

**Server services:**
- `server/services/process_manager.py` — Process lifecycle. New QA agent processes.

### Key Patterns to Follow

1. **New agent types** follow the same `agent.py` session loop — they get a prompt, a client config, and run as a subprocess.
2. **New CLI flags** go in `autonomous_agent_demo.py` argparse. Example: `--skip-review`, `--skip-qa`, `--qa-only`.
3. **New prompt templates** go in `.claude/templates/` as `.template.md` files with the same fallback chain.
4. **Feature status changes** go through the MCP server tools in `mcp_server/feature_mcp.py`.
5. **UI updates** flow through WebSocket events in `useWebSocket.ts`.
6. **Process management** for new agent types uses the existing `process_manager.py` pattern.

## Build Order

Implement features in this order (matches the handoff):

1. **Feature 1: Generated Playwright Test Scripts** — Enhance coding prompt to generate `.spec.ts` files
2. **Feature 2: Review Agent** — New agent type that does code review (read-only, no Playwright)
3. **Feature 3: Enhanced Regression Testing** — Run generated `.spec.ts` files during regression
4. **Feature 4: Final QA Agent** — New agent type that runs full QA sweep at the end
5. **Feature 5: QA Report Generator** — Structured report output after QA completes
6. **Feature 6: Feature State Machine Extension** — Add REVIEWED, QA_VERIFIED states
7. **Feature 7: UI Integration** — Kanban columns, progress indicators, QA controls
8. **Feature 8: Computer Use QA** — Claude Computer Use for exploratory testing (see computer-use-qa-handoff.md)

## What NOT To Do

- Do NOT create a new project — this goes into the EXISTING AutoForge codebase
- Do NOT modify the existing feature flow for non-QA builds — QA phases are OPTIONAL (toggled via flags)
- Do NOT break backward compatibility — existing `--yolo` mode, standard mode, and parallel mode must still work
- Do NOT add new pip dependencies unless absolutely necessary — check existing requirements.txt first
- Do NOT change database schema in a way that breaks existing features.db files

## Testing

After implementing each feature:
```bash
ruff check .                          # Lint
python test_security.py               # Security tests
python -m pytest test_client.py       # Client tests
cd ui && npm run build                # UI type check + build
```

## How to Verify Success

- Running `python autonomous_agent_demo.py --project-dir my-app` still works exactly as before (QA phases OFF by default)
- Running `python autonomous_agent_demo.py --project-dir my-app --qa` enables the full pipeline
- Running `python autonomous_agent_demo.py --project-dir my-app --review-only` runs just the review phase
- The UI shows new QA states in the kanban board when QA is enabled
- Generated `.spec.ts` files appear in the project's test directory
