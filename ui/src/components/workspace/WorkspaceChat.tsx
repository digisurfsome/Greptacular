/**
 * Workspace Chat
 *
 * Main chat area for the IdeaForge Workspace feature. Manages message
 * display, user input, and WebSocket communication for a single
 * conversation. Merges initial REST-loaded messages with live WebSocket
 * messages using Map-based deduplication. Handles both new conversation
 * creation (conversationId === null) and resuming existing conversations.
 */

import { useState, useRef, useEffect, useCallback, useMemo } from 'react'
import { Send, Loader2, MessageSquare } from 'lucide-react'
import { useWorkspaceChat } from '@/hooks/useWorkspaceChat'
import { useWorkspaceConversation } from '@/hooks/useWorkspaceConversations'
import { ChatMessage } from '@/components/ChatMessage'
import { isSubmitEnter } from '@/lib/keyboard'
import { Button } from '@/components/ui/button'
import { WorkspaceChatHeader } from './WorkspaceChatHeader'
import { ContextBudgetBar } from './ContextBudgetBar'
import type { ChatMessage as ChatMessageType } from '@/lib/types'

interface WorkspaceChatProps {
  conversationId: number | null
  onConversationCreated: (id: number) => void
}

/** Generate a unique ID for local messages. */
function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`
}

/**
 * Build a dedup key for a message to detect duplicates across REST and
 * WebSocket sources. Falls back to the message ID when content/timestamp
 * pairs are not suitable.
 */
function dedupKey(msg: ChatMessageType): string {
  return `${msg.role}:${msg.timestamp.getTime()}:${msg.content.slice(0, 80)}`
}

/** Main chat area with messages, input, and WebSocket communication. */
export function WorkspaceChat({
  conversationId,
  onConversationCreated,
}: WorkspaceChatProps): React.JSX.Element {
  const [inputValue, setInputValue] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const lastConversationIdRef = useRef<number | null | undefined>(undefined)

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
    start,
    sendMessage,
    disconnect,
    clearMessages,
  } = useWorkspaceChat({ onError: handleError })

  // REST query for initial messages when resuming a conversation
  const { data: conversationDetail, isLoading: isLoadingConversation } =
    useWorkspaceConversation(conversationId)

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
    const isSwitching = lastConversationIdRef.current !== undefined
    lastConversationIdRef.current = conversationId

    if (isSwitching) {
      disconnect()
      clearMessages()
    }

    // Null means "new chat" -- start without an ID
    if (conversationId !== null) {
      start(conversationId)
    }
  }, [conversationId, isLoadingConversation, start, disconnect, clearMessages])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [liveMessages])

  // Focus input when not loading
  useEffect(() => {
    if (!isLoading) {
      inputRef.current?.focus()
    }
  }, [isLoading])

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

  // Send handler
  const handleSend = useCallback(() => {
    const content = inputValue.trim()
    if (!content || isLoading) return

    // If no conversation yet, start a new one with the first message
    if (conversationId === null && activeConversationId === null) {
      start()
      // Wait briefly for WebSocket to connect, then send
      const waitAndSend = (retries: number) => {
        setTimeout(() => {
          sendMessage(content)
          if (retries <= 0) return
        }, 200)
      }
      waitAndSend(5)
    } else {
      sendMessage(content)
    }

    setInputValue('')
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
  // The parent page manages mutations via useUpdateWorkspaceConversation.
  const handleUpdateTitle = useCallback(
    () => void 0 as void,
    [],
  ) as (title: string) => void

  const handleUpdateCategory = useCallback(
    () => void 0 as void,
    [],
  ) as (category: string) => void

  const effectiveTitle = conversationDetail?.title ?? null
  const effectiveCategory = conversationDetail?.category ?? 'general'

  // Empty state when no conversation is selected
  const showEmptyState = conversationId === null && displayMessages.length === 0

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header */}
      <WorkspaceChatHeader
        conversationId={conversationId ?? activeConversationId}
        title={effectiveTitle}
        category={effectiveCategory}
        connectionStatus={connectionStatus}
        onUpdateTitle={handleUpdateTitle}
        onUpdateCategory={handleUpdateCategory}
      />

      {/* Context budget bar */}
      {totalTokens > 0 && (
        <ContextBudgetBar
          totalTokens={totalTokens}
          contextWindow={contextWindow}
        />
      )}

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto">
        {showEmptyState ? (
          <div className="flex flex-col items-center justify-center h-full gap-3 text-muted-foreground">
            <MessageSquare size={40} strokeWidth={1.5} />
            <div className="text-center">
              <p className="text-base font-medium text-foreground">
                IdeaForge Workspace
              </p>
              <p className="text-sm mt-1">
                Start a new chat or select a conversation
              </p>
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

      {/* Input area */}
      <div className="border-t border-border p-4 bg-card">
        <div className="flex gap-2">
          <textarea
            ref={inputRef}
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
    </div>
  )
}
