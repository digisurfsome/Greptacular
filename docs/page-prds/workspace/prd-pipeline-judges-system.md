# PRD: Pipeline Judge System — Three Levels of Quality Control

> **Status:** Ready to build (after pipeline flow is confirmed)
> **Date:** 2026-04-05
> **Dependency:** Requires working prompt chain pipeline with [STAGE_COMPLETE] mechanism

---

## Overview

Three independent judging layers that can be enabled individually or together. Each solves a different problem:

1. **Stage Judge** — "Did this one stage produce good output?"
2. **Run Judge** — "Did the entire pipeline run produce a coherent result?"
3. **Cross-Run Judge** — "Are the prompts improving across multiple runs?"

All three are separate from the pipeline itself. They plug in as optional quality gates.

---

## Level 1: Stage Judge

### What It Does
Sits between every stage. After a stage outputs `[STAGE_COMPLETE]`, the judge evaluates the output against the stage's contract before the pipeline advances.

### Flow
```
Skill N → [STAGE_COMPLETE] → Stage Judge evaluates
    → Score ≥ threshold? 
        → YES → Feed output to Skill N+1
        → NO  → Send back to Skill N with critique
                 (max 2 retries, then flag for human)
```

### Judge Agent Configuration
- **Model:** Sonnet (fast, cheap — judging doesn't need Opus)
- **Context:** Contract criteria + stage output only (~10-25K tokens per judgment)
- **One session per pipeline run** — judge builds context as it sees more stages
- **OR fresh session per judgment** — cleaner but no cumulative context

### Judge Prompt Template
```
You are a quality gate judge. Your ONLY job is to score output against criteria.
Do NOT produce content — only evaluate.

## Contract Criteria for Stage {N}: {label}
{contract_text}

## Output to Evaluate
<stage_output>
{the JSON output}
</stage_output>

## Scoring Rubric
Score each dimension 0-20:
| Dimension | Description |
|-----------|-------------|
| Completeness | All required fields populated, no nulls, no TBDs |
| Accuracy | Values correct, consistent, make sense |
| Consistency | No contradictions between fields |
| Specificity | Named values, not vague placeholders |
| Handoff Readiness | Next stage can consume without questions |

## Response Format
```json
{
  "score": <0-100>,
  "dimensions": { "completeness": <0-20>, "accuracy": <0-20>, "consistency": <0-20>, "specificity": <0-20>, "handoff_readiness": <0-20> },
  "pass": <true if score >= threshold>,
  "critique": "<specific problems if fail, empty if pass>",
  "missing_fields": ["<list>"],
  "contradictions": ["<list>"]
}
```
Be strict but fair. Quality, not perfection.
```

### Retry Message (prepended to skill on retry)
```
## QUALITY GATE FAILURE — Redo Required

Your previous output did not meet the quality threshold.

**Score:** {score}/100 (threshold: {threshold})

**Critique:**
{critique}

**Missing fields:** {missing_fields}
**Contradictions:** {contradictions}

Redo this stage completely. Address every point above.
Do NOT repeat the same mistakes.

Your original instructions follow below.

---
```

### Configuration
- Toggle: enable/disable (default: enabled)
- Threshold: configurable 70-95 (default: 80)
- Max retries: 1-3 (default: 2)
- Judge model: Sonnet or Opus (default: Sonnet)

### UI
- ON/OFF toggle in pipeline settings
- Threshold slider
- Max retries selector
- Score badge on each stage card (green/amber/red)
- Critique display in amber warning box on failure

### Where Contracts Come From
Option A: Parsed from the skill files (each skill has a "Contract" or "Done When" section)
Option B: Loaded from a separate contracts file
Option C: User pastes contract text per stage (like the append box)

### Token Budget
- Judge prompt: ~2K tokens
- Contract text: ~1-3K per stage
- Output to evaluate: ~5-20K
- Judge response: ~500 tokens
- **Total per judgment: ~10-25K tokens (Sonnet = cheap)**
- 11 stages × ~15K avg = ~165K total for judging

---

## Level 2: Run Judge

### What It Does
After the ENTIRE pipeline completes all stages, the Run Judge evaluates the full set of outputs together. Catches problems the Stage Judge can't see because it only looks at one stage at a time.

### What It Checks
- **Coherence:** Does Stage 5's output actually build on Stage 3's output?
- **Completeness:** Did any information get dropped between stages?
- **Consistency:** Do all stages agree on the same app concept, tech stack, etc.?
- **Coverage:** Were all mechanism categories addressed?
- **Quality arc:** Did quality improve or degrade through the pipeline?

### Key Design: Load Skills Once, Judge Outputs Per Run
The Run Judge loads all 11 skill descriptions ONCE as reference. Then for each run, it only receives the 11 outputs (numbered). This keeps the context window manageable:
- Skill descriptions: loaded once (~50K total)
- Per-run outputs: ~50-100K per run
- Total: ~100-150K per judgment

### Judge Prompt Template
```
You are a pipeline run evaluator. You have read all 11 skill descriptions
(loaded as reference). Now evaluate the outputs from one complete run.

## Run Outputs
<stage_0_output>{...}</stage_0_output>
<stage_1_output>{...}</stage_1_output>
...
<stage_10_output>{...}</stage_10_output>

## Evaluate
1. Coherence: Does each stage build logically on the previous?
2. Information preservation: Was anything dropped between stages?
3. Consistency: Do all stages agree on app concept, stack, users?
4. Coverage: All mechanism categories addressed?
5. Quality arc: Quality trend across stages?

## Response Format
```json
{
  "overall_score": <0-100>,
  "coherence": { "score": <0-20>, "issues": ["..."] },
  "preservation": { "score": <0-20>, "issues": ["..."] },
  "consistency": { "score": <0-20>, "issues": ["..."] },
  "coverage": { "score": <0-20>, "issues": ["..."] },
  "quality_arc": { "score": <0-20>, "trend": "improving|stable|degrading" },
  "stage_weaknesses": [
    { "stage": N, "issue": "..." }
  ],
  "recommendations": ["..."]
}
```
```

### Output
The Run Judge produces:
- Overall score
- Per-dimension breakdown
- List of stage-specific weaknesses
- Recommendations for prompt improvements

### When to Run
- After pipeline completes all stages
- Toggle: auto-run after completion vs manual trigger
- Results shown in a "Run Report" section of the output viewer

---

## Level 3: Cross-Run Judge

### What It Does
Compares multiple runs of the same pipeline across different apps/inputs. Identifies patterns in prompt performance.

### What It Checks
- **Prompt reliability:** Which stages consistently score well/poorly?
- **Failure patterns:** What types of inputs cause which stages to fail?
- **Improvement trends:** Are prompts getting better over time?
- **Outlier detection:** Runs that are significantly better/worse than average

### Key Design: Skills Loaded Once, Outputs Batched
- Load all 11 skill descriptions ONCE
- For each run: receive only the numbered outputs + the Run Judge's score
- The Cross-Run Judge doesn't re-read the skills every time

### Input Format
```json
{
  "skills": [
    { "stage": 0, "label": "...", "contract_summary": "..." },
    ...
  ],
  "runs": [
    {
      "run_id": "...",
      "app_name": "...",
      "run_score": 85,
      "stage_scores": [92, 88, 75, ...],
      "stage_outputs_summary": ["...", "..."],
      "weaknesses": ["..."]
    },
    ...
  ]
}
```

### Output
```json
{
  "prompt_reliability": [
    { "stage": N, "avg_score": 85, "std_dev": 5, "reliability": "high" }
  ],
  "weak_stages": [
    { "stage": N, "avg_score": 65, "common_issues": ["..."], "prompt_suggestions": ["..."] }
  ],
  "improvement_trend": "improving|stable|declining",
  "outlier_runs": ["run_id"],
  "meta_recommendations": ["..."]
}
```

### When to Run
- After N runs completed (configurable, default: 3)
- Manual trigger: "Analyze all runs"
- Results shown in a dedicated "Optimization Report" page/section

### Prompt Optimization Loop
The Cross-Run Judge can suggest specific prompt changes:
```
Stage 3 (Agent OS Structuring) scores 65 avg across 5 runs.
Common issue: "problem statement too vague."
Suggestion: Add to Stage 3 prompt — "The problem statement must
include: who has the problem, what the problem is, and what happens
if it's not solved. Minimum 3 sentences."
```

These suggestions can be manually applied or (future) auto-applied and re-tested.

---

## Architecture

### All Three Judges Share
- Same scoring rubric format (5 dimensions × 20 = /100)
- Same pass/fail threshold mechanism
- Same Sonnet model (fast, cheap)
- Same response format (JSON with score + critique)

### Independence
Each judge is a separate module that can be:
- Enabled/disabled independently
- Used with the pipeline or standalone
- Applied to any skill, not just the PRD Maker pipeline

### Database Models

```python
class JudgeResult(Base):
    __tablename__ = "judge_results"
    id = Column(Integer, primary_key=True)
    pipeline_id = Column(String)
    stage_index = Column(Integer)
    judge_type = Column(String)  # "stage" | "run" | "cross_run"
    score = Column(Integer)
    dimensions_json = Column(Text)  # JSON of dimension scores
    passed = Column(Boolean)
    critique = Column(Text)
    retry_number = Column(Integer, default=0)
    created_at = Column(DateTime)
```

### API Endpoints
```
POST /api/pipeline/judge/stage — Judge a single stage output
POST /api/pipeline/judge/run — Judge a complete run
POST /api/pipeline/judge/cross-run — Judge across multiple runs
GET  /api/pipeline/judge/results/{pipeline_id} — Get judge results
```

---

## Build Order

1. **Stage Judge first** — most immediately useful, simplest
2. **Run Judge second** — adds value after multiple stages are working
3. **Cross-Run Judge third** — needs multiple completed runs to be useful

Each is ~200-300 lines of code. The judge prompt is the hard part (getting the rubric right), not the code.

---

## Integration with Modular Pipeline (Future)

The judges work identically with the modular pipeline (AI/Code/Hybrid steps):
- Code steps: judge validates output against schema (deterministic check)
- AI steps: judge evaluates quality (same as now)
- Hybrid steps: both checks

The judge doesn't care how the output was produced — it only evaluates the result.
