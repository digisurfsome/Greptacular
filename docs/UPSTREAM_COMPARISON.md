# Upstream AutoForge vs Greptacular: Comparison & Update Plan

**Date:** 2026-02-25
**Upstream:** https://github.com/AutoForgeAI/autoforge (v0.1.15, Feb 23 2026)
**Local:** Greptacular (v0.1.8, heavily customized)

---

## Version Gap

| | Upstream (AutoForgeAI/autoforge) | Greptacular |
|---|---|---|
| package.json version | 0.1.15 | 0.1.8 |
| claude-agent-sdk | `>=0.1.39,<0.2.0` | `>=0.1.0,<0.2.0` |
| UI deps difference | has `@radix-ui/react-tooltip` | missing tooltip dep |

---

## Upstream Changes We're Missing

### 1. Graceful Pause / Drain Mode (Medium)
Agents finish current work before stopping, instead of hard-kill.
- `process_manager.py` - new `graceful_pause()`, `graceful_resume()`, states `pausing` → `paused_graceful`
- `server/routers/agent.py` - new `POST /agent/graceful-pause` and `/graceful-resume` endpoints
- UI `AgentControl` updated with pause/resume buttons

### 2. Human Input / Blocked-for-Input (Medium-High)
Agents pause and ask user for input via form (text, textarea, select, boolean).
- `server/routers/features.py` - `POST /{feature_id}/resolve-human-input`
- New types: `HumanInputField`, `HumanInputRequest`, `HumanInputResponseData`
- New component: `HumanInputForm.tsx`
- Feature model has `needs_human_input` field

### 3. Playwright MCP → CLI Migration (Medium)
Browser automation switched from Playwright MCP server to Playwright CLI.
- `client.py` - MCP config changes, `--isolated` flag for parallel mode
- New `.claude/skills/` playwright CLI skill

### 4. Azure Anthropic Provider (Low-Medium)
Azure added as API provider option.
- `client.py` - `get_effective_sdk_env()` handles Azure
- `server/routers/settings.py` - Azure in API_PROVIDERS
- `SettingsModal.tsx` updated

### 5. Read-Only MCP Tools for All Agents (Low)
Testing/initializer agents can access read-only MCP tools.
- `client.py` tool config changes

### 6. Rate Limit Fixes (Low)
Fixed false-positive rate limit detection, one-message-behind bug.
- `rate_limit_utils.py`, chat session files

### 7. Temp File Cleanup Fix (Low)
Prevents temp file accumulation during long runs.
- `temp_cleanup.py`

### 8. VISION.md (Trivial)
Policy doc declaring Claude Agent SDK exclusivity.

### 9. GLM 5 Model (Trivial)
Added GLM 5 to model list.

---

## Our Custom Additions (Not in Upstream)

### A. Workspace System (~25+ files) - MASSIVE
- Routers: `workspace.py`, `notifications.py`, `role_library.py`, `swarm.py`, `dunkstack.py`, `ci_status.py`, `design_guide.py`
- Services: `workspace_chat_session.py`, `workspace_database.py`, `workspace_github.py`, `workspace_library.py`, `workspace_repos.py`, `workspace_summary.py`, `workspace_token_encryption.py`, `swarm_orchestrator.py`, `ci_monitor.py`, `design_guide_session.py`
- Pages: `WorkspacePage.tsx`, `DunkStackPage.tsx`, `RoleLibraryPage.tsx`
- 25+ workspace UI components, 9+ workspace hooks

### B. Boilerplate / Style System (~10+ files)
- Services: `boilerplate_manager.py`, `style_extractor.py`, `style_manager.py`, `style_modifiers.py`
- Components: `ColorCustomizer.tsx`, `PaletteStrip.tsx`, `StylePreview.tsx`, etc.
- Data: `fonts.ts`, `palettes.ts`, `refinementOptions.ts`

### C. CI/CD & Pipeline Features
- `ci_status.py`, `ci_monitor.py`, `PipelineStatusBadge.tsx`, `CIStatusWidget.tsx`
- Extra GitHub workflows: `ci-auto-fix.yml`, `ci-failure-notify.yml`

### D. DunkStack / Agent Comms
- `DunkStackPage.tsx` + 3 dunkstack components
- `.agent/` directory

### E. Misc
- `computer_use.py`, `GitActivityWidget.tsx`, deployment files (Docker, Procfile, nixpacks)
- `tools/preview-generator/`, `scripts/always-on/`, `blueprints/`, `handoffs/`, `docs/`
- `cryptography` dependency

---

## High-Risk Shared Files (Both Modified)

| File | Risk | Notes |
|---|---|---|
| `client.py` | HIGH | Ours has computer_use; theirs has Playwright CLI, Azure, MCP changes |
| `server/routers/agent.py` | HIGH | Theirs adds pause/drain/resume endpoints |
| `server/routers/features.py` | HIGH | Theirs adds human-input endpoint |
| `server/services/process_manager.py` | HIGH | Theirs adds graceful pause machinery |
| `ui/src/App.tsx` | HIGH | Both significantly changed |
| `ui/src/lib/types.ts` | HIGH | Both have significant type additions |
| `server/schemas.py` | MEDIUM | Schema differences |
| `ui/src/components/AgentControl.tsx` | MEDIUM | Theirs has pause/drain UI |
| `ui/src/components/SettingsModal.tsx` | MEDIUM | Theirs has Azure provider |
| `agent.py` | MEDIUM | Core agent loop |

---

## Effort Estimate

| Approach | Effort | Risk |
|---|---|---|
| **A) Port upstream changes INTO ours** | Medium (~2-3 days) | Low - surgical additions |
| **B) Port OUR changes onto fresh upstream** | Very High (~1-2 weeks) | High - workspace is massive |
| **C) Fresh upstream, rebuild later** | None now, High later | Lose all customizations |

---

## Recommended: Option A - Checklist

- [ ] Update `claude-agent-sdk` minimum to `>=0.1.39` in requirements.txt
- [ ] Add graceful pause/drain to `server/services/process_manager.py`
- [ ] Add pause/resume endpoints to `server/routers/agent.py`
- [ ] Add human input resolve endpoint to `server/routers/features.py`
- [ ] Add `HumanInputForm.tsx` component to UI
- [ ] Update `client.py` for Playwright CLI migration, Azure support, read-only MCP
- [ ] Add Azure provider to `server/routers/settings.py`
- [ ] Apply rate limit fixes to `rate_limit_utils.py` and chat sessions
- [ ] Add `@radix-ui/react-tooltip` to UI deps
- [ ] Update `ui/src/lib/types.ts` with human input types + pause states
- [ ] Add `VISION.md`
- [ ] Bump `package.json` version to 0.1.15
