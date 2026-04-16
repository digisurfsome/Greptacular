/**
 * TokenBudgetBadge - Header pill showing CURRENT workspace conversation
 * context-window usage in "used / max" format (e.g. "Ctx: 156K / 200K").
 *
 * Data source: the per-conversation token log summary for whichever
 * conversation is currently active (parsed from URL hash). Main-agent only
 * by construction — subagent (Task tool) usage is already rolled into each
 * main-agent turn's reported totals by the Claude SDK, so nothing to filter.
 * Updates every 5s.
 *
 * Color thresholds are % of context window, so they work for both 200K and
 * 1M conversations:
 *   Green:  <50% full
 *   Yellow: 50–75%
 *   Orange: 75–90%
 *   Red:    >90%
 *
 * Renders null when the user is NOT on a workspace conversation page
 * (i.e. hash is not `#/workspace/chat/{id}`), or when no token data has
 * been logged yet for the current conversation. Hidden on mobile.
 *
 * Clicking navigates to the full Token Budget dashboard.
 */

import { Zap } from 'lucide-react'
import { useCurrentWorkspaceTokenUsage } from '../hooks/useTokenBudget'

/** Format token count to compact display (e.g. 32K, 1.2M). */
function formatCompact(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`
  return String(n)
}

/** Format the max-context label (e.g. 200000 → "200K", 1000000 → "1M"). */
function formatMax(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(0)}M`
  return `${Math.round(n / 1_000)}K`
}

/** Color based on percentage of context window filled. */
function badgeBgColor(tokens: number, max: number): string {
  const pct = max > 0 ? tokens / max : 0
  if (pct > 0.9) return 'bg-red-500 text-white'
  if (pct > 0.75) return 'bg-orange-500 text-white'
  if (pct > 0.5) return 'bg-yellow-400 text-yellow-900'
  return 'bg-green-500 text-white'
}

export function TokenBudgetBadge() {
  const { data: summary } = useCurrentWorkspaceTokenUsage()

  // Hide the badge entirely when there is no active workspace conversation
  // or when no token data has been logged yet.
  if (!summary) return null
  const tokens = summary.current_context_tokens ?? 0
  if (tokens <= 0) return null

  const maxTokens = summary.max_context_tokens ?? 200_000
  const label = `Ctx: ${formatCompact(tokens)} / ${formatMax(maxTokens)}`

  return (
    <button
      onClick={() => { window.location.hash = '#/token-budget' }}
      className={`hidden md:inline-flex items-center gap-1 text-xs font-bold px-2 py-0.5 rounded-full cursor-pointer transition-colors hover:opacity-90 ${badgeBgColor(tokens, maxTokens)}`}
      title="Current conversation context window (updates every 5s). Click for Token Budget dashboard."
    >
      <Zap size={10} />
      {label}
    </button>
  )
}
