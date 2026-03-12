/**
 * Tool Manager page -- grid of tools with filtering, search, sort.
 * Route: /#/tools
 */

import { useState, useMemo, useCallback } from 'react'
import { ArrowLeft, BookOpen, ChevronRight, Search, Wrench, Plus, BarChart3, Layers, CheckCircle2, Circle, Loader2, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import { ToolCard } from './ToolCard'
import { ToolDetailView } from './ToolDetailView'
import { ThemePicker } from './ThemePicker'
import { AnalyticsDashboard } from './AnalyticsDashboard'
import { ToolFactoryGuidePanel } from './ToolFactoryGuidePanel'
import { useTools, useToolStats, useStartBatch, useBatchStatus } from '@/hooks/useToolFactory'
import { useSwapTheme } from '@/hooks/useToolThemes'
import type { TFToolStatus, TFThemeConfig, YTStrategyProject } from '@/lib/types'

type SortOption = 'created' | 'last_run' | 'name'
type ViewTab = 'tools' | 'analytics'

const STATUS_FILTERS: { value: TFToolStatus | 'all'; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'active', label: 'Active' },
  { value: 'draft', label: 'Draft' },
  { value: 'error', label: 'Error' },
  { value: 'archived', label: 'Archived' },
]

export function ToolManagerPage() {
  const [selectedToolId, setSelectedToolId] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<TFToolStatus | 'all'>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState<SortOption>('created')
  const [showThemePicker, setShowThemePicker] = useState(false)
  const [activeTab, setActiveTab] = useState<ViewTab>('tools')
  const [showGuide, setShowGuide] = useState(false)
  const [showBatchModal, setShowBatchModal] = useState(false)
  const [batchSelectedIds, setBatchSelectedIds] = useState<Set<string>>(new Set())
  const [batchAutoDeploy, setBatchAutoDeploy] = useState(false)
  const [activeBatchId, setActiveBatchId] = useState<string | null>(null)

  const { data: tools, isLoading } = useTools(statusFilter === 'all' ? undefined : statusFilter)
  const { data: stats } = useToolStats()
  const swapTheme = useSwapTheme()
  const startBatch = useStartBatch()
  const { data: batchStatus } = useBatchStatus(activeBatchId)

  /** Read YT Lab projects from localStorage, filter to those with steps. */
  const ytLabProjects = useMemo((): YTStrategyProject[] => {
    try {
      const raw = localStorage.getItem('yt-lab-projects')
      if (!raw) return []
      const all: YTStrategyProject[] = JSON.parse(raw)
      return all.filter((p) => {
        const stepsRaw = localStorage.getItem(`yt-lab-steps-${p.id}`)
        if (!stepsRaw) return false
        const steps = JSON.parse(stepsRaw)
        return Array.isArray(steps) && steps.length > 0
      })
    } catch {
      return []
    }
  }, [])

  const handleToggleBatchProject = useCallback((projectId: string) => {
    setBatchSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(projectId)) {
        next.delete(projectId)
      } else {
        next.add(projectId)
      }
      return next
    })
  }, [])

  const handleStartBatch = useCallback(async () => {
    if (batchSelectedIds.size === 0) return
    try {
      const result = await startBatch.mutateAsync({
        project_ids: Array.from(batchSelectedIds),
        auto_deploy: batchAutoDeploy,
      })
      setActiveBatchId(result.batch_id)
    } catch (err) {
      console.error('Batch start failed:', err)
    }
  }, [batchSelectedIds, batchAutoDeploy, startBatch])

  const handleCloseBatchModal = useCallback(() => {
    setShowBatchModal(false)
    setBatchSelectedIds(new Set())
    setBatchAutoDeploy(false)
    setActiveBatchId(null)
  }, [])

  const filteredTools = useMemo(() => {
    if (!tools) return []
    let result = tools

    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      result = result.filter(
        (t) =>
          t.blueprint.tool_name.toLowerCase().includes(q) ||
          t.blueprint.tool_description.toLowerCase().includes(q) ||
          t.tags.some((tag) => tag.toLowerCase().includes(q))
      )
    }

    const sorted = [...result]
    switch (sortBy) {
      case 'created':
        sorted.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
        break
      case 'last_run':
        sorted.sort((a, b) => {
          if (!a.last_run_at) return 1
          if (!b.last_run_at) return -1
          return new Date(b.last_run_at).getTime() - new Date(a.last_run_at).getTime()
        })
        break
      case 'name':
        sorted.sort((a, b) => a.blueprint.tool_name.localeCompare(b.blueprint.tool_name))
        break
    }

    return sorted
  }, [tools, searchQuery, sortBy])

  const handleThemeSelected = async (theme: TFThemeConfig | null) => {
    if (!theme || !selectedToolId) return
    await swapTheme.mutateAsync({ toolId: selectedToolId, themeId: theme.theme_id })
    setShowThemePicker(false)
  }

  // Detail view
  if (selectedToolId) {
    return (
      <div className="h-screen flex flex-col bg-background">
        <div className="flex items-center h-10 px-3 border-b border-border bg-card shrink-0">
          <nav className="flex items-center gap-1 text-sm">
            <Button
              variant="ghost"
              size="sm"
              className="gap-1.5 text-muted-foreground hover:text-foreground h-7 px-2"
              onClick={() => { window.location.hash = '' }}
            >
              <ArrowLeft size={14} />
              <span className="text-xs">AutoForge</span>
            </Button>
            <ChevronRight size={12} className="text-muted-foreground" />
            <Button
              variant="ghost"
              size="sm"
              className="text-muted-foreground hover:text-foreground h-7 px-2"
              onClick={() => setSelectedToolId(null)}
            >
              <span className="text-xs">Tools</span>
            </Button>
            <ChevronRight size={12} className="text-muted-foreground" />
            <span className="text-xs font-semibold text-foreground">Tool Detail</span>
          </nav>
        </div>
        <main className="flex-1 overflow-auto p-6">
          <div className="max-w-4xl mx-auto">
            <ToolDetailView
              toolId={selectedToolId}
              onBack={() => setSelectedToolId(null)}
              onOpenThemePicker={() => setShowThemePicker(true)}
            />
          </div>
        </main>

        {showThemePicker && (
          <ThemePicker
            isOpen={showThemePicker}
            onSelect={handleThemeSelected}
            onClose={() => setShowThemePicker(false)}
          />
        )}
      </div>
    )
  }

  // List view
  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Breadcrumb */}
      <div className="flex items-center h-10 px-3 border-b border-border bg-card shrink-0">
        <nav className="flex items-center gap-1 text-sm">
          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5 text-muted-foreground hover:text-foreground h-7 px-2"
            onClick={() => { window.location.hash = '' }}
          >
            <ArrowLeft size={14} />
            <span className="text-xs">AutoForge</span>
          </Button>
          <ChevronRight size={12} className="text-muted-foreground" />
          <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
            <Wrench size={12} />
            YT Lab Tools
          </span>
        </nav>
      </div>

      <main className="flex-1 overflow-auto p-6">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Page header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-foreground">YT Lab Tools</h1>
              {stats && (
                <p className="text-sm text-muted-foreground mt-1">
                  {stats.total_tools} tools &middot; {stats.active_tools} active &middot; {stats.total_runs} total runs
                </p>
              )}
            </div>
            <div className="flex items-center gap-2">
              <div className="flex border border-border rounded-lg overflow-hidden">
                <button
                  onClick={() => setActiveTab('tools')}
                  className={`px-3 py-1.5 text-xs font-medium flex items-center gap-1.5 transition-colors ${
                    activeTab === 'tools'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-card text-muted-foreground hover:text-foreground'
                  }`}
                >
                  <Wrench size={12} />
                  Tools
                </button>
                <button
                  onClick={() => setActiveTab('analytics')}
                  className={`px-3 py-1.5 text-xs font-medium flex items-center gap-1.5 transition-colors ${
                    activeTab === 'analytics'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-card text-muted-foreground hover:text-foreground'
                  }`}
                >
                  <BarChart3 size={12} />
                  Analytics
                </button>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowGuide(prev => !prev)}
                title="User Guide"
                className="h-8 w-8 p-0"
              >
                <BookOpen size={14} />
              </Button>
              <Button
                variant="outline"
                className="gap-1.5"
                onClick={() => setShowBatchModal(true)}
                disabled={ytLabProjects.length === 0}
                title={ytLabProjects.length === 0 ? 'No YT Lab projects with steps found' : 'Batch generate tools from multiple YT Lab projects'}
              >
                <Layers size={14} />
                Batch Generate
              </Button>
              <Button
                className="gap-1.5"
                onClick={() => { window.location.hash = '#/yt-lab' }}
              >
                <Plus size={14} />
                New Tool (YT Lab)
              </Button>
            </div>
          </div>

          {/* Analytics tab */}
          {activeTab === 'analytics' ? (
            <AnalyticsDashboard />
          ) : (
            <>
              {/* Filters */}
              <div className="flex flex-wrap items-center gap-3">
                {/* Status filter chips */}
                <div className="flex gap-1">
                  {STATUS_FILTERS.map((f) => (
                    <button
                      key={f.value}
                      onClick={() => setStatusFilter(f.value)}
                      className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                        statusFilter === f.value
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted text-muted-foreground hover:text-foreground'
                      }`}
                    >
                      {f.label}
                    </button>
                  ))}
                </div>

                {/* Search */}
                <div className="relative flex-1 min-w-[200px] max-w-sm">
                  <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search tools..."
                    className="pl-9 h-8"
                  />
                </div>

                {/* Sort */}
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as SortOption)}
                  className="h-8 px-2 rounded-md border border-input bg-background text-sm"
                >
                  <option value="created">Newest</option>
                  <option value="last_run">Last Run</option>
                  <option value="name">Name</option>
                </select>
              </div>

              {/* Tool grid */}
              {isLoading ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Array.from({ length: 6 }).map((_, i) => (
                    <div key={i} className="animate-pulse bg-muted rounded-lg h-32" />
                  ))}
                </div>
              ) : filteredTools.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
                  <Wrench size={32} className="mb-3 opacity-50" />
                  <p className="text-sm font-medium">No tools found</p>
                  <p className="text-xs mt-1">
                    {searchQuery ? 'Try a different search' : 'Generate your first tool from YT Strategy Lab'}
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {filteredTools.map((tool) => (
                    <ToolCard
                      key={tool.tool_id}
                      tool={tool}
                      onClick={() => setSelectedToolId(tool.tool_id)}
                    />
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      </main>

      {showGuide && <ToolFactoryGuidePanel onClose={() => setShowGuide(false)} />}

      {/* Batch Generate Modal */}
      <Dialog open={showBatchModal} onOpenChange={(open) => { if (!open) handleCloseBatchModal() }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Batch Generate Tools</DialogTitle>
            <DialogDescription>
              Select YT Lab projects to generate tools from in bulk.
            </DialogDescription>
          </DialogHeader>

          {!activeBatchId ? (
            <>
              {/* Project selection view */}
              <div className="space-y-3 max-h-[400px] overflow-y-auto">
                {ytLabProjects.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-8">
                    No YT Lab projects with steps found. Create projects in YT Strategy Lab first.
                  </p>
                ) : (
                  ytLabProjects.map((project) => (
                    <label
                      key={project.id}
                      className="flex items-center gap-3 p-3 rounded-lg border border-border hover:bg-muted/50 cursor-pointer transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={batchSelectedIds.has(project.id)}
                        onChange={() => handleToggleBatchProject(project.id)}
                        className="w-4 h-4 rounded border-border"
                      />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{project.name}</p>
                        {project.description && (
                          <p className="text-xs text-muted-foreground truncate">{project.description}</p>
                        )}
                      </div>
                    </label>
                  ))
                )}
              </div>

              {/* Auto-deploy toggle */}
              <label className="flex items-center gap-2 pt-2">
                <input
                  type="checkbox"
                  checked={batchAutoDeploy}
                  onChange={(e) => setBatchAutoDeploy(e.target.checked)}
                  className="w-4 h-4 rounded border-border"
                />
                <span className="text-sm">Auto-deploy to Google Sheets</span>
              </label>

              <DialogFooter>
                <Button variant="outline" onClick={handleCloseBatchModal}>
                  Cancel
                </Button>
                <Button
                  onClick={handleStartBatch}
                  disabled={batchSelectedIds.size === 0 || startBatch.isPending}
                  className="gap-1.5"
                >
                  {startBatch.isPending ? (
                    <Loader2 size={14} className="animate-spin" />
                  ) : (
                    <Layers size={14} />
                  )}
                  Start Batch ({batchSelectedIds.size})
                </Button>
              </DialogFooter>
            </>
          ) : (
            <>
              {/* Progress view */}
              <div className="space-y-4">
                {/* Progress bar */}
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">
                      {batchStatus?.status === 'completed' ? 'Completed' : 'Generating...'}
                    </span>
                    <span className="font-medium">
                      {batchStatus ? `${batchStatus.completed + batchStatus.failed}/${batchStatus.total}` : '0/0'}
                    </span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full transition-all duration-300"
                      style={{
                        width: batchStatus
                          ? `${((batchStatus.completed + batchStatus.failed) / Math.max(batchStatus.total, 1)) * 100}%`
                          : '0%',
                      }}
                    />
                  </div>
                </div>

                {/* Per-tool results */}
                <div className="space-y-2 max-h-[300px] overflow-y-auto">
                  {batchStatus?.results.map((result, i) => (
                    <div key={i} className="flex items-center gap-2 p-2 rounded-lg border border-border">
                      {result.status === 'success' ? (
                        <CheckCircle2 size={16} className="text-green-500 shrink-0" />
                      ) : result.status === 'error' ? (
                        <AlertCircle size={16} className="text-red-500 shrink-0" />
                      ) : (
                        <Circle size={16} className="text-muted-foreground shrink-0" />
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{result.tool_name}</p>
                        {result.error && (
                          <p className="text-xs text-red-500 truncate">{result.error}</p>
                        )}
                      </div>
                      <span className="text-xs text-muted-foreground shrink-0">
                        {result.duration_seconds > 0 ? `${result.duration_seconds.toFixed(1)}s` : ''}
                      </span>
                    </div>
                  ))}

                  {/* Current tool being processed */}
                  {batchStatus?.current_tool && batchStatus.status === 'running' && (
                    <div className="flex items-center gap-2 p-2 rounded-lg border border-border bg-muted/30">
                      <Loader2 size={16} className="animate-spin text-primary shrink-0" />
                      <p className="text-sm text-muted-foreground truncate">{batchStatus.current_tool}</p>
                    </div>
                  )}
                </div>
              </div>

              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={handleCloseBatchModal}
                >
                  {batchStatus?.status === 'completed' ? 'Close' : 'Close'}
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
