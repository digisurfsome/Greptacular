import { useQuery } from '@tanstack/react-query'
import { Loader2, AlertTriangle, Wrench, CheckCircle } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { getGapDashboard, listBuildSpecs } from '@/lib/api'
import type { GapRecord, BuildSpec } from '@/lib/types'

export default function GapDashboard() {
  const { data: gaps = [], isLoading: gapsLoading } = useQuery({
    queryKey: ['gap-dashboard'],
    queryFn: getGapDashboard,
    staleTime: 1000 * 30,  // 30s stale time for dashboard data
  })

  const { data: specs = [], isLoading: specsLoading } = useQuery({
    queryKey: ['build-specs'],
    queryFn: listBuildSpecs,
    staleTime: 1000 * 30,
  })

  const isLoading = gapsLoading || specsLoading

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 p-4 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" /> Loading gap dashboard...
      </div>
    )
  }

  const statusColor = (status: string) => {
    switch (status) {
      case 'open': return 'bg-red-500/20 text-red-400'
      case 'in_progress': return 'bg-yellow-500/20 text-yellow-400'
      case 'resolved': return 'bg-green-500/20 text-green-400'
      default: return 'bg-muted text-muted-foreground'
    }
  }

  const complexityColor = (c: string) => {
    switch (c) {
      case 'low': return 'bg-green-500/20 text-green-400'
      case 'medium': return 'bg-yellow-500/20 text-yellow-400'
      case 'high': return 'bg-red-500/20 text-red-400'
      default: return 'bg-muted text-muted-foreground'
    }
  }

  const specStatusColor = (s: string) => {
    switch (s) {
      case 'pending_review': return 'bg-yellow-500/20 text-yellow-400'
      case 'approved': return 'bg-blue-500/20 text-blue-400'
      case 'built': return 'bg-green-500/20 text-green-400'
      default: return 'bg-muted text-muted-foreground'
    }
  }

  return (
    <div className="space-y-6 p-4">
      {/* Gaps Section */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-yellow-400" />
          <h3 className="text-sm font-semibold">Capability Gaps</h3>
          <span className="text-xs text-muted-foreground">({gaps.length} detected)</span>
        </div>

        {gaps.length === 0 ? (
          <p className="text-sm text-muted-foreground">No gaps detected yet. Run some tool executions to detect missing capabilities.</p>
        ) : (
          <div className="space-y-2">
            {gaps.map((gap: GapRecord) => (
              <div key={gap.id} className="p-3 rounded border border-border bg-card space-y-1.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{gap.required_capability}</span>
                    <Badge variant="outline" className="text-[10px]">{gap.component_type}</Badge>
                    <Badge variant="outline" className={`text-[10px] ${statusColor(gap.status)}`}>
                      {gap.status}
                    </Badge>
                  </div>
                  <Badge variant="outline" className="text-[10px]">
                    {gap.frequency}x
                  </Badge>
                </div>
                {gap.affected_tools.length > 0 && (
                  <div className="flex items-center gap-1 flex-wrap">
                    <span className="text-[10px] text-muted-foreground">Affects:</span>
                    {gap.affected_tools.map((toolId: string) => (
                      <Badge key={toolId} variant="outline" className="text-[10px]">
                        {toolId}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Build Specs Section */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <Wrench className="h-4 w-4 text-blue-400" />
          <h3 className="text-sm font-semibold">Build Specs</h3>
          <span className="text-xs text-muted-foreground">({specs.length} generated)</span>
        </div>

        {specs.length === 0 ? (
          <p className="text-sm text-muted-foreground">No build specs generated yet.</p>
        ) : (
          <div className="space-y-2">
            {specs.map((spec: BuildSpec) => (
              <div key={spec.id} className="p-3 rounded border border-border bg-card space-y-1.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{spec.component_name}</span>
                    <Badge variant="outline" className={`text-[10px] ${complexityColor(spec.complexity)}`}>
                      {spec.complexity}
                    </Badge>
                    <Badge variant="outline" className={`text-[10px] ${specStatusColor(spec.status)}`}>
                      {spec.status.replace('_', ' ')}
                    </Badge>
                  </div>
                </div>

                {spec.interface_contract && (
                  <pre className="text-[10px] text-muted-foreground bg-muted/30 p-2 rounded overflow-auto max-h-20">
                    {spec.interface_contract}
                  </pre>
                )}

                {spec.similar_components.length > 0 && (
                  <div className="flex items-center gap-1 flex-wrap">
                    <span className="text-[10px] text-muted-foreground">Similar:</span>
                    {spec.similar_components.map((name: string) => (
                      <Badge key={name} variant="outline" className="text-[10px]">
                        <CheckCircle className="h-2 w-2 mr-0.5" /> {name}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
