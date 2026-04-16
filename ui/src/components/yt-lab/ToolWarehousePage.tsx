import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Loader2, Package } from 'lucide-react'
import { loadToolPage, submitExecution } from '@/lib/api'
import type { ExecutionProgressEvent, ExecutionResultData } from '@/lib/types'
import ToolPageForm from './ToolPageForm'
import ExecutionProgress from './ExecutionProgress'
import ExecutionResults from './ExecutionResults'

interface ToolWarehousePageProps {
  toolId: string
}

export default function ToolWarehousePage({ toolId }: ToolWarehousePageProps) {
  const [executionId, setExecutionId] = useState<string | null>(null)
  const [executionStatus, setExecutionStatus] = useState<'idle' | 'running' | 'complete' | 'error'>('idle')
  const [progressEvents, setProgressEvents] = useState<ExecutionProgressEvent[]>([])
  const [executionResult, setExecutionResult] = useState<ExecutionResultData | null>(null)

  const { data: toolPage, isLoading } = useQuery({
    queryKey: ['warehouse-tool', toolId],
    queryFn: () => loadToolPage(toolId),
  })

  const executeMutation = useMutation({
    mutationFn: (inputs: Record<string, string | number>) => submitExecution(toolId, inputs),
    onSuccess: (data) => {
      setExecutionId(data.execution_id)
      setExecutionStatus('running')
      setProgressEvents([
        { type: 'started', message: 'Execution queued — real-time progress tracking coming soon' },
      ])
    },
    onError: (err) => {
      setExecutionStatus('error')
      setProgressEvents(prev => [...prev, {
        type: 'error',
        message: err instanceof Error ? err.message : 'Execution failed',
      }])
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 p-4 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" /> Loading tool...
      </div>
    )
  }

  if (!toolPage) {
    return (
      <div className="p-4 text-sm text-muted-foreground">
        Tool not found.
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Tool header */}
      <div className="flex items-center gap-2 p-4 border-b border-border">
        <Package className="h-5 w-5 text-muted-foreground" />
        <div>
          <h2 className="text-base font-semibold">{toolPage.name}</h2>
          {toolPage.description && (
            <p className="text-xs text-muted-foreground">{toolPage.description}</p>
          )}
        </div>
      </div>

      {/* Input form */}
      <ToolPageForm
        inputSchema={toolPage.input_schema}
        onSubmit={(values) => executeMutation.mutate(values)}
        isLoading={executeMutation.isPending || executionStatus === 'running'}
      />

      {/* Progress */}
      <ExecutionProgress
        executionId={executionId}
        progressEvents={progressEvents}
        status={executionStatus}
      />

      {/* Results */}
      <ExecutionResults result={executionResult} />
    </div>
  )
}
