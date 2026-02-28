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
  type DunkStackSafetyStatus,
  type DunkStackTokenState,
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

export interface AgentState {
  sessionId: string | null
  running: boolean
  streaming: boolean
  modelId: string
  contextMode: string
}

export interface UseDunkStackReturn {
  // Comms
  commsLog: CommsEntry[]
  sendMessage: (content: string, title?: string) => Promise<void>

  // Agent
  agentState: AgentState
  startAgent: (opts: {
    modelId: string
    contextMode: string
    workingDirectory?: string
    projectName?: string
    effort?: string
  }) => void
  sendAgentMessage: (content: string) => void
  stopAgent: () => void
  agentMessages: CommsEntry[]

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
  const wsRef = useRef<WebSocket | null>(null)
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Agent state
  const [agentState, setAgentState] = useState<AgentState>({
    sessionId: null,
    running: false,
    streaming: false,
    modelId: 'claude-opus-4-6',
    contextMode: '1m',
  })
  const [agentMessages, setAgentMessages] = useState<CommsEntry[]>([])
  // Accumulator for streaming text chunks
  const streamingTextRef = useRef<string>('')

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

            // Agent session events
            case 'agent_started':
              setAgentState(prev => ({
                ...prev,
                sessionId: msg.session_id,
                running: true,
                streaming: false,
                modelId: msg.model_id || prev.modelId,
                contextMode: msg.context_mode || prev.contextMode,
              }))
              break

            case 'agent_stopped':
              setAgentState(prev => ({
                ...prev,
                sessionId: null,
                running: false,
                streaming: false,
              }))
              break

            case 'text': {
              // Agent text response chunk — accumulate and update last message
              const text = msg.content || ''
              streamingTextRef.current += text
              const accumulated = streamingTextRef.current
              setAgentState(prev => ({ ...prev, streaming: true }))
              setAgentMessages(prev => {
                const last = prev[prev.length - 1]
                if (last && last.sender === 'agent' && last.id.startsWith('agent-streaming-')) {
                  // Update existing streaming message
                  return [
                    ...prev.slice(0, -1),
                    { ...last, content: accumulated },
                  ]
                }
                // Create new streaming message
                return [
                  ...prev,
                  {
                    id: `agent-streaming-${Date.now()}`,
                    sender: 'agent' as const,
                    content: accumulated,
                    title: 'Response',
                    timestamp: new Date().toISOString().slice(0, 16).replace('T', ' '),
                  },
                ]
              })
              break
            }

            case 'tool_call':
              setAgentMessages(prev => [
                ...prev,
                {
                  id: `agent-tool-${Date.now()}-${Math.random()}`,
                  sender: 'system' as const,
                  content: `Using tool: **${msg.tool}**`,
                  title: msg.tool,
                  timestamp: new Date().toISOString().slice(0, 16).replace('T', ' '),
                },
              ])
              break

            case 'status':
              setAgentMessages(prev => [
                ...prev,
                {
                  id: `agent-status-${Date.now()}`,
                  sender: 'system' as const,
                  content: msg.content || '',
                  title: 'Status',
                  timestamp: new Date().toISOString().slice(0, 16).replace('T', ' '),
                },
              ])
              break

            case 'response_done':
              streamingTextRef.current = ''
              setAgentState(prev => ({ ...prev, streaming: false }))
              break

            case 'error':
              if (msg.content) {
                setAgentMessages(prev => [
                  ...prev,
                  {
                    id: `agent-error-${Date.now()}`,
                    sender: 'system' as const,
                    content: `Error: ${msg.content}`,
                    title: 'Error',
                    timestamp: new Date().toISOString().slice(0, 16).replace('T', ' '),
                  },
                ])
              }
              streamingTextRef.current = ''
              setAgentState(prev => ({ ...prev, streaming: false }))
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

  // Agent control functions
  const startAgent = useCallback((opts: {
    modelId: string
    contextMode: string
    workingDirectory?: string
    projectName?: string
    effort?: string
  }) => {
    const ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) return
    ws.send(JSON.stringify({
      type: 'start_agent',
      model_id: opts.modelId,
      context_mode: opts.contextMode,
      working_directory: opts.workingDirectory,
      project_name: opts.projectName,
      effort: opts.effort || 'high',
    }))
    setAgentMessages([])
    streamingTextRef.current = ''
  }, [])

  const sendAgentMessage = useCallback((content: string) => {
    const ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) return
    // Add user message to agent messages
    setAgentMessages(prev => [
      ...prev,
      {
        id: `user-${Date.now()}`,
        sender: 'human' as const,
        content,
        title: 'Message',
        timestamp: new Date().toISOString().slice(0, 16).replace('T', ' '),
      },
    ])
    streamingTextRef.current = ''
    ws.send(JSON.stringify({ type: 'message', content }))
  }, [])

  const stopAgent = useCallback(() => {
    const ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) return
    ws.send(JSON.stringify({ type: 'stop_agent' }))
  }, [])

  return {
    commsLog,
    sendMessage,
    agentState,
    startAgent,
    sendAgentMessage,
    stopAgent,
    agentMessages,
    controlMode,
    setControlMode,
    tokenState,
    resetTokens,
    safetyStatus,
    config,
    saveBridge,
    connected,
    loading,
  }
}
