/**
 * EnhancedContextBudgetBar
 *
 * Segmented context budget visualization with color-coded segments
 * for summary and message tokens, hover tooltips, animated transitions,
 * and warning states at high usage thresholds.
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
  /** Number of messages loaded in context */
  messageCount: number
  /** Whether a response is currently streaming */
  isStreaming?: boolean
}

/** Format a token count as a human-readable string with K/M suffixes. */
export function formatTokenCount(tokens: number): string {
  if (tokens >= 1_000_000) return `${(tokens / 1_000_000).toFixed(1)}M`
  if (tokens >= 1_000) return `${(tokens / 1_000).toFixed(0)}K`
  return String(tokens)
}

/** Returns a CSS class for the chat area background based on context usage. */
export function getContextWarningClass(usagePercent: number): string {
  if (usagePercent > 90) return 'bg-destructive/5'
  if (usagePercent > 80) return 'bg-[color:var(--color-status-pending)]/10'
  return ''
}

/** Segmented context budget bar with hover tooltips and streaming shimmer. */
export function EnhancedContextBudgetBar({
  totalBudget,
  messageTokens,
  summaryTokens,
  messageCount,
  isStreaming = false,
}: EnhancedContextBudgetBarProps): React.JSX.Element {
  const usedTokens = messageTokens + summaryTokens

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
  ], [summaryTokens, messageTokens])

  const segmentWidths = useMemo(() => {
    if (totalBudget === 0) return [0, 0]
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
    <div className="px-4 py-2 border-b border-border bg-card">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-muted-foreground">
          Context: {formatTokenCount(usedTokens)} / {formatTokenCount(totalBudget)}
        </span>
        <span className="text-xs text-muted-foreground">
          {messageCount} messages
        </span>
      </div>

      <div className="relative h-2 rounded-full bg-muted overflow-hidden">
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
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 hidden group-hover:block z-10">
                <div className="bg-popover text-popover-foreground text-xs rounded-md px-2 py-1 shadow-md border border-border whitespace-nowrap">
                  {segment.label}: {formatTokenCount(segment.tokens)} tokens
                  {segment.label === 'Messages' && ` across ${messageCount} messages`}
                </div>
              </div>
            </div>
          )
        })}

        {isStreaming && (
          <div className="absolute top-0 right-0 h-full w-8 animate-shimmer bg-gradient-to-r from-transparent via-white/20 to-transparent" />
        )}
      </div>
    </div>
  )
}
