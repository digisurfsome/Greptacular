/**
 * StepTracker — Left sidebar top half in the execution viewer.
 *
 * Shows a numbered list of strategy steps with status indicators,
 * a progress bar, and click-to-view-details popover.
 */

import { useState } from 'react'
import { ChevronRight } from 'lucide-react'
import type { YTStrategyStep, YTStrategyStepStatus } from '@/lib/types'

interface StepTrackerProps {
  steps: YTStrategyStep[]
  currentStepIndex: number
  stepStatuses: Map<string, YTStrategyStepStatus>
  onStepClick?: (stepId: string) => void
  collapsed?: boolean
}

const STATUS_ICONS: Record<YTStrategyStepStatus, { icon: string; className: string }> = {
  complete: { icon: '\u2713', className: 'text-green-400 bg-green-500/20' },
  in_progress: { icon: '\u25CF', className: 'text-cyan-400 bg-cyan-500/20 animate-pulse' },
  pending: { icon: '\u25CB', className: 'text-muted-foreground bg-muted' },
}

export function StepTracker({
  steps,
  currentStepIndex,
  stepStatuses,
  onStepClick,
  collapsed = false,
}: StepTrackerProps) {
  const [expandedStepId, setExpandedStepId] = useState<string | null>(null)

  const completedCount = steps.filter(
    (s) => (stepStatuses.get(s.id) ?? s.status) === 'complete',
  ).length
  const progressPercent = steps.length > 0 ? (completedCount / steps.length) * 100 : 0

  const getStatus = (step: YTStrategyStep): YTStrategyStepStatus => {
    return stepStatuses.get(step.id) ?? step.status
  }

  if (collapsed) {
    return (
      <div className="flex flex-col items-center gap-1 py-2">
        {steps.map((step, i) => {
          const status = getStatus(step)
          const config = STATUS_ICONS[status]
          return (
            <button
              key={step.id}
              onClick={() => onStepClick?.(step.id)}
              className={`w-7 h-7 rounded-md flex items-center justify-center text-xs font-medium transition-colors
                ${i === currentStepIndex ? 'ring-2 ring-primary' : ''}
                ${config.className}`}
              title={`${i + 1}. ${step.title}`}
            >
              {config.icon}
            </button>
          )
        })}
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Progress bar */}
      <div className="px-3 py-2 border-b border-border">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs font-medium text-muted-foreground">Progress</span>
          <span className="text-xs font-semibold text-foreground">
            {completedCount}/{steps.length}
          </span>
        </div>
        <div className="h-1.5 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full bg-green-500 rounded-full transition-all duration-500"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* Step list */}
      <div className="flex-1 overflow-auto py-1">
        {steps.map((step, i) => {
          const status = getStatus(step)
          const config = STATUS_ICONS[status]
          const isActive = i === currentStepIndex
          const isExpanded = expandedStepId === step.id

          return (
            <div key={step.id}>
              <button
                onClick={() => {
                  setExpandedStepId(isExpanded ? null : step.id)
                  onStepClick?.(step.id)
                }}
                className={`w-full flex items-center gap-2 px-3 py-1.5 text-left transition-colors hover:bg-muted/50
                  ${isActive ? 'bg-primary/10 border-l-2 border-primary' : 'border-l-2 border-transparent'}`}
              >
                <span
                  className={`w-5 h-5 rounded-md flex items-center justify-center text-[10px] font-bold shrink-0 ${config.className}`}
                >
                  {config.icon}
                </span>
                <span
                  className={`text-xs truncate flex-1 ${
                    isActive ? 'font-semibold text-foreground' : 'text-muted-foreground'
                  }`}
                >
                  {i + 1}. {step.title}
                </span>
                {step.description && (
                  <ChevronRight
                    size={10}
                    className={`text-muted-foreground shrink-0 transition-transform ${
                      isExpanded ? 'rotate-90' : ''
                    }`}
                  />
                )}
              </button>

              {/* Expanded details */}
              {isExpanded && step.description && (
                <div className="px-3 pb-2 pl-10">
                  <p className="text-[11px] text-muted-foreground leading-relaxed">
                    {step.description}
                  </p>
                  {step.expectedOutput && (
                    <p className="text-[11px] text-muted-foreground mt-1">
                      <span className="font-medium">Expected:</span> {step.expectedOutput}
                    </p>
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
