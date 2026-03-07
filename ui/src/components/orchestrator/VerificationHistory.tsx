/**
 * VerificationHistory - Chronological list of verification (test/lint) runs.
 *
 * Each entry shows the test type as a colored badge, pass/fail icon,
 * timestamp, and duration. Click to expand the output in a scrollable
 * dark code block (max 300px height).
 *
 * Portable widget: receives all data via props, no page-specific hooks.
 */

import { useState } from 'react'
import { ClipboardCheck, CheckCircle, XCircle, ChevronDown, ChevronUp } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import { timeAgo } from './timeAgo'
import type { VerificationResult } from '../../lib/types'

export interface VerificationHistoryProps {
  results: VerificationResult[]
  isLoading?: boolean
}

const TYPE_COLORS: Record<VerificationResult['test_type'], string> = {
  lint: 'bg-blue-500/20 text-blue-700 dark:text-blue-400 border-blue-500/30',
  typecheck: 'bg-purple-500/20 text-purple-700 dark:text-purple-400 border-purple-500/30',
  e2e: 'bg-cyan-500/20 text-cyan-700 dark:text-cyan-400 border-cyan-500/30',
  manual: 'bg-gray-500/20 text-gray-600 dark:text-gray-400 border-gray-500/30',
}

function SkeletonItem() {
  return (
    <div className="flex items-center gap-3 px-4 py-3 animate-pulse">
      <div className="h-5 w-16 rounded-full bg-muted" />
      <div className="h-4 w-4 rounded-full bg-muted" />
      <div className="h-4 w-20 rounded bg-muted" />
      <div className="ml-auto h-4 w-14 rounded bg-muted" />
    </div>
  )
}

export function VerificationHistory({ results, isLoading }: VerificationHistoryProps) {
  const [expandedId, setExpandedId] = useState<number | null>(null)

  return (
    <div className="bg-card text-card-foreground rounded-xl border shadow-sm">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b">
        <ClipboardCheck className="size-4 text-muted-foreground" />
        <h3 className="text-sm font-semibold text-foreground">Verification History</h3>
      </div>

      {isLoading ? (
        <div>
          <SkeletonItem />
          <SkeletonItem />
          <SkeletonItem />
        </div>
      ) : results.length === 0 ? (
        <div className="flex flex-col items-center gap-2 py-12 text-muted-foreground">
          <ClipboardCheck className="size-8 opacity-40" />
          <p className="text-sm font-medium">No verification results yet</p>
          <p className="text-xs">Test, lint, and typecheck results will appear here.</p>
        </div>
      ) : (
        <div className="divide-y divide-border/50">
          {results.map(result => {
            const isExpanded = expandedId === result.id

            return (
              <div key={result.id}>
                <button
                  className={cn(
                    'w-full flex items-center gap-3 px-4 py-3 text-left',
                    'hover:bg-muted/50 transition-colors',
                    isExpanded && 'bg-muted/30',
                  )}
                  onClick={() => setExpandedId(isExpanded ? null : result.id)}
                >
                  {/* Test type badge */}
                  <Badge
                    variant="outline"
                    className={cn('text-[10px] capitalize shrink-0', TYPE_COLORS[result.test_type])}
                  >
                    {result.test_type}
                  </Badge>

                  {/* Pass/fail icon */}
                  {result.passed ? (
                    <CheckCircle className="size-4 text-emerald-500 shrink-0" />
                  ) : (
                    <XCircle className="size-4 text-red-500 shrink-0" />
                  )}

                  {/* Timestamp */}
                  <span className="text-xs text-muted-foreground">
                    {timeAgo(result.created_at)}
                  </span>

                  {/* Feature name if available */}
                  {result.feature_name && (
                    <span className="text-xs text-foreground/70 truncate max-w-[150px]" title={result.feature_name}>
                      {result.feature_name}
                    </span>
                  )}

                  {/* Duration + expand icon on the right */}
                  <span className="ml-auto text-xs text-muted-foreground whitespace-nowrap">
                    {result.duration_ms != null ? `${result.duration_ms}ms` : ''}
                  </span>
                  {result.output && (
                    isExpanded
                      ? <ChevronUp className="size-3 text-muted-foreground shrink-0" />
                      : <ChevronDown className="size-3 text-muted-foreground shrink-0" />
                  )}
                </button>

                {/* Expanded output */}
                {isExpanded && result.output && (
                  <div className="px-4 pb-3">
                    <pre className="text-xs font-mono bg-zinc-900 text-zinc-100 p-3 rounded-md max-h-[300px] overflow-auto whitespace-pre-wrap">
                      {result.output}
                    </pre>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
