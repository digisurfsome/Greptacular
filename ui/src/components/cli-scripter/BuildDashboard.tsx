/**
 * BuildDashboard — Live build monitoring strip for CLI Scripter.
 *
 * Displays at the top of the page during active builds. Shows:
 * - Phase progress indicator circles with connecting arrows
 * - Token counter and timer
 * - ETA estimate based on elapsed time per phase
 * - Start/Stop build controls
 *
 * Polls GET /api/cli-scripter/build-status at the configured refresh interval.
 * Phase indicators:
 *   Gray   = pending
 *   Cyan pulse = active (currently running)
 *   Green  = completed successfully
 *   Red    = failed
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import {
  Play,
  Square,
  Clock,
  Zap,
  Loader2,
  CheckCircle2,
  XCircle,
  Circle,
  AlertTriangle,
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

interface BuildDashboardProps {
  projectDir: string
  scriptsSubdir?: string
  refreshInterval: number // ms, 0 = disabled
  onBuildStart?: () => void
  onBuildEnd?: (status: string) => void
}

// ---------------------------------------------------------------------------
// API helpers
// ---------------------------------------------------------------------------

const API_BASE = import.meta.env.DEV ? 'http://localhost:8888' : ''

async function fetchBuildStatus(): Promise<BuildStatusResponse> {
  const res = await fetch(`${API_BASE}/api/cli-scripter/build-status`)
  if (!res.ok) throw new Error('Failed to fetch build status')
  return res.json()
}

async function startBuild(projectDir: string, scriptsSubdir: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/cli-scripter/start-build`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project_dir: projectDir, scripts_subdir: scriptsSubdir }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Failed to start build')
  }
}

async function stopBuild(): Promise<void> {
  const res = await fetch(`${API_BASE}/api/cli-scripter/stop-build`, {
    method: 'POST',
  })
  if (!res.ok) throw new Error('Failed to stop build')
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatElapsed(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  if (mins > 60) {
    const hrs = Math.floor(mins / 60)
    const remainMins = mins % 60
    return `${hrs}h ${remainMins}m ${secs}s`
  }
  return `${mins}m ${secs}s`
}

function estimateETA(
  elapsed: number,
  currentPhase: number,
  totalPhases: number,
): string {
  if (currentPhase <= 0 || totalPhases <= 0) return '--'
  // Rough: time so far / phases done * phases remaining
  const avgPerPhase = elapsed / Math.max(currentPhase, 1)
  const remaining = (totalPhases - currentPhase) * avgPerPhase
  if (remaining <= 0) return '< 1m'
  return `~${formatElapsed(remaining)}`
}

// ---------------------------------------------------------------------------
// Phase Indicator
// ---------------------------------------------------------------------------

function PhaseIndicator({
  label,
  status,
  elapsed,
}: {
  label: string
  status: string
  elapsed?: number
}) {
  // Status-based styling
  const statusStyles = {
    pending: 'border-zinc-600 text-zinc-500',
    active: 'border-cyan-500 text-cyan-300 animate-pulse',
    completed: 'border-green-500 text-green-300',
    failed: 'border-red-500 text-red-300',
  }
  const style = statusStyles[status as keyof typeof statusStyles] || statusStyles.pending

  const StatusIcon = () => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 size={12} className="text-green-400" />
      case 'failed':
        return <XCircle size={12} className="text-red-400" />
      case 'active':
        return <Loader2 size={12} className="text-cyan-400 animate-spin" />
      default:
        return <Circle size={12} className="text-zinc-600" />
    }
  }

  return (
    <div className={`flex flex-col items-center gap-0.5 min-w-[70px]`}>
      <div className={`border rounded-lg px-2 py-1 text-center ${style} bg-zinc-900/60`}>
        <div className="flex items-center gap-1 justify-center">
          <StatusIcon />
          <span className="text-[10px] font-medium truncate max-w-[60px]">{label}</span>
        </div>
      </div>
      {elapsed !== undefined && elapsed > 0 && (
        <span className="text-[9px] text-zinc-600">{formatElapsed(elapsed)}</span>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export function BuildDashboard({
  projectDir,
  scriptsSubdir = 'scripts/cli-scripter',
  refreshInterval,
  onBuildStart,
  onBuildEnd,
}: BuildDashboardProps) {
  const [buildStatus, setBuildStatus] = useState<BuildStatusResponse | null>(null)
  const [starting, setStarting] = useState(false)
  const [stopping, setStopping] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const prevStatusRef = useRef<string>('idle')

  // Poll build status at the configured interval
  const pollStatus = useCallback(async () => {
    try {
      const status = await fetchBuildStatus()
      setBuildStatus(status)

      // Detect build end transitions
      if (
        prevStatusRef.current === 'running' &&
        status.status !== 'running' &&
        onBuildEnd
      ) {
        onBuildEnd(status.status)
      }
      prevStatusRef.current = status.status
    } catch {
      // Silently fail on poll errors — the build may have been stopped
    }
  }, [onBuildEnd])

  useEffect(() => {
    // Initial fetch
    pollStatus()

    if (refreshInterval <= 0) return
    const timer = setInterval(pollStatus, refreshInterval)
    return () => clearInterval(timer)
  }, [refreshInterval, pollStatus])

  const handleStart = async () => {
    if (!projectDir) return
    setStarting(true)
    setError(null)
    try {
      await startBuild(projectDir, scriptsSubdir)
      onBuildStart?.()
      // Immediately refresh status
      await pollStatus()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start build')
    } finally {
      setStarting(false)
    }
  }

  const handleStop = async () => {
    setStopping(true)
    try {
      await stopBuild()
      await pollStatus()
    } catch {
      // Ignore stop errors
    } finally {
      setStopping(false)
    }
  }

  const isRunning = buildStatus?.status === 'running'
  const isFinished =
    buildStatus?.status === 'completed' ||
    buildStatus?.status === 'failed' ||
    buildStatus?.status === 'stopped'

  // Don't render the dashboard if there's never been a build
  if (!buildStatus || (buildStatus.status === 'idle' && !starting)) {
    return (
      <div className="bg-zinc-800/40 border border-zinc-700/60 rounded-xl p-4 mb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Play size={16} className="text-orange-400" />
            <span className="text-sm text-zinc-300 font-medium">Build Dashboard</span>
            <span className="text-xs text-zinc-600">Ready to build</span>
          </div>
          <button
            onClick={handleStart}
            disabled={starting || !projectDir}
            className="flex items-center gap-1.5 bg-green-600/20 border border-green-700/40 rounded-lg px-3 py-1.5 text-green-300 text-sm hover:border-green-500/60 hover:bg-green-600/30 transition-all disabled:opacity-50"
          >
            {starting ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <Play size={14} />
            )}
            {starting ? 'Starting...' : 'Start Build'}
          </button>
        </div>
        {error && (
          <div className="mt-2 flex items-center gap-1 text-xs text-red-400">
            <AlertTriangle size={12} />
            {error}
          </div>
        )}
      </div>
    )
  }

  // Active or completed build — show full dashboard
  const phases = buildStatus.total_phases || 0
  const currentPhase = buildStatus.current_phase
  const elapsed = buildStatus.elapsed_seconds
  const tokens = buildStatus.total_tokens

  // Build phase indicator list: Architect (0), Phase 1..N, Verifier (-1), Cartographer (-2)
  const phaseList: { key: string; label: string; status: string; elapsed?: number }[] = []

  // Architect (key 0)
  const archStatus = buildStatus.phase_statuses['0'] || 'pending'
  phaseList.push({
    key: '0',
    label: 'Architect',
    status: archStatus,
    elapsed: buildStatus.phase_timings['0']?.elapsed_seconds,
  })

  // Build phases
  for (let i = 1; i <= phases; i++) {
    const status = buildStatus.phase_statuses[String(i)] || 'pending'
    phaseList.push({
      key: String(i),
      label: `Phase ${i}`,
      status,
      elapsed: buildStatus.phase_timings[String(i)]?.elapsed_seconds,
    })
  }

  // Verifier (key -1)
  const verifyStatus = buildStatus.phase_statuses['-1'] || 'pending'
  phaseList.push({
    key: '-1',
    label: 'Verify',
    status: verifyStatus,
    elapsed: buildStatus.phase_timings['-1']?.elapsed_seconds,
  })

  // Cartographer (key -2)
  const cartoStatus = buildStatus.phase_statuses['-2'] || 'pending'
  phaseList.push({
    key: '-2',
    label: 'Docs',
    status: cartoStatus,
    elapsed: buildStatus.phase_timings['-2']?.elapsed_seconds,
  })

  const statusColor = isRunning
    ? 'text-cyan-400'
    : buildStatus.status === 'completed'
      ? 'text-green-400'
      : buildStatus.status === 'failed'
        ? 'text-red-400'
        : 'text-zinc-400'

  const statusLabel = isRunning
    ? 'Building'
    : buildStatus.status === 'completed'
      ? 'Complete'
      : buildStatus.status === 'failed'
        ? 'Failed'
        : buildStatus.status === 'stopped'
          ? 'Stopped'
          : 'Idle'

  return (
    <div className="bg-zinc-800/40 border border-zinc-700/60 rounded-xl p-4 mb-4 space-y-3">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={`w-2.5 h-2.5 rounded-full ${isRunning ? 'bg-cyan-400 animate-pulse' : buildStatus.status === 'completed' ? 'bg-green-400' : buildStatus.status === 'failed' ? 'bg-red-400' : 'bg-zinc-500'}`} />
          <span className={`text-sm font-medium ${statusColor}`}>
            {statusLabel}
          </span>
          {buildStatus.project_dir && (
            <span className="text-xs text-zinc-600 truncate max-w-[200px]">
              {buildStatus.project_dir.split(/[/\\]/).pop()}
            </span>
          )}
          <span className="text-xs text-zinc-600">
            {formatElapsed(elapsed)}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* Stats */}
          <div className="flex items-center gap-3 text-xs text-zinc-400 mr-2">
            <span className="flex items-center gap-1">
              <Zap size={11} className="text-orange-400" />
              {tokens > 0 ? `${Math.round(tokens / 1000)}K` : '--'}
            </span>
            <span className="flex items-center gap-1">
              <Clock size={11} />
              ETA: {isRunning ? estimateETA(elapsed, currentPhase, phases) : '--'}
            </span>
          </div>

          {/* Controls */}
          {isRunning ? (
            <button
              onClick={handleStop}
              disabled={stopping}
              className="flex items-center gap-1 bg-red-600/20 border border-red-700/40 rounded-lg px-3 py-1.5 text-red-300 text-xs hover:border-red-500/60 hover:bg-red-600/30 transition-all disabled:opacity-50"
            >
              {stopping ? (
                <Loader2 size={12} className="animate-spin" />
              ) : (
                <Square size={12} />
              )}
              Stop
            </button>
          ) : (
            <button
              onClick={handleStart}
              disabled={starting || !projectDir}
              className="flex items-center gap-1 bg-green-600/20 border border-green-700/40 rounded-lg px-3 py-1.5 text-green-300 text-xs hover:border-green-500/60 hover:bg-green-600/30 transition-all disabled:opacity-50"
            >
              {starting ? (
                <Loader2 size={12} className="animate-spin" />
              ) : (
                <Play size={12} />
              )}
              {isFinished ? 'Restart' : 'Start'}
            </button>
          )}
        </div>
      </div>

      {/* Phase indicators */}
      <div className="flex items-center gap-1 overflow-x-auto pb-1">
        {phaseList.map((phase, idx) => (
          <div key={phase.key} className="flex items-center gap-1 shrink-0">
            {idx > 0 && (
              <span className="text-orange-500/60 text-xs">→</span>
            )}
            <PhaseIndicator
              label={phase.label}
              status={phase.status}
              elapsed={phase.elapsed}
            />
          </div>
        ))}
      </div>

      {/* Progress bar */}
      {isRunning && phases > 0 && (
        <div className="w-full bg-zinc-800 rounded-full h-1.5">
          <div
            className="bg-gradient-to-r from-cyan-500 to-orange-400 h-1.5 rounded-full transition-all duration-500"
            style={{
              width: `${Math.min(100, (currentPhase / phases) * 100)}%`,
            }}
          />
        </div>
      )}

      {error && (
        <div className="flex items-center gap-1 text-xs text-red-400">
          <AlertTriangle size={12} />
          {error}
        </div>
      )}
    </div>
  )
}
