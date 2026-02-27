# Workspace — Agent Brief

> Multi-panel AI chat workspace with file library, GitHub integration, token tracking, and split-view mode.

## What It Does

The Workspace is a multi-panel chat environment at `/#/workspace`. Users have conversations with Claude (or other providers) in a split-view layout with Research, PRD Builder, and Coder panels. Each panel can use a different model and context mode. Conversations are persisted in SQLite with categories, search, auto-summaries, and a file library system.

## Files Involved

### Frontend — Page
| File | Purpose |
|------|---------|
| `ui/src/pages/WorkspacePage.tsx` | Main page — split-view, sidebar, chat, library, shortcuts |

### Frontend — Components (`ui/src/components/workspace/`)
| File | Purpose |
|------|---------|
| `WorkspaceChat.tsx` (74KB) | Main chat — WebSocket, message history, file uploads, model selection |
| `WorkspaceChatHeader.tsx` | Header — conversation info, model selector, effort level |
| `WorkspaceSidebar.tsx` (41KB) | Conversation list, search, categories, new chat form |
| `WorkspaceLibrary.tsx` | File library panel with folder browser and activation |
| `WorkspaceUserGuide.tsx` (39KB) | Floating panel — user guide and session notes |
| `EnhancedContextBudgetBar.tsx` | Token usage visualization, context window tracking |
| `UsageDashboard.tsx` | Token usage analytics and cost tracking |
| `SwarmPanel.tsx` | Concurrent autonomous agents panel |
| `TokenLogPanel.tsx` | Per-turn token audit log |
| `FileUploadModal.tsx` | Upload files to library |
| `LibraryFolderBrowser.tsx` | Nested folder browser |
| `LibraryPickerModal.tsx` | Select library files to attach |
| `SaveToLibraryModal.tsx` | Save responses to library |
| `RepoBrowser.tsx` | GitHub repo browser |
| `RepoConnector.tsx` | Connect GitHub repos |
| `RepoSelector.tsx` | Select working directory from repos |
| `CategoryManager.tsx` | Conversation category CRUD |
| `ConversationSearch.tsx` | Full-text search across conversations |
| `ChatForkModal.tsx` | Fork conversation to new branch |
| `PassoffEditor.tsx` | PRD passoff section editor |
| `AgentNotifications.tsx` | Notifications from running agents |

### Frontend — Hooks
| File | Purpose |
|------|---------|
| `ui/src/hooks/useWorkspaceChat.ts` (41KB) | Main hook — WebSocket, token tracking, tool descriptions |
| `ui/src/hooks/useWorkspaceConversations.ts` | React Query hooks for conversation CRUD |
| `ui/src/hooks/useWorkspaceCategories.ts` | Category management hooks |
| `ui/src/hooks/useWorkspaceKeyboardShortcuts.ts` | Global keyboard shortcuts |
| `ui/src/hooks/useWorkspaceLibrary.ts` | Library file management hooks |

### Backend — Router
| File | Purpose |
|------|---------|
| `server/routers/workspace.py` | All workspace endpoints + WebSocket |

### Backend — Services
| File | Purpose |
|------|---------|
| `server/services/workspace_chat_session.py` (1500+ lines) | Chat session — WebSocket streaming, tools, token budgeting |
| `server/services/workspace_database.py` | SQLAlchemy models and CRUD |
| `server/services/workspace_library.py` | File upload, storage, folders |
| `server/services/workspace_repos.py` | GitHub repo management |
| `server/services/workspace_github.py` | GitHub API integration |
| `server/services/workspace_summary.py` | Auto-summary generation |
| `server/services/workspace_token_encryption.py` | Token encryption utilities |

## Data Flow

```
User opens Workspace → Loads conversations from workspace.db
User creates/selects conversation → Opens WebSocket to /api/workspace/ws
User sends message → Backend streams response via WebSocket
Token usage tracked per-turn → Displayed in ContextBudgetBar
Files attached from library → Injected into conversation context
Auto-summary generated → Stored in workspace_summaries table
```

## Database (workspace.db at ~/.autoforge/)

| Table | Key Columns |
|-------|-------------|
| workspace_conversations | id, title, category, model, effort, context_mode, provider, token_count |
| workspace_messages | id, conversation_id, role, content, token_estimate |
| workspace_categories | id, name, color, sort_order |
| workspace_library_folders | id, name, parent_id (nested) |
| workspace_library_files | id, folder_id, filename, file_type, content, tags, active_in_context |
| workspace_file_activations | file_id, conversation_id, active |
| workspace_connected_repos | id, repo_url, repo_name, local_path, branch |
| workspace_summaries | id, conversation_id, summary, message_count |
| workspace_notifications | id, type (summary/roadmap/progress/milestone), data |
| workspace_rate_limit_events | Rate limit hit records |
| workspace_premium_ledger | >200K token cost tracking |
| workspace_token_logs | Per-turn token audit |

## API Endpoints

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/api/workspace/providers` | Available AI providers |
| GET/POST | `/api/workspace/conversations` | List / create conversations |
| GET/PUT/DELETE | `/api/workspace/conversations/{id}` | CRUD single conversation |
| POST | `/api/workspace/conversations/bulk-delete` | Bulk delete |
| GET/POST | `/api/workspace/conversations/{id}/summary` | Get / regenerate summary |
| GET | `/api/workspace/search` | Full-text search |
| GET/POST/PUT/DELETE | `/api/workspace/categories/*` | Category CRUD |
| GET | `/api/workspace/usage/*` | Token usage analytics |
| POST | `/api/workspace/fork` | Fork conversation |
| WS | `/api/workspace/ws` | Chat streaming WebSocket |

## Common Modifications

- **Add a new panel type:** `WorkspacePage.tsx` (layout) + `WorkspaceChat.tsx` (panel logic)
- **Add a new conversation field:** `workspace_database.py` (model) + `workspace.py` (router) + `types.ts` + `WorkspaceSidebar.tsx`
- **Add a new tool for the agent:** `workspace_chat_session.py` (tool registration)
- **Add file library features:** `workspace_library.py` (service) + `WorkspaceLibrary.tsx` + `useWorkspaceLibrary.ts`
