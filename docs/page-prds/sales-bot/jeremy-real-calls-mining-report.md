# Jeremy Real Calls Mining Report

> **Status:** ⏳ Pending — run `python scripts/jeremy/mine_real_calls.py` to populate.

## Sources

- `04-The 7 Figure Call Vault` — closed deals, full call arcs
- `NEPQ Training Calls` — coaching calls, advancement moments

## Run Commands

```
cd C:\Users\lober\.autoforge\workspace\repos\digisurfsome__Greptacular
python scripts/jeremy/mine_real_calls.py --dry-run --limit 5

cd C:\Users\lober\.autoforge\workspace\repos\digisurfsome__Greptacular
python scripts/jeremy/mine_real_calls.py --limit 5

cd C:\Users\lober\.autoforge\workspace\repos\digisurfsome__Greptacular
python scripts/jeremy/mine_real_calls.py
```

## Results (fill in after run)

| Metric | Value |
|---|---|
| Total extractions | — |
| Total API calls | — |
| Run date | — |

## Quality Gate Targets

| File | Target | Actual |
|---|---|---|
| gate-moments.md | ≥20 | — |
| deployed-closes.md | ≥10 | — |
| deployed-questions (all stages) | ≥10 each | — |

## Gate Moment Samples (fill in after run — spot-check verbatim)

| # | Seller line | Prospect response | Outcome |
|---|---|---|---|
| 1 | — | — | — |
| 2 | — | — | — |
| 3 | — | — | — |

## Output Files

All in `docs/info/jeremy-miner-corpus/real-calls-corpus/`:

- `deployed-openers.md`
- `deployed-questions-stage-1.md` through `deployed-questions-stage-7.md`
- `deployed-handlers.md`
- `deployed-closes.md`
- `deployed-transitions.md`
- `gate-moments.md` ← highest value
- `tone-demonstrations.md`
- `live-reframes.md`
- `prospect-advancement-signals.md`
- `_real-calls-index.md`
- `_real_calls_mine_progress.json` — resume checkpoint (do not delete)
