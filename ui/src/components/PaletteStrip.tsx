/**
 * PaletteStrip Component
 *
 * Horizontal scrollable strip of color palette presets. Each thumbnail shows
 * the palette's 6 color dots and name. Clicking a palette selects it and
 * populates the color customizer with that palette's colors.
 *
 * Renders inside the ColorCustomizer section, above the individual pickers.
 */

import { useRef } from 'react'
import { ChevronLeft, ChevronRight, Lock } from 'lucide-react'
import { PALETTES, PALETTE_CATEGORIES, type PaletteData } from '../data/palettes'

interface PaletteStripProps {
  selectedId: string | null
  onSelect: (palette: PaletteData) => void
}

/** Single palette thumbnail: 6 color dots + name */
function PaletteThumbnail({
  palette,
  isSelected,
  onSelect,
}: {
  palette: PaletteData
  isSelected: boolean
  onSelect: () => void
}) {
  const colors = [
    palette.brand,
    palette.background,
    palette.surface,
    palette.text,
    palette.accent,
    palette.muted,
  ]
  const isPremium = palette.tier === 'premium'

  return (
    <button
      type="button"
      onClick={onSelect}
      title={`${palette.name} – ${palette.vibe}`}
      className={`
        shrink-0 flex flex-col items-center gap-0.5 px-1.5 py-1 rounded border transition-all
        ${isSelected
          ? 'border-primary bg-primary/5 ring-1 ring-primary/30'
          : 'border-transparent hover:border-border hover:bg-muted/30'
        }
      `}
    >
      <div className="flex gap-0.5 relative">
        {colors.map((c, i) => (
          <span
            key={i}
            className="w-2.5 h-2.5 rounded-full border border-black/10 shrink-0"
            style={{ backgroundColor: c }}
          />
        ))}
        {isPremium && (
          <span className="absolute -top-1 -right-1.5">
            <Lock size={7} className="text-muted-foreground" />
          </span>
        )}
      </div>
      <span className="text-[8px] leading-tight text-muted-foreground whitespace-nowrap max-w-[60px] truncate">
        {palette.name}
      </span>
    </button>
  )
}

export function PaletteStrip({ selectedId, onSelect }: PaletteStripProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  const scroll = (direction: 'left' | 'right') => {
    if (!scrollRef.current) return
    const amount = 200
    scrollRef.current.scrollBy({
      left: direction === 'left' ? -amount : amount,
      behavior: 'smooth',
    })
  }

  return (
    <div className="space-y-1.5">
      <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
        Quick Palette Presets
      </span>

      <div className="relative group">
        {/* Left scroll arrow */}
        <button
          type="button"
          onClick={() => scroll('left')}
          className="absolute left-0 top-0 bottom-0 z-10 w-5 flex items-center justify-center bg-gradient-to-r from-background to-transparent opacity-0 group-hover:opacity-100 transition-opacity"
          tabIndex={-1}
        >
          <ChevronLeft size={12} />
        </button>

        {/* Scrollable strip */}
        <div
          ref={scrollRef}
          className="flex gap-0.5 overflow-x-auto scrollbar-hide pb-1"
          style={{ scrollbarWidth: 'none' }}
        >
          {PALETTE_CATEGORIES.map(category => {
            const palettes = PALETTES.filter(p => p.category === category)
            if (palettes.length === 0) return null
            return (
              <div key={category} className="flex items-center gap-0.5 shrink-0">
                <span className="text-[8px] font-medium text-muted-foreground/50 -rotate-90 w-3 whitespace-nowrap">
                  {category.slice(0, 4)}
                </span>
                {palettes.map(palette => (
                  <PaletteThumbnail
                    key={palette.id}
                    palette={palette}
                    isSelected={selectedId === palette.id}
                    onSelect={() => onSelect(palette)}
                  />
                ))}
              </div>
            )
          })}
        </div>

        {/* Right scroll arrow */}
        <button
          type="button"
          onClick={() => scroll('right')}
          className="absolute right-0 top-0 bottom-0 z-10 w-5 flex items-center justify-center bg-gradient-to-l from-background to-transparent opacity-0 group-hover:opacity-100 transition-opacity"
          tabIndex={-1}
        >
          <ChevronRight size={12} />
        </button>
      </div>
    </div>
  )
}
