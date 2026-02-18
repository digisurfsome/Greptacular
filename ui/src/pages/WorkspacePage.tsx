/**
 * WorkspacePage - Full-page workspace layout with sidebar, chat, and library panel.
 *
 * Provides a standalone coding workspace at /#/workspace with multi-conversation
 * management, full Claude agent capabilities, file library, GitHub repos,
 * real-time context budget tracking, keyboard shortcuts, and breadcrumb navigation.
 */

import { useState, useCallback, useRef } from 'react'
import { WorkspaceSidebar } from '../components/workspace/WorkspaceSidebar'
import { WorkspaceChat } from '../components/workspace/WorkspaceChat'
import { WorkspaceLibrary } from '../components/workspace/WorkspaceLibrary'
import { WorkspaceKeyboardHelp } from '../components/workspace/WorkspaceKeyboardHelp'
import { WorkspaceUserGuide } from '../components/workspace/WorkspaceUserGuide'
import { RepoSelector } from '../components/workspace/RepoSelector'
import { useWorkspaceKeyboardShortcuts } from '../hooks/useWorkspaceKeyboardShortcuts'
import { exportConversationMarkdown } from '../lib/api'
import { ArrowLeft, ChevronRight, Keyboard, BookOpen, Columns2 } from 'lucide-react'
import { Button } from '@/components/ui/button'

/** Full-page workspace layout with keyboard shortcuts, breadcrumbs, and all Phase 4 features. */
export function WorkspacePage(): React.JSX.Element {
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null)
  const [workingDirectory, setWorkingDirectory] = useState<string | null>(null)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [libraryCollapsed, setLibraryCollapsed] = useState(false)
  const [showKeyboardHelp, setShowKeyboardHelp] = useState(false)
  const [showUserGuide, setShowUserGuide] = useState(false)
  const [splitView, setSplitView] = useState(false)
  // In split view, each panel has its own independent conversation.
  // The left panel (Research/200K) uses activeConversationId.
  // The right panel (Execute/1M) uses its own state.
  const [rightConversationId, setRightConversationId] = useState<number | null>(null)
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
    // Focus the sidebar search input
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

  const handleRightConversationCreated = useCallback((id: number) => {
    setRightConversationId(id)
  }, [])

  const handleRightNewChat = useCallback(() => {
    setRightConversationId(null)
  }, [])

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
            title="Split view: Research (Free) + Execute (API) side by side"
          >
            <Columns2 size={14} />
            <span className="text-[10px]">Split</span>
          </Button>
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
          /* Split view: two panels side by side */
          <div className="flex-1 flex overflow-hidden">
            {/* Left panel: Research (Subscription/200K) */}
            <div className="flex-1 flex flex-col overflow-hidden border-r border-border">
              <WorkspaceChat
                conversationId={activeConversationId}
                onConversationCreated={handleConversationCreated}
                onNewConversation={handleNewChat}
                chatInputRef={chatInputRef}
                workingDirectory={workingDirectory}
                fixedContextMode="200k"
                panelLabel="RESEARCH (FREE)"
              />
            </div>
            {/* Right panel: Execute (API/1M) */}
            <div className="flex-1 flex flex-col overflow-hidden">
              <WorkspaceChat
                conversationId={rightConversationId}
                onConversationCreated={handleRightConversationCreated}
                onNewConversation={handleRightNewChat}
                workingDirectory={workingDirectory}
                fixedContextMode="1m"
                panelLabel="EXECUTE (API)"
              />
            </div>
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
