# AutoForge - CLAUDE.md (Leon's Master Project Reference)

> **Source**: `/CLAUDE.md` in the AutoForge/Greptacular repository
> **Role**: Master project reference document - automatically loaded by Claude Code for every session
> **Lines**: ~509

---

This is the complete CLAUDE.md from AutoForge. It serves as the single source of truth for project architecture, module map, technology stack, testing, security, and operational patterns.

See the actual file at the repository root: `/CLAUDE.md`

## What This Document Controls

- **Project Architecture**: Complete module map of all Python and React components
- **Technology Stack**: Python 3.11+ (FastAPI, SQLAlchemy), React 19 (TypeScript, Vite 7, TanStack Query, Tailwind CSS v4, Radix UI)
- **Testing Commands**: ruff, mypy, eslint, Playwright E2E, pytest
- **Design System**: Neobrutalism with custom CSS variable tokens and animations
- **Security Model**: Defense-in-depth with hierarchical bash command allowlists (hardcoded blocklist > org blocklist > org allowlist > global allowlist > project allowlist)
- **Real-time Updates**: WebSocket protocols for progress, agent status, logs, feature updates
- **Agent Session Flow**: How agents orient, implement, verify, and hand off work
- **Prompt Loading**: Fallback chain from project-specific to base templates
- **Parallel Mode**: Multi-agent orchestration with atomic feature claiming
- **MCP Integration**: Feature management tools exposed via MCP server
- **npm CLI**: Node.js wrapper for Python environment and server lifecycle management
- **Project Registry**: SQLite-based name-to-path mapping for cross-platform project storage

## Key Patterns Defined

1. **Prompt Loading Fallback Chain**: Project-specific prompts > Base templates
2. **Agent Session Flow**: Check features.db > Create client > Send prompt > Auto-continue
3. **Real-time UI Updates**: WebSocket messages (progress, agent_status, log, feature_update, agent_update)
4. **Parallel Mode**: Atomic feature claiming, dependency-aware scheduling, isolated browser contexts
5. **Process Limits**: MAX_PARALLEL_AGENTS=5, MAX_TOTAL_AGENTS=10
