"""
API Executor Node — External API Calls via Adapter Registry
=============================================================

Dispatches API calls to the correct adapter based on service name.
Implements exponential backoff for rate-limited responses (429).
"""

import asyncio
import logging
import time

from . import register_node
from .base_node import BaseExecutionNode, ExecutionResult

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


class ApiExecutorNode(BaseExecutionNode):
    """Execute API calls through the adapter registry with retry logic."""

    async def validate(self, task: dict) -> tuple[bool, str]:
        service = task.get("service", "")
        if not service:
            return False, "Missing required field: service (e.g. 'google_sheets', 'slack')"
        action = task.get("action", "")
        if not action:
            return False, "Missing required field: action"
        return True, ""

    async def execute(self, task: dict) -> ExecutionResult:
        service = task.get("service", "")
        action = task.get("action", "")
        payload = task.get("payload", {})
        variables = task.get("variables", {})
        start = time.time()

        # Get adapter from registry
        try:
            from ..api_adapters.base import get_adapter

            adapter = get_adapter(service, variables)
            if adapter is None:
                return self._failure(
                    f"Adapter not found for service: {service}",
                    node_type="api_executor",
                    service=service,
                    action=action,
                )

            if not adapter.validate_key():
                return self._failure(
                    f"API key not configured for service: {service}",
                    node_type="api_executor",
                    service=service,
                    action=action,
                    error_category="configuration_error",
                )
        except Exception as e:
            return self._failure(
                f"Failed to load adapter for {service}: {e}",
                node_type="api_executor",
                service=service,
            )

        # Execute with exponential backoff
        last_error = ""
        for attempt in range(MAX_RETRIES):
            try:
                result = await adapter.execute(action, payload)
                return self._success(
                    data=result,
                    node_type="api_executor",
                    service=service,
                    action=action,
                    attempts=attempt + 1,
                )
            except Exception as e:
                last_error = str(e)
                # Check if it's a rate limit error worth retrying
                if "429" in last_error or "rate limit" in last_error.lower():
                    wait_time = 2 ** attempt  # 1s, 2s, 4s
                    logger.warning(
                        "Rate limited by %s (attempt %d/%d), waiting %ds",
                        service, attempt + 1, MAX_RETRIES, wait_time,
                    )
                    await asyncio.sleep(wait_time)
                    continue
                # Non-retryable error
                break

        duration = time.time() - start
        return ExecutionResult(
            status="failure",
            data={},
            metadata={
                "node_type": "api_executor",
                "service": service,
                "action": action,
                "attempts": attempt + 1,
            },
            error=f"API call failed after {MAX_RETRIES} attempts: {last_error}",
            duration=duration,
        )


# Register at import time
register_node("api_call", ApiExecutorNode)
