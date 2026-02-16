# Phase 2: Context Management & Organization

## What You're Building

Phase 2 adds six features to the IdeaForge Workspace that Phase 1 established:

1. **Enhanced Context Budget Bar** -- segmented visualization with hover tooltips, animated transitions, real-time streaming updates, and warning states at high usage
2. **Auto-Summary System** -- every 50 messages, a side-channel Haiku call generates a conversation summary; summary history stored in a new table; summary displayed as a collapsible pin above the message list
3. **Chat Categories** -- user-created categories (with color and sort order) for organizing conversations in the sidebar; drag-and-drop or dropdown assignment
4. **Pin/Star Conversations** -- toggle pinned state; pinned conversations float to the top of the sidebar
5. **Chat Search** -- server-side full-text search across conversation titles and message content with highlighted excerpts
6. **Enhanced Context Loading** -- dynamic message loading based on token budget instead of fixed message caps; summary-first context strategy

---

## Prerequisites (Phase 1 Already Built)

Before starting, verify these files exist and are functional:

### Backend
- `server/services/workspace_database.py` -- global SQLite at `~/.autoforge/workspace.db`, SQLAlchemy models for `WorkspaceConversation` and `WorkspaceMessage`
- `server/services/workspace_chat_session.py` -- full agent chat session with Claude SDK, session registry, cleanup function
- `server/routers/workspace.py` -- REST endpoints and WebSocket at `/api/workspace/ws/{conversation_id}`

### Frontend
- `ui/src/pages/WorkspacePage.tsx` -- full-page layout with sidebar + chat area
- `ui/src/components/workspace/WorkspaceSidebar.tsx` -- conversation list with client-side filter
- `ui/src/components/workspace/WorkspaceChat.tsx` -- message display + input
- `ui/src/components/workspace/WorkspaceChatHeader.tsx` -- conversation title bar
- `ui/src/components/workspace/ContextBudgetBar.tsx` -- basic progress bar (to be upgraded)
- `ui/src/hooks/useWorkspaceChat.ts` -- WebSocket hook for streaming chat
- `ui/src/hooks/useWorkspaceConversations.ts` -- React Query hooks for conversation CRUD

### Phase 1 Database Schema
```sql
-- workspace_conversations
CREATE TABLE workspace_conversations (
    id INTEGER PRIMARY KEY,
    title VARCHAR(200),
    category VARCHAR(100) DEFAULT 'Uncategorized',
    pinned BOOLEAN DEFAULT FALSE,
    token_count INTEGER DEFAULT 0,
    summary TEXT,
    summary_updated_at DATETIME,
    created_at DATETIME,
    updated_at DATETIME
);

-- workspace_messages
CREATE TABLE workspace_messages (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER REFERENCES workspace_conversations(id),
    role VARCHAR(20),
    content TEXT,
    token_estimate INTEGER DEFAULT 0,
    timestamp DATETIME
);
```

### Phase 1 WebSocket Protocol
```
Client -> Server: start, message, answer, ping
Server -> Client: conversation_created, text, tool_call, question, response_done, error, pong, token_update
```

The `token_update` message already exists and carries `{ type: "token_update", token_count: number, message_count: number }`.

---

## Files to Create

### 1. `server/services/workspace_summary.py`

Summary generation service using a side-channel Haiku call.

```python
"""
Workspace Summary Service
=========================

Generates conversation summaries using a lightweight Claude model (Haiku).
Summaries are stored in a history table and cached on the conversation record.
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text, create_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

# Summary generation threshold: generate a new summary every N messages
SUMMARY_INTERVAL = 50

# Maximum tokens to allocate for summary in context
SUMMARY_TOKEN_BUDGET = 2000

SUMMARY_PROMPT = """Summarize this conversation concisely. Capture:
1) What is being discussed or built
2) Key decisions made
3) Current status and progress
4) Open questions or unresolved items

Keep the summary under 500 words. Be specific about technical details, file names, and decisions. Do not include pleasantries or meta-commentary about the conversation itself."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# --- Database model (defined here, created via workspace_database.py) ---
# The WorkspaceSummary model is defined in workspace_database.py alongside
# the other workspace models. This module only contains the generation logic.


async def should_generate_summary(message_count: int, last_summary_message_count: Optional[int]) -> bool:
    """Check if we should generate a summary based on message count thresholds.

    Returns True when message_count crosses a multiple of SUMMARY_INTERVAL
    since the last summary was generated.
    """
    if message_count < SUMMARY_INTERVAL:
        return False

    last_count = last_summary_message_count or 0
    # Check if we've crossed a new threshold since the last summary
    return (message_count // SUMMARY_INTERVAL) > (last_count // SUMMARY_INTERVAL)


async def generate_summary(
    conversation_id: int,
    messages: list[dict],
    message_count: int,
) -> Optional[str]:
    """Generate a summary using a Haiku model call.

    This runs as a fire-and-forget task -- it should NOT block the main chat.
    Uses the Anthropic Python SDK directly (not the Agent SDK) for a simple
    one-shot completion.

    Args:
        conversation_id: The conversation to summarize.
        messages: List of message dicts with 'role' and 'content' keys.
        message_count: Total messages in the conversation at time of generation.

    Returns:
        The summary text, or None if generation failed.
    """
    try:
        import anthropic

        # Determine the Haiku model to use
        model = os.getenv("ANTHROPIC_DEFAULT_HAIKU_MODEL", "claude-3-5-haiku-20241022")

        # Build the messages payload: include all provided messages as context
        formatted_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "assistant") and content.strip():
                formatted_messages.append({"role": role, "content": content})

        if not formatted_messages:
            logger.warning(f"No messages to summarize for conversation {conversation_id}")
            return None

        # Add the summary request as the final user message
        formatted_messages.append({
            "role": "user",
            "content": SUMMARY_PROMPT,
        })

        # Ensure messages alternate correctly (Anthropic requirement)
        # If the first message is assistant, prepend a system context
        if formatted_messages[0]["role"] == "assistant":
            formatted_messages.insert(0, {
                "role": "user",
                "content": "(Beginning of conversation)"
            })

        # Merge consecutive same-role messages
        merged: list[dict] = []
        for msg in formatted_messages:
            if merged and merged[-1]["role"] == msg["role"]:
                merged[-1]["content"] += "\n\n" + msg["content"]
            else:
                merged.append(dict(msg))
        formatted_messages = merged

        client = anthropic.Anthropic()
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system="You are a conversation summarizer. Produce clear, concise summaries.",
            messages=formatted_messages,
        )

        summary_text = response.content[0].text if response.content else None
        if summary_text:
            logger.info(
                f"Generated summary for conversation {conversation_id} "
                f"({message_count} messages, {len(summary_text)} chars)"
            )
        return summary_text

    except ImportError:
        logger.error(
            "anthropic package not installed. Cannot generate summaries. "
            "Install with: pip install anthropic"
        )
        return None
    except Exception:
        logger.exception(f"Failed to generate summary for conversation {conversation_id}")
        return None


async def trigger_summary_generation(
    conversation_id: int,
    get_messages_fn,
    save_summary_fn,
    message_count: int,
) -> None:
    """Fire-and-forget summary generation.

    Call this after each message exchange. It checks the threshold and
    spawns a background task if a summary is needed.

    Args:
        conversation_id: The conversation ID.
        get_messages_fn: Callable that returns list[dict] of messages.
        save_summary_fn: Callable(conversation_id, summary_text, message_count) to persist.
        message_count: Current total message count.
    """
    from . import workspace_database as db

    # Get the last summary's message count
    last_summary = db.get_latest_summary(conversation_id)
    last_count = last_summary["message_count"] if last_summary else None

    if not await should_generate_summary(message_count, last_count):
        return

    # Spawn background task
    asyncio.create_task(
        _background_summarize(conversation_id, get_messages_fn, save_summary_fn, message_count)
    )


async def _background_summarize(
    conversation_id: int,
    get_messages_fn,
    save_summary_fn,
    message_count: int,
) -> None:
    """Background coroutine that generates and saves a summary."""
    try:
        messages = get_messages_fn(conversation_id)
        summary_text = await generate_summary(conversation_id, messages, message_count)
        if summary_text:
            save_summary_fn(conversation_id, summary_text, message_count)
    except Exception:
        logger.exception(f"Background summary generation failed for conversation {conversation_id}")
```

**Key design decisions:**
- Uses the `anthropic` Python SDK directly (not the Agent SDK) for a simple one-shot call. The Agent SDK is heavyweight and meant for multi-turn tool-use sessions.
- Fire-and-forget via `asyncio.create_task` so summaries never block the chat.
- The `should_generate_summary` function is pure and testable.
- Messages are merged to satisfy Anthropic's alternating-role requirement.

---

### 2. `ui/src/components/workspace/EnhancedContextBudgetBar.tsx`

Replaces the basic `ContextBudgetBar.tsx` with a segmented, animated, tooltip-rich version.

```tsx
/**
 * EnhancedContextBudgetBar
 *
 * Segmented context budget visualization with:
 * - Color-coded segments: summary | messages | available
 * - Hover tooltips with detailed breakdowns
 * - Smooth CSS transitions on segment width changes
 * - Warning background tint at high usage (>80%)
 */

import { useMemo } from 'react'

// --- Types ---

interface ContextBudgetSegment {
  label: string
  tokens: number
  color: string       // Tailwind bg class
  hoverColor: string  // Tailwind hover:bg class
}

interface EnhancedContextBudgetBarProps {
  /** Total context window size in tokens */
  totalBudget: number
  /** Tokens used by messages */
  messageTokens: number
  /** Tokens used by the current summary */
  summaryTokens: number
  /** Number of messages loaded in context */
  messageCount: number
  /** Whether a response is currently streaming */
  isStreaming?: boolean
}
```

**Props breakdown:**
- `totalBudget`: the full context window (default 1,000,000 for Opus)
- `messageTokens`: sum of `token_estimate` for loaded messages
- `summaryTokens`: estimated tokens for the current summary
- `messageCount`: count of messages currently in context
- `isStreaming`: when true, show a subtle shimmer animation on the rightmost filled segment

**Segment definitions (computed via `useMemo`):**
```tsx
const segments: ContextBudgetSegment[] = useMemo(() => [
  {
    label: 'Summary',
    tokens: summaryTokens,
    color: 'bg-primary/60',
    hoverColor: 'hover:bg-primary/70',
  },
  {
    label: 'Messages',
    tokens: messageTokens,
    color: 'bg-primary/30',
    hoverColor: 'hover:bg-primary/40',
  },
], [summaryTokens, messageTokens])
```

**Rendering structure:**
```tsx
return (
  <div className="px-4 py-2 border-b border-border bg-card">
    {/* Usage text */}
    <div className="flex items-center justify-between mb-1">
      <span className="text-xs text-muted-foreground">
        Context: {formatTokenCount(usedTokens)} / {formatTokenCount(totalBudget)}
      </span>
      <span className="text-xs text-muted-foreground">
        {messageCount} messages
      </span>
    </div>

    {/* Segmented bar */}
    <div className="relative h-2 rounded-full bg-muted overflow-hidden">
      {segments.map((segment, i) => (
        <div
          key={segment.label}
          className={`absolute top-0 h-full transition-all duration-500 ease-out ${segment.color} ${segment.hoverColor} group`}
          style={{
            left: `${segmentOffsets[i]}%`,
            width: `${segmentWidths[i]}%`,
          }}
          title={`${segment.label}: ${formatTokenCount(segment.tokens)} tokens`}
        >
          {/* Tooltip appears on hover via group-hover */}
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1
                          hidden group-hover:block z-10">
            <div className="bg-popover text-popover-foreground text-xs rounded-md
                            px-2 py-1 shadow-md border border-border whitespace-nowrap">
              {segment.label}: {formatTokenCount(segment.tokens)} tokens
              {segment.label === 'Messages' && ` across ${messageCount} messages`}
            </div>
          </div>
        </div>
      ))}

      {/* Streaming shimmer overlay */}
      {isStreaming && (
        <div className="absolute top-0 right-0 h-full w-8 animate-shimmer
                        bg-gradient-to-r from-transparent via-white/20 to-transparent" />
      )}
    </div>
  </div>
)
```

**Warning state:**
When usage exceeds 80%, apply a subtle background tint to the parent chat area. The component exposes a `usagePercent` via a callback prop or simply renders a CSS class:

```tsx
// Add to the outer div:
const usagePercent = (usedTokens / totalBudget) * 100
const warningClass = usagePercent > 90
  ? 'bg-destructive/5'
  : usagePercent > 80
    ? 'bg-[color:var(--color-status-pending)]/10'
    : ''
```

The parent `WorkspaceChat.tsx` should read the usage percentage and apply the tint to its own background. Export a helper:

```tsx
export function getContextWarningClass(usagePercent: number): string {
  if (usagePercent > 90) return 'bg-destructive/5'
  if (usagePercent > 80) return 'bg-[color:var(--color-status-pending)]/10'
  return ''
}
```

**Helper function:**
```tsx
function formatTokenCount(tokens: number): string {
  if (tokens >= 1_000_000) return `${(tokens / 1_000_000).toFixed(1)}M`
  if (tokens >= 1_000) return `${(tokens / 1_000).toFixed(0)}K`
  return String(tokens)
}
```

---

### 3. `ui/src/components/workspace/AutoSummaryPin.tsx`

Collapsible summary card pinned at the top of the message area.

```tsx
/**
 * AutoSummaryPin
 *
 * Displays the latest conversation summary in a collapsible card
 * above the message list. Shows update timestamp, message coverage,
 * and a manual regenerate button.
 */

import { useState } from 'react'
import { ChevronDown, ChevronRight, RefreshCw, FileText } from 'lucide-react'

interface AutoSummaryPinProps {
  /** The summary text (markdown-compatible) */
  summary: string | null
  /** ISO timestamp of when the summary was last updated */
  updatedAt: string | null
  /** Number of messages the summary covers */
  messagesCovered: number | null
  /** Callback to trigger manual summary regeneration */
  onRegenerate: () => void
  /** Whether a regeneration is currently in progress */
  isRegenerating?: boolean
}
```

**Rendering:**
```tsx
export function AutoSummaryPin({
  summary,
  updatedAt,
  messagesCovered,
  onRegenerate,
  isRegenerating = false,
}: AutoSummaryPinProps) {
  const [expanded, setExpanded] = useState(false)

  if (!summary) return null

  const timeAgo = updatedAt ? formatTimeAgo(new Date(updatedAt)) : 'unknown'

  return (
    <div className="mx-4 mt-2 mb-1 border border-border rounded-md bg-muted/50">
      {/* Header (always visible) */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center justify-between w-full px-3 py-2 text-left
                   text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <div className="flex items-center gap-2">
          {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          <FileText size={14} />
          <span>
            Summary
            {messagesCovered && ` (${messagesCovered} messages)`}
            {' \u00b7 '}
            updated {timeAgo}
          </span>
        </div>

        <button
          onClick={(e) => { e.stopPropagation(); onRegenerate() }}
          disabled={isRegenerating}
          className="p-1 rounded hover:bg-accent transition-colors
                     disabled:opacity-50 disabled:cursor-not-allowed"
          title="Regenerate summary"
        >
          <RefreshCw size={14} className={isRegenerating ? 'animate-spin' : ''} />
        </button>
      </button>

      {/* Expandable content */}
      {expanded && (
        <div className="px-3 pb-3 text-sm text-foreground whitespace-pre-wrap border-t border-border pt-2">
          {summary}
        </div>
      )}
    </div>
  )
}
```

**`formatTimeAgo` helper** (include in the same file or in a shared `utils.ts`):
```tsx
function formatTimeAgo(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000)
  if (seconds < 60) return 'just now'
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}
```

---

### 4. `ui/src/components/workspace/CategoryManager.tsx`

Modal for CRUD operations on workspace categories.

```tsx
/**
 * CategoryManager
 *
 * Modal dialog for managing workspace categories:
 * - Create new categories with name + color
 * - Edit existing category name/color
 * - Delete categories (conversations become Uncategorized)
 * - Reorder categories via drag or up/down buttons
 */

import { useState, useEffect } from 'react'
import { X, Plus, Trash2, GripVertical, Pencil, Check } from 'lucide-react'

// Preset category colors (hex values for the sidebar dot indicator)
const PRESET_COLORS = [
  '#3b82f6', // blue
  '#22c55e', // green
  '#eab308', // yellow
  '#f97316', // orange
  '#ef4444', // red
  '#a855f7', // purple
  '#ec4899', // pink
  '#06b6d4', // cyan
  '#6366f1', // indigo
  '#84cc16', // lime
] as const

interface WorkspaceCategory {
  id: number
  name: string
  color: string | null
  sort_order: number
  created_at: string
}

interface CategoryManagerProps {
  open: boolean
  onClose: () => void
  categories: WorkspaceCategory[]
  onCreateCategory: (name: string, color: string) => Promise<void>
  onUpdateCategory: (id: number, name: string, color: string) => Promise<void>
  onDeleteCategory: (id: number) => Promise<void>
  onReorderCategories: (orderedIds: number[]) => Promise<void>
}
```

**Component structure:**
- Rendered as a modal overlay (`fixed inset-0 z-50 flex items-center justify-center bg-black/50`)
- Inner panel: `bg-card border border-border rounded-lg shadow-lg max-w-md w-full mx-4`
- Header with title "Manage Categories" and close button
- Scrollable list of categories, each row showing: drag handle | color dot | name | edit button | delete button
- "Add Category" row at bottom with name input + color picker (grid of preset color circles)
- Each color preset rendered as a `w-6 h-6 rounded-full cursor-pointer ring-2 ring-offset-2` with `ring-primary` when selected

**Reordering:**
Use simple up/down arrow buttons rather than implementing full drag-and-drop (keeps complexity down). Each category row has up/down chevrons that call `onReorderCategories` with the new order. The `sort_order` field determines display order.

---

### 5. `ui/src/components/workspace/ConversationSearch.tsx`

Server-side search component for the sidebar.

```tsx
/**
 * ConversationSearch
 *
 * Search input that upgrades to server-side search when the query
 * is 3+ characters. Shows search results with matching message
 * excerpts and highlighted query terms.
 */

import { useState, useEffect, useCallback } from 'react'
import { Search, X, MessageSquare } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { searchWorkspaceConversations } from '../../lib/api'

interface SearchResult {
  conversation_id: number
  conversation_title: string | null
  category: string
  matching_excerpts: Array<{
    message_id: number
    role: string
    excerpt: string  // ~100 chars around match
  }>
}

interface ConversationSearchProps {
  onSelectConversation: (conversationId: number) => void
  /** Fallback client-side filter for short queries */
  onFilterChange: (filter: string) => void
}
```

**Behavior:**
- Input with search icon, debounced at 300ms
- When query length < 3: call `onFilterChange(query)` for client-side sidebar filtering (existing Phase 1 behavior)
- When query length >= 3: make server API call via React Query
- Results panel appears below the search input as an overlay (`absolute top-full left-0 right-0 z-20`)
- Each result shows conversation title, category badge, and up to 2 matching excerpts
- Excerpts highlight the matching query term using `<mark>` with class `bg-primary/20 text-foreground rounded px-0.5`
- Click a result to navigate to that conversation
- Press Escape or click X to clear search

**Highlight helper:**
```tsx
function highlightExcerpt(text: string, query: string): JSX.Element {
  const regex = new RegExp(`(${escapeRegex(query)})`, 'gi')
  const parts = text.split(regex)
  return (
    <>
      {parts.map((part, i) =>
        regex.test(part)
          ? <mark key={i} className="bg-primary/20 text-foreground rounded px-0.5">{part}</mark>
          : <span key={i}>{part}</span>
      )}
    </>
  )
}

function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}
```

---

### 6. `ui/src/hooks/useWorkspaceCategories.ts`

React Query hooks for category CRUD.

```tsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  listWorkspaceCategories,
  createWorkspaceCategory,
  updateWorkspaceCategory,
  deleteWorkspaceCategory,
} from '../lib/api'

const CATEGORIES_KEY = ['workspace', 'categories']

export function useWorkspaceCategories() {
  return useQuery({
    queryKey: CATEGORIES_KEY,
    queryFn: listWorkspaceCategories,
  })
}

export function useCreateCategory() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ name, color }: { name: string; color: string }) =>
      createWorkspaceCategory(name, color),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CATEGORIES_KEY })
    },
  })
}

export function useUpdateCategory() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, name, color }: { id: number; name: string; color: string }) =>
      updateWorkspaceCategory(id, name, color),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CATEGORIES_KEY })
    },
  })
}

export function useDeleteCategory() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => deleteWorkspaceCategory(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CATEGORIES_KEY })
      // Also invalidate conversations since categories may have changed
      queryClient.invalidateQueries({ queryKey: ['workspace', 'conversations'] })
    },
  })
}
```

---

## Files to Modify

### 1. `server/services/workspace_database.py`

**Add the `WorkspaceSummary` model** alongside existing models:

```python
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
```

**Add the `WorkspaceCategory` model:**

```python
class WorkspaceCategory(Base):
    """User-defined categories for organizing conversations."""
    __tablename__ = "workspace_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    color = Column(String(7), nullable=True)  # hex color, e.g. "#3b82f6"
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=_utc_now)
```

**Add these database functions** (follow the existing patterns in `workspace_database.py` and `assistant_database.py`):

```python
# ============================================================================
# Summary Operations
# ============================================================================

def save_summary(conversation_id: int, summary_text: str, message_count: int) -> dict:
    """Save a new summary and update the conversation's cached summary."""
    session = get_session()
    try:
        token_estimate = len(summary_text) // 3

        # Create summary record
        summary = WorkspaceSummary(
            conversation_id=conversation_id,
            summary=summary_text,
            message_count=message_count,
            token_estimate=token_estimate,
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
    """Get the most recent summary for a conversation."""
    session = get_session()
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
    """Get all summaries for a conversation, newest first."""
    session = get_session()
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
    """Calculate total token count for a conversation's messages."""
    from sqlalchemy import func
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
    """Create a new category."""
    session = get_session()
    try:
        # Determine next sort_order
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
    """Get all categories ordered by sort_order."""
    session = get_session()
    try:
        categories = (
            session.query(WorkspaceCategory)
            .order_by(WorkspaceCategory.sort_order.asc())
            .all()
        )
        return [_category_to_dict(c) for c in categories]
    finally:
        session.close()


def update_category(category_id: int, name: Optional[str] = None, color: Optional[str] = None) -> Optional[dict]:
    """Update a category's name and/or color."""
    session = get_session()
    try:
        category = session.query(WorkspaceCategory).filter(WorkspaceCategory.id == category_id).first()
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
    """Delete a category. Conversations in this category become 'Uncategorized'."""
    session = get_session()
    try:
        category = session.query(WorkspaceCategory).filter(WorkspaceCategory.id == category_id).first()
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
    """Update sort_order for categories based on the provided ID order."""
    session = get_session()
    try:
        for index, cat_id in enumerate(ordered_ids):
            session.query(WorkspaceCategory).filter(
                WorkspaceCategory.id == cat_id
            ).update({"sort_order": index})
        session.commit()
        return get_categories()
    finally:
        session.close()


def _category_to_dict(category: WorkspaceCategory) -> dict:
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

    Strategy: search conversations by title first, then search messages
    and group by conversation_id. Returns conversations with matching
    message excerpts.
    """
    session = get_session()
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

            # Extract excerpt around the match
            excerpt = _extract_excerpt(msg.content, query, context_chars=80)
            if len(results[cid]["matching_excerpts"]) < 2:  # Max 2 excerpts per conversation
                results[cid]["matching_excerpts"].append({
                    "message_id": msg.id,
                    "role": msg.role,
                    "excerpt": excerpt,
                })

        # Sort by number of matches (most relevant first) and limit
        sorted_results = sorted(results.values(), key=lambda r: len(r["matching_excerpts"]), reverse=True)
        return sorted_results[:limit]

    finally:
        session.close()


def _extract_excerpt(content: str, query: str, context_chars: int = 80) -> str:
    """Extract a text excerpt centered around the first occurrence of query."""
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

    Always loads most-recent-first until the budget is exhausted.

    Args:
        conversation_id: The conversation to load.
        token_budget: Maximum tokens to allocate for messages.

    Returns:
        Tuple of (messages_oldest_first, total_token_count).
    """
    session = get_session()
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
```

**Important:** The `get_engine()` function in `workspace_database.py` calls `Base.metadata.create_all(engine)` on first access. Adding new models to the same `Base` class means the new tables (`workspace_summaries`, `workspace_categories`) will be auto-created on next server start. No explicit migration step is needed.

---

### 2. `server/services/workspace_chat_session.py`

**Modifications to add auto-summary triggering and enhanced context loading.**

**2a. Add imports at the top:**
```python
from .workspace_summary import trigger_summary_generation
from . import workspace_database as db
```

**2b. Modify `send_message()` -- after storing the assistant response, trigger summary check:**

Find the section where the assistant response is stored (similar to `assistant_chat_session.py` line 431). After the response is stored and `response_done` is yielded, add:

```python
# After storing assistant response and yielding response_done:

# Check if auto-summary should be triggered
if self.conversation_id is not None:
    # Count total messages for this conversation
    messages = db.get_messages(self.conversation_id)
    message_count = len(messages)

    await trigger_summary_generation(
        conversation_id=self.conversation_id,
        get_messages_fn=db.get_messages,
        save_summary_fn=db.save_summary,
        message_count=message_count,
    )
```

**2c. Replace the fixed-count message loading with dynamic context loading:**

In the `send_message()` method, replace the history loading section (the block that loads messages for resumed conversations). Instead of a fixed message cap like:

```python
# OLD: Fixed cap
history = history[-100:] if len(history) > 100 else history
```

Use the new dynamic loader:

```python
# NEW: Dynamic context loading based on token budget
if not self._history_loaded:
    self._history_loaded = True

    # Load the latest summary first
    latest_summary = db.get_latest_summary(self.conversation_id)
    summary_context = ""
    summary_tokens = 0
    if latest_summary:
        summary_context = latest_summary["summary"]
        summary_tokens = latest_summary.get("token_estimate", len(summary_context) // 3)

    # Calculate remaining budget for messages
    # Reserve ~2K for summary, rest for messages
    MESSAGE_TOKEN_BUDGET = 400_000
    remaining_budget = MESSAGE_TOKEN_BUDGET - summary_tokens

    # Load messages dynamically up to the budget
    history_messages, loaded_tokens = db.get_messages_for_context(
        self.conversation_id,
        token_budget=remaining_budget,
    )
    # Exclude the current message we just added (it's the last one chronologically)
    if history_messages and history_messages[-1]["content"] == user_message:
        history_messages = history_messages[:-1]

    if summary_context or history_messages:
        history_lines = []
        if summary_context:
            history_lines.append("[Conversation summary:]")
            history_lines.append(summary_context)
            history_lines.append("")
        if history_messages:
            history_lines.append("[Recent conversation history:]")
            for msg in history_messages:
                role = "User" if msg["role"] == "user" else "Assistant"
                history_lines.append(f"{role}: {msg['content']}")
        history_lines.append("[End of history. Continue the conversation:]")
        history_lines.append(f"User: {user_message}")
        message_to_send = "\n".join(history_lines)
        logger.info(
            f"Loaded context: summary={bool(summary_context)}, "
            f"messages={len(history_messages)}, tokens={loaded_tokens + summary_tokens}"
        )
```

**2d. Add `token_update` emission during streaming:**

Inside the `_query_claude()` method, after each text chunk is yielded, also yield a `token_update` message with the running count:

```python
# Inside _query_claude, after yielding text:
if text:
    full_response += text
    yield {"type": "text", "content": text}

    # Emit running token estimate for real-time budget bar updates
    running_token_estimate = len(full_response) // 3
    yield {
        "type": "token_update",
        "token_count": self._base_token_count + running_token_estimate,
        "message_count": self._message_count,
    }
```

Add `_base_token_count` and `_message_count` as instance attributes, updated at the start of each `send_message()` call:

```python
# At the start of send_message(), before calling _query_claude():
self._base_token_count = db.get_conversation_token_count(self.conversation_id)
self._message_count = db.get_message_count(self.conversation_id)
```

---

### 3. `server/routers/workspace.py`

**Add these new endpoints to the existing workspace router.**

**3a. Summary endpoints:**

```python
# ============================================================================
# Summary Endpoints
# ============================================================================

class SummaryResponse(BaseModel):
    id: int
    conversation_id: int
    summary: str
    message_count: int
    token_estimate: int
    created_at: Optional[str]


@router.get("/conversations/{conversation_id}/summary", response_model=Optional[SummaryResponse])
async def get_conversation_summary(conversation_id: int):
    """Get the latest summary for a conversation."""
    from ..services import workspace_database as db
    summary = db.get_latest_summary(conversation_id)
    if not summary:
        return None
    return SummaryResponse(**summary)


@router.post("/conversations/{conversation_id}/summarize", response_model=SummaryResponse)
async def force_regenerate_summary(conversation_id: int):
    """Force regenerate the summary for a conversation."""
    from ..services import workspace_database as db
    from ..services.workspace_summary import generate_summary

    # Verify conversation exists
    conversation = db.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get all messages
    messages = db.get_messages(conversation_id)
    if not messages:
        raise HTTPException(status_code=400, detail="No messages to summarize")

    # Generate summary (this is synchronous from the caller's perspective)
    summary_text = await generate_summary(conversation_id, messages, len(messages))
    if not summary_text:
        raise HTTPException(status_code=500, detail="Summary generation failed")

    # Save it
    result = db.save_summary(conversation_id, summary_text, len(messages))
    return SummaryResponse(**result)
```

**3b. Category endpoints:**

```python
# ============================================================================
# Category Endpoints
# ============================================================================

class CategoryCreate(BaseModel):
    name: str
    color: Optional[str] = None

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None

class CategoryResponse(BaseModel):
    id: int
    name: str
    color: Optional[str]
    sort_order: int
    created_at: Optional[str]

class CategoryReorder(BaseModel):
    ordered_ids: list[int]


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories():
    """List all workspace categories."""
    from ..services import workspace_database as db
    categories = db.get_categories()
    return [CategoryResponse(**c) for c in categories]


@router.post("/categories", response_model=CategoryResponse, status_code=201)
async def create_category(body: CategoryCreate):
    """Create a new workspace category."""
    from ..services import workspace_database as db
    if not body.name or not body.name.strip():
        raise HTTPException(status_code=400, detail="Category name is required")
    if body.name.strip().lower() == "uncategorized":
        raise HTTPException(status_code=400, detail="Cannot create a category named 'Uncategorized'")
    try:
        category = db.create_category(body.name.strip(), body.color)
        return CategoryResponse(**category)
    except Exception as e:
        if "UNIQUE" in str(e).upper():
            raise HTTPException(status_code=409, detail="Category name already exists")
        raise


@router.patch("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(category_id: int, body: CategoryUpdate):
    """Update a category's name or color."""
    from ..services import workspace_database as db
    if body.name and body.name.strip().lower() == "uncategorized":
        raise HTTPException(status_code=400, detail="Cannot rename to 'Uncategorized'")
    result = db.update_category(category_id, name=body.name, color=body.color)
    if not result:
        raise HTTPException(status_code=404, detail="Category not found")
    return CategoryResponse(**result)


@router.delete("/categories/{category_id}")
async def delete_category(category_id: int):
    """Delete a category. Conversations become Uncategorized."""
    from ..services import workspace_database as db
    success = db.delete_category(category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"success": True, "message": "Category deleted"}


@router.post("/categories/reorder", response_model=list[CategoryResponse])
async def reorder_categories(body: CategoryReorder):
    """Reorder categories by providing ordered list of IDs."""
    from ..services import workspace_database as db
    categories = db.reorder_categories(body.ordered_ids)
    return [CategoryResponse(**c) for c in categories]
```

**3c. Search endpoint:**

```python
# ============================================================================
# Search Endpoint
# ============================================================================

class SearchExcerpt(BaseModel):
    message_id: int
    role: str
    excerpt: str

class SearchResultItem(BaseModel):
    conversation_id: int
    conversation_title: Optional[str]
    category: str
    matching_excerpts: list[SearchExcerpt]


@router.get("/search", response_model=list[SearchResultItem])
async def search_conversations(q: str = "", limit: int = 20):
    """Full-text search across workspace conversations and messages."""
    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")
    if limit < 1 or limit > 100:
        limit = 20

    from ..services import workspace_database as db
    results = db.search_conversations(q.strip(), limit=limit)
    return [SearchResultItem(**r) for r in results]
```

**3d. Pin toggle (modify existing PATCH endpoint):**

The Phase 1 `PATCH /api/workspace/conversations/{id}` endpoint already accepts a body with optional fields. Ensure it handles `pinned`:

```python
class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    pinned: Optional[bool] = None
```

If this model already exists in Phase 1, just verify `pinned` is included. The existing PATCH handler should already update any provided fields on the conversation record.

---

### 4. `ui/src/lib/types.ts`

**Add these types at the end of the file, in a new section:**

```typescript
// ============================================================================
// Workspace Types (Phase 2)
// ============================================================================

export interface WorkspaceCategory {
  id: number
  name: string
  color: string | null
  sort_order: number
  created_at: string
}

export interface WorkspaceSummary {
  id: number
  conversation_id: number
  summary: string
  message_count: number
  token_estimate: number
  created_at: string | null
}

export interface WorkspaceSearchExcerpt {
  message_id: number
  role: string
  excerpt: string
}

export interface WorkspaceSearchResult {
  conversation_id: number
  conversation_title: string | null
  category: string
  matching_excerpts: WorkspaceSearchExcerpt[]
}

export interface WorkspaceContextBudget {
  total_budget: number
  message_tokens: number
  summary_tokens: number
  message_count: number
  usage_percent: number
}
```

---

### 5. `ui/src/lib/api.ts`

**Add these API functions at the end of the file, in a new section:**

```typescript
// ============================================================================
// Workspace Categories API
// ============================================================================

export async function listWorkspaceCategories(): Promise<WorkspaceCategory[]> {
  return fetchJSON('/workspace/categories')
}

export async function createWorkspaceCategory(
  name: string,
  color: string
): Promise<WorkspaceCategory> {
  return fetchJSON('/workspace/categories', {
    method: 'POST',
    body: JSON.stringify({ name, color }),
  })
}

export async function updateWorkspaceCategory(
  id: number,
  name: string,
  color: string
): Promise<WorkspaceCategory> {
  return fetchJSON(`/workspace/categories/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ name, color }),
  })
}

export async function deleteWorkspaceCategory(
  id: number
): Promise<void> {
  await fetchJSON(`/workspace/categories/${id}`, {
    method: 'DELETE',
  })
}

export async function reorderWorkspaceCategories(
  orderedIds: number[]
): Promise<WorkspaceCategory[]> {
  return fetchJSON('/workspace/categories/reorder', {
    method: 'POST',
    body: JSON.stringify({ ordered_ids: orderedIds }),
  })
}

// ============================================================================
// Workspace Summary API
// ============================================================================

export async function getWorkspaceSummary(
  conversationId: number
): Promise<WorkspaceSummary | null> {
  return fetchJSON(`/workspace/conversations/${conversationId}/summary`)
}

export async function regenerateWorkspaceSummary(
  conversationId: number
): Promise<WorkspaceSummary> {
  return fetchJSON(`/workspace/conversations/${conversationId}/summarize`, {
    method: 'POST',
  })
}

// ============================================================================
// Workspace Search API
// ============================================================================

export async function searchWorkspaceConversations(
  query: string,
  limit: number = 20
): Promise<WorkspaceSearchResult[]> {
  const params = new URLSearchParams({ q: query, limit: String(limit) })
  return fetchJSON(`/workspace/search?${params.toString()}`)
}
```

**Also add the new type imports** to the existing import block at the top of `api.ts`:

```typescript
import type {
  // ... existing imports ...
  WorkspaceCategory,
  WorkspaceSummary,
  WorkspaceSearchResult,
} from './types'
```

---

### 6. `ui/src/components/workspace/WorkspaceSidebar.tsx`

**Major modifications for categories, pinning, and search upgrade.**

**6a. Import the new components:**
```tsx
import { ConversationSearch } from './ConversationSearch'
import { CategoryManager } from './CategoryManager'
import { useWorkspaceCategories, useCreateCategory, useUpdateCategory, useDeleteCategory } from '../../hooks/useWorkspaceCategories'
```

**6b. Replace the client-side search input with `ConversationSearch`:**

The Phase 1 sidebar has a simple `<input>` for filtering. Replace it with:

```tsx
<ConversationSearch
  onSelectConversation={(id) => onSelectConversation(id)}
  onFilterChange={(filter) => setLocalFilter(filter)}
/>
```

**6c. Group conversations by category:**

```tsx
// Group conversations into categories
const grouped = useMemo(() => {
  const groups: Record<string, typeof conversations> = {}

  // Pinned conversations go in a special group
  const pinned = conversations.filter(c => c.pinned)
  if (pinned.length > 0) {
    groups['__pinned__'] = pinned
  }

  // Group remaining by category
  const unpinned = conversations.filter(c => !c.pinned)
  for (const conv of unpinned) {
    const cat = conv.category || 'Uncategorized'
    if (!groups[cat]) groups[cat] = []
    groups[cat].push(conv)
  }

  return groups
}, [conversations])

// Render order: pinned first, then categories in sort_order, then Uncategorized last
const categoryOrder = useMemo(() => {
  const order: string[] = []
  if (grouped['__pinned__']) order.push('__pinned__')
  for (const cat of categories) {
    if (grouped[cat.name]) order.push(cat.name)
  }
  if (grouped['Uncategorized'] && !order.includes('Uncategorized')) {
    order.push('Uncategorized')
  }
  return order
}, [grouped, categories])
```

**6d. Render category groups as collapsible sections:**

```tsx
{categoryOrder.map(groupKey => {
  const isPin = groupKey === '__pinned__'
  const label = isPin ? 'Pinned' : groupKey
  const category = categories.find(c => c.name === groupKey)
  const colorDot = category?.color

  return (
    <div key={groupKey}>
      <button
        onClick={() => toggleCollapsed(groupKey)}
        className="flex items-center gap-2 w-full px-3 py-1.5 text-xs font-medium
                   text-muted-foreground uppercase tracking-wider hover:text-foreground"
      >
        {colorDot && (
          <span
            className="w-2 h-2 rounded-full flex-shrink-0"
            style={{ backgroundColor: colorDot }}
          />
        )}
        {isPin && <Star size={12} className="text-primary" />}
        <span className="truncate">{label}</span>
        <span className="ml-auto text-muted-foreground/50">
          {grouped[groupKey].length}
        </span>
      </button>

      {!collapsed[groupKey] && (
        <div className="space-y-0.5">
          {grouped[groupKey].map(conv => (
            <ConversationItem
              key={conv.id}
              conversation={conv}
              isActive={conv.id === activeConversationId}
              onSelect={() => onSelectConversation(conv.id)}
              onTogglePin={() => onTogglePin(conv.id, !conv.pinned)}
              onChangeCategory={(category) => onChangeCategory(conv.id, category)}
              categories={categories}
            />
          ))}
        </div>
      )}
    </div>
  )
})}
```

**6e. Add "Manage Categories" button at the bottom of the sidebar:**

```tsx
<button
  onClick={() => setShowCategoryManager(true)}
  className="flex items-center gap-2 w-full px-3 py-2 text-sm text-muted-foreground
             hover:text-foreground hover:bg-accent transition-colors border-t border-border"
>
  <Settings size={14} />
  Manage Categories
</button>

{showCategoryManager && (
  <CategoryManager
    open={showCategoryManager}
    onClose={() => setShowCategoryManager(false)}
    categories={categories}
    onCreateCategory={async (name, color) => { await createCategory({ name, color }) }}
    onUpdateCategory={async (id, name, color) => { await updateCategory({ id, name, color }) }}
    onDeleteCategory={async (id) => { await deleteCategory(id) }}
    onReorderCategories={async (orderedIds) => {
      await reorderWorkspaceCategories(orderedIds)
    }}
  />
)}
```

**6f. Add pin toggle and category change to the conversation context menu:**

Each `ConversationItem` should have a right-click context menu or an overflow menu (three dots) with:
- "Pin" / "Unpin" (toggles `pinned` via PATCH)
- "Move to Category >" submenu listing all categories
- "Delete" (existing from Phase 1)

Implementation approach: use a simple dropdown triggered by a `...` button on hover:

```tsx
function ConversationItem({
  conversation,
  isActive,
  onSelect,
  onTogglePin,
  onChangeCategory,
  categories,
}: {
  conversation: WorkspaceConversation
  isActive: boolean
  onSelect: () => void
  onTogglePin: () => void
  onChangeCategory: (category: string) => void
  categories: WorkspaceCategory[]
}) {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div
      className={`group flex items-center gap-2 px-3 py-2 cursor-pointer text-sm
                  transition-colors rounded-md mx-1
                  ${isActive ? 'bg-accent text-accent-foreground' : 'hover:bg-accent/50 text-foreground'}`}
      onClick={onSelect}
    >
      {conversation.pinned && <Star size={12} className="text-primary flex-shrink-0" />}
      <span className="truncate flex-1">{conversation.title || 'New Chat'}</span>

      {/* Overflow menu trigger */}
      <button
        onClick={(e) => { e.stopPropagation(); setMenuOpen(!menuOpen) }}
        className="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:bg-accent"
      >
        <MoreHorizontal size={14} />
      </button>

      {menuOpen && (
        <DropdownMenu onClose={() => setMenuOpen(false)}>
          <DropdownItem onClick={onTogglePin}>
            {conversation.pinned ? 'Unpin' : 'Pin'}
          </DropdownItem>
          <DropdownSeparator />
          <DropdownLabel>Move to Category</DropdownLabel>
          <DropdownItem onClick={() => onChangeCategory('Uncategorized')}>
            Uncategorized
          </DropdownItem>
          {categories.map(cat => (
            <DropdownItem
              key={cat.id}
              onClick={() => onChangeCategory(cat.name)}
            >
              <span className="w-2 h-2 rounded-full mr-2" style={{ backgroundColor: cat.color || '#888' }} />
              {cat.name}
            </DropdownItem>
          ))}
        </DropdownMenu>
      )}
    </div>
  )
}
```

The `DropdownMenu`, `DropdownItem`, `DropdownSeparator`, and `DropdownLabel` can be simple styled `<div>` wrappers or you can use Radix UI's `DropdownMenu` if it's available in the project. Check `ui/package.json` for `@radix-ui/react-dropdown-menu`. If present, use it. If not, build a simple positioned dropdown:

```tsx
function DropdownMenu({ onClose, children }: { onClose: () => void; children: React.ReactNode }) {
  // Close on click outside
  useEffect(() => {
    const handler = () => onClose()
    document.addEventListener('click', handler)
    return () => document.removeEventListener('click', handler)
  }, [onClose])

  return (
    <div
      className="absolute right-0 top-full z-30 mt-1 min-w-[160px]
                 bg-popover border border-border rounded-md shadow-md py-1"
      onClick={(e) => e.stopPropagation()}
    >
      {children}
    </div>
  )
}
```

---

### 7. `ui/src/components/workspace/WorkspaceChat.tsx`

**Modifications:**

**7a. Replace `ContextBudgetBar` with `EnhancedContextBudgetBar`:**

```tsx
// Replace:
import { ContextBudgetBar } from './ContextBudgetBar'
// With:
import { EnhancedContextBudgetBar, getContextWarningClass } from './EnhancedContextBudgetBar'
```

Update the render to pass segmented data:

```tsx
<EnhancedContextBudgetBar
  totalBudget={1_000_000}
  messageTokens={contextBudget.messageTokens}
  summaryTokens={contextBudget.summaryTokens}
  messageCount={contextBudget.messageCount}
  isStreaming={isStreaming}
/>
```

**7b. Add `AutoSummaryPin` below the budget bar:**

```tsx
import { AutoSummaryPin } from './AutoSummaryPin'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getWorkspaceSummary, regenerateWorkspaceSummary } from '../../lib/api'

// Inside the component:
const { data: summary } = useQuery({
  queryKey: ['workspace', 'summary', conversationId],
  queryFn: () => getWorkspaceSummary(conversationId!),
  enabled: !!conversationId,
})

const regenerateMutation = useMutation({
  mutationFn: () => regenerateWorkspaceSummary(conversationId!),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['workspace', 'summary', conversationId] })
  },
})

// In the render, after EnhancedContextBudgetBar:
<AutoSummaryPin
  summary={summary?.summary ?? null}
  updatedAt={summary?.created_at ?? null}
  messagesCovered={summary?.message_count ?? null}
  onRegenerate={() => regenerateMutation.mutate()}
  isRegenerating={regenerateMutation.isPending}
/>
```

**7c. Apply warning tint to the chat area background:**

```tsx
// Compute usage percent from context budget data
const usagePercent = contextBudget.messageTokens > 0
  ? ((contextBudget.messageTokens + contextBudget.summaryTokens) / 1_000_000) * 100
  : 0

// Apply to the chat area container:
<div className={`flex flex-col flex-1 overflow-hidden transition-colors duration-500
                 ${getContextWarningClass(usagePercent)}`}>
  {/* ... budget bar, summary pin, messages, input ... */}
</div>
```

**7d. Update token tracking from WebSocket `token_update` messages:**

In the `useWorkspaceChat` hook (or wherever `token_update` messages are handled), update a state variable that feeds the `EnhancedContextBudgetBar`:

```tsx
// In useWorkspaceChat.ts, handle token_update:
case 'token_update':
  setContextBudget(prev => ({
    ...prev,
    messageTokens: message.token_count,
    messageCount: message.message_count,
  }))
  break
```

---

### 8. `ui/src/hooks/useWorkspaceChat.ts`

**Add context budget state management:**

```tsx
// Add to the hook's state:
const [contextBudget, setContextBudget] = useState<{
  messageTokens: number
  summaryTokens: number
  messageCount: number
}>({
  messageTokens: 0,
  summaryTokens: 0,
  messageCount: 0,
})

// In the WebSocket message handler, add a case for token_update:
case 'token_update':
  setContextBudget(prev => ({
    ...prev,
    messageTokens: data.token_count ?? prev.messageTokens,
    messageCount: data.message_count ?? prev.messageCount,
  }))
  break

// Return contextBudget from the hook:
return {
  // ... existing returns ...
  contextBudget,
}
```

---

### 9. `ui/src/hooks/useWorkspaceConversations.ts`

**Add pin toggle and category change mutations:**

```tsx
export function useTogglePin() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ conversationId, pinned }: { conversationId: number; pinned: boolean }) =>
      updateWorkspaceConversation(conversationId, { pinned }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workspace', 'conversations'] })
    },
  })
}

export function useChangeCategory() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ conversationId, category }: { conversationId: number; category: string }) =>
      updateWorkspaceConversation(conversationId, { category }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workspace', 'conversations'] })
    },
  })
}
```

This assumes Phase 1 already has an `updateWorkspaceConversation` API function. If not, add to `api.ts`:

```typescript
export async function updateWorkspaceConversation(
  conversationId: number,
  update: { title?: string; category?: string; pinned?: boolean }
): Promise<void> {
  await fetchJSON(`/workspace/conversations/${conversationId}`, {
    method: 'PATCH',
    body: JSON.stringify(update),
  })
}
```

---

## Database Migrations

No explicit migration is needed. The workspace database uses SQLAlchemy's `Base.metadata.create_all(engine)` on first access, which auto-creates missing tables.

**New tables created on next server start:**

### `workspace_summaries`
```sql
CREATE TABLE workspace_summaries (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES workspace_conversations(id) ON DELETE CASCADE,
    summary TEXT NOT NULL,
    message_count INTEGER NOT NULL,
    token_estimate INTEGER DEFAULT 0,
    created_at DATETIME
);
CREATE INDEX ix_workspace_summaries_conversation_id ON workspace_summaries(conversation_id);
```

### `workspace_categories`
```sql
CREATE TABLE workspace_categories (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    color VARCHAR(7),
    sort_order INTEGER DEFAULT 0,
    created_at DATETIME
);
```

**Verification:** After starting the server, connect to `~/.autoforge/workspace.db` and run:
```sql
SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;
```
Expected tables: `workspace_categories`, `workspace_conversations`, `workspace_messages`, `workspace_summaries`.

---

## API Endpoint Specifications

All endpoints use the router prefix `/api/workspace`.

### Summary Endpoints

| Method | Path | Description | Request Body | Response |
|--------|------|-------------|-------------|----------|
| GET | `/conversations/{id}/summary` | Get latest summary | - | `SummaryResponse \| null` |
| POST | `/conversations/{id}/summarize` | Force regenerate | - | `SummaryResponse` |

**`SummaryResponse`:**
```json
{
  "id": 1,
  "conversation_id": 42,
  "summary": "This conversation covers...",
  "message_count": 150,
  "token_estimate": 500,
  "created_at": "2026-02-16T12:00:00Z"
}
```

### Category Endpoints

| Method | Path | Description | Request Body | Response |
|--------|------|-------------|-------------|----------|
| GET | `/categories` | List all | - | `CategoryResponse[]` |
| POST | `/categories` | Create | `{ name, color? }` | `CategoryResponse` |
| PATCH | `/categories/{id}` | Update | `{ name?, color? }` | `CategoryResponse` |
| DELETE | `/categories/{id}` | Delete | - | `{ success, message }` |
| POST | `/categories/reorder` | Reorder | `{ ordered_ids: int[] }` | `CategoryResponse[]` |

**`CategoryResponse`:**
```json
{
  "id": 1,
  "name": "Architecture",
  "color": "#3b82f6",
  "sort_order": 0,
  "created_at": "2026-02-16T12:00:00Z"
}
```

**Validation rules:**
- Name is required, cannot be empty
- Name cannot be "Uncategorized" (reserved)
- Name must be unique (409 on conflict)
- Color is optional, must be a 7-char hex string like `#3b82f6`

### Search Endpoint

| Method | Path | Description | Query Params | Response |
|--------|------|-------------|-------------|----------|
| GET | `/search` | Full-text search | `q` (required, min 2 chars), `limit` (default 20) | `SearchResultItem[]` |

**`SearchResultItem`:**
```json
{
  "conversation_id": 42,
  "conversation_title": "Building the auth system",
  "category": "Architecture",
  "matching_excerpts": [
    {
      "message_id": 156,
      "role": "user",
      "excerpt": "...I think we should use JWT tokens for the **auth** system..."
    }
  ]
}
```

---

## Component Specifications

### `EnhancedContextBudgetBar`

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `totalBudget` | `number` | yes | Total context window tokens (default 1M) |
| `messageTokens` | `number` | yes | Tokens used by messages |
| `summaryTokens` | `number` | yes | Tokens used by summary |
| `messageCount` | `number` | yes | Number of messages in context |
| `isStreaming` | `boolean` | no | Show shimmer during streaming |

**Exports:** `EnhancedContextBudgetBar` (default), `getContextWarningClass` (named), `formatTokenCount` (named)

### `AutoSummaryPin`

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `summary` | `string \| null` | yes | Summary text |
| `updatedAt` | `string \| null` | yes | ISO timestamp |
| `messagesCovered` | `number \| null` | yes | Messages covered |
| `onRegenerate` | `() => void` | yes | Regeneration callback |
| `isRegenerating` | `boolean` | no | Loading state |

### `CategoryManager`

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `open` | `boolean` | yes | Whether modal is shown |
| `onClose` | `() => void` | yes | Close callback |
| `categories` | `WorkspaceCategory[]` | yes | Current categories |
| `onCreateCategory` | `(name, color) => Promise<void>` | yes | Create handler |
| `onUpdateCategory` | `(id, name, color) => Promise<void>` | yes | Update handler |
| `onDeleteCategory` | `(id) => Promise<void>` | yes | Delete handler |
| `onReorderCategories` | `(orderedIds) => Promise<void>` | yes | Reorder handler |

### `ConversationSearch`

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `onSelectConversation` | `(id: number) => void` | yes | Navigate to conversation |
| `onFilterChange` | `(filter: string) => void` | yes | Client-side filter fallback |

---

## Testing Checklist

### Backend Tests

1. **Summary generation threshold:**
   - `should_generate_summary(49, None)` returns `False`
   - `should_generate_summary(50, None)` returns `True`
   - `should_generate_summary(75, 50)` returns `False` (already summarized at 50)
   - `should_generate_summary(100, 50)` returns `True` (crossed next threshold)
   - `should_generate_summary(150, 100)` returns `True`

2. **Category CRUD:**
   - Create category with name + color
   - Duplicate name returns 409
   - "Uncategorized" name rejected with 400
   - Delete category moves conversations to Uncategorized
   - Reorder updates sort_order correctly

3. **Search:**
   - Title match returns conversation
   - Message content match returns conversation with excerpt
   - Excerpt contains context around match
   - Results limited to `limit` parameter
   - Query shorter than 2 chars returns 400

4. **Enhanced context loading:**
   - Empty conversation returns empty list
   - Messages loaded in chronological order
   - Total tokens stay within budget
   - At least one message always loaded even if over budget

5. **API endpoints:**
   - `GET /api/workspace/conversations/{id}/summary` returns null when no summary
   - `POST /api/workspace/conversations/{id}/summarize` returns generated summary
   - All category CRUD endpoints return correct status codes
   - Search endpoint validates query length

### Frontend Tests

1. **EnhancedContextBudgetBar:**
   - Renders segments proportional to token counts
   - Shows tooltip text on hover
   - Shows shimmer animation when `isStreaming=true`
   - Shows warning tint when usage > 80%
   - Formats token counts correctly (K, M suffixes)

2. **AutoSummaryPin:**
   - Not rendered when `summary` is null
   - Collapsed by default, expands on click
   - Shows time ago string
   - Regenerate button shows spinner when regenerating
   - Regenerate button triggers callback

3. **CategoryManager:**
   - Lists all categories
   - Create form validates non-empty name
   - Color picker selects preset colors
   - Delete shows confirmation or deletes directly
   - Reorder updates order

4. **ConversationSearch:**
   - Short queries (<3 chars) trigger client-side filter
   - Longer queries trigger server search (debounced)
   - Results show highlighted excerpts
   - Click navigates to conversation
   - Escape clears search

5. **Sidebar grouping:**
   - Pinned conversations appear at top
   - Conversations grouped by category
   - Uncategorized appears last
   - Category sections collapsible
   - Pin/unpin toggles correctly

---

## Important Reminders

### Styling Rules

1. **Use theme-agnostic Tailwind tokens only.** The project has 6 themes. Never hardcode hex colors in component classes. Use: `bg-background`, `text-foreground`, `bg-card`, `bg-muted`, `text-muted-foreground`, `border-border`, `bg-accent`, `text-accent-foreground`, `bg-primary`, `text-primary-foreground`, `bg-destructive`, `text-destructive-foreground`, `bg-popover`, `text-popover-foreground`.
2. **Status colors** use CSS variables: `var(--color-status-pending)`, `var(--color-status-progress)`, `var(--color-status-done)`.
3. **Shadows** use CSS variables: `var(--shadow-sm)`, `var(--shadow)`, `var(--shadow-md)`, `var(--shadow-lg)`.
4. **Transitions** use CSS variables: `var(--transition-fast)` (150ms), `var(--transition-normal)` (250ms).
5. **The only exception** for direct hex colors is in data structures (category color presets stored in the database), never in Tailwind classes applied to elements.

### Architecture Rules

1. **Database is global** at `~/.autoforge/workspace.db`. Do NOT use `project_dir` in any workspace database function. The workspace is project-independent.
2. **Engine caching**: Follow the same pattern as `assistant_database.py` -- single global engine, thread-safe cache, `check_same_thread=False`.
3. **Router prefix**: All workspace endpoints use `APIRouter(prefix="/api/workspace", tags=["workspace"])`.
4. **Session registry**: Keyed by `conversation_id` (integer), not by project name. The workspace has no project context.
5. **Cleanup**: The `cleanup_all_workspace_sessions()` function from Phase 1 is already registered in `server/main.py`'s lifespan handler.

### Security Rules

1. The summary generation service uses the `anthropic` Python SDK directly. Verify it is in `requirements.txt`. If not, add it.
2. The Haiku model is read from `ANTHROPIC_DEFAULT_HAIKU_MODEL` env var with fallback to `claude-3-5-haiku-20241022`.
3. Do not expose raw database errors to the API. Catch `IntegrityError` for unique constraint violations and return 409.

### Code Quality

1. Run `ruff check .` and `mypy .` after all Python changes.
2. Run `cd ui && npm run lint && npm run build` after all TypeScript changes.
3. Fix ALL errors before considering the implementation complete.
4. Every new Python function needs a docstring.
5. Every new TypeScript component needs a JSDoc comment block.

### What NOT to Do

1. Do NOT modify `server/services/assistant_database.py` or `server/services/assistant_chat_session.py`. The workspace is separate.
2. Do NOT create a new database file. Use the existing `workspace.db` from Phase 1.
3. Do NOT add drag-and-drop libraries. Use simple up/down reordering for categories.
4. Do NOT implement full-text search indexing (FTS5). SQLite LIKE queries are sufficient for the expected data volume.
5. Do NOT block the chat WebSocket while generating summaries. Always use `asyncio.create_task`.
