# Agent Brief 2: Storage, Prompts & Display Systems

**Phases:** Package 2 from `docs/prd-cli-scripter-v2.md`
**Scope:** React UI + Python backend — build config storage, prompt bars, pipeline cards, parallel waves, deterministic scripts
**Estimated Tokens:** ~70-85k
**Dependencies:** Package 1 must be complete (persistence, rules library exist in codebase)
**Must Complete Before:** Agent 3

---

## YOUR JOB

Read the full PRD at `docs/prd-cli-scripter-v2.md`. Package 1 has already been built — its code is in the codebase. Read it first to understand what exists. Build these 8 phases IN ORDER. After EVERY phase: run `cd ui && npm run build` — zero TypeScript errors. Commit after each phase.

## BUILD ORDER

| Order | Phase | What | Difficulty |
|-------|-------|------|-----------|
| 1 | Phase 7 | SQLite config storage (build configs with full state snapshots) | 2/10 |
| 2 | Phase 8 | Build Library UI (save/load/delete build configs, search, timestamps) | 3/10 |
| 3 | Phase 9 | Queue management upgrade (reorder, status badges, dependency handling) | 3/10 |
| 4 | Phase 12 | PromptBar component (lock icon, inline edit, collapse/expand per prompt) | 2/10 |
| 5 | Phase 13 | Prompt persistence in Build Storage (save edited prompts with configs) | 1/10 |
| 6 | Phase 14 | Pipeline card component (replace unusable text list with visual cards) | 2/10 |
| 7 | Phase 15 | Parallel wave parser + CLI script generation for concurrent phases | 3/10 |
| 8 | FIX | Deterministic script templates (Python string formatting, no LLM) | 2/10 |

## KEY FILES

| File | What |
|------|------|
| `ui/src/pages/CliScripterPage.tsx` | Main page |
| `server/routers/cli_scripter.py` | Backend API — add config CRUD, wave generation |
| `ui/src/components/` | New: PromptBar, PhaseCard, BuildLibrary |
| `ui/src/lib/` | New: waveParser.ts |
| `ui/src/hooks/usePersistedState.ts` | Already built by Agent 1 — use it |

## WHAT AGENT 1 ALREADY BUILT

- `usePersistedState` hook — localStorage persistence for all form fields
- ClearButton component — ✕ icons on all inputs
- Phase Assignments read-only output + Regenerate button
- ProjectFileBrowser component (2 spots)
- RuleBlock component with named blocks, tags, checkboxes
- Combiner with two-way binding
- Gate popup (single/split + new build/edit mode)
- Backend rule persistence

## RULES

- Read each phase's PRD section BEFORE building
- Match existing patterns: neobrutalism, Tailwind v4, React 19, TanStack Query, Radix UI
- Do NOT restructure page layout — surgical additions
- Stay under 50% context window (100k tokens)

## WHEN DONE

Commit with: `feat(cli-scripter): Package 2 — storage, prompts, estimate cards, parallel waves, deterministic fix`
Do NOT push to remote.
