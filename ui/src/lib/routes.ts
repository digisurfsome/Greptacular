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

/**
 * Check if the current URL hash matches the quad preview route.
 * Format: /#/quad-preview/:styleId
 */
export function isQuadPreviewRoute(): boolean {
  return window.location.hash.startsWith('#/quad-preview/')
}

/**
 * Check if the current URL hash matches the workspace route.
 * Format: /#/workspace
 */
export function isWorkspaceRoute(): boolean {
  return window.location.hash === '#/workspace' ||
         window.location.hash.startsWith('#/workspace/')
}

/**
 * Check if the current URL hash matches the role library route.
 * Format: /#/roles
 */
export function isRoleLibraryRoute(): boolean {
  return window.location.hash === '#/roles' ||
         window.location.hash.startsWith('#/roles/')
}

/**
 * Check if the current URL hash matches the multi-session dashboard route.
 * Format: /#/dashboard
 */
export function isDashboardRoute(): boolean {
  return window.location.hash === '#/dashboard' ||
         window.location.hash.startsWith('#/dashboard/')
}
