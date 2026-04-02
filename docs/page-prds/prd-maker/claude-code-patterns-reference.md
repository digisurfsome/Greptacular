# Claude Code Source — Patterns Applicable to PRD Maker Pipeline

> **Source:** Claude Code CLI source analysis (TypeScript, ~512K lines)
> **Purpose:** Patterns from Claude Code's internal architecture that validate and inform our pipeline design
> **Date:** 2026-04-02

---

## 1. Planning Mode: 5-Phase Workflow

Claude Code's planning mode follows a structured process:

1. **Initial Understanding** — Read code, search patterns, ask questions, launch 1-3 Explore agents IN PARALLEL
2. **Design** — Launch 1-3 Plan agents (read-only), each considers different approaches
3. **Synthesis** — Model reads all findings, creates unified synthesis
4. **Final Plan** — Write plan to single file (only file editable in plan mode)
5. **Approval** — User reviews, approves or rejects

**Our application:** Stage 2 (Gap Analysis) should launch parallel explorations of mechanism categories, synthesize findings, then ask targeted questions.

---

## 2. Synthesis-First Architecture (CRITICAL PATTERN)

From coordinator mode:

> **Never delegate work with "based on findings" phrasing. Always synthesize understanding into specific prompts with exact file paths, line numbers, what to change, and why.**

**Our application:** Every stage handoff must prove it understood the previous stage's output. No "based on the gap analysis, extract mechanisms" — instead "the gap analysis identified mechanisms C (data processing), H (integration), and L (monetization). Extract each using the A-N framework sub-questions."

---

## 3. Context Window Management

Compaction constants:
```
POST_COMPACT_TOKEN_BUDGET = 50,000
POST_COMPACT_MAX_FILES_TO_RESTORE = 5
POST_COMPACT_MAX_TOKENS_PER_FILE = 5,000
POST_COMPACT_MAX_TOKENS_PER_SKILL = 5,000
POST_COMPACT_SKILLS_TOKEN_BUDGET = 25,000
```

After compaction: conversation replaced with ~50K summary + up to 5 files (5K each) + skills truncated.

**Our application:**
- Stage skills MUST be under 500 lines / 5K tokens (matches Nate's rule)
- Long reference material goes in references/ subfolder, not the SKILL.md body
- Context packet snapshots saved to disk (not conversation memory)

---

## 4. Verification as Independent Lens

> Spawn DEDICATED verification worker. Give it: original request + changed files + approach. Do NOT give it test results (prevents anchoring bias).

**Our application:** Stage 9 verification agent gets the spec and the code, but NOT the builder agent's reasoning or self-assessment. Fresh eyes, no confirmation bias.

---

## 5. Parallel vs Sequential Execution Rules

- Read-only tasks: Run in parallel freely
- Write-heavy tasks: One at a time per file set
- Verification: Can parallel across different file areas

**Our application:**
- Stage 0 substeps (0A-0D): parallel (all reads/decisions)
- Build phases (7+): sequential per phase
- Testing (11A/B/C): 11A sequential, 11B/C can parallel after 11A passes

---

## 6. Structured Question Pattern (AskUserQuestion)

Capabilities:
- 2-4 multiple-choice options
- Single or multi-select
- Optional previews (markdown/HTML/ASCII mockups)
- "Other" always available for custom input

**Our application:** All human-facing questions in Stages 0-2 should be structured choices, not open-ended. Reduces friction, increases completion rate, prevents the "three sentences and done" problem by making it easy to answer.

---

## 7. When to Plan vs When to Just Do It

Planning mode triggers when:
- Architectural ambiguity exists (multiple valid approaches)
- Unclear requirements need exploration
- High-impact restructuring
- Multi-file changes (3+ files)
- User preferences matter

Skip planning when:
- Single-line/few-line fixes
- Very specific instructions given
- Pure research tasks

**Our application:** Not every app idea needs the full 10-stage pipeline. Simple tools (single CRUD entity, no complex mechanisms) could have a "fast path" that skips Stages 4-5 (mechanism extraction + scaffolding) and goes straight to layout/phasing. This matches the "free tier = 3-5 questions kicking out one flat prompt" concept from the stage extractions.

---

## 8. Modular Prompt Composition

System prompt built from sections with explicit cache boundary:
- Static sections (globally cacheable across users/sessions)
- Dynamic sections (recomputed every turn, user-specific)
- Explicit `SYSTEM_PROMPT_DYNAMIC_BOUNDARY` marker separating them

**Our application:** The structural preamble (Martin's agnostic checklist) is STATIC — same for every stage. The context packet contents are DYNAMIC — change every stage. Keeping them separate means the static parts can be cached/reused efficiently.

---

## Summary: What This Validates

| Our Design Decision | Claude Code Does The Same Thing |
|---|---|
| Modular stages with clean handoffs | Coordinator → workers → verification |
| Parallel exploration, sequential execution | Read parallel, write sequential |
| Contracts/success criteria per stage | Workers get explicit success criteria |
| Context packet as structured data bus | Coordinator synthesizes before delegating |
| Independent verification agent | Verifier gets no builder reasoning |
| Escape hatch / save state | Workers save artifacts before reporting |
| Skills under 500 lines | Skills truncated to 5K tokens in compaction |

**We're not inventing a new pattern — we're applying Claude Code's own internal architecture to PRD generation.**
