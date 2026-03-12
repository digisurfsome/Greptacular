/**
 * Card for a single tool in the Tool Manager grid.
 * Shows tool name, status badge, theme swatches, source icon, and stats.
 */

import { Youtube, FileText, Clock, Play } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import type { TFGeneratedTool, TFToolStatus } from '@/lib/types'

interface ToolCardProps {
  tool: TFGeneratedTool
  onClick: () => void
}

function getStatusStyle(status: TFToolStatus): string {
  switch (status) {
    case 'active': return 'bg-[var(--color-neo-done)]/10 text-[var(--color-neo-done)] border-[var(--color-neo-done)]/30'
    case 'deploying': return 'bg-[var(--color-neo-progress)]/10 text-[var(--color-neo-progress)] border-[var(--color-neo-progress)]/30'
    case 'draft': return 'bg-[var(--color-neo-pending)]/10 text-[var(--color-neo-pending)] border-[var(--color-neo-pending)]/30'
    case 'error': return 'bg-destructive/10 text-destructive border-destructive/30'
    case 'archived': return 'bg-muted text-muted-foreground border-border'
  }
}

function formatDate(iso: string | null): string {
  if (!iso) return 'Never'
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

export function ToolCard({ tool, onClick }: ToolCardProps) {
  const isYouTube = tool.blueprint.ingestion_source === 'youtube'

  return (
    <button
      onClick={onClick}
      className="text-left rounded-lg border-2 border-border bg-card p-4 hover:shadow-md hover:-translate-y-0.5 transition-all w-full"
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-3">
        <h3 className="text-sm font-semibold text-foreground line-clamp-2">
          {tool.blueprint.tool_name}
        </h3>
        <Badge variant="outline" className={`shrink-0 text-xs ${getStatusStyle(tool.status)}`}>
          {tool.status}
        </Badge>
      </div>

      {/* Theme swatches */}
      {tool.active_theme && (
        <div className="flex gap-0.5 mb-3">
          {[
            tool.active_theme.colors.brand_light,
            tool.active_theme.colors.brand_default,
            tool.active_theme.colors.brand_dark,
            tool.active_theme.colors.surface_base,
          ].map((color, i) => (
            <div
              key={i}
              className="w-4 h-4 rounded-sm border border-border/50"
              style={{ backgroundColor: color }}
            />
          ))}
        </div>
      )}

      {/* Source and stats */}
      <div className="flex items-center gap-3 text-xs text-muted-foreground">
        <span className="flex items-center gap-1">
          {isYouTube ? <Youtube size={12} /> : <FileText size={12} />}
          {isYouTube ? 'YouTube' : 'PRD'}
        </span>
        <span className="flex items-center gap-1">
          <Play size={12} />
          {tool.times_run} runs
        </span>
        <span className="flex items-center gap-1">
          <Clock size={12} />
          {formatDate(tool.last_run_at)}
        </span>
      </div>
    </button>
  )
}
