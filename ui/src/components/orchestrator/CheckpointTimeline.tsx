/**
 * CheckpointTimeline - Vertical timeline of git-anchored project checkpoints.
 *
 * Each entry shows a label, short SHA (first 7 chars), relative timestamp,
 * and a feature snapshot summary (X/Y passing). A "Rollback" button fetches
 * a preview of changes and shows a confirmation dialog before executing.
 * Includes a "Create Checkpoint" input at the top.
 *
 * Portable widget: receives all data via props, no page-specific hooks.
 */

import { useState } from 'react'
import { History, RotateCcw, Plus, Loader2, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { timeAgo } from './timeAgo'
import type { Checkpoint, CheckpointFeatureSnapshot, RollbackPreview } from '../../lib/types'

export interface CheckpointTimelineProps {
  checkpoints: Checkpoint[]
  onRollback: (id: number) => Promise<RollbackPreview>
  onConfirmRollback: (id: number) => Promise<void>
  onCreateCheckpoint: (label: string) => Promise<void>
  isLoading?: boolean
}

/** Parse the JSON feature_snapshot string into typed objects. */
function parseSnapshot(raw: string | null): CheckpointFeatureSnapshot[] {
  if (!raw) return []
  try {
    return JSON.parse(raw) as CheckpointFeatureSnapshot[]
  } catch {
    return []
  }
}

/** Summarize "X/Y features passing" from a snapshot. */
function snapshotSummary(raw: string | null): string {
  const items = parseSnapshot(raw)
  if (items.length === 0) return 'No snapshot'
  const passing = items.filter(f => f.passes).length
  return `${passing}/${items.length} features passing`
}

export function CheckpointTimeline({
  checkpoints,
  onRollback,
  onConfirmRollback,
  onCreateCheckpoint,
  isLoading,
}: CheckpointTimelineProps) {
  const [newLabel, setNewLabel] = useState('')
  const [creating, setCreating] = useState(false)

  // Rollback flow: preview -> confirm
  const [rollbackPreview, setRollbackPreview] = useState<RollbackPreview | null>(null)
  const [previewLoadingId, setPreviewLoadingId] = useState<number | null>(null)
  const [confirming, setConfirming] = useState(false)

  async function handleCreate() {
    const label = newLabel.trim()
    if (!label) return
    setCreating(true)
    try {
      await onCreateCheckpoint(label)
      setNewLabel('')
    } finally {
      setCreating(false)
    }
  }

  async function handleRollbackClick(id: number) {
    setPreviewLoadingId(id)
    try {
      const preview = await onRollback(id)
      setRollbackPreview(preview)
    } finally {
      setPreviewLoadingId(null)
    }
  }

  async function handleConfirmRollback() {
    if (!rollbackPreview) return
    setConfirming(true)
    try {
      await onConfirmRollback(rollbackPreview.checkpoint.id)
      setRollbackPreview(null)
    } finally {
      setConfirming(false)
    }
  }

  return (
    <div className="bg-card text-card-foreground rounded-xl border shadow-sm p-4">
      {/* Header with create input */}
      <div className="flex items-center gap-2 mb-4">
        <History className="size-4 text-muted-foreground" />
        <h3 className="text-sm font-semibold text-foreground">Checkpoints</h3>
      </div>

      {/* Create checkpoint control */}
      <div className="flex items-center gap-2 mb-4">
        <Input
          className="h-8 text-xs flex-1"
          placeholder="Checkpoint label..."
          value={newLabel}
          onChange={e => setNewLabel(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') handleCreate() }}
          disabled={creating}
        />
        <Button
          size="sm"
          variant="default"
          disabled={creating || !newLabel.trim()}
          onClick={handleCreate}
        >
          {creating ? <Loader2 className="size-4 animate-spin" /> : <Plus className="size-4" />}
          Create
        </Button>
      </div>

      {/* Skeleton while loading */}
      {isLoading ? (
        <div className="space-y-4 animate-pulse">
          {[1, 2, 3].map(i => (
            <div key={i} className="flex gap-3">
              <div className="w-3 h-3 rounded-full bg-muted mt-1 shrink-0" />
              <div className="flex-1 space-y-1">
                <div className="h-4 w-32 rounded bg-muted" />
                <div className="h-3 w-48 rounded bg-muted" />
              </div>
            </div>
          ))}
        </div>
      ) : checkpoints.length === 0 ? (
        /* Empty state */
        <div className="flex flex-col items-center gap-2 py-8 text-muted-foreground">
          <History className="size-8 opacity-40" />
          <p className="text-sm font-medium">No checkpoints yet</p>
          <p className="text-xs">Create your first checkpoint to track project state.</p>
        </div>
      ) : (
        /* Timeline */
        <div className="relative ml-1.5">
          {/* Vertical line */}
          <div className="absolute left-[5px] top-2 bottom-2 w-px bg-border" />

          <div className="space-y-4">
            {checkpoints.map(cp => (
              <div key={cp.id} className="flex gap-3 relative">
                {/* Dot */}
                <div className="w-3 h-3 rounded-full bg-primary border-2 border-background mt-1 shrink-0 z-10" />

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-semibold text-foreground">{cp.label}</span>
                    <code className="text-[10px] font-mono text-cyan-600 dark:text-cyan-400 bg-cyan-500/10 px-1.5 py-0.5 rounded">
                      {cp.git_sha.slice(0, 7)}
                    </code>
                    <span className="text-[10px] text-muted-foreground">
                      {timeAgo(cp.created_at)}
                    </span>
                  </div>

                  <p className="text-xs text-muted-foreground mt-0.5">
                    {snapshotSummary(cp.feature_snapshot)}
                  </p>

                  {/* Rollback button */}
                  <Button
                    size="xs"
                    variant="outline"
                    className="mt-1.5"
                    disabled={previewLoadingId === cp.id}
                    onClick={() => handleRollbackClick(cp.id)}
                  >
                    {previewLoadingId === cp.id ? (
                      <Loader2 className="size-3 animate-spin" />
                    ) : (
                      <RotateCcw className="size-3" />
                    )}
                    Rollback
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Rollback confirmation dialog (inline overlay) */}
      {rollbackPreview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-card border-2 border-border rounded-xl shadow-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-sm font-bold text-foreground">Confirm Rollback</h4>
              <button
                onClick={() => setRollbackPreview(null)}
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="size-4" />
              </button>
            </div>

            <p className="text-xs text-muted-foreground mb-3">
              Rolling back to <strong>{rollbackPreview.checkpoint.label}</strong>{' '}
              <code className="text-[10px] font-mono text-cyan-600 dark:text-cyan-400">
                {rollbackPreview.checkpoint.git_sha.slice(0, 7)}
              </code>
            </p>

            {rollbackPreview.changes.length === 0 ? (
              <p className="text-xs text-muted-foreground italic mb-4">No feature status changes.</p>
            ) : (
              <div className="max-h-48 overflow-y-auto border rounded-md mb-4">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b text-muted-foreground">
                      <th className="px-2 py-1 text-left font-medium">Feature</th>
                      <th className="px-2 py-1 text-left font-medium">Current</th>
                      <th className="px-2 py-1 text-left font-medium">After</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rollbackPreview.changes.map(c => (
                      <tr key={c.feature_id} className="border-b last:border-0">
                        <td className="px-2 py-1">{c.feature_name}</td>
                        <td className="px-2 py-1 text-muted-foreground">{c.current_status}</td>
                        <td className="px-2 py-1 text-muted-foreground">{c.rollback_status}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div className="flex items-center gap-2 justify-end">
              <Button size="sm" variant="outline" onClick={() => setRollbackPreview(null)}>
                Cancel
              </Button>
              <Button
                size="sm"
                variant="destructive"
                disabled={confirming}
                onClick={handleConfirmRollback}
              >
                {confirming ? <Loader2 className="size-4 animate-spin" /> : <RotateCcw className="size-4" />}
                Confirm Rollback
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
