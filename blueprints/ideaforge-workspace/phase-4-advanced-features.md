# Phase 4: Advanced Features — IdeaForge Workspace

## 1. What You Are Building

This is the final phase of the IdeaForge Workspace. You are adding five capabilities on top of the fully functional workspace built in Phases 1-3:

1. **Chat Forking** — Branch a conversation from any message, copying all context into a new tangent without polluting the original.
2. **Inject from Another Chat** — Pull selected messages from one conversation and prepend them as context in the current conversation's next user message.
3. **Export Chat to Markdown** — Download any conversation as a well-formatted `.md` file.
4. **Navigation Bar Integration** — Add persistent navigation between the main AutoForge app and the workspace.
5. **Keyboard Shortcuts** — Add workspace-specific shortcuts following the main app's pattern.
6. **Polish & Edge Cases** — Empty states, loading skeletons, error recovery, responsive sidebar, input persistence, scroll behavior, delete confirmation.

No new database tables are required. One new column is added to `workspace_conversations`.

---

## 2. Prerequisites (What Phases 1-3 Built)

Before starting, verify these exist and function correctly:

### Backend files
- `server/services/workspace_database.py` — SQLAlchemy models and CRUD for the global `~/.autoforge/workspace.db`
- `server/services/workspace_chat_session.py` — Claude SDK session management per conversation
- `server/routers/workspace.py` — FastAPI router with prefix `/api/workspace`
- Router registered in `server/routers/__init__.py` and `server/main.py`
- Cleanup function registered in `server/main.py` lifespan shutdown

### Frontend files
- `ui/src/pages/WorkspacePage.tsx` — Full-page workspace layout
- `ui/src/hooks/useWorkspaceChat.ts` — WebSocket chat hook
- `ui/src/lib/routes.ts` — Contains `isWorkspaceRoute()`
- `ui/src/main.tsx` — Routes `/#/workspace` to `WorkspacePage`
- Various workspace components in `ui/src/components/workspace/`

### Database schema (in `workspace_database.py`)
```sql
workspace_conversations (id, title, category, pinned, token_count, summary, summary_updated_at, created_at, updated_at)
workspace_messages (id, conversation_id, role, content, token_estimate, timestamp)
workspace_categories (id, name, color, sort_order, created_at)
workspace_summaries (id, conversation_id, summary, message_count, token_estimate, created_at)
workspace_library_files (id, conversation_id, filename, display_name, file_type, content, file_path, file_size, tags, active_in_context, created_at)
workspace_connected_repos (id, conversation_id, repo_url, repo_name, local_path, access_token_ref, branch, last_synced_at, created_at)
```

### Existing API endpoints
```
GET/POST   /api/workspace/conversations
GET/PATCH/DELETE /api/workspace/conversations/{id}
GET    /api/workspace/conversations/{id}/context-budget
GET    /api/workspace/conversations/{id}/summary
POST   /api/workspace/conversations/{id}/summarize
GET/POST/PATCH/DELETE /api/workspace/categories[/{id}]
GET    /api/workspace/search?q=...
WS     /api/workspace/ws/{conversation_id}
GET/POST /api/workspace/library/...
POST   /api/workspace/repos/connect
GET/DELETE /api/workspace/repos/...
```

---

## 3. Database Changes

### New column on `workspace_conversations`

Add `forked_from_id` to track fork lineage:

```python
# In workspace_database.py, WorkspaceConversation model:
forked_from_id = Column(Integer, ForeignKey("workspace_conversations.id"), nullable=True)
```

Add this column via an `ALTER TABLE` migration check in the engine initialization function. Follow the same pattern used elsewhere in the codebase — check if the column exists before adding:

```python
def _ensure_schema_up_to_date(engine: Engine) -> None:
    """Run lightweight schema migrations."""
    with engine.connect() as conn:
        # Check for forked_from_id column
        result = conn.execute(text("PRAGMA table_info(workspace_conversations)"))
        columns = {row[1] for row in result.fetchall()}
        if "forked_from_id" not in columns:
            conn.execute(text(
                "ALTER TABLE workspace_conversations ADD COLUMN forked_from_id INTEGER"
            ))
            conn.commit()
```

Call `_ensure_schema_up_to_date(engine)` inside `get_engine()` after `Base.metadata.create_all(engine)`.

---

## 4. Files to Create

### 4.1 `ui/src/components/workspace/ChatForkModal.tsx`

Modal for forking a conversation from a specific message.

```tsx
interface ChatForkModalProps {
  isOpen: boolean
  onClose: () => void
  conversationId: number
  conversationTitle: string
  messages: WorkspaceMessage[]       // All messages in the conversation
  onForkCreated: (newId: number) => void  // Navigate to new conversation
}
```

**Behavior:**
- Shows the conversation title and a scrollable list of messages
- Each message has a radio button to select the fork point
- Default selection: the last message (fork at current state)
- "Fork" button calls `POST /api/workspace/conversations/{id}/fork` with `{ fork_at_message_id }`
- Shows a loading spinner during the API call
- On success, calls `onForkCreated(newConversation.id)` which navigates to the new chat
- On error, shows an inline error message

**UI layout:**
```
+--------------------------------------+
|  Fork Conversation                   |
|  Create a branch from this chat      |
|                                      |
|  Select fork point:                  |
|  ○ [User] First message...       #1  |
|  ○ [Assistant] Response...       #2  |
|  ○ [User] Follow-up...          #3  |
|  ● [Assistant] Latest reply...   #4  | <-- default
|                                      |
|  Info: Messages after the selected   |
|  point will not be copied.           |
|                                      |
|              [Cancel]  [Fork]        |
+--------------------------------------+
```

Use `Dialog` / `DialogContent` / `DialogHeader` / `DialogTitle` / `DialogFooter` from `@/components/ui/dialog`. Use `Button` from `@/components/ui/button`. Use theme-agnostic Tailwind classes: `bg-background`, `text-foreground`, `border-border`, `text-muted-foreground`, `bg-muted`.

### 4.2 `ui/src/components/workspace/InjectFromChatModal.tsx`

Two-step modal for injecting messages from another conversation.

```tsx
interface InjectFromChatModalProps {
  isOpen: boolean
  onClose: () => void
  currentConversationId: number
  onInject: (injection: PendingInjection) => void
}

interface PendingInjection {
  sourceTitle: string
  sourceConversationId: number
  messages: { role: string; content: string }[]
}
```

**Step 1 — Select Source Conversation:**
- Fetch all conversations via `GET /api/workspace/conversations`
- Filter out the current conversation
- Show as a searchable list (use a text input for filtering by title)
- Each row shows title, message count, last updated
- Click a conversation to proceed to step 2

**Step 2 — Select Messages:**
- Fetch messages via `GET /api/workspace/conversations/{id}/messages?limit=100`
- Show messages with checkboxes
- "Select All" / "Deselect All" toggle at the top
- Show count of selected messages: "5 of 23 selected"
- "Inject" button calls `onInject()` with the selected messages
- "Back" button returns to step 1

**UI:** Two-step layout inside a single `DialogContent`. Use a state variable `step: 1 | 2` to toggle. Use the `Checkbox` component from `@/components/ui/checkbox`.

### 4.3 `ui/src/hooks/useWorkspaceKeyboardShortcuts.ts`

Custom hook for workspace keyboard shortcuts.

```tsx
interface UseWorkspaceKeyboardShortcutsOptions {
  onNewConversation: () => void
  onToggleLibrary: () => void
  onToggleSidebar: () => void
  onFocusSearch: () => void
  onExportChat: () => void
  onShowShortcutsHelp: () => void
  onFocusChatInput: () => void
  sidebarOpen: boolean
  libraryOpen: boolean
  hasActiveConversation: boolean
}

export function useWorkspaceKeyboardShortcuts(options: UseWorkspaceKeyboardShortcutsOptions): void
```

**Implementation pattern** — follow the exact pattern from `App.tsx` lines 146-242:

```tsx
import { useEffect } from 'react'

export function useWorkspaceKeyboardShortcuts(options: UseWorkspaceKeyboardShortcutsOptions): void {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if user is typing in an input or textarea
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        // Exception: allow "/" to focus chat input even from other inputs
        // Exception: allow Escape always
        if (e.key !== 'Escape') return
      }

      const isMod = e.metaKey || e.ctrlKey

      // Ctrl/Cmd+N: New conversation
      if (isMod && e.key === 'n') {
        e.preventDefault()
        options.onNewConversation()
        return
      }

      // Ctrl/Cmd+L: Toggle library panel
      if (isMod && e.key === 'l') {
        e.preventDefault()
        options.onToggleLibrary()
        return
      }

      // Ctrl/Cmd+B: Toggle sidebar
      if (isMod && e.key === 'b') {
        e.preventDefault()
        options.onToggleSidebar()
        return
      }

      // Ctrl/Cmd+F: Focus search in sidebar
      if (isMod && e.key === 'f') {
        e.preventDefault()
        options.onFocusSearch()
        return
      }

      // Ctrl/Cmd+E: Export current chat
      if (isMod && e.key === 'e' && options.hasActiveConversation) {
        e.preventDefault()
        options.onExportChat()
        return
      }

      // Escape: Close any open modal (handled by Dialog components natively,
      // but also close sidebar on mobile)
      if (e.key === 'Escape') {
        // Modals handle their own Escape; this is for non-modal closures
        return
      }

      // / : Focus chat input (only when not already in an input)
      if (e.key === '/' && !(e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement)) {
        e.preventDefault()
        options.onFocusChatInput()
        return
      }

      // ? : Show keyboard shortcuts help
      if (e.key === '?' && !(e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement)) {
        e.preventDefault()
        options.onShowShortcutsHelp()
        return
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [options])
}
```

### 4.4 `ui/src/components/workspace/WorkspaceKeyboardHelp.tsx`

Keyboard shortcuts help modal for the workspace. Follow the exact pattern of `/home/user/Greptacular/ui/src/components/KeyboardShortcutsHelp.tsx`.

```tsx
const shortcuts: Shortcut[] = [
  { key: 'Ctrl+N', description: 'New conversation' },
  { key: 'Ctrl+L', description: 'Toggle library panel' },
  { key: 'Ctrl+B', description: 'Toggle sidebar' },
  { key: 'Ctrl+F', description: 'Focus search' },
  { key: 'Ctrl+E', description: 'Export current chat', context: 'with active chat' },
  { key: '/', description: 'Focus chat input' },
  { key: '?', description: 'Show this help' },
  { key: 'Esc', description: 'Close modal' },
]
```

Display `Cmd` instead of `Ctrl` on macOS. Detect via `navigator.platform.includes('Mac')`.

---

## 5. Files to Modify

### 5.1 `server/services/workspace_database.py`

**Add the `forked_from_id` column** to the `WorkspaceConversation` model and the migration function as described in section 3.

**Add these new functions:**

#### `fork_conversation()`
```python
def fork_conversation(
    conversation_id: int,
    fork_at_message_id: int | None = None,
) -> dict:
    """Fork a conversation, copying messages up to fork_at_message_id.

    Args:
        conversation_id: The source conversation ID.
        fork_at_message_id: Copy messages up to and including this message.
            If None, copies all messages.

    Returns:
        Dict representing the new conversation (same shape as get_conversation).

    Raises:
        ValueError: If conversation_id or fork_at_message_id not found.
    """
    Session = _get_session_factory()
    with Session() as session:
        # 1. Load source conversation
        source = session.query(WorkspaceConversation).filter_by(id=conversation_id).first()
        if not source:
            raise ValueError(f"Conversation {conversation_id} not found")

        # 2. Determine title
        fork_title = f"{source.title or 'Untitled'} (fork)"

        # 3. Create new conversation
        new_conv = WorkspaceConversation(
            title=fork_title,
            category=source.category,
            pinned=False,
            token_count=0,
            forked_from_id=conversation_id,
        )
        session.add(new_conv)
        session.flush()  # Get the new ID

        # 4. Query messages to copy
        query = session.query(WorkspaceMessage).filter_by(
            conversation_id=conversation_id
        ).order_by(WorkspaceMessage.id.asc())

        if fork_at_message_id is not None:
            # Verify the message exists and belongs to this conversation
            fork_msg = session.query(WorkspaceMessage).filter_by(
                id=fork_at_message_id, conversation_id=conversation_id
            ).first()
            if not fork_msg:
                raise ValueError(
                    f"Message {fork_at_message_id} not found in conversation {conversation_id}"
                )
            query = query.filter(WorkspaceMessage.id <= fork_at_message_id)

        messages = query.all()

        # 5. Copy messages
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

        # 6. Copy active library files
        active_files = session.query(WorkspaceLibraryFile).filter_by(
            conversation_id=conversation_id,
            active_in_context=True,
        ).all()
        for f in active_files:
            new_file = WorkspaceLibraryFile(
                conversation_id=new_conv.id,
                filename=f.filename,
                display_name=f.display_name,
                file_type=f.file_type,
                content=f.content,
                file_path=f.file_path,
                file_size=f.file_size,
                tags=f.tags,
                active_in_context=True,
            )
            session.add(new_file)

        # 7. Copy connected repos
        repos = session.query(WorkspaceConnectedRepo).filter_by(
            conversation_id=conversation_id
        ).all()
        for r in repos:
            new_repo = WorkspaceConnectedRepo(
                conversation_id=new_conv.id,
                repo_url=r.repo_url,
                repo_name=r.repo_name,
                local_path=r.local_path,
                access_token_ref=r.access_token_ref,
                branch=r.branch,
            )
            session.add(new_repo)

        # 8. Set token count
        new_conv.token_count = total_tokens

        session.commit()

        # 9. Return the new conversation as a dict
        return {
            "id": new_conv.id,
            "title": new_conv.title,
            "category": new_conv.category,
            "pinned": new_conv.pinned,
            "token_count": new_conv.token_count,
            "forked_from_id": new_conv.forked_from_id,
            "created_at": new_conv.created_at.isoformat() if new_conv.created_at else None,
            "updated_at": new_conv.updated_at.isoformat() if new_conv.updated_at else None,
            "message_count": len(messages),
        }
```

#### `get_messages_paginated()`
```python
def get_messages_paginated(
    conversation_id: int,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """Get paginated messages for a conversation.

    Returns:
        Dict with "messages" list and "total" count.
    """
    Session = _get_session_factory()
    with Session() as session:
        total = session.query(func.count(WorkspaceMessage.id)).filter_by(
            conversation_id=conversation_id
        ).scalar() or 0

        messages = (
            session.query(WorkspaceMessage)
            .filter_by(conversation_id=conversation_id)
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
```

#### `export_conversation_markdown()`
```python
def export_conversation_markdown(conversation_id: int) -> str:
    """Export a conversation as formatted markdown.

    Returns:
        Markdown string.

    Raises:
        ValueError: If conversation not found.
    """
    Session = _get_session_factory()
    with Session() as session:
        conv = session.query(WorkspaceConversation).filter_by(id=conversation_id).first()
        if not conv:
            raise ValueError(f"Conversation {conversation_id} not found")

        messages = (
            session.query(WorkspaceMessage)
            .filter_by(conversation_id=conversation_id)
            .order_by(WorkspaceMessage.id.asc())
            .all()
        )

        # Build markdown
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

        # Summary section
        if conv.summary:
            lines.append("---")
            lines.append("")
            lines.append("## Summary")
            lines.append("")
            lines.append(conv.summary)
            lines.append("")

        # Messages section
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
```

### 5.2 `server/routers/workspace.py`

Add these three new endpoints to the existing workspace router.

#### Fork endpoint
```python
class ForkRequest(BaseModel):
    fork_at_message_id: int | None = None

@router.post("/conversations/{conversation_id}/fork")
async def fork_conversation(conversation_id: int, body: ForkRequest):
    """Fork a conversation from a specific message point."""
    from ..services.workspace_database import fork_conversation as db_fork

    try:
        new_conversation = db_fork(
            conversation_id=conversation_id,
            fork_at_message_id=body.fork_at_message_id,
        )
        return new_conversation
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

#### Paginated messages endpoint
```python
@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: int,
    limit: int = 50,
    offset: int = 0,
):
    """Get paginated messages for a conversation."""
    from ..services.workspace_database import get_messages_paginated

    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 200")
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset must be non-negative")

    return get_messages_paginated(
        conversation_id=conversation_id,
        limit=limit,
        offset=offset,
    )
```

#### Export endpoint
```python
from fastapi.responses import Response

@router.get("/conversations/{conversation_id}/export")
async def export_conversation(conversation_id: int, format: str = "markdown"):
    """Export a conversation as a downloadable file."""
    if format != "markdown":
        raise HTTPException(status_code=400, detail="Only 'markdown' format is supported")

    from ..services.workspace_database import export_conversation_markdown

    try:
        markdown_content = export_conversation_markdown(conversation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Sanitize filename
    from ..services.workspace_database import get_conversation
    conv = get_conversation(conversation_id)
    safe_title = (conv.get("title") or "conversation").replace(" ", "_")
    # Remove characters unsafe for filenames
    safe_title = "".join(c for c in safe_title if c.isalnum() or c in ("_", "-"))
    filename = f"{safe_title}_{conversation_id}.md"

    return Response(
        content=markdown_content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
```

#### Inject endpoint
```python
class InjectRequest(BaseModel):
    source_conversation_id: int
    message_ids: list[int] | str  # list of IDs or "all"

@router.post("/conversations/{conversation_id}/inject")
async def get_injection_content(conversation_id: int, body: InjectRequest):
    """Fetch formatted injection content from a source conversation.

    Returns the formatted injection text that the frontend will prepend
    to the user's next message. Does NOT modify any conversations.
    """
    from ..services.workspace_database import (
        get_conversation,
        get_messages_paginated,
    )

    # Validate source conversation exists
    source = get_conversation(body.source_conversation_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source conversation not found")

    # Validate target conversation exists
    target = get_conversation(conversation_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target conversation not found")

    source_title = source.get("title") or "Untitled"

    # Fetch messages from source
    result = get_messages_paginated(body.source_conversation_id, limit=500, offset=0)
    all_messages = result["messages"]

    if body.message_ids == "all":
        selected = all_messages
    else:
        id_set = set(body.message_ids)
        selected = [m for m in all_messages if m["id"] in id_set]

    if not selected:
        raise HTTPException(status_code=400, detail="No messages selected for injection")

    # Format injection content
    formatted_messages = []
    for m in selected:
        role_label = "User" if m["role"] == "user" else "Assistant"
        formatted_messages.append(f"{role_label}: {m['content']}")

    return {
        "source_title": source_title,
        "source_conversation_id": body.source_conversation_id,
        "message_count": len(selected),
        "formatted_messages": formatted_messages,
    }
```

### 5.3 `ui/src/lib/workspaceApi.ts`

Add these API functions (create this file if it does not exist, or add to the existing workspace API module):

```typescript
const API_BASE = '/api'

// ---- Fork ----

export interface ForkRequest {
  fork_at_message_id: number | null
}

export interface ForkResponse {
  id: number
  title: string
  category: string | null
  pinned: boolean
  token_count: number
  forked_from_id: number
  created_at: string | null
  updated_at: string | null
  message_count: number
}

export async function forkConversation(
  conversationId: number,
  forkAtMessageId: number | null = null,
): Promise<ForkResponse> {
  const res = await fetch(`${API_BASE}/workspace/conversations/${conversationId}/fork`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ fork_at_message_id: forkAtMessageId }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Fork failed' }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

// ---- Paginated Messages ----

export interface WorkspaceMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  token_estimate: number | null
  timestamp: string | null
}

export interface PaginatedMessages {
  messages: WorkspaceMessage[]
  total: number
}

export async function getConversationMessages(
  conversationId: number,
  limit = 50,
  offset = 0,
): Promise<PaginatedMessages> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  const res = await fetch(`${API_BASE}/workspace/conversations/${conversationId}/messages?${params}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to fetch messages' }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

// ---- Export ----

export async function exportConversationMarkdown(conversationId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/workspace/conversations/${conversationId}/export?format=markdown`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Export failed' }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }

  // Extract filename from Content-Disposition header
  const disposition = res.headers.get('Content-Disposition')
  let filename = 'conversation.md'
  if (disposition) {
    const match = disposition.match(/filename="?([^"]+)"?/)
    if (match) filename = match[1]
  }

  // Download the file
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// ---- Inject ----

export interface InjectRequest {
  source_conversation_id: number
  message_ids: number[] | 'all'
}

export interface InjectResponse {
  source_title: string
  source_conversation_id: number
  message_count: number
  formatted_messages: string[]
}

export async function getInjectionContent(
  targetConversationId: number,
  sourceConversationId: number,
  messageIds: number[] | 'all',
): Promise<InjectResponse> {
  const res = await fetch(`${API_BASE}/workspace/conversations/${targetConversationId}/inject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      source_conversation_id: sourceConversationId,
      message_ids: messageIds,
    }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Inject failed' }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}
```

### 5.4 `ui/src/hooks/useWorkspaceChat.ts` — Add Injection State

Add pending injection state management to the existing hook. The exact location depends on Phase 1's implementation, but the pattern is:

```typescript
// Add to the hook's state:
const [pendingInjection, setPendingInjection] = useState<{
  sourceTitle: string
  messages: { role: string; content: string }[]
} | null>(null)

// Modify the sendMessage function to prepend injection content:
function sendMessage(content: string) {
  let fullMessage = content

  if (pendingInjection) {
    const injectedLines = [
      `--- Injected from "${pendingInjection.sourceTitle}" ---`,
      ...pendingInjection.messages.map(
        m => `${m.role === 'user' ? 'User' : 'Assistant'}: ${m.content}`
      ),
      `--- End injection ---`,
      '',
      content,
    ]
    fullMessage = injectedLines.join('\n')
    setPendingInjection(null)
  }

  // Send fullMessage via WebSocket (existing logic)
  ws.current?.send(JSON.stringify({ type: 'message', content: fullMessage }))
}

// Export the injection state and setter:
return {
  // ...existing returns
  pendingInjection,
  setPendingInjection,
}
```

### 5.5 `ui/src/pages/WorkspacePage.tsx` — Integrate All Features

This is the primary integration point. Add the following to the existing `WorkspacePage`:

#### State additions
```typescript
const [showForkModal, setShowForkModal] = useState(false)
const [showInjectModal, setShowInjectModal] = useState(false)
const [showKeyboardHelp, setShowKeyboardHelp] = useState(false)
const chatInputRef = useRef<HTMLTextAreaElement>(null)
const searchInputRef = useRef<HTMLInputElement>(null)
```

#### Import and call the keyboard shortcuts hook
```typescript
import { useWorkspaceKeyboardShortcuts } from '../hooks/useWorkspaceKeyboardShortcuts'

// Inside the component:
useWorkspaceKeyboardShortcuts({
  onNewConversation: () => { /* create new conversation logic */ },
  onToggleLibrary: () => setLibraryOpen(prev => !prev),
  onToggleSidebar: () => setSidebarOpen(prev => !prev),
  onFocusSearch: () => {
    if (!sidebarOpen) setSidebarOpen(true)
    // Use setTimeout to allow sidebar to render before focusing
    setTimeout(() => searchInputRef.current?.focus(), 100)
  },
  onExportChat: () => {
    if (activeConversationId) {
      exportConversationMarkdown(activeConversationId)
    }
  },
  onShowShortcutsHelp: () => setShowKeyboardHelp(true),
  onFocusChatInput: () => chatInputRef.current?.focus(),
  sidebarOpen,
  libraryOpen,
  hasActiveConversation: !!activeConversationId,
})
```

#### Add action buttons to the chat header area

In the chat header (the bar above the message area that shows the conversation title), add a dropdown menu with these actions:

```tsx
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { MoreHorizontal, GitFork, ArrowDownToLine, Download } from 'lucide-react'

// In the chat header:
<DropdownMenu>
  <DropdownMenuTrigger asChild>
    <Button variant="ghost" size="sm">
      <MoreHorizontal size={16} />
    </Button>
  </DropdownMenuTrigger>
  <DropdownMenuContent align="end">
    <DropdownMenuItem onClick={() => setShowForkModal(true)}>
      <GitFork size={14} className="mr-2" />
      Fork Chat
    </DropdownMenuItem>
    <DropdownMenuItem onClick={() => setShowInjectModal(true)}>
      <ArrowDownToLine size={14} className="mr-2" />
      Inject from Chat
    </DropdownMenuItem>
    <DropdownMenuItem onClick={() => exportConversationMarkdown(activeConversationId!)}>
      <Download size={14} className="mr-2" />
      Export as Markdown
    </DropdownMenuItem>
  </DropdownMenuContent>
</DropdownMenu>
```

#### Add injection indicator above the chat input

When `pendingInjection` is set, show a small banner above the textarea:

```tsx
{pendingInjection && (
  <div className="flex items-center gap-2 px-3 py-2 bg-muted border border-border rounded-t-md text-sm text-muted-foreground">
    <ArrowDownToLine size={14} />
    <span>
      Injecting {pendingInjection.messages.length} message{pendingInjection.messages.length !== 1 ? 's' : ''} from "{pendingInjection.sourceTitle}"
    </span>
    <button
      onClick={() => setPendingInjection(null)}
      className="ml-auto text-muted-foreground hover:text-foreground"
    >
      <X size={14} />
    </button>
  </div>
)}
```

#### Render the modals

```tsx
{showForkModal && activeConversationId && (
  <ChatForkModal
    isOpen={showForkModal}
    onClose={() => setShowForkModal(false)}
    conversationId={activeConversationId}
    conversationTitle={activeConversation?.title || 'Untitled'}
    messages={messages}
    onForkCreated={(newId) => {
      setShowForkModal(false)
      setActiveConversationId(newId)
      // Invalidate conversation list query to show the fork
      queryClient.invalidateQueries({ queryKey: ['workspace-conversations'] })
    }}
  />
)}

{showInjectModal && activeConversationId && (
  <InjectFromChatModal
    isOpen={showInjectModal}
    onClose={() => setShowInjectModal(false)}
    currentConversationId={activeConversationId}
    onInject={(injection) => {
      setPendingInjection({
        sourceTitle: injection.sourceTitle,
        messages: injection.messages,
      })
      setShowInjectModal(false)
    }}
  />
)}

<WorkspaceKeyboardHelp
  isOpen={showKeyboardHelp}
  onClose={() => setShowKeyboardHelp(false)}
/>
```

### 5.6 `ui/src/lib/routes.ts` — Already exists from Phase 1

Verify `isWorkspaceRoute()` exists. No changes needed if Phase 1 was implemented correctly.

### 5.7 `ui/src/main.tsx` — Already exists from Phase 1

Verify the workspace route is handled. No changes needed if Phase 1 was implemented correctly.

### 5.8 `ui/src/App.tsx` — Add Workspace Navigation Link

Add a "Workspace" link in the header, next to the docs button. Insert this before the `{/* Docs link */}` comment:

```tsx
{/* Workspace link */}
<Button
  onClick={() => { window.location.hash = '#/workspace' }}
  variant="outline"
  size="sm"
  title="IdeaForge Workspace"
  aria-label="Open Workspace"
>
  <MessageSquare size={18} />
</Button>
```

Import `MessageSquare` from `lucide-react` (add to existing imports).

### 5.9 `ui/src/pages/WorkspacePage.tsx` — Add Navigation Bar

Add a top navigation bar at the very top of the workspace layout, above the three-panel content:

```tsx
{/* Navigation Bar */}
<div className="h-10 border-b border-border bg-card flex items-center px-4 gap-3 shrink-0">
  <button
    onClick={() => { window.location.hash = '' }}
    className="text-sm text-muted-foreground hover:text-foreground transition-colors"
  >
    AutoForge
  </button>
  <span className="text-border text-sm">/</span>
  <span className="text-sm font-medium text-foreground">Workspace</span>
  <div className="flex-1" />
  <button
    onClick={() => setShowKeyboardHelp(true)}
    className="text-xs text-muted-foreground hover:text-foreground transition-colors"
    title="Keyboard shortcuts (?)"
  >
    <Keyboard size={14} />
  </button>
</div>
```

Import `Keyboard` from `lucide-react`.

---

## 6. API Endpoint Specifications (Complete Reference)

### New Endpoints Added in Phase 4

| Method | Path | Request Body | Response | Description |
|--------|------|-------------|----------|-------------|
| `POST` | `/api/workspace/conversations/{id}/fork` | `{ fork_at_message_id: int \| null }` | `ForkResponse` (conversation object with `message_count`) | Create a forked copy of a conversation |
| `GET` | `/api/workspace/conversations/{id}/messages` | Query: `limit`, `offset` | `{ messages: [...], total: int }` | Paginated message list |
| `GET` | `/api/workspace/conversations/{id}/export` | Query: `format=markdown` | `text/markdown` file download | Export conversation as markdown |
| `POST` | `/api/workspace/conversations/{id}/inject` | `{ source_conversation_id: int, message_ids: int[] \| "all" }` | `{ source_title, message_count, formatted_messages }` | Get formatted injection content |

### Response Schemas

**ForkResponse:**
```json
{
  "id": 42,
  "title": "SaaS Ideas (fork)",
  "category": "brainstorming",
  "pinned": false,
  "token_count": 15000,
  "forked_from_id": 7,
  "created_at": "2026-02-16T10:30:00",
  "updated_at": "2026-02-16T10:30:00",
  "message_count": 12
}
```

**PaginatedMessages:**
```json
{
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "Tell me about...",
      "token_estimate": 150,
      "timestamp": "2026-02-16T10:00:00"
    }
  ],
  "total": 47
}
```

**InjectResponse:**
```json
{
  "source_title": "SaaS Ideas Chat",
  "source_conversation_id": 7,
  "message_count": 5,
  "formatted_messages": [
    "User: What about a project management tool?",
    "Assistant: Here are some ideas..."
  ]
}
```

---

## 7. Component Specifications

### 7.1 ChatForkModal

**Props:** See section 4.1.

**Internal state:**
- `selectedMessageId: number | null` — defaults to last message ID
- `isForking: boolean` — loading state
- `error: string | null` — error display

**Data flow:**
1. User opens modal via chat header dropdown
2. Modal renders message list from props (already loaded in the chat view)
3. User selects a fork point via radio buttons
4. On "Fork" click: call `forkConversation(conversationId, selectedMessageId)`
5. On success: call `onForkCreated(response.id)`
6. On error: set error state, show inline

### 7.2 InjectFromChatModal

**Props:** See section 4.2.

**Internal state:**
- `step: 1 | 2`
- `searchQuery: string`
- `selectedSourceId: number | null`
- `sourceMessages: WorkspaceMessage[]`
- `selectedMessageIds: Set<number>`
- `isLoading: boolean`

**Data flow:**
1. Step 1: Fetch conversations, filter by search, user clicks one
2. Step 2: Fetch messages for selected conversation via `getConversationMessages()`
3. User toggles checkboxes to select messages
4. On "Inject": format selected messages into `PendingInjection`, call `onInject()`
5. The `useWorkspaceChat` hook stores the injection and prepends it on next send

### 7.3 WorkspaceKeyboardHelp

Same pattern as `KeyboardShortcutsHelp.tsx`. Show `Cmd` on macOS, `Ctrl` on other platforms.

---

## 8. Polish & Edge Cases

These requirements must be addressed across all workspace components. If any are already handled by Phase 1-3 implementations, verify they work correctly.

### 8.1 Empty States

When no conversations exist, the main chat area should show:

```tsx
<div className="flex-1 flex flex-col items-center justify-center text-center p-8">
  <MessageSquare size={48} className="text-muted-foreground/30 mb-4" />
  <h2 className="text-lg font-semibold mb-2">No conversations yet</h2>
  <p className="text-muted-foreground text-sm mb-6 max-w-sm">
    Start your first conversation to brainstorm ideas, explore concepts, or get help with your projects.
  </p>
  <Button onClick={onNewConversation}>
    <Plus size={16} className="mr-2" />
    Start a Conversation
  </Button>
</div>
```

### 8.2 Loading States

- **Conversation list in sidebar:** Show 4-5 skeleton rows (`bg-muted animate-pulse rounded h-10 w-full`)
- **Message area when loading a conversation:** Show 3 skeleton message bubbles
- **Fork/inject modals:** Show `Loader2` spinner with `animate-spin` during API calls

### 8.3 Error Handling

- **WebSocket disconnection:** Show a reconnecting banner at the top of the chat area:
  ```tsx
  {connectionStatus === 'disconnected' && (
    <div className="bg-destructive/10 border-b border-destructive/20 px-4 py-2 text-sm text-destructive flex items-center gap-2">
      <WifiOff size={14} />
      Connection lost. Reconnecting...
    </div>
  )}
  ```
- **API errors:** Show as inline error messages in modals (not toasts, since the workspace has no toast system defined). Use `text-destructive` for error text.

### 8.4 Responsive Sidebar

The sidebar should auto-collapse on viewports narrower than 768px:

```typescript
// In WorkspacePage, add:
const [sidebarOpen, setSidebarOpen] = useState(() => window.innerWidth >= 768)

useEffect(() => {
  const handleResize = () => {
    if (window.innerWidth < 768) {
      setSidebarOpen(false)
    }
  }
  window.addEventListener('resize', handleResize)
  return () => window.removeEventListener('resize', handleResize)
}, [])
```

On mobile, the sidebar should overlay the content with a backdrop. On desktop (>= 768px), it should be a normal side panel.

### 8.5 Conversation Title Auto-Generation

Verify that Phase 1 implemented this: if a conversation's title is `null` after the first user message, auto-set it to the first 50 characters of the message content. This should happen on the backend in the WebSocket message handler or in the database function that processes the first message.

If not already implemented, add this to `workspace_database.py`:

```python
def auto_set_title_if_needed(conversation_id: int, first_message_content: str) -> None:
    """Set conversation title from first message if title is still null."""
    Session = _get_session_factory()
    with Session() as session:
        conv = session.query(WorkspaceConversation).filter_by(id=conversation_id).first()
        if conv and not conv.title:
            # Take first 50 chars, strip whitespace, add ellipsis if truncated
            title = first_message_content.strip()[:50]
            if len(first_message_content.strip()) > 50:
                title += "..."
            conv.title = title
            session.commit()
```

Call this from the WebSocket handler when the first user message is received.

### 8.6 Delete Confirmation

Wrap the conversation delete action in a confirmation dialog. Use the `Dialog` component:

```tsx
const [showDeleteConfirm, setShowDeleteConfirm] = useState<number | null>(null)

// In the sidebar, the delete button should set showDeleteConfirm to the conversation ID
// Then render:
<Dialog open={!!showDeleteConfirm} onOpenChange={(open) => !open && setShowDeleteConfirm(null)}>
  <DialogContent className="sm:max-w-sm">
    <DialogHeader>
      <DialogTitle>Delete Conversation</DialogTitle>
    </DialogHeader>
    <p className="text-sm text-muted-foreground">
      This action cannot be undone. All messages in this conversation will be permanently deleted.
    </p>
    <DialogFooter>
      <Button variant="outline" onClick={() => setShowDeleteConfirm(null)}>Cancel</Button>
      <Button variant="destructive" onClick={() => handleDelete(showDeleteConfirm!)}>
        Delete
      </Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

### 8.7 Scroll Behavior

In the chat messages area, implement smart auto-scroll:

```typescript
const messagesContainerRef = useRef<HTMLDivElement>(null)
const [isUserScrolledUp, setIsUserScrolledUp] = useState(false)

// Track user scroll position
const handleScroll = useCallback(() => {
  const container = messagesContainerRef.current
  if (!container) return
  const distanceFromBottom = container.scrollHeight - container.scrollTop - container.clientHeight
  setIsUserScrolledUp(distanceFromBottom > 100) // 100px threshold
}, [])

// Auto-scroll to bottom on new messages, unless user has scrolled up
useEffect(() => {
  if (!isUserScrolledUp) {
    messagesContainerRef.current?.scrollTo({
      top: messagesContainerRef.current.scrollHeight,
      behavior: 'smooth',
    })
  }
}, [messages.length, isUserScrolledUp])
```

### 8.8 Input Persistence (Draft Saving)

Save unsent draft input per conversation in localStorage:

```typescript
const DRAFT_KEY_PREFIX = 'workspace-draft-'

// Load draft when switching conversations
useEffect(() => {
  if (activeConversationId) {
    const draft = localStorage.getItem(`${DRAFT_KEY_PREFIX}${activeConversationId}`)
    setInputValue(draft || '')
  }
}, [activeConversationId])

// Save draft on input change (debounced)
useEffect(() => {
  if (!activeConversationId) return
  const timer = setTimeout(() => {
    if (inputValue) {
      localStorage.setItem(`${DRAFT_KEY_PREFIX}${activeConversationId}`, inputValue)
    } else {
      localStorage.removeItem(`${DRAFT_KEY_PREFIX}${activeConversationId}`)
    }
  }, 300)
  return () => clearTimeout(timer)
}, [inputValue, activeConversationId])

// Clear draft after sending a message
function handleSend() {
  sendMessage(inputValue)
  setInputValue('')
  if (activeConversationId) {
    localStorage.removeItem(`${DRAFT_KEY_PREFIX}${activeConversationId}`)
  }
}
```

---

## 9. Testing Checklist

Run these verifications after implementation:

### Python Backend

```bash
# Lint
cd /home/user/Greptacular && ruff check server/services/workspace_database.py server/routers/workspace.py

# Type check (if mypy is configured for server/)
mypy server/services/workspace_database.py server/routers/workspace.py --ignore-missing-imports
```

### React Frontend

```bash
cd /home/user/Greptacular/ui

# Lint
npm run lint

# Type check + build
npm run build
```

### Manual Testing Scenarios

1. **Fork:**
   - Open a conversation with 5+ messages
   - Click "Fork Chat" from the dropdown
   - Select the 3rd message as fork point
   - Verify the new conversation has exactly 3 messages
   - Verify the original conversation is unchanged
   - Verify the sidebar shows the new "(fork)" conversation
   - Fork again at the latest message (default) — verify all messages are copied

2. **Inject:**
   - Open conversation A, send some messages
   - Open conversation B
   - Click "Inject from Chat"
   - Search for conversation A
   - Select 2 messages from A
   - Verify the injection indicator appears above the input
   - Send a message in B
   - Verify the sent message includes the injected content prepended
   - Verify the injection indicator disappears after sending

3. **Export:**
   - Open a conversation with messages and a summary
   - Click "Export as Markdown"
   - Verify a `.md` file downloads
   - Open the file and verify it contains: title, category, creation date, message count, token count, summary section, all messages with role labels and timestamps

4. **Navigation:**
   - From the main AutoForge app, click the Workspace icon — verify it navigates to `/#/workspace`
   - From the workspace, click "AutoForge" in the breadcrumb — verify it navigates back to `/#/`

5. **Keyboard Shortcuts:**
   - Press `Ctrl+N` in workspace — verify new conversation is created
   - Press `Ctrl+B` — verify sidebar toggles
   - Press `Ctrl+L` — verify library panel toggles
   - Press `/` — verify chat input is focused
   - Press `?` — verify keyboard help modal opens
   - Press `Ctrl+E` with active chat — verify export triggers
   - Verify shortcuts do NOT fire when typing in the chat input (except Escape)

6. **Polish:**
   - Delete a conversation — verify confirmation dialog appears
   - Resize browser below 768px — verify sidebar collapses
   - Start a new conversation, send first message — verify title auto-generates
   - Type a message, switch conversations, switch back — verify draft is preserved
   - Scroll up in a long conversation — verify new messages do NOT auto-scroll
   - Scroll back to bottom — verify auto-scroll resumes
   - Disconnect network — verify reconnection banner appears

---

## 10. Important Reminders

1. **Theme-agnostic styling:** Use only Tailwind tokens from the `@theme` block in `globals.css`. Use `bg-background`, `text-foreground`, `bg-card`, `border-border`, `text-muted-foreground`, `bg-muted`, `text-destructive`, `bg-primary`, `text-primary-foreground`, etc. Never hardcode hex colors. The workspace must look correct in all 6 themes (Twitter, Claude, Neo Brutalism, Retro Arcade, Aurora, Business) and in both light and dark mode.

2. **Routing:** There is NO React Router in this project. Navigation uses `window.location.hash`. Route detection uses functions in `ui/src/lib/routes.ts`. The workspace route is `/#/workspace`.

3. **Component library:** Use the existing Radix-based components in `ui/src/components/ui/` — `Button`, `Dialog`, `DialogContent`, `DialogHeader`, `DialogTitle`, `DialogFooter`, `DropdownMenu`, `DropdownMenuContent`, `DropdownMenuItem`, `DropdownMenuTrigger`, `Input`, `Textarea`, `Checkbox`, `Badge`, `Card`, `Separator`, `Label`, `Switch`. Do not install new UI libraries.

4. **Icons:** Use `lucide-react` for all icons. It is already installed.

5. **Database:** The workspace database is global at `~/.autoforge/workspace.db`. It is NOT per-project. All database functions in `workspace_database.py` should use the global engine/session factory pattern, not accept a `project_dir` parameter.

6. **Router prefix:** All workspace API endpoints are under `APIRouter(prefix="/api/workspace")`. The WebSocket is at `/api/workspace/ws/{conversation_id}`.

7. **No new dependencies:** All features in this phase can be built with existing dependencies. No new pip or npm packages are needed.

8. **SQLAlchemy patterns:** Follow the same patterns as `assistant_database.py` — engine caching with thread locks, `_utc_now()` for timestamps, session factory pattern, `DeclarativeBase` (SQLAlchemy 2.0 style).

9. **File organization:** Place all new workspace components in `ui/src/components/workspace/`. Place the keyboard shortcuts hook in `ui/src/hooks/`. Place the API module in `ui/src/lib/`.

10. **Pydantic models:** Define request/response models inline in the router file using `BaseModel`. Follow the pattern in `server/routers/assistant_chat.py`.

11. **Error handling on the backend:** Use `raise HTTPException(status_code=..., detail=...)` for all error responses. Use `ValueError` in database functions and catch them in router handlers.

12. **Lint and type check:** Before considering the implementation complete, run `ruff check .` from the project root and `npm run build` from the `ui/` directory. Fix ALL errors. The CI pipeline (`.github/workflows/ci.yml`) will catch any regressions.
