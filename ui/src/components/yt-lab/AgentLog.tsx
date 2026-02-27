/**
 * AgentLog — Left sidebar bottom half in the execution viewer.
 *
 * Real-time scrolling log of agent actions, thinking, errors, and chat
 * messages. Auto-scrolls to bottom unless user scrolls up to review.
 */

import { useEffect, useRef, useState } from 'react'
import { Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import type { YTExecutionLogEntry } from '@/lib/types'

interface AgentLogProps {
  logs: YTExecutionLogEntry[]
  onClear?: () => void
  collapsed?: boolean
}

const LOG_TYPE_STYLES: Record<YTExecutionLogEntry['type'], string> = {
  action: 'text-blue-400',
  thinking: 'text-muted-foreground italic',
  error: 'text-red-400',
  success: 'text-green-400',
  user: 'text-amber-400 font-medium',
  agent: 'text-cyan-400',
}

function formatTimestamp(iso: string): string {
  try {
    const d = new Date(iso)
    return d.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    })
  } catch {
    return ''
  }
}

export function AgentLog({ logs, onClear, collapsed = false }: AgentLogProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [autoScroll, setAutoScroll] = useState(true)

  // Auto-scroll to bottom when new logs arrive (if autoScroll enabled)
  useEffect(() => {
    if (autoScroll && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [logs, autoScroll])

  // Detect user scroll to disable auto-scroll
  const handleScroll = () => {
    if (!containerRef.current) return
    const { scrollTop, scrollHeight, clientHeight } = containerRef.current
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 40
    setAutoScroll(isAtBottom)
  }

  if (collapsed) {
    const hasRecentActivity = logs.length > 0 && (Date.now() - new Date(logs[logs.length - 1].timestamp).getTime()) < 10000
    return (
      <div className="flex flex-col items-center py-2 gap-1">
        <div className={`w-2 h-2 rounded-full ${hasRecentActivity ? 'bg-cyan-400 animate-pulse' : 'bg-muted-foreground/30'}`} title={hasRecentActivity ? 'Agent active' : 'No recent activity'} />
        <span className="text-[9px] text-muted-foreground [writing-mode:vertical-rl]">
          Logs ({logs.length})
        </span>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-1.5 border-t border-border shrink-0">
        <span className="text-xs font-medium text-muted-foreground">Agent Log</span>
        <div className="flex items-center gap-1">
          {!autoScroll && (
            <button
              onClick={() => {
                setAutoScroll(true)
                if (containerRef.current) {
                  containerRef.current.scrollTop = containerRef.current.scrollHeight
                }
              }}
              className="text-[10px] text-primary hover:underline"
            >
              Jump to latest
            </button>
          )}
          {onClear && logs.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              className="h-5 w-5 p-0 text-muted-foreground hover:text-foreground"
              onClick={onClear}
              aria-label="Clear logs"
            >
              <Trash2 size={10} />
            </Button>
          )}
        </div>
      </div>

      {/* Log entries */}
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-auto px-3 pb-2 font-mono text-[11px] leading-relaxed"
      >
        {logs.length === 0 ? (
          <p className="text-muted-foreground text-center py-4">
            Waiting for agent activity...
          </p>
        ) : (
          logs.map((entry) => (
            <div key={entry.id} className="flex gap-1.5 py-0.5">
              <span className="text-muted-foreground/60 shrink-0 select-none">
                {formatTimestamp(entry.timestamp)}
              </span>
              <span className={LOG_TYPE_STYLES[entry.type]}>{entry.text}</span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
