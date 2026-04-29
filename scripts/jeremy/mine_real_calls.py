#!/usr/bin/env python3
"""
mine_real_calls.py — Jeremy Miner Real Call Vault Miner

Walks 2 real-call transcript files (7 Figure Call Vault + NEPQ Training Calls),
splits by section/video, chunks into 4 000-token windows with 500-token overlap,
calls Claude Sonnet via subscription (claude -p) to extract verbatim DEPLOYED
sales patterns — live call flow, real objection handlers, gate moments,
prospect advancement signals.

Different from mine_teaching.py (Agent 2) — this captures DEPLOYED phrases,
not how Jeremy teaches the framework.

Output:
    docs/info/jeremy-miner-corpus/real-calls-corpus/
    ├── deployed-openers.md
    ├── deployed-questions-stage-1.md  (through stage-7)
    ├── deployed-handlers.md
    ├── deployed-closes.md
    ├── deployed-transitions.md
    ├── gate-moments.md                ← high-value: real advancement triggers
    ├── tone-demonstrations.md
    ├── live-reframes.md
    └── _real-calls-index.md

Fully resumable — kill at any time, restart and it skips done chunks.
Progress: real-calls-corpus/_real_calls_mine_progress.json

Usage:
    cd C:\\Users\\lober\\.autoforge\\workspace\\repos\\digisurfsome__Greptacular
    python scripts/jeremy/mine_real_calls.py
    python scripts/jeremy/mine_real_calls.py --limit 5      # smoke test
    python scripts/jeremy/mine_real_calls.py --dry-run      # no API calls

Requirements:
    pip install tiktoken
    claude login  (subscription — no API key needed)
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

# ── Pop CLAUDECODE at import time so every subprocess inherits clean env ───────
os.environ.pop("CLAUDECODE", None)

# ── Dependency check ──────────────────────────────────────────────────────────
try:
    import tiktoken
except ImportError:
    print("ERROR: tiktoken not installed.  Run: pip install tiktoken")
    sys.exit(1)


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

TARGET_FILES = [
    REPO_ROOT / "docs/info/jeremy-miner-corpus/videos/04-The 7 Figure Call Vault/all-transcripts.md",
    REPO_ROOT / "docs/info/jeremy-miner-corpus/videos/NEPQ Training Calls/all-transcripts.md",
]

OUTPUT_DIR    = REPO_ROOT / "docs/info/jeremy-miner-corpus/real-calls-corpus"
PROGRESS_FILE = OUTPUT_DIR / "_real_calls_mine_progress.json"
ERROR_LOG     = OUTPUT_DIR / "_real_calls_mine_errors.log"

MODEL           = "claude-sonnet-4-5-20250929"   # Sonnet 4.6 — MUST be Sonnet, Haiku paraphrases
CHUNK_TOKENS    = 4000
OVERLAP_TOKENS  = 500
MAX_CONCURRENCY = 5
CALL_TIMEOUT    = 120
RETRY_DELAYS    = [2, 5, 10]

# ── Extraction types ──────────────────────────────────────────────────────────
ALL_TYPES = [
    "deployed_opener",
    "deployed_question",
    "deployed_handler",
    "deployed_close",
    "deployed_transition",
    "prospect_advancement_signal",
    "gate_moment",
    "tone_demonstration",
    "live_reframe",
]

# Types that go into their own dedicated file (not per-stage)
TYPE_FILES = {
    "deployed_opener":              "deployed-openers.md",
    "deployed_handler":             "deployed-handlers.md",
    "deployed_close":               "deployed-closes.md",
    "deployed_transition":          "deployed-transitions.md",
    "gate_moment":                  "gate-moments.md",
    "tone_demonstration":           "tone-demonstrations.md",
    "live_reframe":                 "live-reframes.md",
    "prospect_advancement_signal":  "prospect-advancement-signals.md",
}

# deployed_question also gets per-stage files
STAGE_QUESTION_FILES = {
    s: f"deployed-questions-stage-{s}.md" for s in range(1, 8)
}

STAGE_NAMES = {
    0: "General",
    1: "Connect",
    2: "Situation",
    3: "Problem Awareness",
    4: "Solution Awareness",
    5: "Consequence",
    6: "Transition / Presentation",
    7: "Commitment",
}

VALID_OUTCOMES = {"advanced", "stayed", "backed-up", "closed", "lost", "unknown"}

# Resolved at runtime
CLAUDE_CLI: str = ""


# ══════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT  (verbatim from spec)
# ══════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """\
Extract verbatim DEPLOYED sales phrases from real call recordings. \
These are LIVE calls, not teaching. Capture what the salesperson says in flow \
and key prospect responses that triggered advancement.

EXTRACT:
- deployed_opener — verbatim opening lines used in real call
- deployed_question — verbatim NEPQ question as actually deployed \
(note: may differ from taught version)
- deployed_handler — full verbatim objection handler in real-time use
- deployed_close — verbatim Stage 7 commitment ask in real call
- deployed_transition — verbatim bridge between stages in flow
- prospect_advancement_signal — verbatim prospect response that triggered \
seller to advance (e.g. "yeah I guess we do need..." → seller moves to Stage 4)
- gate_moment — the exchange where stage transition occurred \
(verbatim seller line + verbatim prospect response)
- tone_demonstration — verbatim line where transcript shows pacing/delivery cue \
("[pause]", deliberate slowdown, soft tonality)
- live_reframe — real-time polarity flip on prospect's resistance

NEPQ 7 stages: 1-Connect, 2-Situation, 3-Problem-Aware, 4-Solution-Aware, \
5-Consequence, 6-Transition/Present, 7-Commit. Use 0 if stage unclear.

OUTPUT (strict JSON, nothing outside the JSON object):
{"extractions":[{"text":"verbatim seller line","type":"deployed_question",\
"nepq_stage":3,"prospect_response":"verbatim prospect line if relevant",\
"outcome":"advanced|stayed|backed-up|closed|lost","context_note":"brief",\
"tags":["tag1","tag2"]}]}

RULES:
- VERBATIM ONLY — every word in "text" and "prospect_response" must appear \
in the chunk exactly. Do not paraphrase or reconstruct.
- For gate_moment: "text" = seller line, "prospect_response" mandatory, \
"outcome" mandatory.
- nepq_stage must be integer 0-7.
- type must be one of the 9 types listed above (exact spelling).
- outcome: use "unknown" if not determinable.
- prospect_response: use "" if not applicable for this type.
- Return {"extractions":[]} if no deployed patterns found in chunk.
- No markdown fences, no explanation — JSON object only.\
"""


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def resolve_claude_cli() -> str:
    cli = shutil.which("claude")
    if not cli:
        print("FATAL: 'claude' CLI not found on PATH.")
        print("       Install Claude Code: https://docs.anthropic.com/en/docs/claude-code")
        sys.exit(2)
    return cli


def split_sections(text: str, folder_name: str) -> list[tuple[str, str]]:
    """Split an all-transcripts.md into (video_title, content) pairs."""
    sections: list[tuple[str, str]] = []
    current_title = folder_name
    current_lines: list[str] = []

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            body = "\n".join(current_lines).strip()
            if body:
                sections.append((current_title, body))
            current_title = stripped[3:].strip()
            current_lines = []
        elif stripped == "---":
            body = "\n".join(current_lines).strip()
            if body:
                sections.append((current_title, body))
            current_lines = []
        elif stripped.startswith("# ") and not sections and not current_lines:
            current_title = stripped[2:].strip()
        else:
            current_lines.append(line)

    body = "\n".join(current_lines).strip()
    if body:
        sections.append((current_title, body))

    return sections


def chunk_text(text: str, enc) -> list[str]:
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
            data.setdefault("extractions_total", 0)
            return data
        except Exception as e:
            print(f"Warning: progress file unreadable ({e}) — starting fresh.")
    return {"processed": {}, "call_count": 0, "extractions_total": 0}


def save_state(path: Path, state: dict) -> None:
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def log_error(msg: str) -> None:
    ts = datetime.now().isoformat(timespec="seconds")
    entry = f"[{ts}]  {msg}\n"
    print(f"  ⚠  {entry.strip()}", flush=True)
    with open(ERROR_LOG, "a", encoding="utf-8") as fh:
        fh.write(entry)


# ══════════════════════════════════════════════════════════════════════════════
# PREFLIGHT
# ══════════════════════════════════════════════════════════════════════════════

async def preflight_auth_check() -> None:
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    env.pop("ANTHROPIC_API_KEY", None)

    print("Preflight: verifying claude subscription auth …", flush=True)
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

        if proc.returncode != 0:
            print(f"\nFATAL: preflight failed — exit {proc.returncode}")
            print(f"  stderr: {err[:300] if err else '(empty)'}")
            print(f"  stdout: {out[:300] if out else '(empty)'}")
            print("\nFix: run `claude login` then retry.")
            sys.exit(3)

        print(f"Preflight OK — claude says: {out[:60]!r}\n", flush=True)

    except asyncio.TimeoutError:
        print("FATAL: preflight timed out. Auth prompt hanging — run `claude login`.")
        sys.exit(3)
    except FileNotFoundError as e:
        print(f"FATAL: cannot launch claude CLI: {e}")
        sys.exit(3)


# ══════════════════════════════════════════════════════════════════════════════
# API CALL  (Sonnet via subscription — claude -p subprocess)
# ══════════════════════════════════════════════════════════════════════════════

async def call_claude(
    user_msg: str,
    source_label: str,
    chunk_idx: int,
) -> list[dict]:
    """Call Claude Sonnet via subscription. Returns list of extraction dicts."""
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    env.pop("ANTHROPIC_API_KEY", None)

    combined_prompt = (
        "SYSTEM INSTRUCTIONS:\n"
        + SYSTEM_PROMPT
        + "\n\n---\n\nTRANSCRIPT CHUNK TO ANALYZE:\n"
        + user_msg
    )

    for attempt, delay in enumerate([0] + RETRY_DELAYS):
        if delay:
            await asyncio.sleep(delay)

        try:
            proc = await asyncio.create_subprocess_exec(
                CLAUDE_CLI, "-p", combined_prompt,
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
                log_error(f"{source_label}  chunk={chunk_idx}  TimeoutExpired after {CALL_TIMEOUT}s")
                if attempt < len(RETRY_DELAYS):
                    continue
                return []

            raw_out = out_b.decode("utf-8", errors="replace").strip()
            raw_err = err_b.decode("utf-8", errors="replace").strip()

            if chunk_idx == 0 and attempt == 0:
                preview = raw_out[:200].replace("\n", " ")
                print(f"  [DEBUG chunk0]: {preview!r}", flush=True)

            if proc.returncode != 0:
                if proc.returncode in (15, 3) and attempt < len(RETRY_DELAYS):
                    log_error(f"{source_label}  chunk={chunk_idx}  exit {proc.returncode} — retrying")
                    continue
                log_error(f"{source_label}  chunk={chunk_idx}  exit {proc.returncode}: {raw_err[:200]}")
                return []

            if not raw_out:
                return []

            # Strip accidental markdown fences
            m = re.search(r'\{[\s\S]*\}', raw_out)
            if m:
                raw_out = m.group(0)

            parsed = json.loads(raw_out)
            raw_items = parsed.get("extractions", [])

            extractions: list[dict] = []
            for item in raw_items:
                if not isinstance(item, dict):
                    continue
                text = item.get("text", "").strip()
                etype = item.get("type", "")
                if not text or etype not in ALL_TYPES:
                    continue
                stage = item.get("nepq_stage", 0)
                if not isinstance(stage, int) or stage < 0 or stage > 7:
                    stage = 0
                outcome = item.get("outcome", "unknown")
                if outcome not in VALID_OUTCOMES:
                    outcome = "unknown"
                extractions.append({
                    "text":              text,
                    "type":              etype,
                    "nepq_stage":        stage,
                    "prospect_response": item.get("prospect_response", ""),
                    "outcome":           outcome,
                    "context_note":      item.get("context_note", ""),
                    "tags":              item.get("tags", []),
                })

            return extractions

        except json.JSONDecodeError as e:
            log_error(f"{source_label}  chunk={chunk_idx}  JSON parse failed: {e}  raw: {raw_out[:150]}")
            return []
        except Exception as e:
            log_error(f"{source_label}  chunk={chunk_idx}  {type(e).__name__}: {e}")
            return []

    return []


# ══════════════════════════════════════════════════════════════════════════════
# PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

async def run(limit: int = 0, dry_run: bool = False) -> None:
    global CLAUDE_CLI

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    sep = "─" * 66
    print(f"\n{sep}")
    print("  Jeremy Miner Real Call Vault Miner")
    print(f"  Model:   {MODEL}  (Sonnet — verbatim required)")
    print(f"  Auth:    subscription (claude -p)")
    print(f"  Output:  {OUTPUT_DIR}")
    print(f"  Targets: {len(TARGET_FILES)} files")
    print(f"  Concurrency: {MAX_CONCURRENCY}  |  Chunk: {CHUNK_TOKENS}tok  |  Overlap: {OVERLAP_TOKENS}tok")
    print(f"{sep}\n")

    CLAUDE_CLI = resolve_claude_cli()
    print(f"Claude CLI: {CLAUDE_CLI}\n", flush=True)

    if not dry_run:
        await preflight_auth_check()

    state = load_state(PROGRESS_FILE)
    print(f"Loaded progress: {len(state['processed'])} chunks done | "
          f"{state['call_count']} calls | {state['extractions_total']} extractions so far\n")

    missing = [f for f in TARGET_FILES if not f.exists()]
    if missing:
        print("ERROR: missing target files:")
        for m in missing:
            print(f"  {m}")
        sys.exit(1)

    try:
        enc = tiktoken.get_encoding("cl100k_base")
    except Exception:
        enc = tiktoken.get_encoding("gpt2")

    # ── Build work queue ───────────────────────────────────────────────────────
    work_queue: list[tuple] = []
    section_count = 0

    for target_path in TARGET_FILES:
        folder_name = target_path.parent.name
        try:
            raw = target_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            log_error(f"Read error {target_path}: {e}")
            continue

        sections = split_sections(raw, folder_name)
        print(f"{folder_name}: {len(sections)} sections", flush=True)

        for video_title, section_text in sections:
            section_count += 1
            if limit > 0 and section_count > limit:
                break

            chunks = chunk_text(section_text, enc) if section_text else []
            if not chunks:
                continue

            total = len(chunks)
            for chunk_idx, ck in enumerate(chunks):
                key = f"{folder_name}::{video_title}::chunk_{chunk_idx}"
                if key not in state["processed"]:
                    work_queue.append((folder_name, video_title, chunk_idx, total, ck, key))

        if limit > 0 and section_count > limit:
            break

    total_new = len(work_queue)
    already_done = len(state["processed"])
    print(f"\nChunks to process: {total_new}  |  Already done: {already_done}\n")

    if dry_run:
        print("=== DRY RUN — first 5 chunks ===")
        for item in work_queue[:5]:
            folder, video, cidx, total, ck, key = item
            print(f"\n  [{folder}]  {video!r}  chunk {cidx+1}/{total}")
            print(f"  Preview: {ck[:200].replace(chr(10), ' ')!r}")
        print("\nDry run done. No API calls made.")
        return

    # ── Dispatch ───────────────────────────────────────────────────────────────
    if total_new == 0:
        print("Nothing new — all chunks done.\n")
    else:
        semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
        lock = asyncio.Lock()

        async def process_one(item: tuple) -> None:
            folder_name, video_title, chunk_idx, total_chunks, ck, key = item
            source_label = f"[{folder_name[:30]}] {video_title[:25]}"

            user_msg = (
                f"Source folder: {folder_name}\n"
                f"Video / call: {video_title}\n"
                f"Chunk {chunk_idx + 1} of {total_chunks}:\n\n"
                f"{ck}\n\n"
                "Extract deployed sales patterns. JSON only."
            )

            async with semaphore:
                extractions = await call_claude(user_msg, source_label, chunk_idx)

            for ex in extractions:
                ex["source_folder"] = folder_name
                ex["source_video"]  = video_title

            async with lock:
                state["processed"][key] = {
                    "extractions": extractions,
                    "ts": datetime.now().isoformat(timespec="seconds"),
                }
                state["call_count"]        += 1
                state["extractions_total"] += len(extractions)
                save_state(PROGRESS_FILE, state)

            tag = f"  → {len(extractions)} extraction(s) ✓" if extractions else ""
            print(
                f"  [{folder_name[:26]:<26}]  {video_title[:28]:<28}  "
                f"chunk {chunk_idx+1:>2}/{total_chunks}{tag}",
                flush=True,
            )
            for ex in extractions:
                stage_label = STAGE_NAMES.get(ex.get("nepq_stage", 0), "?")
                preview = ex.get("text", "")[:90].replace("\n", " ")
                outcome = ex.get("outcome", "")
                pr = ex.get("prospect_response", "")
                print(
                    f"     ┌─ [{ex['type']}]  stage:{ex['nepq_stage']}-{stage_label}"
                    + (f"  outcome:{outcome}" if outcome and outcome != "unknown" else ""),
                    flush=True,
                )
                print(f"     │  \"{preview}…\"", flush=True)
                if pr:
                    pr_preview = pr[:70].replace("\n", " ")
                    print(f"     │  prospect: \"{pr_preview}…\"", flush=True)
                print(f"     └─ {ex.get('context_note', '')}", flush=True)

        tasks    = [asyncio.create_task(process_one(item)) for item in work_queue]
        done_cnt = 0
        start_ts = asyncio.get_event_loop().time()

        for fut in asyncio.as_completed(tasks):
            await fut
            done_cnt += 1
            if done_cnt % 20 == 0 or done_cnt == total_new:
                elapsed   = asyncio.get_event_loop().time() - start_ts
                rate      = done_cnt / elapsed if elapsed > 0 else 0
                remaining = (total_new - done_cnt) / rate if rate > 0 else 0
                print(
                    f"\n  ── {done_cnt}/{total_new} ({done_cnt/total_new*100:.0f}%)"
                    f"  {rate:.1f} chunks/s"
                    f"  ETA: {remaining/60:.1f}min"
                    f"  | extractions so far: {state['extractions_total']} ──\n",
                    flush=True,
                )

    # ── Collect all extractions ────────────────────────────────────────────────
    all_extractions: list[dict] = []
    for key, entry in state["processed"].items():
        parts  = key.split("::")
        folder = parts[0] if len(parts) > 0 else "unknown"
        video  = parts[1] if len(parts) > 1 else "unknown"
        for ex in entry.get("extractions", []):
            ex.setdefault("source_folder", folder)
            ex.setdefault("source_video",  video)
            all_extractions.append(ex)

    print(f"\n{sep}")
    print(f"  COMPLETE")
    print(f"  Total extractions:  {len(all_extractions)}")
    print(f"  Total API calls:    {state['call_count']}")
    print(f"{sep}\n")

    write_output(all_extractions, state)
    print(f"Output written → {OUTPUT_DIR}\n")


# ══════════════════════════════════════════════════════════════════════════════
# OUTPUT WRITER
# ══════════════════════════════════════════════════════════════════════════════

def _entry_jsonl(ex: dict) -> str:
    return json.dumps({
        "text":              ex.get("text", ""),
        "type":              ex.get("type", ""),
        "nepq_stage":        ex.get("nepq_stage", 0),
        "prospect_response": ex.get("prospect_response", ""),
        "outcome":           ex.get("outcome", "unknown"),
        "context_note":      ex.get("context_note", ""),
        "tags":              ex.get("tags", []),
        "source_video":      ex.get("source_video", ""),
        "source_folder":     ex.get("source_folder", ""),
    }, ensure_ascii=False)


def write_output(extractions: list[dict], state: dict) -> None:
    # Deduplicate by text
    seen: set[str] = set()
    deduped: list[dict] = []
    for ex in extractions:
        t = ex.get("text", "").strip()
        if t and t not in seen:
            seen.add(t)
            deduped.append(ex)

    ts    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = len(deduped)

    # ── Per-stage deployed-question files ─────────────────────────────────────
    q_stage_counts: dict[int, int] = {}
    for stage in range(1, 8):
        q_entries = [
            ex for ex in deduped
            if ex.get("type") == "deployed_question" and ex.get("nepq_stage", 0) == stage
        ]
        q_stage_counts[stage] = len(q_entries)
        filename = STAGE_QUESTION_FILES[stage]
        out_path = OUTPUT_DIR / filename
        lines = [
            f"# Deployed Questions — Stage {stage}: {STAGE_NAMES[stage]}",
            "",
            f"Generated: {ts}",
            f"Total entries: {len(q_entries)}",
            "",
        ]
        if q_entries:
            for ex in q_entries:
                lines.append(_entry_jsonl(ex))
        else:
            lines.append("*(no entries yet)*")
        lines.append("")
        out_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"  Written: {filename}  ({len(q_entries)} entries)", flush=True)

    # ── Type-specific files ───────────────────────────────────────────────────
    type_counts: dict[str, int] = {}
    for etype, filename in TYPE_FILES.items():
        type_entries = [ex for ex in deduped if ex.get("type") == etype]
        type_counts[etype] = len(type_entries)
        out_path = OUTPUT_DIR / filename
        type_label = etype.replace("_", " ").title()
        lines = [
            f"# {type_label}",
            "",
            f"Generated: {ts}",
            f"Total entries: {len(type_entries)}",
            "",
        ]
        if type_entries:
            # Group gate_moments by outcome (high-value — special treatment)
            if etype == "gate_moment":
                by_outcome: dict[str, list[dict]] = {}
                for ex in type_entries:
                    o = ex.get("outcome", "unknown")
                    by_outcome.setdefault(o, []).append(ex)
                for outcome in ["advanced", "closed", "stayed", "backed-up", "lost", "unknown"]:
                    if outcome not in by_outcome:
                        continue
                    lines.append(f"## Outcome: {outcome}")
                    lines.append("")
                    for ex in by_outcome[outcome]:
                        lines.append(_entry_jsonl(ex))
                    lines.append("")
            else:
                # Group by stage
                by_stage: dict[int, list[dict]] = {}
                for ex in type_entries:
                    s = ex.get("nepq_stage", 0)
                    by_stage.setdefault(s, []).append(ex)
                for s in sorted(by_stage.keys()):
                    lines.append(f"## Stage {s} — {STAGE_NAMES.get(s, 'General')}")
                    lines.append("")
                    for ex in by_stage[s]:
                        lines.append(_entry_jsonl(ex))
                    lines.append("")
        else:
            lines.append("*(no entries yet)*")
            lines.append("")
        out_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"  Written: {filename}  ({len(type_entries)} entries)", flush=True)

    # ── Quality warnings ──────────────────────────────────────────────────────
    warnings: list[str] = []
    gate_count  = type_counts.get("gate_moment", 0)
    close_count = type_counts.get("deployed_close", 0)
    if gate_count < 20:
        warnings.append(f"  ⚠  gate_moments: {gate_count} — target ≥20")
    if close_count < 10:
        warnings.append(f"  ⚠  deployed_closes: {close_count} — target ≥10")

    # ── Index ─────────────────────────────────────────────────────────────────
    folder_counts: dict[str, int] = {}
    for ex in deduped:
        f = ex.get("source_folder", "unknown")
        folder_counts[f] = folder_counts.get(f, 0) + 1

    idx_lines = [
        "# Real Calls Corpus — Index",
        "",
        f"Generated: {ts}",
        f"Total unique extractions: {total}",
        f"Total API calls: {state.get('call_count', 0)}",
        f"Processed chunks: {len(state.get('processed', {}))}",
        "",
        "## Deployed Questions by Stage",
        "",
    ]
    for s in range(1, 8):
        count = q_stage_counts.get(s, 0)
        idx_lines.append(f"| Stage {s} | {STAGE_NAMES[s]} | {count} |")
    idx_lines.append("")

    idx_lines += ["## By Extraction Type", ""]
    for etype in ALL_TYPES:
        count = type_counts.get(etype, 0) if etype != "deployed_question" else sum(q_stage_counts.values())
        idx_lines.append(f"| {etype} | {count} |")
    idx_lines.append("")

    idx_lines += ["## By Source", ""]
    for folder, count in sorted(folder_counts.items()):
        idx_lines.append(f"| {folder} | {count} |")
    idx_lines.append("")

    if warnings:
        idx_lines += ["## Quality Warnings", ""]
        for w in warnings:
            idx_lines.append(w)
        idx_lines.append("")

    idx_lines += ["## Output Files", ""]
    for s, fn in STAGE_QUESTION_FILES.items():
        idx_lines.append(f"- `{fn}` — {q_stage_counts.get(s, 0)} deployed questions")
    for etype, fn in TYPE_FILES.items():
        idx_lines.append(f"- `{fn}` — {type_counts.get(etype, 0)} entries")
    idx_lines.append("")

    (OUTPUT_DIR / "_real-calls-index.md").write_text(
        "\n".join(idx_lines), encoding="utf-8"
    )
    print(f"  Written: _real-calls-index.md  ({total} total unique extractions)", flush=True)

    if warnings:
        print("\nQuality warnings:")
        for w in warnings:
            print(w)


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Mine Jeremy Miner real call vault for deployed sales patterns."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Only process first N sections (0 = no limit; use 5 for smoke test)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print first 5 chunks without making API calls",
    )
    args = parser.parse_args()
    asyncio.run(run(limit=args.limit, dry_run=args.dry_run))
