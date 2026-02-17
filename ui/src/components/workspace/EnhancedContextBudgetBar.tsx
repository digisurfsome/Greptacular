/**
 * EnhancedContextBudgetBar
 *
 * Large, always-visible context window meter for the workspace.
 * Shows token usage at a glance with a bold progress bar,
 * percentage, and color-coded segments.
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

/** Pick a color for the percentage text based on usage. */
function usageColor(percent: number): string {
  if (percent > 90) return 'text-destructive'
  if (percent > 75) return 'text-orange-400'
  if (percent > 50) return 'text-yellow-400'
  return 'text-emerald-400'
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
}: EnhancedContextBudgetBarProps): React.JSX.Element {
  const usedTokens = messageTokens + summaryTokens + libraryTokens + repoTokens
  const usagePercent = totalBudget > 0 ? (usedTokens / totalBudget) * 100 : 0

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
      {/* Main row: usage left, token counts center, messages right */}
      <div className="flex items-center justify-between mb-2">
        <span className={`text-lg font-bold tabular-nums ${usageColor(usagePercent)}`}>
          {usagePercent.toFixed(1)}%
        </span>

        <span className="text-base font-semibold text-foreground tabular-nums">
          {formatTokenCount(usedTokens)}{' '}
          <span className="text-muted-foreground font-normal">/ {formatTokenCount(totalBudget)}</span>
        </span>

        <span className="text-sm text-muted-foreground tabular-nums">
          {messageCount} msg{messageCount !== 1 ? 's' : ''}
        </span>
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

        {isStreaming && (
          <div className="absolute top-0 right-0 h-full w-12 animate-shimmer bg-gradient-to-r from-transparent via-white/20 to-transparent" />
        )}
      </div>
    </div>
  )
}
