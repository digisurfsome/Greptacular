"""
Gemini CLI Bridge
=================

Drives Google's Gemini CLI in headless mode using ``--output-format stream-json``.
Parses JSONL events (init, message, tool_use, tool_result, result) and forwards
them as workspace-compatible event dicts.

Used by WorkspaceChatSession when provider == "gemini".

Session resume: Gemini CLI supports ``--resume <sessionId>`` to continue
previous conversations. The session_id from the ``init`` event is stored
and used for subsequent calls.
"""

import asyncio
import json
import logging
import os
import shutil
from pathlib import Path
from typing import AsyncGenerator, Optional

logger = logging.getLogger(__name__)


def _find_gemini() -> Optional[str]:
    """Find gemini CLI, checking PATH first then common npm global locations."""
    # 1. Check PATH
    found = shutil.which("gemini")
    if found:
        return found
    # 2. Check common npm global bin dirs (Windows)
    npm_global = Path(os.environ.get("APPDATA", "")) / "npm" / "gemini.cmd"
    if npm_global.exists():
        return str(npm_global)
    # 3. Check npm prefix
    npm_prefix = shutil.which("npm")
    if npm_prefix:
        prefix_dir = Path(npm_prefix).parent
        for name in ("gemini.cmd", "gemini"):
            candidate = prefix_dir / name
            if candidate.exists():
                return str(candidate)
    return None


class GeminiBridge:
    """
    Manages Gemini CLI invocations in headless streaming mode.

    Unlike the Codex bridge (which keeps a long-lived MCP server process),
    the Gemini bridge spawns a new ``gemini`` process per turn with
    ``--output-format stream-json``. Session continuity is achieved via
    the ``--resume <session_id>`` flag using the session_id from the
    previous ``init`` event.

    This approach is simpler and more robust — each turn is an independent
    process, so crashes don't lose the session state.
    """

    def __init__(
        self,
        *,
        cwd: str,
        model: Optional[str] = None,
        approval_mode: str = "yolo",   # "default", "auto_edit", "yolo"
        sandbox: bool = False,
    ):
        self.cwd = str(Path(cwd).resolve())
        self.model = model  # e.g. "pro", "flash", "flash-lite", or full model ID
        self.approval_mode = approval_mode
        self.sandbox = sandbox
        self.session_id: Optional[str] = None

        self._current_process: Optional[asyncio.subprocess.Process] = None

    async def start(self) -> None:
        """Pre-check Gemini CLI availability before starting the session."""
        gemini_path = _find_gemini()
        if not gemini_path:
            raise RuntimeError(
                "Gemini CLI is not installed globally.\n\n"
                "Please install it by running this command in your terminal:\n"
                "  npm install -g @google/gemini-cli\n\n"
                "If it is already installed, make sure it is on your system PATH."
            )
        logger.info("Found Gemini CLI at: %s", gemini_path)

    async def close(self) -> None:
        """Kill any running Gemini process."""
        if self._current_process:
            try:
                self._current_process.terminate()
                await asyncio.wait_for(self._current_process.wait(), timeout=5)
            except (asyncio.TimeoutError, ProcessLookupError):
                try:
                    self._current_process.kill()
                except ProcessLookupError:
                    pass
            self._current_process = None

    async def send(self, prompt: str) -> str:
        """Send a prompt and return the complete response text."""
        full_text: list[str] = []
        async for event in self.send_streaming(prompt):
            if event["type"] == "text":
                full_text.append(event["content"])
        return "".join(full_text)

    async def send_streaming(self, prompt: str) -> AsyncGenerator[dict, None]:
        """Send a prompt to Gemini CLI and yield streaming events.

        Spawns a new gemini process per turn with --output-format stream-json.
        Uses --resume to continue the session if we have a previous session_id.

        Yields dicts:
        - {"type": "text", "content": "..."}  (assistant response chunks)
        - {"type": "tool_call", "tool": "...", "input": {...}}
        - {"type": "tool_result", "tool": "...", "status": "...", "output": "..."}
        - {"type": "init", "session_id": "...", "model": "..."}
        - {"type": "result", "status": "...", "stats": {...}}
        - {"type": "error", "content": "..."}
        """
        # Find gemini CLI
        gemini_path = _find_gemini()
        if not gemini_path:
            # Last resort: try npx
            npx_path = shutil.which("npx")
            if not npx_path:
                raise RuntimeError(
                    "Neither 'gemini' nor 'npx' found. "
                    "Install Gemini CLI: npm install -g @google/gemini-cli"
                )
            cmd = [npx_path, "-y", "@google/gemini-cli"]
        else:
            cmd = [gemini_path]

        # Output format — stream-json for JSONL events
        cmd.extend(["--output-format", "stream-json"])

        # Model selection
        if self.model:
            cmd.extend(["-m", self.model])

        # Approval mode (yolo = auto-approve all actions)
        if self.approval_mode:
            cmd.extend(["--approval-mode", self.approval_mode])

        # Sandbox
        if self.sandbox:
            cmd.append("--sandbox")

        # Resume session from previous call
        if self.session_id:
            cmd.extend(["--resume", self.session_id])

        # Prompt as -p flag
        cmd.extend(["-p", prompt])

        # Build environment — inherit current env, include GEMINI_API_KEY if set.
        # When absent, Gemini uses cached Google account login (subscription mode).
        env = dict(os.environ)
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if api_key:
            env["GEMINI_API_KEY"] = api_key

        logger.info(
            "Running Gemini CLI (cwd=%s, session=%s, model=%s)",
            self.cwd, self.session_id, self.model,
        )

        # Kill any lingering process from a previous concurrent call (BUG 6)
        if self._current_process and self._current_process.returncode is None:
            try:
                self._current_process.terminate()
                await asyncio.wait_for(self._current_process.wait(), timeout=5)
            except (asyncio.TimeoutError, ProcessLookupError):
                try:
                    self._current_process.kill()
                except ProcessLookupError:
                    pass
            self._current_process = None

        # Spawn process
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.cwd,
            env=env,
        )
        self._current_process = process

        try:
            accumulated_text: list[str] = []

            while process.stdout:
                try:
                    line = await asyncio.wait_for(
                        process.stdout.readline(),
                        timeout=600,  # 10 min max per line (BUG 8)
                    )
                except asyncio.TimeoutError:
                    logger.error("Gemini CLI stdout read timed out after 600s")
                    yield {"type": "error", "content": "Gemini CLI response timed out"}
                    break
                if not line:
                    break

                line_str = line.decode("utf-8", errors="replace").strip()
                if not line_str:
                    continue

                try:
                    event = json.loads(line_str)
                except json.JSONDecodeError:
                    logger.debug("Non-JSON line from Gemini: %s", line_str[:200])
                    continue

                event_type = event.get("type", "")

                if event_type == "init":
                    # Store session_id for resume on next turn
                    self.session_id = event.get("session_id")
                    yield {
                        "type": "init",
                        "session_id": self.session_id,
                        "model": event.get("model"),
                    }

                elif event_type == "message":
                    role = event.get("role", "")
                    content = event.get("content", "")
                    if role == "assistant" and content:
                        accumulated_text.append(content)
                        yield {"type": "text", "content": content}

                elif event_type == "tool_use":
                    yield {
                        "type": "tool_call",
                        "tool": event.get("name", "unknown"),
                        "input": event.get("parameters", {}),
                    }

                elif event_type == "tool_result":
                    yield {
                        "type": "tool_result",
                        "tool": event.get("name", "unknown"),
                        "status": event.get("status", ""),
                        "output": event.get("output", ""),
                    }

                elif event_type == "result":
                    yield {
                        "type": "result",
                        "status": event.get("status", ""),
                        "stats": event.get("stats", {}),
                    }

            # Wait for process to finish
            try:
                await asyncio.wait_for(process.wait(), timeout=30)
            except asyncio.TimeoutError:
                pass

            # Check for errors in stderr
            if process.returncode and process.returncode != 0:
                stderr_data = b""
                if process.stderr:
                    stderr_data = await process.stderr.read()
                stderr_text = stderr_data.decode("utf-8", errors="replace").strip()
                if stderr_text:
                    # Filter out npm deprecation warnings that mask real errors
                    clean_lines = [
                        line for line in stderr_text.splitlines()
                        if "npm warn deprecated" not in line.lower()
                    ]
                    clean_stderr = "\n".join(clean_lines).strip()
                    if not clean_stderr:
                        clean_stderr = "(No meaningful error output. Only npm warnings were found.)"

                    logger.warning(
                        "Gemini CLI stderr (rc=%d): %s",
                        process.returncode, clean_stderr[:500] or stderr_text[:200],
                    )
                    if not accumulated_text:
                        stderr_lower = clean_stderr.lower()
                        # Detect auth-specific errors and give clear guidance
                        if "auth method" in stderr_lower or "gemini_api_key" in stderr_lower or "google_genai" in stderr_lower:
                            error_msg = (
                                "**Gemini authentication required.**\n\n"
                                "Run this in your terminal to log in with your Google account (free tier):\n"
                                "```\ngemini\n```\n"
                                "Or set `GEMINI_API_KEY` in `~/.autoforge/.env` to use an API key instead."
                            )
                        elif "401" in clean_stderr or "403" in clean_stderr:
                            error_msg = (
                                "**Gemini auth expired or invalid.**\n\n"
                                "Re-authenticate by running `gemini` in a terminal, "
                                "or set a fresh `GEMINI_API_KEY` in `~/.autoforge/.env`."
                            )
                        elif "429" in clean_stderr or "quota" in stderr_lower or "rate" in stderr_lower:
                            error_msg = (
                                "**Gemini rate limit / quota exceeded.**\n\n"
                                "Wait a moment and try again. If this persists, your subscription "
                                "tier may need an upgrade or you may need to set `GEMINI_API_KEY`."
                            )
                        else:
                            error_msg = f"Gemini CLI error:\n{clean_stderr[:500]}"
                        yield {
                            "type": "error",
                            "content": error_msg,
                        }

        except asyncio.TimeoutError:
            logger.error("Gemini CLI process timed out")
            yield {"type": "error", "content": "Gemini CLI timed out"}
        finally:
            self._current_process = None
            if process.returncode is None:
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=5)
                except (asyncio.TimeoutError, ProcessLookupError):
                    try:
                        process.kill()
                    except ProcessLookupError:
                        pass
