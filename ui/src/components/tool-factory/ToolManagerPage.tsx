/**
 * Tool Manager page -- grid of tools with filtering, search, sort.
 * Route: /#/tools
 */

import { useState, useMemo } from 'react'
import { ArrowLeft, ChevronRight, Search, Wrench, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ToolCard } from './ToolCard'
import { ToolDetailView } from './ToolDetailView'
import { ThemePicker } from './ThemePicker'
import { useTools, useToolStats } from '@/hooks/useToolFactory'
import { useSwapTheme } from '@/hooks/useToolThemes'
import type { TFToolStatus, TFThemeConfig } from '@/lib/types'

type SortOption = 'created' | 'last_run' | 'name'

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

  const { data: tools, isLoading } = useTools(statusFilter === 'all' ? undefined : statusFilter)
  const { data: stats } = useToolStats()
  const swapTheme = useSwapTheme()

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
            Tool Manager
          </span>
        </nav>
      </div>

      <main className="flex-1 overflow-auto p-6">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Page header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-foreground">Tool Manager</h1>
              {stats && (
                <p className="text-sm text-muted-foreground mt-1">
                  {stats.total_tools} tools &middot; {stats.active_tools} active &middot; {stats.total_runs} total runs
                </p>
              )}
            </div>
            <Button
              className="gap-1.5"
              onClick={() => { window.location.hash = '#/yt-lab' }}
            >
              <Plus size={14} />
              New Tool
            </Button>
          </div>

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
        </div>
      </main>
    </div>
  )
}
