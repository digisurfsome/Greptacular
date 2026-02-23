/**
 * GitActivityWidget - Compact git commit activity indicator with dropdown.
 *
 * Shows a small square with a git icon and an unseen-commit badge.
 * Click to expand a dropdown of the last 10 commits with timestamps.
 * Blinks cyan when new commits arrive. Badge resets on click.
 * Includes a "Processing Log" button that opens the slide-out panel.
 *
 * Placed on: AutoForge front page header + Workspace breadcrumb bar.
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getGitCommits } from '../lib/api'
import type { GitCommit } from '../lib/types'
import { GitCommit as GitCommitIcon, FileText } from 'lucide-react'

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

export function GitActivityWidget({ workingDirectory, onOpenProcessingLog }: GitActivityWidgetProps) {
  const [expanded, setExpanded] = useState(false)
  const [seenCount, setSeenCount] = useState(0)
  const [hasNewSinceClick, setHasNewSinceClick] = useState(false)
  const prevCommitsRef = useRef<string[]>([])
  const dropdownRef = useRef<HTMLDivElement>(null)

  const { data: commits } = useQuery<GitCommit[]>({
    queryKey: ['git-commits', workingDirectory],
    queryFn: () => getGitCommits(workingDirectory!, 10),
    enabled: !!workingDirectory,
    refetchInterval: 10000,
  })

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
      // Opening — mark all as seen
      setSeenCount(0)
      setHasNewSinceClick(false)
    }
  }, [expanded])

  if (!workingDirectory) return null

  const totalCommits = commits?.length ?? 0
  const unseenBadge = seenCount > 0 ? seenCount : null

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Compact square button */}
      <button
        onClick={handleClick}
        className={`
          relative flex items-center justify-center w-8 h-8 rounded-md border border-border
          transition-all duration-200 hover:opacity-80 bg-card
          ${hasNewSinceClick ? 'animate-pulse border-cyan-400/60' : ''}
        `}
        title={`Git Activity (${totalCommits} recent commits)`}
      >
        <GitCommitIcon size={16} className={hasNewSinceClick ? 'text-cyan-400' : 'text-muted-foreground'} />

        {/* Badge for unseen commits */}
        {unseenBadge != null && (
          <span className="absolute -top-1.5 -right-1.5 flex items-center justify-center min-w-[16px] h-4 px-1 text-[9px] font-bold text-white bg-cyan-500 rounded-full border border-background">
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
