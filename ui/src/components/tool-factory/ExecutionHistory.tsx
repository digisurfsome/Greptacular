/**
 * Table showing execution history for a tool.
 * Displays run number, timestamp, steps completed, tokens used, and duration.
 */

import { Clock, Zap, Hash } from 'lucide-react'

interface ExecutionRun {
  run_number: number
  timestamp: string
  steps_completed: number
  total_steps: number
  tokens_used: number
  duration_seconds: number
}

interface ExecutionHistoryProps {
  toolId: string
  runs?: ExecutionRun[]
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}m ${secs}s`
}

export function ExecutionHistory({ runs }: ExecutionHistoryProps) {
  if (!runs || runs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
        <Clock size={24} className="mb-2 opacity-50" />
        <p className="text-sm">No execution history yet</p>
        <p className="text-xs mt-1">Runs will appear here after the tool is executed.</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Summary stats */}
      <div className="grid grid-cols-3 gap-3">
        <div className="rounded-md border border-border p-3 text-center">
          <p className="text-2xl font-bold text-foreground">{runs.length}</p>
          <p className="text-xs text-muted-foreground">Total Runs</p>
        </div>
        <div className="rounded-md border border-border p-3 text-center">
          <p className="text-2xl font-bold text-foreground">
            {runs.reduce((sum, r) => sum + r.tokens_used, 0).toLocaleString()}
          </p>
          <p className="text-xs text-muted-foreground">Total Tokens</p>
        </div>
        <div className="rounded-md border border-border p-3 text-center">
          <p className="text-2xl font-bold text-foreground">
            {formatDuration(Math.round(runs.reduce((sum, r) => sum + r.duration_seconds, 0) / runs.length))}
          </p>
          <p className="text-xs text-muted-foreground">Avg Duration</p>
        </div>
      </div>

      {/* Runs table */}
      <div className="rounded-lg border border-border overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/30">
              <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground">
                <Hash size={12} className="inline mr-1" />Run
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground">
                <Clock size={12} className="inline mr-1" />Time
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Steps</th>
              <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground">
                <Zap size={12} className="inline mr-1" />Tokens
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Duration</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => (
              <tr key={run.run_number} className="border-b border-border/50 hover:bg-muted/20">
                <td className="px-3 py-2 font-mono">{run.run_number}</td>
                <td className="px-3 py-2 text-muted-foreground">
                  {new Date(run.timestamp).toLocaleString(undefined, {
                    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
                  })}
                </td>
                <td className="px-3 py-2">
                  {run.steps_completed}/{run.total_steps}
                </td>
                <td className="px-3 py-2 font-mono">{run.tokens_used.toLocaleString()}</td>
                <td className="px-3 py-2">{formatDuration(run.duration_seconds)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
