"""
Skill Pipeline Orchestrator
============================

Manages sequential skill pipelines where output from stage N feeds as
context into stage N+1.  Each stage creates a fresh WorkspaceChatSession,
sends a prompt containing the skill instructions and previous output,
collects the full response, then advances.

Key concepts:
- **SkillPipeline**: A sequence of skill stages executed one after another.
- **Token budget**: If the context window grows beyond the budget, the
  session is closed and a fresh one is created for the next stage.
- **Combined output**: All stage outputs are available as a single
  Markdown document for export.
"""

import asyncio
import json
import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import AsyncGenerator, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================

class StageStatus(str, Enum):
    """Status of a single pipeline stage."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineStatus(str, Enum):
    """Status of the overall pipeline."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class PipelineStage:
    """A single stage in the skill pipeline."""
    index: int
    label: str
    skill_text: str
    status: StageStatus = StageStatus.PENDING
    output: str = ""
    full_response: str = ""
    tokens_used: int = 0
    duration_seconds: float = 0.0
    conversation_id: Optional[int] = None
    session_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


@dataclass
class PipelineEvent:
    """An event emitted by the pipeline for real-time updates."""
    event_type: str
    data: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "type": self.event_type,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }


# ============================================================================
# Skill Pipeline
# ============================================================================

class SkillPipeline:
    """Orchestrates sequential execution of skill stages through Claude.

    Usage::

        pipeline = SkillPipeline(
            working_directory="/some/path",
            stages=[PipelineStage(...)],
            kickoff_message="Build me an app",
        )
        async for event in pipeline.run():
            handle(event)
    """

    # Valid execution modes for the pipeline
    VALID_EXECUTION_MODES = ("same_session", "new_session", "file_based", "database")

    def __init__(
        self,
        working_directory: str,
        stages: list[PipelineStage],
        kickoff_message: str,
        token_budget: int = 400_000,
        model: str = "opus",
        pipeline_id: Optional[str] = None,
        output_mode: str = "json",
        execution_mode: str = "same_session",
    ):
        self.pipeline_id = pipeline_id or f"pipeline-{uuid.uuid4().hex[:8]}"
        self.working_directory = working_directory
        self.stages = stages
        self.kickoff_message = kickoff_message
        self.token_budget = token_budget
        self.model = model
        self.output_mode = output_mode
        self.execution_mode = execution_mode if execution_mode in self.VALID_EXECUTION_MODES else "same_session"
        self.status = PipelineStatus.IDLE
        self.created_at = datetime.now(timezone.utc)
        self.completed_at: Optional[datetime] = None

        # Total counters
        self.total_tokens = 0
        self.total_duration = 0.0

        # Internal state
        self._running = False
        self._current_session = None
        self._waiting_for_answer = False
        self._waiting_question: Optional[str] = None
        self._answer_event: asyncio.Event = asyncio.Event()
        self._pending_answer: Optional[str] = None

        logger.info(
            "SkillPipeline created: id=%s, stages=%d, model=%s, token_budget=%d, output_mode=%s, execution_mode=%s",
            self.pipeline_id,
            len(stages),
            model,
            token_budget,
            output_mode,
            self.execution_mode,
        )

    @staticmethod
    def extract_json_output(full_text: str) -> str:
        """Extract the JSON context_packet from an agent's full response.

        The agent outputs commentary (parsing tables, confidence scores, etc.)
        mixed with the actual JSON output.  We need to extract just the JSON.

        Detection strategy (in order):
        1. Look for the LAST ``json ... `` code fence block (agents put the
           final output JSON at the end)
        2. Look for the LAST ``{ ... }`` block that is valid JSON and > 100 chars
        3. Fall back to the full text if no JSON found
        """
        import re as _re

        # Strategy 1: Last JSON code fence
        json_blocks = _re.findall(r'```json\s*\n(.*?)\n\s*```', full_text, _re.DOTALL)
        if json_blocks:
            return json_blocks[-1].strip()

        # Strategy 2: Last large JSON object — brace-depth scanning
        candidates: list[str] = []
        brace_depth = 0
        start = -1
        for i, ch in enumerate(full_text):
            if ch == '{':
                if brace_depth == 0:
                    start = i
                brace_depth += 1
            elif ch == '}':
                brace_depth -= 1
                if brace_depth == 0 and start >= 0:
                    block = full_text[start:i + 1]
                    if len(block) > 100:
                        try:
                            json.loads(block)
                            candidates.append(block)
                        except (json.JSONDecodeError, ValueError):
                            pass
                    start = -1

        if candidates:
            return candidates[-1].strip()

        # Strategy 3: Return full text as-is
        return full_text.strip()

    def _build_stage_prompt(self, stage: PipelineStage) -> str:
        """Build the prompt for a given stage, incorporating previous output."""
        if stage.index == 0:
            return (
                f"{stage.skill_text}\n\n"
                f"## User's Input\n\n"
                f"{self.kickoff_message}\n\n"
            )

        # Stages 1+: include previous stage output
        prev = self.stages[stage.index - 1]
        return (
            f"{stage.skill_text}\n\n"
            f"## Output From Previous Stage ({prev.label})\n\n"
            f"<previous_stage_output>\n"
            f"{prev.output}\n"
            f"</previous_stage_output>\n\n"
        )

    # ------------------------------------------------------------------
    # Shared stage lifecycle — used by ALL execution modes
    # ------------------------------------------------------------------

    STAGE_COMPLETE_MARKER = "[STAGE_COMPLETE]"

    async def _run_stage(
        self,
        stage: PipelineStage,
        session: "WorkspaceChatSession",  # noqa: F821
        prompt: str,
        start_time: float,
    ) -> AsyncGenerator[PipelineEvent, None]:
        """Run a single stage: send prompt, collect output, emit events.

        The stage runs until the agent outputs [STAGE_COMPLETE] — that's the
        agent's signal that its contract is met and the output is ready.
        If the agent asks questions instead, the stage stays active and the
        user can answer via inject_answer(). Each answer may produce more
        output. The stage only advances when [STAGE_COMPLETE] appears.

        Args:
            stage: The stage to run.
            session: An already-started WorkspaceChatSession.
            prompt: The fully-built prompt for this stage.
            start_time: ``time.monotonic()`` of the overall pipeline start.
        """
        full_text = ""
        context_tokens = 0
        stage_start = time.monotonic()
        stage_complete = False

        try:
            # Send the initial prompt
            async for chunk in session.send_message(prompt):
                if not self._running:
                    break

                chunk_type = chunk.get("type", "")
                if chunk_type == "text":
                    text = chunk.get("content", "")
                    full_text += text
                    stage.full_response = full_text
                    yield PipelineEvent(
                        event_type="pipeline_stage_text",
                        data={"stage_index": stage.index, "text": text},
                    )
                    # Check for completion marker
                    if self.STAGE_COMPLETE_MARKER in full_text:
                        stage_complete = True
                elif chunk_type == "token_usage":
                    context_tokens = chunk.get("context_tokens", 0)
                    output_tokens = chunk.get("output_tokens", 0)
                    stage.tokens_used = context_tokens + output_tokens
                    self.total_tokens = sum(s.tokens_used for s in self.stages)
                    yield PipelineEvent(
                        event_type="pipeline_token_usage",
                        data={
                            "stage_index": stage.index,
                            "context_tokens": context_tokens,
                            "output_tokens": output_tokens,
                            "total_tokens": self.total_tokens,
                            "budget": self.token_budget,
                        },
                    )

            # If no [STAGE_COMPLETE] marker, wait for user interaction.
            # The user answers via inject_answer() which sends to the same
            # session and collects more output. Each answer's response is
            # checked for the marker too.
            if not stage_complete and self._running:
                self._waiting_for_answer = True
                self._waiting_question = (
                    f"Stage {stage.index} needs interaction. "
                    f"Answer in the chat, or click Force Next to advance."
                )
                yield PipelineEvent(
                    event_type="pipeline_stage_waiting",
                    data={
                        "stage_index": stage.index,
                        "label": stage.label,
                        "question": self._waiting_question,
                    },
                )

                # Wait for [STAGE_COMPLETE] or Force Next
                while not stage_complete and self._running:
                    self._answer_event.clear()
                    # Wait for user to send a message or click Force Next
                    while not self._answer_event.is_set() and self._running:
                        # Check if inject_answer added [STAGE_COMPLETE] to full_response
                        if self.STAGE_COMPLETE_MARKER in (stage.full_response or ""):
                            stage_complete = True
                            full_text = stage.full_response
                            break
                        await asyncio.sleep(1.0)

                    if stage_complete:
                        break

                    # Force Next was clicked (answer_event set but no new content with marker)
                    if self._answer_event.is_set():
                        full_text = stage.full_response or full_text
                        break

                self._waiting_for_answer = False
                self._waiting_question = None

            # Strip the marker from the output
            if self.STAGE_COMPLETE_MARKER in full_text:
                full_text = full_text.split(self.STAGE_COMPLETE_MARKER)[0].strip()

            # Extract output based on output_mode
            if self.output_mode == "json":
                stage.output = self.extract_json_output(full_text)
                stage.full_response = full_text
            else:
                stage.output = full_text
                stage.full_response = full_text

            stage.status = StageStatus.COMPLETED
            stage.completed_at = datetime.now(timezone.utc)
            stage.duration_seconds = round(time.monotonic() - stage_start, 1)
            self.total_duration = round(time.monotonic() - start_time, 1)

            yield PipelineEvent(
                event_type="pipeline_stage_completed",
                data={
                    "stage_index": stage.index,
                    "label": stage.label,
                    "tokens_used": stage.tokens_used,
                    "duration_seconds": stage.duration_seconds,
                    "output_length": len(full_text),
                },
            )

            # Persist stage output
            try:
                from .workspace_database import save_pipeline_stage_output
                save_pipeline_stage_output(
                    pipeline_id=self.pipeline_id,
                    stage_index=stage.index,
                    label=stage.label,
                    output_text=full_text,
                    tokens_used=stage.tokens_used,
                    duration_seconds=stage.duration_seconds,
                    status=stage.status.value,
                )
            except Exception as e:
                logger.warning("Failed to persist stage %d output: %s", stage.index, e)

            # Log if context tokens are getting large
            if context_tokens > self.token_budget:
                logger.info(
                    "Stage %d context tokens (%d) exceeded budget (%d).",
                    stage.index, context_tokens, self.token_budget,
                )

        except asyncio.CancelledError:
            stage.status = StageStatus.FAILED
            stage.error = "Cancelled"
            stage.completed_at = datetime.now(timezone.utc)
            stage.duration_seconds = round(time.monotonic() - stage_start, 1)
            yield PipelineEvent(
                event_type="pipeline_stage_failed",
                data={"stage_index": stage.index, "label": stage.label, "error": "Cancelled"},
            )

        except Exception as e:
            stage.status = StageStatus.FAILED
            stage.error = str(e)
            stage.completed_at = datetime.now(timezone.utc)
            stage.duration_seconds = round(time.monotonic() - stage_start, 1)
            logger.exception("Pipeline stage %d (%s) failed: %s", stage.index, stage.label, e)

            yield PipelineEvent(
                event_type="pipeline_stage_failed",
                data={"stage_index": stage.index, "label": stage.label, "error": str(e)},
            )

            # Persist failed stage
            try:
                from .workspace_database import save_pipeline_stage_output
                save_pipeline_stage_output(
                    pipeline_id=self.pipeline_id,
                    stage_index=stage.index,
                    label=stage.label,
                    output_text=full_text,
                    tokens_used=stage.tokens_used,
                    duration_seconds=stage.duration_seconds,
                    status=stage.status.value,
                    error=str(e),
                )
            except Exception as persist_err:
                logger.warning("Failed to persist failed stage %d: %s", stage.index, persist_err)

    async def _create_and_start_session(self, session_id: str) -> "WorkspaceChatSession":  # noqa: F821
        """Create a new WorkspaceChatSession and start it.

        Returns the started session. Also sets ``self._current_session``.
        """
        from .workspace_chat_session import WorkspaceChatSession

        session = WorkspaceChatSession(
            session_id=session_id,
            working_directory=self.working_directory,
            context_mode="1m",
            model=self.model,
        )
        self._current_session = session

        async for chunk in session.start():
            chunk_type = chunk.get("type", "")
            if chunk_type == "conversation_created":
                conv_id = chunk.get("conversation_id")
                try:
                    from .workspace_database import update_conversation
                    update_conversation(conv_id, title=f"Pipeline: {self.pipeline_id}", category="pipeline")
                except Exception:
                    pass
            elif chunk_type == "error":
                logger.warning("Pipeline session start error: %s", chunk.get("content"))

        return session

    async def _close_session(self, session: "WorkspaceChatSession") -> None:  # noqa: F821
        """Close a session and clear ``_current_session`` if it matches."""
        try:
            await session.close()
        except Exception:
            pass
        if self._current_session is session:
            self._current_session = None

    # ------------------------------------------------------------------
    # Execution mode: same_session (original behavior)
    # ------------------------------------------------------------------

    async def _run_same_session(self, start_time: float) -> AsyncGenerator[PipelineEvent, None]:
        """One session for the entire pipeline.  All stages are messages in the
        same conversation — exactly the original behavior."""
        session_id = f"pipeline-{self.pipeline_id}"
        session = await self._create_and_start_session(session_id)

        try:
            for stage in self.stages:
                if not self._running:
                    break

                stage.status = StageStatus.RUNNING
                stage.started_at = datetime.now(timezone.utc)
                stage.session_id = session_id

                yield PipelineEvent(
                    event_type="pipeline_stage_started",
                    data={"stage_index": stage.index, "label": stage.label, "session_id": session_id},
                )

                prompt = self._build_stage_prompt(stage)
                async for event in self._run_stage(stage, session, prompt, start_time):
                    yield event

                # Abort pipeline on stage failure
                if stage.status == StageStatus.FAILED:
                    self.status = PipelineStatus.FAILED
                    break
        finally:
            await self._close_session(session)

    # ------------------------------------------------------------------
    # Execution mode: new_session (fresh session per stage)
    # ------------------------------------------------------------------

    async def _run_new_session(self, start_time: float) -> AsyncGenerator[PipelineEvent, None]:
        """Fresh WorkspaceChatSession per stage.  Each stage gets an independent
        conversation with the previous stage's output injected into its prompt."""
        for stage in self.stages:
            if not self._running:
                break

            session_id = f"pipeline-{self.pipeline_id}-stage-{stage.index}"
            session = await self._create_and_start_session(session_id)

            try:
                stage.status = StageStatus.RUNNING
                stage.started_at = datetime.now(timezone.utc)
                stage.session_id = session_id

                yield PipelineEvent(
                    event_type="pipeline_stage_started",
                    data={"stage_index": stage.index, "label": stage.label, "session_id": session_id},
                )

                prompt = self._build_stage_prompt(stage)
                async for event in self._run_stage(stage, session, prompt, start_time):
                    yield event

                if stage.status == StageStatus.FAILED:
                    self.status = PipelineStatus.FAILED
                    break
            finally:
                await self._close_session(session)

    # ------------------------------------------------------------------
    # Execution mode: file_based (disk handoff between stages)
    # ------------------------------------------------------------------

    def _get_file_based_dir(self) -> Path:
        """Return the directory for file-based pipeline outputs."""
        base = Path.home() / ".autoforge" / "pipeline" / self.pipeline_id
        base.mkdir(parents=True, exist_ok=True)
        return base

    def _build_stage_prompt_from_text(self, stage: PipelineStage, previous_output: str) -> str:
        """Build a stage prompt using explicit previous output text (for file/db modes)."""
        if stage.index == 0:
            return (
                f"{stage.skill_text}\n\n"
                f"## User's Input\n\n"
                f"{self.kickoff_message}\n\n"
            )

        prev_label = self.stages[stage.index - 1].label
        return (
            f"{stage.skill_text}\n\n"
            f"## Output From Previous Stage ({prev_label})\n\n"
            f"<previous_stage_output>\n"
            f"{previous_output}\n"
            f"</previous_stage_output>\n\n"
        )

    async def _run_file_based(self, start_time: float) -> AsyncGenerator[PipelineEvent, None]:
        """Each stage writes output to a file on disk.  The next stage reads
        the previous file and incorporates it into its prompt."""
        output_dir = self._get_file_based_dir()

        for stage in self.stages:
            if not self._running:
                break

            session_id = f"pipeline-{self.pipeline_id}-stage-{stage.index}"
            session = await self._create_and_start_session(session_id)

            try:
                stage.status = StageStatus.RUNNING
                stage.started_at = datetime.now(timezone.utc)
                stage.session_id = session_id

                yield PipelineEvent(
                    event_type="pipeline_stage_started",
                    data={"stage_index": stage.index, "label": stage.label, "session_id": session_id},
                )

                # Read previous stage output from file (if not first stage)
                if stage.index > 0:
                    prev_file = output_dir / f"stage-{stage.index - 1}-output.txt"
                    try:
                        previous_output = prev_file.read_text(encoding="utf-8")
                    except FileNotFoundError:
                        previous_output = ""
                        logger.warning("File-based mode: previous stage file not found: %s", prev_file)
                    prompt = self._build_stage_prompt_from_text(stage, previous_output)
                else:
                    prompt = self._build_stage_prompt(stage)

                async for event in self._run_stage(stage, session, prompt, start_time):
                    yield event

                # Write this stage's output to disk
                if stage.status == StageStatus.COMPLETED:
                    out_file = output_dir / f"stage-{stage.index}-output.txt"
                    out_file.write_text(stage.output, encoding="utf-8")
                    logger.info("File-based mode: wrote %d chars to %s", len(stage.output), out_file)

                if stage.status == StageStatus.FAILED:
                    self.status = PipelineStatus.FAILED
                    break
            finally:
                await self._close_session(session)

    # ------------------------------------------------------------------
    # Execution mode: database (DB handoff between stages)
    # ------------------------------------------------------------------

    async def _run_database(self, start_time: float) -> AsyncGenerator[PipelineEvent, None]:
        """Each stage reads the previous stage's output from the database
        (already persisted by ``_run_stage``) and uses it in the prompt."""
        for stage in self.stages:
            if not self._running:
                break

            session_id = f"pipeline-{self.pipeline_id}-stage-{stage.index}"
            session = await self._create_and_start_session(session_id)

            try:
                stage.status = StageStatus.RUNNING
                stage.started_at = datetime.now(timezone.utc)
                stage.session_id = session_id

                yield PipelineEvent(
                    event_type="pipeline_stage_started",
                    data={"stage_index": stage.index, "label": stage.label, "session_id": session_id},
                )

                # Read previous stage output from database (if not first stage)
                if stage.index > 0:
                    from .workspace_database import get_pipeline_stage_outputs
                    db_stages = get_pipeline_stage_outputs(self.pipeline_id)
                    prev_output = ""
                    for db_stage in db_stages:
                        if db_stage.get("stage_index") == stage.index - 1:
                            prev_output = db_stage.get("output_text", "")
                            break
                    prompt = self._build_stage_prompt_from_text(stage, prev_output)
                else:
                    prompt = self._build_stage_prompt(stage)

                async for event in self._run_stage(stage, session, prompt, start_time):
                    yield event

                if stage.status == StageStatus.FAILED:
                    self.status = PipelineStatus.FAILED
                    break
            finally:
                await self._close_session(session)

    # ------------------------------------------------------------------
    # Main run() dispatcher
    # ------------------------------------------------------------------

    async def run(self) -> AsyncGenerator[PipelineEvent, None]:
        """Execute stages sequentially.  Yields PipelineEvent objects.

        Dispatches to the appropriate execution mode method based on
        ``self.execution_mode``.
        """
        self.status = PipelineStatus.RUNNING
        self._running = True
        start_time = time.monotonic()

        yield PipelineEvent(
            event_type="pipeline_started",
            data={
                "pipeline_id": self.pipeline_id,
                "total_stages": len(self.stages),
                "model": self.model,
                "token_budget": self.token_budget,
                "execution_mode": self.execution_mode,
            },
        )

        # Persist the initial run record
        try:
            from .workspace_database import save_pipeline_run
            save_pipeline_run(
                pipeline_id=self.pipeline_id,
                name=self.stages[0].label if self.stages else "Unnamed",
                status=self.status.value,
                model=self.model,
                token_budget=self.token_budget,
                working_directory=self.working_directory,
                kickoff_message=self.kickoff_message,
                stages_json=json.dumps([
                    {"label": s.label, "skill_text": s.skill_text} for s in self.stages
                ]),
            )
        except Exception as e:
            logger.warning("Failed to save initial pipeline run record: %s", e)

        # Dispatch to the correct execution mode
        mode_runners = {
            "same_session": self._run_same_session,
            "new_session": self._run_new_session,
            "file_based": self._run_file_based,
            "database": self._run_database,
        }
        runner = mode_runners.get(self.execution_mode, self._run_same_session)

        try:
            async for event in runner(start_time):
                yield event

            # Determine final status (if not already set by a failed stage)
            if not self._running and self.status != PipelineStatus.FAILED:
                self.status = PipelineStatus.STOPPED
            elif self.status != PipelineStatus.FAILED:
                all_done = all(s.status == StageStatus.COMPLETED for s in self.stages)
                self.status = PipelineStatus.COMPLETED if all_done else PipelineStatus.FAILED

        except Exception as e:
            self.status = PipelineStatus.FAILED
            logger.exception("Pipeline %s failed unexpectedly: %s", self.pipeline_id, e)
            yield PipelineEvent(
                event_type="pipeline_error",
                data={"pipeline_id": self.pipeline_id, "error": str(e)},
            )

        # Close any lingering session
        if self._current_session:
            try:
                await self._current_session.close()
            except Exception:
                pass
            self._current_session = None

        # Finalize
        self.completed_at = datetime.now(timezone.utc)
        self.total_duration = round(time.monotonic() - start_time, 1)

        final_event_type = (
            "pipeline_completed" if self.status == PipelineStatus.COMPLETED
            else "pipeline_stopped" if self.status == PipelineStatus.STOPPED
            else "pipeline_error"
        )
        yield PipelineEvent(
            event_type=final_event_type,
            data={
                "pipeline_id": self.pipeline_id,
                "status": self.status.value,
                "total_tokens": self.total_tokens,
                "total_duration": self.total_duration,
                "stages_completed": sum(1 for s in self.stages if s.status == StageStatus.COMPLETED),
                "stages_total": len(self.stages),
            },
        )

        # Update the run record in the database
        try:
            from .workspace_database import update_pipeline_run
            update_pipeline_run(
                self.pipeline_id,
                status=self.status.value,
                total_tokens=self.total_tokens,
                total_duration=self.total_duration,
                completed_at=self.completed_at,
            )
        except Exception as e:
            logger.warning("Failed to update pipeline run record: %s", e)

    async def inject_answer(self, answer: str) -> dict:
        """Send a user message to the currently running stage's session.

        The message is sent to the same conversation the stage is using.
        The agent's response is collected and appended to the stage's output.
        Returns the response text so the frontend can display it.
        """
        if not self._current_session:
            return {"success": False, "response": "", "error": "No active session"}

        # Find the running stage
        running_stage = next((s for s in self.stages if s.status == StageStatus.RUNNING), None)
        if not running_stage:
            # Try the most recently completed stage (pipeline might be between stages)
            running_stage = next((s for s in reversed(self.stages) if s.status == StageStatus.COMPLETED), None)

        response_text = ""
        try:
            async for chunk in self._current_session.send_message(answer):
                chunk_type = chunk.get("type", "")
                if chunk_type == "text":
                    text = chunk.get("content", "")
                    response_text += text
                    if running_stage:
                        running_stage.full_response += text
                elif chunk_type == "token_usage":
                    if running_stage:
                        ctx = chunk.get("context_tokens", 0)
                        out = chunk.get("output_tokens", 0)
                        running_stage.tokens_used = ctx + out
                        self.total_tokens = sum(s.tokens_used for s in self.stages)

            # Update the stage output with the new response
            if running_stage and response_text:
                running_stage.output += "\n\n" + response_text
                running_stage.full_response = running_stage.full_response or ""

            # Signal the waiting loop to check for [STAGE_COMPLETE]
            self._answer_event.set()

            logger.info("Pipeline %s: message sent, got %d chars back", self.pipeline_id, len(response_text))
            return {"success": True, "response": response_text}

        except Exception as e:
            logger.warning("Pipeline %s: send message failed: %s", self.pipeline_id, e)
            return {"success": False, "response": response_text, "error": str(e)}

    async def stop(self):
        """Stop the pipeline and close any active session."""
        logger.info("Stopping pipeline %s", self.pipeline_id)
        self._running = False
        self.status = PipelineStatus.STOPPED

        if self._current_session:
            try:
                await self._current_session.close()
            except Exception as e:
                logger.warning("Error closing current session: %s", e)
            self._current_session = None

    async def force_advance(self) -> dict:
        """Force-advance to the next stage.

        Closes the current session, marks the running stage as completed
        with whatever output has been collected so far, and unblocks the
        run loop so it moves to the next stage.
        """
        running_stage = next((s for s in self.stages if s.status == StageStatus.RUNNING), None)
        if not running_stage:
            return {"success": False, "message": "No running stage to advance from"}

        logger.info(
            "Force-advancing pipeline %s from stage %d (%s)",
            self.pipeline_id, running_stage.index, running_stage.label,
        )

        # Close the current session to stop the SDK
        if self._current_session:
            try:
                await self._current_session.close()
            except Exception:
                pass
            self._current_session = None

        # Mark stage as completed with whatever we have
        running_stage.status = StageStatus.COMPLETED
        running_stage.completed_at = datetime.now(timezone.utc)
        if not running_stage.output and running_stage.full_response:
            if self.output_mode == "json":
                running_stage.output = self.extract_json_output(running_stage.full_response)
            else:
                running_stage.output = running_stage.full_response

        # Clear waiting state
        self._waiting_for_answer = False
        self._waiting_question = None
        self._answer_event.set()

        return {
            "success": True,
            "message": f"Force-advanced from stage {running_stage.index} ({running_stage.label})",
            "stage_index": running_stage.index,
        }

    def get_status(self) -> dict:
        """Return full status dict suitable for API responses."""
        return {
            "pipeline_id": self.pipeline_id,
            "status": self.status.value,
            "model": self.model,
            "token_budget": self.token_budget,
            "output_mode": self.output_mode,
            "execution_mode": self.execution_mode,
            "total_tokens": self.total_tokens,
            "total_duration": self.total_duration,
            "working_directory": self.working_directory,
            "kickoff_message": self.kickoff_message,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "waiting_for_answer": self._waiting_for_answer,
            "waiting_question": self._waiting_question,
            "stages": [
                {
                    "index": s.index,
                    "label": s.label,
                    "status": s.status.value,
                    "tokens_used": s.tokens_used,
                    "duration_seconds": s.duration_seconds,
                    "conversation_id": s.conversation_id,
                    "session_id": s.session_id,
                    "started_at": s.started_at.isoformat() if s.started_at else None,
                    "completed_at": s.completed_at.isoformat() if s.completed_at else None,
                    "output": s.output,
                    "output_length": len(s.output),
                    "full_response_length": len(s.full_response),
                    "error": s.error,
                }
                for s in self.stages
            ],
        }

    def get_combined_output(self) -> str:
        """Return all stage outputs concatenated as a single Markdown document."""
        parts = [f"# Skill Pipeline Output — {self.pipeline_id}\n"]
        parts.append(f"**Model:** {self.model}  ")
        parts.append(f"**Total Duration:** {self.total_duration}s  ")
        parts.append(f"**Total Tokens:** {self.total_tokens}\n")

        for stage in self.stages:
            parts.append(f"\n---\n\n## Stage {stage.index}: {stage.label}\n")
            if stage.status == StageStatus.COMPLETED:
                parts.append(f"*Duration: {stage.duration_seconds}s | Tokens: {stage.tokens_used}*\n")
                parts.append(stage.output)
            elif stage.status == StageStatus.FAILED:
                parts.append(f"**FAILED:** {stage.error or 'Unknown error'}\n")
            else:
                parts.append(f"*Status: {stage.status.value}*\n")

        return "\n".join(parts)


# =============================================================================
# Global Pipeline Registry
# =============================================================================

_pipelines: dict[str, SkillPipeline] = {}
_pipeline_lock = threading.Lock()


async def create_pipeline(
    working_directory: str,
    stages: list[dict],
    kickoff_message: str,
    token_budget: int = 400_000,
    model: str = "opus",
    pipeline_id: Optional[str] = None,
    output_mode: str = "json",
    execution_mode: str = "same_session",
) -> SkillPipeline:
    """Create a new skill pipeline.

    Args:
        working_directory: The working directory for agent sessions.
        stages: List of stage dicts, each with ``label`` and ``skill_text``.
        kickoff_message: The user's initial message for stage 0.
        token_budget: Maximum context tokens before forcing a fresh session.
        model: Model shorthand (``"opus"`` or ``"sonnet"``).
        pipeline_id: Optional custom pipeline ID.
        output_mode: ``"json"`` to extract JSON from responses, ``"text"`` for raw output.
        execution_mode: How stages share context — ``"same_session"``, ``"new_session"``,
            ``"file_based"``, or ``"database"``.

    Returns:
        The created SkillPipeline instance.
    """
    pipeline_stages = [
        PipelineStage(
            index=i,
            label=s["label"],
            skill_text=s["skill_text"],
        )
        for i, s in enumerate(stages)
    ]

    pipeline = SkillPipeline(
        working_directory=working_directory,
        stages=pipeline_stages,
        kickoff_message=kickoff_message,
        token_budget=token_budget,
        model=model,
        pipeline_id=pipeline_id,
        output_mode=output_mode,
        execution_mode=execution_mode,
    )

    with _pipeline_lock:
        # Stop any existing pipeline with the same ID
        if pipeline_id and pipeline_id in _pipelines:
            old = _pipelines.pop(pipeline_id)
            try:
                asyncio.get_event_loop().create_task(old.stop())
            except RuntimeError:
                pass
        _pipelines[pipeline.pipeline_id] = pipeline

    return pipeline


def get_pipeline(pipeline_id: str) -> Optional[SkillPipeline]:
    """Get an active pipeline by ID."""
    with _pipeline_lock:
        return _pipelines.get(pipeline_id)


def list_pipelines() -> list[dict]:
    """List all active (in-memory) pipelines."""
    with _pipeline_lock:
        return [p.get_status() for p in _pipelines.values()]


async def cleanup_all_pipelines():
    """Stop all running pipelines.  Called on server shutdown."""
    with _pipeline_lock:
        pipelines = list(_pipelines.values())
        _pipelines.clear()

    for pipeline in pipelines:
        try:
            await pipeline.stop()
        except Exception as e:
            logger.warning("Error stopping pipeline %s: %s", pipeline.pipeline_id, e)
