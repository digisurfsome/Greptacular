/**
 * DunkStack Context Gauge
 *
 * Visual context window usage meter with color-coded zones per the PRD:
 * - Green: 0-70% (safe zone)
 * - Yellow: 70-85% (operating zone for file-based system)
 * - Orange: 85-90% (approaching warning threshold)
 * - Red: 90-100% (warning/danger zone)
 *
 * Also displays safety tier indicators (OK / WARNING / HANDOFF / HARD STOP)
 * and session summary stats (total tokens, cost, API calls, avg per call).
 */

import { useMemo } from 'react'
import { Activity, AlertTriangle, ShieldAlert, XOctagon, RotateCcw } from 'lucide-react'
import type { DunkStackSafetyStatus } from '@/lib/api'

interface DunkStackContextGaugeProps {
  /** Total tokens used (input + output cumulative) */
  totalTokens: number
  /** Model context window limit */
  modelLimit: number
  /** Input tokens cumulative */
  inputTokens: number
  /** Output tokens cumulative */
  outputTokens: number
  /** Cache read tokens (latest, not cumulative) */
  cacheReadTokens: number
  /** Total cost in USD */
  totalCost: number
  /** Number of API calls */
  apiCalls: number
  /** Mode: subscription | api */
  mode: string
  /** Current safety status */
  safety: DunkStackSafetyStatus | null
  /** Whether gauge is streaming/updating */
  isStreaming?: boolean
  /** Callback to reset token tracking */
  onReset?: () => void
}

function formatTokenCount(tokens: number): string {
  if (tokens >= 1_000_000) return `${(tokens / 1_000_000).toFixed(1)}M`
  if (tokens >= 1_000) return `${(tokens / 1_000).toFixed(1)}K`
  return String(tokens)
}

function getGaugeColor(pct: number): string {
  if (pct >= 90) return 'bg-red-500'
  if (pct >= 85) return 'bg-orange-500'
  if (pct >= 70) return 'bg-yellow-500'
  return 'bg-emerald-500'
}

function getTextColor(pct: number): string {
  if (pct >= 90) return 'text-red-500'
  if (pct >= 85) return 'text-orange-400'
  if (pct >= 70) return 'text-yellow-400'
  return 'text-emerald-400'
}

function SafetyBadge({ safety }: { safety: DunkStackSafetyStatus | null }) {
  if (!safety) return null

  const config = {
    0: { icon: Activity, bg: 'bg-emerald-500/15', text: 'text-emerald-500', border: 'border-emerald-500/30' },
    1: { icon: AlertTriangle, bg: 'bg-orange-500/15', text: 'text-orange-500', border: 'border-orange-500/30' },
    2: { icon: ShieldAlert, bg: 'bg-red-500/15', text: 'text-red-500', border: 'border-red-500/30' },
    3: { icon: XOctagon, bg: 'bg-red-600/20', text: 'text-red-600', border: 'border-red-600/40' },
  }[safety.tier] ?? { icon: Activity, bg: 'bg-muted', text: 'text-muted-foreground', border: 'border-border' }

  const Icon = config.icon

  return (
    <div
      className={`flex items-center gap-1.5 px-2 py-1 rounded-md border ${config.bg} ${config.border}`}
      title={safety.message}
    >
      <Icon size={14} className={config.text} />
      <span className={`text-xs font-bold ${config.text}`}>
        {safety.label}
      </span>
    </div>
  )
}

export function DunkStackContextGauge({
  totalTokens,
  modelLimit,
  inputTokens,
  outputTokens,
  cacheReadTokens,
  totalCost,
  apiCalls,
  mode,
  safety,
  isStreaming = false,
  onReset,
}: DunkStackContextGaugeProps): React.JSX.Element {
  const usagePct = useMemo(
    () => modelLimit > 0 ? Math.min(100, (totalTokens / modelLimit) * 100) : 0,
    [totalTokens, modelLimit]
  )

  const avgPerCall = useMemo(
    () => apiCalls > 0 ? Math.round(totalTokens / apiCalls) : 0,
    [totalTokens, apiCalls]
  )

  const remaining = useMemo(
    () => Math.max(0, modelLimit - totalTokens),
    [modelLimit, totalTokens]
  )

  return (
    <div className="px-4 py-3 border-b border-border bg-card/80">
      {/* Row 1: Percentage, safety badge, stats, model limit */}
      <div className="flex items-center justify-between mb-2">
        {/* Left: percentage + total */}
        <div className="flex items-center gap-3">
          <span className={`text-2xl font-bold tabular-nums ${getTextColor(usagePct)}`}>
            {usagePct < 1 && usagePct > 0 ? usagePct.toFixed(2) : usagePct.toFixed(1)}%
          </span>
          <span className="text-sm font-semibold text-foreground tabular-nums">
            {formatTokenCount(totalTokens)}
          </span>
          <SafetyBadge safety={safety} />
        </div>

        {/* Center: Input / Output / Cache breakdown */}
        {(inputTokens > 0 || outputTokens > 0) && (
          <div className="flex items-center gap-3">
            <div className="flex flex-col items-center">
              <span className="text-[10px] text-muted-foreground uppercase tracking-wider leading-none mb-0.5">In</span>
              <span className="text-sm font-bold font-mono tabular-nums text-foreground leading-none">
                {formatTokenCount(inputTokens)}
              </span>
            </div>
            <div className="flex flex-col items-center">
              <span className="text-[10px] text-muted-foreground uppercase tracking-wider leading-none mb-0.5">Out</span>
              <span className="text-sm font-bold font-mono tabular-nums text-foreground leading-none">
                {formatTokenCount(outputTokens)}
              </span>
            </div>
            {cacheReadTokens > 0 && (
              <div className="flex flex-col items-center">
                <span className="text-[10px] text-muted-foreground uppercase tracking-wider leading-none mb-0.5">Cache</span>
                <span className="text-sm font-bold font-mono tabular-nums text-blue-400 leading-none">
                  {formatTokenCount(cacheReadTokens)}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Right: cost, calls, avg, limit, mode badge, reset */}
        <div className="flex items-center gap-3">
          {totalCost > 0 && (
            <span className="text-sm font-bold tabular-nums text-emerald-400">
              ${totalCost.toFixed(4)}
            </span>
          )}
          {apiCalls > 0 && (
            <span className="text-xs text-muted-foreground tabular-nums">
              {apiCalls} call{apiCalls !== 1 ? 's' : ''}
              {avgPerCall > 0 && ` (~${formatTokenCount(avgPerCall)}/call)`}
            </span>
          )}
          <span className="text-xs text-muted-foreground tabular-nums">
            / {formatTokenCount(modelLimit)}
          </span>
          <span
            className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded ${
              mode === 'api'
                ? 'bg-blue-500/20 text-blue-400'
                : 'bg-emerald-500/20 text-emerald-400'
            }`}
          >
            {mode === 'api' ? 'API' : 'SUB'}
          </span>
          {onReset && (
            <button
              onClick={onReset}
              className="p-1 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
              title="Reset token tracking"
            >
              <RotateCcw size={12} />
            </button>
          )}
        </div>
      </div>

      {/* Row 2: Progress bar with zone markers */}
      <div className="relative h-4 rounded-full bg-muted overflow-hidden">
        {/* Fill bar */}
        <div
          className={`absolute top-0 left-0 h-full transition-all duration-500 ease-out rounded-full ${getGaugeColor(usagePct)}`}
          style={{ width: `${Math.min(100, usagePct)}%` }}
        />

        {/* Zone markers */}
        <div
          className="absolute top-0 h-full w-px bg-yellow-500/40"
          style={{ left: '70%' }}
          title="70% - Operating zone starts"
        />
        <div
          className="absolute top-0 h-full w-px bg-orange-500/40"
          style={{ left: '85%' }}
          title="85% - Approaching warning"
        />
        <div
          className="absolute top-0 h-full w-px bg-red-500/60"
          style={{ left: '90%' }}
          title="90% - Warning zone"
        />

        {/* Streaming shimmer */}
        {isStreaming && (
          <div className="absolute top-0 right-0 h-full w-12 animate-shimmer bg-gradient-to-r from-transparent via-white/20 to-transparent" />
        )}
      </div>

      {/* Row 3: Remaining capacity */}
      <div className="flex items-center justify-between mt-1.5">
        <span className="text-[10px] text-muted-foreground">
          Remaining: <span className="font-mono font-bold text-foreground">{formatTokenCount(remaining)}</span> tokens
        </span>
        {safety && safety.tier > 0 && (
          <span className={`text-[10px] font-bold ${
            safety.tier >= 2 ? 'text-red-500' : 'text-orange-400'
          }`}>
            {safety.message}
          </span>
        )}
      </div>
    </div>
  )
}
