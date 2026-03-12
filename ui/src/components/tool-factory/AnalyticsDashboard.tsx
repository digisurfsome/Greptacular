/**
 * Analytics Dashboard — usage metrics, tool stats, and tier gauge.
 * Phase 8: SaaS layer UI component.
 * All [ROBOT] — pure React rendering, no LLM calls.
 */

import { useToolUsage, useToolUsageHistory, useToolStats } from '@/hooks/useToolFactory'
import { BarChart3, Zap, Layers, TrendingUp, Package } from 'lucide-react'

function StatCard({
  label,
  value,
  sub,
  icon: Icon,
}: {
  label: string
  value: string | number
  sub?: string
  icon?: React.ElementType
}) {
  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
          {label}
        </span>
        {Icon && <Icon size={14} className="text-muted-foreground" />}
      </div>
      <div className="text-2xl font-semibold text-foreground">{value}</div>
      {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
    </div>
  )
}

function BarChart({
  data,
  maxValue,
  color = 'bg-primary',
}: {
  data: { label: string; value: number }[]
  maxValue?: number
  color?: string
}) {
  const max = maxValue || Math.max(...data.map((d) => d.value), 1)
  return (
    <div className="space-y-2">
      {data.map((item, i) => (
        <div key={i} className="flex items-center gap-3">
          <span className="text-xs text-muted-foreground w-16 truncate text-right">
            {item.label}
          </span>
          <div className="flex-1 h-5 bg-muted rounded-sm overflow-hidden">
            <div
              className={`h-full ${color} rounded-sm transition-all`}
              style={{ width: `${Math.max((item.value / max) * 100, 2)}%` }}
            />
          </div>
          <span className="text-xs font-medium text-foreground w-10 text-right">
            {item.value.toLocaleString()}
          </span>
        </div>
      ))}
    </div>
  )
}

function TierGauge({ used, limit, tier }: { used: number; limit: number; tier: string }) {
  const isUnlimited = limit === -1
  const pct = isUnlimited ? 0 : Math.min((used / Math.max(limit, 1)) * 100, 100)
  const barColor =
    pct >= 90 ? 'bg-red-500' : pct >= 70 ? 'bg-yellow-500' : 'bg-green-500'

  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
          Tier Usage
        </span>
        <span className="text-xs font-semibold text-foreground capitalize px-2 py-0.5 bg-muted rounded-full">
          {tier}
        </span>
      </div>
      {isUnlimited ? (
        <div className="text-sm text-muted-foreground">
          {used} tools generated &middot; Unlimited
        </div>
      ) : (
        <>
          <div className="flex items-baseline gap-1 mb-2">
            <span className="text-2xl font-semibold text-foreground">{used}</span>
            <span className="text-sm text-muted-foreground">/ {limit} tools this month</span>
          </div>
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <div
              className={`h-full ${barColor} rounded-full transition-all`}
              style={{ width: `${pct}%` }}
            />
          </div>
        </>
      )}
    </div>
  )
}

export function AnalyticsDashboard() {
  const { data: usage, isLoading: usageLoading } = useToolUsage()
  const { data: historyData, isLoading: historyLoading } = useToolUsageHistory(6)
  const { data: stats, isLoading: statsLoading } = useToolStats()

  const isLoading = usageLoading || historyLoading || statsLoading

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="animate-pulse bg-muted rounded-lg h-24" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="animate-pulse bg-muted rounded-lg h-48" />
          <div className="animate-pulse bg-muted rounded-lg h-48" />
        </div>
      </div>
    )
  }

  const monthly = usage?.monthly
  const allTime = usage?.all_time
  const tier = usage?.tier ?? 'free'
  const limits = usage?.limits
  const history = historyData?.history ?? []

  // Build chart data from history
  const historyChartData = [...history]
    .reverse()
    .map((m) => ({
      label: m.month.slice(5), // "03" from "2026-03"
      value: m.tools_generated,
    }))

  const tokenChartData = [...history]
    .reverse()
    .map((m) => ({
      label: m.month.slice(5),
      value: m.tokens_used,
    }))

  // Status breakdown from stats
  const statusData = stats?.by_status
    ? Object.entries(stats.by_status as Record<string, number>).map(([label, value]) => ({
        label,
        value,
      }))
    : []

  return (
    <div className="space-y-6">
      {/* Top stats row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Tools This Month"
          value={monthly?.tools_generated ?? 0}
          sub={`${allTime?.total_tools_generated ?? 0} all time`}
          icon={Package}
        />
        <StatCard
          label="Executions"
          value={monthly?.chain_executions ?? 0}
          sub={`${allTime?.total_chain_executions ?? 0} all time`}
          icon={Zap}
        />
        <StatCard
          label="Tokens Used"
          value={(monthly?.tokens_used ?? 0).toLocaleString()}
          sub={`${(allTime?.total_tokens_used ?? 0).toLocaleString()} all time`}
          icon={BarChart3}
        />
        <StatCard
          label="Total Deployed"
          value={allTime?.total_tools_deployed ?? 0}
          sub={`${monthly?.tools_deployed ?? 0} this month`}
          icon={Layers}
        />
      </div>

      {/* Tier gauge */}
      <TierGauge
        used={monthly?.tools_generated ?? 0}
        limit={limits?.tools_per_month ?? 5}
        tier={tier}
      />

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Tools generated by month */}
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp size={14} className="text-muted-foreground" />
            <h3 className="text-sm font-medium text-foreground">Tools by Month</h3>
          </div>
          {historyChartData.length > 0 ? (
            <BarChart data={historyChartData} color="bg-primary" />
          ) : (
            <p className="text-xs text-muted-foreground">No history data yet</p>
          )}
        </div>

        {/* Token usage by month */}
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 size={14} className="text-muted-foreground" />
            <h3 className="text-sm font-medium text-foreground">Token Usage by Month</h3>
          </div>
          {tokenChartData.length > 0 ? (
            <BarChart data={tokenChartData} color="bg-cyan-500" />
          ) : (
            <p className="text-xs text-muted-foreground">No token data yet</p>
          )}
        </div>
      </div>

      {/* Status breakdown */}
      {statusData.length > 0 && (
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center gap-2 mb-4">
            <Layers size={14} className="text-muted-foreground" />
            <h3 className="text-sm font-medium text-foreground">Tools by Status</h3>
          </div>
          <BarChart data={statusData} color="bg-emerald-500" />
        </div>
      )}

      {/* Registry quick stats */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatCard label="Total Tools" value={stats.total_tools ?? 0} />
          <StatCard label="Total Runs" value={stats.total_runs ?? 0} />
          <StatCard label="Total Tokens" value={(stats.total_tokens ?? 0).toLocaleString()} />
          <StatCard
            label="Avg Tokens/Tool"
            value={
              stats.total_tools
                ? Math.round((stats.total_tokens ?? 0) / stats.total_tools).toLocaleString()
                : '0'
            }
          />
        </div>
      )}
    </div>
  )
}
