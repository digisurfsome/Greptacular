/**
 * FileUploadModal
 *
 * Modal for uploading files or pasting text content into the workspace library.
 * Supports drag-and-drop, file picker, and direct text paste modes.
 */

import { useState, useCallback, useRef } from 'react'
import { X, Upload, Loader2 } from 'lucide-react'
import { useUploadFile, useUploadText, useFolderTree } from '@/hooks/useWorkspaceLibrary'
import { Button } from '@/components/ui/button'
import type { LibraryFolder } from '@/lib/types'

interface FileUploadModalProps {
  open: boolean
  onClose: () => void
  conversationId: number | null
  mode: 'file' | 'text'
  /** Pre-select a folder when opening from within a folder. */
  defaultFolderId?: number | null
}

function flattenFolderTree(folders: LibraryFolder[], depth = 0): Array<{ id: number; name: string; depth: number }> {
  const result: Array<{ id: number; name: string; depth: number }> = []
  for (const f of folders) {
    result.push({ id: f.id, name: f.name, depth })
    if (f.children?.length) {
      result.push(...flattenFolderTree(f.children, depth + 1))
    }
  }
  return result
}

const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10MB

const ACCEPTED_EXTENSIONS = '.md,.txt,.py,.js,.ts,.tsx,.jsx,.json,.yaml,.yml,.xml,.html,.css,.scss,.less,.sql,.sh,.bash,.zsh,.env,.toml,.ini,.cfg,.conf,.csv,.rs,.go,.java,.kt,.swift,.c,.cpp,.h,.hpp,.rb,.php,.r,.lua,.zig'

function formatFileSize(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  if (bytes >= 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${bytes} B`
}

export function FileUploadModal({
  open,
  onClose,
  conversationId,
  mode,
  defaultFolderId = null,
}: FileUploadModalProps): React.JSX.Element | null {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [displayName, setDisplayName] = useState('')
  const [tags, setTags] = useState('')
  const [scope, setScope] = useState<'global' | 'chat'>('global')
  const [folderId, setFolderId] = useState<number | null>(defaultFolderId)
  const [error, setError] = useState('')
  const [isDragging, setIsDragging] = useState(false)
  // Text mode state
  const [textFilename, setTextFilename] = useState('untitled.md')
  const [textContent, setTextContent] = useState('')

  const fileInputRef = useRef<HTMLInputElement>(null)
  const uploadFile = useUploadFile()
  const uploadText = useUploadText()
  const { data: folderTree = [] } = useFolderTree()
  const flatFolders = flattenFolderTree(folderTree)

  const isUploading = uploadFile.isPending || uploadText.isPending

  const handleFileSelect = useCallback((file: File) => {
    setError('')
    if (file.size > MAX_FILE_SIZE) {
      setError(`File too large (${formatFileSize(file.size)}). Maximum size is 10 MB.`)
      return
    }
    setSelectedFile(file)
    if (!displayName) {
      setDisplayName(file.name)
    }
  }, [displayName])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFileSelect(file)
  }, [handleFileSelect])

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFileSelect(file)
  }, [handleFileSelect])

  const handleSubmit = useCallback(async () => {
    setError('')
    const scopeConversationId = scope === 'chat' ? (conversationId ?? undefined) : undefined

    try {
      if (mode === 'file') {
        if (!selectedFile) return
        await uploadFile.mutateAsync({
          file: selectedFile,
          conversationId: scopeConversationId,
          displayName: displayName || undefined,
          tags: tags || undefined,
          folderId: folderId ?? undefined,
        })
      } else {
        if (!textContent.trim()) {
          setError('Content is required')
          return
        }
        await uploadText.mutateAsync({
          filename: textFilename || 'untitled.txt',
          content: textContent,
          conversationId: scopeConversationId,
          displayName: displayName || textFilename || undefined,
          tags: tags || undefined,
          folderId: folderId ?? undefined,
        })
      }
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    }
  }, [mode, selectedFile, textFilename, textContent, displayName, tags, scope, folderId, conversationId, uploadFile, uploadText, onClose])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-card border border-border rounded-lg shadow-lg p-6 max-w-md w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-semibold text-foreground">
            {mode === 'file' ? 'Upload File' : 'Paste Content'}
          </h3>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X size={18} />
          </button>
        </div>

        {mode === 'file' ? (
          <>
            {/* Drop zone */}
            <div
              className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                isDragging
                  ? 'border-primary bg-muted/50'
                  : 'border-border hover:border-primary hover:bg-muted/30'
              }`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload size={24} className="mx-auto text-muted-foreground mb-2" />
              {selectedFile ? (
                <div>
                  <p className="text-sm font-medium text-foreground">{selectedFile.name}</p>
                  <p className="text-xs text-muted-foreground">{formatFileSize(selectedFile.size)}</p>
                </div>
              ) : (
                <div>
                  <p className="text-sm text-muted-foreground">Drag and drop a file here</p>
                  <p className="text-xs text-muted-foreground mt-1">or click to browse</p>
                </div>
              )}
              <input
                ref={fileInputRef}
                type="file"
                accept={ACCEPTED_EXTENSIONS}
                onChange={handleInputChange}
                className="hidden"
              />
            </div>
          </>
        ) : (
          <>
            {/* Text mode */}
            <div className="space-y-3">
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">Filename</label>
                <input
                  type="text"
                  value={textFilename}
                  onChange={(e) => setTextFilename(e.target.value)}
                  className="w-full bg-background border border-input rounded-md px-3 py-2 text-sm text-foreground"
                  placeholder="my-notes.md"
                />
              </div>
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">Content</label>
                <textarea
                  value={textContent}
                  onChange={(e) => setTextContent(e.target.value)}
                  className="w-full bg-background border border-input rounded-md px-3 py-2 text-sm text-foreground min-h-[120px] resize-y font-mono"
                  placeholder="Paste your content here..."
                />
              </div>
            </div>
          </>
        )}

        {/* Shared fields */}
        <div className="space-y-3 mt-4">
          <div>
            <label className="text-xs text-muted-foreground mb-1 block">Display Name</label>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="w-full bg-background border border-input rounded-md px-3 py-2 text-sm text-foreground"
              placeholder="Optional display name"
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground mb-1 block">Tags</label>
            <input
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              className="w-full bg-background border border-input rounded-md px-3 py-2 text-sm text-foreground"
              placeholder="comma-separated tags"
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground mb-1 block">Folder</label>
            <select
              value={folderId ?? ''}
              onChange={(e) => setFolderId(e.target.value ? Number(e.target.value) : null)}
              className="w-full bg-background border border-input rounded-md px-3 py-2 text-sm text-foreground"
            >
              <option value="">Root</option>
              {flatFolders.map((f) => (
                <option key={f.id} value={f.id} style={{ paddingLeft: `${8 + f.depth * 16}px` }}>
                  {'  '.repeat(f.depth)}{f.depth > 0 ? '└ ' : ''}{f.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-muted-foreground mb-1 block">Scope</label>
            <div className="flex gap-4">
              <label className="flex items-center gap-1.5 text-sm text-foreground">
                <input
                  type="radio"
                  name="scope"
                  checked={scope === 'global'}
                  onChange={() => setScope('global')}
                />
                Global
              </label>
              <label className={`flex items-center gap-1.5 text-sm ${conversationId ? 'text-foreground' : 'text-muted-foreground'}`}>
                <input
                  type="radio"
                  name="scope"
                  checked={scope === 'chat'}
                  onChange={() => setScope('chat')}
                  disabled={!conversationId}
                />
                This Chat
              </label>
            </div>
          </div>
        </div>

        {/* Error */}
        {error && (
          <p className="text-sm text-destructive mt-3">{error}</p>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-2 mt-4">
          <Button variant="outline" onClick={onClose} disabled={isUploading}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isUploading || (mode === 'file' && !selectedFile) || (mode === 'text' && !textContent.trim())}
          >
            {isUploading ? (
              <>
                <Loader2 size={14} className="animate-spin mr-1" />
                {mode === 'file' ? 'Uploading...' : 'Saving...'}
              </>
            ) : (
              mode === 'file' ? 'Upload' : 'Save'
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}
