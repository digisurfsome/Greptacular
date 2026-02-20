/**
 * Agent Notifications Panel
 *
 * Displays agent messages (status, questions, discoveries, warnings, milestones)
 * and allows the user to send messages back to the agent via the inbox API.
 * Also shows the current agent phase when the agent is running.
 */

import { useState, useRef, useEffect } from 'react'
import { Send, MessageCircle, ChevronDown, ChevronUp } from 'lucide-react'
import { sendToAgentInbox } from '../lib/api'

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

interface AgentNotificationsProps {
  projectName: string | null
  agentMessages: Array<{ id: string; text: string; category: string; timestamp: string }>
  agentPhase: { phase: string; detail: string; timestamp: string } | null
  agentStatus: string
}

export function AgentNotifications({ projectName, agentMessages, agentPhase, agentStatus }: AgentNotificationsProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [inputText, setInputText] = useState('')
  const [sending, setSending] = useState(false)
  const [sentMessages, setSentMessages] = useState<Array<{ id: string; text: string; timestamp: string }>>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const isAgentRunning = agentStatus === 'running' || agentStatus === 'paused'
  const isWaitingForReply = agentPhase?.phase === 'waiting'

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
    // Auto-focus input when agent starts waiting
    if (isWaitingForReply && inputRef.current) {
      inputRef.current.focus()
    }
  // Only trigger on message count changes or waiting state, not on isExpanded changes
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agentMessages.length, isWaitingForReply])

  const handleSend = async () => {
    if (!inputText.trim() || !projectName || sending) return

    setSending(true)
    try {
      const result = await sendToAgentInbox(projectName, inputText.trim())
      if (result.sent) {
        setSentMessages(prev => [...prev, {
          id: result.id,
          text: inputText.trim(),
          timestamp: new Date().toISOString(),
        }])
        setInputText('')
        inputRef.current?.focus()
      }
    } catch (err) {
      console.error('Failed to send message to agent:', err)
    } finally {
      setSending(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }
  const unreadCount = agentMessages.length

  // Don't render if no project selected
  if (!projectName) return null

  // Merge and sort all messages by timestamp for chronological display
  const allMessages = [
    ...agentMessages.map(m => ({ ...m, source: 'agent' as const })),
    ...sentMessages.map(m => ({ ...m, category: 'user', source: 'user' as const })),
  ].sort((a, b) => a.timestamp.localeCompare(b.timestamp))

  return (
    <div className="border-2 border-black rounded-lg bg-white shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] overflow-hidden">
      {/* Header - always visible */}
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
              {agentPhase.detail && `: ${agentPhase.detail}`}
            </span>
          )}
        </div>
        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </button>

      {/* Expanded panel */}
      {isExpanded && (
        <div className="border-t-2 border-black">
          {/* Messages area */}
          <div className="max-h-48 overflow-y-auto p-2 space-y-1.5 bg-gray-50">
            {allMessages.length === 0 ? (
              <p className="text-xs text-gray-400 text-center py-4">
                {isAgentRunning
                  ? 'Waiting for agent messages...'
                  : 'Start the agent to begin communication'}
              </p>
            ) : (
              allMessages.map((msg) => {
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
            <div ref={messagesEndRef} />
          </div>

          {/* Input area */}
          <div className="border-t border-gray-200 p-2 flex gap-1.5">
            <input
              ref={inputRef}
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={isWaitingForReply ? "Agent is waiting for your reply..." : isAgentRunning ? "Message the agent..." : "Agent not running"}
              disabled={!isAgentRunning || sending}
              className={`flex-1 text-xs px-2.5 py-1.5 border-2 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-400 disabled:bg-gray-100 disabled:text-gray-400 disabled:border-gray-300 ${isWaitingForReply ? 'border-purple-500 bg-purple-50 animate-pulse' : 'border-black'}`}
            />
            <button
              onClick={handleSend}
              disabled={!inputText.trim() || !isAgentRunning || sending}
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
