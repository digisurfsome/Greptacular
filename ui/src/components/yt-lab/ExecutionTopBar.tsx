/**
 * ExecutionTopBar — Top bar (48px) for the execution viewer.
 *
 * Left: Project name, current step, "Step X of Y"
 * Center: Chat input ("Talk to the agent...")
 * Right: Model indicator, state-dependent buttons (Pause/Resume/Take Over/Stop)
 */

import { useState, useCallback } from 'react'
import {
  ChevronRight,
  Pause,
  Play,
  Square,
  Hand,
  RotateCcw,
  Send,
  ArrowLeft,
  Loader2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import type { YTExecutionStatus } from '@/lib/types'

interface ExecutionTopBarProps {
  projectName: string
  currentStepTitle: string
  currentStep: number
  totalSteps: number
  status: YTExecutionStatus
  model: string
  onPause: () => void
  onResume: () => void
  onStop: () => void
  onTakeover: () => void
  onReturnControl: () => void
  onSendMessage: (message: string) => void
  onBack: () => void
  isPending?: boolean
  confirmingStop?: boolean
}

const STATUS_CONFIG: Record<YTExecutionStatus, { label: string; className: string }> = {
  idle: { label: 'Idle', className: 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30' },
  running: { label: 'Running', className: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30' },
  paused: { label: 'Paused', className: 'bg-amber-500/20 text-amber-400 border-amber-500/30' },
  takeover: { label: 'Takeover', className: 'bg-amber-500/20 text-amber-300 border-amber-500/30' },
  completed: { label: 'Complete', className: 'bg-green-500/20 text-green-400 border-green-500/30' },
  error: { label: 'Error', className: 'bg-red-500/20 text-red-400 border-red-500/30' },
}

const MODEL_LABELS: Record<string, string> = {
  'claude-opus-4-6': 'Opus',
  'claude-sonnet-4-6': 'Sonnet',
  'claude-haiku-4-5': 'Haiku',
}

export function ExecutionTopBar({
  projectName,
  currentStepTitle,
  currentStep,
  totalSteps,
  status,
  model,
  onPause,
  onResume,
  onStop,
  onTakeover,
  onReturnControl,
  onSendMessage,
  onBack,
  isPending = false,
  confirmingStop = false,
}: ExecutionTopBarProps) {
  const [chatMessage, setChatMessage] = useState('')

  const handleSend = useCallback(() => {
    const msg = chatMessage.trim()
    if (!msg) return
    onSendMessage(msg)
    setChatMessage('')
  }, [chatMessage, onSendMessage])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        handleSend()
      }
    },
    [handleSend],
  )

  const statusConfig = STATUS_CONFIG[status]
  const modelLabel = MODEL_LABELS[model] ?? model

  const canChat = status === 'running' || status === 'paused'
  const isTerminal = status === 'completed' || status === 'error' || status === 'idle'

  return (
    <div className="flex items-center h-12 px-3 border-b border-border bg-card shrink-0 gap-3">
      {/* Left: Back + Project info */}
      <div className="flex items-center gap-2 shrink-0">
        <Button
          variant="ghost"
          size="sm"
          className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground"
          onClick={onBack}
          aria-label="Back to project"
        >
          <ArrowLeft size={14} />
        </Button>

        <span className="text-sm font-semibold text-foreground truncate max-w-[140px]">
          {projectName}
        </span>
        <ChevronRight size={12} className="text-muted-foreground shrink-0" />
        <span className="text-xs text-muted-foreground truncate max-w-[120px]">
          {currentStepTitle || `Step ${currentStep}`}
        </span>
        <span className="text-[10px] text-muted-foreground/60 shrink-0">
          {currentStep}/{totalSteps}
        </span>

        <Badge variant="outline" className={`text-[10px] h-5 px-1.5 ${statusConfig.className}`}>
          {status === 'running' && <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse mr-1" />}
          {statusConfig.label}
        </Badge>
      </div>

      {/* Center: Chat input */}
      <div className="flex-1 flex items-center gap-1.5 min-w-0 mx-2">
        <Input
          placeholder={canChat ? 'Talk to the agent...' : 'Agent not active'}
          value={chatMessage}
          onChange={(e) => setChatMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={!canChat}
          className="h-7 text-xs bg-background border-border"
        />
        <Button
          variant="ghost"
          size="sm"
          className="h-7 w-7 p-0 shrink-0 text-muted-foreground hover:text-primary"
          onClick={handleSend}
          disabled={!canChat || !chatMessage.trim()}
          aria-label="Send message"
        >
          <Send size={12} />
        </Button>
      </div>

      {/* Right: Model + Controls */}
      <div className="flex items-center gap-1.5 shrink-0">
        <Badge variant="outline" className="text-[10px] h-5 px-1.5 text-muted-foreground">
          {modelLabel}
        </Badge>

        {status === 'running' && (
          <Button
            variant="outline"
            size="sm"
            className="h-7 gap-1 text-xs"
            onClick={onPause}
            disabled={isPending}
          >
            {isPending ? <Loader2 size={12} className="animate-spin" /> : <Pause size={12} />}
            Pause
          </Button>
        )}

        {status === 'paused' && (
          <>
            <Button
              size="sm"
              className="h-7 gap-1 text-xs"
              onClick={onResume}
              disabled={isPending}
            >
              {isPending ? <Loader2 size={12} className="animate-spin" /> : <Play size={12} />}
              Resume
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="h-7 gap-1 text-xs"
              onClick={onTakeover}
              disabled={isPending}
            >
              <Hand size={12} />
              Take Over
            </Button>
          </>
        )}

        {status === 'takeover' && (
          <Button
            size="sm"
            className="h-7 gap-1 text-xs bg-amber-500 hover:bg-amber-600 text-black"
            onClick={onReturnControl}
            disabled={isPending}
          >
            {isPending ? <Loader2 size={12} className="animate-spin" /> : <RotateCcw size={12} />}
            Return Control
          </Button>
        )}

        {!isTerminal && (
          <Button
            variant="destructive"
            size="sm"
            className={`h-7 gap-1 text-xs ${confirmingStop ? 'animate-pulse' : ''}`}
            onClick={onStop}
            disabled={isPending}
          >
            <Square size={10} />
            {confirmingStop ? 'Confirm?' : 'Stop'}
          </Button>
        )}
      </div>
    </div>
  )
}
