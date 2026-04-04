# PRD: Pipeline Judge Agent — Quality Gate Between Stages

> **Status:** Draft — build after [STAGE_COMPLETE] pipeline flow is confirmed working
> **Date:** 2026-04-04

---

## Overview

A dedicated judging agent sits between every stage of the pipeline. After a skill produces its output and signals [STAGE_COMPLETE], the judge evaluates the output against the skill's contract before allowing advancement to the next stage.

## Flow

```
Skill N runs → outputs JSON + [STAGE_COMPLETE]
    ↓
Judge Agent receives:
  - The skill's contract/criteria (what "done" looks like)
  - The skill's output (the JSON)
  - The scoring rubric
    ↓
Judge scores: 5 dimensions × 20 points = /100
    ↓
Score ≥ 80? → PASS → Feed output to Skill N+1
Score < 80? → FAIL → Send back to Skill N with:
  1. "This did not meet the quality threshold."
  2. The specific critique (what failed, what's missing)
  3. "Redo this stage. Focus on the critique above."
    ↓
Skill N runs again with critique prepended
    ↓
Judge evaluates again
    ↓
Max 2 retries. If fails 3 times → flag for human review, pipeline pauses.
```

## Judge Agent Prompt Template

```
You are a quality gate judge for a pipeline stage. Your ONLY job is to
score the output against the contract criteria. You do NOT produce any
content — you only evaluate.

## Contract Criteria for Stage {N}: {label}

{contract_text — extracted from the skill's contract section}

## Output to Evaluate

<stage_output>
{the JSON output from the stage}
</stage_output>

## Scoring Rubric

Score each dimension 0-20:

| Dimension | Description |
|-----------|-------------|
| Completeness | All required fields populated, no nulls, no TBDs |
| Accuracy | Values are correct, consistent, and make sense |
| Consistency | No contradictions between fields |
| Specificity | Named values, not vague placeholders |
| Handoff Readiness | Next stage can consume this without asking questions |

## Your Response Format

```json
{
  "score": <total 0-100>,
  "dimensions": {
    "completeness": <0-20>,
    "accuracy": <0-20>,
    "consistency": <0-20>,
    "specificity": <0-20>,
    "handoff_readiness": <0-20>
  },
  "pass": <true if score >= 80, false otherwise>,
  "critique": "<if fail: specific problems to fix. if pass: empty string>",
  "missing_fields": ["<list of any required fields that are empty or missing>"],
  "contradictions": ["<list of any contradictions found>"]
}
```

Be strict but fair. The purpose is quality, not perfection.
```

## Retry Message Template (prepended to skill prompt on retry)

```
## ⚠️ QUALITY GATE FAILURE — Redo Required

Your previous output for this stage did not meet the quality threshold.

**Score:** {score}/100 (threshold: 80)

**Critique:**
{critique}

**Missing fields:** {missing_fields}
**Contradictions:** {contradictions}

Redo this stage completely. Address every point in the critique above.
Do NOT repeat the same mistakes. Produce a complete, correct output
that meets the contract criteria.

Your original instructions follow below — execute them again with the
critique in mind.

---

```

## Implementation

### Option A: Separate Judge Agent (Recommended)
- One dedicated WorkspaceChatSession for the judge
- Lightweight — only receives contract + output, not the full skill
- ~10-20K tokens per judgment
- Same judge agent session for all stages (it builds context of the whole pipeline)
- Uses Sonnet (fast, cheap) instead of Opus for judging

### Option B: Next Skill Judges Previous (Simpler, Not Recommended)
- Prepend judging instructions to the beginning of the next skill
- Compromises the next skill's focus
- Mixes two different objectives in one prompt
- Harder to retry (would need to undo the next skill's work)

### Token Budget
- Judge prompt: ~2K tokens (rubric + instructions)
- Contract text: ~1-3K tokens per stage
- Output to evaluate: ~5-20K tokens (the JSON)
- Judge response: ~500 tokens (score + critique)
- Total per judgment: ~10-25K tokens
- 11 stages × ~15K average = ~165K tokens for judging (using Sonnet = cheap)

### Configuration
- Toggle: enable/disable judge (default: enabled)
- Threshold: configurable score cutoff (default: 80)
- Max retries: configurable (default: 2)
- Judge model: configurable (default: Sonnet for speed/cost)
- Per-stage contracts: loaded from skill files or a separate contracts file

### Pipeline Panel UI Additions
- Toggle: "Quality Gate" on/off
- Threshold slider: 70-95
- Max retries: 1-3
- Show judge results in output viewer: score badge per stage
- On failure: show critique in amber warning box

## Files to Create/Modify
- `server/services/pipeline_judge.py` — Judge agent logic
- `server/services/pipeline_orchestrator.py` — Add judge step between stages
- `ui/src/components/workspace/PipelinePanel.tsx` — Quality gate toggle + settings
- `ui/src/components/workspace/PipelineOutputViewer.tsx` — Score badges + critique display

## Dependencies
- [STAGE_COMPLETE] mechanism must be working first
- Pipeline must successfully chain stages before adding judge layer
