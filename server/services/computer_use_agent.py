"""
Computer Use Agent
==================

Core agent class for the Computer Use Execution Engine.
Manages the Claude API agent loop with computer_20250124, text_editor_20250124,
and bash_20250124 tools. Executes tool calls and streams events to callbacks.

The agent loop:
  1. Send prompt to Claude with computer-use tools
  2. Receive response (may contain tool_use blocks)
  3. Execute each tool call (screenshot, click, type, bash, etc.)
  4. Append tool results to message history
  5. Repeat until stop_reason == "end_turn" (no more tool calls)
  6. Capture final output and advance to next step
"""

import asyncio
import base64
import logging
import os
import re
import subprocess
from typing import Awaitable, Callable, Literal

from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Environment configuration
COMPUTER_USE_DEFAULT_MODEL = os.getenv("COMPUTER_USE_DEFAULT_MODEL", "claude-opus-4-6")
COMPUTER_USE_DISPLAY_WIDTH = int(os.getenv("COMPUTER_USE_DISPLAY_WIDTH", "1920"))
COMPUTER_USE_DISPLAY_HEIGHT = int(os.getenv("COMPUTER_USE_DISPLAY_HEIGHT", "1080"))

# Maximum tool call iterations per step to prevent infinite loops
MAX_ITERATIONS = 100

# Maximum tokens per API response
MAX_TOKENS = 8192

# Sensitive data patterns (from process_manager.py)
SENSITIVE_PATTERNS = [
    r"sk-[a-zA-Z0-9]{20,}",
    r"ANTHROPIC_API_KEY=[^\s]+",
    r"api[_-]?key[=:][^\s]+",
    r"token[=:][^\s]+",
    r"password[=:][^\s]+",
    r"secret[=:][^\s]+",
]


def _sanitize(text: str) -> str:
    """Remove sensitive information from text before streaming."""
    for pattern in SENSITIVE_PATTERNS:
        text = re.sub(pattern, "[REDACTED]", text, flags=re.IGNORECASE)
    return text


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class StepConfig(BaseModel):
    """Configuration for a single step to execute."""

    step_id: str
    prompt: str
    model: str = COMPUTER_USE_DEFAULT_MODEL
    role_system_prompt: str = ""
    previous_outputs: list[str] = []


class StepResult(BaseModel):
    """Result of executing a single step."""

    step_id: str
    ai_output: str
    screenshots: list[str] = []  # base64-encoded PNGs
    status: Literal["completed", "error", "paused"] = "completed"
    error_message: str = ""


class ExecutionEvent(BaseModel):
    """Event emitted during execution, streamed via WebSocket."""

    type: Literal[
        "status", "screenshot", "step_progress", "agent_message", "error"
    ]
    session_id: str
    data: dict


# ---------------------------------------------------------------------------
# Computer Use Agent
# ---------------------------------------------------------------------------


class ComputerUseAgent:
    """
    Manages a single computer-use agent execution session.

    Loops Claude API calls with computer_20250124, text_editor_20250124,
    and bash_20250124 tools. Executes tool calls and streams events to
    registered callbacks.
    """

    def __init__(self, session_id: str, model: str = COMPUTER_USE_DEFAULT_MODEL):
        self.session_id = session_id
        self.model = model
        self.messages: list[dict] = []
        self.paused = False
        self.stopped = False
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # Not paused initially
        self._callbacks: list[Callable[[ExecutionEvent], Awaitable[None]]] = []
        self._client = None

        # Tool definitions for Claude's Computer Use API
        self.tools = [
            {
                "type": "computer_20250124",
                "name": "computer",
                "display_width_px": COMPUTER_USE_DISPLAY_WIDTH,
                "display_height_px": COMPUTER_USE_DISPLAY_HEIGHT,
                "display_number": 0,
            },
            {
                "type": "text_editor_20250124",
                "name": "str_replace_editor",
            },
            {
                "type": "bash_20250124",
                "name": "bash",
            },
        ]

    def _get_client(self):
        """Lazily initialize the Anthropic client."""
        if self._client is None:
            try:
                import anthropic

                self._client = anthropic.Anthropic()
            except ImportError:
                raise RuntimeError(
                    "anthropic package not installed. Install with: pip install anthropic"
                )
        return self._client

    def on_event(self, callback: Callable[[ExecutionEvent], Awaitable[None]]) -> None:
        """Register a callback for execution events."""
        self._callbacks.append(callback)

    async def _emit(self, event: ExecutionEvent) -> None:
        """Emit an event to all registered callbacks."""
        for callback in self._callbacks:
            try:
                await callback(event)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")

    async def execute_step(
        self,
        step_prompt: str,
        context: str = "",
        role_system_prompt: str = "",
    ) -> StepResult:
        """Execute a single strategy step using computer-use tools."""
        client = self._get_client()

        # Build the full prompt with context
        parts = []
        if context:
            parts.append(context)
        parts.append(step_prompt)
        full_prompt = "\n\n".join(parts)

        # Reset messages for this step
        self.messages = [{"role": "user", "content": full_prompt}]

        # Build system prompt
        system_prompt = role_system_prompt or ""

        screenshots: list[str] = []
        iterations = 0

        await self._emit(
            ExecutionEvent(
                type="status",
                session_id=self.session_id,
                data={"status": "running", "message": "Starting step execution"},
            )
        )

        try:
            while iterations < MAX_ITERATIONS:
                # Check for stop
                if self.stopped:
                    return StepResult(
                        step_id="",
                        ai_output="Execution stopped by user.",
                        screenshots=screenshots,
                        status="paused",
                    )

                # Check for pause (wait until resumed)
                if self.paused:
                    await self._emit(
                        ExecutionEvent(
                            type="status",
                            session_id=self.session_id,
                            data={"status": "paused"},
                        )
                    )
                    await self._pause_event.wait()
                    if self.stopped:
                        return StepResult(
                            step_id="",
                            ai_output="Execution stopped while paused.",
                            screenshots=screenshots,
                            status="paused",
                        )

                iterations += 1

                # Call Claude API
                api_kwargs: dict = {
                    "model": self.model,
                    "max_tokens": MAX_TOKENS,
                    "tools": self.tools,
                    "messages": self.messages,
                }
                if system_prompt:
                    api_kwargs["system"] = system_prompt

                response = await asyncio.to_thread(
                    client.messages.create, **api_kwargs
                )

                # Append assistant response to history
                self.messages.append(
                    {"role": "assistant", "content": response.content}
                )

                # Extract text output from response
                text_output = self._extract_text(response)
                if text_output:
                    await self._emit(
                        ExecutionEvent(
                            type="agent_message",
                            session_id=self.session_id,
                            data={"text": _sanitize(text_output)},
                        )
                    )

                # Check if agent is done (no more tool calls)
                if response.stop_reason == "end_turn":
                    final_output = self._extract_all_text(response)
                    return StepResult(
                        step_id="",
                        ai_output=final_output,
                        screenshots=screenshots,
                        status="completed",
                    )

                # Execute tool calls
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = await self._execute_tool(block)
                        tool_results.append(result)

                        # Capture screenshots from tool results
                        if block.name == "computer" and hasattr(block, "input"):
                            action = block.input.get("action", "")
                            if action == "screenshot":
                                for tr in tool_results:
                                    if isinstance(tr.get("content"), list):
                                        for item in tr["content"]:
                                            if (
                                                isinstance(item, dict)
                                                and item.get("type") == "image"
                                            ):
                                                b64 = item.get("source", {}).get(
                                                    "data", ""
                                                )
                                                if b64:
                                                    screenshots.append(b64)
                                                    await self._emit(
                                                        ExecutionEvent(
                                                            type="screenshot",
                                                            session_id=self.session_id,
                                                            data={
                                                                "screenshot": b64[:100]
                                                                + "...",
                                                                "total": len(
                                                                    screenshots
                                                                ),
                                                            },
                                                        )
                                                    )

                if not tool_results:
                    # No tool calls and not end_turn — shouldn't happen, but break
                    break

                # Append tool results to message history
                self.messages.append({"role": "user", "content": tool_results})

            # Hit max iterations
            return StepResult(
                step_id="",
                ai_output=f"Step reached maximum iterations ({MAX_ITERATIONS}).",
                screenshots=screenshots,
                status="error",
                error_message=f"Max iterations ({MAX_ITERATIONS}) exceeded",
            )

        except Exception as e:
            error_msg = f"Agent error: {_sanitize(str(e))}"
            logger.error(f"Step execution error for session {self.session_id}: {e}")
            await self._emit(
                ExecutionEvent(
                    type="error",
                    session_id=self.session_id,
                    data={"error": error_msg},
                )
            )
            return StepResult(
                step_id="",
                ai_output="",
                screenshots=screenshots,
                status="error",
                error_message=error_msg,
            )

    async def execute_steps(self, steps: list[StepConfig]) -> list[StepResult]:
        """Execute multiple steps sequentially, passing context forward."""
        results: list[StepResult] = []
        previous_outputs: list[str] = []

        for i, step in enumerate(steps):
            if self.stopped:
                break

            await self._emit(
                ExecutionEvent(
                    type="step_progress",
                    session_id=self.session_id,
                    data={
                        "current_step": i + 1,
                        "total_steps": len(steps),
                        "step_id": step.step_id,
                    },
                )
            )

            # Build context from previous outputs
            context_parts = list(step.previous_outputs) + previous_outputs
            context = ""
            if context_parts:
                context = "Previous step results:\n" + "\n---\n".join(context_parts)

            result = await self.execute_step(
                step_prompt=step.prompt,
                context=context,
                role_system_prompt=step.role_system_prompt,
            )
            result.step_id = step.step_id
            results.append(result)

            if result.status == "completed" and result.ai_output:
                previous_outputs.append(result.ai_output)

            if result.status == "error":
                logger.warning(
                    f"Step {step.step_id} failed: {result.error_message}. "
                    "Continuing to next step."
                )

        return results

    async def pause(self) -> None:
        """Pause execution after the current tool call completes."""
        self.paused = True
        self._pause_event.clear()
        logger.info(f"Session {self.session_id} paused")

    async def resume(self) -> None:
        """Resume from paused state."""
        self.paused = False
        self._pause_event.set()
        logger.info(f"Session {self.session_id} resumed")
        await self._emit(
            ExecutionEvent(
                type="status",
                session_id=self.session_id,
                data={"status": "running", "message": "Resumed"},
            )
        )

    async def inject_message(self, message: str) -> None:
        """Inject a human message into the conversation between tool calls."""
        sanitized = _sanitize(message)
        self.messages.append(
            {"role": "user", "content": f"[HUMAN MESSAGE]: {sanitized}"}
        )
        logger.info(f"Message injected into session {self.session_id}")
        await self._emit(
            ExecutionEvent(
                type="agent_message",
                session_id=self.session_id,
                data={"text": f"[Human]: {sanitized}", "injected": True},
            )
        )

    async def stop(self) -> None:
        """Stop execution entirely."""
        self.stopped = True
        self.paused = False
        self._pause_event.set()  # Unblock if paused
        logger.info(f"Session {self.session_id} stopped")
        await self._emit(
            ExecutionEvent(
                type="status",
                session_id=self.session_id,
                data={"status": "stopped"},
            )
        )

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    async def _execute_tool(self, tool_block) -> dict:
        """Execute a single tool call and return the result for the API.

        Returns a tool_result dict with 'content' that is either:
        - str: for text results (editor, bash)
        - list[dict]: for image results (computer screenshot)
        Both formats are accepted by the Anthropic Messages API.
        """
        tool_name = tool_block.name
        tool_input = tool_block.input if hasattr(tool_block, "input") else {}

        logger.debug(
            f"Executing tool: {tool_name}, "
            f"action={tool_input.get('action', 'N/A')}"
        )

        try:
            content: str | list
            if tool_name == "computer":
                content = await self._handle_computer_tool(tool_input)
            elif tool_name == "str_replace_editor":
                content = await self._handle_editor_tool(tool_input)
            elif tool_name == "bash":
                content = await self._handle_bash_tool(tool_input)
            else:
                return {
                    "type": "tool_result",
                    "tool_use_id": tool_block.id,
                    "content": f"Unknown tool: {tool_name}",
                    "is_error": True,
                }

            return {
                "type": "tool_result",
                "tool_use_id": tool_block.id,
                "content": content,
            }

        except Exception as e:
            error_msg = _sanitize(str(e))
            logger.error(f"Tool execution error ({tool_name}): {error_msg}")
            return {
                "type": "tool_result",
                "tool_use_id": tool_block.id,
                "content": f"Error: {error_msg}",
                "is_error": True,
            }

    async def _handle_computer_tool(self, tool_input: dict) -> list | str:
        """Handle computer tool actions (screenshot, click, type, etc.)."""
        action = tool_input.get("action", "")

        if action == "screenshot":
            # Capture screenshot from the X11 display
            screenshot_b64 = await self._capture_screenshot()
            if screenshot_b64:
                return [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": screenshot_b64,
                        },
                    }
                ]
            return "Screenshot capture failed"

        elif action == "mouse_move":
            x = tool_input.get("coordinate", [0, 0])
            await self._run_xdotool(f"mousemove {x[0]} {x[1]}")
            return "Mouse moved"

        elif action == "left_click":
            x = tool_input.get("coordinate", [0, 0])
            await self._run_xdotool(f"mousemove {x[0]} {x[1]} click 1")
            return "Left clicked"

        elif action == "right_click":
            x = tool_input.get("coordinate", [0, 0])
            await self._run_xdotool(f"mousemove {x[0]} {x[1]} click 3")
            return "Right clicked"

        elif action == "double_click":
            x = tool_input.get("coordinate", [0, 0])
            await self._run_xdotool(
                f"mousemove {x[0]} {x[1]} click --repeat 2 --delay 100 1"
            )
            return "Double clicked"

        elif action == "left_click_drag":
            start = tool_input.get("start_coordinate", [0, 0])
            end = tool_input.get("coordinate", [0, 0])
            await self._run_xdotool(
                f"mousemove {start[0]} {start[1]} mousedown 1 "
                f"mousemove {end[0]} {end[1]} mouseup 1"
            )
            return "Drag completed"

        elif action == "type":
            text = tool_input.get("text", "")
            # Use xdotool to type text
            await self._run_xdotool(f"type --clearmodifiers -- {text!r}")
            return "Text typed"

        elif action == "key":
            key = tool_input.get("text", "")
            await self._run_xdotool(f"key -- {key}")
            return f"Key pressed: {key}"

        elif action == "scroll":
            x = tool_input.get("coordinate", [0, 0])
            direction = tool_input.get("direction", "down")
            amount = tool_input.get("amount", 3)
            button = 5 if direction == "down" else 4
            await self._run_xdotool(
                f"mousemove {x[0]} {x[1]} click --repeat {amount} {button}"
            )
            return f"Scrolled {direction}"

        elif action == "wait":
            duration = tool_input.get("duration", 1)
            await asyncio.sleep(min(duration, 10))  # Cap at 10 seconds
            return f"Waited {duration}s"

        elif action == "triple_click":
            x = tool_input.get("coordinate", [0, 0])
            await self._run_xdotool(
                f"mousemove {x[0]} {x[1]} click --repeat 3 --delay 100 1"
            )
            return "Triple clicked"

        else:
            return f"Unknown computer action: {action}"

    async def _handle_editor_tool(self, tool_input: dict) -> str:
        """Handle text editor tool (file operations)."""
        command = tool_input.get("command", "")
        path = tool_input.get("path", "")

        if command == "view":
            try:
                result = await asyncio.to_thread(self._read_file, path)
                return _sanitize(result)
            except Exception as e:
                return f"Error reading file: {e}"

        elif command == "create":
            file_text = tool_input.get("file_text", "")
            try:
                await asyncio.to_thread(self._write_file, path, file_text)
                return f"File created: {path}"
            except Exception as e:
                return f"Error creating file: {e}"

        elif command == "str_replace":
            old_str = tool_input.get("old_str", "")
            new_str = tool_input.get("new_str", "")
            try:
                content = await asyncio.to_thread(self._read_file, path)
                if old_str not in content:
                    return f"Error: old_str not found in {path}"
                updated = content.replace(old_str, new_str, 1)
                await asyncio.to_thread(self._write_file, path, updated)
                return f"File updated: {path}"
            except Exception as e:
                return f"Error updating file: {e}"

        elif command == "insert":
            insert_line = tool_input.get("insert_line", 0)
            new_str = tool_input.get("new_str", "")
            try:
                content = await asyncio.to_thread(self._read_file, path)
                lines = content.split("\n")
                lines.insert(insert_line, new_str)
                await asyncio.to_thread(self._write_file, path, "\n".join(lines))
                return f"Text inserted at line {insert_line} in {path}"
            except Exception as e:
                return f"Error inserting text: {e}"

        return f"Unknown editor command: {command}"

    async def _handle_bash_tool(self, tool_input: dict) -> str:
        """Handle bash tool (command execution).

        Security note: shell=True is required because the Computer Use API sends
        full shell commands (with pipes, redirects, etc.). Security is provided by
        Docker container isolation — commands run inside the ephemeral container,
        not on the host.
        """
        command = tool_input.get("command", "")
        if not command:
            return "No command provided"

        try:
            result = await asyncio.to_thread(
                subprocess.run,
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120,
                env={**os.environ, "DISPLAY": ":0"},
            )
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR:\n{result.stderr}"
            if result.returncode != 0:
                output += f"\n(exit code: {result.returncode})"
            return _sanitize(output[:10000])  # Truncate long output
        except subprocess.TimeoutExpired:
            return "Command timed out (120s limit)"
        except Exception as e:
            return f"Command error: {_sanitize(str(e))}"

    async def _capture_screenshot(self) -> str:
        """Capture a screenshot of the virtual display. Returns base64 PNG."""
        try:
            # Ensure display is active
            await asyncio.to_thread(
                subprocess.run,
                ["xdotool", "getactivewindow"],
                capture_output=True,
                text=True,
                timeout=5,
                env={**os.environ, "DISPLAY": ":0"},
            )

            # Use import (ImageMagick) for screenshot capture
            import_result = await asyncio.to_thread(
                subprocess.run,
                ["import", "-window", "root", "png:-"],
                capture_output=True,
                timeout=10,
                env={**os.environ, "DISPLAY": ":0"},
            )

            if import_result.returncode == 0 and import_result.stdout:
                return base64.b64encode(import_result.stdout).decode("utf-8")

            # Fallback: use xdotool + xwd + convert
            return ""
        except Exception as e:
            logger.debug(f"Screenshot capture failed: {e}")
            return ""

    async def _run_xdotool(self, args: str) -> None:
        """Run an xdotool command."""
        await asyncio.to_thread(
            subprocess.run,
            f"xdotool {args}",
            shell=True,
            capture_output=True,
            timeout=10,
            env={**os.environ, "DISPLAY": ":0"},
        )

    @staticmethod
    def _read_file(path: str) -> str:
        with open(path, encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def _write_file(path: str, content: str) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    @staticmethod
    def _extract_text(response) -> str:
        """Extract text blocks from a Claude API response."""
        parts = []
        for block in response.content:
            if hasattr(block, "text"):
                parts.append(block.text)
        return "\n".join(parts)

    @staticmethod
    def _extract_all_text(response) -> str:
        """Extract all text from the final response."""
        parts = []
        for block in response.content:
            if hasattr(block, "text"):
                parts.append(block.text)
        return "\n".join(parts)
