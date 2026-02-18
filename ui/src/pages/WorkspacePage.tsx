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
 *   3. Coder (Sonnet 4.6, 1M API) — execute the PRD
 *
 * The passoff editor overlays on the PRD panel. Auto-forward sends the PRD
 * panel's completed response directly to the Coder panel.
 */

import { useState, useCallback, useRef } from 'react'
import { WorkspaceSidebar } from '../components/workspace/WorkspaceSidebar'
import { WorkspaceChat } from '../components/workspace/WorkspaceChat'
import { WorkspaceLibrary } from '../components/workspace/WorkspaceLibrary'
import { WorkspaceKeyboardHelp } from '../components/workspace/WorkspaceKeyboardHelp'
import { WorkspaceUserGuide } from '../components/workspace/WorkspaceUserGuide'
import { RepoSelector } from '../components/workspace/RepoSelector'
import { PassoffEditor, type PassoffSection } from '../components/workspace/PassoffEditor'
import { useWorkspaceKeyboardShortcuts } from '../hooks/useWorkspaceKeyboardShortcuts'
import { exportConversationMarkdown } from '../lib/api'
import {
  ArrowLeft,
  ChevronRight,
  Keyboard,
  BookOpen,
  Columns2,
  ChevronsLeft,
  ChevronsRight,
  FileText,
  Zap,
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

/** Full-page workspace layout with keyboard shortcuts, breadcrumbs, and all Phase 4 features. */
export function WorkspacePage(): React.JSX.Element {
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null)
  const [workingDirectory, setWorkingDirectory] = useState<string | null>(null)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [libraryCollapsed, setLibraryCollapsed] = useState(false)
  const [showKeyboardHelp, setShowKeyboardHelp] = useState(false)
  const [showUserGuide, setShowUserGuide] = useState(false)
  const [splitView, setSplitView] = useState(false)

  // Three-panel state (split view)
  const [prdConversationId, setPrdConversationId] = useState<number | null>(null)
  const [coderConversationId, setCoderConversationId] = useState<number | null>(null)
  const [researchCollapsed, setResearchCollapsed] = useState(false)
  const [prdCollapsed, setPrdCollapsed] = useState(false)
  const [coderCollapsed, setCoderCollapsed] = useState(false)

  // Passoff editor state — overlays on PRD panel
  const [passoffSections, setPassoffSections] = useState<PassoffSection[]>([])
  const [passoffPreamble, setPassoffPreamble] = useState('')
  const [showPassoffOverlay, setShowPassoffOverlay] = useState(false)

  // Inject messages for PRD and Coder panels
  const [prdInjectMessage, setPrdInjectMessage] = useState<string | null>(null)
  const [coderInjectMessage, setCoderInjectMessage] = useState<string | null>(null)

  // Auto-forward: when PRD panel finishes, auto-send to Coder panel
  const [autoForward, setAutoForward] = useState(false)

  const chatInputRef = useRef<HTMLTextAreaElement | null>(null)

  const handleNewChat = useCallback(() => {
    setActiveConversationId(null)
  }, [])

  const handleSelectConversation = useCallback((id: number) => {
    setActiveConversationId(id)
  }, [])

  const handleConversationCreated = useCallback((id: number) => {
    setActiveConversationId(id)
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
    onNewConversation: handleNewChat,
    onToggleLibrary: () => setLibraryCollapsed((v) => !v),
    onToggleSidebar: () => setSidebarCollapsed((v) => !v),
    onFocusSearch: handleFocusSearch,
    onExportChat: handleExportChat,
    onShowShortcutsHelp: () => setShowKeyboardHelp(true),
    onFocusChatInput: handleFocusChatInput,
    hasActiveConversation: activeConversationId !== null,
  })

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
            Workspace
          </span>
          <ChevronRight size={12} className="text-muted-foreground" />
          <RepoSelector
            onSelect={handleRepoSelect}
            selectedPath={workingDirectory}
          />
        </nav>

        <div className="ml-auto flex items-center gap-1">
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
            <span className="text-[10px]">Split</span>
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
              <span className="text-[10px]">Auto</span>
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 gap-1.5 text-muted-foreground hover:text-foreground"
            onClick={() => setShowUserGuide(v => !v)}
            title="User guide & notes"
          >
            <BookOpen size={14} />
            <span className="text-[10px]">Guide</span>
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

      {/* Main content area: sidebar | chat(s) | library */}
      <div className="flex flex-1 overflow-hidden">
        <WorkspaceSidebar
          activeConversationId={activeConversationId}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
          onNewChat={handleNewChat}
          onSelectConversation={handleSelectConversation}
        />

        {splitView ? (
          /* Three-panel split view with accordion collapse */
          <div className="flex-1 flex overflow-hidden">

            {/* Panel 1: Research (200K subscription) */}
            {researchCollapsed ? (
              <CollapsedPanelBar
                label="RESEARCH"
                color="bg-emerald-500/5"
                onClick={() => setResearchCollapsed(false)}
              />
            ) : (
              <div className="flex-1 min-w-0 flex flex-col overflow-hidden border-r border-border relative">
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
                  onNewConversation={handleNewChat}
                  chatInputRef={chatInputRef}
                  workingDirectory={workingDirectory}
                  fixedContextMode="200k"
                  panelLabel="RESEARCH (200K)"
                  onCopyToPassoff={handleCopyToPassoff}
                />
              </div>
            )}

            {/* Panel 2: PRD Builder (Opus 4.6, 1M API) with passoff overlay */}
            {prdCollapsed ? (
              <CollapsedPanelBar
                label="PRD BUILDER"
                color="bg-violet-500/5"
                onClick={() => setPrdCollapsed(false)}
              />
            ) : (
              <div className="flex-1 min-w-0 flex flex-col overflow-hidden border-r border-border relative">
                {/* Collapse button */}
                <button
                  onClick={() => setPrdCollapsed(true)}
                  className="absolute top-1 right-1 z-10 p-0.5 text-muted-foreground/40 hover:text-muted-foreground"
                  title="Collapse PRD Builder panel"
                >
                  <ChevronsLeft size={14} />
                </button>
                {/* Passoff overlay button */}
                <button
                  onClick={() => setShowPassoffOverlay(v => !v)}
                  className={`absolute top-1 right-7 z-10 p-0.5 transition-colors ${
                    showPassoffOverlay
                      ? 'text-amber-500'
                      : passoffSections.length > 0
                        ? 'text-amber-500/60 hover:text-amber-500'
                        : 'text-muted-foreground/40 hover:text-muted-foreground'
                  }`}
                  title={`Passoff editor (${passoffSections.length} sections)`}
                >
                  <FileText size={14} />
                </button>

                {/* Passoff overlay */}
                {showPassoffOverlay && (
                  <div className="absolute inset-0 z-20 bg-background/95 backdrop-blur-sm flex flex-col">
                    <PassoffEditor
                      sections={passoffSections}
                      onSectionsChange={setPassoffSections}
                      onSendToExecute={handleSendToPrd}
                      preamble={passoffPreamble}
                      onPreambleChange={setPassoffPreamble}
                    />
                    <button
                      onClick={() => setShowPassoffOverlay(false)}
                      className="absolute top-2 right-2 text-muted-foreground hover:text-foreground text-xs px-2 py-0.5 rounded border border-border bg-background"
                    >
                      Close
                    </button>
                  </div>
                )}

                <WorkspaceChat
                  conversationId={prdConversationId}
                  onConversationCreated={handlePrdConversationCreated}
                  onNewConversation={handlePrdNewChat}
                  workingDirectory={workingDirectory}
                  fixedContextMode="1m"
                  panelLabel="PRD BUILDER (Opus 4.6)"
                  injectMessage={prdInjectMessage}
                  onInjectConsumed={handlePrdInjectConsumed}
                  onResponseComplete={handlePrdResponseComplete}
                />
              </div>
            )}

            {/* Panel 3: Coder (Sonnet 4.6, 1M API) */}
            {coderCollapsed ? (
              <CollapsedPanelBar
                label="CODER"
                color="bg-cyan-500/5"
                onClick={() => setCoderCollapsed(false)}
              />
            ) : (
              <div className="flex-1 min-w-0 flex flex-col overflow-hidden relative">
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
                  fixedContextMode="1m"
                  panelLabel="CODER (Sonnet 4.6)"
                  injectMessage={coderInjectMessage}
                  onInjectConsumed={handleCoderInjectConsumed}
                />
              </div>
            )}

          </div>
        ) : (
          /* Single panel: normal mode */
          <div className="flex-1 flex flex-col overflow-hidden">
            <WorkspaceChat
              conversationId={activeConversationId}
              onConversationCreated={handleConversationCreated}
              onNewConversation={handleNewChat}
              chatInputRef={chatInputRef}
              workingDirectory={workingDirectory}
            />
          </div>
        )}

        <WorkspaceLibrary
          conversationId={activeConversationId}
          collapsed={libraryCollapsed}
          onToggleCollapse={() => setLibraryCollapsed(!libraryCollapsed)}
        />
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
    </div>
  )
}
