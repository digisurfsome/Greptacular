/**
 * React Query hooks for workspace category CRUD operations.
 *
 * Provides TanStack Query v5 hooks for listing, creating, updating,
 * and deleting workspace categories. Invalidates both category and
 * conversation queries on mutations to keep the sidebar current.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  listWorkspaceCategories,
  createWorkspaceCategory,
  updateWorkspaceCategory,
  deleteWorkspaceCategory,
} from '../lib/api'

const CATEGORIES_KEY = ['workspace', 'categories'] as const

/** Hook to fetch all workspace categories. */
export function useWorkspaceCategories() {
  return useQuery({
    queryKey: [...CATEGORIES_KEY],
    queryFn: listWorkspaceCategories,
  })
}

/** Hook to create a new workspace category. */
export function useCreateCategory() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ name, color }: { name: string; color: string }) =>
      createWorkspaceCategory(name, color),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [...CATEGORIES_KEY] })
    },
  })
}

/** Hook to update a workspace category's name or color. */
export function useUpdateCategory() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, name, color }: { id: number; name: string; color: string }) =>
      updateWorkspaceCategory(id, name, color),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [...CATEGORIES_KEY] })
    },
  })
}

/** Hook to delete a workspace category. */
export function useDeleteCategory() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => deleteWorkspaceCategory(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [...CATEGORIES_KEY] })
      queryClient.invalidateQueries({ queryKey: ['workspace', 'conversations'] })
    },
  })
}
