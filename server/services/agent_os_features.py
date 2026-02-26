"""
Agent OS Feature Extraction & Gap Analysis
============================================

Extracts features from the Product layer, categorizes by priority,
identifies dependencies, and runs cross-layer gap analysis between
Standards, Product, and Features.
"""

import json
import logging
from pathlib import Path
from typing import Any, Optional

from .agent_os_file_utils import AgentOSFileUtils

logger = logging.getLogger(__name__)

# Feature priority levels
PRIORITY_LEVELS = ["must_have", "should_have", "nice_to_have"]

# Feature complexity estimates
COMPLEXITY_LEVELS = ["small", "medium", "large"]

# Gap severity levels
GAP_SEVERITIES = ["blocking", "important", "minor"]

# ── Prompt templates ─────────────────────────────────────────────────

FEATURE_EXTRACTION_PROMPT = """Analyze the following product context and extract a complete feature list.

## Product Context
{product_summary}

## Extracted Entities
{entities_json}

## Product Documents
{product_files_content}

## Standards Summary
{standards_summary}

For each feature, determine:
1. A clear, concise name
2. A 1-2 sentence description
3. Priority: must_have (MVP), should_have (v1.1), nice_to_have (future)
4. Complexity: small (< 1 hour agent work), medium (1-3 hours), large (3+ hours)
5. Category: auth, ui, data, api, infrastructure, integration, etc.
6. Dependencies: which other features (by name) must exist first
7. Source: which product document or entity this feature derives from

Return ONLY valid JSON array:
[
  {{
    "name": "<feature name>",
    "description": "<1-2 sentences>",
    "priority": "<must_have|should_have|nice_to_have>",
    "complexity": "<small|medium|large>",
    "category": "<category>",
    "dependencies": ["<dependency feature name>"],
    "source": "<which document/entity>"
  }}
]

Order features by build priority (must_have first, dependencies before dependents).
"""

GAP_ANALYSIS_PROMPT = """Analyze the following project context for gaps, contradictions, and missing information.

## Standards Summary
{standards_summary}

## Product Summary
{product_summary}

## Feature List
{features_json}

Check for these gap types:
1. **missing_detail** — A feature references something not fully defined
2. **contradiction** — Two pieces of context conflict with each other
3. **unstated_dep** — A feature implicitly requires something not in the feature list
4. **standards_conflict** — A feature conflicts with the defined standards
5. **scope_creep** — The feature set is overly ambitious for MVP

For each gap found, provide:
- type: one of the types above
- severity: blocking (must fix before specs), important (should fix), minor (note but don't block)
- message: clear description of the gap
- layers: which layers are involved ["standards", "product", "features"]
- recommendation: what to do about it
- confidence: 0.0-1.0 how confident you are in the recommendation

Return ONLY valid JSON array:
[
  {{
    "type": "<gap type>",
    "severity": "<blocking|important|minor>",
    "message": "<description>",
    "layers": ["<layer1>", "<layer2>"],
    "recommendation": "<what to do>",
    "confidence": <0.0-1.0>
  }}
]
"""


# Priority sort order for features
_PRIORITY_ORDER = {p: i for i, p in enumerate(PRIORITY_LEVELS)}


class AgentOSFeatures:
    """Feature extraction from Product layer and cross-layer gap analysis."""

    def __init__(
        self,
        project_dir: Path,
        file_utils: AgentOSFileUtils,
        entities: dict[str, Any],
        config: dict[str, Any],
    ):
        self.project_dir = project_dir
        self.file_utils = file_utils
        self.entities = entities
        self.config = config  # The agent_os section of config.yml
        self._features: list[dict[str, Any]] = []
        self._gaps: list[dict[str, Any]] = []
        self._next_feature_id: int = 1
        self._next_gap_id: int = 1

    # ── Feature extraction ───────────────────────────────────────────

    def get_feature_extraction_prompt(self) -> str:
        """Return a prompt for Claude to extract features from product context."""
        # Gather product file contents
        product_files = self.file_utils.list_files_in_layer("product")
        product_content_parts: list[str] = []
        for f in product_files:
            content = self.file_utils.read_product_file(f["name"])
            if content:
                product_content_parts.append(f"### {f['name']}\n{content}")

        product_files_content = "\n\n".join(product_content_parts) if product_content_parts else "(No product documents)"

        # Get standards summary
        standards_files = self.file_utils.list_files_in_layer("standards")
        standards_parts: list[str] = []
        for f in standards_files:
            content = self.file_utils.read_standards_file(f["name"])
            if content:
                standards_parts.append(f"### {f['name']}\n{content}")
        standards_summary = "\n\n".join(standards_parts) if standards_parts else "(No standards defined)"

        # Format entities
        entities_json = json.dumps(self.entities, indent=2, default=str)

        # Product summary from entities
        product_summary_parts: list[str] = []
        if self.entities.get("product_name"):
            product_summary_parts.append(f"Product: {self.entities['product_name']}")
        if self.entities.get("product_description"):
            product_summary_parts.append(f"Description: {self.entities['product_description']}")
        if self.entities.get("problem_statement"):
            product_summary_parts.append(f"Problem: {self.entities['problem_statement']}")
        product_summary = "\n".join(product_summary_parts) if product_summary_parts else "(No product summary)"

        return FEATURE_EXTRACTION_PROMPT.format(
            product_summary=product_summary,
            entities_json=entities_json,
            product_files_content=product_files_content,
            standards_summary=standards_summary,
        )

    def process_extracted_features(self, features_json: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Process Claude's extracted features: assign IDs, validate, store."""
        processed: list[dict[str, Any]] = []

        # Build a name→id mapping for dependency resolution
        name_to_id: dict[str, int] = {}

        for raw in features_json:
            feature: dict[str, Any] = {
                "id": self._next_feature_id,
                "name": raw.get("name", "Unnamed Feature"),
                "description": raw.get("description", ""),
                "priority": raw.get("priority", "should_have") if raw.get("priority") in PRIORITY_LEVELS else "should_have",
                "complexity": raw.get("complexity", "medium") if raw.get("complexity") in COMPLEXITY_LEVELS else "medium",
                "category": raw.get("category", "general"),
                "dependencies": [],  # Resolved below
                "source": raw.get("source", ""),
            }
            name_to_id[feature["name"]] = feature["id"]
            processed.append(feature)
            self._next_feature_id += 1

        # Resolve named dependencies to IDs
        for i, raw in enumerate(features_json):
            raw_deps = raw.get("dependencies", [])
            if isinstance(raw_deps, list):
                resolved_ids: list[int] = []
                for dep_name in raw_deps:
                    if isinstance(dep_name, str) and dep_name in name_to_id:
                        dep_id = name_to_id[dep_name]
                        # Don't allow self-dependency
                        if dep_id != processed[i]["id"]:
                            resolved_ids.append(dep_id)
                    elif isinstance(dep_name, int):
                        resolved_ids.append(dep_name)
                processed[i]["dependencies"] = resolved_ids

        self._features = processed
        logger.info("Processed %d features", len(processed))
        return processed

    def add_feature(self, feature: dict[str, Any]) -> dict[str, Any]:
        """Manually add a feature. Assigns ID, stores, returns."""
        new_feature: dict[str, Any] = {
            "id": self._next_feature_id,
            "name": feature.get("name", "Unnamed Feature"),
            "description": feature.get("description", ""),
            "priority": feature.get("priority", "should_have") if feature.get("priority") in PRIORITY_LEVELS else "should_have",
            "complexity": feature.get("complexity", "medium") if feature.get("complexity") in COMPLEXITY_LEVELS else "medium",
            "category": feature.get("category", "general"),
            "dependencies": feature.get("dependencies", []),
            "source": feature.get("source", "manual"),
        }
        self._next_feature_id += 1
        self._features.append(new_feature)
        logger.info("Added feature: %s (id=%d)", new_feature["name"], new_feature["id"])
        return new_feature

    def remove_feature(self, feature_id: int) -> bool:
        """Remove a feature by ID. Also removes it from other features' dependencies."""
        original_len = len(self._features)
        self._features = [f for f in self._features if f["id"] != feature_id]

        if len(self._features) == original_len:
            return False

        # Clean up dependency references
        for f in self._features:
            if feature_id in f.get("dependencies", []):
                f["dependencies"] = [d for d in f["dependencies"] if d != feature_id]

        logger.info("Removed feature id=%d", feature_id)
        return True

    def update_feature(self, feature_id: int, updates: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Update a feature's fields. Returns updated feature or None."""
        for f in self._features:
            if f["id"] == feature_id:
                for key, value in updates.items():
                    if key == "id":
                        continue  # Never update the ID
                    if key == "priority" and value not in PRIORITY_LEVELS:
                        continue
                    if key == "complexity" and value not in COMPLEXITY_LEVELS:
                        continue
                    f[key] = value
                return f
        return None

    def get_feature_list(self) -> list[dict[str, Any]]:
        """Return features sorted by priority (must_have first) then by ID."""
        return sorted(
            self._features,
            key=lambda f: (_PRIORITY_ORDER.get(f.get("priority", "nice_to_have"), 99), f["id"]),
        )

    def get_feature_by_id(self, feature_id: int) -> Optional[dict[str, Any]]:
        """Return a single feature by ID."""
        for f in self._features:
            if f["id"] == feature_id:
                return f
        return None

    # ── Gap analysis ─────────────────────────────────────────────────

    def get_gap_analysis_prompt(self) -> str:
        """Return a prompt for Claude to run gap analysis across all layers."""
        # Standards summary
        standards_files = self.file_utils.list_files_in_layer("standards")
        standards_parts: list[str] = []
        for f in standards_files:
            content = self.file_utils.read_standards_file(f["name"])
            if content:
                standards_parts.append(f"### {f['name']}\n{content}")
        standards_summary = "\n\n".join(standards_parts) if standards_parts else "(No standards)"

        # Product summary
        product_files = self.file_utils.list_files_in_layer("product")
        product_parts: list[str] = []
        for f in product_files:
            content = self.file_utils.read_product_file(f["name"])
            if content:
                product_parts.append(f"### {f['name']}\n{content}")
        product_summary = "\n\n".join(product_parts) if product_parts else "(No product docs)"

        # Feature list
        features_json = json.dumps(self.get_feature_list(), indent=2, default=str)

        return GAP_ANALYSIS_PROMPT.format(
            standards_summary=standards_summary,
            product_summary=product_summary,
            features_json=features_json,
        )

    def process_gap_analysis(self, gaps_json: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Process Claude's gap analysis output. Assigns IDs, applies thresholds."""
        auto_select_threshold = self.config.get("auto_select_threshold", 85) / 100.0
        processed: list[dict[str, Any]] = []

        for raw in gaps_json:
            gap_type = raw.get("type", "missing_detail")
            severity = raw.get("severity", "minor")
            confidence = float(raw.get("confidence", 0.0))

            gap: dict[str, Any] = {
                "id": self._next_gap_id,
                "type": gap_type,
                "severity": severity if severity in GAP_SEVERITIES else "minor",
                "message": raw.get("message", ""),
                "layers": raw.get("layers", []),
                "recommendation": raw.get("recommendation", ""),
                "confidence": max(0.0, min(1.0, confidence)),
                "auto_fillable": confidence >= auto_select_threshold,
                "resolved": False,
                "resolution": None,
            }
            processed.append(gap)
            self._next_gap_id += 1

        self._gaps = processed
        logger.info("Processed %d gaps (%d auto-fillable)", len(processed), sum(1 for g in processed if g["auto_fillable"]))
        return processed

    def get_blocking_gaps(self) -> list[dict[str, Any]]:
        """Return only unresolved blocking gaps."""
        return [g for g in self._gaps if g["severity"] == "blocking" and not g["resolved"]]

    def get_all_gaps(self) -> list[dict[str, Any]]:
        """Return all gaps sorted by severity (blocking first)."""
        severity_order = {s: i for i, s in enumerate(GAP_SEVERITIES)}
        return sorted(self._gaps, key=lambda g: severity_order.get(g.get("severity", "minor"), 99))

    def resolve_gap(self, gap_id: int, resolution: str) -> Optional[dict[str, Any]]:
        """Mark a gap as resolved with the given resolution text."""
        for g in self._gaps:
            if g["id"] == gap_id:
                g["resolved"] = True
                g["resolution"] = resolution
                logger.info("Resolved gap id=%d", gap_id)
                return g
        return None

    def auto_resolve_gaps(self) -> list[dict[str, Any]]:
        """Auto-resolve all gaps where auto_fillable is True."""
        resolved: list[dict[str, Any]] = []
        for g in self._gaps:
            if g["auto_fillable"] and not g["resolved"]:
                g["resolved"] = True
                g["resolution"] = g["recommendation"]
                resolved.append(g)
        logger.info("Auto-resolved %d gaps", len(resolved))
        return resolved

    def has_blocking_gaps(self) -> bool:
        """Return True if any unresolved blocking gaps exist."""
        return len(self.get_blocking_gaps()) > 0

    def get_feature_count_by_priority(self) -> dict[str, int]:
        """Return feature counts per priority level."""
        counts: dict[str, int] = {p: 0 for p in PRIORITY_LEVELS}
        for f in self._features:
            priority = f.get("priority", "nice_to_have")
            if priority in counts:
                counts[priority] += 1
        return counts
