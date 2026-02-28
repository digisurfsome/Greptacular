/**
 * DunkStack Comms Chat
 *
 * Chat-style interface that now supports BOTH:
 * 1. File-based walkie-talkie (legacy .agent/comms/ files)
 * 2. Real-time agent chat (Claude SDK integration via WebSocket)
 *
 * When an agent session is running, messages are sent directly to the
 * agent via WebSocket. The agent's streaming responses appear in real-time.
 * When no agent is running, falls back to the file-based comms system.
 */

import { useState, useRef, useEffect, useCallback } from 'react'
import { Send, Radio, User, Bot, Info, Loader2, Wrench, Play, Square } from 'lucide-react'
import type { CommsEntry, AgentState } from '@/hooks/useDunkStack'

interface DunkStackCommsChatProps {
  /** Combined, sorted comms log (file-based) */
  commsLog: CommsEntry[]
  /** Send a message via file-based comms (human → from_human.md) */
  onSendMessage: (content: string, title?: string) => Promise<void>
  /** Current session control mode */
  controlMode: string
  /** Whether connected to WebSocket */
  connected: boolean
  /** Agent state */
  agentState: AgentState
  /** Agent messages (real-time chat) */
  agentMessages: CommsEntry[]
  /** Send message to the running agent */
  onSendAgentMessage: (content: string) => void
  /** Start agent session */
  onStartAgent: () => void
  /** Stop agent session */
  onStopAgent: () => void
}

function SenderIcon({ sender }: { sender: 'human' | 'agent' | 'system' }) {
  switch (sender) {
    case 'human':
      return <User size={14} className="text-amber-500" />
    case 'agent':
      return <Bot size={14} className="text-primary" />
    case 'system':
      return <Info size={14} className="text-muted-foreground" />
  }
}

function senderLabel(sender: 'human' | 'agent' | 'system'): string {
  switch (sender) {
    case 'human': return 'You'
    case 'agent': return 'Agent'
    case 'system': return 'System'
  }
}

function senderBg(sender: 'human' | 'agent' | 'system'): string {
  switch (sender) {
    case 'human': return 'bg-amber-500/10 border-amber-500/20'
    case 'agent': return 'bg-primary/5 border-primary/20'
    case 'system': return 'bg-muted/50 border-border'
  }
}

function ToolCallBadge({ content }: { content: string }) {
  // Extract tool name from "Using tool: **ToolName**"
  const match = content.match(/\*\*(.+?)\*\*/)
  const toolName = match ? match[1] : content
  return (
    <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
      <Wrench size={12} />
      <span className="font-mono">{toolName}</span>
    </div>
  )
}

export function DunkStackCommsChat({
  commsLog,
  onSendMessage,
  controlMode,
  connected,
  agentState,
  agentMessages,
  onSendAgentMessage,
  onStartAgent,
  onStopAgent,
}: DunkStackCommsChatProps): React.JSX.Element {
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Use agent messages when agent is running, otherwise file-based comms
  const messages = agentState.running ? agentMessages : commsLog

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages.length, agentMessages.length])

  const handleSend = useCallback(async () => {
    const trimmed = input.trim()
    if (!trimmed || sending) return

    if (agentState.running) {
      // Send directly to agent via WebSocket
      onSendAgentMessage(trimmed)
      setInput('')
    } else {
      // Legacy file-based send
      setSending(true)
      try {
        await onSendMessage(trimmed)
        setInput('')
      } finally {
        setSending(false)
      }
    }
  }, [input, sending, agentState.running, onSendAgentMessage, onSendMessage])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }, [handleSend])

  return (
    <div className="flex flex-col h-full">
      {/* Chat header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-card shrink-0">
        <div className="flex items-center gap-2">
          {agentState.running ? (
            <>
              <Bot size={16} className="text-primary" />
              <span className="text-sm font-semibold text-foreground">Agent Chat</span>
              {agentState.streaming && (
                <span className="flex items-center gap-1 text-[10px] text-cyan-400">
                  <Loader2 size={10} className="animate-spin" />
                  streaming
                </span>
              )}
            </>
          ) : (
            <>
              <Radio size={16} className="text-amber-500" />
              <span className="text-sm font-semibold text-foreground">DunkStack</span>
            </>
          )}
        </div>
        <div className="flex items-center gap-2">
          {/* Agent start/stop button */}
          {agentState.running ? (
            <button
              onClick={onStopAgent}
              className="flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors"
              title="Stop agent"
            >
              <Square size={10} />
              Stop
            </button>
          ) : (
            <button
              onClick={onStartAgent}
              disabled={!connected}
              className="flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 disabled:opacity-50 transition-colors"
              title="Start agent"
            >
              <Play size={10} />
              Start Agent
            </button>
          )}

          <span className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
            agentState.running ? 'bg-cyan-500/20 text-cyan-400' :
            controlMode === 'autopilot' ? 'bg-emerald-500/20 text-emerald-400' :
            controlMode === 'continue' ? 'bg-blue-500/20 text-blue-400' :
            'bg-muted text-muted-foreground'
          }`}>
            {agentState.running ? 'ACTIVE' : controlMode.toUpperCase()}
          </span>
          <span className={`w-2 h-2 rounded-full ${connected ? 'bg-emerald-500' : 'bg-red-500'}`}
            title={connected ? 'Connected' : 'Disconnected'}
          />
        </div>
      </div>

      {/* Messages area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3 min-h-0">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center gap-3">
            {agentState.running ? (
              <>
                <Bot size={32} className="text-primary/30" />
                <div>
                  <p className="text-sm text-muted-foreground">Agent is ready</p>
                  <p className="text-xs text-muted-foreground/60 mt-1">
                    Send a message to start working with the agent.
                  </p>
                </div>
              </>
            ) : (
              <>
                <Radio size={32} className="text-muted-foreground/30" />
                <div>
                  <p className="text-sm text-muted-foreground">No agent running</p>
                  <p className="text-xs text-muted-foreground/60 mt-1">
                    Click "Start Agent" to launch a coding agent with the selected model.
                    <br />
                    Select a project from the sidebar for the agent to work on.
                  </p>
                </div>
              </>
            )}
          </div>
        ) : (
          messages.map((entry) => {
            // Render tool calls as compact badges
            if (entry.sender === 'system' && entry.title && entry.content.startsWith('Using tool:')) {
              return (
                <div key={entry.id} className="px-3 py-1">
                  <ToolCallBadge content={entry.content} />
                </div>
              )
            }

            // Render status messages compactly
            if (entry.sender === 'system' && entry.title === 'Status') {
              return (
                <div key={entry.id} className="px-3 py-1 text-xs text-muted-foreground italic">
                  {entry.content}
                </div>
              )
            }

            return (
              <div
                key={entry.id}
                className={`flex gap-2 p-3 rounded-lg border ${senderBg(entry.sender)}`}
              >
                <div className="shrink-0 mt-0.5">
                  <SenderIcon sender={entry.sender} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline gap-2 mb-1">
                    <span className="text-xs font-bold text-foreground">
                      {senderLabel(entry.sender)}
                    </span>
                    {entry.title && entry.title !== 'Response' && entry.title !== 'Message' && (
                      <span className="text-[10px] text-muted-foreground truncate">
                        {entry.title}
                      </span>
                    )}
                    <span className="text-[10px] text-muted-foreground/60 ml-auto shrink-0">
                      {entry.timestamp}
                    </span>
                  </div>
                  <div className="text-sm text-foreground whitespace-pre-wrap break-words">
                    {entry.content}
                  </div>
                </div>
              </div>
            )
          })
        )}

        {/* Streaming indicator */}
        {agentState.streaming && (
          <div className="flex items-center gap-2 px-3 py-2 text-xs text-cyan-400">
            <Loader2 size={12} className="animate-spin" />
            <span>Agent is thinking...</span>
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="shrink-0 border-t border-border bg-card p-3">
        <div className="flex gap-2 items-end">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              agentState.running
                ? 'Send message to agent...'
                : 'Start an agent first, then send messages here...'
            }
            disabled={!agentState.running && !commsLog.length}
            className="flex-1 min-h-[40px] max-h-[120px] resize-none rounded-lg border border-border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50"
            rows={1}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || sending || agentState.streaming}
            className="shrink-0 h-10 w-10 flex items-center justify-center rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Send message"
          >
            <Send size={16} />
          </button>
        </div>
        <div className="flex items-center gap-2 mt-1.5">
          <span className="text-[10px] text-muted-foreground">
            Enter to send, Shift+Enter for newline
          </span>
        </div>
      </div>
    </div>
  )
}
