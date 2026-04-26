"""
Truth Builder — Subscription Mode (claude-sonnet-4-6)
=====================================================
Reads output/videos/ one transcript at a time (oldest → newest),
asks Claude what's NEW vs. what's already in the truth doc,
and builds a rolling truth document.

USES AUTOFORGE SUBSCRIPTION — no API key needed.
Runs via the Claude CLI on your local machine.

SETUP:
  pip install anthropic  (for the SDK client)
  Make sure 'claude' CLI is on your PATH and you're logged in.

RUN (after youtube_analyzer.py):
  python tools/truth_builder.py

Output:
  output/truth_document.md       — saved after EVERY video (resume-safe)
  output/truth_builder_log.txt   — which videos were processed
"""

import asyncio
import json
import logging
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

# ─────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────
MODEL      = "claude-sonnet-4-6"
OUTPUT_DIR = Path("output")

TRUTH_DOC_PATH = OUTPUT_DIR / "truth_document.md"
LOG_PATH       = OUTPUT_DIR / "truth_builder_log.txt"

# Max transcript chars per call (~8K chars ≈ 2K tokens — plenty for 15-min video)
MAX_TRANSCRIPT_CHARS = 8000

# SDK timeout per video call (seconds)
SDK_TIMEOUT = 180

# ─────────────────────────────────────────
#  TRUTH DOC SECTIONS
# ─────────────────────────────────────────
TRUTH_SECTIONS = [
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

SYSTEM_PROMPT = f"""You are building a master "source of truth" document
about an AI agency business model from YouTube video transcripts.

The truth document is organized into these sections:
{chr(10).join(f'  ## {s}' for s in TRUTH_SECTIONS)}

Your job per video:
1. Read the existing truth document (may be empty at start)
2. Read the new transcript
3. Extract ONLY information that is NEW — not already covered
4. Return a JSON object with the updates to make

Rules:
- SKIP: promotional filler, book-a-call pitches, repeats of what's already in the doc
- SKIP: Shorts (< 90 seconds, no real content)
- KEEP: specific numbers, prices, scripts, tool names, URLs, tactics, workflows
- KEEP: any new script lines or cold call language not yet in the doc
- KEEP: any tool URLs found (even if mentioned in passing)
- For scripts: copy verbatim where possible, note what context they're used in

Return ONLY valid JSON in this exact format (no markdown fences, no preamble):
{{
  "has_new_info": true,
  "updates": {{
    "Services & Pricing": "text to ADD to this section, or null",
    "Free Tools & Assets": "text to ADD, or null",
    "Sales Scripts & Pitches": "text to ADD, or null",
    "Client Acquisition Methods": "text to ADD, or null",
    "Automation & Tech Stack": "text to ADD, or null",
    "Niche Strategy & Target Markets": "text to ADD, or null",
    "Retention & Anti-Churn": "text to ADD, or null",
    "Scaling & Hiring": "text to ADD, or null",
    "Misc Tactics & Nuggets": "text to ADD, or null"
  }},
  "video_summary": "1-2 sentence summary of what this video covered"
}}

If has_new_info is false, set all updates values to null.
Start response with {{ and end with }}. Raw JSON only."""


# ─────────────────────────────────────────
#  SUBSCRIPTION SDK CALLER
# ─────────────────────────────────────────

async def call_via_sdk(system_prompt: str, user_message: str) -> str:
    """Call Claude via subscription (no API key). Mirrors yt_processor._call_via_sdk()."""
    # Add the server directory to path so we can import registry
    repo_root = Path(__file__).parent.parent
    server_dir = repo_root / "server"
    if str(server_dir) not in sys.path:
        sys.path.insert(0, str(server_dir))

    try:
        from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
        from registry import get_effective_sdk_env
    except ImportError as e:
        raise RuntimeError(
            f"Could not import SDK modules: {e}\n"
            "Run this script from the Greptacular repo root, or ensure "
            "claude_agent_sdk and registry are importable."
        )

    t0 = time.time()

    # CRITICAL: Remove CLAUDECODE so nested CLI sessions aren't blocked
    os.environ.pop("CLAUDECODE", None)

    system_cli = shutil.which("claude")
    if not system_cli:
        raise RuntimeError(
            "Claude CLI not found on PATH. Install it and run 'claude login'."
        )
    print(f"  [SDK] CLI: {system_cli}")

    sdk_env = get_effective_sdk_env(force_subscription=True)
    sdk_env.pop("CLAUDECODE", None)

    # Verify subscription mode (no API key)
    api_key_val = sdk_env.get("ANTHROPIC_API_KEY", "(NOT SET)")
    if api_key_val and api_key_val not in ("", "(NOT SET)"):
        print(f"  ⚠️  WARNING: API key still present — {api_key_val[:10]}...")
    else:
        print(f"  ✅ Subscription mode confirmed (no API key)")

    scratch = tempfile.mkdtemp(prefix="truth_builder_")
    settings_file = Path(scratch) / ".claude-settings.json"
    settings_file.write_text(json.dumps({
        "permissions": {
            "defaultMode": "acceptEdits",
            "allow": [],
        },
    }))

    client = ClaudeSDKClient(
        options=ClaudeAgentOptions(
            model=MODEL,
            cli_path=system_cli,
            system_prompt=system_prompt,
            env=sdk_env,
            max_turns=2,
            permission_mode="acceptEdits",
            allowed_tools=[],
            cwd=scratch,
            settings=str(settings_file.resolve()),
            setting_sources=["user"],
        )
    )

    print(f"  [SDK] Client ready ({time.time()-t0:.1f}s) | model={MODEL}")

    async def _run() -> str:
        full_text = ""
        rate_limit_count = 0
        last_heartbeat = time.time()

        try:
            await client.__aenter__()
        except Exception as e:
            raise RuntimeError(f"CLI failed to start: {e}") from e

        await client.query(user_message)
        print(f"  [SDK] Query sent — waiting for {MODEL}...")

        try:
            async for msg in client.receive_response():
                msg_type = type(msg).__name__

                # Heartbeat every 15s
                if time.time() - last_heartbeat >= 15:
                    print(f"  [SDK] Still processing... {len(full_text):,} chars received")
                    last_heartbeat = time.time()

                if msg_type in ("RateLimitEvent", "rate_limit_event"):
                    rate_limit_count += 1
                    print(f"  [SDK] Rate limit #{rate_limit_count} — continuing...")
                    continue

                # Extract text from result messages
                if hasattr(msg, "result"):
                    result = msg.result
                    if isinstance(result, str):
                        full_text = result
                    elif hasattr(result, "content"):
                        for block in (result.content or []):
                            if hasattr(block, "text"):
                                full_text += block.text

                # Extract text from content blocks
                if hasattr(msg, "content"):
                    for block in (msg.content or []):
                        if hasattr(block, "text"):
                            full_text += block.text

        except Exception as exc:
            err_str = str(exc).lower()
            if full_text.strip() and "unknown message type" in err_str:
                print(f"  [SDK] Caught rate_limit_event exception — using collected text")
            elif full_text.strip():
                print(f"  [SDK] Non-fatal exception, using collected text: {exc}")
            else:
                try:
                    await client.__aexit__(None, None, None)
                except Exception:
                    pass
                raise

        try:
            await client.__aexit__(None, None, None)
        except Exception:
            pass

        return full_text

    result = await asyncio.wait_for(_run(), timeout=SDK_TIMEOUT)
    elapsed = time.time() - t0
    print(f"  [SDK] Done in {elapsed:.1f}s — {len(result):,} chars returned")

    # Clean temp dir
    try:
        shutil.rmtree(scratch, ignore_errors=True)
    except Exception:
        pass

    return result


# ─────────────────────────────────────────
#  TRUTH DOC MANAGEMENT
# ─────────────────────────────────────────

def init_truth_doc() -> str:
    doc_parts = [
        "# AI Agency Source of Truth\n",
        "Built by truth_builder.py — updated incrementally, oldest video → newest.\n",
    ]
    for section in TRUTH_SECTIONS:
        doc_parts.append(f"\n## {section}\n\n*(no content yet)*\n")
    doc = "\n".join(doc_parts)
    TRUTH_DOC_PATH.write_text(doc, encoding="utf-8")
    return doc


def load_truth_doc() -> str:
    if TRUTH_DOC_PATH.exists():
        return TRUTH_DOC_PATH.read_text(encoding="utf-8")
    return ""


def save_truth_doc(content: str):
    TRUTH_DOC_PATH.write_text(content, encoding="utf-8")


def apply_updates(truth_doc: str, updates: dict) -> str:
    """Append new content under each matching section header."""
    for section_name, new_content in updates.items():
        if not new_content:
            continue
        # Build a regex that finds ## {SectionName} header line
        escaped = re.escape(section_name)
        pattern = re.compile(rf"(##\s+{escaped}\s*\n)", re.IGNORECASE)
        match = pattern.search(truth_doc)
        if match:
            insert_pos = match.end()
            # Remove placeholder if present
            truth_doc = truth_doc.replace("*(no content yet)*\n", "", 1)
            truth_doc = (
                truth_doc[:insert_pos]
                + "\n" + new_content.strip() + "\n"
                + truth_doc[insert_pos:]
            )
        else:
            # Section missing — append it
            truth_doc += f"\n\n## {section_name}\n\n{new_content.strip()}\n"
    return truth_doc


def parse_response(raw: str) -> dict:
    """Extract JSON from the model response, handling fences."""
    raw = raw.strip()
    # Strip markdown fences if model wrapped it
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"\s*```$", "", raw, flags=re.MULTILINE)
    raw = raw.strip()
    # Find first { ... } balanced block
    start = raw.find("{")
    if start == -1:
        raise ValueError("No JSON object found in response")
    depth, in_str, escape = 0, False, False
    for i in range(start, len(raw)):
        ch = raw[i]
        if escape:
            escape = False; continue
        if ch == "\\": escape = True; continue
        if ch == '"': in_str = not in_str; continue
        if in_str: continue
        if ch == "{": depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(raw[start:i+1])
    raise ValueError("Unbalanced JSON in response")


# ─────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────

def get_video_folders() -> list[Path]:
    videos_dir = OUTPUT_DIR / "videos"
    if not videos_dir.exists():
        return []
    return sorted(f for f in videos_dir.iterdir() if f.is_dir())


def load_processed_log() -> set:
    if LOG_PATH.exists():
        return set(LOG_PATH.read_text(encoding="utf-8").splitlines())
    return set()


def log_processed(folder_name: str):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(folder_name + "\n")


async def process_video(folder: Path, truth_doc: str) -> tuple[str, str]:
    """Process one video folder. Returns (updated_truth_doc, summary)."""
    transcript_path = folder / "transcript.txt"
    info_path = folder / "info.md"

    if not transcript_path.exists():
        return truth_doc, "No transcript file."

    transcript = transcript_path.read_text(encoding="utf-8")
    if "[TRANSCRIPT UNAVAILABLE" in transcript or not transcript.strip():
        return truth_doc, "Transcript unavailable or empty."

    # Truncate if needed
    if len(transcript) > MAX_TRANSCRIPT_CHARS:
        transcript = transcript[:MAX_TRANSCRIPT_CHARS] + "\n[...truncated]"

    # Get video title
    video_title = folder.name
    if info_path.exists():
        info = info_path.read_text(encoding="utf-8")
        m = re.search(r"^# (.+)$", info, re.MULTILINE)
        if m:
            video_title = m.group(1)

    user_message = (
        f"VIDEO TITLE: {video_title}\n\n"
        f"=== CURRENT TRUTH DOCUMENT ===\n{truth_doc}\n\n"
        f"=== NEW TRANSCRIPT ===\n{transcript}\n\n"
        "What is NEW in this transcript that should be added to the truth document? "
        "Return only JSON as specified."
    )

    raw = await call_via_sdk(SYSTEM_PROMPT, user_message)

    try:
        result = parse_response(raw)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"  ⚠️  JSON parse error: {e}")
        print(f"  Raw preview: {raw[:300]}")
        return truth_doc, "Parse error — skipped."

    if result.get("has_new_info") and result.get("updates"):
        truth_doc = apply_updates(truth_doc, result["updates"])

    return truth_doc, result.get("video_summary", "")


async def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Load or init truth doc
    truth_doc = load_truth_doc()
    if not truth_doc:
        print("Starting fresh truth document.")
        truth_doc = init_truth_doc()
    else:
        print(f"Resuming — truth doc has {len(truth_doc):,} chars.")

    folders = get_video_folders()
    if not folders:
        print(f"No video folders in {OUTPUT_DIR}/videos/")
        print("Run youtube_analyzer.py first.")
        return

    processed = load_processed_log()
    remaining = [f for f in folders if f.name not in processed]

    print(
        f"\n{len(folders)} total videos | "
        f"{len(processed)} already processed | "
        f"{len(remaining)} to go\n"
        f"Model: {MODEL} | Subscription billing\n"
    )

    for i, folder in enumerate(remaining, 1):
        print(f"\n[{i}/{len(remaining)}] {folder.name}")
        try:
            truth_doc, summary = await process_video(folder, truth_doc)
            save_truth_doc(truth_doc)
            log_processed(folder.name)
            print(f"  ✅ {summary}")
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            continue

    print(f"\n✅ Done. Truth doc → {TRUTH_DOC_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
