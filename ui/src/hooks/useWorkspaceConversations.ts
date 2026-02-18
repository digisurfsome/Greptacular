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
} from '../lib/api'

const CONVERSATIONS_KEY = ['workspace', 'conversations'] as const

/** Hook to fetch all workspace conversations with auto-refresh. */
export function useWorkspaceConversations() {
  return useQuery({
    queryKey: [...CONVERSATIONS_KEY],
    queryFn: listWorkspaceConversations,
    refetchInterval: 10_000,
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

/** Hook to update a workspace conversation title, category, or tags. */
export function useUpdateWorkspaceConversation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      conversationId,
      title,
      category,
      tags,
    }: {
      conversationId: number
      title?: string
      category?: string
      tags?: string
    }) => updateWorkspaceConversation(conversationId, { title, category, tags }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [...CONVERSATIONS_KEY] })
    },
  })
}

/** Hook to delete a workspace conversation. */
export function useDeleteWorkspaceConversation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deleteWorkspaceConversation,
    onSuccess: () => {
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
