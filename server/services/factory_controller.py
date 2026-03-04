"""
Factory Controller — orchestrates multi-phase autonomous builds.

Manages the factory lifecycle: start → agent runs → handoff detected →
auto-restart next agent → repeat until all phases complete or rate limit.

State is persisted to .autoforge/factory_state.json so the factory
survives server restarts.
"""

import asyncio
import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Awaitable, Literal, Optional

from server.services.handoff_watcher import HandoffWatcher

logger = logging.getLogger(__name__)

# Root directory of the AutoForge project (for process_manager)
ROOT_DIR = Path(__file__).parent.parent.parent

# Default handoff instructions template — user can edit this via UI
DEFAULT_HANDOFF_TEMPLATE = """## Context Budget & Handoff Protocol

You are running in Factory Mode. AutoForge will automatically start a new agent
session when you finish, passing along your handoff notes.

### Context Budget
- **WARNING** at {warning_pct}%: Start wrapping up your current task
- **HANDOFF** at {handoff_pct}%: Commit all work and write your handoff
- **HARD STOP** at {stop_pct}%: Stop immediately

### Before Your Session Ends
Call `factory_write_handoff` with:
1. **What you completed** — features done, files created/modified
2. **What the next agent should do** — priority tasks, which features to work on
3. **Known bugs** — anything you found but didn't fix
4. **Dev server state** — was it running? What URL?
5. **Git state** — last commit hash, any uncommitted changes

### Phase Scope
You are working on Phase {phase_num} of {phase_total}.
Your assigned features: {feature_list}
Focus ONLY on these features. Do not work outside your phase scope.

### Visual Verification (for UI features)
After implementing a UI feature:
1. Call `preview_start` to ensure the dev server is running
2. Take a screenshot and check for visual correctness
3. Check console for JavaScript errors
4. Fix any issues, wait for hot reload, re-verify
5. Call `preview_save_screenshot` to record your work

### Git
Commit your work before writing the handoff. Use descriptive commit messages.
"""


class FactoryState:
    """Persisted factory state."""

    def __init__(
        self,
        mode: Literal["continuous", "single"] = "continuous",
        status: Literal["idle", "running", "paused", "waiting_rate_limit", "completed"] = "idle",
        current_phase: int = 0,
        total_phases: int = 0,
        started_at: Optional[str] = None,
        model: str = "claude-opus-4-6",
        yolo_mode: bool = False,
        auto_commit: bool = True,
        rate_limit_strategy: Literal["wait", "stop"] = "wait",
        handoff_threshold: int = 45,
        handoff_template: str = DEFAULT_HANDOFF_TEMPLATE,
        rate_limit: Optional[dict] = None,
        history: Optional[list] = None,
        phases: Optional[list] = None,
    ):
        self.mode = mode
        self.status = status
        self.current_phase = current_phase
        self.total_phases = total_phases
        self.started_at = started_at
        self.model = model
        self.yolo_mode = yolo_mode
        self.auto_commit = auto_commit
        self.rate_limit_strategy = rate_limit_strategy
        self.handoff_threshold = handoff_threshold
        self.handoff_template = handoff_template
        self.rate_limit = rate_limit or {"active": False, "detected_at": None, "resumes_at": None, "queued_phase": None}
        self.history = history or []
        self.phases = phases or []

    def to_dict(self) -> dict:
        return {
            "version": 1,
            "mode": self.mode,
            "status": self.status,
            "current_phase": self.current_phase,
            "total_phases": self.total_phases,
            "started_at": self.started_at,
            "model": self.model,
            "yolo_mode": self.yolo_mode,
            "auto_commit": self.auto_commit,
            "rate_limit_strategy": self.rate_limit_strategy,
            "handoff_threshold": self.handoff_threshold,
            "handoff_template": self.handoff_template,
            "rate_limit": self.rate_limit,
            "history": self.history,
            "phases": self.phases,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FactoryState":
        return cls(
            mode=data.get("mode", "continuous"),
            status=data.get("status", "idle"),
            current_phase=data.get("current_phase", 0),
            total_phases=data.get("total_phases", 0),
            started_at=data.get("started_at"),
            model=data.get("model", "claude-opus-4-6"),
            yolo_mode=data.get("yolo_mode", False),
            auto_commit=data.get("auto_commit", True),
            rate_limit_strategy=data.get("rate_limit_strategy", "wait"),
            handoff_threshold=data.get("handoff_threshold", 45),
            handoff_template=data.get("handoff_template", DEFAULT_HANDOFF_TEMPLATE),
            rate_limit=data.get("rate_limit"),
            history=data.get("history"),
            phases=data.get("phases"),
        )

    @classmethod
    def load(cls, project_dir: Path) -> "FactoryState":
        state_path = project_dir / ".autoforge" / "factory_state.json"
        if state_path.exists():
            try:
                data = json.loads(state_path.read_text(encoding="utf-8"))
                return cls.from_dict(data)
            except Exception as e:
                logger.error(f"Failed to load factory state: {e}")
        return cls()

    def save(self, project_dir: Path) -> None:
        state_path = project_dir / ".autoforge" / "factory_state.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    def get_threshold_levels(self) -> dict:
        """Compute warning/handoff/stop percentages from the handoff_threshold.

        The sequence spans 10 percentage points:
        - WARNING: threshold - 10
        - HANDOFF: threshold - 5
        - HARD STOP: threshold
        """
        t = self.handoff_threshold
        return {
            "warning_pct": max(t - 10, 20),
            "handoff_pct": max(t - 5, 25),
            "stop_pct": t,
        }


class FactoryController:
    """Orchestrates multi-phase autonomous builds."""

    # Maximum retry attempts for a failed phase
    MAX_PHASE_RETRIES = 3
    # Delay between agent exit and next phase start (seconds)
    PHASE_TRANSITION_DELAY = 5
    # Default rate limit cooldown (5 hours in seconds)
    DEFAULT_RATE_LIMIT_COOLDOWN = 18000

    def __init__(self, project_name: str, project_dir: Path):
        self.project_name = project_name
        self.project_dir = project_dir
        self.state = FactoryState.load(project_dir)
        self._phase_retry_count: dict[int, int] = {}
        self._rate_limit_timer: Optional[asyncio.Task] = None
        self._ws_callbacks: list[Callable[[dict], Awaitable[None]]] = []

        # Create the handoff watcher
        self.watcher = HandoffWatcher(
            project_name=project_name,
            project_dir=project_dir,
            on_handoff=self._handle_handoff,
            on_exit_no_handoff=self._handle_exit_no_handoff,
        )

    def add_ws_callback(self, callback: Callable[[dict], Awaitable[None]]) -> None:
        """Register a WebSocket broadcast callback."""
        self._ws_callbacks.append(callback)

    def remove_ws_callback(self, callback: Callable[[dict], Awaitable[None]]) -> None:
        """Remove a WebSocket broadcast callback."""
        try:
            self._ws_callbacks.remove(callback)
        except ValueError:
            pass

    async def _broadcast(self, event: dict) -> None:
        """Send event to all WebSocket subscribers."""
        for cb in self._ws_callbacks:
            try:
                await cb(event)
            except Exception as e:
                logger.error(f"WS broadcast error: {e}")

    async def start(
        self,
        mode: str = "continuous",
        model: str = "claude-opus-4-6",
        yolo_mode: bool = False,
        auto_commit: bool = True,
        rate_limit_strategy: str = "wait",
        start_phase: int = 1,
    ) -> tuple[bool, str]:
        """Start factory mode for the project."""
        if self.state.status == "running":
            return False, "Factory is already running"

        # Load or generate phase plan
        phases = self._load_phases()
        if not phases:
            # Auto-generate minimal phases from features
            phases = await self._generate_default_phases()
            if not phases:
                return False, "No features found — cannot generate phases"

        # Update state
        self.state.mode = mode
        self.state.status = "running"
        self.state.model = model
        self.state.yolo_mode = yolo_mode
        self.state.auto_commit = auto_commit
        self.state.rate_limit_strategy = rate_limit_strategy
        self.state.phases = phases
        self.state.total_phases = len(phases)
        self.state.started_at = datetime.now(timezone.utc).isoformat()

        # Find first incomplete phase
        self.state.current_phase = start_phase
        for phase in phases:
            if phase.get("status") != "completed":
                self.state.current_phase = phase["number"]
                break

        self.state.save(self.project_dir)

        # Activate the handoff watcher
        self.watcher.activate()

        # Register watcher with the process manager
        from server.services.process_manager import get_manager
        manager = get_manager(self.project_name, self.project_dir, ROOT_DIR)
        manager.add_status_callback(self.watcher.on_agent_status_change)

        # Start the first phase
        success, msg = await self._start_phase(self.state.current_phase)
        if not success:
            self.state.status = "idle"
            self.state.save(self.project_dir)
            self.watcher.deactivate()
            return False, f"Failed to start phase {self.state.current_phase}: {msg}"

        await self._broadcast({
            "type": "factory_started",
            "mode": mode,
            "current_phase": self.state.current_phase,
            "total_phases": self.state.total_phases,
        })

        return True, f"Factory started at phase {self.state.current_phase}/{self.state.total_phases}"

    async def stop(self) -> tuple[bool, str]:
        """Stop factory mode, preserving progress."""
        if self.state.status not in ("running", "waiting_rate_limit", "paused"):
            return False, f"Factory is not active (status: {self.state.status})"

        # Stop the current agent
        from server.services.process_manager import get_manager
        manager = get_manager(self.project_name, self.project_dir, ROOT_DIR)

        # Deactivate watcher BEFORE stopping agent so it doesn't trigger restart
        self.watcher.deactivate()
        manager.remove_status_callback(self.watcher.on_agent_status_change)

        await manager.stop()

        # Cancel rate limit timer if active
        if self._rate_limit_timer and not self._rate_limit_timer.done():
            self._rate_limit_timer.cancel()

        # Remove factory prompt file so non-factory agent runs don't inherit
        # stale handoff instructions via the {factory_instructions} placeholder.
        self._cleanup_factory_prompt()

        self.state.status = "idle"
        self.state.save(self.project_dir)

        await self._broadcast({
            "type": "factory_stopped",
            "current_phase": self.state.current_phase,
            "total_phases": self.state.total_phases,
        })

        return True, "Factory stopped"

    async def get_status(self) -> dict:
        """Get full factory status."""
        # Count completed features
        features_completed = 0
        features_total = 0
        for phase in self.state.phases:
            feature_ids = phase.get("features", [])
            features_total += len(feature_ids)
            if phase.get("status") == "completed":
                features_completed += len(feature_ids)

        is_continuous = self._is_continuous_mode()
        return {
            "mode": self.state.mode,
            "status": self.state.status,
            "current_phase": self.state.current_phase,
            "total_phases": self.state.total_phases,
            "phases": self.state.phases,
            "rate_limit": self.state.rate_limit,
            "started_at": self.state.started_at,
            "features_completed": features_completed,
            "features_total": features_total,
            "model": self.state.model,
            "yolo_mode": self.state.yolo_mode,
            "auto_commit": self.state.auto_commit,
            "handoff_threshold": self.state.handoff_threshold,
            "handoff_template": self.state.handoff_template,
            "continuous": is_continuous,
            "session_count": len(self.state.history),
        }

    async def update_settings(
        self,
        handoff_threshold: Optional[int] = None,
        handoff_template: Optional[str] = None,
    ) -> dict:
        """Update factory settings (threshold and/or template)."""
        if handoff_threshold is not None:
            # Clamp to valid range
            self.state.handoff_threshold = max(35, min(55, handoff_threshold))
        if handoff_template is not None:
            self.state.handoff_template = handoff_template
        self.state.save(self.project_dir)
        return {
            "handoff_threshold": self.state.handoff_threshold,
            "handoff_template": self.state.handoff_template,
        }

    def get_rendered_handoff_instructions(self, phase_num: int = 1, phase_total: int = 1, feature_list: str = "") -> str:
        """Render the handoff template with current threshold values."""
        levels = self.state.get_threshold_levels()
        rendered = self.state.handoff_template.format(
            warning_pct=levels["warning_pct"],
            handoff_pct=levels["handoff_pct"],
            stop_pct=levels["stop_pct"],
            phase_num=phase_num,
            phase_total=phase_total,
            feature_list=feature_list or "All pending features",
        )
        # In continuous (phaseless) mode, strip the Phase Scope section
        if self._is_continuous_mode():
            lines = rendered.split("\n")
            filtered = []
            skip = False
            for line in lines:
                if line.strip().startswith("### Phase Scope"):
                    skip = True
                    continue
                if skip and line.strip().startswith("### "):
                    skip = False  # Next section
                if not skip:
                    filtered.append(line)
            rendered = "\n".join(filtered)
        return rendered

    def _get_previous_handoff_summary(self, current_phase: int) -> str | None:
        """Read the most recent handoff archive to pass context to the next agent."""
        if current_phase <= 1:
            return None
        history_dir = self.project_dir / ".autoforge" / "handoff_history"
        if not history_dir.exists():
            return None
        # Find the latest handoff file
        files = sorted(history_dir.glob("handoff-*.json"), reverse=True)
        for f in files:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                parts = []
                completed = data.get("completed", {})
                if completed.get("summary"):
                    parts.append(f"**Completed:** {completed['summary']}")
                next_phase = data.get("next_phase", {})
                if next_phase.get("summary"):
                    parts.append(f"**Next:** {next_phase['summary']}")
                if next_phase.get("priority_tasks"):
                    tasks = "\n".join(f"- {t}" for t in next_phase["priority_tasks"])
                    parts.append(f"**Priority tasks:**\n{tasks}")
                bugs = data.get("current_bugs", [])
                if bugs:
                    bug_lines = "\n".join(f"- {b.get('description', str(b))}" for b in bugs)
                    parts.append(f"**Known bugs:**\n{bug_lines}")
                if parts:
                    return "\n\n".join(parts)
            except Exception:
                continue
        return None

    def _cleanup_factory_prompt(self) -> None:
        """Remove the factory prompt file so non-factory runs stay clean."""
        factory_prompt_path = self.project_dir / ".autoforge" / "factory_prompt.md"
        factory_prompt_path.unlink(missing_ok=True)

    async def _git_auto_commit(self, phase_num: int, handoff_data: dict) -> None:
        """Auto-commit all changes after a phase completes."""
        try:
            summary = handoff_data.get("completed", {}).get("summary", "")
            commit_msg = f"factory: phase {phase_num} complete"
            if summary:
                commit_msg += f" — {summary[:80]}"

            # Run git add + commit in the project directory
            result = subprocess.run(
                ["git", "add", "-A"],
                cwd=str(self.project_dir),
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                logger.warning(f"[{self.project_name}] git add failed: {result.stderr}")
                return

            result = subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=str(self.project_dir),
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                logger.info(f"[{self.project_name}] Auto-committed phase {phase_num}")
                await self._broadcast({
                    "type": "factory_git_commit",
                    "phase": phase_num,
                    "message": commit_msg,
                })
            elif "nothing to commit" in result.stdout:
                logger.info(f"[{self.project_name}] Nothing to commit for phase {phase_num}")
            else:
                logger.warning(f"[{self.project_name}] git commit failed: {result.stderr}")

        except subprocess.TimeoutExpired:
            logger.error(f"[{self.project_name}] Git auto-commit timed out for phase {phase_num}")
        except Exception as e:
            logger.error(f"[{self.project_name}] Git auto-commit failed: {e}")

    # ── Internal methods ──────────────────────────────────────────

    async def _start_phase(self, phase_num: int) -> tuple[bool, str]:
        """Start an agent for the given phase."""
        from server.services.process_manager import get_manager

        # Find the phase data
        phase = None
        for p in self.state.phases:
            if p["number"] == phase_num:
                phase = p
                break

        if not phase:
            return False, f"Phase {phase_num} not found"

        # Mark phase as running
        phase["status"] = "running"
        phase["started_at"] = datetime.now(timezone.utc).isoformat()
        self.state.current_phase = phase_num
        self.state.save(self.project_dir)

        # Write rendered factory instructions so the coding prompt can inject them.
        # The agent subprocess reads this file via prompts.py when loading the
        # coding_prompt template (fills the {factory_instructions} placeholder).
        feature_ids = phase.get("features", [])
        feature_list = ", ".join(f"#{fid}" for fid in feature_ids) if feature_ids else "All pending features"
        rendered_instructions = self.get_rendered_handoff_instructions(
            phase_num=phase_num,
            phase_total=self.state.total_phases,
            feature_list=feature_list,
        )

        # Append phase PRD content if a document exists for this phase number
        phase_prd_path = self.project_dir / ".autoforge" / "phases" / f"{phase_num}.md"
        if phase_prd_path.exists():
            try:
                prd_content = phase_prd_path.read_text(encoding="utf-8").strip()
                if prd_content:
                    rendered_instructions += f"\n\n### Phase {phase_num} PRD\n\n{prd_content}"
                    logger.info(f"[{self.project_name}] Injected phase {phase_num} PRD ({len(prd_content)} chars)")
            except Exception as e:
                logger.warning(f"[{self.project_name}] Failed to read phase PRD {phase_prd_path}: {e}")

        # Include the previous handoff summary so the new agent has context
        prev_handoff = self._get_previous_handoff_summary(phase_num)
        if prev_handoff:
            rendered_instructions += f"\n\n### Previous Agent Handoff Notes\n\n{prev_handoff}"

        factory_prompt_path = self.project_dir / ".autoforge" / "factory_prompt.md"
        factory_prompt_path.parent.mkdir(parents=True, exist_ok=True)
        factory_prompt_path.write_text(rendered_instructions, encoding="utf-8")
        logger.info(f"[{self.project_name}] Wrote factory instructions for phase {phase_num}")

        # Start the agent
        manager = get_manager(self.project_name, self.project_dir, ROOT_DIR)
        success, msg = await manager.start(
            yolo_mode=self.state.yolo_mode,
            model=self.state.model,
        )

        if success:
            await self._broadcast({
                "type": "phase_update",
                "phase": phase_num,
                "status": "running",
                "total_phases": self.state.total_phases,
                "features_in_phase": phase.get("features", []),
            })

        return success, msg

    def _is_continuous_mode(self) -> bool:
        """Check if factory is in phaseless continuous mode (no phase boundaries)."""
        return (
            len(self.state.phases) == 1
            and self.state.phases[0].get("continuous", False)
        )

    async def _handle_handoff(self, handoff_data: dict) -> None:
        """Called by HandoffWatcher when a valid handoff file is found."""
        current_phase = self.state.current_phase
        is_continuous = self._is_continuous_mode()

        # In continuous mode, don't mark the phase completed — just log the handoff
        if not is_continuous:
            for phase in self.state.phases:
                if phase["number"] == current_phase:
                    phase["status"] = "completed"
                    phase["completed_at"] = datetime.now(timezone.utc).isoformat()
                    break

        # Add to history (always, even in continuous mode)
        self.state.history.append({
            "phase": current_phase,
            "status": "handoff" if is_continuous else "completed",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "handoff_summary": handoff_data.get("completed", {}).get("summary", ""),
            "session_number": len(self.state.history) + 1,
        })

        self.state.save(self.project_dir)

        # Git auto-commit after phase completion (if enabled)
        if self.state.auto_commit:
            await self._git_auto_commit(current_phase, handoff_data)

        await self._broadcast({
            "type": "handoff_detected",
            "from_phase": current_phase,
            "to_phase": current_phase if is_continuous else current_phase + 1,
            "summary": handoff_data.get("completed", {}).get("summary", ""),
            "continuous": is_continuous,
            "session_number": len(self.state.history),
        })

        # Check for rate limit in handoff data
        context_info = handoff_data.get("context_usage", {})
        if context_info.get("reason") == "rate_limited":
            next_target = current_phase if is_continuous else current_phase + 1
            await self._handle_rate_limit(next_target)
            return

        # ── Continuous mode: restart same phase ──
        if is_continuous:
            if self.state.mode == "continuous":
                session_num = len(self.state.history) + 1
                logger.info(f"[{self.project_name}] Continuous mode — starting session {session_num} in {self.PHASE_TRANSITION_DELAY}s")
                await asyncio.sleep(self.PHASE_TRANSITION_DELAY)
                if self.state.status != "running":
                    return
                await self._start_phase(current_phase)
            return

        # ── Phased mode: advance to next phase ──
        next_phase = current_phase + 1
        if next_phase > self.state.total_phases:
            # All phases complete
            self.state.status = "completed"
            self.state.save(self.project_dir)
            self.watcher.deactivate()
            self._cleanup_factory_prompt()
            await self._broadcast({
                "type": "factory_complete",
                "total_phases": self.state.total_phases,
            })
            return

        # Auto-start next phase after a short delay
        if self.state.mode == "continuous":
            logger.info(f"[{self.project_name}] Starting phase {next_phase} in {self.PHASE_TRANSITION_DELAY}s")
            await asyncio.sleep(self.PHASE_TRANSITION_DELAY)

            if self.state.status != "running":
                return  # Factory was stopped during delay

            success, msg = await self._start_phase(next_phase)
            if not success:
                logger.error(f"[{self.project_name}] Failed to start phase {next_phase}: {msg}")
                # Retry logic
                retries = self._phase_retry_count.get(next_phase, 0)
                if retries < self.MAX_PHASE_RETRIES:
                    self._phase_retry_count[next_phase] = retries + 1
                    await asyncio.sleep(10)
                    await self._start_phase(next_phase)
        else:
            # Single mode — stop after one phase
            self.state.status = "idle"
            self.state.save(self.project_dir)
            self.watcher.deactivate()
            self._cleanup_factory_prompt()

    async def _handle_exit_no_handoff(self, status: str) -> None:
        """Called when agent exits without a handoff file."""
        current_phase = self.state.current_phase
        is_continuous = self._is_continuous_mode()

        if status == "crashed":
            retries = self._phase_retry_count.get(current_phase, 0)

            if retries < self.MAX_PHASE_RETRIES:
                self._phase_retry_count[current_phase] = retries + 1
                logger.warning(
                    f"[{self.project_name}] Agent crashed without handoff. "
                    f"Retry {retries + 1}/{self.MAX_PHASE_RETRIES} for phase {current_phase}"
                )
                await asyncio.sleep(self.PHASE_TRANSITION_DELAY * (retries + 1))

                if self.state.status == "running":
                    await self._start_phase(current_phase)
            else:
                logger.error(f"[{self.project_name}] Phase {current_phase} failed after {self.MAX_PHASE_RETRIES} retries")
                self.state.status = "idle"
                self.state.save(self.project_dir)
                self.watcher.deactivate()
                self._cleanup_factory_prompt()
                await self._broadcast({
                    "type": "factory_error",
                    "phase": current_phase,
                    "message": f"Phase {current_phase} failed after {self.MAX_PHASE_RETRIES} retries",
                })
        elif is_continuous and self.state.mode == "continuous" and self.state.status == "running":
            # Continuous mode — agent exited cleanly (maybe context limit hit
            # without writing handoff). Restart it.
            logger.info(f"[{self.project_name}] Continuous mode — agent exited without handoff, restarting")
            self.state.history.append({
                "phase": current_phase,
                "status": "restarted",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "handoff_summary": "Agent exited without writing handoff — auto-restarted",
            })
            self.state.save(self.project_dir)
            await asyncio.sleep(self.PHASE_TRANSITION_DELAY)
            if self.state.status == "running":
                await self._start_phase(current_phase)
        else:
            # Agent stopped cleanly without handoff — it's done with everything
            logger.info(f"[{self.project_name}] Agent stopped without handoff — factory complete")
            self.state.status = "completed"
            self.state.save(self.project_dir)
            self.watcher.deactivate()
            self._cleanup_factory_prompt()
            await self._broadcast({
                "type": "factory_complete",
                "total_phases": self.state.total_phases,
            })

    async def _handle_rate_limit(self, queued_phase: int) -> None:
        """Handle rate limit — queue next phase and set timer."""
        cooldown = self.DEFAULT_RATE_LIMIT_COOLDOWN
        resumes_at = datetime.now(timezone.utc).timestamp() + cooldown

        self.state.status = "waiting_rate_limit"
        self.state.rate_limit = {
            "active": True,
            "detected_at": datetime.now(timezone.utc).isoformat(),
            "resumes_at": datetime.fromtimestamp(resumes_at, tz=timezone.utc).isoformat(),
            "queued_phase": queued_phase,
        }
        self.state.save(self.project_dir)

        await self._broadcast({
            "type": "rate_limit_wait",
            "resumes_at": self.state.rate_limit["resumes_at"],
            "cooldown_seconds": cooldown,
            "queued_phase": queued_phase,
        })

        if self.state.rate_limit_strategy == "wait":
            self._rate_limit_timer = asyncio.create_task(
                self._rate_limit_countdown(cooldown, queued_phase)
            )

    async def _rate_limit_countdown(self, cooldown: int, phase: int) -> None:
        """Wait for rate limit to expire, then restart."""
        try:
            await asyncio.sleep(cooldown)
            if self.state.status == "waiting_rate_limit":
                self.state.rate_limit["active"] = False
                self.state.status = "running"
                self.state.save(self.project_dir)
                await self._start_phase(phase)
        except asyncio.CancelledError:
            pass

    def _load_phases(self) -> list[dict]:
        """Load phase plan from file."""
        plan_path = self.project_dir / ".autoforge" / "phase_plan.json"
        if plan_path.exists():
            try:
                data = json.loads(plan_path.read_text(encoding="utf-8"))
                return data.get("phases", [])
            except Exception as e:
                logger.error(f"Failed to load phase plan: {e}")
        return self.state.phases if self.state.phases else []

    async def _generate_default_phases(self) -> list[dict]:
        """Generate a phase plan from features, or a single continuous phase if none exist."""
        # Read features from the database (if it exists)
        features_db = self.project_dir / ".autoforge" / "features.db"
        feature_ids: list[int] = []

        if features_db.exists():
            try:
                from sqlalchemy import create_engine
                from sqlalchemy.orm import Session as SASession
                from api.database import Feature

                engine = create_engine(f"sqlite:///{features_db}", echo=False)
                with SASession(engine) as session:
                    features = session.query(Feature).all()
                    feature_ids = [f.id for f in features]
            except Exception as e:
                logger.error(f"Failed to read features: {e}")

        if feature_ids:
            return [{
                "number": 1,
                "name": "All Features",
                "status": "queued",
                "features": feature_ids,
                "description": f"Implement all {len(feature_ids)} features",
            }]

        # No features — phaseless continuous mode (bug fixes, edits, etc.)
        logger.info(f"[{self.project_name}] No features found — starting in continuous (phaseless) mode")
        return [{
            "number": 1,
            "name": "Continuous",
            "status": "queued",
            "features": [],
            "continuous": True,
            "description": "Continuous factory mode — no phase boundaries",
        }]


# ── Global registry ──────────────────────────────────────────────

_controllers: dict[str, FactoryController] = {}


def get_factory_controller(project_name: str, project_dir: Path) -> FactoryController:
    """Get or create a factory controller for a project."""
    key = f"{project_name}:{project_dir}"
    if key not in _controllers:
        _controllers[key] = FactoryController(project_name, project_dir)
    return _controllers[key]


def get_existing_controller(project_name: str) -> Optional[FactoryController]:
    """Get an existing controller by project name (if any)."""
    for key, ctrl in _controllers.items():
        if key.startswith(f"{project_name}:"):
            return ctrl
    return None
