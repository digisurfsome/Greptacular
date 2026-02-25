/**
 * DashboardPage - Multi-session dashboard with flexible pane layout.
 *
 * Provides a standalone page at /#/dashboard where the user can run
 * 1, 2, or 3 independent AI sessions side-by-side. Each pane can be
 * any provider (Claude, Codex, Gemini) and any conversation from the
 * sidebar. Sessions in the sidebar keep working when not actively viewed.
 *
 * Layout modes:
 *   - Single: one full-width pane
 *   - Dual: two side-by-side panes
 *   - Triple: three side-by-side panes
 *
 * Each pane has its own provider selector, conversation identity, and
 * WebSocket connection managed by the WorkspaceChat component.
 */

import { useState, useCallback, useEffect } from 'react'
import { WorkspaceSidebar } from '../components/workspace/WorkspaceSidebar'
import { WorkspaceChat } from '../components/workspace/WorkspaceChat'
import { RepoSelector } from '../components/workspace/RepoSelector'
import {
  ArrowLeft,
  ChevronRight,
  Columns2,
  Columns3,
  Square,
  ChevronsLeft,
  ChevronsRight,
  X,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import type { WorkspaceProvider, EffortLevel } from '@/lib/types'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** State for a single dashboard pane. */
interface PaneState {
  id: string
  conversationId: number | null
  provider: WorkspaceProvider
  label: string
  collapsed: boolean
}

type LayoutMode = 'single' | 'dual' | 'triple'

/** Provider metadata for the selector UI. */
const PROVIDERS: { id: WorkspaceProvider; name: string; color: string; dot: string }[] = [
  { id: 'claude', name: 'Claude', color: 'bg-blue-600 text-white border-blue-400', dot: 'bg-blue-500' },
  { id: 'codex', name: 'Codex', color: 'bg-emerald-600 text-white border-emerald-400', dot: 'bg-emerald-500' },
  { id: 'gemini', name: 'Gemini', color: 'bg-violet-600 text-white border-violet-400', dot: 'bg-violet-500' },
]

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function createPane(provider: WorkspaceProvider = 'claude', label?: string): PaneState {
  return {
    id: `pane-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
    conversationId: null,
    provider,
    label: label ?? provider.charAt(0).toUpperCase() + provider.slice(1),
    collapsed: false,
  }
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/** Collapsed pane bar — thin vertical strip with rotated label. */
function CollapsedPaneBar({
  label,
  provider,
  onClick,
}: {
  label: string
  provider: WorkspaceProvider
  onClick: () => void
}): React.JSX.Element {
  const bg = provider === 'codex'
    ? 'bg-emerald-500/5'
    : provider === 'gemini'
      ? 'bg-violet-500/5'
      : 'bg-blue-500/5'

  return (
    <button
      onClick={onClick}
      className={`w-10 shrink-0 flex items-center justify-center border-r border-border cursor-pointer hover:opacity-80 transition-opacity ${bg}`}
      title={`Expand ${label}`}
    >
      <span className="text-[10px] font-bold tracking-widest [writing-mode:vertical-lr] rotate-180 select-none">
        {label.toUpperCase()}
      </span>
    </button>
  )
}

/** Provider selector pill strip for a pane header. */
function ProviderSelector({
  current,
  onChange,
}: {
  current: WorkspaceProvider
  onChange: (p: WorkspaceProvider) => void
}): React.JSX.Element {
  return (
    <div className="flex rounded-full border border-border overflow-hidden shadow-sm" role="radiogroup" aria-label="Provider selection">
      {PROVIDERS.map((p, idx) => {
        const isActive = current === p.id
        return (
          <button
            key={p.id}
            type="button"
            role="radio"
            aria-checked={isActive}
            onClick={() => onChange(p.id)}
            className={`px-2.5 py-1 text-[10px] font-semibold whitespace-nowrap transition-all duration-150 ${
              isActive
                ? p.color + ' shadow-inner'
                : 'bg-card text-muted-foreground hover:bg-muted hover:text-foreground'
            } ${idx === 0 ? 'rounded-l-full' : ''} ${idx === PROVIDERS.length - 1 ? 'rounded-r-full' : 'border-r border-border'}`}
          >
            {p.name}
          </button>
        )
      })}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export function DashboardPage(): React.JSX.Element {
  // --- Layout state ---
  const [layoutMode, setLayoutMode] = useState<LayoutMode>(() => {
    try {
      return (localStorage.getItem('dashboard-layout') as LayoutMode) || 'dual'
    } catch { return 'dual' }
  })

  // Panes array — length matches layout mode
  const [panes, setPanes] = useState<PaneState[]>(() => {
    try {
      const saved = localStorage.getItem('dashboard-panes')
      if (saved) {
        const parsed = JSON.parse(saved) as PaneState[]
        if (Array.isArray(parsed) && parsed.length > 0) return parsed
      }
    } catch { /* ignore */ }
    return [
      createPane('claude', 'Claude'),
      createPane('codex', 'Codex'),
    ]
  })

  // Sidebar state
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [workingDirectory, setWorkingDirectory] = useState<string | null>(() => {
    try { return localStorage.getItem('dashboard-working-dir') || null } catch { return null }
  })

  // Track which conversations are streaming
  const [streamingIds, setStreamingIds] = useState<Set<number>>(new Set())

  // Model/effort for new chats from sidebar
  const [pendingModel, setPendingModel] = useState<'opus' | 'sonnet'>('opus')
  const [pendingContextMode, setPendingContextMode] = useState<'1m' | '200k'>('200k')
  const [pendingEffort, setPendingEffort] = useState<EffortLevel>('high')
  const [newChatKey, setNewChatKey] = useState(0)
  const [modelPresetIndex, setModelPresetIndex] = useState(0)

  // Persist layout and panes
  useEffect(() => {
    try {
      localStorage.setItem('dashboard-layout', layoutMode)
      localStorage.setItem('dashboard-panes', JSON.stringify(panes))
      if (workingDirectory) localStorage.setItem('dashboard-working-dir', workingDirectory)
    } catch { /* ignore */ }
  }, [layoutMode, panes, workingDirectory])

  // Sync pane count with layout mode
  useEffect(() => {
    const targetCount = layoutMode === 'single' ? 1 : layoutMode === 'dual' ? 2 : 3
    setPanes(prev => {
      if (prev.length === targetCount) return prev
      if (prev.length < targetCount) {
        // Add panes with different providers
        const usedProviders = new Set(prev.map(p => p.provider))
        const available: WorkspaceProvider[] = (['claude', 'codex', 'gemini'] as const).filter(p => !usedProviders.has(p))
        const newPanes = [...prev]
        while (newPanes.length < targetCount) {
          const provider = available.shift() || 'claude'
          newPanes.push(createPane(provider))
        }
        return newPanes
      }
      // Shrink: keep first N
      return prev.slice(0, targetCount)
    })
  }, [layoutMode])

  // --- Pane operations ---
  const updatePane = useCallback((paneId: string, updates: Partial<PaneState>) => {
    setPanes(prev => prev.map(p => p.id === paneId ? { ...p, ...updates } : p))
  }, [])

  const handlePaneProviderChange = useCallback((paneId: string, provider: WorkspaceProvider) => {
    updatePane(paneId, {
      provider,
      label: provider.charAt(0).toUpperCase() + provider.slice(1),
      conversationId: null, // Reset conversation when switching provider
    })
  }, [updatePane])

  const handlePaneConversationCreated = useCallback((paneId: string, convId: number) => {
    updatePane(paneId, { conversationId: convId })
  }, [updatePane])

  const handlePaneStreamingChange = useCallback((paneId: string, isStreaming: boolean) => {
    setPanes(prev => {
      const pane = prev.find(p => p.id === paneId)
      if (!pane?.conversationId) return prev
      setStreamingIds(ids => {
        const next = new Set(ids)
        if (isStreaming) next.add(pane.conversationId!)
        else next.delete(pane.conversationId!)
        return next
      })
      return prev
    })
  }, [])

  // Sidebar: assign conversation to first available pane (or active pane)
  const handleSelectConversation = useCallback((convId: number) => {
    setPanes(prev => {
      // Find first pane without a conversation, or update first pane
      const emptyIdx = prev.findIndex(p => p.conversationId === null)
      const targetIdx = emptyIdx >= 0 ? emptyIdx : 0
      return prev.map((p, i) => i === targetIdx ? { ...p, conversationId: convId } : p)
    })
  }, [])

  const handleDeleteConversation = useCallback((deletedId: number) => {
    setPanes(prev => prev.map(p =>
      p.conversationId === deletedId ? { ...p, conversationId: null } : p
    ))
    setStreamingIds(ids => {
      const next = new Set(ids)
      next.delete(deletedId)
      return next
    })
  }, [])

  const handleNewChat = useCallback((model: 'opus' | 'sonnet', contextMode: '1m' | '200k', effort: EffortLevel = 'high') => {
    setPendingModel(model)
    setPendingContextMode(contextMode)
    setPendingEffort(effort)
    setNewChatKey(k => k + 1)
    // Clear first pane's conversation to trigger new chat
    setPanes(prev => {
      const updated = [...prev]
      if (updated.length > 0) {
        updated[0] = { ...updated[0], conversationId: null }
      }
      return updated
    })
  }, [])

  const handleRepoSelect = useCallback((path: string) => {
    setWorkingDirectory(path || null)
  }, [])

  // Get the first streaming conversation ID for sidebar indicator
  const firstStreamingId = streamingIds.size > 0 ? Array.from(streamingIds)[0] : null

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Breadcrumb navigation bar */}
      <div className="flex items-center h-10 px-3 border-b border-border bg-card shrink-0">
        <nav className="flex items-center gap-1 text-sm" aria-label="Breadcrumb">
          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5 text-muted-foreground hover:text-foreground h-7 px-2"
            onClick={() => { window.location.hash = '' }}
          >
            <ArrowLeft size={14} />
            <span className="text-xs">AutoForge</span>
          </Button>
          <ChevronRight size={12} className="text-muted-foreground" />
          <span className="text-xs font-semibold text-foreground">
            Dashboard
          </span>
          <ChevronRight size={12} className="text-muted-foreground" />
          <RepoSelector
            onSelect={handleRepoSelect}
            selectedPath={workingDirectory}
          />
        </nav>

        <div className="ml-auto flex items-center gap-1">
          {/* Layout mode buttons */}
          <Button
            variant={layoutMode === 'single' ? 'default' : 'ghost'}
            size="sm"
            className={`h-7 px-2 gap-1 ${layoutMode === 'single' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'}`}
            onClick={() => setLayoutMode('single')}
            title="Single pane"
          >
            <Square size={14} />
            <span className="text-[10px]">1</span>
          </Button>
          <Button
            variant={layoutMode === 'dual' ? 'default' : 'ghost'}
            size="sm"
            className={`h-7 px-2 gap-1 ${layoutMode === 'dual' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'}`}
            onClick={() => setLayoutMode('dual')}
            title="Two panes side by side"
          >
            <Columns2 size={14} />
            <span className="text-[10px]">2</span>
          </Button>
          <Button
            variant={layoutMode === 'triple' ? 'default' : 'ghost'}
            size="sm"
            className={`h-7 px-2 gap-1 ${layoutMode === 'triple' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'}`}
            onClick={() => setLayoutMode('triple')}
            title="Three panes side by side"
          >
            <Columns3 size={14} />
            <span className="text-[10px]">3</span>
          </Button>

          <div className="w-px h-5 bg-border mx-1" />

          {/* Back to Workspace link */}
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 gap-1.5 text-muted-foreground hover:text-foreground"
            onClick={() => { window.location.hash = '#/workspace' }}
            title="Open Workspace"
          >
            <span className="text-[10px]">Workspace</span>
          </Button>
        </div>
      </div>

      {/* Main content: sidebar + panes */}
      <div className="flex flex-1 overflow-hidden">
        <WorkspaceSidebar
          activeConversationId={panes[0]?.conversationId ?? null}
          streamingConversationId={firstStreamingId}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(v => !v)}
          onNewChat={handleNewChat}
          onSelectConversation={handleSelectConversation}
          onDeleteConversation={handleDeleteConversation}
          selectedWorkingDirectory={workingDirectory}
          onWorkingDirectoryChange={handleRepoSelect}
          modelPresetIndex={modelPresetIndex}
          onModelPresetChange={setModelPresetIndex}
          effortLevel={pendingEffort}
          onEffortChange={setPendingEffort}
        />

        {/* Panes */}
        <div className="flex-1 flex overflow-hidden">
          {panes.map((pane, idx) => {
            if (pane.collapsed) {
              return (
                <CollapsedPaneBar
                  key={pane.id}
                  label={pane.label}
                  provider={pane.provider}
                  onClick={() => updatePane(pane.id, { collapsed: false })}
                />
              )
            }

            const isLast = idx === panes.length - 1

            return (
              <div
                key={pane.id}
                className={`flex-1 min-w-0 flex flex-col overflow-hidden relative ${!isLast ? 'border-r border-border' : ''}`}
              >
                {/* Pane header with provider selector + collapse */}
                <div className="flex items-center gap-2 px-3 py-1.5 border-b border-border bg-card shrink-0">
                  <ProviderSelector
                    current={pane.provider}
                    onChange={(p) => handlePaneProviderChange(pane.id, p)}
                  />
                  <span className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider flex-1 truncate">
                    {pane.label}
                    {pane.conversationId && (
                      <span className="ml-1 text-muted-foreground/50">#{pane.conversationId}</span>
                    )}
                  </span>

                  {/* Clear pane button */}
                  {pane.conversationId && (
                    <button
                      onClick={() => updatePane(pane.id, { conversationId: null })}
                      className="p-0.5 text-muted-foreground/40 hover:text-muted-foreground transition-colors"
                      title="Clear this pane"
                    >
                      <X size={12} />
                    </button>
                  )}

                  {/* Collapse button */}
                  {panes.length > 1 && (
                    <button
                      onClick={() => updatePane(pane.id, { collapsed: true })}
                      className="p-0.5 text-muted-foreground/40 hover:text-muted-foreground transition-colors"
                      title={`Collapse ${pane.label}`}
                    >
                      {idx === panes.length - 1 ? <ChevronsRight size={14} /> : <ChevronsLeft size={14} />}
                    </button>
                  )}
                </div>

                {/* Chat area */}
                <WorkspaceChat
                  conversationId={pane.conversationId}
                  onConversationCreated={(id) => handlePaneConversationCreated(pane.id, id)}
                  onNewConversation={() => updatePane(pane.id, { conversationId: null })}
                  workingDirectory={workingDirectory}
                  panelLabel={`${pane.provider.toUpperCase()} SESSION`}
                  pendingModel={idx === 0 ? pendingModel : undefined}
                  pendingContextMode={idx === 0 ? pendingContextMode : undefined}
                  pendingEffort={idx === 0 ? pendingEffort : undefined}
                  newChatKey={idx === 0 ? newChatKey : undefined}
                  onStreamingChange={(streaming) => handlePaneStreamingChange(pane.id, streaming)}
                />
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
