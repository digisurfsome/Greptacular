# Jeremy Objections Mining Report

> **Status:** ⏳ Pending — run `python scripts/jeremy/mine_objections.py` to populate.

## Source

- `01-Common Objections` — 53 videos, one per named objection

## Run Commands

```
cd C:\Users\lober\.autoforge\workspace\repos\digisurfsome__Greptacular
python scripts/jeremy/mine_objections.py --dry-run --limit 5

cd C:\Users\lober\.autoforge\workspace\repos\digisurfsome__Greptacular
python scripts/jeremy/mine_objections.py --limit 5

cd C:\Users\lober\.autoforge\workspace\repos\digisurfsome__Greptacular
python scripts/jeremy/mine_objections.py
```

## Results (fill in after run)

| Metric | Value |
|---|---|
| Total extractions | — |
| Distinct objections | — |
| Full handlers (gold) | — |
| Total API calls | — |
| Run date | — |

## Quality Gate Targets

| Target | Goal | Actual |
|---|---|---|
| Distinct objection_name count | ≥30 | — |
| handler_full count | ≥20 | — |
| Verbatim spot-check | 10/10 | — |

## Objection Coverage List (fill in after run)

*(copy from _objection-index.md after run)*

## Output Files

All in `docs/info/jeremy-miner-corpus/objection-handlers/`:

- `_objection-index.md` — coverage table, type counts, quality warnings
- `{objection-name}.md` — one file per objection (full handler + steps + prevention + psychology)
- `prevention-phrases.md` — all prevention phrases grouped by objection
- `psychology-notes.md` — all definitions + root causes grouped by objection
- `_objection_mine_progress.json` — resume checkpoint (do not delete)
