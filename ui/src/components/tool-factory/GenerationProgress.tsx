/**
 * Full-screen overlay showing real-time pipeline generation progress.
 * Connects to the backend SSE /generate-stream endpoint for live updates.
 *
 * Shows each completed step with a checkmark, the active step with a spinner,
 * and auto-scrolls to keep the latest step visible.
 *
 * When an early_report SSE event arrives (before prompt conversion finishes),
 * a consulting report panel appears below the log feed showing complexity,
 * red flags, API costs, and an AI assessment.
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import {
  Loader2,
  CheckCircle2,
  AlertCircle,
  Clock,
  ShieldCheck,
  ChevronDown,
  ChevronRight,
  AlertTriangle,
  DollarSign,
  Zap,
  Users,
  Layers,
  Search,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { generateBlueprintStream, type GenerateBlueprintParams, type EarlyConsultingReport } from '@/lib/api'
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

// ---------------------------------------------------------------------------
// Complexity score badge — color-coded circle with the score number
// ---------------------------------------------------------------------------

function ComplexityBadge({ score }: { score: number }) {
  let bg: string
  let text: string
  if (score <= 3) {
    bg = 'bg-green-500'
    text = 'text-white'
  } else if (score <= 6) {
    bg = 'bg-yellow-500'
    text = 'text-yellow-950'
  } else {
    bg = 'bg-red-500'
    text = 'text-white'
  }

  return (
    <div className={`${bg} ${text} w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg shrink-0 border-2 border-border`}>
      {score}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Collapsible card for a single API in the early report
// ---------------------------------------------------------------------------

type EarlyAPIResult = NonNullable<EarlyConsultingReport['api_research']>['results'][number]

function EarlyAPICard({ result }: { result: EarlyAPIResult }) {
  const hasRedFlags = result.red_flags.length > 0
  const [expanded, setExpanded] = useState(hasRedFlags)

  return (
    <div className="border-2 border-border rounded-lg overflow-hidden">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-3 text-left hover:bg-muted/30 transition-colors"
      >
        <div className="flex items-center gap-2 flex-wrap">
          <Search size={14} className="text-muted-foreground shrink-0" />
          <span className="text-sm font-semibold text-foreground">{result.service_name}</span>
          <Badge variant="outline" className="text-xs">{result.category}</Badge>
          {hasRedFlags && (
            <Badge className="bg-orange-500/10 text-orange-600 border-orange-500/30 text-xs">
              <AlertTriangle size={10} className="mr-0.5" />
              {result.red_flags.length} warning{result.red_flags.length > 1 ? 's' : ''}
            </Badge>
          )}
        </div>
        {expanded
          ? <ChevronDown size={16} className="text-muted-foreground shrink-0" />
          : <ChevronRight size={16} className="text-muted-foreground shrink-0" />
        }
      </button>

      {expanded && (
        <div className="border-t border-border p-3 space-y-3">
          {/* Pricing */}
          <div className="space-y-1">
            <p className="text-sm text-foreground">
              <span className="font-medium">Pricing:</span>{' '}
              {result.pricing_summary}
            </p>
            <p className="text-sm text-foreground">
              <span className="font-medium">API Access:</span>{' '}
              <span className={
                result.api_access_cost.toLowerCase().includes('free')
                  ? 'text-green-600'
                  : 'text-orange-600 font-medium'
              }>
                {result.api_access_cost}
              </span>
            </p>
            <p className="text-sm text-muted-foreground">
              <span className="font-medium text-foreground">Per-use:</span>{' '}
              {result.per_unit_cost}
            </p>
          </div>

          {/* Pricing tiers */}
          {result.pricing_tiers.length > 0 && (
            <div className="space-y-1">
              <span className="text-xs font-medium text-muted-foreground">Pricing Tiers</span>
              <ul className="text-xs text-muted-foreground space-y-0.5 list-disc list-inside">
                {result.pricing_tiers.map((tier, i) => (
                  <li key={i}>{tier}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Red flags */}
          {hasRedFlags && (
            <div className="space-y-1.5">
              <span className="text-xs font-medium text-orange-600 flex items-center gap-1">
                <AlertTriangle size={12} />
                Red Flags
              </span>
              <ul className="space-y-1">
                {result.red_flags.map((flag, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-orange-700">
                    <span className="text-orange-500 mt-0.5 shrink-0">&#x2022;</span>
                    {flag}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Alternatives */}
          {result.alternatives.length > 0 && (
            <div className="space-y-1.5">
              <span className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                <DollarSign size={12} />
                Alternatives
              </span>
              <div className="border border-border rounded-lg overflow-hidden">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="bg-muted/50">
                      <th className="text-left p-2 font-medium text-muted-foreground">Service</th>
                      <th className="text-left p-2 font-medium text-muted-foreground">Price</th>
                      <th className="text-left p-2 font-medium text-muted-foreground hidden sm:table-cell">Tradeoff</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.alternatives.map((alt) => (
                      <tr key={alt.service_name} className="border-t border-border">
                        <td className="p-2 font-medium text-foreground">{alt.service_name}</td>
                        <td className="p-2 text-muted-foreground">{alt.pricing_summary}</td>
                        <td className="p-2 text-muted-foreground hidden sm:table-cell">{alt.tradeoff}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Research source */}
          {result.research_source === 'static_database' && (
            <p className="text-[10px] text-muted-foreground italic">
              Cached data -- may not reflect current pricing
            </p>
          )}
          {result.research_source === 'not_found' && (
            <p className="text-[10px] text-orange-600 italic">
              Pricing data could not be retrieved -- verify manually
            </p>
          )}
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Consulting report panel — rendered when earlyReport state is set
// ---------------------------------------------------------------------------

function ConsultingReportPanel({ report }: { report: EarlyConsultingReport }) {
  const { metrics, assessment, api_research } = report
  const [apiSectionExpanded, setApiSectionExpanded] = useState(true)

  const totalRedFlags = metrics.red_flags.length

  return (
    <div className="mt-4 rounded-xl border-2 border-border bg-card overflow-hidden animate-in fade-in slide-in-from-bottom-2 duration-300">
      {/* Header */}
      <div className="flex items-center gap-3 px-5 py-4 border-b border-border bg-muted/30">
        <ShieldCheck size={20} className="text-foreground shrink-0" />
        <h3 className="text-base font-semibold text-foreground">Consulting Report</h3>
      </div>

      <div className="p-5 space-y-5">
        {/* Row 1: Complexity badge + Verdict + Cost */}
        <div className="flex items-start gap-4">
          <ComplexityBadge score={metrics.complexity_score} />
          <div className="flex-1 min-w-0 space-y-1">
            <p className="text-sm font-semibold text-foreground">{metrics.verdict}</p>
            <p className="text-xs text-muted-foreground">
              Complexity {metrics.complexity_score}/10
              {metrics.estimated_monthly_cost && (
                <> &mdash; Est. {metrics.estimated_monthly_cost}</>
              )}
            </p>
          </div>
        </div>

        {/* Quick stats grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <StatCard
            icon={<Layers size={14} />}
            label="Total Steps"
            value={String(metrics.total_steps)}
          />
          <StatCard
            icon={<Users size={14} />}
            label="Manual"
            value={String(metrics.manual_steps)}
          />
          <StatCard
            icon={<Zap size={14} />}
            label="Automated"
            value={String(metrics.automated_steps)}
          />
          <StatCard
            icon={<Search size={14} />}
            label="APIs"
            value={String(metrics.api_count)}
          />
        </div>

        {/* User variables */}
        {metrics.user_variables.length > 0 && (
          <div className="space-y-1.5">
            <span className="text-xs font-medium text-muted-foreground">Required Variables</span>
            <div className="flex flex-wrap gap-1.5">
              {metrics.user_variables.map((v) => (
                <Badge key={v} variant="outline" className="text-xs font-mono">
                  {v}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Red flags */}
        {totalRedFlags > 0 && (
          <div className="rounded-lg border-2 border-orange-500/30 bg-orange-500/5 p-3 space-y-2">
            <span className="text-xs font-semibold text-orange-600 flex items-center gap-1.5">
              <AlertTriangle size={14} />
              Red Flags ({totalRedFlags})
            </span>
            <ul className="space-y-1">
              {metrics.red_flags.map((flag, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-orange-700">
                  <span className="text-orange-500 mt-0.5 shrink-0">&#x2022;</span>
                  {flag}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* AI Assessment */}
        {assessment && (
          <div className="space-y-1.5">
            <span className="text-xs font-medium text-muted-foreground">AI Assessment</span>
            <div className="text-sm text-foreground/80 leading-relaxed whitespace-pre-wrap">
              {assessment}
            </div>
          </div>
        )}

        {/* API Research details (collapsible) */}
        {api_research && api_research.results.length > 0 && (
          <div className="space-y-3">
            <button
              type="button"
              onClick={() => setApiSectionExpanded(!apiSectionExpanded)}
              className="w-full flex items-center justify-between"
            >
              <div className="flex items-center gap-2">
                <DollarSign size={16} className="text-foreground" />
                <span className="text-sm font-semibold text-foreground">API Cost Details</span>
                <Badge variant="outline" className="text-xs">
                  {api_research.results.length} API{api_research.results.length !== 1 ? 's' : ''}
                </Badge>
              </div>
              <div className="flex items-center gap-2">
                {api_research.total_estimated_monthly_cost && (
                  <span className="text-xs text-muted-foreground">
                    {api_research.total_estimated_monthly_cost}
                  </span>
                )}
                {apiSectionExpanded
                  ? <ChevronDown size={14} className="text-muted-foreground" />
                  : <ChevronRight size={14} className="text-muted-foreground" />
                }
              </div>
            </button>

            {apiSectionExpanded && (
              <div className="space-y-2">
                {api_research.research_duration_seconds > 0 && (
                  <p className="text-[10px] text-muted-foreground">
                    Research completed in {api_research.research_duration_seconds.toFixed(1)}s
                  </p>
                )}
                {api_research.results.map((result) => (
                  <EarlyAPICard key={result.service_key} result={result} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Small stat card used in the quick-stats grid
// ---------------------------------------------------------------------------

function StatCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-muted/30 p-2.5 text-center space-y-0.5">
      <div className="flex items-center justify-center text-muted-foreground">{icon}</div>
      <p className="text-lg font-bold text-foreground tabular-nums">{value}</p>
      <p className="text-[10px] text-muted-foreground">{label}</p>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function GenerationProgress({ params, onComplete, onCancel }: GenerationProgressProps) {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [error, setError] = useState<string | null>(null)
  const [elapsed, setElapsed] = useState(0)
  const [done, setDone] = useState(false)
  const [earlyReport, setEarlyReport] = useState<EarlyConsultingReport | null>(null)
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
      (report) => {
        if (!cancelled) setEarlyReport(report)
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

  // Widen the modal when the consulting report is visible
  const modalWidth = earlyReport ? 'max-w-3xl' : 'max-w-lg'

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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/95 backdrop-blur-sm overflow-y-auto py-8">
      <div className={`w-full ${modalWidth} mx-4 transition-all duration-300`}>
        <div className="rounded-xl border-2 border-border bg-card p-8 shadow-lg">
          <h2 className="text-xl font-semibold text-foreground mb-2 text-center">
            Generating Blueprint
          </h2>

          {/* Elapsed timer */}
          <div className="flex items-center justify-center gap-1.5 text-sm text-muted-foreground mb-6">
            <Clock size={14} />
            <span>{formatElapsed(elapsed)} elapsed</span>
          </div>

          {/* Live log feed -- auto-scrolls to keep latest visible */}
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

          {/* Active step indicator -- always visible below the scroll area */}
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

          {/* Early consulting report — appears once the backend sends it */}
          {earlyReport && <ConsultingReportPanel report={earlyReport} />}

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
