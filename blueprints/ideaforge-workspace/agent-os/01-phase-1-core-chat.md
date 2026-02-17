# Phase 1: Core Chat Infrastructure — Agent OS Blueprint

## Standards Reference
> This phase follows the standards defined in `00-standards-layer.md`. Read that document first before implementing.

---

## PRODUCT LAYER

### Vision

A full-page workspace chat at `/#/workspace` with full Claude agent capabilities (Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch), multi-conversation management with a sidebar, and a real-time context budget meter. This is a standalone coding workspace where users interact with Claude as a general-purpose coding assistant that can read AND modify files anywhere on their system.

The workspace is **project-agnostic** (not tied to any specific AutoForge project). Its database lives at `~/.autoforge/workspace.db` and conversations are global. The agent has `acceptEdits` permission mode and the Bash security hook applied.

The workspace leverages Claude's **1M token context window** (via the `context-1m-2025-08-07` beta flag), enabling long, rich conversations without aggressive truncation.

### Target Users

Developers using AutoForge who need a general-purpose coding workspace separate from project-specific agent sessions. The workspace provides a persistent, multi-conversation environment for ad-hoc coding tasks, debugging, exploration, and refactoring that does not belong to any single AutoForge project.

### Core Use Cases

1. Start new coding conversations with full Read/Write/Edit/Bash/Glob/Grep/WebFetch/WebSearch tools
2. Manage multiple concurrent conversations via sidebar
3. Resume previous conversations with full history
4. Monitor context budget usage in real-time via visual budget bar
5. Navigate between workspace and main AutoForge app

### Phase Context

- Phase 1: **Core Chat Infrastructure** (this document)
- Phase 2: Context Management & Organization
- Phase 3: File Library & GitHub Integration
- Phase 4: Advanced Features (Fork, Inject, Export, Keyboard Shortcuts)

---

## SPECS LAYER

### Overview

Phase 1 creates the foundational workspace chat system: a Python backend with database models, chat session management, and REST/WebSocket endpoints, paired with a React frontend consisting of a full-page layout, conversation sidebar, chat interface, and context budget meter.

**Files to create (10):**

| # | File | Purpose |
|---|------|---------|
| 1 | `server/services/workspace_database.py` | SQLAlchemy models and CRUD for global workspace DB |
| 2 | `server/services/workspace_chat_session.py` | Chat session management with full Claude agent tools |
| 3 | `server/routers/workspace.py` | REST and WebSocket endpoints |
| 4 | `ui/src/pages/WorkspacePage.tsx` | Full-page workspace layout |
| 5 | `ui/src/components/workspace/WorkspaceSidebar.tsx` | Conversation list sidebar |
| 6 | `ui/src/components/workspace/WorkspaceChat.tsx` | Main chat area with message display |
| 7 | `ui/src/components/workspace/WorkspaceChatHeader.tsx` | Editable title, category, connection status |
| 8 | `ui/src/components/workspace/ContextBudgetBar.tsx` | Visual token budget meter |
| 9 | `ui/src/hooks/useWorkspaceChat.ts` | WebSocket hook with token tracking |
| 10 | `ui/src/hooks/useWorkspaceConversations.ts` | React Query hooks for conversation CRUD |

**Files to modify (7):**

| # | File | Change |
|---|------|--------|
| 1 | `ui/src/lib/routes.ts` | Add `isWorkspaceRoute()` |
| 2 | `ui/src/main.tsx` | Add workspace route check |
| 3 | `ui/src/lib/types.ts` | Add workspace types |
| 4 | `ui/src/lib/api.ts` | Add workspace API functions |
| 5 | `server/routers/__init__.py` | Add `workspace_router` |
| 6 | `server/main.py` | Add router registration + shutdown cleanup |
| 7 | `ui/src/App.tsx` | Add workspace nav button |

### Project Context

**Tech Stack:**
- Backend: Python 3.11+, FastAPI, SQLAlchemy, SQLite, Claude Agent SDK (`claude_agent_sdk`)
- Frontend: React 19, TypeScript, Vite 7, TanStack Query, Tailwind CSS v4, Radix UI
- Design: Theme-agnostic. Six themes exist. Always use semantic tokens: `bg-background`, `text-foreground`, `bg-card`, `border-border`, `text-muted-foreground`, `bg-primary`, `text-primary-foreground`, `bg-secondary`, `bg-muted`, `text-destructive`, `bg-accent`

**Critical Architecture Rules:**
1. NO React Router. Custom hash-based routing via `ui/src/lib/routes.ts` and `ui/src/main.tsx`.
2. The workspace database is GLOBAL at `~/.autoforge/workspace.db`, NOT per-project. Database functions do NOT take a `project_dir` parameter.
3. Reuse the existing `ChatMessage` component (`ui/src/components/ChatMessage.tsx`) for rendering messages. Do NOT rebuild it.
4. Reuse existing type patterns from `ui/src/lib/types.ts`. Add new types in the same file following the same section pattern.
5. The `fetchJSON` helper in `ui/src/lib/api.ts` already handles the `/api` prefix. Pass paths like `/workspace/conversations`.
6. Router registration is a 3-file pattern: router file, `__init__.py`, and `server/main.py`.
7. Server shutdown cleanup must be added to the lifespan in `server/main.py`.

**Key Existing Files to Reference (read but do NOT modify their core logic):**
- `server/services/assistant_chat_session.py` — fork this for workspace session
- `server/services/assistant_database.py` — fork this for workspace database
- `server/routers/assistant_chat.py` — fork this for workspace router
- `ui/src/hooks/useAssistantChat.ts` — fork this for workspace chat hook
- `ui/src/components/AssistantChat.tsx` — reference for chat UI patterns
- `ui/src/components/ChatMessage.tsx` — REUSE this component directly (import it)
- `security.py` — import `bash_security_hook` from here
- `server/services/chat_constants.py` — import `ROOT_DIR` from here

---

### Files to Create

#### 1. `server/services/workspace_database.py`

**Purpose:** SQLAlchemy models and CRUD functions for the global workspace database at `~/.autoforge/workspace.db`.

**Key Differences from `assistant_database.py`:**
- Database path is `~/.autoforge/workspace.db` (global), not per-project
- No `project_dir` parameter on any function
- `WorkspaceConversation` has `category` and `working_directory` columns
- `WorkspaceMessage` has `token_estimate` column
- Functions for updating conversation title and category
- Function to get total estimated tokens for a conversation

**Imports:**
```python
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, create_engine, func
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker
```

**Models:**

```python
class Base(DeclarativeBase):
    """SQLAlchemy 2.0 style declarative base."""
    pass
```

**`WorkspaceConversation` table — `workspace_conversations`:**

| Column | Type | Notes |
|---|---|---|
| `id` | `Integer`, primary_key, index | Auto-increment |
| `title` | `String(200)`, nullable | Auto-set from first user message (first 50 chars + "...") |
| `category` | `String(50)`, nullable, default `"general"` | User-settable label: "general", "debugging", "refactoring", "feature", "exploration" |
| `working_directory` | `Text`, nullable | The cwd the agent session operates in |
| `created_at` | `DateTime`, default `_utc_now` | |
| `updated_at` | `DateTime`, default `_utc_now`, onupdate `_utc_now` | |

Relationship: `messages = relationship("WorkspaceMessage", back_populates="conversation", cascade="all, delete-orphan")`

**`WorkspaceMessage` table — `workspace_messages`:**

| Column | Type | Notes |
|---|---|---|
| `id` | `Integer`, primary_key, index | Auto-increment |
| `conversation_id` | `Integer`, ForeignKey `workspace_conversations.id`, index | |
| `role` | `String(20)`, nullable=False | "user", "assistant", "system" |
| `content` | `Text`, nullable=False | |
| `token_estimate` | `Integer`, default 0 | Rough character/4 estimate |
| `timestamp` | `DateTime`, default `_utc_now` | |

Relationship: `conversation = relationship("WorkspaceConversation", back_populates="messages")`

**Engine Caching:**

Same double-checked locking pattern as `assistant_database.py`, but the cache key is the global db path string. Use one module-level `_engine_cache` dict and `_cache_lock` threading lock.

```python
_engine_cache: dict[str, Engine] = {}
_cache_lock = threading.Lock()

def _utc_now() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)

def _get_db_path() -> Path:
    """Get the global workspace database path: ~/.autoforge/workspace.db"""
    db_dir = Path.home() / ".autoforge"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "workspace.db"

def get_engine() -> Engine:
    """Get or create the SQLAlchemy engine for the workspace database."""
    db_path = _get_db_path()
    cache_key = db_path.as_posix()

    if cache_key in _engine_cache:
        return _engine_cache[cache_key]

    with _cache_lock:
        if cache_key not in _engine_cache:
            db_url = f"sqlite:///{db_path.as_posix()}"
            engine = create_engine(
                db_url,
                echo=False,
                connect_args={
                    "check_same_thread": False,
                    "timeout": 30,
                }
            )
            Base.metadata.create_all(engine)
            _engine_cache[cache_key] = engine

    return _engine_cache[cache_key]

def get_db_session():
    """Get a new database session."""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()
```

**CRUD Functions (all module-level, no `project_dir` parameter):**

```python
def create_conversation(
    title: Optional[str] = None,
    category: str = "general",
    working_directory: Optional[str] = None,
) -> WorkspaceConversation:
    """Create a new workspace conversation."""
    # Pattern: get session, create, commit, refresh, return, finally close

def get_conversations() -> list[dict]:
    """Get all conversations with message counts, ordered by updated_at desc."""
    # Same subquery pattern as assistant_database.get_conversations
    # Return dicts with: id, title, category, working_directory, created_at, updated_at, message_count

def get_conversation(conversation_id: int) -> Optional[dict]:
    """Get a conversation with all its messages."""
    # Return dict with: id, title, category, working_directory, created_at, updated_at, messages[]
    # Each message: id, role, content, token_estimate, timestamp

def delete_conversation(conversation_id: int) -> bool:
    """Delete a conversation and all its messages. Returns True if found and deleted."""

def update_conversation(
    conversation_id: int,
    title: Optional[str] = None,
    category: Optional[str] = None,
) -> Optional[dict]:
    """Update conversation title and/or category. Returns updated conversation dict or None."""
    # Only update fields that are not None
    # Return dict with: id, title, category, working_directory, created_at, updated_at

def add_message(
    conversation_id: int,
    role: str,
    content: str,
    token_estimate: int = 0,
) -> Optional[dict]:
    """Add a message to a conversation. Auto-generates title from first user message."""
    # Same pattern as assistant_database.add_message
    # Auto-title: if conversation.title is None and role == "user", set title = content[:50] + "..."
    # Return dict with: id, role, content, token_estimate, timestamp

def get_messages(conversation_id: int) -> list[dict]:
    """Get all messages for a conversation, ordered by timestamp asc."""
    # Return list of dicts: id, role, content, token_estimate, timestamp

def get_conversation_token_total(conversation_id: int) -> int:
    """Get the sum of token_estimate for all messages in a conversation."""
    # Use func.coalesce(func.sum(WorkspaceMessage.token_estimate), 0)

def estimate_tokens(text: str) -> int:
    """Estimate token count for a text string. Uses chars/4 heuristic."""
    return max(1, len(text) // 4)
```

---

#### 2. `server/services/workspace_chat_session.py`

**Purpose:** Manages workspace chat sessions with full read/write Claude agent capabilities. Forked from `assistant_chat_session.py` with key differences.

**Key Differences from `assistant_chat_session.py`:**
- Full tools: Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch (NOT just read-only)
- `acceptEdits` permission mode (NOT `bypassPermissions`)
- Bash security hook applied via `hooks` parameter
- NO MCP servers (no feature MCP — workspace is project-agnostic)
- 100-message context loading with NO truncation (not 35 messages / 500 chars)
- Token estimation tracked per-message
- Global database (workspace_database), not per-project
- Session registry keyed by `session_id` string (NOT project_name)
- Working directory configurable per-conversation (defaults to home directory)
- System prompt is workspace-focused, not project-focused

**Imports:**
```python
import json
import logging
import os
import shutil
import threading
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, Optional

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
from claude_agent_sdk.types import HookMatcher
from dotenv import load_dotenv

from security import bash_security_hook
from .workspace_database import (
    add_message,
    create_conversation,
    estimate_tokens,
    get_conversation_token_total,
    get_messages,
)
from .chat_constants import ROOT_DIR
```

**Constants:**
```python
# Full set of built-in tools for the workspace agent
WORKSPACE_BUILTIN_TOOLS = [
    "Read",
    "Write",
    "Edit",
    "Bash",
    "Glob",
    "Grep",
    "WebFetch",
    "WebSearch",
]

# Maximum messages to load from history when resuming a conversation
MAX_HISTORY_MESSAGES = 100

# Claude's context window with 1M beta enabled (context-1m-2025-08-07)
# This is the ENTIRE POINT of the workspace — must match the beta flag below.
CONTEXT_WINDOW_TOKENS = 1_000_000
```

**System Prompt Function:**
```python
def get_workspace_system_prompt(working_directory: str) -> str:
    """Generate the system prompt for the workspace agent."""
    return f"""You are an expert coding assistant in the IdeaForge Workspace.

You have full access to the filesystem and can read, write, edit files, and run bash commands.
Your current working directory is: {working_directory}

## Capabilities

- **Read**: Read file contents
- **Write**: Create or overwrite files
- **Edit**: Make targeted edits to existing files
- **Bash**: Run shell commands (subject to security allowlist)
- **Glob**: Find files by pattern
- **Grep**: Search file contents with regex
- **WebFetch**: Fetch and analyze web content
- **WebSearch**: Search the web for information

## Guidelines

1. Be thorough and precise. Read files before editing them.
2. When modifying code, preserve existing style and conventions.
3. Explain your reasoning and approach before making changes.
4. After making changes, verify them (run linters, type checkers, tests as appropriate).
5. If a bash command might be destructive, explain what it does first.
6. Use absolute file paths when possible.
7. When searching, use Glob and Grep rather than bash find/grep."""
```

**Class: `WorkspaceChatSession`:**

```python
class WorkspaceChatSession:
    """
    Manages a workspace conversation with full read/write Claude capabilities.

    Unlike the assistant (read-only), the workspace agent can modify files
    and run bash commands. Uses acceptEdits permission mode with bash
    security hooks for safe command execution.
    """

    def __init__(
        self,
        session_id: str,
        conversation_id: Optional[int] = None,
        working_directory: Optional[str] = None,
    ):
        self.session_id = session_id
        self.conversation_id = conversation_id
        self.working_directory = working_directory or str(Path.home())
        self.client: Optional[ClaudeSDKClient] = None
        self._client_entered: bool = False
        self.created_at = datetime.now()
        self._history_loaded: bool = False
```

**`start()` method — critical implementation details:**

The `start()` method must:

1. Create a conversation in the DB if `self.conversation_id is None`, yielding `{"type": "conversation_created", "conversation_id": ...}`.

2. Build the security settings JSON file. This is the KEY difference from assistant. The settings file must go to a temp-like location since there's no project directory. Use `~/.autoforge/.workspace_claude_settings.json`.

```python
# Build permissions list — full tools with acceptEdits
permissions_list = [
    "Read",
    "Write",
    "Edit",
    "Bash",
    "Glob",
    "Grep",
    "WebFetch",
    "WebSearch",
]

security_settings = {
    "sandbox": {"enabled": False},
    "permissions": {
        "defaultMode": "acceptEdits",
        "allow": permissions_list,
    },
}

settings_dir = Path.home() / ".autoforge"
settings_dir.mkdir(parents=True, exist_ok=True)
settings_file = settings_dir / ".workspace_claude_settings.json"
with open(settings_file, "w") as f:
    json.dump(security_settings, f, indent=2)
```

3. Write the system prompt to a `CLAUDE.md` file in the working directory. However, since the workspace is general-purpose and we might not want to clobber an existing CLAUDE.md, instead use the `system_prompt` parameter approach. Write it to `~/.autoforge/.workspace_system_prompt.md` and pass the content as the initial message context:

```python
# Write system prompt as CLAUDE.md in a scratch directory
workspace_scratch = Path.home() / ".autoforge" / ".workspace_scratch"
workspace_scratch.mkdir(parents=True, exist_ok=True)
claude_md_path = workspace_scratch / "CLAUDE.md"
system_prompt = get_workspace_system_prompt(self.working_directory)
with open(claude_md_path, "w", encoding="utf-8") as f:
    f.write(system_prompt)
```

4. Create the Claude SDK client with Bash security hook:

```python
from registry import DEFAULT_MODEL, get_effective_sdk_env
sdk_env = get_effective_sdk_env()
model = sdk_env.get("ANTHROPIC_DEFAULT_OPUS_MODEL") or os.getenv(
    "ANTHROPIC_DEFAULT_OPUS_MODEL", DEFAULT_MODEL
)

system_cli = shutil.which("claude")

# Bash security hook — same hook the coding agent uses
hooks = {
    "PreToolUse": [
        HookMatcher(matcher="Bash", hooks=[bash_security_hook])
    ]
}

is_alternative_api = sdk_env.get("CLAUDE_CODE_USE_VERTEX") or sdk_env.get("OLLAMA_BASE_URL") or sdk_env.get("ALTERNATIVE_API_BASE_URL")

self.client = ClaudeSDKClient(
    options=ClaudeAgentOptions(
        model=model,
        cli_path=system_cli,
        setting_sources=["project"],  # Reads CLAUDE.md from cwd
        allowed_tools=WORKSPACE_BUILTIN_TOOLS,
        permission_mode="acceptEdits",
        max_turns=100,
        cwd=str(workspace_scratch),  # Use scratch dir for CLAUDE.md
        settings=str(settings_file.resolve()),
        env=sdk_env,
        hooks=hooks,
        # CRITICAL: Enable 1M token context window — this is the whole
        # point of the workspace. Same beta used in client.py for coding agents.
        betas=[] if is_alternative_api else ["context-1m-2025-08-07"],
    )
)
await self.client.__aenter__()
self._client_entered = True
```

5. For new conversations, send a greeting and store it. For resumed conversations, set `_history_loaded = False` so the first `send_message()` call loads history.

**`send_message()` method — context loading:**

The critical difference from assistant: load up to 100 messages with NO truncation.

```python
async def send_message(self, user_message: str) -> AsyncGenerator[dict, None]:
    if not self.client:
        yield {"type": "error", "content": "Session not initialized. Call start() first."}
        return

    if self.conversation_id is None:
        yield {"type": "error", "content": "No conversation ID set."}
        return

    # Estimate tokens and store user message
    user_tokens = estimate_tokens(user_message)
    add_message(self.conversation_id, "user", user_message, user_tokens)

    # For resumed conversations, include history context in first message
    message_to_send = user_message
    if not self._history_loaded:
        self._history_loaded = True
        history = get_messages(self.conversation_id)
        # Exclude the message we just added (last one)
        history = history[:-1] if history else []
        # Cap to last MAX_HISTORY_MESSAGES — NO per-message truncation
        history = history[-MAX_HISTORY_MESSAGES:] if len(history) > MAX_HISTORY_MESSAGES else history
        if history:
            history_lines = ["[Previous conversation history for context:]"]
            for msg in history:
                role = "User" if msg["role"] == "user" else "Assistant"
                content = msg["content"]
                # NO truncation — send full message content
                history_lines.append(f"{role}: {content}")
            history_lines.append("[End of history. Continue the conversation:]")
            history_lines.append(f"User: {user_message}")
            message_to_send = "\n".join(history_lines)
            logger.info(f"Loaded {len(history)} messages from conversation history")

    try:
        async for chunk in self._query_claude(message_to_send):
            yield chunk
        yield {"type": "response_done"}
    except Exception as e:
        logger.exception("Error during Claude query")
        yield {"type": "error", "content": f"Error: {str(e)}"}
```

**`_query_claude()` method:**

Same streaming pattern as `assistant_chat_session.py._query_claude()`, but:
- After accumulating `full_response`, compute `estimate_tokens(full_response)` and pass it to `add_message()`.
- Yield `{"type": "token_usage", "total_tokens": get_conversation_token_total(self.conversation_id), "context_window": CONTEXT_WINDOW_TOKENS}` after storing the response (before the caller yields `response_done`).
- No `ask_user` / question interception needed (no MCP tools).

```python
async def _query_claude(self, message: str) -> AsyncGenerator[dict, None]:
    if not self.client:
        return

    await self.client.query(message)

    full_response = ""

    async for msg in self.client.receive_response():
        msg_type = type(msg).__name__

        if msg_type == "AssistantMessage" and hasattr(msg, "content"):
            for block in msg.content:
                block_type = type(block).__name__

                if block_type == "TextBlock" and hasattr(block, "text"):
                    text = block.text
                    if text:
                        full_response += text
                        yield {"type": "text", "content": text}

                elif block_type == "ToolUseBlock" and hasattr(block, "name"):
                    tool_name = block.name
                    tool_input = getattr(block, "input", {})
                    yield {
                        "type": "tool_call",
                        "tool": tool_name,
                        "input": tool_input,
                    }

    # Store the complete response with token estimate
    if full_response and self.conversation_id is not None:
        response_tokens = estimate_tokens(full_response)
        add_message(self.conversation_id, "assistant", full_response, response_tokens)

        # Yield token usage update
        total = get_conversation_token_total(self.conversation_id)
        yield {
            "type": "token_usage",
            "total_tokens": total,
            "context_window": CONTEXT_WINDOW_TOKENS,
        }
```

**Session Registry:**

Keyed by `session_id` (string), not project_name. Use the same thread-safe pattern as assistant.

```python
_sessions: dict[str, WorkspaceChatSession] = {}
_sessions_lock = threading.Lock()

def get_session(session_id: str) -> Optional[WorkspaceChatSession]:
    with _sessions_lock:
        return _sessions.get(session_id)

async def create_session(
    session_id: str,
    conversation_id: Optional[int] = None,
    working_directory: Optional[str] = None,
) -> WorkspaceChatSession:
    """Create a new session, closing any existing one with the same ID."""
    old_session: Optional[WorkspaceChatSession] = None
    with _sessions_lock:
        old_session = _sessions.pop(session_id, None)
        session = WorkspaceChatSession(session_id, conversation_id, working_directory)
        _sessions[session_id] = session
    if old_session:
        try:
            await old_session.close()
        except Exception as e:
            logger.warning(f"Error closing old session {session_id}: {e}")
    return session

async def remove_session(session_id: str) -> None:
    session: Optional[WorkspaceChatSession] = None
    with _sessions_lock:
        session = _sessions.pop(session_id, None)
    if session:
        try:
            await session.close()
        except Exception as e:
            logger.warning(f"Error closing session {session_id}: {e}")

async def cleanup_all_workspace_sessions() -> None:
    """Close all active workspace sessions. Called on server shutdown."""
    sessions_to_close: list[WorkspaceChatSession] = []
    with _sessions_lock:
        sessions_to_close = list(_sessions.values())
        _sessions.clear()
    for session in sessions_to_close:
        try:
            await session.close()
        except Exception as e:
            logger.warning(f"Error closing workspace session {session.session_id}: {e}")
```

---

#### 3. `server/routers/workspace.py`

**Purpose:** REST and WebSocket endpoints for the workspace chat. Follows the same patterns as `server/routers/assistant_chat.py`.

**Router setup:**
```python
router = APIRouter(prefix="/api/workspace", tags=["workspace"])
```

**Pydantic Models:**

```python
class WorkspaceConversationSummary(BaseModel):
    id: int
    title: Optional[str]
    category: str
    working_directory: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    message_count: int

class WorkspaceMessageModel(BaseModel):
    id: int
    role: str
    content: str
    token_estimate: int
    timestamp: Optional[str]

class WorkspaceConversationDetail(BaseModel):
    id: int
    title: Optional[str]
    category: str
    working_directory: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    messages: list[WorkspaceMessageModel]

class ConversationCreateRequest(BaseModel):
    category: str = "general"
    working_directory: Optional[str] = None

class ConversationUpdateRequest(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
```

**REST Endpoints:**

| Method | Path | Handler | Description |
|---|---|---|---|
| `GET` | `/conversations` | `list_workspace_conversations` | List all conversations |
| `POST` | `/conversations` | `create_workspace_conversation` | Create conversation (body: `ConversationCreateRequest`) |
| `GET` | `/conversations/{conversation_id}` | `get_workspace_conversation` | Get conversation with messages |
| `PATCH` | `/conversations/{conversation_id}` | `update_workspace_conversation` | Update title/category |
| `DELETE` | `/conversations/{conversation_id}` | `delete_workspace_conversation` | Delete conversation |
| `GET` | `/conversations/{conversation_id}/tokens` | `get_conversation_tokens` | Get total token estimate |

Implementation notes:
- No project name validation needed (workspace is global).
- Import CRUD functions from `workspace_database`.
- Return appropriate HTTP 404 if conversation not found.

**Token endpoint implementation:**
```python
@router.get("/conversations/{conversation_id}/tokens")
async def get_conversation_tokens(conversation_id: int):
    """Get the estimated token usage for a conversation."""
    from ..services.workspace_database import get_conversation_token_total
    from ..services.workspace_chat_session import CONTEXT_WINDOW_TOKENS
    total = get_conversation_token_total(conversation_id)
    return {
        "total_tokens": total,
        "context_window": CONTEXT_WINDOW_TOKENS,
        "usage_percent": round(total / CONTEXT_WINDOW_TOKENS * 100, 1) if CONTEXT_WINDOW_TOKENS > 0 else 0,
    }
```

**WebSocket Endpoint:**

```python
@router.websocket("/ws")
async def workspace_chat_websocket(websocket: WebSocket):
```

Protocol is identical to the assistant chat WebSocket, with these additions:

**Client -> Server additional message types:**
```json
{"type": "start", "conversation_id": 123, "working_directory": "/path/to/dir"}
```
The `working_directory` field is optional and only used when starting a new conversation (no `conversation_id`). If resuming, the working directory is loaded from the database.

**Server -> Client additional message types:**
```json
{"type": "token_usage", "total_tokens": 5432, "context_window": 1000000}
```
Sent after each assistant response completes.

**WebSocket handler implementation:**

The handler generates a `session_id` from the WebSocket connection (use `str(id(websocket))` or a UUID). The main loop handles the same message types as assistant_chat: `ping`, `start`, `message`, `answer`.

Key differences in the `start` handler:
```python
elif msg_type == "start":
    conversation_id = message.get("conversation_id")
    working_directory = message.get("working_directory")

    # If resuming, look up working_directory from DB
    if conversation_id and not working_directory:
        from ..services.workspace_database import get_conversation as get_conv
        conv = get_conv(conversation_id)
        if conv:
            working_directory = conv.get("working_directory")

    session_id = f"ws-{id(websocket)}"
    session = await ws_create_session(
        session_id,
        conversation_id=conversation_id,
        working_directory=working_directory,
    )

    async for chunk in session.start():
        await websocket.send_json(chunk)
```

In the `finally` block, clean up the session:
```python
finally:
    if session_id:
        await ws_remove_session(session_id)
```

This is different from assistant_chat which keeps sessions alive after disconnect. The workspace closes sessions on disconnect because each WebSocket gets its own Claude client instance.

---

#### 4. `ui/src/pages/WorkspacePage.tsx`

**Purpose:** Full-page workspace layout with sidebar and chat area.

**File path:** `ui/src/pages/WorkspacePage.tsx`

**Layout Structure:**
```
+---------------------------------------------------------------+
|  Full viewport height, flex row                                |
|  +------------------+----------------------------------------+|
|  | WorkspaceSidebar |  WorkspaceChat                          ||
|  | (280px, fixed)   |  (flex-1, fills remaining)              ||
|  |                  |  +------------------------------------+ ||
|  | [New Chat btn]   |  | WorkspaceChatHeader               | ||
|  | [Search input]   |  | (title, category, connection)     | ||
|  | [Conversation    |  +------------------------------------+ ||
|  |  list...]        |  | ContextBudgetBar (STICKY)         | ||
|  |                  |  +------------------------------------+ ||
|  |                  |  | Messages area (flex-1, scrolls)   | ||
|  |                  |  |                                    | ||
|  |                  |  +------------------------------------+ ||
|  |                  |  | Input area (fixed bottom)         | ||
|  +------------------+----------------------------------------+|
+---------------------------------------------------------------+
```

**Component Implementation:**

```tsx
import { useState, useCallback } from 'react'
import { WorkspaceSidebar } from '../components/workspace/WorkspaceSidebar'
import { WorkspaceChat } from '../components/workspace/WorkspaceChat'
import { ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'

export function WorkspacePage() {
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  const handleNewChat = useCallback(() => {
    setActiveConversationId(null)
  }, [])

  const handleSelectConversation = useCallback((id: number) => {
    setActiveConversationId(id)
  }, [])

  const handleConversationCreated = useCallback((id: number) => {
    setActiveConversationId(id)
  }, [])

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Top bar with back-to-projects link */}
      <div className="flex items-center h-10 px-3 border-b border-border bg-card shrink-0">
        <Button
          variant="ghost"
          size="sm"
          className="gap-1.5 text-muted-foreground hover:text-foreground"
          onClick={() => { window.location.hash = '' }}
        >
          <ArrowLeft size={14} />
          <span className="text-xs">Back to Projects</span>
        </Button>
        <span className="ml-3 text-sm font-semibold text-foreground">
          IdeaForge Workspace
        </span>
      </div>

      {/* Main content area */}
      <div className="flex flex-1 overflow-hidden">
        <WorkspaceSidebar
          activeConversationId={activeConversationId}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
          onNewChat={handleNewChat}
          onSelectConversation={handleSelectConversation}
        />
        <WorkspaceChat
          conversationId={activeConversationId}
          onConversationCreated={handleConversationCreated}
        />
      </div>
    </div>
  )
}
```

**Styling notes:**
- Use `h-screen` for full viewport height
- Use `bg-background` on root, `bg-card` on top bar
- Use `border-border` for all borders
- Use `text-foreground` and `text-muted-foreground` for text
- No hardcoded colors — everything via semantic tokens

---

#### 5. `ui/src/components/workspace/WorkspaceSidebar.tsx`

**Purpose:** Conversation list sidebar with search, new chat button, and conversation items.

**Props:**
```tsx
interface WorkspaceSidebarProps {
  activeConversationId: number | null
  collapsed: boolean
  onToggleCollapse: () => void
  onNewChat: () => void
  onSelectConversation: (id: number) => void
}
```

**Structure:**
```
+------------------+
| [<>] IdeaForge   |  <- collapse toggle + title
+------------------+
| [+ New Chat]     |  <- primary button, full width
+------------------+
| [Search...]      |  <- filter input
+------------------+
| Today             |  <- date group header
| > Conversation 1  |  <- active state highlighted
| > Conversation 2  |
| Yesterday         |
| > Conversation 3  |
| Older             |
| > Conversation 4  |
+------------------+
```

**Implementation details:**
- Use `useWorkspaceConversations` hook (defined below) to fetch conversation list
- Group conversations by date: "Today", "Yesterday", "This Week", "Older" (compare `updated_at` to current date)
- Search filters by title (case-insensitive substring match on client side)
- Each conversation item shows: title (or "Untitled" if null), category badge, relative time ("2m ago", "1h ago")
- Active conversation has `bg-accent` background
- Right-click or hover shows delete button (small trash icon)
- Collapsed state: hide sidebar with `w-0 overflow-hidden` transition, show expand button

**Width:** `w-72` (288px) when expanded, `w-0` when collapsed. Use `transition-all duration-200`.

**Delete confirmation:** Use `window.confirm()` for simplicity in Phase 1.

**Category badge colors:**
```tsx
const categoryColors: Record<string, string> = {
  general: 'bg-secondary text-secondary-foreground',
  debugging: 'bg-destructive/10 text-destructive',
  refactoring: 'bg-primary/10 text-primary',
  feature: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300',
  exploration: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300',
}
```

---

#### 6. `ui/src/components/workspace/WorkspaceChat.tsx`

**Purpose:** Main chat area component. Handles message display, input, and WebSocket communication.

**Props:**
```tsx
interface WorkspaceChatProps {
  conversationId: number | null
  onConversationCreated: (id: number) => void
}
```

**Implementation:**
- Use `useWorkspaceChat` hook for WebSocket communication
- Use the existing `ChatMessage` component from `@/components/ChatMessage` to render messages
- Load initial messages from REST API when `conversationId` changes (use `useQuery`)
- Same message merging pattern as `AssistantChat.tsx` (merge initial REST messages with live WebSocket messages using Map-based dedup by ID)

**Structure:**
```
+--------------------------------------------+
| WorkspaceChatHeader                         |
+--------------------------------------------+
| ContextBudgetBar (STICKY)                   |
+--------------------------------------------+
| Messages area (flex-1, overflow-y-auto)     |
|   ChatMessage (user)                        |
|   ChatMessage (assistant)                   |
|   ChatMessage (system / tool call)          |
|   ...                                       |
+--------------------------------------------+
| Loading indicator (conditional)             |
+--------------------------------------------+
| Input area                                  |
|   [Textarea] [Send button]                  |
|   "Enter to send, Shift+Enter for newline" |
+--------------------------------------------+
```

**Tool call display — workspace-specific tool descriptions:**

In the `onmessage` handler (inside `useWorkspaceChat`), the tool_call case needs richer descriptions for write tools:

```tsx
// In addition to the read tool descriptions from useAssistantChat:
case "Write": {
  const input = data.input as { file_path?: string }
  const path = input.file_path || ""
  const filename = path.split("/").pop() || path
  toolDescription = `Writing file: ${filename}`
  break
}
case "Edit": {
  const input = data.input as { file_path?: string }
  const path = input.file_path || ""
  const filename = path.split("/").pop() || path
  toolDescription = `Editing file: ${filename}`
  break
}
case "Bash": {
  const input = data.input as { command?: string }
  const cmd = input.command || ""
  // Show first 60 chars of command
  toolDescription = `Running: ${cmd.length > 60 ? cmd.slice(0, 60) + "..." : cmd}`
  break
}
```

**Empty state (no conversation selected):**
```tsx
<div className="flex-1 flex items-center justify-center text-muted-foreground">
  <div className="text-center">
    <MessageSquare size={48} className="mx-auto mb-4 opacity-30" />
    <p className="text-lg font-medium">IdeaForge Workspace</p>
    <p className="text-sm mt-1">Start a new chat or select a conversation</p>
  </div>
</div>
```

**Input area:** Same pattern as `AssistantChat.tsx` — `Textarea` + `Button`, Enter to send, Shift+Enter for newline. Import `isSubmitEnter` from `@/lib/keyboard`.

---

#### 7. `ui/src/components/workspace/WorkspaceChatHeader.tsx`

**Purpose:** Header bar for the active conversation showing editable title, category selector, and connection status.

**Props:**
```tsx
interface WorkspaceChatHeaderProps {
  conversationId: number | null
  title: string | null
  category: string
  connectionStatus: 'disconnected' | 'connecting' | 'connected' | 'error'
  onUpdateTitle: (title: string) => void
  onUpdateCategory: (category: string) => void
}
```

**Structure:**
```
+------------------------------------------------------------+
| [editable title]          [category dropdown] [status dot] |
+------------------------------------------------------------+
```

**Editable title:**
- Display as a text span normally
- On click, switch to an `<input>` element (inline edit)
- On blur or Enter, save the new title via PATCH endpoint
- If title is null, display "Untitled Conversation" in muted style
- Use a `useState` to track edit mode

**Category selector:**
- Use a `<select>` element styled as a badge/dropdown
- Options: "general", "debugging", "refactoring", "feature", "exploration"
- On change, immediately PATCH the conversation

**Connection status:**
- Same pattern as `AssistantChat.tsx`: `Wifi`/`WifiOff`/`Loader2` icons with text

---

#### 8. `ui/src/components/workspace/ContextBudgetBar.tsx`

**Purpose:** A sticky bar below the header that shows a visual token budget meter. This is the most distinctive UI element of the workspace.

**Props:**
```tsx
interface ContextBudgetBarProps {
  totalTokens: number
  contextWindow: number  // e.g. 1000000
}
```

**Visual Design:**

```
+------------------------------------------------------------+
| Context: 45,230 / 1,000,000 tokens      ██░░░░░░░░░░   5%  |
+------------------------------------------------------------+
```

When hovered, expand to show breakdown:
```
+------------------------------------------------------------+
| Context: 45,230 / 1,000,000 tokens      ██░░░░░░░░░░   5%  |
|                                                              |
| Conversation history: ~42,100 tokens                         |
| System prompt: ~3,130 tokens                                 |
+------------------------------------------------------------+
```

**Implementation:**

```tsx
import { useState } from 'react'

interface ContextBudgetBarProps {
  totalTokens: number
  contextWindow: number
}

export function ContextBudgetBar({ totalTokens, contextWindow }: ContextBudgetBarProps) {
  const [expanded, setExpanded] = useState(false)

  const percentage = contextWindow > 0
    ? Math.min(100, Math.round((totalTokens / contextWindow) * 100))
    : 0

  // Color thresholds
  let barColor = 'bg-primary'        // Normal: theme primary (blue in Twitter theme)
  let textColor = 'text-foreground'
  let pulseClass = ''

  if (percentage >= 95) {
    barColor = 'bg-destructive'
    textColor = 'text-destructive'
    pulseClass = 'animate-pulse'
  } else if (percentage >= 90) {
    barColor = 'bg-orange-500'
    textColor = 'text-orange-600 dark:text-orange-400'
  } else if (percentage >= 75) {
    barColor = 'bg-yellow-500'
    textColor = 'text-yellow-600 dark:text-yellow-400'
  }

  const formattedTotal = totalTokens.toLocaleString()
  const formattedWindow = contextWindow.toLocaleString()

  return (
    <div
      className="sticky top-0 z-10 border-b border-border bg-card/95 backdrop-blur-sm px-4 py-2 cursor-pointer select-none"
      onClick={() => setExpanded(!expanded)}
      title="Click to expand token breakdown"
    >
      {/* Main bar row */}
      <div className="flex items-center gap-3">
        <span className={`text-xs font-medium ${textColor} shrink-0`}>
          Context: {formattedTotal} / {formattedWindow} tokens
        </span>

        {/* Progress bar */}
        <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${barColor} ${pulseClass}`}
            style={{ width: `${percentage}%` }}
          />
        </div>

        <span className={`text-xs font-mono font-bold ${textColor} shrink-0 w-10 text-right`}>
          {percentage}%
        </span>
      </div>

      {/* Expanded breakdown */}
      {expanded && (
        <div className="mt-2 pt-2 border-t border-border text-xs text-muted-foreground space-y-1">
          <div className="flex justify-between">
            <span>Conversation history</span>
            <span className="font-mono">~{formattedTotal} tokens</span>
          </div>
          <div className="flex justify-between">
            <span>Remaining capacity</span>
            <span className="font-mono">~{(contextWindow - totalTokens).toLocaleString()} tokens</span>
          </div>
        </div>
      )}
    </div>
  )
}
```

**Styling rules:**
- `sticky top-0 z-10` makes it stick below the header as user scrolls
- `bg-card/95 backdrop-blur-sm` gives a frosted glass effect
- Progress bar uses `bg-muted` for track and themed colors for fill
- The `animate-pulse` at 95%+ creates urgency
- All colors use semantic tokens (destructive, muted, etc.) so it works across all 6 themes

---

#### 9. `ui/src/hooks/useWorkspaceChat.ts`

**Purpose:** WebSocket hook for workspace chat communication. Forked from `useAssistantChat.ts` with token tracking.

**Key differences from `useAssistantChat.ts`:**
- WebSocket URL: `/api/workspace/ws` (no project name in path)
- Tracks `totalTokens` and `contextWindow` state from `token_usage` messages
- `start()` accepts optional `working_directory` parameter
- Tool call descriptions include Write/Edit/Bash tools
- Session ID not needed client-side (server generates it from the WebSocket connection)

**Interface:**
```tsx
interface UseWorkspaceChatOptions {
  onError?: (error: string) => void
}

interface UseWorkspaceChatReturn {
  messages: ChatMessage[]
  isLoading: boolean
  connectionStatus: ConnectionStatus
  conversationId: number | null
  totalTokens: number
  contextWindow: number
  start: (conversationId?: number | null, workingDirectory?: string) => void
  sendMessage: (content: string) => void
  disconnect: () => void
  clearMessages: () => void
}
```

**WebSocket URL construction:**
```tsx
const protocol = window.location.protocol === "https:" ? "wss:" : "ws:"
const host = window.location.host
const wsUrl = `${protocol}//${host}/api/workspace/ws`
```

**Additional message handler in `onmessage`:**
```tsx
case "token_usage": {
  const tokenData = data as { total_tokens: number; context_window: number }
  setTotalTokens(tokenData.total_tokens)
  setContextWindow(tokenData.context_window)
  break
}
```

**Tool call descriptions:**
Add the workspace-specific descriptions (Write, Edit, Bash) in addition to the existing Read/Glob/Grep/WebFetch/WebSearch ones from `useAssistantChat`.

**Full state:**
```tsx
const [totalTokens, setTotalTokens] = useState(0)
const [contextWindow, setContextWindow] = useState(1_000_000)
```

Include these in the return object. Reset `totalTokens` to 0 in `clearMessages()`.

---

#### 10. `ui/src/hooks/useWorkspaceConversations.ts`

**Purpose:** React Query hooks for workspace conversation CRUD operations.

```tsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  listWorkspaceConversations,
  getWorkspaceConversation,
  createWorkspaceConversation,
  updateWorkspaceConversation,
  deleteWorkspaceConversation,
} from '../lib/api'

const CONVERSATIONS_KEY = ['workspace', 'conversations']

export function useWorkspaceConversations() {
  return useQuery({
    queryKey: CONVERSATIONS_KEY,
    queryFn: listWorkspaceConversations,
    refetchInterval: 10_000,  // Refresh every 10 seconds
  })
}

export function useWorkspaceConversation(conversationId: number | null) {
  return useQuery({
    queryKey: [...CONVERSATIONS_KEY, conversationId],
    queryFn: () => getWorkspaceConversation(conversationId!),
    enabled: conversationId !== null,
  })
}

export function useCreateWorkspaceConversation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createWorkspaceConversation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CONVERSATIONS_KEY })
    },
  })
}

export function useUpdateWorkspaceConversation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      conversationId,
      title,
      category,
    }: {
      conversationId: number
      title?: string
      category?: string
    }) => updateWorkspaceConversation(conversationId, { title, category }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CONVERSATIONS_KEY })
    },
  })
}

export function useDeleteWorkspaceConversation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deleteWorkspaceConversation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CONVERSATIONS_KEY })
    },
  })
}
```

---

### Files to Modify

#### 1. `ui/src/lib/routes.ts`

**Add** the `isWorkspaceRoute` function:

```typescript
/**
 * Check if the current URL hash matches the workspace route.
 * Format: /#/workspace
 */
export function isWorkspaceRoute(): boolean {
  return window.location.hash === '#/workspace' ||
         window.location.hash.startsWith('#/workspace/')
}
```

---

#### 2. `ui/src/main.tsx`

**Import** the new route function and page component:

```tsx
import { WorkspacePage } from './pages/WorkspacePage'
import { isStylePreviewRoute, isQuadPreviewRoute, isWorkspaceRoute } from './lib/routes'
```

**Update** the `Root()` function to check the workspace route BEFORE the default App:

```tsx
function Root() {
  if (isStylePreviewRoute()) {
    return <StylePreviewPage />
  }
  if (isQuadPreviewRoute()) {
    return <QuadPreviewPage />
  }
  if (isWorkspaceRoute()) {
    return <WorkspacePage />
  }
  return <App />
}
```

---

#### 3. `ui/src/lib/types.ts`

**Add** a new section after the "Assistant Chat Types" section:

```typescript
// ============================================================================
// Workspace Chat Types
// ============================================================================

export interface WorkspaceConversation {
  id: number
  title: string | null
  category: string
  working_directory: string | null
  created_at: string | null
  updated_at: string | null
  message_count: number
}

export interface WorkspaceMessage {
  id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  token_estimate: number
  timestamp: string | null
}

export interface WorkspaceConversationDetail {
  id: number
  title: string | null
  category: string
  working_directory: string | null
  created_at: string | null
  updated_at: string | null
  messages: WorkspaceMessage[]
}

export interface WorkspaceChatTokenUsageMessage {
  type: 'token_usage'
  total_tokens: number
  context_window: number
}

export type WorkspaceChatServerMessage =
  | AssistantChatTextMessage          // Reuse text
  | AssistantChatToolCallMessage      // Reuse tool_call
  | WorkspaceChatTokenUsageMessage    // New: token usage
  | AssistantChatResponseDoneMessage  // Reuse response_done
  | AssistantChatErrorMessage         // Reuse error
  | AssistantChatConversationCreatedMessage  // Reuse conversation_created
  | AssistantChatPongMessage          // Reuse pong
```

---

#### 4. `ui/src/lib/api.ts`

**Add** imports for the new types at the top of the import block:

```typescript
import type {
  // ... existing imports ...
  WorkspaceConversation,
  WorkspaceConversationDetail,
} from './types'
```

**Add** a new section after the "Assistant Chat API" section:

```typescript
// ============================================================================
// Workspace Chat API
// ============================================================================

export async function listWorkspaceConversations(): Promise<WorkspaceConversation[]> {
  return fetchJSON('/workspace/conversations')
}

export async function getWorkspaceConversation(
  conversationId: number
): Promise<WorkspaceConversationDetail> {
  return fetchJSON(`/workspace/conversations/${conversationId}`)
}

export async function createWorkspaceConversation(
  options?: { category?: string; working_directory?: string }
): Promise<WorkspaceConversation> {
  return fetchJSON('/workspace/conversations', {
    method: 'POST',
    body: JSON.stringify(options ?? {}),
  })
}

export async function updateWorkspaceConversation(
  conversationId: number,
  update: { title?: string; category?: string }
): Promise<WorkspaceConversation> {
  return fetchJSON(`/workspace/conversations/${conversationId}`, {
    method: 'PATCH',
    body: JSON.stringify(update),
  })
}

export async function deleteWorkspaceConversation(
  conversationId: number
): Promise<void> {
  await fetchJSON(`/workspace/conversations/${conversationId}`, {
    method: 'DELETE',
  })
}

export async function getWorkspaceTokenUsage(
  conversationId: number
): Promise<{ total_tokens: number; context_window: number; usage_percent: number }> {
  return fetchJSON(`/workspace/conversations/${conversationId}/tokens`)
}
```

---

#### 5. `server/routers/__init__.py`

**Add** the workspace router import and export:

```python
from .workspace import router as workspace_router
```

Add `"workspace_router"` to the `__all__` list.

---

#### 6. `server/main.py`

**Four changes:**

1. **Import the router** in the imports block:
```python
from .routers import (
    # ... existing imports ...
    workspace_router,
)
```

2. **Import the cleanup function:**
```python
from .services.workspace_chat_session import cleanup_all_workspace_sessions
```

3. **Register the router** in the "Include Routers" section:
```python
app.include_router(workspace_router)
```

4. **Add cleanup** to the lifespan shutdown section (after `cleanup_all_expand_sessions()`):
```python
await cleanup_all_workspace_sessions()
```

---

#### 7. `ui/src/App.tsx`

**Add** a "Workspace" navigation button in the top bar. Look for the existing header area (the section with the project selector and settings buttons). Add a button that navigates to the workspace:

```tsx
<Button
  variant="ghost"
  size="sm"
  className="gap-1.5"
  onClick={() => { window.location.hash = '#/workspace' }}
  title="Open IdeaForge Workspace"
>
  <MessageSquare size={16} />
  <span className="hidden sm:inline text-xs">Workspace</span>
</Button>
```

Import `MessageSquare` from `lucide-react`.

Place this button near the existing settings/theme buttons in the top-right area of the header.

---

### Directory Structure

After Phase 1, these new files exist:

```
server/
  services/
    workspace_database.py      (NEW)
    workspace_chat_session.py  (NEW)
  routers/
    workspace.py               (NEW)

ui/src/
  pages/
    WorkspacePage.tsx           (NEW)
  components/
    workspace/
      WorkspaceSidebar.tsx      (NEW)
      WorkspaceChat.tsx         (NEW)
      WorkspaceChatHeader.tsx   (NEW)
      ContextBudgetBar.tsx      (NEW)
  hooks/
    useWorkspaceChat.ts         (NEW)
    useWorkspaceConversations.ts (NEW)
```

Modified files:
```
ui/src/lib/routes.ts           (ADD isWorkspaceRoute)
ui/src/main.tsx                (ADD workspace route check)
ui/src/lib/types.ts            (ADD workspace types)
ui/src/lib/api.ts              (ADD workspace API functions)
ui/src/App.tsx                 (ADD workspace nav button)
server/routers/__init__.py     (ADD workspace_router)
server/main.py                 (ADD router + cleanup)
```

---

### Testing Checklist

#### Backend

1. **Start the server and verify the workspace endpoints exist:**
   - `GET /api/workspace/conversations` returns `200 []`
   - `POST /api/workspace/conversations` with `{"category": "general"}` returns a new conversation
   - `GET /api/workspace/conversations/{id}` returns the conversation with empty messages
   - `PATCH /api/workspace/conversations/{id}` with `{"title": "New Title"}` updates successfully
   - `DELETE /api/workspace/conversations/{id}` returns success
   - `GET /api/workspace/conversations/{id}/tokens` returns `{"total_tokens": 0, "context_window": 1000000, "usage_percent": 0}`

2. **Database file location:** Verify `~/.autoforge/workspace.db` is created after the first API call. Verify it has `workspace_conversations` and `workspace_messages` tables.

3. **WebSocket connection:** Open browser DevTools, connect to `ws://localhost:8888/api/workspace/ws`, send `{"type": "start"}`, verify you receive `conversation_created` and `text` (greeting) messages, then `response_done`.

4. **Chat functionality:** Send `{"type": "message", "content": "What files are in the current directory?"}` and verify Claude responds with text chunks and tool_call messages (should use Bash `ls` or Glob).

5. **Token tracking:** After a response, verify you receive a `{"type": "token_usage", "total_tokens": N, "context_window": 1000000}` message with N > 0.

6. **Security:** Send a message asking Claude to run `sudo rm -rf /`. Verify the bash_security_hook blocks the command and Claude reports the restriction.

#### Frontend

7. **Route works:** Navigate to `http://localhost:8888/#/workspace`. Verify the full-page workspace renders (not the main App).

8. **Back button:** Click "Back to Projects". Verify it navigates to `/#/` (main app).

9. **Sidebar loads:** Verify the sidebar shows "New Chat" button and an empty conversation list.

10. **New chat flow:** Click "New Chat". Verify:
    - WebSocket connects (status shows "Connected")
    - A greeting message appears from the assistant
    - The conversation appears in the sidebar
    - Context budget bar shows a small number of tokens

11. **Send message:** Type a message and press Enter. Verify:
    - User message appears in the chat
    - Loading indicator shows
    - Assistant response streams in with tool call indicators
    - Context budget bar updates after response

12. **Conversation switching:** Create a second conversation. Click between them in the sidebar. Verify messages load correctly for each.

13. **Title editing:** Click the conversation title in the header. Edit it. Press Enter. Verify the sidebar updates.

14. **Category changing:** Change the category dropdown. Verify the badge color updates in the sidebar.

15. **Context budget bar:**
    - Verify it sticks below the header when scrolling through messages
    - Verify the percentage and token count update after each response
    - After many messages, verify yellow/orange/red color thresholds work

16. **Delete conversation:** Delete a conversation from the sidebar. Verify it disappears and the chat area shows the empty state.

17. **Theme compatibility:** Switch to at least 3 different themes (Twitter, Claude, Neo Brutalism). Verify all workspace components render correctly with proper colors and no hardcoded colors bleeding through.

#### Lint and Build

18. **Python linting:**
    ```bash
    cd /path/to/autoforge
    ruff check server/services/workspace_database.py server/services/workspace_chat_session.py server/routers/workspace.py
    ```
    Must pass with zero errors.

19. **Frontend build:**
    ```bash
    cd ui
    npm run lint
    npm run build
    ```
    Must pass with zero errors and zero type errors.

---

### Important Reminders

1. **Do NOT modify assistant files.** The workspace is a completely separate system. Do not change `assistant_chat_session.py`, `assistant_database.py`, `assistant_chat.py`, `useAssistantChat.ts`, or `AssistantChat.tsx`. Fork them — do not modify them.

2. **Do NOT add React Router.** The app uses custom hash routing. Add `isWorkspaceRoute()` to `routes.ts` and check it in `main.tsx`. Navigation uses `window.location.hash = '#/workspace'`.

3. **Use theme tokens everywhere.** No hardcoded colors like `bg-blue-500` or `text-gray-700`. Always use `bg-primary`, `text-foreground`, `bg-card`, `border-border`, `text-muted-foreground`, etc. The only exception is status-specific colors inside the `ContextBudgetBar` thresholds (orange, yellow, red), which must still work with both light and dark modes — use `dark:` variants.

4. **Add the Bash security hook.** The workspace agent can run Bash commands. You MUST apply the security hook. Import `bash_security_hook` from `security.py` and pass it via the `hooks` parameter to `ClaudeAgentOptions`. See the code snippet in the `workspace_chat_session.py` section above.

5. **Import `HookMatcher` correctly:**
   ```python
   from claude_agent_sdk.types import HookMatcher
   ```

6. **The workspace database is GLOBAL.** Path is `~/.autoforge/workspace.db`. Functions do NOT take `project_dir`. This is the fundamental architectural difference from the assistant database.

7. **Reuse `ChatMessage` component.** Import it from `@/components/ChatMessage` in `WorkspaceChat.tsx`. Do not rebuild the message rendering UI.

8. **Clean up on server shutdown.** Add `await cleanup_all_workspace_sessions()` to the lifespan shutdown in `server/main.py`.

9. **WebSocket cleanup on disconnect.** Unlike assistant chat (which keeps sessions alive for resume), workspace sessions should be cleaned up when the WebSocket disconnects. This is because each connection gets its own Claude SDK client, and we don't want orphaned clients consuming resources.

10. **Python line length.** The project uses `ruff` with line length 120. Keep lines under 120 characters. Check with `ruff check`.

11. **TypeScript strict mode.** The project uses strict TypeScript. Ensure all types are properly annotated — no `any` types, no missing return types on exported functions.

12. **Create the `ui/src/pages/` directory.** It does not exist yet. Also create `ui/src/components/workspace/`.

13. **Token estimation is approximate.** The `chars / 4` heuristic is intentionally rough. Do not over-engineer this. The context budget bar is for user awareness, not precision billing.

14. **The `fetchJSON` helper already prepends `/api`.** When calling `fetchJSON('/workspace/conversations')`, the actual URL will be `/api/workspace/conversations`. Do NOT double-prefix.

15. **Use `acceptEdits` permission mode**, not `bypassPermissions`. The `acceptEdits` mode is what the spec creation chat uses for Write/Edit operations. It allows the agent to write and edit files while still going through the permission system. Since we have the security hook for Bash, this is the correct choice.
