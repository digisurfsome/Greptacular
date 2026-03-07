/**
 * React Query hooks for orchestrator approval gates.
 *
 * Pending approvals poll every 2 seconds so the operator sees
 * agent-blocked requests almost immediately.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as api from '../lib/api'

export function useApprovals(projectName: string) {
  const queryClient = useQueryClient()

  const pendingQuery = useQuery({
    queryKey: ['approvals', projectName, 'pending'],
    queryFn: () => api.getApprovals(projectName, 'pending'),
    refetchInterval: 2000, // Poll every 2 seconds for real-time approval notifications
    enabled: !!projectName,
  })

  const historyQuery = useQuery({
    queryKey: ['approvals', projectName, 'all'],
    queryFn: () => api.getApprovals(projectName, undefined, 100),
    enabled: !!projectName,
  })

  const approveMutation = useMutation({
    mutationFn: (id: number) =>
      api.resolveApproval(projectName, id, { status: 'approved', resolved_by: 'operator' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approvals', projectName] })
    },
  })

  const denyMutation = useMutation({
    mutationFn: ({ id }: { id: number; reason?: string }) =>
      api.resolveApproval(projectName, id, { status: 'denied', resolved_by: 'operator' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approvals', projectName] })
    },
  })

  return {
    pendingApprovals: pendingQuery.data?.approvals ?? [],
    approvalHistory: historyQuery.data?.approvals ?? [],
    approveRequest: async (id: number) => {
      await approveMutation.mutateAsync(id)
    },
    denyRequest: async (id: number, reason?: string) => {
      await denyMutation.mutateAsync({ id, reason })
    },
    approvalsLoading: pendingQuery.isLoading || historyQuery.isLoading,
  }
}
