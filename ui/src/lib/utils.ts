import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Parse a timestamp string from the API, treating it as UTC if no timezone
 * indicator is present.
 *
 * The backend stores timestamps with `datetime.now(timezone.utc)`, but
 * SQLite strips timezone info. So `.isoformat()` returns strings like
 * `2024-02-21T02:07:00` without a `Z` or `+00:00` suffix. JavaScript's
 * `new Date()` then interprets these as local time, which is wrong.
 *
 * This function appends `Z` when no timezone indicator is found so that
 * the Date is created as UTC and `toLocaleTimeString()` converts correctly
 * to the user's local timezone.
 */
export function parseUtcTimestamp(ts: string): Date {
  // If already has timezone indicator (Z, +HH:MM, or -HH:MM after T), parse as-is
  if (/[Z]$/i.test(ts) || /[+-]\d{2}:\d{2}$/.test(ts)) {
    return new Date(ts)
  }
  // Append Z to treat as UTC
  return new Date(ts + 'Z')
}
