/**
 * ArenaChatPage - Lightweight chat view designed to run inside an Arena iframe.
 *
 * Listens for postMessage events from the parent ArenaPage, connects to the
 * workspace WebSocket via useWorkspaceChat, and displays a simple scrollable
 * chat. Each iframe instance runs its own independent WebSocket session.
 */

import { useState, useEffect, useRef } from 'react'
import { useWorkspaceChat } from '../hooks/useWorkspaceChat'
import type { ChatMessage } from '../lib/types'

/** Message shape sent from ArenaPage parent via postMessage. */
interface ArenaPostMessage {
  type: 'arena_message'
  content: string
  model: string
  provider: string
}

/** Status update sent from iframe to parent via postMessage. */
interface ArenaStatusMessage {
  type: 'arena_status'
  panelId: string
  status: 'streaming' | 'done' | 'error' | 'connected' | 'disconnected'
}

function getPanelIdFromHash(): string {
  const match = window.location.hash.match(/[?&]panel=([^&]+)/)
  return match ? match[1] : 'unknown'
}

function postStatusToParent(panelId: string, status: ArenaStatusMessage['status']) {
  if (window.parent !== window) {
    window.parent.postMessage({ type: 'arena_status', panelId, status } satisfies ArenaStatusMessage, '*')
  }
}

export function ArenaChatPage(): React.JSX.Element {
  const panelId = getPanelIdFromHash()
  const [activeModel, setActiveModel] = useState<string | null>(null)
  const [activeProvider, setActiveProvider] = useState<string | null>(null)
  const [started, setStarted] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const prevLoadingRef = useRef(false)

  const chat = useWorkspaceChat({
    onError: (err) => {
      console.error(`[Arena Panel ${panelId}] Error:`, err)
      postStatusToParent(panelId, 'error')
    },
  })

  // Notify parent of connection status changes
  useEffect(() => {
    if (chat.connectionStatus === 'connected') {
      postStatusToParent(panelId, 'connected')
    } else if (chat.connectionStatus === 'disconnected' || chat.connectionStatus === 'error') {
      postStatusToParent(panelId, 'disconnected')
    }
  }, [chat.connectionStatus, panelId])

  // Notify parent when streaming starts/stops
  useEffect(() => {
    if (chat.isLoading && !prevLoadingRef.current) {
      postStatusToParent(panelId, 'streaming')
    } else if (!chat.isLoading && prevLoadingRef.current) {
      postStatusToParent(panelId, 'done')
    }
    prevLoadingRef.current = chat.isLoading
  }, [chat.isLoading, panelId])

  // Listen for messages from parent
  useEffect(() => {
    const handler = (event: MessageEvent) => {
      const data = event.data as ArenaPostMessage
      if (data?.type !== 'arena_message') return

      setActiveModel(data.model)
      setActiveProvider(data.provider)

      if (!started) {
        // First message: start the session with the specified model/provider
        setStarted(true)
        chat.start(null, undefined, '200k', undefined, data.model, data.provider)
        // Queue the message to send after session is ready
        const waitAndSend = () => {
          setTimeout(() => {
            chat.sendMessage(data.content)
          }, 2000)
        }
        waitAndSend()
      } else {
        chat.sendMessage(data.content)
      }
    }

    window.addEventListener('message', handler)
    return () => window.removeEventListener('message', handler)
  }, [started, chat])

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chat.messages])

  const modelLabel = activeModel || 'Waiting...'

  return (
    <div className="flex flex-col h-screen bg-[#1a1a2e] text-gray-100 overflow-hidden">
      {/* Model label header */}
      <div className="shrink-0 px-3 py-2 border-b border-white/10 bg-[#12122a] flex items-center gap-2">
        <div className="w-2 h-2 rounded-full shrink-0" style={{
          backgroundColor: chat.connectionStatus === 'connected'
            ? '#22d3ee'
            : chat.connectionStatus === 'connecting'
              ? '#facc15'
              : '#ef4444'
        }} />
        <span className="text-xs font-mono font-bold text-cyan-300 truncate">
          {modelLabel}
        </span>
        {activeProvider && (
          <span className="text-[10px] text-white/40 font-mono">
            ({activeProvider})
          </span>
        )}
        {chat.isLoading && (
          <span className="ml-auto text-[10px] text-yellow-400 animate-pulse">
            streaming...
          </span>
        )}
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3">
        {chat.messages.length === 0 && !started && (
          <div className="flex items-center justify-center h-full text-white/30 text-sm">
            Waiting for a question from Arena...
          </div>
        )}
        {chat.messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        <div ref={messagesEndRef} />
      </div>
    </div>
  )
}

function MessageBubble({ message }: { message: ChatMessage }): React.JSX.Element {
  if (message.role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-lg px-3 py-2 bg-cyan-900/40 border border-cyan-500/20 text-sm whitespace-pre-wrap">
          {message.content}
        </div>
      </div>
    )
  }

  if (message.role === 'system') {
    return (
      <div className="text-[11px] text-white/30 font-mono px-1 py-0.5 truncate">
        {message.content}
      </div>
    )
  }

  // Assistant message
  return (
    <div className="flex justify-start">
      <div className="max-w-[95%] rounded-lg px-3 py-2 bg-white/5 border border-white/10 text-sm whitespace-pre-wrap">
        {message.content}
        {message.isStreaming && (
          <span className="inline-block w-1.5 h-4 bg-cyan-400 ml-0.5 animate-pulse" />
        )}
      </div>
    </div>
  )
}
