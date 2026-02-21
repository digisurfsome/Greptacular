/**
 * SwarmPanel
 *
 * Controls and status display for the swarm pipeline — concurrent autonomous
 * agents that share files and auto-hand off work.
 *
 * Shows:
 * - Pipeline stages with real-time status (pending → running → completed)
 * - Shared workspace files as they're created
 * - File contents preview
 * - Start/stop controls
 * - Per-stage walkie-talkie injection
 */

import { useState, useRef, useEffect, useCallback } from 'react'
import {
  Play,
  Square,
  FileText,
  ArrowRight,
  Loader2,
  CheckCircle2,
  XCircle,
  Clock,
  Radio,
  Eye,
  X,
  Send,
  Zap,
  Network,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import type {
  SwarmPipelineStatus,
  SwarmStageStatus,
  SwarmSharedFile,
  SwarmStartResponse,
} from '@/lib/api'
import {
  startSwarm,
  stopSwarm,
  getSwarmStatus,
  readSwarmFile,
  injectSwarmMessage,
} from '@/lib/api'

interface SwarmPanelProps {
  workingDirectory: string | null
  onClose: () => void
}

/** Status badge colors and icons for each stage status. */
const STATUS_CONFIG: Record<string, { color: string; icon: typeof Clock; label: string }> = {
  pending: { color: 'text-muted-foreground bg-muted/50', icon: Clock, label: 'Pending' },
  running: { color: 'text-cyan-600 bg-cyan-500/10', icon: Loader2, label: 'Running' },
  waiting_trigger: { color: 'text-amber-600 bg-amber-500/10', icon: Clock, label: 'Waiting' },
  completed: { color: 'text-green-600 bg-green-500/10', icon: CheckCircle2, label: 'Done' },
  failed: { color: 'text-red-600 bg-red-500/10', icon: XCircle, label: 'Failed' },
}

function StageCard({ stage, onInject }: { stage: SwarmStageStatus; onInject: (name: string) => void }) {
  const config = STATUS_CONFIG[stage.status] || STATUS_CONFIG.pending
  const Icon = config.icon

  return (
    <div className={`border border-border rounded-lg p-3 ${stage.status === 'running' ? 'ring-2 ring-cyan-400/30' : ''}`}>
      <div className="flex items-center justify-between mb-1.5">
        <div className="flex items-center gap-2">
          <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold ${config.color}`}>
            <Icon size={10} className={stage.status === 'running' ? 'animate-spin' : ''} />
            {config.label}
          </span>
          <span className="text-xs font-bold text-foreground">{stage.label}</span>
        </div>
        <span className="text-[10px] text-muted-foreground">{stage.model} / {stage.context_mode}</span>
      </div>

      <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
        {stage.trigger_file && (
          <span>Trigger: <code className="bg-muted px-1 rounded">{stage.trigger_file}</code></span>
        )}
        <span>Output: <code className="bg-muted px-1 rounded">{stage.output_file}</code></span>
      </div>

      {stage.error && (
        <p className="text-[10px] text-red-500 mt-1 truncate">{stage.error}</p>
      )}

      {stage.status === 'running' && (
        <button
          onClick={() => onInject(stage.name)}
          className="mt-1.5 flex items-center gap-1 text-[10px] text-amber-600 hover:text-amber-700"
        >
          <Radio size={10} /> Send walkie-talkie
        </button>
      )}
    </div>
  )
}

function SharedFileCard({
  file,
  onPreview,
}: {
  file: SwarmSharedFile
  onPreview: (name: string) => void
}) {
  return (
    <div
      className="flex items-center gap-2 px-2 py-1.5 hover:bg-muted/50 rounded cursor-pointer"
      onClick={() => onPreview(file.name)}
    >
      <FileText size={14} className="text-muted-foreground flex-shrink-0" />
      <span className="text-xs text-foreground flex-1 truncate">{file.name}</span>
      <span className="text-[10px] text-muted-foreground">
        {file.size >= 1024 ? `${(file.size / 1024).toFixed(0)}K` : `${file.size}B`}
      </span>
      <Eye size={12} className="text-muted-foreground" />
    </div>
  )
}

export function SwarmPanel({ workingDirectory, onClose }: SwarmPanelProps): React.JSX.Element {
  const [swarmId, setSwarmId] = useState<string | null>(null)
  const [status, setStatus] = useState<SwarmPipelineStatus | null>(null)
  const [taskInput, setTaskInput] = useState('')
  const [starting, setStarting] = useState(false)
  const [previewFile, setPreviewFile] = useState<{ name: string; content: string } | null>(null)
  const [injectTarget, setInjectTarget] = useState<string | null>(null)
  const [injectInput, setInjectInput] = useState('')
  const wsRef = useRef<WebSocket | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Poll for status updates when a swarm is running
  useEffect(() => {
    if (!swarmId) return

    const poll = async () => {
      try {
        const s = await getSwarmStatus(swarmId)
        setStatus(s)

        // Stop polling when done
        if (s.status === 'completed' || s.status === 'failed' || s.status === 'stopped') {
          if (pollRef.current) {
            clearInterval(pollRef.current)
            pollRef.current = null
          }
        }
      } catch {
        // Swarm may have been cleaned up
      }
    }

    poll()
    pollRef.current = setInterval(poll, 3000)
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [swarmId])

  // Connect WebSocket for real-time events
  useEffect(() => {
    if (!swarmId) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${protocol}//${window.location.host}/api/swarm/ws/${swarmId}`)
    wsRef.current = ws

    ws.onopen = () => {
      ws.send(JSON.stringify({ type: 'start' }))
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        // Refresh status on any swarm event
        if (data.type?.startsWith('swarm_')) {
          getSwarmStatus(swarmId).then(setStatus).catch(() => {})
        }
      } catch {
        // ignore parse errors
      }
    }

    ws.onerror = () => {
      // WebSocket errors are handled by onclose
    }

    ws.onclose = () => {
      wsRef.current = null
    }

    return () => {
      ws.close()
      wsRef.current = null
    }
  }, [swarmId])

  const handleStart = useCallback(async () => {
    if (!workingDirectory || !taskInput.trim()) return

    setStarting(true)
    try {
      const result = await startSwarm({
        working_directory: workingDirectory,
        task_description: taskInput.trim(),
      })
      setSwarmId(result.swarm_id)
      setTaskInput('')
    } catch (e) {
      console.error('Failed to start swarm:', e)
    } finally {
      setStarting(false)
    }
  }, [workingDirectory, taskInput])

  const handleStop = useCallback(async () => {
    if (!swarmId) return
    try {
      await stopSwarm(swarmId)
      // Status will update via polling
    } catch (e) {
      console.error('Failed to stop swarm:', e)
    }
  }, [swarmId])

  const handlePreviewFile = useCallback(async (filename: string) => {
    if (!swarmId) return
    try {
      const result = await readSwarmFile(swarmId, filename)
      setPreviewFile({ name: filename, content: result.content })
    } catch {
      // File not readable
    }
  }, [swarmId])

  const handleInject = useCallback(async () => {
    if (!swarmId || !injectTarget || !injectInput.trim()) return
    try {
      await injectSwarmMessage(swarmId, injectTarget, injectInput.trim())
      setInjectInput('')
      setInjectTarget(null)
    } catch (e) {
      console.error('Failed to inject message:', e)
    }
  }, [swarmId, injectTarget, injectInput])

  const isRunning = status?.status === 'running'
  const isDone = status?.status === 'completed' || status?.status === 'failed' || status?.status === 'stopped'

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-border bg-gradient-to-r from-violet-500/10 to-cyan-500/10">
        <div className="flex items-center gap-2">
          <Network size={14} className="text-violet-500" />
          <span className="text-xs font-bold tracking-wide text-foreground">SWARM</span>
          {status && (
            <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${
              isRunning ? 'bg-cyan-500/20 text-cyan-600' :
              status.status === 'completed' ? 'bg-green-500/20 text-green-600' :
              status.status === 'failed' ? 'bg-red-500/20 text-red-600' :
              'bg-muted text-muted-foreground'
            }`}>
              {status.status.toUpperCase()}
            </span>
          )}
        </div>
        <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
          <X size={14} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3">
        {/* Task input (before start) */}
        {!swarmId && (
          <div className="space-y-2">
            <p className="text-xs text-muted-foreground">
              Describe the task. The swarm will run 3 concurrent agents:
              <strong> Research</strong> (explores codebase) →
              <strong> PRD Builder</strong> (creates requirements) →
              <strong> Coder</strong> (implements changes).
            </p>
            <textarea
              value={taskInput}
              onChange={(e) => setTaskInput(e.target.value)}
              placeholder="What should the swarm build? e.g. 'Add user authentication with JWT tokens and login page'"
              className="w-full resize-none min-h-[80px] rounded-md border border-border bg-input px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground/60 outline-none ring-ring focus:ring-1"
              rows={4}
            />
            {!workingDirectory && (
              <p className="text-[10px] text-amber-600">
                Select a working directory first (use the repo selector in the breadcrumb bar).
              </p>
            )}
            <Button
              onClick={handleStart}
              disabled={!workingDirectory || !taskInput.trim() || starting}
              className="w-full bg-violet-600 hover:bg-violet-700 text-white text-xs gap-2"
            >
              {starting ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <Zap size={14} />
              )}
              Launch Swarm
            </Button>
          </div>
        )}

        {/* Pipeline stages */}
        {status && (
          <>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold text-muted-foreground tracking-wide">PIPELINE</span>
                {isRunning && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 px-2 text-[10px] text-red-500 hover:text-red-600 hover:bg-red-500/10"
                    onClick={handleStop}
                  >
                    <Square size={10} className="mr-1" /> Stop
                  </Button>
                )}
                {isDone && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 px-2 text-[10px]"
                    onClick={() => { setSwarmId(null); setStatus(null) }}
                  >
                    New Swarm
                  </Button>
                )}
              </div>

              {/* Stage cards with flow arrows */}
              {status.stages.map((stage, i) => (
                <div key={stage.name}>
                  <StageCard
                    stage={stage}
                    onInject={(name) => setInjectTarget(name)}
                  />
                  {i < status.stages.length - 1 && (
                    <div className="flex justify-center py-1">
                      <ArrowRight size={14} className="text-muted-foreground/40 rotate-90" />
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Shared files */}
            {status.shared_files.length > 0 && (
              <div>
                <span className="text-[10px] font-bold text-muted-foreground tracking-wide">
                  SHARED FILES
                </span>
                <div className="mt-1 border border-border rounded-md overflow-hidden">
                  {status.shared_files.map((file) => (
                    <SharedFileCard
                      key={file.name}
                      file={file}
                      onPreview={handlePreviewFile}
                    />
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Walkie-talkie injection modal */}
      {injectTarget && (
        <div className="px-3 py-2 border-t border-amber-500/30 bg-amber-500/5">
          <div className="flex items-center gap-1 mb-1">
            <Radio size={10} className="text-amber-600" />
            <span className="text-[10px] font-bold text-amber-600">
              Walkie-talkie → {injectTarget}
            </span>
            <button
              onClick={() => setInjectTarget(null)}
              className="ml-auto text-muted-foreground hover:text-foreground"
            >
              <X size={10} />
            </button>
          </div>
          <div className="flex gap-1">
            <input
              value={injectInput}
              onChange={(e) => setInjectInput(e.target.value)}
              placeholder="Message to the agent..."
              className="flex-1 rounded border border-border bg-input px-2 py-1 text-xs text-foreground outline-none"
              onKeyDown={(e) => { if (e.key === 'Enter') handleInject() }}
            />
            <Button
              size="sm"
              className="h-7 px-2 bg-amber-500 hover:bg-amber-600 text-white"
              onClick={handleInject}
              disabled={!injectInput.trim()}
            >
              <Send size={12} />
            </Button>
          </div>
        </div>
      )}

      {/* File preview modal */}
      {previewFile && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-card border border-border rounded-lg shadow-lg max-w-2xl w-full mx-4 max-h-[80vh] flex flex-col">
            <div className="flex items-center justify-between px-4 py-3 border-b border-border">
              <span className="text-sm font-medium text-foreground">{previewFile.name}</span>
              <button
                onClick={() => setPreviewFile(null)}
                className="text-muted-foreground hover:text-foreground"
              >
                <X size={16} />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              <pre className="bg-muted rounded-lg p-4 overflow-x-auto font-mono text-xs text-foreground whitespace-pre-wrap">
                {previewFile.content}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
