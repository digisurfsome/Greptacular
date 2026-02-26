"""
Agent OS Feature Expansion
===========================

Adds features to existing Agent OS projects. Cross-references new
features against existing ones, checks for conflicts, updates
dependency graph, and generates specs for new features.
"""

import json
import logging
from pathlib import Path
from typing import Any, Optional

from .agent_os_file_utils import AgentOSFileUtils

logger = logging.getLogger(__name__)

# ── Prompt templates ─────────────────────────────────────────────────

EXPANSION_PROMPT = """Extract new features from the following user description.

## Existing Features (do NOT duplicate these)
{existing_features}

## Product Summary
{product_summary}

## Standards Summary
{standards_summary}

## User Description of New Features
{user_input}

For each NEW feature (not already in the existing list), provide:
1. name — concise, unique name
2. description — 1-2 sentences
3. priority — must_have | should_have | nice_to_have
4. complexity — small | medium | large
5. category — auth, ui, data, api, infrastructure, integration, etc.
6. dependencies — list of existing feature names this depends on
7. reason — why this feature is needed

Return ONLY valid JSON array:
[
  {{
    "name": "<name>",
    "description": "<description>",
    "priority": "<priority>",
    "complexity": "<complexity>",
    "category": "<category>",
    "dependencies": ["<existing feature name>"],
    "reason": "<why needed>"
  }}
]
"""

CONFLICT_CHECK_PROMPT = """Analyze these NEW features against the EXISTING feature set for conflicts.

## Existing Features
{existing_features}

## New Features Being Added
{new_features}

Check for:
1. **Conflicts** — Does a new feature contradict or break an existing one?
2. **Required changes** — Would adding this require modifying an existing spec?
3. **New dependencies** — Which existing features must this new feature depend on?

Return ONLY valid JSON:
{{
  "conflicts": [
    {{
      "new_feature": "<name>",
      "existing_feature": "<name>",
      "description": "<what conflicts>",
      "severity": "blocking|warning"
    }}
  ],
  "required_changes": [
    {{
      "existing_feature": "<name>",
      "change": "<what needs to change>",
      "reason": "<why>"
    }}
  ],
  "new_dependencies": [
    {{
      "new_feature": "<name>",
      "depends_on": "<existing feature name>",
      "reason": "<why>"
    }}
  ]
}}
"""


class AgentOSExpand:
    """Feature addition engine for existing Agent OS projects."""

    def __init__(
        self,
        project_dir: Path,
        file_utils: AgentOSFileUtils,
        features: Any,  # AgentOSFeatures
        specs: Any,  # AgentOSSpecs
        handoff: Any,  # AgentOSHandoff
        config: dict[str, Any],
    ):
        self.project_dir = project_dir
        self.file_utils = file_utils
        self.features = features
        self.specs = specs
        self.handoff = handoff
        self.config = config
        self.max_features_per_expansion = config.get("max_features_per_expansion", 5)
        self._last_expansion: Optional[dict[str, Any]] = None

    # ── Prompt generation ────────────────────────────────────────────

    def get_expansion_prompt(self, user_input: str) -> str:
        """Return a prompt for Claude to extract new features from user input.

        Includes the existing feature list (to avoid duplication), product
        summary, and standards summary so Claude has full context.
        """
        feature_list = self.features.get_feature_list()
        existing_lines = "\n".join(
            f"- #{f['id']} {f['name']} ({f.get('priority', '?')}) — {f.get('description', '')[:80]}"
            for f in feature_list
        ) or "(No existing features)"

        # Standards summary — first 3 non-empty lines per file
        standards_files = self.file_utils.list_files_in_layer("standards")
        standards_parts: list[str] = []
        for f in standards_files:
            content = self.file_utils.read_standards_file(f["name"])
            if content:
                lines = [line for line in content.split("\n") if line.strip()][:3]
                standards_parts.append(f"**{f['name']}:** {' | '.join(lines)}")
        standards_summary = "\n".join(standards_parts) if standards_parts else "(No standards)"

        # Product summary — first 3 non-empty lines per file
        product_files = self.file_utils.list_files_in_layer("product")
        product_parts: list[str] = []
        for f in product_files:
            content = self.file_utils.read_product_file(f["name"])
            if content:
                lines = [line for line in content.split("\n") if line.strip()][:3]
                product_parts.append(f"**{f['name']}:** {' | '.join(lines)}")
        product_summary = "\n".join(product_parts) if product_parts else "(No product docs)"

        return EXPANSION_PROMPT.format(
            existing_features=existing_lines,
            product_summary=product_summary,
            standards_summary=standards_summary,
            user_input=user_input,
        )

    def get_conflict_check_prompt(self, new_features: list[dict[str, Any]]) -> str:
        """Return a prompt for Claude to check new features against existing ones.

        Detects conflicts, required changes to existing specs, and
        dependencies that new features should declare.
        """
        feature_list = self.features.get_feature_list()
        existing_lines = "\n".join(
            f"- #{f['id']} {f['name']} ({f.get('priority', '?')}) — {f.get('description', '')[:80]}"
            for f in feature_list
        ) or "(No existing features)"

        new_lines = json.dumps(new_features, indent=2, default=str)

        return CONFLICT_CHECK_PROMPT.format(
            existing_features=existing_lines,
            new_features=new_lines,
        )

    # ── Processing ───────────────────────────────────────────────────

    def process_expansion(self, new_features_json: list[dict[str, Any]]) -> dict[str, Any]:
        """Validate new features: check count against limit, detect name conflicts.

        Returns a dict with keys:
        - added: features that passed validation
        - conflicts: features rejected due to name collisions
        - warnings: non-fatal issues (e.g., count trimmed)
        """
        result: dict[str, Any] = {"added": [], "conflicts": [], "warnings": []}

        # Enforce max features per expansion
        if len(new_features_json) > self.max_features_per_expansion:
            result["warnings"].append(
                f"Requested {len(new_features_json)} features but max is "
                f"{self.max_features_per_expansion}. Only first "
                f"{self.max_features_per_expansion} will be added."
            )
            new_features_json = new_features_json[: self.max_features_per_expansion]

        # Check for name conflicts with existing features
        existing_names = {f["name"].lower() for f in self.features.get_feature_list()}

        valid_features: list[dict[str, Any]] = []
        for feat in new_features_json:
            name = feat.get("name", "").strip()
            if not name:
                result["warnings"].append("Skipped feature with empty name")
                continue

            if name.lower() in existing_names:
                result["conflicts"].append({
                    "name": name,
                    "reason": f"Feature '{name}' already exists",
                    "type": "duplicate_name",
                })
                continue

            # Track the name so subsequent features in this batch
            # cannot collide with each other either
            valid_features.append(feat)
            existing_names.add(name.lower())

        result["added"] = valid_features
        return result

    def process_conflict_check(self, conflict_json: dict[str, Any]) -> dict[str, Any]:
        """Process Claude's conflict analysis result.

        Flags any required_changes that affect already-built features
        (passes="passing") as critical — those need explicit approval.
        """
        feature_list = self.features.get_feature_list()
        built_names = {
            f["name"].lower()
            for f in feature_list
            if f.get("passes") == "passing" or f.get("passes") is True
        }

        conflicts = conflict_json.get("conflicts", [])
        required_changes = conflict_json.get("required_changes", [])
        new_dependencies = conflict_json.get("new_dependencies", [])

        # Flag changes to built features prominently
        flagged_changes: list[dict[str, Any]] = []
        for change in required_changes:
            existing_name = change.get("existing_feature", "")
            if existing_name.lower() in built_names:
                change["severity"] = "critical"
                change["warning"] = (
                    f"Feature '{existing_name}' is already BUILT (passing). "
                    f"Modifying it requires explicit approval."
                )
                flagged_changes.append(change)

        return {
            "conflicts": conflicts,
            "required_changes": required_changes,
            "new_dependencies": new_dependencies,
            "flagged_built_feature_changes": flagged_changes,
        }

    # ── Feature addition ─────────────────────────────────────────────

    def add_features(self, features_to_add: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Add validated features via the features service.

        Resolves named dependencies (strings) to feature IDs before adding.
        Returns the added features with their assigned IDs.
        """
        added: list[dict[str, Any]] = []

        # Build name->id mapping for dependency resolution
        existing_name_to_id: dict[str, int] = {
            f["name"].lower(): f["id"] for f in self.features.get_feature_list()
        }

        for feat in features_to_add:
            # Resolve named dependencies to IDs
            raw_deps = feat.get("dependencies", [])
            resolved_deps: list[int] = []
            if isinstance(raw_deps, list):
                for dep in raw_deps:
                    if isinstance(dep, str):
                        dep_id = existing_name_to_id.get(dep.lower())
                        if dep_id is not None:
                            resolved_deps.append(dep_id)
                    elif isinstance(dep, int):
                        resolved_deps.append(dep)

            new_feature = self.features.add_feature({
                "name": feat.get("name", "Unnamed"),
                "description": feat.get("description", ""),
                "priority": feat.get("priority", "should_have"),
                "complexity": feat.get("complexity", "medium"),
                "category": feat.get("category", "general"),
                "dependencies": resolved_deps,
                "source": "expansion",
            })
            added.append(new_feature)
            # Update mapping so subsequent features can reference this one
            existing_name_to_id[new_feature["name"].lower()] = new_feature["id"]

        self._last_expansion = {"added": added}
        logger.info("Added %d expanded features", len(added))
        return added

    # ── Spec generation ──────────────────────────────────────────────

    def generate_new_specs(self, feature_ids: list[int]) -> list[str]:
        """Return spec generation prompts for each new feature.

        Uses self.specs.get_spec_generation_prompt() to build a prompt
        per feature that Claude can use to generate the full spec.
        """
        prompts: list[str] = []
        for fid in feature_ids:
            feature = self.features.get_feature_by_id(fid)
            if feature:
                prompt = self.specs.get_spec_generation_prompt(feature)
                prompts.append(prompt)
        return prompts

    # ── Dependency & handoff updates ─────────────────────────────────

    def update_dependency_graph(self) -> dict[str, Any]:
        """Regenerate the dependency graph to include new features."""
        result: dict[str, Any] = self.handoff.generate_dependency_graph()
        return result

    def update_scope_boundary(self) -> Path:
        """Regenerate scope boundary with new features included."""
        result: Path = self.handoff.generate_scope_boundary()
        return result

    def recalculate_build_order(self) -> list[int]:
        """Recalculate build order with new features factored in."""
        result: list[int] = self.handoff.calculate_build_order()
        return result

    # ── Summary ──────────────────────────────────────────────────────

    def get_expansion_summary(self) -> str:
        """Return human-readable summary of what was added.

        Includes count of new features, their priorities, dependencies,
        and the updated build order.
        """
        if not self._last_expansion:
            return "No expansion has been performed yet."

        added = self._last_expansion.get("added", [])
        if not added:
            return "Last expansion added no features."

        lines = [
            "## Expansion Summary",
            "",
            f"**Added {len(added)} new feature(s):**",
        ]

        for feat in added:
            deps = feat.get("dependencies", [])
            dep_str = f" (depends on: {', '.join(f'#{d}' for d in deps)})" if deps else ""
            lines.append(
                f"- #{feat['id']} **{feat['name']}** "
                f"[{feat.get('priority', '?')}] "
                f"({feat.get('complexity', '?')}){dep_str}"
            )

        # Build order
        try:
            build_order = self.recalculate_build_order()
            lines.append("")
            lines.append("**Updated build order:**")
            for i, fid in enumerate(build_order, 1):
                feat = self.features.get_feature_by_id(fid)
                if feat:
                    lines.append(f"{i}. #{fid} {feat['name']}")
        except Exception as e:
            lines.append(f"\n(Could not recalculate build order: {e})")

        return "\n".join(lines)
