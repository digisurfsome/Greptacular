/**
 * ProcessingLogPanel - Slide-out panel showing CI event timeline per commit.
 *
 * Shows the full lifecycle of each commit through the CI pipeline:
 * commit pushed → CI started → passed/failed → auto-fix → re-run → merged → deployed.
 *
 * Opens from the right side as a slide-out panel.
 * Includes "stuck" detection: flags commits in "running" state for >1 hour.
 */

import { useState, useEffect, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getGitCommits, getCITimeline } from '../lib/api'
import type { GitCommit, CITimelineEvent } from '../lib/types'
import {
  X,
  Check,
  AlertTriangle,
  Loader2,
  Wrench,
  GitMerge,
  Clock,
  GitCommit as GitCommitIcon,
  ChevronDown,
  ChevronRight,
} from 'lucide-react'

interface ProcessingLogPanelProps {
  workingDirectory: string | null
  open: boolean
  onClose: () => void
}

const EVENT_ICONS: Record<string, { icon: typeof Check; color: string }> = {
  ci_passed: { icon: Check, color: 'text-emerald-400' },
  ci_failed: { icon: AlertTriangle, color: 'text-red-400' },
  fixing: { icon: Wrench, color: 'text-amber-400' },
  merging: { icon: GitMerge, color: 'text-violet-400' },
  merged: { icon: GitMerge, color: 'text-emerald-400' },
  pulled: { icon: Check, color: 'text-emerald-400' },
  deployed: { icon: Check, color: 'text-emerald-400' },
  complete: { icon: Check, color: 'text-emerald-400' },
  exhausted: { icon: AlertTriangle, color: 'text-red-400' },
  vetoed: { icon: X, color: 'text-amber-400' },
  pull_warning: { icon: AlertTriangle, color: 'text-amber-400' },
}

function formatTime(isoDate: string): string {
  const d = new Date(isoDate)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function formatDate(isoDate: string): string {
  const d = new Date(isoDate)
  return d.toLocaleDateString([], { month: 'short', day: 'numeric' })
}

function EventIcon({ eventType }: { eventType: string }) {
  const config = EVENT_ICONS[eventType]
  if (config) {
    const Icon = config.icon
    return <Icon size={12} className={config.color} />
  }
  return <Clock size={12} className="text-muted-foreground" />
}

/** Group timeline events by commit SHA */
function groupByCommit(
  events: CITimelineEvent[],
  commits: GitCommit[],
): Array<{ sha: string; shortSha: string; message: string; author: string; timestamp: string; events: CITimelineEvent[]; status: 'success' | 'failed' | 'running' | 'stuck' | 'unknown' }> {
  const commitMap = new Map(commits.map(c => [c.short_sha, c]))
  const groups = new Map<string, CITimelineEvent[]>()

  // Group events by commit SHA
  for (const event of events) {
    const key = event.commit_sha ?? 'unknown'
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key)!.push(event)
  }

  // Build result from commits (to preserve order), filling in events
  const result: Array<{ sha: string; shortSha: string; message: string; author: string; timestamp: string; events: CITimelineEvent[]; status: 'success' | 'failed' | 'running' | 'stuck' | 'unknown' }> = []

  for (const commit of commits) {
    const evts = groups.get(commit.short_sha) ?? []
    // Sort events chronologically
    evts.sort((a, b) => a.timestamp.localeCompare(b.timestamp))

    // Determine overall status
    let status: 'success' | 'failed' | 'running' | 'stuck' | 'unknown' = 'unknown'
    if (evts.some(e => e.event_type === 'complete' || e.event_type === 'deployed')) {
      status = 'success'
    } else if (evts.some(e => e.event_type === 'exhausted')) {
      status = 'failed'
    } else if (evts.some(e => e.event_type === 'ci_failed')) {
      // Check if there's a fix after the failure
      let lastFail = -1
      for (let i = evts.length - 1; i >= 0; i--) {
        if (evts[i].event_type === 'ci_failed') { lastFail = i; break }
      }
      const hasFixAfter = lastFail >= 0 && evts.slice(lastFail).some(e => e.event_type === 'ci_passed' || e.event_type === 'complete')
      status = hasFixAfter ? 'success' : 'failed'
    } else if (evts.some(e => e.event_type === 'ci_passed')) {
      status = 'success'
    } else if (evts.length > 0) {
      // Has events but no conclusion — check if stuck
      const oldest = new Date(evts[0].timestamp).getTime()
      const hourAgo = Date.now() - 3600_000
      status = oldest < hourAgo ? 'stuck' : 'running'
    }

    result.push({
      sha: commit.sha,
      shortSha: commit.short_sha,
      message: commit.message,
      author: commit.author,
      timestamp: commit.timestamp,
      events: evts,
      status,
    })
  }

  // Also include events for commits not in the list (orphaned events)
  for (const [sha, evts] of groups) {
    if (sha === 'unknown' || commitMap.has(sha)) continue
    if (!result.some(r => r.shortSha === sha)) {
      result.push({
        sha,
        shortSha: sha,
        message: '(commit not in recent history)',
        author: '',
        timestamp: evts[0]?.timestamp ?? '',
        events: evts.sort((a, b) => a.timestamp.localeCompare(b.timestamp)),
        status: 'unknown',
      })
    }
  }

  return result
}

const STATUS_BADGES: Record<string, { label: string; color: string; bg: string }> = {
  success: { label: 'DEPLOYED', color: 'text-emerald-400', bg: 'bg-emerald-500/15' },
  failed: { label: 'FAILED', color: 'text-red-400', bg: 'bg-red-500/15' },
  running: { label: 'IN PROGRESS', color: 'text-cyan-400', bg: 'bg-cyan-500/15' },
  stuck: { label: 'POSSIBLY STUCK', color: 'text-amber-400', bg: 'bg-amber-500/15' },
  unknown: { label: 'NO CI DATA', color: 'text-muted-foreground', bg: 'bg-muted' },
}

export function ProcessingLogPanel({ workingDirectory, open, onClose }: ProcessingLogPanelProps) {
  const [expandedCommits, setExpandedCommits] = useState<Set<string>>(new Set())

  const { data: commits } = useQuery({
    queryKey: ['git-commits-log', workingDirectory],
    queryFn: () => getGitCommits(workingDirectory!, 10),
    enabled: !!workingDirectory && open,
    refetchInterval: 15000,
  })

  const { data: timeline } = useQuery({
    queryKey: ['ci-timeline', workingDirectory],
    queryFn: () => getCITimeline(workingDirectory!, undefined, 100),
    enabled: !!workingDirectory && open,
    refetchInterval: 15000,
  })

  // Auto-expand the first commit on load
  useEffect(() => {
    if (commits && commits.length > 0 && expandedCommits.size === 0) {
      setExpandedCommits(new Set([commits[0].short_sha]))
    }
  }, [commits, expandedCommits.size])

  const toggleCommit = useCallback((sha: string) => {
    setExpandedCommits(prev => {
      const next = new Set(prev)
      if (next.has(sha)) next.delete(sha)
      else next.add(sha)
      return next
    })
  }, [])

  // Close on Escape
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape' && open) onClose()
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [open, onClose])

  const groups = groupByCommit(timeline ?? [], commits ?? [])

  // Calculate total duration for completed commits
  function getDuration(events: CITimelineEvent[]): string | null {
    if (events.length < 2) return null
    const start = new Date(events[0].timestamp).getTime()
    const end = new Date(events[events.length - 1].timestamp).getTime()
    const diff = Math.max(0, end - start)
    const minutes = Math.floor(diff / 60000)
    const seconds = Math.floor((diff % 60000) / 1000)
    if (minutes > 0) return `${minutes}m ${seconds}s`
    return `${seconds}s`
  }

  return (
    <>
      {/* Backdrop */}
      {open && (
        <div
          className="fixed inset-0 bg-black/30 z-[90] transition-opacity"
          onClick={onClose}
        />
      )}

      {/* Slide-out panel */}
      <div
        className={`
          fixed top-0 right-0 h-full w-96 bg-card border-l-2 border-border shadow-2xl z-[95]
          transform transition-transform duration-300 ease-out
          ${open ? 'translate-x-0' : 'translate-x-full'}
        `}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <div className="flex items-center gap-2">
            <GitCommitIcon size={16} className="text-cyan-400" />
            <span className="text-sm font-bold text-foreground">Processing Log</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-muted transition-colors"
            title="Close (Esc)"
          >
            <X size={16} className="text-muted-foreground" />
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto h-[calc(100%-52px)]">
          {groups.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
              <Loader2 size={24} className="animate-spin mb-2" />
              <span className="text-xs">Waiting for commit data...</span>
            </div>
          ) : (
            groups.map((group) => {
              const isExpanded = expandedCommits.has(group.shortSha)
              const badge = STATUS_BADGES[group.status]
              const duration = getDuration(group.events)

              return (
                <div key={group.sha} className="border-b border-border/50">
                  {/* Commit header — click to expand */}
                  <button
                    onClick={() => toggleCommit(group.shortSha)}
                    className="w-full flex items-start gap-2 px-4 py-3 hover:bg-muted/30 text-left transition-colors"
                  >
                    <div className="mt-0.5 shrink-0">
                      {isExpanded
                        ? <ChevronDown size={14} className="text-muted-foreground" />
                        : <ChevronRight size={14} className="text-muted-foreground" />
                      }
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-mono text-cyan-400">
                          {group.shortSha}
                        </span>
                        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${badge.color} ${badge.bg}`}>
                          {badge.label}
                        </span>
                        {duration && group.status === 'success' && (
                          <span className="text-[9px] text-muted-foreground">
                            {duration}
                          </span>
                        )}
                        {group.status === 'stuck' && (
                          <AlertTriangle size={12} className="text-amber-400 animate-pulse" />
                        )}
                      </div>
                      <div className="text-xs text-foreground/80 truncate mt-0.5">
                        {group.message}
                      </div>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-[10px] text-muted-foreground">
                          {group.author}
                        </span>
                        <span className="text-[10px] text-muted-foreground">
                          {formatDate(group.timestamp)} {formatTime(group.timestamp)}
                        </span>
                      </div>
                    </div>
                  </button>

                  {/* Timeline events */}
                  {isExpanded && (
                    <div className="px-4 pb-3 pl-9">
                      {group.events.length === 0 ? (
                        <div className="text-[10px] text-muted-foreground italic py-2">
                          No CI events recorded for this commit
                        </div>
                      ) : (
                        <div className="relative">
                          {/* Vertical timeline line */}
                          <div className="absolute left-[5px] top-2 bottom-2 w-px bg-border" />

                          {group.events.map((event) => (
                            <div key={event.id} className="relative flex items-start gap-3 py-1.5">
                              {/* Timeline dot */}
                              <div className="relative z-10 mt-0.5 shrink-0">
                                <EventIcon eventType={event.event_type} />
                              </div>
                              {/* Event content */}
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                  <span className="text-[10px] text-muted-foreground">
                                    {formatTime(event.timestamp)}
                                  </span>
                                  <span className="text-[10px] font-medium text-foreground/90">
                                    {event.message}
                                  </span>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            })
          )}
        </div>
      </div>
    </>
  )
}
