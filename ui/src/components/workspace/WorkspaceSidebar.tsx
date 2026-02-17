/**
 * Workspace Sidebar
 *
 * Collapsible sidebar that lists workspace conversations grouped by date
 * (Today, Yesterday, This Week, Older). Provides search filtering, a
 * new-chat button, and per-item delete with confirmation. The active
 * conversation is visually highlighted.
 */

import { useState, useCallback, useMemo } from 'react'
import {
  Plus,
  Search,
  Trash2,
  PanelLeftClose,
  PanelLeftOpen,
  MessageSquare,
} from 'lucide-react'
import {
  useWorkspaceConversations,
  useDeleteWorkspaceConversation,
} from '@/hooks/useWorkspaceConversations'
import { Button } from '@/components/ui/button'
import type { WorkspaceConversation } from '@/lib/types'

interface WorkspaceSidebarProps {
  activeConversationId: number | null
  collapsed: boolean
  onToggleCollapse: () => void
  onNewChat: () => void
  onSelectConversation: (id: number) => void
}

// ---------------------------------------------------------------------------
// Category badge colors
// ---------------------------------------------------------------------------

const categoryColors: Record<string, string> = {
  general: 'bg-secondary text-secondary-foreground',
  debugging: 'bg-destructive/10 text-destructive',
  refactoring: 'bg-primary/10 text-primary',
  feature: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300',
  exploration: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300',
}

// ---------------------------------------------------------------------------
// Date grouping helpers
// ---------------------------------------------------------------------------

type DateGroup = 'Today' | 'Yesterday' | 'This Week' | 'Older'

/** Classify a date string into a display group relative to the current day. */
function getDateGroup(dateString: string | null): DateGroup {
  if (!dateString) return 'Older'

  const date = new Date(dateString)
  const now = new Date()

  // Zero-out time portions for clean day comparison
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const target = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  const diffMs = today.getTime() - target.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays === 0) return 'Today'
  if (diffDays === 1) return 'Yesterday'
  if (diffDays < 7) return 'This Week'
  return 'Older'
}

/** Format a date string as a human-friendly relative time. */
function relativeTime(dateString: string | null): string {
  if (!dateString) return ''

  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMinutes = Math.floor(diffMs / 60_000)
  const diffHours = Math.floor(diffMs / 3_600_000)
  const diffDays = Math.floor(diffMs / 86_400_000)

  if (diffMinutes < 1) return 'just now'
  if (diffMinutes < 60) return `${diffMinutes}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  return `${diffDays}d ago`
}

// Ordered groups for rendering
const GROUP_ORDER: DateGroup[] = ['Today', 'Yesterday', 'This Week', 'Older']

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

/** Conversation list sidebar with search, new chat, and date-grouped items. */
export function WorkspaceSidebar({
  activeConversationId,
  collapsed,
  onToggleCollapse,
  onNewChat,
  onSelectConversation,
}: WorkspaceSidebarProps): React.JSX.Element {
  const [search, setSearch] = useState('')
  const [hoveredId, setHoveredId] = useState<number | null>(null)

  const { data: conversations, isLoading } = useWorkspaceConversations()
  const deleteMutation = useDeleteWorkspaceConversation()

  /** Filter conversations by search term (case-insensitive substring). */
  const filtered = useMemo(() => {
    if (!conversations) return []
    if (!search.trim()) return conversations

    const term = search.trim().toLowerCase()
    return conversations.filter((c) =>
      (c.title ?? 'Untitled').toLowerCase().includes(term),
    )
  }, [conversations, search])

  /** Group filtered conversations by date. */
  const grouped = useMemo(() => {
    const groups: Record<DateGroup, WorkspaceConversation[]> = {
      Today: [],
      Yesterday: [],
      'This Week': [],
      Older: [],
    }

    for (const conv of filtered) {
      const group = getDateGroup(conv.updated_at)
      groups[group].push(conv)
    }

    return groups
  }, [filtered])

  const handleDelete = useCallback(
    (e: React.MouseEvent, id: number) => {
      e.stopPropagation()
      if (window.confirm('Delete this conversation? This cannot be undone.')) {
        deleteMutation.mutate(id)
      }
    },
    [deleteMutation],
  )

  const handleSearchChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setSearch(e.target.value)
    },
    [],
  )

  const handleMouseEnter = useCallback((id: number) => {
    setHoveredId(id)
  }, [])

  const handleMouseLeave = useCallback(() => {
    setHoveredId(null)
  }, [])

  return (
    <div
      className={`flex flex-col border-r border-border bg-card transition-all duration-200 ${
        collapsed ? 'w-0 overflow-hidden' : 'w-72'
      }`}
    >
      {/* Collapse toggle */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-border">
        <span className="text-sm font-medium text-foreground truncate">
          Conversations
        </span>
        <Button
          variant="ghost"
          size="icon-xs"
          onClick={onToggleCollapse}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? (
            <PanelLeftOpen size={16} />
          ) : (
            <PanelLeftClose size={16} />
          )}
        </Button>
      </div>

      {/* New Chat button */}
      <div className="px-3 py-2">
        <Button
          className="w-full"
          onClick={onNewChat}
        >
          <Plus size={16} />
          New Chat
        </Button>
      </div>

      {/* Search */}
      <div className="px-3 pb-2">
        <div className="relative">
          <Search
            size={14}
            className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground"
          />
          <input
            type="text"
            value={search}
            onChange={handleSearchChange}
            placeholder="Search conversations..."
            className="w-full pl-8 pr-3 py-1.5 text-xs border border-border rounded bg-input text-foreground placeholder:text-muted-foreground outline-none ring-ring focus:ring-1"
            aria-label="Search conversations"
          />
        </div>
      </div>

      {/* Conversation list */}
      <div className="flex-1 overflow-y-auto px-1">
        {isLoading ? (
          <div className="flex items-center justify-center py-8 text-muted-foreground text-xs">
            Loading...
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 gap-2 text-muted-foreground text-xs">
            <MessageSquare size={20} strokeWidth={1.5} />
            <span>{search ? 'No matching conversations' : 'No conversations yet'}</span>
          </div>
        ) : (
          GROUP_ORDER.map((group) => {
            const items = grouped[group]
            if (items.length === 0) return null

            return (
              <div key={group} className="mb-2">
                {/* Group heading */}
                <div className="px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                  {group}
                </div>

                {/* Conversation items */}
                {items.map((conv) => {
                  const isActive = conv.id === activeConversationId
                  const isHovered = conv.id === hoveredId
                  const badgeClass =
                    categoryColors[conv.category] ?? categoryColors.general

                  return (
                    <button
                      key={conv.id}
                      type="button"
                      onClick={() => onSelectConversation(conv.id)}
                      onMouseEnter={() => handleMouseEnter(conv.id)}
                      onMouseLeave={handleMouseLeave}
                      className={`w-full flex items-start gap-2 px-2 py-2 rounded-md text-left transition-colors ${
                        isActive
                          ? 'bg-accent text-accent-foreground'
                          : 'hover:bg-muted text-foreground'
                      }`}
                      aria-current={isActive ? 'page' : undefined}
                    >
                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-1.5">
                          <span
                            className={`text-xs font-medium truncate ${
                              conv.title ? '' : 'italic text-muted-foreground'
                            }`}
                          >
                            {conv.title ?? 'Untitled'}
                          </span>
                        </div>

                        <div className="flex items-center gap-1.5 mt-0.5">
                          <span
                            className={`inline-block text-[10px] px-1.5 py-0.5 rounded-full font-medium ${badgeClass}`}
                          >
                            {conv.category}
                          </span>
                          <span className="text-[10px] text-muted-foreground">
                            {relativeTime(conv.updated_at)}
                          </span>
                        </div>
                      </div>

                      {/* Delete button (visible on hover) */}
                      {isHovered && (
                        <button
                          type="button"
                          onClick={(e) => handleDelete(e, conv.id)}
                          className="flex-shrink-0 p-1 rounded hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors"
                          title="Delete conversation"
                          aria-label={`Delete conversation: ${conv.title ?? 'Untitled'}`}
                        >
                          <Trash2 size={14} />
                        </button>
                      )}
                    </button>
                  )
                })}
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
