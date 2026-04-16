"""
Base Execution Node — Abstract base class and ExecutionResult schema.
=====================================================================

All 5 execution nodes inherit from BaseExecutionNode and return
ExecutionResult instances. This ensures consistent error reporting
for the tool analyzer's gap detection pipeline.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ExecutionResult:
    """Standardized result from any execution node.

    Fields:
        status: 'success', 'failure', or 'partial'
        data: Execution output data (node-specific)
        metadata: Additional context (node_type, timing, retries, etc.)
        error: Error description if status != 'success'
        duration: Execution duration in seconds
        started_at: ISO timestamp when execution began
        completed_at: ISO timestamp when execution ended
    """
    status: str  # 'success' | 'failure' | 'partial'
    data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    duration: float = 0.0
    started_at: str = ""
    completed_at: str = ""


class BaseExecutionNode(ABC):
    """Abstract base for all execution nodes.

    Subclasses must implement:
        execute(task) -> ExecutionResult
        validate(task) -> (valid, error_message)
    """

    @abstractmethod
    async def execute(self, task: dict) -> ExecutionResult:
        """Execute the task and return a standardized result.

        Must ALWAYS return an ExecutionResult, even on failure.
        Failure results must include enough context for gap detection:
        what was attempted, which service/URL/command, and why it failed.
        """
        ...

    @abstractmethod
    async def validate(self, task: dict) -> tuple[bool, str]:
        """Validate task parameters before execution.

        Returns:
            (True, "") if valid
            (False, "error description") if invalid
        """
        ...

    def _result(
        self,
        status: str,
        data: dict | None = None,
        error: str | None = None,
        **meta: Any,
    ) -> ExecutionResult:
        """Helper to build an ExecutionResult with timestamp."""
        return ExecutionResult(
            status=status,
            data=data or {},
            metadata=meta,
            error=error,
            completed_at=datetime.now(timezone.utc).isoformat(),
        )

    def _failure(self, error: str, **meta: Any) -> ExecutionResult:
        """Shorthand for creating a failure result with context."""
        return self._result("failure", error=error, **meta)

    def _success(self, data: dict | None = None, **meta: Any) -> ExecutionResult:
        """Shorthand for creating a success result."""
        return self._result("success", data=data, **meta)
