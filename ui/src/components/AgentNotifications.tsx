/**
 * Agent Notifications Panel (Walkie-Talkie)
 *
 * Features:
 * - Chat messages (agent ↔ user) with category styling
 * - Countdown timer when agent is waiting (chat_with_user)
 * - "Keep Going" quick-dismiss button
 * - Auto-reply on timeout (configurable in settings)
 * - Roadmap display: agent sends [ROADMAP] messages rendered as checklist
 * - Progress tracking: [PROGRESS] messages update the roadmap
 * - Finishing-soon indicator: [FINISHING] messages show warning
 * - Image/file attachments: paste, drag-drop, or click to attach
 */

import { useState, useRef, useEffect, useCallback } from 'react'
import { Send, MessageCircle, ChevronDown, ChevronUp, Play, Paperclip, X, AlertTriangle } from 'lucide-react'
import { sendToAgentInbox } from '../lib/api'
import { useSettings } from '../hooks/useProjects'

// Category styling for agent messages
const CATEGORY_STYLES: Record<string, { bg: string; border: string; icon: string }> = {
  status: { bg: 'bg-blue-50', border: 'border-blue-300', icon: '\u{1F4CB}' },
  question: { bg: 'bg-purple-50', border: 'border-purple-300', icon: '\u{2753}' },
  discovery: { bg: 'bg-green-50', border: 'border-green-300', icon: '\u{1F50D}' },
  warning: { bg: 'bg-amber-50', border: 'border-amber-300', icon: '\u{26A0}\u{FE0F}' },
  milestone: { bg: 'bg-emerald-50', border: 'border-emerald-300', icon: '\u{1F3AF}' },
}

// Phase display names and icons
const PHASE_DISPLAY: Record<string, { label: string; icon: string; color: string }> = {
  acknowledged: { label: 'Acknowledged', icon: '\u{1F44B}', color: 'text-blue-600' },
  reading: { label: 'Reading Code', icon: '\u{1F4D6}', color: 'text-indigo-600' },
  planning: { label: 'Planning', icon: '\u{1F5FA}\u{FE0F}', color: 'text-violet-600' },
  building: { label: 'Building', icon: '\u{1F528}', color: 'text-orange-600' },
  testing: { label: 'Testing', icon: '\u{1F9EA}', color: 'text-cyan-600' },
  debugging: { label: 'Debugging', icon: '\u{1F41B}', color: 'text-red-600' },
  complete: { label: 'Complete', icon: '\u{2705}', color: 'text-green-600' },
  waiting: { label: 'Waiting for you...', icon: '\u{1F4AC}', color: 'text-purple-600' },
}

const ALLOWED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.pdf', '.txt', '.md', '.json', '.csv']
const MAX_ATTACHMENT_SIZE = 5 * 1024 * 1024

interface RoadmapStep {
  index: number
  label: string
  done: boolean
}

interface PendingAttachment {
  file: File
  preview?: string // data URL for images
}

interface AgentNotificationsProps {
  projectName: string | null
  agentMessages: Array<{ id: string; text: string; category: string; timestamp: string }>
  agentPhase: { phase: string; detail: string; timestamp: string } | null
  agentStatus: string
}

/**
 * Parse [ROADMAP] messages into step objects.
 * Format: "[ROADMAP] 1. Step one | 2. Step two | 3. Step three"
 */
function parseRoadmap(text: string): RoadmapStep[] {
  const body = text.replace(/^\[ROADMAP\]\s*/i, '')
  return body.split('|').map((part, i) => {
    const trimmed = part.trim().replace(/^\d+\.\s*/, '')
    return { index: i + 1, label: trimmed, done: false }
  }).filter(s => s.label.length > 0)
}

/**
 * Parse [PROGRESS] messages to get completed step number.
 * Format: "[PROGRESS] 2/4 Step label — done"
 */
function parseProgress(text: string): { step: number; total: number } | null {
  const match = text.match(/^\[PROGRESS\]\s*(\d+)\/(\d+)/)
  if (match) return { step: parseInt(match[1], 10), total: parseInt(match[2], 10) }
  return null
}

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = reader.result as string
      // Strip "data:mime;base64," prefix
      resolve(result.split(',')[1] || '')
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

export function AgentNotifications({ projectName, agentMessages, agentPhase, agentStatus }: AgentNotificationsProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [inputText, setInputText] = useState('')
  const [sending, setSending] = useState(false)
  const [sentMessages, setSentMessages] = useState<Array<{ id: string; text: string; timestamp: string }>>([])
  const [countdown, setCountdown] = useState<number | null>(null)
  const [autoReplied, setAutoReplied] = useState(false)
  const [pendingAttachments, setPendingAttachments] = useState<PendingAttachment[]>([])
  const [roadmap, setRoadmap] = useState<RoadmapStep[]>([])
  const [isFinishing, setIsFinishing] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const autoReplyRef = useRef(false)

  const { data: settings } = useSettings()

  const isAgentRunning = agentStatus === 'running' || agentStatus === 'paused'
  const isWaitingForReply = agentPhase?.phase === 'waiting'
  const waitTimeout = settings?.comm_wait_timeout ?? 120
  const autoReplyEnabled = settings?.comm_auto_reply ?? true

  // Process agent messages for roadmap/progress/finishing signals
  useEffect(() => {
    for (const msg of agentMessages) {
      if (msg.text.startsWith('[ROADMAP]')) {
        setRoadmap(parseRoadmap(msg.text))
        setIsFinishing(false)
      } else if (msg.text.startsWith('[PROGRESS]')) {
        const prog = parseProgress(msg.text)
        if (prog) {
          setRoadmap(prev => prev.map(s => ({ ...s, done: s.index <= prog.step })))
        }
      } else if (msg.text.startsWith('[FINISHING]')) {
        setIsFinishing(true)
      }
    }
  }, [agentMessages])

  // Clear roadmap when agent stops
  useEffect(() => {
    if (!isAgentRunning) {
      setRoadmap([])
      setIsFinishing(false)
    }
  }, [isAgentRunning])

  // Countdown timer when agent is waiting
  useEffect(() => {
    if (!isWaitingForReply || !agentPhase?.timestamp) {
      setCountdown(null)
      setAutoReplied(false)
      autoReplyRef.current = false
      return
    }

    const startTime = new Date(agentPhase.timestamp).getTime()

    const tick = () => {
      const elapsed = (Date.now() - startTime) / 1000
      const remaining = Math.max(0, waitTimeout - elapsed)
      setCountdown(Math.ceil(remaining))

      if (remaining <= 0 && autoReplyEnabled && !autoReplyRef.current && projectName) {
        autoReplyRef.current = true
        setAutoReplied(true)
        sendToAgentInbox(projectName, "Keep going, you're doing great!").catch(() => {})
      }
    }

    tick()
    const interval = setInterval(tick, 1000)
    return () => clearInterval(interval)
  }, [isWaitingForReply, agentPhase?.timestamp, waitTimeout, autoReplyEnabled, projectName])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (isExpanded && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [agentMessages, sentMessages, isExpanded])

  // Auto-expand when first agent message arrives or when agent is waiting for reply
  useEffect(() => {
    if ((agentMessages.length > 0 || isWaitingForReply) && !isExpanded) {
      setIsExpanded(true)
    }
    if (isWaitingForReply && inputRef.current) {
      inputRef.current.focus()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agentMessages.length, isWaitingForReply])

  const handleSend = async () => {
    if ((!inputText.trim() && pendingAttachments.length === 0) || !projectName || sending) return

    setSending(true)
    try {
      // Convert attachments to base64
      const attachments = await Promise.all(
        pendingAttachments.map(async (pa) => ({
          filename: pa.file.name,
          mime_type: pa.file.type || 'application/octet-stream',
          base64_data: await fileToBase64(pa.file),
        }))
      )

      const text = inputText.trim() || (attachments.length > 0 ? `[Sent ${attachments.length} file(s)]` : '')
      const result = await sendToAgentInbox(projectName, text, attachments.length > 0 ? attachments : undefined)
      if (result.sent) {
        setSentMessages(prev => [...prev, {
          id: result.id,
          text,
          timestamp: new Date().toISOString(),
        }])
        setInputText('')
        setPendingAttachments([])
        inputRef.current?.focus()
      }
    } catch (err) {
      console.error('Failed to send message to agent:', err)
    } finally {
      setSending(false)
    }
  }

  const handleKeepGoing = useCallback(async () => {
    if (!projectName || sending) return
    setSending(true)
    try {
      const result = await sendToAgentInbox(projectName, 'Keep going!')
      if (result.sent) {
        setSentMessages(prev => [...prev, {
          id: result.id,
          text: 'Keep going!',
          timestamp: new Date().toISOString(),
        }])
      }
    } catch (err) {
      console.error('Failed to send keep going:', err)
    } finally {
      setSending(false)
    }
  }, [projectName, sending])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleFileSelect = (files: FileList | null) => {
    if (!files) return
    const newAttachments: PendingAttachment[] = []
    for (const file of Array.from(files)) {
      const ext = '.' + file.name.split('.').pop()?.toLowerCase()
      if (!ALLOWED_EXTENSIONS.includes(ext)) continue
      if (file.size > MAX_ATTACHMENT_SIZE) continue
      if (pendingAttachments.length + newAttachments.length >= 5) break

      const pa: PendingAttachment = { file }
      if (file.type.startsWith('image/')) {
        pa.preview = URL.createObjectURL(file)
      }
      newAttachments.push(pa)
    }
    setPendingAttachments(prev => [...prev, ...newAttachments])
  }

  const handlePaste = (e: React.ClipboardEvent) => {
    const files = e.clipboardData?.files
    if (files && files.length > 0) {
      e.preventDefault()
      handleFileSelect(files)
    }
  }

  const removeAttachment = (index: number) => {
    setPendingAttachments(prev => {
      const removed = prev[index]
      if (removed.preview) URL.revokeObjectURL(removed.preview)
      return prev.filter((_, i) => i !== index)
    })
  }

  const unreadCount = agentMessages.length

  if (!projectName) return null

  const allMessages = [
    ...agentMessages.map(m => ({ ...m, source: 'agent' as const })),
    ...sentMessages.map(m => ({ ...m, category: 'user', source: 'user' as const })),
  ].sort((a, b) => a.timestamp.localeCompare(b.timestamp))

  const formatCountdown = (secs: number) => {
    const m = Math.floor(secs / 60)
    const s = secs % 60
    return m > 0 ? `${m}:${s.toString().padStart(2, '0')}` : `${s}s`
  }

  // Roadmap progress
  const roadmapDone = roadmap.filter(s => s.done).length
  const roadmapTotal = roadmap.length

  // Filter out [ROADMAP], [PROGRESS], [FINISHING] from chat display (they show in roadmap widget)
  const chatMessages = allMessages.filter(m =>
    m.source === 'user' ||
    (!m.text.startsWith('[ROADMAP]') && !m.text.startsWith('[PROGRESS]') && !m.text.startsWith('[FINISHING]'))
  )

  return (
    <div className="border-2 border-black rounded-lg bg-white shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-3 py-2 bg-gradient-to-r from-indigo-50 to-purple-50 hover:from-indigo-100 hover:to-purple-100 transition-colors"
      >
        <div className="flex items-center gap-2">
          <MessageCircle className="w-4 h-4 text-indigo-600" />
          <span className="text-sm font-bold text-gray-800">Agent Walkie-Talkie</span>
          {unreadCount > 0 && (
            <span className="inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-indigo-600 rounded-full">
              {unreadCount}
            </span>
          )}
          {agentPhase && isAgentRunning && (
            <span className={`text-xs font-medium ${PHASE_DISPLAY[agentPhase.phase]?.color || 'text-gray-600'}`}>
              {PHASE_DISPLAY[agentPhase.phase]?.icon} {PHASE_DISPLAY[agentPhase.phase]?.label || agentPhase.phase}
              {agentPhase.phase !== 'waiting' && agentPhase.detail && `: ${agentPhase.detail}`}
            </span>
          )}
          {/* Countdown badge */}
          {isWaitingForReply && countdown !== null && countdown > 0 && (
            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 text-[10px] font-mono font-bold text-purple-700 bg-purple-100 border border-purple-300 rounded-full">
              {formatCountdown(countdown)}
            </span>
          )}
          {/* Finishing soon badge */}
          {isFinishing && !isWaitingForReply && (
            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 text-[10px] font-bold text-amber-700 bg-amber-100 border border-amber-300 rounded-full animate-pulse">
              <AlertTriangle className="w-3 h-3" />
              Finishing soon
            </span>
          )}
          {/* Roadmap progress badge */}
          {roadmapTotal > 0 && (
            <span className="text-[10px] font-mono text-gray-500">
              {roadmapDone}/{roadmapTotal}
            </span>
          )}
        </div>
        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </button>

      {/* Expanded panel */}
      {isExpanded && (
        <div className="border-t-2 border-black">
          {/* Roadmap tracker */}
          {roadmapTotal > 0 && (
            <div className="px-2 py-1.5 bg-slate-50 border-b border-gray-200">
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] font-bold text-slate-600 uppercase tracking-wide">Roadmap</span>
                <span className="text-[10px] font-mono text-slate-500">{roadmapDone}/{roadmapTotal}</span>
              </div>
              {/* Progress bar */}
              <div className="w-full h-1.5 bg-slate-200 rounded-full overflow-hidden mb-1.5">
                <div
                  className="h-full bg-indigo-500 rounded-full transition-all duration-500 ease-out"
                  style={{ width: `${roadmapTotal > 0 ? (roadmapDone / roadmapTotal) * 100 : 0}%` }}
                />
              </div>
              {/* Steps */}
              <div className="space-y-0.5">
                {roadmap.map((step) => (
                  <div key={step.index} className="flex items-center gap-1.5">
                    <span className={`text-[10px] ${step.done ? 'text-green-600' : 'text-gray-400'}`}>
                      {step.done ? '\u{2705}' : '\u{2B1C}'}
                    </span>
                    <span className={`text-[10px] ${step.done ? 'text-gray-500 line-through' : 'text-gray-700'}`}>
                      {step.label}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Finishing soon banner */}
          {isFinishing && (
            <div className="px-2 py-1.5 bg-amber-50 border-b border-amber-200 flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
              <span className="text-xs font-medium text-amber-700">
                Agent is on final steps — send any last questions now!
              </span>
            </div>
          )}

          {/* Messages area */}
          <div className="max-h-48 overflow-y-auto p-2 space-y-1.5 bg-gray-50">
            {chatMessages.length === 0 ? (
              <p className="text-xs text-gray-400 text-center py-4">
                {isAgentRunning
                  ? 'Waiting for agent messages...'
                  : 'Start the agent to begin communication'}
              </p>
            ) : (
              chatMessages.map((msg) => {
                if (msg.source === 'user') {
                  return (
                    <div key={msg.id} className="flex justify-end">
                      <div className="max-w-[80%] rounded-lg px-2.5 py-1.5 bg-indigo-100 border border-indigo-300">
                        <p className="text-xs text-gray-800">{msg.text}</p>
                        <p className="text-[10px] text-gray-500 mt-0.5">You</p>
                      </div>
                    </div>
                  )
                }
                const style = CATEGORY_STYLES[msg.category] || CATEGORY_STYLES.status
                return (
                  <div key={msg.id} className="flex justify-start">
                    <div className={`max-w-[80%] rounded-lg px-2.5 py-1.5 ${style.bg} border ${style.border}`}>
                      <p className="text-xs text-gray-800">
                        <span className="mr-1">{style.icon}</span>
                        {msg.text}
                      </p>
                      <p className="text-[10px] text-gray-500 mt-0.5">Agent</p>
                    </div>
                  </div>
                )
              })
            )}
            {autoReplied && (
              <div className="flex justify-center">
                <span className="text-[10px] text-gray-400 italic">Auto-replied: "Keep going!"</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Waiting bar with countdown + Keep Going */}
          {isWaitingForReply && countdown !== null && countdown > 0 && (
            <div className="border-t border-purple-200 bg-purple-50 px-2 py-1.5 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xs text-purple-700 font-medium">
                  Waiting for your reply
                </span>
                <span className="font-mono text-xs font-bold text-purple-800 bg-purple-100 px-1.5 py-0.5 rounded">
                  {formatCountdown(countdown)}
                </span>
                <div className="w-20 h-1.5 bg-purple-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-purple-500 rounded-full transition-all duration-1000 ease-linear"
                    style={{ width: `${(countdown / waitTimeout) * 100}%` }}
                  />
                </div>
              </div>
              <button
                onClick={handleKeepGoing}
                disabled={sending}
                className="flex items-center gap-1 px-2 py-1 text-[11px] font-bold text-purple-700 bg-purple-100 border border-purple-300 rounded-md hover:bg-purple-200 transition-colors disabled:opacity-50"
              >
                <Play className="w-3 h-3" />
                Keep Going
              </button>
            </div>
          )}

          {/* Pending attachments preview */}
          {pendingAttachments.length > 0 && (
            <div className="border-t border-gray-200 px-2 py-1.5 flex gap-1.5 flex-wrap bg-white">
              {pendingAttachments.map((pa, i) => (
                <div key={i} className="relative group">
                  {pa.preview ? (
                    <img src={pa.preview} alt={pa.file.name} className="w-10 h-10 object-cover rounded border border-gray-300" />
                  ) : (
                    <div className="w-10 h-10 flex items-center justify-center bg-gray-100 rounded border border-gray-300">
                      <span className="text-[8px] text-gray-500 text-center leading-tight">{pa.file.name.split('.').pop()}</span>
                    </div>
                  )}
                  <button
                    onClick={() => removeAttachment(i)}
                    className="absolute -top-1 -right-1 w-3.5 h-3.5 bg-red-500 text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <X className="w-2 h-2" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Input area */}
          <div className="border-t border-gray-200 p-2 flex gap-1.5">
            <input
              type="file"
              ref={fileInputRef}
              className="hidden"
              multiple
              accept={ALLOWED_EXTENSIONS.join(',')}
              onChange={(e) => handleFileSelect(e.target.files)}
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={!isAgentRunning || pendingAttachments.length >= 5}
              className="px-1.5 py-1.5 text-gray-500 hover:text-indigo-600 disabled:text-gray-300 transition-colors"
              title="Attach file"
            >
              <Paperclip className="w-3.5 h-3.5" />
            </button>
            <input
              ref={inputRef}
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              onPaste={handlePaste}
              placeholder={isWaitingForReply ? "Agent is waiting for your reply..." : isAgentRunning ? "Message the agent..." : "Agent not running"}
              disabled={!isAgentRunning || sending}
              className={`flex-1 text-xs px-2.5 py-1.5 border-2 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-400 disabled:bg-gray-100 disabled:text-gray-400 disabled:border-gray-300 ${isWaitingForReply ? 'border-purple-500 bg-purple-50 animate-pulse' : 'border-black'}`}
            />
            <button
              onClick={handleSend}
              disabled={(!inputText.trim() && pendingAttachments.length === 0) || !isAgentRunning || sending}
              className="px-2.5 py-1.5 bg-indigo-600 text-white rounded-md border-2 border-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:shadow-none hover:translate-x-[2px] hover:translate-y-[2px] transition-all disabled:opacity-50 disabled:shadow-none disabled:translate-x-0 disabled:translate-y-0"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
