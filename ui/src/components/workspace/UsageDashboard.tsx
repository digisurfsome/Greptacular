/**
 * Usage Dashboard
 *
 * Compact expandable panel showing workspace usage across daily, weekly,
 * and monthly periods with cost zone breakdown for the active conversation.
 */

import { useState, useEffect } from 'react'
import { ChevronDown, ChevronUp, TrendingUp, DollarSign, Clock, AlertTriangle } from 'lucide-react'
import { getUsageSummary, getConversationCost } from '@/lib/api'
import type { UsageSummary, CostZone } from '@/lib/api'

interface UsageDashboardProps {
  conversationId: number | null
  contextMode: '1m' | '200k'
}

/** Format token count with K/M suffix. */
function formatTokens(tokens: number): string {
  if (tokens >= 1_000_000) return `${(tokens / 1_000_000).toFixed(1)}M`
  if (tokens >= 1_000) return `${(tokens / 1_000).toFixed(1)}K`
  return String(tokens)
}

/** Format a cost in dollars. */
function formatCost(cost: number): string {
  if (cost < 0.01) return '<$0.01'
  return `$${cost.toFixed(2)}`
}

/** Small horizontal usage meter bar. */
function UsageMeter({ label, tokens, icon }: { label: string; tokens: number; icon: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex items-center gap-1 text-muted-foreground w-20 flex-shrink-0">
        {icon}
        <span className="text-[10px] font-medium">{label}</span>
      </div>
      <span className="text-xs font-mono font-bold text-foreground tabular-nums">
        {formatTokens(tokens)}
      </span>
    </div>
  )
}

export function UsageDashboard({ conversationId, contextMode }: UsageDashboardProps): React.JSX.Element {
  const [expanded, setExpanded] = useState(false)
  const [usage, setUsage] = useState<UsageSummary | null>(null)
  const [costZone, setCostZone] = useState<CostZone | null>(null)

  // Fetch usage data on mount and when expanded
  useEffect(() => {
    getUsageSummary()
      .then(setUsage)
      .catch(() => {})
  }, [expanded])

  // Fetch cost zone for active conversation
  useEffect(() => {
    if (conversationId) {
      getConversationCost(conversationId)
        .then(setCostZone)
        .catch(() => setCostZone(null))
    } else {
      setCostZone(null)
    }
  }, [conversationId])

  const isPremiumZone = costZone?.cost_zone === 'premium'
  const premiumPercent = costZone
    ? Math.round((costZone.premium_tokens / Math.max(1, costZone.total_tokens)) * 100)
    : 0

  // Context window size for the visual bar proportions
  const contextWindowSize = contextMode === '1m' ? 1_000_000 : 200_000

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
            Today: <span className="font-mono font-bold text-foreground">{usage ? formatTokens(usage.daily.total_tokens) : '...'}</span>
          </span>
          {isPremiumZone && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-orange-500/10 text-orange-400 font-medium">
              PREMIUM ZONE
            </span>
          )}
          {costZone && costZone.estimated_cost.total > 0 && (
            <span className="text-[10px] text-muted-foreground">
              ~{formatCost(costZone.estimated_cost.total)} API equiv
            </span>
          )}
        </div>
        {expanded ? <ChevronUp size={12} className="text-muted-foreground" /> : <ChevronDown size={12} className="text-muted-foreground" />}
      </button>

      {/* Expanded: full dashboard */}
      {expanded && (
        <div className="px-4 pb-3 space-y-3">
          {/* Period meters */}
          <div className="space-y-1.5">
            <UsageMeter
              label="Today"
              tokens={usage?.daily.total_tokens ?? 0}
              icon={<Clock size={10} />}
            />
            <UsageMeter
              label="Week"
              tokens={usage?.weekly.total_tokens ?? 0}
              icon={<Clock size={10} />}
            />
            <UsageMeter
              label="Month"
              tokens={usage?.monthly.total_tokens ?? 0}
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
                    style={{ width: `${Math.round((costZone.standard_tokens / contextWindowSize) * 100)}%` }}
                    title={`Standard: ${formatTokens(costZone.standard_tokens)} @ $15/MTok`}
                  />
                )}
                {costZone.premium_tokens > 0 && (
                  <div
                    className="h-full bg-orange-500/60 transition-all"
                    style={{ width: `${Math.round((costZone.premium_tokens / contextWindowSize) * 100)}%` }}
                    title={`Premium: ${formatTokens(costZone.premium_tokens)} @ $22.50/MTok (1.5x)`}
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
                    <span className="font-mono font-bold text-orange-400">{formatTokens(costZone.premium_tokens)}</span>
                  </div>
                )}
              </div>

              {/* Cost estimate */}
              <div className="flex items-center gap-2">
                <DollarSign size={10} className="text-muted-foreground" />
                <span className="text-[10px] text-muted-foreground">
                  API equivalent: <span className="font-mono font-bold text-foreground">{formatCost(costZone.estimated_cost.total)}</span>
                  {costZone.premium_tokens > 0 && (
                    <span className="text-orange-400 ml-1">
                      (+{formatCost(costZone.estimated_cost.premium_surcharge)} premium surcharge)
                    </span>
                  )}
                </span>
              </div>

              {/* Warning if in premium zone */}
              {isPremiumZone && (
                <div className="flex items-center gap-1.5 text-[10px] text-orange-400 bg-orange-500/5 rounded px-2 py-1">
                  <AlertTriangle size={10} />
                  <span>{premiumPercent}% of tokens at premium rate. Each new message costs ~1.5x more.</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
