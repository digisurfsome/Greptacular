/**
 * CIStatusWidget - Non-intrusive CI pipeline notification for the Workspace header.
 *
 * Shows a compact indicator that:
 * - Spins when CI is running
 * - Blinks green when CI passes (with veto countdown)
 * - Auto-merges + pulls when countdown expires
 * - Blinks red/orange when CI fails / auto-fix is working
 * - Shows "Success" toast when fully deployed
 * - Shows veto (X) button during countdown to cancel merge
 * - NEVER steals focus or takes over the screen
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getCIStatus, startCIMonitor, vetoCIMerge } from '../../lib/api'
import type { CIPipelineStatus, CIStatusResponse } from '../../lib/types'
import { X, Check, Loader2, AlertTriangle, GitMerge, Wrench, Ban, CircleDot } from 'lucide-react'

interface CIStatusWidgetProps {
  workingDirectory: string | null
}

const STATUS_CONFIG: Record<CIPipelineStatus, {
  label: string
  color: string
  bgColor: string
  blink: boolean
  icon: 'spinner' | 'check' | 'x' | 'wrench' | 'merge' | 'warning' | 'ban' | 'dot'
}> = {
  idle: { label: 'CI Idle', color: 'text-muted-foreground', bgColor: 'bg-muted', blink: false, icon: 'dot' },
  running: { label: 'CI Running', color: 'text-cyan-400', bgColor: 'bg-cyan-500/15', blink: false, icon: 'spinner' },
  passed: { label: 'CI Passed', color: 'text-emerald-400', bgColor: 'bg-emerald-500/15', blink: true, icon: 'check' },
  failed: { label: 'CI Failed', color: 'text-red-400', bgColor: 'bg-red-500/15', blink: true, icon: 'x' },
  fixing: { label: 'Auto-fixing', color: 'text-amber-400', bgColor: 'bg-amber-500/15', blink: true, icon: 'wrench' },
  merging: { label: 'Merging', color: 'text-violet-400', bgColor: 'bg-violet-500/15', blink: false, icon: 'merge' },
  merged: { label: 'Deployed', color: 'text-emerald-400', bgColor: 'bg-emerald-500/20', blink: true, icon: 'check' },
  veto: { label: 'Merge Cancelled', color: 'text-amber-400', bgColor: 'bg-amber-500/15', blink: false, icon: 'ban' },
  exhausted: { label: 'Needs Help', color: 'text-red-400', bgColor: 'bg-red-500/15', blink: true, icon: 'warning' },
  error: { label: 'CI Error', color: 'text-red-400', bgColor: 'bg-red-500/15', blink: false, icon: 'warning' },
}

function StatusIcon({ icon, className }: { icon: string; className?: string }) {
  const size = 14
  switch (icon) {
    case 'spinner': return <Loader2 size={size} className={`animate-spin ${className}`} />
    case 'check': return <Check size={size} className={className} />
    case 'x': return <X size={size} className={className} />
    case 'wrench': return <Wrench size={size} className={className} />
    case 'merge': return <GitMerge size={size} className={className} />
    case 'warning': return <AlertTriangle size={size} className={className} />
    case 'ban': return <Ban size={size} className={className} />
    default: return <CircleDot size={size} className={className} />
  }
}

export function CIStatusWidget({ workingDirectory }: CIStatusWidgetProps) {
  const queryClient = useQueryClient()
  const [initialized, setInitialized] = useState(false)
  const [showSuccess, setShowSuccess] = useState(false)
  const [expanded, setExpanded] = useState(false)
  const prevStatusRef = useRef<CIPipelineStatus>('idle')
  const successTimerRef = useRef<ReturnType<typeof setTimeout>>(null)

  // Start monitoring when working directory changes
  useEffect(() => {
    if (!workingDirectory) {
      setInitialized(false)
      return
    }
    startCIMonitor(workingDirectory)
      .then(() => setInitialized(true))
      .catch(() => setInitialized(false))
  }, [workingDirectory])

  // Poll CI status every 5 seconds
  const { data: ciStatus } = useQuery<CIStatusResponse>({
    queryKey: ['ci-status', workingDirectory],
    queryFn: () => getCIStatus(workingDirectory!),
    enabled: !!workingDirectory && initialized,
    refetchInterval: 5000,
  })

  const status: CIPipelineStatus = ciStatus?.status ?? 'idle'
  const config = STATUS_CONFIG[status]

  // Show success toast when transitioning to merged
  useEffect(() => {
    if (status === 'merged' && prevStatusRef.current !== 'merged') {
      setShowSuccess(true)
      successTimerRef.current = setTimeout(() => setShowSuccess(false), 8000)
    }
    prevStatusRef.current = status
    return () => {
      if (successTimerRef.current) clearTimeout(successTimerRef.current)
    }
  }, [status])

  const handleVeto = useCallback(async () => {
    if (!workingDirectory) return
    await vetoCIMerge(workingDirectory)
    queryClient.invalidateQueries({ queryKey: ['ci-status', workingDirectory] })
  }, [workingDirectory, queryClient])

  if (!workingDirectory || !initialized) return null
  if (status === 'idle' && !ciStatus?.latest_run) return null

  const vetoRemaining = ciStatus?.veto_remaining
  const vetoSeconds = vetoRemaining != null ? Math.ceil(vetoRemaining) : null
  const autofixAttempt = ciStatus?.autofix_attempt ?? 0

  return (
    <>
      {/* Compact widget in header */}
      <div className="relative flex items-center">
        <button
          onClick={() => setExpanded(v => !v)}
          className={`
            flex items-center gap-1.5 px-2.5 py-1 rounded-md border border-border
            transition-all duration-200 hover:opacity-80
            ${config.bgColor}
            ${config.blink ? 'animate-pulse' : ''}
          `}
          title={config.label}
        >
          <StatusIcon icon={config.icon} className={config.color} />
          <span className={`text-[10px] font-bold tracking-wide ${config.color}`}>
            {status === 'passed' && vetoSeconds != null
              ? `${vetoSeconds}s`
              : status === 'fixing'
                ? `FIX ${autofixAttempt}/3`
                : config.label.toUpperCase()
            }
          </span>

          {/* Veto button — only during countdown */}
          {status === 'passed' && vetoSeconds != null && (
            <button
              onClick={(e) => { e.stopPropagation(); handleVeto() }}
              className="ml-1 p-0.5 rounded hover:bg-red-500/20 transition-colors"
              title="Cancel auto-merge"
            >
              <X size={12} className="text-red-400" />
            </button>
          )}
        </button>

        {/* Expanded dropdown with details */}
        {expanded && ciStatus && (
          <div className="absolute top-full right-0 mt-1 z-50 w-72 bg-card border-2 border-border rounded-lg shadow-lg p-3">
            <div className="space-y-2">
              {/* Header */}
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-foreground">CI Pipeline</span>
                <span className={`text-[10px] font-bold ${config.color}`}>
                  {config.label}
                </span>
              </div>

              {/* Repo info */}
              {ciStatus.owner && (
                <div className="text-[10px] text-muted-foreground">
                  {ciStatus.owner}/{ciStatus.repo} ({ciStatus.branch})
                </div>
              )}

              {/* Latest run */}
              {ciStatus.latest_run && (
                <div className="text-[10px] text-muted-foreground border-t border-border pt-2">
                  <div className="flex justify-between">
                    <span>Commit: {ciStatus.latest_run.commit_sha}</span>
                    <span>{ciStatus.latest_run.conclusion ?? ciStatus.latest_run.status}</span>
                  </div>
                  <div className="truncate mt-0.5 text-foreground/70">
                    {ciStatus.latest_run.commit_message}
                  </div>
                </div>
              )}

              {/* PR link */}
              {ciStatus.pr_url && (
                <a
                  href={ciStatus.pr_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block text-[10px] text-cyan-400 hover:underline"
                >
                  PR #{ciStatus.pr_number}
                </a>
              )}

              {/* Veto countdown bar */}
              {status === 'passed' && vetoSeconds != null && (
                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-emerald-400 font-bold">
                      Auto-merge in {vetoSeconds}s
                    </span>
                    <button
                      onClick={handleVeto}
                      className="text-[10px] text-red-400 hover:text-red-300 font-bold"
                    >
                      CANCEL
                    </button>
                  </div>
                  <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-emerald-500 rounded-full transition-all duration-1000"
                      style={{ width: `${((30 - (vetoSeconds ?? 0)) / 30) * 100}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Recent events */}
              {ciStatus.history.length > 0 && (
                <div className="border-t border-border pt-2 max-h-32 overflow-y-auto">
                  <span className="text-[10px] font-bold text-muted-foreground">Events</span>
                  {ciStatus.history.slice(-5).reverse().map((event, i) => (
                    <div key={i} className="text-[10px] text-muted-foreground mt-1">
                      {event.message}
                    </div>
                  ))}
                </div>
              )}

              {/* Error */}
              {ciStatus.error_message && (
                <div className="text-[10px] text-red-400 border-t border-border pt-2">
                  {ciStatus.error_message}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Success toast — slides in from top-right, non-intrusive */}
      {showSuccess && (
        <div className="fixed top-4 right-4 z-[100] animate-in slide-in-from-top-2 duration-300">
          <div className="flex items-center gap-2 px-4 py-3 bg-emerald-500/90 text-white rounded-lg shadow-xl border border-emerald-400">
            <Check size={18} className="shrink-0" />
            <div>
              <div className="text-sm font-bold">Deployed</div>
              <div className="text-xs opacity-90">
                PR merged, code pulled, ready to go.
              </div>
            </div>
            <button
              onClick={() => setShowSuccess(false)}
              className="ml-2 p-0.5 hover:bg-white/20 rounded"
            >
              <X size={14} />
            </button>
          </div>
        </div>
      )}
    </>
  )
}
