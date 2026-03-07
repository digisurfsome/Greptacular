/**
 * ActionLogSummaryCard - Summary stats for agent action logs.
 *
 * Displays 4 mini-cards in a 2x2 grid: Total Calls, Error Rate (%),
 * Average Duration (ms), and Most Used Tool. Error rate is color-coded:
 * green (<5%), yellow (5-15%), red (>15%).
 *
 * Portable widget: receives all data via props, no page-specific hooks.
 */

import { Activity, AlertTriangle, Clock, Wrench } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ActionLogSummary } from '../../lib/types'

export interface ActionLogSummaryProps {
  summary: ActionLogSummary | null
  isLoading?: boolean
}

function SkeletonCard() {
  return (
    <div className="rounded-lg border bg-card p-3 animate-pulse">
      <div className="h-3 w-16 rounded bg-muted mb-2" />
      <div className="h-6 w-12 rounded bg-muted" />
    </div>
  )
}

/** Return the Tailwind text color class for the error rate. */
function errorRateColor(rate: number): string {
  if (rate < 5) return 'text-emerald-600 dark:text-emerald-400'
  if (rate <= 15) return 'text-yellow-600 dark:text-yellow-400'
  return 'text-red-600 dark:text-red-400'
}

export function ActionLogSummaryCard({ summary, isLoading }: ActionLogSummaryProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 gap-3">
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </div>
    )
  }

  // Derive most-used tool from the tools array
  const mostUsedTool = summary?.tools && summary.tools.length > 0
    ? [...summary.tools].sort((a, b) => b.count - a.count)[0].tool_name
    : null

  const errorRate = summary ? summary.error_rate : null
  const formattedRate = errorRate != null ? `${errorRate.toFixed(1)}%` : '\u2014'

  return (
    <div className="grid grid-cols-2 gap-3">
      {/* Total Calls */}
      <div className="rounded-lg border bg-card p-3">
        <div className="flex items-center gap-1.5 mb-1">
          <Activity className="size-3 text-muted-foreground" />
          <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">
            Total Calls
          </span>
        </div>
        <p className="text-lg font-bold text-foreground">
          {summary?.total_calls ?? '\u2014'}
        </p>
      </div>

      {/* Error Rate */}
      <div className="rounded-lg border bg-card p-3">
        <div className="flex items-center gap-1.5 mb-1">
          <AlertTriangle className="size-3 text-muted-foreground" />
          <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">
            Error Rate
          </span>
        </div>
        <p className={cn('text-lg font-bold', errorRate != null ? errorRateColor(errorRate) : 'text-foreground')}>
          {formattedRate}
        </p>
      </div>

      {/* Avg Duration */}
      <div className="rounded-lg border bg-card p-3">
        <div className="flex items-center gap-1.5 mb-1">
          <Clock className="size-3 text-muted-foreground" />
          <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">
            Avg Duration
          </span>
        </div>
        <p className="text-lg font-bold text-foreground">
          {summary?.avg_duration_ms != null ? `${Math.round(summary.avg_duration_ms)}ms` : '\u2014'}
        </p>
      </div>

      {/* Most Used Tool */}
      <div className="rounded-lg border bg-card p-3">
        <div className="flex items-center gap-1.5 mb-1">
          <Wrench className="size-3 text-muted-foreground" />
          <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">
            Top Tool
          </span>
        </div>
        <p className="text-sm font-bold text-foreground font-mono truncate" title={mostUsedTool ?? undefined}>
          {mostUsedTool ?? '\u2014'}
        </p>
      </div>
    </div>
  )
}
