/**
 * React Query hooks for orchestrator verification results.
 *
 * Fetches recent failures across all features, and provides a
 * helper to get the verification history for a specific feature.
 */

import { useQuery, useQueryClient } from '@tanstack/react-query'
import * as api from '../lib/api'
import type { VerificationResult } from '../lib/types'

export function useVerificationHistory(projectName: string) {
  const queryClient = useQueryClient()

  // Fetch only failures so the operator sees what needs attention
  const failuresQuery = useQuery({
    queryKey: ['verifications', projectName, 'failures'],
    queryFn: () => api.getAllVerifications(projectName, false, 50),
    enabled: !!projectName,
  })

  /**
   * Return cached verification history for a specific feature.
   * If data has not been fetched yet, trigger a query and return
   * an empty array until it resolves.
   */
  const getVerificationHistory = (featureId: number): VerificationResult[] => {
    const cached = queryClient.getQueryData<{ verifications: VerificationResult[]; feature_id: number }>(
      ['verifications', projectName, 'feature', featureId]
    )

    if (cached) {
      return cached.verifications
    }

    // Prefetch in background — the caller will get data on re-render
    queryClient.prefetchQuery({
      queryKey: ['verifications', projectName, 'feature', featureId],
      queryFn: () => api.getFeatureVerifications(projectName, featureId, 20),
    })

    return []
  }

  return {
    getVerificationHistory,
    recentFailures: failuresQuery.data?.verifications ?? [],
    verificationsLoading: failuresQuery.isLoading,
  }
}
