/**
 * Workspace Sidebar
 *
 * Collapsible sidebar that lists workspace conversations grouped by
 * category with pinned items at the top. Provides server-side search,
 * a new-chat button, per-item pin/delete, and a category manager modal.
 */

import { useState, useCallback, useMemo } from 'react'
import {
  Plus,
  Trash2,
  PanelLeftClose,
  PanelLeftOpen,
  MessageSquare,
  Pin,
  Star,
  Settings,
} from 'lucide-react'
import {
  useWorkspaceConversations,
  useDeleteWorkspaceConversation,
  useTogglePin,
  useToggleContextMode,
} from '@/hooks/useWorkspaceConversations'
import {
  useWorkspaceCategories,
  useCreateCategory,
  useUpdateCategory,
  useDeleteCategory,
} from '@/hooks/useWorkspaceCategories'
import { reorderWorkspaceCategories } from '@/lib/api'
import { ConversationSearch } from './ConversationSearch'
import { CategoryManager } from './CategoryManager'
import { Button } from '@/components/ui/button'
import type { WorkspaceConversation, WorkspaceCategory } from '@/lib/types'

interface WorkspaceSidebarProps {
  activeConversationId: number | null
  collapsed: boolean
  onToggleCollapse: () => void
  onNewChat: () => void
  onSelectConversation: (id: number) => void
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

/** Conversation list sidebar with search, categories, pinning, and category management. */
export function WorkspaceSidebar({
  activeConversationId,
  collapsed,
  onToggleCollapse,
  onNewChat,
  onSelectConversation,
}: WorkspaceSidebarProps): React.JSX.Element {
  const [search, setSearch] = useState('')
  const [hoveredId, setHoveredId] = useState<number | null>(null)
  const [showCategoryManager, setShowCategoryManager] = useState(false)
  const [collapsedGroups, setCollapsedGroups] = useState<Record<string, boolean>>({})

  const { data: conversations, isLoading } = useWorkspaceConversations()
  const deleteMutation = useDeleteWorkspaceConversation()
  const { data: categories = [] } = useWorkspaceCategories()
  const createCategoryMut = useCreateCategory()
  const updateCategoryMut = useUpdateCategory()
  const deleteCategoryMut = useDeleteCategory()
  const togglePinMut = useTogglePin()
  const toggleContextModeMut = useToggleContextMode()

  /** Filter conversations by search term (case-insensitive substring). */
  const filtered = useMemo(() => {
    if (!conversations) return []
    if (!search.trim()) return conversations

    const term = search.trim().toLowerCase()
    return conversations.filter((c) =>
      (c.title ?? 'Untitled').toLowerCase().includes(term),
    )
  }, [conversations, search])

  /** Group filtered conversations by category with pinned at top. */
  const grouped = useMemo(() => {
    const groups: Record<string, WorkspaceConversation[]> = {}

    // Pinned conversations go in a special group
    const pinned = filtered.filter(c => c.pinned)
    if (pinned.length > 0) {
      groups['__pinned__'] = pinned
    }

    // Group remaining by category
    const unpinned = filtered.filter(c => !c.pinned)
    for (const conv of unpinned) {
      const cat = conv.category || 'Uncategorized'
      if (!groups[cat]) groups[cat] = []
      groups[cat].push(conv)
    }

    return groups
  }, [filtered])

  const categoryOrder = useMemo(() => {
    const order: string[] = []
    if (grouped['__pinned__']) order.push('__pinned__')
    for (const cat of categories) {
      if (grouped[cat.name]) order.push(cat.name)
    }
    // Add any categories that appear in conversations but not in the categories list
    for (const key of Object.keys(grouped)) {
      if (key !== '__pinned__' && !order.includes(key)) {
        order.push(key)
      }
    }
    return order
  }, [grouped, categories])

  const toggleCollapsed = useCallback((key: string) => {
    setCollapsedGroups(prev => ({ ...prev, [key]: !prev[key] }))
  }, [])

  const handleTogglePin = useCallback((convId: number, pinned: boolean) => {
    togglePinMut.mutate({ conversationId: convId, pinned })
  }, [togglePinMut])

  const handleDelete = useCallback(
    (e: React.MouseEvent, id: number) => {
      e.stopPropagation()
      if (window.confirm('Delete this conversation? This cannot be undone.')) {
        deleteMutation.mutate(id)
      }
    },
    [deleteMutation],
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
        <ConversationSearch
          onSelectConversation={(id) => onSelectConversation(id)}
          onFilterChange={(filter) => setSearch(filter)}
        />
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
          categoryOrder.map(groupKey => {
            const isPin = groupKey === '__pinned__'
            const label = isPin ? 'Pinned' : groupKey
            const category = categories.find((c: WorkspaceCategory) => c.name === groupKey)
            const items = grouped[groupKey]

            return (
              <div key={groupKey} className="mb-2">
                <button
                  onClick={() => toggleCollapsed(groupKey)}
                  className="flex items-center gap-2 w-full px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground hover:text-foreground"
                >
                  {category?.color && (
                    <span
                      className="w-2 h-2 rounded-full flex-shrink-0"
                      style={{ backgroundColor: category.color }}
                    />
                  )}
                  {isPin && <Star size={10} className="text-primary" />}
                  <span className="truncate">{label}</span>
                  <span className="ml-auto text-muted-foreground/50">{items.length}</span>
                </button>

                {!collapsedGroups[groupKey] && items.map((conv) => {
                  const isActive = conv.id === activeConversationId
                  const isHovered = conv.id === hoveredId

                  return (
                    <div
                      key={conv.id}
                      className="relative mb-1"
                      onMouseEnter={() => handleMouseEnter(conv.id)}
                      onMouseLeave={handleMouseLeave}
                    >
                      {/* Context mode badge — top-right corner, clickable to toggle */}
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation()
                          toggleContextModeMut.mutate({
                            conversationId: conv.id,
                            context_mode: conv.context_mode === '1m' ? '200k' : '1m',
                          })
                        }}
                        className={`absolute -top-1 -right-1 z-10 text-[9px] font-mono font-extrabold px-1.5 py-0.5 rounded-md border shadow-sm cursor-pointer transition-colors ${
                          conv.context_mode === '1m'
                            ? 'bg-blue-600 text-white border-blue-400 hover:bg-blue-500'
                            : 'bg-zinc-700 text-zinc-200 border-zinc-500 hover:bg-zinc-600'
                        }`}
                        title={`Switch to ${conv.context_mode === '1m' ? '200K' : '1M'} context`}
                      >
                        {conv.context_mode === '1m' ? '1M' : '200K'}
                      </button>
                      <button
                        type="button"
                        onClick={() => onSelectConversation(conv.id)}
                        className={`w-full flex items-center gap-2 px-2 py-2 rounded-lg border text-left transition-colors ${
                          isActive
                            ? 'bg-accent text-accent-foreground border-primary/30'
                            : 'hover:bg-muted text-foreground border-border'
                        }`}
                        aria-current={isActive ? 'page' : undefined}
                      >
                        {conv.pinned && <Star size={10} className="text-primary flex-shrink-0" />}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1">
                            <span className={`text-xs font-medium truncate ${conv.title ? '' : 'italic text-muted-foreground'}`}>
                              {conv.title ?? 'Untitled'}
                            </span>
                          </div>
                          <span className="text-[10px] text-muted-foreground">
                            {relativeTime(conv.updated_at)}
                          </span>
                        </div>

                        {isHovered && (
                          <div className="flex items-center gap-0.5 flex-shrink-0">
                            <button
                              type="button"
                              onClick={(e) => { e.stopPropagation(); handleTogglePin(conv.id, !conv.pinned) }}
                              className="p-1 rounded hover:bg-accent text-muted-foreground"
                              title={conv.pinned ? 'Unpin' : 'Pin'}
                            >
                              <Pin size={12} />
                            </button>
                            <button
                              type="button"
                              onClick={(e) => handleDelete(e, conv.id)}
                              className="p-1 rounded hover:bg-destructive/10 text-muted-foreground hover:text-destructive"
                              title="Delete"
                            >
                              <Trash2 size={12} />
                            </button>
                          </div>
                        )}
                      </button>
                    </div>
                  )
                })}
              </div>
            )
          })
        )}
      </div>

      {/* Category management */}
      <button
        onClick={() => setShowCategoryManager(true)}
        className="flex items-center gap-2 w-full px-3 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-accent transition-colors border-t border-border"
      >
        <Settings size={14} />
        Manage Categories
      </button>

      {showCategoryManager && (
        <CategoryManager
          open={showCategoryManager}
          onClose={() => setShowCategoryManager(false)}
          categories={categories}
          onCreateCategory={async (name, color) => { await createCategoryMut.mutateAsync({ name, color }) }}
          onUpdateCategory={async (id, name, color) => { await updateCategoryMut.mutateAsync({ id, name, color }) }}
          onDeleteCategory={async (id) => { await deleteCategoryMut.mutateAsync(id) }}
          onReorderCategories={async (orderedIds) => { await reorderWorkspaceCategories(orderedIds) }}
        />
      )}
    </div>
  )
}
