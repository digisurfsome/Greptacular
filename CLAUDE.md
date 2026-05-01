# CLAUDE.md

## ⚠️ TIME ESTIMATION RULE — READ BEFORE GIVING ANY ETA ⚠️

**You output ~500,000 tokens per 30 minutes of straight coding.** To estimate task time:
`(tokens the task will produce ÷ 500,000) × 30 minutes`.

**NEVER quote human-coder timelines** (hours, days, weeks). A feature a human calls "1–2 hours" is usually **2–10 minutes** of agent time. Small scripts ≈ under a minute. Multi-file refactors ≈ minutes, not hours. Think in tokens, not humans.

## Owner
- NOT a coder. Plain language. Move fast.
- **Dev repo:** `c:\Users\lober\GitHub\Greptacular - AutoForge Build\Greptacular`
- **Live install:** `C:\Users\lober\Greptacular` (port 8888)
- Commit directly to `main`. No branches.
- AutoForge = autonomous coding agent system (React UI + Claude Agent SDK).

## Critical Rules
- **Always merge to `main`.** User pulls from `main`.
- **`ui/dist/` is gitignored.** `start_ui.bat` auto-rebuilds from source.
- **Sonnet builds, Opus reviews.** Never assign Opus as per-phase Reviewer. See `docs/SONNET_OPUS_OPTIMIZATION.md`.
- **Every command you give the owner MUST include the `cd` to the correct directory first.** Owner runs many parallel chats; no chat remembers the previous working directory. Always: `cd <repo-root>` then the command. No exceptions.

## File Maps — Use These Before Searching

- **Unified page index** (one row per page = all its files) → `docs/references/page-index.md`
- UI inventory → `ui/CLAUDE.md`
- Server inventory → `server/CLAUDE.md`
- Docs inventory → `docs/CLAUDE.md`

## Tool Efficiency — Mandatory
Full rules: `.claude/rules/tool-efficiency.md`. Short version: use the map, stay in your lane, max 3 exploratory searches, max 15 tool calls per single-page task.

### Subagent-First Rule (enforce this hard)
**Default:** for any search, file discovery, or code exploration, spawn an **Explore subagent** instead of searching in main context. Main context = the user's conversation; every Glob/Grep/Read result stays there forever. Subagents return a short summary and keep main context clean.

- **Use a subagent for:** finding files by pattern, searching where a symbol is used, understanding how a feature is wired across files, answering "is there code that does X?"
- **Stay in main context ONLY when:** the task requires multi-step decision-making with course correction between results, you already know the exact path (just Read it), or you're about to edit (subagents shouldn't edit except for scoped bulk work).

Default: subagent. Main-context exploration is the exception, not the rule.

## Where Docs Go — 3 Directories Only
- `docs/page-prds/{page-name}/` — PRDs, specs per page
- `docs/ideas/` — brainstorms
- `docs/info/` — research, guides, saved context

Never drop loose `.md` files in `docs/`. Create the page folder if missing.

## MANDATORY: Announce Where You Put Things

When you create or edit ANY file (docs, PRDs, notes, code), your user-facing response MUST include:
- The full file path
- The category (PRD | idea | info | code)
- A one-line summary of what you added

Example: *"Added PRD at `docs/page-prds/workspace/README.md` — spec for new chat persistence layer."*

The owner is not a coder. He cannot browse the file tree looking for what you did. If you don't announce the path, you failed the task. This applies to EVERY file operation, EVERY time.

## Mandatory Reads (ONLY if task applies)
- Task calls a Claude model or creates an SDK client → `docs/SUBSCRIPTION_AND_WEBSOCKET_GUIDE.md` + `docs/references/sdk-client-pattern.md`
- Task touches `useWorkspaceChat.ts` or `WorkspaceChat.tsx` → don't. One WebSocket per page, hook already exists.

## References (load only when needed)

| Topic | File |
|-------|------|
| Deploy chain (after code changes) | `docs/references/deploy-chain.md` |
| Market Scraper PRD | `docs/page-prds/market-scraper/README.md` |
| SDK client 3-bug pattern | `docs/references/sdk-client-pattern.md` |
| Architecture | `docs/references/architecture.md` |
| Commands | `docs/references/commands-reference.md` |
| Testing | `docs/references/testing-guide.md` |
| Security model | `docs/references/security-model.md` |
| AI providers | `docs/references/providers.md` |
| Emergency UI fix | `docs/references/emergency-ui-fix.md` |
| Subscription + WebSocket | `docs/SUBSCRIPTION_AND_WEBSOCKET_GUIDE.md` |
| Workspace UI standards | `ui/WORKSPACE_STANDARDS.md` |
| Activepieces (MCP, flows, auth) | `docs/ACTIVEPIECES.md` |
| New page checklist | `.claude/rules/new-page-standards.md` |
| Communication / walkie-talkie / tags | `docs/references/communication.md` |
| Token/tool control history + remaining levers | `docs/info/token-tool-control-history.md` |
| **Claude subscription from a Python script** (no API key — boilerplate + gotchas for standalone mining/extraction scripts) | `docs/info/claude-subscription-from-python-script.md` |

## After Edits
Commit changed files only (never `git add -A`). Clear message. Report files, hash, branch.
