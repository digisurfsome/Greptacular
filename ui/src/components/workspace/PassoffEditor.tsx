/**
 * Passoff Editor
 *
 * A staging area between the Research (200K) and Execute (1M) chat panels.
 * As the user figures things out in the Research panel, they can send
 * assistant summaries here. Each section gets a title and content block.
 * The user can freely edit everything, add their own notes between sections,
 * and finally send the whole document to the Execute panel as one payload.
 */

import { useState, useRef, useCallback, useEffect } from 'react'
import { Send, Trash2, GripVertical, Plus, ChevronDown, ChevronUp } from 'lucide-react'
import { Button } from '@/components/ui/button'

export interface PassoffSection {
  id: string
  title: string
  content: string
}

interface PassoffEditorProps {
  sections: PassoffSection[]
  onSectionsChange: (sections: PassoffSection[]) => void
  onSendToExecute: (fullDocument: string) => void
  /** Optional preamble text shown at the top (user-editable). */
  preamble: string
  onPreambleChange: (text: string) => void
}

function generateSectionId(): string {
  return `sec-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`
}

export function PassoffEditor({
  sections,
  onSectionsChange,
  onSendToExecute,
  preamble,
  onPreambleChange,
}: PassoffEditorProps): React.JSX.Element {
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set())
  const [dragIndex, setDragIndex] = useState<number | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  // Scroll to bottom when a new section is added
  const prevCountRef = useRef(sections.length)
  useEffect(() => {
    if (sections.length > prevCountRef.current) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
    prevCountRef.current = sections.length
  }, [sections.length])

  const updateSection = useCallback((id: string, updates: Partial<PassoffSection>) => {
    onSectionsChange(sections.map(s => s.id === id ? { ...s, ...updates } : s))
  }, [sections, onSectionsChange])

  const removeSection = useCallback((id: string) => {
    onSectionsChange(sections.filter(s => s.id !== id))
  }, [sections, onSectionsChange])

  const addSection = useCallback(() => {
    onSectionsChange([...sections, {
      id: generateSectionId(),
      title: '',
      content: '',
    }])
  }, [sections, onSectionsChange])

  const toggleCollapse = useCallback((id: string) => {
    setCollapsed(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  // Drag-and-drop reorder
  const handleDragStart = useCallback((index: number) => {
    setDragIndex(index)
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent, index: number) => {
    e.preventDefault()
    if (dragIndex === null || dragIndex === index) return
    const reordered = [...sections]
    const [moved] = reordered.splice(dragIndex, 1)
    reordered.splice(index, 0, moved)
    onSectionsChange(reordered)
    setDragIndex(index)
  }, [dragIndex, sections, onSectionsChange])

  const handleDragEnd = useCallback(() => {
    setDragIndex(null)
  }, [])

  // Build the full document for sending to Execute
  const buildDocument = useCallback(() => {
    const parts: string[] = []
    if (preamble.trim()) {
      parts.push(preamble.trim())
      parts.push('')
    }
    for (const section of sections) {
      if (section.title.trim() || section.content.trim()) {
        if (section.title.trim()) {
          parts.push(`## ${section.title.trim()}`)
          parts.push('')
        }
        if (section.content.trim()) {
          parts.push(section.content.trim())
          parts.push('')
        }
      }
    }
    return parts.join('\n')
  }, [preamble, sections])

  const handleSend = useCallback(() => {
    const doc = buildDocument()
    if (doc.trim()) {
      onSendToExecute(doc)
    }
  }, [buildDocument, onSendToExecute])

  const isEmpty = !preamble.trim() && sections.length === 0

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-border bg-amber-500/10">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold tracking-wide text-amber-600">
            PASSOFF
          </span>
          <span className="text-[10px] text-amber-600/60">
            {sections.length} section{sections.length !== 1 ? 's' : ''}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            className="h-6 px-1.5 text-amber-600 hover:text-amber-700"
            onClick={addSection}
            title="Add empty section"
          >
            <Plus size={14} />
          </Button>
        </div>
      </div>

      {/* Preamble - user's own intro text */}
      <div className="px-3 pt-3 pb-1">
        <textarea
          value={preamble}
          onChange={(e) => onPreambleChange(e.target.value)}
          placeholder="Add context here... Explain the big picture, how sections connect, what the Execute agent should know upfront."
          className="w-full resize-none min-h-[60px] rounded-md border border-border bg-input px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground/60 outline-none ring-ring focus:ring-1"
          rows={3}
        />
      </div>

      {/* Sections */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-2">
        {sections.map((section, index) => (
          <div
            key={section.id}
            className={`border border-border rounded-md bg-card transition-shadow ${
              dragIndex === index ? 'shadow-lg ring-2 ring-amber-400/50' : ''
            }`}
            draggable
            onDragStart={() => handleDragStart(index)}
            onDragOver={(e) => handleDragOver(e, index)}
            onDragEnd={handleDragEnd}
          >
            {/* Section header */}
            <div className="flex items-center gap-1 px-2 py-1.5 border-b border-border/50">
              <GripVertical
                size={12}
                className="text-muted-foreground/40 cursor-grab flex-shrink-0"
              />
              <input
                value={section.title}
                onChange={(e) => updateSection(section.id, { title: e.target.value })}
                placeholder={`Section ${index + 1} title...`}
                className="flex-1 text-xs font-semibold bg-transparent outline-none text-foreground placeholder:text-muted-foreground/40"
              />
              <button
                onClick={() => toggleCollapse(section.id)}
                className="p-0.5 text-muted-foreground/60 hover:text-foreground"
              >
                {collapsed.has(section.id) ? <ChevronDown size={12} /> : <ChevronUp size={12} />}
              </button>
              <button
                onClick={() => removeSection(section.id)}
                className="p-0.5 text-muted-foreground/40 hover:text-destructive"
                title="Remove section"
              >
                <Trash2 size={12} />
              </button>
            </div>

            {/* Section content */}
            {!collapsed.has(section.id) && (
              <textarea
                value={section.content}
                onChange={(e) => updateSection(section.id, { content: e.target.value })}
                placeholder="Paste or type content here..."
                className="w-full resize-none min-h-[80px] px-3 py-2 text-xs text-foreground bg-transparent outline-none placeholder:text-muted-foreground/40"
                rows={4}
              />
            )}
          </div>
        ))}

        {isEmpty && (
          <div className="flex flex-col items-center justify-center py-8 text-muted-foreground/50">
            <p className="text-xs text-center max-w-[200px]">
              Use the <span className="font-semibold text-amber-600/60">Passoff</span> button on assistant messages to send findings here.
            </p>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Send to Execute button */}
      <div className="px-3 py-2 border-t border-border">
        <Button
          onClick={handleSend}
          disabled={isEmpty}
          className="w-full bg-violet-600 hover:bg-violet-700 text-white text-xs gap-2"
          title="Send entire passoff document to the Execute (API/1M) panel"
        >
          <Send size={14} />
          Send to Execute
        </Button>
      </div>
    </div>
  )
}
