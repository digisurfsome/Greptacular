/**
 * CheckpointDetail - Expanded view comparing a checkpoint's feature snapshot
 * with current feature statuses.
 *
 * Shows a table with Feature ID, Name, Status at Checkpoint, Current Status.
 * Rows where the two statuses differ are highlighted with a yellow background
 * so operators can quickly see what has changed since the checkpoint was taken.
 *
 * Portable widget: receives all data via props, no page-specific hooks.
 */

import { History } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Checkpoint, CheckpointFeatureSnapshot } from '../../lib/types'

export interface CheckpointDetailProps {
  checkpoint: Checkpoint
  currentFeatures?: { id: number; name: string; passes: boolean; in_progress: boolean }[]
}

/** Parse the JSON feature_snapshot field into typed objects. */
function parseSnapshot(raw: string | null): CheckpointFeatureSnapshot[] {
  if (!raw) return []
  try {
    return JSON.parse(raw) as CheckpointFeatureSnapshot[]
  } catch {
    return []
  }
}

/** Derive a readable status label from boolean flags. */
function statusLabel(passes: boolean, inProgress: boolean): string {
  if (passes) return 'Passing'
  if (inProgress) return 'In Progress'
  return 'Pending'
}

export function CheckpointDetail({ checkpoint, currentFeatures }: CheckpointDetailProps) {
  const snapshot = parseSnapshot(checkpoint.feature_snapshot)

  // Build a lookup map for current features
  const currentMap = new Map(
    (currentFeatures ?? []).map(f => [f.id, f]),
  )

  return (
    <div className="bg-card text-card-foreground rounded-xl border shadow-sm p-4">
      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        <History className="size-4 text-muted-foreground" />
        <h3 className="text-sm font-semibold text-foreground">{checkpoint.label}</h3>
        <code className="text-[10px] font-mono text-cyan-600 dark:text-cyan-400 bg-cyan-500/10 px-1.5 py-0.5 rounded ml-1">
          {checkpoint.git_sha.slice(0, 7)}
        </code>
      </div>

      {snapshot.length === 0 ? (
        <p className="text-xs text-muted-foreground italic py-4 text-center">
          No feature snapshot data available.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b text-muted-foreground">
                <th className="px-3 py-2 text-left font-medium">ID</th>
                <th className="px-3 py-2 text-left font-medium">Feature</th>
                <th className="px-3 py-2 text-left font-medium">At Checkpoint</th>
                <th className="px-3 py-2 text-left font-medium">Current</th>
              </tr>
            </thead>
            <tbody>
              {snapshot.map(snap => {
                const current = currentMap.get(snap.id)
                const snapStatus = statusLabel(snap.passes, snap.in_progress)
                const currentStatus = current
                  ? statusLabel(current.passes, current.in_progress)
                  : '\u2014'
                const differs = current
                  ? snapStatus !== currentStatus
                  : false

                return (
                  <tr
                    key={snap.id}
                    className={cn(
                      'border-b border-border/50 last:border-0',
                      differs && 'bg-yellow-50 dark:bg-yellow-900/20',
                    )}
                  >
                    <td className="px-3 py-2 font-mono text-muted-foreground">#{snap.id}</td>
                    <td className="px-3 py-2">{snap.name}</td>
                    <td className="px-3 py-2 text-muted-foreground">{snapStatus}</td>
                    <td className="px-3 py-2 text-muted-foreground">{currentStatus}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
