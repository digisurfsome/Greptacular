/**
 * Capture Gallery
 *
 * Displays a grid of screen captures (screenshots and video clips) from an
 * execution session. Organized by step number with type indicators.
 *
 * Screenshots: click to enlarge in a lightbox modal.
 * Video clips: click to play inline using HTML5 <video>.
 * Full session recording: link to open in a new tab.
 */

import { useState, useCallback, useEffect, useMemo } from 'react'
import {
  Camera,
  Film,
  Video,
  X,
  Play,
  ChevronLeft,
  ChevronRight,
  Circle,
  Square,
} from 'lucide-react'
import type { YTCaptureItem, YTCaptureType, YTCaptureTrigger } from '@/lib/types'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface CaptureGalleryProps {
  captures: YTCaptureItem[]
  /** Base URL for fetching capture files (e.g., /api/yt-lab/execution/{id}/captures) */
  captureBaseUrl: string
  /** Current execution step number (used for manual capture attribution) */
  currentStepNumber?: number
  /** Whether session recording is active */
  isRecording?: boolean
  /** Callback to trigger manual capture */
  onManualCapture?: (stepNumber: number) => void
  /** Callbacks for session recording control */
  onStartRecording?: () => void
  onStopRecording?: () => void
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Icon component for capture type */
function CaptureTypeIcon({ type, size = 14 }: { type: YTCaptureType; size?: number }) {
  switch (type) {
    case 'screenshot':
      return <Camera size={size} />
    case 'clip':
      return <Film size={size} />
    case 'session':
      return <Video size={size} />
  }
}

/** Human-readable label for trigger reasons */
function triggerLabel(trigger: YTCaptureTrigger): string {
  switch (trigger) {
    case 'step_start': return 'Step Start'
    case 'step_complete': return 'Step Complete'
    case 'button_click': return 'Button Click'
    case 'form_fill': return 'Form Fill'
    case 'navigation': return 'Navigation'
    case 'user_pause': return 'Paused'
    case 'error': return 'Error'
    case 'manual': return 'Manual'
  }
}

/** Badge color for trigger type */
function triggerColor(trigger: YTCaptureTrigger): string {
  switch (trigger) {
    case 'step_start': return 'bg-blue-500/20 text-blue-300 border-blue-500/30'
    case 'step_complete': return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
    case 'button_click': return 'bg-violet-500/20 text-violet-300 border-violet-500/30'
    case 'form_fill': return 'bg-amber-500/20 text-amber-300 border-amber-500/30'
    case 'navigation': return 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30'
    case 'user_pause': return 'bg-orange-500/20 text-orange-300 border-orange-500/30'
    case 'error': return 'bg-red-500/20 text-red-300 border-red-500/30'
    case 'manual': return 'bg-muted text-muted-foreground border-border'
  }
}

/** Format seconds into MM:SS */
function formatTimestamp(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

/** Format duration for clips */
function formatDuration(seconds: number | null): string {
  if (seconds == null) return ''
  return `${seconds.toFixed(0)}s`
}

/** Build the URL for a capture file */
function captureFileUrl(baseUrl: string, captureId: string): string {
  return `${baseUrl}/${encodeURIComponent(captureId)}`
}

// ---------------------------------------------------------------------------
// Lightbox Modal (Screenshots)
// ---------------------------------------------------------------------------

function ScreenshotLightbox({
  capture,
  captures,
  currentIndex,
  baseUrl,
  onClose,
  onNavigate,
}: {
  capture: YTCaptureItem
  captures: YTCaptureItem[]
  currentIndex: number
  baseUrl: string
  onClose: () => void
  onNavigate: (index: number) => void
}) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
      if (e.key === 'ArrowLeft' && currentIndex > 0) onNavigate(currentIndex - 1)
      if (e.key === 'ArrowRight' && currentIndex < captures.length - 1) onNavigate(currentIndex + 1)
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [onClose, onNavigate, currentIndex, captures.length])

  const url = captureFileUrl(baseUrl, capture.id)

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative max-w-4xl w-full mx-4 bg-card border border-border rounded-lg overflow-hidden shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <div className="flex items-center gap-3">
            <CaptureTypeIcon type={capture.capture_type} size={14} />
            <span className="text-sm font-mono text-muted-foreground">
              Step {capture.step_number}
            </span>
            <span className={`text-xs px-2 py-0.5 rounded-full border ${triggerColor(capture.trigger)}`}>
              {triggerLabel(capture.trigger)}
            </span>
            <span className="text-xs text-muted-foreground">
              {formatTimestamp(capture.timestamp)}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">
              {currentIndex + 1} / {captures.length}
            </span>
            <button
              onClick={onClose}
              className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              aria-label="Close"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="relative bg-black flex items-center justify-center min-h-[300px] max-h-[70vh]">
          {capture.capture_type === 'screenshot' ? (
            <img
              src={url}
              alt={`${triggerLabel(capture.trigger)} at step ${capture.step_number}`}
              className="max-w-full max-h-[70vh] object-contain"
            />
          ) : (
            <video
              src={url}
              controls
              autoPlay
              className="max-w-full max-h-[70vh]"
            >
              Your browser does not support the video tag.
            </video>
          )}

          {/* Navigation arrows */}
          {currentIndex > 0 && (
            <button
              onClick={() => onNavigate(currentIndex - 1)}
              className="absolute left-2 top-1/2 -translate-y-1/2 p-2 rounded-full bg-black/60 text-white hover:bg-black/80 transition-colors"
              aria-label="Previous capture"
            >
              <ChevronLeft size={20} />
            </button>
          )}
          {currentIndex < captures.length - 1 && (
            <button
              onClick={() => onNavigate(currentIndex + 1)}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-full bg-black/60 text-white hover:bg-black/80 transition-colors"
              aria-label="Next capture"
            >
              <ChevronRight size={20} />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Step Group
// ---------------------------------------------------------------------------

function StepCaptureGroup({
  stepNumber,
  captures,
  baseUrl,
  onSelectCapture,
}: {
  stepNumber: number
  captures: YTCaptureItem[]
  baseUrl: string
  onSelectCapture: (capture: YTCaptureItem) => void
}) {
  return (
    <div className="space-y-2">
      <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
        Step {stepNumber}
      </h4>
      <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-5 gap-2">
        {captures.map((capture) => (
          <button
            key={capture.id}
            onClick={() => onSelectCapture(capture)}
            className="group relative rounded-md border border-border bg-muted/30 overflow-hidden
              hover:border-primary/50 hover:shadow-md transition-all duration-200 text-left"
            aria-label={`${capture.capture_type === 'screenshot' ? 'View screenshot' : 'Play clip'} — ${triggerLabel(capture.trigger)} at step ${capture.step_number}`}
          >
            {/* Thumbnail area */}
            <div className="aspect-video bg-black flex items-center justify-center relative">
              {capture.capture_type === 'screenshot' ? (
                <img
                  src={captureFileUrl(baseUrl, capture.id)}
                  alt={`Step ${capture.step_number} — ${triggerLabel(capture.trigger)}`}
                  className="w-full h-full object-cover"
                  loading="lazy"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center bg-muted/50">
                  <Play size={24} className="text-muted-foreground" />
                </div>
              )}

              {/* Hover overlay */}
              <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center">
                {capture.capture_type === 'screenshot' ? (
                  <Camera size={18} className="text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                ) : (
                  <Play size={18} className="text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                )}
              </div>

              {/* Duration badge for clips */}
              {capture.duration != null && (
                <span className="absolute bottom-1 right-1 text-[9px] bg-black/70 text-white px-1 rounded font-mono">
                  {formatDuration(capture.duration)}
                </span>
              )}
            </div>

            {/* Info bar */}
            <div className="px-1.5 py-1 space-y-0.5">
              <div className="flex items-center justify-between gap-1">
                <span className="flex items-center gap-1 text-[10px] text-muted-foreground">
                  <CaptureTypeIcon type={capture.capture_type} size={10} />
                  {formatTimestamp(capture.timestamp)}
                </span>
              </div>
              <span className={`text-[9px] px-1.5 py-0.5 rounded-full border inline-block ${triggerColor(capture.trigger)}`}>
                {triggerLabel(capture.trigger)}
              </span>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export function CaptureGallery({
  captures,
  captureBaseUrl,
  currentStepNumber = 1,
  isRecording = false,
  onManualCapture,
  onStartRecording,
  onStopRecording,
}: CaptureGalleryProps): React.JSX.Element | null {
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null)

  const handleClose = useCallback(() => setSelectedIndex(null), [])
  const handleNavigate = useCallback((index: number) => setSelectedIndex(index), [])

  // Group captures by step number, excluding session recordings
  const stepGroups = useMemo(() => {
    const nonSession = captures.filter((c) => c.capture_type !== 'session')
    const grouped = new Map<number, YTCaptureItem[]>()
    for (const c of nonSession) {
      const group = grouped.get(c.step_number) || []
      group.push(c)
      grouped.set(c.step_number, group)
    }
    return Array.from(grouped.entries()).sort(([a], [b]) => a - b)
  }, [captures])

  const sessionRecording = useMemo(
    () => captures.find((c) => c.capture_type === 'session'),
    [captures],
  )

  // Flat list for lightbox navigation (excluding session recordings)
  const flatCaptures = useMemo(
    () => captures.filter((c) => c.capture_type !== 'session'),
    [captures],
  )

  const handleSelectCapture = useCallback(
    (capture: YTCaptureItem) => {
      const idx = flatCaptures.findIndex((c) => c.id === capture.id)
      if (idx >= 0) setSelectedIndex(idx)
    },
    [flatCaptures],
  )

  const selectedCapture = selectedIndex !== null ? flatCaptures[selectedIndex] : null

  if (captures.length === 0 && !isRecording) return null

  return (
    <div className="space-y-4">
      {/* Section header */}
      <div className="flex items-center justify-between">
        <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
          <Camera size={12} />
          Execution Captures ({captures.length})
        </label>

        <div className="flex items-center gap-2">
          {/* Manual capture button */}
          {onManualCapture && (
            <button
              onClick={() => onManualCapture(currentStepNumber)}
              className="flex items-center gap-1 text-xs px-2 py-1 rounded-md border border-border
                text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            >
              <Camera size={12} />
              Capture
            </button>
          )}

          {/* Recording toggle */}
          {(onStartRecording || onStopRecording) && (
            isRecording ? (
              <button
                onClick={onStopRecording}
                className="flex items-center gap-1 text-xs px-2 py-1 rounded-md border border-red-500/30
                  text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-colors"
              >
                <Square size={10} className="fill-current" />
                Stop Recording
              </button>
            ) : (
              <button
                onClick={onStartRecording}
                className="flex items-center gap-1 text-xs px-2 py-1 rounded-md border border-border
                  text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              >
                <Circle size={10} className="text-red-400 fill-red-400" />
                Record Session
              </button>
            )
          )}
        </div>
      </div>

      {/* Recording indicator */}
      {isRecording && (
        <div className="flex items-center gap-2 text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-md px-3 py-2">
          <Circle size={8} className="fill-red-400 animate-pulse" />
          Full session recording in progress...
        </div>
      )}

      {/* Step groups */}
      {stepGroups.map(([stepNumber, stepCaptures]) => (
        <StepCaptureGroup
          key={stepNumber}
          stepNumber={stepNumber}
          captures={stepCaptures}
          baseUrl={captureBaseUrl}
          onSelectCapture={handleSelectCapture}
        />
      ))}

      {/* Session recording link */}
      {sessionRecording && (
        <div className="flex items-center gap-2 text-xs text-muted-foreground bg-muted/30 rounded-md px-3 py-2 border border-border">
          <Video size={14} />
          <a
            href={captureFileUrl(captureBaseUrl, sessionRecording.id)}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:underline"
          >
            Full session recording available
            {sessionRecording.duration != null && ` (${formatTimestamp(sessionRecording.duration)})`}
          </a>
        </div>
      )}

      {/* Click hint */}
      {flatCaptures.length > 0 && (
        <p className="text-[10px] text-muted-foreground/60">
          Click screenshots to enlarge. Click clips to play inline.
        </p>
      )}

      {/* Lightbox */}
      {selectedCapture && selectedIndex !== null && (
        <ScreenshotLightbox
          capture={selectedCapture}
          captures={flatCaptures}
          currentIndex={selectedIndex}
          baseUrl={captureBaseUrl}
          onClose={handleClose}
          onNavigate={handleNavigate}
        />
      )}
    </div>
  )
}
