# IdeaForge: Million-Token Workspace Chat

## What This Is

A persistent, multi-chat workspace built into AutoForge that gives you a personalized Claude Code experience with the full 1M token context window. Each chat is its own persistent context — you start a conversation about an idea, and that context lives forever. Come back a month later, it's right where you left it. No handoffs, no context destruction, no re-explaining.

Think of it as: **Claude Code as a web app, but customized with features Claude Code doesn't have** — file library, GitHub repo connections, chat organization, context budget visualization, and the ability to take an idea from first word to fully coded feature all in one window.

## Why This Matters

Right now, the workflow is broken:
1. You rant about an idea in one chat
2. Get a handoff/spec
3. Open a NEW agent with zero context about the conversation
4. Paste fragments of the old chat to catch it up
5. Lose 40-60% of the nuance every time

With IdeaForge: you rant, spec, blueprint, AND build — all in the same 1M token window. No handoffs. The agent that heard you describe the idea is the same one that codes it.

## What Already Exists (Build ON This)

AutoForge already has an assistant chat system that's ~60% of the way there:

**Existing infrastructure to extend (DO NOT rebuild from scratch):**
- `server/services/assistant_chat_session.py` — Session management with Claude SDK
- `server/services/assistant_database.py` — SQLite persistence (`conversations` + `conversation_messages` tables)
- `server/routers/assistant_chat.py` — REST + WebSocket API
- `ui/src/components/AssistantPanel.tsx` — Slide-in panel UI
- `ui/src/components/AssistantChat.tsx` — Chat interface with streaming
- `ui/src/hooks/useAssistantChat.ts` — WebSocket hook with reconnection

**What's already working:**
- SQLite conversation persistence (come back later, it's there)
- Multi-conversation history with sidebar browsing
- WebSocket streaming with real-time chunks
- Claude SDK integration with model/provider selection
- Conversation resume with last 35 messages as context
- Structured question/answer UI (ask_user tool)

**What's currently limited (the gaps to fill):**
- READ-ONLY tools only (Read, Glob, Grep, WebFetch, WebSearch) — needs Write/Edit
- Scoped to one project directory — needs GitHub repo access + arbitrary paths
- No file upload/library system
- No context budget visualization
- No chat organization (categories, search, pinning)
- Side panel layout — needs full-page mode for serious work
- 35-message history cap — needs smarter context management for 1M window

---

## Architecture

### New Route: `/workspace` (Full-Page Chat Experience)

This is NOT the existing assistant side panel. This is a **full-page workspace** accessible from the main nav. The assistant panel stays as-is for quick project Q&A.

```
/workspace
  ├── Sidebar (left, collapsible)
  │   ├── New Chat button
  │   ├── Search chats
  │   ├── Chat Categories (collapsible groups)
  │   │   ├── "AutoForge Development"
  │   │   ├── "SaaS Ideas"
  │   │   ├── "Client Projects"
  │   │   └── "Uncategorized"
  │   └── Chat List (per category)
  │       ├── Chat title
  │       ├── Last message preview
  │       ├── Timestamp (relative)
  │       ├── Pin/Star indicator
  │       └── Context usage bar (mini)
  │
  ├── Main Chat Area (center)
  │   ├── Chat Header
  │   │   ├── Chat title (editable)
  │   │   ├── Category selector
  │   │   ├── Context Budget Bar (tokens used / 1M)
  │   │   ├── Connected Repos indicator
  │   │   ├── Fork Chat button
  │   │   └── Settings (model, tools)
  │   ├── Auto-Summary Pin (collapsible, at top)
  │   ├── Messages Area (streaming, markdown)
  │   └── Input Area
  │       ├── Textarea (auto-resize, Shift+Enter for newline)
  │       ├── File attach button (from library or upload)
  │       ├── Inject from another chat button
  │       └── Send button
  │
  └── Library Panel (right, togglable)
      ├── Global Files (always available)
      │   ├── Docs (WordPress, Elementor, etc.)
      │   ├── Specs (agent_os_system.md, etc.)
      │   └── Templates
      ├── Chat Files (per-conversation)
      └── Connected Repos
          ├── Repo browser (tree view)
          └── File preview
```

### Database Schema Extensions

Extend the existing `assistant_database.py` — do NOT create a separate database.

```sql
-- Extend existing conversations table with new columns
ALTER TABLE conversations ADD COLUMN category VARCHAR(100) DEFAULT 'Uncategorized';
ALTER TABLE conversations ADD COLUMN pinned BOOLEAN DEFAULT FALSE;
ALTER TABLE conversations ADD COLUMN token_count INTEGER DEFAULT 0;
ALTER TABLE conversations ADD COLUMN summary TEXT;  -- auto-generated summary
ALTER TABLE conversations ADD COLUMN summary_updated_at DATETIME;

-- New table: file library (global + per-chat)
CREATE TABLE library_files (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER NULLABLE,  -- NULL = global, set = per-chat
    filename VARCHAR(500) NOT NULL,
    display_name VARCHAR(200),
    file_type VARCHAR(50),  -- 'doc', 'spec', 'template', 'upload', 'repo_file'
    content TEXT,  -- file content (cached for context injection)
    file_size INTEGER,
    tags VARCHAR(500),  -- comma-separated tags for organization
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

-- New table: connected GitHub repos
CREATE TABLE connected_repos (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER NULLABLE,  -- NULL = global, set = per-chat
    repo_url VARCHAR(500) NOT NULL,
    repo_name VARCHAR(200) NOT NULL,
    access_token_ref VARCHAR(100),  -- reference to secure token storage, NOT the token itself
    branch VARCHAR(100) DEFAULT 'main',
    last_synced_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL
);

-- New table: chat categories
CREATE TABLE chat_categories (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    color VARCHAR(7),  -- hex color for sidebar indicator
    sort_order INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- New table: auto-summaries (snapshots every ~50 messages)
CREATE TABLE conversation_summaries (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER NOT NULL,
    summary TEXT NOT NULL,
    message_count INTEGER,  -- messages covered at time of summary
    token_estimate INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);
```

### Backend: New Service + Extended Router

#### `server/services/workspace_chat_session.py`

Fork from `assistant_chat_session.py` but with these critical differences:

**1. Full Agent Mode (NOT read-only):**
```python
WORKSPACE_TOOLS = [
    # Read capabilities
    "Read", "Glob", "Grep", "WebFetch", "WebSearch",
    # Write capabilities (THE KEY DIFFERENCE)
    "Write", "Edit",
    # Bash for git operations, builds, etc.
    "Bash",
]
```

**2. Permission Mode:**
```python
# Use acceptEdits instead of bypassPermissions
# This allows write/edit but still shows the user what's happening
permission_mode = "acceptEdits"
```

**3. GitHub Repo Access:**
When a repo is connected, add its path to the allowed read/write paths:
```python
# Clone repo to ~/.autoforge/workspace/repos/{repo_name}/
# Add to Claude SDK's allowed paths
# Refresh on each session start (git pull)
```

**4. Context Management for 1M Window:**
```python
# Instead of 35-message cap, use intelligent context loading:
# 1. Always include: auto-summary of conversation so far
# 2. Include: last 100 messages verbatim
# 3. Include: any library files toggled "active" in this chat
# 4. Include: connected repo file tree (not contents, just structure)
# 5. Track token count and update conversation.token_count
```

**5. File Library Integration:**
```python
# When user toggles a library file into chat:
# 1. Read file content
# 2. Prepend to next message as context: "--- Library file: {name} ---\n{content}\n---"
# 3. Track which files are "active" in this conversation
# Claude sees the file content in its context window
```

**6. Auto-Summary Generation:**
```python
# Every 50 messages, trigger summary generation:
# 1. Collect all messages since last summary
# 2. Ask Claude (in a side-channel, NOT in the main conversation) to summarize
# 3. Store in conversation_summaries table
# 4. Pin summary at top of chat UI
# The summary is always included in context for resumed conversations
```

#### `server/services/workspace_database.py`

Extend `assistant_database.py` with the new tables. Key operations:

```python
# File Library
def add_library_file(conversation_id, filename, content, file_type, tags)
def get_library_files(conversation_id=None)  # None = global files
def remove_library_file(file_id)
def get_active_files_for_chat(conversation_id)  # files toggled into context

# GitHub Repos
def connect_repo(conversation_id, repo_url, token_ref, branch)
def disconnect_repo(repo_id)
def get_connected_repos(conversation_id=None)
def update_repo_sync_time(repo_id)

# Categories
def create_category(name, color)
def list_categories()
def update_conversation_category(conversation_id, category_id)

# Summaries
def add_summary(conversation_id, summary, message_count, token_estimate)
def get_latest_summary(conversation_id)
def get_all_summaries(conversation_id)

# Token tracking
def update_token_count(conversation_id, token_count)
```

#### `server/routers/workspace.py`

New router at `/api/workspace`:

```python
# Chat Management
GET    /conversations                    # List all workspace conversations
POST   /conversations                    # Create new conversation
GET    /conversations/{id}               # Get conversation with messages
DELETE /conversations/{id}               # Delete conversation
PATCH  /conversations/{id}               # Update title, category, pinned

# WebSocket (main chat)
WS     /ws/{conversation_id}             # Stream chat (same protocol as assistant)

# File Library
GET    /library                          # List all global library files
GET    /library/{conversation_id}        # List chat-specific files
POST   /library/upload                   # Upload file (global or per-chat)
DELETE /library/{file_id}                # Remove file
POST   /library/{file_id}/toggle/{cid}   # Toggle file into/out of chat context

# GitHub Repos
POST   /repos/connect                    # Connect repo (url + token)
DELETE /repos/{repo_id}                  # Disconnect repo
GET    /repos/{repo_id}/tree             # Get repo file tree
GET    /repos/{repo_id}/file             # Read specific file from repo
POST   /repos/{repo_id}/sync            # Pull latest from remote

# Categories
GET    /categories                       # List categories
POST   /categories                       # Create category
PATCH  /categories/{id}                  # Update category
DELETE /categories/{id}                  # Delete category

# Chat Operations
POST   /conversations/{id}/fork          # Fork conversation (copy context to new chat)
POST   /conversations/{id}/inject        # Inject messages from another chat
GET    /conversations/{id}/summary       # Get auto-summary
POST   /conversations/{id}/summarize     # Force regenerate summary
GET    /conversations/{id}/context-budget # Get token usage breakdown
```

### Frontend: New Page + Components

#### New Route: `/#/workspace`

Add to `App.tsx` router alongside existing routes.

#### `ui/src/pages/WorkspacePage.tsx`

Full-page layout with three-panel design (sidebar, chat, library panel).

#### Key Components

```
ui/src/components/workspace/
├── WorkspaceSidebar.tsx        # Left panel: categories, chat list, search
├── WorkspaceChat.tsx           # Center: main chat area (extend AssistantChat)
├── WorkspaceChatHeader.tsx     # Title, category, context bar, fork button
├── WorkspaceLibrary.tsx        # Right panel: file browser + repo tree
├── ContextBudgetBar.tsx        # Visual bar showing token usage (used/1M)
├── FileLibraryBrowser.tsx      # Tree view of global + chat files
├── RepoConnector.tsx           # GitHub connect modal (URL + token input)
├── RepoBrowser.tsx             # File tree for connected repos
├── CategoryManager.tsx         # Create/edit/delete categories
├── ChatForkModal.tsx           # Fork conversation dialog
├── InjectFromChatModal.tsx     # Pick messages from another chat to inject
├── AutoSummaryPin.tsx          # Collapsible summary at top of chat
└── ConversationSearch.tsx      # Search across all conversations
```

#### `ui/src/hooks/useWorkspaceChat.ts`

Extended version of `useAssistantChat.ts`:
- Same WebSocket protocol base
- Adds: file library state management
- Adds: context budget tracking (update on each message)
- Adds: auto-summary detection (when message count crosses 50-message threshold)
- Adds: fork/inject operations

---

## GitHub Integration Details

### Connecting a Repo

1. User clicks "Connect Repository" in the Library panel
2. Enters: GitHub repo URL + Personal Access Token (for private repos)
3. Backend clones repo to `~/.autoforge/workspace/repos/{owner}_{repo}/`
4. Token stored encrypted in `~/.autoforge/workspace/.tokens` (NOT in SQLite)
5. Repo file tree cached in memory, refreshed on sync
6. Repo path added to Claude SDK's allowed paths

### How Claude Accesses Repo Files

```python
# When conversation has connected repos:
# 1. Add repo path to sandbox allow list
allowed_paths = [repo.local_path for repo in connected_repos]

# 2. Include repo structure in system prompt context
# "Connected Repository: {repo_name} ({branch})\n{file_tree}"

# 3. Claude can now Read/Write/Edit files in the repo
# 4. Claude can run git operations via Bash (commit, push, branch)
```

### Security

- Tokens NEVER stored in SQLite — separate encrypted file
- Token reference IDs link DB records to encrypted storage
- Repos cloned to isolated directory (not in project dir)
- Each conversation can only access its own connected repos
- Global repos accessible to all conversations

---

## Context Management Strategy (1M Window)

### Context Loading Priority

When a conversation resumes, context is loaded in this priority order:

```
1. [ALWAYS] Latest auto-summary (condensed history)           ~2K tokens
2. [ALWAYS] Active library files toggled into chat             ~varies
3. [ALWAYS] Connected repo file tree (structure only)          ~1-5K tokens
4. [ALWAYS] Last 100 messages verbatim                         ~50-100K tokens
5. [IF ROOM] Previous messages beyond 100 (oldest first)       ~fills remaining
6. [NEVER] Messages already covered by summary                 ~skip
```

### Token Counting

```python
# Rough estimation (fast, no API call needed):
# 1 token ≈ 4 characters for English text
# 1 token ≈ 3 characters for code

def estimate_tokens(text: str) -> int:
    return len(text) // 3  # conservative estimate

# Track cumulative tokens per conversation
# Update after each message exchange
# Display in ContextBudgetBar component
```

### Context Budget Bar UI

**CRITICAL: This is a sticky element that scrolls with you. Always visible. Always.**

The context meter lives as a thin bar pinned to the top of the chat area (below the chat header). It stays fixed as you scroll through messages — like a browser's loading bar but permanent. You should ALWAYS be able to glance up and know exactly where you stand.

```
┌─────────────────────────────────────────────────────────┐
│ ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░  312K / 1M    │
│  Messages ■  Library ■  Repos ■  Available ░            │
└─────────────────────────────────────────────────────────┘
```

**Behavior:**
- `position: sticky; top: 0; z-index: 10;` — always visible while scrolling
- Color-coded segments: blue (messages), purple (library files), green (repo context), gray (available)
- Hover any segment for a tooltip breakdown (e.g., "Messages: 287K tokens across 156 messages")
- Subtle color shift at thresholds: normal → yellow tint at 75% → orange at 90% → red pulse at 95%
- Click to expand a detailed breakdown panel showing per-category token usage
- Updates in real-time as messages stream in (not just after response completes)

**Why it matters:** Strategic decisions about what to discuss, when to summarize, when to fork a chat, when to offload files — all depend on knowing your budget at a glance. This isn't a warning system, it's a navigation instrument.

---

## Auto-Summary System

### Trigger

Every 50 new messages, automatically generate a summary snapshot.

### Generation (Side-Channel)

```python
# DO NOT use the main conversation's Claude session
# Use a separate, lightweight Claude call (Haiku for speed):

summary_prompt = f"""
Summarize this conversation concisely. Capture:
1. What's being built / discussed
2. Key decisions made
3. Current status / where things left off
4. Any open questions or next steps

Conversation messages:
{messages_since_last_summary}

Previous summary (if any):
{previous_summary}
"""

# Call Claude Haiku for fast, cheap summary
# Store result in conversation_summaries table
```

### Display

- Pinned at the top of the chat, collapsible
- Shows: "Summary (last updated: 5 min ago, covering 150 messages)"
- Click to expand full summary
- "Regenerate" button for manual refresh

---

## Chat Forking

### How It Works

1. User clicks "Fork Chat" button in header
2. Modal appears: "Fork from this point? This creates a new chat with all context up to now."
3. New conversation created with:
   - All messages copied up to the fork point
   - Same connected repos
   - Same active library files
   - Same category
   - Title: "{original_title} (fork)"
4. User lands in the new chat, can take the tangent without polluting the original

### Backend

```python
POST /api/workspace/conversations/{id}/fork
Body: { "fork_at_message_id": int | null }  # null = fork at latest

# 1. Create new conversation
# 2. Copy messages up to fork point
# 3. Copy connected repos and active library files
# 4. Generate summary for the forked conversation
# 5. Return new conversation_id
```

---

## Inject from Another Chat

### How It Works

1. User clicks "Inject" button in input area
2. Modal shows list of other conversations
3. User picks a conversation, sees its messages
4. User selects specific messages (or "all") to inject
5. Selected content prepended to the next message as context:

```
--- Injected from "{other_chat_title}" ---
[Selected messages in chronological order]
--- End injection ---

{user's actual message}
```

---

## MVP Build Order (What to Build First)

### Phase 1: Core Chat (Build This First — Start Using Immediately)

1. **WorkspacePage route** (`/#/workspace`) with basic layout
2. **Full-agent chat session** — fork `assistant_chat_session.py`, enable Write/Edit/Bash
3. **Multi-conversation persistence** — extend existing DB schema
4. **Chat sidebar** with conversation list, create new, switch between
5. **Context budget bar** — show token usage
6. **Full-page chat UI** — extend `AssistantChat.tsx` for full-page mode

**This alone gives you:** Persistent 1M-window chats with full agent capabilities. You can start using it immediately for idea development.

### Phase 2: File Library + GitHub

7. **File upload** — drag-and-drop files into library
8. **Library panel** — browse global + per-chat files
9. **Toggle files into context** — activate/deactivate library files per chat
10. **GitHub repo connect** — clone, browse tree, read files
11. **GitHub write access** — Claude can edit repo files, commit, push

### Phase 3: Organization + Intelligence

12. **Chat categories** — create, assign, color-code
13. **Auto-summaries** — generate every 50 messages
14. **Chat search** — full-text search across all conversations
15. **Pin/star conversations** — quick access to important chats

### Phase 4: Advanced

16. **Chat forking** — create branch conversation from any point
17. **Inject from chat** — pull context from another conversation
18. **Quick inject** — keyboard shortcut to inject without modal
19. **Export chat** — markdown export for sharing

---

## Key Technical Decisions

### Separate from Assistant Panel

The workspace is a NEW full-page experience, NOT a modification of the existing assistant side panel. The assistant panel stays as-is for quick project Q&A. The workspace is for deep, multi-session idea development.

### File Storage

- Library files stored in `~/.autoforge/workspace/library/`
- File content cached in SQLite for fast context injection
- Large files (>100KB) stored on disk, path referenced in DB
- GitHub repos cloned to `~/.autoforge/workspace/repos/`

### Token Security

- GitHub PATs stored in `~/.autoforge/workspace/.tokens` (encrypted)
- NOT stored in SQLite database
- DB references tokens by ID only
- Tokens encrypted at rest using machine-specific key

### Model Selection

- Default: Claude Opus (best for complex reasoning + coding)
- User can switch per-conversation via chat header settings
- Model stored per-conversation in DB

---

## SaaS Potential (Future)

This is a standalone product. The same architecture works as:
- **Personal tool**: Use your $200 Max subscription
- **SaaS product**: Users bring their own API keys
- **Team version**: Shared repos, shared library, team categories

For now: build it for personal use inside AutoForge. Extract to standalone later.
