# Token Optimization Brief — 50% Tool Use Reduction

**Date:** 2026-04-03
**Goal:** Cut exploratory tool calls (Glob, Grep, Read, WebSearch, WebFetch) by ~50% across all agent sessions.

## Problem

Agents are burning tokens on redundant exploration:
- Coder agent reads 20+ files before writing 1 line
- Deep-dive agent told to "leave no stone unturned" — explores tangential code
- No ceiling on tool calls before producing output
- `effortLevel: "high"` in settings.json maximizes tool use by default
- CLAUDE.md had no exploration guardrails at all

## Changes Made

### 1. `.claude/settings.json`
- Changed `effortLevel` from `"high"` to `"medium"` — reduces default tool use intensity

### 2. `CLAUDE.md` — New "Tool Use Budget" section
- Hard cap: **10 exploratory tool calls** before producing output (read/glob/grep/search)
- Must use project structure (already in CLAUDE.md) before reaching for tools
- Parallel tool calls preferred (1 message with 3 reads > 3 messages with 1 read)
- No speculative exploration — only read files you have a reason to read
- Web search only when the task explicitly requires external info

### 3. `.claude/agents/coder.md` — Tightened Phase 1
- Research phase capped at 8 tool calls max
- Removed "look for README, CLAUDE.md" (already loaded in context)
- Removed "research external dependencies" as default — only when needed
- Added: "If project structure in CLAUDE.md tells you where the file is, go directly"

### 4. `.claude/agents/deep-dive.md` — Removed "leave no stone unturned"
- Replaced "USE THEM EXTENSIVELY" with "USE THEM EFFICIENTLY"
- Added tool call budget: 15 max for exploration phase
- Removed "explore tangentially related things anyway"
- Added: "Stop exploring when you have enough to answer the question"

### 5. `.claude/agents/code-review.md` — Minor tightening
- Added: "Read only the files under review plus direct imports — not the whole codebase"

## Expected Impact

| Metric | Before | After |
|--------|--------|-------|
| Avg tool calls per coder session | ~30-40 | ~15-20 |
| Avg tool calls per deep-dive | ~40-60 | ~20-30 |
| Avg tool calls per code-review | ~15-20 | ~10-12 |
| Token cost per session | Baseline | ~50% reduction |

## Rollback

If agents start missing context they need:
1. Bump `effortLevel` back to `"high"` in `.claude/settings.json`
2. Remove the tool call caps from agent configs
3. Remove the "Tool Use Budget" section from CLAUDE.md
