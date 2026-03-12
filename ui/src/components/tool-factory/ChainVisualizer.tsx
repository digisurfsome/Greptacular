/**
 * Visual flow diagram of chain steps. Vertical layout with arrows.
 * Simpler than DependencyGraph -- just a linear chain, not a DAG.
 */

import { ArrowDown } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import type { TFChainConfigRow, TFStepType } from '@/lib/types'

interface ChainVisualizerProps {
  chain: TFChainConfigRow[]
}

function getStepTypeColor(type: TFStepType): string {
  switch (type) {
    case 'research': return 'bg-blue-500/10 text-blue-600 border-blue-500/30'
    case 'generation': return 'bg-purple-500/10 text-purple-600 border-purple-500/30'
    case 'action': return 'bg-orange-500/10 text-orange-600 border-orange-500/30'
    case 'manual': return 'bg-yellow-500/10 text-yellow-600 border-yellow-500/30'
  }
}

function getStepDotColor(type: TFStepType): string {
  switch (type) {
    case 'research': return 'bg-blue-500'
    case 'generation': return 'bg-purple-500'
    case 'action': return 'bg-orange-500'
    case 'manual': return 'bg-yellow-500'
  }
}

export function ChainVisualizer({ chain }: ChainVisualizerProps) {
  if (chain.length === 0) {
    return (
      <div className="flex items-center justify-center py-12 text-muted-foreground text-sm">
        No steps in chain
      </div>
    )
  }

  return (
    <div className="space-y-1">
      {chain.map((step, i) => (
        <div key={step.row_number}>
          {/* Step node */}
          <div className="flex items-start gap-3 rounded-lg border border-border bg-card p-3 hover:shadow-sm transition-shadow">
            {/* Step number dot */}
            <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 text-white text-xs font-bold ${getStepDotColor(step.step_type)}`}>
              {step.row_number}
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-sm font-semibold text-foreground">{step.title}</span>
                <Badge variant="outline" className={`text-xs ${getStepTypeColor(step.step_type)}`}>
                  {step.step_type}
                </Badge>
                {step.is_gate && (
                  <Badge variant="outline" className="text-xs bg-amber-500/10 text-amber-600 border-amber-500/30">
                    Gate
                  </Badge>
                )}
              </div>
              <div className="flex gap-3 mt-1 text-xs text-muted-foreground">
                <span>In: {step.input_source || 'User input'}</span>
                <span>Out: {step.output_destination || 'Next step'}</span>
              </div>
            </div>
          </div>

          {/* Arrow between steps */}
          {i < chain.length - 1 && (
            <div className="flex justify-center py-0.5">
              <ArrowDown size={14} className="text-muted-foreground/40" />
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
