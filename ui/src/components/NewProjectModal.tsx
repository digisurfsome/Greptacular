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

import { useState, useMemo } from 'react'
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
} from 'lucide-react'
import { useCreateProject, useBoilerplates, useStyles, useStyleProfiles, useStyleRecommendations, useStyleModifiers, useDescriptionRecommendation } from '../hooks/useProjects'
import { SpecCreationChat } from './SpecCreationChat'
import { FolderBrowser } from './FolderBrowser'
import { startAgent } from '../lib/api'
import type { BoilerplateCategory, StyleOption } from '../lib/types'
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

  // Suppress unused variable warning - specMethod may be used in future
  void _specMethod

  const createProject = useCreateProject()
  const { data: boilerplateCategories, isLoading: boilerplatesLoading } = useBoilerplates()
  const { data: styles, isLoading: stylesLoading } = useStyles()
  const { data: profiles } = useStyleProfiles()
  const { data: recommendations } = useStyleRecommendations(
    selectedAudience || undefined,
    selectedVibe || undefined,
    selectedAge || undefined,
  )
  const { data: modifiers } = useStyleModifiers()
  const descriptionRec = useDescriptionRecommendation()

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
        <DialogContent className="sm:max-w-3xl max-h-[85vh] flex flex-col p-0">
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
      <DialogContent className={step === 'style' ? 'sm:max-w-2xl max-h-[85vh] overflow-hidden flex flex-col' : step === 'boilerplate' ? 'sm:max-w-xl' : 'sm:max-w-lg'}>
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

              {/* Category filter tabs */}
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
            </div>

            {/* AI Recommender Panel */}
            {showRecommender && profiles && (
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
                              // Auto-fill the dropdowns with detected signals
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

            {/* Style Grid */}
            {stylesLoading && (
              <div className="flex items-center justify-center gap-2 py-8 text-muted-foreground">
                <Loader2 size={16} className="animate-spin" />
                <span>Loading styles...</span>
              </div>
            )}

            {!stylesLoading && filteredStyles.length > 0 && (
              <div className="overflow-y-auto pr-1 -mr-1 flex-1 min-h-0">
                <div className="grid grid-cols-2 gap-2">
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
                        <CardContent className="p-3">
                          {/* Color swatches preview */}
                          <div className="flex gap-1 mb-2">
                            {swatches.map((color, i) => (
                              <div
                                key={i}
                                className="h-5 flex-1 rounded-sm border border-black/10"
                                style={{ backgroundColor: color }}
                              />
                            ))}
                          </div>

                          {/* Style name and badges */}
                          <div className="flex items-center gap-1.5 mb-1">
                            <span className="font-semibold text-sm leading-tight">{style.name}</span>
                            {isTopPick && (
                              <Badge className="text-[10px] px-1.5 py-0 h-4">Best</Badge>
                            )}
                            {isRecommended && !isTopPick && (
                              <Check size={12} className="text-primary" />
                            )}
                          </div>

                          {/* Description */}
                          <p className="text-xs text-muted-foreground leading-snug line-clamp-2">
                            {style.description}
                          </p>

                          {/* Best for */}
                          <p className="text-[10px] text-muted-foreground/70 mt-1 leading-snug">
                            {style.best_for}
                          </p>
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
