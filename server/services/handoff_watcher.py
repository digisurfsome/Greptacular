"""
Handoff Watcher — monitors agent process exits and checks for handoff files.

When an agent process exits, the watcher checks for .autoforge/handoff.json.
If found, it validates the schema, archives it, and fires a callback to the
Factory Controller so the next agent session can be auto-started.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Awaitable, Optional

logger = logging.getLogger(__name__)


class HandoffWatcher:
    """Watches for agent completion and handoff files."""

    def __init__(
        self,
        project_name: str,
        project_dir: Path,
        on_handoff: Callable[[dict], Awaitable[None]],
        on_exit_no_handoff: Callable[[str], Awaitable[None]],
    ):
        self.project_name = project_name
        self.project_dir = project_dir
        self.on_handoff = on_handoff
        self.on_exit_no_handoff = on_exit_no_handoff
        self.handoff_path = project_dir / ".autoforge" / "handoff.json"
        self._active = False

    async def on_agent_status_change(self, status: str) -> None:
        """Status callback registered with AgentProcessManager.

        Called whenever agent status changes. We only care about
        'stopped' and 'crashed'.
        """
        if not self._active:
            return

        if status in ("stopped", "crashed"):
            handoff = await self.check_for_handoff()
            if handoff:
                logger.info(f"[{self.project_name}] Handoff file found, triggering continuation")
                await self.on_handoff(handoff)
            else:
                logger.info(f"[{self.project_name}] Agent {status} without handoff file")
                await self.on_exit_no_handoff(status)

    async def check_for_handoff(self) -> Optional[dict]:
        """Check for handoff file, validate, and archive."""
        if not self.handoff_path.exists():
            return None

        try:
            raw = self.handoff_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            self._validate_schema(data)
            self._archive(data)
            self.handoff_path.unlink()
            return data
        except json.JSONDecodeError as e:
            logger.error(f"[{self.project_name}] Handoff file is invalid JSON: {e}")
            self._archive_broken(raw if 'raw' in dir() else "")
            return None
        except ValueError as e:
            logger.error(f"[{self.project_name}] Handoff validation failed: {e}")
            return None
        except Exception as e:
            logger.error(f"[{self.project_name}] Error reading handoff file: {e}")
            return None

    def _validate_schema(self, data: dict) -> None:
        """Validate handoff file has required fields."""
        required = ["version", "timestamp", "completed", "next_phase"]
        missing = [f for f in required if f not in data]
        if missing:
            raise ValueError(f"Handoff file missing required fields: {missing}")

        # Validate completed has at least a summary
        if "summary" not in data.get("completed", {}):
            raise ValueError("Handoff 'completed' section must include a 'summary'")

        # Validate next_phase has at least a summary
        if "summary" not in data.get("next_phase", {}):
            raise ValueError("Handoff 'next_phase' section must include a 'summary'")

    def _archive(self, data: dict) -> None:
        """Move handoff to history directory."""
        history_dir = self.project_dir / ".autoforge" / "handoff_history"
        history_dir.mkdir(parents=True, exist_ok=True)

        timestamp = data.get("timestamp", datetime.now(timezone.utc).isoformat())
        # Sanitize timestamp for filename
        safe_ts = timestamp.replace(":", "").replace("+", "").replace("-", "")[:20]
        archive_path = history_dir / f"handoff-{safe_ts}.json"

        # Avoid overwriting
        counter = 1
        while archive_path.exists():
            archive_path = history_dir / f"handoff-{safe_ts}-{counter}.json"
            counter += 1

        archive_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.info(f"[{self.project_name}] Archived handoff to {archive_path.name}")

    def _archive_broken(self, raw_content: str) -> None:
        """Archive a broken handoff file for debugging."""
        history_dir = self.project_dir / ".autoforge" / "handoff_history"
        history_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        archive_path = history_dir / f"handoff-{ts}-BROKEN.txt"
        archive_path.write_text(raw_content, encoding="utf-8")

        # Remove the broken original
        try:
            self.handoff_path.unlink(missing_ok=True)
        except Exception:
            pass

    def activate(self) -> None:
        """Start watching for handoffs."""
        self._active = True
        logger.info(f"[{self.project_name}] Handoff watcher activated")

    def deactivate(self) -> None:
        """Stop watching for handoffs."""
        self._active = False
        logger.info(f"[{self.project_name}] Handoff watcher deactivated")

    @property
    def is_active(self) -> bool:
        return self._active
