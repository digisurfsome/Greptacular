/**
 * useDunkStack Hook
 *
 * Manages DunkStack state: WebSocket connection for real-time updates,
 * comms file polling, token tracking, safety status, and session control.
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import {
  dunkstackReadToHuman,
  dunkstackReadFromHuman,
  dunkstackWriteFromHuman,
  dunkstackReadControl,
  dunkstackUpdateControl,
  dunkstackGetTokenState,
  dunkstackReadConfig,
  dunkstackSaveBridge,
  dunkstackStartAgent,
  dunkstackStopAgent,
  dunkstackSendToAgent,
  type DunkStackSafetyStatus,
  type DunkStackTokenState,
  type DunkStackAgentStatus,
} from '@/lib/api'

// ============================================================================
// Types
// ============================================================================

export interface CommsEntry {
  id: string
  sender: 'human' | 'agent' | 'system'
  content: string
  title: string
  timestamp: string
}

export interface AgentState {
  running: boolean
  streaming: boolean
}

export interface AgentEventEntry {
  id: string
  type: string
  content?: string
  tool?: string
  input?: unknown
  output?: string
  is_error?: boolean
  usage?: Record<string, number>
  status?: string
  timestamp: string
}

export interface DunkStackConfig {
  mode?: { type?: string; model_family?: string }
  api?: { key_env_var?: string; model_id?: string; max_tokens_output?: number }
  context_management?: Record<string, unknown>
  session?: Record<string, unknown>
  safety?: {
    warning_threshold_pct?: number
    handoff_threshold_pct?: number
    hard_stop_threshold_pct?: number
    post_stop_review?: boolean
    model_limit?: number
  }
}

export interface UseDunkStackReturn {
  // Comms
  commsLog: CommsEntry[]
  sendMessage: (content: string, title?: string) => Promise<void>

  // Session control
  controlMode: string
  setControlMode: (mode: string, message?: string) => Promise<void>

  // Token tracking
  tokenState: DunkStackTokenState | null
  resetTokens: () => void

  // Safety
  safetyStatus: DunkStackSafetyStatus | null

  // Config
  config: DunkStackConfig | null

  // Bridge
  saveBridge: (data: {
    reason?: string
    current_task?: string
    progress?: string
    next_steps?: string
    open_questions?: string
  }) => Promise<void>

  // Coding Agent
  agentStatus: DunkStackAgentStatus | null
  startAgent: (projectName: string, modelId?: string, contextWindow?: number) => Promise<void>
  stopAgent: (projectName: string) => Promise<void>
  sendToAgent: (projectName: string, message: string) => Promise<Array<Record<string, unknown>>>
  agentStarting: boolean
  agentEvents: AgentEventEntry[]
  clearAgentEvents: () => void

  // Connection
  connected: boolean
  loading: boolean
}

// ============================================================================
// Parse markdown comms files into structured entries
// ============================================================================

function parseCommsFile(content: string, sender: 'human' | 'agent'): CommsEntry[] {
  if (!content) return []

  const entries: CommsEntry[] = []
  // Match ## [timestamp] Title or ## [timestamp] Category - Title
  const pattern = /^## \[([^\]]+)\]\s*(.+?)$/gm
  let match: RegExpExecArray | null
  const positions: Array<{ index: number; timestamp: string; title: string }> = []

  while ((match = pattern.exec(content)) !== null) {
    positions.push({ index: match.index, timestamp: match[1], title: match[2] })
  }

  for (let i = 0; i < positions.length; i++) {
    const start = positions[i].index
    const headerEnd = content.indexOf('\n', start)
    const end = i + 1 < positions.length ? positions[i + 1].index : content.length
    const body = content.slice(headerEnd + 1, end).trim()

    entries.push({
      id: `${sender}-${positions[i].timestamp}-${i}`,
      sender,
      content: body,
      title: positions[i].title,
      timestamp: positions[i].timestamp,
    })
  }

  return entries
}

// ============================================================================
// Hook
// ============================================================================

export function useDunkStack(): UseDunkStackReturn {
  const [commsLog, setCommsLog] = useState<CommsEntry[]>([])
  const [controlMode, setControlModeState] = useState('idle')
  const [tokenState, setTokenState] = useState<DunkStackTokenState | null>(null)
  const [safetyStatus, setSafetyStatus] = useState<DunkStackSafetyStatus | null>(null)
  const [config, setConfig] = useState<DunkStackConfig | null>(null)
  const [connected, setConnected] = useState(false)
  const [loading, setLoading] = useState(true)
  const [agentStatus, setAgentStatus] = useState<DunkStackAgentStatus | null>(null)
  const [agentStarting, setAgentStarting] = useState(false)
  const [agentEvents, setAgentEvents] = useState<AgentEventEntry[]>([])
  const wsRef = useRef<WebSocket | null>(null)
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Load initial data on mount
  useEffect(() => {
    async function loadInitial() {
      try {
        const [toHuman, fromHuman, control, tokens, cfg] = await Promise.all([
          dunkstackReadToHuman(),
          dunkstackReadFromHuman(),
          dunkstackReadControl(),
          dunkstackGetTokenState(),
          dunkstackReadConfig(),
        ])

        // Parse comms into combined log
        const agentEntries = parseCommsFile(toHuman.content, 'agent')
        const humanEntries = parseCommsFile(fromHuman.content, 'human')
        const combined = [...agentEntries, ...humanEntries].sort(
          (a, b) => a.timestamp.localeCompare(b.timestamp)
        )
        setCommsLog(combined)

        setControlModeState(control.mode)
        setTokenState(tokens)
        setSafetyStatus(tokens.safety)
        setConfig(cfg.config as DunkStackConfig)
      } catch (e) {
        // Server may not be running - that's ok for initial load
        console.debug('DunkStack initial load failed:', e)
      } finally {
        setLoading(false)
      }
    }

    loadInitial()
  }, [])

  // WebSocket connection for real-time updates
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/api/dunkstack/ws`
    let ws: WebSocket

    function connect() {
      ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        setConnected(true)
        wsRef.current = ws
      }

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data)

          switch (msg.type) {
            case 'init':
              if (msg.token_state) {
                setTokenState(prev => prev ? { ...prev, ...msg.token_state } : msg.token_state)
              }
              break

            case 'comms_update':
              setCommsLog(prev => [
                ...prev,
                {
                  id: `${msg.channel}-${msg.timestamp}-${Date.now()}`,
                  sender: msg.channel === 'from_human' ? 'human' : 'agent',
                  content: msg.content,
                  title: msg.title,
                  timestamp: msg.timestamp,
                },
              ])
              break

            case 'control_update':
              setControlModeState(msg.mode)
              break

            case 'token_update':
              setTokenState(prev => ({
                cumulative: msg.cumulative,
                model_limit: prev?.model_limit ?? 200000,
                mode: prev?.mode ?? 'subscription',
                usage_percent: msg.usage_percent,
                entries_count: (prev?.entries_count ?? 0) + 1,
                safety: msg.safety,
              }))
              setSafetyStatus(msg.safety)
              break

            case 'token_reset':
              setTokenState(prev => ({
                cumulative: { input_tokens: 0, output_tokens: 0, cache_read_tokens: 0, cache_creation_tokens: 0, total_cost_usd: 0, api_calls: 0 },
                model_limit: prev?.model_limit ?? 200000,
                mode: prev?.mode ?? 'subscription',
                usage_percent: 0,
                entries_count: 0,
                safety: { tier: 0, label: 'OK', color: 'green', message: 'Operating normally.' },
              }))
              setSafetyStatus({ tier: 0, label: 'OK', color: 'green', message: 'Operating normally.' })
              break

            case 'config_update':
              setConfig(msg.config as DunkStackConfig)
              break

            case 'bridge_saved':
              setCommsLog(prev => [
                ...prev,
                {
                  id: `system-bridge-${msg.timestamp}`,
                  sender: 'system',
                  content: 'Bridge state saved.',
                  title: 'Bridge Save',
                  timestamp: msg.timestamp,
                },
              ])
              break

            case 'agent_event':
            case 'text':
            case 'tool_call':
            case 'tool_result':
            case 'result':
            case 'response_done':
            case 'error':
            case 'agent_status':
              // Real-time agent updates from the backend.
              // Note: the backend broadcasts {"type": "agent_event", **event}
              // but **event has its own 'type' field that overwrites "agent_event",
              // so we receive "text", "tool_call", etc. directly.
              if (msg.status) {
                setAgentStatus(prev => ({ ...prev, status: msg.status, error: msg.error || null }))
              }
              // Accumulate all agent events for the split-screen API call view
              setAgentEvents(prev => [...prev, {
                id: `ae-${Date.now()}-${prev.length}`,
                type: msg.type,
                content: msg.content,
                tool: msg.tool,
                input: msg.input,
                output: msg.output,
                is_error: msg.is_error,
                usage: msg.usage,
                status: msg.status,
                timestamp: new Date().toISOString(),
              }])
              break

            case 'pong':
              break
          }
        } catch {
          // Ignore parse errors
        }
      }

      ws.onclose = () => {
        setConnected(false)
        wsRef.current = null
        // Reconnect after 3s
        setTimeout(connect, 3000)
      }

      ws.onerror = () => {
        ws.close()
      }
    }

    connect()

    return () => {
      ws?.close()
    }
  }, [])

  // Poll comms files periodically as a fallback (every 10s)
  useEffect(() => {
    pollIntervalRef.current = setInterval(async () => {
      try {
        const [toHuman, fromHuman] = await Promise.all([
          dunkstackReadToHuman(),
          dunkstackReadFromHuman(),
        ])
        const agentEntries = parseCommsFile(toHuman.content, 'agent')
        const humanEntries = parseCommsFile(fromHuman.content, 'human')
        const combined = [...agentEntries, ...humanEntries].sort(
          (a, b) => a.timestamp.localeCompare(b.timestamp)
        )
        setCommsLog(combined)
      } catch {
        // Ignore
      }
    }, 10000)

    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current)
    }
  }, [])

  // Send message (human → agent)
  const sendMessage = useCallback(async (content: string, title?: string) => {
    await dunkstackWriteFromHuman(content, title)
  }, [])

  // Update control mode
  const setControlMode = useCallback(async (mode: string, message?: string) => {
    await dunkstackUpdateControl(mode, message)
    setControlModeState(mode)
  }, [])

  // Save bridge
  const saveBridge = useCallback(async (data: {
    reason?: string
    current_task?: string
    progress?: string
    next_steps?: string
    open_questions?: string
  }) => {
    await dunkstackSaveBridge(data)
  }, [])

  // Reset tokens
  const resetTokens = useCallback(() => {
    fetch('/api/dunkstack/tokens/reset', { method: 'POST' })
  }, [])

  // ── Coding Agent ──

  const startAgent = useCallback(async (projectName: string, modelId?: string, contextWindow?: number) => {
    setAgentStarting(true)
    setAgentEvents([]) // Clear events on new start
    try {
      const result = await dunkstackStartAgent(projectName, modelId, contextWindow)
      setAgentStatus(result)
      // Accumulate events from the start response
      const events = [...(result.startup_events || []), ...(result.response_events || [])] as Array<Record<string, unknown>>
      if (events.length) {
        setAgentEvents(events.map((e, i) => ({
          id: `start-${Date.now()}-${i}`,
          type: String(e.type || 'text'),
          content: e.content as string | undefined,
          tool: e.tool as string | undefined,
          input: e.input,
          output: e.output as string | undefined,
          is_error: e.is_error as boolean | undefined,
          usage: e.usage as Record<string, number> | undefined,
          status: e.status as string | undefined,
          timestamp: new Date().toISOString(),
        })))
      }
    } catch (e) {
      setAgentStatus({ status: 'error', error: String(e) })
    } finally {
      setAgentStarting(false)
    }
  }, [])

  const clearAgentEvents = useCallback(() => setAgentEvents([]), [])

  const stopAgent = useCallback(async (projectName: string) => {
    try {
      await dunkstackStopAgent(projectName)
      setAgentStatus({ status: 'stopped' })
    } catch (e) {
      console.error('Failed to stop agent:', e)
    }
  }, [])

  const sendToAgent = useCallback(async (projectName: string, message: string) => {
    try {
      const result = await dunkstackSendToAgent(projectName, message)
      const events = result.events || []
      // Accumulate events from the HTTP response (WebSocket may also deliver
      // them, but duplicates are harmless in the log)
      if (events.length) {
        setAgentEvents(prev => [...prev, ...events.map((e, i) => ({
          id: `send-${Date.now()}-${i}`,
          type: String(e.type || 'text'),
          content: e.content as string | undefined,
          tool: e.tool as string | undefined,
          input: e.input,
          output: e.output as string | undefined,
          is_error: e.is_error as boolean | undefined,
          usage: e.usage as Record<string, number> | undefined,
          status: e.status as string | undefined,
          timestamp: new Date().toISOString(),
        }))])
      }
      return events
    } catch (e) {
      console.error('Failed to send to agent:', e)
      return []
    }
  }, [])

  // Handle agent_event from WebSocket (update status in real-time)
  // This is already handled in the onmessage handler above — we just need
  // to add the agent_event case to the switch statement.

  return {
    commsLog,
    sendMessage,
    controlMode,
    setControlMode,
    tokenState,
    resetTokens,
    safetyStatus,
    config,
    saveBridge,
    agentStatus,
    startAgent,
    stopAgent,
    sendToAgent,
    agentStarting,
    agentEvents,
    clearAgentEvents,
    connected,
    loading,
  }
}
