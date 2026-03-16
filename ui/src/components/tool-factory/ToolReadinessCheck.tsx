/**
 * ToolReadinessCheck — runs a quick readiness check on tool steps before generation.
 *
 * On mount, auto-calls POST /api/tool-analyzer/quick-check. Shows:
 *   - Green panel + "Generate Tool" if 100% ready
 *   - Yellow/red panel with step breakdown + "Run Full Analysis" + "Generate Anyway" otherwise
 */

import { useState, useEffect, useCallback } from 'react'
import {
  CheckCircle2,
  AlertTriangle,
  Loader2,
  Shield,
  ChevronDown,
  ChevronRight,
  Zap,
  Search,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { GapAnalysisView } from './GapAnalysisView'

// ---------------------------------------------------------------------------
// Types matching backend response
// ---------------------------------------------------------------------------

interface StepDetail {
  step: number
  title: string
  components: string[]
  status: string
  missing: string[]
}

interface QuickCheckResult {
  tool_name: string
  total_steps: number
  executable_steps: number
  blocked_steps: number
  pass: boolean
  coverage_pct: number
  details: StepDetail[]
  missing_components: string[]
  recommendation: string
}

interface BuildPlan {
  component_name: string
  difficulty: number
  description: string
  files_to_create: string[]
  integration_point: string
}

export interface GapAnalysisResult extends QuickCheckResult {
  build_plans: BuildPlan[]
  priority_order: string[]
  impact_summary: string
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface ToolReadinessCheckProps {
  steps: Array<{
    order: number
    title: string
    description?: string
    prompt: string
    expectedOutput?: string
    notes?: string
    model?: string
  }>
  toolName: string
  onProceed: () => void
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ToolReadinessCheck({ steps, toolName, onProceed }: ToolReadinessCheckProps) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<QuickCheckResult | null>(null)
  const [gapResult, setGapResult] = useState<GapAnalysisResult | null>(null)
  const [gapLoading, setGapLoading] = useState(false)
  const [detailsExpanded, setDetailsExpanded] = useState(false)

  // Auto-run quick check on mount
  useEffect(() => {
    let cancelled = false

    async function runCheck() {
      try {
        setLoading(true)
        setError(null)
        const res = await fetch('/api/tool-analyzer/quick-check', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ steps, tool_name: toolName }),
        })
        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: 'Check failed' }))
          throw new Error(err.detail || `HTTP ${res.status}`)
        }
        const data: QuickCheckResult = await res.json()
        if (!cancelled) setResult(data)
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Check failed')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    runCheck()
    return () => { cancelled = true }
  }, [steps, toolName])

  const handleGapAnalysis = useCallback(async () => {
    try {
      setGapLoading(true)
      const res = await fetch('/api/tool-analyzer/gap-analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ steps, tool_name: toolName }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Analysis failed' }))
        throw new Error(err.detail || `HTTP ${res.status}`)
      }
      const data: GapAnalysisResult = await res.json()
      setGapResult(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Gap analysis failed')
    } finally {
      setGapLoading(false)
    }
  }, [steps, toolName])

  // Loading state
  if (loading) {
    return (
      <div className="rounded-lg border-2 border-border bg-card p-4">
        <div className="flex items-center gap-2 text-muted-foreground">
          <Loader2 size={16} className="animate-spin" />
          <span className="text-sm">Checking tool readiness...</span>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="rounded-lg border-2 border-destructive/30 bg-destructive/5 p-4">
        <div className="flex items-center gap-2 text-destructive">
          <AlertTriangle size={16} />
          <span className="text-sm">{error}</span>
        </div>
        <Button size="sm" variant="outline" className="mt-2" onClick={onProceed}>
          Generate Anyway
        </Button>
      </div>
    )
  }

  if (!result) return null

  // Full pass — green
  if (result.pass) {
    return (
      <div className="rounded-lg border-2 border-green-500/40 bg-green-500/5 p-4 space-y-3">
        <div className="flex items-center gap-2">
          <CheckCircle2 size={18} className="text-green-600 shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-foreground">
              Ready to generate — {result.coverage_pct}% coverage
            </p>
            <p className="text-xs text-muted-foreground">{result.recommendation}</p>
          </div>
          <Badge className="bg-green-500/10 text-green-700 border-green-500/30 shrink-0">
            {result.executable_steps}/{result.total_steps} steps
          </Badge>
        </div>
        <Button size="sm" className="w-full gap-1.5" onClick={onProceed}>
          <Zap size={14} />
          Generate Tool
        </Button>
      </div>
    )
  }

  // Partial or blocked — yellow/red
  const isLow = result.coverage_pct < 50
  const borderColor = isLow ? 'border-red-500/40' : 'border-yellow-500/40'
  const bgColor = isLow ? 'bg-red-500/5' : 'bg-yellow-500/5'
  const iconColor = isLow ? 'text-red-600' : 'text-yellow-600'

  return (
    <div className={`rounded-lg border-2 ${borderColor} ${bgColor} p-4 space-y-3`}>
      {/* Header */}
      <div className="flex items-center gap-2">
        <Shield size={18} className={`${iconColor} shrink-0`} />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-foreground">
            {result.coverage_pct}% ready — {result.blocked_steps} step{result.blocked_steps !== 1 ? 's' : ''} blocked
          </p>
          <p className="text-xs text-muted-foreground">{result.recommendation}</p>
        </div>
        <Badge className={`${isLow ? 'bg-red-500/10 text-red-700 border-red-500/30' : 'bg-yellow-500/10 text-yellow-700 border-yellow-500/30'} shrink-0`}>
          {result.executable_steps}/{result.total_steps}
        </Badge>
      </div>

      {/* Missing components */}
      {result.missing_components.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {result.missing_components.map((name) => (
            <Badge key={name} variant="outline" className="text-xs font-mono">
              {name}
            </Badge>
          ))}
        </div>
      )}

      {/* Expandable step details */}
      <button
        type="button"
        onClick={() => setDetailsExpanded(!detailsExpanded)}
        className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
      >
        {detailsExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
        Step breakdown
      </button>

      {detailsExpanded && (
        <div className="space-y-1 max-h-48 overflow-y-auto">
          {result.details.map((d) => (
            <div key={d.step} className="flex items-center gap-2 text-xs py-1">
              {d.status === 'ready' ? (
                <CheckCircle2 size={12} className="text-green-600 shrink-0" />
              ) : (
                <AlertTriangle size={12} className="text-red-500 shrink-0" />
              )}
              <span className="text-muted-foreground shrink-0">#{d.step}</span>
              <span className="text-foreground truncate flex-1">{d.title}</span>
              {d.missing.length > 0 && (
                <span className="text-red-500 text-[10px] shrink-0">
                  needs: {d.missing.join(', ')}
                </span>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Gap analysis results */}
      {gapResult && <GapAnalysisView result={gapResult} />}

      {/* Action buttons */}
      <div className="flex gap-2">
        {!gapResult && (
          <Button
            size="sm"
            variant="outline"
            className="gap-1.5"
            onClick={handleGapAnalysis}
            disabled={gapLoading}
          >
            {gapLoading ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <Search size={14} />
            )}
            Run Full Analysis
          </Button>
        )}
        <Button size="sm" className="gap-1.5" onClick={onProceed}>
          <Zap size={14} />
          Generate Anyway
        </Button>
      </div>
    </div>
  )
}
