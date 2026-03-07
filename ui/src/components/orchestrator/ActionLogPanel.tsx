/**
 * ActionLogPanel - Paginated, filterable table of agent tool call actions.
 *
 * Displays timestamp (relative), tool name (monospace badge), input preview
 * (truncated), status dot (green/red), and duration. Clicking a row expands
 * an accordion with the full input and output in a scrollable code block.
 *
 * Filters: tool name text search, status dropdown. Pagination at the bottom.
 *
 * Portable widget: receives all data via props, no page-specific hooks.
 */

import { useState } from 'react'
import { Activity, Search, ChevronLeft, ChevronRight, ChevronDown, ChevronUp } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { timeAgo } from './timeAgo'
import type { ActionLogEntry, ActionLogFilters, PaginatedResult } from '../../lib/types'

export interface ActionLogPanelProps {
  entries: PaginatedResult<ActionLogEntry>
  filters: ActionLogFilters
  onFiltersChange: (filters: ActionLogFilters) => void
  isLoading?: boolean
}

function SkeletonRow() {
  return (
    <tr className="animate-pulse">
      <td className="px-3 py-2"><div className="h-4 w-14 rounded bg-muted" /></td>
      <td className="px-3 py-2"><div className="h-5 w-20 rounded bg-muted" /></td>
      <td className="px-3 py-2"><div className="h-4 w-48 rounded bg-muted" /></td>
      <td className="px-3 py-2"><div className="h-3 w-3 rounded-full bg-muted" /></td>
      <td className="px-3 py-2"><div className="h-4 w-12 rounded bg-muted" /></td>
    </tr>
  )
}

export function ActionLogPanel({ entries, filters, onFiltersChange, isLoading }: ActionLogPanelProps) {
  const [expandedId, setExpandedId] = useState<number | null>(null)

  const totalPages = Math.max(1, Math.ceil(entries.total / entries.limit))
  const currentPage = entries.page

  function updateFilter(patch: Partial<ActionLogFilters>) {
    onFiltersChange({ ...filters, ...patch })
  }

  return (
    <div className="bg-card text-card-foreground rounded-xl border shadow-sm">
      {/* Header with filters */}
      <div className="flex flex-wrap items-center gap-3 px-4 py-3 border-b">
        <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
          <Activity className="size-4" />
          Action Log
        </h3>
        <div className="ml-auto flex items-center gap-2">
          {/* Status filter */}
          <select
            className={cn(
              'h-8 rounded-md border border-input bg-background px-2 text-xs',
              'focus:outline-none focus:ring-2 focus:ring-ring',
            )}
            value={filters.status ?? ''}
            onChange={e =>
              updateFilter({
                status: (e.target.value || undefined) as ActionLogFilters['status'],
                page: 1,
              })
            }
          >
            <option value="">All statuses</option>
            <option value="success">Success</option>
            <option value="error">Error</option>
          </select>

          {/* Tool name search */}
          <div className="relative">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 size-3 text-muted-foreground" />
            <Input
              className="h-8 pl-7 text-xs w-40"
              placeholder="Tool name..."
              value={filters.tool_name ?? ''}
              onChange={e => updateFilter({ tool_name: e.target.value || undefined, page: 1 })}
            />
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b text-muted-foreground">
              <th className="px-3 py-2 text-left font-medium">Time</th>
              <th className="px-3 py-2 text-left font-medium">Tool</th>
              <th className="px-3 py-2 text-left font-medium">Input</th>
              <th className="px-3 py-2 text-left font-medium">Status</th>
              <th className="px-3 py-2 text-left font-medium">Duration</th>
              <th className="px-3 py-2 w-8" />
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <>
                <SkeletonRow />
                <SkeletonRow />
                <SkeletonRow />
                <SkeletonRow />
                <SkeletonRow />
              </>
            ) : entries.items.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-3 py-12 text-center">
                  <div className="flex flex-col items-center gap-2 text-muted-foreground">
                    <Activity className="size-8 opacity-40" />
                    <p className="text-sm font-medium">No actions recorded yet</p>
                    <p className="text-xs">Agent tool calls will appear here as they execute.</p>
                  </div>
                </td>
              </tr>
            ) : (
              entries.items.map(entry => {
                const isExpanded = expandedId === entry.id
                const inputPreview =
                  entry.tool_input_summary && entry.tool_input_summary.length > 80
                    ? entry.tool_input_summary.slice(0, 77) + '...'
                    : entry.tool_input_summary ?? '\u2014'

                return (
                  <tbody key={entry.id}>
                    <tr
                      className={cn(
                        'border-b border-border/50 hover:bg-muted/50 transition-colors cursor-pointer',
                        isExpanded && 'bg-muted/30',
                      )}
                      onClick={() => setExpandedId(isExpanded ? null : entry.id)}
                    >
                      <td className="px-3 py-2 text-muted-foreground whitespace-nowrap">
                        {timeAgo(entry.created_at)}
                      </td>
                      <td className="px-3 py-2">
                        <span className="font-mono text-[10px] bg-primary/10 text-primary px-1.5 py-0.5 rounded">
                          {entry.tool_name}
                        </span>
                      </td>
                      <td className="px-3 py-2 max-w-xs truncate text-muted-foreground" title={entry.tool_input_summary ?? ''}>
                        {inputPreview}
                      </td>
                      <td className="px-3 py-2">
                        <span
                          className={cn(
                            'inline-block w-2.5 h-2.5 rounded-full',
                            entry.status === 'success'
                              ? 'bg-emerald-500'
                              : 'bg-red-500',
                          )}
                          title={entry.status}
                        />
                      </td>
                      <td className="px-3 py-2 text-muted-foreground whitespace-nowrap">
                        {entry.duration_ms != null ? `${entry.duration_ms}ms` : '\u2014'}
                      </td>
                      <td className="px-3 py-2">
                        {isExpanded ? (
                          <ChevronUp className="size-3 text-muted-foreground" />
                        ) : (
                          <ChevronDown className="size-3 text-muted-foreground" />
                        )}
                      </td>
                    </tr>

                    {/* Expanded detail row */}
                    {isExpanded && (
                      <tr>
                        <td colSpan={6} className="px-3 py-3 bg-muted/20">
                          <div className="space-y-2">
                            {entry.tool_input_summary && (
                              <div>
                                <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wide mb-1">
                                  Input
                                </p>
                                <pre className="text-xs font-mono bg-zinc-900 text-zinc-100 p-3 rounded-md max-h-48 overflow-auto whitespace-pre-wrap">
                                  {entry.tool_input_summary}
                                </pre>
                              </div>
                            )}
                            {entry.result_summary && (
                              <div>
                                <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wide mb-1">
                                  Output
                                </p>
                                <pre className="text-xs font-mono bg-zinc-900 text-zinc-100 p-3 rounded-md max-h-48 overflow-auto whitespace-pre-wrap">
                                  {entry.result_summary}
                                </pre>
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </tbody>
                )
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {entries.total > 0 && (
        <div className="flex items-center justify-between px-4 py-3 border-t">
          <p className="text-xs text-muted-foreground">
            Page {currentPage} of {totalPages} ({entries.total} total)
          </p>
          <div className="flex items-center gap-1">
            <Button
              size="xs"
              variant="outline"
              disabled={currentPage <= 1}
              onClick={() => updateFilter({ page: currentPage - 1 })}
            >
              <ChevronLeft className="size-3" />
              Prev
            </Button>
            <Button
              size="xs"
              variant="outline"
              disabled={!entries.has_more}
              onClick={() => updateFilter({ page: currentPage + 1 })}
            >
              Next
              <ChevronRight className="size-3" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
