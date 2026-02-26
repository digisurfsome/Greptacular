"""
Agent OS Spec Generation
=========================

Generates detailed feature specifications from the feature list.
Each spec is a self-contained markdown document that the build agent
consumes to implement one feature.
"""

import logging
import re
from pathlib import Path
from typing import Any, Optional

from .agent_os_file_utils import AgentOSFileUtils

logger = logging.getLogger(__name__)

# ── Spec template ────────────────────────────────────────────────────

SPEC_TEMPLATE = """# Feature {id}: {name}

## Overview
{overview}

## Requirements
### Functional
{functional_requirements}

### Technical
{technical_requirements}

## User Stories
{user_stories}

## Acceptance Criteria
{acceptance_criteria}

## Technical Specification
- **API Endpoints:** {api_endpoints}
- **Data Models:** {data_models}
- **Components:** {components}
- **Dependencies:** {dependencies}
- **Edge Cases:** {edge_cases}

## Standards References
{standards_references}

## Success Metrics
{success_metrics}
"""

# ── Prompt templates ─────────────────────────────────────────────────

SPEC_GENERATION_PROMPT = """Generate a detailed feature specification for the following feature.

## Feature
- ID: {feature_id}
- Name: {feature_name}
- Description: {feature_description}
- Priority: {feature_priority}
- Category: {feature_category}
- Dependencies: {feature_dependencies}

## Product Context
{product_summary}

## Standards
{standards_summary}

## All Features (for cross-referencing)
{all_features_summary}

Generate a COMPLETE spec using this exact format:

# Feature {feature_id}: {feature_name}

## Overview
[1-2 sentence description]

## Requirements
### Functional
1. [User-visible behavior requirement]
2. [...]

### Technical
1. [Architecture/data model/API requirement]
2. [...]

## User Stories
- As a [user type], I want to [action] so that [benefit]

## Acceptance Criteria
- [ ] [Measurable criterion 1]
- [ ] [Measurable criterion 2]

## Technical Specification
- **API Endpoints:** [Routes, methods, request/response]
- **Data Models:** [Fields, types, relationships]
- **Components:** [UI components if applicable]
- **Dependencies:** [Features that must exist first]
- **Edge Cases:** [What to handle]

## Standards References
- See [standards file] for [relevant pattern]

## Success Metrics
[How to measure if this feature works]

Return the FULL spec as markdown. Be specific enough that a build agent can implement this without asking questions.
"""

SPEC_REGENERATION_PROMPT = """Regenerate the following feature specification with improvements.

## Current Spec
{current_spec}

## Feedback / Corrections
{feedback}

Generate the FULL updated spec in the same format. Apply the feedback while keeping all sections complete.
"""


def _slugify(name: str, max_len: int = 30) -> str:
    """Convert a feature name to a URL-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug[:max_len].rstrip("-")


class AgentOSSpecs:
    """Generates detailed feature specifications from the feature list."""

    def __init__(
        self,
        project_dir: Path,
        file_utils: AgentOSFileUtils,
        features: Any,  # AgentOSFeatures — forward ref to avoid circular import
        mechanism: Any,  # AgentOSMechanism
        standards_summary: str = "",
        product_summary: str = "",
    ):
        self.project_dir = project_dir
        self.file_utils = file_utils
        self.features = features
        self.mechanism = mechanism
        self.standards_summary = standards_summary
        self.product_summary = product_summary
        self._generated_specs: dict[int, str] = {}  # feature_id -> spec file path
        self._spec_contents: dict[int, str] = {}  # feature_id -> raw spec content
        self._quality_reports: dict[int, dict[str, Any]] = {}

    # ── Prompt generation ────────────────────────────────────────────

    def get_spec_generation_prompt(self, feature: dict[str, Any]) -> str:
        """Return a prompt for Claude to generate a complete spec for one feature."""
        # Summarize all features for cross-referencing
        all_features = self.features.get_feature_list()
        all_features_summary = "\n".join(
            f"- #{f['id']} {f['name']} ({f['priority']}) — {f['description'][:80]}"
            for f in all_features
        )

        # Format dependencies
        dep_ids = feature.get("dependencies", [])
        dep_names: list[str] = []
        for dep_id in dep_ids:
            dep = self.features.get_feature_by_id(dep_id)
            if dep:
                dep_names.append(f"#{dep_id} {dep['name']}")
        feature_dependencies = ", ".join(dep_names) if dep_names else "None"

        return SPEC_GENERATION_PROMPT.format(
            feature_id=feature["id"],
            feature_name=feature["name"],
            feature_description=feature.get("description", ""),
            feature_priority=feature.get("priority", "should_have"),
            feature_category=feature.get("category", "general"),
            feature_dependencies=feature_dependencies,
            product_summary=self.product_summary or "(No product context)",
            standards_summary=self.standards_summary or "(No standards defined)",
            all_features_summary=all_features_summary or "(No other features)",
        )

    def process_generated_spec(self, feature_id: int, spec_content: str) -> Path:
        """Write Claude's generated spec to .agent/specs/. Returns path."""
        feature = self.features.get_feature_by_id(feature_id)
        feature_name = feature["name"] if feature else f"feature-{feature_id}"
        filename = self.get_spec_filename(feature_id, feature_name)

        path = self.file_utils.write_spec_file(filename, spec_content)
        self._generated_specs[feature_id] = str(path)
        self._spec_contents[feature_id] = spec_content
        logger.info("Generated spec for feature #%d: %s", feature_id, filename)
        return path

    def validate_spec(self, feature_id: int) -> dict[str, Any]:
        """Validate a generated spec for quality. Returns report dict."""
        content = self._spec_contents.get(feature_id)
        if content is None:
            report: dict[str, Any] = {"valid": False, "issues": [{"severity": "error", "message": "No spec content found"}]}
            self._quality_reports[feature_id] = report
            return report

        issues: list[dict[str, str]] = []
        lines = content.split("\n")

        # Check: has at least 1 user story
        has_user_story = any("As a " in line or "as a " in line for line in lines)
        if not has_user_story:
            issues.append({"severity": "warning", "message": "No user stories found (expected 'As a ...')"})

        # Check: has at least 2 acceptance criteria
        criteria_count = sum(1 for line in lines if line.strip().startswith("- [ ]") or line.strip().startswith("- [x]"))
        if criteria_count < 2:
            issues.append({"severity": "warning", "message": f"Only {criteria_count} acceptance criteria (minimum 2)"})

        # Check: references at least 1 standards section
        has_standards_ref = any("standards" in line.lower() or "## Standards References" in line for line in lines)
        if not has_standards_ref:
            issues.append({"severity": "minor", "message": "No standards references found"})

        # Check: not too short
        non_empty_lines = [line for line in lines if line.strip()]
        if len(non_empty_lines) < 20:
            issues.append({"severity": "warning", "message": f"Spec too short ({len(non_empty_lines)} non-empty lines, minimum 20)"})

        # Check: not too long
        if len(non_empty_lines) > 200:
            issues.append({"severity": "minor", "message": f"Spec very long ({len(non_empty_lines)} lines, consider splitting)"})

        # Check: has dependencies section
        has_dependencies = any("Dependencies" in line for line in lines)
        if not has_dependencies:
            issues.append({"severity": "minor", "message": "No dependencies section found"})

        valid = not any(i["severity"] == "error" for i in issues)
        report = {"valid": valid, "issues": issues}
        self._quality_reports[feature_id] = report
        return report

    def get_quality_report(self, feature_id: int) -> dict[str, Any]:
        """Return the quality report from validation."""
        return self._quality_reports.get(feature_id, {"valid": False, "issues": [{"severity": "error", "message": "Not validated yet"}]})

    def get_spec_content(self, feature_id: int) -> Optional[str]:
        """Return the generated spec content for a feature."""
        return self._spec_contents.get(feature_id)

    def get_all_specs(self) -> dict[int, str]:
        """Return all generated specs: {feature_id: file_path}."""
        return dict(self._generated_specs)

    def regenerate_spec(self, feature_id: int, feedback: str) -> str:
        """Return a prompt for Claude to regenerate a spec with user feedback."""
        current_spec = self._spec_contents.get(feature_id, "(No current spec)")
        return SPEC_REGENERATION_PROMPT.format(
            current_spec=current_spec,
            feedback=feedback,
        )

    def get_spec_filename(self, feature_id: int, feature_name: str) -> str:
        """Return the filename for a spec: feature-{id:03d}-{slug}.md."""
        slug = _slugify(feature_name)
        return f"feature-{feature_id:03d}-{slug}.md"
