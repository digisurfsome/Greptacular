import { useState } from 'react'
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
  Check,
} from 'lucide-react'
import {
  useScrapes,
  useScrape,
  useScrapeThread,
  useDeleteScrape,
} from '../hooks/useMarketScraper'
import type { MarketScrape, MarketPhrase } from '../lib/types'
import { exportScrape } from '../lib/api'

// Category display config: label, bg color, text color, icon
const CATEGORY_CONFIG: Record<string, { label: string; bg: string; text: string; icon: React.ReactNode }> = {
  pain_point: { label: 'Pain Point', bg: 'bg-red-100', text: 'text-red-700', icon: <AlertTriangle size={14} /> },
  desire: { label: 'Desire', bg: 'bg-blue-100', text: 'text-blue-700', icon: <Heart size={14} /> },
  feature_request: { label: 'Feature Request', bg: 'bg-amber-100', text: 'text-amber-700', icon: <MessageSquare size={14} /> },
  validation: { label: 'Validation', bg: 'bg-green-100', text: 'text-green-700', icon: <ThumbsUp size={14} /> },
  social_proof: { label: 'Social Proof', bg: 'bg-purple-100', text: 'text-purple-700', icon: <TrendingUp size={14} /> },
}

const FILTER_TABS = ['all', 'pain_point', 'desire', 'feature_request', 'validation', 'social_proof'] as const
type FilterTab = typeof FILTER_TABS[number]

type SortMode = 'score' | 'validation' | 'recent'

/** Renders 1-5 filled stars for validation signal strength */
function ValidationStars({ value }: { value: number }) {
  return (
    <div className="flex items-center gap-0.5" title={`Validation signal: ${value}/5`}>
      {Array.from({ length: 5 }, (_, i) => (
        <Star
          key={i}
          size={14}
          className={i < value ? 'fill-amber-400 text-amber-400' : 'text-gray-300'}
        />
      ))}
    </div>
  )
}

/** Copy-to-clipboard button with brief "Copied!" feedback */
function CopyButton({ text, label }: { text: string; label: string }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      // Clipboard API may be blocked in some contexts
    }
  }

  return (
    <Button
      variant="ghost"
      size="sm"
      className="h-7 gap-1 text-xs"
      onClick={handleCopy}
      title={`Copy ${label}`}
    >
      {copied ? <Check size={12} className="text-green-600" /> : <Copy size={12} />}
      {copied ? 'Copied' : `Copy ${label}`}
    </Button>
  )
}

/** Single phrase result card */
function PhraseCard({ phrase }: { phrase: MarketPhrase }) {
  const config = CATEGORY_CONFIG[phrase.category] ?? {
    label: phrase.category,
    bg: 'bg-gray-100',
    text: 'text-gray-700',
    icon: null,
  }

  return (
    <Card className="border-2 border-black shadow-[4px_4px_0_0_#000] hover:shadow-[6px_6px_0_0_#000] transition-shadow">
      <CardContent className="p-4 space-y-3">
        {/* Quote */}
        <blockquote className="border-l-4 border-gray-400 pl-3 italic text-sm text-muted-foreground leading-relaxed">
          &ldquo;{phrase.raw_text}&rdquo;
        </blockquote>

        {/* Author + Score + Category */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-mono text-muted-foreground">u/{phrase.author}</span>
          <Badge variant="secondary" className="text-xs font-mono">
            {phrase.score} pts
          </Badge>
          <Badge className={`text-xs gap-1 ${config.bg} ${config.text} border-0`}>
            {config.icon}
            {config.label}
          </Badge>
          {phrase.subcategory && (
            <Badge variant="outline" className="text-xs">
              {phrase.subcategory}
            </Badge>
          )}
        </div>

        {/* Ad Hook */}
        {phrase.ad_hook && (
          <div className="rounded-lg bg-amber-50 border border-amber-200 p-3 space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wide text-amber-700">Ad Hook</span>
              <CopyButton text={phrase.ad_hook} label="Ad Hook" />
            </div>
            <p className="text-sm text-amber-900">{phrase.ad_hook}</p>
          </div>
        )}

        {/* Social Post Idea */}
        {phrase.social_post_idea && (
          <div className="rounded-lg bg-blue-50 border border-blue-200 p-3 space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wide text-blue-700">Social Post Idea</span>
              <CopyButton text={phrase.social_post_idea} label="Social Post" />
            </div>
            <p className="text-sm text-blue-900">{phrase.social_post_idea}</p>
          </div>
        )}

        {/* Validation Signal */}
        <div className="flex items-center justify-between pt-1">
          <ValidationStars value={phrase.validation_signal} />
          <span className="text-xs text-muted-foreground">
            {new Date(phrase.created_at).toLocaleDateString()}
          </span>
        </div>
      </CardContent>
    </Card>
  )
}

/** Summary stat card for the dashboard row */
function StatCard({
  label,
  count,
  color,
  icon,
}: {
  label: string
  count: number
  color: string
  icon: React.ReactNode
}) {
  return (
    <Card className={`border-2 border-black shadow-[3px_3px_0_0_#000] ${color}`}>
      <CardContent className="p-3 flex items-center gap-3">
        <div className="p-2 rounded-lg bg-white/60">{icon}</div>
        <div>
          <p className="text-2xl font-bold font-mono">{count}</p>
          <p className="text-xs font-medium uppercase tracking-wide">{label}</p>
        </div>
      </CardContent>
    </Card>
  )
}

/** Sidebar item for a past scrape */
function ScrapeListItem({
  scrape,
  isActive,
  onSelect,
  onDelete,
  onExport,
}: {
  scrape: MarketScrape
  isActive: boolean
  onSelect: () => void
  onDelete: () => void
  onExport: () => void
}) {
  const [confirmDelete, setConfirmDelete] = useState(false)

  return (
    <div
      className={`p-3 rounded-lg border-2 cursor-pointer transition-all ${
        isActive
          ? 'border-black bg-primary/10 shadow-[3px_3px_0_0_#000]'
          : 'border-gray-300 hover:border-black hover:shadow-[2px_2px_0_0_#000]'
      }`}
      onClick={onSelect}
    >
      <p className="font-bold text-sm truncate">r/{scrape.subreddit}</p>
      <p className="text-xs text-muted-foreground truncate mt-0.5" title={scrape.title}>
        {scrape.title}
      </p>
      <div className="flex items-center justify-between mt-2">
        <span className="text-xs text-muted-foreground">
          {new Date(scrape.scraped_at).toLocaleDateString()}
        </span>
        <Badge variant="secondary" className="text-xs">
          {scrape.total_phrases} phrases
        </Badge>
      </div>
      <div className="flex items-center gap-1 mt-2">
        <Button
          variant="ghost"
          size="sm"
          className="h-6 w-6 p-0"
          onClick={(e) => {
            e.stopPropagation()
            onExport()
          }}
          title="Export CSV"
        >
          <Download size={12} />
        </Button>
        {confirmDelete ? (
          <div className="flex items-center gap-1 ml-auto" onClick={(e) => e.stopPropagation()}>
            <span className="text-xs text-red-600 font-medium">Delete?</span>
            <Button
              variant="destructive"
              size="sm"
              className="h-6 px-2 text-xs"
              onClick={onDelete}
            >
              Yes
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 px-2 text-xs"
              onClick={() => setConfirmDelete(false)}
            >
              No
            </Button>
          </div>
        ) : (
          <Button
            variant="ghost"
            size="sm"
            className="h-6 w-6 p-0 ml-auto text-muted-foreground hover:text-red-600"
            onClick={(e) => {
              e.stopPropagation()
              setConfirmDelete(true)
            }}
            title="Delete scrape"
          >
            <Trash2 size={12} />
          </Button>
        )}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export function MarketScraperPage() {
  const [url, setUrl] = useState('')
  const [activeScrapeId, setActiveScrapeId] = useState<number | null>(null)
  const [activeFilter, setActiveFilter] = useState<FilterTab>('all')
  const [sortMode, setSortMode] = useState<SortMode>('score')
  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  // Data hooks
  const { data: scrapes, isLoading: scrapesLoading } = useScrapes()
  const { data: activeScrape } = useScrape(activeScrapeId)
  const scrapeThread = useScrapeThread()
  const deleteScrape = useDeleteScrape()

  // Auto-dismiss toast after 3 seconds
  const showToast = (type: 'success' | 'error', message: string) => {
    setToast({ type, message })
    setTimeout(() => setToast(null), 3000)
  }

  // Handle scrape submission
  const handleScrape = async () => {
    if (!url.trim()) return
    try {
      const result = await scrapeThread.mutateAsync(url.trim())
      setActiveScrapeId(result.id)
      setUrl('')
      showToast('success', `Scraped ${result.total_phrases} phrases from r/${result.subreddit}`)
    } catch (err) {
      showToast('error', err instanceof Error ? err.message : 'Scrape failed')
    }
  }

  // Handle CSV export (downloads as file)
  const handleExport = async (id: number) => {
    try {
      const blob = await exportScrape(id)
      const downloadUrl = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = downloadUrl
      a.download = `scrape-${id}.csv`
      a.click()
      URL.revokeObjectURL(downloadUrl)
    } catch {
      showToast('error', 'Export failed')
    }
  }

  // Handle delete
  const handleDelete = async (id: number) => {
    try {
      await deleteScrape.mutateAsync(id)
      if (activeScrapeId === id) setActiveScrapeId(null)
      showToast('success', 'Scrape deleted')
    } catch {
      showToast('error', 'Delete failed')
    }
  }

  // Get phrases from the active scrape, applying filter and sort
  const phrases: MarketPhrase[] = activeScrape?.phrases ?? []
  const filteredPhrases = phrases
    .filter((p: MarketPhrase) => activeFilter === 'all' || p.category === activeFilter)
    .sort((a: MarketPhrase, b: MarketPhrase) => {
      if (sortMode === 'score') return b.score - a.score
      if (sortMode === 'validation') return b.validation_signal - a.validation_signal
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    })

  // Compute category counts for summary cards
  const categoryCounts = phrases.reduce(
    (acc: Record<string, number>, p: MarketPhrase) => {
      acc[p.category] = (acc[p.category] || 0) + 1
      return acc
    },
    {} as Record<string, number>,
  )

  return (
    <div className="flex h-screen flex-col bg-background">
      {/* Header Bar */}
      <div className="flex items-center gap-3 border-b-2 border-black px-4 py-3 bg-card">
        <Button
          variant="ghost"
          size="sm"
          className="h-8 w-8 p-0"
          onClick={() => { window.location.hash = '' }}
          title="Back to home"
        >
          <ArrowLeft size={18} />
        </Button>
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-primary/10">
            <Search size={20} className="text-primary" />
          </div>
          <div>
            <h1 className="text-lg font-bold leading-tight">Market Scraper</h1>
            <p className="text-xs text-muted-foreground">
              Scrape Reddit for pain points, desires, and ad copy gold
            </p>
          </div>
        </div>
      </div>

      {/* Toast notification */}
      {toast && (
        <div
          className={`mx-4 mt-2 rounded-lg border-2 border-black px-4 py-2 text-sm font-medium shadow-[3px_3px_0_0_#000] ${
            toast.type === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}
        >
          {toast.message}
        </div>
      )}

      {/* Main layout: sidebar + content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar: Past Scrapes */}
        <aside className="w-64 shrink-0 border-r-2 border-black bg-card/50 p-3 overflow-y-auto hidden md:block">
          <h2 className="font-bold text-sm uppercase tracking-wide text-muted-foreground mb-3">
            Past Scrapes
          </h2>
          {scrapesLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 size={20} className="animate-spin text-muted-foreground" />
            </div>
          ) : !scrapes?.length ? (
            <p className="text-xs text-muted-foreground text-center py-8">
              No scrapes yet. Paste a Reddit URL above to get started.
            </p>
          ) : (
            <div className="space-y-2">
              {scrapes.map((s: MarketScrape) => (
                <ScrapeListItem
                  key={s.id}
                  scrape={s}
                  isActive={activeScrapeId === s.id}
                  onSelect={() => setActiveScrapeId(s.id)}
                  onDelete={() => handleDelete(s.id)}
                  onExport={() => handleExport(s.id)}
                />
              ))}
            </div>
          )}
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto p-4 space-y-6">
          {/* Section 1: Scrape Input */}
          <Card className="border-2 border-black shadow-[4px_4px_0_0_#000]">
            <CardContent className="p-4">
              <div className="flex gap-2">
                <Input
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="Paste a Reddit thread URL..."
                  className="flex-1 border-2 border-black font-mono text-sm"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleScrape()
                  }}
                  disabled={scrapeThread.isPending}
                />
                <Button
                  onClick={handleScrape}
                  disabled={!url.trim() || scrapeThread.isPending}
                  className="border-2 border-black shadow-[3px_3px_0_0_#000] hover:shadow-[1px_1px_0_0_#000] active:shadow-none transition-shadow font-bold"
                >
                  {scrapeThread.isPending ? (
                    <>
                      <Loader2 size={16} className="animate-spin mr-1" />
                      Scraping...
                    </>
                  ) : (
                    <>
                      <Search size={16} className="mr-1" />
                      Scrape Thread
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Section 2: Results Dashboard (only show when a scrape is selected) */}
          {activeScrape && (
            <>
              {/* Scrape title */}
              <div>
                <h2 className="font-bold text-lg">{activeScrape.title}</h2>
                <p className="text-xs text-muted-foreground">
                  r/{activeScrape.subreddit} &middot; {new Date(activeScrape.scraped_at).toLocaleString()}
                </p>
              </div>

              {/* Summary Cards Row */}
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                <StatCard
                  label="Total Phrases"
                  count={phrases.length}
                  color="bg-gray-50"
                  icon={<MessageSquare size={18} className="text-gray-600" />}
                />
                <StatCard
                  label="Pain Points"
                  count={categoryCounts['pain_point'] ?? 0}
                  color="bg-red-50"
                  icon={<AlertTriangle size={18} className="text-red-500" />}
                />
                <StatCard
                  label="Desires"
                  count={categoryCounts['desire'] ?? 0}
                  color="bg-blue-50"
                  icon={<Heart size={18} className="text-blue-500" />}
                />
                <StatCard
                  label="Validation"
                  count={categoryCounts['validation'] ?? 0}
                  color="bg-green-50"
                  icon={<ThumbsUp size={18} className="text-green-500" />}
                />
                <StatCard
                  label="Social Proof"
                  count={categoryCounts['social_proof'] ?? 0}
                  color="bg-purple-50"
                  icon={<TrendingUp size={18} className="text-purple-500" />}
                />
              </div>

              {/* Category Filter Tabs + Sort */}
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex flex-wrap gap-1">
                  {FILTER_TABS.map((tab) => {
                    const config = tab === 'all'
                      ? { label: 'All', bg: '', text: '' }
                      : CATEGORY_CONFIG[tab] ?? { label: tab, bg: '', text: '' }
                    const isActive = activeFilter === tab
                    return (
                      <Button
                        key={tab}
                        variant={isActive ? 'default' : 'outline'}
                        size="sm"
                        className={`text-xs border-2 border-black ${
                          isActive ? 'shadow-[2px_2px_0_0_#000]' : 'shadow-none'
                        }`}
                        onClick={() => setActiveFilter(tab)}
                      >
                        {config.label}
                        {tab !== 'all' && (
                          <span className="ml-1 opacity-70">
                            ({categoryCounts[tab] ?? 0})
                          </span>
                        )}
                      </Button>
                    )
                  })}
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground font-medium">Sort by:</span>
                  {([
                    { key: 'score' as SortMode, label: 'Score' },
                    { key: 'validation' as SortMode, label: 'Validation' },
                    { key: 'recent' as SortMode, label: 'Recent' },
                  ]).map(({ key, label }) => (
                    <Button
                      key={key}
                      variant={sortMode === key ? 'default' : 'ghost'}
                      size="sm"
                      className="text-xs h-7"
                      onClick={() => setSortMode(key)}
                    >
                      {label}
                    </Button>
                  ))}
                </div>
              </div>

              {/* Section 3: Phrase Cards */}
              {filteredPhrases.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <Search size={32} className="mx-auto mb-2 opacity-40" />
                  <p className="text-sm">No phrases match the current filter.</p>
                </div>
              ) : (
                <div className="grid gap-4 sm:grid-cols-1 lg:grid-cols-2">
                  {filteredPhrases.map((phrase: MarketPhrase) => (
                    <PhraseCard key={phrase.id} phrase={phrase} />
                  ))}
                </div>
              )}
            </>
          )}

          {/* Empty state when no scrape is selected */}
          {!activeScrape && !scrapeThread.isPending && (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <div className="p-4 rounded-2xl bg-primary/5 mb-4">
                <Search size={48} className="text-primary/40" />
              </div>
              <h3 className="text-lg font-bold mb-1">No scrape selected</h3>
              <p className="text-sm text-muted-foreground max-w-md">
                Paste a Reddit thread URL above to scrape it for pain points, desires, and ad copy
                angles. Or select a past scrape from the sidebar.
              </p>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
