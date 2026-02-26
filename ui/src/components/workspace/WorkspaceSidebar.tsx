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
  CheckSquare,
} from 'lucide-react'
import {
  useWorkspaceConversations,
  useCreateWorkspaceConversation,
  useDeleteWorkspaceConversation,
  useBulkDeleteWorkspaceConversations,
  useTogglePin,
  useCycleModelBadge,
  useWorkspaceProviders,
} from '@/hooks/useWorkspaceConversations'
import { useBackgroundSessions } from '@/hooks/useBackgroundSessions'
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
  DropdownMenuSub,
  DropdownMenuSubTrigger,
  DropdownMenuSubContent,
} from '@/components/ui/dropdown-menu'
import { parseUtcTimestamp } from '@/lib/utils'
import type { WorkspaceConversation, WorkspaceCategory, WorkspaceProvider, EffortLevel } from '@/lib/types'
import type { WorkspaceProviderDef } from '@/lib/api'

/** Model preset option for the sidebar pill selector. */
interface ModelPreset {
  model: string
  context: '1m' | '200k'
  label: string
}

/** Claude-only fallback presets (used when providers haven't loaded yet). */
const CLAUDE_MODEL_PRESETS: ModelPreset[] = [
  { model: 'opus', context: '1m', label: 'Opus 4.6 · 1M' },
  { model: 'sonnet', context: '1m', label: 'Sonnet 4.6 · 1M' },
  { model: 'opus', context: '200k', label: 'Opus 4.6 · 200K' },
]

/** Build model presets from a provider definition. Claude gets context modes; others don't. */
function buildPresetsForProvider(providerId: string, providerDef: WorkspaceProviderDef): ModelPreset[] {
  if (providerId === 'claude') {
    // Claude models get 1M + 200K context variants
    return [
      ...providerDef.models.map(m => ({ model: m.id, context: '1m' as const, label: `${m.name} · 1M` })),
      { model: providerDef.models[0]?.id ?? 'opus', context: '200k' as const, label: `${providerDef.models[0]?.name ?? 'Opus'} · 200K` },
    ]
  }
  // Non-Claude: single context mode, no 200K variant
  return providerDef.models.map(m => ({ model: m.id, context: '1m' as const, label: m.name }))
}

/** Effort level presets with Anthropic's recommended use cases. */
interface EffortPreset {
  key: EffortLevel
  label: string
  useCases: string
}

const EFFORT_PRESETS: EffortPreset[] = [
  { key: 'low', label: 'Low', useCases: 'Quick lookups, classification, routing, sub-agents' },
  { key: 'medium', label: 'Medium', useCases: 'Agentic coding, tool use, code generation' },
  { key: 'high', label: 'High', useCases: 'Complex analysis, nuanced reasoning, quality-critical' },
]

interface WorkspaceSidebarProps {
  activeConversationId: number | null
  /** Set of conversation IDs that are currently streaming (agents actively working). */
  streamingIds?: Set<number>
  collapsed: boolean
  onToggleCollapse: () => void
  /** Called when user starts a new chat with model selection from the dropdown. */
  onNewChat: (model: string, contextMode: '1m' | '200k', effort: EffortLevel, provider?: WorkspaceProvider) => void
  onSelectConversation: (id: number, provider?: string) => void
  /** Called when a conversation is deleted. Parent should clear activeConversationId if it matches. */
  onDeleteConversation?: (id: number) => void
  /** Currently selected working directory (repo path) from the page. */
  selectedWorkingDirectory?: string | null
  /** Callback when the user picks a repo in the naming form. */
  onWorkingDirectoryChange?: (path: string) => void
  /** Current model preset index (synced with WorkspaceChat). */
  modelPresetIndex?: number
  /** Callback when user changes the model preset from the naming form. */
  onModelPresetChange?: (index: number) => void
  /** Current effort level (synced with WorkspaceChat). */
  effortLevel?: EffortLevel
  /** Callback when user changes the effort level from the naming form. */
  onEffortChange?: (effort: EffortLevel) => void
  /** Active provider from the focused dashboard pane (drives which models appear in the dropdown). */
  activeProvider?: WorkspaceProvider
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
  streamingIds,
  collapsed,
  onToggleCollapse,
  onNewChat,
  onSelectConversation,
  onDeleteConversation,
  selectedWorkingDirectory,
  onWorkingDirectoryChange,
  modelPresetIndex = 0,
  onModelPresetChange,
  effortLevel = 'high',
  onEffortChange,
  activeProvider = 'claude',
}: WorkspaceSidebarProps): React.JSX.Element {
  // Fetch provider definitions from backend
  const { data: providers } = useWorkspaceProviders()

  // Build model presets for the active provider (falls back to Claude presets)
  const isClaudeProvider = activeProvider === 'claude'
  const SIDEBAR_MODEL_PRESETS: ModelPreset[] = useMemo(() => {
    if (!providers || !providers[activeProvider]) return CLAUDE_MODEL_PRESETS
    return buildPresetsForProvider(activeProvider, providers[activeProvider])
  }, [providers, activeProvider])

  const [search, setSearch] = useState('')
  const [hoveredId, setHoveredId] = useState<number | null>(null)
  const [showCategoryManager, setShowCategoryManager] = useState(false)
  const [collapsedGroups, setCollapsedGroups] = useState<Record<string, boolean>>({})
  const [selectMode, setSelectMode] = useState(false)
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())

  // Naming form state: when a category is selected from the dropdown,
  // show an inline form to name the new chat before creating it.
  const [namingCategory, setNamingCategory] = useState<string | null>(null)
  const [newChatName, setNewChatName] = useState('')
  const namingInputRef = useRef<HTMLInputElement>(null)

  const { data: conversations, isLoading } = useWorkspaceConversations()
  const { data: bgSessions } = useBackgroundSessions()

  // Build a map of conversation_id → background session state for self-sufficient indicators
  const sessionStateMap = useMemo(() => {
    const map = new Map<number, { state: string; provider: string; startedAt: string | null }>()
    bgSessions?.forEach(s => {
      map.set(s.conversation_id, { state: s.state, provider: s.provider, startedAt: s.started_at })
    })
    return map
  }, [bgSessions])

  const createConversationMut = useCreateWorkspaceConversation()
  const deleteMutation = useDeleteWorkspaceConversation()
  const { data: categories = [] } = useWorkspaceCategories()
  const createCategoryMut = useCreateCategory()
  const updateCategoryMut = useUpdateCategory()
  const deleteCategoryMut = useDeleteCategory()
  const togglePinMut = useTogglePin()
  const cycleModelBadgeMut = useCycleModelBadge()
  const bulkDeleteMutation = useBulkDeleteWorkspaceConversations()

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
    const safeIdx = Math.min(modelPresetIndex, SIDEBAR_MODEL_PRESETS.length - 1)
    const preset = SIDEBAR_MODEL_PRESETS[safeIdx]
    if (!preset) return
    // Only pass effort for Claude 1M context models; others don't support it
    const effort = (isClaudeProvider && preset.context === '1m') ? effortLevel : 'high'
    createConversationMut.mutate({
      title,
      category: namingCategory,
      model: preset.model,
      context_mode: preset.context,
      effort,
      provider: activeProvider,
    }, {
      onSuccess: (newConv) => {
        onSelectConversation(newConv.id, newConv.provider)
        setNamingCategory(null)
        setNewChatName('')
      },
    })
  }, [namingCategory, newChatName, createConversationMut, onSelectConversation, modelPresetIndex, effortLevel, SIDEBAR_MODEL_PRESETS, isClaudeProvider, activeProvider])

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
      deleteMutation.mutate(id)
      // Notify parent so it can clear activeConversationId + disconnect WebSocket
      onDeleteConversation?.(id)
    },
    [deleteMutation, onDeleteConversation],
  )

  const handleToggleSelect = useCallback((id: number) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  const handleBulkDelete = useCallback(() => {
    if (selectedIds.size === 0) return
    const ids = Array.from(selectedIds)
    bulkDeleteMutation.mutate(ids)
    // Notify parent for each deleted id in case active conversation was selected
    for (const id of ids) {
      onDeleteConversation?.(id)
    }
    setSelectedIds(new Set())
    setSelectMode(false)
  }, [selectedIds, bulkDeleteMutation, onDeleteConversation])

  const handleExitSelectMode = useCallback(() => {
    setSelectMode(false)
    setSelectedIds(new Set())
  }, [])

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
        <div className="flex items-center gap-0.5">
          <Button
            variant={selectMode ? 'default' : 'ghost'}
            size="icon-xs"
            onClick={selectMode ? handleExitSelectMode : () => setSelectMode(true)}
            title={selectMode ? 'Exit select mode' : 'Select conversations'}
          >
            {selectMode ? <X size={16} /> : <CheckSquare size={16} />}
          </Button>
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
          <DropdownMenuContent align="start" className="w-56">
            <DropdownMenuLabel className="text-xs">
              {activeProvider === 'claude' ? 'Select model' : `${activeProvider.charAt(0).toUpperCase() + activeProvider.slice(1)} models`}
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            {SIDEBAR_MODEL_PRESETS.map((preset) => {
              // Color coding: provider-specific dot colors
              const dotColor = activeProvider === 'codex'
                ? 'bg-emerald-500'
                : activeProvider === 'gemini'
                  ? 'bg-violet-500'
                  : preset.model === 'sonnet'
                    ? 'bg-violet-500'
                    : preset.context === '1m'
                      ? 'bg-blue-500'
                      : 'bg-zinc-500'

              // Claude Opus 1M: show effort sub-menu (effort only works on Claude Opus)
              if (isClaudeProvider && preset.context === '1m' && preset.model === 'opus') {
                return (
                  <DropdownMenuSub key={preset.label}>
                    <DropdownMenuSubTrigger className="gap-2 text-xs">
                      <span className={`w-2 h-2 rounded-full flex-shrink-0 ${dotColor}`} />
                      <span className="font-medium">{preset.label}</span>
                      <span className="ml-auto text-[10px] text-muted-foreground">API key</span>
                    </DropdownMenuSubTrigger>
                    <DropdownMenuSubContent className="w-56">
                      <DropdownMenuLabel className="text-[10px]">Thinking Effort</DropdownMenuLabel>
                      <DropdownMenuSeparator />
                      {EFFORT_PRESETS.map((ep) => (
                        <DropdownMenuItem
                          key={ep.key}
                          onClick={() => onNewChat(preset.model, preset.context, ep.key, activeProvider)}
                          className="gap-2 text-xs"
                        >
                          <span className={`w-2 h-2 rounded-full flex-shrink-0 ${
                            ep.key === 'low' ? 'bg-emerald-500' : ep.key === 'medium' ? 'bg-blue-500' : 'bg-orange-500'
                          }`} />
                          <div className="flex flex-col gap-0">
                            <span className="font-semibold">{ep.label}</span>
                            <span className="text-[10px] text-muted-foreground leading-tight">{ep.useCases}</span>
                          </div>
                        </DropdownMenuItem>
                      ))}
                    </DropdownMenuSubContent>
                  </DropdownMenuSub>
                )
              }

              // Non-Claude models or Claude 200K: direct click, no effort choice
              return (
                <DropdownMenuItem
                  key={preset.label}
                  onClick={() => onNewChat(preset.model, preset.context, 'high', activeProvider)}
                  className="gap-2 text-xs"
                >
                  <span className={`w-2 h-2 rounded-full flex-shrink-0 ${dotColor}`} />
                  <span className="font-medium">{preset.label}</span>
                  {isClaudeProvider && (
                    <span className="ml-auto text-[10px] text-muted-foreground">
                      {preset.context === '200k' ? 'Subscription' : 'API key'}
                    </span>
                  )}
                </DropdownMenuItem>
              )
            })}
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
                // Provider-specific active colors
                const activeColor = activeProvider === 'codex'
                  ? 'bg-emerald-600 text-white shadow-inner'
                  : activeProvider === 'gemini'
                    ? 'bg-violet-600 text-white shadow-inner'
                    : preset.model === 'sonnet'
                      ? 'bg-violet-500 text-white shadow-inner'
                      : preset.context === '1m'
                        ? 'bg-primary text-primary-foreground shadow-inner'
                        : 'bg-zinc-600 text-white shadow-inner'
                return (
                  <button
                    key={preset.label}
                    type="button"
                    role="radio"
                    aria-checked={isActive}
                    onClick={() => onModelPresetChange?.(idx)}
                    className={`flex-1 px-1.5 py-1 text-[10px] font-semibold whitespace-nowrap transition-all duration-150 ${
                      isActive
                        ? activeColor
                        : 'bg-card text-muted-foreground hover:bg-muted hover:text-foreground'
                    } ${idx === 0 ? 'rounded-l-full' : ''} ${idx === SIDEBAR_MODEL_PRESETS.length - 1 ? 'rounded-r-full' : 'border-r border-border'}`}
                  >
                    {preset.label}
                  </button>
                )
              })}
            </div>
          </div>
          {/* Effort level selector — only shown for Claude provider, active for Opus 1M */}
          {isClaudeProvider && (() => {
            const selectedPreset = SIDEBAR_MODEL_PRESETS[modelPresetIndex]
            const isOpus1M = selectedPreset?.context === '1m' && selectedPreset?.model === 'opus'
            return (
              <div className={`mb-1.5 transition-opacity duration-150 ${isOpus1M ? '' : 'opacity-35 pointer-events-none'}`}>
                <span className="text-[10px] text-muted-foreground mb-0.5 block">
                  Thinking Effort {!isOpus1M && <span className="italic">(Opus 1M only)</span>}
                </span>
                <div className="flex rounded-full border border-border overflow-hidden shadow-sm" role="radiogroup" aria-label="Thinking effort level">
                  {EFFORT_PRESETS.map((preset, idx) => {
                    const isActive = effortLevel === preset.key
                    const activeClass = preset.key === 'low'
                      ? 'bg-emerald-500 text-white shadow-inner'
                      : preset.key === 'medium'
                        ? 'bg-blue-500 text-white shadow-inner'
                        : 'bg-orange-500 text-white shadow-inner'
                    return (
                      <button
                        key={preset.key}
                        type="button"
                        role="radio"
                        aria-checked={isActive}
                        disabled={!isOpus1M}
                        onClick={() => onEffortChange?.(preset.key)}
                        title={preset.useCases}
                        className={`flex-1 px-1.5 py-1 text-[10px] font-semibold whitespace-nowrap transition-all duration-150 ${
                          isActive ? activeClass : 'bg-card text-muted-foreground hover:bg-muted hover:text-foreground'
                        } ${idx === 0 ? 'rounded-l-full' : ''} ${idx === EFFORT_PRESETS.length - 1 ? 'rounded-r-full' : 'border-r border-border'}`}
                      >
                        {preset.label}
                      </button>
                    )
                  })}
                </div>
                {isOpus1M && (
                  <span className="text-[9px] text-muted-foreground mt-0.5 block">
                    {EFFORT_PRESETS.find(p => p.key === effortLevel)?.useCases}
                  </span>
                )}
              </div>
            )
          })()}
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

      {/* Bulk action bar */}
      {selectMode && (
        <div className="px-3 py-1.5 border-b border-border bg-muted/50 flex items-center justify-between gap-2">
          <span className="text-xs text-muted-foreground">
            {selectedIds.size} selected
          </span>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              className="h-6 text-xs px-2"
              onClick={() => {
                if (!conversations) return
                const allIds = new Set(conversations.map(c => c.id))
                setSelectedIds(prev => prev.size === allIds.size ? new Set() : allIds)
              }}
            >
              {conversations && selectedIds.size === conversations.length ? 'None' : 'All'}
            </Button>
            <Button
              variant="destructive"
              size="sm"
              className="h-6 text-xs px-2"
              onClick={handleBulkDelete}
              disabled={selectedIds.size === 0 || bulkDeleteMutation.isPending}
            >
              <Trash2 size={12} className="mr-1" />
              Delete{selectedIds.size > 0 ? ` (${selectedIds.size})` : ''}
            </Button>
          </div>
        </div>
      )}

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
                  const isStreaming = streamingIds?.has(conv.id) ?? false

                  // Background session state for richer indicators
                  const bgState = sessionStateMap.get(conv.id)
                  const isRunningBg = bgState && (bgState.state === 'running' || bgState.state === 'streaming')
                  const isWaitingInput = bgState?.state === 'waiting_input'
                  const isCompletedRecent = bgState?.state === 'completed'
                  const isFailedBg = bgState?.state === 'failed'
                  // Show activity from either WebSocket streaming or background session
                  const showActivity = isStreaming || isRunningBg

                  return (
                    <div
                      key={conv.id}
                      className="relative mb-1"
                      onMouseEnter={() => handleMouseEnter(conv.id)}
                      onMouseLeave={handleMouseLeave}
                    >
                      {/* Model+context badge — top-right corner. Claude: clickable to cycle. Others: static label. */}
                      {(() => {
                        const model = conv.model ?? 'opus'
                        const ctx = conv.context_mode ?? '1m'
                        const convProvider = conv.provider ?? 'claude'

                        // Non-Claude providers: static badge showing model ID
                        if (convProvider !== 'claude') {
                          const badgeColor = convProvider === 'codex'
                            ? 'bg-emerald-600 text-white border-emerald-400'
                            : 'bg-violet-600 text-white border-violet-400'
                          return (
                            <span
                              className={`absolute -top-1 -right-1 z-10 text-[9px] font-mono font-extrabold px-1.5 py-0.5 rounded-md border shadow-sm ${badgeColor}`}
                              title={`${convProvider}: ${model}`}
                            >
                              {model}
                            </span>
                          )
                        }

                        // Claude: clickable cycling badge
                        const abbr = model === 'sonnet' ? 'S' : 'O'
                        const badgeLabel = `${abbr}\u00B7${ctx === '1m' ? '1M' : '200K'}`

                        // Cycle: O-1M -> S-1M -> O-200K -> O-1M
                        const cycleNext = () => {
                          if (model === 'opus' && ctx === '1m') return { model: 'sonnet', context_mode: '1m' }
                          if (model === 'sonnet' && ctx === '1m') return { model: 'opus', context_mode: '200k' }
                          if (model === 'opus' && ctx === '200k') return { model: 'opus', context_mode: '1m' }
                          return { model: 'opus', context_mode: '1m' }
                        }
                        const next = cycleNext()

                        // Color-code: blue for opus+1M, violet for sonnet+1M, zinc for 200K
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
                      {/* Streaming accent bar — glowing left edge when agent is active */}
                      {showActivity && (
                        <div className="absolute left-0 top-1 bottom-1 w-0.5 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(0,180,216,0.6)] animate-pulse z-10" />
                      )}
                      {/* Waiting input accent bar — yellow glow */}
                      {isWaitingInput && !showActivity && (
                        <div className="absolute left-0 top-1 bottom-1 w-0.5 rounded-full bg-yellow-400 shadow-[0_0_8px_rgba(234,179,8,0.6)] animate-pulse z-10" />
                      )}
                      {/* Failed accent bar — red */}
                      {isFailedBg && !showActivity && !isWaitingInput && (
                        <div className="absolute left-0 top-1 bottom-1 w-0.5 rounded-full bg-red-400 z-10" />
                      )}
                      <button
                        type="button"
                        onClick={() => selectMode ? handleToggleSelect(conv.id) : onSelectConversation(conv.id, conv.provider)}
                        className={`w-full flex items-center gap-2 px-2 py-2 rounded-lg border text-left transition-colors overflow-hidden ${
                          selectMode && selectedIds.has(conv.id)
                            ? 'bg-destructive/10 text-foreground border-destructive/30'
                            : isActive
                              ? 'bg-accent text-accent-foreground border-primary/30'
                              : 'hover:bg-muted text-foreground border-border'
                        }`}
                        aria-current={isActive ? 'page' : undefined}
                      >
                        {/* Checkbox in select mode */}
                        {selectMode && (
                          <input
                            type="checkbox"
                            checked={selectedIds.has(conv.id)}
                            onChange={() => handleToggleSelect(conv.id)}
                            onClick={(e) => e.stopPropagation()}
                            className="h-3.5 w-3.5 rounded border-border text-primary flex-shrink-0 cursor-pointer"
                          />
                        )}
                        {!selectMode && conv.pinned && <Star size={10} className="text-primary flex-shrink-0" />}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1">
                            {/* Pulsing dot — running/streaming */}
                            {showActivity && (
                              <span className="relative flex h-2 w-2 flex-shrink-0">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500" />
                              </span>
                            )}
                            {/* Pulsing dot — waiting for input */}
                            {isWaitingInput && !showActivity && (
                              <span className="relative flex h-2 w-2 flex-shrink-0">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-yellow-400 opacity-75" />
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-yellow-500" />
                              </span>
                            )}
                            {/* Green check — recently completed */}
                            {isCompletedRecent && !showActivity && !isWaitingInput && (
                              <span className="flex h-2 w-2 flex-shrink-0">
                                <span className="inline-flex rounded-full h-2 w-2 bg-green-500" />
                              </span>
                            )}
                            {/* Red dot — failed */}
                            {isFailedBg && !showActivity && !isWaitingInput && !isCompletedRecent && (
                              <span className="flex h-2 w-2 flex-shrink-0">
                                <span className="inline-flex rounded-full h-2 w-2 bg-red-500" />
                              </span>
                            )}
                            <span className={`text-xs font-medium truncate ${conv.title ? '' : 'italic text-muted-foreground'}`}>
                              {conv.title ?? 'Untitled'}
                            </span>
                          </div>
                          <span className="text-[10px] text-muted-foreground">
                            {relativeTime(conv.updated_at)}
                          </span>
                        </div>

                        {/* Shimmer sweep when active */}
                        {showActivity && (
                          <div className="absolute inset-0 pointer-events-none overflow-hidden rounded-lg">
                            <div className="absolute top-0 right-0 h-full w-12 animate-shimmer bg-gradient-to-r from-transparent via-white/10 to-transparent" />
                          </div>
                        )}

                        {!selectMode && isHovered && (
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
