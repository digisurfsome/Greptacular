/**
 * SaveToLibraryModal
 *
 * Modal dialog for saving a chat assistant message to the workspace library.
 * Provides fields for filename, display name, folder selection, and tags.
 * The filename is auto-generated from the first line of content.
 */

import { useState, useCallback, useEffect, useMemo } from 'react'
import { BookmarkPlus, X, Folder, Loader2 } from 'lucide-react'
import { useSaveFromChat, useFolderTree } from '@/hooks/useWorkspaceLibrary'
import type { LibraryFolder } from '@/lib/types'

interface SaveToLibraryModalProps {
  open: boolean
  onClose: () => void
  content: string
}

/**
 * Generates a sanitized filename from the first line of content.
 * Truncates to 40 characters, removes invalid filesystem characters,
 * and appends `.md` extension.
 */
function generateDefaultFilename(content: string): string {
  const firstLine = content.split('\n').find((line) => line.trim().length > 0) ?? 'untitled'
  // Strip leading markdown heading markers (e.g., "## Title" -> "Title")
  const cleaned = firstLine.replace(/^#+\s*/, '').trim()
  // Remove characters that are invalid in filenames
  // eslint-disable-next-line no-control-regex -- intentionally stripping control chars from filenames
  const sanitized = cleaned.replace(/[<>:"/\\|?*\x00-\x1f]/g, '').replace(/\s+/g, '-')
  const truncated = sanitized.slice(0, 40).replace(/-+$/, '')
  return (truncated || 'untitled') + '.md'
}

/**
 * Recursively flattens a nested folder tree into a flat list with depth indicators
 * for rendering as indented select options.
 */
function flattenTree(
  folders: LibraryFolder[],
  depth = 0,
): Array<{ id: number; name: string; depth: number }> {
  const result: Array<{ id: number; name: string; depth: number }> = []
  for (const f of folders) {
    result.push({ id: f.id, name: f.name, depth })
    if (f.children?.length) {
      result.push(...flattenTree(f.children, depth + 1))
    }
  }
  return result
}

export function SaveToLibraryModal({
  open,
  onClose,
  content,
}: SaveToLibraryModalProps): React.JSX.Element | null {
  const [filename, setFilename] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [folderId, setFolderId] = useState<number | undefined>(undefined)
  const [tags, setTags] = useState('')
  const [error, setError] = useState('')

  const saveFromChat = useSaveFromChat()
  const { data: folderTree } = useFolderTree()

  // Reset form state whenever the modal opens with new content
  useEffect(() => {
    if (open) {
      setFilename(generateDefaultFilename(content))
      setDisplayName('')
      setFolderId(undefined)
      setTags('')
      setError('')
    }
  }, [open, content])

  const flatFolders = useMemo(() => {
    if (!folderTree) return []
    return flattenTree(folderTree)
  }, [folderTree])

  const handleSave = useCallback(async () => {
    setError('')
    const trimmedFilename = filename.trim()
    if (!trimmedFilename) {
      setError('Filename is required')
      return
    }

    try {
      await saveFromChat.mutateAsync({
        content,
        filename: trimmedFilename,
        folderId: folderId,
        displayName: displayName.trim() || undefined,
        tags: tags.trim() || undefined,
      })
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save to library')
    }
  }, [content, filename, folderId, displayName, tags, saveFromChat, onClose])

  // Handle Escape key to close the modal
  useEffect(() => {
    if (!open) return

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        e.stopPropagation()
        onClose()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [open, onClose])

  if (!open) return null

  const isSaving = saveFromChat.isPending

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-card border border-border rounded-lg shadow-lg max-w-md w-full mx-4 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <span className="text-sm font-medium text-foreground flex items-center gap-2">
            <BookmarkPlus size={16} />
            Save to Library
          </span>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground"
            aria-label="Close"
          >
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div className="px-4 py-4 space-y-3">
          {/* Filename */}
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-1 block">
              Filename
            </label>
            <input
              type="text"
              value={filename}
              onChange={(e) => setFilename(e.target.value)}
              className="w-full px-3 py-1.5 text-sm rounded-md border border-border bg-background text-foreground"
              placeholder="document.md"
            />
          </div>

          {/* Display Name */}
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-1 block">
              Display Name (optional)
            </label>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="w-full px-3 py-1.5 text-sm rounded-md border border-border bg-background text-foreground"
              placeholder="Human-readable label"
            />
          </div>

          {/* Folder Picker */}
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-1 block">
              <Folder size={12} className="inline mr-1 -mt-0.5" />
              Folder
            </label>
            <select
              value={folderId ?? ''}
              onChange={(e) => {
                const val = e.target.value
                setFolderId(val ? Number(val) : undefined)
              }}
              className="w-full px-3 py-1.5 text-sm rounded-md border border-border bg-background text-foreground"
            >
              <option value="">Root</option>
              {flatFolders.map((item) => (
                <option
                  key={item.id}
                  value={item.id}
                  style={{ paddingLeft: `${8 + item.depth * 16}px` }}
                >
                  {'  '.repeat(item.depth)}{item.name}
                </option>
              ))}
            </select>
          </div>

          {/* Tags */}
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-1 block">
              Tags (optional)
            </label>
            <input
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              className="w-full px-3 py-1.5 text-sm rounded-md border border-border bg-background text-foreground"
              placeholder="comma-separated tags"
            />
          </div>

          {/* Error */}
          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2 px-4 py-3 border-t border-border">
          <button
            onClick={onClose}
            disabled={isSaving}
            className="px-3 py-1.5 text-sm rounded-md border border-border text-muted-foreground hover:text-foreground disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving || !filename.trim()}
            className="px-3 py-1.5 text-sm rounded-md bg-primary text-primary-foreground hover:opacity-90 disabled:opacity-50 flex items-center gap-1"
          >
            {isSaving ? (
              <>
                <Loader2 size={14} className="animate-spin" />
                Saving...
              </>
            ) : (
              'Save'
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
