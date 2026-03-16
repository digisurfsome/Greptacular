/**
 * GapAnalysisView — shows full gap analysis results with build plans.
 *
 * Displays priority-ordered missing components, difficulty badges,
 * impact summary, and "Generate PRD" buttons per component.
 */

import { useState, useCallback } from 'react'
import {
  FileText,
  Wrench,
  ChevronDown,
  ChevronRight,
  Loader2,
  Copy,
  CheckCircle2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import type { GapAnalysisResult } from './ToolReadinessCheck'

// ---------------------------------------------------------------------------
// Difficulty badge — color-coded
// ---------------------------------------------------------------------------

function DifficultyBadge({ level }: { level: number }) {
  let className: string
  if (level <= 3) {
    className = 'bg-green-500/10 text-green-700 border-green-500/30'
  } else if (level <= 6) {
    className = 'bg-yellow-500/10 text-yellow-700 border-yellow-500/30'
  } else {
    className = 'bg-red-500/10 text-red-700 border-red-500/30'
  }

  return (
    <Badge className={`${className} text-xs`}>
      {level}/10
    </Badge>
  )
}

// ---------------------------------------------------------------------------
// PRD Modal (inline textarea)
// ---------------------------------------------------------------------------

function PRDDisplay({ prd, onClose }: { prd: string; onClose: () => void }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = useCallback(async () => {
    await navigator.clipboard.writeText(prd)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }, [prd])

  return (
    <div className="mt-2 rounded-lg border border-border bg-muted/30 p-3 space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-muted-foreground">Generated PRD</span>
        <div className="flex gap-1.5">
          <Button size="sm" variant="ghost" className="h-6 px-2 text-xs gap-1" onClick={handleCopy}>
            {copied ? <CheckCircle2 size={12} /> : <Copy size={12} />}
            {copied ? 'Copied' : 'Copy'}
          </Button>
          <Button size="sm" variant="ghost" className="h-6 px-2 text-xs" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
      <pre className="text-xs text-foreground/80 whitespace-pre-wrap max-h-64 overflow-y-auto font-mono leading-relaxed">
        {prd}
      </pre>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

interface GapAnalysisViewProps {
  result: GapAnalysisResult
}

export function GapAnalysisView({ result }: GapAnalysisViewProps) {
  const [expandedPlans, setExpandedPlans] = useState<Set<string>>(new Set())
  const [prdLoading, setPrdLoading] = useState<string | null>(null)
  const [prdContent, setPrdContent] = useState<Record<string, string>>({})

  const togglePlan = useCallback((name: string) => {
    setExpandedPlans((prev) => {
      const next = new Set(prev)
      if (next.has(name)) next.delete(name)
      else next.add(name)
      return next
    })
  }, [])

  const handleGeneratePRD = useCallback(async (componentName: string) => {
    try {
      setPrdLoading(componentName)
      const res = await fetch(`/api/tool-analyzer/generate-prd/${componentName}`, {
        method: 'POST',
      })
      if (!res.ok) throw new Error('PRD generation failed')
      const data = await res.json()
      setPrdContent((prev) => ({ ...prev, [componentName]: data.prd }))
    } catch {
      // Silently fail — button stays available for retry
    } finally {
      setPrdLoading(null)
    }
  }, [])

  if (result.build_plans.length === 0) {
    return (
      <div className="rounded-lg border border-green-500/30 bg-green-500/5 p-3">
        <div className="flex items-center gap-2 text-sm text-green-700">
          <CheckCircle2 size={16} />
          No gaps found. All components are available.
        </div>
      </div>
    )
  }

  // Map build plans by name for quick lookup
  const planMap = Object.fromEntries(result.build_plans.map((p) => [p.component_name, p]))

  return (
    <div className="space-y-3">
      {/* Impact summary */}
      <div className="rounded-lg border border-border bg-muted/20 p-3">
        <p className="text-xs font-medium text-muted-foreground mb-1">Impact Summary</p>
        <pre className="text-xs text-foreground/80 whitespace-pre-wrap font-mono leading-relaxed">
          {result.impact_summary}
        </pre>
      </div>

      {/* Priority-ordered component list */}
      <div className="space-y-2">
        <p className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
          <Wrench size={12} />
          Missing Components ({result.priority_order.length})
        </p>

        {result.priority_order.map((name) => {
          const plan = planMap[name]
          if (!plan) return null
          const isExpanded = expandedPlans.has(name)

          return (
            <div key={name} className="rounded-lg border border-border overflow-hidden">
              <button
                type="button"
                onClick={() => togglePlan(name)}
                className="w-full flex items-center justify-between p-3 text-left hover:bg-muted/30 transition-colors"
              >
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-medium text-foreground">{name}</span>
                  <DifficultyBadge level={plan.difficulty} />
                </div>
                {isExpanded
                  ? <ChevronDown size={14} className="text-muted-foreground shrink-0" />
                  : <ChevronRight size={14} className="text-muted-foreground shrink-0" />
                }
              </button>

              {isExpanded && (
                <div className="border-t border-border p-3 space-y-2">
                  <p className="text-xs text-foreground/80">{plan.description}</p>

                  {plan.files_to_create.length > 0 && (
                    <div>
                      <span className="text-[10px] font-medium text-muted-foreground">Files to create:</span>
                      <div className="flex flex-wrap gap-1 mt-0.5">
                        {plan.files_to_create.map((f) => (
                          <Badge key={f} variant="outline" className="text-[10px] font-mono">
                            {f}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  <p className="text-[10px] text-muted-foreground">
                    <span className="font-medium">Integration:</span> {plan.integration_point}
                  </p>

                  {/* Generate PRD button */}
                  {!prdContent[name] ? (
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-7 text-xs gap-1.5"
                      onClick={() => handleGeneratePRD(name)}
                      disabled={prdLoading === name}
                    >
                      {prdLoading === name ? (
                        <Loader2 size={12} className="animate-spin" />
                      ) : (
                        <FileText size={12} />
                      )}
                      Generate PRD
                    </Button>
                  ) : (
                    <PRDDisplay
                      prd={prdContent[name]}
                      onClose={() => setPrdContent((prev) => {
                        const next = { ...prev }
                        delete next[name]
                        return next
                      })}
                    />
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
