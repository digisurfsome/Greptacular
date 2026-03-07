/**
 * Composite hook that wires together all orchestrator sub-hooks
 * into a single return value.
 *
 * This is the PUBLIC API for pages — individual sub-hooks
 * (useApprovals, useCheckpoints, etc.) are implementation details
 * and should not be imported directly by page components.
 */

import { useApprovals } from './useApprovals'
import { useCheckpoints } from './useCheckpoints'
import { useActionLog } from './useActionLog'
import { useVerificationHistory } from './useVerificationHistory'
import { useCommits } from './useCommits'
import type {
  ApprovalRequest,
  Checkpoint,
  RollbackPreview,
  ActionLogEntry,
  ActionLogSummary,
  ActionLogFilters,
  PaginatedResult,
  VerificationResult,
  Commit,
} from '../lib/types'

export interface UseOrchestratorSessionReturn {
  // Approvals
  pendingApprovals: ApprovalRequest[]
  approvalHistory: ApprovalRequest[]
  approveRequest: (id: number) => Promise<void>
  denyRequest: (id: number, reason?: string) => Promise<void>
  approvalsLoading: boolean

  // Checkpoints
  checkpoints: Checkpoint[]
  createCheckpoint: (label: string) => Promise<void>
  rollbackToCheckpoint: (id: number) => Promise<RollbackPreview>
  confirmRollback: (id: number) => Promise<void>
  checkpointsLoading: boolean

  // Action Log
  actionLog: PaginatedResult<ActionLogEntry>
  actionLogSummary: ActionLogSummary | null
  actionLogFilters: ActionLogFilters
  setActionLogFilters: (filters: ActionLogFilters) => void
  actionLogLoading: boolean

  // Verifications
  getVerificationHistory: (featureId: number) => VerificationResult[]
  recentFailures: VerificationResult[]
  verificationsLoading: boolean

  // Commits
  commits: Commit[]
  commitFeatureFilter: number | null
  setCommitFeatureFilter: (featureId: number | null) => void
  commitsLoading: boolean
}

export function useOrchestratorSession(projectName: string): UseOrchestratorSessionReturn {
  const approvals = useApprovals(projectName)
  const checkpoints = useCheckpoints(projectName)
  const actionLog = useActionLog(projectName)
  const verifications = useVerificationHistory(projectName)
  const commits = useCommits(projectName)

  return {
    ...approvals,
    ...checkpoints,
    ...actionLog,
    ...verifications,
    ...commits,
  }
}
