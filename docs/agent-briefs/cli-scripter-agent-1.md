# Agent Brief 1: Foundation & UX Fixes

**Phases:** Package 1 from `docs/prd-cli-scripter-v2.md`
**Scope:** React UI + Python backend — persistence, clear buttons, file browser, rules library
**Estimated Tokens:** ~70-85k
**Dependencies:** None (this agent goes first)
**Must Complete Before:** Agents 2, 3, and 4

---

## YOUR JOB

Read the full PRD at `docs/prd-cli-scripter-v2.md`. Build these 8 phases IN ORDER. After EVERY phase: run `cd ui && npm run build` — zero TypeScript errors. Commit after each phase.

## BUILD ORDER

| Order | Phase | What | Difficulty |
|-------|-------|------|-----------|
| 1 | Phase 20 | `usePersistedState` hook + migrate ~30 useState calls to localStorage | 2/10 |
| 2 | Phase 21 | Clear buttons (✕ icon) on all text inputs and textareas | 1/10 |
| 3 | Phase 22 | Phase Assignments → read-only output + Regenerate button | 1/10 |
| 4 | Phase 23 | ProjectFileBrowser component in 2 spots + backend git endpoint | 3/10 |
| 5 | Phase 16 | RuleBlock component (named blocks, tags, checkboxes, sidebar rail) | 3/10 |
| 6 | Phase 17 | Combiner component + two-way checkbox binding with RuleBlocks | 3/10 |
| 7 | Phase 18 | Gate popup (single/split + new build/edit mode) + Send-to-Combiner | 3/10 |
| 8 | Phase 19 | Backend rule persistence (SQLite or JSON) + load/save endpoints | 2/10 |

## KEY FILES

| File | What |
|------|------|
| `ui/src/pages/CliScripterPage.tsx` | Main page — most UI changes go here (~1,976 lines) |
| `server/routers/cli_scripter.py` | Backend API (~472 lines) |
| `ui/src/components/` | New components: RuleBlock, Combiner, GatePopup, ClearButton, ProjectFileBrowser |
| `ui/src/hooks/` | New hook: usePersistedState |
| `server/main.py` | FastAPI app — update if adding new routers |

## RULES

- Read each phase's PRD section BEFORE building
- Read existing source files to understand current patterns
- Match existing patterns: neobrutalism design, Tailwind CSS v4, React 19, TanStack Query, Radix UI, orange accent
- Do NOT restructure the page layout — surgical additions only
- Do NOT add npm dependencies without checking if existing packages cover the need
- Stay under 50% context window (100k tokens). If running low, commit what you have.

## WHEN DONE

Commit with: `feat(cli-scripter): Package 1 — persistence, UX fixes, rules library`
Do NOT push to remote.
