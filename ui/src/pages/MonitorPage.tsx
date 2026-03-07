/**
 * MonitorPage — Standalone agent monitoring wall
 *
 * Opens in a second browser window (/#/monitor) showing a live grid
 * of all active agents with their scrolling log feeds.
 * No controls, no clutter — just watching agents work.
 *
 * Reads the selected project from localStorage (same key as App.tsx).
 * Can also be passed via hash: /#/monitor/projectName
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import { useProjectWebSocket } from '../hooks/useWebSocket'
import { AgentAvatar } from '../components/AgentAvatar'
import { OrchestratorStatusCard } from '../components/OrchestratorStatusCard'
import type { ActiveAgent, AgentLogEntry, AgentState } from '../lib/types'
import { Badge } from '@/components/ui/badge'
import { Rocket, Monitor, Maximize2, Minimize2, Radio } from 'lucide-react'

const STORAGE_KEY = 'autoforge-selected-project'

function getProjectFromHash(): string | null {
  const hash = window.location.hash
  // /#/monitor/projectName
  const match = hash.match(/^#\/monitor\/(.+)$/)
  if (match) return decodeURIComponent(match[1])
  return null
}

function getProjectFromStorage(): string | null {
  try {
    return localStorage.getItem(STORAGE_KEY)
  } catch {
    return null
  }
}

// Get state color for the status dot
function getStateDotColor(state: AgentState): string {
  switch (state) {
    case 'working': return 'bg-cyan-400'
    case 'thinking': return 'bg-yellow-400'
    case 'testing': return 'bg-purple-400'
    case 'success': return 'bg-green-400'
    case 'error': return 'bg-red-400'
    case 'struggling': return 'bg-orange-400'
    default: return 'bg-zinc-400'
  }
}

function getStateLabel(state: AgentState): string {
  switch (state) {
    case 'idle': return 'Idle'
    case 'thinking': return 'Thinking'
    case 'working': return 'Coding'
    case 'testing': return 'Testing'
    case 'success': return 'Done'
    case 'error': return 'Error'
    case 'struggling': return 'Struggling'
    default: return 'Active'
  }
}

// Single agent feed panel with scrolling logs
function AgentFeed({
  agent,
  logs,
  isFullscreen,
  onToggleFullscreen,
}: {
  agent: ActiveAgent
  logs: AgentLogEntry[]
  isFullscreen: boolean
  onToggleFullscreen: () => void
}) {
  const logContainerRef = useRef<HTMLDivElement>(null)
  const [autoScroll, setAutoScroll] = useState(true)

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight
    }
  }, [logs.length, autoScroll])

  // Detect if user scrolled up (disable auto-scroll)
  const handleScroll = useCallback(() => {
    if (!logContainerRef.current) return
    const el = logContainerRef.current
    const isAtBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 50
    setAutoScroll(isAtBottom)
  }, [])

  const isActive = ['thinking', 'working', 'testing'].includes(agent.state)

  return (
    <div className={`
      flex flex-col rounded-lg border-2 border-border bg-card overflow-hidden
      ${isFullscreen ? 'fixed inset-4 z-50' : ''}
      ${isActive ? 'border-primary/50' : ''}
    `}>
      {/* Agent header bar */}
      <div className="flex items-center gap-2 px-3 py-2 bg-muted/50 border-b border-border shrink-0">
        <AgentAvatar name={agent.agentName} state={agent.state} size="sm" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-bold text-sm">{agent.agentName}</span>
            <div className="flex items-center gap-1.5">
              <div className={`w-2 h-2 rounded-full ${getStateDotColor(agent.state)} ${isActive ? 'animate-pulse' : ''}`} />
              <span className="text-xs text-muted-foreground">{getStateLabel(agent.state)}</span>
            </div>
            <Badge variant="outline" className="text-[10px] ml-auto">
              {agent.agentType === 'testing' ? 'TEST' : 'CODE'}
            </Badge>
          </div>
          <div className="text-xs text-muted-foreground truncate">
            {agent.featureIds && agent.featureIds.length > 1
              ? `Batch: ${agent.featureIds.map(id => `#${id}`).join(', ')} — Active: #${agent.featureId}`
              : `Feature #${agent.featureId}: ${agent.featureName}`
            }
          </div>
        </div>
        <button
          onClick={onToggleFullscreen}
          className="p-1 rounded hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
          title={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
        >
          {isFullscreen ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
        </button>
      </div>

      {/* Thought bubble */}
      {agent.thought && (
        <div className="px-3 py-1.5 bg-primary/5 border-b border-border text-xs italic text-muted-foreground truncate">
          💭 {agent.thought}
        </div>
      )}

      {/* Scrolling log feed */}
      <div
        ref={logContainerRef}
        onScroll={handleScroll}
        className="flex-1 min-h-0 overflow-y-auto p-2 bg-zinc-950 font-mono text-xs leading-relaxed"
      >
        {logs.length === 0 ? (
          <div className="text-zinc-500 italic p-2">Waiting for output...</div>
        ) : (
          logs.map((log, idx) => (
            <div
              key={idx}
              className={`whitespace-pre-wrap break-all ${
                log.type === 'error' ? 'text-red-400' :
                log.type === 'state_change' ? 'text-cyan-400' :
                'text-zinc-300'
              }`}
            >
              {log.line}
            </div>
          ))
        )}
        {/* Auto-scroll anchor */}
        {!autoScroll && (
          <button
            onClick={() => {
              setAutoScroll(true)
              if (logContainerRef.current) {
                logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight
              }
            }}
            className="sticky bottom-2 left-1/2 -translate-x-1/2 px-3 py-1 bg-primary text-primary-foreground rounded-full text-xs shadow-lg hover:bg-primary/90 transition-colors"
          >
            ↓ Jump to bottom
          </button>
        )}
      </div>
    </div>
  )
}

// Idle state when no agents are running
function IdleState({ projectName }: { projectName: string | null }) {
  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="text-center space-y-4 max-w-md">
        <div className="w-20 h-20 rounded-full bg-muted flex items-center justify-center mx-auto">
          <Monitor size={36} className="text-muted-foreground" />
        </div>
        <h2 className="text-xl font-semibold text-foreground">No agents running</h2>
        <p className="text-muted-foreground">
          {projectName
            ? `Monitoring "${projectName}" — start parallel agents from the main AutoForge window and they'll appear here automatically.`
            : 'No project selected. Open AutoForge in another window and select a project first.'
          }
        </p>
        <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
          <Radio size={14} className="animate-pulse" />
          <span>Listening for agent activity...</span>
        </div>
      </div>
    </div>
  )
}

export function MonitorPage() {
  const projectFromHash = getProjectFromHash()
  const [projectName, setProjectName] = useState<string | null>(projectFromHash || getProjectFromStorage())
  const [fullscreenAgent, setFullscreenAgent] = useState<number | null>(null)

  // Listen for storage changes (if user switches project in main window)
  useEffect(() => {
    if (projectFromHash) return // Hash takes priority

    const handleStorage = (e: StorageEvent) => {
      if (e.key === STORAGE_KEY) {
        setProjectName(e.newValue)
      }
    }
    window.addEventListener('storage', handleStorage)

    // Also poll localStorage in case storage events don't fire (same-origin same-tab)
    const poll = setInterval(() => {
      const current = getProjectFromStorage()
      setProjectName(prev => current !== prev ? current : prev)
    }, 2000)

    return () => {
      window.removeEventListener('storage', handleStorage)
      clearInterval(poll)
    }
  }, [projectFromHash])

  const wsState = useProjectWebSocket(projectName)

  // Determine grid layout based on agent count
  const agentCount = wsState.activeAgents.length
  const gridClass = agentCount <= 1
    ? 'grid-cols-1'
    : agentCount <= 2
      ? 'grid-cols-1 lg:grid-cols-2'
      : agentCount <= 4
        ? 'grid-cols-1 md:grid-cols-2'
        : agentCount <= 6
          ? 'grid-cols-1 md:grid-cols-2 xl:grid-cols-3'
          : 'grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4'

  return (
    <div className="h-screen flex flex-col bg-background text-foreground dark">
      {/* Top bar */}
      <header className="flex items-center justify-between px-4 py-2 bg-card border-b-2 border-border shrink-0">
        <div className="flex items-center gap-3">
          <Rocket size={20} className="text-primary" />
          <h1 className="font-bold text-lg tracking-tight">Agent Monitor</h1>
          {projectName && (
            <Badge variant="secondary" className="font-mono text-xs">
              {projectName}
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-3">
          {wsState.isConnected && (
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
              <span className="text-xs text-muted-foreground">Connected</span>
            </div>
          )}
          {agentCount > 0 && (
            <Badge variant="default">
              {agentCount} {agentCount === 1 ? 'agent' : 'agents'} active
            </Badge>
          )}
          {wsState.orchestratorStatus && (
            <Badge variant="outline" className="text-xs">
              {wsState.orchestratorStatus.codingAgents} coding · {wsState.orchestratorStatus.testingAgents} testing
            </Badge>
          )}
        </div>
      </header>

      {/* Orchestrator status bar (when available) */}
      {wsState.orchestratorStatus && (
        <div className="px-4 py-2 shrink-0">
          <OrchestratorStatusCard status={wsState.orchestratorStatus} />
        </div>
      )}

      {/* Main content */}
      {agentCount === 0 ? (
        <IdleState projectName={projectName} />
      ) : (
        <div className={`flex-1 min-h-0 grid ${gridClass} gap-3 p-3`}>
          {wsState.activeAgents.map((agent) => (
            <AgentFeed
              key={`agent-${agent.agentIndex}`}
              agent={agent}
              logs={wsState.getAgentLogs(agent.agentIndex)}
              isFullscreen={fullscreenAgent === agent.agentIndex}
              onToggleFullscreen={() =>
                setFullscreenAgent(prev =>
                  prev === agent.agentIndex ? null : agent.agentIndex
                )
              }
            />
          ))}
        </div>
      )}

      {/* Fullscreen backdrop */}
      {fullscreenAgent !== null && (
        <div
          className="fixed inset-0 bg-black/60 z-40"
          onClick={() => setFullscreenAgent(null)}
        />
      )}
    </div>
  )
}
