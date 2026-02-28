/**
 * DunkStack Agent View
 *
 * Split-screen layout for when the coding agent is running.
 * Left panel shows real-time streaming API output (text, tool calls,
 * tool results, token usage, errors). Right panel renders the
 * file-based comms chat (DunkStackCommsChat).
 */

import { useRef, useEffect } from 'react'
import { Terminal, Wrench, CheckCircle2, XCircle, AlertTriangle, Activity, Cpu, Coins } from 'lucide-react'
import { DunkStackCommsChat } from './DunkStackCommsChat'
import type { CommsEntry } from '@/hooks/useDunkStack'

// ============================================================================
// Types
// ============================================================================

export interface AgentEvent {
  id: string
  type: 'text' | 'tool_call' | 'tool_result' | 'result' | 'error' | 'agent_status' | 'response_done'
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
  /** Agent streaming events (accumulated from WebSocket) */
  agentEvents: AgentEvent[]
  /** Combined, sorted comms log */
  commsLog: CommsEntry[]
  /** Send a message (human -> agent via from_human.md) */
  onSendMessage: (content: string, title?: string) => Promise<void>
  /** Current session control mode */
  controlMode: string
  /** Whether connected to WebSocket */
  connected: boolean
  /** Model identifier shown in the header */
  modelId?: string
  /** Whether the agent is currently running */
  isRunning: boolean
}

// ============================================================================
// Helpers
// ============================================================================

/** Truncate long strings for display, preserving start and end. */
function truncate(text: string, max: number): string {
  if (text.length <= max) return text
  const half = Math.floor((max - 3) / 2)
  return `${text.slice(0, half)}...${text.slice(-half)}`
}

/** Format a JSON-serializable value into a compact one-line preview. */
function formatInputPreview(input: unknown): string {
  if (input == null) return ''
  try {
    const str = typeof input === 'string' ? input : JSON.stringify(input)
    return truncate(str, 120)
  } catch {
    return String(input)
  }
}

/** Format token counts with K/M suffixes. */
function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return String(n)
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
}: DunkStackAgentViewProps): React.JSX.Element {
  const scrollRef = useRef<HTMLDivElement>(null)

  // Auto-scroll the API call log when new events arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [agentEvents.length])

  return (
    <div className="flex h-full w-full">
      {/* ── Left Panel: API Call Output ── */}
      <div className="flex-1 flex flex-col min-w-0 border-r border-border">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-card shrink-0">
          <div className="flex items-center gap-2">
            <Terminal size={16} className="text-primary" />
            <span className="text-sm font-semibold text-foreground">API Call</span>
            {modelId && (
              <span className="text-[10px] text-muted-foreground font-mono">
                {modelId}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Cpu size={12} className="text-muted-foreground" />
            <span className="text-[10px] text-muted-foreground font-mono">
              {agentEvents.length} events
            </span>
            <span
              className={`w-2 h-2 rounded-full shrink-0 ${
                isRunning ? 'bg-emerald-500 animate-pulse' : 'bg-muted-foreground/30'
              }`}
              title={isRunning ? 'Agent running' : 'Agent idle'}
            />
          </div>
        </div>

        {/* Scrollable event log */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-2 min-h-0">
          {agentEvents.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center gap-3">
              <Terminal size={32} className="text-muted-foreground/30" />
              <div>
                <p className="text-sm text-muted-foreground">No agent output yet</p>
                <p className="text-xs text-muted-foreground/60 mt-1">
                  Streaming events will appear here when the agent starts processing.
                </p>
              </div>
            </div>
          ) : (
            agentEvents.map((event) => (
              <EventItem key={event.id} event={event} />
            ))
          )}
        </div>
      </div>

      {/* ── Right Panel: Walkie-Talkie (Comms Chat) ── */}
      <div className="flex-1 flex flex-col min-w-0">
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
