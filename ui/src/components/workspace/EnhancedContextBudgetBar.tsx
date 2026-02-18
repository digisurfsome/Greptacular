/**
 * EnhancedContextBudgetBar
 *
 * Large, always-visible context window meter for the workspace.
 * Shows token usage at a glance with a bold progress bar,
 * percentage, and color-coded segments.
 *
 * On 1M API panels, shows:
 * - Live dollar cost that updates as tokens increase
 * - 200K pricing cliff marker (amber line on the progress bar)
 * - STD RATE / 2x RATE indicator when crossing the threshold
 */

import { useMemo } from 'react'

interface ContextBudgetSegment {
  label: string
  tokens: number
  color: string
  hoverColor: string
}

interface EnhancedContextBudgetBarProps {
  /** Total context window size in tokens */
  totalBudget: number
  /** Tokens used by messages */
  messageTokens: number
  /** Tokens used by the current summary */
  summaryTokens: number
  /** Tokens used by library files in context */
  libraryTokens?: number
  /** Tokens used by repository context */
  repoTokens?: number
  /** Number of messages loaded in context */
  messageCount: number
  /** Whether a response is currently streaming */
  isStreaming?: boolean
  /** Model for cost estimation on API panels. Only shown on 1M panels. */
  preferredModel?: 'opus' | 'sonnet'
}

/** Format a token count as a human-readable string with K/M suffixes. */
export function formatTokenCount(tokens: number): string {
  if (tokens >= 1_000_000) return `${(tokens / 1_000_000).toFixed(1)}M`
  if (tokens >= 1_000) return `${(tokens / 1_000).toFixed(1)}K`
  return String(tokens)
}

/** Returns a CSS class for the chat area background based on context usage. */
export function getContextWarningClass(usagePercent: number): string {
  if (usagePercent > 90) return 'bg-destructive/5'
  if (usagePercent > 80) return 'bg-[color:var(--color-status-pending)]/10'
  return ''
}

/** Pick a color for the percentage text based on usage and pricing tier. */
function usageColor(percent: number, totalBudget: number, usedTokens: number): string {
  // On 1M panels, warn at the 200K pricing cliff
  if (totalBudget === 1_000_000 && usedTokens > 200_000) {
    if (percent > 90) return 'text-destructive'
    return 'text-amber-400' // Premium pricing zone
  }
  if (percent > 90) return 'text-destructive'
  if (percent > 75) return 'text-orange-400'
  if (percent > 50) return 'text-yellow-400'
  return 'text-emerald-400'
}

// Input pricing per million tokens
const INPUT_RATES = {
  opus:   { standard: 5, extended: 10 },
  sonnet: { standard: 3, extended: 6 },
} as const

/** Estimate the input cost for the current conversation. */
function estimateInputCost(inputTokens: number, model: 'opus' | 'sonnet'): string {
  if (inputTokens <= 0) return '$0.00'
  const isExtended = inputTokens > 200_000
  const rate = isExtended ? INPUT_RATES[model].extended : INPUT_RATES[model].standard
  const cost = (inputTokens / 1_000_000) * rate
  if (cost < 0.01) return '<$0.01'
  return `$${cost.toFixed(2)}`
}

/** Large, always-visible context budget meter. */
export function EnhancedContextBudgetBar({
  totalBudget,
  messageTokens,
  summaryTokens,
  libraryTokens = 0,
  repoTokens = 0,
  messageCount,
  isStreaming = false,
  preferredModel,
}: EnhancedContextBudgetBarProps): React.JSX.Element {
  const usedTokens = messageTokens + summaryTokens + libraryTokens + repoTokens
  const usagePercent = totalBudget > 0 ? (usedTokens / totalBudget) * 100 : 0

  // Show cost on 1M API panels when a model is specified
  const showCost = totalBudget === 1_000_000 && !!preferredModel
  const isExtendedPricing = usedTokens > 200_000

  const segments: ContextBudgetSegment[] = useMemo(() => [
    {
      label: 'Summary',
      tokens: summaryTokens,
      color: 'bg-primary/60',
      hoverColor: 'hover:bg-primary/70',
    },
    {
      label: 'Messages',
      tokens: messageTokens,
      color: 'bg-primary/30',
      hoverColor: 'hover:bg-primary/40',
    },
    {
      label: 'Library',
      tokens: libraryTokens,
      color: 'bg-blue-500/50',
      hoverColor: 'hover:bg-blue-500/60',
    },
    {
      label: 'Repos',
      tokens: repoTokens,
      color: 'bg-green-500/50',
      hoverColor: 'hover:bg-green-500/60',
    },
  ], [summaryTokens, messageTokens, libraryTokens, repoTokens])

  const segmentWidths = useMemo(() => {
    if (totalBudget === 0) return segments.map(() => 0)
    return segments.map(s => Math.max(0, (s.tokens / totalBudget) * 100))
  }, [segments, totalBudget])

  const segmentOffsets = useMemo(() => {
    const offsets: number[] = []
    let cumulative = 0
    for (const w of segmentWidths) {
      offsets.push(cumulative)
      cumulative += w
    }
    return offsets
  }, [segmentWidths])

  return (
    <div className="px-4 py-3 border-b border-border bg-card/80">
      {/* Main row: tokens | cost | max */}
      <div className="flex items-center justify-between mb-2">
        {/* Left: percentage + token count */}
        <div className="flex items-center gap-2">
          <span className={`text-lg font-bold tabular-nums ${usageColor(usagePercent, totalBudget, usedTokens)}`}>
            {usagePercent < 1 && usagePercent > 0 ? usagePercent.toFixed(2) : usagePercent.toFixed(1)}%
          </span>
          <span className="text-sm font-semibold text-foreground tabular-nums">
            {formatTokenCount(usedTokens)}
          </span>
        </div>

        {/* Center: live dollar cost (only on 1M API panels) */}
        {showCost && (
          <div className="flex items-center gap-1.5">
            <span className={`text-base font-bold tabular-nums ${
              isExtendedPricing ? 'text-amber-400' : 'text-emerald-400'
            }`}>
              {estimateInputCost(usedTokens, preferredModel!)}
            </span>
            <span className={`text-[9px] font-mono font-bold px-1 py-0.5 rounded ${
              isExtendedPricing
                ? 'bg-amber-500/20 text-amber-500'
                : 'bg-emerald-500/20 text-emerald-500'
            }`}>
              {isExtendedPricing ? '2x' : 'STD'}
            </span>
          </div>
        )}

        {/* Right: max budget + message count */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground tabular-nums">
            / {formatTokenCount(totalBudget)}
          </span>
          <span className="text-xs text-muted-foreground/60 tabular-nums">
            {messageCount} msg{messageCount !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      {/* Thick progress bar */}
      <div className="relative h-4 rounded-full bg-muted overflow-hidden">
        {segments.map((segment, i) => {
          if (segment.tokens <= 0) return null
          return (
            <div
              key={segment.label}
              className={`absolute top-0 h-full transition-all duration-500 ease-out ${segment.color} ${segment.hoverColor} group`}
              style={{
                left: `${segmentOffsets[i]}%`,
                width: `${segmentWidths[i]}%`,
              }}
              title={`${segment.label}: ${formatTokenCount(segment.tokens)} tokens`}
            >
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 hidden group-hover:block z-10">
                <div className="bg-popover text-popover-foreground text-xs rounded-md px-2 py-1 shadow-md border border-border whitespace-nowrap">
                  {segment.label}: {formatTokenCount(segment.tokens)} tokens
                  {segment.label === 'Messages' && ` across ${messageCount} messages`}
                </div>
              </div>
            </div>
          )
        })}

        {/* 200K pricing cliff marker — only on 1M context panels */}
        {totalBudget === 1_000_000 && (
          <div
            className={`absolute top-0 h-full w-0.5 z-10 ${
              isExtendedPricing ? 'bg-amber-500' : 'bg-amber-500/50'
            }`}
            style={{ left: '20%' }}
            title="200K pricing threshold — above this, all tokens cost 2x input / 1.5x output"
          />
        )}

        {isStreaming && (
          <div className="absolute top-0 right-0 h-full w-12 animate-shimmer bg-gradient-to-r from-transparent via-white/20 to-transparent" />
        )}
      </div>
    </div>
  )
}
