"""
PRD Analyzer — 4-Stage Analysis Pipeline
=========================================

Ingestion → Codebase Discovery → Task Extraction → Consulting Review

Each stage uses Claude Sonnet via subscription auth (cheap, fast).
Prompts are loaded from ~/.autoforge/prd_shredder_prompts.json so they
can be edited without touching code.
"""

import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Callable, Optional

from ..models.prd_shredder import PRDAnalysis, PRDTask

logger = logging.getLogger(__name__)

# Default model for analysis stages (Sonnet — cheap, fast)
DEFAULT_ANALYSIS_MODEL = "claude-sonnet-4-6"

# Prompt config file
PROMPT_CONFIG_PATH = Path.home() / ".autoforge" / "prd_shredder_prompts.json"

# ---------------------------------------------------------------------------
# Default prompts — written to config file on first use
# ---------------------------------------------------------------------------

DEFAULT_PROMPTS = {
    "stage1_ingestion": (
        "You are a PRD analyst. Read this PRD and extract:\n\n"
        "1. OBJECTIVE — What is being built or fixed? One sentence.\n"
        "2. TARGET FILES — Every file mentioned that needs to be created or modified.\n"
        "3. REQUIREMENTS — Every specific requirement, numbered.\n"
        "4. SUCCESS CRITERIA — How do we know it's done?\n"
        "5. DEPENDENCIES — What must exist before this can be built?\n"
        "6. SCOPE — What is explicitly OUT of scope?\n"
        "7. DIFFICULTY — Your honest estimate (1-10) with reasoning.\n\n"
        "Return as a single JSON object with keys: objective, target_files, requirements, "
        "success_criteria, dependencies, scope_exclusions, difficulty, difficulty_reasoning.\n\n"
        "CRITICAL: Your ENTIRE response must be a single JSON object. No markdown, no code fences, "
        "no preamble. Start with {{ and end with }}.\n\n"
        "PRD:\n{prd_text}"
    ),
    "stage2_discovery": (
        "You are a codebase analyst. You've been given a PRD analysis and a file listing "
        "of the target repository.\n\n"
        "PRD Analysis:\n{stage1_output}\n\n"
        "Repository file tree:\n{file_tree}\n\n"
        "Key file contents (auto-selected based on PRD target files):\n{relevant_file_contents}\n\n"
        "Analyze:\n"
        "1. Which files from the PRD already exist? What's their current state?\n"
        "2. Which files need to be created from scratch?\n"
        "3. Which existing files need modification? What specifically needs to change?\n"
        "4. Are there patterns in the codebase the new code should follow? (naming, structure, imports)\n"
        "5. Are there any conflicts between the PRD and the current codebase?\n"
        "6. What is the correct order to make these changes? (dependencies between files)\n\n"
        "Return as a single JSON object with keys: existing_files (list of {{path, state}}), "
        "files_to_create (list of paths), files_to_modify (list of {{path, changes}}), "
        "codebase_patterns (list of strings), conflicts (list of strings), "
        "suggested_order (list of paths).\n\n"
        "CRITICAL: Your ENTIRE response must be a single JSON object. No markdown, no code fences, "
        "no preamble. Start with {{ and end with }}.\n\n"
    ),
    "stage3_tasks": (
        "You are a task planner for a coding agent. Given the PRD analysis and codebase discovery, "
        "create an ordered list of exact code tasks.\n\n"
        "PRD Analysis:\n{stage1_output}\n\n"
        "Codebase Discovery:\n{stage2_output}\n\n"
        "For each task, specify:\n"
        "1. task_number — execution order\n"
        "2. action — \"create_file\" | \"modify_file\" | \"delete_lines\" | \"add_dependency\"\n"
        "3. file_path — exact path relative to repo root\n"
        "4. description — what to do in plain English\n"
        "5. details — specific code patterns to follow, functions to create, imports needed\n"
        "6. depends_on — which task numbers must complete first\n"
        "7. verification — how to check this task succeeded (lint command, import check, etc.)\n\n"
        "Rules:\n"
        "- Each task should be small enough to verify independently\n"
        "- Order tasks so dependencies come first\n"
        "- Group related changes (e.g., model + router + UI for same feature)\n"
        "- Include lint/test verification as separate tasks between groups\n\n"
        "Return as a JSON object with key \"tasks\" containing an array of task objects.\n\n"
        "CRITICAL: Your ENTIRE response must be a single JSON object. No markdown, no code fences, "
        "no preamble. Start with {{ and end with }}.\n\n"
    ),
    "stage4_review": (
        "You are a senior software architect reviewing a build plan before execution.\n\n"
        "Original PRD:\n{prd_text}\n\n"
        "Extracted Tasks:\n{stage3_output}\n\n"
        "Review this plan and identify:\n\n"
        "1. MISSING TASKS — What did the task extraction miss? Are there obvious requirements "
        "in the PRD that don't have corresponding tasks?\n\n"
        "2. ORDER PROBLEMS — Are any tasks in the wrong order? Will anything fail because "
        "a dependency hasn't been created yet?\n\n"
        "3. SCOPE CREEP — Are any tasks doing MORE than the PRD asks for? Remove them.\n\n"
        "4. INTEGRATION GAPS — After all tasks complete, will everything actually work together? "
        "Are there missing imports, missing route registrations, missing UI links?\n\n"
        "5. RISK ASSESSMENT — Which tasks are most likely to cause problems? Flag them.\n\n"
        "6. FINAL TASK LIST — Return the corrected, complete task list.\n"
        "Add any missing tasks. Remove any scope-creep tasks. Fix the order.\n\n"
        "Return as a JSON object with key \"tasks\" containing the corrected array of task objects, "
        "plus \"review_notes\" (string with your findings).\n\n"
        "CRITICAL: Your ENTIRE response must be a single JSON object. No markdown, no code fences, "
        "no preamble. Start with {{ and end with }}.\n\n"
    ),
}


def _load_prompts() -> dict[str, str]:
    """Load prompts from config file, creating defaults if missing."""
    if PROMPT_CONFIG_PATH.exists():
        try:
            data = json.loads(PROMPT_CONFIG_PATH.read_text(encoding="utf-8"))
            # Merge with defaults so new prompts are added on upgrade
            merged = {**DEFAULT_PROMPTS, **data}
            return merged
        except Exception as e:
            logger.warning("Failed to load prompt config: %s — using defaults", e)

    # Write defaults
    PROMPT_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROMPT_CONFIG_PATH.write_text(json.dumps(DEFAULT_PROMPTS, indent=2), encoding="utf-8")
    logger.info("Created default PRD Shredder prompts at %s", PROMPT_CONFIG_PATH)
    return dict(DEFAULT_PROMPTS)


# ---------------------------------------------------------------------------
# File tree + content helpers
# ---------------------------------------------------------------------------

def _get_file_tree(repo_dir: Path, max_depth: int = 4) -> str:
    """Get a file tree listing of the repo (respects .gitignore via git ls-files)."""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split("\n")
            # Filter to max_depth
            filtered = [f for f in lines if f.count("/") < max_depth]
            # Limit to 500 lines
            if len(filtered) > 500:
                filtered = filtered[:500]
                filtered.append(f"... ({len(lines) - 500} more files)")
            return "\n".join(filtered)
    except Exception as e:
        logger.warning("git ls-files failed: %s — falling back to os.walk", e)

    # Fallback: os.walk
    lines = []
    for root, dirs, files in os.walk(repo_dir):
        # Skip hidden dirs and node_modules
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules" and d != "__pycache__"]
        rel = Path(root).relative_to(repo_dir)
        depth = len(rel.parts)
        if depth >= max_depth:
            dirs.clear()
            continue
        for f in files:
            lines.append(str(rel / f) if str(rel) != "." else f)
        if len(lines) > 500:
            break
    return "\n".join(lines[:500])


def _read_relevant_files(repo_dir: Path, target_files: list[str], max_chars: int = 100_000) -> str:
    """Read the contents of files mentioned in the PRD analysis."""
    contents = []
    total_chars = 0

    for file_path in target_files:
        full_path = repo_dir / file_path
        if not full_path.exists() or not full_path.is_file():
            continue

        try:
            # Ensure path is within repo
            full_path.resolve().relative_to(repo_dir.resolve())
        except ValueError:
            continue

        try:
            text = full_path.read_text(encoding="utf-8", errors="replace")
            if total_chars + len(text) > max_chars:
                # Truncate this file
                remaining = max_chars - total_chars
                if remaining > 200:
                    text = text[:remaining] + "\n... (truncated)"
                else:
                    break
            contents.append(f"=== {file_path} ===\n{text}")
            total_chars += len(text)
        except Exception as e:
            logger.warning("Failed to read %s: %s", file_path, e)

    return "\n\n".join(contents) if contents else "(no target files found in repo)"


# ---------------------------------------------------------------------------
# JSON parsing helpers (copied from yt_processor pattern)
# ---------------------------------------------------------------------------

def _repair_json(text: str) -> str:
    """Best-effort repair of common LLM JSON mistakes."""
    text = re.sub(r",\s*([}\]])", r"\1", text)
    text = re.sub(r"}\s*{", "},{", text)
    text = re.sub(r"//[^\n]*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return text


def _parse_json_response(raw_text: str) -> dict:
    """Parse JSON from AI response, handling wrappers and errors."""
    text = raw_text.strip()

    # Try 1: direct parse
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass

    # Try 2: strip markdown fences
    if "```" in text:
        fence_match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
        if fence_match:
            try:
                return json.loads(fence_match.group(1).strip())
            except (json.JSONDecodeError, ValueError):
                pass

    # Try 3: brace extraction
    first = text.find("{")
    last = text.rfind("}")
    if first >= 0 and last > first:
        candidate = text[first:last + 1]
        try:
            return json.loads(candidate)
        except (json.JSONDecodeError, ValueError):
            pass
        # Try 4: repair + parse
        try:
            return json.loads(_repair_json(candidate))
        except (json.JSONDecodeError, ValueError):
            pass

    raise ValueError(f"Could not parse JSON from response (length={len(text)}). Preview: {text[:300]}")


# ---------------------------------------------------------------------------
# SDK caller (subscription auth — copied from yt_processor._call_via_sdk)
# ---------------------------------------------------------------------------

# SDK timeout: 15 minutes (PRD analysis is multi-stage and can stall on rate limits)
SDK_TIMEOUT_SECONDS = 900

# Retry config for rate limit recovery
MAX_SDK_RETRIES = 3
RETRY_DELAYS = [30, 60, 120]  # Exponential backoff in seconds


async def _call_via_sdk(
    system_prompt: str,
    user_message: str,
    model: str,
    timeout: float | None = None,
    on_progress: Optional[Callable[[str], None]] = None,
) -> str:
    """Call Claude via the Agent SDK using SUBSCRIPTION auth ONLY.

    Copied from yt_processor._call_via_sdk — see that file for full docs.
    Uses permission_mode='acceptEdits', NOT 'bypassPermissions'.
    Wraps receive_response() in try/except for rate_limit_event recovery.
    """
    from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

    from registry import get_effective_sdk_env

    def _log(msg: str) -> None:
        logger.info(msg)
        if on_progress:
            on_progress(msg)

    os.environ.pop("CLAUDECODE", None)

    system_cli = shutil.which("claude")
    if not system_cli:
        raise RuntimeError("Claude CLI not found on PATH")

    sdk_env = get_effective_sdk_env(force_subscription=True)
    sdk_env.pop("CLAUDECODE", None)

    scratch = tempfile.mkdtemp(prefix="prd_analyzer_")

    settings_file = Path(scratch) / ".claude-prd-settings.json"
    settings_file.write_text(json.dumps({
        "permissions": {
            "defaultMode": "acceptEdits",
            "allow": [],
        },
    }))

    client = ClaudeSDKClient(
        options=ClaudeAgentOptions(
            model=model,
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

    effective_timeout = timeout if timeout is not None else SDK_TIMEOUT_SECONDS
    _log(f"[PRD Analyzer] Model={model} | Timeout={effective_timeout}s | Payload={len(user_message):,} chars")

    async def _run_sdk() -> str:
        sdk_t0 = time.time()

        try:
            await client.__aenter__()
        except Exception as enter_err:
            _log(f"[PRD Analyzer] CLI FAILED TO START: {enter_err}")
            raise RuntimeError(f"Claude CLI failed to start: {enter_err}") from enter_err

        await client.query(user_message)
        sdk_t2 = time.time()
        _log("[PRD Analyzer] Query sent — waiting for response...")

        full_text = ""
        msg_count = 0
        sdk_error: str | None = None
        rate_limit_count = 0
        last_progress_time = time.time()

        try:
            async for msg in client.receive_response():
                now = time.time()
                elapsed = now - sdk_t2
                msg_type = type(msg).__name__
                msg_count += 1

                if now - last_progress_time >= 15:
                    _log(f"[PRD Analyzer] Still waiting... {elapsed:.0f}s | {len(full_text):,} chars")
                    last_progress_time = now

                if msg_type in ("RateLimitEvent", "rate_limit_event"):
                    rate_limit_count += 1
                    _log(f"[PRD Analyzer] Rate limit #{rate_limit_count} at {elapsed:.0f}s")
                    continue

                elif msg_type == "AssistantMessage" and hasattr(msg, "content"):
                    for block in msg.content:
                        if type(block).__name__ == "TextBlock" and hasattr(block, "text"):
                            full_text += block.text

                elif msg_type == "ResultMessage":
                    is_error = getattr(msg, "is_error", False)
                    if is_error:
                        result_text = ""
                        if hasattr(msg, "result") and msg.result:
                            result_text = str(msg.result)[:500]
                        sdk_error = f"SDK error: {result_text}" if result_text else "SDK ResultMessage error"
                        _log(f"[PRD Analyzer] ERROR: {sdk_error}")

        except Exception as stream_exc:
            exc_str = str(stream_exc)
            if full_text.strip() and "unknown message type" in exc_str.lower():
                _log(f"[PRD Analyzer] Recovered {len(full_text):,} chars despite SDK error")
            elif full_text.strip():
                _log(f"[PRD Analyzer] Stream error — using {len(full_text):,} chars collected")
            else:
                raise

        total = time.time() - sdk_t0
        _log(f"[PRD Analyzer] Done: {len(full_text):,} chars in {total:.1f}s")

        if sdk_error:
            raise RuntimeError(sdk_error)
        if not full_text.strip():
            raise RuntimeError("Claude returned empty response")
        return full_text.strip()

    last_error: Exception | None = None
    for attempt in range(MAX_SDK_RETRIES):
        try:
            result = await asyncio.wait_for(_run_sdk(), timeout=effective_timeout)
            return result
        except asyncio.TimeoutError:
            last_error = RuntimeError(f"Claude timed out after {effective_timeout}s")
            # Timeouts are retryable (could be transient rate limit stall)
        except RuntimeError as e:
            last_error = e
            err_str = str(e).lower()
            # Only retry on rate limit / unknown message type errors
            if "rate_limit" not in err_str and "unknown message type" not in err_str:
                break  # Non-retryable error
        except Exception as e:
            last_error = e
            err_str = str(e).lower()
            if "rate_limit" not in err_str and "unknown message type" not in err_str:
                break
        finally:
            # Clean up the client between attempts
            try:
                await client.__aexit__(None, None, None)
            except Exception:
                pass

        # Retry with backoff
        if attempt < MAX_SDK_RETRIES - 1:
            delay = RETRY_DELAYS[attempt]
            _log(f"[PRD Analyzer] Rate limited — waiting {delay}s before retry "
                 f"(attempt {attempt + 2}/{MAX_SDK_RETRIES})")
            await asyncio.sleep(delay)

            # Re-create client for next attempt
            client = ClaudeSDKClient(
                options=ClaudeAgentOptions(
                    model=model,
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

    # All retries exhausted
    try:
        shutil.rmtree(scratch, ignore_errors=True)
    except Exception:
        pass
    raise last_error or RuntimeError("All SDK retries exhausted")


# ---------------------------------------------------------------------------
# The 4-Stage Pipeline
# ---------------------------------------------------------------------------

class PRDAnalyzer:
    """4-stage PRD analysis pipeline: Ingestion → Discovery → Tasks → Review."""

    def __init__(self, model: str | None = None):
        self.model = model or os.getenv("PRD_SHREDDER_ANALYSIS_MODEL", DEFAULT_ANALYSIS_MODEL)

    async def analyze(
        self,
        prd_text: str,
        repo_dir: Path,
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> PRDAnalysis:
        """Run the full 4-stage analysis pipeline."""
        prompts = _load_prompts()
        t0 = time.time()

        def _log(msg: str) -> None:
            logger.info(msg)
            if on_progress:
                on_progress(msg)

        # ---- Stage 1: PRD Ingestion ----
        _log("[Stage 1/4] Ingesting PRD...")
        stage1_prompt = prompts["stage1_ingestion"].format(prd_text=prd_text)
        stage1_raw = await _call_via_sdk(
            "You are a PRD analyst. Output ONLY valid JSON.",
            stage1_prompt,
            self.model,
            on_progress=on_progress,
        )
        stage1 = _parse_json_response(stage1_raw)
        _log(f"[Stage 1/4] Done — difficulty={stage1.get('difficulty', '?')}/10, "
             f"{len(stage1.get('target_files', []))} target files")

        # ---- Stage 2: Codebase Discovery ----
        _log("[Stage 2/4] Scanning codebase...")
        file_tree = _get_file_tree(repo_dir)
        target_files = stage1.get("target_files", [])
        relevant_contents = _read_relevant_files(repo_dir, target_files)

        stage2_prompt = prompts["stage2_discovery"].format(
            stage1_output=json.dumps(stage1, indent=2),
            file_tree=file_tree,
            relevant_file_contents=relevant_contents,
        )
        stage2_raw = await _call_via_sdk(
            "You are a codebase analyst. Output ONLY valid JSON.",
            stage2_prompt,
            self.model,
            on_progress=on_progress,
        )
        stage2 = _parse_json_response(stage2_raw)
        _log(f"[Stage 2/4] Done — {len(stage2.get('files_to_create', []))} to create, "
             f"{len(stage2.get('files_to_modify', []))} to modify")

        # ---- Stage 3: Task Extraction ----
        _log("[Stage 3/4] Extracting tasks...")
        stage3_prompt = prompts["stage3_tasks"].format(
            stage1_output=json.dumps(stage1, indent=2),
            stage2_output=json.dumps(stage2, indent=2),
        )
        stage3_raw = await _call_via_sdk(
            "You are a task planner for a coding agent. Output ONLY valid JSON.",
            stage3_prompt,
            self.model,
            on_progress=on_progress,
        )
        stage3 = _parse_json_response(stage3_raw)
        raw_tasks = stage3.get("tasks", [])
        _log(f"[Stage 3/4] Done — {len(raw_tasks)} tasks extracted")

        # ---- Stage 4: Consulting Review ----
        _log("[Stage 4/4] Consulting review...")
        stage4_prompt = prompts["stage4_review"].format(
            prd_text=prd_text,
            stage3_output=json.dumps(stage3, indent=2),
        )
        stage4_raw = await _call_via_sdk(
            "You are a senior software architect. Output ONLY valid JSON.",
            stage4_prompt,
            self.model,
            on_progress=on_progress,
        )
        stage4 = _parse_json_response(stage4_raw)
        final_tasks_raw = stage4.get("tasks", raw_tasks)
        review_notes = stage4.get("review_notes", "")
        if review_notes:
            _log(f"[Stage 4/4] Review notes: {review_notes[:200]}")

        # Build PRDTask objects
        tasks = []
        for t in final_tasks_raw:
            tasks.append(PRDTask(
                task_number=t.get("task_number", len(tasks) + 1),
                action=t.get("action", "modify_file"),
                file_path=t.get("file_path", ""),
                description=t.get("description", ""),
                details=t.get("details", ""),
                depends_on=t.get("depends_on", []),
                verification=t.get("verification", ""),
            ))

        elapsed = time.time() - t0
        _log(f"[Analysis Complete] {len(tasks)} tasks in {elapsed:.1f}s")

        return PRDAnalysis(
            objective=stage1.get("objective", ""),
            target_files=stage1.get("target_files", []),
            requirements=stage1.get("requirements", []),
            success_criteria=stage1.get("success_criteria", []),
            dependencies=stage1.get("dependencies", []),
            scope_exclusions=stage1.get("scope_exclusions", []),
            difficulty=stage1.get("difficulty", 0),
            difficulty_reasoning=stage1.get("difficulty_reasoning", ""),
            existing_files=stage2.get("existing_files", []),
            files_to_create=stage2.get("files_to_create", []),
            files_to_modify=stage2.get("files_to_modify", []),
            codebase_patterns=stage2.get("codebase_patterns", []),
            conflicts=stage2.get("conflicts", []),
            tasks=tasks,
            analysis_model=self.model,
            analysis_time=round(elapsed, 2),
        )
