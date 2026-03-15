import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as api from '../lib/api'

export function useShredderQueue(status?: string) {
  return useQuery({
    queryKey: ['prd-shredder-queue', status],
    queryFn: () => api.getShredderQueue(status),
    refetchInterval: 5_000,
  })
}

export function useShredderStats() {
  return useQuery({
    queryKey: ['prd-shredder-stats'],
    queryFn: api.getShredderStats,
    refetchInterval: 5_000,
  })
}

export function useShredderStatus() {
  return useQuery({
    queryKey: ['prd-shredder-status'],
    queryFn: api.getShredderStatus,
    refetchInterval: 5_000,
  })
}

export function useShredderItemLogs(itemId: string | null) {
  return useQuery({
    queryKey: ['prd-shredder-logs', itemId],
    queryFn: () => api.getShredderItemLogs(itemId!),
    enabled: !!itemId,
    refetchInterval: 3_000,
  })
}

export function useEnqueuePRD() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { title: string; prd_text: string; target_repo: string; target_branch?: string }) =>
      api.enqueueShredderPRD(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['prd-shredder-queue'] })
      qc.invalidateQueries({ queryKey: ['prd-shredder-stats'] })
    },
  })
}

export function useRetryItem() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (itemId: string) => api.retryShredderItem(itemId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['prd-shredder-queue'] })
      qc.invalidateQueries({ queryKey: ['prd-shredder-stats'] })
    },
  })
}

export function useRetryAllFailed() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: api.retryAllFailedShredder,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['prd-shredder-queue'] })
      qc.invalidateQueries({ queryKey: ['prd-shredder-stats'] })
    },
  })
}

export function useDeleteItem() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (itemId: string) => api.deleteShredderItem(itemId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['prd-shredder-queue'] })
      qc.invalidateQueries({ queryKey: ['prd-shredder-stats'] })
    },
  })
}

// ---------------------------------------------------------------------------
// Build Rules
// ---------------------------------------------------------------------------

export function useBuildRules(category?: string) {
  return useQuery({
    queryKey: ['shredder-rules', category],
    queryFn: () => api.listBuildRules(category),
  })
}

export function useCreateRule() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: api.createBuildRule,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['shredder-rules'] }),
  })
}

export function useUpdateRule() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ ruleId, updates }: { ruleId: string; updates: Partial<api.BuildRule> }) =>
      api.updateBuildRule(ruleId, updates),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['shredder-rules'] }),
  })
}

export function useDeleteRule() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: api.deleteBuildRule,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['shredder-rules'] }),
  })
}

export function useToggleRule() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: api.toggleBuildRule,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['shredder-rules'] }),
  })
}

// ---------------------------------------------------------------------------
// Shredder Config
// ---------------------------------------------------------------------------

export function useShredderConfig() {
  return useQuery({
    queryKey: ['shredder-config'],
    queryFn: api.getShredderConfig,
  })
}

export function useUpdateShredderConfig() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: api.updateShredderConfig,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['shredder-config'] }),
  })
}
