/**
 * Hash-based route helpers.
 *
 * The app uses hash routing for standalone pages that need
 * clean URLs without the main app chrome (e.g., Playwright screenshots).
 */

/**
 * Check if the current URL hash matches the style preview route.
 * Format: /#/style-preview/:styleId/:page
 */
export function isStylePreviewRoute(): boolean {
  return window.location.hash.startsWith('#/style-preview/')
}
