/**
 * Token Processing Log Panel
 *
 * Collapsible panel that shows exactly where every token goes in a
 * workspace conversation. Receives real-time entries via WebSocket
 * and can load the full log + per-tool breakdown from the REST API.
 *
 * Designed for debugging and auditing token usage -- information-dense
 * layout following the existing neobrutalism/collapsible panel pattern
 * used by UsageDashboard and CostControls.
 */

import { useState, useMemo, useCallback, useEffect, useRef } from 'react'
import {
  ChevronDown,
  ChevronUp,
  ScrollText,
  Download,
  Trash2,
  BarChart3,
  Loader2,
} from 'lucide-react'
import { getTokenLogSummary, clearTokenLog as clearTokenLogApi } from '@/lib/api'
import type { TokenLogEntry, TokenLogSummary, TokenLogToolBreakdown } from '@/lib/types'

// -- Helpers ------------------------------------------------------------------

/** Format a token count with commas for readability (e.g. 1,234,567). */
function formatTokens(n: number): string {
  return n.toLocaleString()
}

/** Compact token format for the collapsed summary row. */
function formatTokensCompact(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return String(n)
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

// -- Sub-components -----------------------------------------------------------

/** Cumulative totals summary shown at the top of the expanded panel. */
function TokenLogTotals({
  entries,
  summary,
}: {
  entries: TokenLogEntry[]
  summary: TokenLogSummary | null
}) {
  // Compute running totals from live entries
  const totals = useMemo(() => {
    let estimatedTokens = 0
    let apiInput = 0
    let apiOutput = 0
    let cacheCreation = 0
    let cacheRead = 0
    let totalCost = 0
    let turns = 0

    for (const e of entries) {
      estimatedTokens += e.estimated_tokens
      if (e.event_type === 'result_summary') {
        apiInput += e.api_input_tokens ?? 0
        apiOutput += e.api_output_tokens ?? 0
        cacheCreation += e.api_cache_creation_tokens ?? 0
        cacheRead += e.api_cache_read_tokens ?? 0
        totalCost += e.api_total_cost_usd ?? 0
        turns += e.api_num_turns ?? 0
      }
    }

    return { estimatedTokens, apiInput, apiOutput, cacheCreation, cacheRead, totalCost, turns }
  }, [entries])

  // Prefer summary from API when available (more accurate), fall back to live totals
  const data = summary
    ? {
        estimatedTokens: summary.total_estimated_tokens,
        apiInput: summary.total_api_input_tokens,
        apiOutput: summary.total_api_output_tokens,
        cacheCreation: summary.total_api_cache_creation_tokens,
        cacheRead: summary.total_api_cache_read_tokens,
        totalCost: summary.total_cost_usd,
        turns: entries.filter(e => e.event_type === 'assistant_turn').length,
      }
    : totals

  return (
    <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-[10px]">
      <div className="flex justify-between">
        <span className="text-muted-foreground">Est. tokens:</span>
        <span className="font-mono font-bold text-foreground tabular-nums">
          {formatTokens(data.estimatedTokens)}
        </span>
      </div>
      <div className="flex justify-between">
        <span className="text-muted-foreground">API input:</span>
        <span className="font-mono font-bold text-foreground tabular-nums">
          {formatTokens(data.apiInput)}
        </span>
      </div>
      <div className="flex justify-between">
        <span className="text-muted-foreground">API output:</span>
        <span className="font-mono font-bold text-foreground tabular-nums">
          {formatTokens(data.apiOutput)}
        </span>
      </div>
      <div className="flex justify-between">
        <span className="text-muted-foreground">Cache create:</span>
        <span className="font-mono font-bold text-foreground tabular-nums">
          {formatTokens(data.cacheCreation)}
        </span>
      </div>
      <div className="flex justify-between">
        <span className="text-muted-foreground">Cache read:</span>
        <span className="font-mono font-bold text-foreground tabular-nums">
          {formatTokens(data.cacheRead)}
        </span>
      </div>
      <div className="flex justify-between">
        <span className="text-muted-foreground">Total cost:</span>
        <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400 tabular-nums">
          {formatCost(data.totalCost)}
        </span>
      </div>
    </div>
  )
}

/** Per-tool breakdown table. */
function ToolBreakdownTable({ breakdown }: { breakdown: TokenLogToolBreakdown[] }) {
  if (breakdown.length === 0) return null

  // Sort by total estimated tokens descending to highlight the most expensive tools
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
              <th className="text-right py-1 px-1.5 text-muted-foreground font-medium">Calls</th>
              <th className="text-right py-1 px-1.5 text-muted-foreground font-medium">Input Tok</th>
              <th className="text-right py-1 px-1.5 text-muted-foreground font-medium">Result Tok</th>
              <th className="text-right py-1 pl-1.5 text-muted-foreground font-medium">Est. Total</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((row) => (
              <tr key={row.tool_name} className="border-b border-border/50 hover:bg-muted/30">
                <td className="py-1 pr-2 font-mono text-foreground">
                  {row.tool_name}
                  {row.error_count > 0 && (
                    <span className="ml-1 text-destructive">({row.error_count} err)</span>
                  )}
                </td>
                <td className="py-1 px-1.5 text-right font-mono tabular-nums text-foreground">
                  {row.call_count}
                </td>
                <td className="py-1 px-1.5 text-right font-mono tabular-nums text-muted-foreground">
                  {formatTokens(row.total_input_tokens)}
                </td>
                <td className="py-1 px-1.5 text-right font-mono tabular-nums text-muted-foreground">
                  {formatTokens(row.total_result_tokens)}
                </td>
                <td className="py-1 pl-1.5 text-right font-mono tabular-nums font-bold text-foreground">
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

/** Single log entry row. */
function TokenLogRow({ entry }: { entry: TokenLogEntry }) {
  const time = new Date(entry.timestamp).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })

  const isSummary = entry.event_type === 'result_summary'

  return (
    <div className="flex items-start gap-2 py-1 border-b border-border/30 hover:bg-muted/20 transition-colors text-[10px]">
      {/* Turn number */}
      <span className="flex-shrink-0 w-5 text-right font-mono tabular-nums text-muted-foreground">
        {entry.turn_number}
      </span>

      {/* Timestamp */}
      <span className="flex-shrink-0 w-16 font-mono tabular-nums text-muted-foreground/70">
        {time}
      </span>

      {/* Event type badge */}
      <span className={`flex-shrink-0 px-1.5 py-0.5 rounded text-[9px] font-semibold border ${eventTypeColor(entry.event_type)}`}>
        {eventTypeLabel(entry.event_type)}
      </span>

      {/* Tool name or text info */}
      <div className="flex-1 min-w-0 space-y-0.5">
        {entry.tool_name && (
          <span className="font-mono text-foreground">
            {entry.tool_name}
            {entry.tool_is_error && (
              <span className="ml-1 text-destructive font-bold">ERR</span>
            )}
          </span>
        )}

        {/* Details for different event types */}
        {entry.event_type === 'tool_call' && entry.tool_input_length != null && (
          <span className="text-muted-foreground ml-1">
            input: {formatTokens(entry.tool_input_length)} chars
          </span>
        )}
        {entry.event_type === 'tool_result' && entry.tool_result_length != null && (
          <span className="text-muted-foreground ml-1">
            result: {formatTokens(entry.tool_result_length)} chars
          </span>
        )}
        {entry.event_type === 'assistant_turn' && (
          <span className="text-muted-foreground">
            {entry.text_length != null && `${formatTokens(entry.text_length)} chars`}
            {entry.num_tool_calls != null && entry.num_tool_calls > 0 && (
              <span className="ml-1">+ {entry.num_tool_calls} tool call{entry.num_tool_calls !== 1 ? 's' : ''}</span>
            )}
          </span>
        )}

        {/* Summary line with API actuals */}
        {isSummary && (
          <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-muted-foreground mt-0.5">
            {entry.api_input_tokens != null && (
              <span>in: <span className="font-mono text-foreground">{formatTokens(entry.api_input_tokens)}</span></span>
            )}
            {entry.api_output_tokens != null && (
              <span>out: <span className="font-mono text-foreground">{formatTokens(entry.api_output_tokens)}</span></span>
            )}
            {entry.api_cache_read_tokens != null && entry.api_cache_read_tokens > 0 && (
              <span>cache: <span className="font-mono text-foreground">{formatTokens(entry.api_cache_read_tokens)}</span></span>
            )}
            {entry.api_total_cost_usd != null && (
              <span>cost: <span className="font-mono text-emerald-600 dark:text-emerald-400 font-bold">{formatCost(entry.api_total_cost_usd)}</span></span>
            )}
            {entry.api_duration_ms != null && (
              <span>time: <span className="font-mono text-foreground">{formatDuration(entry.api_duration_ms)}</span></span>
            )}
            {entry.model && (
              <span className="text-muted-foreground/60">{entry.model}</span>
            )}
          </div>
        )}
      </div>

      {/* Estimated tokens (right-aligned) */}
      <span className="flex-shrink-0 w-16 text-right font-mono tabular-nums font-bold text-foreground">
        {formatTokens(entry.estimated_tokens)}
      </span>
    </div>
  )
}

// -- Main Component -----------------------------------------------------------

interface TokenLogPanelProps {
  /** Real-time token log entries received via WebSocket. */
  entries: TokenLogEntry[]
  /** Active conversation ID (required for REST API calls). */
  conversationId: number | null
}

export function TokenLogPanel({ entries, conversationId }: TokenLogPanelProps): React.JSX.Element {
  const [expanded, setExpanded] = useState(false)
  const [summary, setSummary] = useState<TokenLogSummary | null>(null)
  const [isLoadingSummary, setIsLoadingSummary] = useState(false)
  const [isClearing, setIsClearing] = useState(false)
  const logContainerRef = useRef<HTMLDivElement>(null)

  // Compute a quick cumulative estimated tokens total from live entries
  const totalEstimated = useMemo(
    () => entries.reduce((sum, e) => sum + e.estimated_tokens, 0),
    [entries],
  )

  // Compute total cost from result_summary entries
  const totalCost = useMemo(
    () =>
      entries
        .filter((e) => e.event_type === 'result_summary')
        .reduce((sum, e) => sum + (e.api_total_cost_usd ?? 0), 0),
    [entries],
  )

  // Auto-scroll the log to the bottom when new entries arrive
  useEffect(() => {
    if (expanded && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight
    }
  }, [entries.length, expanded])

  // Load the full summary (with per-tool breakdown) from the REST API
  const handleLoadSummary = useCallback(async () => {
    if (!conversationId) return
    setIsLoadingSummary(true)
    try {
      const data = await getTokenLogSummary(conversationId)
      setSummary(data)
    } catch {
      // Silently fail -- summary is a nice-to-have
    } finally {
      setIsLoadingSummary(false)
    }
  }, [conversationId])

  // Clear the token log via the REST API
  const handleClear = useCallback(async () => {
    if (!conversationId) return
    setIsClearing(true)
    try {
      await clearTokenLogApi(conversationId)
      setSummary(null)
    } catch {
      // Silently fail
    } finally {
      setIsClearing(false)
    }
  }, [conversationId])

  // Don't render if there are no entries and no conversation
  if (entries.length === 0 && !conversationId) {
    return <></>
  }

  return (
    <div className="border-b border-border bg-card/40">
      {/* Collapsed: compact summary row */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center justify-between w-full px-4 py-1.5 text-left hover:bg-muted/30 transition-colors"
      >
        <div className="flex items-center gap-3">
          <ScrollText size={12} className="text-muted-foreground" />
          <span className="text-[10px] text-muted-foreground">
            Token Log:{' '}
            <span className="font-mono font-bold text-foreground tabular-nums">
              {formatTokensCompact(totalEstimated)}
            </span>
            <span className="text-muted-foreground/70 ml-1">
              ({entries.length} event{entries.length !== 1 ? 's' : ''})
            </span>
          </span>
          {totalCost > 0 && (
            <span className="text-[10px] font-mono text-emerald-600 dark:text-emerald-400 font-bold tabular-nums">
              {formatCost(totalCost)}
            </span>
          )}
        </div>
        {expanded ? (
          <ChevronUp size={12} className="text-muted-foreground" />
        ) : (
          <ChevronDown size={12} className="text-muted-foreground" />
        )}
      </button>

      {/* Expanded: full log panel */}
      {expanded && (
        <div className="px-4 pb-3 space-y-3 border-t border-border/50 pt-2">
          {/* Cumulative totals */}
          <div className="space-y-1.5">
            <div className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
              Cumulative Totals
            </div>
            <TokenLogTotals entries={entries} summary={summary} />
          </div>

          {/* Per-tool breakdown (loaded from API) */}
          {summary && summary.per_tool_breakdown.length > 0 && (
            <ToolBreakdownTable breakdown={summary.per_tool_breakdown} />
          )}

          {/* Action buttons */}
          <div className="flex gap-2">
            <button
              onClick={handleLoadSummary}
              disabled={isLoadingSummary || !conversationId}
              className="flex items-center gap-1 px-2 py-1 text-[10px] rounded border border-border bg-muted/50 hover:bg-muted text-foreground transition-colors disabled:opacity-50"
            >
              {isLoadingSummary ? (
                <Loader2 size={9} className="animate-spin" />
              ) : (
                <Download size={9} />
              )}
              {isLoadingSummary ? 'Loading...' : summary ? 'Refresh Summary' : 'Load Full Summary'}
            </button>
            <button
              onClick={handleClear}
              disabled={isClearing || !conversationId}
              className="flex items-center gap-1 px-2 py-1 text-[10px] rounded border border-border bg-muted/50 hover:bg-destructive/10 hover:text-destructive hover:border-destructive/30 text-muted-foreground transition-colors disabled:opacity-50"
            >
              {isClearing ? (
                <Loader2 size={9} className="animate-spin" />
              ) : (
                <Trash2 size={9} />
              )}
              {isClearing ? 'Clearing...' : 'Clear Log'}
            </button>
          </div>

          {/* Live event log */}
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <div className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                Event Log
              </div>
              <div className="flex items-center gap-3 text-[9px] text-muted-foreground/70">
                <span className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-500" />
                  Turn
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-yellow-500" />
                  Call
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-orange-500" />
                  Result
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                  Summary
                </span>
              </div>
            </div>

            {/* Column header row */}
            <div className="flex items-center gap-2 py-0.5 text-[9px] text-muted-foreground/60 font-medium border-b border-border/50">
              <span className="flex-shrink-0 w-5 text-right">#</span>
              <span className="flex-shrink-0 w-16">Time</span>
              <span className="flex-shrink-0 w-14">Type</span>
              <span className="flex-1">Details</span>
              <span className="flex-shrink-0 w-16 text-right">Est. Tok</span>
            </div>

            {/* Scrollable log entries */}
            <div
              ref={logContainerRef}
              className="max-h-64 overflow-y-auto"
            >
              {entries.length === 0 ? (
                <div className="py-4 text-center text-[10px] text-muted-foreground/60">
                  No token log entries yet. Events will appear here as the agent processes your message.
                </div>
              ) : (
                entries.map((entry) => (
                  <TokenLogRow key={entry.id} entry={entry} />
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
