/**
 * React Query hooks for workspace conversation CRUD operations.
 *
 * Provides TanStack Query v5 hooks for listing, fetching, creating,
 * updating, and deleting workspace conversations. The list query
 * auto-refreshes every 10 seconds to keep the sidebar current.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  listWorkspaceConversations,
  getWorkspaceConversation,
  createWorkspaceConversation,
  updateWorkspaceConversation,
  deleteWorkspaceConversation,
  bulkDeleteWorkspaceConversations,
  fetchWorkspaceProviders,
} from '../lib/api'

const CONVERSATIONS_KEY = ['workspace', 'conversations'] as const
const PROVIDERS_KEY = ['workspace', 'providers'] as const

/** Hook to fetch workspace provider definitions (models per provider). Cached for 5 minutes. */
export function useWorkspaceProviders() {
  return useQuery({
    queryKey: [...PROVIDERS_KEY],
    queryFn: fetchWorkspaceProviders,
    staleTime: 5 * 60 * 1000,  // providers rarely change — cache 5 min
  })
}

/** Hook to fetch all workspace conversations with auto-refresh. */
export function useWorkspaceConversations() {
  return useQuery({
    queryKey: [...CONVERSATIONS_KEY],
    queryFn: listWorkspaceConversations,
    refetchInterval: 30_000,
  })
}

/** Hook to fetch a single workspace conversation with messages. */
export function useWorkspaceConversation(conversationId: number | null) {
  return useQuery({
    queryKey: [...CONVERSATIONS_KEY, conversationId],
    queryFn: () => getWorkspaceConversation(conversationId!),
    enabled: conversationId !== null,
  })
}

/** Hook to create a new workspace conversation. */
export function useCreateWorkspaceConversation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createWorkspaceConversation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [...CONVERSATIONS_KEY] })
    },
  })
}

/** Hook to update a workspace conversation title, category, working_directory, or tags. */
export function useUpdateWorkspaceConversation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      conversationId,
      title,
      category,
      working_directory,
      tags,
    }: {
      conversationId: number
      title?: string
      category?: string
      working_directory?: string
      tags?: string
    }) => updateWorkspaceConversation(conversationId, { title, category, working_directory, tags }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [...CONVERSATIONS_KEY] })
    },
  })
}

/** Hook to delete a workspace conversation.
 *
 * Uses optimistic removal to immediately hide the conversation from the
 * sidebar, preventing the "delete then reappear" race condition caused by
 * in-flight refetch intervals overwriting the cache before the server
 * confirms the deletion.
 */
export function useDeleteWorkspaceConversation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deleteWorkspaceConversation,
    onMutate: async (conversationId: number) => {
      // Cancel any in-flight refetches so they don't overwrite our optimistic removal
      await queryClient.cancelQueries({ queryKey: [...CONVERSATIONS_KEY] })

      // Snapshot previous value for rollback on error
      const previous = queryClient.getQueryData([...CONVERSATIONS_KEY])

      // Optimistically remove the conversation from the list cache
      queryClient.setQueryData(
        [...CONVERSATIONS_KEY],
        (old: Array<{ id: number; [key: string]: unknown }> | undefined) =>
          old?.filter(conv => conv.id !== conversationId)
      )

      // Remove the individual conversation detail cache
      queryClient.removeQueries({ queryKey: [...CONVERSATIONS_KEY, conversationId] })

      return { previous }
    },
    onError: (err, _vars, context) => {
      // Roll back to snapshot on error
      if (context?.previous) {
        queryClient.setQueryData([...CONVERSATIONS_KEY], context.previous)
      }
      console.error('Failed to delete conversation:', err)
    },
    onSettled: () => {
      // Always refetch after mutation settles to ensure server state is authoritative
      queryClient.invalidateQueries({ queryKey: [...CONVERSATIONS_KEY] })
    },
  })
}

/** Hook to bulk delete multiple workspace conversations.
 *
 * Uses optimistic removal identical to single delete but for multiple IDs.
 */
export function useBulkDeleteWorkspaceConversations() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: bulkDeleteWorkspaceConversations,
    onMutate: async (conversationIds: number[]) => {
      await queryClient.cancelQueries({ queryKey: [...CONVERSATIONS_KEY] })
      const previous = queryClient.getQueryData([...CONVERSATIONS_KEY])

      queryClient.setQueryData(
        [...CONVERSATIONS_KEY],
        (old: Array<{ id: number; [key: string]: unknown }> | undefined) =>
          old?.filter(conv => !conversationIds.includes(conv.id))
      )

      for (const id of conversationIds) {
        queryClient.removeQueries({ queryKey: [...CONVERSATIONS_KEY, id] })
      }

      return { previous }
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData([...CONVERSATIONS_KEY], context.previous)
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: [...CONVERSATIONS_KEY] })
    },
  })
}

/** Hook to toggle a workspace conversation's pinned state. */
export function useTogglePin() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ conversationId, pinned }: { conversationId: number; pinned: boolean }) =>
      updateWorkspaceConversation(conversationId, { pinned }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [...CONVERSATIONS_KEY] })
    },
  })
}

/** Hook to change a workspace conversation's category. */
export function useChangeCategory() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ conversationId, category }: { conversationId: number; category: string }) =>
      updateWorkspaceConversation(conversationId, { category }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [...CONVERSATIONS_KEY] })
    },
  })
}

/** Hook to toggle a workspace conversation's context mode between 1m and 200k. */
export function useToggleContextMode() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ conversationId, context_mode }: { conversationId: number; context_mode: string }) =>
      updateWorkspaceConversation(conversationId, { context_mode }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [...CONVERSATIONS_KEY] })
    },
  })
}

/** Hook to cycle a workspace conversation's model+context badge (O-1M -> S-1M -> O-200K -> O-1M).
 *
 * Uses optimistic updates to immediately reflect the change in the UI,
 * preventing stale closure bugs and flickering on rapid clicks.
 */
export function useCycleModelBadge() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ conversationId, model, context_mode }: { conversationId: number; model: string; context_mode: string }) =>
      updateWorkspaceConversation(conversationId, { model, context_mode }),
    onMutate: async ({ conversationId, model, context_mode }) => {
      // Cancel any in-flight refetches so they don't overwrite our optimistic update
      await queryClient.cancelQueries({ queryKey: [...CONVERSATIONS_KEY] })

      // Snapshot previous value for rollback on error
      const previous = queryClient.getQueryData([...CONVERSATIONS_KEY])

      // Optimistically update the conversation list cache
      queryClient.setQueryData(
        [...CONVERSATIONS_KEY],
        (old: Array<{ id: number; model?: string; context_mode?: string; [key: string]: unknown }> | undefined) =>
          old?.map(conv =>
            conv.id === conversationId
              ? { ...conv, model, context_mode }
              : conv
          )
      )

      // Also update the individual conversation detail cache if it exists
      queryClient.setQueryData(
        [...CONVERSATIONS_KEY, conversationId],
        (old: { model?: string; context_mode?: string; [key: string]: unknown } | undefined) =>
          old ? { ...old, model, context_mode } : old
      )

      return { previous }
    },
    onError: (_err, _vars, context) => {
      // Roll back to snapshot on error
      if (context?.previous) {
        queryClient.setQueryData([...CONVERSATIONS_KEY], context.previous)
      }
    },
    onSettled: (_data, _err, variables) => {
      // Always refetch after mutation settles to ensure server state is authoritative
      queryClient.invalidateQueries({ queryKey: [...CONVERSATIONS_KEY] })
      // Also invalidate the specific conversation detail
      queryClient.invalidateQueries({ queryKey: [...CONVERSATIONS_KEY, variables.conversationId] })
    },
  })
}
