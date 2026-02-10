/**
 * New Project Modal Component
 *
 * Multi-step modal for creating new projects:
 * 1. Enter project name
 * 2. Select project folder
 * 3. Choose boilerplate (web, mobile, scratch, etc.)
 * 4. Choose design style (placeholder - coming soon)
 * 5. Choose spec method (Claude or manual)
 * 6a. If Claude: Show SpecCreationChat
 * 6b. If manual: Create project and close
 */

import { useState } from 'react'
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
} from 'lucide-react'
import { useCreateProject, useBoilerplates, useStyles, useStyleRecommendations } from '../hooks/useProjects'
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

/** Map category IDs to lucide-react icons */
const CATEGORY_ICONS: Record<string, React.ComponentType<{ size?: number; className?: string }>> = {
  web: Globe,
  mobile: Smartphone,
  web_mobile: Layers,
  scratch: Zap,
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
  const [recAudience, setRecAudience] = useState('')
  const [recVibe, setRecVibe] = useState('')
  const [recAge, setRecAge] = useState('')

  // Suppress unused variable warning - specMethod may be used in future
  void _specMethod

  const createProject = useCreateProject()
  const { data: boilerplateCategories, isLoading: boilerplatesLoading } = useBoilerplates()
  const { data: styleCategories, isLoading: stylesLoading } = useStyles()
  const { data: recommendations } = useStyleRecommendations(recAudience, recVibe, recAge)

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

  const handleStyleSelect = (style: StyleOption) => {
    setStyleId(style.id)
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
    setRecAudience('')
    setRecVibe('')
    setRecAge('')
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
      <DialogContent className={step === 'boilerplate' || step === 'style' ? 'sm:max-w-2xl' : 'sm:max-w-lg'}>
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

        {/* Step 4: Design Style */}
        {step === 'style' && (
          <div className="space-y-4">
            <DialogDescription>
              Choose a visual design style. This will guide the AI to build a consistent UI.
            </DialogDescription>

            {/* AI Recommendation */}
            <details className="group">
              <summary className="cursor-pointer text-sm font-medium text-primary hover:underline">
                Not sure? Let AI recommend a style
              </summary>
              <div className="mt-3 p-3 bg-muted rounded-lg space-y-2">
                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Audience</label>
                    <select
                      value={recAudience}
                      onChange={(e) => setRecAudience(e.target.value)}
                      className="w-full mt-1 px-2 py-1.5 text-sm rounded-md border bg-background"
                    >
                      <option value="">Select...</option>
                      <option value="health-conscious">Health-conscious</option>
                      <option value="young-edgy">Young / Edgy</option>
                      <option value="premium-luxury">Premium / Luxury</option>
                      <option value="friendly-approachable">Friendly / Approachable</option>
                      <option value="finance-dashboard">Finance / Dashboard</option>
                      <option value="gaming-entertainment">Gaming / Entertainment</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Vibe</label>
                    <select
                      value={recVibe}
                      onChange={(e) => setRecVibe(e.target.value)}
                      className="w-full mt-1 px-2 py-1.5 text-sm rounded-md border bg-background"
                    >
                      <option value="">Select...</option>
                      <option value="trustworthy">Trustworthy</option>
                      <option value="fun">Fun</option>
                      <option value="modern">Modern</option>
                      <option value="nostalgic">Nostalgic</option>
                      <option value="edgy">Edgy</option>
                      <option value="warm">Warm</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Age Group</label>
                    <select
                      value={recAge}
                      onChange={(e) => setRecAge(e.target.value)}
                      className="w-full mt-1 px-2 py-1.5 text-sm rounded-md border bg-background"
                    >
                      <option value="">Select...</option>
                      <option value="under-30">Under 30</option>
                      <option value="30-50">30 - 50</option>
                      <option value="50-plus">50+</option>
                    </select>
                  </div>
                </div>
                {recommendations && recommendations.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {recommendations.slice(0, 3).map((rec, i) => (
                      <Badge
                        key={rec.style_id}
                        variant={i === 0 ? 'default' : 'secondary'}
                        className="cursor-pointer"
                        onClick={() => {
                          setStyleId(rec.style_id)
                          changeStep('method')
                        }}
                      >
                        {i === 0 && '★ '}{rec.style_name}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            </details>

            {/* Style Grid */}
            {stylesLoading && (
              <div className="flex items-center justify-center gap-2 py-8 text-muted-foreground">
                <Loader2 size={16} className="animate-spin" />
                <span>Loading styles...</span>
              </div>
            )}

            {!stylesLoading && styleCategories && (
              <div className="space-y-4 max-h-[50vh] overflow-y-auto pr-1">
                {styleCategories.map((cat) => (
                  <div key={cat.category}>
                    <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                      {cat.label}
                    </p>
                    <div className="grid grid-cols-2 gap-2">
                      {cat.styles.map((style: StyleOption) => {
                        const isRec = recommendations?.some((r) => r.style_id === style.id && r.score >= 6)
                        return (
                          <Card
                            key={style.id}
                            className={`cursor-pointer transition-all hover:border-primary ${
                              styleId === style.id ? 'border-primary ring-2 ring-primary/20' : ''
                            } ${isRec ? 'ring-1 ring-yellow-400/50' : ''}`}
                            onClick={() => handleStyleSelect(style)}
                          >
                            <CardContent className="p-3">
                              <div className="flex gap-3">
                                {/* Mini preview swatch */}
                                <div
                                  className="w-14 h-14 rounded-md flex-shrink-0 flex items-center justify-center overflow-hidden"
                                  style={{
                                    background: style.css_preview.background,
                                    border: style.css_preview.card_border !== 'none'
                                      ? style.css_preview.card_border
                                      : '1px solid #e5e7eb',
                                  }}
                                >
                                  {/* Inner card preview */}
                                  <div
                                    className="w-10 h-8"
                                    style={{
                                      background: style.css_preview.card_bg,
                                      border: style.css_preview.card_border !== 'none'
                                        ? style.css_preview.card_border
                                        : undefined,
                                      borderRadius: style.css_preview.card_radius,
                                      boxShadow: style.css_preview.card_shadow !== 'none'
                                        ? style.css_preview.card_shadow
                                        : undefined,
                                    }}
                                  >
                                    <div
                                      className="w-6 h-1.5 mt-1.5 mx-auto rounded-full"
                                      style={{ background: style.css_preview.accent }}
                                    />
                                    <div
                                      className="w-4 h-1 mt-1 mx-auto rounded-full opacity-40"
                                      style={{ background: style.css_preview.text }}
                                    />
                                  </div>
                                </div>
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-1.5">
                                    <span className="font-semibold text-sm">{style.name}</span>
                                    {isRec && <Badge variant="outline" className="text-[10px] px-1 py-0">Recommended</Badge>}
                                  </div>
                                  <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
                                    {style.best_for}
                                  </p>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        )
                      })}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <DialogFooter className="sm:justify-between">
              <Button variant="ghost" onClick={handleBack}>
                <ArrowLeft size={16} />
                Back
              </Button>
              <Button variant="outline" onClick={handleStyleSkip}>
                Skip for Now
                <ArrowRight size={16} />
              </Button>
            </DialogFooter>
          </div>
        )}

        {/* Step 5: Spec Method */}
        {step === 'method' && (
          <div className="space-y-4">
            <DialogDescription>
              How would you like to define your project?
            </DialogDescription>

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
