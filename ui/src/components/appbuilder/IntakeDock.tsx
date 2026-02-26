/**
 * IntakeDock Component
 *
 * File staging area for Agent OS project intake.
 * Users drag & drop files, tag them by category, and process them
 * to start the Agent OS PRD creation workflow.
 */

import { useCallback, useRef, useState } from 'react'
import {
  Upload,
  FileText,
  CheckCircle2,
  AlertCircle,
  Trash2,
  Play,
  ClipboardPaste,
  SkipForward,
  X,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import {
  useStagedFiles,
  useReadiness,
  useStageFile,
  useTagFile,
  useRemoveStagedFile,
  usePasteText,
  useProcessIntake,
} from '@/hooks/useAgentOS'

// ============================================================================
// Constants
// ============================================================================

const TAG_OPTIONS = [
  { value: 'standards', label: 'Standards', color: 'bg-blue-500' },
  { value: 'product', label: 'Product', color: 'bg-purple-500' },
  { value: 'spec', label: 'Spec', color: 'bg-green-500' },
  { value: 'reference', label: 'Reference', color: 'bg-amber-500' },
  { value: 'intake', label: 'Intake', color: 'bg-gray-500' },
] as const

const TAG_COLOR_MAP: Record<string, string> = {
  standards: 'bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-900/30 dark:text-blue-300',
  product: 'bg-purple-100 text-purple-800 border-purple-300 dark:bg-purple-900/30 dark:text-purple-300',
  spec: 'bg-green-100 text-green-800 border-green-300 dark:bg-green-900/30 dark:text-green-300',
  reference: 'bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-900/30 dark:text-amber-300',
  intake: 'bg-gray-100 text-gray-800 border-gray-300 dark:bg-gray-900/30 dark:text-gray-300',
}

// ============================================================================
// Component
// ============================================================================

interface IntakeDockProps {
  projectName: string
  onProcessComplete: () => void
  onSkip: () => void
}

export function IntakeDock({ projectName, onProcessComplete, onSkip }: IntakeDockProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [showPasteInput, setShowPasteInput] = useState(false)
  const [pasteFilename, setPasteFilename] = useState('')
  const [pasteContent, setPasteContent] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Queries
  const { data: stagedData } = useStagedFiles(projectName)
  const { data: readiness } = useReadiness(projectName)
  const files = stagedData?.files ?? []

  // Mutations
  const stageFile = useStageFile(projectName)
  const tagFile = useTagFile(projectName)
  const removeStagedFile = useRemoveStagedFile(projectName)
  const pasteText = usePasteText(projectName)
  const processIntake = useProcessIntake(projectName)

  // Drag & drop handlers
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    const droppedFiles = Array.from(e.dataTransfer.files)
    droppedFiles.forEach(file => {
      const formData = new FormData()
      formData.append('file', file)
      stageFile.mutate(formData)
    })
  }, [stageFile])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || [])
    selectedFiles.forEach(file => {
      const formData = new FormData()
      formData.append('file', file)
      stageFile.mutate(formData)
    })
    // Reset input
    if (fileInputRef.current) fileInputRef.current.value = ''
  }, [stageFile])

  const handlePasteSubmit = useCallback(() => {
    if (!pasteFilename.trim() || !pasteContent.trim()) return
    pasteText.mutate({ filename: pasteFilename.trim(), content: pasteContent })
    setPasteFilename('')
    setPasteContent('')
    setShowPasteInput(false)
  }, [pasteFilename, pasteContent, pasteText])

  const handleTagChange = useCallback((fileId: string, tag: string) => {
    tagFile.mutate({ fileId, tag })
  }, [tagFile])

  const handleProcess = useCallback(() => {
    processIntake.mutate(undefined, {
      onSuccess: () => onProcessComplete(),
    })
  }, [processIntake, onProcessComplete])

  const canProceed = readiness?.can_proceed ?? false

  return (
    <div className="flex flex-col gap-4 p-4 max-w-3xl mx-auto w-full">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-foreground tracking-tight">Project Intake Dock</h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Drop files, tag them by category, then process to start Agent OS
          </p>
        </div>
      </div>

      {/* Drop zone */}
      <Card
        className={`border-2 border-dashed transition-colors cursor-pointer ${
          isDragging
            ? 'border-primary bg-primary/5'
            : 'border-border hover:border-primary/50'
        }`}
        onClick={() => fileInputRef.current?.click()}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <CardContent className="flex flex-col items-center justify-center py-8 gap-2">
          <Upload size={28} className={isDragging ? 'text-primary' : 'text-muted-foreground'} />
          <span className="text-sm font-medium text-foreground">
            Drop files here or click to upload
          </span>
          <span className="text-xs text-muted-foreground">
            Supports: .md, .txt, .pdf, .docx, .png, .json
          </span>
          <Button
            variant="outline"
            size="sm"
            className="mt-2"
            onClick={(e) => {
              e.stopPropagation()
              setShowPasteInput(prev => !prev)
            }}
          >
            <ClipboardPaste size={14} />
            Paste from Clipboard
          </Button>
        </CardContent>
      </Card>

      <input
        ref={fileInputRef}
        type="file"
        multiple
        className="hidden"
        onChange={handleFileSelect}
        accept=".md,.txt,.pdf,.docx,.png,.json,.yaml,.yml"
      />

      {/* Paste input */}
      {showPasteInput && (
        <Card>
          <CardContent className="p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-bold text-foreground">Paste Content</span>
              <Button variant="ghost" size="sm" onClick={() => setShowPasteInput(false)}>
                <X size={14} />
              </Button>
            </div>
            <Input
              placeholder="Filename (e.g., my-ideas.md)"
              value={pasteFilename}
              onChange={e => setPasteFilename(e.target.value)}
            />
            <textarea
              className="w-full h-32 p-3 text-sm border-2 border-border rounded-lg bg-background text-foreground resize-none focus:outline-none focus:border-primary"
              placeholder="Paste your content here..."
              value={pasteContent}
              onChange={e => setPasteContent(e.target.value)}
            />
            <Button
              size="sm"
              onClick={handlePasteSubmit}
              disabled={!pasteFilename.trim() || !pasteContent.trim()}
            >
              Stage File
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Staged files list */}
      {files.length > 0 && (
        <Card>
          <CardContent className="p-0">
            <div className="px-4 py-2 border-b border-border">
              <span className="text-xs font-bold text-foreground uppercase tracking-wider">
                Staged Files ({files.length})
              </span>
            </div>
            <div className="divide-y divide-border">
              {files.map(file => (
                <div key={file.id} className="flex items-center gap-3 px-4 py-2.5">
                  {/* Icon + name */}
                  <FileText size={16} className="text-muted-foreground shrink-0" />
                  <div className="flex-1 min-w-0">
                    <span className="text-sm font-medium text-foreground truncate block">
                      {file.name}
                    </span>
                    <span className="text-[10px] text-muted-foreground">
                      {(file.size / 1024).toFixed(1)} KB
                    </span>
                  </div>

                  {/* Auto-tag suggestion */}
                  {!file.tag && file.auto_tag && (
                    <button
                      onClick={() => handleTagChange(file.id, file.auto_tag!)}
                      className="flex items-center gap-1"
                      title={`Accept suggestion: ${file.auto_tag}`}
                    >
                      <Badge variant="outline" className="text-[10px] border-dashed cursor-pointer hover:border-primary">
                        {file.auto_tag}?
                      </Badge>
                    </button>
                  )}

                  {/* Tag dropdown */}
                  <select
                    value={file.tag || ''}
                    onChange={e => handleTagChange(file.id, e.target.value)}
                    className="text-xs border border-border rounded px-2 py-1 bg-background text-foreground"
                  >
                    <option value="">Tag needed</option>
                    {TAG_OPTIONS.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>

                  {/* Tag badge */}
                  {file.tag && (
                    <Badge className={`text-[10px] ${TAG_COLOR_MAP[file.tag] || ''}`}>
                      {file.tag}
                    </Badge>
                  )}

                  {/* Processed indicator */}
                  {file.processed && (
                    <CheckCircle2 size={14} className="text-green-500 shrink-0" />
                  )}

                  {/* Delete */}
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0 text-muted-foreground hover:text-destructive"
                    onClick={() => removeStagedFile.mutate(file.id)}
                  >
                    <Trash2 size={14} />
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Readiness checklist */}
      {readiness && (
        <Card>
          <CardContent className="p-4">
            <span className="text-xs font-bold text-foreground uppercase tracking-wider">
              Readiness
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 mt-3">
              {(['standards', 'product', 'spec', 'reference', 'intake'] as const).map(cat => {
                const status = readiness[cat]
                if (!status) return null
                return (
                  <div
                    key={cat}
                    className={`flex flex-col items-center p-2 rounded-lg border ${
                      status.ready ? 'border-green-300 bg-green-50 dark:bg-green-900/10' : 'border-border'
                    }`}
                  >
                    {status.ready
                      ? <CheckCircle2 size={16} className="text-green-500" />
                      : <div className="w-4 h-4 rounded border-2 border-muted-foreground/30" />
                    }
                    <span className="text-[10px] font-bold mt-1 capitalize">{cat}</span>
                    <span className="text-[10px] text-muted-foreground">{status.count} file{status.count !== 1 ? 's' : ''}</span>
                  </div>
                )
              })}
            </div>

            {readiness.untagged > 0 && (
              <div className="flex items-center gap-1.5 mt-3 text-amber-600 dark:text-amber-400">
                <AlertCircle size={14} />
                <span className="text-xs font-medium">
                  {readiness.untagged} file{readiness.untagged !== 1 ? 's' : ''} need{readiness.untagged === 1 ? 's' : ''} a tag
                </span>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Action buttons */}
      <div className="flex items-center justify-between pt-2">
        <Button variant="outline" size="sm" onClick={onSkip}>
          <SkipForward size={14} />
          Skip — Start from Scratch
        </Button>

        <Button
          onClick={handleProcess}
          disabled={!canProceed || processIntake.isPending}
          className="gap-2"
        >
          {processIntake.isPending ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <Play size={14} />
          )}
          Process & Start Agent OS
        </Button>
      </div>
    </div>
  )
}
