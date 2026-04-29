# Mining Script & Truth Builder Recipe

> **Audience:** AI agents building Python scripts that extract structured content from YouTube transcript `.md` files using the Claude CLI subscription (no API key).
>
> **Read time:** 2 minutes. Everything you need to build a working script is here.

---

## Two Script Types

| Type | Purpose | Concurrency | State |
|------|---------|-------------|-------|
| **Mining script** | Extract specific items (questions, objections, frameworks) from transcript chunks | Parallel (5 concurrent) | JSON sidecar per run |
| **Truth builder** | Build a cumulative knowledge document across all transcripts | Sequential (each call uses previous output) | Text log + truth_doc file |

---

## 1. Mining Scripts

**Examples:** `mine_teaching.py`, `mine_real_calls.py`, `mine_objections.py`, `mine_b2b_bonus.py`

### Pipeline

1. Read `.md` transcript files from a source folder
2. Split each file by `## section headers` to preserve per-video provenance
3. Chunk each section into ~4K token chunks (500 token overlap)
4. Send each chunk to Claude with a system prompt requesting JSON extractions
5. Write output to per-type `.md` files (e.g., `gate-criteria.md`, `objection-handlers/`)
6. Track progress in a JSON sidecar so runs are resumable

### Section-Aware Chunking

```python
def split_sections(text: str) -> list[tuple[str, str]]:
    """Split .md by ## headers and --- separators. Returns [(section_title, content)]."""
    sections = []
    current_title = "general"
    current_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            if current_lines:
                sections.append((current_title, "\n".join(current_lines)))
            current_title = stripped[3:].strip()
            current_lines = []
        elif stripped == "---":
            if current_lines:
                sections.append((current_title, "\n".join(current_lines)))
            current_title = "general"
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines:
        sections.append((current_title, "\n".join(current_lines)))
    return sections
```

Then token-chunk each section independently (4K tokens, 500 overlap).

### JSON Response Format

Ask Claude to return raw JSON only (no markdown fences). Example schema:

```json
{"extractions": [{"text": "...", "type": "question_taught", "nepq_stage": 2, "context_note": "..."}]}
```

Parse defensively -- strip markdown fences if present, find first `{` to last `}` as fallback.

### Progress Tracking

```python
# JSON sidecar, keyed by chunk identity
progress_key = f"{folder_name}::{video_name}::chunk_{idx}"
# Load at start, skip if key present, save after each successful chunk
```

### Concurrency

```python
MAX_CONCURRENCY = 5
semaphore = asyncio.Semaphore(MAX_CONCURRENCY)

async def process_chunk_with_sem(chunk, ...):
    async with semaphore:
        return await process_chunk(chunk, ...)

tasks = [process_chunk_with_sem(c) for c in all_chunks]
results = await asyncio.gather(*tasks)
```

---

## 2. Truth Builder

**Example:** `truth_builder.py`

### Pipeline

1. Read `transcript.txt` files from per-video folders (`output/videos/video-name/transcript.txt`)
2. SEQUENTIAL -- each call passes the CURRENT cumulative `truth_doc` + the new transcript
3. Claude extracts only what is NEW vs what is already in the truth doc
4. Merge updates into the truth doc section by section
5. Save `truth_doc` after every video

### Progress Tracking

```python
# Log file -- one line per video, DONE: prefix = processed
# "DONE: 2026-04-23_the-best-cold-call"
# Read at start -> set of folder names -> skip those folders
```

### No Concurrency

Each call depends on the previous `truth_doc` state. Run videos one at a time.

---

## 3. The Core Subprocess Call (Canonical Pattern)

This is the single most important piece. Copy this exactly.

```python
import asyncio, os, shutil, sys

CLAUDE_CLI = shutil.which("claude")
if not CLAUDE_CLI:
    sys.exit("FATAL: claude not on PATH -- install Claude Code")

MODEL = "claude-sonnet-4-5-20250929"  # MUST specify -- Haiku paraphrases, Sonnet extracts verbatim


async def call_claude(prompt: str, label: str) -> str:
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)        # REQUIRED -- strips AutoForge env vars
    env.pop("ANTHROPIC_API_KEY", None)  # REQUIRED -- forces subscription auth

    for attempt, delay in enumerate([0, 2, 5, 10]):
        if delay:
            await asyncio.sleep(delay)
        try:
            proc = await asyncio.create_subprocess_exec(
                CLAUDE_CLI, "-p",                  # -p with NO inline arg = reads stdin
                "--model", MODEL,
                "--output-format", "text",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            out_b, err_b = await asyncio.wait_for(
                proc.communicate(input=prompt.encode("utf-8")),  # prompt via stdin
                timeout=300
            )
            if proc.returncode == 0:
                return out_b.decode("utf-8", errors="replace").strip()
            if proc.returncode in (15, 3) and attempt < 3:
                continue  # exit 15 = spurious SIGTERM, retry
            return ""
        except asyncio.TimeoutError:
            proc.kill()
            if attempt < 3:
                continue
            return ""
    return ""
```

---

## 4. Why Stdin Pipe (Not `-p "string"`)

| Approach | Limit | Works for truth builder? |
|----------|-------|--------------------------|
| `claude -p "giant string"` | Windows CreateProcess caps `lpCommandLine` at ~32,767 chars | No -- truth doc grows to 50K+ chars |
| `claude -p` + stdin pipe | Only Claude's context window (~200K tokens = ~800K chars for Sonnet 4.6) | Yes -- any practical size |

The command line with stdin is just `claude -p --model ... --output-format text` (tiny). The entire prompt flows through stdin with no size limit.

---

## 5. Exit 15 -- Spurious SIGTERM

- Happens when multiple Claude subprocesses hit the subscription auth layer simultaneously
- NOT a real error -- just a race condition in the auth handshake
- Fix: retry up to 3x with delays `[2, 5, 10]` seconds
- At concurrency 5 you will see some exit 15s -- normal, retries catch them all
- Running 2-3 scripts in parallel: drop per-script concurrency to 2-3

---

## 6. Auth Pattern -- Why Pop Env Vars

Inside AutoForge/Claude Code, the environment has `CLAUDECODE=1` and sometimes `ANTHROPIC_API_KEY` set. These vars can cause the subprocess to route through the API (costs money) or fail outright. Popping them forces the subprocess to use your `claude login` subscription session.

Do this for EVERY subprocess call, including preflight.

---

## 7. Preflight Check

Every script must run a preflight before touching real data:

```python
async def preflight():
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    env.pop("ANTHROPIC_API_KEY", None)

    for attempt, delay in enumerate([0, 2, 5, 10]):
        if delay:
            await asyncio.sleep(delay)
        proc = await asyncio.create_subprocess_exec(
            CLAUDE_CLI, "-p", "say only the word OK",  # inline -p is fine here (tiny)
            "--model", MODEL,
            "--output-format", "text",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        out_b, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
        if proc.returncode == 0:
            print("Preflight OK")
            return
        if proc.returncode in (15, 3) and attempt < 3:
            continue
    sys.exit("Preflight FAILED -- run `claude login` and retry")
```

- Preflight uses inline `-p "small string"` (tiny, no arg limit risk)
- Must also retry on exit 15 (same retry loop)
- If preflight fails after all retries: `claude login` and retry

---

## 8. Stdin Size Limit

The only real limit is Claude's context window: ~200,000 tokens for Sonnet 4.6, which is roughly 800,000 characters. A truth_doc hitting 800K chars would need a different approach.

In practice for a 100-video channel, truth_doc typically grows to 50K-150K chars -- well within limits. You would need 500+ hours of dense video content before hitting the context window.

---

## 9. File Naming / Folder Conventions

| Item | Path pattern |
|------|-------------|
| Scripts | `scripts/{topic}/script_name.py` |
| Output (mining, Jeremy Miner corpus) | `docs/info/jeremy-miner-corpus/{corpus-name}/` |
| Output (truth builder, AI agency) | `output/truth_document.md` |
| Output (truth builder, meta programs) | `E:\AutoForge\Metaprograms\` |

---

## 10. Alternative Approaches

Use the stdin pipe pattern above by default. These alternatives exist for edge cases.

| Approach | When to use | Tradeoff |
|----------|-------------|----------|
| **Temp file** -- write prompt to disk, pass file path | Stdin pipe has a specific bug on your OS/CLI version | Messier (cleanup needed), same effect |
| **Multi-file truth_doc** -- split into chapters, run one pass per chapter | Truth doc approaches context window limits (rare) | Claude cannot cross-reference between chapters in one call |
| **Python `anthropic` SDK** -- `pip install anthropic` + direct API calls | High-volume automated pipelines where you need true parallelism | Requires API key (costs money) or extracting subscription auth token (fragile). No subprocess, no stdin, no arg limits, no exit 15s |
| **Chunked sequential passes** -- pass only last N chars of truth_doc | Truth doc genuinely exceeds context window | Claude might re-add things captured early in the doc |

---

## Quick-Start Skeleton

```python
#!/usr/bin/env python3
"""Mining script skeleton. Replace TODOs with your extraction logic."""

import asyncio, json, os, shutil, sys
from pathlib import Path

CLAUDE_CLI = shutil.which("claude")
if not CLAUDE_CLI:
    sys.exit("FATAL: claude not on PATH")

MODEL = "claude-sonnet-4-5-20250929"
MAX_CONCURRENCY = 5
SOURCE_DIR = Path("path/to/transcripts")
OUTPUT_DIR = Path("path/to/output")
PROGRESS_FILE = OUTPUT_DIR / "progress.json"


async def call_claude(prompt: str, label: str) -> str:
    # ... (copy canonical pattern from section 3 above)
    pass


def load_progress() -> dict:
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
    return {}


def save_progress(progress: dict):
    PROGRESS_FILE.write_text(json.dumps(progress, indent=2), encoding="utf-8")


async def process_chunk(section_title: str, chunk: str, idx: int,
                        folder: str, video: str, progress: dict) -> None:
    key = f"{folder}::{video}::chunk_{idx}"
    if key in progress:
        return

    prompt = f"""TODO: your system prompt here.

Section: {section_title}

{chunk}"""

    result = await call_claude(prompt, key)
    if result:
        # TODO: parse JSON, append to output files
        progress[key] = True
        save_progress(progress)


async def main():
    # Preflight
    # ... (copy from section 7)

    progress = load_progress()
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
    tasks = []

    for md_file in sorted(SOURCE_DIR.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        sections = split_sections(text)  # copy from section above
        for section_title, content in sections:
            chunks = chunk_text(content, max_tokens=4000, overlap=500)  # TODO: implement
            for idx, chunk in enumerate(chunks):
                async def _task(s=section_title, c=chunk, i=idx,
                                f=SOURCE_DIR.name, v=md_file.stem):
                    async with semaphore:
                        await process_chunk(s, c, i, f, v, progress)
                tasks.append(_task())

    await asyncio.gather(*tasks)
    print(f"Done. {len(progress)} chunks processed.")


if __name__ == "__main__":
    asyncio.run(main())
```
