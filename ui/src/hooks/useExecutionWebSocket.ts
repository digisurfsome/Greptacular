/**
 * WebSocket Hook for YT Strategy Lab Execution Viewer
 *
 * Connects to /ws/execution/{session_id} and handles real-time events
 * from the computer-use agent: status changes, agent actions, step
 * transitions, screenshots, and chat messages.
 */

import { useEffect, useRef, useState, useCallback } from 'react'
import type {
  YTExecutionEvent,
  YTExecutionLogEntry,
  YTStrategyStepStatus,
  YTExecutionStatus,
} from '../lib/types'

interface StepState {
  stepId: string
  status: YTStrategyStepStatus
}

interface ExecutionWebSocketState {
  status: YTExecutionStatus
  currentStep: number
  totalSteps: number
  logs: YTExecutionLogEntry[]
  stepStates: StepState[]
  isConnected: boolean
  error: string | null
}

const MAX_LOGS = 500

export function useExecutionWebSocket(sessionId: string | null) {
  const [state, setState] = useState<ExecutionWebSocketState>({
    status: 'idle',
    currentStep: 0,
    totalSteps: 0,
    logs: [],
    stepStates: [],
    isConnected: false,
    error: null,
  })

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const reconnectAttempts = useRef(0)
  const logIdCounterRef = useRef(0)

  const addLog = useCallback(
    (text: string, type: YTExecutionLogEntry['type'], timestamp?: string) => {
      const id = `log-${++logIdCounterRef.current}`
      const entry: YTExecutionLogEntry = {
        id,
        text,
        type,
        timestamp: timestamp ?? new Date().toISOString(),
      }
      setState((prev) => ({
        ...prev,
        logs: [...prev.logs.slice(-MAX_LOGS + 1), entry],
      }))
    },
    [],
  )

  // Use a ref to always have the latest addLog without triggering reconnects
  const addLogRef = useRef(addLog)
  addLogRef.current = addLog

  useEffect(() => {
    if (!sessionId) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/ws/execution/${encodeURIComponent(sessionId)}`

    function connect() {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        reconnectAttempts.current = 0
        setState((prev) => ({ ...prev, isConnected: true, error: null }))
      }

      ws.onmessage = (event) => {
        try {
          const msg: YTExecutionEvent = JSON.parse(event.data)
          const ts = msg.timestamp

          switch (msg.type) {
            case 'status_change':
              if (msg.data.status) {
                setState((prev) => ({ ...prev, status: msg.data.status! }))
                addLogRef.current(`Status: ${msg.data.status}`, 'action', ts)
              }
              break

            case 'agent_action':
              if (msg.data.description) {
                addLogRef.current(msg.data.description, 'action', ts)
              }
              break

            case 'agent_thinking':
              if (msg.data.content) {
                addLogRef.current(msg.data.content, 'thinking', ts)
              }
              break

            case 'step_change':
              if (msg.data.step_id && msg.data.step_status) {
                setState((prev) => {
                  let found = false
                  const updated = prev.stepStates.map((s) => {
                    if (s.stepId === msg.data.step_id) {
                      found = true
                      return { ...s, status: msg.data.step_status! }
                    }
                    return s
                  })
                  if (!found) {
                    updated.push({
                      stepId: msg.data.step_id!,
                      status: msg.data.step_status!,
                    })
                  }
                  return {
                    ...prev,
                    stepStates: updated,
                    currentStep: msg.data.current_step ?? prev.currentStep,
                    totalSteps: msg.data.total_steps ?? prev.totalSteps,
                  }
                })
                addLogRef.current(
                  `Step "${msg.data.step_id}" \u2192 ${msg.data.step_status}`,
                  'success',
                  ts,
                )
              }
              break

            case 'screenshot':
              // Screenshots are stored but not displayed in the log
              break

            case 'user_message':
              if (msg.data.content) {
                addLogRef.current(`YOU: ${msg.data.content}`, 'user', ts)
              }
              break

            case 'agent_response':
              if (msg.data.content) {
                addLogRef.current(`AGENT: ${msg.data.content}`, 'agent', ts)
              }
              break

            case 'error':
              if (msg.data.message) {
                setState((prev) => ({
                  ...prev,
                  status: 'error',
                  error: msg.data.message ?? null,
                }))
                addLogRef.current(msg.data.message, 'error', ts)
              }
              break
          }
        } catch {
          // Ignore malformed messages
        }
      }

      ws.onclose = () => {
        setState((prev) => ({ ...prev, isConnected: false }))
        wsRef.current = null

        // Reconnect with backoff (max 5 attempts)
        if (reconnectAttempts.current < 5) {
          const delay = Math.min(1000 * 2 ** reconnectAttempts.current, 16000)
          reconnectAttempts.current += 1
          reconnectTimeoutRef.current = setTimeout(connect, delay)
        }
      }

      ws.onerror = () => {
        // onclose will fire after onerror
      }
    }

    connect()

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [sessionId])

  const clearLogs = useCallback(() => {
    setState((prev) => ({ ...prev, logs: [] }))
  }, [])

  const initStepStates = useCallback(
    (stepIds: string[]) => {
      setState((prev) => ({
        ...prev,
        stepStates: stepIds.map((id) => ({ stepId: id, status: 'pending' as const })),
        totalSteps: stepIds.length,
      }))
    },
    [],
  )

  return {
    ...state,
    clearLogs,
    initStepStates,
  }
}
