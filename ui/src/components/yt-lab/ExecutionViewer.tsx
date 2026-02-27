/**
 * ExecutionViewer — Main split-screen layout for the live execution viewer.
 *
 * Layout:
 *   - Left sidebar (280px): StepTracker (top) + AgentLog (bottom)
 *   - Top bar (48px): ExecutionTopBar with project info, chat, controls
 *   - Main area: BrowserView (noVNC iframe)
 *
 * Responsive:
 *   - >1200px: Full layout
 *   - 768-1200px: Sidebar collapsed to icons
 *   - <768px: Full-screen browser, sidebar/log in drawers
 */

import { useState, useCallback, useMemo, useEffect, useRef } from 'react'
import { PanelLeftClose, PanelLeftOpen } from 'lucide-react'
import { Button } from '@/components/ui/button'
import type { YTStrategyProject, YTStrategyStep, YTStrategyStepStatus } from '@/lib/types'
import { useExecutionWebSocket } from '@/hooks/useExecutionWebSocket'
import {
  pauseExecution,
  resumeExecution,
  stopExecution,
  injectExecutionMessage,
  setTakeoverMode,
} from '@/lib/api'
import { StepTracker } from './StepTracker'
import { AgentLog } from './AgentLog'
import { BrowserView } from './BrowserView'
import { ExecutionTopBar } from './ExecutionTopBar'

interface ExecutionViewerProps {
  project: YTStrategyProject
  steps: YTStrategyStep[]
  sessionId: string | null
  novncUrl: string | null
  onBack: () => void
}

export function ExecutionViewer({
  project,
  steps,
  sessionId,
  novncUrl,
  onBack,
}: ExecutionViewerProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [isPending, setIsPending] = useState(false)
  const [confirmingStop, setConfirmingStop] = useState(false)
  const stopTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const ws = useExecutionWebSocket(sessionId)

  // Initialize step states when steps change
  useEffect(() => {
    if (steps.length > 0) {
      ws.initStepStates(steps.map((s) => s.id))
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [steps.length])

  // Build step status map from WebSocket state
  const stepStatusMap = useMemo(() => {
    const map = new Map<string, YTStrategyStepStatus>()
    for (const ss of ws.stepStates) {
      map.set(ss.stepId, ss.status)
    }
    return map
  }, [ws.stepStates])

  // Current step info
  const currentStepIndex = Math.max(0, ws.currentStep - 1)
  const currentStep = steps[currentStepIndex]
  const currentModel = currentStep?.model ?? 'claude-opus-4-6'

  // API action handlers
  const handleAction = useCallback(
    async (action: () => Promise<void>) => {
      setIsPending(true)
      try {
        await action()
      } catch {
        // Errors will appear in the WebSocket stream
      } finally {
        setIsPending(false)
      }
    },
    [],
  )

  const handlePause = useCallback(() => {
    if (!sessionId) return
    void handleAction(() => pauseExecution(sessionId))
  }, [sessionId, handleAction])

  const handleResume = useCallback(() => {
    if (!sessionId) return
    void handleAction(() => resumeExecution(sessionId))
  }, [sessionId, handleAction])

  const handleStop = useCallback(() => {
    if (!sessionId) return
    if (!confirmingStop) {
      setConfirmingStop(true)
      // Auto-dismiss after 3 seconds
      if (stopTimerRef.current) clearTimeout(stopTimerRef.current)
      stopTimerRef.current = setTimeout(() => setConfirmingStop(false), 3000)
      return
    }
    setConfirmingStop(false)
    void handleAction(() => stopExecution(sessionId))
  }, [sessionId, handleAction, confirmingStop])

  const handleTakeover = useCallback(() => {
    if (!sessionId) return
    void handleAction(() => setTakeoverMode(sessionId, true))
  }, [sessionId, handleAction])

  const handleReturnControl = useCallback(() => {
    if (!sessionId) return
    void handleAction(() => setTakeoverMode(sessionId, false))
  }, [sessionId, handleAction])

  // Cleanup stop confirmation timer on unmount
  useEffect(() => {
    return () => {
      if (stopTimerRef.current) clearTimeout(stopTimerRef.current)
    }
  }, [])

  const handleSendMessage = useCallback(
    (message: string) => {
      if (!sessionId) return
      injectExecutionMessage(sessionId, message).catch(() => {
        // Errors will appear in the WebSocket stream
      })
    },
    [sessionId],
  )

  // Responsive sidebar width
  const sidebarWidth = sidebarCollapsed ? 48 : 280

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Top bar */}
      <ExecutionTopBar
        projectName={project.name}
        currentStepTitle={currentStep?.title ?? ''}
        currentStep={ws.currentStep || 1}
        totalSteps={ws.totalSteps || steps.length}
        status={ws.status}
        model={currentModel}
        onPause={handlePause}
        onResume={handleResume}
        onStop={handleStop}
        onTakeover={handleTakeover}
        onReturnControl={handleReturnControl}
        onSendMessage={handleSendMessage}
        onBack={onBack}
        isPending={isPending}
        confirmingStop={confirmingStop}
      />

      {/* Main content: sidebar + browser */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left sidebar */}
        <div
          className="shrink-0 flex flex-col border-r border-border bg-card transition-all duration-200 overflow-hidden"
          style={{ width: sidebarWidth }}
        >
          {/* Sidebar toggle */}
          <div className="flex items-center justify-end px-1 py-1 border-b border-border shrink-0">
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0 text-muted-foreground hover:text-foreground"
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              {sidebarCollapsed ? <PanelLeftOpen size={12} /> : <PanelLeftClose size={12} />}
            </Button>
          </div>

          {/* Step tracker (top half) */}
          <div className="flex-1 overflow-hidden min-h-0">
            <StepTracker
              steps={steps}
              currentStepIndex={currentStepIndex}
              stepStatuses={stepStatusMap}
              collapsed={sidebarCollapsed}
            />
          </div>

          {/* Agent log (bottom half) */}
          <div className="flex-1 overflow-hidden min-h-0">
            <AgentLog
              logs={ws.logs}
              onClear={ws.clearLogs}
              collapsed={sidebarCollapsed}
            />
          </div>
        </div>

        {/* Browser view (main area) */}
        <div className="flex-1 flex flex-col p-2 min-w-0">
          <BrowserView
            novncUrl={novncUrl}
            status={ws.status}
            isTakeover={ws.status === 'takeover'}
          />
        </div>
      </div>
    </div>
  )
}
