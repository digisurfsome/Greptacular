/**
 * TokenBudgetPage - Dashboard for viewing token usage against subscription windows.
 *
 * Full-page layout at /#/token-budget showing:
 * - 3-column grid of window cards (5-hour, weekly, monthly) with gauge bars
 * - "I Hit the Wall" calibration button in the header
 * - Recent sessions table with relative timestamps
 *
 * Follows WORKSPACE_STANDARDS.md layout patterns.
 */

import { useState, useEffect } from 'react'
import {
  ArrowLeft,
  ChevronRight,
  Zap,
  AlertTriangle,
  Clock,
  CalendarDays,
  CalendarRange,
  Activity,
  Check,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  useTokenBudgetStatus,
  useTokenBudgetHistory,
  useCalibrateTokenBudget,
} from '../hooks/useTokenBudget'
import type { TokenBudgetWindow, TokenBudgetSession } from '../lib/types'

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** Rough estimated token limits per window for gauge bar display. */
const WINDOW_LIMITS = {
  five_hour: 500_000,
  weekly: 5_000_000,
  monthly: 20_000_000,
} as const

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Format a token count into a short human-readable string (e.g. 31.7K, 1.2M). */
function formatTokens(n: number): string {
  if (n >= 1_000_000) {
    return `${(n / 1_000_000).toFixed(1)}M`
  }
  if (n >= 1_000) {
    return `${(n / 1_000).toFixed(1)}K`
  }
  return String(n)
}

/** Format USD cost as a compact dollar string. */
function formatCost(usd: number): string {
  if (usd < 0.01 && usd > 0) return '<$0.01'
  return `$${usd.toFixed(2)}`
}

/** Format an ISO timestamp as a relative time string (e.g. "2m ago"). */
function formatRelativeTime(isoTimestamp: string): string {
  const now = Date.now()
  const then = new Date(isoTimestamp).getTime()
  const diffMs = now - then

  const seconds = Math.floor(diffMs / 1000)
  if (seconds < 60) return `${seconds}s ago`

  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`

  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`

  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

/**
 * Determine the gauge bar color class based on percentage of window used.
 * Green <50%, Yellow 50-75%, Orange 75-90%, Red >90%.
 */
function gaugeColor(pct: number): string {
  if (pct >= 90) return 'bg-red-500'
  if (pct >= 75) return 'bg-orange-500'
  if (pct >= 50) return 'bg-yellow-500'
  return 'bg-green-500'
}

/**
 * Determine the text color class for the percentage label.
 */
function gaugeTextColor(pct: number): string {
  if (pct >= 90) return 'text-red-600'
  if (pct >= 75) return 'text-orange-600'
  if (pct >= 50) return 'text-yellow-600'
  return 'text-green-600'
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/** A single window usage card with gauge bar. */
function WindowCard({
  label,
  icon: Icon,
  window: w,
  limit,
}: {
  label: string
  icon: React.ElementType
  window: TokenBudgetWindow
  limit: number
}) {
  const pct = Math.min((w.total_tokens / Math.max(limit, 1)) * 100, 100)

  return (
    <div className="bg-card border-2 border-border rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Icon size={16} className="text-muted-foreground" />
          <span className="text-sm font-semibold text-foreground">{label}</span>
        </div>
        <span className={`text-xs font-bold ${gaugeTextColor(pct)}`}>
          {pct.toFixed(0)}%
        </span>
      </div>

      {/* Total tokens */}
      <div className="flex items-baseline gap-1.5 mb-3">
        <span className="text-2xl font-semibold text-foreground">
          {formatTokens(w.total_tokens)}
        </span>
        <span className="text-sm text-muted-foreground">
          / {formatTokens(limit)}
        </span>
      </div>

      {/* Gauge bar */}
      <div className="h-2.5 bg-muted rounded-full overflow-hidden mb-4">
        <div
          className={`h-full ${gaugeColor(pct)} rounded-full transition-all`}
          style={{ width: `${pct}%` }}
        />
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 gap-3 text-xs text-muted-foreground">
        <div>
          <span className="block font-medium text-foreground">{w.session_count}</span>
          <span>{w.session_count === 1 ? 'session' : 'sessions'}</span>
        </div>
        <div>
          <span className="block font-medium text-foreground">{formatCost(w.cost_usd)}</span>
          <span>est. cost</span>
        </div>
        <div>
          <span className="block font-medium text-foreground">{formatTokens(w.input_tokens)}</span>
          <span>input</span>
        </div>
        <div>
          <span className="block font-medium text-foreground">{formatTokens(w.output_tokens)}</span>
          <span>output</span>
        </div>
      </div>
    </div>
  )
}

/** Sessions table row. */
function SessionRow({ session }: { session: TokenBudgetSession }) {
  return (
    <tr className="border-b border-border last:border-b-0 hover:bg-muted/50 transition-colors">
      <td className="py-2.5 px-3 text-xs text-muted-foreground whitespace-nowrap">
        {formatRelativeTime(session.timestamp)}
      </td>
      <td className="py-2.5 px-3 text-xs text-foreground">
        {session.session_type}
      </td>
      <td className="py-2.5 px-3 text-xs text-foreground">
        {session.model}
      </td>
      <td className="py-2.5 px-3 text-xs font-medium text-foreground text-right whitespace-nowrap">
        {formatTokens(session.total_tokens)}
      </td>
      <td className="py-2.5 px-3 text-xs text-muted-foreground text-right whitespace-nowrap">
        {formatCost(session.cost_usd)}
      </td>
      <td className="py-2.5 px-3 text-xs text-muted-foreground truncate max-w-[140px]">
        {session.project_name ?? '-'}
      </td>
    </tr>
  )
}

/** Loading skeleton matching the page layout. */
function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      {/* Window cards skeleton */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="animate-pulse bg-muted rounded-lg h-52" />
        ))}
      </div>
      {/* Table skeleton */}
      <div className="animate-pulse bg-muted rounded-lg h-64" />
    </div>
  )
}

/** Empty state when no sessions recorded. */
function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <Activity className="w-12 h-12 text-muted-foreground mb-4" />
      <h3 className="text-lg font-medium text-foreground mb-1">No token usage recorded yet</h3>
      <p className="text-sm text-muted-foreground mb-4">
        Token usage will appear here once AutoForge starts running agent sessions.
      </p>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Page component
// ---------------------------------------------------------------------------

export function TokenBudgetPage() {
  const { data: status, isLoading: statusLoading } = useTokenBudgetStatus()
  const { data: history, isLoading: historyLoading } = useTokenBudgetHistory(50)
  const calibrateMutation = useCalibrateTokenBudget()

  // "Recorded!" flash state for the calibrate button
  const [showRecorded, setShowRecorded] = useState(false)

  useEffect(() => {
    if (showRecorded) {
      const timer = setTimeout(() => setShowRecorded(false), 2000)
      return () => clearTimeout(timer)
    }
  }, [showRecorded])

  const handleCalibrate = () => {
    calibrateMutation.mutate(
      { windowType: '5hour', notes: 'User reported hitting rate limit wall' },
      { onSuccess: () => setShowRecorded(true) },
    )
  }

  const isLoading = statusLoading || historyLoading
  const hasData = status && (
    status.five_hour.total_tokens > 0 ||
    status.weekly.total_tokens > 0 ||
    status.monthly.total_tokens > 0
  )

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Breadcrumb bar */}
      <div className="flex items-center h-10 px-3 border-b border-border bg-card shrink-0">
        <nav className="flex items-center gap-1 text-sm">
          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5 text-muted-foreground hover:text-foreground h-7 px-2"
            onClick={() => { window.location.hash = '' }}
          >
            <ArrowLeft size={14} />
            <span className="text-xs">Back</span>
          </Button>
          <ChevronRight size={12} className="text-muted-foreground" />
          <Zap size={14} className="text-foreground" />
          <span className="text-xs font-semibold text-foreground">Token Budget</span>
        </nav>

        {/* Right side: calibrate button */}
        <div className="ml-auto flex items-center gap-2">
          {showRecorded ? (
            <span className="inline-flex items-center gap-1 text-xs font-bold text-green-600 px-3 py-1">
              <Check size={14} />
              Recorded!
            </span>
          ) : (
            <Button
              variant="default"
              size="sm"
              className="h-7 px-3 bg-red-500 hover:bg-red-600 text-white font-bold text-xs border-0"
              onClick={handleCalibrate}
              disabled={calibrateMutation.isPending}
            >
              <AlertTriangle size={12} className="mr-1" />
              I Hit the Wall
            </Button>
          )}
        </div>
      </div>

      {/* Main scrollable content */}
      <main className="flex-1 overflow-auto p-6">
        <div className="max-w-7xl mx-auto">
          {isLoading ? (
            <LoadingSkeleton />
          ) : !hasData ? (
            <EmptyState />
          ) : (
            <div className="space-y-6">
              {/* Window cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                <WindowCard
                  label="5-Hour Window"
                  icon={Clock}
                  window={status!.five_hour}
                  limit={WINDOW_LIMITS.five_hour}
                />
                <WindowCard
                  label="Weekly"
                  icon={CalendarDays}
                  window={status!.weekly}
                  limit={WINDOW_LIMITS.weekly}
                />
                <WindowCard
                  label="Monthly"
                  icon={CalendarRange}
                  window={status!.monthly}
                  limit={WINDOW_LIMITS.monthly}
                />
              </div>

              {/* Recent sessions table */}
              {history && history.sessions.length > 0 && (
                <div className="bg-card border-2 border-border rounded-lg overflow-hidden">
                  <div className="px-4 py-3 border-b border-border">
                    <h2 className="text-sm font-semibold text-foreground">Recent Sessions</h2>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left">
                      <thead>
                        <tr className="border-b border-border bg-muted/50">
                          <th className="py-2 px-3 text-xs font-medium text-muted-foreground">Time</th>
                          <th className="py-2 px-3 text-xs font-medium text-muted-foreground">Type</th>
                          <th className="py-2 px-3 text-xs font-medium text-muted-foreground">Model</th>
                          <th className="py-2 px-3 text-xs font-medium text-muted-foreground text-right">Tokens</th>
                          <th className="py-2 px-3 text-xs font-medium text-muted-foreground text-right">Cost</th>
                          <th className="py-2 px-3 text-xs font-medium text-muted-foreground">Project</th>
                        </tr>
                      </thead>
                      <tbody>
                        {history.sessions.map((session) => (
                          <SessionRow key={session.id} session={session} />
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Calibrations section (if any exist) */}
              {history && history.calibrations.length > 0 && (
                <div className="bg-card border-2 border-border rounded-lg overflow-hidden">
                  <div className="px-4 py-3 border-b border-border">
                    <h2 className="text-sm font-semibold text-foreground">Rate Limit Calibrations</h2>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left">
                      <thead>
                        <tr className="border-b border-border bg-muted/50">
                          <th className="py-2 px-3 text-xs font-medium text-muted-foreground">Time</th>
                          <th className="py-2 px-3 text-xs font-medium text-muted-foreground">Window</th>
                          <th className="py-2 px-3 text-xs font-medium text-muted-foreground text-right">Tokens at Wall</th>
                          <th className="py-2 px-3 text-xs font-medium text-muted-foreground">Notes</th>
                        </tr>
                      </thead>
                      <tbody>
                        {history.calibrations.map((cal) => (
                          <tr
                            key={cal.id}
                            className="border-b border-border last:border-b-0 hover:bg-muted/50 transition-colors"
                          >
                            <td className="py-2.5 px-3 text-xs text-muted-foreground whitespace-nowrap">
                              {formatRelativeTime(cal.timestamp)}
                            </td>
                            <td className="py-2.5 px-3 text-xs text-foreground">
                              {cal.window_type}
                            </td>
                            <td className="py-2.5 px-3 text-xs font-medium text-foreground text-right">
                              {formatTokens(cal.tracked_total)}
                            </td>
                            <td className="py-2.5 px-3 text-xs text-muted-foreground truncate max-w-[200px]">
                              {cal.notes ?? '-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
