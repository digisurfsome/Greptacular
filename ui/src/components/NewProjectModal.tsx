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
  Star,
  ChevronLeft,
  ChevronRight,
  Github,
  ExternalLink,
  Eye,
  EyeOff,
  Lock,
  Unlock,
} from 'lucide-react'
import { useCreateProject, useBoilerplates, useStyles, useStyleProfiles, useStyleRecommendations, useStyleModifiers, useDescriptionRecommendation, useExtractStyleFromScreenshot } from '../hooks/useProjects'
import { SpecCreationChat } from './SpecCreationChat'
import { FolderBrowser } from './FolderBrowser'
import { StylePreview } from './StylePreview'
import type { PreviewPage } from './StylePreview'
import { StyleCardPreview } from './StyleCardPreview'
import { DesignGuidePanel } from './DesignGuidePanel'
import { ColorCustomizer } from './ColorCustomizer'
import { PALETTES } from '../data/palettes'
import { FONT_OPTIONS } from '../data/fonts'
import { REFINEMENT_GROUPS } from '../data/refinementOptions'
import { paletteToCustomColors } from '../lib/paletteUtils'
import { startAgent, validateGitHubToken, createGitHubRepo } from '../lib/api'
import type { BoilerplateCategory, StyleOption, StyleGuide, StyleExtractionResult, DesignRefinement, DesignGuideAction } from '../lib/types'
import { DEFAULT_REFINEMENT } from '../lib/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'

type InitializerStatus = 'idle' | 'starting' | 'error'

type Step = 'name' | 'folder' | 'boilerplate' | 'style' | 'github' | 'method' | 'chat' | 'complete'
type SpecMethod = 'claude' | 'manual'
type StyleCategory = 'all' | 'core' | 'vibe'
type StyleView = 'browse' | 'preview'

/** Sequential step definitions for the progress bar */
const STEP_ORDER: { id: Step; label: string }[] = [
  { id: 'name', label: 'Project' },
  { id: 'folder', label: 'Location' },
  { id: 'boilerplate', label: 'Boilerplate' },
  { id: 'style', label: 'Design' },
  { id: 'github', label: 'GitHub' },
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

/** Fallback style guide used when no style is selected or style_guide is missing */
const DEFAULT_STYLE_GUIDE: StyleGuide = {
  color_tokens: {
    brand: { light: '#93c5fd', DEFAULT: '#3b82f6', dark: '#1e40af' },
    surface: { canvas: '#ffffff', base: '#f8fafc', muted: '#f1f5f9' },
    text: { primary: '#0f172a', secondary: '#475569', tertiary: '#94a3b8' },
    border: { subtle: '#e2e8f0' },
    status: { success: '#22c55e', error: '#ef4444', warning: '#f59e0b', info: '#3b82f6' },
  },
  typography: { font_family: 'Inter, sans-serif', hierarchy: [] },
  components: {
    cards: { radius: '8px', shadow: 'sm' },
    buttons: { radius: '6px' },
    inputs: { radius: '6px' },
    icons: { style: 'outline', size: '20px' },
  },
  spacing: { base_unit: '4px', density: 'comfortable', card_gap: '16px', section_gap: '32px' },
  tailwind_config: {},
}

// ---------------------------------------------------------------------------
// Pill-shaped Prev/Next Navigator
// ---------------------------------------------------------------------------

/** Compact pill with left/right arrows to cycle through items in a section */
function PillNav({ onPrev, onNext }: { onPrev: () => void; onNext: () => void }) {
  return (
    <div className="flex items-center justify-center mb-1">
      <div className="flex items-center border border-border rounded-full overflow-hidden">
        <button
          type="button"
          onClick={onPrev}
          className="px-1.5 py-0.5 hover:bg-muted/50 transition-colors border-r border-border"
        >
          <ChevronLeft size={10} />
        </button>
        <button
          type="button"
          onClick={onNext}
          className="px-1.5 py-0.5 hover:bg-muted/50 transition-colors"
        >
          <ChevronRight size={10} />
        </button>
      </div>
    </div>
  )
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

  // GitHub integration state
  const [githubToken, setGithubToken] = useState(() => localStorage.getItem('github_token') || '')
  const [githubUser, setGithubUser] = useState<{ login: string; name: string; avatar_url: string } | null>(null)
  const [githubTokenValidating, setGithubTokenValidating] = useState(false)
  const [githubTokenError, setGithubTokenError] = useState<string | null>(null)
  const [githubRepoPrivate, setGithubRepoPrivate] = useState(true)
  const [githubRepoCreating, setGithubRepoCreating] = useState(false)
  const [githubRepoUrl, setGithubRepoUrl] = useState<string | null>(null)
  const [githubRepoError, setGithubRepoError] = useState<string | null>(null)
  const [githubShowToken, setGithubShowToken] = useState(false)

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
  const [_styleView, setStyleView] = useState<StyleView>('browse')
  const [previewPage, setPreviewPage] = useState<PreviewPage>('landing')
  const [previewViewMode, setPreviewViewMode] = useState<'quad' | 'single'>('quad')

  // Accent style state
  const [accentStyleId, setAccentStyleId] = useState<string | null>(null)

  // Favorites and palette navigation state
  const [favoriteStyles, setFavoriteStyles] = useState<Set<string>>(new Set())
  const [paletteIndex, setPaletteIndex] = useState(0)

  // Design tab: base (style/colors) vs refine (detailed decisions)
  const [designTab, setDesignTab] = useState<'base' | 'refine'>('base')

  // Refinement options
  const [refinement, setRefinement] = useState<DesignRefinement>(DEFAULT_REFINEMENT)

  // Font selection
  const [selectedFontId, setSelectedFontId] = useState<string | null>(null)

  // Quad view dynamic scaling
  const QUAD_INTERNAL_W = 1280
  const QUAD_INTERNAL_H = 800
  const quadGridRef = useRef<HTMLDivElement>(null)
  const [quadScale, setQuadScale] = useState(0.4)

  useEffect(() => {
    if (previewViewMode !== 'quad' || !quadGridRef.current) return
    const el = quadGridRef.current
    const update = () => {
      const { clientWidth, clientHeight } = el
      if (clientWidth === 0 || clientHeight === 0) return
      // Account for padding (8px * 2 = 16px) and gap (6px) in the CSS grid
      const cellW = (clientWidth - 16 - 6) / 2
      const cellH = (clientHeight - 16 - 6) / 2
      const scale = Math.min(cellW / QUAD_INTERNAL_W, cellH / QUAD_INTERNAL_H)
      setQuadScale(Math.max(0.1, Math.min(1, scale)))
    }
    update() // Immediate first calculation
    const observer = new ResizeObserver(() => update())
    observer.observe(el)
    return () => observer.disconnect()
  }, [previewViewMode])

  // Screenshot extractor state
  const [stylePickerTab, setStylePickerTab] = useState<'browse' | 'describe' | 'screenshot'>('browse')
  const [screenshotExtracting, setScreenshotExtracting] = useState(false)
  const [extractionResult, setExtractionResult] = useState<StyleExtractionResult | null>(null)

  // Suppress unused variable warnings - these may be used in future
  void _specMethod
  void _styleView
  void paletteIndex

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

  // Action handler for the AI design guide panel -- must be before early return
  // because useCallback is a hook and hooks cannot be called conditionally.
  const handleDesignGuideAction = useCallback((action: DesignGuideAction) => {
    switch (action.action) {
      case 'select_style':
        // Inline handleStyleSelect logic to avoid dependency on post-return function
        setCustomColors({})
        setStyleId(action.styleId)
        break
      case 'set_accent_style':
        setAccentStyleId(action.styleId)
        break
      case 'toggle_modifier':
        setSelectedModifiers(prev =>
          prev.includes(action.modifierId)
            ? prev.filter(id => id !== action.modifierId)
            : prev.length < 3 ? [...prev, action.modifierId] : prev
        )
        break
      case 'set_palette': {
        const palette = PALETTES[action.paletteIndex]
        if (palette) {
          setPaletteIndex(action.paletteIndex)
          setSelectedPaletteId(palette.id)
          setCustomColors(paletteToCustomColors(palette))
        }
        break
      }
      case 'set_custom_color':
        setCustomColors(prev => ({ ...prev, [action.colorKey]: action.value }))
        break
      case 'switch_tab':
        setDesignTab(action.tab)
        break
      case 'set_refinement':
        setRefinement(prev => ({ ...prev, [action.key]: action.value }))
        break
      case 'set_preview_mode':
        setPreviewViewMode(action.mode)
        break
      case 'set_preview_page':
        setPreviewPage(action.page)
        break
      case 'highlight_option':
        // TODO: Implement highlight animation
        break
    }
  }, [])

  // Auto-select first style when styles load and nothing is selected yet
  useEffect(() => {
    if (styleId || !filteredStyles.length) return
    setCustomColors({})
    setStyleId(filteredStyles[0].id)
  }, [filteredStyles]) // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-validate saved GitHub token when entering the GitHub step
  useEffect(() => {
    if (step !== 'github' || githubUser || githubTokenValidating) return
    const savedToken = localStorage.getItem('github_token')
    if (savedToken && savedToken.length > 0) {
      setGithubToken(savedToken)
      setGithubTokenValidating(true)
      setGithubTokenError(null)
      validateGitHubToken(savedToken)
        .then((user) => {
          setGithubUser(user)
          setGithubTokenError(null)
        })
        .catch(() => {
          // Token expired or invalid -- clear it
          localStorage.removeItem('github_token')
          setGithubToken('')
          setGithubTokenError('Saved token is no longer valid. Please enter a new one.')
        })
        .finally(() => setGithubTokenValidating(false))
    }
  }, [step]) // eslint-disable-line react-hooks/exhaustive-deps

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
    changeStep('github')
  }

  const handleStyleSkip = () => {
    setStyleId(null)
    changeStep('github')
  }

  // GitHub step handlers
  const handleGithubValidateToken = async () => {
    const token = githubToken.trim()
    if (!token) {
      setGithubTokenError('Please enter a GitHub token')
      return
    }
    setGithubTokenValidating(true)
    setGithubTokenError(null)
    try {
      const user = await validateGitHubToken(token)
      setGithubUser(user)
      localStorage.setItem('github_token', token)
    } catch {
      setGithubTokenError('Invalid token. Make sure it has "repo" scope.')
      setGithubUser(null)
    } finally {
      setGithubTokenValidating(false)
    }
  }

  const handleGithubCreateRepo = async () => {
    if (!githubUser || !githubToken) return
    setGithubRepoCreating(true)
    setGithubRepoError(null)

    // Parse template owner/repo from boilerplate if available
    let templateOwner: string | undefined
    let templateRepo: string | undefined
    if (boilerplateId && boilerplateId !== 'scratch' && boilerplateCategories) {
      for (const cat of boilerplateCategories) {
        const opt = cat.options.find((o) => o.id === boilerplateId)
        if (opt?.repo_url) {
          const match = opt.repo_url.match(/github\.com\/([^/]+)\/([^/]+?)(?:\.git)?$/)
          if (match) {
            templateOwner = match[1]
            templateRepo = match[2]
          }
          break
        }
      }
    }

    try {
      const result = await createGitHubRepo({
        token: githubToken,
        repo_name: projectName.trim(),
        private: githubRepoPrivate,
        description: `Created with AutoForge`,
        template_owner: templateOwner,
        template_repo: templateRepo,
      })
      setGithubRepoUrl(result.repo_url)
    } catch (err: unknown) {
      setGithubRepoError(err instanceof Error ? err.message : 'Failed to create repo')
    } finally {
      setGithubRepoCreating(false)
    }
  }

  const handleGithubSkip = () => {
    changeStep('method')
  }

  const handleGithubContinue = () => {
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
          fontId: selectedFontId,
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
          fontId: selectedFontId,
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
    setFavoriteStyles(new Set())
    setPaletteIndex(0)
    setDesignTab('base')
    setRefinement(DEFAULT_REFINEMENT)
    setSelectedFontId(null)
    // Reset GitHub state (keep token in localStorage for convenience)
    setGithubUser(null)
    setGithubTokenValidating(false)
    setGithubTokenError(null)
    setGithubRepoPrivate(true)
    setGithubRepoCreating(false)
    setGithubRepoUrl(null)
    setGithubRepoError(null)
    setGithubShowToken(false)
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
      setFavoriteStyles(new Set())
      setPaletteIndex(0)
      setDesignTab('base')
      setRefinement(DEFAULT_REFINEMENT)
      setSelectedFontId(null)
    } else if (step === 'github') {
      changeStep('style')
    } else if (step === 'method') {
      changeStep('github')
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
    if (targetIndex < 5) {
      // Going before github: reset github repo state (keep token for convenience)
      setGithubRepoUrl(null)
      setGithubRepoError(null)
      setGithubRepoCreating(false)
    }
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
      setFavoriteStyles(new Set())
      setPaletteIndex(0)
      setDesignTab('base')
      setRefinement(DEFAULT_REFINEMENT)
      setSelectedFontId(null)
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
      <div className="fixed inset-0 z-[70] bg-background flex flex-col">
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
    <div className="fixed inset-0 z-[70] bg-background flex flex-col h-screen overflow-hidden">
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

            {/* Category filter tabs */}
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

            {/* Center spacer */}
            <div className="flex-1" />

            {/* AI Recommendation button */}
            <Button
              variant={showRecommender ? 'default' : 'outline'}
              size="sm"
              onClick={() => setShowRecommender(!showRecommender)}
              className="h-6 text-[11px] shrink-0"
            >
              <Sparkles size={11} />
              AI Recommendation
            </Button>

            {/* Style Picker Mode Tabs */}
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
          <div className="flex-1 flex flex-col items-center min-h-0 py-4">
            <div className="w-full max-w-2xl flex flex-col min-h-0 flex-1 border rounded-lg overflow-hidden bg-card">
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
            {/* AI Recommender Panel (collapsible, compact)             */}
            {/* ==================================================== */}
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

            {/* ==================================================== */}
            {/* Screenshot Extraction Tab                               */}
            {/* ==================================================== */}
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
                                    className="h-5 w-6 rounded border border-foreground/10"
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

            {/* ==================================================== */}
            {/* 4-COLUMN LAYOUT: styles | controls | AI guide | preview */}
            {/* ==================================================== */}
            {stylePickerTab !== 'screenshot' && (
              <div className="flex-1 min-h-0 flex overflow-hidden">
                {/* COLUMN 1: Style Cards — 2-col grid with large previews */}
                <div className="w-[380px] shrink-0 border-r border-border/50 overflow-y-auto p-2">
                  {stylesLoading && (
                    <div className="flex items-center justify-center gap-2 py-8 text-muted-foreground">
                      <Loader2 size={16} className="animate-spin" />
                      <span>Loading styles...</span>
                    </div>
                  )}
                  {!stylesLoading && filteredStyles.length > 0 && (
                    <>
                    <PillNav
                      onPrev={() => {
                        if (!filteredStyles.length) return
                        const idx = filteredStyles.findIndex((s: StyleOption) => s.id === styleId)
                        const prev = (idx <= 0 ? filteredStyles.length : idx) - 1
                        handleStyleSelect(filteredStyles[prev].id)
                      }}
                      onNext={() => {
                        if (!filteredStyles.length) return
                        const idx = filteredStyles.findIndex((s: StyleOption) => s.id === styleId)
                        const next = (idx + 1) % filteredStyles.length
                        handleStyleSelect(filteredStyles[next].id)
                      }}
                    />
                    <div className="grid grid-cols-2 gap-3">
                      {filteredStyles.map((style: StyleOption) => {
                        const isSelected = styleId === style.id
                        const isFavorite = favoriteStyles.has(style.id)
                        const isRecommended = recommendedIds.has(style.id)

                        return (
                          <div
                            key={style.id}
                            className={`relative cursor-pointer rounded-lg border transition-all ${
                              isSelected ? 'border-primary ring-2 ring-primary/30 bg-primary/5' :
                              isRecommended ? 'border-primary/40 hover:border-primary' :
                              'border-border hover:border-primary/50'
                            }`}
                            onClick={() => handleStyleSelect(style.id)}
                          >
                            {/* Favorite star */}
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation()
                                setFavoriteStyles(prev => {
                                  const next = new Set(prev)
                                  if (next.has(style.id)) next.delete(style.id)
                                  else next.add(style.id)
                                  return next
                                })
                              }}
                              className={`absolute top-1 right-1 z-10 p-0.5 rounded-sm transition-colors ${
                                isFavorite ? 'text-primary' : 'text-muted-foreground/30 hover:text-primary/80'
                              }`}
                            >
                              <Star size={14} fill={isFavorite ? 'currentColor' : 'none'} />
                            </button>

                            {/* Mini preview showing button, card, input */}
                            {style.style_guide && (
                              <div className="w-full overflow-hidden rounded-t-lg" style={{ height: '180px' }}>
                                <StyleCardPreview
                                  guide={style.style_guide}
                                  accentGuide={accentStyleId
                                    ? styles?.find((s: StyleOption) => s.id === accentStyleId)?.style_guide
                                    : undefined}
                                  modifiers={selectedModifiers.length > 0 ? selectedModifiers : undefined}
                                />
                              </div>
                            )}

                            {/* Style name */}
                            <div className="px-2 py-2">
                              <p className="text-xs font-semibold leading-tight truncate">{style.name}</p>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                    </>
                  )}
                </div>

                {/* COLUMN 2a: Accent Style + Modifiers + Color Palette */}
                <div className="w-[240px] shrink-0 border-r border-border/50 overflow-y-auto flex flex-col">
                  {/* Tab switcher */}
                  <div className="shrink-0 flex border-b bg-muted/30">
                    <button
                      onClick={() => setDesignTab('base')}
                      className={`flex-1 py-2 text-[11px] font-semibold text-center transition-colors ${
                        designTab === 'base'
                          ? 'bg-background text-foreground border-b-2 border-primary'
                          : 'text-muted-foreground hover:text-foreground'
                      }`}
                    >
                      Base
                    </button>
                    <button
                      onClick={() => setDesignTab('refine')}
                      className={`flex-1 py-2 text-[11px] font-semibold text-center transition-colors ${
                        designTab === 'refine'
                          ? 'bg-background text-foreground border-b-2 border-primary'
                          : 'text-muted-foreground hover:text-foreground'
                      }`}
                    >
                      Refine
                    </button>
                  </div>

                  <div className="flex-1 overflow-y-auto p-3 space-y-4">
                    {/* ===== BASE TAB ===== */}
                    {designTab === 'base' && (
                      <>
                        {/* Accent Styles -- compact pills */}
                        <div className="space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Accent Style</span>
                            <PillNav
                              onPrev={() => {
                                const opts = styles?.filter((s: StyleOption) => s.id !== styleId) || []
                                if (!opts.length) return
                                const idx = opts.findIndex((s: StyleOption) => s.id === accentStyleId)
                                const prev = (idx <= 0 ? opts.length : idx) - 1
                                setAccentStyleId(opts[prev].id)
                              }}
                              onNext={() => {
                                const opts = styles?.filter((s: StyleOption) => s.id !== styleId) || []
                                if (!opts.length) return
                                const idx = opts.findIndex((s: StyleOption) => s.id === accentStyleId)
                                const next = (idx + 1) % opts.length
                                setAccentStyleId(opts[next].id)
                              }}
                            />
                          </div>
                          <div className="grid grid-cols-3 gap-1.5">
                            {/* None pill */}
                            <button
                              type="button"
                              onClick={() => setAccentStyleId(null)}
                              className={`text-left px-1.5 py-1 rounded border transition-colors ${
                                !accentStyleId
                                  ? 'border-primary bg-primary/10'
                                  : 'border-border hover:border-primary/50'
                              }`}
                            >
                              <span className="text-[10px] font-medium text-muted-foreground">None</span>
                            </button>
                            {/* All styles as possible accents */}
                            {styles?.filter((s: StyleOption) => s.id !== styleId).map((style: StyleOption) => {
                              const swatches = STYLE_SWATCHES[style.id] || ['#3B82F6', '#FFFFFF', '#111827']
                              const isActive = accentStyleId === style.id
                              return (
                                <button
                                  key={style.id}
                                  type="button"
                                  onClick={() => setAccentStyleId(isActive ? null : style.id)}
                                  className={`text-left px-1.5 py-1 rounded border transition-colors ${
                                    isActive
                                      ? 'border-primary bg-primary/10'
                                      : 'border-border hover:border-primary/50'
                                  }`}
                                >
                                  <div className="flex gap-0.5 mb-0.5 flex-wrap">
                                    {swatches.map((color, i) => (
                                      <div
                                        key={i}
                                        className="w-2.5 h-2.5 rounded-full border border-foreground/10"
                                        style={{ backgroundColor: color }}
                                      />
                                    ))}
                                  </div>
                                  <span className="text-[10px] font-medium leading-tight line-clamp-1">{style.name}</span>
                                </button>
                              )
                            })}
                          </div>
                        </div>

                        <div className="border-t" />

                        {/* Modifiers -- compact checkboxes */}
                        {modifiers && modifiers.length > 0 && (
                          <div className="space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Modifiers</span>
                              <PillNav
                                onPrev={() => {
                                  if (!modifiers?.length) return
                                  const currentIdx = modifiers.findIndex(m => selectedModifiers.includes(m.id))
                                  const prev = (currentIdx <= 0 ? modifiers.length : currentIdx) - 1
                                  setSelectedModifiers([modifiers[prev].id])
                                }}
                                onNext={() => {
                                  if (!modifiers?.length) return
                                  const currentIdx = modifiers.findIndex(m => selectedModifiers.includes(m.id))
                                  const next = (currentIdx + 1) % modifiers.length
                                  setSelectedModifiers([modifiers[next].id])
                                }}
                              />
                            </div>
                            <div className="space-y-0.5">
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
                                    className={`w-full text-left px-2 py-1.5 rounded border transition-colors flex items-center gap-1.5 ${
                                      isActive
                                        ? 'border-primary bg-primary/10'
                                        : 'border-border hover:border-primary/50'
                                    }`}
                                    title={mod.description}
                                  >
                                    <div className={`w-3.5 h-3.5 rounded-sm border flex items-center justify-center shrink-0 ${
                                      isActive ? 'bg-primary border-primary' : 'border-muted-foreground/30'
                                    }`}>
                                      {isActive && <Check size={8} className="text-primary-foreground" />}
                                    </div>
                                    <span className="text-[11px] font-medium truncate">{mod.name}</span>
                                  </button>
                                )
                              })}
                            </div>
                          </div>
                        )}

                        <div className="border-t" />

                        {/* Color Palettes */}
                        <div className="space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Color Palette</span>
                            <PillNav
                              onPrev={() => {
                                const idx = PALETTES.findIndex(p => p.id === selectedPaletteId)
                                const prev = (idx <= 0 ? PALETTES.length : idx) - 1
                                setPaletteIndex(prev)
                                setSelectedPaletteId(PALETTES[prev].id)
                                setCustomColors(paletteToCustomColors(PALETTES[prev]))
                              }}
                              onNext={() => {
                                const idx = PALETTES.findIndex(p => p.id === selectedPaletteId)
                                const next = (idx + 1) % PALETTES.length
                                setPaletteIndex(next)
                                setSelectedPaletteId(PALETTES[next].id)
                                setCustomColors(paletteToCustomColors(PALETTES[next]))
                              }}
                            />
                          </div>
                          <div className="grid grid-cols-3 gap-1.5">
                            {PALETTES.map((palette, idx) => {
                              const isActive = selectedPaletteId === palette.id
                              return (
                                <button
                                  key={palette.id}
                                  type="button"
                                  onClick={() => {
                                    setPaletteIndex(idx)
                                    setSelectedPaletteId(palette.id)
                                    setCustomColors(paletteToCustomColors(palette))
                                  }}
                                  className={`px-1.5 py-1.5 rounded border transition-colors ${
                                    isActive
                                      ? 'border-primary bg-primary/10'
                                      : 'border-border hover:border-primary/50'
                                  }`}
                                  title={palette.name}
                                >
                                  <div className="flex gap-1 justify-center mb-1 flex-wrap">
                                    {[palette.brand, palette.background, palette.surface, palette.text, palette.accent, palette.muted].map((c, i) => (
                                      <div
                                        key={i}
                                        className="w-3.5 h-3.5 rounded-full border border-foreground/10"
                                        style={{ backgroundColor: c }}
                                      />
                                    ))}
                                  </div>
                                  <span className="text-[10px] font-medium leading-tight line-clamp-1 text-center block">{palette.name}</span>
                                </button>
                              )
                            })}
                          </div>
                          {selectedPaletteId && (
                            <button
                              type="button"
                              onClick={() => {
                                setSelectedPaletteId(null)
                                setCustomColors({})
                              }}
                              className="w-full text-[9px] text-muted-foreground hover:text-foreground transition-colors text-center"
                            >
                              Reset to style default
                            </button>
                          )}
                        </div>

                      </>
                    )}

                    {/* ===== REFINE TAB ===== */}
                    {designTab === 'refine' && (
                      <div className="space-y-3">
                        {REFINEMENT_GROUPS.map((group) => (
                          <div key={group.key} className="space-y-1">
                            <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                              {group.label}
                            </span>
                            <p className="text-[9px] text-muted-foreground leading-tight mb-1">
                              {group.description}
                            </p>
                            <div className="flex flex-wrap gap-1">
                              {group.options.map((option) => {
                                const isActive = refinement[group.key] === option.value
                                return (
                                  <button
                                    key={option.value}
                                    type="button"
                                    onClick={() => setRefinement(prev => ({ ...prev, [group.key]: option.value }))}
                                    className={`px-1.5 py-0.5 rounded border text-[10px] font-medium transition-colors ${
                                      isActive
                                        ? 'border-primary bg-primary/10 text-foreground'
                                        : 'border-border text-muted-foreground hover:border-primary/50 hover:text-foreground'
                                    }`}
                                    title={option.description}
                                  >
                                    {option.label}
                                  </button>
                                )
                              })}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* COLUMN 2b: Fonts + Customize Colors */}
                <div className="w-[240px] shrink-0 border-r border-border/50 overflow-y-auto p-3 space-y-3">
                  {/* Font Selection */}
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Font</span>
                      <PillNav
                        onPrev={() => {
                          const idx = FONT_OPTIONS.findIndex(f => f.id === selectedFontId)
                          const prev = (idx <= 0 ? FONT_OPTIONS.length : idx) - 1
                          setSelectedFontId(FONT_OPTIONS[prev].id)
                        }}
                        onNext={() => {
                          const idx = FONT_OPTIONS.findIndex(f => f.id === selectedFontId)
                          const next = (idx + 1) % FONT_OPTIONS.length
                          setSelectedFontId(FONT_OPTIONS[next].id)
                        }}
                      />
                    </div>
                    <div className="grid grid-cols-3 gap-1.5">
                      {FONT_OPTIONS.map((font) => {
                        const isActive = selectedFontId === font.id
                        return (
                          <button
                            key={font.id}
                            type="button"
                            onClick={() => setSelectedFontId(isActive ? null : font.id)}
                            className={`text-left px-1.5 py-1 rounded border transition-colors ${
                              isActive
                                ? 'border-primary bg-primary/10'
                                : 'border-border hover:border-primary/50'
                            }`}
                          >
                            <span
                              className="text-[11px] font-medium leading-tight block truncate"
                              style={{ fontFamily: font.family }}
                            >
                              {font.name}
                            </span>
                            <span className="text-[8px] text-muted-foreground">{font.category}</span>
                          </button>
                        )
                      })}
                    </div>
                  </div>

                  <div className="border-t border-border/50" />

                  {/* Color Customizer (individual tweaks) — always visible */}
                  <ColorCustomizer
                    styleGuide={(styles?.find((s: StyleOption) => s.id === styleId)?.style_guide) ?? DEFAULT_STYLE_GUIDE}
                    customColors={customColors}
                    onChange={setCustomColors}
                    selectedPaletteId={selectedPaletteId}
                    onPaletteSelect={setSelectedPaletteId}
                  />
                </div>

                {/* COLUMN 3: AI Design Guide */}
                <DesignGuidePanel
                  onAction={handleDesignGuideAction}
                />

                {/* COLUMN 4: Preview (keep existing quad/single view) */}
                <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
                  {/* View controls bar */}
                  <div className="shrink-0 flex items-center gap-2 px-3 py-1.5 border-b bg-muted/30">
                    <div className="flex bg-muted rounded-lg p-0.5">
                      <button
                        onClick={() => setPreviewViewMode('quad')}
                        className={`flex items-center gap-1 px-2 py-0.5 text-[10px] font-medium rounded-md transition-colors ${
                          previewViewMode === 'quad' ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground'
                        }`}
                      >
                        <Grid2x2 size={11} />
                        Quad
                      </button>
                      <button
                        onClick={() => setPreviewViewMode('single')}
                        className={`flex items-center gap-1 px-2 py-0.5 text-[10px] font-medium rounded-md transition-colors ${
                          previewViewMode === 'single' ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground'
                        }`}
                      >
                        <Maximize2 size={11} />
                        Single
                      </button>
                    </div>
                    {previewViewMode === 'single' && (
                      <div className="flex gap-1 ml-1">
                        {(['landing', 'dashboard', 'settings', 'feed'] as PreviewPage[]).map((p) => (
                          <button
                            key={p}
                            onClick={() => setPreviewPage(p)}
                            className={`px-1.5 py-0.5 text-[10px] font-medium rounded-md transition-colors ${
                              previewPage === p ? 'bg-primary/10 text-foreground' : 'text-muted-foreground hover:bg-muted'
                            }`}
                          >
                            {p.charAt(0).toUpperCase() + p.slice(1)}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Favorites bar */}
                  {favoriteStyles.size > 0 && (
                    <div className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 border-b bg-primary/5">
                      <Star size={10} className="text-primary shrink-0" fill="currentColor" />
                      <span className="text-[9px] font-medium text-muted-foreground shrink-0">Favorites:</span>
                      <div className="flex gap-1 overflow-x-auto">
                        {Array.from(favoriteStyles).map(favId => {
                          const favStyle = styles?.find((s: StyleOption) => s.id === favId)
                          if (!favStyle) return null
                          const swatches = STYLE_SWATCHES[favId] || ['#3B82F6', '#FFFFFF', '#111827']
                          const isActive = styleId === favId
                          return (
                            <button
                              key={favId}
                              type="button"
                              onClick={() => handleStyleSelect(favId)}
                              className={`shrink-0 flex items-center gap-1 px-1.5 py-0.5 rounded border transition-colors ${
                                isActive ? 'border-primary bg-primary/10' : 'border-border hover:border-primary/50'
                              }`}
                            >
                              <div className="flex gap-0.5 flex-wrap">
                                {swatches.map((color, i) => (
                                  <div
                                    key={i}
                                    className="w-2.5 h-2.5 rounded-sm border border-foreground/10"
                                    style={{ backgroundColor: color }}
                                  />
                                ))}
                              </div>
                              <span className="text-[9px] font-medium">{favStyle.name}</span>
                            </button>
                          )
                        })}
                      </div>
                    </div>
                  )}

                  {/* Preview area */}
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
                        const quadPages: { id: PreviewPage; label: string }[] = [
                          { id: 'landing', label: 'Landing' },
                          { id: 'dashboard', label: 'Dashboard' },
                          { id: 'feed', label: 'Feed' },
                          { id: 'settings', label: 'Settings' },
                        ]
                        return (
                          <div
                            ref={quadGridRef}
                            className="w-full h-full grid grid-cols-2 grid-rows-2 p-2"
                            style={{ gap: '6px' }}
                          >
                            {quadPages.map((page) => (
                              <div
                                key={page.id}
                                className="relative overflow-hidden cursor-pointer group rounded-md border-2 border-border"
                                onClick={() => {
                                  setPreviewPage(page.id)
                                  setPreviewViewMode('single')
                                }}
                              >
                                <div className="absolute top-1.5 left-1.5 z-10 px-1.5 py-0.5 rounded text-[9px] font-semibold bg-foreground/60 text-background backdrop-blur-sm pointer-events-none">
                                  {page.label}
                                </div>
                                <div className="absolute top-1.5 right-1.5 z-10 opacity-0 group-hover:opacity-100 transition-opacity p-0.5 rounded bg-foreground/60 text-background backdrop-blur-sm pointer-events-none">
                                  <Maximize2 size={10} />
                                </div>
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
                        Select a style to preview
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

          </div>
        )}

        {/* ---------------------------------------------------------------- */}
        {/* Step 5: GitHub Repo (Optional)                                   */}
        {/* ---------------------------------------------------------------- */}
        {step === 'github' && (
          <div className="flex-1 flex items-center justify-center p-6">
            <div className="w-full max-w-lg space-y-4">
              <div className="mb-2">
                <h2 className="text-2xl font-semibold mb-1">GitHub Repository</h2>
                <p className="text-sm text-muted-foreground">
                  Create a GitHub repo for your project. This step is optional.
                </p>
              </div>

              {/* Token input */}
              <div className="space-y-2">
                <Label htmlFor="github-token" className="text-sm font-medium">
                  Personal Access Token
                </Label>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Input
                      id="github-token"
                      type={githubShowToken ? 'text' : 'password'}
                      placeholder="ghp_xxxxxxxxxxxx"
                      value={githubToken}
                      onChange={(e) => {
                        setGithubToken(e.target.value)
                        setGithubTokenError(null)
                        setGithubUser(null)
                      }}
                      disabled={githubTokenValidating || !!githubUser}
                      className="pr-9"
                    />
                    <button
                      type="button"
                      onClick={() => setGithubShowToken(!githubShowToken)}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {githubShowToken ? <EyeOff size={14} /> : <Eye size={14} />}
                    </button>
                  </div>
                  {!githubUser ? (
                    <Button
                      onClick={handleGithubValidateToken}
                      disabled={githubTokenValidating || !githubToken.trim()}
                      size="sm"
                    >
                      {githubTokenValidating ? (
                        <>
                          <Loader2 size={14} className="animate-spin" />
                          Validating
                        </>
                      ) : (
                        'Validate'
                      )}
                    </Button>
                  ) : (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setGithubUser(null)
                        setGithubToken('')
                        setGithubRepoUrl(null)
                        setGithubRepoError(null)
                        localStorage.removeItem('github_token')
                      }}
                    >
                      Change
                    </Button>
                  )}
                </div>
                {githubTokenError && (
                  <p className="text-xs text-destructive">{githubTokenError}</p>
                )}
                <p className="text-xs text-muted-foreground">
                  Needs <code className="px-1 py-0.5 bg-muted rounded text-[10px]">repo</code> scope.{' '}
                  <a
                    href="https://github.com/settings/tokens/new?scopes=repo&description=AutoForge"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline inline-flex items-center gap-0.5"
                  >
                    Create one <ExternalLink size={10} />
                  </a>
                </p>
              </div>

              {/* Authenticated user info */}
              {githubUser && (
                <Card>
                  <CardContent className="p-3">
                    <div className="flex items-center gap-3">
                      {githubUser.avatar_url && (
                        <img
                          src={githubUser.avatar_url}
                          alt={githubUser.login}
                          className="w-8 h-8 rounded-full border"
                        />
                      )}
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-sm">{githubUser.login}</div>
                        {githubUser.name && (
                          <div className="text-xs text-muted-foreground truncate">{githubUser.name}</div>
                        )}
                      </div>
                      <CheckCircle2 size={16} className="text-green-500 shrink-0" />
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Repo creation section (only after token validated) */}
              {githubUser && !githubRepoUrl && (
                <div className="space-y-3 pt-2">
                  <div className="flex items-center justify-between">
                    <Label className="text-sm font-medium">Repository Name</Label>
                    <Badge variant="secondary" className="font-mono text-xs">
                      {githubUser.login}/{projectName.trim().toLowerCase().replace(/[^a-z0-9_-]/g, '-')}
                    </Badge>
                  </div>

                  <div className="flex items-center justify-between">
                    <Label className="text-sm font-medium">Visibility</Label>
                    <button
                      type="button"
                      onClick={() => setGithubRepoPrivate(!githubRepoPrivate)}
                      className="flex items-center gap-1.5 text-sm px-2 py-1 rounded-md border hover:bg-muted transition-colors"
                    >
                      {githubRepoPrivate ? (
                        <>
                          <Lock size={12} />
                          Private
                        </>
                      ) : (
                        <>
                          <Unlock size={12} />
                          Public
                        </>
                      )}
                    </button>
                  </div>

                  {boilerplateId && boilerplateId !== 'scratch' && (
                    <p className="text-xs text-muted-foreground">
                      Will be created from the{' '}
                      <span className="font-medium text-foreground">
                        {boilerplateCategories?.flatMap((c) => c.options).find((o) => o.id === boilerplateId)?.name}
                      </span>{' '}
                      template.
                    </p>
                  )}

                  <Button
                    onClick={handleGithubCreateRepo}
                    disabled={githubRepoCreating}
                    className="w-full"
                  >
                    {githubRepoCreating ? (
                      <>
                        <Loader2 size={14} className="animate-spin" />
                        Creating Repository...
                      </>
                    ) : (
                      <>
                        <Github size={14} />
                        Create GitHub Repository
                      </>
                    )}
                  </Button>

                  {githubRepoError && (
                    <Alert variant="destructive">
                      <AlertDescription>{githubRepoError}</AlertDescription>
                    </Alert>
                  )}
                </div>
              )}

              {/* Success state */}
              {githubRepoUrl && (
                <Card className="border-green-500/50 bg-green-500/5">
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3">
                      <CheckCircle2 size={20} className="text-green-500 shrink-0 mt-0.5" />
                      <div className="flex-1 min-w-0 space-y-1">
                        <div className="font-medium text-sm">Repository created</div>
                        <a
                          href={githubRepoUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-primary hover:underline inline-flex items-center gap-1 break-all"
                        >
                          {githubRepoUrl}
                          <ExternalLink size={10} />
                        </a>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Navigation */}
              <div className="flex justify-between pt-2">
                <Button variant="ghost" onClick={handleBack}>
                  <ArrowLeft size={16} />
                  Back
                </Button>
                <div className="flex gap-2">
                  <Button variant="outline" onClick={handleGithubSkip}>
                    Skip
                  </Button>
                  {githubRepoUrl && (
                    <Button onClick={handleGithubContinue}>
                      Continue
                      <ArrowRight size={16} />
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ---------------------------------------------------------------- */}
        {/* Step 6: Spec Method                                              */}
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
