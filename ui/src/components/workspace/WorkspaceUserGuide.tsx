/**
 * WorkspaceUserGuide - Floating, draggable, resizable user guide panel.
 *
 * Provides tabbed documentation sections for the workspace chat feature,
 * plus a "Notes" tab where users can write freeform notes that are
 * auto-saved to localStorage. Position, size, and notes all persist
 * across sessions via localStorage.
 */

import { useState, useCallback, useEffect, useRef } from 'react'
import { X, Minus, Maximize2, BookOpen, GripHorizontal } from 'lucide-react'
import { Button } from '@/components/ui/button'

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const STORAGE_KEY_POS = 'workspace-guide-pos'
const STORAGE_KEY_SIZE = 'workspace-guide-size'
const STORAGE_KEY_NOTES = 'workspace-guide-notes'

const MIN_WIDTH = 340
const MIN_HEIGHT = 280
const DEFAULT_WIDTH = 460
const DEFAULT_HEIGHT = 520

const TAB_IDS = [
  'overview',
  'shortcuts',
  'sidebar',
  'chat',
  'library',
  'advanced',
  'notes',
] as const

type TabId = (typeof TAB_IDS)[number]

const TAB_LABELS: Record<TabId, string> = {
  overview: 'Overview',
  shortcuts: 'Shortcuts',
  sidebar: 'Sidebar',
  chat: 'Chat',
  library: 'Library & Repos',
  advanced: 'Advanced',
  notes: 'Notes',
}

// Platform detection for keyboard shortcut labels
const isMac = typeof navigator !== 'undefined' && navigator.platform.includes('Mac')
const mod = isMac ? 'Cmd' : 'Ctrl'

// ---------------------------------------------------------------------------
// localStorage helpers
// ---------------------------------------------------------------------------

interface Position {
  x: number
  y: number
}

interface Size {
  width: number
  height: number
}

function loadJSON<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    if (raw) return JSON.parse(raw) as T
  } catch {
    // Ignore parse errors; use fallback
  }
  return fallback
}

function saveJSON(key: string, value: unknown): void {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch {
    // Quota errors are silently ignored
  }
}

// ---------------------------------------------------------------------------
// Kbd - inline keyboard shortcut badge
// ---------------------------------------------------------------------------

function Kbd({ children }: { children: React.ReactNode }): React.JSX.Element {
  return (
    <kbd className="px-1.5 py-0.5 text-[10px] font-mono bg-muted rounded border border-border">
      {children}
    </kbd>
  )
}

// ---------------------------------------------------------------------------
// Tab content sections
// ---------------------------------------------------------------------------

function OverviewTab(): React.JSX.Element {
  return (
    <div className="space-y-2 text-xs text-muted-foreground">
      <p className="font-semibold text-foreground text-[11px]">Three-panel layout</p>
      <ul className="list-disc pl-4 space-y-1">
        <li><span className="text-foreground font-medium">Sidebar</span> &mdash; conversation list, search, categories</li>
        <li><span className="text-foreground font-medium">Chat</span> &mdash; active conversation with message history</li>
        <li><span className="text-foreground font-medium">Library &amp; Repos</span> &mdash; file uploads, GitHub repo browser</li>
      </ul>

      <p className="font-semibold text-foreground text-[11px] pt-1">Context window</p>
      <p>
        Up to <span className="text-foreground font-medium">1M tokens</span> of context.
        The budget bar shows how your context is allocated:
      </p>
      <ul className="list-disc pl-4 space-y-1">
        <li><span className="font-medium text-foreground/80">Dark</span> &mdash; conversation summaries</li>
        <li><span className="font-medium text-foreground/80">Medium</span> &mdash; recent messages</li>
        <li><span className="font-medium text-primary">Blue</span> &mdash; library files</li>
        <li><span className="font-medium text-green-600 dark:text-green-400">Green</span> &mdash; repo files</li>
      </ul>
      <p>
        The bar turns <span className="text-orange-500 font-medium">orange at 80%</span> and{' '}
        <span className="text-destructive font-medium">red at 90%</span> to warn you before
        hitting the limit.
      </p>
    </div>
  )
}

function ShortcutsTab(): React.JSX.Element {
  const shortcuts = [
    { key: `${mod}+N`, desc: 'New conversation' },
    { key: `${mod}+B`, desc: 'Toggle sidebar' },
    { key: `${mod}+L`, desc: 'Toggle library panel' },
    { key: `${mod}+F`, desc: 'Focus search' },
    { key: `${mod}+E`, desc: 'Export chat as Markdown' },
    { key: '/', desc: 'Focus chat input' },
    { key: '?', desc: 'Shortcuts help modal' },
    { key: 'Enter', desc: 'Send message' },
    { key: 'Shift+Enter', desc: 'New line' },
    { key: 'Esc', desc: 'Close modals' },
  ]

  return (
    <table className="w-full text-[10px]">
      <thead>
        <tr className="border-b border-border">
          <th className="text-left py-1 pr-2 text-muted-foreground font-medium">Shortcut</th>
          <th className="text-left py-1 text-muted-foreground font-medium">Action</th>
        </tr>
      </thead>
      <tbody>
        {shortcuts.map((s) => (
          <tr key={s.key} className="border-b border-border/50">
            <td className="py-1.5 pr-2">
              <Kbd>{s.key}</Kbd>
            </td>
            <td className="py-1.5 text-xs text-muted-foreground">{s.desc}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function SidebarTab(): React.JSX.Element {
  return (
    <div className="space-y-2 text-xs text-muted-foreground">
      <p>
        <span className="text-foreground font-medium">+ New Chat</span> button at the top
        creates a fresh conversation.
      </p>

      <p className="font-semibold text-foreground text-[11px] pt-1">Search</p>
      <ul className="list-disc pl-4 space-y-1">
        <li>Under 3 characters &mdash; local filter across visible titles</li>
        <li>3+ characters &mdash; server-side full-text search across all messages</li>
      </ul>

      <p className="font-semibold text-foreground text-[11px] pt-1">Categories</p>
      <p>
        Conversations are grouped by category with colored dots. Hover a
        conversation to reveal <span className="text-foreground font-medium">pin</span> and{' '}
        <span className="text-foreground font-medium">delete</span> actions.
      </p>
      <p>
        Use the <span className="text-foreground font-medium">Manage Categories</span> gear
        button at the bottom to create, rename, reorder, or remove categories.
      </p>
    </div>
  )
}

function ChatTab(): React.JSX.Element {
  return (
    <div className="space-y-2 text-xs text-muted-foreground">
      <p className="font-semibold text-foreground text-[11px]">Header</p>
      <ul className="list-disc pl-4 space-y-1">
        <li>Click the title to <span className="text-foreground font-medium">edit inline</span></li>
        <li>Category dropdown to re-categorize the conversation</li>
        <li>
          Connection dot:{' '}
          <span className="text-green-500">green</span> = connected,{' '}
          <span className="text-yellow-500">yellow</span> = connecting,{' '}
          <span className="text-red-500">red</span> = disconnected
        </li>
      </ul>

      <p className="font-semibold text-foreground text-[11px] pt-1">Three-dot menu</p>
      <ul className="list-disc pl-4 space-y-1">
        <li><span className="text-foreground font-medium">Fork Chat</span> &mdash; branch from any message</li>
        <li><span className="text-foreground font-medium">Inject from Chat</span> &mdash; pull messages from another conversation</li>
        <li><span className="text-foreground font-medium">Export as Markdown</span> &mdash; download full conversation</li>
      </ul>

      <p className="font-semibold text-foreground text-[11px] pt-1">Composing</p>
      <ul className="list-disc pl-4 space-y-1">
        <li><Kbd>Enter</Kbd> to send, <Kbd>Shift+Enter</Kbd> for a new line</li>
        <li>Drafts are auto-saved while you type</li>
        <li>After 50 messages an automatic summary is generated</li>
      </ul>
    </div>
  )
}

function LibraryTab(): React.JSX.Element {
  return (
    <div className="space-y-2 text-xs text-muted-foreground">
      <p className="font-semibold text-foreground text-[11px]">Files</p>
      <ul className="list-disc pl-4 space-y-1">
        <li><span className="text-foreground font-medium">Upload</span> / <span className="text-foreground font-medium">Paste</span> buttons to add files</li>
        <li>Toggle switch to inject individual files into context</li>
        <li>Scope selector: <span className="text-foreground font-medium">Global</span> (all chats) vs <span className="text-foreground font-medium">This Chat</span></li>
      </ul>

      <p className="font-semibold text-foreground text-[11px] pt-1">Repos</p>
      <ul className="list-disc pl-4 space-y-1">
        <li>Connect a GitHub repository</li>
        <li>Browse the file tree and select files to inject</li>
        <li>Sync to pull the latest changes</li>
        <li>Disconnect when no longer needed</li>
      </ul>
    </div>
  )
}

function AdvancedTab(): React.JSX.Element {
  return (
    <div className="space-y-2 text-xs text-muted-foreground">
      <p className="font-semibold text-foreground text-[11px]">Fork conversation</p>
      <p>
        Create a branch from any message. The new conversation inherits all
        messages up to the fork point. Useful for exploring alternative
        directions without losing history.
      </p>

      <p className="font-semibold text-foreground text-[11px] pt-1">Inject from Chat</p>
      <p>
        Pull messages from another conversation into the current one.
        Useful for combining insights across separate threads.
      </p>

      <p className="font-semibold text-foreground text-[11px] pt-1">Export as Markdown</p>
      <p>
        Downloads the full conversation as a <code className="text-[10px] bg-muted px-1 rounded">.md</code> file.
      </p>

      <p className="font-semibold text-foreground text-[11px] pt-1">How context works</p>
      <ul className="list-disc pl-4 space-y-1">
        <li><span className="text-foreground font-medium">Summaries</span> &mdash; older messages are summarized to save space</li>
        <li><span className="text-foreground font-medium">Recent messages</span> &mdash; kept verbatim, up to ~400K tokens</li>
        <li><span className="text-foreground font-medium">Library files</span> &mdash; injected when toggled on</li>
        <li><span className="text-foreground font-medium">Repo files</span> &mdash; selected files from connected repos</li>
      </ul>
    </div>
  )
}

function NotesTab(): React.JSX.Element {
  const [notes, setNotes] = useState(() => {
    try {
      return localStorage.getItem(STORAGE_KEY_NOTES) ?? ''
    } catch {
      return ''
    }
  })
  const [showSaved, setShowSaved] = useState(false)
  const savedTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const handleChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value
    setNotes(value)
    try {
      localStorage.setItem(STORAGE_KEY_NOTES, value)
    } catch {
      // Quota exceeded - silently ignore
    }

    // Flash the "Auto-saved" indicator
    setShowSaved(true)
    if (savedTimer.current) clearTimeout(savedTimer.current)
    savedTimer.current = setTimeout(() => setShowSaved(false), 1500)
  }, [])

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (savedTimer.current) clearTimeout(savedTimer.current)
    }
  }, [])

  return (
    <div className="flex flex-col h-full gap-1">
      <textarea
        className="flex-1 w-full resize-none bg-background border border-border rounded p-2 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
        placeholder="Jot down notes, reminders, or things to try..."
        value={notes}
        onChange={handleChange}
      />
      <div className="h-4 flex items-center justify-end">
        {showSaved && (
          <span className="text-[10px] text-muted-foreground animate-fade-in">
            Auto-saved
          </span>
        )}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Tab content dispatcher
// ---------------------------------------------------------------------------

function TabContent({ tab }: { tab: TabId }): React.JSX.Element {
  switch (tab) {
    case 'overview':
      return <OverviewTab />
    case 'shortcuts':
      return <ShortcutsTab />
    case 'sidebar':
      return <SidebarTab />
    case 'chat':
      return <ChatTab />
    case 'library':
      return <LibraryTab />
    case 'advanced':
      return <AdvancedTab />
    case 'notes':
      return <NotesTab />
  }
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

interface WorkspaceUserGuideProps {
  isOpen: boolean
  onClose: () => void
}

/** Floating, draggable, resizable user guide panel for workspace chat. */
export function WorkspaceUserGuide({
  isOpen,
  onClose,
}: WorkspaceUserGuideProps): React.JSX.Element | null {
  // ---- State ----

  const [activeTab, setActiveTab] = useState<TabId>('overview')
  const [minimized, setMinimized] = useState(false)

  // Position and size, initialized from localStorage or centered on screen
  const [position, setPosition] = useState<Position>(() => {
    const saved = loadJSON<Position | null>(STORAGE_KEY_POS, null)
    if (saved) return saved
    // Center on screen on first open
    if (typeof window !== 'undefined') {
      return {
        x: Math.max(0, Math.round((window.innerWidth - DEFAULT_WIDTH) / 2)),
        y: Math.max(0, Math.round((window.innerHeight - DEFAULT_HEIGHT) / 2)),
      }
    }
    return { x: 100, y: 100 }
  })

  const [size, setSize] = useState<Size>(() =>
    loadJSON<Size>(STORAGE_KEY_SIZE, { width: DEFAULT_WIDTH, height: DEFAULT_HEIGHT }),
  )

  // ---- Refs for drag/resize ----

  const panelRef = useRef<HTMLDivElement>(null)
  const isDragging = useRef(false)
  const isResizing = useRef(false)
  const dragOffset = useRef({ x: 0, y: 0 })
  const resizeStart = useRef({ x: 0, y: 0, w: 0, h: 0 })

  // ---- Persist position and size on change ----

  useEffect(() => {
    saveJSON(STORAGE_KEY_POS, position)
  }, [position])

  useEffect(() => {
    saveJSON(STORAGE_KEY_SIZE, size)
  }, [size])

  // ---- Drag handlers ----

  const handleDragStart = useCallback(
    (e: React.MouseEvent) => {
      // Only start drag from left mouse button
      if (e.button !== 0) return
      e.preventDefault()
      isDragging.current = true
      dragOffset.current = {
        x: e.clientX - position.x,
        y: e.clientY - position.y,
      }
    },
    [position],
  )

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (isDragging.current) {
        const newX = Math.max(0, Math.min(e.clientX - dragOffset.current.x, window.innerWidth - 100))
        const newY = Math.max(0, Math.min(e.clientY - dragOffset.current.y, window.innerHeight - 40))
        setPosition({ x: newX, y: newY })
      }

      if (isResizing.current) {
        const newW = Math.max(MIN_WIDTH, resizeStart.current.w + (e.clientX - resizeStart.current.x))
        const newH = Math.max(MIN_HEIGHT, resizeStart.current.h + (e.clientY - resizeStart.current.y))
        setSize({ width: newW, height: newH })
      }
    }

    const handleMouseUp = () => {
      isDragging.current = false
      isResizing.current = false
    }

    window.addEventListener('mousemove', handleMouseMove)
    window.addEventListener('mouseup', handleMouseUp)
    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('mouseup', handleMouseUp)
    }
  }, [])

  // ---- Resize handlers ----

  const handleResizeStart = useCallback(
    (e: React.MouseEvent) => {
      if (e.button !== 0) return
      e.preventDefault()
      e.stopPropagation()
      isResizing.current = true
      resizeStart.current = {
        x: e.clientX,
        y: e.clientY,
        w: size.width,
        h: size.height,
      }
    },
    [size],
  )

  // ---- Render ----

  if (!isOpen) return null

  return (
    <div
      ref={panelRef}
      className="fixed z-50 flex flex-col bg-card border border-border rounded-lg shadow-lg overflow-hidden animate-pop-in"
      style={{
        left: position.x,
        top: position.y,
        width: size.width,
        height: minimized ? 'auto' : size.height,
      }}
    >
      {/* Title bar - draggable */}
      <div
        className="flex items-center justify-between px-3 py-2 bg-muted border-b border-border cursor-move select-none shrink-0"
        onMouseDown={handleDragStart}
      >
        <div className="flex items-center gap-2 min-w-0">
          <BookOpen size={14} className="text-primary shrink-0" />
          <span className="text-xs font-semibold text-foreground truncate">
            Workspace Guide
          </span>
        </div>

        <div className="flex items-center gap-0.5 shrink-0">
          <Button
            variant="ghost"
            size="icon-xs"
            onClick={() => setMinimized((prev) => !prev)}
            title={minimized ? 'Expand' : 'Minimize'}
          >
            {minimized ? <Maximize2 size={12} /> : <Minus size={12} />}
          </Button>
          <Button
            variant="ghost"
            size="icon-xs"
            onClick={onClose}
            title="Close guide"
          >
            <X size={12} />
          </Button>
        </div>
      </div>

      {/* Body - hidden when minimized */}
      {!minimized && (
        <>
          {/* Tab bar */}
          <div className="flex border-b border-border bg-background overflow-x-auto shrink-0">
            {TAB_IDS.map((id) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`px-2.5 py-1.5 text-[10px] font-medium whitespace-nowrap transition-colors border-b-2 ${
                  activeTab === id
                    ? 'border-primary text-foreground'
                    : 'border-transparent text-muted-foreground hover:text-foreground hover:bg-muted/50'
                }`}
              >
                {TAB_LABELS[id]}
              </button>
            ))}
          </div>

          {/* Tab content area */}
          <div className="flex-1 overflow-y-auto p-3 min-h-0">
            <TabContent tab={activeTab} />
          </div>

          {/* Resize handle (bottom-right corner) */}
          <div
            className="absolute bottom-0 right-0 w-4 h-4 cursor-nwse-resize flex items-center justify-center"
            onMouseDown={handleResizeStart}
            title="Resize"
          >
            <GripHorizontal size={10} className="text-muted-foreground rotate-[-45deg]" />
          </div>
        </>
      )}
    </div>
  )
}
