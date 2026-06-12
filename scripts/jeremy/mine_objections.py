#!/usr/bin/env python3
"""
mine_objections.py — Jeremy Miner Common Objections Handler Miner

Walks the 01-Common Objections transcript file (53 videos = 53+ named objections),
splits by section/video, chunks into 4 000-token windows with 500-token overlap,
calls Claude Sonnet via subscription (claude -p) to extract verbatim
Clarify → Discuss → Diffuse handler trees, prevention phrases, and root cause notes.

Output: one .md file per distinct objection_name + cross-cutting files.
    docs/info/jeremy-miner-corpus/objection-handlers/
    ├── _objection-index.md
    ├── send-me-a-quote.md
    ├── too-expensive.md
    ├── ... (one per objection)
    ├── prevention-phrases.md
    └── psychology-notes.md

Fully resumable — kill at any time, restart and it skips done chunks.
Progress: objection-handlers/_objection_mine_progress.json

Usage:
    cd C:\\Users\\lober\\.autoforge\\workspace\\repos\\digisurfsome__Greptacular
    python scripts/jeremy/mine_objections.py
    python scripts/jeremy/mine_objections.py --limit 5      # smoke test
    python scripts/jeremy/mine_objections.py --dry-run      # no API calls

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
    REPO_ROOT / "docs/info/jeremy-miner-corpus/videos/01-Common Objections/all-transcripts.md",
]

OUTPUT_DIR    = REPO_ROOT / "docs/info/jeremy-miner-corpus/objection-handlers"
PROGRESS_FILE = OUTPUT_DIR / "_objection_mine_progress.json"
ERROR_LOG     = OUTPUT_DIR / "_objection_mine_errors.log"

MODEL           = "claude-sonnet-4-5-20250929"   # Sonnet 4.6 — MUST be Sonnet, Haiku paraphrases
CHUNK_TOKENS    = 4000
OVERLAP_TOKENS  = 500
MAX_CONCURRENCY = 5
CALL_TIMEOUT    = 120
RETRY_DELAYS    = [2, 5, 10]

# ── Extraction types ──────────────────────────────────────────────────────────
ALL_TYPES = [
    "handler_full",
    "handler_clarify",
    "handler_discuss",
    "handler_diffuse",
    "prevention_phrase",
    "objection_definition",
    "objection_root_cause",
]

VALID_STEPS = {"clarify", "discuss", "diffuse", "all", ""}

# Cross-cutting output files (not per-objection)
CROSS_FILES = {
    "prevention_phrase":    "prevention-phrases.md",
    "objection_definition": "psychology-notes.md",
    "objection_root_cause": "psychology-notes.md",
}

NEPQ_STAGE_NAMES = {
    0: "General",
    1: "Connect",
    2: "Situation",
    3: "Problem Awareness",
    4: "Solution Awareness",
    5: "Consequence",
    6: "Transition / Presentation",
    7: "Commitment",
}

# Resolved at runtime
CLAUDE_CLI: str = ""


# ══════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT
# ══════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """\
Extract verbatim objection handlers from Jeremy Miner Common Objections training. \
Each handler typically follows Clarify → Discuss → Diffuse pattern.

EXTRACT:
- handler_full — full 3-step handler verbatim (preferred — capture entire arc)
- handler_clarify — verbatim Clarify step only (when full not present)
- handler_discuss — verbatim Discuss step only
- handler_diffuse — verbatim Diffuse step only
- prevention_phrase — verbatim phrase used EARLIER in call to prevent this objection
- objection_definition — Jeremy defining the objection / what it really means
- objection_root_cause — Jeremy explaining what's behind this objection psychologically

NEPQ 7 stages: 1-Connect, 2-Situation, 3-Problem-Aware, 4-Solution-Aware, \
5-Consequence, 6-Transition/Present, 7-Commit. \
Objection handlers usually appear at stage 6 or 7. Use 0 if unclear.

OUTPUT (strict JSON, nothing outside the JSON object):
{"extractions":[{"text":"verbatim","type":"handler_full",\
"objection_name":"send-me-a-quote","step":"clarify|discuss|diffuse|all",\
"nepq_stage":6,"context_note":"brief","tags":["tag1"]}]}

RULES:
- VERBATIM ONLY — every word in "text" must appear in the chunk exactly as written.
- objection_name MANDATORY for all entries. Use the video/section title as the \
primary hint (provided in the prompt). Derive from content if not obvious. \
Format: lowercase-hyphenated (e.g. "too-expensive", "let-me-think-about-it", \
"send-me-information").
- type must be one of the 7 types listed above (exact spelling).
- step: use "all" for handler_full, specific step for handler_clarify/discuss/diffuse, \
"" for non-handler types.
- handler_full is the gold standard — capture the full arc when Jeremy delivers all 3 \
steps in sequence.
- Return {"extractions":[]} if no objection handler content found in chunk.
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


def slugify(text: str) -> str:
    """Convert section title to lowercase-hyphenated filename slug."""
    text = text.lower().strip()
    # Remove leading video number prefix like "01-", "02a-"
    text = re.sub(r'^\d+[a-z]?[-_\s]+', '', text)
    # Replace non-alphanumeric with hyphens
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = text.strip('-')
    return text[:60] if text else "unknown-objection"


def split_sections(text: str, folder_name: str) -> list[tuple[str, str, str]]:
    """Split transcript into (video_title, slug_hint, content) triples.

    slug_hint = slugified video title — passed to Claude as objection_name hint.
    """
    sections: list[tuple[str, str, str]] = []
    current_title = folder_name
    current_lines: list[str] = []

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            body = "\n".join(current_lines).strip()
            if body:
                sections.append((current_title, slugify(current_title), body))
            current_title = stripped[3:].strip()
            current_lines = []
        elif stripped == "---":
            body = "\n".join(current_lines).strip()
            if body:
                sections.append((current_title, slugify(current_title), body))
            current_lines = []
        elif stripped.startswith("# ") and not sections and not current_lines:
            current_title = stripped[2:].strip()
        else:
            current_lines.append(line)

    body = "\n".join(current_lines).strip()
    if body:
        sections.append((current_title, slugify(current_title), body))

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
                stage = item.get("nepq_stage", 6)
                if not isinstance(stage, int) or stage < 0 or stage > 7:
                    stage = 6   # objections default to stage 6
                step = item.get("step", "")
                if step not in VALID_STEPS:
                    step = ""
                objection_name = item.get("objection_name", "").strip()
                if not objection_name:
                    objection_name = "unknown-objection"
                # Normalize to slug format
                objection_name = slugify(objection_name) if objection_name != "unknown-objection" else "unknown-objection"
                extractions.append({
                    "text":           text,
                    "type":           etype,
                    "objection_name": objection_name,
                    "step":           step,
                    "nepq_stage":     stage,
                    "context_note":   item.get("context_note", ""),
                    "tags":           item.get("tags", []),
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
    print("  Jeremy Miner Common Objections Handler Miner")
    print(f"  Model:   {MODEL}  (Sonnet — verbatim required)")
    print("  Auth:    subscription (claude -p)")
    print(f"  Output:  {OUTPUT_DIR}")
    print(f"  Targets: {len(TARGET_FILES)} file(s)")
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
    # WorkItem: (folder_name, video_title, slug_hint, chunk_idx, total, chunk_text, key)
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
        print(f"{folder_name}: {len(sections)} sections found", flush=True)

        for video_title, slug_hint, section_text in sections:
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
                    work_queue.append(
                        (folder_name, video_title, slug_hint, chunk_idx, total, ck, key)
                    )

        if limit > 0 and section_count > limit:
            break

    total_new = len(work_queue)
    already_done = len(state["processed"])
    print(f"\nChunks to process: {total_new}  |  Already done: {already_done}\n")

    if dry_run:
        print("=== DRY RUN — first 5 chunks ===")
        for item in work_queue[:5]:
            folder, video, slug, cidx, total, ck, key = item
            print(f"\n  [{folder}]  {video!r}  slug:{slug!r}  chunk {cidx+1}/{total}")
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
            folder_name, video_title, slug_hint, chunk_idx, total_chunks, ck, key = item
            source_label = f"[{folder_name[:28]}] {video_title[:25]}"

            user_msg = (
                f"Source folder: {folder_name}\n"
                f"Video / section title: {video_title}\n"
                f"Suggested objection_name (derived from title): {slug_hint}\n"
                f"Chunk {chunk_idx + 1} of {total_chunks}:\n\n"
                f"{ck}\n\n"
                "Extract objection handlers. Use the suggested objection_name unless "
                "content clearly indicates a different objection. JSON only."
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
                f"  [{folder_name[:24]:<24}]  {video_title[:30]:<30}  "
                f"chunk {chunk_idx+1:>2}/{total_chunks}{tag}",
                flush=True,
            )
            for ex in extractions:
                obj  = ex.get("objection_name", "?")
                step = ex.get("step", "")
                preview = ex.get("text", "")[:80].replace("\n", " ")
                step_tag = f"  step:{step}" if step else ""
                print(
                    f"     ┌─ [{ex['type']}]  obj:{obj}{step_tag}",
                    flush=True,
                )
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
    print("  COMPLETE")
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
        "text":           ex.get("text", ""),
        "type":           ex.get("type", ""),
        "objection_name": ex.get("objection_name", ""),
        "step":           ex.get("step", ""),
        "nepq_stage":     ex.get("nepq_stage", 6),
        "context_note":   ex.get("context_note", ""),
        "tags":           ex.get("tags", []),
        "source_video":   ex.get("source_video", ""),
        "source_folder":  ex.get("source_folder", ""),
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

    # ── Group by objection_name ────────────────────────────────────────────────
    by_objection: dict[str, list[dict]] = {}
    for ex in deduped:
        name = ex.get("objection_name", "unknown-objection")
        by_objection.setdefault(name, []).append(ex)

    # ── Per-objection files ────────────────────────────────────────────────────
    obj_entry_counts: dict[str, int] = {}
    full_handler_counts: dict[str, int] = {}

    for obj_name, obj_entries in sorted(by_objection.items()):
        # Skip cross-cutting types from per-objection files
        handler_entries = [
            ex for ex in obj_entries
            if ex.get("type") not in ("prevention_phrase", "objection_definition", "objection_root_cause")
        ]
        obj_entry_counts[obj_name]      = len(obj_entries)
        full_handler_counts[obj_name]   = sum(1 for ex in obj_entries if ex.get("type") == "handler_full")

        filename = f"{obj_name}.md"
        out_path = OUTPUT_DIR / filename

        # Human-readable title from slug
        display_name = obj_name.replace("-", " ").title()

        lines = [
            f"# Objection: {display_name}",
            "",
            f"Generated: {ts}",
            f"Total entries: {len(obj_entries)}",
            f"Full handlers: {full_handler_counts[obj_name]}",
            "",
        ]

        # Section order: full → clarify → discuss → diffuse → other
        type_order = [
            ("handler_full",   "## Full Handler (Clarify → Discuss → Diffuse)"),
            ("handler_clarify","## Clarify Step"),
            ("handler_discuss","## Discuss Step"),
            ("handler_diffuse","## Diffuse Step"),
        ]
        for etype, heading in type_order:
            entries = [ex for ex in obj_entries if ex.get("type") == etype]
            if entries:
                lines.append(heading)
                lines.append("")
                for ex in entries:
                    lines.append(_entry_jsonl(ex))
                lines.append("")

        # Prevention phrases that mention this objection
        prev = [ex for ex in obj_entries if ex.get("type") == "prevention_phrase"]
        if prev:
            lines.append("## Prevention Phrases")
            lines.append("")
            for ex in prev:
                lines.append(_entry_jsonl(ex))
            lines.append("")

        # Psychology / definition / root cause
        psych = [
            ex for ex in obj_entries
            if ex.get("type") in ("objection_definition", "objection_root_cause")
        ]
        if psych:
            lines.append("## Psychology Notes")
            lines.append("")
            for ex in psych:
                lines.append(_entry_jsonl(ex))
            lines.append("")

        out_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"  Written: {filename}  ({len(obj_entries)} entries, {full_handler_counts[obj_name]} full handlers)", flush=True)

    # ── prevention-phrases.md (cross-cutting) ─────────────────────────────────
    prev_all = [ex for ex in deduped if ex.get("type") == "prevention_phrase"]
    prev_path = OUTPUT_DIR / "prevention-phrases.md"
    prev_lines = [
        "# Prevention Phrases (All Objections)",
        "",
        f"Generated: {ts}",
        f"Total entries: {len(prev_all)}",
        "",
        "Prevention phrases = verbatim lines used EARLIER in the call to prevent",
        "specific objections from arising at Stage 6/7.",
        "",
    ]
    by_obj_prev: dict[str, list[dict]] = {}
    for ex in prev_all:
        by_obj_prev.setdefault(ex.get("objection_name", "unknown"), []).append(ex)
    for obj_name in sorted(by_obj_prev.keys()):
        prev_lines.append(f"## {obj_name.replace('-', ' ').title()}")
        prev_lines.append("")
        for ex in by_obj_prev[obj_name]:
            prev_lines.append(_entry_jsonl(ex))
        prev_lines.append("")
    prev_path.write_text("\n".join(prev_lines), encoding="utf-8")
    print(f"  Written: prevention-phrases.md  ({len(prev_all)} entries)", flush=True)

    # ── psychology-notes.md (cross-cutting) ───────────────────────────────────
    psych_all = [
        ex for ex in deduped
        if ex.get("type") in ("objection_definition", "objection_root_cause")
    ]
    psych_path = OUTPUT_DIR / "psychology-notes.md"
    psych_lines = [
        "# Objection Psychology Notes",
        "",
        f"Generated: {ts}",
        f"Total entries: {len(psych_all)}",
        "",
    ]
    by_obj_psych: dict[str, list[dict]] = {}
    for ex in psych_all:
        by_obj_psych.setdefault(ex.get("objection_name", "unknown"), []).append(ex)
    for obj_name in sorted(by_obj_psych.keys()):
        psych_lines.append(f"## {obj_name.replace('-', ' ').title()}")
        psych_lines.append("")
        for ex in by_obj_psych[obj_name]:
            psych_lines.append(_entry_jsonl(ex))
        psych_lines.append("")
    psych_path.write_text("\n".join(psych_lines), encoding="utf-8")
    print(f"  Written: psychology-notes.md  ({len(psych_all)} entries)", flush=True)

    # ── Quality warnings ──────────────────────────────────────────────────────
    distinct_obj_count = len(by_objection)
    total_full_handlers = sum(full_handler_counts.values())
    warnings: list[str] = []
    if distinct_obj_count < 30:
        warnings.append(f"  ⚠  distinct objections: {distinct_obj_count} — target ≥30")
    if total_full_handlers < 20:
        warnings.append(f"  ⚠  handler_full count: {total_full_handlers} — target ≥20")

    # ── _objection-index.md ────────────────────────────────────────────────────
    type_counts = {t: sum(1 for ex in deduped if ex.get("type") == t) for t in ALL_TYPES}
    folder_counts: dict[str, int] = {}
    for ex in deduped:
        f = ex.get("source_folder", "unknown")
        folder_counts[f] = folder_counts.get(f, 0) + 1

    idx_lines = [
        "# Objection Handlers — Index",
        "",
        f"Generated: {ts}",
        f"Total unique extractions: {total}",
        f"Distinct objections: {distinct_obj_count}",
        f"Full handlers (gold): {total_full_handlers}",
        f"Total API calls: {state.get('call_count', 0)}",
        f"Processed chunks: {len(state.get('processed', {}))}",
        "",
        "## Objection Coverage",
        "",
        "| Objection | Entries | Full Handlers | File |",
        "|---|---|---|---|",
    ]
    for obj_name in sorted(by_objection.keys()):
        count = obj_entry_counts.get(obj_name, 0)
        full  = full_handler_counts.get(obj_name, 0)
        full_tag = " ★" if full >= 1 else ""
        idx_lines.append(f"| {obj_name} | {count} | {full}{full_tag} | `{obj_name}.md` |")
    idx_lines.append("")

    idx_lines += ["## By Extraction Type", ""]
    for etype in ALL_TYPES:
        idx_lines.append(f"| {etype} | {type_counts.get(etype, 0)} |")
    idx_lines.append("")

    if warnings:
        idx_lines += ["## Quality Warnings", ""]
        for w in warnings:
            idx_lines.append(w)
        idx_lines.append("")

    idx_lines += ["## Output Files", ""]
    idx_lines.append("- `prevention-phrases.md` — cross-cutting prevention phrases")
    idx_lines.append("- `psychology-notes.md` — definitions + root causes")
    idx_lines.append(f"- `{distinct_obj_count}` per-objection files (see coverage table above)")
    idx_lines.append("")

    (OUTPUT_DIR / "_objection-index.md").write_text(
        "\n".join(idx_lines), encoding="utf-8"
    )
    print(f"  Written: _objection-index.md  ({distinct_obj_count} objections, {total} total extractions)", flush=True)

    if warnings:
        print("\nQuality warnings:")
        for w in warnings:
            print(w)


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Mine Jeremy Miner Common Objections for handler trees."
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
