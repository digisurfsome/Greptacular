"""
Workspace Library Service
=========================

Manages file uploads, storage, and context injection for the workspace.
Files can be global (available to all conversations) or per-chat.
"""

import logging
import uuid
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Disk storage root
LIBRARY_DIR = Path.home() / ".autoforge" / "workspace" / "library"

# Max file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024

# Content cache threshold: files <= 100KB get content stored in SQLite
CONTENT_CACHE_THRESHOLD = 100 * 1024

# Allowed file extensions (text-based files only for context injection)
ALLOWED_EXTENSIONS = {
    ".md", ".txt", ".py", ".js", ".ts", ".tsx", ".jsx",
    ".json", ".yaml", ".yml", ".xml", ".html", ".css",
    ".scss", ".less", ".sql", ".sh", ".bash", ".zsh",
    ".env", ".toml", ".ini", ".cfg", ".conf", ".csv",
    ".rs", ".go", ".java", ".kt", ".swift", ".c", ".cpp",
    ".h", ".hpp", ".rb", ".php", ".r", ".lua", ".zig",
    ".dockerfile", ".gitignore", ".editorconfig",
}

# File type classification based on extension
EXTENSION_TO_TYPE: dict[str, str] = {
    ".md": "doc",
    ".txt": "doc",
    ".py": "code",
    ".js": "code",
    ".ts": "code",
    ".tsx": "code",
    ".jsx": "code",
    ".json": "spec",
    ".yaml": "spec",
    ".yml": "spec",
    ".xml": "spec",
    ".html": "code",
    ".css": "code",
    ".sql": "code",
    ".sh": "code",
}


def ensure_library_dir() -> Path:
    """Create library directory if it doesn't exist. Return the path."""
    LIBRARY_DIR.mkdir(parents=True, exist_ok=True)
    return LIBRARY_DIR


def detect_file_type(filename: str) -> str:
    """Classify file type from extension. Returns 'doc', 'code', 'spec', or 'upload'."""
    ext = Path(filename).suffix.lower()
    return EXTENSION_TO_TYPE.get(ext, "upload")


def validate_file_extension(filename: str) -> bool:
    """Check if the file extension is in the allowed set."""
    ext = Path(filename).suffix.lower()
    # Allow extensionless files (like Dockerfile, Makefile)
    if not ext:
        return True
    return ext in ALLOWED_EXTENSIONS


def save_file_to_disk(filename: str, content: bytes) -> tuple[str, str]:
    """
    Save file content to disk with a UUID prefix for uniqueness.

    Returns:
        Tuple of (disk_path, display_name)
    """
    ensure_library_dir()
    safe_name = f"{uuid.uuid4().hex[:12]}_{filename}"
    disk_path = LIBRARY_DIR / safe_name
    disk_path.write_bytes(content)
    return str(disk_path), filename


def _file_to_dict(file_obj) -> dict:
    """Convert a WorkspaceLibraryFile ORM object to a dict."""
    return {
        "id": file_obj.id,
        "conversation_id": file_obj.conversation_id,
        "filename": file_obj.filename,
        "display_name": file_obj.display_name or file_obj.filename,
        "file_type": file_obj.file_type,
        "file_size": file_obj.file_size,
        "tags": file_obj.tags,
        "active_in_context": bool(file_obj.active_in_context),
        "created_at": file_obj.created_at.isoformat() if file_obj.created_at else None,
    }


def upload_file(
    filename: str,
    content: bytes,
    conversation_id: Optional[int] = None,
    display_name: Optional[str] = None,
    tags: Optional[str] = None,
) -> dict:
    """
    Upload a file to the library.

    - If content <= 100KB: store in SQLite content column
    - If content > 100KB: store on disk, set file_path in DB
    """
    from .workspace_database import WorkspaceLibraryFile, get_db_session

    file_type = detect_file_type(filename)
    file_size = len(content)

    # Determine storage strategy
    content_text = None
    file_path = None
    if file_size <= CONTENT_CACHE_THRESHOLD:
        try:
            content_text = content.decode("utf-8")
        except UnicodeDecodeError:
            file_path_str, _ = save_file_to_disk(filename, content)
            file_path = file_path_str
    else:
        file_path_str, _ = save_file_to_disk(filename, content)
        file_path = file_path_str

    session = get_db_session()
    try:
        lib_file = WorkspaceLibraryFile(
            conversation_id=conversation_id,
            filename=filename,
            display_name=display_name or filename,
            file_type=file_type,
            content=content_text,
            file_path=file_path,
            file_size=file_size,
            tags=tags,
            active_in_context=False,
        )
        session.add(lib_file)
        session.commit()
        session.refresh(lib_file)
        logger.info("Uploaded library file %d: %s (%d bytes)", lib_file.id, filename, file_size)
        return _file_to_dict(lib_file)
    finally:
        session.close()


def upload_text(
    filename: str,
    text_content: str,
    conversation_id: Optional[int] = None,
    display_name: Optional[str] = None,
    tags: Optional[str] = None,
) -> dict:
    """Upload text content directly (for paste operations)."""
    content_bytes = text_content.encode("utf-8")
    return upload_file(filename, content_bytes, conversation_id, display_name, tags)


def get_file_content(file_id: int) -> Optional[str]:
    """
    Get file content by ID.

    If content is cached in DB, return it directly.
    If stored on disk (file_path set), read from disk.
    """
    from .workspace_database import WorkspaceLibraryFile, get_db_session

    session = get_db_session()
    try:
        lib_file = (
            session.query(WorkspaceLibraryFile)
            .filter(WorkspaceLibraryFile.id == file_id)
            .first()
        )
        if not lib_file:
            return None

        if lib_file.content is not None:
            return lib_file.content

        if lib_file.file_path:
            disk_path = Path(lib_file.file_path)
            if disk_path.exists():
                try:
                    return disk_path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    return None

        return None
    finally:
        session.close()


def delete_file(file_id: int) -> bool:
    """Delete a file from DB and disk (if stored on disk)."""
    from .workspace_database import WorkspaceLibraryFile, get_db_session

    session = get_db_session()
    try:
        lib_file = (
            session.query(WorkspaceLibraryFile)
            .filter(WorkspaceLibraryFile.id == file_id)
            .first()
        )
        if not lib_file:
            return False

        if lib_file.file_path:
            disk_path = Path(lib_file.file_path)
            if disk_path.exists():
                try:
                    disk_path.unlink()
                except OSError as e:
                    logger.warning("Failed to delete file from disk: %s", e)

        session.delete(lib_file)
        session.commit()
        logger.info("Deleted library file %d", file_id)
        return True
    finally:
        session.close()


def list_global_files() -> list[dict]:
    """List all files where conversation_id IS NULL (global scope)."""
    from .workspace_database import WorkspaceLibraryFile, get_db_session

    session = get_db_session()
    try:
        files = (
            session.query(WorkspaceLibraryFile)
            .filter(WorkspaceLibraryFile.conversation_id.is_(None))
            .order_by(WorkspaceLibraryFile.created_at.desc())
            .all()
        )
        return [_file_to_dict(f) for f in files]
    finally:
        session.close()


def list_conversation_files(conversation_id: int) -> list[dict]:
    """List files for a conversation: global files + per-chat files."""
    from .workspace_database import (
        WorkspaceFileActivation,
        WorkspaceLibraryFile,
        get_db_session,
    )

    session = get_db_session()
    try:
        # Get global files with activation status for this conversation
        global_files = (
            session.query(WorkspaceLibraryFile)
            .filter(WorkspaceLibraryFile.conversation_id.is_(None))
            .order_by(WorkspaceLibraryFile.created_at.desc())
            .all()
        )

        result = []
        for f in global_files:
            d = _file_to_dict(f)
            activation = (
                session.query(WorkspaceFileActivation)
                .filter(
                    WorkspaceFileActivation.file_id == f.id,
                    WorkspaceFileActivation.conversation_id == conversation_id,
                )
                .first()
            )
            d["active_in_context"] = bool(activation.active) if activation else False
            result.append(d)

        # Get per-chat files for this conversation
        chat_files = (
            session.query(WorkspaceLibraryFile)
            .filter(WorkspaceLibraryFile.conversation_id == conversation_id)
            .order_by(WorkspaceLibraryFile.created_at.desc())
            .all()
        )
        result.extend([_file_to_dict(f) for f in chat_files])

        return result
    finally:
        session.close()


def toggle_file_in_context(file_id: int, conversation_id: int) -> Optional[dict]:
    """
    Toggle a file's active_in_context status for a conversation.

    For global files: creates/updates a per-conversation activation record.
    For per-chat files: toggles the active_in_context column directly.
    """
    from .workspace_database import (
        WorkspaceFileActivation,
        WorkspaceLibraryFile,
        get_db_session,
    )

    session = get_db_session()
    try:
        lib_file = (
            session.query(WorkspaceLibraryFile)
            .filter(WorkspaceLibraryFile.id == file_id)
            .first()
        )
        if not lib_file:
            return None

        if lib_file.conversation_id is None:
            # Global file -- use activation table
            activation = (
                session.query(WorkspaceFileActivation)
                .filter(
                    WorkspaceFileActivation.file_id == file_id,
                    WorkspaceFileActivation.conversation_id == conversation_id,
                )
                .first()
            )
            if activation:
                activation.active = not activation.active
                new_active = activation.active
            else:
                activation = WorkspaceFileActivation(
                    file_id=file_id,
                    conversation_id=conversation_id,
                    active=True,
                )
                session.add(activation)
                new_active = True
            session.commit()
            d = _file_to_dict(lib_file)
            d["active_in_context"] = bool(new_active)
            return d
        else:
            # Per-chat file -- toggle directly
            lib_file.active_in_context = not lib_file.active_in_context
            session.commit()
            session.refresh(lib_file)
            return _file_to_dict(lib_file)
    finally:
        session.close()


def get_active_files(conversation_id: int) -> list[dict]:
    """Get all files that are currently active in a conversation's context."""
    from .workspace_database import (
        WorkspaceFileActivation,
        WorkspaceLibraryFile,
        get_db_session,
    )

    session = get_db_session()
    try:
        result = []

        # Active global files (via activation table)
        activations = (
            session.query(WorkspaceFileActivation)
            .filter(
                WorkspaceFileActivation.conversation_id == conversation_id,
                WorkspaceFileActivation.active.is_(True),
            )
            .all()
        )
        for act in activations:
            lib_file = (
                session.query(WorkspaceLibraryFile)
                .filter(WorkspaceLibraryFile.id == act.file_id)
                .first()
            )
            if lib_file and lib_file.conversation_id is None:
                d = _file_to_dict(lib_file)
                d["active_in_context"] = True
                result.append(d)

        # Active per-chat files
        chat_files = (
            session.query(WorkspaceLibraryFile)
            .filter(
                WorkspaceLibraryFile.conversation_id == conversation_id,
                WorkspaceLibraryFile.active_in_context.is_(True),
            )
            .all()
        )
        result.extend([_file_to_dict(f) for f in chat_files])

        return result
    finally:
        session.close()


def update_file_metadata(
    file_id: int,
    display_name: Optional[str] = None,
    tags: Optional[str] = None,
) -> Optional[dict]:
    """Update display_name and/or tags for a file."""
    from .workspace_database import WorkspaceLibraryFile, get_db_session

    session = get_db_session()
    try:
        lib_file = (
            session.query(WorkspaceLibraryFile)
            .filter(WorkspaceLibraryFile.id == file_id)
            .first()
        )
        if not lib_file:
            return None

        if display_name is not None:
            lib_file.display_name = display_name
        if tags is not None:
            lib_file.tags = tags

        session.commit()
        session.refresh(lib_file)
        return _file_to_dict(lib_file)
    finally:
        session.close()


def get_active_files_context(conversation_id: int, token_cap: int = 50_000) -> tuple[str, int]:
    """
    Build the context string for all active files in a conversation.

    Enforces a token cap to prevent library files from inflating every
    message's input cost (each token is billed on every subsequent turn).

    Args:
        conversation_id: The conversation ID.
        token_cap: Maximum tokens for library injection (default 50K).

    Returns:
        Tuple of (context_string, estimated_token_count)
    """
    LIBRARY_TOKEN_CAP = token_cap

    active_files = get_active_files(conversation_id)
    if not active_files:
        return "", 0

    parts = []
    total_tokens = 0
    for f in active_files:
        content = get_file_content(f["id"])
        if content:
            block = (
                f"--- Library File: {f['display_name']} ({f['file_type']}) ---\n"
                f"{content}\n"
                f"--- End File ---"
            )
            block_tokens = len(block) // 4
            if total_tokens + block_tokens > LIBRARY_TOKEN_CAP:
                logger.warning(
                    "Library injection capped at ~%d tokens. Skipping '%s' (%d tokens).",
                    total_tokens, f['display_name'], block_tokens,
                )
                break
            parts.append(block)
            total_tokens += block_tokens

    return "\n\n".join(parts), total_tokens
