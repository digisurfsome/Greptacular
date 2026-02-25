/**
 * DunkStack Comms Chat
 *
 * Chat-style interface for the file-based walkie-talkie system.
 * Reads/writes to .agent/comms/ files (to_human.md, from_human.md).
 * Messages display in chronological order with sender color coding.
 *
 * This is the file-based version of the workspace walkie-talkie:
 * instead of WebSocket injection into a running agent, messages are
 * written to files that the agent reads on each turn.
 */

import { useState, useRef, useEffect, useCallback } from 'react'
import { Send, Radio, User, Bot, Info } from 'lucide-react'
import type { CommsEntry } from '@/hooks/useDunkStack'

interface DunkStackCommsChatProps {
  /** Combined, sorted comms log */
  commsLog: CommsEntry[]
  /** Send a message (human → agent via from_human.md) */
  onSendMessage: (content: string, title?: string) => Promise<void>
  /** Current session control mode */
  controlMode: string
  /** Whether connected to WebSocket */
  connected: boolean
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

export function DunkStackCommsChat({
  commsLog,
  onSendMessage,
  controlMode,
  connected,
}: DunkStackCommsChatProps): React.JSX.Element {
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [commsLog.length])

  const handleSend = useCallback(async () => {
    const trimmed = input.trim()
    if (!trimmed || sending) return

    setSending(true)
    try {
      await onSendMessage(trimmed)
      setInput('')
    } finally {
      setSending(false)
    }
  }, [input, sending, onSendMessage])

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
          <Radio size={16} className="text-amber-500" />
          <span className="text-sm font-semibold text-foreground">File Comms</span>
          <span className="text-[10px] text-muted-foreground">
            (.agent/comms/)
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
            controlMode === 'autopilot' ? 'bg-emerald-500/20 text-emerald-400' :
            controlMode === 'continue' ? 'bg-blue-500/20 text-blue-400' :
            'bg-muted text-muted-foreground'
          }`}>
            {controlMode.toUpperCase()}
          </span>
          <span className={`w-2 h-2 rounded-full ${connected ? 'bg-emerald-500' : 'bg-red-500'}`}
            title={connected ? 'Connected' : 'Disconnected'}
          />
        </div>
      </div>

      {/* Messages area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3 min-h-0">
        {commsLog.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center gap-3">
            <Radio size={32} className="text-muted-foreground/30" />
            <div>
              <p className="text-sm text-muted-foreground">No messages yet</p>
              <p className="text-xs text-muted-foreground/60 mt-1">
                Messages written to .agent/comms/ files will appear here.
                <br />
                Send a message to write to from_human.md.
              </p>
            </div>
          </div>
        ) : (
          commsLog.map((entry) => (
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
                  {entry.title && (
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
          ))
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
            placeholder="Send message to agent (writes to from_human.md)..."
            className="flex-1 min-h-[40px] max-h-[120px] resize-none rounded-lg border border-border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
            rows={1}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || sending}
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
