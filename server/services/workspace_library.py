"""
Workspace Library Service
=========================

Manages file uploads, storage, folder organization, and per-message context
attachment for the workspace. Files live in a nested folder filesystem
(Google Drive-style) and are explicitly attached to individual chat messages
rather than auto-injected into every session.
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


# ============================================================================
# Serialization Helpers
# ============================================================================

def _file_to_dict(file_obj) -> dict:
    """Convert a WorkspaceLibraryFile ORM object to a dict."""
    return {
        "id": file_obj.id,
        "conversation_id": file_obj.conversation_id,
        "folder_id": file_obj.folder_id,
        "filename": file_obj.filename,
        "display_name": file_obj.display_name or file_obj.filename,
        "file_type": file_obj.file_type,
        "file_size": file_obj.file_size,
        "tags": file_obj.tags,
        "active_in_context": bool(file_obj.active_in_context),
        "created_at": file_obj.created_at.isoformat() if file_obj.created_at else None,
    }


def _folder_to_dict(folder_obj) -> dict:
    """Convert a WorkspaceLibraryFolder ORM object to a dict."""
    return {
        "id": folder_obj.id,
        "name": folder_obj.name,
        "parent_id": folder_obj.parent_id,
        "created_at": folder_obj.created_at.isoformat() if folder_obj.created_at else None,
        "updated_at": folder_obj.updated_at.isoformat() if folder_obj.updated_at else None,
    }


# ============================================================================
# Folder CRUD
# ============================================================================

def create_folder(name: str, parent_id: Optional[int] = None) -> dict:
    """Create a new folder. parent_id=None means root level."""
    from .workspace_database import WorkspaceLibraryFolder, get_db_session

    session = get_db_session()
    try:
        # Validate parent exists if specified
        if parent_id is not None:
            parent = (
                session.query(WorkspaceLibraryFolder)
                .filter(WorkspaceLibraryFolder.id == parent_id)
                .first()
            )
            if not parent:
                raise ValueError(f"Parent folder {parent_id} not found")

        folder = WorkspaceLibraryFolder(name=name, parent_id=parent_id)
        session.add(folder)
        session.commit()
        session.refresh(folder)
        logger.info("Created folder %d: '%s' (parent=%s)", folder.id, name, parent_id)
        return _folder_to_dict(folder)
    finally:
        session.close()


def rename_folder(folder_id: int, name: str) -> Optional[dict]:
    """Rename a folder."""
    from .workspace_database import WorkspaceLibraryFolder, get_db_session

    session = get_db_session()
    try:
        folder = (
            session.query(WorkspaceLibraryFolder)
            .filter(WorkspaceLibraryFolder.id == folder_id)
            .first()
        )
        if not folder:
            return None
        folder.name = name
        session.commit()
        session.refresh(folder)
        return _folder_to_dict(folder)
    finally:
        session.close()


def move_folder(folder_id: int, new_parent_id: Optional[int]) -> Optional[dict]:
    """Move a folder to a new parent. Prevents cycles."""
    from .workspace_database import WorkspaceLibraryFolder, get_db_session

    session = get_db_session()
    try:
        folder = (
            session.query(WorkspaceLibraryFolder)
            .filter(WorkspaceLibraryFolder.id == folder_id)
            .first()
        )
        if not folder:
            return None

        # Can't move a folder into itself
        if new_parent_id == folder_id:
            raise ValueError("Cannot move a folder into itself")

        # Cycle detection: walk up from new_parent_id to root, ensure we don't hit folder_id
        if new_parent_id is not None:
            parent = (
                session.query(WorkspaceLibraryFolder)
                .filter(WorkspaceLibraryFolder.id == new_parent_id)
                .first()
            )
            if not parent:
                raise ValueError(f"Target parent folder {new_parent_id} not found")

            current_id = new_parent_id
            visited = set()
            while current_id is not None:
                if current_id == folder_id:
                    raise ValueError("Cannot move a folder into one of its descendants")
                if current_id in visited:
                    break  # safety: break infinite loop
                visited.add(current_id)
                ancestor = (
                    session.query(WorkspaceLibraryFolder)
                    .filter(WorkspaceLibraryFolder.id == current_id)
                    .first()
                )
                current_id = ancestor.parent_id if ancestor else None

        folder.parent_id = new_parent_id
        session.commit()
        session.refresh(folder)
        return _folder_to_dict(folder)
    finally:
        session.close()


def delete_folder(folder_id: int) -> bool:
    """Delete a folder. Files inside move to root (folder_id=NULL). Subfolders cascade-delete."""
    from .workspace_database import WorkspaceLibraryFile, WorkspaceLibraryFolder, get_db_session

    session = get_db_session()
    try:
        folder = (
            session.query(WorkspaceLibraryFolder)
            .filter(WorkspaceLibraryFolder.id == folder_id)
            .first()
        )
        if not folder:
            return False

        # Move files in this folder (and all descendant folders) to root
        descendant_ids = _get_descendant_folder_ids(session, folder_id)
        all_folder_ids = [folder_id] + descendant_ids

        session.query(WorkspaceLibraryFile).filter(
            WorkspaceLibraryFile.folder_id.in_(all_folder_ids)
        ).update({WorkspaceLibraryFile.folder_id: None}, synchronize_session="fetch")

        # Delete the folder (subfolders cascade via FK)
        session.delete(folder)
        session.commit()
        logger.info("Deleted folder %d", folder_id)
        return True
    finally:
        session.close()


def _get_descendant_folder_ids(session, folder_id: int) -> list[int]:
    """Get all descendant folder IDs recursively (BFS)."""
    from .workspace_database import WorkspaceLibraryFolder

    result = []
    queue = [folder_id]
    while queue:
        current = queue.pop(0)
        children = (
            session.query(WorkspaceLibraryFolder.id)
            .filter(WorkspaceLibraryFolder.parent_id == current)
            .all()
        )
        for (child_id,) in children:
            result.append(child_id)
            queue.append(child_id)
    return result


def list_folder_contents(folder_id: Optional[int] = None) -> dict:
    """
    List files and subfolders in a folder. folder_id=None means root.

    Returns: {"folders": [...], "files": [...]}
    """
    from .workspace_database import WorkspaceLibraryFile, WorkspaceLibraryFolder, get_db_session

    session = get_db_session()
    try:
        if folder_id is None:
            folders = (
                session.query(WorkspaceLibraryFolder)
                .filter(WorkspaceLibraryFolder.parent_id.is_(None))
                .order_by(WorkspaceLibraryFolder.name)
                .all()
            )
            files = (
                session.query(WorkspaceLibraryFile)
                .filter(WorkspaceLibraryFile.folder_id.is_(None))
                .order_by(WorkspaceLibraryFile.created_at.desc())
                .all()
            )
        else:
            folders = (
                session.query(WorkspaceLibraryFolder)
                .filter(WorkspaceLibraryFolder.parent_id == folder_id)
                .order_by(WorkspaceLibraryFolder.name)
                .all()
            )
            files = (
                session.query(WorkspaceLibraryFile)
                .filter(WorkspaceLibraryFile.folder_id == folder_id)
                .order_by(WorkspaceLibraryFile.created_at.desc())
                .all()
            )

        return {
            "folders": [_folder_to_dict(f) for f in folders],
            "files": [_file_to_dict(f) for f in files],
        }
    finally:
        session.close()


def get_folder_breadcrumb(folder_id: int) -> list[dict]:
    """Get the path from root to this folder as a list of {id, name} dicts."""
    from .workspace_database import WorkspaceLibraryFolder, get_db_session

    session = get_db_session()
    try:
        crumbs = []
        current_id: Optional[int] = folder_id
        visited: set[int] = set()
        while current_id is not None:
            if current_id in visited:
                break
            visited.add(current_id)
            folder = (
                session.query(WorkspaceLibraryFolder)
                .filter(WorkspaceLibraryFolder.id == current_id)
                .first()
            )
            if not folder:
                break
            crumbs.append({"id": folder.id, "name": folder.name})
            current_id = folder.parent_id
        crumbs.reverse()
        return crumbs
    finally:
        session.close()


def get_folder_tree() -> list[dict]:
    """Get the full folder tree as a nested structure for sidebar rendering."""
    from .workspace_database import WorkspaceLibraryFolder, get_db_session

    session = get_db_session()
    try:
        all_folders = session.query(WorkspaceLibraryFolder).order_by(WorkspaceLibraryFolder.name).all()
        folders_by_id = {f.id: _folder_to_dict(f) for f in all_folders}

        # Add children lists
        for f in folders_by_id.values():
            f["children"] = []

        roots = []
        for f in folders_by_id.values():
            if f["parent_id"] is None:
                roots.append(f)
            elif f["parent_id"] in folders_by_id:
                folders_by_id[f["parent_id"]]["children"].append(f)

        return roots
    finally:
        session.close()


# ============================================================================
# File Operations (updated with folder support)
# ============================================================================

def upload_file(
    filename: str,
    content: bytes,
    conversation_id: Optional[int] = None,
    display_name: Optional[str] = None,
    tags: Optional[str] = None,
    folder_id: Optional[int] = None,
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
            folder_id=folder_id,
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
        logger.info("Uploaded library file %d: %s (%d bytes, folder=%s)", lib_file.id, filename, file_size, folder_id)
        return _file_to_dict(lib_file)
    finally:
        session.close()


def upload_text(
    filename: str,
    text_content: str,
    conversation_id: Optional[int] = None,
    display_name: Optional[str] = None,
    tags: Optional[str] = None,
    folder_id: Optional[int] = None,
) -> dict:
    """Upload text content directly (for paste operations)."""
    content_bytes = text_content.encode("utf-8")
    return upload_file(filename, content_bytes, conversation_id, display_name, tags, folder_id)


def save_from_chat(
    content: str,
    filename: str,
    folder_id: Optional[int] = None,
    display_name: Optional[str] = None,
    tags: Optional[str] = None,
) -> dict:
    """Save content from a chat message into the library."""
    return upload_text(
        filename=filename,
        text_content=content,
        conversation_id=None,  # Always global scope
        display_name=display_name,
        tags=tags,
        folder_id=folder_id,
    )


def move_file(file_id: int, folder_id: Optional[int]) -> Optional[dict]:
    """Move a file to a different folder. folder_id=None means root."""
    from .workspace_database import WorkspaceLibraryFile, WorkspaceLibraryFolder, get_db_session

    session = get_db_session()
    try:
        lib_file = (
            session.query(WorkspaceLibraryFile)
            .filter(WorkspaceLibraryFile.id == file_id)
            .first()
        )
        if not lib_file:
            return None

        # Validate target folder exists
        if folder_id is not None:
            target = (
                session.query(WorkspaceLibraryFolder)
                .filter(WorkspaceLibraryFolder.id == folder_id)
                .first()
            )
            if not target:
                raise ValueError(f"Target folder {folder_id} not found")

        lib_file.folder_id = folder_id
        session.commit()
        session.refresh(lib_file)
        return _file_to_dict(lib_file)
    finally:
        session.close()


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

    NOTE: This is kept for backward compatibility but the preferred approach
    is now per-message attachment via get_files_context_by_ids().
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


# ============================================================================
# Per-message file attachment (replaces auto-injection)
# ============================================================================

def get_files_context_by_ids(file_ids: list[int], token_cap: int = 50_000) -> tuple[str, int]:
    """
    Build a context string for specific file IDs (per-message attachment).

    This is the replacement for auto-injection. The frontend sends file IDs
    with each message, and the backend inlines their content into that
    single message only.

    Args:
        file_ids: List of library file IDs to include.
        token_cap: Maximum tokens for the combined content (default 50K).

    Returns:
        Tuple of (context_string, estimated_token_count)
    """
    if not file_ids:
        return "", 0

    parts = []
    total_tokens = 0
    for fid in file_ids:
        content = get_file_content(fid)
        if not content:
            continue

        # Get file metadata for the header
        from .workspace_database import WorkspaceLibraryFile, get_db_session
        session = get_db_session()
        try:
            lib_file = (
                session.query(WorkspaceLibraryFile)
                .filter(WorkspaceLibraryFile.id == fid)
                .first()
            )
            display_name = (lib_file.display_name or lib_file.filename) if lib_file else f"file-{fid}"
            file_type = lib_file.file_type if lib_file else "unknown"
        finally:
            session.close()

        block = (
            f"--- Attached File: {display_name} ({file_type}) ---\n"
            f"{content}\n"
            f"--- End File ---"
        )
        block_tokens = len(block) // 4
        if total_tokens + block_tokens > token_cap:
            logger.warning(
                "Attachment context capped at ~%d tokens. Skipping '%s' (%d tokens).",
                total_tokens, display_name, block_tokens,
            )
            break
        parts.append(block)
        total_tokens += block_tokens

    return "\n\n".join(parts), total_tokens


def get_active_files_context(conversation_id: int, token_cap: int = 50_000) -> tuple[str, int]:
    """
    Build the context string for all active files in a conversation.

    NOTE: This is the legacy auto-injection function. It is kept for backward
    compatibility but the preferred approach is now get_files_context_by_ids()
    which attaches files to individual messages.

    Args:
        conversation_id: The conversation ID.
        token_cap: Maximum tokens for library injection (default 50K).

    Returns:
        Tuple of (context_string, estimated_token_count)
    """
    active_files = get_active_files(conversation_id)
    if not active_files:
        return "", 0

    file_ids = [f["id"] for f in active_files]
    return get_files_context_by_ids(file_ids, token_cap)
