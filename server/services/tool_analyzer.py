"""Tool Analyzer — checks whether tool steps can execute with available components.

Two analysis levels:
  1. Quick Check — fast keyword matching (handles 80%+ of cases)
  2. Gap Analysis — extends quick check with build plans for missing components
"""

from __future__ import annotations

import logging

from pydantic import BaseModel, Field

from .component_registry import (
    ComponentMatch,
    ComponentStatus,
    get_component_registry,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result models
# ---------------------------------------------------------------------------

class StepDetail(BaseModel):
    """Analysis result for a single step."""
    step: int
    title: str
    components: list[str] = Field(default_factory=list)
    status: str = "unknown"  # "ready", "blocked", "partial"
    missing: list[str] = Field(default_factory=list)


class QuickCheckResult(BaseModel):
    """Result of a quick readiness check."""
    tool_name: str
    total_steps: int
    executable_steps: int = 0
    blocked_steps: int = 0
    pass_check: bool = Field(default=False, alias="pass")
    coverage_pct: float = 0.0
    details: list[StepDetail] = Field(default_factory=list)
    missing_components: list[str] = Field(default_factory=list)
    recommendation: str = ""

    model_config = {"populate_by_name": True}


class BuildPlan(BaseModel):
    """Plan for building a missing component."""
    component_name: str
    difficulty: int = Field(ge=1, le=10)
    description: str = ""
    files_to_create: list[str] = Field(default_factory=list)
    integration_point: str = ""


class GapAnalysisResult(QuickCheckResult):
    """Extended analysis with build plans for missing components."""
    build_plans: list[BuildPlan] = Field(default_factory=list)
    priority_order: list[str] = Field(default_factory=list)
    impact_summary: str = ""


# ---------------------------------------------------------------------------
# Build plan templates for known components
# ---------------------------------------------------------------------------

_BUILD_PLAN_TEMPLATES: dict[str, dict] = {
    "openai_api": {
        "difficulty": 3,
        "description": "Add OpenAI API client for GPT/DALL-E calls",
        "files_to_create": ["server/services/openai_client.py"],
        "integration_point": "Tool execution engine step handler",
    },
    "google_sheets_deploy": {
        "difficulty": 2,
        "description": "Already built — just needs Google OAuth connection",
        "files_to_create": [],
        "integration_point": "Tool Factory deploy flow",
    },
    "playwright_browser": {
        "difficulty": 4,
        "description": "Install playwright and create browser automation wrapper",
        "files_to_create": ["server/services/browser_executor.py"],
        "integration_point": "Tool execution engine step handler",
    },
    "computer_use": {
        "difficulty": 7,
        "description": "Integrate Claude Computer Use for GUI automation",
        "files_to_create": [
            "server/services/computer_use_executor.py",
            "server/services/screen_capture.py",
        ],
        "integration_point": "Requires Claude API with computer_use beta flag",
    },
    "webhook_output": {
        "difficulty": 2,
        "description": "HTTP POST to webhook URLs — mostly built-in",
        "files_to_create": ["server/services/webhook_sender.py"],
        "integration_point": "Tool execution engine output handler",
    },
    "file_creation": {
        "difficulty": 1,
        "description": "File I/O is built-in — just wire to execution engine",
        "files_to_create": [],
        "integration_point": "Tool execution engine output handler",
    },
    "cli_execution": {
        "difficulty": 2,
        "description": "CLI execution via security.py allowlist",
        "files_to_create": [],
        "integration_point": "Already available via agent bash tool",
    },
    "email_send": {
        "difficulty": 4,
        "description": "Email sending via SendGrid or SMTP",
        "files_to_create": ["server/services/email_sender.py"],
        "integration_point": "Tool execution engine action handler",
    },
    "web_search": {
        "difficulty": 2,
        "description": "Web search via Claude CLI built-in capability",
        "files_to_create": [],
        "integration_point": "Available via Claude agent web search tool",
    },
    "claude_api": {
        "difficulty": 1,
        "description": "Claude API access — already built into the system",
        "files_to_create": [],
        "integration_point": "Core system capability",
    },
}


# ---------------------------------------------------------------------------
# Analyzer
# ---------------------------------------------------------------------------

def _build_step_text(step: dict) -> str:
    """Combine step fields into a single searchable string."""
    parts = [
        step.get("title", ""),
        step.get("description", ""),
        step.get("prompt", ""),
        step.get("expectedOutput", ""),
        step.get("notes", ""),
    ]
    return " ".join(p for p in parts if p)


def quick_check(steps: list[dict], tool_name: str = "") -> QuickCheckResult:
    """Run a fast keyword-based readiness check against the component registry.

    Returns a QuickCheckResult with per-step breakdown and overall coverage.
    """
    registry = get_component_registry()
    all_components = {c.name: c for c in registry.get_all()}

    details: list[StepDetail] = []
    all_missing: set[str] = set()
    executable = 0
    blocked = 0

    for i, step in enumerate(steps):
        step_text = _build_step_text(step)
        title = step.get("title", f"Step {i + 1}")
        matches: list[ComponentMatch] = registry.match_step(step_text)

        if not matches:
            # No component match — assume it's a pure AI generation step (Claude handles it)
            details.append(StepDetail(
                step=i + 1,
                title=title,
                components=["claude_api"],
                status="ready",
                missing=[],
            ))
            executable += 1
            continue

        step_components: list[str] = []
        step_missing: list[str] = []

        for match in matches:
            comp = all_components.get(match.component_name)
            if not comp:
                continue
            step_components.append(match.component_name)
            if comp.status != ComponentStatus.AVAILABLE:
                step_missing.append(match.component_name)
                all_missing.add(match.component_name)

        if step_missing:
            blocked += 1
            status = "blocked"
        else:
            executable += 1
            status = "ready"

        details.append(StepDetail(
            step=i + 1,
            title=title,
            components=step_components,
            status=status,
            missing=step_missing,
        ))

    total = len(steps)
    coverage = (executable / total * 100) if total > 0 else 0
    pass_check = coverage >= 100

    # Build recommendation
    if pass_check:
        recommendation = "All steps can execute with available components. Ready to generate."
    elif coverage >= 75:
        recommendation = (
            f"{len(all_missing)} component(s) missing but {executable}/{total} steps are ready. "
            "You can generate now — blocked steps will need manual handling."
        )
    elif coverage >= 50:
        recommendation = (
            f"Only {executable}/{total} steps ready. Consider building missing components first "
            "or simplifying the strategy."
        )
    else:
        recommendation = (
            f"Low readiness ({coverage:.0f}%). Most steps require components that aren't available. "
            "Run a full gap analysis to see what needs to be built."
        )

    return QuickCheckResult(
        tool_name=tool_name,
        total_steps=total,
        executable_steps=executable,
        blocked_steps=blocked,
        pass_check=pass_check,
        coverage_pct=round(coverage, 1),
        details=details,
        missing_components=sorted(all_missing),
        recommendation=recommendation,
    )


def gap_analysis(steps: list[dict], tool_name: str = "") -> GapAnalysisResult:
    """Run full gap analysis with build plans for missing components.

    Extends quick_check with actionable build plans and priority ordering.
    """
    check = quick_check(steps, tool_name)

    # Build plans for each missing component
    build_plans: list[BuildPlan] = []
    # Track how many steps each missing component would unblock
    impact_count: dict[str, int] = {}

    for comp_name in check.missing_components:
        # Count steps this component appears in as missing
        count = sum(1 for d in check.details if comp_name in d.missing)
        impact_count[comp_name] = count

        template = _BUILD_PLAN_TEMPLATES.get(comp_name, {})
        build_plans.append(BuildPlan(
            component_name=comp_name,
            difficulty=template.get("difficulty", 5),
            description=template.get("description", f"Build {comp_name} integration"),
            files_to_create=template.get("files_to_create", []),
            integration_point=template.get("integration_point", "Tool execution engine"),
        ))

    # Priority: highest impact (most steps unblocked) first, then lowest difficulty
    priority_order = sorted(
        check.missing_components,
        key=lambda n: (-impact_count.get(n, 0), _BUILD_PLAN_TEMPLATES.get(n, {}).get("difficulty", 5)),
    )

    # Impact summary
    if not check.missing_components:
        impact_summary = "No gaps found. All components are available."
    else:
        lines = []
        for name in priority_order:
            count = impact_count.get(name, 0)
            diff = _BUILD_PLAN_TEMPLATES.get(name, {}).get("difficulty", 5)
            lines.append(f"  {name}: unblocks {count} step(s), difficulty {diff}/10")
        impact_summary = "Build priority (highest impact first):\n" + "\n".join(lines)

    return GapAnalysisResult(
        tool_name=check.tool_name,
        total_steps=check.total_steps,
        executable_steps=check.executable_steps,
        blocked_steps=check.blocked_steps,
        pass_check=check.pass_check,
        coverage_pct=check.coverage_pct,
        details=check.details,
        missing_components=check.missing_components,
        recommendation=check.recommendation,
        build_plans=build_plans,
        priority_order=priority_order,
        impact_summary=impact_summary,
    )


def get_coverage_stats() -> dict:
    """Global coverage statistics across all components."""
    registry = get_component_registry()
    all_comps = registry.get_all()
    available = [c for c in all_comps if c.status == ComponentStatus.AVAILABLE]
    configurable = [c for c in all_comps if c.status == ComponentStatus.AVAILABLE_IF_CONFIGURED]
    not_built = [c for c in all_comps if c.status == ComponentStatus.NOT_BUILT]

    total = len(all_comps)
    pct = (len(available) / total * 100) if total > 0 else 0

    return {
        "total_components": total,
        "available": len(available),
        "available_if_configured": len(configurable),
        "not_built": len(not_built),
        "coverage_pct": round(pct, 1),
        "available_names": [c.name for c in available],
        "configurable_names": [c.name for c in configurable],
        "not_built_names": [c.name for c in not_built],
    }
