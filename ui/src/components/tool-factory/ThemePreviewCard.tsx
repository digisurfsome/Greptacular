/**
 * A single theme card in the ThemePicker grid.
 * Shows color swatches, font names, and style classification badge.
 */

import { Check } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import type { TFThemeConfig } from '@/lib/types'

interface ThemePreviewCardProps {
  theme: TFThemeConfig
  selected: boolean
  onClick: () => void
}

export function ThemePreviewCard({ theme, selected, onClick }: ThemePreviewCardProps) {
  const { colors, typography, style_classification } = theme

  return (
    <button
      onClick={onClick}
      className={`relative text-left rounded-lg border-2 p-3 transition-all hover:shadow-md hover:-translate-y-0.5 ${
        selected
          ? 'border-primary ring-2 ring-primary/20'
          : 'border-border hover:border-primary/50'
      }`}
    >
      {selected && (
        <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-primary flex items-center justify-center">
          <Check size={12} className="text-primary-foreground" />
        </div>
      )}

      {/* Color swatches */}
      <div className="flex gap-1 mb-2">
        {[colors.brand_light, colors.brand_default, colors.brand_dark, colors.surface_base, colors.surface_muted].map(
          (color, i) => (
            <div
              key={i}
              className="w-6 h-6 rounded border border-border/50"
              style={{ backgroundColor: color }}
            />
          )
        )}
      </div>

      {/* Theme name */}
      <p className="text-sm font-semibold text-foreground truncate">{theme.theme_name}</p>

      {/* Font info */}
      <p className="text-xs text-muted-foreground truncate mt-0.5">
        {typography.font_family_heading}
        {typography.font_family_heading !== typography.font_family_body && ` / ${typography.font_family_body}`}
      </p>

      {/* Classification badge */}
      {style_classification && (
        <Badge variant="outline" className="mt-2 text-xs">
          {style_classification}
        </Badge>
      )}
    </button>
  )
}
