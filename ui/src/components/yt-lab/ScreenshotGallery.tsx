/**
 * Screenshot Gallery
 *
 * Displays a grid of analyzed screenshots from a YouTube video.
 * Each thumbnail shows the timestamp, classification badge, and relevance score.
 * Click to enlarge in a modal with full OCR text and analysis details.
 */

import { useState, useCallback, useEffect } from 'react'
import {
  Camera,
  X,
  Eye,
  Monitor,
  FileText,
  Star,
  MessageSquare,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import type { YTScreenshotCapture } from '@/lib/types'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ScreenshotGalleryProps {
  screenshots: YTScreenshotCapture[]
  summary?: string
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Format seconds into MM:SS or HH:MM:SS */
function formatTimestamp(totalSeconds: number): string {
  const total = Math.floor(totalSeconds)
  const hours = Math.floor(total / 3600)
  const minutes = Math.floor((total % 3600) / 60)
  const seconds = total % 60

  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
  }
  return `${minutes}:${String(seconds).padStart(2, '0')}`
}

/** Get display color for classification badge */
function classificationColor(classification: string): string {
  switch (classification) {
    case 'prompt': return 'bg-violet-500/20 text-violet-300 border-violet-500/30'
    case 'result': return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
    case 'dashboard': return 'bg-blue-500/20 text-blue-300 border-blue-500/30'
    case 'form': return 'bg-amber-500/20 text-amber-300 border-amber-500/30'
    case 'navigation': return 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30'
    default: return 'bg-muted text-muted-foreground border-border'
  }
}

/** Relevance score color */
function relevanceColor(score: number): string {
  if (score >= 8) return 'text-emerald-400'
  if (score >= 5) return 'text-amber-400'
  return 'text-muted-foreground'
}

// ---------------------------------------------------------------------------
// Lightbox Modal
// ---------------------------------------------------------------------------

function ScreenshotModal({
  screenshot,
  screenshots,
  currentIndex,
  onClose,
  onNavigate,
}: {
  screenshot: YTScreenshotCapture
  screenshots: YTScreenshotCapture[]
  currentIndex: number
  onClose: () => void
  onNavigate: (index: number) => void
}) {
  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
      if (e.key === 'ArrowLeft' && currentIndex > 0) onNavigate(currentIndex - 1)
      if (e.key === 'ArrowRight' && currentIndex < screenshots.length - 1) onNavigate(currentIndex + 1)
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [onClose, onNavigate, currentIndex, screenshots.length])

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
            <span className="text-sm font-mono text-muted-foreground">
              {formatTimestamp(screenshot.timestamp)}
            </span>
            <span className={`text-xs px-2 py-0.5 rounded-full border ${classificationColor(screenshot.classification)}`}>
              {screenshot.classification}
            </span>
            <span className={`text-xs font-medium flex items-center gap-1 ${relevanceColor(screenshot.relevance_score)}`}>
              <Star size={10} />
              {screenshot.relevance_score}/10
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">
              {currentIndex + 1} / {screenshots.length}
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

        {/* Image */}
        <div className="relative bg-black flex items-center justify-center min-h-[300px] max-h-[60vh]">
          <img
            src={screenshot.image_path}
            alt={screenshot.reason || `Screenshot at ${formatTimestamp(screenshot.timestamp)}`}
            className="max-w-full max-h-[60vh] object-contain"
          />

          {/* Navigation arrows */}
          {currentIndex > 0 && (
            <button
              onClick={() => onNavigate(currentIndex - 1)}
              className="absolute left-2 top-1/2 -translate-y-1/2 p-2 rounded-full bg-black/60 text-white hover:bg-black/80 transition-colors"
              aria-label="Previous screenshot"
            >
              <ChevronLeft size={20} />
            </button>
          )}
          {currentIndex < screenshots.length - 1 && (
            <button
              onClick={() => onNavigate(currentIndex + 1)}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-full bg-black/60 text-white hover:bg-black/80 transition-colors"
              aria-label="Next screenshot"
            >
              <ChevronRight size={20} />
            </button>
          )}
        </div>

        {/* Details */}
        <div className="p-4 space-y-3 max-h-[30vh] overflow-y-auto">
          {/* UI detected */}
          {screenshot.ui_detected && (
            <div className="flex items-start gap-2">
              <Monitor size={14} className="text-muted-foreground mt-0.5 shrink-0" />
              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">App / Interface</p>
                <p className="text-sm text-foreground">{screenshot.ui_detected}</p>
              </div>
            </div>
          )}

          {/* OCR text */}
          {screenshot.ocr_text && (
            <div className="flex items-start gap-2">
              <FileText size={14} className="text-muted-foreground mt-0.5 shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Visible Text (OCR)</p>
                <p className="text-sm text-foreground whitespace-pre-wrap break-words mt-0.5">{screenshot.ocr_text}</p>
              </div>
            </div>
          )}

          {/* Transcript context */}
          {screenshot.transcript_segment && (
            <div className="flex items-start gap-2">
              <MessageSquare size={14} className="text-muted-foreground mt-0.5 shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Transcript Context</p>
                <p className="text-sm text-muted-foreground italic mt-0.5">"{screenshot.transcript_segment}"</p>
              </div>
            </div>
          )}

          {/* Reason */}
          <div className="flex items-start gap-2">
            <Eye size={14} className="text-muted-foreground mt-0.5 shrink-0" />
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Capture Reason</p>
              <p className="text-xs text-muted-foreground mt-0.5">{screenshot.reason}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export function ScreenshotGallery({ screenshots, summary }: ScreenshotGalleryProps): React.JSX.Element | null {
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null)

  const handleClose = useCallback(() => setSelectedIndex(null), [])
  const handleNavigate = useCallback((index: number) => setSelectedIndex(index), [])

  if (screenshots.length === 0) return null

  const selectedScreenshot = selectedIndex !== null ? screenshots[selectedIndex] : null

  return (
    <div className="space-y-3">
      {/* Section header */}
      <div className="flex items-center justify-between">
        <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
          <Camera size={12} />
          Screenshots from Video ({screenshots.length})
        </label>
      </div>

      {/* Summary */}
      {summary && (
        <p className="text-xs text-muted-foreground bg-muted/30 rounded-md px-3 py-2 border border-border">
          {summary}
        </p>
      )}

      {/* Thumbnail grid */}
      <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-5 gap-2">
        {screenshots.map((ss, idx) => (
          <button
            key={`${ss.timestamp}-${idx}`}
            onClick={() => setSelectedIndex(idx)}
            className="group relative rounded-md border border-border bg-muted/30 overflow-hidden
              hover:border-primary/50 hover:shadow-md transition-all duration-200 text-left"
            aria-label={`View screenshot at ${formatTimestamp(ss.timestamp)}`}
          >
            {/* Thumbnail image */}
            <div className="aspect-video bg-black flex items-center justify-center">
              <img
                src={ss.image_path}
                alt={`Screenshot at ${formatTimestamp(ss.timestamp)}`}
                className="w-full h-full object-cover"
                loading="lazy"
              />
              {/* Hover overlay */}
              <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center">
                <Eye size={20} className="text-white opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            </div>

            {/* Info bar */}
            <div className="px-1.5 py-1 space-y-0.5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono text-muted-foreground">
                  {formatTimestamp(ss.timestamp)}
                </span>
                <span className={`text-[10px] font-medium ${relevanceColor(ss.relevance_score)}`}>
                  {ss.relevance_score}/10
                </span>
              </div>
              <span className={`text-[9px] px-1.5 py-0.5 rounded-full border inline-block ${classificationColor(ss.classification)}`}>
                {ss.classification}
              </span>
            </div>
          </button>
        ))}
      </div>

      {/* Click hint */}
      <p className="text-[10px] text-muted-foreground/60">
        Click to enlarge. OCR text and analysis shown in detail view.
      </p>

      {/* Modal */}
      {selectedScreenshot && selectedIndex !== null && (
        <ScreenshotModal
          screenshot={selectedScreenshot}
          screenshots={screenshots}
          currentIndex={selectedIndex}
          onClose={handleClose}
          onNavigate={handleNavigate}
        />
      )}
    </div>
  )
}
