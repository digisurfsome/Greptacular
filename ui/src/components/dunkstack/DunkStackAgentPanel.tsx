/**
 * DunkStack Agent Panel
 *
 * Left-side panel showing the Claude API call session.
 * Displays streaming agent output and provides start/stop controls.
 * This is the "API call" side — you start the session here,
 * then communicate through the walkie-talkie (comms) panel on the right.
 */

import { useState, useRef, useEffect, useCallback } from 'react'
import { Play, Square, Terminal, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  dunkstackStartAgent,
  dunkstackStopAgent,
  dunkstackGetAgentStatus,
  dunkstackGetAgentOutput,
} from '@/lib/api'

interface DunkStackAgentPanelProps {
  /** Currently selected project name */
  projectName: string | null
  /** Whether WebSocket is connected */
  connected: boolean
  /** Current model preset label for display */
  modelLabel: string
}

export function DunkStackAgentPanel({
  projectName,
  modelLabel,
}: DunkStackAgentPanelProps): React.JSX.Element {
  const [agentStatus, setAgentStatus] = useState<string>('stopped')
  const [outputLines, setOutputLines] = useState<string[]>([])
  const [starting, setStarting] = useState(false)
  const [stopping, setStopping] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new output arrives
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [outputLines.length])

  // Poll agent status on mount + periodically
  useEffect(() => {
    async function checkStatus() {
      try {
        const status = await dunkstackGetAgentStatus()
        setAgentStatus(status.status)
      } catch {
        // Server may not be running
      }
    }

    checkStatus()
    const interval = setInterval(checkStatus, 5000)

    return () => clearInterval(interval)
  }, [])

  // Load existing output on mount
  useEffect(() => {
    async function loadOutput() {
      try {
        const result = await dunkstackGetAgentOutput(500)
        if (result.lines.length > 0) {
          setOutputLines(result.lines)
        }
      } catch {
        // Ignore
      }
    }
    loadOutput()
  }, [])

  // Listen for agent_output and agent_status messages on the DunkStack WebSocket
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/api/dunkstack/ws`
    let ws: WebSocket
    let reconnectTimer: ReturnType<typeof setTimeout>

    function connect() {
      ws = new WebSocket(wsUrl)

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data)
          if (msg.type === 'agent_output') {
            setOutputLines((prev: string[]) => {
              const next = [...prev, msg.line]
              // Keep last 2000 lines
              return next.length > 2000 ? next.slice(-2000) : next
            })
          } else if (msg.type === 'agent_status') {
            setAgentStatus(msg.status)
          }
        } catch {
          // Ignore parse errors
        }
      }

      ws.onclose = () => {
        reconnectTimer = setTimeout(connect, 3000)
      }

      ws.onerror = () => {
        ws.close()
      }
    }

    connect()

    return () => {
      clearTimeout(reconnectTimer)
      ws?.close()
    }
  }, [])

  const handleStart = useCallback(async () => {
    if (!projectName) return
    setStarting(true)
    try {
      setOutputLines([]) // Clear previous output
      const result = await dunkstackStartAgent(projectName)
      setAgentStatus(result.status === 'started' || result.status === 'already_running' ? 'running' : result.status)
    } catch (e) {
      setOutputLines((prev: string[]) => [...prev, `[Error] Failed to start agent: ${e}`])
    } finally {
      setStarting(false)
    }
  }, [projectName])

  const handleStop = useCallback(async () => {
    setStopping(true)
    try {
      await dunkstackStopAgent()
      setAgentStatus('stopped')
    } catch (e) {
      setOutputLines((prev: string[]) => [...prev, `[Error] Failed to stop agent: ${e}`])
    } finally {
      setStopping(false)
    }
  }, [])

  const isRunning = agentStatus === 'running'

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-card shrink-0">
        <div className="flex items-center gap-2">
          <Terminal size={16} className="text-primary" />
          <span className="text-sm font-semibold text-foreground">Agent Session</span>
          <span className="text-[10px] text-muted-foreground">(API Call)</span>
        </div>
        <div className="flex items-center gap-2">
          {/* Status indicator */}
          <span className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
            isRunning ? 'bg-emerald-500/20 text-emerald-400' :
            agentStatus === 'crashed' ? 'bg-red-500/20 text-red-400' :
            'bg-muted text-muted-foreground'
          }`}>
            {agentStatus.toUpperCase()}
          </span>

          {/* Start/Stop button */}
          {isRunning ? (
            <Button
              variant="destructive"
              size="sm"
              className="gap-1.5 text-xs h-7"
              onClick={handleStop}
              disabled={stopping}
            >
              {stopping ? <Loader2 size={12} className="animate-spin" /> : <Square size={12} />}
              Stop
            </Button>
          ) : (
            <Button
              variant="default"
              size="sm"
              className="gap-1.5 text-xs h-7"
              onClick={handleStart}
              disabled={starting || !projectName}
              title={!projectName ? 'Select a project first' : `Start agent for ${projectName}`}
            >
              {starting ? <Loader2 size={12} className="animate-spin" /> : <Play size={12} />}
              Start
            </Button>
          )}
        </div>
      </div>

      {/* Output area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 min-h-0 bg-zinc-950/50">
        {outputLines.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center gap-3">
            <Terminal size={32} className="text-muted-foreground/30" />
            <div>
              <p className="text-sm text-muted-foreground">No agent session active</p>
              <p className="text-xs text-muted-foreground/60 mt-1">
                {projectName ? (
                  <>
                    Press <strong>Start</strong> to begin a Claude session for <strong>{projectName}</strong>.
                    <br />
                    The agent will read .agent/ files and start working.
                    <br />
                    Talk to it through the walkie-talkie chat on the right.
                  </>
                ) : (
                  'Select a project from the sidebar first.'
                )}
              </p>
            </div>
          </div>
        ) : (
          <pre className="text-[11px] font-mono text-zinc-300 whitespace-pre-wrap break-words leading-relaxed">
            {outputLines.map((line: string, i: number) => (
              <div key={i} className={
                line.startsWith('[Tool:') ? 'text-cyan-400' :
                line.startsWith('   [Done]') ? 'text-emerald-500/60' :
                line.startsWith('   [Error]') || line.startsWith('[Error]') ? 'text-red-400' :
                line.startsWith('[Budget]') ? 'text-amber-400' :
                line.startsWith('=') ? 'text-zinc-500' :
                ''
              }>
                {line}
              </div>
            ))}
          </pre>
        )}
      </div>

      {/* Footer with model info */}
      <div className="shrink-0 border-t border-border bg-card px-3 py-1.5">
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-muted-foreground">
            Model: {modelLabel}
          </span>
          <span className="text-[10px] text-muted-foreground">
            {outputLines.length > 0 ? `${outputLines.length} lines` : ''}
          </span>
        </div>
      </div>
    </div>
  )
}
