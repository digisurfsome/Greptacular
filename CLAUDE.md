# CLAUDE.md

## Owner Context
- Owner is NOT a coder. Plain language. Move fast.
- **Dev repo:** `c:\Users\lober\GitHub\Greptacular - AutoForge Build\Greptacular`
- **Live install:** `C:\Users\lober\Greptacular` (port 8888)
- Commit directly to `main`. No branches.
- AutoForge: autonomous coding agent system with React UI + Claude Agent SDK.

## Deploy Chain (after every server/UI code change)
1. `cd ui && npm run build` (in dev repo)
2. `git push origin main`
3. `cd C:\Users\lober\Greptacular && git pull origin main --no-edit`
4. Kill python processes, restart `start_ui.bat`
5. Ctrl+Shift+R in browser

## Critical Rules — Violating These Causes Real Damage

- **Always merge to `main`.** User pulls from main, not feature branches.
- **`ui/dist/` is gitignored.** `start_ui.bat` auto-rebuilds. Source changes alone fix the UI.
- **Sonnet builds, Opus reviews.** Never assign Opus to per-phase Reviewer role. See `docs/SONNET_OPUS_OPTIMIZATION.md`

## ⚠️ MANDATORY READS — Before Calling AI Models or Editing Pages

**If your task calls an AI model, creates an SDK client, or adds/edits a UI page, you MUST read these files first. Not optional. Not "if you have time." MUST.**

1. **Subscription vs API Key Auth** → `docs/SUBSCRIPTION_AND_WEBSOCKET_GUIDE.md`
   EVERY Claude call MUST use subscription auth (`force_subscription=True`). Never use API keys for subscription models. The guide has code examples, good/bad patterns, and pre-commit checks. Agents have failed this 20+ times — read the full doc before writing a single line.

2. **SDK Client Pattern (3 Bugs)** → `docs/references/sdk-client-pattern.md`
   Never use `bypassPermissions` (crashes CLI). Always wrap `receive_response()` in try/except. Always pass `on_progress` callbacks. 20+ agents missed these stacked bugs. Read the doc, copy the working pattern from `yt_processor.py._call_via_sdk()`.

3. **WebSocket Rule** → `docs/SUBSCRIPTION_AND_WEBSOCKET_GUIDE.md` (WebSocket section)
   ONE WebSocket per page. Do NOT create new connections. Do NOT modify `useWorkspaceChat.ts` or `WorkspaceChat.tsx`. The hook and component already exist — build around them.

## File Maps — Read BEFORE Exploring

Find files here instead of searching:
- **UI files:** `ui/CLAUDE.md` — every page, component, hook, utility
- **Server files:** `server/CLAUDE.md` — every router, service, database model
- **Docs:** `docs/CLAUDE.md` — doc structure and PRD locations

## 🚨 ALL PAGE PRDs LIVE IN `docs/page-prds/` 🚨

```
┌─────────────────────────────────────────────────────────────────────┐
│  EVERY page has a PRD folder: docs/page-prds/{page-name}/          │
│  ALL specs, features, file maps, and design docs go THERE.         │
│  If the folder doesn't exist, CREATE IT before writing anything.   │
│  Index: docs/page-prds/README.md                                   │
└─────────────────────────────────────────────────────────────────────┘
```

Check `docs/page-prds/README.md` BEFORE modifying any page. If your page isn't listed, add it.

## References — Read ONLY When Your Task Needs It

| Topic | File |
|-------|------|
| SDK client bugs (3-bug fix pattern) | `docs/references/sdk-client-pattern.md` |
| Full architecture + key patterns | `docs/references/architecture.md` |
| Commands (CLI, npm, Python, UI) | `docs/references/commands-reference.md` |
| Testing (Python, React, CI/CD) | `docs/references/testing-guide.md` |
| Security model + allowed commands | `docs/references/security-model.md` |
| AI providers (Vertex, Ollama, etc.) | `docs/references/providers.md` |
| Emergency UI fix | `docs/references/emergency-ui-fix.md` |
| Subscription + WebSocket protocol | `docs/SUBSCRIPTION_AND_WEBSOCKET_GUIDE.md` |
| Workspace UI standards | `ui/WORKSPACE_STANDARDS.md` |
| **Activepieces (MCP, flows, auth, setup)** | **`docs/ACTIVEPIECES.md`** |

## After Edits
Commit changed files only (never `git add -A`). Clear message. Don't push. Report files, hash, branch.
