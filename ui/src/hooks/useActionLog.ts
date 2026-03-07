/**
 * React Query hooks for the orchestrator action log.
 *
 * Manages paginated action entries plus a summary of tool call
 * counts and error rates across the current session.
 */

import { useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import * as api from '../lib/api'
import type { ActionLogFilters, ActionLogSummary, ActionLogEntry, PaginatedResult } from '../lib/types'

const DEFAULT_FILTERS: ActionLogFilters = {
  page: 1,
  limit: 50,
}

const EMPTY_PAGE: PaginatedResult<ActionLogEntry> = {
  items: [],
  total: 0,
  page: 1,
  limit: 50,
  has_more: false,
}

export function useActionLog(projectName: string) {
  const [filters, setFiltersRaw] = useState<ActionLogFilters>(DEFAULT_FILTERS)

  // Wrap setFilters so consumers can pass a partial update
  const setActionLogFilters = useCallback((next: ActionLogFilters) => {
    setFiltersRaw(next)
  }, [])

  const entriesQuery = useQuery({
    queryKey: ['action-log', projectName, filters],
    queryFn: () => api.getActionLog(projectName, filters),
    enabled: !!projectName,
  })

  const summaryQuery = useQuery({
    queryKey: ['action-log-summary', projectName],
    queryFn: () => api.getActionLogSummary(projectName),
    enabled: !!projectName,
  })

  return {
    actionLog: entriesQuery.data ?? EMPTY_PAGE,
    actionLogSummary: (summaryQuery.data as ActionLogSummary) ?? null,
    actionLogFilters: filters,
    setActionLogFilters,
    actionLogLoading: entriesQuery.isLoading || summaryQuery.isLoading,
  }
}
