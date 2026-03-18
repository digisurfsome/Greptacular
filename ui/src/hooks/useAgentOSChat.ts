/**
 * useAgentOSChat Hook
 *
 * Manages the WebSocket connection for the interactive Agent OS
 * PRD creation workflow. Handles all message types from the server
 * and provides send functions for client messages.
 */

import { useState, useEffect, useCallback, useRef } from 'react'

// ============================================================================
// Types
// ============================================================================

export interface AgentOSChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  isStreaming?: boolean
}

export interface AgentOSQuestion {
  id: string
  question: string
  type: 'text' | 'choice' | 'multi_choice'
  options?: string[]
  purpose?: string
}

export interface AgentOSChatFeature {
  id: number
  name: string
  description: string
  priority: string
  complexity: string
  category: string
  dependencies: number[]
}

export interface AgentOSChatGap {
  id: number
  type: string
  severity: string
  message: string
  recommendation: string
  confidence: number
  auto_fillable: boolean
  resolved: boolean
}

export interface AgentOSChatHandoffStatus {
  ready: boolean
  missing: string[]
  feature_count: number
  build_order: number[]
  estimated_sessions: number
}

type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error'

interface UseAgentOSChatOptions {
  projectName: string
  onComplete?: () => void
  onError?: (error: string) => void
}

export interface UseAgentOSChatReturn {
  // State
  messages: AgentOSChatMessage[]
  currentStage: string
  stageIndex: number
  totalStages: number
  currentQuestion: AgentOSQuestion | null
  features: AgentOSChatFeature[]
  gaps: AgentOSChatGap[]
  specPreview: { featureId: number; content: string } | null
  handoffStatus: AgentOSChatHandoffStatus | null
  isConnected: boolean
  isThinking: boolean
  connectionStatus: ConnectionStatus

  // Actions
  sendMessage: (content: string) => void
  sendAnswer: (questionId: string, answer: string) => void
  sendApprove: (target: string) => void
  skipStage: () => void
  connect: () => void
  disconnect: () => void
}

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`
}

// ============================================================================
// Hook
// ============================================================================

export function useAgentOSChat({
  projectName,
  onComplete,
  onError,
}: UseAgentOSChatOptions): UseAgentOSChatReturn {
  const [messages, setMessages] = useState<AgentOSChatMessage[]>([])
  const [currentStage, setCurrentStage] = useState('intake')
  const [stageIndex, setStageIndex] = useState(0)
  const [totalStages, setTotalStages] = useState(8)
  const [currentQuestion, setCurrentQuestion] = useState<AgentOSQuestion | null>(null)
  const [features, setFeatures] = useState<AgentOSChatFeature[]>([])
  const [gaps, setGaps] = useState<AgentOSChatGap[]>([])
  const [specPreview, setSpecPreview] = useState<{ featureId: number; content: string } | null>(null)
  const [handoffStatus, setHandoffStatus] = useState<AgentOSChatHandoffStatus | null>(null)
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected')
  const [isThinking, setIsThinking] = useState(false)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttempts = useRef(0)
  const maxReconnectAttempts = 3
  const pingIntervalRef = useRef<number | null>(null)
  const reconnectTimeoutRef = useRef<number | null>(null)

  // Stable callback refs to avoid reconnection loops
  const onCompleteRef = useRef(onComplete)
  const onErrorRef = useRef(onError)
  useEffect(() => { onCompleteRef.current = onComplete }, [onComplete])
  useEffect(() => { onErrorRef.current = onError }, [onError])

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (pingIntervalRef.current) clearInterval(pingIntervalRef.current)
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current)
      if (wsRef.current) wsRef.current.close()
    }
  }, [])

  const handleServerMessage = useCallback((event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data)

      switch (data.type) {
        case 'message': {
          setIsThinking(false)
          setMessages(prev => [
            ...prev,
            {
              id: generateId(),
              role: 'assistant',
              content: data.content || data.message || '',
              timestamp: new Date(),
            },
          ])
          break
        }

        case 'question': {
          setIsThinking(false)
          // Backend sends question data nested under data.question as an object
          const q = data.question
          if (q && typeof q === 'object') {
            setCurrentQuestion({
              id: q.id || generateId(),
              question: q.question || '',
              type: q.type || 'text',
              options: q.options,
              purpose: q.purpose,
            })
          } else {
            // Fallback: flat structure for backward compatibility
            setCurrentQuestion({
              id: data.question_id || generateId(),
              question: (typeof data.question === 'string' ? data.question : '') || '',
              type: data.question_type || 'text',
              options: data.options,
              purpose: data.purpose,
            })
          }
          break
        }

        case 'stage_change': {
          setCurrentStage(data.stage || '')
          setStageIndex(data.index ?? 0)
          if (data.total) setTotalStages(data.total)

          setMessages(prev => [
            ...prev,
            {
              id: generateId(),
              role: 'system',
              content: `Stage: ${data.stage || 'unknown'}`,
              timestamp: new Date(),
            },
          ])
          break
        }

        case 'progress': {
          // Stage-specific progress update (informational)
          break
        }

        case 'features': {
          setFeatures(data.features || [])
          break
        }

        case 'gaps': {
          setGaps(data.gaps || [])
          break
        }

        case 'spec_preview': {
          setSpecPreview({
            featureId: data.feature_id ?? 0,
            content: data.generation_prompt || data.content || '',
          })
          break
        }

        case 'handoff_ready': {
          setHandoffStatus(data.status || data)
          setIsThinking(false)
          // Do not call onComplete here — 'complete' event handles that.
          // Calling it on both handoff_ready and complete would fire it twice.
          break
        }

        case 'complete': {
          setIsThinking(false)
          onCompleteRef.current?.()
          break
        }

        case 'error': {
          setIsThinking(false)
          const errorMsg = data.message || data.content || 'Unknown error'
          onErrorRef.current?.(errorMsg)
          setMessages(prev => [
            ...prev,
            {
              id: generateId(),
              role: 'system',
              content: `Error: ${errorMsg}`,
              timestamp: new Date(),
            },
          ])
          break
        }

        case 'pong':
          break
      }
    } catch (e) {
      console.error('Failed to parse Agent OS WebSocket message:', e)
    }
  }, [])

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    setConnectionStatus('connecting')
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/api/agent-os/ws/${encodeURIComponent(projectName)}`

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setConnectionStatus('connected')
      reconnectAttempts.current = 0

      // Ping every 30s to keep alive
      pingIntervalRef.current = window.setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }))
        }
      }, 30000)
    }

    ws.onclose = (event) => {
      setConnectionStatus('disconnected')
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current)
        pingIntervalRef.current = null
      }

      const isAppError = event.code >= 4000 && event.code <= 4999
      if (!isAppError && reconnectAttempts.current < maxReconnectAttempts) {
        reconnectAttempts.current++
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 10000)
        reconnectTimeoutRef.current = window.setTimeout(connect, delay)
      }
    }

    ws.onerror = () => {
      setConnectionStatus('error')
      onErrorRef.current?.('WebSocket connection error')
    }

    ws.onmessage = handleServerMessage
  }, [projectName, handleServerMessage])

  const disconnect = useCallback(() => {
    reconnectAttempts.current = maxReconnectAttempts
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current)
      pingIntervalRef.current = null
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setConnectionStatus('disconnected')
  }, [])

  const sendMessage = useCallback((content: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return

    setMessages(prev => [
      ...prev,
      { id: generateId(), role: 'user', content, timestamp: new Date() },
    ])
    setCurrentQuestion(null)
    setIsThinking(true)
    wsRef.current.send(JSON.stringify({ type: 'message', content }))
  }, [])

  const sendAnswer = useCallback((questionId: string, answer: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return

    setMessages(prev => [
      ...prev,
      { id: generateId(), role: 'user', content: answer, timestamp: new Date() },
    ])
    setCurrentQuestion(null)
    setIsThinking(true)
    wsRef.current.send(JSON.stringify({ type: 'answer', question_id: questionId, answer }))
  }, [])

  const sendApprove = useCallback((target: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return

    setMessages(prev => [
      ...prev,
      { id: generateId(), role: 'user', content: `Approved: ${target}`, timestamp: new Date() },
    ])
    setIsThinking(true)
    wsRef.current.send(JSON.stringify({ type: 'approve', target }))
  }, [])

  const skipStage = useCallback(() => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return
    wsRef.current.send(JSON.stringify({ type: 'skip_stage' }))
  }, [])

  return {
    messages,
    currentStage,
    stageIndex,
    totalStages,
    currentQuestion,
    features,
    gaps,
    specPreview,
    handoffStatus,
    isConnected: connectionStatus === 'connected',
    isThinking,
    connectionStatus,
    sendMessage,
    sendAnswer,
    sendApprove,
    skipStage,
    connect,
    disconnect,
  }
}
