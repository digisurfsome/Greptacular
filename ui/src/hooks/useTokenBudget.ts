/**
 * React Query hooks for Token Budget data
 */

import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as api from '../lib/api'

/** Parse conversation ID from the URL hash (e.g. #/workspace/chat/42 → 42). */
function parseConversationIdFromHash(): number | null {
  const match = window.location.hash.match(/^#\/workspace\/chat\/(\d+)/)
  return match ? parseInt(match[1], 10) : null
}

/**
 * Returns the currently active workspace conversation ID by watching the URL
 * hash. Returns null when not on a workspace chat page. Updates automatically
 * on `hashchange` — no WebSocket, no cross-component state.
 */
export function useCurrentWorkspaceConversationId(): number | null {
  const [id, setId] = useState<number | null>(parseConversationIdFromHash)
  useEffect(() => {
    const handler = () => setId(parseConversationIdFromHash())
    window.addEventListener('hashchange', handler)
    return () => window.removeEventListener('hashchange', handler)
  }, [])
  return id
}

/**
 * Fetches the token log summary for the currently active workspace
 * conversation. Polls every 5 seconds. Returns the full TokenLogSummary
 * (use `current_context_tokens` for the header meter — see types.ts).
 * Subagent (Task tool) usage is already rolled into each main-agent turn,
 * so this shows ONLY the main agent's running total by construction.
 */
export function useCurrentWorkspaceTokenUsage() {
  const conversationId = useCurrentWorkspaceConversationId()
  return useQuery({
    queryKey: ['workspace-token-log-summary', conversationId],
    queryFn: () => api.getTokenLogSummary(conversationId!),
    enabled: conversationId !== null,
    refetchInterval: 5_000,
  })
}

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
