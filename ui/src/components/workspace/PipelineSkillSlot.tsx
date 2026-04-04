/**
 * PipelineSkillSlot
 *
 * Individual skill slot for the pipeline configurator. Each slot holds a prompt
 * (pasted or uploaded from a .md file) that becomes one stage in the sequential
 * pipeline. Supports expand/collapse, file upload, and inline editing.
 */

import { useState, useRef } from 'react'
import { Upload, ChevronDown, ChevronRight, X, CheckCircle2 } from 'lucide-react'

interface PipelineSkillSlotProps {
  index: number
  label: string
  text: string
  onUpdate: (field: 'label' | 'text', value: string) => void
  onRemove: () => void
  onFileUpload: (file: File) => void
}

export function PipelineSkillSlot({
  index,
  label,
  text,
  onUpdate,
  onRemove,
  onFileUpload,
}: PipelineSkillSlotProps): React.JSX.Element {
  const [expanded, setExpanded] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Notify parent so it can handle file-level logic if needed
    onFileUpload(file)

    const reader = new FileReader()
    reader.onload = () => {
      const content = reader.result as string
      onUpdate('text', content)
      // Auto-extract label from first markdown heading
      const match = content.match(/^#\s+(.+)$/m)
      if (match) onUpdate('label', match[1].trim())
    }
    reader.readAsText(file)
    e.target.value = '' // reset for re-upload
  }

  const hasContent = text.trim().length > 0
  const preview = text.split('\n')[0]?.slice(0, 60) || '(empty)'

  return (
    <div className="border border-border rounded-lg overflow-hidden">
      {/* Header row */}
      <div className="flex items-center gap-2 px-2 py-1.5 bg-muted/30">
        <span className="text-[10px] font-mono text-muted-foreground w-5 text-right">
          {index + 1}.
        </span>

        {/* Editable label */}
        <input
          value={label}
          onChange={(e) => onUpdate('label', e.target.value)}
          className="flex-1 text-xs font-semibold bg-transparent border-none outline-none text-foreground"
          placeholder={`Skill ${index + 1}`}
        />

        {/* Status indicator */}
        {hasContent && (
          <span className="text-[10px] text-emerald-600 flex items-center gap-0.5">
            <CheckCircle2 size={10} /> loaded
          </span>
        )}

        {/* Upload button */}
        <button
          onClick={() => fileInputRef.current?.click()}
          className="text-muted-foreground hover:text-foreground"
          title="Upload .md file"
        >
          <Upload size={12} />
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".md,.txt,.markdown"
          onChange={handleFile}
          className="hidden"
        />

        {/* Expand/collapse */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-muted-foreground hover:text-foreground"
        >
          {expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
        </button>

        {/* Remove */}
        <button
          onClick={onRemove}
          className="text-muted-foreground hover:text-red-500"
        >
          <X size={12} />
        </button>
      </div>

      {/* Collapsed preview */}
      {!expanded && hasContent && (
        <div className="px-2 py-1 text-[10px] text-muted-foreground truncate border-t border-border/50">
          {preview}
        </div>
      )}

      {/* Expanded editor */}
      {expanded && (
        <textarea
          value={text}
          onChange={(e) => onUpdate('text', e.target.value)}
          className="w-full resize-none min-h-[120px] max-h-[300px] px-2 py-1.5 text-[11px] font-mono bg-muted/20 border-t border-border/50 outline-none text-foreground"
          placeholder="Paste skill prompt or upload a .md file..."
        />
      )}
    </div>
  )
}
