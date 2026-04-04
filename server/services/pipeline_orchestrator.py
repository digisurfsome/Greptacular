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

    def __init__(
        self,
        working_directory: str,
        stages: list[PipelineStage],
        kickoff_message: str,
        token_budget: int = 400_000,
        model: str = "opus",
        pipeline_id: Optional[str] = None,
    ):
        self.pipeline_id = pipeline_id or f"pipeline-{uuid.uuid4().hex[:8]}"
        self.working_directory = working_directory
        self.stages = stages
        self.kickoff_message = kickoff_message
        self.token_budget = token_budget
        self.model = model
        self.status = PipelineStatus.IDLE
        self.created_at = datetime.now(timezone.utc)
        self.completed_at: Optional[datetime] = None

        # Total counters
        self.total_tokens = 0
        self.total_duration = 0.0

        # Internal state
        self._running = False
        self._current_session = None

        logger.info(
            "SkillPipeline created: id=%s, stages=%d, model=%s, token_budget=%d",
            self.pipeline_id,
            len(stages),
            model,
            token_budget,
        )

    def _build_stage_prompt(self, stage: PipelineStage) -> str:
        """Build the prompt for a given stage, incorporating previous output."""
        total = len(self.stages)

        if stage.index == 0:
            return (
                f"[SKILL PIPELINE — Stage 0: {stage.label}]\n\n"
                f"You are executing stage 0 of a {total}-stage skill pipeline.\n\n"
                f"## Your Skill Instructions\n\n"
                f"{stage.skill_text}\n\n"
                f"## User's Kickoff Message\n\n"
                f"{self.kickoff_message}\n\n"
                f"## Rules\n"
                f"1. Follow the skill instructions above completely.\n"
                f"2. Your full response IS the output for this stage.\n"
                f"3. Be thorough — your output feeds directly into the next stage.\n"
            )

        # Stages 1+: include previous stage output
        prev = self.stages[stage.index - 1]
        return (
            f"[SKILL PIPELINE — Stage {stage.index}: {stage.label}]\n\n"
            f"You are executing stage {stage.index} of a {total}-stage skill pipeline.\n\n"
            f"## Your Skill Instructions\n\n"
            f"{stage.skill_text}\n\n"
            f"## Output From Previous Stage ({prev.label})\n\n"
            f'<previous_stage_output stage="{stage.index - 1}" label="{prev.label}">\n'
            f"{prev.output}\n"
            f"</previous_stage_output>\n\n"
            f"## Rules\n"
            f"1. Follow the skill instructions above completely.\n"
            f"2. Your full response IS the output for this stage.\n"
            f"3. Be thorough — your output feeds directly into the next stage.\n"
        )

    async def run(self) -> AsyncGenerator[PipelineEvent, None]:
        """Execute stages sequentially.  Yields PipelineEvent objects."""
        from .workspace_chat_session import WorkspaceChatSession

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

        try:
            for stage in self.stages:
                if not self._running:
                    break

                stage.status = StageStatus.RUNNING
                stage.started_at = datetime.now(timezone.utc)
                stage.session_id = f"pipeline-{self.pipeline_id}-stage-{stage.index}"

                yield PipelineEvent(
                    event_type="pipeline_stage_started",
                    data={
                        "stage_index": stage.index,
                        "label": stage.label,
                        "session_id": stage.session_id,
                    },
                )

                prompt = self._build_stage_prompt(stage)
                full_text = ""
                context_tokens = 0
                stage_start = time.monotonic()

                try:
                    # Create a fresh session for this stage
                    session = WorkspaceChatSession(
                        session_id=stage.session_id,
                        working_directory=self.working_directory,
                        context_mode="1m",
                        model=self.model,
                    )
                    self._current_session = session

                    # Start the session
                    async for chunk in session.start():
                        chunk_type = chunk.get("type", "")
                        if chunk_type == "conversation_created":
                            stage.conversation_id = chunk.get("conversation_id")
                        elif chunk_type == "error":
                            logger.warning(
                                "Stage %d (%s) start error: %s",
                                stage.index, stage.label, chunk.get("content"),
                            )

                    # Send the skill prompt and collect the response
                    async for chunk in session.send_message(prompt):
                        if not self._running:
                            break

                        chunk_type = chunk.get("type", "")
                        if chunk_type == "text":
                            text = chunk.get("content", "")
                            full_text += text
                            yield PipelineEvent(
                                event_type="pipeline_stage_text",
                                data={
                                    "stage_index": stage.index,
                                    "text": text,
                                },
                            )
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

                    # Close the session after stage completes
                    try:
                        await session.close()
                    except Exception:
                        pass
                    self._current_session = None

                    # Mark stage completed
                    stage.output = full_text
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

                    # If context tokens exceeded budget, log it (the session is already
                    # closed above, so the next stage will get a fresh session regardless)
                    if context_tokens > self.token_budget:
                        logger.info(
                            "Stage %d context tokens (%d) exceeded budget (%d). "
                            "Next stage will use a fresh session.",
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
                    break

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

                    # Stop the entire pipeline on stage failure
                    self.status = PipelineStatus.FAILED
                    break

            # Determine final status
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

    def get_status(self) -> dict:
        """Return full status dict suitable for API responses."""
        return {
            "pipeline_id": self.pipeline_id,
            "status": self.status.value,
            "model": self.model,
            "token_budget": self.token_budget,
            "total_tokens": self.total_tokens,
            "total_duration": self.total_duration,
            "working_directory": self.working_directory,
            "kickoff_message": self.kickoff_message,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
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
                    "output_length": len(s.output),
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
) -> SkillPipeline:
    """Create a new skill pipeline.

    Args:
        working_directory: The working directory for agent sessions.
        stages: List of stage dicts, each with ``label`` and ``skill_text``.
        kickoff_message: The user's initial message for stage 0.
        token_budget: Maximum context tokens before forcing a fresh session.
        model: Model shorthand (``"opus"`` or ``"sonnet"``).
        pipeline_id: Optional custom pipeline ID.

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
