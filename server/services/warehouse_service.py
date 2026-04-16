"""
Warehouse Service — Tool Page Loading and Execution Dispatch
==============================================================

Bridge between the UI and execution engine.
Loads tool blueprints, validates user inputs against schemas,
and dispatches execution to the tool runner.
"""

import json
import logging
from datetime import datetime, timezone

from .filing_service import _get_session
from ..models.tool_execution import ExecutionResultModel

logger = logging.getLogger(__name__)


async def load_tool_blueprint(tool_id: str) -> dict | None:
    """Load a tool blueprint by ID and return its input schema.

    Queries the tool factory's generated tools for the blueprint.
    Returns a dict with tool_id, name, description, and input_schema.
    """
    try:
        from ..models.tool_factory import get_tool_store
        store = get_tool_store()
        tool = store.get(tool_id)
        if not tool:
            return None

        blueprint = tool.blueprint
        input_schema = _extract_input_schema(blueprint)

        return {
            "tool_id": tool_id,
            "name": blueprint.tool_name,
            "description": getattr(blueprint, "description", ""),
            "input_schema": input_schema,
        }
    except Exception as e:
        logger.warning("Failed to load tool blueprint %s: %s", tool_id, e)
        return None


async def validate_inputs(input_schema: list[dict], inputs: dict) -> tuple[bool, str]:
    """Validate user inputs against the tool's input schema."""
    for field in input_schema:
        name = field.get("name", "")
        required = field.get("required", False)
        field_type = field.get("type", "text")

        if required and name not in inputs:
            return False, f"Missing required field: {name}"
        if required and not str(inputs.get(name, "")).strip():
            return False, f"Required field '{name}' cannot be empty"

        if name in inputs:
            value = inputs[name]
            if field_type == "number":
                try:
                    float(value)
                except (ValueError, TypeError):
                    return False, f"Field '{name}' must be a number"
            elif field_type == "url":
                if not str(value).startswith(("http://", "https://")):
                    return False, f"Field '{name}' must be a valid URL"

    return True, ""


async def dispatch_execution(tool_id: str, inputs: dict) -> dict:
    """Dispatch tool execution via the tool runner.

    Returns an execution_id for tracking progress.
    """
    import uuid
    execution_id = str(uuid.uuid4())[:8]

    # Store the execution request for async processing
    logger.info("Dispatching execution %s for tool %s", execution_id, tool_id)

    return {"execution_id": execution_id, "tool_id": tool_id, "status": "queued"}


async def store_execution_result(
    tool_id: str,
    node_type: str,
    result_data: dict,
) -> dict:
    """Store an execution result in the database."""
    session = _get_session()
    try:
        record = ExecutionResultModel(
            tool_id=tool_id,
            node_type=node_type,
            status=result_data.get("status", "unknown"),
            result_json=json.dumps(result_data),
            error=result_data.get("error"),
            duration=str(result_data.get("duration", 0)),
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return {
            "id": record.id,
            "tool_id": record.tool_id,
            "status": record.status,
            "created_at": record.created_at.isoformat() if record.created_at else None,
        }
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def get_execution_history(tool_id: str, limit: int = 20) -> list[dict]:
    """Get execution history for a tool."""
    session = _get_session()
    try:
        results = (
            session.query(ExecutionResultModel)
            .filter(ExecutionResultModel.tool_id == tool_id)
            .order_by(ExecutionResultModel.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": r.id,
                "tool_id": r.tool_id,
                "node_type": r.node_type,
                "status": r.status,
                "error": r.error,
                "duration": r.duration,
                "result": json.loads(r.result_json) if r.result_json else {},
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in results
        ]
    finally:
        session.close()


def _extract_input_schema(blueprint) -> list[dict]:
    """Extract input schema from a tool blueprint.

    Looks for input fields in the blueprint's chain config or variables.
    """
    schema: list[dict] = []

    # Try to get variable definitions from the blueprint
    if hasattr(blueprint, "variables") and blueprint.variables:
        for var_name, var_info in blueprint.variables.items():
            if isinstance(var_info, dict):
                schema.append({
                    "name": var_name,
                    "type": var_info.get("type", "text"),
                    "label": var_info.get("label", var_name.replace("_", " ").title()),
                    "required": var_info.get("required", True),
                    "placeholder": var_info.get("placeholder", ""),
                })
            else:
                schema.append({
                    "name": var_name,
                    "type": "text",
                    "label": var_name.replace("_", " ").title(),
                    "required": True,
                })

    # If no variables found, check chain_config for referenced variables
    if not schema and hasattr(blueprint, "chain_config"):
        import re
        seen = set()
        for step in blueprint.chain_config:
            # Look for {{variable}} references in step config
            step_str = json.dumps(step) if isinstance(step, dict) else str(step)
            for match in re.findall(r'\{\{(\w+)\}\}', step_str):
                if match not in seen:
                    seen.add(match)
                    schema.append({
                        "name": match,
                        "type": "text",
                        "label": match.replace("_", " ").title(),
                        "required": True,
                    })

    return schema
