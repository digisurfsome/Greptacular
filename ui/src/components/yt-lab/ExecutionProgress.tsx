import { Loader2, CheckCircle, XCircle, Clock } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import type { ExecutionProgressEvent } from '@/lib/types'

interface ExecutionProgressProps {
  executionId: string | null
  progressEvents: ExecutionProgressEvent[]
  status: 'idle' | 'running' | 'complete' | 'error'
}

/**
 * Pure display component for execution progress.
 * Receives progress events as props from the parent page component.
 * Does NOT create or manage WebSocket connections.
 */
export default function ExecutionProgress({ executionId, progressEvents, status }: ExecutionProgressProps) {
  if (!executionId || status === 'idle') {
    return null
  }

  const statusIcon = {
    running: <Loader2 className="h-4 w-4 animate-spin text-blue-400" />,
    complete: <CheckCircle className="h-4 w-4 text-green-400" />,
    error: <XCircle className="h-4 w-4 text-red-400" />,
    idle: <Clock className="h-4 w-4 text-muted-foreground" />,
  }

  const statusColor = {
    running: 'bg-blue-500/20 text-blue-400',
    complete: 'bg-green-500/20 text-green-400',
    error: 'bg-red-500/20 text-red-400',
    idle: 'bg-muted text-muted-foreground',
  }

  return (
    <div className="space-y-2 p-4 border border-border rounded-lg bg-card">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {statusIcon[status]}
          <span className="text-sm font-medium">Execution {executionId}</span>
        </div>
        <Badge variant="outline" className={`text-[10px] ${statusColor[status]}`}>
          {status}
        </Badge>
      </div>

      {/* Progress bar for running state */}
      {status === 'running' && (
        <div className="h-1.5 bg-muted rounded-full overflow-hidden">
          <div className="h-full bg-blue-500 rounded-full animate-pulse w-1/3" />
        </div>
      )}

      {/* Event log */}
      {progressEvents.length > 0 && (
        <div className="space-y-1 max-h-40 overflow-auto">
          {progressEvents.map((event, i) => (
            <div key={i} className="flex items-start gap-2 text-xs">
              <span className="text-muted-foreground font-mono w-6 shrink-0">
                {event.step_number !== undefined ? `#${event.step_number}` : ''}
              </span>
              <span className={event.type === 'error' ? 'text-red-400' : 'text-muted-foreground'}>
                {event.message || event.type}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
