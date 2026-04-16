import { useState, useCallback, useMemo } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import {
  Search,
  ArrowLeft,
  Copy,
  Trash2,
  Download,
  Star,
  MessageSquare,
  TrendingUp,
  AlertTriangle,
  Heart,
  ThumbsUp,
  Loader2,
  Link,
  Globe,
  ChevronDown,
  ExternalLink,
  Zap,
  FolderPlus,
  Play,
  Check,
  Plus,
  ChevronLeft,
  BookOpen,
  Target,
  ShieldCheck,
  Workflow,
  GraduationCap,
} from 'lucide-react'
import {
  useScrapes,
  useScrape,
  useScrapeThread,
  useDeleteScrape,
  useSearchOptions,
  useSearchAndScrape,
  usePhraseFrequency,
  useAngleTypes,
  useResearchProjects,
  useResearchProject,
  useCreateProject,
  useDeleteProject,
  useRunAngle,
  useRunAllAngles,
} from '@/hooks/useMarketScraper'
import { exportScrape } from '@/lib/api'
import type { MarketScrape, MarketScrapeDetail, MarketPhrase, MarketSearchOptions, MarketSearchResult, MarketTopPhrase, ResearchProject, ProjectAngle, AngleTypeInfo } from '@/lib/types'

/** Category display configuration: label, Tailwind classes, and icon */
const CATEGORY_CONFIG: Record<string, { label: string; color: string; bg: string; icon: typeof AlertTriangle }> = {
  pain_point: { label: 'Pain Point', color: 'text-white', bg: 'bg-[#ef4444]', icon: AlertTriangle },
  desire: { label: 'Desire', color: 'text-white', bg: 'bg-[#3b82f6]', icon: Heart },
  feature_request: { label: 'Feature Request', color: 'text-black', bg: 'bg-[#f59e0b]', icon: MessageSquare },
  validation: { label: 'Validation', color: 'text-white', bg: 'bg-[#22c55e]', icon: ThumbsUp },
  social_proof: { label: 'Social Proof', color: 'text-white', bg: 'bg-[#a855f7]', icon: Star },
}

const FILTER_TABS = [
  { key: 'all', label: 'All' },
  { key: 'pain_point', label: 'Pain Points' },
  { key: 'desire', label: 'Desires' },
  { key: 'feature_request', label: 'Feature Requests' },
  { key: 'validation', label: 'Validation' },
  { key: 'social_proof', label: 'Social Proof' },
]

type SortMode = 'score' | 'validation' | 'recent'
type InputMode = 'url' | 'topic'
type ResultsView = 'phrases' | 'top-phrases'
type PageView = 'scraper' | 'projects' | 'project-detail' | 'project-create'

/** Angle type display config: color, icon */
const ANGLE_TYPE_CONFIG: Record<string, { color: string; bg: string; icon: typeof Target }> = {
  discovery: { color: 'text-white', bg: 'bg-[#3b82f6]', icon: Search },
  desire: { color: 'text-white', bg: 'bg-[#8b5cf6]', icon: Heart },
  pain_point: { color: 'text-white', bg: 'bg-[#ef4444]', icon: AlertTriangle },
  validation: { color: 'text-white', bg: 'bg-[#22c55e]', icon: ShieldCheck },
  workflow: { color: 'text-black', bg: 'bg-[#f59e0b]', icon: Workflow },
  education: { color: 'text-white', bg: 'bg-[#06b6d4]', icon: GraduationCap },
}

/** Status badge styling */
const STATUS_BADGE: Record<string, { label: string; className: string }> = {
  draft: { label: 'Draft', className: 'bg-gray-200 text-gray-700 border-gray-400' },
  running: { label: 'Running', className: 'bg-[#06b6d4]/20 text-[#06b6d4] border-[#06b6d4] animate-pulse' },
  complete: { label: 'Complete', className: 'bg-[#22c55e]/20 text-[#22c55e] border-[#22c55e]' },
  pending: { label: 'Pending', className: 'bg-gray-200 text-gray-700 border-gray-400' },
  error: { label: 'Error', className: 'bg-[#ef4444]/20 text-[#ef4444] border-[#ef4444]' },
}

export function MarketScraperPage() {
  // Top-level page view
  const [pageView, setPageView] = useState<PageView>('scraper')
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null)

  // Input mode
  const [inputMode, setInputMode] = useState<InputMode>('topic')

  // URL mode state
  const [url, setUrl] = useState('')

  // Topic mode state
  const [topicQuery, setTopicQuery] = useState('')
  const [selectedSubs, setSelectedSubs] = useState<string[]>([])
  const [topicSort, setTopicSort] = useState('relevance')
  const [topicTime, setTopicTime] = useState('week')
  const [maxThreads, setMaxThreads] = useState(5)
  const [searchType, setSearchType] = useState('link')
  const [includeNsfw, setIncludeNsfw] = useState(false)
  const [minComments, setMinComments] = useState(2)
  const [maxCommentsPerPost, setMaxCommentsPerPost] = useState(0)
  const [skipComments, setSkipComments] = useState(false)
  const [showSubPicker, setShowSubPicker] = useState(false)
  const [searchResult, setSearchResult] = useState<{
    query: string
    threads_found: number
    threads_scraped: number
    scrape_ids: number[]
    total_phrases: number
    category_counts: Record<string, number>
  } | null>(null)

  // Shared state
  const [activeScrapeId, setActiveScrapeId] = useState<number | null>(null)
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [sortMode, setSortMode] = useState<SortMode>('validation')
  const [resultsView, setResultsView] = useState<ResultsView>('phrases')
  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null)

  const { data: scrapesRaw } = useScrapes()
  const { data: activeScrapeRaw } = useScrape(activeScrapeId)
  const scrapes = scrapesRaw as MarketScrape[] | undefined
  const activeScrapeData = activeScrapeRaw as MarketScrapeDetail | undefined
  const scrapeThread = useScrapeThread()
  const deleteScrape = useDeleteScrape()
  const { data: searchOptions } = useSearchOptions()
  const searchAndScrape = useSearchAndScrape()
  const { data: phraseFreqData } = usePhraseFrequency(
    activeScrapeId ? { scrape_ids: [activeScrapeId], top_n: 50 } : { top_n: 50 }
  )

  // Research Project hooks
  const { data: angleTypesData } = useAngleTypes()
  const { data: projectsRaw } = useResearchProjects()
  const { data: selectedProjectRaw, refetch: refetchProject } = useResearchProject(selectedProjectId)
  const createProject = useCreateProject()
  const deleteProject = useDeleteProject()
  const runAngle = useRunAngle()
  const runAllAngles = useRunAllAngles()

  const projects = projectsRaw as ResearchProject[] | undefined
  const selectedProject = selectedProjectRaw as ResearchProject | undefined
  const angleTypes = angleTypesData?.angle_types as Record<string, AngleTypeInfo> | undefined

  // Project create wizard state
  const [wizardName, setWizardName] = useState('')
  const [wizardNiche, setWizardNiche] = useState('')
  const [wizardDescription, setWizardDescription] = useState('')
  const [wizardAngles, setWizardAngles] = useState<Record<string, { selected: boolean; keywords: string }>>({})

  // Initialize wizard angles when angle types load
  const angleTypeKeys = useMemo(() => Object.keys(angleTypes ?? {}), [angleTypes])

  const resetWizard = useCallback(() => {
    setWizardName('')
    setWizardNiche('')
    setWizardDescription('')
    setWizardAngles({})
  }, [])

  const showToast = useCallback((type: 'success' | 'error', message: string) => {
    setToast({ type, message })
    setTimeout(() => setToast(null), 3000)
  }, [])

  const handleCreateProject = useCallback(() => {
    if (!wizardName.trim() || !wizardNiche.trim()) return
    const selectedAngles = Object.entries(wizardAngles)
      .filter(([, v]) => v.selected)
      .map(([type, v]) => ({
        type,
        custom_keywords: v.keywords.trim() || undefined,
      }))
    createProject.mutate(
      {
        name: wizardName.trim(),
        niche: wizardNiche.trim(),
        description: wizardDescription.trim() || undefined,
        angles: selectedAngles.length > 0 ? selectedAngles : undefined,
      },
      {
        onSuccess: (proj) => {
          const created = proj as ResearchProject
          showToast('success', `Project "${created.name}" created`)
          resetWizard()
          setSelectedProjectId(created.id)
          setPageView('project-detail')
        },
        onError: (err: Error) => showToast('error', err.message || 'Failed to create project'),
      },
    )
  }, [wizardName, wizardNiche, wizardDescription, wizardAngles, createProject, showToast, resetWizard])

  const handleDeleteProject = useCallback((id: number) => {
    deleteProject.mutate(id, {
      onSuccess: () => {
        showToast('success', 'Project deleted')
        if (selectedProjectId === id) {
          setSelectedProjectId(null)
          setPageView('projects')
        }
      },
      onError: (err: Error) => showToast('error', err.message || 'Failed to delete'),
    })
  }, [deleteProject, selectedProjectId, showToast])

  const handleRunAngle = useCallback((angleId: number) => {
    runAngle.mutate(
      { angleId },
      {
        onSuccess: (result) => {
          showToast('success', `Angle complete: ${result.total_phrases} phrases from ${result.queries_run} queries`)
          refetchProject()
        },
        onError: (err: Error) => showToast('error', err.message || 'Failed to run angle'),
      },
    )
  }, [runAngle, showToast, refetchProject])

  const handleRunAll = useCallback((projectId: number) => {
    runAllAngles.mutate(
      { projectId },
      {
        onSuccess: () => {
          showToast('success', 'All angles complete')
          refetchProject()
        },
        onError: (err: Error) => showToast('error', err.message || 'Failed to run all angles'),
      },
    )
  }, [runAllAngles, showToast, refetchProject])

  const opts = searchOptions as MarketSearchOptions | undefined
  const defaultSubs: string[] = opts?.default_subreddits ?? []
  const sortOptions: string[] = opts?.sort_options ?? ['relevance', 'hot', 'top', 'new', 'comments']
  const timeFilters: string[] = opts?.time_filters ?? ['all', 'year', 'month', 'week', 'day', 'hour']

  // URL scrape handler
  const handleScrape = useCallback(() => {
    if (!url.trim()) return
    scrapeThread.mutate(url.trim(), {
      onSuccess: (raw) => {
        const data = raw as MarketScrapeDetail
        showToast('success', `Scraped ${data.total_phrases} phrases from r/${data.subreddit}`)
        setActiveScrapeId(data.id)
        setUrl('')
      },
      onError: (err: Error) => {
        showToast('error', err.message || 'Failed to scrape thread')
      },
    })
  }, [url, scrapeThread, showToast])

  // Topic search + scrape handler
  const handleTopicSearch = useCallback(() => {
    if (!topicQuery.trim()) return
    searchAndScrape.mutate(
      {
        query: topicQuery.trim(),
        subreddits: selectedSubs.length > 0 ? selectedSubs : undefined,
        sort: topicSort,
        time_filter: topicTime,
        max_threads: maxThreads,
        search_type: searchType,
        include_nsfw: includeNsfw,
        min_comments: minComments,
        max_comments_per_post: maxCommentsPerPost,
        skip_comments: skipComments,
      },
      {
        onSuccess: (raw) => {
          const data = raw as MarketSearchResult
          setSearchResult(data)
          if (data.scrape_ids?.length > 0) {
            setActiveScrapeId(data.scrape_ids[0])
            showToast(
              'success',
              `Found ${data.threads_found} threads, scraped ${data.threads_scraped}, got ${data.total_phrases} phrases`
            )
          } else {
            showToast('error', 'No matching threads found — try different keywords or subreddits')
          }
        },
        onError: (err: Error) => {
          showToast('error', err.message || 'Search failed')
        },
      }
    )
  }, [topicQuery, selectedSubs, topicSort, topicTime, maxThreads, searchType, includeNsfw, minComments, maxCommentsPerPost, skipComments, searchAndScrape, showToast])

  const handleDelete = useCallback((id: number) => {
    deleteScrape.mutate(id, {
      onSuccess: () => {
        showToast('success', 'Scrape deleted')
        if (activeScrapeId === id) setActiveScrapeId(null)
        setDeleteConfirmId(null)
      },
      onError: (err: Error) => {
        showToast('error', err.message || 'Failed to delete')
        setDeleteConfirmId(null)
      },
    })
  }, [deleteScrape, activeScrapeId, showToast])

  const handleExport = useCallback(async (id: number) => {
    try {
      const blob = await exportScrape(id)
      const downloadUrl = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = downloadUrl
      a.download = `scrape-${id}.csv`
      a.click()
      URL.revokeObjectURL(downloadUrl)
    } catch {
      showToast('error', 'Failed to export CSV')
    }
  }, [showToast])

  const copyToClipboard = useCallback((text: string, label: string) => {
    navigator.clipboard.writeText(text).then(() => {
      showToast('success', `${label} copied to clipboard`)
    })
  }, [showToast])

  const toggleSub = useCallback((sub: string) => {
    setSelectedSubs(prev =>
      prev.includes(sub) ? prev.filter(s => s !== sub) : [...prev, sub]
    )
  }, [])

  // Derive filtered + sorted phrases from the active scrape
  const phrases: MarketPhrase[] = activeScrapeData?.phrases ?? []
  const filteredPhrases = phrases
    .filter((p: MarketPhrase) => categoryFilter === 'all' || p.category === categoryFilter)
    .sort((a: MarketPhrase, b: MarketPhrase) => {
      if (sortMode === 'score') return b.score - a.score
      if (sortMode === 'validation') return b.validation_signal - a.validation_signal
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    })

  // Summary counts by category
  const categoryCounts = phrases.reduce<Record<string, number>>((acc, p: MarketPhrase) => {
    acc[p.category] = (acc[p.category] || 0) + 1
    return acc
  }, {})

  const isLoading = scrapeThread.isPending || searchAndScrape.isPending

  return (
    <div className="flex h-screen flex-col bg-background">
      {/* Header */}
      <div className="flex items-center gap-3 border-b-2 border-border px-4 py-3">
        <Button
          variant="outline"
          size="sm"
          onClick={() => { window.location.hash = '' }}
          className="border-2 border-black shadow-[2px_2px_0_0_#000]"
        >
          <ArrowLeft size={16} />
        </Button>
        <Search size={24} className="text-primary" />
        <div>
          <h1 className="text-xl font-bold tracking-tight">Market Scraper</h1>
          <p className="text-sm text-muted-foreground">
            Scrape Reddit for pain points, desires, and ad copy gold
          </p>
        </div>
        {/* Top-level nav: Scraper vs Projects */}
        <div className="ml-auto flex gap-2">
          <Button
            variant={pageView === 'scraper' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setPageView('scraper')}
            className="gap-2 border-2 border-black shadow-[2px_2px_0_0_#000]"
          >
            <Search size={16} />
            Scraper
          </Button>
          <Button
            variant={pageView !== 'scraper' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setPageView('projects')}
            className="gap-2 border-2 border-black shadow-[2px_2px_0_0_#000]"
          >
            <FolderPlus size={16} />
            Projects
          </Button>
        </div>
      </div>

      {/* Toast notification */}
      {toast && (
        <div
          className={`mx-4 mt-2 rounded border-2 border-black px-4 py-2 text-sm font-bold shadow-[3px_3px_0_0_#000] ${
            toast.type === 'success' ? 'bg-[#22c55e] text-white' : 'bg-[#ef4444] text-white'
          }`}
        >
          {toast.message}
        </div>
      )}

      {/* ========== PROJECT VIEWS ========== */}
      {pageView === 'projects' && (
        <div className="flex-1 overflow-y-auto p-4">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-bold">Research Projects</h2>
            <Button
              onClick={() => { resetWizard(); setPageView('project-create') }}
              className="gap-2 border-2 border-black bg-[#22c55e] text-white shadow-[3px_3px_0_0_#000] hover:bg-[#16a34a]"
            >
              <Plus size={16} />
              New Project
            </Button>
          </div>
          {(!projects || projects.length === 0) ? (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <FolderPlus size={48} className="mb-4 text-muted-foreground/30" />
              <h3 className="text-lg font-bold">No research projects yet</h3>
              <p className="mt-1 max-w-md text-sm text-muted-foreground">
                Create a project to organize your market research by niche. Add scrape angles to systematically gather Reddit data.
              </p>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {projects.map((proj) => {
                const statusBadge = STATUS_BADGE[proj.status] ?? STATUS_BADGE.draft
                return (
                  <Card
                    key={proj.id}
                    className="cursor-pointer border-2 border-black shadow-[4px_4px_0_0_#000] transition-all hover:shadow-[6px_6px_0_0_#000]"
                    onClick={() => { setSelectedProjectId(proj.id); setPageView('project-detail') }}
                  >
                    <CardContent className="p-4">
                      <div className="mb-2 flex items-start justify-between">
                        <h3 className="text-base font-bold">{proj.name}</h3>
                        <Badge className={`border text-[10px] ${statusBadge.className}`}>
                          {statusBadge.label}
                        </Badge>
                      </div>
                      <p className="mb-3 text-xs text-muted-foreground">{proj.niche}</p>
                      {proj.description && (
                        <p className="mb-3 line-clamp-2 text-sm text-foreground/80">{proj.description}</p>
                      )}
                      <div className="flex items-center gap-3 text-xs text-muted-foreground">
                        <span className="font-semibold">{proj.angle_count} angle{proj.angle_count !== 1 ? 's' : ''}</span>
                        <span>{proj.total_phrases} phrases</span>
                        <span className="ml-auto">{new Date(proj.created_at).toLocaleDateString()}</span>
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* ========== PROJECT CREATE WIZARD ========== */}
      {pageView === 'project-create' && (
        <div className="flex-1 overflow-y-auto p-4">
          <Button
            variant="ghost"
            size="sm"
            className="mb-4 gap-1"
            onClick={() => setPageView('projects')}
          >
            <ChevronLeft size={16} />
            Back to Projects
          </Button>
          <Card className="mx-auto max-w-2xl border-2 border-black shadow-[4px_4px_0_0_#000]">
            <CardContent className="p-6 space-y-6">
              <h2 className="text-xl font-bold">Create Research Project</h2>

              {/* Step 1: Basic info */}
              <div className="space-y-3">
                <div>
                  <label className="mb-1 block text-sm font-bold">Project Name *</label>
                  <Input
                    value={wizardName}
                    onChange={(e) => setWizardName(e.target.value)}
                    placeholder='e.g., "AI Coding Tools Research"'
                    className="border-2 border-black"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-bold">Niche *</label>
                  <Input
                    value={wizardNiche}
                    onChange={(e) => setWizardNiche(e.target.value)}
                    placeholder='e.g., "AI-powered code editors"'
                    className="border-2 border-black"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-bold">Description (optional)</label>
                  <textarea
                    value={wizardDescription}
                    onChange={(e) => setWizardDescription(e.target.value)}
                    placeholder="Brief notes about what you want to learn..."
                    className="w-full rounded border-2 border-black bg-background px-3 py-2 text-sm"
                    rows={3}
                  />
                </div>
              </div>

              {/* Step 2: Angle selection */}
              <div>
                <h3 className="mb-2 text-sm font-bold">Scrape Angles</h3>
                <p className="mb-3 text-xs text-muted-foreground">
                  Select the research angles you want to explore. Each angle generates targeted search queries.
                </p>
                <div className="space-y-3">
                  {angleTypeKeys.map((key) => {
                    const info = angleTypes?.[key]
                    const config = ANGLE_TYPE_CONFIG[key]
                    const Icon = config?.icon ?? Target
                    const isSelected = wizardAngles[key]?.selected ?? false
                    return (
                      <div
                        key={key}
                        className={`rounded border-2 border-black p-3 transition-all ${
                          isSelected
                            ? `${config?.bg ?? 'bg-primary'}/10 shadow-[3px_3px_0_0_#000]`
                            : 'bg-card hover:bg-accent/50'
                        }`}
                      >
                        <label className="flex cursor-pointer items-start gap-3">
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() =>
                              setWizardAngles((prev) => ({
                                ...prev,
                                [key]: { selected: !isSelected, keywords: prev[key]?.keywords ?? '' },
                              }))
                            }
                            className="mt-1 h-4 w-4 accent-black"
                          />
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <Icon size={16} className={config?.color ?? ''} />
                              <span className="text-sm font-bold">{info?.label ?? key}</span>
                            </div>
                            <p className="mt-0.5 text-xs text-muted-foreground">{info?.description ?? ''}</p>
                            {isSelected && (
                              <Input
                                value={wizardAngles[key]?.keywords ?? ''}
                                onChange={(e) =>
                                  setWizardAngles((prev) => ({
                                    ...prev,
                                    [key]: { ...prev[key], keywords: e.target.value },
                                  }))
                                }
                                placeholder="Custom keywords (optional)"
                                className="mt-2 border-2 border-black text-xs"
                                onClick={(e) => e.stopPropagation()}
                              />
                            )}
                          </div>
                        </label>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Create button */}
              <Button
                onClick={handleCreateProject}
                disabled={!wizardName.trim() || !wizardNiche.trim() || createProject.isPending}
                className="w-full border-2 border-black bg-[#22c55e] text-white shadow-[3px_3px_0_0_#000] hover:bg-[#16a34a]"
              >
                {createProject.isPending ? (
                  <>
                    <Loader2 size={16} className="mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <FolderPlus size={16} className="mr-2" />
                    Create Project
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      {/* ========== PROJECT DETAIL VIEW ========== */}
      {pageView === 'project-detail' && selectedProject && (
        <div className="flex-1 overflow-y-auto p-4">
          <div className="mb-4 flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              className="gap-1"
              onClick={() => { setSelectedProjectId(null); setPageView('projects') }}
            >
              <ChevronLeft size={16} />
              Back to Projects
            </Button>
          </div>

          {/* Project header */}
          <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
            <div>
              <div className="flex items-center gap-3">
                <h2 className="text-xl font-bold">{selectedProject.name}</h2>
                <Badge className={`border text-xs ${(STATUS_BADGE[selectedProject.status] ?? STATUS_BADGE.draft).className}`}>
                  {(STATUS_BADGE[selectedProject.status] ?? STATUS_BADGE.draft).label}
                </Badge>
              </div>
              <p className="mt-1 text-sm text-muted-foreground">{selectedProject.niche}</p>
              {selectedProject.description && (
                <p className="mt-1 text-sm text-foreground/80">{selectedProject.description}</p>
              )}
            </div>
            <div className="flex gap-2">
              <Button
                onClick={() => handleRunAll(selectedProject.id)}
                disabled={runAllAngles.isPending || !selectedProject.angles?.length}
                className="gap-2 border-2 border-black bg-[#22c55e] text-white shadow-[3px_3px_0_0_#000] hover:bg-[#16a34a]"
              >
                {runAllAngles.isPending ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : (
                  <Play size={16} />
                )}
                Run All Angles
              </Button>
              <Button
                variant="destructive"
                size="sm"
                className="border-2 border-black shadow-[2px_2px_0_0_#000]"
                onClick={() => handleDeleteProject(selectedProject.id)}
              >
                <Trash2 size={14} />
              </Button>
            </div>
          </div>

          {/* Summary stats */}
          <div className="mb-6 grid grid-cols-3 gap-3">
            <SummaryCard
              label="Angles"
              count={selectedProject.angle_count}
              color="bg-card"
              icon={<Target size={18} />}
            />
            <SummaryCard
              label="Total Phrases"
              count={selectedProject.total_phrases}
              color="bg-card"
              icon={<MessageSquare size={18} />}
            />
            <SummaryCard
              label="Complete"
              count={selectedProject.angles?.filter((a) => a.status === 'complete').length ?? 0}
              color="bg-[#22c55e]/10"
              textColor="text-[#22c55e]"
              icon={<Check size={18} className="text-[#22c55e]" />}
            />
          </div>

          {/* Angle cards */}
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-base font-bold">Scrape Angles</h3>
          </div>

          {(!selectedProject.angles || selectedProject.angles.length === 0) ? (
            <Card className="border-2 border-black p-8 text-center shadow-[4px_4px_0_0_#000]">
              <p className="text-muted-foreground">No angles yet. Add angles to start researching.</p>
            </Card>
          ) : (
            <div className="space-y-3">
              {selectedProject.angles.map((angle) => (
                <AngleCard
                  key={angle.id}
                  angle={angle}
                  angleTypes={angleTypes}
                  onRun={handleRunAngle}
                  isRunning={runAngle.isPending}
                  onViewScrape={(scrapeId) => {
                    setActiveScrapeId(scrapeId)
                    setPageView('scraper')
                  }}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Loading state for project detail */}
      {pageView === 'project-detail' && !selectedProject && selectedProjectId !== null && (
        <div className="flex flex-1 items-center justify-center">
          <Loader2 size={32} className="animate-spin text-muted-foreground" />
        </div>
      )}

      {/* ========== SCRAPER VIEW (original) ========== */}
      {pageView === 'scraper' && (
      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar — Past Scrapes */}
        <aside className="w-64 flex-shrink-0 overflow-y-auto border-r-2 border-border bg-card p-3">
          <h2 className="mb-3 text-sm font-bold uppercase tracking-wider text-muted-foreground">
            Past Scrapes
          </h2>
          {(!scrapes || scrapes.length === 0) ? (
            <p className="text-xs text-muted-foreground italic">
              No scrapes yet. Search a topic or paste a URL to get started.
            </p>
          ) : (
            <div className="space-y-2">
              {scrapes.map((scrape) => (
                <div
                  key={scrape.id}
                  className={`group cursor-pointer rounded border-2 border-black p-2 transition-all hover:shadow-[3px_3px_0_0_#000] ${
                    activeScrapeId === scrape.id
                      ? 'bg-primary/10 shadow-[3px_3px_0_0_#000]'
                      : 'bg-card hover:bg-accent'
                  }`}
                  onClick={() => setActiveScrapeId(scrape.id)}
                >
                  <div className="flex items-start justify-between gap-1">
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-bold">r/{scrape.subreddit}</p>
                      <p className="truncate text-xs text-muted-foreground">{scrape.title}</p>
                      <div className="mt-1 flex items-center gap-2">
                        <Badge variant="secondary" className="text-[10px]">
                          {scrape.total_phrases} phrases
                        </Badge>
                        <span className="text-[10px] text-muted-foreground">
                          {new Date(scrape.scraped_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                    <div className="flex flex-col gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleExport(scrape.id)
                        }}
                        title="Export CSV"
                      >
                        <Download size={12} />
                      </Button>
                      {deleteConfirmId === scrape.id ? (
                        <Button
                          variant="destructive"
                          size="sm"
                          className="h-6 w-6 p-0"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDelete(scrape.id)
                          }}
                          title="Confirm delete"
                        >
                          <Trash2 size={12} />
                        </Button>
                      ) : (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0 hover:text-destructive"
                          onClick={(e) => {
                            e.stopPropagation()
                            setDeleteConfirmId(scrape.id)
                          }}
                          title="Delete scrape"
                        >
                          <Trash2 size={12} />
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </aside>

        {/* Main Content Area */}
        <div className="flex-1 overflow-y-auto p-4">
          {/* Input Mode Tabs */}
          <div className="mb-4 flex gap-2">
            <Button
              variant={inputMode === 'topic' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setInputMode('topic')}
              className="gap-2 border-2 border-black shadow-[2px_2px_0_0_#000]"
            >
              <Globe size={16} />
              Topic Search
            </Button>
            <Button
              variant={inputMode === 'url' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setInputMode('url')}
              className="gap-2 border-2 border-black shadow-[2px_2px_0_0_#000]"
            >
              <Link size={16} />
              URL Scrape
            </Button>
          </div>

          {/* Topic Search Mode */}
          {inputMode === 'topic' && (
            <Card className="mb-6 border-2 border-black shadow-[4px_4px_0_0_#000]">
              <CardContent className="p-4 space-y-3">
                {/* Search query input */}
                <div className="flex gap-3">
                  <Input
                    value={topicQuery}
                    onChange={(e) => setTopicQuery(e.target.value)}
                    placeholder='Search for a topic... (e.g., "app maker frustrations", "SaaS pricing complaints")'
                    className="flex-1 border-2 border-black"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleTopicSearch()
                    }}
                  />
                  <Button
                    onClick={handleTopicSearch}
                    disabled={!topicQuery.trim() || isLoading}
                    className="border-2 border-black bg-[#22c55e] text-white shadow-[3px_3px_0_0_#000] transition-all hover:bg-[#16a34a] hover:shadow-[1px_1px_0_0_#000]"
                  >
                    {searchAndScrape.isPending ? (
                      <>
                        <Loader2 size={16} className="mr-2 animate-spin" />
                        Searching...
                      </>
                    ) : (
                      <>
                        <Zap size={16} className="mr-2" />
                        Search & Scrape
                      </>
                    )}
                  </Button>
                </div>

                {/* Options row */}
                <div className="flex flex-wrap items-center gap-3">
                  {/* Subreddit picker */}
                  <div className="relative">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowSubPicker(!showSubPicker)}
                      className="gap-1 border-2 border-black text-xs"
                    >
                      <Globe size={12} />
                      {selectedSubs.length === 0
                        ? 'All of Reddit'
                        : `${selectedSubs.length} subreddit${selectedSubs.length > 1 ? 's' : ''}`}
                      <ChevronDown size={12} />
                    </Button>
                    {showSubPicker && (
                      <div className="absolute top-full left-0 z-50 mt-1 w-72 rounded border-2 border-black bg-card p-3 shadow-[4px_4px_0_0_#000]">
                        <p className="mb-2 text-xs font-bold uppercase text-muted-foreground">Pick subreddits</p>
                        <div className="flex flex-wrap gap-1.5">
                          {defaultSubs.map((sub) => (
                            <Badge
                              key={sub}
                              variant={selectedSubs.includes(sub) ? 'default' : 'outline'}
                              className={`cursor-pointer border-2 border-black text-xs transition-all ${
                                selectedSubs.includes(sub)
                                  ? 'bg-primary text-primary-foreground shadow-[2px_2px_0_0_#000]'
                                  : 'hover:bg-accent'
                              }`}
                              onClick={() => toggleSub(sub)}
                            >
                              r/{sub}
                            </Badge>
                          ))}
                        </div>
                        <div className="mt-2 flex justify-between">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-xs"
                            onClick={() => setSelectedSubs([])}
                          >
                            Clear all
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-xs"
                            onClick={() => setSelectedSubs([...defaultSubs])}
                          >
                            Select all
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Sort */}
                  <div className="flex items-center gap-1">
                    <span className="text-xs font-bold text-muted-foreground">Sort:</span>
                    <select
                      value={topicSort}
                      onChange={(e) => setTopicSort(e.target.value)}
                      className="rounded border-2 border-black bg-card px-2 py-1 text-xs"
                    >
                      {sortOptions.map((opt) => (
                        <option key={opt} value={opt}>{opt}</option>
                      ))}
                    </select>
                  </div>

                  {/* Time */}
                  <div className="flex items-center gap-1">
                    <span className="text-xs font-bold text-muted-foreground">Time:</span>
                    <select
                      value={topicTime}
                      onChange={(e) => setTopicTime(e.target.value)}
                      className="rounded border-2 border-black bg-card px-2 py-1 text-xs"
                    >
                      {timeFilters.map((opt) => (
                        <option key={opt} value={opt}>{opt}</option>
                      ))}
                    </select>
                  </div>

                  {/* Max threads */}
                  <div className="flex items-center gap-1">
                    <span className="text-xs font-bold text-muted-foreground">Threads:</span>
                    <select
                      value={maxThreads}
                      onChange={(e) => setMaxThreads(Number(e.target.value))}
                      className="rounded border-2 border-black bg-card px-2 py-1 text-xs"
                    >
                      {[3, 5, 10, 15, 20].map((n) => (
                        <option key={n} value={n}>{n}</option>
                      ))}
                    </select>
                  </div>

                  {/* Search type */}
                  <div className="flex items-center gap-1">
                    <span className="text-xs font-bold text-muted-foreground">Type:</span>
                    <select
                      value={searchType}
                      onChange={(e) => setSearchType(e.target.value)}
                      className="rounded border-2 border-black bg-card px-2 py-1 text-xs"
                    >
                      <option value="link">Posts</option>
                      <option value="comment">Comments</option>
                      <option value="sr">Communities</option>
                      <option value="user">Users</option>
                    </select>
                  </div>

                  {/* Min comments — only relevant for link/post search */}
                  {searchType === 'link' && (
                    <div className="flex items-center gap-1">
                      <span className="text-xs font-bold text-muted-foreground">Min comments:</span>
                      <input
                        type="number"
                        min={0}
                        max={1000}
                        value={minComments}
                        onChange={(e) => setMinComments(Number(e.target.value))}
                        className="w-16 rounded border-2 border-black bg-card px-2 py-1 text-xs"
                      />
                    </div>
                  )}

                  {/* Max comments per post */}
                  <div className="flex items-center gap-1">
                    <span className="text-xs font-bold text-muted-foreground">Max comments:</span>
                    <input
                      type="number"
                      min={0}
                      max={5000}
                      value={maxCommentsPerPost}
                      onChange={(e) => setMaxCommentsPerPost(Number(e.target.value))}
                      className="w-16 rounded border-2 border-black bg-card px-2 py-1 text-xs"
                      title="0 = unlimited"
                    />
                  </div>

                  {/* NSFW toggle */}
                  <label className="flex items-center gap-1 text-xs">
                    <input
                      type="checkbox"
                      checked={includeNsfw}
                      onChange={(e) => setIncludeNsfw(e.target.checked)}
                    />
                    NSFW
                  </label>

                  {/* Skip comments toggle */}
                  <label className="flex items-center gap-1 text-xs">
                    <input
                      type="checkbox"
                      checked={skipComments}
                      onChange={(e) => setSkipComments(e.target.checked)}
                    />
                    Skip comments
                  </label>
                </div>

                {/* Search result summary */}
                {searchResult && (
                  <div className="rounded border-2 border-black bg-[#22c55e]/10 p-3">
                    <div className="flex items-center gap-2 text-sm">
                      <TrendingUp size={16} className="text-[#22c55e]" />
                      <span className="font-bold">
                        Found {searchResult.threads_found} threads for &quot;{searchResult.query}&quot;
                      </span>
                      <span className="text-muted-foreground">
                        — scraped {searchResult.threads_scraped}, extracted {searchResult.total_phrases} phrases
                      </span>
                    </div>
                    {searchResult.scrape_ids.length > 1 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {searchResult.scrape_ids.map((id, i) => (
                          <Button
                            key={id}
                            variant={activeScrapeId === id ? 'default' : 'outline'}
                            size="sm"
                            className="border-2 border-black text-xs"
                            onClick={() => setActiveScrapeId(id)}
                          >
                            Thread {i + 1}
                          </Button>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* URL Scrape Mode */}
          {inputMode === 'url' && (
            <Card className="mb-6 border-2 border-black shadow-[4px_4px_0_0_#000]">
              <CardContent className="p-4">
                <div className="flex gap-3">
                  <Input
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="Paste a Reddit thread URL..."
                    className="flex-1 border-2 border-black"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleScrape()
                    }}
                  />
                  <Button
                    onClick={handleScrape}
                    disabled={!url.trim() || isLoading}
                    className="border-2 border-black shadow-[3px_3px_0_0_#000] transition-all hover:shadow-[1px_1px_0_0_#000]"
                  >
                    {scrapeThread.isPending ? (
                      <>
                        <Loader2 size={16} className="mr-2 animate-spin" />
                        Scraping...
                      </>
                    ) : (
                      <>
                        <Search size={16} className="mr-2" />
                        Scrape Thread
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Results dashboard + phrase cards (when a scrape is active) */}
          {activeScrapeId && activeScrapeData && (
            <>
              {/* Active scrape title */}
              <div className="mb-4 flex items-center gap-2">
                <h2 className="text-lg font-bold">
                  r/{activeScrapeData.subreddit}: {activeScrapeData.title}
                </h2>
                <a
                  href={activeScrapeData.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-muted-foreground hover:text-foreground"
                >
                  <ExternalLink size={14} />
                </a>
              </div>

              {/* Summary Cards */}
              <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-5">
                <SummaryCard
                  label="Total Phrases"
                  count={phrases.length}
                  color="bg-card"
                  icon={<MessageSquare size={18} />}
                />
                <SummaryCard
                  label="Pain Points"
                  count={categoryCounts.pain_point || 0}
                  color="bg-[#ef4444]/10"
                  textColor="text-[#ef4444]"
                  icon={<AlertTriangle size={18} className="text-[#ef4444]" />}
                />
                <SummaryCard
                  label="Desires"
                  count={categoryCounts.desire || 0}
                  color="bg-[#3b82f6]/10"
                  textColor="text-[#3b82f6]"
                  icon={<Heart size={18} className="text-[#3b82f6]" />}
                />
                <SummaryCard
                  label="Validation"
                  count={categoryCounts.validation || 0}
                  color="bg-[#22c55e]/10"
                  textColor="text-[#22c55e]"
                  icon={<ThumbsUp size={18} className="text-[#22c55e]" />}
                />
                <SummaryCard
                  label="Social Proof"
                  count={categoryCounts.social_proof || 0}
                  color="bg-[#a855f7]/10"
                  textColor="text-[#a855f7]"
                  icon={<Star size={18} className="text-[#a855f7]" />}
                />
              </div>

              {/* Results View Toggle */}
              <div className="mb-4 flex gap-2">
                <Button
                  variant={resultsView === 'phrases' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setResultsView('phrases')}
                  className="gap-1.5 border-2 border-black shadow-[2px_2px_0_0_#000]"
                >
                  <MessageSquare size={14} />
                  Individual Phrases
                </Button>
                <Button
                  variant={resultsView === 'top-phrases' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setResultsView('top-phrases')}
                  className="gap-1.5 border-2 border-black shadow-[2px_2px_0_0_#000]"
                >
                  <TrendingUp size={14} />
                  Top Phrases
                  {phraseFreqData?.total ? (
                    <Badge variant="secondary" className="ml-1 text-[10px]">{phraseFreqData.total}</Badge>
                  ) : null}
                </Button>
              </div>

              {/* TOP PHRASES VIEW */}
              {resultsView === 'top-phrases' && (
                <>
                  <div className="mb-3 rounded border-2 border-black bg-[#f59e0b]/10 p-3 shadow-[2px_2px_0_0_#000]">
                    <p className="text-sm font-bold">
                      These are the exact phrases people repeat most — the language your market actually speaks.
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Ranked by frequency. Copy them directly into ad copy, landing pages, and social posts.
                    </p>
                  </div>
                  {phraseFreqData?.phrases?.length ? (
                    <div className="space-y-2">
                      {phraseFreqData.phrases.map((tp: MarketTopPhrase, idx: number) => (
                        <TopPhraseRow key={tp.phrase} phrase={tp} rank={idx + 1} onCopy={copyToClipboard} />
                      ))}
                    </div>
                  ) : (
                    <Card className="border-2 border-black p-8 text-center shadow-[4px_4px_0_0_#000]">
                      <p className="text-muted-foreground">No phrase patterns found yet. Scrape more threads to build up data.</p>
                    </Card>
                  )}
                </>
              )}

              {/* INDIVIDUAL PHRASES VIEW */}
              {resultsView === 'phrases' && (
                <>
                  {/* Filter Tabs + Sort Controls */}
                  <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
                    <div className="flex flex-wrap gap-1">
                      {FILTER_TABS.map((tab) => (
                        <Button
                          key={tab.key}
                          variant={categoryFilter === tab.key ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => setCategoryFilter(tab.key)}
                          className={`border-2 border-black text-xs ${
                            categoryFilter === tab.key ? 'shadow-[2px_2px_0_0_#000]' : ''
                          }`}
                        >
                          {tab.label}
                          {tab.key !== 'all' && categoryCounts[tab.key] ? (
                            <span className="ml-1 opacity-70">({categoryCounts[tab.key]})</span>
                          ) : null}
                        </Button>
                      ))}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-muted-foreground">Sort:</span>
                      {([
                        { key: 'score' as SortMode, label: 'Score', icon: <TrendingUp size={12} /> },
                        { key: 'validation' as SortMode, label: 'Validation', icon: <Star size={12} /> },
                        { key: 'recent' as SortMode, label: 'Recent', icon: <MessageSquare size={12} /> },
                      ]).map((s) => (
                        <Button
                          key={s.key}
                          variant={sortMode === s.key ? 'default' : 'ghost'}
                          size="sm"
                          onClick={() => setSortMode(s.key)}
                          className="gap-1 text-xs"
                        >
                          {s.icon}
                          {s.label}
                        </Button>
                      ))}
                    </div>
                  </div>

                  {/* Phrase Cards */}
                  {filteredPhrases.length === 0 ? (
                    <Card className="border-2 border-black p-8 text-center shadow-[4px_4px_0_0_#000]">
                      <p className="text-muted-foreground">No phrases match the current filter.</p>
                    </Card>
                  ) : (
                    <div className="space-y-4">
                      {filteredPhrases.map((phrase: MarketPhrase) => (
                        <PhraseCard
                          key={phrase.id}
                          phrase={phrase}
                          onCopy={copyToClipboard}
                        />
                      ))}
                    </div>
                  )}
                </>
              )}
            </>
          )}

          {/* Empty state — no scrape selected */}
          {!activeScrapeId && !searchResult && (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <Search size={48} className="mb-4 text-muted-foreground/30" />
              <h3 className="text-lg font-bold">Ready to research</h3>
              <p className="mt-1 max-w-md text-sm text-muted-foreground">
                Search for a topic like &quot;app maker frustrations&quot; or paste a specific Reddit URL.
                The scraper will pull every comment and categorize them into pain points, desires, validation signals, and ad copy hooks.
              </p>
              <div className="mt-6 grid max-w-lg gap-3 text-left text-sm">
                <div className="rounded border-2 border-black bg-card p-3 shadow-[2px_2px_0_0_#000]">
                  <p className="font-bold">Topic Search examples:</p>
                  <ul className="mt-1 space-y-1 text-muted-foreground">
                    <li>&bull; &quot;SaaS pricing complaints&quot;</li>
                    <li>&bull; &quot;AI coding tools frustrations&quot;</li>
                    <li>&bull; &quot;looking for project management app&quot;</li>
                    <li>&bull; &quot;vibe coding app maker&quot;</li>
                  </ul>
                </div>
                <div className="rounded border-2 border-black bg-card p-3 shadow-[2px_2px_0_0_#000]">
                  <p className="font-bold">Rate limits (free, no API key):</p>
                  <ul className="mt-1 space-y-1 text-muted-foreground">
                    <li>&bull; ~10 requests/minute without key</li>
                    <li>&bull; ~60 requests/minute with free Reddit API key</li>
                    <li>&bull; Each thread = 1 request. Search = 1 request per subreddit.</li>
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function SummaryCard({
  label,
  count,
  color,
  textColor,
  icon,
}: {
  label: string
  count: number
  color: string
  textColor?: string
  icon: React.ReactNode
}) {
  return (
    <Card className={`border-2 border-black shadow-[3px_3px_0_0_#000] ${color}`}>
      <CardContent className="flex items-center gap-3 p-3">
        {icon}
        <div>
          <p className={`text-2xl font-bold ${textColor ?? ''}`}>{count}</p>
          <p className="text-xs font-semibold text-muted-foreground">{label}</p>
        </div>
      </CardContent>
    </Card>
  )
}

function PhraseCard({
  phrase,
  onCopy,
}: {
  phrase: MarketPhrase
  onCopy: (text: string, label: string) => void
}) {
  const config = CATEGORY_CONFIG[phrase.category] || {
    label: phrase.category,
    color: 'text-white',
    bg: 'bg-gray-500',
    icon: MessageSquare,
  }
  const CategoryIcon = config.icon

  return (
    <Card className="border-2 border-black shadow-[4px_4px_0_0_#000] transition-all hover:shadow-[6px_6px_0_0_#000]">
      <CardContent className="p-4">
        {/* Top row: category badge, author, score, validation stars */}
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <Badge className={`${config.bg} ${config.color} gap-1 border-0`}>
            <CategoryIcon size={12} />
            {config.label}
          </Badge>
          {phrase.subcategory && phrase.subcategory !== 'general' && (
            <Badge variant="outline" className="border-2 border-black text-[10px]">
              {phrase.subcategory}
            </Badge>
          )}
          <span className="text-xs text-muted-foreground">u/{phrase.author}</span>
          <Badge variant="outline" className="border-2 border-black text-xs">
            {phrase.score} pts
          </Badge>
          <div className="ml-auto flex items-center gap-0.5" title={`Validation signal: ${phrase.validation_signal}/5`}>
            {Array.from({ length: 5 }, (_, i) => (
              <Star
                key={i}
                size={14}
                className={
                  i < phrase.validation_signal
                    ? 'fill-[#f59e0b] text-[#f59e0b]'
                    : 'text-muted-foreground/30'
                }
              />
            ))}
          </div>
        </div>

        {/* Raw Reddit quote */}
        <blockquote className="mb-4 border-l-4 border-primary/40 bg-muted/50 py-2 pl-4 pr-2 text-sm italic text-foreground">
          &ldquo;{phrase.raw_text}&rdquo;
        </blockquote>

        {/* Ad Hook + Social Post Idea side by side */}
        <div className="grid gap-3 md:grid-cols-2">
          <div className="rounded border-2 border-black bg-[#ef4444]/5 p-3">
            <div className="mb-1 flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-[#ef4444]">
                Ad Hook
              </span>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0"
                onClick={() => onCopy(phrase.ad_hook, 'Ad Hook')}
                title="Copy ad hook"
              >
                <Copy size={12} />
              </Button>
            </div>
            <p className="text-sm">{phrase.ad_hook}</p>
          </div>

          <div className="rounded border-2 border-black bg-[#3b82f6]/5 p-3">
            <div className="mb-1 flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-[#3b82f6]">
                Social Post Idea
              </span>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0"
                onClick={() => onCopy(phrase.social_post_idea, 'Social Post Idea')}
                title="Copy social post idea"
              >
                <Copy size={12} />
              </Button>
            </div>
            <p className="text-sm">{phrase.social_post_idea}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function TopPhraseRow({
  phrase,
  rank,
  onCopy,
}: {
  phrase: MarketTopPhrase
  rank: number
  onCopy: (text: string, label: string) => void
}) {
  const [expanded, setExpanded] = useState(false)

  // Determine the dominant category for color-coding
  const topCategory = Object.entries(phrase.categories)
    .sort(([, a], [, b]) => b - a)[0]?.[0] ?? 'uncategorized'
  const config = CATEGORY_CONFIG[topCategory]

  // Bar width based on count relative to #1 (rank 1 = 100%)
  const maxCount = rank === 1 ? phrase.count : phrase.count // parent handles normalization

  return (
    <Card
      className="cursor-pointer border-2 border-black shadow-[3px_3px_0_0_#000] transition-all hover:shadow-[4px_4px_0_0_#000]"
      onClick={() => setExpanded(!expanded)}
    >
      <CardContent className="p-3">
        <div className="flex items-center gap-3">
          {/* Rank number */}
          <span className="w-8 text-center text-lg font-black text-muted-foreground">
            #{rank}
          </span>

          {/* Phrase + bar */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold">&ldquo;{phrase.phrase}&rdquo;</span>
              <Button
                variant="ghost"
                size="sm"
                className="h-5 w-5 p-0 shrink-0"
                onClick={(e) => {
                  e.stopPropagation()
                  onCopy(phrase.phrase, 'Phrase')
                }}
                title="Copy phrase"
              >
                <Copy size={10} />
              </Button>
            </div>
            {/* Frequency bar */}
            <div className="mt-1 h-2 w-full rounded-full bg-muted/50 border border-black/10">
              <div
                className={`h-full rounded-full ${config?.bg ?? 'bg-primary'}`}
                style={{ width: `${Math.min(100, (phrase.count / maxCount) * 100)}%`, opacity: 0.7 }}
              />
            </div>
          </div>

          {/* Count badge */}
          <Badge
            variant="outline"
            className="border-2 border-black text-sm font-bold shrink-0"
          >
            {phrase.count}x
          </Badge>

          {/* Category badges */}
          <div className="hidden md:flex gap-1 shrink-0">
            {Object.entries(phrase.categories)
              .sort(([, a], [, b]) => b - a)
              .slice(0, 2)
              .map(([cat, count]) => {
                const c = CATEGORY_CONFIG[cat]
                return c ? (
                  <Badge key={cat} className={`${c.bg} ${c.color} border-0 text-[10px]`}>
                    {c.label} ({count})
                  </Badge>
                ) : null
              })}
          </div>

          <ChevronDown
            size={14}
            className={`text-muted-foreground transition-transform ${expanded ? 'rotate-180' : ''}`}
          />
        </div>

        {/* Expanded: sample texts */}
        {expanded && phrase.sample_texts.length > 0 && (
          <div className="mt-3 border-t-2 border-black/10 pt-3 space-y-2">
            <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
              Sample comments containing this phrase:
            </p>
            {phrase.sample_texts.map((sample, i) => (
              <blockquote
                key={i}
                className="border-l-4 border-primary/30 bg-muted/30 py-1.5 pl-3 pr-2 text-xs italic text-muted-foreground"
              >
                &ldquo;{sample}&rdquo;
              </blockquote>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

/** Angle card used in the project detail view */
function AngleCard({
  angle,
  angleTypes,
  onRun,
  isRunning,
  onViewScrape,
}: {
  angle: ProjectAngle
  angleTypes: Record<string, AngleTypeInfo> | undefined
  onRun: (angleId: number) => void
  isRunning: boolean
  onViewScrape: (scrapeId: number) => void
}) {
  const [expanded, setExpanded] = useState(false)
  const config = ANGLE_TYPE_CONFIG[angle.angle_type]
  const Icon = config?.icon ?? Target
  const info = angleTypes?.[angle.angle_type]
  const statusBadge = STATUS_BADGE[angle.status] ?? STATUS_BADGE.pending

  return (
    <Card
      className="border-2 border-black shadow-[3px_3px_0_0_#000] transition-all hover:shadow-[4px_4px_0_0_#000]"
    >
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          {/* Angle type icon + label */}
          <div className={`flex h-10 w-10 items-center justify-center rounded border-2 border-black ${config?.bg ?? 'bg-gray-200'}`}>
            <Icon size={20} className={config?.color ?? 'text-black'} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold">{info?.label ?? angle.angle_type}</span>
              <Badge className={`border text-[10px] ${statusBadge.className}`}>
                {statusBadge.label}
              </Badge>
            </div>
            {angle.custom_keywords && (
              <p className="mt-0.5 text-xs text-muted-foreground">Keywords: {angle.custom_keywords}</p>
            )}
          </div>

          {/* Phrase count */}
          <Badge variant="outline" className="border-2 border-black text-sm font-bold">
            {angle.total_phrases} phrases
          </Badge>

          {/* Run button */}
          <Button
            variant="outline"
            size="sm"
            className="gap-1.5 border-2 border-black shadow-[2px_2px_0_0_#000]"
            onClick={() => onRun(angle.id)}
            disabled={isRunning || angle.status === 'running'}
          >
            {angle.status === 'running' || isRunning ? (
              <Loader2 size={14} className="animate-spin" />
            ) : angle.status === 'complete' ? (
              <Check size={14} className="text-[#22c55e]" />
            ) : (
              <Play size={14} />
            )}
            {angle.status === 'complete' ? 'Re-run' : 'Run'}
          </Button>

          {/* Expand toggle */}
          <button
            className="text-muted-foreground transition-transform"
            onClick={() => setExpanded(!expanded)}
          >
            <ChevronDown size={16} className={expanded ? 'rotate-180' : ''} />
          </button>
        </div>

        {/* Expanded details: search queries and scrape links */}
        {expanded && (
          <div className="mt-4 border-t-2 border-black/10 pt-3 space-y-3">
            {angle.search_queries.length > 0 && (
              <div>
                <p className="mb-1 text-xs font-bold uppercase tracking-wider text-muted-foreground">
                  Generated Search Queries
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {angle.search_queries.map((q, i) => (
                    <Badge key={i} variant="outline" className="border border-black text-xs">
                      {q}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
            {angle.scrape_ids.length > 0 && (
              <div>
                <p className="mb-1 text-xs font-bold uppercase tracking-wider text-muted-foreground">
                  Linked Scrapes
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {angle.scrape_ids.map((sid) => (
                    <Button
                      key={sid}
                      variant="outline"
                      size="sm"
                      className="gap-1 border-2 border-black text-xs"
                      onClick={() => onViewScrape(sid)}
                    >
                      <BookOpen size={12} />
                      Scrape #{sid}
                    </Button>
                  ))}
                </div>
              </div>
            )}
            {angle.search_queries.length === 0 && angle.scrape_ids.length === 0 && (
              <p className="text-xs text-muted-foreground italic">
                Run this angle to generate search queries and gather data.
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
