/**
 * ApprovalHistory - Searchable table of all approval requests.
 *
 * Columns: Command, Agent, Status (badge), Requested (relative), Resolved
 * (relative), Resolved By. Includes a status filter dropdown and skeleton
 * loading state.
 *
 * Portable widget: receives all data via props, no page-specific hooks.
 */

import { useState } from 'react'
import { Shield, Search } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { timeAgo } from './timeAgo'
import type { ApprovalRequest } from '../../lib/types'

export interface ApprovalHistoryProps {
  approvals: ApprovalRequest[]
  isLoading?: boolean
}

const STATUS_COLORS: Record<ApprovalRequest['status'], string> = {
  pending: 'bg-yellow-500/20 text-yellow-700 dark:text-yellow-400 border-yellow-500/30',
  approved: 'bg-emerald-500/20 text-emerald-700 dark:text-emerald-400 border-emerald-500/30',
  denied: 'bg-red-500/20 text-red-700 dark:text-red-400 border-red-500/30',
  expired: 'bg-gray-500/20 text-gray-600 dark:text-gray-400 border-gray-500/30',
}

function SkeletonRow() {
  return (
    <tr className="animate-pulse">
      <td className="px-3 py-2"><div className="h-4 w-40 rounded bg-muted" /></td>
      <td className="px-3 py-2"><div className="h-4 w-16 rounded bg-muted" /></td>
      <td className="px-3 py-2"><div className="h-5 w-20 rounded-full bg-muted" /></td>
      <td className="px-3 py-2"><div className="h-4 w-16 rounded bg-muted" /></td>
      <td className="px-3 py-2"><div className="h-4 w-16 rounded bg-muted" /></td>
      <td className="px-3 py-2"><div className="h-4 w-20 rounded bg-muted" /></td>
    </tr>
  )
}

export function ApprovalHistory({ approvals, isLoading }: ApprovalHistoryProps) {
  const [statusFilter, setStatusFilter] = useState<ApprovalRequest['status'] | 'all'>('all')
  const [search, setSearch] = useState('')

  const filtered = approvals.filter(a => {
    if (statusFilter !== 'all' && a.status !== statusFilter) return false
    if (search && !a.command.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  return (
    <div className="bg-card text-card-foreground rounded-xl border shadow-sm">
      {/* Header row with filter controls */}
      <div className="flex flex-wrap items-center gap-3 px-4 py-3 border-b">
        <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
          <Shield className="size-4" />
          Approval History
        </h3>
        <div className="ml-auto flex items-center gap-2">
          {/* Status filter */}
          <select
            className={cn(
              'h-8 rounded-md border border-input bg-background px-2 text-xs',
              'focus:outline-none focus:ring-2 focus:ring-ring',
            )}
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value as ApprovalRequest['status'] | 'all')}
          >
            <option value="all">All statuses</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="denied">Denied</option>
            <option value="expired">Expired</option>
          </select>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 size-3 text-muted-foreground" />
            <Input
              className="h-8 pl-7 text-xs w-44"
              placeholder="Search commands..."
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b text-muted-foreground">
              <th className="px-3 py-2 text-left font-medium">Command</th>
              <th className="px-3 py-2 text-left font-medium">Agent</th>
              <th className="px-3 py-2 text-left font-medium">Status</th>
              <th className="px-3 py-2 text-left font-medium">Requested</th>
              <th className="px-3 py-2 text-left font-medium">Resolved</th>
              <th className="px-3 py-2 text-left font-medium">Resolved By</th>
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
                <td colSpan={6} className="px-3 py-12 text-center">
                  <div className="flex flex-col items-center gap-2 text-muted-foreground">
                    <Shield className="size-8 opacity-40" />
                    <p className="text-sm font-medium">No approval requests yet</p>
                    <p className="text-xs">Approval requests from agents will appear here.</p>
                  </div>
                </td>
              </tr>
            ) : (
              filtered.map(a => (
                <tr
                  key={a.id}
                  className="border-b border-border/50 last:border-0 hover:bg-muted/50 transition-colors"
                >
                  <td className="px-3 py-2 font-mono max-w-xs truncate" title={a.command}>
                    {a.command}
                  </td>
                  <td className="px-3 py-2 text-muted-foreground">{a.agent_id}</td>
                  <td className="px-3 py-2">
                    <Badge
                      variant="outline"
                      className={cn('text-[10px] capitalize', STATUS_COLORS[a.status])}
                    >
                      {a.status}
                    </Badge>
                  </td>
                  <td className="px-3 py-2 text-muted-foreground">{timeAgo(a.requested_at)}</td>
                  <td className="px-3 py-2 text-muted-foreground">
                    {a.resolved_at ? timeAgo(a.resolved_at) : '\u2014'}
                  </td>
                  <td className="px-3 py-2 text-muted-foreground">{a.resolved_by ?? '\u2014'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
