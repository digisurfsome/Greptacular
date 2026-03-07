/**
 * React Query hooks for orchestrator commit history.
 *
 * Supports optional filtering by feature ID so the operator
 * can see which commits relate to a specific feature.
 */

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import * as api from '../lib/api'

export function useCommits(projectName: string) {
  const [commitFeatureFilter, setCommitFeatureFilter] = useState<number | null>(null)

  const commitsQuery = useQuery({
    queryKey: ['commits', projectName, commitFeatureFilter],
    queryFn: () =>
      api.getProjectCommits(
        projectName,
        commitFeatureFilter ?? undefined,
        50
      ),
    enabled: !!projectName,
  })

  return {
    commits: commitsQuery.data?.commits ?? [],
    commitFeatureFilter,
    setCommitFeatureFilter,
    commitsLoading: commitsQuery.isLoading,
  }
}
