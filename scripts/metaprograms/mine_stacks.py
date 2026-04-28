#!/usr/bin/env python3
"""
mine_stacks.py — Deterministic metaprogram stack scanner.

Walks a folder of transcripts, chunks each into 4 000-token windows with
500-token overlap, sends each chunk to Claude Sonnet for verbatim
multi-metaprogram stack detection.  Fully resumable: kill at any time,
restart safely — already-processed chunks are skipped.

Usage:
    python mine_stacks.py
    python mine_stacks.py E:\\path\\to\\transcripts
    python mine_stacks.py E:\\path\\to\\transcripts --output E:\\path\\output.md

Requirements:
    pip install anthropic tiktoken python-dotenv

Environment:
    ANTHROPIC_API_KEY   required
    ANTHROPIC_MODEL     optional, overrides default model
"""

import argparse
import asyncio
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# ── Dependency checks ──────────────────────────────────────────────────────────

try:
    import tiktoken
except ImportError:
    print("ERROR: tiktoken not installed.  Run: pip install tiktoken")
    sys.exit(1)

try:
    from anthropic import AsyncAnthropic, APIStatusError
except ImportError:
    print("ERROR: anthropic not installed.  Run: pip install anthropic")
    sys.exit(1)

try:
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv(usecwd=True))          # walk up from cwd
except ImportError:
    pass                                            # python-dotenv optional


# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

DEFAULT_FOLDER  = r"E:\AutoForge\Metaprograms\videos"
DEFAULT_OUTPUT  = r"E:\AutoForge\Metaprograms\stacks-rerun.md"
PROGRESS_FILE   = "_stack_mine_progress.json"
ERROR_LOG_FILE  = "_stack_mine_errors.log"

# Model: claude-sonnet-4-5-20250929 is verified Sonnet 4.5.
# If Sonnet 4.6 is available at your tier, set ANTHROPIC_MODEL in .env.
# e.g. ANTHROPIC_MODEL=claude-sonnet-4-6-20260201
DEFAULT_MODEL   = "claude-sonnet-4-5-20250929"

CHUNK_TOKENS    = 4_000
OVERLAP_TOKENS  = 500
MAX_CONCURRENCY = 5

# Retry delays on 429 rate-limit (seconds: 5 → 10 → 20 → 40)
BACKOFF_DELAYS  = [5, 10, 20, 40]

# Pricing per million tokens — update if Anthropic changes rates
PRICE = {
    "input":        3.00,    # standard input
    "output":      15.00,    # standard output
    "cache_write":  3.75,    # cache creation (1.25× input)
    "cache_read":   0.30,    # cache hit     (0.10× input)
}

# Speaker fingerprinting — substring match on lowercased full file path
SPEAKER_MAP = [
    ("anthony robbins", "Anthony Robbins"),
    ("tony robbins",    "Anthony Robbins"),
    ("charles faulkner","Charles Faulkner"),
    ("david shepherd",  "David Shepherd"),
    ("jordan peterson", "Jordan Peterson"),
    ("ben shapiro",     "Ben Shapiro"),
    ("matt james",      "Matt James"),
]


# ══════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT  (cached — identical across all API calls → big cost saving)
# ══════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """\
You are a metaprogram stack detector. Scan transcript chunks for sentences where a \
single speaker activates 2+ NLP metaprograms simultaneously in the SAME sentence or \
tightly-linked sentence pair.

CORE METAPROGRAMS:
- toward / away              (motivation direction: gain vs loss)
- internal / external        (reference frame: own judgment vs others' validation)
- match / mismatch           (sameness vs difference detection)
- convincer-see / convincer-hear / convincer-feel / convincer-do / convincer-times

TIER 2 (capture if clearly present):
options/procedures, general/specific, past/present/future, sameness-with-exception, \
person/thing/place/info/activity

STACK DEFINITION — ALL three must be true:
1. One coherent utterance (1 sentence, or 2 tightly-linked sentences max)
2. 2+ distinct metaprograms CLEARLY activated — not vaguely implied
3. Speaker is USING the programs on a listener — NOT lecturing/explaining them

DO NOT include:
- Single-metaprogram utterances
- Teaching passages ("the toward program means…" / meta-discussions about metaprograms)
- Anything paraphrased — verbatim only

OUTPUT FORMAT — strict JSON, nothing outside the JSON object:
{"stacks":[{"text":"verbatim quote","metaprograms":["away","internal"],"stack_size":2,\
"context_note":"brief note","confidence":"high|medium|low"}]}

No stacks found → {"stacks":[]}

VERBATIM DISCIPLINE: "text" must be copied character-for-character from the chunk. \
No rewording, no reconstruction, no summarising. If you cannot find exact words, skip it.\
"""


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def get_api_key() -> str:
    key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not key:
        print(
            "\nERROR: ANTHROPIC_API_KEY not set.\n"
            "Add to .env:  ANTHROPIC_API_KEY=sk-ant-...\n"
            "Script needs Sonnet for verbatim discipline — Haiku will paraphrase.\n"
        )
        sys.exit(1)
    return key


def get_model() -> str:
    return os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL).strip()


def infer_speaker(path: Path) -> str:
    haystack = str(path).lower()
    for needle, label in SPEAKER_MAP:
        if needle in haystack:
            return label
    return "UNKNOWN"


def strip_caption_header(text: str) -> str:
    """Remove YouTube caption header lines and join remaining into prose."""
    lines = text.splitlines()
    result = []
    past_header = False
    for line in lines:
        s = line.strip()
        if not past_header:
            if s in ("", "Kind: captions", "Language: en"):
                continue
            past_header = True
        if s:
            result.append(s)
    return " ".join(result)


def chunk_text(text: str, enc) -> list[str]:
    """Split into CHUNK_TOKENS-sized windows with OVERLAP_TOKENS overlap."""
    tokens = enc.encode(text)
    chunks: list[str] = []
    start = 0
    while start < len(tokens):
        end = min(start + CHUNK_TOKENS, len(tokens))
        chunks.append(enc.decode(tokens[start:end]))
        if end >= len(tokens):
            break
        start = end - OVERLAP_TOKENS
    return chunks


def calc_cost(in_tok: int, out_tok: int, cw_tok: int, cr_tok: int) -> float:
    return (
        (in_tok  / 1_000_000) * PRICE["input"]
        + (out_tok / 1_000_000) * PRICE["output"]
        + (cw_tok  / 1_000_000) * PRICE["cache_write"]
        + (cr_tok  / 1_000_000) * PRICE["cache_read"]
    )


def load_state(path: Path) -> dict:
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            for k in ("processed", ):
                data.setdefault(k, {})
            for k in ("input_tokens", "output_tokens", "cache_write_tokens",
                      "cache_read_tokens"):
                data.setdefault(k, 0)
            data.setdefault("cost_usd", 0.0)
            return data
        except Exception as e:
            print(f"Warning: progress file unreadable ({e}) — starting fresh.")
    return {
        "processed":          {},
        "input_tokens":       0,
        "output_tokens":      0,
        "cache_write_tokens": 0,
        "cache_read_tokens":  0,
        "cost_usd":           0.0,
    }


def save_state(path: Path, state: dict) -> None:
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def log_error(log_path: Path, source: str, chunk_idx: int, msg: str) -> None:
    ts    = datetime.now().isoformat(timespec="seconds")
    entry = f"[{ts}]  {source}  chunk={chunk_idx}  {msg}\n"
    print(f"  ⚠ {entry.strip()}", flush=True)
    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write(entry)


# ══════════════════════════════════════════════════════════════════════════════
# API CALL  (with prompt caching + backoff)
# ══════════════════════════════════════════════════════════════════════════════

async def call_api(
    client:       "AsyncAnthropic",
    model:        str,
    source_name:  str,
    chunk_idx:    int,
    total_chunks: int,
    chunk:        str,
    semaphore:    asyncio.Semaphore,
    log_path:     Path,
) -> tuple[list[dict], int, int, int, int]:
    """
    Returns (stacks, input_tokens, output_tokens, cache_write_tokens, cache_read_tokens).
    On unrecoverable failure returns ([], 0, 0, 0, 0) and logs the error.
    """
    user_msg = (
        f"Source video: {source_name}\n"
        f"Chunk {chunk_idx + 1} of {total_chunks}:\n\n"
        f"{chunk}\n\n"
        "Find stacks. JSON only."
    )

    delays_seq = [0] + BACKOFF_DELAYS   # [0, 5, 10, 20, 40]

    async with semaphore:
        for attempt, pre_sleep in enumerate(delays_seq):
            if pre_sleep:
                await asyncio.sleep(pre_sleep)
            raw = ""
            try:
                resp = await client.messages.create(
                    model=model,
                    max_tokens=2048,
                    system=[
                        {
                            "type": "text",
                            "text": SYSTEM_PROMPT,
                            "cache_control": {"type": "ephemeral"},
                        }
                    ],
                    messages=[{"role": "user", "content": user_msg}],
                )

                raw = resp.content[0].text.strip()

                # Strip accidental markdown fences
                m = re.search(r'\{[\s\S]*\}', raw)
                if m:
                    raw = m.group(0)

                parsed = json.loads(raw)
                raw_stacks = parsed.get("stacks", [])

                # Normalise + validate each stack entry
                stacks: list[dict] = []
                for s in raw_stacks:
                    if not isinstance(s, dict):
                        continue
                    if "text" not in s or "metaprograms" not in s:
                        continue
                    s["stack_size"] = len(s["metaprograms"])
                    s.setdefault("context_note", "")
                    s.setdefault("confidence", "medium")
                    stacks.append(s)

                u = resp.usage
                return (
                    stacks,
                    getattr(u, "input_tokens", 0),
                    getattr(u, "output_tokens", 0),
                    getattr(u, "cache_creation_input_tokens", 0),
                    getattr(u, "cache_read_input_tokens", 0),
                )

            except APIStatusError as e:
                if e.status_code == 429:
                    if attempt + 1 < len(delays_seq):
                        nxt = delays_seq[attempt + 1]
                        print(
                            f"  [429] rate-limited on {source_name} chunk {chunk_idx+1} "
                            f"— backing off {nxt}s (attempt {attempt+1}/{len(BACKOFF_DELAYS)})",
                            flush=True,
                        )
                        continue
                    log_error(log_path, source_name, chunk_idx,
                              "429 exhausted all retries — skipping chunk")
                    return [], 0, 0, 0, 0
                log_error(log_path, source_name, chunk_idx,
                          f"APIStatusError {e.status_code}: {getattr(e, 'message', str(e))}")
                return [], 0, 0, 0, 0

            except json.JSONDecodeError as e:
                snippet = raw[:300] if raw else "N/A"
                log_error(log_path, source_name, chunk_idx,
                          f"JSON parse failed: {e} | raw={snippet!r}")
                return [], 0, 0, 0, 0

            except Exception as e:
                log_error(log_path, source_name, chunk_idx,
                          f"{type(e).__name__}: {e}")
                return [], 0, 0, 0, 0

    # Unreachable — semaphore always releases — but keeps type-checker happy
    return [], 0, 0, 0, 0


# ══════════════════════════════════════════════════════════════════════════════
# PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

async def run(folder: Path, output_path: Path, limit: int = 0) -> None:
    model   = get_model()
    api_key = get_api_key()
    client  = AsyncAnthropic(api_key=api_key)

    out_dir = output_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    progress_path  = out_dir / PROGRESS_FILE
    error_log_path = out_dir / ERROR_LOG_FILE

    sep = "─" * 62
    print(f"\n{sep}")
    print("  Metaprogram Stack Miner")
    print(f"  Model:    {model}")
    print(f"  Folder:   {folder}")
    print(f"  Output:   {output_path}")
    print(f"  Progress: {progress_path}")
    print(f"{sep}\n")

    state = load_state(progress_path)
    print(f"Loaded progress: {len(state['processed'])} chunks done | "
          f"${state['cost_usd']:.4f} spent so far\n")

    # ── Find all transcript files ──────────────────────────────────────────────
    all_files = sorted(folder.rglob("*.txt"))
    if not all_files:
        print(f"ERROR: No .txt files found in {folder}")
        sys.exit(1)
    print(f"Found {len(all_files)} transcript files.")
    if limit > 0:
        all_files = all_files[:limit]
        print(f"--limit {limit}: processing first {len(all_files)} file(s) only.")

    # ── Tokeniser ─────────────────────────────────────────────────────────────
    try:
        enc = tiktoken.get_encoding("cl100k_base")
    except Exception:
        enc = tiktoken.get_encoding("gpt2")

    # ── Build work queue (skip already-processed chunks) ──────────────────────
    # Each item: (path, speaker, source_name, chunk_idx, total_chunks, chunk_text)
    WorkItem = tuple

    work_queue:   list[WorkItem] = []
    file_speakers: dict[str, str] = {}

    print("Scanning files and building work queue…", flush=True)
    for path in all_files:
        speaker     = infer_speaker(path)
        source_name = path.name
        path_str    = str(path)
        file_speakers[path_str] = speaker

        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            log_error(error_log_path, source_name, -1, f"Read error: {e}")
            continue

        cleaned = strip_caption_header(raw)
        if not cleaned.strip():
            continue

        chunks = chunk_text(cleaned, enc)
        total  = len(chunks)

        for idx, ck in enumerate(chunks):
            key = f"{path_str}::chunk_{idx}"
            if key not in state["processed"]:
                work_queue.append((path, speaker, source_name, idx, total, ck))

    total_new     = len(work_queue)
    total_skipped = len(state["processed"])
    print(f"Chunks to process: {total_new}  |  Already done: {total_skipped}\n")

    # ── Dispatch all tasks concurrently (semaphore limits to MAX_CONCURRENCY) ──
    if total_new > 0:
        semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
        lock      = asyncio.Lock()

        async def process_one(item: WorkItem) -> None:
            path, speaker, source_name, chunk_idx, total_chunks, ck = item
            key = f"{str(path)}::chunk_{chunk_idx}"

            stacks, in_tok, out_tok, cw_tok, cr_tok = await call_api(
                client, model, source_name, chunk_idx, total_chunks,
                ck, semaphore, error_log_path,
            )

            # Annotate with provenance
            for s in stacks:
                s["speaker"]     = speaker
                s["source_file"] = source_name
                s["source_path"] = str(path)

            cost = calc_cost(in_tok, out_tok, cw_tok, cr_tok)

            async with lock:
                state["processed"][key] = {
                    "stacks":     stacks,
                    "in_tokens":  in_tok,
                    "out_tokens": out_tok,
                    "ts":         datetime.now().isoformat(timespec="seconds"),
                }
                state["input_tokens"]       += in_tok
                state["output_tokens"]      += out_tok
                state["cache_write_tokens"] += cw_tok
                state["cache_read_tokens"]  += cr_tok
                state["cost_usd"]           += cost
                save_state(progress_path, state)   # persist after every chunk

            if stacks:
                print(
                    f"  ✓ {source_name}  chunk {chunk_idx+1}/{total_chunks}"
                    f"  → {len(stacks)} stack(s)",
                    flush=True,
                )

        tasks     = [asyncio.create_task(process_one(item)) for item in work_queue]
        done_cnt  = 0

        for fut in asyncio.as_completed(tasks):
            await fut
            done_cnt += 1
            if done_cnt % 10 == 0 or done_cnt == total_new:
                pct = done_cnt / total_new * 100
                print(
                    f"\r  Progress: {done_cnt}/{total_new} ({pct:.0f}%) "
                    f"| cost: ${state['cost_usd']:.4f}   ",
                    end="",
                    flush=True,
                )

        print()  # newline after progress counter
    else:
        print("Nothing new to process — all chunks already done.\n")

    # ── Collect all stacks from saved state ───────────────────────────────────
    all_stacks: list[dict] = []
    for key, entry in state["processed"].items():
        path_str   = key.split("::")[0]
        fp         = Path(path_str)
        speaker    = infer_speaker(fp)
        source_nm  = fp.name
        for s in entry.get("stacks", []):
            s.setdefault("speaker",     speaker)
            s.setdefault("source_file", source_nm)
            s.setdefault("source_path", path_str)
            all_stacks.append(s)

    # ── Print summary ──────────────────────────────────────────────────────────
    print(f"\n{sep}")
    print("  COMPLETE")
    print(f"  Total stacks found:    {len(all_stacks)}")
    print(f"  Total input tokens:    {state['input_tokens']:,}")
    print(f"  Total output tokens:   {state['output_tokens']:,}")
    print(f"  Cache writes:          {state['cache_write_tokens']:,}")
    print(f"  Cache reads:           {state['cache_read_tokens']:,}")
    print(f"  Total cost:            ${state['cost_usd']:.4f}")
    print(f"{sep}\n")

    write_output(all_stacks, all_files, state, output_path)
    print(f"Output written → {output_path}\n")


# ══════════════════════════════════════════════════════════════════════════════
# OUTPUT WRITER
# ══════════════════════════════════════════════════════════════════════════════

def write_output(
    stacks:    list[dict],
    all_files: list[Path],
    state:     dict,
    out:       Path,
) -> None:
    # Deduplicate by text (sort for idempotency)
    seen: set[str] = set()
    deduped: list[dict] = []
    for s in sorted(stacks, key=lambda x: (x.get("speaker", ""), x.get("text", ""))):
        t = s.get("text", "").strip()
        if t and t not in seen:
            seen.add(t)
            deduped.append(s)

    # Group by stack_size
    by_size: dict[int, list[dict]] = {}
    for s in deduped:
        sz = s.get("stack_size", len(s.get("metaprograms", [])))
        by_size.setdefault(sz, []).append(s)

    total    = len(deduped)
    speakers = sorted({s.get("speaker", "UNKNOWN") for s in deduped})
    ts       = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Per-source stack counts
    cov: dict[str, int] = {f.name: 0 for f in all_files}
    for s in deduped:
        fn = s.get("source_file", "")
        if fn in cov:
            cov[fn] += 1

    lines: list[str] = [
        "# Metaprogram Stacks (Re-run)",
        "",
        f"Total stacks found: {total}",
        f"Sources scanned: {len(all_files)} transcripts",
        f"Unique speakers: {', '.join(speakers) if speakers else 'none'}",
        f"Generated: {ts}",
        (
            f"Cost: ${state.get('cost_usd', 0):.4f}"
            f" | in: {state.get('input_tokens', 0):,}"
            f" | out: {state.get('output_tokens', 0):,}"
            f" | cache-write: {state.get('cache_write_tokens', 0):,}"
            f" | cache-read: {state.get('cache_read_tokens', 0):,}"
        ),
        "",
    ]

    for sz in sorted(by_size.keys(), reverse=True):
        heading = "## 5+ Program Stacks" if sz >= 5 else f"## {sz}-Program Stacks"
        lines.append(heading)
        lines.append("")
        for s in by_size[sz]:
            mps     = ", ".join(s.get("metaprograms", []))
            speaker = s.get("speaker", "UNKNOWN")
            source  = s.get("source_file", "")
            ctx     = s.get("context_note", "")
            conf    = s.get("confidence", "medium")
            text    = s.get("text", "")
            row     = f'- "{text}" — metaprograms: {mps} — speaker: {speaker} — source: {source}'
            if ctx:
                row += f" — context: {ctx}"
            row += f" — confidence: {conf}"
            lines.append(row)
        lines.append("")

    lines += ["## Source Coverage", ""]
    for fname in sorted(cov.keys()):
        lines.append(f"- {fname} — {cov[fname]} stack(s)")
    lines.append("")

    out.write_text("\n".join(lines), encoding="utf-8")


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Mine metaprogram stacks from transcripts using Claude Sonnet."
    )
    parser.add_argument(
        "folder",
        nargs="?",
        default=DEFAULT_FOLDER,
        help=f"Transcript folder (default: {DEFAULT_FOLDER})",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Output .md path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Only process the first N files (0 = no limit; use for smoke testing)",
    )
    args = parser.parse_args()
    asyncio.run(run(Path(args.folder), Path(args.output), limit=args.limit))
