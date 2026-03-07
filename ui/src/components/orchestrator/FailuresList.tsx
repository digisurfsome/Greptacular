/**
 * FailuresList - Table of recent verification failures.
 *
 * Shows failed test/lint/typecheck results with feature name (clickable),
 * test type badge, and timestamp. Includes a filter dropdown by test type.
 * Uses a positive empty state ("All clear") when there are no failures.
 *
 * Portable widget: receives all data via props, no page-specific hooks.
 */

import { useState } from 'react'
import { CheckCircle, XCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import { timeAgo } from './timeAgo'
import type { VerificationResult } from '../../lib/types'

export interface FailuresListProps {
  failures: VerificationResult[]
  onNavigateToFeature?: (featureId: number) => void
  isLoading?: boolean
}

const TYPE_COLORS: Record<VerificationResult['test_type'], string> = {
  lint: 'bg-blue-500/20 text-blue-700 dark:text-blue-400 border-blue-500/30',
  typecheck: 'bg-purple-500/20 text-purple-700 dark:text-purple-400 border-purple-500/30',
  e2e: 'bg-cyan-500/20 text-cyan-700 dark:text-cyan-400 border-cyan-500/30',
  manual: 'bg-gray-500/20 text-gray-600 dark:text-gray-400 border-gray-500/30',
}

function SkeletonRow() {
  return (
    <tr className="animate-pulse">
      <td className="px-3 py-2"><div className="h-4 w-32 rounded bg-muted" /></td>
      <td className="px-3 py-2"><div className="h-5 w-16 rounded-full bg-muted" /></td>
      <td className="px-3 py-2"><div className="h-4 w-14 rounded bg-muted" /></td>
    </tr>
  )
}

export function FailuresList({ failures, onNavigateToFeature, isLoading }: FailuresListProps) {
  const [typeFilter, setTypeFilter] = useState<VerificationResult['test_type'] | 'all'>('all')

  const filtered = typeFilter === 'all'
    ? failures
    : failures.filter(f => f.test_type === typeFilter)

  return (
    <div className="bg-card text-card-foreground rounded-xl border shadow-sm">
      {/* Header with filter */}
      <div className="flex items-center gap-3 px-4 py-3 border-b">
        <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
          <XCircle className="size-4 text-red-500" />
          Recent Failures
        </h3>
        <div className="ml-auto">
          <select
            className={cn(
              'h-8 rounded-md border border-input bg-background px-2 text-xs',
              'focus:outline-none focus:ring-2 focus:ring-ring',
            )}
            value={typeFilter}
            onChange={e => setTypeFilter(e.target.value as VerificationResult['test_type'] | 'all')}
          >
            <option value="all">All types</option>
            <option value="lint">Lint</option>
            <option value="typecheck">Typecheck</option>
            <option value="e2e">E2E</option>
            <option value="manual">Manual</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b text-muted-foreground">
              <th className="px-3 py-2 text-left font-medium">Feature</th>
              <th className="px-3 py-2 text-left font-medium">Type</th>
              <th className="px-3 py-2 text-left font-medium">When</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <>
                <SkeletonRow />
                <SkeletonRow />
                <SkeletonRow />
              </>
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={3} className="px-3 py-12 text-center">
                  <div className="flex flex-col items-center gap-2 text-muted-foreground">
                    <CheckCircle className="size-8 text-emerald-500 opacity-60" />
                    <p className="text-sm font-medium text-emerald-700 dark:text-emerald-400">
                      All clear — no recent failures
                    </p>
                    <p className="text-xs">Everything is passing. Keep it up!</p>
                  </div>
                </td>
              </tr>
            ) : (
              filtered.map(f => {
                const featureLabel = f.feature_name || `Feature #${f.feature_id}`
                const isClickable = !!onNavigateToFeature

                return (
                  <tr
                    key={f.id}
                    className="border-b border-border/50 last:border-0 hover:bg-muted/50 transition-colors"
                  >
                    <td className="px-3 py-2">
                      {isClickable ? (
                        <button
                          className="text-primary hover:underline font-medium"
                          onClick={() => onNavigateToFeature!(f.feature_id)}
                        >
                          {featureLabel}
                        </button>
                      ) : (
                        <span className="text-foreground">{featureLabel}</span>
                      )}
                    </td>
                    <td className="px-3 py-2">
                      <Badge
                        variant="outline"
                        className={cn('text-[10px] capitalize', TYPE_COLORS[f.test_type])}
                      >
                        {f.test_type}
                      </Badge>
                    </td>
                    <td className="px-3 py-2 text-muted-foreground">
                      {timeAgo(f.created_at)}
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
