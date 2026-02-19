/**
 * Hook for managing the AI Design Guide WebSocket connection.
 *
 * Connects to the design guide WebSocket endpoint and handles:
 * - Sending/receiving chat messages with streaming text
 * - Receiving structured actions from the AI (style changes, tab switches, etc.)
 * - Sending context updates about current selections
 * - Automatic keepalive pings and reconnection with exponential backoff
 */

import { useState, useCallback, useRef, useEffect } from 'react'
import type { ChatMessage, DesignGuideAction, DesignGuideContext, DesignGuideMessage } from '../lib/types'

type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error'

interface UseDesignGuideOptions {
  onAction?: (action: DesignGuideAction) => void
  onError?: (error: string) => void
}

interface UseDesignGuideReturn {
  messages: ChatMessage[]
  isLoading: boolean
  connectionStatus: ConnectionStatus
  start: (context: DesignGuideContext) => void
  sendMessage: (content: string, context?: DesignGuideContext) => void
  disconnect: () => void
  clearMessages: () => void
}

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`
}

export function useDesignGuide({
  onAction,
  onError,
}: UseDesignGuideOptions = {}): UseDesignGuideReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected')

  const wsRef = useRef<WebSocket | null>(null)
  const currentAssistantMessageRef = useRef<string | null>(null)
  const reconnectAttempts = useRef(0)
  const maxReconnectAttempts = 3
  const pingIntervalRef = useRef<number | null>(null)
  const reconnectTimeoutRef = useRef<number | null>(null)
  const checkAndSendTimeoutRef = useRef<number | null>(null)
  const manuallyDisconnectedRef = useRef(false)

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current)
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (checkAndSendTimeoutRef.current) {
        clearTimeout(checkAndSendTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
      currentAssistantMessageRef.current = null
    }
  }, [])

  const connect = useCallback(() => {
    // Don't reconnect if manually disconnected
    if (manuallyDisconnectedRef.current) {
      return
    }

    // Prevent multiple connection attempts
    if (
      wsRef.current?.readyState === WebSocket.OPEN ||
      wsRef.current?.readyState === WebSocket.CONNECTING
    ) {
      return
    }

    setConnectionStatus('connecting')

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/api/design-guide/ws`

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setConnectionStatus('connected')
      reconnectAttempts.current = 0

      // Start ping interval to keep connection alive
      pingIntervalRef.current = window.setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }))
        }
      }, 30000)
    }

    ws.onclose = (event) => {
      setConnectionStatus('disconnected')
      setIsLoading(false)
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current)
        pingIntervalRef.current = null
      }

      // Don't retry on application-level errors (4xxx codes won't resolve on retry)
      const isAppError = event.code >= 4000 && event.code <= 4999

      // Attempt reconnection if not intentionally closed
      if (
        !manuallyDisconnectedRef.current &&
        !isAppError &&
        reconnectAttempts.current < maxReconnectAttempts
      ) {
        reconnectAttempts.current++
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 10000)
        reconnectTimeoutRef.current = window.setTimeout(connect, delay)
      }
    }

    ws.onerror = () => {
      setConnectionStatus('error')
      setIsLoading(false)
      onError?.('WebSocket connection error')
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as DesignGuideMessage

        switch (data.type) {
          case 'text': {
            // Append text to current assistant message or create new one
            setMessages((prev) => {
              const lastMessage = prev[prev.length - 1]
              if (lastMessage?.role === 'assistant' && lastMessage.isStreaming) {
                // Append to existing streaming message
                return [
                  ...prev.slice(0, -1),
                  {
                    ...lastMessage,
                    content: lastMessage.content + (data.content ?? ''),
                  },
                ]
              } else {
                // Create new assistant message
                currentAssistantMessageRef.current = generateId()
                return [
                  ...prev,
                  {
                    id: currentAssistantMessageRef.current,
                    role: 'assistant',
                    content: data.content ?? '',
                    timestamp: new Date(),
                    isStreaming: true,
                  },
                ]
              }
            })
            break
          }

          case 'greeting': {
            // Initial greeting from the AI -- treat like a text message
            currentAssistantMessageRef.current = generateId()
            setMessages((prev) => [
              ...prev,
              {
                id: currentAssistantMessageRef.current!,
                role: 'assistant',
                content: data.content ?? '',
                timestamp: new Date(),
                isStreaming: false,
              },
            ])
            break
          }

          case 'action': {
            if (data.action) {
              onAction?.(data.action)
            }
            break
          }

          case 'response_done': {
            // Response complete -- hide loading indicator and mark message as done
            setIsLoading(false)
            currentAssistantMessageRef.current = null

            // Mark current message as done streaming
            setMessages((prev) => {
              const lastMessage = prev[prev.length - 1]
              if (lastMessage?.role === 'assistant' && lastMessage.isStreaming) {
                return [
                  ...prev.slice(0, -1),
                  { ...lastMessage, isStreaming: false },
                ]
              }
              return prev
            })
            break
          }

          case 'error': {
            setIsLoading(false)
            onError?.(data.content ?? 'Unknown error')

            // Add error as system message
            setMessages((prev) => [
              ...prev,
              {
                id: generateId(),
                role: 'system',
                content: `Error: ${data.content ?? 'Unknown error'}`,
                timestamp: new Date(),
              },
            ])
            break
          }

          case 'pong': {
            // Keep-alive response, nothing to do
            break
          }
        }
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    }
  }, [onAction, onError])

  const start = useCallback((context: DesignGuideContext) => {
    manuallyDisconnectedRef.current = false

    // Clear any pending check timeout from previous call
    if (checkAndSendTimeoutRef.current) {
      clearTimeout(checkAndSendTimeoutRef.current)
      checkAndSendTimeoutRef.current = null
    }

    connect()

    // Wait for connection then send start message with initial context
    let attempts = 0
    const maxAttempts = 50 // 5 seconds max (50 * 100ms)
    const checkAndSend = () => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        checkAndSendTimeoutRef.current = null
        setIsLoading(true)
        wsRef.current.send(JSON.stringify({ type: 'start', context }))
      } else if (wsRef.current?.readyState === WebSocket.CONNECTING) {
        if (attempts++ < maxAttempts) {
          checkAndSendTimeoutRef.current = window.setTimeout(checkAndSend, 100)
        } else {
          checkAndSendTimeoutRef.current = null
          onError?.('Connection timeout')
          setIsLoading(false)
        }
      } else {
        checkAndSendTimeoutRef.current = null
      }
    }

    checkAndSendTimeoutRef.current = window.setTimeout(checkAndSend, 100)
  }, [connect, onError])

  const sendMessage = useCallback((content: string, context?: DesignGuideContext) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      onError?.('Not connected')
      return
    }

    // Add user message to chat
    setMessages((prev) => [
      ...prev,
      {
        id: generateId(),
        role: 'user',
        content,
        timestamp: new Date(),
      },
    ])

    setIsLoading(true)

    // Send to server with optional context update
    wsRef.current.send(
      JSON.stringify({
        type: 'message',
        content,
        ...(context ? { context } : {}),
      }),
    )
  }, [onError])

  const disconnect = useCallback(() => {
    manuallyDisconnectedRef.current = true
    reconnectAttempts.current = maxReconnectAttempts // Prevent reconnection
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current)
      pingIntervalRef.current = null
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    if (checkAndSendTimeoutRef.current) {
      clearTimeout(checkAndSendTimeoutRef.current)
      checkAndSendTimeoutRef.current = null
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setConnectionStatus('disconnected')
    setIsLoading(false)
  }, [])

  const clearMessages = useCallback(() => {
    setMessages([])
  }, [])

  return {
    messages,
    isLoading,
    connectionStatus,
    start,
    sendMessage,
    disconnect,
    clearMessages,
  }
}
