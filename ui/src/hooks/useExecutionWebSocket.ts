/**
 * WebSocket Hook for YT Strategy Lab Execution Viewer
 *
 * Connects to /ws/execution/{session_id} and handles real-time events
 * from the computer-use agent: status changes, agent actions, step
 * transitions, screenshots, and chat messages.
 */

import { useEffect, useRef, useState, useCallback } from 'react'
import type {
  YTExecutionStatus,
  YTExecutionEvent,
  YTExecutionLogEntry,
  YTStrategyStepStatus,
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

let logIdCounter = 0
function nextLogId(): string {
  return `log-${++logIdCounter}`
}

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

  const addLog = useCallback(
    (text: string, type: YTExecutionLogEntry['type'], timestamp?: string) => {
      const entry: YTExecutionLogEntry = {
        id: nextLogId(),
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

  const connect = useCallback(() => {
    if (!sessionId) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/ws/execution/${encodeURIComponent(sessionId)}`

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
              addLog(`Status: ${msg.data.status}`, 'action', ts)
            }
            break

          case 'agent_action':
            if (msg.data.description) {
              addLog(msg.data.description, 'action', ts)
            }
            break

          case 'agent_thinking':
            if (msg.data.content) {
              addLog(msg.data.content, 'thinking', ts)
            }
            break

          case 'step_change':
            if (msg.data.step_id && msg.data.step_status) {
              setState((prev) => {
                const updated = prev.stepStates.map((s) =>
                  s.stepId === msg.data.step_id
                    ? { ...s, status: msg.data.step_status! }
                    : s,
                )
                // If step_id not in list, add it
                if (!updated.find((s) => s.stepId === msg.data.step_id)) {
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
              addLog(
                `Step "${msg.data.step_id}" → ${msg.data.step_status}`,
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
              addLog(`YOU: ${msg.data.content}`, 'user', ts)
            }
            break

          case 'agent_response':
            if (msg.data.content) {
              addLog(`AGENT: ${msg.data.content}`, 'agent', ts)
            }
            break

          case 'error':
            if (msg.data.message) {
              setState((prev) => ({
                ...prev,
                status: 'error',
                error: msg.data.message ?? null,
              }))
              addLog(msg.data.message, 'error', ts)
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
  }, [sessionId, addLog])

  useEffect(() => {
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
  }, [connect])

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
