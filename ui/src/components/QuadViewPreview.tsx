/**
 * QuadViewPreview Component
 *
 * Shows all 4 sample pages (Landing, Dashboard, Settings, Feed) simultaneously
 * in a 2x2 grid. All pages respond to the same style, modifier, and accent
 * changes in real-time. Click any quadrant to expand it to full-screen single
 * page view.
 *
 * This is the default preview mode. Users can toggle to single-page view by
 * clicking a quadrant or using the view toggle.
 *
 * Supports:
 * - Left/right arrow keys to cycle through all 12 styles
 * - Style selector strip at the top
 * - Modifier toggles and accent selector
 * - Click any quadrant to go full-screen single page
 * - Responsive: 2x2 on desktop, 2x1 stacked on tablet, 1x1 stacked on mobile
 */

import { useState, useRef, useEffect, useCallback } from 'react'
import { X, ChevronLeft, ChevronRight, Maximize2, Grid2x2 } from 'lucide-react'
import { StylePreview } from './StylePreview'
import type { PreviewPage } from './StylePreview'
import { Button } from '@/components/ui/button'
import type { StyleGuide, StyleModifier, StyleOption } from '../lib/types'

const PAGES: { id: PreviewPage; label: string }[] = [
  { id: 'landing', label: 'Landing' },
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'settings', label: 'Settings' },
  { id: 'feed', label: 'Feed' },
]

/** Color swatches for the style selector strip */
const STYLE_SWATCHES: Record<string, string[]> = {
  'flat-design': ['#3B82F6', '#F8FAFC', '#0F172A'],
  'minimalism': ['#111827', '#FFFFFF', '#6B7280'],
  'neumorphism': ['#6366F1', '#E0E5EC', '#2D3748'],
  'glassmorphism': ['#A855F7', '#667eea', '#764ba2'],
  'skeuomorphism': ['#2563EB', '#F5F0EB', '#1A1A1A'],
  'neubrutalism': ['#FACC15', '#FFFBEB', '#18181B'],
  'bauhaus': ['#DC2626', '#FAFAFA', '#2563EB'],
  'claymorphism': ['#F59E0B', '#FFF7ED', '#292524'],
  'retro-futurism': ['#D946EF', '#0C0A1A', '#06B6D4'],
  'cyberpunk': ['#06B6D4', '#09090B', '#F43F5E'],
  'dark-mode': ['#3B82F6', '#0F172A', '#1E293B'],
  'warmer-shades': ['#D97706', '#FFFBF5', '#292524'],
}

type ViewMode = 'quad' | 'single'

interface QuadViewPreviewProps {
  guide: StyleGuide
  styleName: string
  styleDescription: string
  styleId: string
  onSelect: () => void
  onClose: () => void
  /** All available styles for the style selector strip */
  allStyles?: StyleOption[]
  /** Callback when user switches to a different style in the preview */
  onStyleChange?: (id: string) => void
  /** Available modifier definitions */
  modifiers?: StyleModifier[]
  /** Currently active modifier IDs (from parent state) */
  activeModifiers?: string[]
  /** Callback when modifiers change in the preview */
  onModifiersChange?: (ids: string[]) => void
  /** Available accent styles for mixing */
  accentStyles?: StyleOption[]
  /** Currently selected accent style ID */
  activeAccentId?: string | null
  /** Callback when accent changes in the preview */
  onAccentChange?: (id: string | null) => void
  /** Initial view mode (defaults to 'quad') */
  initialViewMode?: ViewMode
}

export function QuadViewPreview({
  guide,
  styleName,
  styleDescription,
  styleId,
  onSelect,
  onClose,
  allStyles,
  onStyleChange,
  modifiers,
  activeModifiers = [],
  onModifiersChange,
  accentStyles,
  activeAccentId = null,
  onAccentChange,
  initialViewMode = 'quad',
}: QuadViewPreviewProps) {
  const [viewMode, setViewMode] = useState<ViewMode>(initialViewMode)
  const [singlePage, setSinglePage] = useState<PreviewPage>('landing')
  const styleSelectorRef = useRef<HTMLDivElement>(null)

  // Scroll active style button into view
  useEffect(() => {
    if (!styleSelectorRef.current) return
    const active = styleSelectorRef.current.querySelector('[data-active="true"]')
    if (active) {
      active.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' })
    }
  }, [styleId])

  // Find current style index for arrow key navigation
  const currentStyleIndex = allStyles?.findIndex(s => s.id === styleId) ?? -1

  // Keyboard: Escape to close, Arrow keys to navigate styles, G to toggle view
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      if (viewMode === 'single') {
        setViewMode('quad')
      } else {
        onClose()
      }
    }
    if (e.key === 'ArrowLeft' && allStyles && onStyleChange && currentStyleIndex > 0) {
      onStyleChange(allStyles[currentStyleIndex - 1].id)
    }
    if (e.key === 'ArrowRight' && allStyles && onStyleChange && currentStyleIndex < allStyles.length - 1) {
      onStyleChange(allStyles[currentStyleIndex + 1].id)
    }
  }, [onClose, viewMode, allStyles, onStyleChange, currentStyleIndex])

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  // Local modifier state if parent doesn't control it
  const [localModifiers, setLocalModifiers] = useState<string[]>(activeModifiers)
  const effectiveModifiers = onModifiersChange ? activeModifiers : localModifiers
  const handleModifierToggle = (id: string) => {
    const next = effectiveModifiers.includes(id)
      ? effectiveModifiers.filter(m => m !== id)
      : effectiveModifiers.length < 3
        ? [...effectiveModifiers, id]
        : effectiveModifiers
    if (onModifiersChange) {
      onModifiersChange(next)
    } else {
      setLocalModifiers(next)
    }
  }

  // Local accent state if parent doesn't control it
  const [localAccentId, setLocalAccentId] = useState<string | null>(activeAccentId)
  const effectiveAccentId = onAccentChange ? activeAccentId : localAccentId
  const handleAccentToggle = (id: string) => {
    const next = effectiveAccentId === id ? null : id
    if (onAccentChange) {
      onAccentChange(next)
    } else {
      setLocalAccentId(next)
    }
  }

  // Resolve accent guide from accent styles
  const accentGuide = effectiveAccentId
    ? accentStyles?.find(s => s.id === effectiveAccentId)?.style_guide
    : undefined

  // Single-page navigation
  const pageIdx = PAGES.findIndex(p => p.id === singlePage)
  const prevPage = () => {
    const idx = (pageIdx - 1 + PAGES.length) % PAGES.length
    setSinglePage(PAGES[idx].id)
  }
  const nextPage = () => {
    const idx = (pageIdx + 1) % PAGES.length
    setSinglePage(PAGES[idx].id)
  }

  // Style navigation (for prev/next arrows)
  const prevStyle = () => {
    if (allStyles && onStyleChange && currentStyleIndex > 0) {
      onStyleChange(allStyles[currentStyleIndex - 1].id)
    }
  }
  const nextStyle = () => {
    if (allStyles && onStyleChange && currentStyleIndex < (allStyles?.length ?? 0) - 1) {
      onStyleChange(allStyles[currentStyleIndex + 1].id)
    }
  }

  // Dynamic scaling for quad view: measure grid container, compute scale to fit
  const INTERNAL_W = 1280
  const INTERNAL_H = 800
  const quadGridRef = useRef<HTMLDivElement>(null)
  const [quadScale, setQuadScale] = useState(0.4)

  useEffect(() => {
    if (viewMode !== 'quad' || !quadGridRef.current) return
    const el = quadGridRef.current
    const update = () => {
      const { clientWidth, clientHeight } = el
      if (clientWidth === 0 || clientHeight === 0) return
      const cellW = clientWidth / 2
      const cellH = clientHeight / 2
      const scale = Math.min(cellW / INTERNAL_W, cellH / INTERNAL_H)
      setQuadScale(Math.max(0.15, Math.min(1, scale)))
    }
    update() // Immediate first calculation
    const observer = new ResizeObserver(() => update())
    observer.observe(el)
    return () => observer.disconnect()
  }, [viewMode])

  const handleQuadrantClick = (page: PreviewPage) => {
    setSinglePage(page)
    setViewMode('single')
  }

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center"
      onClick={onClose}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />

      {/* Content */}
      <div
        className="relative z-10 w-[95vw] h-[94vh] max-w-7xl rounded-xl overflow-hidden border border-border bg-background shadow-2xl flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Style selector strip across the top */}
        {allStyles && allStyles.length > 0 && (
          <div
            ref={styleSelectorRef}
            className="flex items-center gap-1 px-3 py-2 border-b bg-muted/40 shrink-0 overflow-x-auto scrollbar-thin"
          >
            {allStyles.map((s) => {
              const isActive = s.id === styleId
              const swatches = STYLE_SWATCHES[s.id] || ['#888', '#ccc', '#333']
              return (
                <button
                  key={s.id}
                  data-active={isActive}
                  onClick={() => onStyleChange?.(s.id)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all shrink-0 ${
                    isActive
                      ? 'bg-primary text-primary-foreground shadow-sm'
                      : 'bg-background border border-border text-muted-foreground hover:text-foreground hover:border-primary/50'
                  }`}
                  title={s.description}
                >
                  <div className="flex gap-0.5">
                    {swatches.map((color, i) => (
                      <div
                        key={i}
                        className="w-3 h-3 rounded-sm"
                        style={{
                          backgroundColor: color,
                          border: isActive ? '1px solid rgba(255,255,255,0.3)' : '1px solid rgba(0,0,0,0.1)',
                        }}
                      />
                    ))}
                  </div>
                  {s.name}
                </button>
              )
            })}
          </div>
        )}

        {/* Header bar */}
        <div className="flex items-center justify-between px-6 py-2.5 border-b bg-background/95 backdrop-blur shrink-0">
          <div className="flex items-center gap-4 min-w-0">
            {/* Style counter + arrows (quad mode) */}
            {viewMode === 'quad' && allStyles && allStyles.length > 1 && (
              <div className="flex items-center gap-1.5 shrink-0">
                <button
                  onClick={prevStyle}
                  disabled={currentStyleIndex <= 0}
                  className="p-1 rounded-md hover:bg-muted transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                  aria-label="Previous style"
                >
                  <ChevronLeft size={18} />
                </button>
                <span className="text-sm text-muted-foreground tabular-nums min-w-[3.5rem] text-center">
                  {currentStyleIndex + 1} / {allStyles.length}
                </span>
                <button
                  onClick={nextStyle}
                  disabled={currentStyleIndex >= allStyles.length - 1}
                  className="p-1 rounded-md hover:bg-muted transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                  aria-label="Next style"
                >
                  <ChevronRight size={18} />
                </button>
              </div>
            )}
            <div className="min-w-0">
              <h2 className="text-lg font-semibold truncate">{styleName}</h2>
              <p className="text-xs text-muted-foreground truncate">{styleDescription}</p>
            </div>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            {/* View mode toggle */}
            <button
              onClick={() => setViewMode(viewMode === 'quad' ? 'single' : 'quad')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                viewMode === 'quad'
                  ? 'border-primary bg-primary/10 text-primary'
                  : 'border-border text-muted-foreground hover:border-primary/50 hover:text-foreground'
              }`}
              title={viewMode === 'quad' ? 'Switch to single page view' : 'Switch to quad view'}
            >
              {viewMode === 'quad' ? (
                <>
                  <Grid2x2 size={14} />
                  Quad View
                </>
              ) : (
                <>
                  <Maximize2 size={14} />
                  Single View
                </>
              )}
            </button>
            <Button onClick={onSelect}>
              Select This Style
            </Button>
            <button
              onClick={(e) => {
                e.stopPropagation()
                onClose()
              }}
              className="p-2 rounded-md hover:bg-muted transition-colors"
              aria-label="Close preview"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Single-page tabs + navigation (only in single mode) */}
        {viewMode === 'single' && (
          <div className="flex items-center border-b bg-muted/30 px-4 shrink-0">
            <button
              onClick={prevPage}
              className="p-1.5 rounded-md hover:bg-muted transition-colors mr-1"
              aria-label="Previous page"
            >
              <ChevronLeft size={16} />
            </button>
            <div className="flex gap-0.5">
              {PAGES.map((page) => (
                <button
                  key={page.id}
                  onClick={() => setSinglePage(page.id)}
                  className={`px-4 py-2.5 text-sm font-medium transition-colors border-b-2 ${
                    singlePage === page.id
                      ? 'border-primary text-primary'
                      : 'border-transparent text-muted-foreground hover:text-foreground'
                  }`}
                >
                  {page.label}
                </button>
              ))}
            </div>
            <button
              onClick={nextPage}
              className="p-1.5 rounded-md hover:bg-muted transition-colors ml-1"
              aria-label="Next page"
            >
              <ChevronRight size={16} />
            </button>

            {/* Back to quad view */}
            <button
              onClick={() => setViewMode('quad')}
              className="ml-2 flex items-center gap-1 px-2.5 py-1 text-xs rounded-full border border-border text-muted-foreground hover:border-primary/50 hover:text-foreground transition-colors"
            >
              <Grid2x2 size={12} />
              Quad
            </button>

            {/* Modifier toggles in single mode */}
            {modifiers && modifiers.length > 0 && (
              <div className="ml-auto flex items-center gap-1.5">
                <span className="text-xs text-muted-foreground mr-1">Modifiers:</span>
                {modifiers.map((mod) => {
                  const isActive = effectiveModifiers.includes(mod.id)
                  return (
                    <button
                      key={mod.id}
                      onClick={() => handleModifierToggle(mod.id)}
                      className={`px-2.5 py-1 text-xs rounded-full border transition-colors ${
                        isActive
                          ? 'border-primary bg-primary/10 text-primary font-medium'
                          : 'border-border text-muted-foreground hover:border-primary/50 hover:text-foreground'
                      }`}
                      title={mod.description}
                    >
                      {mod.name}
                    </button>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {/* Modifier + accent controls bar (quad mode - shown below header) */}
        {viewMode === 'quad' && (modifiers?.length || accentStyles?.length) && (
          <div className="flex items-center gap-4 px-4 py-2 border-b bg-muted/20 shrink-0 overflow-x-auto">
            {/* Modifier toggles */}
            {modifiers && modifiers.length > 0 && (
              <div className="flex items-center gap-1.5 shrink-0">
                <span className="text-xs text-muted-foreground mr-1">Modifiers:</span>
                {modifiers.map((mod) => {
                  const isActive = effectiveModifiers.includes(mod.id)
                  return (
                    <button
                      key={mod.id}
                      onClick={() => handleModifierToggle(mod.id)}
                      className={`px-2.5 py-1 text-xs rounded-full border transition-colors ${
                        isActive
                          ? 'border-primary bg-primary/10 text-primary font-medium'
                          : 'border-border text-muted-foreground hover:border-primary/50 hover:text-foreground'
                      }`}
                      title={mod.description}
                    >
                      {mod.name}
                    </button>
                  )
                })}
              </div>
            )}

            {/* Divider */}
            {modifiers?.length && accentStyles?.length ? (
              <div className="w-px h-5 bg-border shrink-0" />
            ) : null}

            {/* Accent style selector */}
            {accentStyles && accentStyles.length > 0 && (
              <div className="flex items-center gap-1.5 shrink-0">
                <span className="text-xs text-muted-foreground whitespace-nowrap">Accent:</span>
                <button
                  onClick={() => handleAccentToggle('')}
                  className={`px-2.5 py-1 text-xs rounded-full border transition-colors ${
                    !effectiveAccentId
                      ? 'border-primary bg-primary/10 text-primary font-medium'
                      : 'border-border text-muted-foreground hover:border-primary/50'
                  }`}
                >
                  None
                </button>
                {accentStyles.map((accent) => (
                  <button
                    key={accent.id}
                    onClick={() => handleAccentToggle(accent.id)}
                    className={`px-2.5 py-1 text-xs rounded-full border transition-colors whitespace-nowrap ${
                      effectiveAccentId === accent.id
                        ? 'border-primary bg-primary/10 text-primary font-medium'
                        : 'border-border text-muted-foreground hover:border-primary/50'
                    }`}
                    title={accent.description}
                  >
                    {accent.name}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Accent style selector strip (single mode) */}
        {viewMode === 'single' && accentStyles && accentStyles.length > 0 && (
          <div className="flex items-center gap-2 px-4 py-2 border-b bg-muted/20 shrink-0 overflow-x-auto">
            <span className="text-xs text-muted-foreground whitespace-nowrap">Accent:</span>
            <button
              onClick={() => handleAccentToggle('')}
              className={`px-2.5 py-1 text-xs rounded-full border transition-colors ${
                !effectiveAccentId
                  ? 'border-primary bg-primary/10 text-primary font-medium'
                  : 'border-border text-muted-foreground hover:border-primary/50'
              }`}
            >
              None
            </button>
            {accentStyles.map((accent) => (
              <button
                key={accent.id}
                onClick={() => handleAccentToggle(accent.id)}
                className={`px-2.5 py-1 text-xs rounded-full border transition-colors whitespace-nowrap ${
                  effectiveAccentId === accent.id
                    ? 'border-primary bg-primary/10 text-primary font-medium'
                    : 'border-border text-muted-foreground hover:border-primary/50'
                }`}
                title={accent.description}
              >
                {accent.name}
              </button>
            ))}
          </div>
        )}

        {/* Preview area */}
        {viewMode === 'quad' ? (
          (() => {
            const quadPages: { id: PreviewPage; label: string; top: string; left: string }[] = [
              { id: 'landing', label: 'Landing', top: '0', left: '0' },
              { id: 'dashboard', label: 'Dashboard', top: '0', left: '50%' },
              { id: 'settings', label: 'Settings', top: '50%', left: '0' },
              { id: 'feed', label: 'Feed', top: '50%', left: '50%' },
            ]
            return (
              <div
                ref={quadGridRef}
                className="relative w-full flex-1"
              >
                {quadPages.map((page) => (
                  <div
                    key={page.id}
                    className="absolute overflow-hidden cursor-pointer group"
                    style={{
                      top: page.top,
                      left: page.left,
                      width: '50%',
                      height: '50%',
                      borderRight: page.left === '0' ? '1px solid var(--color-border)' : undefined,
                      borderBottom: page.top === '0' ? '1px solid var(--color-border)' : undefined,
                    }}
                    onClick={() => handleQuadrantClick(page.id)}
                  >
                    {/* Page label overlay */}
                    <div className="absolute top-2 left-2 z-10 px-2 py-0.5 rounded text-[10px] font-semibold bg-black/60 text-white backdrop-blur-sm pointer-events-none">
                      {page.label}
                    </div>

                    {/* Expand icon on hover */}
                    <div className="absolute top-2 right-2 z-10 opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded bg-black/60 text-white backdrop-blur-sm pointer-events-none">
                      <Maximize2 size={12} />
                    </div>

                    {/* Scaled-down preview - render at full size then scale to fit quadrant */}
                    <div
                      style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: `${INTERNAL_W}px`,
                        height: `${INTERNAL_H}px`,
                        transform: `scale(${quadScale})`,
                        transformOrigin: 'top left',
                      }}
                    >
                      <StylePreview
                        guide={guide}
                        accentGuide={accentGuide}
                        modifiers={effectiveModifiers}
                        size="full"
                        styleName={styleName}
                        activePage={page.id}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )
          })()
        ) : (
          /* Single page view */
          <div className="flex-1 overflow-y-auto">
            <StylePreview
              guide={guide}
              accentGuide={accentGuide}
              modifiers={effectiveModifiers}
              size="full"
              styleName={styleName}
              activePage={singlePage}
            />
          </div>
        )}
      </div>
    </div>
  )
}
