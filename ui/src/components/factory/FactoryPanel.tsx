/**
 * FactoryPanel - Main factory mode control panel for the Workspace page.
 *
 * Embeds a compact panel with:
 *   1. Factory Toggle (Start/Stop) with status badge
 *   2. Phase Pipeline - horizontal strip showing phase progress
 *   3. Settings Button - opens FactorySettings modal
 *   4. Status bar - current phase, feature counts, rate limit countdown
 *
 * Uses semantic Tailwind tokens for theme compatibility across all themes.
 * Status polling handled by useFactoryStatus (5s interval).
 */

import { useState } from 'react'
import {
  Factory,
  Play,
  Square,
  Settings,
  ChevronRight,
  Clock,
  Loader2,
} from 'lucide-react'
import {
  useFactoryStatus,
  useFactoryStart,
  useFactoryStop,
} from '../../hooks/useFactory'
import { FactorySettings } from './FactorySettings'
import { PhasePRDManager } from './PhasePRDManager'

/** Shape of a single phase from the factory status response. */
interface FactoryPhase {
  number: number
  name?: string
  status: 'completed' | 'running' | 'queued' | 'pending'
  features?: string[]
}

/** Subset of the factory status response we consume. */
interface FactoryStatusData {
  status: 'idle' | 'running' | 'waiting_rate_limit' | 'completed' | 'error'
  phases?: FactoryPhase[]
  current_phase?: number
  total_phases?: number
  features_completed?: number
  features_total?: number
  rate_limit?: { resumes_at?: string }
  handoff_threshold?: number
  handoff_template?: string
}

interface FactoryPanelProps {
  projectName: string | null
  model?: string
  yoloMode?: boolean
}

/**
 * Returns theme-aware color classes for a given phase status.
 * Uses the same tier-indicator pattern from DunkStackSafetyPanel.
 */
function getPhaseClasses(phase: FactoryPhase, isCurrent: boolean): string {
  const base = 'flex-shrink-0 px-2.5 py-1.5 rounded-lg border text-[11px] font-medium transition-all'
  const currentRing = isCurrent ? ' ring-1 ring-ring/40 scale-105' : ''

  switch (phase.status) {
    case 'completed':
      return `${base} bg-emerald-500/15 border-emerald-500/30 text-emerald-600 dark:text-emerald-400${currentRing}`
    case 'running':
      return `${base} bg-blue-500/15 border-blue-500/30 text-blue-600 dark:text-blue-400 animate-pulse${currentRing}`
    case 'queued':
      return `${base} bg-muted/50 border-border text-muted-foreground${currentRing}`
    default:
      return `${base} bg-muted/30 border-border/50 text-muted-foreground/60${currentRing}`
  }
}

export function FactoryPanel({ projectName, model, yoloMode }: FactoryPanelProps): React.JSX.Element {
  const [showSettings, setShowSettings] = useState(false)
  const { data: statusResponse } = useFactoryStatus(projectName)
  const startFactory = useFactoryStart(projectName)
  const stopFactory = useFactoryStop(projectName)

  // Parse the status data from the generic FactoryResponse wrapper
  const status = statusResponse?.data as FactoryStatusData | undefined
  const isRunning = status?.status === 'running'
  const isWaiting = status?.status === 'waiting_rate_limit'
  const isCompleted = status?.status === 'completed'
  const phases = status?.phases ?? []
  const currentPhase = status?.current_phase ?? 0
  const totalPhases = status?.total_phases ?? 0

  const handleStart = () => {
    startFactory.mutate({
      mode: 'continuous',
      model: model || 'claude-opus-4-6',
      yolo_mode: yoloMode || false,
    })
  }

  const handleStop = () => {
    stopFactory.mutate()
  }

  return (
    <div className="border border-border rounded-lg bg-card overflow-hidden shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-muted/30 border-b border-border">
        <div className="flex items-center gap-2">
          <Factory className="w-4 h-4 text-amber-500" />
          <span className="text-sm font-bold text-foreground tracking-wide uppercase">
            Factory Mode
          </span>

          {/* Status badge */}
          {isRunning && (
            <span className="px-2 py-0.5 text-[10px] font-bold bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-500/30 rounded-full animate-pulse">
              RUNNING
            </span>
          )}
          {isWaiting && (
            <span className="px-2 py-0.5 text-[10px] font-bold bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30 rounded-full">
              RATE LIMITED
            </span>
          )}
          {isCompleted && (
            <span className="px-2 py-0.5 text-[10px] font-bold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 rounded-full">
              COMPLETE
            </span>
          )}
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={() => setShowSettings(true)}
            className="p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted rounded transition-colors"
            title="Factory Settings"
            aria-label="Factory Settings"
          >
            <Settings className="w-3.5 h-3.5" />
          </button>

          {!isRunning ? (
            <button
              onClick={handleStart}
              disabled={!projectName || startFactory.isPending}
              className="flex items-center gap-1 px-2.5 py-1 text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white rounded border border-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {startFactory.isPending ? (
                <Loader2 className="w-3 h-3 animate-spin" />
              ) : (
                <Play className="w-3 h-3" />
              )}
              Start
            </button>
          ) : (
            <button
              onClick={handleStop}
              disabled={stopFactory.isPending}
              className="flex items-center gap-1 px-2.5 py-1 text-xs font-bold bg-destructive hover:bg-destructive/90 text-destructive-foreground rounded border border-destructive disabled:opacity-50 transition-colors"
            >
              {stopFactory.isPending ? (
                <Loader2 className="w-3 h-3 animate-spin" />
              ) : (
                <Square className="w-3 h-3" />
              )}
              Stop
            </button>
          )}
        </div>
      </div>

      {/* Phase Pipeline -- horizontal scrollable strip */}
      {phases.length > 0 && (
        <div className="px-3 py-2">
          <div className="flex items-center gap-1 overflow-x-auto pb-1">
            {phases.map((phase, i) => (
              <div key={phase.number} className="flex items-center gap-1">
                <div className={getPhaseClasses(phase, phase.number === currentPhase)}>
                  <div className="font-bold">P{phase.number}</div>
                  <div className="text-[10px] opacity-70 truncate max-w-[80px]">
                    {phase.name || `Phase ${phase.number}`}
                  </div>
                  <div className="text-[9px] opacity-50">
                    {phase.features?.length ?? 0} feat
                  </div>
                </div>
                {i < phases.length - 1 && (
                  <ChevronRight className="w-3 h-3 text-muted-foreground/40 flex-shrink-0" />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Phase PRD Documents */}
      <div className="px-3 py-2 border-t border-border/50">
        <PhasePRDManager projectName={projectName} currentPhase={currentPhase} />
      </div>

      {/* Status bar -- only visible while running or rate-limited */}
      {(isRunning || isWaiting) && (
        <div className="px-3 py-1.5 bg-muted/20 border-t border-border/50 text-[11px] text-muted-foreground flex items-center gap-3">
          {isRunning && (
            <>
              <span>Phase {currentPhase}/{totalPhases}</span>
              <span className="text-border">|</span>
              <span>
                {status?.features_completed ?? 0}/{status?.features_total ?? 0} features
              </span>
            </>
          )}
          {isWaiting && status?.rate_limit?.resumes_at && (
            <>
              <Clock className="w-3 h-3 text-amber-500" />
              <span>
                Resumes at{' '}
                {new Date(status.rate_limit.resumes_at).toLocaleTimeString()}
              </span>
            </>
          )}
        </div>
      )}

      {/* Settings Modal */}
      {showSettings && (
        <FactorySettings
          projectName={projectName}
          onClose={() => setShowSettings(false)}
        />
      )}
    </div>
  )
}
