/**
 * DesignGuidePanel - Skinny AI chat column for the design step.
 *
 * A permanent chat interface that sits between the controls and preview columns.
 * The AI can send both text messages and structured actions to control the design page.
 * Adapts to the user's pace - if they're clicking around, the AI goes quiet;
 * if they pause, it re-engages.
 */

import { useState, useRef, useEffect, useCallback } from 'react'
import { Send, Bot, User, Loader2, MessageCircle, ChevronDown } from 'lucide-react'
import type { DesignGuideAction } from '../lib/types'
import { isSubmitEnter } from '../lib/keyboard'

interface GuideMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: number
  action?: DesignGuideAction  // Optional action that was executed
}

interface DesignGuidePanelProps {
  /** Callback when the AI sends an action to control the page */
  onAction: (action: DesignGuideAction) => void
  /** Whether the panel is connected to the backend */
  isConnected?: boolean
  /** Current context summary shown to the user */
  contextSummary?: string
}

export function DesignGuidePanel({
  onAction,
  isConnected = false,
  contextSummary,
}: DesignGuidePanelProps) {
  const [messages, setMessages] = useState<GuideMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: "Hey! I'm your design guide. Are you familiar with design styles and colors, or would you like me to walk you through everything in plain terms? Just tell me what kind of app you're building and I'll help you find the right look.",
      timestamp: Date.now(),
    },
  ])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [isMinimized, setIsMinimized] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Suppress unused for now - will be connected to WebSocket later
  void onAction
  void isConnected
  void contextSummary

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  // Focus input when not typing
  useEffect(() => {
    if (!isTyping && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isTyping])

  const handleSend = useCallback(() => {
    const trimmed = input.trim()
    if (!trimmed || isTyping) return

    const userMessage: GuideMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: trimmed,
      timestamp: Date.now(),
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsTyping(true)

    // Reset textarea height
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
    }

    // TODO: Send to WebSocket backend
    // For now, show a placeholder response after a brief delay
    setTimeout(() => {
      const assistantMessage: GuideMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: "I hear you! Once the backend is connected, I'll be able to help pick styles, adjust colors, and walk you through each design decision. For now, feel free to explore the styles on the left!",
        timestamp: Date.now(),
      }
      setMessages(prev => [...prev, assistantMessage])
      setIsTyping(false)
    }, 1000)
  }, [input, isTyping])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (isSubmitEnter(e)) {
      e.preventDefault()
      handleSend()
    }
  }

  if (isMinimized) {
    return (
      <div className="w-10 shrink-0 border-r bg-muted/30 flex flex-col items-center py-2">
        <button
          onClick={() => setIsMinimized(false)}
          className="p-1.5 rounded-md hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
          title="Open AI Guide"
        >
          <MessageCircle size={16} />
        </button>
        <div className="mt-2 text-[9px] font-medium text-muted-foreground tracking-wider"
          style={{ writingMode: 'vertical-rl', textOrientation: 'mixed' }}
        >
          AI GUIDE
        </div>
      </div>
    )
  }

  return (
    <div className="w-[200px] shrink-0 border-r border-border/50 flex flex-col bg-background">
      {/* Header */}
      <div className="shrink-0 flex items-center justify-between px-2 py-1.5 border-b bg-primary/5">
        <div className="flex items-center gap-1.5">
          <Bot size={13} className="text-primary" />
          <span className="text-[10px] font-bold uppercase tracking-wider text-primary">AI Guide</span>
        </div>
        <button
          onClick={() => setIsMinimized(true)}
          className="p-0.5 rounded hover:bg-muted transition-colors text-muted-foreground"
          title="Minimize"
        >
          <ChevronDown size={12} />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto min-h-0 p-2 space-y-2">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex gap-1.5 ${msg.role === 'user' ? 'justify-end' : ''}`}>
            {msg.role === 'assistant' && (
              <div className="w-5 h-5 rounded-full bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
                <Bot size={10} className="text-primary" />
              </div>
            )}
            <div
              className={`max-w-[90%] rounded-lg px-2 py-1.5 text-[11px] leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted/50 text-foreground'
              }`}
            >
              {msg.content}
            </div>
            {msg.role === 'user' && (
              <div className="w-5 h-5 rounded-full bg-muted flex items-center justify-center shrink-0 mt-0.5">
                <User size={10} />
              </div>
            )}
          </div>
        ))}

        {/* Typing indicator */}
        {isTyping && (
          <div className="flex gap-1.5">
            <div className="w-5 h-5 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
              <Bot size={10} className="text-primary" />
            </div>
            <div className="bg-muted/50 rounded-lg px-2 py-1.5">
              <div className="flex gap-0.5">
                <span className="w-1.5 h-1.5 bg-primary/40 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 bg-primary/40 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 bg-primary/40 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="shrink-0 border-t p-1.5 bg-card">
        <div className="flex gap-1">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => {
              setInput(e.target.value)
              e.target.style.height = 'auto'
              e.target.style.height = `${Math.min(e.target.scrollHeight, 80)}px`
            }}
            onKeyDown={handleKeyDown}
            placeholder="Ask me anything..."
            className="flex-1 resize-none text-[11px] min-h-[28px] max-h-[80px] rounded-md border border-border bg-background px-2 py-1 focus:outline-none focus:ring-1 focus:ring-primary/50"
            disabled={isTyping}
            rows={1}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isTyping}
            className="shrink-0 w-7 h-7 rounded-md bg-primary text-primary-foreground flex items-center justify-center disabled:opacity-50 hover:bg-primary/90 transition-colors"
          >
            {isTyping ? (
              <Loader2 size={12} className="animate-spin" />
            ) : (
              <Send size={11} />
            )}
          </button>
        </div>
        <p className="text-[8px] text-muted-foreground mt-0.5 px-0.5">
          Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  )
}
