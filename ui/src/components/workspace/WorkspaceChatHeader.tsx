/**
 * Workspace Chat Header
 *
 * Header bar for the active workspace conversation. Displays an editable
 * title (click to edit, save on blur or Enter), a category selector
 * dropdown, tag chips with add/remove, an optional git branch indicator
 * with rename support, and a live connection status indicator.
 */

import { useState, useCallback, useRef, useEffect, useMemo } from 'react'
import { Wifi, WifiOff, Loader2, Tag, X, Plus, GitBranch, Pencil, ExternalLink, GitPullRequest, Settings } from 'lucide-react'
import { getGitBranches, renameGitBranch, getGitRemoteInfo, getGitPrInfo } from '@/lib/api'
import { useWorkspaceCategories } from '@/hooks/useWorkspaceCategories'

interface WorkspaceChatHeaderProps {
  conversationId: number | null
  title: string | null
  category: string
  tags: string
  connectionStatus: 'disconnected' | 'connecting' | 'connected' | 'error'
  onUpdateTitle: (title: string) => void
  onUpdateCategory: (category: string) => void
  onUpdateTags: (tags: string) => void
  workingDirectory?: string | null
  /** Whether the walkie-talkie system is active (agent is working). */
  walkieTalkieActive?: boolean
  /** Whether the agent is currently waiting for user input. */
  agentWaiting?: boolean
  /** Callback to toggle walkie-talkie settings panel. */
  onToggleSettings?: () => void
  /** Whether the settings panel is currently open. */
  settingsOpen?: boolean
}

/** Default categories used as fallbacks when no custom categories exist. */
const DEFAULT_CATEGORIES = [
  'general',
  'debugging',
  'refactoring',
  'feature',
  'exploration',
]

/** Branch names that should not be renamed. */
const PROTECTED_BRANCHES = ['main', 'master']

/**
 * Maps a connection status value to a visual indicator element
 * (colored dot and icon).
 */
function ConnectionIndicator({
  status,
}: {
  status: WorkspaceChatHeaderProps['connectionStatus']
}): React.JSX.Element {
  switch (status) {
    case 'connected':
      return (
        <div className="flex items-center gap-1.5">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full rounded-full bg-green-500 opacity-75 animate-ping" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500" />
          </span>
          <Wifi size={14} className="text-muted-foreground" />
        </div>
      )
    case 'connecting':
      return (
        <div className="flex items-center gap-1.5">
          <span className="relative flex h-2 w-2">
            <span className="relative inline-flex h-2 w-2 rounded-full bg-yellow-500" />
          </span>
          <Loader2 size={14} className="text-muted-foreground animate-spin" />
        </div>
      )
    case 'disconnected':
    case 'error':
      return (
        <div className="flex items-center gap-1.5">
          <span className="relative flex h-2 w-2">
            <span className="relative inline-flex h-2 w-2 rounded-full bg-red-500" />
          </span>
          <WifiOff size={14} className="text-muted-foreground" />
        </div>
      )
  }
}

/** Header bar for the active workspace conversation. */
export function WorkspaceChatHeader({
  conversationId,
  title,
  category,
  tags,
  connectionStatus,
  onUpdateTitle,
  onUpdateCategory,
  onUpdateTags,
  workingDirectory,
  walkieTalkieActive = false,
  agentWaiting = false,
  onToggleSettings,
  settingsOpen = false,
}: WorkspaceChatHeaderProps): React.JSX.Element {
  // --- Title editing state ---
  const [isEditing, setIsEditing] = useState(false)
  const [editValue, setEditValue] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  // --- Tag adding state ---
  const [isAddingTag, setIsAddingTag] = useState(false)
  const [newTagValue, setNewTagValue] = useState('')
  const tagInputRef = useRef<HTMLInputElement>(null)

  // --- Branch state ---
  const [currentBranch, setCurrentBranch] = useState<string | null>(null)
  const [isEditingBranch, setIsEditingBranch] = useState(false)
  const [branchEditValue, setBranchEditValue] = useState('')
  const [branchLoading, setBranchLoading] = useState(false)
  const branchInputRef = useRef<HTMLInputElement>(null)

  // --- Repo & PR state ---
  const [githubUrl, setGithubUrl] = useState<string | null>(null)
  const [prUrl, setPrUrl] = useState<string | null>(null)

  // Fetch custom categories and merge with defaults
  const { data: customCategories = [] } = useWorkspaceCategories()
  const allCategories = useMemo(() => {
    const customNames = customCategories.map((c) => c.name)
    const merged = [...DEFAULT_CATEGORIES]
    for (const name of customNames) {
      if (!merged.includes(name)) {
        merged.push(name)
      }
    }
    // Ensure current category is always in the list (even if deleted)
    if (category && !merged.includes(category)) {
      merged.push(category)
    }
    return merged
  }, [customCategories, category])

  // Focus the title input when entering edit mode
  useEffect(() => {
    if (isEditing) {
      inputRef.current?.focus()
      inputRef.current?.select()
    }
  }, [isEditing])

  // Focus the tag input when adding a tag
  useEffect(() => {
    if (isAddingTag) {
      tagInputRef.current?.focus()
    }
  }, [isAddingTag])

  // Focus the branch input when editing branch name
  useEffect(() => {
    if (isEditingBranch) {
      branchInputRef.current?.focus()
      branchInputRef.current?.select()
    }
  }, [isEditingBranch])

  // Fetch git branch info when workingDirectory changes
  useEffect(() => {
    if (!workingDirectory) {
      setCurrentBranch(null)
      return
    }

    let cancelled = false
    getGitBranches(workingDirectory)
      .then((result) => {
        if (!cancelled) {
          setCurrentBranch(result.current_branch)
        }
      })
      .catch(() => {
        // Not a git repo or API error -- silently ignore
        if (!cancelled) {
          setCurrentBranch(null)
        }
      })

    return () => { cancelled = true }
  }, [workingDirectory])

  // Fetch GitHub remote URL when workingDirectory changes
  useEffect(() => {
    if (!workingDirectory) {
      setGithubUrl(null)
      return
    }

    let cancelled = false
    getGitRemoteInfo(workingDirectory)
      .then((result) => {
        if (!cancelled) {
          setGithubUrl(result.github_url)
        }
      })
      .catch(() => {
        if (!cancelled) setGithubUrl(null)
      })

    return () => { cancelled = true }
  }, [workingDirectory])

  // Check for PR on the current branch (re-check when branch changes)
  useEffect(() => {
    if (!workingDirectory || !currentBranch) {
      setPrUrl(null)
      return
    }

    let cancelled = false
    getGitPrInfo(workingDirectory, currentBranch)
      .then((result) => {
        if (!cancelled) {
          setPrUrl(result.pr_url)
        }
      })
      .catch(() => {
        if (!cancelled) setPrUrl(null)
      })

    return () => { cancelled = true }
  }, [workingDirectory, currentBranch])

  // --- Title handlers ---
  const handleStartEditing = useCallback(() => {
    if (conversationId === null) return
    setEditValue(title ?? '')
    setIsEditing(true)
  }, [conversationId, title])

  const handleSave = useCallback(() => {
    const trimmed = editValue.trim()
    if (trimmed && trimmed !== (title ?? '')) {
      onUpdateTitle(trimmed)
    }
    setIsEditing(false)
  }, [editValue, title, onUpdateTitle])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter') {
        e.preventDefault()
        handleSave()
      } else if (e.key === 'Escape') {
        setIsEditing(false)
      }
    },
    [handleSave],
  )

  // --- New category state ---
  const [isAddingCategory, setIsAddingCategory] = useState(false)
  const [newCategoryValue, setNewCategoryValue] = useState('')
  const newCategoryRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (isAddingCategory) {
      newCategoryRef.current?.focus()
    }
  }, [isAddingCategory])

  const handleCategoryChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      if (e.target.value === '__add_new__') {
        setIsAddingCategory(true)
        return
      }
      onUpdateCategory(e.target.value)
    },
    [onUpdateCategory],
  )

  const handleSaveNewCategory = useCallback(() => {
    const trimmed = newCategoryValue.trim()
    if (trimmed) {
      onUpdateCategory(trimmed)
    }
    setIsAddingCategory(false)
    setNewCategoryValue('')
  }, [newCategoryValue, onUpdateCategory])

  const handleNewCategoryKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter') {
        e.preventDefault()
        handleSaveNewCategory()
      } else if (e.key === 'Escape') {
        setIsAddingCategory(false)
        setNewCategoryValue('')
      }
    },
    [handleSaveNewCategory],
  )

  // --- Tag handlers ---
  const tagList = useMemo(
    () => (tags ? tags.split(',').map((t) => t.trim()).filter(Boolean) : []),
    [tags],
  )

  const handleRemoveTag = useCallback(
    (tagToRemove: string) => {
      const updated = tagList.filter((t) => t !== tagToRemove)
      onUpdateTags(updated.join(', '))
    },
    [tagList, onUpdateTags],
  )

  const handleAddTag = useCallback(() => {
    const trimmed = newTagValue.trim()
    if (!trimmed) {
      setIsAddingTag(false)
      setNewTagValue('')
      return
    }
    // Avoid duplicates (case-insensitive)
    if (tagList.some((t) => t.toLowerCase() === trimmed.toLowerCase())) {
      setIsAddingTag(false)
      setNewTagValue('')
      return
    }
    const updated = [...tagList, trimmed]
    onUpdateTags(updated.join(', '))
    setNewTagValue('')
    setIsAddingTag(false)
  }, [newTagValue, tagList, onUpdateTags])

  const handleTagKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter') {
        e.preventDefault()
        handleAddTag()
      } else if (e.key === 'Escape') {
        setIsAddingTag(false)
        setNewTagValue('')
      }
    },
    [handleAddTag],
  )

  // --- Branch handlers ---
  const isProtectedBranch = currentBranch ? PROTECTED_BRANCHES.includes(currentBranch) : false

  const handleStartBranchEdit = useCallback(() => {
    if (!currentBranch || isProtectedBranch) return
    setBranchEditValue(currentBranch)
    setIsEditingBranch(true)
  }, [currentBranch, isProtectedBranch])

  const handleSaveBranch = useCallback(async () => {
    const trimmed = branchEditValue.trim()
    if (!trimmed || trimmed === currentBranch || !workingDirectory || !currentBranch) {
      setIsEditingBranch(false)
      return
    }

    setBranchLoading(true)
    try {
      await renameGitBranch(workingDirectory, currentBranch, trimmed)
      setCurrentBranch(trimmed)
    } catch (err) {
      console.error('Failed to rename branch:', err)
    } finally {
      setBranchLoading(false)
      setIsEditingBranch(false)
    }
  }, [branchEditValue, currentBranch, workingDirectory])

  const handleBranchKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter') {
        e.preventDefault()
        handleSaveBranch()
      } else if (e.key === 'Escape') {
        setIsEditingBranch(false)
      }
    },
    [handleSaveBranch],
  )

  return (
    <div className="flex items-center flex-wrap gap-y-1 justify-between px-4 py-2 border-b border-border bg-card">
      {/* Left section: title, category, tags, branch */}
      <div className="flex items-center gap-3 min-w-0 flex-1 flex-wrap gap-y-1">
        {/* Editable title */}
        {isEditing ? (
          <input
            ref={inputRef}
            type="text"
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onBlur={handleSave}
            onKeyDown={handleKeyDown}
            className="text-sm font-medium bg-input border border-border rounded px-2 py-1 outline-none ring-ring focus:ring-1 min-w-0 flex-1 max-w-xs text-foreground"
            aria-label="Conversation title"
          />
        ) : (
          <button
            type="button"
            onClick={handleStartEditing}
            className={`flex items-center gap-1.5 text-sm font-medium truncate cursor-pointer group ${
              title ? 'text-foreground' : 'text-muted-foreground italic'
            }`}
            title={title ? 'Click to rename' : 'Click to set title'}
          >
            <span className="truncate">{title ?? 'Untitled Conversation'}</span>
            {conversationId !== null && (
              <Pencil size={12} className="flex-shrink-0 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
            )}
          </button>
        )}

        {/* Category selector */}
        {conversationId !== null && (
          isAddingCategory ? (
            <input
              ref={newCategoryRef}
              type="text"
              value={newCategoryValue}
              onChange={(e) => setNewCategoryValue(e.target.value)}
              onBlur={handleSaveNewCategory}
              onKeyDown={handleNewCategoryKeyDown}
              placeholder="New category..."
              className="text-xs bg-input border border-border rounded px-1.5 py-0.5 outline-none ring-ring focus:ring-1 w-24 text-foreground"
              aria-label="New category name"
            />
          ) : (
            <select
              value={category}
              onChange={handleCategoryChange}
              className="text-xs bg-input border border-border rounded px-1.5 py-0.5 text-foreground outline-none ring-ring focus:ring-1"
              aria-label="Conversation category"
            >
              {allCategories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
              <option value="__add_new__">+ Add new...</option>
            </select>
          )
        )}

        {/* Tags section */}
        {conversationId !== null && (
          <div className="flex items-center gap-1 flex-wrap">
            {tagList.map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full bg-primary/10 text-primary text-[10px] font-medium"
              >
                {tag}
                <button
                  onClick={() => handleRemoveTag(tag)}
                  className="hover:text-destructive transition-colors"
                  aria-label={`Remove tag ${tag}`}
                >
                  <X size={10} />
                </button>
              </span>
            ))}

            {isAddingTag ? (
              <input
                ref={tagInputRef}
                type="text"
                value={newTagValue}
                onChange={(e) => setNewTagValue(e.target.value)}
                onBlur={handleAddTag}
                onKeyDown={handleTagKeyDown}
                placeholder="tag..."
                className="text-[10px] bg-input border border-border rounded-full px-1.5 py-0.5 outline-none ring-ring focus:ring-1 w-16 text-foreground"
                aria-label="New tag"
              />
            ) : (
              <button
                onClick={() => setIsAddingTag(true)}
                className="inline-flex items-center gap-0.5 px-1 py-0.5 rounded-full text-[10px] text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                aria-label="Add tag"
                title="Add tag"
              >
                <Tag size={10} />
                <Plus size={8} />
              </button>
            )}
          </div>
        )}

        {/* Git branch indicator */}
        {currentBranch && (
          <div className="flex items-center gap-1 text-muted-foreground">
            <GitBranch size={12} />
            {isEditingBranch ? (
              <input
                ref={branchInputRef}
                type="text"
                value={branchEditValue}
                onChange={(e) => setBranchEditValue(e.target.value)}
                onBlur={() => handleSaveBranch()}
                onKeyDown={handleBranchKeyDown}
                disabled={branchLoading}
                className="text-[10px] bg-input border border-border rounded px-1.5 py-0.5 outline-none ring-ring focus:ring-1 w-28 text-foreground"
                aria-label="Rename branch"
              />
            ) : (
              <>
                <span className="text-[10px] font-mono truncate max-w-[120px]" title={currentBranch}>
                  {currentBranch}
                </span>
                {!isProtectedBranch && (
                  <button
                    onClick={handleStartBranchEdit}
                    className="hover:text-foreground transition-colors"
                    aria-label="Rename branch"
                    title="Rename branch"
                  >
                    <Pencil size={10} />
                  </button>
                )}
              </>
            )}
            {branchLoading && <Loader2 size={10} className="animate-spin" />}
          </div>
        )}
      </div>

      {/* Right: repo link, PR link, connection status */}
      <div className="flex items-center gap-2">
        {githubUrl && (
          <a
            href={githubUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium bg-muted text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
            title="View repository on GitHub"
          >
            <ExternalLink size={10} />
            Repo
          </a>
        )}
        {prUrl && (
          <a
            href={prUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium bg-primary/10 text-primary hover:bg-primary/20 transition-colors"
            title="View pull request on GitHub"
          >
            <GitPullRequest size={10} />
            View PR
          </a>
        )}
        {/* Walkie-talkie settings gear */}
        <button
          type="button"
          onClick={onToggleSettings}
          className={`p-1 rounded transition-colors ${
            settingsOpen
              ? 'text-amber-600 dark:text-amber-400 bg-amber-100 dark:bg-amber-900/30'
              : 'text-muted-foreground hover:text-foreground hover:bg-muted'
          }`}
          title="Walkie-talkie settings"
          aria-label="Walkie-talkie settings"
        >
          <Settings size={14} />
        </button>
        {/* Walkie-talkie status indicator */}
        {walkieTalkieActive && (
          <div className="flex items-center gap-1.5 text-[10px] font-medium text-amber-600 dark:text-amber-400">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full rounded-full bg-amber-500 opacity-75 animate-ping" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-amber-500" />
            </span>
            {agentWaiting ? 'Waiting' : 'Live'}
          </div>
        )}
        <ConnectionIndicator status={connectionStatus} />
      </div>
    </div>
  )
}
