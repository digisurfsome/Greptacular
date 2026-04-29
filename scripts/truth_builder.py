#!/usr/bin/env python3
"""
truth_builder.py — Standalone Truth Builder (NO server dependency)

Processes video transcript folders through Claude Sonnet via subscription
(claude -p subprocess — Pattern A). Builds a cumulative "source of truth"
document section by section. Fully resumable.

NO AutoForge restart needed. No API key. No server imports.
Auth via your existing `claude login` session.

Supports two topics:
  ai_agency     — Connor Cahil AI agency videos (default)
  meta_programs — NLP metaprogram vocabulary corpus (E: drive)

Usage:
    cd "C:\\Users\\lober\\GitHub\\Greptacular - AutoForge Build\\Greptacular"
    python scripts/truth_builder.py
    python scripts/truth_builder.py --topic meta_programs
    python scripts/truth_builder.py --limit 5     # smoke test: first 5 videos
    python scripts/truth_builder.py --dry-run     # print plan, no API calls

Output (ai_agency):
    output/truth_document.md        — cumulative truth doc, saved after every video
    output/truth_builder_log.txt    — log (DONE: folder lines = resume state)

Output (meta_programs):
    E:\\AutoForge\\Metaprograms\\truth_document.md
    E:\\AutoForge\\Metaprograms\\truth_builder_log.txt
    E:\\AutoForge\\Metaprograms\\toward.md  (per-section files, one per meta program)

Requirements:
    pip install tiktoken   (already installed if you ran the mining scripts)
    claude login           (subscription — no API key)
"""

import argparse
import asyncio
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

# ── Pop CLAUDECODE at import time ─────────────────────────────────────────────
os.environ.pop("CLAUDECODE", None)


# ── Load .env ─────────────────────────────────────────────────────────────────
def _load_dotenv() -> None:
    for candidate in [
        Path(".env"),
        Path(__file__).parent / ".env",
        Path(__file__).parent.parent / ".env",
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

REPO_ROOT = Path(__file__).parent.parent  # scripts/ → repo root

MODEL        = "claude-sonnet-4-5-20250929"   # Sonnet 4.6
CALL_TIMEOUT = 300                            # 5 min — truth builder needs more headroom than mining
RETRY_DELAYS = [5, 15, 30]                    # backoff on exit 15 / exit 3

# No prompt size caps — stdin pipe bypasses Windows 32K arg limit entirely.
# Full transcript + full truth_doc passed on every call.

CLAUDE_CLI: str = ""


# ══════════════════════════════════════════════════════════════════════════════
# TOPIC CONFIGS
# ══════════════════════════════════════════════════════════════════════════════

# ── AI Agency (Connor Cahil videos) ──────────────────────────────────────────

AI_AGENCY_SECTIONS = [
    "Services & Pricing",
    "Free Tools & Assets",
    "Sales Scripts & Pitches",
    "Client Acquisition Methods",
    "Automation & Tech Stack",
    "Niche Strategy & Target Markets",
    "Retention & Anti-Churn",
    "Scaling & Hiring",
    "Misc Tactics & Nuggets",
]

AI_AGENCY_PROMPT = """\
You are building a master "source of truth" document about an AI agency business model \
from YouTube video transcripts.

The document has these sections:
## Services & Pricing
## Free Tools & Assets
## Sales Scripts & Pitches
## Client Acquisition Methods
## Automation & Tech Stack
## Niche Strategy & Target Markets
## Retention & Anti-Churn
## Scaling & Hiring
## Misc Tactics & Nuggets

For each video transcript:
- Extract ONLY information that is NEW vs what's already in the truth doc
- SKIP: promotional filler, book-a-call pitches, repeats
- KEEP: specific numbers, prices, scripts, tool names, URLs, tactics, workflows

CRITICAL — SCRIPT CAPTURE RULE:
For "Sales Scripts & Pitches" specifically (cold calls, opener lines, objection
handling, closing call lines, zoom pitch wording, follow-up texts) — capture
ALL verbatim phrasing word-for-word, even if it sounds similar to existing
entries. Small wording differences matter. Err on the side of including a line
rather than deduping it. Tag each line with its context (cold call opener /
objection response / close ask / zoom intro / etc.).

Mirror this rule for any direct quotes of his sales/pitch language anywhere
else in the doc.

Return raw JSON only (no markdown fences):
{"has_new_info": true/false, "updates": {"Services & Pricing": "text or null", \
"Free Tools & Assets": "text or null", "Sales Scripts & Pitches": "text or null", \
"Client Acquisition Methods": "text or null", "Automation & Tech Stack": "text or null", \
"Niche Strategy & Target Markets": "text or null", "Retention & Anti-Churn": "text or null", \
"Scaling & Hiring": "text or null", "Misc Tactics & Nuggets": "text or null"}, \
"video_summary": "1-2 sentences"}\
"""

AI_AGENCY_TEMPLATE = """\
# AI Agency Business Model — Source of Truth

> Auto-generated by truth_builder.py. Each section is cumulative across all
> processed video transcripts.

## Services & Pricing

## Free Tools & Assets

## Sales Scripts & Pitches

## Client Acquisition Methods

## Automation & Tech Stack

## Niche Strategy & Target Markets

## Retention & Anti-Churn

## Scaling & Hiring

## Misc Tactics & Nuggets
"""

# ── Meta Programs (NLP vocabulary corpus) ─────────────────────────────────────

META_PROGRAMS_SECTIONS = [
    "Toward", "Away", "Internal", "External", "Match", "Mismatch",
    "Convincer-See", "Convincer-Hear", "Convincer-Feel",
    "Convincer-Do", "Convincer-Times", "Other",
]

META_PROGRAMS_SLUGS = {
    "Toward": "toward", "Away": "away", "Internal": "internal",
    "External": "external", "Match": "match", "Mismatch": "mismatch",
    "Convincer-See": "convincer-see", "Convincer-Hear": "convincer-hear",
    "Convincer-Feel": "convincer-feel", "Convincer-Do": "convincer-do",
    "Convincer-Times": "convincer-times", "Other": "other",
}

META_PROGRAMS_PROMPT = """\
You are building a vocabulary corpus about NLP META PROGRAMS from YouTube video transcripts. \
The corpus trains an AI sales/conversation bot to (a) detect which meta program a person is \
running, (b) respond with phrasing that matches their type, and (c) reframe statements INTO \
a target frame.

The corpus sections (use these EXACT section names as the JSON keys):
Toward, Away, Internal, External, Match, Mismatch, Convincer-See, Convincer-Hear, \
Convincer-Feel, Convincer-Do, Convincer-Times, Other

For each section output markdown with THREE ### subsections:
### Elicitation Questions — verbatim questions to detect this meta program
### Example Phrases — verbatim phrases showing the type in action or what to SAY to that type
### Reframe Examples — Original: "..." -> Reframe: "..." — Speaker Name

CRITICAL RULES:
1. VERBATIM. Never paraphrase. Word-for-word only.
2. NEVER DEDUP. Two speakers saying similar things differently = capture BOTH.
3. SPEAKER ATTRIBUTION on every line.
4. Tag every example phrase with its [context: sales/coaching/etc].

For each video:
- Extract ONLY info NEW vs current truth doc.
- SKIP: intros, sponsor reads, promo filler, repeats already captured.

Return raw JSON only (no markdown fences):
{"has_new_info": true/false, "speaker": "Speaker name", \
"updates": {"Toward": "markdown or null", "Away": "markdown or null", \
"Internal": "markdown or null", "External": "markdown or null", \
"Match": "markdown or null", "Mismatch": "markdown or null", \
"Convincer-See": "markdown or null", "Convincer-Hear": "markdown or null", \
"Convincer-Feel": "markdown or null", "Convincer-Do": "markdown or null", \
"Convincer-Times": "markdown or null", "Other": "markdown or null"}, \
"video_summary": "1-2 sentences naming which meta programs this video covered"}\
"""

META_PROGRAMS_TEMPLATE = """\
# NLP Meta Programs — Vocabulary Corpus

> Auto-generated. Trains an AI sales/conversation bot. Per-section files
> mirror the headers below. Each section uses three ### subsections:
> Elicitation Questions / Example Phrases / Reframe Examples.
> Every line has speaker attribution.

## Toward

## Away

## Internal

## External

## Match

## Mismatch

## Convincer-See

## Convincer-Hear

## Convincer-Feel

## Convincer-Do

## Convincer-Times

## Other
"""

# ── Topic registry ────────────────────────────────────────────────────────────

TOPICS = {
    "ai_agency": {
        "videos_dir":    REPO_ROOT / "output/videos",
        "output_dir":    REPO_ROOT / "output",
        "truth_doc":     REPO_ROOT / "output/truth_document.md",
        "log_file":      REPO_ROOT / "output/truth_builder_log.txt",
        "system_prompt": AI_AGENCY_PROMPT,
        "template":      AI_AGENCY_TEMPLATE,
        "sections":      AI_AGENCY_SECTIONS,
        "section_slugs": None,
    },
    "meta_programs": {
        "videos_dir":    Path(r"E:\AutoForge\Metaprograms\videos"),
        "output_dir":    Path(r"E:\AutoForge\Metaprograms"),
        "truth_doc":     Path(r"E:\AutoForge\Metaprograms\truth_document.md"),
        "log_file":      Path(r"E:\AutoForge\Metaprograms\truth_builder_log.txt"),
        "system_prompt": META_PROGRAMS_PROMPT,
        "template":      META_PROGRAMS_TEMPLATE,
        "sections":      META_PROGRAMS_SECTIONS,
        "section_slugs": META_PROGRAMS_SLUGS,
    },
}

DEFAULT_TOPIC = "ai_agency"


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


def get_video_folders(videos_dir: Path) -> list[Path]:
    """Get folders that contain transcript.txt, sorted oldest→newest."""
    if not videos_dir.exists():
        return []
    folders = []
    for entry in sorted(videos_dir.iterdir()):
        if entry.is_dir() and (entry / "transcript.txt").exists():
            folders.append(entry)
    return sorted(folders, key=lambda p: p.stat().st_mtime)


def get_processed(log_path: Path) -> set[str]:
    """Return set of folder names already processed (marked DONE: in log)."""
    if not log_path.exists():
        return set()
    processed: set[str] = set()
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if "DONE:" in line:
            parts = line.split("DONE:", 1)
            if len(parts) == 2:
                name = parts[1].strip()
                if name:
                    processed.add(name)
    return processed


def append_log(log_path: Path, msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write(f"[{ts}] {msg}\n")


def read_truth_doc(truth_doc_path: Path, template: str) -> str:
    if truth_doc_path.exists():
        return truth_doc_path.read_text(encoding="utf-8")
    truth_doc_path.parent.mkdir(parents=True, exist_ok=True)
    truth_doc_path.write_text(template, encoding="utf-8")
    return template


def save_truth_doc(truth_doc_path: Path, content: str) -> None:
    truth_doc_path.parent.mkdir(parents=True, exist_ok=True)
    truth_doc_path.write_text(content, encoding="utf-8")


def merge_updates(truth_doc: str, updates: dict, sections: list[str]) -> str:
    """Append new section content into the cumulative truth doc."""
    for section_name, new_text in updates.items():
        if not new_text or str(new_text).strip().lower() in ("null", "none", ""):
            continue
        header = f"## {section_name}"
        if header not in truth_doc:
            truth_doc += f"\n{header}\n\n{new_text.strip()}\n"
        else:
            idx = truth_doc.index(header)
            header_end = truth_doc.index("\n", idx) if "\n" in truth_doc[idx:] else len(truth_doc)
            next_header_idx = len(truth_doc)
            for other in sections:
                marker = f"\n## {other}"
                pos = truth_doc.find(marker, header_end)
                if 0 <= pos < next_header_idx:
                    next_header_idx = pos
            truth_doc = (
                truth_doc[:next_header_idx]
                + f"\n{new_text.strip()}\n"
                + truth_doc[next_header_idx:]
            )
    return truth_doc


def write_per_section_files(
    truth_doc: str,
    output_dir: Path,
    sections: list[str],
    slug_map: dict,
) -> None:
    """Split master truth doc by ## headers → one .md file per section."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for section in sections:
        slug = slug_map.get(section)
        if not slug:
            continue
        header = f"## {section}"
        if header not in truth_doc:
            (output_dir / f"{slug}.md").write_text(
                f"# {section}\n\n_(no content captured yet)_\n", encoding="utf-8"
            )
            continue
        idx = truth_doc.index(header)
        next_idx = len(truth_doc)
        for other in sections:
            if other == section:
                continue
            pos = truth_doc.find(f"\n## {other}", idx + len(header))
            if 0 <= pos < next_idx:
                next_idx = pos
        section_text = truth_doc[idx:next_idx].rstrip()
        body = section_text.split("\n", 1)[1] if "\n" in section_text else ""
        body = body.strip()
        file_text = (
            f"# {section}\n\n{body}\n" if body
            else f"# {section}\n\n_(no content captured yet)_\n"
        )
        (output_dir / f"{slug}.md").write_text(file_text, encoding="utf-8")
    # Index
    idx_lines = [
        "# Meta Programs Corpus — Index", "",
        "Per-section vocabulary files. Each file: Elicitation Questions / "
        "Example Phrases / Reframe Examples. Every line has speaker attribution.", "",
    ]
    for s in sections:
        slug = slug_map.get(s)
        if slug:
            idx_lines.append(f"- [{s}]({slug}.md)")
    (output_dir / "_index.md").write_text("\n".join(idx_lines) + "\n", encoding="utf-8")


def parse_response(raw: str) -> dict:
    """Parse JSON response, handling markdown fences and preamble."""
    text = raw.strip()
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass
    if "```" in text:
        m = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1).strip())
            except (json.JSONDecodeError, ValueError):
                pass
    first = text.find("{")
    last = text.rfind("}")
    if first >= 0 and last > first:
        try:
            return json.loads(text[first:last + 1])
        except (json.JSONDecodeError, ValueError):
            pass
    return {"has_new_info": False, "updates": {}, "video_summary": "Parse error — skipped"}


def build_combined_prompt(
    system_prompt: str,
    folder_name: str,
    info_text: str,
    transcript: str,
    truth_doc: str,
) -> str:
    """Build combined prompt — no size limits.

    Prompt is piped via stdin (not -p arg), so Windows CreateProcess
    32K char limit does not apply. Full transcript and full truth_doc
    are included on every call regardless of size.
    """
    user_message_parts = [f"VIDEO FOLDER: {folder_name}"]
    if info_text.strip():
        user_message_parts.append(f"VIDEO INFO:\n{info_text.strip()}")
    user_message_parts.append(f"CURRENT TRUTH DOCUMENT:\n{truth_doc}")
    user_message_parts.append(f"NEW TRANSCRIPT:\n{transcript}")
    user_message_parts.append(
        "Extract what is NEW in this transcript vs the truth document. Return JSON only."
    )

    user_message = "\n\n".join(user_message_parts)

    combined = (
        "SYSTEM INSTRUCTIONS:\n"
        + system_prompt
        + "\n\n---\n\n"
        + user_message
    )
    return combined


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
# CLAUDE CALL  (Pattern A — subprocess, no server dependency)
# ══════════════════════════════════════════════════════════════════════════════

async def call_claude(combined_prompt: str, folder_name: str) -> str:
    """Call Claude Sonnet via subscription. Returns raw response text."""
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    env.pop("ANTHROPIC_API_KEY", None)

    for attempt, delay in enumerate([0] + RETRY_DELAYS):
        if delay:
            print(f"  Waiting {delay}s before retry …", flush=True)
            await asyncio.sleep(delay)

        try:
            # Pipe prompt via stdin — bypasses Windows 32K arg limit entirely.
            # -p with no inline arg = print mode, reads prompt from stdin.
            proc = await asyncio.create_subprocess_exec(
                CLAUDE_CLI, "-p",
                "--model", MODEL,
                "--output-format", "text",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            try:
                out_b, err_b = await asyncio.wait_for(
                    proc.communicate(input=combined_prompt.encode("utf-8")),
                    timeout=CALL_TIMEOUT
                )
            except asyncio.TimeoutError:
                proc.kill()
                print(f"  ⚠  Timeout after {CALL_TIMEOUT}s for {folder_name}", flush=True)
                if attempt < len(RETRY_DELAYS):
                    continue
                return ""

            raw_out = out_b.decode("utf-8", errors="replace").strip()
            raw_err = err_b.decode("utf-8", errors="replace").strip()

            if proc.returncode != 0:
                if proc.returncode in (15, 3) and attempt < len(RETRY_DELAYS):
                    print(f"  ⚠  exit {proc.returncode} for {folder_name} — retrying", flush=True)
                    continue
                print(f"  ⚠  claude exit {proc.returncode}: {raw_err[:200]}", flush=True)
                return ""

            return raw_out

        except Exception as e:
            print(f"  ⚠  {type(e).__name__}: {e}", flush=True)
            if attempt < len(RETRY_DELAYS):
                continue
            return ""

    return ""


# ══════════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

async def run(topic_name: str, limit: int, dry_run: bool) -> None:
    global CLAUDE_CLI

    cfg = TOPICS[topic_name]
    videos_dir   = cfg["videos_dir"]
    truth_doc_path = cfg["truth_doc"]
    log_path     = cfg["log_file"]
    system_prompt = cfg["system_prompt"]
    template     = cfg["template"]
    sections     = cfg["sections"]
    section_slugs = cfg.get("section_slugs")
    output_dir   = cfg["output_dir"]

    sep = "─" * 66
    print(f"\n{sep}")
    print(f"  Truth Builder — Standalone (claude -p, no server needed)")
    print(f"  Topic:   {topic_name}")
    print(f"  Model:   {MODEL}  (Sonnet 4.6)")
    print(f"  Videos:  {videos_dir}")
    print(f"  Output:  {truth_doc_path}")
    print(f"  Log:     {log_path}")
    print(f"  Caps:    none — stdin pipe, full transcript + full truth_doc")
    print(f"{sep}\n")

    CLAUDE_CLI = resolve_claude_cli()
    print(f"Claude CLI: {CLAUDE_CLI}\n", flush=True)

    if not dry_run:
        await preflight_auth_check()

    # Discover videos
    all_folders = get_video_folders(videos_dir)
    if not all_folders:
        print(f"ERROR: no video folders with transcript.txt found in {videos_dir}")
        sys.exit(1)

    processed = get_processed(log_path)
    pending   = [f for f in all_folders if f.name not in processed]

    if limit > 0:
        pending = pending[:limit]

    total      = len(all_folders)
    done_count = len(processed)
    to_process = len(pending)

    print(f"Found {total} video folders | {done_count} already done | {to_process} to process\n")

    if dry_run:
        print("=== DRY RUN — would process these videos (first 10 shown) ===")
        for f in pending[:10]:
            print(f"  {f.name}")
        if len(pending) > 10:
            print(f"  ... and {len(pending) - 10} more")
        print(f"\nDry run done. No API calls made.")
        return

    if to_process == 0:
        print("All videos already processed. Nothing to do.")
        return

    # Load truth doc
    truth_doc = read_truth_doc(truth_doc_path, template)
    print(f"Truth doc: {len(truth_doc):,} chars loaded\n")

    append_log(log_path, f"=== Truth Builder started (topic={topic_name}, {to_process} videos) ===")

    start_ts = time.time()

    for i, folder in enumerate(pending, start=1):
        folder_name = folder.name
        print(f"\n[{i}/{to_process}] {folder_name}", flush=True)

        # Read transcript
        transcript_path = folder / "transcript.txt"
        try:
            transcript = transcript_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"  ⚠  Read error: {e} — skipping")
            append_log(log_path, f"SKIPPED: {folder_name} | read error: {e}")
            continue

        # Guard: skip blocked/empty transcripts
        stripped = transcript.strip()
        bad_markers = ("[Transcript unavailable", "[Transcript", "Could not retrieve")
        if len(stripped) < 200 or any(stripped.startswith(m) for m in bad_markers):
            print(f"  ⚠  Transcript missing or blocked — skipping")
            append_log(log_path, f"SKIPPED: {folder_name} | transcript missing/blocked")
            continue

        # Read info.md
        info_text = ""
        info_path = folder / "info.md"
        if info_path.exists():
            try:
                info_text = info_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass

        # Build combined prompt (capped to fit Windows arg limits)
        combined_prompt = build_combined_prompt(
            system_prompt=system_prompt,
            folder_name=folder_name,
            info_text=info_text,
            transcript=transcript,
            truth_doc=truth_doc,
        )
        print(f"  Prompt: {len(combined_prompt):,} chars | transcript: {len(transcript):,} chars | truth_doc: {len(truth_doc):,} chars", flush=True)

        # Call Claude
        call_start = time.time()
        raw_response = await call_claude(combined_prompt, folder_name)
        elapsed = time.time() - call_start

        if not raw_response:
            print(f"  ⚠  Empty response after {elapsed:.1f}s — skipping (not marked done, will retry on re-run)")
            append_log(log_path, f"ERROR: {folder_name} | empty response after {elapsed:.1f}s")
            await asyncio.sleep(3)
            continue

        print(f"  Response: {len(raw_response):,} chars in {elapsed:.1f}s", flush=True)

        # Parse
        result = parse_response(raw_response)
        has_new = result.get("has_new_info", False)
        summary = result.get("video_summary", "")
        updates = result.get("updates", {})

        if has_new and updates:
            truth_doc = merge_updates(truth_doc, updates, sections)
            save_truth_doc(truth_doc_path, truth_doc)
            if section_slugs:
                try:
                    write_per_section_files(truth_doc, output_dir, sections, section_slugs)
                except Exception as e:
                    print(f"  ⚠  Per-section file split failed: {e}", flush=True)
            n_updated = sum(1 for v in updates.values() if v and str(v).strip().lower() not in ("null", "none", ""))
            print(f"  ✓ NEW INFO — {n_updated} section(s) updated | {summary}", flush=True)
            append_log(log_path, f"DONE: {folder_name} | NEW INFO | {summary}")
        else:
            print(f"  ✓ No new info | {summary}", flush=True)
            append_log(log_path, f"DONE: {folder_name} | no new info | {summary}")

        # Brief pause between videos to avoid rate limiting
        await asyncio.sleep(2)

    total_elapsed = time.time() - start_ts
    print(f"\n{sep}")
    print(f"  COMPLETE — {to_process} videos processed in {total_elapsed/60:.1f} min")
    print(f"  Truth doc: {truth_doc_path}")
    print(f"  Size: {len(truth_doc):,} chars")
    print(f"{sep}\n")
    append_log(log_path, f"=== Truth Builder finished — {to_process} videos in {total_elapsed:.0f}s ===")


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Truth Builder — standalone, no AutoForge server needed."
    )
    parser.add_argument(
        "--topic",
        default=DEFAULT_TOPIC,
        choices=list(TOPICS.keys()),
        help=f"Topic to process (default: {DEFAULT_TOPIC})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Only process first N pending videos (0 = no limit; use 5 for smoke test)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be processed without making any API calls",
    )
    args = parser.parse_args()
    asyncio.run(run(topic_name=args.topic, limit=args.limit, dry_run=args.dry_run))
