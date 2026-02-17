/**
 * WorkspacePage - Full-page workspace layout with sidebar and chat area.
 *
 * Provides a standalone coding workspace at /#/workspace with multi-conversation
 * management, full Claude agent capabilities, and real-time context budget tracking.
 */

import { useState, useCallback } from 'react'
import { WorkspaceSidebar } from '../components/workspace/WorkspaceSidebar'
import { WorkspaceChat } from '../components/workspace/WorkspaceChat'
import { ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'

/** Full-page workspace layout with conversation sidebar and chat area. */
export function WorkspacePage(): React.JSX.Element {
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  const handleNewChat = useCallback(() => {
    setActiveConversationId(null)
  }, [])

  const handleSelectConversation = useCallback((id: number) => {
    setActiveConversationId(id)
  }, [])

  const handleConversationCreated = useCallback((id: number) => {
    setActiveConversationId(id)
  }, [])

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Top bar with back-to-projects link */}
      <div className="flex items-center h-10 px-3 border-b border-border bg-card shrink-0">
        <Button
          variant="ghost"
          size="sm"
          className="gap-1.5 text-muted-foreground hover:text-foreground"
          onClick={() => { window.location.hash = '' }}
        >
          <ArrowLeft size={14} />
          <span className="text-xs">Back to Projects</span>
        </Button>
        <span className="ml-3 text-sm font-semibold text-foreground">
          IdeaForge Workspace
        </span>
      </div>

      {/* Main content area */}
      <div className="flex flex-1 overflow-hidden">
        <WorkspaceSidebar
          activeConversationId={activeConversationId}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
          onNewChat={handleNewChat}
          onSelectConversation={handleSelectConversation}
        />
        <WorkspaceChat
          conversationId={activeConversationId}
          onConversationCreated={handleConversationCreated}
        />
      </div>
    </div>
  )
}
