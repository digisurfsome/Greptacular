# Phase 3: File Library & GitHub Integration

## Agent OS Blueprint for IdeaForge Workspace

---

## 1. What You're Building

Phase 3 adds two major features to the IdeaForge Workspace:

1. **File Library** -- A document management system where users upload, organize, and inject files into chat context. Files can be scoped globally (available to all conversations) or per-chat (attached to a specific conversation). Active files are prepended to the user's message so Claude can reference them.

2. **GitHub Repository Connection** -- Users connect GitHub repos by URL and personal access token. Repos are cloned locally and made accessible to Claude's Read/Write/Edit/Bash tools within the workspace chat session. Tokens are encrypted at rest using machine-derived Fernet keys.

3. **Enhanced Context Budget Bar** -- The existing context budget visualization gains two new segments (Library and Repos) so users can see how much of their 1M token window is consumed by injected files and repository context.

---

## 2. Prerequisites (Phases 1-2 Already Built)

Before starting Phase 3, verify these exist:

### Backend files
- `server/routers/workspace.py` -- Workspace router with prefix `/api/workspace`
- `server/services/workspace_database.py` -- Global SQLite DB at `~/.autoforge/workspace.db`
- `server/services/workspace_chat_session.py` -- Chat session manager (Claude SDK client per conversation)

### Database tables (in `workspace.db`)
```sql
workspace_conversations (id, title, category, pinned, token_count, summary, summary_updated_at, created_at, updated_at)
workspace_messages (id, conversation_id, role, content, token_estimate, timestamp)
workspace_categories (id, name, color, sort_order, created_at)
workspace_summaries (id, conversation_id, summary, message_count, token_estimate, created_at)
```

### API endpoints already working
```
GET/POST   /api/workspace/conversations
GET/PATCH/DELETE /api/workspace/conversations/{id}
GET    /api/workspace/conversations/{id}/context-budget
GET    /api/workspace/conversations/{id}/summary
POST   /api/workspace/conversations/{id}/summarize
GET/POST/PATCH/DELETE /api/workspace/categories[/{id}]
GET    /api/workspace/search?q=...
WS     /api/workspace/ws/{conversation_id}
```

### Frontend files
- `ui/src/components/workspace/WorkspacePage.tsx` -- Full-page workspace at `/#/workspace`
- `ui/src/components/workspace/WorkspaceSidebar.tsx` -- Conversation sidebar
- `ui/src/components/workspace/WorkspaceChat.tsx` -- Streaming chat
- `ui/src/components/workspace/ContextBudgetBar.tsx` -- Token budget visualization

### Routing
- `ui/src/lib/routes.ts` has `isWorkspaceRoute()`
- `ui/src/main.tsx` renders `WorkspacePage` for `/#/workspace`

---

## 3. New Dependencies

### Python (add to `requirements.txt`)

```
cryptography>=43.0.0
```

`python-multipart` is already in `requirements.txt` (version `>=0.0.17`). Verify it is present; do not add a duplicate.

### Frontend

No new npm packages required. The existing stack (React 19, TanStack Query, Tailwind CSS v4) is sufficient. File upload uses the native `fetch` API with `FormData`. Syntax highlighting for file preview uses a `<pre>` block with `font-mono` -- no third-party highlighter needed for Phase 3.

---

## 4. Files to Create

### 4.1 `server/services/workspace_library.py`

File library service: upload, delete, toggle, list, content retrieval.

```python
"""
Workspace Library Service
=========================

Manages file uploads, storage, and context injection for the workspace.
Files can be global (available to all conversations) or per-chat.
"""

import logging
import os
import uuid
from pathlib import Path
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

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
```

**Key functions to implement:**

```python
def ensure_library_dir() -> Path:
    """Create library directory if it doesn't exist. Return the path."""
    LIBRARY_DIR.mkdir(parents=True, exist_ok=True)
    return LIBRARY_DIR


def detect_file_type(filename: str) -> str:
    """Classify file type from extension. Returns 'doc', 'code', 'spec', 'template', or 'upload'."""
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

    Returns:
        Dict with file metadata.
    """
    ...


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
    ...


def delete_file(file_id: int) -> bool:
    """Delete a file from DB and disk (if stored on disk)."""
    ...


def list_global_files() -> list[dict]:
    """List all files where conversation_id IS NULL (global scope)."""
    ...


def list_conversation_files(conversation_id: int) -> list[dict]:
    """List files for a conversation: global files + per-chat files for this conversation."""
    ...


def toggle_file_in_context(file_id: int, conversation_id: int) -> dict:
    """
    Toggle a file's active_in_context status for a conversation.

    For global files: creates a per-conversation activation record.
    For per-chat files: toggles the active_in_context column directly.

    Returns updated file dict.
    """
    ...


def get_active_files(conversation_id: int) -> list[dict]:
    """Get all files that are currently active in a conversation's context."""
    ...


def update_file_metadata(file_id: int, display_name: Optional[str] = None, tags: Optional[str] = None) -> Optional[dict]:
    """Update display_name and/or tags for a file."""
    ...


def get_active_files_context(conversation_id: int) -> tuple[str, int]:
    """
    Build the context string for all active files in a conversation.

    Returns:
        Tuple of (context_string, estimated_token_count)

    The context string format:
        --- Library File: {display_name} ({file_type}) ---
        {file_content}
        --- End File ---

        (repeated for each active file)
    """
    active_files = get_active_files(conversation_id)
    if not active_files:
        return "", 0

    parts = []
    total_tokens = 0
    for f in active_files:
        content = get_file_content(f["id"])
        if content:
            block = f"--- Library File: {f['display_name']} ({f['file_type']}) ---\n{content}\n--- End File ---"
            parts.append(block)
            total_tokens += len(block) // 3  # same estimation as workspace_database.py

    return "\n\n".join(parts), total_tokens
```

**Database table** -- The `workspace_library_files` table must be added to the same `workspace.db` database. Add the SQLAlchemy model to `workspace_database.py` (see Section 5.1 for modifications).

**Activation tracking for global files** -- Global files need per-conversation activation state. Add a junction table:

```sql
CREATE TABLE workspace_file_activations (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL,
    conversation_id INTEGER NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (file_id) REFERENCES workspace_library_files(id) ON DELETE CASCADE,
    FOREIGN KEY (conversation_id) REFERENCES workspace_conversations(id) ON DELETE CASCADE,
    UNIQUE(file_id, conversation_id)
);
```

This allows the same global file to be active in one conversation but not another. Per-chat files use their own `active_in_context` column directly since they belong to one conversation only.

---

### 4.2 `server/services/workspace_token_encryption.py`

Token encryption for GitHub access tokens.

```python
"""
Workspace Token Encryption
===========================

Encrypts and stores GitHub personal access tokens using Fernet symmetric
encryption. The encryption key is derived from the machine's MAC address,
making tokens non-portable between machines (intentional security measure).

Tokens are stored in ~/.autoforge/workspace/.tokens (JSON file).
Only encrypted values are persisted; plaintext tokens never touch disk.
"""

import base64
import hashlib
import json
import logging
import uuid
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

TOKENS_FILE = Path.home() / ".autoforge" / "workspace" / ".tokens"


def _get_machine_key() -> bytes:
    """
    Derive a Fernet-compatible encryption key from the machine's MAC address.

    Uses SHA-256 hash of the MAC address (uuid.getnode()) to produce
    a 32-byte key, then base64url-encodes it for Fernet compatibility.

    Note: uuid.getnode() may return a random value on some systems if
    no MAC address is available. This is acceptable -- the key just needs
    to be stable per machine across restarts.
    """
    machine_id = str(uuid.getnode())
    key_bytes = hashlib.sha256(machine_id.encode()).digest()
    return base64.urlsafe_b64encode(key_bytes)


def encrypt_token(token: str) -> str:
    """Encrypt a plaintext token string. Returns the encrypted ciphertext."""
    f = Fernet(_get_machine_key())
    return f.encrypt(token.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    """
    Decrypt an encrypted token string. Returns plaintext.

    Raises:
        ValueError: If decryption fails (wrong machine, corrupted data).
    """
    try:
        f = Fernet(_get_machine_key())
        return f.decrypt(encrypted.encode()).decode()
    except InvalidToken:
        raise ValueError("Failed to decrypt token -- was it encrypted on a different machine?")


def store_token(ref_id: str, token: str) -> None:
    """
    Encrypt and store a token with a reference ID.

    Creates the .tokens file and parent directories if they don't exist.
    """
    TOKENS_FILE.parent.mkdir(parents=True, exist_ok=True)

    tokens = _load_tokens_file()
    tokens[ref_id] = encrypt_token(token)
    _save_tokens_file(tokens)
    logger.info(f"Stored encrypted token with ref_id={ref_id}")


def retrieve_token(ref_id: str) -> Optional[str]:
    """
    Retrieve and decrypt a token by reference ID.

    Returns None if the ref_id is not found.
    """
    tokens = _load_tokens_file()
    encrypted = tokens.get(ref_id)
    if encrypted is None:
        return None
    return decrypt_token(encrypted)


def delete_token(ref_id: str) -> bool:
    """Delete a token by reference ID. Returns True if found and deleted."""
    tokens = _load_tokens_file()
    if ref_id not in tokens:
        return False
    del tokens[ref_id]
    _save_tokens_file(tokens)
    logger.info(f"Deleted token with ref_id={ref_id}")
    return True


def _load_tokens_file() -> dict[str, str]:
    """Load the tokens JSON file. Returns empty dict if file doesn't exist."""
    if not TOKENS_FILE.exists():
        return {}
    try:
        return json.loads(TOKENS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Failed to load tokens file: {e}")
        return {}


def _save_tokens_file(tokens: dict[str, str]) -> None:
    """Save tokens dict to the JSON file with restricted permissions."""
    TOKENS_FILE.write_text(json.dumps(tokens, indent=2), encoding="utf-8")
    # Restrict file permissions (owner read/write only)
    try:
        TOKENS_FILE.chmod(0o600)
    except OSError:
        pass  # Windows doesn't support Unix permissions
```

---

### 4.3 `server/services/workspace_repos.py`

GitHub repository connection service.

```python
"""
Workspace Repository Service
=============================

Manages GitHub repository connections for the workspace.
Repos are cloned to ~/.autoforge/workspace/repos/ and made
accessible to Claude's tools within chat sessions.
"""

import logging
import re
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

REPOS_DIR = Path.home() / ".autoforge" / "workspace" / "repos"


def ensure_repos_dir() -> Path:
    """Create repos directory if it doesn't exist."""
    REPOS_DIR.mkdir(parents=True, exist_ok=True)
    return REPOS_DIR


def validate_repo_url(url: str) -> bool:
    """
    Validate that the URL looks like a GitHub HTTPS repo URL.

    Accepts:
        https://github.com/owner/repo
        https://github.com/owner/repo.git
    """
    pattern = r"^https://github\.com/[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+(\.git)?$"
    return bool(re.match(pattern, url))


def _build_authenticated_url(repo_url: str, token: str) -> str:
    """
    Insert token into GitHub HTTPS URL for authenticated clone.

    https://github.com/owner/repo -> https://{token}@github.com/owner/repo
    """
    return repo_url.replace("https://", f"https://{token}@", 1)


def extract_repo_name(repo_url: str) -> str:
    """
    Extract 'owner/repo' from a GitHub URL.

    https://github.com/owner/repo.git -> owner/repo
    """
    # Remove trailing .git
    url = repo_url.rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]
    parts = url.split("/")
    if len(parts) >= 2:
        return f"{parts[-2]}/{parts[-1]}"
    return parts[-1]


def _local_dir_name(repo_url: str) -> str:
    """Generate a safe directory name from repo URL: owner_repo."""
    name = extract_repo_name(repo_url)
    return name.replace("/", "_")


def connect_repo(
    repo_url: str,
    token: str,
    branch: str = "main",
    conversation_id: Optional[int] = None,
) -> dict:
    """
    Connect a GitHub repo: validate, encrypt token, clone, store metadata.

    Steps:
        1. Validate repo URL format
        2. Encrypt token via workspace_token_encryption.store_token()
        3. Clone repo to ~/.autoforge/workspace/repos/{owner}_{repo}/
        4. Store metadata in workspace_connected_repos table
        5. Return repo info dict

    Returns:
        Dict with repo metadata including id, repo_name, local_path, branch.

    Raises:
        ValueError: If URL is invalid or clone fails.
    """
    ...


def disconnect_repo(repo_id: int, delete_local: bool = False) -> bool:
    """
    Disconnect a repo: remove DB record, delete encrypted token,
    optionally delete local clone.
    """
    ...


def sync_repo(repo_id: int) -> dict:
    """
    Pull latest changes for a connected repo.

    Runs: git -C {local_path} pull origin {branch}
    Updates last_synced_at in DB.
    """
    ...


def get_repo_tree(repo_id: int, max_depth: int = 3) -> list[dict]:
    """
    Get the file tree of a connected repo.

    Returns a list of dicts with:
        {"path": str, "type": "file"|"dir", "size": int}

    Uses os.walk() on the local clone, excluding .git/ directory.
    Limits depth to max_depth levels for performance.
    """
    ...


def get_repo_file(repo_id: int, file_path: str) -> Optional[str]:
    """
    Read a specific file from a connected repo.

    Validates that the resolved path stays within the repo directory
    (prevents path traversal attacks via '../' in file_path).

    Returns file content as string, or None if not found / binary.
    """
    ...


def list_repos(conversation_id: Optional[int] = None) -> list[dict]:
    """
    List connected repos.

    If conversation_id is None: return all repos (global + all per-chat).
    If conversation_id is set: return global repos + repos for that conversation.
    """
    ...
```

**Clone security:** When cloning, never log the authenticated URL (it contains the token). Use `subprocess.run()` with `capture_output=True` and check the return code. On failure, sanitize the error message to remove any token substring before raising the exception.

---

### 4.4 Frontend: `ui/src/components/workspace/WorkspaceLibrary.tsx`

Right panel component, toggleable from the chat header.

**Props:**
```typescript
interface WorkspaceLibraryProps {
  conversationId: number | null
  onClose: () => void
}
```

**Layout:**
```
+-----------------------------------------------+
| Library                              [X close] |
+-----------------------------------------------+
| [Upload File]  [Paste Text]                    |
+-----------------------------------------------+
| > Global Files (3)                             |
|   [icon] project-spec.md     [toggle] [...]    |
|   [icon] design-tokens.json  [toggle] [...]    |
|   [icon] api-reference.txt   [toggle] [...]    |
+-----------------------------------------------+
| > Chat Files (1)                               |
|   [icon] meeting-notes.md    [toggle] [...]    |
+-----------------------------------------------+
| > Connected Repos (1)                          |
|   [git] owner/repo-name     [sync] [...]       |
+-----------------------------------------------+
```

**Behavior:**
- Three collapsible sections: "Global Files", "Chat Files", "Connected Repos"
- Each file row shows: type icon (from `file_type`), display name, size (human-readable), active/inactive toggle switch
- Toggle switch calls `POST /api/workspace/library/{file_id}/toggle/{conversation_id}`
- "..." menu on each file: Preview, Edit Metadata, Delete
- "Upload File" button opens `FileUploadModal`
- "Paste Text" button opens `FileUploadModal` in text mode
- Drag-and-drop zone at the top (entire panel is a drop target)
- Repos section shows connected repos with sync button and disconnect option

**Styling (theme-agnostic):**
```
Panel:        bg-card border-l border-border
Section head: text-foreground font-semibold text-sm
File row:     hover:bg-muted/50 px-3 py-2 rounded-md
Toggle:       bg-muted -> bg-primary when active (use a simple div-based toggle)
Upload zone:  border-2 border-dashed border-border hover:border-primary
```

**TanStack Query hooks (add to a new file `ui/src/hooks/useWorkspaceLibrary.ts`):**

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

// Query keys
const LIBRARY_KEYS = {
  global: ['workspace', 'library', 'global'] as const,
  conversation: (id: number) => ['workspace', 'library', 'conversation', id] as const,
  active: (id: number) => ['workspace', 'library', 'active', id] as const,
  content: (fileId: number) => ['workspace', 'library', 'content', fileId] as const,
}

export function useGlobalFiles() {
  return useQuery({
    queryKey: LIBRARY_KEYS.global,
    queryFn: () => fetchJSON<LibraryFile[]>('/workspace/library'),
  })
}

export function useConversationFiles(conversationId: number | null) {
  return useQuery({
    queryKey: conversationId ? LIBRARY_KEYS.conversation(conversationId) : [],
    queryFn: () => fetchJSON<LibraryFile[]>(`/workspace/library/conversation/${conversationId}`),
    enabled: !!conversationId,
  })
}

export function useActiveFiles(conversationId: number | null) {
  return useQuery({
    queryKey: conversationId ? LIBRARY_KEYS.active(conversationId) : [],
    queryFn: () => fetchJSON<LibraryFile[]>(`/workspace/library/active/${conversationId}`),
    enabled: !!conversationId,
  })
}

export function useToggleFile(conversationId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (fileId: number) =>
      fetchJSON(`/workspace/library/${fileId}/toggle/${conversationId}`, { method: 'POST' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: LIBRARY_KEYS.conversation(conversationId) })
      queryClient.invalidateQueries({ queryKey: LIBRARY_KEYS.active(conversationId) })
      queryClient.invalidateQueries({ queryKey: LIBRARY_KEYS.global })
    },
  })
}

export function useUploadFile() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: { file: File; conversationId?: number; displayName?: string; tags?: string }) => {
      const formData = new FormData()
      formData.append('file', data.file)
      if (data.conversationId) formData.append('conversation_id', String(data.conversationId))
      if (data.displayName) formData.append('display_name', data.displayName)
      if (data.tags) formData.append('tags', data.tags)

      const response = await fetch('/api/workspace/library/upload', {
        method: 'POST',
        body: formData,
        // Do NOT set Content-Type -- browser sets multipart boundary automatically
      })
      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: 'Upload failed' }))
        throw new Error(err.detail)
      }
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workspace', 'library'] })
    },
  })
}

export function useDeleteFile() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (fileId: number) =>
      fetchJSON(`/workspace/library/${fileId}`, { method: 'DELETE' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workspace', 'library'] })
    },
  })
}
```

---

### 4.5 Frontend: `ui/src/components/workspace/FileUploadModal.tsx`

Modal for uploading files or pasting text.

**Props:**
```typescript
interface FileUploadModalProps {
  open: boolean
  onClose: () => void
  conversationId: number | null
  mode: 'file' | 'text'  // 'file' = file picker, 'text' = paste textarea
}
```

**Layout (file mode):**
```
+-------------------------------------------+
| Upload File                        [X]    |
+-------------------------------------------+
| +---------------------------------------+ |
| |                                       | |
| |    Drag & drop a file here            | |
| |    or click to browse                 | |
| |                                       | |
| +---------------------------------------+ |
|                                           |
| Display Name: [auto-filled from filename] |
| Tags:         [comma-separated input    ] |
| Scope:        ( ) Global  ( ) This Chat   |
|                                           |
| [Cancel]                      [Upload]    |
+-------------------------------------------+
```

**Layout (text mode):**
```
+-------------------------------------------+
| Paste Content                      [X]    |
+-------------------------------------------+
| Filename:     [my-notes.md            ]   |
|                                           |
| +---------------------------------------+ |
| | (textarea for pasting content)        | |
| |                                       | |
| +---------------------------------------+ |
|                                           |
| Display Name: [auto-filled from name   ]  |
| Tags:         [comma-separated input   ]  |
| Scope:        ( ) Global  ( ) This Chat   |
|                                           |
| [Cancel]                      [Save]      |
+-------------------------------------------+
```

**Behavior:**
- File picker accepts extensions from `ALLOWED_EXTENSIONS` (pass as `accept` attribute)
- Shows file size after selection; reject files > 10MB with inline error
- "Scope" radio buttons: Global (conversation_id = null) or This Chat (conversation_id = current)
- Disable "This Chat" if no conversation is active (conversationId is null)
- Upload progress: disable button and show spinner text "Uploading..."
- On success: close modal, invalidate library queries
- On error: show error message in destructive-colored text below the form

**Styling:**
```
Modal:        bg-card border border-border rounded-lg shadow-lg p-6 max-w-md
Drop zone:    border-2 border-dashed border-border rounded-lg p-8 text-center
              hover:border-primary hover:bg-muted/30
              (when dragging over: border-primary bg-muted/50)
Inputs:       bg-background border border-input rounded-md px-3 py-2
Radio:        Standard radio buttons with text-foreground labels
Buttons:      Cancel = bg-muted text-foreground, Upload = bg-primary text-primary-foreground
```

---

### 4.6 Frontend: `ui/src/components/workspace/FilePreview.tsx`

File content preview, either as a modal or inline panel.

**Props:**
```typescript
interface FilePreviewProps {
  fileId: number
  fileName: string
  fileType: string
  onClose: () => void
  onToggleContext?: () => void
  onDelete?: () => void
  isActive?: boolean
}
```

**Content rendering:**
- `.md` files: Render through the same markdown pipeline used in `WorkspaceChat.tsx` (the `chat-prose` CSS class)
- `.py`, `.js`, `.ts`, etc. (code files): `<pre><code>` block with `font-mono text-sm` styling
- All other files: Plain `<pre>` block

**Layout:**
```
+------------------------------------------------+
| file-name.md                           [X]     |
+------------------------------------------------+
| [Toggle into Context]  [Delete]                 |
+------------------------------------------------+
| (rendered content area, scrollable)             |
|                                                 |
| ...                                             |
+------------------------------------------------+
```

**Data fetching:**
```typescript
const { data: content, isLoading } = useQuery({
  queryKey: LIBRARY_KEYS.content(fileId),
  queryFn: () => fetchJSON<{ content: string }>(`/workspace/library/${fileId}/content`),
})
```

---

### 4.7 Frontend: `ui/src/components/workspace/RepoConnector.tsx`

Modal for connecting a GitHub repository.

**Props:**
```typescript
interface RepoConnectorProps {
  open: boolean
  onClose: () => void
  conversationId: number | null
}
```

**Layout:**
```
+------------------------------------------------+
| Connect GitHub Repository              [X]     |
+------------------------------------------------+
|                                                 |
| Repository URL:                                 |
| [https://github.com/owner/repo         ]       |
|                                                 |
| Personal Access Token:                          |
| [****************************************]      |
|  (fine-grained token with repo read access)     |
|                                                 |
| Branch:                                         |
| [main                                  ]        |
|                                                 |
| Scope:  ( ) Global  ( ) This Chat               |
|                                                 |
| [Cancel]                          [Connect]     |
+------------------------------------------------+
```

**Behavior:**
- URL field validates against GitHub HTTPS pattern on blur
- Token field is `type="password"` -- never displayed in plaintext
- Branch defaults to "main"
- Connect button: POST to `/api/workspace/repos/connect`
- Show loading state during clone (can take 10-30 seconds for large repos)
- On success: close modal, invalidate repo queries, show success toast
- On error: show error message

**TanStack Query hooks (add to `useWorkspaceLibrary.ts` or create `useWorkspaceRepos.ts`):**

```typescript
export function useConnectedRepos(conversationId: number | null) {
  return useQuery({
    queryKey: ['workspace', 'repos', conversationId],
    queryFn: () => fetchJSON<ConnectedRepo[]>(
      `/workspace/repos${conversationId ? `?conversation_id=${conversationId}` : ''}`
    ),
  })
}

export function useConnectRepo() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: { repoUrl: string; token: string; branch: string; conversationId?: number }) =>
      fetchJSON('/workspace/repos/connect', {
        method: 'POST',
        body: JSON.stringify({
          repo_url: data.repoUrl,
          token: data.token,
          branch: data.branch,
          conversation_id: data.conversationId,
        }),
        headers: { 'Content-Type': 'application/json' },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workspace', 'repos'] })
    },
  })
}

export function useSyncRepo() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (repoId: number) =>
      fetchJSON(`/workspace/repos/${repoId}/sync`, { method: 'POST' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workspace', 'repos'] })
    },
  })
}

export function useDisconnectRepo() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (repoId: number) =>
      fetchJSON(`/workspace/repos/${repoId}`, { method: 'DELETE' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workspace', 'repos'] })
    },
  })
}

export function useRepoTree(repoId: number | null) {
  return useQuery({
    queryKey: ['workspace', 'repos', 'tree', repoId],
    queryFn: () => fetchJSON<RepoTreeEntry[]>(`/workspace/repos/${repoId}/tree`),
    enabled: !!repoId,
  })
}
```

---

### 4.8 Frontend: `ui/src/components/workspace/RepoBrowser.tsx`

Inline tree view for connected repos, rendered inside the Library panel.

**Props:**
```typescript
interface RepoBrowserProps {
  repo: ConnectedRepo
  onSyncRepo: (repoId: number) => void
  onDisconnect: (repoId: number) => void
}
```

**Layout:**
- Collapsible tree with indent levels
- Directory nodes expand/collapse on click
- File nodes show file icon by extension
- Click file to open `FilePreview` with content from `/api/workspace/repos/{repo_id}/file?path=...`
- Repo header shows: repo name, branch badge, last synced time, sync button, disconnect button

**Styling:**
```
Tree item:    pl-{level*4} py-1 text-sm hover:bg-muted/50 cursor-pointer
Dir icon:     text-muted-foreground (folder emoji or chevron)
File icon:    text-muted-foreground
Branch badge: bg-muted text-muted-foreground text-xs px-2 py-0.5 rounded-md
Sync button:  text-muted-foreground hover:text-foreground (refresh icon)
```

---

## 5. Files to Modify

### 5.1 `server/services/workspace_database.py`

Add two new SQLAlchemy models and ensure they are created when the database engine initializes.

**Add these models:**

```python
class WorkspaceLibraryFile(Base):
    """A file in the workspace library."""
    __tablename__ = "workspace_library_files"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("workspace_conversations.id", ondelete="CASCADE"), nullable=True, index=True)
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
    file_id = Column(Integer, ForeignKey("workspace_library_files.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(Integer, ForeignKey("workspace_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    active = Column(Boolean, default=True)

    __table_args__ = (
        # Ensure unique file+conversation pairs
        {"sqlite_autoincrement": False},
    )


class WorkspaceConnectedRepo(Base):
    """A connected GitHub repository."""
    __tablename__ = "workspace_connected_repos"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("workspace_conversations.id", ondelete="SET NULL"), nullable=True, index=True)
    repo_url = Column(String(500), nullable=False)
    repo_name = Column(String(200), nullable=False)
    local_path = Column(String(500), nullable=True)
    access_token_ref = Column(String(100), nullable=True)
    branch = Column(String(100), default="main")
    last_synced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utc_now)
```

**Important:** Add a `UniqueConstraint` import and apply it to `WorkspaceFileActivation`:

```python
from sqlalchemy import UniqueConstraint

# On the WorkspaceFileActivation class:
__table_args__ = (
    UniqueConstraint('file_id', 'conversation_id', name='uq_file_conversation'),
)
```

The `Base.metadata.create_all(engine)` call in `get_engine()` will automatically create the new tables on first access. No manual migration script is needed.

---

### 5.2 `server/routers/workspace.py`

Add new API endpoints for the file library and repos.

**Library endpoints (add after existing endpoints):**

```python
from fastapi import File, Form, UploadFile
from typing import Optional

# ============================================================================
# Library Endpoints
# ============================================================================

@router.get("/library")
async def list_global_library_files():
    """List all global library files (not attached to any conversation)."""
    from ..services.workspace_library import list_global_files
    return list_global_files()


@router.get("/library/conversation/{conversation_id}")
async def list_conversation_library_files(conversation_id: int):
    """List files for a conversation (global + per-chat)."""
    from ..services.workspace_library import list_conversation_files
    return list_conversation_files(conversation_id)


@router.post("/library/upload")
async def upload_library_file(
    file: UploadFile = File(...),
    conversation_id: Optional[int] = Form(None),
    display_name: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
):
    """
    Upload a file to the library.

    Accepts multipart form data with:
    - file: The file to upload (required)
    - conversation_id: Attach to conversation (optional, null = global)
    - display_name: Display name override (optional)
    - tags: Comma-separated tags (optional)
    """
    from ..services.workspace_library import upload_file, MAX_FILE_SIZE, validate_file_extension

    # Validate file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB.")

    # Validate file extension
    filename = file.filename or "untitled"
    if not validate_file_extension(filename):
        raise HTTPException(status_code=400, detail=f"File type not supported: {filename}")

    result = upload_file(
        filename=filename,
        content=content,
        conversation_id=conversation_id,
        display_name=display_name,
        tags=tags,
    )
    return result


@router.post("/library/upload-text")
async def upload_text_content(body: dict):
    """
    Upload text content directly (for paste operations).

    Body: { "filename": str, "content": str, "conversation_id": int|null, "display_name": str|null, "tags": str|null }
    """
    from ..services.workspace_library import upload_text

    filename = body.get("filename", "untitled.txt")
    content = body.get("content", "")
    if not content:
        raise HTTPException(status_code=400, detail="Content is required")

    result = upload_text(
        filename=filename,
        text_content=content,
        conversation_id=body.get("conversation_id"),
        display_name=body.get("display_name"),
        tags=body.get("tags"),
    )
    return result


@router.get("/library/{file_id}/content")
async def get_library_file_content(file_id: int):
    """Get the content of a library file."""
    from ..services.workspace_library import get_file_content

    content = get_file_content(file_id)
    if content is None:
        raise HTTPException(status_code=404, detail="File not found or content unavailable")
    return {"content": content}


@router.patch("/library/{file_id}")
async def update_library_file(file_id: int, body: dict):
    """Update file metadata (display_name, tags)."""
    from ..services.workspace_library import update_file_metadata

    result = update_file_metadata(
        file_id=file_id,
        display_name=body.get("display_name"),
        tags=body.get("tags"),
    )
    if result is None:
        raise HTTPException(status_code=404, detail="File not found")
    return result


@router.delete("/library/{file_id}")
async def delete_library_file(file_id: int):
    """Delete a library file."""
    from ..services.workspace_library import delete_file

    success = delete_file(file_id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    return {"success": True}


@router.post("/library/{file_id}/toggle/{conversation_id}")
async def toggle_library_file_context(file_id: int, conversation_id: int):
    """Toggle a file's active/inactive status in a conversation's context."""
    from ..services.workspace_library import toggle_file_in_context

    result = toggle_file_in_context(file_id, conversation_id)
    if result is None:
        raise HTTPException(status_code=404, detail="File not found")
    return result


@router.get("/library/active/{conversation_id}")
async def get_active_library_files(conversation_id: int):
    """Get all files currently active in a conversation's context."""
    from ..services.workspace_library import get_active_files
    return get_active_files(conversation_id)


# ============================================================================
# Repository Endpoints
# ============================================================================

@router.post("/repos/connect")
async def connect_repository(body: dict):
    """
    Connect a GitHub repository.

    Body: { "repo_url": str, "token": str, "branch": str, "conversation_id": int|null }
    """
    from ..services.workspace_repos import connect_repo

    repo_url = body.get("repo_url", "")
    token = body.get("token", "")
    branch = body.get("branch", "main")
    conversation_id = body.get("conversation_id")

    if not repo_url:
        raise HTTPException(status_code=400, detail="Repository URL is required")
    if not token:
        raise HTTPException(status_code=400, detail="Personal access token is required")

    try:
        result = connect_repo(
            repo_url=repo_url,
            token=token,
            branch=branch,
            conversation_id=conversation_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/repos/{repo_id}")
async def disconnect_repository(repo_id: int, delete_local: bool = False):
    """Disconnect a repo and optionally delete local clone."""
    from ..services.workspace_repos import disconnect_repo

    success = disconnect_repo(repo_id, delete_local=delete_local)
    if not success:
        raise HTTPException(status_code=404, detail="Repository not found")
    return {"success": True}


@router.get("/repos")
async def list_repositories(conversation_id: Optional[int] = None):
    """List connected repositories."""
    from ..services.workspace_repos import list_repos
    return list_repos(conversation_id=conversation_id)


@router.get("/repos/{repo_id}/tree")
async def get_repository_tree(repo_id: int):
    """Get file tree for a connected repo."""
    from ..services.workspace_repos import get_repo_tree

    tree = get_repo_tree(repo_id)
    if tree is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    return tree


@router.get("/repos/{repo_id}/file")
async def get_repository_file(repo_id: int, path: str):
    """Read a specific file from a connected repo."""
    from ..services.workspace_repos import get_repo_file

    content = get_repo_file(repo_id, path)
    if content is None:
        raise HTTPException(status_code=404, detail="File not found or binary file")
    return {"content": content, "path": path}


@router.post("/repos/{repo_id}/sync")
async def sync_repository(repo_id: int):
    """Pull latest changes for a connected repo."""
    from ..services.workspace_repos import sync_repo

    try:
        result = sync_repo(repo_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

### 5.3 `server/services/workspace_chat_session.py`

Modify `send_message()` to inject active library file content.

**Find the section where `message_to_send` is built (in `send_message()`).** After the history loading logic and before sending to Claude, add library context injection:

```python
async def send_message(self, user_message: str) -> AsyncGenerator[dict, None]:
    # ... existing history loading code ...

    # Inject active library file content
    library_context = ""
    library_tokens = 0
    if self.conversation_id:
        from .workspace_library import get_active_files_context
        library_context, library_tokens = get_active_files_context(self.conversation_id)

    # Build final message with library context prepended
    if library_context:
        message_to_send = f"{library_context}\n\n{message_to_send}"

    # ... existing Claude query code ...
```

Also modify the session initialization to add connected repo paths to Claude's allowed filesystem access. In the `start()` method, after creating the `ClaudeSDKClient`:

```python
# Add connected repo paths to allowed filesystem
if self.conversation_id:
    from .workspace_repos import list_repos
    repos = list_repos(conversation_id=self.conversation_id)
    extra_read_paths = [r["local_path"] for r in repos if r.get("local_path")]
    # These paths get added to the SDK client's allowed read/write paths
```

**Important:** The exact mechanism for adding extra paths depends on how the Phase 1-2 chat session was implemented. If it uses `ClaudeAgentOptions(cwd=...)`, connected repos can be added as additional `allowed_paths` entries. If the session uses a settings JSON file with `permissions.allow`, add `Read({repo_path}/**)` and `Edit({repo_path}/**)` entries.

Also update the context budget calculation to include library tokens. In whatever function calculates the context budget for the `/context-budget` endpoint:

```python
def get_context_budget(conversation_id: int) -> dict:
    # ... existing calculation ...

    # Add library file tokens
    from .workspace_library import get_active_files_context
    _, library_tokens = get_active_files_context(conversation_id)

    # Add repo context tokens (estimate: file tree ~500 tokens per repo)
    from .workspace_repos import list_repos
    repos = list_repos(conversation_id=conversation_id)
    repo_tokens = len(repos) * 500  # rough estimate for tree context

    return {
        "total_budget": 1_000_000,
        "messages_tokens": message_tokens,
        "summary_tokens": summary_tokens,
        "library_tokens": library_tokens,
        "repo_tokens": repo_tokens,
        "available_tokens": 1_000_000 - message_tokens - summary_tokens - library_tokens - repo_tokens,
    }
```

---

### 5.4 `ui/src/components/workspace/ContextBudgetBar.tsx`

Add Library and Repo segments to the budget bar.

**Update the segment data structure.** The existing bar shows Messages and Available. Add:

```typescript
interface BudgetSegment {
  label: string
  tokens: number
  color: string  // Tailwind bg class
  tooltip: string
}

// Build segments from budget data:
const segments: BudgetSegment[] = [
  {
    label: 'Messages',
    tokens: budget.messages_tokens + budget.summary_tokens,
    color: 'bg-primary',
    tooltip: `${formatTokens(budget.messages_tokens)} message tokens + ${formatTokens(budget.summary_tokens)} summary tokens`,
  },
  {
    label: 'Library',
    tokens: budget.library_tokens,
    color: 'bg-chart-4',  // Uses chart-4 from theme tokens (typically purple/violet range)
    tooltip: `${formatTokens(budget.library_tokens)} tokens from ${activeFileCount} active files`,
  },
  {
    label: 'Repos',
    tokens: budget.repo_tokens,
    color: 'bg-chart-2',  // Uses chart-2 from theme tokens (typically green/teal range)
    tooltip: `${formatTokens(budget.repo_tokens)} tokens from ${repoCount} connected repos`,
  },
]

// Filter out zero-token segments
const visibleSegments = segments.filter(s => s.tokens > 0)
```

**Bar rendering:**
```tsx
<div className="flex h-2 w-full rounded-full bg-muted overflow-hidden">
  {visibleSegments.map((seg, i) => (
    <div
      key={seg.label}
      className={`${seg.color} transition-all duration-300`}
      style={{ width: `${(seg.tokens / budget.total_budget) * 100}%` }}
      title={seg.tooltip}
    />
  ))}
</div>
```

**Legend update (below the bar):**
```tsx
<div className="flex flex-wrap gap-3 text-xs text-muted-foreground mt-1">
  {visibleSegments.map(seg => (
    <span key={seg.label} className="flex items-center gap-1">
      <span className={`inline-block w-2 h-2 rounded-full ${seg.color}`} />
      {seg.label}: {formatTokens(seg.tokens)}
    </span>
  ))}
  <span className="flex items-center gap-1">
    <span className="inline-block w-2 h-2 rounded-full bg-muted" />
    Available: {formatTokens(budget.available_tokens)}
  </span>
</div>
```

---

### 5.5 `ui/src/components/workspace/WorkspacePage.tsx`

Add the toggleable right panel for the library.

**Update the layout from two-panel to three-panel:**

```tsx
// State for library panel visibility
const [libraryOpen, setLibraryOpen] = useState(false)

// In the JSX:
<div className="flex h-screen">
  {/* Left: Conversation Sidebar */}
  <WorkspaceSidebar ... />

  {/* Center: Chat Area */}
  <div className="flex-1 flex flex-col min-w-0">
    {/* Chat header with library toggle button */}
    <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-card">
      <span className="font-semibold text-foreground">
        {currentConversation?.title || 'New Chat'}
      </span>
      <button
        onClick={() => setLibraryOpen(!libraryOpen)}
        className={`p-2 rounded-md transition-colors ${
          libraryOpen
            ? 'bg-primary/10 text-primary'
            : 'text-muted-foreground hover:text-foreground hover:bg-muted'
        }`}
        title="Toggle Library"
      >
        {/* Folder/document icon SVG */}
        <svg className="w-5 h-5" ...>{/* folder icon */}</svg>
      </button>
    </div>

    {/* Chat content */}
    <WorkspaceChat ... />
  </div>

  {/* Right: Library Panel (conditional) */}
  {libraryOpen && (
    <div className="w-80 border-l border-border bg-card flex-shrink-0 overflow-y-auto">
      <WorkspaceLibrary
        conversationId={activeConversationId}
        onClose={() => setLibraryOpen(false)}
      />
    </div>
  )}
</div>
```

---

### 5.6 `ui/src/lib/types.ts`

Add TypeScript types for library files and connected repos.

```typescript
// ============================================================================
// Workspace Library Types
// ============================================================================

export interface LibraryFile {
  id: number
  conversation_id: number | null
  filename: string
  display_name: string | null
  file_type: string
  file_size: number
  tags: string | null
  active_in_context: boolean
  created_at: string
}

export interface ConnectedRepo {
  id: number
  conversation_id: number | null
  repo_url: string
  repo_name: string
  local_path: string | null
  branch: string
  last_synced_at: string | null
  created_at: string
}

export interface RepoTreeEntry {
  path: string
  type: 'file' | 'dir'
  size: number
}

export interface ContextBudget {
  total_budget: number
  messages_tokens: number
  summary_tokens: number
  library_tokens: number
  repo_tokens: number
  available_tokens: number
}
```

---

### 5.7 `ui/src/lib/api.ts`

Add API functions for library and repos. Add these at the bottom of the file (before the closing exports):

```typescript
// ============================================================================
// Workspace Library API
// ============================================================================

export async function listGlobalLibraryFiles(): Promise<LibraryFile[]> {
  return fetchJSON('/workspace/library')
}

export async function listConversationLibraryFiles(conversationId: number): Promise<LibraryFile[]> {
  return fetchJSON(`/workspace/library/conversation/${conversationId}`)
}

export async function uploadLibraryFile(
  file: File,
  conversationId?: number,
  displayName?: string,
  tags?: string,
): Promise<LibraryFile> {
  const formData = new FormData()
  formData.append('file', file)
  if (conversationId != null) formData.append('conversation_id', String(conversationId))
  if (displayName) formData.append('display_name', displayName)
  if (tags) formData.append('tags', tags)

  const response = await fetch(`${API_BASE}/workspace/library/upload`, {
    method: 'POST',
    body: formData,
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Upload failed' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function uploadLibraryText(
  filename: string,
  content: string,
  conversationId?: number,
  displayName?: string,
  tags?: string,
): Promise<LibraryFile> {
  return fetchJSON('/workspace/library/upload-text', {
    method: 'POST',
    body: JSON.stringify({
      filename,
      content,
      conversation_id: conversationId ?? null,
      display_name: displayName ?? null,
      tags: tags ?? null,
    }),
  })
}

export async function getLibraryFileContent(fileId: number): Promise<{ content: string }> {
  return fetchJSON(`/workspace/library/${fileId}/content`)
}

export async function updateLibraryFile(
  fileId: number,
  data: { display_name?: string; tags?: string },
): Promise<LibraryFile> {
  return fetchJSON(`/workspace/library/${fileId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export async function deleteLibraryFile(fileId: number): Promise<void> {
  await fetchJSON(`/workspace/library/${fileId}`, { method: 'DELETE' })
}

export async function toggleLibraryFile(
  fileId: number,
  conversationId: number,
): Promise<LibraryFile> {
  return fetchJSON(`/workspace/library/${fileId}/toggle/${conversationId}`, {
    method: 'POST',
  })
}

export async function getActiveLibraryFiles(conversationId: number): Promise<LibraryFile[]> {
  return fetchJSON(`/workspace/library/active/${conversationId}`)
}

// ============================================================================
// Workspace Repository API
// ============================================================================

export async function connectRepository(
  repoUrl: string,
  token: string,
  branch: string = 'main',
  conversationId?: number,
): Promise<ConnectedRepo> {
  return fetchJSON('/workspace/repos/connect', {
    method: 'POST',
    body: JSON.stringify({
      repo_url: repoUrl,
      token,
      branch,
      conversation_id: conversationId ?? null,
    }),
  })
}

export async function disconnectRepository(
  repoId: number,
  deleteLocal: boolean = false,
): Promise<void> {
  await fetchJSON(`/workspace/repos/${repoId}?delete_local=${deleteLocal}`, {
    method: 'DELETE',
  })
}

export async function listRepositories(conversationId?: number): Promise<ConnectedRepo[]> {
  const params = conversationId != null ? `?conversation_id=${conversationId}` : ''
  return fetchJSON(`/workspace/repos${params}`)
}

export async function getRepoTree(repoId: number): Promise<RepoTreeEntry[]> {
  return fetchJSON(`/workspace/repos/${repoId}/tree`)
}

export async function getRepoFile(repoId: number, path: string): Promise<{ content: string; path: string }> {
  return fetchJSON(`/workspace/repos/${repoId}/file?path=${encodeURIComponent(path)}`)
}

export async function syncRepository(repoId: number): Promise<ConnectedRepo> {
  return fetchJSON(`/workspace/repos/${repoId}/sync`, { method: 'POST' })
}
```

Also add the type imports at the top of the file:
```typescript
import type { ..., LibraryFile, ConnectedRepo, RepoTreeEntry, ContextBudget } from './types'
```

---

## 6. Database Schema

### New tables (added to `workspace.db`)

```sql
-- File library
CREATE TABLE workspace_library_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER,
    filename VARCHAR(500) NOT NULL,
    display_name VARCHAR(200),
    file_type VARCHAR(50),
    content TEXT,
    file_path VARCHAR(500),
    file_size INTEGER,
    tags VARCHAR(500),
    active_in_context BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES workspace_conversations(id) ON DELETE CASCADE
);

-- Per-conversation file activation (for global files)
CREATE TABLE workspace_file_activations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    conversation_id INTEGER NOT NULL,
    active BOOLEAN DEFAULT 1,
    FOREIGN KEY (file_id) REFERENCES workspace_library_files(id) ON DELETE CASCADE,
    FOREIGN KEY (conversation_id) REFERENCES workspace_conversations(id) ON DELETE CASCADE,
    UNIQUE(file_id, conversation_id)
);

-- Connected repositories
CREATE TABLE workspace_connected_repos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER,
    repo_url VARCHAR(500) NOT NULL,
    repo_name VARCHAR(200) NOT NULL,
    local_path VARCHAR(500),
    access_token_ref VARCHAR(100),
    branch VARCHAR(100) DEFAULT 'main',
    last_synced_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES workspace_conversations(id) ON DELETE SET NULL
);
```

**Migration strategy:** SQLAlchemy's `Base.metadata.create_all(engine)` handles table creation automatically. New tables are created on the next engine initialization. No manual migration needed since existing tables are not altered.

---

## 7. API Endpoint Specifications

### Library Endpoints

| Method | Path | Request | Response | Notes |
|--------|------|---------|----------|-------|
| GET | `/api/workspace/library` | -- | `LibraryFile[]` | Global files only |
| GET | `/api/workspace/library/conversation/{id}` | -- | `LibraryFile[]` | Global + per-chat |
| POST | `/api/workspace/library/upload` | Multipart form: `file`, `conversation_id?`, `display_name?`, `tags?` | `LibraryFile` | Max 10MB |
| POST | `/api/workspace/library/upload-text` | JSON: `{filename, content, conversation_id?, display_name?, tags?}` | `LibraryFile` | For paste |
| GET | `/api/workspace/library/{file_id}/content` | -- | `{content: str}` | File content |
| PATCH | `/api/workspace/library/{file_id}` | JSON: `{display_name?, tags?}` | `LibraryFile` | Metadata update |
| DELETE | `/api/workspace/library/{file_id}` | -- | `{success: true}` | Deletes file + disk |
| POST | `/api/workspace/library/{file_id}/toggle/{conversation_id}` | -- | `LibraryFile` | Toggle context |
| GET | `/api/workspace/library/active/{conversation_id}` | -- | `LibraryFile[]` | Active files |

### Repository Endpoints

| Method | Path | Request | Response | Notes |
|--------|------|---------|----------|-------|
| POST | `/api/workspace/repos/connect` | JSON: `{repo_url, token, branch?, conversation_id?}` | `ConnectedRepo` | Clones repo |
| DELETE | `/api/workspace/repos/{repo_id}` | Query: `delete_local=bool` | `{success: true}` | Disconnects |
| GET | `/api/workspace/repos` | Query: `conversation_id?` | `ConnectedRepo[]` | List repos |
| GET | `/api/workspace/repos/{repo_id}/tree` | -- | `RepoTreeEntry[]` | File tree |
| GET | `/api/workspace/repos/{repo_id}/file` | Query: `path=str` | `{content, path}` | Read file |
| POST | `/api/workspace/repos/{repo_id}/sync` | -- | `ConnectedRepo` | Git pull |

---

## 8. Component Specifications

### WorkspaceLibrary

- **Location:** `ui/src/components/workspace/WorkspaceLibrary.tsx`
- **Width:** Fixed 320px (`w-80`) right panel
- **Sections:** Three collapsible sections with counts in headers
- **Empty state:** "No files yet. Upload a file or paste text to get started."
- **File row height:** 44px with padding
- **Toggle animation:** Smooth 150ms color transition on the toggle switch
- **Loading state:** Skeleton rows (3 gray bars) while fetching

### FileUploadModal

- **Location:** `ui/src/components/workspace/FileUploadModal.tsx`
- **Max width:** 448px (`max-w-md`)
- **Overlay:** `bg-black/50` backdrop with `animate-fade-in`
- **Drag state:** Track `dragenter`/`dragleave`/`drop` events on the drop zone
- **Validation:** Client-side extension check before upload, file size check before upload
- **Error display:** Red text below form fields using `text-destructive`

### FilePreview

- **Location:** `ui/src/components/workspace/FilePreview.tsx`
- **Rendering:** Modal overlay, max width 640px, max height 80vh with scroll
- **Code files:** `<pre>` with `bg-muted rounded-lg p-4 overflow-x-auto font-mono text-sm`
- **Markdown files:** Rendered HTML with `chat-prose` class (same as chat messages)
- **Loading:** Centered spinner while content loads

### RepoConnector

- **Location:** `ui/src/components/workspace/RepoConnector.tsx`
- **Max width:** 480px modal
- **URL validation:** Check on blur, show error if not matching GitHub HTTPS pattern
- **Token field:** `type="password"`, never log or display
- **Clone progress:** Disable form and show "Cloning repository..." with spinner

### RepoBrowser

- **Location:** `ui/src/components/workspace/RepoBrowser.tsx`
- **Tree indent:** 16px per level (`pl-4` per depth)
- **Max depth:** 3 levels shown by default, expand on click
- **File count limit:** Show "... and N more files" if directory has > 50 entries

### ContextBudgetBar (updated)

- **Segments:** Messages (primary), Library (chart-4), Repos (chart-2), Available (muted)
- **Tooltips:** Show token count and item count on hover
- **Zero segments:** Hidden (not rendered if tokens = 0)
- **Legend:** Horizontal flex-wrap row below the bar

---

## 9. Security Considerations

### File Uploads
- **Size limit:** 10MB enforced server-side (check `len(content)` after `await file.read()`)
- **Extension allowlist:** Only text-based file extensions permitted (see `ALLOWED_EXTENSIONS`)
- **Path traversal:** File names sanitized with UUID prefix; never use user-provided filename as direct path
- **Content injection:** Library files injected as plaintext context, never executed

### Token Encryption
- **Fernet encryption:** Symmetric encryption using machine-derived key (MAC address hash)
- **File permissions:** `.tokens` file set to `0o600` (owner read/write only)
- **Never logged:** Token plaintext never appears in logs; authenticated URLs never logged
- **DB stores references only:** The `access_token_ref` column contains a UUID reference, not the token itself

### Repository Access
- **Clone isolation:** Each repo cloned to its own directory under `~/.autoforge/workspace/repos/`
- **Path traversal protection:** In `get_repo_file()`, resolve the path and verify it stays within the repo directory using `resolved.relative_to(repo_dir)`
- **Git operations:** Use `subprocess.run()` with `capture_output=True` and `timeout=120` to prevent hanging
- **Error sanitization:** Strip token substrings from git error messages before returning to client

### Workspace Chat Session
- **Repo paths:** Connected repo paths added to Claude's allowed filesystem, NOT to the entire system
- **Bash security:** The workspace chat session's Bash security hook (from Phase 1) remains active
- **Read-only by default:** Connected repos start as read-accessible; write access requires explicit `Edit()` permission in the settings JSON

---

## 10. Testing Checklist

### Backend Unit Tests

```python
# test_workspace_library.py

def test_upload_small_file():
    """Files <= 100KB should have content stored in SQLite."""
    ...

def test_upload_large_file():
    """Files > 100KB should be stored on disk with file_path set."""
    ...

def test_upload_rejects_oversized_file():
    """Files > 10MB should be rejected with 413 status."""
    ...

def test_upload_rejects_disallowed_extension():
    """Binary files (.exe, .dll, .bin) should be rejected."""
    ...

def test_toggle_global_file():
    """Toggling a global file creates/updates an activation record."""
    ...

def test_toggle_perchat_file():
    """Toggling a per-chat file updates active_in_context directly."""
    ...

def test_active_files_context_format():
    """Active files should produce correctly formatted context string."""
    ...

def test_delete_file_removes_disk_copy():
    """Deleting a large file should also remove the disk copy."""
    ...

def test_file_extension_validation():
    """All ALLOWED_EXTENSIONS should pass, others should fail."""
    ...
```

```python
# test_workspace_token_encryption.py

def test_encrypt_decrypt_roundtrip():
    """Encrypting then decrypting should return the original token."""
    ...

def test_store_and_retrieve_token():
    """Storing a token and retrieving it should work correctly."""
    ...

def test_delete_token():
    """Deleting a token should make it unretrievable."""
    ...

def test_decrypt_wrong_machine():
    """Decrypting a token from a different machine should raise ValueError."""
    # This is hard to test directly -- mock uuid.getnode() to return different values
    ...
```

```python
# test_workspace_repos.py

def test_validate_repo_url_valid():
    """Valid GitHub HTTPS URLs should pass."""
    ...

def test_validate_repo_url_invalid():
    """Non-GitHub URLs, SSH URLs, etc. should fail."""
    ...

def test_extract_repo_name():
    """Should correctly extract 'owner/repo' from URLs."""
    ...

def test_repo_file_path_traversal():
    """Requesting '../../../etc/passwd' should be rejected."""
    ...

def test_clone_sanitizes_error_messages():
    """Git error messages should not contain the access token."""
    ...
```

### Frontend Manual Test Plan

1. **Upload Flow:** Upload a .md file < 100KB, verify it appears in Global Files
2. **Upload Large:** Upload a .py file > 100KB, verify it appears (content on disk)
3. **Paste Text:** Use "Paste Text" mode, enter content, verify file created
4. **Toggle Context:** Toggle a file active, send a message, verify file content appears in Claude's context
5. **Context Budget:** Verify budget bar shows Library segment when files are active
6. **Delete File:** Delete a file, verify it disappears from list and disk
7. **Per-Chat Scope:** Upload a file with "This Chat" scope, verify it only appears for that conversation
8. **GitHub Connect:** Connect a public repo (with PAT), verify clone completes
9. **Repo Browser:** Browse the connected repo's file tree, open a file
10. **Repo Sync:** Click sync, verify last_synced_at updates
11. **Disconnect Repo:** Disconnect, verify repo removed from list
12. **Library Panel Toggle:** Toggle the library panel open/closed via header button
13. **Empty States:** Verify graceful empty states for no files, no repos
14. **Error Handling:** Upload a .exe file, verify rejection error displayed

### Integration Tests

```bash
# Run from project root
cd ui && npm run build     # Verify TypeScript compiles
cd ui && npm run lint      # Verify no lint errors
ruff check .               # Python lint
mypy server/services/workspace_library.py server/services/workspace_token_encryption.py server/services/workspace_repos.py
```

---

## 11. Important Reminders

### Patterns to Follow

1. **Database access pattern:** Follow `assistant_database.py` -- engine cache with thread-safe locking, `get_session()` factory, try/finally for session cleanup.

2. **Router pattern:** Follow `assistant_chat.py` -- router with prefix, Pydantic models for responses, HTTPException for errors, inline imports for services (lazy loading).

3. **Frontend component pattern:** Follow existing workspace components from Phases 1-2 -- functional components with hooks, TanStack Query for data fetching, Tailwind utility classes for styling.

4. **Token estimation:** Use `len(text) // 3` consistently (same formula as `workspace_database.py`).

5. **Theme-agnostic styling:** Use ONLY Tailwind token classes (`bg-card`, `text-foreground`, `border-border`, `bg-muted`, `text-muted-foreground`, `bg-primary`, `text-primary-foreground`). NEVER hardcode hex colors or use neobrutalism-specific classes. The UI has 6 themes; all must work.

6. **Error handling:** Always return structured error responses via `HTTPException`. Never expose internal paths or stack traces to the client.

7. **File operations:** Always use `Path` objects, never string concatenation for paths. Always validate that resolved paths stay within expected directories.

### Things NOT to Do

1. **Do NOT modify** the existing workspace conversation/message/category/summary tables or endpoints.
2. **Do NOT add** `cryptography` inline -- add it to `requirements.txt` and import normally.
3. **Do NOT store** plaintext tokens anywhere -- not in SQLite, not in logs, not in error messages.
4. **Do NOT use** `os.system()` for git operations -- use `subprocess.run()` with explicit argument lists.
5. **Do NOT create** a separate SQLite database for the library. The library tables go in the existing `workspace.db`.
6. **Do NOT use** any emoji in code, comments, or UI text.
7. **Do NOT use** `git clone` with the token embedded in a shell command string. Build the authenticated URL in Python and pass it as an argument to `subprocess.run()`.

### Build Order

Implement in this order:

1. **Database models** -- Add new SQLAlchemy models to `workspace_database.py`
2. **Token encryption** -- Create `workspace_token_encryption.py` (standalone, no DB deps)
3. **Library service** -- Create `workspace_library.py` (depends on DB models)
4. **Repos service** -- Create `workspace_repos.py` (depends on DB models + token encryption)
5. **Router endpoints** -- Add all new endpoints to `workspace.py`
6. **TypeScript types** -- Add `LibraryFile`, `ConnectedRepo`, etc. to `types.ts`
7. **API functions** -- Add fetch functions to `api.ts`
8. **Query hooks** -- Create `useWorkspaceLibrary.ts` (and optionally `useWorkspaceRepos.ts`)
9. **WorkspaceLibrary panel** -- Build the right panel component
10. **FileUploadModal** -- Build the upload/paste modal
11. **FilePreview** -- Build the preview modal
12. **RepoConnector** -- Build the connect modal
13. **RepoBrowser** -- Build the tree browser
14. **WorkspacePage update** -- Add three-panel layout with library toggle
15. **ContextBudgetBar update** -- Add Library and Repos segments
16. **Chat session update** -- Inject library context into messages
17. **Verify** -- Run `npm run build`, `npm run lint`, `ruff check .`, `mypy`
