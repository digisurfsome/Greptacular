/**
 * LibraryFolderBrowser
 *
 * Compact folder browser for the workspace library panel (w-72 / 288px).
 * Replaces the flat file list with a Google Drive-style navigable folder
 * structure. Shows breadcrumbs, folders first (alphabetical), then files
 * (newest first), with inline rename, new-folder creation, and context
 * menu actions on hover.
 */

import { useState, useCallback, useRef, useEffect, useMemo } from 'react'
import {
  Folder,
  FolderOpen,
  ChevronRight,
  MoreHorizontal,
  Pencil,
  Trash2,
  Eye,
  FolderPlus,
  Home,
  Loader2,
  Check,
} from 'lucide-react'
import {
  useFolderContents,
  useFolderBreadcrumb,
  useCreateFolder,
  useRenameFolder,
  useDeleteFolder,
  useDeleteFile,
} from '@/hooks/useWorkspaceLibrary'
import type { LibraryFile, LibraryFolder } from '@/lib/types'

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface LibraryFolderBrowserProps {
  currentFolderId: number | null
  onNavigateToFolder: (folderId: number | null) => void
  onPreviewFile: (file: LibraryFile) => void
  onDeleteFile: (fileId: number) => void
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const TYPE_COLORS: Record<string, string> = {
  doc: 'bg-blue-500/10 text-blue-500',
  code: 'bg-green-500/10 text-green-500',
  spec: 'bg-purple-500/10 text-purple-500',
  template: 'bg-orange-500/10 text-orange-500',
  upload: 'bg-muted text-muted-foreground',
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Format file size into a compact human-readable string. */
function formatSize(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)}M`
  if (bytes >= 1024) return `${(bytes / 1024).toFixed(0)}K`
  return `${bytes}B`
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function LibraryFolderBrowser({
  currentFolderId,
  onNavigateToFolder,
  onPreviewFile,
  onDeleteFile,
}: LibraryFolderBrowserProps): React.JSX.Element {
  // ---- Data hooks --------------------------------------------------------

  const { data: contents, isLoading } = useFolderContents(currentFolderId)
  const { data: breadcrumb = [] } = useFolderBreadcrumb(currentFolderId)

  const createFolderMut = useCreateFolder()
  const renameFolderMut = useRenameFolder()
  const deleteFolderMut = useDeleteFolder()
  const deleteFileMut = useDeleteFile()

  // ---- Local state -------------------------------------------------------

  // Inline new-folder creation
  const [isCreatingFolder, setIsCreatingFolder] = useState(false)
  const [newFolderName, setNewFolderName] = useState('')
  const newFolderInputRef = useRef<HTMLInputElement>(null)

  // Inline rename (folder only)
  const [renamingFolderId, setRenamingFolderId] = useState<number | null>(null)
  const [renameValue, setRenameValue] = useState('')
  const renameInputRef = useRef<HTMLInputElement>(null)

  // Context menu visibility
  const [openMenuId, setOpenMenuId] = useState<string | null>(null)

  // ---- Derived data ------------------------------------------------------

  const folders = useMemo(() => {
    if (!contents?.folders) return []
    return [...contents.folders].sort((a, b) => a.name.localeCompare(b.name))
  }, [contents?.folders])

  const files = useMemo(() => {
    if (!contents?.files) return []
    // Newest first — compare created_at timestamps in descending order
    return [...contents.files].sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    )
  }, [contents?.files])

  // ---- Effects -----------------------------------------------------------

  // Focus the new-folder input when it appears
  useEffect(() => {
    if (isCreatingFolder) {
      newFolderInputRef.current?.focus()
    }
  }, [isCreatingFolder])

  // Focus the rename input when it appears
  useEffect(() => {
    if (renamingFolderId !== null) {
      renameInputRef.current?.focus()
      renameInputRef.current?.select()
    }
  }, [renamingFolderId])

  // Close context menu on outside click
  useEffect(() => {
    if (!openMenuId) return
    const handler = (e: MouseEvent) => {
      // Close if clicking outside of any menu popover
      const target = e.target as HTMLElement
      if (!target.closest('[data-menu-popover]')) {
        setOpenMenuId(null)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [openMenuId])

  // ---- Handlers ----------------------------------------------------------

  const handleCreateFolder = useCallback(() => {
    const trimmed = newFolderName.trim()
    if (!trimmed) {
      setIsCreatingFolder(false)
      setNewFolderName('')
      return
    }
    createFolderMut.mutate(
      { name: trimmed, parentId: currentFolderId ?? undefined },
      {
        onSuccess: () => {
          setIsCreatingFolder(false)
          setNewFolderName('')
        },
      },
    )
  }, [newFolderName, currentFolderId, createFolderMut])

  const handleRenameFolder = useCallback(
    (folderId: number) => {
      const trimmed = renameValue.trim()
      if (!trimmed) {
        setRenamingFolderId(null)
        setRenameValue('')
        return
      }
      renameFolderMut.mutate(
        { folderId, name: trimmed },
        {
          onSuccess: () => {
            setRenamingFolderId(null)
            setRenameValue('')
          },
        },
      )
    },
    [renameValue, renameFolderMut],
  )

  const handleDeleteFolder = useCallback(
    (folderId: number) => {
      if (window.confirm('Delete this folder and all its contents?')) {
        deleteFolderMut.mutate(folderId)
        setOpenMenuId(null)
      }
    },
    [deleteFolderMut],
  )

  const handleDeleteFile = useCallback(
    (fileId: number) => {
      if (window.confirm('Delete this file from the library?')) {
        deleteFileMut.mutate(fileId)
        onDeleteFile(fileId)
      }
    },
    [deleteFileMut, onDeleteFile],
  )

  const startRename = useCallback((folder: LibraryFolder) => {
    setRenamingFolderId(folder.id)
    setRenameValue(folder.name)
    setOpenMenuId(null)
  }, [])

  const toggleMenu = useCallback(
    (menuId: string) => {
      setOpenMenuId(prev => (prev === menuId ? null : menuId))
    },
    [],
  )

  // ---- Render helpers ----------------------------------------------------

  const isEmpty = !isLoading && folders.length === 0 && files.length === 0 && !isCreatingFolder

  return (
    <div className="flex flex-col h-full">
      {/* Breadcrumb bar + new-folder button */}
      <div className="flex items-center gap-1 px-2 py-1.5 border-b border-border min-h-[32px]">
        <div className="flex-1 flex items-center gap-0.5 min-w-0 overflow-x-auto text-xs">
          {/* Root crumb */}
          <button
            onClick={() => onNavigateToFolder(null)}
            className={`flex-shrink-0 p-0.5 rounded hover:bg-muted/50 transition-colors ${
              currentFolderId === null
                ? 'text-foreground'
                : 'text-muted-foreground hover:text-foreground'
            }`}
            title="Root"
          >
            <Home size={13} />
          </button>

          {/* Intermediate crumbs */}
          {breadcrumb.map((crumb) => (
            <span key={crumb.id} className="flex items-center gap-0.5 flex-shrink-0 min-w-0">
              <ChevronRight size={10} className="text-muted-foreground flex-shrink-0" />
              <button
                onClick={() => onNavigateToFolder(crumb.id)}
                className={`truncate max-w-[80px] px-1 py-0.5 rounded hover:bg-muted/50 transition-colors ${
                  crumb.id === currentFolderId
                    ? 'text-foreground font-medium'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
                title={crumb.name}
              >
                {crumb.name}
              </button>
            </span>
          ))}
        </div>

        {/* New folder button */}
        <button
          onClick={() => {
            setIsCreatingFolder(true)
            setNewFolderName('')
          }}
          className="flex-shrink-0 p-1 rounded text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
          title="New folder"
        >
          <FolderPlus size={14} />
        </button>
      </div>

      {/* Content area */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 size={16} className="animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="py-0.5">
            {/* Inline new-folder input */}
            {isCreatingFolder && (
              <div className="flex items-center gap-1.5 px-2 py-1.5">
                <FolderOpen size={14} className="text-muted-foreground flex-shrink-0" />
                <input
                  ref={newFolderInputRef}
                  type="text"
                  value={newFolderName}
                  onChange={(e) => setNewFolderName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleCreateFolder()
                    if (e.key === 'Escape') {
                      setIsCreatingFolder(false)
                      setNewFolderName('')
                    }
                  }}
                  onBlur={handleCreateFolder}
                  placeholder="Folder name..."
                  className="flex-1 min-w-0 bg-muted/50 border border-border rounded px-1.5 py-0.5 text-xs text-foreground placeholder:text-muted-foreground outline-none focus:border-primary"
                  disabled={createFolderMut.isPending}
                />
                {createFolderMut.isPending && (
                  <Loader2 size={12} className="animate-spin text-muted-foreground flex-shrink-0" />
                )}
              </div>
            )}

            {/* Folders */}
            {folders.map((folder) => {
              const isRenaming = renamingFolderId === folder.id
              const menuId = `folder-${folder.id}`
              const isMenuOpen = openMenuId === menuId

              return (
                <div
                  key={folder.id}
                  className="group flex items-center gap-1.5 px-2 py-1.5 hover:bg-muted/50 cursor-pointer"
                >
                  {/* Folder icon */}
                  <Folder size={14} className="text-muted-foreground flex-shrink-0" />

                  {/* Name or inline rename input */}
                  {isRenaming ? (
                    <div className="flex-1 flex items-center gap-1 min-w-0">
                      <input
                        ref={renameInputRef}
                        type="text"
                        value={renameValue}
                        onChange={(e) => setRenameValue(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleRenameFolder(folder.id)
                          if (e.key === 'Escape') {
                            setRenamingFolderId(null)
                            setRenameValue('')
                          }
                        }}
                        onBlur={() => handleRenameFolder(folder.id)}
                        className="flex-1 min-w-0 bg-muted/50 border border-border rounded px-1.5 py-0.5 text-xs text-foreground outline-none focus:border-primary"
                        disabled={renameFolderMut.isPending}
                      />
                      {renameFolderMut.isPending ? (
                        <Loader2 size={12} className="animate-spin text-muted-foreground flex-shrink-0" />
                      ) : (
                        <button
                          onClick={() => handleRenameFolder(folder.id)}
                          className="p-0.5 text-muted-foreground hover:text-foreground"
                        >
                          <Check size={12} />
                        </button>
                      )}
                    </div>
                  ) : (
                    <span
                      className="flex-1 text-xs text-foreground truncate"
                      onClick={() => onNavigateToFolder(folder.id)}
                    >
                      {folder.name}
                    </span>
                  )}

                  {/* Context menu trigger (visible on hover, or when menu is open) */}
                  {!isRenaming && (
                    <div className="relative flex-shrink-0">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          toggleMenu(menuId)
                        }}
                        className={`p-0.5 rounded text-muted-foreground hover:text-foreground transition-opacity ${
                          isMenuOpen ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
                        }`}
                      >
                        <MoreHorizontal size={14} />
                      </button>

                      {/* Dropdown menu */}
                      {isMenuOpen && (
                        <div
                          data-menu-popover
                          className="absolute right-0 top-full mt-1 z-20 bg-card border border-border rounded-md shadow-md py-1 min-w-[120px]"
                        >
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              startRename(folder)
                            }}
                            className="flex items-center gap-2 w-full px-3 py-1.5 text-xs text-foreground hover:bg-muted/50"
                          >
                            <Pencil size={12} />
                            Rename
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleDeleteFolder(folder.id)
                            }}
                            className="flex items-center gap-2 w-full px-3 py-1.5 text-xs text-destructive hover:bg-muted/50"
                          >
                            <Trash2 size={12} />
                            Delete
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            })}

            {/* Files */}
            {files.map((file) => (
              <div
                key={file.id}
                className="group flex items-center gap-1.5 px-2 py-1.5 hover:bg-muted/50"
              >
                {/* Type badge */}
                <span
                  className={`flex-shrink-0 px-1 py-0.5 rounded text-[10px] font-medium leading-none ${
                    TYPE_COLORS[file.file_type] || TYPE_COLORS.upload
                  }`}
                >
                  {file.file_type}
                </span>

                {/* File info — single line: name + size */}
                <div className="flex-1 min-w-0 flex items-center gap-1.5">
                  <span className="text-xs text-foreground truncate">
                    {file.display_name || file.filename}
                  </span>
                  <span className="flex-shrink-0 text-[10px] text-muted-foreground/60">
                    {formatSize(file.file_size)}
                  </span>
                </div>

                {/* Hover actions: Preview + Delete */}
                <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 flex-shrink-0 transition-opacity">
                  <button
                    onClick={() => onPreviewFile(file)}
                    className="p-1 rounded text-muted-foreground hover:text-foreground"
                    title="Preview"
                  >
                    <Eye size={12} />
                  </button>
                  <button
                    onClick={() => handleDeleteFile(file.id)}
                    className="p-1 rounded text-muted-foreground hover:text-destructive"
                    title="Delete"
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              </div>
            ))}

            {/* Empty state */}
            {isEmpty && (
              <div className="flex flex-col items-center justify-center py-8 gap-2 text-muted-foreground">
                <FolderOpen size={20} strokeWidth={1.5} />
                <span className="text-xs">Empty folder</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
