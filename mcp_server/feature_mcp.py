#!/usr/bin/env python3
"""
MCP Server for Feature Management
==================================

Provides tools to manage features in the autonomous coding system.

Tools:
- feature_get_stats: Get progress statistics
- feature_get_by_id: Get a specific feature by ID
- feature_get_summary: Get minimal feature info (id, name, status, deps)
- feature_mark_passing: Mark a feature as passing
- feature_mark_failing: Mark a feature as failing (regression detected)
- feature_skip: Skip a feature (move to end of queue)
- feature_mark_in_progress: Mark a feature as in-progress
- feature_claim_and_get: Atomically claim and get feature details
- feature_clear_in_progress: Clear in-progress status
- feature_create_bulk: Create multiple features at once
- feature_create: Create a single feature
- feature_add_dependency: Add a dependency between features
- feature_remove_dependency: Remove a dependency
- feature_get_ready: Get features ready to implement
- feature_get_blocked: Get features blocked by dependencies (with limit)
- feature_get_graph: Get the dependency graph
- feature_split: Split a large feature into two parts at a step boundary
- preview_start: Start the project dev server for visual verification
- preview_stop: Stop the project dev server
- preview_status: Get dev server status (running/stopped + URL)

Note: Feature selection (which feature to work on) is handled by the
orchestrator, not by agents. Agents receive pre-assigned feature IDs.
"""

import json
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from sqlalchemy import text

# Add parent directory to path so we can import from api module
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.database import Feature, VerificationResult, atomic_transaction, create_database
from api.dependency_resolver import (
    MAX_DEPENDENCIES_PER_FEATURE,
    compute_scheduling_scores,
    would_create_circular_dependency,
)
from api.migration import migrate_json_to_sqlite

# Configuration from environment
PROJECT_DIR = Path(os.environ.get("PROJECT_DIR", ".")).resolve()


# Pydantic models for input validation
class MarkPassingInput(BaseModel):
    """Input for marking a feature as passing."""
    feature_id: int = Field(..., description="The ID of the feature to mark as passing", ge=1)


class SkipFeatureInput(BaseModel):
    """Input for skipping a feature."""
    feature_id: int = Field(..., description="The ID of the feature to skip", ge=1)


class MarkInProgressInput(BaseModel):
    """Input for marking a feature as in-progress."""
    feature_id: int = Field(..., description="The ID of the feature to mark as in-progress", ge=1)


class ClearInProgressInput(BaseModel):
    """Input for clearing in-progress status."""
    feature_id: int = Field(..., description="The ID of the feature to clear in-progress status", ge=1)


class RegressionInput(BaseModel):
    """Input for getting regression features."""
    limit: int = Field(default=3, ge=1, le=10, description="Maximum number of passing features to return")


class FeatureCreateItem(BaseModel):
    """Schema for creating a single feature."""
    category: str = Field(..., min_length=1, max_length=100, description="Feature category")
    name: str = Field(..., min_length=1, max_length=255, description="Feature name")
    description: str = Field(..., min_length=1, description="Detailed description")
    steps: list[str] = Field(..., min_length=1, description="Implementation/test steps")


class BulkCreateInput(BaseModel):
    """Input for bulk creating features."""
    features: list[FeatureCreateItem] = Field(..., min_length=1, description="List of features to create")


# Global database session maker (initialized on startup)
_session_maker = None
_engine = None

# NOTE: The old threading.Lock() was removed because it only worked per-process,
# not cross-process. In parallel mode, multiple MCP servers run in separate
# processes, so the lock was useless. We now use atomic SQL operations instead.


@asynccontextmanager
async def server_lifespan(server: FastMCP):
    """Initialize database on startup, cleanup on shutdown."""
    global _session_maker, _engine

    # Create project directory if it doesn't exist
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize database
    _engine, _session_maker = create_database(PROJECT_DIR)

    # Run migration if needed (converts legacy JSON to SQLite)
    migrate_json_to_sqlite(PROJECT_DIR, _session_maker)

    yield

    # Cleanup
    if _engine:
        _engine.dispose()


# Initialize the MCP server
mcp = FastMCP("features", lifespan=server_lifespan)


def get_session():
    """Get a new database session."""
    if _session_maker is None:
        raise RuntimeError("Database not initialized")
    return _session_maker()


# Maximum output size for verification records (10KB)
_MAX_VERIFICATION_OUTPUT = 10240


def _record_verification(session, feature_id: int, passed: bool, output: str, test_type: str) -> None:
    """Record a VerificationResult for a feature.

    Creates a new verification record in the database. Output is truncated
    to 10KB to prevent oversized entries.

    Args:
        session: Active SQLAlchemy session (will be committed by caller).
        feature_id: The feature this verification belongs to.
        passed: Whether the verification passed.
        output: Raw test output text.
        test_type: Type of verification (lint/typecheck/e2e/manual).
    """
    try:
        truncated_output = output[:_MAX_VERIFICATION_OUTPUT] if output else ""
        record = VerificationResult(
            feature_id=feature_id,
            session_id=os.environ.get("AUTOFORGE_SESSION_ID"),
            agent_index=int(os.environ.get("AUTOFORGE_AGENT_INDEX", "0")),
            test_type=test_type,
            passed=passed,
            output=truncated_output,
        )
        session.add(record)
        session.commit()
    except Exception:
        # Don't let verification recording failure break the main operation
        try:
            session.rollback()
        except Exception:
            pass


@mcp.tool()
def feature_get_stats() -> str:
    """Get statistics about feature completion progress.

    Returns the number of passing features, in-progress features, total features,
    and completion percentage. Use this to track overall progress of the implementation.

    Returns:
        JSON with: passing (int), in_progress (int), total (int), percentage (float)
    """
    from sqlalchemy import case, func

    session = get_session()
    try:
        # Single aggregate query instead of 3 separate COUNT queries
        result = session.query(
            func.count(Feature.id).label('total'),
            func.sum(case((Feature.passes == True, 1), else_=0)).label('passing'),
            func.sum(case((Feature.in_progress == True, 1), else_=0)).label('in_progress')
        ).first()

        total = result.total or 0
        passing = int(result.passing or 0)
        in_progress = int(result.in_progress or 0)
        percentage = round((passing / total) * 100, 1) if total > 0 else 0.0

        return json.dumps({
            "passing": passing,
            "in_progress": in_progress,
            "total": total,
            "percentage": percentage
        })
    finally:
        session.close()


@mcp.tool()
def feature_get_by_id(
    feature_id: Annotated[int, Field(description="The ID of the feature to retrieve", ge=1)]
) -> str:
    """Get a specific feature by its ID.

    Returns the full details of a feature including its name, description,
    verification steps, and current status.

    Args:
        feature_id: The ID of the feature to retrieve

    Returns:
        JSON with feature details, or error if not found.
    """
    session = get_session()
    try:
        feature = session.query(Feature).filter(Feature.id == feature_id).first()

        if feature is None:
            return json.dumps({"error": f"Feature with ID {feature_id} not found"})

        return json.dumps(feature.to_dict())
    finally:
        session.close()


@mcp.tool()
def feature_get_summary(
    feature_id: Annotated[int, Field(description="The ID of the feature", ge=1)]
) -> str:
    """Get minimal feature info: id, name, status, and dependencies only.

    Use this instead of feature_get_by_id when you only need status info,
    not the full description and steps. This reduces response size significantly.

    Args:
        feature_id: The ID of the feature to retrieve

    Returns:
        JSON with: id, name, passes, in_progress, dependencies
    """
    session = get_session()
    try:
        feature = session.query(Feature).filter(Feature.id == feature_id).first()
        if feature is None:
            return json.dumps({"error": f"Feature with ID {feature_id} not found"})
        return json.dumps({
            "id": feature.id,
            "name": feature.name,
            "passes": feature.passes,
            "in_progress": feature.in_progress,
            "dependencies": feature.dependencies or [],
            "reviewed": feature.reviewed if feature.reviewed is not None else False,
            "qa_verified": feature.qa_verified if feature.qa_verified is not None else False,
        })
    finally:
        session.close()


@mcp.tool()
def feature_mark_passing(
    feature_id: Annotated[int, Field(description="The ID of the feature to mark as passing", ge=1)],
    verification_output: Annotated[str, Field(description="Test/verification output text (optional)", default="")] = "",
    test_type: Annotated[str, Field(description="Type of test: lint/typecheck/e2e/manual (optional)", default="manual")] = "manual",
) -> str:
    """Mark a feature as passing after successful implementation.

    Updates the feature's passes field to true and clears the in_progress flag.
    Use this after you have implemented the feature and verified it works correctly.

    Optionally records a VerificationResult if verification_output is provided.

    Args:
        feature_id: The ID of the feature to mark as passing
        verification_output: Optional test output text to record
        test_type: Type of verification (lint/typecheck/e2e/manual)

    Returns:
        JSON with success confirmation: {success, feature_id, name}
    """
    session = get_session()
    try:
        # Atomic update with state guard - prevents double-pass in parallel mode
        result = session.execute(text("""
            UPDATE features
            SET passes = 1, in_progress = 0
            WHERE id = :id AND passes = 0
        """), {"id": feature_id})
        session.commit()

        if result.rowcount == 0:
            # Check why the update didn't match
            feature = session.query(Feature).filter(Feature.id == feature_id).first()
            if feature is None:
                return json.dumps({"error": f"Feature with ID {feature_id} not found"})
            if feature.passes:
                return json.dumps({"error": f"Feature with ID {feature_id} is already passing"})
            return json.dumps({"error": "Failed to mark feature passing for unknown reason"})

        # Record verification result if output was provided
        if verification_output:
            _record_verification(session, feature_id, True, verification_output, test_type)

        # Get the feature name for the response
        feature = session.query(Feature).filter(Feature.id == feature_id).first()
        return json.dumps({"success": True, "feature_id": feature_id, "name": feature.name})
    except Exception as e:
        session.rollback()
        return json.dumps({"error": f"Failed to mark feature passing: {str(e)}"})
    finally:
        session.close()


@mcp.tool()
def feature_mark_failing(
    feature_id: Annotated[int, Field(description="The ID of the feature to mark as failing", ge=1)],
    verification_output: Annotated[str, Field(description="Test/verification output text (optional)", default="")] = "",
    test_type: Annotated[str, Field(description="Type of test: lint/typecheck/e2e/manual (optional)", default="manual")] = "manual",
) -> str:
    """Mark a feature as failing after finding a regression.

    Updates the feature's passes field to false and clears the in_progress flag.
    Use this when a testing agent discovers that a previously-passing feature
    no longer works correctly (regression detected).

    Optionally records a VerificationResult if verification_output is provided.

    After marking as failing, you should:
    1. Investigate the root cause
    2. Fix the regression
    3. Verify the fix
    4. Call feature_mark_passing once fixed

    Args:
        feature_id: The ID of the feature to mark as failing
        verification_output: Optional test output text to record
        test_type: Type of verification (lint/typecheck/e2e/manual)

    Returns:
        JSON with the updated feature details, or error if not found.
    """
    session = get_session()
    try:
        # Check if feature exists first
        feature = session.query(Feature).filter(Feature.id == feature_id).first()
        if feature is None:
            return json.dumps({"error": f"Feature with ID {feature_id} not found"})

        # Atomic update for parallel safety
        # Also reset reviewed and qa_verified when a regression is detected
        session.execute(text("""
            UPDATE features
            SET passes = 0, in_progress = 0, reviewed = 0, qa_verified = 0
            WHERE id = :id
        """), {"id": feature_id})
        session.commit()

        # Record verification result if output was provided
        if verification_output:
            _record_verification(session, feature_id, False, verification_output, test_type)

        # Refresh to get updated state
        session.refresh(feature)

        return json.dumps({
            "message": f"Feature #{feature_id} marked as failing - regression detected",
            "feature": feature.to_dict()
        })
    except Exception as e:
        session.rollback()
        return json.dumps({"error": f"Failed to mark feature failing: {str(e)}"})
    finally:
        session.close()


@mcp.tool()
def feature_mark_reviewed(
    feature_id: Annotated[int, Field(description="The ID of the feature to mark as reviewed", ge=1)]
) -> str:
    """Mark a feature as reviewed after code review passes.

    Only succeeds when the feature has passes=True. Sets reviewed=1.
    Use this after the review agent has verified code quality, test quality,
    and found no issues.

    Args:
        feature_id: The ID of the feature to mark as reviewed

    Returns:
        JSON with success confirmation or error for invalid state transitions.
    """
    session = get_session()
    try:
        feature = session.query(Feature).filter(Feature.id == feature_id).first()
        if feature is None:
            return json.dumps({"error": f"Feature with ID {feature_id} not found"})
        if not feature.passes:
            return json.dumps({"error": f"Feature {feature_id} must be passing before it can be reviewed. Current passes={feature.passes}"})
        if feature.reviewed:
            return json.dumps({"error": f"Feature {feature_id} is already reviewed"})

        session.execute(text("""
            UPDATE features SET reviewed = 1 WHERE id = :id AND passes = 1
        """), {"id": feature_id})
        session.commit()

        session.refresh(feature)
        return json.dumps({"success": True, "feature_id": feature_id, "name": feature.name, "reviewed": True})
    except Exception as e:
        session.rollback()
        return json.dumps({"error": f"Failed to mark feature reviewed: {str(e)}"})
    finally:
        session.close()


@mcp.tool()
def feature_mark_qa_verified(
    feature_id: Annotated[int, Field(description="The ID of the feature to mark as QA verified", ge=1)]
) -> str:
    """Mark a feature as QA verified after final QA sweep passes.

    Only succeeds when the feature has reviewed=1. Sets qa_verified=1.
    Use this after the QA agent has verified the feature in the final QA sweep.

    Args:
        feature_id: The ID of the feature to mark as QA verified

    Returns:
        JSON with success confirmation or error for invalid state transitions.
    """
    session = get_session()
    try:
        feature = session.query(Feature).filter(Feature.id == feature_id).first()
        if feature is None:
            return json.dumps({"error": f"Feature with ID {feature_id} not found"})
        if not feature.reviewed:
            return json.dumps({"error": f"Feature {feature_id} must be reviewed before QA verification. Current reviewed={feature.reviewed}"})
        if feature.qa_verified:
            return json.dumps({"error": f"Feature {feature_id} is already QA verified"})

        session.execute(text("""
            UPDATE features SET qa_verified = 1 WHERE id = :id AND reviewed = 1
        """), {"id": feature_id})
        session.commit()

        session.refresh(feature)
        return json.dumps({"success": True, "feature_id": feature_id, "name": feature.name, "qa_verified": True})
    except Exception as e:
        session.rollback()
        return json.dumps({"error": f"Failed to mark feature QA verified: {str(e)}"})
    finally:
        session.close()


@mcp.tool()
def feature_skip(
    feature_id: Annotated[int, Field(description="The ID of the feature to skip", ge=1)]
) -> str:
    """Skip a feature by moving it to the end of the priority queue.

    Use this when a feature cannot be implemented yet due to:
    - Dependencies on other features that aren't implemented yet
    - External blockers (missing assets, unclear requirements)
    - Technical prerequisites that need to be addressed first

    The feature's priority is set to max_priority + 1, so it will be
    worked on after all other pending features. Also clears the in_progress
    flag so the feature returns to "pending" status.

    Args:
        feature_id: The ID of the feature to skip

    Returns:
        JSON with skip details: id, name, old_priority, new_priority, message
    """
    session = get_session()
    try:
        feature = session.query(Feature).filter(Feature.id == feature_id).first()

        if feature is None:
            return json.dumps({"error": f"Feature with ID {feature_id} not found"})

        if feature.passes:
            return json.dumps({"error": "Cannot skip a feature that is already passing"})

        old_priority = feature.priority
        name = feature.name

        # Atomic update: set priority to max+1 in a single statement
        # This prevents race conditions where two features get the same priority
        session.execute(text("""
            UPDATE features
            SET priority = (SELECT COALESCE(MAX(priority), 0) + 1 FROM features),
                in_progress = 0
            WHERE id = :id
        """), {"id": feature_id})
        session.commit()

        # Refresh to get new priority
        session.refresh(feature)
        new_priority = feature.priority

        return json.dumps({
            "id": feature_id,
            "name": name,
            "old_priority": old_priority,
            "new_priority": new_priority,
            "message": f"Feature '{name}' moved to end of queue"
        })
    except Exception as e:
        session.rollback()
        return json.dumps({"error": f"Failed to skip feature: {str(e)}"})
    finally:
        session.close()


@mcp.tool()
def feature_mark_in_progress(
    feature_id: Annotated[int, Field(description="The ID of the feature to mark as in-progress", ge=1)]
) -> str:
    """Mark a feature as in-progress.

    This prevents other agent sessions from working on the same feature.
    Call this after getting your assigned feature details with feature_get_by_id.

    Args:
        feature_id: The ID of the feature to mark as in-progress

    Returns:
        JSON with the updated feature details, or error if not found or already in-progress.
    """
    session = get_session()
    try:
        # Atomic claim: only succeeds if feature is not already claimed or passing
        result = session.execute(text("""
            UPDATE features
            SET in_progress = 1
            WHERE id = :id AND passes = 0 AND in_progress = 0
        """), {"id": feature_id})
        session.commit()

        if result.rowcount == 0:
            # Check why the claim failed
            feature = session.query(Feature).filter(Feature.id == feature_id).first()
            if feature is None:
                return json.dumps({"error": f"Feature with ID {feature_id} not found"})
            if feature.passes:
                return json.dumps({"error": f"Feature with ID {feature_id} is already passing"})
            if feature.in_progress:
                return json.dumps({"error": f"Feature with ID {feature_id} is already in-progress"})
            return json.dumps({"error": "Failed to mark feature in-progress for unknown reason"})

        # Fetch the claimed feature
        feature = session.query(Feature).filter(Feature.id == feature_id).first()
        return json.dumps(feature.to_dict())
    except Exception as e:
        session.rollback()
        return json.dumps({"error": f"Failed to mark feature in-progress: {str(e)}"})
    finally:
        session.close()


@mcp.tool()
def feature_claim_and_get(
    feature_id: Annotated[int, Field(description="The ID of the feature to claim", ge=1)]
) -> str:
    """Atomically claim a feature (mark in-progress) and return its full details.

    Combines feature_mark_in_progress + feature_get_by_id into a single operation.
    If already in-progress, still returns the feature details (idempotent).

    Args:
        feature_id: The ID of the feature to claim and retrieve

    Returns:
        JSON with feature details including claimed status, or error if not found.
    """
    session = get_session()
    try:
        # First check if feature exists
        feature = session.query(Feature).filter(Feature.id == feature_id).first()
        if feature is None:
            return json.dumps({"error": f"Feature with ID {feature_id} not found"})

        if feature.passes:
            return json.dumps({"error": f"Feature with ID {feature_id} is already passing"})

        # Try atomic claim: only succeeds if not already claimed
        result = session.execute(text("""
            UPDATE features
            SET in_progress = 1
            WHERE id = :id AND passes = 0 AND in_progress = 0
        """), {"id": feature_id})
        session.commit()

        # Determine if we claimed it or it was already claimed
        already_claimed = result.rowcount == 0
        if already_claimed:
            # Verify it's in_progress (not some other failure condition)
            session.refresh(feature)
            if not feature.in_progress:
                return json.dumps({"error": f"Failed to claim feature {feature_id} for unknown reason"})

        # Refresh to get current state
        session.refresh(feature)
        result_dict = feature.to_dict()
        result_dict["already_claimed"] = already_claimed
        return json.dumps(result_dict)
    except Exception as e:
        session.rollback()
        return json.dumps({"error": f"Failed to claim feature: {str(e)}"})
    finally:
        session.close()


@mcp.tool()
def feature_clear_in_progress(
    feature_id: Annotated[int, Field(description="The ID of the feature to clear in-progress status", ge=1)]
) -> str:
    """Clear in-progress status from a feature.

    Use this when abandoning a feature or manually unsticking a stuck feature.
    The feature will return to the pending queue.

    Args:
        feature_id: The ID of the feature to clear in-progress status

    Returns:
        JSON with the updated feature details, or error if not found.
    """
    session = get_session()
    try:
        # Check if feature exists
        feature = session.query(Feature).filter(Feature.id == feature_id).first()
        if feature is None:
            return json.dumps({"error": f"Feature with ID {feature_id} not found"})

        # Atomic update - idempotent, safe in parallel mode
        session.execute(text("""
            UPDATE features
            SET in_progress = 0
            WHERE id = :id
        """), {"id": feature_id})
        session.commit()

        session.refresh(feature)
        return json.dumps(feature.to_dict())
    except Exception as e:
        session.rollback()
        return json.dumps({"error": f"Failed to clear in-progress status: {str(e)}"})
    finally:
        session.close()


@mcp.tool()
def feature_create_bulk(
    features: Annotated[list[dict], Field(description="List of features to create, each with category, name, description, and steps")]
) -> str:
    """Create multiple features in a single operation.

    Features are assigned sequential priorities based on their order.
    All features start with passes=false.

    This is typically used by the initializer agent to set up the initial
    feature list from the app specification.

    Args:
        features: List of features to create, each with:
            - category (str): Feature category
            - name (str): Feature name
            - description (str): Detailed description
            - steps (list[str]): Implementation/test steps
            - depends_on_indices (list[int], optional): Array indices (0-based) of
              features in THIS batch that this feature depends on. Use this instead
              of 'dependencies' since IDs aren't known until after creation.
              Example: [0, 2] means this feature depends on features at index 0 and 2.

    Returns:
        JSON with: created (int) - number of features created, with_dependencies (int)
    """
    try:
        # Use atomic transaction for bulk inserts to prevent priority conflicts
        with atomic_transaction(_session_maker) as session:
            # Get the starting priority atomically within the transaction
            result = session.execute(text("""
                SELECT COALESCE(MAX(priority), 0) FROM features
            """)).fetchone()
            start_priority = (result[0] or 0) + 1

            # First pass: validate all features and their index-based dependencies
            for i, feature_data in enumerate(features):
                # Validate required fields
                if not all(key in feature_data for key in ["category", "name", "description", "steps"]):
                    return json.dumps({
                        "error": f"Feature at index {i} missing required fields (category, name, description, steps)"
                    })

                # Validate depends_on_indices
                indices = feature_data.get("depends_on_indices", [])
                if indices:
                    # Check max dependencies
                    if len(indices) > MAX_DEPENDENCIES_PER_FEATURE:
                        return json.dumps({
                            "error": f"Feature at index {i} has {len(indices)} dependencies, max is {MAX_DEPENDENCIES_PER_FEATURE}"
                        })
                    # Check for duplicates
                    if len(indices) != len(set(indices)):
                        return json.dumps({
                            "error": f"Feature at index {i} has duplicate dependencies"
                        })
                    # Check for forward references (can only depend on earlier features)
                    for idx in indices:
                        if not isinstance(idx, int) or idx < 0:
                            return json.dumps({
                                "error": f"Feature at index {i} has invalid dependency index: {idx}"
                            })
                        if idx >= i:
                            return json.dumps({
                                "error": f"Feature at index {i} cannot depend on feature at index {idx} (forward reference not allowed)"
                            })

            # Second pass: create all features with reserved priorities
            created_features: list[Feature] = []
            for i, feature_data in enumerate(features):
                db_feature = Feature(
                    priority=start_priority + i,
                    category=feature_data["category"],
                    name=feature_data["name"],
                    description=feature_data["description"],
                    steps=feature_data["steps"],
                    passes=False,
                    in_progress=False,
                )
                session.add(db_feature)
                created_features.append(db_feature)

            # Flush to get IDs assigned
            session.flush()

            # Third pass: resolve index-based dependencies to actual IDs
            deps_count = 0
            for i, feature_data in enumerate(features):
                indices = feature_data.get("depends_on_indices", [])
                if indices:
                    # Convert indices to actual feature IDs
                    dep_ids = [created_features[idx].id for idx in indices]
                    created_features[i].dependencies = sorted(dep_ids)  # type: ignore[assignment]  # SQLAlchemy JSON Column accepts list at runtime
                    deps_count += 1

            # Commit happens automatically on context manager exit
            return json.dumps({
                "created": len(created_features),
                "with_dependencies": deps_count
            })
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def feature_create(
    category: Annotated[str, Field(min_length=1, max_length=100, description="Feature category (e.g., 'Authentication', 'API', 'UI')")],
    name: Annotated[str, Field(min_length=1, max_length=255, description="Feature name")],
    description: Annotated[str, Field(min_length=1, description="Detailed description of the feature")],
    steps: Annotated[list[str], Field(min_length=1, description="List of implementation/verification steps")]
) -> str:
    """Create a single feature in the project backlog.

    Use this when the user asks to add a new feature, capability, or test case.
    The feature will be added with the next available priority number.

    Args:
        category: Feature category for grouping (e.g., 'Authentication', 'API', 'UI')
        name: Descriptive name for the feature
        description: Detailed description of what this feature should do
        steps: List of steps to implement or verify the feature

    Returns:
        JSON with the created feature details including its ID
    """
    try:
        # Use atomic transaction to prevent priority collisions
        with atomic_transaction(_session_maker) as session:
            # Get the next priority atomically within the transaction
            result = session.execute(text("""
                SELECT COALESCE(MAX(priority), 0) + 1 FROM features
            """)).fetchone()
            next_priority = result[0]

            db_feature = Feature(
                priority=next_priority,
                category=category,
                name=name,
                description=description,
                steps=steps,
                passes=False,
                in_progress=False,
            )
            session.add(db_feature)
            session.flush()  # Get the ID

            feature_dict = db_feature.to_dict()
            # Commit happens automatically on context manager exit

        return json.dumps({
            "success": True,
            "message": f"Created feature: {name}",
            "feature": feature_dict
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def feature_add_dependency(
    feature_id: Annotated[int, Field(ge=1, description="Feature to add dependency to")],
    dependency_id: Annotated[int, Field(ge=1, description="ID of the dependency feature")]
) -> str:
    """Add a dependency relationship between features.

    The dependency_id feature must be completed before feature_id can be started.
    Validates: self-reference, existence, circular dependencies, max limit.

    Args:
        feature_id: The ID of the feature that will depend on another feature
        dependency_id: The ID of the feature that must be completed first

    Returns:
        JSON with success status and updated dependencies list, or error message
    """
    try:
        # Security: Self-reference check (can do before transaction)
        if feature_id == dependency_id:
            return json.dumps({"error": "A feature cannot depend on itself"})

        # Use atomic transaction for consistent cycle detection
        with atomic_transaction(_session_maker) as session:
            feature = session.query(Feature).filter(Feature.id == feature_id).first()
            dependency = session.query(Feature).filter(Feature.id == dependency_id).first()

            if not feature:
                return json.dumps({"error": f"Feature {feature_id} not found"})
            if not dependency:
                return json.dumps({"error": f"Dependency feature {dependency_id} not found"})

            current_deps = feature.dependencies or []

            # Security: Max dependencies limit
            if len(current_deps) >= MAX_DEPENDENCIES_PER_FEATURE:
                return json.dumps({"error": f"Maximum {MAX_DEPENDENCIES_PER_FEATURE} dependencies allowed per feature"})

            # Check if already exists
            if dependency_id in current_deps:
                return json.dumps({"error": "Dependency already exists"})

            # Security: Circular dependency check
            # Within IMMEDIATE transaction, snapshot is protected by write lock
            all_features = [f.to_dict() for f in session.query(Feature).all()]
            if would_create_circular_dependency(all_features, feature_id, dependency_id):
                return json.dumps({"error": "Cannot add: would create circular dependency"})

            # Add dependency atomically
            new_deps = sorted(current_deps + [dependency_id])
            feature.dependencies = new_deps
            # Commit happens automatically on context manager exit

            return json.dumps({
                "success": True,
                "feature_id": feature_id,
                "dependencies": new_deps
            })
    except Exception as e:
        return json.dumps({"error": f"Failed to add dependency: {str(e)}"})


@mcp.tool()
def feature_remove_dependency(
    feature_id: Annotated[int, Field(ge=1, description="Feature to remove dependency from")],
    dependency_id: Annotated[int, Field(ge=1, description="ID of dependency to remove")]
) -> str:
    """Remove a dependency from a feature.

    Args:
        feature_id: The ID of the feature to remove a dependency from
        dependency_id: The ID of the dependency to remove

    Returns:
        JSON with success status and updated dependencies list, or error message
    """
    try:
        # Use atomic transaction for consistent read-modify-write
        with atomic_transaction(_session_maker) as session:
            feature = session.query(Feature).filter(Feature.id == feature_id).first()
            if not feature:
                return json.dumps({"error": f"Feature {feature_id} not found"})

            current_deps = feature.dependencies or []
            if dependency_id not in current_deps:
                return json.dumps({"error": "Dependency does not exist"})

            # Remove dependency atomically
            new_deps = [d for d in current_deps if d != dependency_id]
            feature.dependencies = new_deps if new_deps else None
            # Commit happens automatically on context manager exit

            return json.dumps({
                "success": True,
                "feature_id": feature_id,
                "dependencies": new_deps
            })
    except Exception as e:
        return json.dumps({"error": f"Failed to remove dependency: {str(e)}"})


@mcp.tool()
def feature_get_ready(
    limit: Annotated[int, Field(default=10, ge=1, le=50, description="Max features to return")] = 10
) -> str:
    """Get all features ready to start (dependencies satisfied, not in progress).

    Useful for parallel execution - returns multiple features that can run simultaneously.
    A feature is ready if it is not passing, not in progress, and all dependencies are passing.

    Args:
        limit: Maximum number of features to return (1-50, default 10)

    Returns:
        JSON with: features (list), count (int), total_ready (int)
    """
    session = get_session()
    try:
        all_features = session.query(Feature).all()
        passing_ids = {f.id for f in all_features if f.passes}

        ready = []
        all_dicts = [f.to_dict() for f in all_features]
        for f in all_features:
            if f.passes or f.in_progress:
                continue
            deps = f.dependencies or []
            if all(dep_id in passing_ids for dep_id in deps):
                ready.append(f.to_dict())

        # Sort by scheduling score (higher = first), then priority, then id
        scores = compute_scheduling_scores(all_dicts)
        ready.sort(key=lambda f: (-scores.get(f["id"], 0), f["priority"], f["id"]))

        return json.dumps({
            "features": ready[:limit],
            "count": len(ready[:limit]),
            "total_ready": len(ready)
        })
    finally:
        session.close()


@mcp.tool()
def feature_get_blocked(
    limit: Annotated[int, Field(default=20, ge=1, le=100, description="Max features to return")] = 20
) -> str:
    """Get features that are blocked by unmet dependencies.

    Returns features that have dependencies which are not yet passing.
    Each feature includes a 'blocked_by' field listing the blocking feature IDs.

    Args:
        limit: Maximum number of features to return (1-100, default 20)

    Returns:
        JSON with: features (list with blocked_by field), count (int), total_blocked (int)
    """
    session = get_session()
    try:
        all_features = session.query(Feature).all()
        passing_ids = {f.id for f in all_features if f.passes}

        blocked = []
        for f in all_features:
            if f.passes:
                continue
            deps = f.dependencies or []
            blocking = [d for d in deps if d not in passing_ids]
            if blocking:
                blocked.append({
                    **f.to_dict(),
                    "blocked_by": blocking
                })

        return json.dumps({
            "features": blocked[:limit],
            "count": len(blocked[:limit]),
            "total_blocked": len(blocked)
        })
    finally:
        session.close()


@mcp.tool()
def feature_get_graph() -> str:
    """Get dependency graph data for visualization.

    Returns nodes (features) and edges (dependencies) for rendering a graph.
    Each node includes status: 'pending', 'in_progress', 'done', or 'blocked'.

    Returns:
        JSON with: nodes (list), edges (list of {source, target})
    """
    session = get_session()
    try:
        all_features = session.query(Feature).all()
        passing_ids = {f.id for f in all_features if f.passes}

        nodes = []
        edges = []

        for f in all_features:
            deps = f.dependencies or []
            blocking = [d for d in deps if d not in passing_ids]

            if f.passes:
                status = "done"
            elif blocking:
                status = "blocked"
            elif f.in_progress:
                status = "in_progress"
            else:
                status = "pending"

            nodes.append({
                "id": f.id,
                "name": f.name,
                "category": f.category,
                "status": status,
                "priority": f.priority,
                "dependencies": deps
            })

            for dep_id in deps:
                edges.append({"source": dep_id, "target": f.id})

        return json.dumps({
            "nodes": nodes,
            "edges": edges
        })
    finally:
        session.close()


@mcp.tool()
def feature_set_dependencies(
    feature_id: Annotated[int, Field(ge=1, description="Feature to set dependencies for")],
    dependency_ids: Annotated[list[int], Field(description="List of dependency feature IDs")]
) -> str:
    """Set all dependencies for a feature at once, replacing any existing dependencies.

    Validates: self-reference, existence of all dependencies, circular dependencies, max limit.

    Args:
        feature_id: The ID of the feature to set dependencies for
        dependency_ids: List of feature IDs that must be completed first

    Returns:
        JSON with success status and updated dependencies list, or error message
    """
    try:
        # Security: Self-reference check (can do before transaction)
        if feature_id in dependency_ids:
            return json.dumps({"error": "A feature cannot depend on itself"})

        # Security: Max dependencies limit
        if len(dependency_ids) > MAX_DEPENDENCIES_PER_FEATURE:
            return json.dumps({"error": f"Maximum {MAX_DEPENDENCIES_PER_FEATURE} dependencies allowed"})

        # Check for duplicates
        if len(dependency_ids) != len(set(dependency_ids)):
            return json.dumps({"error": "Duplicate dependencies not allowed"})

        # Use atomic transaction for consistent cycle detection
        with atomic_transaction(_session_maker) as session:
            feature = session.query(Feature).filter(Feature.id == feature_id).first()
            if not feature:
                return json.dumps({"error": f"Feature {feature_id} not found"})

            # Validate all dependencies exist
            all_feature_ids = {f.id for f in session.query(Feature).all()}
            missing = [d for d in dependency_ids if d not in all_feature_ids]
            if missing:
                return json.dumps({"error": f"Dependencies not found: {missing}"})

            # Check for circular dependencies
            # Within IMMEDIATE transaction, snapshot is protected by write lock
            all_features = [f.to_dict() for f in session.query(Feature).all()]
            test_features = []
            for f in all_features:
                if f["id"] == feature_id:
                    test_features.append({**f, "dependencies": dependency_ids})
                else:
                    test_features.append(f)

            for dep_id in dependency_ids:
                if would_create_circular_dependency(test_features, feature_id, dep_id):
                    return json.dumps({"error": f"Cannot add dependency {dep_id}: would create circular dependency"})

            # Set dependencies atomically
            sorted_deps = sorted(dependency_ids) if dependency_ids else None
            feature.dependencies = sorted_deps
            # Commit happens automatically on context manager exit

            return json.dumps({
                "success": True,
                "feature_id": feature_id,
                "dependencies": sorted_deps or []
            })
    except Exception as e:
        return json.dumps({"error": f"Failed to set dependencies: {str(e)}"})


@mcp.tool()
def feature_split(
    feature_id: Annotated[int, Field(ge=1, description="The ID of the feature to split")],
    split_after_step: Annotated[int, Field(ge=1, description="Split after this step index (1-based). Part 1 keeps steps 1..N, Part 2 gets the remaining steps.")],
    part2_name: Annotated[str, Field(min_length=1, max_length=255, description="Name for the new Part 2 feature")],
) -> str:
    """Split a feature into two parts at a given step boundary.

    Use this when a feature is too large to complete within the 45% context budget.
    Part 1 retains the original feature's steps up to split_after_step.
    Part 2 is created as a new feature with the remaining steps and depends on Part 1.

    The original feature keeps its ID, name (with ' (Part 1)' appended), and dependencies.
    Part 2 gets a new ID and depends on Part 1 plus all of Part 1's original dependencies.

    Args:
        feature_id: The ID of the feature to split
        split_after_step: Split after this step number (1-based). Steps 1..N stay in Part 1,
            remaining steps go to Part 2.
        part2_name: Name for the new Part 2 feature

    Returns:
        JSON with both feature details, or error message
    """
    if _session_maker is None:
        return json.dumps({"error": "Database not initialized"})

    try:
        with atomic_transaction(_session_maker) as session:
            feature = session.query(Feature).filter(Feature.id == feature_id).first()
            if not feature:
                return json.dumps({"error": f"Feature {feature_id} not found"})

            if feature.passes:
                return json.dumps({"error": f"Feature {feature_id} is already passing, cannot split"})

            steps = feature.steps or []
            if not isinstance(steps, list) or len(steps) < 2:
                return json.dumps({"error": "Feature must have at least 2 steps to split"})

            if split_after_step < 1 or split_after_step >= len(steps):
                return json.dumps({
                    "error": f"split_after_step must be between 1 and {len(steps) - 1} "
                             f"(feature has {len(steps)} steps)"
                })

            # Split the steps
            part1_steps = steps[:split_after_step]
            part2_steps = steps[split_after_step:]

            # Update Part 1 (original feature)
            original_name = feature.name
            feature.name = f"{original_name} (Part 1)"
            feature.steps = part1_steps

            # Get the original dependencies for Part 2
            original_deps = list(feature.get_dependencies_safe())

            # Determine Part 2's priority (right after Part 1)
            max_priority = session.query(Feature).count()
            part2_priority = max_priority + 1

            # Create Part 2 with dependency on Part 1
            part2_deps = sorted(set(original_deps + [feature_id]))
            part2 = Feature(
                priority=part2_priority,
                category=feature.category,
                name=part2_name,
                description=f"Continuation of '{original_name}'. "
                            f"This feature implements the remaining steps after Part 1 is complete.",
                steps=part2_steps,
                passes=False,
                in_progress=False,
                dependencies=part2_deps,
            )
            session.add(part2)
            session.flush()  # Get the new ID

            return json.dumps({
                "success": True,
                "part1": {
                    "id": feature.id,
                    "name": feature.name,
                    "steps_count": len(part1_steps),
                },
                "part2": {
                    "id": part2.id,
                    "name": part2.name,
                    "steps_count": len(part2_steps),
                    "dependencies": part2_deps,
                },
                "message": f"Feature split successfully. Part 1 (#{feature.id}) has "
                           f"{len(part1_steps)} steps, Part 2 (#{part2.id}) has "
                           f"{len(part2_steps)} steps."
            })
    except Exception as e:
        return json.dumps({"error": f"Failed to split feature: {str(e)}"})


@mcp.tool()
def ask_user(
    questions: Annotated[list[dict], Field(description="List of questions to ask, each with question, header, options (list of {label, description}), and multiSelect (bool)")]
) -> str:
    """Ask the user structured questions with selectable options.

    Use this when you need clarification or want to offer choices to the user.
    Each question has a short header, the question text, and 2-4 clickable options.
    The user's selections will be returned as your next message.

    Args:
        questions: List of questions, each with:
            - question (str): The question to ask
            - header (str): Short label (max 12 chars)
            - options (list): Each with label (str) and description (str)
            - multiSelect (bool): Allow multiple selections (default false)

    Returns:
        Acknowledgment that questions were presented to the user
    """
    # Validate input
    for i, q in enumerate(questions):
        if not all(key in q for key in ["question", "header", "options"]):
            return json.dumps({"error": f"Question at index {i} missing required fields"})
        if len(q["options"]) < 2 or len(q["options"]) > 4:
            return json.dumps({"error": f"Question at index {i} must have 2-4 options"})

    return "Questions presented to the user. Their response will arrive as your next message."


@mcp.tool()
def factory_write_handoff(
    completed_summary: Annotated[str, Field(min_length=1, description="What you accomplished this session")],
    next_phase_summary: Annotated[str, Field(min_length=1, description="What the next agent should work on")],
    features_completed: Annotated[list[int] | None, Field(description="List of feature IDs you completed")] = None,
    files_created: Annotated[list[str] | None, Field(description="List of new files you created")] = None,
    files_modified: Annotated[list[str] | None, Field(description="List of existing files you modified")] = None,
    priority_tasks: Annotated[list[str] | None, Field(description="Ordered list of tasks for the next agent")] = None,
    feature_ids_to_work: Annotated[list[int] | None, Field(description="Feature IDs for the next agent to implement")] = None,
    notes: Annotated[str | None, Field(description="Any important context for the next agent")] = None,
    current_bugs: Annotated[list[dict] | None, Field(description="List of known bugs [{file, line, description, severity}]")] = None,
    dev_server_url: Annotated[str | None, Field(description="URL of the running dev server (if any)")] = None,
    dev_server_status: Annotated[str | None, Field(description="Status of dev server (running/stopped/was_running)")] = None,
    context_usage_percent: Annotated[int | None, Field(description="Your estimated context usage percentage")] = None,
    context_reason: Annotated[str | None, Field(description="Why you're handing off (approaching_budget, rate_limited, completed, etc.)")] = None,
) -> str:
    """Write a handoff file for the next agent session.

    Call this when you are approaching your context budget or when you have
    completed all assigned work for this phase. The handoff file tells AutoForge
    what you accomplished, what's left to do, and any issues the next agent
    should know about. AutoForge will automatically read this file and start
    the next agent session.

    Args:
        completed_summary: What you accomplished this session
        next_phase_summary: What the next agent should work on
        features_completed: List of feature IDs you completed
        files_created: List of new files you created
        files_modified: List of existing files you modified
        priority_tasks: Ordered list of tasks for the next agent
        feature_ids_to_work: Feature IDs for the next agent to implement
        notes: Any important context for the next agent
        current_bugs: List of known bugs [{file, line, description, severity}]
        dev_server_url: URL of the running dev server (if any)
        dev_server_status: Status of dev server (running/stopped/was_running)
        context_usage_percent: Your estimated context usage percentage
        context_reason: Why you're handing off (approaching_budget, rate_limited, completed, etc.)

    Returns:
        JSON with status, path, and confirmation message.
    """
    from datetime import datetime, timezone

    handoff_data = {
        "version": 1,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "completed": {
            "summary": completed_summary,
            "features_completed": features_completed or [],
            "files_created": files_created or [],
            "files_modified": files_modified or [],
        },
        "next_phase": {
            "summary": next_phase_summary,
            "priority_tasks": priority_tasks or [],
            "feature_ids_to_work": feature_ids_to_work or [],
            "notes": notes or "",
        },
        "current_bugs": current_bugs or [],
        "dev_server": {
            "url": dev_server_url,
            "status": dev_server_status or "unknown",
        },
        "context_usage": {
            "estimated_percent": context_usage_percent,
            "reason": context_reason or "approaching_budget",
        },
    }

    try:
        handoff_path = PROJECT_DIR / ".autoforge" / "handoff.json"
        handoff_path.parent.mkdir(parents=True, exist_ok=True)
        handoff_path.write_text(json.dumps(handoff_data, indent=2), encoding="utf-8")

        return json.dumps({
            "status": "written",
            "path": str(handoff_path),
            "message": "Handoff file written. AutoForge will read this when your session ends and auto-start the next agent."
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to write handoff file: {str(e)}"})


# ── Preview / Dev Server MCP Tools ──────────────────────────────────────────
# Lightweight dev server management so agents can start a preview server,
# screenshot pages, and verify their own UI work.  Subprocess is managed
# inside this MCP process — no REST round-trip to the FastAPI server.

import re as _re
import shlex as _shlex
import subprocess as _subprocess
import threading as _threading
import time as _time

_preview_process: _subprocess.Popen | None = None
_preview_url: str | None = None
_preview_lock = _threading.Lock()

_URL_PATTERNS = [
    r'https?://(?:localhost|127\.0\.0\.1):\d+(?:/[^\s]*)?',
    r'https?://\[::1\]:\d+(?:/[^\s]*)?',
    r'https?://0\.0\.0\.0:\d+(?:/[^\s]*)?',
]


def _detect_url(line: str) -> str | None:
    for pat in _URL_PATTERNS:
        m = _re.search(pat, line)
        if m:
            return m.group(0)
    return None


def _get_dev_command() -> str | None:
    """Read the effective dev command from project config (same logic as project_config.py)."""
    config_path = PROJECT_DIR / ".autoforge" / "config.json"
    if not config_path.exists():
        config_path = PROJECT_DIR / ".autocoder" / "config.json"
    if config_path.exists():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            cmd = data.get("dev_command")
            if isinstance(cmd, str) and cmd.strip():
                return cmd.strip()
        except Exception:
            pass
    # Auto-detect: check for common patterns
    if (PROJECT_DIR / "package.json").exists():
        return "npm run dev"
    if (PROJECT_DIR / "manage.py").exists():
        return "python manage.py runserver"
    return None


@mcp.tool()
def preview_start(
    command: Annotated[str | None, Field(description="Dev server command (e.g. 'npm run dev'). Leave empty to auto-detect.")] = None,
) -> str:
    """Start the project's dev server so you can preview your work.

    Once the server is running, use Playwright MCP tools (screenshot, etc.)
    to verify your UI changes visually.

    Args:
        command: Dev server command. Defaults to auto-detected command.

    Returns:
        JSON with status, url (if detected), and message.
    """
    global _preview_process, _preview_url

    with _preview_lock:
        # Already running?
        if _preview_process is not None and _preview_process.poll() is None:
            return json.dumps({
                "status": "already_running",
                "url": _preview_url,
                "message": f"Dev server already running (PID {_preview_process.pid}). URL: {_preview_url or 'detecting...'}",
            })

        cmd = command or _get_dev_command()
        if not cmd:
            return json.dumps({
                "error": "No dev command available. Pass a command or configure one in .autoforge/config.json"
            })

        argv = _shlex.split(cmd, posix=(sys.platform != "win32"))
        if not argv:
            return json.dumps({"error": "Empty command"})

        # Windows: use .cmd shims for Node package managers
        base = Path(argv[0]).name.lower()
        if sys.platform == "win32" and base in {"npm", "pnpm", "yarn", "npx"} and not argv[0].lower().endswith(".cmd"):
            argv[0] = argv[0] + ".cmd"

        try:
            popen_kwargs: dict = {
                "stdin": _subprocess.DEVNULL,
                "stdout": _subprocess.PIPE,
                "stderr": _subprocess.STDOUT,
                "cwd": str(PROJECT_DIR),
            }
            if sys.platform == "win32":
                popen_kwargs["creationflags"] = _subprocess.CREATE_NO_WINDOW

            _preview_process = _subprocess.Popen(argv, **popen_kwargs)
            _preview_url = None

            # Read output in background thread to detect URL
            def _reader():
                global _preview_url
                proc = _preview_process
                if not proc or not proc.stdout:
                    return
                try:
                    for raw_line in proc.stdout:
                        decoded = raw_line.decode("utf-8", errors="replace").rstrip()
                        if not _preview_url:
                            url = _detect_url(decoded)
                            if url:
                                _preview_url = url
                except Exception:
                    pass

            t = _threading.Thread(target=_reader, daemon=True)
            t.start()

            # Wait briefly for URL detection
            for _ in range(40):  # 4 seconds max
                _time.sleep(0.1)
                if _preview_url:
                    break

            return json.dumps({
                "status": "started",
                "pid": _preview_process.pid,
                "url": _preview_url,
                "command": cmd,
                "message": f"Dev server started (PID {_preview_process.pid}). URL: {_preview_url or 'still starting...'}",
            })

        except FileNotFoundError:
            _preview_process = None
            return json.dumps({"error": f"Command not found: {argv[0]}"})
        except Exception as e:
            _preview_process = None
            return json.dumps({"error": f"Failed to start dev server: {e}"})


@mcp.tool()
def preview_stop() -> str:
    """Stop the project's dev server.

    Returns:
        JSON with status and message.
    """
    global _preview_process, _preview_url

    with _preview_lock:
        if _preview_process is None or _preview_process.poll() is not None:
            _preview_process = None
            _preview_url = None
            return json.dumps({"status": "not_running", "message": "Dev server is not running."})

        try:
            import psutil
            proc = psutil.Process(_preview_process.pid)
            children = proc.children(recursive=True)
            for child in children:
                try:
                    child.terminate()
                except Exception:
                    pass
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except psutil.TimeoutExpired:
                for child in children:
                    try:
                        child.kill()
                    except Exception:
                        pass
                proc.kill()
        except Exception:
            try:
                _preview_process.terminate()
                _preview_process.wait(timeout=3)
            except Exception:
                try:
                    _preview_process.kill()
                except Exception:
                    pass

        pid = _preview_process.pid
        _preview_process = None
        _preview_url = None
        return json.dumps({"status": "stopped", "message": f"Dev server stopped (was PID {pid})."})


@mcp.tool()
def preview_status() -> str:
    """Get the current status of the dev server.

    Returns:
        JSON with status (running/stopped), url, and pid.
    """
    global _preview_process, _preview_url

    with _preview_lock:
        if _preview_process is not None and _preview_process.poll() is None:
            return json.dumps({
                "status": "running",
                "pid": _preview_process.pid,
                "url": _preview_url,
            })
        else:
            # Clean up if process died
            if _preview_process is not None:
                _preview_process = None
                _preview_url = None
            return json.dumps({"status": "stopped", "pid": None, "url": None})


if __name__ == "__main__":
    mcp.run()
