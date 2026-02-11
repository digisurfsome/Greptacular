/**
 * StylePreview Component
 *
 * Renders actual UI elements (heading, paragraph, buttons, input, toggle)
 * styled with a design system's tokens via inline styles. Used in the style
 * picker grid to give users a real visual preview of each style.
 *
 * Two sizes:
 * - compact: for grid cards (shows key elements in a small area)
 * - full: for the full-screen hover overlay (mock app layout)
 */

import type { StyleGuide } from '../lib/types'

interface StylePreviewProps {
  guide: StyleGuide
  size?: 'compact' | 'full'
  styleName?: string
}

/**
 * Resolve a color token that might be a named reference (e.g., "brand-DEFAULT",
 * "surface-base") or a raw CSS value (hex, rgba, gradient).
 */
function resolveColor(value: string | undefined, tokens: StyleGuide['color_tokens']): string {
  if (!value) return 'transparent'

  // Direct CSS values - return as-is
  if (value.startsWith('#') || value.startsWith('rgb') || value.startsWith('hsl') ||
      value.startsWith('linear-gradient') || value.startsWith('radial-gradient') ||
      value === 'none' || value === 'transparent') {
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

/** Extract a usable background color from the canvas token (handles gradients) */
function getCanvasColor(canvas: string): string {
  if (canvas.startsWith('linear-gradient') || canvas.startsWith('radial-gradient')) {
    return canvas
  }
  return canvas
}

/** Parse a border string like "1px solid #E2E8F0" or "3px solid #18181B" */
function resolveBorder(border: string | undefined, tokens: StyleGuide['color_tokens']): string {
  if (!border || border === 'none') return 'none'
  // Try to resolve any color token references in the border value
  const parts = border.split(' ')
  if (parts.length === 3) {
    const color = resolveColor(parts[2], tokens)
    return `${parts[0]} ${parts[1]} ${color}`
  }
  return border
}

export function StylePreview({ guide, size = 'compact', styleName }: StylePreviewProps) {
  const { color_tokens, typography, components, spacing } = guide
  const ct = color_tokens

  // Resolve key colors
  const canvasBg = getCanvasColor(ct.surface.canvas)
  const textPrimary = ct.text.primary
  const textSecondary = ct.text.secondary
  const brandDefault = ct.brand.DEFAULT

  // Component tokens
  const card = components.cards
  const btn = components.buttons
  const input = components.inputs

  // Typography
  const fontFamily = typography.font_family.split(',')[0].trim().replace(/'/g, '')
  const h2 = typography.hierarchy.find(h => h.level === 'H2') || typography.hierarchy[1]
  const body = typography.hierarchy.find(h => h.level === 'Body') || typography.hierarchy[4]

  const isGradientBg = canvasBg.startsWith('linear-gradient') || canvasBg.startsWith('radial-gradient')

  if (size === 'compact') {
    return (
      <div
        style={{
          ...(isGradientBg ? { backgroundImage: canvasBg } : { backgroundColor: canvasBg }),
          borderRadius: '8px',
          padding: '12px',
          fontFamily,
          overflow: 'hidden',
          minHeight: '140px',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
        }}
      >
        {/* Heading */}
        <div
          style={{
            color: textPrimary,
            fontSize: '13px',
            fontWeight: h2?.weight ?? 600,
            lineHeight: 1.3,
            letterSpacing: '-0.01em',
          }}
        >
          {styleName || 'Sample Heading'}
        </div>

        {/* Body text */}
        <div
          style={{
            color: textSecondary,
            fontSize: '10px',
            fontWeight: body?.weight ?? 400,
            lineHeight: 1.5,
          }}
        >
          Body text preview with this design style applied.
        </div>

        {/* Card sample */}
        <div
          style={{
            background: resolveColor(card.background, ct),
            border: resolveBorder(card.border, ct),
            borderRadius: card.radius,
            boxShadow: card.shadow === 'none' ? undefined : card.shadow,
            padding: '8px',
            backdropFilter: card.backdrop_filter,
          }}
        >
          <div style={{ color: textPrimary, fontSize: '9px', fontWeight: 600 }}>Card Title</div>
          <div style={{ color: textSecondary, fontSize: '8px', marginTop: '2px' }}>Card content</div>
        </div>

        {/* Buttons row */}
        <div style={{ display: 'flex', gap: '6px', marginTop: 'auto' }}>
          <div
            style={{
              background: resolveColor(btn.primary_bg, ct),
              color: resolveColor(btn.primary_text, ct),
              borderRadius: btn.radius,
              padding: '4px 10px',
              fontSize: '9px',
              fontWeight: 600,
              border: btn.border ? resolveBorder(btn.border, ct) : 'none',
              boxShadow: btn.shadow,
              textTransform: btn.text_transform as React.CSSProperties['textTransform'],
              textAlign: 'center' as const,
            }}
          >
            Primary
          </div>
          <div
            style={{
              background: 'transparent',
              color: brandDefault,
              borderRadius: btn.radius,
              padding: '4px 10px',
              fontSize: '9px',
              fontWeight: 600,
              border: `1px solid ${brandDefault}`,
              textAlign: 'center' as const,
            }}
          >
            Secondary
          </div>
        </div>

        {/* Input sample */}
        <div
          style={{
            background: resolveColor(input.background, ct),
            border: resolveBorder(input.border, ct),
            borderRadius: input.radius,
            padding: '4px 8px',
            fontSize: '8px',
            color: ct.text.tertiary,
            boxShadow: input.shadow,
          }}
        >
          Input field...
        </div>
      </div>
    )
  }

  // Full size preview (for the overlay)
  return (
    <div
      style={{
        ...(isGradientBg ? { backgroundImage: canvasBg } : { backgroundColor: canvasBg }),
        fontFamily,
        padding: spacing.section_gap || '32px',
        minHeight: '100%',
        display: 'flex',
        flexDirection: 'column',
        gap: spacing.card_gap || '24px',
      }}
    >
      {/* Navbar mock */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '12px 24px',
          background: resolveColor(card.background, ct),
          border: resolveBorder(card.border, ct),
          borderRadius: card.radius,
          boxShadow: card.shadow === 'none' ? undefined : card.shadow,
          backdropFilter: card.backdrop_filter,
        }}
      >
        <div style={{ color: textPrimary, fontWeight: 700, fontSize: '16px' }}>AppName</div>
        <div style={{ display: 'flex', gap: '16px' }}>
          <span style={{ color: textSecondary, fontSize: '13px' }}>Home</span>
          <span style={{ color: textSecondary, fontSize: '13px' }}>Features</span>
          <span style={{ color: brandDefault, fontSize: '13px', fontWeight: 600 }}>Pricing</span>
        </div>
        <div
          style={{
            background: resolveColor(btn.primary_bg, ct),
            color: resolveColor(btn.primary_text, ct),
            borderRadius: btn.radius,
            padding: '6px 16px',
            fontSize: '12px',
            fontWeight: 600,
            border: btn.border ? resolveBorder(btn.border, ct) : 'none',
            boxShadow: btn.shadow,
          }}
        >
          Sign Up
        </div>
      </div>

      {/* Hero section */}
      <div style={{ textAlign: 'center', padding: '32px 0' }}>
        <h1
          style={{
            color: textPrimary,
            fontSize: typography.hierarchy[0]?.size || '36px',
            fontWeight: typography.hierarchy[0]?.weight || 700,
            lineHeight: typography.hierarchy[0]?.line_height || 1.2,
            margin: '0 0 12px',
          }}
        >
          Welcome to the Future
        </h1>
        <p
          style={{
            color: textSecondary,
            fontSize: body?.size || '14px',
            fontWeight: body?.weight || 400,
            lineHeight: body?.line_height || 1.6,
            maxWidth: '500px',
            margin: '0 auto 24px',
          }}
        >
          Experience a beautifully crafted interface that feels exactly right.
          Every pixel is intentional.
        </p>
        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
          <div
            style={{
              background: resolveColor(btn.primary_bg, ct),
              color: resolveColor(btn.primary_text, ct),
              borderRadius: btn.radius,
              padding: btn.padding,
              fontSize: '14px',
              fontWeight: 600,
              border: btn.border ? resolveBorder(btn.border, ct) : 'none',
              boxShadow: btn.shadow,
              cursor: 'pointer',
            }}
          >
            Get Started
          </div>
          <div
            style={{
              background: 'transparent',
              color: brandDefault,
              borderRadius: btn.radius,
              padding: btn.padding,
              fontSize: '14px',
              fontWeight: 600,
              border: `1px solid ${brandDefault}`,
              cursor: 'pointer',
            }}
          >
            Learn More
          </div>
        </div>
      </div>

      {/* Feature cards grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: spacing.card_gap || '16px',
        }}
      >
        {['Dashboard', 'Analytics', 'Settings'].map((title) => (
          <div
            key={title}
            style={{
              background: resolveColor(card.background, ct),
              border: resolveBorder(card.border, ct),
              borderRadius: card.radius,
              boxShadow: card.shadow === 'none' ? undefined : card.shadow,
              padding: card.padding,
              backdropFilter: card.backdrop_filter,
            }}
          >
            <h3
              style={{
                color: textPrimary,
                fontSize: h2?.size || '18px',
                fontWeight: h2?.weight || 600,
                margin: '0 0 8px',
              }}
            >
              {title}
            </h3>
            <p
              style={{
                color: textSecondary,
                fontSize: body?.size || '14px',
                lineHeight: body?.line_height || 1.6,
                margin: 0,
              }}
            >
              A brief description of this feature and how it helps your workflow.
            </p>
          </div>
        ))}
      </div>

      {/* Form section */}
      <div
        style={{
          background: resolveColor(card.background, ct),
          border: resolveBorder(card.border, ct),
          borderRadius: card.radius,
          boxShadow: card.shadow === 'none' ? undefined : card.shadow,
          padding: card.padding,
          backdropFilter: card.backdrop_filter,
          maxWidth: '400px',
          margin: '0 auto',
          width: '100%',
        }}
      >
        <h3 style={{ color: textPrimary, fontSize: '16px', fontWeight: 600, margin: '0 0 12px' }}>
          Contact Us
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div
            style={{
              background: resolveColor(input.background, ct),
              border: resolveBorder(input.border, ct),
              borderRadius: input.radius,
              padding: input.padding,
              color: ct.text.tertiary,
              fontSize: '13px',
              boxShadow: input.shadow,
            }}
          >
            Your email address
          </div>
          <div
            style={{
              background: resolveColor(input.background, ct),
              border: resolveBorder(input.border, ct),
              borderRadius: input.radius,
              padding: input.padding,
              color: ct.text.tertiary,
              fontSize: '13px',
              boxShadow: input.shadow,
              minHeight: '60px',
            }}
          >
            Your message...
          </div>
          <div
            style={{
              background: resolveColor(btn.primary_bg, ct),
              color: resolveColor(btn.primary_text, ct),
              borderRadius: btn.radius,
              padding: btn.padding,
              fontSize: '13px',
              fontWeight: 600,
              border: btn.border ? resolveBorder(btn.border, ct) : 'none',
              boxShadow: btn.shadow,
              textAlign: 'center',
              cursor: 'pointer',
            }}
          >
            Send Message
          </div>
        </div>
      </div>

      {/* Toggle / status indicators */}
      <div
        style={{
          display: 'flex',
          gap: '16px',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '8px 0',
        }}
      >
        {/* Toggle switch mock */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: textSecondary, fontSize: '12px' }}>Dark Mode</span>
          <div
            style={{
              width: '36px',
              height: '20px',
              borderRadius: '10px',
              background: brandDefault,
              position: 'relative',
              cursor: 'pointer',
            }}
          >
            <div
              style={{
                width: '16px',
                height: '16px',
                borderRadius: '50%',
                background: '#fff',
                position: 'absolute',
                top: '2px',
                right: '2px',
                boxShadow: '0 1px 2px rgba(0,0,0,0.2)',
              }}
            />
          </div>
        </div>

        {/* Status badges */}
        <div
          style={{
            background: ct.status.success + '20',
            color: ct.status.success,
            fontSize: '11px',
            fontWeight: 600,
            padding: '3px 10px',
            borderRadius: '999px',
          }}
        >
          Active
        </div>
        <div
          style={{
            background: ct.status.warning + '20',
            color: ct.status.warning,
            fontSize: '11px',
            fontWeight: 600,
            padding: '3px 10px',
            borderRadius: '999px',
          }}
        >
          Pending
        </div>
      </div>
    </div>
  )
}
