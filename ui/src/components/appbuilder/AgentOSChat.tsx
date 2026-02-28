/**
 * AgentOSChat Component
 *
 * Interactive chat interface for the Agent OS PRD creation workflow.
 * Shows the conversation, current stage indicator, questions, and
 * provides input for user responses.
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import {
  Send,
  X,
  CheckCircle2,
  Wifi,
  WifiOff,
  SkipForward,
  Loader2,
  Zap,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ChatMessage } from '@/components/ChatMessage'
import { TypingIndicator } from '@/components/TypingIndicator'
import {
  useAgentOSChat,
  type AgentOSChatFeature,
  type AgentOSChatGap,
} from '@/hooks/useAgentOSChat'
import { isSubmitEnter } from '@/lib/keyboard'

// ============================================================================
// Stage definitions
// ============================================================================

const STAGES = [
  { key: 'intake', label: 'Intake' },
  { key: 'standards', label: 'Standards' },
  { key: 'product_discovery', label: 'Product' },
  { key: 'feature_extraction', label: 'Features' },
  { key: 'gap_analysis', label: 'Gaps' },
  { key: 'spec_generation', label: 'Specs' },
  { key: 'database_population', label: 'Database' },
  { key: 'handoff', label: 'Handoff' },
]

// ============================================================================
// Component
// ============================================================================

interface AgentOSChatProps {
  projectName: string
  onComplete: () => void
  onCancel: () => void
}

export function AgentOSChat({ projectName, onComplete, onCancel }: AgentOSChatProps) {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const {
    messages,
    currentStage,
    stageIndex,
    currentQuestion,
    features,
    gaps,
    specPreview,
    handoffStatus,
    isConnected,
    isThinking,
    connectionStatus,
    sendMessage,
    sendAnswer,
    sendApprove,
    skipStage,
    fastTrack,
    connect,
    disconnect,
  } = useAgentOSChat({
    projectName,
    onComplete,
    onError: (err) => console.error('Agent OS chat error:', err),
  })

  // Connect on mount
  useEffect(() => {
    connect()
    return () => disconnect()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-scroll on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, currentQuestion, isThinking, features, gaps])

  // Focus input when not thinking
  useEffect(() => {
    if (!isThinking && !currentQuestion && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isThinking, currentQuestion])

  const handleSend = useCallback(() => {
    const trimmed = input.trim()
    if (!trimmed || isThinking) return
    sendMessage(trimmed)
    setInput('')
    if (inputRef.current) inputRef.current.style.height = 'auto'
  }, [input, isThinking, sendMessage])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (isSubmitEnter(e)) {
      e.preventDefault()
      handleSend()
    }
  }, [handleSend])

  const handleQuestionAnswer = useCallback((answer: string) => {
    if (!currentQuestion) return
    sendAnswer(currentQuestion.id, answer)
  }, [currentQuestion, sendAnswer])

  // Adapt messages for ChatMessage component (needs Date, not string)
  const chatMessages = messages.map(m => ({
    id: m.id,
    role: m.role,
    content: m.content,
    timestamp: m.timestamp instanceof Date ? m.timestamp : new Date(m.timestamp),
    isStreaming: m.isStreaming,
  }))

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header with stage progress */}
      <div className="shrink-0 border-b border-border bg-card px-4 py-3">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-bold text-foreground">Agent OS PRD Creation</h2>
            <ConnectionIndicator status={connectionStatus} />
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant="outline"
              size="sm"
              onClick={fastTrack}
              disabled={!isConnected || isThinking}
              className="gap-1 text-xs text-amber-600 border-amber-500/40 hover:bg-amber-500/10 hover:text-amber-500"
              title="Skip all stages — I already have a complete spec"
            >
              <Zap size={14} />
              Fast Track
            </Button>
            <Button variant="ghost" size="sm" onClick={onCancel}>
              <X size={16} />
            </Button>
          </div>
        </div>

        {/* Stage progress bar */}
        <div className="flex items-center gap-1">
          {STAGES.map((stage, idx) => {
            const isComplete = idx < stageIndex
            const isCurrent = stage.key === currentStage || idx === stageIndex
            return (
              <div key={stage.key} className="flex items-center gap-1 flex-1">
                <div
                  className={`h-1.5 flex-1 rounded-full transition-colors ${
                    isComplete
                      ? 'bg-green-500'
                      : isCurrent
                        ? 'bg-primary'
                        : 'bg-muted'
                  }`}
                />
                {idx < STAGES.length - 1 && <div className="w-0.5" />}
              </div>
            )
          })}
        </div>
        <div className="flex justify-between mt-1">
          {STAGES.map((stage, idx) => {
            const isCurrent = stage.key === currentStage || idx === stageIndex
            return (
              <span
                key={stage.key}
                className={`text-[9px] ${isCurrent ? 'text-primary font-bold' : 'text-muted-foreground'}`}
              >
                {stage.label}
              </span>
            )
          })}
        </div>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto min-h-0 py-2">
        {chatMessages.length === 0 && !isThinking && (
          <div className="flex items-center justify-center h-full text-center p-8">
            <div className="text-sm text-muted-foreground">
              {isConnected ? 'Starting Agent OS workflow...' : 'Connecting...'}
            </div>
          </div>
        )}

        {chatMessages.map(message => (
          <ChatMessage key={message.id} message={message} />
        ))}

        {/* Question options (choice-based) */}
        {currentQuestion && currentQuestion.type !== 'text' && currentQuestion.options && (
          <div className="px-4 py-3">
            <Card className="p-4">
              <p className="text-sm font-medium text-foreground mb-3">{currentQuestion.question}</p>
              <div className="flex flex-wrap gap-2">
                {currentQuestion.options.map(option => (
                  <Button
                    key={option}
                    variant="outline"
                    size="sm"
                    onClick={() => handleQuestionAnswer(option)}
                  >
                    {option}
                  </Button>
                ))}
              </div>
            </Card>
          </div>
        )}

        {/* Feature list review */}
        {features.length > 0 && (
          <FeatureReview features={features} onApprove={() => sendApprove('feature_list')} />
        )}

        {/* Gap display */}
        {gaps.length > 0 && (
          <GapSummary gaps={gaps} />
        )}

        {/* Spec preview */}
        {specPreview && (
          <div className="px-4 py-2">
            <Card className="p-4 bg-muted/30">
              <p className="text-xs font-bold text-muted-foreground mb-2">
                Spec Preview — Feature #{specPreview.featureId}
              </p>
              <pre className="text-xs text-foreground whitespace-pre-wrap font-mono">
                {specPreview.content.slice(0, 500)}
                {specPreview.content.length > 500 && '...'}
              </pre>
            </Card>
          </div>
        )}

        {/* Handoff ready */}
        {handoffStatus?.ready && (
          <div className="px-4 py-2">
            <Card className="p-4 border-green-300 bg-green-50 dark:bg-green-900/10">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle2 size={16} className="text-green-500" />
                <span className="text-sm font-bold text-foreground">Handoff Ready</span>
              </div>
              <p className="text-xs text-muted-foreground">
                {handoffStatus.feature_count} features · {handoffStatus.estimated_sessions} estimated sessions
              </p>
              <Button size="sm" className="mt-3" onClick={onComplete}>
                Start Build
              </Button>
            </Card>
          </div>
        )}

        {isThinking && <TypingIndicator />}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="shrink-0 p-3 border-t border-border bg-card">
        <div className="flex gap-2">
          <Textarea
            ref={inputRef}
            value={input}
            onChange={e => {
              setInput(e.target.value)
              e.target.style.height = 'auto'
              e.target.style.height = `${Math.min(e.target.scrollHeight, 150)}px`
            }}
            onKeyDown={handleKeyDown}
            placeholder={currentQuestion ? 'Type your answer...' : 'Type your message...'}
            className="flex-1 resize-none min-h-[40px] max-h-[150px] overflow-y-auto text-sm"
            disabled={isThinking || !isConnected}
            rows={1}
          />
          <Button onClick={handleSend} disabled={!input.trim() || isThinking || !isConnected} size="sm">
            <Send size={16} />
          </Button>
        </div>
        <div className="flex items-center justify-between mt-2">
          <span className="text-[10px] text-muted-foreground">
            Enter to send, Shift+Enter for new line
          </span>
          <Button variant="ghost" size="sm" className="text-xs h-6" onClick={skipStage}>
            <SkipForward size={12} />
            Skip Stage
          </Button>
        </div>
      </div>
    </div>
  )
}

// ============================================================================
// Sub-components
// ============================================================================

function ConnectionIndicator({ status }: { status: string }) {
  switch (status) {
    case 'connected':
      return <span className="flex items-center gap-1 text-[10px] text-green-500"><Wifi size={10} />Connected</span>
    case 'connecting':
      return <span className="flex items-center gap-1 text-[10px] text-amber-500"><Loader2 size={10} className="animate-spin" />Connecting</span>
    case 'error':
      return <span className="flex items-center gap-1 text-[10px] text-destructive"><WifiOff size={10} />Error</span>
    default:
      return <span className="flex items-center gap-1 text-[10px] text-muted-foreground"><WifiOff size={10} />Disconnected</span>
  }
}

function FeatureReview({ features, onApprove }: { features: AgentOSChatFeature[]; onApprove: () => void }) {
  return (
    <div className="px-4 py-2">
      <Card className="p-4">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-bold text-foreground uppercase tracking-wider">
            Features ({features.length})
          </span>
          <Button size="sm" variant="outline" onClick={onApprove}>
            <CheckCircle2 size={14} />
            Approve List
          </Button>
        </div>
        <div className="space-y-1.5">
          {features.map(f => (
            <div key={f.id} className="flex items-center gap-2 text-xs">
              <span className="font-mono text-muted-foreground">#{f.id}</span>
              <span className="font-medium text-foreground">{f.name}</span>
              <Badge variant="outline" className="text-[9px]">{f.priority}</Badge>
              <Badge variant="outline" className="text-[9px]">{f.complexity}</Badge>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}

function GapSummary({ gaps }: { gaps: AgentOSChatGap[] }) {
  const blocking = gaps.filter(g => g.severity === 'blocking' && !g.resolved)
  const resolved = gaps.filter(g => g.resolved)
  const other = gaps.filter(g => g.severity !== 'blocking' && !g.resolved)

  return (
    <div className="px-4 py-2">
      <Card className="p-4">
        <span className="text-xs font-bold text-foreground uppercase tracking-wider">
          Gap Analysis ({gaps.length})
        </span>
        {blocking.length > 0 && (
          <div className="mt-2">
            <span className="text-[10px] font-bold text-red-500">BLOCKING ({blocking.length})</span>
            {blocking.map(g => (
              <div key={g.id} className="text-xs text-muted-foreground mt-1 pl-2 border-l-2 border-red-300">
                {g.message}
              </div>
            ))}
          </div>
        )}
        {other.length > 0 && (
          <div className="mt-2">
            <span className="text-[10px] font-bold text-amber-500">OPEN ({other.length})</span>
          </div>
        )}
        {resolved.length > 0 && (
          <div className="mt-2">
            <span className="text-[10px] font-bold text-green-500">RESOLVED ({resolved.length})</span>
          </div>
        )}
      </Card>
    </div>
  )
}
