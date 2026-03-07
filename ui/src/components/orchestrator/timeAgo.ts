/**
 * Shared relative time formatter for orchestrator widgets.
 *
 * Converts an ISO-8601 timestamp into a human-friendly "X ago" string.
 * Treats bare timestamps (no timezone suffix) as UTC to match the backend
 * convention documented in `lib/utils.ts`.
 */
export function timeAgo(dateStr: string): string {
  // Append 'Z' for bare timestamps so JS parses them as UTC
  const normalized = /[Z]$/i.test(dateStr) || /[+-]\d{2}:\d{2}$/.test(dateStr)
    ? dateStr
    : dateStr + 'Z'
  const seconds = Math.floor((Date.now() - new Date(normalized).getTime()) / 1000)
  if (seconds < 60) return 'Just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`
  return new Date(normalized).toLocaleDateString()
}
