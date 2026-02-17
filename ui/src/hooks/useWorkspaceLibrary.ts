/**
 * React Query hooks for workspace library and repository operations.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  listGlobalLibraryFiles,
  listConversationLibraryFiles,
  getActiveLibraryFiles,
  uploadLibraryFile,
  uploadLibraryText,
  getLibraryFileContent,
  deleteLibraryFile,
  toggleLibraryFile,
  listRepositories,
  connectRepository,
  disconnectRepository,
  syncRepository,
  getRepoTree,
} from '../lib/api'
// Types (LibraryFile, ConnectedRepo, RepoTreeEntry) are inferred from API return types

// Query keys
const LIBRARY_KEYS = {
  global: ['workspace', 'library', 'global'] as const,
  conversation: (id: number) => ['workspace', 'library', 'conversation', id] as const,
  active: (id: number) => ['workspace', 'library', 'active', id] as const,
  content: (fileId: number) => ['workspace', 'library', 'content', fileId] as const,
}

export function useGlobalFiles() {
  return useQuery({
    queryKey: LIBRARY_KEYS.global,
    queryFn: listGlobalLibraryFiles,
  })
}

export function useConversationFiles(conversationId: number | null) {
  return useQuery({
    queryKey: conversationId ? LIBRARY_KEYS.conversation(conversationId) : [],
    queryFn: () => listConversationLibraryFiles(conversationId!),
    enabled: !!conversationId,
  })
}

export function useActiveFiles(conversationId: number | null) {
  return useQuery({
    queryKey: conversationId ? LIBRARY_KEYS.active(conversationId) : [],
    queryFn: () => getActiveLibraryFiles(conversationId!),
    enabled: !!conversationId,
  })
}

export function useFileContent(fileId: number | null) {
  return useQuery({
    queryKey: fileId ? LIBRARY_KEYS.content(fileId) : [],
    queryFn: () => getLibraryFileContent(fileId!),
    enabled: !!fileId,
  })
}

export function useToggleFile(conversationId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (fileId: number) => toggleLibraryFile(fileId, conversationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: LIBRARY_KEYS.conversation(conversationId) })
      queryClient.invalidateQueries({ queryKey: LIBRARY_KEYS.active(conversationId) })
      queryClient.invalidateQueries({ queryKey: LIBRARY_KEYS.global })
    },
  })
}

export function useUploadFile() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: { file: File; conversationId?: number; displayName?: string; tags?: string }) => {
      return uploadLibraryFile(data.file, data.conversationId, data.displayName, data.tags)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workspace', 'library'] })
    },
  })
}

export function useUploadText() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: { filename: string; content: string; conversationId?: number; displayName?: string; tags?: string }) => {
      return uploadLibraryText(data.filename, data.content, data.conversationId, data.displayName, data.tags)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workspace', 'library'] })
    },
  })
}

export function useDeleteFile() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (fileId: number) => deleteLibraryFile(fileId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workspace', 'library'] })
    },
  })
}

// Repository hooks

export function useConnectedRepos(conversationId: number | null) {
  return useQuery({
    queryKey: ['workspace', 'repos', conversationId],
    queryFn: () => listRepositories(conversationId ?? undefined),
  })
}

export function useConnectRepo() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: { repoUrl: string; token: string; branch: string; conversationId?: number }) =>
      connectRepository(data.repoUrl, data.token, data.branch, data.conversationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workspace', 'repos'] })
    },
  })
}

export function useSyncRepo() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (repoId: number) => syncRepository(repoId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workspace', 'repos'] })
    },
  })
}

export function useDisconnectRepo() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (repoId: number) => disconnectRepository(repoId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workspace', 'repos'] })
    },
  })
}

export function useRepoTree(repoId: number | null) {
  return useQuery({
    queryKey: ['workspace', 'repos', 'tree', repoId],
    queryFn: () => getRepoTree(repoId!),
    enabled: !!repoId,
  })
}
