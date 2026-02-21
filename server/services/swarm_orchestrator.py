"""
Swarm Orchestrator
==================

Manages concurrent autonomous agent pipelines ("swarms") where multiple
agents run in parallel, share files through a common workspace directory,
and automatically hand off work when one agent produces output.

Key concepts:
- **SwarmPipeline**: A sequence of agent stages (e.g. Research → PRD → Coder)
- **Shared workspace**: A directory where all agents read/write files
- **File watcher**: Monitors the shared workspace and triggers the next
  agent when a trigger file appears
- **Auto-handoff**: Uses the walkie-talkie mechanism to inject outputs
  from one agent into the next agent's session

Each agent is a full WorkspaceChatSession with its own Claude instance.
The orchestrator coordinates them without limiting their autonomy.
"""

import asyncio
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class StageStatus(str, Enum):
    """Status of a pipeline stage."""
    PENDING = "pending"
    RUNNING = "running"
    WAITING_TRIGGER = "waiting_trigger"  # Waiting for trigger file from previous stage
    COMPLETED = "completed"
    FAILED = "failed"


class SwarmStatus(str, Enum):
    """Status of the overall swarm pipeline."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


@dataclass
class SwarmStage:
    """Definition of a single stage in the swarm pipeline."""
    name: str                          # e.g. "research", "prd", "coder"
    label: str                         # e.g. "Research Agent"
    model: str                         # "opus" or "sonnet"
    context_mode: str                  # "1m" or "200k"
    initial_prompt: str                # The first message sent to start this agent
    output_file: str                   # File the agent should write its output to
    trigger_file: Optional[str] = None # File from previous stage that triggers this stage
    status: StageStatus = StageStatus.PENDING
    session_id: Optional[str] = None   # WorkspaceChatSession ID
    conversation_id: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


@dataclass
class SwarmEvent:
    """An event emitted by the swarm for real-time UI updates."""
    event_type: str     # "stage_started", "stage_completed", "file_created", "handoff", "error", "status_change"
    stage_name: Optional[str] = None
    data: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "type": f"swarm_{self.event_type}",
            "stage": self.stage_name,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }


class SwarmPipeline:
    """Orchestrates a multi-agent pipeline with shared workspace and auto-handoff.

    Usage:
        pipeline = SwarmPipeline(
            working_directory="/path/to/project",
            stages=[...],
        )
        async for event in pipeline.run():
            # Handle real-time events
            pass
    """

    def __init__(
        self,
        working_directory: str,
        stages: list[SwarmStage],
        swarm_id: Optional[str] = None,
    ):
        self.swarm_id = swarm_id or f"swarm-{uuid.uuid4().hex[:8]}"
        self.working_directory = working_directory
        self.stages = stages
        self.status = SwarmStatus.IDLE

        # Shared workspace directory — all agents read/write here
        self.shared_dir = Path.home() / ".autoforge" / "swarm" / self.swarm_id
        self.shared_dir.mkdir(parents=True, exist_ok=True)

        # Event queue for broadcasting to WebSocket clients
        self._event_queue: asyncio.Queue[SwarmEvent] = asyncio.Queue()

        # File watcher state
        self._known_files: set[str] = set()
        self._watcher_task: Optional[asyncio.Task] = None
        self._running = False

        # Agent sessions
        self._sessions: dict[str, Any] = {}  # stage_name -> WorkspaceChatSession
        self._agent_tasks: dict[str, asyncio.Task] = {}  # stage_name -> running task

        logger.info(
            "SwarmPipeline created: id=%s, stages=%s, shared_dir=%s",
            self.swarm_id,
            [s.name for s in stages],
            self.shared_dir,
        )

    def get_status(self) -> dict:
        """Get the current status of the pipeline and all stages."""
        return {
            "swarm_id": self.swarm_id,
            "status": self.status.value,
            "shared_dir": str(self.shared_dir),
            "working_directory": self.working_directory,
            "stages": [
                {
                    "name": s.name,
                    "label": s.label,
                    "model": s.model,
                    "context_mode": s.context_mode,
                    "status": s.status.value,
                    "output_file": s.output_file,
                    "trigger_file": s.trigger_file,
                    "conversation_id": s.conversation_id,
                    "started_at": s.started_at.isoformat() if s.started_at else None,
                    "completed_at": s.completed_at.isoformat() if s.completed_at else None,
                    "error": s.error,
                }
                for s in self.stages
            ],
            "shared_files": self._list_shared_files(),
        }

    def _list_shared_files(self) -> list[dict]:
        """List all files in the shared workspace."""
        files = []
        if self.shared_dir.exists():
            for f in sorted(self.shared_dir.iterdir()):
                if f.is_file() and not f.name.startswith("."):
                    files.append({
                        "name": f.name,
                        "size": f.stat().st_size,
                        "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                    })
        return files

    def _emit(self, event_type: str, stage_name: Optional[str] = None, **data):
        """Emit an event to the event queue."""
        event = SwarmEvent(event_type=event_type, stage_name=stage_name, data=data)
        self._event_queue.put_nowait(event)

    async def run(self):
        """Run the swarm pipeline. Yields SwarmEvent objects in real-time.

        This is an async generator that:
        1. Starts the first stage (no trigger needed)
        2. Starts the file watcher
        3. Yields events as agents work and files are created
        4. Auto-triggers subsequent stages when their trigger files appear
        """
        self.status = SwarmStatus.RUNNING
        self._running = True
        self._emit("status_change", data={"status": "running"})

        try:
            # Scan existing files in shared dir
            if self.shared_dir.exists():
                for f in self.shared_dir.iterdir():
                    if f.is_file():
                        self._known_files.add(f.name)

            # Start stages that have no trigger (first stage, or independent stages)
            for stage in self.stages:
                if stage.trigger_file is None:
                    await self._start_stage(stage)

            # Start file watcher
            self._watcher_task = asyncio.create_task(self._watch_files())

            # Yield events as they come
            while self._running:
                try:
                    event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                    yield event

                    # Check if all stages are done
                    if self._all_stages_done():
                        self.status = SwarmStatus.COMPLETED
                        self._running = False
                        self._emit("status_change", data={"status": "completed"})
                        # Yield the final status event
                        try:
                            final = await asyncio.wait_for(self._event_queue.get(), timeout=0.1)
                            yield final
                        except asyncio.TimeoutError:
                            pass

                except asyncio.TimeoutError:
                    # Check if all done during timeout
                    if self._all_stages_done():
                        self.status = SwarmStatus.COMPLETED
                        self._running = False
                        self._emit("status_change", data={"status": "completed"})
                        yield await self._event_queue.get()

        except Exception as e:
            self.status = SwarmStatus.FAILED
            self._emit("error", data={"error": str(e)})
            logger.exception("Swarm pipeline failed: %s", e)
        finally:
            self._running = False
            if self._watcher_task:
                self._watcher_task.cancel()
                try:
                    await self._watcher_task
                except asyncio.CancelledError:
                    pass

    async def stop(self):
        """Stop the running swarm pipeline and all agent sessions."""
        logger.info("Stopping swarm pipeline %s", self.swarm_id)
        self._running = False
        self.status = SwarmStatus.STOPPED

        # Cancel all agent tasks
        for name, task in self._agent_tasks.items():
            if not task.done():
                task.cancel()
                logger.info("Cancelled agent task for stage '%s'", name)

        # Close all sessions
        for name, session in self._sessions.items():
            try:
                await session.close()
                logger.info("Closed session for stage '%s'", name)
            except Exception as e:
                logger.warning("Error closing session for '%s': %s", name, e)

        # Cancel file watcher
        if self._watcher_task and not self._watcher_task.done():
            self._watcher_task.cancel()

        self._emit("status_change", data={"status": "stopped"})

    def _all_stages_done(self) -> bool:
        """Check if all stages have completed (or failed)."""
        return all(
            s.status in (StageStatus.COMPLETED, StageStatus.FAILED)
            for s in self.stages
        )

    async def _start_stage(self, stage: SwarmStage):
        """Start an agent for a pipeline stage."""
        from .workspace_chat_session import WorkspaceChatSession

        logger.info("Starting swarm stage '%s' (model=%s, context=%s)", stage.name, stage.model, stage.context_mode)

        stage.status = StageStatus.RUNNING
        stage.started_at = datetime.now()
        stage.session_id = f"swarm-{self.swarm_id}-{stage.name}"

        # Augment the initial prompt with shared workspace instructions
        augmented_prompt = self._build_stage_prompt(stage)

        # Create the agent session
        session = WorkspaceChatSession(
            session_id=stage.session_id,
            working_directory=self.working_directory,
            context_mode=stage.context_mode,
            model=stage.model,
        )
        self._sessions[stage.name] = session

        self._emit("stage_started", stage.name, label=stage.label, model=stage.model)

        # Run the agent in a background task
        task = asyncio.create_task(self._run_agent(stage, session, augmented_prompt))
        self._agent_tasks[stage.name] = task

    def _build_stage_prompt(self, stage: SwarmStage) -> str:
        """Build the augmented prompt for a stage, including shared workspace instructions."""
        shared_path = str(self.shared_dir)

        preamble = f"""[SWARM PIPELINE - {stage.label.upper()}]

You are the **{stage.label}** in an autonomous multi-agent swarm pipeline.

## Shared Workspace
All agents in this pipeline share a workspace directory at:
  {shared_path}

## Your Output
When you complete your work, you MUST write your final output to:
  {shared_path}/{stage.output_file}

This is CRITICAL — the next agent in the pipeline is watching for this file
and will automatically start working once it appears.

## Guidelines
1. Do your work thoroughly and autonomously
2. Write your output file when done — this is how the pipeline advances
3. If you receive walkie-talkie messages with input from a previous agent, incorporate that context
4. Use absolute paths when reading/writing to the shared workspace
5. The shared workspace is at: {shared_path}

## Your Task
"""
        # If there's content from a trigger file, include it
        if stage.trigger_file:
            trigger_path = self.shared_dir / stage.trigger_file
            if trigger_path.exists():
                try:
                    trigger_content = trigger_path.read_text(encoding="utf-8")
                    preamble += f"""
The previous agent has completed their work. Their output is below:

<previous_agent_output file="{stage.trigger_file}">
{trigger_content}
</previous_agent_output>

Based on this input, here is your task:

"""
                except Exception as e:
                    logger.warning("Could not read trigger file %s: %s", trigger_path, e)

        return preamble + stage.initial_prompt

    async def _run_agent(self, stage: SwarmStage, session, prompt: str):
        """Run an agent session for a stage, collecting events."""
        try:
            # Start the session
            async for chunk in session.start():
                chunk_type = chunk.get("type", "")
                if chunk_type == "conversation_created":
                    stage.conversation_id = chunk.get("conversation_id")
                    self._emit("stage_update", stage.name, conversation_id=stage.conversation_id)
                elif chunk_type == "error":
                    logger.warning("Stage '%s' start error: %s", stage.name, chunk.get("content"))

            # Send the initial prompt
            async for chunk in session.send_message(prompt):
                chunk_type = chunk.get("type", "")
                if chunk_type == "text":
                    # Check if the agent wrote the output file
                    output_path = self.shared_dir / stage.output_file
                    if output_path.exists() and stage.output_file not in self._known_files:
                        self._known_files.add(stage.output_file)
                        self._emit(
                            "file_created",
                            stage.name,
                            filename=stage.output_file,
                            size=output_path.stat().st_size,
                        )
                elif chunk_type == "error":
                    logger.warning("Stage '%s' error: %s", stage.name, chunk.get("content"))

            # After the agent finishes, check if output file exists
            output_path = self.shared_dir / stage.output_file
            if output_path.exists():
                stage.status = StageStatus.COMPLETED
                stage.completed_at = datetime.now()
                self._emit(
                    "stage_completed",
                    stage.name,
                    output_file=stage.output_file,
                    duration_s=round((stage.completed_at - stage.started_at).total_seconds(), 1) if stage.started_at else None,
                )
            else:
                # Agent finished but didn't write the output file — mark as completed anyway
                # (the agent may have written output inline or made code changes directly)
                stage.status = StageStatus.COMPLETED
                stage.completed_at = datetime.now()
                self._emit(
                    "stage_completed",
                    stage.name,
                    output_file=None,
                    note="Agent completed without writing output file",
                )

        except asyncio.CancelledError:
            stage.status = StageStatus.FAILED
            stage.error = "Cancelled"
            self._emit("stage_failed", stage.name, error="Cancelled")
        except Exception as e:
            stage.status = StageStatus.FAILED
            stage.error = str(e)
            self._emit("stage_failed", stage.name, error=str(e))
            logger.exception("Agent error in stage '%s': %s", stage.name, e)
        finally:
            try:
                await session.close()
            except Exception:
                pass

    async def _watch_files(self):
        """Watch the shared workspace for new files and trigger waiting stages."""
        logger.info("File watcher started for swarm %s, watching %s", self.swarm_id, self.shared_dir)

        while self._running:
            try:
                await asyncio.sleep(2)  # Poll every 2 seconds

                if not self.shared_dir.exists():
                    continue

                # Check for new files
                current_files = {
                    f.name for f in self.shared_dir.iterdir()
                    if f.is_file() and not f.name.startswith(".")
                }
                new_files = current_files - self._known_files

                for filename in new_files:
                    self._known_files.add(filename)
                    file_path = self.shared_dir / filename
                    self._emit(
                        "file_created",
                        data={
                            "filename": filename,
                            "size": file_path.stat().st_size,
                        },
                    )
                    logger.info("New file detected in swarm workspace: %s", filename)

                    # Check if any waiting stage is triggered by this file
                    for stage in self.stages:
                        if (
                            stage.trigger_file == filename
                            and stage.status == StageStatus.PENDING
                        ):
                            logger.info(
                                "Trigger file '%s' detected — starting stage '%s'",
                                filename, stage.name,
                            )
                            self._emit(
                                "handoff",
                                stage.name,
                                trigger_file=filename,
                                from_stage=self._find_stage_by_output(filename),
                            )
                            await self._start_stage(stage)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning("File watcher error: %s", e)
                await asyncio.sleep(5)

        logger.info("File watcher stopped for swarm %s", self.swarm_id)

    def _find_stage_by_output(self, filename: str) -> Optional[str]:
        """Find which stage produces the given output file."""
        for stage in self.stages:
            if stage.output_file == filename:
                return stage.name
        return None

    async def inject_message(self, stage_name: str, content: str) -> bool:
        """Inject a walkie-talkie message into a running stage's agent.

        Args:
            stage_name: The stage to send the message to.
            content: The message content.

        Returns:
            True if the message was queued, False if the stage is not running.
        """
        session = self._sessions.get(stage_name)
        if session and session.walkie_talkie_enabled:
            await session.queue_walkie_talkie_message(content)
            return True
        return False

    def read_shared_file(self, filename: str) -> Optional[str]:
        """Read a file from the shared workspace."""
        file_path = self.shared_dir / filename
        if file_path.exists() and file_path.is_file():
            try:
                return file_path.read_text(encoding="utf-8")
            except Exception:
                return None
        return None


# =============================================================================
# Global Swarm Registry
# =============================================================================

_active_swarms: dict[str, SwarmPipeline] = {}
_swarms_lock = asyncio.Lock()


async def create_swarm(
    working_directory: str,
    stages: list[dict],
    swarm_id: Optional[str] = None,
) -> SwarmPipeline:
    """Create a new swarm pipeline.

    Args:
        working_directory: The project directory all agents work in.
        stages: List of stage definitions, each with:
            - name: Stage identifier
            - label: Human-readable label
            - model: "opus" or "sonnet"
            - context_mode: "1m" or "200k"
            - initial_prompt: First message to the agent
            - output_file: File the agent writes when done
            - trigger_file: (optional) File that triggers this stage
        swarm_id: Optional custom swarm ID.

    Returns:
        The created SwarmPipeline instance.
    """
    pipeline_stages = [
        SwarmStage(
            name=s["name"],
            label=s["label"],
            model=s.get("model", "opus"),
            context_mode=s.get("context_mode", "1m"),
            initial_prompt=s["initial_prompt"],
            output_file=s["output_file"],
            trigger_file=s.get("trigger_file"),
        )
        for s in stages
    ]

    pipeline = SwarmPipeline(
        working_directory=working_directory,
        stages=pipeline_stages,
        swarm_id=swarm_id,
    )

    async with _swarms_lock:
        # Stop any existing swarm with the same ID
        if swarm_id and swarm_id in _active_swarms:
            old = _active_swarms.pop(swarm_id)
            await old.stop()
        _active_swarms[pipeline.swarm_id] = pipeline

    return pipeline


async def get_swarm(swarm_id: str) -> Optional[SwarmPipeline]:
    """Get an active swarm by ID."""
    async with _swarms_lock:
        return _active_swarms.get(swarm_id)


async def stop_swarm(swarm_id: str) -> bool:
    """Stop and remove an active swarm."""
    async with _swarms_lock:
        pipeline = _active_swarms.pop(swarm_id, None)

    if pipeline:
        await pipeline.stop()
        return True
    return False


async def list_swarms() -> list[dict]:
    """List all active swarms."""
    async with _swarms_lock:
        return [p.get_status() for p in _active_swarms.values()]


async def cleanup_all_swarms():
    """Stop all active swarms. Called on server shutdown."""
    async with _swarms_lock:
        swarms = list(_active_swarms.values())
        _active_swarms.clear()

    for pipeline in swarms:
        try:
            await pipeline.stop()
        except Exception as e:
            logger.warning("Error stopping swarm %s: %s", pipeline.swarm_id, e)


def build_default_pipeline_stages(
    task_description: str,
    research_model: str = "sonnet",
    prd_model: str = "opus",
    coder_model: str = "sonnet",
) -> list[dict]:
    """Build the default 3-stage Research → PRD → Coder pipeline.

    This is the standard swarm configuration. Each stage writes its output
    to a file in the shared workspace, which triggers the next stage.

    Args:
        task_description: What the swarm should accomplish.
        research_model: Model for the research stage.
        prd_model: Model for the PRD stage.
        coder_model: Model for the coder stage.

    Returns:
        List of stage definition dicts ready for create_swarm().
    """
    return [
        {
            "name": "research",
            "label": "Research Agent",
            "model": research_model,
            "context_mode": "200k",
            "output_file": "research_report.md",
            "trigger_file": None,  # First stage, no trigger
            "initial_prompt": (
                f"## Research Task\n\n"
                f"{task_description}\n\n"
                f"Your job is to thoroughly research this task. Investigate the codebase, "
                f"understand the architecture, identify relevant files and patterns, "
                f"and produce a comprehensive research report.\n\n"
                f"When you're done, write your complete research report to the shared "
                f"workspace output file. Include:\n"
                f"1. Summary of findings\n"
                f"2. Relevant files and their purposes\n"
                f"3. Architecture patterns identified\n"
                f"4. Recommended approach\n"
                f"5. Potential risks or considerations\n"
            ),
        },
        {
            "name": "prd",
            "label": "PRD Builder Agent",
            "model": prd_model,
            "context_mode": "1m",
            "output_file": "prd.md",
            "trigger_file": "research_report.md",  # Triggered when research completes
            "initial_prompt": (
                f"## PRD Builder Task\n\n"
                f"Original task: {task_description}\n\n"
                f"You will receive a research report from the Research Agent. Based on that "
                f"research, create a detailed PRD (Product Requirements Document) that includes:\n"
                f"1. Overview and goals\n"
                f"2. Technical approach (based on research findings)\n"
                f"3. Detailed implementation steps\n"
                f"4. File changes required (specific files, what to add/modify)\n"
                f"5. Testing strategy\n"
                f"6. Acceptance criteria\n\n"
                f"Write the complete PRD to the shared workspace output file when done.\n"
            ),
        },
        {
            "name": "coder",
            "label": "Coder Agent",
            "model": coder_model,
            "context_mode": "1m",
            "output_file": "implementation_report.md",
            "trigger_file": "prd.md",  # Triggered when PRD completes
            "initial_prompt": (
                f"## Implementation Task\n\n"
                f"Original task: {task_description}\n\n"
                f"You will receive a PRD from the PRD Builder Agent. Your job is to "
                f"implement everything specified in the PRD:\n"
                f"1. Read the PRD carefully\n"
                f"2. Implement all code changes specified\n"
                f"3. Run linters and type checks to verify\n"
                f"4. Write an implementation report to the shared workspace when done\n\n"
                f"The implementation report should include:\n"
                f"- Files created/modified\n"
                f"- Summary of changes\n"
                f"- Any deviations from the PRD and why\n"
                f"- Test results\n"
            ),
        },
    ]
