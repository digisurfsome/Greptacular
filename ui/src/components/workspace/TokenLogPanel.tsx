/**
 * Token Processing Log Panel (Left Side Panel)
 *
 * Full-height side panel that sits to the left of the chat area,
 * squishing the chat content to make room. Shows a running
 * cumulative cost total alongside every token log entry, with the
 * cumulative total accumulating from result_summary events (which
 * carry the real api_total_cost_usd).
 *
 * Designed for debugging and auditing token usage -- dense, compact
 * layout that packs maximum information into 320px of width.
 */

import { useState, useMemo, useCallback, useEffect, useRef } from 'react'
import {
  ScrollText,
  Download,
  Trash2,
  BarChart3,
  Loader2,
  X,
} from 'lucide-react'
import { getTokenLogSummary, clearTokenLog as clearTokenLogApi } from '@/lib/api'
import { parseUtcTimestamp } from '@/lib/utils'
import type { TokenLogEntry, TokenLogSummary, TokenLogToolBreakdown } from '@/lib/types'

// -- Helpers ------------------------------------------------------------------

/** Format a token count with commas for readability (e.g. 1,234,567). */
function formatTokens(n: number): string {
  return n.toLocaleString()
}

/** Format cost with 4 decimal places (e.g. $0.0042). */
function formatCost(cost: number): string {
  if (cost === 0) return '$0.0000'
  return `$${cost.toFixed(4)}`
}

/** Format milliseconds as a human-readable duration. */
function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`
  if (ms < 60_000) return `${(ms / 1000).toFixed(1)}s`
  return `${(ms / 60_000).toFixed(1)}m`
}

/** Map event_type to a color class for the badge. */
function eventTypeColor(eventType: string): string {
  switch (eventType) {
    case 'assistant_turn':
      return 'bg-cyan-500/15 text-cyan-500 border-cyan-500/30'
    case 'tool_call':
      return 'bg-yellow-500/15 text-yellow-600 dark:text-yellow-400 border-yellow-500/30'
    case 'tool_result':
      return 'bg-orange-500/15 text-orange-600 dark:text-orange-400 border-orange-500/30'
    case 'result_summary':
      return 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30'
    default:
      return 'bg-muted text-muted-foreground border-border'
  }
}

/** Short display label for event types. */
function eventTypeLabel(eventType: string): string {
  switch (eventType) {
    case 'assistant_turn': return 'Turn'
    case 'tool_call': return 'Call'
    case 'tool_result': return 'Result'
    case 'result_summary': return 'Summary'
    default: return eventType
  }
}

// -- Types for running total computation -------------------------------------

interface EntryWithRunningTotal {
  entry: TokenLogEntry
  /** Cumulative API cost up to and including this entry. */
  runningTotal: number
}

// -- Sub-components -----------------------------------------------------------

/** Format token count in compact form for the header (e.g. 142.3K). */
function formatTokensCompact(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return String(n)
}

/** Two-row header: "This Turn" (latest API response) + "Session Total". */
function TokenLogTotals({
  entries,
  summary,
}: {
  entries: TokenLogEntry[]
  summary: TokenLogSummary | null
}) {
  const { thisTurn, sessionTotal } = useMemo(() => {
    let totalInput = 0
    let totalOutput = 0
    let totalCost = 0
    let turnCount = 0
    // Latest turn data
    let lastInput = 0
    let lastOutput = 0
    let lastCost = 0
    let lastCacheRead = 0
    let lastCacheCreate = 0

    for (const e of entries) {
      if (e.event_type === 'result_summary') {
        totalInput += e.api_input_tokens ?? 0
        totalOutput += e.api_output_tokens ?? 0
        totalCost += e.api_total_cost_usd ?? 0
        turnCount++
        lastInput = e.api_input_tokens ?? 0
        lastOutput = e.api_output_tokens ?? 0
        lastCost = e.api_total_cost_usd ?? 0
        lastCacheRead = e.api_cache_read_tokens ?? 0
        lastCacheCreate = e.api_cache_creation_tokens ?? 0
      }
    }

    const currentContext = lastInput + lastCacheRead + lastCacheCreate
    const cacheHitRate = (lastInput + lastCacheRead) > 0
      ? Math.round((lastCacheRead / (lastInput + lastCacheRead)) * 100)
      : 0

    return {
      thisTurn: {
        input: lastInput,
        output: lastOutput,
        cost: lastCost,
        currentContext,
        cacheHitRate,
        cacheRead: lastCacheRead,
      },
      sessionTotal: {
        input: summary?.total_api_input_tokens ?? totalInput,
        output: summary?.total_api_output_tokens ?? totalOutput,
        cost: summary?.total_cost_usd ?? totalCost,
        turnCount,
      },
    }
  }, [entries, summary])

  return (
    <div className="space-y-2 text-[10px]">
      {/* This Turn — latest API response */}
      <div>
        <div className="text-[9px] font-semibold text-muted-foreground/70 uppercase tracking-wider mb-0.5">This Turn</div>
        <div className="grid grid-cols-2 gap-x-3 gap-y-0.5">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Input:</span>
            <span className="font-mono font-bold text-foreground tabular-nums">
              {formatTokensCompact(thisTurn.input)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Output:</span>
            <span className="font-mono font-bold text-foreground tabular-nums">
              {formatTokensCompact(thisTurn.output)}
            </span>
          </div>
          {thisTurn.currentContext > 0 && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Context:</span>
              <span className="font-mono font-bold text-blue-500 tabular-nums">
                {formatTokensCompact(thisTurn.currentContext)}
              </span>
            </div>
          )}
          {thisTurn.cacheRead > 0 && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Cache Hit:</span>
              <span className="font-mono font-bold text-purple-500 tabular-nums">
                {thisTurn.cacheHitRate}%
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Session Total — sum of all turns */}
      <div className="border-t border-border/30 pt-1.5">
        <div className="text-[9px] font-semibold text-muted-foreground/70 uppercase tracking-wider mb-0.5">
          Session Total <span className="normal-case font-normal">({sessionTotal.turnCount} turn{sessionTotal.turnCount !== 1 ? 's' : ''})</span>
        </div>
        <div className="grid grid-cols-2 gap-x-3 gap-y-0.5">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Total Input:</span>
            <span className="font-mono font-bold text-foreground tabular-nums">
              {formatTokensCompact(sessionTotal.input)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Total Output:</span>
            <span className="font-mono font-bold text-foreground tabular-nums">
              {formatTokensCompact(sessionTotal.output)}
            </span>
          </div>
          <div className="flex justify-between col-span-2">
            <span className="text-muted-foreground">API Cost:</span>
            <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400 tabular-nums">
              {formatCost(sessionTotal.cost)}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

/** Per-tool breakdown table. */
function ToolBreakdownTable({ breakdown }: { breakdown: TokenLogToolBreakdown[] }) {
  if (breakdown.length === 0) return null

  const sorted = [...breakdown].sort((a, b) => b.total_estimated_tokens - a.total_estimated_tokens)

  return (
    <div className="space-y-1.5">
      <div className="flex items-center gap-1.5 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
        <BarChart3 size={10} />
        Per-Tool Breakdown
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-[10px] border-collapse">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left py-1 pr-2 text-muted-foreground font-medium">Tool</th>
              <th className="text-right py-1 px-1 text-muted-foreground font-medium">#</th>
              <th className="text-right py-1 pl-1 text-muted-foreground font-medium">Est. Tot</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((row) => (
              <tr key={row.tool_name} className="border-b border-border/50 hover:bg-muted/30">
                <td className="py-0.5 pr-2 font-mono text-foreground truncate max-w-[120px]">
                  {row.tool_name}
                  {row.error_count > 0 && (
                    <span className="ml-1 text-destructive">({row.error_count})</span>
                  )}
                </td>
                <td className="py-0.5 px-1 text-right font-mono tabular-nums text-foreground">
                  {row.call_count}
                </td>
                <td className="py-0.5 pl-1 text-right font-mono tabular-nums font-bold text-foreground">
                  {formatTokens(row.total_estimated_tokens)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

/** Single log entry row for the side panel. */
function TokenLogRow({
  entry,
  runningTotal,
}: {
  entry: TokenLogEntry
  runningTotal: number
}) {
  const time = parseUtcTimestamp(entry.timestamp).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })

  const isSummary = entry.event_type === 'result_summary'
  const thisTurnCost = isSummary ? (entry.api_total_cost_usd ?? 0) : 0

  return (
    <div className={`py-1 px-2 border-b border-border/30 hover:bg-muted/20 transition-colors text-[10px] ${isSummary ? 'bg-emerald-500/5' : ''}`}>
      {/* Top line: turn#, time, badge, cost info */}
      <div className="flex items-center gap-1.5">
        <span className="flex-shrink-0 w-4 text-right font-mono tabular-nums text-muted-foreground">
          {entry.turn_number}
        </span>
        <span className="flex-shrink-0 font-mono tabular-nums text-muted-foreground/70">
          {time}
        </span>
        <span className={`flex-shrink-0 px-1 py-0.5 rounded text-[9px] font-semibold border ${eventTypeColor(entry.event_type)}`}>
          {eventTypeLabel(entry.event_type)}
        </span>
        {/* Right side: incremental cost (summary only) | running total */}
        <span className="ml-auto flex-shrink-0 font-mono tabular-nums text-muted-foreground">
          {isSummary && thisTurnCost > 0 && (
            <span className="text-emerald-600 dark:text-emerald-400 mr-1.5">
              +{formatCost(thisTurnCost)}
            </span>
          )}
          <span className="text-muted-foreground/60">{formatCost(runningTotal)}</span>
        </span>
      </div>

      {/* Second line: tool name or details */}
      <div className="mt-0.5 pl-[22px]">
        {entry.tool_name && (
          <span className="font-mono text-foreground">
            {entry.tool_name}
            {entry.tool_is_error && (
              <span className="ml-1 text-destructive font-bold">ERR</span>
            )}
          </span>
        )}

        {entry.event_type === 'tool_call' && entry.tool_input_length != null && (
          <span className="text-muted-foreground ml-1">
            in:{formatTokens(entry.tool_input_length)}c
          </span>
        )}
        {entry.event_type === 'tool_result' && entry.tool_result_length != null && (
          <span className="text-muted-foreground ml-1">
            out:{formatTokens(entry.tool_result_length)}c
          </span>
        )}
        {entry.event_type === 'assistant_turn' && (
          <span className="text-muted-foreground">
            {entry.text_length != null && `${formatTokens(entry.text_length)} chars`}
            {entry.num_tool_calls != null && entry.num_tool_calls > 0 && (
              <span className="ml-1">+ {entry.num_tool_calls} call{entry.num_tool_calls !== 1 ? 's' : ''}</span>
            )}
          </span>
        )}

        {/* Summary details: actual API token counts */}
        {isSummary && (
          <div className="flex flex-wrap gap-x-2 gap-y-0.5 text-muted-foreground mt-0.5">
            {entry.api_input_tokens != null && (
              <span>in:<span className="font-mono text-foreground">{formatTokens(entry.api_input_tokens)}</span></span>
            )}
            {entry.api_output_tokens != null && (
              <span>out:<span className="font-mono text-foreground">{formatTokens(entry.api_output_tokens)}</span></span>
            )}
            {entry.api_cache_read_tokens != null && entry.api_cache_read_tokens > 0 && (
              <span>cache:<span className="font-mono text-purple-500">{formatTokens(entry.api_cache_read_tokens)}</span></span>
            )}
            {entry.api_duration_ms != null && (
              <span>{formatDuration(entry.api_duration_ms)}</span>
            )}
          </div>
        )}

        {/* Non-summary: show actual token data if available, else chars */}
        {!isSummary && entry.event_type === 'tool_result' && entry.tool_result_length != null && entry.tool_result_length > 0 && (
          <span className="text-muted-foreground/60 ml-1">
            ({formatTokens(entry.tool_result_length)} chars)
          </span>
        )}
      </div>
    </div>
  )
}

// -- Main Component -----------------------------------------------------------

interface TokenLogPanelProps {
  /** Real-time token log entries received via WebSocket. */
  entries: TokenLogEntry[]
  /** Active conversation ID (required for REST API calls). */
  conversationId: number | null
  /** Callback to close/dismiss the panel. */
  onClose?: () => void
  /** Callback to clear the local entries array in the parent. */
  onClear?: () => void
}

const TOKEN_LOG_WIDTH_KEY = 'token-log-panel-width'
const MIN_WIDTH = 240
const MAX_WIDTH = 600
const DEFAULT_WIDTH = 320

export function TokenLogPanel({ entries, conversationId, onClose, onClear }: TokenLogPanelProps): React.JSX.Element {
  const [summary, setSummary] = useState<TokenLogSummary | null>(null)
  const [isLoadingSummary, setIsLoadingSummary] = useState(false)
  const [isClearing, setIsClearing] = useState(false)
  const [showBreakdown, setShowBreakdown] = useState(false)
  const logContainerRef = useRef<HTMLDivElement>(null)

  // --- Resizable width ---
  const [panelWidth, setPanelWidth] = useState(() => {
    const saved = localStorage.getItem(TOKEN_LOG_WIDTH_KEY)
    const w = saved ? parseInt(saved, 10) : DEFAULT_WIDTH
    return (w >= MIN_WIDTH && w <= MAX_WIDTH) ? w : DEFAULT_WIDTH
  })
  const isDraggingRef = useRef(false)
  const startXRef = useRef(0)
  const startWidthRef = useRef(DEFAULT_WIDTH)

  const handleResizeStart = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    isDraggingRef.current = true
    startXRef.current = e.clientX
    startWidthRef.current = panelWidth

    const handleMove = (ev: MouseEvent) => {
      if (!isDraggingRef.current) return
      // Panel is on the LEFT, so dragging left = wider (negative delta = wider)
      const delta = startXRef.current - ev.clientX
      const newWidth = Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, startWidthRef.current + delta))
      setPanelWidth(newWidth)
    }
    const handleUp = () => {
      isDraggingRef.current = false
      document.removeEventListener('mousemove', handleMove)
      document.removeEventListener('mouseup', handleUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
      // Persist
      setPanelWidth((w) => {
        localStorage.setItem(TOKEN_LOG_WIDTH_KEY, String(w))
        return w
      })
    }
    document.addEventListener('mousemove', handleMove)
    document.addEventListener('mouseup', handleUp)
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }, [panelWidth])

  // Compute running cumulative cost for each entry.
  // The running total only increments on result_summary events,
  // which carry the real api_total_cost_usd from the API.
  // Non-summary entries show the last known running total.
  const entriesWithTotals: EntryWithRunningTotal[] = useMemo(() => {
    let cumulative = 0
    return entries.map((entry) => {
      if (entry.event_type === 'result_summary') {
        cumulative += entry.api_total_cost_usd ?? 0
      }
      return { entry, runningTotal: cumulative }
    })
  }, [entries])

  // Auto-scroll the log to the bottom when new entries arrive
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight
    }
  }, [entries.length])

  // Load the full summary (with per-tool breakdown) from the REST API
  const handleLoadSummary = useCallback(async () => {
    if (!conversationId) return
    setIsLoadingSummary(true)
    try {
      const data = await getTokenLogSummary(conversationId)
      setSummary(data)
      setShowBreakdown(true)
    } catch {
      // Silently fail -- summary is a nice-to-have
    } finally {
      setIsLoadingSummary(false)
    }
  }, [conversationId])

  // Clear the token log via the REST API and reset local state
  const handleClear = useCallback(async () => {
    if (!conversationId) return
    setIsClearing(true)
    try {
      await clearTokenLogApi(conversationId)
      setSummary(null)
      setShowBreakdown(false)
      onClear?.()
    } catch {
      // Silently fail
    } finally {
      setIsClearing(false)
    }
  }, [conversationId, onClear])

  return (
    <div
      className="flex-shrink-0 flex flex-col h-full border-r border-border bg-card/60 animate-slide-in relative"
      style={{ width: `${panelWidth}px` }}
    >
      {/* Drag handle on left edge for resizing */}
      <div
        onMouseDown={handleResizeStart}
        className="absolute top-0 left-0 w-1.5 h-full cursor-col-resize z-10 hover:bg-primary/30 active:bg-primary/50 transition-colors"
        title="Drag to resize"
      />
      {/* Panel header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-border bg-card">
        <div className="flex items-center gap-2">
          <ScrollText size={14} className="text-muted-foreground" />
          <span className="text-xs font-semibold text-foreground">Token Log</span>
          <span className="text-[10px] text-muted-foreground tabular-nums">
            ({entries.length})
          </span>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="p-0.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
            aria-label="Close token log"
          >
            <X size={14} />
          </button>
        )}
      </div>

      {/* Compact cumulative totals */}
      <div className="px-3 py-2 border-b border-border/50">
        <TokenLogTotals entries={entries} summary={summary} />
      </div>

      {/* Action buttons */}
      <div className="flex gap-1.5 px-3 py-1.5 border-b border-border/50">
        <button
          onClick={handleLoadSummary}
          disabled={isLoadingSummary || !conversationId}
          className="flex items-center gap-1 px-2 py-0.5 text-[10px] rounded border border-border bg-muted/50 hover:bg-muted text-foreground transition-colors disabled:opacity-50"
        >
          {isLoadingSummary ? (
            <Loader2 size={9} className="animate-spin" />
          ) : (
            <Download size={9} />
          )}
          {summary ? 'Refresh' : 'Summary'}
        </button>
        <button
          onClick={handleClear}
          disabled={isClearing || !conversationId}
          className="flex items-center gap-1 px-2 py-0.5 text-[10px] rounded border border-border bg-muted/50 hover:bg-destructive/10 hover:text-destructive hover:border-destructive/30 text-muted-foreground transition-colors disabled:opacity-50"
        >
          {isClearing ? (
            <Loader2 size={9} className="animate-spin" />
          ) : (
            <Trash2 size={9} />
          )}
          Clear
        </button>
      </div>

      {/* Per-tool breakdown (loaded from API) */}
      {showBreakdown && summary && summary.per_tool_breakdown.length > 0 && (
        <div className="px-3 py-2 border-b border-border/50 overflow-y-auto max-h-40">
          <ToolBreakdownTable breakdown={summary.per_tool_breakdown} />
        </div>
      )}

      {/* Column header */}
      <div className="flex items-center gap-1.5 px-2 py-1 text-[9px] text-muted-foreground/60 font-medium border-b border-border/50 bg-muted/20">
        <span className="w-4 text-right">#</span>
        <span className="flex-1">Time / Type / Details</span>
        <span className="flex-shrink-0 text-right">+Turn / Total</span>
      </div>

      {/* Scrollable log entries -- takes remaining vertical space */}
      <div
        ref={logContainerRef}
        className="flex-1 overflow-y-auto min-h-0"
      >
        {entries.length === 0 ? (
          <div className="py-8 px-4 text-center text-[10px] text-muted-foreground/60">
            No token log entries yet. Events will appear here as the agent processes your message.
          </div>
        ) : (
          entriesWithTotals.map(({ entry, runningTotal }) => (
            <TokenLogRow
              key={entry.id}
              entry={entry}
              runningTotal={runningTotal}
            />
          ))
        )}
      </div>

      {/* Legend at bottom */}
      <div className="flex items-center justify-center gap-3 px-3 py-1.5 border-t border-border/50 bg-card/80">
        <span className="flex items-center gap-1 text-[9px] text-muted-foreground/70">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-500" />
          Turn
        </span>
        <span className="flex items-center gap-1 text-[9px] text-muted-foreground/70">
          <span className="w-1.5 h-1.5 rounded-full bg-yellow-500" />
          Call
        </span>
        <span className="flex items-center gap-1 text-[9px] text-muted-foreground/70">
          <span className="w-1.5 h-1.5 rounded-full bg-orange-500" />
          Result
        </span>
        <span className="flex items-center gap-1 text-[9px] text-muted-foreground/70">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          Summary
        </span>
      </div>
    </div>
  )
}
