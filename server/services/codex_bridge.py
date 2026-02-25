"""
Codex CLI Bridge
================

Drives OpenAI's Codex CLI via its MCP server mode (``codex mcp-server``).
Exposes two MCP tools:
- ``codex`` — start a new session (returns threadId)
- ``codex-reply`` — continue a session with existing threadId

Used by WorkspaceChatSession when provider == "codex".
"""

import asyncio
import json
import logging
import os
import shutil
from pathlib import Path
from typing import Any, AsyncGenerator, Optional

logger = logging.getLogger(__name__)


class CodexBridge:
    """
    Manages a Codex CLI process running as an MCP server over stdio.

    The bridge spawns ``codex mcp-server`` (or via npx),
    communicates via JSON-RPC 2.0 over stdin/stdout, and exposes a simple
    send() / close() interface for the workspace session.

    Thread semantics:
    - First call to send() uses the ``codex`` tool (starts a new thread)
    - Subsequent calls use ``codex-reply`` with the stored threadId
    - threadId is exposed as a property for persistence
    """

    def __init__(
        self,
        *,
        cwd: str,
        model: Optional[str] = None,
        sandbox: str = "workspace-write",
        approval_policy: str = "never",
    ):
        self.cwd = str(Path(cwd).resolve())
        self.model = model
        self.sandbox = sandbox
        self.approval_policy = approval_policy
        self.thread_id: Optional[str] = None

        self._process: Optional[asyncio.subprocess.Process] = None
        self._request_id: int = 0
        self._pending: dict[int, asyncio.Future] = {}
        self._reader_task: Optional[asyncio.Task] = None
        self._initialized: bool = False

    async def start(self) -> None:
        """Spawn the codex mcp-server subprocess and perform MCP initialize handshake."""
        if self._process is not None:
            return

        # Find codex CLI — prefer global install, fall back to npx
        codex_path = shutil.which("codex")
        if codex_path:
            cmd = [codex_path, "mcp-server"]
        else:
            npx_path = shutil.which("npx")
            if not npx_path:
                raise RuntimeError(
                    "Neither 'codex' nor 'npx' found on PATH. "
                    "Install Codex CLI: npm i -g @openai/codex"
                )
            cmd = [npx_path, "-y", "@openai/codex", "mcp-server"]

        # Build environment — inherit current env, optionally include OPENAI_API_KEY.
        # When the key is absent, Codex falls back to cached ChatGPT plan login
        # (subscription mode), matching Claude's subscription-vs-API-key pattern.
        env = dict(os.environ)
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if api_key:
            env["OPENAI_API_KEY"] = api_key

        logger.info("Starting Codex MCP server: %s (cwd=%s)", " ".join(cmd), self.cwd)

        self._process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.cwd,
            env=env,
        )

        # Start background reader task for stdout
        self._reader_task = asyncio.create_task(self._read_stdout())

        # MCP initialize handshake
        result = await self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "autoforge-workspace", "version": "1.0.0"},
        })
        logger.info("Codex MCP initialized: %s", result)

        # Send initialized notification (required by MCP protocol)
        await self._send_notification("notifications/initialized", {})
        self._initialized = True

    async def close(self) -> None:
        """Shut down the MCP server and kill the subprocess."""
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
            self._reader_task = None

        if self._process:
            try:
                if self._process.stdin:
                    self._process.stdin.close()
            except Exception:
                pass
            try:
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=5)
            except (asyncio.TimeoutError, ProcessLookupError):
                try:
                    self._process.kill()
                except ProcessLookupError:
                    pass
            self._process = None

        self._initialized = False
        # Resolve any pending futures with errors
        for fut in self._pending.values():
            if not fut.done():
                fut.set_exception(RuntimeError("Codex bridge closed"))
        self._pending.clear()

    async def send(self, prompt: str) -> str:
        """Send a prompt to Codex and return the response text.

        First call starts a new session; subsequent calls continue with threadId.
        """
        await self.start()

        if self.thread_id is None:
            # Start new session
            args: dict[str, Any] = {
                "prompt": prompt,
                "cwd": self.cwd,
                "sandbox": self.sandbox,
                "approval-policy": self.approval_policy,
            }
            if self.model:
                args["model"] = self.model

            result = await self._call_tool("codex", args)
        else:
            # Continue existing session
            result = await self._call_tool("codex-reply", {
                "threadId": self.thread_id,
                "prompt": prompt,
            })

        # Extract response from MCP tool result
        text, thread_id = self._parse_tool_result(result)
        if thread_id:
            self.thread_id = thread_id

        return text

    async def send_streaming(self, prompt: str) -> AsyncGenerator[dict, None]:
        """Send a prompt and yield streaming events.

        Codex MCP returns complete responses per tool call (not per-token streaming).
        We yield the full response as a single text event.

        Yields dicts:
        - {"type": "text", "content": "..."}
        """
        text = await self.send(prompt)
        yield {"type": "text", "content": text}

    # --- Internal MCP JSON-RPC plumbing ---

    async def _send_request(self, method: str, params: dict) -> dict:
        """Send a JSON-RPC request and wait for the response."""
        if not self._process or not self._process.stdin:
            raise RuntimeError("Codex MCP server not running")

        self._request_id += 1
        req_id = self._request_id

        message = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params,
        }

        future: asyncio.Future = asyncio.get_running_loop().create_future()
        self._pending[req_id] = future

        raw = json.dumps(message) + "\n"
        self._process.stdin.write(raw.encode())
        await self._process.stdin.drain()

        try:
            return await asyncio.wait_for(future, timeout=600)  # 10 min timeout
        except asyncio.TimeoutError:
            self._pending.pop(req_id, None)
            raise RuntimeError(f"Codex MCP request timed out: {method}")

    async def _send_notification(self, method: str, params: dict) -> None:
        """Send a JSON-RPC notification (no response expected)."""
        if not self._process or not self._process.stdin:
            return

        message = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }
        raw = json.dumps(message) + "\n"
        self._process.stdin.write(raw.encode())
        await self._process.stdin.drain()

    async def _call_tool(self, name: str, arguments: dict) -> dict:
        """Call an MCP tool and return the result."""
        return await self._send_request("tools/call", {
            "name": name,
            "arguments": arguments,
        })

    async def _read_stdout(self) -> None:
        """Background task: read JSON-RPC messages from stdout and dispatch."""
        try:
            while self._process and self._process.stdout:
                line = await self._process.stdout.readline()
                if not line:
                    break

                try:
                    msg = json.loads(line.decode().strip())
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue

                # JSON-RPC response (has "id")
                if "id" in msg:
                    req_id = msg["id"]
                    future = self._pending.pop(req_id, None)
                    if future and not future.done():
                        if "error" in msg:
                            future.set_exception(RuntimeError(
                                f"Codex MCP error: {msg['error'].get('message', str(msg['error']))}"
                            ))
                        else:
                            future.set_result(msg.get("result", {}))

                # JSON-RPC notification (no "id") — Codex event stream
                elif "method" in msg:
                    logger.debug("Codex notification: %s", msg.get("method"))

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("Codex stdout reader error: %s", e)
            # Fail all pending requests
            for fut in self._pending.values():
                if not fut.done():
                    fut.set_exception(RuntimeError(f"Codex reader died: {e}"))
            self._pending.clear()

    @staticmethod
    def _parse_tool_result(result: dict) -> tuple[str, Optional[str]]:
        """Extract text content and threadId from an MCP tool call result."""
        # structuredContent path (modern MCP clients)
        structured = (
            result.get("structuredContent")
            or result.get("structured_content")
            or {}
        )
        thread_id = structured.get("threadId")
        content = structured.get("content")

        # Fallback: content blocks array
        if content is None:
            blocks = result.get("content", [])
            if isinstance(blocks, list):
                texts = [
                    b.get("text", "")
                    for b in blocks
                    if isinstance(b, dict) and b.get("type") == "text"
                ]
                content = "\n".join(t for t in texts if t)

        return (content or ""), thread_id
