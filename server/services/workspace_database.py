"""
Workspace Database
==================

SQLAlchemy models and CRUD functions for persisting workspace conversations.
Uses a global database at ``~/.autoforge/workspace.db`` (not per-project).
"""

import json
import logging
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    func,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 style declarative base."""
    pass


# Engine cache to avoid creating new engines for each request
# Key: database path (as posix string), Value: SQLAlchemy engine
_engine_cache: dict[str, Engine] = {}

# Lock for thread-safe access to the engine cache
# Prevents race conditions when multiple threads create engines simultaneously
_cache_lock = threading.Lock()


def _utc_now() -> datetime:
    """Return current UTC time. Replacement for deprecated datetime.utcnow()."""
    return datetime.now(timezone.utc)


# ============================================================================
# Models
# ============================================================================

class WorkspaceConversation(Base):
    """A conversation in the global workspace."""
    __tablename__ = "workspace_conversations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=True)  # Optional title, derived from first user message
    category = Column(String(50), nullable=False, default="general")
    working_directory = Column(Text, nullable=True)  # Optional cwd for the conversation
    pinned = Column(Integer, nullable=False, default=0)  # Boolean as int for SQLite
    tags = Column(String(500), nullable=True)  # comma-separated tags
    context_mode = Column(String(10), nullable=True, default="200k")  # "1m" or "200k"
    model = Column(String(20), nullable=True, default="opus")  # "opus" or "sonnet"
    effort = Column(String(10), nullable=True, default="high")  # "low", "medium", "high"
    branch_name = Column(String(200), nullable=True)  # Git branch for this conversation
    provider = Column(String(20), nullable=False, default="claude")  # "claude" | "codex" | "gemini"
    provider_thread_id = Column(String(200), nullable=True)  # Codex threadId / Gemini session_id
    token_count = Column(Integer, nullable=False, default=0)
    summary = Column(Text, nullable=True)
    summary_updated_at = Column(DateTime, nullable=True)
    forked_from_id = Column(
        Integer,
        ForeignKey("workspace_conversations.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    messages = relationship(
        "WorkspaceMessage", back_populates="conversation", cascade="all, delete-orphan"
    )


class WorkspaceMessage(Base):
    """A single message within a workspace conversation."""
    __tablename__ = "workspace_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        Integer, ForeignKey("workspace_conversations.id"), nullable=False, index=True
    )
    role = Column(String(20), nullable=False)  # "user" | "assistant" | "system"
    content = Column(Text, nullable=False)
    token_estimate = Column(Integer, nullable=False, default=0)
    timestamp = Column(DateTime, default=_utc_now)

    conversation = relationship("WorkspaceConversation", back_populates="messages")


class WorkspaceSummary(Base):
    """History of auto-generated conversation summaries."""
    __tablename__ = "workspace_summaries"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        Integer,
        ForeignKey("workspace_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    summary = Column(Text, nullable=False)
    message_count = Column(Integer, nullable=False)
    token_estimate = Column(Integer, default=0)
    created_at = Column(DateTime, default=_utc_now)


class WorkspaceCategory(Base):
    """User-defined categories for organizing conversations."""
    __tablename__ = "workspace_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    color = Column(String(7), nullable=True)  # hex color, e.g. "#3b82f6"
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=_utc_now)


class WorkspaceLibraryFolder(Base):
    """A folder in the workspace library filesystem."""
    __tablename__ = "workspace_library_folders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    parent_id = Column(
        Integer,
        ForeignKey("workspace_library_folders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)


class WorkspaceLibraryFile(Base):
    """A file in the workspace library."""
    __tablename__ = "workspace_library_files"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        Integer,
        ForeignKey("workspace_conversations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    folder_id = Column(
        Integer,
        ForeignKey("workspace_library_folders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    filename = Column(String(500), nullable=False)
    display_name = Column(String(200), nullable=True)
    file_type = Column(String(50), nullable=True)  # 'doc', 'spec', 'template', 'upload', 'code'
    content = Column(Text, nullable=True)  # cached content (NULL for large files)
    file_path = Column(String(500), nullable=True)  # disk path for large files
    file_size = Column(Integer, nullable=True)
    tags = Column(String(500), nullable=True)  # comma-separated
    active_in_context = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utc_now)


class WorkspaceFileActivation(Base):
    """Per-conversation activation state for global library files."""
    __tablename__ = "workspace_file_activations"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(
        Integer,
        ForeignKey("workspace_library_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id = Column(
        Integer,
        ForeignKey("workspace_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    active = Column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint("file_id", "conversation_id", name="uq_file_conversation"),
    )


class WorkspaceConnectedRepo(Base):
    """A connected GitHub repository."""
    __tablename__ = "workspace_connected_repos"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        Integer,
        ForeignKey("workspace_conversations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    repo_url = Column(String(500), nullable=False)
    repo_name = Column(String(200), nullable=False)
    local_path = Column(String(500), nullable=True)
    access_token_ref = Column(String(100), nullable=True)
    branch = Column(String(100), default="main")
    last_synced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utc_now)


class WorkspaceNotification(Base):
    """A structured notification from an agent (summary, roadmap, progress, milestone)."""
    __tablename__ = "workspace_notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(
        Integer,
        ForeignKey("workspace_conversations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    notification_type = Column(String(50), nullable=False)  # "summary", "roadmap", "progress", "milestone"
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=True)  # JSON-encoded metadata
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)


class WorkspaceRateLimitEvent(Base):
    """Records when a rate limit is hit (5-hour daily, weekly, or monthly)."""
    __tablename__ = "workspace_rate_limit_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String, nullable=False)  # "daily", "weekly", "monthly"
    timestamp = Column(DateTime, default=_utc_now)
    tokens_at_hit = Column(Integer, nullable=False, default=0)  # Total tokens used when limit was hit
    premium_tokens_at_hit = Column(Integer, nullable=False, default=0)  # Tokens in 200K+ zone at hit
    message_count_at_hit = Column(Integer, nullable=False, default=0)
    period_start = Column(DateTime, nullable=False)  # Start of the period (day/week/month)
    notes = Column(String, nullable=True)


class WorkspacePremiumLedger(Base):
    """Tracks premium-zone (>200K) token usage per conversation for cost analysis."""
    __tablename__ = "workspace_premium_ledger"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=_utc_now)
    total_tokens = Column(Integer, nullable=False, default=0)  # Total conversation tokens at this point
    standard_tokens = Column(Integer, nullable=False, default=0)  # 0-200K portion
    premium_tokens = Column(Integer, nullable=False, default=0)  # 200K+ portion
    estimated_cost = Column(Float, nullable=False, default=0.0)  # API-equivalent cost at this point


class WorkspaceTokenLog(Base):
    """Per-turn token processing log for auditing API usage.

    Each row records a single event in the conversation: an assistant turn,
    a tool call, a tool result, or the final SDK ResultMessage summary.
    """
    __tablename__ = "workspace_token_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, nullable=False, index=True)
    # "assistant_turn" | "tool_call" | "tool_result" | "result_summary"
    event_type = Column(String(30), nullable=False)
    turn_number = Column(Integer, nullable=False, default=0)
    timestamp = Column(DateTime, default=_utc_now)

    # For tool_call events
    tool_name = Column(String(100), nullable=True)
    tool_input_length = Column(Integer, nullable=True)  # chars of tool input

    # For tool_result events
    tool_result_length = Column(Integer, nullable=True)  # chars of tool result
    tool_is_error = Column(Integer, nullable=True)  # 0 or 1

    # For assistant_turn events
    text_length = Column(Integer, nullable=True)  # chars of assistant text
    num_tool_calls = Column(Integer, nullable=True)  # tool calls in this turn

    # Token estimates (heuristic: ~4 chars/token)
    estimated_tokens = Column(Integer, nullable=False, default=0)

    # SDK-reported actual usage (only on result_summary events)
    api_input_tokens = Column(Integer, nullable=True)
    api_output_tokens = Column(Integer, nullable=True)
    api_cache_creation_tokens = Column(Integer, nullable=True)
    api_cache_read_tokens = Column(Integer, nullable=True)
    api_total_cost_usd = Column(Float, nullable=True)
    api_num_turns = Column(Integer, nullable=True)
    api_duration_ms = Column(Integer, nullable=True)
    api_duration_api_ms = Column(Integer, nullable=True)

    # Model used
    model = Column(String(100), nullable=True)


# ============================================================================
# Role Library Models
# ============================================================================


class RoleBlueprint(Base):
    """A pre-PRD role blueprint in the role library.

    Each blueprint describes an agent role that can be built for the terminal —
    e.g. an "SDK Update Agent" or a "Lint Fix Agent".  Blueprints are organized
    by category and store the full PRD/documentation as markdown content.
    Multiple files/artifacts that belong to a role are linked via ``role_tag``.
    """

    __tablename__ = "role_blueprints"

    id = Column(Integer, primary_key=True, index=True)

    # Identity
    name = Column(String(200), nullable=False)
    role_tag = Column(String(100), nullable=False, unique=True, index=True)

    # Classification
    category = Column(String(50), nullable=False, index=True)  # e.g. "updating", "building", "testing"
    subcategory = Column(String(100), nullable=True)  # e.g. "sdk", "dependencies", "security"

    # Content
    one_liner = Column(String(300), nullable=False)  # Short description
    prd_content = Column(Text, nullable=False, default="")  # Full PRD markdown
    target_files = Column(Text, nullable=True)  # JSON list of file paths this role touches

    # Metadata
    status = Column(String(20), nullable=False, default="draft")  # draft | ready | built
    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)


# ============================================================================
# Background Session Event Persistence
# ============================================================================


class WorkspaceSessionEvent(Base):
    """Persisted event from a background AI session.

    Each row records a single streaming event (text chunk, tool call,
    token usage, response_done, error, etc.) from a background session.
    Events are written in batches for performance and read back for
    catch-up replay when a viewer reconnects.

    The ``sequence`` column is a monotonically increasing counter
    within a session, allowing viewers to request "all events since
    sequence N" for efficient catch-up without re-downloading the
    entire history.
    """
    __tablename__ = "workspace_session_events"

    id = Column(Integer, primary_key=True)
    session_id = Column(String(50), nullable=False, index=True)
    conversation_id = Column(Integer, nullable=False, index=True)
    sequence = Column(Integer, nullable=False)
    event_type = Column(String(50), nullable=False)
    event_data = Column(Text, nullable=False)  # JSON-encoded event payload
    created_at = Column(DateTime, default=_utc_now)


# ============================================================================
# Engine and Session Management
# ============================================================================

def _get_db_path() -> Path:
    """Return the path to the global workspace database.

    The database lives at ``~/.autoforge/workspace.db``.  The parent
    directory is created if it does not exist.
    """
    db_dir = Path.home() / ".autoforge"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "workspace.db"


def get_engine() -> Engine:
    """Get or create a SQLAlchemy engine for the workspace database.

    Uses a cache to avoid creating new engines for each request, which improves
    performance by reusing database connections.

    Thread-safe: Uses double-checked locking to prevent race conditions when
    multiple threads try to create the engine simultaneously.
    """
    db_path = _get_db_path()
    cache_key = db_path.as_posix()

    # Double-checked locking for thread safety and performance
    if cache_key in _engine_cache:
        return _engine_cache[cache_key]

    with _cache_lock:
        # Check again inside the lock in case another thread created it
        if cache_key not in _engine_cache:
            # Use as_posix() for cross-platform compatibility with SQLite connection strings
            db_url = f"sqlite:///{db_path.as_posix()}"
            engine = create_engine(
                db_url,
                echo=False,
                connect_args={
                    "check_same_thread": False,
                    "timeout": 30,  # Wait up to 30s for locks
                }
            )
            Base.metadata.create_all(engine)

            # Enable WAL mode for concurrent reads during writes.
            # Without WAL, all writes serialize with exclusive locks which
            # causes delete timeouts when the agent is actively streaming.
            import sqlite3
            conn = sqlite3.connect(db_path.as_posix())
            conn.execute("PRAGMA journal_mode=WAL")

            # Schema migration: add Phase 2 columns if missing
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(workspace_conversations)")
            existing_cols = {row[1] for row in cursor.fetchall()}
            if "pinned" not in existing_cols:
                cursor.execute(
                    "ALTER TABLE workspace_conversations ADD COLUMN pinned INTEGER NOT NULL DEFAULT 0"
                )
            if "token_count" not in existing_cols:
                cursor.execute(
                    "ALTER TABLE workspace_conversations ADD COLUMN token_count INTEGER NOT NULL DEFAULT 0"
                )
            if "summary" not in existing_cols:
                cursor.execute("ALTER TABLE workspace_conversations ADD COLUMN summary TEXT")
            if "summary_updated_at" not in existing_cols:
                cursor.execute(
                    "ALTER TABLE workspace_conversations ADD COLUMN summary_updated_at DATETIME"
                )
            if "forked_from_id" not in existing_cols:
                cursor.execute(
                    "ALTER TABLE workspace_conversations ADD COLUMN forked_from_id INTEGER"
                )
            if "tags" not in existing_cols:
                cursor.execute("ALTER TABLE workspace_conversations ADD COLUMN tags TEXT")
            if "context_mode" not in existing_cols:
                cursor.execute(
                    "ALTER TABLE workspace_conversations ADD COLUMN context_mode TEXT DEFAULT '1m'"
                )
            if "model" not in existing_cols:
                cursor.execute(
                    "ALTER TABLE workspace_conversations ADD COLUMN model TEXT DEFAULT 'opus'"
                )
            if "effort" not in existing_cols:
                cursor.execute(
                    "ALTER TABLE workspace_conversations ADD COLUMN effort TEXT DEFAULT 'high'"
                )
            if "branch_name" not in existing_cols:
                cursor.execute(
                    "ALTER TABLE workspace_conversations ADD COLUMN branch_name TEXT"
                )
            if "provider" not in existing_cols:
                cursor.execute(
                    "ALTER TABLE workspace_conversations ADD COLUMN provider TEXT NOT NULL DEFAULT 'claude'"
                )
            if "provider_thread_id" not in existing_cols:
                cursor.execute(
                    "ALTER TABLE workspace_conversations ADD COLUMN provider_thread_id TEXT"
                )

            # Migrate workspace_library_files: add folder_id if missing
            cursor.execute("PRAGMA table_info(workspace_library_files)")
            lib_cols = {row[1] for row in cursor.fetchall()}
            if lib_cols and "folder_id" not in lib_cols:
                cursor.execute(
                    "ALTER TABLE workspace_library_files ADD COLUMN folder_id INTEGER"
                )

            # One-time fix: early migration defaulted context_mode to '200k' but
            # the workspace actually uses '1m' by default.  All conversations
            # created before split-view existed were 1M context sessions.
            cursor.execute("PRAGMA user_version")
            db_version = cursor.fetchone()[0]
            if db_version < 1:
                cursor.execute(
                    "UPDATE workspace_conversations SET context_mode = '1m' "
                    "WHERE context_mode = '200k' OR context_mode IS NULL"
                )
                cursor.execute("PRAGMA user_version = 1")

            conn.commit()
            conn.close()

            _engine_cache[cache_key] = engine
            logger.debug("Created workspace database engine at %s", cache_key)

    return _engine_cache[cache_key]


def get_db_session():
    """Get a new database session for the workspace database."""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


# ============================================================================
# Token Estimation
# ============================================================================

def estimate_tokens(text: str) -> int:
    """Estimate the number of tokens in a text string.

    Uses a simple heuristic of ~4 characters per token, which is a reasonable
    approximation for English text with Claude models.
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


# ============================================================================
# Conversation Operations
# ============================================================================

def create_conversation(
    title: Optional[str] = None,
    category: str = "general",
    working_directory: Optional[str] = None,
    context_mode: Optional[str] = None,
    model: Optional[str] = None,
    effort: Optional[str] = None,
    provider: Optional[str] = None,
) -> WorkspaceConversation:
    """Create a new workspace conversation.

    Args:
        title: Optional conversation title. If not provided, it will be
            auto-generated from the first user message.
        category: Conversation category (default: "general").
        working_directory: Optional working directory path for the conversation.
        context_mode: Context window mode ("1m" or "200k").
        model: Model shorthand ("opus" or "sonnet").
        effort: Thinking effort level ("low", "medium", "high").
        provider: CLI provider ("claude", "codex", or "gemini").

    Returns:
        The newly created WorkspaceConversation instance.
    """
    session = get_db_session()
    try:
        conversation = WorkspaceConversation(
            title=title,
            category=category,
            working_directory=working_directory,
            context_mode=context_mode or "200k",
            model=model or "opus",
            effort=effort or "high",
            provider=provider or "claude",
        )
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
        logger.info("Created workspace conversation %d (category=%s)", conversation.id, category)
        return conversation
    finally:
        session.close()


def get_conversations(category: Optional[str] = None) -> list[dict]:
    """Get all workspace conversations with message counts.

    Uses a subquery for message_count to avoid the N+1 query problem.

    Args:
        category: Optional filter by category. If None, returns all conversations.

    Returns:
        List of conversation dicts ordered by most recently updated first.
    """
    session = get_db_session()
    try:
        # Subquery to count messages per conversation (avoids N+1 query)
        message_count_subquery = (
            session.query(
                WorkspaceMessage.conversation_id,
                func.count(WorkspaceMessage.id).label("message_count")
            )
            .group_by(WorkspaceMessage.conversation_id)
            .subquery()
        )

        # Build the base query with the message count join
        query = (
            session.query(
                WorkspaceConversation,
                func.coalesce(message_count_subquery.c.message_count, 0).label("message_count")
            )
            .outerjoin(
                message_count_subquery,
                WorkspaceConversation.id == message_count_subquery.c.conversation_id
            )
        )

        if category is not None:
            query = query.filter(WorkspaceConversation.category == category)

        conversations = query.order_by(WorkspaceConversation.updated_at.desc()).all()

        return [
            {
                "id": row.WorkspaceConversation.id,
                "title": row.WorkspaceConversation.title,
                "category": row.WorkspaceConversation.category,
                "working_directory": row.WorkspaceConversation.working_directory,
                "pinned": bool(row.WorkspaceConversation.pinned),
                "tags": row.WorkspaceConversation.tags or "",
                "context_mode": row.WorkspaceConversation.context_mode or "200k",
                "model": row.WorkspaceConversation.model or "opus",
                "effort": row.WorkspaceConversation.effort or "high",
                "provider": row.WorkspaceConversation.provider or "claude",
                "created_at": (
                    row.WorkspaceConversation.created_at.isoformat()
                    if row.WorkspaceConversation.created_at else None
                ),
                "updated_at": (
                    row.WorkspaceConversation.updated_at.isoformat()
                    if row.WorkspaceConversation.updated_at else None
                ),
                "message_count": row.message_count,
            }
            for row in conversations
        ]
    finally:
        session.close()


def get_conversation(conversation_id: int) -> Optional[dict]:
    """Get a single conversation with all its messages.

    Args:
        conversation_id: The conversation ID to retrieve.

    Returns:
        A dict with conversation details and messages, or None if not found.
    """
    session = get_db_session()
    try:
        conversation = (
            session.query(WorkspaceConversation)
            .filter(WorkspaceConversation.id == conversation_id)
            .first()
        )
        if not conversation:
            return None
        return {
            "id": conversation.id,
            "title": conversation.title,
            "category": conversation.category,
            "working_directory": conversation.working_directory,
            "pinned": bool(conversation.pinned),
            "tags": conversation.tags or "",
            "context_mode": conversation.context_mode or "200k",
            "model": conversation.model or "opus",
            "effort": conversation.effort or "high",
            "provider": conversation.provider or "claude",
            "provider_thread_id": conversation.provider_thread_id,
            "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
            "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "token_estimate": m.token_estimate,
                    "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                }
                for m in sorted(conversation.messages, key=lambda x: x.timestamp or datetime.min)
            ],
        }
    finally:
        session.close()


def delete_conversation(conversation_id: int) -> bool:
    """Delete a conversation, its messages, and orphaned token log entries.

    Messages cascade via the SQLAlchemy relationship on WorkspaceConversation.
    Token log entries have no FK constraint, so we delete them explicitly.

    Args:
        conversation_id: The conversation ID to delete.

    Returns:
        True if the conversation was deleted, False if it was not found.
    """
    session = get_db_session()
    try:
        conversation = (
            session.query(WorkspaceConversation)
            .filter(WorkspaceConversation.id == conversation_id)
            .first()
        )
        if not conversation:
            return False
        # Delete orphaned token log entries (no FK cascade on this table)
        token_log_count = (
            session.query(WorkspaceTokenLog)
            .filter(WorkspaceTokenLog.conversation_id == conversation_id)
            .delete(synchronize_session=False)
        )
        session.delete(conversation)
        session.commit()
        logger.info(
            "Deleted workspace conversation %d (+ %d token log entries)",
            conversation_id, token_log_count,
        )
        return True
    except Exception:
        session.rollback()
        logger.exception("Failed to delete workspace conversation %d", conversation_id)
        raise
    finally:
        session.close()


def delete_conversations_bulk(conversation_ids: list[int]) -> int:
    """Delete multiple conversations in a single transaction.

    Args:
        conversation_ids: List of conversation IDs to delete.

    Returns:
        Number of conversations actually deleted.
    """
    if not conversation_ids:
        return 0

    session = get_db_session()
    try:
        # Delete orphaned token log entries first
        session.query(WorkspaceTokenLog).filter(
            WorkspaceTokenLog.conversation_id.in_(conversation_ids)
        ).delete(synchronize_session=False)

        # Delete the conversations (messages cascade via relationship)
        count = (
            session.query(WorkspaceConversation)
            .filter(WorkspaceConversation.id.in_(conversation_ids))
            .delete(synchronize_session=False)
        )
        session.commit()
        logger.info("Bulk deleted %d workspace conversations", count)
        return count
    except Exception:
        session.rollback()
        logger.exception("Failed to bulk delete workspace conversations")
        raise
    finally:
        session.close()


def update_conversation(
    conversation_id: int,
    title: Optional[str] = None,
    category: Optional[str] = None,
    working_directory: Optional[str] = None,
    pinned: Optional[bool] = None,
    tags: Optional[str] = None,
    context_mode: Optional[str] = None,
    model: Optional[str] = None,
    effort: Optional[str] = None,
    provider: Optional[str] = None,
    provider_thread_id: Optional[str] = None,
) -> Optional[dict]:
    """Update a conversation's metadata.

    Only the fields that are provided (not None) will be updated.

    Args:
        conversation_id: The conversation ID to update.
        title: New title, or None to leave unchanged.
        category: New category, or None to leave unchanged.
        working_directory: New working directory, or None to leave unchanged.
        pinned: New pinned state, or None to leave unchanged.
        tags: New comma-separated tags, or None to leave unchanged.
        context_mode: New context mode (``"1m"`` or ``"200k"``), or None to leave unchanged.
        model: New model shorthand (``"opus"`` or ``"sonnet"``), or None to leave unchanged.
        provider: CLI provider (``"claude"``, ``"codex"``, or ``"gemini"``), or None.
        provider_thread_id: Provider session/thread ID for continuity, or None.

    Returns:
        Updated conversation dict, or None if the conversation was not found.
    """
    session = get_db_session()
    try:
        conversation = (
            session.query(WorkspaceConversation)
            .filter(WorkspaceConversation.id == conversation_id)
            .first()
        )
        if not conversation:
            return None

        if title is not None:
            conversation.title = title
        if category is not None:
            conversation.category = category
        if working_directory is not None:
            conversation.working_directory = working_directory
        if pinned is not None:
            conversation.pinned = 1 if pinned else 0
        if tags is not None:
            conversation.tags = tags
        if context_mode is not None:
            conversation.context_mode = context_mode
        if model is not None:
            conversation.model = model
        if effort is not None:
            conversation.effort = effort
        if provider is not None:
            conversation.provider = provider
        if provider_thread_id is not None:
            conversation.provider_thread_id = provider_thread_id

        conversation.updated_at = _utc_now()
        session.commit()
        session.refresh(conversation)

        msg_count = (
            session.query(WorkspaceMessage)
            .filter(WorkspaceMessage.conversation_id == conversation_id)
            .count()
        )

        logger.debug("Updated workspace conversation %d", conversation_id)
        return {
            "id": conversation.id,
            "title": conversation.title,
            "category": conversation.category,
            "working_directory": conversation.working_directory,
            "pinned": bool(conversation.pinned),
            "tags": conversation.tags or "",
            "context_mode": conversation.context_mode or "200k",
            "model": conversation.model or "opus",
            "effort": conversation.effort or "high",
            "provider": conversation.provider or "claude",
            "provider_thread_id": conversation.provider_thread_id,
            "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
            "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
            "message_count": msg_count,
        }
    finally:
        session.close()


# ============================================================================
# Message Operations
# ============================================================================

def add_message(
    conversation_id: int, role: str, content: str, token_estimate: Optional[int] = None
) -> Optional[dict]:
    """Add a message to a conversation.

    Automatically estimates token count and sets it on the message unless
    a pre-computed ``token_estimate`` is provided.
    Auto-generates a conversation title from the first user message if
    no title has been set yet.

    Args:
        conversation_id: The conversation to add the message to.
        role: Message role ("user", "assistant", or "system").
        content: The message content.
        token_estimate: Optional pre-computed token count. If None, auto-estimated.

    Returns:
        A dict with the new message details, or None if the conversation was not found.
    """
    session = get_db_session()
    try:
        conversation = (
            session.query(WorkspaceConversation)
            .filter(WorkspaceConversation.id == conversation_id)
            .first()
        )
        if not conversation:
            return None

        tokens = token_estimate if token_estimate is not None else estimate_tokens(content)

        message = WorkspaceMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            token_estimate=tokens,
        )
        session.add(message)

        # Update conversation's updated_at timestamp
        conversation.updated_at = _utc_now()

        # Auto-generate title from first user message if not set
        if not conversation.title and role == "user":
            conversation.title = content[:50] + ("..." if len(content) > 50 else "")

        session.commit()
        session.refresh(message)

        logger.debug("Added %s message to workspace conversation %d", role, conversation_id)
        return {
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "token_estimate": message.token_estimate,
            "timestamp": message.timestamp.isoformat() if message.timestamp else None,
        }
    finally:
        session.close()


def get_messages(conversation_id: int) -> list[dict]:
    """Get all messages for a conversation in chronological order.

    Args:
        conversation_id: The conversation to retrieve messages from.

    Returns:
        List of message dicts ordered by timestamp ascending.
    """
    session = get_db_session()
    try:
        messages = (
            session.query(WorkspaceMessage)
            .filter(WorkspaceMessage.conversation_id == conversation_id)
            .order_by(WorkspaceMessage.timestamp.asc())
            .all()
        )
        return [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "token_estimate": m.token_estimate,
                "timestamp": m.timestamp.isoformat() if m.timestamp else None,
            }
            for m in messages
        ]
    finally:
        session.close()


def get_conversation_token_total(conversation_id: int) -> int:
    """Get the total estimated token count for all messages in a conversation.

    Args:
        conversation_id: The conversation to calculate tokens for.

    Returns:
        Total estimated token count across all messages. Returns 0 if
        the conversation has no messages or does not exist.
    """
    session = get_db_session()
    try:
        result = (
            session.query(func.coalesce(func.sum(WorkspaceMessage.token_estimate), 0))
            .filter(WorkspaceMessage.conversation_id == conversation_id)
            .scalar()
        )
        return int(result)
    finally:
        session.close()


def get_message_count(conversation_id: int) -> int:
    """Get the count of messages in a conversation.

    Args:
        conversation_id: The conversation to count messages for.

    Returns:
        Number of messages in the conversation.
    """
    session = get_db_session()
    try:
        count = (
            session.query(func.count(WorkspaceMessage.id))
            .filter(WorkspaceMessage.conversation_id == conversation_id)
            .scalar()
        )
        return int(count or 0)
    finally:
        session.close()


# ============================================================================
# Summary Operations
# ============================================================================

def save_summary(conversation_id: int, summary_text: str, message_count: int) -> dict:
    """Save a new summary and update the conversation's cached summary.

    Creates a new ``WorkspaceSummary`` record and also caches the summary
    text and updated-at timestamp directly on the conversation row for
    fast retrieval without joining.

    Args:
        conversation_id: The conversation to save the summary for.
        summary_text: The generated summary text.
        message_count: Total messages in the conversation at generation time.

    Returns:
        A dict representing the saved summary record.
    """
    session = get_db_session()
    try:
        token_est = len(summary_text) // 3

        # Create summary record
        summary = WorkspaceSummary(
            conversation_id=conversation_id,
            summary=summary_text,
            message_count=message_count,
            token_estimate=token_est,
        )
        session.add(summary)

        # Update cached summary on conversation
        conversation = session.query(WorkspaceConversation).filter(
            WorkspaceConversation.id == conversation_id
        ).first()
        if conversation:
            conversation.summary = summary_text
            conversation.summary_updated_at = _utc_now()
            conversation.token_count = _calculate_conversation_tokens(session, conversation_id)

        session.commit()
        session.refresh(summary)
        return {
            "id": summary.id,
            "conversation_id": summary.conversation_id,
            "summary": summary.summary,
            "message_count": summary.message_count,
            "token_estimate": summary.token_estimate,
            "created_at": summary.created_at.isoformat() if summary.created_at else None,
        }
    finally:
        session.close()


def get_latest_summary(conversation_id: int) -> Optional[dict]:
    """Get the most recent summary for a conversation.

    Args:
        conversation_id: The conversation to get the summary for.

    Returns:
        A dict with the latest summary details, or None if no summary exists.
    """
    session = get_db_session()
    try:
        summary = (
            session.query(WorkspaceSummary)
            .filter(WorkspaceSummary.conversation_id == conversation_id)
            .order_by(WorkspaceSummary.created_at.desc())
            .first()
        )
        if not summary:
            return None
        return {
            "id": summary.id,
            "conversation_id": summary.conversation_id,
            "summary": summary.summary,
            "message_count": summary.message_count,
            "token_estimate": summary.token_estimate,
            "created_at": summary.created_at.isoformat() if summary.created_at else None,
        }
    finally:
        session.close()


def get_summary_history(conversation_id: int) -> list[dict]:
    """Get all summaries for a conversation, newest first.

    Args:
        conversation_id: The conversation to retrieve summary history for.

    Returns:
        List of summary dicts ordered by creation time descending.
    """
    session = get_db_session()
    try:
        summaries = (
            session.query(WorkspaceSummary)
            .filter(WorkspaceSummary.conversation_id == conversation_id)
            .order_by(WorkspaceSummary.created_at.desc())
            .all()
        )
        return [
            {
                "id": s.id,
                "conversation_id": s.conversation_id,
                "summary": s.summary,
                "message_count": s.message_count,
                "token_estimate": s.token_estimate,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in summaries
        ]
    finally:
        session.close()


def _calculate_conversation_tokens(session, conversation_id: int) -> int:
    """Calculate total token count for a conversation's messages.

    This is an internal helper that reuses an existing database session
    (to be called within an active transaction).

    Args:
        session: An active SQLAlchemy session.
        conversation_id: The conversation to calculate tokens for.

    Returns:
        Total estimated token count across all messages.
    """
    result = session.query(
        func.coalesce(func.sum(WorkspaceMessage.token_estimate), 0)
    ).filter(
        WorkspaceMessage.conversation_id == conversation_id
    ).scalar()
    return int(result)


# ============================================================================
# Category Operations
# ============================================================================

def create_category(name: str, color: Optional[str] = None) -> dict:
    """Create a new user-defined category.

    Automatically assigns the next sort_order value so new categories
    appear at the end of the list.

    Args:
        name: The category name (must be unique).
        color: Optional hex color string, e.g. ``"#3b82f6"``.

    Returns:
        A dict representing the created category.
    """
    session = get_db_session()
    try:
        max_order = session.query(func.max(WorkspaceCategory.sort_order)).scalar() or 0
        category = WorkspaceCategory(
            name=name,
            color=color,
            sort_order=max_order + 1,
        )
        session.add(category)
        session.commit()
        session.refresh(category)
        return _category_to_dict(category)
    finally:
        session.close()


def get_categories() -> list[dict]:
    """Get all categories ordered by sort_order.

    Returns:
        List of category dicts ordered by sort_order ascending.
    """
    session = get_db_session()
    try:
        categories = (
            session.query(WorkspaceCategory)
            .order_by(WorkspaceCategory.sort_order.asc())
            .all()
        )
        return [_category_to_dict(c) for c in categories]
    finally:
        session.close()


def update_category(
    category_id: int,
    name: Optional[str] = None,
    color: Optional[str] = None,
) -> Optional[dict]:
    """Update a category's name and/or color.

    Only the fields that are provided (not None) will be updated.

    Args:
        category_id: The category ID to update.
        name: New name, or None to leave unchanged.
        color: New color, or None to leave unchanged.

    Returns:
        Updated category dict, or None if the category was not found.
    """
    session = get_db_session()
    try:
        category = (
            session.query(WorkspaceCategory)
            .filter(WorkspaceCategory.id == category_id)
            .first()
        )
        if not category:
            return None
        if name is not None:
            category.name = name
        if color is not None:
            category.color = color
        session.commit()
        session.refresh(category)
        return _category_to_dict(category)
    finally:
        session.close()


def delete_category(category_id: int) -> bool:
    """Delete a category. Conversations in this category become 'Uncategorized'.

    Args:
        category_id: The category ID to delete.

    Returns:
        True if the category was deleted, False if it was not found.
    """
    session = get_db_session()
    try:
        category = (
            session.query(WorkspaceCategory)
            .filter(WorkspaceCategory.id == category_id)
            .first()
        )
        if not category:
            return False
        # Move conversations to Uncategorized
        session.query(WorkspaceConversation).filter(
            WorkspaceConversation.category == category.name
        ).update({"category": "Uncategorized"})
        session.delete(category)
        session.commit()
        return True
    finally:
        session.close()


def reorder_categories(ordered_ids: list[int]) -> list[dict]:
    """Update sort_order for categories based on the provided ID order.

    Each category's ``sort_order`` is set to its index in the provided list.

    Args:
        ordered_ids: List of category IDs in the desired display order.

    Returns:
        The full list of categories with updated sort_order values.
    """
    session = get_db_session()
    try:
        for index, cat_id in enumerate(ordered_ids):
            session.query(WorkspaceCategory).filter(
                WorkspaceCategory.id == cat_id
            ).update({"sort_order": index})
        session.commit()
    finally:
        session.close()
    return get_categories()


def _category_to_dict(category: WorkspaceCategory) -> dict:
    """Convert a WorkspaceCategory ORM instance to a plain dict.

    Args:
        category: The category ORM object.

    Returns:
        A serializable dict with all category fields.
    """
    return {
        "id": category.id,
        "name": category.name,
        "color": category.color,
        "sort_order": category.sort_order,
        "created_at": category.created_at.isoformat() if category.created_at else None,
    }


# ============================================================================
# Search Operations
# ============================================================================

def search_conversations(query: str, limit: int = 20) -> list[dict]:
    """Full-text search across conversation titles and message content.

    Searches conversations by title first, then searches message content
    and groups results by conversation_id. Returns conversations with up
    to 2 matching message excerpts each.

    Args:
        query: The search string to match (case-insensitive LIKE).
        limit: Maximum number of conversation results to return.

    Returns:
        List of search result dicts sorted by relevance (most matches first).
    """
    session = get_db_session()
    try:
        results: dict[int, dict] = {}
        search_pattern = f"%{query}%"

        # 1. Search by conversation title
        title_matches = (
            session.query(WorkspaceConversation)
            .filter(WorkspaceConversation.title.ilike(search_pattern))
            .limit(limit)
            .all()
        )
        for conv in title_matches:
            results[conv.id] = {
                "conversation_id": conv.id,
                "conversation_title": conv.title,
                "category": conv.category,
                "matching_excerpts": [],
            }

        # 2. Search by message content
        message_matches = (
            session.query(WorkspaceMessage)
            .filter(WorkspaceMessage.content.ilike(search_pattern))
            .order_by(WorkspaceMessage.timestamp.desc())
            .limit(limit * 3)  # Get extra to allow grouping
            .all()
        )

        for msg in message_matches:
            cid = msg.conversation_id
            if cid not in results:
                # Load the conversation
                conv = session.query(WorkspaceConversation).filter(
                    WorkspaceConversation.id == cid
                ).first()
                if not conv:
                    continue
                results[cid] = {
                    "conversation_id": cid,
                    "conversation_title": conv.title,
                    "category": conv.category,
                    "matching_excerpts": [],
                }

            # Extract excerpt around the match (max 2 excerpts per conversation)
            if len(results[cid]["matching_excerpts"]) < 2:
                excerpt = _extract_excerpt(msg.content, query, context_chars=80)
                results[cid]["matching_excerpts"].append({
                    "message_id": msg.id,
                    "role": msg.role,
                    "excerpt": excerpt,
                })

        # Sort by number of matches (most relevant first) and limit
        sorted_results = sorted(
            results.values(),
            key=lambda r: len(r["matching_excerpts"]),
            reverse=True,
        )
        return sorted_results[:limit]

    finally:
        session.close()


def _extract_excerpt(content: str, query: str, context_chars: int = 80) -> str:
    """Extract a text excerpt centered around the first occurrence of query.

    Args:
        content: The full message content to extract from.
        query: The search query to center the excerpt around.
        context_chars: Number of characters of context on each side of the match.

    Returns:
        A string excerpt with ellipsis markers if truncated.
    """
    lower_content = content.lower()
    lower_query = query.lower()
    idx = lower_content.find(lower_query)
    if idx == -1:
        # Shouldn't happen but fallback to start of content
        return content[:context_chars * 2] + ("..." if len(content) > context_chars * 2 else "")

    start = max(0, idx - context_chars)
    end = min(len(content), idx + len(query) + context_chars)
    excerpt = content[start:end]

    if start > 0:
        excerpt = "..." + excerpt
    if end < len(content):
        excerpt = excerpt + "..."

    return excerpt


# ============================================================================
# Enhanced Context Loading
# ============================================================================

def get_messages_for_context(
    conversation_id: int,
    token_budget: int = 400_000,
) -> tuple[list[dict], int]:
    """Load messages dynamically based on token budget.

    Always loads most-recent messages first until the budget is exhausted.
    At least one message is always included even if it exceeds the budget.

    Args:
        conversation_id: The conversation to load messages from.
        token_budget: Maximum tokens to allocate for messages.

    Returns:
        A tuple of (messages_oldest_first, total_token_count).
    """
    session = get_db_session()
    try:
        # Get messages in reverse chronological order
        messages = (
            session.query(WorkspaceMessage)
            .filter(WorkspaceMessage.conversation_id == conversation_id)
            .order_by(WorkspaceMessage.timestamp.desc())
            .all()
        )

        selected: list[dict] = []
        total_tokens = 0

        for msg in messages:
            estimate = msg.token_estimate or (len(msg.content) // 3)
            if total_tokens + estimate > token_budget and selected:
                break  # Budget exhausted (always include at least 1 message)
            total_tokens += estimate
            selected.append({
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "token_estimate": estimate,
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
            })

        # Reverse to chronological order
        selected.reverse()
        return selected, total_tokens

    finally:
        session.close()


# ============================================================================
# Fork, Paginate, and Export Operations (Phase 4)
# ============================================================================

def fork_conversation(
    conversation_id: int,
    fork_at_message_id: int | None = None,
    *,
    title: str | None = None,
    category: str | None = None,
    context_mode: str | None = None,
    model: str | None = None,
    effort: str | None = None,
    provider: str | None = None,
    working_directory: str | None = None,
) -> dict:
    """Fork a conversation, copying messages up to fork_at_message_id.

    Args:
        conversation_id: The source conversation ID.
        fork_at_message_id: Copy messages up to and including this message.
            If None, copies all messages.
        title: Override title (default: "{source title} (fork)").
        category: Override category (default: source category).
        context_mode: Override context mode (default: source context_mode).
        model: Override model (default: source model).
        effort: Override effort (default: source effort).
        provider: Override provider (default: source provider).
        working_directory: Override working directory (default: source working_directory).

    Returns:
        Dict representing the new conversation (same shape as get_conversations items).

    Raises:
        ValueError: If conversation_id or fork_at_message_id not found.
    """
    session = get_db_session()
    try:
        source = (
            session.query(WorkspaceConversation)
            .filter(WorkspaceConversation.id == conversation_id)
            .first()
        )
        if not source:
            raise ValueError(f"Conversation {conversation_id} not found")

        fork_title = title or f"{source.title or 'Untitled'} (fork)"

        new_conv = WorkspaceConversation(
            title=fork_title,
            category=category or source.category,
            pinned=0,
            tags=source.tags,
            context_mode=context_mode or source.context_mode or "200k",
            model=model or source.model or "opus",
            effort=effort or source.effort or "high",
            provider=provider or getattr(source, "provider", None) or "claude",
            working_directory=working_directory or source.working_directory,
            token_count=0,
            forked_from_id=conversation_id,
        )
        session.add(new_conv)
        session.flush()

        query = (
            session.query(WorkspaceMessage)
            .filter(WorkspaceMessage.conversation_id == conversation_id)
            .order_by(WorkspaceMessage.id.asc())
        )

        if fork_at_message_id is not None:
            fork_msg = (
                session.query(WorkspaceMessage)
                .filter_by(id=fork_at_message_id, conversation_id=conversation_id)
                .first()
            )
            if not fork_msg:
                raise ValueError(
                    f"Message {fork_at_message_id} not found in conversation {conversation_id}"
                )
            query = query.filter(WorkspaceMessage.id <= fork_at_message_id)

        messages = query.all()

        total_tokens = 0
        for msg in messages:
            new_msg = WorkspaceMessage(
                conversation_id=new_conv.id,
                role=msg.role,
                content=msg.content,
                token_estimate=msg.token_estimate,
            )
            session.add(new_msg)
            total_tokens += msg.token_estimate or 0

        new_conv.token_count = total_tokens
        session.commit()
        session.refresh(new_conv)

        return {
            "id": new_conv.id,
            "title": new_conv.title,
            "category": new_conv.category,
            "pinned": bool(new_conv.pinned),
            "tags": new_conv.tags or "",
            "context_mode": new_conv.context_mode or "200k",
            "model": new_conv.model or "opus",
            "effort": new_conv.effort or "high",
            "provider": getattr(new_conv, "provider", None) or "claude",
            "working_directory": new_conv.working_directory,
            "token_count": new_conv.token_count,
            "forked_from_id": new_conv.forked_from_id,
            "created_at": new_conv.created_at.isoformat() if new_conv.created_at else None,
            "updated_at": new_conv.updated_at.isoformat() if new_conv.updated_at else None,
            "message_count": len(messages),
        }
    finally:
        session.close()


def get_messages_paginated(
    conversation_id: int,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """Get paginated messages for a conversation.

    Args:
        conversation_id: The conversation to retrieve messages from.
        limit: Maximum number of messages to return.
        offset: Number of messages to skip.

    Returns:
        Dict with ``messages`` list and ``total`` count.
    """
    session = get_db_session()
    try:
        total = (
            session.query(func.count(WorkspaceMessage.id))
            .filter(WorkspaceMessage.conversation_id == conversation_id)
            .scalar()
        ) or 0

        messages = (
            session.query(WorkspaceMessage)
            .filter(WorkspaceMessage.conversation_id == conversation_id)
            .order_by(WorkspaceMessage.id.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return {
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "token_estimate": m.token_estimate,
                    "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                }
                for m in messages
            ],
            "total": total,
        }
    finally:
        session.close()


def export_conversation_markdown(conversation_id: int) -> str:
    """Export a conversation as formatted markdown.

    Args:
        conversation_id: The conversation to export.

    Returns:
        Markdown string.

    Raises:
        ValueError: If conversation not found.
    """
    session = get_db_session()
    try:
        conv = (
            session.query(WorkspaceConversation)
            .filter(WorkspaceConversation.id == conversation_id)
            .first()
        )
        if not conv:
            raise ValueError(f"Conversation {conversation_id} not found")

        messages = (
            session.query(WorkspaceMessage)
            .filter(WorkspaceMessage.conversation_id == conversation_id)
            .order_by(WorkspaceMessage.id.asc())
            .all()
        )

        lines: list[str] = []
        lines.append(f"# {conv.title or 'Untitled Conversation'}")
        lines.append("")

        if conv.category:
            lines.append(f"**Category:** {conv.category}")
        if conv.created_at:
            lines.append(f"**Created:** {conv.created_at.strftime('%Y-%m-%d %H:%M UTC')}")
        lines.append(f"**Messages:** {len(messages)}")
        if conv.token_count:
            lines.append(f"**Tokens Used:** {conv.token_count:,}")
        lines.append("")

        if conv.summary:
            lines.append("---")
            lines.append("")
            lines.append("## Summary")
            lines.append("")
            lines.append(conv.summary)
            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("## Conversation")
        lines.append("")

        for msg in messages:
            role_label = "User" if msg.role == "user" else "Assistant"
            timestamp_str = ""
            if msg.timestamp:
                timestamp_str = f" ({msg.timestamp.strftime('%Y-%m-%d %H:%M UTC')})"
            lines.append(f"**{role_label}**{timestamp_str}:")
            lines.append("")
            lines.append(msg.content)
            lines.append("")

        return "\n".join(lines)
    finally:
        session.close()


# ============================================================================
# Usage Tracking Operations
# ============================================================================

def get_usage_by_period(period: str = "daily") -> dict:
    """Get token usage aggregated by time period.

    Args:
        period: "daily", "weekly", or "monthly"

    Returns:
        Dict with total_tokens, conversation_count, and period_label.
    """
    session = get_db_session()
    try:
        now = _utc_now()

        if period == "daily":
            cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
            label = "Today"
        elif period == "weekly":
            # Start of current week (Monday)
            days_since_monday = now.weekday()
            cutoff = (now - timedelta(days=days_since_monday)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            label = "This Week"
        else:  # monthly
            cutoff = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            label = "This Month"

        # Sum all message token estimates since cutoff
        total = (
            session.query(func.coalesce(func.sum(WorkspaceMessage.token_estimate), 0))
            .filter(WorkspaceMessage.timestamp >= cutoff)
            .scalar()
        )

        # Count distinct conversations with activity in this period
        conv_count = (
            session.query(func.count(func.distinct(WorkspaceMessage.conversation_id)))
            .filter(WorkspaceMessage.timestamp >= cutoff)
            .scalar()
        )

        # Count messages in this period
        msg_count = (
            session.query(func.count(WorkspaceMessage.id))
            .filter(WorkspaceMessage.timestamp >= cutoff)
            .scalar()
        )

        return {
            "period": period,
            "label": label,
            "total_tokens": int(total),
            "conversation_count": int(conv_count or 0),
            "message_count": int(msg_count or 0),
            "since": cutoff.isoformat(),
        }
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Model pricing (per million tokens, USD) -- Anthropic official rates
# ---------------------------------------------------------------------------
# Each model maps to (standard_input, extended_input, standard_output, extended_output).
# Extended rates apply to tokens beyond 200K context.
# Cache rates are derived: cache_read = 0.1x standard input, cache_creation = 1.25x standard input.

_MODEL_PRICING: dict[str, dict[str, float]] = {
    "opus": {
        "standard_input": 5.0,
        "extended_input": 10.0,
        "standard_output": 25.0,
        "extended_output": 37.50,
    },
    "sonnet": {
        "standard_input": 3.0,
        "extended_input": 6.0,
        "standard_output": 15.0,
        "extended_output": 22.50,
    },
}


def _get_model_rates(model: str = "opus") -> dict[str, float]:
    """Return the pricing rates for a given model shorthand.

    Falls back to Opus pricing for unknown model names.
    """
    return _MODEL_PRICING.get(model, _MODEL_PRICING["opus"])


def get_conversation_cost_zones(conversation_id: int, model: str = "opus") -> dict:
    """Calculate the cost zone breakdown for a conversation.

    Tokens in 0-200K are "standard tier", tokens beyond 200K are "premium tier"
    (extended context pricing applies beyond 200K).

    Args:
        conversation_id: The conversation to analyze.
        model: Model shorthand ("opus" or "sonnet") for pricing lookup.

    Returns:
        Dict with standard_tokens, premium_tokens, and estimated costs.
    """
    session = get_db_session()
    try:
        total = (
            session.query(func.coalesce(func.sum(WorkspaceMessage.token_estimate), 0))
            .filter(WorkspaceMessage.conversation_id == conversation_id)
            .scalar()
        )
        total = int(total)

        STANDARD_LIMIT = 200_000
        rates = _get_model_rates(model)
        standard_input_rate = rates["standard_input"]
        extended_input_rate = rates["extended_input"]

        standard_tokens = min(total, STANDARD_LIMIT)
        premium_tokens = max(0, total - STANDARD_LIMIT)

        standard_cost = (standard_tokens / 1_000_000) * standard_input_rate
        premium_cost = (premium_tokens / 1_000_000) * extended_input_rate
        total_cost = standard_cost + premium_cost

        # What it would cost if ALL tokens were standard rate
        all_standard_cost = (total / 1_000_000) * standard_input_rate

        return {
            "total_tokens": total,
            "standard_tokens": standard_tokens,
            "premium_tokens": premium_tokens,
            "standard_limit": STANDARD_LIMIT,
            "model": model,
            "estimated_cost": {
                "standard_portion": round(standard_cost, 4),
                "premium_portion": round(premium_cost, 4),
                "total": round(total_cost, 4),
                "all_standard_equivalent": round(all_standard_cost, 4),
                "premium_surcharge": round(
                    premium_cost - (premium_tokens / 1_000_000 * standard_input_rate), 4
                ),
            },
            "cost_zone": "standard" if premium_tokens == 0 else "premium",
        }
    finally:
        session.close()


def get_usage_summary() -> dict:
    """Get a comprehensive usage summary across all time periods.

    Returns:
        Dict with daily, weekly, monthly usage and rate limit events.
    """
    daily = get_usage_by_period("daily")
    weekly = get_usage_by_period("weekly")
    monthly = get_usage_by_period("monthly")

    return {
        "daily": daily,
        "weekly": weekly,
        "monthly": monthly,
    }


# ============================================================================
# Rate Limit Learning Operations
# ============================================================================

def log_rate_limit_event(
    event_type: str,
    tokens_at_hit: int,
    premium_tokens_at_hit: int = 0,
    message_count_at_hit: int = 0,
    notes: str | None = None,
) -> dict:
    """Log a rate limit event for calibration.

    Args:
        event_type: "daily", "weekly", or "monthly"
        tokens_at_hit: Total tokens used when the limit was hit.
        premium_tokens_at_hit: Tokens in the 200K+ premium zone.
        message_count_at_hit: Number of messages sent during the period.
        notes: Optional notes about the event.

    Returns:
        Dict with the created event data.
    """
    session = get_db_session()
    try:
        now = _utc_now()

        if event_type == "daily":
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif event_type == "weekly":
            days_since_monday = now.weekday()
            period_start = (now - timedelta(days=days_since_monday)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        else:  # monthly
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        event = WorkspaceRateLimitEvent(
            event_type=event_type,
            timestamp=now,
            tokens_at_hit=tokens_at_hit,
            premium_tokens_at_hit=premium_tokens_at_hit,
            message_count_at_hit=message_count_at_hit,
            period_start=period_start,
            notes=notes,
        )
        session.add(event)
        session.commit()

        return {
            "id": event.id,
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat(),
            "tokens_at_hit": event.tokens_at_hit,
            "premium_tokens_at_hit": event.premium_tokens_at_hit,
            "message_count_at_hit": event.message_count_at_hit,
            "period_start": event.period_start.isoformat(),
        }
    finally:
        session.close()


def log_premium_usage(conversation_id: int, model: str = "opus") -> dict | None:
    """Log premium-zone usage for a conversation if it's in the premium zone.

    Called after each message to track when conversations enter the premium zone.
    Only creates a ledger entry if the conversation exceeds 200,000 tokens.

    Args:
        conversation_id: The conversation to check.
        model: Model shorthand ("opus" or "sonnet") for pricing lookup.

    Returns:
        Dict with the ledger entry data, or None if not in premium zone.
    """
    session = get_db_session()
    try:
        total = (
            session.query(func.coalesce(func.sum(WorkspaceMessage.token_estimate), 0))
            .filter(WorkspaceMessage.conversation_id == conversation_id)
            .scalar()
        )
        total = int(total)
        STANDARD_LIMIT = 200_000

        if total <= STANDARD_LIMIT:
            return None

        standard_tokens = STANDARD_LIMIT
        premium_tokens = total - STANDARD_LIMIT

        rates = _get_model_rates(model)
        cost = (
            (standard_tokens / 1_000_000 * rates["standard_input"])
            + (premium_tokens / 1_000_000 * rates["extended_input"])
        )

        entry = WorkspacePremiumLedger(
            conversation_id=conversation_id,
            total_tokens=total,
            standard_tokens=standard_tokens,
            premium_tokens=premium_tokens,
            estimated_cost=round(cost, 4),
        )
        session.add(entry)
        session.commit()

        return {
            "conversation_id": conversation_id,
            "total_tokens": total,
            "standard_tokens": standard_tokens,
            "premium_tokens": premium_tokens,
            "estimated_cost": round(cost, 4),
        }
    finally:
        session.close()


def get_rate_limit_history(limit: int = 20) -> list[dict]:
    """Get recent rate limit events for calibration analysis.

    Returns:
        List of rate limit event dicts, most recent first.
    """
    session = get_db_session()
    try:
        events = (
            session.query(WorkspaceRateLimitEvent)
            .order_by(WorkspaceRateLimitEvent.timestamp.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": e.id,
                "event_type": e.event_type,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                "tokens_at_hit": e.tokens_at_hit,
                "premium_tokens_at_hit": e.premium_tokens_at_hit,
                "message_count_at_hit": e.message_count_at_hit,
                "period_start": e.period_start.isoformat() if e.period_start else None,
                "notes": e.notes,
            }
            for e in events
        ]
    finally:
        session.close()


def get_calibrated_limits() -> dict:
    """Calculate calibrated limits based on historical rate limit events.

    Uses the most recent rate limit event of each type (daily, weekly, monthly)
    to estimate token limits. Applies a 10% safety margin.

    Returns:
        Dict with estimated limits for each period type and confidence data.
    """
    session = get_db_session()
    try:
        result = {}
        for period_type in ("daily", "weekly", "monthly"):
            events = (
                session.query(WorkspaceRateLimitEvent)
                .filter(WorkspaceRateLimitEvent.event_type == period_type)
                .order_by(WorkspaceRateLimitEvent.timestamp.desc())
                .limit(5)
                .all()
            )
            if events:
                # Average the token counts from recent hits
                avg_tokens = sum(e.tokens_at_hit for e in events) / len(events)
                # Apply 10% safety margin (warn at 90% of observed limit)
                safe_limit = int(avg_tokens * 0.90)
                result[period_type] = {
                    "estimated_limit": int(avg_tokens),
                    "safe_limit": safe_limit,
                    "sample_count": len(events),
                    "last_hit": events[0].timestamp.isoformat() if events[0].timestamp else None,
                    "confidence": "high" if len(events) >= 3 else "medium" if len(events) >= 2 else "low",
                }
            else:
                result[period_type] = {
                    "estimated_limit": None,
                    "safe_limit": None,
                    "sample_count": 0,
                    "last_hit": None,
                    "confidence": "none",
                }
        return result
    finally:
        session.close()


def get_premium_usage_summary() -> dict:
    """Get a summary of premium-zone usage across all conversations.

    Returns:
        Dict with total premium tokens, total estimated cost, and
        per-conversation breakdown.
    """
    session = get_db_session()
    try:
        # Get the latest ledger entry for each conversation
        from sqlalchemy import func as sa_func

        subquery = (
            session.query(
                WorkspacePremiumLedger.conversation_id,
                sa_func.max(WorkspacePremiumLedger.id).label("max_id"),
            )
            .group_by(WorkspacePremiumLedger.conversation_id)
            .subquery()
        )

        latest_entries = (
            session.query(WorkspacePremiumLedger)
            .join(subquery, WorkspacePremiumLedger.id == subquery.c.max_id)
            .all()
        )

        total_premium = sum(e.premium_tokens for e in latest_entries)
        total_cost = sum(e.estimated_cost for e in latest_entries)

        conversations = [
            {
                "conversation_id": e.conversation_id,
                "total_tokens": e.total_tokens,
                "premium_tokens": e.premium_tokens,
                "estimated_cost": e.estimated_cost,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            }
            for e in latest_entries
        ]

        return {
            "total_premium_tokens": total_premium,
            "total_estimated_cost": round(total_cost, 4),
            "conversations_in_premium": len(conversations),
            "conversations": conversations,
        }
    finally:
        session.close()


# ============================================================================
# Notification Operations
# ============================================================================

VALID_NOTIFICATION_TYPES = ("summary", "roadmap", "progress", "milestone")


def _notification_to_dict(notification: WorkspaceNotification) -> dict:
    """Convert a WorkspaceNotification ORM instance to a plain dict.

    Deserializes the ``metadata_json`` column back to a Python dict (or None).

    Args:
        notification: The notification ORM object.

    Returns:
        A serializable dict with all notification fields.
    """
    metadata = None
    if notification.metadata_json:
        try:
            metadata = json.loads(notification.metadata_json)
        except (json.JSONDecodeError, TypeError):
            metadata = None

    return {
        "id": notification.id,
        "conversation_id": notification.conversation_id,
        "notification_type": notification.notification_type,
        "title": notification.title,
        "content": notification.content,
        "metadata": metadata,
        "is_read": bool(notification.is_read),
        "created_at": notification.created_at.isoformat() if notification.created_at else None,
        "updated_at": notification.updated_at.isoformat() if notification.updated_at else None,
    }


def create_notification(
    conversation_id: Optional[int],
    notification_type: str,
    title: str,
    content: str,
    metadata: Optional[dict] = None,
) -> dict:
    """Create a new workspace notification.

    Args:
        conversation_id: Optional conversation this notification belongs to.
        notification_type: One of "summary", "roadmap", "progress", "milestone".
        title: Short title for the notification.
        content: Full notification content.
        metadata: Optional JSON-serializable metadata dict.

    Returns:
        A dict representing the created notification.

    Raises:
        ValueError: If notification_type is not a valid type.
    """
    if notification_type not in VALID_NOTIFICATION_TYPES:
        raise ValueError(
            f"Invalid notification_type '{notification_type}'. "
            f"Must be one of: {', '.join(VALID_NOTIFICATION_TYPES)}"
        )

    session = get_db_session()
    try:
        metadata_json = json.dumps(metadata) if metadata is not None else None

        notification = WorkspaceNotification(
            conversation_id=conversation_id,
            notification_type=notification_type,
            title=title,
            content=content,
            metadata_json=metadata_json,
        )
        session.add(notification)
        session.commit()
        session.refresh(notification)
        logger.info(
            "Created notification %d (type=%s, conversation=%s)",
            notification.id, notification_type, conversation_id,
        )
        return _notification_to_dict(notification)
    finally:
        session.close()


def get_notifications(
    conversation_id: Optional[int] = None,
    notification_type: Optional[str] = None,
    limit: int = 50,
) -> list[dict]:
    """Get notifications with optional filters.

    Args:
        conversation_id: Filter by conversation ID. If None, returns all.
        notification_type: Filter by notification type. If None, returns all types.
        limit: Maximum number of notifications to return.

    Returns:
        List of notification dicts ordered by creation time descending (newest first).
    """
    session = get_db_session()
    try:
        query = session.query(WorkspaceNotification)

        if conversation_id is not None:
            query = query.filter(WorkspaceNotification.conversation_id == conversation_id)
        if notification_type is not None:
            query = query.filter(WorkspaceNotification.notification_type == notification_type)

        notifications = (
            query.order_by(WorkspaceNotification.created_at.desc())
            .limit(limit)
            .all()
        )
        return [_notification_to_dict(n) for n in notifications]
    finally:
        session.close()


def get_notification(notification_id: int) -> Optional[dict]:
    """Get a single notification by ID.

    Args:
        notification_id: The notification ID to retrieve.

    Returns:
        A notification dict, or None if not found.
    """
    session = get_db_session()
    try:
        notification = (
            session.query(WorkspaceNotification)
            .filter(WorkspaceNotification.id == notification_id)
            .first()
        )
        if not notification:
            return None
        return _notification_to_dict(notification)
    finally:
        session.close()


def delete_notification(notification_id: int) -> bool:
    """Delete a single notification.

    Args:
        notification_id: The notification ID to delete.

    Returns:
        True if the notification was deleted, False if not found.
    """
    session = get_db_session()
    try:
        notification = (
            session.query(WorkspaceNotification)
            .filter(WorkspaceNotification.id == notification_id)
            .first()
        )
        if not notification:
            return False
        session.delete(notification)
        session.commit()
        logger.info("Deleted notification %d", notification_id)
        return True
    finally:
        session.close()


def clear_notifications(conversation_id: Optional[int] = None) -> int:
    """Clear (delete) all notifications, optionally filtered by conversation.

    Args:
        conversation_id: If provided, only clear notifications for this conversation.
            If None, clears all notifications.

    Returns:
        The number of notifications deleted.
    """
    session = get_db_session()
    try:
        query = session.query(WorkspaceNotification)
        if conversation_id is not None:
            query = query.filter(WorkspaceNotification.conversation_id == conversation_id)

        count = query.delete(synchronize_session="fetch")
        session.commit()
        logger.info("Cleared %d notifications (conversation_id=%s)", count, conversation_id)
        return count
    finally:
        session.close()


def mark_notification_read(notification_id: int) -> Optional[dict]:
    """Mark a single notification as read.

    Args:
        notification_id: The notification ID to mark as read.

    Returns:
        The updated notification dict, or None if not found.
    """
    session = get_db_session()
    try:
        notification = (
            session.query(WorkspaceNotification)
            .filter(WorkspaceNotification.id == notification_id)
            .first()
        )
        if not notification:
            return None
        notification.is_read = True
        notification.updated_at = _utc_now()
        session.commit()
        session.refresh(notification)
        return _notification_to_dict(notification)
    finally:
        session.close()


def mark_all_notifications_read(conversation_id: Optional[int] = None) -> int:
    """Mark all notifications as read, optionally filtered by conversation.

    Args:
        conversation_id: If provided, only mark notifications for this conversation.
            If None, marks all notifications as read.

    Returns:
        The number of notifications updated.
    """
    session = get_db_session()
    try:
        query = session.query(WorkspaceNotification).filter(
            WorkspaceNotification.is_read == False  # noqa: E712
        )
        if conversation_id is not None:
            query = query.filter(WorkspaceNotification.conversation_id == conversation_id)

        count = query.update(
            {"is_read": True, "updated_at": _utc_now()},
            synchronize_session="fetch",
        )
        session.commit()
        logger.info(
            "Marked %d notifications as read (conversation_id=%s)", count, conversation_id
        )
        return count
    finally:
        session.close()


# ============================================================================
# Token Processing Log
# ============================================================================

def add_token_log_entry(
    conversation_id: int,
    event_type: str,
    turn_number: int = 0,
    tool_name: str | None = None,
    tool_input_length: int | None = None,
    tool_result_length: int | None = None,
    tool_is_error: bool | None = None,
    text_length: int | None = None,
    num_tool_calls: int | None = None,
    estimated_tokens: int = 0,
    api_input_tokens: int | None = None,
    api_output_tokens: int | None = None,
    api_cache_creation_tokens: int | None = None,
    api_cache_read_tokens: int | None = None,
    api_total_cost_usd: float | None = None,
    api_num_turns: int | None = None,
    api_duration_ms: int | None = None,
    api_duration_api_ms: int | None = None,
    model: str | None = None,
) -> dict:
    """Add a token log entry for a conversation turn or event."""
    session = get_db_session()
    try:
        entry = WorkspaceTokenLog(
            conversation_id=conversation_id,
            event_type=event_type,
            turn_number=turn_number,
            tool_name=tool_name,
            tool_input_length=tool_input_length,
            tool_result_length=tool_result_length,
            tool_is_error=1 if tool_is_error else (0 if tool_is_error is not None else None),
            text_length=text_length,
            num_tool_calls=num_tool_calls,
            estimated_tokens=estimated_tokens,
            api_input_tokens=api_input_tokens,
            api_output_tokens=api_output_tokens,
            api_cache_creation_tokens=api_cache_creation_tokens,
            api_cache_read_tokens=api_cache_read_tokens,
            api_total_cost_usd=api_total_cost_usd,
            api_num_turns=api_num_turns,
            api_duration_ms=api_duration_ms,
            api_duration_api_ms=api_duration_api_ms,
            model=model,
        )
        session.add(entry)
        session.commit()
        return _token_log_to_dict(entry)
    finally:
        session.close()


def get_token_log(conversation_id: int) -> list[dict]:
    """Get all token log entries for a conversation, ordered by timestamp."""
    session = get_db_session()
    try:
        entries = (
            session.query(WorkspaceTokenLog)
            .filter(WorkspaceTokenLog.conversation_id == conversation_id)
            .order_by(WorkspaceTokenLog.id.asc())
            .all()
        )
        return [_token_log_to_dict(e) for e in entries]
    finally:
        session.close()


def get_token_log_summary(conversation_id: int) -> dict:
    """Get a summary of token usage for a conversation.

    Returns a shape matching the frontend ``TokenLogSummary`` interface:
    total counts, cumulative API token breakdowns, per-tool breakdowns,
    and the full list of log entries.

    **Important distinction for cache tokens:**

    - ``total_api_input_tokens`` / ``total_api_output_tokens``: These are
      summed across all turns and represent total billing-relevant counts
      (each turn adds NEW input/output tokens that are billed).
    - ``total_api_cache_read_tokens`` / ``total_api_cache_creation_tokens``:
      These are summed across turns for billing-relevant totals.  However,
      individual turn cache numbers overlap (turn 5's cache_read includes
      content already counted in turn 4's cache_read) so the sum represents
      "total cache-served token reads across all API calls", NOT the current
      cache size.
    - ``current_context_tokens``: The actual context window utilization from
      the most recent API call (input + cache_read + cache_creation).  This
      is what should drive the context-window meter in the UI.
    """
    session = get_db_session()
    try:
        entries = (
            session.query(WorkspaceTokenLog)
            .filter(WorkspaceTokenLog.conversation_id == conversation_id)
            .order_by(WorkspaceTokenLog.id.asc())
            .all()
        )
        if not entries:
            return {
                "total_entries": 0,
                "total_estimated_tokens": 0,
                "total_api_input_tokens": 0,
                "total_api_output_tokens": 0,
                "total_api_cache_creation_tokens": 0,
                "total_api_cache_read_tokens": 0,
                "current_context_tokens": 0,
                "total_cost_usd": 0.0,
                "per_tool_breakdown": [],
                "entries": [],
            }

        total_est = sum(e.estimated_tokens for e in entries)

        # Cumulative API totals from result_summary entries (billing-relevant sums)
        summaries = [e for e in entries if e.event_type == "result_summary"]
        total_api_input = sum(s.api_input_tokens or 0 for s in summaries)
        total_api_output = sum(s.api_output_tokens or 0 for s in summaries)
        total_api_cache_creation = sum(s.api_cache_creation_tokens or 0 for s in summaries)
        total_api_cache_read = sum(s.api_cache_read_tokens or 0 for s in summaries)
        total_cost = sum(s.api_total_cost_usd or 0.0 for s in summaries)

        # Current context window utilization from the LATEST result_summary.
        # This is the real number that tells you how much of the context
        # window is occupied right now: input + cache_read + cache_creation.
        current_context_tokens = 0
        latest_cache_read = 0
        latest_cache_create = 0
        latest_input = 0
        latest_output = 0
        if summaries:
            latest = summaries[-1]
            latest_input = latest.api_input_tokens or 0
            latest_output = latest.api_output_tokens or 0
            latest_cache_read = latest.api_cache_read_tokens or 0
            latest_cache_create = latest.api_cache_creation_tokens or 0
            current_context_tokens = latest_input + latest_cache_read + latest_cache_create

        # Per-tool breakdown matching frontend TokenLogToolBreakdown
        tool_usage: dict[str, dict[str, int]] = {}
        for e in entries:
            if e.event_type == "tool_call" and e.tool_name:
                if e.tool_name not in tool_usage:
                    tool_usage[e.tool_name] = {
                        "call_count": 0,
                        "total_input_chars": 0,
                        "total_result_chars": 0,
                        "error_count": 0,
                    }
                tool_usage[e.tool_name]["call_count"] += 1
                tool_usage[e.tool_name]["total_input_chars"] += e.tool_input_length or 0
            elif e.event_type == "tool_result" and e.tool_name:
                if e.tool_name not in tool_usage:
                    tool_usage[e.tool_name] = {
                        "call_count": 0,
                        "total_input_chars": 0,
                        "total_result_chars": 0,
                        "error_count": 0,
                    }
                tool_usage[e.tool_name]["total_result_chars"] += e.tool_result_length or 0
                if e.tool_is_error:
                    tool_usage[e.tool_name]["error_count"] += 1

        per_tool_breakdown = [
            {
                "tool_name": name,
                "call_count": stats["call_count"],
                # Estimate tokens from character counts (roughly 1 token per 4 chars)
                "total_input_tokens": stats["total_input_chars"] // 4,
                "total_result_tokens": stats["total_result_chars"] // 4,
                "total_estimated_tokens": (stats["total_input_chars"] + stats["total_result_chars"]) // 4,
                "error_count": stats["error_count"],
            }
            for name, stats in sorted(
                tool_usage.items(),
                key=lambda x: x[1]["total_result_chars"],
                reverse=True,
            )
        ]

        # Serialize all entries for the frontend
        serialized_entries = [_token_log_to_dict(e) for e in entries]

        return {
            "total_entries": len(entries),
            "total_estimated_tokens": total_est,
            # Cumulative billing-relevant totals (sum across all turns)
            "total_api_input_tokens": total_api_input,
            "total_api_output_tokens": total_api_output,
            "total_api_cache_creation_tokens": total_api_cache_creation,
            "total_api_cache_read_tokens": total_api_cache_read,
            "total_cost_usd": round(total_cost, 6),
            # Current context window utilization (from LATEST turn only)
            "current_context_tokens": current_context_tokens,
            "latest_input_tokens": latest_input,
            "latest_output_tokens": latest_output,
            "latest_cache_read_tokens": latest_cache_read,
            "latest_cache_creation_tokens": latest_cache_create,
            "per_tool_breakdown": per_tool_breakdown,
            "entries": serialized_entries,
        }
    finally:
        session.close()


def clear_token_log(conversation_id: int) -> int:
    """Delete all token log entries for a conversation."""
    session = get_db_session()
    try:
        count = (
            session.query(WorkspaceTokenLog)
            .filter(WorkspaceTokenLog.conversation_id == conversation_id)
            .delete()
        )
        session.commit()
        return count
    finally:
        session.close()


def _token_log_to_dict(entry: WorkspaceTokenLog) -> dict:
    """Convert a WorkspaceTokenLog to a dictionary."""
    return {
        "id": entry.id,
        "conversation_id": entry.conversation_id,
        "event_type": entry.event_type,
        "turn_number": entry.turn_number,
        "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
        "tool_name": entry.tool_name,
        "tool_input_length": entry.tool_input_length,
        "tool_result_length": entry.tool_result_length,
        "tool_is_error": bool(entry.tool_is_error) if entry.tool_is_error is not None else None,
        "text_length": entry.text_length,
        "num_tool_calls": entry.num_tool_calls,
        "estimated_tokens": entry.estimated_tokens,
        "api_input_tokens": entry.api_input_tokens,
        "api_output_tokens": entry.api_output_tokens,
        "api_cache_creation_tokens": entry.api_cache_creation_tokens,
        "api_cache_read_tokens": entry.api_cache_read_tokens,
        "api_total_cost_usd": entry.api_total_cost_usd,
        "api_num_turns": entry.api_num_turns,
        "api_duration_ms": entry.api_duration_ms,
        "api_duration_api_ms": entry.api_duration_api_ms,
        "model": entry.model,
    }


# ============================================================================
# Role Library Operations
# ============================================================================


def _blueprint_to_dict(bp: RoleBlueprint) -> dict:
    """Convert a RoleBlueprint to a JSON-serializable dictionary."""
    target_files = []
    if bp.target_files:
        try:
            target_files = json.loads(bp.target_files)
        except (json.JSONDecodeError, TypeError):
            target_files = []
    return {
        "id": bp.id,
        "name": bp.name,
        "role_tag": bp.role_tag,
        "category": bp.category,
        "subcategory": bp.subcategory,
        "one_liner": bp.one_liner,
        "prd_content": bp.prd_content,
        "target_files": target_files,
        "status": bp.status,
        "created_at": bp.created_at.isoformat() if bp.created_at else None,
        "updated_at": bp.updated_at.isoformat() if bp.updated_at else None,
    }


def list_blueprints(category: Optional[str] = None) -> list[dict]:
    """List all role blueprints, optionally filtered by category."""
    session = get_db_session()
    try:
        query = session.query(RoleBlueprint)
        if category:
            query = query.filter(RoleBlueprint.category == category)
        entries = query.order_by(RoleBlueprint.category, RoleBlueprint.name).all()
        return [_blueprint_to_dict(e) for e in entries]
    finally:
        session.close()


def get_blueprint(blueprint_id: int) -> Optional[dict]:
    """Get a single blueprint by ID."""
    session = get_db_session()
    try:
        bp = session.query(RoleBlueprint).filter(RoleBlueprint.id == blueprint_id).first()
        return _blueprint_to_dict(bp) if bp else None
    finally:
        session.close()


def get_blueprint_by_tag(role_tag: str) -> Optional[dict]:
    """Get a single blueprint by its unique role_tag."""
    session = get_db_session()
    try:
        bp = session.query(RoleBlueprint).filter(RoleBlueprint.role_tag == role_tag).first()
        return _blueprint_to_dict(bp) if bp else None
    finally:
        session.close()


def create_blueprint(
    name: str,
    role_tag: str,
    category: str,
    one_liner: str,
    prd_content: str = "",
    subcategory: Optional[str] = None,
    target_files: Optional[list[str]] = None,
    status: str = "draft",
) -> dict:
    """Create a new role blueprint."""
    session = get_db_session()
    try:
        bp = RoleBlueprint(
            name=name,
            role_tag=role_tag,
            category=category,
            subcategory=subcategory,
            one_liner=one_liner,
            prd_content=prd_content,
            target_files=json.dumps(target_files) if target_files else None,
            status=status,
        )
        session.add(bp)
        session.commit()
        session.refresh(bp)
        return _blueprint_to_dict(bp)
    finally:
        session.close()


def update_blueprint(blueprint_id: int, **kwargs) -> Optional[dict]:  # type: ignore[no-untyped-def]
    """Update a blueprint. Only provided kwargs are updated."""
    session = get_db_session()
    try:
        bp = session.query(RoleBlueprint).filter(RoleBlueprint.id == blueprint_id).first()
        if not bp:
            return None
        for key, value in kwargs.items():
            if key == "target_files" and isinstance(value, list):
                setattr(bp, key, json.dumps(value))
            elif hasattr(bp, key):
                setattr(bp, key, value)
        bp.updated_at = _utc_now()
        session.commit()
        session.refresh(bp)
        return _blueprint_to_dict(bp)
    finally:
        session.close()


def delete_blueprint(blueprint_id: int) -> bool:
    """Delete a role blueprint by ID."""
    session = get_db_session()
    try:
        bp = session.query(RoleBlueprint).filter(RoleBlueprint.id == blueprint_id).first()
        if not bp:
            return False
        session.delete(bp)
        session.commit()
        return True
    finally:
        session.close()


def list_blueprint_categories() -> list[dict]:
    """Return distinct categories with counts."""
    session = get_db_session()
    try:
        rows = (
            session.query(RoleBlueprint.category, func.count(RoleBlueprint.id))
            .group_by(RoleBlueprint.category)
            .order_by(RoleBlueprint.category)
            .all()
        )
        return [{"category": cat, "count": cnt} for cat, cnt in rows]
    finally:
        session.close()


# ============================================================================
# Background Session Event Operations
# ============================================================================


def persist_session_events_batch(events: list[dict]) -> int:
    """Persist a batch of session events to the database.

    Each dict in ``events`` must contain: session_id, conversation_id,
    sequence, event_type, event_data (JSON string).

    Args:
        events: List of event dicts to persist.

    Returns:
        Number of events persisted.
    """
    if not events:
        return 0

    session = get_db_session()
    try:
        for evt in events:
            row = WorkspaceSessionEvent(
                session_id=evt["session_id"],
                conversation_id=evt["conversation_id"],
                sequence=evt["sequence"],
                event_type=evt["event_type"],
                event_data=evt["event_data"],
            )
            session.add(row)
        session.commit()
        return len(events)
    except Exception:
        session.rollback()
        logger.exception("Failed to persist %d session events", len(events))
        raise
    finally:
        session.close()


def get_session_events_since(session_id: str, since_sequence: int, limit: int = 2000) -> list[dict]:
    """Retrieve session events after a given sequence number.

    Used for catch-up replay when a viewer reconnects to a running
    or completed session.

    Args:
        session_id: The background session ID.
        since_sequence: Return events with sequence > this value.
            Use 0 to get all events from the beginning.
        limit: Maximum number of events to return (default 2000).

    Returns:
        List of event dicts ordered by sequence number, each containing:
        sequence, event_type, event_data, created_at.
    """
    session = get_db_session()
    try:
        rows = (
            session.query(WorkspaceSessionEvent)
            .filter(
                WorkspaceSessionEvent.session_id == session_id,
                WorkspaceSessionEvent.sequence > since_sequence,
            )
            .order_by(WorkspaceSessionEvent.sequence)
            .limit(limit)
            .all()
        )
        return [
            {
                "sequence": row.sequence,
                "event_type": row.event_type,
                "event_data": row.event_data,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]
    finally:
        session.close()


def delete_session_events(session_id: str) -> int:
    """Delete all persisted events for a background session.

    Args:
        session_id: The background session ID whose events to delete.

    Returns:
        Number of events deleted.
    """
    session = get_db_session()
    try:
        count = (
            session.query(WorkspaceSessionEvent)
            .filter(WorkspaceSessionEvent.session_id == session_id)
            .delete(synchronize_session=False)
        )
        session.commit()
        logger.info("Deleted %d session events for session %s", count, session_id)
        return count
    except Exception:
        session.rollback()
        logger.exception("Failed to delete session events for %s", session_id)
        raise
    finally:
        session.close()
