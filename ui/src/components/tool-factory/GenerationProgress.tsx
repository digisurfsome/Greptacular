/**
 * Full-screen overlay showing real-time pipeline generation progress.
 * Connects to the backend SSE /generate-stream endpoint for live updates.
 *
 * Shows each completed step with a checkmark, the active step with a spinner,
 * and auto-scrolls to keep the latest step visible.
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import { Loader2, CheckCircle2, AlertCircle, Clock } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { generateBlueprintStream, type GenerateBlueprintParams } from '@/lib/api'
import type { TFSheetBlueprint } from '@/lib/types'

interface GenerationProgressProps {
  /** Parameters matching the backend GenerateBlueprintRequest schema */
  params: GenerateBlueprintParams
  onComplete: (blueprint: TFSheetBlueprint, toolId: string) => void
  onCancel: () => void
}

interface LogEntry {
  message: string
  /** Seconds since pipeline start (cumulative) */
  pipelineElapsed: number
  /** Seconds this individual step took */
  stepDuration: number
}

export function GenerationProgress({ params, onComplete, onCancel }: GenerationProgressProps) {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [error, setError] = useState<string | null>(null)
  const [elapsed, setElapsed] = useState(0)
  const [done, setDone] = useState(false)
  const startTimeRef = useRef(Date.now())
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  // Auto-scroll log container to bottom when new entries arrive
  const scrollToBottom = useCallback(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [])

  // Live elapsed timer
  useEffect(() => {
    startTimeRef.current = Date.now()
    timerRef.current = setInterval(() => {
      setElapsed(Math.round((Date.now() - startTimeRef.current) / 1000))
    }, 500)
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [])

  // SSE stream connection
  useEffect(() => {
    let cancelled = false

    generateBlueprintStream(
      params,
      (message, sseElapsed) => {
        if (cancelled) return
        setLogs((prev) => {
          // Calculate step duration: time between this event and the previous one
          const prevCumulative = prev.length > 0
            ? prev[prev.length - 1].pipelineElapsed
            : 0
          const stepDuration = Math.max(0, Math.round((sseElapsed - prevCumulative) * 10) / 10)
          return [
            ...prev,
            { message, pipelineElapsed: sseElapsed, stepDuration },
          ]
        })
      },
    )
      .then((result) => {
        if (cancelled) return
        setDone(true)
        if (timerRef.current) clearInterval(timerRef.current)
        setTimeout(() => {
          if (!cancelled) onComplete(result.blueprint, result.tool_id)
        }, 600)
      })
      .catch((err) => {
        if (cancelled) return
        if (timerRef.current) clearInterval(timerRef.current)
        setError(err instanceof Error ? err.message : 'Generation failed')
      })

    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params])

  // Auto-scroll whenever logs change
  useEffect(() => {
    scrollToBottom()
  }, [logs, scrollToBottom])

  // Determine the latest log message for the active step indicator
  const latestLog = logs.length > 0 ? logs[logs.length - 1].message : 'Starting pipeline...'

  // Format elapsed as M:SS (e.g. "3:35" not "215s")
  const formatElapsed = (totalSeconds: number) => {
    const mins = Math.floor(totalSeconds / 60)
    const secs = totalSeconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  // Format step duration for display (short form for individual steps)
  const formatDuration = (seconds: number) => {
    if (seconds < 0.1) return '<0.1s'
    if (seconds < 10) return `${seconds.toFixed(1)}s`
    if (seconds < 60) return `${Math.round(seconds)}s`
    const m = Math.floor(seconds / 60)
    const s = Math.round(seconds % 60)
    return `${m}:${s.toString().padStart(2, '0')}`
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/95 backdrop-blur-sm">
      <div className="w-full max-w-lg mx-4">
        <div className="rounded-xl border-2 border-border bg-card p-8 shadow-lg">
          <h2 className="text-xl font-semibold text-foreground mb-2 text-center">
            Generating Blueprint
          </h2>

          {/* Elapsed timer */}
          <div className="flex items-center justify-center gap-1.5 text-sm text-muted-foreground mb-6">
            <Clock size={14} />
            <span>{formatElapsed(elapsed)} elapsed</span>
          </div>

          {/* Live log feed — auto-scrolls to keep latest visible */}
          <div ref={scrollRef} className="space-y-2 max-h-72 overflow-y-auto pr-1 scroll-smooth">
            {logs.map((entry, i) => {
              const isLatest = i === logs.length - 1
              const isDone = !isLatest || done
              return (
                <div key={i} className="flex items-start gap-2.5">
                  {isDone ? (
                    <CheckCircle2 size={16} className="text-[var(--color-neo-done)] shrink-0 mt-0.5" />
                  ) : (
                    <Loader2 size={16} className="animate-spin text-[var(--color-neo-progress)] shrink-0 mt-0.5" />
                  )}
                  <div className="flex-1 min-w-0">
                    <span className={`text-sm ${isDone ? 'text-muted-foreground' : 'text-foreground font-medium'}`}>
                      {entry.message}
                    </span>
                  </div>
                  <span className="text-xs text-muted-foreground/60 shrink-0 tabular-nums">
                    {formatDuration(entry.stepDuration)}
                  </span>
                </div>
              )
            })}

            {/* Show spinner if no logs yet */}
            {logs.length === 0 && !error && (
              <div className="flex items-center gap-2.5">
                <Loader2 size={16} className="animate-spin text-[var(--color-neo-progress)] shrink-0" />
                <span className="text-sm text-foreground font-medium">Connecting to pipeline...</span>
              </div>
            )}
          </div>

          {/* Active step indicator — always visible below the scroll area */}
          {!done && !error && logs.length > 0 && (
            <div className="mt-4 pt-3 border-t border-border">
              <div className="flex items-center gap-2">
                <Loader2 size={14} className="animate-spin text-[var(--color-neo-progress)] shrink-0" />
                <span className="text-sm text-muted-foreground">{latestLog}</span>
              </div>
            </div>
          )}

          {/* Done indicator */}
          {done && (
            <div className="mt-4 pt-3 border-t border-border">
              <div className="flex items-center justify-center gap-2 text-[var(--color-neo-done)]">
                <CheckCircle2 size={18} />
                <span className="text-sm font-medium">Blueprint complete — {formatElapsed(elapsed)} total</span>
              </div>
            </div>
          )}

          {/* Error display */}
          {error && (
            <div className="mt-4 flex gap-2 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2">
              <AlertCircle size={16} className="text-destructive shrink-0 mt-0.5" />
              <p className="text-sm text-destructive">{error}</p>
            </div>
          )}

          <div className="mt-6 flex justify-center">
            <Button variant="ghost" size="sm" onClick={onCancel}>
              Cancel
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
