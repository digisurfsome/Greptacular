/**
 * Video Ingest Panel
 *
 * Self-contained panel for importing YouTube videos into the YT Strategy Lab.
 * User pastes a YouTube URL and the system extracts transcript, metadata,
 * description links, and screenshot suggestions.
 *
 * Designed to be imported and used by YTStrategyLabPage. The panel manages
 * its own state and calls onIngestComplete when finished, passing the full
 * ingestion result to the parent.
 */

import { useState, useCallback, useRef, useEffect } from 'react'
import {
  Download,
  Loader2,
  CheckCircle2,
  Circle,
  Link2,
  Clock,
  Camera,
  FileText,
  AlertCircle,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Youtube,
} from 'lucide-react'
import type { YTIngestResponse } from '@/lib/types'
import { ingestYouTubeVideo } from '@/lib/api'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface VideoIngestPanelProps {
  /** Called with the full ingestion result when processing completes */
  onIngestComplete?: (result: YTIngestResponse) => void
  /** Pre-populate the URL field (e.g. from the project creation form) */
  initialUrl?: string
}

type IngestStep = 'idle' | 'fetching_metadata' | 'fetching_transcript' | 'analyzing' | 'done' | 'error'

interface StepConfig {
  label: string
  completedLabel: string
}

/** Maps each processing phase to its display labels */
const STEP_LABELS: Record<Exclude<IngestStep, 'idle' | 'done' | 'error'>, StepConfig> = {
  fetching_metadata: {
    label: 'Fetching video metadata...',
    completedLabel: 'Metadata fetched',
  },
  fetching_transcript: {
    label: 'Extracting transcript...',
    completedLabel: 'Transcript extracted',
  },
  analyzing: {
    label: 'Analyzing for screenshots & links...',
    completedLabel: 'Analysis complete',
  },
}

/** Ordered list of steps for display */
const STEP_ORDER: Array<Exclude<IngestStep, 'idle' | 'done' | 'error'>> = [
  'fetching_metadata',
  'fetching_transcript',
  'analyzing',
]

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Format seconds into MM:SS or HH:MM:SS */
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

/** Count total words across all transcript segments */
function countTranscriptWords(transcript: YTIngestResponse['transcript']): number {
  return transcript.reduce((sum, seg) => sum + seg.text.split(/\s+/).filter(Boolean).length, 0)
}

/** Basic YouTube URL validation */
function isValidYouTubeUrl(url: string): boolean {
  return /(?:youtube\.com\/(?:watch|embed|shorts|v\/)|youtu\.be\/)/.test(url)
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/** Renders a single status step with appropriate icon */
function StatusStep({
  step,
  currentStep,
  errorAtStep,
}: {
  step: Exclude<IngestStep, 'idle' | 'done' | 'error'>
  currentStep: IngestStep
  errorAtStep: IngestStep | null
}) {
  const stepIndex = STEP_ORDER.indexOf(step)

  // When in error state, use the step where the error occurred to determine progress
  const referenceStep = currentStep === 'error' && errorAtStep ? errorAtStep : currentStep
  const currentIndex = referenceStep === 'done'
    ? STEP_ORDER.length
    : referenceStep === 'error'
      ? -1
      : STEP_ORDER.indexOf(referenceStep as Exclude<IngestStep, 'idle' | 'done' | 'error'>)

  const isComplete = currentIndex > stepIndex || referenceStep === 'done'
  const isFailed = currentStep === 'error' && errorAtStep === step
  const isActive = currentStep === step
  const config = STEP_LABELS[step]

  return (
    <div className="flex items-center gap-2 text-sm">
      {isFailed ? (
        <AlertCircle size={16} className="text-destructive shrink-0" />
      ) : isComplete ? (
        <CheckCircle2 size={16} className="text-emerald-500 shrink-0" />
      ) : isActive ? (
        <Loader2 size={16} className="text-primary animate-spin shrink-0" />
      ) : (
        <Circle size={16} className="text-muted-foreground/40 shrink-0" />
      )}
      <span className={isFailed ? 'text-destructive' : isComplete ? 'text-foreground' : isActive ? 'text-foreground' : 'text-muted-foreground'}>
        {isFailed ? `Failed: ${config.label.replace('...', '')}` : isComplete ? config.completedLabel : isActive ? config.label : config.label.replace('...', '')}
      </span>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export function VideoIngestPanel({ onIngestComplete, initialUrl }: VideoIngestPanelProps): React.JSX.Element {
  const [url, setUrl] = useState(initialUrl ?? '')
  const [captureScreenshots, setCaptureScreenshots] = useState(false)
  const [currentStep, setCurrentStep] = useState<IngestStep>('idle')
  const [errorAtStep, setErrorAtStep] = useState<IngestStep | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [result, setResult] = useState<YTIngestResponse | null>(null)
  const [showTranscript, setShowTranscript] = useState(false)

  const isProcessing = currentStep !== 'idle' && currentStep !== 'done' && currentStep !== 'error'

  // Track latest step for error reporting and timer cleanup on unmount
  const currentStepRef = useRef(currentStep)
  useEffect(() => { currentStepRef.current = currentStep }, [currentStep])
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([])

  // Clean up timers on unmount
  useEffect(() => {
    return () => { timersRef.current.forEach(clearTimeout) }
  }, [])

  const handleImport = useCallback(async () => {
    const trimmedUrl = url.trim()

    if (!trimmedUrl) return

    if (!isValidYouTubeUrl(trimmedUrl)) {
      setErrorMessage('Please enter a valid YouTube URL')
      return
    }

    setErrorMessage(null)
    setErrorAtStep(null)
    setResult(null)
    setShowTranscript(false)

    // Simulate step progression. The backend does all processing in a single
    // call, but we show incremental feedback to keep the user informed.
    setCurrentStep('fetching_metadata')

    timersRef.current.forEach(clearTimeout)
    const t1 = setTimeout(() => setCurrentStep('fetching_transcript'), 800)
    const t2 = setTimeout(() => setCurrentStep('analyzing'), 1800)
    timersRef.current = [t1, t2]

    try {
      const response = await ingestYouTubeVideo(trimmedUrl, captureScreenshots)
      clearTimeout(t1)
      clearTimeout(t2)
      timersRef.current = []
      setCurrentStep('done')
      setResult(response)
      onIngestComplete?.(response)
    } catch (err) {
      clearTimeout(t1)
      clearTimeout(t2)
      timersRef.current = []
      setErrorAtStep(currentStepRef.current)
      setCurrentStep('error')
      setErrorMessage(err instanceof Error ? err.message : 'Failed to ingest video')
    }
  }, [url, captureScreenshots, onIngestComplete])

  const handleReset = useCallback(() => {
    setUrl('')
    setCurrentStep('idle')
    setErrorAtStep(null)
    setErrorMessage(null)
    setResult(null)
    setShowTranscript(false)
  }, [])

  return (
    <div className="rounded-lg border border-border bg-card">
      {/* Header */}
      <div className="flex items-center gap-2 border-b border-border px-4 py-3">
        <Download size={18} className="text-primary" />
        <h3 className="text-sm font-semibold text-foreground">Import from YouTube</h3>
      </div>

      <div className="p-4 space-y-4">
        {/* URL Input */}
        <div className="space-y-2">
          <label htmlFor="yt-url-input" className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            YouTube URL
          </label>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Youtube
                size={16}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
              />
              <input
                id="yt-url-input"
                type="url"
                value={url}
                onChange={(e) => {
                  setUrl(e.target.value)
                  if (errorMessage) setErrorMessage(null)
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !isProcessing) handleImport()
                }}
                placeholder="https://youtube.com/watch?v=..."
                disabled={isProcessing}
                className="w-full rounded-md border border-input bg-background px-3 py-2 pl-9 text-sm
                  text-foreground placeholder:text-muted-foreground
                  focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent
                  disabled:opacity-50 disabled:cursor-not-allowed"
              />
            </div>
            {currentStep === 'done' ? (
              <button
                onClick={handleReset}
                className="shrink-0 rounded-md bg-secondary px-4 py-2 text-sm font-medium
                  text-secondary-foreground hover:bg-secondary/80 transition-colors"
              >
                Reset
              </button>
            ) : (
              <button
                onClick={handleImport}
                disabled={isProcessing || !url.trim()}
                aria-label="Import YouTube video"
                className="shrink-0 rounded-md bg-primary px-4 py-2 text-sm font-medium
                  text-primary-foreground hover:bg-primary/90 transition-colors
                  disabled:opacity-50 disabled:cursor-not-allowed
                  flex items-center gap-2"
              >
                {isProcessing ? (
                  <>
                    <Loader2 size={14} className="animate-spin" />
                    Importing
                  </>
                ) : (
                  'Import'
                )}
              </button>
            )}
          </div>
        </div>

        {/* Screenshot toggle */}
        <label className="flex items-center gap-2 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={captureScreenshots}
            onChange={(e) => setCaptureScreenshots(e.target.checked)}
            disabled={isProcessing}
            className="h-4 w-4 rounded border-input text-primary focus:ring-ring
              disabled:opacity-50 disabled:cursor-not-allowed accent-primary"
          />
          <span className="text-sm text-muted-foreground flex items-center gap-1.5">
            <Camera size={14} />
            Capture screenshots at key moments
          </span>
        </label>

        {/* Error message */}
        {errorMessage && (
          <div className="flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2">
            <AlertCircle size={16} className="text-destructive shrink-0 mt-0.5" />
            <p className="text-sm text-destructive">{errorMessage}</p>
          </div>
        )}

        {/* Status steps — shown during/after processing */}
        {currentStep !== 'idle' && (
          <div className="space-y-1.5 border-t border-border pt-3">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Status</p>
            {STEP_ORDER.map((step) => (
              <StatusStep key={step} step={step} currentStep={currentStep} errorAtStep={errorAtStep} />
            ))}
          </div>
        )}

        {/* Result preview */}
        {result && (
          <div className="space-y-3 border-t border-border pt-3">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Preview</p>

            {/* Thumbnail + title */}
            <div className="flex gap-3">
              {result.thumbnail_url && (
                <img
                  src={result.thumbnail_url}
                  alt={`Thumbnail for ${result.title}`}
                  className="w-28 h-auto rounded-md border border-border object-cover shrink-0"
                />
              )}
              <div className="min-w-0 space-y-1">
                <p className="text-sm font-semibold text-foreground leading-snug line-clamp-2">
                  {result.title}
                </p>
                <p className="text-xs text-muted-foreground">{result.channel}</p>
              </div>
            </div>

            {/* Stats grid */}
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              <StatCard
                icon={<Clock size={14} />}
                label="Duration"
                value={formatDuration(result.duration)}
              />
              <StatCard
                icon={<FileText size={14} />}
                label="Transcript"
                value={result.transcript.length > 0
                  ? `${countTranscriptWords(result.transcript).toLocaleString()} words`
                  : 'Not available'}
              />
              <StatCard
                icon={<Link2 size={14} />}
                label="Links found"
                value={String(result.extracted_urls.length)}
              />
              <StatCard
                icon={<Camera size={14} />}
                label="Screenshot moments"
                value={String(result.screenshot_suggestions.length)}
              />
            </div>

            {/* Extracted URLs */}
            {result.extracted_urls.length > 0 && (
              <div className="space-y-1.5">
                <p className="text-xs font-medium text-muted-foreground">Links from description</p>
                <div className="max-h-24 overflow-y-auto space-y-1 rounded-md border border-border bg-muted/30 p-2">
                  {result.extracted_urls.map((link, i) => (
                    <a
                      key={i}
                      href={link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1.5 text-xs text-primary hover:underline truncate"
                    >
                      <ExternalLink size={10} className="shrink-0" />
                      <span className="truncate">{link}</span>
                    </a>
                  ))}
                </div>
              </div>
            )}

            {/* Transcript preview / toggle */}
            {result.transcript.length > 0 && (
              <div className="space-y-1.5">
                <button
                  onClick={() => setShowTranscript(!showTranscript)}
                  className="flex items-center gap-1.5 text-xs font-medium text-primary hover:text-primary/80 transition-colors"
                  aria-label={showTranscript ? 'Hide transcript' : 'Show full transcript'}
                >
                  {showTranscript ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  {showTranscript ? 'Hide Transcript' : 'View Full Transcript'}
                </button>
                {showTranscript && (
                  <div className="max-h-64 overflow-y-auto rounded-md border border-border bg-muted/30 p-3 text-xs text-foreground leading-relaxed space-y-1">
                    {result.transcript.map((seg, i) => (
                      <span key={i}>
                        <span className="text-muted-foreground font-mono text-[10px]">
                          [{formatDuration(Math.floor(seg.start))}]
                        </span>{' '}
                        {seg.text}{' '}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Stat Card (internal)
// ---------------------------------------------------------------------------

function StatCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode
  label: string
  value: string
}) {
  return (
    <div className="rounded-md border border-border bg-muted/30 px-3 py-2">
      <div className="flex items-center gap-1.5 text-muted-foreground mb-0.5">
        {icon}
        <span className="text-[10px] uppercase tracking-wider">{label}</span>
      </div>
      <p className="text-sm font-semibold text-foreground">{value}</p>
    </div>
  )
}
