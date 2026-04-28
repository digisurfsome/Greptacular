# Stacks Re-Run Report
**Status:** Script built. Awaiting API key to run.
**Date:** 2026-04-28
**Script:** `scripts/metaprograms/mine_stacks.py`
**Commit:** c13ce0a

---

## What was built

A deterministic Python script that scans all 128 transcripts for
multi-metaprogram stacks. NOT an agent loop — a script with one LLM call
per 4 000-token chunk. Resumable at any point.

### Architecture
```
transcript folder (128 .txt files)
  → recursive glob → sorted list of files
  → each file stripped of YouTube caption header
  → chunked: 4 000-token windows, 500-token overlap (tiktoken cl100k_base)
  → all chunks queued as asyncio tasks
  → bounded by asyncio.Semaphore(5) — max 5 concurrent API calls
  → Claude Sonnet via Anthropic API (prompt caching on system prompt)
  → JSON response parsed → stacks extracted + annotated
  → progress saved after EVERY chunk (_stack_mine_progress.json)
  → kill + restart safely anytime
  → final output: stacks-rerun.md sorted by stack_size desc
```

### Key design decisions
| Decision | Choice | Reason |
|----------|--------|--------|
| Model | Claude Sonnet | Verbatim discipline — Haiku paraphrases |
| Prompt caching | Yes (ephemeral) | System prompt is ~600 tokens × 640+ calls = massive savings |
| Chunk size | 4 000 tokens | Fits comfortably in context; Robbins Part 1/2 is one giant paragraph |
| Overlap | 500 tokens | Catches stacks that span chunk boundaries |
| Concurrency | 5 | Stays under Anthropic rate limits; ~5× throughput vs sequential |
| Idempotency | By text dedup | Re-running same data → same output (sorted by speaker+text) |
| Progress | JSON file | Every chunk saves immediately — safe to kill anytime |
| Speaker ID | Filename substring | "anthony robbins" in path → "Anthony Robbins" |

---

## How to run

### Step 1: Get Anthropic API key
Go to https://console.anthropic.com → API Keys → Create key.
This is separate from your Claude.ai subscription.
Cost estimate: ~128 files × ~5 chunks avg × ~4200 input tokens = ~2.7M tokens input.
With prompt caching (reads after first write): ~$0.80–$2.00 total for full run.

### Step 2: Add to .env (repo root)
```
ANTHROPIC_API_KEY=sk-ant-...
```

### Step 3: Install dependencies (if not already installed)
```
pip install anthropic tiktoken python-dotenv
```

### Step 4: Smoke test — 3 files
```
python scripts/metaprograms/mine_stacks.py "E:\AutoForge\Metaprograms\videos" --output "E:\AutoForge\Metaprograms\stacks-smoketest.md" --limit 3
```
Verify:
- Script starts, shows "Found 128 transcript files. --limit 3: processing first 3 file(s) only."
- API calls fire, JSON parses, progress saves
- smoketest.md appears with any stacks found (likely 0 from the first 3 files — they're generic NLP education videos)
- Pick a verbatim quote from the output and ctrl+F it in the source transcript → must match exactly

### Step 5: Full run (Robbins files first to validate gold stacks)
Run the Robbins folder first to confirm the two gold stacks appear:
```
python scripts/metaprograms/mine_stacks.py "E:\AutoForge\Metaprograms\videos\Anthony Robbins Meta Programs" --output "E:\AutoForge\Metaprograms\stacks-robbins-only.md"
```
Expected: both gold stacks below should be found.

### Step 6: Full corpus
```
python scripts/metaprograms/mine_stacks.py
```
Uses defaults: `E:\AutoForge\Metaprograms\videos` → `E:\AutoForge\Metaprograms\stacks-rerun.md`

Safe to kill and restart at any time. Progress tracked in
`E:\AutoForge\Metaprograms\_stack_mine_progress.json`.

---

## Model override (optional)
If Sonnet 4.6 API is available at your tier, set in .env:
```
ANTHROPIC_MODEL=claude-sonnet-4-6-20260201
```
Check exact model ID at https://docs.anthropic.com/en/docs/about-claude/models

---

## Quality gate (after run)

### Spot-check verbatim discipline
Pick 5 stacks from output. For each:
```
# PowerShell
Select-String -Path "E:\AutoForge\Metaprograms\videos\*\transcript.txt" -Pattern "first few words of the quote"
```
Every quoted word must appear verbatim in the source. Zero tolerance for paraphrase.

### Robbins gold stacks — MUST be found
Both of these should appear as 4-5 program stacks:

**Gold stack 1 — The challenger (guest event, guest challenges Tony to convince him):**
Key phrase: `"you're the only one who knows who would lose if you didn't go to this program"`
Expected programs: internal + away + necessity (possibly convincer-times)

**Gold stack 2 — The $50k business partner:**
Key phrase: `"I have had it, this is it... there is now a necessity. You have three minutes to make a decision"`
Expected programs: away + necessity + internal + mismatch + convincer-times

### Compare to original 8 stacks
All 8 stacks from `E:\AutoForge\Metaprograms\stacks.md` should be re-found
(same Robbins Part 12 source). If any are missing, check error log at
`E:\AutoForge\Metaprograms\_stack_mine_errors.log`.

---

## Files created / modified
| Path | Type | What |
|------|------|------|
| `scripts/metaprograms/mine_stacks.py` | code | The scanner script |
| `docs/page-prds/sales-bot/stacks-rerun-report.md` | PRD | This file |
| `E:\AutoForge\Metaprograms\stacks-rerun.md` | output | Created when script runs |
| `E:\AutoForge\Metaprograms\_stack_mine_progress.json` | state | Created when script runs |
| `E:\AutoForge\Metaprograms\_stack_mine_errors.log` | log | Created if any errors |

---

## Cost estimate (full 128-file run)
- ~640 chunks estimated (128 files × ~5 chunks avg)
- System prompt = ~600 tokens, cached after first write
- Cache-write cost (first call): 600 × $3.75/M = $0.002
- Cache-read cost (remaining 639 calls): 639 × 600 × $0.30/M = $0.115
- User content per chunk: ~4200 input tokens × 640 × $3.00/M = $8.06 ← bulk of cost
- Output per chunk: ~100 tokens avg × 640 × $15.00/M = $0.96
- **Total estimate: ~$9–12** (most from input; prompt caching saves ~$1 on system prompt)

With prompt caching on system prompt AND if you run the Robbins folder first as
a "warm" check, the total should be under $12.

---

## Resumability demo
To test resumability: start the full run, kill after 30 seconds, restart.
The second run will skip all completed chunks and pick up exactly where it
stopped. Progress file is written after every single chunk — no chunk is
ever lost.
