/**
 * React Query hooks for Token Budget data
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as api from '../lib/api'

/**
 * Hook to fetch the current token budget status across all windows.
 * Polls every 30 seconds to keep dashboard data fresh.
 */
export function useTokenBudgetStatus() {
  return useQuery({
    queryKey: ['token-budget-status'],
    queryFn: api.getTokenBudgetStatus,
    refetchInterval: 30_000,
  })
}

/**
 * Hook to fetch token budget history (sessions + calibrations).
 * Polls every 60 seconds for background updates.
 */
export function useTokenBudgetHistory(limit?: number) {
  return useQuery({
    queryKey: ['token-budget-history', limit],
    queryFn: () => api.getTokenBudgetHistory(limit),
    refetchInterval: 60_000,
  })
}

/**
 * Hook to calibrate a token budget window.
 * Invalidates both status and history queries on success.
 */
export function useCalibrateTokenBudget() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ windowType, notes }: { windowType: string; notes?: string }) =>
      api.calibrateTokenBudget(windowType, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['token-budget-status'] })
      queryClient.invalidateQueries({ queryKey: ['token-budget-history'] })
    },
  })
}
