"""
Computer Use Module for Exploratory QA
=======================================

Uses Claude's Computer Use capability for visual, exploratory testing
after the QA agent completes. This module manages the Computer Use API
interaction with budget controls.

The Computer Use agent navigates the application like a human user would,
taking screenshots and interacting with the UI to find visual bugs,
layout issues, and UX problems that programmatic tests might miss.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from prompts import load_prompt

# Budget tracking
DEFAULT_BUDGET_USD = 5.0
MAX_BUDGET_USD = 10.0

# Approximate cost per Computer Use API call (conservative estimate)
APPROX_COST_PER_CALL_USD = 0.05


class ComputerUseBudget:
    """Track Computer Use API spend against a budget limit.

    Provides a simple spend-tracking mechanism with configurable budget
    ceiling. The budget is clamped to [1.0, MAX_BUDGET_USD] on creation
    to prevent accidental over-spend or zero-budget sessions.
    """

    def __init__(self, budget_usd: float = DEFAULT_BUDGET_USD):
        self.budget_usd = min(max(budget_usd, 1.0), MAX_BUDGET_USD)
        self.spent_usd = 0.0
        self.call_count = 0

    def can_spend(self, amount: float = APPROX_COST_PER_CALL_USD) -> bool:
        """Check if there's budget remaining for another call."""
        return (self.spent_usd + amount) <= self.budget_usd

    def record_spend(self, amount: float = APPROX_COST_PER_CALL_USD) -> None:
        """Record a spend against the budget."""
        self.spent_usd += amount
        self.call_count += 1

    @property
    def remaining(self) -> float:
        """Remaining budget in USD."""
        return max(0.0, self.budget_usd - self.spent_usd)

    @property
    def utilization_pct(self) -> float:
        """Budget utilization as a percentage."""
        if self.budget_usd == 0:
            return 100.0
        return (self.spent_usd / self.budget_usd) * 100.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize budget state to a dictionary for report output."""
        return {
            "budget_usd": self.budget_usd,
            "spent_usd": round(self.spent_usd, 4),
            "remaining_usd": round(self.remaining, 4),
            "call_count": self.call_count,
            "utilization_pct": round(self.utilization_pct, 1),
        }


def _build_prompt(
    project_dir: Path,
    app_url: str,
    budget_usd: float,
    scenarios: list[str] | None,
) -> str:
    """Load and populate the Computer Use prompt template.

    Replaces template placeholders (``{{APP_URL}}``, ``{{BUDGET_USD}}``,
    ``{{SCENARIOS}}``) with session-specific values.

    Args:
        project_dir: Project directory (used for prompt fallback chain).
        app_url: URL of the running application to test.
        budget_usd: Maximum API spend for the session.
        scenarios: Specific scenarios to test, or None for all.

    Returns:
        The fully-populated prompt string.
    """
    prompt = load_prompt("computer_use_prompt", project_dir)
    prompt = prompt.replace("{{APP_URL}}", app_url)
    prompt = prompt.replace("{{BUDGET_USD}}", f"${budget_usd:.2f}")

    if scenarios and scenarios != ["all"]:
        scenarios_str = "\n".join(f"- {s}" for s in scenarios)
        prompt = prompt.replace("{{SCENARIOS}}", scenarios_str)
    else:
        prompt = prompt.replace("{{SCENARIOS}}", "- All scenarios (full exploratory testing)")

    return prompt


async def run_computer_use_session(
    project_dir: Path,
    model: str = "claude-opus-4-6",
    budget_usd: float = DEFAULT_BUDGET_USD,
    app_url: str = "http://localhost:3000",
    scenarios: list[str] | None = None,
) -> dict[str, Any]:
    """
    Run a Computer Use exploratory QA session.

    Launches a Computer Use agent that navigates the running application,
    takes screenshots, and reports visual or UX issues. The session is
    bounded by a USD budget to prevent runaway API spend.

    Args:
        project_dir: Project directory.
        model: Model to use (should support Computer Use).
        budget_usd: Maximum API spend in USD (clamped to [1.0, MAX_BUDGET_USD]).
        app_url: URL of the running application to test.
        scenarios: Specific scenarios to test, or None for full exploratory testing.

    Returns:
        Dictionary with session results including findings and budget usage.
        The same data is also written to ``{project_dir}/.autoforge/computer-use-report.json``.
    """
    budget = ComputerUseBudget(budget_usd)

    # Build the prompt from template with session-specific values.
    # The prompt is not yet sent to an API (Computer Use SDK integration pending),
    # but we validate that it loads and populates correctly.
    _build_prompt(project_dir, app_url, budget_usd, scenarios)

    results: dict[str, Any] = {
        "started_at": datetime.now().isoformat(),
        "app_url": app_url,
        "model": model,
        "budget": budget.to_dict(),
        "findings": [],
        "screenshots": [],
        "status": "pending",
    }

    try:
        print("\n[Computer Use] Starting exploratory QA session")
        print(f"[Computer Use] App URL: {app_url}")
        print(f"[Computer Use] Budget: ${budget_usd:.2f}")
        print(f"[Computer Use] Model: {model}")

        # Computer Use integration is a placeholder that will be activated
        # when the Claude Computer Use API becomes available in the Agent SDK.
        # The infrastructure (budget tracking, prompt loading, report generation)
        # is ready for immediate activation.
        #
        # When Computer Use API is available, this section will:
        # 1. Launch a browser session via Computer Use
        # 2. Navigate the app and take screenshots
        # 3. Report visual issues, UX problems, layout bugs
        # 4. Track spend against the budget and stop when exhausted
        # 5. Generate a detailed findings report

        results["status"] = "skipped"
        results["message"] = "Computer Use API integration pending SDK support"
        print("[Computer Use] Computer Use API not yet available in Agent SDK")
        print("[Computer Use] Infrastructure is ready - enable when SDK supports Computer Use")

    except Exception as e:
        results["status"] = "error"
        results["error"] = str(e)
        print(f"[Computer Use] Error: {e}")

    results["completed_at"] = datetime.now().isoformat()
    results["budget"] = budget.to_dict()

    # Write report to the project's .autoforge directory
    report_path = project_dir / ".autoforge" / "computer-use-report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"[Computer Use] Report written to {report_path}")

    return results
