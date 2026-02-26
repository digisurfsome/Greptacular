/**
 * StandardsPanel Component
 *
 * Collapsible side panel showing the project's coding standards.
 * Allows viewing and editing standards files.
 */

import { useState, useCallback } from 'react'
import { ChevronDown, ChevronRight, Edit3, Save, X, FileText } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import {
  useStandards,
  useStandardFile,
  useUpdateStandard,
} from '@/hooks/useAgentOS'

interface StandardsPanelProps {
  projectName: string
  isOpen: boolean
  onToggle: () => void
}

export function StandardsPanel({ projectName, isOpen, onToggle }: StandardsPanelProps) {
  const { data } = useStandards(projectName)
  const files = data?.files ?? []

  if (!isOpen) {
    return (
      <button
        onClick={onToggle}
        className="flex items-center gap-2 px-3 py-2 text-xs font-bold text-foreground hover:bg-muted/50 rounded-lg w-full text-left transition-colors"
      >
        <ChevronRight size={14} />
        <FileText size={14} className="text-blue-500" />
        Standards ({files.length})
      </button>
    )
  }

  return (
    <Card>
      <CardContent className="p-0">
        <button
          onClick={onToggle}
          className="flex items-center justify-between w-full px-3 py-2 border-b border-border hover:bg-muted/30 transition-colors"
        >
          <div className="flex items-center gap-2">
            <ChevronDown size={14} />
            <FileText size={14} className="text-blue-500" />
            <span className="text-xs font-bold text-foreground">Standards</span>
          </div>
          <span className="text-[10px] text-muted-foreground">{files.length} files</span>
        </button>

        <div className="divide-y divide-border/50">
          {files.length === 0 ? (
            <div className="px-3 py-4 text-center text-xs text-muted-foreground">
              No standards files yet
            </div>
          ) : (
            files.map(file => (
              <StandardsFileItem
                key={file.name}
                projectName={projectName}
                filename={file.name}
              />
            ))
          )}
        </div>
      </CardContent>
    </Card>
  )
}

// ============================================================================
// File accordion item
// ============================================================================

function StandardsFileItem({ projectName, filename }: { projectName: string; filename: string }) {
  const [expanded, setExpanded] = useState(false)
  const [editing, setEditing] = useState(false)
  const [editContent, setEditContent] = useState('')

  const { data: fileData } = useStandardFile(projectName, expanded ? filename : '')
  const updateStandard = useUpdateStandard(projectName)

  const handleEdit = useCallback(() => {
    setEditContent(fileData?.content || '')
    setEditing(true)
  }, [fileData])

  const handleSave = useCallback(() => {
    updateStandard.mutate(
      { filename, content: editContent },
      { onSuccess: () => setEditing(false) },
    )
  }, [filename, editContent, updateStandard])

  const handleCancel = useCallback(() => {
    setEditing(false)
    setEditContent('')
  }, [])

  // Pretty-print filename: "tech-stack.md" → "Tech Stack"
  const displayName = filename
    .replace(/\.md$/, '')
    .replace(/-/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase())

  return (
    <div>
      <button
        onClick={() => setExpanded(prev => !prev)}
        className="flex items-center gap-2 w-full px-3 py-2 text-left hover:bg-muted/20 transition-colors"
      >
        {expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
        <span className="text-xs font-medium text-foreground">{displayName}</span>
      </button>

      {expanded && (
        <div className="px-3 pb-3">
          {editing ? (
            <div className="space-y-2">
              <textarea
                className="w-full h-40 p-2 text-xs border border-border rounded bg-background text-foreground resize-none font-mono focus:outline-none focus:border-primary"
                value={editContent}
                onChange={e => setEditContent(e.target.value)}
              />
              <div className="flex gap-1.5">
                <Button size="sm" className="h-6 text-[10px]" onClick={handleSave} disabled={updateStandard.isPending}>
                  <Save size={10} />
                  Save
                </Button>
                <Button size="sm" variant="ghost" className="h-6 text-[10px]" onClick={handleCancel}>
                  <X size={10} />
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            <div>
              <pre className="text-[11px] text-muted-foreground whitespace-pre-wrap font-mono leading-relaxed max-h-48 overflow-y-auto">
                {fileData?.content || '(loading...)'}
              </pre>
              <Button
                size="sm"
                variant="ghost"
                className="h-6 text-[10px] mt-2"
                onClick={handleEdit}
              >
                <Edit3 size={10} />
                Edit
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
