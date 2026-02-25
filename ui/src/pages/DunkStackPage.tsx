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

import { useState, useCallback } from 'react'
import {
  ArrowLeft,
  BookOpen,
  Sun,
  Moon,
  Shield,
  FileText,
  Layers,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ThemeSelector } from '@/components/ThemeSelector'
import { useTheme } from '@/hooks/useTheme'
import { useDunkStack } from '@/hooks/useDunkStack'
import { DunkStackContextGauge } from '@/components/dunkstack/DunkStackContextGauge'
import { DunkStackCommsChat } from '@/components/dunkstack/DunkStackCommsChat'
import { DunkStackSafetyPanel } from '@/components/dunkstack/DunkStackSafetyPanel'

type RightPanel = 'safety' | 'files' | null

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
    connected,
    loading,
  } = useDunkStack()

  const [rightPanel, setRightPanel] = useState<RightPanel>('safety')
  const [showGuide, setShowGuide] = useState(false)

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
      <div className="flex items-center h-10 px-3 border-b border-border bg-card shrink-0">
        {/* Left: back button + page title */}
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5 text-xs"
            onClick={() => { window.location.hash = '' }}
          >
            <ArrowLeft size={14} />
            AutoForge
          </Button>
          <span className="text-muted-foreground/30">/</span>
          <div className="flex items-center gap-1.5">
            <Layers size={14} className="text-primary" />
            <span className="text-sm font-bold text-foreground tracking-tight">DunkStack</span>
          </div>
        </div>

        {/* Center spacer */}
        <div className="flex-1" />

        {/* Right: controls */}
        <div className="flex items-center gap-2">
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

          {/* Separator */}
          <div className="w-px h-5 bg-border mx-1" />

          {/* Guide */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowGuide(prev => !prev)}
            title="Guide"
          >
            <BookOpen size={14} />
          </Button>

          {/* Theme Selector */}
          <ThemeSelector
            themes={themes}
            currentTheme={theme}
            onThemeChange={setTheme}
          />

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

      {/* Main content area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Chat panel (main area) */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="flex flex-col items-center gap-3">
                <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                <span className="text-sm text-muted-foreground">Loading DunkStack...</span>
              </div>
            </div>
          ) : (
            <DunkStackCommsChat
              commsLog={commsLog}
              onSendMessage={sendMessage}
              controlMode={controlMode}
              connected={connected}
            />
          )}
        </div>

        {/* Right panel */}
        {rightPanel && (
          <div className="w-[320px] shrink-0 border-l border-border bg-card/60 overflow-y-auto">
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
          </div>
        )}
      </div>

      {/* Guide overlay */}
      {showGuide && (
        <GuideOverlay onClose={() => setShowGuide(false)} />
      )}
    </div>
  )
}

// ============================================================================
// File Viewer - Shows .agent/ file contents
// ============================================================================

function FileViewer(): React.JSX.Element {
  const [activeFile, setActiveFile] = useState<string>('index')
  const [fileContent, setFileContent] = useState<string>('')
  const [fileLoading, setFileLoading] = useState(false)

  const files = [
    { id: 'index', label: 'Index', endpoint: '/api/dunkstack/index' },
    { id: 'working-memory', label: 'Working Memory', endpoint: '/api/dunkstack/working-memory' },
    { id: 'bridge', label: 'Bridge', endpoint: '/api/dunkstack/bridge' },
    { id: 'build-log', label: 'Build Log', endpoint: '/api/dunkstack/build-log' },
    { id: 'config', label: 'Config', endpoint: '/api/dunkstack/config' },
  ]

  const loadFile = useCallback(async (fileId: string) => {
    setActiveFile(fileId)
    setFileLoading(true)
    try {
      const file = files.find(f => f.id === fileId)
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

  // Load on mount and when tab changes
  useState(() => { loadFile('index') })

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-border bg-card shrink-0">
        <FileText size={14} className="text-muted-foreground" />
        <span className="text-xs font-semibold text-foreground">.agent/ Files</span>
      </div>

      {/* File tabs */}
      <div className="flex flex-wrap gap-1 px-3 py-2 border-b border-border/50">
        {files.map(f => (
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

// ============================================================================
// Guide Overlay
// ============================================================================

function GuideOverlay({ onClose }: { onClose: () => void }): React.JSX.Element {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-card border-2 border-border rounded-xl shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <div className="flex items-center gap-2">
            <BookOpen size={20} className="text-primary" />
            <h2 className="text-lg font-bold text-foreground">DunkStack Guide</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
          >
            &times;
          </button>
        </div>
        <div className="px-6 py-4 space-y-4 text-sm text-foreground">
          <section>
            <h3 className="font-bold text-base mb-2">What is DunkStack?</h3>
            <p className="text-muted-foreground">
              DunkStack is a file-based context management mechanism for AI coding agents.
              Instead of dumping all output through the API response (consuming context window),
              agents write substantive output to files and use the API response only for brief status signals.
            </p>
          </section>

          <section>
            <h3 className="font-bold text-base mb-2">The 7 Core Mechanisms</h3>
            <ol className="list-decimal list-inside space-y-1 text-muted-foreground">
              <li><strong className="text-foreground">System Prompt</strong> - Redirects output to files</li>
              <li><strong className="text-foreground">File Structure</strong> - .agent/ directory with index, memory, comms</li>
              <li><strong className="text-foreground">Walkie-Talkie</strong> - Bidirectional communication through files</li>
              <li><strong className="text-foreground">Idle/Pause</strong> - Back-and-forth session management</li>
              <li><strong className="text-foreground">Bridge Save</strong> - Session continuity across restarts</li>
              <li><strong className="text-foreground">Context Gauge</strong> - Real-time token tracking</li>
              <li><strong className="text-foreground">Safety System</strong> - Warning / Handoff / Hard Stop</li>
            </ol>
          </section>

          <section>
            <h3 className="font-bold text-base mb-2">File Comms</h3>
            <p className="text-muted-foreground">
              Messages in the chat panel read/write to <code className="text-xs bg-muted px-1 rounded">.agent/comms/</code> files:
            </p>
            <ul className="list-disc list-inside space-y-1 text-muted-foreground mt-1">
              <li><code className="text-xs bg-muted px-1 rounded">from_human.md</code> - Your messages to the agent</li>
              <li><code className="text-xs bg-muted px-1 rounded">to_human.md</code> - Agent's messages to you</li>
              <li><code className="text-xs bg-muted px-1 rounded">control.md</code> - Session mode (idle/continue/autopilot)</li>
            </ul>
          </section>

          <section>
            <h3 className="font-bold text-base mb-2">Context Safety</h3>
            <p className="text-muted-foreground">
              The gauge tracks token usage. When thresholds are crossed:
            </p>
            <ul className="list-disc list-inside space-y-1 text-muted-foreground mt-1">
              <li><strong className="text-orange-400">WARNING (45%)</strong> - Agent notified to prepare</li>
              <li><strong className="text-red-500">HANDOFF (47.5%)</strong> - Stop coding, write handoff file</li>
              <li><strong className="text-red-600">HARD STOP (50%)</strong> - Session terminates</li>
            </ul>
          </section>

          <section>
            <h3 className="font-bold text-base mb-2">Mode</h3>
            <p className="text-muted-foreground">
              <strong className="text-emerald-400">Subscription</strong>: Uses CLAUDE.md, estimated tokens, compaction occurs.
              <br />
              <strong className="text-blue-400">API</strong>: Direct API calls, exact token tracking, no compaction.
            </p>
          </section>
        </div>
      </div>
    </div>
  )
}
