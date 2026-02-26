/**
 * ExpandPanel Component
 *
 * Simple panel for adding features to an existing Agent OS project.
 * User describes new features in natural language, system analyzes
 * conflicts and generates specs.
 */

import { useState, useCallback } from 'react'
import { Plus, AlertTriangle, CheckCircle2, Loader2, ChevronDown, ChevronUp } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  useExpandFeatures,
  useBuildPlan,
  type AgentOSExpandResult,
} from '@/hooks/useAgentOS'

interface ExpandPanelProps {
  projectName: string
  onExpansionComplete: () => void
}

const PRIORITY_COLORS: Record<string, string> = {
  must_have: 'bg-green-100 text-green-800 border-green-300',
  should_have: 'bg-blue-100 text-blue-800 border-blue-300',
  nice_to_have: 'bg-gray-100 text-gray-700 border-gray-300',
}

const COMPLEXITY_COLORS: Record<string, string> = {
  small: 'bg-emerald-100 text-emerald-700 border-emerald-300',
  medium: 'bg-amber-100 text-amber-700 border-amber-300',
  large: 'bg-red-100 text-red-700 border-red-300',
}

export function ExpandPanel({ projectName, onExpansionComplete }: ExpandPanelProps): React.JSX.Element {
  const [description, setDescription] = useState('')
  const [result, setResult] = useState<AgentOSExpandResult | null>(null)
  const [showBuildPlan, setShowBuildPlan] = useState(false)

  const expandMutation = useExpandFeatures(projectName)
  const { data: buildPlanData } = useBuildPlan(projectName)

  const handleAnalyze = useCallback(() => {
    if (!description.trim()) return

    // Parse simple feature descriptions into feature objects
    const featureLines = description.split('\n').filter(line => line.trim())
    const features = featureLines.map(line => ({
      name: line.trim().replace(/^[-*•]\s*/, ''),
      description: line.trim(),
      priority: 'should_have',
      complexity: 'medium',
      category: 'general',
      dependencies: [],
    }))

    expandMutation.mutate(features, {
      onSuccess: (data) => {
        setResult(data)
        if (data.added && data.added.length > 0) {
          onExpansionComplete()
        }
      },
    })
  }, [description, expandMutation, onExpansionComplete])

  const hasConflicts = (result?.conflicts?.length ?? 0) > 0
  const hasWarnings = (result?.warnings?.length ?? 0) > 0
  const addedCount = result?.added?.length ?? 0

  return (
    <div className="border-2 border-border rounded-lg bg-card">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-border">
        <Plus size={16} className="text-primary" />
        <span className="text-sm font-bold text-foreground">Add Features</span>
      </div>

      {/* Input area */}
      <div className="p-4 space-y-3">
        <div>
          <label className="text-xs font-semibold text-muted-foreground block mb-1.5">
            Describe the features you want to add:
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder={"User notifications\nEmail templates\nPush notifications"}
            rows={4}
            className="w-full px-3 py-2 text-sm bg-background border-2 border-border rounded-lg resize-none focus:outline-none focus:border-primary placeholder:text-muted-foreground/50"
          />
        </div>

        <Button
          onClick={handleAnalyze}
          disabled={!description.trim() || expandMutation.isPending}
          className="w-full gap-2 font-bold"
          size="sm"
        >
          {expandMutation.isPending ? (
            <>
              <Loader2 size={14} className="animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <Plus size={14} />
              Analyze & Add
            </>
          )}
        </Button>
      </div>

      {/* Results */}
      {result && (
        <div className="border-t border-border p-4 space-y-3">
          {/* Added features */}
          {addedCount > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-1.5">
                <CheckCircle2 size={14} className="text-green-500" />
                <span className="text-xs font-bold text-foreground">
                  Added {addedCount} new feature{addedCount !== 1 ? 's' : ''}:
                </span>
              </div>
              {result.added.map((feat) => (
                <div
                  key={feat.id}
                  className="flex items-center gap-2 pl-5 text-xs text-muted-foreground"
                >
                  <span className="font-semibold text-foreground">
                    #{feat.id} {feat.name}
                  </span>
                  <Badge
                    variant="outline"
                    className={`text-[10px] px-1.5 py-0 ${PRIORITY_COLORS[feat.priority] ?? ''}`}
                  >
                    {feat.priority?.replace('_', ' ')}
                  </Badge>
                  <Badge
                    variant="outline"
                    className={`text-[10px] px-1.5 py-0 ${COMPLEXITY_COLORS[feat.complexity] ?? ''}`}
                  >
                    {feat.complexity}
                  </Badge>
                </div>
              ))}
            </div>
          )}

          {/* Conflicts */}
          {hasConflicts && (
            <div className="space-y-1.5">
              <div className="flex items-center gap-1.5">
                <AlertTriangle size={14} className="text-amber-500" />
                <span className="text-xs font-bold text-foreground">Conflicts:</span>
              </div>
              {result.conflicts.map((c, i) => (
                <div key={i} className="pl-5 text-xs text-muted-foreground">
                  <span className="font-medium text-amber-600">{c.name}</span>
                  {' — '}
                  {c.reason}
                </div>
              ))}
            </div>
          )}

          {/* Warnings */}
          {hasWarnings && (
            <div className="space-y-1">
              {result.warnings.map((w, i) => (
                <div key={i} className="text-xs text-amber-600 pl-5">
                  {w}
                </div>
              ))}
            </div>
          )}

          {/* Build plan toggle */}
          {addedCount > 0 && (
            <div>
              <button
                onClick={() => setShowBuildPlan(!showBuildPlan)}
                className="flex items-center gap-1.5 text-xs font-semibold text-primary hover:text-primary/80 transition-colors"
              >
                {showBuildPlan ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                View Updated Build Plan
              </button>
              {showBuildPlan && buildPlanData?.plan && (
                <pre className="mt-2 p-3 text-[11px] bg-muted/30 border border-border rounded-md overflow-x-auto whitespace-pre-wrap font-mono text-muted-foreground">
                  {buildPlanData.plan}
                </pre>
              )}
            </div>
          )}
        </div>
      )}

      {/* Error */}
      {expandMutation.isError && (
        <div className="border-t border-border p-4">
          <div className="text-xs text-red-500">
            Failed to add features: {(expandMutation.error as Error)?.message ?? 'Unknown error'}
          </div>
        </div>
      )}
    </div>
  )
}
