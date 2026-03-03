/**
 * DunkStackPage - File-based context mechanism workspace.
 *
 * Full-page layout at /#/dunkstack providing:
 * - Context gauge (real-time token tracking with color-coded zones)
 * - File-based walkie-talkie chat (reads/writes .agent/comms/ files)
 * - 3-tier context safety system (warning / handoff / hard stop)
 * - Session control (idle / continue / autopilot)
 * - Bridge save for session continuity
 * - Theme selector and dark mode toggle (own copies on this page)
 *
 * Mirrors the workspace page layout but adapted for the file-based
 * context management mechanism described in the BASE_BUILD_PRD.
 */

import { useState, useCallback, useEffect, useRef } from 'react'
import {
  ArrowLeft,
  BookOpen,
  Sun,
  Moon,
  Shield,
  FileText,
  Layers,
  ChevronLeft,
  ChevronRight,
  FolderOpen,
  Cpu,
  Sparkles,
  Play,
  Square,
  Loader2,
  Globe,
  Plus,
  Check,
  X,
  Menu,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ThemeSelector } from '@/components/ThemeSelector'
import { useTheme } from '@/hooks/useTheme'
import { useProjects, useCreateProject } from '@/hooks/useProjects'
import { useDunkStack } from '@/hooks/useDunkStack'
import { dunkstackUpdateModelPreset } from '@/lib/api'
import { DunkStackContextGauge } from '@/components/dunkstack/DunkStackContextGauge'
import { DunkStackAgentView } from '@/components/dunkstack/DunkStackAgentView'
import { DunkStackSafetyPanel } from '@/components/dunkstack/DunkStackSafetyPanel'
import { DunkStackGuidePanel } from '@/components/dunkstack/DunkStackGuidePanel'
import { IntakeDock } from '@/components/appbuilder/IntakeDock'
import { AgentOSChat } from '@/components/appbuilder/AgentOSChat'
import { StandardsPanel } from '@/components/appbuilder/StandardsPanel'
import { ProductPanel } from '@/components/appbuilder/ProductPanel'
import { SpecCards } from '@/components/appbuilder/SpecCards'
import { GapAnalysisPanel } from '@/components/appbuilder/GapAnalysisPanel'
import { ExpandPanel } from '@/components/appbuilder/ExpandPanel'
import {
  useFeatures,
  useGaps,
  useResolveGap,
  useAutoResolveGaps,
} from '@/hooks/useAgentOS'
import { DunkStackPreviewPanel } from '@/components/dunkstack/DunkStackPreviewPanel'

type RightPanel = 'safety' | 'files' | 'agent-os' | 'preview' | null
type CenterView = 'chat' | 'agent-os-intake' | 'agent-os-workflow'

type ModelPreset = { model: string; context: string; label: string; limit: number; color: string }

const MODEL_PRESETS: ModelPreset[] = [
  { model: 'opus', context: '200k', label: 'Opus 4.6 \u00b7 200K', limit: 200000, color: 'bg-zinc-700' },
  { model: 'opus', context: '1m', label: 'Opus 4.6 \u00b7 1M', limit: 1000000, color: 'bg-blue-600' },
  { model: 'sonnet', context: '1m', label: 'Sonnet 4.6 \u00b7 1M', limit: 1000000, color: 'bg-violet-600' },
]

function getStoredModelPreset(): number {
  try {
    const stored = localStorage.getItem('dunkstack-model-preset')
    if (stored !== null) {
      const idx = parseInt(stored, 10)
      if (idx >= 0 && idx < MODEL_PRESETS.length) return idx
    }
  } catch { /* ignore localStorage errors */ }
  return 0
}

function getStoredProject(): string | null {
  try {
    return localStorage.getItem('dunkstack-selected-project')
  } catch { /* ignore localStorage errors */ }
  return null
}

export function DunkStackPage(): React.JSX.Element {
  const { theme, setTheme, darkMode, toggleDarkMode, themes } = useTheme()
  const {
    commsLog,
    sendMessage,
    controlMode,
    setControlMode,
    tokenState,
    resetTokens,
    safetyStatus,
    config,
    saveBridge,
    agentStatus,
    startAgent,
    stopAgent,
    sendToAgent,
    agentStarting,
    agentEvents: hookAgentEvents,
    connected,
    loading,
  } = useDunkStack()
  const { data: projects } = useProjects()
  const createProject = useCreateProject()

  const [rightPanel, setRightPanel] = useState<RightPanel>('safety')
  const [showGuide, setShowGuide] = useState(false)
  const [modelPresetIndex, setModelPresetIndex] = useState(getStoredModelPreset)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false)
  const [selectedProject, setSelectedProject] = useState<string | null>(getStoredProject)

  // New project inline form state
  const [showNewProject, setShowNewProject] = useState(false)
  const [newProjectName, setNewProjectName] = useState('')
  const [newProjectError, setNewProjectError] = useState('')

  const handleCreateProject = useCallback(async () => {
    const raw = newProjectName.trim()
    if (!raw) { setNewProjectError('Name required'); return }
    // Auto-sanitize: lowercase, replace spaces/special chars with hyphens
    const name = raw.toLowerCase().replace(/[^a-z0-9_-]/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '')
    if (!name) { setNewProjectError('Invalid name'); return }
    // Auto-generate path on server
    const path = `/home/user/${name}`
    setNewProjectError('')
    try {
      await createProject.mutateAsync({ name, path, specMethod: 'manual' })
      setSelectedProject(name)
      localStorage.setItem('dunkstack-selected-project', name)
      setShowNewProject(false)
      setNewProjectName('')
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      setNewProjectError(msg)
    }
  }, [newProjectName, createProject, setSelectedProject])
  const [centerView, setCenterView] = useState<CenterView>('chat')
  const [standardsPanelOpen, setStandardsPanelOpen] = useState(true)
  const [productPanelOpen, setProductPanelOpen] = useState(false)
  const [previewWidth, setPreviewWidth] = useState(520) // default preview panel width in px
  const [previewHalf, setPreviewHalf] = useState(false) // half-screen toggle
  const rightPanelDragRef = useRef(false)

  /** Drag handler for resizable right panel (preview). */
  const handleRightPanelDragStart = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    rightPanelDragRef.current = true
    const onMove = (ev: MouseEvent) => {
      if (!rightPanelDragRef.current) return
      const newWidth = window.innerWidth - ev.clientX
      setPreviewWidth(Math.min(window.innerWidth * 0.85, Math.max(300, newWidth)))
      setPreviewHalf(false) // user is manually dragging, disable half snap
    }
    const onUp = () => {
      rightPanelDragRef.current = false
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseup', onUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
    document.addEventListener('mousemove', onMove)
    document.addEventListener('mouseup', onUp)
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }, [])

  // Agent OS data hooks (only active when a project is selected and in agent-os view)
  const isAgentOSView = centerView === 'agent-os-intake' || centerView === 'agent-os-workflow'
  const { data: featuresData } = useFeatures(isAgentOSView && selectedProject ? selectedProject : '')
  const { data: gapsData } = useGaps(isAgentOSView && selectedProject ? selectedProject : '')
  const resolveGap = useResolveGap(selectedProject || '')
  const autoResolveGaps = useAutoResolveGaps(selectedProject || '')

  /** Switch model preset: persist to localStorage and push config to backend.
   *  Uses the dedicated model-preset endpoint which auto-derives billing mode:
   *  200K = subscription (free), 1M = API key (paid). */
  const handleModelPresetChange = useCallback(async (index: number) => {
    setModelPresetIndex(index)
    localStorage.setItem('dunkstack-model-preset', String(index))
    const preset = MODEL_PRESETS[index]
    const modelId = preset.model === 'opus' ? 'claude-opus-4-6' : 'claude-sonnet-4-6'
    try {
      await dunkstackUpdateModelPreset(modelId, preset.limit)
    } catch {
      // Config update is best-effort; the UI still reflects the choice
    }
  }, [])

  /** Select a project and persist choice. */
  const handleSelectProject = useCallback((name: string) => {
    setSelectedProject(name)
    localStorage.setItem('dunkstack-selected-project', name)
  }, [])

  /** Start the coding agent for the selected project. */
  const handleStartAgent = useCallback(async () => {
    if (!selectedProject) return
    const preset = MODEL_PRESETS[modelPresetIndex]
    const modelId = preset.model === 'opus' ? 'claude-opus-4-6' : 'claude-sonnet-4-6'
    await startAgent(selectedProject, modelId, preset.limit)
  }, [selectedProject, modelPresetIndex, startAgent])

  /** Start/stop the coding agent for the selected project. */
  const handleToggleAgent = useCallback(async () => {
    if (!selectedProject) return
    if (agentStatus?.status === 'running') {
      await stopAgent(selectedProject)
    } else {
      await handleStartAgent()
    }
  }, [selectedProject, agentStatus, handleStartAgent, stopAgent])

  /** Send a message to the agent via the API call. */
  const handleSendToAgent = useCallback(async (message: string) => {
    if (!selectedProject) return
    await sendToAgent(selectedProject, message)
  }, [selectedProject, sendToAgent])

  const isAgentRunning = agentStatus?.status === 'running'

  const handleToggleRightPanel = useCallback((panel: RightPanel) => {
    setRightPanel(prev => prev === panel ? null : panel)
  }, [])

  const cum = tokenState?.cumulative ?? {
    input_tokens: 0,
    output_tokens: 0,
    cache_read_tokens: 0,
    cache_creation_tokens: 0,
    total_cost_usd: 0,
    api_calls: 0,
  }
  const totalTokens = cum.input_tokens + cum.output_tokens

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Breadcrumb navigation bar */}
      <div className="flex items-center h-10 px-2 md:px-3 border-b border-border bg-card shrink-0 overflow-x-auto">
        {/* Mobile: hamburger toggle for sidebar */}
        <Button
          variant="ghost"
          size="sm"
          className="md:hidden shrink-0 p-1.5"
          onClick={() => setMobileSidebarOpen(prev => !prev)}
          title="Toggle project sidebar"
        >
          <Menu size={16} />
        </Button>

        {/* Left: back button + page title */}
        <div className="flex items-center gap-2 shrink-0">
          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5 text-xs"
            onClick={() => { window.location.hash = '' }}
          >
            <ArrowLeft size={14} />
            <span className="hidden sm:inline">AutoForge</span>
          </Button>
          <span className="text-muted-foreground/30 hidden sm:inline">/</span>
          <div className="flex items-center gap-1.5">
            <Layers size={14} className="text-primary" />
            <span className="text-sm font-bold text-foreground tracking-tight">DunkStack</span>
          </div>
        </div>

        {/* Model preset pills — hidden on mobile */}
        <div className="hidden md:flex items-center gap-1 ml-4">
          <Cpu size={13} className="text-muted-foreground mr-1" />
          {MODEL_PRESETS.map((preset, idx) => (
            <button
              key={`${preset.model}-${preset.context}`}
              onClick={() => handleModelPresetChange(idx)}
              className={`px-2.5 py-0.5 rounded-full text-[11px] font-semibold transition-colors ${
                idx === modelPresetIndex
                  ? `${preset.color} text-white shadow-sm`
                  : 'bg-muted/50 text-muted-foreground hover:bg-muted'
              }`}
              title={`Switch to ${preset.label}`}
            >
              {preset.label}
            </button>
          ))}
        </div>

        {/* Center spacer */}
        <div className="flex-1 min-w-2" />

        {/* Right: controls */}
        <div className="flex items-center gap-1 md:gap-2 shrink-0">
          {/* Right panel toggles — hidden on mobile (panels are hidden too) */}
          <div className="hidden md:flex items-center gap-2">
            {/* Safety panel toggle */}
            <Button
              variant={rightPanel === 'safety' ? 'default' : 'ghost'}
              size="sm"
              className="gap-1.5 text-xs"
              onClick={() => handleToggleRightPanel('safety')}
              title="Toggle Safety Panel"
            >
              <Shield size={14} />
              <span className="hidden sm:inline">Safety</span>
            </Button>

            {/* File viewer toggle */}
            <Button
              variant={rightPanel === 'files' ? 'default' : 'ghost'}
              size="sm"
              className="gap-1.5 text-xs"
              onClick={() => handleToggleRightPanel('files')}
              title="Toggle File Viewer"
            >
              <FileText size={14} />
              <span className="hidden sm:inline">Files</span>
            </Button>

            {/* Live Preview toggle */}
            <Button
              variant={rightPanel === 'preview' ? 'default' : 'ghost'}
              size="sm"
              className="gap-1.5 text-xs"
              onClick={() => handleToggleRightPanel('preview')}
              title="Toggle Live Preview"
            >
              <Globe size={14} />
              <span className="hidden sm:inline">Preview</span>
            </Button>

            {/* Agent OS toggle */}
            <Button
              variant={isAgentOSView ? 'default' : 'ghost'}
              size="sm"
              className="gap-1.5 text-xs"
              onClick={() => {
                if (isAgentOSView) {
                  setCenterView('chat')
                  setRightPanel('safety')
                } else {
                  setCenterView('agent-os-intake')
                  setRightPanel('agent-os')
                }
              }}
              title="Toggle Agent OS PRD Creator"
            >
              <Sparkles size={14} />
              <span className="hidden sm:inline">Agent OS</span>
            </Button>

            {/* Separator */}
            <div className="w-px h-5 bg-border mx-1" />
          </div>

          {/* Guide */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowGuide(prev => !prev)}
            title="Guide"
          >
            <BookOpen size={14} />
          </Button>

          {/* Theme Selector — hidden on small mobile */}
          <div className="hidden sm:block">
            <ThemeSelector
              themes={themes}
              currentTheme={theme}
              onThemeChange={setTheme}
            />
          </div>

          {/* Dark Mode Toggle */}
          <Button
            onClick={toggleDarkMode}
            variant="outline"
            size="sm"
            title="Toggle dark mode"
            aria-label="Toggle dark mode"
          >
            {darkMode ? <Sun size={16} /> : <Moon size={16} />}
          </Button>
        </div>
      </div>

      {/* Context Gauge */}
      <DunkStackContextGauge
        totalTokens={totalTokens}
        modelLimit={tokenState?.model_limit ?? 200000}
        inputTokens={cum.input_tokens}
        outputTokens={cum.output_tokens}
        cacheReadTokens={cum.cache_read_tokens}
        totalCost={cum.total_cost_usd}
        apiCalls={cum.api_calls}
        mode={tokenState?.mode ?? 'subscription'}
        safety={safetyStatus}
        onReset={resetTokens}
      />

      {/* Agent Control Bar */}
      {selectedProject && (
        <div className="flex items-center h-9 px-2 md:px-3 border-b border-border bg-card/80 shrink-0 gap-2 md:gap-3 overflow-x-auto">
          <Button
            variant={isAgentRunning ? 'destructive' : 'default'}
            size="sm"
            className="gap-1.5 text-xs h-7 shrink-0"
            onClick={handleToggleAgent}
            disabled={agentStarting || !selectedProject}
          >
            {agentStarting ? (
              <Loader2 size={13} className="animate-spin" />
            ) : isAgentRunning ? (
              <Square size={13} />
            ) : (
              <Play size={13} />
            )}
            <span className="hidden sm:inline">
              {agentStarting ? 'Starting...' : isAgentRunning ? 'Stop Agent' : 'Start Agent'}
            </span>
          </Button>

          <div className="flex items-center gap-1.5 min-w-0">
            <span className={`w-2 h-2 rounded-full shrink-0 ${
              isAgentRunning ? 'bg-emerald-500 animate-pulse' :
              agentStarting ? 'bg-amber-500 animate-pulse' :
              agentStatus?.status === 'error' ? 'bg-red-500' :
              'bg-zinc-400'
            }`} />
            <span className="text-[11px] text-muted-foreground truncate">
              {agentStarting ? 'Starting...' :
               isAgentRunning ? `Running · ${agentStatus?.model_id ?? ''}` :
               agentStatus?.status === 'error' ? `Error` :
               'Idle'}
            </span>
          </div>

          <div className="flex-1 min-w-1" />

          <span className="text-[10px] text-muted-foreground shrink-0 hidden sm:block">
            {selectedProject}
          </span>
        </div>
      )}

      {/* Mobile sidebar backdrop overlay */}
      {mobileSidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}

      {/* Main content area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left sidebar: project list
            - On mobile (<md): fixed overlay drawer controlled by mobileSidebarOpen
            - On desktop (md+): inline with collapse toggle */}
        {sidebarCollapsed && !mobileSidebarOpen ? (
          <button
            onClick={() => setSidebarCollapsed(false)}
            className="hidden md:flex shrink-0 w-8 items-center justify-center border-r border-border bg-card/40 hover:bg-card transition-colors"
            title="Expand project sidebar"
          >
            <ChevronRight size={14} className="text-muted-foreground" />
          </button>
        ) : (
          <div className={`
            ${mobileSidebarOpen
              ? 'fixed inset-y-0 left-0 z-50 w-72 shadow-xl'
              : 'hidden md:flex w-64'
            }
            shrink-0 border-r border-border bg-card/60 flex flex-col overflow-hidden
          `}>
            {/* Sidebar header */}
            <div className="flex items-center justify-between px-3 py-2 border-b border-border shrink-0">
              <div className="flex items-center gap-1.5">
                <FolderOpen size={14} className="text-primary" />
                <span className="text-xs font-bold text-foreground">Projects</span>
              </div>
              <div className="flex items-center gap-1">
                {/* Close button on mobile */}
                <button
                  onClick={() => setMobileSidebarOpen(false)}
                  className="md:hidden p-1 rounded hover:bg-muted text-muted-foreground"
                  title="Close sidebar"
                >
                  <X size={14} />
                </button>
                {/* Collapse button on desktop */}
                <button
                  onClick={() => setSidebarCollapsed(true)}
                  className="hidden md:block p-1 rounded hover:bg-muted text-muted-foreground"
                  title="Collapse sidebar"
                >
                  <ChevronLeft size={14} />
                </button>
              </div>
            </div>

            {/* New Project button / form */}
            <div className="px-2 py-1.5 border-b border-border shrink-0">
              {!showNewProject ? (
                <button
                  onClick={() => setShowNewProject(true)}
                  className="w-full flex items-center gap-1.5 px-2 py-1.5 text-xs font-semibold rounded border-2 border-dashed border-muted-foreground/30 hover:border-primary hover:bg-primary/5 text-muted-foreground hover:text-primary transition-colors"
                >
                  <Plus size={14} />
                  New Project
                </button>
              ) : (
                <div className="space-y-1.5">
                  <input
                    type="text"
                    placeholder="Project name (e.g. my-app)"
                    value={newProjectName}
                    onChange={e => setNewProjectName(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleCreateProject()}
                    className="w-full px-2 py-1 text-xs border border-border rounded bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                    autoFocus
                  />
                  {newProjectName.trim() && (
                    <div className="text-[10px] text-muted-foreground px-0.5">
                      /home/user/{newProjectName.trim().toLowerCase().replace(/[^a-z0-9_-]/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '') || '...'}
                    </div>
                  )}
                  {newProjectError && (
                    <div className="text-[10px] text-red-500 px-0.5">{newProjectError}</div>
                  )}
                  <div className="flex gap-1">
                    <button
                      onClick={handleCreateProject}
                      disabled={createProject.isPending}
                      className="flex-1 flex items-center justify-center gap-1 px-2 py-1 text-xs font-semibold rounded bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                    >
                      <Check size={12} />
                      {createProject.isPending ? 'Creating...' : 'Create'}
                    </button>
                    <button
                      onClick={() => { setShowNewProject(false); setNewProjectError(''); setNewProjectName('') }}
                      className="px-2 py-1 text-xs rounded border border-border hover:bg-muted text-muted-foreground"
                    >
                      <X size={12} />
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Project list */}
            <div className="flex-1 overflow-y-auto py-1">
              {!projects || projects.length === 0 ? (
                <div className="px-3 py-4 text-center text-xs text-muted-foreground">
                  No projects registered
                </div>
              ) : (
                projects.map(proj => (
                  <button
                    key={proj.name}
                    onClick={() => {
                      handleSelectProject(proj.name)
                      // Auto-close sidebar on mobile after selection
                      setMobileSidebarOpen(false)
                    }}
                    className={`w-full text-left px-3 py-2 transition-colors ${
                      selectedProject === proj.name
                        ? 'bg-primary/10 border-l-2 border-primary'
                        : 'hover:bg-muted/50 border-l-2 border-transparent'
                    }`}
                  >
                    <div className="text-xs font-semibold text-foreground truncate">{proj.name}</div>
                    <div className="text-[10px] text-muted-foreground mt-0.5">
                      {proj.stats.passing}/{proj.stats.total} features
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>
        )}

        {/* Main content area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {centerView === 'chat' && (
            loading ? (
              <div className="flex items-center justify-center h-full">
                <div className="flex flex-col items-center gap-3">
                  <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                  <span className="text-sm text-muted-foreground">Loading DunkStack...</span>
                </div>
              </div>
            ) : (
              /* Always show split screen: API Call (left) + Walkie-Talkie (right) */
              <DunkStackAgentView
                agentEvents={hookAgentEvents}
                commsLog={commsLog}
                onSendMessage={sendMessage}
                controlMode={controlMode}
                connected={connected}
                modelId={agentStatus?.model_id}
                isRunning={isAgentRunning}
                onStartAgent={handleStartAgent}
                onSendToAgent={handleSendToAgent}
                agentStarting={agentStarting}
                projectName={selectedProject ?? undefined}
                onStopAgent={handleToggleAgent}
              />
            )
          )}

          {centerView === 'agent-os-intake' && selectedProject && (
            <div className="flex-1 overflow-y-auto">
              <IntakeDock
                projectName={selectedProject}
                onProcessComplete={() => setCenterView('agent-os-workflow')}
                onSkip={() => setCenterView('agent-os-workflow')}
              />
            </div>
          )}

          {centerView === 'agent-os-workflow' && selectedProject && (
            <AgentOSChat
              projectName={selectedProject}
              onComplete={() => {
                setCenterView('chat')
                setRightPanel('safety')
              }}
              onCancel={() => setCenterView('agent-os-intake')}
            />
          )}

          {isAgentOSView && !selectedProject && (
            <div className="flex items-center justify-center h-full">
              <p className="text-sm text-muted-foreground">Select a project from the sidebar to start Agent OS</p>
            </div>
          )}
        </div>

        {/* Right panel — hidden on mobile */}
        {rightPanel && (
          <>
          {/* Drag handle for resizable preview panel */}
          {rightPanel === 'preview' && (
            <div
              onMouseDown={handleRightPanelDragStart}
              className="hidden md:flex w-1.5 shrink-0 cursor-col-resize bg-border/50 hover:bg-primary/30 transition-colors items-center justify-center"
            >
              <div className="h-8 w-0.5 rounded-full bg-muted-foreground/30" />
            </div>
          )}
          <div
            className={`hidden md:flex md:flex-col shrink-0 border-l border-border bg-card/60 ${
              rightPanel !== 'preview' ? 'w-full md:w-[320px]' : ''
            } ${rightPanel === 'preview' ? 'overflow-hidden' : 'overflow-y-auto'}`}
            style={rightPanel === 'preview' ? { width: previewHalf ? '50vw' : `${previewWidth}px` } : undefined}
          >
            {rightPanel === 'safety' && (
              <DunkStackSafetyPanel
                safety={safetyStatus}
                config={config}
                controlMode={controlMode}
                onSetControlMode={setControlMode}
                onSaveBridge={saveBridge}
                usagePercent={tokenState?.usage_percent ?? 0}
              />
            )}
            {rightPanel === 'files' && (
              <FileViewer />
            )}
            {rightPanel === 'preview' && selectedProject && (
              <DunkStackPreviewPanel
                projectName={selectedProject}
                isHalf={previewHalf}
                onToggleHalf={() => setPreviewHalf(prev => !prev)}
              />
            )}
            {rightPanel === 'preview' && !selectedProject && (
              <div className="flex items-center justify-center h-full">
                <p className="text-sm text-muted-foreground">Select a project to preview</p>
              </div>
            )}
            {rightPanel === 'agent-os' && selectedProject && (
              <div className="p-3 space-y-3">
                <StandardsPanel
                  projectName={selectedProject}
                  isOpen={standardsPanelOpen}
                  onToggle={() => setStandardsPanelOpen(prev => !prev)}
                />
                <ProductPanel
                  projectName={selectedProject}
                  isOpen={productPanelOpen}
                  onToggle={() => setProductPanelOpen(prev => !prev)}
                />
                {(featuresData?.features?.length ?? 0) > 0 && (
                  <SpecCards
                    features={featuresData?.features ?? []}
                    onReviewSpec={() => {}}
                  />
                )}
                {(gapsData?.gaps?.length ?? 0) > 0 && (
                  <GapAnalysisPanel
                    gaps={gapsData?.gaps ?? []}
                    onResolveGap={(gapId, resolution) => resolveGap.mutate({ gapId, resolution })}
                    onAutoResolve={() => autoResolveGaps.mutate()}
                  />
                )}
                {(featuresData?.features?.length ?? 0) > 0 && (
                  <ExpandPanel
                    projectName={selectedProject}
                    onExpansionComplete={() => {
                      // Refresh features data after expansion
                    }}
                  />
                )}
              </div>
            )}
          </div>
          </>
        )}
      </div>

      {/* Guide panel (floating, resizable, tabbed) */}
      {showGuide && (
        <DunkStackGuidePanel onClose={() => setShowGuide(false)} />
      )}
    </div>
  )
}

// ============================================================================
// File Viewer - Shows .agent/ file contents
// ============================================================================

const FILE_TABS = [
  { id: 'index', label: 'Index', endpoint: '/api/dunkstack/index' },
  { id: 'working-memory', label: 'Working Memory', endpoint: '/api/dunkstack/working-memory' },
  { id: 'bridge', label: 'Bridge', endpoint: '/api/dunkstack/bridge' },
  { id: 'build-log', label: 'Build Log', endpoint: '/api/dunkstack/build-log' },
  { id: 'config', label: 'Config', endpoint: '/api/dunkstack/config' },
] as const

function FileViewer(): React.JSX.Element {
  const [activeFile, setActiveFile] = useState<string>('index')
  const [fileContent, setFileContent] = useState<string>('')
  const [fileLoading, setFileLoading] = useState(false)

  const loadFile = useCallback(async (fileId: string) => {
    setActiveFile(fileId)
    setFileLoading(true)
    try {
      const file = FILE_TABS.find(f => f.id === fileId)
      if (!file) return
      const resp = await fetch(file.endpoint)
      const data = await resp.json()
      if (fileId === 'config') {
        setFileContent(JSON.stringify(data.config, null, 2))
      } else {
        setFileContent(data.content || '(empty)')
      }
    } catch {
      setFileContent('(failed to load)')
    } finally {
      setFileLoading(false)
    }
  }, [])

  // Load initial file on mount
  useEffect(() => { loadFile('index') }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-border bg-card shrink-0">
        <FileText size={14} className="text-muted-foreground" />
        <span className="text-xs font-semibold text-foreground">.agent/ Files</span>
      </div>

      {/* File tabs */}
      <div className="flex flex-wrap gap-1 px-3 py-2 border-b border-border/50">
        {FILE_TABS.map(f => (
          <button
            key={f.id}
            onClick={() => loadFile(f.id)}
            className={`px-2 py-1 rounded text-[10px] font-bold transition-colors ${
              activeFile === f.id
                ? 'bg-primary/10 text-primary border border-primary/20'
                : 'text-muted-foreground hover:bg-muted'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* File content */}
      <div className="flex-1 overflow-auto p-3 min-h-0">
        {fileLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <pre className="text-[11px] font-mono text-foreground whitespace-pre-wrap break-words leading-relaxed">
            {fileContent}
          </pre>
        )}
      </div>
    </div>
  )
}

