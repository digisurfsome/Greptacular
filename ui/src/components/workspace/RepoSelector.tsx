/**
 * RepoSelector
 *
 * A dropdown selector for picking a GitHub repository from the user's
 * account. Fetches repos via the `gh` CLI through the backend, provides
 * search/filter, and clones the selected repo to produce a local path.
 *
 * Designed for the workspace breadcrumb bar. Uses a custom dropdown
 * (no Radix Popover) to keep dependencies minimal.
 */

import { useState, useCallback, useRef, useEffect, useMemo } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import {
  GitBranch,
  Lock,
  Search,
  Loader2,
  ChevronDown,
  AlertCircle,
  X,
  FolderGit2,
} from 'lucide-react'
import { listGitHubRepos, cloneGitHubRepo } from '@/lib/api'
import type { GitHubRepo } from '@/lib/api'
import { Button } from '@/components/ui/button'

interface RepoSelectorProps {
  /** Called with the local path once a repo is selected and cloned. */
  onSelect: (localPath: string) => void
  /** The currently selected working directory, if any. */
  selectedPath: string | null
}

/**
 * Format an ISO date string into a relative time description
 * (e.g. "2 days ago", "3 months ago").
 */
function formatRelativeTime(isoDate: string): string {
  const date = new Date(isoDate)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMinutes = Math.floor(diffMs / 60_000)
  const diffHours = Math.floor(diffMs / 3_600_000)
  const diffDays = Math.floor(diffMs / 86_400_000)

  if (diffMinutes < 1) return 'just now'
  if (diffMinutes < 60) return `${diffMinutes}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 30) return `${diffDays}d ago`
  if (diffDays < 365) return `${Math.floor(diffDays / 30)}mo ago`
  return `${Math.floor(diffDays / 365)}y ago`
}

/** Extracts a display label from a local path. */
function labelFromPath(path: string): string {
  const parts = path.replace(/\\/g, '/').split('/')
  return parts[parts.length - 1] || path
}

/** GitHub repo selector dropdown for the workspace breadcrumb bar. */
export function RepoSelector({ onSelect, selectedPath }: RepoSelectorProps): React.JSX.Element {
  const [isOpen, setIsOpen] = useState(false)
  const [filter, setFilter] = useState('')
  const dropdownRef = useRef<HTMLDivElement>(null)
  const searchInputRef = useRef<HTMLInputElement>(null)

  // Fetch repos from the backend (which calls `gh repo list`)
  const {
    data,
    isLoading: isLoadingRepos,
    error: fetchError,
  } = useQuery({
    queryKey: ['github-repos'],
    queryFn: listGitHubRepos,
    // Only fetch when the dropdown is open to avoid unnecessary calls
    enabled: isOpen,
    staleTime: 60_000, // Cache for 1 minute
  })

  const ghError = data?.error ?? null

  // Clone mutation
  const cloneMutation = useMutation({
    mutationFn: ({ repoUrl, repoName }: { repoUrl: string; repoName: string }) =>
      cloneGitHubRepo(repoUrl, repoName),
    onSuccess: (result) => {
      onSelect(result.local_path)
      setIsOpen(false)
      setFilter('')
    },
  })

  // Filter repos by search term. Derives from `data` directly to avoid
  // creating a new array reference on every render (react-hooks/exhaustive-deps).
  const filteredRepos = useMemo(() => {
    const repos = data?.repos ?? []
    if (!filter.trim()) return repos
    const term = filter.toLowerCase()
    return repos.filter(
      (repo: GitHubRepo) =>
        repo.name.toLowerCase().includes(term) ||
        repo.nameWithOwner.toLowerCase().includes(term) ||
        (repo.description && repo.description.toLowerCase().includes(term)),
    )
  }, [data, filter])

  // Close dropdown on outside click
  useEffect(() => {
    if (!isOpen) return

    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
        setFilter('')
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [isOpen])

  // Focus search input when dropdown opens
  useEffect(() => {
    if (isOpen) {
      // Small delay so the DOM has rendered
      const timer = setTimeout(() => searchInputRef.current?.focus(), 50)
      return () => clearTimeout(timer)
    }
  }, [isOpen])

  // Close dropdown on Escape
  useEffect(() => {
    if (!isOpen) return

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setIsOpen(false)
        setFilter('')
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isOpen])

  const handleRepoSelect = useCallback(
    (repo: GitHubRepo) => {
      cloneMutation.mutate({
        repoUrl: repo.url,
        repoName: repo.nameWithOwner,
      })
    },
    [cloneMutation],
  )

  const handleClear = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation()
      onSelect('')
    },
    [onSelect],
  )

  const isCloning = cloneMutation.isPending

  return (
    <div ref={dropdownRef} className="relative">
      {/* Trigger button */}
      <Button
        variant="ghost"
        size="sm"
        className="h-7 px-2 gap-1.5 text-muted-foreground hover:text-foreground max-w-[220px]"
        onClick={() => setIsOpen((v) => !v)}
        disabled={isCloning}
        title={selectedPath || 'Select a GitHub repo'}
      >
        {isCloning ? (
          <Loader2 size={14} className="animate-spin shrink-0" />
        ) : (
          <FolderGit2 size={14} className="shrink-0" />
        )}
        <span className="truncate text-xs">
          {isCloning
            ? 'Cloning...'
            : selectedPath
              ? labelFromPath(selectedPath)
              : 'Select Repo'}
        </span>
        {selectedPath && !isCloning ? (
          <button
            onClick={handleClear}
            className="ml-0.5 text-muted-foreground hover:text-foreground"
            title="Clear selection"
          >
            <X size={12} />
          </button>
        ) : (
          <ChevronDown size={12} className="shrink-0" />
        )}
      </Button>

      {/* Dropdown panel */}
      {isOpen && (
        <div className="absolute top-full left-0 mt-1 w-80 bg-popover border border-border rounded-md shadow-lg z-50 overflow-hidden animate-in fade-in-0 zoom-in-95 duration-100">
          {/* Search input */}
          <div className="p-2 border-b border-border">
            <div className="relative">
              <Search size={14} className="absolute left-2 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <input
                ref={searchInputRef}
                type="text"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                placeholder="Search repositories..."
                className="w-full pl-7 pr-3 py-1.5 text-xs bg-background border border-input rounded-md text-foreground placeholder:text-muted-foreground outline-none ring-ring focus:ring-1"
              />
            </div>
          </div>

          {/* Content area */}
          <div className="max-h-64 overflow-y-auto">
            {/* Loading state */}
            {isLoadingRepos && (
              <div className="flex items-center justify-center gap-2 py-8 text-muted-foreground">
                <Loader2 size={16} className="animate-spin" />
                <span className="text-xs">Loading repositories...</span>
              </div>
            )}

            {/* Error from fetch failure */}
            {fetchError && !isLoadingRepos && (
              <div className="flex items-center gap-2 px-3 py-4 text-xs text-destructive">
                <AlertCircle size={14} className="shrink-0" />
                <span>Failed to load repos. Check your connection.</span>
              </div>
            )}

            {/* Error from gh CLI (not installed / not authenticated) */}
            {ghError && !isLoadingRepos && !fetchError && (
              <div className="flex items-start gap-2 px-3 py-4 text-xs text-destructive">
                <AlertCircle size={14} className="shrink-0 mt-0.5" />
                <span>{ghError}</span>
              </div>
            )}

            {/* Clone error */}
            {cloneMutation.isError && (
              <div className="flex items-start gap-2 px-3 py-2 text-xs text-destructive border-b border-border">
                <AlertCircle size={14} className="shrink-0 mt-0.5" />
                <span>
                  {cloneMutation.error instanceof Error
                    ? cloneMutation.error.message
                    : 'Clone failed'}
                </span>
              </div>
            )}

            {/* Repo list */}
            {!isLoadingRepos && !fetchError && !ghError && filteredRepos.length === 0 && (
              <div className="px-3 py-6 text-center text-xs text-muted-foreground">
                {filter ? 'No matching repositories' : 'No repositories found'}
              </div>
            )}

            {!isLoadingRepos &&
              !fetchError &&
              !ghError &&
              filteredRepos.map((repo: GitHubRepo) => (
                <button
                  key={repo.nameWithOwner}
                  onClick={() => handleRepoSelect(repo)}
                  disabled={isCloning}
                  className="w-full text-left px-3 py-2 hover:bg-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed border-b border-border last:border-b-0"
                >
                  <div className="flex items-center gap-2">
                    <GitBranch size={14} className="text-muted-foreground shrink-0" />
                    <span className="text-xs font-medium text-foreground truncate">
                      {repo.nameWithOwner}
                    </span>
                    {repo.isPrivate && (
                      <Lock size={10} className="text-muted-foreground shrink-0" />
                    )}
                    {repo.updatedAt && (
                      <span className="ml-auto text-[10px] text-muted-foreground shrink-0">
                        {formatRelativeTime(repo.updatedAt)}
                      </span>
                    )}
                  </div>
                  {repo.description && (
                    <p className="text-[10px] text-muted-foreground mt-0.5 pl-5 truncate">
                      {repo.description}
                    </p>
                  )}
                </button>
              ))}
          </div>
        </div>
      )}
    </div>
  )
}
