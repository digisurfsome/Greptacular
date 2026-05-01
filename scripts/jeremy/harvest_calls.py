#!/usr/bin/env python3
"""
harvest_calls.py — Jeremy Call Library Harvester

Reads YouTube URLs from the inbox, transcribes via Deepgram (transcribe_call.py),
runs Claude stage-tagging + NEPQ analysis, writes annotated transcripts,
and maintains the call library index.

Pipeline per URL:
    1. Read _inbox.md, collect unprocessed URLs
    2. Determine type (cold/sales) from inline annotation or default to sales
    3. Call transcribe_call.py subprocess -> get transcript + slug
    4. Run Claude stage-tagging + analysis via subscription (claude -p)
    5. Write output to calls/cold-calls/{slug}.txt or calls/sales-calls/{slug}.txt
    6. Append row to _index.md

Fully resumable — tracks processed slugs in _harvest_progress.json.

Usage:
    cd C:\\Users\\lober\\.autoforge\\workspace\\repos\\digisurfsome__Greptacular
    python scripts/jeremy/harvest_calls.py
    python scripts/jeremy/harvest_calls.py --limit 3      # only process 3 URLs
    python scripts/jeremy/harvest_calls.py --dry-run       # no API calls
    python scripts/jeremy/harvest_calls.py --reprocess {slug}  # force re-analyze one

Requirements:
    yt-dlp, ffmpeg on PATH
    DEEPGRAM_API_KEY in .env or environment
    claude login  (subscription — no API key needed)
"""

import argparse
import asyncio
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

# ── Pop CLAUDECODE at import time so every subprocess inherits clean env ───────
os.environ.pop("CLAUDECODE", None)


# ── Load .env (no python-dotenv required) ────────────────────────────────────
def _load_dotenv() -> None:
    for candidate in [
        Path(".env"),
        Path(__file__).parent / ".env",
        Path(__file__).parent.parent.parent / ".env",
    ]:
        if candidate.exists():
            for line in candidate.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
            break


_load_dotenv()


# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

REPO_ROOT = Path(__file__).parent.parent.parent

CALLS_DIR      = REPO_ROOT / "docs/info/jeremy-miner-corpus/calls"
INBOX_FILE     = CALLS_DIR / "_inbox.md"
INDEX_FILE     = CALLS_DIR / "_index.md"
PROGRESS_FILE  = CALLS_DIR / "_harvest_progress.json"
ERROR_LOG      = CALLS_DIR / "_harvest_errors.log"
COLD_DIR       = CALLS_DIR / "cold-calls"
SALES_DIR      = CALLS_DIR / "sales-calls"
TRANSCRIBE_SCRIPT = Path(__file__).parent / "transcribe_call.py"

MODEL          = "claude-sonnet-4-6"
CALL_TIMEOUT   = 300       # Claude analysis can take a while on long transcripts
RETRY_DELAYS   = [2, 5, 10]

# Resolved at runtime
CLAUDE_CLI: str = ""


# ══════════════════════════════════════════════════════════════════════════════
# CLAUDE PROMPT TEMPLATE
# ══════════════════════════════════════════════════════════════════════════════

ANALYSIS_PROMPT_TEMPLATE = """\
You are analyzing a Jeremy Miner sales/cold call transcript for NEPQ stage mapping and pattern extraction.

CALL TYPE: {call_type}

TRANSCRIPT:
{transcript_text}

---

TASK 1 — STAGE-TAG THE TRANSCRIPT:
For each speaker turn, identify which NEPQ stage it belongs to. Add inline tags after each turn.
NEPQ stages: [CONNECTING], [SITUATION], [PROB-AW], [SOL-AW], [CONSEQUENCE], [TRANSITION], [COMMITMENT]
Use [CONNECTING] for opening rapport, [SITUATION] for discovery questions, [PROB-AW] for problem awareness questions, [SOL-AW] for solution awareness, [CONSEQUENCE] for implication questions, [TRANSITION] for bridge to presentation, [COMMITMENT] for close.
Keep every verbatim line intact. Add the tag on the next line below the speaker turn.

TASK 2 — CALL ANALYSIS:
After the tagged transcript, output exactly this structure:

---
## Call Analysis — {slug}

**Length:** {length_placeholder}
**Type:** {call_type}
**Outcome:** booked | closed | passed | callback | unknown

### Stage transitions (estimated)
- Connecting -> Situation: ~{{timestamp}}
- Situation -> Problem-Aw: ~{{timestamp}}
(list all transitions you detect)

### Hook (first 30s)
> "{{verbatim opening line(s)}}"
Pattern type: disrupt | curious-question | permission-frame | name-the-pain

### Objection rolls (verbatim, with handler)
1. Prospect: "{{objection verbatim}}"
   Jeremy: "{{response verbatim}}"
   Tactic: {{NEPQ tactic name, e.g. "clarification question", "consequence amplifier"}}

### Close cadence (commitment stage)
> "{{verbatim 2-4 turns ending in commitment}}"

### Stacks detected
{{List any 3+ linked problem-consequence-urgency braid. Quote verbatim. If none: "None detected."}}

### Voice-agent training notes
- Pause patterns: {{observed patterns, e.g. "pauses after consequence questions"}}
- Tonality shifts: {{soft / direct / curious moments}}
- Pacing estimate: {{fast / medium / slow}}

OUTPUT FORMAT: Return ONLY the tagged transcript followed by the ## Call Analysis section. No preamble, no explanation.\
"""


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def resolve_claude_cli() -> str:
    """Find claude CLI binary on PATH or fallback location."""
    cli = shutil.which("claude")
    if cli:
        return cli
    # Fallback: common install location
    fallback = Path.home() / ".claude" / "bin" / "claude"
    if fallback.exists():
        return str(fallback)
    print("FATAL: 'claude' CLI not found on PATH or ~/.claude/bin/claude.")
    print("       Install Claude Code: https://docs.anthropic.com/en/docs/claude-code")
    sys.exit(2)


def load_state(path: Path) -> dict:
    """Load progress state from JSON file. Returns fresh state if missing/corrupt."""
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            data.setdefault("processed_slugs", [])
            data.setdefault("processed_urls", [])
            data.setdefault("call_count", 0)
            return data
        except Exception as e:
            print(f"Warning: progress file unreadable ({e}) — starting fresh.")
    return {"processed_slugs": [], "processed_urls": [], "call_count": 0}


def save_state(path: Path, state: dict) -> None:
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def log_error(msg: str) -> None:
    ts = datetime.now().isoformat(timespec="seconds")
    entry = f"[{ts}]  {msg}\n"
    print(f"  ERROR: {entry.strip()}", flush=True)
    with open(ERROR_LOG, "a", encoding="utf-8") as fh:
        fh.write(entry)


def parse_inbox(inbox_path: Path) -> list[tuple[str, str]]:
    """Parse _inbox.md and return list of (url, type) tuples.

    Lines in the ## URLs section can be:
        https://youtube.com/watch?v=xxx cold
        https://youtube.com/watch?v=xxx sales
        https://youtube.com/watch?v=xxx          (defaults to sales)
    Skips blank lines, comments, and markdown formatting.
    """
    if not inbox_path.exists():
        print(f"FATAL: inbox file not found: {inbox_path}")
        sys.exit(1)

    text = inbox_path.read_text(encoding="utf-8")
    entries: list[tuple[str, str]] = []

    in_urls_section = False
    for line in text.splitlines():
        stripped = line.strip()

        # Detect ## URLs section
        if stripped.startswith("## URLs"):
            in_urls_section = True
            continue

        # Stop at next section header
        if stripped.startswith("## ") and in_urls_section:
            break

        if not in_urls_section:
            continue

        # Skip empty lines, comments, markdown artifacts
        if not stripped or stripped.startswith("<!--") or stripped.startswith("#"):
            continue

        # Parse URL and optional type
        parts = stripped.split()
        url = parts[0]

        # Basic URL validation
        if not (url.startswith("http://") or url.startswith("https://")):
            continue

        call_type = "sales"  # default
        if len(parts) >= 2 and parts[1].lower() in ("cold", "sales"):
            call_type = parts[1].lower()

        entries.append((url, call_type))

    return entries


def estimate_length_from_transcript(transcript: str) -> str:
    """Estimate call length from last timestamp in transcript."""
    # Find all timestamps in [SPEAKER_X HH:MM:SS] or [SPEAKER_X MM:SS] format
    timestamps = re.findall(r"\[SPEAKER_\d+\s+(\d+:\d+(?::\d+)?)\]", transcript)
    if not timestamps:
        return "unknown"

    last_ts = timestamps[-1]
    return last_ts


def parse_analysis_field(analysis_text: str, field: str) -> str:
    """Extract a field value from the Call Analysis block."""
    pattern = rf"\*\*{re.escape(field)}:\*\*\s*(.+)"
    m = re.search(pattern, analysis_text)
    if m:
        # Take first word/value (e.g., "booked | closed" -> first real value)
        raw = m.group(1).strip()
        # If it contains pipes, Claude filled in the actual value (not the template)
        if "|" not in raw:
            return raw
        # Template wasn't filled — return "unknown"
        return "unknown"
    return "unknown"


def parse_stages_found(analysis_text: str) -> str:
    """Extract which NEPQ stages appear in the tagged transcript."""
    stage_tags = re.findall(
        r"\[(CONNECTING|SITUATION|PROB-AW|SOL-AW|CONSEQUENCE|TRANSITION|COMMITMENT)\]",
        analysis_text,
    )
    unique = list(dict.fromkeys(stage_tags))  # preserve order, deduplicate
    return ", ".join(unique) if unique else "none"


def count_stacks(analysis_text: str) -> str:
    """Count stacks detected in the analysis."""
    # Look for the stacks section
    stacks_match = re.search(
        r"### Stacks detected\s*\n(.*?)(?:\n###|\Z)",
        analysis_text,
        re.DOTALL,
    )
    if not stacks_match:
        return "0"
    content = stacks_match.group(1).strip()
    if "none detected" in content.lower() or not content:
        return "0"
    # Count numbered items or quoted blocks
    items = re.findall(r"^\d+\.", content, re.MULTILINE)
    if items:
        return str(len(items))
    # Count quote blocks as individual stacks
    quotes = re.findall(r'^>', content, re.MULTILINE)
    return str(max(1, len(quotes))) if quotes else "1"


# ══════════════════════════════════════════════════════════════════════════════
# PREFLIGHT
# ══════════════════════════════════════════════════════════════════════════════

async def preflight_auth_check() -> None:
    """Verify claude CLI is authenticated before starting pipeline."""
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    env.pop("ANTHROPIC_API_KEY", None)

    print("Preflight: verifying claude subscription auth ...", flush=True)

    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            proc = await asyncio.create_subprocess_exec(
                CLAUDE_CLI, "-p", "say only the word OK",
                "--model", MODEL,
                "--output-format", "text",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            out_b, err_b = await asyncio.wait_for(proc.communicate(), timeout=60)
            out = out_b.decode("utf-8", errors="replace").strip()
            err = err_b.decode("utf-8", errors="replace").strip()

            if proc.returncode == 0:
                print(f"Preflight OK — claude says: {out[:60]!r}\n", flush=True)
                return

            # Exit code 15 = transient — retry
            if proc.returncode in (15, 3) and attempt < max_attempts - 1:
                delay = [2, 5, 10][attempt]
                print(f"  Preflight exit {proc.returncode} — retrying in {delay}s ...", flush=True)
                await asyncio.sleep(delay)
                continue

            print(f"\nFATAL: preflight failed — exit {proc.returncode}")
            print(f"  stderr: {err[:300] if err else '(empty)'}")
            print(f"  stdout: {out[:300] if out else '(empty)'}")
            print("\nFix: run `claude login` then retry.")
            sys.exit(3)

        except asyncio.TimeoutError:
            if attempt < max_attempts - 1:
                print(f"  Preflight timed out — retrying ...", flush=True)
                continue
            print("FATAL: preflight timed out. Auth prompt hanging — run `claude login`.")
            sys.exit(3)
        except FileNotFoundError as e:
            print(f"FATAL: cannot launch claude CLI: {e}")
            sys.exit(3)

    print("FATAL: preflight exhausted all retries.")
    sys.exit(3)


# ══════════════════════════════════════════════════════════════════════════════
# TRANSCRIPTION STEP
# ══════════════════════════════════════════════════════════════════════════════

async def run_transcription(url: str) -> tuple[str, str, str]:
    """Run transcribe_call.py as subprocess. Returns (transcript_text, slug, title).

    Raises RuntimeError on failure.
    """
    import tempfile

    # Create temp file for transcript output
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".txt", prefix="transcript_")
    os.close(tmp_fd)

    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, str(TRANSCRIBE_SCRIPT),
            url, "--output", tmp_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        out_b, err_b = await asyncio.wait_for(proc.communicate(), timeout=900)
        out = out_b.decode("utf-8", errors="replace")
        err = err_b.decode("utf-8", errors="replace")

        if proc.returncode != 0:
            raise RuntimeError(
                f"transcribe_call.py failed (exit {proc.returncode}): "
                f"{err[:300] if err else out[:300]}"
            )

        # Parse __META__ line from stdout
        slug = "unknown"
        title = "Unknown"
        for line in out.splitlines():
            if line.startswith("__META__:"):
                meta = json.loads(line[len("__META__:"):])
                slug = meta.get("slug", slug)
                title = meta.get("title", title)
                break

        # Read transcript from output file
        transcript = Path(tmp_path).read_text(encoding="utf-8")
        if not transcript.strip():
            raise RuntimeError("Transcript file is empty")

        return transcript, slug, title

    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


# ══════════════════════════════════════════════════════════════════════════════
# CLAUDE ANALYSIS STEP
# ══════════════════════════════════════════════════════════════════════════════

async def analyze_with_claude(
    transcript: str,
    call_type: str,
    slug: str,
) -> str:
    """Send transcript to Claude for NEPQ stage-tagging and analysis.

    Returns Claude's full output (tagged transcript + analysis).
    """
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    env.pop("ANTHROPIC_API_KEY", None)

    # Estimate length from transcript timestamps
    length_est = estimate_length_from_transcript(transcript)

    prompt = ANALYSIS_PROMPT_TEMPLATE.format(
        call_type=call_type,
        transcript_text=transcript,
        slug=slug,
        length_placeholder=f"~{length_est} (estimated from transcript)",
    )

    for attempt, delay in enumerate([0] + RETRY_DELAYS):
        if delay:
            print(f"    Retrying Claude in {delay}s (attempt {attempt + 1}) ...", flush=True)
            await asyncio.sleep(delay)

        try:
            proc = await asyncio.create_subprocess_exec(
                CLAUDE_CLI, "-p", prompt,
                "--model", MODEL,
                "--output-format", "text",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            try:
                out_b, err_b = await asyncio.wait_for(
                    proc.communicate(), timeout=CALL_TIMEOUT
                )
            except asyncio.TimeoutError:
                proc.kill()
                log_error(f"{slug}  Claude timeout after {CALL_TIMEOUT}s")
                if attempt < len(RETRY_DELAYS):
                    continue
                raise RuntimeError(f"Claude analysis timed out for {slug}")

            raw_out = out_b.decode("utf-8", errors="replace").strip()
            raw_err = err_b.decode("utf-8", errors="replace").strip()

            if proc.returncode != 0:
                # Exit 15 / 3 = transient failures worth retrying
                if proc.returncode in (15, 3) and attempt < len(RETRY_DELAYS):
                    log_error(f"{slug}  Claude exit {proc.returncode} — retrying")
                    continue
                raise RuntimeError(
                    f"Claude failed for {slug} (exit {proc.returncode}): "
                    f"{raw_err[:200] if raw_err else raw_out[:200]}"
                )

            if not raw_out:
                raise RuntimeError(f"Claude returned empty output for {slug}")

            return raw_out

        except Exception as e:
            if attempt < len(RETRY_DELAYS) and "timed out" not in str(e):
                log_error(f"{slug}  {type(e).__name__}: {e}")
                continue
            raise

    raise RuntimeError(f"Claude analysis exhausted all retries for {slug}")


# ══════════════════════════════════════════════════════════════════════════════
# OUTPUT WRITER
# ══════════════════════════════════════════════════════════════════════════════

def write_call_output(
    slug: str,
    call_type: str,
    url: str,
    title: str,
    analysis: str,
) -> Path:
    """Write the final annotated transcript + analysis to the appropriate directory."""
    target_dir = COLD_DIR if call_type == "cold" else SALES_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    out_path = target_dir / f"{slug}.txt"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    content = (
        f"# {title}\n"
        f"URL: {url}\n"
        f"Slug: {slug}\n"
        f"Type: {call_type}\n"
        f"Transcribed: {now}\n"
        f"Analyzed: {now}\n"
        f"\n"
        f"{analysis}\n"
    )

    out_path.write_text(content, encoding="utf-8")
    return out_path


def append_index_row(
    slug: str,
    call_type: str,
    analysis: str,
) -> None:
    """Append a row to _index.md with parsed metadata from Claude's analysis."""
    length = estimate_length_from_transcript(analysis)
    outcome = parse_analysis_field(analysis, "Outcome")
    stages = parse_stages_found(analysis)
    stacks = count_stacks(analysis)
    date = datetime.now().strftime("%Y-%m-%d")

    row = f"| {slug} | {call_type} | {length} | {outcome} | {stages} | {stacks} | {date} |\n"

    # Append to index file
    with open(INDEX_FILE, "a", encoding="utf-8") as f:
        f.write(row)


# ══════════════════════════════════════════════════════════════════════════════
# PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

async def process_one_url(
    url: str,
    call_type: str,
    state: dict,
    dry_run: bool = False,
) -> bool:
    """Process a single URL through the full pipeline. Returns True on success."""
    print(f"\n  Processing: {url}", flush=True)
    print(f"  Type: {call_type}", flush=True)

    if dry_run:
        print("  [DRY RUN] Would transcribe, analyze, and write output.", flush=True)
        return True

    # Step 1: Transcribe
    print("  Step 1/3: Transcribing via Deepgram ...", flush=True)
    try:
        transcript, slug, title = await run_transcription(url)
    except Exception as e:
        log_error(f"Transcription failed for {url}: {e}")
        return False

    print(f"  Slug: {slug}", flush=True)
    print(f"  Title: {title}", flush=True)
    print(f"  Transcript: {len(transcript)} chars, {transcript.count(chr(10)) + 1} lines", flush=True)

    # Check if already processed (by slug)
    if slug in state["processed_slugs"]:
        print(f"  Slug {slug} already processed — skipping.", flush=True)
        return True

    # Step 2: Claude analysis
    print("  Step 2/3: Claude NEPQ analysis ...", flush=True)
    try:
        analysis = await analyze_with_claude(transcript, call_type, slug)
    except Exception as e:
        log_error(f"Claude analysis failed for {slug}: {e}")
        return False

    print(f"  Analysis: {len(analysis)} chars", flush=True)

    # Step 3: Write output + update index
    print("  Step 3/3: Writing output ...", flush=True)
    out_path = write_call_output(slug, call_type, url, title, analysis)
    append_index_row(slug, call_type, analysis)

    # Update progress state
    state["processed_slugs"].append(slug)
    state["processed_urls"].append(url)
    state["call_count"] += 1
    save_state(PROGRESS_FILE, state)

    print(f"  Done: {out_path}", flush=True)
    return True


async def reprocess_slug(slug: str, state: dict) -> bool:
    """Force re-analyze an existing transcript by slug.

    Finds the existing .txt file, re-reads the URL from it, re-runs Claude analysis,
    and overwrites the file.
    """
    # Find the existing file
    existing = None
    for d in [COLD_DIR, SALES_DIR]:
        candidate = d / f"{slug}.txt"
        if candidate.exists():
            existing = candidate
            break

    if not existing:
        print(f"FATAL: no existing file found for slug '{slug}'")
        print(f"  Looked in: {COLD_DIR} and {SALES_DIR}")
        sys.exit(1)

    # Parse URL and type from the file header
    text = existing.read_text(encoding="utf-8")
    url_match = re.search(r"^URL:\s*(.+)$", text, re.MULTILINE)
    type_match = re.search(r"^Type:\s*(.+)$", text, re.MULTILINE)

    if not url_match:
        print(f"FATAL: cannot find URL in {existing}")
        sys.exit(1)

    url = url_match.group(1).strip()
    call_type = type_match.group(1).strip() if type_match else "sales"
    title_match = re.search(r"^# (.+)$", text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else slug

    print(f"  Reprocessing: {slug}", flush=True)
    print(f"  URL: {url}", flush=True)
    print(f"  Type: {call_type}", flush=True)

    # Re-transcribe
    print("  Step 1/3: Re-transcribing ...", flush=True)
    try:
        transcript, _, _ = await run_transcription(url)
    except Exception as e:
        log_error(f"Re-transcription failed for {slug}: {e}")
        return False

    # Re-analyze
    print("  Step 2/3: Re-analyzing with Claude ...", flush=True)
    try:
        analysis = await analyze_with_claude(transcript, call_type, slug)
    except Exception as e:
        log_error(f"Re-analysis failed for {slug}: {e}")
        return False

    # Overwrite
    print("  Step 3/3: Writing output ...", flush=True)
    out_path = write_call_output(slug, call_type, url, title, analysis)
    print(f"  Reprocessed: {out_path}", flush=True)
    return True


async def run(
    limit: int = 0,
    dry_run: bool = False,
    reprocess: str | None = None,
) -> None:
    global CLAUDE_CLI

    CALLS_DIR.mkdir(parents=True, exist_ok=True)
    COLD_DIR.mkdir(parents=True, exist_ok=True)
    SALES_DIR.mkdir(parents=True, exist_ok=True)

    sep = "=" * 66
    print(f"\n{sep}")
    print("  Jeremy Call Library Harvester")
    print(f"  Model:   {MODEL}  (Sonnet — subscription)")
    print(f"  Inbox:   {INBOX_FILE}")
    print(f"  Output:  {CALLS_DIR}")
    print(f"{sep}\n")

    CLAUDE_CLI = resolve_claude_cli()
    print(f"Claude CLI: {CLAUDE_CLI}\n", flush=True)

    state = load_state(PROGRESS_FILE)
    print(
        f"Progress: {len(state['processed_slugs'])} slugs done | "
        f"{state['call_count']} calls processed\n"
    )

    # Handle --reprocess mode
    if reprocess:
        if not dry_run:
            await preflight_auth_check()
        ok = await reprocess_slug(reprocess, state)
        if ok:
            print("\nReprocess complete.")
        else:
            print("\nReprocess FAILED — check error log.")
            sys.exit(1)
        return

    # Normal mode: read inbox
    entries = parse_inbox(INBOX_FILE)
    if not entries:
        print("Inbox is empty — no URLs to process.")
        print(f"Add YouTube URLs to: {INBOX_FILE}")
        return

    print(f"Inbox: {len(entries)} URL(s) found", flush=True)

    # Filter out already-processed URLs
    pending = [
        (url, ctype) for url, ctype in entries
        if url not in state["processed_urls"]
    ]

    if limit > 0:
        pending = pending[:limit]

    print(f"Pending: {len(pending)} URL(s) to process", flush=True)

    if not pending:
        print("All URLs already processed. Nothing to do.")
        return

    if dry_run:
        print("\n=== DRY RUN ===")
        for url, ctype in pending:
            print(f"  [{ctype}] {url}")
        print("\nDry run done. No API calls made.")
        return

    # Preflight auth check
    await preflight_auth_check()

    # Process URLs sequentially (each involves download + Deepgram + Claude)
    success = 0
    failed = 0
    for i, (url, ctype) in enumerate(pending, 1):
        print(f"\n{'─' * 60}")
        print(f"  [{i}/{len(pending)}]")
        ok = await process_one_url(url, ctype, state, dry_run=False)
        if ok:
            success += 1
        else:
            failed += 1

    # Summary
    print(f"\n{sep}")
    print(f"  HARVEST COMPLETE")
    print(f"  Processed: {success}  |  Failed: {failed}")
    print(f"  Total calls in library: {state['call_count']}")
    print(f"  Index: {INDEX_FILE}")
    print(f"{sep}\n")

    if failed > 0:
        print(f"Check error log: {ERROR_LOG}")


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Harvest Jeremy Miner call library from YouTube URLs."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Only process first N URLs (0 = no limit)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be processed without making API calls",
    )
    parser.add_argument(
        "--reprocess",
        type=str,
        default=None,
        help="Force re-analyze a specific slug (re-transcribes and re-analyzes)",
    )
    args = parser.parse_args()
    asyncio.run(run(limit=args.limit, dry_run=args.dry_run, reprocess=args.reprocess))
