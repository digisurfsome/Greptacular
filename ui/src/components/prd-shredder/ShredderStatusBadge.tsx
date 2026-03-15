/**
 * ShredderStatusBadge — Compact global badge for PRD Shredder state.
 *
 * Shows at a glance whether the shredder is idle, building, queued, or has
 * failures. Clicking navigates to the #/prd-shredder page.
 *
 * Priority logic (first match wins):
 *   1. building > 0 → orange spinner + current PRD title + queue count
 *   2. queued > 0   → amber pulse + queue count
 *   3. failed > 0 && done === 0 → red dot + failure count
 *   4. everything else → green ping + READY
 *
 * Reuses existing React Query hooks (useShredderStats, useShredderQueue)
 * which already poll every 5 seconds.
 */

import { useShredderStats, useShredderQueue } from '@/hooks/usePRDShredder'

const ACTIVE_STATUSES = ['cloning', 'analyzing', 'building', 'testing', 'committing', 'qa_testing']

function navigateToShredder() {
  window.location.hash = '#/prd-shredder'
}

export function ShredderStatusBadge() {
  const { data: stats } = useShredderStats()
  const { data: queueData } = useShredderQueue()

  // Don't render until data loads
  if (!stats) return null

  const { building, queued, failed, done, total } = stats

  // Find the currently building item's title from the queue
  const buildingItem = queueData?.items?.find(
    (item) => ACTIVE_STATUSES.includes(item.status)
  )
  const buildingTitle = buildingItem?.title ?? 'Building...'

  // --- State 1: Building ---
  if (building > 0) {
    return (
      <button
        onClick={navigateToShredder}
        className="hidden md:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border border-orange-500/40 bg-orange-500/10 hover:bg-orange-500/20 transition-colors cursor-pointer"
        title={`Shredder building: ${buildingTitle}`}
      >
        {/* Spinning circle icon */}
        <svg
          className="animate-spin h-3.5 w-3.5 text-orange-400"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <span className="text-xs font-bold text-orange-400 max-w-[120px] truncate">
          {buildingTitle}
        </span>
        {queued > 0 && (
          <span className="text-xs text-amber-400/70">+{queued}</span>
        )}
      </button>
    )
  }

  // --- State 2: Queued only ---
  if (queued > 0) {
    return (
      <button
        onClick={navigateToShredder}
        className="hidden md:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border border-amber-500/40 bg-amber-500/10 hover:bg-amber-500/20 transition-colors cursor-pointer"
        title={`Shredder: ${queued} item${queued > 1 ? 's' : ''} queued`}
      >
        <span className="relative flex h-2.5 w-2.5">
          <span className="animate-pulse absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-amber-500" />
        </span>
        <span className="text-xs font-bold text-amber-400">
          {queued} queued
        </span>
      </button>
    )
  }

  // --- State 3: Failures (with nothing queued/building and nothing done) ---
  if (failed > 0 && done === 0) {
    return (
      <button
        onClick={navigateToShredder}
        className="hidden md:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border border-red-500/40 bg-red-500/10 hover:bg-red-500/20 transition-colors cursor-pointer"
        title={`Shredder: ${failed} failed`}
      >
        <span className="inline-flex h-2.5 w-2.5 rounded-full bg-red-500" />
        <span className="text-xs font-bold text-red-400">
          {failed} failed
        </span>
      </button>
    )
  }

  // --- State 4: Done (all complete, no failures) ---
  if (total > 0 && done > 0 && failed === 0 && queued === 0 && building === 0) {
    return (
      <button
        onClick={navigateToShredder}
        className="hidden md:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border border-emerald-500/40 bg-emerald-500/10 hover:bg-emerald-500/20 transition-colors cursor-pointer"
        title={`Shredder: ${done} complete`}
      >
        {/* Checkmark icon */}
        <svg className="h-3 w-3 text-emerald-400" viewBox="0 0 20 20" fill="currentColor">
          <path
            fillRule="evenodd"
            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
            clipRule="evenodd"
          />
        </svg>
        <span className="text-xs font-bold text-emerald-400">
          {done} done
        </span>
      </button>
    )
  }

  // --- State 5: Idle / READY (default) ---
  return (
    <button
      onClick={navigateToShredder}
      className="hidden md:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border border-emerald-500/40 bg-emerald-500/10 hover:bg-emerald-500/20 transition-colors cursor-pointer"
      title="PRD Shredder — ready for PRDs"
    >
      <span className="relative flex h-2.5 w-2.5">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
        <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500" />
      </span>
      <span className="text-xs font-bold text-emerald-400">READY</span>
    </button>
  )
}
