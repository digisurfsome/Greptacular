"""
Activepieces Code Manager Router
=================================

HTTP endpoints for reading and writing source code on Activepieces Code-type
flow steps.  Works around the AP MCP limitation that cannot set source code
on Code steps.

Connects to the Activepieces PostgreSQL database running inside Docker
(``modular-pipeline-builder-postgres-1``) via ``docker exec`` + ``psql``.
Uses PostgreSQL ``jsonb_set`` to surgically update the ``sourceCode.code``
field (and the ``valid`` flag) on the target step within ``flow_version.trigger``.

Endpoints:
- POST /api/ap-code/update-step       — write source code to a Code step
- POST /api/ap-code/get-step-code     — read current source code from a Code step
- POST /api/ap-code/update-step-input — set proper JSON input on any step (fixes HTTP body string bug)
- GET  /api/ap-code/health            — verify AP database connectivity
"""

import logging
import re
import subprocess
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ap-code", tags=["ap-code-manager"])

# Docker container and database connection details
AP_POSTGRES_CONTAINER = "modular-pipeline-builder-postgres-1"
AP_DATABASE = "pipeline"
AP_USER = "pipeline"


# ============================================================================
# Pydantic Models
# ============================================================================

class UpdateStepRequest(BaseModel):
    """Request body for updating source code on an AP Code step."""
    flow_id: str
    step_name: str  # e.g. "step_1", "step_2", etc.
    source_code: str


class UpdateStepResponse(BaseModel):
    """Response body for the update-step endpoint."""
    success: bool
    flow_id: Optional[str] = None
    step_name: Optional[str] = None
    rows_affected: Optional[int] = None
    error: Optional[str] = None


class GetStepCodeRequest(BaseModel):
    """Request body for reading source code from an AP Code step."""
    flow_id: str
    step_name: str


class GetStepCodeResponse(BaseModel):
    """Response body for the get-step-code endpoint."""
    success: bool
    flow_id: Optional[str] = None
    step_name: Optional[str] = None
    source_code: Optional[str] = None
    error: Optional[str] = None


# ============================================================================
# Internal Helpers
# ============================================================================

def _parse_step_depth(step_name: str) -> int:
    """Extract the numeric depth from a step name like 'step_1' or 'step_3'.

    Returns the integer depth (1-based).
    Raises ValueError if the step name format is invalid.
    """
    match = re.match(r"^step_(\d+)$", step_name.strip())
    if not match:
        raise ValueError(
            f"Invalid step_name '{step_name}'. Expected format: step_N (e.g. step_1, step_2)"
        )
    depth = int(match.group(1))
    if depth < 1:
        raise ValueError(f"Step depth must be >= 1, got {depth}")
    return depth


def _build_jsonb_path(depth: int, field: str) -> str:
    """Build the PostgreSQL JSONB path array for a given step depth and field.

    For depth=1, field='settings,sourceCode,code':
        '{nextAction,settings,sourceCode,code}'

    For depth=2, field='valid':
        '{nextAction,nextAction,valid}'

    Args:
        depth: Step depth (1-based). step_1 = 1 nextAction, step_2 = 2 nextActions.
        field: Comma-separated JSONB field suffix (e.g. 'settings,sourceCode,code' or 'valid').

    Returns:
        PostgreSQL array literal like '{nextAction,nextAction,settings,sourceCode,code}'.
    """
    next_actions = ",".join(["nextAction"] * depth)
    return "{" + next_actions + "," + field + "}"


def _escape_sql_string(value: str) -> str:
    """Escape a string for use inside a PostgreSQL single-quoted literal.

    Replaces single quotes with doubled single quotes (SQL standard escaping).
    Also escapes backslashes for PostgreSQL.
    """
    # Escape backslashes first, then single quotes
    return value.replace("\\", "\\\\").replace("'", "''")


def _run_psql(sql: str) -> subprocess.CompletedProcess:
    """Execute a SQL statement against the AP PostgreSQL database via docker exec.

    Args:
        sql: The SQL statement to execute.

    Returns:
        CompletedProcess with stdout/stderr.

    Raises:
        RuntimeError: If the docker exec command fails.
    """
    cmd = [
        "docker", "exec", AP_POSTGRES_CONTAINER,
        "psql", "-U", AP_USER, "-d", AP_DATABASE,
        "-t",   # Tuples-only output (no headers/footers)
        "-A",   # Unaligned output (no padding)
        "-c", sql,
    ]

    logger.debug("[ap-code] Running psql command: %s", sql[:200])

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode != 0:
        error_detail = result.stderr.strip() or result.stdout.strip()
        logger.error("[ap-code] psql failed (rc=%d): %s", result.returncode, error_detail)
        raise RuntimeError(f"psql command failed: {error_detail}")

    return result


# ============================================================================
# REST Endpoints
# ============================================================================

@router.get("/health")
async def health_check():
    """Verify that the Activepieces PostgreSQL database is reachable.

    Runs a simple SELECT 1 query via docker exec to confirm:
    1. Docker is running
    2. The AP postgres container is up
    3. The database accepts connections
    """
    try:
        result = _run_psql("SELECT 1;")
        value = result.stdout.strip()
        if value == "1":
            return {"status": "ok", "database": "reachable"}
        else:
            return {"status": "degraded", "database": "unexpected_response", "raw": value}
    except Exception as exc:
        logger.error("[ap-code] Health check failed: %s", exc)
        return {"status": "error", "database": "unreachable", "error": str(exc)}


@router.post("/update-step", response_model=UpdateStepResponse)
async def update_step_code(body: UpdateStepRequest):
    """Set source code on an Activepieces Code step.

    Targets the latest flow_version row for the given flowId.  Updates two
    JSONB fields:
    1. ``trigger → ...nextAction(s) → settings → sourceCode → code`` — the actual code
    2. ``trigger → ...nextAction(s) → valid`` — set to ``true`` so AP treats the step as valid

    The step depth is derived from the step_name: step_1 = 1 level of nextAction,
    step_2 = 2 levels, etc.
    """
    try:
        depth = _parse_step_depth(body.step_name)
    except ValueError as exc:
        return UpdateStepResponse(success=False, error=str(exc))

    # Build JSONB paths for the code field and the valid flag
    code_path = _build_jsonb_path(depth, "settings,sourceCode,code")
    valid_path = _build_jsonb_path(depth, "valid")

    # Escape the source code for safe SQL embedding
    escaped_code = _escape_sql_string(body.source_code)
    escaped_flow_id = _escape_sql_string(body.flow_id)

    # Build the UPDATE statement.  Uses a subquery to target only the latest
    # flow_version for the given flowId (by created DESC).
    sql = (
        f"UPDATE flow_version "
        f"SET trigger = jsonb_set("
        f"  jsonb_set(trigger, '{code_path}', '\"{escaped_code}\"'::jsonb), "
        f"  '{valid_path}', 'true'::jsonb"
        f") "
        f"WHERE id = ("
        f"  SELECT id FROM flow_version "
        f"  WHERE \"flowId\" = '{escaped_flow_id}' "
        f"  ORDER BY created DESC LIMIT 1"
        f");"
    )

    try:
        result = _run_psql(sql)
        # Parse rows affected from psql output (e.g. "UPDATE 1")
        stdout = result.stdout.strip()
        rows_affected = 0
        if "UPDATE" in stdout.upper():
            parts = stdout.split()
            if len(parts) >= 2 and parts[-1].isdigit():
                rows_affected = int(parts[-1])

        if rows_affected == 0:
            return UpdateStepResponse(
                success=False,
                flow_id=body.flow_id,
                step_name=body.step_name,
                rows_affected=0,
                error=f"No flow_version found for flowId '{body.flow_id}'. "
                      f"Verify the flow_id is correct.",
            )

        logger.info(
            "[ap-code] Updated %s on flow %s: %d rows affected",
            body.step_name, body.flow_id, rows_affected,
        )
        return UpdateStepResponse(
            success=True,
            flow_id=body.flow_id,
            step_name=body.step_name,
            rows_affected=rows_affected,
        )

    except Exception as exc:
        logger.error("[ap-code] Update failed: %s", exc)
        return UpdateStepResponse(
            success=False,
            flow_id=body.flow_id,
            step_name=body.step_name,
            error=str(exc),
        )


@router.post("/get-step-code", response_model=GetStepCodeResponse)
async def get_step_code(body: GetStepCodeRequest):
    """Read the current source code from an Activepieces Code step.

    Extracts the code string from the JSONB trigger column at the path
    determined by the step depth.
    """
    try:
        depth = _parse_step_depth(body.step_name)
    except ValueError as exc:
        return GetStepCodeResponse(success=False, error=str(exc))

    # Build the JSONB extraction path using -> operators
    # For depth=1: trigger->'nextAction'->'settings'->'sourceCode'->>'code'
    # For depth=2: trigger->'nextAction'->'nextAction'->'settings'->'sourceCode'->>'code'
    path_parts = ["'nextAction'"] * depth + ["'settings'", "'sourceCode'"]
    arrow_chain = "->".join(path_parts)
    # Use ->> for the final key to get text instead of JSON
    json_path = f"trigger->{arrow_chain}->>'code'"

    escaped_flow_id = _escape_sql_string(body.flow_id)

    sql = (
        f"SELECT {json_path} FROM flow_version "
        f"WHERE \"flowId\" = '{escaped_flow_id}' "
        f"ORDER BY created DESC LIMIT 1;"
    )

    try:
        result = _run_psql(sql)
        source_code = result.stdout.strip()

        # psql returns empty string for NULL values with -t -A flags
        if not source_code:
            return GetStepCodeResponse(
                success=False,
                flow_id=body.flow_id,
                step_name=body.step_name,
                error=f"No code found at {body.step_name} for flowId '{body.flow_id}'. "
                      f"The step may not exist or may not be a Code step.",
            )

        logger.info(
            "[ap-code] Read %d chars from %s on flow %s",
            len(source_code), body.step_name, body.flow_id,
        )
        return GetStepCodeResponse(
            success=True,
            flow_id=body.flow_id,
            step_name=body.step_name,
            source_code=source_code,
        )

    except Exception as exc:
        logger.error("[ap-code] Read failed: %s", exc)
        return GetStepCodeResponse(
            success=False,
            flow_id=body.flow_id,
            step_name=body.step_name,
            error=str(exc),
        )


# ============================================================================
# HTTP Step Input Fix — works around ap_update_step storing body as string
# ============================================================================

class UpdateStepInputRequest(BaseModel):
    """Request body for setting proper JSON input on any AP step."""
    flow_id: str
    step_name: str  # e.g. "step_1", "step_2"
    input_json: dict  # The full input object to set (proper JSON, not string)
    target_state: Optional[str] = None  # "DRAFT", "LOCKED", or None for latest


class UpdateStepInputResponse(BaseModel):
    """Response body for the update-step-input endpoint."""
    success: bool
    flow_id: Optional[str] = None
    step_name: Optional[str] = None
    rows_affected: Optional[int] = None
    error: Optional[str] = None


@router.post("/update-step-input", response_model=UpdateStepInputResponse)
async def update_step_input(body: UpdateStepInputRequest):
    """Set the input fields on any Activepieces step as proper JSON.

    Works around the MCP bug where ``ap_update_step`` stores HTTP body
    fields as JSON strings (``"{...}"``) instead of JSON objects (``{...}``).

    This endpoint replaces the entire ``settings.input`` object on the
    target step with the provided ``input_json`` as a proper JSONB value.
    """
    import json as json_module

    try:
        depth = _parse_step_depth(body.step_name)
    except ValueError as exc:
        return UpdateStepInputResponse(success=False, error=str(exc))

    # Build JSONB path: trigger -> nextAction(s) -> settings -> input
    input_path = _build_jsonb_path(depth, "settings,input")

    # Serialize the input as proper JSON
    input_json_str = json_module.dumps(body.input_json)
    # Escape for SQL embedding
    escaped_json = _escape_sql_string(input_json_str)
    escaped_flow_id = _escape_sql_string(body.flow_id)

    # Build WHERE clause — target specific state or latest version
    if body.target_state:
        escaped_state = _escape_sql_string(body.target_state)
        where_clause = (
            f"WHERE \"flowId\" = '{escaped_flow_id}' "
            f"AND state = '{escaped_state}'"
        )
    else:
        where_clause = (
            f"WHERE id = ("
            f"  SELECT id FROM flow_version "
            f"  WHERE \"flowId\" = '{escaped_flow_id}' "
            f"  ORDER BY created DESC LIMIT 1"
            f")"
        )

    sql = (
        f"UPDATE flow_version "
        f"SET trigger = jsonb_set(trigger, '{input_path}', '{escaped_json}'::jsonb) "
        f"{where_clause};"
    )

    try:
        result = _run_psql(sql)
        stdout = result.stdout.strip()
        rows_affected = 0
        if "UPDATE" in stdout.upper():
            parts = stdout.split()
            if len(parts) >= 2 and parts[-1].isdigit():
                rows_affected = int(parts[-1])

        if rows_affected == 0:
            return UpdateStepInputResponse(
                success=False,
                flow_id=body.flow_id,
                step_name=body.step_name,
                rows_affected=0,
                error=f"No flow_version found for flowId '{body.flow_id}'"
                      + (f" with state '{body.target_state}'" if body.target_state else "")
                      + ". Verify the flow_id is correct.",
            )

        logger.info(
            "[ap-code] Updated input on %s for flow %s: %d rows",
            body.step_name, body.flow_id, rows_affected,
        )
        return UpdateStepInputResponse(
            success=True,
            flow_id=body.flow_id,
            step_name=body.step_name,
            rows_affected=rows_affected,
        )

    except Exception as exc:
        logger.error("[ap-code] Input update failed: %s", exc)
        return UpdateStepInputResponse(
            success=False,
            flow_id=body.flow_id,
            step_name=body.step_name,
            error=str(exc),
        )
