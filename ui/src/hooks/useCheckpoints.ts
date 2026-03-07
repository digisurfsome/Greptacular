/**
 * React Query hooks for orchestrator checkpoints.
 *
 * Provides list, create, and two-step rollback (preview then confirm).
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as api from '../lib/api'
import type { RollbackPreview } from '../lib/types'

export function useCheckpoints(projectName: string) {
  const queryClient = useQueryClient()

  const listQuery = useQuery({
    queryKey: ['checkpoints', projectName],
    queryFn: () => api.getCheckpoints(projectName),
    enabled: !!projectName,
  })

  const createMutation = useMutation({
    mutationFn: (label: string) => api.createCheckpoint(projectName, label),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['checkpoints', projectName] })
    },
  })

  // Preview rollback — returns a RollbackPreview without actually rolling back
  const rollbackPreviewMutation = useMutation({
    mutationFn: (id: number) => api.rollbackCheckpoint(projectName, id, false),
  })

  // Confirm rollback — actually performs the rollback
  const confirmRollbackMutation = useMutation({
    mutationFn: (id: number) => api.rollbackCheckpoint(projectName, id, true),
    onSuccess: () => {
      // Rollback changes features and git state, so invalidate broadly
      queryClient.invalidateQueries({ queryKey: ['checkpoints', projectName] })
      queryClient.invalidateQueries({ queryKey: ['features', projectName] })
      queryClient.invalidateQueries({ queryKey: ['commits', projectName] })
    },
  })

  return {
    checkpoints: listQuery.data?.checkpoints ?? [],
    createCheckpoint: async (label: string) => {
      await createMutation.mutateAsync(label)
    },
    rollbackToCheckpoint: async (id: number): Promise<RollbackPreview> => {
      return rollbackPreviewMutation.mutateAsync(id)
    },
    confirmRollback: async (id: number) => {
      await confirmRollbackMutation.mutateAsync(id)
    },
    checkpointsLoading: listQuery.isLoading,
  }
}
