/**
 * usePersistedState - localStorage-backed useState with debounced writes.
 *
 * Drop-in replacement for useState that persists values to localStorage.
 * Loads from localStorage on mount, falls back to defaultValue if missing.
 * Debounces writes (500ms) to avoid thrashing on every keystroke.
 */

import { useState, useEffect, useRef, useCallback } from 'react'

/**
 * Parse a stored JSON string, returning the parsed value or the fallback.
 * Handles malformed JSON gracefully by returning the default.
 */
function loadFromStorage<T>(key: string, defaultValue: T): T {
  try {
    const stored = localStorage.getItem(key)
    if (stored === null) return defaultValue
    return JSON.parse(stored) as T
  } catch {
    // Malformed JSON or storage error — fall back to default
    return defaultValue
  }
}

export function usePersistedState<T>(
  key: string,
  defaultValue: T
): [T, (v: T | ((prev: T) => T)) => void] {
  // Initialize state from localStorage (runs once per mount)
  const [value, setValueInternal] = useState<T>(() => loadFromStorage(key, defaultValue))

  // Ref to track the latest value for the debounced save
  const latestValue = useRef(value)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Keep the ref in sync with state
  useEffect(() => {
    latestValue.current = value
  }, [value])

  // Debounced save to localStorage (500ms)
  useEffect(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current)
    }
    timerRef.current = setTimeout(() => {
      try {
        localStorage.setItem(key, JSON.stringify(value))
      } catch {
        // Storage full or unavailable — silently ignore
      }
    }, 500)

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current)
      }
    }
  }, [key, value])

  // Setter that matches useState signature (value or updater function)
  const setValue = useCallback(
    (v: T | ((prev: T) => T)) => {
      setValueInternal(v)
    },
    []
  )

  return [value, setValue]
}
