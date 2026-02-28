/**
 * DunkStack Agent View
 *
 * Resizable split-screen layout:
 *   Left (1/4 default):  Agent event log (top 3/4) + API chat input (bottom 1/4)
 *   Right (3/4 default): Walkie-talkie file comms (DunkStackCommsChat)
 *
 * Both the horizontal (left/right) and vertical (log/chat) splits are
 * draggable via mouse. The first message typed into the API chat starts
 * the agent — no separate "Start Agent" button needed.
 */

import { useState, useRef, useEffect, useCallback } from 'react'
import { Terminal, Wrench, CheckCircle2, XCircle, AlertTriangle, Activity, Cpu, Coins, Send, Loader2 } from 'lucide-react'
import { DunkStackCommsChat } from './DunkStackCommsChat'
import type { CommsEntry } from '@/hooks/useDunkStack'

// ============================================================================
// Types
// ============================================================================

export interface AgentEvent {
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

interface DunkStackAgentViewProps {
  agentEvents: AgentEvent[]
  commsLog: CommsEntry[]
  onSendMessage: (content: string, title?: string) => Promise<void>
  controlMode: string
  connected: boolean
  modelId?: string
  isRunning: boolean
  /** Send a message to the agent via API call */
  onSendToAgent?: (message: string) => Promise<void>
  /** Start the agent (called automatically on first API chat message) */
  onStartAgent?: () => Promise<void>
  /** Whether the agent is currently starting up */
  agentStarting?: boolean
  /** Name of the selected project */
  projectName?: string
}

// ============================================================================
// Helpers
// ============================================================================

function truncate(text: string, max: number): string {
  if (text.length <= max) return text
  const half = Math.floor((max - 3) / 2)
  return `${text.slice(0, half)}...${text.slice(-half)}`
}

function formatInputPreview(input: unknown): string {
  if (input == null) return ''
  try {
    const str = typeof input === 'string' ? input : JSON.stringify(input)
    return truncate(str, 120)
  } catch {
    return String(input)
  }
}

function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return String(n)
}

// ============================================================================
// Resizable splitter hook
// ============================================================================

function useSplitter(
  direction: 'horizontal' | 'vertical',
  defaultRatio: number,
  containerRef: React.RefObject<HTMLDivElement | null>,
) {
  const [ratio, setRatio] = useState(defaultRatio)
  const dragging = useRef(false)

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    dragging.current = true

    const onMouseMove = (ev: MouseEvent) => {
      if (!dragging.current || !containerRef.current) return
      const rect = containerRef.current.getBoundingClientRect()
      let newRatio: number
      if (direction === 'horizontal') {
        newRatio = (ev.clientX - rect.left) / rect.width
      } else {
        newRatio = (ev.clientY - rect.top) / rect.height
      }
      // Clamp between 10% and 90%
      setRatio(Math.min(0.9, Math.max(0.1, newRatio)))
    }

    const onMouseUp = () => {
      dragging.current = false
      document.removeEventListener('mousemove', onMouseMove)
      document.removeEventListener('mouseup', onMouseUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }

    document.addEventListener('mousemove', onMouseMove)
    document.addEventListener('mouseup', onMouseUp)
    document.body.style.cursor = direction === 'horizontal' ? 'col-resize' : 'row-resize'
    document.body.style.userSelect = 'none'
  }, [direction, containerRef])

  return { ratio, onMouseDown }
}

// ============================================================================
// Event renderers
// ============================================================================

function TextEvent({ event }: { event: AgentEvent }) {
  return (
    <div className="pl-3 py-1">
      <p className="text-sm text-foreground font-mono whitespace-pre-wrap break-words leading-relaxed">
        {event.content}
      </p>
    </div>
  )
}

function ToolCallEvent({ event }: { event: AgentEvent }) {
  return (
    <div className="flex items-start gap-2 p-2 rounded-lg bg-cyan-500/5 border border-cyan-500/15">
      <Wrench size={14} className="text-cyan-400 mt-0.5 shrink-0" />
      <div className="min-w-0">
        <span className="text-xs font-bold text-cyan-400">{event.tool ?? 'tool'}</span>
        {event.input != null && (
          <p className="text-[11px] text-muted-foreground font-mono mt-0.5 break-all">
            {formatInputPreview(event.input)}
          </p>
        )}
      </div>
    </div>
  )
}

function ToolResultEvent({ event }: { event: AgentEvent }) {
  const isError = event.is_error ?? false
  return (
    <div className={`flex items-start gap-2 p-2 rounded-lg ${
      isError ? 'bg-red-500/5 border border-red-500/15' : 'bg-emerald-500/5 border border-emerald-500/15'
    }`}>
      {isError
        ? <XCircle size={14} className="text-red-400 mt-0.5 shrink-0" />
        : <CheckCircle2 size={14} className="text-emerald-400 mt-0.5 shrink-0" />}
      <p className="text-[11px] text-muted-foreground font-mono break-all">
        {event.output ? truncate(event.output, 200) : isError ? 'Error (no output)' : 'OK'}
      </p>
    </div>
  )
}

function ResultEvent({ event }: { event: AgentEvent }) {
  const usage = event.usage ?? {}
  return (
    <div className="flex items-center gap-3 p-2 rounded-lg bg-primary/5 border border-primary/15">
      <Coins size={14} className="text-primary shrink-0" />
      <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-[11px] text-muted-foreground font-mono">
        {usage.input_tokens != null && <span>in: {formatTokens(usage.input_tokens)}</span>}
        {usage.output_tokens != null && <span>out: {formatTokens(usage.output_tokens)}</span>}
        {usage.total_cost_usd != null && <span>cost: ${Number(usage.total_cost_usd).toFixed(4)}</span>}
      </div>
    </div>
  )
}

function ErrorEvent({ event }: { event: AgentEvent }) {
  return (
    <div className="flex items-start gap-2 p-2 rounded-lg bg-red-500/10 border border-red-500/20">
      <AlertTriangle size={14} className="text-red-500 mt-0.5 shrink-0" />
      <p className="text-xs text-red-400 font-mono break-words">{event.content ?? 'Unknown error'}</p>
    </div>
  )
}

function AgentStatusEvent({ event }: { event: AgentEvent }) {
  return (
    <div className="flex items-center gap-2 p-2 rounded-lg bg-yellow-500/5 border border-yellow-500/15">
      <Activity size={14} className="text-yellow-400 shrink-0" />
      <span className="text-xs font-semibold text-yellow-400">{event.status ?? event.content ?? 'status change'}</span>
    </div>
  )
}

function EventItem({ event }: { event: AgentEvent }) {
  switch (event.type) {
    case 'text':           return <TextEvent event={event} />
    case 'tool_call':      return <ToolCallEvent event={event} />
    case 'tool_result':    return <ToolResultEvent event={event} />
    case 'result':         return <ResultEvent event={event} />
    case 'error':          return <ErrorEvent event={event} />
    case 'agent_status':   return <AgentStatusEvent event={event} />
    case 'response_done':  return <ResultEvent event={event} />
    default:               return null
  }
}

// ============================================================================
// Main Component
// ============================================================================

export function DunkStackAgentView({
  agentEvents,
  commsLog,
  onSendMessage,
  controlMode,
  connected,
  modelId,
  isRunning,
  onSendToAgent,
  onStartAgent,
  agentStarting,
  projectName,
}: DunkStackAgentViewProps): React.JSX.Element {
  const scrollRef = useRef<HTMLDivElement>(null)
  const [apiChatInput, setApiChatInput] = useState('')
  const [apiChatSending, setApiChatSending] = useState(false)

  // Refs for resizable containers
  const hContainerRef = useRef<HTMLDivElement>(null)
  const vContainerRef = useRef<HTMLDivElement>(null)

  // Horizontal split: left (API) / right (walkie-talkie) — default 25% / 75%
  const hSplitter = useSplitter('horizontal', 0.25, hContainerRef)
  // Vertical split on left panel: top (log) / bottom (chat) — default 75% / 25%
  const vSplitter = useSplitter('vertical', 0.75, vContainerRef)

  // Auto-scroll the event log
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [agentEvents.length])

  // Send a message via the API chat. If agent isn't running, start it first.
  const handleApiChatSend = useCallback(async () => {
    const msg = apiChatInput.trim()
    if (!msg) return

    setApiChatSending(true)
    setApiChatInput('')

    try {
      // Start agent if not running
      if (!isRunning && !agentStarting && onStartAgent) {
        await onStartAgent()
      }
      // Send message to agent
      if (onSendToAgent) {
        await onSendToAgent(msg)
      }
    } catch (e) {
      console.error('Failed to send API chat message:', e)
    } finally {
      setApiChatSending(false)
    }
  }, [apiChatInput, isRunning, agentStarting, onStartAgent, onSendToAgent])

  const handleApiChatKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleApiChatSend()
    }
  }, [handleApiChatSend])

  const isBusy = agentStarting || apiChatSending

  return (
    <div ref={hContainerRef} className="flex h-full w-full overflow-hidden">
      {/* ── Left Panel: API Call (log + chat) ── */}
      <div
        className="flex flex-col min-w-0 overflow-hidden"
        style={{ width: `${hSplitter.ratio * 100}%` }}
      >
        <div ref={vContainerRef} className="flex flex-col flex-1 min-h-0">
          {/* Top: Event Log */}
          <div
            className="flex flex-col min-h-0 overflow-hidden"
            style={{ height: `${vSplitter.ratio * 100}%` }}
          >
            {/* Log header */}
            <div className="flex items-center justify-between px-3 py-1.5 border-b border-border bg-card shrink-0">
              <div className="flex items-center gap-2">
                <Terminal size={14} className="text-primary" />
                <span className="text-xs font-semibold text-foreground">API Call</span>
                {modelId && (
                  <span className="text-[10px] text-muted-foreground font-mono">{modelId}</span>
                )}
              </div>
              <div className="flex items-center gap-1.5">
                <Cpu size={11} className="text-muted-foreground" />
                <span className="text-[10px] text-muted-foreground font-mono">
                  {agentEvents.length} events
                </span>
                <span
                  className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                    isRunning ? 'bg-emerald-500 animate-pulse' :
                    agentStarting ? 'bg-amber-500 animate-pulse' :
                    'bg-muted-foreground/30'
                  }`}
                />
              </div>
            </div>

            {/* Scrollable event log */}
            <div ref={scrollRef} className="flex-1 overflow-y-auto p-2 space-y-1.5 min-h-0">
              {agentEvents.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center gap-2">
                  <Terminal size={24} className="text-muted-foreground/20" />
                  <p className="text-xs text-muted-foreground">
                    {isRunning ? 'Waiting for output...' : 'Type a message below to start the agent'}
                  </p>
                </div>
              ) : (
                agentEvents.map((event) => (
                  <EventItem key={event.id} event={event} />
                ))
              )}
            </div>
          </div>

          {/* Vertical splitter handle */}
          <div
            onMouseDown={vSplitter.onMouseDown}
            className="h-1.5 shrink-0 cursor-row-resize bg-border/50 hover:bg-primary/30 transition-colors flex items-center justify-center"
          >
            <div className="w-8 h-0.5 rounded-full bg-muted-foreground/30" />
          </div>

          {/* Bottom: API Chat Input */}
          <div
            className="flex flex-col min-h-0 overflow-hidden"
            style={{ height: `${(1 - vSplitter.ratio) * 100}%` }}
          >
            <div className="flex-1 flex flex-col p-2 min-h-0">
              <textarea
                value={apiChatInput}
                onChange={e => setApiChatInput(e.target.value)}
                onKeyDown={handleApiChatKeyDown}
                placeholder={
                  isRunning
                    ? 'Send a message to the agent...'
                    : projectName
                      ? `Type a message to start the agent on "${projectName}"...`
                      : 'Select a project, then type to start...'
                }
                disabled={isBusy || !projectName}
                className="flex-1 w-full resize-none bg-background text-foreground text-sm font-mono p-2 rounded-lg border border-border focus:outline-none focus:border-primary placeholder:text-muted-foreground/50 min-h-0"
              />
              <div className="flex items-center justify-between mt-1.5 shrink-0">
                <span className="text-[10px] text-muted-foreground">
                  {isRunning ? 'Agent running' : 'Enter sends · Shift+Enter for newline'}
                </span>
                <button
                  onClick={handleApiChatSend}
                  disabled={!apiChatInput.trim() || isBusy || !projectName}
                  className="flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  {isBusy ? (
                    <Loader2 size={12} className="animate-spin" />
                  ) : (
                    <Send size={12} />
                  )}
                  {!isRunning && !agentStarting ? 'Start' : 'Send'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Horizontal splitter handle */}
      <div
        onMouseDown={hSplitter.onMouseDown}
        className="w-1.5 shrink-0 cursor-col-resize bg-border/50 hover:bg-primary/30 transition-colors flex items-center justify-center"
      >
        <div className="h-8 w-0.5 rounded-full bg-muted-foreground/30" />
      </div>

      {/* ── Right Panel: Walkie-Talkie (Comms Chat) ── */}
      <div
        className="flex flex-col min-w-0 overflow-hidden"
        style={{ width: `${(1 - hSplitter.ratio) * 100}%` }}
      >
        <DunkStackCommsChat
          commsLog={commsLog}
          onSendMessage={onSendMessage}
          controlMode={controlMode}
          connected={connected}
        />
      </div>
    </div>
  )
}
