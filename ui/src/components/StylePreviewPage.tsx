/**
 * StylePreviewPage Component
 *
 * Standalone page for rendering a single style preview without any modal chrome.
 * Used for:
 * - Playwright screenshot generation (automated)
 * - Shareable preview URLs
 *
 * Route: /#/style-preview/:styleId/:page
 *
 * Reads styleId and page from the URL hash and fetches the style data via API,
 * then renders the StylePreview component full-screen.
 */

import { useState, useEffect, useMemo } from 'react'
import { StylePreview } from './StylePreview'
import type { PreviewPage } from './StylePreview'
import type { StyleOption } from '../lib/types'
import { listStyles } from '../lib/api'

const VALID_PAGES: PreviewPage[] = ['landing', 'dashboard', 'settings', 'feed']

interface ParsedRoute {
  styleId: string
  page: PreviewPage
  modifiers: string[]
  accentId: string | null
}

function parseHash(): ParsedRoute | null {
  const hash = window.location.hash
  // Format: #/style-preview/:styleId/:page?modifiers=a,b&accent=c
  const match = hash.match(/^#\/style-preview\/([^/]+)\/([^?]+)(?:\?(.*))?$/)
  if (!match) return null

  const styleId = decodeURIComponent(match[1])
  const page = match[2] as PreviewPage
  if (!VALID_PAGES.includes(page)) return null

  // Parse optional query params
  const params = new URLSearchParams(match[3] || '')
  const modifiers = params.get('modifiers')?.split(',').filter(Boolean) || []
  const accentId = params.get('accent') || null

  return { styleId, page, modifiers, accentId }
}

export function StylePreviewPage() {
  const [styles, setStyles] = useState<StyleOption[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [route, setRoute] = useState<ParsedRoute | null>(parseHash)

  // Listen for hash changes
  useEffect(() => {
    const handler = () => setRoute(parseHash())
    window.addEventListener('hashchange', handler)
    return () => window.removeEventListener('hashchange', handler)
  }, [])

  // Fetch all styles with tokens
  useEffect(() => {
    listStyles(true)
      .then(setStyles)
      .catch((err) => setError(err.message || 'Failed to load styles'))
  }, [])

  const resolvedStyle = useMemo(() => {
    if (!styles || !route) return null
    return styles.find(s => s.id === route.styleId) || null
  }, [styles, route])

  const accentGuide = useMemo(() => {
    if (!styles || !route?.accentId) return undefined
    return styles.find(s => s.id === route.accentId)?.style_guide
  }, [styles, route])

  if (!route) {
    return (
      <div style={{ padding: 40, fontFamily: 'system-ui' }}>
        <h1>Style Preview</h1>
        <p>Invalid URL. Expected format: <code>/#/style-preview/:styleId/:page</code></p>
        <p>Valid pages: {VALID_PAGES.join(', ')}</p>
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
        <p>No style with ID &quot;{route.styleId}&quot; was found.</p>
        <p>Available styles: {styles.map(s => s.id).join(', ')}</p>
      </div>
    )
  }

  return (
    <div style={{ width: '100vw', minHeight: '100vh' }}>
      <StylePreview
        guide={resolvedStyle.style_guide}
        accentGuide={accentGuide}
        modifiers={route.modifiers}
        size="full"
        styleName={resolvedStyle.name}
        activePage={route.page}
      />
    </div>
  )
}

