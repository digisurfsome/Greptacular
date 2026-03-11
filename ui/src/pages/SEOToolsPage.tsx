/**
 * SEOToolsPage - SEO Keyword Research Tool page for AutoForge.
 *
 * Embeds the standalone keyword research HTML app in an iframe,
 * with a collapsible AI chat sidebar for keyword analysis powered
 * by the user's subscription.
 *
 * Layout:
 *   - Breadcrumb bar (back to AutoForge, page title, AI Assist toggle)
 *   - Main content: iframe loading /api/seo-tools/app
 *   - Right panel: AI Keyword Analyst chat (WebSocket-based, collapsible)
 */

import { useState, useRef, useEffect, useCallback } from 'react'
import {
  ArrowLeft,
  Search,
  Sparkles,
  Send,
  X,
  Loader2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

/** Resolve the WebSocket URL for the SEO tools AI endpoint. */
function buildWsUrl(): string {
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${window.location.host}/api/seo-tools/ws`
}

/**
 * Lightweight markdown renderer for chat messages.
 * Handles bold, italic, inline code, fenced code blocks, and line breaks.
 * HTML entities are escaped first to prevent injection.
 */
function renderMarkdown(text: string): string {
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  // Fenced code blocks (```...```)
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_m, _lang, code) => {
    return `<pre class="bg-gray-100 rounded-md p-3 my-2 overflow-x-auto text-xs font-mono border-2 border-black"><code>${code.trim()}</code></pre>`
  })

  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-xs font-mono border border-gray-300">$1</code>')

  // Bold
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')

  // Italic
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')

  // Line breaks
  html = html.replace(/\n/g, '<br />')

  return html
}

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export function SEOToolsPage(): React.JSX.Element {
  const [aiPanelOpen, setAiPanelOpen] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)

  const wsRef = useRef<WebSocket | null>(null)
  const messagesEndRef = useRef<HTMLDivElement | null>(null)
  const inputRef = useRef<HTMLTextAreaElement | null>(null)
  // Buffer for accumulating streamed chunks without stale closure issues
  const streamBufferRef = useRef('')

  /* ---- Auto-scroll chat to bottom when messages change ---- */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  /* ---- WebSocket lifecycle: connect when panel opens, disconnect on close ---- */
  const connectWebSocket = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState <= WebSocket.OPEN) {
      return // already connected or connecting
    }

    const ws = new WebSocket(buildWsUrl())
    wsRef.current = ws

    ws.addEventListener('open', () => {
      // Initiate the session with provider/model handshake
      ws.send(JSON.stringify({
        type: 'start',
        provider: 'claude',
        model: 'claude-sonnet-4-6',
      }))
    })

    ws.addEventListener('message', (event) => {
      try {
        const data = JSON.parse(event.data)

        if (data.type === 'text' || data.type === 'chunk' || data.type === 'delta') {
          // Accumulate streamed text into the current assistant message
          const chunk = data.content ?? data.text ?? ''
          streamBufferRef.current += chunk
          const updatedContent = streamBufferRef.current

          setMessages((prev) => {
            const last = prev[prev.length - 1]
            if (last && last.role === 'assistant') {
              return [...prev.slice(0, -1), { role: 'assistant', content: updatedContent }]
            }
            return [...prev, { role: 'assistant', content: updatedContent }]
          })
        } else if (data.type === 'response_done' || data.type === 'done' || data.type === 'end') {
          setIsStreaming(false)
          streamBufferRef.current = ''
        } else if (data.type === 'error') {
          setIsStreaming(false)
          streamBufferRef.current = ''
          setMessages((prev) => [
            ...prev,
            { role: 'assistant', content: `Error: ${data.content ?? data.message ?? 'Unknown error occurred.'}` },
          ])
        }
      } catch {
        // Non-JSON message — treat entire payload as a text chunk
        streamBufferRef.current += event.data
        const updatedContent = streamBufferRef.current

        setMessages((prev) => {
          const last = prev[prev.length - 1]
          if (last && last.role === 'assistant') {
            return [...prev.slice(0, -1), { role: 'assistant', content: updatedContent }]
          }
          return [...prev, { role: 'assistant', content: updatedContent }]
        })
      }
    })

    ws.addEventListener('close', () => {
      wsRef.current = null
      setIsStreaming(false)
      streamBufferRef.current = ''
    })

    ws.addEventListener('error', () => {
      wsRef.current = null
      setIsStreaming(false)
      streamBufferRef.current = ''
    })
  }, [])

  const disconnectWebSocket = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [])

  /* ---- Toggle AI panel ---- */
  const toggleAIPanel = useCallback(() => {
    setAiPanelOpen((prev) => {
      const opening = !prev
      if (opening) {
        // Defer connect to next tick so the panel DOM is rendered first
        setTimeout(() => connectWebSocket(), 0)
      } else {
        disconnectWebSocket()
      }
      return opening
    })
  }, [connectWebSocket, disconnectWebSocket])

  /* ---- Cleanup WebSocket on unmount ---- */
  useEffect(() => {
    return () => {
      disconnectWebSocket()
    }
  }, [disconnectWebSocket])

  /* ---- Send a user message ---- */
  const sendMessage = useCallback(() => {
    const text = inputValue.trim()
    if (!text || isStreaming) return

    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setInputValue('')
    setIsStreaming(true)
    streamBufferRef.current = ''

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'message', content: text }))
    } else {
      // Reconnect and queue the message with a retry loop
      connectWebSocket()
      const checkAndSend = setInterval(() => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ type: 'message', content: text }))
          clearInterval(checkAndSend)
        }
      }, 100)
      // Safety: stop retrying after 5 seconds
      setTimeout(() => clearInterval(checkAndSend), 5000)
    }
  }, [inputValue, isStreaming, connectWebSocket])

  /* ---- Handle Enter key in textarea (Shift+Enter for newline) ---- */
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        sendMessage()
      }
    },
    [sendMessage],
  )

  /* ---- Auto-resize textarea helper ---- */
  const handleTextareaInput = useCallback((e: React.FormEvent<HTMLTextAreaElement>) => {
    const target = e.target as HTMLTextAreaElement
    target.style.height = 'auto'
    target.style.height = `${Math.min(target.scrollHeight, 120)}px`
  }, [])

  /* ---------------------------------------------------------------- */
  /*  Render                                                           */
  /* ---------------------------------------------------------------- */

  return (
    <div className="h-screen flex flex-col bg-[var(--color-bg)]">
      {/* ---- Breadcrumb bar ---- */}
      <div className="flex items-center gap-3 px-4 py-2 border-b-3 border-black bg-white shrink-0">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => { window.location.hash = '' }}
          title="Back to AutoForge"
        >
          <ArrowLeft size={16} />
        </Button>
        <Search size={18} className="text-gray-600" />
        <h1 className="text-lg font-bold tracking-tight">SEO Tools</h1>
        <div className="flex-1" />
        <Button
          variant="ghost"
          size="sm"
          className="gap-1.5"
          onClick={toggleAIPanel}
          title="Toggle AI Keyword Analyst"
        >
          <Sparkles size={16} />
          <span className="text-xs">AI Assist</span>
        </Button>
      </div>

      {/* ---- Main content area ---- */}
      <div className="flex-1 flex overflow-hidden">
        {/* Iframe: standalone keyword research tool */}
        <div className="flex-1 min-w-0">
          <iframe
            src="/api/seo-tools/app"
            className="w-full h-full border-0"
            title="SEO Keyword Research"
          />
        </div>

        {/* AI Chat Panel (collapsible right sidebar) */}
        {aiPanelOpen && (
          <div className="w-[400px] shrink-0 border-l-3 border-black flex flex-col bg-white">
            {/* Panel header */}
            <div className="flex items-center gap-2 px-4 py-3 border-b-3 border-black bg-amber-50 shrink-0">
              <Sparkles size={16} className="text-amber-600" />
              <span className="font-bold text-sm tracking-tight">AI Keyword Analyst</span>
              <div className="flex-1" />
              <Button
                variant="ghost"
                size="icon-xs"
                onClick={toggleAIPanel}
                title="Close AI panel"
              >
                <X size={14} />
              </Button>
            </div>

            {/* Chat messages */}
            <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3">
              {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center text-center text-gray-400 gap-2 py-16 px-4">
                  <Sparkles size={28} className="text-amber-400" />
                  <p className="text-sm font-bold text-gray-500">AI Keyword Analyst</p>
                  <p className="text-xs leading-relaxed max-w-[260px]">
                    Ask about keyword difficulty, search volume trends, content gaps, or get
                    suggestions for your SEO strategy.
                  </p>
                </div>
              )}

              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[85%] rounded-lg px-3 py-2 text-sm leading-relaxed ${
                      msg.role === 'user'
                        ? 'bg-black text-white border-2 border-black'
                        : 'bg-gray-50 text-gray-800 border-2 border-gray-200'
                    }`}
                  >
                    {msg.role === 'assistant' ? (
                      <div
                        className="prose prose-sm max-w-none [&_pre]:my-2 [&_code]:text-xs"
                        dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }}
                      />
                    ) : (
                      <span className="whitespace-pre-wrap">{msg.content}</span>
                    )}
                  </div>
                </div>
              ))}

              {/* Streaming indicator (shown when waiting for first chunk) */}
              {isStreaming && messages[messages.length - 1]?.role !== 'assistant' && (
                <div className="flex justify-start">
                  <div className="bg-gray-50 border-2 border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-400 flex items-center gap-2">
                    <Loader2 size={14} className="animate-spin" />
                    <span>Analyzing...</span>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Chat input */}
            <div className="border-t-3 border-black p-3 shrink-0">
              <div className="flex items-end gap-2">
                <textarea
                  ref={inputRef}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleKeyDown}
                  onInput={handleTextareaInput}
                  placeholder="Ask about keywords, SEO strategy..."
                  rows={1}
                  className="flex-1 resize-none rounded-md border-2 border-black px-3 py-2 text-sm
                    placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-amber-400
                    max-h-[120px] overflow-y-auto"
                  disabled={isStreaming}
                />
                <Button
                  size="icon-sm"
                  onClick={sendMessage}
                  disabled={!inputValue.trim() || isStreaming}
                  title="Send message"
                  className="shrink-0 bg-black text-white hover:bg-gray-800 border-2 border-black"
                >
                  {isStreaming ? (
                    <Loader2 size={14} className="animate-spin" />
                  ) : (
                    <Send size={14} />
                  )}
                </Button>
              </div>
              <p className="text-[10px] text-gray-400 mt-1.5 px-1">
                Press Enter to send, Shift+Enter for new line
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
