/**
 * ComponentDashboardPage — global view of all execution components and their status.
 *
 * Shows availability status, coverage percentage, and allows refreshing detection.
 */

import { useState, useEffect, useCallback } from 'react'
import {
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  RefreshCw,
  Loader2,
  Shield,
  Cpu,
  Globe,
  Terminal,
  Mail,
  FileOutput,
  Monitor,
  Search,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ComponentDef {
  name: string
  component_type: string
  description: string
  handles: string[]
  requirements: string[]
  status: 'available' | 'not_built' | 'available_if_configured'
  status_detail: string
}

interface CoverageStats {
  total_components: number
  available: number
  available_if_configured: number
  not_built: number
  coverage_pct: number
  available_names: string[]
  configurable_names: string[]
  not_built_names: string[]
}

// ---------------------------------------------------------------------------
// Icon mapping
// ---------------------------------------------------------------------------

function componentIcon(type: string) {
  switch (type) {
    case 'api': return <Cpu size={16} />
    case 'browser': return <Globe size={16} />
    case 'output': return <FileOutput size={16} />
    case 'execution': return <Terminal size={16} />
    case 'communication': return <Mail size={16} />
    default: return <Monitor size={16} />
  }
}

function statusBadge(status: string) {
  switch (status) {
    case 'available':
      return (
        <Badge className="bg-green-500/10 text-green-700 border-green-500/30 text-xs gap-1">
          <CheckCircle2 size={10} /> Available
        </Badge>
      )
    case 'available_if_configured':
      return (
        <Badge className="bg-yellow-500/10 text-yellow-700 border-yellow-500/30 text-xs gap-1">
          <AlertTriangle size={10} /> Needs Config
        </Badge>
      )
    case 'not_built':
      return (
        <Badge className="bg-red-500/10 text-red-700 border-red-500/30 text-xs gap-1">
          <XCircle size={10} /> Not Built
        </Badge>
      )
    default:
      return <Badge variant="outline" className="text-xs">{status}</Badge>
  }
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function ComponentDashboardPage() {
  const [components, setComponents] = useState<ComponentDef[]>([])
  const [coverage, setCoverage] = useState<CoverageStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const fetchData = useCallback(async () => {
    try {
      const [compRes, covRes] = await Promise.all([
        fetch('/api/tool-analyzer/components'),
        fetch('/api/tool-analyzer/coverage'),
      ])
      if (compRes.ok) {
        const data = await compRes.json()
        setComponents(data.components || [])
      }
      if (covRes.ok) {
        setCoverage(await covRes.json())
      }
    } catch {
      // Silently fail — page shows empty state
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  const handleRefresh = useCallback(async () => {
    setRefreshing(true)
    try {
      await fetch('/api/tool-analyzer/refresh', { method: 'POST' })
      await fetchData()
    } finally {
      setRefreshing(false)
    }
  }, [fetchData])

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 size={24} className="animate-spin text-muted-foreground" />
      </div>
    )
  }

  const coveragePct = coverage?.coverage_pct ?? 0
  const coverageColor = coveragePct >= 80 ? 'text-green-600' : coveragePct >= 50 ? 'text-yellow-600' : 'text-red-600'

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b border-border bg-card">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => { window.location.hash = '#/yt-lab' }}
              className="p-1.5 text-muted-foreground hover:text-foreground rounded-md hover:bg-muted/50 transition-colors"
            >
              <ArrowLeft size={18} />
            </button>
            <div>
              <h1 className="text-lg font-semibold text-foreground flex items-center gap-2">
                <Shield size={18} />
                Component Dashboard
              </h1>
              <p className="text-xs text-muted-foreground">
                Execution capabilities for tool generation
              </p>
            </div>
          </div>
          <Button
            size="sm"
            variant="outline"
            className="gap-1.5"
            onClick={handleRefresh}
            disabled={refreshing}
          >
            {refreshing ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
            Refresh
          </Button>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-6 py-6 space-y-6">
        {/* Coverage overview */}
        {coverage && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4 text-center">
                <p className={`text-2xl font-bold ${coverageColor}`}>{coveragePct}%</p>
                <p className="text-xs text-muted-foreground">Coverage</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <p className="text-2xl font-bold text-green-600">{coverage.available}</p>
                <p className="text-xs text-muted-foreground">Available</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <p className="text-2xl font-bold text-yellow-600">{coverage.available_if_configured}</p>
                <p className="text-xs text-muted-foreground">Needs Config</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <p className="text-2xl font-bold text-red-600">{coverage.not_built}</p>
                <p className="text-xs text-muted-foreground">Not Built</p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Component list */}
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-foreground flex items-center gap-1.5">
            <Search size={14} />
            All Components ({components.length})
          </h2>

          <div className="grid gap-3 sm:grid-cols-2">
            {components.map((comp) => (
              <Card key={comp.name} className="overflow-hidden">
                <CardContent className="p-4 space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground">{componentIcon(comp.component_type)}</span>
                      <span className="text-sm font-semibold text-foreground">{comp.name}</span>
                    </div>
                    {statusBadge(comp.status)}
                  </div>
                  <p className="text-xs text-muted-foreground">{comp.description}</p>
                  <p className="text-[10px] text-muted-foreground/70">{comp.status_detail}</p>
                  {comp.requirements.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {comp.requirements.map((r) => (
                        <Badge key={r} variant="outline" className="text-[10px]">
                          {r}
                        </Badge>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
