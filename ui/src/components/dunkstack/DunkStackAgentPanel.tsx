/**
 * DunkStack Agent Panel
 *
 * Left-side panel showing the Claude API call session.
 * Split into two resizable sections:
 *   Top: Raw agent output (tool calls, file ops, status)
 *   Bottom: Mini chat for agent text messages + input
 * Draggable divider between them.
 */

import { useState, useRef, useEffect, useCallback } from 'react'
import { Play, Square, Terminal, Loader2, MessageSquare, Send, GripHorizontal } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  dunkstackStartAgent,
  dunkstackStopAgent,
  dunkstackGetAgentStatus,
} from '@/lib/api'

interface DunkStackAgentPanelProps {
  /** Currently selected project name */
  projectName: string | null
  /** Current model preset label for display */
  modelLabel: string
  /** Called when agent status changes */
  onStatusChange?: (status: string) => void
}

/** Classify a line as raw output or agent chat text */
function isAgentChatLine(line: string): boolean {
  // Lines that are NOT tool calls, status bars, or system output = agent chat text
  if (line.startsWith('[Tool:')) return false
  if (line.startsWith('   [Done]')) return false
  if (line.startsWith('   [Error]') || line.startsWith('[Error]')) return false
  if (line.startsWith('[Budget]')) return false
  if (line.startsWith('=')) return false
  if (line.startsWith('DunkStack Agent')) return false
  if (line.startsWith('   Project:') || line.startsWith('   Model:') || line.startsWith('   Billing:') || line.startsWith('   CLI:')) return false
  if (line.trim() === '') return false
  // Anything else is agent text
  return true
}

export function DunkStackAgentPanel({
  projectName,
  modelLabel,
  onStatusChange,
}: DunkStackAgentPanelProps): React.JSX.Element {
  const [agentStatus, setAgentStatus] = useState<string>('stopped')
  const [outputLines, setOutputLines] = useState<string[]>([])
  const [chatMessages, setChatMessages] = useState<Array<{ from: 'agent' | 'you'; text: string }>>([])
  const [chatInput, setChatInput] = useState('')
  const [starting, setStarting] = useState(false)
  const [stopping, setStopping] = useState(false)
  const [splitPercent, setSplitPercent] = useState(65) // top section gets 65%
  const [isDragging, setIsDragging] = useState(false)

  const scrollRef = useRef<HTMLDivElement>(null)
  const chatScrollRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  // Notify parent when agent status changes
  useEffect(() => {
    onStatusChange?.(agentStatus)
  }, [agentStatus, onStatusChange])

  // Auto-scroll raw output to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [outputLines.length])

  // Auto-scroll chat to bottom
  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight
    }
  }, [chatMessages.length])

  // Poll agent status on mount + periodically
  useEffect(() => {
    if (!projectName) return
    async function checkStatus() {
      try {
        const status = await dunkstackGetAgentStatus(projectName!)
        setAgentStatus(status.status)
      } catch {
        // Server may not be running
      }
    }

    checkStatus()
    const interval = setInterval(checkStatus, 5000)

    return () => clearInterval(interval)
  }, [projectName])

  // Listen for agent_output and agent_status messages on the DunkStack WebSocket
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/api/dunkstack/ws`
    let ws: WebSocket
    let reconnectTimer: ReturnType<typeof setTimeout>

    function connect() {
      ws = new WebSocket(wsUrl)

      ws.onmessage = (event: MessageEvent) => {
        try {
          const msg = JSON.parse(event.data)
          if (msg.type === 'agent_output') {
            setOutputLines((prev: string[]) => {
              const next = [...prev, msg.line]
              return next.length > 2000 ? next.slice(-2000) : next
            })
            // If it's agent chat text, add to chat messages
            if (isAgentChatLine(msg.line)) {
              setChatMessages((prev: Array<{ from: 'agent' | 'you'; text: string }>) => [
                ...prev,
                { from: 'agent' as const, text: msg.line },
              ])
            }
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
      setOutputLines([])
      setChatMessages([])
      const result = await dunkstackStartAgent(projectName)
      setAgentStatus(result.status === 'started' || result.status === 'already_running' ? 'running' : result.status)
    } catch (e: unknown) {
      setOutputLines((prev: string[]) => [...prev, `[Error] Failed to start agent: ${e}`])
    } finally {
      setStarting(false)
    }
  }, [projectName])

  const handleStop = useCallback(async () => {
    if (!projectName) return
    setStopping(true)
    try {
      await dunkstackStopAgent(projectName)
      setAgentStatus('stopped')
    } catch (e: unknown) {
      setOutputLines((prev: string[]) => [...prev, `[Error] Failed to stop agent: ${e}`])
    } finally {
      setStopping(false)
    }
  }, [])

  // Send a chat message (writes to from_human.md via the comms API)
  const handleSendChat = useCallback(async () => {
    const text = chatInput.trim()
    if (!text) return
    setChatInput('')
    setChatMessages((prev: Array<{ from: 'agent' | 'you'; text: string }>) => [
      ...prev,
      { from: 'you' as const, text },
    ])
    // Post to from_human via the dunkstack comms endpoint
    try {
      const params = projectName ? `?project_name=${encodeURIComponent(projectName)}` : ''
      await fetch(`/api/dunkstack/comms/from-human${params}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: text, title: 'API Chat', category: 'Chat' }),
      })
    } catch {
      // Best effort
    }
  }, [chatInput, projectName])

  // Draggable divider logic
  const handleDragStart = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  useEffect(() => {
    if (!isDragging) return

    function onMouseMove(e: MouseEvent) {
      if (!containerRef.current) return
      const rect = containerRef.current.getBoundingClientRect()
      // Subtract header height (~40px) and footer (~28px)
      const headerHeight = 40
      const footerHeight = 28
      const availableHeight = rect.height - headerHeight - footerHeight
      const relativeY = e.clientY - rect.top - headerHeight
      const pct = Math.min(85, Math.max(25, (relativeY / availableHeight) * 100))
      setSplitPercent(pct)
    }

    function onMouseUp() {
      setIsDragging(false)
    }

    document.addEventListener('mousemove', onMouseMove)
    document.addEventListener('mouseup', onMouseUp)
    return () => {
      document.removeEventListener('mousemove', onMouseMove)
      document.removeEventListener('mouseup', onMouseUp)
    }
  }, [isDragging])

  const isRunning = agentStatus === 'running'

  return (
    <div ref={containerRef} className="flex flex-col h-full select-none">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-card shrink-0">
        <div className="flex items-center gap-2">
          <Terminal size={16} className="text-primary" />
          <span className="text-sm font-semibold text-foreground">Agent Session</span>
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

      {/* Resizable content area */}
      <div className="flex-1 flex flex-col overflow-hidden min-h-0">
        {/* Top: Raw output */}
        <div style={{ height: `${splitPercent}%` }} className="overflow-hidden flex flex-col min-h-0">
          <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 min-h-0 bg-zinc-950/50">
            {outputLines.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center gap-3">
                <Terminal size={28} className="text-muted-foreground/30" />
                <div>
                  <p className="text-xs text-muted-foreground">
                    {projectName
                      ? <>Press <strong>Start</strong> to begin a session for <strong>{projectName}</strong></>
                      : 'Select a project first'
                    }
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
        </div>

        {/* Draggable divider */}
        <div
          onMouseDown={handleDragStart}
          className={`shrink-0 h-2 flex items-center justify-center cursor-row-resize border-y border-border transition-colors ${
            isDragging ? 'bg-primary/20' : 'bg-card hover:bg-muted'
          }`}
        >
          <GripHorizontal size={12} className="text-muted-foreground/50" />
        </div>

        {/* Bottom: Mini chat */}
        <div style={{ height: `${100 - splitPercent}%` }} className="overflow-hidden flex flex-col min-h-0">
          {/* Chat header */}
          <div className="flex items-center gap-1.5 px-3 py-1 border-b border-border/50 bg-card/80 shrink-0">
            <MessageSquare size={12} className="text-primary" />
            <span className="text-[10px] font-bold text-foreground">Agent Chat</span>
            <span className="text-[10px] text-muted-foreground ml-auto">{modelLabel}</span>
          </div>

          {/* Chat messages */}
          <div ref={chatScrollRef} className="flex-1 overflow-y-auto p-2 min-h-0 bg-zinc-950/30 space-y-1.5">
            {chatMessages.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <p className="text-[10px] text-muted-foreground/50">
                  Agent text messages appear here
                </p>
              </div>
            ) : (
              chatMessages.map((msg: { from: 'agent' | 'you'; text: string }, i: number) => (
                <div key={i} className={`flex ${msg.from === 'you' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[90%] px-2 py-1 rounded text-[11px] ${
                    msg.from === 'you'
                      ? 'bg-primary/20 text-primary-foreground'
                      : 'bg-muted/50 text-foreground'
                  }`}>
                    {msg.text}
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Chat input */}
          <div className="shrink-0 border-t border-border/50 bg-card/80 p-1.5 flex gap-1.5">
            <input
              type="text"
              value={chatInput}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setChatInput(e.target.value)}
              onKeyDown={(e: React.KeyboardEvent) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSendChat()
                }
              }}
              placeholder={isRunning ? 'Message the agent...' : 'Start agent first'}
              disabled={!isRunning}
              className="flex-1 min-w-0 bg-background border border-border rounded px-2 py-1 text-[11px] text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-1 focus:ring-primary disabled:opacity-40"
            />
            <button
              onClick={handleSendChat}
              disabled={!isRunning || !chatInput.trim()}
              className="shrink-0 p-1 rounded bg-primary/10 text-primary hover:bg-primary/20 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <Send size={12} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
