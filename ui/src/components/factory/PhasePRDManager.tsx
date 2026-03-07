/**
 * PhasePRDManager - Phase PRD document management component.
 *
 * Renders numbered pills for each phase that light up based on active phase,
 * supports drag-and-drop file upload, and provides an inline editor for
 * viewing/editing phase PRD content with token estimates.
 *
 * Designed for the FactoryPanel as a compact, self-contained section.
 * Uses semantic Tailwind tokens for theme compatibility.
 */

import { useState, useRef, useCallback, useEffect } from 'react'
import {
  Upload,
  FileText,
  Plus,
  X,
  Save,
  Loader2,
  Trash2,
} from 'lucide-react'
import {
  usePhaseDocuments,
  usePhaseDocument,
  useUpdatePhaseDocument,
  useDeletePhaseDocument,
  useUploadPhaseDocuments,
} from '../../hooks/useFactory'

/** Shape of a single phase document from the list endpoint. */
interface PhaseDocumentEntry {
  phase: number
  filename: string
  size: number
  preview: string
}

interface PhasePRDManagerProps {
  projectName: string | null
  currentPhase?: number
}

/**
 * Returns theme-aware pill classes based on phase status relative to
 * the current active phase. Active phase gets a highlighted ring,
 * completed phases are green, future phases are muted.
 */
function getPillClasses(phase: number, currentPhase: number, hasDocument: boolean): string {
  const base = 'w-7 h-7 rounded-md border text-xs font-bold flex items-center justify-center transition-all cursor-pointer'

  if (phase === currentPhase) {
    return `${base} bg-blue-500/20 text-blue-600 dark:text-blue-400 border-blue-500/40 ring-1 ring-blue-500/30 scale-110`
  }
  if (hasDocument && phase < currentPhase) {
    return `${base} bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30`
  }
  if (hasDocument) {
    return `${base} bg-muted/60 text-foreground border-border hover:bg-muted`
  }
  return `${base} bg-muted/20 text-muted-foreground/50 border-border/50 border-dashed hover:border-border`
}

export function PhasePRDManager({ projectName, currentPhase = 0 }: PhasePRDManagerProps): React.JSX.Element {
  const [editingPhase, setEditingPhase] = useState<number | null>(null)
  const [editContent, setEditContent] = useState('')
  const [showUpload, setShowUpload] = useState(false)
  const [isDragOver, setIsDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const { data: docsData } = usePhaseDocuments(projectName)
  const { data: docDetail } = usePhaseDocument(projectName, editingPhase)
  const updateDoc = useUpdatePhaseDocument(projectName)
  const deleteDoc = useDeletePhaseDocument(projectName)
  const uploadDocs = useUploadPhaseDocuments(projectName)

  const documents = (
    (docsData?.data as Record<string, unknown> | undefined)?.documents as PhaseDocumentEntry[] | undefined
  ) ?? []

  // Sync editor content when the detail query resolves
  useEffect(() => {
    if (docDetail?.data) {
      const data = docDetail.data as Record<string, unknown>
      setEditContent(typeof data.content === 'string' ? data.content : '')
    }
  }, [docDetail])

  const handleFileUpload = useCallback(async (files: FileList | null) => {
    if (!files || files.length === 0) return
    const fileArray = Array.from(files).filter(
      f => f.name.endsWith('.md') || f.name.endsWith('.txt'),
    )
    if (fileArray.length === 0) return
    await uploadDocs.mutateAsync(fileArray)
    setShowUpload(false)
  }, [uploadDocs])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    handleFileUpload(e.dataTransfer.files)
  }, [handleFileUpload])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback(() => {
    setIsDragOver(false)
  }, [])

  const handleEditClick = (phase: number) => {
    if (editingPhase === phase) {
      // Toggle off
      setEditingPhase(null)
      setEditContent('')
    } else {
      setEditingPhase(phase)
    }
  }

  const handleSave = async () => {
    if (editingPhase === null) return
    await updateDoc.mutateAsync({ phaseNum: editingPhase, content: editContent })
    setEditingPhase(null)
    setEditContent('')
  }

  const handleDelete = async () => {
    if (editingPhase === null) return
    await deleteDoc.mutateAsync(editingPhase)
    setEditingPhase(null)
    setEditContent('')
  }

  // Generate pill range: show all existing phases + one extra slot
  const maxPhase = documents.length > 0
    ? Math.max(...documents.map(d => d.phase))
    : 0
  const pillNumbers = Array.from(
    { length: Math.max(maxPhase, 1) },
    (_, i) => i + 1,
  )

  return (
    <div className="space-y-2">
      {/* Phase Pills Row */}
      <div className="flex items-center gap-1.5 flex-wrap">
        <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mr-1">
          Phases:
        </span>

        {pillNumbers.map(num => {
          const doc = documents.find(d => d.phase === num)
          return (
            <button
              key={num}
              onClick={() => handleEditClick(num)}
              className={getPillClasses(num, currentPhase, !!doc)}
              title={
                doc
                  ? `Phase ${num} -- ${doc.size.toLocaleString()} chars`
                  : `Phase ${num} -- no document`
              }
            >
              {num}
            </button>
          )
        })}

        {/* Add / Upload button */}
        <button
          onClick={() => setShowUpload(!showUpload)}
          className="w-7 h-7 rounded-md border border-dashed border-border text-muted-foreground hover:text-foreground hover:border-foreground/30 text-xs font-bold flex items-center justify-center transition-all"
          title="Upload phase PRDs"
        >
          <Plus className="w-3.5 h-3.5" />
        </button>

        {documents.length > 0 && (
          <span className="text-[10px] text-muted-foreground ml-2">
            {documents.length} PRD{documents.length !== 1 ? 's' : ''} loaded
          </span>
        )}
      </div>

      {/* Upload Zone (toggles with + button) */}
      {showUpload && (
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          className={`border-2 border-dashed rounded-lg p-4 text-center transition-colors ${
            isDragOver
              ? 'border-primary bg-primary/5'
              : 'border-border bg-muted/20 hover:border-foreground/20'
          }`}
        >
          <Upload className="w-6 h-6 mx-auto mb-2 text-muted-foreground" />
          <p className="text-xs text-muted-foreground mb-1">
            Drag & drop .md files, or click to browse
          </p>
          <p className="text-[10px] text-muted-foreground/60 mb-3">
            Name files with numbers (1.md, 2.md...) for auto-ordering
          </p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".md,.txt"
            multiple
            className="hidden"
            onChange={e => handleFileUpload(e.target.files)}
          />
          <div className="flex gap-2 justify-center">
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploadDocs.isPending}
              className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium bg-primary text-primary-foreground rounded hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {uploadDocs.isPending ? (
                <>
                  <Loader2 className="w-3 h-3 animate-spin" />
                  Uploading...
                </>
              ) : (
                'Browse Files'
              )}
            </button>
            <button
              onClick={() => setShowUpload(false)}
              className="px-3 py-1.5 text-xs text-muted-foreground border border-border rounded hover:bg-muted/50 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Inline Editor (opens when a pill is clicked) */}
      {editingPhase !== null && (
        <div className="border border-border rounded-lg bg-card overflow-hidden">
          {/* Editor header */}
          <div className="flex items-center justify-between px-3 py-2 bg-muted/30 border-b border-border">
            <div className="flex items-center gap-2">
              <FileText className="w-3.5 h-3.5 text-primary" />
              <span className="text-xs font-bold text-foreground">
                Phase {editingPhase} PRD
              </span>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={handleDelete}
                disabled={deleteDoc.isPending}
                className="p-1 text-muted-foreground hover:text-destructive rounded hover:bg-destructive/10 transition-colors"
                title="Delete this phase document"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={handleSave}
                disabled={updateDoc.isPending}
                className="flex items-center gap-1 px-2 py-1 text-[11px] font-medium bg-primary text-primary-foreground rounded hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                {updateDoc.isPending ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  <Save className="w-3 h-3" />
                )}
                Save
              </button>
              <button
                onClick={() => {
                  setEditingPhase(null)
                  setEditContent('')
                }}
                className="p-1 text-muted-foreground hover:text-foreground rounded hover:bg-muted/50 transition-colors"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Textarea */}
          <textarea
            value={editContent}
            onChange={e => setEditContent(e.target.value)}
            rows={10}
            className="w-full bg-card p-3 text-xs text-foreground font-mono resize-y focus:outline-none border-0"
            placeholder="Write or paste your phase PRD here..."
          />

          {/* Token estimate footer */}
          <div className="px-3 py-1.5 bg-muted/20 border-t border-border text-[10px] text-muted-foreground">
            {editContent.length.toLocaleString()} chars
            {' -- '}
            ~{Math.ceil(editContent.length / 4).toLocaleString()} tokens
          </div>
        </div>
      )}
    </div>
  )
}
