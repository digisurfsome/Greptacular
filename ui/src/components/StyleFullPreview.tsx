/**
 * StyleFullPreview Component
 *
 * Full-screen overlay that shows a complete mock app layout rendered in a
 * specific design style. Shows 4 tabbed pages (Landing, Dashboard, Settings,
 * Feed) with interactive modifier toggles and optional accent style mixing.
 *
 * Triggered by hovering/clicking a style card in the grid.
 */

import { useState } from 'react'
import { X, ChevronLeft, ChevronRight } from 'lucide-react'
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

interface StyleFullPreviewProps {
  guide: StyleGuide
  styleName: string
  styleDescription: string
  onSelect: () => void
  onClose: () => void
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
}

export function StyleFullPreview({
  guide,
  styleName,
  styleDescription,
  onSelect,
  onClose,
  modifiers,
  activeModifiers = [],
  onModifiersChange,
  accentStyles,
  activeAccentId = null,
  onAccentChange,
}: StyleFullPreviewProps) {
  const [activePage, setActivePage] = useState<PreviewPage>('landing')

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

  const pageIdx = PAGES.findIndex(p => p.id === activePage)
  const prevPage = () => {
    const idx = (pageIdx - 1 + PAGES.length) % PAGES.length
    setActivePage(PAGES[idx].id)
  }
  const nextPage = () => {
    const idx = (pageIdx + 1) % PAGES.length
    setActivePage(PAGES[idx].id)
  }

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center"
      onClick={onClose}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      {/* Content */}
      <div
        className="relative z-10 w-[95vw] h-[92vh] max-w-7xl rounded-xl overflow-hidden border border-border bg-background shadow-2xl flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header bar */}
        <div className="flex items-center justify-between px-6 py-3 border-b bg-background/95 backdrop-blur shrink-0">
          <div className="min-w-0">
            <h2 className="text-lg font-semibold truncate">{styleName}</h2>
            <p className="text-sm text-muted-foreground truncate">{styleDescription}</p>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            <Button onClick={onSelect}>
              Select This Style
            </Button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-md hover:bg-muted transition-colors"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Page tabs + navigation arrows */}
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
                onClick={() => setActivePage(page.id)}
                className={`px-4 py-2.5 text-sm font-medium transition-colors border-b-2 ${
                  activePage === page.id
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

          {/* Modifier toggles in the tab bar */}
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

        {/* Accent style selector strip */}
        {accentStyles && accentStyles.length > 0 && (
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
        <div className="flex-1 overflow-y-auto">
          <StylePreview
            guide={guide}
            accentGuide={accentGuide}
            modifiers={effectiveModifiers}
            size="full"
            styleName={styleName}
            activePage={activePage}
          />
        </div>
      </div>
    </div>
  )
}
