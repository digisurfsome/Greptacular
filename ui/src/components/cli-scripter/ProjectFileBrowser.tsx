/**
 * ProjectFileBrowser - Collapsible mini file browser for the CLI Scripter.
 *
 * Shows top-level files/folders in the selected project directory with
 * relative timestamps and recent git commits. Highlights previous
 * CLI Scripter builds if found. Used in two spots on the page (Project
 * Basics and Generate sections) sharing the same React Query cache.
 */

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  ChevronDown,
  ChevronRight,
  Folder,
  FileText,
  GitCommit,
  RefreshCw,
  Loader2,
  AlertCircle,
} from 'lucide-react'

const API_BASE = import.meta.env.DEV ? 'http://localhost:8888' : ''

interface FileEntry {
  name: string
  is_dir: boolean
  size: number | null
  modified: string
  modified_relative: string
}

interface CommitEntry {
  hash: string
  message: string
  date: string
  date_relative: string
}

interface ProjectInfoResponse {
  path: string
  files: FileEntry[]
  recent_commits: CommitEntry[]
  has_previous_builds: boolean
  is_git_repo: boolean
}

async function fetchProjectInfo(path: string): Promise<ProjectInfoResponse> {
  const res = await fetch(
    `${API_BASE}/api/cli-scripter/project-info?path=${encodeURIComponent(path)}`
  )
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Failed to load project info')
  }
  return res.json()
}

interface ProjectFileBrowserProps {
  /** Absolute path to the project directory */
  projectDir: string
}

export function ProjectFileBrowser({ projectDir }: ProjectFileBrowserProps) {
  const [expanded, setExpanded] = useState(false)

  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ['cli-scripter-project-info', projectDir],
    queryFn: () => fetchProjectInfo(projectDir),
    enabled: !!projectDir.trim() && expanded,
    staleTime: 60_000, // Cache for 1 minute
    retry: 1,
  })

  // No directory entered — don't show anything
  if (!projectDir.trim()) return null

  return (
    <div className="border border-zinc-700/60 rounded-lg overflow-hidden mt-2">
      {/* Header bar — always visible */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2 px-3 py-2 bg-zinc-800/30 hover:bg-zinc-800/50 transition-colors text-left"
      >
        {expanded ? (
          <ChevronDown size={14} className="text-zinc-500" />
        ) : (
          <ChevronRight size={14} className="text-zinc-500" />
        )}
        <Folder size={14} className="text-zinc-400" />
        <span className="text-xs text-zinc-400 flex-1">Project Files</span>
        {data?.has_previous_builds && (
          <span className="text-xs text-orange-400 px-1.5 py-0.5 rounded bg-orange-500/10 border border-orange-500/20">
            Previous builds found
          </span>
        )}
        {expanded && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              refetch()
            }}
            disabled={isFetching}
            className="text-zinc-500 hover:text-orange-400 transition-colors p-0.5"
            title="Refresh"
          >
            {isFetching ? (
              <Loader2 size={12} className="animate-spin" />
            ) : (
              <RefreshCw size={12} />
            )}
          </button>
        )}
      </button>

      {/* Expanded content */}
      {expanded && (
        <div className="border-t border-zinc-800">
          {isLoading ? (
            <div className="flex items-center gap-2 px-3 py-4 text-xs text-zinc-500">
              <Loader2 size={14} className="animate-spin" />
              Loading project files...
            </div>
          ) : isError ? (
            <div className="flex items-center gap-2 px-3 py-3 text-xs text-red-400">
              <AlertCircle size={14} />
              {error instanceof Error ? error.message : 'Failed to load directory'}
            </div>
          ) : data ? (
            <div className="divide-y divide-zinc-800/50">
              {/* File listing */}
              <div className="px-3 py-2 space-y-0.5 max-h-48 overflow-y-auto">
                {data.files.length === 0 ? (
                  <p className="text-xs text-zinc-600 py-2">Empty directory</p>
                ) : (
                  data.files.map((file) => (
                    <div
                      key={file.name}
                      className={`flex items-center gap-2 py-0.5 text-xs ${
                        file.name === 'scripts' && data.has_previous_builds
                          ? 'text-orange-400'
                          : 'text-zinc-400'
                      }`}
                    >
                      {file.is_dir ? (
                        <Folder size={12} className="shrink-0" />
                      ) : (
                        <FileText size={12} className="shrink-0" />
                      )}
                      <span className="flex-1 truncate">{file.name}{file.is_dir ? '/' : ''}</span>
                      <span className="text-zinc-600 shrink-0">{file.modified_relative}</span>
                    </div>
                  ))
                )}
              </div>

              {/* Recent commits */}
              {data.is_git_repo && data.recent_commits.length > 0 && (
                <div className="px-3 py-2 space-y-1">
                  <p className="text-xs text-zinc-500 font-medium flex items-center gap-1">
                    <GitCommit size={12} />
                    Recent commits
                  </p>
                  {data.recent_commits.slice(0, 3).map((commit) => (
                    <div key={commit.hash} className="flex items-start gap-2 text-xs">
                      <span className="text-zinc-600 font-mono shrink-0">{commit.hash}</span>
                      <span className="text-zinc-400 flex-1 truncate">{commit.message}</span>
                      <span className="text-zinc-600 shrink-0">{commit.date_relative}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : null}
        </div>
      )}
    </div>
  )
}
