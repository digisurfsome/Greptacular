# Confidence Assessment Rubric

> Source: nicknisi/claude-plugins/plugins/ideation/skills/ideation/references/confidence-rubric.md

## Overview

Evaluates brain dump clarity before contract generation. Requires 95 points minimum to proceed. Five dimensions, each scored 0-20.

## Five Scoring Dimensions

### Problem Clarity (0-20)

- 0-5: Completely unclear
- 6-10: Vague mentions
- 11-15: Clear but incomplete
- 16-20: Crystal clear with quantified impact

Example (20): Describes specific users, frequency, and "$50k/month in lost revenue."

### Goal Definition (0-20)

- 0-5: No goals stated
- 6-10: Vague aspirations ("improve UX")
- 11-15: Goals stated but unmeasurable
- 16-20: SMART metrics ("reduce checkout latency to under 500ms p95")

### Success Criteria (0-20)

- 0-5: None provided
- 6-10: Subjective only
- 11-15: Partially measurable
- 16-20: Clear, testable acceptance criteria for ALL goals with pass/fail verification

### Scope Boundaries (0-20)

- 0-5: Unlimited scope
- 6-10: Implied boundaries
- 11-15: Stated but gapped
- 16-20: Clear in/out of scope with rationale. Future considerations noted.

### Consistency (0-20)

- 0-5: Major contradictions making requirements impossible
- 6-10: Conflicting statements
- 11-15: Minor inconsistencies
- 16-20: Internally aligned requirements

## Confidence Thresholds

| Range | Interpretation | Action |
|-------|---|---|
| <70 | Major gaps | Ask 5+ questions; multiple rounds needed |
| 70-84 | Moderate gaps | Ask 3-5 questions; one more round likely |
| 85-94 | Minor gaps | Ask 1-2 questions; nearly ready |
| >= 95 | Ready | Generate contract |

## Question Best Practices

**Do:** Be specific ("What happens when..."), offer options, reference context, limit to 3-5 questions, prioritize lowest dimension, chain logically.

**Don't:** Use open-ended prompts, ask redundant questions, employ leading questions, ask compound questions, skip context.

## Spec Feedback Quality Framework

Applied during Phase 4.5 (separate from brain-dump confidence):

- **Strong:** Feedback Strategy section present with inner-loop command. All iterative components have loops; trivial components correctly omit them.
- **Adequate:** Feedback Strategy exists but some iterative components lack loops or experiments are vague.
- **Weak:** No Feedback Strategy section; complex iterative components missing feedback loops entirely.

### Quality Checklist

- Feedback Strategy section exists
- Inner-loop command runs in seconds
- Iterative components have feedback loops
- Experiments are parameterized
- Trivial components skip unnecessary loops
- Playground matches component type

### Actions by Level

- Strong: Present spec as-is
- Adequate: Present with note about specific gaps
- Weak: Revise before presenting; add loops for iterative components

## Recalculation Protocol

After each clarification round: re-read materials, re-score all dimensions, identify new lowest dimension, ask targeted questions. Typical progression: Round 1 (50-65 -> 70-80), Round 2 (70-80 -> 85-92), Round 3 (85-92 -> 95+). Score conservatively -- when uncertain, choose lower.
