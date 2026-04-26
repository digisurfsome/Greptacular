"""
Truth Builder
Reads output/videos/ one transcript at a time (oldest → newest),
asks Claude what's NEW vs. what's already in the truth doc,
and builds a rolling truth document.

SETUP:
  pip install anthropic

CONFIGURE:
  ANTHROPIC_API_KEY below

RUN (after youtube_analyzer.py):
  python tools/truth_builder.py

Output:
  output/truth_document.md  — saved after EVERY video so you can stop/resume
  output/truth_builder_log.txt — which videos were processed
"""

import os
import json
import re
from pathlib import Path
import anthropic

# ─────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────
ANTHROPIC_API_KEY = "PASTE_YOUR_KEY_HERE"
OUTPUT_DIR        = Path("output")
TRUTH_DOC_PATH    = OUTPUT_DIR / "truth_document.md"
LOG_PATH          = OUTPUT_DIR / "truth_builder_log.txt"
MODEL             = "claude-opus-4-5"

# Max transcript characters sent per call (keeps costs down).
# ~6,000 chars ≈ 1,500 tokens — plenty for a 15-minute video.
MAX_TRANSCRIPT_CHARS = 8000

# Sections the truth doc is organized into.
TRUTH_SECTIONS = """
## 1. Services & Pricing
## 2. Free Tools & Assets (with URLs)
## 3. Sales Scripts & Pitches
## 4. Client Acquisition Methods
## 5. Automation & Tech Stack
## 6. Niche Strategy & Target Markets
## 7. Retention & Anti-Churn
## 8. Scaling & Hiring
## 9. Misc Tactics & Nuggets
"""
# ─────────────────────────────────────────

SYSTEM_PROMPT = f"""You are building a master "source of truth" document
about an AI agency business model from YouTube video transcripts.

The truth document is organized into these sections:
{TRUTH_SECTIONS}

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

Return ONLY valid JSON in this exact format:
{{
  "has_new_info": true/false,
  "updates": {{
    "Services & Pricing": "text to ADD (not replace) to this section, or null",
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

If has_new_info is false, all updates values should be null.
Do not include markdown fences around the JSON. Return raw JSON only.
"""


def load_truth_doc() -> str:
    if TRUTH_DOC_PATH.exists():
        return TRUTH_DOC_PATH.read_text(encoding="utf-8")
    return ""


def save_truth_doc(content: str):
    TRUTH_DOC_PATH.write_text(content, encoding="utf-8")


def init_truth_doc() -> str:
    """Create an empty structured truth document."""
    sections = [
        "# AI Agency Source of Truth\n",
        f"Built by truth_builder.py — updated incrementally.\n",
    ]
    for section in TRUTH_SECTIONS.strip().split("\n"):
        section = section.strip()
        if section:
            sections.append(f"\n{section}\n\n*(no content yet)*\n")
    doc = "\n".join(sections)
    save_truth_doc(doc)
    return doc


def apply_updates(truth_doc: str, updates: dict) -> str:
    """Add new content to each section in the truth doc."""
    for section_name, new_content in updates.items():
        if not new_content:
            continue
        # Find the section header
        header = f"## {section_name.split('. ', 1)[-1]}" if ". " in section_name else f"## {section_name}"
        # Try exact match first, then partial
        pattern = re.compile(
            rf"(## [^\n]*{re.escape(section_name.split('. ', 1)[-1])}[^\n]*\n)",
            re.IGNORECASE
        )
        match = pattern.search(truth_doc)
        if match:
            insert_pos = match.end()
            # Remove "*(no content yet)*" placeholder if present
            truth_doc = truth_doc.replace("*(no content yet)*", "", 1)
            truth_doc = (
                truth_doc[:insert_pos]
                + "\n" + new_content.strip() + "\n"
                + truth_doc[insert_pos:]
            )
        else:
            # Section not found — append it
            truth_doc += f"\n\n## {section_name}\n\n{new_content.strip()}\n"
    return truth_doc


def load_processed_log() -> set:
    if LOG_PATH.exists():
        return set(LOG_PATH.read_text(encoding="utf-8").splitlines())
    return set()


def log_processed(video_folder: str):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(video_folder + "\n")


def get_video_folders() -> list[Path]:
    """Return video folders sorted oldest → newest."""
    videos_dir = OUTPUT_DIR / "videos"
    if not videos_dir.exists():
        return []
    folders = [f for f in videos_dir.iterdir() if f.is_dir()]
    # Folder names start with YYYY-MM-DD so lexicographic sort = chronological
    return sorted(folders)


def process_video(
    client: anthropic.Anthropic,
    folder: Path,
    truth_doc: str,
) -> tuple[str, str]:
    """
    Process one video. Returns (updated_truth_doc, video_summary).
    """
    transcript_path = folder / "transcript.txt"
    info_path = folder / "info.md"

    if not transcript_path.exists():
        return truth_doc, "No transcript file found."

    transcript = transcript_path.read_text(encoding="utf-8")
    if "[TRANSCRIPT UNAVAILABLE" in transcript:
        return truth_doc, "Transcript unavailable."
    if not transcript.strip():
        return truth_doc, "Empty transcript."

    # Truncate if too long
    if len(transcript) > MAX_TRANSCRIPT_CHARS:
        transcript = transcript[:MAX_TRANSCRIPT_CHARS] + "\n[...truncated]"

    # Read video title from info.md if available
    video_title = folder.name
    if info_path.exists():
        info = info_path.read_text(encoding="utf-8")
        title_match = re.search(r"^# (.+)$", info, re.MULTILINE)
        if title_match:
            video_title = title_match.group(1)

    # Build the user message — no cache_control, just plain content
    user_message = (
        f"VIDEO TITLE: {video_title}\n\n"
        f"=== CURRENT TRUTH DOCUMENT ===\n{truth_doc}\n\n"
        f"=== NEW TRANSCRIPT ===\n{transcript}\n\n"
        f"What is NEW in this transcript that should be added to the truth document? "
        f"Return only JSON as specified."
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text.strip()

    # Strip markdown code fences if model wrapped it anyway
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        print(f"  WARNING: Could not parse JSON response. Raw:\n{raw[:300]}")
        return truth_doc, "Parse error — skipped."

    if result.get("has_new_info") and result.get("updates"):
        truth_doc = apply_updates(truth_doc, result["updates"])

    return truth_doc, result.get("video_summary", "")


def main():
    if ANTHROPIC_API_KEY == "PASTE_YOUR_KEY_HERE":
        print("ERROR: Set your ANTHROPIC_API_KEY at the top of this script.")
        return

    OUTPUT_DIR.mkdir(exist_ok=True)

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Load or init truth doc
    truth_doc = load_truth_doc()
    if not truth_doc:
        print("Starting fresh truth document.")
        truth_doc = init_truth_doc()
    else:
        print(f"Resuming — truth doc has {len(truth_doc)} chars.")

    folders = get_video_folders()
    if not folders:
        print(f"No video folders found in {OUTPUT_DIR}/videos/")
        print("Run youtube_analyzer.py first.")
        return

    processed = load_processed_log()
    remaining = [f for f in folders if f.name not in processed]

    print(f"{len(folders)} total videos | {len(processed)} already processed | {len(remaining)} to go\n")

    for i, folder in enumerate(remaining, 1):
        print(f"[{i}/{len(remaining)}] {folder.name}")
        try:
            truth_doc, summary = process_video(client, folder, truth_doc)
            save_truth_doc(truth_doc)
            log_processed(folder.name)
            print(f"  Summary: {summary}")
        except Exception as e:
            print(f"  ERROR: {e}")
            continue

    print(f"\nDone. Truth document saved to {TRUTH_DOC_PATH}")
    print(f"Sections filled:\n{truth_doc[:500]}...")


if __name__ == "__main__":
    main()
