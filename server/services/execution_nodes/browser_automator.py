"""
Browser Automator Node — JSON-Driven Browser Interactions
==========================================================

Executes sequences of browser actions specified as JSON:
  [
    {"type": "goto", "target": "https://example.com"},
    {"type": "click", "target": "#submit-button"},
    {"type": "fill", "target": "input[name=email]", "value": "test@test.com"},
    {"type": "wait", "target": "#result", "value": "5000"},
    {"type": "screenshot", "value": "result.png"},
    {"type": "extract", "target": ".output-text"}
  ]

Uses PlaywrightManager for browser instance management.
"""

import logging
import time

from . import register_node
from .base_node import BaseExecutionNode, ExecutionResult

logger = logging.getLogger(__name__)

SUPPORTED_ACTIONS = {"goto", "click", "fill", "wait", "screenshot", "extract", "select", "scroll"}


class BrowserAutomatorNode(BaseExecutionNode):
    """Executes JSON action sequences in a browser context."""

    async def validate(self, task: dict) -> tuple[bool, str]:
        actions = task.get("actions", [])
        if not actions:
            return False, "Missing required field: actions (list of action objects)"
        if not isinstance(actions, list):
            return False, "actions must be a list"
        for i, action in enumerate(actions):
            if not isinstance(action, dict):
                return False, f"Action {i} must be a dict"
            action_type = action.get("type", "")
            if action_type not in SUPPORTED_ACTIONS:
                return False, f"Action {i}: unsupported type '{action_type}'. Supported: {SUPPORTED_ACTIONS}"
        return True, ""

    async def execute(self, task: dict) -> ExecutionResult:
        actions = task.get("actions", [])
        start = time.time()
        results: list[dict] = []

        try:
            from . import playwright_manager

            context = await playwright_manager.create_context()
            try:
                page = await context.new_page()

                for i, action in enumerate(actions):
                    action_type = action.get("type", "")
                    target = action.get("target", "")
                    value = action.get("value", "")

                    try:
                        result = await self._execute_action(page, action_type, target, value)
                        results.append({"step": i, "type": action_type, "status": "success", **result})
                    except Exception as e:
                        results.append({"step": i, "type": action_type, "status": "failure", "error": str(e)})
                        # Stop on failure by default
                        if not task.get("continue_on_error", False):
                            return ExecutionResult(
                                status="partial",
                                data={"results": results, "completed_steps": i},
                                metadata={"node_type": "browser_automator", "total_actions": len(actions)},
                                error=f"Action {i} ({action_type}) failed: {e}",
                                duration=time.time() - start,
                            )

                return self._success(
                    data={"results": results, "completed_steps": len(actions)},
                    node_type="browser_automator",
                    total_actions=len(actions),
                )
            finally:
                await context.close()
        except Exception as e:
            return self._failure(
                f"Browser automator failed: {e}",
                node_type="browser_automator",
                total_actions=len(actions),
            )

    async def _execute_action(self, page, action_type: str, target: str, value: str) -> dict:
        """Execute a single browser action. Returns action-specific data."""
        if action_type == "goto":
            await page.goto(target, wait_until="domcontentloaded", timeout=15000)
            return {"url": target}

        elif action_type == "click":
            await page.click(target, timeout=10000)
            return {"target": target}

        elif action_type == "fill":
            await page.fill(target, value, timeout=10000)
            return {"target": target, "value_length": len(value)}

        elif action_type == "wait":
            if target:
                await page.wait_for_selector(target, timeout=int(value or "10000"))
                return {"waited_for": target}
            else:
                await page.wait_for_timeout(int(value or "1000"))
                return {"waited_ms": int(value or "1000")}

        elif action_type == "screenshot":
            path = value or "screenshot.png"
            await page.screenshot(path=path, full_page=True)
            return {"path": path}

        elif action_type == "extract":
            element = await page.query_selector(target)
            if element:
                text = await element.inner_text()
                return {"text": text[:10000]}
            return {"text": "", "note": f"Selector '{target}' not found"}

        elif action_type == "select":
            await page.select_option(target, value, timeout=10000)
            return {"target": target, "value": value}

        elif action_type == "scroll":
            pixels = int(value or "500")
            await page.evaluate(f"window.scrollBy(0, {pixels})")
            return {"scrolled_pixels": pixels}

        return {}


# Register at import time
register_node("browser_action", BrowserAutomatorNode)
