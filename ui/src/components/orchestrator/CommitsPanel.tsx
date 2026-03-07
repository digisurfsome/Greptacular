/**
 * CommitsPanel - List of parsed git commits with optional feature filtering.
 *
 * Shows each commit's short SHA (monospace), message, relative timestamp,
 * and a conventional-commit type badge when the commit message was parsed
 * successfully. A dropdown lets operators filter commits by linked feature.
 *
 * Portable widget: receives all data via props, no page-specific hooks.
 */

import { GitCommit as GitCommitIcon } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import { timeAgo } from './timeAgo'
import type { Commit } from '../../lib/types'

export interface CommitsPanelProps {
  commits: Commit[]
  featureFilter: number | null
  onFeatureFilterChange: (featureId: number | null) => void
  features?: { id: number; name: string }[]
  isLoading?: boolean
}

/** Map conventional commit type to a badge color. */
const TYPE_BADGE_COLORS: Record<string, string> = {
  feat: 'bg-emerald-500/20 text-emerald-700 dark:text-emerald-400 border-emerald-500/30',
  fix: 'bg-red-500/20 text-red-700 dark:text-red-400 border-red-500/30',
  test: 'bg-blue-500/20 text-blue-700 dark:text-blue-400 border-blue-500/30',
  refactor: 'bg-purple-500/20 text-purple-700 dark:text-purple-400 border-purple-500/30',
  chore: 'bg-gray-500/20 text-gray-600 dark:text-gray-400 border-gray-500/30',
  docs: 'bg-yellow-500/20 text-yellow-700 dark:text-yellow-400 border-yellow-500/30',
  style: 'bg-pink-500/20 text-pink-700 dark:text-pink-400 border-pink-500/30',
  perf: 'bg-orange-500/20 text-orange-700 dark:text-orange-400 border-orange-500/30',
  ci: 'bg-teal-500/20 text-teal-700 dark:text-teal-400 border-teal-500/30',
}

function SkeletonItem() {
  return (
    <div className="flex items-center gap-3 px-4 py-3 animate-pulse">
      <div className="h-4 w-14 rounded bg-muted" />
      <div className="h-4 w-48 rounded bg-muted flex-1" />
      <div className="h-4 w-12 rounded bg-muted" />
    </div>
  )
}

export function CommitsPanel({
  commits,
  featureFilter,
  onFeatureFilterChange,
  features,
  isLoading,
}: CommitsPanelProps) {
  // Apply feature filter
  const filtered = featureFilter != null
    ? commits.filter(c => c.feature_ids.includes(featureFilter))
    : commits

  return (
    <div className="bg-card text-card-foreground rounded-xl border shadow-sm">
      {/* Header with feature filter */}
      <div className="flex items-center gap-3 px-4 py-3 border-b">
        <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
          <GitCommitIcon className="size-4 text-muted-foreground" />
          Commits
        </h3>
        {features && features.length > 0 && (
          <div className="ml-auto">
            <select
              className={cn(
                'h-8 rounded-md border border-input bg-background px-2 text-xs',
                'focus:outline-none focus:ring-2 focus:ring-ring',
              )}
              value={featureFilter ?? ''}
              onChange={e => {
                const val = e.target.value
                onFeatureFilterChange(val ? Number(val) : null)
              }}
            >
              <option value="">All features</option>
              {features.map(f => (
                <option key={f.id} value={f.id}>
                  {f.name}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Commit list */}
      {isLoading ? (
        <div>
          <SkeletonItem />
          <SkeletonItem />
          <SkeletonItem />
          <SkeletonItem />
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center gap-2 py-12 text-muted-foreground">
          <GitCommitIcon className="size-8 opacity-40" />
          <p className="text-sm font-medium">No commits yet</p>
          <p className="text-xs">Git commits will appear here as the agent works.</p>
        </div>
      ) : (
        <div className="divide-y divide-border/50">
          {filtered.map(commit => {
            const badgeColor = commit.parsed
              ? TYPE_BADGE_COLORS[commit.parsed.type] ?? TYPE_BADGE_COLORS.chore
              : null

            return (
              <div
                key={commit.sha}
                className="flex items-start gap-3 px-4 py-3 hover:bg-muted/50 transition-colors"
              >
                {/* SHA */}
                <code className="text-[10px] font-mono text-cyan-600 dark:text-cyan-400 bg-cyan-500/10 px-1.5 py-0.5 rounded shrink-0 mt-0.5">
                  {commit.sha.slice(0, 7)}
                </code>

                {/* Message + optional type badge */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    {commit.parsed && badgeColor && (
                      <Badge
                        variant="outline"
                        className={cn('text-[10px]', badgeColor)}
                      >
                        {commit.parsed.type}
                      </Badge>
                    )}
                    <span className="text-xs text-foreground truncate">
                      {commit.message}
                    </span>
                  </div>
                </div>

                {/* Timestamp */}
                <span className="text-[10px] text-muted-foreground whitespace-nowrap shrink-0">
                  {timeAgo(commit.timestamp)}
                </span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
