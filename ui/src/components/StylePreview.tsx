/**
 * StylePreview Component
 *
 * Live style preview engine that renders sample UI pages using inline CSS
 * derived from design system tokens. Supports 4 different sample pages
 * (landing, dashboard, settings, feed), modifier overlays for accessibility
 * adjustments, and accent style mixing for interactive elements.
 *
 * Two modes:
 * - compact: grid card thumbnail (~200px wide) showing key elements
 * - full: full-screen preview rendering one of four sample pages
 */

import type { StyleGuide, StyleComponentTokens } from '../lib/types'

// ---------------------------------------------------------------------------
// Public types
// ---------------------------------------------------------------------------

export type PreviewPage = 'landing' | 'dashboard' | 'settings' | 'feed'

interface StylePreviewProps {
  guide: StyleGuide
  accentGuide?: StyleGuide
  modifiers?: string[]
  size?: 'compact' | 'full'
  styleName?: string
  activePage?: PreviewPage
}

// ---------------------------------------------------------------------------
// Internal type for merged/resolved tokens used throughout rendering
// ---------------------------------------------------------------------------

interface ResolvedTokens {
  ct: StyleGuide['color_tokens']
  typography: StyleGuide['typography']
  card: StyleComponentTokens
  btn: StyleComponentTokens
  input: StyleComponentTokens
  spacing: StyleGuide['spacing']
  fontFamily: string
  canvasBg: string
  isGradientBg: boolean
  textPrimary: string
  textSecondary: string
  textTertiary: string
  brandDefault: string
  brandLight: string
  brandDark: string
  /** Resolved hierarchy levels for convenient lookup */
  display: { size: string; weight: number; lineHeight: number }
  h1: { size: string; weight: number; lineHeight: number }
  h2: { size: string; weight: number; lineHeight: number }
  h3: { size: string; weight: number; lineHeight: number }
  body: { size: string; weight: number; lineHeight: number }
  small: { size: string; weight: number; lineHeight: number }
}

// ---------------------------------------------------------------------------
// Token helpers (preserved from original)
// ---------------------------------------------------------------------------

/**
 * Resolve a color token that might be a named reference (e.g., "brand-DEFAULT",
 * "surface-base") or a raw CSS value (hex, rgba, gradient).
 */
function resolveColor(value: string | undefined, tokens: StyleGuide['color_tokens']): string {
  if (!value) return 'transparent'

  // Direct CSS values - return as-is
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

/** Extract a usable background color from the canvas token (handles gradients) */
function getCanvasColor(canvas: string): string {
  return canvas
}

/** Parse a border string like "1px solid #E2E8F0" or "3px solid #18181B" */
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
// Token merging: base + accent + modifiers
// ---------------------------------------------------------------------------

/**
 * Scale a CSS font-size string by a multiplier. Handles px, rem, and em units.
 * Returns the scaled value with the same unit.
 */
function scaleFontSize(size: string, factor: number): string {
  const match = size.match(/^([\d.]+)(px|rem|em)$/)
  if (!match) return size
  const value = parseFloat(match[1])
  const unit = match[2]
  return `${(value * factor).toFixed(unit === 'px' ? 0 : 2)}${unit}`
}

/**
 * Merge base guide tokens with an optional accent guide and modifiers.
 *
 * Accent guide: overrides ONLY button, input, and card interactive tokens
 * (background layout, text colors, and typography remain from the base).
 *
 * Modifiers apply visual effects on top of the merged result:
 * - high-contrast-buttons: thicker borders and heavier font weight on buttons
 * - large-touch-targets: increased padding on buttons/inputs and larger gaps
 * - high-contrast-text: heavier body/small text weight
 * - larger-type: all font sizes scale up 1.15x, body line_height 1.8
 */
function mergeTokens(
  guide: StyleGuide,
  accentGuide?: StyleGuide,
  modifiers?: string[],
): StyleGuide {
  // Deep-clone the base so mutations are safe
  const merged: StyleGuide = JSON.parse(JSON.stringify(guide))

  // --- Accent overrides (interactive elements only) ---
  if (accentGuide) {
    const accent = accentGuide.components
    // Buttons: override all button tokens from accent
    merged.components.buttons = { ...merged.components.buttons, ...accent.buttons }
    // Inputs: override all input tokens from accent
    merged.components.inputs = { ...merged.components.inputs, ...accent.inputs }
    // Cards: selectively override interactive tokens (background, border, shadow, radius)
    // but keep padding from base to preserve layout density
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

  // --- Modifier effects ---
  if (modifiers && modifiers.length > 0) {
    const activeSet = new Set(modifiers)

    if (activeSet.has('high-contrast-buttons')) {
      merged.components.buttons.border = '2px solid currentColor'
      merged.components.buttons.font_weight = '700'
    }

    if (activeSet.has('large-touch-targets')) {
      merged.components.buttons.padding = '14px 28px'
      merged.components.inputs.padding = '14px 18px'
      merged.spacing.card_gap = '24px'
      merged.spacing.section_gap = '48px'
    }

    if (activeSet.has('high-contrast-text')) {
      // Bump body weight to 500 and small text to 600
      merged.typography.hierarchy = merged.typography.hierarchy.map(level => {
        if (level.level === 'Body') return { ...level, weight: 500 }
        if (level.level === 'Small') return { ...level, weight: 600 }
        return level
      })
    }

    if (activeSet.has('larger-type')) {
      merged.typography.hierarchy = merged.typography.hierarchy.map(level => ({
        ...level,
        size: scaleFontSize(level.size, 1.15),
        line_height: level.level === 'Body' ? 1.8 : level.line_height,
      }))
    }
  }

  return merged
}

// ---------------------------------------------------------------------------
// Resolve guide tokens into a flat, easy-to-use object
// ---------------------------------------------------------------------------

function resolveTokens(guide: StyleGuide): ResolvedTokens {
  const { color_tokens: ct, typography, components, spacing } = guide

  const fontFamily = typography.font_family.split(',')[0].trim().replace(/'/g, '')
  const canvasBg = getCanvasColor(ct.surface.canvas)
  const isGradientBg = canvasBg.startsWith('linear-gradient') || canvasBg.startsWith('radial-gradient')

  // Find hierarchy levels with sensible fallbacks
  const findLevel = (name: string, fallbackIndex: number) => {
    const found = typography.hierarchy.find(h => h.level === name) || typography.hierarchy[fallbackIndex]
    return {
      size: found?.size || '14px',
      weight: found?.weight ?? 400,
      lineHeight: found?.line_height ?? 1.5,
    }
  }

  return {
    ct,
    typography,
    card: components.cards,
    btn: components.buttons,
    input: components.inputs,
    spacing,
    fontFamily,
    canvasBg,
    isGradientBg,
    textPrimary: ct.text.primary,
    textSecondary: ct.text.secondary,
    textTertiary: ct.text.tertiary,
    brandDefault: ct.brand.DEFAULT,
    brandLight: ct.brand.light,
    brandDark: ct.brand.dark,
    display: findLevel('Display', 0),
    h1: findLevel('H1', 0),
    h2: findLevel('H2', 1),
    h3: findLevel('H3', 2),
    body: findLevel('Body', 4),
    small: findLevel('Small', 5),
  }
}

// ---------------------------------------------------------------------------
// Shared style builder helpers
// ---------------------------------------------------------------------------

function cardStyle(t: ResolvedTokens, extraPadding?: string): React.CSSProperties {
  return {
    background: resolveColor(t.card.background, t.ct),
    border: resolveBorder(t.card.border, t.ct),
    borderRadius: t.card.radius,
    boxShadow: t.card.shadow === 'none' ? undefined : t.card.shadow,
    padding: extraPadding || t.card.padding,
    backdropFilter: t.card.backdrop_filter,
  }
}

function primaryBtnStyle(t: ResolvedTokens, fontSize?: string): React.CSSProperties {
  return {
    background: resolveColor(t.btn.primary_bg, t.ct),
    color: resolveColor(t.btn.primary_text, t.ct),
    borderRadius: t.btn.radius,
    padding: t.btn.padding,
    fontSize: fontSize || '14px',
    fontWeight: t.btn.font_weight ? Number(t.btn.font_weight) : 600,
    border: t.btn.border ? resolveBorder(t.btn.border, t.ct) : 'none',
    boxShadow: t.btn.shadow,
    textTransform: t.btn.text_transform as React.CSSProperties['textTransform'],
    cursor: 'pointer',
    textAlign: 'center' as const,
    display: 'inline-block',
  }
}

function outlineBtnStyle(t: ResolvedTokens, fontSize?: string): React.CSSProperties {
  return {
    background: 'transparent',
    color: t.brandDefault,
    borderRadius: t.btn.radius,
    padding: t.btn.padding,
    fontSize: fontSize || '14px',
    fontWeight: t.btn.font_weight ? Number(t.btn.font_weight) : 600,
    border: `1px solid ${t.brandDefault}`,
    cursor: 'pointer',
    textAlign: 'center' as const,
    display: 'inline-block',
  }
}

function ghostBtnStyle(t: ResolvedTokens, fontSize?: string): React.CSSProperties {
  return {
    background: 'transparent',
    color: t.textSecondary,
    borderRadius: t.btn.radius,
    padding: t.btn.padding,
    fontSize: fontSize || '14px',
    fontWeight: 500,
    border: 'none',
    cursor: 'pointer',
    textAlign: 'center' as const,
    display: 'inline-block',
  }
}

function inputStyle(t: ResolvedTokens): React.CSSProperties {
  return {
    background: resolveColor(t.input.background, t.ct),
    border: resolveBorder(t.input.border, t.ct),
    borderRadius: t.input.radius,
    padding: t.input.padding,
    fontSize: t.body.size,
    color: t.textTertiary,
    boxShadow: t.input.shadow,
    width: '100%',
    boxSizing: 'border-box' as const,
  }
}

function statusBadge(_t: ResolvedTokens, color: string, label: string): React.JSX.Element {
  return (
    <span
      style={{
        background: color + '20',
        color: color,
        fontSize: '11px',
        fontWeight: 600,
        padding: '3px 10px',
        borderRadius: '999px',
        whiteSpace: 'nowrap',
      }}
    >
      {label}
    </span>
  )
}

/** Toggle switch mock */
function toggleSwitch(t: ResolvedTokens, isOn: boolean): React.JSX.Element {
  return (
    <div
      style={{
        width: '40px',
        height: '22px',
        borderRadius: '11px',
        background: isOn ? t.brandDefault : (t.ct.border.subtle || '#ccc'),
        position: 'relative',
        cursor: 'pointer',
        flexShrink: 0,
        transition: 'background 0.2s',
      }}
    >
      <div
        style={{
          width: '18px',
          height: '18px',
          borderRadius: '50%',
          background: '#fff',
          position: 'absolute',
          top: '2px',
          ...(isOn ? { right: '2px' } : { left: '2px' }),
          boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
        }}
      />
    </div>
  )
}

/** Radio button mock */
function radioButton(t: ResolvedTokens, isSelected: boolean): React.JSX.Element {
  return (
    <div
      style={{
        width: '18px',
        height: '18px',
        borderRadius: '50%',
        border: `2px solid ${isSelected ? t.brandDefault : (t.ct.border.subtle || '#ccc')}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
      }}
    >
      {isSelected && (
        <div
          style={{
            width: '10px',
            height: '10px',
            borderRadius: '50%',
            background: t.brandDefault,
          }}
        />
      )}
    </div>
  )
}

/** Checkbox mock */
function checkbox(t: ResolvedTokens, isChecked: boolean): React.JSX.Element {
  return (
    <div
      style={{
        width: '18px',
        height: '18px',
        borderRadius: '4px',
        border: `2px solid ${isChecked ? t.brandDefault : (t.ct.border.subtle || '#ccc')}`,
        background: isChecked ? t.brandDefault : 'transparent',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
      }}
    >
      {isChecked && (
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
          <path d="M2.5 6L5 8.5L9.5 3.5" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      )}
    </div>
  )
}

/** Progress bar mock */
function progressBar(t: ResolvedTokens, percent: number): React.JSX.Element {
  return (
    <div
      style={{
        width: '100%',
        height: '8px',
        borderRadius: '4px',
        background: t.ct.surface.muted,
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          width: `${percent}%`,
          height: '100%',
          borderRadius: '4px',
          background: t.brandDefault,
        }}
      />
    </div>
  )
}

// ---------------------------------------------------------------------------
// Page icon placeholders (simple SVG shapes)
// ---------------------------------------------------------------------------

function iconPlaceholder(t: ResolvedTokens, size: number = 32): React.JSX.Element {
  return (
    <div
      style={{
        width: `${size}px`,
        height: `${size}px`,
        borderRadius: '8px',
        background: t.brandDefault + '18',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
      }}
    >
      <svg width={size * 0.5} height={size * 0.5} viewBox="0 0 16 16" fill={t.brandDefault}>
        <rect x="2" y="2" width="5" height="5" rx="1" />
        <rect x="9" y="2" width="5" height="5" rx="1" />
        <rect x="2" y="9" width="5" height="5" rx="1" />
        <rect x="9" y="9" width="5" height="5" rx="1" />
      </svg>
    </div>
  )
}

/** Image placeholder for feed cards */
function imagePlaceholder(t: ResolvedTokens, height: string = '120px'): React.JSX.Element {
  return (
    <div
      style={{
        width: '100%',
        height,
        background: `linear-gradient(135deg, ${t.ct.surface.muted}, ${t.brandDefault}20)`,
        borderRadius: t.card.radius ? `${t.card.radius} ${t.card.radius} 0 0` : '8px 8px 0 0',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke={t.textTertiary} strokeWidth="1.5">
        <rect x="3" y="3" width="18" height="18" rx="2" />
        <circle cx="8.5" cy="8.5" r="1.5" />
        <path d="M21 15l-5-5L5 21" />
      </svg>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Compact mode (grid card thumbnail)
// ---------------------------------------------------------------------------

function renderCompact(t: ResolvedTokens, styleName?: string): React.JSX.Element {
  return (
    <div
      style={{
        ...(t.isGradientBg ? { backgroundImage: t.canvasBg } : { backgroundColor: t.canvasBg }),
        borderRadius: '8px',
        padding: '12px',
        fontFamily: t.fontFamily,
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
          color: t.textPrimary,
          fontSize: '13px',
          fontWeight: t.h2.weight,
          lineHeight: 1.3,
          letterSpacing: '-0.01em',
        }}
      >
        {styleName || 'Sample Heading'}
      </div>

      {/* Body text */}
      <div
        style={{
          color: t.textSecondary,
          fontSize: '10px',
          fontWeight: t.body.weight,
          lineHeight: 1.5,
        }}
      >
        Body text preview with this design style applied.
      </div>

      {/* Card sample */}
      <div
        style={{
          ...cardStyle(t, '8px'),
        }}
      >
        <div style={{ color: t.textPrimary, fontSize: '9px', fontWeight: 600 }}>Card Title</div>
        <div style={{ color: t.textSecondary, fontSize: '8px', marginTop: '2px' }}>Card content</div>
      </div>

      {/* Buttons row */}
      <div style={{ display: 'flex', gap: '6px', marginTop: 'auto' }}>
        <div
          style={{
            ...primaryBtnStyle(t, '9px'),
            padding: '4px 10px',
          }}
        >
          Primary
        </div>
        <div
          style={{
            ...outlineBtnStyle(t, '9px'),
            padding: '4px 10px',
          }}
        >
          Secondary
        </div>
      </div>

      {/* Input sample */}
      <div
        style={{
          ...inputStyle(t),
          fontSize: '8px',
          padding: '4px 8px',
        }}
      >
        Input field...
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Full mode - Page 1: Landing
// ---------------------------------------------------------------------------

function renderLanding(t: ResolvedTokens): React.JSX.Element {
  const sectionGap = t.spacing.section_gap || '32px'
  const cardGap = t.spacing.card_gap || '16px'

  return (
    <>
      {/* Navbar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '14px 28px',
          ...cardStyle(t),
        }}
      >
        <div style={{ color: t.textPrimary, fontWeight: 700, fontSize: '18px', letterSpacing: '-0.02em' }}>
          Acme Inc.
        </div>
        <div style={{ display: 'flex', gap: '24px', alignItems: 'center' }}>
          <span style={{ color: t.textSecondary, fontSize: '14px', cursor: 'pointer' }}>Features</span>
          <span style={{ color: t.textSecondary, fontSize: '14px', cursor: 'pointer' }}>Pricing</span>
          <span style={{ color: t.textSecondary, fontSize: '14px', cursor: 'pointer' }}>About</span>
          <div style={primaryBtnStyle(t, '13px')}>Get Started</div>
        </div>
      </div>

      {/* Hero */}
      <div style={{ textAlign: 'center', padding: `${sectionGap} 0` }}>
        <h1
          style={{
            color: t.textPrimary,
            fontSize: t.display.size,
            fontWeight: t.display.weight,
            lineHeight: t.display.lineHeight,
            margin: '0 0 16px',
            letterSpacing: '-0.03em',
          }}
        >
          Build Something Remarkable
        </h1>
        <p
          style={{
            color: t.textSecondary,
            fontSize: t.body.size,
            fontWeight: t.body.weight,
            lineHeight: t.body.lineHeight,
            maxWidth: '540px',
            margin: '0 auto 28px',
          }}
        >
          A beautifully designed platform that empowers teams to create, collaborate,
          and ship products faster than ever before.
        </p>
        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
          <div style={primaryBtnStyle(t)}>Start Free Trial</div>
          <div style={outlineBtnStyle(t)}>Watch Demo</div>
        </div>
      </div>

      {/* Feature cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: cardGap,
        }}
      >
        {[
          { title: 'Real-Time Analytics', desc: 'Track performance metrics with live dashboards that update as your data flows in. Make data-driven decisions instantly.' },
          { title: 'Team Collaboration', desc: 'Work together seamlessly with shared workspaces, real-time editing, and integrated messaging for your entire team.' },
          { title: 'Smart Automation', desc: 'Automate repetitive tasks with intelligent workflows. Set triggers, conditions, and actions to save hours every week.' },
        ].map(({ title, desc }) => (
          <div key={title} style={{ ...cardStyle(t), display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {iconPlaceholder(t, 36)}
            <h3
              style={{
                color: t.textPrimary,
                fontSize: t.h3.size,
                fontWeight: t.h3.weight,
                lineHeight: t.h3.lineHeight,
                margin: 0,
              }}
            >
              {title}
            </h3>
            <p
              style={{
                color: t.textSecondary,
                fontSize: t.body.size,
                fontWeight: t.body.weight,
                lineHeight: t.body.lineHeight,
                margin: 0,
              }}
            >
              {desc}
            </p>
            <div style={{ marginTop: 'auto', paddingTop: '4px' }}>
              <span style={{ color: t.brandDefault, fontSize: t.small.size, fontWeight: 600, cursor: 'pointer' }}>
                Learn more &rarr;
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Contact form section */}
      <div
        style={{
          ...cardStyle(t),
          maxWidth: '480px',
          margin: '0 auto',
          width: '100%',
        }}
      >
        <h3
          style={{
            color: t.textPrimary,
            fontSize: t.h3.size,
            fontWeight: t.h3.weight,
            margin: '0 0 16px',
          }}
        >
          Get in Touch
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={inputStyle(t)}>your@email.com</div>
          <div style={{ ...inputStyle(t), minHeight: '80px' }}>Tell us about your project...</div>
          <div style={{ ...primaryBtnStyle(t), textAlign: 'center', width: '100%' }}>Send Message</div>
        </div>
      </div>

      {/* Footer */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '20px 0',
          borderTop: `1px solid ${t.ct.border.subtle}`,
          marginTop: '8px',
        }}
      >
        <div style={{ color: t.textTertiary, fontSize: t.small.size }}>
          &copy; 2026 Acme Inc. All rights reserved.
        </div>
        <div style={{ display: 'flex', gap: '20px' }}>
          <span style={{ color: t.textSecondary, fontSize: t.small.size, cursor: 'pointer' }}>Privacy</span>
          <span style={{ color: t.textSecondary, fontSize: t.small.size, cursor: 'pointer' }}>Terms</span>
          <span style={{ color: t.textSecondary, fontSize: t.small.size, cursor: 'pointer' }}>Support</span>
        </div>
      </div>
    </>
  )
}

// ---------------------------------------------------------------------------
// Full mode - Page 2: Dashboard
// ---------------------------------------------------------------------------

function renderDashboard(t: ResolvedTokens): React.JSX.Element {
  const cardGap = t.spacing.card_gap || '16px'

  const stats = [
    { label: 'Total Revenue', value: '$48,290', change: '+12.5%', color: t.ct.status.success },
    { label: 'Active Users', value: '2,847', change: '+8.2%', color: t.ct.status.success },
    { label: 'Conversion Rate', value: '3.24%', change: '-0.4%', color: t.ct.status.error },
    { label: 'Avg. Session', value: '4m 32s', change: '+1.1%', color: t.ct.status.success },
  ]

  const tableRows = [
    { name: 'Enterprise Plan', customer: 'Globex Corp.', amount: '$2,400', status: 'Completed', statusColor: t.ct.status.success },
    { name: 'Pro Subscription', customer: 'Initech LLC', amount: '$890', status: 'Pending', statusColor: t.ct.status.warning },
    { name: 'Starter Pack', customer: 'Wayne Enterprises', amount: '$450', status: 'Completed', statusColor: t.ct.status.success },
    { name: 'Custom Integration', customer: 'Stark Industries', amount: '$3,200', status: 'In Progress', statusColor: t.ct.status.info },
  ]

  const navItems = ['Overview', 'Analytics', 'Customers', 'Orders', 'Products', 'Settings']

  return (
    <div style={{ display: 'flex', gap: cardGap, minHeight: '600px' }}>
      {/* Sidebar */}
      <div
        style={{
          ...cardStyle(t),
          width: '200px',
          flexShrink: 0,
          display: 'flex',
          flexDirection: 'column',
          gap: '2px',
          padding: '16px 12px',
        }}
      >
        <div
          style={{
            color: t.textPrimary,
            fontWeight: 700,
            fontSize: '16px',
            padding: '8px 12px',
            marginBottom: '12px',
            letterSpacing: '-0.02em',
          }}
        >
          Dashboard
        </div>
        {navItems.map((item, i) => (
          <div
            key={item}
            style={{
              padding: '10px 12px',
              borderRadius: t.btn.radius || '6px',
              fontSize: '13px',
              fontWeight: i === 0 ? 600 : 400,
              color: i === 0 ? resolveColor(t.btn.primary_text, t.ct) : t.textSecondary,
              background: i === 0 ? resolveColor(t.btn.primary_bg, t.ct) : 'transparent',
              cursor: 'pointer',
            }}
          >
            {item}
          </div>
        ))}
      </div>

      {/* Main content */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: cardGap }}>
        {/* Stats row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: cardGap }}>
          {stats.map(({ label, value, change, color }) => (
            <div key={label} style={{ ...cardStyle(t), display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <div style={{ color: t.textSecondary, fontSize: t.small.size, fontWeight: 500 }}>{label}</div>
              <div style={{ color: t.textPrimary, fontSize: t.h2.size, fontWeight: t.h2.weight }}>{value}</div>
              <div style={{ color, fontSize: '12px', fontWeight: 600 }}>{change}</div>
            </div>
          ))}
        </div>

        {/* Progress section */}
        <div style={{ ...cardStyle(t), display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ color: t.textPrimary, fontSize: t.h3.size, fontWeight: t.h3.weight }}>Monthly Goals</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {[
              { label: 'Revenue Target', percent: 78 },
              { label: 'New Signups', percent: 92 },
              { label: 'Customer Satisfaction', percent: 65 },
            ].map(({ label, percent }) => (
              <div key={label} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: t.textSecondary, fontSize: t.small.size }}>{label}</span>
                  <span style={{ color: t.textPrimary, fontSize: t.small.size, fontWeight: 600 }}>{percent}%</span>
                </div>
                {progressBar(t, percent)}
              </div>
            ))}
          </div>
        </div>

        {/* Data table */}
        <div style={{ ...cardStyle(t), padding: 0, overflow: 'hidden' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: t.card.padding || '16px',
              borderBottom: `1px solid ${t.ct.border.subtle}`,
            }}
          >
            <div style={{ color: t.textPrimary, fontSize: t.h3.size, fontWeight: t.h3.weight }}>Recent Transactions</div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <div style={primaryBtnStyle(t, '12px')}>Add New</div>
            </div>
          </div>

          {/* Table header */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '2fr 2fr 1fr 1fr 1fr',
              padding: '10px 16px',
              background: t.ct.surface.muted,
              fontSize: '12px',
              fontWeight: 600,
              color: t.textSecondary,
              borderBottom: `1px solid ${t.ct.border.subtle}`,
            }}
          >
            <span>Product</span>
            <span>Customer</span>
            <span>Amount</span>
            <span>Status</span>
            <span>Actions</span>
          </div>

          {/* Table rows */}
          {tableRows.map(({ name, customer, amount, status, statusColor }) => (
            <div
              key={name}
              style={{
                display: 'grid',
                gridTemplateColumns: '2fr 2fr 1fr 1fr 1fr',
                padding: '12px 16px',
                borderBottom: `1px solid ${t.ct.border.subtle}`,
                alignItems: 'center',
                fontSize: '13px',
              }}
            >
              <span style={{ color: t.textPrimary, fontWeight: 500 }}>{name}</span>
              <span style={{ color: t.textSecondary }}>{customer}</span>
              <span style={{ color: t.textPrimary, fontWeight: 500 }}>{amount}</span>
              <span>{statusBadge(t, statusColor, status)}</span>
              <div style={{ display: 'flex', gap: '6px' }}>
                <span style={{ color: t.brandDefault, fontSize: '12px', fontWeight: 500, cursor: 'pointer' }}>Edit</span>
                <span style={{ color: t.ct.status.error, fontSize: '12px', fontWeight: 500, cursor: 'pointer' }}>Delete</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Full mode - Page 3: Settings
// ---------------------------------------------------------------------------

function renderSettings(t: ResolvedTokens): React.JSX.Element {
  const cardGap = t.spacing.card_gap || '16px'

  return (
    <div style={{ maxWidth: '640px', margin: '0 auto', width: '100%', display: 'flex', flexDirection: 'column', gap: cardGap }}>
      {/* Profile header */}
      <div style={{ ...cardStyle(t), display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div
          style={{
            width: '56px',
            height: '56px',
            borderRadius: '50%',
            background: `linear-gradient(135deg, ${t.brandLight}, ${t.brandDefault})`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontWeight: 700,
            fontSize: '20px',
            flexShrink: 0,
          }}
        >
          JD
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ color: t.textPrimary, fontSize: t.h3.size, fontWeight: t.h3.weight }}>Jane Doe</div>
          <div style={{ color: t.textSecondary, fontSize: t.small.size, marginTop: '2px' }}>jane.doe@example.com</div>
        </div>
        <div style={outlineBtnStyle(t, '13px')}>Edit Photo</div>
      </div>

      {/* Form fields */}
      <div style={{ ...cardStyle(t), display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ color: t.textPrimary, fontSize: t.h3.size, fontWeight: t.h3.weight, marginBottom: '4px' }}>
          Personal Information
        </div>

        {/* Name row */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ color: t.textSecondary, fontSize: t.small.size, fontWeight: 500 }}>First Name</label>
            <div style={inputStyle(t)}>Jane</div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ color: t.textSecondary, fontSize: t.small.size, fontWeight: 500 }}>Last Name</label>
            <div style={inputStyle(t)}>Doe</div>
          </div>
        </div>

        {/* Email */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <label style={{ color: t.textSecondary, fontSize: t.small.size, fontWeight: 500 }}>Email Address</label>
          <div style={inputStyle(t)}>jane.doe@example.com</div>
        </div>

        {/* Bio */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <label style={{ color: t.textSecondary, fontSize: t.small.size, fontWeight: 500 }}>Bio</label>
          <div style={{ ...inputStyle(t), minHeight: '72px' }}>
            Product designer with 8 years of experience in creating user-centered digital experiences.
          </div>
        </div>
      </div>

      {/* Toggle switches */}
      <div style={{ ...cardStyle(t), display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ color: t.textPrimary, fontSize: t.h3.size, fontWeight: t.h3.weight, marginBottom: '4px' }}>
          Notifications
        </div>
        {[
          { label: 'Email Notifications', desc: 'Receive updates about your account activity', on: true },
          { label: 'Push Notifications', desc: 'Get real-time alerts on your mobile device', on: false },
          { label: 'Weekly Digest', desc: 'A summary of your team\'s progress sent every Monday', on: true },
        ].map(({ label, desc, on }) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '16px' }}>
            <div>
              <div style={{ color: t.textPrimary, fontSize: t.body.size, fontWeight: 500 }}>{label}</div>
              <div style={{ color: t.textSecondary, fontSize: t.small.size, marginTop: '2px' }}>{desc}</div>
            </div>
            {toggleSwitch(t, on)}
          </div>
        ))}
      </div>

      {/* Radio button group */}
      <div style={{ ...cardStyle(t), display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ color: t.textPrimary, fontSize: t.h3.size, fontWeight: t.h3.weight, marginBottom: '4px' }}>
          Theme Preference
        </div>
        {[
          { label: 'Light Mode', desc: 'Classic light interface', selected: false },
          { label: 'Dark Mode', desc: 'Easy on the eyes in low light', selected: true },
          { label: 'System Default', desc: 'Follow your operating system setting', selected: false },
        ].map(({ label, desc, selected }) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }}>
            {radioButton(t, selected)}
            <div>
              <div style={{ color: t.textPrimary, fontSize: t.body.size, fontWeight: selected ? 600 : 400 }}>{label}</div>
              <div style={{ color: t.textSecondary, fontSize: t.small.size, marginTop: '1px' }}>{desc}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Checkbox group */}
      <div style={{ ...cardStyle(t), display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ color: t.textPrimary, fontSize: t.h3.size, fontWeight: t.h3.weight, marginBottom: '4px' }}>
          Privacy Settings
        </div>
        {[
          { label: 'Show profile publicly', checked: true },
          { label: 'Allow search engines to index my profile', checked: false },
          { label: 'Share usage data for product improvements', checked: false },
        ].map(({ label, checked }) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }}>
            {checkbox(t, checked)}
            <span style={{ color: t.textPrimary, fontSize: t.body.size }}>{label}</span>
          </div>
        ))}
      </div>

      {/* Select mock */}
      <div style={{ ...cardStyle(t), display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <div style={{ color: t.textPrimary, fontSize: t.h3.size, fontWeight: t.h3.weight }}>
          Language & Region
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <label style={{ color: t.textSecondary, fontSize: t.small.size, fontWeight: 500 }}>Language</label>
          <div
            style={{
              ...inputStyle(t),
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              color: t.textPrimary,
            }}
          >
            <span>English (US)</span>
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke={t.textTertiary} strokeWidth="2">
              <path d="M3 4.5L6 7.5L9 4.5" />
            </svg>
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <label style={{ color: t.textSecondary, fontSize: t.small.size, fontWeight: 500 }}>Timezone</label>
          <div
            style={{
              ...inputStyle(t),
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              color: t.textPrimary,
            }}
          >
            <span>Pacific Time (UTC-8)</span>
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke={t.textTertiary} strokeWidth="2">
              <path d="M3 4.5L6 7.5L9 4.5" />
            </svg>
          </div>
        </div>
      </div>

      {/* Save / Cancel row */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', paddingTop: '4px' }}>
        <div style={ghostBtnStyle(t, '14px')}>Cancel</div>
        <div style={primaryBtnStyle(t, '14px')}>Save Changes</div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Full mode - Page 4: Feed
// ---------------------------------------------------------------------------

function renderFeed(t: ResolvedTokens): React.JSX.Element {
  const cardGap = t.spacing.card_gap || '16px'

  const tags = ['All', 'Design', 'Engineering', 'Product', 'Research']
  const feedCards = [
    {
      title: 'Rethinking Design Systems at Scale',
      desc: 'How we rebuilt our component library to serve 50+ product teams with consistent, accessible UI patterns.',
      tags: ['Design', 'Engineering'],
    },
    {
      title: 'The Future of Real-Time Collaboration',
      desc: 'Exploring WebSocket architectures and CRDT-based sync engines that power modern collaborative editing tools.',
      tags: ['Engineering', 'Product'],
    },
    {
      title: 'Conducting Effective User Research',
      desc: 'A practical guide to planning research sessions, recruiting participants, and synthesizing findings into actionable insights.',
      tags: ['Research', 'Design'],
    },
    {
      title: 'Building Accessible Forms That Convert',
      desc: 'Best practices for creating inclusive form experiences that improve completion rates for all users.',
      tags: ['Design', 'Product'],
    },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: cardGap }}>
      {/* Search bar */}
      <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
        <div
          style={{
            ...inputStyle(t),
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            color: t.textPrimary,
          }}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke={t.textTertiary} strokeWidth="1.5">
            <circle cx="7" cy="7" r="5" />
            <path d="M11 11L14 14" />
          </svg>
          <span style={{ color: t.textTertiary }}>Search articles, topics, authors...</span>
        </div>
      </div>

      {/* Filter chips */}
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        {tags.map((tag, i) => (
          <div
            key={tag}
            style={{
              padding: '6px 16px',
              borderRadius: '999px',
              fontSize: t.small.size,
              fontWeight: 500,
              cursor: 'pointer',
              background: i === 0 ? t.brandDefault : 'transparent',
              color: i === 0 ? (resolveColor(t.btn.primary_text, t.ct) || '#fff') : t.textSecondary,
              border: i === 0 ? 'none' : `1px solid ${t.ct.border.subtle}`,
            }}
          >
            {tag}
          </div>
        ))}
      </div>

      {/* Content cards grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: cardGap,
        }}
      >
        {feedCards.map(({ title, desc, tags: cardTags }) => (
          <div
            key={title}
            style={{
              ...cardStyle(t, '0'),
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            {imagePlaceholder(t, '140px')}
            <div style={{ padding: t.card.padding || '16px', display: 'flex', flexDirection: 'column', gap: '10px', flex: 1 }}>
              <h3
                style={{
                  color: t.textPrimary,
                  fontSize: t.h3.size,
                  fontWeight: t.h3.weight,
                  lineHeight: t.h3.lineHeight,
                  margin: 0,
                }}
              >
                {title}
              </h3>
              <p
                style={{
                  color: t.textSecondary,
                  fontSize: t.body.size,
                  fontWeight: t.body.weight,
                  lineHeight: t.body.lineHeight,
                  margin: 0,
                }}
              >
                {desc}
              </p>
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '4px' }}>
                {cardTags.map(tag => (
                  <span
                    key={tag}
                    style={{
                      padding: '2px 10px',
                      borderRadius: '999px',
                      fontSize: '11px',
                      fontWeight: 500,
                      background: t.ct.surface.muted,
                      color: t.textSecondary,
                    }}
                  >
                    {tag}
                  </span>
                ))}
              </div>
              <div style={{ marginTop: 'auto', paddingTop: '8px' }}>
                <span style={{ color: t.brandDefault, fontSize: t.small.size, fontWeight: 600, cursor: 'pointer' }}>
                  Read article &rarr;
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '4px', padding: '8px 0' }}>
        <div
          style={{
            ...outlineBtnStyle(t, '13px'),
            padding: '8px 14px',
          }}
        >
          &larr; Prev
        </div>
        {[1, 2, 3].map(n => (
          <div
            key={n}
            style={{
              width: '36px',
              height: '36px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: t.btn.radius || '6px',
              fontSize: '13px',
              fontWeight: n === 1 ? 600 : 400,
              cursor: 'pointer',
              background: n === 1 ? resolveColor(t.btn.primary_bg, t.ct) : 'transparent',
              color: n === 1 ? resolveColor(t.btn.primary_text, t.ct) : t.textSecondary,
              border: n === 1 ? 'none' : `1px solid ${t.ct.border.subtle}`,
            }}
          >
            {n}
          </div>
        ))}
        <div
          style={{
            ...outlineBtnStyle(t, '13px'),
            padding: '8px 14px',
          }}
        >
          Next &rarr;
        </div>
      </div>

      {/* Load more */}
      <div style={{ textAlign: 'center' }}>
        <div
          style={{
            ...outlineBtnStyle(t, '14px'),
            padding: '12px 32px',
          }}
        >
          Load More Articles
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Full mode wrapper
// ---------------------------------------------------------------------------

function renderFull(t: ResolvedTokens, activePage: PreviewPage): React.JSX.Element {
  const sectionGap = t.spacing.section_gap || '32px'

  let pageContent: React.JSX.Element
  switch (activePage) {
    case 'dashboard':
      pageContent = renderDashboard(t)
      break
    case 'settings':
      pageContent = renderSettings(t)
      break
    case 'feed':
      pageContent = renderFeed(t)
      break
    case 'landing':
    default:
      pageContent = renderLanding(t)
      break
  }

  return (
    <div
      style={{
        ...(t.isGradientBg ? { backgroundImage: t.canvasBg } : { backgroundColor: t.canvasBg }),
        fontFamily: t.fontFamily,
        padding: sectionGap,
        minHeight: '100%',
        display: 'flex',
        flexDirection: 'column',
        gap: t.spacing.card_gap || '24px',
      }}
    >
      {pageContent}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main component export
// ---------------------------------------------------------------------------

export function StylePreview({
  guide,
  accentGuide,
  modifiers,
  size = 'compact',
  styleName,
  activePage = 'landing',
}: StylePreviewProps) {
  const merged = mergeTokens(guide, accentGuide, modifiers)
  const tokens = resolveTokens(merged)

  if (size === 'compact') {
    return renderCompact(tokens, styleName)
  }

  return renderFull(tokens, activePage)
}
