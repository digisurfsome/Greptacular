/**
 * New Project Modal Component
 *
 * Multi-step modal for creating new projects:
 * 1. Enter project name
 * 2. Select project folder
 * 3. Choose boilerplate (web, mobile, scratch, etc.)
 * 4. Choose design style (with AI recommendation)
 * 5. Choose spec method (Claude or manual)
 * 6a. If Claude: Show SpecCreationChat
 * 6b. If manual: Create project and close
 */

import { useState, useMemo, useCallback } from 'react'
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
} from 'lucide-react'
import { useCreateProject, useBoilerplates, useStyles, useStyleProfiles, useStyleRecommendations, useStyleModifiers, useDescriptionRecommendation, useAccentCompatibility, useExtractStyleFromScreenshot } from '../hooks/useProjects'
import { SpecCreationChat } from './SpecCreationChat'
import { FolderBrowser } from './FolderBrowser'
import { StylePreview } from './StylePreview'
import type { PreviewPage } from './StylePreview'
import { ColorCustomizer } from './ColorCustomizer'
import { startAgent } from '../lib/api'
import type { BoilerplateCategory, StyleOption, AccentStyleOption, StyleExtractionResult } from '../lib/types'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
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

  // Style view toggle: browse (card grid) vs preview (sidebar + full render)
  const [styleView, setStyleView] = useState<StyleView>('browse')
  const [previewPage, setPreviewPage] = useState<PreviewPage>('landing')

  // Accent style state
  const [accentStyleId, setAccentStyleId] = useState<string | null>(null)

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

  // Full-screen chat view - use portal to render at body level
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

  // Folder step uses larger modal
  if (step === 'folder') {
    return (
      <Dialog open={true} onOpenChange={(open) => !open && handleClose()}>
        <DialogContent className="sm:max-w-3xl flex flex-col p-0">
          {/* Header */}
          <DialogHeader className="p-6 pb-4 border-b">
            <div className="flex items-center gap-3">
              <Folder size={24} className="text-primary" />
              <div>
                <DialogTitle>Select Project Location</DialogTitle>
                <DialogDescription>
                  Select the folder to use for project <span className="font-semibold font-mono">{projectName}</span>. Create a new folder or choose an existing one.
                </DialogDescription>
              </div>
            </div>
          </DialogHeader>

          {/* Folder Browser */}
          <div className="flex-1 overflow-hidden">
            <FolderBrowser
              onSelect={handleFolderSelect}
              onCancel={handleFolderCancel}
            />
          </div>
        </DialogContent>
      </Dialog>
    )
  }

  return (
    <Dialog open={true} onOpenChange={(open) => !open && handleClose()}>
      <DialogContent className={step === 'style' ? 'sm:max-w-7xl overflow-hidden flex flex-col max-h-[90vh] p-4 gap-2' : step === 'boilerplate' ? 'sm:max-w-xl' : 'sm:max-w-lg'}>
        <DialogHeader>
          <DialogTitle>
            {step === 'name' && 'Create New Project'}
            {step === 'boilerplate' && 'Choose a Boilerplate'}
            {step === 'style' && 'Choose a Design Style'}
            {step === 'method' && 'Choose Setup Method'}
            {step === 'complete' && 'Project Created!'}
          </DialogTitle>
        </DialogHeader>

        {/* Step 1: Project Name */}
        {step === 'name' && (
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

            <DialogFooter>
              <Button type="submit" disabled={!projectName.trim()}>
                Next
                <ArrowRight size={16} />
              </Button>
            </DialogFooter>
          </form>
        )}

        {/* Step 3: Boilerplate Selection */}
        {step === 'boilerplate' && (
          <div className="space-y-4">
            <DialogDescription>
              Pick a starting point for your project.
            </DialogDescription>

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

            <DialogFooter className="sm:justify-start">
              <Button variant="ghost" onClick={handleBack}>
                <ArrowLeft size={16} />
                Back
              </Button>
            </DialogFooter>
          </div>
        )}

        {/* Step 4: Design Style Selection */}
        {step === 'style' && (
          <div className="flex flex-col gap-3 min-h-0">
            <DialogDescription>
              Pick the design system for your app. Each style includes a complete Tailwind CSS theme, typography, and component patterns.
            </DialogDescription>

            {/* View toggle bar: Browse Styles vs Preview */}
            <div className="flex items-center gap-2 pb-2 border-b shrink-0">
              <div className="flex bg-muted rounded-lg p-0.5">
                <button
                  onClick={() => setStyleView('browse')}
                  className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                    styleView === 'browse' ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground'
                  }`}
                >
                  Browse Styles
                </button>
                <button
                  onClick={() => setStyleView('preview')}
                  className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                    styleView === 'preview' ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground'
                  }`}
                >
                  Preview
                </button>
              </div>

              {/* Category filter tabs (shown in browse view only) */}
              {styleView === 'browse' && (
                <div className="flex gap-1 ml-auto">
                  {(['all', 'core', 'vibe'] as StyleCategory[]).map((cat) => (
                    <Button
                      key={cat}
                      variant={styleCategory === cat ? 'default' : 'ghost'}
                      size="sm"
                      onClick={() => setStyleCategory(cat)}
                      className="text-xs px-2 h-7"
                    >
                      {cat === 'all' ? 'All' : cat === 'core' ? 'Core' : 'Vibe'}
                    </Button>
                  ))}
                </div>
              )}

              {/* Selected style indicator (shown in preview view) */}
              {styleView === 'preview' && styleId && styles && (
                <span className="ml-auto text-sm text-muted-foreground">
                  Previewing: <span className="font-medium text-foreground">{styles.find((s: StyleOption) => s.id === styleId)?.name}</span>
                </span>
              )}
            </div>

            {/* ============================================================ */}
            {/* BROWSE VIEW: card grid + recommender + modifiers + accent     */}
            {/* ============================================================ */}
            {styleView === 'browse' && (
              <>
                {/* AI Recommender Toggle */}
                <div className="flex items-center gap-2">
                  <Button
                    variant={showRecommender ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setShowRecommender(!showRecommender)}
                  >
                    <Sparkles size={14} />
                    {showRecommender ? 'Hide Recommender' : 'Help Me Choose'}
                  </Button>
                </div>

                {/* Style Picker Mode Tabs */}
                <div className="flex border-b border-border">
                  {(['browse', 'describe', 'screenshot'] as const).map((tab) => (
                    <button
                      key={tab}
                      onClick={() => setStylePickerTab(tab)}
                      className={`px-3 py-1.5 text-xs font-medium border-b-2 transition-colors ${
                        stylePickerTab === tab
                          ? 'border-primary text-primary'
                          : 'border-transparent text-muted-foreground hover:text-foreground'
                      }`}
                    >
                      {tab === 'browse' ? 'Browse Styles' : tab === 'describe' ? 'Describe App' : 'Screenshot'}
                    </button>
                  ))}
                </div>

                {/* AI Recommender Panel */}
                {(stylePickerTab === 'browse' || stylePickerTab === 'describe') && showRecommender && profiles && (
                  <Card className="border-primary/30 bg-primary/5">
                    <CardContent className="p-3 space-y-3">
                      {/* Quick description option */}
                      <div className="space-y-1.5">
                        <Label className="text-xs">Describe your app (optional)</Label>
                        <div className="flex gap-2">
                          <textarea
                            value={appDescription}
                            onChange={(e) => setAppDescription(e.target.value)}
                            placeholder="e.g., A sugar tracking app for diabetics aged 50-80 that scans nutrition labels..."
                            className="flex-1 text-xs rounded-md border border-border bg-background px-2 py-1.5 resize-none h-14"
                          />
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
                            className="self-end"
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
                          <p className="text-[10px] text-muted-foreground">
                            Detected: {[
                              descriptionRec.data.detected_signals.audience && `Audience: ${descriptionRec.data.detected_signals.audience}`,
                              descriptionRec.data.detected_signals.vibe && `Vibe: ${descriptionRec.data.detected_signals.vibe}`,
                              descriptionRec.data.detected_signals.age_group && `Age: ${descriptionRec.data.detected_signals.age_group}`,
                            ].filter(Boolean).join(' | ')}
                          </p>
                        )}
                      </div>

                      {/* Divider */}
                      <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                        <div className="flex-1 h-px bg-border" />
                        <span>or choose manually</span>
                        <div className="flex-1 h-px bg-border" />
                      </div>

                      <div className="grid grid-cols-3 gap-2">
                        <div>
                          <Label className="text-xs">Audience</Label>
                          <select
                            value={selectedAudience}
                            onChange={(e) => setSelectedAudience(e.target.value)}
                            className="w-full mt-1 text-xs rounded-md border border-border bg-background px-2 py-1.5"
                          >
                            <option value="">Any</option>
                            {Object.entries(profiles.audiences).map(([key, val]) => (
                              <option key={key} value={key}>{val.label}</option>
                            ))}
                          </select>
                        </div>
                        <div>
                          <Label className="text-xs">Vibe</Label>
                          <select
                            value={selectedVibe}
                            onChange={(e) => setSelectedVibe(e.target.value)}
                            className="w-full mt-1 text-xs rounded-md border border-border bg-background px-2 py-1.5"
                          >
                            <option value="">Any</option>
                            {Object.entries(profiles.vibes).map(([key, val]) => (
                              <option key={key} value={key}>{val.label}</option>
                            ))}
                          </select>
                        </div>
                        <div>
                          <Label className="text-xs">Age Group</Label>
                          <select
                            value={selectedAge}
                            onChange={(e) => setSelectedAge(e.target.value)}
                            className="w-full mt-1 text-xs rounded-md border border-border bg-background px-2 py-1.5"
                          >
                            <option value="">Any</option>
                            {Object.entries(profiles.age_groups).map(([key, val]) => (
                              <option key={key} value={key}>{val.label}</option>
                            ))}
                          </select>
                        </div>
                      </div>
                      {recommendations && recommendations.length > 0 && (
                        <p className="text-xs text-muted-foreground mt-2">
                          Top picks highlighted below. Best match: <span className="font-semibold text-primary">{styles?.find((s: StyleOption) => s.id === recommendations[0].style_id)?.name}</span>
                        </p>
                      )}
                    </CardContent>
                  </Card>
                )}

                {/* Screenshot Extraction Tab */}
                {stylePickerTab === 'screenshot' && (
                  <div className="space-y-4 py-4">
                    <div className="flex flex-col items-center gap-3">
                      <div className="w-full max-w-md">
                        <label
                          className={`flex flex-col items-center gap-3 p-8 border-2 border-dashed rounded-xl cursor-pointer transition-colors ${
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
                              <Loader2 size={32} className="text-primary animate-spin" />
                              <span className="text-sm text-muted-foreground">Analyzing screenshot...</span>
                            </>
                          ) : (
                            <>
                              <Upload size={32} className="text-muted-foreground" />
                              <div className="text-center">
                                <p className="text-sm font-medium">Drop an image here or click to upload</p>
                                <p className="text-xs text-muted-foreground mt-1">.png, .jpg, or .webp</p>
                              </div>
                            </>
                          )}
                        </label>
                      </div>

                      {/* Extraction Results */}
                      {extractionResult && (
                        <Card className="w-full">
                          <CardContent className="p-4 space-y-3">
                            <div className="flex items-center gap-2">
                              <ImageIcon size={16} className="text-primary" />
                              <span className="font-medium text-sm">Style Analysis</span>
                            </div>

                            {extractionResult.identified_style.primary && (
                              <div className="space-y-1">
                                <p className="text-sm">
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
                                <p className="text-xs text-muted-foreground">
                                  Confidence: {extractionResult.identified_style.primary_confidence}
                                </p>
                              </div>
                            )}

                            {/* Extracted color palette preview */}
                            {extractionResult.tailwind_config && !!(extractionResult.tailwind_config as Record<string, unknown>).colors && (
                              <div className="space-y-1">
                                <p className="text-xs text-muted-foreground">Extracted palette:</p>
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
                                        className="h-6 w-8 rounded border border-black/10"
                                        style={{ backgroundColor: c }}
                                        title={c}
                                      />
                                    ))
                                  })()}
                                </div>
                              </div>
                            )}

                            <div className="flex gap-2 pt-1">
                              <Button size="sm" onClick={() => {
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
                                onClick={() => {
                                  setExtractionResult(null)
                                }}
                              >
                                Try Another Image
                              </Button>
                            </div>
                          </CardContent>
                        </Card>
                      )}

                      {extractScreenshot.isError && (
                        <Alert variant="destructive" className="w-full">
                          <AlertDescription>
                            Failed to analyze screenshot. Make sure you have a valid ANTHROPIC_API_KEY set.
                          </AlertDescription>
                        </Alert>
                      )}
                    </div>
                  </div>
                )}

                {/* Style Grid */}
                {stylePickerTab !== 'screenshot' && stylesLoading && (
                  <div className="flex items-center justify-center gap-2 py-8 text-muted-foreground">
                    <Loader2 size={16} className="animate-spin" />
                    <span>Loading styles...</span>
                  </div>
                )}

                {stylePickerTab !== 'screenshot' && !stylesLoading && filteredStyles.length > 0 && (
                  <div className="overflow-y-auto pr-1 -mr-1 flex-1 min-h-0">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
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
                            <CardContent className="p-3 flex gap-3">
                              {/* LEFT: Style info */}
                              <div className="flex-1 min-w-0 flex flex-col">
                                {/* Color swatches + name row */}
                                <div className="flex items-center gap-2 mb-1.5">
                                  <div className="flex gap-0.5">
                                    {swatches.map((color, i) => (
                                      <div
                                        key={i}
                                        className="h-5 w-5 rounded-sm border border-black/10"
                                        style={{ backgroundColor: color }}
                                      />
                                    ))}
                                  </div>
                                  <span className="font-semibold text-sm leading-tight">{style.name}</span>
                                  {isTopPick && (
                                    <Badge className="text-[10px] px-1.5 py-0 h-4">Best</Badge>
                                  )}
                                  {isRecommended && !isTopPick && (
                                    <Check size={12} className="text-primary" />
                                  )}
                                  <Badge variant="outline" className="text-[9px] px-1.5 py-0 h-4 ml-auto capitalize">
                                    {style.category}
                                  </Badge>
                                </div>

                                {/* Description */}
                                <p className="text-xs text-muted-foreground leading-snug">
                                  {style.description}
                                </p>

                                {/* Philosophy */}
                                <p className="text-[10px] text-muted-foreground/60 mt-1 leading-snug line-clamp-2 italic">
                                  {style.philosophy}
                                </p>

                                {/* Best for */}
                                <p className="text-[10px] text-muted-foreground/70 mt-auto pt-1 leading-snug">
                                  <span className="font-medium text-muted-foreground/90">Best for:</span> {style.best_for}
                                </p>
                              </div>

                              {/* RIGHT: UI Preview */}
                              {style.style_guide && (
                                <div className="w-[200px] shrink-0">
                                  <StylePreview
                                    guide={style.style_guide}
                                    size="compact"
                                    styleName={style.name}
                                    modifiers={isSelected ? selectedModifiers : undefined}
                                    accentGuide={isSelected && accentStyleId
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

                    {/* Modifier Selection (shown after picking a style) */}
                    {styleId && modifiers && modifiers.length > 0 && (
                      <div className="space-y-2 border-t pt-3 mt-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium">Accessibility Modifiers</span>
                          <Badge variant="secondary" className="text-[10px]">Optional</Badge>
                        </div>
                        <p className="text-xs text-muted-foreground">
                          Layer accessibility enhancements on top of your chosen style.
                        </p>
                        <div className="grid grid-cols-2 gap-2">
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
                                className={`text-left p-2.5 rounded-lg border transition-colors ${
                                  isActive
                                    ? 'border-primary bg-primary/10'
                                    : 'border-border hover:border-primary/50'
                                }`}
                              >
                                <div className="flex items-center gap-1.5">
                                  {isActive && <Check size={12} className="text-primary" />}
                                  <span className="text-sm font-medium">{mod.name}</span>
                                </div>
                                <p className="text-xs text-muted-foreground mt-0.5 leading-snug">
                                  {mod.description}
                                </p>
                              </button>
                            )
                          })}
                        </div>
                        {selectedModifiers.length >= 3 && (
                          <p className="text-xs text-muted-foreground">Maximum 3 modifiers.</p>
                        )}
                      </div>
                    )}

                    {/* Accent Style Picker (shown after picking a base style) */}
                    {styleId && accentStyles && accentStyles.length > 0 && (
                      <div className="space-y-2 border-t pt-3 mt-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium">Accent Style</span>
                          <Badge variant="secondary" className="text-[10px]">Optional</Badge>
                        </div>
                        <p className="text-xs text-muted-foreground">
                          Add a secondary style for buttons, inputs, and interactive elements only.
                        </p>
                        <div className="grid grid-cols-2 gap-2">
                          {accentStyles.map((accent: AccentStyleOption) => {
                            const isActive = accentStyleId === accent.id
                            return (
                              <button
                                key={accent.id}
                                onClick={() => setAccentStyleId(isActive ? null : accent.id)}
                                className={`text-left p-2.5 rounded-lg border transition-colors ${
                                  isActive
                                    ? 'border-primary bg-primary/10'
                                    : 'border-border hover:border-primary/50'
                                }`}
                              >
                                <div className="flex items-center gap-1.5">
                                  {isActive && <Check size={12} className="text-primary" />}
                                  <span className="text-sm font-medium">{accent.name}</span>
                                </div>
                                <p className="text-xs text-muted-foreground mt-0.5 leading-snug line-clamp-2">
                                  {accent.description}
                                </p>
                              </button>
                            )
                          })}
                        </div>
                        {accentStyleId && (
                          <p className="text-[10px] text-muted-foreground">
                            Base style controls layout, colors, and typography. Accent controls buttons and inputs only.
                          </p>
                        )}
                      </div>
                    )}

                    {/* Color Customization (shown after picking a style that has tokens) */}
                    {styleId && (() => {
                      const selected = styles?.find((s: StyleOption) => s.id === styleId)
                      if (!selected?.style_guide) return null
                      return (
                        <ColorCustomizer
                          styleGuide={selected.style_guide}
                          customColors={customColors}
                          onChange={setCustomColors}
                        />
                      )
                    })()}
                  </div>
                )}
              </>
            )}

            {/* ============================================================ */}
            {/* PREVIEW VIEW: sidebar + full render                          */}
            {/* ============================================================ */}
            {styleView === 'preview' && (
              <div className="flex flex-1 min-h-0 gap-0 border rounded-lg overflow-hidden">
                {/* Left sidebar */}
                <div className="w-[280px] shrink-0 border-r bg-muted/30 overflow-y-auto">
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

                  {/* Page tabs section */}
                  <div className="p-3 border-b">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">Page</h4>
                    <div className="space-y-0.5">
                      {([
                        { id: 'landing' as PreviewPage, label: 'Landing' },
                        { id: 'dashboard' as PreviewPage, label: 'Dashboard' },
                        { id: 'settings' as PreviewPage, label: 'Settings' },
                        { id: 'feed' as PreviewPage, label: 'Feed' },
                      ]).map((page) => {
                        const isActive = previewPage === page.id
                        return (
                          <button
                            key={page.id}
                            onClick={() => setPreviewPage(page.id)}
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
                <div className="flex-1 overflow-y-auto min-h-0 bg-muted/10">
                  {styleId && (() => {
                    const previewStyle = styles?.find((s: StyleOption) => s.id === styleId)
                    if (!previewStyle?.style_guide) return (
                      <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
                        Select a style to preview
                      </div>
                    )
                    const accentGuide = accentStyleId
                      ? styles?.find((s: StyleOption) => s.id === accentStyleId)?.style_guide
                      : undefined
                    return (
                      <StylePreview
                        guide={previewStyle.style_guide}
                        accentGuide={accentGuide}
                        modifiers={selectedModifiers}
                        size="full"
                        styleName={previewStyle.name}
                        activePage={previewPage}
                      />
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

            <DialogFooter className="sm:justify-between pt-1">
              <Button variant="ghost" onClick={handleBack}>
                <ArrowLeft size={16} />
                Back
              </Button>
              <div className="flex gap-2">
                {!styleId && (
                  <Button variant="outline" onClick={handleStyleSkip}>
                    Skip for Now
                    <ArrowRight size={16} />
                  </Button>
                )}
                {styleId && (
                  <Button onClick={handleStyleConfirm}>
                    Continue
                    <ArrowRight size={16} />
                  </Button>
                )}
              </div>
            </DialogFooter>
          </div>
        )}

        {/* Step 5: Spec Method */}
        {step === 'method' && (
          <div className="space-y-4">
            <DialogDescription>
              How would you like to define your project?
            </DialogDescription>

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

            <DialogFooter className="sm:justify-start">
              <Button
                variant="ghost"
                onClick={handleBack}
                disabled={createProject.isPending}
              >
                <ArrowLeft size={16} />
                Back
              </Button>
            </DialogFooter>
          </div>
        )}

        {/* Step 6: Complete */}
        {step === 'complete' && (
          <div className="text-center py-8">
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
        )}
      </DialogContent>
    </Dialog>
  )
}
