/**
 * React Query hooks for Tool Factory theme operations
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as api from '../lib/api'
import type { TFThemeConfig } from '../lib/types'

export function useThemes() {
  return useQuery({
    queryKey: ['tf-themes'],
    queryFn: api.fetchThemes,
    staleTime: 5 * 60_000,
  })
}

export function useTheme(themeId: string | null) {
  return useQuery({
    queryKey: ['tf-theme', themeId],
    queryFn: () => api.fetchTheme(themeId!),
    enabled: !!themeId,
  })
}

export function useExtractTheme() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (imageFile: File) => api.extractTheme(imageFile),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tf-themes'] })
    },
  })
}

export function useThemePreview() {
  return useMutation({
    mutationFn: (themeId: string) => api.previewTheme(themeId),
  })
}

export function useSwapTheme() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ toolId, themeId }: { toolId: string; themeId: string }) =>
      api.swapTheme(toolId, themeId),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['tf-tools'] })
      queryClient.invalidateQueries({ queryKey: ['tf-tool', variables.toolId] })
    },
  })
}

export function useCreateCustomTheme() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (config: Partial<TFThemeConfig>) => api.createCustomTheme(config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tf-themes'] })
    },
  })
}
