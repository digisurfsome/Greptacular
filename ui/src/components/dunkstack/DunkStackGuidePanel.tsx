/**
 * DunkStackGuidePanel - Floating, resizable, tabbed guide panel.
 *
 * Features:
 * - Draggable: click-and-drag the title bar to reposition
 * - Resizable: drag edges/corners to resize (min 400x300, max viewport)
 * - Tabs: "Manual" (renders DUNKSTACK_MANUAL.md) and "Notes" (CRUD with tags/dates)
 * - Notes persisted to localStorage with create, save, date, tag support
 */

import { useState, useCallback, useEffect, useRef } from 'react'
import ReactMarkdown, { type Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  BookOpen,
  StickyNote,
  Plus,
  Trash2,
  Save,
  Tag,
  X,
  GripHorizontal,
  Maximize2,
  Minimize2,
} from 'lucide-react'

// ============================================================================
// Types
// ============================================================================

interface Note {
  id: string
  title: string
  content: string
  tags: string[]
  createdAt: string
  updatedAt: string
}

type GuideTab = 'manual' | 'notes'

interface DunkStackGuidePanelProps {
  onClose: () => void
}

// ============================================================================
// Constants
// ============================================================================

const STORAGE_KEY = 'dunkstack-guide-notes'
const PANEL_POS_KEY = 'dunkstack-guide-position'
const PANEL_SIZE_KEY = 'dunkstack-guide-size'

const MIN_WIDTH = 420
const MIN_HEIGHT = 340
const DEFAULT_WIDTH = 720
const DEFAULT_HEIGHT = 560

// ============================================================================
// Helpers
// ============================================================================

function loadNotes(): Note[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return JSON.parse(raw)
  } catch { /* ignore */ }
  return []
}

function saveNotes(notes: Note[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(notes))
}

function loadPosition(): { x: number; y: number } | null {
  try {
    const raw = localStorage.getItem(PANEL_POS_KEY)
    if (raw) return JSON.parse(raw)
  } catch { /* ignore */ }
  return null
}

function savePosition(pos: { x: number; y: number }) {
  localStorage.setItem(PANEL_POS_KEY, JSON.stringify(pos))
}

function loadSize(): { w: number; h: number } | null {
  try {
    const raw = localStorage.getItem(PANEL_SIZE_KEY)
    if (raw) return JSON.parse(raw)
  } catch { /* ignore */ }
  return null
}

function saveSize(size: { w: number; h: number }) {
  localStorage.setItem(PANEL_SIZE_KEY, JSON.stringify(size))
}

function generateId(): string {
  return `note-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// ============================================================================
// Markdown components for the Manual tab
// ============================================================================

const remarkPlugins = [remarkGfm]

const markdownComponents: Components = {
  a: ({ children, href, ...props }) => (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="text-primary underline hover:text-primary/80"
      {...props}
    >
      {children}
    </a>
  ),
  h1: ({ children, ...props }) => (
    <h1 className="text-2xl font-bold mt-6 mb-3 text-foreground border-b border-border pb-2" {...props}>
      {children}
    </h1>
  ),
  h2: ({ children, ...props }) => (
    <h2 className="text-xl font-bold mt-5 mb-2 text-foreground border-b border-border/50 pb-1" {...props}>
      {children}
    </h2>
  ),
  h3: ({ children, ...props }) => (
    <h3 className="text-lg font-semibold mt-4 mb-2 text-foreground" {...props}>{children}</h3>
  ),
  h4: ({ children, ...props }) => (
    <h4 className="text-base font-semibold mt-3 mb-1 text-foreground" {...props}>{children}</h4>
  ),
  p: ({ children, ...props }) => (
    <p className="text-sm text-muted-foreground mb-3 leading-relaxed" {...props}>{children}</p>
  ),
  ul: ({ children, ...props }) => (
    <ul className="list-disc list-inside text-sm text-muted-foreground mb-3 space-y-1" {...props}>{children}</ul>
  ),
  ol: ({ children, ...props }) => (
    <ol className="list-decimal list-inside text-sm text-muted-foreground mb-3 space-y-1" {...props}>{children}</ol>
  ),
  li: ({ children, ...props }) => (
    <li className="text-sm text-muted-foreground" {...props}>{children}</li>
  ),
  code: ({ children, className, ...props }) => {
    const isBlock = className?.includes('language-')
    if (isBlock) {
      return (
        <code className={`block bg-muted/60 rounded px-3 py-2 text-xs font-mono overflow-x-auto mb-3 ${className || ''}`} {...props}>
          {children}
        </code>
      )
    }
    return (
      <code className="bg-muted px-1.5 py-0.5 rounded text-xs font-mono text-foreground" {...props}>
        {children}
      </code>
    )
  },
  pre: ({ children, ...props }) => (
    <pre className="bg-muted/60 rounded-lg p-3 overflow-x-auto mb-3 border border-border/30" {...props}>
      {children}
    </pre>
  ),
  table: ({ children, ...props }) => (
    <div className="overflow-x-auto mb-3">
      <table className="w-full text-sm border border-border rounded" {...props}>{children}</table>
    </div>
  ),
  thead: ({ children, ...props }) => (
    <thead className="bg-muted/40" {...props}>{children}</thead>
  ),
  th: ({ children, ...props }) => (
    <th className="text-left px-3 py-2 text-xs font-bold text-foreground border-b border-border" {...props}>
      {children}
    </th>
  ),
  td: ({ children, ...props }) => (
    <td className="px-3 py-2 text-xs text-muted-foreground border-b border-border/30" {...props}>
      {children}
    </td>
  ),
  hr: (props) => <hr className="my-4 border-border" {...props} />,
  blockquote: ({ children, ...props }) => (
    <blockquote className="border-l-4 border-primary/40 pl-4 py-1 mb-3 text-sm text-muted-foreground italic" {...props}>
      {children}
    </blockquote>
  ),
  strong: ({ children, ...props }) => (
    <strong className="font-bold text-foreground" {...props}>{children}</strong>
  ),
}

// ============================================================================
// Manual Tab
// ============================================================================

function ManualTab(): React.JSX.Element {
  const [content, setContent] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    fetch('/DUNKSTACK_MANUAL.md')
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.text()
      })
      .then(text => {
        if (!cancelled) {
          setContent(text)
          setLoading(false)
        }
      })
      .catch(err => {
        if (!cancelled) {
          setError(err.message)
          setLoading(false)
        }
      })
    return () => { cancelled = true }
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="flex flex-col items-center gap-3">
          <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <span className="text-xs text-muted-foreground">Loading manual...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-sm text-destructive">Failed to load manual: {error}</p>
      </div>
    )
  }

  return (
    <div className="p-5 overflow-y-auto h-full">
      <ReactMarkdown remarkPlugins={remarkPlugins} components={markdownComponents}>
        {content}
      </ReactMarkdown>
    </div>
  )
}

// ============================================================================
// Notes Tab
// ============================================================================

function NotesTab(): React.JSX.Element {
  const [notes, setNotes] = useState<Note[]>(loadNotes)
  const [selectedNoteId, setSelectedNoteId] = useState<string | null>(null)
  const [editTitle, setEditTitle] = useState('')
  const [editContent, setEditContent] = useState('')
  const [editTags, setEditTags] = useState('')
  const [tagInput, setTagInput] = useState('')
  const [filterTag, setFilterTag] = useState<string | null>(null)
  const [dirty, setDirty] = useState(false)
  const titleRef = useRef<HTMLInputElement>(null)

  const selectedNote = notes.find(n => n.id === selectedNoteId) ?? null

  // All unique tags across notes
  const allTags = Array.from(new Set(notes.flatMap(n => n.tags))).sort()

  // Filtered notes
  const filteredNotes = filterTag
    ? notes.filter(n => n.tags.includes(filterTag))
    : notes

  const persistNotes = useCallback((updated: Note[]) => {
    setNotes(updated)
    saveNotes(updated)
  }, [])

  const handleCreateNote = useCallback(() => {
    const now = new Date().toISOString()
    const newNote: Note = {
      id: generateId(),
      title: 'Untitled Note',
      content: '',
      tags: [],
      createdAt: now,
      updatedAt: now,
    }
    const updated = [newNote, ...notes]
    persistNotes(updated)
    setSelectedNoteId(newNote.id)
    setEditTitle(newNote.title)
    setEditContent(newNote.content)
    setEditTags('')
    setDirty(false)
    setTimeout(() => titleRef.current?.select(), 50)
  }, [notes, persistNotes])

  const handleSelectNote = useCallback((note: Note) => {
    setSelectedNoteId(note.id)
    setEditTitle(note.title)
    setEditContent(note.content)
    setEditTags(note.tags.join(', '))
    setDirty(false)
  }, [])

  const handleSaveNote = useCallback(() => {
    if (!selectedNoteId) return
    const now = new Date().toISOString()
    const tags = editTags
      .split(',')
      .map(t => t.trim())
      .filter(Boolean)
    const updated = notes.map(n =>
      n.id === selectedNoteId
        ? { ...n, title: editTitle, content: editContent, tags, updatedAt: now }
        : n
    )
    persistNotes(updated)
    setDirty(false)
  }, [selectedNoteId, editTitle, editContent, editTags, notes, persistNotes])

  const handleDeleteNote = useCallback((noteId: string) => {
    const updated = notes.filter(n => n.id !== noteId)
    persistNotes(updated)
    if (selectedNoteId === noteId) {
      setSelectedNoteId(null)
      setEditTitle('')
      setEditContent('')
      setEditTags('')
      setDirty(false)
    }
  }, [notes, selectedNoteId, persistNotes])

  const handleAddTag = useCallback(() => {
    if (!tagInput.trim()) return
    const currentTags = editTags
      .split(',')
      .map(t => t.trim())
      .filter(Boolean)
    if (!currentTags.includes(tagInput.trim())) {
      currentTags.push(tagInput.trim())
      setEditTags(currentTags.join(', '))
      setDirty(true)
    }
    setTagInput('')
  }, [tagInput, editTags])

  const handleRemoveTag = useCallback((tag: string) => {
    const currentTags = editTags
      .split(',')
      .map(t => t.trim())
      .filter(t => t !== tag)
    setEditTags(currentTags.join(', '))
    setDirty(true)
  }, [editTags])

  // Keyboard shortcut: Ctrl+S to save
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's' && selectedNoteId && dirty) {
        e.preventDefault()
        handleSaveNote()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [selectedNoteId, dirty, handleSaveNote])

  const currentTags = editTags
    .split(',')
    .map(t => t.trim())
    .filter(Boolean)

  return (
    <div className="flex h-full">
      {/* Notes sidebar list */}
      <div className="w-[200px] shrink-0 border-r border-border/50 flex flex-col bg-card/30">
        {/* Header + create button */}
        <div className="flex items-center justify-between px-3 py-2 border-b border-border/50">
          <span className="text-xs font-bold text-foreground">Notes</span>
          <button
            onClick={handleCreateNote}
            className="p-1 rounded hover:bg-muted text-primary"
            title="Create new note"
          >
            <Plus size={14} />
          </button>
        </div>

        {/* Tag filter */}
        {allTags.length > 0 && (
          <div className="px-2 py-1.5 border-b border-border/30 flex flex-wrap gap-1">
            <button
              onClick={() => setFilterTag(null)}
              className={`px-1.5 py-0.5 rounded text-[9px] font-semibold transition-colors ${
                filterTag === null
                  ? 'bg-primary/15 text-primary'
                  : 'text-muted-foreground hover:bg-muted'
              }`}
            >
              All
            </button>
            {allTags.map(tag => (
              <button
                key={tag}
                onClick={() => setFilterTag(filterTag === tag ? null : tag)}
                className={`px-1.5 py-0.5 rounded text-[9px] font-semibold transition-colors ${
                  filterTag === tag
                    ? 'bg-primary/15 text-primary'
                    : 'text-muted-foreground hover:bg-muted'
                }`}
              >
                {tag}
              </button>
            ))}
          </div>
        )}

        {/* Notes list */}
        <div className="flex-1 overflow-y-auto">
          {filteredNotes.length === 0 ? (
            <div className="px-3 py-6 text-center text-xs text-muted-foreground">
              {notes.length === 0 ? 'No notes yet' : 'No matching notes'}
            </div>
          ) : (
            filteredNotes.map(note => (
              <div
                key={note.id}
                onClick={() => handleSelectNote(note)}
                className={`group px-3 py-2 cursor-pointer border-b border-border/20 transition-colors ${
                  selectedNoteId === note.id
                    ? 'bg-primary/10 border-l-2 border-l-primary'
                    : 'hover:bg-muted/50 border-l-2 border-l-transparent'
                }`}
              >
                <div className="flex items-start justify-between gap-1">
                  <div className="text-xs font-semibold text-foreground truncate flex-1">
                    {note.title || 'Untitled'}
                  </div>
                  <button
                    onClick={e => { e.stopPropagation(); handleDeleteNote(note.id) }}
                    className="p-0.5 rounded opacity-0 group-hover:opacity-100 hover:bg-destructive/10 text-destructive transition-opacity"
                    title="Delete note"
                  >
                    <Trash2 size={11} />
                  </button>
                </div>
                <div className="text-[10px] text-muted-foreground mt-0.5">
                  {formatDate(note.updatedAt)}
                </div>
                {note.tags.length > 0 && (
                  <div className="flex flex-wrap gap-0.5 mt-1">
                    {note.tags.map(t => (
                      <span key={t} className="px-1 py-px rounded bg-primary/10 text-primary text-[8px] font-semibold">
                        {t}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Note editor */}
      <div className="flex-1 flex flex-col min-w-0">
        {selectedNote ? (
          <>
            {/* Title */}
            <div className="px-4 pt-3 pb-2">
              <input
                ref={titleRef}
                type="text"
                value={editTitle}
                onChange={e => { setEditTitle(e.target.value); setDirty(true) }}
                className="w-full bg-transparent text-base font-bold text-foreground outline-none border-b border-border/30 pb-1 focus:border-primary/50"
                placeholder="Note title..."
              />
            </div>

            {/* Tags area */}
            <div className="px-4 pb-2">
              <div className="flex items-center gap-1.5 flex-wrap">
                <Tag size={11} className="text-muted-foreground shrink-0" />
                {currentTags.map(tag => (
                  <span
                    key={tag}
                    className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-primary/10 text-primary text-[10px] font-semibold"
                  >
                    {tag}
                    <button
                      onClick={() => handleRemoveTag(tag)}
                      className="hover:text-destructive ml-0.5"
                    >
                      <X size={9} />
                    </button>
                  </span>
                ))}
                <div className="flex items-center gap-1">
                  <input
                    type="text"
                    value={tagInput}
                    onChange={e => setTagInput(e.target.value)}
                    onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); handleAddTag() } }}
                    className="bg-transparent text-[10px] text-muted-foreground outline-none w-20 placeholder:text-muted-foreground/40"
                    placeholder="add tag..."
                  />
                </div>
              </div>
            </div>

            {/* Date info */}
            <div className="px-4 pb-2 flex items-center gap-3 text-[10px] text-muted-foreground/60">
              <span>Created: {formatDate(selectedNote.createdAt)}</span>
              <span>Updated: {formatDate(selectedNote.updatedAt)}</span>
            </div>

            {/* Content */}
            <div className="flex-1 px-4 pb-3 min-h-0">
              <textarea
                value={editContent}
                onChange={e => { setEditContent(e.target.value); setDirty(true) }}
                className="w-full h-full bg-muted/20 rounded-lg p-3 text-sm text-foreground outline-none resize-none border border-border/30 focus:border-primary/30 font-mono leading-relaxed"
                placeholder="Write your notes here..."
              />
            </div>

            {/* Save bar */}
            <div className="flex items-center justify-between px-4 py-2 border-t border-border/50 bg-card/40">
              <span className="text-[10px] text-muted-foreground">
                {dirty ? 'Unsaved changes' : 'Saved'}
              </span>
              <button
                onClick={handleSaveNote}
                disabled={!dirty}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold transition-colors ${
                  dirty
                    ? 'bg-primary text-primary-foreground hover:bg-primary/90'
                    : 'bg-muted text-muted-foreground cursor-not-allowed'
                }`}
              >
                <Save size={12} />
                Save
              </button>
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-muted-foreground gap-2">
            <StickyNote size={32} className="opacity-30" />
            <p className="text-sm">Select a note or create a new one</p>
            <button
              onClick={handleCreateNote}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90 mt-2"
            >
              <Plus size={12} />
              New Note
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

// ============================================================================
// Main Panel Component (Floating, Resizable, Tabbed)
// ============================================================================

export function DunkStackGuidePanel({ onClose }: DunkStackGuidePanelProps): React.JSX.Element {
  const [activeTab, setActiveTab] = useState<GuideTab>('manual')
  const [maximized, setMaximized] = useState(false)

  // Position and size state
  const savedPos = loadPosition()
  const savedSize = loadSize()
  const [pos, setPos] = useState({ x: savedPos?.x ?? 80, y: savedPos?.y ?? 40 })
  const [size, setSize] = useState({ w: savedSize?.w ?? DEFAULT_WIDTH, h: savedSize?.h ?? DEFAULT_HEIGHT })

  // Pre-maximize state for restore
  const preMaxRef = useRef({ pos: { x: 80, y: 40 }, size: { w: DEFAULT_WIDTH, h: DEFAULT_HEIGHT } })

  // Refs for drag and resize
  const panelRef = useRef<HTMLDivElement>(null)
  const dragState = useRef<{ startX: number; startY: number; startPosX: number; startPosY: number } | null>(null)
  const resizeState = useRef<{
    startX: number
    startY: number
    startW: number
    startH: number
    startPosX: number
    startPosY: number
    edge: string
  } | null>(null)

  // Persist position & size changes
  useEffect(() => { if (!maximized) savePosition(pos) }, [pos, maximized])
  useEffect(() => { if (!maximized) saveSize(size) }, [size, maximized])

  // Close on Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  // ---- Drag logic ----
  const handleDragStart = useCallback((e: React.MouseEvent) => {
    if (maximized) return
    e.preventDefault()
    dragState.current = {
      startX: e.clientX,
      startY: e.clientY,
      startPosX: pos.x,
      startPosY: pos.y,
    }

    const handleDragMove = (ev: MouseEvent) => {
      if (!dragState.current) return
      const dx = ev.clientX - dragState.current.startX
      const dy = ev.clientY - dragState.current.startY
      const newX = Math.max(0, Math.min(window.innerWidth - 100, dragState.current.startPosX + dx))
      const newY = Math.max(0, Math.min(window.innerHeight - 40, dragState.current.startPosY + dy))
      setPos({ x: newX, y: newY })
    }

    const handleDragEnd = () => {
      dragState.current = null
      window.removeEventListener('mousemove', handleDragMove)
      window.removeEventListener('mouseup', handleDragEnd)
    }

    window.addEventListener('mousemove', handleDragMove)
    window.addEventListener('mouseup', handleDragEnd)
  }, [pos, maximized])

  // ---- Resize logic ----
  const handleResizeStart = useCallback((e: React.MouseEvent, edge: string) => {
    if (maximized) return
    e.preventDefault()
    e.stopPropagation()
    resizeState.current = {
      startX: e.clientX,
      startY: e.clientY,
      startW: size.w,
      startH: size.h,
      startPosX: pos.x,
      startPosY: pos.y,
      edge,
    }

    const handleResizeMove = (ev: MouseEvent) => {
      if (!resizeState.current) return
      const rs = resizeState.current
      const dx = ev.clientX - rs.startX
      const dy = ev.clientY - rs.startY

      let newW = rs.startW
      let newH = rs.startH
      let newX = rs.startPosX
      let newY = rs.startPosY

      if (rs.edge.includes('e')) newW = Math.max(MIN_WIDTH, rs.startW + dx)
      if (rs.edge.includes('s')) newH = Math.max(MIN_HEIGHT, rs.startH + dy)
      if (rs.edge.includes('w')) {
        newW = Math.max(MIN_WIDTH, rs.startW - dx)
        newX = rs.startPosX + (rs.startW - newW)
      }
      if (rs.edge.includes('n')) {
        newH = Math.max(MIN_HEIGHT, rs.startH - dy)
        newY = rs.startPosY + (rs.startH - newH)
      }

      setSize({ w: newW, h: newH })
      setPos({ x: newX, y: newY })
    }

    const handleResizeEnd = () => {
      resizeState.current = null
      window.removeEventListener('mousemove', handleResizeMove)
      window.removeEventListener('mouseup', handleResizeEnd)
    }

    window.addEventListener('mousemove', handleResizeMove)
    window.addEventListener('mouseup', handleResizeEnd)
  }, [size, pos, maximized])

  // ---- Maximize / Restore ----
  const handleToggleMaximize = useCallback(() => {
    if (maximized) {
      setPos(preMaxRef.current.pos)
      setSize(preMaxRef.current.size)
      setMaximized(false)
    } else {
      preMaxRef.current = { pos: { ...pos }, size: { ...size } }
      setMaximized(true)
    }
  }, [maximized, pos, size])

  const panelStyle = maximized
    ? { left: 0, top: 0, width: '100vw', height: '100vh' }
    : { left: pos.x, top: pos.y, width: size.w, height: size.h }

  const resizeEdges = ['n', 's', 'e', 'w', 'ne', 'nw', 'se', 'sw'] as const
  const edgeCursors: Record<string, string> = {
    n: 'cursor-n-resize', s: 'cursor-s-resize', e: 'cursor-e-resize', w: 'cursor-w-resize',
    ne: 'cursor-ne-resize', nw: 'cursor-nw-resize', se: 'cursor-se-resize', sw: 'cursor-sw-resize',
  }
  const edgePositions: Record<string, string> = {
    n: 'top-0 left-2 right-2 h-1.5',
    s: 'bottom-0 left-2 right-2 h-1.5',
    e: 'right-0 top-2 bottom-2 w-1.5',
    w: 'left-0 top-2 bottom-2 w-1.5',
    ne: 'top-0 right-0 w-3 h-3',
    nw: 'top-0 left-0 w-3 h-3',
    se: 'bottom-0 right-0 w-3 h-3',
    sw: 'bottom-0 left-0 w-3 h-3',
  }

  return (
    <div
      ref={panelRef}
      className="fixed z-50 flex flex-col bg-card border-2 border-border rounded-xl shadow-2xl overflow-hidden"
      style={panelStyle}
    >
      {/* Resize handles */}
      {!maximized && resizeEdges.map(edge => (
        <div
          key={edge}
          className={`absolute ${edgePositions[edge]} ${edgeCursors[edge]} z-10`}
          onMouseDown={e => handleResizeStart(e, edge)}
        />
      ))}

      {/* Title bar (drag handle) */}
      <div
        className="flex items-center justify-between px-4 py-2.5 border-b border-border bg-card shrink-0 select-none"
        onMouseDown={handleDragStart}
        style={{ cursor: maximized ? 'default' : 'move' }}
      >
        <div className="flex items-center gap-2">
          <GripHorizontal size={14} className="text-muted-foreground/50" />
          <BookOpen size={16} className="text-primary" />
          <h2 className="text-sm font-bold text-foreground">DunkStack Guide</h2>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={handleToggleMaximize}
            className="p-1.5 rounded hover:bg-muted text-muted-foreground transition-colors"
            title={maximized ? 'Restore' : 'Maximize'}
          >
            {maximized ? <Minimize2 size={13} /> : <Maximize2 size={13} />}
          </button>
          <button
            onClick={onClose}
            className="p-1.5 rounded hover:bg-destructive/10 text-foreground font-bold transition-colors"
            title="Close (Esc)"
          >
            <X size={14} />
          </button>
        </div>
      </div>

      {/* Tab bar */}
      <div className="flex items-center gap-1 px-3 py-1.5 border-b border-border/50 bg-card/80 shrink-0">
        <button
          onClick={() => setActiveTab('manual')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
            activeTab === 'manual'
              ? 'bg-primary/10 text-primary border border-primary/20'
              : 'text-muted-foreground hover:bg-muted'
          }`}
        >
          <BookOpen size={12} />
          Manual
        </button>
        <button
          onClick={() => setActiveTab('notes')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
            activeTab === 'notes'
              ? 'bg-primary/10 text-primary border border-primary/20'
              : 'text-muted-foreground hover:bg-muted'
          }`}
        >
          <StickyNote size={12} />
          Notes
        </button>
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-hidden min-h-0">
        {activeTab === 'manual' && <ManualTab />}
        {activeTab === 'notes' && <NotesTab />}
      </div>
    </div>
  )
}
