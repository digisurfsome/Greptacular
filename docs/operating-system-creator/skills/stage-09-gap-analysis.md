# OS Automation Skills — Stage 9: Gap Analysis

> **What this does:** Final sweep across everything captured in Stages 0-8. Checks every known gap category against the current design. Catches what was missed.

---

## When to Use

**Runs TWICE:**
1. **Early pass (after Stage 2):** Quick scan for obvious missing pieces before detailed design begins. Catches showstoppers early.
2. **Final pass (after Stage 8):** Thorough sweep with everything laid out. Catches subtle gaps.

## Input

All previous stage outputs.

## Process

### The Gap Checklist

Run through every item. For each, answer: "Is this covered? Where?"

#### Structural Gaps

| # | Gap | Question to Ask | Covered? | Where? |
|---|-----|----------------|----------|--------|
| 1 | Multi-level phasing | Is this one phase or multiple? Are phases documented separately? | | |
| 2 | Repeating steps | Does any step run N times? Is N fixed or variable? | | |
| 3 | Extensible options | Do the options in any step grow over time? Can new types/filters/templates be added? | | |
| 4 | Presets | Are there common combinations that should be one-click? | | |
| 5 | Cross-item merge | Can multiple items be batch-processed together into one output? | | |

#### Environment Gaps

| # | Gap | Question to Ask | Covered? | Where? |
|---|-----|----------------|----------|--------|
| 6 | API keys/credentials | Is every required key listed with how-to-get instructions? | | |
| 7 | Dependencies | Are all packages, runtimes, and system requirements listed? | | |
| 8 | Cost-per-run | Is the exact cost per run calculated? Monthly estimate? | | |
| 9 | Rate limits | Is every API rate limit documented with buffer strategy? | | |
| 10 | Prerequisites | Are setup steps listed in order with one-time vs per-instance marked? | | |

#### Design Gaps

| # | Gap | Question to Ask | Covered? | Where? |
|---|-----|----------------|----------|--------|
| 11 | Prompt templates | For every AI step, is the prompt skeleton captured? | | |
| 12 | User interaction | Is the interface defined? CLI commands? Dashboard? Bot? | | |
| 13 | Data retention | How long is data kept? When archived? When deleted? | | |
| 14 | Output quality | How do you know the output is correct? Quality gates defined? | | |
| 15 | Versioning/reprocessing | Can you rerun old items with a new prompt? How? | | |

#### Operations Gaps

| # | Gap | Question to Ask | Covered? | Where? |
|---|-----|----------------|----------|--------|
| 16 | Sample test case | Is there a real, concrete test case? Not hypothetical? | | |
| 17 | Rollback/undo | If output is wrong, how do you redo? | | |
| 18 | Access control | Who can run this? Who can change settings? Does it matter? | | |

### Scoring

After checking all 18 gaps:

| Coverage | Rating | Action |
|----------|--------|--------|
| 18/18 covered | COMPLETE | Ready to generate CLAUDE.md |
| 15-17 covered | NEAR COMPLETE | Fill remaining gaps, then generate |
| 10-14 covered | GAPS FOUND | Go back to relevant stages and fill |
| < 10 covered | INCOMPLETE | Major rework needed — revisit Stages 0-4 |

### New Gaps Discovery

After checking the standard 18, ask:

"Is there anything specific to THIS automation that doesn't fit any of the 18 categories above?"

If yes, document it as gap #19+ and note which stage should have captured it. This is how the gap checklist grows over time.

## Output

```json
{
  "stage_9": {
    "pass_type": "early | final",
    "gap_results": [
      {
        "gap_number": 1,
        "gap_name": "string",
        "covered": "boolean",
        "where": "string (which stage/section covers it)",
        "action_needed": "string (if not covered)"
      }
    ],
    "coverage_score": "number out of 18",
    "rating": "COMPLETE | NEAR_COMPLETE | GAPS_FOUND | INCOMPLETE",
    "new_gaps_discovered": [
      {"description": "string", "should_be_in_stage": "number"}
    ],
    "actions_required": ["string"]
  }
}
```

## Rules

1. Be honest. If something is only partially covered, mark it as NOT covered and note what's missing.
2. The early pass should take 2 minutes. Just scan for showstoppers.
3. The final pass should be thorough. Check every single item.
4. New gaps get fed back into the skill definitions. The checklist evolves.
