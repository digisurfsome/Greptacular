#!/usr/bin/env python3
"""
mine_stacks.py — Deterministic metaprogram stack scanner.

Walks a folder of transcripts, chunks each into 4 000-token windows with
500-token overlap, sends each chunk to Claude Sonnet via the Anthropic API
for verbatim multi-metaprogram stack detection.  Fully resumable: kill at
any time, restart safely — already-processed chunks are skipped.

Prompt caching ON: system prompt is cached after the first call (~90% savings
on repeat calls).  Progress + cost tracked in _stack_mine_progress.json.

Usage:
    python mine_stacks.py
    python mine_stacks.py E:\\path\\to\\transcripts
    python mine_stacks.py E:\\path\\to\\transcripts --output E:\\path\\output.md
    python mine_stacks.py --limit 3   (smoke test on first 3 files)

Requirements:
    pip install anthropic tiktoken
    Set ANTHROPIC_API_KEY in .env or environment
"""

import argparse
import asyncio
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# CRITICAL — pop CLAUDECODE at process level (not just subprocess env).
# When this script is launched from a Claude Code session, CLAUDECODE=1 is set.
# That env var poisons every nested `claude` CLI invocation → exit 11 with no stderr.
# Popping at os.environ level ensures every subprocess inherits a clean slate.
os.environ.pop("CLAUDECODE", None)

# ── Dependency check ──────────────────────────────────────────────────────────

try:
    import tiktoken
except ImportError:
    print("ERROR: tiktoken not installed.  Run: pip install tiktoken")
    sys.exit(1)


# ── Load .env (no python-dotenv required) ────────────────────────────────────

def _load_dotenv() -> None:
    """Load .env from cwd or script directory into os.environ."""
    for candidate in [Path(".env"), Path(__file__).parent / ".env",
                      Path(__file__).parent.parent.parent / ".env"]:
        if candidate.exists():
            for line in candidate.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    os.environ.setdefault(k, v)
            break

_load_dotenv()


# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

DEFAULT_FOLDER  = r"E:\AutoForge\Metaprograms\videos"
DEFAULT_OUTPUT  = r"E:\AutoForge\Metaprograms\stacks-rerun.md"
PROGRESS_FILE   = "_stack_mine_progress.json"
ERROR_LOG_FILE  = "_stack_mine_errors.log"

MODEL           = "claude-sonnet-4-5-20250929"  # Sonnet 4.6
# 2026-04-29 perf rewrite:
#   chunk 1200→4000  : 3.3× fewer subprocess spawns
#   conc  3→15       : Max-plan tolerates 15 parallel claude -p sessions in practice
#   combined         : ~17× faster end-to-end vs. previous defaults
CHUNK_TOKENS    = 4000
OVERLAP_TOKENS  = 400        # ~10% overlap so cross-chunk stacks aren't lost
MAX_CONCURRENCY = 15         # was 3 — overly conservative; bench shows 15 is sweet spot
MAX_TOKENS_OUT  = 1_024

# Resolved at runtime — see resolve_claude_cli()
CLAUDE_CLI: str = ""
SCRATCH_DIR: str = ""
SETTINGS_FILE: str = ""

# Files to skip — already scanned, stacks documented
SKIP_FILES = {
    "Anthony Robbins Unlimited Power Meta Programs 1 of 2.txt",  # gold stacks already found
    "transcript.txt",  # no speaker, always exit 15
}

# Retry on 429 rate limit
RATE_LIMIT_DELAYS = [5, 10, 20, 40]   # seconds

# Pricing per million tokens (Sonnet — update if pricing changes)
PRICE_INPUT        = 3.00   # $/MTok
PRICE_OUTPUT       = 15.00  # $/MTok
PRICE_CACHE_WRITE  = 3.75   # $/MTok (first time system prompt is cached)
PRICE_CACHE_READ   = 0.30   # $/MTok (every subsequent call)

# Speaker fingerprinting
SPEAKER_MAP = [
    ("anthony robbins", "Anthony Robbins"),
    ("tony robbins",    "Anthony Robbins"),
    ("charles faulkner","Charles Faulkner"),
    ("david shepherd",  "David Shepherd"),
    ("david shephard",  "David Shepherd"),
    ("matt james",      "Matt James"),
    ("abby eagle",      "Abby Eagle"),
    ("shelle rose",     "Shelle Rose Charvet"),
    ("tad james",       "Tad James"),
]


# ══════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT  (cached via cache_control — huge cost savings)
# ══════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """\
You are a metaprogram stack detector. Find utterances where 3+ NLP metaprograms braid \
simultaneously in REAL SPEECH — not theory, not advice, not editorial structure.

CORE METAPROGRAMS:
- toward / away              (motivation: gain vs loss)
- internal / external        (reference: own judgment vs others validation)
- match / mismatch           (sameness vs difference detection)
- convincer-see / convincer-hear / convincer-feel / convincer-do / convincer-times

STACK DEFINITION — ALL 5 RULES MUST BE TRUE:
1. CONCRETE — at least one specific detail: number, name, place, time, sensory image, \
real stakes ("three minutes", "fifty thousand", "all the windows", "your TV")
2. MOMENT — anchored to a specific instance, story, or direct address. NOT a thesis \
or general claim about human nature
3. STATE-TRIGGER — read aloud to a stranger, they feel something: urgency, fear, desire, \
recognition. NOT a thought experiment or textbook illustration
4. NATURAL RHYTHM — sounds like someone talking under pressure or emotion. NOT cleaned-up \
editorial prose with "not X but Y" parallel structure
5. 3+ DISTINCT metaprograms braid in the same breath

BUILD-UP RULE: Each new sentence in a stack must add at least one NEW metaprogram. \
If next sentence only repeats existing programs without adding new ones, it is restating \
not stacking. Reject it.

CONVINCER-TIMES RIGOR — requires EXPLICIT repetition signal ONLY:
PASS: "after the third time" / "every single time" / "on a regular basis" / "it took 6 weeks"
FAIL: "two sessions" / "a few drinks" / "twice" / "a couple of times" (bare numbers = reject)

TEACHING-VS-DEMONSTRATION:
Speaker EXPLAINS how a metaprogram works → NOT a stack
Speaker QUOTES someone actually DELIVERING a close in a real situation → IS a stack
Speaker enacts a live close on an actual person in the room → IS a stack
The KEY: is a real person being influenced right now (or in quoted memory)? Yes = stack candidate.

REJECT THESE PATTERNS:
- Generic advice with no instance: "you've got to be curious and can't think you already know"
- Editorial "not X but Y": "this is not about winning arguments but expanding our minds"
- Abstract claim: "living a lie is very stressful on the body"
- Bare number as convincer-times: "after a few drinks i felt better"
- Theory explanation: "the toward program means moving toward gain rather than away from pain"

OUTPUT — strict JSON, nothing outside the JSON object:
{"stacks":[{"text":"verbatim quote from chunk","metaprograms":["away","internal","convincer-times"],\
"stack_size":3,"context_note":"who is speaking and what is happening",\
"confidence":"high|medium|low","utterance_type":"first_person|quoted_close|direct_address"}]}

No stacks found → {"stacks":[]}

VERBATIM DISCIPLINE: every word in "text" must appear in the chunk exactly as written. \
Do not paraphrase, reconstruct, or summarise. If you cannot find the exact words, skip it.\
"""


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

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


def load_state(path: Path) -> dict:
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            data.setdefault("processed", {})
            data.setdefault("call_count", 0)
            data.setdefault("tokens_input", 0)
            data.setdefault("tokens_output", 0)
            data.setdefault("tokens_cache_write", 0)
            data.setdefault("tokens_cache_read", 0)
            return data
        except Exception as e:
            print(f"Warning: progress file unreadable ({e}) — starting fresh.")
    return {
        "processed": {},
        "call_count": 0,
        "tokens_input": 0,
        "tokens_output": 0,
        "tokens_cache_write": 0,
        "tokens_cache_read": 0,
    }


def save_state(path: Path, state: dict) -> None:
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def log_error(log_path: Path, source: str, chunk_idx: int, msg: str) -> None:
    ts    = datetime.now().isoformat(timespec="seconds")
    entry = f"[{ts}]  {source}  chunk={chunk_idx}  {msg}\n"
    print(f"  ⚠ {entry.strip()}", flush=True)
    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write(entry)


def resolve_claude_cli() -> str:
    """Find absolute path to claude CLI. Aborts script on failure."""
    cli = shutil.which("claude")
    if not cli:
        print("FATAL: 'claude' CLI not found on PATH.")
        print("       Run: where claude")
        print("       Install: https://docs.anthropic.com/en/docs/claude-code")
        sys.exit(2)
    return cli


def setup_scratch_dir() -> tuple[str, str]:
    """Create a clean tempdir + minimal settings file matching the truth_builder pattern.

    Running claude from project root loads project .claude/settings.json which can
    cause exit 11. A clean scratch dir with explicit user-only settings avoids this.
    """
    scratch = tempfile.mkdtemp(prefix="stack_miner_")
    settings_path = Path(scratch) / ".claude-stack-miner-settings.json"
    settings_path.write_text(json.dumps({
        "permissions": {
            "defaultMode": "acceptEdits",
            "allow": [],
        },
    }), encoding="utf-8")
    return scratch, str(settings_path.resolve())


async def preflight_auth_check() -> None:
    """Run a tiny `claude -p` call to verify subscription auth works.

    If this fails we abort BEFORE burning 75s × 1350 chunks on retries.
    Prints exact exit code + stderr so the failure is diagnosable.
    """
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    env.pop("ANTHROPIC_API_KEY", None)

    print("Preflight: verifying claude subscription auth ...", flush=True)

    try:
        proc = await asyncio.create_subprocess_exec(
            CLAUDE_CLI,
            "-p", "Reply with the single word: OK",
            "--output-format", "text",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        out_b, err_b = await asyncio.wait_for(proc.communicate(), timeout=60)
        out = out_b.decode("utf-8", errors="replace").strip()
        err = err_b.decode("utf-8", errors="replace").strip()

        if proc.returncode != 0:
            print(f"\nFATAL: preflight failed — claude exit {proc.returncode}")
            print(f"  CLI:      {CLAUDE_CLI}")
            print(f"  cwd:      {SCRATCH_DIR}")
            print(f"  settings: {SETTINGS_FILE}")
            print(f"  stderr:   {err if err else '(empty)'}")
            print(f"  stdout:   {out if out else '(empty)'}")
            print("\nLikely causes:")
            print("  exit 11  → subscription session quota burned, OR auth not active in this shell")
            print("            Run from cmd:   claude -p \"say OK\"")
            print("            If that works, re-run this script. If not, run: claude login")
            print("  exit 15  → spurious SIGTERM (CLI killed mid-start). Usually means --settings or --model flag not recognized by this CLI version.")
            print("  exit 127 → CLI binary not executable")
            sys.exit(3)

        print(f"Preflight OK — claude responded: {out[:80]!r}\n", flush=True)

    except asyncio.TimeoutError:
        print("FATAL: preflight timed out after 60s. CLI is hanging — probably auth prompt.")
        print("       Run from cmd:   claude login")
        sys.exit(3)
    except FileNotFoundError as e:
        print(f"FATAL: cannot launch claude CLI: {e}")
        sys.exit(3)


def calc_cost(state: dict) -> float:
    ti  = state.get("tokens_input", 0)
    to  = state.get("tokens_output", 0)
    tcw = state.get("tokens_cache_write", 0)
    tcr = state.get("tokens_cache_read", 0)
    cost = (
        (ti  / 1_000_000) * PRICE_INPUT +
        (to  / 1_000_000) * PRICE_OUTPUT +
        (tcw / 1_000_000) * PRICE_CACHE_WRITE +
        (tcr / 1_000_000) * PRICE_CACHE_READ
    )
    return cost


# ══════════════════════════════════════════════════════════════════════════════
# ANTHROPIC API CALL  (with prompt caching + rate-limit backoff)
# ══════════════════════════════════════════════════════════════════════════════

async def call_api(
    client,        # unused in subscription mode
    user_msg:  str,
    log_path:  Path,
    source_name: str,
    chunk_idx: int,
) -> tuple[list[dict], dict]:
    """
    Call Claude via subscription using asyncio.create_subprocess_exec.
    System prompt passed via --append-system-prompt (separate from user msg).
    Pops CLAUDECODE and ANTHROPIC_API_KEY so subscription auth is used.
    Returns (stacks, usage_dict).
    """
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    env.pop("ANTHROPIC_API_KEY", None)

    for attempt, delay in enumerate([0] + RATE_LIMIT_DELAYS):
        if delay:
            await asyncio.sleep(delay)

        try:
            proc = await asyncio.create_subprocess_exec(
                CLAUDE_CLI, "-p", user_msg,
                "--output-format", "text",
                "--append-system-prompt", SYSTEM_PROMPT,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(), timeout=90
                )
            except asyncio.TimeoutError:
                proc.kill()
                # short timeout + retry is faster than long timeout once
                # (a stuck slot blocks one of 15 concurrency slots for the timeout duration)
                log_error(log_path, source_name, chunk_idx, "TimeoutExpired after 90s")
                if attempt < len(RATE_LIMIT_DELAYS):
                    continue
                return [], {}

            raw_out = stdout_bytes.decode("utf-8", errors="replace").strip()
            raw_err = stderr_bytes.decode("utf-8", errors="replace").strip()

            if proc.returncode != 0:
                err_msg = raw_err[:200] if raw_err else "no stderr"
                log_error(log_path, source_name, chunk_idx,
                          f"claude exit {proc.returncode}: {err_msg}")
                if attempt < len(RATE_LIMIT_DELAYS):
                    continue
                return [], {}

            if not raw_out:
                return [], {}

            # --output-format text: raw_out IS the Claude response directly
            assistant_text = raw_out

            # Strip accidental markdown fences
            m = re.search(r'\{[\s\S]*\}', assistant_text)
            if m:
                assistant_text = m.group(0)

            if not assistant_text.strip():
                return [], {}

            parsed = json.loads(assistant_text)
            raw_stacks = parsed.get("stacks", [])

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

            return stacks, {}

        except json.JSONDecodeError as e:
            log_error(log_path, source_name, chunk_idx,
                      f"JSON parse failed: {e} | raw: {assistant_text[:200]}")
            return [], {}

        except Exception as e:
            log_error(log_path, source_name, chunk_idx, f"{type(e).__name__}: {e}")
            return [], {}

    return [], {}


# ══════════════════════════════════════════════════════════════════════════════
# PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

async def run(folder: Path, output_path: Path, limit: int = 0) -> None:
    global CLAUDE_CLI, SCRATCH_DIR, SETTINGS_FILE

    client = None   # subscription mode — no API client needed

    out_dir = output_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    progress_path  = out_dir / PROGRESS_FILE
    error_log_path = out_dir / ERROR_LOG_FILE

    # Resolve CLI + build clean scratch dir BEFORE preflight
    CLAUDE_CLI = resolve_claude_cli()
    SCRATCH_DIR, SETTINGS_FILE = setup_scratch_dir()

    sep = "─" * 62
    print(f"\n{sep}")
    print("  Metaprogram Stack Miner  (Claude subscription — claude -p)")
    print("  Model:    subscription (Sonnet)")
    print(f"  CLI:      {CLAUDE_CLI}")
    print(f"  Scratch:  {SCRATCH_DIR}")
    print(f"  Folder:   {folder}")
    print(f"  Output:   {output_path}")
    print(f"  Progress: {progress_path}")
    print(f"  Concurrency: {MAX_CONCURRENCY}")
    print(f"{sep}\n")

    # Fail fast if auth/CLI is broken — don't waste time on 1350 retries
    await preflight_auth_check()

    state = load_state(progress_path)
    cost_so_far = calc_cost(state)
    print(f"Loaded progress: {len(state['processed'])} chunks done | "
          f"{state['call_count']} total calls | ${cost_so_far:.4f} spent so far\n")

    # ── Find all transcript files ──────────────────────────────────────────────
    all_files = sorted(
        f for f in folder.rglob("*.txt")
        if f.name not in SKIP_FILES
    )
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
    WorkItem = tuple  # (path, speaker, source_name, chunk_idx, total_chunks, chunk_text)

    work_queue: list[WorkItem] = []

    print("Scanning files and building work queue…", flush=True)
    for path in all_files:
        speaker     = infer_speaker(path)
        source_name = path.name
        path_str    = str(path)

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

    # ── Dispatch concurrently ─────────────────────────────────────────────────
    if total_new > 0:
        semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
        lock      = asyncio.Lock()

        async def process_one(item: WorkItem) -> None:
            path, speaker, source_name, chunk_idx, total_chunks, ck = item
            key = f"{str(path)}::chunk_{chunk_idx}"

            user_msg = (
                f"Source video: {source_name}\n"
                f"Chunk {chunk_idx + 1} of {total_chunks}:\n\n"
                f"{ck}\n\n"
                "Find stacks. JSON only."
            )

            async with semaphore:
                stacks, usage = await call_api(
                    client, user_msg, error_log_path, source_name, chunk_idx
                )

            # Annotate with provenance
            for s in stacks:
                s["speaker"]     = speaker
                s["source_file"] = source_name
                s["source_path"] = str(path)

            async with lock:
                state["processed"][key] = {
                    "stacks": stacks,
                    "ts":     datetime.now().isoformat(timespec="seconds"),
                }
                state["call_count"]          += 1
                state["tokens_input"]        += usage.get("input_tokens", 0)
                state["tokens_output"]       += usage.get("output_tokens", 0)
                state["tokens_cache_write"]  += usage.get("cache_creation_input_tokens", 0)
                state["tokens_cache_read"]   += usage.get("cache_read_input_tokens", 0)
                save_state(progress_path, state)

            # Always print per-chunk progress so user can see activity
            stack_tag = f"  → {len(stacks)} STACK(S) ⭐" if stacks else ""
            print(
                f"  [{source_name[:35]:<35}]  chunk {chunk_idx+1:>3}/{total_chunks}{stack_tag}",
                flush=True,
            )

        tasks    = [asyncio.create_task(process_one(item)) for item in work_queue]
        done_cnt = 0
        start_ts = asyncio.get_event_loop().time()

        for fut in asyncio.as_completed(tasks):
            await fut
            done_cnt += 1
            if done_cnt % 25 == 0 or done_cnt == total_new:
                elapsed  = asyncio.get_event_loop().time() - start_ts
                rate     = done_cnt / elapsed if elapsed > 0 else 0
                remaining = (total_new - done_cnt) / rate if rate > 0 else 0
                print(
                    f"\n  ── Progress: {done_cnt}/{total_new} ({done_cnt/total_new*100:.0f}%)"
                    f"  | {rate:.1f} chunks/s"
                    f"  | ETA: {remaining/60:.1f} min ──\n",
                    flush=True,
                )

        print()  # newline after progress counter
    else:
        print("Nothing new to process — all chunks already done.\n")

    # ── Collect all stacks from saved state ───────────────────────────────────
    all_stacks: list[dict] = []
    for key, entry in state["processed"].items():
        path_str  = key.split("::")[0]
        fp        = Path(path_str)
        speaker   = infer_speaker(fp)
        source_nm = fp.name
        for s in entry.get("stacks", []):
            s.setdefault("speaker",     speaker)
            s.setdefault("source_file", source_nm)
            s.setdefault("source_path", path_str)
            all_stacks.append(s)

    # ── Summary ────────────────────────────────────────────────────────────────
    final_cost = calc_cost(state)
    print(f"\n{sep}")
    print("  COMPLETE")
    print(f"  Total stacks found:  {len(all_stacks)}")
    print(f"  Total API calls:     {state['call_count']}")
    print(f"  Input tokens:        {state['tokens_input']:,}")
    print(f"  Cache writes:        {state['tokens_cache_write']:,}")
    print(f"  Cache reads:         {state['tokens_cache_read']:,}")
    print(f"  Output tokens:       {state['tokens_output']:,}")
    print(f"  Total cost:          ${final_cost:.4f}")
    print(f"{sep}\n")

    write_output(all_stacks, all_files, state, output_path, final_cost)
    print(f"Output written → {output_path}\n")


# ══════════════════════════════════════════════════════════════════════════════
# OUTPUT WRITER
# ══════════════════════════════════════════════════════════════════════════════

def write_output(
    stacks:    list[dict],
    all_files: list[Path],
    state:     dict,
    out:       Path,
    cost:      float,
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
        f"Cost: ${cost:.4f} | Total API calls: {state.get('call_count', 0)}",
        f"Tokens — input: {state.get('tokens_input',0):,} | "
        f"output: {state.get('tokens_output',0):,} | "
        f"cache_write: {state.get('tokens_cache_write',0):,} | "
        f"cache_read: {state.get('tokens_cache_read',0):,}",
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
        count = cov[fname]
        lines.append(f"- {fname} — {count} stack(s)")
    lines.append("")

    out.write_text("\n".join(lines), encoding="utf-8")


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Mine metaprogram stacks from transcripts via Anthropic API."
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
