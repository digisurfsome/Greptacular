/**
 * LibraryPickerModal
 *
 * Modal dialog for browsing the workspace library filesystem and selecting
 * files to attach to a single chat message. Supports folder navigation via
 * breadcrumb and multi-select with checkboxes.
 */

import { useState, useCallback, useEffect, useMemo } from 'react'
import { Folder, Home, ChevronRight, Check, X, Paperclip } from 'lucide-react'
import { useFolderContents, useFolderBreadcrumb } from '@/hooks/useWorkspaceLibrary'
import { Button } from '@/components/ui/button'
import type { LibraryFile } from '@/lib/types'

interface LibraryPickerModalProps {
  open: boolean
  onClose: () => void
  onAttach: (files: LibraryFile[]) => void
  /** IDs of files that are already selected (for re-opening the picker). */
  selectedFileIds?: number[]
}

const TYPE_COLORS: Record<string, string> = {
  doc: 'bg-blue-500/10 text-blue-500',
  code: 'bg-green-500/10 text-green-500',
  spec: 'bg-purple-500/10 text-purple-500',
  template: 'bg-orange-500/10 text-orange-500',
  upload: 'bg-muted text-muted-foreground',
}

/** Format byte sizes into compact human-readable strings. */
function formatSize(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)}M`
  if (bytes >= 1024) return `${(bytes / 1024).toFixed(0)}K`
  return `${bytes}B`
}

export function LibraryPickerModal({
  open,
  onClose,
  onAttach,
  selectedFileIds,
}: LibraryPickerModalProps): React.JSX.Element | null {
  const [currentFolderId, setCurrentFolderId] = useState<number | null>(null)
  const [selectedFiles, setSelectedFiles] = useState<Map<number, LibraryFile>>(new Map())

  // Load folder contents and breadcrumb for the current folder
  const { data: folderContents } = useFolderContents(currentFolderId)
  const { data: breadcrumb = [] } = useFolderBreadcrumb(currentFolderId)

  // Initialize selection from the selectedFileIds prop when the modal opens.
  // We match against files visible in the current folder contents so that
  // the Map always contains full LibraryFile objects.
  useEffect(() => {
    if (!open) return

    if (!selectedFileIds || selectedFileIds.length === 0) {
      setSelectedFiles(new Map())
      return
    }

    // Build the initial map from any files we can find in the current folder
    if (folderContents?.files) {
      const idSet = new Set(selectedFileIds)
      const initial = new Map<number, LibraryFile>()
      for (const file of folderContents.files) {
        if (idSet.has(file.id)) {
          initial.set(file.id, file)
        }
      }
      // Only set once on open (keep user's changes after that)
      setSelectedFiles((prev) => {
        if (prev.size === 0 && initial.size > 0) return initial
        return prev
      })
    }
  }, [open, selectedFileIds, folderContents?.files])

  // Reset folder navigation when the modal closes
  useEffect(() => {
    if (!open) {
      setCurrentFolderId(null)
      setSelectedFiles(new Map())
    }
  }, [open])

  const toggleFileSelection = useCallback((file: LibraryFile) => {
    setSelectedFiles((prev) => {
      const next = new Map(prev)
      if (next.has(file.id)) {
        next.delete(file.id)
      } else {
        next.set(file.id, file)
      }
      return next
    })
  }, [])

  const handleAttach = useCallback(() => {
    onAttach(Array.from(selectedFiles.values()))
    onClose()
  }, [selectedFiles, onAttach, onClose])

  // Handle Escape key to close the modal
  useEffect(() => {
    if (!open) return

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        onClose()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [open, onClose])

  const folders = useMemo(() => folderContents?.folders ?? [], [folderContents])
  const files = useMemo(() => folderContents?.files ?? [], [folderContents])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-card border border-border rounded-lg shadow-lg max-w-lg w-full mx-4 max-h-[80vh] flex flex-col">
        {/* Title bar */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <div className="flex items-center gap-2">
            <Paperclip size={16} className="text-primary" />
            <h3 className="text-sm font-semibold text-foreground">Attach Files</h3>
            {selectedFiles.size > 0 && (
              <span className="bg-primary/10 text-primary text-xs font-medium px-1.5 py-0.5 rounded-full">
                {selectedFiles.size}
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Breadcrumb bar */}
        <div className="flex items-center gap-1 px-4 py-2 border-b border-border overflow-x-auto">
          <button
            onClick={() => setCurrentFolderId(null)}
            className={`flex-shrink-0 ${
              currentFolderId === null
                ? 'text-foreground font-medium'
                : 'text-muted-foreground hover:text-foreground cursor-pointer'
            } text-xs transition-colors`}
          >
            <Home size={14} />
          </button>
          {breadcrumb.map((crumb) => (
            <div key={crumb.id} className="flex items-center gap-1 flex-shrink-0">
              <ChevronRight size={12} className="text-muted-foreground" />
              <button
                onClick={() => setCurrentFolderId(crumb.id)}
                className={`text-xs transition-colors ${
                  crumb.id === currentFolderId
                    ? 'text-foreground font-medium'
                    : 'text-muted-foreground hover:text-foreground cursor-pointer'
                }`}
              >
                {crumb.name}
              </button>
            </div>
          ))}
        </div>

        {/* Content area */}
        <div className="flex-1 overflow-y-auto max-h-[60vh]">
          {folders.length === 0 && files.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 gap-2 text-muted-foreground">
              <Folder size={24} strokeWidth={1.5} />
              <span className="text-sm">This folder is empty</span>
            </div>
          ) : (
            <>
              {/* Folders */}
              {folders.map((folder) => (
                <button
                  key={`folder-${folder.id}`}
                  type="button"
                  onClick={() => setCurrentFolderId(folder.id)}
                  className="w-full flex items-center gap-2 px-3 py-2 hover:bg-muted/50 cursor-pointer text-sm transition-colors"
                >
                  <Folder size={16} className="text-muted-foreground flex-shrink-0" />
                  <span className="text-foreground truncate">{folder.name}</span>
                </button>
              ))}

              {/* Files */}
              {files.map((file) => {
                const isSelected = selectedFiles.has(file.id)
                return (
                  <button
                    key={`file-${file.id}`}
                    type="button"
                    onClick={() => toggleFileSelection(file)}
                    className={`w-full flex items-center gap-2 px-3 py-2 hover:bg-muted/50 cursor-pointer text-sm transition-colors ${
                      isSelected ? 'bg-primary/5' : ''
                    }`}
                  >
                    {/* Checkbox */}
                    <div
                      className={`w-4 h-4 rounded border flex items-center justify-center flex-shrink-0 transition-colors ${
                        isSelected
                          ? 'bg-primary border-primary'
                          : 'border-border'
                      }`}
                    >
                      {isSelected && <Check size={12} className="text-primary-foreground" />}
                    </div>

                    {/* Type badge */}
                    <span
                      className={`px-1 py-0.5 rounded text-[10px] font-medium flex-shrink-0 ${
                        TYPE_COLORS[file.file_type] || TYPE_COLORS.upload
                      }`}
                    >
                      {file.file_type}
                    </span>

                    {/* File name */}
                    <span className="text-foreground truncate flex-1 text-left">
                      {file.display_name || file.filename}
                    </span>

                    {/* File size */}
                    <span className="text-xs text-muted-foreground flex-shrink-0">
                      {formatSize(file.file_size)}
                    </span>
                  </button>
                )
              })}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 px-4 py-3 border-t border-border">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleAttach} disabled={selectedFiles.size === 0}>
            <Paperclip size={14} />
            Attach {selectedFiles.size > 0 ? `${selectedFiles.size} file${selectedFiles.size === 1 ? '' : 's'}` : 'files'}
          </Button>
        </div>
      </div>
    </div>
  )
}
