"""
Workspace Database
==================

SQLAlchemy models and CRUD functions for persisting workspace conversations.
Uses a global database at ``~/.autoforge/workspace.db`` (not per-project).
"""

import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, create_engine, func
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
    token_count = Column(Integer, nullable=False, default=0)
    summary = Column(Text, nullable=True)
    summary_updated_at = Column(DateTime, nullable=True)
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

            # Schema migration: add Phase 2 columns if missing
            import sqlite3
            conn = sqlite3.connect(db_path.as_posix())
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
) -> WorkspaceConversation:
    """Create a new workspace conversation.

    Args:
        title: Optional conversation title. If not provided, it will be
            auto-generated from the first user message.
        category: Conversation category (default: "general").
        working_directory: Optional working directory path for the conversation.

    Returns:
        The newly created WorkspaceConversation instance.
    """
    session = get_db_session()
    try:
        conversation = WorkspaceConversation(
            title=title,
            category=category,
            working_directory=working_directory,
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
                for m in sorted(conversation.messages, key=lambda x: x.timestamp or datetime.min.replace(tzinfo=timezone.utc))
            ],
        }
    finally:
        session.close()


def delete_conversation(conversation_id: int) -> bool:
    """Delete a conversation and all its messages.

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
        session.delete(conversation)
        session.commit()
        logger.info("Deleted workspace conversation %d", conversation_id)
        return True
    finally:
        session.close()


def update_conversation(
    conversation_id: int,
    title: Optional[str] = None,
    category: Optional[str] = None,
    working_directory: Optional[str] = None,
    pinned: Optional[bool] = None,
) -> Optional[dict]:
    """Update a conversation's metadata.

    Only the fields that are provided (not None) will be updated.

    Args:
        conversation_id: The conversation ID to update.
        title: New title, or None to leave unchanged.
        category: New category, or None to leave unchanged.
        working_directory: New working directory, or None to leave unchanged.
        pinned: New pinned state, or None to leave unchanged.

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
