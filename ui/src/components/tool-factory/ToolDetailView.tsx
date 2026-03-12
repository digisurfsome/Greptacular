/**
 * Full tool detail view with 4 tabs: Blueprint, Theme, History, Settings.
 */

import { useState, useCallback } from 'react'
import { ArrowLeft, ExternalLink, Palette, RefreshCw, Archive, Share2, Pencil, Check, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { ChainVisualizer } from './ChainVisualizer'
import { ExecutionHistory } from './ExecutionHistory'
import { ShareToolModal } from './ShareToolModal'
import { useTool, useArchiveTool } from '@/hooks/useToolFactory'
import type { TFToolStatus } from '@/lib/types'

interface ToolDetailViewProps {
  toolId: string
  onBack: () => void
  onOpenThemePicker: () => void
}

type TabId = 'blueprint' | 'theme' | 'history' | 'settings'

const TABS: { id: TabId; label: string }[] = [
  { id: 'blueprint', label: 'Blueprint' },
  { id: 'theme', label: 'Theme' },
  { id: 'history', label: 'History' },
  { id: 'settings', label: 'Settings' },
]

function getStatusStyle(status: TFToolStatus): string {
  switch (status) {
    case 'active': return 'bg-[var(--color-neo-done)]/10 text-[var(--color-neo-done)] border-[var(--color-neo-done)]/30'
    case 'deploying': return 'bg-[var(--color-neo-progress)]/10 text-[var(--color-neo-progress)] border-[var(--color-neo-progress)]/30'
    case 'draft': return 'bg-[var(--color-neo-pending)]/10 text-[var(--color-neo-pending)] border-[var(--color-neo-pending)]/30'
    case 'error': return 'bg-destructive/10 text-destructive border-destructive/30'
    case 'archived': return 'bg-muted text-muted-foreground border-border'
  }
}

export function ToolDetailView({ toolId, onBack, onOpenThemePicker }: ToolDetailViewProps) {
  const [activeTab, setActiveTab] = useState<TabId>('blueprint')
  const [showShare, setShowShare] = useState(false)
  const [isEditingName, setIsEditingName] = useState(false)
  const [editName, setEditName] = useState('')
  const { data: tool, isLoading } = useTool(toolId)
  const archiveTool = useArchiveTool()

  const handleArchive = useCallback(async () => {
    if (!tool) return
    await archiveTool.mutateAsync(tool.tool_id)
    onBack()
  }, [tool, archiveTool, onBack])

  if (isLoading || !tool) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="animate-pulse bg-muted rounded-lg h-64 w-full max-w-2xl" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <Button variant="ghost" size="sm" onClick={onBack}>
            <ArrowLeft size={14} />
          </Button>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-semibold text-foreground">{tool.blueprint.tool_name}</h2>
              <Badge variant="outline" className={`text-xs ${getStatusStyle(tool.status)}`}>
                {tool.status}
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground mt-1">{tool.blueprint.tool_description}</p>
          </div>
        </div>
        <div className="flex gap-2 shrink-0">
          {tool.sheet_url && (
            <Button variant="outline" size="sm" asChild>
              <a href={tool.sheet_url} target="_blank" rel="noopener noreferrer" className="gap-1.5">
                <ExternalLink size={14} />
                Open Sheet
              </a>
            </Button>
          )}
          <Button variant="outline" size="sm" onClick={() => setShowShare(true)} className="gap-1.5">
            <Share2 size={14} />
            Share
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-border">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.id
                ? 'border-primary text-foreground'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === 'blueprint' && (
        <div className="space-y-6">
          <ChainVisualizer chain={tool.blueprint.chain_config} />

          {/* Detected APIs */}
          {tool.blueprint.detected_apis.length > 0 && (
            <Card>
              <CardContent className="p-4">
                <h3 className="text-sm font-semibold mb-3">Detected APIs</h3>
                <div className="space-y-2">
                  {tool.blueprint.detected_apis.map((api) => (
                    <div key={api.service_key} className="flex items-center justify-between text-sm">
                      <span>{api.service_name}</span>
                      <span className="text-xs text-muted-foreground font-mono">{api.service_key}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* User variables */}
          {tool.blueprint.user_input_variables.length > 0 && (
            <Card>
              <CardContent className="p-4">
                <h3 className="text-sm font-semibold mb-3">User Variables</h3>
                <div className="flex flex-wrap gap-1.5">
                  {tool.blueprint.user_input_variables.map((v) => (
                    <Badge key={v} variant="outline" className="text-xs font-mono">
                      {v}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Source info */}
          <Card>
            <CardContent className="p-4">
              <h3 className="text-sm font-semibold mb-3">Source</h3>
              <div className="text-sm text-muted-foreground space-y-1">
                <p>Type: <span className="text-foreground capitalize">{tool.blueprint.ingestion_source.replace('_', ' ')}</span></p>
                {tool.blueprint.source_video_title && (
                  <p>Video: <span className="text-foreground">{tool.blueprint.source_video_title}</span></p>
                )}
                {tool.blueprint.source_video_channel && (
                  <p>Channel: <span className="text-foreground">{tool.blueprint.source_video_channel}</span></p>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {activeTab === 'theme' && (
        <div className="space-y-4">
          {tool.active_theme ? (
            <Card>
              <CardContent className="p-4 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold">{tool.active_theme.theme_name}</h3>
                  <Button variant="outline" size="sm" onClick={onOpenThemePicker} className="gap-1.5">
                    <Palette size={14} />
                    Change Theme
                  </Button>
                </div>

                {/* Color palette */}
                <div>
                  <p className="text-xs text-muted-foreground mb-2">Colors</p>
                  <div className="flex gap-1">
                    {Object.entries(tool.active_theme.colors).map(([key, value]) => (
                      <div
                        key={key}
                        className="w-8 h-8 rounded border border-border/50"
                        style={{ backgroundColor: value }}
                        title={`${key}: ${value}`}
                      />
                    ))}
                  </div>
                </div>

                {/* Typography */}
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Typography</p>
                  <p className="text-sm">
                    {tool.active_theme.typography.font_family_heading} / {tool.active_theme.typography.font_family_body}
                  </p>
                </div>

                {/* Classification */}
                {tool.active_theme.style_classification && (
                  <Badge variant="outline">{tool.active_theme.style_classification}</Badge>
                )}
              </CardContent>
            </Card>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              <Palette size={24} className="mb-2 opacity-50" />
              <p className="text-sm">No theme applied</p>
              <Button variant="outline" size="sm" className="mt-3 gap-1.5" onClick={onOpenThemePicker}>
                <Palette size={14} />
                Apply Theme
              </Button>
            </div>
          )}
        </div>
      )}

      {activeTab === 'history' && (
        <ExecutionHistory toolId={tool.tool_id} />
      )}

      {activeTab === 'settings' && (
        <div className="space-y-6 max-w-lg">
          {/* Tool name */}
          <div>
            <label className="text-xs font-medium text-muted-foreground">Tool Name</label>
            {isEditingName ? (
              <div className="flex gap-2 mt-1">
                <Input
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                />
                <Button size="sm" onClick={() => setIsEditingName(false)}>
                  <Check size={14} />
                </Button>
                <Button variant="ghost" size="sm" onClick={() => setIsEditingName(false)}>
                  <X size={14} />
                </Button>
              </div>
            ) : (
              <div className="flex items-center gap-2 mt-1">
                <p className="text-sm text-foreground">{tool.blueprint.tool_name}</p>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0"
                  onClick={() => { setEditName(tool.blueprint.tool_name); setIsEditingName(true) }}
                >
                  <Pencil size={12} />
                </Button>
              </div>
            )}
          </div>

          {/* Tags */}
          <div>
            <label className="text-xs font-medium text-muted-foreground">Tags</label>
            <div className="flex flex-wrap gap-1.5 mt-1">
              {tool.tags.length > 0 ? tool.tags.map((tag) => (
                <Badge key={tag} variant="outline" className="text-xs">{tag}</Badge>
              )) : (
                <span className="text-sm text-muted-foreground">No tags</span>
              )}
            </div>
          </div>

          {/* Danger zone */}
          <div className="pt-4 border-t border-border">
            <h4 className="text-sm font-semibold text-destructive mb-3">Danger Zone</h4>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                className="gap-1.5 text-destructive border-destructive/30 hover:bg-destructive/5"
                onClick={handleArchive}
                disabled={archiveTool.isPending}
              >
                <Archive size={14} />
                Archive Tool
              </Button>
              <Button variant="outline" size="sm" className="gap-1.5">
                <RefreshCw size={14} />
                Re-generate
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Share Modal */}
      {showShare && (
        <ShareToolModal
          isOpen={showShare}
          tool={tool}
          onClose={() => setShowShare(false)}
        />
      )}
    </div>
  )
}
