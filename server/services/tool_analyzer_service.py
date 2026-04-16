"""
Tool Analyzer Service — Gap Detection and Build Spec Generation
=================================================================

READ-ONLY diagnostic system that:
1. Classifies execution failures into gap categories
2. Detects missing components in the registry
3. Generates build specs for missing pieces
4. Tracks gap frequency for prioritization

IMPORTANT: This is Phase 1 of the flywheel. It does NOT spawn agents
or auto-build anything. All build specs are stored as 'pending_review'
and require human approval.
"""

import json
import logging
from datetime import datetime, timezone

from .filing_service import _get_session
from ..models.tool_execution import BuildSpec, GapRecord

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Failure Classification
# ---------------------------------------------------------------------------


def classify_failure(result: dict) -> str:
    """Classify a failure type from an execution result.

    Returns one of:
        - missing_adapter: API adapter not found for a service
        - missing_component: Execution node or component not registered
        - configuration_error: Missing API key or credentials
        - runtime_error: Everything else (code bugs, timeouts, etc.)
    """
    error = str(result.get("error", "")).lower()
    metadata = result.get("metadata", {})

    if "adapter not found" in error or "unknown service" in error:
        return "missing_adapter"
    if "node not found" in error or "unknown node type" in error:
        return "missing_component"
    if any(kw in error for kw in ("api_key", "credentials", "auth", "not configured")):
        return "configuration_error"
    if metadata.get("error_category") == "configuration_error":
        return "configuration_error"

    return "runtime_error"


# ---------------------------------------------------------------------------
# Gap Detection
# ---------------------------------------------------------------------------


async def analyze_failure(tool_id: str, result: dict) -> dict:
    """Analyze a single execution failure and record any detected gaps.

    Returns analysis with gap type, existing alternatives, and recommendation.
    """
    gap_type = classify_failure(result)
    error = result.get("error", "")
    metadata = result.get("metadata", {})
    node_type = metadata.get("node_type", "unknown")

    # Extract the missing capability from the error context
    capability = _extract_capability(error, metadata)

    analysis = {
        "gap_type": gap_type,
        "capability": capability,
        "node_type": node_type,
        "error": error,
        "alternatives": [],
    }

    # Check for existing alternatives in the component registry
    if gap_type in ("missing_adapter", "missing_component"):
        alternatives = await _check_registry_alternatives(gap_type, capability)
        analysis["alternatives"] = alternatives

        # Record the gap
        await _record_gap(
            component_type=gap_type.replace("missing_", ""),
            required_capability=capability,
            tool_id=tool_id,
        )

    return analysis


async def detect_gaps() -> list[dict]:
    """Get all open gaps ordered by frequency (most common first)."""
    session = _get_session()
    try:
        gaps = (
            session.query(GapRecord)
            .filter(GapRecord.status == "open")
            .order_by(GapRecord.frequency.desc())
            .all()
        )
        return [_gap_to_dict(g) for g in gaps]
    finally:
        session.close()


async def get_gap_dashboard_data() -> list[dict]:
    """Get all gaps with frequency and status for the dashboard."""
    session = _get_session()
    try:
        gaps = (
            session.query(GapRecord)
            .order_by(GapRecord.frequency.desc())
            .all()
        )
        return [_gap_to_dict(g) for g in gaps]
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Build Spec Generation
# ---------------------------------------------------------------------------


async def generate_build_spec(gap_id: int) -> dict:
    """Generate a build spec for a specific gap.

    The spec describes what needs to be built, its interface contract,
    complexity estimate, and similar existing components.
    """
    session = _get_session()
    try:
        gap = session.query(GapRecord).filter(GapRecord.id == gap_id).first()
        if not gap:
            raise ValueError(f"Gap {gap_id} not found")

        # Check for similar components
        alternatives = await _check_registry_alternatives(
            gap.component_type, gap.required_capability
        )
        similar_names = [a["component_name"] for a in alternatives]

        # Determine complexity based on component type
        complexity = _estimate_complexity(gap.component_type, gap.required_capability)

        # Generate the interface contract
        interface_contract = _generate_interface(gap.component_type, gap.required_capability)

        spec = BuildSpec(
            gap_id=gap_id,
            component_name=f"{gap.required_capability}_{gap.component_type}",
            interface_contract=interface_contract,
            complexity=complexity,
            status="pending_review",
            similar_components_json=json.dumps(similar_names),
            spec_json=json.dumps({
                "gap_type": gap.component_type,
                "capability": gap.required_capability,
                "frequency": gap.frequency,
                "affected_tools": json.loads(gap.affected_tools_json),
                "interface": interface_contract,
                "similar": similar_names,
            }),
        )
        session.add(spec)
        session.commit()
        session.refresh(spec)
        return _spec_to_dict(spec)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def list_build_specs(status: str | None = None) -> list[dict]:
    """List build specs, optionally filtered by status."""
    session = _get_session()
    try:
        q = session.query(BuildSpec)
        if status:
            q = q.filter(BuildSpec.status == status)
        specs = q.order_by(BuildSpec.created_at.desc()).all()
        return [_spec_to_dict(s) for s in specs]
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------


def _extract_capability(error: str, metadata: dict) -> str:
    """Extract the missing capability name from error context."""
    # Try to get service name from metadata
    service = metadata.get("service", "")
    if service:
        return service

    # Try to extract from error message
    for prefix in ("adapter not found for service: ", "unknown service: ", "unknown node type: "):
        if prefix in error.lower():
            return error.lower().split(prefix)[-1].split(".")[0].split(",")[0].strip()

    return metadata.get("node_type", "unknown_capability")


async def _check_registry_alternatives(component_type: str, capability: str) -> list[dict]:
    """Check the component registry for similar existing components."""
    try:
        from .component_registry import get_component_registry
        registry = get_component_registry()
        matches = registry.match_step(f"{component_type} {capability}")
        return [
            {
                "component_name": m.component_name,
                "confidence": m.confidence,
                "matched_keywords": m.matched_keywords,
            }
            for m in matches[:5]  # Top 5 alternatives
        ]
    except Exception as e:
        logger.warning("Registry lookup failed: %s", e)
        return []


async def _record_gap(component_type: str, required_capability: str, tool_id: str) -> None:
    """Record or update a gap in the database.

    Increments frequency if the same gap exists. Adds tool_id to affected list.
    """
    session = _get_session()
    try:
        existing = (
            session.query(GapRecord)
            .filter(
                GapRecord.component_type == component_type,
                GapRecord.required_capability == required_capability,
            )
            .first()
        )

        if existing:
            existing.frequency += 1
            existing.last_seen = datetime.now(timezone.utc)
            # Add tool_id to affected list if not already there
            affected = json.loads(existing.affected_tools_json)
            if tool_id not in affected:
                affected.append(tool_id)
                existing.affected_tools_json = json.dumps(affected)
        else:
            gap = GapRecord(
                component_type=component_type,
                required_capability=required_capability,
                frequency=1,
                status="open",
                affected_tools_json=json.dumps([tool_id]),
            )
            session.add(gap)

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _estimate_complexity(component_type: str, capability: str) -> str:
    """Estimate build complexity for a missing component."""
    # Adapters are usually low-medium complexity
    if component_type == "adapter":
        return "low"
    # Nodes are medium complexity
    if component_type == "component":
        return "medium"
    return "medium"


def _generate_interface(component_type: str, capability: str) -> str:
    """Generate the interface contract string for a missing component."""
    if component_type == "adapter":
        return (
            f"class {capability.title().replace('_', '')}Adapter(APIAdapter):\n"
            f"    async def execute(self, action: str, payload: dict) -> dict:\n"
            f"        # Implement {capability} API actions\n"
            f"        ...\n"
        )
    if component_type == "component":
        return (
            f"class {capability.title().replace('_', '')}Node(BaseExecutionNode):\n"
            f"    async def execute(self, task: dict) -> ExecutionResult:\n"
            f"        # Implement {capability} execution\n"
            f"        ...\n"
            f"    async def validate(self, task: dict) -> tuple[bool, str]:\n"
            f"        ...\n"
        )
    return f"# Interface for {component_type}: {capability}"


def _gap_to_dict(g: GapRecord) -> dict:
    return {
        "id": g.id,
        "component_type": g.component_type,
        "required_capability": g.required_capability,
        "frequency": g.frequency,
        "status": g.status,
        "affected_tools": json.loads(g.affected_tools_json),
        "first_seen": g.first_seen.isoformat() if g.first_seen else None,
        "last_seen": g.last_seen.isoformat() if g.last_seen else None,
    }


def _spec_to_dict(s: BuildSpec) -> dict:
    return {
        "id": s.id,
        "gap_id": s.gap_id,
        "component_name": s.component_name,
        "interface_contract": s.interface_contract,
        "complexity": s.complexity,
        "status": s.status,
        "similar_components": json.loads(s.similar_components_json),
        "spec": json.loads(s.spec_json) if s.spec_json else None,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }
