/**
 * TokenBudgetBadge - Header pill showing CURRENT workspace conversation
 * context-window usage in "used / max" format (e.g. "Ctx: 156K / 200K").
 *
 * Data source: the per-conversation token log summary for whichever
 * conversation is currently active (parsed from URL hash).
 *
 * Prefers `current_main_context_tokens` — the subagent-excluded value
 * captured from per-message AssistantMessage.usage where
 * parent_tool_use_id is None.  That's the TRUE "agent I'm talking to"
 * size and is the number that matters for the 50%-of-1M degradation
 * threshold.  Falls back to `current_context_tokens` (the SDK's
 * rolled-up value that includes subagent Task turns) for older
 * conversations logged before the main_* columns existed.
 *
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

  // Prefer the main-agent-only context size (subagent Task calls excluded).
  // Falls back to the SDK's rolled-up number when the conversation predates
  // the AssistantMessage.usage capture path.  Both come from the latest
  // result_summary row — neither is a summed estimate, so the $650K bug
  // caused by cumulative char-based math cannot happen here.
  const mainTokens = summary.current_main_context_tokens ?? 0
  const rolledTokens = summary.current_context_tokens ?? 0
  const usingMain = mainTokens > 0
  const tokens = usingMain ? mainTokens : rolledTokens
  if (tokens <= 0) return null

  const maxTokens = summary.max_context_tokens ?? 200_000
  const label = `Ctx: ${formatCompact(tokens)} / ${formatMax(maxTokens)}`

  // Title text explains which number is showing so the user knows whether
  // subagents are included.  Pre-fix conversations get the "includes
  // subagents" caveat — once a new turn runs, main_* populates and the
  // caveat goes away on the next 5-second poll.
  const sourceNote = usingMain
    ? 'main agent only (subagent Task calls excluded)'
    : 'includes subagent usage (pre-fix conversation)'
  const titleText = `Current conversation context window — ${sourceNote}. Updates every 5s. Click for Token Budget dashboard.`

  return (
    <button
      onClick={() => { window.location.hash = '#/token-budget' }}
      className={`hidden md:inline-flex items-center gap-1 text-xs font-bold px-2 py-0.5 rounded-full cursor-pointer transition-colors hover:opacity-90 ${badgeBgColor(tokens, maxTokens)}`}
      title={titleText}
    >
      <Zap size={10} />
      {label}
    </button>
  )
}
