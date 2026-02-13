/**
 * Palette Utilities
 *
 * Converts a PaletteData selection into the customColors map consumed by
 * ColorCustomizer and the project-creation API.
 *
 * The 6 palette slots map to the 6 COLOR_FIELDS in ColorCustomizer:
 *   brand      → primary   (brand.DEFAULT)
 *   (derived)  → secondary (brand.dark)  – palette brand darkened 15%
 *   accent     → accent    (brand.light)
 *   background → background (surface.canvas)
 *   surface    → surface    (surface.base)
 *   text       → text       (text.primary)
 */

import type { PaletteData } from '../data/palettes'

/**
 * Darken a hex color by a percentage (0-100).
 * Clamps each channel to [0, 255].
 */
function darkenHex(hex: string, percent: number): string {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  const factor = 1 - percent / 100
  const dr = Math.max(0, Math.round(r * factor))
  const dg = Math.max(0, Math.round(g * factor))
  const db = Math.max(0, Math.round(b * factor))
  return `#${dr.toString(16).padStart(2, '0')}${dg.toString(16).padStart(2, '0')}${db.toString(16).padStart(2, '0')}`
}

/**
 * Convert a palette into the customColors record expected by ColorCustomizer.
 * Keys match COLOR_FIELDS in ColorCustomizer.tsx.
 */
export function paletteToCustomColors(palette: PaletteData): Record<string, string> {
  return {
    primary: palette.brand,
    secondary: darkenHex(palette.brand, 15),
    accent: palette.accent,
    background: palette.background,
    surface: palette.surface,
    text: palette.text,
  }
}
