/**
 * Modal for uploading or pasting a PRD document to extract strategy steps.
 * Two tabs: Upload File and Paste Content.
 */

import { useState, useCallback, useRef } from 'react'
import { Upload, FileText, Loader2, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { useUploadPRD } from '@/hooks/useToolFactory'
import type { TFPRDExtractionResult } from '@/lib/types'

interface PRDUploadModalProps {
  isOpen: boolean
  onClose: () => void
  onExtractionComplete: (result: TFPRDExtractionResult) => void
}

type Tab = 'upload' | 'paste'

export function PRDUploadModal({ isOpen, onClose, onExtractionComplete }: PRDUploadModalProps) {
  const [tab, setTab] = useState<Tab>('paste')
  const [pasteContent, setPasteContent] = useState('')
  const [fileName, setFileName] = useState<string | null>(null)
  const [fileContent, setFileContent] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const uploadPRD = useUploadPRD()

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setFileName(file.name)
    setError(null)
    const reader = new FileReader()
    reader.onload = (ev) => {
      setFileContent(ev.target?.result as string)
    }
    reader.onerror = () => setError('Failed to read file')
    reader.readAsText(file)
  }, [])

  const handleSubmit = useCallback(async () => {
    setError(null)
    const content = tab === 'upload' ? fileContent : pasteContent
    const name = tab === 'upload' ? (fileName ?? 'prd.md') : 'pasted-prd.md'

    if (!content || content.trim().length < 100) {
      setError('Content must be at least 100 characters')
      return
    }

    try {
      const result = await uploadPRD.mutateAsync({ content: content.trim(), filename: name })
      onExtractionComplete(result)
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Extraction failed')
    }
  }, [tab, fileContent, pasteContent, fileName, uploadPRD, onExtractionComplete, onClose])

  const canSubmit = tab === 'upload' ? !!fileContent : pasteContent.trim().length >= 100

  return (
    <Dialog open={isOpen} onOpenChange={(open) => { if (!open) onClose() }}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Import from PRD</DialogTitle>
          <DialogDescription>
            Upload a PRD document or paste its content to extract strategy steps.
          </DialogDescription>
        </DialogHeader>

        {/* Tab selector */}
        <div className="flex gap-1 rounded-lg border border-border p-1 bg-muted/30">
          <button
            onClick={() => setTab('upload')}
            className={`flex-1 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              tab === 'upload' ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <Upload size={14} className="inline mr-1.5" />
            Upload File
          </button>
          <button
            onClick={() => setTab('paste')}
            className={`flex-1 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              tab === 'paste' ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <FileText size={14} className="inline mr-1.5" />
            Paste Content
          </button>
        </div>

        {/* Tab content */}
        {tab === 'upload' ? (
          <div className="space-y-3">
            <div
              onClick={() => fileInputRef.current?.click()}
              className="flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-border p-8 cursor-pointer hover:border-primary/50 transition-colors"
            >
              <Upload size={24} className="text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                {fileName ?? 'Click to upload .md, .txt, or .pdf'}
              </p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".md,.txt,.pdf"
                onChange={handleFileChange}
                className="hidden"
              />
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            <Textarea
              value={pasteContent}
              onChange={(e) => setPasteContent(e.target.value)}
              placeholder="Paste your PRD content here..."
              className="min-h-[200px] font-mono text-sm"
            />
            <p className="text-xs text-muted-foreground text-right">
              {pasteContent.length.toLocaleString()} characters (min 100)
            </p>
          </div>
        )}

        {error && (
          <div className="flex gap-2 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2">
            <AlertCircle size={16} className="text-destructive shrink-0 mt-0.5" />
            <p className="text-sm text-destructive">{error}</p>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={uploadPRD.isPending}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!canSubmit || uploadPRD.isPending}>
            {uploadPRD.isPending ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Extracting...
              </>
            ) : (
              'Extract Steps'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
