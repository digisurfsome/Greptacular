/**
 * React Query hooks for Tool Factory operations
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as api from '../lib/api'
import type { TFToolStatus, TFThemeConfig } from '../lib/types'

// ============================================================================
// Tool CRUD
// ============================================================================

export function useTools(status?: TFToolStatus) {
  return useQuery({
    queryKey: ['tf-tools', status],
    queryFn: () => api.fetchTools(status),
  })
}

export function useTool(toolId: string | null) {
  return useQuery({
    queryKey: ['tf-tool', toolId],
    queryFn: () => api.fetchTool(toolId!),
    enabled: !!toolId,
  })
}

export function useArchiveTool() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (toolId: string) => api.archiveTool(toolId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tf-tools'] })
    },
  })
}

export function useToolStats() {
  return useQuery({
    queryKey: ['tf-tool-stats'],
    queryFn: api.fetchToolStats,
    staleTime: 30_000,
  })
}

// ============================================================================
// Generation
// ============================================================================

export function useGenerateBlueprint() {
  return useMutation({
    mutationFn: ({ projectId, theme }: { projectId: string; theme?: TFThemeConfig | null }) =>
      api.generateBlueprint(projectId, theme),
  })
}

export function useUploadPRD() {
  return useMutation({
    mutationFn: ({ content, filename }: { content: string; filename: string }) =>
      api.uploadPRD(content, filename),
  })
}

export function useDeployTool() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ toolId, folderId }: { toolId: string; folderId?: string }) =>
      api.deployTool(toolId, folderId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tf-tools'] })
    },
  })
}

// ============================================================================
// Google Auth
// ============================================================================

export function useGoogleAuthStatus() {
  return useQuery({
    queryKey: ['tf-google-auth'],
    queryFn: api.fetchGoogleAuthStatus,
    staleTime: 60_000,
  })
}

export function useGoogleAuthUrl() {
  return useQuery({
    queryKey: ['tf-google-auth-url'],
    queryFn: api.fetchGoogleAuthUrl,
    enabled: false, // Only fetch on demand
  })
}
