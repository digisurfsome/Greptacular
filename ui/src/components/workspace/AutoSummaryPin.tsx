/**
 * AutoSummaryPin
 *
 * Displays the latest conversation summary in a collapsible card
 * above the message list. Shows update timestamp, message coverage,
 * and a manual regenerate button.
 */

import { useState } from 'react'
import { ChevronDown, ChevronRight, RefreshCw, FileText } from 'lucide-react'

interface AutoSummaryPinProps {
  /** The summary text */
  summary: string | null
  /** ISO timestamp of when the summary was last updated */
  updatedAt: string | null
  /** Number of messages the summary covers */
  messagesCovered: number | null
  /** Callback to trigger manual summary regeneration */
  onRegenerate: () => void
  /** Whether a regeneration is currently in progress */
  isRegenerating?: boolean
}

/** Format a date as a relative "time ago" string. */
function formatTimeAgo(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000)
  if (seconds < 60) return 'just now'
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

/** Collapsible summary card pinned above the message list. */
export function AutoSummaryPin({
  summary,
  updatedAt,
  messagesCovered,
  onRegenerate,
  isRegenerating = false,
}: AutoSummaryPinProps): React.JSX.Element | null {
  const [expanded, setExpanded] = useState(false)

  if (!summary) return null

  const timeAgo = updatedAt ? formatTimeAgo(new Date(updatedAt)) : 'unknown'

  return (
    <div className="mx-4 mt-2 mb-1 border border-border rounded-md bg-muted/50">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center justify-between w-full px-3 py-2 text-left text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <div className="flex items-center gap-2">
          {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          <FileText size={14} />
          <span>
            Summary
            {messagesCovered != null && ` (${messagesCovered} messages)`}
            {' \u00b7 '}
            updated {timeAgo}
          </span>
        </div>

        <button
          onClick={(e) => { e.stopPropagation(); onRegenerate() }}
          disabled={isRegenerating}
          className="p-1 rounded hover:bg-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Regenerate summary"
        >
          <RefreshCw size={14} className={isRegenerating ? 'animate-spin' : ''} />
        </button>
      </button>

      {expanded && (
        <div className="px-3 pb-3 text-sm text-foreground whitespace-pre-wrap border-t border-border pt-2">
          {summary}
        </div>
      )}
    </div>
  )
}
