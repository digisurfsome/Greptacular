"""
Deployment Executor Node — Sandboxed Subprocess Execution
==========================================================

Runs deployment commands in a sandboxed subprocess with:
- Command allowlist validation (SECURITY CRITICAL)
- subprocess.run() with shell=False
- Timeout enforcement
- Output capture

SECURITY: Every command is validated against the allowlist before execution.
Blocked commands are logged with the reason for blocking.
"""

import asyncio
import logging
import subprocess
import time

from . import register_node
from .base_node import BaseExecutionNode, ExecutionResult

logger = logging.getLogger(__name__)

# Command allowlist — only these base commands are permitted
ALLOWED_COMMANDS = {
    "npm", "npx", "node", "python", "python3", "pip", "pip3",
    "git", "docker", "docker-compose",
    "curl", "wget",
    "mkdir", "cp", "mv", "ls", "dir", "echo",
    "tsc", "eslint", "prettier",
    "pytest", "mypy", "ruff",
}

# Blocked patterns — commands that are never allowed regardless of base command
BLOCKED_PATTERNS = [
    "rm -rf /",
    "rm -rf ~",
    "format c:",
    "del /s /q",
    ":(){:|:&};:",  # Fork bomb
    "> /dev/sda",
    "dd if=",
    "mkfs",
    "shutdown",
    "reboot",
]

DEFAULT_TIMEOUT_SECONDS = 60


class DeploymentExecutorNode(BaseExecutionNode):
    """Execute deployment commands in a sandboxed subprocess."""

    async def validate(self, task: dict) -> tuple[bool, str]:
        command = task.get("command", [])
        if not command:
            return False, "Missing required field: command (list of strings)"
        if isinstance(command, str):
            return False, "command must be a list of strings, not a single string"
        if not isinstance(command, list):
            return False, "command must be a list of strings"

        # Validate against allowlist
        base_cmd = command[0].lower().split("/")[-1].split("\\")[-1]
        if base_cmd not in ALLOWED_COMMANDS:
            logger.warning("BLOCKED command: %s (not in allowlist)", command)
            return False, f"Command '{base_cmd}' is not in the allowed commands list"

        # Check for blocked patterns
        full_cmd = " ".join(command).lower()
        for pattern in BLOCKED_PATTERNS:
            if pattern in full_cmd:
                logger.warning("BLOCKED dangerous pattern in command: %s", command)
                return False, f"Command contains blocked pattern: {pattern}"

        return True, ""

    async def execute(self, task: dict) -> ExecutionResult:
        command = task.get("command", [])
        cwd = task.get("cwd")
        timeout = task.get("timeout", DEFAULT_TIMEOUT_SECONDS)
        env_overrides = task.get("env", {})
        start = time.time()

        # Run subprocess in a thread to avoid blocking the event loop
        try:
            result = await asyncio.to_thread(
                self._run_subprocess, command, cwd, timeout, env_overrides
            )
            duration = time.time() - start

            if result["returncode"] == 0:
                return ExecutionResult(
                    status="success",
                    data={
                        "stdout": result["stdout"][:20000],
                        "stderr": result["stderr"][:5000],
                        "returncode": result["returncode"],
                    },
                    metadata={"node_type": "deployment_executor", "command": command},
                    duration=duration,
                )
            else:
                return ExecutionResult(
                    status="failure",
                    data={
                        "stdout": result["stdout"][:20000],
                        "stderr": result["stderr"][:5000],
                        "returncode": result["returncode"],
                    },
                    metadata={"node_type": "deployment_executor", "command": command},
                    error=f"Command exited with code {result['returncode']}: {result['stderr'][:500]}",
                    duration=duration,
                )
        except subprocess.TimeoutExpired:
            return self._failure(
                f"Command timed out after {timeout}s",
                node_type="deployment_executor",
                command=command,
                timeout=timeout,
            )
        except Exception as e:
            return self._failure(
                f"Subprocess execution failed: {e}",
                node_type="deployment_executor",
                command=command,
            )

    def _run_subprocess(
        self,
        command: list[str],
        cwd: str | None,
        timeout: int,
        env_overrides: dict,
    ) -> dict:
        """Run subprocess synchronously (called via asyncio.to_thread)."""
        import os

        env = dict(os.environ)
        env.update(env_overrides)

        result = subprocess.run(
            command,
            cwd=cwd,
            timeout=timeout,
            capture_output=True,
            text=True,
            env=env,
            # NEVER use shell=True for security
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }


# Register at import time
register_node("deploy", DeploymentExecutorNode)
