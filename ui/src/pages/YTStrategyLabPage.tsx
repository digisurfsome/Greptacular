/**
 * YTStrategyLabPage - YouTube Strategy Lab for extracting, organizing,
 * and operationalizing strategies from YouTube videos.
 *
 * Three views:
 *   1. Project List (default) - Grid of strategy project cards
 *   2. Project Detail / Strategy Builder - Step editor with collapsible sidebar
 *   3. Create New Project - Simple form for new projects
 *
 * All data is persisted in localStorage. No backend API calls.
 */

import { useState, useMemo, useCallback, useEffect } from 'react'
import {
  AlertCircle,
  ArrowLeft,
  ChevronRight,
  Plus,
  Search,
  FlaskConical,
  CirclePlay,
  Pencil,
  Trash2,
  ChevronDown,
  ChevronUp,
  GripVertical,
  X,
  ClipboardCopy,
  ExternalLink,
  Hash,
  FileText,
  ListOrdered,
  CircleCheck,
  FolderOpen,
  Sparkles,
  PanelLeftClose,
  PanelLeftOpen,
  Loader2,
  Wand2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import type {
  YTStrategyProject,
  YTStrategyStep,
  YTStrategySubStep,
  YTIngestResponse,
  YTProjectStatus,
  YTStrategyStepStatus,
} from '@/lib/types'
import { VideoIngestPanel } from '@/components/yt-lab/VideoIngestPanel'
import { processYouTubeVideo } from '@/lib/api'

// ============================================================================
// Constants
// ============================================================================

const STORAGE_KEY_PROJECTS = 'yt-lab-projects'

/** Prefix for per-project step storage keys. */
function stepsStorageKey(projectId: string): string {
  return `yt-lab-steps-${projectId}`
}

/** AI model options displayed in the step editor dropdown. */
const MODEL_OPTIONS = [
  { value: 'claude-opus-4-6', label: 'Claude Opus 4.6' },
  { value: 'claude-sonnet-4-6', label: 'Claude Sonnet 4.6' },
  { value: 'codex', label: 'Codex' },
  { value: 'gemini', label: 'Gemini' },
  { value: 'custom', label: 'Custom' },
] as const

/** Sort options for the project list. */
const SORT_OPTIONS = [
  { value: 'date-desc', label: 'Newest first' },
  { value: 'date-asc', label: 'Oldest first' },
  { value: 'name-asc', label: 'Name A-Z' },
  { value: 'name-desc', label: 'Name Z-A' },
  { value: 'status', label: 'Status' },
] as const

type SortOption = typeof SORT_OPTIONS[number]['value']

// ============================================================================
// Persistence helpers
// ============================================================================

function loadProjects(): YTStrategyProject[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY_PROJECTS)
    if (raw) return JSON.parse(raw) as YTStrategyProject[]
  } catch {
    // Corrupted data - start fresh
  }
  return []
}

/** Callback set by the page component to show save errors in the UI. */
let _onSaveError: ((msg: string) => void) | null = null

function saveProjects(projects: YTStrategyProject[]): void {
  try {
    localStorage.setItem(STORAGE_KEY_PROJECTS, JSON.stringify(projects))
  } catch {
    _onSaveError?.('Failed to save projects — localStorage may be full. Your changes may be lost.')
  }
}

function loadSteps(projectId: string): YTStrategyStep[] {
  try {
    const raw = localStorage.getItem(stepsStorageKey(projectId))
    if (raw) return JSON.parse(raw) as YTStrategyStep[]
  } catch {
    // Corrupted data - start fresh
  }
  return []
}

function saveSteps(projectId: string, steps: YTStrategyStep[]): void {
  try {
    localStorage.setItem(stepsStorageKey(projectId), JSON.stringify(steps))
  } catch {
    _onSaveError?.('Failed to save steps — localStorage may be full. Your changes may be lost.')
  }
}

function deleteSteps(projectId: string): void {
  try {
    localStorage.removeItem(stepsStorageKey(projectId))
  } catch {
    // Ignore
  }
}

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`
}

// ============================================================================
// Status display helpers
// ============================================================================

const PROJECT_STATUS_CONFIG: Record<YTProjectStatus, { label: string; className: string }> = {
  'draft': { label: 'Draft', className: 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30' },
  'in-progress': { label: 'In Progress', className: 'bg-blue-500/20 text-blue-400 border-blue-500/30' },
  'complete': { label: 'Complete', className: 'bg-green-500/20 text-green-400 border-green-500/30' },
}

const STEP_STATUS_CONFIG: Record<YTStrategyStepStatus, { label: string; dot: string }> = {
  'pending': { label: 'Pending', dot: 'bg-zinc-400' },
  'in_progress': { label: 'In Progress', dot: 'bg-blue-500' },
  'complete': { label: 'Complete', dot: 'bg-green-500' },
}

// ============================================================================
// Sub-components: Project List View
// ============================================================================

/** Status badge for a project. */
function ProjectStatusBadge({ status }: { status: YTProjectStatus }): React.JSX.Element {
  const config = PROJECT_STATUS_CONFIG[status]
  return (
    <Badge variant="outline" className={config.className}>
      {config.label}
    </Badge>
  )
}

/** Single project card in the list view. */
function ProjectCard({
  project,
  stepsCompleted,
  totalSteps,
  onClick,
  onEdit,
  onParse,
  onDelete,
}: {
  project: YTStrategyProject
  stepsCompleted: number
  totalSteps: number
  onClick: () => void
  onEdit: () => void
  onParse: () => void
  onDelete: () => void
}): React.JSX.Element {
  const isYouTubeUrl = project.sourceUrl && (
    project.sourceUrl.includes('youtube.com') || project.sourceUrl.includes('youtu.be')
  )

  return (
    <Card
      className="cursor-pointer hover:shadow-md transition-shadow group relative"
      onClick={onClick}
    >
      <CardContent className="p-5 space-y-3">
        {/* Header row: name + status */}
        <div className="flex items-start justify-between gap-2">
          <h3 className="text-base font-medium text-foreground leading-tight line-clamp-2">
            {project.name}
          </h3>
          <ProjectStatusBadge status={project.status} />
        </div>

        {/* Source + niche */}
        {project.niche && (
          <p className="text-xs text-muted-foreground flex items-center gap-1">
            <Hash size={12} />
            {project.niche}
          </p>
        )}
        {project.sourceUrl && (
          <p className="text-xs text-muted-foreground flex items-center gap-1 truncate">
            <ExternalLink size={12} />
            <span className="truncate">{project.sourceUrl}</span>
          </p>
        )}

        {/* Parse Video button - shown when source is a YouTube URL */}
        {isYouTubeUrl && (
          <Button
            variant="outline"
            size="sm"
            className="w-full gap-1.5 text-xs"
            onClick={(e) => { e.stopPropagation(); onParse() }}
            aria-label={`Parse video for ${project.name}`}
          >
            <CirclePlay size={14} />
            Parse Video
          </Button>
        )}

        {/* Progress bar */}
        <div className="space-y-1">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>{stepsCompleted} / {totalSteps} steps</span>
            <span>{totalSteps > 0 ? Math.round((stepsCompleted / totalSteps) * 100) : 0}%</span>
          </div>
          <div className="h-1.5 bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-primary rounded-full transition-all duration-300"
              style={{ width: totalSteps > 0 ? `${(stepsCompleted / totalSteps) * 100}%` : '0%' }}
            />
          </div>
        </div>

        {/* Tags */}
        {project.tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {project.tags.slice(0, 4).map((tag) => (
              <span
                key={tag}
                className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground"
              >
                {tag}
              </span>
            ))}
            {project.tags.length > 4 && (
              <span className="text-[10px] text-muted-foreground">
                +{project.tags.length - 4}
              </span>
            )}
          </div>
        )}

        {/* Date */}
        <p className="text-xs text-muted-foreground">
          {new Date(project.createdAt).toLocaleDateString()}
        </p>

        {/* Action buttons (appear on hover) */}
        <div className="absolute top-2 right-2 flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            className="p-1 rounded text-muted-foreground hover:text-foreground hover:bg-muted"
            onClick={(e) => { e.stopPropagation(); onEdit() }}
            aria-label={`Edit project ${project.name}`}
          >
            <Pencil size={14} />
          </button>
          <button
            className="p-1 rounded text-muted-foreground hover:text-destructive hover:bg-destructive/10"
            onClick={(e) => { e.stopPropagation(); onDelete() }}
            aria-label={`Delete project ${project.name}`}
          >
            <Trash2 size={14} />
          </button>
        </div>
      </CardContent>
    </Card>
  )
}

/** Empty state when no projects exist. */
function EmptyProjectState({ onCreate }: { onCreate: () => void }): React.JSX.Element {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <FlaskConical size={48} className="text-muted-foreground/40 mb-4" />
      <h3 className="text-lg font-semibold text-foreground mb-2">
        No strategy projects yet
      </h3>
      <p className="text-sm text-muted-foreground mb-6 max-w-sm">
        Create your first project to start breaking down YouTube strategies into repeatable workflows with prompts.
      </p>
      <Button onClick={onCreate} className="gap-1.5">
        <Plus size={16} />
        New Project
      </Button>
    </div>
  )
}

// ============================================================================
// Sub-components: Create Project Form
// ============================================================================

interface CreateFormData {
  name: string
  sourceUrl: string
  niche: string
  description: string
  tags: string
}

function CreateProjectForm({
  onSubmit,
  onCancel,
  initialData,
  editMode = false,
}: {
  onSubmit: (data: CreateFormData) => void
  onCancel: () => void
  initialData?: CreateFormData
  editMode?: boolean
}): React.JSX.Element {
  const [form, setForm] = useState<CreateFormData>(initialData ?? {
    name: '',
    sourceUrl: '',
    niche: '',
    description: '',
    tags: '',
  })

  const isValid = form.name.trim().length > 0

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (isValid) onSubmit(form)
  }

  return (
    <form onSubmit={handleSubmit} className="max-w-2xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-semibold text-foreground mb-1">
          {editMode ? 'Edit Project' : 'New Strategy Project'}
        </h2>
        <p className="text-sm text-muted-foreground">
          {editMode
            ? 'Update the project details below.'
            : 'Define a new project for extracting and organizing strategies.'}
        </p>
      </div>

      <div className="space-y-4">
        <div className="space-y-1.5">
          <label htmlFor="project-name" className="text-sm font-medium text-foreground">
            Project Name <span className="text-destructive">*</span>
          </label>
          <Input
            id="project-name"
            placeholder='e.g., "AI Ad Agency - Car Dealerships"'
            value={form.name}
            onChange={(e) => setForm(prev => ({ ...prev, name: e.target.value }))}
            autoFocus
          />
        </div>

        <div className="space-y-1.5">
          <label htmlFor="source-url" className="text-sm font-medium text-foreground">
            Source URL
          </label>
          <Input
            id="source-url"
            placeholder="https://youtube.com/watch?v=..."
            value={form.sourceUrl}
            onChange={(e) => setForm(prev => ({ ...prev, sourceUrl: e.target.value }))}
          />
          <p className="text-xs text-muted-foreground">YouTube video or other source URL (optional)</p>
        </div>

        <div className="space-y-1.5">
          <label htmlFor="niche" className="text-sm font-medium text-foreground">
            Niche / Industry
          </label>
          <Input
            id="niche"
            placeholder='e.g., "SaaS", "Real Estate", "E-commerce"'
            value={form.niche}
            onChange={(e) => setForm(prev => ({ ...prev, niche: e.target.value }))}
          />
        </div>

        <div className="space-y-1.5">
          <label htmlFor="description" className="text-sm font-medium text-foreground">
            Description
          </label>
          <Textarea
            id="description"
            placeholder="Brief description of this strategy..."
            value={form.description}
            onChange={(e) => setForm(prev => ({ ...prev, description: e.target.value }))}
            className="min-h-24"
          />
        </div>

        <div className="space-y-1.5">
          <label htmlFor="tags" className="text-sm font-medium text-foreground">
            Tags
          </label>
          <Input
            id="tags"
            placeholder="Comma-separated: ai, automation, lead-gen"
            value={form.tags}
            onChange={(e) => setForm(prev => ({ ...prev, tags: e.target.value }))}
          />
          <p className="text-xs text-muted-foreground">Separate tags with commas</p>
        </div>
      </div>

      <div className="flex items-center gap-3 pt-2">
        <Button type="submit" disabled={!isValid} className="gap-1.5">
          {editMode ? <Pencil size={16} /> : <Plus size={16} />}
          {editMode ? 'Save Changes' : 'Create Project'}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  )
}

// ============================================================================
// Sub-components: Strategy Builder
// ============================================================================

/** A single step entry in the sidebar step list. */
function StepListItem({
  step,
  isSelected,
  onClick,
  onMoveUp,
  onMoveDown,
  isFirst,
  isLast,
}: {
  step: YTStrategyStep
  isSelected: boolean
  onClick: () => void
  onMoveUp: () => void
  onMoveDown: () => void
  isFirst: boolean
  isLast: boolean
}): React.JSX.Element {
  const statusConfig = STEP_STATUS_CONFIG[step.status]

  return (
    <div
      className={`flex items-center gap-2 px-3 py-2 rounded-md cursor-pointer transition-colors group ${
        isSelected
          ? 'bg-primary/10 border border-primary/30'
          : 'hover:bg-muted border border-transparent'
      }`}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onClick() }}
    >
      {/* Drag handle placeholder */}
      <GripVertical size={14} className="text-muted-foreground/40 shrink-0" />

      {/* Step number */}
      <span className="text-xs font-mono text-muted-foreground w-5 text-center shrink-0">
        {step.order}
      </span>

      {/* Status dot + title */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <div className={`w-2 h-2 rounded-full shrink-0 ${statusConfig.dot}`} />
          <span className="text-sm text-foreground truncate">{step.title || 'Untitled Step'}</span>
        </div>
        {step.subSteps.length > 0 && (
          <span className="text-[10px] text-muted-foreground ml-3.5">
            {step.subSteps.length} sub-step{step.subSteps.length !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      {/* Reorder buttons */}
      <div className="flex flex-col opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          onClick={(e) => { e.stopPropagation(); onMoveUp() }}
          disabled={isFirst}
          className="p-0.5 text-muted-foreground hover:text-foreground disabled:opacity-30"
          aria-label="Move step up"
        >
          <ChevronUp size={12} />
        </button>
        <button
          onClick={(e) => { e.stopPropagation(); onMoveDown() }}
          disabled={isLast}
          className="p-0.5 text-muted-foreground hover:text-foreground disabled:opacity-30"
          aria-label="Move step down"
        >
          <ChevronDown size={12} />
        </button>
      </div>
    </div>
  )
}

/** Editable section with label and textarea. */
function EditableSection({
  label,
  value,
  onChange,
  placeholder,
  readOnly,
  minRows,
  icon,
  actions,
}: {
  label: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
  readOnly?: boolean
  minRows?: number
  icon?: React.ReactNode
  actions?: React.ReactNode
}): React.JSX.Element {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
          {icon}
          {label}
        </label>
        {actions}
      </div>
      <Textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        readOnly={readOnly}
        className={`text-sm ${readOnly ? 'bg-muted/50 cursor-default' : ''}`}
        rows={minRows ?? 3}
      />
    </div>
  )
}

/** Model selector dropdown for a step. */
function ModelSelector({
  value,
  onChange,
}: {
  value: string
  onChange: (value: string) => void
}): React.JSX.Element {
  return (
    <div className="flex items-center gap-2">
      <label className="text-xs text-muted-foreground whitespace-nowrap">Model:</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="text-xs bg-card border border-border rounded px-2 py-1 text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
      >
        {MODEL_OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
    </div>
  )
}

/** Sub-step editor row. */
function SubStepRow({
  subStep,
  onUpdate,
  onDelete,
  onStatusChange,
}: {
  subStep: YTStrategySubStep
  onUpdate: (updates: Partial<YTStrategySubStep>) => void
  onDelete: () => void
  onStatusChange: (status: YTStrategyStepStatus) => void
}): React.JSX.Element {
  const [expanded, setExpanded] = useState(false)
  const statusConfig = STEP_STATUS_CONFIG[subStep.status]

  return (
    <div className="border border-border rounded-md p-3 space-y-2 bg-muted/30">
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full shrink-0 ${statusConfig.dot}`} />
        <Input
          value={subStep.title}
          onChange={(e) => onUpdate({ title: e.target.value })}
          placeholder="Sub-step title..."
          className="h-7 text-sm flex-1"
        />
        <button
          onClick={() => setExpanded(!expanded)}
          className="p-1 text-muted-foreground hover:text-foreground"
          aria-label={expanded ? 'Collapse sub-step' : 'Expand sub-step'}
        >
          {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>
        <select
          value={subStep.status}
          onChange={(e) => onStatusChange(e.target.value as YTStrategyStepStatus)}
          className="text-[10px] bg-card border border-border rounded px-1.5 py-0.5 text-foreground"
        >
          <option value="pending">Pending</option>
          <option value="in_progress">In Progress</option>
          <option value="complete">Complete</option>
        </select>
        <button
          onClick={onDelete}
          className="p-1 text-muted-foreground hover:text-destructive"
          aria-label="Delete sub-step"
        >
          <Trash2 size={14} />
        </button>
      </div>

      {expanded && (
        <div className="space-y-2 pl-4">
          <Textarea
            value={subStep.description}
            onChange={(e) => onUpdate({ description: e.target.value })}
            placeholder="What to do in this sub-step..."
            className="text-sm"
            rows={2}
          />
          <Textarea
            value={subStep.prompt}
            onChange={(e) => onUpdate({ prompt: e.target.value })}
            placeholder="Prompt for this sub-step..."
            className="text-sm"
            rows={2}
          />
        </div>
      )}
    </div>
  )
}

/** Full step detail editor - the main content area of the strategy builder. */
function StepDetail({
  step,
  onUpdate,
  onDelete,
  onAddSubStep,
  onUpdateSubStep,
  onDeleteSubStep,
  onStatusChange,
  onSubStepStatusChange,
}: {
  step: YTStrategyStep
  onUpdate: (updates: Partial<YTStrategyStep>) => void
  onDelete: () => void
  onAddSubStep: () => void
  onUpdateSubStep: (subStepId: string, updates: Partial<YTStrategySubStep>) => void
  onDeleteSubStep: (subStepId: string) => void
  onStatusChange: (status: YTStrategyStepStatus) => void
  onSubStepStatusChange: (subStepId: string, status: YTStrategyStepStatus) => void
}): React.JSX.Element {
  const statusConfig = STEP_STATUS_CONFIG[step.status]
  const [confirmDeleteStep, setConfirmDeleteStep] = useState(false)
  const [confirmDeleteSubStepId, setConfirmDeleteSubStepId] = useState<string | null>(null)

  /** Copy prompt text to clipboard. */
  const copyPrompt = useCallback(() => {
    if (step.prompt) {
      navigator.clipboard.writeText(step.prompt).catch(() => {
        // Clipboard API not available
      })
    }
  }, [step.prompt])

  return (
    <div className="space-y-6">
      {/* Step deletion confirmation */}
      {confirmDeleteStep && (
        <div className="flex items-center gap-3 rounded-md border border-destructive/30 bg-destructive/5 px-4 py-3">
          <p className="text-sm text-foreground flex-1">
            Delete <strong>Step {step.order}{step.title ? `: ${step.title}` : ''}</strong> and all its sub-steps?
          </p>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setConfirmDeleteStep(false)}
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={() => { setConfirmDeleteStep(false); onDelete() }}
          >
            Delete
          </Button>
        </div>
      )}

      {/* Sub-step deletion confirmation */}
      {confirmDeleteSubStepId && (
        <div className="flex items-center gap-3 rounded-md border border-destructive/30 bg-destructive/5 px-4 py-3">
          <p className="text-sm text-foreground flex-1">Delete this sub-step?</p>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setConfirmDeleteSubStepId(null)}
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={() => { onDeleteSubStep(confirmDeleteSubStepId); setConfirmDeleteSubStepId(null) }}
          >
            Delete
          </Button>
        </div>
      )}

      {/* Step header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-sm font-mono text-muted-foreground">Step {step.order}:</span>
            <Input
              value={step.title}
              onChange={(e) => onUpdate({ title: e.target.value })}
              placeholder="Step title..."
              className="text-lg font-semibold h-auto py-1 border-none shadow-none focus-visible:ring-0 px-0"
            />
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <div className={`w-2.5 h-2.5 rounded-full ${statusConfig.dot}`} />
              <select
                value={step.status}
                onChange={(e) => onStatusChange(e.target.value as YTStrategyStepStatus)}
                className="text-xs bg-card border border-border rounded px-2 py-1 text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
              >
                <option value="pending">Pending</option>
                <option value="in_progress">In Progress</option>
                <option value="complete">Complete</option>
              </select>
            </div>
            <ModelSelector
              value={step.model}
              onChange={(model) => onUpdate({ model })}
            />
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setConfirmDeleteStep(true)}
          className="text-destructive hover:bg-destructive/10 shrink-0"
          aria-label="Delete step"
        >
          <Trash2 size={14} />
        </Button>
      </div>

      {/* Editable sections */}
      <EditableSection
        label="What to Do"
        value={step.description}
        onChange={(description) => onUpdate({ description })}
        placeholder="Describe what needs to be done in this step..."
        icon={<FileText size={12} />}
        minRows={3}
      />

      <EditableSection
        label="Prompt"
        value={step.prompt}
        onChange={(prompt) => onUpdate({ prompt })}
        placeholder="The actual prompt to use with the AI model..."
        icon={<Sparkles size={12} />}
        minRows={5}
        actions={
          <Button
            variant="ghost"
            size="sm"
            className="h-6 px-2 text-xs gap-1 text-muted-foreground"
            onClick={copyPrompt}
            aria-label="Copy prompt to clipboard"
          >
            <ClipboardCopy size={12} />
            Copy
          </Button>
        }
      />

      <EditableSection
        label="Expected Output"
        value={step.expectedOutput}
        onChange={(expectedOutput) => onUpdate({ expectedOutput })}
        placeholder="What should the AI response look like..."
        icon={<ListOrdered size={12} />}
        minRows={3}
      />

      <EditableSection
        label="Notes & Enhancements"
        value={step.notes}
        onChange={(notes) => onUpdate({ notes })}
        placeholder="Your additions, improvements, ideas..."
        icon={<Pencil size={12} />}
        minRows={3}
      />

      <EditableSection
        label="AI Output (Results)"
        value={step.aiOutput}
        onChange={(aiOutput) => onUpdate({ aiOutput })}
        placeholder="Paste or store AI responses here..."
        icon={<CirclePlay size={12} />}
        minRows={4}
      />

      {/* Sub-steps */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
            <Hash size={12} />
            Sub-Steps ({step.subSteps.length})
          </label>
          <Button
            variant="outline"
            size="sm"
            className="h-7 text-xs gap-1"
            onClick={onAddSubStep}
          >
            <Plus size={12} />
            Add Sub-Step
          </Button>
        </div>

        {step.subSteps.length === 0 ? (
          <p className="text-xs text-muted-foreground py-2">
            No sub-steps yet. Add one to break this step into smaller tasks.
          </p>
        ) : (
          <div className="space-y-2">
            {step.subSteps.map((subStep) => (
              <SubStepRow
                key={subStep.id}
                subStep={subStep}
                onUpdate={(updates) => onUpdateSubStep(subStep.id, updates)}
                onDelete={() => setConfirmDeleteSubStepId(subStep.id)}
                onStatusChange={(status) => onSubStepStatusChange(subStep.id, status)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Action buttons */}
      <div className="flex items-center gap-3 pt-2 border-t border-border">
        <Button
          variant={step.status === 'complete' ? 'outline' : 'default'}
          size="sm"
          className="gap-1.5"
          onClick={() => onStatusChange(step.status === 'complete' ? 'pending' : 'complete')}
        >
          <CircleCheck size={14} />
          {step.status === 'complete' ? 'Mark Incomplete' : 'Mark Complete'}
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="gap-1.5"
          onClick={onAddSubStep}
        >
          <Plus size={14} />
          Add Sub-Step
        </Button>
      </div>
    </div>
  )
}

/** Empty state when no step is selected. */
function NoStepSelected(): React.JSX.Element {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center py-20">
      <FolderOpen size={40} className="text-muted-foreground/40 mb-3" />
      <h3 className="text-base font-medium text-foreground mb-1">No step selected</h3>
      <p className="text-sm text-muted-foreground max-w-xs">
        Select a step from the sidebar or add a new one to get started.
      </p>
    </div>
  )
}

/** Empty state when project has no steps. */
function NoStepsYet({ onAddStep }: { onAddStep: () => void }): React.JSX.Element {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center py-20">
      <ListOrdered size={40} className="text-muted-foreground/40 mb-3" />
      <h3 className="text-base font-medium text-foreground mb-1">No steps yet</h3>
      <p className="text-sm text-muted-foreground mb-4 max-w-xs">
        Add your first step to start building out this strategy workflow.
      </p>
      <Button onClick={onAddStep} className="gap-1.5">
        <Plus size={16} />
        Add First Step
      </Button>
    </div>
  )
}

// ============================================================================
// Strategy Builder (Project Detail) View
// ============================================================================

function StrategyBuilder({
  project,
  onUpdateProject,
}: {
  project: YTStrategyProject
  onUpdateProject: (updates: Partial<YTStrategyProject>) => void
}): React.JSX.Element {
  const [steps, setSteps] = useState<YTStrategyStep[]>(() => loadSteps(project.id))
  const [selectedStepId, setSelectedStepId] = useState<string | null>(
    () => steps.length > 0 ? steps[0].id : null
  )
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  // --- AI Processing state (Phase 2) ---
  const [ingestResult, setIngestResult] = useState<YTIngestResponse | null>(null)
  const [userContext, setUserContext] = useState('')
  const [processingModel, setProcessingModel] = useState('claude-sonnet-4-6')
  const [isProcessing, setIsProcessing] = useState(false)
  const [processingError, setProcessingError] = useState<string | null>(null)
  const [processingTime, setProcessingTime] = useState<number | null>(null)

  // Persist steps whenever they change
  useEffect(() => {
    saveSteps(project.id, steps)

    // Derive project status from step states — only update if it actually changed
    let derivedStatus: YTProjectStatus
    if (steps.length === 0) {
      derivedStatus = 'draft'
    } else if (steps.every(s => s.status === 'complete')) {
      derivedStatus = 'complete'
    } else if (steps.some(s => s.status === 'in_progress' || s.status === 'complete')) {
      derivedStatus = 'in-progress'
    } else {
      derivedStatus = 'draft'
    }
    if (derivedStatus !== project.status) {
      onUpdateProject({ status: derivedStatus })
    }
  }, [steps, project.id, project.status, onUpdateProject])

  const selectedStep = useMemo(
    () => steps.find(s => s.id === selectedStepId) ?? null,
    [steps, selectedStepId]
  )

  /** Add a new step at the end of the list. */
  const addStep = useCallback(() => {
    const newStep: YTStrategyStep = {
      id: generateId(),
      projectId: project.id,
      order: steps.length + 1,
      title: '',
      description: '',
      prompt: '',
      expectedOutput: '',
      notes: '',
      aiOutput: '',
      status: 'pending',
      model: 'claude-opus-4-6',
      subSteps: [],
    }
    setSteps(prev => [...prev, newStep])
    setSelectedStepId(newStep.id)
  }, [project.id, steps.length])

  /** Update a step's fields. */
  const updateStep = useCallback((stepId: string, updates: Partial<YTStrategyStep>) => {
    setSteps(prev => prev.map(s => s.id === stepId ? { ...s, ...updates } : s))
  }, [])

  /** Delete a step and re-number remaining steps. */
  const deleteStep = useCallback((stepId: string) => {
    setSteps(prev => {
      const filtered = prev.filter(s => s.id !== stepId)
      // Select an adjacent step if the deleted step was selected
      if (selectedStepId === stepId) {
        const deletedIdx = prev.findIndex(s => s.id === stepId)
        const nextStep = filtered[Math.min(deletedIdx, filtered.length - 1)] ?? null
        setSelectedStepId(nextStep?.id ?? null)
      }
      // Re-number
      return filtered.map((s, i) => ({ ...s, order: i + 1 }))
    })
  }, [selectedStepId])

  /** Move a step up (decrease order). */
  const moveStepUp = useCallback((stepId: string) => {
    setSteps(prev => {
      const idx = prev.findIndex(s => s.id === stepId)
      if (idx <= 0) return prev
      const next = [...prev]
      ;[next[idx - 1], next[idx]] = [next[idx], next[idx - 1]]
      return next.map((s, i) => ({ ...s, order: i + 1 }))
    })
  }, [])

  /** Move a step down (increase order). */
  const moveStepDown = useCallback((stepId: string) => {
    setSteps(prev => {
      const idx = prev.findIndex(s => s.id === stepId)
      if (idx < 0 || idx >= prev.length - 1) return prev
      const next = [...prev]
      ;[next[idx], next[idx + 1]] = [next[idx + 1], next[idx]]
      return next.map((s, i) => ({ ...s, order: i + 1 }))
    })
  }, [])

  /** Change a step's status. */
  const changeStepStatus = useCallback((stepId: string, status: YTStrategyStepStatus) => {
    updateStep(stepId, { status })
  }, [updateStep])

  /** Add a sub-step to the selected step. */
  const addSubStep = useCallback((stepId: string) => {
    setSteps(prev => prev.map(s => {
      if (s.id !== stepId) return s
      const newSubStep: YTStrategySubStep = {
        id: generateId(),
        stepId,
        order: s.subSteps.length + 1,
        title: '',
        description: '',
        prompt: '',
        status: 'pending',
      }
      return { ...s, subSteps: [...s.subSteps, newSubStep] }
    }))
  }, [])

  /** Update a sub-step's fields. */
  const updateSubStep = useCallback((stepId: string, subStepId: string, updates: Partial<YTStrategySubStep>) => {
    setSteps(prev => prev.map(s => {
      if (s.id !== stepId) return s
      return {
        ...s,
        subSteps: s.subSteps.map(ss => ss.id === subStepId ? { ...ss, ...updates } : ss),
      }
    }))
  }, [])

  /** Delete a sub-step and re-number remaining sub-steps. */
  const deleteSubStep = useCallback((stepId: string, subStepId: string) => {
    setSteps(prev => prev.map(s => {
      if (s.id !== stepId) return s
      const filtered = s.subSteps.filter(ss => ss.id !== subStepId)
      return {
        ...s,
        subSteps: filtered.map((ss, i) => ({ ...ss, order: i + 1 })),
      }
    }))
  }, [])

  /** Change a sub-step's status. */
  const changeSubStepStatus = useCallback((stepId: string, subStepId: string, status: YTStrategyStepStatus) => {
    updateSubStep(stepId, subStepId, { status })
  }, [updateSubStep])

  /** Handle ingestion complete — store result for processing. */
  const handleIngestComplete = useCallback((result: YTIngestResponse) => {
    setIngestResult(result)
    setProcessingError(null)
    setProcessingTime(null)
  }, [])

  /** Process ingested video through AI to generate steps. */
  const handleProcessVideo = useCallback(async () => {
    if (!ingestResult) return

    setIsProcessing(true)
    setProcessingError(null)
    setProcessingTime(null)

    try {
      const response = await processYouTubeVideo({
        video_id: ingestResult.video_id,
        transcript: ingestResult.transcript,
        metadata: {
          title: ingestResult.title,
          channel: ingestResult.channel,
          duration: ingestResult.duration,
          description: ingestResult.description,
        },
        user_context: userContext,
        extracted_urls: ingestResult.extracted_urls,
        screenshot_suggestions: ingestResult.screenshot_suggestions,
        model: processingModel,
      })

      // Update project metadata from AI response
      onUpdateProject({
        name: response.project.name || project.name,
        niche: response.project.niche || project.niche,
        description: response.project.description || project.description,
        tags: response.project.tags.length > 0 ? response.project.tags : project.tags,
      })

      // Create steps from AI response
      const newSteps: YTStrategyStep[] = response.steps.map((s) => ({
        id: generateId(),
        projectId: project.id,
        order: s.order,
        title: s.title,
        description: s.description,
        prompt: s.prompt,
        expectedOutput: s.expectedOutput,
        notes: s.notes,
        aiOutput: '',
        status: 'pending' as const,
        model: s.model || 'claude-opus-4-6',
        subSteps: [],
      }))

      setSteps(newSteps)
      if (newSteps.length > 0) {
        setSelectedStepId(newSteps[0].id)
      }
      setProcessingTime(response.processing_time)
    } catch (err) {
      setProcessingError(err instanceof Error ? err.message : 'Failed to process video')
    } finally {
      setIsProcessing(false)
    }
  }, [ingestResult, userContext, processingModel, project.id, project.name, project.niche, project.description, project.tags, onUpdateProject])

  const completedCount = steps.filter(s => s.status === 'complete').length

  return (
    <div className="flex flex-1 overflow-hidden">
      {/* Left sidebar */}
      {!sidebarCollapsed ? (
        <div className="w-72 border-r border-border flex flex-col shrink-0 bg-card">
          {/* Project info */}
          <div className="p-4 border-b border-border space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-foreground truncate">{project.name}</h3>
              <button
                onClick={() => setSidebarCollapsed(true)}
                className="p-1 text-muted-foreground hover:text-foreground"
                aria-label="Collapse sidebar"
              >
                <PanelLeftClose size={16} />
              </button>
            </div>
            {project.niche && (
              <p className="text-xs text-muted-foreground flex items-center gap-1">
                <Hash size={10} /> {project.niche}
              </p>
            )}
            <div className="text-xs text-muted-foreground">
              {completedCount} / {steps.length} steps complete
            </div>
            {steps.length > 0 && (
              <div className="h-1 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full transition-all duration-300"
                  style={{ width: `${(completedCount / steps.length) * 100}%` }}
                />
              </div>
            )}
          </div>

          {/* Step list */}
          <div className="flex-1 overflow-auto p-2 space-y-1">
            {steps.map((step, idx) => (
              <StepListItem
                key={step.id}
                step={step}
                isSelected={step.id === selectedStepId}
                onClick={() => setSelectedStepId(step.id)}
                onMoveUp={() => moveStepUp(step.id)}
                onMoveDown={() => moveStepDown(step.id)}
                isFirst={idx === 0}
                isLast={idx === steps.length - 1}
              />
            ))}
          </div>

          {/* Add step button */}
          <div className="p-3 border-t border-border">
            <Button
              variant="outline"
              size="sm"
              className="w-full gap-1.5"
              onClick={addStep}
            >
              <Plus size={14} />
              Add Step
            </Button>
          </div>
        </div>
      ) : (
        /* Collapsed sidebar strip */
        <div className="w-10 shrink-0 flex flex-col items-center border-r border-border bg-card">
          <button
            onClick={() => setSidebarCollapsed(false)}
            className="p-2 text-muted-foreground hover:text-foreground"
            aria-label="Expand sidebar"
          >
            <PanelLeftOpen size={16} />
          </button>
        </div>
      )}

      {/* Main content area */}
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-3xl mx-auto space-y-6">
          {/* Video Ingest Panel — shown when project has a YouTube source URL */}
          {project.sourceUrl && (
            project.sourceUrl.includes('youtube.com') || project.sourceUrl.includes('youtu.be')
          ) && (
            <VideoIngestPanel onIngestComplete={handleIngestComplete} />
          )}

          {/* AI Processing Panel — shown after successful ingestion */}
          {ingestResult && (
            <div className="rounded-lg border border-border bg-card">
              <div className="flex items-center gap-2 border-b border-border px-4 py-3">
                <Wand2 size={18} className="text-primary" />
                <h3 className="text-sm font-semibold text-foreground">AI Strategy Extraction</h3>
                {processingTime != null && (
                  <span className="ml-auto text-xs text-muted-foreground">
                    Processed in {processingTime.toFixed(1)}s
                  </span>
                )}
              </div>

              <div className="p-4 space-y-4">
                {/* User context textarea */}
                <div className="space-y-1.5">
                  <label htmlFor="user-context" className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    What do you want to extract from this video?
                  </label>
                  <Textarea
                    id="user-context"
                    value={userContext}
                    onChange={(e) => setUserContext(e.target.value)}
                    placeholder="e.g., I want the step-by-step process for building an AI ad agency. Focus on the automation workflow and computer-use prompts."
                    className="min-h-20 text-sm"
                    disabled={isProcessing}
                  />
                  <p className="text-xs text-muted-foreground">
                    Providing context helps the AI focus on what matters to you. Leave blank to extract the full strategy.
                  </p>
                </div>

                {/* Model selection */}
                <div className="space-y-1.5">
                  <label htmlFor="processing-model" className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Processing Model
                  </label>
                  <select
                    id="processing-model"
                    value={processingModel}
                    onChange={(e) => setProcessingModel(e.target.value)}
                    disabled={isProcessing}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm
                      text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent
                      disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <option value="claude-sonnet-4-6">Claude Sonnet 4.6 (Recommended)</option>
                    <option value="claude-opus-4-6">Claude Opus 4.6 (Premium)</option>
                    <option value="claude-haiku-4-5">Claude Haiku 4.5 (Fast)</option>
                  </select>
                </div>

                {/* Error message */}
                {processingError && (
                  <div className="flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2">
                    <AlertCircle size={16} className="text-destructive shrink-0 mt-0.5" />
                    <p className="text-sm text-destructive">{processingError}</p>
                  </div>
                )}

                {/* Process button */}
                <Button
                  onClick={handleProcessVideo}
                  disabled={isProcessing || !ingestResult.transcript.length}
                  className="w-full gap-2"
                >
                  {isProcessing ? (
                    <>
                      <Loader2 size={16} className="animate-spin" />
                      Processing Video...
                    </>
                  ) : (
                    <>
                      <Sparkles size={16} />
                      Process Video
                    </>
                  )}
                </Button>

                {!ingestResult.transcript.length && (
                  <p className="text-xs text-muted-foreground text-center">
                    No transcript available — video processing requires a transcript.
                  </p>
                )}
              </div>
            </div>
          )}

          {steps.length === 0 ? (
            <NoStepsYet onAddStep={addStep} />
          ) : selectedStep ? (
            <StepDetail
              step={selectedStep}
              onUpdate={(updates) => updateStep(selectedStep.id, updates)}
              onDelete={() => deleteStep(selectedStep.id)}
              onAddSubStep={() => addSubStep(selectedStep.id)}
              onUpdateSubStep={(subStepId, updates) => updateSubStep(selectedStep.id, subStepId, updates)}
              onDeleteSubStep={(subStepId) => deleteSubStep(selectedStep.id, subStepId)}
              onStatusChange={(status) => changeStepStatus(selectedStep.id, status)}
              onSubStepStatusChange={(subStepId, status) => changeSubStepStatus(selectedStep.id, subStepId, status)}
            />
          ) : (
            <NoStepSelected />
          )}
        </div>
      </div>
    </div>
  )
}

// ============================================================================
// Main Page Component
// ============================================================================

type View = 'list' | 'create' | 'edit' | 'detail'

export function YTStrategyLabPage(): React.JSX.Element {
  const [view, setView] = useState<View>('list')
  const [projects, setProjects] = useState<YTStrategyProject[]>(loadProjects)
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null)
  const [editingProjectId, setEditingProjectId] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState<SortOption>('date-desc')
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null)
  const [saveError, setSaveError] = useState<string | null>(null)

  // Register save error callback so persistence helpers can show errors
  useEffect(() => {
    _onSaveError = (msg) => setSaveError(msg)
    return () => { _onSaveError = null }
  }, [])

  // Persist projects whenever they change
  useEffect(() => {
    saveProjects(projects)
  }, [projects])

  const selectedProject = useMemo(
    () => projects.find(p => p.id === selectedProjectId) ?? null,
    [projects, selectedProjectId]
  )

  /** Memoized step counts for all projects — avoids localStorage reads during render. */
  const stepCountsMap = useMemo(() => {
    const map: Record<string, { total: number; completed: number }> = {}
    for (const p of projects) {
      const steps = loadSteps(p.id)
      map[p.id] = {
        total: steps.length,
        completed: steps.filter(s => s.status === 'complete').length,
      }
    }
    return map
  }, [projects])

  const getStepCounts = useCallback((projectId: string) => {
    return stepCountsMap[projectId] ?? { total: 0, completed: 0 }
  }, [stepCountsMap])

  /** Filtered and sorted projects for the list view. */
  const filteredProjects = useMemo(() => {
    let result = projects

    // Apply search filter
    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      result = result.filter(p =>
        p.name.toLowerCase().includes(q) ||
        p.niche.toLowerCase().includes(q) ||
        p.description.toLowerCase().includes(q) ||
        p.tags.some(t => t.toLowerCase().includes(q))
      )
    }

    // Apply sort
    const sorted = [...result]
    switch (sortBy) {
      case 'date-desc':
        sorted.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
        break
      case 'date-asc':
        sorted.sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime())
        break
      case 'name-asc':
        sorted.sort((a, b) => a.name.localeCompare(b.name))
        break
      case 'name-desc':
        sorted.sort((a, b) => b.name.localeCompare(a.name))
        break
      case 'status': {
        const statusOrder: Record<YTProjectStatus, number> = { 'in-progress': 0, 'draft': 1, 'complete': 2 }
        sorted.sort((a, b) => statusOrder[a.status] - statusOrder[b.status])
        break
      }
    }

    return sorted
  }, [projects, searchQuery, sortBy])

  /** Create a new project. */
  const handleCreateProject = useCallback((data: CreateFormData) => {
    const now = new Date().toISOString()
    const newProject: YTStrategyProject = {
      id: generateId(),
      name: data.name.trim(),
      sourceUrl: data.sourceUrl.trim(),
      niche: data.niche.trim(),
      description: data.description.trim(),
      tags: data.tags
        .split(',')
        .map(t => t.trim())
        .filter(t => t.length > 0),
      status: 'draft',
      createdAt: now,
      updatedAt: now,
    }
    setProjects(prev => [newProject, ...prev])
    setSelectedProjectId(newProject.id)
    setView('detail')
  }, [])

  /** Open edit form for a project. */
  const handleEditProject = useCallback((projectId: string) => {
    setEditingProjectId(projectId)
    setView('edit')
  }, [])

  /** Save edits to an existing project. */
  const handleSaveEdit = useCallback((data: CreateFormData) => {
    if (!editingProjectId) return
    setProjects(prev => prev.map(p =>
      p.id === editingProjectId
        ? {
            ...p,
            name: data.name.trim(),
            sourceUrl: data.sourceUrl.trim(),
            niche: data.niche.trim(),
            description: data.description.trim(),
            tags: data.tags.split(',').map(t => t.trim()).filter(t => t.length > 0),
            updatedAt: new Date().toISOString(),
          }
        : p
    ))
    setEditingProjectId(null)
    setView('list')
  }, [editingProjectId])

  /** Handle parsing a YouTube video for a project. */
  const handleParseVideo = useCallback((projectId: string) => {
    setSelectedProjectId(projectId)
    setView('detail')
    // TODO: Auto-open the VideoIngestPanel when navigating to detail view
    // For now, navigates to the project so user can use the ingest panel there
  }, [])

  /** Delete a project and its steps. */
  const handleDeleteProject = useCallback((projectId: string) => {
    deleteSteps(projectId)
    setProjects(prev => prev.filter(p => p.id !== projectId))
    if (selectedProjectId === projectId) {
      setSelectedProjectId(null)
      setView('list')
    }
    setConfirmDeleteId(null)
  }, [selectedProjectId])

  /** Open a project in the strategy builder. */
  const handleOpenProject = useCallback((projectId: string) => {
    setSelectedProjectId(projectId)
    setView('detail')
  }, [])

  /** Update a project's fields. */
  const handleUpdateProject = useCallback((updates: Partial<YTStrategyProject>) => {
    if (!selectedProjectId) return
    setProjects(prev => prev.map(p =>
      p.id === selectedProjectId
        ? { ...p, ...updates, updatedAt: new Date().toISOString() }
        : p
    ))
  }, [selectedProjectId])

  /** Navigate back to the project list. */
  const handleBackToList = useCallback(() => {
    setSelectedProjectId(null)
    setView('list')
  }, [])

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Breadcrumb navigation bar */}
      <div className="flex items-center h-10 px-3 border-b border-border bg-card shrink-0">
        <nav className="flex items-center gap-1 text-sm" aria-label="Breadcrumb">
          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5 text-muted-foreground hover:text-foreground h-7 px-2"
            onClick={() => { window.location.hash = '' }}
          >
            <ArrowLeft size={14} />
            <span className="text-xs">AutoForge</span>
          </Button>
          <ChevronRight size={12} className="text-muted-foreground" />

          {view === 'list' && (
            <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
              <FlaskConical size={12} />
              YT Strategy Lab
            </span>
          )}

          {(view === 'create' || view === 'edit') && (
            <>
              <Button
                variant="ghost"
                size="sm"
                className="text-muted-foreground hover:text-foreground h-7 px-2"
                onClick={() => { setEditingProjectId(null); setView('list') }}
              >
                <span className="text-xs">YT Strategy Lab</span>
              </Button>
              <ChevronRight size={12} className="text-muted-foreground" />
              <span className="text-xs font-semibold text-foreground">
                {view === 'edit' ? 'Edit Project' : 'New Project'}
              </span>
            </>
          )}

          {view === 'detail' && selectedProject && (
            <>
              <Button
                variant="ghost"
                size="sm"
                className="text-muted-foreground hover:text-foreground h-7 px-2"
                onClick={handleBackToList}
              >
                <span className="text-xs">YT Strategy Lab</span>
              </Button>
              <ChevronRight size={12} className="text-muted-foreground" />
              <span className="text-xs font-semibold text-foreground truncate max-w-[200px]">
                {selectedProject.name}
              </span>
            </>
          )}
        </nav>

        {/* Right side: Import Template placeholder */}
        {view === 'list' && (
          <div className="ml-auto flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              className="h-7 px-2 gap-1.5 text-muted-foreground"
              disabled
              title="Import from template (coming soon)"
            >
              <FolderOpen size={14} />
              <span className="text-[10px]">Import Template</span>
            </Button>
          </div>
        )}
      </div>

      {/* Save error banner */}
      {saveError && (
        <div className="flex items-center gap-2 px-4 py-2 bg-destructive/10 border-b border-destructive/30">
          <AlertCircle size={14} className="text-destructive shrink-0" />
          <p className="text-xs text-destructive flex-1">{saveError}</p>
          <button
            onClick={() => setSaveError(null)}
            className="p-0.5 text-destructive hover:text-destructive/80"
            aria-label="Dismiss save error"
          >
            <X size={14} />
          </button>
        </div>
      )}

      {/* Main content */}
      {view === 'list' && (
        <div className="flex-1 overflow-auto p-6">
          <div className="max-w-7xl mx-auto space-y-6">
            {/* Page header + controls */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <h1 className="text-2xl font-semibold text-foreground flex items-center gap-2">
                  <FlaskConical size={24} />
                  YT Strategy Lab
                </h1>
                <p className="text-sm text-muted-foreground mt-1">
                  Extract, organize, and operationalize strategies from YouTube videos.
                </p>
              </div>
              <Button onClick={() => setView('create')} className="gap-1.5 shrink-0">
                <Plus size={16} />
                New Project
              </Button>
            </div>

            {/* Search + sort controls */}
            {projects.length > 0 && (
              <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
                <div className="relative flex-1 max-w-sm">
                  <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    placeholder="Search projects..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-8 h-8 text-sm"
                  />
                  {searchQuery && (
                    <button
                      onClick={() => setSearchQuery('')}
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-0.5 text-muted-foreground hover:text-foreground"
                      aria-label="Clear search"
                    >
                      <X size={14} />
                    </button>
                  )}
                </div>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as SortOption)}
                  className="text-xs bg-card border border-border rounded px-2 py-1.5 text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                >
                  {SORT_OPTIONS.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
                <span className="text-xs text-muted-foreground">
                  {filteredProjects.length} project{filteredProjects.length !== 1 ? 's' : ''}
                </span>
              </div>
            )}

            {/* Project grid or empty state */}
            {projects.length === 0 ? (
              <EmptyProjectState onCreate={() => setView('create')} />
            ) : filteredProjects.length === 0 ? (
              <div className="text-center py-12">
                <Search size={32} className="text-muted-foreground/40 mx-auto mb-3" />
                <p className="text-sm text-muted-foreground">
                  No projects match &ldquo;{searchQuery}&rdquo;
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredProjects.map((project) => {
                  const counts = getStepCounts(project.id)
                  return (
                    <ProjectCard
                      key={project.id}
                      project={project}
                      stepsCompleted={counts.completed}
                      totalSteps={counts.total}
                      onClick={() => handleOpenProject(project.id)}
                      onEdit={() => handleEditProject(project.id)}
                      onParse={() => handleParseVideo(project.id)}
                      onDelete={() => setConfirmDeleteId(project.id)}
                    />
                  )
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {view === 'create' && (
        <div className="flex-1 overflow-auto p-6">
          <CreateProjectForm
            onSubmit={handleCreateProject}
            onCancel={handleBackToList}
          />
        </div>
      )}

      {view === 'edit' && editingProjectId && (() => {
        const editProject = projects.find(p => p.id === editingProjectId)
        if (!editProject) return null
        return (
          <div className="flex-1 overflow-auto p-6">
            <CreateProjectForm
              editMode
              initialData={{
                name: editProject.name,
                sourceUrl: editProject.sourceUrl,
                niche: editProject.niche,
                description: editProject.description,
                tags: editProject.tags.join(', '),
              }}
              onSubmit={handleSaveEdit}
              onCancel={() => { setEditingProjectId(null); setView('list') }}
            />
          </div>
        )
      })()}

      {view === 'detail' && selectedProject && (
        <StrategyBuilder
          project={selectedProject}
          onUpdateProject={handleUpdateProject}
        />
      )}

      {/* Delete confirmation overlay */}
      {confirmDeleteId && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-labelledby="delete-dialog-title"
          aria-describedby="delete-dialog-desc"
          onClick={(e) => { if (e.target === e.currentTarget) setConfirmDeleteId(null) }}
          onKeyDown={(e) => { if (e.key === 'Escape') setConfirmDeleteId(null) }}
        >
          <Card className="w-full max-w-sm mx-4">
            <CardContent className="p-6 space-y-4">
              <h3 id="delete-dialog-title" className="text-base font-semibold text-foreground">Delete Project?</h3>
              <p id="delete-dialog-desc" className="text-sm text-muted-foreground">
                This will permanently delete the project and all its steps. This action cannot be undone.
              </p>
              <div className="flex items-center gap-3 justify-end">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setConfirmDeleteId(null)}
                >
                  Cancel
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => handleDeleteProject(confirmDeleteId)}
                  autoFocus
                >
                  Delete
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
