# Overhead Budget Breakdown

## Standard Per-Phase Overhead (~25,000 tokens)

Every protocol-injected phase adds a fixed overhead on top of Stage 7's `estimated_tokens`. This overhead is predictable because it uses standardized templates.

| Component | Token Estimate | What It Contains |
|-----------|---------------|------------------|
| Build rules preamble | ~8,000 | Martin's structural rules applicable to this phase. Sourced from the agnostic checklist. Includes banned patterns, file naming conventions, component structure rules, state management rules. |
| File sandbox declaration | ~2,000 | `files_allowed`, `files_read_only`, `files_forbidden` lists with explanations. Includes "DO NOT MODIFY" warnings for protected files. |
| Build order with pulse points | ~3,000 | The ordered file list with pulse check definitions after each entry. More files = more tokens, but pulse checks are concise (~50 tokens each). |
| Seam check definitions | ~2,000 | Connection-point verification instructions. Typically 2-5 seam checks per phase at ~200-400 tokens each. Phases with no interfaces: ~200 tokens (just the "no seam checks needed" note). |
| Full checkpoint | ~5,000 | Pattern verification instructions (~2,000), functional check commands (~1,500), gate condition (~500), checkpoint summary format (~1,000). |
| Pattern verification prompt | ~3,000 | Instructions for the git diff process: how to run it, how to compare, how to interpret results, what to report. |
| Violation handling | ~2,000 | The 4-level decision tree with triggers and responses customized to this phase's sandbox. |
| **TOTAL** | **~25,000** | |

## Budget Validation Rules

1. **Per-phase overhead MUST be ≤ 30,000 tokens.** If it exceeds this after injection, trim verbose descriptions. Checks should be single-line commands, not paragraphs.

2. **Per-phase total MUST be ≤ 350,000 tokens.** Formula: `stage_7.phases[].estimated_tokens + overhead_tokens ≤ 350,000`. This leaves room for the Claude context window overhead (system prompt, tools, etc.).

3. **If overhead exceeds 30,000**, apply these trims in order:
   - Reduce build rules preamble to only the rules relevant to this phase's mechanisms (can drop to ~4,000)
   - Condense pulse checks to single-line format: `"PULSE: auth.ts → [exists, exports loginUser/logoutUser]"`
   - Merge similar seam checks
   - If still over: flag for Stage 7 to re-split the phase

4. **If total exceeds 350,000**, signal back to Stage 7 that this phase has too much content and needs to be split into sub-phases.

## Overhead Variation by Phase Size

| Phase Size (files) | Typical Pulse Overhead | Typical Seam Overhead | Total Overhead Range |
|--------------------|-----------------------|----------------------|---------------------|
| 2-5 files | ~500 tokens | ~400 tokens | 22,000 - 24,000 |
| 6-10 files | ~1,000 tokens | ~800 tokens | 24,000 - 26,000 |
| 11-15 files | ~1,500 tokens | ~1,200 tokens | 26,000 - 28,000 |
| 16+ files | ~2,000+ tokens | ~1,600+ tokens | 28,000 - 30,000 |

Phases with 16+ files are rare (Stage 7 typically caps at ~12 files per phase). If you see one, it's likely a candidate for splitting.

## Recording the Breakdown

The `overhead_breakdown` object in the output is a TEMPLATE — it records the standard budget allocation, not the per-phase actual. Per-phase actuals are in each phase's `overhead_tokens` field.

```json
{
  "overhead_breakdown": {
    "build_rules_preamble": 8000,
    "file_sandbox_declaration": 2000,
    "build_order_with_pulse": 3000,
    "seam_check_definitions": 2000,
    "full_checkpoint": 5000,
    "pattern_verification": 3000,
    "violation_handling": 2000
  }
}
```

This is the same for every run. Individual phase `overhead_tokens` may vary slightly based on file count and seam check count.
