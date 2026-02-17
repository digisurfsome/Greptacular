/**
 * Workspace Chat Header
 *
 * Header bar for the active workspace conversation. Displays an editable
 * title (click to edit, save on blur or Enter), a category selector
 * dropdown, and a live connection status indicator with animated icons.
 */

import { useState, useCallback, useRef, useEffect } from 'react'
import { Wifi, WifiOff, Loader2 } from 'lucide-react'

interface WorkspaceChatHeaderProps {
  conversationId: number | null
  title: string | null
  category: string
  connectionStatus: 'disconnected' | 'connecting' | 'connected' | 'error'
  onUpdateTitle: (title: string) => void
  onUpdateCategory: (category: string) => void
}

/** Ordered list of available conversation categories. */
const CATEGORIES = [
  'general',
  'debugging',
  'refactoring',
  'feature',
  'exploration',
] as const

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
  connectionStatus,
  onUpdateTitle,
  onUpdateCategory,
}: WorkspaceChatHeaderProps): React.JSX.Element {
  const [isEditing, setIsEditing] = useState(false)
  const [editValue, setEditValue] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  // Focus the input when entering edit mode
  useEffect(() => {
    if (isEditing) {
      inputRef.current?.focus()
      inputRef.current?.select()
    }
  }, [isEditing])

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

  const handleCategoryChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      onUpdateCategory(e.target.value)
    },
    [onUpdateCategory],
  )

  return (
    <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-card">
      {/* Left: editable title */}
      <div className="flex items-center gap-3 min-w-0 flex-1">
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
          <span
            role="button"
            tabIndex={0}
            onClick={handleStartEditing}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') handleStartEditing()
            }}
            className={`text-sm font-medium truncate cursor-pointer hover:underline ${
              title ? 'text-foreground' : 'text-muted-foreground italic'
            }`}
            title={title ?? 'Click to set title'}
          >
            {title ?? 'Untitled Conversation'}
          </span>
        )}

        {/* Category selector */}
        {conversationId !== null && (
          <select
            value={category}
            onChange={handleCategoryChange}
            className="text-xs bg-input border border-border rounded px-1.5 py-0.5 text-foreground outline-none ring-ring focus:ring-1"
            aria-label="Conversation category"
          >
            {CATEGORIES.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Right: connection status */}
      <ConnectionIndicator status={connectionStatus} />
    </div>
  )
}
