/**
 * ApprovalBanner - Fixed banner for pending agent approval requests.
 *
 * Shows a pulsing amber card stack when agents are waiting for operator
 * sign-off on commands. Each card displays the truncated command, agent ID,
 * and how long ago it was requested. Approve/Deny buttons fire async
 * callbacks with per-button loading spinners.
 *
 * Portable widget: receives all data via props, no page-specific hooks.
 */

import { useState } from 'react'
import { Shield, Check, X, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { timeAgo } from './timeAgo'
import type { ApprovalRequest } from '../../lib/types'

export interface ApprovalBannerProps {
  approvals: ApprovalRequest[]
  onApprove: (id: number) => Promise<void>
  onDeny: (id: number, reason?: string) => Promise<void>
  isLoading?: boolean
}

export function ApprovalBanner({ approvals, onApprove, onDeny, isLoading }: ApprovalBannerProps) {
  // Track which button is in-flight so we can show a spinner per card
  const [loadingIds, setLoadingIds] = useState<Record<number, 'approve' | 'deny'>>({})

  const pending = approvals.filter(a => a.status === 'pending')

  // Nothing pending? Render nothing.
  if (pending.length === 0) return null

  async function handleAction(id: number, action: 'approve' | 'deny') {
    setLoadingIds(prev => ({ ...prev, [id]: action }))
    try {
      if (action === 'approve') {
        await onApprove(id)
      } else {
        await onDeny(id)
      }
    } finally {
      setLoadingIds(prev => {
        const next = { ...prev }
        delete next[id]
        return next
      })
    }
  }

  return (
    <div
      className={cn(
        'w-full rounded-lg border-2 border-amber-500/60 bg-amber-50 dark:bg-amber-950/30',
        'p-4 animate-pulse shadow-md',
      )}
    >
      {/* Banner header */}
      <div className="flex items-center gap-2 mb-3">
        <Shield className="size-5 text-amber-600 dark:text-amber-400" />
        <span className="text-sm font-bold text-amber-800 dark:text-amber-300">
          {pending.length} Pending Approval{pending.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Stack of approval cards */}
      <div className="space-y-2">
        {pending.map(approval => {
          const busy = loadingIds[approval.id]
          const truncatedCmd =
            approval.command.length > 60
              ? approval.command.slice(0, 57) + '...'
              : approval.command

          return (
            <div
              key={approval.id}
              className={cn(
                'flex items-center justify-between gap-3 rounded-md border',
                'border-amber-300 dark:border-amber-700 bg-white dark:bg-card p-3',
              )}
            >
              {/* Left: command + metadata */}
              <div className="min-w-0 flex-1">
                <p
                  className="text-sm font-mono text-foreground truncate"
                  title={approval.command}
                >
                  {truncatedCmd}
                </p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Agent <span className="font-semibold">{approval.agent_id}</span>
                  {' \u00B7 '}
                  {timeAgo(approval.requested_at)}
                </p>
              </div>

              {/* Right: action buttons */}
              <div className="flex items-center gap-2 shrink-0">
                <Button
                  size="sm"
                  variant="default"
                  className="bg-emerald-600 hover:bg-emerald-700 text-white"
                  disabled={!!busy || isLoading}
                  onClick={() => handleAction(approval.id, 'approve')}
                >
                  {busy === 'approve' ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : (
                    <Check className="size-4" />
                  )}
                  Approve
                </Button>
                <Button
                  size="sm"
                  variant="destructive"
                  disabled={!!busy || isLoading}
                  onClick={() => handleAction(approval.id, 'deny')}
                >
                  {busy === 'deny' ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : (
                    <X className="size-4" />
                  )}
                  Deny
                </Button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
