/**
 * QuadPreviewPage Component
 *
 * Standalone page for the quad-view preview without any modal chrome.
 * Shows all 4 pages in a 2x2 grid with controls for style switching,
 * modifiers, and accents. Click any quadrant to expand.
 *
 * Route: /#/quad-preview/:styleId
 * Optional params: ?modifiers=a,b&accent=c
 *
 * Used for:
 * - Direct links to quad-view comparison
 * - Shareable preview URLs
 */

import { useState, useEffect, useMemo, useCallback, useRef } from 'react'
import { ChevronLeft, ChevronRight, Maximize2, Grid2x2 } from 'lucide-react'
import { StylePreview } from './StylePreview'
import type { PreviewPage } from './StylePreview'
import type { StyleOption, StyleModifier } from '../lib/types'
import { listStyles, listStyleModifiers } from '../lib/api'

const PAGES: { id: PreviewPage; label: string }[] = [
  { id: 'landing', label: 'Landing' },
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'settings', label: 'Settings' },
  { id: 'feed', label: 'Feed' },
]

interface ParsedRoute {
  styleId: string
  modifiers: string[]
  accentId: string | null
}

function parseHash(): ParsedRoute | null {
  const hash = window.location.hash
  const match = hash.match(/^#\/quad-preview\/([^?]+)(?:\?(.*))?$/)
  if (!match) return null

  const styleId = decodeURIComponent(match[1])
  const params = new URLSearchParams(match[2] || '')
  const modifiers = params.get('modifiers')?.split(',').filter(Boolean) || []
  const accentId = params.get('accent') || null

  return { styleId, modifiers, accentId }
}

type ViewMode = 'quad' | 'single'

export function QuadPreviewPage() {
  const [styles, setStyles] = useState<StyleOption[] | null>(null)
  const [modifierDefs, setModifierDefs] = useState<StyleModifier[]>([])
  const [error, setError] = useState<string | null>(null)
  const [route, setRoute] = useState<ParsedRoute | null>(parseHash)

  const [currentStyleId, setCurrentStyleId] = useState<string>(route?.styleId || '')
  const [activeModifiers, setActiveModifiers] = useState<string[]>(route?.modifiers || [])
  const [activeAccentId, setActiveAccentId] = useState<string | null>(route?.accentId || null)
  const [viewMode, setViewMode] = useState<ViewMode>('quad')
  const [singlePage, setSinglePage] = useState<PreviewPage>('landing')

  // Dynamic scaling for quad view
  const INTERNAL_W = 1280
  const INTERNAL_H = 800
  const quadGridRef = useRef<HTMLDivElement>(null)
  const [quadScale, setQuadScale] = useState(0.4)

  useEffect(() => {
    if (viewMode !== 'quad' || !quadGridRef.current) return
    const el = quadGridRef.current
    const observer = new ResizeObserver((entries) => {
      const entry = entries[0]
      if (!entry) return
      const { width, height } = entry.contentRect
      const cellW = width / 2
      const cellH = height / 2
      const scale = Math.min(cellW / INTERNAL_W, cellH / INTERNAL_H)
      setQuadScale(Math.max(0.15, Math.min(1, scale)))
    })
    observer.observe(el)
    return () => observer.disconnect()
  }, [viewMode])

  // Listen for hash changes
  useEffect(() => {
    const handler = () => {
      const parsed = parseHash()
      setRoute(parsed)
      if (parsed) {
        setCurrentStyleId(parsed.styleId)
        setActiveModifiers(parsed.modifiers)
        setActiveAccentId(parsed.accentId)
      }
    }
    window.addEventListener('hashchange', handler)
    return () => window.removeEventListener('hashchange', handler)
  }, [])

  // Fetch all styles with tokens
  useEffect(() => {
    listStyles(true)
      .then(setStyles)
      .catch((err) => setError(err.message || 'Failed to load styles'))
    listStyleModifiers()
      .then(setModifierDefs)
      .catch(() => {}) // Modifiers are optional
  }, [])

  const resolvedStyle = useMemo(() => {
    if (!styles || !currentStyleId) return null
    return styles.find(s => s.id === currentStyleId) || null
  }, [styles, currentStyleId])

  const accentGuide = useMemo(() => {
    if (!styles || !activeAccentId) return undefined
    return styles.find(s => s.id === activeAccentId)?.style_guide
  }, [styles, activeAccentId])

  const currentStyleIndex = styles?.findIndex(s => s.id === currentStyleId) ?? -1

  const handleModifierToggle = (id: string) => {
    setActiveModifiers(prev =>
      prev.includes(id)
        ? prev.filter(m => m !== id)
        : prev.length < 3
          ? [...prev, id]
          : prev
    )
  }

  const handleAccentToggle = (id: string) => {
    setActiveAccentId(prev => prev === id ? null : id)
  }

  const prevStyle = useCallback(() => {
    if (styles && currentStyleIndex > 0) {
      setCurrentStyleId(styles[currentStyleIndex - 1].id)
    }
  }, [styles, currentStyleIndex])

  const nextStyle = useCallback(() => {
    if (styles && currentStyleIndex < styles.length - 1) {
      setCurrentStyleId(styles[currentStyleIndex + 1].id)
    }
  }, [styles, currentStyleIndex])

  // Keyboard navigation
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft') prevStyle()
      if (e.key === 'ArrowRight') nextStyle()
      if (e.key === 'Escape' && viewMode === 'single') setViewMode('quad')
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [prevStyle, nextStyle, viewMode])

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

  if (!route) {
    return (
      <div style={{ padding: 40, fontFamily: 'system-ui' }}>
        <h1>Quad Preview</h1>
        <p>Invalid URL. Expected format: <code>/#/quad-preview/:styleId</code></p>
        <p>Optional params: <code>?modifiers=high-contrast-buttons,larger-type&accent=cyberpunk</code></p>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ padding: 40, fontFamily: 'system-ui', color: '#dc2626' }}>
        <h1>Error</h1>
        <p>{error}</p>
      </div>
    )
  }

  if (!styles) {
    return (
      <div style={{ padding: 40, fontFamily: 'system-ui', textAlign: 'center' }}>
        <p>Loading styles...</p>
      </div>
    )
  }

  if (!resolvedStyle || !resolvedStyle.style_guide) {
    return (
      <div style={{ padding: 40, fontFamily: 'system-ui' }}>
        <h1>Style Not Found</h1>
        <p>No style with ID &quot;{currentStyleId}&quot; was found.</p>
        <p>Available styles: {styles.map(s => s.id).join(', ')}</p>
      </div>
    )
  }

  const styleGuide = resolvedStyle.style_guide

  return (
    <div className="w-screen h-screen flex flex-col bg-background text-foreground overflow-hidden">
      {/* Top controls bar */}
      <div className="flex items-center gap-3 px-4 py-2 border-b bg-muted/40 shrink-0">
        {/* Style navigation */}
        <div className="flex items-center gap-1.5 shrink-0">
          <button
            onClick={prevStyle}
            disabled={currentStyleIndex <= 0}
            className="p-1 rounded-md hover:bg-muted transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <ChevronLeft size={18} />
          </button>
          <span className="text-sm text-muted-foreground tabular-nums min-w-[3.5rem] text-center">
            {currentStyleIndex + 1} / {styles.length}
          </span>
          <button
            onClick={nextStyle}
            disabled={currentStyleIndex >= styles.length - 1}
            className="p-1 rounded-md hover:bg-muted transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <ChevronRight size={18} />
          </button>
        </div>

        {/* Style name */}
        <div className="min-w-0 mr-auto">
          <span className="text-sm font-semibold truncate">{resolvedStyle.name}</span>
          <span className="text-xs text-muted-foreground ml-2 hidden md:inline">{resolvedStyle.description}</span>
        </div>

        {/* View toggle */}
        <button
          onClick={() => setViewMode(viewMode === 'quad' ? 'single' : 'quad')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
            viewMode === 'quad'
              ? 'border-primary bg-primary/10 text-primary'
              : 'border-border text-muted-foreground hover:border-primary/50'
          }`}
        >
          {viewMode === 'quad' ? <Grid2x2 size={14} /> : <Maximize2 size={14} />}
          {viewMode === 'quad' ? 'Quad' : 'Single'}
        </button>
      </div>

      {/* Controls row: modifiers + accents */}
      {(modifierDefs.length > 0 || (styles && styles.length > 1)) && (
        <div className="flex items-center gap-4 px-4 py-1.5 border-b bg-muted/20 shrink-0 overflow-x-auto">
          {/* Modifiers */}
          {modifierDefs.length > 0 && (
            <div className="flex items-center gap-1.5 shrink-0">
              <span className="text-xs text-muted-foreground">Modifiers:</span>
              {modifierDefs.map((mod) => {
                const isActive = activeModifiers.includes(mod.id)
                return (
                  <button
                    key={mod.id}
                    onClick={() => handleModifierToggle(mod.id)}
                    className={`px-2.5 py-1 text-xs rounded-full border transition-colors ${
                      isActive
                        ? 'border-primary bg-primary/10 text-primary font-medium'
                        : 'border-border text-muted-foreground hover:border-primary/50'
                    }`}
                    title={mod.description}
                  >
                    {mod.name}
                  </button>
                )
              })}
            </div>
          )}

          {modifierDefs.length > 0 && styles.length > 1 && (
            <div className="w-px h-5 bg-border shrink-0" />
          )}

          {/* Accent selector */}
          {styles.length > 1 && (
            <div className="flex items-center gap-1.5 shrink-0">
              <span className="text-xs text-muted-foreground">Accent:</span>
              <button
                onClick={() => handleAccentToggle('')}
                className={`px-2.5 py-1 text-xs rounded-full border transition-colors ${
                  !activeAccentId
                    ? 'border-primary bg-primary/10 text-primary font-medium'
                    : 'border-border text-muted-foreground hover:border-primary/50'
                }`}
              >
                None
              </button>
              {styles
                .filter(s => s.id !== currentStyleId)
                .map((accent) => (
                  <button
                    key={accent.id}
                    onClick={() => handleAccentToggle(accent.id)}
                    className={`px-2.5 py-1 text-xs rounded-full border transition-colors whitespace-nowrap ${
                      activeAccentId === accent.id
                        ? 'border-primary bg-primary/10 text-primary font-medium'
                        : 'border-border text-muted-foreground hover:border-primary/50'
                    }`}
                  >
                    {accent.name}
                  </button>
                ))}
            </div>
          )}
        </div>
      )}

      {/* Single mode tab bar */}
      {viewMode === 'single' && (
        <div className="flex items-center border-b bg-muted/30 px-4 shrink-0">
          <button onClick={prevPage} className="p-1.5 rounded-md hover:bg-muted transition-colors mr-1">
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
          <button onClick={nextPage} className="p-1.5 rounded-md hover:bg-muted transition-colors ml-1">
            <ChevronRight size={16} />
          </button>
          <button
            onClick={() => setViewMode('quad')}
            className="ml-2 flex items-center gap-1 px-2.5 py-1 text-xs rounded-full border border-border text-muted-foreground hover:border-primary/50 transition-colors"
          >
            <Grid2x2 size={12} />
            Quad
          </button>
        </div>
      )}

      {/* Preview area */}
      {viewMode === 'quad' ? (
        <div
          ref={quadGridRef}
          className="flex-1 overflow-hidden grid grid-cols-1 sm:grid-cols-2"
        >
          {PAGES.map((page) => (
            <div
              key={page.id}
              className="relative overflow-hidden cursor-pointer group"
              style={{
                borderRight: page.id === 'landing' || page.id === 'settings' ? '1px solid var(--color-border)' : undefined,
                borderBottom: page.id === 'landing' || page.id === 'dashboard' ? '1px solid var(--color-border)' : undefined,
              }}
              onClick={() => {
                setSinglePage(page.id)
                setViewMode('single')
              }}
            >
              {/* Page label */}
              <div className="absolute top-2 left-2 z-10 px-2 py-0.5 rounded text-[10px] font-semibold bg-black/60 text-white backdrop-blur-sm pointer-events-none">
                {page.label}
              </div>
              {/* Expand icon on hover */}
              <div className="absolute top-2 right-2 z-10 opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded bg-black/60 text-white backdrop-blur-sm pointer-events-none">
                <Maximize2 size={12} />
              </div>
              {/* Scaled preview - dynamically fits quadrant */}
              <div
                style={{
                  width: `${INTERNAL_W}px`,
                  height: `${INTERNAL_H}px`,
                  transform: `scale(${quadScale})`,
                  transformOrigin: 'top left',
                  overflow: 'hidden',
                }}
              >
                <StylePreview
                  guide={styleGuide}
                  accentGuide={accentGuide}
                  modifiers={activeModifiers}
                  size="full"
                  styleName={resolvedStyle.name}
                  activePage={page.id}
                />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto">
          <StylePreview
            guide={styleGuide}
            accentGuide={accentGuide}
            modifiers={activeModifiers}
            size="full"
            styleName={resolvedStyle.name}
            activePage={singlePage}
          />
        </div>
      )}
    </div>
  )
}
