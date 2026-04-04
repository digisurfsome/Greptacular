/**
 * PipelineOutputViewer
 *
 * Full-size output display for the Skill Pipeline. Replaces WorkspaceChat
 * in the pipeline panel's right column. No WebSocket, no hanging — just
 * polls the pipeline status API and displays streaming output.
 *
 * Features:
 * - Streaming stage output with auto-scroll
 * - Agent question display with answer template
 * - File/image upload for answers
 * - Per-stage token usage display
 * - Stage headers with status badges
 */

import { useState, useRef, useEffect, useCallback } from 'react'
import {
  Send,
  Loader2,
  CheckCircle2,
  Clock,
  XCircle,
  Upload,
  X,
  Image,
  FileText,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import type { PipelineStatusResponse } from '@/lib/api'
import { sendPipelineAnswer } from '@/lib/api'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface PipelineOutputViewerProps {
  pipelineId: string | null
  status: PipelineStatusResponse | null
}

interface Attachment {
  name: string
  type: string
  content: string // base64 or text content
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`
  return String(n)
}

const STAGE_STATUS_CONFIG: Record<string, { color: string; icon: typeof Clock; label: string }> = {
  pending:   { color: 'text-muted-foreground', icon: Clock, label: 'Pending' },
  running:   { color: 'text-cyan-500', icon: Loader2, label: 'Running' },
  completed: { color: 'text-green-500', icon: CheckCircle2, label: 'Done' },
  failed:    { color: 'text-red-500', icon: XCircle, label: 'Failed' },
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function PipelineOutputViewer({ pipelineId, status }: PipelineOutputViewerProps) {
  const [inputText, setInputText] = useState('')
  const [sending, setSending] = useState(false)
  const [attachments, setAttachments] = useState<Attachment[]>([])
  const outputEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-scroll to bottom when new output arrives
  useEffect(() => {
    outputEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [status?.stages])

  // Pre-fill input with formatted questions when agent is waiting
  useEffect(() => {
    if (status?.waiting_for_answer && status?.waiting_question) {
      const lines = status.waiting_question.split('\n').filter((l: string) => l.trim())
      const numbered = lines.filter((l: string) => /^\d+[\.\)]\s/.test(l.trim()))

      if (numbered.length > 0) {
        const formatted = numbered
          .map((q: string) => `${q.trim()}\nAnswer: \n`)
          .join('\n')
        setInputText(formatted)
      }
      textareaRef.current?.focus()
    }
  }, [status?.waiting_for_answer, status?.waiting_question])

  const handleSend = useCallback(async () => {
    if (!pipelineId || !inputText.trim()) return
    setSending(true)
    try {
      // Include attachment info in the message if any
      let message = inputText.trim()
      if (attachments.length > 0) {
        const attachmentText = attachments
          .map(a => `\n\n[Attached: ${a.name}]\n${a.content}`)
          .join('')
        message += attachmentText
      }
      await sendPipelineAnswer(pipelineId, message)
      setInputText('')
      setAttachments([])
    } catch (e) {
      console.error('Failed to send:', e)
    } finally {
      setSending(false)
    }
  }, [pipelineId, inputText, attachments])

  const handleFileUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files) return

    Array.from(files).forEach(file => {
      const reader = new FileReader()
      if (file.type.startsWith('image/')) {
        reader.onload = () => {
          setAttachments(prev => [...prev, {
            name: file.name,
            type: file.type,
            content: `[Image: ${file.name}, ${(file.size / 1024).toFixed(0)}KB]`,
          }])
        }
        reader.readAsDataURL(file)
      } else {
        reader.onload = () => {
          setAttachments(prev => [...prev, {
            name: file.name,
            type: file.type,
            content: reader.result as string,
          }])
        }
        reader.readAsText(file)
      }
    })
    e.target.value = ''
  }, [])

  const removeAttachment = useCallback((index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index))
  }, [])

  // No pipeline running — show idle state
  if (!pipelineId || !status) {
    return (
      <div className="flex flex-col h-full bg-background">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center space-y-3">
            <div className="text-4xl opacity-20">⚡</div>
            <p className="text-sm text-muted-foreground">Pipeline output will appear here</p>
            <p className="text-xs text-muted-foreground/60">Configure and launch a pipeline from the left panel</p>
          </div>
        </div>
      </div>
    )
  }

  const isRunning = status.status === 'running'
  const isWaiting = status.waiting_for_answer

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header bar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-muted/30 shrink-0">
        <div className="flex items-center gap-3">
          <span className="text-xs font-bold text-foreground">Pipeline Output</span>
          <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${
            isRunning ? 'bg-cyan-500/20 text-cyan-600' :
            status.status === 'completed' ? 'bg-green-500/20 text-green-600' :
            status.status === 'failed' ? 'bg-red-500/20 text-red-600' :
            'bg-muted text-muted-foreground'
          }`}>
            {status.status.toUpperCase()}
          </span>
        </div>
        <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
          <span>Tokens: {formatTokens(status.total_tokens)}</span>
          <span>Budget: {formatTokens(status.token_budget)}</span>
          <span>{Math.round((status.total_tokens / status.token_budget) * 100)}%</span>
        </div>
      </div>

      {/* Token budget bar */}
      <div className="h-1 bg-muted shrink-0">
        <div
          className="h-full bg-emerald-500 transition-all"
          style={{ width: `${Math.min(100, (status.total_tokens / status.token_budget) * 100)}%` }}
        />
      </div>

      {/* Output area — scrollable */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4">
        {status.stages.map((stage, i) => {
          const cfg = STAGE_STATUS_CONFIG[stage.status] || STAGE_STATUS_CONFIG.pending
          const Icon = cfg.icon

          return (
            <div key={i}>
              {/* Stage header */}
              <div className="flex items-center gap-2 mb-2 sticky top-0 bg-background/90 backdrop-blur-sm py-1 z-10">
                <Icon
                  size={14}
                  className={`${cfg.color} ${stage.status === 'running' ? 'animate-spin' : ''}`}
                />
                <span className="text-xs font-bold text-foreground">
                  Stage {stage.stage_index}: {stage.label}
                </span>
                {stage.status === 'completed' && (
                  <span className="text-[10px] text-muted-foreground">
                    {formatTokens(stage.tokens_used)} tokens · {stage.duration_seconds.toFixed(0)}s
                  </span>
                )}
                {stage.status === 'running' && stage.tokens_used > 0 && (
                  <span className="text-[10px] text-cyan-500">
                    {formatTokens(stage.tokens_used)} tokens
                  </span>
                )}
              </div>

              {/* Stage output */}
              {stage.output && (
                <div className="pl-5 border-l-2 border-border">
                  <pre className="text-xs font-mono whitespace-pre-wrap text-foreground/90 leading-relaxed">
                    {stage.output}
                  </pre>
                </div>
              )}

              {/* Running indicator */}
              {stage.status === 'running' && !stage.output && (
                <div className="pl-5 border-l-2 border-cyan-500/30">
                  <div className="flex items-center gap-2 text-xs text-cyan-500">
                    <Loader2 size={12} className="animate-spin" />
                    Processing...
                  </div>
                </div>
              )}

              {/* Error */}
              {stage.error && (
                <div className="pl-5 border-l-2 border-red-500/30 mt-1">
                  <p className="text-xs text-red-500">{stage.error}</p>
                </div>
              )}
            </div>
          )
        })}
        <div ref={outputEndRef} />
      </div>

      {/* Agent question display */}
      {isWaiting && status.waiting_question && (
        <div className="px-4 py-2 bg-amber-500/10 border-t border-amber-500/30 shrink-0">
          <p className="text-[10px] font-semibold text-amber-600 uppercase tracking-wider mb-1">Agent Question</p>
          <p className="text-xs text-amber-700 dark:text-amber-300 whitespace-pre-wrap">
            {status.waiting_question}
          </p>
        </div>
      )}

      {/* Attachments bar */}
      {attachments.length > 0 && (
        <div className="flex gap-2 px-4 py-1.5 bg-muted/30 border-t border-border shrink-0 overflow-x-auto">
          {attachments.map((att, i) => (
            <div key={i} className="flex items-center gap-1 px-2 py-0.5 rounded bg-muted text-[10px] text-foreground shrink-0">
              {att.type.startsWith('image/') ? <Image size={10} /> : <FileText size={10} />}
              <span className="max-w-[120px] truncate">{att.name}</span>
              <button onClick={() => removeAttachment(i)} className="text-muted-foreground hover:text-red-500">
                <X size={10} />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Input area — always visible when pipeline is running */}
      {(isRunning || isWaiting) && (
        <div className="border-t border-border px-4 py-3 shrink-0 bg-background">
          <div className="flex gap-2">
            <div className="flex-1 flex flex-col gap-1">
              <textarea
                ref={textareaRef}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                    e.preventDefault()
                    handleSend()
                  }
                }}
                placeholder={isWaiting ? 'Type your answers...' : 'Send message to agent...'}
                rows={isWaiting ? Math.max(4, inputText.split('\n').length) : 2}
                className="w-full rounded-md border border-border bg-input px-3 py-2 text-sm font-mono text-foreground placeholder:text-muted-foreground/60 outline-none ring-ring focus:ring-1 resize-y"
              />
              <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                <span>Ctrl+Enter to send</span>
                {isWaiting && <span className="text-amber-500 font-semibold">· Waiting for your answer</span>}
              </div>
            </div>
            <div className="flex flex-col gap-1">
              <Button
                size="sm"
                className="h-8 px-3 bg-emerald-600 hover:bg-emerald-700 text-white"
                onClick={handleSend}
                disabled={!inputText.trim() || sending}
              >
                {sending ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="h-8 px-3"
                onClick={() => fileInputRef.current?.click()}
                title="Attach file or image"
              >
                <Upload size={14} />
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".md,.txt,.json,.csv,.png,.jpg,.jpeg,.gif,.webp"
                onChange={handleFileUpload}
                className="hidden"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
