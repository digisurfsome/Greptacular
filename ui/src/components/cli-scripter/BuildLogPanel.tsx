/**
 * BuildLogPanel — Embedded build log viewer for CLI Scripter.
 *
 * Collapsible left panel that streams raw CLI build output (tail -f style).
 * Polls GET /api/cli-scripter/build-log for the latest lines.
 * Features:
 * - Auto-scroll to bottom (toggleable)
 * - Collapsible with smooth animation
 * - Last ~200 lines shown
 * - ANSI-stripped plain text rendering (no xterm dependency needed for read-only)
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import {
  Terminal,
  ChevronDown,
  ChevronRight,
  ArrowDownToLine,
} from 'lucide-react'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface BuildLogResponse {
  lines: string[]
  total: number
  status: string
}

interface BuildLogPanelProps {
  refreshInterval: number // ms
  collapsed?: boolean
  onToggle?: () => void
}

// ---------------------------------------------------------------------------
// API
// ---------------------------------------------------------------------------

const API_BASE = import.meta.env.DEV ? 'http://localhost:8888' : ''

async function fetchBuildLog(lastN: number = 200): Promise<BuildLogResponse> {
  const res = await fetch(`${API_BASE}/api/cli-scripter/build-log?last_n=${lastN}`)
  if (!res.ok) throw new Error('Failed to fetch build log')
  return res.json()
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function BuildLogPanel({
  refreshInterval,
  collapsed: controlledCollapsed,
  onToggle,
}: BuildLogPanelProps) {
  const [internalCollapsed, setInternalCollapsed] = useState(true)
  const collapsed = controlledCollapsed !== undefined ? controlledCollapsed : internalCollapsed
  const toggleCollapsed = onToggle || (() => setInternalCollapsed((p) => !p))

  const [lines, setLines] = useState<string[]>([])
  const [totalLines, setTotalLines] = useState(0)
  const [autoScroll, setAutoScroll] = useState(true)
  const [buildStatus, setBuildStatus] = useState<string>('idle')
  const logEndRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  // Poll for new log lines
  const pollLog = useCallback(async () => {
    try {
      const data = await fetchBuildLog(200)
      setLines(data.lines)
      setTotalLines(data.total)
      setBuildStatus(data.status)
    } catch {
      // Silently fail
    }
  }, [])

  useEffect(() => {
    if (collapsed) return
    // Initial fetch
    pollLog()
    if (refreshInterval <= 0) return
    const timer = setInterval(pollLog, refreshInterval)
    return () => clearInterval(timer)
  }, [refreshInterval, collapsed, pollLog])

  // Auto-scroll to bottom when new lines arrive
  useEffect(() => {
    if (autoScroll && !collapsed && logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [lines, autoScroll, collapsed])

  // Detect manual scroll to disable auto-scroll
  const handleScroll = useCallback(() => {
    if (!containerRef.current) return
    const el = containerRef.current
    const isAtBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 50
    setAutoScroll(isAtBottom)
  }, [])

  const isActive = buildStatus === 'running'

  return (
    <div className="bg-zinc-800/40 border border-zinc-700/60 rounded-xl overflow-hidden">
      {/* Header */}
      <button
        onClick={toggleCollapsed}
        className="w-full flex items-center gap-2 px-4 py-2.5 hover:bg-zinc-800/60 transition-colors"
      >
        {collapsed ? (
          <ChevronRight size={14} className="text-zinc-500" />
        ) : (
          <ChevronDown size={14} className="text-zinc-500" />
        )}
        <Terminal size={14} className={isActive ? 'text-cyan-400' : 'text-zinc-500'} />
        <span className="text-sm text-zinc-300 font-medium">Build Log</span>
        {totalLines > 0 && (
          <span className="text-xs text-zinc-600">{totalLines} lines</span>
        )}
        {isActive && (
          <span className="ml-auto text-[10px] text-cyan-400 bg-cyan-900/30 border border-cyan-700/40 rounded px-1.5 py-0.5">
            LIVE
          </span>
        )}
      </button>

      {/* Log content */}
      {!collapsed && (
        <div className="border-t border-zinc-800">
          <div
            ref={containerRef}
            onScroll={handleScroll}
            className="max-h-[400px] overflow-y-auto bg-zinc-950/80 px-3 py-2 font-mono text-xs text-zinc-400 leading-relaxed"
          >
            {lines.length === 0 ? (
              <div className="text-center py-8 text-zinc-600">
                {buildStatus === 'idle'
                  ? 'No build output yet. Start a build to see output here.'
                  : 'Waiting for output...'}
              </div>
            ) : (
              lines.map((line, i) => (
                <div
                  key={i}
                  className={`whitespace-pre-wrap break-all ${
                    line.includes('Error') || line.includes('FATAL') || line.includes('failed')
                      ? 'text-red-400'
                      : line.includes('complete') || line.includes('COMPLETE')
                        ? 'text-green-400'
                        : line.startsWith('>>>')
                          ? 'text-orange-400'
                          : line.startsWith('===')
                            ? 'text-cyan-400'
                            : ''
                  }`}
                >
                  {line}
                </div>
              ))
            )}
            <div ref={logEndRef} />
          </div>

          {/* Footer with auto-scroll toggle */}
          <div className="flex items-center justify-between px-3 py-1.5 border-t border-zinc-800/60">
            <span className="text-[10px] text-zinc-600">
              {totalLines > 200 && `Showing last 200 of ${totalLines} lines`}
            </span>
            <button
              onClick={() => {
                setAutoScroll(!autoScroll)
                if (!autoScroll && logEndRef.current) {
                  logEndRef.current.scrollIntoView({ behavior: 'smooth' })
                }
              }}
              className={`flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded transition-colors ${
                autoScroll
                  ? 'text-cyan-400 bg-cyan-900/20'
                  : 'text-zinc-600 hover:text-zinc-400'
              }`}
            >
              <ArrowDownToLine size={10} />
              Auto-scroll {autoScroll ? 'ON' : 'OFF'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
