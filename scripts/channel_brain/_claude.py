#!/usr/bin/env python3
"""
_claude.py — Shared auth + call utilities for channel_brain scripts.

Pattern: subscription auth via claude CLI subprocess, stdin pipe for prompts.
No ANTHROPIC_API_KEY. No server. No AutoForge restart needed.

Import from any sweep file:
    from _claude import preflight, call_claude_stdin, parse_json, ...
"""

import asyncio
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

# Pop at import time — every subprocess inherits clean env (CLAUDECODE=1 → exit 11)
os.environ.pop("CLAUDECODE", None)

MODEL = "claude-sonnet-4-5-20250929"  # Sonnet 4.6 — explicit, never default to Haiku
CALL_TIMEOUT = 600                     # 10 min per call (long transcripts)
RETRY_DELAYS = [10, 20, 40]           # backoff on exit 15 / transient failures

_CLAUDE_CLI: str = ""
_SCRATCH_DIR: str = ""


# =============================================================================
# CLI + SCRATCH
# =============================================================================

def resolve_claude_cli() -> str:
    global _CLAUDE_CLI
    if _CLAUDE_CLI:
        return _CLAUDE_CLI
    cli = shutil.which("claude")
    if not cli:
        print("FATAL: 'claude' CLI not found on PATH.")
        print("  Install: https://docs.anthropic.com/en/docs/claude-code")
        sys.exit(2)
    _CLAUDE_CLI = cli
    return cli


def setup_scratch() -> str:
    """Minimal settings file in temp dir — avoids project .claude settings causing exit 11."""
    global _SCRATCH_DIR
    if _SCRATCH_DIR:
        return _SCRATCH_DIR
    scratch = tempfile.mkdtemp(prefix="channel_brain_")
    settings = Path(scratch) / "settings.json"
    settings.write_text(json.dumps({
        "permissions": {"defaultMode": "acceptEdits", "allow": []}
    }), encoding="utf-8")
    _SCRATCH_DIR = scratch
    return scratch


def cleanup_scratch() -> None:
    if _SCRATCH_DIR:
        shutil.rmtree(_SCRATCH_DIR, ignore_errors=True)


def _clean_env() -> dict:
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    env.pop("ANTHROPIC_API_KEY", None)
    return env


# =============================================================================
# PREFLIGHT
# =============================================================================

async def preflight(retries: int = 3) -> None:
    """Verify subscription auth. Retries on exit 15 (spurious SIGTERM)."""
    cli = resolve_claude_cli()
    env = _clean_env()
    print(f"Preflight: verifying claude subscription auth ... (CLI: {cli})", flush=True)

    wait_times = [5, 15, 30]
    for attempt in range(retries):
        try:
            proc = await asyncio.create_subprocess_exec(
                cli, "-p", "Reply with the single word: OK",
                "--output-format", "text",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            out_b, err_b = await asyncio.wait_for(proc.communicate(), timeout=60)
            out = out_b.decode("utf-8", errors="replace").strip()

            if proc.returncode == 0 and out:
                print(f"Preflight OK — claude responded: {out[:60]!r}\n", flush=True)
                return

            wait = wait_times[min(attempt, len(wait_times) - 1)]
            err = err_b.decode("utf-8", errors="replace").strip()
            print(
                f"  preflight exit {proc.returncode} (attempt {attempt + 1}/{retries}), "
                f"retry in {wait}s ... stderr={err[:100]!r}",
                flush=True,
            )
            await asyncio.sleep(wait)

        except asyncio.TimeoutError:
            print(f"  preflight timeout (attempt {attempt + 1}/{retries}), retrying ...", flush=True)

    print("FATAL: preflight failed after all retries.")
    print("  Try: claude login  then re-run this script.")
    sys.exit(3)


# =============================================================================
# CLAUDE CALL — STDIN PIPE (no arg-length limit)
# =============================================================================

async def call_claude_stdin(prompt: str, label: str = "") -> str | None:
    """
    Send prompt via stdin. No Windows command-line length limit.
    Claude reads from stdin when -p is absent and stdin isn't a terminal.
    Returns response text or None on failure after retries.
    """
    cli = resolve_claude_cli()
    env = _clean_env()
    tag = f"[{label}] " if label else ""

    for attempt, delay in enumerate([0] + RETRY_DELAYS):
        if delay:
            await asyncio.sleep(delay)

        try:
            proc = await asyncio.create_subprocess_exec(
                cli,
                "--model", MODEL,
                "--output-format", "text",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            try:
                out_b, err_b = await asyncio.wait_for(
                    proc.communicate(input=prompt.encode("utf-8")),
                    timeout=CALL_TIMEOUT,
                )
            except asyncio.TimeoutError:
                proc.kill()
                print(
                    f"  ! {tag}timeout at {CALL_TIMEOUT}s (attempt {attempt + 1})",
                    flush=True,
                )
                continue

            out = out_b.decode("utf-8", errors="replace")
            err = err_b.decode("utf-8", errors="replace").strip()

            if proc.returncode == 0 and out.strip():
                return out

            print(
                f"  ! {tag}exit {proc.returncode} (attempt {attempt + 1}/{len(RETRY_DELAYS) + 1}) "
                f"stderr={err[:150]!r}",
                flush=True,
            )

        except FileNotFoundError as exc:
            print(f"  ! cannot launch claude CLI: {exc}", flush=True)
            return None

    return None


# =============================================================================
# JSON PARSING
# =============================================================================

def parse_json(raw: str) -> dict | list | None:
    """Parse JSON from raw response. Handles markdown fences + preamble text."""
    text = raw.strip()

    # 1. Direct
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass

    # 2. Markdown fences
    if "```" in text:
        m = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1).strip())
            except (json.JSONDecodeError, ValueError):
                pass

    # 3. First balanced object
    fb, lb = text.find("{"), text.rfind("}")
    if fb >= 0 and lb > fb:
        try:
            return json.loads(text[fb:lb + 1])
        except (json.JSONDecodeError, ValueError):
            pass

    # 4. First balanced array
    fa, la = text.find("["), text.rfind("]")
    if fa >= 0 and la > fa:
        try:
            return json.loads(text[fa:la + 1])
        except (json.JSONDecodeError, ValueError):
            pass

    return None


# =============================================================================
# CONFIG + PROGRESS
# =============================================================================

def load_config(config_path: str) -> dict:
    p = Path(config_path)
    if not p.exists():
        print(f"FATAL: config not found: {config_path}")
        sys.exit(1)
    return json.loads(p.read_text(encoding="utf-8"))


def load_progress(output_dir: Path) -> dict:
    p = output_dir / "_progress.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "sweeps_done": [],
        "sweep1_done": [],
        "sweep1_errors": [],
    }


def save_progress(output_dir: Path, state: dict) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "_progress.json").write_text(
        json.dumps(state, indent=2), encoding="utf-8"
    )
