# Live Call Extraction Playbook
*Last updated: 2026-05-01*

---

## What This Is For (Read This First)

Use this when you have **video recordings of real human conversations** — cold calls, sales calls, Zoom demos, phone pitches — and you want to extract the actual back-and-forth dialogue for bot training, script building, or sales analysis.

This is NOT for:
- Educational content / tutorials (use `truth_builder_v2.py`)
- Coaching sessions where someone is teaching (use `mine_teaching.py`)
- One-sided narration / vlogs

The output is **verbatim dialogue pairs**: what the prospect said, what the seller said, what happened next. Gold for training a sales bot because it's real human reactions, not theoretical examples.

---

## Human Summary — Plain Language

### What we built
Two scripts that watch videos, find the actual call portion, separate who's talking, and extract the real exchanges:

- **`scripts/call_miner/call_miner.py`** — Full pipeline: discovers interaction categories, screens videos for real calls, extracts exchanges, clusters similar ones, renders organized output files. Use this for a folder of call videos.
- **`scripts/call_miner/cold_call_extractor.py`** — Simpler direct extractor. No pipeline, no clustering. Use this for quick targeted extraction or troubleshooting.

### What it produces
```
output/connor_calls/
├── all_exchanges.md          ← MAIN FILE — read this
├── _call-index.md            — by video, with V001-V009 IDs
├── _video_report.md          — which videos confirmed/uncertain/skipped
├── voice-quality.md          — all voice quality exchanges grouped
├── pricing-pushback.md       — all pricing exchanges
├── opener-hook.md            — opening lines
└── ... (8 category files total)
```

### Key points to remember
- Each video gets a permanent ID (V001, V002...) — every exchange is tagged to its source
- The script pre-screens videos: `confirmed` = extracts, `uncertain` = extracts with warning flag, `not_a_call` = skips
- If a video fails, it's marked and retried — no silent skips
- Fully resumable: kill it and restart, it picks up where it left off
- Connor's videos: older ones have `>>` speaker markers. New videos transcribed going forward will have `Speaker 0:` / `Speaker 1:` from Deepgram diarization

### Key things to watch out for
1. **Exit 15 errors** — The Claude subscription auth layer occasionally kills processes under load. The scripts retry 4x automatically. If all 4 fail on a chunk, that chunk is skipped and logged. This is normal. Re-running heals skipped chunks.
2. **Narration sandwich** — Many YouTubers introduce and debrief around their actual call. The script detects where the call starts/ends and strips the narration. Only dialogue gets extracted.
3. **Same call, two videos** — Connor has videos of raw calls AND his review of the same call. This creates duplicates. The dedup is not automatic — check `_video_report.md` and use `purge_video.py` to remove if needed.
4. **V9 ("best cold call")** — consistently failed exit 15 on all chunks across 3 runs. Unknown cause. Possibly transcript format issue. Skip it and move on.

### What to do when things go wrong
| Problem | Fix |
|---|---|
| Everything skips ("N done, 0 to extract") | Previous failed run left empty files. Run with `--reset` |
| Exit 15 on all chunks of one video | Skip it. Re-run later when nothing else is using Claude. |
| 0 exchanges but it's definitely a call | Check `_video_report.md` — was it flagged `not_a_call`? Read the actual transcript and check for speaker markers. |
| Clustering produces "47 clusters, 0 singletons" | Batch size too large. Delete `clusters.json` and re-run `--sweep 2`. |
| Want to remove one bad video from output | `python scripts/call_miner/purge_video.py --config ... --list` then `--remove V006 --re-render` |

---

## Where We Ended Up — The Final Solution

### Transcript format (source of truth for NEW videos)
**Deepgram with diarization.** Every new video transcribed through `transcribe_deepgram.py` now outputs:
```
Speaker 0: Hey Bruce, you have a roofing company?
Speaker 1: I do.
Speaker 0: My name's Connor...
```
This gives clean speaker separation with zero LLM calls. Free, automatic, reliable.

### Speaker detection hierarchy (handles all formats)
The scripts auto-detect which format a transcript uses and handle all three:
1. `Speaker N:` format (Deepgram diarized — new videos)
2. `>>` format (YouTube auto-captions — Connor's existing videos)
3. No labels (Claude infers from context — fallback, least reliable)

### Call window detection
Before extracting, the script finds where the actual call starts and ends by looking for first/last speaker switch. Everything before (intro narration) and after (debrief) is stripped. Only the live dialogue is passed to Claude for extraction.

### Chunk size
1,500 tokens per chunk with 200-token overlap. This is the sweet spot for the subscription auth layer — small enough that exit 15 is rare, large enough that context is preserved across chunk boundaries.

### Concurrency
Sequential per video (1 chunk at a time per video). No parallel workers. This prevents rate pressure on the subscription auth layer.

---

## What We Tried and What Happened

### Failed approaches

**Single large prompt per video**
Tried passing entire transcript in one Claude call. Transcripts are 10K-20K chars. Exit 15 hit 100% of the time. Root cause: Windows command-line arg limit (~32K chars) AND subscription auth pressure under large payloads.

**`claude -p "giant string"` pattern**
Same issue. Replaced with stdin pipe (`claude -p` + `communicate(input=prompt.encode())`). Removed the command-line size limit. But still hit exit 15 on large transcripts.

**4,000 token chunks**
Still too large. Exit 15 rate was ~30-40% per chunk. Retries helped but slow.

**25-exchange clustering batches**
Clustering sent 25 exchanges at once. Long exchanges (200-500 word responses) = 8K+ tokens per clustering call. All 4 retries failed. Resulted in "47 clusters, 0 singletons" — no actual grouping, every exchange treated as its own cluster. Fix: reduce to 8 exchanges per batch.

**Taxonomy LLM call with 8 sample transcripts**
8 × 2000 chars = 16K chars. Hit exit 15. Reduced to 4 samples × 2000 chars.

**Empty JSONL = "done"**
Early code treated any existing JSONL file as complete — even empty ones from failed extractions. Re-runs skipped failed videos permanently. Fixed: only skip if file has content OR video is a confirmed `not_a_call`.

### What worked

**1,500-token chunks via stdin** — exit 15 rate dropped to ~20% per chunk (vs 100% before). Retries handle the rest.

**Pre-filter sweep (Sweep 0.5)** — cheap LLM call per video on title + first 800 chars. Correctly identifies `not_a_call` videos (tutorials, demos not involving a real call). Saves extraction time on bad videos.

**Video registry (V001, V002...)** — permanent IDs assigned at Sweep 0. Every exchange traces back to source video. Enables surgical removal with `purge_video.py`.

**`>>` boundary detection** — Connor's YouTube-auto-captioned transcripts have `>>` before prospect lines. First `>>` = call start, last `>>` = call end. Narration outside that window is discarded. Zero LLM calls for this step.

**Deepgram diarization** — one param (`diarize: true`) in `transcribe_deepgram.py`. Clean `Speaker 0:` / `Speaker 1:` output for all future transcriptions.

---

## Agent Spec — Full Technical Details

### Scripts and their roles

| Script | Purpose | Input | Output |
|---|---|---|---|
| `scripts/call_miner/call_miner.py` | Full 4-sweep pipeline | Config JSON | JSONL per video + clustered MD files |
| `scripts/call_miner/cold_call_extractor.py` | Direct extractor, no clustering | CLI args | Single MD file |
| `scripts/call_miner/purge_video.py` | Remove video from corpus | Config + video ID | Rewrites JSONL + re-renders |
| `scripts/call_miner/_claude.py` | Shared utilities | — | Functions for auth, chunking, speaker detection |
| `transcribe_deepgram.py` | Transcription with diarization | Audio file | `transcript.txt` with `Speaker N:` labels |

### Config schema (connor-calls.json pattern)
```json
{
  "project_name": "connor_live_calls",
  "videos_dir": "...",
  "output_dir": "...",
  "call_filter_keywords": ["cold-call", "cold-calling", "live", "call-", "-call", "sales-call", "demo", "calling"],
  "taxonomy_sample_n": 4,
  "llm_batch_size": 8,
  "max_chunk_tokens": 1500,
  "chunk_overlap_tokens": 200
}
```

### Sweep pipeline (call_miner.py)
```
Sweep 0  → Taxonomy discovery (4 sample transcripts → 11 interaction types)
           Video registry (V001...VN assigned, never changes)
           GATE: human reviews taxonomy.json, can edit, presses Enter
Sweep 0.5 → Pre-filter: each video screened (confirmed / uncertain / not_a_call)
Sweep 1  → Exchange extraction per video:
             1. Read transcript
             2. preprocess_transcript() → detect format, extract call window, normalize labels
             3. Chunk at 1,500 tokens with 200-token overlap
             4. Per-chunk: claude -p via stdin, parse JSON extractions
             5. Dedup cross-chunk overlaps
             6. Write JSONL to exchanges/{video_slug}.jsonl
Sweep 2  → Clustering: batch 8 exchanges at a time, LLM groups by interaction type
Sweep 3  → Render: per-type MD files + all_exchanges.md + _call-index.md
```

### Speaker detection logic (`_claude.py`)
```python
def detect_speaker_format(text):
    # Returns: "deepgram" | "youtube" | "unknown"
    if re.search(r'^Speaker \d+:', text, re.MULTILINE): return "deepgram"
    if ">>" in text: return "youtube"
    return "unknown"

def extract_call_window(text, fmt):
    # Finds first and last speaker switch → strips narration outside
    # deepgram: first "Speaker 1:" ... last "Speaker 1:"
    # youtube: first ">>" ... last ">>"
    # unknown: returns full text (Claude infers speakers)

def normalize_speakers(text, fmt):
    # Maps to SELLER: / PROSPECT: labels for consistent extraction prompt
```

### Extraction prompt key rules
- `VERBATIM ONLY` — every word in `text` must appear in transcript exactly
- `prospect_response` mandatory for gate_moment entries
- `outcome` field: `advanced | deflected | stalled | closed | lost`
- Empty list `[]` if no exchanges in chunk — never fabricate
- `source_video` + `video_id` mandatory on every entry

### Resumability
- `exchanges/{video_slug}.jsonl` with content = done, skip
- `exchanges/{video_slug}.jsonl` empty = failed, retry
- `_video_registry.json` = V-IDs, never deleted between runs
- `taxonomy.json` = cached, delete to regenerate
- `--reset` flag wipes all output and starts fresh
- `--sweep N` flag jumps to specific sweep (skips prior sweeps)

### Auth pattern (mandatory for all scripts)
```python
env = os.environ.copy()
env.pop("ANTHROPIC_API_KEY", None)
env.pop("CLAUDE_CODE", None) 
proc = await asyncio.create_subprocess_exec(
    CLAUDE_CLI, "-p", "--model", MODEL, "--output-format", "text",
    stdin=asyncio.subprocess.PIPE,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
    env=env, shell=False
)
stdout, stderr = await proc.communicate(input=prompt.encode("utf-8"))
```
Exit code 15 = SIGTERM from auth layer. Retry with backoff: 5s, 15s, 30s, 60s. Max 4 attempts.

### For a new channel / playlist
1. Download videos (yt-dlp)
2. Transcribe: `python transcribe_deepgram.py --input <folder>` → `transcript.txt` per video with `Speaker N:` labels
3. Copy `scripts/call_miner/config.example.json` → `scripts/call_miner/your-channel.json`
4. Set `videos_dir`, `output_dir`, `project_name`
5. Set `call_filter_keywords: []` if all videos are calls (no filtering needed)
6. Dry run: `python scripts/call_miner/call_miner.py --config your-channel.json --dry-run`
7. Full run: `python scripts/call_miner/call_miner.py --config your-channel.json`

---

## Results from Connor's Channel (First Run)

| Metric | Result |
|---|---|
| Videos processed | 9 matched filter / 71 total |
| Confirmed call videos | 5 |
| Not-a-call (correctly skipped) | 4 |
| Exchanges extracted | 47 (call_miner) + 26 (cold_call_extractor) |
| Estimated unique exchanges | ~55-60 |
| Clustering | Failed (exit 15 on all batches) — no grouping |
| V9 ("best cold call") | Failed all attempts, unknown cause |
| Output size | 36 KB (all_exchanges.md) |
| Bot training value | 7/10 — real exchanges, real objections, thin volume |

**What the corpus has:**
- Voice quality objections ("is it going to sound like a robot?")
- Memory/context concerns ("will it know my company's info?")
- Human-likeness doubts ("can it really talk like a human?")
- Pricing/ROI conversations
- Cold-call opener lines
- Missed-call ROI math (30/day × 50% = $45K/mo)

**What it's missing:**
- More volume (need 200+ exchanges minimum for bot training)
- Metaprogram tags (toward/away, internal/external)
- NEPQ stage tags (Connect/Situation/Problem-Aware etc.)
- Cross-channel variety (different sales styles, different niches)

---

## Future Ideas and Potential Improvements

### Near-term (before next channel run)
- **Fix clustering batch size** — re-run `--sweep 2` with batch size 8. Will group the 47 Connor exchanges properly.
- **Add NEPQ stage tagging** — port the stage tagging from `mine_real_calls.py` as a post-extraction pass. Lets the bot pull exchanges by conversation stage.
- **Dedup V001/V002** — run `purge_video.py` to remove V002 (Connor's review of his own call) since V001 has the raw exchange. Review content bleeds into verbatim fields.

### Medium-term (cross-channel playlist)
- Point at a playlist of voice-AI cold calls from multiple channels (any creator selling AI receptionist)
- No filter keywords needed (all are calls) — set `call_filter_keywords: []`
- Taxonomy will auto-discover voice-AI-specific categories from samples
- With 20-30 videos from multiple creators: expect 150-200 exchanges
- That's the production corpus threshold

### Niche-specific runs
Same pipeline, different playlist. For SEO sales calls: download SEO cold call playlist → run → auto-discovers SEO-specific objections. For website sales: same. The taxonomy discovery makes it self-configuring for any niche.

### Metaprogram layer (future)
After extraction, run a tagging pass that adds `metaprogram_tags` to each exchange:
- `toward` / `away_from` — does prospect move toward gain or away from pain?
- `internal` / `external` — does prospect trust their own judgment or need social proof?
- `options` / `procedures` — does prospect want flexibility or a step-by-step?
These come from the meta_programs truth builder work. Layering them onto exchanges lets the bot adapt its response style to the prospect's language pattern.

### Stage transition detection
Add a second extraction sweep that specifically hunts for `gate_moments` — the exact exchange where the conversation shifted. "Prospect said X → seller responded Y → tone changed → call advanced." These are the highest-value training examples and currently mixed in with regular exchanges.

### Multi-pass quality check
After extraction, run a spot-check pass: sample 10 random exchanges, grep each `text` field against its source transcript. 10/10 verbatim = corpus is clean. If any fail = something in the extraction prompt is allowing paraphrase. This is in the original spec but not yet implemented.
