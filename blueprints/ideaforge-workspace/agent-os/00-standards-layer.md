# IdeaForge Workspace — Standards Layer

> Agent OS Standards Document | Referenced by all phase blueprints

---

## 1. Technology Stack

### Backend

| Technology | Version / Notes |
|---|---|
| Python | 3.11+ (target in `pyproject.toml`) |
| FastAPI | ASGI web framework (uvicorn server) |
| SQLAlchemy 2.0 | ORM with `DeclarativeBase` pattern |
| SQLite | Database engine (file-per-database, WAL mode not required) |
| Claude Agent SDK | `claude_agent_sdk` — `ClaudeSDKClient`, `ClaudeAgentOptions`, `HookMatcher` |
| `cryptography` | Fernet symmetric encryption for token storage (Phase 3) |
| `python-multipart` | File upload support via `UploadFile` (already in `requirements.txt`) |
| `anthropic` | Python SDK for lightweight side-channel API calls (summary generation) |

### Frontend

| Technology | Version / Notes |
|---|---|
| React | 19 (`react` and `react-dom` ^19.0.0) |
| TypeScript | ~5.7.3, strict mode enabled |
| Vite | 7 (`vite` ^7.3.0, build tool) |
| TanStack Query | React Query v5 (`@tanstack/react-query` ^5.72.0) |
| Tailwind CSS | v4 with `@theme inline` directive and `tw-animate-css` |
| Radix UI | Primitives: Dialog, DropdownMenu, Checkbox, Label, Separator, Switch, Slot |
| lucide-react | Icon library (^0.475.0) |
| xterm.js | Terminal emulation (existing, `@xterm/xterm` ^6.0.0) |
| dagre | Graph layout (existing, ^0.8.5) |
| react-markdown | Markdown rendering with `remark-gfm` |
| class-variance-authority | Variant utility for component styling |
| tailwind-merge | Tailwind class merging utility |

### Infrastructure

- **No React Router** — custom hash-based routing (no `react-router-dom`, no `HashRouter`, no `BrowserRouter`)
- **WebSocket** for real-time chat streaming (native browser WebSocket API)
- **SQLite** for all persistence (no external database, no Redis, no Postgres)
- **File storage** — `~/.autoforge/workspace/` directory hierarchy for library files, tokens, and scratch data
- **No new npm packages** required for Phases 1-2; `cryptography` added to `requirements.txt` for Phase 3

---

## 2. Architecture Standards

### Database Architecture

The workspace database is **GLOBAL** at `~/.autoforge/workspace.db`. This is the fundamental architectural difference from the assistant database, which is per-project at `{project_dir}/.autoforge/assistant.db`.

**Rules:**
- Database functions do NOT take a `project_dir` parameter (unlike `assistant_database.py`)
- Use SQLAlchemy 2.0 `DeclarativeBase` pattern (class `Base(DeclarativeBase): pass`)
- Engine caching with thread-safe double-checked locking:
  - Module-level `_engine_cache: dict[str, Engine] = {}` and `_cache_lock = threading.Lock()`
  - Check cache outside lock, then re-check inside lock before creating
- Session factory via `sessionmaker(bind=engine)`, always close sessions in `finally` blocks
- `Base.metadata.create_all(engine)` auto-creates tables on first access
- Schema migrations via `PRAGMA table_info` checks + `ALTER TABLE ADD COLUMN` for new columns
- Use `_utc_now()` helper for all datetime defaults: `datetime.now(timezone.utc)`
- Use `func.coalesce()` for SQL aggregations with defaults (e.g., `func.coalesce(func.sum(...), 0)`)
- All table names prefixed with `workspace_` to avoid collisions

**Engine initialization reference (from `assistant_database.py`):**
```python
_engine_cache: dict[str, Engine] = {}
_cache_lock = threading.Lock()

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)

def get_engine() -> Engine:
    db_path = Path.home() / ".autoforge" / "workspace.db"
    cache_key = db_path.as_posix()
    if cache_key in _engine_cache:
        return _engine_cache[cache_key]
    with _cache_lock:
        if cache_key not in _engine_cache:
            db_path.parent.mkdir(parents=True, exist_ok=True)
            db_url = f"sqlite:///{db_path.as_posix()}"
            engine = create_engine(
                db_url, echo=False,
                connect_args={"check_same_thread": False, "timeout": 30}
            )
            Base.metadata.create_all(engine)
            _engine_cache[cache_key] = engine
    return _engine_cache[cache_key]
```

### Routing Architecture

**No React Router.** The app uses custom hash-based routing.

- Route detection functions live in `ui/src/lib/routes.ts` (e.g., `isWorkspaceRoute()`)
- The `Root()` function in `ui/src/main.tsx` checks each route function and returns the matching component
- Navigation uses `window.location.hash = '#/workspace'`
- Each standalone page is a full-viewport component, not a nested route

**Adding the workspace route:**
1. Add `isWorkspaceRoute()` to `ui/src/lib/routes.ts`
2. Add conditional check in `Root()` in `ui/src/main.tsx` (before the default `<App />` return)
3. All internal workspace navigation uses `window.location.hash`

### Backend Router Pattern

Router registration is a **3-file pattern:**

1. **Router file** — e.g., `server/routers/workspace.py`
2. **Export in `__init__`** — add `from .workspace import router as workspace_router` to `server/routers/__init__.py`, plus add `"workspace_router"` to the `__all__` list
3. **Include in main** — add `app.include_router(workspace_router)` in `server/main.py`

**Router configuration:**
- All workspace endpoints use `APIRouter(prefix="/api/workspace", tags=["workspace"])`
- WebSocket endpoints include the full router prefix: `/api/workspace/ws/{conversation_id}`
- Server shutdown cleanup via lifespan handler in `server/main.py` — add `await cleanup_all_workspace_sessions()` after the existing cleanup calls

**Existing lifespan shutdown order in `server/main.py`:**
```python
await cleanup_scheduler()
await cleanup_all_managers()
await cleanup_assistant_sessions()
await cleanup_all_expand_sessions()
await cleanup_all_terminals()
await cleanup_all_devservers()
# Add workspace cleanup here:
await cleanup_all_workspace_sessions()
```

### Frontend Component Architecture

- Functional components with hooks (no class components)
- TanStack Query for all server state (queries + mutations with `useQuery` / `useMutation`)
- Query invalidation via `useQueryClient().invalidateQueries()` in mutation `onSuccess`

**File organization:**

| Location | Purpose |
|---|---|
| `ui/src/pages/` | Full-page layouts (e.g., `WorkspacePage.tsx`) |
| `ui/src/components/workspace/` | All workspace-specific components |
| `ui/src/hooks/` | Custom hooks (prefixed `useWorkspace*`) |
| `ui/src/lib/types.ts` | TypeScript type definitions — add new sections, do NOT create separate files |
| `ui/src/lib/api.ts` | API functions — add new sections, do NOT create separate files |
| `ui/src/lib/routes.ts` | Route detection functions |

**The `fetchJSON` helper** in `ui/src/lib/api.ts` already prepends `/api`. Pass paths like `/workspace/conversations`, NOT `/api/workspace/conversations`.

### Session Management

Chat sessions are managed via the Claude Agent SDK (`ClaudeSDKClient`).

**Key configuration:**
- Permission mode: `acceptEdits` (NOT `bypassPermissions` — the workspace can write files)
- Bash security hook applied via `PreToolUse` hook:
  ```python
  from claude_agent_sdk.types import HookMatcher
  from security import bash_security_hook
  hooks = {"PreToolUse": [HookMatcher(matcher="Bash", hooks=[bash_security_hook])]}
  ```
- Security settings written to `~/.autoforge/.workspace_claude_settings.json`
- System prompt written to `~/.autoforge/.workspace_scratch/CLAUDE.md`
- SDK reads CLAUDE.md via `setting_sources=["project"]` with `cwd` set to the scratch directory

**Context window — CRITICAL:**
- **1,000,000 tokens** (1M) via beta flag `context-1m-2025-08-07`
- This is enabled via `betas=["context-1m-2025-08-07"]` on `ClaudeAgentOptions`
- Disabled for alternative APIs (Ollama, GLM, etc.) that do not support this beta
- The constant is `CONTEXT_WINDOW_TOKENS = 1_000_000`
- Do NOT use `200000` or `200_000` — the correct value is `1_000_000`
- Max history messages: 100 with NO per-message truncation (unlike the assistant's 35/500-char limit)

**Session registry:**
- Thread-safe dict with locking, keyed by `session_id` string (NOT project_name)
- Module-level `_sessions: dict[str, WorkspaceChatSession] = {}` and `_sessions_lock = threading.Lock()`
- Sessions closed on WebSocket disconnect (unlike assistant which keeps sessions alive)
- `cleanup_all_workspace_sessions()` for server shutdown

**Model resolution:**
```python
from registry import DEFAULT_MODEL, get_effective_sdk_env
sdk_env = get_effective_sdk_env()
model = sdk_env.get("ANTHROPIC_DEFAULT_OPUS_MODEL") or os.getenv(
    "ANTHROPIC_DEFAULT_OPUS_MODEL", DEFAULT_MODEL
)
```
The `DEFAULT_MODEL` is `"claude-opus-4-6"` (defined in `registry.py`).

### Folder Structure

```
server/
  services/
    workspace_database.py            # SQLAlchemy models + CRUD (global DB)
    workspace_chat_session.py        # Claude SDK session management
    workspace_summary.py             # Auto-summary generation service (Phase 2)
    workspace_library.py             # File library service (Phase 3)
    workspace_token_encryption.py    # Fernet token encryption (Phase 3)
    workspace_repos.py               # GitHub repo connection service (Phase 3)
  routers/
    workspace.py                     # REST + WebSocket endpoints

ui/src/
  pages/
    WorkspacePage.tsx                 # Full-page workspace layout
  components/
    workspace/
      WorkspaceSidebar.tsx            # Conversation list sidebar
      WorkspaceChat.tsx               # Message display + input
      WorkspaceChatHeader.tsx         # Title bar with actions
      ContextBudgetBar.tsx            # Token budget visualization
      EnhancedContextBudgetBar.tsx    # Segmented budget bar (Phase 2+)
      AutoSummaryPin.tsx              # Collapsible summary card (Phase 2)
      CategoryManager.tsx             # Category CRUD modal (Phase 2)
      ConversationSearch.tsx          # Server-side search (Phase 2)
      WorkspaceLibrary.tsx            # File library right panel (Phase 3)
      FileUploadModal.tsx             # Upload/paste modal (Phase 3)
      FilePreview.tsx                 # File content preview (Phase 3)
      RepoConnector.tsx               # GitHub repo connection modal (Phase 3)
      RepoBrowser.tsx                 # Repo file tree browser (Phase 3)
      ChatForkModal.tsx               # Fork conversation modal (Phase 4)
      InjectFromChatModal.tsx         # Cross-chat injection modal (Phase 4)
      WorkspaceKeyboardHelp.tsx       # Keyboard shortcuts help (Phase 4)
  hooks/
    useWorkspaceChat.ts               # WebSocket chat hook
    useWorkspaceConversations.ts      # Conversation CRUD hooks
    useWorkspaceCategories.ts         # Category CRUD hooks (Phase 2)
    useWorkspaceLibrary.ts            # Library file hooks (Phase 3)
    useWorkspaceKeyboardShortcuts.ts  # Keyboard shortcut hook (Phase 4)
```

### Key Files to Fork (NOT Modify Originals)

These files serve as the architectural template. Create new workspace-specific copies that follow the same patterns but with workspace-specific logic.

| Original | Fork To |
|---|---|
| `server/services/assistant_chat_session.py` | `server/services/workspace_chat_session.py` |
| `server/services/assistant_database.py` | `server/services/workspace_database.py` |
| `server/routers/assistant_chat.py` | `server/routers/workspace.py` |
| `ui/src/hooks/useAssistantChat.ts` | `ui/src/hooks/useWorkspaceChat.ts` |

### Key Files to Reuse (Import Directly)

Do NOT rebuild these. Import and use them as-is.

| File | What to Import | Purpose |
|---|---|---|
| `ui/src/components/ChatMessage.tsx` | `ChatMessage` component | Message rendering (supports text, tool calls, markdown) |
| `security.py` | `bash_security_hook` | Bash command validation against allowlist |
| `server/services/chat_constants.py` | `ROOT_DIR`, `make_multimodal_message()` | Project root path, multimodal message construction |
| `registry.py` | `DEFAULT_MODEL`, `get_effective_sdk_env()` | Model resolution and API provider configuration |

---

## 3. Coding Conventions

### Python

| Rule | Detail |
|---|---|
| Line length | 120 characters (ruff configuration in `pyproject.toml`) |
| Python target | 3.11+ |
| Type hints | Required on all function signatures |
| Docstrings | Required on all public functions (module-level functions and class methods) |
| File paths | Use `Path` objects, never string concatenation for path building |
| Imports in routers | Inline imports for services inside handler functions (lazy loading pattern) |
| Request/response schemas | Pydantic `BaseModel` classes, defined inline in router files |
| Error handling (routers) | `HTTPException` for all error responses |
| Error handling (services) | `ValueError` in database/service functions, caught by router handlers |
| SQL aggregations | Use `func.coalesce()` for aggregations with defaults |
| Linting | `ruff check .` must pass with zero errors |
| Type checking | `mypy .` (strict returns, ignores missing imports) |

**ruff configuration (from `pyproject.toml`):**
```toml
[tool.ruff]
line-length = 120
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "W"]
ignore = ["E501", "E402", "E712"]
```

### TypeScript

| Rule | Detail |
|---|---|
| Strict mode | Enabled (`tsc -b` runs as part of `npm run build`) |
| No `any` types | All types must be explicit |
| Return types | Required on all exported functions |
| Component docs | JSDoc comment block on every new component |
| Props definitions | `interface` over `type` alias for component props |
| Event handlers | Wrap with `useCallback` when passed as props |
| Computed values | Wrap with `useMemo` when used in render |
| Linting | `npm run lint` (ESLint) must pass with zero errors |
| Build | `npm run build` (TypeScript check + Vite build) must succeed |

### General

- No emoji in code, comments, or UI text
- Token estimation heuristic: `len(text) // 4` (consistent within each module)
- WebSocket protocol: JSON messages with `type` string discriminator field
- All datetime values stored in UTC; use `_utc_now()` helper in Python, `.toISOString()` in TypeScript
- Boolean columns in SQLite: use `Integer` with 0/1 (SQLAlchemy `Boolean` maps to this automatically)

---

## 4. Styling Standards

### Theme System

The project has **6 themes** defined in `ui/src/styles/globals.css`:

1. **Twitter** (default) — clean modern blue
2. **Claude** — warm beige/cream with orange primary
3. **Neo Brutalism** — bold black borders, bright colors
4. **Retro Arcade** — pixel-inspired neon
5. **Aurora** — soft gradients, purple/teal
6. **Business** — conservative gray/blue

Each theme has both light and dark mode variants. All workspace components MUST be theme-agnostic. Never hardcode theme-specific styles.

### Required Tailwind Tokens

Use ONLY these semantic tokens for colors and backgrounds. They adapt automatically to all 6 themes and both light/dark modes.

| Token | Purpose |
|---|---|
| `bg-background` | Page/app background |
| `text-foreground` | Primary text |
| `bg-card` / `text-card-foreground` | Card/panel backgrounds and text |
| `border-border` | All borders |
| `text-muted-foreground` | Secondary/dimmed text |
| `bg-muted` | Muted backgrounds, track fills |
| `bg-primary` / `text-primary-foreground` | Primary actions, active states |
| `bg-secondary` / `text-secondary-foreground` | Secondary elements |
| `bg-accent` / `text-accent-foreground` | Active sidebar items, hover states |
| `bg-destructive` / `text-destructive` | Errors, destructive actions |
| `bg-popover` / `text-popover-foreground` | Tooltips, dropdown menus |
| `bg-chart-1` through `bg-chart-5` | Chart/graph segment colors |
| `bg-input` | Input field backgrounds |
| `ring-ring` | Focus ring color |

### CSS Variables

These variables are defined in `:root` and `.dark` blocks in `globals.css`.

| Variable | Purpose |
|---|---|
| `var(--color-status-pending)` | Pending state color |
| `var(--color-status-progress)` | In-progress state color |
| `var(--color-status-done)` | Completed state color |
| `var(--shadow-sm)` | Small shadow |
| `var(--shadow)` | Default shadow |
| `var(--shadow-md)` | Medium shadow |
| `var(--shadow-lg)` | Large shadow |
| `var(--transition-fast)` | 150ms transition duration |
| `var(--transition-normal)` | 250ms transition duration |
| `var(--ease-smooth)` | `cubic-bezier(0.4, 0, 0.2, 1)` easing |
| `var(--radius)` | Border radius (varies per theme) |
| `var(--font-sans)` | Sans-serif font stack |
| `var(--font-mono)` | Monospace font stack |

### Forbidden

1. **No hardcoded hex colors in Tailwind classes** (e.g., `bg-blue-500`, `text-gray-700`, `border-slate-300`)
2. **No neobrutalism-specific styles** (no `border-4 border-black`, no `shadow-[4px_4px_0px_0px]`)
3. **No `--color-neo-*` variables** — these do NOT exist in the codebase. The correct names are `--color-status-pending`, `--color-status-progress`, `--color-status-done`

**Exception:** Status-specific threshold colors in `ContextBudgetBar` (orange, yellow, red for usage warnings). These MUST include both light and dark variants:
```tsx
// Acceptable for threshold indicators only:
barColor = 'bg-orange-500'
textColor = 'text-orange-600 dark:text-orange-400'
```

---

## 5. Security Standards

### Bash Command Security

- All Bash commands validated via `bash_security_hook` from `security.py`
- Applied as `PreToolUse` hook: `HookMatcher(matcher="Bash", hooks=[bash_security_hook])`
- The hook checks against `ALLOWED_COMMANDS` allowlist (npm, git, node, ls, cat, etc.)
- Hardcoded blocklist (sudo, dd, shutdown, etc.) can NEVER be overridden
- Workspace agent uses `acceptEdits` permission mode (NOT `bypassPermissions`)

### Token and Credential Security

- GitHub personal access tokens encrypted with Fernet (Phase 3)
- Machine-derived encryption key from MAC address SHA-256
- Tokens stored in `~/.autoforge/workspace/.tokens` (JSON file, `0o600` POSIX permissions)
- Database stores reference IDs only (`access_token_ref`), never plaintext tokens
- Plaintext tokens NEVER appear in logs, error messages, or API responses
- Authenticated git URLs (containing tokens) NEVER logged

### File Upload Security

- Maximum file size: 10MB (enforced server-side)
- Extension allowlist for text-based files only (`.md`, `.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.json`, `.yaml`, `.yml`, `.toml`, `.txt`, `.csv`, `.html`, `.css`, `.sql`, `.sh`, `.bash`, `.xml`, `.env.example`)
- UUID prefix on stored filenames prevents path traversal and collision
- Content injection: library files injected as plaintext context, never executed
- Images handled via `make_multimodal_message()` from `chat_constants.py`

### Path Traversal Prevention

- Use `Path.resolve()` + `.relative_to()` to verify paths stay within expected directories
- Never use user-provided filenames directly as filesystem paths
- Git operations use `subprocess.run()` with argument lists (list form), never `os.system()` or shell strings
- Never embed tokens in shell command strings

### Error Sanitization

- Strip token substrings from git error messages before returning to client
- Never expose internal file paths or stack traces in API responses
- Use structured `HTTPException` responses with safe error messages

### Security Settings File

Every chat session type writes a security settings JSON file. The workspace uses:
```python
security_settings = {
    "sandbox": {"enabled": False},
    "permissions": {
        "defaultMode": "acceptEdits",
        "allow": ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "WebFetch", "WebSearch"],
    },
}
# Written to: ~/.autoforge/.workspace_claude_settings.json
```

---

## 6. Quality Standards

### Testing Commands

```bash
# Python linting (line length 120, Python 3.11 target)
ruff check .

# Python type checking (strict returns, ignores missing imports)
mypy .

# Frontend linting (ESLint)
cd ui && npm run lint

# Frontend type check + production build (Vite 7)
cd ui && npm run build
```

### Quality Gates

Every implementation must pass ALL of these before being considered complete:

1. **`ruff check .`** — zero errors on all new/modified Python files
2. **`npm run lint`** — zero ESLint errors in `ui/` directory
3. **`npm run build`** — TypeScript compilation and Vite build succeed with zero errors
4. **No `any` types** in new TypeScript code
5. **All new Python functions** have docstrings
6. **All new TypeScript components** have JSDoc comments
7. **No hardcoded colors** in Tailwind classes (verified by visual inspection)
8. **WebSocket protocol** tested manually via browser DevTools or automated tests

### Existing Test Suites (Do Not Break)

```bash
python test_security.py                    # 12 security unit tests
python test_security_integration.py        # 9 integration tests
python -m pytest test_client.py            # 20 client tests
python -m pytest test_dependency_resolver.py  # 12 dependency resolver tests
python -m pytest test_rate_limit_utils.py  # 22 rate limit tests
```

These tests must continue to pass after workspace changes. The workspace should not modify any files that these tests cover.

---

## 7. WebSocket Protocol

### Connection

The workspace WebSocket endpoint is at `/api/workspace/ws` (or `/api/workspace/ws/{conversation_id}` depending on phase). Connect using:

```typescript
const protocol = window.location.protocol === "https:" ? "wss:" : "ws:"
const host = window.location.host
const wsUrl = `${protocol}//${host}/api/workspace/ws`
```

### Client-to-Server Messages

```jsonc
// Start a new conversation
{"type": "start"}

// Resume an existing conversation
{"type": "start", "conversation_id": 123, "working_directory": "/path/to/dir"}

// Send a user message
{"type": "message", "content": "What files are in this directory?"}

// Answer an interactive question
{"type": "answer", "answer": "Option A"}

// Keep-alive ping
{"type": "ping"}
```

### Server-to-Client Messages

```jsonc
// New conversation created
{"type": "conversation_created", "conversation_id": 42}

// Streaming text content
{"type": "text", "content": "Here is the analysis..."}

// Tool call indicator
{"type": "tool_call", "tool": "Read", "input": {"file_path": "/home/user/file.py"}}

// Interactive question from agent
{"type": "question", "questions": [...]}

// Response complete
{"type": "response_done"}

// Token usage update (sent after each response)
{"type": "token_usage", "total_tokens": 5432, "context_window": 1000000}

// Error
{"type": "error", "content": "Error message here"}

// Pong (response to ping)
{"type": "pong"}
```

### Session Lifecycle

1. Client connects to WebSocket endpoint
2. Client sends `start` message (with optional `conversation_id` to resume)
3. Server creates or resumes a `WorkspaceChatSession`
4. For new conversations: server yields `conversation_created` + greeting `text` + `response_done`
5. For resumed conversations: server yields `response_done` (history loaded on first message)
6. Client sends `message` messages, server streams responses
7. On WebSocket disconnect: server closes the Claude SDK client and removes the session

**Important:** Unlike assistant chat (which keeps sessions alive after disconnect for resume), workspace sessions are cleaned up on disconnect. Each WebSocket connection gets its own Claude SDK client instance, and orphaned clients waste resources.

---

## 8. Type Definitions

All workspace types live in `ui/src/lib/types.ts`. Add a new section after the existing "Assistant Chat Types" section. Do NOT create separate type files.

### Core Types

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
```

### Reused Types

The workspace reuses several existing assistant chat message types for the WebSocket protocol:

- `AssistantChatTextMessage` (type: "text")
- `AssistantChatToolCallMessage` (type: "tool_call")
- `AssistantChatResponseDoneMessage` (type: "response_done")
- `AssistantChatErrorMessage` (type: "error")
- `AssistantChatConversationCreatedMessage` (type: "conversation_created")
- `AssistantChatPongMessage` (type: "pong")

---

## 9. API Functions

All workspace API functions live in `ui/src/lib/api.ts`. Add a new section after the existing "Assistant Chat API" section. Do NOT create separate API files.

Remember: `fetchJSON` already prepends `/api`, so pass paths like `/workspace/conversations`.

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

## 10. Database Schema (Cumulative Across All Phases)

### Phase 1 Tables

```sql
CREATE TABLE workspace_conversations (
    id INTEGER PRIMARY KEY,
    title VARCHAR(200),
    category VARCHAR(100) DEFAULT 'Uncategorized',
    working_directory TEXT,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE workspace_messages (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER REFERENCES workspace_conversations(id),
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    token_estimate INTEGER DEFAULT 0,
    timestamp DATETIME
);
```

### Phase 2 Additions

New columns on `workspace_conversations`:
- `pinned` BOOLEAN DEFAULT FALSE
- `token_count` INTEGER DEFAULT 0
- `summary` TEXT
- `summary_updated_at` DATETIME

New tables:
```sql
CREATE TABLE workspace_categories (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    color VARCHAR(50),
    sort_order INTEGER DEFAULT 0,
    created_at DATETIME
);

CREATE TABLE workspace_summaries (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER REFERENCES workspace_conversations(id),
    summary TEXT NOT NULL,
    message_count INTEGER DEFAULT 0,
    token_estimate INTEGER DEFAULT 0,
    created_at DATETIME
);
```

### Phase 3 Additions

```sql
CREATE TABLE workspace_library_files (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER,  -- NULL means global
    filename VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    file_type VARCHAR(50),
    content TEXT,
    file_path TEXT,
    file_size INTEGER DEFAULT 0,
    tags TEXT,
    active_in_context BOOLEAN DEFAULT FALSE,
    created_at DATETIME
);

CREATE TABLE workspace_connected_repos (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER,  -- NULL means global
    repo_url TEXT NOT NULL,
    repo_name VARCHAR(255),
    local_path TEXT,
    access_token_ref VARCHAR(100),  -- reference ID, not plaintext
    branch VARCHAR(100) DEFAULT 'main',
    last_synced_at DATETIME,
    created_at DATETIME
);
```

### Phase 4 Additions

New column on `workspace_conversations`:
- `forked_from_id` INTEGER (FK to `workspace_conversations.id`, nullable)

---

## 11. Anti-Patterns (What NOT to Do)

These rules are non-negotiable. Violating any of them will produce incorrect, insecure, or unmaintainable code.

### Architecture Anti-Patterns

1. **Do NOT modify `assistant_chat_session.py`, `assistant_database.py`, or `assistant_chat.py`** — the workspace is a completely separate system. Fork them; do not modify originals.
2. **Do NOT add React Router** (`react-router-dom`, `HashRouter`, `BrowserRouter`) — use the custom hash routing in `routes.ts` and `main.tsx`.
3. **Do NOT create separate database files** — all workspace tables go in the single `workspace.db` file at `~/.autoforge/workspace.db`.
4. **Do NOT add drag-and-drop libraries** — use simple up/down button reordering for sort operations.
5. **Do NOT implement FTS5** — SQLite `LIKE` queries are sufficient for the expected data volume.
6. **Do NOT use separate type or API files** — add workspace types to `ui/src/lib/types.ts` and API functions to `ui/src/lib/api.ts` in new sections.

### Security Anti-Patterns

7. **Do NOT store plaintext tokens anywhere** — not on disk, not in the database, not in logs, not in error messages.
8. **Do NOT use `os.system()` for git operations** — use `subprocess.run()` with argument lists.
9. **Do NOT embed tokens in shell command strings** — pass them via environment variables or `--config` files.
10. **Do NOT use `bypassPermissions`** — use `acceptEdits` permission mode for the workspace agent.

### Context Window Anti-Patterns

11. **Do NOT use `200000` or `200_000` for context window** — the correct value is `1_000_000` (1M tokens).
12. **Do NOT truncate messages in history loading** — full content with the 1M window. The assistant's 35-message / 500-char limit does NOT apply to the workspace.
13. **Do NOT block the chat WebSocket during summary generation** — use `asyncio.create_task()` to run summaries in the background.

### Styling Anti-Patterns

14. **Do NOT hardcode hex colors in Tailwind classes** — no `bg-blue-500`, `text-gray-700`, `border-slate-300`.
15. **Do NOT use neobrutalism-specific styles** — no `border-4 border-black`, no `shadow-[4px_4px_0px_0px]`.
16. **Do NOT reference `--color-neo-*` variables** — they do not exist. Use `--color-status-pending`, `--color-status-progress`, `--color-status-done`.

### Code Quality Anti-Patterns

17. **Do NOT use emoji** in code, comments, or UI text.
18. **Do NOT skip the security hook** — every workspace session must apply `bash_security_hook` via `PreToolUse`.
19. **Do NOT create `ui/src/pages/` directory manually if it exists** — check first. The same applies to `ui/src/components/workspace/`.

---

## 12. Reference: Existing Patterns

This section documents exact patterns from the codebase that workspace code must follow.

### SQLAlchemy Model Pattern (from `assistant_database.py`)

```python
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, create_engine, func
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

class Base(DeclarativeBase):
    pass

class WorkspaceConversation(Base):
    __tablename__ = "workspace_conversations"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=True)
    # ... other columns ...
    messages = relationship("WorkspaceMessage", back_populates="conversation", cascade="all, delete-orphan")
```

### CRUD Function Pattern (from `assistant_database.py`)

```python
def create_conversation(...) -> WorkspaceConversation:
    session = get_db_session()
    try:
        conversation = WorkspaceConversation(...)
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
        return conversation
    finally:
        session.close()
```

### Router Handler Pattern (from `assistant_chat.py`)

```python
@router.get("/conversations")
async def list_conversations():
    from ..services.workspace_database import get_conversations
    return get_conversations()

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int):
    from ..services.workspace_database import delete_conversation
    success = delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted"}
```

### WebSocket Handler Pattern (from `assistant_chat.py`)

```python
@router.websocket("/ws")
async def workspace_chat_websocket(websocket: WebSocket):
    await websocket.accept()
    session_id: Optional[str] = None
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            elif msg_type == "start":
                # ... create session and start ...
            elif msg_type == "message":
                # ... send message and stream response ...
    except WebSocketDisconnect:
        pass
    finally:
        if session_id:
            await remove_session(session_id)
```

### TanStack Query Hook Pattern (from existing hooks)

```typescript
export function useWorkspaceConversations() {
  return useQuery({
    queryKey: ['workspace', 'conversations'],
    queryFn: listWorkspaceConversations,
    refetchInterval: 10_000,
  })
}

export function useDeleteWorkspaceConversation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deleteWorkspaceConversation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workspace', 'conversations'] })
    },
  })
}
```

### Claude SDK Client Creation Pattern (from `assistant_chat_session.py`)

```python
system_cli = shutil.which("claude")

self.client = ClaudeSDKClient(
    options=ClaudeAgentOptions(
        model=model,
        cli_path=system_cli,
        setting_sources=["project"],
        allowed_tools=WORKSPACE_BUILTIN_TOOLS,
        permission_mode="acceptEdits",
        max_turns=100,
        cwd=str(workspace_scratch),
        settings=str(settings_file.resolve()),
        env=sdk_env,
        hooks=hooks,
        betas=[] if is_alternative_api else ["context-1m-2025-08-07"],
    )
)
await self.client.__aenter__()
self._client_entered = True
```

### Session Close Pattern (from `assistant_chat_session.py`)

```python
async def close(self) -> None:
    if self.client and self._client_entered:
        try:
            await self.client.__aexit__(None, None, None)
        except Exception as e:
            logger.warning(f"Error closing Claude client: {e}")
        finally:
            self._client_entered = False
            self.client = None
```

---

## 13. Quick Reference Card

| What | Value |
|---|---|
| Database path | `~/.autoforge/workspace.db` |
| Settings file | `~/.autoforge/.workspace_claude_settings.json` |
| System prompt file | `~/.autoforge/.workspace_scratch/CLAUDE.md` |
| Token file (Phase 3) | `~/.autoforge/workspace/.tokens` |
| Library file storage (Phase 3) | `~/.autoforge/workspace/files/` |
| Cloned repos (Phase 3) | `~/.autoforge/workspace/repos/` |
| Context window | 1,000,000 tokens |
| Beta flag | `context-1m-2025-08-07` |
| Max history messages | 100 (no truncation) |
| Permission mode | `acceptEdits` |
| Default model | `claude-opus-4-6` |
| Router prefix | `/api/workspace` |
| WebSocket endpoint | `/api/workspace/ws` |
| Token estimation | `len(text) // 4` |
| Summary interval (Phase 2) | Every 50 messages |
| Max file upload (Phase 3) | 10MB |
| Python line length | 120 characters |
| Ruff target | Python 3.11 |
