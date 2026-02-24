/**
 * GitActivityWidget - Compact "G" notification button with CI-aware blink colors.
 *
 * Shows a bold "G" letter that blinks with different colors based on CI status:
 *   - Yellow blink: new (unseen) commits detected
 *   - Green blink: successful merge happened
 *   - Red blink: CI error or failure
 *   - No blink: idle / running (nothing noteworthy)
 *
 * Click to expand a dropdown of the last 10 commits with timestamps.
 * Includes a "Processing Log" button that opens the slide-out panel.
 * Badge count and blink reset when the dropdown is opened.
 *
 * Placed on: AutoForge front page header + Workspace breadcrumb bar.
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getGitCommits, getCIStatus } from '../lib/api'
import type { GitCommit, CIPipelineStatus } from '../lib/types'
import { FileText } from 'lucide-react'

interface GitActivityWidgetProps {
  workingDirectory: string | null
  onOpenProcessingLog?: () => void
}

function timeAgo(isoDate: string): string {
  const now = Date.now()
  const then = new Date(isoDate).getTime()
  const diff = Math.max(0, now - then)
  const seconds = Math.floor(diff / 1000)
  if (seconds < 60) return `${seconds}s ago`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

/** Statuses that indicate a failure or error condition. */
const ERROR_STATUSES: ReadonlySet<CIPipelineStatus> = new Set([
  'failed',
  'exhausted',
  'error',
])

/**
 * Determine the notification blink color based on unseen commits and CI status.
 *
 * Priority order:
 *   1. Red   - CI failure / error / exhausted
 *   2. Green - successful merge
 *   3. Yellow - new unseen commits
 *   4. null  - no notification (idle / running)
 */
function resolveBlinkColor(
  unseenCount: number,
  ciStatus: CIPipelineStatus | null,
): 'yellow' | 'green' | 'red' | null {
  if (ciStatus && ERROR_STATUSES.has(ciStatus)) return 'red'
  if (ciStatus === 'merged') return 'green'
  if (unseenCount > 0) return 'yellow'
  return null
}

/** Map blink color to Tailwind border + text classes for the G icon. */
const BLINK_STYLES: Record<string, { border: string; text: string; badge: string }> = {
  yellow: {
    border: 'border-yellow-400/80',
    text: 'text-yellow-400',
    badge: 'bg-yellow-500',
  },
  green: {
    border: 'border-emerald-400/80',
    text: 'text-emerald-400',
    badge: 'bg-emerald-500',
  },
  red: {
    border: 'border-red-400/80',
    text: 'text-red-400',
    badge: 'bg-red-500',
  },
}

export function GitActivityWidget({ workingDirectory, onOpenProcessingLog }: GitActivityWidgetProps) {
  const [expanded, setExpanded] = useState(false)
  const [seenCount, setSeenCount] = useState(0)
  const [hasNewSinceClick, setHasNewSinceClick] = useState(false)
  const prevCommitsRef = useRef<string[]>([])
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Fetch last 10 commits, polling every 10 seconds
  const { data: commits } = useQuery<GitCommit[]>({
    queryKey: ['git-commits', workingDirectory],
    queryFn: () => getGitCommits(workingDirectory!, 10),
    enabled: !!workingDirectory,
    refetchInterval: 10000,
  })

  // Fetch CI status, polling every 15 seconds
  const { data: ciStatusData } = useQuery({
    queryKey: ['ci-status-widget', workingDirectory],
    queryFn: () => getCIStatus(workingDirectory!),
    enabled: !!workingDirectory,
    refetchInterval: 15000,
  })

  const ciStatus: CIPipelineStatus | null = ciStatusData?.status ?? null

  // Track new commits arriving
  useEffect(() => {
    if (!commits || commits.length === 0) return
    const currentShas = commits.map(c => c.sha)
    const prevShas = prevCommitsRef.current

    if (prevShas.length > 0) {
      const newOnes = currentShas.filter(sha => !prevShas.includes(sha))
      if (newOnes.length > 0) {
        setSeenCount(prev => prev + newOnes.length)
        setHasNewSinceClick(true)
      }
    }
    prevCommitsRef.current = currentShas
  }, [commits])

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setExpanded(false)
      }
    }
    if (expanded) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [expanded])

  const handleClick = useCallback(() => {
    setExpanded(v => !v)
    if (!expanded) {
      // Opening the dropdown resets the notification state
      setSeenCount(0)
      setHasNewSinceClick(false)
    }
  }, [expanded])

  if (!workingDirectory) return null

  const totalCommits = commits?.length ?? 0
  const unseenBadge = seenCount > 0 ? seenCount : null

  // Derive blink color from unseen commits + CI status.
  // When dropdown is open (user has seen everything), suppress the blink.
  const blinkColor = expanded ? null : resolveBlinkColor(seenCount, ciStatus)
  const hasNotification = blinkColor !== null || hasNewSinceClick
  const style = blinkColor ? BLINK_STYLES[blinkColor] : null

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Compact square button with bold "G" */}
      <button
        onClick={handleClick}
        className={`
          relative flex items-center justify-center w-8 h-8 rounded-md border
          transition-all duration-200 hover:opacity-80 bg-card
          ${hasNotification && style ? `${style.border} animate-pulse` : 'border-border'}
        `}
        title={`Git Activity (${totalCommits} recent commits)`}
      >
        <span
          className={`
            text-sm font-black leading-none select-none
            ${hasNotification && style ? style.text : 'text-muted-foreground'}
          `}
        >
          G
        </span>

        {/* Badge for unseen commits */}
        {unseenBadge != null && (
          <span
            className={`
              absolute -top-1.5 -right-1.5 flex items-center justify-center
              min-w-[16px] h-4 px-1 text-[9px] font-bold text-white rounded-full
              border border-background
              ${style ? style.badge : 'bg-cyan-500'}
            `}
          >
            {unseenBadge > 9 ? '9+' : unseenBadge}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {expanded && (
        <div className="absolute top-full right-0 mt-1 z-50 w-80 bg-card border-2 border-border rounded-lg shadow-lg overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-3 py-2 border-b border-border">
            <span className="text-xs font-bold text-foreground">Recent Commits</span>
            {onOpenProcessingLog && (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  setExpanded(false)
                  onOpenProcessingLog()
                }}
                className="flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold text-violet-400 hover:bg-violet-500/15 transition-colors"
                title="Open CI Processing Log"
              >
                <FileText size={12} />
                Processing Log
              </button>
            )}
          </div>

          {/* Commit list */}
          <div className="max-h-64 overflow-y-auto">
            {!commits || commits.length === 0 ? (
              <div className="px-3 py-4 text-center text-xs text-muted-foreground">
                No commits found
              </div>
            ) : (
              commits.map((commit) => (
                <div
                  key={commit.sha}
                  className="px-3 py-2 hover:bg-muted/50 border-b border-border/50 last:border-0"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono text-cyan-400 shrink-0">
                      {commit.short_sha}
                    </span>
                    <span className="text-[10px] text-muted-foreground shrink-0">
                      {timeAgo(commit.timestamp)}
                    </span>
                  </div>
                  <div className="text-xs text-foreground/80 truncate mt-0.5">
                    {commit.message}
                  </div>
                  <div className="text-[10px] text-muted-foreground mt-0.5">
                    {commit.author}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
