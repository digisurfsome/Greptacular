"""
Agent OS Handoff
=================

Bridges Agent OS output (specs + features) to DunkStack build input
(features.db + dependency graph + scope boundary). This is the critical
translation layer between the PRD system and the build system.
"""

import logging
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .agent_os_file_utils import AgentOSFileUtils

logger = logging.getLogger(__name__)

# Priority mapping: Agent OS priority names → features.db integer priorities
_PRIORITY_MAP = {"must_have": 1, "should_have": 2, "nice_to_have": 3}

# ── Scope boundary template ─────────────────────────────────────────

SCOPE_BOUNDARY_TEMPLATE = """# Scope Boundary
Generated: {timestamp}
Project: {project_name}

## IN SCOPE — Build These (MVP)
{mvp_features}

## NEXT PHASE — Build After MVP
{next_features}

## FUTURE — Don't Build Yet
{future_features}

## Build Order
{build_order}

## QUALITY BOUNDARY
- Code must work and pass lint. That's the bar for MVP.
- Don't add tests unless the spec requires them
- Don't add documentation beyond code comments
- Don't optimize for edge cases the spec doesn't mention

## STOP SIGNALS
If you find yourself doing any of these, STOP and return to the current task:
- Adding error handling for impossible scenarios
- Refactoring code that already works
- Building a utility/helper for something used once
- Adding configuration for something that has one value
- Writing more than 3 sentences in a chat response
"""


class AgentOSHandoff:
    """Bridges Agent OS output to DunkStack build input."""

    def __init__(
        self,
        project_dir: Path,
        file_utils: AgentOSFileUtils,
        features: Any,  # AgentOSFeatures
        specs: Any,  # AgentOSSpecs
    ):
        self.project_dir = project_dir
        self.file_utils = file_utils
        self.features = features
        self.specs = specs
        self._build_order: list[int] = []
        self._handoff_complete: bool = False
        self._features_db_populated: bool = False
        self._dependencies_set: bool = False
        self._scope_boundary_generated: bool = False

    # ── Database population ──────────────────────────────────────────

    def populate_features_db(self, db_path: Optional[Path] = None) -> int:
        """Create features.db entries from the feature list.

        Returns count of features created.
        """
        from api.database import Base, Feature, create_database

        if db_path is not None:
            # Custom path: create engine directly
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker

            db_path.parent.mkdir(parents=True, exist_ok=True)
            engine = create_engine(f"sqlite:///{db_path.as_posix()}", connect_args={"check_same_thread": False})
            Base.metadata.create_all(bind=engine)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        else:
            _engine, SessionLocal = create_database(self.project_dir)

        feature_list = self.features.get_feature_list()
        count = 0

        session = SessionLocal()
        try:
            for feature in feature_list:
                row_data = self._feature_to_db_row(feature)
                db_feature = Feature(
                    priority=row_data["priority"],
                    category=row_data["category"],
                    name=row_data["name"],
                    description=row_data["description"],
                    steps=row_data["steps"],
                    passes=False,
                    in_progress=False,
                    dependencies=feature.get("dependencies", []) or None,
                )
                session.add(db_feature)
                count += 1

            session.commit()
            self._features_db_populated = True
            self._dependencies_set = True  # Dependencies are set inline
            logger.info("Populated features.db with %d features", count)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

        return count

    def _feature_to_db_row(self, feature: dict[str, Any]) -> dict[str, Any]:
        """Map an Agent OS feature to a features.db row dict."""
        # Extract acceptance criteria from spec to use as 'steps'
        spec_content = self.specs.get_spec_content(feature["id"])
        steps: Any = []

        if spec_content:
            lines = spec_content.split("\n")
            criteria: list[str] = []
            in_criteria = False
            for line in lines:
                if "## Acceptance Criteria" in line:
                    in_criteria = True
                    continue
                if in_criteria and line.startswith("##"):
                    break
                stripped = line.strip()
                if in_criteria and (stripped.startswith("- [ ]") or stripped.startswith("- [x]")):
                    # Strip the checkbox prefix
                    text = stripped[6:].strip() if len(stripped) > 6 else stripped
                    criteria.append(text)
            if criteria:
                steps = criteria

        return {
            "priority": _PRIORITY_MAP.get(feature.get("priority", "should_have"), 2),
            "category": feature.get("category", "general"),
            "name": feature["name"],
            "description": feature.get("description", ""),
            "steps": steps,
        }

    # ── Dependency graph ─────────────────────────────────────────────

    def generate_dependency_graph(self, db_path: Optional[Path] = None) -> dict[str, Any]:
        """Validate and report on the dependency graph.

        Dependencies are already written during populate_features_db.
        This method validates the graph for cycles and returns status.
        """
        feature_list = self.features.get_feature_list()

        # Build feature dicts in the format dependency_resolver expects
        feature_dicts = [
            {"id": f["id"], "dependencies": f.get("dependencies", []), "passes": False}
            for f in feature_list
        ]

        from api.dependency_resolver import resolve_dependencies

        result = resolve_dependencies(feature_dicts)
        has_cycles = len(result["circular_dependencies"]) > 0
        edge_count = sum(len(f.get("dependencies", []) or []) for f in feature_list)

        cycle_info = None
        if has_cycles:
            cycle_info = f"Cycles detected: {result['circular_dependencies']}"

        self._dependencies_set = True
        return {
            "edges": edge_count,
            "valid": not has_cycles,
            "cycle_info": cycle_info,
        }

    def validate_dependency_graph(self) -> dict[str, Any]:
        """Validate the dependency graph without writing it."""
        return self.generate_dependency_graph()

    def calculate_build_order(self) -> list[int]:
        """Topological sort of features by dependencies. Returns feature IDs in build order."""
        feature_list = self.features.get_feature_list()

        feature_dicts = [
            {"id": f["id"], "priority": f.get("priority", 999), "dependencies": f.get("dependencies", []), "passes": False}
            for f in feature_list
        ]

        from api.dependency_resolver import resolve_dependencies

        result = resolve_dependencies(feature_dicts)
        self._build_order = [f["id"] for f in result["ordered_features"]]
        return list(self._build_order)

    # ── Scope boundary ───────────────────────────────────────────────

    def generate_scope_boundary(self) -> Path:
        """Generate .agent/scope_boundary.md from the feature list."""
        feature_list = self.features.get_feature_list()
        timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Get project name from entities or directory name
        project_name = self.project_dir.name

        # Categorize features by priority
        mvp: list[str] = []
        next_phase: list[str] = []
        future: list[str] = []

        for f in feature_list:
            line = f"- #{f['id']} **{f['name']}** — {f.get('description', '')[:80]}"
            priority = f.get("priority", "nice_to_have")
            if priority == "must_have":
                mvp.append(line)
            elif priority == "should_have":
                next_phase.append(line)
            else:
                future.append(line)

        # Build order
        build_order_ids = self._build_order or self.calculate_build_order()
        build_order_lines: list[str] = []
        for i, fid in enumerate(build_order_ids, 1):
            feat = self.features.get_feature_by_id(fid)
            if feat:
                build_order_lines.append(f"{i}. #{fid} {feat['name']}")

        content = SCOPE_BOUNDARY_TEMPLATE.format(
            timestamp=timestamp,
            project_name=project_name,
            mvp_features="\n".join(mvp) if mvp else "(None)",
            next_features="\n".join(next_phase) if next_phase else "(None)",
            future_features="\n".join(future) if future else "(None)",
            build_order="\n".join(build_order_lines) if build_order_lines else "(Not calculated)",
        )

        # Write to .agent/scope_boundary.md
        path = self.project_dir / ".agent" / "scope_boundary.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        self._scope_boundary_generated = True
        logger.info("Generated scope boundary at %s", path)
        return path

    # ── Handoff assembly ─────────────────────────────────────────────

    def assemble_handoff_package(self) -> dict[str, Any]:
        """Verify all pieces exist and return handoff status."""
        missing: list[str] = []

        # Check standards
        if not self.file_utils.standards_exist():
            missing.append("standards files")

        # Check product docs
        if not self.file_utils.product_exists():
            missing.append("product documents")

        # Check specs
        if not self.file_utils.specs_exist():
            missing.append("spec files")

        # Check features.db populated
        if not self._features_db_populated:
            missing.append("features.db")

        # Check scope boundary
        scope_path = self.project_dir / ".agent" / "scope_boundary.md"
        if not scope_path.is_file():
            missing.append("scope_boundary.md")

        feature_count = len(self.features.get_feature_list())
        build_order = self._build_order or []
        estimated_sessions = math.ceil(feature_count / 3) if feature_count > 0 else 0

        ready = len(missing) == 0
        if ready:
            self._handoff_complete = True

        return {
            "ready": ready,
            "missing": missing,
            "feature_count": feature_count,
            "build_order": build_order,
            "estimated_sessions": estimated_sessions,
        }

    def get_build_plan_summary(self) -> str:
        """Return a human-readable build plan summary."""
        feature_list = self.features.get_feature_list()
        if not feature_list:
            return "No features to build."

        build_order = self._build_order or self.calculate_build_order()
        feature_count = len(feature_list)
        estimated_sessions = math.ceil(feature_count / 3)

        counts = self.features.get_feature_count_by_priority()

        lines = [
            "# Build Plan Summary",
            "",
            f"**Total features:** {feature_count}",
            f"**Estimated sessions:** {estimated_sessions} (at ~3 features per session)",
            "",
            "## Feature Breakdown",
            f"- Must-have (MVP): {counts.get('must_have', 0)}",
            f"- Should-have (v1.1): {counts.get('should_have', 0)}",
            f"- Nice-to-have (future): {counts.get('nice_to_have', 0)}",
            "",
            "## Build Order",
        ]

        for i, fid in enumerate(build_order, 1):
            feat = self.features.get_feature_by_id(fid)
            if feat:
                deps = feat.get("dependencies", [])
                dep_str = f" (depends on: {', '.join(f'#{d}' for d in deps)})" if deps else ""
                lines.append(f"{i}. #{fid} {feat['name']} [{feat.get('priority', '?')}]{dep_str}")

        return "\n".join(lines)

    def get_handoff_status(self) -> dict[str, bool]:
        """Return current handoff state."""
        return {
            "features_db_populated": self._features_db_populated,
            "dependencies_set": self._dependencies_set,
            "scope_boundary_generated": self._scope_boundary_generated,
            "build_order_calculated": len(self._build_order) > 0,
            "handoff_complete": self._handoff_complete,
        }
