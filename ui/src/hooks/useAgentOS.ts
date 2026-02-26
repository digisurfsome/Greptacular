/**
 * useAgentOS Hook
 *
 * React Query hooks for the Agent OS PRD creation system.
 * Covers: standards, product, specs, features, gaps, handoff, intake dock, sessions.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  agentOSListStandards,
  agentOSGetStandard,
  agentOSUpdateStandard,
  agentOSInferStandards,
  agentOSListProduct,
  agentOSGetProduct,
  agentOSListFeatures,
  agentOSAddFeature,
  agentOSRemoveFeature,
  agentOSListGaps,
  agentOSResolveGap,
  agentOSAutoResolveGaps,
  agentOSListSpecs,
  agentOSGetSpec,
  agentOSPopulateDB,
  agentOSGetHandoffStatus,
  agentOSAssembleHandoff,
  agentOSGetBuildPlan,
  agentOSListStagedFiles,
  agentOSStageFile,
  agentOSPasteText,
  agentOSTagFile,
  agentOSRemoveStagedFile,
  agentOSGetReadiness,
  agentOSProcessIntake,
  agentOSListSessions,
  agentOSGetSession,
  agentOSCancelSession,
  agentOSAddExpandedFeatures,
  agentOSScanCodebase,
  agentOSGetCREAnalysis,
  agentOSGetCRESummary,
  type AgentOSStagedFile,
  type AgentOSReadinessStatus,
  type AgentOSFeatureCreate,
  type AgentOSFeatureItem,
  type AgentOSGapItem,
  type AgentOSHandoffStatus,
  type AgentOSFileEntry,
  type AgentOSExpandResult,
  type AgentOSCREAnalysis,
} from '@/lib/api'

// Re-export types for consumers
export type {
  AgentOSStagedFile,
  AgentOSReadinessStatus,
  AgentOSFeatureCreate,
  AgentOSFeatureItem,
  AgentOSGapItem,
  AgentOSHandoffStatus,
  AgentOSFileEntry,
  AgentOSExpandResult,
  AgentOSCREAnalysis,
}

// ============================================================================
// Query Key Factory
// ============================================================================

export const agentOSKeys = {
  all: ['agent-os'] as const,
  standards: (projectName: string) => [...agentOSKeys.all, 'standards', projectName] as const,
  standardsFile: (projectName: string, filename: string) =>
    [...agentOSKeys.standards(projectName), filename] as const,
  product: (projectName: string) => [...agentOSKeys.all, 'product', projectName] as const,
  productFile: (projectName: string, filename: string) =>
    [...agentOSKeys.product(projectName), filename] as const,
  specs: (projectName: string) => [...agentOSKeys.all, 'specs', projectName] as const,
  spec: (projectName: string, featureId: number) =>
    [...agentOSKeys.specs(projectName), featureId] as const,
  features: (projectName: string) => [...agentOSKeys.all, 'features', projectName] as const,
  gaps: (projectName: string) => [...agentOSKeys.all, 'gaps', projectName] as const,
  handoff: (projectName: string) => [...agentOSKeys.all, 'handoff', projectName] as const,
  buildPlan: (projectName: string) => [...agentOSKeys.all, 'build-plan', projectName] as const,
  intakeDock: (projectName: string) => [...agentOSKeys.all, 'intake-dock', projectName] as const,
  readiness: (projectName: string) => [...agentOSKeys.all, 'readiness', projectName] as const,
  sessions: () => [...agentOSKeys.all, 'sessions'] as const,
  session: (projectName: string) => [...agentOSKeys.all, 'session', projectName] as const,
  expand: (projectName: string) => [...agentOSKeys.all, 'expand', projectName] as const,
  cre: (projectName: string) => [...agentOSKeys.all, 'cre', projectName] as const,
  creSummary: (projectName: string) => [...agentOSKeys.all, 'cre-summary', projectName] as const,
}

// ============================================================================
// Query Hooks
// ============================================================================

export function useStandards(projectName: string) {
  return useQuery({
    queryKey: agentOSKeys.standards(projectName),
    queryFn: () => agentOSListStandards(projectName),
    enabled: !!projectName,
  })
}

export function useStandardFile(projectName: string, filename: string) {
  return useQuery({
    queryKey: agentOSKeys.standardsFile(projectName, filename),
    queryFn: () => agentOSGetStandard(projectName, filename),
    enabled: !!projectName && !!filename,
  })
}

export function useProductFiles(projectName: string) {
  return useQuery({
    queryKey: agentOSKeys.product(projectName),
    queryFn: () => agentOSListProduct(projectName),
    enabled: !!projectName,
  })
}

export function useProductFile(projectName: string, filename: string) {
  return useQuery({
    queryKey: agentOSKeys.productFile(projectName, filename),
    queryFn: () => agentOSGetProduct(projectName, filename),
    enabled: !!projectName && !!filename,
  })
}

export function useFeatures(projectName: string) {
  return useQuery({
    queryKey: agentOSKeys.features(projectName),
    queryFn: () => agentOSListFeatures(projectName),
    enabled: !!projectName,
  })
}

export function useGaps(projectName: string) {
  return useQuery({
    queryKey: agentOSKeys.gaps(projectName),
    queryFn: () => agentOSListGaps(projectName),
    enabled: !!projectName,
  })
}

export function useSpecs(projectName: string) {
  return useQuery({
    queryKey: agentOSKeys.specs(projectName),
    queryFn: () => agentOSListSpecs(projectName),
    enabled: !!projectName,
  })
}

export function useSpec(projectName: string, featureId: number) {
  return useQuery({
    queryKey: agentOSKeys.spec(projectName, featureId),
    queryFn: () => agentOSGetSpec(projectName, featureId),
    enabled: !!projectName && featureId > 0,
  })
}

export function useStagedFiles(projectName: string) {
  return useQuery({
    queryKey: agentOSKeys.intakeDock(projectName),
    queryFn: () => agentOSListStagedFiles(projectName),
    enabled: !!projectName,
  })
}

export function useReadiness(projectName: string) {
  return useQuery({
    queryKey: agentOSKeys.readiness(projectName),
    queryFn: () => agentOSGetReadiness(projectName),
    enabled: !!projectName,
  })
}

export function useHandoffStatus(projectName: string) {
  return useQuery({
    queryKey: agentOSKeys.handoff(projectName),
    queryFn: () => agentOSGetHandoffStatus(projectName),
    enabled: !!projectName,
  })
}

export function useBuildPlan(projectName: string) {
  return useQuery({
    queryKey: agentOSKeys.buildPlan(projectName),
    queryFn: () => agentOSGetBuildPlan(projectName),
    enabled: !!projectName,
  })
}

export function useAgentOSSessions() {
  return useQuery({
    queryKey: agentOSKeys.sessions(),
    queryFn: agentOSListSessions,
  })
}

export function useAgentOSSession(projectName: string) {
  return useQuery({
    queryKey: agentOSKeys.session(projectName),
    queryFn: () => agentOSGetSession(projectName),
    enabled: !!projectName,
  })
}

// ============================================================================
// Mutation Hooks
// ============================================================================

export function useUpdateStandard(projectName: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ filename, content, location }: { filename: string; content: string; location?: string }) =>
      agentOSUpdateStandard(projectName, filename, content, location),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: agentOSKeys.standards(projectName) })
    },
  })
}

export function useInferStandards(projectName: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => agentOSInferStandards(projectName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: agentOSKeys.standards(projectName) })
    },
  })
}

export function useAddFeature(projectName: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (feature: AgentOSFeatureCreate) => agentOSAddFeature(projectName, feature),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: agentOSKeys.features(projectName) })
    },
  })
}

export function useRemoveFeature(projectName: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (featureId: number) => agentOSRemoveFeature(projectName, featureId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: agentOSKeys.features(projectName) })
    },
  })
}

export function useResolveGap(projectName: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ gapId, resolution }: { gapId: number; resolution: string }) =>
      agentOSResolveGap(projectName, gapId, resolution),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: agentOSKeys.gaps(projectName) })
    },
  })
}

export function useAutoResolveGaps(projectName: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => agentOSAutoResolveGaps(projectName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: agentOSKeys.gaps(projectName) })
    },
  })
}

export function usePopulateDB(projectName: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => agentOSPopulateDB(projectName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: agentOSKeys.handoff(projectName) })
      queryClient.invalidateQueries({ queryKey: agentOSKeys.features(projectName) })
    },
  })
}

export function useAssembleHandoff(projectName: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => agentOSAssembleHandoff(projectName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: agentOSKeys.handoff(projectName) })
    },
  })
}

export function useStageFile(projectName: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (formData: FormData) => agentOSStageFile(projectName, formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: agentOSKeys.intakeDock(projectName) })
      queryClient.invalidateQueries({ queryKey: agentOSKeys.readiness(projectName) })
    },
  })
}

export function usePasteText(projectName: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ filename, content }: { filename: string; content: string }) =>
      agentOSPasteText(projectName, filename, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: agentOSKeys.intakeDock(projectName) })
      queryClient.invalidateQueries({ queryKey: agentOSKeys.readiness(projectName) })
    },
  })
}

export function useTagFile(projectName: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ fileId, tag }: { fileId: string; tag: string }) =>
      agentOSTagFile(projectName, fileId, tag),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: agentOSKeys.intakeDock(projectName) })
      queryClient.invalidateQueries({ queryKey: agentOSKeys.readiness(projectName) })
    },
  })
}

export function useRemoveStagedFile(projectName: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (fileId: string) => agentOSRemoveStagedFile(projectName, fileId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: agentOSKeys.intakeDock(projectName) })
      queryClient.invalidateQueries({ queryKey: agentOSKeys.readiness(projectName) })
    },
  })
}

export function useProcessIntake(projectName: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => agentOSProcessIntake(projectName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: agentOSKeys.intakeDock(projectName) })
      queryClient.invalidateQueries({ queryKey: agentOSKeys.readiness(projectName) })
      queryClient.invalidateQueries({ queryKey: agentOSKeys.standards(projectName) })
      queryClient.invalidateQueries({ queryKey: agentOSKeys.product(projectName) })
    },
  })
}

export function useCancelSession(projectName: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => agentOSCancelSession(projectName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: agentOSKeys.sessions() })
      queryClient.invalidateQueries({ queryKey: agentOSKeys.session(projectName) })
    },
  })
}

// ============================================================================
// Expand Hooks (Phase 7)
// ============================================================================

export function useExpandFeatures(projectName: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (features: Record<string, unknown>[]) =>
      agentOSAddExpandedFeatures(projectName, features),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: agentOSKeys.features(projectName) })
      queryClient.invalidateQueries({ queryKey: agentOSKeys.buildPlan(projectName) })
      queryClient.invalidateQueries({ queryKey: agentOSKeys.handoff(projectName) })
    },
  })
}

// ============================================================================
// CRE Hooks (Phase 7)
// ============================================================================

export function useScanCodebase(projectName: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => agentOSScanCodebase(projectName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: agentOSKeys.cre(projectName) })
      queryClient.invalidateQueries({ queryKey: agentOSKeys.creSummary(projectName) })
    },
  })
}

export function useCREAnalysis(projectName: string) {
  return useQuery({
    queryKey: agentOSKeys.cre(projectName),
    queryFn: () => agentOSGetCREAnalysis(projectName),
    enabled: !!projectName,
  })
}

export function useCRESummary(projectName: string) {
  return useQuery({
    queryKey: agentOSKeys.creSummary(projectName),
    queryFn: () => agentOSGetCRESummary(projectName),
    enabled: !!projectName,
  })
}
