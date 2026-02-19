/**
 * StyleCardPreview - Mini UI preview for style selection cards.
 *
 * Renders a miniature button, card, and text input styled by the given
 * StyleGuide's design tokens. Designed to fit inside ~120-150px wide card
 * tiles. Follows the same color/border resolution pattern as StylePreview.tsx
 * to correctly handle token references (e.g. "brand-DEFAULT", "surface-base")
 * alongside raw CSS values.
 */

import { useMemo } from 'react'
import type { StyleGuide } from '../lib/types'

interface StyleCardPreviewProps {
  guide: StyleGuide
  accentGuide?: StyleGuide
  modifiers?: string[]
}

// ---------------------------------------------------------------------------
// Token resolution helpers (mirrored from StylePreview.tsx)
// ---------------------------------------------------------------------------

/**
 * Resolve a color token that might be a named reference (e.g. "brand-DEFAULT",
 * "surface-base") or a raw CSS value (hex, rgba, gradient).
 */
function resolveColor(value: string | undefined, tokens: StyleGuide['color_tokens']): string {
  if (!value) return 'transparent'

  // Direct CSS values -- return as-is
  if (
    value.startsWith('#') || value.startsWith('rgb') || value.startsWith('hsl') ||
    value.startsWith('linear-gradient') || value.startsWith('radial-gradient') ||
    value === 'none' || value === 'transparent'
  ) {
    return value
  }

  // Token references like "brand-DEFAULT", "surface-base", "surface-muted"
  const parts = value.split('-')
  if (parts.length >= 2) {
    const group = parts[0]
    const key = parts.slice(1).join('-')
    const tokenGroup = tokens[group]
    if (tokenGroup && typeof tokenGroup === 'object' && key in (tokenGroup as Record<string, unknown>)) {
      return (tokenGroup as Record<string, string>)[key]
    }
  }

  return value
}

/** Parse a border string like "1px solid #E2E8F0" and resolve its color part. */
function resolveBorder(border: string | undefined, tokens: StyleGuide['color_tokens']): string {
  if (!border || border === 'none') return 'none'
  const parts = border.split(' ')
  if (parts.length === 3) {
    const color = resolveColor(parts[2], tokens)
    return `${parts[0]} ${parts[1]} ${color}`
  }
  return border
}

// ---------------------------------------------------------------------------
// Accent + modifier merging (simplified version of StylePreview's mergeTokens)
// ---------------------------------------------------------------------------

function mergeGuide(
  base: StyleGuide,
  accentGuide?: StyleGuide,
  modifiers?: string[],
): StyleGuide {
  const merged: StyleGuide = JSON.parse(JSON.stringify(base))

  // Accent overrides -- interactive elements only
  if (accentGuide) {
    const accent = accentGuide.components
    merged.components.buttons = { ...merged.components.buttons, ...accent.buttons }
    merged.components.inputs = { ...merged.components.inputs, ...accent.inputs }
    if (accent.cards) {
      merged.components.cards = {
        ...merged.components.cards,
        background: accent.cards.background || merged.components.cards.background,
        border: accent.cards.border || merged.components.cards.border,
        shadow: accent.cards.shadow || merged.components.cards.shadow,
        radius: accent.cards.radius || merged.components.cards.radius,
        backdrop_filter: accent.cards.backdrop_filter || merged.components.cards.backdrop_filter,
      }
    }
  }

  // Modifier effects relevant to the mini preview
  if (modifiers && modifiers.length > 0) {
    const active = new Set(modifiers)

    if (active.has('high-contrast-buttons')) {
      merged.components.buttons.border = '2px solid currentColor'
      merged.components.buttons.font_weight = '700'
    }
  }

  return merged
}

// ---------------------------------------------------------------------------
// Flat resolved tokens for rendering
// ---------------------------------------------------------------------------

interface MiniTokens {
  ct: StyleGuide['color_tokens']
  fontFamily: string
  canvasBg: string
  isGradientBg: boolean
  textPrimary: string
  textSecondary: string
  // Card
  cardBg: string
  cardBorder: string
  cardRadius: string
  cardShadow: string | undefined
  // Button
  btnBg: string
  btnText: string
  btnRadius: string
  btnBorder: string
  btnShadow: string | undefined
  btnFontWeight: number
  // Input
  inputBg: string
  inputBorder: string
  inputRadius: string
  inputShadow: string | undefined
}

function resolveTokens(guide: StyleGuide): MiniTokens {
  const { color_tokens: ct, typography, components } = guide

  const fontFamily = typography.font_family.split(',')[0].trim().replace(/'/g, '')
  const canvasBg = ct.surface.canvas
  const isGradientBg = canvasBg.startsWith('linear-gradient') || canvasBg.startsWith('radial-gradient')

  const borderFallback = ct.border.DEFAULT || ct.border.subtle || '#e5e7eb'

  return {
    ct,
    fontFamily,
    canvasBg,
    isGradientBg,
    textPrimary: ct.text.primary,
    textSecondary: ct.text.secondary,

    // Card tokens -- resolve references through color_tokens
    cardBg: resolveColor(components.cards.background, ct) || ct.surface.base,
    cardBorder: resolveBorder(components.cards.border, ct) || `1px solid ${borderFallback}`,
    cardRadius: components.cards.radius || '8px',
    cardShadow: components.cards.shadow === 'none' ? undefined : components.cards.shadow,

    // Button tokens
    btnBg: resolveColor(components.buttons.primary_bg, ct) || ct.brand.DEFAULT,
    btnText: resolveColor(components.buttons.primary_text, ct) || '#ffffff',
    btnRadius: components.buttons.radius || '6px',
    btnBorder: components.buttons.border
      ? resolveBorder(components.buttons.border, ct)
      : 'none',
    btnShadow: components.buttons.shadow === 'none' ? undefined : components.buttons.shadow,
    btnFontWeight: components.buttons.font_weight ? Number(components.buttons.font_weight) : 600,

    // Input tokens -- ensure border is always visible so the input doesn't vanish
    inputBg: resolveColor(components.inputs.background, ct) || ct.surface.base,
    inputBorder: resolveBorder(components.inputs.border, ct) || `1px solid ${borderFallback}`,
    inputRadius: components.inputs.radius || '6px',
    inputShadow: components.inputs.shadow === 'none' ? undefined : (components.inputs.shadow || `inset 0 1px 2px ${borderFallback}40`),
  }
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function StyleCardPreview({ guide, accentGuide, modifiers }: StyleCardPreviewProps) {
  const tokens = useMemo(() => {
    const merged = mergeGuide(guide, accentGuide, modifiers)
    return resolveTokens(merged)
  }, [guide, accentGuide, modifiers])

  return (
    <div
      className="w-full h-full overflow-hidden flex flex-col"
      style={{
        ...(tokens.isGradientBg
          ? { backgroundImage: tokens.canvasBg }
          : { backgroundColor: tokens.canvasBg }),
        fontFamily: tokens.fontFamily,
        padding: '10px',
        gap: '8px',
      }}
    >
      {/* Mini Card */}
      <div
        style={{
          backgroundColor: tokens.cardBg,
          border: tokens.cardBorder,
          borderRadius: tokens.cardRadius,
          boxShadow: tokens.cardShadow,
          padding: '10px 12px',
          flex: '1 1 auto',
        }}
      >
        <div
          style={{
            fontSize: '11px',
            fontWeight: 600,
            color: tokens.textPrimary,
            lineHeight: 1.3,
            marginBottom: '4px',
          }}
        >
          Card Title
        </div>
        <div
          style={{
            fontSize: '9px',
            color: tokens.textSecondary,
            lineHeight: 1.3,
          }}
        >
          Description text here
        </div>
      </div>

      {/* Mini Button */}
      <div
        style={{
          background: tokens.btnBg,
          color: tokens.btnText,
          borderRadius: tokens.btnRadius,
          border: tokens.btnBorder,
          boxShadow: tokens.btnShadow,
          fontWeight: tokens.btnFontWeight,
          fontSize: '10px',
          padding: '6px 12px',
          textAlign: 'center',
          lineHeight: 1.3,
        }}
      >
        Button
      </div>

      {/* Mini Input */}
      <div
        style={{
          backgroundColor: tokens.inputBg,
          border: tokens.inputBorder,
          borderRadius: tokens.inputRadius,
          boxShadow: tokens.inputShadow,
          fontSize: '9px',
          color: tokens.textSecondary,
          padding: '6px 8px',
          lineHeight: 1.3,
        }}
      >
        Type here...
      </div>
    </div>
  )
}
