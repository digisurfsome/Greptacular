/**
 * PipelinePanel — the five Preview Machine stages in run order, each with a Run
 * button. Stages 2-5 take a CSV input picked from a dropdown (populated by
 * GET /files). Stage 5 also chooses how to build (offline test vs copy cache).
 *
 * A live status pill + log viewer poll GET /status every 2s while running
 * (handled by the status hook). A Stop button terminates the running stage.
 */

import { Loader2, Play, Square } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  usePreviewMachineStatus,
  usePreviewMachineFiles,
  useRunPreviewMachineStage,
  useStopPreviewMachine,
} from '@/hooks/usePreviewMachine'
import type { PreviewMachineStage } from '@/lib/types'
import { CopywriterControls, type CopywriterSettings } from './CopywriterControls'
import { useEffect, useRef, useState } from 'react'

/** Default CSV used by the audit / copy / build stages when present. */
const DEFAULT_AUDIT_CSV = 'site_audit.csv'

interface StageDef {
  num: number
  stage: PreviewMachineStage
  title: string
  /** Plain-language explanation for the owner. */
  blurb: string
  /** Whether this stage needs a CSV input picked from the dropdown. */
  needsCsv: boolean
}

const STAGES: StageDef[] = [
  { num: 1, stage: 'biz_pull', title: 'Pull businesses', blurb: 'Find businesses to target.', needsCsv: false },
  { num: 2, stage: 'gsa_filter', title: 'GSA filter', blurb: 'Keep only the good-fit ones.', needsCsv: true },
  { num: 3, stage: 'site_age', title: 'Audit sites', blurb: 'Check their current websites.', needsCsv: true },
  { num: 4, stage: 'copywriter', title: 'Write copy', blurb: 'Generate ad copy for each.', needsCsv: true },
  { num: 5, stage: 'sitegen', title: 'Build sites', blurb: 'Build preview websites.', needsCsv: true },
]

interface PipelinePanelProps {
  copywriter: CopywriterSettings
  onCopywriterChange: (next: CopywriterSettings) => void
}

export function PipelinePanel({ copywriter, onCopywriterChange }: PipelinePanelProps) {
  const { data: status } = usePreviewMachineStatus()
  const { data: files } = usePreviewMachineFiles()
  const runStage = useRunPreviewMachineStage()
  const stopStage = useStopPreviewMachine()

  const running = status?.running ?? false

  // Per-stage selected CSV. Stages 4/5 default to site_audit.csv when it exists.
  const [csvByStage, setCsvByStage] = useState<Record<string, string>>({})
  // Stage 5 build mode: 'copy' (from copy cache) is the default; 'offline' is a free test.
  const [sitegenMode, setSitegenMode] = useState<'copy' | 'offline'>('copy')

  // Once files load, seed defaults for stages that prefer site_audit.csv.
  useEffect(() => {
    if (!files || files.length === 0) return
    const names = files.map((f) => f.name)
    setCsvByStage((prev) => {
      const next = { ...prev }
      for (const s of STAGES) {
        if (!s.needsCsv || next[s.stage]) continue
        const prefersAudit = s.stage === 'copywriter' || s.stage === 'sitegen'
        if (prefersAudit && names.includes(DEFAULT_AUDIT_CSV)) {
          next[s.stage] = DEFAULT_AUDIT_CSV
        } else {
          next[s.stage] = names[0]
        }
      }
      return next
    })
  }, [files])

  // Auto-scroll the log to the newest line.
  const logRef = useRef<HTMLPreElement>(null)
  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight
  }, [status?.log])

  /** Assemble the validated argv for a stage from current UI state. */
  function buildArgs(stage: PreviewMachineStage): string[] {
    const csv = csvByStage[stage]
    if (stage === 'biz_pull') return []
    if (stage === 'gsa_filter' || stage === 'site_age') return csv ? [csv] : []
    if (stage === 'copywriter') {
      const args: string[] = csv ? [csv] : []
      args.push('--model', copywriter.model)
      args.push('--batch-size', String(copywriter.batchSize))
      if (copywriter.perHour > 0) args.push('--per-hour', String(copywriter.perHour))
      if (copywriter.autoRetry) args.push('--auto-retry', String(copywriter.autoRetryMinutes))
      return args
    }
    if (stage === 'sitegen') {
      const args: string[] = csv ? [csv] : []
      if (sitegenMode === 'offline') args.push('--offline')
      else args.push('--copydir', 'copy')
      return args
    }
    return []
  }

  function handleRun(stage: PreviewMachineStage) {
    runStage.mutate({ stage, args: buildArgs(stage) })
  }

  const activeStage = status?.stage
  const exitCode = status?.exit_code

  return (
    <div className="space-y-6">
      {/* Status bar */}
      <div className="flex items-center gap-3">
        <StatusPill running={running} stage={activeStage ?? null} exitCode={exitCode ?? null} />
        {running && (
          <Button
            variant="destructive"
            size="sm"
            onClick={() => stopStage.mutate()}
            disabled={stopStage.isPending}
          >
            <Square className="w-4 h-4" />
            Stop
          </Button>
        )}
        {runStage.isError && (
          <span className="text-sm text-destructive">{(runStage.error as Error).message}</span>
        )}
      </div>

      {/* Stage cards */}
      <div className="space-y-3">
        {STAGES.map((s) => {
          const isActive = running && activeStage === s.stage
          return (
            <div key={s.stage} className="bg-card rounded-lg border border-border p-4 shadow-sm">
              <div className="flex items-start gap-4">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted text-sm font-bold text-foreground">
                  {s.num}
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <h4 className="text-base font-medium text-foreground">{s.title}</h4>
                      <p className="text-xs text-muted-foreground">{s.blurb}</p>
                    </div>
                    <Button
                      size="sm"
                      onClick={() => handleRun(s.stage)}
                      disabled={running || runStage.isPending}
                    >
                      {isActive ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Play className="w-4 h-4" />
                      )}
                      Run
                    </Button>
                  </div>

                  {/* CSV picker for stages 2-5 */}
                  {s.needsCsv && (
                    <div className="mt-3">
                      <label className="text-xs font-medium text-foreground" htmlFor={`csv-${s.stage}`}>
                        Input CSV
                      </label>
                      <select
                        id={`csv-${s.stage}`}
                        className="block mt-1 w-full max-w-md px-3 py-1.5 text-sm bg-background border border-border rounded-lg outline-none focus:ring-2 focus:ring-primary"
                        value={csvByStage[s.stage] ?? ''}
                        disabled={running}
                        onChange={(e) =>
                          setCsvByStage((prev) => ({ ...prev, [s.stage]: e.target.value }))
                        }
                      >
                        {(!files || files.length === 0) && <option value="">No CSV files found</option>}
                        {files?.map((f) => (
                          <option key={f.name} value={f.name}>
                            {f.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}

                  {/* Stage 5 build mode */}
                  {s.stage === 'sitegen' && (
                    <fieldset className="mt-3" disabled={running}>
                      <legend className="text-xs font-medium text-foreground mb-1">Build mode</legend>
                      <div className="flex flex-col gap-1.5">
                        <label className="flex items-center gap-2 text-sm text-foreground">
                          <input
                            type="radio"
                            name="sitegen-mode"
                            checked={sitegenMode === 'copy'}
                            onChange={() => setSitegenMode('copy')}
                          />
                          From copy cache (real ad copy)
                        </label>
                        <label className="flex items-center gap-2 text-sm text-foreground">
                          <input
                            type="radio"
                            name="sitegen-mode"
                            checked={sitegenMode === 'offline'}
                            onChange={() => setSitegenMode('offline')}
                          />
                          Offline (free test)
                        </label>
                      </div>
                    </fieldset>
                  )}

                  {/* Stage 4 copywriter settings */}
                  {s.stage === 'copywriter' && (
                    <div className="mt-3">
                      <CopywriterControls
                        value={copywriter}
                        onChange={onCopywriterChange}
                        disabled={running}
                      />
                    </div>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Live log viewer */}
      <div>
        <h4 className="text-sm font-semibold text-foreground mb-2">Live log</h4>
        <pre
          ref={logRef}
          className="h-64 overflow-auto rounded-lg border border-border bg-muted/40 p-3 text-xs font-mono text-foreground whitespace-pre-wrap"
        >
          {status?.log && status.log.length > 0
            ? status.log.join('\n')
            : 'No output yet. Run a stage to see live output here.'}
        </pre>
      </div>
    </div>
  )
}

function StatusPill({
  running,
  stage,
  exitCode,
}: {
  running: boolean
  stage: PreviewMachineStage | null
  exitCode: number | null
}) {
  let text: string
  let cls: string
  if (running) {
    text = `Running: ${stage ?? ''}`
    cls = 'bg-[--color-neo-progress] text-foreground'
  } else if (exitCode === 0) {
    text = 'Done'
    cls = 'bg-[--color-neo-done] text-foreground'
  } else if (exitCode != null) {
    text = `Stopped (code ${exitCode})`
    cls = 'bg-destructive text-destructive-foreground'
  } else {
    text = 'Idle'
    cls = 'bg-muted text-muted-foreground'
  }
  return (
    <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-medium ${cls}`}>
      {text}
    </span>
  )
}
