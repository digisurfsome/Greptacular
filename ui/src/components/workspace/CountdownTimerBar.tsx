/**
 * CountdownTimerBar
 *
 * A thin floating bar shown at the top of the WorkspacePage when the agent
 * is waiting for user input. Displays a depleting progress bar, time
 * remaining, and a "Keep Going" action button.
 *
 * Supports auto-reply mode: when enabled, an "(auto-reply)" badge appears
 * and the `onTimeout` callback fires when the countdown reaches zero.
 * In manual mode the bar simply shows "Time's up" when expired.
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import { Clock } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface CountdownTimerBarProps {
  /** Whether the timer is active. */
  active: boolean
  /** Total seconds for the countdown (from settings comm_wait_timeout). */
  totalSeconds: number
  /** Whether auto-reply is enabled. */
  autoReply: boolean
  /** Called when the user clicks "Keep Going". */
  onKeepGoing: () => void
  /** Called when the countdown reaches zero (for auto-reply). */
  onTimeout: () => void
}

/** Format remaining seconds as "M:SS". */
function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

export function CountdownTimerBar({
  active,
  totalSeconds,
  autoReply,
  onKeepGoing,
  onTimeout,
}: CountdownTimerBarProps): React.JSX.Element | null {
  const [remaining, setRemaining] = useState(totalSeconds)
  const timeoutFiredRef = useRef(false)

  // Stabilise callback refs to avoid re-triggering the interval effect
  const onTimeoutRef = useRef(onTimeout)
  onTimeoutRef.current = onTimeout

  // Reset the countdown whenever `active` toggles on or totalSeconds changes
  useEffect(() => {
    if (active) {
      setRemaining(totalSeconds)
      timeoutFiredRef.current = false
    }
  }, [active, totalSeconds])

  // Tick every second while active and time remains
  useEffect(() => {
    if (!active) return

    const interval = setInterval(() => {
      setRemaining((prev) => {
        if (prev <= 1) {
          clearInterval(interval)
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(interval)
  }, [active])

  // Fire onTimeout exactly once when the countdown hits zero in auto-reply mode
  const handleTimeout = useCallback(() => {
    if (!timeoutFiredRef.current) {
      timeoutFiredRef.current = true
      onTimeoutRef.current()
    }
  }, [])

  useEffect(() => {
    if (remaining === 0 && autoReply && active) {
      handleTimeout()
    }
  }, [remaining, autoReply, active, handleTimeout])

  if (!active) return null

  const expired = remaining === 0
  const pct = totalSeconds > 0 ? (remaining / totalSeconds) * 100 : 0

  return (
    <div className="w-full h-9 bg-amber-500/10 border-b border-amber-500/20 flex items-center px-4 gap-3 relative animate-slide-in-down">
      {/* Left: icon + status text + time */}
      <div className="flex items-center gap-2 text-sm text-amber-700 dark:text-amber-400 whitespace-nowrap">
        <Clock size={14} className="flex-shrink-0" />
        <span className="font-medium">
          {expired ? "Time's up" : 'Agent waiting for response...'}
        </span>
        {!expired && (
          <span className="font-mono text-xs">{formatTime(remaining)}</span>
        )}
        {autoReply && (
          <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-600 dark:text-amber-400">
            auto-reply
          </span>
        )}
      </div>

      {/* Right: action button */}
      <div className="ml-auto flex-shrink-0">
        <Button size="xs" onClick={onKeepGoing}>
          Keep Going
        </Button>
      </div>

      {/* Bottom: depleting progress bar */}
      <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-amber-500/10">
        <div
          className="h-full bg-amber-500 transition-all duration-1000 ease-linear"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}
