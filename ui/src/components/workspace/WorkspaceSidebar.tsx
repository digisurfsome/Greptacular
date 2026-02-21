/**
 * Workspace Sidebar
 *
 * Collapsible sidebar that lists workspace conversations grouped by
 * category with pinned items at the top. Provides server-side search,
 * a new-chat button, per-item pin/delete, and a category manager modal.
 */

import { useState, useCallback, useMemo, useRef, useEffect } from 'react'
import {
  Plus,
  Trash2,
  PanelLeftClose,
  PanelLeftOpen,
  MessageSquare,
  Pin,
  Star,
  Settings,
  ChevronDown,
  X,
} from 'lucide-react'
import {
  useWorkspaceConversations,
  useCreateWorkspaceConversation,
  useDeleteWorkspaceConversation,
  useTogglePin,
  useCycleModelBadge,
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
import { RepoSelector } from './RepoSelector'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu'
import { parseUtcTimestamp } from '@/lib/utils'
import type { WorkspaceConversation, WorkspaceCategory } from '@/lib/types'

/** Model preset option for the sidebar pill selector. */
interface ModelPreset {
  model: 'opus' | 'sonnet'
  context: '1m' | '200k'
  label: string
}

const SIDEBAR_MODEL_PRESETS: ModelPreset[] = [
  { model: 'opus', context: '1m', label: 'Opus 4.6 · 1M' },
  { model: 'opus', context: '200k', label: 'Opus 4.6 · 200K' },
  { model: 'sonnet', context: '200k', label: 'Sonnet 4.6 · 200K' },
]

interface WorkspaceSidebarProps {
  activeConversationId: number | null
  collapsed: boolean
  onToggleCollapse: () => void
  /** Called when user starts a new chat with model selection from the dropdown. */
  onNewChat: (model: 'opus' | 'sonnet', contextMode: '1m' | '200k') => void
  onSelectConversation: (id: number) => void
  /** Currently selected working directory (repo path) from the page. */
  selectedWorkingDirectory?: string | null
  /** Callback when the user picks a repo in the naming form. */
  onWorkingDirectoryChange?: (path: string) => void
  /** Current model preset index (synced with WorkspaceChat). */
  modelPresetIndex?: number
  /** Callback when user changes the model preset from the naming form. */
  onModelPresetChange?: (index: number) => void
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Format a date string as a human-friendly relative time. */
function relativeTime(dateString: string | null): string {
  if (!dateString) return ''

  const date = parseUtcTimestamp(dateString)
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
  selectedWorkingDirectory,
  onWorkingDirectoryChange,
  modelPresetIndex = 0,
  onModelPresetChange,
}: WorkspaceSidebarProps): React.JSX.Element {
  const [search, setSearch] = useState('')
  const [hoveredId, setHoveredId] = useState<number | null>(null)
  const [showCategoryManager, setShowCategoryManager] = useState(false)
  const [collapsedGroups, setCollapsedGroups] = useState<Record<string, boolean>>({})

  // Naming form state: when a category is selected from the dropdown,
  // show an inline form to name the new chat before creating it.
  const [namingCategory, setNamingCategory] = useState<string | null>(null)
  const [newChatName, setNewChatName] = useState('')
  const namingInputRef = useRef<HTMLInputElement>(null)

  const { data: conversations, isLoading } = useWorkspaceConversations()
  const createConversationMut = useCreateWorkspaceConversation()
  const deleteMutation = useDeleteWorkspaceConversation()
  const { data: categories = [] } = useWorkspaceCategories()
  const createCategoryMut = useCreateCategory()
  const updateCategoryMut = useUpdateCategory()
  const deleteCategoryMut = useDeleteCategory()
  const togglePinMut = useTogglePin()
  const cycleModelBadgeMut = useCycleModelBadge()

  // Focus the naming input when it appears
  useEffect(() => {
    if (namingCategory !== null) {
      // Small delay to allow DOM render
      const timer = setTimeout(() => namingInputRef.current?.focus(), 50)
      return () => clearTimeout(timer)
    }
  }, [namingCategory])

  /** Open the naming form for a specific category. */
  const handleOpenNamingForm = useCallback((categoryName: string) => {
    setNamingCategory(categoryName)
    setNewChatName('')
  }, [])

  /** Create the named conversation and select it. */
  const handleCreateNamedChat = useCallback(() => {
    if (!namingCategory) return
    const title = newChatName.trim() || undefined
    createConversationMut.mutate({ title, category: namingCategory }, {
      onSuccess: (newConv) => {
        onSelectConversation(newConv.id)
        setNamingCategory(null)
        setNewChatName('')
      },
    })
  }, [namingCategory, newChatName, createConversationMut, onSelectConversation])

  /** Cancel the naming form. */
  const handleCancelNaming = useCallback(() => {
    setNamingCategory(null)
    setNewChatName('')
  }, [])

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

      {/* New Chat button with model selection dropdown + category dropdown */}
      <div className="px-3 py-2 flex gap-1">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button className="flex-1">
              <Plus size={16} />
              New Chat
              <ChevronDown size={12} className="ml-1 opacity-60" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-52">
            <DropdownMenuLabel className="text-xs">Select model</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {SIDEBAR_MODEL_PRESETS.map((preset) => (
              <DropdownMenuItem
                key={preset.label}
                onClick={() => onNewChat(preset.model, preset.context)}
                className="gap-2 text-xs"
              >
                <span
                  className={`w-2 h-2 rounded-full flex-shrink-0 ${
                    preset.model === 'sonnet'
                      ? 'bg-violet-500'
                      : preset.context === '1m'
                        ? 'bg-blue-500'
                        : 'bg-zinc-500'
                  }`}
                />
                <span className="font-medium">{preset.label}</span>
                <span className="ml-auto text-[10px] text-muted-foreground">
                  {preset.context === '200k' ? 'Subscription' : 'API key'}
                </span>
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
        {categories.length > 0 && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button size="icon" variant="outline" className="shrink-0 w-8" title="New chat in category...">
                <ChevronDown size={14} />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48">
              <DropdownMenuLabel className="text-xs">New chat in category</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {categories.map((cat) => (
                <DropdownMenuItem
                  key={cat.id}
                  onClick={() => handleOpenNamingForm(cat.name)}
                  className="gap-2 text-xs"
                >
                  {cat.color && (
                    <span
                      className="w-2 h-2 rounded-full flex-shrink-0"
                      style={{ backgroundColor: cat.color }}
                    />
                  )}
                  {cat.name}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>

      {/* Naming form: slides in when a category is selected from the dropdown */}
      {namingCategory !== null && (
        <div className="px-3 py-2 border-b border-border bg-muted/50 animate-in slide-in-from-top-2 duration-150">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              New chat in {namingCategory}
            </span>
            <button
              type="button"
              onClick={handleCancelNaming}
              className="p-0.5 rounded hover:bg-accent text-muted-foreground hover:text-foreground"
              title="Cancel"
            >
              <X size={12} />
            </button>
          </div>
          <input
            ref={namingInputRef}
            type="text"
            value={newChatName}
            onChange={(e) => setNewChatName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault()
                handleCreateNamedChat()
              } else if (e.key === 'Escape') {
                handleCancelNaming()
              }
            }}
            placeholder="Name"
            className="w-full text-xs bg-input border border-border rounded px-2 py-1.5 outline-none ring-ring focus:ring-1 text-foreground placeholder:text-muted-foreground mb-1.5"
            aria-label="Chat name"
          />
          {/* Repo selector — pick a repo before starting the chat */}
          <div className="mb-1.5">
            <span className="text-[10px] text-muted-foreground mb-0.5 block">Repository</span>
            <RepoSelector
              onSelect={(path) => onWorkingDirectoryChange?.(path)}
              selectedPath={selectedWorkingDirectory ?? null}
            />
          </div>
          {/* Model preset pill — pick model + context before starting */}
          <div className="mb-1.5">
            <span className="text-[10px] text-muted-foreground mb-0.5 block">Model</span>
            <div className="flex rounded-full border border-border overflow-hidden shadow-sm" role="radiogroup" aria-label="Model selection">
              {SIDEBAR_MODEL_PRESETS.map((preset, idx) => {
                const isActive = modelPresetIndex === idx
                return (
                  <button
                    key={preset.label}
                    type="button"
                    role="radio"
                    aria-checked={isActive}
                    onClick={() => onModelPresetChange?.(idx)}
                    className={`flex-1 px-1.5 py-1 text-[10px] font-semibold whitespace-nowrap transition-all duration-150 ${
                      isActive
                        ? preset.model === 'sonnet'
                          ? 'bg-violet-500 text-white shadow-inner'
                          : preset.context === '1m'
                            ? 'bg-primary text-primary-foreground shadow-inner'
                            : 'bg-zinc-600 text-white shadow-inner'
                        : 'bg-card text-muted-foreground hover:bg-muted hover:text-foreground'
                    } ${idx === 0 ? 'rounded-l-full' : ''} ${idx === SIDEBAR_MODEL_PRESETS.length - 1 ? 'rounded-r-full' : 'border-r border-border'}`}
                  >
                    {preset.label}
                  </button>
                )
              })}
            </div>
          </div>
          <Button
            size="sm"
            className="w-full h-7 text-xs"
            onClick={handleCreateNamedChat}
            disabled={createConversationMut.isPending}
          >
            {createConversationMut.isPending ? 'Creating...' : 'Start Chat'}
          </Button>
        </div>
      )}

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
                      {/* Model+context badge — top-right corner, clickable to cycle O-1M -> O-200K -> S-200K -> O-1M */}
                      {(() => {
                        const model = conv.model ?? 'opus'
                        const ctx = conv.context_mode ?? '1m'
                        const abbr = model === 'sonnet' ? 'S' : 'O'
                        const badgeLabel = `${abbr}\u00B7${ctx === '1m' ? '1M' : '200K'}`

                        // Cycle: O-1M -> O-200K -> S-200K -> O-1M
                        // Sonnet does not support the 1M context beta, so skip that combination.
                        const cycleNext = () => {
                          if (model === 'opus' && ctx === '1m') return { model: 'opus' as const, context_mode: '200k' as const }
                          if (model === 'opus' && ctx === '200k') return { model: 'sonnet' as const, context_mode: '200k' as const }
                          if (model === 'sonnet') return { model: 'opus' as const, context_mode: '1m' as const }
                          return { model: 'opus' as const, context_mode: '1m' as const }
                        }
                        const next = cycleNext()

                        // Color-code: blue for opus+1M, violet for sonnet, zinc for 200K
                        const badgeColor = model === 'sonnet'
                          ? 'bg-violet-600 text-white border-violet-400 hover:bg-violet-500'
                          : ctx === '1m'
                            ? 'bg-blue-600 text-white border-blue-400 hover:bg-blue-500'
                            : 'bg-zinc-700 text-zinc-200 border-zinc-500 hover:bg-zinc-600'

                        return (
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation()
                              cycleModelBadgeMut.mutate({
                                conversationId: conv.id,
                                model: next.model,
                                context_mode: next.context_mode,
                              })
                            }}
                            className={`absolute -top-1 -right-1 z-10 text-[9px] font-mono font-extrabold px-1.5 py-0.5 rounded-md border shadow-sm cursor-pointer transition-colors ${badgeColor}`}
                            title={`${model === 'opus' ? 'Opus' : 'Sonnet'} · ${ctx === '1m' ? '1M' : '200K'} (click to cycle)`}
                          >
                            {badgeLabel}
                          </button>
                        )
                      })()}
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
