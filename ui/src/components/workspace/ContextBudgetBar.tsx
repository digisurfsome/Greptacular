/**
 * Context Budget Bar
 *
 * Visual token budget meter displayed as a sticky bar below the chat header.
 * Shows the current context window usage as a progress bar with color-coded
 * thresholds. Expands on click to show a detailed breakdown of token
 * allocation between conversation history and remaining capacity.
 */

import { useState, useCallback, useMemo } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'

interface ContextBudgetBarProps {
  totalTokens: number
  contextWindow: number
}

/**
 * Returns the Tailwind classes for the progress bar fill and label text
 * based on the current usage percentage.
 *
 * Thresholds:
 * - >=95%: destructive (red) with pulse animation
 * - >=90%: orange warning
 * - >=75%: yellow caution
 * - <75%:  primary (default brand color)
 */
function getThemeClasses(percentage: number): { bar: string; text: string } {
  if (percentage >= 95) {
    return {
      bar: 'bg-destructive animate-pulse',
      text: 'text-destructive',
    }
  }
  if (percentage >= 90) {
    return {
      bar: 'bg-orange-500',
      text: 'text-orange-600 dark:text-orange-400',
    }
  }
  if (percentage >= 75) {
    return {
      bar: 'bg-yellow-500',
      text: 'text-yellow-600 dark:text-yellow-400',
    }
  }
  return {
    bar: 'bg-primary',
    text: 'text-primary',
  }
}

/** Sticky context-window usage bar with expandable breakdown. */
export function ContextBudgetBar({
  totalTokens,
  contextWindow,
}: ContextBudgetBarProps): React.JSX.Element {
  const [expanded, setExpanded] = useState(false)

  const handleToggle = useCallback(() => {
    setExpanded((prev) => !prev)
  }, [])

  const percentage = useMemo(
    () => Math.min(100, Math.round((totalTokens / contextWindow) * 100)),
    [totalTokens, contextWindow],
  )

  const remaining = useMemo(
    () => Math.max(0, contextWindow - totalTokens),
    [contextWindow, totalTokens],
  )

  const theme = useMemo(() => getThemeClasses(percentage), [percentage])

  return (
    <div className="sticky top-0 z-10 border-b border-border bg-card/95 backdrop-blur-sm">
      {/* Clickable summary row */}
      <button
        type="button"
        onClick={handleToggle}
        className="flex w-full items-center gap-3 px-4 py-2 text-left"
        aria-expanded={expanded}
        aria-label={`Context usage: ${percentage}% of ${contextWindow.toLocaleString()} tokens`}
      >
        {/* Progress track */}
        <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-300 ${theme.bar}`}
            style={{ width: `${percentage}%` }}
          />
        </div>

        {/* Percentage label */}
        <span className={`text-xs font-medium tabular-nums ${theme.text}`}>
          {percentage}%
        </span>

        {/* Expand/collapse chevron */}
        {expanded ? (
          <ChevronUp size={14} className="text-muted-foreground" />
        ) : (
          <ChevronDown size={14} className="text-muted-foreground" />
        )}
      </button>

      {/* Expanded breakdown */}
      {expanded && (
        <div className="px-4 pb-3 space-y-1 text-xs text-muted-foreground">
          <div className="flex justify-between">
            <span>Conversation history</span>
            <span className="font-mono tabular-nums text-foreground">
              {totalTokens.toLocaleString()} tokens
            </span>
          </div>
          <div className="flex justify-between">
            <span>Remaining capacity</span>
            <span className="font-mono tabular-nums text-foreground">
              {remaining.toLocaleString()} tokens
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
