/**
 * React Query hooks for Factory Mode
 *
 * Provides start/stop/status/settings/handoffs for the autonomous factory
 * agent loop. Status polls every 5 seconds while a project is selected.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  factoryStart,
  factoryStop,
  factoryResume,
  factoryStatus,
  factoryUpdateSettings,
  factoryGetHandoffs,
  factoryGetPresets,
  factoryListPhaseDocuments,
  factoryGetPhaseDocument,
  factoryUpdatePhaseDocument,
  factoryDeletePhaseDocument,
  factoryUploadPhaseDocuments,
  type FactoryStartRequest,
  type FactorySettingsRequest,
} from '../lib/api'

/**
 * Poll factory status. Polls every 2s when factory is active (running/waiting),
 * every 5s when idle or completed.
 */
export function useFactoryStatus(projectName: string | null) {
  const query = useQuery({
    queryKey: ['factory-status', projectName],
    queryFn: () => factoryStatus(projectName!),
    enabled: !!projectName,
    refetchInterval: (query) => {
      const status = (query.state.data as { data?: { status?: string } } | undefined)?.data?.status
      return status === 'running' || status === 'waiting_rate_limit' ? 2000 : 5000
    },
  })
  return query
}

/**
 * Start factory mode for a project.
 */
export function useFactoryStart(projectName: string | null) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (req: FactoryStartRequest) => factoryStart(projectName!, req),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['factory-status', projectName] })
    },
  })
}

/**
 * Stop factory mode for a project.
 */
export function useFactoryStop(projectName: string | null) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => factoryStop(projectName!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['factory-status', projectName] })
    },
  })
}

/**
 * Resume factory (skip rate limit wait).
 */
export function useFactoryResume(projectName: string | null) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => factoryResume(projectName!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['factory-status', projectName] })
    },
  })
}

/**
 * Update factory settings (handoff threshold, template, etc.).
 */
export function useFactorySettings(projectName: string | null) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (req: FactorySettingsRequest) => factoryUpdateSettings(projectName!, req),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['factory-status', projectName] })
    },
  })
}

/**
 * Fetch handoff history for a project.
 */
export function useFactoryHandoffs(projectName: string | null) {
  return useQuery({
    queryKey: ['factory-handoffs', projectName],
    queryFn: () => factoryGetHandoffs(projectName!),
    enabled: !!projectName,
  })
}

/**
 * Fetch factory mode presets (global, not project-specific).
 */
export function useFactoryPresets() {
  return useQuery({
    queryKey: ['factory-presets'],
    queryFn: () => factoryGetPresets(),
    staleTime: Infinity, // Presets don't change at runtime
  })
}

// ============================================================================
// Phase PRD Document hooks
// ============================================================================

/**
 * List all phase PRD documents for a project.
 */
export function usePhaseDocuments(projectName: string | null) {
  return useQuery({
    queryKey: ['phase-documents', projectName],
    queryFn: () => factoryListPhaseDocuments(projectName!),
    enabled: !!projectName,
  })
}

/**
 * Fetch the content of a single phase PRD document.
 */
export function usePhaseDocument(projectName: string | null, phaseNum: number | null) {
  return useQuery({
    queryKey: ['phase-document', projectName, phaseNum],
    queryFn: () => factoryGetPhaseDocument(projectName!, phaseNum!),
    enabled: !!projectName && phaseNum !== null,
  })
}

/**
 * Update (save) a phase PRD document's content.
 */
export function useUpdatePhaseDocument(projectName: string | null) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ phaseNum, content }: { phaseNum: number; content: string }) =>
      factoryUpdatePhaseDocument(projectName!, phaseNum, content),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['phase-documents', projectName] })
      queryClient.invalidateQueries({ queryKey: ['phase-document', projectName, variables.phaseNum] })
    },
  })
}

/**
 * Delete a phase PRD document.
 */
export function useDeletePhaseDocument(projectName: string | null) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (phaseNum: number) => factoryDeletePhaseDocument(projectName!, phaseNum),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['phase-documents', projectName] })
    },
  })
}

/**
 * Upload .md/.txt files as phase PRD documents.
 */
export function useUploadPhaseDocuments(projectName: string | null) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (files: File[]) => factoryUploadPhaseDocuments(projectName!, files),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['phase-documents', projectName] })
    },
  })
}
