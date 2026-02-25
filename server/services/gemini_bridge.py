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
        gemini_path = shutil.which("gemini")
        use_npx = False
        if not gemini_path:
            npx_path = shutil.which("npx")
            if not npx_path:
                raise RuntimeError(
                    "Neither 'gemini' nor 'npx' found on PATH. "
                    "Install Gemini CLI: npm install -g @google/gemini-cli"
                )
            gemini_path = npx_path
            use_npx = True

        # Build command
        cmd: list[str] = []
        if use_npx:
            cmd = [gemini_path, "-y", "@google/gemini-cli"]
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

        # Spawn process
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.cwd,
            env=env,
        )
        self._current_process = process

        try:
            accumulated_text: list[str] = []

            while process.stdout:
                line = await process.stdout.readline()
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
                    logger.warning(
                        "Gemini CLI stderr (rc=%d): %s",
                        process.returncode, stderr_text[:500],
                    )
                    if not accumulated_text:
                        yield {
                            "type": "error",
                            "content": f"Gemini CLI error: {stderr_text[:500]}",
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
