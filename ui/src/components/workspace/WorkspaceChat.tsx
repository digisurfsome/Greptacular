/**
 * Workspace Chat
 *
 * Main chat area for the IdeaForge Workspace feature. Manages message
 * display, user input, and WebSocket communication for a single
 * conversation. Merges initial REST-loaded messages with live WebSocket
 * messages using Map-based deduplication. Handles both new conversation
 * creation (conversationId === null) and resuming existing conversations.
 *
 * Phase 4 additions: fork/inject/export actions via header dropdown,
 * injection indicator, draft persistence, smart auto-scroll.
 */

import { useState, useRef, useEffect, useCallback, useMemo } from 'react'
import {
  Send,
  Loader2,
  MessageSquare,
  MoreHorizontal,
  GitFork,
  ArrowDownToLine,
  Download,
  X,
  Plus,
  WifiOff,
} from 'lucide-react'
import { useWorkspaceChat } from '@/hooks/useWorkspaceChat'
import { useWorkspaceConversation } from '@/hooks/useWorkspaceConversations'
import { ChatMessage } from '@/components/ChatMessage'
import { isSubmitEnter } from '@/lib/keyboard'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getWorkspaceSummary, regenerateWorkspaceSummary, exportConversationMarkdown } from '@/lib/api'
import { WorkspaceChatHeader } from './WorkspaceChatHeader'
import { EnhancedContextBudgetBar, getContextWarningClass } from './EnhancedContextBudgetBar'
import { AutoSummaryPin } from './AutoSummaryPin'
import { ChatForkModal } from './ChatForkModal'
import { InjectFromChatModal } from './InjectFromChatModal'
import type { ChatMessage as ChatMessageType, WorkspaceMessage, PendingInjection } from '@/lib/types'

const DRAFT_KEY_PREFIX = 'workspace-draft-'

interface WorkspaceChatProps {
  conversationId: number | null
  onConversationCreated: (id: number) => void
  onNewConversation?: () => void
  chatInputRef?: React.RefObject<HTMLTextAreaElement | null>
}

/** Generate a unique ID for local messages. */
function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`
}

/**
 * Build a dedup key for a message to detect duplicates across REST and
 * WebSocket sources.
 */
function dedupKey(msg: ChatMessageType): string {
  return `${msg.role}:${msg.timestamp.getTime()}:${msg.content.slice(0, 80)}`
}

/** Main chat area with messages, input, and WebSocket communication. */
export function WorkspaceChat({
  conversationId,
  onConversationCreated,
  onNewConversation,
  chatInputRef: externalInputRef,
}: WorkspaceChatProps): React.JSX.Element {
  const [inputValue, setInputValue] = useState('')
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const internalInputRef = useRef<HTMLTextAreaElement>(null)
  const inputRef = externalInputRef ?? internalInputRef
  const lastConversationIdRef = useRef<number | null | undefined>(undefined)
  const [isUserScrolledUp, setIsUserScrolledUp] = useState(false)
  const [showForkModal, setShowForkModal] = useState(false)
  const [showInjectModal, setShowInjectModal] = useState(false)

  // Memoize error handler to keep hook reference stable
  const handleError = useCallback((error: string) => {
    console.error('Workspace chat error:', error)
  }, [])

  // WebSocket-based chat hook
  const {
    messages: liveMessages,
    isLoading,
    connectionStatus,
    conversationId: activeConversationId,
    totalTokens,
    contextWindow,
    contextBudget,
    pendingInjection,
    setPendingInjection,
    start,
    sendMessage,
    disconnect,
    clearMessages,
  } = useWorkspaceChat({ onError: handleError })

  // REST query for initial messages when resuming a conversation
  const { data: conversationDetail, isLoading: isLoadingConversation } =
    useWorkspaceConversation(conversationId)

  // Summary query and mutation for auto-summary pin
  const queryClient = useQueryClient()

  const { data: summary } = useQuery({
    queryKey: ['workspace', 'summary', conversationId ?? activeConversationId],
    queryFn: () => getWorkspaceSummary((conversationId ?? activeConversationId)!),
    enabled: (conversationId ?? activeConversationId) !== null,
  })

  const regenerateMutation = useMutation({
    mutationFn: () => regenerateWorkspaceSummary((conversationId ?? activeConversationId)!),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['workspace', 'summary', conversationId ?? activeConversationId],
      })
    },
  })

  // Context budget usage for warning state
  const usagePercent = contextBudget.messageTokens > 0
    ? ((contextBudget.messageTokens + contextBudget.summaryTokens) / 1_000_000) * 100
    : 0

  // Notify parent when a new conversation is created via WebSocket
  const previousActiveIdRef = useRef<number | null>(activeConversationId)
  useEffect(() => {
    const hadNone = previousActiveIdRef.current === null
    const hasNow = activeConversationId !== null

    if (hadNone && hasNow) {
      onConversationCreated(activeConversationId)
    }

    previousActiveIdRef.current = activeConversationId
  }, [activeConversationId, onConversationCreated])

  // Start or resume session when conversationId changes
  useEffect(() => {
    if (isLoadingConversation) return

    // Only act when the ID has actually changed
    if (lastConversationIdRef.current === conversationId) return
    const previousId = lastConversationIdRef.current
    lastConversationIdRef.current = conversationId

    // When a new conversation is created via the active WebSocket (null → new ID),
    // the session already owns this conversation. Don't tear it down.
    if (previousId === null && conversationId !== null && activeConversationId === conversationId) {
      return
    }

    // Genuine switch between conversations — disconnect the old session
    if (previousId !== undefined) {
      disconnect()
      clearMessages()
    }

    // Start/resume the selected conversation
    if (conversationId !== null) {
      start(conversationId)
    }
  }, [conversationId, isLoadingConversation, activeConversationId, start, disconnect, clearMessages])

  // Smart auto-scroll: only scroll if user is near the bottom
  const handleScroll = useCallback(() => {
    const container = messagesContainerRef.current
    if (!container) return
    const distanceFromBottom = container.scrollHeight - container.scrollTop - container.clientHeight
    setIsUserScrolledUp(distanceFromBottom > 100)
  }, [])

  useEffect(() => {
    if (!isUserScrolledUp) {
      messagesContainerRef.current?.scrollTo({
        top: messagesContainerRef.current.scrollHeight,
        behavior: 'smooth',
      })
    }
  }, [liveMessages.length, isUserScrolledUp])

  // Focus input when not loading
  useEffect(() => {
    if (!isLoading) {
      inputRef.current?.focus()
    }
  }, [isLoading, inputRef])

  // Draft persistence: load draft when switching conversations
  useEffect(() => {
    if (conversationId !== null) {
      const draft = localStorage.getItem(`${DRAFT_KEY_PREFIX}${conversationId}`)
      setInputValue(draft || '')
    } else {
      setInputValue('')
    }
  }, [conversationId])

  // Draft persistence: save draft on input change (debounced)
  useEffect(() => {
    const effectiveId = conversationId ?? activeConversationId
    if (!effectiveId) return
    const timer = setTimeout(() => {
      if (inputValue) {
        localStorage.setItem(`${DRAFT_KEY_PREFIX}${effectiveId}`, inputValue)
      } else {
        localStorage.removeItem(`${DRAFT_KEY_PREFIX}${effectiveId}`)
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [inputValue, conversationId, activeConversationId])

  // Convert REST messages to ChatMessageType format for merging
  const initialMessages: ChatMessageType[] = useMemo(() => {
    if (!conversationDetail?.messages) return []
    return conversationDetail.messages.map((m) => ({
      id: `rest-${m.id}`,
      role: m.role,
      content: m.content,
      timestamp: m.timestamp ? new Date(m.timestamp) : new Date(),
    }))
  }, [conversationDetail])

  // Merge initial (REST) messages with live (WebSocket) messages, deduplicating
  const displayMessages: ChatMessageType[] = useMemo(() => {
    if (initialMessages.length === 0) return liveMessages
    if (liveMessages.length === 0) return initialMessages

    const seen = new Map<string, ChatMessageType>()
    for (const msg of initialMessages) {
      seen.set(dedupKey(msg), msg)
    }
    for (const msg of liveMessages) {
      // Live messages take precedence (may have streaming state)
      seen.set(dedupKey(msg), msg)
    }
    return Array.from(seen.values())
  }, [initialMessages, liveMessages])

  // Build WorkspaceMessage[] for the fork modal from REST conversation detail
  const forkableMessages: WorkspaceMessage[] = useMemo(() => {
    if (!conversationDetail?.messages) return []
    return conversationDetail.messages
      .filter((m) => m.role === 'user' || m.role === 'assistant')
      .map((m) => ({
        id: m.id,
        role: m.role as 'user' | 'assistant',
        content: m.content,
        token_estimate: m.token_estimate,
        timestamp: m.timestamp,
      }))
  }, [conversationDetail])

  // Send handler
  const handleSend = useCallback(() => {
    const content = inputValue.trim()
    if (!content || isLoading) return

    // If no conversation yet, start a new one with the first message.
    // start() connects the WebSocket and sends "start" to the backend.
    // After a delay (to let the session initialize), send the user message.
    if (conversationId === null && activeConversationId === null) {
      start()
      setTimeout(() => {
        sendMessage(content)
      }, 500)
    } else {
      sendMessage(content)
    }

    setInputValue('')
    // Clear draft after sending
    const effectiveId = conversationId ?? activeConversationId
    if (effectiveId) {
      localStorage.removeItem(`${DRAFT_KEY_PREFIX}${effectiveId}`)
    }
  }, [inputValue, isLoading, conversationId, activeConversationId, start, sendMessage])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (isSubmitEnter(e)) {
        e.preventDefault()
        handleSend()
      }
    },
    [handleSend],
  )

  // Title/category update handlers are no-ops at this level.
  const handleUpdateTitle = useCallback(
    () => void 0 as void,
    [],
  ) as (title: string) => void

  const handleUpdateCategory = useCallback(
    () => void 0 as void,
    [],
  ) as (category: string) => void

  const effectiveConversationId = conversationId ?? activeConversationId
  const effectiveTitle = conversationDetail?.title ?? null
  const effectiveCategory = conversationDetail?.category ?? 'general'
  const hasActiveChat = effectiveConversationId !== null

  // Empty state when no conversation is selected
  const showEmptyState = conversationId === null && displayMessages.length === 0

  const handleExport = useCallback(() => {
    if (effectiveConversationId) {
      exportConversationMarkdown(effectiveConversationId)
    }
  }, [effectiveConversationId])

  const handleForkCreated = useCallback((newId: number) => {
    setShowForkModal(false)
    onConversationCreated(newId)
    queryClient.invalidateQueries({ queryKey: ['workspace-conversations'] })
  }, [onConversationCreated, queryClient])

  const handleInject = useCallback((injection: PendingInjection) => {
    setPendingInjection(injection)
    setShowInjectModal(false)
  }, [setPendingInjection])

  return (
    <div className={`flex flex-col h-full bg-background transition-colors duration-500 ${getContextWarningClass(usagePercent)}`}>
      {/* Header with actions dropdown */}
      <div className="flex items-center border-b border-border bg-card">
        <div className="flex-1">
          <WorkspaceChatHeader
            conversationId={effectiveConversationId}
            title={effectiveTitle}
            category={effectiveCategory}
            connectionStatus={connectionStatus}
            onUpdateTitle={handleUpdateTitle}
            onUpdateCategory={handleUpdateCategory}
          />
        </div>

        {/* Actions dropdown */}
        {hasActiveChat && (
          <div className="pr-3">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm">
                  <MoreHorizontal size={16} />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => setShowForkModal(true)}>
                  <GitFork size={14} className="mr-2" />
                  Fork Chat
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setShowInjectModal(true)}>
                  <ArrowDownToLine size={14} className="mr-2" />
                  Inject from Chat
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleExport}>
                  <Download size={14} className="mr-2" />
                  Export as Markdown
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        )}
      </div>

      {/* Disconnection banner */}
      {connectionStatus === 'disconnected' && hasActiveChat && (
        <div className="bg-destructive/10 border-b border-destructive/20 px-4 py-2 text-sm text-destructive flex items-center gap-2">
          <WifiOff size={14} />
          Connection lost. Reconnecting...
        </div>
      )}

      {/* Context budget bar */}
      {(totalTokens > 0 || contextBudget.messageTokens > 0) && (
        <EnhancedContextBudgetBar
          totalBudget={contextWindow}
          messageTokens={contextBudget.messageTokens || totalTokens}
          summaryTokens={contextBudget.summaryTokens}
          messageCount={contextBudget.messageCount}
          isStreaming={isLoading}
        />
      )}

      {/* Auto-summary pin */}
      <AutoSummaryPin
        summary={summary?.summary ?? null}
        updatedAt={summary?.created_at ?? null}
        messagesCovered={summary?.message_count ?? null}
        onRegenerate={() => regenerateMutation.mutate()}
        isRegenerating={regenerateMutation.isPending}
      />

      {/* Messages area */}
      <div
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto"
        onScroll={handleScroll}
      >
        {showEmptyState ? (
          <div className="flex flex-col items-center justify-center h-full gap-3 text-muted-foreground">
            <MessageSquare size={48} className="text-muted-foreground/30" />
            <div className="text-center">
              <h2 className="text-lg font-semibold text-foreground mb-2">
                No conversations yet
              </h2>
              <p className="text-sm mb-6 max-w-sm">
                Start your first conversation to brainstorm ideas, explore concepts, or get help with your projects.
              </p>
              {onNewConversation && (
                <Button onClick={onNewConversation}>
                  <Plus size={16} className="mr-2" />
                  Start a Conversation
                </Button>
              )}
            </div>
          </div>
        ) : isLoadingConversation ? (
          <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
            <div className="flex items-center gap-2">
              <Loader2 size={16} className="animate-spin" />
              <span>Loading conversation...</span>
            </div>
          </div>
        ) : (
          <div className="py-4">
            {displayMessages.map((message) => (
              <ChatMessage
                key={message.id ?? generateId()}
                message={message}
              />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Loading indicator */}
      {isLoading && displayMessages.length > 0 && (
        <div className="px-4 py-2 border-t border-border bg-background">
          <div className="flex items-center gap-2 text-muted-foreground text-sm">
            <Loader2 size={16} className="animate-spin" />
            <span>Thinking...</span>
          </div>
        </div>
      )}

      {/* Injection indicator */}
      {pendingInjection && (
        <div className="flex items-center gap-2 px-4 py-2 bg-muted border-t border-border text-sm text-muted-foreground">
          <ArrowDownToLine size={14} />
          <span>
            Injecting {pendingInjection.messages.length} message{pendingInjection.messages.length !== 1 ? 's' : ''} from &quot;{pendingInjection.sourceTitle}&quot;
          </span>
          <button
            onClick={() => setPendingInjection(null)}
            className="ml-auto text-muted-foreground hover:text-foreground"
          >
            <X size={14} />
          </button>
        </div>
      )}

      {/* Input area */}
      <div className="border-t border-border p-4 bg-card">
        <div className="flex gap-2">
          <textarea
            ref={inputRef as React.RefObject<HTMLTextAreaElement>}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything..."
            disabled={isLoading || isLoadingConversation}
            className="flex-1 resize-none min-h-[44px] max-h-[120px] rounded-md border border-border bg-input px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground outline-none ring-ring focus:ring-1 disabled:cursor-not-allowed disabled:opacity-50"
            rows={1}
          />
          <Button
            onClick={handleSend}
            disabled={!inputValue.trim() || isLoading || isLoadingConversation}
            title="Send message"
          >
            {isLoading ? (
              <Loader2 size={18} className="animate-spin" />
            ) : (
              <Send size={18} />
            )}
          </Button>
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>

      {/* Fork modal */}
      {showForkModal && effectiveConversationId && (
        <ChatForkModal
          isOpen={showForkModal}
          onClose={() => setShowForkModal(false)}
          conversationId={effectiveConversationId}
          conversationTitle={effectiveTitle || 'Untitled'}
          messages={forkableMessages}
          onForkCreated={handleForkCreated}
        />
      )}

      {/* Inject modal */}
      {showInjectModal && effectiveConversationId && (
        <InjectFromChatModal
          isOpen={showInjectModal}
          onClose={() => setShowInjectModal(false)}
          currentConversationId={effectiveConversationId}
          onInject={handleInject}
        />
      )}
    </div>
  )
}
