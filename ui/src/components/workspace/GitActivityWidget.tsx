/**
 * GitActivityWidget - Tiny git activity box for the header bar.
 *
 * Shows a compact "AG" square with a badge count of unseen commits.
 * Click to expand a dropdown of the last 10 commits with times.
 * Blinks when new commits arrive since last click.
 * NEVER steals focus, NEVER opens new tabs, NEVER refreshes.
 */

import { useState, useEffect, useMemo, useRef, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getRecentCommits } from '../../lib/api'
import type { GitCommitInfo, GitCommitsResponse } from '../../lib/types'
import { GitCommit, X } from 'lucide-react'

interface GitActivityWidgetProps {
  workingDirectory: string | null
}

export function GitActivityWidget({ workingDirectory }: GitActivityWidgetProps) {
  const [expanded, setExpanded] = useState(false)
  const [lastSeenSha, setLastSeenSha] = useState<string | null>(null)
  const [unseenCount, setUnseenCount] = useState(0)
  const prevCommitsRef = useRef<GitCommitInfo[]>([])
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Poll for commits every 10 seconds
  const { data } = useQuery<GitCommitsResponse>({
    queryKey: ['git-commits', workingDirectory],
    queryFn: () => getRecentCommits(workingDirectory!, 10),
    enabled: !!workingDirectory,
    refetchInterval: 10000,
  })

  const commits = useMemo(() => data?.commits ?? [], [data?.commits])
  const branch = data?.branch ?? ''

  // Track unseen commits
  useEffect(() => {
    if (commits.length === 0) return

    if (lastSeenSha === null) {
      // First load — mark everything as seen
      setLastSeenSha(commits[0]?.sha ?? null)
      setUnseenCount(0)
      prevCommitsRef.current = commits
      return
    }

    // Count how many new commits since lastSeenSha
    const idx = commits.findIndex(c => c.sha === lastSeenSha)
    if (idx === -1) {
      // All commits are new (lastSeenSha scrolled off)
      setUnseenCount(commits.length)
    } else {
      setUnseenCount(idx)
    }
    prevCommitsRef.current = commits
  }, [commits, lastSeenSha])

  // On click: mark all as seen
  const handleToggle = useCallback(() => {
    setExpanded(v => {
      if (!v && commits.length > 0) {
        // Opening — mark all as seen
        setLastSeenSha(commits[0].sha)
        setUnseenCount(0)
      }
      return !v
    })
  }, [commits])

  // Close on click outside
  useEffect(() => {
    if (!expanded) return
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setExpanded(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [expanded])

  if (!workingDirectory) return null

  const hasNew = unseenCount > 0

  return (
    <div className="relative flex items-center" ref={dropdownRef}>
      {/* Compact square button */}
      <button
        onClick={handleToggle}
        className={`
          relative flex items-center justify-center w-8 h-8
          rounded-md border border-border
          transition-all duration-200 hover:opacity-80
          ${hasNew
            ? 'bg-cyan-500/15 border-cyan-400/50 animate-pulse'
            : 'bg-muted'
          }
        `}
        title={hasNew ? `${unseenCount} new commit${unseenCount > 1 ? 's' : ''}` : 'Git activity'}
      >
        <GitCommit size={16} className={hasNew ? 'text-cyan-400' : 'text-muted-foreground'} />

        {/* Badge */}
        {hasNew && (
          <span className="absolute -top-1.5 -right-1.5 min-w-[18px] h-[18px] flex items-center justify-center rounded-full bg-cyan-500 text-white text-[9px] font-bold px-1 leading-none shadow-sm">
            {unseenCount > 99 ? '99+' : unseenCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {expanded && (
        <div className="absolute top-full right-0 mt-1 z-50 w-80 bg-card border-2 border-border rounded-lg shadow-lg overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-3 py-2 border-b border-border bg-muted/50">
            <div className="flex items-center gap-2">
              <GitCommit size={14} className="text-muted-foreground" />
              <span className="text-xs font-bold text-foreground">Recent Commits</span>
              {branch && (
                <span className="text-[10px] text-muted-foreground font-mono bg-muted px-1.5 py-0.5 rounded">
                  {branch}
                </span>
              )}
            </div>
            <button
              onClick={() => setExpanded(false)}
              className="p-0.5 rounded hover:bg-muted transition-colors"
            >
              <X size={14} className="text-muted-foreground" />
            </button>
          </div>

          {/* Commit list */}
          <div className="max-h-64 overflow-y-auto">
            {commits.length === 0 ? (
              <div className="px-3 py-4 text-center text-xs text-muted-foreground">
                No commits found
              </div>
            ) : (
              commits.map((commit, i) => (
                <div
                  key={commit.sha}
                  className={`
                    px-3 py-2 border-b border-border/50 last:border-b-0
                    hover:bg-muted/30 transition-colors
                    ${i < unseenCount ? 'bg-cyan-500/5' : ''}
                  `}
                >
                  <div className="flex items-start gap-2">
                    <span className="text-[10px] font-mono text-cyan-400 shrink-0 mt-0.5">
                      {commit.short_sha}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="text-[11px] text-foreground truncate leading-tight">
                        {commit.message}
                      </div>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-[10px] text-muted-foreground">
                          {commit.author}
                        </span>
                        <span className="text-[10px] text-muted-foreground/70">
                          {commit.relative_time}
                        </span>
                      </div>
                    </div>
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
