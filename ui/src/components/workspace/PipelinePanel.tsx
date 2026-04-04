/**
 * PipelinePanel
 *
 * Controls and status display for the Skill Pipeline — sequential prompt
 * chains that pass output from one skill stage to the next.
 *
 * Two modes:
 * - Configure: set kickoff message, token budget, model, and skill slots
 * - Running: monitor stage progress, token usage, and view/export outputs
 *
 * Follows the same panel pattern as SwarmPanel (slides in from the right).
 */

import { useState, useRef, useEffect, useCallback } from 'react'
import {
  X,
  Zap,
  Square,
  Loader2,
  CheckCircle2,
  XCircle,
  Clock,
  ChevronDown,
  ChevronRight,
  Download,
  Workflow,
  Send,
  MessageSquare,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { PipelineSkillSlot } from './PipelineSkillSlot'
import type { PipelineStatusResponse, PipelineStageStatus } from '@/lib/api'
import {
  startPipeline,
  stopPipeline,
  getPipelineStatus,
  exportPipelineOutputs,
  sendPipelineAnswer,
} from '@/lib/api'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface PipelinePanelProps {
  workingDirectory: string | null
  onClose: () => void
}

interface SkillSlot {
  label: string
  text: string
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Format a token count into a compact human-readable string. */
function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`
  return String(n)
}

// ---------------------------------------------------------------------------
// PipelineStageCard (inline component)
// ---------------------------------------------------------------------------

/** Status badge colors and icons for each stage status. */
const STATUS_CONFIG: Record<string, { color: string; icon: typeof Clock; label: string }> = {
  pending:   { color: 'text-muted-foreground bg-muted/50', icon: Clock, label: 'Pending' },
  running:   { color: 'text-cyan-600 bg-cyan-500/10', icon: Loader2, label: 'Running' },
  completed: { color: 'text-green-600 bg-green-500/10', icon: CheckCircle2, label: 'Done' },
  failed:    { color: 'text-red-600 bg-red-500/10', icon: XCircle, label: 'Failed' },
}

function PipelineStageCard({
  stage,
  expanded,
  onToggleOutput,
}: {
  stage: PipelineStageStatus
  expanded: boolean
  onToggleOutput: () => void
}): React.JSX.Element {
  const config = STATUS_CONFIG[stage.status] || STATUS_CONFIG.pending
  const Icon = config.icon

  return (
    <div className={`border border-border rounded-lg p-3 ${stage.status === 'running' ? 'ring-2 ring-cyan-400/30' : ''}`}>
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono text-muted-foreground">{stage.stage_index + 1}.</span>
          <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold ${config.color}`}>
            <Icon size={10} className={stage.status === 'running' ? 'animate-spin' : ''} />
            {config.label}
          </span>
          <span className="text-xs font-bold text-foreground">{stage.label}</span>
        </div>
      </div>

      {/* Stats for completed stages */}
      {stage.status === 'completed' && (
        <div className="flex items-center gap-3 text-[10px] text-muted-foreground mt-1">
          <span>{stage.tokens_used.toLocaleString()} tokens</span>
          <span>{stage.duration_seconds.toFixed(0)}s</span>
          <button
            onClick={onToggleOutput}
            className="text-emerald-600 hover:text-emerald-700 flex items-center gap-1"
          >
            {expanded ? <ChevronDown size={10} /> : <ChevronRight size={10} />} View Output
          </button>
        </div>
      )}

      {/* Running indicator */}
      {stage.status === 'running' && (
        <div className="text-[10px] text-cyan-600 mt-1 flex items-center gap-1">
          <Loader2 size={10} className="animate-spin" /> Processing...
          {stage.tokens_used > 0 && <span>{stage.tokens_used.toLocaleString()} tokens</span>}
        </div>
      )}

      {/* Error message */}
      {stage.error && (
        <p className="text-[10px] text-red-500 mt-1 truncate">{stage.error}</p>
      )}

      {/* Expanded output */}
      {expanded && stage.output && (
        <pre className="mt-2 p-2 bg-muted/50 rounded text-[10px] max-h-60 overflow-y-auto whitespace-pre-wrap">
          {stage.output}
        </pre>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// PipelinePanel (main export)
// ---------------------------------------------------------------------------

export function PipelinePanel({ workingDirectory, onClose }: PipelinePanelProps): React.JSX.Element {
  // ---- State ----
  const [pipelineId, setPipelineId] = useState<string | null>(null)
  const [status, setStatus] = useState<PipelineStatusResponse | null>(null)
  const [kickoffMessage, setKickoffMessage] = useState('')
  const [tokenBudget, setTokenBudget] = useState(400_000)
  const [model, setModel] = useState('opus')
  const [skills, setSkills] = useState<SkillSlot[]>([{ label: 'Skill 1', text: '' }])
  const [starting, setStarting] = useState(false)
  const [expandedOutput, setExpandedOutput] = useState<number | null>(null)
  const [chatInput, setChatInput] = useState('')
  const [sendingAnswer, setSendingAnswer] = useState(false)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // ---- Poll for status when a pipeline is running (same pattern as SwarmPanel) ----
  useEffect(() => {
    if (!pipelineId) return

    const poll = async () => {
      try {
        const s = await getPipelineStatus(pipelineId)
        setStatus(s)

        // Stop polling when the pipeline is no longer active
        if (s.status === 'completed' || s.status === 'failed' || s.status === 'stopped') {
          if (pollRef.current) {
            clearInterval(pollRef.current)
            pollRef.current = null
          }
        }
      } catch {
        // Pipeline may have been cleaned up
      }
    }

    poll()
    pollRef.current = setInterval(poll, 3_000)
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [pipelineId])

  // ---- Handlers ----

  const handleStart = useCallback(async () => {
    if (!workingDirectory) return

    // At least one skill must have content
    const filledSkills = skills.filter((s) => s.text.trim())
    if (filledSkills.length === 0) return

    setStarting(true)
    try {
      const result = await startPipeline({
        working_directory: workingDirectory,
        kickoff_message: kickoffMessage.trim(),
        token_budget: tokenBudget,
        model,
        stages: filledSkills.map((s) => ({ label: s.label, skill_text: s.text })),
      })
      setPipelineId(result.pipeline_id)
    } catch (e) {
      console.error('Failed to start pipeline:', e)
    } finally {
      setStarting(false)
    }
  }, [workingDirectory, kickoffMessage, tokenBudget, model, skills])

  const handleStop = useCallback(async () => {
    if (!pipelineId) return
    try {
      await stopPipeline(pipelineId)
    } catch (e) {
      console.error('Failed to stop pipeline:', e)
    }
  }, [pipelineId])

  const handleSendAnswer = useCallback(async () => {
    if (!pipelineId || !chatInput.trim()) return
    setSendingAnswer(true)
    try {
      await sendPipelineAnswer(pipelineId, chatInput.trim())
      setChatInput('')
    } catch (e) {
      console.error('Failed to send answer:', e)
    } finally {
      setSendingAnswer(false)
    }
  }, [pipelineId, chatInput])

  const handleExport = useCallback(async () => {
    if (!pipelineId) return
    try {
      const blob = await exportPipelineOutputs(pipelineId)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `pipeline-${pipelineId}.zip`
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      console.error('Failed to export pipeline outputs:', e)
    }
  }, [pipelineId])

  const handleAddSkill = useCallback(() => {
    setSkills((prev) => [...prev, { label: `Skill ${prev.length + 1}`, text: '' }])
  }, [])

  const handleRemoveSkill = useCallback((index: number) => {
    setSkills((prev) => prev.filter((_, i) => i !== index))
  }, [])

  const handleUpdateSkill = useCallback((index: number, field: 'label' | 'text', value: string) => {
    setSkills((prev) => prev.map((s, i) => (i === index ? { ...s, [field]: value } : s)))
  }, [])

  const handleFileUpload = useCallback((_index: number, _file: File) => {
    // File reading is handled inside PipelineSkillSlot; this callback exists
    // so the parent can hook into the upload event if needed in the future.
  }, [])

  // ---- Derived state ----
  const isRunning = status?.status === 'running'
  const isDone = status?.status === 'completed' || status?.status === 'failed' || status?.status === 'stopped'

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header — emerald gradient */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-border bg-gradient-to-r from-emerald-500/10 to-cyan-500/10">
        <div className="flex items-center gap-2">
          <Workflow size={14} className="text-emerald-500" />
          <span className="text-xs font-bold tracking-wide text-foreground">SKILL PIPELINE</span>
          {status && (
            <span
              className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${
                isRunning
                  ? 'bg-cyan-500/20 text-cyan-600'
                  : status.status === 'completed'
                    ? 'bg-green-500/20 text-green-600'
                    : status.status === 'failed'
                      ? 'bg-red-500/20 text-red-600'
                      : 'bg-muted text-muted-foreground'
              }`}
            >
              {status.status.toUpperCase()}
            </span>
          )}
        </div>
        <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
          <X size={14} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3">
        {!pipelineId ? (
          /* ============================================================
           * CONFIGURE MODE — set up the pipeline before launching
           * ============================================================ */
          <>
            {/* Kickoff message */}
            <div className="space-y-1">
              <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                Kickoff Message
              </label>
              <textarea
                value={kickoffMessage}
                onChange={(e) => setKickoffMessage(e.target.value)}
                placeholder="Optional context or instructions to prepend to every stage..."
                className="w-full resize-none min-h-[60px] rounded-md border border-border bg-input px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground/60 outline-none ring-ring focus:ring-1"
                rows={3}
              />
            </div>

            {/* Settings row */}
            <div className="flex gap-2">
              <div className="flex-1 space-y-1">
                <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                  Token Budget
                </label>
                <select
                  value={tokenBudget}
                  onChange={(e) => setTokenBudget(Number(e.target.value))}
                  className="w-full h-7 rounded-md border border-border bg-input px-2 text-xs text-foreground outline-none ring-ring focus:ring-1"
                >
                  <option value={200_000}>200K</option>
                  <option value={400_000}>400K</option>
                  <option value={450_000}>450K</option>
                </select>
              </div>
              <div className="flex-1 space-y-1">
                <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                  Model
                </label>
                <select
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="w-full h-7 rounded-md border border-border bg-input px-2 text-xs text-foreground outline-none ring-ring focus:ring-1"
                >
                  <option value="opus">Opus</option>
                  <option value="sonnet">Sonnet</option>
                </select>
              </div>
            </div>

            {/* Skills list */}
            <div className="space-y-1">
              <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                Skills ({skills.length})
              </label>
              <div className="space-y-2">
                {skills.map((skill, i) => (
                  <PipelineSkillSlot
                    key={i}
                    index={i}
                    label={skill.label}
                    text={skill.text}
                    onUpdate={(field, val) => handleUpdateSkill(i, field, val)}
                    onRemove={() => handleRemoveSkill(i)}
                    onFileUpload={(file) => handleFileUpload(i, file)}
                  />
                ))}
              </div>
              <button
                onClick={handleAddSkill}
                className="mt-1 text-xs text-emerald-600 hover:text-emerald-700 font-medium"
              >
                + Add Skill
              </button>
            </div>

            {/* Warning if no working directory */}
            {!workingDirectory && (
              <p className="text-[10px] text-amber-600">
                Select a working directory first (use the repo selector in the breadcrumb bar).
              </p>
            )}

            {/* Launch button */}
            <Button
              onClick={handleStart}
              disabled={!workingDirectory || skills.every((s) => !s.text.trim()) || starting}
              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white text-xs gap-2"
            >
              {starting ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <Zap size={14} />
              )}
              Launch Pipeline
            </Button>
          </>
        ) : (
          /* ============================================================
           * RUNNING MODE — monitor progress and view results
           * ============================================================ */
          <>
            {/* Stop button */}
            {isRunning && (
              <Button
                onClick={handleStop}
                variant="outline"
                className="w-full text-xs gap-2"
              >
                <Square size={14} /> Stop Pipeline
              </Button>
            )}

            {/* New pipeline button when done */}
            {isDone && (
              <Button
                variant="ghost"
                size="sm"
                className="w-full h-6 text-[10px]"
                onClick={() => {
                  setPipelineId(null)
                  setStatus(null)
                }}
              >
                New Pipeline
              </Button>
            )}

            {/* Token budget progress bar */}
            <div className="space-y-1">
              <div className="flex justify-between text-[10px] text-muted-foreground">
                <span>Token Budget: {formatTokens(tokenBudget)}</span>
                <span>Used: {formatTokens(status?.total_tokens || 0)}</span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-emerald-500 rounded-full transition-all"
                  style={{
                    width: `${Math.min(100, ((status?.total_tokens || 0) / tokenBudget) * 100)}%`,
                  }}
                />
              </div>
              <div className="text-right text-[10px] text-muted-foreground">
                {Math.round(((status?.total_tokens || 0) / tokenBudget) * 100)}%
              </div>
            </div>

            {/* Stage progress cards */}
            <div className="space-y-2">
              {status?.stages.map((stage, i) => (
                <PipelineStageCard
                  key={i}
                  stage={stage}
                  expanded={expandedOutput === i}
                  onToggleOutput={() => setExpandedOutput(expandedOutput === i ? null : i)}
                />
              ))}
            </div>

            {/* Agent question / chat input */}
            {isRunning && (
              <div className="space-y-2 border border-border rounded-lg p-2 bg-muted/20">
                {status?.waiting_for_answer && status?.waiting_question && (
                  <div className="flex items-start gap-2 p-2 bg-amber-500/10 rounded border border-amber-500/20">
                    <MessageSquare size={14} className="text-amber-600 mt-0.5 flex-shrink-0" />
                    <div className="text-xs text-amber-800 dark:text-amber-200">
                      <p className="font-semibold text-[10px] uppercase tracking-wider mb-1">Agent Question:</p>
                      <p>{status.waiting_question}</p>
                    </div>
                  </div>
                )}
                <div className="flex gap-1.5">
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendAnswer() } }}
                    placeholder={status?.waiting_for_answer ? 'Type your answer...' : 'Send message to agent...'}
                    className="flex-1 h-7 rounded-md border border-border bg-input px-2 text-xs text-foreground placeholder:text-muted-foreground/60 outline-none ring-ring focus:ring-1"
                    disabled={sendingAnswer}
                  />
                  <Button
                    size="sm"
                    className="h-7 px-2 bg-emerald-600 hover:bg-emerald-700 text-white"
                    onClick={handleSendAnswer}
                    disabled={!chatInput.trim() || sendingAnswer}
                  >
                    {sendingAnswer ? <Loader2 size={12} className="animate-spin" /> : <Send size={12} />}
                  </Button>
                </div>
              </div>
            )}

            {/* Download button when pipeline is finished */}
            {isDone && (
              <Button
                onClick={handleExport}
                className="w-full bg-emerald-600 hover:bg-emerald-700 text-white text-xs gap-2"
              >
                <Download size={14} /> Download All Outputs
              </Button>
            )}
          </>
        )}
      </div>
    </div>
  )
}
