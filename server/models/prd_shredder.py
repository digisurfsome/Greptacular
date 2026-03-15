"""Data models for the PRD Shredder — drop a PRD in, code comes out."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class PRDStatus(str, Enum):
    QUEUED = "queued"
    CLONING = "cloning"
    ANALYZING = "analyzing"
    BUILDING = "building"
    TESTING = "testing"
    COMMITTING = "committing"
    DONE = "done"
    FAILED = "failed"


class PRDTask(BaseModel):
    """A single code task extracted from PRD analysis."""
    task_number: int
    action: str  # create_file, modify_file, delete_lines, add_dependency
    file_path: str
    description: str
    details: str = ""
    depends_on: list[int] = Field(default_factory=list)
    verification: str = ""
    status: str = "pending"  # pending, in_progress, done, skipped


class PRDAnalysis(BaseModel):
    """Result of the 4-stage analysis pipeline."""
    # Stage 1: PRD Ingestion
    objective: str = ""
    target_files: list[str] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    scope_exclusions: list[str] = Field(default_factory=list)
    difficulty: int = 0
    difficulty_reasoning: str = ""

    # Stage 2: Codebase Discovery
    existing_files: list[dict] = Field(default_factory=list)
    files_to_create: list[str] = Field(default_factory=list)
    files_to_modify: list[dict] = Field(default_factory=list)
    codebase_patterns: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)

    # Stage 3+4: Task list (corrected by consulting review)
    tasks: list[PRDTask] = Field(default_factory=list)

    # Metadata
    analysis_model: str = ""
    analysis_time: float = 0.0


class PRDQueueItem(BaseModel):
    """A PRD in the shredder queue."""
    id: str
    title: str
    prd_text: str
    target_repo: str  # GitHub URL or local path
    target_branch: str = "main"
    status: PRDStatus = PRDStatus.QUEUED
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    commit_hash: Optional[str] = None
    build_log: list[str] = Field(default_factory=list)
    tasks_total: int = 0
    tasks_done: int = 0
    analysis: Optional[PRDAnalysis] = None


class QueueStats(BaseModel):
    """Aggregate queue statistics."""
    total: int = 0
    queued: int = 0
    building: int = 0
    done: int = 0
    failed: int = 0
