import { useQuery, useMutation } from '@tanstack/react-query'
import { Loader2, Sparkles, Target, AlertTriangle, Trophy } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { getGamePlan, generateGamePlan } from '@/lib/api'
import type { YTGamePlanStep } from '@/lib/types'

interface GamePlanViewProps {
  videoId: string
  transcriptText?: string
}

export default function GamePlanView({ videoId, transcriptText }: GamePlanViewProps) {
  const { data: gamePlan, isLoading, refetch } = useQuery({
    queryKey: ['yt-game-plan', videoId],
    queryFn: () => getGamePlan(videoId),
    retry: false,
  })

  const generateMutation = useMutation({
    mutationFn: () => {
      if (!transcriptText) throw new Error('No transcript available')
      return generateGamePlan(videoId, transcriptText)
    },
    onSuccess: () => refetch(),
  })

  const effortColor = (e: string) => {
    switch (e) {
      case 'low': return 'bg-green-500/20 text-green-400'
      case 'medium': return 'bg-yellow-500/20 text-yellow-400'
      case 'high': return 'bg-red-500/20 text-red-400'
      default: return 'bg-muted text-muted-foreground'
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 p-4 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" /> Loading game plan...
      </div>
    )
  }

  if (!gamePlan) {
    return (
      <div className="p-4 space-y-3">
        <p className="text-sm text-muted-foreground">No game plan generated yet.</p>
        {transcriptText && (
          <Button
            size="sm"
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
            className="gap-1.5"
          >
            {generateMutation.isPending ? (
              <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Generating...</>
            ) : (
              <><Sparkles className="h-3.5 w-3.5" /> Generate Game Plan</>
            )}
          </Button>
        )}
        {generateMutation.isError && (
          <p className="text-xs text-red-400">
            {generateMutation.error instanceof Error ? generateMutation.error.message : 'Generation failed'}
          </p>
        )}
      </div>
    )
  }

  const data = gamePlan.data

  return (
    <div className="space-y-4 p-4">
      {/* Key Strategy */}
      <div className="p-3 rounded-lg border border-border bg-card">
        <div className="flex items-center gap-2 mb-1">
          <Target className="h-4 w-4 text-blue-400" />
          <h3 className="text-sm font-semibold">Key Strategy</h3>
          <Badge variant="outline" className={`text-[10px] ml-auto ${effortColor(data.estimated_effort)}`}>
            {data.estimated_effort} effort
          </Badge>
        </div>
        <p className="text-sm text-foreground">{data.key_strategy}</p>
        {data.estimated_time && (
          <p className="text-xs text-muted-foreground mt-1">Timeline: {data.estimated_time}</p>
        )}
      </div>

      {/* Prerequisites */}
      {data.prerequisites?.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-muted-foreground uppercase mb-1">Prerequisites</h4>
          <ul className="text-xs text-muted-foreground space-y-0.5">
            {data.prerequisites.map((p: string, i: number) => (
              <li key={i} className="flex items-start gap-1.5">
                <span className="text-muted-foreground/50 mt-0.5">-</span>
                {p}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Steps */}
      <div className="space-y-2">
        <h4 className="text-xs font-semibold text-muted-foreground uppercase">Steps</h4>
        {data.steps_overview?.map((step: YTGamePlanStep) => (
          <div key={step.order} className="p-2.5 rounded border border-border bg-card">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-muted-foreground w-5">{step.order}.</span>
              <span className="text-sm font-medium">{step.title}</span>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5 ml-7">{step.description}</p>
            {step.key_actions?.length > 0 && (
              <ul className="mt-1 ml-7 space-y-0.5">
                {step.key_actions.map((action: string, i: number) => (
                  <li key={i} className="text-xs text-muted-foreground flex items-start gap-1">
                    <span className="text-muted-foreground/50">-</span> {action}
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>

      {/* Key Insights */}
      {data.key_insights?.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-muted-foreground uppercase mb-1">Key Insights</h4>
          <ul className="space-y-0.5">
            {data.key_insights.map((insight: string, i: number) => (
              <li key={i} className="text-xs text-foreground flex items-start gap-1.5">
                <Sparkles className="h-3 w-3 text-yellow-400 shrink-0 mt-0.5" /> {insight}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Pitfalls */}
      {data.potential_pitfalls?.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-muted-foreground uppercase mb-1">Watch Out For</h4>
          <ul className="space-y-0.5">
            {data.potential_pitfalls.map((pitfall: string, i: number) => (
              <li key={i} className="text-xs text-orange-400/80 flex items-start gap-1.5">
                <AlertTriangle className="h-3 w-3 shrink-0 mt-0.5" /> {pitfall}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Expected Outcome */}
      {data.expected_outcome && (
        <div className="p-2.5 rounded border border-green-500/20 bg-green-500/5">
          <div className="flex items-center gap-1.5 mb-0.5">
            <Trophy className="h-3.5 w-3.5 text-green-400" />
            <h4 className="text-xs font-semibold text-green-400">Expected Outcome</h4>
          </div>
          <p className="text-xs text-foreground">{data.expected_outcome}</p>
        </div>
      )}
    </div>
  )
}
