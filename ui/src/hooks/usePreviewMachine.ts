/**
 * React Query hooks for the Preview Machine pipeline.
 *
 * Polling only — no WebSockets. The status query refetches every 2s while a
 * stage is running so the log viewer stays live without a socket connection.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import * as api from '../lib/api'
import type { PreviewMachineStage } from '../lib/types'

const STATUS_KEY = ['preview-machine', 'status']
const FILES_KEY = ['preview-machine', 'files']

/**
 * Live pipeline status. Polls every 2s while a stage is running; stops polling
 * once the stage finishes so we don't hammer the server when idle.
 */
export function usePreviewMachineStatus() {
  return useQuery({
    queryKey: STATUS_KEY,
    queryFn: api.getPreviewMachineStatus,
    // refetchInterval receives the latest query result; poll only when running.
    refetchInterval: (query) => (query.state.data?.running ? 2000 : false),
  })
}

/** CSV files available as stage inputs (newest first). */
export function usePreviewMachineFiles() {
  return useQuery({
    queryKey: FILES_KEY,
    queryFn: api.listPreviewMachineFiles,
  })
}

/** Start a pipeline stage. Invalidates status + files on success. */
export function useRunPreviewMachineStage() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ stage, args }: { stage: PreviewMachineStage; args: string[] }) =>
      api.runPreviewMachineStage(stage, args),
    onSuccess: (status) => {
      // Seed the status cache immediately so the UI flips to "running" without
      // waiting for the next poll, then refresh the file list.
      qc.setQueryData(STATUS_KEY, status)
      qc.invalidateQueries({ queryKey: STATUS_KEY })
      qc.invalidateQueries({ queryKey: FILES_KEY })
    },
  })
}

/** Stop the running stage. */
export function useStopPreviewMachine() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: api.stopPreviewMachine,
    onSuccess: (status) => {
      qc.setQueryData(STATUS_KEY, status)
      qc.invalidateQueries({ queryKey: STATUS_KEY })
    },
  })
}

/**
 * Calibration is calculated on demand (not auto-run). Returns a mutation so the
 * "Calculate" button drives it with the chosen target percentage.
 */
export function useCalculateCalibration() {
  return useMutation({
    mutationFn: (targetPct: number) => api.getPreviewMachineCalibration(targetPct),
  })
}
