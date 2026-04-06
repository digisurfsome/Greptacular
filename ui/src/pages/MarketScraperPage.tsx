import { useState, useCallback } from 'react'
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
} from 'lucide-react'
import { useScrapes, useScrape, useScrapeThread, useDeleteScrape } from '@/hooks/useMarketScraper'
import { exportScrape } from '@/lib/api'
import type { MarketScrape, MarketPhrase } from '@/lib/types'

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

export function MarketScraperPage() {
  const [url, setUrl] = useState('')
  const [activeScrapeId, setActiveScrapeId] = useState<number | null>(null)
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [sortMode, setSortMode] = useState<SortMode>('score')
  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null)

  const { data: scrapes } = useScrapes()
  const { data: activeScrapeData } = useScrape(activeScrapeId)
  const scrapeThread = useScrapeThread()
  const deleteScrape = useDeleteScrape()

  // Show a toast notification that auto-dismisses after 3 seconds
  const showToast = useCallback((type: 'success' | 'error', message: string) => {
    setToast({ type, message })
    setTimeout(() => setToast(null), 3000)
  }, [])

  const handleScrape = useCallback(() => {
    if (!url.trim()) return
    scrapeThread.mutate(url.trim(), {
      onSuccess: (data: MarketScrape) => {
        showToast('success', `Scraped ${data.total_phrases} phrases from r/${data.subreddit}`)
        setActiveScrapeId(data.id)
        setUrl('')
      },
      onError: (err: Error) => {
        showToast('error', err.message || 'Failed to scrape thread')
      },
    })
  }, [url, scrapeThread, showToast])

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

      {/* Main layout: sidebar + content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar — Past Scrapes */}
        <aside className="w-64 flex-shrink-0 overflow-y-auto border-r-2 border-border bg-card p-3">
          <h2 className="mb-3 text-sm font-bold uppercase tracking-wider text-muted-foreground">
            Past Scrapes
          </h2>
          {(!scrapes || scrapes.length === 0) ? (
            <p className="text-xs text-muted-foreground italic">
              No scrapes yet. Paste a URL above to get started.
            </p>
          ) : (
            <div className="space-y-2">
              {(scrapes as MarketScrape[]).map((scrape) => (
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
          {/* Section 1: Scrape Input */}
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
                  disabled={!url.trim() || scrapeThread.isPending}
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

          {/* Section 2 + 3: Results dashboard + phrase cards (when a scrape is active) */}
          {activeScrapeId && activeScrapeData && (
            <>
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

          {/* Empty state — no scrape selected */}
          {!activeScrapeId && (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <Search size={48} className="mb-4 text-muted-foreground/30" />
              <h3 className="text-lg font-bold">No scrape selected</h3>
              <p className="mt-1 max-w-md text-sm text-muted-foreground">
                Paste a Reddit thread URL above and hit Scrape Thread, or select a past scrape from the sidebar.
              </p>
            </div>
          )}
        </div>
      </div>
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
