"""
Tool Execution Models — Results, Gaps, and Build Specs
========================================================

SQLAlchemy 2.0 models for storing execution results, detected gaps,
and generated build specs for the tool analyzer flywheel.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text

from .filing import FilingBase, _utc_now


class ExecutionResultModel(FilingBase):
    """Stored result from a tool execution run."""
    __tablename__ = "yt_execution_results"

    id = Column(Integer, primary_key=True, index=True)
    tool_id = Column(String(64), nullable=False, index=True)
    node_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)  # success | failure | partial
    result_json = Column(Text, nullable=False)  # Full ExecutionResult as JSON
    error = Column(Text, nullable=True)
    duration = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=_utc_now)


class GapRecord(FilingBase):
    """A detected capability gap from failed executions."""
    __tablename__ = "yt_gap_records"

    id = Column(Integer, primary_key=True, index=True)
    component_type = Column(String(100), nullable=False)  # e.g., "adapter", "node", "component"
    required_capability = Column(String(200), nullable=False)  # What's missing
    frequency = Column(Integer, nullable=False, default=1)
    status = Column(String(20), nullable=False, default="open")  # open | resolved | in_progress
    affected_tools_json = Column(Text, nullable=False, default="[]")  # JSON array of tool IDs
    first_seen = Column(DateTime, default=_utc_now)
    last_seen = Column(DateTime, default=_utc_now)


class BuildSpec(FilingBase):
    """Generated specification for building a missing component."""
    __tablename__ = "yt_build_specs"

    id = Column(Integer, primary_key=True, index=True)
    gap_id = Column(Integer, nullable=True)  # Optional link to GapRecord
    component_name = Column(String(200), nullable=False)
    interface_contract = Column(Text, nullable=False)  # What the component must implement
    complexity = Column(String(20), nullable=False, default="medium")  # low | medium | high
    status = Column(String(20), nullable=False, default="pending_review")  # pending_review | approved | built
    similar_components_json = Column(Text, nullable=False, default="[]")  # JSON array of similar component names
    spec_json = Column(Text, nullable=True)  # Full spec details as JSON
    created_at = Column(DateTime, default=_utc_now)
