/**
 * PhaseStatusSidebar — Clickable phase list with live status icons.
 *
 * Compact sidebar showing each phase's current status:
 * - Gray circle = pending
 * - Cyan pulse = active
 * - Green check = completed
 * - Red X = failed
 *
 * Click a completed phase to see its summary (timing, tokens).
 * Polls the same build-status endpoint as the dashboard.
 */

import { useState, useEffect, useCallback } from 'react'
import {
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  XCircle,
  Circle,
  Loader2,
  Clock,
  LayoutList,
} from 'lucide-react'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface BuildStatusResponse {
  status: 'idle' | 'running' | 'completed' | 'failed' | 'stopped'
  pid: number | null
  project_dir: string | null
  elapsed_seconds: number
  current_phase: number
  total_phases: number
  phase_statuses: Record<string, string>
  phase_timings: Record<string, { elapsed_seconds: number; status: string }>
  total_tokens: number
  log_lines_count: number
}

interface PhaseStatusSidebarProps {
  refreshInterval: number
  collapsed?: boolean
  onToggle?: () => void
}

// ---------------------------------------------------------------------------
// API
// ---------------------------------------------------------------------------

const API_BASE = import.meta.env.DEV ? 'http://localhost:8888' : ''

async function fetchBuildStatus(): Promise<BuildStatusResponse> {
  const res = await fetch(`${API_BASE}/api/cli-scripter/build-status`)
  if (!res.ok) throw new Error('Failed to fetch build status')
  return res.json()
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatElapsed(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  if (mins > 60) {
    const hrs = Math.floor(mins / 60)
    return `${hrs}h ${mins % 60}m`
  }
  return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`
}

// ---------------------------------------------------------------------------
// Phase Item
// ---------------------------------------------------------------------------

interface PhaseItemData {
  key: string
  label: string
  status: string
  elapsed: number
}

function PhaseItem({ phase }: { phase: PhaseItemData }) {
  const [expanded, setExpanded] = useState(false)
  const isCompleted = phase.status === 'completed'
  const canExpand = isCompleted || phase.status === 'failed'

  const StatusIcon = () => {
    switch (phase.status) {
      case 'completed':
        return <CheckCircle2 size={14} className="text-green-400 shrink-0" />
      case 'failed':
        return <XCircle size={14} className="text-red-400 shrink-0" />
      case 'active':
        return <Loader2 size={14} className="text-cyan-400 animate-spin shrink-0" />
      default:
        return <Circle size={14} className="text-zinc-600 shrink-0" />
    }
  }

  return (
    <div>
      <button
        onClick={() => canExpand && setExpanded(!expanded)}
        className={`w-full flex items-center gap-2 px-3 py-2 text-left rounded-lg transition-colors ${
          canExpand ? 'hover:bg-zinc-800/40 cursor-pointer' : 'cursor-default'
        } ${phase.status === 'active' ? 'bg-cyan-900/10' : ''}`}
      >
        <StatusIcon />
        <span className={`text-sm flex-1 truncate ${
          phase.status === 'active' ? 'text-cyan-300 font-medium' :
          phase.status === 'completed' ? 'text-green-300' :
          phase.status === 'failed' ? 'text-red-300' :
          'text-zinc-500'
        }`}>
          {phase.label}
        </span>
        {phase.elapsed > 0 && (
          <span className="text-[10px] text-zinc-600 shrink-0">
            {formatElapsed(phase.elapsed)}
          </span>
        )}
        {canExpand && (
          expanded ? (
            <ChevronDown size={12} className="text-zinc-600 shrink-0" />
          ) : (
            <ChevronRight size={12} className="text-zinc-600 shrink-0" />
          )
        )}
      </button>

      {/* Expanded detail */}
      {expanded && canExpand && (
        <div className="ml-8 mr-3 mb-2 px-3 py-2 bg-zinc-900/40 rounded-lg border border-zinc-800/50 text-xs text-zinc-500 space-y-1">
          <div className="flex items-center gap-1">
            <Clock size={10} />
            Duration: {formatElapsed(phase.elapsed)}
          </div>
          <div>
            Status: <span className={phase.status === 'completed' ? 'text-green-400' : 'text-red-400'}>
              {phase.status}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export function PhaseStatusSidebar({
  refreshInterval,
  collapsed: controlledCollapsed,
  onToggle,
}: PhaseStatusSidebarProps) {
  const [internalCollapsed, setInternalCollapsed] = useState(false)
  const collapsed = controlledCollapsed !== undefined ? controlledCollapsed : internalCollapsed
  const toggleCollapsed = onToggle || (() => setInternalCollapsed((p) => !p))

  const [buildData, setBuildData] = useState<BuildStatusResponse | null>(null)

  const pollStatus = useCallback(async () => {
    try {
      const data = await fetchBuildStatus()
      setBuildData(data)
    } catch {
      // Silently fail
    }
  }, [])

  useEffect(() => {
    pollStatus()
    if (refreshInterval <= 0) return
    const timer = setInterval(pollStatus, refreshInterval)
    return () => clearInterval(timer)
  }, [refreshInterval, pollStatus])

  // Build phase list
  const phases: PhaseItemData[] = []

  if (buildData && buildData.status !== 'idle') {
    // Architect (key 0)
    phases.push({
      key: '0',
      label: 'Architect',
      status: buildData.phase_statuses['0'] || 'pending',
      elapsed: buildData.phase_timings['0']?.elapsed_seconds || 0,
    })

    // Build phases
    for (let i = 1; i <= buildData.total_phases; i++) {
      phases.push({
        key: String(i),
        label: `Phase ${i}`,
        status: buildData.phase_statuses[String(i)] || 'pending',
        elapsed: buildData.phase_timings[String(i)]?.elapsed_seconds || 0,
      })
    }

    // Verifier (key -1)
    phases.push({
      key: '-1',
      label: 'Verifier',
      status: buildData.phase_statuses['-1'] || 'pending',
      elapsed: buildData.phase_timings['-1']?.elapsed_seconds || 0,
    })

    // Cartographer (key -2)
    phases.push({
      key: '-2',
      label: 'Cartographer',
      status: buildData.phase_statuses['-2'] || 'pending',
      elapsed: buildData.phase_timings['-2']?.elapsed_seconds || 0,
    })
  }

  // If no build has started, show minimal state
  if (!buildData || buildData.status === 'idle') {
    return null
  }

  const completedCount = phases.filter((p) => p.status === 'completed').length
  const totalCount = phases.length

  return (
    <div className="bg-zinc-800/40 border border-zinc-700/60 rounded-xl overflow-hidden">
      {/* Header */}
      <button
        onClick={toggleCollapsed}
        className="w-full flex items-center gap-2 px-4 py-2.5 hover:bg-zinc-800/60 transition-colors"
      >
        {collapsed ? (
          <ChevronRight size={14} className="text-zinc-500" />
        ) : (
          <ChevronDown size={14} className="text-zinc-500" />
        )}
        <LayoutList size={14} className="text-orange-400" />
        <span className="text-sm text-zinc-300 font-medium">Phase Status</span>
        <span className="text-xs text-zinc-600 ml-auto">
          {completedCount}/{totalCount}
        </span>
      </button>

      {/* Phase list */}
      {!collapsed && (
        <div className="border-t border-zinc-800 py-1">
          {phases.map((phase) => (
            <PhaseItem key={phase.key} phase={phase} />
          ))}
        </div>
      )}
    </div>
  )
}
