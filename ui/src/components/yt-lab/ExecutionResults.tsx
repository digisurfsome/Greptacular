import { CheckCircle, XCircle, AlertTriangle, Clock } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import type { ExecutionResultData } from '@/lib/types'

interface ExecutionResultsProps {
  result: ExecutionResultData | null
}

export default function ExecutionResults({ result }: ExecutionResultsProps) {
  if (!result) return null

  const statusConfig = {
    success: { icon: <CheckCircle className="h-4 w-4 text-green-400" />, color: 'bg-green-500/20 text-green-400' },
    failure: { icon: <XCircle className="h-4 w-4 text-red-400" />, color: 'bg-red-500/20 text-red-400' },
    partial: { icon: <AlertTriangle className="h-4 w-4 text-yellow-400" />, color: 'bg-yellow-500/20 text-yellow-400' },
  }

  const config = statusConfig[result.status] || statusConfig.failure

  return (
    <div className="space-y-3 p-4 border border-border rounded-lg bg-card">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {config.icon}
          <span className="text-sm font-medium">
            {result.status === 'success' ? 'Execution Complete' :
             result.status === 'partial' ? 'Partial Result' : 'Execution Failed'}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className={`text-[10px] ${config.color}`}>
            {result.status}
          </Badge>
          {result.duration > 0 && (
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <Clock className="h-3 w-3" /> {result.duration.toFixed(1)}s
            </span>
          )}
        </div>
      </div>

      {/* Error message */}
      {result.error && (
        <div className="p-2.5 rounded border border-red-500/20 bg-red-500/5">
          <p className="text-xs text-red-400">{result.error}</p>
        </div>
      )}

      {/* Output data */}
      {result.data && Object.keys(result.data).length > 0 && (
        <div className="space-y-1">
          <h4 className="text-xs font-semibold text-muted-foreground uppercase">Output</h4>
          <pre className="p-2.5 rounded border border-border bg-muted/30 text-xs overflow-auto max-h-60 whitespace-pre-wrap">
            {JSON.stringify(result.data, null, 2)}
          </pre>
        </div>
      )}

      {/* Metadata */}
      {result.metadata && Object.keys(result.metadata).length > 0 && (
        <div className="space-y-1">
          <h4 className="text-xs font-semibold text-muted-foreground uppercase">Metadata</h4>
          <div className="flex flex-wrap gap-1.5">
            {Object.entries(result.metadata).map(([key, value]) => (
              <Badge key={key} variant="outline" className="text-[10px]">
                {key}: {String(value)}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
