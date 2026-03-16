/**
 * WorkspacePage - Full-page workspace layout with sidebar, chat, and library panel.
 *
 * Provides a standalone coding workspace at /#/workspace with multi-conversation
 * management, full Claude agent capabilities, file library, GitHub repos,
 * real-time context budget tracking, keyboard shortcuts, and breadcrumb navigation.
 *
 * Split view provides three collapsible (accordion) panels:
 *   1. Research (200K subscription) — explore & figure things out
 *   2. PRD Builder (Opus 4.6, 1M API) — create the PRD with codebase context
 *   3. Coder (Sonnet 4.6, 200K / Opus 4.6, 1M API) — execute the PRD
 *
 * The passoff editor is a tab alongside Chat in the PRD panel. Auto-forward
 * sends the PRD panel's completed response directly to the Coder panel.
 */

import { useState, useCallback, useRef, useEffect } from 'react'
import { WorkspaceSidebar } from '../components/workspace/WorkspaceSidebar'
import { WorkspaceChat } from '../components/workspace/WorkspaceChat'
import { WorkspaceLibrary } from '../components/workspace/WorkspaceLibrary'
import { WorkspaceKeyboardHelp } from '../components/workspace/WorkspaceKeyboardHelp'
import { WorkspaceUserGuide } from '../components/workspace/WorkspaceUserGuide'
import { PassoffEditor, type PassoffSection } from '../components/workspace/PassoffEditor'
import { SwarmPanel } from '../components/workspace/SwarmPanel'
import { CIStatusWidget } from '../components/workspace/CIStatusWidget'
import { GitActivityWidget } from '../components/GitActivityWidget'
import { useWorkspaceKeyboardShortcuts } from '../hooks/useWorkspaceKeyboardShortcuts'
import { exportConversationMarkdown, getSettings } from '../lib/api'
import type { WalkieTalkieLogEntry, WorkspaceProvider } from '../lib/types'
import { CountdownTimerBar } from '../components/workspace/CountdownTimerBar'
import { FactoryPanel } from '../components/factory/FactoryPanel'
import {
  ArrowLeft,
  ChevronRight,
  Keyboard,
  BookOpen,
  Bot,
  Columns2,
  ChevronsLeft,
  ChevronsRight,
  Zap,
  Network,
  LayoutDashboard,
  Menu,
  Factory,
  Swords,
} from 'lucide-react'
import { Button } from '@/components/ui/button'

/** Collapsed panel bar — a thin vertical strip with a rotated label. */
function CollapsedPanelBar({
  label,
  color,
  onClick,
}: {
  label: string
  color: string
  onClick: () => void
}): React.JSX.Element {
  return (
    <button
      onClick={onClick}
      className={`w-10 shrink-0 flex items-center justify-center border-r border-border cursor-pointer hover:opacity-80 transition-opacity ${color}`}
      title={`Expand ${label}`}
    >
      <span className="text-[10px] font-bold tracking-widest [writing-mode:vertical-lr] rotate-180 select-none">
        {label}
      </span>
    </button>
  )
}

/** Parse conversation ID from the URL hash (e.g. #/workspace/chat/42 → 42). */
function parseConversationIdFromHash(): number | null {
  const match = window.location.hash.match(/^#\/workspace\/chat\/(\d+)/)
  return match ? parseInt(match[1], 10) : null
}

/** Full-page workspace layout with keyboard shortcuts, breadcrumbs, and all Phase 4 features. */
export function WorkspacePage(): React.JSX.Element {
  // Conversation ID is driven by the URL hash — each conversation is its own "page".
  // Sidebar navigation changes the hash, which triggers a re-render with the new ID.
  const [activeConversationId, setActiveConversationId] = useState<number | null>(parseConversationIdFromHash)
  const [workingDirectory, setWorkingDirectory] = useState<string | null>(() => {
    try {
      return localStorage.getItem('workspace-working-dir') || null
    } catch {
      return null
    }
  })
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false)
  const [libraryCollapsed, setLibraryCollapsed] = useState(false)
  const [showKeyboardHelp, setShowKeyboardHelp] = useState(false)
  const [showUserGuide, setShowUserGuide] = useState(false)
  const [splitView, setSplitView] = useState(false)
  const [showSwarm, setShowSwarm] = useState(false)
  const [showFactory, setShowFactory] = useState(false)

  // Three-panel state (split view)
  const [prdConversationId, setPrdConversationId] = useState<number | null>(null)
  const [coderConversationId, setCoderConversationId] = useState<number | null>(null)
  // Per-panel model selection (persisted to localStorage)
  const [researchModel, setResearchModel] = useState<'opus' | 'sonnet'>(() => {
    try { return (localStorage.getItem('workspace-panel-research-model') as 'opus' | 'sonnet') || 'opus' } catch { return 'opus' }
  })
  const [prdModel, setPrdModel] = useState<'opus' | 'sonnet'>(() => {
    try { return (localStorage.getItem('workspace-panel-prd-model') as 'opus' | 'sonnet') || 'opus' } catch { return 'opus' }
  })
  const [coderModel, setCoderModel] = useState<'opus' | 'sonnet'>(() => {
    try { return (localStorage.getItem('workspace-panel-coder-model') as 'opus' | 'sonnet') || 'sonnet' } catch { return 'sonnet' }
  })
  const [researchCollapsed, setResearchCollapsed] = useState(() => {
    try { return localStorage.getItem('workspace-panel-research') === 'collapsed' } catch { return false }
  })
  const [prdCollapsed, setPrdCollapsed] = useState(() => {
    try { return localStorage.getItem('workspace-panel-prd') === 'collapsed' } catch { return false }
  })
  const [coderCollapsed, setCoderCollapsed] = useState(() => {
    try { return localStorage.getItem('workspace-panel-coder') === 'collapsed' } catch { return false }
  })

  // Active provider (claude, codex, gemini) — persisted to localStorage
  const [activeProvider, setActiveProvider] = useState<WorkspaceProvider>(() => {
    try { return (localStorage.getItem('workspace-provider') as WorkspaceProvider) || 'claude' } catch { return 'claude' }
  })

  // Pending provider switch — shown in confirmation dialog when switching with an active conversation
  const [pendingProviderSwitch, setPendingProviderSwitch] = useState<WorkspaceProvider | null>(null)

  // Persist panel collapse state to localStorage
  useEffect(() => {
    try {
      localStorage.setItem('workspace-panel-research', researchCollapsed ? 'collapsed' : 'expanded')
      localStorage.setItem('workspace-panel-prd', prdCollapsed ? 'collapsed' : 'expanded')
      localStorage.setItem('workspace-panel-coder', coderCollapsed ? 'collapsed' : 'expanded')
      localStorage.setItem('workspace-panel-research-model', researchModel)
      localStorage.setItem('workspace-panel-prd-model', prdModel)
      localStorage.setItem('workspace-panel-coder-model', coderModel)
      localStorage.setItem('workspace-provider', activeProvider)
    } catch { /* ignore quota or security errors */ }
  }, [researchCollapsed, prdCollapsed, coderCollapsed, researchModel, prdModel, coderModel, activeProvider])

  // Persist working directory to localStorage so new conversations remember it
  useEffect(() => {
    if (workingDirectory) {
      try {
        localStorage.setItem('workspace-working-dir', workingDirectory)
      } catch { /* ignore quota or security errors */ }
    }
  }, [workingDirectory])

  // Sync activeConversationId with the URL hash — this is how "page navigation" works.
  // When the sidebar navigates to #/workspace/chat/{id}, this picks up the change.
  useEffect(() => {
    const handler = () => setActiveConversationId(parseConversationIdFromHash())
    window.addEventListener('hashchange', handler)
    return () => window.removeEventListener('hashchange', handler)
  }, [])

  // Passoff editor state — tab alongside Chat in PRD panel
  const [passoffSections, setPassoffSections] = useState<PassoffSection[]>([])
  const [passoffPreamble, setPassoffPreamble] = useState('')
  const [showPassoffOverlay, setShowPassoffOverlay] = useState(false)

  // Inject messages for PRD and Coder panels
  const [prdInjectMessage, setPrdInjectMessage] = useState<string | null>(null)
  const [coderInjectMessage, setCoderInjectMessage] = useState<string | null>(null)

  // Auto-forward: when PRD panel finishes, auto-send to Coder panel
  const [autoForward, setAutoForward] = useState(false)

  // Countdown timer state (shared across panels)
  const [timerActive, setTimerActive] = useState(false)
  const [commTimeout, setCommTimeout] = useState(120)
  const [commAutoReply, setCommAutoReply] = useState(true)

  // Track which conversation is currently streaming (for sidebar activity indicator)
  const [streamingIds, setStreamingIds] = useState<Set<number>>(new Set())

  // Walkie-talkie log (bridged from WorkspaceChat to WorkspaceLibrary)
  const [walkieTalkieLog, setWalkieTalkieLog] = useState<WalkieTalkieLogEntry[]>([])

  // Load comm settings from server on mount
  useEffect(() => {
    getSettings()
      .then((s) => {
        if (s.comm_wait_timeout) setCommTimeout(s.comm_wait_timeout)
        if (s.comm_auto_reply !== undefined) setCommAutoReply(s.comm_auto_reply)
      })
      .catch(() => { /* use defaults */ })
  }, [])

  const chatInputRef = useRef<HTMLTextAreaElement | null>(null)

  // Model preset state — shared between sidebar (new chat form) and WorkspaceChat (pill toggle)
  const [modelPresetIndex, setModelPresetIndex] = useState(() => {
    const saved = Number(localStorage.getItem('workspace-model-preset') ?? '0')
    return saved >= 0 && saved < 10 ? saved : 0  // generous upper bound; sidebar clamps to actual preset count
  })
  const handleModelPresetChange = useCallback((idx: number) => {
    setModelPresetIndex(idx)
    localStorage.setItem('workspace-model-preset', String(idx))
    // Context mode for Claude presets: 0=Opus 1M, 1=Sonnet 1M, 2=Opus 200K
    // Non-Claude presets are all '1m'. Fallback to '1m' for out-of-range indices.
    const claudeContexts: Record<number, string> = { 0: '1m', 1: '1m', 2: '200k' }
    localStorage.setItem('workspace-context-mode', claudeContexts[idx] ?? '1m')
  }, [])

  // Model + context chosen at new-chat creation time (from sidebar dropdown).
  // Stored as pending state, passed to WorkspaceChat for the new session.
  // newChatKey is a counter that increments on every "New Chat" click to ensure
  // state changes even when the same model is selected twice in a row.
  const [pendingModel, setPendingModel] = useState<string>('opus')
  const [pendingContextMode, setPendingContextMode] = useState<'1m' | '200k'>('200k')
  const [pendingEffort, setPendingEffort] = useState<'low' | 'medium' | 'high'>('high')
  const [newChatKey, setNewChatKey] = useState(0)

  const handleNewChat = useCallback((model: string, contextMode: '1m' | '200k', effort: 'low' | 'medium' | 'high' = 'high', provider?: WorkspaceProvider) => {
    if (provider && provider !== activeProvider) {
      setActiveProvider(provider)
    }
    setPendingModel(model)
    setPendingContextMode(contextMode)
    setPendingEffort(effort)
    setNewChatKey(k => k + 1)
    window.location.hash = '#/workspace'
  }, [activeProvider])

  /** Clear active conversation when it's deleted so the chat panel disconnects. */
  const handleDeleteConversation = useCallback((deletedId: number) => {
    if (parseConversationIdFromHash() === deletedId) {
      window.location.hash = '#/workspace'
    }
    // Always clean up streaming state — the deleted conversation could be
    // streaming in any panel (main, PRD, coder) or split-view mode.
    setStreamingIds(prev => {
      if (!prev.has(deletedId)) return prev
      const next = new Set(prev)
      next.delete(deletedId)
      return next
    })
  }, [])

  /** Navigate back to conversation list (no model selection needed). */
  const handleBackToConversations = useCallback(() => {
    window.location.hash = '#/workspace'
  }, [])

  /** Navigate to a conversation page — each conversation is its own route. */
  const handleSelectConversation = useCallback((id: number) => {
    window.location.hash = `#/workspace/chat/${id}`
    setMobileSidebarOpen(false)
  }, [])

  /** After a new conversation is created, navigate to its page. */
  const handleConversationCreated = useCallback((id: number) => {
    window.location.hash = `#/workspace/chat/${id}`
  }, [])

  const handleExportChat = useCallback(() => {
    if (activeConversationId) {
      exportConversationMarkdown(activeConversationId)
    }
  }, [activeConversationId])

  const handleFocusSearch = useCallback(() => {
    const searchInput = document.querySelector(
      '[data-workspace-search]',
    ) as HTMLInputElement | null
    searchInput?.focus()
  }, [])

  const handleFocusChatInput = useCallback(() => {
    chatInputRef.current?.focus()
  }, [])

  const handleRepoSelect = useCallback((localPath: string) => {
    setWorkingDirectory(localPath || null)
  }, [])

  // PRD panel handlers
  const handlePrdConversationCreated = useCallback((id: number) => {
    setPrdConversationId(id)
  }, [])

  const handlePrdNewChat = useCallback(() => {
    setPrdConversationId(null)
  }, [])

  // Coder panel handlers
  const handleCoderConversationCreated = useCallback((id: number) => {
    setCoderConversationId(id)
  }, [])

  const handleCoderNewChat = useCallback(() => {
    setCoderConversationId(null)
  }, [])

  // Passoff: add a section from an assistant message in the Research panel
  const handleCopyToPassoff = useCallback((content: string) => {
    const id = `sec-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`
    setPassoffSections(prev => [...prev, { id, title: '', content }])
    // Auto-show the passoff overlay when content is added
    setShowPassoffOverlay(true)
  }, [])

  // Passoff: send the full document to the PRD panel
  const handleSendToPrd = useCallback((fullDocument: string) => {
    setPrdInjectMessage(fullDocument)
    setShowPassoffOverlay(false)
    // Expand the PRD panel if collapsed
    setPrdCollapsed(false)
  }, [])

  const handlePrdInjectConsumed = useCallback(() => {
    setPrdInjectMessage(null)
  }, [])

  const handleCoderInjectConsumed = useCallback(() => {
    setCoderInjectMessage(null)
  }, [])

  // Auto-forward: when PRD panel finishes responding, send to Coder
  const handlePrdResponseComplete = useCallback((content: string) => {
    if (autoForward) {
      setCoderInjectMessage(content)
      // Expand the Coder panel and optionally collapse PRD
      setCoderCollapsed(false)
    }
  }, [autoForward])

  // Register workspace keyboard shortcuts
  useWorkspaceKeyboardShortcuts({
    onNewConversation: handleBackToConversations,
    onToggleLibrary: () => setLibraryCollapsed((v) => !v),
    onToggleSidebar: () => setSidebarCollapsed((v) => !v),
    onFocusSearch: handleFocusSearch,
    onExportChat: handleExportChat,
    onShowShortcutsHelp: () => setShowKeyboardHelp(true),
    onFocusChatInput: handleFocusChatInput,
    hasActiveConversation: activeConversationId !== null,
    onTogglePanel1: splitView ? () => setResearchCollapsed(v => !v) : undefined,
    onTogglePanel2: splitView ? () => setPrdCollapsed(v => !v) : undefined,
    onTogglePanel3: splitView ? () => setCoderCollapsed(v => !v) : undefined,
  })

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Breadcrumb navigation bar — wraps on narrow screens */}
      <div className="flex flex-wrap items-center min-h-10 px-3 py-1 border-b border-border bg-card shrink-0 gap-y-1">
        <nav className="flex items-center gap-1 text-sm" aria-label="Breadcrumb">
          {/* Sidebar toggle -- visible on mobile always, visible on desktop when sidebar is collapsed */}
          <Button
            variant="ghost"
            size="sm"
            className={`h-7 px-2 text-muted-foreground hover:text-foreground ${sidebarCollapsed ? '' : 'md:hidden'}`}
            onClick={() => {
              // On mobile (below md), toggle the mobile drawer overlay
              // On desktop (md+), toggle the sidebar collapse state
              const isMobile = window.innerWidth < 768
              if (isMobile) {
                setMobileSidebarOpen(v => !v)
              } else {
                setSidebarCollapsed(v => !v)
              }
            }}
            title="Toggle sidebar"
          >
            <Menu size={16} />
          </Button>
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
            Workspace
          </span>
        </nav>

        <div className="ml-auto flex flex-wrap items-center gap-1">
          {/* Git Activity Widget — hidden on small screens to save space */}
          <div className="hidden md:flex items-center">
            <GitActivityWidget
              workingDirectory={workingDirectory}
            />
            <div className="w-px h-5 bg-border mx-1" />
          </div>
          {/* CI Pipeline Status — hidden on small screens */}
          <div className="hidden md:flex items-center">
            <CIStatusWidget workingDirectory={workingDirectory} />
            <div className="w-px h-5 bg-border mx-1" />
          </div>
          <Button
            variant={splitView ? 'default' : 'ghost'}
            size="sm"
            className={`h-7 px-2 gap-1.5 ${splitView
              ? 'bg-primary text-primary-foreground'
              : 'text-muted-foreground hover:text-foreground'
            }`}
            onClick={() => setSplitView(v => !v)}
            title="Three-panel mode: Research + PRD Builder + Coder"
          >
            <Columns2 size={14} />
            <span className="hidden sm:inline text-[10px]">Split</span>
          </Button>
          <Button
            variant={showSwarm ? 'default' : 'ghost'}
            size="sm"
            className={`h-7 px-2 gap-1.5 ${showSwarm
              ? 'bg-violet-600 text-white hover:bg-violet-700'
              : 'text-muted-foreground hover:text-foreground'
            }`}
            onClick={() => setShowSwarm(v => !v)}
            title="Swarm: concurrent autonomous agents with shared workspace"
          >
            <Network size={14} />
            <span className="hidden sm:inline text-[10px]">Swarm</span>
          </Button>
          <Button
            variant={showFactory ? 'default' : 'ghost'}
            size="sm"
            className={`h-7 px-2 gap-1.5 ${showFactory
              ? 'bg-amber-600 text-white hover:bg-amber-700'
              : 'text-muted-foreground hover:text-foreground'
            }`}
            onClick={() => setShowFactory(v => !v)}
            title="Factory Mode: autonomous phased feature pipeline"
          >
            <Factory size={14} />
            <span className="hidden sm:inline text-[10px]">Factory</span>
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 gap-1.5 text-muted-foreground hover:text-foreground"
            onClick={() => { window.location.hash = '#/arena' }}
            title="Arena — compare AI models side-by-side"
          >
            <Swords size={14} />
            <span className="hidden sm:inline text-[10px]">Arena</span>
          </Button>
          {splitView && (
            <Button
              variant={autoForward ? 'default' : 'ghost'}
              size="sm"
              className={`h-7 px-2 gap-1.5 ${autoForward
                ? 'bg-amber-500 text-white hover:bg-amber-600'
                : 'text-muted-foreground hover:text-foreground'
              }`}
              onClick={() => setAutoForward(v => !v)}
              title="Auto-forward: when PRD Builder finishes, auto-send to Coder"
            >
              <Zap size={14} />
              <span className="hidden sm:inline text-[10px]">Auto</span>
            </Button>
          )}
          {/* Split-view panel focus buttons — hidden on mobile, advanced controls */}
          {splitView && (
            <div className="hidden md:flex items-center">
              <div className="w-px h-5 bg-border mx-1" />
              <Button
                variant="ghost"
                size="sm"
                className="h-7 px-2 text-[10px] text-muted-foreground hover:text-foreground"
                onClick={() => { setResearchCollapsed(false); setPrdCollapsed(true); setCoderCollapsed(true) }}
                title="Research Focus: only Research panel expanded"
              >
                R
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-7 px-2 text-[10px] text-muted-foreground hover:text-foreground"
                onClick={() => { setResearchCollapsed(true); setPrdCollapsed(false); setCoderCollapsed(true) }}
                title="Build Focus: only PRD Builder panel expanded"
              >
                P
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-7 px-2 text-[10px] text-muted-foreground hover:text-foreground"
                onClick={() => { setResearchCollapsed(true); setPrdCollapsed(true); setCoderCollapsed(false) }}
                title="Code Focus: only Coder panel expanded"
              >
                C
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-7 px-2 text-[10px] text-muted-foreground hover:text-foreground"
                onClick={() => { setResearchCollapsed(false); setPrdCollapsed(false); setCoderCollapsed(false) }}
                title="All panels expanded"
              >
                All
              </Button>
            </div>
          )}
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 gap-1.5 text-muted-foreground hover:text-foreground"
            onClick={() => { window.location.hash = '#/roles' }}
            title="Agent Role Library — blueprints for terminal agent roles"
          >
            <Bot size={14} />
            <span className="hidden sm:inline text-[10px]">Roles</span>
          </Button>
          {/* Provider selector */}
          <div className="flex rounded-full border border-border overflow-hidden shadow-sm">
            {(['claude', 'codex', 'gemini'] as const).map((p, idx) => {
              const isActive = activeProvider === p
              const colors: Record<string, string> = {
                claude: 'bg-blue-600 text-white border-blue-400',
                codex: 'bg-emerald-600 text-white border-emerald-400',
                gemini: 'bg-violet-600 text-white border-violet-400',
              }
              return (
                <button
                  key={p}
                  type="button"
                  onClick={() => {
                    if (p === activeProvider) return
                    if (activeConversationId !== null) {
                      setPendingProviderSwitch(p)
                    } else {
                      setActiveProvider(p)
                    }
                  }}
                  className={`px-2.5 py-1 text-[10px] font-semibold whitespace-nowrap transition-all duration-150 ${
                    isActive
                      ? colors[p] + ' shadow-inner'
                      : 'bg-card text-muted-foreground hover:bg-muted hover:text-foreground'
                  } ${idx === 0 ? 'rounded-l-full' : ''} ${idx === 2 ? 'rounded-r-full' : 'border-r border-border'}`}
                >
                  {p.charAt(0).toUpperCase() + p.slice(1)}
                </button>
              )
            })}
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 gap-1.5 text-muted-foreground hover:text-foreground"
            onClick={() => { window.location.hash = '#/dashboard' }}
            title="Multi-session Dashboard — run Claude, Codex, and Gemini side by side"
          >
            <LayoutDashboard size={14} />
            <span className="hidden sm:inline text-[10px]">Dashboard</span>
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 gap-1.5 text-muted-foreground hover:text-foreground"
            onClick={() => setShowUserGuide(v => !v)}
            title="User guide & notes"
          >
            <BookOpen size={14} />
            <span className="hidden sm:inline text-[10px]">Guide</span>
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-muted-foreground hover:text-foreground"
            onClick={() => setShowKeyboardHelp(true)}
            title="Keyboard shortcuts (?)"
          >
            <Keyboard size={14} />
          </Button>
        </div>
      </div>

      {/* Countdown timer bar (session-level, shared across panels) */}
      <CountdownTimerBar
        active={timerActive}
        totalSeconds={commTimeout}
        autoReply={commAutoReply}
        onKeepGoing={() => setTimerActive(false)}
        onTimeout={() => setTimerActive(false)}
      />

      {/* Factory Mode panel -- collapsible, between timer and main content */}
      {showFactory && (
        <div className="px-3 py-2 border-b border-border bg-card/50 shrink-0">
          <FactoryPanel
            projectName={workingDirectory}
            model={pendingModel}
            yoloMode={false}
          />
        </div>
      )}

      {/* Main content area: sidebar | chat(s) | library */}
      <div className="flex flex-1 overflow-hidden">
        {/* Mobile backdrop -- darkens the screen when the sidebar drawer is open */}
        {mobileSidebarOpen && (
          <div
            className="fixed inset-0 bg-black/40 z-40 md:hidden"
            onClick={() => setMobileSidebarOpen(false)}
          />
        )}

        {/* Sidebar: fixed overlay on mobile, normal column on desktop */}
        <div
          className={`
            shrink-0 transition-all duration-200
            md:relative md:flex md:flex-col
            ${mobileSidebarOpen
              ? 'fixed inset-y-0 left-0 z-50 flex flex-col bg-card shadow-xl w-72'
              : 'hidden md:flex'
            }
            ${sidebarCollapsed && !mobileSidebarOpen ? 'md:w-0 md:overflow-hidden' : ''}
          `}
        >
          <WorkspaceSidebar
            activeConversationId={activeConversationId}
            streamingIds={streamingIds}
            collapsed={sidebarCollapsed && !mobileSidebarOpen}
            onToggleCollapse={() => {
              setSidebarCollapsed(!sidebarCollapsed)
              // On mobile, also close the drawer when collapsing via the sidebar button
              setMobileSidebarOpen(false)
            }}
            onNewChat={handleNewChat}
            onSelectConversation={handleSelectConversation}
            onDeleteConversation={handleDeleteConversation}
            selectedWorkingDirectory={workingDirectory}
            onWorkingDirectoryChange={handleRepoSelect}
            modelPresetIndex={modelPresetIndex}
            onModelPresetChange={handleModelPresetChange}
            effortLevel={pendingEffort}
            onEffortChange={setPendingEffort}
            activeProvider={activeProvider}
          />
        </div>

        {splitView ? (
          /* Three-panel split view with accordion collapse */
          <div className="flex-1 flex overflow-hidden">

            {/* Panel 1: Research (200K subscription) — always mounted, toggled via CSS */}
            {researchCollapsed && (
              <CollapsedPanelBar
                label="RESEARCH"
                color="bg-emerald-500/5"
                onClick={() => setResearchCollapsed(false)}
              />
            )}
            <div className={`flex-1 min-w-0 flex flex-col overflow-hidden border-r border-border relative${researchCollapsed ? ' hidden' : ''}`}>
              {/* Collapse button */}
              <button
                onClick={() => setResearchCollapsed(true)}
                className="absolute top-1 right-1 z-10 p-0.5 text-muted-foreground/40 hover:text-muted-foreground"
                title="Collapse Research panel"
              >
                <ChevronsLeft size={14} />
              </button>
              <WorkspaceChat
                conversationId={activeConversationId}
                onConversationCreated={handleConversationCreated}
                onNewConversation={handleBackToConversations}
                chatInputRef={chatInputRef}
                workingDirectory={workingDirectory}
                fixedContextMode="200k"
                panelLabel={`RESEARCH (${researchModel === 'opus' ? 'Opus' : 'Sonnet'} · 200K)`}
                onCopyToPassoff={handleCopyToPassoff}
                preferredModel={researchModel}
                onModelChange={setResearchModel}
                onStreamingChange={(streaming) => {
                  if (activeConversationId != null) {
                    setStreamingIds(prev => {
                      const has = prev.has(activeConversationId)
                      if (streaming && has) return prev
                      if (!streaming && !has) return prev
                      const next = new Set(prev)
                      if (streaming) next.add(activeConversationId)
                      else next.delete(activeConversationId)
                      return next
                    })
                  }
                }}
              />
            </div>

            {/* Panel 2: PRD Builder (Opus 4.6, 1M API) with passoff tabs — always mounted, toggled via CSS */}
            {prdCollapsed && (
              <CollapsedPanelBar
                label="PRD BUILDER"
                color="bg-violet-500/5"
                onClick={() => setPrdCollapsed(false)}
              />
            )}
            <div className={`flex-1 min-w-0 flex flex-col overflow-hidden border-r border-border relative${prdCollapsed ? ' hidden' : ''}`}>
              {/* Collapse button */}
              <button
                onClick={() => setPrdCollapsed(true)}
                className="absolute top-1 right-1 z-10 p-0.5 text-muted-foreground/40 hover:text-muted-foreground"
                title="Collapse PRD Builder panel"
              >
                <ChevronsLeft size={14} />
              </button>

              {/* Tab bar */}
              <div className="flex items-center border-b border-border bg-card shrink-0">
                <button
                  onClick={() => setShowPassoffOverlay(false)}
                  className={`px-3 py-1.5 text-xs font-semibold border-b-2 transition-colors ${
                    !showPassoffOverlay
                      ? 'border-violet-500 text-violet-600'
                      : 'border-transparent text-muted-foreground hover:text-foreground'
                  }`}
                >
                  Chat
                </button>
                <button
                  onClick={() => setShowPassoffOverlay(true)}
                  className={`px-3 py-1.5 text-xs font-semibold border-b-2 transition-colors flex items-center gap-1.5 ${
                    showPassoffOverlay
                      ? 'border-amber-500 text-amber-600'
                      : 'border-transparent text-muted-foreground hover:text-foreground'
                  }`}
                >
                  Passoff
                  {passoffSections.length > 0 && (
                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${
                      showPassoffOverlay
                        ? 'bg-amber-500/20 text-amber-600'
                        : 'bg-muted text-muted-foreground'
                    }`}>
                      {passoffSections.length}
                    </span>
                  )}
                </button>
              </div>

              {/* Tab content — both kept mounted, toggled via CSS hidden */}
              <div className={`flex-1 overflow-hidden${showPassoffOverlay ? '' : ' hidden'}`}>
                <PassoffEditor
                  sections={passoffSections}
                  onSectionsChange={setPassoffSections}
                  onSendToExecute={handleSendToPrd}
                  preamble={passoffPreamble}
                  onPreambleChange={setPassoffPreamble}
                />
              </div>
              <div className={`flex-1 overflow-hidden${showPassoffOverlay ? ' hidden' : ''}`}>
                <WorkspaceChat
                  conversationId={prdConversationId}
                  onConversationCreated={handlePrdConversationCreated}
                  onNewConversation={handlePrdNewChat}
                  workingDirectory={workingDirectory}
                  fixedContextMode={prdModel === 'sonnet' ? '200k' : '1m'}
                  panelLabel={`PRD BUILDER (${prdModel === 'opus' ? 'Opus' : 'Sonnet'} · ${prdModel === 'sonnet' ? '200K' : '1M'})`}
                  injectMessage={prdInjectMessage}
                  onInjectConsumed={handlePrdInjectConsumed}
                  onResponseComplete={handlePrdResponseComplete}
                  preferredModel={prdModel}
                  onModelChange={setPrdModel}
                  onStreamingChange={(streaming) => {
                    if (prdConversationId != null) {
                      setStreamingIds(prev => {
                        const has = prev.has(prdConversationId)
                        if (streaming && has) return prev
                        if (!streaming && !has) return prev
                        const next = new Set(prev)
                        if (streaming) next.add(prdConversationId)
                        else next.delete(prdConversationId)
                        return next
                      })
                    }
                  }}
                />
              </div>
            </div>

            {/* Panel 3: Coder (model-dependent context) — always mounted, toggled via CSS */}
            {coderCollapsed && (
              <CollapsedPanelBar
                label="CODER"
                color="bg-cyan-500/5"
                onClick={() => setCoderCollapsed(false)}
              />
            )}
            <div className={`flex-1 min-w-0 flex flex-col overflow-hidden relative${coderCollapsed ? ' hidden' : ''}`}>
              {/* Collapse button */}
              <button
                onClick={() => setCoderCollapsed(true)}
                className="absolute top-1 right-1 z-10 p-0.5 text-muted-foreground/40 hover:text-muted-foreground"
                title="Collapse Coder panel"
              >
                <ChevronsRight size={14} />
              </button>
              <WorkspaceChat
                conversationId={coderConversationId}
                onConversationCreated={handleCoderConversationCreated}
                onNewConversation={handleCoderNewChat}
                workingDirectory={workingDirectory}
                fixedContextMode={coderModel === 'sonnet' ? '200k' : '1m'}
                panelLabel={`CODER (${coderModel === 'opus' ? 'Opus' : 'Sonnet'} · ${coderModel === 'sonnet' ? '200K' : '1M'})`}
                injectMessage={coderInjectMessage}
                onInjectConsumed={handleCoderInjectConsumed}
                preferredModel={coderModel}
                onModelChange={setCoderModel}
                onStreamingChange={(streaming) => {
                  if (coderConversationId != null) {
                    setStreamingIds(prev => {
                      const has = prev.has(coderConversationId)
                      if (streaming && has) return prev
                      if (!streaming && !has) return prev
                      const next = new Set(prev)
                      if (streaming) next.add(coderConversationId)
                      else next.delete(coderConversationId)
                      return next
                    })
                  }
                }}
              />
            </div>

          </div>
        ) : (
          /* Single panel: normal mode */
          <div className="flex-1 flex flex-col overflow-hidden">
            <WorkspaceChat
              conversationId={activeConversationId}
              onConversationCreated={handleConversationCreated}
              onNewConversation={handleBackToConversations}
              chatInputRef={chatInputRef}
              workingDirectory={workingDirectory}
              onWalkieTalkieLog={setWalkieTalkieLog}
              pendingModel={pendingModel}
              pendingContextMode={pendingContextMode}
              pendingEffort={pendingEffort}
              provider={activeProvider}
              newChatKey={newChatKey}
              onStreamingChange={(streaming) => {
                if (activeConversationId != null) {
                  setStreamingIds(prev => {
                    const has = prev.has(activeConversationId)
                    if (streaming && has) return prev
                    if (!streaming && !has) return prev
                    const next = new Set(prev)
                    if (streaming) next.add(activeConversationId)
                    else next.delete(activeConversationId)
                    return next
                  })
                }
              }}
            />
          </div>
        )}

        {/* Swarm panel (slides in from right, before library) -- hidden on mobile */}
        {showSwarm && (
          <div className="hidden md:block w-80 border-l border-border shrink-0">
            <SwarmPanel
              workingDirectory={workingDirectory}
              onClose={() => setShowSwarm(false)}
            />
          </div>
        )}

        {/* Library panel -- hidden on mobile to give chat full width */}
        <div className="hidden md:flex">
          <WorkspaceLibrary
            conversationId={activeConversationId}
            collapsed={libraryCollapsed}
            onToggleCollapse={() => setLibraryCollapsed(!libraryCollapsed)}
            walkieTalkieLog={walkieTalkieLog}
          />
        </div>
      </div>

      {/* Keyboard shortcuts help modal */}
      <WorkspaceKeyboardHelp
        isOpen={showKeyboardHelp}
        onClose={() => setShowKeyboardHelp(false)}
      />

      {/* Floating user guide & notes panel */}
      <WorkspaceUserGuide
        isOpen={showUserGuide}
        onClose={() => setShowUserGuide(false)}
      />

      {/* Provider switch confirmation dialog */}
      {pendingProviderSwitch && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-card border border-border rounded-lg shadow-lg p-6 max-w-sm w-full mx-4">
            <h3 className="text-sm font-semibold text-foreground mb-2">
              Switch to {pendingProviderSwitch.charAt(0).toUpperCase() + pendingProviderSwitch.slice(1)}?
            </h3>
            <p className="text-xs text-muted-foreground mb-4">
              This will change the active provider for new conversations. Your current chat will keep its original provider.
            </p>
            <div className="flex items-center justify-end gap-2">
              <Button
                variant="ghost"
                size="sm"
                className="h-7 text-xs"
                onClick={() => setPendingProviderSwitch(null)}
              >
                Cancel
              </Button>
              <Button
                size="sm"
                className="h-7 text-xs"
                onClick={() => {
                  setActiveProvider(pendingProviderSwitch)
                  setPendingProviderSwitch(null)
                }}
              >
                Switch
              </Button>
            </div>
          </div>
        </div>
      )}

    </div>
  )
}
