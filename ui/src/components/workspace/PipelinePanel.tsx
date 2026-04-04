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
  MessageSquare,
  FolderOpen,
  Save,
  Copy,
  Trash2,
  SkipForward,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { PipelineSkillSlot } from './PipelineSkillSlot'
import { PipelineOutputViewer } from './PipelineOutputViewer'
import type { PipelineStatusResponse, PipelineStageStatus, PipelineProject } from '@/lib/api'
import {
  startPipeline,
  stopPipeline,
  forceAdvancePipeline,
  getPipelineStatus,
  exportPipelineOutputs,
  listPipelineProjects,
  createPipelineProject,
  updatePipelineProject,
  deletePipelineProject,
  clonePipelineProject,
  loadPipelineFolder,
} from '@/lib/api'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface PipelinePanelProps {
  workingDirectory: string | null
  onWorkingDirectoryChange?: (path: string | null) => void
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
        <pre className="mt-2 p-2 bg-muted/50 rounded text-[11px] max-h-[600px] overflow-y-auto whitespace-pre-wrap">
          {stage.output}
        </pre>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// PipelinePanel (main export)
// ---------------------------------------------------------------------------

export function PipelinePanel({
  workingDirectory,
  onWorkingDirectoryChange,
  onClose,
}: PipelinePanelProps): React.JSX.Element {
  // ---- State ----
  const [pipelineId, setPipelineId] = useState<string | null>(null)
  const [status, setStatus] = useState<PipelineStatusResponse | null>(null)
  const [kickoffMessage, setKickoffMessage] = useState('')
  const [tokenBudget, setTokenBudget] = useState(400_000)
  const [model, setModel] = useState('opus')
  const [outputMode, setOutputMode] = useState<'json' | 'text'>('json')
  const [skills, setSkills] = useState<SkillSlot[]>([{ label: 'Skill 1', text: '' }])
  const [starting, setStarting] = useState(false)
  const [expandedOutput, setExpandedOutput] = useState<number | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // ---- Project state ----
  const [projects, setProjects] = useState<PipelineProject[]>([])
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null)
  const [projectName, setProjectName] = useState('New Pipeline')
  const [showFolderInput, setShowFolderInput] = useState(false)
  const [folderPath, setFolderPath] = useState('')

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

  // ---- Load projects on mount ----
  useEffect(() => {
    listPipelineProjects().then(setProjects).catch(() => {})
  }, [])

  /** Refresh the project list from the server. */
  const refreshProjects = useCallback(async () => {
    try {
      const list = await listPipelineProjects()
      setProjects(list)
    } catch { /* ignore */ }
  }, [])

  /** Load a project's config into the panel state. */
  const loadProject = useCallback((project: PipelineProject) => {
    setSelectedProjectId(project.id)
    setProjectName(project.name)
    setModel(project.default_model)
    setTokenBudget(project.default_token_budget)
    setOutputMode(project.output_mode)
    try {
      const stages = JSON.parse(project.stages_json) as { label: string; skill_text: string }[]
      setSkills(stages.map((s) => ({ label: s.label, text: s.skill_text })))
    } catch {
      setSkills([{ label: 'Skill 1', text: '' }])
    }
  }, [])

  /** Handle project dropdown change. */
  const handleProjectSelect = useCallback((value: string) => {
    if (value === 'new') {
      setSelectedProjectId(null)
      setProjectName('New Pipeline')
      setSkills([{ label: 'Skill 1', text: '' }])
      setOutputMode('json')
      setModel('opus')
      setTokenBudget(400_000)
      setKickoffMessage('')
      return
    }
    const id = Number(value)
    const proj = projects.find((p) => p.id === id)
    if (proj) loadProject(proj)
  }, [projects, loadProject])

  /** Save current config to existing project or create new one. */
  const handleSave = useCallback(async () => {
    const stages = skills.filter((s) => s.text.trim()).map((s) => ({
      label: s.label,
      skill_text: s.text,
    }))
    try {
      if (selectedProjectId) {
        const updated = await updatePipelineProject(selectedProjectId, {
          name: projectName,
          output_mode: outputMode,
          default_model: model,
          default_token_budget: tokenBudget,
          stages,
        })
        setSelectedProjectId(updated.id)
      } else {
        const created = await createPipelineProject({
          name: projectName,
          output_mode: outputMode,
          default_model: model,
          default_token_budget: tokenBudget,
          stages,
        })
        setSelectedProjectId(created.id)
      }
      await refreshProjects()
    } catch (e) {
      console.error('Failed to save project:', e)
    }
  }, [selectedProjectId, projectName, outputMode, model, tokenBudget, skills, refreshProjects])

  /** Save As — prompt for a new name, then create. */
  const handleSaveAs = useCallback(async () => {
    const newName = window.prompt('Save pipeline as:', `${projectName} (copy)`)
    if (!newName?.trim()) return
    const stages = skills.filter((s) => s.text.trim()).map((s) => ({
      label: s.label,
      skill_text: s.text,
    }))
    try {
      const created = await createPipelineProject({
        name: newName.trim(),
        output_mode: outputMode,
        default_model: model,
        default_token_budget: tokenBudget,
        stages,
      })
      setSelectedProjectId(created.id)
      setProjectName(created.name)
      await refreshProjects()
    } catch (e) {
      console.error('Failed to save-as project:', e)
    }
  }, [projectName, outputMode, model, tokenBudget, skills, refreshProjects])

  /** Delete the currently selected project. */
  const handleDeleteProject = useCallback(async () => {
    if (!selectedProjectId) return
    if (!window.confirm(`Delete "${projectName}"?`)) return
    try {
      await deletePipelineProject(selectedProjectId)
      setSelectedProjectId(null)
      setProjectName('New Pipeline')
      await refreshProjects()
    } catch (e) {
      console.error('Failed to delete project:', e)
    }
  }, [selectedProjectId, projectName, refreshProjects])

  /** Clone the currently selected project. */
  const handleCloneProject = useCallback(async () => {
    if (!selectedProjectId) return
    const newName = window.prompt('Clone name:', `${projectName} (clone)`)
    if (!newName?.trim()) return
    try {
      const cloned = await clonePipelineProject(selectedProjectId, newName.trim())
      setSelectedProjectId(cloned.id)
      setProjectName(cloned.name)
      await refreshProjects()
    } catch (e) {
      console.error('Failed to clone project:', e)
    }
  }, [selectedProjectId, projectName, refreshProjects])

  /** Load stages from a folder on disk. */
  const handleLoadFolder = useCallback(async () => {
    if (!folderPath.trim()) return
    try {
      const stages = await loadPipelineFolder(folderPath.trim())
      setSkills(stages.map((s) => ({ label: s.label, text: s.skill_text })))
      setShowFolderInput(false)
      setFolderPath('')
    } catch (e) {
      console.error('Failed to load folder:', e)
    }
  }, [folderPath])

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
        output_mode: outputMode,
        stages: filledSkills.map((s) => ({ label: s.label, skill_text: s.text })),
      })
      setPipelineId(result.pipeline_id)
    } catch (e) {
      console.error('Failed to start pipeline:', e)
    } finally {
      setStarting(false)
    }
  }, [workingDirectory, kickoffMessage, tokenBudget, model, outputMode, skills])

  const handleStop = useCallback(async () => {
    if (!pipelineId) return
    try {
      await stopPipeline(pipelineId)
    } catch (e) {
      console.error('Failed to stop pipeline:', e)
    }
  }, [pipelineId])

  const handleForceAdvance = useCallback(async () => {
    if (!pipelineId) return
    try {
      const result = await forceAdvancePipeline(pipelineId)
      if (result.success) {
        // Refresh status immediately
        const s = await getPipelineStatus(pipelineId)
        setStatus(s)
      }
    } catch (e) {
      console.error('Failed to force advance:', e)
    }
  }, [pipelineId])

  const handleExport = useCallback(async () => {
    if (!pipelineId) return
    try {
      const blob = await exportPipelineOutputs(pipelineId)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `pipeline-${pipelineId}-output.md`
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
          {projectName && projectName !== 'New Pipeline' && (
            <span className="text-[10px] text-muted-foreground">— {projectName}</span>
          )}
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

      {/* Two-column body: pipeline controls (left) + workspace chat (right) */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left column: Pipeline controls — scrolls independently */}
        <div className="w-[350px] shrink-0 border-r border-border overflow-y-auto px-3 py-3 space-y-3">
          {!pipelineId ? (
            /* ============================================================
             * CONFIGURE MODE — set up the pipeline before launching
             * ============================================================ */
            <>
              {/* ── Project selector ── */}
              <div className="space-y-1.5">
                <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                  Project
                </label>
                <select
                  value={selectedProjectId ?? 'new'}
                  onChange={(e) => handleProjectSelect(e.target.value)}
                  className="w-full h-7 rounded-md border border-border bg-input px-2 text-xs text-foreground outline-none ring-ring focus:ring-1"
                >
                  <option value="new">New Pipeline</option>
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
                <input
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  placeholder="Pipeline name"
                  className="w-full h-7 rounded-md border border-border bg-input px-2 text-xs text-foreground placeholder:text-muted-foreground/60 outline-none ring-ring focus:ring-1"
                />
                <div className="flex gap-1">
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-6 px-2 text-[10px] gap-1"
                    onClick={handleSave}
                  >
                    <Save size={10} /> Save
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-6 px-2 text-[10px] gap-1"
                    onClick={handleSaveAs}
                  >
                    <Copy size={10} /> Save As
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-6 px-2 text-[10px] gap-1"
                    onClick={handleCloneProject}
                    disabled={!selectedProjectId}
                  >
                    <Copy size={10} /> Clone
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-6 px-2 text-[10px] gap-1 text-red-600 hover:text-red-700"
                    onClick={handleDeleteProject}
                    disabled={!selectedProjectId}
                  >
                    <Trash2 size={10} /> Delete
                  </Button>
                </div>
              </div>

              {/* Working directory */}
              <div className="space-y-1">
                <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                  Working Directory
                </label>
                <div className="flex gap-1">
                  <input
                    type="text"
                    value={workingDirectory ?? ''}
                    onChange={(e) => onWorkingDirectoryChange?.(e.target.value || null)}
                    placeholder="C:\Users\...\your-project"
                    className="flex-1 h-7 rounded-md border border-border bg-input px-2 text-xs text-foreground placeholder:text-muted-foreground/60 outline-none ring-ring focus:ring-1"
                  />
                </div>
              </div>

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

              {/* Settings row: Token Budget + Model */}
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

              {/* Output mode */}
              <div className="space-y-1">
                <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                  Output Mode
                </label>
                <select
                  value={outputMode}
                  onChange={(e) => setOutputMode(e.target.value as 'json' | 'text')}
                  className="w-full h-7 rounded-md border border-border bg-input px-2 text-xs text-foreground outline-none ring-ring focus:ring-1"
                >
                  <option value="json">JSON Extract</option>
                  <option value="text">Full Text</option>
                </select>
              </div>

              {/* Skills list */}
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                    Skills ({skills.length})
                  </label>
                  <button
                    onClick={() => setShowFolderInput((v) => !v)}
                    className="text-[10px] text-emerald-600 hover:text-emerald-700 font-medium flex items-center gap-1"
                  >
                    <FolderOpen size={10} /> Load from folder
                  </button>
                </div>

                {/* Folder loader */}
                {showFolderInput && (
                  <div className="flex gap-1">
                    <input
                      type="text"
                      value={folderPath}
                      onChange={(e) => setFolderPath(e.target.value)}
                      onKeyDown={(e) => { if (e.key === 'Enter') handleLoadFolder() }}
                      placeholder="/path/to/skills/folder"
                      className="flex-1 h-7 rounded-md border border-border bg-input px-2 text-xs text-foreground placeholder:text-muted-foreground/60 outline-none ring-ring focus:ring-1"
                    />
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-7 px-2 text-[10px]"
                      onClick={handleLoadFolder}
                      disabled={!folderPath.trim()}
                    >
                      Load
                    </Button>
                  </div>
                )}

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
              {/* Stop + Force Next buttons */}
              {isRunning && (
                <div className="flex gap-2">
                  <Button
                    onClick={handleStop}
                    variant="outline"
                    className="flex-1 text-xs gap-2"
                  >
                    <Square size={14} /> Stop
                  </Button>
                  <Button
                    onClick={handleForceAdvance}
                    variant="outline"
                    className="flex-1 text-xs gap-2 border-emerald-500/50 text-emerald-600 hover:bg-emerald-500/10"
                  >
                    <SkipForward size={14} /> Force Next
                  </Button>
                </div>
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

              {/* Agent waiting indicator (answers go through the output viewer on the right) */}
              {isRunning && status?.waiting_for_answer && (
                <div className="flex items-center gap-2 p-2 bg-amber-500/10 rounded border border-amber-500/20 text-xs text-amber-600">
                  <MessageSquare size={12} />
                  Agent is waiting — answer in the panel on the right
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

              {/* Endpoint placeholder — future next-action routing */}
              {isDone && (
                <div className="border border-dashed border-border rounded-lg p-3 text-center">
                  <p className="text-[10px] text-muted-foreground">
                    Next Action (coming soon)
                  </p>
                  <select
                    disabled
                    className="mt-1 h-7 w-full rounded-md border border-border bg-muted/50 text-xs text-muted-foreground"
                  >
                    <option>Done — no further action</option>
                    <option>Send to Swarm Builder</option>
                    <option>Send to Coder Agent</option>
                  </select>
                </div>
              )}
            </>
          )}
        </div>

        {/* Right column: Pipeline output viewer — no WorkspaceChat, no hanging */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <PipelineOutputViewer
            pipelineId={pipelineId}
            status={status}
          />
        </div>
      </div>
    </div>
  )
}
