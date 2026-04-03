# Task: Install Token Optimization System

> **Give this prompt to a workspace agent in AutoForge.**
> **Scope:** This is a quick install task — merge a branch and verify files are in place.
> **Expected tool calls:** Under 10. Do NOT explore the codebase. Follow these steps exactly.

---

## What You're Doing

The branch `claude/define-app-archetypes-mZyRD` has 6 files that cut token waste by 30-50%. Your job is to merge them into main so they take effect for all future agents.

## Step 1: Merge the Branch

```bash
git fetch origin claude/define-app-archetypes-mZyRD
git checkout main
git merge origin/claude/define-app-archetypes-mZyRD --no-edit
git push origin main
```

If there are merge conflicts, resolve them by keeping the NEW files (from the branch). These are all new files — there should be no conflicts.

## Step 2: Verify These 6 Files Exist

Read the first 5 lines of each to confirm they landed:

1. **`.claude/rules/tool-efficiency.md`** — Tool usage rules (max 3 exploratory searches, batch reads, stay in your lane)
2. **`.claude/rules/new-page-standards.md`** — Standards for building new pages
3. **`ui/CLAUDE.md`** — File map: every page, component, hook, and utility in the UI
4. **`server/CLAUDE.md`** — File map: every router and service in the backend
5. **`docs/CLAUDE.md`** — File map: docs directory with "don't read this" guidance
6. **`docs/optimization-tracker.md`** — Master optimization checklist

If any file is missing, check `git log --oneline -5` to confirm the merge happened.

## Step 3: Verify Rules Auto-Load

Files in `.claude/rules/` are automatically loaded by Claude Code for every session in this repo. Confirm by checking that `.claude/rules/` exists and contains `tool-efficiency.md` and `new-page-standards.md`.

No code changes needed. No UI changes. No server changes. Just the merge.

## What These Files Do (For Your Understanding — Don't Modify Them)

### tool-efficiency.md (the big one)
This file gets auto-loaded into every agent's context. It enforces:
- **Read the map first** — Before using Glob or Grep, read the CLAUDE.md in the relevant directory
- **Stay in your lane** — If your task is about one page, only touch that page's files
- **Max 3 exploratory searches** — If you haven't found it in 3 Glob/Grep calls, re-read the map or ask the human
- **Read only what you need** — Files over 100 lines: use offset/limit. Never read a 2000-line file when you need one function
- **No unnecessary verification** — Don't Read a file after Edit to "check" it worked
- **No drive-by improvements** — Don't refactor code you encounter while working
- **Batch reads** — Read multiple files in one turn, not one at a time
- **Token budget awareness** — Target under 15 tool calls for a single-page task

### CLAUDE.md file maps
These replace exploration. Instead of:
```
Glob **/*.tsx → 50 results → Read 5 files → figure out which one is right
```
The agent does:
```
Read ui/CLAUDE.md → sees exact path → Read that one file
```

That's the difference between 7 tool calls and 2 tool calls, multiplied by every task.

## Do NOT Do Any of These Things
- Do NOT modify the files you just merged
- Do NOT explore the codebase
- Do NOT run builds or tests
- Do NOT read files other than the 6 listed above
- Do NOT create any new files

This is a merge-and-verify task. Should take under 5 minutes.

---

## Also on the Branch (Bonus — Already Merged With the Above)

These files are also useful but not the "giant token burners":
- `docs/prd-index.md` — Index of all 44 PRDs in the repo
- `docs/page-prds/workspace/prd-optimization-agents.md` — Full PRD for the optimization dashboard, rant compressor, task scout, and org agent (build these later)

---

## Complementary Changes (Already on Main)

These edits were made alongside the branch merge to tighten agent configs:

### `.claude/settings.json`
- Changed `effortLevel` from `"high"` to `"medium"`

### `CLAUDE.md` — New "Tool Use Budget" section
- Hard cap: 10 exploratory tool calls before producing output
- Parallel reads preferred, no speculative exploration

### `.claude/agents/coder.md` — Tightened Phase 1
- Research phase capped at 8 tool calls max
- Removed speculative exploration defaults

### `.claude/agents/deep-dive.md`
- Replaced "USE THEM EXTENSIVELY" with "USE THEM EFFICIENTLY"
- 15-call budget for exploration phase

### `.claude/agents/code-review.md`
- Scoped to files under review + direct imports only
