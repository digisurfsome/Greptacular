/**
 * ColorCustomizer Component
 *
 * Allows users to customize individual colors within a chosen design style.
 * Shows the 6 main color tokens (primary, secondary, accent, background, surface, text)
 * with color picker inputs and hex value displays. Collapsed by default.
 *
 * Includes a PaletteStrip for quick preset selection that populates all 6 colors at once.
 */

import { useState } from 'react'
import { RotateCcw, ChevronDown, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { PaletteStrip } from './PaletteStrip'
import { paletteToCustomColors } from '../lib/paletteUtils'
import type { PaletteData } from '../data/palettes'
import type { StyleGuide } from '../lib/types'

/** The 6 main customizable color keys and their labels */
const COLOR_FIELDS = [
  { key: 'primary', label: 'Primary', path: ['brand', 'DEFAULT'] },
  { key: 'secondary', label: 'Secondary', path: ['brand', 'dark'] },
  { key: 'accent', label: 'Accent', path: ['brand', 'light'] },
  { key: 'background', label: 'Background', path: ['surface', 'canvas'] },
  { key: 'surface', label: 'Surface', path: ['surface', 'base'] },
  { key: 'text', label: 'Text', path: ['text', 'primary'] },
] as const

type CustomColors = Record<string, string>

interface ColorCustomizerProps {
  styleGuide: StyleGuide
  customColors: CustomColors
  onChange: (colors: CustomColors) => void
  selectedPaletteId: string | null
  onPaletteSelect: (paletteId: string | null) => void
}

/** Get the default value for a color field from the style guide tokens */
function getDefaultColor(guide: StyleGuide, path: readonly string[]): string {
  const group = guide.color_tokens[path[0]]
  if (group && typeof group === 'object' && path[1] in (group as Record<string, unknown>)) {
    const val = (group as Record<string, string>)[path[1]]
    // Only return hex-like values for the color picker
    if (typeof val === 'string' && val.startsWith('#')) return val
  }
  return '#888888'
}

/** Check if a value is a valid hex color */
function isValidHex(value: string): boolean {
  return /^#[0-9A-Fa-f]{6}$/.test(value)
}

export function ColorCustomizer({ styleGuide, customColors, onChange, selectedPaletteId, onPaletteSelect }: ColorCustomizerProps) {
  const [isOpen, setIsOpen] = useState(true)

  const hasChanges = Object.keys(customColors).length > 0

  const handleColorChange = (key: string, value: string) => {
    const next = { ...customColors }
    const field = COLOR_FIELDS.find(f => f.key === key)
    if (!field) return

    const defaultValue = getDefaultColor(styleGuide, field.path)
    if (value === defaultValue) {
      delete next[key]
    } else {
      next[key] = value
    }
    // Manual edit clears the palette selection
    onPaletteSelect(null)
    onChange(next)
  }

  const handlePaletteSelect = (palette: PaletteData) => {
    onPaletteSelect(palette.id)
    onChange(paletteToCustomColors(palette))
  }

  const handleReset = () => {
    onPaletteSelect(null)
    onChange({})
  }

  return (
    <div className="space-y-2 border-t pt-3 mt-1">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 w-full text-left"
      >
        {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        <span className="text-sm font-medium">Customize Colors</span>
        <Badge variant="secondary" className="text-[10px]">Optional</Badge>
        {hasChanges && (
          <span className="text-[10px] text-primary ml-auto">Modified</span>
        )}
      </button>

      {isOpen && (
        <div className="space-y-3 pl-5">
          <p className="text-xs text-muted-foreground">
            Pick a palette preset or tweak individual colors.
          </p>

          {/* Palette preset strip */}
          <PaletteStrip
            selectedId={selectedPaletteId}
            onSelect={handlePaletteSelect}
          />

          <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
            {COLOR_FIELDS.map(({ key, label, path }) => {
              const defaultValue = getDefaultColor(styleGuide, path)
              const currentValue = customColors[key] || defaultValue
              const isModified = key in customColors

              return (
                <div key={key} className="flex items-center gap-2">
                  <div className="relative">
                    <input
                      type="color"
                      value={currentValue}
                      onChange={(e) => handleColorChange(key, e.target.value)}
                      className="w-8 h-8 rounded border border-border cursor-pointer p-0 bg-transparent [&::-webkit-color-swatch-wrapper]:p-0.5 [&::-webkit-color-swatch]:rounded-sm [&::-webkit-color-swatch]:border-0"
                    />
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-1">
                      <span className="text-xs font-medium">{label}</span>
                      {isModified && (
                        <span className="w-1.5 h-1.5 rounded-full bg-primary shrink-0" />
                      )}
                    </div>
                    <input
                      type="text"
                      value={currentValue}
                      onChange={(e) => {
                        const val = e.target.value
                        if (isValidHex(val)) handleColorChange(key, val)
                      }}
                      placeholder="#000000"
                      className="text-[10px] text-muted-foreground font-mono w-[72px] bg-transparent border-none p-0 outline-none"
                    />
                  </div>
                </div>
              )
            })}
          </div>

          {hasChanges && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleReset}
              className="text-xs h-7 gap-1"
            >
              <RotateCcw size={12} />
              Reset to Default
            </Button>
          )}
        </div>
      )}
    </div>
  )
}
