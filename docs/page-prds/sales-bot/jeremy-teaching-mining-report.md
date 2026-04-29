# Jeremy Miner Teaching Mining Report

> **Status:** ⏳ Pending — run `python scripts/jeremy/mine_teaching.py` to populate.
> This file is pre-created. Update manually after mining completes.

## What This Script Mines

Teaching content from 5 NEPQ course folders:
- `01-Intro to NEPQ Selling`
- `02-The Power of NEPQ`
- `02-The NEPQ Kickstart Crash Course`
- `Jeremy Miner - NEPQ Black Book Bundle`
- `The Training`

Extraction types: `framework_definition`, `gate_criteria`, `tone_note`,
`nepq_question_taught`, `example_phrase_taught`, `mistake_warning`,
`transition_taught`, `reframe_taught`

## Run Commands

```bash
# Smoke test (first 5 sections only, no API calls)
python scripts/jeremy/mine_teaching.py --dry-run --limit 5

# Smoke test with API calls (5 sections)
python scripts/jeremy/mine_teaching.py --limit 5

# Full run
python scripts/jeremy/mine_teaching.py
```

## Results (fill in after run)

| Metric | Value |
|---|---|
| Total extractions | — |
| Total API calls | — |
| Subscription cost | $0 |
| Run date | — |
| Run duration | — |

## Per-Stage Counts (target ≥30 each, ≥15 for gate criteria)

| Stage | Name | Count | Target | Status |
|---|---|---|---|---|
| 1 | Connect | — | ≥30 | ⏳ |
| 2 | Situation | — | ≥30 | ⏳ |
| 3 | Problem Awareness | — | ≥30 | ⏳ |
| 4 | Solution Awareness | — | ≥30 | ⏳ |
| 5 | Consequence | — | ≥30 | ⏳ |
| 6 | Transition/Presentation | — | ≥30 | ⏳ |
| 7 | Commitment | — | ≥30 | ⏳ |

## Per-Type Counts

| Type | Count | Target |
|---|---|---|
| framework_definition | — | ≥30 |
| gate_criteria | — | ≥15 |
| tone_note | — | ≥20 |
| nepq_question_taught | — | ≥40 |
| example_phrase_taught | — | ≥30 |
| mistake_warning | — | ≥20 |
| transition_taught | — | ≥15 |
| reframe_taught | — | ≥10 |

## Quality Gate (spot-check 10 verbatim)

After run, manually grep 10 random `text` values against source transcripts.
Target: 10/10 must appear verbatim.

| # | Text (first 60 chars) | Found verbatim? |
|---|---|---|
| 1 | — | — |
| 2 | — | — |
| 3 | — | — |
| 4 | — | — |
| 5 | — | — |
| 6 | — | — |
| 7 | — | — |
| 8 | — | — |
| 9 | — | — |
| 10 | — | — |

## Gaps / Notes

*(fill in after review)*

## Output Files

All in `docs/info/jeremy-miner-corpus/teaching-corpus/`:

- `stage-1-connecting.md` through `stage-7-commitment.md` (7 stage files)
- `gate-criteria.md` — all gate advancement rules (cross-stage)
- `tone-notes.md` — delivery / tonality instructions
- `mistakes-warnings.md` — "don't do this" verbatim
- `reframes-taught.md` — polarity/reframe examples
- `_teaching-index.md` — summary with counts and quality warnings
- `_teaching_mine_progress.json` — resume checkpoint (do not delete)
