/**
 * DunkStack Safety Panel
 *
 * Displays the 3-tier context safety system status and controls:
 * - Tier 1 (WARNING at 45%): Notify agent to prepare for handoff
 * - Tier 2 (HANDOFF at 47.5%): Stop coding, write handoff file
 * - Tier 3 (HARD STOP at 50%): Kill session
 *
 * Also shows session control (idle/continue/autopilot) and bridge save.
 */

import { useCallback, useState } from 'react'
import {
  Shield,
  Activity,
  AlertTriangle,
  ShieldAlert,
  XOctagon,
  Pause,
  Play,
  Zap,
  Save,
  FileText,
} from 'lucide-react'
import type { DunkStackSafetyStatus } from '@/lib/api'
import type { DunkStackConfig } from '@/hooks/useDunkStack'

interface DunkStackSafetyPanelProps {
  safety: DunkStackSafetyStatus | null
  config: DunkStackConfig | null
  controlMode: string
  onSetControlMode: (mode: string, message?: string) => Promise<void>
  onSaveBridge: (data: {
    reason?: string
    current_task?: string
  }) => Promise<void>
  usagePercent: number
}

function TierIndicator({
  tier,
  label,
  threshold,
  active,
  icon: Icon,
}: {
  tier: number
  label: string
  threshold: number
  active: boolean
  icon: React.ComponentType<{ size?: number; className?: string }>
}) {
  const colors = {
    0: { bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', text: 'text-emerald-500' },
    1: { bg: 'bg-orange-500/10', border: 'border-orange-500/30', text: 'text-orange-500' },
    2: { bg: 'bg-red-500/10', border: 'border-red-500/30', text: 'text-red-500' },
    3: { bg: 'bg-red-600/15', border: 'border-red-600/40', text: 'text-red-600' },
  }[tier] ?? { bg: 'bg-muted', border: 'border-border', text: 'text-muted-foreground' }

  return (
    <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${
      active ? `${colors.bg} ${colors.border}` : 'bg-muted/30 border-border/50'
    }`}>
      <Icon size={16} className={active ? colors.text : 'text-muted-foreground/40'} />
      <div className="flex-1">
        <span className={`text-xs font-bold ${active ? colors.text : 'text-muted-foreground/40'}`}>
          {label}
        </span>
        <span className="text-[10px] text-muted-foreground ml-2">
          at {threshold}%
        </span>
      </div>
      {active && (
        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${colors.bg} ${colors.text}`}>
          ACTIVE
        </span>
      )}
    </div>
  )
}

export function DunkStackSafetyPanel({
  safety,
  config,
  controlMode,
  onSetControlMode,
  onSaveBridge,
  usagePercent,
}: DunkStackSafetyPanelProps): React.JSX.Element {
  const [saving, setSaving] = useState(false)

  const thresholds = {
    warning: config?.safety?.warning_threshold_pct ?? 45,
    handoff: config?.safety?.handoff_threshold_pct ?? 47.5,
    hardStop: config?.safety?.hard_stop_threshold_pct ?? 50,
  }

  const currentTier = safety?.tier ?? 0

  const handleBridgeSave = useCallback(async () => {
    setSaving(true)
    try {
      await onSaveBridge({ reason: 'manual' })
    } finally {
      setSaving(false)
    }
  }, [onSaveBridge])

  return (
    <div className="flex flex-col gap-4 p-4">
      {/* Safety Tiers */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <Shield size={16} className="text-foreground" />
          <span className="text-sm font-semibold text-foreground">Context Safety</span>
        </div>
        <div className="space-y-2">
          <TierIndicator
            tier={0}
            label="OK"
            threshold={0}
            active={currentTier === 0}
            icon={Activity}
          />
          <TierIndicator
            tier={1}
            label="WARNING"
            threshold={thresholds.warning}
            active={currentTier >= 1}
            icon={AlertTriangle}
          />
          <TierIndicator
            tier={2}
            label="HANDOFF"
            threshold={thresholds.handoff}
            active={currentTier >= 2}
            icon={ShieldAlert}
          />
          <TierIndicator
            tier={3}
            label="HARD STOP"
            threshold={thresholds.hardStop}
            active={currentTier >= 3}
            icon={XOctagon}
          />
        </div>
      </div>

      {/* Session Control */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <Play size={16} className="text-foreground" />
          <span className="text-sm font-semibold text-foreground">Session Control</span>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => onSetControlMode('idle')}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg border text-xs font-bold transition-colors ${
              controlMode === 'idle'
                ? 'bg-muted border-border text-foreground'
                : 'border-border/50 text-muted-foreground hover:bg-muted/50'
            }`}
          >
            <Pause size={12} />
            Idle
          </button>
          <button
            onClick={() => onSetControlMode('continue')}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg border text-xs font-bold transition-colors ${
              controlMode === 'continue'
                ? 'bg-blue-500/15 border-blue-500/30 text-blue-500'
                : 'border-border/50 text-muted-foreground hover:bg-muted/50'
            }`}
          >
            <Play size={12} />
            Continue
          </button>
          <button
            onClick={() => onSetControlMode('autopilot')}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg border text-xs font-bold transition-colors ${
              controlMode === 'autopilot'
                ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-500'
                : 'border-border/50 text-muted-foreground hover:bg-muted/50'
            }`}
          >
            <Zap size={12} />
            Autopilot
          </button>
        </div>
      </div>

      {/* Bridge Save */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <Save size={16} className="text-foreground" />
          <span className="text-sm font-semibold text-foreground">Bridge Save</span>
        </div>
        <button
          onClick={handleBridgeSave}
          disabled={saving}
          className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border bg-card hover:bg-muted text-sm font-medium text-foreground transition-colors disabled:opacity-50"
        >
          <FileText size={14} />
          {saving ? 'Saving...' : 'Save Bridge State'}
        </button>
        <p className="text-[10px] text-muted-foreground mt-1.5">
          Saves current task, progress, and context to .agent/bridge.md for session continuity.
        </p>
      </div>

      {/* Current usage info */}
      <div className="mt-2 p-3 rounded-lg bg-muted/30 border border-border/50">
        <span className="text-[10px] text-muted-foreground block mb-1">Current Usage</span>
        <span className="text-sm font-bold tabular-nums text-foreground">
          {usagePercent.toFixed(1)}%
        </span>
        <span className="text-xs text-muted-foreground ml-2">
          of context window
        </span>
      </div>
    </div>
  )
}
