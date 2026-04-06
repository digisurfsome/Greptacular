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
  Link,
  Globe,
  ChevronDown,
  ExternalLink,
  Zap,
} from 'lucide-react'
import {
  useScrapes,
  useScrape,
  useScrapeThread,
  useDeleteScrape,
  useSearchOptions,
  useSearchAndScrape,
} from '@/hooks/useMarketScraper'
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
type InputMode = 'url' | 'topic'

export function MarketScraperPage() {
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
  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null)

  const { data: scrapes } = useScrapes()
  const { data: activeScrapeData } = useScrape(activeScrapeId)
  const scrapeThread = useScrapeThread()
  const deleteScrape = useDeleteScrape()
  const { data: searchOptions } = useSearchOptions()
  const searchAndScrape = useSearchAndScrape()

  const defaultSubs: string[] = searchOptions?.default_subreddits ?? []
  const sortOptions: string[] = searchOptions?.sort_options ?? ['relevance', 'hot', 'top', 'new', 'comments']
  const timeFilters: string[] = searchOptions?.time_filters ?? ['all', 'year', 'month', 'week', 'day', 'hour']

  const showToast = useCallback((type: 'success' | 'error', message: string) => {
    setToast({ type, message })
    setTimeout(() => setToast(null), 3000)
  }, [])

  // URL scrape handler
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
      },
      {
        onSuccess: (data) => {
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
  }, [topicQuery, selectedSubs, topicSort, topicTime, maxThreads, searchAndScrape, showToast])

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
              No scrapes yet. Search a topic or paste a URL to get started.
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
