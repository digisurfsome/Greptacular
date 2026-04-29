#!/usr/bin/env python3
"""
mine_b2b_bonus.py — Jeremy Miner B2B + Bonus Content Miner

Walks 2 transcript files (06-B2B + 02-Bonus Content), splits by section,
chunks into 4 000-token windows with 500-token overlap, calls Claude Sonnet
via subscription (claude -p) to extract B2B-variant phrases + delivery/mindset
content from bonus material.

Two output directories:
    docs/info/jeremy-miner-corpus/b2b-corpus/
    ├── b2b-reframes.md
    ├── multi-stakeholder.md
    ├── gatekeeper-bypass.md
    ├── exec-language.md
    ├── procurement-handlers.md
    └── _b2b-index.md

    docs/info/jeremy-miner-corpus/delivery-corpus/
    ├── delivery-principles.md
    ├── mindset-phrases.md
    ├── pacing-rules.md
    ├── voice-modulation.md
    └── _delivery-index.md

Fully resumable — kill at any time, restart and it skips done chunks.
Progress: b2b-corpus/_b2b_bonus_mine_progress.json

Usage:
    cd C:\\Users\\lober\\.autoforge\\workspace\\repos\\digisurfsome__Greptacular
    python scripts/jeremy/mine_b2b_bonus.py
    python scripts/jeremy/mine_b2b_bonus.py --limit 5      # smoke test
    python scripts/jeremy/mine_b2b_bonus.py --dry-run      # no API calls

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


# ── Load .env ────────────────────────────────────────────────────────────────
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
    REPO_ROOT / "docs/info/jeremy-miner-corpus/videos/06-B2B/all-transcripts.md",
    REPO_ROOT / "docs/info/jeremy-miner-corpus/videos/02-Bonus Content/all-transcripts.md",
]

B2B_DIR      = REPO_ROOT / "docs/info/jeremy-miner-corpus/b2b-corpus"
DELIVERY_DIR = REPO_ROOT / "docs/info/jeremy-miner-corpus/delivery-corpus"

# Single progress file in b2b dir (covers both outputs)
PROGRESS_FILE = B2B_DIR / "_b2b_bonus_mine_progress.json"
ERROR_LOG     = B2B_DIR / "_b2b_bonus_mine_errors.log"

MODEL           = "claude-sonnet-4-5-20250929"   # Sonnet 4.6 — MUST be Sonnet, Haiku paraphrases
CHUNK_TOKENS    = 4000
OVERLAP_TOKENS  = 500
MAX_CONCURRENCY = 5
CALL_TIMEOUT    = 120
RETRY_DELAYS    = [2, 5, 10]

# ── Extraction types + routing ────────────────────────────────────────────────
B2B_TYPES = [
    "b2b_reframe",
    "multi_stakeholder_phrase",
    "gatekeeper_bypass",
    "exec_language",
    "procurement_handler",
]

BONUS_TYPES = [
    "delivery_principle",
    "mindset_phrase",
    "pacing_rule",
    "voice_modulation",
]

ALL_TYPES = B2B_TYPES + BONUS_TYPES

# Maps extraction type → output filename (within its directory)
B2B_TYPE_FILES = {
    "b2b_reframe":             "b2b-reframes.md",
    "multi_stakeholder_phrase":"multi-stakeholder.md",
    "gatekeeper_bypass":       "gatekeeper-bypass.md",
    "exec_language":           "exec-language.md",
    "procurement_handler":     "procurement-handlers.md",
}

BONUS_TYPE_FILES = {
    "delivery_principle": "delivery-principles.md",
    "mindset_phrase":     "mindset-phrases.md",
    "pacing_rule":        "pacing-rules.md",
    "voice_modulation":   "voice-modulation.md",
}

# Canonical folder identifiers (match parent.name of target files)
B2B_FOLDER_ID   = "06-B2B"
BONUS_FOLDER_ID = "02-Bonus Content"

NEPQ_STAGE_NAMES = {
    0: "General", 1: "Connect", 2: "Situation",
    3: "Problem Awareness", 4: "Solution Awareness",
    5: "Consequence", 6: "Transition / Presentation", 7: "Commitment",
}

CLAUDE_CLI: str = ""


# ══════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT
# ══════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """\
Extract verbatim content from Jeremy Miner B2B variant and Bonus material. \
Two extraction modes depending on source_folder provided in the prompt.

B2B EXTRACTIONS (source_folder = 06-B2B):
- b2b_reframe — B2B-specific rephrase of NEPQ question for exec/boardroom audience
- multi_stakeholder_phrase — verbatim phrase addressing multiple decision-makers
- gatekeeper_bypass — verbatim opener/script for getting past assistant
- exec_language — verbatim phrase using exec-grade vocabulary \
(ROI, capex, board, risk, initiative, stakeholder, etc.)
- procurement_handler — verbatim handler for procurement-driven objections

BONUS EXTRACTIONS (source_folder = 02-Bonus Content):
- delivery_principle — verbatim delivery/tonality teaching
- mindset_phrase — verbatim mindset/state instruction for seller
- pacing_rule — verbatim rule about pacing/silence/pause use
- voice_modulation — verbatim instruction on voice tone shift

NEPQ 7 stages: 1-Connect, 2-Situation, 3-Problem-Aware, 4-Solution-Aware, \
5-Consequence, 6-Transition/Present, 7-Commit. Use 0 if general.

OUTPUT (strict JSON, nothing outside the JSON object):
{"extractions":[{"text":"verbatim","type":"b2b_reframe",\
"nepq_stage":2,"source_folder":"06-B2B","context_note":"brief","tags":["exec","reframe"]}]}

RULES:
- VERBATIM ONLY — every word in "text" must appear in the chunk exactly as written.
- type must be one of the 9 types listed above (exact spelling).
- source_folder must match the folder provided in the prompt exactly.
- Only extract types appropriate for the current source_folder \
(B2B types from 06-B2B, Bonus types from 02-Bonus Content).
- Return {"extractions":[]} if no relevant content found in this chunk.
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
    """Split transcript into (video_title, content) pairs."""
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
# API CALL
# ══════════════════════════════════════════════════════════════════════════════

async def call_claude(
    user_msg: str,
    source_label: str,
    chunk_idx: int,
) -> list[dict]:
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

            m = re.search(r'\{[\s\S]*\}', raw_out)
            if m:
                raw_out = m.group(0)

            parsed = json.loads(raw_out)
            raw_items = parsed.get("extractions", [])

            extractions: list[dict] = []
            for item in raw_items:
                if not isinstance(item, dict):
                    continue
                text  = item.get("text", "").strip()
                etype = item.get("type", "")
                if not text or etype not in ALL_TYPES:
                    continue
                stage = item.get("nepq_stage", 0)
                if not isinstance(stage, int) or stage < 0 or stage > 7:
                    stage = 0
                extractions.append({
                    "text":          text,
                    "type":          etype,
                    "nepq_stage":    stage,
                    "source_folder": item.get("source_folder", ""),
                    "context_note":  item.get("context_note", ""),
                    "tags":          item.get("tags", []),
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

    B2B_DIR.mkdir(parents=True, exist_ok=True)
    DELIVERY_DIR.mkdir(parents=True, exist_ok=True)

    sep = "─" * 66
    print(f"\n{sep}")
    print("  Jeremy Miner B2B + Bonus Content Miner")
    print(f"  Model:   {MODEL}  (Sonnet — verbatim required)")
    print(f"  Auth:    subscription (claude -p)")
    print(f"  B2B out: {B2B_DIR}")
    print(f"  Del out: {DELIVERY_DIR}")
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

    total_new    = len(work_queue)
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
            source_label = f"[{folder_name[:28]}] {video_title[:25]}"

            # Tell Claude exactly which mode to use
            mode_hint = (
                "Extract B2B types only (b2b_reframe, multi_stakeholder_phrase, "
                "gatekeeper_bypass, exec_language, procurement_handler)."
                if folder_name == B2B_FOLDER_ID
                else
                "Extract Bonus/delivery types only (delivery_principle, mindset_phrase, "
                "pacing_rule, voice_modulation)."
            )

            user_msg = (
                f"Source folder: {folder_name}\n"
                f"Video / section: {video_title}\n"
                f"Extraction mode: {mode_hint}\n"
                f"Chunk {chunk_idx + 1} of {total_chunks}:\n\n"
                f"{ck}\n\n"
                "Extract relevant content. Set source_folder to the exact folder name above. JSON only."
            )

            async with semaphore:
                extractions = await call_claude(user_msg, source_label, chunk_idx)

            # Enforce folder → type routing (belt-and-suspenders)
            valid_types = B2B_TYPES if folder_name == B2B_FOLDER_ID else BONUS_TYPES
            extractions = [ex for ex in extractions if ex.get("type") in valid_types]

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
            mode = "B2B" if folder_name == B2B_FOLDER_ID else "BONUS"
            print(
                f"  [{mode}] {video_title[:35]:<35}  chunk {chunk_idx+1:>2}/{total_chunks}{tag}",
                flush=True,
            )
            for ex in extractions:
                preview = ex.get("text", "")[:85].replace("\n", " ")
                print(f"     ┌─ [{ex['type']}]", flush=True)
                print(f"     └─ \"{preview}…\"", flush=True)

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

    # ── Collect ────────────────────────────────────────────────────────────────
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
    print(f"Output written → {B2B_DIR}  +  {DELIVERY_DIR}\n")


# ══════════════════════════════════════════════════════════════════════════════
# OUTPUT WRITER
# ══════════════════════════════════════════════════════════════════════════════

def _entry_jsonl(ex: dict) -> str:
    return json.dumps({
        "text":          ex.get("text", ""),
        "type":          ex.get("type", ""),
        "nepq_stage":    ex.get("nepq_stage", 0),
        "source_folder": ex.get("source_folder", ""),
        "context_note":  ex.get("context_note", ""),
        "tags":          ex.get("tags", []),
        "source_video":  ex.get("source_video", ""),
    }, ensure_ascii=False)


def _write_corpus(
    entries: list[dict],
    type_file_map: dict[str, str],
    out_dir: Path,
    index_filename: str,
    corpus_title: str,
    state: dict,
    ts: str,
    min_target: int,
) -> dict[str, int]:
    """Write one corpus directory. Returns type → count dict."""
    type_counts: dict[str, int] = {}

    for etype, filename in type_file_map.items():
        type_entries = [ex for ex in entries if ex.get("type") == etype]
        type_counts[etype] = len(type_entries)
        out_path = out_dir / filename
        label = etype.replace("_", " ").title()

        lines = [
            f"# {label}",
            "",
            f"Generated: {ts}",
            f"Total entries: {len(type_entries)}",
            "",
        ]
        if type_entries:
            # Group by stage within each file
            by_stage: dict[int, list[dict]] = {}
            for ex in type_entries:
                s = ex.get("nepq_stage", 0)
                by_stage.setdefault(s, []).append(ex)
            for s in sorted(by_stage.keys()):
                stage_name = NEPQ_STAGE_NAMES.get(s, "General")
                lines.append(f"## Stage {s} — {stage_name}")
                lines.append("")
                for ex in by_stage[s]:
                    lines.append(_entry_jsonl(ex))
                lines.append("")
        else:
            lines.append("*(no entries yet)*")
            lines.append("")

        out_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"  Written: {out_dir.name}/{filename}  ({len(type_entries)} entries)", flush=True)

    # Index
    total = sum(type_counts.values())
    warnings: list[str] = []
    if total < min_target:
        warnings.append(f"  ⚠  total {corpus_title} entries: {total} — target ≥{min_target}")

    folder_counts: dict[str, int] = {}
    for ex in entries:
        f = ex.get("source_video", "unknown")
        folder_counts[f] = folder_counts.get(f, 0) + 1

    idx_lines = [
        f"# {corpus_title} — Index",
        "",
        f"Generated: {ts}",
        f"Total unique extractions: {total}",
        f"Total API calls (shared): {state.get('call_count', 0)}",
        "",
        "## By Type",
        "",
    ]
    for etype in type_file_map:
        idx_lines.append(f"| {etype} | {type_counts.get(etype, 0)} | `{type_file_map[etype]}` |")
    idx_lines.append("")

    if warnings:
        idx_lines += ["## Quality Warnings", ""]
        for w in warnings:
            idx_lines.append(w)
        idx_lines.append("")

    (out_dir / index_filename).write_text("\n".join(idx_lines), encoding="utf-8")
    print(f"  Written: {out_dir.name}/{index_filename}  ({total} total entries)", flush=True)

    if warnings:
        for w in warnings:
            print(w)

    return type_counts


def write_output(extractions: list[dict], state: dict) -> None:
    # Deduplicate by text
    seen: set[str] = set()
    deduped: list[dict] = []
    for ex in extractions:
        t = ex.get("text", "").strip()
        if t and t not in seen:
            seen.add(t)
            deduped.append(ex)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    b2b_entries    = [ex for ex in deduped if ex.get("type") in B2B_TYPES]
    bonus_entries  = [ex for ex in deduped if ex.get("type") in BONUS_TYPES]

    print(f"\nB2B entries: {len(b2b_entries)}  |  Delivery/bonus entries: {len(bonus_entries)}\n")

    _write_corpus(
        b2b_entries, B2B_TYPE_FILES, B2B_DIR,
        "_b2b-index.md", "B2B Corpus", state, ts, min_target=30,
    )
    _write_corpus(
        bonus_entries, BONUS_TYPE_FILES, DELIVERY_DIR,
        "_delivery-index.md", "Delivery Corpus", state, ts, min_target=20,
    )


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Mine Jeremy Miner B2B + Bonus content for variant phrases and delivery notes."
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
