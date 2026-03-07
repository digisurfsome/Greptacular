/**
 * DunkStack Agent View
 *
 * Three-column resizable layout:
 *   Left   (~15%): API Chat — persistent message history + input at bottom
 *   Middle (~35%): Agent event log — real-time tool calls, text, token usage
 *   Right  (~50%): Walkie-talkie file comms (DunkStackCommsChat)
 *
 * Two draggable splitter handles between the columns.
 * First message typed into the API chat auto-starts the agent.
 */

import { useState, useRef, useEffect, useCallback } from 'react'
import { Terminal, Wrench, CheckCircle2, XCircle, AlertTriangle, Activity, Cpu, Coins, Send, Loader2, MessageSquare } from 'lucide-react'
import { DunkStackCommsChat } from './DunkStackCommsChat'
import type { CommsEntry, AgentState } from '@/hooks/useDunkStack'

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

interface ApiChatMessage {
  id: string
  role: 'user' | 'agent' | 'system'
  content: string
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
  /** Stop the running agent session */
  onStopAgent?: () => void
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
// Resizable 3-column hook
// ============================================================================

/** Manages two splitter positions for a 3-column layout. */
function useThreeColumnSplitter(
  containerRef: React.RefObject<HTMLDivElement | null>,
  defaultSplit1: number, // fraction for first splitter (e.g. 0.15)
  defaultSplit2: number, // fraction for second splitter (e.g. 0.50)
) {
  const [split1, setSplit1] = useState(defaultSplit1)
  const [split2, setSplit2] = useState(defaultSplit2)
  const dragging = useRef<'none' | 'first' | 'second'>('none')

  const onMouseDown1 = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    dragging.current = 'first'
    const onMove = (ev: MouseEvent) => {
      if (dragging.current !== 'first' || !containerRef.current) return
      const rect = containerRef.current.getBoundingClientRect()
      const ratio = (ev.clientX - rect.left) / rect.width
      // Clamp: min 5%, max up to 5% before split2
      setSplit1(Math.min(split2 - 0.05, Math.max(0.05, ratio)))
    }
    const onUp = () => {
      dragging.current = 'none'
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseup', onUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
    document.addEventListener('mousemove', onMove)
    document.addEventListener('mouseup', onUp)
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }, [containerRef, split2])

  const onMouseDown2 = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    dragging.current = 'second'
    const onMove = (ev: MouseEvent) => {
      if (dragging.current !== 'second' || !containerRef.current) return
      const rect = containerRef.current.getBoundingClientRect()
      const ratio = (ev.clientX - rect.left) / rect.width
      // Clamp: min 5% after split1, max 95%
      setSplit2(Math.min(0.95, Math.max(split1 + 0.05, ratio)))
    }
    const onUp = () => {
      dragging.current = 'none'
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseup', onUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
    document.addEventListener('mousemove', onMove)
    document.addEventListener('mouseup', onUp)
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }, [containerRef, split1])

  // Column widths as percentages
  const col1 = `${split1 * 100}%`
  const col2 = `${(split2 - split1) * 100}%`
  const col3 = `${(1 - split2) * 100}%`

  return { col1, col2, col3, onMouseDown1, onMouseDown2 }
}

// ============================================================================
// Event renderers (for the log column)
// ============================================================================

function TextEvent({ event }: { event: AgentEvent }) {
  return (
    <div className="pl-2 py-0.5">
      <p className="text-xs text-foreground font-mono whitespace-pre-wrap break-words leading-relaxed">
        {event.content}
      </p>
    </div>
  )
}

function ToolCallEvent({ event }: { event: AgentEvent }) {
  return (
    <div className="flex items-start gap-1.5 p-1.5 rounded bg-cyan-500/5 border border-cyan-500/15">
      <Wrench size={12} className="text-cyan-400 mt-0.5 shrink-0" />
      <div className="min-w-0">
        <span className="text-[11px] font-bold text-cyan-400">{event.tool ?? 'tool'}</span>
        {event.input != null && (
          <p className="text-[10px] text-muted-foreground font-mono mt-0.5 break-all">
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
    <div className={`flex items-start gap-1.5 p-1.5 rounded ${
      isError ? 'bg-red-500/5 border border-red-500/15' : 'bg-emerald-500/5 border border-emerald-500/15'
    }`}>
      {isError
        ? <XCircle size={12} className="text-red-400 mt-0.5 shrink-0" />
        : <CheckCircle2 size={12} className="text-emerald-400 mt-0.5 shrink-0" />}
      <p className="text-[10px] text-muted-foreground font-mono break-all">
        {event.output ? truncate(event.output, 200) : isError ? 'Error (no output)' : 'OK'}
      </p>
    </div>
  )
}

function ResultEvent({ event }: { event: AgentEvent }) {
  const usage = event.usage ?? {}
  return (
    <div className="flex items-center gap-2 p-1.5 rounded bg-primary/5 border border-primary/15">
      <Coins size={12} className="text-primary shrink-0" />
      <div className="flex flex-wrap gap-x-2 gap-y-0.5 text-[10px] text-muted-foreground font-mono">
        {usage.input_tokens != null && <span>in: {formatTokens(usage.input_tokens)}</span>}
        {usage.output_tokens != null && <span>out: {formatTokens(usage.output_tokens)}</span>}
        {usage.total_cost_usd != null && <span>${Number(usage.total_cost_usd).toFixed(4)}</span>}
      </div>
    </div>
  )
}

function ErrorEvent({ event }: { event: AgentEvent }) {
  return (
    <div className="flex items-start gap-1.5 p-1.5 rounded bg-red-500/10 border border-red-500/20">
      <AlertTriangle size={12} className="text-red-500 mt-0.5 shrink-0" />
      <p className="text-[10px] text-red-400 font-mono break-words">{event.content ?? 'Unknown error'}</p>
    </div>
  )
}

function AgentStatusEvent({ event }: { event: AgentEvent }) {
  return (
    <div className="flex items-center gap-1.5 p-1.5 rounded bg-yellow-500/5 border border-yellow-500/15">
      <Activity size={12} className="text-yellow-400 shrink-0" />
      <span className="text-[10px] font-semibold text-yellow-400">{event.status ?? event.content ?? 'status change'}</span>
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
  onStopAgent,
}: DunkStackAgentViewProps): React.JSX.Element {
  const logScrollRef = useRef<HTMLDivElement>(null)
  const chatScrollRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  const [apiChatInput, setApiChatInput] = useState('')
  const [apiChatSending, setApiChatSending] = useState(false)
  const [apiMessages, setApiMessages] = useState<ApiChatMessage[]>([])

  // Agent state derived from props
  const agentState: AgentState = { running: isRunning, streaming: false }

  // Note: agentMessages derivation removed — walkie-talkie now always
  // shows commsLog (file-based messages) to keep channels separate.

  // 3-column layout: API chat (15%) | Log (35%) | Walkie-talkie (50%)
  const cols = useThreeColumnSplitter(containerRef, 0.15, 0.50)

  // Auto-scroll the event log
  useEffect(() => {
    if (logScrollRef.current) {
      logScrollRef.current.scrollTop = logScrollRef.current.scrollHeight
    }
  }, [agentEvents.length])

  // Auto-scroll the API chat
  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight
    }
  }, [apiMessages.length])

  // NOTE: Agent text responses are NOT mirrored to the API chat.
  // The API chat (left) only shows user-initiated messages and status.
  // All agent responses appear on the walkie-talkie (right) via commsLog.

  // Send a message via the API chat. If agent isn't running, start it first.
  const handleApiChatSend = useCallback(async () => {
    const msg = apiChatInput.trim()
    if (!msg) return

    // Add to persistent message list immediately
    setApiMessages(prev => [...prev, {
      id: `user-${Date.now()}`,
      role: 'user',
      content: msg,
      timestamp: new Date().toISOString(),
    }])

    setApiChatSending(true)
    setApiChatInput('')

    try {
      // Start agent if not running
      if (!isRunning && !agentStarting && onStartAgent) {
        setApiMessages(prev => [...prev, {
          id: `sys-${Date.now()}`,
          role: 'system',
          content: 'Starting agent...',
          timestamp: new Date().toISOString(),
        }])
        await onStartAgent()
      }
      // Send message to agent
      if (onSendToAgent) {
        await onSendToAgent(msg)
      }
    } catch (e) {
      setApiMessages(prev => [...prev, {
        id: `err-${Date.now()}`,
        role: 'system',
        content: `Error: ${e instanceof Error ? e.message : String(e)}`,
        timestamp: new Date().toISOString(),
      }])
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
    <div ref={containerRef} className="flex h-full w-full overflow-hidden">
      {/* ── Column 1: API Chat — hidden on mobile ── */}
      <div className="hidden md:flex flex-col min-w-0 overflow-hidden" style={{ width: cols.col1 }}>
        {/* Header */}
        <div className="flex items-center gap-1.5 px-2 py-1.5 border-b border-border bg-card shrink-0">
          <MessageSquare size={12} className="text-primary shrink-0" />
          <span className="text-[11px] font-semibold text-foreground truncate">API Chat</span>
          <span
            className={`w-1.5 h-1.5 rounded-full shrink-0 ml-auto ${
              isRunning ? 'bg-emerald-500 animate-pulse' :
              agentStarting ? 'bg-amber-500 animate-pulse' :
              'bg-muted-foreground/30'
            }`}
          />
        </div>

        {/* Message history */}
        <div ref={chatScrollRef} className="flex-1 overflow-y-auto p-1.5 space-y-1 min-h-0">
          {apiMessages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center gap-1.5 px-1">
              <MessageSquare size={18} className="text-muted-foreground/20" />
              <p className="text-[10px] text-muted-foreground leading-tight">
                {projectName ? 'Type below to start' : 'Select a project'}
              </p>
            </div>
          ) : (
            apiMessages.map(msg => (
              <div
                key={msg.id}
                className={`rounded px-1.5 py-1 text-[11px] font-mono break-words leading-tight ${
                  msg.role === 'user'
                    ? 'bg-primary/10 text-primary ml-1'
                    : msg.role === 'system'
                    ? 'bg-yellow-500/10 text-yellow-400 text-center italic'
                    : 'bg-muted/50 text-foreground mr-1'
                }`}
              >
                {msg.content}
              </div>
            ))
          )}
        </div>

        {/* Input */}
        <div className="border-t border-border p-1.5 shrink-0">
          <div className="flex gap-1">
            <input
              type="text"
              value={apiChatInput}
              onChange={e => setApiChatInput(e.target.value)}
              onKeyDown={handleApiChatKeyDown}
              placeholder={isRunning ? 'Message...' : 'Start...'}
              disabled={isBusy || !projectName}
              className="flex-1 min-w-0 bg-background text-foreground text-[11px] font-mono px-1.5 py-1 rounded border border-border focus:outline-none focus:border-primary placeholder:text-muted-foreground/40"
            />
            <button
              onClick={handleApiChatSend}
              disabled={!apiChatInput.trim() || isBusy || !projectName}
              className="shrink-0 p-1 rounded bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              {isBusy ? <Loader2 size={12} className="animate-spin" /> : <Send size={12} />}
            </button>
          </div>
        </div>
      </div>

      {/* Splitter 1 — hidden on mobile */}
      <div
        onMouseDown={cols.onMouseDown1}
        className="hidden md:flex w-1 shrink-0 cursor-col-resize bg-border/50 hover:bg-primary/30 transition-colors items-center justify-center"
      >
        <div className="h-8 w-0.5 rounded-full bg-muted-foreground/30" />
      </div>

      {/* ── Column 2: Agent Event Log — hidden on mobile ── */}
      <div className="hidden md:flex flex-col min-w-0 overflow-hidden" style={{ width: cols.col2 }}>
        {/* Header */}
        <div className="flex items-center justify-between px-2 py-1.5 border-b border-border bg-card shrink-0">
          <div className="flex items-center gap-1.5">
            <Terminal size={12} className="text-primary" />
            <span className="text-[11px] font-semibold text-foreground">Log</span>
            {modelId && (
              <span className="text-[9px] text-muted-foreground font-mono truncate">{modelId}</span>
            )}
          </div>
          <div className="flex items-center gap-1">
            <Cpu size={10} className="text-muted-foreground" />
            <span className="text-[9px] text-muted-foreground font-mono">
              {agentEvents.length}
            </span>
          </div>
        </div>

        {/* Scrollable event log */}
        <div ref={logScrollRef} className="flex-1 overflow-y-auto p-1.5 space-y-1 min-h-0">
          {agentEvents.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center gap-1.5">
              <Terminal size={18} className="text-muted-foreground/20" />
              <p className="text-[10px] text-muted-foreground">
                {isRunning ? 'Waiting for output...' : 'No events yet'}
              </p>
            </div>
          ) : (
            agentEvents.map(event => (
              <EventItem key={event.id} event={event} />
            ))
          )}
        </div>
      </div>

      {/* Splitter 2 — hidden on mobile */}
      <div
        onMouseDown={cols.onMouseDown2}
        className="hidden md:flex w-1 shrink-0 cursor-col-resize bg-border/50 hover:bg-primary/30 transition-colors items-center justify-center"
      >
        <div className="h-8 w-0.5 rounded-full bg-muted-foreground/30" />
      </div>

      {/* ── Column 3: Walkie-Talkie (Comms Chat) ──
           On mobile: min-w-full forces 100% width (overrides inline %).
           On desktop: min-w-0 lets the splitter-based width work. */}
      <div
        className="flex flex-col min-w-full md:min-w-0 overflow-hidden"
        style={{ width: cols.col3 }}
      >
        <DunkStackCommsChat
          commsLog={commsLog}
          onSendMessage={onSendMessage}
          controlMode={controlMode}
          connected={connected}
          agentState={agentState}
          onStartAgent={() => { onStartAgent?.() }}
          onStopAgent={() => { onStopAgent?.() }}
        />
      </div>
    </div>
  )
}
