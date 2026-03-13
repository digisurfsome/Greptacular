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
  Camera,
  AlertCircle,
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
  /** Extracted strategy steps — used for the Game Plan view */
  steps?: Array<{ title: string; description: string; order: number }>
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

export function VideoIngestPanel({ onIngestComplete, initialUrl, steps }: VideoIngestPanelProps): React.JSX.Element {
  const [url, setUrl] = useState(initialUrl ?? '')
  const [captureScreenshots, setCaptureScreenshots] = useState(false)
  const [currentStep, setCurrentStep] = useState<IngestStep>('idle')
  const [errorAtStep, setErrorAtStep] = useState<IngestStep | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [result, setResult] = useState<YTIngestResponse | null>(null)
  const [showTranscript, setShowTranscript] = useState(false)
  const [showGamePlan, setShowGamePlan] = useState(false)

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

  // ---- Compact mode: ingestion is complete ----
  if (result) {
    return (
      <div className="rounded-lg border border-border bg-card">
        {/* Compact header: thumbnail + title + stats inline */}
        <div className="flex items-center gap-3 px-4 py-3">
          {result.thumbnail_url && (
            <img
              src={result.thumbnail_url}
              alt={result.title}
              className="w-24 h-14 rounded border border-border object-cover shrink-0"
            />
          )}
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-foreground leading-snug truncate">
              {result.title}
            </p>
            <p className="text-xs text-muted-foreground">
              {result.channel} &middot; {formatDuration(result.duration)} &middot;{' '}
              {countTranscriptWords(result.transcript).toLocaleString()} words
              {result.extracted_urls.length > 0 && (
                <> &middot; {result.extracted_urls.length} links</>
              )}
            </p>
          </div>
          <button
            onClick={handleReset}
            className="shrink-0 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            Reset
          </button>
        </div>

        {/* Expandable content: links, transcript, game plan */}
        <div className="border-t border-border px-4 py-2 space-y-2">
          {/* Action buttons row */}
          <div className="flex items-center gap-3 flex-wrap">
            {result.transcript.length > 0 && (
              <button
                onClick={() => { setShowTranscript(!showTranscript); if (!showTranscript) setShowGamePlan(false) }}
                className="flex items-center gap-1.5 text-xs font-medium text-primary hover:text-primary/80 transition-colors"
              >
                {showTranscript ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                {showTranscript ? 'Hide Transcript' : 'View Transcript'}
              </button>
            )}
            {steps && steps.length > 0 && (
              <button
                onClick={() => { setShowGamePlan(!showGamePlan); if (!showGamePlan) setShowTranscript(false) }}
                className="flex items-center gap-1.5 text-xs font-medium text-primary hover:text-primary/80 transition-colors"
              >
                {showGamePlan ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                {showGamePlan ? 'Hide Game Plan' : 'View Game Plan'}
              </button>
            )}
            {result.extracted_urls.length > 0 && (
              <span className="text-xs text-muted-foreground flex items-center gap-1">
                <Link2 size={10} />
                {result.extracted_urls.map((link, i) => (
                  <a
                    key={i}
                    href={link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline truncate max-w-48 inline-block align-bottom"
                  >
                    {new URL(link).hostname.replace('www.', '')}
                  </a>
                )).reduce<React.ReactNode[]>((acc, el, i) => i === 0 ? [el] : [...acc, <span key={`sep-${i}`}>, </span>, el], [])}
              </span>
            )}
          </div>

          {/* Clean transcript — no timestamps */}
          {showTranscript && result.transcript.length > 0 && (
            <div className="max-h-72 overflow-y-auto rounded-md border border-border bg-muted/30 p-3 text-xs text-foreground leading-relaxed">
              {result.transcript.map((seg) => seg.text).join(' ')}
            </div>
          )}

          {/* Game Plan — structured step list */}
          {showGamePlan && steps && steps.length > 0 && (
            <div className="max-h-72 overflow-y-auto rounded-md border border-border bg-muted/30 p-3 space-y-2">
              {[...steps].sort((a, b) => a.order - b.order).map((step, i) => (
                <div key={i} className="flex gap-2">
                  <span className="text-xs font-bold text-primary shrink-0 w-5 text-right">{i + 1}.</span>
                  <div className="min-w-0">
                    <p className="text-xs font-semibold text-foreground">{step.title}</p>
                    {step.description && (
                      <p className="text-xs text-muted-foreground leading-relaxed">{step.description}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    )
  }

  // ---- Import mode: no result yet ----
  return (
    <div className="rounded-lg border border-border bg-card">
      {/* Header */}
      <div className="flex items-center gap-2 border-b border-border px-4 py-3">
        <Download size={18} className="text-primary" />
        <h3 className="text-sm font-semibold text-foreground">Import from YouTube</h3>
      </div>

      <div className="p-4 space-y-4">
        {/* URL Input */}
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
        </div>

        {/* Screenshot toggle — inline, compact */}
        <label className="flex items-center gap-2 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={captureScreenshots}
            onChange={(e) => setCaptureScreenshots(e.target.checked)}
            disabled={isProcessing}
            className="h-3.5 w-3.5 rounded border-input text-primary focus:ring-ring
              disabled:opacity-50 disabled:cursor-not-allowed accent-primary"
          />
          <span className="text-xs text-muted-foreground flex items-center gap-1">
            <Camera size={12} />
            Capture screenshots
          </span>
        </label>

        {/* Error message */}
        {errorMessage && (
          <div className="flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2">
            <AlertCircle size={16} className="text-destructive shrink-0 mt-0.5" />
            <p className="text-sm text-destructive">{errorMessage}</p>
          </div>
        )}

        {/* Status steps — shown during processing only (not after done) */}
        {currentStep !== 'idle' && currentStep !== 'done' && (
          <div className="space-y-1.5">
            {STEP_ORDER.map((step) => (
              <StatusStep key={step} step={step} currentStep={currentStep} errorAtStep={errorAtStep} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

