"""
DunkStack Shared Hooks
======================

Shared PreToolUse and PreCompact hooks used by both DunkStackCodingSession
and DunkStackChatSession. Extracted to avoid copy-paste duplication.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Any

from claude_agent_sdk.types import SyncHookJSONOutput

logger = logging.getLogger(__name__)


def create_bash_hook_with_context(bash_security_hook: Any, project_dir_str: str):
    """Create a Bash security hook that passes project_dir through to the global bash_security_hook."""

    async def bash_hook_with_context(
        input_data: Any, tool_use_id: Any = None, context: Any = None
    ) -> dict[str, Any]:
        if context is None:
            context = {}
        context["project_dir"] = project_dir_str
        result: dict[str, Any] = await bash_security_hook(input_data, tool_use_id, context)
        return result

    return bash_hook_with_context


def create_pre_compact_hook():
    """Create a PreCompact hook that guides compaction toward file-based recovery."""

    async def pre_compact_hook(
        input_data: Any, tool_use_id: Any = None, context: Any = None
    ) -> SyncHookJSONOutput:
        """Guide compaction to preserve file-based protocol awareness."""
        logger.info("[DunkStack] Context compaction triggered")
        return SyncHookJSONOutput(
            hookSpecificOutput={  # type: ignore[typeddict-item]
                "hookEventName": "PreCompact",
                "customInstructions": (
                    "## DunkStack Compaction Guidelines\n"
                    "After compaction, re-read .agent/index.md and "
                    ".agent/working_memory.md.\n"
                    "These files are the source of truth, not conversation "
                    "history.\n\n"
                    "## DISCARD\n"
                    "- Full file contents from Read results (keep: "
                    "'Read file X')\n"
                    "- Large Grep/Glob outputs (keep: 'Found N matches')\n"
                    "- Verbose Bash output (keep: command + success/failure)\n\n"
                    "## PRESERVE\n"
                    "- Current task and progress state\n"
                    "- Files created or modified (paths only)\n"
                    "- Unresolved errors or blockers\n"
                ),
            }
        )

    return pre_compact_hook


def create_walkie_talkie_hook(project_dir: Path) -> tuple[Any, dict[str, int]]:
    """Create a walkie-talkie PreToolUse hook for file-based messaging.

    Checks .agent/comms/from_human.md for new messages and .agent/comms/control.md
    for session mode (idle/continue/autopilot).

    Args:
        project_dir: The project directory containing .agent/ files.

    Returns:
        Tuple of (hook_function, walkie_state_dict) so the caller can access state.
    """
    walkie_state: dict[str, int] = {"last_size": 0, "idle_count": 0}

    # Seed last_size to current char count so we only inject NEW messages
    from_human_init = project_dir / ".agent" / "comms" / "from_human.md"
    if from_human_init.exists():
        try:
            walkie_state["last_size"] = len(from_human_init.read_text(encoding="utf-8"))
        except Exception:
            pass

    async def walkie_talkie_hook(
        input_data: Any, tool_use_id: Any = None, context: Any = None
    ) -> SyncHookJSONOutput:
        """Check walkie-talkie for new messages and enforce session control."""
        comms_dir = project_dir / ".agent" / "comms"
        from_human_path = comms_dir / "from_human.md"
        control_path = comms_dir / "control.md"

        new_messages: str | None = None
        control_mode = "continue"

        # Check for new messages (compare character count)
        if from_human_path.exists():
            try:
                content = from_human_path.read_text(encoding="utf-8")
                current_size = len(content)
                if current_size > walkie_state["last_size"]:
                    new_content = content[walkie_state["last_size"]:]
                    walkie_state["last_size"] = current_size
                    if new_content.strip():
                        new_messages = new_content.strip()
            except Exception as e:
                logger.debug("Walkie-talkie read error: %s", e)

        # Check control mode
        if control_path.exists():
            try:
                raw = control_path.read_text(encoding="utf-8").strip().lower()
                for line in raw.splitlines():
                    if line.startswith("mode:"):
                        mode_val = line.split(":", 1)[1].strip()
                        if mode_val in ("idle", "continue", "autopilot"):
                            control_mode = mode_val
                        break
            except Exception:
                pass

        # Reset idle backoff when not idle
        if control_mode != "idle":
            walkie_state["idle_count"] = 0

        # IDLE mode: block the tool call and wait with exponential backoff
        if control_mode == "idle":
            reason = (
                "SESSION MODE: IDLE. The human has paused your session. "
                "Do NOT proceed with any work. "
            )
            if new_messages:
                reason += (
                    f"New walkie-talkie message:\n\n{new_messages}\n\n"
                    "Read and acknowledge this message by writing to "
                    ".agent/comms/to_human.md, then wait for mode change."
                )
            else:
                reason += (
                    "Check .agent/comms/control.md periodically. "
                    "Resume work when mode changes to 'continue' or 'autopilot'."
                )
            # Exponential backoff: 10s, 20s, 40s, 60s, 60s, ...
            idle_count = walkie_state.get("idle_count", 0)
            walkie_state["idle_count"] = idle_count + 1
            sleep_secs = min(60, 10 * (2 ** idle_count))
            await asyncio.sleep(sleep_secs)
            return SyncHookJSONOutput(
                hookSpecificOutput={  # type: ignore[typeddict-item]
                    "hookEventName": "PreToolUse",
                    "decision": "block",
                    "reason": reason,
                }
            )

        # AUTOPILOT mode: check if human is actively typing
        if control_mode == "autopilot" and from_human_path.exists():
            try:
                mtime = from_human_path.stat().st_mtime
                if time.time() - mtime < 30:
                    # Human modified file recently — wait briefly
                    await asyncio.sleep(3)
            except Exception:
                pass

        # If there are new messages, block once to inject them
        if new_messages:
            return SyncHookJSONOutput(
                hookSpecificOutput={  # type: ignore[typeddict-item]
                    "hookEventName": "PreToolUse",
                    "decision": "block",
                    "reason": (
                        "WALKIE-TALKIE — NEW MESSAGE FROM HUMAN:\n\n"
                        f"{new_messages}\n\n"
                        "Read and acknowledge this message by writing a response to "
                        ".agent/comms/to_human.md (using the Write tool). "
                        "If the message contains new instructions, adjust your plan. "
                        "Then continue your work."
                    ),
                }
            )

        # No new messages, mode is continue or autopilot — approve
        return SyncHookJSONOutput(
            hookSpecificOutput={  # type: ignore[typeddict-item]
                "hookEventName": "PreToolUse",
                "decision": "approve",
            }
        )

    return walkie_talkie_hook, walkie_state
