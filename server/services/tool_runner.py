"""Tool Runner — Hybrid Execution Engine for YT Lab tool chains.

Executes chain steps using the right method per step type:
- generation/research → Claude SDK (subscription auth)
- api_call/webhook    → direct HTTP adapter
- file_create         → AI generates content → writes to disk
- browser_action      → computer use (future) or Playwright
- manual              → pause and wait for human approval

Architecture follows the Stripe Blueprint Pattern:
  ROBOT steps = deterministic (template resolution, variable substitution)
  AGENT steps = creative (Claude SDK calls for generation/research)
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import tempfile
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING, AsyncGenerator, Optional

if TYPE_CHECKING:
    from ..models.tool_factory import (
        ChainConfigRow,
        GeneratedTool,
        RunConfig,
        StepResult,
        ToolRunState,
    )

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory run registry (run_id → ToolRunState)
# ---------------------------------------------------------------------------
_active_runs: dict[str, "ToolRunState"] = {}


def get_run(run_id: str) -> Optional["ToolRunState"]:
    return _active_runs.get(run_id)


def get_runs_for_tool(tool_id: str) -> list["ToolRunState"]:
    return [r for r in _active_runs.values() if r.tool_id == tool_id]


def _store_run(state: "ToolRunState") -> None:
    _active_runs[state.run_id] = state


def cancel_run(run_id: str) -> bool:
    state = _active_runs.get(run_id)
    if state and state.status in ("running", "paused"):
        from ..models.tool_factory import RunStatus
        state.status = RunStatus.CANCELLED
        return True
    return False


# ---------------------------------------------------------------------------
# ToolRunner
# ---------------------------------------------------------------------------

class ToolRunner:
    """Orchestrates step-by-step execution of a blueprint's chain config.

    Usage:
        runner = ToolRunner(tool, config)
        async for event in runner.run():
            # event is a dict with keys: type, step_number, data, ...
            yield event
    """

    SDK_TIMEOUT_SECONDS = 300

    def __init__(self, tool: "GeneratedTool", config: "RunConfig") -> None:
        from ..models.tool_factory import RunStatus, ToolRunState

        self.tool = tool
        self.config = config
        self.blueprint = tool.blueprint

        self.state = ToolRunState(
            run_id=config.run_id,
            tool_id=config.tool_id,
            tool_name=tool.blueprint.tool_name,
            config=config,
            status=RunStatus.IDLE,
            total_steps=len(self.blueprint.chain_config),
        )
        _store_run(self.state)

        # Resolved variables dict (user-supplied + will hold previousOutput)
        self._vars: dict[str, str] = dict(config.variables)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def run(self) -> AsyncGenerator[dict, None]:
        """Stream execution events for the entire chain.

        Yields dicts:
          {"type": "run_started",   "run_id": ..., "tool_name": ..., "total_steps": ...}
          {"type": "step_started",  "step_number": ..., "title": ..., "execution_mode": ...}
          {"type": "log",           "step_number": ..., "message": ...}
          {"type": "step_done",     "step_number": ..., "result": StepResult.dict()}
          {"type": "step_error",    "step_number": ..., "error": ...}
          {"type": "checkpoint",    "step_number": ..., "title": ..., "message": ...}
          {"type": "run_done",      "run_id": ..., "total_tokens": ..., "duration": ...}
          {"type": "run_error",     "run_id": ..., "error": ...}
        """
        from ..models.tool_factory import RunStatus, StepResult, StepStatus

        run_start = time.time()
        self.state.status = RunStatus.RUNNING
        self.state.started_at = datetime.now(timezone.utc).isoformat()

        yield {
            "type": "run_started",
            "run_id": self.config.run_id,
            "tool_name": self.blueprint.tool_name,
            "total_steps": self.state.total_steps,
        }

        try:
            for step in self.blueprint.chain_config:
                # Range checks
                if step.row_number < self.config.start_from_step:
                    continue
                if self.config.stop_after_step and step.row_number > self.config.stop_after_step:
                    break
                if self.state.status == RunStatus.CANCELLED:
                    break

                self.state.current_step = step.row_number

                yield {
                    "type": "step_started",
                    "step_number": step.row_number,
                    "title": step.title,
                    "step_type": step.step_type.value,
                    "execution_mode": step.execution_mode.value,
                }

                # Resolve variables in the prompt template
                resolved_prompt = self._resolve_template(step.prompt_template)

                step_result: StepResult | None = None

                async for event in self._execute_step(step, resolved_prompt):
                    if event.get("type") == "_result":
                        step_result = event["result"]
                    else:
                        yield event

                if step_result is None:
                    # Should not happen — _execute_step always yields _result
                    step_result = StepResult(
                        step_number=step.row_number,
                        title=step.title,
                        step_type=step.step_type,
                        execution_mode=step.execution_mode,
                        status=StepStatus.ERROR,
                        error="No result produced",
                    )

                self.state.step_results.append(step_result)
                self.state.total_tokens += step_result.tokens_used

                if step_result.status == StepStatus.ERROR:
                    yield {
                        "type": "step_error",
                        "step_number": step.row_number,
                        "error": step_result.error,
                        "result": step_result.model_dump(),
                    }
                    # Non-fatal — continue to next step unless it's a gate
                    if step.is_gate:
                        break
                elif step_result.status == StepStatus.WAITING:
                    # Human checkpoint — pause the run
                    self.state.status = RunStatus.PAUSED
                    yield {
                        "type": "checkpoint",
                        "step_number": step.row_number,
                        "title": step.title,
                        "message": f"Waiting for your review: {step.title}",
                        "output_so_far": step_result.output,
                    }
                    # Caller must resume by calling run() again with start_from_step+1
                    break
                else:
                    # Store output as {{previousOutput}} for next step
                    self._vars["previousOutput"] = step_result.output
                    yield {
                        "type": "step_done",
                        "step_number": step.row_number,
                        "result": step_result.model_dump(),
                    }

                # Fire webhook if configured on this step
                if step.webhook_url and step_result.status == StepStatus.DONE:
                    try:
                        await self._fire_webhook(step.webhook_url, step_result)
                        yield {
                            "type": "log",
                            "step_number": step.row_number,
                            "message": f"✅ Webhook fired: {step.webhook_url}",
                        }
                    except Exception as wh_err:
                        yield {
                            "type": "log",
                            "step_number": step.row_number,
                            "message": f"⚠️ Webhook failed: {wh_err}",
                        }

        except Exception as run_err:
            from ..models.tool_factory import RunStatus
            self.state.status = RunStatus.ERROR
            self.state.error = str(run_err)
            self.state.completed_at = datetime.now(timezone.utc).isoformat()
            yield {"type": "run_error", "run_id": self.config.run_id, "error": str(run_err)}
            return

        duration = time.time() - run_start
        if self.state.status == RunStatus.RUNNING:
            self.state.status = RunStatus.DONE
        self.state.completed_at = datetime.now(timezone.utc).isoformat()

        yield {
            "type": "run_done",
            "run_id": self.config.run_id,
            "status": self.state.status.value,
            "total_tokens": self.state.total_tokens,
            "duration": round(duration, 2),
            "steps_completed": len([r for r in self.state.step_results if r.status == "done"]),
        }

    # ------------------------------------------------------------------
    # Step dispatcher
    # ------------------------------------------------------------------

    async def _execute_step(
        self,
        step: "ChainConfigRow",
        resolved_prompt: str,
    ) -> AsyncGenerator[dict, None]:
        from ..models.tool_factory import ExecutionMode, StepResult, StepStatus

        started_at = datetime.now(timezone.utc).isoformat()
        t0 = time.time()

        def _log(msg: str) -> dict:
            return {"type": "log", "step_number": step.row_number, "message": msg}

        mode = step.execution_mode

        try:
            if mode == ExecutionMode.AI_ONLY:
                output = ""
                tokens = 0
                async for event in self._execute_ai(step, resolved_prompt):
                    if event.get("type") == "_ai_result":
                        output = event["text"]
                        tokens = event.get("tokens", 0)
                    else:
                        yield event
                result = StepResult(
                    step_number=step.row_number,
                    title=step.title,
                    step_type=step.step_type,
                    execution_mode=mode,
                    status=StepStatus.DONE,
                    output=output,
                    tokens_used=tokens,
                    duration_seconds=round(time.time() - t0, 2),
                    started_at=started_at,
                    completed_at=datetime.now(timezone.utc).isoformat(),
                )

            elif mode == ExecutionMode.AI_THEN_ACT:
                # Phase 1: AI generates content
                ai_output = ""
                tokens = 0
                async for event in self._execute_ai(step, resolved_prompt):
                    if event.get("type") == "_ai_result":
                        ai_output = event["text"]
                        tokens = event.get("tokens", 0)
                    else:
                        yield event

                # Phase 2: action handler (Phase 2 of PRD — currently returns AI output)
                yield _log(f"🔧 Action phase: {step.step_type.value} — executing post-AI action")
                action_result = await self._execute_action(step, ai_output)

                result = StepResult(
                    step_number=step.row_number,
                    title=step.title,
                    step_type=step.step_type,
                    execution_mode=mode,
                    status=StepStatus.DONE,
                    output=ai_output,
                    action_result=action_result,
                    tokens_used=tokens,
                    duration_seconds=round(time.time() - t0, 2),
                    started_at=started_at,
                    completed_at=datetime.now(timezone.utc).isoformat(),
                )

            elif mode == ExecutionMode.DIRECT_ACTION:
                yield _log(f"⚡ Direct action: {step.step_type.value}")
                action_result = await self._execute_action(step, resolved_prompt)
                output = action_result.get("output", resolved_prompt)
                result = StepResult(
                    step_number=step.row_number,
                    title=step.title,
                    step_type=step.step_type,
                    execution_mode=mode,
                    status=StepStatus.DONE,
                    output=output,
                    action_result=action_result,
                    duration_seconds=round(time.time() - t0, 2),
                    started_at=started_at,
                    completed_at=datetime.now(timezone.utc).isoformat(),
                )

            elif mode == ExecutionMode.HUMAN_CHECKPOINT:
                yield _log(f"⏸️ Human checkpoint: {step.title} — pausing for review")
                result = StepResult(
                    step_number=step.row_number,
                    title=step.title,
                    step_type=step.step_type,
                    execution_mode=mode,
                    status=StepStatus.WAITING,
                    output=resolved_prompt,
                    duration_seconds=round(time.time() - t0, 2),
                    started_at=started_at,
                )

            elif mode == ExecutionMode.COMPUTER_USE:
                # Phase 3 placeholder — fall back to AI_ONLY for now
                yield _log("🖥️ Computer use requested — falling back to AI description (browser automation in Phase 3)")
                output = ""
                tokens = 0
                async for event in self._execute_ai(step, resolved_prompt):
                    if event.get("type") == "_ai_result":
                        output = event["text"]
                        tokens = event.get("tokens", 0)
                    else:
                        yield event
                result = StepResult(
                    step_number=step.row_number,
                    title=step.title,
                    step_type=step.step_type,
                    execution_mode=mode,
                    status=StepStatus.DONE,
                    output=output,
                    tokens_used=tokens,
                    duration_seconds=round(time.time() - t0, 2),
                    started_at=started_at,
                    completed_at=datetime.now(timezone.utc).isoformat(),
                )

            else:
                # Unknown mode — AI fallback
                yield _log(f"❓ Unknown execution mode '{mode}' — falling back to AI")
                output = ""
                tokens = 0
                async for event in self._execute_ai(step, resolved_prompt):
                    if event.get("type") == "_ai_result":
                        output = event["text"]
                        tokens = event.get("tokens", 0)
                    else:
                        yield event
                result = StepResult(
                    step_number=step.row_number,
                    title=step.title,
                    step_type=step.step_type,
                    execution_mode=mode,
                    status=StepStatus.DONE,
                    output=output,
                    tokens_used=tokens,
                    duration_seconds=round(time.time() - t0, 2),
                    started_at=started_at,
                    completed_at=datetime.now(timezone.utc).isoformat(),
                )

        except Exception as exc:
            result = StepResult(
                step_number=step.row_number,
                title=step.title,
                step_type=step.step_type,
                execution_mode=mode,
                status=StepStatus.ERROR,
                error=str(exc),
                duration_seconds=round(time.time() - t0, 2),
                started_at=started_at,
                completed_at=datetime.now(timezone.utc).isoformat(),
            )

        yield {"type": "_result", "result": result}

    # ------------------------------------------------------------------
    # AI execution (Claude SDK — subscription auth)
    # ------------------------------------------------------------------

    async def _execute_ai(
        self,
        step: "ChainConfigRow",
        resolved_prompt: str,
    ) -> AsyncGenerator[dict, None]:
        """Call Claude via the Agent SDK using subscription auth.

        Copied from yt_processor._call_via_sdk() — the ONLY working pattern.
        """
        from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

        from registry import get_effective_sdk_env

        step_num = step.row_number

        def _log(msg: str) -> dict:
            return {"type": "log", "step_number": step_num, "message": msg}

        os.environ.pop("CLAUDECODE", None)

        system_cli = shutil.which("claude")
        if not system_cli:
            raise RuntimeError("Claude CLI not found on PATH")

        sdk_env = get_effective_sdk_env(force_subscription=True)
        sdk_env.pop("CLAUDECODE", None)

        # Model mapping
        model_map = {
            "sonnet": "claude-sonnet-4-6",
            "opus": "claude-opus-4-6",
            "haiku": "claude-haiku-4-5-20251001",
        }
        model = model_map.get(step.model_recommendation, "claude-sonnet-4-6")
        if step.model_recommendation not in model_map:
            model = step.model_recommendation  # passed as full model ID

        import pathlib

        scratch = tempfile.mkdtemp(prefix="tool_runner_")
        settings_file = pathlib.Path(scratch) / ".claude-runner-settings.json"
        settings_file.write_text(json.dumps({
            "permissions": {
                "defaultMode": "acceptEdits",
                "allow": [],
            },
        }))

        system_prompt = (
            f"You are executing step {step_num} of the '{self.blueprint.tool_name}' tool chain. "
            f"Step type: {step.step_type.value}. Expected output: {step.expected_output}. "
            "Be precise, complete, and production-ready. Output ONLY the requested content — "
            "no meta-commentary or explanations unless the step specifically asks for it."
        )

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

        yield _log(f"🤖 Step {step_num}: calling {model}...")

        t0 = time.time()
        full_text = ""
        tokens_used = 0

        try:
            await client.__aenter__()
            await client.query(resolved_prompt)

            full_text = ""
            rate_limit_count = 0
            last_heartbeat = time.time()

            try:
                async for msg in client.receive_response():
                    now = time.time()
                    elapsed = now - t0
                    msg_type = type(msg).__name__

                    if now - last_heartbeat >= 15:
                        yield _log(f"[SDK] Step {step_num}: {elapsed:.0f}s elapsed | {len(full_text):,} chars")
                        last_heartbeat = now

                    if msg_type in ("RateLimitEvent", "rate_limit_event"):
                        rate_limit_count += 1
                        yield _log(f"⚠️ Rate limit #{rate_limit_count} at {elapsed:.0f}s — retrying...")
                        continue

                    elif msg_type == "AssistantMessage" and hasattr(msg, "content"):
                        for block in msg.content:
                            if type(block).__name__ == "TextBlock" and hasattr(block, "text"):
                                full_text += block.text

                    elif msg_type == "ResultMessage":
                        if getattr(msg, "is_error", False):
                            err_text = str(getattr(msg, "result", "SDK error"))
                            raise RuntimeError(f"Claude returned error: {err_text}")
                        else:
                            yield _log(f"✅ Step {step_num} done: {len(full_text):,} chars in {time.time() - t0:.1f}s")

            except Exception as stream_exc:
                exc_str = str(stream_exc)
                if full_text.strip() and "unknown message type" in exc_str.lower():
                    yield _log(f"✅ Recovered after rate_limit_event exception: {len(full_text):,} chars")
                elif full_text.strip():
                    yield _log(f"⚠️ Stream exception but have {len(full_text):,} chars — using collected text")
                else:
                    raise

        finally:
            try:
                await client.__aexit__(None, None, None)
            except Exception:
                pass
            shutil.rmtree(scratch, ignore_errors=True)

        if not full_text.strip():
            raise RuntimeError(f"Step {step_num}: Claude returned empty response")

        yield {"type": "_ai_result", "text": full_text.strip(), "tokens": tokens_used}

    # ------------------------------------------------------------------
    # Action handler (Phase 2 stub — calls api_adapters)
    # ------------------------------------------------------------------

    async def _execute_action(self, step: "ChainConfigRow", content: str) -> dict:
        """Route to the appropriate API adapter based on step type and detected APIs."""
        from ..models.tool_factory import StepType
        from .api_adapters.base import get_adapter

        step_type = step.step_type

        if step_type == StepType.WEBHOOK:
            if step.webhook_url:
                from .api_adapters.webhook import WebhookAdapter
                adapter = WebhookAdapter(webhook_url=step.webhook_url)
                return await adapter.execute("post", {"content": content, "step": step.title})
            return {"output": content, "note": "No webhook_url configured"}

        if step_type == StepType.FILE_CREATE:
            from .api_adapters.file_creator import FileCreatorAdapter
            adapter = FileCreatorAdapter(variables=self._vars)
            return await adapter.execute("create", {
                "content": content,
                "expected_output": step.expected_output,
                "title": step.title,
            })

        # For API_CALL steps, try to route to a known adapter
        for api_key in step.apis_required:
            adapter = get_adapter(api_key, self.config.variables)
            if adapter:
                return await adapter.execute("call", {"prompt": content, "step": step.title})

        # Generic fallback — return content as-is
        return {"output": content, "note": f"No adapter for step_type={step_type.value}"}

    # ------------------------------------------------------------------
    # Webhook firing (post-step)
    # ------------------------------------------------------------------

    async def _fire_webhook(self, url: str, result: "StepResult") -> None:
        import aiohttp
        payload = {
            "step_number": result.step_number,
            "title": result.title,
            "output": result.output,
            "status": result.status.value,
            "tool_name": self.blueprint.tool_name,
            "run_id": self.config.run_id,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status >= 400:
                    raise RuntimeError(f"Webhook returned {resp.status}")

    # ------------------------------------------------------------------
    # Template resolution
    # ------------------------------------------------------------------

    def _resolve_template(self, template: str) -> str:
        """[ROBOT] Replace {{variable}} and {variable} placeholders with values."""
        result = template

        # Double-brace style {{variable}}
        def replace_double(m: re.Match) -> str:
            key = m.group(1).strip()
            return self._vars.get(key, m.group(0))

        result = re.sub(r"\{\{(\w+)\}\}", replace_double, result)

        # Single-brace style {variable}
        def replace_single(m: re.Match) -> str:
            key = m.group(1).strip()
            return self._vars.get(key, m.group(0))

        result = re.sub(r"\{(\w+)\}", replace_single, result)

        return result
