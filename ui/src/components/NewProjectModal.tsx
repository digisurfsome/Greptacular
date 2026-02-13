/**
 * New Project Modal Component
 *
 * Full-screen multi-step wizard for creating new projects:
 * 1. Enter project name
 * 2. Select project folder
 * 3. Choose boilerplate (web, mobile, scratch, etc.)
 * 4. Choose design style (with AI recommendation)
 * 5. Choose spec method (Claude or manual)
 * 6a. If Claude: Show SpecCreationChat
 * 6b. If manual: Create project and close
 *
 * All steps render as full-screen portals with a persistent step
 * progress indicator at the top for a consistent, immersive UX.
 */

import { useState, useMemo, useCallback, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import {
  Bot,
  FileEdit,
  ArrowRight,
  ArrowLeft,
  Loader2,
  CheckCircle2,
  Folder,
  Globe,
  Smartphone,
  Layers,
  Zap,
  Sparkles,
  Paintbrush,
  Check,
  Upload,
  ImageIcon,
  X,
  Grid2x2,
  Maximize2,
} from 'lucide-react'
import { useCreateProject, useBoilerplates, useStyles, useStyleProfiles, useStyleRecommendations, useStyleModifiers, useDescriptionRecommendation, useAccentCompatibility, useExtractStyleFromScreenshot } from '../hooks/useProjects'
import { SpecCreationChat } from './SpecCreationChat'
import { FolderBrowser } from './FolderBrowser'
import { StylePreview } from './StylePreview'
import type { PreviewPage } from './StylePreview'
import { ColorCustomizer } from './ColorCustomizer'
import { startAgent } from '../lib/api'
import type { BoilerplateCategory, StyleOption, AccentStyleOption, StyleExtractionResult } from '../lib/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'

type InitializerStatus = 'idle' | 'starting' | 'error'

type Step = 'name' | 'folder' | 'boilerplate' | 'style' | 'method' | 'chat' | 'complete'
type SpecMethod = 'claude' | 'manual'
type StyleCategory = 'all' | 'core' | 'vibe'
type StyleView = 'browse' | 'preview'

/** Sequential step definitions for the progress bar */
const STEP_ORDER: { id: Step; label: string }[] = [
  { id: 'name', label: 'Project' },
  { id: 'folder', label: 'Location' },
  { id: 'boilerplate', label: 'Boilerplate' },
  { id: 'style', label: 'Design' },
  { id: 'method', label: 'Setup' },
  { id: 'chat', label: 'Build' },
]

/** Map category IDs to lucide-react icons */
const CATEGORY_ICONS: Record<string, React.ComponentType<{ size?: number; className?: string }>> = {
  web: Globe,
  mobile: Smartphone,
  web_mobile: Layers,
  scratch: Zap,
}

/** Preview color swatches for each style (brand + surface + accent) */
const STYLE_SWATCHES: Record<string, string[]> = {
  'flat-design': ['#3B82F6', '#F8FAFC', '#0F172A', '#22C55E'],
  'minimalism': ['#111827', '#FFFFFF', '#6B7280', '#F9FAFB'],
  'neumorphism': ['#6366F1', '#E0E5EC', '#2D3748', '#b8bec7'],
  'glassmorphism': ['#A855F7', '#667eea', '#764ba2', '#FFFFFF'],
  'skeuomorphism': ['#2563EB', '#F5F0EB', '#E8E0D8', '#1A1A1A'],
  'neubrutalism': ['#FACC15', '#FFFBEB', '#18181B', '#EF4444'],
  'bauhaus': ['#DC2626', '#FAFAFA', '#2563EB', '#FACC15'],
  'claymorphism': ['#F59E0B', '#FFF7ED', '#292524', '#FEF3E2'],
  'retro-futurism': ['#D946EF', '#0C0A1A', '#06B6D4', '#F97316'],
  'cyberpunk': ['#06B6D4', '#09090B', '#F43F5E', '#FBBF24'],
  'dark-mode': ['#3B82F6', '#0F172A', '#1E293B', '#F1F5F9'],
  'warmer-shades': ['#D97706', '#FFFBF5', '#FFF8F0', '#292524'],
}

// ---------------------------------------------------------------------------
// Step Progress Bar
// ---------------------------------------------------------------------------

/** Persistent top nav bar with logo and step progress indicator */
function StepProgressBar({
  currentStep,
  onStepClick,
  onClose,
  styleControls,
}: {
  currentStep: Step
  onStepClick: (step: Step) => void
  onClose: () => void
  styleControls?: React.ReactNode
}) {
  const currentIndex = STEP_ORDER.findIndex((s) => s.id === currentStep)

  return (
    <div className="h-12 border-b bg-background flex items-center px-4 shrink-0 z-10 gap-3">
      {/* Logo */}
      <div className="flex items-center gap-2 shrink-0">
        <img src="/logo.png" alt="AutoForge" className="h-7 w-7 rounded-full" />
        <span className="font-semibold text-sm hidden sm:inline">AutoForge</span>
      </div>

      {/* Step progress indicator */}
      <div className="flex items-center gap-0 shrink-0">
        {STEP_ORDER.map((stepDef, idx) => {
          const isCompleted = idx < currentIndex
          const isActive = idx === currentIndex
          const isClickable = isCompleted

          return (
            <div key={stepDef.id} className="flex items-center">
              {idx > 0 && (
                <div
                  className={`w-6 h-0.5 transition-colors ${
                    idx <= currentIndex ? 'bg-primary' : 'bg-border'
                  }`}
                />
              )}
              <button
                type="button"
                disabled={!isClickable}
                onClick={() => isClickable && onStepClick(stepDef.id)}
                className={`flex flex-col items-center gap-0.5 group ${
                  isClickable ? 'cursor-pointer' : 'cursor-default'
                }`}
                title={isClickable ? `Go back to ${stepDef.label}` : stepDef.label}
              >
                <div
                  className={`flex items-center justify-center rounded-full transition-all ${
                    isActive
                      ? 'w-6 h-6 bg-primary text-primary-foreground ring-2 ring-primary/30'
                      : isCompleted
                        ? 'w-5 h-5 bg-primary text-primary-foreground group-hover:ring-2 group-hover:ring-primary/20'
                        : 'w-5 h-5 border-2 border-muted-foreground/30 text-muted-foreground/40'
                  }`}
                >
                  {isCompleted ? (
                    <Check size={10} strokeWidth={3} />
                  ) : (
                    <span className={`text-[9px] font-bold`}>
                      {idx + 1}
                    </span>
                  )}
                </div>
                <span
                  className={`text-[9px] font-medium leading-none whitespace-nowrap ${
                    isActive
                      ? 'text-primary'
                      : isCompleted
                        ? 'text-foreground/70'
                        : 'text-muted-foreground/50'
                  }`}
                >
                  {stepDef.label}
                </span>
              </button>
            </div>
          )
        })}
      </div>

      {/* Style step controls (injected from parent) */}
      {styleControls && (
        <div className="flex-1 flex items-center min-w-0">
          {styleControls}
        </div>
      )}

      {/* Spacer when no style controls */}
      {!styleControls && <div className="flex-1" />}

      {/* Close button */}
      <button
        type="button"
        onClick={onClose}
        className="shrink-0 p-1.5 rounded-md hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
        title="Close"
      >
        <X size={18} />
      </button>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

interface NewProjectModalProps {
  isOpen: boolean
  onClose: () => void
  onProjectCreated: (projectName: string) => void
  onStepChange?: (step: Step) => void
}

export function NewProjectModal({
  isOpen,
  onClose,
  onProjectCreated,
  onStepChange,
}: NewProjectModalProps) {
  const [step, setStep] = useState<Step>('name')
  const [projectName, setProjectName] = useState('')
  const [projectPath, setProjectPath] = useState<string | null>(null)
  const [boilerplateId, setBoilerplateId] = useState<string | null>(null)
  const [styleId, setStyleId] = useState<string | null>(null)
  const [_specMethod, setSpecMethod] = useState<SpecMethod | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [initializerStatus, setInitializerStatus] = useState<InitializerStatus>('idle')
  const [initializerError, setInitializerError] = useState<string | null>(null)
  const [yoloModeSelected, setYoloModeSelected] = useState(false)

  // Style picker state
  const [styleCategory, setStyleCategory] = useState<StyleCategory>('all')
  const [selectedAudience, setSelectedAudience] = useState<string>('')
  const [selectedVibe, setSelectedVibe] = useState<string>('')
  const [selectedAge, setSelectedAge] = useState<string>('')
  const [showRecommender, setShowRecommender] = useState(false)
  const [selectedModifiers, setSelectedModifiers] = useState<string[]>([])
  const [appDescription, setAppDescription] = useState('')
  const [customColors, setCustomColors] = useState<Record<string, string>>({})
  const [selectedPaletteId, setSelectedPaletteId] = useState<string | null>(null)

  // Style view toggle: browse (card grid) vs preview (sidebar + full render)
  const [styleView, setStyleView] = useState<StyleView>('browse')
  const [previewPage, setPreviewPage] = useState<PreviewPage>('landing')
  const [previewViewMode, setPreviewViewMode] = useState<'quad' | 'single'>('quad')

  // Accent style state
  const [accentStyleId, setAccentStyleId] = useState<string | null>(null)

  // Quad view dynamic scaling
  const QUAD_INTERNAL_W = 1280
  const QUAD_INTERNAL_H = 800
  const quadGridRef = useRef<HTMLDivElement>(null)
  const [quadScale, setQuadScale] = useState(0.4)

  useEffect(() => {
    if (styleView !== 'preview' || previewViewMode !== 'quad' || !quadGridRef.current) return
    const el = quadGridRef.current
    const update = () => {
      const { clientWidth, clientHeight } = el
      if (clientWidth === 0 || clientHeight === 0) return
      const cellW = clientWidth / 2
      const cellH = clientHeight / 2
      const scale = Math.min(cellW / QUAD_INTERNAL_W, cellH / QUAD_INTERNAL_H)
      setQuadScale(Math.max(0.1, Math.min(1, scale)))
    }
    update() // Immediate first calculation
    const observer = new ResizeObserver(() => update())
    observer.observe(el)
    return () => observer.disconnect()
  }, [styleView, previewViewMode])

  // Screenshot extractor state
  const [stylePickerTab, setStylePickerTab] = useState<'browse' | 'describe' | 'screenshot'>('browse')
  const [screenshotExtracting, setScreenshotExtracting] = useState(false)
  const [extractionResult, setExtractionResult] = useState<StyleExtractionResult | null>(null)

  // Suppress unused variable warning - specMethod may be used in future
  void _specMethod

  const createProject = useCreateProject()
  const { data: boilerplateCategories, isLoading: boilerplatesLoading } = useBoilerplates()
  const { data: styles, isLoading: stylesLoading } = useStyles(true)
  const { data: profiles } = useStyleProfiles()
  const { data: recommendations } = useStyleRecommendations(
    selectedAudience || undefined,
    selectedVibe || undefined,
    selectedAge || undefined,
  )
  const { data: modifiers } = useStyleModifiers()
  const descriptionRec = useDescriptionRecommendation()
  const { data: accentStyles } = useAccentCompatibility(styleId)
  const extractScreenshot = useExtractStyleFromScreenshot()

  // Filtered styles by category
  const filteredStyles = useMemo(() => {
    if (!styles) return []
    if (styleCategory === 'all') return styles
    return styles.filter((s: StyleOption) => s.category === styleCategory)
  }, [styles, styleCategory])

  // Get recommended style IDs for highlighting
  const recommendedIds = useMemo(() => {
    if (!recommendations || recommendations.length === 0) return new Set<string>()
    return new Set(recommendations.slice(0, 3).map((r) => r.style_id))
  }, [recommendations])

  const handleScreenshotUpload = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setScreenshotExtracting(true)
    setExtractionResult(null)

    const reader = new FileReader()
    reader.onload = async () => {
      const base64 = (reader.result as string).split(',')[1]
      try {
        const result = await extractScreenshot.mutateAsync(base64)
        setExtractionResult(result)
        // Auto-select the detected primary style
        if (result.identified_style.primary) {
          setStyleId(result.identified_style.primary)
          if (result.identified_style.accent) {
            setAccentStyleId(result.identified_style.accent)
          }
        }
      } catch {
        // Error handled by mutation state
      } finally {
        setScreenshotExtracting(false)
      }
    }
    reader.readAsDataURL(file)
  }, [extractScreenshot])

  // Wrapper to notify parent of step changes
  const changeStep = (newStep: Step) => {
    setStep(newStep)
    onStepChange?.(newStep)
  }

  if (!isOpen) return null

  const handleNameSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = projectName.trim()

    if (!trimmed) {
      setError('Please enter a project name')
      return
    }

    if (!/^[a-zA-Z0-9_-]+$/.test(trimmed)) {
      setError('Project name can only contain letters, numbers, hyphens, and underscores')
      return
    }

    setError(null)
    changeStep('folder')
  }

  const handleFolderSelect = (path: string) => {
    setProjectPath(path)
    changeStep('boilerplate')
  }

  const handleFolderCancel = () => {
    changeStep('name')
  }

  /**
   * Handle selecting a boilerplate category card.
   * Categories with no available options are disabled (coming soon).
   * Categories with exactly one available option auto-select it.
   * Categories with multiple available options could expand inline (future).
   */
  const handleBoilerplateSelect = (category: BoilerplateCategory) => {
    const availableOptions = category.options.filter((opt) => opt.available)

    // No available options - card should not be clickable
    if (availableOptions.length === 0) return

    if (availableOptions.length === 1) {
      // Single available option - select it directly
      setBoilerplateId(availableOptions[0].id)
      changeStep('style')
    } else {
      // Multiple options - for now, select the first one.
      // Future: expand inline to show sub-options.
      setBoilerplateId(availableOptions[0].id)
      changeStep('style')
    }
  }

  const handleStyleSelect = (id: string) => {
    if (id !== styleId) setCustomColors({}) // Reset colors when changing style
    setStyleId(id)
    // Don't advance - show modifier section below the style grid
  }

  const handleStyleConfirm = () => {
    changeStep('method')
  }

  const handleStyleSkip = () => {
    setStyleId(null)
    changeStep('method')
  }

  const handleMethodSelect = async (method: SpecMethod) => {
    setSpecMethod(method)

    if (!projectPath) {
      setError('Please select a project folder first')
      changeStep('folder')
      return
    }

    if (method === 'manual') {
      // Create project immediately with manual method
      try {
        const project = await createProject.mutateAsync({
          name: projectName.trim(),
          path: projectPath,
          specMethod: 'manual',
          boilerplateId,
          styleId,
          modifierIds: selectedModifiers,
          customColors: Object.keys(customColors).length > 0 ? customColors : undefined,
          accentStyle: accentStyleId,
          paletteId: selectedPaletteId,
        })
        changeStep('complete')
        setTimeout(() => {
          onProjectCreated(project.name)
          handleClose()
        }, 1500)
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Failed to create project')
      }
    } else {
      // Create project then show chat
      try {
        await createProject.mutateAsync({
          name: projectName.trim(),
          path: projectPath,
          specMethod: 'claude',
          boilerplateId,
          styleId,
          modifierIds: selectedModifiers,
          customColors: Object.keys(customColors).length > 0 ? customColors : undefined,
          accentStyle: accentStyleId,
          paletteId: selectedPaletteId,
        })
        changeStep('chat')
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Failed to create project')
      }
    }
  }

  const handleSpecComplete = async (_specPath: string, yoloMode: boolean = false) => {
    // Save yoloMode for retry
    setYoloModeSelected(yoloMode)
    // Auto-start the initializer agent
    setInitializerStatus('starting')
    try {
      // Use default concurrency of 3 to match AgentControl.tsx default
      await startAgent(projectName.trim(), {
        yoloMode,
        maxConcurrency: 3,
      })
      // Success - navigate to project
      changeStep('complete')
      setTimeout(() => {
        onProjectCreated(projectName.trim())
        handleClose()
      }, 1500)
    } catch (err) {
      setInitializerStatus('error')
      setInitializerError(err instanceof Error ? err.message : 'Failed to start agent')
    }
  }

  const handleRetryInitializer = () => {
    setInitializerError(null)
    setInitializerStatus('idle')
    handleSpecComplete('', yoloModeSelected)
  }

  const handleChatCancel = () => {
    // Go back to method selection but keep the project
    changeStep('method')
    setSpecMethod(null)
  }

  const handleExitToProject = () => {
    // Exit chat and go directly to project - user can start agent manually
    onProjectCreated(projectName.trim())
    handleClose()
  }

  const handleClose = () => {
    changeStep('name')
    setProjectName('')
    setProjectPath(null)
    setBoilerplateId(null)
    setStyleId(null)
    setSpecMethod(null)
    setError(null)
    setInitializerStatus('idle')
    setInitializerError(null)
    setYoloModeSelected(false)
    setStyleCategory('all')
    setSelectedAudience('')
    setSelectedVibe('')
    setSelectedAge('')
    setShowRecommender(false)
    setSelectedModifiers([])
    setAppDescription('')
    setCustomColors({})
    setAccentStyleId(null)
    setStyleView('browse')
    setPreviewPage('landing')
    setStylePickerTab('browse')
    setScreenshotExtracting(false)
    setExtractionResult(null)
    onClose()
  }

  const handleBack = () => {
    if (step === 'folder') {
      changeStep('name')
      setProjectPath(null)
    } else if (step === 'boilerplate') {
      changeStep('folder')
      setBoilerplateId(null)
    } else if (step === 'style') {
      changeStep('boilerplate')
      setStyleId(null)
      setSelectedModifiers([])
      setCustomColors({})
      setAccentStyleId(null)
      setExtractionResult(null)
      setStylePickerTab('browse')
      setStyleView('browse')
      setPreviewPage('landing')
    } else if (step === 'method') {
      changeStep('style')
      setSpecMethod(null)
    }
  }

  /**
   * Handle clicking a completed step in the progress bar to navigate back.
   * We need to reset intermediate state just like handleBack does, but
   * potentially skip multiple steps.
   */
  const handleStepClick = (targetStep: Step) => {
    const targetIndex = STEP_ORDER.findIndex((s) => s.id === targetStep)
    const currentIndex = STEP_ORDER.findIndex((s) => s.id === step)
    if (targetIndex >= currentIndex) return // Only navigate backwards

    // Reset state for steps we are skipping over
    if (targetIndex < 4) {
      // Going before style: reset style state
      setStyleId(null)
      setSelectedModifiers([])
      setCustomColors({})
      setAccentStyleId(null)
      setExtractionResult(null)
      setStylePickerTab('browse')
      setStyleView('browse')
      setPreviewPage('landing')
    }
    if (targetIndex < 3) {
      // Going before boilerplate: reset boilerplate
      setBoilerplateId(null)
    }
    if (targetIndex < 2) {
      // Going before folder: reset folder
      setProjectPath(null)
    }
    if (targetIndex < 1) {
      // Going to name: reset project path
      setProjectPath(null)
    }

    setSpecMethod(null)
    setError(null)
    changeStep(targetStep)
  }

  // =========================================================================
  // Chat step - full-screen, no nav bar (SpecCreationChat has its own header)
  // =========================================================================
  if (step === 'chat') {
    return createPortal(
      <div className="fixed inset-0 z-50 bg-background flex flex-col">
        <SpecCreationChat
          projectName={projectName.trim()}
          onComplete={handleSpecComplete}
          onCancel={handleChatCancel}
          onExitToProject={handleExitToProject}
          initializerStatus={initializerStatus}
          initializerError={initializerError}
          onRetryInitializer={handleRetryInitializer}
        />
      </div>,
      document.body
    )
  }

  // =========================================================================
  // All other steps: full-screen portal with nav bar + step progress
  // =========================================================================
  return createPortal(
    <div className="fixed inset-0 z-50 bg-background flex flex-col h-screen overflow-hidden">
      {/* Top Navigation Bar with Step Progress */}
      <StepProgressBar
        currentStep={step}
        onStepClick={handleStepClick}
        onClose={handleClose}
        styleControls={step === 'style' ? (
          <>
            {/* Back button */}
            <Button variant="ghost" size="sm" className="h-7 text-xs shrink-0" onClick={handleBack}>
              <ArrowLeft size={12} />
              Back
            </Button>

            {/* Browse / Preview toggle */}
            <div className="flex bg-muted rounded-lg p-0.5 shrink-0 ml-2">
              <button
                onClick={() => setStyleView('browse')}
                className={`px-2.5 py-0.5 text-[11px] font-medium rounded-md transition-colors ${
                  styleView === 'browse' ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground'
                }`}
              >
                Browse
              </button>
              <button
                onClick={() => setStyleView('preview')}
                className={`px-2.5 py-0.5 text-[11px] font-medium rounded-md transition-colors ${
                  styleView === 'preview' ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground'
                }`}
              >
                Preview
              </button>
            </div>

            {/* Category filter tabs (browse view only) */}
            {styleView === 'browse' && (
              <div className="flex gap-0.5 ml-2 shrink-0">
                {(['all', 'core', 'vibe'] as StyleCategory[]).map((cat) => (
                  <Button
                    key={cat}
                    variant={styleCategory === cat ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setStyleCategory(cat)}
                    className="text-[11px] px-2 h-6"
                  >
                    {cat === 'all' ? 'All' : cat === 'core' ? 'Core' : 'Vibe'}
                  </Button>
                ))}
              </div>
            )}

            {/* Selected style indicator (preview view) */}
            {styleView === 'preview' && styleId && styles && (
              <span className="ml-2 text-xs text-muted-foreground shrink-0">
                Previewing: <span className="font-medium text-foreground">{styles.find((s: StyleOption) => s.id === styleId)?.name}</span>
              </span>
            )}

            {/* Center spacer */}
            <div className="flex-1" />

            {/* AI Recommendation button */}
            {styleView === 'browse' && (
              <Button
                variant={showRecommender ? 'default' : 'outline'}
                size="sm"
                onClick={() => setShowRecommender(!showRecommender)}
                className="h-6 text-[11px] shrink-0"
              >
                <Sparkles size={11} />
                AI Recommendation
              </Button>
            )}

            {/* Style Picker Mode Tabs (browse view only) */}
            {styleView === 'browse' && (
              <div className="flex border border-border rounded-md overflow-hidden shrink-0 ml-2">
                {(['browse', 'describe', 'screenshot'] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setStylePickerTab(tab)}
                    className={`px-2 py-0.5 text-[10px] font-medium transition-colors ${
                      stylePickerTab === tab
                        ? 'bg-primary text-primary-foreground'
                        : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                    }`}
                  >
                    {tab === 'browse' ? 'Browse' : tab === 'describe' ? 'Describe' : 'Screenshot'}
                  </button>
                ))}
              </div>
            )}

            {/* Continue / Skip */}
            <div className="flex gap-1 ml-2 shrink-0">
              {!styleId && (
                <Button variant="outline" size="sm" className="h-7 text-xs" onClick={handleStyleSkip}>
                  Skip
                  <ArrowRight size={12} />
                </Button>
              )}
              {styleId && (
                <Button size="sm" className="h-7 text-xs" onClick={handleStyleConfirm}>
                  Continue
                  <ArrowRight size={12} />
                </Button>
              )}
            </div>
          </>
        ) : undefined}
      />

      {/* Step Content Area - uses remaining viewport height */}
      <div className="flex-1 min-h-0 overflow-hidden flex flex-col">
        {/* ---------------------------------------------------------------- */}
        {/* Step 1: Project Name                                             */}
        {/* ---------------------------------------------------------------- */}
        {step === 'name' && (
          <div className="flex-1 flex items-center justify-center p-6">
            <div className="w-full max-w-md">
              <div className="mb-6">
                <h2 className="text-2xl font-semibold mb-1">Create New Project</h2>
                <p className="text-sm text-muted-foreground">
                  Give your project a name to get started.
                </p>
              </div>

              <form onSubmit={handleNameSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="project-name">Project Name</Label>
                  <Input
                    id="project-name"
                    type="text"
                    value={projectName}
                    onChange={(e) => setProjectName(e.target.value)}
                    placeholder="my-awesome-app"
                    pattern="^[a-zA-Z0-9_-]+$"
                    autoFocus
                  />
                  <p className="text-sm text-muted-foreground">
                    Use letters, numbers, hyphens, and underscores only.
                  </p>
                </div>

                {error && (
                  <Alert variant="destructive">
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                <div className="flex justify-end">
                  <Button type="submit" disabled={!projectName.trim()}>
                    Next
                    <ArrowRight size={16} />
                  </Button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* ---------------------------------------------------------------- */}
        {/* Step 2: Folder Selection                                         */}
        {/* ---------------------------------------------------------------- */}
        {step === 'folder' && (
          <div className="flex-1 flex flex-col min-h-0">
            {/* Header */}
            <div className="px-6 py-4 border-b shrink-0">
              <div className="flex items-center gap-3">
                <Folder size={24} className="text-primary" />
                <div>
                  <h2 className="text-lg font-semibold">Select Project Location</h2>
                  <p className="text-sm text-muted-foreground">
                    Select the folder to use for project <span className="font-semibold font-mono">{projectName}</span>. Create a new folder or choose an existing one.
                  </p>
                </div>
              </div>
            </div>

            {/* Folder Browser - takes remaining space */}
            <div className="flex-1 overflow-hidden">
              <FolderBrowser
                onSelect={handleFolderSelect}
                onCancel={handleFolderCancel}
              />
            </div>
          </div>
        )}

        {/* ---------------------------------------------------------------- */}
        {/* Step 3: Boilerplate Selection                                    */}
        {/* ---------------------------------------------------------------- */}
        {step === 'boilerplate' && (
          <div className="flex-1 flex items-center justify-center p-6">
            <div className="w-full max-w-xl space-y-4">
              <div className="mb-2">
                <h2 className="text-2xl font-semibold mb-1">Choose a Boilerplate</h2>
                <p className="text-sm text-muted-foreground">
                  Pick a starting point for your project.
                </p>
              </div>

              {boilerplatesLoading && (
                <div className="flex items-center justify-center gap-2 py-8 text-muted-foreground">
                  <Loader2 size={16} className="animate-spin" />
                  <span>Loading boilerplates...</span>
                </div>
              )}

              {!boilerplatesLoading && boilerplateCategories && (
                <div className="space-y-3">
                  {boilerplateCategories.map((category) => {
                    const availableOptions = category.options.filter((opt) => opt.available)
                    const isDisabled = availableOptions.length === 0
                    const Icon = CATEGORY_ICONS[category.category] ?? Zap

                    return (
                      <Card
                        key={category.category}
                        className={
                          isDisabled
                            ? 'opacity-60 cursor-not-allowed'
                            : 'cursor-pointer hover:border-primary transition-colors'
                        }
                        onClick={() => !isDisabled && handleBoilerplateSelect(category)}
                      >
                        <CardContent className="p-4">
                          <div className="flex items-start gap-4">
                            <div className="p-2 bg-primary/10 rounded-lg">
                              <Icon size={24} className="text-primary" />
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <span className="font-semibold">{category.label}</span>
                                {isDisabled && (
                                  <Badge variant="secondary">Coming Soon</Badge>
                                )}
                              </div>

                              {/* Show available options with tech summaries */}
                              {availableOptions.length > 0 && (
                                <div className="mt-1 space-y-1">
                                  {availableOptions.map((option) => (
                                    <div key={option.id}>
                                      <p className="text-sm text-muted-foreground">
                                        {option.tech_summary}
                                      </p>
                                    </div>
                                  ))}
                                </div>
                              )}

                              {/* For disabled categories, show a brief explanation */}
                              {isDisabled && category.options.length > 0 && (
                                <p className="text-sm text-muted-foreground mt-1">
                                  {category.options[0].description}
                                </p>
                              )}
                              {isDisabled && category.options.length === 0 && (
                                <p className="text-sm text-muted-foreground mt-1">
                                  More options coming soon.
                                </p>
                              )}
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    )
                  })}
                </div>
              )}

              {/* Show pre_built badges for the selected boilerplate */}
              {boilerplateId && boilerplateCategories && (() => {
                const selectedOption = boilerplateCategories
                  .flatMap((c) => c.options)
                  .find((opt) => opt.id === boilerplateId)
                if (!selectedOption || selectedOption.pre_built.length === 0) return null
                return (
                  <div className="space-y-2">
                    <p className="text-sm font-medium">Included out of the box:</p>
                    <div className="flex flex-wrap gap-1.5">
                      {selectedOption.pre_built.map((item) => (
                        <Badge key={item} variant="secondary">{item}</Badge>
                      ))}
                    </div>
                  </div>
                )
              })()}

              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <div className="flex justify-start">
                <Button variant="ghost" onClick={handleBack}>
                  <ArrowLeft size={16} />
                  Back
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* ---------------------------------------------------------------- */}
        {/* Step 4: Design Style Selection (full-screen layout)              */}
        {/* ---------------------------------------------------------------- */}
        {step === 'style' && (
          <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
            {/* ==================================================== */}
            {/* BROWSE VIEW                                            */}
            {/* ==================================================== */}
            {styleView === 'browse' && (
              <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
                {/* AI Recommender Panel (collapsible, compact) */}
                {(stylePickerTab === 'browse' || stylePickerTab === 'describe') && showRecommender && profiles && (
                  <div className="shrink-0 px-4 py-2 border-b bg-primary/5">
                    <div className="flex gap-4 items-start">
                      {/* Description input */}
                      <div className="flex-1 min-w-0">
                        <div className="flex gap-2 items-end">
                          <div className="flex-1">
                            <Label className="text-[11px]">Describe your app (optional)</Label>
                            <textarea
                              value={appDescription}
                              onChange={(e) => setAppDescription(e.target.value)}
                              placeholder="e.g., A sugar tracking app for diabetics aged 50-80..."
                              className="w-full text-xs rounded-md border border-border bg-background px-2 py-1.5 resize-none h-10 mt-0.5"
                            />
                          </div>
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={appDescription.length < 10 || descriptionRec.isPending}
                            onClick={() => {
                              descriptionRec.mutate(appDescription, {
                                onSuccess: (data) => {
                                  if (data.detected_signals.audience) setSelectedAudience(data.detected_signals.audience)
                                  if (data.detected_signals.vibe) setSelectedVibe(data.detected_signals.vibe)
                                  if (data.detected_signals.age_group) setSelectedAge(data.detected_signals.age_group)
                                }
                              })
                            }}
                            className="h-7 text-xs mb-0.5"
                          >
                            {descriptionRec.isPending ? (
                              <Loader2 size={12} className="animate-spin" />
                            ) : (
                              <Sparkles size={12} />
                            )}
                            Analyze
                          </Button>
                        </div>
                        {descriptionRec.data && (
                          <p className="text-[10px] text-muted-foreground mt-0.5">
                            Detected: {[
                              descriptionRec.data.detected_signals.audience && `Audience: ${descriptionRec.data.detected_signals.audience}`,
                              descriptionRec.data.detected_signals.vibe && `Vibe: ${descriptionRec.data.detected_signals.vibe}`,
                              descriptionRec.data.detected_signals.age_group && `Age: ${descriptionRec.data.detected_signals.age_group}`,
                            ].filter(Boolean).join(' | ')}
                          </p>
                        )}
                      </div>

                      {/* Manual selectors */}
                      <div className="flex gap-2 shrink-0">
                        <div>
                          <Label className="text-[11px]">Audience</Label>
                          <select
                            value={selectedAudience}
                            onChange={(e) => setSelectedAudience(e.target.value)}
                            className="w-full mt-0.5 text-xs rounded-md border border-border bg-background px-2 py-1.5"
                          >
                            <option value="">Any</option>
                            {Object.entries(profiles.audiences).map(([key, val]) => (
                              <option key={key} value={key}>{val.label}</option>
                            ))}
                          </select>
                        </div>
                        <div>
                          <Label className="text-[11px]">Vibe</Label>
                          <select
                            value={selectedVibe}
                            onChange={(e) => setSelectedVibe(e.target.value)}
                            className="w-full mt-0.5 text-xs rounded-md border border-border bg-background px-2 py-1.5"
                          >
                            <option value="">Any</option>
                            {Object.entries(profiles.vibes).map(([key, val]) => (
                              <option key={key} value={key}>{val.label}</option>
                            ))}
                          </select>
                        </div>
                        <div>
                          <Label className="text-[11px]">Age Group</Label>
                          <select
                            value={selectedAge}
                            onChange={(e) => setSelectedAge(e.target.value)}
                            className="w-full mt-0.5 text-xs rounded-md border border-border bg-background px-2 py-1.5"
                          >
                            <option value="">Any</option>
                            {Object.entries(profiles.age_groups).map(([key, val]) => (
                              <option key={key} value={key}>{val.label}</option>
                            ))}
                          </select>
                        </div>
                      </div>
                    </div>
                    {recommendations && recommendations.length > 0 && (
                      <p className="text-[10px] text-muted-foreground mt-1">
                        Top picks highlighted below. Best match: <span className="font-semibold text-primary">{styles?.find((s: StyleOption) => s.id === recommendations[0].style_id)?.name}</span>
                      </p>
                    )}
                  </div>
                )}

                {/* Screenshot Extraction Tab */}
                {stylePickerTab === 'screenshot' && (
                  <div className="shrink-0 px-4 py-3 border-b">
                    <div className="flex items-start gap-4 max-w-2xl mx-auto">
                      <label
                        className={`flex flex-col items-center gap-2 p-4 border-2 border-dashed rounded-xl cursor-pointer transition-colors flex-1 ${
                          screenshotExtracting
                            ? 'border-primary/50 bg-primary/5'
                            : 'border-border hover:border-primary/50 hover:bg-muted/50'
                        }`}
                      >
                        <input
                          type="file"
                          accept="image/png,image/jpeg,image/webp"
                          className="hidden"
                          onChange={handleScreenshotUpload}
                          disabled={screenshotExtracting}
                        />
                        {screenshotExtracting ? (
                          <>
                            <Loader2 size={24} className="text-primary animate-spin" />
                            <span className="text-xs text-muted-foreground">Analyzing...</span>
                          </>
                        ) : (
                          <>
                            <Upload size={24} className="text-muted-foreground" />
                            <div className="text-center">
                              <p className="text-xs font-medium">Drop an image or click to upload</p>
                              <p className="text-[10px] text-muted-foreground">.png, .jpg, or .webp</p>
                            </div>
                          </>
                        )}
                      </label>

                      {/* Extraction Results */}
                      {extractionResult && (
                        <Card className="flex-1">
                          <CardContent className="p-3 space-y-2">
                            <div className="flex items-center gap-2">
                              <ImageIcon size={14} className="text-primary" />
                              <span className="font-medium text-xs">Style Analysis</span>
                            </div>

                            {extractionResult.identified_style.primary && (
                              <div className="space-y-0.5">
                                <p className="text-xs">
                                  <span className="text-muted-foreground">Detected: </span>
                                  <span className="font-semibold">
                                    {styles?.find(s => s.id === extractionResult.identified_style.primary)?.name || extractionResult.identified_style.primary}
                                  </span>
                                  {extractionResult.identified_style.accent && (
                                    <span className="text-muted-foreground">
                                      {' + '}
                                      <span className="font-medium">
                                        {styles?.find(s => s.id === extractionResult.identified_style.accent)?.name || extractionResult.identified_style.accent}
                                      </span>
                                      {' accent'}
                                    </span>
                                  )}
                                </p>
                                <p className="text-[10px] text-muted-foreground">
                                  Confidence: {extractionResult.identified_style.primary_confidence}
                                </p>
                              </div>
                            )}

                            {/* Extracted color palette preview */}
                            {extractionResult.tailwind_config && !!(extractionResult.tailwind_config as Record<string, unknown>).colors && (
                              <div className="space-y-0.5">
                                <p className="text-[10px] text-muted-foreground">Extracted palette:</p>
                                <div className="flex gap-1">
                                  {(() => {
                                    const colors = (extractionResult.tailwind_config as Record<string, Record<string, Record<string, string>>>).colors || {}
                                    const swatches: string[] = []
                                    if (colors.brand?.DEFAULT) swatches.push(colors.brand.DEFAULT)
                                    if (colors.surface?.canvas) swatches.push(colors.surface.canvas)
                                    if (colors.surface?.base) swatches.push(colors.surface.base)
                                    if (colors.text?.primary) swatches.push(colors.text.primary)
                                    return swatches.slice(0, 6).map((c, i) => (
                                      <div
                                        key={i}
                                        className="h-5 w-6 rounded border border-black/10"
                                        style={{ backgroundColor: c }}
                                        title={c}
                                      />
                                    ))
                                  })()}
                                </div>
                              </div>
                            )}

                            <div className="flex gap-2">
                              <Button size="sm" className="h-7 text-xs" onClick={() => {
                                if (extractionResult.identified_style.primary) {
                                  setStyleId(extractionResult.identified_style.primary)
                                  if (extractionResult.identified_style.accent) {
                                    setAccentStyleId(extractionResult.identified_style.accent)
                                  }
                                  setStylePickerTab('browse')
                                }
                              }}>
                                Use This Style
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                className="h-7 text-xs"
                                onClick={() => {
                                  setExtractionResult(null)
                                }}
                              >
                                Try Another
                              </Button>
                            </div>
                          </CardContent>
                        </Card>
                      )}

                      {extractScreenshot.isError && (
                        <Alert variant="destructive" className="flex-1">
                          <AlertDescription className="text-xs">
                            Failed to analyze screenshot. Make sure you have a valid ANTHROPIC_API_KEY set.
                          </AlertDescription>
                        </Alert>
                      )}
                    </div>
                  </div>
                )}

                {stylePickerTab !== 'screenshot' && (
                  <div className="flex-1 min-h-0 flex overflow-hidden">
                    {/* Left panel: modifiers, accent, colors (always visible) */}
                    <div className="w-[240px] shrink-0 border-r overflow-y-auto p-3 space-y-3">
                      {/* Modifier Selection */}
                      {modifiers && modifiers.length > 0 && (
                        <div className="space-y-1.5">
                          <div className="flex items-center gap-2">
                            <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Modifiers</span>
                            <Badge variant="secondary" className="text-[9px] h-4">Optional</Badge>
                          </div>
                          <div className="space-y-1">
                            {modifiers.map((mod) => {
                              const isActive = selectedModifiers.includes(mod.id)
                              return (
                                <button
                                  key={mod.id}
                                  onClick={() => {
                                    setSelectedModifiers(prev =>
                                      isActive
                                        ? prev.filter(id => id !== mod.id)
                                        : prev.length < 3
                                          ? [...prev, mod.id]
                                          : prev
                                    )
                                  }}
                                  className={`w-full text-left p-1.5 rounded-md border transition-colors ${
                                    isActive
                                      ? 'border-primary bg-primary/10'
                                      : 'border-border hover:border-primary/50'
                                  }`}
                                >
                                  <div className="flex items-center gap-1.5">
                                    {isActive && <Check size={10} className="text-primary" />}
                                    <span className="text-[11px] font-medium">{mod.name}</span>
                                  </div>
                                  <p className="text-[10px] text-muted-foreground mt-0.5 leading-snug">
                                    {mod.description}
                                  </p>
                                </button>
                              )
                            })}
                          </div>
                          {selectedModifiers.length >= 3 && (
                            <p className="text-[10px] text-muted-foreground">Maximum 3 modifiers.</p>
                          )}
                        </div>
                      )}

                      {/* Accent Style Picker */}
                      {accentStyles && accentStyles.length > 0 && (
                        <div className="space-y-1.5">
                          <div className="flex items-center gap-2">
                            <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Accent Style</span>
                            <Badge variant="secondary" className="text-[9px] h-4">Optional</Badge>
                          </div>
                          <div className="space-y-1">
                            {accentStyles.map((accent: AccentStyleOption) => {
                              const isActive = accentStyleId === accent.id
                              return (
                                <button
                                  key={accent.id}
                                  onClick={() => setAccentStyleId(isActive ? null : accent.id)}
                                  className={`w-full text-left p-1.5 rounded-md border transition-colors ${
                                    isActive
                                      ? 'border-primary bg-primary/10'
                                      : 'border-border hover:border-primary/50'
                                  }`}
                                >
                                  <div className="flex items-center gap-1.5">
                                    {isActive && <Check size={10} className="text-primary" />}
                                    <span className="text-[11px] font-medium">{accent.name}</span>
                                  </div>
                                </button>
                              )
                            })}
                          </div>
                          {accentStyleId && (
                            <p className="text-[10px] text-muted-foreground">
                              Accent controls buttons and inputs only.
                            </p>
                          )}
                        </div>
                      )}

                      {/* No style selected hint for accent */}
                      {!styleId && (!accentStyles || accentStyles.length === 0) && (
                        <div className="space-y-1.5">
                          <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Accent Style</span>
                          <p className="text-[10px] text-muted-foreground">Select a style to see compatible accents.</p>
                        </div>
                      )}

                      {/* Color Customization */}
                      {(() => {
                        const selected = styles?.find((s: StyleOption) => s.id === styleId)
                        if (!selected?.style_guide) return null
                        return (
                          <ColorCustomizer
                            styleGuide={selected.style_guide}
                            customColors={customColors}
                            onChange={setCustomColors}
                            selectedPaletteId={selectedPaletteId}
                            onPaletteSelect={setSelectedPaletteId}
                          />
                        )
                      })()}
                    </div>

                    {/* Style Grid */}
                    <div className="flex-1 min-w-0 overflow-y-auto p-3">
                      {stylesLoading && (
                        <div className="flex items-center justify-center gap-2 py-8 text-muted-foreground">
                          <Loader2 size={16} className="animate-spin" />
                          <span>Loading styles...</span>
                        </div>
                      )}

                      {!stylesLoading && filteredStyles.length > 0 && (
                        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-2">
                          {filteredStyles.map((style: StyleOption) => {
                            const swatches = STYLE_SWATCHES[style.id] || ['#3B82F6', '#FFFFFF', '#111827', '#22C55E']
                            const isRecommended = recommendedIds.has(style.id)
                            const isTopPick = recommendations && recommendations.length > 0 && recommendations[0].style_id === style.id
                            const isSelected = styleId === style.id

                            return (
                              <Card
                                key={style.id}
                                className={`cursor-pointer transition-all hover:border-primary ${
                                  isRecommended ? 'border-primary/50 ring-1 ring-primary/20' : ''
                                } ${isTopPick ? 'ring-2 ring-primary/40' : ''} ${
                                  isSelected ? 'border-primary ring-2 ring-primary/30' : ''
                                }`}
                                onClick={() => handleStyleSelect(style.id)}
                              >
                                <CardContent className="p-2 flex flex-col gap-1.5">
                                  {/* Style info */}
                                  <div className="flex flex-col gap-0.5">
                                    {/* Color swatches + name row */}
                                    <div className="flex items-center gap-1.5">
                                      <div className="flex gap-0.5">
                                        {swatches.map((color, i) => (
                                          <div
                                            key={i}
                                            className="h-3 w-3 rounded-sm border border-black/10"
                                            style={{ backgroundColor: color }}
                                          />
                                        ))}
                                      </div>
                                      <span className="font-semibold text-xs leading-tight truncate">{style.name}</span>
                                      {isTopPick && (
                                        <Badge className="text-[8px] px-1 py-0 h-3.5">Best</Badge>
                                      )}
                                      {isRecommended && !isTopPick && (
                                        <Check size={10} className="text-primary shrink-0" />
                                      )}
                                      <Badge variant="outline" className="text-[8px] px-1 py-0 h-3.5 ml-auto capitalize shrink-0">
                                        {style.category}
                                      </Badge>
                                    </div>

                                    {/* Description - single line */}
                                    <p className="text-[10px] text-muted-foreground leading-snug line-clamp-1">
                                      {style.description}
                                    </p>

                                    {/* Best for */}
                                    <p className="text-[9px] text-muted-foreground/70 leading-snug line-clamp-1">
                                      <span className="font-medium text-muted-foreground/90">Best for:</span> {style.best_for}
                                    </p>
                                  </div>

                                  {/* UI Preview - full width below text */}
                                  {style.style_guide && (
                                    <div className="w-full">
                                      <StylePreview
                                        guide={style.style_guide}
                                        size="compact"
                                        styleName={style.name}
                                        modifiers={selectedModifiers.length > 0 ? selectedModifiers : undefined}
                                        accentGuide={accentStyleId
                                          ? styles?.find((s: StyleOption) => s.id === accentStyleId)?.style_guide
                                          : undefined}
                                      />
                                    </div>
                                  )}
                                </CardContent>
                              </Card>
                            )
                          })}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* ==================================================== */}
            {/* PREVIEW VIEW: sidebar + full render                    */}
            {/* ==================================================== */}
            {styleView === 'preview' && (
              <div className="flex-1 min-h-0 flex overflow-hidden">
                {/* Left sidebar - wider for full-screen */}
                <div className="w-[320px] shrink-0 border-r bg-muted/30 overflow-y-auto">
                  {/* Styles section */}
                  <div className="p-3 border-b">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">Styles</h4>
                    <div className="space-y-0.5">
                      {(styles || []).map((style: StyleOption) => {
                        const swatches = STYLE_SWATCHES[style.id] || ['#3B82F6', '#FFFFFF', '#111827']
                        const isActive = styleId === style.id
                        return (
                          <button
                            key={style.id}
                            onClick={() => handleStyleSelect(style.id)}
                            className={`w-full flex items-center gap-2 px-2.5 py-2 rounded-md text-left transition-colors ${
                              isActive
                                ? 'bg-primary/10 border-l-2 border-l-primary pl-2'
                                : 'hover:bg-muted border-l-2 border-l-transparent pl-2'
                            }`}
                          >
                            <div className="flex gap-0.5 shrink-0">
                              {swatches.slice(0, 3).map((color, i) => (
                                <div
                                  key={i}
                                  className="w-3 h-3 rounded-sm"
                                  style={{
                                    backgroundColor: color,
                                    border: '1px solid rgba(0,0,0,0.1)',
                                  }}
                                />
                              ))}
                            </div>
                            <span className={`text-sm truncate ${isActive ? 'font-medium text-foreground' : 'text-muted-foreground'}`}>
                              {style.name}
                            </span>
                          </button>
                        )
                      })}
                    </div>
                  </div>

                  {/* View mode + Page selector section */}
                  <div className="p-3 border-b">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">View</h4>
                    {/* Quad / Single toggle */}
                    <div className="flex bg-muted rounded-lg p-0.5 mb-2">
                      <button
                        onClick={() => setPreviewViewMode('quad')}
                        className={`flex-1 flex items-center justify-center gap-1 px-2 py-1 text-[11px] font-medium rounded-md transition-colors ${
                          previewViewMode === 'quad' ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground'
                        }`}
                      >
                        <Grid2x2 size={12} />
                        Quad
                      </button>
                      <button
                        onClick={() => setPreviewViewMode('single')}
                        className={`flex-1 flex items-center justify-center gap-1 px-2 py-1 text-[11px] font-medium rounded-md transition-colors ${
                          previewViewMode === 'single' ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground'
                        }`}
                      >
                        <Maximize2 size={12} />
                        Single
                      </button>
                    </div>
                    {/* Page selector - click goes to single view of that page */}
                    <div className="space-y-0.5">
                      {([
                        { id: 'landing' as PreviewPage, label: 'Landing' },
                        { id: 'dashboard' as PreviewPage, label: 'Dashboard' },
                        { id: 'settings' as PreviewPage, label: 'Settings' },
                        { id: 'feed' as PreviewPage, label: 'Feed' },
                      ]).map((page) => {
                        const isActive = previewViewMode === 'single' && previewPage === page.id
                        return (
                          <button
                            key={page.id}
                            onClick={() => {
                              setPreviewPage(page.id)
                              setPreviewViewMode('single')
                            }}
                            className={`w-full text-left px-2.5 py-1.5 rounded-md text-sm transition-colors ${
                              isActive
                                ? 'bg-primary/10 font-medium text-foreground'
                                : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                            }`}
                          >
                            {page.label}
                          </button>
                        )
                      })}
                    </div>
                  </div>

                  {/* Modifiers section */}
                  {modifiers && modifiers.length > 0 && (
                    <div className="p-3 border-b">
                      <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">Modifiers</h4>
                      <div className="space-y-1">
                        {modifiers.map((mod) => {
                          const isActive = selectedModifiers.includes(mod.id)
                          return (
                            <label
                              key={mod.id}
                              className="flex items-center gap-2 px-2 py-1.5 rounded-md cursor-pointer hover:bg-muted transition-colors"
                            >
                              <input
                                type="checkbox"
                                checked={isActive}
                                onChange={() => {
                                  setSelectedModifiers(prev =>
                                    isActive
                                      ? prev.filter(id => id !== mod.id)
                                      : prev.length < 3
                                        ? [...prev, mod.id]
                                        : prev
                                  )
                                }}
                                className="rounded border-border"
                              />
                              <span className={`text-sm ${isActive ? 'text-foreground font-medium' : 'text-muted-foreground'}`}>
                                {mod.name}
                              </span>
                            </label>
                          )
                        })}
                      </div>
                    </div>
                  )}

                  {/* Accent section */}
                  <div className="p-3">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">Accent</h4>
                    <div className="space-y-0.5">
                      <button
                        onClick={() => setAccentStyleId(null)}
                        className={`w-full text-left px-2.5 py-1.5 rounded-md text-sm transition-colors ${
                          !accentStyleId
                            ? 'bg-primary/10 font-medium text-foreground'
                            : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                        }`}
                      >
                        None
                      </button>
                      {(styles || [])
                        .filter((s: StyleOption) => s.id !== styleId && s.style_guide)
                        .map((accent: StyleOption) => {
                          const isActive = accentStyleId === accent.id
                          return (
                            <button
                              key={accent.id}
                              onClick={() => setAccentStyleId(isActive ? null : accent.id)}
                              className={`w-full text-left px-2.5 py-1.5 rounded-md text-sm transition-colors ${
                                isActive
                                  ? 'bg-primary/10 font-medium text-foreground'
                                  : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                              }`}
                            >
                              {accent.name}
                            </button>
                          )
                        })}
                    </div>
                  </div>
                </div>

                {/* Right: preview render area */}
                <div className="flex-1 min-h-0 bg-muted/10 overflow-hidden">
                  {styleId && (() => {
                    const previewStyle = styles?.find((s: StyleOption) => s.id === styleId)
                    if (!previewStyle?.style_guide) return (
                      <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
                        Select a style to preview
                      </div>
                    )
                    const guide = previewStyle.style_guide
                    const accentGuide = accentStyleId
                      ? styles?.find((s: StyleOption) => s.id === accentStyleId)?.style_guide
                      : undefined

                    if (previewViewMode === 'quad') {
                      const quadPages: { id: PreviewPage; label: string; top: string; left: string }[] = [
                        { id: 'landing', label: 'Landing', top: '0', left: '0' },
                        { id: 'dashboard', label: 'Dashboard', top: '0', left: '50%' },
                        { id: 'settings', label: 'Settings', top: '50%', left: '0' },
                        { id: 'feed', label: 'Feed', top: '50%', left: '50%' },
                      ]
                      return (
                        <div
                          ref={quadGridRef}
                          className="relative w-full h-full"
                        >
                          {quadPages.map((page) => (
                            <div
                              key={page.id}
                              className="absolute overflow-hidden cursor-pointer group"
                              style={{
                                top: page.top,
                                left: page.left,
                                width: '50%',
                                height: '50%',
                                borderRight: page.left === '0' ? '1px solid var(--color-border)' : undefined,
                                borderBottom: page.top === '0' ? '1px solid var(--color-border)' : undefined,
                              }}
                              onClick={() => {
                                setPreviewPage(page.id)
                                setPreviewViewMode('single')
                              }}
                            >
                              {/* Page label overlay */}
                              <div className="absolute top-1.5 left-1.5 z-10 px-1.5 py-0.5 rounded text-[9px] font-semibold bg-black/60 text-white backdrop-blur-sm pointer-events-none">
                                {page.label}
                              </div>
                              {/* Expand icon on hover */}
                              <div className="absolute top-1.5 right-1.5 z-10 opacity-0 group-hover:opacity-100 transition-opacity p-0.5 rounded bg-black/60 text-white backdrop-blur-sm pointer-events-none">
                                <Maximize2 size={10} />
                              </div>
                              {/* Scaled-down preview */}
                              <div
                                style={{
                                  position: 'absolute',
                                  top: 0,
                                  left: 0,
                                  width: `${QUAD_INTERNAL_W}px`,
                                  height: `${QUAD_INTERNAL_H}px`,
                                  transform: `scale(${quadScale})`,
                                  transformOrigin: 'top left',
                                }}
                              >
                                <StylePreview
                                  guide={guide}
                                  accentGuide={accentGuide}
                                  modifiers={selectedModifiers}
                                  size="full"
                                  styleName={previewStyle.name}
                                  activePage={page.id}
                                />
                              </div>
                            </div>
                          ))}
                        </div>
                      )
                    }

                    return (
                      <div className="h-full overflow-y-auto">
                        <StylePreview
                          guide={guide}
                          accentGuide={accentGuide}
                          modifiers={selectedModifiers}
                          size="full"
                          styleName={previewStyle.name}
                          activePage={previewPage}
                        />
                      </div>
                    )
                  })()}
                  {!styleId && (
                    <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
                      Select a style from the sidebar to preview
                    </div>
                  )}
                </div>
              </div>
            )}

          </div>
        )}

        {/* ---------------------------------------------------------------- */}
        {/* Step 5: Spec Method                                              */}
        {/* ---------------------------------------------------------------- */}
        {step === 'method' && (
          <div className="flex-1 flex items-center justify-center p-6">
            <div className="w-full max-w-lg space-y-4">
              <div className="mb-2">
                <h2 className="text-2xl font-semibold mb-1">Choose Setup Method</h2>
                <p className="text-sm text-muted-foreground">
                  How would you like to define your project?
                </p>
              </div>

              {/* Show selected style summary */}
              {styleId && styles && (
                <div className="flex items-center gap-2 text-sm">
                  <Paintbrush size={14} className="text-primary" />
                  <span className="text-muted-foreground">Style:</span>
                  <Badge variant="secondary">{styles.find((s: StyleOption) => s.id === styleId)?.name}</Badge>
                  {accentStyleId && styles && (
                    <span className="text-muted-foreground"> + {styles.find((s: StyleOption) => s.id === accentStyleId)?.name} accent</span>
                  )}
                </div>
              )}

              <div className="space-y-3">
                {/* Claude option */}
                <Card
                  className="cursor-pointer hover:border-primary transition-colors"
                  onClick={() => !createProject.isPending && handleMethodSelect('claude')}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start gap-4">
                      <div className="p-2 bg-primary/10 rounded-lg">
                        <Bot size={24} className="text-primary" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold">Create with Claude</span>
                          <Badge>Recommended</Badge>
                        </div>
                        <p className="text-sm text-muted-foreground mt-1">
                          Interactive conversation to define features and generate your app specification automatically.
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Manual option */}
                <Card
                  className="cursor-pointer hover:border-primary transition-colors"
                  onClick={() => !createProject.isPending && handleMethodSelect('manual')}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start gap-4">
                      <div className="p-2 bg-secondary rounded-lg">
                        <FileEdit size={24} className="text-secondary-foreground" />
                      </div>
                      <div className="flex-1">
                        <span className="font-semibold">Edit Templates Manually</span>
                        <p className="text-sm text-muted-foreground mt-1">
                          Edit the template files directly. Best for developers who want full control.
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {createProject.isPending && (
                <div className="flex items-center justify-center gap-2 text-muted-foreground">
                  <Loader2 size={16} className="animate-spin" />
                  <span>
                    {boilerplateId && boilerplateId !== 'scratch'
                      ? 'Cloning boilerplate...'
                      : 'Creating project...'}
                  </span>
                </div>
              )}

              <div className="flex justify-start">
                <Button
                  variant="ghost"
                  onClick={handleBack}
                  disabled={createProject.isPending}
                >
                  <ArrowLeft size={16} />
                  Back
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* ---------------------------------------------------------------- */}
        {/* Step 6: Complete                                                  */}
        {/* ---------------------------------------------------------------- */}
        {step === 'complete' && (
          <div className="flex-1 flex items-center justify-center p-6">
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-primary/10 rounded-full mb-4">
                <CheckCircle2 size={32} className="text-primary" />
              </div>
              <h3 className="font-semibold text-xl mb-2">{projectName}</h3>
              <p className="text-muted-foreground">
                Your project has been created successfully!
              </p>
              <div className="mt-4 flex items-center justify-center gap-2">
                <Loader2 size={16} className="animate-spin" />
                <span className="text-sm text-muted-foreground">Redirecting...</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>,
    document.body
  )
}
