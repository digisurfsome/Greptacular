/**
 * BatchImportView — Multi-URL YouTube batch import for YT Strategy Lab.
 *
 * Allows pasting multiple YouTube URLs, fetching previews for all,
 * adding per-video context/instructions, and processing them into
 * projects on autopilot.
 */

import { useState, useCallback, useRef, useEffect } from 'react'
import {
  ArrowLeft,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Youtube,
  Camera,
  Clock,
  X,
  Layers,
  Play,
  Hash,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import type {
  YTBatchVideoInput,
  YTBatchVideoState,
  YTBatchStatusResponse,
} from '@/lib/types'
import { batchIngestVideos, batchProcessVideos, getBatchStatus } from '@/lib/api'

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const MODEL_OPTIONS: { value: string; label: string }[] = [
  { value: 'claude-sonnet-4-6', label: 'Sonnet 4.6 (Balanced — default for bulk)' },
  { value: 'claude-opus-4-6', label: 'Opus 4.6 (Heavy thinking)' },
  { value: 'claude-haiku-4-5', label: 'Haiku 4.5 (Fast & light)' },
]

/** Extract video IDs from various YouTube URL formats. */
function parseYouTubeUrls(input: string): string[] {
  const urlPattern = /(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/|v\/)|youtu\.be\/)[a-zA-Z0-9_-]+[^\s,]*/g
  const matches = input.match(urlPattern) || []

  // Deduplicate
  const seen = new Set<string>()
  const unique: string[] = []
  for (const m of matches) {
    const clean = m.trim().replace(/[,;]+$/, '')
    if (!seen.has(clean)) {
      seen.add(clean)
      unique.push(clean)
    }
  }
  return unique
}

function formatDuration(totalSeconds: number): string {
  const total = Math.floor(totalSeconds)
  const hours = Math.floor(total / 3600)
  const minutes = Math.floor((total % 3600) / 60)
  const seconds = total % 60
  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
  }
  return `${minutes}:${String(seconds).padStart(2, '0')}`
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type BatchPhase = 'input' | 'preview' | 'processing' | 'complete'

interface VideoEntry {
  url: string
  context: string
  niche: string
  tags: string[]
  captureScreenshots: boolean
  priority: number
  tagInput: string
}

interface BatchImportViewProps {
  onBack: () => void
  onBatchComplete?: () => void
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function VideoPreviewCard({
  video,
  entry,
  index,
  onUpdateEntry,
  onRemove,
}: {
  video: YTBatchVideoState
  entry: VideoEntry
  index: number
  onUpdateEntry: (index: number, updates: Partial<VideoEntry>) => void
  onRemove: (index: number) => void
}) {
  const statusColor = {
    pending: 'text-muted-foreground',
    ingesting: 'text-blue-500',
    ingested: 'text-emerald-500',
    processing: 'text-blue-500',
    complete: 'text-emerald-500',
    error: 'text-destructive',
  }[video.status]

  const statusLabel = {
    pending: 'Queued',
    ingesting: 'Fetching...',
    ingested: 'Ready',
    processing: 'Processing...',
    complete: 'Complete',
    error: 'Error',
  }[video.status]

  return (
    <div className="rounded-lg border border-border bg-card p-4 space-y-3">
      {/* Header row with thumbnail + metadata */}
      <div className="flex gap-3">
        {video.thumbnail_url ? (
          <img
            src={video.thumbnail_url}
            alt={video.title || 'Video thumbnail'}
            className="w-28 h-auto rounded-md border border-border object-cover shrink-0"
          />
        ) : (
          <div className="w-28 h-16 rounded-md border border-border bg-muted flex items-center justify-center shrink-0">
            <Youtube size={24} className="text-muted-foreground" />
          </div>
        )}
        <div className="min-w-0 flex-1 space-y-1">
          <div className="flex items-start justify-between gap-2">
            <p className="text-sm font-semibold text-foreground leading-snug line-clamp-2">
              {video.title || video.url}
            </p>
            <button
              onClick={() => onRemove(index)}
              className="shrink-0 p-1 rounded hover:bg-muted transition-colors"
              aria-label="Remove video"
            >
              <X size={14} className="text-muted-foreground" />
            </button>
          </div>
          {video.channel && (
            <p className="text-xs text-muted-foreground">{video.channel}</p>
          )}
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            {video.duration > 0 && (
              <span className="flex items-center gap-1">
                <Clock size={12} />
                {formatDuration(video.duration)}
              </span>
            )}
            <span className={`flex items-center gap-1 ${statusColor}`}>
              {video.status === 'ingesting' || video.status === 'processing' ? (
                <Loader2 size={12} className="animate-spin" />
              ) : video.status === 'complete' || video.status === 'ingested' ? (
                <CheckCircle2 size={12} />
              ) : video.status === 'error' ? (
                <AlertCircle size={12} />
              ) : null}
              {statusLabel}
            </span>
          </div>
          {video.error && (
            <p className="text-xs text-destructive">{video.error}</p>
          )}
        </div>
      </div>

      {/* Context textarea */}
      <div className="space-y-1.5">
        <label className="text-xs font-medium text-muted-foreground">
          Context / Instructions
        </label>
        <Textarea
          value={entry.context}
          onChange={(e) => onUpdateEntry(index, { context: e.target.value })}
          placeholder="What should we extract from this video? Focus on specific steps, prompts, tools..."
          className="min-h-[60px] text-sm"
        />
      </div>

      {/* Niche + tags + screenshot toggle row */}
      <div className="flex flex-wrap gap-3 items-end">
        <div className="flex-1 min-w-[120px] space-y-1">
          <label className="text-xs font-medium text-muted-foreground">Niche</label>
          <Input
            value={entry.niche}
            onChange={(e) => onUpdateEntry(index, { niche: e.target.value })}
            placeholder="e.g., Car Dealerships"
            className="text-sm h-8"
          />
        </div>
        <div className="flex-1 min-w-[150px] space-y-1">
          <label className="text-xs font-medium text-muted-foreground flex items-center gap-1">
            <Hash size={12} />
            Tags
          </label>
          <div className="flex gap-1.5 items-center flex-wrap">
            {entry.tags.map((tag, ti) => (
              <Badge key={ti} variant="secondary" className="text-xs gap-1">
                {tag}
                <button
                  onClick={() => {
                    const newTags = entry.tags.filter((_, i) => i !== ti)
                    onUpdateEntry(index, { tags: newTags })
                  }}
                  className="ml-0.5 hover:text-destructive"
                >
                  <X size={10} />
                </button>
              </Badge>
            ))}
            <Input
              value={entry.tagInput}
              onChange={(e) => onUpdateEntry(index, { tagInput: e.target.value })}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && entry.tagInput.trim()) {
                  e.preventDefault()
                  onUpdateEntry(index, {
                    tags: [...entry.tags, entry.tagInput.trim()],
                    tagInput: '',
                  })
                }
              }}
              placeholder="Add tag..."
              className="text-xs h-7 w-20 min-w-[80px]"
            />
          </div>
        </div>
        <label className="flex items-center gap-1.5 cursor-pointer select-none shrink-0 pb-0.5">
          <input
            type="checkbox"
            checked={entry.captureScreenshots}
            onChange={(e) => onUpdateEntry(index, { captureScreenshots: e.target.checked })}
            className="h-3.5 w-3.5 rounded border-input accent-primary"
          />
          <span className="text-xs text-muted-foreground flex items-center gap-1">
            <Camera size={12} />
            Screenshots
          </span>
        </label>
        <div className="space-y-1 shrink-0">
          <label className="text-xs font-medium text-muted-foreground">Priority</label>
          <select
            value={entry.priority}
            onChange={(e) => onUpdateEntry(index, { priority: Number(e.target.value) })}
            className="text-xs bg-card border border-border rounded px-2 py-1 h-8 text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
          >
            {[1, 2, 3, 4, 5].map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Progress Bar
// ---------------------------------------------------------------------------

function BatchProgressBar({
  status,
}: {
  status: YTBatchStatusResponse
}) {
  const pct = status.total > 0
    ? Math.round(((status.ingested + status.processed) / (status.total * 2)) * 100)
    : 0

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>
          {status.status === 'ingesting'
            ? `Fetching metadata... (${status.ingested}/${status.total})`
            : status.status === 'ingested'
              ? `Metadata fetched. Starting processing...`
              : status.status === 'processing'
                ? `Processing... (${status.processed}/${status.total})`
                : status.status === 'complete'
                  ? 'Complete!'
                  : 'Starting...'}
        </span>
        <span>{pct}%</span>
      </div>
      <div className="h-2 rounded-full bg-muted overflow-hidden">
        <div
          className="h-full rounded-full bg-primary transition-all duration-500 ease-out"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export function BatchImportView({ onBack, onBatchComplete }: BatchImportViewProps): React.JSX.Element {
  const [phase, setPhase] = useState<BatchPhase>('input')
  const [urlInput, setUrlInput] = useState('')
  const [entries, setEntries] = useState<VideoEntry[]>([])
  const [selectedModel, setSelectedModel] = useState('claude-sonnet-4-6')
  const [, setBatchId] = useState<string | null>(null)
  const [batchStatus, setBatchStatus] = useState<YTBatchStatusResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Clean up polling on unmount
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [])

  /** Parse URLs from textarea and create entries */
  const handleParseUrls = useCallback(() => {
    const urls = parseYouTubeUrls(urlInput)
    if (urls.length === 0) {
      setError('No valid YouTube URLs found. Paste URLs separated by newlines or commas.')
      return
    }
    setError(null)
    setEntries(
      urls.map((url, i) => ({
        url,
        context: '',
        niche: '',
        tags: [],
        captureScreenshots: false,
        priority: i + 1,
        tagInput: '',
      }))
    )
    setPhase('preview')
  }, [urlInput])

  /** Update a single entry */
  const handleUpdateEntry = useCallback((index: number, updates: Partial<VideoEntry>) => {
    setEntries((prev) =>
      prev.map((e, i) => (i === index ? { ...e, ...updates } : e))
    )
  }, [])

  /** Remove a video entry */
  const handleRemoveEntry = useCallback((index: number) => {
    setEntries((prev) => prev.filter((_, i) => i !== index))
  }, [])

  /** Submit batch for ingestion + processing */
  const handleProcessAll = useCallback(async () => {
    if (entries.length === 0) return
    setIsSubmitting(true)
    setError(null)

    try {
      const videos: YTBatchVideoInput[] = entries.map((e) => ({
        url: e.url,
        context: e.context,
        niche: e.niche,
        tags: e.tags,
        capture_screenshots: e.captureScreenshots,
        priority: e.priority,
      }))

      const result = await batchIngestVideos(videos, selectedModel)
      setBatchId(result.batch_id)
      setPhase('processing')

      // Start polling for status
      let processingTriggered = false
      pollRef.current = setInterval(async () => {
        try {
          const status = await getBatchStatus(result.batch_id)
          setBatchStatus(status)

          // When ingestion is done, trigger processing (once)
          if (
            !processingTriggered &&
            status.status === 'ingested'
          ) {
            processingTriggered = true
            await batchProcessVideos(result.batch_id)
          }

          // When fully complete, stop polling
          if (status.status === 'complete' || status.status === 'error') {
            if (pollRef.current) clearInterval(pollRef.current)
            pollRef.current = null
            setPhase('complete')
            onBatchComplete?.()
          }
        } catch {
          // Ignore polling errors, will retry
        }
      }, 1500)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start batch import')
    } finally {
      setIsSubmitting(false)
    }
  }, [entries, selectedModel, onBatchComplete])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft size={16} />
          Back
        </button>
        <div className="flex items-center gap-2">
          <Layers size={20} className="text-primary" />
          <h2 className="text-lg font-semibold text-foreground">Batch Import</h2>
        </div>
      </div>

      {/* Phase: Input */}
      {phase === 'input' && (
        <div className="space-y-4">
          <div className="rounded-lg border border-border bg-card p-4 space-y-3">
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Paste YouTube URLs (one per line, comma-separated, or mixed)
            </label>
            <Textarea
              value={urlInput}
              onChange={(e) => {
                setUrlInput(e.target.value)
                if (error) setError(null)
              }}
              placeholder={`https://youtube.com/watch?v=abc123\nhttps://youtu.be/def456\nhttps://youtube.com/shorts/ghi789`}
              className="min-h-[120px] font-mono text-sm"
              autoFocus
            />
            {error && (
              <div className="flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2">
                <AlertCircle size={16} className="text-destructive shrink-0 mt-0.5" />
                <p className="text-sm text-destructive">{error}</p>
              </div>
            )}
            <div className="flex justify-between items-center">
              <p className="text-xs text-muted-foreground">
                {parseYouTubeUrls(urlInput).length} URL{parseYouTubeUrls(urlInput).length !== 1 ? 's' : ''} detected
              </p>
              <Button
                onClick={handleParseUrls}
                disabled={!urlInput.trim()}
                className="gap-1.5"
              >
                <Youtube size={14} />
                Fetch Previews
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Phase: Preview */}
      {phase === 'preview' && (
        <div className="space-y-4">
          {/* Model selector */}
          <div className="flex items-center gap-3 rounded-lg border border-border bg-card px-4 py-3">
            <label className="text-xs font-medium text-muted-foreground whitespace-nowrap">
              Processing Model:
            </label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="text-sm bg-card border border-border rounded px-2 py-1.5 text-foreground focus:outline-none focus:ring-1 focus:ring-ring flex-1 max-w-xs"
            >
              {MODEL_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Video cards — use batchStatus if available for live status, otherwise mock previews */}
          <div className="space-y-3">
            {entries.map((entry, i) => {
              const videoState: YTBatchVideoState = batchStatus?.videos[i] || {
                url: entry.url,
                video_id: null,
                title: null,
                channel: null,
                duration: 0,
                thumbnail_url: '',
                publish_date: '',
                context: entry.context,
                niche: entry.niche,
                tags: entry.tags,
                capture_screenshots: entry.captureScreenshots,
                priority: entry.priority,
                status: 'pending',
                error: null,
              }
              return (
                <VideoPreviewCard
                  key={entry.url}
                  video={videoState}
                  entry={entry}
                  index={i}
                  onUpdateEntry={handleUpdateEntry}
                  onRemove={handleRemoveEntry}
                />
              )
            })}
          </div>

          {entries.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              <p className="text-sm">All videos removed.</p>
              <Button
                variant="outline"
                onClick={() => setPhase('input')}
                className="mt-3"
              >
                Start Over
              </Button>
            </div>
          )}

          {error && (
            <div className="flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2">
              <AlertCircle size={16} className="text-destructive shrink-0 mt-0.5" />
              <p className="text-sm text-destructive">{error}</p>
            </div>
          )}

          {/* Action buttons */}
          {entries.length > 0 && (
            <div className="flex justify-between items-center">
              <Button
                variant="outline"
                onClick={() => {
                  setPhase('input')
                  setEntries([])
                }}
              >
                Back to URLs
              </Button>
              <Button
                onClick={handleProcessAll}
                disabled={isSubmitting}
                className="gap-1.5"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 size={14} className="animate-spin" />
                    Starting...
                  </>
                ) : (
                  <>
                    <Play size={14} />
                    Process All ({entries.length})
                  </>
                )}
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Phase: Processing */}
      {phase === 'processing' && batchStatus && (
        <div className="space-y-4">
          <BatchProgressBar status={batchStatus} />
          <div className="space-y-3">
            {batchStatus.videos.map((video, i) => {
              const entry = entries[i] || {
                url: video.url,
                context: video.context,
                niche: video.niche,
                tags: video.tags,
                captureScreenshots: video.capture_screenshots,
                priority: video.priority,
                tagInput: '',
              }
              return (
                <VideoPreviewCard
                  key={video.url}
                  video={video}
                  entry={entry}
                  index={i}
                  onUpdateEntry={() => {}}
                  onRemove={() => {}}
                />
              )
            })}
          </div>
        </div>
      )}

      {/* Phase: Processing — waiting for first status update */}
      {phase === 'processing' && !batchStatus && (
        <div className="flex flex-col items-center justify-center py-12 gap-3">
          <Loader2 size={32} className="text-primary animate-spin" />
          <p className="text-sm text-muted-foreground">Starting batch import...</p>
        </div>
      )}

      {/* Phase: Complete */}
      {phase === 'complete' && batchStatus && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 rounded-lg border border-emerald-500/30 bg-emerald-500/5 px-4 py-3">
            <CheckCircle2 size={18} className="text-emerald-500" />
            <p className="text-sm font-medium text-foreground">
              Batch complete! {batchStatus.processed} of {batchStatus.total} videos processed.
            </p>
          </div>
          <div className="space-y-3">
            {batchStatus.videos.map((video, i) => {
              const entry = entries[i] || {
                url: video.url,
                context: video.context,
                niche: video.niche,
                tags: video.tags,
                captureScreenshots: video.capture_screenshots,
                priority: video.priority,
                tagInput: '',
              }
              return (
                <VideoPreviewCard
                  key={video.url}
                  video={video}
                  entry={entry}
                  index={i}
                  onUpdateEntry={() => {}}
                  onRemove={() => {}}
                />
              )
            })}
          </div>
          <div className="flex justify-end">
            <Button onClick={onBack}>
              Back to Projects
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
