/**
 * TokenBudgetBadge - Small header pill showing 5-hour window token usage.
 *
 * Displays a color-coded badge with the current 5-hour window token count.
 * Clicking navigates to the full Token Budget dashboard page.
 *
 * Color thresholds (based on ~500K estimated 5-hour Sonnet Max window):
 *   Green:  <150K tokens
 *   Yellow: 150K - 300K
 *   Orange: 300K - 500K
 *   Red:    >500K
 *
 * Hidden on mobile (md:inline-flex). Returns null while data is loading.
 */

import { Zap } from 'lucide-react'
import { useTokenBudgetStatus } from '../hooks/useTokenBudget'

/** Format token count to compact display (e.g. 32K, 1.2M). */
function formatCompact(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`
  return String(n)
}

/** Determine background color class based on 5-hour window token count. */
function badgeBgColor(tokens: number): string {
  if (tokens > 500_000) return 'bg-red-500 text-white'
  if (tokens > 300_000) return 'bg-orange-500 text-white'
  if (tokens > 150_000) return 'bg-yellow-400 text-yellow-900'
  return 'bg-green-500 text-white'
}

export function TokenBudgetBadge() {
  const { data: status } = useTokenBudgetStatus()

  // Don't render until data has loaded
  if (!status) return null

  const tokens = status.five_hour.total_tokens
  const label = tokens > 0 ? `5hr: ${formatCompact(tokens)}` : 'OK'

  return (
    <button
      onClick={() => { window.location.hash = '#/token-budget' }}
      className={`hidden md:inline-flex items-center gap-1 text-xs font-bold px-2 py-0.5 rounded-full cursor-pointer transition-colors hover:opacity-90 ${badgeBgColor(tokens)}`}
      title="View Token Budget dashboard"
    >
      <Zap size={10} />
      {label}
    </button>
  )
}
