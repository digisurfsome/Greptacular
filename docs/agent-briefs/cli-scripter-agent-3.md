# Agent Brief 3: Dashboard, Terminal, Boilerplate & Sketches

**Phases:** Package 3 from `docs/prd-cli-scripter-v2.md`
**Scope:** React UI + Python backend — live build monitoring, embedded terminal, boilerplate docs, architectural sketch system
**Estimated Tokens:** ~80-95k
**Dependencies:** Packages 1 and 2 must be complete
**Must Complete Before:** Agent 4 (verification)

---

## YOUR JOB

Read the full PRD at `docs/prd-cli-scripter-v2.md`. Packages 1 and 2 have already been built — their code is in the codebase. Read it first to understand what exists. Build these 10 phases IN ORDER. After EVERY phase: run `cd ui && npm run build` — zero TypeScript errors. Commit after each phase.

## BUILD ORDER

| Order | Phase | What | Difficulty |
|-------|-------|------|-----------|
| 1 | Phase 1 | Backend process manager (subprocess lifecycle, PID tracking) | 3/10 |
| 2 | Phase 2 | Progress parser (regex extraction from Claude CLI stdout) | 2/10 |
| 3 | Phase 3 | Dashboard UI strip (progress bars, agent status, phase indicators) | 3/10 |
| 4 | Phase 4 | Embedded terminal panel (xterm.js, WebSocket to pty) | 3/10 |
| 5 | Phase 5 | Phase status sidebar (clickable phase list with live status icons) | 2/10 |
| 6 | Phase 6 | Refresh interval selector (auto-refresh rate control) | 1/10 |
| 7 | Phase 10 | Boilerplate analysis docs (framework detection, structure templates) | 1/10 |
| 8 | Phase 11 | Prep phase for dual builds (boilerplate + fresh project support) | 2/10 |
| 9 | Phase 24 | Cartographer prompt enhancement — ASCII wireframe sketches for all pages | 2/10 |
| 10 | Phase 25 | Verifier prompt enhancement — sketch-aware testing + visual match report | 1/10 |

## KEY FILES

| File | What |
|------|------|
| `ui/src/pages/CliScripterPage.tsx` | Main page |
| `server/routers/cli_scripter.py` | Backend API — add process management, build status |
| `ui/src/components/` | New: BuildDashboard, EmbeddedTerminal, PhaseSidebar |
| `ui/src/components/Terminal.tsx` | EXISTING terminal component — reuse for embedded terminal |
| `ui/src/hooks/useWebSocket.ts` | EXISTING WebSocket hook — reuse for streaming |

## WHAT AGENTS 1-2 ALREADY BUILT

Agent 1: Persistence layer, clear buttons, file browser, rules library with combiner + gate popup
Agent 2: Build config storage (SQLite), build library UI, queue management, prompt bars, pipeline cards, wave parser, deterministic scripts

## RULES

- Read each phase's PRD section BEFORE building
- Reuse existing components where possible (Terminal.tsx, useWebSocket.ts)
- Match existing patterns: neobrutalism, Tailwind v4, React 19, TanStack Query, Radix UI
- Do NOT restructure page layout — surgical additions
- Stay under 50% context window (100k tokens). This package has 10 phases — prioritize getting them all done over perfection on any single one.

## WHEN DONE

Commit with: `feat(cli-scripter): Package 3 — dashboard, terminal, boilerplate, architectural sketches`
Do NOT push to remote.
