/**
 * Full-screen overlay showing pipeline generation progress.
 * Displays step-by-step completion with checkmarks as each stage finishes.
 */

import { useState, useEffect } from 'react'
import { Loader2, CheckCircle2, Circle, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useGenerateBlueprint } from '@/hooks/useToolFactory'
import type { GenerateBlueprintParams } from '@/lib/api'
import type { TFSheetBlueprint } from '@/lib/types'

interface GenerationProgressProps {
  /** Parameters matching the backend GenerateBlueprintRequest schema */
  params: GenerateBlueprintParams
  onComplete: (blueprint: TFSheetBlueprint, toolId: string) => void
  onCancel: () => void
}

interface PipelineStep {
  label: string
  status: 'pending' | 'active' | 'done' | 'error'
}

const PIPELINE_LABELS = [
  'Classifying steps...',
  'Detecting APIs...',
  'Converting prompts...',
  'Assembling blueprint...',
  'Applying theme...',
]

export function GenerationProgress({ params, onComplete, onCancel }: GenerationProgressProps) {
  const [steps, setSteps] = useState<PipelineStep[]>(
    PIPELINE_LABELS.map((label) => ({ label, status: 'pending' }))
  )
  const [error, setError] = useState<string | null>(null)
  const generateBlueprint = useGenerateBlueprint()

  // Simulate step progression while the actual API call runs
  useEffect(() => {
    let cancelled = false
    let stepIndex = 0

    const advanceStep = () => {
      if (cancelled || stepIndex >= steps.length) return
      setSteps((prev) =>
        prev.map((s, i) => {
          if (i < stepIndex) return { ...s, status: 'done' }
          if (i === stepIndex) return { ...s, status: 'active' }
          return s
        })
      )
      stepIndex++
    }

    // Start the first step immediately
    advanceStep()

    // Advance every 1.5s for visual feedback
    const interval = setInterval(advanceStep, 1500)

    // Kick off actual generation
    generateBlueprint
      .mutateAsync(params)
      .then((result) => {
        if (cancelled) return
        // Mark all steps done
        setSteps((prev) => prev.map((s) => ({ ...s, status: 'done' })))
        setTimeout(() => {
          if (!cancelled) onComplete(result.blueprint, result.tool_id)
        }, 500)
      })
      .catch((err) => {
        if (cancelled) return
        setError(err instanceof Error ? err.message : 'Generation failed')
        setSteps((prev) =>
          prev.map((s) => (s.status === 'active' ? { ...s, status: 'error' } : s))
        )
      })

    return () => {
      cancelled = true
      clearInterval(interval)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/95 backdrop-blur-sm">
      <div className="w-full max-w-md mx-4">
        <div className="rounded-xl border-2 border-border bg-card p-8 shadow-lg">
          <h2 className="text-xl font-semibold text-foreground mb-6 text-center">
            Generating Blueprint
          </h2>

          <div className="space-y-4">
            {steps.map((step, i) => (
              <div key={i} className="flex items-center gap-3">
                {step.status === 'done' && (
                  <CheckCircle2 size={20} className="text-[var(--color-neo-done)] shrink-0" />
                )}
                {step.status === 'active' && (
                  <Loader2 size={20} className="animate-spin text-[var(--color-neo-progress)] shrink-0" />
                )}
                {step.status === 'pending' && (
                  <Circle size={20} className="text-muted-foreground/40 shrink-0" />
                )}
                {step.status === 'error' && (
                  <AlertCircle size={20} className="text-destructive shrink-0" />
                )}
                <span
                  className={`text-sm ${
                    step.status === 'done'
                      ? 'text-foreground'
                      : step.status === 'active'
                        ? 'text-foreground font-medium'
                        : step.status === 'error'
                          ? 'text-destructive'
                          : 'text-muted-foreground'
                  }`}
                >
                  {step.label}
                </span>
              </div>
            ))}
          </div>

          {/* Progress bar */}
          <div className="mt-6 h-2 rounded-full bg-muted overflow-hidden">
            <div
              className="h-full bg-primary transition-all duration-500 rounded-full"
              style={{
                width: `${(steps.filter((s) => s.status === 'done').length / steps.length) * 100}%`,
              }}
            />
          </div>

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
