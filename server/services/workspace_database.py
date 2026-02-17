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
) -> Optional[dict]:
    """Update a conversation's metadata.

    Only the fields that are provided (not None) will be updated.

    Args:
        conversation_id: The conversation ID to update.
        title: New title, or None to leave unchanged.
        category: New category, or None to leave unchanged.
        working_directory: New working directory, or None to leave unchanged.

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
