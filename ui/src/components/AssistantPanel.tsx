/**
 * Assistant Panel Component
 *
 * Slide-in panel container for the project assistant chat.
 * Renders as a portal on document.body when open.
 * Manages conversation state with localStorage persistence.
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { createPortal } from 'react-dom'
import { X, Bot } from 'lucide-react'
import { AssistantChat } from './AssistantChat'
import { useConversation } from '../hooks/useConversations'
import type { ChatMessage } from '../lib/types'

interface AssistantPanelProps {
  projectName: string
  isOpen: boolean
  onClose: () => void
}

const STORAGE_KEY_PREFIX = 'assistant-conversation-'

function getStoredConversationId(projectName: string): number | null {
  try {
    const stored = localStorage.getItem(`${STORAGE_KEY_PREFIX}${projectName}`)
    if (stored) {
      const data = JSON.parse(stored)
      return data.conversationId || null
    }
  } catch {
    // Invalid stored data, ignore
  }
  return null
}

function setStoredConversationId(projectName: string, conversationId: number | null) {
  const key = `${STORAGE_KEY_PREFIX}${projectName}`
  if (conversationId) {
    localStorage.setItem(key, JSON.stringify({ conversationId }))
  } else {
    localStorage.removeItem(key)
  }
}

export function AssistantPanel({ projectName, isOpen, onClose }: AssistantPanelProps) {
  // Keep a stable ref to onClose so native DOM listeners always call the latest version
  const onCloseRef = useRef(onClose)
  onCloseRef.current = onClose

  // Native DOM click listener on the close button — bypasses React event system entirely
  const closeBtnRef = useRef<HTMLButtonElement>(null)
  useEffect(() => {
    const btn = closeBtnRef.current
    if (!btn || !isOpen) return
    const handleNativeClick = (e: MouseEvent) => {
      e.stopPropagation()
      e.preventDefault()
      onCloseRef.current()
    }
    btn.addEventListener('click', handleNativeClick, true) // capture phase
    return () => btn.removeEventListener('click', handleNativeClick, true)
  }, [isOpen])

  // Capture-phase Escape handler — fires before the textarea can swallow the event
  useEffect(() => {
    if (!isOpen) return
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault()
        e.stopPropagation()
        onCloseRef.current()
      }
    }
    window.addEventListener('keydown', handleEscape, true) // capture phase
    return () => window.removeEventListener('keydown', handleEscape, true)
  }, [isOpen])

  // Load initial conversation ID from localStorage
  const [conversationId, setConversationId] = useState<number | null>(() =>
    getStoredConversationId(projectName)
  )

  // Fetch conversation details when we have an ID
  const { data: conversationDetail, isLoading: isLoadingConversation, error: conversationError } = useConversation(
    projectName,
    conversationId
  )

  // Clear stored conversation ID if it no longer exists (404 error)
  useEffect(() => {
    if (conversationError && conversationId) {
      const message = conversationError.message.toLowerCase()
      // Only clear for 404 errors, not transient network issues
      if (message.includes('not found') || message.includes('404')) {
        console.warn(`Conversation ${conversationId} not found, clearing stored ID`)
        setConversationId(null)
      }
    }
  }, [conversationError, conversationId])

  // Convert API messages to ChatMessage format for the chat component
  const initialMessages: ChatMessage[] | undefined = conversationDetail?.messages.map((msg) => ({
    id: `db-${msg.id}`,
    role: msg.role,
    content: msg.content,
    timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date(),
  }))

  // Persist conversation ID changes to localStorage
  useEffect(() => {
    setStoredConversationId(projectName, conversationId)
  }, [projectName, conversationId])

  // Reset conversation ID when project changes
  useEffect(() => {
    setConversationId(getStoredConversationId(projectName))
  }, [projectName])

  // Handle starting a new chat
  const handleNewChat = useCallback(() => {
    setConversationId(null)
  }, [])

  // Handle selecting a conversation from history
  const handleSelectConversation = useCallback((id: number) => {
    setConversationId(id)
  }, [])

  // Handle when a new conversation is created (from WebSocket)
  const handleConversationCreated = useCallback((id: number) => {
    setConversationId(id)
  }, [])

  // When closed, don't render anything at all — no CSS hide, no off-screen panel.
  // This guarantees the panel disappears regardless of CSS/transition/stacking issues.
  if (!isOpen) return null

  return createPortal(
    <>
      {/* Backdrop - click to close */}
      <div
        className="fixed inset-0 bg-black/20 z-[55]"
        onClick={() => onCloseRef.current()}
        aria-hidden="true"
      />

      {/* Panel */}
      <div
        className="fixed right-0 top-0 bottom-0 z-[60] w-[400px] max-w-[90vw] bg-card border-l border-border flex flex-col shadow-xl"
        role="dialog"
        aria-label="Project Assistant"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-primary text-primary-foreground">
          <div className="flex items-center gap-2">
            <div className="bg-card text-foreground border border-border p-1.5 rounded">
              <Bot size={18} />
            </div>
            <div>
              <h2 className="font-semibold">Project Assistant</h2>
              <p className="text-xs opacity-80 font-mono">{projectName}</p>
            </div>
          </div>
          <button
            ref={closeBtnRef}
            type="button"
            onClick={() => onCloseRef.current()}
            className="size-9 inline-flex items-center justify-center rounded-md text-primary-foreground hover:bg-primary-foreground/20 transition-colors"
            title="Close Assistant (Press A)"
            aria-label="Close Assistant"
          >
            <X size={18} />
          </button>
        </div>

        {/* Chat area */}
        <div className="flex-1 overflow-hidden">
          <AssistantChat
            projectName={projectName}
            conversationId={conversationId}
            initialMessages={initialMessages}
            isLoadingConversation={isLoadingConversation}
            onNewChat={handleNewChat}
            onSelectConversation={handleSelectConversation}
            onConversationCreated={handleConversationCreated}
          />
        </div>
      </div>
    </>,
    document.body
  )
}
