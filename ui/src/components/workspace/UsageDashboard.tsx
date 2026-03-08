/**
 * Usage Dashboard
 *
 * Compact expandable panel showing workspace usage across daily, weekly,
 * and monthly periods with:
 * - Calibrated limit bars (learned from past rate limit events)
 * - Cost zone breakdown for the active conversation
 * - Rate limit event logging for calibration
 * - Premium-zone tracking
 */

import { useState, useEffect, useCallback } from 'react'
import {
  ChevronDown,
  ChevronUp,
  TrendingUp,
  DollarSign,
  Clock,
  AlertTriangle,
  Zap,
  Target,
} from 'lucide-react'
import { getUsageSummary, getConversationCost, logRateLimit, getCalibration } from '@/lib/api'
import type { UsageSummary, CostZone, CalibrationData } from '@/lib/api'

interface UsageDashboardProps {
  conversationId: number | null
  contextMode: '1m' | '200k'
  model?: string
}

function formatTokens(tokens: number): string {
  if (tokens >= 1_000_000) return `${(tokens / 1_000_000).toFixed(1)}M`
  if (tokens >= 1_000) return `${(tokens / 1_000).toFixed(1)}K`
  return String(tokens)
}

function formatCost(cost: number): string {
  if (cost < 0.01) return '<$0.01'
  return `$${cost.toFixed(2)}`
}

/** Bar that shows current usage against a calibrated limit. */
function CalibratedMeter({
  label,
  tokens,
  estimatedLimit,
  safeLimit,
  confidence,
  icon,
}: {
  label: string
  tokens: number
  estimatedLimit: number | null
  safeLimit: number | null
  confidence: string
  icon: React.ReactNode
}) {
  const hasCalibration = estimatedLimit !== null && estimatedLimit > 0
  const percent = hasCalibration ? Math.min(100, (tokens / estimatedLimit) * 100) : 0
  const safePercent = hasCalibration && safeLimit ? (safeLimit / estimatedLimit) * 100 : 90
  const isWarning = hasCalibration && percent >= safePercent
  const isDanger = hasCalibration && percent >= 95

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-muted-foreground">
          {icon}
          <span className="text-[10px] font-medium">{label}</span>
          {confidence !== 'none' && (
            <span
              className={`text-[8px] px-1 py-0.5 rounded ${
                confidence === 'high'
                  ? 'bg-emerald-500/10 text-emerald-400'
                  : confidence === 'medium'
                    ? 'bg-yellow-500/10 text-yellow-400'
                    : 'bg-muted text-muted-foreground'
              }`}
            >
              {confidence}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-xs font-mono font-bold tabular-nums ${
            isDanger ? 'text-destructive' : isWarning ? 'text-orange-400' : 'text-foreground'
          }`}>
            {formatTokens(tokens)}
          </span>
          {hasCalibration && (
            <span className="text-[10px] text-muted-foreground font-mono tabular-nums">
              / ~{formatTokens(estimatedLimit)}
            </span>
          )}
        </div>
      </div>

      {/* Progress bar */}
      {hasCalibration ? (
        <div className="relative h-2.5 rounded-full bg-muted overflow-hidden">
          {/* Usage fill */}
          <div
            className={`absolute top-0 left-0 h-full rounded-full transition-all duration-500 ${
              isDanger ? 'bg-destructive' : isWarning ? 'bg-orange-500' : 'bg-emerald-500/70'
            }`}
            style={{ width: `${Math.min(percent, 100)}%` }}
          />
          {/* Safe limit marker */}
          <div
            className="absolute top-0 h-full w-px bg-yellow-500/60"
            style={{ left: `${safePercent}%` }}
            title={`Safe limit (~${Math.round(safePercent)}%)`}
          />
        </div>
      ) : (
        <div className="h-2.5 rounded-full bg-muted flex items-center justify-center">
          <span className="text-[8px] text-muted-foreground">No calibration data yet</span>
        </div>
      )}

      {/* Warning */}
      {isDanger && (
        <div className="flex items-center gap-1 text-[9px] text-destructive">
          <AlertTriangle size={9} />
          <span>Approaching limit! Consider pausing.</span>
        </div>
      )}
      {isWarning && !isDanger && (
        <div className="flex items-center gap-1 text-[9px] text-orange-400">
          <AlertTriangle size={9} />
          <span>In warning zone -- ~{Math.round(100 - percent)}% remaining</span>
        </div>
      )}
    </div>
  )
}

export function UsageDashboard({ conversationId, contextMode, model = 'opus' }: UsageDashboardProps): React.JSX.Element {
  const [expanded, setExpanded] = useState(false)
  const [usage, setUsage] = useState<UsageSummary | null>(null)
  const [costZone, setCostZone] = useState<CostZone | null>(null)
  const [calibration, setCalibration] = useState<CalibrationData | null>(null)
  const [loggingLimit, setLoggingLimit] = useState<string | null>(null)

  // Fetch usage + calibration data
  useEffect(() => {
    getUsageSummary().then(setUsage).catch(() => {})
    getCalibration().then(setCalibration).catch(() => {})
  }, [expanded])

  // Refresh usage periodically when expanded (every 30s)
  useEffect(() => {
    if (!expanded) return
    const interval = setInterval(() => {
      getUsageSummary().then(setUsage).catch(() => {})
    }, 30000)
    return () => clearInterval(interval)
  }, [expanded])

  // Fetch cost zone for active conversation
  useEffect(() => {
    if (conversationId) {
      getConversationCost(conversationId).then(setCostZone).catch(() => setCostZone(null))
    } else {
      setCostZone(null)
    }
  }, [conversationId])

  const handleLogRateLimit = useCallback(async (eventType: string) => {
    setLoggingLimit(eventType)
    try {
      await logRateLimit(eventType)
      // Refresh calibration data after logging
      const newCal = await getCalibration()
      setCalibration(newCal)
    } catch {
      // Silently fail
    } finally {
      setLoggingLimit(null)
    }
  }, [])

  const isPremiumZone = costZone?.cost_zone === 'premium'
  const premiumPercent = costZone
    ? Math.round((costZone.premium_tokens / Math.max(1, costZone.total_tokens)) * 100)
    : 0

  // Quick summary for collapsed state
  const dailyTokens = usage?.daily.total_tokens ?? 0
  const dailyLimit = calibration?.daily.estimated_limit
  const dailyConfidence = calibration?.daily.confidence ?? 'none'
  // Only show percentage when we have meaningful calibration (medium+ confidence)
  // and cap at 999% to avoid absurd numbers from bad calibration data
  const rawDailyPercent = dailyLimit && dailyLimit > 0 ? Math.round((dailyTokens / dailyLimit) * 100) : null
  const dailyPercent = (rawDailyPercent !== null && (dailyConfidence === 'medium' || dailyConfidence === 'high'))
    ? Math.min(rawDailyPercent, 999)
    : null
  const dailyConvos = usage?.daily.conversation_count ?? 0
  const dailyMsgs = usage?.daily.message_count ?? 0

  return (
    <div className="border-b border-border bg-card/60">
      {/* Collapsed: one-line summary */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center justify-between w-full px-4 py-1.5 text-left hover:bg-muted/30 transition-colors"
      >
        <div className="flex items-center gap-3">
          <TrendingUp size={12} className="text-muted-foreground" />
          <span className="text-[10px] text-muted-foreground">
            Today: <span className="font-mono font-bold text-foreground">{formatTokens(dailyTokens)}</span>
            {dailyPercent !== null && (
              <span className={`ml-1 ${dailyPercent > 90 ? 'text-destructive' : dailyPercent > 75 ? 'text-orange-400' : 'text-muted-foreground'}`}>
                ({dailyPercent}%)
              </span>
            )}
            {dailyConvos > 0 && (
              <span className="ml-1.5 text-muted-foreground/70">
                · {dailyConvos} chat{dailyConvos !== 1 ? 's' : ''} · {dailyMsgs} msg{dailyMsgs !== 1 ? 's' : ''}
              </span>
            )}
          </span>
          {isPremiumZone && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-orange-500/10 text-orange-400 font-medium">
              PREMIUM
            </span>
          )}
          {costZone && costZone.estimated_cost.total > 0 && (
            <span className="text-[10px] text-muted-foreground">
              ~{formatCost(costZone.estimated_cost.total)}
            </span>
          )}
        </div>
        {expanded ? <ChevronUp size={12} className="text-muted-foreground" /> : <ChevronDown size={12} className="text-muted-foreground" />}
      </button>

      {/* Expanded: full dashboard */}
      {expanded && (
        <div className="px-4 pb-3 space-y-4">
          {/* Calibrated period meters */}
          <div className="space-y-3">
            <CalibratedMeter
              label="Daily"
              tokens={usage?.daily.total_tokens ?? 0}
              estimatedLimit={calibration?.daily.estimated_limit ?? null}
              safeLimit={calibration?.daily.safe_limit ?? null}
              confidence={calibration?.daily.confidence ?? 'none'}
              icon={<Clock size={10} />}
            />
            <CalibratedMeter
              label="Weekly"
              tokens={usage?.weekly.total_tokens ?? 0}
              estimatedLimit={calibration?.weekly.estimated_limit ?? null}
              safeLimit={calibration?.weekly.safe_limit ?? null}
              confidence={calibration?.weekly.confidence ?? 'none'}
              icon={<Clock size={10} />}
            />
            <CalibratedMeter
              label="Monthly"
              tokens={usage?.monthly.total_tokens ?? 0}
              estimatedLimit={calibration?.monthly.estimated_limit ?? null}
              safeLimit={calibration?.monthly.safe_limit ?? null}
              confidence={calibration?.monthly.confidence ?? 'none'}
              icon={<Clock size={10} />}
            />
          </div>

          {/* Activity stats */}
          {usage && (
            <div className="flex gap-4 text-[10px] text-muted-foreground">
              <span>{usage.daily.conversation_count} chat{usage.daily.conversation_count !== 1 ? 's' : ''} today</span>
              <span>{usage.daily.message_count} msg{usage.daily.message_count !== 1 ? 's' : ''} today</span>
            </div>
          )}

          {/* Cost zone breakdown */}
          {costZone && costZone.total_tokens > 0 && (
            <div className="space-y-2">
              <div className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                Cost Zone (This Chat)
              </div>

              {/* Visual bar showing standard vs premium */}
              <div className="h-3 rounded-full bg-muted overflow-hidden flex">
                {costZone.standard_tokens > 0 && (
                  <div
                    className="h-full bg-emerald-500/60 transition-all"
                    style={{
                      width: `${Math.round(
                        (costZone.standard_tokens / (contextMode === '1m' ? 1_000_000 : 200_000)) * 100,
                      )}%`,
                    }}
                    title={`Standard: ${formatTokens(costZone.standard_tokens)} @ $${model === 'sonnet' ? '3' : '5'}/MTok`}
                  />
                )}
                {costZone.premium_tokens > 0 && (
                  <div
                    className="h-full bg-orange-500/60 transition-all"
                    style={{
                      width: `${Math.round(
                        (costZone.premium_tokens / (contextMode === '1m' ? 1_000_000 : 200_000)) * 100,
                      )}%`,
                    }}
                    title={`Premium: ${formatTokens(costZone.premium_tokens)} @ $${model === 'sonnet' ? '4.50' : '7.50'}/MTok (1.5x)`}
                  />
                )}
              </div>

              {/* Legend */}
              <div className="flex items-center gap-4 text-[10px]">
                <div className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-emerald-500/60" />
                  <span className="text-muted-foreground">0-200K</span>
                  <span className="font-mono font-bold text-foreground">{formatTokens(costZone.standard_tokens)}</span>
                </div>
                {costZone.premium_tokens > 0 && (
                  <div className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-orange-500/60" />
                    <span className="text-muted-foreground">200K+ (1.5x)</span>
                    <span className="font-mono font-bold text-orange-400">
                      {formatTokens(costZone.premium_tokens)}
                    </span>
                  </div>
                )}
              </div>

              {/* Cost estimate */}
              <div className="flex items-center gap-2">
                <DollarSign size={10} className="text-muted-foreground" />
                <span className="text-[10px] text-muted-foreground">
                  API equiv: <span className="font-mono font-bold text-foreground">{formatCost(costZone.estimated_cost.total)}</span>
                  {costZone.premium_tokens > 0 && (
                    <span className="text-orange-400 ml-1">
                      (+{formatCost(costZone.estimated_cost.premium_surcharge)} surcharge)
                    </span>
                  )}
                </span>
              </div>

              {isPremiumZone && (
                <div className="flex items-center gap-1.5 text-[10px] text-orange-400 bg-orange-500/5 rounded px-2 py-1">
                  <AlertTriangle size={10} />
                  <span>{premiumPercent}% of tokens at premium rate</span>
                </div>
              )}
            </div>
          )}

          {/* Rate limit logging section */}
          <div className="space-y-2 pt-1 border-t border-border">
            <div className="flex items-center gap-1.5 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
              <Target size={10} />
              Calibration
            </div>
            <p className="text-[10px] text-muted-foreground leading-relaxed">
              Hit a rate limit? Log it to calibrate the meters. Each event improves prediction accuracy.
            </p>
            <div className="flex gap-2">
              {(['daily', 'weekly', 'monthly'] as const).map((period) => (
                <button
                  key={period}
                  onClick={() => handleLogRateLimit(period)}
                  disabled={loggingLimit !== null}
                  className="flex items-center gap-1 px-2 py-1 text-[10px] rounded border border-border bg-muted/50 hover:bg-muted text-foreground transition-colors disabled:opacity-50"
                >
                  <Zap size={9} className={loggingLimit === period ? 'animate-pulse text-orange-400' : ''} />
                  {loggingLimit === period ? 'Logging...' : `Hit ${period}`}
                </button>
              ))}
            </div>
            {calibration && (
              <div className="text-[9px] text-muted-foreground">
                {calibration.daily.sample_count > 0 && (
                  <span>Daily: {calibration.daily.sample_count} sample{calibration.daily.sample_count !== 1 ? 's' : ''} · </span>
                )}
                {calibration.weekly.sample_count > 0 && (
                  <span>Weekly: {calibration.weekly.sample_count} sample{calibration.weekly.sample_count !== 1 ? 's' : ''} · </span>
                )}
                {calibration.monthly.sample_count > 0 && (
                  <span>Monthly: {calibration.monthly.sample_count} sample{calibration.monthly.sample_count !== 1 ? 's' : ''}</span>
                )}
                {calibration.daily.sample_count === 0 && calibration.weekly.sample_count === 0 && calibration.monthly.sample_count === 0 && (
                  <span>No calibration data yet. Log rate limit events to enable predictions.</span>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
