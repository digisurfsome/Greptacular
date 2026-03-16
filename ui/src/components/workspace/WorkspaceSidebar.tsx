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
  FolderPlus,
} from 'lucide-react'
import {
  useWorkspaceConversations,
  useCreateWorkspaceConversation,
  useUpdateWorkspaceConversation,
  useDeleteWorkspaceConversation,
  useBulkDeleteWorkspaceConversations,
  useTogglePin,
  useCycleModelBadge,
  useWorkspaceProviders,
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
// Dropdown menu imports removed — new-chat flow uses inline form instead
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
  { model: 'opus', context: '200k', label: 'Opus 4.6 · 200K' },
  { model: 'sonnet', context: '200k', label: 'Sonnet 4.6 · 200K' },
  { model: 'haiku', context: '200k', label: 'Haiku · 200K' },
  { model: 'opus', context: '1m', label: 'Opus 4.6 · 1M' },
  { model: 'sonnet', context: '1m', label: 'Sonnet 4.6 · 1M' },
]

/** Build model presets from a provider definition. Claude gets context modes; others use supports_1m. */
function buildPresetsForProvider(providerId: string, providerDef: WorkspaceProviderDef): ModelPreset[] {
  if (providerId === 'claude') {
    // Claude: 200K and 1M variants (all subscription billing) for models that support each
    const presets200k = providerDef.models.map(m => ({ model: m.id, context: '200k' as const, label: `${m.name} · 200K` }))
    const presets1m = providerDef.models
      .filter(m => m.id !== 'haiku') // Haiku doesn't support 1M context beta
      .map(m => ({ model: m.id, context: '1m' as const, label: `${m.name} · 1M` }))
    return [...presets200k, ...presets1m]
  }
  // Non-Claude: base preset for each model, plus 1M variant for models that support it
  const presets: ModelPreset[] = []
  for (const m of providerDef.models) {
    presets.push({ model: m.id, context: '200k' as const, label: m.name })
    if (m.supports_1m) {
      presets.push({ model: m.id, context: '1m' as const, label: `${m.name} · 1M` })
    }
  }
  return presets
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
  // onNewChat is kept in the interface for backward compatibility but no longer
  // used internally — new-chat creation goes through the inline form instead.
  onNewChat: _onNewChat,
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
  void _onNewChat // suppress unused-variable lint warning
  // Fetch provider definitions from backend
  const { data: providers } = useWorkspaceProviders()

  const [search, setSearch] = useState('')
  const [hoveredId, setHoveredId] = useState<number | null>(null)
  const [showCategoryManager, setShowCategoryManager] = useState(false)
  const [collapsedGroups, setCollapsedGroups] = useState<Record<string, boolean>>({})
  const [selectMode, setSelectMode] = useState(false)
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())

  // Inline edit popover: which conversation is currently being edited (repo/folder)
  const [editingConvId, setEditingConvId] = useState<number | null>(null)
  const editPopoverRef = useRef<HTMLDivElement>(null)

  // New-chat creation form state: toggled by the "New Chat" button.
  // The inline form includes name, folder, repo toggle, provider, model, and effort.
  const [showNewChatForm, setShowNewChatForm] = useState(false)
  const [newChatName, setNewChatName] = useState('')
  const [newChatCategory, setNewChatCategory] = useState('')
  const [attachRepo, setAttachRepo] = useState(false)
  const [newChatProvider, setNewChatProvider] = useState<WorkspaceProvider>(activeProvider)
  const namingInputRef = useRef<HTMLInputElement>(null)

  // Sort mode: 'recent' (most recently updated first) or 'sequential' (creation order)
  type SortMode = 'recent' | 'sequential'
  const [sortMode, setSortMode] = useState<SortMode>(() => {
    const saved = localStorage.getItem('workspace-sort-mode')
    return (saved === 'recent' || saved === 'sequential') ? saved : 'recent'
  })
  const handleSortChange = useCallback((mode: SortMode) => {
    setSortMode(mode)
    localStorage.setItem('workspace-sort-mode', mode)
  }, [])

  const { data: conversations, isLoading } = useWorkspaceConversations()

  const createConversationMut = useCreateWorkspaceConversation()
  const updateConversationMut = useUpdateWorkspaceConversation()
  const deleteMutation = useDeleteWorkspaceConversation()
  const { data: categories = [] } = useWorkspaceCategories()
  const createCategoryMut = useCreateCategory()
  const updateCategoryMut = useUpdateCategory()
  const deleteCategoryMut = useDeleteCategory()
  const togglePinMut = useTogglePin()
  const cycleModelBadgeMut = useCycleModelBadge()
  const bulkDeleteMutation = useBulkDeleteWorkspaceConversations()

  // Reset newChatProvider when the form opens, or when the global provider changes
  useEffect(() => {
    setNewChatProvider(activeProvider)
  }, [activeProvider, showNewChatForm])

  // Build model presets for the new-chat form based on its local provider selection
  const isNewChatClaude = newChatProvider === 'claude'
  const newChatModelPresets: ModelPreset[] = useMemo(() => {
    if (!providers || !providers[newChatProvider]) return CLAUDE_MODEL_PRESETS
    return buildPresetsForProvider(newChatProvider, providers[newChatProvider])
  }, [providers, newChatProvider])

  // Focus the naming input when the form appears
  useEffect(() => {
    if (showNewChatForm) {
      // Small delay to allow DOM render
      const timer = setTimeout(() => namingInputRef.current?.focus(), 50)
      return () => clearTimeout(timer)
    }
  }, [showNewChatForm])

  // Close the edit popover when clicking outside of it
  useEffect(() => {
    if (editingConvId === null) return
    const handleClickOutside = (e: MouseEvent) => {
      if (editPopoverRef.current && !editPopoverRef.current.contains(e.target as Node)) {
        setEditingConvId(null)
      }
    }
    // Use a short delay so the opening click doesn't immediately close the popover
    const timer = setTimeout(() => {
      document.addEventListener('mousedown', handleClickOutside)
    }, 0)
    return () => {
      clearTimeout(timer)
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [editingConvId])

  /** Create the named conversation and select it. */
  const handleCreateNamedChat = useCallback(() => {
    if (!showNewChatForm) return
    // Auto-append timestamp if user didn't provide a title (format: M.DD.YY/HH:MMp)
    const rawTitle = newChatName.trim()
    const now = new Date()
    const mo = now.getMonth() + 1
    const dd = String(now.getDate()).padStart(2, '0')
    const yy = String(now.getFullYear()).slice(-2)
    const hr = now.getHours()
    const mn = String(now.getMinutes()).padStart(2, '0')
    const ampm = hr >= 12 ? 'p' : 'a'
    const hr12 = hr % 12 || 12
    const stamp = `${mo}.${dd}.${yy}/${hr12}:${mn}${ampm}`
    const title = rawTitle ? `${rawTitle} · ${stamp}` : `Chat · ${stamp}`
    const safeIdx = Math.min(modelPresetIndex, newChatModelPresets.length - 1)
    const preset = newChatModelPresets[safeIdx]
    if (!preset) return
    // Only pass effort for Claude 1M context models; others don't support it
    const effort = (isNewChatClaude && preset.context === '1m') ? effortLevel : 'high'
    createConversationMut.mutate({
      title,
      category: newChatCategory || undefined,
      model: preset.model,
      context_mode: preset.context,
      effort,
      provider: newChatProvider,
    }, {
      onSuccess: (newConv) => {
        onSelectConversation(newConv.id, newConv.provider)
        setShowNewChatForm(false)
        setNewChatName('')
        setNewChatCategory('')
        setAttachRepo(false)
      },
      onError: (err) => {
        console.error('Failed to create conversation:', err)
        setShowNewChatForm(false)
        setNewChatName('')
        setNewChatCategory('')
        setAttachRepo(false)
      },
    })
  }, [showNewChatForm, newChatName, newChatCategory, createConversationMut, onSelectConversation, modelPresetIndex, effortLevel, newChatModelPresets, isNewChatClaude, newChatProvider])

  /** Cancel the naming form. */
  const handleCancelNaming = useCallback(() => {
    setShowNewChatForm(false)
    setNewChatName('')
    setNewChatCategory('')
    setAttachRepo(false)
    setNewChatProvider(activeProvider)
  }, [activeProvider])

  /** Filter conversations by search term (case-insensitive substring) and sort. */
  const filtered = useMemo(() => {
    if (!conversations) return []
    let result = conversations
    if (search.trim()) {
      const term = search.trim().toLowerCase()
      result = result.filter((c) =>
        (c.title ?? 'Untitled').toLowerCase().includes(term),
      )
    }
    // Sort: 'recent' = most recently updated first, 'sequential' = oldest first (creation order)
    const sorted = [...result].sort((a, b) => {
      const dateA = new Date(a.updated_at ?? a.created_at ?? 0).getTime()
      const dateB = new Date(b.updated_at ?? b.created_at ?? 0).getTime()
      return sortMode === 'recent' ? dateB - dateA : dateA - dateB
    })
    return sorted
  }, [conversations, search, sortMode])

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
      className={`flex flex-col border-r border-border bg-card transition-all duration-200 h-full ${
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

      {/* New Chat button — opens the creation form */}
      <div className="px-3 py-2">
        <Button
          className="w-full"
          onClick={() => setShowNewChatForm(prev => !prev)}
        >
          <Plus size={16} />
          New Chat
          <ChevronDown size={12} className={`ml-1 opacity-60 transition-transform ${showNewChatForm ? 'rotate-180' : ''}`} />
        </Button>
      </div>

      {/* New-chat creation form — slides in when the button is toggled */}
      {showNewChatForm && (
        <div className="px-3 py-2 border-b border-border bg-muted/50 animate-in slide-in-from-top-2 duration-150">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              New Conversation
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

          {/* Name (optional) */}
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
            placeholder="Name (optional)"
            className="w-full text-xs bg-input border border-border rounded px-2 py-1.5 outline-none ring-ring focus:ring-1 text-foreground placeholder:text-muted-foreground mb-1.5"
            aria-label="Chat name"
          />

          {/* Folder / Category selector */}
          <div className="mb-1.5">
            <span className="text-[10px] text-muted-foreground mb-0.5 block">Folder</span>
            <select
              value={newChatCategory}
              onChange={(e) => setNewChatCategory(e.target.value)}
              className="w-full text-xs bg-input border border-border rounded px-2 py-1.5 outline-none ring-ring focus:ring-1 text-foreground"
            >
              <option value="">No folder</option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.name}>{cat.name}</option>
              ))}
            </select>
          </div>

          {/* Attach Repo toggle */}
          <div className="mb-1.5">
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-muted-foreground">Attach Repository</span>
              <button
                type="button"
                onClick={() => setAttachRepo(!attachRepo)}
                className={`relative w-7 h-4 rounded-full transition-colors ${attachRepo ? 'bg-primary' : 'bg-muted-foreground/30'}`}
                role="switch"
                aria-checked={attachRepo}
              >
                <span className={`absolute top-0.5 left-0.5 w-3 h-3 rounded-full bg-white transition-transform ${attachRepo ? 'translate-x-3' : ''}`} />
              </button>
            </div>
            {attachRepo && (
              <div className="mt-1">
                <RepoSelector
                  onSelect={(path) => onWorkingDirectoryChange?.(path)}
                  selectedPath={selectedWorkingDirectory ?? null}
                />
              </div>
            )}
          </div>

          {/* Provider pill bar — pick provider before model */}
          <div className="mb-1.5">
            <span className="text-[10px] text-muted-foreground mb-0.5 block">Provider</span>
            <div className="flex rounded-full border border-border overflow-hidden shadow-sm" role="radiogroup" aria-label="Provider selection">
              {(['claude', 'codex', 'gemini'] as const).map((p, idx) => {
                const isActive = newChatProvider === p
                const colors: Record<string, string> = {
                  claude: 'bg-blue-600 text-white shadow-inner',
                  codex: 'bg-emerald-600 text-white shadow-inner',
                  gemini: 'bg-violet-600 text-white shadow-inner',
                }
                return (
                  <button
                    key={p}
                    type="button"
                    role="radio"
                    aria-checked={isActive}
                    onClick={() => {
                      setNewChatProvider(p)
                      // Reset model selection when provider changes
                      onModelPresetChange?.(0)
                    }}
                    className={`flex-1 px-1.5 py-1 text-[10px] font-semibold whitespace-nowrap transition-all duration-150 ${
                      isActive
                        ? colors[p]
                        : 'bg-card text-muted-foreground hover:bg-muted hover:text-foreground'
                    } ${idx === 0 ? 'rounded-l-full' : ''} ${idx === 2 ? 'rounded-r-full' : 'border-r border-border'}`}
                  >
                    {p.charAt(0).toUpperCase() + p.slice(1)}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Model preset pills — pick model + context before starting */}
          <div className="mb-1.5">
            <span className="text-[10px] text-muted-foreground mb-0.5 block">Model</span>
            <div className="flex flex-wrap gap-1" role="radiogroup" aria-label="Model selection">
              {newChatModelPresets.map((preset, idx) => {
                const isActive = modelPresetIndex === idx
                // Provider-specific active colors
                const activeColor = newChatProvider === 'codex'
                  ? 'bg-emerald-600 text-white shadow-inner'
                  : newChatProvider === 'gemini'
                    ? 'bg-violet-600 text-white shadow-inner'
                    : preset.model === 'sonnet'
                      ? 'bg-violet-500 text-white shadow-inner'
                      : preset.model === 'haiku'
                        ? 'bg-emerald-600 text-white shadow-inner'
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
                    className={`px-2 py-0.5 text-[9px] font-semibold whitespace-nowrap rounded-full border border-border transition-all duration-150 ${
                      isActive
                        ? activeColor
                        : 'bg-card text-muted-foreground hover:bg-muted hover:text-foreground'
                    }`}
                  >
                    {preset.label}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Effort level selector — only shown for Claude provider, active for Opus 1M */}
          {isNewChatClaude && (() => {
            const selectedPreset = newChatModelPresets[modelPresetIndex]
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

          {/* Start Chat button */}
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

      {/* Search + sort toggle */}
      <div className="px-3 pb-2 space-y-1.5">
        <ConversationSearch
          onSelectConversation={(id) => onSelectConversation(id)}
          onFilterChange={(filter) => setSearch(filter)}
        />
        <div className="flex items-center gap-1">
          <span className="text-[10px] text-muted-foreground mr-1">Sort:</span>
          {(['recent', 'sequential'] as const).map((mode) => (
            <button
              key={mode}
              onClick={() => handleSortChange(mode)}
              className={`px-2 py-0.5 text-[10px] rounded-full transition-colors ${
                sortMode === mode
                  ? 'bg-primary text-primary-foreground font-semibold'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted'
              }`}
            >
              {mode === 'recent' ? 'Recent' : 'Sequential'}
            </button>
          ))}
        </div>
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
                  const isRunningBg = false
                  const isWaitingInput = false
                  const isCompletedRecent = false
                  const isFailedBg = false
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

                        // Non-Claude providers: static badge showing abbreviated model label
                        if (convProvider !== 'claude') {
                          const badgeColor = convProvider === 'codex'
                            ? 'bg-emerald-600 text-white border-emerald-400'
                            : 'bg-violet-600 text-white border-violet-400'
                          // Abbreviate long model IDs for the tiny badge
                          const SHORT_MODEL: Record<string, string> = {
                            'gpt-5.4': '5.4', 'gpt-5.4-pro': '5.4P', 'gpt-5.3': '5.3',
                            'gpt-5-codex': '5C', 'o3': 'o3', 'o4-mini': 'o4m',
                            'gemini-3.1-pro': '3.1P', 'gemini-3.1-flash': '3.1F',
                            'gemini-3.1-flash-lite': '3.1L',
                            'pro': 'Pro', 'flash': 'Flsh', 'flash-lite': 'Lite',
                          }
                          const badgeLabel = SHORT_MODEL[model] ?? model
                          return (
                            <span
                              className={`absolute -top-1 -right-1 z-10 text-[9px] font-mono font-extrabold px-1.5 py-0.5 rounded-md border shadow-sm ${badgeColor}`}
                              title={`${convProvider}: ${model}`}
                            >
                              {badgeLabel}
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
                      <div
                        role="button"
                        tabIndex={0}
                        onClick={() => selectMode ? handleToggleSelect(conv.id) : onSelectConversation(conv.id, conv.provider)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault()
                            if (selectMode) {
                              handleToggleSelect(conv.id)
                            } else {
                              onSelectConversation(conv.id, conv.provider)
                            }
                          }
                        }}
                        className={`w-full flex items-center gap-2 px-2 py-2 rounded-lg border text-left transition-colors overflow-hidden cursor-pointer ${
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

                        {!selectMode && (isHovered || editingConvId === conv.id) && (
                          <div className="flex items-center gap-0.5 flex-shrink-0">
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation()
                                setEditingConvId(editingConvId === conv.id ? null : conv.id)
                              }}
                              className={`p-1 rounded text-muted-foreground ${editingConvId === conv.id ? 'bg-accent text-foreground' : 'hover:bg-accent'}`}
                              title="Assign folder or repo"
                            >
                              <FolderPlus size={12} />
                            </button>
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
                      </div>

                      {/* Inline edit popover — folder + repo assignment */}
                      {editingConvId === conv.id && (
                        <div
                          ref={editPopoverRef}
                          className="mt-1 p-2 rounded-lg border border-border bg-card shadow-md animate-in slide-in-from-top-1 duration-100"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {/* Folder / Category selector */}
                          <div className="mb-1.5">
                            <span className="text-[10px] text-muted-foreground mb-0.5 block">Move to Folder</span>
                            <select
                              value={conv.category || ''}
                              onChange={(e) => {
                                updateConversationMut.mutate({
                                  conversationId: conv.id,
                                  category: e.target.value || 'Uncategorized',
                                })
                              }}
                              className="w-full text-xs bg-input border border-border rounded px-2 py-1.5 outline-none ring-ring focus:ring-1 text-foreground"
                            >
                              <option value="">No folder</option>
                              {categories.map((cat) => (
                                <option key={cat.id} value={cat.name}>{cat.name}</option>
                              ))}
                            </select>
                          </div>

                          {/* Repo selector */}
                          <div className="mb-1.5">
                            <span className="text-[10px] text-muted-foreground mb-0.5 block">Attach Repository</span>
                            <RepoSelector
                              onSelect={(path) => {
                                updateConversationMut.mutate({
                                  conversationId: conv.id,
                                  working_directory: path,
                                })
                              }}
                              selectedPath={conv.working_directory ?? null}
                            />
                          </div>

                          {/* Done button */}
                          <button
                            type="button"
                            onClick={() => setEditingConvId(null)}
                            className="w-full text-xs font-medium text-center py-1 rounded bg-muted hover:bg-accent text-foreground transition-colors"
                          >
                            Done
                          </button>
                        </div>
                      )}
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
